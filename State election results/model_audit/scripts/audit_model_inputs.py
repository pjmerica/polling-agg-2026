"""Dump exactly what the model sees for the competitive races: every poll row that survives
predict.py's loading/filtering, and every feature value in the candidate table.

    py -X utf8 audit_model_inputs.py <raw_dir> <out_dir> <natl_env>
"""
import os
import sys

MODEL = r"C:\Users\pjmer\Documents\Polling prediction model"
sys.path.insert(0, os.path.join(MODEL, "src"))
sys.path.insert(0, os.path.join(MODEL, "pipeline", "fetch"))
sys.path.insert(0, MODEL)

import json  # noqa: E402
import pandas as pd  # noqa: E402

import features as F  # noqa: E402
import predict as P  # noqa: E402
from cycles import natl_env as natl_env_hist  # noqa: E402
from macro_features import build_macro  # noqa: E402

RACES = ["2026_AK_Senate", "2026_GA_Governor", "2026_OH_Governor", "2026_OH_Senate-S",
         "2026_KS_Senate", "2026_TX_Senate", "2026_NE_Senate", "2026_ME_Senate",
         "2026_IA_Senate", "2026_MI_Senate"]


def main():
    raw_dir, out_dir, ne_val = sys.argv[1], sys.argv[2], float(sys.argv[3])
    os.makedirs(out_dir, exist_ok=True)
    polls = [os.path.join(raw_dir, "nyt_polls.csv"), os.path.join(raw_dir, "wikipedia_polls.csv")]
    d = P.load_agg_polls(polls, 2026)
    print("race_ids present:", sorted(set(d["race_id"]) & set(RACES)))
    keep_cols = [c for c in ["race_id", "end_date", "pollster", "candidate", "party_std", "display_party",
                             "pct", "partisan", "sample_size", "question_id", "poll_id"] if c in d.columns]
    sub = d[d["race_id"].isin(RACES)].sort_values(["race_id", "end_date", "pollster", "candidate"])
    sub[keep_cols].to_csv(os.path.join(out_dir, "polls_used.csv"), index=False)

    with open(os.path.join(MODEL, "data", "model_features.json")) as f:
        meta = json.load(f)
    hist = pd.read_csv(os.path.join(MODEL, "polls_long_with_results.csv"), low_memory=False)
    hist = F.prepare_polls(hist[hist["has_result"] == 1])
    hist["race_id"] = (hist["year"].astype(str) + "_" + hist["state"] + "_" + hist["office"]
                       + hist["district"].radd("-").where(hist["district"] != "", ""))
    house = F.compute_house_effect(hist, sorted(hist["year"].unique()))
    bias = F.compute_bias_priors(hist)
    macro = build_macro(cycles=[2026])
    ne = dict(natl_env_hist())
    ne[2026] = ne_val
    cand = F.build_candidate_table(d, macro, ne, F.load_fundamentals(), house=house,
                                   fec=F.load_fec(extended=True), bias_priors=bias,
                                   candidate_bios=F.load_candidate_bios(),
                                   primary_results=F.load_primary_results())
    cand = P.patch_redistricted_priors(cand)
    feats = meta["features"]
    c = cand[cand["race_id"].isin(RACES)]
    # one row per candidate, every model feature plus identifying columns
    ident = [x for x in ["race_id", "candidate", "party", "cand_key", "n_polls", "poll_avg", "poll_lead"]
             if x in c.columns]
    c[ident + [f for f in feats if f not in ident]].to_csv(os.path.join(out_dir, "features.csv"), index=False)
    import xgboost as xgb
    model = xgb.XGBClassifier()
    model.load_model(os.path.join(MODEL, "data", "model_xgb.json"))
    c = c.copy()
    c["win_prob"] = model.predict_proba(c.reindex(columns=feats))[:, 1]
    c["win_prob_norm"] = c["win_prob"] / c.groupby("race_id")["win_prob"].transform("sum")
    print(c[["race_id", "candidate", "party", "n_polls", "poll_avg", "poll_lead", "win_prob_norm"]]
          .sort_values(["race_id", "win_prob_norm"], ascending=[True, False]).to_string(index=False))
    print(f"\n{len(feats)} features; saved polls_used.csv ({len(sub)} rows) and features.csv")


if __name__ == "__main__":
    main()
