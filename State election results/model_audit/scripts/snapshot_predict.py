"""Run the model's own predict pipeline (load_agg_polls -> build_candidate_table -> win model) from a
given checkout of the model repo and a given poll directory, and write one row per candidate:
poll numbers the model sees (n_polls, poll_avg, poll_lead, n_surveys) and the win probability.

    py -X utf8 snapshot_predict.py <model_root> <polls_dir> <natl_env> <out_csv> [win_model_json]
"""
import json
import os
import sys

root, polls_dir, ne_val, out_csv = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
sys.path[:0] = [os.path.join(root, "src"), os.path.join(root, "pipeline", "fetch"), root]
os.chdir(root)

import pandas as pd  # noqa: E402
import xgboost as xgb  # noqa: E402

import features as F  # noqa: E402
import predict as P  # noqa: E402
from cycles import natl_env as natl_env_hist  # noqa: E402
from macro_features import build_macro  # noqa: E402

d = P.load_agg_polls([os.path.join(polls_dir, "nyt_polls.csv"), os.path.join(polls_dir, "wikipedia_polls.csv")], 2026)
hist = pd.read_csv(os.path.join(root, "polls_long_with_results.csv"), low_memory=False)
hist = F.prepare_polls(hist[hist["has_result"] == 1])
hist["race_id"] = (hist["year"].astype(str) + "_" + hist["state"] + "_" + hist["office"]
                   + hist["district"].radd("-").where(hist["district"] != "", ""))
ne = dict(natl_env_hist())
ne[2026] = ne_val
cand = F.build_candidate_table(d, build_macro(cycles=[2026]), ne, F.load_fundamentals(),
                               house=F.compute_house_effect(hist, sorted(hist["year"].unique())),
                               fec=F.load_fec(extended=True), bias_priors=F.compute_bias_priors(hist),
                               candidate_bios=F.load_candidate_bios(), primary_results=F.load_primary_results())
cand = P.patch_redistricted_priors(cand)
meta = json.load(open(os.path.join(root, "data", "model_features.json")))
m = xgb.XGBClassifier()
m.load_model(sys.argv[5] if len(sys.argv) > 5 else os.path.join(root, "data", "model_xgb.json"))
cand["win_prob"] = m.predict_proba(cand.reindex(columns=meta["features"]))[:, 1]
cand["win_prob_norm"] = cand["win_prob"] / cand.groupby("race_id")["win_prob"].transform("sum")
surveys = d.groupby("race_id").apply(lambda g: g.groupby(["pollster", "end_date"]).ngroups, include_groups=False)
cand["n_surveys"] = cand["race_id"].map(surveys).fillna(0).astype(int)
cols = ["race_id", "candidate", "party", "cand_key", "n_polls", "n_surveys", "poll_avg", "poll_lead",
        "poll_last", "n_polls_dpoll", "n_polls_rpoll", "bio_office_level", "win_prob", "win_prob_norm"]
cand[[c for c in cols if c in cand.columns]].to_csv(out_csv, index=False)
print(f"wrote {out_csv}: {cand['race_id'].nunique()} races, {len(d)} poll rows")
