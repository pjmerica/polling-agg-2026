"""Kalshi's price history for the 2026 races, from its candle API: one gz CSV per market, plus index.json.

Kalshi keeps candles after a market settles, so this fills what wasn't recorded live and can be re-run at any time:
    winner markets, House + Senate + Governor, by the minute:
      py kalshi_backfill.py --out DIR --start 2026-11-03T00:00:00Z --period 1
    the same by the hour, back through the campaign:
      py kalshi_backfill.py --out DIR --start 2026-01-01T00:00:00Z --period 60
    --end stops earlier than now. Each run reaches up to the moment it runs, so re-run it to extend. A request holds at most
    5,000 candles, so long ranges are fetched in chunks. Minutes without activity have no candle.
    margin markets:
      py kalshi_backfill.py --out DIR --start 2026-11-03T00:00:00Z --period 1 --series KXMIDTERMMOV KXGENERALMOV KXAKMOV
Columns: end_ts, yes bid/ask (close), last price (close), volume, open interest.
"""
import argparse
import calendar
import csv
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
UA = {"User-Agent": "polling-agg election record"}
HERE = os.path.dirname(os.path.abspath(__file__))
STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD "
          "TN TX UT VT VA WA WV WI WY").split()
MANY_SEATS = {"CA": 52, "TX": 38, "FL": 28, "NY": 26, "PA": 17, "IL": 17, "OH": 15, "GA": 14, "NC": 14, "MI": 13, "NJ": 12, "VA": 11}


def get(url):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (i + 1))
                continue
            if e.code == 404:
                return None
            raise
        except OSError:
            time.sleep(2)
    return None


def series_events(series):
    out, cursor = [], ""
    while True:
        d = get(f"{KALSHI}/events?series_ticker={series}&limit=200&with_nested_markets=true" + (f"&cursor={cursor}" if cursor else "")) or {}
        out += d.get("events") or []
        cursor = d.get("cursor")
        if not cursor:
            return out


def one_event(ev):
    j = get(f"{KALSHI}/events/{ev}?with_nested_markets=true")
    if not j or not j.get("event"):
        return None
    e = j["event"]
    e["markets"] = j.get("markets") or e.get("markets") or []
    return e


def winner_events():
    """Every House event (KXHOUSERACE, and the older per-district events), then each Senate and Governor race's."""
    events = series_events("KXHOUSERACE")
    for st in STATES:
        seats = MANY_SEATS.get(st, 10)
        for n in ["AL"] + [str(i) for i in range(1, seats + 1)]:
            for ev in (f"HOUSE{st}{n}-26", f"KXHOUSE{st}{n}-26"):
                e = one_event(ev)
                if e:
                    events.append(e)
                time.sleep(0.07)
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.join(HERE, "..", "..", "State election results", "scripts"))
    import capture_markets
    for kev, _ in capture_markets.RACES.values():
        e = one_event(kev) if kev else None
        if e:
            events.append(e)
        time.sleep(0.07)
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", help="default: now")
    ap.add_argument("--period", type=int, default=1, choices=(1, 60, 1440), help="minutes per candle")
    ap.add_argument("--series", nargs="*", help="these series instead of the winner markets")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stamp = lambda x: calendar.timegm(time.strptime(x[:19], "%Y-%m-%dT%H:%M:%S"))
    start, end = stamp(a.start), stamp(a.end) if a.end else int(time.time())
    chunk = 4800 * a.period * 60
    events = [e for s in a.series for e in series_events(s)] if a.series else winner_events()
    print(len(events), "events", flush=True)
    done = rows = 0
    meta, seen = [], set()
    for e in events:
        series = e.get("series_ticker")
        for m in e.get("markets") or []:
            t = m["ticker"]
            if t in seen:
                continue
            seen.add(t)
            cs, t0 = [], start
            while t0 < end:
                j = get(f"{KALSHI}/series/{series}/markets/{t}/candlesticks?start_ts={t0}&end_ts={min(t0 + chunk, end)}&period_interval={a.period}")
                time.sleep(0.07)
                cs += (j or {}).get("candlesticks") or []
                t0 += chunk
            cs = list({c.get("end_period_ts"): c for c in cs}.values())    # a chunk's edge can repeat
            meta.append(dict(event=e["event_ticker"], ticker=t, side=m.get("yes_sub_title"), status=m.get("status"), result=m.get("result"), candles=len(cs)))
            if not cs:
                continue
            with gzip.open(os.path.join(a.out, t + ".csv.gz"), "wt", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["end_ts", "bid_close", "ask_close", "price_close", "volume", "open_interest"])
                for c in cs:
                    w.writerow([c.get("end_period_ts"), (c.get("yes_bid") or {}).get("close_dollars"), (c.get("yes_ask") or {}).get("close_dollars"),
                                (c.get("price") or {}).get("close_dollars"), c.get("volume_fp"), c.get("open_interest_fp")])
            done += 1
            rows += len(cs)
            if done % 200 == 0:
                print(done, "markets", rows, "candles", flush=True)
    with open(os.path.join(a.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(dict(start=start, end=end, period_minutes=a.period, markets=meta), f, indent=0)
    print("done:", done, "markets with candles of", len(meta), ";", rows, "candles", flush=True)


if __name__ == "__main__":
    main()
