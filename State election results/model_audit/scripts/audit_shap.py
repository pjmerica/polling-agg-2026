"""Per-feature contributions (log-odds, XGBoost pred_contribs) of the WIN model for the
competitive races, from the candidate table dumped by audit_model_inputs.py.

    py -X utf8 audit_shap.py <out_dir>
"""
import json
import os
import sys

import pandas as pd
import xgboost as xgb

MODEL = r"C:\Users\pjmer\Documents\Polling prediction model"
out_dir = sys.argv[1]
meta = json.load(open(os.path.join(MODEL, "data", "model_features.json")))
feats = meta["features"]
m = xgb.XGBClassifier()
m.load_model(os.path.join(MODEL, "data", "model_xgb.json"))
f = pd.read_csv(os.path.join(out_dir, "features.csv"))
f = f[f["party"].isin(["DEM", "REP"])].reset_index(drop=True)
X = f.reindex(columns=feats)
contrib = m.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)
c = pd.DataFrame(contrib, columns=feats + ["bias"])
c.insert(0, "candidate", f["candidate"])
c.insert(0, "race_id", f["race_id"])
c.to_csv(os.path.join(out_dir, "shap_win.csv"), index=False)
# group macro columns
macro = [x for x in feats if any(k in x for k in ("fed_funds", "generic_ballot", "inflation", "unemp", "gdp",
                                                    "sentiment", "payroll", "claims", "approval", "gas", "sp500",
                                                    "umcsent", "cpi", "macro"))]
for (rid, cand), row in c.set_index(["race_id", "candidate"]).iterrows():
    s = row.drop("bias")
    grp = {"macro (all %d cols)" % len(macro): s[macro].sum()}
    rest = s.drop(macro)
    top = rest.reindex(rest.abs().sort_values(ascending=False).index)[:12]
    print(f"\n{rid} | {cand} | total logit {row.sum():+.2f} (bias {row['bias']:+.2f}, macro {grp[list(grp)[0]]:+.2f})")
    print("   " + "; ".join(f"{k} {v:+.2f} (={f.loc[(f.race_id == rid) & (f.candidate == cand), k].values[0]:.3g})"
                              for k, v in top.items()))
