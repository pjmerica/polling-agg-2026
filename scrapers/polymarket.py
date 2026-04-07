"""
Polymarket prediction market scraper.

Polymarket has a public REST API — no auth required for read operations.

Docs: https://docs.polymarket.com/
CLOB API base: https://clob.polymarket.com/
Gamma (markets) API base: https://gamma-api.polymarket.com/

Useful endpoints:
  GET https://gamma-api.polymarket.com/markets
    ?tag=politics           filter by tag
    ?limit=100              pagination
    ?offset=0
    Returns list of market objects

  GET https://gamma-api.polymarket.com/markets/{condition_id}
    Single market details including current prices

  GET https://clob.polymarket.com/prices-history?market={token_id}&...
    Price history for a market token

Market object key fields:
  condition_id, question, description, end_date_iso,
  active, closed, tags,
  outcomes (list of strings, e.g. ["Yes","No"] or candidate names),
  outcomePrices (list of current prices, implied probabilities)

TODO: Build a tag/keyword filter to find all US election markets.
      Tags to try: "politics", "elections", "2026-elections", "us-senate", "us-governor"
      Also search by question text containing state names + "Senate"/"Governor"
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

GAMMA_BASE = "https://gamma-api.polymarket.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (research/polling-aggregator)"}

ELECTION_TAGS = ["politics", "elections"]  # TODO: verify correct tag names for 2026


def fetch_markets(tag: str = "politics", limit: int = 100) -> list[dict]:
    """
    Fetch all active markets for a given tag, handling pagination.

    TODO: Verify tag names by browsing https://polymarket.com and inspecting
    the Network tab for the tag used in election market URLs.
    """
    markets = []
    offset = 0
    while True:
        url = f"{GAMMA_BASE}/markets"
        params = {"tag": tag, "limit": limit, "offset": offset, "active": "true"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        markets.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return markets


def filter_election_markets(markets: list[dict]) -> list[dict]:
    """
    Filter markets down to US Senate, Governor, and House races.

    TODO: Refine these keywords once we see actual market question text.
    """
    keywords = [
        "senate", "senator", "governor", "gubernatorial",
        "house of representatives", "congressional"
    ]
    result = []
    for m in markets:
        q = m.get("question", "").lower()
        if any(kw in q for kw in keywords):
            result.append(m)
    return result


def parse_market(m: dict) -> dict:
    """
    Flatten a Polymarket market object to a standard row.

    TODO: Map to canonical race_id once utils/races.py exists.
    """
    outcomes = m.get("outcomes", [])
    prices = m.get("outcomePrices", [])

    return {
        "condition_id": m.get("conditionId") or m.get("condition_id"),
        "question": m.get("question"),
        "end_date": m.get("endDateIso") or m.get("end_date_iso"),
        "active": m.get("active"),
        "closed": m.get("closed"),
        "outcomes": "|".join(outcomes) if outcomes else None,
        "prices": "|".join(str(p) for p in prices) if prices else None,
        "fetched_at": datetime.utcnow().isoformat(),
        # TODO: add race_id matched from utils/races.py
    }


def run():
    """Fetch Polymarket election markets and save to CSV."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_markets = []
    for tag in ELECTION_TAGS:
        print(f"Fetching Polymarket markets with tag='{tag}'...")
        # TODO: uncomment once tags are verified
        # markets = fetch_markets(tag=tag)
        # election_markets = filter_election_markets(markets)
        # all_markets.extend(election_markets)
        # print(f"  Found {len(election_markets)} election markets (tag={tag})")
        print(f"  TODO: verify tag name '{tag}' at https://polymarket.com")

    if all_markets:
        rows = [parse_market(m) for m in all_markets]
        df = pd.DataFrame(rows).drop_duplicates(subset=["condition_id"])
        df.to_csv(RAW_DATA_DIR / "polymarket_markets.csv", index=False)
        print(f"Saved {len(df)} markets to data/raw/polymarket_markets.csv")


if __name__ == "__main__":
    run()
