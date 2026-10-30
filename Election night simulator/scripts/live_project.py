"""Election-night projector, v0 (statewide): where the count will finish, and what the markets pay.

At any moment the visible margin is the counted votes' margin. What matters is the margin of
the votes NOT yet counted, and in most states that leans the same way every year (Election Day
votes after early votes, Wayne County last, Nevada's late mail). From the 2020-2024 NYT
timelines (State election results/data/processed/state_timeseries.csv) this learns, per state and per share counted p,
    g(p) = (final margin - margin at p) / (1 - p)
= how much more Democratic (non-Republican) the uncounted votes were than the counted ones.
Live:
    count estimate   final ~ N(m + (1 - p) * g_mean, ((1 - p) * g_sd)^2)
    baseline         final ~ N(prior_sd * Phi^-1(market price at poll close), prior_sd^2), or
                     final ~ N(our margin model's margin, MODEL_MARGIN_SD^2)
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
import county_project  # noqa: E402  - v1, same folder

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
# Our margin model's error as a standard deviation: held-out 2018-24 margin MAE 4.85 (model repo HANDOFF,
# 2026-10-29) x 1.25 (sd / MAE for a normal error). Its published win chance comes from a separate model and
# can disagree (GA-Gov: +1.2 margin, 78% win); the projector forecasts margins, so it starts from the margin.
MODEL_MARGIN_SD = 6.1


def prior_for(fc, race_key):
    """Model baseline for the non-Republican: (name, win prob, margin in points of all votes)."""
    st, off = race_key.split("-")
    r = fc.get(FC_ID.get(race_key, f"2026_{st}_{OFFICE[off]}"))
    if not r:
        return None
    opp = max((c for c in r["cands"] if c["party"] != "REP"), key=lambda c: c["win"])
    return opp["name"], opp["win"], opp.get("margin")


def latest_nyt(date, race_key):
    """Statewide count from the latest capture, plus every county's (for v1): dict(pct, margin, total,
    stamp, units={county key: dict(d, r, total, expected)})."""
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
    stamp = os.path.basename(files[-1])[:16]
    if not total or not reps or not opps:
        return dict(pct=0.0, margin=0.0, total=total, stamp=stamp, units={})
    rep, opp = max(reps, key=votes.get), max(opps, key=votes.get)
    units = {}
    rus = [u for u in r.get("reporting_units") or [] if u.get("level") != "state"]
    # Maine (and other town-reporting states) lists only towns, each carrying its county's code: add them up
    # into counties, which is what the benchmarks use. Where counties are listed, use just those.
    if any(u.get("level") == "county" for u in rus):
        rus = [u for u in rus if u.get("level") == "county"]
    for u in rus:
        key = (u.get("fips_state") or "") + (u.get("fips_county") or "") or str(u.get("name"))
        v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in u.get("candidates") or []}
        agg = units.setdefault(key, dict(d=0, r=0, total=0, expected=0, name=u.get("name")))
        if u.get("level") != "county":
            agg["name"] = None                 # a county of towns: the benchmark has its name
        agg["d"] += v.get(opp, 0)
        agg["r"] += v.get(rep, 0)
        agg["total"] += u.get("total_votes") or 0
        agg["expected"] += u.get("total_expected_vote") or 0
    return dict(pct=float(top.get("eevp") or 0), total=total, mtime=os.path.getmtime(files[-1]),
                margin=100 * (votes[opp] - votes[rep]) / total, stamp=stamp, units=units)


_bench = None


def bench_record(race_key):
    """The race's entry in State election results/data/processed/county_benchmarks.json, or None."""
    global _bench
    if _bench is None:
        p = os.path.join(RESULTS, "data", "processed", "county_benchmarks.json")
        _bench = {r["id"]: r for r in json.load(open(p, encoding="utf-8"))["races"]} if os.path.exists(p) else {}
    st, off = race_key.split("-")
    return _bench.get(FC_ID.get(race_key, f"2026_{st}_{OFFICE[off]}"))


def benchmarks(race_key):
    """(L {county: lean at a tied statewide result}, w {county: turnout share}), or None."""
    r = bench_record(race_key)
    if not r:
        return None
    L = {c["f"]: c["L"] for c in r["counties"] if c.get("L") is not None}
    w = {c["f"]: c["w"] for c in r["counties"] if c.get("w")}
    s = sum(w.values())
    return L, {k: v / s for k, v in w.items()}


