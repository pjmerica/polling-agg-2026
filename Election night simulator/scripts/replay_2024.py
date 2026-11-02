"""Replay election night 2024 through the projector, with real data at every step (2026-11-02).

A test run for the election-night pages that shows what a real night looks like, buy signals included.
Unlike dry_run.py (2024 presidential counts under 2026 race names, one frozen price capture), every number
here is from the 2024 race it shows:

- the count: NYT's statewide timeline for the race (State election results' state_timeseries.csv, 100-650
  updates per race). Share counted is the share of the FINAL count, a little better than the NYT estimate a
  live viewer had;
- counties: the Internet Archive's whole NYT captures (fetch_wayback_full.py). Only 2-12 survive per race,
  so the county projector (v1) runs only while the latest capture's votes counted are within 3% of the final
  vote of the timeline's (votes, not share counted: NYT's share was against its own estimate of the total); otherwise the statewide projector (v0) runs, as live when the counties don't line up. The
  county table shows the latest capture, with its time. Nothing is interpolated;
- county leans from other years only (2020 President, 2022 Senate and Governor; county_replay.leans_other_years),
  and v0's history leaves 2024 out, so the projector never sees the answer;
- prices: Kalshi's minute bid/ask and Polymarket's minute price +/- at least 1c (market_check.py), for the
  race's non-Republican contract. The starting point is their price at poll close, as live. A venue whose
  contract settled against the count's winner is left out (Polymarket paid King's 2024 Maine win as "No",
  so Maine shows its presidential race);
- buy signals: live_project.best_trade and is_flip, today's fee schedules.

No archived 2024 forecast exists, so there is no "our model" line: over/under is against the margin the
poll-close price implies. Each race carries its real result, hidden on the page until you ask for it.

Writes data/raw/replay/live_data.js (never the live data file; publish_live.py refuses it anyway). Open
data_dashboard.html#replay while it runs.

    py "Election night simulator/scripts/replay_2024.py"                         # ~360 steps, 2 s apart
    py "Election night simulator/scripts/replay_2024.py" --pause 0.5             # faster
    py "Election night simulator/scripts/replay_2024.py" --until 2024-11-06T06:15 --pause 0   # jump to 1:15 am ET
    py "Election night simulator/scripts/replay_2024.py" --publish     # the whole night -> docs/ (GitHub Pages,
                                                                       # election-night-replay.html, time slider)
"""
import argparse
import datetime as dt
import glob
import gzip
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_project as lp  # noqa: E402  (also puts State election results/scripts on the path)
import county_project as cp  # noqa: E402
import county_replay as cr  # noqa: E402
import market_check as mc  # noqa: E402
import swing_analysis as sa  # noqa: E402
import volatility as vol  # noqa: E402

DATE = "2024-11-05"
OUT_DIR = os.path.join(lp.ROOT, "data", "raw", "replay")
FEES = {"kalshi": lp.kalshi_spec(1), "polymarket": lp.polymarket_spec(0.04)}
MATCH_PTS = 3.0          # county capture vs timeline, points of the final vote, for v1 to run
# (card key, state slug, NYT office file, market_history folder, office label) in poll-closing order. The Senate
# race where the state had one, else President; the 12 states with NYT timelines.
RACES = [("GA-Pres", "georgia", "president", "GA-President", "President"),
         ("SC-Pres", "south-carolina", "president", "SC-President", "President"),
         ("OH-Sen", "ohio", "us-senate", "OH-Senate", "Senate"),
         ("MI-Sen", "michigan", "us-senate", "MI-Senate", "Senate"),
         ("TX-Sen", "texas", "us-senate", "TX-Senate", "Senate"),
         ("KS-Pres", "kansas", "president", "KS-President", "President"),
         ("ME-Pres", "maine", "president", "ME-President", "President"),
         ("IA-Pres", "iowa", "president", "IA-President", "President"),
         ("NE-Sen", "nebraska", "us-senate", "NE-Senate", "Senate"),
         ("NV-Sen", "nevada", "us-senate", "NV-Senate", "Senate"),
         ("OR-Pres", "oregon", "president", "OR-President", "President"),
         ("AK-Pres", "alaska", "president", "AK-President", "President")]


