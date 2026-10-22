"""Dump the poll rows the model keeps for given races (after load_agg_polls), from a given checkout.
    py -X utf8 dump_race_polls.py <model_root> <polls_dir> <out_csv> <race_id> [race_id ...]"""
import os
import sys

root, polls_dir, out_csv = sys.argv[1], sys.argv[2], sys.argv[3]
races = sys.argv[4:]
sys.path[:0] = [os.path.join(root, "src"), os.path.join(root, "pipeline", "fetch"), root]
os.chdir(root)
import predict as P  # noqa: E402

d = P.load_agg_polls([os.path.join(polls_dir, "nyt_polls.csv"), os.path.join(polls_dir, "wikipedia_polls.csv")], 2026)
cols = [c for c in ["race_id", "end_date", "pollster", "candidate", "party_std", "pct", "sample_size",
                    "population", "partisan", "question_id"] if c in d.columns]
d[d["race_id"].isin(races)].sort_values(["race_id", "end_date", "pollster", "candidate"])[cols].to_csv(out_csv, index=False)
print("rows", int(d["race_id"].isin(races).sum()))