def v1(nyt, race_key, p0=None, m0=None):
    """Projector v1 (county_project.py) when the live counties line up with the benchmarks. Starts from
    p0 (a win probability: the markets) or m0 (margin, sd: our margin model)."""
    b = benchmarks(race_key)
    if not b or not nyt.get("units") or nyt["pct"] <= 0:
        return None
    L, w = b
    if sum(1 for k in nyt["units"] if k in L) < 0.9 * len(nyt["units"]):
        return None                        # different units (Alaska's districts, Maine's towns)
    return county_project.project(nyt["units"], L, w, p0=p0, m0=m0)


def tracking(nyt, race_key, v1res, m0, p_close):
    """Are the votes coming in over or under what we expected? -> dict, or None where v1 doesn't run.
    implied: the final margin the counted votes alone point to (v1's count-only shift on the county leans,
    no starting point), with its sd. expected: our margin model. market: the margin the poll-close price
    implies (6-point spread). Per county: the counted two-party share against the share expected there if
    the state lands on our model's margin, and the share a tied statewide result needs. net: votes the
    non-Republican is ahead (+) or behind (-) of that expectation, as net margin.
    Every benchmark county is listed from before the count (its share of the state's vote, the share
    expected there, the share a tie needs); counted votes fill in as NYT reports them. None when the live
    units don't line up with the benchmarks (Alaska's districts once results come in)."""
    b = benchmarks(race_key)
    if not b:
        return None
    units = nyt.get("units") or {}
    L, w = b
    if units and sum(1 for k in units if k in L) < 0.9 * len(units):
        return None
    rec = bench_record(race_key) or {}
    bc = {c["f"]: c for c in rec.get("counties", [])}
    ts = (v1res or {}).get("two_share") or 0.97
    cp = county_project
    implied = sd = None
    if v1res and v1res["n_counties"]:
        s, se = v1res["count_shift"], v1res["count_shift_se"]
        implied = cp.shift_margin(L, w, s, ts)
        sd = (cp.shift_margin(L, w, s + se, ts) - cp.shift_margin(L, w, s - se, ts)) / 2
    s_mod = cp.margin_shift(L, w, m0[0] / ts, 1.0)[0] if m0 else None
    counties, net_all = [], 0.0
    zero = dict(d=0, r=0, total=0, expected=0)
    for f in L:
        u = units.get(f, zero)
        two = u["d"] + u["r"]
        tie = float(cp.expit(L[f]))
        exp_ = float(cp.expit(L[f] + s_mod)) if s_mod is not None else None
        share = u["d"] / two if two >= 50 else None
        net = (u["d"] - u["r"]) - (2 * exp_ - 1) * two if share is not None and exp_ is not None else None
        net_all += net or 0
        # NYT's expected vote once it reports; before that the county's benchmark turnout
        expected = max(u["expected"] or bc.get(f, {}).get("v") or 0, u["total"])
        counties.append(dict(n=bc.get(f, {}).get("n") or u.get("name") or f, f=f,
                             w=round(w.get(f, 0), 4),
                             pct=round(100 * u["total"] / expected, 1) if expected else 0.0,
                             share=round(share, 4) if share is not None else None,
                             exp=round(exp_, 4) if exp_ is not None else None, tie=round(tie, 4),
                             net=round(net) if net is not None else None,
                             left=round(max(expected - u["total"], 0)), votes=u["total"]))
    return dict(implied=implied, implied_sd=sd, expected=m0[0] if m0 else None,
                market=PRIOR_SD * phi_inv(p_close) if p_close is not None else None,
                net=round(net_all), unit=rec.get("unit") or "county", counties=counties)


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
    # capture_markets.py starts a new folder each Eastern day: read election day and every day after it,
    # or prices would freeze at midnight ET (the overnight count is where 2024's misreads were)
    days = sorted(d for d in os.listdir(MARKETS) if d[:2] == "20" and d >= date) if os.path.isdir(MARKETS) else []
    for venue in ("kalshi", "polymarket"):
        paths = [os.path.join(MARKETS, d, f"{venue}.csv") for d in days]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            continue
        df = pd.concat([pd.read_csv(p, usecols=["ts_utc", "race", "market", "outcome", "bid", "ask"])
                        for p in paths], ignore_index=True)
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
         "ME-Sen", "IA-Sen", "NE-Sen", "NV-Gov", "AK-Sen"]     # poll-closing order
