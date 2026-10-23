"""Which states' counts swing the most while votes come in? Every state, 2020-2024.

Reads NYT's minute-by-minute statewide timelines for every President, Senate and Governor general
election 2020-2024 (data/raw/nyt_all, from `fetch_nyt_history.py --all`) and measures, per race:

  move after 25% / 50% / 75% counted   final margin minus the margin at the first update with that
                                       share in (a big first batch can already be past 25%)
  move after election night            final margin minus the margin at 6 am ET the next morning
  biggest gap                          largest distance between the running margin and the final
                                       once 25% was counted
  lead changes                         after 10% counted; leads held under 10 minutes are ignored
  leader lost                          the leader at 25%, 50% or 75% counted, or at 6 am ET, lost

Margins are Democrat (or the top non-Republican) minus Republican, in points of the votes counted
so far; positive moves mean the count moved toward the Democrat. A state's volatility score weighs
two things equally: SIZE (the average of its percentile ranks on the typical, i.e. median, size of the
move after 25%, 50% and 75% counted and after election night) and REVERSALS (its percentile rank on
the share of races whose leader at one of those points lost).

Writes data/processed/volatility_races.csv, data/processed/volatility_states.csv and VOLATILITY.md
(from scripts/volatility_template.md).

    py "State election results/scripts/volatility.py"
"""
import csv
import glob
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import swing_analysis as sa  # noqa: E402  - same parsing and checkpoint code as SWINGS.md

ABBR = {"alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
        "connecticut": "CT", "delaware": "DE", "district-of-columbia": "DC", "florida": "FL", "georgia": "GA",
        "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
        "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
        "nebraska": "NE", "nevada": "NV", "new-hampshire": "NH", "new-jersey": "NJ", "new-mexico": "NM",
        "new-york": "NY", "north-carolina": "NC", "north-dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode-island": "RI", "south-carolina": "SC", "south-dakota": "SD",
        "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
        "west-virginia": "WV", "wisconsin": "WI", "wyoming": "WY"}
NAME = {v: k.replace("-", " ").title().replace("Of", "of") for k, v in ABBR.items()}
# Main poll close, hours after midnight ET, Nov 2020/2022/2024 (all EST). Where a state straddles time
# zones this is when most of it closes. Iowa 2020 (22.0) is handled in swing_analysis.close_hours.
CLOSE = {"IN": 18.0, "KY": 18.0, "FL": 19.0, "GA": 19.0, "SC": 19.0, "VA": 19.0, "VT": 19.0, "NH": 19.0,
         "NC": 19.5, "OH": 19.5, "WV": 19.5,
         "AL": 20.0, "CT": 20.0, "DE": 20.0, "DC": 20.0, "IL": 20.0, "KS": 20.0, "ME": 20.0, "MD": 20.0,
         "MA": 20.0, "MI": 20.0, "MS": 20.0, "MO": 20.0, "NJ": 20.0, "OK": 20.0, "PA": 20.0, "RI": 20.0,
         "SD": 20.0, "TN": 20.0, "TX": 20.0, "AR": 20.5,
         "AZ": 21.0, "CO": 21.0, "IA": 21.0, "LA": 21.0, "MN": 21.0, "NE": 21.0, "NM": 21.0, "NY": 21.0,
         "ND": 21.0, "WI": 21.0, "WY": 21.0,
         "ID": 22.0, "MT": 22.0, "NV": 22.0, "UT": 22.0,
         "CA": 23.0, "OR": 23.0, "WA": 23.0, "HI": 24.0, "AK": 24.0}
sa.STATES.update(ABBR)
sa.CLOSE.update(CLOSE)
COMPETITIVE = {"GA", "OH", "MI", "TX", "KS", "ME", "IA", "NE", "NV", "OR", "AK"}
RAW = os.path.join(ROOT, "data", "raw", "nyt_all")
OFFICE = {"president": "President", "senate": "Senate", "u.s. senate": "Senate", "governor": "Governor"}
MEASURES = ["move25", "move50", "move75", "move6am"]


