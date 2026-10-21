"""Build SWINGS.md: how far election-night counts moved, with every table generated from data.

Inputs:  data/processed/swings.csv (scripts/swing_analysis.py)
         data/raw/wayback_2020/*.json (scripts/fetch_wayback_2020.py)
Template: scripts/swings_template.md  (tokens like {{BIG_SWINGS}})

    py "State election results/scripts/build_swings_report.py"
"""
import csv
import datetime as dt
import glob
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ORDER = ["GA", "OH", "MI", "TX", "KS", "ME", "IA", "NE", "AK"]
NAMES = {"GA": "Georgia", "OH": "Ohio", "MI": "Michigan", "TX": "Texas", "KS": "Kansas", "ME": "Maine",
         "IA": "Iowa", "NE": "Nebraska", "AK": "Alaska"}
REP = ("gop", "rep", "republican")


def f(x):
    return float(x) if x not in ("", None) else None


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "processed", "swings.csv"), encoding="utf-8")))
    for r in rows:
        r["label"] = f"{r['year']} {r['office']}" + (f" ({r['race_id'].split('-')[3]})" if "-H-" in r["race_id"] else "")
        r["label"] = r["label"].replace("U.S. House (", "House ").replace(")", "").replace("U.S. Senate", "Senate")
        if "-CD_" in r["race_id"]:
            r["label"] += " (district " + r["race_id"].split("CD_")[1].split("-")[0] + ")"
        if r["rcv"]:
            r["label"] += " [RCV, 1st round]"
    return rows


def generals(rows):
    # AK 2022 Senate: two Republicans finished on top, so a D-vs-R margin says nothing about that race
    return [r for r in rows if r["kind"] == "G" and r["final_dr"] != "" and r["race_id"] != "AK-G-S-2022-11-08"]


def swing(r, cp):
    d = f(r[f"dr_{cp}"])
    return None if d is None else f(r["final_dr"]) - d


def big_swings(rows):
    # competitive races, and only where 10%+ was counted 2 h after close (smaller counts are noise)
    g = [r for r in generals(rows) if abs(f(r["final_dr"])) <= 15 and (f(r["pct_2h"]) or 0) >= 10]
    out = []
    for s in ORDER:
        cand = [(r, swing(r, "2h")) for r in g if r["state"] == s and swing(r, "2h") is not None]
        cand.sort(key=lambda x: -abs(x[1]))
        if not cand:
            continue
        out.append(f"**{NAMES[s]}**\n")
        out.append("| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |")
        out.append("|---|---|---|---|---|---|---|")
        for r, sw in cand[:5]:
            se = swing(r, "night_end")
            out.append(f"| {r['label']} | {r['pct_2h']}% / {f(r['dr_2h']):+.1f} | "
                       f"{r['pct_midnight'] or '-'}% / {('-' if r['dr_midnight']=='' else format(f(r['dr_midnight']), '+.1f'))} | "
                       f"{r['pct_night_end'] or '-'}% / {('-' if r['dr_night_end']=='' else format(f(r['dr_night_end']), '+.1f'))} | "
                       f"{f(r['final_dr']):+.1f} | **{sw:+.1f}** | {('-' if se is None else format(se, '+.1f'))} |")
        out.append("")
    return "\n".join(out)


def comebacks(rows):
    out = ["| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Winner, final margin | Winner ahead for good from (ET) |",
           "|---|---|---|---|---|---|"]
    for r in sorted([r for r in rows if r["kind"] == "G"], key=lambda r: (ORDER.index(r["state"]), r["year"], r["label"])):
        lost2 = r["leader_2h"] and r["leader_2h"] != r["winner"]
        lostm = r["leader_midnight"] and r["leader_midnight"] != r["winner"]
        if not (lost2 or lostm):
            continue
        out.append(f"| {NAMES[r['state']]} {r['label']} | {r['race_id']} | {r['leader_2h'] or '-'} ({r['pct_2h']}%) | "
                   f"{r['leader_midnight'] or '-'} ({r['pct_midnight'] or '-'}%) | {r['winner']} +{f(r['final_margin']):.1f} | "
                   f"{r['winner_lead_for_good_et']} ({r['pct_when_winner_took_lead']}% in) |")
    return "\n".join(out)