# OR-Gov dropped from live tracking 2026-10-30 (user call); capture_markets.py still records its prices


def _with_baseline(hist, state, nyt, p0, prior_sd, m0=None):
    """v0 from a baseline: P(non-Republican) p0 (the markets) or m0 = (margin, sd) (our margin model), or None."""
    if m0 is not None:
        mu0, prior_sd = m0
    elif p0 is not None:
        mu0 = prior_sd * phi_inv(p0)
    else:
        return None
    if nyt["pct"] <= 0:
        return dict(mu=mu0, sd=prior_sd, p_win=phi(mu0 / prior_sd), steady=None)
    return project(hist, state, nyt["pct"], nyt["margin"], mu0, prior_sd)


def market_now(books):
    """The markets' P(non-Republican) now: mid D / (D + R), averaged over venues; None without quotes."""
    ps = []
    for side in (books or {}).values():
        mid = {k: (s["bid"] + s["ask"]) / 2 for k, s in side.items()
               if s["bid"] == s["bid"] and s["ask"] == s["ask"]}
        if "D" in mid and "R" in mid and mid["D"] + mid["R"] > 0:
            ps.append(mid["D"] / (mid["D"] + mid["R"]))
        elif "D" in mid:
            ps.append(mid["D"])
    return float(np.mean(ps)) if ps else None


def _r(x, n=4):
    return round(float(x), n) if x is not None and x == x else None


