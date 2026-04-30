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
import re
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
# (e.g. "Ottawa Senators vs. Hurricanes" hits "senator" keyword → filter out)
EXCLUDE_KEYWORDS = [
    "nhl", "nba", "nfl", "mlb", "ahl", "mls", "soccer", "stanley cup",
    "premier league", "world cup", " vs.", " vs ", "o/u ",
    "spread:", "over/under", "puck line", "moneyline", "ml (",
]

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

# State abbreviation patterns in questions like "NY-16", "CA-37"
STATE_ABBREVS = set(STATE_NAME_TO_ABBREV.values())


def infer_race_id(question: str) -> str | None:
    """Map a Polymarket question to a canonical race_id."""
    q = question.lower()

    # Skip control/balance-of-power questions
    if any(k in q for k in ["control the", "balance of power", "how many seats", "which party will win the"]):
        return None

    # House: patterns like "NY-16 House seat", "CA-37 house", "AZ-07"
    m = re.search(r'\b([A-Z]{2})-(\d{1,2})\b', question)
    if m:
        sa = m.group(1)
        dist = str(int(m.group(2))).zfill(2)
        if sa in STATE_ABBREVS:
            return f"2026-H-{sa}-{dist}"

    # Find state by full name. Sort longest-first so multi-word names like
    # "west virginia" / "new hampshire" / "north carolina" match before
    # their substrings ("virginia", "hampshire", "carolina") trigger first.
    state_abbrev = None
    for name, abbrev in sorted(STATE_NAME_TO_ABBREV.items(), key=lambda kv: -len(kv[0])):
        if name in q:
            state_abbrev = abbrev
            break

    if not state_abbrev:
        return None

    # Senate
    if "senate" in q or "senator" in q:
        if state_abbrev == "FL" and "special" in q:
            return f"2026-SEN-FL-S"
        if state_abbrev == "OH" and "special" in q:
            return f"2026-SEN-OH-S"
        return f"2026-SEN-{state_abbrev}"

    # Governor
    if "governor" in q or "gubernatorial" in q or "governor election" in q:
        return f"2026-GOV-{state_abbrev}"

    # House with district number in text
    m2 = re.search(r"(\d+)(?:st|nd|rd|th)?\s*(?:congressional\s*)?district", q)
    if m2 and ("house" in q or "congressional" in q or "district" in q):
        dist = str(int(m2.group(1))).zfill(2)
        return f"2026-H-{state_abbrev}-{dist}"

    return None


def _get(path: str, params: dict = None) -> list | dict:
    url = f"{GAMMA_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def fetch_all_active_markets(limit: int = 100) -> list[dict]:
    """
    Paginate through ALL active Polymarket events; flatten into markets.
    Each market is annotated with its parent event_slug so we can build
    working polymarket.com/event/{slug} URLs.
    Returns only election-related markets.
    """
    all_markets = []
    offset = 0
    page = 0

    while True:
        batch = _get("/events", {"limit": limit, "active": "true", "closed": "false", "offset": offset})
        if not batch:
            break

        for event in batch:
            event_slug = event.get("slug", "") or ""
            event_title = event.get("title", "") or ""
            for m in event.get("markets", []) or []:
                q = m.get("question", "").lower()
                t = event_title.lower()
                combined = q + " " + t
                if (
                    any(k in combined for k in ELECTION_KEYWORDS)
                    and not any(k in combined for k in EXCLUDE_KEYWORDS)
                ):
                    m["_event_slug"] = event_slug
                    m["_event_title"] = event_title
                    all_markets.append(m)

        page += 1
        if len(batch) < limit:
            break
        offset += limit

        if page % 10 == 0:
            print(f"  Scanned {offset} events, found {len(all_markets)} election markets so far")

    return all_markets


