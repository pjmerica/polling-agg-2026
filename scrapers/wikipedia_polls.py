"""
Wikipedia polling scraper.

Supplements the NYT bulk feed (scrapers/nytimes.py) which only carries
~86 races. Wikipedia's per-state "Opinion polling for the 2026
United States ___ elections in <State>" pages have comprehensive
per-district polling tables that include polls NYT prunes from its
bulk CSV (e.g. NY-13 primary polls in 2026).

Coverage:
  - U.S. House: one page per state, sections per district.
  - U.S. Senate: one page per Senate race (state-level).
  - Governor: one page per Governor race (state-level).
  - Generic ballot + presidential approval: dedicated pages, tagged
    with stage='generic_ballot' or 'approval' so the dashboard can
    show them under a separate Raw Polls sub-tab.

Conflict policy: NYT wins. The scraper writes to
data/raw/wikipedia_polls.csv with the same schema as nyt_polls.csv;
scripts/regen_data.py concats them, dedups on
(pollster, end_date, candidate), keeping NYT rows on conflict.

How table parsing works (per Wikipedia's convention):
  - Polling tables are <table class="wikitable">
  - First <th> contains "Poll source", "Pollster", or similar
  - Subsequent <th>s name columns: Date(s) administered, Sample size,
    Margin of error, then one column per candidate, then Other/Undecided
  - Each <tr> after the header is a poll. Cells:
      - pollster name (in first td, with [partisan tag] like "(D)")
      - dates (e.g. "June 9-11, 2026" — we parse end date)
      - sample size with population type (e.g. "468 (LV)")
      - margin of error (we ignore)
      - per-candidate percentages

The structure is fairly stable across state pages but every parser
needs to be defensive — Wikipedia volunteers don't follow a strict
schema. We skip rows we can't parse rather than crashing.

Output schema (matches nyt_polls.csv exactly so they concat cleanly):
  race_id, source, market_title, implied_prob, weight, fetched_at,
  pollster, candidate, party, stage, sample_size, end_date,
  partisan, poll_id, question_id
"""

import sys
import re
import time
import urllib.request
import urllib.error
import urllib.parse
import hashlib
from pathlib import Path
from datetime import datetime, timezone, date

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from utils.http_headers import DEFAULT_HEADERS

RAW = ROOT / "data" / "raw"

# Wikipedia URL templates per category. The state name segment uses
# underscores in URL form (e.g. "New_York", "Rhode_Island").
URL_HOUSE = "https://en.wikipedia.org/wiki/2026_United_States_House_of_Representatives_elections_in_{state}"
URL_SENATE = "https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_{state}"
URL_GOVERNOR = "https://en.wikipedia.org/wiki/2026_{state}_gubernatorial_election"
URL_GENERIC_BALLOT = "https://en.wikipedia.org/wiki/2026_United_States_elections"
URL_APPROVAL = "https://en.wikipedia.org/wiki/Public_image_of_Donald_Trump"  # rough but has approval tables

# Mayoral races. Wikipedia uses "<Year>_<City>_mayoral_election" pages.
# Each tuple is (year, city_slug_for_url, race_id_slug). Mayoral cycle
# varies by city — list curated 2026-06-25 from cities with a current
# Wikipedia page. Add more as new cycles open up.
MAYORAL_RACES = [
    (2025, "New_York_City",  "nyc"),
    (2025, "Boston",         "boston"),
    (2025, "Detroit",        "detroit"),
    (2025, "Pittsburgh",     "pittsburgh"),
    (2025, "Cleveland",      "cleveland"),
    (2025, "Seattle",        "seattle"),
    (2025, "Atlanta",        "atlanta"),
    (2025, "Minneapolis",    "minneapolis"),
    (2025, "Buffalo",        "buffalo"),
    (2026, "Los_Angeles",    "la"),
    (2026, "Miami",          "miami"),
    (2027, "Chicago",        "chicago"),
]

