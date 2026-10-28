"""Record Kalshi and Polymarket prices for the competitive races on election night.

capture_live.py records the count (NYT, every county); this records what the markets
were paying at the same moments, so the live projector can be compared with the price
and so we can see afterwards where the markets misread the count. Every INTERVAL
seconds it saves each market's best bid/ask, sizes, last trade and the top 5 levels of
each side of the book, one row per market:
    data/raw/markets/{date}/{kalshi,polymarket}.csv      (appended, flushed every pass)
Prices are dollars per $1 contract for the market's YES side.

    py "Election night simulator/scripts/capture_markets.py"            # until Ctrl+C
    py "Election night simulator/scripts/capture_markets.py" --once     # one pass (test)

Markets are found from a reviewed list of EVENTS (event tickers are not predictable:
Kansas Governor is GOVPARTYKS-27, inaugurated 2027) and every live market in each event
is recorded; Polymarket's placeholder outcomes ("Candidate C", no bid) are skipped. The
list is re-read from the APIs every REDISCOVER seconds, so a market added late is picked up.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "markets")
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from utils.http_headers import DEFAULT_HEADERS  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
INTERVAL = 20
REDISCOVER = 1800
LEVELS = 5
KALSHI_GAP = 0.12          # seconds between Kalshi requests (a fast burst got HTTP 429)

# race key (as in capture_live.py) -> (Kalshi event ticker, Polymarket event slug);
# checked against both APIs 2026-10-28. Both venues list party markets except Polymarket
# Alaska (per candidate) and Nebraska (Republican / independent: Osborn).
RACES = {
    "AK-Sen": ("SENATEAK-26", "alaska-senate-election-winner"),
    "GA-Gov": ("GOVPARTYGA-26", "georgia-governor-winner-2026"),
    "OH-Gov": ("GOVPARTYOH-26", "ohio-governor-winner-2026"),
    "OH-Sen": ("SENATEOHS-26", "ohio-senate-election-winner"),
    "KS-Sen": ("SENATEKS-26", "kansas-senate-election-winner"),
    "KS-Gov": ("GOVPARTYKS-27", "kansas-governor-winner-2026"),
    "SC-Sen": ("SENATESC-26", "south-carolina-senate-election-winner"),
    "TX-Sen": ("SENATETX-26", "texas-senate-election-winner"),
    "NE-Sen": ("SENATENE-26", "nebraska-senate-election-winner"),
    "ME-Sen": ("SENATEME-26", "maine-senate-election-winner"),
    "IA-Sen": ("SENATEIA-26", "iowa-senate-election-winner"),
    "MI-Sen": ("SENATEMI-26", "michigan-senate-election-winner"),
    "NV-Gov": ("GOVPARTYNV-26", "nevada-governor-winner-2026"),
    "OR-Gov": ("GOVPARTYOR-26", "oregon-governor-winner-2026"),
    "TX-Gov": ("GOVPARTYTX-26", "texas-governor-winner-2026"),
    # chamber control: the whole night's news in one price, a check on the state markets
    "US-Senate": ("CONTROLS-2026", "which-party-will-win-the-senate-in-2026"),
    "US-House": ("CONTROLH-2026", "which-party-will-win-the-house-in-2026"),
}

FIELDS = ["ts_utc", "race", "market", "outcome", "bid", "ask", "bid_size", "ask_size",
          "last", "volume", "bids", "asks"]


def get(url, body=None, tries=3):
    headers = dict(DEFAULT_HEADERS)
    if body is not None:
        headers["Content-Type"] = "application/json"
    for i in range(tries):
        req = urllib.request.Request(url, headers=headers,
                                     data=None if body is None else json.dumps(body).encode())
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i + 1 < tries:
                time.sleep(2 * (i + 1))
                continue
            raise


def _f(x):
    try:
        return None if x is None or x == "" else float(x)
    except (TypeError, ValueError):
        return None


def _levels(pairs):
    """[(price, size)] best first -> '0.64:540|0.63:120|...' (top LEVELS)."""
    return "|".join(f"{p:g}:{round(s, 2):.12g}" for p, s in pairs[:LEVELS])


def discover(races):
    """-> (kalshi [{race, ticker, outcome}], polymarket [{race, token, market, outcome}])."""
    kal, poly = [], []
    for race, (kev, pslug) in races.items():
        try:
            ev = get(f"{KALSHI}/events/{kev}?with_nested_markets=true")["event"]
            for m in ev["markets"]:
                if m.get("status") == "active":
                    kal.append(dict(race=race, ticker=m["ticker"],
                                    outcome=m.get("yes_sub_title") or m.get("title")))
        except Exception as e:
            print(f"discover {race} kalshi {kev}: {e}")
        time.sleep(KALSHI_GAP)
        try:
            for ev in get(f"{GAMMA}/events?slug={pslug}"):
                for m in ev["markets"]:
                    # placeholders ("Candidate C", "Party A") never have a bid
                    if (not m.get("active") or m.get("closed")
                            or _f(m.get("bestBid")) in (None, 0.0)):
                        continue
                    tok = json.loads(m["clobTokenIds"])[0]          # YES token
                    poly.append(dict(race=race, token=tok, market=m["slug"],
                                     outcome=m.get("groupItemTitle") or m["question"]))
        except Exception as e:
            print(f"discover {race} polymarket {pslug}: {e}")
    return kal, poly


def poll_kalshi(kal, now):
    rows = []
    summary = {}
    tickers = [m["ticker"] for m in kal]
    for i in range(0, len(tickers), 50):
        for m in get(f"{KALSHI}/markets?tickers={','.join(tickers[i:i + 50])}")["markets"]:
            summary[m["ticker"]] = m
        time.sleep(KALSHI_GAP)
    for m in kal:
        t = m["ticker"]
        try:
            ob = get(f"{KALSHI}/markets/{t}/orderbook?depth={LEVELS}")["orderbook_fp"]
        except Exception as e:
            print(f"{now} kalshi {t}: {e}")
            continue
        finally:
            time.sleep(KALSHI_GAP)
        # each side is [[price, size]] ascending; a NO bid at p is a YES ask at 1 - p
        yes = sorted(((_f(p), _f(s)) for p, s in ob.get("yes_dollars") or []), reverse=True)
        no = sorted(((_f(p), _f(s)) for p, s in ob.get("no_dollars") or []), reverse=True)
        asks = [(round(1 - p, 4), s) for p, s in no]
        s = summary.get(t, {})
        rows.append(dict(ts_utc=now, race=m["race"], market=t, outcome=m["outcome"],
                         bid=yes[0][0] if yes else None, ask=asks[0][0] if asks else None,
                         bid_size=yes[0][1] if yes else None,
                         ask_size=asks[0][1] if asks else None,
                         last=_f(s.get("last_price_dollars")), volume=_f(s.get("volume_fp")),
                         bids=_levels(yes), asks=_levels(asks)))
    return rows


def poll_polymarket(poly, now):
    rows = []
    by_tok = {m["token"]: m for m in poly}
    toks = list(by_tok)
    # the book's own last_trade_price is the event's, not this token's (Rogers and
    # El-Sayed both showed 0.70); /last-trades-prices is per token
    last = {}
    for i in range(0, len(toks), 100):
        try:
            for x in get(f"{CLOB}/last-trades-prices", [{"token_id": t} for t in toks[i:i + 100]]):
                last[x.get("token_id")] = _f(x.get("price"))
        except Exception as e:
            print(f"{now} polymarket last trades: {e}")
    for i in range(0, len(toks), 100):
        for b in get(f"{CLOB}/books", [{"token_id": t} for t in toks[i:i + 100]]):
            m = by_tok.get(b.get("asset_id"))
            if not m:
                continue
            bids = sorted(((_f(x["price"]), _f(x["size"])) for x in b.get("bids") or []),
                          reverse=True)
            asks = sorted((_f(x["price"]), _f(x["size"])) for x in b.get("asks") or [])
            rows.append(dict(ts_utc=now, race=m["race"], market=m["market"],
                             outcome=m["outcome"],
                             bid=bids[0][0] if bids else None, ask=asks[0][0] if asks else None,
                             bid_size=bids[0][1] if bids else None,
                             ask_size=asks[0][1] if asks else None,
                             last=last.get(b.get("asset_id")), volume=None,
                             bids=_levels(bids), asks=_levels(asks)))
    return rows


def write(date, venue, rows):
    if not rows:
        return
    d = os.path.join(OUT, date)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{venue}.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)


def keep_awake():
    """Hold off sleep while recording, as capture_live.py does: this PC sleeps in Modern Standby,
    which suspends background programs. Leave the lid open and the PC plugged in."""
    if os.name == "nt":
        import ctypes
        if not ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001):
            print("WARNING: could not hold off sleep; keep the PC awake by hand")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=INTERVAL)
    ap.add_argument("--until", help="stop at this UTC time, e.g. 2026-11-06T17:00")
    a = ap.parse_args()
    until = dt.datetime.fromisoformat(a.until).replace(tzinfo=dt.timezone.utc) if a.until else None
    if not a.once:
        keep_awake()
    kal, poly, found_at = [], [], 0.0
    while True:
        start = time.time()
        if start - found_at > REDISCOVER or not (kal or poly):
            kal, poly = discover(RACES)
            found_at = start
            print(f"discovered {len(kal)} Kalshi and {len(poly)} Polymarket markets")
        now_dt = dt.datetime.now(dt.timezone.utc)
        now = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        # files by US Eastern date (UTC-5 in November), so election night is one file
        date = (now_dt - dt.timedelta(hours=5)).strftime("%Y-%m-%d")
        for venue, fn, mk in (("kalshi", poll_kalshi, kal), ("polymarket", poll_polymarket, poly)):
            try:
                rows = fn(mk, now)
                write(date, venue, rows)
                print(f"{now} {venue}: {len(rows)} markets")
            except Exception as e:
                print(f"{now} {venue}: error {e}")
        sys.stdout.flush()
        if a.once or (until and dt.datetime.now(dt.timezone.utc) >= until):
            break
        time.sleep(max(1.0, a.interval - (time.time() - start)))


if __name__ == "__main__":
    main()
