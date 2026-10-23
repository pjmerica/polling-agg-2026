"""Statewide election-night curves from the NYT timelines (2020, 2022, 2024).

For every state/race/year in data/raw/nyt: share of the final vote counted and the
margin of the counted vote at fixed hours after the state's poll close, against
the final margin. Margin = top non-Republican minus top Republican, % of all votes.

Writes:
    data/processed/state_timeseries.csv   every timeline point, tidy
    data/processed/state_curves.csv       checkpoint table
    state_curves.md                       the checkpoint table, readable

    py "State election results/scripts/state_curves.py"
"""
import csv
import datetime as dt
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw", "nyt")
PROC = os.path.join(ROOT, "data", "processed")

# Main poll close, ET (EST, UTC-5, in 2020/2022/2024/2026), as hours after midnight ET.
# Later-closing parts (MI UP, TX El Paso, KS west, OR Malheur earlier) are ignored; AK = 8 p.m. AKST.
# Iowa closed at 9 p.m. CT (10 p.m. ET) until 2021 (SF 413 moved it to 8 p.m. from 2022).
CLOSE_ET = {"georgia": 19.0, "ohio": 19.5, "michigan": 20.0, "texas": 20.0, "kansas": 20.0,
            "maine": 20.0, "iowa": 21.0, "nebraska": 21.0, "nevada": 22.0, "oregon": 23.0,
            "alaska": 24.0}
CHECKPOINTS = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 9, 15, 24, 48]  # hours after poll close
REP = {"republican", "gop", "rep"}
ELECTION_DAY = {2020: dt.date(2020, 11, 3), 2022: dt.date(2022, 11, 8), 2024: dt.date(2024, 11, 5)}


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(path):
    year = int(os.path.basename(os.path.dirname(path)))
    state, race = os.path.basename(path)[:-5].split("-", 1)
    d = json.load(open(path, encoding="utf-8"))
    pts = []  # (ts, total, {cand: votes}, {cand: advance votes} or None)
    if year == 2020:
        r = d["data"]["races"][0]
        party = {c["candidate_key"]: c["party_id"] for c in r["candidates"]}
        final = {c["candidate_key"]: c["votes"] for c in r["candidates"]}
        for t in r["timeseries"]:
            v = t["votes"]
            pts.append((parse_ts(t["timestamp"]), v, {k: s * v for k, s in t["vote_shares"].items()}, None))
    else:
        r = d["races"][0]
        party = {k: (m.get("party") or {}).get("nyt_id", "") for k, m in r["candidate_metadata"].items()}
        top = r["top_reporting_unit"]
        final = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in top["candidates"]}
        for t in next(iter(d["timeseries"].values()), []):
            stamp = t.get("greatest_updated_at") or t.get("provider_updated_at")
            votes = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in t["candidates"] if c.get("votes")}
            adv = {c["nyt_id"]: c["votes"]["advance"] for c in t["candidates"]
                   if c.get("votes") and "advance" in c["votes"]}
            pts.append((parse_ts(stamp), t.get("total_votes") or sum(votes.values()), votes, adv or None))
    pts = sorted((p for p in pts if p[1] > 0), key=lambda p: p[0])
    party = {k: str(v).lower() for k, v in party.items()}
    reps = [k for k in final if party.get(k) in REP]
    opps = [k for k in final if party.get(k) not in REP]
    if not reps or not opps:
        return None  # e.g. AK 2022 Senate (two Republicans)
    rep = max(reps, key=final.get)
    opp = max(opps, key=final.get)
    total_final = sum(final.values())
    close_h = 22.0 if (state == "iowa" and year < 2022) else CLOSE_ET[state]
    close = dt.datetime.combine(ELECTION_DAY[year], dt.time(0), dt.timezone(dt.timedelta(hours=-5))) \
        + dt.timedelta(hours=close_h)
    return dict(year=year, state=state, race=race, rep=rep, opp=opp, opp_party=party.get(opp, ""),
                total_final=total_final, final_margin=100 * (final[opp] - final[rep]) / total_final,
                close=close, pts=pts)


def at(race, hours):
    """Last timeline point at or before close + hours."""
    cutoff = race["close"] + dt.timedelta(hours=hours)
    best = None
    for p in race["pts"]:
        if p[0] <= cutoff:
            best = p
    return best


