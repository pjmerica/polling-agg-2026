"""Replay projector v1 (county_project.py) through the 2020 count, every state, and score it.

The 2020 Internet Archive captures of NYT's national results file (State election results/data/raw/
wayback_2020, 140 captures over election week) hold every county's votes by candidate, NYT's expected
vote and share counted. At each capture where a state is 5-99% counted, v1 projects the final
presidential margin from the counties alone (no starting point); the score is against the final count.

County leans come from the 2024 presidential result by county, a different year, as on Nov 3, 2026,
when the benchmarks are 2022/2024 results. The comparison is the visible margin and, in the 12 states
with timelines, v0 (live_project.py, 2020 left out of its history).

    py "Election night simulator/scripts/county_replay.py"                  # score with PARAMS
    py "Election night simulator/scripts/county_replay.py" --tune           # try settings

Writes data/processed/county_replay_2020.csv.
"""
import argparse
import ast
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
RES = os.path.join(REPO, "State election results", "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, HERE)
import county_project as cp  # noqa: E402

D_KEYS, R_KEYS = ("bidenj",), ("trumpd",)


def leans_2024():
    """{state slug: (L {fips: logit D two-party share}, w {fips: share of state votes})} from 2024."""
    out = {}
    for p in glob.glob(os.path.join(RES, "nyt_all", "2024", "*-president.json")):
        slug = os.path.basename(p)[:-len("-president.json")]
        r = json.load(open(p, encoding="utf-8"))["races"][0]
        party = {k: str((m.get("party") or {}).get("nyt_id", "")).lower() for k, m in r["candidate_metadata"].items()}
        L, tot = {}, {}
        for u in r.get("reporting_units") or []:
            if u.get("level") != "county":
                continue
            f = (u.get("fips_state") or "") + (u.get("fips_county") or "")
            dv = sum((c.get("votes") or {}).get("total", 0) for c in u["candidates"] if party.get(c["nyt_id"]) == "dem")
            rv = sum((c.get("votes") or {}).get("total", 0) for c in u["candidates"] if party.get(c["nyt_id"]) == "gop")
            if dv + rv > 0:
                L[f] = cp.logit(dv / (dv + rv))
                tot[f] = u.get("total_votes") or (dv + rv)
        s = sum(tot.values())
        if L and s:
            out[slug] = (L, {k: v / s for k, v in tot.items()})
    return out


def captures_2020():
    """[(capture time, {state: {fips: dict(d, r, total, expected)}})] in time order."""
    caps = []
    for p in sorted(glob.glob(os.path.join(RES, "wayback_2020", "*.json"))):
        d = json.load(open(p, encoding="utf8"))
        t = pd.Timestamp(os.path.basename(p)[:14], tz="UTC")
        snap = {}
        for st, s in (d.get("states") or {}).items():
            u = {}
            for c in s.get("counties") or []:
                res = c.get("results")
                res = ast.literal_eval(res) if isinstance(res, str) else (res or {})
                u[str(c.get("fips"))[:5]] = dict(d=sum(res.get(k, 0) for k in D_KEYS),
                                                 r=sum(res.get(k, 0) for k in R_KEYS),
                                                 total=c.get("votes") or 0, expected=c.get("tot_exp_vote") or 0)
            snap[st] = u
        caps.append((t, snap))
    return caps


def final_2020():
    """{state slug: final margin, D minus R, % of all votes} from NYT's 2020 race files."""
    out = {}
    for p in glob.glob(os.path.join(RES, "nyt_all", "2020", "*-president.json")):
        slug = os.path.basename(p)[:-len("-president.json")]
        r = json.load(open(p, encoding="utf-8"))["data"]["races"][0]
        v = {c["candidate_key"]: c["votes"] for c in r["candidates"]}
        tot = sum(v.values())
        if tot and "bidenj" in v and "trumpd" in v:
            out[slug] = 100 * (v["bidenj"] - v["trumpd"]) / tot
    return out


def replay(params=None, p0=False, with_v0=False):
    leans, finals, caps = leans_2024(), final_2020(), captures_2020()
    if with_v0:
        import live_project as lp
        hist = lp.load_history()
    rows = []
    for t, snap in caps:
        for st, units in snap.items():
            if st not in leans or st not in finals:
                continue
            L, w = leans[st]
            if sum(1 for k in units if k in L) < 0.9 * len(units):
                continue                                    # county keys don't line up (New England towns)
            tot = sum(u["total"] for u in units.values())
            exp_ = sum(max(u["expected"], u["total"]) for u in units.values())
            if not exp_ or not 5 <= 100 * tot / exp_ < 99:
                continue
            d = sum(u["d"] for u in units.values())
            r = sum(u["r"] for u in units.values())
            res = cp.project(units, L, w, p0=0.5 if p0 else None, params=params)
            if not res:
                continue
            fin = finals[st]
            vis = 100 * (d - r) / tot
            row = dict(t=t, state=st, counted=res["counted_pct"], visible=vis,
                       proj=res["mu"], sd=res["sd"], p_win=res["p_win"], final=fin)
            if with_v0 and st in hist:
                v0 = lp.project(hist, st, res["counted_pct"], vis, skip_year=2020)
                row.update(v0_proj=v0["mu"], v0_p=v0["p_win"])
            rows.append(row)
    df = pd.DataFrame(rows).drop_duplicates(["state", "counted"])
    df["err"] = df.final - df.proj
    df["err_naive"] = df.final - df.visible
    df["in80"] = (df.err.abs() / df.sd.clip(lower=0.05)) < 1.2816
    df["brier"] = (df.p_win - (df.final > 0)) ** 2
    df["brier_naive"] = ((df.visible > 0).astype(float) - (df.final > 0)) ** 2
    return df


# ---- 2022 / 2024: whole Internet Archive captures (fetch_wayback_full.py), out of sample ----------
FULL = os.path.join(ROOT, "data", "raw", "wayback_full")
OFFICE_FILE = {"U.S. Senate": "us-senate", "Senate": "us-senate", "Governor": "governor",
               "President": "president"}
REP = {"gop", "rep", "republican"}


def _units_new(r):
    """{fips: {candidate id: votes}}, {fips: total}, {fips: expected} from a 2022/2024 race."""
    votes, tot, exp_ = {}, {}, {}
    for u in r.get("reporting_units") or []:
        if u.get("level") != "county":
            continue
        f = (u.get("fips_state") or "") + (u.get("fips_county") or "")
        votes[f] = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in u.get("candidates") or []}
        tot[f] = u.get("total_votes") or sum(votes[f].values())
        exp_[f] = u.get("total_expected_vote") or 0
    return votes, tot, exp_