def late_movers(rows):
    g = [(r, swing(r, "night_end")) for r in generals(rows) if swing(r, "night_end") is not None]
    g = [x for x in g if abs(x[1]) >= 1.5]
    g.sort(key=lambda x: -abs(x[1]))
    out = ["| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |", "|---|---|---|---|---|"]
    for r, sw in g:
        out.append(f"| {NAMES[r['state']]} {r['label']} | {r['pct_night_end']}% | {f(r['dr_night_end']):+.1f} | "
                   f"{f(r['final_dr']):+.1f} | **{sw:+.1f}** |")
    return "\n".join(out)


def state_pace(rows):
    g = generals(rows)
    out = ["| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |",
           "|---|---|---|---|---|---|---|---|"]
    for s in ORDER:
        for y in ("2020", "2022", "2024"):
            rs = [r for r in g if r["state"] == s and r["year"] == y]
            if not rs:
                continue
            def med(k):
                v = [f(r[k]) for r in rs if f(r[k]) is not None]
                return f"{st.median(v):.0f}%" if v else "-"
            def msw(cp):
                v = [swing(r, cp) for r in rs if swing(r, cp) is not None]
                return f"{st.median(v):+.1f}" if v else "-"
            n5 = sum(1 for r in rs if swing(r, "2h") is not None and abs(swing(r, "2h")) >= 5)
            n2 = sum(1 for r in rs if swing(r, "2h") is not None)
            out.append(f"| {NAMES[s]} | {y} | {len(rs)} | {med('pct_1h')} / {med('pct_2h')} / {med('pct_midnight')} / {med('pct_night_end')} | "
                       f"{msw('1h')} | {msw('2h')} | {msw('night_end')} | {n5} of {n2} |")
    return "\n".join(out)


def early_eday(rows):
    def dr(r, k):
        v = f(r[k])
        return -v if r["winner_party"] in REP else v
    # NYT tagged only a sliver of early votes in OH/MI 2022 (2-14%): partial data, left out
    g = [r for r in generals(rows) if r["advance_margin"] != "" and r["eday_margin"] != "" and f(r["advance_share"]) >= 25]
    out = ["| State | Year | Races | Early/mail share of votes (median) | Early/mail margin minus Election Day margin (median, range) | Top-of-ticket example |",
           "|---|---|---|---|---|---|"]
    for s in ORDER:
        for y in ("2022", "2024"):
            rs = [r for r in g if r["state"] == s and r["year"] == y]
            if not rs:
                continue
            gaps = sorted(dr(r, "advance_margin") - dr(r, "eday_margin") for r in rs)
            ex = [r for r in rs if r["office"] in ("Governor", "U.S. Senate", "President")]
            exs = "; ".join(f"{r['office'].replace('U.S. ', '')}: early/mail {dr(r, 'advance_margin'):+.1f}, Election Day {dr(r, 'eday_margin'):+.1f}" for r in ex)
            out.append(f"| {NAMES[s]} | {y} | {len(rs)} | {st.median([f(r['advance_share']) for r in rs]):.0f}% | "
                       f"{st.median(gaps):+.1f} ({gaps[0]:+.0f} to {gaps[-1]:+.0f}) | {exs} |")
    return "\n".join(out)