def main():
    os.makedirs(PROC, exist_ok=True)
    races = [r for r in (load(p) for p in sorted(glob.glob(os.path.join(RAW, "*", "*.json")))) if r]
    with open(os.path.join(PROC, "state_timeseries.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "state", "race", "ts_utc", "hours_after_close", "votes", "pct_of_final",
                    "opp_votes", "rep_votes", "margin_pts", "advance_votes"])
        for r in races:
            for ts, tot, v, adv in r["pts"]:
                h = (ts - r["close"]).total_seconds() / 3600
                m = 100 * (v.get(r["opp"], 0) - v.get(r["rep"], 0)) / tot
                w.writerow([r["year"], r["state"], r["race"], ts.isoformat(), round(h, 3), round(tot),
                            round(100 * tot / r["total_final"], 2), round(v.get(r["opp"], 0)),
                            round(v.get(r["rep"], 0)), round(m, 2),
                            round(sum(adv.values())) if adv else ""])
    rows = []
    for r in races:
        for h in CHECKPOINTS:
            p = at(r, h)
            if p is None:
                pct = margin = None
            else:
                pct = 100 * p[1] / r["total_final"]
                margin = 100 * (p[2].get(r["opp"], 0) - p[2].get(r["rep"], 0)) / p[1]
            rows.append(dict(year=r["year"], state=r["state"], race=r["race"], opp_party=r["opp_party"],
                             hours=h, pct_counted=pct, counted_margin=margin, final_margin=r["final_margin"],
                             shift_to_final=None if margin is None else r["final_margin"] - margin))
    with open(os.path.join(PROC, "state_curves.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for x in rows:
            w.writerow({k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items()})
    write_md(races, rows)
    print(f"{len(races)} races -> data/processed/state_curves.csv, state_curves.md")


def fmt(pct, margin):
    if pct is None:
        return "-"
    return f"{pct:.0f}% / {margin:+.1f}"


def write_md(races, rows):
    hrs = [1, 2, 3, 4, 6, 15, 24]
    by = {(x["year"], x["state"], x["race"], x["hours"]): x for x in rows}
    out = ["# Election-night curves by state (NYT timelines)", "",
           "Each cell: **% of the final vote counted / margin of the counted vote** at N hours after the "
           "state's main poll close. Margin = top non-Republican minus top Republican, points of all "
           "votes (+ = Democrat/independent ahead). *Shift* = final margin minus the margin at 2 hours "
           "after close: positive means the count moved toward the non-Republican after that point.", "",
           "Poll close used (ET): GA 7:00, OH 7:30, MI/TX/KS/ME 8:00, IA/NE 9:00 (Iowa 2020: 10:00, before "
           "SF 413 moved its close an hour earlier), NV 10:00, OR 11:00, AK midnight. "
           "Built by `scripts/state_curves.py` from `data/raw/nyt` (2020, 2022, 2024).", "",
           "Caveats:", "",
           "- 2024 **president** timelines cover only 8 p.m.-5:40 a.m. ET (NYT model window); later cells "
           "repeat the last point. 2024 Senate files run through certification.",
           "- 2020 timelines are Edison data; the vote-share fields are rounded to 0.1 pt.",
           "- Alaska 2022 Senate: both leading candidates are Republican (Murkowski, Tshibaka), so the margin "
           "column is the Democrat vs the top Republican and says nothing about that race.",
           "- Maine 2024 Senate: the non-Republican is King (I). Nebraska 2024 Senate: Osborn (I).",
           "- Rules changed since these years (OH grace period ended, GA early votes due by 8 p.m., MI early "
           "tabulation from 2024): see the report.", ""]
    for state in CLOSE_ET:
        rs = [r for r in races if r["state"] == state]
        if not rs:
            continue
        out += [f"## {state.title()}", "",
                "| Year | Race | " + " | ".join(f"+{h}h" for h in hrs) + " | Final | Shift after +2h |",
                "|---|---|" + "---|" * (len(hrs) + 2)]
        for r in sorted(rs, key=lambda r: (r["year"], r["race"])):
            cells = [fmt(by[(r["year"], state, r["race"], h)]["pct_counted"],
                         by[(r["year"], state, r["race"], h)]["counted_margin"]) for h in hrs]
            s2 = by[(r["year"], state, r["race"], 2)]["shift_to_final"]
            out.append(f"| {r['year']} | {r['race']} | " + " | ".join(cells) +
                       f" | {r['final_margin']:+.1f} | {'-' if s2 is None else f'{s2:+.1f}'} |")
        out.append("")
    with open(os.path.join(ROOT, "state_curves.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    main()