def final_race(year, slug, office):
    """(opp id, rep id, final margin % of all votes, county two-party logits {fips: L}, county totals)
    from NYT's final file in nyt_all, or None."""
    p = os.path.join(RES, "nyt_all", str(year), f"{slug}-{office}.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    if "data" in d:                                            # 2020 layout
        r = d["data"]["races"][0]
        party = {c["candidate_key"]: c["party_id"].lower() for c in r["candidates"]}
        fin = {c["candidate_key"]: c["votes"] for c in r["candidates"]}
        cvotes = {}
        for c in r.get("counties") or []:
            res = c.get("results")
            cvotes[str(c["fips"])[:5]] = ast.literal_eval(res) if isinstance(res, str) else (res or {})
        ctot = {k: sum(v.values()) for k, v in cvotes.items()}
    else:
        r = d["races"][0]
        party = {k: str((m.get("party") or {}).get("nyt_id", "")).lower() for k, m in r["candidate_metadata"].items()}
        fin = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in r["top_reporting_unit"]["candidates"]}
        cvotes, ctot, _ = _units_new(r)
    reps = [k for k in fin if party.get(k) in REP]
    opps = [k for k in fin if party.get(k) not in REP]
    if not reps or not opps:
        return None
    rep, opp = max(reps, key=fin.get), max(opps, key=fin.get)
    tot = sum(fin.values())
    L = {f: cp.logit(v.get(opp, 0) / (v.get(opp, 0) + v.get(rep, 0)))
         for f, v in cvotes.items() if v.get(opp, 0) + v.get(rep, 0) > 0}
    return opp, rep, 100 * (fin[opp] - fin[rep]) / tot, L, ctot


