"""
PredictIt prediction market scraper.

PredictIt has a public REST API — no auth required.
Base URL: https://www.predictit.org/api/marketdata/

Key endpoints:
  GET /api/marketdata/all/
    All active markets with nested contracts.

Market structure:
  - Each market has multiple contracts (e.g. "Democratic", "Republican")
  - Each contract has: lastTradePrice, bestBuyYesCost, bestSellYesCost
  - Prices are 0.0-1.0 (e.g. 0.84 = 84 cents = 84% implied prob)

Race identification:
  Market names follow patterns like:
    "Which party will win the 2026 US Senate election in Georgia?"
    "Which party will win the 2026 election for governor of California?"
    "Which party will win the 2026 US House election in Pennsylvania's 7th district?"

Output: data/raw/predictit_markets.csv
"""

import urllib.request
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
PREDICTIT_URL = "https://www.predictit.org/api/marketdata/all/"
HEADERS = {"User-Agent": "Mozilla/5.0 (research/polling-aggregator)", "Accept": "application/json"}

STATE_NAME_TO_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}

ELECTION_KEYWORDS = [
    "2026", "senate", "governor", "house", "midterm", "congressional"
]

EXCLUDE_KEYWORDS = [
    "how many", "which party will control", "how many seats", "which party will win the house",
    "which party will win the senate",
]


def fetch_all_markets() -> list[dict]:
    req = urllib.request.Request(PREDICTIT_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read()).get("markets", [])


def infer_race_id(name: str) -> str | None:
    """
    Map a PredictIt market name to a canonical race_id.

    Handles patterns like:
      "Which party will win the 2026 US Senate election in Georgia?"
      "Which party will win the 2026 election for governor of California?"
      "Which party will win the 2026 US House election in Pennsylvania's 7th district?"
      "Which party will win the 2026 US Senate election in Florida?" (special)
    """
    name_lower = name.lower()

    # Find state. Sort longest-first so multi-word names ("west virginia",
    # "new hampshire", "north carolina") match before their substrings.
    state_abbrev = None
    for state_name, abbrev in sorted(STATE_NAME_TO_ABBREV.items(), key=lambda kv: -len(kv[0])):
        if state_name in name_lower:
            state_abbrev = abbrev
            break
    if not state_abbrev:
        return None

    # Determine office
    if "senate" in name_lower:
        # Check for special elections
        if state_abbrev == "FL":
            return "2026-SEN-FL-S"
        if state_abbrev == "OH":
            return "2026-SEN-OH-S"
        return f"2026-SEN-{state_abbrev}"

    if "governor" in name_lower or "gubernatorial" in name_lower:
        return f"2026-GOV-{state_abbrev}"

    if "house" in name_lower or "congressional" in name_lower or "district" in name_lower:
        # Try to extract district number
        m = re.search(r"(\d+)(?:st|nd|rd|th)?\s*(?:congressional\s*)?district", name_lower)
        if m:
            district = str(int(m.group(1))).zfill(2)
            return f"2026-H-{state_abbrev}-{district}"
        # No district found — can't map to specific race
        return None

    return None


def parse_contract(market: dict, contract: dict, race_id: str | None) -> dict:
    last = contract.get("lastTradePrice")
    buy_yes = contract.get("bestBuyYesCost")
    sell_yes = contract.get("bestSellYesCost")

    # Implied prob: midpoint of buy/sell if available, else last trade
    if buy_yes is not None and sell_yes is not None:
        implied_prob = (buy_yes + sell_yes) / 2
    elif last is not None:
        implied_prob = last
    else:
        implied_prob = None

    return {
        "race_id": race_id,
        "source": "predictit",
        "market_id": market.get("id"),
        "market_name": market.get("name"),
        "contract_id": contract.get("id"),
        "contract_name": contract.get("name"),
        "last_trade_price": last,
        "best_buy_yes": buy_yes,
        "best_sell_yes": sell_yes,
        "implied_prob": round(implied_prob, 4) if implied_prob is not None else None,
        "status": market.get("status"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching PredictIt markets...")
    all_markets = fetch_all_markets()
    print(f"  Total markets: {len(all_markets)}")

    # Filter to election-related
    election_markets = [
        m for m in all_markets
        if any(k in m.get("name", "").lower() for k in ELECTION_KEYWORDS)
        and not any(k in m.get("name", "").lower() for k in EXCLUDE_KEYWORDS)
    ]
    print(f"  Election-related: {len(election_markets)}")

    rows = []
    for market in election_markets:
        race_id = infer_race_id(market.get("name", ""))
        for contract in market.get("contracts", []):
            rows.append(parse_contract(market, contract, race_id))

    df = pd.DataFrame(rows)
    out_path = RAW_DATA_DIR / "predictit_markets.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} contract rows to {out_path}")

    matched = df["race_id"].notna().sum()
    print(f"Matched to canonical race_id: {matched}/{len(df)}")

    print("\nSample matched contracts:")
    sample = df[df["race_id"].notna()][["race_id", "contract_name", "implied_prob"]].head(20)
    print(sample.to_string(index=False))


if __name__ == "__main__":
    run()