# State name → URL segment. Two-letter abbreviations for race_id mapping.
STATES = {
    "AL": "Alabama",  "AK": "Alaska",   "AZ": "Arizona",  "AR": "Arkansas",
    "CA": "California","CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida",  "GA": "Georgia",  "HI": "Hawaii",   "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana",  "IA": "Iowa",     "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana","ME": "Maine",    "MD": "Maryland",
    "MA": "Massachusetts","MI": "Michigan","MN": "Minnesota","MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana",  "NE": "Nebraska", "NV": "Nevada",
    "NH": "New_Hampshire","NJ": "New_Jersey","NM": "New_Mexico","NY": "New_York",
    "NC": "North_Carolina","ND": "North_Dakota","OH": "Ohio","OK": "Oklahoma",
    "OR": "Oregon",   "PA": "Pennsylvania","RI": "Rhode_Island","SC": "South_Carolina",
    "SD": "South_Dakota","TN": "Tennessee","TX": "Texas","UT": "Utah",
    "VT": "Vermont",  "VA": "Virginia", "WA": "Washington","WV": "West_Virginia",
    "WI": "Wisconsin","WY": "Wyoming",
}

# Headers signaling a row is a poll table (case-insensitive substring match
# in the first <th>). Wikipedia uses several phrasings for "Poll source".
POLL_TABLE_HEADER_HINTS = ("poll source", "pollster", "polling firm")

# Words to detect a column is the date column
DATE_COL_HINTS = ("date", "administered", "field")

# Sample-size column hints
SAMPLE_COL_HINTS = ("sample", "size", "n=")

# Margin-of-error hints (we skip this column)
MOE_COL_HINTS = ("margin", "moe", "error")

# Non-candidate columns to skip (those that aren't an actual candidate)
SKIP_CANDIDATE_HEADERS = {
    "other", "someone else", "undecided", "no opinion", "unsure", "don't know",
    "would not vote", "neither", "none of these", "no one", "skip",
    "lead", "spread", "margin",
}

REQUEST_DELAY_S = 0.4  # polite between Wikipedia hits


