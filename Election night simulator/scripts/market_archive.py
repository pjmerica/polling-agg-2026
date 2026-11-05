"""Price history for every election market we can find on Kalshi and Polymarket (user 2026-11-04: "try to find every market
you can on polymarket and kalshi. And save the price history"). Run by .github/workflows/market-archive.yml in parallel
shards; each shard's tar.gz goes to the release election-night-2026 as it grows.

  kalshi      every market in Kalshi's Elections category that closes on or after --since: by the hour from --hour-start, by
              the minute from --minute-start, and by the minute over the last 9 days of any market that closed before that
              (a primary's final days and night). Columns: end_ts, bid, ask, price, volume, open_interest. Kalshi moves markets
              settled before its cutoff (2026-09-05 when written; /historical/cutoff) out of /events and /series to
              /historical/markets, with field names that drop "_dollars" and "_fp"; both are read.
  polymarket  every market in events with one of TAGS ending on or after --since: the YES token's whole life by the hour, by
              the minute from --minute-start, by the minute from --core-minute-start for general-election winner markets, and
              by the minute over the last 9 days of any market that stopped before --minute-start. Columns: ts, price. It has
              no bid or ask history. A request for a whole history (interval=max) returns nothing finer than 12 hours on a
              closed market, but a date range of up to 15 days returns every minute, so history is walked in 14-day ranges.
              The daily interval=max call only roughly finds where a market's prices start and stop: it can end days before
              trading did and is empty for a market under a day old, so the walk runs 14 days past it each way and the minute
              window is set from the hourly prices found. Its event list stops at an offset of
              about 2,100 per tag and closed/open state, newest end dates first; on 2026-11-04 that reached back to November 2025.
              A market with no price history at all is usually a placeholder ("Will Person A win ...").

A request that still fails after retries counts in the index as errors, per market and per file, so a failed fetch can't pass
for a market with no prices.

Files: market_archive/{venue}/{hour,minute}/{ticker or token}.csv.gz, and index-{shard}.json (what each market is).

    py market_archive.py --venue kalshi --shard 0 --of 4 --out DIR --minutes 330
"""
import argparse
import calendar
import concurrent.futures
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
TAGS = ("elections", "midterms", "primaries", "global-elections", "congress", "governor", "house")
RANGE = 14 * 86400      # the longest date range to ask Polymarket for (15 days works, 20 returns 400, at any fidelity)
LAST_DAYS = 9 * 86400   # by the minute before a market that stopped earlier closed
POLY_THREADS = 3        # at once per job, 8 jobs: about 70 requests a second against a published limit of 100
WINNER = re.compile(r"-(house|senate|governor)-election-winner|-governor-winner-2026|which-party-will-win-the-house-race")
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


def ranges(a, b, step=RANGE):
    """[a, b] cut into consecutive ranges of at most step seconds."""
    out = []
    while a < b:
        out.append((a, min(a + step, b)))
        a += step
    return out


def mine(key, shard, of):
    return zlib.crc32(key.encode()) % of == shard


def kalshi_markets(since, shard, of):
    series = [s for s in (get(f"{KALSHI}/series") or {}).get("series", []) if s.get("category") == "Elections"]
    print(len(series), "Elections series", flush=True)
    out, seen = [], set()
    for s in series:
        cursor = ""
        while True:
            d = get(f"{KALSHI}/events?series_ticker={s['ticker']}&limit=200&with_nested_markets=true" + (f"&cursor={cursor}" if cursor else "")) or {}
            for e in d.get("events") or []:
                for m in e.get("markets") or []:
                    if (m.get("close_time") or "9") >= since and mine(m["ticker"], shard, of):
                        seen.add(m["ticker"])
                        out.append(dict(series=s["ticker"], event=e["event_ticker"], title=e.get("title"), ticker=m["ticker"], side=m.get("yes_sub_title"),
                                        status=m.get("status"), result=m.get("result"), close=m.get("close_time")))
            cursor = d.get("cursor")
            if not cursor:
                break
            time.sleep(0.05)
        time.sleep(0.05)
        cursor = ""
        while True:     # settled before Kalshi's cutoff: not in /events any more
            d = get(f"{KALSHI}/historical/markets?series_ticker={s['ticker']}&limit=1000" + (f"&cursor={cursor}" if cursor else "")) or {}
            for m in d.get("markets") or []:
                if m["ticker"] not in seen and (m.get("close_time") or "9") >= since and mine(m["ticker"], shard, of):
                    seen.add(m["ticker"])
                    out.append(dict(series=s["ticker"], event=m.get("event_ticker"), title=m.get("title"), ticker=m["ticker"], side=m.get("yes_sub_title"),
                                    status=m.get("status"), result=m.get("result"), close=m.get("close_time"), historical=True))
            cursor = d.get("cursor")
            if not cursor:
                break
            time.sleep(0.05)
        time.sleep(0.05)
    return out


