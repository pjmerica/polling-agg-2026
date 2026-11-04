"""How did election night's FLIPs and buy signals do? Re-run when the count is done: some races are still open.

Each signal is scored once, the first time a race + side (+ venue, for FLIPs) showed it, one contract at the ask shown then,
after Kalshi's fee (0.07 P(1-P)) or Polymarket's (0.04 P(1-P)):  win: 1 - ask - fee; loss: -ask - fee.
Open races are marked at today's price and kept apart from the settled ones.

Desk (Senate / Governor): the logged signals in projections.csv. FLIP = the `flip` column as it was computed that pass; the
rule didn't change on the night. Board = the page's rule (kalshiSides): our chance - Kalshi ask - fee >= 3c. A price is used only
if Kalshi was still quoting that race within 10 minutes (a settled market's last price stays in the log; the page showed it).
Races: 15 until 03:46 UTC Nov 4, then all 71.

House: nothing logged the board until Nov 4 19:14 UTC, so it's recomputed: hist.json (our chance, share counted, margin, Kalshi's
Democratic ask) and Kalshi's minute candles for the Republican's ask (or 1 - the Democrat's bid). hist.json has no count read, so
the page's count guard is approximated with the margin so far ("leads by 1+"). Not what the page showed, row for row.

    py "Election night simulator/scripts/evaluate_signals.py" --dir EVAL_DIR
      EVAL_DIR: projections.csv, outcomes.json, markets/*.csv (Kalshi's state-folder prices), house_hist.json, house_live.json,
      house_bench.json, kalshi_minutes/ (from the backfill), kalshi_map.json
"""
import argparse
import bisect
import calendar
import collections
import csv
import glob
import gzip
import json
import os
import time

BOARD = 0.03
FRESH_S = 600
SETTLE_FROM = "2026-11-03T19:41:00Z"      # the model start was live from here (beee6fb7)


def kfee(p):
    return 0.07 * p * (1 - p)


def f(x):
    try:
        return None if x in ("", None) else float(x)
    except ValueError:
        return None


def secs(ts):
    return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))


def score(rows, label):
    """rows: dict(ask, fee, won (True/False/None), mark). -> one summary line."""
    done = [r for r in rows if r["won"] is not None]
    wins = sum(r["won"] for r in done)
    cost = sum(r["ask"] + r["fee"] for r in done)
    pnl = sum((1 if r["won"] else 0) - r["ask"] - r["fee"] for r in done)
    op = [r for r in rows if r["won"] is None]
    expect = sum(r["ask"] for r in done)
    opnl = sum((r["mark"] if r["mark"] is not None else r["ask"]) - r["ask"] - r["fee"] for r in op)
    s = f"{label:44} {len(done):4} settled, {wins:3} won (price implied {expect:6.1f}) | cost ${cost:7.2f} P&L ${pnl:+7.2f} ROI {100 * pnl / cost if cost else 0:+6.1f}%"
    if op:
        s += f" | {len(op)} open, marked ${opnl:+.2f}"
    return s


def outcome(race, side, oc):
    o = oc.get(race) or {}
    if o.get("nyt_win"):
        return o["nyt_win"] == side, None
    k = o.get("kalshi") or {}
    t = next((v for n, v in k.items() if n.endswith("-" + side)), None)
    if t and t.get("result") in ("yes", "no"):
        return t["result"] == "yes", None
    mark = None
    if t:
        b = f(t.get("bid"))
        mark = b
    return None, mark