LEAN_SOURCES = {2022: [(2020, "president"), (2024, "president")],
                2024: [(2020, "president"), (2022, "us-senate"), (2022, "governor")]}


def leans_other_years(year, slug):
    """County leans for a `year` replay from OTHER years' results only (averaged log-odds), weights from
    the most recent source."""
    Ls, w = [], None
    for y, office in LEAN_SOURCES[year]:
        f = final_race(y, slug, office)
        if f:
            Ls.append(f[3])
            if w is None or y > w[0]:
                s = sum(f[4].values())
                w = (y, {k: v / s for k, v in f[4].items()}) if s else w
    if not Ls or not w:
        return None
    keys = set.intersection(*(set(L) for L in Ls))
    return {k: sum(L[k] for L in Ls) / len(Ls) for k in keys}, {k: w[1].get(k, 0) for k in keys}


def snapshots_full(year):
    """[(capture time, state slug, office slug, {fips: dict(d, r, total, expected)})]"""
    import gzip
    out = []
    for p in sorted(glob.glob(os.path.join(FULL, str(year), "*", "*.json.gz"))):
        slug = os.path.basename(os.path.dirname(p))
        t = pd.Timestamp(os.path.basename(p)[:14], tz="UTC")
        try:
            d = json.load(gzip.open(p))
        except (OSError, ValueError):
            continue
        for r in d.get("races") or []:
            office = OFFICE_FILE.get(str(r.get("office")))
            if not office or r.get("race_type_id") not in (None, "G") or not r.get("reporting_units"):
                continue
            votes, tot, exp_ = _units_new(r)
            out.append((t, slug, office, votes, tot, exp_))
    return out


def replay_full(year, params=None):
    import live_project as lp
    hist = lp.load_history()
    rows, finals, leans = [], {}, {}
    for t, slug, office, votes, tot, exp_ in snapshots_full(year):
        key = (slug, office)
        if key not in finals:
            finals[key] = final_race(year, slug, office)
            leans[key] = leans_other_years(year, slug)
        fr, ln = finals[key], leans[key]
        if not fr or not ln:
            continue
        opp, rep, fin, _, _ = fr
        L, w = ln
        units = {f: dict(d=v.get(opp, 0), r=v.get(rep, 0), total=tot[f], expected=exp_[f])
                 for f, v in votes.items()}
        if not units or sum(1 for k in units if k in L) < 0.9 * len(units):
            continue
        T = sum(u["total"] for u in units.values())
        E = sum(max(u["expected"], u["total"]) for u in units.values())
        if not T or not E or not 5 <= 100 * T / E < 99:
            continue
        D = sum(u["d"] for u in units.values())
        R = sum(u["r"] for u in units.values())
        res = cp.project(units, L, w, params=params)
        if not res:
            continue
        vis = 100 * (D - R) / T
        row = dict(year=year, t=t, state=slug, office=office, counted=res["counted_pct"], visible=vis,
                   proj=res["mu"], sd=res["sd"], p_win=res["p_win"], final=fin)
        if slug in hist:
            v0 = lp.project(hist, slug, res["counted_pct"], vis, skip_year=year)
            row.update(v0_proj=v0["mu"], v0_p=v0["p_win"])
        rows.append(row)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.drop_duplicates(["state", "office", "counted"])
    df["err"] = df.final - df.proj
    df["err_naive"] = df.final - df.visible
    df["in80"] = (df.err.abs() / df.sd.clip(lower=0.05)) < 1.2816
    df["brier"] = (df.p_win - (df.final > 0)) ** 2
    df["brier_naive"] = ((df.visible > 0).astype(float) - (df.final > 0)) ** 2
    return df