def _iso(t):
    return pd.Timestamp(t).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def names(slug, office):
    """{nyt_id: 'First Last'} from NYT's final file."""
    p = os.path.join(cr.RES, "nyt_all", "2024", f"{slug}-{office}.json")
    r = json.load(open(p, encoding="utf-8"))["races"][0]
    return {k: f"{m.get('first_name') or ''} {m.get('last_name') or ''}".strip()
            for k, m in r["candidate_metadata"].items()}


def county_captures(slug, office, opp, rep):
    """[(time, {fips: dict(d, r, total, expected, name)})] from the archive's whole captures, in time order."""
    out = []
    for p in sorted(glob.glob(os.path.join(cr.FULL, "2024", slug, "*.json.gz"))):
        try:
            d = json.load(gzip.open(p))
        except (OSError, ValueError):
            continue
        for r in d.get("races") or []:
            if cr.OFFICE_FILE.get(str(r.get("office"))) != office or r.get("race_type_id") not in (None, "G"):
                continue
            units = {}
            for u in r.get("reporting_units") or []:
                if u.get("level") != "county":
                    continue
                v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in u.get("candidates") or []}
                f = (u.get("fips_state") or "") + (u.get("fips_county") or "")
                units[f] = dict(d=v.get(opp, 0), r=v.get(rep, 0), total=u.get("total_votes") or sum(v.values()),
                                expected=u.get("total_expected_vote") or 0, name=u.get("name"))
            if units:
                out.append((pd.Timestamp(os.path.basename(p)[:14], tz="UTC"), units))
            break
    return out


def counted_pct(units):
    T = sum(u["total"] for u in units.values())
    E = sum(max(u["expected"], u["total"]) for u in units.values())
    return 100 * T / E if E else 0.0


def prepare():
    tl_all = pd.read_csv(lp.HISTORY)
    tl_all = tl_all[tl_all.year == 2024]
    tl_all["t"] = pd.to_datetime(tl_all.ts_utc, utc=True, format="ISO8601")
    settled = mc.contract_results()
    races = []
    for key, slug, office, mh, label in RACES:
        fr = cr.final_race(2024, slug, office)
        if not fr:
            print(f"{key}: no final NYT file, skipped")
            continue
        opp, rep, final, _, _ = fr
        nm = names(slug, office)
        tl = tl_all[(tl_all.state == slug) & (tl_all.race == office)].sort_values("t")
        frame = mc.minute_frame(mh)
        won = final > 0
        for v, cols in (("kalshi", ["k_bid", "k_ask"]), ("polymarket", ["poly"])):
            if settled.get((mh, v), won) != won:
                frame = frame.drop(columns=[c for c in cols if c in frame])
                print(f"{key}: {v} contract settled against the count's winner - left out")
        st = vol.ABBR[slug]
        close = (dt.datetime(2024, 11, 5, tzinfo=dt.timezone(dt.timedelta(hours=-5)))
                 + dt.timedelta(hours=sa.close_hours(st, dt.date(2024, 11, 5))))
        p_close = mc.mid(mc.quote(frame, close - dt.timedelta(minutes=1)))
        lean = cr.leans_other_years(2024, slug)
        caps = county_captures(slug, office, opp, rep) if lean else []
        races.append(dict(key=key, slug=slug, state=slug.replace("-", " ").title(), office=label,
                          d_name=nm.get(opp, opp), r_name=nm.get(rep, rep), final=final, tl=tl, frame=frame,
                          close=pd.Timestamp(close).tz_convert("UTC"), p_close=p_close, lean=lean, caps=caps,
                          final_votes=int(tl.votes.max()) if len(tl) else 0, history=[], cache={}))
        print(f"{key}: {len(tl)} count updates, {len(caps)} county captures, close price "
              f"{'-' if p_close is None else f'{p_close:.2f}'}")
    return races


