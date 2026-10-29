"""Download what Kalshi and Polymarket paid, minute by minute, during the 2024 count.

For every 2024 President, Senate and Governor race with an NYT timeline (State election results/
data/raw/nyt_all, from fetch_nyt_history.py --all), the non-Republican contract's prices from
Nov 5 23:00 UTC (6 pm ET) to Nov 11:
    data/raw/market_history/2024/{ST}-{office}/kalshi.csv       ts, bid, ask, last  (1-minute candles)
    data/raw/market_history/2024/{ST}-{office}/polymarket.csv   ts, p               (1-minute price)
    data/raw/market_history/2024/index.csv                      which contract, result, volume
Kalshi moved settled markets to /historical/* (cutoff 2026-08-29); its 2024 party markets are
PRESPARTY{ST}-24, SENATE{ST}-24, GOVPARTY{ST}-24. Polymarket's are {state}-presidential-election-winner
and {state}-us-senate-election-winner (minute prices from /prices-history; no book). Files already
downloaded are kept; delete a race's folder to fetch it again.

    py "Election night simulator/scripts/market_history.py"
"""
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "State election results", "scripts"))
from utils.http_headers import DEFAULT_HEADERS  # noqa: E402
import volatility as vol  # noqa: E402  - every state's NYT timeline, as VOLATILITY.md reads them

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
OUT = os.path.join(ROOT, "data", "raw", "market_history")
START = dt.datetime(2024, 11, 5, 23, 0, tzinfo=dt.timezone.utc)
END = dt.datetime(2024, 11, 11, 0, 0, tzinfo=dt.timezone.utc)
CHUNK = 12 * 3600
KALSHI_SERIES = {"President": "PRESPARTY", "Senate": "SENATE", "Governor": "GOVPARTY"}
POLY_SLUG = {"President": ["{s}-presidential-election-winner"],
             "Senate": ["{s}-us-senate-election-winner", "{s}-senate-election-winner"],
             "Governor": ["{s}-governor-election-winner", "{s}-gubernatorial-election-winner"]}


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=DEFAULT_HEADERS),
                                        timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 and i + 1 < tries:
                time.sleep(3 * (i + 1))
                continue
            raise


def races_2024():
    """[(abbr, state slug, office, opp party)] for 2024 races with a usable NYT timeline."""
    out = {}
    for r in vol.race_rows():
        if r["year"] == 2024:
            st = r["state"]
            slug = next(k for k, v in vol.ABBR.items() if v == st)
            out[(st, r["office"])] = (st, slug, r["office"], str(r["opp_party"]).lower())
    return sorted(out.values())


def kalshi(st, office, opp_party, folder):
    ev = f"{KALSHI_SERIES[office]}{st}-24"
    d = get(f"{KALSHI}/historical/markets?event_ticker={ev}")
    ms = (d or {}).get("markets") or []
    want = "Democratic" if opp_party in ("dem", "democrat", "democratic") else None
    pick = None
    for m in ms:
        party = (m.get("custom_strike") or {}).get("Party")
        if party == "Republican":
            continue
        if want is None or party == want:
            if pick is None or float(m.get("volume_fp") or 0) > float(pick.get("volume_fp") or 0):
                pick = m
    if not pick:
        return None
    t = pick["ticker"]
    rows = []
    s = int(START.timestamp())
    while s < int(END.timestamp()):
        e = min(s + CHUNK, int(END.timestamp()))
        c = get(f"{KALSHI}/historical/markets/{t}/candlesticks?start_ts={s}&end_ts={e}&period_interval=1")
        for k in (c or {}).get("candlesticks", []):
            rows.append(dict(ts=k["end_period_ts"], bid=(k.get("yes_bid") or {}).get("close"),
                             ask=(k.get("yes_ask") or {}).get("close"),
                             last=(k.get("price") or {}).get("close")))
        s = e
        time.sleep(0.15)
    write(os.path.join(folder, "kalshi.csv"), rows, ["ts", "bid", "ask", "last"])
    return dict(venue="kalshi", contract=t, side=(pick.get("custom_strike") or {}).get("Party"),
                result=pick.get("result"), volume=pick.get("volume_fp"), rows=len(rows))


def polymarket(slug, office, opp_party, folder):
    ev = None
    for pat in POLY_SLUG[office]:
        evs = get(f"{GAMMA}/events?slug={pat.format(s=slug)}")
        if evs:
            ev = evs[0]
            break
    if not ev:
        return None
    key = "democrat" if opp_party in ("dem", "democrat", "democratic") else "another party"
    m = next((m for m in ev["markets"] if key in m["question"].lower()), None)
    if not m:
        return None
    tok = json.loads(m["clobTokenIds"])[0]
    rows = []
    s = int(START.timestamp())
    while s < int(END.timestamp()):
        e = min(s + CHUNK, int(END.timestamp()))
        h = get(f"{CLOB}/prices-history?market={tok}&startTs={s}&endTs={e}&fidelity=1")
        rows += [dict(ts=x["t"], p=x["p"]) for x in (h or {}).get("history", [])]
        s = e
        time.sleep(0.1)
    write(os.path.join(folder, "polymarket.csv"), rows, ["ts", "p"])
    won = json.loads(m.get("outcomePrices") or "[]")
    return dict(venue="polymarket", contract=m["slug"], side=m["question"],
                result="yes" if won and won[0] == "1" else "no", volume=m.get("volumeNum"), rows=len(rows))


def write(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: r["ts"]):
        if r["ts"] not in seen:
            seen.add(r["ts"])
            out.append(r)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)


def main():
    base = os.path.join(OUT, "2024")
    index = []
    for st, slug, office, opp in races_2024():
        folder = os.path.join(base, f"{st}-{office}")
        for venue, fn, arg in (("kalshi", kalshi, st), ("polymarket", polymarket, slug)):
            if os.path.exists(os.path.join(folder, f"{venue}.csv")):
                index.append(dict(race=f"{st}-{office}", venue=venue, contract="(cached)"))
                continue
            try:
                info = fn(arg, office, opp, folder)
            except Exception as e:
                print(f"{st}-{office} {venue}: {e}")
                continue
            if info:
                index.append(dict(race=f"{st}-{office}", **info))
                print(f"{st}-{office} {venue}: {info['contract']} ({info['rows']} minutes, result {info['result']})")
    old = {}
    ipath = os.path.join(base, "index.csv")
    if os.path.exists(ipath):
        with open(ipath, encoding="utf-8") as f:
            old = {(r["race"], r["venue"]): r for r in csv.DictReader(f)}
    for r in index:
        if r.get("contract") != "(cached)":
            old[(r["race"], r["venue"])] = r
    fields = ["race", "venue", "contract", "side", "result", "volume", "rows"]
    write_index = sorted(old.values(), key=lambda r: (r["race"], r["venue"]))
    os.makedirs(base, exist_ok=True)
    with open(ipath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(write_index)
    print(f"{len(write_index)} race-venue series -> {ipath}")


if __name__ == "__main__":
    main()
