"""An ESTIMATE of how each House district's counties came in on election night 2026.

NYT publishes a House district's counties only as the latest count, and the night's copies weren't recorded (the
recording starts 2026-11-04 14:02 ET; the Internet Archive has none). What does exist for the night:
  - states/  (the release election-night-2026): NYT's state pages about every 10 minutes, with the Senate or Governor
    race on the same ballots by county;
  - each district's own file: its counties now, and the district's real total through the night (`timeseries`, to
    07:59 UTC Nov 4).

So, per district and county (user 2026-11-04: "we have the county votes for senate which is still very good"):
  pace(t)        the county's statewide-race votes at t / its votes at the end; the same ballots, counted together
  votes(t)       the district's votes in the county now x pace(t)
  D share(t)     the county's House share now, moved on log-odds by how far the statewide race's share at t was from its
                 share now (keeps the county's ticket-splitting)
A county split between districts is assumed to count at the same pace in each. States with no Senate or Governor race
use the biggest other race with county results, for pace only (no share).

Checked against the truth: at each point of a district's real timeline, the counties' estimates are added up and compared
with the real votes counted and margin, beside the naive guess that the margin was always the final one. The estimate is
never presented as a recording: every row is an estimate, and the check is written with it.

    py "Election night simulator/scripts/house_county_path.py" --states DIR --districts DIR --out DIR
      DIR: folders holding states/2026-11-03/{state}/*.json.gz and districts/2026-11-03/{XX-NN}/*.json.gz
"""
import argparse
import bisect
import csv
import glob
import gzip
import json
import math
import os
import statistics as st

DATE = "2026-11-03"
CHECK_PCT = (10, 25, 50, 75, 90)


def stamp_of(path):
    return os.path.basename(path)[:16]


def iso_to_stamp(s):
    return s[:19].replace("-", "").replace(":", "") + "Z"


def unit_key(u):
    k = (u.get("fips_state") or "") + (u.get("fips_county") or "")
    if u.get("level") == "township" and u.get("fips_suffix"):
        k += "-" + str(u["fips_suffix"])
    return k


def logit(p):
    p = min(max(p, 0.001), 0.999)
    return math.log(p / (1 - p))


def expit(x):
    return 1 / (1 + math.exp(-x))


def sides(race):
    """(GOP ids, the top non-GOP id) from the race's current totals, or (None, None) without a two-sided contest."""
    meta = race.get("candidate_metadata") or {}
    top = race.get("top_reporting_unit") or {}
    votes = {c["nyt_id"]: (c.get("votes") or {}).get("total") or 0 for c in top.get("candidates") or []}
    gop = [k for k in votes if ((meta.get(k) or {}).get("party") or {}).get("nyt_id") == "GOP"]
    opp = [k for k in votes if k not in gop]
    if not gop or not opp:
        return None, None
    return set(gop), max(opp, key=votes.get)


def units_of(race):
    out = {}
    gop, opp = sides(race)
    for u in race.get("reporting_units") or []:
        if u.get("level") not in ("county", "township"):
            continue
        v = {c["nyt_id"]: (c.get("votes") or {}).get("total") or 0 for c in u.get("candidates") or []}
        rec = dict(t=u.get("total_votes") or sum(v.values()), name=u.get("name"))
        if gop:
            rec.update(d=v.get(opp, 0), r=sum(n for k, n in v.items() if k in gop))
        out[unit_key(u)] = rec
    return out


def pick_proxy(races):
    """The state page's race to borrow from: Senate, else Governor, else the biggest with county results (pace only)."""
    with_units = [r for r in races if any(u.get("level") in ("county", "township") for u in r.get("reporting_units") or [])]
    for office in ("U.S. Senate", "Governor"):
        rs = [r for r in with_units if r.get("office") == office and sides(r)[0]]
        if rs:
            rs.sort(key=lambda r: "-G-" not in str(r.get("nyt_id")))
            return rs[0]["nyt_id"], office, True
    if with_units:
        r = max(with_units, key=lambda r: (r.get("top_reporting_unit") or {}).get("total_votes") or 0)
        return r["nyt_id"], r.get("office") or "other", False
    return None, None, False


