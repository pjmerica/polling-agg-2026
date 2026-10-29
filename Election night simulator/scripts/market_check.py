"""Did the 2024 markets misread the count, and would the projector have caught it?

For every 2024 race with an NYT timeline and minute prices (market_history.py), at every NYT
update from 5% to 99% counted:
  - the projector's P(non-Republican wins), live_project.project() with the race's own state history
    from 2020 and 2022 only (2024 left out) and the market's price at poll close as the starting point:
    exactly what the live tool would have printed, 2 minutes after NYT posted the update;
  - what the market charged at that moment (Kalshi: the minute's bid/ask; Polymarket: its minute price
    +/- 1 cent, since no book history survives);
  - a trade whenever the projector's edge after fees beat a threshold, settled on the real result.
Also: was the market or the projector closer to the result (Brier), and did the edge predict where the
market went next (if markets were slow, they should drift toward the projector)?

NYT's timestamps are when NYT posted; AP and Decision Desk feeds that traders watch are often faster.
So the market had at least the projector's information and the test is, if anything, unfair to the
projector.

    py "Election night simulator/scripts/market_check.py"

Writes data/processed/market_check_2024_points.csv (every update) and market_check_2024_trades.csv.
"""
import datetime as dt
import glob
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "State election results", "scripts"))
import live_project as lp  # noqa: E402
import swing_analysis as sa  # noqa: E402
import volatility as vol  # noqa: E402  - registers every state's poll close with swing_analysis
from utils.fees import leg_fee, kalshi_spec, polymarket_spec  # noqa: E402

RAW_NYT = os.path.join(REPO, "State election results", "data", "raw", "nyt_all")
HIST = os.path.join(ROOT, "data", "raw", "market_history", "2024")
PROC = os.path.join(ROOT, "data", "processed")
LAG = dt.timedelta(minutes=2)          # capture every 2 min, then project
POLY_HALF_SPREAD = 0.01
THRESHOLDS = [0.03, 0.05, 0.10]
REENTRY = dt.timedelta(minutes=15)     # one trade per race and side per 15 minutes
FEES = {"kalshi": kalshi_spec(1), "polymarket": polymarket_spec(0.04)}  # today's schedules


def timelines():
    """{(year, ST, office): (pct array, margin array, final, [datetimes])} for every general race."""
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW_NYT, "*", "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        gen = sa.races_2020(path, d) if "data" in d else sa.races_new(path, d)
        for r in gen:
            office = vol.OFFICE.get(str(r["office"]).lower())
            if r["kind"] != "G" or not office:
                continue
            x = vol.series(r)
            if not x:
                continue
            s, final, _ = x
            pct, mar, ts = [], [], []
            for t, share, m in s:
                if not pct or share > pct[-1]:
                    pct.append(share)
                    mar.append(m)
                    ts.append(t)
            out[(r["date"].year, r["state"], office)] = (np.array(pct), np.array(mar), final, ts)
    return out


def history(tl):
    """live_project's history shape, keyed by state abbreviation: every year's races."""
    h = {}
    for (year, st, office), (pct, mar, final, _) in tl.items():
        h.setdefault(st, []).append((year, office, pct, mar, final))
    return h


def minute_frame(race):
    """Per-minute D-side quotes: kalshi_bid/ask, poly (price), forward-filled."""
    idx = pd.date_range(lp_dt(1730847600), lp_dt(1731283200), freq="1min", tz="UTC")
    df = pd.DataFrame(index=idx)
    k = os.path.join(HIST, race, "kalshi.csv")
    p = os.path.join(HIST, race, "polymarket.csv")
    if os.path.exists(k):
        x = pd.read_csv(k)
        x.index = pd.to_datetime(x.ts, unit="s", utc=True)
        x = x[~x.index.duplicated()]
        df["k_bid"] = x.bid.reindex(idx, method="ffill")
        df["k_ask"] = x.ask.reindex(idx, method="ffill")
    if os.path.exists(p):
        x = pd.read_csv(p)
        x.index = pd.DatetimeIndex(pd.to_datetime(x.ts, unit="s", utc=True)).floor("min")
        x = x[~x.index.duplicated(keep="last")]
        df["poly"] = x.p.reindex(idx, method="ffill")
    return df


def lp_dt(ts):
    return pd.Timestamp(ts, unit="s", tz="UTC")


def quote(df, t):
    """{venue: (bid, ask)} at time t (the last minute at or before t)."""
    t = pd.Timestamp(t).tz_convert("UTC").floor("min")
    if t not in df.index:
        return {}
    row = df.loc[t]
    q = {}
    if "k_bid" in df and row.k_bid == row.k_bid and row.k_ask == row.k_ask and 0 < row.k_ask:
        q["kalshi"] = (float(row.k_bid), float(row.k_ask))
    if "poly" in df and row.poly == row.poly:
        # no Polymarket book survives; in the minutes that matter Kalshi's spread blew out (Michigan
        # Senate, 5 am ET: 0.30 / 0.88), so assume Polymarket's was at least as wide as Kalshi's
        half = POLY_HALF_SPREAD
        if "kalshi" in q:
            half = max(half, (q["kalshi"][1] - q["kalshi"][0]) / 2)
        q["polymarket"] = (max(0.0, row.poly - half), min(1.0, row.poly + half))
    return q