def desk(a):
    oc = json.load(open(os.path.join(a.dir, "outcomes.json"), encoding="utf-8"))
    quotes = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(a.dir, "markets", "*.csv"))):
        for x in csv.DictReader(open(p, encoding="utf-8")):
            quotes[x["race"]].append(secs(x["ts_utc"]))
    for v in quotes.values():
        v.sort()
    rows = [x for x in csv.DictReader(open(os.path.join(a.dir, "projections.csv"), encoding="utf-8")) if x["ts_utc"] >= SETTLE_FROM]
    print(f"\nDESK: {len(rows)} logged rows, {rows[0]['ts_utc']} -> {rows[-1]['ts_utc']}, {len({r['race'] for r in rows})} races")
    flips, seen = [], set()
    for x in rows:
        if x["flip"] != "1":
            continue
        k = (x["race"], x["best_side"], x["best_venue"])
        if k in seen:
            continue
        seen.add(k)
        ask = f(x["best_ask"])
        won, mark = outcome(x["race"], x["best_side"], oc)
        rate = 0.07 if x["best_venue"] == "kalshi" else 0.04
        flips.append(dict(ask=ask, fee=rate * ask * (1 - ask), won=won, mark=mark, race=x["race"], side=x["best_side"], venue=x["best_venue"],
                          ts=x["ts_utc"], pct=f(x["pct"]), m=f(x["margin"]), p=f(x["p_v1"]) if x["best_side"] == "D" else 1 - (f(x["p_v1"]) or 0)))
    print("\nFLIPs, first time each showed:")
    for r in flips:
        res = "OPEN (now " + (f"{r['mark'] * 100:.0f}c" if r["mark"] is not None else "?") + ")" if r["won"] is None else ("WON" if r["won"] else "lost")
        print(f"  {r['ts'][5:16]} {r['race']:7} {r['side']} {r['venue']:10} ask {r['ask'] * 100:5.1f}c ours {100 * r['p']:3.0f}% | {r['pct']:5.1f}% counted, margin {r['m']:+6.1f} -> {res}")
    print(score(flips, "FLIPs"))
    kf = [r for r in flips if r["venue"] == "kalshi"]
    print(score(kf, "FLIPs, Kalshi only (races: " + str(len({r['race'] for r in kf})) + ")"))

    first, stale = {}, 0
    for x in rows:
        p = f(x["p_v1"]) if f(x["p_v1"]) is not None else f(x["p_mkt"])
        if p is None:
            continue
        t = secs(x["ts_utc"])
        q = quotes.get(x["race"], [])
        i = bisect.bisect_right(q, t) - 1
        fresh = i >= 0 and t - q[i] <= FRESH_S
        for side, ask, prob in (("D", f(x["k_ask"]), p), ("R", f(x["k_rask"]), 1 - p)):
            if ask is None or not 0 < ask < 1:
                continue
            e = prob - ask - kfee(ask)
            if e < BOARD:
                continue
            if not fresh:
                stale += 1
                continue
            first.setdefault((x["race"], side), dict(x=x, ask=ask, prob=prob, edge=e, side=side))
    board = []
    for (race, side), v in first.items():
        won, mark = outcome(race, side, oc)
        x = v["x"]
        board.append(dict(ask=v["ask"], fee=kfee(v["ask"]), won=won, mark=mark, race=race, side=side, edge=v["edge"], prob=v["prob"], pct=f(x["pct"]) or 0, ts=x["ts_utc"],
                          flip=x["flip"] == "1" and x["best_side"] == side))
    print(f"\nKalshi board (buy signals), first time each race + side showed; {stale} later rows dropped for a stale price:")
    print(score(board, "All board signals"))
    print(score([r for r in board if r["pct"] == 0], "  before the count (our model vs market)"))
    c = [r for r in board if r["pct"] > 0]
    print(score(c, "  once counting"))
    print(score([r for r in c if r["pct"] < 20], "    under 20% counted"))
    print(score([r for r in c if 20 <= r["pct"] < 98], "    20-98% counted"))
    print(score([r for r in c if r["pct"] >= 98], "    98%+ counted"))
    for lab, lo, hi in (("ask under 15c", 0, .15), ("ask 15-40c", .15, .40), ("ask 40-80c", .40, .80), ("ask 80c+", .80, 1.01)):
        print(score([r for r in board if lo <= r["ask"] < hi], "  " + lab))
    for lab, lo, hi in (("edge 3-10c", 0, .10), ("edge 10-25c", .10, .25), ("edge 25c+", .25, 2)):
        print(score([r for r in board if lo <= r["edge"] < hi], "  " + lab))
    print(score([r for r in board if r["side"] == "D"], "  buying the Democrat/non-Republican"))
    print(score([r for r in board if r["side"] == "R"], "  buying the Republican"))
    print("  biggest settled losers:", [(r["race"], r["side"], f"{r['ask'] * 100:.0f}c") for r in sorted([r for r in board if r["won"] is False], key=lambda r: -r["ask"])[:8]])
    print("  biggest settled winners:", [(r["race"], r["side"], f"{r['ask'] * 100:.0f}c") for r in sorted([r for r in board if r["won"] is True], key=lambda r: r["ask"])[:8]])

    # were we sharper than Kalshi? same moments, settled races, only races seen crossing that share of the count (the races
    # added at 03:46 UTC come in already well along, and a settled market has no price to compare)
    print("\nBrier score (lower is better; the moment each race crossed that share counted, settled races):")
    print(f"  {'counted':10}{'races':>6}{'ours':>8}{'market start':>14}{'Kalshi':>8}")
    for lo in (10, 25, 50, 75, 90):
        got, last = {}, {}
        for x in rows:
            pc, race = f(x["pct"]) or 0, x["race"]
            before = last.get(race)
            last[race] = pc
            if before is None or before >= lo or pc < lo or race in got:
                continue
            o = oc.get(race) or {}
            p, ms, b, ask = (f(x["p_v1"]) if f(x["p_v1"]) is not None else f(x["p_mkt"])), f(x["p_mstart"]), f(x["k_bid"]), f(x["k_ask"])
            if o.get("nyt_win") and None not in (p, ms, b, ask) and 0 < ask < 1:
                got[race] = (p, ms, (b + ask) / 2, 1.0 if o["nyt_win"] == "D" else 0.0)
        if got:
            n = len(got)
            br = [sum((v[k] - v[3]) ** 2 for v in got.values()) / n for k in range(3)]
            print(f"  {str(lo) + '%+':10}{n:6}{br[0]:8.3f}{br[1]:14.3f}{br[2]:8.3f}")

    # the same rules with the projector started from the market at poll close (logged beside ours on every pass)
    seen_b, seen_f = {}, {}
    for x in rows:
        ms = f(x["p_mstart"])
        if ms is None:
            continue
        for side, ask, prob in (("D", f(x["k_ask"]), ms), ("R", f(x["k_rask"]), 1 - ms)):
            if ask is None or not 0 < ask < 1:
                continue
            e = prob - ask - kfee(ask)
            if e < BOARD:
                continue
            won, mark = outcome(x["race"], side, oc)
            row = dict(ask=ask, fee=kfee(ask), won=won, mark=mark, race=x["race"], side=side)
            seen_b.setdefault((x["race"], side), row)
            if prob >= .45 and e >= .05 and ask <= .40 and (f(x["pct"]) or 0) >= 20:
                seen_f.setdefault((x["race"], side), row)
    print("\nIf the projector had started from the market at poll close (the road not taken, recomputed):")
    print(score(list(seen_b.values()), "Board signals"))
    print(score(list(seen_f.values()), "FLIPs, Kalshi"), [(k[0], k[1], f"{v['ask'] * 100:.0f}c", "open" if v["won"] is None else "won" if v["won"] else "lost") for k, v in seen_f.items()])