def polymarket_markets(since, shard, of):
    seen, out = set(), []
    for tag in TAGS:
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
                                            outcome=m.get("groupItemTitle"), token=tok, closed=m.get("closed"), prices=m.get("outcomePrices"), volume=m.get("volume"),
                                            vol=float(m.get("volumeNum") or m.get("volume") or 0)))
                off += 100
                if len(d) < 100:
                    break
                time.sleep(0.05)
    print(len(seen), "Polymarket events", flush=True)
    return out


def kalshi_candles(m, start, end, period):
    chunk, t0, cs = 4800 * period * 60, start, []
    path = f"historical/markets/{m['ticker']}" if m.get("historical") else f"series/{m['series']}/markets/{m['ticker']}"
    while t0 < end:
        j = get(f"{KALSHI}/{path}/candlesticks?start_ts={t0}&end_ts={min(t0 + chunk, end)}&period_interval={period}")
        cs += (j or {}).get("candlesticks") or []
        t0 += chunk
        time.sleep(0.03)
    return list({c.get("end_period_ts"): c for c in cs}.values())


def write_kalshi(path, cs):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["end_ts", "bid", "ask", "price", "volume", "open_interest"])
        close = lambda x: x.get("close_dollars", x.get("close")) if x else None     # the historical API has no "_dollars"
        for c in cs:
            w.writerow([c.get("end_period_ts"), close(c.get("yes_bid")), close(c.get("yes_ask")), close(c.get("price")),
                        c.get("volume_fp", c.get("volume")), c.get("open_interest_fp", c.get("open_interest"))])


def poly_range(tok, a, b, fidelity, rec):
    """Prices between two times, walked in 14-day ranges. A failed request counts in rec["errors"]."""
    seen = {}
    for x, y in ranges(a, b):
        j = get(f"{CLOB}/prices-history?market={tok}&startTs={x}&endTs={y}&fidelity={fidelity}")
        if j is None:
            rec["errors"] += 1
        for p in (j or {}).get("history") or []:
            seen[p.get("t")] = p
        time.sleep(0.02)
    return [seen[t] for t in sorted(seen)]


def poly_bounds(m, ms, hs, end, rec):
    """Where to look for a market's prices, or None if it never had any. Generous: a range with nothing in it costs one request."""
    for fidelity in (1440, 60):     # 60 finds a market under a day old, which has no daily price; on an old closed market it is empty
        j = get(f"{CLOB}/prices-history?market={m['token']}&interval=max&fidelity={fidelity}")
        if j is None:
            rec["errors"] += 1
        h = (j or {}).get("history") or []
        if h:
            return h[0]["t"] - RANGE, min(h[-1]["t"] + RANGE, end)
    if m.get("vol"):
        return hs, end              # traded, but with too few prices for interval=max to show any
    return None if m.get("closed") else (ms, end)


def poly_market(m, ms, core_ms, hs, end, rec, v):
    """The hour and minute files for one Polymarket market."""
    tok = m["token"]
    bounds = poly_bounds(m, ms, hs, end, rec)
    if not bounds:
        return
    first, last = bounds
    hours = poly_range(tok, first, last, 60, rec)
    if hours:
        write_poly(os.path.join(v, "hour", tok + ".csv.gz"), hours)
        first, last = hours[0]["t"], min(hours[-1]["t"] + 3600, end)
    rec["first"], rec["last"] = first, last
    rec["hour"] = len(hours)
    start = core_ms if WINNER.search(m.get("event") or "") else ms
    if last <= start:
        start = last - LAST_DAYS    # stopped before the minute window: its last days
    mins = poly_range(tok, max(start, first), last, 1, rec)
    if mins:
        write_poly(os.path.join(v, "minute", tok + ".csv.gz"), mins)
    rec["minute"] = len(mins)


