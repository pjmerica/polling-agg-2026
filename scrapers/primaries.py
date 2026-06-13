"""
Scrape Ballotpedia for 2026 primary election dates + each state's primary
type (open / closed / semi-closed / top-two-jungle / etc) and write
data/raw/primaries.json. The dashboard reads this directly to populate
the Primaries tab.

Two source pages:
  1. https://ballotpedia.org/Election_calendar  → table with dates
  2. https://ballotpedia.org/State_primary_election_types  → per-state
     classification (open/closed/jungle/etc)

We only keep federal/statewide primary rows (House, Senate, Governor,
"statewide primary"). Local elections and special-district runoffs are
excluded.

Output schema (data/raw/primaries.json):
  {
    "fetched_at": "<iso>",
    "states": {
      "AL": {"type": "closed", "type_detail": "closed", "url": "https://ballotpedia.org/..."},
      ...
    },
    "races": [
      {"date_iso": "2026-06-09", "state": "Maine", "state_abbrev": "ME",
       "office": "MIXED", "description": "Maine statewide primary",
       "ballotpedia_url": "https://ballotpedia.org/..."},
      ...
    ]
  }

Notes:
  - "MIXED" office is used when a single Ballotpedia row covers multiple
    federal offices (Senate + House + Gov on one primary day). Most states
    work this way — one primary date.
  - We don't try to scrape filing-deadline data here; can add later.
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path

RAW = Path(__file__).parent.parent / "data" / "raw"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

CALENDAR_URL = "https://ballotpedia.org/Election_calendar"
PRIMARY_TYPES_URL = "https://ballotpedia.org/State_primary_election_types"

STATE_NAME_TO_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

# Manual classification for states with non-standard federal primary
# systems. Overrides whatever section of Ballotpedia's primary-types
# page mentions the state.
# Top-two / jungle: CA, LA, WA. AK is top-4 nonpartisan + RCV.
# Majority runoff: AL, AR, GA, MS, NC (some), OK, SC, TX go to a runoff
# if nobody >50% in the first round.
RUNOFF_STATES = {
    "AK": "top-four-rcv",
    "CA": "top-two",
    "GA": "majority-runoff",
    "LA": "top-two",
    "WA": "top-two",
    "AL": "majority-runoff",
    "AR": "majority-runoff",
    "MS": "majority-runoff",
    "OK": "majority-runoff",
    "SC": "majority-runoff",
    "TX": "majority-runoff",
    "NC": "majority-runoff",
}

# Electoral system used at the FEDERAL primary stage. Independent of the
# closed/open/jungle partisan structure — this axis describes the
# vote-counting METHOD itself.
#   FPTP   — plurality wins, one round
#   Runoff — top-1 must hit >50%, else top-2 runoff round (or top-two
#            jungle systems that proceed to a head-to-head general)
#   RCV    — ranked-choice ballots
ELECTORAL_SYSTEM = {
    "AK": "RCV",          # top-4 nonpartisan + RCV general
    "AL": "Runoff",
    "AR": "Runoff",
    "CA": "Runoff",       # top-two jungle (one head-to-head round)
    "GA": "Runoff",
    "LA": "Runoff",       # top-two jungle
    "MS": "Runoff",
    "NC": "Runoff",
    "OK": "Runoff",
    "SC": "Runoff",
    "TX": "Runoff",
    "WA": "Runoff",       # top-two jungle
    # Maine uses RCV for federal *general* but not primaries — primary is FPTP.
    # All other states: plurality wins the primary.
}

# Statutory offset (in DAYS) from a state's federal primary to its
# runoff election, IF no candidate wins outright. Sources: each state's
# election code, cross-checked with Ballotpedia per-cycle tables.
#
# States not in this map either don't have a runoff (FPTP plurality),
# don't have a fixed offset (LA's "primary" is the November general; its
# runoff is a December date set by law for that cycle), or use RCV (AK).
RUNOFF_OFFSET_DAYS = {
    "AL": 28,    # 4 weeks
    "AR": 28,    # 4 weeks (changed from 5 weeks per Act 1101 of 2019)
    "GA": 63,    # 9 weeks for federal runoffs (per SB 202, 2021)
    "MS": 21,    # 3 weeks
    "NC": 70,    # 10 weeks (only if no candidate >30%)
    "OK": 70,    # late August, roughly 10 weeks after June primary
    "SC": 14,    # 2 weeks
    "TX": 63,    # 9 weeks
}

# States with a runoff but a fixed calendar date (not offset-based).
# For 2026 only. LA primary is the November general; runoff date is set
# by law. CA/WA's "runoff" is the November general — same date as the
# general for everyone, so we don't list those here.
RUNOFF_FIXED_DATE_2026 = {
    "LA": "2026-12-05",  # Louisiana general runoff is first Saturday in December
}

# Note for CA/WA/AK: their "runoff" isn't a separate event — it's the
# November general (CA/WA top-two jungle) or the November RCV count (AK).
TOP_TWO_GENERAL_2026 = "2026-11-03"


def compute_runoff_date(state_abbrev, primary_date_iso, description):
    """Return ISO date for the runoff if applicable, else None.
    A "runoff" only applies to primary contests — runoff or special-runoff
    rows themselves should not generate a further runoff date.
    """
    if not primary_date_iso:
        return None
    desc_lower = (description or "").lower()
    # Already a runoff row? Don't chain another runoff off it.
    if "runoff" in desc_lower:
        return None
    if state_abbrev in RUNOFF_FIXED_DATE_2026:
        return RUNOFF_FIXED_DATE_2026[state_abbrev]
    if state_abbrev in ("CA", "WA"):
        # Top-two jungle: the "runoff" is the general election.
        return TOP_TWO_GENERAL_2026
    offset = RUNOFF_OFFSET_DAYS.get(state_abbrev)
    if not offset:
        return None
    try:
        d = date.fromisoformat(primary_date_iso) + timedelta(days=offset)
        return d.isoformat()
    except ValueError:
        return None

RETRY_CODES = {403, 408, 429, 500, 502, 503, 504}


def fetch(url, max_retries=4):
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in RETRY_CODES and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  HTTP {e.code} on {url}, retry in {wait}s...")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Network error: {e}, retry in {wait}s...")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"fetch failed after {max_retries} retries: {url}")


def _clean(s):
    """Strip tags and normalize whitespace."""
    s = re.sub(r"<[^>]+>", " ", unescape(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_calendar(html):
    """Pull (date_iso, state, state_abbrev, description, url) from the
    edatetable. Keep only federal+statewide rows."""
    out = []
    seen = set()
    # There are 2 edatetable instances (upcoming + recent); concat both.
    for table_match in re.finditer(
        r'<table[^>]*class="edatetable[^"]*"[\s\S]*?</table>', html
    ):
        tbl = table_match.group(0)
        rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", tbl)
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row)
            if len(cells) < 4:
                continue
            state_raw = _clean(cells[0])
            # district column often duplicates state — ignore
            desc_raw = _clean(cells[2])
            date_raw = _clean(cells[3])
            # Skip header rows
            if state_raw.lower() == "state":
                continue
            if not state_raw or not desc_raw or not date_raw:
                continue
            # Extract state abbrev — first word match
            state_abbrev = None
            for name, ab in STATE_NAME_TO_ABBREV.items():
                if state_raw.startswith(name):
                    state_abbrev = ab
                    state_name = name
                    break
            if not state_abbrev:
                continue
            # Filter to STATEWIDE federal+gubernatorial primary events only.
            # Drops local elections, school boards, special districts, etc.
            d = desc_raw.lower()
            # Require either a statewide primary mention, or an explicit
            # Senate/House/Governor primary or runoff.
            statewide = "statewide primary" in d or "statewide runoff" in d
            federal = any(k in d for k in (
                "u.s. senate", "us senate", "united states senate",
                "u.s. house", "us house", "united states house",
            ))
            gubernatorial = "governor" in d or "gubernat" in d
            if not (statewide or federal or gubernatorial):
                continue
            # Skip local / non-federal events even if "primary" appears
            if any(k in d for k in (
                "recall", "school board", "city council", "mayoral",
                "city general", "city primary", "special general",
                "special districts", "community schools", "board of regents",
                "newark", "lancaster county",
            )):
                continue
            # Parse date
            date_iso = None
            m = re.match(r"([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})", date_raw)
            if m:
                month = {
                    "January": 1, "February": 2, "March": 3, "April": 4,
                    "May": 5, "June": 6, "July": 7, "August": 8,
                    "September": 9, "October": 10, "November": 11, "December": 12,
                }.get(m.group(1))
                if month:
                    date_iso = f"{m.group(3)}-{month:02d}-{int(m.group(2)):02d}"
            if not date_iso:
                continue
            # Office classification
            office = "MIXED"
            if "senate" in d:
                office = "SEN"
            elif "governor" in d or "gubernat" in d:
                office = "GOV"
            elif "house" in d and "district" in d:
                office = "H"
            # Dedupe
            key = (date_iso, state_abbrev, desc_raw)
            if key in seen:
                continue
            seen.add(key)
            # Best-effort ballotpedia link
            bp_url = (f"https://ballotpedia.org/{state_name.replace(' ', '_')}"
                      f"_elections,_2026")
            out.append({
                "date_iso": date_iso,
                "state": state_name,
                "state_abbrev": state_abbrev,
                "office": office,
                "description": desc_raw,
                "ballotpedia_url": bp_url,
            })
    out.sort(key=lambda r: (r["date_iso"], r["state_abbrev"]))
    return out


def parse_primary_types(html):
    """Walk the Open/Closed/Semi-closed/Top-two sections and tag each
    state with its primary type. Returns {abbrev: {type: ..., type_detail: ...}}.
    """
    out = {}
    # Section markers on this page (in order): Open primaries, Closed
    # primaries, Semi-closed primaries, Top-two primaries and variants.
    # The Top-two section also mentions Nebraska because its STATE
    # legislature is nonpartisan — but federal primaries there are
    # partisan, so we don't want to over-classify it. Restrict the
    # top-two section to states we explicitly list in RUNOFF_STATES.
    section_pat = re.compile(
        r'<h[23][^>]*>\s*<span[^>]*id="([^"]+)"[^>]*>([^<]+)</span>'
    )
    sections = [(m.start(), m.group(1), m.group(2)) for m in section_pat.finditer(html)]
    # Map id -> (start, type)
    target_secs = {
        "Open_primaries": "open",
        "Closed_primaries": "closed",
        "Semi-closed_primaries": "semi-closed",
        "Top-two_primaries_and_variants": "top-two",
    }
    for i, (start, sec_id, _label) in enumerate(sections):
        kind = target_secs.get(sec_id)
        if not kind:
            continue
        end = sections[i + 1][0] if i + 1 < len(sections) else len(html)
        chunk = html[start:end]
        # State names linked inside the chunk
        for name, ab in STATE_NAME_TO_ABBREV.items():
            if re.search(rf'\b{re.escape(name)}\b', chunk):
                # Top-two section mentions Nebraska (state legislature only).
                # Only honor the top-two label for states in our explicit
                # RUNOFF_STATES allowlist for federal top-two systems.
                if kind == "top-two" and RUNOFF_STATES.get(ab) not in (
                    "top-two", "top-four-rcv"
                ):
                    continue
                detail = RUNOFF_STATES.get(ab, kind)
                # Don't downgrade a manual top-two/runoff classification
                if ab in out and out[ab]["type_detail"] in (
                    "top-two", "majority-runoff", "top-four-rcv"
                ):
                    continue
                out[ab] = {"type": kind, "type_detail": detail}
    # Fill remaining states with their RUNOFF_STATES classification or
    # default "open".
    for ab in STATE_NAME_TO_ABBREV.values():
        if ab not in out:
            detail = RUNOFF_STATES.get(ab, "open")
            kind = "top-two" if detail in ("top-two", "top-four-rcv") else (
                "closed" if detail == "majority-runoff" else "open"
            )
            out[ab] = {"type": kind, "type_detail": detail}
    # Tag every state with its electoral system (FPTP / Runoff / RCV).
    for ab, info in out.items():
        info["electoral_system"] = ELECTORAL_SYSTEM.get(ab, "FPTP")
    return out


def run():
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"Fetching {CALENDAR_URL} ...")
    cal_html = fetch(CALENDAR_URL)
    print(f"  got {len(cal_html)} bytes")
    print(f"Fetching {PRIMARY_TYPES_URL} ...")
    types_html = fetch(PRIMARY_TYPES_URL)
    print(f"  got {len(types_html)} bytes")

    print("Parsing primary types ...")
    types = parse_primary_types(types_html)
    print(f"  classified {len(types)} states")

    print("Parsing election calendar ...")
    races = parse_calendar(cal_html)
    print(f"  found {len(races)} primary/runoff rows")

    if not races:
        # Ballotpedia's calendar rolls past dates off as the year progresses,
        # so by late summer most state primaries are gone and only specials/
        # runoffs remain — those don't match our "statewide primary" filter.
        # That's not a fetch failure, so don't kill the whole daily refresh.
        # If a prior docs/primaries_data.js exists, leave it in place and
        # exit 0 so downstream steps continue. Only fail if there's no
        # prior data at all (first-ever run with no rows).
        docs_path = Path(__file__).parent.parent / "docs" / "primaries_data.js"
        if docs_path.exists() and docs_path.stat().st_size > 100:
            print(f"  No matching rows today — keeping existing {docs_path.name}.")
            return
        raise SystemExit(
            "Ballotpedia returned no primary rows AND no prior data to keep. "
            "Page structure may have changed."
        )

    # Annotate each race with its state's primary type + electoral system,
    # plus the runoff date if one would apply.
    for r in races:
        t = types.get(r["state_abbrev"], {})
        r["primary_type"] = t.get("type")
        r["primary_type_detail"] = t.get("type_detail")
        r["electoral_system"] = t.get("electoral_system", "FPTP")
        r["runoff_date_iso"] = compute_runoff_date(
            r["state_abbrev"], r["date_iso"], r["description"]
        )

    data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_urls": [CALENDAR_URL, PRIMARY_TYPES_URL],
        "states": types,
        "races": races,
    }
    out_path = RAW / "primaries.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved to {out_path}")

    # Also publish to docs/ so the dashboard can fetch it without a build step.
    docs_path = Path(__file__).parent.parent / "docs" / "primaries_data.js"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_text(
        "const PRIMARIES = " + json.dumps(data, separators=(",", ":")) + ";",
        encoding="utf-8",
    )
    print(f"Published to {docs_path}")
    print("\nSample rows:")
    for r in races[:8]:
        print(f"  {r['date_iso']}  {r['state_abbrev']}  {r['office']:5}  "
              f"{r['primary_type_detail']:18}  {r['description'][:60]}")


if __name__ == "__main__":
    run()