def house(a):
    hp = os.path.join(a.dir, "house_hist.json")
    if not os.path.exists(hp):
        return
    hist = json.load(open(hp, encoding="utf-8"))
    live = {r["id"]: r for r in json.load(open(os.path.join(a.dir, "house_live.json"), encoding="utf-8"))["races"]}
    bench = {r["id"]: r for r in json.load(open(os.path.join(a.dir, "house_bench.json"), encoding="utf-8"))["races"]}
    idx = json.load(open(os.path.join(a.dir, "kalshi_minutes", "index.json"), encoding="utf-8"))["markets"]
    by_event = collections.defaultdict(dict)
    res = {}
    for m in idx:
        t = m["ticker"]
        if t.endswith("-D") or t.endswith("-R"):
            ev = m["event"]
            by_event[ev][t[-1]] = t
            res[t] = m.get("result")
    import re
    EV = re.compile(r"^(?:KX)?HOUSE(?:RACE-)?([A-Z]{2})(\d{1,2}|AL)-")
    race_ev = collections.defaultdict(list)
    for ev, s in by_event.items():
        m = EV.match(ev)
        if m:
            race_ev[f"2026-H-{m.group(1)}-{1 if m.group(2) == 'AL' else int(m.group(2)):02d}"].append(s)
    candles = {}

    def load(t):
        if t not in candles:
            p = os.path.join(a.dir, "kalshi_minutes", t + ".csv.gz")
            rows = []
            if os.path.exists(p):
                with gzip.open(p, "rt", encoding="utf-8") as g:
                    for x in csv.DictReader(g):
                        rows.append((int(x["end_ts"]), f(x["bid_close"]), f(x["ask_close"])))
            candles[t] = rows
        return candles[t]

    def quote(t, ts):
        rows = load(t)
        i = bisect.bisect_right([r[0] for r in rows], ts) - 1
        return rows[i] if i >= 0 and ts - rows[i][0] <= 900 else None

    def asks(rid, ts):
        out = {}
        for s in race_ev.get(rid, []):
            qd, qr = quote(s.get("D"), ts) if s.get("D") else None, quote(s.get("R"), ts) if s.get("R") else None
            for side, q, o in (("D", qd, qr), ("R", qr, qd)):
                opts = [q[2]] if q and q[2] and 0 < q[2] < 1 else []
                if o and o[1] and 0 < o[1] < 1:
                    opts.append(1 - o[1])
                if opts and (side not in out or min(opts) < out[side]):
                    out[side] = min(opts)
        return out

    def result(rid, side):
        call = (live.get(rid) or {}).get("call")
        if call in ("D", "R"):
            return call == side
        for s in race_ev.get(rid, []):
            t = s.get(side)
            if t and res.get(t) in ("yes", "no"):
                return res[t] == "yes"
        return None

    def run(t0, t1, label):
        firsts, ffirst, rflip = {}, {}, {}
        for rid, pts in hist.items():
            if not rid.startswith("2026-H-") or bench.get(rid, {}).get("kind") != "ok":
                continue
            for x in pts:
                ts, pct, m, p = x[0], x[1], x[2], x[4]
                if p is None or not (t0 <= ts < t1):
                    continue
                aa = asks(rid, secs(ts))
                for side, ask in aa.items():
                    prob = p if side == "D" else 1 - p
                    e = prob - ask - kfee(ask)
                    if e < BOARD:
                        continue
                    row = dict(ask=ask, fee=kfee(ask), won=result(rid, side), mark=None, rid=rid, side=side, edge=e, prob=prob, pct=pct or 0, m=m, ts=ts)
                    firsts.setdefault((rid, side), row)
                    rule = prob >= .45 and e >= .05 and .08 <= ask <= .40 and (pct or 0) >= 20
                    lead = m is not None and (m if side == "D" else -m) >= 1
                    if rule:
                        rflip.setdefault((rid, side), row)
                    if rule and lead:
                        ffirst.setdefault((rid, side), row)
        print(f"\n{label}")
        rows = list(firsts.values())
        print(score(rows, "All board signals (recomputed)"))
        for lab, lo, hi in (("ask under 15c", 0, .15), ("ask 15-40c", .15, .40), ("ask 40-80c", .40, .80), ("ask 80c+", .80, 1.01)):
            print(score([r for r in rows if lo <= r["ask"] < hi], "  " + lab))
        print(score(list(rflip.values()), "FLIP rule, no count guard"))
        fl = list(ffirst.values())
        print(score(fl, "FLIP rule + leading on screen by 1+"))
        for r in sorted(fl, key=lambda r: r["ts"]):
            res_ = "open" if r["won"] is None else "WON" if r["won"] else "lost"
            print(f"   {r['ts'][5:16]} {r['rid'][7:]} {r['side']} ask {r['ask'] * 100:4.1f}c ours {100 * r['prob']:3.0f}% {r['pct']:5.1f}% counted margin {r['m']:+6.1f} -> {res_}")

    print("\nHOUSE (recomputed; hist.json only covers counting races):")
    run("2026-11-04T04:07:00Z", "2026-11-04T05:08:00Z", "Kalshi board, district totals only (11:07 pm - 12:08 am ET):")
    run("2026-11-04T05:08:00Z", "2026-11-05T00:00:00Z", "Kalshi board, county by county (from 12:08 am ET):")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    desk(a)
    house(a)


if __name__ == "__main__":
    main()