def write_poly(path, h):
    tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(path)))), os.path.basename(path) + ".part")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts", "price"])
        for x in h:
            w.writerow([x.get("t"), x.get("p")])
    os.replace(tmp, path)       # an upload running meanwhile sees whole files only


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
    ap.add_argument("--since", default="2026-01-01")
    ap.add_argument("--hour-start", default="2026-01-01T00:00:00Z")
    ap.add_argument("--minute-start", default="2026-11-03T00:00:00Z")
    ap.add_argument("--core-minute-start", default="2026-10-01T00:00:00Z")
    ap.add_argument("--minutes", type=float, default=330)
    ap.add_argument("--label", default="", help="in the asset's name, so a new run doesn't replace a good copy until it is checked")
    ap.add_argument("--limit", type=int, help="only this many markets (test)")
    a = ap.parse_args()
    stop = time.time() + a.minutes * 60
    v = os.path.join(a.out, a.venue)
    os.makedirs(os.path.join(v, "hour"), exist_ok=True)
    os.makedirs(os.path.join(v, "minute"), exist_ok=True)
    markets = kalshi_markets(a.since, a.shard, a.of) if a.venue == "kalshi" else polymarket_markets(a.since, a.shard, a.of)
    print(len(markets), "markets in this shard", flush=True)
    if a.venue == "polymarket":
        markets.sort(key=lambda m: -m["vol"])       # if time runs out, the least traded go
    if a.limit:
        markets = markets[:a.limit]
    hs, ms, end = stamp(a.hour_start), stamp(a.minute_start), int(time.time())
    core_ms = stamp(a.core_minute_start)
    name = f"market-archive-{a.label + '-' if a.label else ''}{a.venue}-{a.shard + 1}of{a.of}.tar.gz"
    index, done, last_up, cut = [], 0, time.time(), None
    idx_path = os.path.join(v, f"index-{a.shard + 1}of{a.of}.json")

    def fetch(m):
        if time.time() > stop:
            return None
        rec = dict(m, hour=0, minute=0, errors=0)
        if a.venue == "kalshi":
            key = re.sub(r"[^\w.-]", "_", m["ticker"])
            closed_at = stamp(m["close"]) if m.get("close") else end
            for res, st, period in (("hour", hs, 60), ("minute", ms if closed_at > ms else closed_at - LAST_DAYS, 1)):
                cs = kalshi_candles(m, st, min(end, closed_at + 3600), period)
                if cs:
                    write_kalshi(os.path.join(v, res, key + ".csv.gz"), cs)
                    rec[res] = len(cs)
        else:
            poly_market(m, ms, core_ms, hs, end, rec, v)
        return rec

    with concurrent.futures.ThreadPoolExecutor(POLY_THREADS if a.venue == "polymarket" else 1) as pool:
        for i, rec in enumerate(pool.map(fetch, markets)):
            if rec is None:
                cut = i if cut is None else cut
                continue
            index.append(rec)
            done += bool(rec["hour"] or rec["minute"])
            if (i + 1) % 500 == 0:
                print(i + 1, "of", len(markets), "markets;", done, "with prices;", sum(r["errors"] for r in index), "failed requests", flush=True)
            if time.time() - last_up > UPLOAD_EVERY:
                with open(idx_path, "w", encoding="utf-8") as f:
                    json.dump(dict(total=len(markets), done=i + 1, end=end, markets=index), f)
                upload(a.out, name)
                last_up = time.time()
    if cut is not None:
        print("time up at", cut, "of", len(markets), flush=True)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(dict(total=len(markets), done=len(index), cut_at=cut, end=end, markets=index), f)
    upload(a.out, name)
    print(f"done: {len(index)} of {len(markets)} markets, {done} with prices, {sum(r['errors'] for r in index)} failed requests", flush=True)


if __name__ == "__main__":
    main()
