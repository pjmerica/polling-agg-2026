"""Side-by-side win probabilities from several snapshot_predict.py outputs, for the race favorite in the
first file. Prints a markdown table plus a whole-slate summary per later file.

    py -X utf8 attribution.py "label=before.csv" "label=next.csv" ... [--races id,id,...]
"""
import sys

import pandas as pd

args = [a for a in sys.argv[1:] if not a.startswith("--races")]
races = None
for a in sys.argv[1:]:
    if a.startswith("--races"):
        races = a.split("=", 1)[1].split(",")
snaps = []
for a in args:
    label, path = a.split("=", 1)
    snaps.append((label, pd.read_csv(path)))

first = snaps[0][1].sort_values(["race_id", "win_prob_norm"], ascending=[True, False])
fav = first.groupby("race_id").head(1).set_index("race_id")[["candidate", "party"]]
for label, df in snaps:
    s = df.set_index(["race_id", "cand_key" if "cand_key" in df else "candidate"])["win_prob_norm"]
    key = first.groupby("race_id").head(1).set_index("race_id")["cand_key" if "cand_key" in df else "candidate"]
    fav[label] = [s.get((r, k)) for r, k in key.items()]

rows = fav.loc[[r for r in races if r in fav.index]] if races else fav
cols = [lbl for lbl, _ in snaps]
print("| Race | Favorite before | " + " | ".join(cols) + " |")
print("|---|---|" + "---|" * len(cols))
for rid, r in rows.iterrows():
    vals = " | ".join("-" if pd.isna(r[c]) else f"{100 * r[c]:.1f}%" for c in cols)
    print(f"| {rid.replace('2026_', '')} | {r['candidate']} ({r['party']}) | {vals} |")

print()
base = fav[cols[0]]
for c in cols[1:]:
    d = (fav[c] - base).abs() * 100
    print(f"- **{c}** vs {cols[0]}: {int((d >= 2).sum())} of {int(d.notna().sum())} races moved 2+ pts, "
          f"{int((d >= 5).sum())} moved 5+, favorite changed in {int((fav[c] < 0.5).sum())}")