def primaries(rows):
    rs = [r for r in rows if r["year"] == "2026"]
    out = ["| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |",
           "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rs, key=lambda r: (ORDER.index(r["state"]), r["date"], r["race_id"])):
        flag = " **(comeback)**" if ((r["leader_2h"] and r["leader_2h"] != r["winner"]) or
                                      (r["leader_midnight"] and r["leader_midnight"] != r["winner"])) else ""
        if r["rcv"]:
            flag += " (1st round)"
            if r["official_winner"] and r["official_winner"] != r["winner"]:
                flag += f" **- {r['official_winner']} won the ranked-choice count**"
        out.append(f"| {NAMES[r['state']]} | {r['date']} | {r['office']} | {r['race_id']} | {r['pct_1h'] or '-'} / {r['pct_2h'] or '-'} / "
                   f"{r['pct_midnight'] or '-'} / {r['pct_night_end'] or '-'} | {r['winner']} +{f(r['final_margin']):.1f}{flag} | "
                   f"{r['margin_2h'] or '-'} | {r['winner_lead_for_good_et'][6:]} ({r['pct_when_winner_took_lead']}%) |")
    return "\n".join(out)


def county_2020():
    snaps = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "wayback_2020", "*.json"))):
        d = json.load(open(path))
        t = dt.datetime.strptime(d["capture"], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        snaps.append((t, d["states"]))

    def state_at(state, when):
        out, cap = {}, None
        for t, s in snaps:
            if t > when:
                break
            cap = t
            for c in s.get(state, {}).get("counties", []):
                out[c["fips"]] = c
        return out, cap

    utc = dt.timezone.utc
    points = [("midnight ET", dt.datetime(2020, 11, 4, 5, 0, tzinfo=utc)), ("6 am ET", dt.datetime(2020, 11, 4, 11, 0, tzinfo=utc))]
    out = ["| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |",
           "|---|---|---|---|---|---|"]
    for state in ["georgia", "ohio", "michigan", "texas", "kansas", "maine", "iowa", "nebraska"]:
        fin, _ = state_at(state, snaps[-1][0])
        tot = sum(c["votes"] or 0 for c in fin.values())
        for lab, when in points:
            early, cap = state_at(state, when)
            D = R = V = 0
            per = []
            for fips, c in fin.items():
                e = early.get(fips, {})
                dv = c["results"].get("bidenj", 0) - (e.get("results") or {}).get("bidenj", 0)
                rv = c["results"].get("trumpd", 0) - (e.get("results") or {}).get("trumpd", 0)
                vv = (c["votes"] or 0) - (e.get("votes") or 0)
                D, R, V = D + dv, R + rv, V + vv
                if vv > 0:
                    per.append((c["name"], vv, 100 * (dv - rv) / vv))
            per.sort(key=lambda x: -x[1])
            share = 100 * V / tot
            if share < 0.5:
                out.append(f"| {state.title()} | {lab} | under 0.5% | - | - | {cap.astimezone(dt.timezone(dt.timedelta(hours=-5))).strftime('%I:%M %p').lstrip('0')} |")
                continue
            top = "; ".join(f"{n} {100 * v / tot:.1f}% ({m:+.0f})" for n, v, m in per[:4])
            out.append(f"| {state.title()} | {lab} | {share:.0f}% | {100 * (D - R) / V:+.1f} | {top} | "
                       f"{cap.astimezone(dt.timezone(dt.timedelta(hours=-5))).strftime('%I:%M %p').lstrip('0')} |")
    return "\n".join(out)


def main():
    rows = load()
    tmpl = open(os.path.join(HERE, "swings_template.md"), encoding="utf-8").read()
    parts = {"BIG_SWINGS": big_swings(rows), "COMEBACKS": comebacks(rows), "LATE_MOVERS": late_movers(rows),
             "STATE_PACE": state_pace(rows), "EARLY_EDAY": early_eday(rows), "PRIMARIES_2026": primaries(rows),
             "COUNTY_2020": county_2020(), "N_RACES": str(len(rows)), "N_GENERAL": str(len(generals(rows)))}
    for k, v in parts.items():
        tmpl = tmpl.replace("{{%s}}" % k, v)
    assert "{{" not in tmpl
    with open(os.path.join(ROOT, "SWINGS.md"), "w", encoding="utf-8") as fh:
        fh.write(tmpl)
    print("wrote SWINGS.md")


if __name__ == "__main__":
    main()
