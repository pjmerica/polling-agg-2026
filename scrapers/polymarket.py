"""
Polymarket prediction market scraper.

Polymarket has a public REST API — no auth required for read operations.
Gamma API base: https://gamma-api.polymarket.com/

Key findings from API exploration (2026-04-07):
  - The `tag` and `category` filters are largely ineffective — most markets
    have empty category fields. Filtering by question text is more reliable.
  - 2026 election markets are sparse (~17 in first 1000 active markets).
    Mostly control questions (who wins Senate/House) and primary races.
  - Prices are in decimal probability form (0.0 - 1.0), e.g. 0.87 = 87%.
  - Markets with prices ["0", "0"] are closed/resolved with no current market.

Pagination: use offset parameter, stop when batch < limit.

Market object key fields (verified):
  id, question, conditionId, slug, endDate, liquidity, startDate,
  image, icon, description, outcomes, outcomePrices, volume, active,
  marketType, closed, resolutionSource
"""

import time
import urllib.request
import urllib.parse
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
GAMMA_BASE = "https://gamma-api.polymarket.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (research/polling-aggregator)"}

# Keywords to identify US election markets by question text
ELECTION_KEYWORDS = [
    "senate", "senator", "governor", "gubernatorial",
    "house seat", "congressional district", "congress",
    "win the seat", "2026 midterm", "2026 election",
    "control the senate", "control the house",
    "balance of power",
]

# Keywords that look like election but are NOT US races
EXCLUDE_KEYWORDS = [
    "nhl", "nba", "nfl", "mlb", "soccer", "stanley cup",
    "premier league", "world cup",
]


def _get(path: str, params: dict = None) -> list | dict:
    url = f"{GAMMA_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_all_active_markets(limit: int = 100) -> list[dict]:
    """
    Paginate through ALL active Polymarket markets.
    Returns only election-related ones.
    """
    all_markets = []
    offset = 0
    page = 0

    while True:
        batch = _get("/markets", {"limit": limit, "active": "true", "closed": "false", "offset": offset})
        if not batch:
            break

        for m in batch:
            q = m.get("question", "").lower()
            if (
                any(k in q for k in ELECTION_KEYWORDS)
                and not any(k in q for k in EXCLUDE_KEYWORDS)
            ):
                all_markets.append(m)

        page += 1
        if len(batch) < limit:
            break
        offset += limit

        if page % 10 == 0:
            print(f"  Scanned {offset} markets, found {len(all_markets)} election markets so far")

    return all_markets


def parse_market(m: dict) -> dict:
    """Flatten a Polymarket market into a standard row."""
    outcomes = m.get("outcomes", [])
    prices = m.get("outcomePrices", [])

    # Build outcome->price pairs
    outcome_price_pairs = {}
    if outcomes and prices and len(outcomes) == len(prices):
        for o, p in zip(outcomes, prices):
            try:
                outcome_price_pairs[o] = float(p)
            except (ValueError, TypeError):
                outcome_price_pairs[o] = None

    # For Yes/No markets, extract the "Yes" price as implied_prob
    implied_prob = None
    if "Yes" in outcome_price_pairs:
        implied_prob = outcome_price_pairs["Yes"]
    elif len(outcome_price_pairs) == 2:
        # Take the first non-"No" outcome
        for k, v in outcome_price_pairs.items():
            if k.lower() != "no":
                implied_prob = v
                break

    return {
        "source": "polymarket",
        "condition_id": m.get("conditionId"),
        "market_id": m.get("id"),
        "question": m.get("question"),
        "end_date": m.get("endDate"),
        "active": m.get("active"),
        "closed": m.get("closed"),
        "market_type": m.get("marketType"),
        "liquidity": m.get("liquidity"),
        "volume": m.get("volume"),
        "outcomes": "|".join(str(o) for o in outcomes),
        "prices": "|".join(str(p) for p in prices),
        "implied_prob": implied_prob,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        # race_id: left null here — matching to canonical IDs is done in analysis/aggregator.py
        # Polymarket markets are mostly control/primary questions, not individual race winners yet
    }


def run():
    """Fetch Polymarket election markets and save to data/raw/polymarket_markets.csv."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Scanning Polymarket for election markets (paginating all active markets)...")
    markets = fetch_all_active_markets()
    print(f"  Found {len(markets)} election-related markets")

    if not markets:
        print("No markets found. Polymarket 2026 election coverage may be sparse this far out.")
        return

    rows = [parse_market(m) for m in markets]
    df = pd.DataFrame(rows).drop_duplicates(subset=["condition_id"])
    out_path = RAW_DATA_DIR / "polymarket_markets.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} markets to {out_path}")
    print("\nMarket questions found:")
    for q in df["question"].tolist():
        print(f"  - {q}")


if __name__ == "__main__":
    run()
