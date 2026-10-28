"""Election-night projector, v0 (statewide): where the count will finish, and what the markets pay.

At any moment the visible margin is the counted votes' margin. What matters is the margin of
the votes NOT yet counted, and in most states that leans the same way every year (Election Day
votes after early votes, Wayne County last, Nevada's late mail). From the 2020-2024 NYT
timelines (State election results/data/processed/state_timeseries.csv) this learns, per state and per share counted p,
    g(p) = (final margin - margin at p) / (1 - p)
= how much more Democratic (non-Republican) the uncounted votes were than the counted ones.
Live:
    count estimate   final ~ N(m + (1 - p) * g_mean, ((1 - p) * g_sd)^2)
    model baseline   final ~ N(prior_sd * Phi^-1(model win prob), prior_sd^2)
combined by precision (early in the count the baseline dominates, late the count does),
-> P(the non-Republican wins), compared with the best Kalshi/Polymarket asks after fees.

    py "Election night simulator/scripts/live_project.py"                  # latest NYT + market captures
    py "Election night simulator/scripts/live_project.py" --watch 60       # repeat every 60 s
    py "Election night simulator/scripts/live_project.py" --race MI-Sen --pct 45 --margin -3.2   # what-if
    py "Election night simulator/scripts/live_project.py" --backtest       # leave-one-year-out check

Margins are non-Republican minus Republican, points of all votes (as state_curves.py). Maine and
Alaska are first-round margins: ranked-choice tabulation can still change the winner there.
v0 ignores time of night and which counties are out; the county x vote-type projector (v1) will not.
"""
import argparse
import csv
import datetime as dt
import glob
import gzip
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
# the count history and the NYT captures belong to the State election results project
RESULTS = os.path.join(REPO, "State election results")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(RESULTS, "scripts"))
from utils.fees import leg_fee, kalshi_spec, polymarket_spec  # noqa: E402

HISTORY = os.path.join(RESULTS, "data", "processed", "state_timeseries.csv")   # state_curves.py
LIVE = os.path.join(RESULTS, "data", "raw", "live")                            # capture_live.py
MARKETS = os.path.join(ROOT, "data", "raw", "markets")                         # capture_markets.py
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "data", "raw", "projections.csv")

PRIOR_SD = 6.0          # statewide forecast miss, points
YEAR_WEIGHT = {2020: 0.5, 2022: 1.0, 2024: 1.0}   # 2020's pandemic mail made its late shifts unusual
POOL_K = 2.0            # pseudo-years of the all-state spread mixed into each state's spread
SD_FLOOR = 0.4          # points: rounding, late corrections, provisional ballots
# The spread of g between 2-3 past years understates the next year's: leave-one-year-out the
# 80% band held only 57% of results unwidened, 82% at x2.0, where Brier and log loss are best
# (2026-10-28; pulling g toward 0 when years disagree lowered the miss but raised both scores).
SD_SCALE = 2.0

ABBR = {"AK": "alaska", "GA": "georgia", "IA": "iowa", "KS": "kansas", "ME": "maine", "MI": "michigan",
        "NE": "nebraska", "NV": "nevada", "OH": "ohio", "OR": "oregon", "SC": "south-carolina", "TX": "texas"}