def market_compare_2024():
    """v1 at every archived 2024 snapshot, started from the market's price at poll close (as the live
    tool does), against what the market was charging then (market_check.py's minute prices)."""
    import datetime as dt
    import market_check as mc
    import swing_analysis as sa
    import volatility as vol
    settled = mc.contract_results()
    rows, finals, leans, frames = [], {}, {}, {}
    for t, slug, office, votes, tot, exp_ in snapshots_full(2024):
        st = vol.ABBR.get(slug)
        race = f"{st}-{ {'us-senate': 'Senate', 'president': 'President', 'governor': 'Governor'}[office]}"
        if not os.path.isdir(os.path.join(mc.HIST, race)):
            continue
        key = (slug, office)
        if key not in finals:
            finals[key] = final_race(2024, slug, office)
            leans[key] = leans_other_years(2024, slug)
            frames[key] = mc.minute_frame(race)
        fr, ln, df = finals[key], leans[key], frames[key]
        if not fr or not ln:
            continue
        opp, rep, fin, _, _ = fr
        won = fin > 0
        if any(settled.get((race, v), won) != won for v in ("kalshi", "polymarket")):
            continue
        L, w = ln
        units = {f: dict(d=v.get(opp, 0), r=v.get(rep, 0), total=tot[f], expected=exp_[f]) for f, v in votes.items()}
        if not units or sum(1 for k in units if k in L) < 0.9 * len(units):
            continue
        T = sum(u["total"] for u in units.values())
        E = sum(max(u["expected"], u["total"]) for u in units.values())
        if not T or not E or not 5 <= 100 * T / E < 99:
            continue
        close = (dt.datetime(2024, 11, 5, tzinfo=dt.timezone(dt.timedelta(hours=-5)))
                 + dt.timedelta(hours=sa.close_hours(st, dt.date(2024, 11, 5))))
        p0 = mc.mid(mc.quote(df, close - dt.timedelta(minutes=1)))
        q = mc.quote(df, t + pd.Timedelta(minutes=2))
        mk = mc.mid(q)
        if p0 is None or mk is None or not 0.03 <= p0 <= 0.97:
            continue
        res = cp.project(units, L, w, p0=p0)
        D = sum(u["d"] for u in units.values())
        R = sum(u["r"] for u in units.values())
        k = q.get("kalshi")
        rows.append(dict(race=race, t_et=t.tz_convert("America/New_York").strftime("%a %H:%M"),
                         counted=round(res["counted_pct"], 1), visible=round(100 * (D - R) / T, 2),
                         v1_proj=round(res["mu"], 2), p_v1=round(res["p_win"], 3), market=round(mk, 3),
                         k_bid=k[0] if k else None, k_ask=k[1] if k else None,
                         final=round(fin, 2), won=int(won)))
    out = pd.DataFrame(rows).drop_duplicates(["race", "counted"]).sort_values(["race", "t_et"])
    return out


