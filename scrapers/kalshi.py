"""
Kalshi prediction market scraper.

Kalshi has a public REST API for their elections domain — no auth required for reads.

Base URL: https://api.elections.kalshi.com/v1/

Key endpoints:
  GET /v1/series/?limit=100&cursor=...
    All market series (9500+ total, ~565 election-related)

  GET /v1/series/{ticker}
    Detail for a single series

  GET /v1/events/?series_ticker={ticker}&limit=100
    Events (elections) under a series. Markets are nested inside event objects.
    Market fields include: ticker, title, yes_ask, yes_bid, last_price,
    open_interest, volume, status

Market price scale: 0-100 (cents), so 87 = 87% implied probability.

Race identification strategy:
  Series tickers follow patterns:
    SENATEPARTY{STATE}   — e.g. SENATEPARTYCA, SENATEPARTYGA
    GOVPARTY{STATE}      — e.g. GOVPARTYCA, GOVPARTYTX
    HOUSE{STATE}{DIST}   — e.g. HOUSECA47, HOUSETX28
    SENATE{STATE}        — alternate form, e.g. SENATEPA, SENATENH
  We match these to canonical race_ids from utils/races.py.
"""

import time
import urllib.request
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
KALSHI_BASE = "https://api.elections.kalshi.com/v1"
HEADERS = {"User-Agent": "Mozilla/5.0 (research/polling-aggregator)", "Accept": "application/json"}

# Keywords to identify 2026 election series
ELECTION_KEYWORDS = [
    "senate", "governor", "house", "midterm", "2026",
    "senateparty", "govparty", "houseaz", "housenc", "housega",
    "housetx", "housemi", "houseca", "houseny", "housepa",
    "houseva", "housefl", "housewi", "houseoh", "housemo",
]

# Map state abbreviations to full names for matching
STATE_ABBREV_MAP = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def _get(path: str, params: dict = None) -> dict:
    url = f"{KALSHI_BASE}{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_all_series() -> list[dict]:
    """Paginate through all Kalshi series and return election-related ones."""
    all_series = []
    cursor = None
    page = 0
    while True:
        params = {"limit": "100"}
        if cursor:
            params["cursor"] = cursor
        data = _get("/series/", params)
        batch = data.get("series", [])
        if not batch:
            break
        for s in batch:
            ticker = s.get("ticker", "").lower()
            title = s.get("title", "").lower()
            if any(k in ticker or k in title for k in ELECTION_KEYWORDS):
                all_series.append(s)
        cursor = data.get("cursor")
        page += 1
        if not cursor or len(batch) < 100:
            break
    return all_series


def fetch_events_for_series(series_ticker: str) -> list[dict]:
    """Fetch all events (and their nested markets) for a series."""
    data = _get("/events/", {"series_ticker": series_ticker, "limit": "100"})
    return data.get("events", [])


