"""
Kalshi prediction market scraper.

Public REST API for elections, no auth required for reads.

Base URL: https://api.elections.kalshi.com/trade-api/v2/

Key endpoints:
  GET /series?category=Politics
    All Politics-category series in one response (no pagination).

  GET /events?series_ticker={ticker}&with_nested_markets=true
    Events under a series, with markets nested inside each event.
    Market fields used here: ticker, title, yes_bid_dollars, yes_ask_dollars,
    last_price_dollars, yes_bid_size_fp, yes_ask_size_fp, liquidity_dollars,
    open_interest_fp, volume_fp, status

  GET /markets/{ticker}/orderbook?depth=N
    Full orderbook ladder. Used by scripts/fetch_depth.py for matched markets.

Prices on v2 are decimals 0.0000-1.0000 (string-encoded). Sizes are in
contracts ($1 max payout each).

Race identification: see infer_race_id() — pattern-matches series tickers
to canonical race_ids defined in utils/races.py.
"""

import time
import urllib.request
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
HEADERS = {"User-Agent": "Mozilla/5.0 (research/polling-aggregator)", "Accept": "application/json"}

# Keywords to identify 2026 election series (filter against 1800+ Politics series)
ELECTION_KEYWORDS = [
    "senate", "governor", "house", "midterm", "2026",
    "senateparty", "govparty", "houseaz", "housenc", "housega",
    "housetx", "housemi", "houseca", "houseny", "housepa",
    "houseva", "housefl", "housewi", "houseoh", "housemo",
    "primary", "nominee", "nomination",
]

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
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def fetch_all_series() -> list[dict]:
    """Fetch all Elections + Politics series, filtered to election-related."""
    out = []
    seen = set()
    for category in ("Elections", "Politics"):
        data = _get("/series", {"category": category, "limit": "2000"})
        for s in data.get("series", []):
            ticker = (s.get("ticker") or "")
            if ticker in seen:
                continue
            t_lower = ticker.lower()
            title_lower = (s.get("title") or "").lower()
            if category == "Elections" or any(k in t_lower or k in title_lower for k in ELECTION_KEYWORDS):
                out.append(s)
                seen.add(ticker)
    return out


def fetch_events_for_series(series_ticker: str) -> list[dict]:
    """Fetch events with nested markets for a series."""
    data = _get("/events", {
        "series_ticker": series_ticker,
        "with_nested_markets": "true",
        "limit": "200",
    })
    return data.get("events", [])


def infer_race_id(series_ticker: str, series_title: str) -> str | None:
    """
    Map a Kalshi series ticker/title to a canonical race_id like "2026-SEN-PA".
    Returns None if no pattern matches.
    """
    ticker = (series_ticker or "").upper()

    m = re.match(r"SENATEPARTY[-_]?([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    m = re.match(r"SENATE[-_]?([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    m = re.match(r"KXSENATE([A-Z]{2})([A-Z]?)$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    m = re.match(r"KXSENATE([A-Z]{2})$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-SEN-{m.group(1)}"

    m = re.match(r"GOVPARTY([A-Z]{2})(?:[A-Z0-9]*)?$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-GOV-{m.group(1)}"

    m = re.match(r"KXGOV([A-Z]{2})[A-Z0-9]+$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        return f"2026-GOV-{m.group(1)}"

    m = re.match(r"HOUSE([A-Z]{2})(\d+)$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        state = m.group(1)
        dist = m.group(2).zfill(2)
        return f"2026-H-{state}-{dist}"

    m = re.match(r"KXHOUSE([A-Z]{2})(\d+)$", ticker)
    if m and m.group(1) in STATE_ABBREV_MAP:
        state = m.group(1)
        dist = m.group(2).zfill(2)
        return f"2026-H-{state}-{dist}"

    title_lower = (series_title or "").lower()
    for abbrev, full in STATE_ABBREV_MAP.items():
        if full.lower() in title_lower:
            if "senate" in title_lower:
                return f"2026-SEN-{abbrev}"
            if "governor" in title_lower or "gubernat" in title_lower:
                return f"2026-GOV-{abbrev}"

    return None


def _to_float(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_market_row(event: dict, market: dict, series_ticker: str, series_title: str) -> dict:
    """Flatten a v2 Kalshi market into a standard row."""
    race_id = infer_race_id(series_ticker, series_title)

    yes_bid = _to_float(market.get("yes_bid_dollars"))
    yes_ask = _to_float(market.get("yes_ask_dollars"))
    last_price = _to_float(market.get("last_price_dollars"))

    if yes_bid is not None and yes_ask is not None:
        implied_prob = (yes_bid + yes_ask) / 2
    elif last_price is not None:
        implied_prob = last_price
    else:
        implied_prob = None

    return {
        "race_id": race_id,
        "source": "kalshi",
        "series_ticker": series_ticker,
        "series_title": series_title,
        "event_ticker": event.get("event_ticker"),
        "event_title": event.get("title"),
        "market_ticker": market.get("ticker"),
        "market_title": market.get("title"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "last_price": last_price,
        "implied_prob": implied_prob,
        "yes_bid_size": _to_float(market.get("yes_bid_size_fp")),
        "yes_ask_size": _to_float(market.get("yes_ask_size_fp")),
        "liquidity_dollars": _to_float(market.get("liquidity_dollars")),
        "open_interest": _to_float(market.get("open_interest_fp")),
        "volume": _to_float(market.get("volume_fp")),
        "volume_24h": _to_float(market.get("volume_24h_fp")),
        "status": market.get("status"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def run(delay: float = 0.2):
    """Fetch all Kalshi election markets and save to data/raw/kalshi_markets.csv."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching Kalshi election series list (v2)...")
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

    if "race_id" in df.columns:
        matched = df["race_id"].notna().sum()
        print(f"Matched to canonical race_id: {matched}/{len(df)}")
        with_ticker = df["market_ticker"].notna().sum()
        print(f"With market_ticker populated: {with_ticker}/{len(df)}")
        print("\nSample of matched markets:")
        print(df[df["race_id"].notna()][["race_id", "market_ticker", "market_title", "implied_prob"]].head(10).to_string(index=False))


if __name__ == "__main__":
    run()