def fetch_page(url: str, max_retries: int = 3) -> str | None:
    """Fetch a Wikipedia page. Returns HTML body or None on 404 / error."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Page doesn't exist for this race
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            print(f"    WARN: fetch_page {url} failed: HTTP {e.code}")
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            print(f"    WARN: fetch_page {url} failed: {e}")
            return None
    return None


def parse_pct(text: str) -> float | None:
    """Extract a percentage from a cell like '35%' or '<b>35%</b>' or '–'."""
    if not text:
        return None
    text = text.replace("\xa0", " ").strip()
    if text in ("–", "—", "-", ""):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_sample_size(text: str) -> int | None:
    """Extract integer sample size from '468 (LV)' or '~1,200' etc."""
    if not text:
        return None
    text = text.replace(",", "").replace("~", "").replace("≈", "").strip()
    m = re.search(r"(\d+)", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def parse_population(text: str) -> str:
    """Extract the surveyed-population tag from '468 (LV)' / '1,200 RV' / 'A' cells.
    Returns 'lv' | 'rv' | 'a' | 'v' | '' (matching the NYT/538 vocabulary)."""
    if not text:
        return ""
    m = re.search(r"\b(LV|RV|A|V)\b", str(text).upper())
    return m.group(1).lower() if m else ""


def parse_end_date(text: str) -> str | None:
    """Parse the END date from a Wikipedia date range like 'June 9-11, 2026'
    or 'March 25–30, 2026'. Returns ISO YYYY-MM-DD or None.

    Wikipedia uses several formats:
      'June 9–11, 2026'       → 2026-06-11
      'March 25–April 2, 2026' → 2026-04-02
      'June 11, 2026'          → 2026-06-11
    """
    if not text:
        return None
    text = text.replace("\xa0", " ").strip()
    # Try the end-of-range explicitly. Cases:
    #   "MONTH D1-D2, YYYY"      (same month range)
    #   "MONTH1 D1-MONTH2 D2, YYYY" (cross-month)
    #   "MONTH D, YYYY"          (single date)
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
        "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
        "november": 11, "december": 12,
    }
    # Strip cite-bracket annotations
    text = re.sub(r"\[[^\]]+\]", "", text)
    # Last "Month Day, Year" pattern in the string is usually the end of range.
    # Cross-month: "March 25-April 2, 2026" → match "April 2, 2026"
    # Single date: "June 11, 2026" → match "June 11, 2026"
    # Range same month: "June 9-11, 2026" → match end day separately
    cross_month = re.search(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})\s*$",
        text,
    )
    if cross_month:
        mon = cross_month.group(1).lower()
        day = int(cross_month.group(2))
        year = int(cross_month.group(3))
        if mon in months:
            try:
                return date(year, months[mon], day).isoformat()
            except ValueError:
                return None
    # Same-month range: "June 9-11, 2026"
    same_month = re.search(
        r"([A-Za-z]+)\s+\d{1,2}\s*[–\-]\s*(\d{1,2}),?\s*(\d{4})",
        text,
    )
    if same_month:
        mon = same_month.group(1).lower()
        end_day = int(same_month.group(2))
        year = int(same_month.group(3))
        if mon in months:
            try:
                return date(year, months[mon], end_day).isoformat()
            except ValueError:
                return None
    # Fallback: pandas
    try:
        return pd.to_datetime(text).date().isoformat()
    except (ValueError, TypeError):
        return None


def clean_pollster(text: str) -> tuple[str, str]:
    """Split 'Mercury Public Affairs (D)' into ('Mercury Public Affairs', 'D')."""
    if not text:
        return ("", "")
    text = re.sub(r"\[[^\]]+\]", "", text).strip()
    m = re.search(r"\(([RDIRC]|REP|DEM|IND)\)\s*$", text, re.IGNORECASE)
    partisan = ""
    if m:
        partisan = m.group(1).upper()[0]  # 'R', 'D', 'I'
        text = text[:m.start()].strip()
    return (text, partisan)


def clean_candidate_header(text: str) -> str:
    """A column header like 'Darializa\\nAvila Chevalier' → 'Darializa Avila Chevalier'.

    Also strips party suffix annotations like '(D)' / '(R)' / '(I)' that
    Wikipedia adds on the column header. The party gets parsed
    separately (extract_candidate_party) so dedup against NYT (which
    uses bare names) works."""
    if not text:
        return ""
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s*\(\s*[DRIL](?:EM|EP|ND|IB)?\s*\)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_candidate_party(text: str) -> str:
    """Pull DEM/REP/IND from a candidate label like 'Mike Rogers (R)' or
    'Abdul El-Sayed (D)'. Returns '' if no annotation."""
    if not text:
        return ""
    m = re.search(r"\(\s*([DRIL](?:EM|EP|ND|IB)?)\s*\)", text, re.IGNORECASE)
    if not m:
        return ""
    code = m.group(1).upper()
    if code.startswith("D"): return "DEM"
    if code.startswith("R"): return "REP"
    if code.startswith("I") or code.startswith("L"): return "IND"
    return ""


def stable_id(*parts) -> str:
    """Deterministic id from a tuple of strings — for poll_id/question_id when
    Wikipedia doesn't provide one. Reasonably collision-resistant."""
    s = "|".join(str(p or "") for p in parts)
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:24]


def infer_section_context(header_text: str) -> tuple[str, str]:
    """Read a section heading like 'Republican primary' or 'Democratic
    primary runoff' and return (stage, party). Stage is one of
    'primary', 'primary runoff', 'general', or '' if unknown. Party is
    'REP', 'DEM', 'IND', or '' if unknown.

    Wikipedia consistently uses these section names, and tables under
    them tend not to repeat the party annotation on each candidate
    column — so when our header parser comes back with empty party we
    fall back to the section's implied party.
    """
    if not header_text:
        return ("", "")
    h = header_text.lower()
    party = ""
    if "republican" in h: party = "REP"
    elif "democratic" in h or "democrat" in h: party = "DEM"
    elif "independent" in h: party = "IND"
    stage = ""
    if "runoff" in h: stage = "primary runoff"
    elif "primary" in h: stage = "primary"
    elif "general" in h: stage = "general"
    return (stage, party)


