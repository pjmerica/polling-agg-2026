"""Per race: which surveys the fixes removed or replaced (survey = race + pollster + end date),
before vs after, as a markdown section. Margin = D/independent minus R.

    py -X utf8 poll_changes.py <before.csv> <after.csv> <out.md>
"""
import re
import sys

import pandas as pd

b = pd.read_csv(sys.argv[1])
a = pd.read_csv(sys.argv[2])
NAMES = {"2026_AK_Senate": "Alaska Senate", "2026_GA_Governor": "Georgia Governor", "2026_OH_Governor": "Ohio Governor",
         "2026_OH_Senate-S": "Ohio Senate (special)", "2026_KS_Senate": "Kansas Senate", "2026_TX_Senate": "Texas Senate",
         "2026_NE_Senate": "Nebraska Senate", "2026_ME_Senate": "Maine Senate", "2026_IA_Senate": "Iowa Senate",
         "2026_MI_Senate": "Michigan Senate"}


def squash(p):
    s = str(p).lower()
    s = re.sub(r"\((?:d|r|dem|rep)\)", "", s)
    s = re.sub(r"\bthe\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def surveys(df):
    df = df.copy()
    df["end"] = pd.to_datetime(df["end_date"]).dt.date.astype(str)
    out = {}
    for (rid, end, pol), g in df.groupby(["race_id", "end", "pollster"]):
        dem = g[g["party_std"] == "DEM"]["pct"]
        rep = g[g["party_std"] == "REP"]["pct"]
        out.setdefault(rid, []).append(dict(end=end, pollster=pol, key=squash(pol),
                                            D=dem.iloc[0] if len(dem) else None,
                                            R=rep.iloc[0] if len(rep) else None,
                                            q=",".join(sorted(g["question_id"].astype(str).str[:8].unique()))))
    return out


def fmt(s):
    d = "-" if s["D"] is None else f"{s['D']:g}"
    r = "-" if s["R"] is None else f"{s['R']:g}"
    m = "" if (s["D"] is None or s["R"] is None) else f" ({s['D'] - s['R']:+.1f})"
    return f"{s['end']} {s['pollster']}: D {d} / R {r}{m}"


B, A = surveys(b), surveys(a)
lines = ["## What changed in each competitive race's poll set", "",
         "Each line is one survey (race + pollster + end date) as the model sees it. Margin = Democrat (or "
         "Osborn) minus Republican. 'Removed' = the survey is no longer counted (a duplicate, a one-sided "
         "question or out of cycle); 'Changed' = still counted, but a different question/version of it.", ""]
for rid in NAMES:
    bs, as_ = B.get(rid, []), A.get(rid, [])
    akeys = {(s["end"], s["key"]): s for s in as_}
    removed, changed = [], []
    for s in bs:
        t = akeys.get((s["end"], s["key"]))
        if t is None:
            removed.append(s)
        elif (t["D"], t["R"]) != (s["D"], s["R"]):
            changed.append((s, t))
    lines.append(f"### {NAMES[rid]}: {len(bs)} -> {len(as_)} surveys")
    lines.append("")
    if not removed and not changed:
        lines.append("No change.")
    for s in removed:
        dup = [t for t in as_ if t["end"] == s["end"] and t["key"] != s["key"]]
        why = (" - same survey as " + "; ".join(t["pollster"] for t in dup) + " (kept)") if dup else ""
        lines.append(f"- Removed: {fmt(s)}{why}")
    for s, t in changed:
        lines.append(f"- Changed: {fmt(s)} -> D {t['D'] if t['D'] is not None else '-'} / R {t['R'] if t['R'] is not None else '-'}")
    lines.append("")
open(sys.argv[3], "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