def books_at(frame, t):
    out = {}
    for venue, (bid, ask) in mc.quote(frame, t).items():
        spec = FEES[venue]
        out[venue] = {"D": dict(bid=bid, ask=ask, spec=spec), "R": dict(bid=1 - ask, ask=1 - bid, spec=spec)}
    return out


def mid_now(books):
    ps = [(s["D"]["bid"] + s["D"]["ask"]) / 2 for s in books.values()]
    return float(np.mean(ps)) if ps else None


def lag_pts(R, cap, votes):
    """How far the county capture trails the count, in points of the final vote (None without both)."""
    if not cap or not votes or not R["final_votes"]:
        return None
    return 100 * (votes - sum(u["total"] for u in cap.values())) / R["final_votes"]


def track_for(R, cap, cap_t, lag):
    """County table + over/under against the poll-close price's margin, from the latest capture."""
    L, w = R["lean"]
    units = cap or {}
    key = ("track", cap_t)
    if key not in R["cache"]:
        res = cp.project(units, L, w) if units else None
        R["cache"][key] = res
    res = R["cache"][key]
    ts = (res or {}).get("two_share") or 0.97
    implied = sd = None
    if res and res["n_counties"]:
        s, se = res["count_shift"], res["count_shift_se"]
        implied = cp.shift_margin(L, w, s, ts)
        sd = (cp.shift_margin(L, w, s + se, ts) - cp.shift_margin(L, w, s - se, ts)) / 2
    expected = lp.PRIOR_SD * lp.phi_inv(R["p_close"]) if R["p_close"] is not None else None
    s_exp = cp.margin_shift(L, w, expected / ts, 1.0)[0] if expected is not None else None
    counties, net_all = [], 0.0
    for f in L:
        u = units.get(f, dict(d=0, r=0, total=0, expected=0, name=None))
        two = u["d"] + u["r"]
        exp_ = float(cp.expit(L[f] + s_exp)) if s_exp is not None else None
        share = u["d"] / two if two >= 50 else None
        net = (u["d"] - u["r"]) - (2 * exp_ - 1) * two if share is not None and exp_ is not None else None
        net_all += net or 0
        expected_votes = max(u["expected"] or 0, u["total"])
        counties.append(dict(n=u.get("name") or f, f=f, w=round(w.get(f, 0), 4),
                             pct=round(100 * u["total"] / expected_votes, 1) if expected_votes else 0.0,
                             share=round(share, 4) if share is not None else None,
                             exp=round(exp_, 4) if exp_ is not None else None, tie=round(float(cp.expit(L[f])), 4),
                             net=round(net) if net is not None else None,
                             left=round(max(expected_votes - u["total"], 0)), votes=u["total"]))
    return dict(implied=implied, implied_sd=sd, expected=expected, expected_src="market at poll close",
                market=expected, net=round(net_all), unit="county", counties=counties,
                as_of=_iso(cap_t) if cap_t is not None else None,
                lag_pts=round(lag, 1) if lag is not None else None)