def load_proxy(folder):
    """{unit key: ([stamps], [recs])} for one state, with what it borrowed from; None when no page has counties."""
    files = sorted(glob.glob(os.path.join(folder, "*.json.gz")))
    if not files:
        return None
    with gzip.open(files[-1]) as f:
        nyt_id, office, has_share = pick_proxy(json.load(f).get("races") or [])
    if not nyt_id:
        return None
    path = {}
    for p in files:
        try:
            with gzip.open(p) as f:
                race = next((r for r in json.load(f).get("races") or [] if r.get("nyt_id") == nyt_id), None)
        except (OSError, ValueError):
            continue
        if not race:
            continue
        stamp = stamp_of(p)
        for k, rec in units_of(race).items():
            s, rs = path.setdefault(k, ([], []))
            s.append(stamp)
            rs.append(rec)
    return dict(office=office, share=has_share, path=path)


def at(series, stamp):
    """The last record at or before stamp, or None."""
    s, rs = series
    i = bisect.bisect_right(s, stamp) - 1
    return rs[i] if i >= 0 else None


def estimate(house, proxy, stamp, fin_stamp):
    """{unit: dict(t, d, r, pace)} at stamp for one district; a unit outside the statewide race is left out."""
    out = {}
    for k, h in house.items():
        series = proxy["path"].get(k)
        if not series:
            continue
        now, fin = at(series, stamp), at(series, fin_stamp)
        if not fin or not fin["t"]:
            continue
        pace = min(1.0, (now["t"] / fin["t"]) if now else 0.0)
        e = dict(t=h["t"] * pace, pace=pace, d=None, r=None)
        two_h = (h.get("d") or 0) + (h.get("r") or 0)
        if proxy["share"] and two_h and now and (now.get("d", 0) + now.get("r", 0)) > 0 and (fin.get("d", 0) + fin.get("r", 0)) > 0:
            s_now, s_fin = now["d"] / (now["d"] + now["r"]), fin["d"] / (fin["d"] + fin["r"])
            s = expit(logit(h["d"] / two_h) + logit(s_now) - logit(s_fin))
            e["d"], e["r"] = two_h * pace * s, two_h * pace * (1 - s)
        elif two_h:                       # pace only: the county's final split
            e["d"], e["r"] = h["d"] * pace, h["r"] * pace
        out[k] = e
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", required=True)
    ap.add_argument("--districts", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    proxies = {}
    rows = 0
    checks, skipped, per_race = [], {}, []
    csv_path = os.path.join(a.out, "house_county_path_ESTIMATE.csv.gz")
    with gzip.open(csv_path, "wt", newline="", encoding="utf-8") as g:
        w = csv.writer(g)
        w.writerow(["race", "unit", "county", "ts_utc", "est_votes", "est_d", "est_r", "pace", "borrowed_from"])
        for folder in sorted(glob.glob(os.path.join(a.districts, "districts", DATE, "*"))):
            key = os.path.basename(folder)
            files = sorted(glob.glob(os.path.join(folder, "*.json.gz")))
            if not files:
                continue
            with gzip.open(files[-1]) as f:
                d = json.load(f)
            race = (d.get("races") or [None])[0]
            if not race:
                skipped[key] = "no race"
                continue
            state_slug = str(race.get("url") or "").split("results-")[-1].split("-us-house")[0]
            if state_slug not in proxies:
                proxies[state_slug] = load_proxy(os.path.join(a.states, "states", DATE, state_slug))
            proxy = proxies[state_slug]
            house = units_of(race)
            if not proxy or not house:
                skipped[key] = "no statewide county path" if not proxy else "no county units"
                continue
            fin_stamp = stamp_of(files[-1])
            cover = sum(h["t"] for k, h in house.items() if k in proxy["path"])
            total = sum(h["t"] for h in house.values())
            if not total or cover < 0.9 * total:
                skipped[key] = f"counties don't line up ({cover}/{total})"
                continue
            stamps = sorted({s for k in house if k in proxy["path"] for s in proxy["path"][k][0] if s <= fin_stamp})
            for s in stamps:
                for k, e in estimate(house, proxy, s, fin_stamp).items():
                    if e["t"] <= 0 and e["pace"] <= 0:
                        continue
                    ts = f"{s[:4]}-{s[4:6]}-{s[6:8]}T{s[9:11]}:{s[11:13]}:{s[13:15]}Z"
                    w.writerow([key, k, house[k]["name"], ts, round(e["t"]), None if e["d"] is None else round(e["d"]),
                                None if e["r"] is None else round(e["r"]), round(e["pace"], 4), proxy["office"]])
                    rows += 1
            # the check: the district's real path
            gop, opp = sides(race)
            series = next(iter((d.get("timeseries") or {}).values()), [])
            fin_vote = (race.get("top_reporting_unit") or {}).get("total_votes") or 0
            real = []
            for x in series:
                v = {c["nyt_id"]: (c.get("votes") or {}).get("total") or 0 for c in x.get("candidates") or []}
                tv = x.get("total_votes") or sum(v.values())
                real.append((iso_to_stamp(x.get("greatest_updated_at") or ""), tv, v.get(opp, 0) if gop else None,
                             sum(n for k, n in v.items() if gop and k in gop) if gop else None))
            if not real or not fin_vote or not gop:
                per_race.append(dict(race=key, office=proxy["office"], cover=round(cover / total, 3), checked=0))
                continue
            top_v = {c["nyt_id"]: (c.get("votes") or {}).get("total") or 0 for c in race["top_reporting_unit"].get("candidates") or []}
            fin_m = 100 * (top_v.get(opp, 0) - sum(n for k, n in top_v.items() if k in gop)) / fin_vote
            seen = 0
            for pct in CHECK_PCT:
                pt = next((x for x in real if x[1] >= pct / 100 * fin_vote), None)
                if not pt:
                    continue
                es = estimate(house, proxy, pt[0], fin_stamp)
                et = sum(e["t"] for e in es.values())
                ed = sum(e["d"] or 0 for e in es.values())
                er = sum(e["r"] or 0 for e in es.values())
                if et < 0.01 * fin_vote or pt[1] <= 0:
                    checks.append(dict(race=key, pct=pct, vote_err=None, m_err=None, naive=None))
                    continue
                m_real = 100 * (pt[2] - pt[3]) / pt[1]
                m_est = 100 * (ed - er) / et
                checks.append(dict(race=key, pct=pct, vote_err=100 * abs(et - pt[1]) / fin_vote, m_err=abs(m_est - m_real),
                                   naive=abs(fin_m - m_real), share=proxy["share"]))
                seen += 1
            per_race.append(dict(race=key, office=proxy["office"], cover=round(cover / total, 3), checked=seen))
    good = [c for c in checks if c["m_err"] is not None]
    summary = dict(rows=rows, districts_estimated=len(per_race), skipped=skipped,
                   proxies={k: (v["office"] if v else None) for k, v in proxies.items()}, by_pct={})
    for pct in CHECK_PCT:
        g = [c for c in good if c["pct"] == pct]
        if g:
            summary["by_pct"][pct] = dict(
                n=len(g), votes_counted_miss_median=round(st.median(c["vote_err"] for c in g), 1),
                margin_miss_median=round(st.median(c["m_err"] for c in g), 1),
                margin_miss_p90=round(sorted(c["m_err"] for c in g)[int(.9 * len(g))], 1),
                naive_final_margin_miss_median=round(st.median(c["naive"] for c in g), 1),
                naive_miss_p90=round(sorted(c["naive"] for c in g)[int(.9 * len(g))], 1),
                beats_naive=round(sum(c["m_err"] < c["naive"] for c in g) / len(g), 2))
    summary["no_estimate_at_check"] = sum(1 for c in checks if c["m_err"] is None)
    with open(os.path.join(a.out, "house_county_path_CHECK.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=summary, races=per_race), f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