OFFICE = {"Sen": "Senate", "Gov": "Governor"}
REP = {"republican", "gop", "rep"}


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def phi_inv(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- history: how the uncounted vote leaned, per state ----------

def load_history():
    """{state: [(year, race, pct array, margin array, final margin)]} from state_timeseries.csv."""
    ts = pd.read_csv(HISTORY)
    out = {}
    for (year, state, race), g in ts.groupby(["year", "state", "race"]):
        g = g.sort_values("ts_utc")
        final = g.loc[g.pct_of_final.idxmax()]
        if final.pct_of_final < 99:
            continue
        pct, mar = [], []
        for p, m in zip(g.pct_of_final, g.margin_pts):
            if not pct or p > pct[-1]:          # the share counted only grows
                pct.append(p)
                mar.append(m)
        out.setdefault(state, []).append((int(year), race, np.array(pct), np.array(mar),
                                          float(final.margin_pts)))
    return out


def lean_at(hist, state, p, skip_year=None):
    """-> (g_mean, g_sd, years used, same direction every year) at share counted p (0-100);
    None if no history."""
    by_year = {}
    for year, race, pct, mar, final in hist.get(state, []):
        if year == skip_year or p < pct[0] or p >= 99.5:
            continue
        m = float(np.interp(p, pct, mar))
        by_year.setdefault(year, []).append((final - m) / (1 - p / 100))
    if not by_year:
        return None
    ys = sorted(by_year)
    g = np.array([np.mean(by_year[y]) for y in ys])     # a year's President and Senate move together
    w = np.array([YEAR_WEIGHT.get(y, 1.0) for y in ys])
    mean = float(np.sum(w * g) / np.sum(w))
    var_state = float(np.sum(w * (g - mean) ** 2) / np.sum(w)) if len(g) > 1 else 0.0
    var_pool = pooled_var(hist, p, skip_year)
    n = float(np.sum(w))
    var = (n * var_state + POOL_K * var_pool) / (n + POOL_K)
    steady = bool(np.all(g > 0) or np.all(g < 0))
    return mean, SD_SCALE * math.sqrt(var * (1 + 1 / n)), ys, steady


_pool_cache = {}


def pooled_var(hist, p, skip_year):
    """Across all states: the spread of g between years within a state, at p (rounded to 5)."""
    key = (round(p / 5) * 5, skip_year)
    if key in _pool_cache:
        return _pool_cache[key]
    q = max(key[0], 1)
    devs = []
    for state, races in hist.items():
        by_year = {}
        for year, race, pct, mar, final in races:
            if year == skip_year or q < pct[0] or q >= 99.5:
                continue
            by_year.setdefault(year, []).append((final - float(np.interp(q, pct, mar))) / (1 - q / 100))
        g = [np.mean(v) for v in by_year.values()]
        if len(g) > 1:
            devs += list(np.array(g) - np.mean(g))
    v = float(np.mean(np.square(devs)) * 1.5) if devs else 25.0   # x1.5: few years per state
    _pool_cache[key] = v
    return v


def project(hist, state, pct, margin, prior_mu=None, prior_sd=PRIOR_SD, skip_year=None):
    """-> dict(mu, sd, p_win, count_mu, count_sd, steady)."""
    lean = lean_at(hist, state, pct, skip_year) if pct < 99.5 else (0.0, 0.0, [], True)
    steady = None
    if lean is None:                                      # before the first historical point
        c_mu, c_sd = margin, 60.0
    else:
        g_mu, g_sd, _, steady = lean
        rem = 1 - pct / 100
        c_mu, c_sd = margin + rem * g_mu, math.hypot(rem * g_sd, SD_FLOOR)
    if prior_mu is None:
        mu, sd = c_mu, c_sd
    else:
        wc, wp = 1 / c_sd ** 2, 1 / prior_sd ** 2
        mu, sd = (wc * c_mu + wp * prior_mu) / (wc + wp), math.sqrt(1 / (wc + wp))
    return dict(mu=mu, sd=sd, p_win=phi(mu / sd), count_mu=c_mu, count_sd=c_sd, steady=steady)


# ---------- inputs: forecast, NYT capture, market capture ----------

def load_forecast():
    s = open(os.path.join(REPO, "docs", "forecast_data.js"), encoding="utf-8").read()
    races = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))["races"]
    return {r["id"]: r for r in races}


FC_ID = {"OH-Sen": "2026_OH_Senate-S"}     # Ohio's Senate race is the special election


def prior_for(fc, race_key):
    """Model baseline for the non-Republican: (name, win prob)."""
    st, off = race_key.split("-")
    r = fc.get(FC_ID.get(race_key, f"2026_{st}_{OFFICE[off]}"))
    if not r:
        return None
    opp = max((c for c in r["cands"] if c["party"] != "REP"), key=lambda c: c["win"])
    return opp["name"], opp["win"]