def mid(q):
    for v in ("kalshi", "polymarket"):
        if v in q:
            return (q[v][0] + q[v][1]) / 2
    return None


def contract_results():
    """{(race, venue): True/False}: how the recorded non-Republican contract actually settled."""
    p = os.path.join(HIST, "index.csv")
    if not os.path.exists(p):
        return {}
    ix = pd.read_csv(p)
    return {(r.race, r.venue): str(r.result).lower() == "yes" for r in ix.itertuples()}


def main():
    tl = timelines()
    hist = history(tl)
    lp._pool_cache.clear()
    settled = contract_results()
    points, trades, lows = [], [], []
    races = sorted(os.listdir(HIST)) if os.path.isdir(HIST) else []
    for race in races:
        if not os.path.isdir(os.path.join(HIST, race)):
            continue
        st, office = race.split("-", 1)
        key = (2024, st, office)
        if key not in tl:
            continue
        pct, mar, final, ts = tl[key]
        won = final > 0
        # a contract that settled against the count's winner measures something else: Polymarket's
        # Maine 2024 "another party" contract resolved No although King (I) won - it counts him as the
        # Democrat. Drop those venues; settling on them made $56 of fake profit.
        wrong = [v for v in ("kalshi", "polymarket") if settled.get((race, v), won) != won]
        if wrong:
            print(f"{race}: {', '.join(wrong)} contract settled against the count's winner - left out")
        df = minute_frame(race)
        for v in wrong:
            df = df.drop(columns=[c for c in df.columns if c.startswith("k_" if v == "kalshi" else "poly")])
        close = (dt.datetime(2024, 11, 5, tzinfo=dt.timezone(dt.timedelta(hours=-5)))
                 + dt.timedelta(hours=sa.close_hours(st, dt.date(2024, 11, 5))))
        p0 = mid(quote(df, close - dt.timedelta(minutes=1)))
        if p0 is None or not 0.03 <= p0 <= 0.97:
            continue                                   # no price, or nothing to trade
        mu0 = lp.PRIOR_SD * lp.phi_inv(p0)
        last_entry = {}
        for share, m, t in zip(pct, mar, ts):
            if share < 5 or share >= 99:
                continue
            td = t + LAG
            q = quote(df, td)
            mk = mid(q)
            if mk is None:
                continue
            res = lp.project(hist, st, share, m, mu0, lp.PRIOR_SD, skip_year=2024)
            later = mid(quote(df, td + dt.timedelta(minutes=30)))
            points.append(dict(race=race, t=td.isoformat(), pct=round(share, 1), margin=round(m, 2),
                               final=round(final, 2), won=int(won), p_close=round(p0, 3),
                               proj=round(res["mu"], 2), p_proj=round(res["p_win"], 4),
                               steady=res["steady"], market=round(mk, 4),
                               market_30m=None if later is None else round(later, 4)))
            k_spread = q["kalshi"][1] - q["kalshi"][0] if "kalshi" in q else None
            for venue, (bid, ask) in q.items():
                if venue == "polymarket" and k_spread is None:
                    continue        # no way to bound Polymarket's spread (thin markets like MS-Senate)
                for side, prob, price in (("D", res["p_win"], ask), ("R", 1 - res["p_win"], 1 - bid)):
                    if not 0.01 <= price <= 0.99:
                        continue
                    edge = prob - price - leg_fee(venue, FEES[venue], price)
                    if edge < THRESHOLDS[0]:
                        continue
                    k = (venue, side)
                    if k in last_entry and td - last_entry[k] < REENTRY:
                        continue
                    last_entry[k] = td
                    pay = 1.0 if (side == "D") == won else 0.0
                    trades.append(dict(race=race, venue=venue, t=td.isoformat(), pct=round(share, 1),
                                       margin=round(m, 2), side=side, price=round(price, 3),
                                       p_proj=round(prob, 3), edge=round(edge, 3), steady=res["steady"],
                                       kalshi_spread=None if k_spread is None else round(k_spread, 3),
                                       pnl=round(pay - price - leg_fee(venue, FEES[venue], price), 3)))
        lows.append(winner_low(race, df, pct, ts, won, close))
    os.makedirs(PROC, exist_ok=True)
    pts = pd.DataFrame(points)
    trd = pd.DataFrame(trades)
    pts.to_csv(os.path.join(PROC, "market_check_2024_points.csv"), index=False)
    trd.to_csv(os.path.join(PROC, "market_check_2024_trades.csv"), index=False)
    report(pts, trd, pd.DataFrame([x for x in lows if x]))