def step(R, t, hist, with_history=True):
    tl = R["tl"][R["tl"].t <= t]
    if len(tl):
        row = tl.iloc[-1]
        pct, margin, votes, nyt_t = float(row.pct_of_final), float(row.margin_pts), int(row.votes), row.t
    else:
        pct, margin, votes, nyt_t = 0.0, 0.0, None, None
    books = books_at(R["frame"], t)
    p0 = R["p_close"] if t >= R["close"] else None
    mu0 = lp.PRIOR_SD * lp.phi_inv(p0) if p0 is not None else None
    # v0: statewide, 2024 left out of its history
    if pct <= 0:
        v0 = dict(mu=mu0, sd=lp.PRIOR_SD, p_win=lp.phi(mu0 / lp.PRIOR_SD), steady=None) if mu0 is not None else None
    elif R["slug"] in hist:
        v0 = lp.project(hist, R["slug"], pct, margin, mu0, lp.PRIOR_SD, skip_year=2024)
    else:
        v0 = None
    # v1: county by county, while the latest real capture matches the count
    caps = [(ct, u) for ct, u in R["caps"] if ct <= t]
    cap_t, cap = caps[-1] if caps else (None, None)
    lag = lag_pts(R, cap, votes)
    v1 = None
    if cap and R["lean"] and 5 <= pct < 99.5 and lag is not None and abs(lag) <= MATCH_PTS:
        L, w = R["lean"]
        if sum(1 for k in cap if k in L) >= 0.9 * len(cap):
            k = ("v1", cap_t, p0)
            if k not in R["cache"]:
                R["cache"][k] = cp.project(cap, L, w, p0=p0)
            v1 = R["cache"][k]
    res = v1 or v0
    bt = lp.best_trade(res["p_win"], books) if res and books else None
    flip = lp.is_flip(v1, bt, pct)
    track = track_for(R, cap, cap_t, lag) if R["lean"] else None
    p_now = mid_now(books)
    R["history"].append(dict(ts_utc=_iso(t), pct=round(pct, 2), margin=round(margin, 2),
                             v1_proj=lp._r(v1["mu"], 2) if v1 else None, v1_sd=lp._r(v1["sd"], 2) if v1 else None,
                             p_v1=lp._r(v1["p_win"]) if v1 else None,
                             v0_proj=lp._r(v0["mu"], 2) if v0 else None, p_mkt=lp._r(v0["p_win"]) if v0 else None,
                             p_model=None, model_proj=None, p_now=lp._r(p_now),
                             implied=lp._r(track["implied"], 2) if track and track["implied"] is not None else None,
                             implied_sd=lp._r(track["implied_sd"], 2) if track and track["implied_sd"] is not None
                             else None))
    return dict(race=R["key"], state=R["state"], office=R["office"], d_name=R["d_name"], r_name=R["r_name"],
                close_utc=_iso(R["close"]), nyt_file=_iso(nyt_t) if nyt_t is not None else "-",
                nyt_utc=_iso(nyt_t) if nyt_t is not None else None, pct=round(pct, 1), margin=round(margin, 2),
                votes=votes,
                v1=dict(proj=lp._r(v1["mu"], 2), sd=lp._r(v1["sd"], 2), p=lp._r(v1["p_win"])) if v1 else None,
                v0=dict(proj=lp._r(v0["mu"], 2), sd=lp._r(v0["sd"], 2), p=lp._r(v0["p_win"]),
                        steady=v0["steady"]) if v0 else None,
                p_model=None, model_proj=None, model_win=None, model_margin=None,
                p_close=lp._r(p0), p_now=lp._r(p_now),
                books={v: dict(bid=lp._r(s["D"]["bid"]), ask=lp._r(s["D"]["ask"])) for v, s in books.items()},
                best=dict(venue=bt[0], side=bt[1], ask=lp._r(bt[2]), edge=lp._r(bt[3]), src="v1" if v1 else "v0",
                          flip=flip) if bt else None,
                track=track, history=list(R["history"]) if with_history else None,
                result=dict(margin=round(R["final"], 2),
                            winner=R["d_name"] if R["final"] > 0 else R["r_name"]))


def clock(step_min):
    t = pd.Timestamp("2024-11-05T23:30Z")
    night_end, end = pd.Timestamp("2024-11-06T10:00Z"), pd.Timestamp("2024-11-11T06:00Z")
    out = []
    while t <= end:
        out.append(t)
        t += pd.Timedelta(minutes=step_min if t < night_end else 30)
    return out


def write(now, cards):
    data = dict(generated=_iso(now), date=DATE, baseline="market", model_margin_sd=None, replay=True,
                dry_run="2024 replay: real count, real county captures where they line up, real Kalshi and "
                        "Polymarket minute prices",
                markets_utc=_iso(now), nyt_utc=max((c["nyt_utc"] for c in cards if c["nyt_utc"]), default=None),
                control={}, races=cards)
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = os.path.join(OUT_DIR, "live_data.js.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.LIVE = " + json.dumps(data, separators=(",", ":"), default=lp._json_default) + ";\n")
    os.replace(tmp, os.path.join(OUT_DIR, "live_data.js"))


DOCS = os.path.join(lp.REPO, "docs")
BUNDLE = "election_night_replay_2024.js"
PAGE = "election-night-replay.html"
STATIC = ("race", "state", "office", "d_name", "r_name", "close_utc", "result")