def latest_nyt(date, race_key):
    files = sorted(glob.glob(os.path.join(LIVE, date, race_key, "*.json.gz")))
    if not files:
        return None
    d = json.load(gzip.open(files[-1]))
    r = d["races"][0]
    party = {k: str((m.get("party") or {}).get("nyt_id", "")).lower()
             for k, m in r["candidate_metadata"].items()}
    top = r["top_reporting_unit"]
    votes = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in top["candidates"]}
    total = sum(votes.values())
    reps = [k for k in votes if party.get(k) in REP]
    opps = [k for k in votes if party.get(k) not in REP]
    if not total or not reps or not opps:
        return dict(pct=0.0, margin=0.0, total=total, stamp=os.path.basename(files[-1])[:16])
    rep, opp = max(reps, key=votes.get), max(opps, key=votes.get)
    return dict(pct=float(top.get("eevp") or 0), total=total,
                margin=100 * (votes[opp] - votes[rep]) / total,
                stamp=os.path.basename(files[-1])[:16])


def _is_rep(venue, outcome, market):
    if venue == "kalshi":                 # Kalshi labels outcomes by name; the ticker says the party
        return str(market).upper().endswith("-R")
    s = f"{outcome} {market}".lower()
    return "(r)" in s or "republican" in s or "sullivan" in s