def parse_poll_table(table, race_id: str, stage: str, default_party: str = "") -> list[dict]:
    """Parse one Wikipedia <table class='wikitable'> that contains polls.
    Returns a list of row dicts in nyt_polls.csv schema. Returns [] if the
    table isn't actually a polling table.

    default_party: fallback party assigned to candidates whose column
    header lacks a (D)/(R) annotation. Comes from the enclosing
    section heading (see infer_section_context).
    """
    rows_out = []
    # Pull header row
    thead_rows = table.find_all("tr")
    if not thead_rows:
        return []
    header_cells = thead_rows[0].find_all(["th"])
    if not header_cells:
        return []
    # Keep both the raw text (carries party annotations like '(D)')
    # and the cleaned text (party stripped). Party gets parsed out
    # from raw and stored on the row so we know each candidate's
    # affiliation; the cleaned text is the dedup-safe candidate name
    # that matches NYT's bare names.
    header_raw = [
        re.sub(r"\s+", " ",
               re.sub(r"\[[^\]]+\]", "", c.get_text(" ", strip=True))
        ).strip()
        for c in header_cells
    ]
    header_texts = [clean_candidate_header(t) for t in header_raw]
    candidate_party_for_col = [extract_candidate_party(t) for t in header_raw]
    if not header_texts:
        return []
    # Verify first column is a poll-source header (otherwise it's a different table)
    first = header_texts[0].lower()
    if not any(hint in first for hint in POLL_TABLE_HEADER_HINTS):
        return []

    # Identify column roles
    col_role = []  # list parallel to header_texts: 'pollster', 'date', 'sample',
                   # 'moe', 'candidate:<name>', 'skip'
    for h in header_texts:
        h_low = h.lower()
        if any(hint in h_low for hint in POLL_TABLE_HEADER_HINTS):
            col_role.append("pollster")
        elif any(hint in h_low for hint in DATE_COL_HINTS):
            col_role.append("date")
        elif any(hint in h_low for hint in SAMPLE_COL_HINTS):
            col_role.append("sample")
        elif any(hint in h_low for hint in MOE_COL_HINTS):
            col_role.append("moe")
        elif h_low in SKIP_CANDIDATE_HEADERS:
            col_role.append("skip")
        elif h.strip():
            col_role.append(f"candidate:{h}")
        else:
            col_role.append("skip")

    # Per-candidate party lookup built from the header annotations,
    # used by the row loop below so each candidate gets the right
    # party rather than inheriting from the pollster sponsor tag.
    candidate_party = {
        header_texts[i]: candidate_party_for_col[i]
        for i, role in enumerate(col_role)
        if role.startswith("candidate:")
    }

    fetched_at = datetime.now(timezone.utc).isoformat()

    for tr in thead_rows[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        # Only data rows. Skip rows used for separators / colspan tricks.
        if all(not c.get_text(strip=True) for c in cells):
            continue

        row_vals = {}
        for i, cell in enumerate(cells):
            if i >= len(col_role):
                break
            role = col_role[i]
            text = cell.get_text(" ", strip=True)
            row_vals[role] = text

        pollster_raw = row_vals.get("pollster", "")
        date_raw = row_vals.get("date", "")
        sample_raw = row_vals.get("sample", "")

        # Skip header-of-section rows like a blank pollster
        if not pollster_raw or not date_raw:
            continue

        pollster, partisan = clean_pollster(pollster_raw)
        end_date_iso = parse_end_date(date_raw)
        if not end_date_iso:
            continue
        sample = parse_sample_size(sample_raw)
        population = parse_population(sample_raw)   # 'lv'/'rv'/'a'/'v'/'' from '468 (LV)'

        # NYT CSV expects end_date in M/D/YY format (the format
        # regen_data.py's parse_iso handles). Convert.
        try:
            dt = date.fromisoformat(end_date_iso)
            nyt_format_date = f"{dt.month}/{dt.day}/{dt.year % 100:02d}"
        except ValueError:
            continue

        # Stable IDs derived from race + pollster + date so the same poll
        # gets the same ID across runs (lets the archive merge dedupe).
        poll_id = stable_id("wiki", race_id, pollster, end_date_iso)
        question_id = stable_id("wiki", race_id, pollster, end_date_iso, "q")

        # One CSV row per candidate column. NYT's nyt_polls.csv shape is
        # one row per (poll × candidate).
        for role, text in row_vals.items():
            if not role.startswith("candidate:"):
                continue
            cand_name = role[len("candidate:"):]
            pct = parse_pct(text)
            if pct is None:
                continue
            # Party comes from the column-header annotation (e.g. "Mike
            # Rogers (R)" → REP), with fallback to the enclosing
            # section's implied party (e.g. "Republican primary"
            # section → REP for unlabeled candidates). The pollster's
            # partisan sponsor tag is intentionally NOT used —
            # historically that made Mike Rogers (R) show up as DEM
            # whenever the pollster was a Democratic firm. It's still
            # preserved separately in the `partisan` column below.
            party = candidate_party.get(cand_name, "") or default_party
            rows_out.append({
                "race_id": race_id,
                "source": "wikipedia",
                "market_title": f"{pollster} — {race_id}",
                "implied_prob": round(pct / 100, 4),
                "weight": float(sample) if sample else 1.0,
                "fetched_at": fetched_at,
                "pollster": pollster,
                "candidate": cand_name,
                "party": party,
                "stage": stage,
                "sample_size": float(sample) if sample else None,
                "end_date": nyt_format_date,
                "partisan": partisan,
                "population": population,
                "poll_id": poll_id,
                "question_id": question_id,
            })

    return rows_out


def scrape_house_state(state_abbrev: str) -> list[dict]:
    """Scrape every district's polling table on a state's House page."""
    state = STATES.get(state_abbrev)
    if not state:
        return []
    url = URL_HOUSE.format(state=state)
    html = fetch_page(url)
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    # Walk the DOM in order tracking both the current District N and
    # the current stage / party context. When we cross into a new
    # district section both stage and party reset since district-level
    # subsections vary independently.
    current_district = None
    current_stage, current_party = "general", ""
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            text = el.get_text(" ", strip=True)
            m = re.search(r"District\s+(\d+)", text)
            if m:
                current_district = int(m.group(1))
                current_stage, current_party = "general", ""
            s, p = infer_section_context(text)
            if s: current_stage = s
            if p: current_party = p
        elif el.name == "table" and current_district is not None:
            classes = el.get("class", []) or []
            if "wikitable" not in classes:
                continue
            race_id = f"2026-H-{state_abbrev}-{current_district:02d}"
            new_rows = parse_poll_table(
                el, race_id, current_stage, default_party=current_party,
            )
            rows.extend(new_rows)
    return rows


def _scrape_state_race(url: str, race_id: str) -> list[dict]:
    """Shared helper for state-level races (Senate, Governor). Walks the
    DOM in document order so we know the closest preceding
    'Republican primary' / 'Democratic primary' / 'General election'
    section header, and use it to derive (stage, party) for each
    table. Falls back to ('general', '') when no section context
    applies."""
    html = fetch_page(url)
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    current_stage, current_party = "general", ""
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            s, p = infer_section_context(el.get_text(" ", strip=True))
            if s: current_stage = s
            if p: current_party = p
            # No party-bearing keywords means this is a non-partisan
            # section heading (e.g. "Campaign", "Endorsements") — only
            # reset stage if it ALSO had no stage match, otherwise we'd
            # lose section context every time we passed a sub-header.
            # In practice infer_section_context returns ('','') for
            # those, so we don't overwrite.
        elif el.name == "table":
            classes = el.get("class", []) or []
            if "wikitable" not in classes:
                continue
            new_rows = parse_poll_table(
                el, race_id, current_stage, default_party=current_party,
            )
            rows.extend(new_rows)
    return rows


def scrape_senate_state(state_abbrev: str) -> list[dict]:
    state = STATES.get(state_abbrev)
    if not state:
        return []
    return _scrape_state_race(URL_SENATE.format(state=state), f"2026-SEN-{state_abbrev}")


def scrape_governor_state(state_abbrev: str) -> list[dict]:
    state = STATES.get(state_abbrev)
    if not state:
        return []
    return _scrape_state_race(URL_GOVERNOR.format(state=state), f"2026-GOV-{state_abbrev}")


def scrape_generic_ballot() -> list[dict]:
    """Scrape the 2026 generic-ballot polling table.

    Tagged with stage='generic_ballot' and race_id='2026-GENERIC' so the
    dashboard can route to a separate Raw Polls sub-tab. Currently no
    canonical race in utils/races.py for this — that's intentional, it's
    not a race, it's a nationwide indicator.
    """
    html = fetch_page(URL_GENERIC_BALLOT)
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        classes = table.get("class", []) or []
        if "wikitable" not in classes:
            continue
        new_rows = parse_poll_table(table, "2026-GENERIC", "generic_ballot")
        rows.extend(new_rows)
    return rows


def scrape_mayoral(year: int, city_slug: str, race_id_slug: str) -> list[dict]:
    """Scrape one mayoral race page. race_id pattern is
    'YYYY-MAYOR-<slug>'. Stage stays 'mayoral' so the Raw Polls
    sub-tab can route accordingly; section-context still feeds
    default_party for primary tables.
    """
    url = f"https://en.wikipedia.org/wiki/{year}_{city_slug}_mayoral_election"
    html = fetch_page(url)
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    race_id = f"{year}-MAYOR-{race_id_slug}"
    current_party = ""
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            _, p = infer_section_context(el.get_text(" ", strip=True))
            if p: current_party = p
        elif el.name == "table":
            classes = el.get("class", []) or []
            if "wikitable" not in classes:
                continue
            new_rows = parse_poll_table(
                table=el, race_id=race_id, stage="mayoral",
                default_party=current_party,
            )
            rows.extend(new_rows)
    return rows


def scrape_approval() -> list[dict]:
    """Scrape presidential approval polling. Best-effort; the Wikipedia page
    isn't strictly a polling-only page so coverage may be partial."""
    html = fetch_page(URL_APPROVAL)
    if html is None:
        return []
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        classes = table.get("class", []) or []
        if "wikitable" not in classes:
            continue
        new_rows = parse_poll_table(table, "2026-APPROVAL", "approval")
        rows.extend(new_rows)
    return rows


def run():
    RAW.mkdir(parents=True, exist_ok=True)
    out_path = RAW / "wikipedia_polls.csv"

    all_rows = []
    print("Wikipedia polling scraper starting...")

    # House — one page per state
    print("\n[house]")
    for abbr in sorted(STATES.keys()):
        rows = scrape_house_state(abbr)
        if rows:
            print(f"  {abbr} house: {len(rows)} rows across "
                  f"{len(set(r['race_id'] for r in rows))} districts")
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY_S)

    # Senate — only states with a 2026 Senate race exist as pages
    print("\n[senate]")
    for abbr in sorted(STATES.keys()):
        rows = scrape_senate_state(abbr)
        if rows:
            print(f"  {abbr} senate: {len(rows)} rows")
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY_S)

    # Governor — only states with a 2026 Governor race
    print("\n[governor]")
    for abbr in sorted(STATES.keys()):
        rows = scrape_governor_state(abbr)
        if rows:
            print(f"  {abbr} gov: {len(rows)} rows")
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY_S)

    # Mayoral races
    print("\n[mayoral]")
    for year, city_slug, race_id_slug in MAYORAL_RACES:
        rows = scrape_mayoral(year, city_slug, race_id_slug)
        if rows:
            print(f"  {year} {race_id_slug}: {len(rows)} rows")
        all_rows.extend(rows)
        time.sleep(REQUEST_DELAY_S)

    # Generic ballot + approval
    print("\n[generic ballot]")
    gb = scrape_generic_ballot()
    print(f"  {len(gb)} rows")
    all_rows.extend(gb)

    print("\n[approval]")
    ap = scrape_approval()
    print(f"  {len(ap)} rows")
    all_rows.extend(ap)

    if not all_rows:
        print("\nNo data scraped. Wikipedia structure may have changed or all pages 404'd.")
        return

    df = pd.DataFrame(all_rows)
    # Dedup within this scrape on (race_id, poll_id, candidate).
    df = df.drop_duplicates(subset=["race_id", "poll_id", "candidate"], keep="first")
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} rows to {out_path}")
    print(f"Coverage: {df['race_id'].nunique()} races, "
          f"{df['poll_id'].nunique()} unique polls, "
          f"{df['pollster'].nunique()} pollsters")


if __name__ == "__main__":
    run()