def _compact(x):
    """Drop None values (the page treats a missing key as null) to keep the bundle small."""
    if isinstance(x, dict):
        return {k: _compact(v) for k, v in x.items() if v is not None}
    if isinstance(x, list):
        return [_compact(v) for v in x]
    return x


def publish(races, hist, steps):
    """The whole night in one file for the GitHub Pages copy: docs/election_night_replay_2024.js (every step,
    county tables stored once per capture) and docs/election-night-replay.html (data_dashboard.html, which
    plays the bundle with a time slider when it is present)."""
    out = [dict(**{k: None for k in STATIC}, f=[], tracks={}) for _ in races]
    for i, t in enumerate(steps):
        for o, R in zip(out, races):
            c = step(R, t, hist, with_history=False)
            if i == 0:
                o.update({k: c[k] for k in STATIC})
            tr = c.pop("track")
            for k in STATIC + ("history", "p_model", "model_proj", "model_win", "model_margin", "nyt_file"):
                c.pop(k, None)
            if tr:
                ck = tr.get("as_of") or "none"
                if ck not in o["tracks"]:
                    o["tracks"][ck] = tr["counties"]
                c["track"] = {k: v for k, v in tr.items() if k != "counties"} | {"ck": ck}
            o["f"].append(c)
        if i % 50 == 0:
            print(f"  {i}/{len(steps)}")
    data = dict(label="2024 replay: real count, real county captures where they line up, real Kalshi and "
                      "Polymarket minute prices", date=DATE, steps=[_iso(t) for t in steps], races=out)
    with open(os.path.join(DOCS, BUNDLE), "w", encoding="utf-8") as f:
        f.write("window.REPLAY_BUNDLE = " + json.dumps(_compact(data), separators=(",", ":"),
                                                     default=lp._json_default) + ";\n")
    page = open(os.path.join(lp.ROOT, "data_dashboard.html"), encoding="utf-8").read().replace("\r\n", "\n")
    marker = '<script>\n"use strict";'
    assert page.count(marker) == 1
    page = page.replace(marker, f'<script src="{BUNDLE}"></script>\n' + marker)
    page = page.replace("<title>Election Night Data Desk</title>", "<title>Election Night 2024 Replay</title>")
    with open(os.path.join(DOCS, PAGE), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    kb = os.path.getsize(os.path.join(DOCS, BUNDLE)) / 1024
    print(f"wrote docs/{PAGE} and docs/{BUNDLE} ({kb:,.0f} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between steps")
    ap.add_argument("--step", type=float, default=5.0, help="replay minutes per step until 5 am ET (then 30)")
    ap.add_argument("--until", help="stop at this UTC time, e.g. 2024-11-06T06:15 (1:15 am ET)")
    ap.add_argument("--publish", action="store_true",
                    help="write the whole night to docs/ for GitHub Pages (election-night-replay.html), no stepping")
    a = ap.parse_args()
    races = prepare()
    hist = lp.load_history()
    steps = clock(a.step)
    if a.publish:
        publish(races, hist, steps)
        return
    if a.until:
        stop = pd.Timestamp(a.until, tz="UTC") if pd.Timestamp(a.until).tzinfo is None else pd.Timestamp(a.until)
        steps = [t for t in steps if t <= stop]
    print(f"{len(steps)} steps; open data_dashboard.html#replay")
    for t in steps:
        cards = [step(R, t, hist) for R in races]
        write(t, cards)
        sig = [f"{c['race']} {c['best']['side']}@{c['best']['ask']:.2f}{' FLIP' if c['best']['flip'] else ''}"
               for c in cards if c["best"] and c["best"]["edge"] is not None and c["best"]["edge"] >= 0.05]
        et = t.tz_convert("America/New_York").strftime("%a %I:%M %p")
        print(f"{et} ET  " + (" | ".join(sig) if sig else "-"))
        if a.pause:
            time.sleep(a.pause)
    print("done: the page shows the last step")


if __name__ == "__main__":
    main()