def infer_race_id(series_ticker: str, series_title: str) -> str | None:
    """
    Attempt to infer a canonical race_id from the Kalshi series ticker/title.

    Returns a string like "2026-SEN-PA" or None if can't determine.

    Handles Kalshi ticker patterns:
      SENATEPARTY{ST}    -> 2026-SEN-{ST}   e.g. SENATEPARTYCA
      SENATE{ST}         -> 2026-SEN-{ST}   e.g. SENATEPA, SENATENH
      SENATE-{ST}        -> 2026-SEN-{ST}   e.g. SENATE-MI
      KXSENATE{ST}...    -> 2026-SEN-{ST}   e.g. KXSENATEMSR (MS primary)
      GOVPARTY{ST}       -> 2026-GOV-{ST}   e.g. GOVPARTYCA
      GOVPARTY{ST}...    -> 2026-GOV-{ST}   e.g. GOVPARTYNE
      HOUSE{ST}{DIST}    -> 2026-H-{ST}-{D} e.g. HOUSECA47
      Title fallback: "X Senate race" or "X Governor" -> extract state name
    """
    ticker = series_ticker.upper()

    # SENATEPARTY{STATE} or SENATEPARTY-{STATE}
    m = re.match(r"SENATEPARTY[-_]?([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    # SENATE{STATE} or SENATE-{STATE} (bare, no prefix)
    m = re.match(r"SENATE[-_]?([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    # KXSENATE{STATE}{SUFFIX} — e.g. KXSENATEMSR (Mississippi), KXSENATEMTD, KXSENATESCR
    # State abbrev is 2 chars, sometimes followed by 1 char suffix
    m = re.match(r"KXSENATE([A-Z]{2})([A-Z]?)$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    # KXSENATE{STATE} with no suffix
    m = re.match(r"KXSENATE([A-Z]{2})$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    # GOVPARTY{STATE}...
    m = re.match(r"GOVPARTY([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-GOV-{m.group(1)}"

    # KXGOV{STATE}... e.g. KXGOVOHNOMD, KXGOVMNOMR
    m = re.match(r"KXGOV([A-Z]{2})[A-Z0-9]+$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-GOV-{m.group(1)}"

    # HOUSE{STATE}{DIST} (e.g. HOUSECA47, HOUSETX28)
    m = re.match(r"HOUSE([A-Z]{2})(\d+)$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        state = m.group(1)
        dist = m.group(2).zfill(2)
        return f"2026-H-{state}-{dist}"

    # Title fallback: "{State} Senate race", "{State} Governor", etc.
    title_lower = series_title.lower()
    for abbrev, full in STATE_ABBREV_MAP.items():
        if full.lower() in title_lower:
            if "senate" in title_lower:
                return f"2026-SEN-{abbrev}"
            if "governor" in title_lower or "gubernat" in title_lower:
                return f"2026-GOV-{abbrev}"
            if "house" in title_lower or "congressional" in title_lower:
                # Can't determine district from title alone
                pass

    return None


def parse_market_row(event: dict, market: dict, series_ticker: str, series_title: str) -> dict:
    """Flatten a Kalshi market into a standard row."""
    race_id = infer_race_id(series_ticker, series_title)
    yes_ask = market.get("yes_ask")
    yes_bid = market.get("yes_bid")
    last_price = market.get("last_price")

    # Implied probability: midpoint of bid/ask, fallback to last_price (scale: 0-100)
    if yes_ask is not None and yes_bid is not None:
        implied_prob = (yes_ask + yes_bid) / 2 / 100
    elif last_price is not None:
        implied_prob = last_price / 100
    else:
        implied_prob = None

    return {
        "race_id": race_id,
        "source": "kalshi",
        "series_ticker": series_ticker,
        "series_title": series_title,
        "event_title": event.get("title"),
        "market_ticker": market.get("ticker"),
        "market_title": market.get("title"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last_price": last_price,
        "implied_prob": implied_prob,
        "open_interest": market.get("open_interest"),
        "volume": market.get("volume"),
        "status": market.get("status"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def run(delay: float = 0.3):
    """
    Fetch all Kalshi election markets and save to data/raw/kalshi_markets.csv.

    delay: seconds to sleep between series fetches (be polite).
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching Kalshi election series list...")
    series_list = fetch_all_series()
    print(f"  Found {len(series_list)} election-related series")

    rows = []
    for i, series in enumerate(series_list):
        ticker = series["ticker"]
        title = series.get("title", "")
        try:
            events = fetch_events_for_series(ticker)
        except Exception as e:
            print(f"  WARNING: failed to fetch events for {ticker}: {e}")
            continue

        for event in events:
            for market in event.get("markets", []):
                rows.append(parse_market_row(event, market, ticker, title))

        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(series_list)} series, {len(rows)} markets so far")
        time.sleep(delay)

    df = pd.DataFrame(rows)
    out_path = RAW_DATA_DIR / "kalshi_markets.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} market rows to {out_path}")

    # Print summary
    if "race_id" in df.columns:
        matched = df["race_id"].notna().sum()
        print(f"Matched to canonical race_id: {matched}/{len(df)}")
        print("\nSample of matched markets:")
        print(df[df["race_id"].notna()][["race_id", "market_title", "implied_prob"]].head(20).to_string(index=False))


if __name__ == "__main__":
    run()
