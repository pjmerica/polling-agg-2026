"""Build competitive_races.md from the published forecast (docs/forecast_data.js): every Governor
and Senate race whose model favorite is at 75% or less, the ones just outside the cut, races where
the market favors the other candidate, and Governor/Senate races the forecast doesn't cover.

    py "State election results/scripts/build_competitive.py"
"""
import json
import os
import re

import build_state_guide as g

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CUT, NEAR = 0.75, 0.80
NOTES = """## Notes from the research that affect these races

- **Nebraska Senate:** no Democratic nominee (Cindy Burbank withdrew in July and backed Osborn). Ballot: Ricketts (R), Osborn (I), Conboy (America First), Richards (Nebraska Working People Party), Marvin (Legal Marijuana NOW; withdrew but stays on the ballot).
- **Alaska Senate** and **Maine Senate** use ranked-choice voting; a winner may not be known until the RCV count (Alaska Nov 18; Maine usually 8-10 days after the election).
- **Georgia Governor:** majority needed or a Dec 1 runoff; two-candidate ballot, so runoff risk is near zero. A margin of 0.5% or less triggers an automatic statewide hand recount (2026 law).
- **Nevada Governor:** Lombardo (R), Aaron Ford (D), Danielle Ford (no party) and "None of these candidates", which is reported but never decides the winner (NRS 293.269). Close races are counted Wednesday to Saturday; the late count has leaned Democratic in every statewide race since 2020.
- **Oregon Governor:** a 2022 rematch (Kotek D vs Drazan R, plus Pacific Green's Brett Smith). Election Day drop-offs, a quarter of the vote, are counted Wednesday to Friday; automatic recount at 0.2%.
- **Texas Governor:** counted with the Senate race; the Texas rules apply unchanged.
"""


def label(r):
    off = "Senate (special)" if r["office"] == "Senate" and r.get("special") else r["office"]
    return r["state_name"], off


def row(r):
    c = sorted(r["cands"], key=lambda x: -(x.get("win") or 0))
    a, b = c[0], c[1]
    m = None
    if a.get("margin") is not None and b.get("margin") is not None:
        m = (a["margin"] - b["margin"]) / 2
    mk = r.get("market")
    market = f"{mk['name']} ({mk['side'] if mk['side'] in ('DEM', 'REP', 'IND') else '?'}) {100 * mk['prob']:.0f}%" if mk and mk.get("prob") is not None else "-"
    st, off = label(r)
    return (f"| {st} | {off} | {a['name']} ({a['party']}) | {100 * a['win']:.1f}% | "
            f"{'-' if m is None else f'{m:+.1f}'} | {b['name']} ({b['party']}) | {market} | {r.get('n_surveys', '-')} |")


def main():
    data = g.forecast()
    races = [r for r in data["races"] if r["office"] in ("Governor", "Senate") and r.get("cands")]
    for r in races:
        r["_p"] = max(c.get("win") or 0 for c in r["cands"])
    comp = sorted([r for r in races if r["_p"] <= CUT], key=lambda r: r["_p"])
    near = sorted([r for r in races if CUT < r["_p"] <= NEAR], key=lambda r: r["_p"])

    head = ("| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | "
            "Market (side priced) | Surveys |\n|---|---|---|---|---|---|---|---|")
    by_state = {}
    for r in comp:
        st, off = label(r)
        by_state.setdefault(st, []).append(off)

    flips = []
    for r in comp + near:
        fav = sorted(r["cands"], key=lambda x: -(x.get("win") or 0))[0]
        mk = r.get("market")
        if mk and mk.get("prob") is not None:
            p = mk["prob"] if mk["name"] == fav["name"] else 1 - mk["prob"]
            if p < 0.5:
                st, off = label(r)
                flips.append(f"- {st} {off}: model {fav['name']} {100 * r['_p']:.1f}%, market implies "
                             f"{fav['name']} about {100 * p:.0f}%")

    # Governor/Senate races on the ballot (docs/data.js) that the forecast doesn't cover
    s = open(os.path.join(g.DOCS, "data.js"), encoding="utf-8").read()
    ballot = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    covered = {r["agg_id"] for r in data["races"]}
    missing = sorted({x["race_id"] for x in ballot if re.match(r"2026-(GOV|SEN)-", x["race_id"])} - covered)
    missing = [m.replace("2026-GOV-", "").replace("2026-SEN-", "") + ("-Gov" if "GOV" in m else "-Sen") for m in missing]

    out = [
        "# Competitive 2026 Governor and Senate races",
        "",
        f"Source: `docs/forecast_data.js` (model run {data['predictions_as_of'][:16].replace('T', ' ')} UTC, polls "
        f"through {data['polls_as_of']}). Competitive = the model's favorite has a win probability of 75% or less. "
        "Built by `scripts/build_competitive.py`; numbers move with every model refresh, so rebuild before relying on it.",
        "",
        "## By state",
        "",
        "| State | Competitive races |",
        "|---|---|",
        *[f"| {st} | {', '.join(offs)} |" for st, offs in by_state.items()],
        "",
        f"{len(comp)} races in {len(by_state)} states.",
        "",
        "## Competitive races (favorite at 75% or less)",
        "",
        head,
        *[row(r) for r in comp],
        "",
        "## Just outside the cut (favorite 75-80%)",
        "",
        "Not part of the vote-timing research; listed so a model shift is easy to spot.",
        "",
        head,
        *([row(r) for r in near] or ["| (none) | | | | | | | |"]),
        "",
        "## Market favors a different candidate",
        "",
        *(flips or ["- None."]),
        "",
        "## Not in the forecast",
        "",
        "These Governor/Senate races are on the ballot (`docs/data.js`) but not in the forecast file, so they "
        f"were not screened: {', '.join(missing) or 'none'}.",
        "",
        NOTES,
    ]
    with open(os.path.join(ROOT, "competitive_races.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote competitive_races.md: {len(comp)} competitive, {len(near)} near the cut")


if __name__ == "__main__":
    main()
