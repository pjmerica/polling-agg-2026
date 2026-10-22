"""Win model: how much do the hyperparameters alone move things? Runs the win notebook's own data
build (every code cell before the tuning cell), then scores two parameter sets on the same data:
tune-cycle CV (what the tuner compares), the expanding-window 2018-2024 eval (the honest numbers),
and the slice that moved most in 2026 - House candidates with thin polling and a small lead. Saves a
production fit of each set so snapshot_predict.py can score the 2026 slate with it.

    py -X utf8 compare_params.py <model_root> <out_dir>
"""
import json
import os
import sys

root, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
os.environ.setdefault("MPLBACKEND", "Agg")
os.chdir(root)
sys.path.insert(0, root)

nb = json.load(open(os.path.join("models", "poll", "model.ipynb"), encoding="utf-8"))
ns = {}
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] != "code":
        continue
    src = "".join(c["source"])
    if "GRID = dict(" in src:          # stop at the tuning cell
        break
    exec(compile(src, f"<cell {i}>", "exec"), ns)

np, pd, xgb = ns["np"], ns["pd"], ns["xgb"]
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score  # noqa: E402

FOLDS, BASE, FEATURES = ns["FOLDS"], ns["BASE"], ns["FEATURES"]
TUNE, EVAL = ns["TUNE_CYCLES"], ns["EVAL_CYCLES"]
PARAMS = {
    "depth1 (shipped before)": dict(max_depth=1, learning_rate=0.05, n_estimators=300, min_child_weight=8,
                                    subsample=0.8, colsample_bytree=1.0, reg_lambda=5, reg_alpha=1),
    "depth2 (picked by the retune)": dict(max_depth=2, learning_rate=0.02, n_estimators=300, min_child_weight=15,
                                          subsample=1.0, colsample_bytree=1.0, reg_lambda=1, reg_alpha=1),
}


def model(p):
    return xgb.XGBClassifier(eval_metric="logloss", random_state=42, **p)


preds = {}
rows = []
for name, p in PARAMS.items():
    auc, brier = ns["cv_auc_brier"](FEATURES, p, TUNE)
    te_all = []
    for ty in EVAL:
        c = FOLDS[ty]
        tr, te = c[c["year"] < ty], c[c["year"] == ty].copy()
        m = model(p).fit(tr[FEATURES], tr["won"].astype(int))
        te["p"] = m.predict_proba(te[FEATURES])[:, 1]
        te_all.append(te)
    te = pd.concat(te_all)
    preds[name] = te
    m = model(p).fit(BASE[FEATURES], BASE["won"].astype(int))
    slug = name.split()[0]
    m.save_model(os.path.join(out_dir, f"model_xgb_{slug}.json"))
    rows.append((name, auc, brier, te))

# ensemble = plain average of the two
te_e = preds[rows[0][0]].copy()
te_e["p"] = (preds[rows[0][0]]["p"].values + preds[rows[1][0]]["p"].values) / 2
rows.append(("average of the two", np.nan, np.nan, te_e))


def race_acc(te):
    return te.loc[te.groupby("race_id")["p"].idxmax(), "won"].mean()


def stats(te):
    y = te["won"].astype(int)
    return dict(n=len(te), Brier=brier_score_loss(y, te["p"]), LogLoss=log_loss(y, te["p"].clip(1e-6, 1 - 1e-6)),
                AUC=roc_auc_score(y, te["p"]) if y.nunique() > 1 else np.nan, race_acc=race_acc(te))


print("\n### Tune-cycle CV (1998-2016 leave-one-cycle-out; the tuner picks the higher AUC)\n")
print("| Settings | AUC | Brier |\n|---|---|---|")
for name, auc, brier, _ in rows[:2]:
    print(f"| {name} | {auc:.4f} | {brier:.4f} |")

print("\n### Honest eval 2018-2024 (expanding window, all offices)\n")
print("| Settings | Brier | Log loss | AUC | Races called right |\n|---|---|---|---|---|")
for name, _, _, te in rows:
    s = stats(te)
    print(f"| {name} | {s['Brier']:.4f} | {s['LogLoss']:.4f} | {s['AUC']:.4f} | {s['race_acc']:.3f} |")

print("\n### Per cycle, Brier\n")
print("| Settings | " + " | ".join(str(y) for y in EVAL) + " |\n|---|" + "---|" * len(EVAL))
for name, _, _, te in rows:
    print(f"| {name} | " + " | ".join(f"{brier_score_loss(g['won'].astype(int), g['p']):.4f}"
                                      for _, g in te.groupby('year')) + " |")


def slice_table(title, mask_fn):
    print(f"\n### {title}\n")
    print("| Settings | Candidates | Mean predicted | Actually won | Brier |\n|---|---|---|---|---|")
    for name, _, _, te in rows:
        s = te[mask_fn(te)]
        if not len(s):
            continue
        print(f"| {name} | {len(s)} | {s['p'].mean():.3f} | {s['won'].mean():.3f} | "
              f"{brier_score_loss(s['won'].astype(int), s['p']):.4f} |")


thin = lambda t: t["n_polls"] <= 3  # noqa: E731
slice_table("House, 1-3 polls, leading by 0-5 points",
            lambda t: (t["office"] == "House") & thin(t) & (t["poll_lead"] > 0) & (t["poll_lead"] <= 5))
slice_table("House, 1-3 polls, trailing by 0-5 points",
            lambda t: (t["office"] == "House") & thin(t) & (t["poll_lead"] < 0) & (t["poll_lead"] >= -5))
slice_table("House, 4+ polls, leading by 0-5 points",
            lambda t: (t["office"] == "House") & ~thin(t) & (t["poll_lead"] > 0) & (t["poll_lead"] <= 5))
slice_table("Senate/Governor, leading by 0-5 points",
            lambda t: (t["office"] != "House") & (t["poll_lead"] > 0) & (t["poll_lead"] <= 5))
slice_table("Democrats leading by 0-5 points, any office",
            lambda t: (t["party"] == "DEM") & (t["poll_lead"] > 0) & (t["poll_lead"] <= 5))
slice_table("Republicans leading by 0-5 points, any office",
            lambda t: (t["party"] == "REP") & (t["poll_lead"] > 0) & (t["poll_lead"] <= 5))
