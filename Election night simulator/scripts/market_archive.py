"""Price history for every election market we can find on Kalshi and Polymarket (user 2026-11-04: "try to find every market
you can on polymarket and kalshi. And save the price history"). Run by .github/workflows/market-archive.yml in parallel
shards; each shard's tar.gz goes to the release election-night-2026 as it grows.

  kalshi      every market in Kalshi's Elections category that closes on or after --since (about 21,000): by the hour from
              --hour-start, by the minute from --minute-start. Columns: end_ts, bid, ask, price, volume, open_interest.
  polymarket  every market in events tagged elections or midterms ending on or after --since: the YES token's whole history by
              the hour (Polymarket keeps roughly the last month at that fidelity), by the minute from --minute-start.
              Columns: ts, price. It has no bid or ask history. Its event list stops at an offset of about 2,100 per tag and
              closed/open state, newest end dates first, so older closed events can be missing.

Files: market_archive/{venue}/{hour,minute}/{ticker or token}.csv.gz, and index-{shard}.json (what each market is).

    py market_archive.py --venue kalshi --shard 0 --of 4 --out DIR --minutes 330
"""
import argparse
import calendar
import csv
import gzip
import json
import os
import re
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import zlib

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
UA = {"User-Agent": "polling-agg election record"}
RELEASE = "election-night-2026"
UPLOAD_EVERY = 1800


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (i + 1))
                continue
            if e.code in (400, 404, 422):
                return None
            time.sleep(2)
        except (OSError, ValueError):
            time.sleep(2)
    return None


def stamp(x):
    return calendar.timegm(time.strptime(x[:19], "%Y-%m-%dT%H:%M:%S"))


def mine(key, shard, of):
    return zlib.crc32(key.encode()) % of == shard


def kalshi_markets(since, shard, of):
    series = [s for s in (get(f"{KALSHI}/series") or {}).get("series", []) if s.get("category") == "Elections"]
    print(len(series), "Elections series", flush=True)
    out = []
    for s in series:
        cursor = ""
        while True:
            d = get(f"{KALSHI}/events?series_ticker={s['ticker']}&limit=200&with_nested_markets=true" + (f"&cursor={cursor}" if cursor else "")) or {}
            for e in d.get("events") or []:
                for m in e.get("markets") or []:
                    if (m.get("close_time") or "9") >= since and mine(m["ticker"], shard, of):
                        out.append(dict(series=s["ticker"], event=e["event_ticker"], title=e.get("title"), ticker=m["ticker"], side=m.get("yes_sub_title"),
                                        status=m.get("status"), result=m.get("result"), close=m.get("close_time")))
            cursor = d.get("cursor")
            if not cursor:
                break
            time.sleep(0.05)
        time.sleep(0.05)
    return out


def polymarket_markets(since, shard, of):
    seen, out = set(), []
    for tag in ("elections", "midterms"):
        for closed in ("false", "true"):
            off = 0
            while True:
                d = get(f"{GAMMA}/events?tag_slug={tag}&closed={closed}&limit=100&offset={off}&order=endDate&ascending=false")
                if not d:
                    break
                for e in d:
                    if e.get("id") in seen or (e.get("endDate") or "9") < since:
                        continue
                    seen.add(e.get("id"))
                    for m in e.get("markets") or []:
                        try:
                            tok = json.loads(m.get("clobTokenIds") or "[]")[0]
                        except (ValueError, IndexError):
                            continue
                        if mine(tok, shard, of):
                            out.append(dict(event=e.get("slug"), title=e.get("title"), market=m.get("slug"), question=m.get("question"),
                                            outcome=m.get("groupItemTitle"), token=tok, closed=m.get("closed"), prices=m.get("outcomePrices"), volume=m.get("volume")))
                off += 100
                if len(d) < 100:
                    break
                time.sleep(0.05)
    print(len(seen), "Polymarket events", flush=True)
    return out


def kalshi_candles(m, start, end, period):
    chunk, t0, cs = 4800 * period * 60, start, []
    while t0 < end:
        j = get(f"{KALSHI}/series/{m['series']}/markets/{m['ticker']}/candlesticks?start_ts={t0}&end_ts={min(t0 + chunk, end)}&period_interval={period}")
        cs += (j or {}).get("candlesticks") or []
        t0 += chunk
        time.sleep(0.03)
    return list({c.get("end_period_ts"): c for c in cs}.values())


