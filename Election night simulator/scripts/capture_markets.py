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
# Kalshi market statuses worth recording: trading, paused ("inactive") or closed but not yet settled. Only "active"
# before 2026-11-03: a market caught paused at a discovery would have dropped out for 30 minutes.
KALSHI_KEEP = {"active", "open", "inactive", "closed"}

# race key (as in capture_live.py) -> (Kalshi event ticker, Polymarket event slug);
# checked against both APIs 2026-10-28. Both venues list party markets except Polymarket
# Alaska (per candidate) and Nebraska (Republican / independent: Osborn).
RACES = {
    "AK-Sen": ("SENATEAK-26", "alaska-senate-election-winner"),
    "GA-Gov": ("GOVPARTYGA-26", "georgia-governor-winner-2026"),
    "GA-Sen": ("SENATEGA-26", "georgia-senate-election-winner"),     # split-ticket view, 2026-11-02
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
    # every other Senate and Governor race (2026-11-03); None = no market found (KY-Sen on Kalshi; AK-Gov is
    # per candidate under ranked choice, left out)
    "AK-Gov": (None, None),
    "AL-Gov": ("GOVPARTYAL-26", "alabama-governor-winner-2026"),
    "AL-Sen": ("SENATEAL-26", "alabama-senate-election-winner-154"),
    "AR-Gov": ("GOVPARTYAR-26", "arkansas-governor-winner-2026"),
    "AR-Sen": ("SENATEAR-26", "arkansas-senate-election-winner"),
    "AZ-Gov": ("GOVPARTYAZ-26", "arizona-governor-winner-2026"),
    "CA-Gov": ("GOVPARTYCA-26", "california-governor-election-2026"),
    "CO-Gov": ("GOVPARTYCO-26", "colorado-governor-winner-2026"),
    "CO-Sen": ("SENATECO-26", "colorado-senate-election-winner"),
    "CT-Gov": ("GOVPARTYCT-26", "connecticut-governor-winner-2026"),
    "DE-Sen": ("SENATEDE-26", "delaware-senate-election-winner"),
    "FL-Gov": ("GOVPARTYFL-26", "florida-governor-winner-2026"),
    "FL-Sen": ("SENATEFLS-26", "florida-senate-election-winner"),
    "HI-Gov": ("GOVPARTYHI-26", "hawaii-governor-winner-2026"),
    "IA-Gov": ("GOVPARTYIA-26", "iowa-governor-winner-2026"),
    "ID-Gov": ("GOVPARTYID-26", "idaho-governor-winner-2026"),
    "ID-Sen": ("SENATEID-26", "idaho-senate-election-winner"),
    "IL-Gov": ("GOVPARTYIL-26", "illinois-governor-winner-2026"),
    "IL-Sen": ("SENATEIL-26", "illinois-senate-election-winner"),
    "KY-Sen": (None, "kentucky-senate-election-winner"),
    "LA-Sen": ("SENATELA-26", "louisiana-senate-election-winner"),
    "MA-Gov": ("GOVPARTYMA-26", "massachusetts-governor-winner-2026"),
    "MA-Sen": ("SENATEMA-26", "massachusetts-senate-election-winner"),
    "MD-Gov": ("GOVPARTYMD-26", "maryland-governor-winner-2026"),
    "ME-Gov": ("GOVPARTYME-26", "maine-governor-winner-2026"),
    "MI-Gov": ("GOVPARTYMI-26", "michigan-governor-winner-2026"),
    "MN-Gov": ("GOVPARTYMN-26", "minnesota-governor-winner-2026"),
    "MN-Sen": ("SENATEMN-26", "minnesota-senate-election-winner"),
    "MS-Sen": ("SENATEMS-26", "mississippi-senate-election-winner"),
    "MT-Sen": ("SENATEMT-26", "montana-senate-election-winner"),
    "NC-Sen": ("SENATENC-26", "north-carolina-senate-election-winner"),
    "NE-Gov": ("GOVPARTYNE-26", "nebraska-governor-winner-2026"),
    "NH-Gov": ("GOVPARTYNH-28", "new-hampshire-governor-winner-2026"),
    "NH-Sen": ("SENATENH-26", "new-hampshire-senate-election-winner"),
    "NJ-Sen": ("SENATENJ-26", "new-jersey-senate-election-winner"),
    "NM-Gov": ("GOVPARTYNM-26", "new-mexico-governor-winner-2026"),
    "NM-Sen": ("SENATENM-26", "new-mexico-senate-election-winner"),
    "NY-Gov": ("GOVPARTYNY-26", "new-york-governor-winner-2026"),
    "OK-Gov": ("GOVPARTYOK-26", "oklahoma-governor-winner-2026"),
    "OK-Sen": ("SENATEOK-26", "oklahoma-senate-election-winner"),
    "OR-Sen": ("SENATEOR-26", "oregon-senate-election-winner"),
    "PA-Gov": ("GOVPARTYPA-26", "pennsylvania-governor-winner-2026"),
    "RI-Gov": ("GOVPARTYRI-26", "rhode-island-governor-winner-2026"),
    "RI-Sen": ("SENATERI-26", "rhode-island-senate-election-winner"),
    "SC-Gov": ("GOVPARTYSC-26", "south-carolina-governor-winner-2026"),
    "SD-Gov": ("GOVPARTYSD-26", "south-dakota-governor-winner-2026"),
    "SD-Sen": ("SENATESD-26", "south-dakota-senate-election-winner"),
    "TN-Gov": ("GOVPARTYTN-26", "tennessee-governor-winner-2026"),
    "TN-Sen": ("SENATETN-26", "tennessee-senate-election-winner"),
    "VA-Sen": ("SENATEVA-26", "virginia-senate-election-winner"),
    "VT-Gov": ("GOVPARTYVT-26", "vermont-governor-winner-2026"),
    "WI-Gov": ("GOVPARTYWI-26", "wisconsin-governor-winner-2026"),
    "WV-Sen": ("SENATEWV-26", "west-virginia-senate-election-winner"),
    "WY-Gov": ("GOVPARTYWY-26", "wyoming-governor-winner-2026"),
    "WY-Sen": ("SENATEWY-26", "wyoming-senate-election-winner"),
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


def discover(races, prev=None):
    """-> (kalshi [{race, ticker, outcome}], polymarket [{race, token, market, outcome}]).
    prev = the last discovery's (kalshi, polymarket): a race whose lookup fails (or comes back empty) keeps
    its markets from it, so one API error doesn't drop that race's prices until the next discovery."""
    pk, pp = prev or ([], [])
    kal, poly = [], []
    for race, (kev, pslug) in races.items():
        found = []
        try:
            if not kev:
                raise LookupError("no Kalshi event")
            ev = get(f"{KALSHI}/events/{kev}?with_nested_markets=true")["event"]
            for m in ev["markets"]:
                if m.get("status") in KALSHI_KEEP:
                    found.append(dict(race=race, ticker=m["ticker"],
                                      outcome=m.get("yes_sub_title") or m.get("title")))
        except LookupError:
            pass
        except Exception as e:
            print(f"discover {race} kalshi {kev}: {e}")
        kal += found or [m for m in pk if m["race"] == race]
        time.sleep(KALSHI_GAP)
        found = []
        try:
            for ev in (get(f"{GAMMA}/events?slug={pslug}") if pslug else []):
                for m in ev["markets"]:
                    # placeholders ("Candidate C", "Party A") never have a bid
                    if (not m.get("active") or m.get("closed")
                            or _f(m.get("bestBid")) in (None, 0.0)):
                        continue
                    tok = json.loads(m["clobTokenIds"])[0]          # YES token
                    found.append(dict(race=race, token=tok, market=m["slug"],
                                      outcome=m.get("groupItemTitle") or m["question"]))
        except Exception as e:
            print(f"discover {race} polymarket {pslug}: {e}")
        poly += found or [m for m in pp if m["race"] == race]
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
            kal, poly = discover(RACES, (kal, poly))
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