def run_live(a, hist, fc):
    mk = load_markets(a.date)
    now = getattr(a, "now", None) or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, cards = [], []
    print(f"\n{now}  margins: non-Republican minus Republican; P = P(non-Republican wins)")
    print(f"Starting point: the markets' price at poll close ({'used' if a.baseline == 'market' else 'shown'}) "
          f"or our model. v1 = county by county (used where the counties line up); v0 = statewide.")
    print(f"{'race':7} {'counted':>7} {'margin':>6} | {'v1 proj':>7} {'+/-80%':>6} {'P v1':>5} | {'P v0':>5} "
          f"{'P mod':>5} {'close':>5} | {'K bid/ask':>9} {'PM bid/ask':>10} | best buy")
    for race in ([a.race] if a.race else RACES):
        state = ABBR[race.split("-")[0]]
        pr = prior_for(fc, race)
        if a.pct is not None:
            nyt = dict(pct=a.pct, margin=a.margin, stamp="what-if", units={})
        else:
            nyt = latest_nyt(a.date, race) or dict(pct=0.0, margin=0.0, stamp="-", units={})
        c_utc = close_utc(a.date, state)
        p_close = market_baseline(mk, race, c_utc)
        m0 = (pr[2], MODEL_MARGIN_SD) if pr and pr[2] is not None else None
        by_mkt = _with_baseline(hist, state, nyt, p_close, a.prior_sd)
        by_mod = _with_baseline(hist, state, nyt, None, a.prior_sd, m0=m0)
        v1_mkt = v1(nyt, race, p0=p_close) if p_close is not None else None
        v1_mod = v1(nyt, race, m0=m0) if m0 else None
        if a.baseline == "market" and p_close is not None:
            v0res, v1res = by_mkt, v1_mkt
        else:                                  # --baseline model, or no market price at the close
            v0res, v1res = by_mod or by_mkt, v1_mod or v1_mkt
        mod = v1_mod or by_mod                 # the 'P mod' column: from our margin model, v1 where it runs
        res = v1res or v0res
        books = latest_books(mk, race)
        bt = best_trade(res["p_win"], books) if res else None
        p_now = market_now(books)
        track = tracking(nyt, race, v1res, m0, p_close) if a.pct is None else None

        def ba(v):
            s = books.get(v, {}).get("D")
            return f"{s['bid']:.2f}/{s['ask']:.2f}" if s and s["ask"] == s["ask"] else "-"

        def f2(x):
            return f"{x:5.2f}" if x is not None else "    -"
        # FLIP: v1 gives the side it would buy 45%+ although the market prices it far lower, with 20%+ counted
        # - the only kind of v1 edge that paid in 2024 (Slotkin at 15c, Rosen at 33c). Edges on longshots v1
        # merely rates higher than the market (5c -> 20c) lost, and so did a flip at 6% counted (Georgia
        # President); every backtest is weakest under 20% counted (MARKET_CHECK.md).
        flip = bool(v1res and bt and (bt[3] + bt[2]) >= 0.45 and nyt["pct"] >= 20)
        trade = (f"{bt[1]} on {bt[0]} @{bt[2]:.2f}: {bt[3] * 100:+.1f}c ({'v1' if v1res else 'v0'})"
                 f"{'  FLIP' if flip else ''}" if bt else "-")
        # '?' (v0 only): past years' late votes leaned opposite ways at this point in the count, so
        # the direction is a guess (backtest: GA, OR, NV, AK, SC did worse than the visible margin)
        flag = "?" if not v1res and v0res and v0res["steady"] is False else " "
        p1 = f"{v1res['mu']:+7.1f} {1.2816 * v1res['sd']:6.1f} {v1res['p_win']:5.2f}" if v1res else \
            f"{'-':>7} {'-':>6} {'-':>5}"
        print(f"{race:7} {nyt['pct']:6.1f}% {nyt['margin']:+6.1f} |{flag}{p1} | "
              f"{f2(v0res and v0res['p_win'])} {f2(mod and mod['p_win'])} "
              f"{f2(p_close)} | {ba('kalshi'):>9} {ba('polymarket'):>10} | {trade}")

        def side(v, k):
            s = books.get(v, {}).get("D")
            return _r(s[k]) if s else None
        rows.append(dict(ts_utc=now, date=a.date, race=race, nyt_file=nyt["stamp"], pct=round(nyt["pct"], 2),
                         margin=round(nyt["margin"], 2), baseline=a.baseline,
                         v1_proj=round(v1res["mu"], 2) if v1res else "",
                         v1_sd=round(v1res["sd"], 2) if v1res else "",
                         p_v1=round(v1res["p_win"], 4) if v1res else "",
                         v0_proj=round(v0res["mu"], 2) if v0res else "",
                         v0_sd=round(v0res["sd"], 2) if v0res else "",
                         p_mkt=round(by_mkt["p_win"], 4) if by_mkt else "",
                         p_model=round(mod["p_win"], 4) if mod else "",
                         model_proj=round(mod["mu"], 2) if mod else "",
                         p_close=round(p_close, 4) if p_close is not None else "",
                         p_now=round(p_now, 4) if p_now is not None else "",
                         implied=round(track["implied"], 2) if track and track["implied"] is not None else "",
                         implied_sd=round(track["implied_sd"], 2) if track and track["implied_sd"] is not None
                         else "",
                         net_vs_model=track["net"] if track else "",
                         model_win=pr[1] if pr else "", model_margin=pr[2] if pr else "",
                         steady="" if not v0res or v0res["steady"] is None else int(v0res["steady"]),
                         best_from="v1" if v1res else "v0", flip=int(flip),
                         best_venue=bt[0] if bt else "", best_side=bt[1] if bt else "",
                         best_ask=bt[2] if bt else "", edge=round(bt[3], 4) if bt else "",
                         k_bid=side("kalshi", "bid") or "", k_ask=side("kalshi", "ask") or "",
                         pm_bid=side("polymarket", "bid") or "", pm_ask=side("polymarket", "ask") or ""))
        b = bench_record(race) or {}
        rep = next((c for c in (fc.get(FC_ID.get(race, f"2026_{race.split('-')[0]}_{OFFICE[race.split('-')[1]]}"))
                                or {}).get("cands", []) if c["party"] == "REP"), None)
        cards.append(dict(
            race=race, state=b.get("state") or state.replace("-", " ").title(), office=OFFICE[race.split("-")[1]],
            d_name=pr[0] if pr else (b.get("d") or {}).get("name"), r_name=rep["name"] if rep else
            (b.get("r") or {}).get("name"), close_utc=c_utc, nyt_file=nyt["stamp"],
            nyt_utc=dt.datetime.fromtimestamp(nyt["mtime"], dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if nyt.get("mtime") else None,
            pct=round(nyt["pct"], 1), margin=round(nyt["margin"], 2), votes=nyt.get("total"),
            v1=dict(proj=_r(v1res["mu"], 2), sd=_r(v1res["sd"], 2), p=_r(v1res["p_win"])) if v1res else None,
            v0=dict(proj=_r(v0res["mu"], 2), sd=_r(v0res["sd"], 2), p=_r(v0res["p_win"]),
                    steady=v0res["steady"]) if v0res else None,
            p_model=_r(mod["p_win"]) if mod else None, model_proj=_r(mod["mu"], 2) if mod else None,
            model_win=pr[1] if pr else None, model_margin=pr[2] if pr else None,
            p_close=_r(p_close), p_now=_r(p_now),
            books={v: dict(bid=side(v, "bid"), ask=side(v, "ask")) for v in ("kalshi", "polymarket") if v in books},
            best=dict(venue=bt[0], side=bt[1], ask=_r(bt[2]), edge=_r(bt[3]), src="v1" if v1res else "v0",
                      flip=flip) if bt else None,
            track=track))
    if a.pct is None:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        if os.path.exists(OUT):               # columns changed: keep the old log aside
            with open(OUT, encoding="utf-8") as f:
                if f.readline().strip().split(",") != list(rows[0]):
                    f.close()
                    os.replace(OUT, OUT.replace(".csv", "_old.csv"))
        new = not os.path.exists(OUT)
        with open(OUT, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        if not a.race:
            write_dashboard(a, now, cards, mk)


HIST_COLS = ["ts_utc", "pct", "margin", "v1_proj", "v1_sd", "p_v1", "v0_proj", "p_mkt", "p_model", "model_proj",
             "p_now", "implied", "implied_sd"]


def write_dashboard(a, now, cards, mk):
    """data/raw/dashboard/live_data.js for dashboard.html: this pass's races (with county tracking), each
    race's history tonight from projections.csv, Senate/House control prices and feed times. Written to a
    temporary file and swapped in, so the page never reads half a file."""
    hist = pd.read_csv(OUT)
    hist = hist[hist.date.astype(str) == a.date]
    for c in cards:
        h = hist[hist.race == c["race"]][HIST_COLS]
        if len(h) > 400:                       # keep the page light: thin to ~400 points, always the latest
            h = pd.concat([h.iloc[:: max(len(h) // 400, 1)], h.iloc[[-1]]]).drop_duplicates("ts_utc")
        c["history"] = [{k: (None if v != v else v) for k, v in r.items()} for r in h.to_dict("records")]
    control = {}
    for key in ("US-Senate", "US-House"):
        books = latest_books(mk, key)
        control[key] = dict(p=_r(market_now(books)),
                            books={v: dict(bid=_r(s["D"]["bid"]), ask=_r(s["D"]["ask"]))
                                   for v, s in books.items() if "D" in s})
    m_ts = [g.ts_utc.max() for r in mk.values() for g in r.values()]
    n_ts = [c["nyt_utc"] for c in cards if c.get("nyt_utc")]
    data = dict(generated=now, date=a.date, baseline=a.baseline, model_margin_sd=MODEL_MARGIN_SD,
                dry_run=getattr(a, "dry_run", None),
                markets_utc=max(m_ts) if m_ts else None, nyt_utc=max(n_ts) if n_ts else None,
                control=control, races=cards)
    d = os.path.join(ROOT, "data", "raw", "dashboard")
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, "live_data.js.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.LIVE = " + json.dumps(data, separators=(",", ":"), default=_json_default) + ";\n")
    os.replace(tmp, os.path.join(d, "live_data.js"))


def _json_default(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if x != x else float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    raise TypeError(type(x))


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
        if not a.watch:
            run_live(a, hist, fc)
            break
        try:                       # a half-written capture (the recorders write while we read) must not end the night
            run_live(a, hist, fc)
        except Exception as e:     # noqa: BLE001
            print(f"\n{dt.datetime.now(dt.timezone.utc):%H:%M:%SZ} pass failed, retrying next pass: "
                  f"{type(e).__name__}: {e}")
        sys.stdout.flush()
        time.sleep(a.watch)
        try:
            fc = load_forecast()
        except Exception:          # noqa: BLE001  - keep the last forecast if the file is mid-refresh
            pass


if __name__ == "__main__":
    main()