def series(r):
    """(time, share counted %, margin D/I minus R) for every timeline point; plus the final margin."""
    cands = r["cands"]
    order = sorted(cands, key=lambda k: -cands[k]["votes"])
    if len(order) < 2:
        return None
    a, b = order[0], order[1]
    rep_in_top2 = [k for k in (a, b) if cands[k]["party"] in sa.REP]
    if len(rep_in_top2) != 1:  # need exactly one Republican in the top two (no D-v-D, R-v-R)
        return None
    rep = rep_in_top2[0]
    opp = b if rep == a else a
    total = sum(c["votes"] for c in cands.values())
    pts = sorted((p for p in r["pts"] if p[1] > 0), key=lambda p: p[0])
    if len(pts) < 5 or not total:  # races whose timeline is unusable (see swing_analysis.races_2020)
        return None
    denom = max([total] + [p[1] for p in pts])
    out = [(t, 100 * tot / denom, 100 * (v.get(opp, 0) - v.get(rep, 0)) / tot) for t, tot, v in pts]
    final = 100 * (cands[opp]["votes"] - cands[rep]["votes"]) / total
    return out, final, cands[opp]["party"]


def at_share(s, pct):
    for t, share, m in s:
        if share >= pct:
            return m
    return None


def lead_changes(s):
    seq, prev = [], None
    for t, share, m in s:
        if share < 10:
            continue
        lead = m >= 0
        if lead != prev:
            seq.append(t)
            prev = lead
    # changes after the first leader; a run of flips each under 10 minutes apart nets out:
    # an odd number of quick flips is one change, an even number is none
    changes, i = 0, 1
    while i < len(seq):
        j = i
        while j + 1 < len(seq) and (seq[j + 1] - seq[j]).total_seconds() < 600:
            j += 1
        changes += 1 if (j - i) % 2 == 0 else 0
        i = j + 1
    return changes