def parse_market(m: dict) -> dict:
    """Flatten a Polymarket market into a standard row."""
    outcomes = m.get("outcomes", [])
    prices = m.get("outcomePrices", [])

    # Gamma returns these as JSON-encoded strings ('["Yes","No"]'), not lists.
    # Without this parse, zip(outcomes, prices) iterates characters of the
    # string and produces garbage, leaving implied_prob=None and falling back
    # to lastTradePrice — which can be days stale, producing fake arbs.
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (ValueError, TypeError):
            outcomes = []
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except (ValueError, TypeError):
            prices = []

    # Build outcome->price pairs
    outcome_price_pairs = {}
    if outcomes and prices and len(outcomes) == len(prices):
        for o, p in zip(outcomes, prices):
            try:
                outcome_price_pairs[o] = float(p)
            except (ValueError, TypeError):
                outcome_price_pairs[o] = None

    # Pick implied_prob with this priority:
    #   1. midpoint of bestBid + bestAsk           (live orderbook, freshest)
    #   2. bestAsk alone                            (only ask side)
    #   3. bestBid alone                            (only bid side)
    #   4. outcomePrices "Yes"                      (gamma snapshot, can be stale)
    #   5. lastTradePrice                           (worst — can be days stale)
    # The earlier code went straight to outcomePrices then lastTradePrice. For
    # low-volume markets that's wildly stale: gamma reported outcomePrices
    # ["0.43","0.57"] for a market whose live ask was $0.86, producing fake
    # 40pp arbs against Kalshi.
    implied_prob = None
    bb = m.get("bestBid")
    ba = m.get("bestAsk")
    try:
        bb = float(bb) if bb is not None else None
    except (TypeError, ValueError):
        bb = None
    try:
        ba = float(ba) if ba is not None else None
    except (TypeError, ValueError):
        ba = None
    # Require BOTH a bid AND an ask. A one-sided quote is a stale standing
    # order, not a real market — using it pairs against other platforms'
    # tight quotes and produces fake arbs (e.g. a lone $0.86 sell order
    # sitting on a dead market).
    if bb is not None and ba is not None and 0 < bb <= ba < 1:
        # Wide spread (>10pp) means the midpoint is fictional; only the ask
        # is actually fillable. Use ask to be conservative.
        if (ba - bb) > 0.10:
            implied_prob = ba
        else:
            implied_prob = round((bb + ba) / 2, 4)

    if implied_prob is None and "Yes" in outcome_price_pairs:
        implied_prob = outcome_price_pairs["Yes"]
    elif implied_prob is None and len(outcome_price_pairs) == 2:
        for k, v in outcome_price_pairs.items():
            if k.lower() != "no":
                implied_prob = v
                break

    question = m.get("question", "")
    race_id = infer_race_id(question)

    # Last resort: lastTradePrice (often days stale on low-volume markets)
    if implied_prob is None:
        implied_prob = m.get("lastTradePrice")

    event_slug = m.get("_event_slug", "") or ""
    market_slug = m.get("slug", "") or ""
    url_slug = event_slug or market_slug

    # clobTokenIds: comes back as a JSON-encoded string like '["yes_id","no_id"]'
    # or a real list. Outcome order in `outcomes` aligns with token order.
    raw_tokens = m.get("clobTokenIds")
    yes_token = no_token = None
    try:
        tokens = json.loads(raw_tokens) if isinstance(raw_tokens, str) else raw_tokens
        if isinstance(tokens, list) and len(tokens) >= 2 and outcomes and len(outcomes) >= 2:
            for o, tid in zip(outcomes, tokens):
                if str(o).lower() == "yes":
                    yes_token = tid
                elif str(o).lower() == "no":
                    no_token = tid
            if yes_token is None and no_token is None:
                yes_token, no_token = tokens[0], tokens[1]
    except (ValueError, TypeError):
        pass

    return {
        "source": "polymarket",
        "condition_id": m.get("conditionId"),
        "market_id": m.get("id"),
        "question": question,
        "race_id": race_id,
        "end_date": m.get("endDate"),
        "active": m.get("active"),
        "closed": m.get("closed"),
        "market_type": m.get("marketType"),
        "liquidity": m.get("liquidity"),
        "volume": m.get("volume"),
        "best_ask": m.get("bestAsk"),
        "best_bid": m.get("bestBid"),
        "implied_prob": implied_prob,
        "yes_token_id": yes_token,
        "no_token_id": no_token,
        "event_slug": event_slug,
        "market_slug": market_slug,
        "url_slug": url_slug,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
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

    # Drop unrealistic markets:
    #   1. Liquidity < $200 — basically no real trading
    #   2. Spread (best_ask - best_bid) > 30pp — only one-sided standing
    #      orders, no two-sided market. Pairing these against active
    #      Kalshi markets produces fake 80%+ "guaranteed" arbs against
    #      a $0.97 sell order that nothing would actually fill.
    if "liquidity" in df.columns:
        liq = pd.to_numeric(df["liquidity"], errors="coerce").fillna(0)
        bb = pd.to_numeric(df.get("best_bid"), errors="coerce")
        ba = pd.to_numeric(df.get("best_ask"), errors="coerce")
        has_two_sided = bb.notna() & ba.notna() & ((ba - bb) <= 0.20)
        before = len(df)
        df = df[(liq >= 200) & has_two_sided]
        print(f"  Dropped {before - len(df)} markets (liquidity<$200 or spread>30pp)")

    out_path = RAW_DATA_DIR / "polymarket_markets.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} markets to {out_path}")
    print("\nMarket questions found:")
    for q in df["question"].tolist():
        print(f"  - {q}")


if __name__ == "__main__":
    run()