def score(df, label=""):
    df = df.copy()
    df["bucket"] = pd.cut(df.counted, [5, 20, 40, 60, 80, 99])
    # each state counts once per bucket
    per = df.groupby(["bucket", "state"], observed=True).agg(
        miss=("err", lambda e: e.abs().mean()), miss_naive=("err_naive", lambda e: e.abs().mean()),
        in80=("in80", "mean"), brier=("brier", "mean"), brier_naive=("brier_naive", "mean")).reset_index()
    t = per.groupby("bucket", observed=True).agg(states=("state", "size"), miss=("miss", "mean"),
                                                 miss_naive=("miss_naive", "mean"), in80=("in80", "mean"),
                                                 brier=("brier", "mean"), brier_naive=("brier_naive", "mean"))
    if label:
        print(label)
    print(t.round(3).to_string())
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--year", type=int, default=2020, help="2020 (national file) or 2022/2024 (whole captures)")
    ap.add_argument("--markets", action="store_true", help="2024: v1 against the market at each snapshot")
    a = ap.parse_args()
    if a.markets:
        m = market_compare_2024()
        os.makedirs(PROC, exist_ok=True)
        m.to_csv(os.path.join(PROC, "county_market_2024.csv"), index=False)
        pd.set_option("display.width", 220)
        print(m.to_string(index=False))
        if len(m):
            per = m.assign(b_v1=(m.p_v1 - m.won) ** 2, b_mk=(m.market - m.won) ** 2).groupby("race")[["b_v1", "b_mk"]].mean()
            print(f"\n{len(m)} snapshots in {m.race.nunique()} races. Brier (races weighted equally): "
                  f"v1 {per.b_v1.mean():.3f}, market {per.b_mk.mean():.3f}")
        return
    if a.year != 2020:
        df = replay_full(a.year)
        os.makedirs(PROC, exist_ok=True)
        df.to_csv(os.path.join(PROC, f"county_replay_{a.year}.csv"), index=False)
        print(f"{a.year}: {df.groupby(['state', 'office']).ngroups if len(df) else 0} races, {len(df)} snapshots, "
              f"states: {sorted(df.state.unique()) if len(df) else []}\n")
        if df.empty:
            return
        df["state"] = df.state + "-" + df.office          # score each race once per bucket
        score(df, f"v1, {a.year}, out of sample (count only):")
        v = df.dropna(subset=["v0_proj"])
        v = v[v.counted.between(20, 90)]
        if len(v):
            print(f"\nSame snapshots, 20-90% counted ({len(v)}): average miss v1 {v.err.abs().mean():.2f}, "
                  f"v0 {(v.final - v.v0_proj).abs().mean():.2f}, visible {v.err_naive.abs().mean():.2f}; Brier v1 "
                  f"{v.brier.mean():.3f}, v0 {((v.v0_p - (v.final > 0)) ** 2).mean():.3f}, visible "
                  f"{v.brier_naive.mean():.3f}")
        m = df[df.counted.between(20, 90)].groupby("state").agg(
            miss=("err", lambda e: e.abs().mean()), naive=("err_naive", lambda e: e.abs().mean()),
            in80=("in80", "mean"), n=("err", "size"))
        print("\nBy race, 20-90% counted:\n", m.round(2).to_string())
        return
    if a.tune:
        for rem in (0.15, 0.3, 0.45, 0.6):
            for inflate in (2.0, 3.0):
                for power in (6,):
                    disc = 0.0
                    df = replay(dict(frac_power=power, early_discount=disc, shift_inflate=inflate, county_sd=0.15,
                                     remaining_sd=rem, sims=1500))
                    m = df[df.counted.between(20, 90)]
                    mi = m[m.state.isin(["michigan", "ohio"])]
                    print(f"remaining_sd {rem} inflate {inflate}: MI+OH miss {mi.err.abs().mean():.2f} | "
                          f"all miss {m.err.abs().mean():.2f} "
                          f"(naive {m.err_naive.abs().mean():.2f}) in80 {m.in80.mean():.2f} "
                          f"brier {m.brier.mean():.3f} (naive {m.brier_naive.mean():.3f})")
        return
    df = replay(with_v0=True)
    os.makedirs(PROC, exist_ok=True)
    df.to_csv(os.path.join(PROC, "county_replay_2020.csv"), index=False)
    print(f"{df.state.nunique()} states, {len(df)} state-snapshots\n")
    score(df, "v1, count only (no starting point):")
    v = df.dropna(subset=["v0_proj"])
    v = v[v.counted.between(20, 90)]
    print(f"\nSame snapshots, 20-90% counted ({len(v)}): average miss v1 {v.err.abs().mean():.2f}, "
          f"v0 {(v.final - v.v0_proj).abs().mean():.2f}, visible {v.err_naive.abs().mean():.2f}; Brier v1 "
          f"{v.brier.mean():.3f}, v0 {((v.v0_p - (v.final > 0)) ** 2).mean():.3f}, visible {v.brier_naive.mean():.3f}")
    worst = df[df.counted.between(20, 90)].groupby("state").err.apply(lambda e: e.abs().mean()).sort_values()
    print("\nAverage miss by state, 20-90% counted (worst 12):\n", worst.tail(12).round(2).to_string())


if __name__ == "__main__":
    main()
