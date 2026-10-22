"""Compare two snapshot_predict.py outputs: per race, the leading two candidates' poll numbers and
win probability before vs after. Prints markdown tables (competitive races, then the biggest movers).

    py -X utf8 compare_snapshots.py <before.csv> <after.csv> [label_after]
"""
import sys

import pandas as pd

b = pd.read_csv(sys.argv[1])
a = pd.read_csv(sys.argv[2])
label = sys.argv[3] if len(sys.argv) > 3 else "after"
RACES = ["2026_AK_Senate", "2026_GA_Governor", "2026_OH_Governor", "2026_OH_Senate-S", "2026_KS_Senate",
         "2026_TX_Senate", "2026_NE_Senate", "2026_ME_Senate", "2026_IA_Senate", "2026_MI_Senate"]


def top2(df):
    df = df.sort_values(["race_id", "win_prob_norm"], ascending=[True, False])
    return df[df["party"].isin(["DEM", "REP"]) | (df.groupby("race_id").cumcount() < 2)].groupby("race_id").head(2)


def fmt(x, nd=1):
    return "-" if pd.isna(x) else f"{x:.{nd}f}"


bt = top2(b).set_index(["race_id", "cand_key"])
at = a.set_index(["race_id", "cand_key"])
rows = []
for (rid, ck), r in bt.iterrows():
    x = at.loc[(rid, ck)] if (rid, ck) in at.index else None
    rows.append(dict(race=rid, candidate=r["candidate"], party=r["party"],
                     n_b=r["n_polls"], n_a=None if x is None else x["n_polls"],
                     avg_b=r["poll_avg"], avg_a=None if x is None else x["poll_avg"],
                     lead_b=r["poll_lead"], lead_a=None if x is None else x["poll_lead"],
                     p_b=100 * r["win_prob_norm"], p_a=None if x is None else 100 * x["win_prob_norm"],
                     lvl_b=r.get("bio_office_level"), lvl_a=None if x is None else x.get("bio_office_level")))
R = pd.DataFrame(rows)

print(f"### Competitive races: before vs {label}\n")
print("| Race | Candidate | Polls used | Poll average | Poll lead | Win probability |")
print("|---|---|---|---|---|---|")
for r in R[R["race"].isin(RACES)].itertuples():
    print(f"| {r.race.replace('2026_', '')} | {r.candidate} ({r.party}) | {fmt(r.n_b, 0)} -> {fmt(r.n_a, 0)} | "
          f"{fmt(r.avg_b, 2)} -> {fmt(r.avg_a, 2)} | {fmt(r.lead_b, 2)} -> {fmt(r.lead_a, 2)} | "
          f"{fmt(r.p_b)}% -> {fmt(r.p_a)}% ({'' if pd.isna(r.p_a) else f'{r.p_a - r.p_b:+.1f}'}) |")

fav = R.sort_values("p_b", ascending=False).groupby("race").head(1).copy()
fav["chg"] = fav["p_a"] - fav["p_b"]
fav["flip"] = fav["p_a"] < 50
print(f"\n### Whole slate ({fav['race'].nunique()} races): favorite's probability, before vs {label}\n")
print(f"- moved 2+ pts: {(fav['chg'].abs() >= 2).sum()}; 5+ pts: {(fav['chg'].abs() >= 5).sum()}; "
      f"favorite changed: {int(fav['flip'].sum())}")
print("\n| Race | Favorite before | Before | After | Change | Poll lead before -> after |")
print("|---|---|---|---|---|---|")
for r in fav.reindex(fav["chg"].abs().sort_values(ascending=False).index).head(20).itertuples():
    print(f"| {r.race.replace('2026_', '')} | {r.candidate} ({r.party}) | {fmt(r.p_b)}% | {fmt(r.p_a)}% | "
          f"{'' if pd.isna(r.chg) else f'{r.chg:+.1f}'} | {fmt(r.lead_b, 2)} -> {fmt(r.lead_a, 2)} |")