def write_kalshi(path, cs):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["end_ts", "bid", "ask", "price", "volume", "open_interest"])
        for c in cs:
            w.writerow([c.get("end_period_ts"), (c.get("yes_bid") or {}).get("close_dollars"), (c.get("yes_ask") or {}).get("close_dollars"),
                        (c.get("price") or {}).get("close_dollars"), c.get("volume_fp"), c.get("open_interest_fp")])


def poly_history(tok, q):
    return (get(f"{CLOB}/prices-history?market={tok}&{q}") or {}).get("history") or []


def write_poly(path, h):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "price"])
        for x in h:
            w.writerow([x.get("t"), x.get("p")])


def upload(out, name):
    if not os.environ.get("GH_TOKEN") or not os.environ.get("GITHUB_REPOSITORY"):
        return
    path = os.path.join(os.path.dirname(os.path.abspath(out)), name)
    with tarfile.open(path, "w:gz") as t:
        t.add(out, arcname="market_archive")
    r = subprocess.run(["gh", "release", "upload", RELEASE, path, "--clobber", "--repo", os.environ["GITHUB_REPOSITORY"]], capture_output=True, text=True)
    print("uploaded" if not r.returncode else "UPLOAD FAILED " + r.stderr[:200], name, f"{os.path.getsize(path) / 1e6:.0f} MB", flush=True)
    os.remove(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", required=True, choices=("kalshi", "polymarket"))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--since", default="2026-06-01")
    ap.add_argument("--hour-start", default="2026-01-01T00:00:00Z")
    ap.add_argument("--minute-start", default="2026-11-03T00:00:00Z")
    ap.add_argument("--minutes", type=float, default=330)
    ap.add_argument("--limit", type=int, help="only this many markets (test)")
    a = ap.parse_args()
    stop = time.time() + a.minutes * 60
    v = os.path.join(a.out, a.venue)
    os.makedirs(os.path.join(v, "hour"), exist_ok=True)
    os.makedirs(os.path.join(v, "minute"), exist_ok=True)
    markets = kalshi_markets(a.since, a.shard, a.of) if a.venue == "kalshi" else polymarket_markets(a.since, a.shard, a.of)
    print(len(markets), "markets in this shard", flush=True)
    if a.limit:
        markets = markets[:a.limit]
    hs, ms, end = stamp(a.hour_start), stamp(a.minute_start), int(time.time())
    name = f"market-archive-{a.venue}-{a.shard + 1}of{a.of}.tar.gz"
    index, done, last_up, cut = [], 0, time.time(), None
    idx_path = os.path.join(v, f"index-{a.shard + 1}of{a.of}.json")
    for i, m in enumerate(markets):
        if time.time() > stop:
            cut = i
            print("time up at", i, "of", len(markets), flush=True)
            break
        rec = dict(m, hour=0, minute=0)
        if a.venue == "kalshi":
            key = re.sub(r"[^\w.-]", "_", m["ticker"])
            for res, st, period in (("hour", hs, 60), ("minute", ms, 1)):
                cs = kalshi_candles(m, st, end, period)
                if cs:
                    write_kalshi(os.path.join(v, res, key + ".csv.gz"), cs)
                    rec[res] = len(cs)
        else:
            key = m["token"]
            for res, q in (("hour", "interval=max&fidelity=60"), ("minute", f"startTs={ms}&endTs={end}&fidelity=1")):
                h = poly_history(m["token"], q)
                if h:
                    write_poly(os.path.join(v, res, key + ".csv.gz"), h)
                    rec[res] = len(h)
                time.sleep(0.03)
        index.append(rec)
        done += bool(rec["hour"] or rec["minute"])
        if (i + 1) % 500 == 0:
            print(i + 1, "of", len(markets), "markets;", done, "with prices", flush=True)
        if time.time() - last_up > UPLOAD_EVERY:
            with open(idx_path, "w", encoding="utf-8") as f:
                json.dump(dict(total=len(markets), done=i + 1, end=end, markets=index), f)
            upload(a.out, name)
            last_up = time.time()
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(dict(total=len(markets), done=len(index), cut_at=cut, end=end, markets=index), f)
    upload(a.out, name)
    print(f"done: {len(index)} of {len(markets)} markets, {done} with prices", flush=True)


if __name__ == "__main__":
    main()