def load_markets(date):
    """{race: {venue: DataFrame of the D and R contracts' rows}} for the whole day. The
    non-Republican side is the most traded non-Republican contract (Nebraska: Osborn, not
    Kalshi's Democratic placeholder)."""
    out = {}
    for venue in ("kalshi", "polymarket"):
        path = os.path.join(MARKETS, date, f"{venue}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df["side"] = ["R" if _is_rep(venue, o, m) else "D" for o, m in zip(df.outcome, df.market)]
        for race, g in df.groupby("race"):
            d = g[g.side == "D"]
            if d.market.nunique() > 1:
                top = d.groupby("market").bid.mean().idxmax()
                g = g[(g.side == "R") | (g.market == top)]
            out.setdefault(race, {})[venue] = g
    return out


def latest_books(markets, race):
    """{venue: {'D'/'R': dict(bid, ask, market, spec)}} from each venue's last pass."""
    fee_k, fee_p = _fee_specs()
    out = {}
    for venue, g in markets.get(race, {}).items():
        last = g[g.ts_utc == g.ts_utc.max()]
        side = {}
        for r in last.itertuples():
            spec = (kalshi_spec(fee_k.get(r.market.rsplit("-", 2)[0], 1)) if venue == "kalshi"
                    else polymarket_spec(fee_p.get(r.market, 0.04)))
            side[r.side] = dict(bid=r.bid, ask=r.ask, market=r.market, spec=spec, ts=r.ts_utc)
        out[venue] = side
    return out


def market_baseline(markets, race, close_utc):
    """The markets' P(non-Republican) at the state's poll close (mid, D / (D + R), averaged over
    venues), from the last capture before the close; the day's first capture if none is."""
    ps = []
    for venue, g in markets.get(race, {}).items():
        before = g[g.ts_utc <= close_utc]
        snap = before[before.ts_utc == before.ts_utc.max()] if len(before) else g[g.ts_utc == g.ts_utc.min()]
        mid = {r.side: (r.bid + r.ask) / 2 for r in snap.itertuples() if r.bid == r.bid and r.ask == r.ask}
        if "D" in mid and "R" in mid and mid["D"] + mid["R"] > 0:
            ps.append(mid["D"] / (mid["D"] + mid["R"]))
        elif "D" in mid:
            ps.append(mid["D"])
    return float(np.mean(ps)) if ps else None


def close_utc(date, state):
    from state_curves import CLOSE_ET               # main poll close, hours after midnight ET
    d = dt.datetime.fromisoformat(date)
    return (d + dt.timedelta(hours=CLOSE_ET[state] + 5)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fee_specs():
    k, p = {}, {}
    kp = os.path.join(REPO, "data", "raw", "kalshi_markets.csv")
    pp = os.path.join(REPO, "data", "raw", "polymarket_markets.csv")
    if os.path.exists(kp):
        d = pd.read_csv(kp, usecols=["series_ticker", "fee_multiplier"], low_memory=False).dropna()
        k = dict(zip(d.series_ticker, d.fee_multiplier))
    if os.path.exists(pp):
        d = pd.read_csv(pp, usecols=["market_slug", "fee_rate"], low_memory=False).dropna()
        p = dict(zip(d.market_slug, d.fee_rate))
    return k, p


def best_trade(p_win, books):
    """Best taker buy across venues: (venue, side, ask, edge per $1 contract after fee)."""
    best = None
    for venue, side in (books or {}).items():
        for k, prob in (("D", p_win), ("R", 1 - p_win)):
            s = side.get(k)
            if not s or s["ask"] != s["ask"] or not s["ask"]:
                continue
            venue_name = "kalshi" if venue == "kalshi" else "polymarket"
            edge = prob - s["ask"] - leg_fee(venue_name, s["spec"], s["ask"])
            if best is None or edge > best[3]:
                best = (venue, k, s["ask"], edge)
    return best


# ---------- modes ----------

RACES = ["GA-Gov", "SC-Sen", "OH-Gov", "OH-Sen", "MI-Sen", "TX-Sen", "TX-Gov", "KS-Sen", "KS-Gov",
         "ME-Sen", "IA-Sen", "NE-Sen", "NV-Gov", "OR-Gov", "AK-Sen"]     # poll-closing order


def _with_baseline(hist, state, nyt, p0, prior_sd):
    """Projection from a baseline P(non-Republican) p0 (model or market), or None."""
    if p0 is None:
        return None
    mu0 = prior_sd * phi_inv(p0)
    if nyt["pct"] <= 0:
        return dict(mu=mu0, sd=prior_sd, p_win=p0, steady=None)
    return project(hist, state, nyt["pct"], nyt["margin"], mu0, prior_sd)


def run_live(a, hist, fc):
    mk = load_markets(a.date)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    print(f"\n{now}  margins: non-Republican minus Republican; P = P(non-Republican wins)")
    print(f"P mkt starts from the markets' price at poll close and adds only the count; P mod starts "
          f"from our model. Best buy uses P {'mkt' if a.baseline == 'market' else 'mod'}.")
    print(f"{'race':7} {'counted':>7} {'margin':>6} | {'proj':>6} {'+/-80%':>6} {'P mkt':>5} {'P mod':>5} "
          f"{'close':>5} | {'K bid/ask':>9} {'PM bid/ask':>10} | best buy")
    for race in ([a.race] if a.race else RACES):
        state = ABBR[race.split("-")[0]]
        pr = prior_for(fc, race)
        if a.pct is not None:
            nyt = dict(pct=a.pct, margin=a.margin, stamp="what-if")
        else:
            nyt = latest_nyt(a.date, race) or dict(pct=0.0, margin=0.0, stamp="-")
        p_close = market_baseline(mk, race, close_utc(a.date, state))
        by_mkt = _with_baseline(hist, state, nyt, p_close, a.prior_sd)
        by_mod = _with_baseline(hist, state, nyt, pr[1] if pr else None, a.prior_sd)
        res = (by_mkt if a.baseline == "market" else by_mod) or by_mod or by_mkt
        books = latest_books(mk, race)
        bt = best_trade(res["p_win"], books) if res else None

        def ba(v):
            s = books.get(v, {}).get("D")
            return f"{s['bid']:.2f}/{s['ask']:.2f}" if s and s["ask"] == s["ask"] else "-"

        def f2(x):
            return f"{x:5.2f}" if x is not None else "    -"
        trade = (f"{bt[1]} on {bt[0]} @{bt[2]:.2f}: {bt[3] * 100:+.1f}c" if bt else "-")
        # '?': past years' late votes leaned opposite ways at this point in the count, so the
        # direction is a guess (backtest: GA, OR, NV, AK, SC did worse than the visible margin)
        flag = "?" if res and res["steady"] is False else " "
        print(f"{race:7} {nyt['pct']:6.1f}% {nyt['margin']:+6.1f} |{flag}{res['mu']:+6.1f} "
              f"{1.2816 * res['sd']:6.1f} {f2(by_mkt and by_mkt['p_win'])} {f2(by_mod and by_mod['p_win'])} "
              f"{f2(p_close)} | {ba('kalshi'):>9} {ba('polymarket'):>10} | {trade}")
        rows.append(dict(ts_utc=now, race=race, nyt_file=nyt["stamp"], pct=round(nyt["pct"], 2),
                         margin=round(nyt["margin"], 2), baseline=a.baseline,
                         proj=round(res["mu"], 2), sd=round(res["sd"], 2),
                         p_mkt=round(by_mkt["p_win"], 4) if by_mkt else "",
                         p_model=round(by_mod["p_win"], 4) if by_mod else "",
                         p_close=round(p_close, 4) if p_close is not None else "",
                         model=pr[1] if pr else "",
                         steady="" if res["steady"] is None else int(res["steady"]),
                         best_venue=bt[0] if bt else "", best_side=bt[1] if bt else "",
                         best_ask=bt[2] if bt else "", edge=round(bt[3], 4) if bt else ""))
    if a.pct is None:
        new = not os.path.exists(OUT)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)


def run_backtest(hist):
    """Every 2020-2024 race, each year predicted from the OTHER years only, count alone (no model
    baseline: we have no archived 2020-2024 forecasts). Is the band honest, and does it beat
    'the current leader wins'?"""
    grid = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95]
    recs = []
    for state, races in hist.items():
        for year, race, pct, mar, final in races:
            for p in grid:
                if p < pct[0]:
                    continue
                m = float(np.interp(p, pct, mar))
                res = project(hist, state, p, m, skip_year=year)
                win = final > 0
                recs.append(dict(state=state, year=year, race=race, p=p, steady=res["steady"],
                                 err=final - res["mu"],
                                 z=(final - res["mu"]) / res["sd"], p_win=res["p_win"], win=win,
                                 naive=float(m > 0), naive_err=final - m))
    df = pd.DataFrame(recs)
    df["brier"] = (df.p_win - df.win) ** 2
    df["brier_naive"] = (df.naive - df.win) ** 2
    df["in80"] = df.z.abs() < 1.2816
    t = df.groupby("p").agg(races=("z", "size"), mae=("err", lambda e: e.abs().mean()),
                            mae_naive=("naive_err", lambda e: e.abs().mean()),
                            in80=("in80", "mean"), brier=("brier", "mean"),
                            brier_naive=("brier_naive", "mean"))
    print("Leave-one-year-out, count only (no model baseline). mae = |final - projection|, points;")
    print("naive = the visible margin as the forecast / the visible leader wins. in80 should be ~0.80.\n")
    print(t.round(3).to_string())
    by_state = df[df.p.between(20, 80)].groupby("state").agg(
        mae=("err", lambda e: e.abs().mean()), mae_naive=("naive_err", lambda e: e.abs().mean()),
        in80=("in80", "mean"), brier=("brier", "mean"), brier_naive=("brier_naive", "mean"))
    print("\nBy state, 20-80% counted:\n")
    print(by_state.round(3).to_string())
    os.makedirs(PROC, exist_ok=True)
    df.to_csv(os.path.join(PROC, "live_project_backtest.csv"), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-11-03")
    ap.add_argument("--race", help="one race key, e.g. MI-Sen")
    ap.add_argument("--pct", type=float, help="what-if: share counted (0-100); needs --race and --margin")
    ap.add_argument("--margin", type=float, help="what-if: counted margin, non-Republican minus Republican")
    ap.add_argument("--prior-sd", type=float, default=PRIOR_SD)
    ap.add_argument("--baseline", choices=["market", "model"], default="market",
                    help="what the best-buy edge starts from: the markets' price at poll close "
                         "(edge = the count only) or our model (edge includes model-vs-market disagreement)")
    ap.add_argument("--watch", type=int, help="repeat every N seconds")
    ap.add_argument("--backtest", action="store_true")
    a = ap.parse_args()
    hist = load_history()
    if a.backtest:
        run_backtest(hist)
        return
    fc = load_forecast()
    while True:
        run_live(a, hist, fc)
        if not a.watch:
            break
        sys.stdout.flush()
        time.sleep(a.watch)
        fc = load_forecast()


if __name__ == "__main__":
    main()