def race_rows():
    rows = []
    for path in sorted(glob.glob(os.path.join(RAW, "*", "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        gen = sa.races_2020(path, d) if "data" in d else sa.races_new(path, d)
        for r in gen:
            if r["kind"] != "G":
                continue
            office = OFFICE.get(str(r["office"]).lower())
            if not office:
                continue
            x = series(r)
            row = sa.analyse(r)
            if not x or not row:
                continue
            s, final, opp_party = x
            m = {k: at_share(s, k) for k in (25, 50, 75)}
            m6 = None if row["dr_night_end"] == "" else row["dr_night_end"]
            after25 = [v for t, share, v in s if share >= 25]
            checks = [v for v in (m[25], m[50], m[75], m6) if v is not None]
            rows.append(dict(
                state=r["state"], year=r["date"].year, office=office, race_id=r["race_id"],
                final=round(final, 2), opp_party=opp_party,
                move25=None if m[25] is None else round(final - m[25], 2),
                move50=None if m[50] is None else round(final - m[50], 2),
                move75=None if m[75] is None else round(final - m[75], 2),
                pct6am=row["pct_night_end"], move6am=None if m6 is None else round(final - m6, 2),
                max_gap=round(max(abs(v - final) for v in after25), 2) if after25 else None,
                lead_changes=lead_changes(s),
                lost25=None if m[25] is None else int((m[25] >= 0) != (final >= 0)),
                lost6am=None if m6 is None else int((m6 >= 0) != (final >= 0)),
                lost_any=int(any((v >= 0) != (final >= 0) for v in checks)),
                first_votes_et=row["first_votes_et"]))
    return rows


def pct_rank(values, v):
    """Percentile rank with ties at the middle of their range (29 states tied at 0 reversals share ~28)."""
    return 100 * (sum(1 for x in values if x < v) + 0.5 * sum(1 for x in values if x == v)) / len(values)


def states(rows):
    out = []
    for s in sorted({r["state"] for r in rows}):
        rs = [r for r in rows if r["state"] == s]

        def med(k, absolute=True):
            v = [abs(r[k]) if absolute else r[k] for r in rs if r[k] is not None]
            return round(st.median(v), 2) if v else None

        worst = max(rs, key=lambda r: r["max_gap"] or 0)
        pace = [float(r["pct6am"]) for r in rs if r["pct6am"] != ""]
        out.append(dict(state=s, name=NAME[s], races=len(rs),
                        move25=med("move25"), move50=med("move50"), move75=med("move75"), move6am=med("move6am"),
                        dir25=med("move25", False), dir6am=med("move6am", False), max_gap=med("max_gap"),
                        lead_changes=sum(r["lead_changes"] for r in rs),
                        races_with_change=sum(1 for r in rs if r["lead_changes"] > 0),
                        lost=sum(r["lost_any"] for r in rs),
                        worst=f"{worst['year']} {worst['office']} ({worst['max_gap']:.0f})" if worst["max_gap"] else "-",
                        pct6am=round(st.median(pace), 1) if pace else None,
                        competitive=s in COMPETITIVE))
    for k in MEASURES:
        vals = [x[k] for x in out if x[k] is not None]
        for x in out:
            x[f"r_{k}"] = pct_rank(vals, x[k]) if x[k] is not None else None
    rates = [x["lost"] / x["races"] for x in out]
    for x in out:
        x["r_lost"] = pct_rank(rates, x["lost"] / x["races"])
        size = [x[f"r_{k}"] for k in MEASURES if x[f"r_{k}"] is not None]
        x["size_score"] = round(sum(size) / len(size), 1)
        x["score"] = round((x["size_score"] + x["r_lost"]) / 2, 1)
    out.sort(key=lambda x: -x["score"])
    for i, x in enumerate(out, 1):
        x["rank"] = i
    return out


def fmt(v, sign=False):
    if v is None:
        return "-"
    return f"{v:+.1f}" if sign else f"{v:.1f}"


def tables(rows, sts):
    head = ("| Rank | State | Score (size / reversals) | Races | Typical move after 25% counted | after 50% | after 75% | "
            "after election night (6 am ET) | Direction after 25% (+ = toward D) | Races whose leader at 25/50/75% or 6 am lost | "
            "Races with a lead change | "
            "Counted by 6 am ET | Biggest gap (race, pts) |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    def line(x):
        name = f"**{x['name']}**" if x["competitive"] else x["name"]
        pace = "-" if x["pct6am"] is None else f"{x['pct6am']:.0f}%"
        return (f"| {x['rank']} | {name} | {x['score']:.0f} ({x['size_score']:.0f} / {x['r_lost']:.0f}) | {x['races']} | "
                f"{fmt(x['move25'])} | {fmt(x['move50'])} | "
                f"{fmt(x['move75'])} | {fmt(x['move6am'])} | {fmt(x['dir25'], True)} | {x['lost']} | "
                f"{x['races_with_change']} | {pace} | {x['worst']} |")
    top = "\n".join([head] + [line(x) for x in sts[:15]])
    full = "\n".join([head] + [line(x) for x in sts])
    comp = "\n".join([head] + [line(x) for x in sts if x["competitive"]])

    big = sorted([r for r in rows if r["max_gap"] is not None and abs(r["final"]) <= 10],
                 key=lambda r: -r["max_gap"])[:25]
    races = ["| Race | Final margin | Biggest gap after 25% counted | Move after 25% | after 50% | after 75% | after 6 am ET | Lead changes | A checkpoint leader lost |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in big:
        races.append(f"| {NAME[r['state']]} {r['year']} {r['office']} | {r['final']:+.1f} | **{r['max_gap']:.1f}** | "
                     f"{fmt(r['move25'], True)} | {fmt(r['move50'], True)} | {fmt(r['move75'], True)} | {fmt(r['move6am'], True)} | "
                     f"{r['lead_changes']} | {'yes' if r['lost_any'] else 'no'} |")
    late = sorted([r for r in rows if r["move6am"] is not None and abs(r["move6am"]) >= 1.5], key=lambda r: -abs(r["move6am"]))[:25]
    lates = ["| Race | Counted by 6 am ET | Final margin | Move after 6 am ET | 6 am leader lost |", "|---|---|---|---|---|"]
    for r in late:
        lates.append(f"| {NAME[r['state']]} {r['year']} {r['office']} | {r['pct6am']}% | {r['final']:+.1f} | **{r['move6am']:+.1f}** | "
                     f"{'yes' if r['lost6am'] else 'no'} |")
    return top, full, comp, "\n".join(races), "\n".join(lates)


def main():
    rows = race_rows()
    sts = states(rows)
    proc = os.path.join(ROOT, "data", "processed")
    for name, data in (("volatility_races.csv", rows), ("volatility_states.csv", sts)):
        with open(os.path.join(proc, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    top, full, comp, races, lates = tables(rows, sts)
    tmpl = open(os.path.join(HERE, "volatility_template.md"), encoding="utf-8").read()
    parts = {"TOP15": top, "ALL_STATES": full, "COMPETITIVE": comp, "BIG_RACES": races, "LATE_RACES": lates,
             "N_RACES": str(len(rows)), "N_STATES": str(len(sts))}
    for k, v in parts.items():
        tmpl = tmpl.replace("{{%s}}" % k, v)
    assert "{{" not in tmpl, "unfilled token"
    with open(os.path.join(ROOT, "VOLATILITY.md"), "w", encoding="utf-8") as f:
        f.write(tmpl)
    print(f"{len(rows)} races in {len(sts)} states -> VOLATILITY.md")


if __name__ == "__main__":
    main()