def winner_low(race, df, pct, ts, won, close):
    """How cheap the eventual winner got once half the vote was counted, until 99% was: the lowest
    mid (Kalshi when its spread was 10c or less, else Polymarket) and the minutes spent under 30c."""
    half = next((t for p, t in zip(pct, ts) if p >= 50), None)
    done = next((t for p, t in zip(pct, ts) if p >= 99), ts[-1])
    if half is None:
        return None
    w = df.loc[pd.Timestamp(half).tz_convert("UTC"):pd.Timestamp(done).tz_convert("UTC")]
    if w.empty:
        return None
    m = pd.Series(np.nan, index=w.index)
    if "k_bid" in w:
        ok = (w.k_ask - w.k_bid) <= 0.10
        m[ok] = ((w.k_bid + w.k_ask) / 2)[ok]
    if "poly" in w:
        m = m.fillna(w.poly)
    m = m.dropna()
    if m.empty:
        return None
    win = m if won else 1 - m
    return dict(race=race, winner="non-Rep" if won else "Rep", low=round(float(win.min()), 3),
                when_low=win.idxmin().tz_convert("America/New_York").strftime("%a %H:%M ET"),
                min_under_30=int((win < 0.30).sum()), min_under_15=int((win < 0.15).sum()))


def report(pts, trd, lows):
    print(f"{pts.race.nunique()} races with a live market at poll close (3-97%), {len(pts)} NYT updates\n")
    if not lows.empty:
        bad = lows[lows.low < 0.5].sort_values("low")
        print(f"Eventual winners priced under 50c after half the vote was counted: {len(bad)} of {len(lows)} races\n")
        print(bad.to_string(index=False), "\n")
    pts["b_mkt"] = (pts.market - pts.won) ** 2
    pts["b_proj"] = (pts.p_proj - pts.won) ** 2
    pts["bucket"] = pd.cut(pts.pct, [0, 20, 40, 60, 80, 99], labels=["5-20", "20-40", "40-60", "60-80", "80-99"])
    # each race counts once per bucket: average its updates first, so a race with 300 updates doesn't swamp
    per = pts.groupby(["bucket", "race"], observed=True)[["b_mkt", "b_proj"]].mean().reset_index()
    t = per.groupby("bucket", observed=True).agg(races=("race", "size"), brier_market=("b_mkt", "mean"),
                                                 brier_projector=("b_proj", "mean"))
    print("Who was closer to the result? (Brier, lower is better; each race weighted equally)\n")
    print(t.round(4).to_string(), "\n")
    pts["edge"] = pts.p_proj - pts.market
    pts["drift"] = pts.market_30m - pts.market
    ok = pts.dropna(subset=["drift"])
    ok = ok[ok.edge.abs() > 0.03]
    if len(ok) > 10:
        same = (np.sign(ok.edge) == np.sign(ok.drift)) & (ok.drift != 0)
        print(f"When the projector and market differed by 3+ pts ({len(ok)} updates): the market moved toward "
              f"the projector in the next 30 min {same.mean():.0%} of the time "
              f"(corr {ok.edge.corr(ok.drift):+.2f})\n")
    if trd.empty:
        print("No trades at any threshold.")
        return
    print("Trades (1 contract each; at most one per race, venue and side per 15 min; settled on the result):\n")
    rows = []
    for th in THRESHOLDS:
        for venue in ("kalshi", "polymarket"):
            x = trd[(trd.edge >= th) & (trd.venue == venue)]
            if x.empty:
                continue
            rows.append(dict(threshold=f"{th * 100:.0f}c", venue=venue, trades=len(x), races=x.race.nunique(),
                             won=f"{(x.pnl > 0).mean():.0%}", avg_pnl_c=round(100 * x.pnl.mean(), 1),
                             total_pnl=round(x.pnl.sum(), 2),
                             steady_only_avg_c=round(100 * x[x.steady == True].pnl.mean(), 1)  # noqa: E712
                             if (x.steady == True).any() else None))  # noqa: E712
    print(pd.DataFrame(rows).to_string(index=False), "\n")
    x = trd[trd.edge >= THRESHOLDS[1]].copy()
    x["counted"] = pd.cut(x.pct, [0, 40, 70, 99], labels=["5-40%", "40-70%", "70-99%"])
    x["kalshi_book"] = np.where(x.kalshi_spread.isna(), "none", np.where(x.kalshi_spread <= 0.05, "tight", "wide"))
    print("5c threshold, both venues: avg P&L per contract (cents) and trades\n")
    print(x.pivot_table(index="counted", columns="kalshi_book", values="pnl",
                        aggfunc=lambda s: f"{100 * s.mean():+.1f} ({len(s)})", observed=True).to_string(), "\n")
    x = trd[(trd.edge >= THRESHOLDS[1]) & (trd.venue == "kalshi")]
    if not x.empty:
        by = x.groupby("race").agg(trades=("pnl", "size"), pnl=("pnl", "sum"),
                                   sides=("side", lambda s: "".join(sorted(set(s))))).sort_values("pnl")
        print("Kalshi, 5c threshold, by race:\n")
        print(by.round(2).to_string())


if __name__ == "__main__":
    main()
