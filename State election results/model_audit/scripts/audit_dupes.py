"""How many surveys does the live 2026 general feed count twice after predict.py's own dedup?

A pair of question-groups is flagged as the same survey when they share race, end_date and
candidate set, and either (a) the sample size matches and every candidate's pct is within 1.0,
or (b) the normalized pollster names are equal once 'the', spaces and punctuation are removed.
Also reports single-candidate (orphan) questions and poll age vs the training data.

    py -X utf8 audit_dupes.py <raw_dir>
"""
import os
import re
import sys

MODEL = r"C:\Users\pjmer\Documents\Polling prediction model"
sys.path.insert(0, os.path.join(MODEL, "src"))
sys.path.insert(0, os.path.join(MODEL, "pipeline", "fetch"))
sys.path.insert(0, MODEL)
import pandas as pd  # noqa: E402

import features as F  # noqa: E402
import predict as P  # noqa: E402

raw = sys.argv[1]
d = P.load_agg_polls([os.path.join(raw, "nyt_polls.csv"), os.path.join(raw, "wikipedia_polls.csv")], 2026)
d["qkey"] = d["pollster"].astype(str) + "|" + d["question_id"].astype(str)


def squash(p):
    s = F.norm_pollster(p)
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"\bthe\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


qs = []
for (rid, q), g in d.groupby(["race_id", "qkey"]):
    qs.append(dict(race_id=rid, qkey=q, pollster=g["pollster"].iloc[0], squash=squash(g["pollster"].iloc[0]),
                   end=g["end_date"].iloc[0], n=g["sample_size"].iloc[0],
                   cands=frozenset(g["cand_key"]), pct=dict(zip(g["cand_key"], g["pct"])),
                   partisan=g["partisan"].iloc[0] if "partisan" in g else None))
Q = pd.DataFrame(qs)
dup_pairs = []
for (rid, end), g in Q.groupby(["race_id", "end"]):
    rows = g.to_dict("records")
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a["cands"] != b["cands"] or len(a["cands"]) < 2:
                continue
            close = all(abs(a["pct"][c] - b["pct"][c]) <= 1.0 for c in a["cands"])
            same_n = pd.notna(a["n"]) and a["n"] == b["n"]
            same_name = a["squash"] == b["squash"]
            if (same_n and close) or (same_name and a["pollster"] != b["pollster"]):
                dup_pairs.append((rid, end.date(), a["pollster"], b["pollster"], a["n"], b["n"],
                                  "same n & within 1pt" if (same_n and close) else "same name after squash"))
D = pd.DataFrame(dup_pairs, columns=["race_id", "end", "pollster_a", "pollster_b", "n_a", "n_b", "why"])
print(f"questions in feed: {len(Q)}; probable duplicate question pairs surviving dedup: {len(D)} "
      f"in {D['race_id'].nunique()} of {Q['race_id'].nunique()} races")
print(D.groupby(["pollster_a", "pollster_b"]).size().sort_values(ascending=False).head(25).to_string())
D.to_csv(os.path.join(raw, "..", "dupe_pairs.csv"), index=False)

orph = Q[Q["cands"].map(len) == 1]
print(f"\nsingle-candidate questions (opponent row missing): {len(orph)} in {orph['race_id'].nunique()} races")

# poll age: live vs training
d["days"] = (pd.Timestamp("2026-11-03") - d["end_date"]).dt.days
hist = pd.read_csv(os.path.join(MODEL, "polls_long_with_results.csv"), low_memory=False,
                   usecols=["year", "end_date", "election_date", "has_result"])
hist = hist[hist["has_result"] == 1]
hd = (pd.to_datetime(hist["election_date"], errors="coerce", format="mixed")
      - pd.to_datetime(hist["end_date"], errors="coerce", format="mixed")).dt.days
print("\npoll age (days before the election):")
print("  training 1998-2024: max %d, 99th pct %d, share > 730 days %.3f%%" % (hd.max(), hd.quantile(.99), 100 * (hd > 730).mean()))
print("  live 2026: max %d; rows > 730 days: %d (races %s)" % (d["days"].max(), (d["days"] > 730).sum(),
      sorted(d.loc[d["days"] > 730, "race_id"].unique())))
print("  per cycle max:", hd.groupby(hist["year"]).max().to_dict())
