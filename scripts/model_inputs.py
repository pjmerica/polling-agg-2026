"""Every input the forecast's models use -> data/processed/model_inputs_2026.json. 2026-11-01.

The per-race explainer (model_explanations_2026.json) carries only each race's ten strongest
inputs, so a reader could never see the whole list: 37 of the win model's 73 inputs never
appear in any race's top ten. This catalogues all of them for the forecast page's "Every input
the model uses" section and for the explainer's labels:

  models   the three models' input lists (model repo data/*_features.json): the polled win and
           margin models (73 each) and the no-polls model (32, the same list for its win and
           margin halves), with the cycles each was trained on
  inputs   every input once: plain-English label and definition (the model repo's FRIENDLY and
           DESC tables in src/explain_2026.py, the same text the explainer serves), a reading
           group, and how its value should be printed

The model repo is read, never written. It sits beside this repo both locally and in the
model-refresh workflow (which checks it out there), so build_forecast.py rebuilds this file on
every model refresh and commits it with the rest of data/processed. Anywhere the model repo is
absent (the market refresh, a fresh clone), the committed copy is used instead.

    python scripts/model_inputs.py        # rebuild from the model repo and print a summary
"""
import ast
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "data", "processed", "model_inputs_2026.json")
# sibling checkout, same layout as model-refresh.yml
MODEL_REPO = os.path.normpath(os.path.join(REPO, "..", "..", "Polling prediction model"))

MODELS = [  # (key, features file, what it is)
    ("polls_win", "race_win_model_features.json", "Win chance, races with polls"),
    ("polls_margin", "race_margin_model_features.json", "Margin, races with polls"),
    ("nopolls_win", "fundamentals_model_general_features.json", "Win chance, races without polls"),
    ("nopolls_margin", "fundamentals_margin_model_features.json", "Margin, races without polls"),
]

# Reading groups, in the order the page lists them. The first matching rule wins.
GROUPS = ["Polls", "Money", "The seat", "The candidates", "National mood", "Race setup"]
_GROUP_RULES = [
    ("Money", lambda f: f.startswith("fund_")),
    ("The seat", lambda f: f in {"prior_margin_cand", "pres_lean_cand", "dist_pres_lean_cand",
                                 "is_incumbent", "is_inc_party_race", "open_seat"}),
    ("The candidates", lambda f: f in {"is_personal_inc", "bio_office_level", "primary_margin",
                                       "opp_primary_margin", "primary_margin_diff",
                                       "primary_uncontested"}),
    ("National mood", lambda f: f in {"natl_env_cand", "is_president_party", "midterm_pres_party",
                                      "midterm_approval_cand"} or f.startswith("pres_")),
    ("Race setup", lambda f: f in {"is_dem", "is_rep", "is_senate", "is_gov", "n_cands"}),
    ("Polls", lambda f: True),   # every other input is built from the polls
]

# How the page prints a value (the explainer shows both candidates' values):
#   pct01 a 0-1 share as a percent    pct    already a percent       pts  signed points
#   pts01 a 0-1 difference as points  apts   unsigned points         yesno  0/1 flag
#   money_ln  log dollars as dollars  office the experience scale    int  count
#   days  a count of days             num    a plain number
_FMT = {
    "pct01": {"fund_share", "fund_indiv_pct", "fund_pac_pct", "fund_party_pct", "fund_self_pct",
              "fund_smalldollar_pct", "fund_cash_share", "fund_spend_share", "frac_polls_over50",
              "poll_share"},
    "pts01": {"fund_pac_rel"},
    "pct": {"poll_avg", "poll_last", "poll_last30", "poll_last7", "poll_avg_60", "poll_avg_dpoll",
            "poll_avg_rpoll", "poll_avg_npoll", "poll_avg_rw", "poll_adj", "undecided"},
    "apts": {"abs_gap", "poll_std", "poll_std_60", "pollster_sd", "margin_volatility"},
    "money_ln": {"fund_receipts_ln"},
    "office": {"bio_office_level"},
    "days": {"min_days"},
    "num": {"poll_momentum", "margin_trend"},
}


def group_of(f):
    return next(g for g, rule in _GROUP_RULES if rule(f))


def fmt_of(f):
    for k, names in _FMT.items():
        if f in names:
            return k
    if f.startswith(("is_", "open_seat", "tossup", "lead_changed", "primary_uncontested",
                     "midterm_pres_party")):
        return "yesno"
    if f.startswith(("n_", "race_total_polls", "avg_sample")):
        return "int"
    return "pts"


def _tables(src_path):
    """FRIENDLY and DESC from explain_2026.py, read as literals (the module itself imports
    xgboost and the model's loaders, which this repo does not need)."""
    tree = ast.parse(open(src_path, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("FRIENDLY", "DESC")):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out.get("FRIENDLY", {}), out.get("DESC", {})


def build():
    """Rebuild from the model repo. Returns the catalogue, or None if the repo is not there."""
    src = os.path.join(MODEL_REPO, "src", "explain_2026.py")
    if not os.path.exists(src):
        return None
    friendly, desc = _tables(src)
    models, order = {}, []
    for key, fname, what in MODELS:
        p = os.path.join(MODEL_REPO, "data", fname)
        if not os.path.exists(p):
            continue
        meta = json.load(open(p, encoding="utf-8"))
        feats = list(meta.get("features", []))
        models[key] = dict(label=what, features=feats,
                           trained_on=meta.get("trained_on_cycles") or [])
        order += [f for f in feats if f not in order]
    inputs = {f: dict(label=friendly.get(f, f.replace("_", " ")), desc=desc.get(f, ""),
                      group=group_of(f), fmt=fmt_of(f)) for f in order}
    return dict(groups=GROUPS, models=models, inputs=inputs)


def load(write=True):
    """The catalogue: rebuilt from the model repo when it is beside this one (and written to
    data/processed so the committed copy stays current), else the committed copy, else None."""
    cat = build()
    if cat is not None:
        if write:
            text = json.dumps(cat, indent=1, ensure_ascii=False) + "\n"
            old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
            if text != old:
                with open(OUT, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
        return cat
    if os.path.exists(OUT):
        return json.load(open(OUT, encoding="utf-8"))
    return None


if __name__ == "__main__":
    cat = load()
    if cat is None:
        raise SystemExit(f"model repo not found at {MODEL_REPO} and no {OUT}")
    print(f"wrote {OUT}")
    for k, m in cat["models"].items():
        print(f"  {k}: {len(m['features'])} inputs, trained on {m['trained_on'][:1]}..{m['trained_on'][-1:]}")
    from collections import Counter
    print("  groups:", dict(Counter(v["group"] for v in cat["inputs"].values())))
    missing = [f for f, v in cat["inputs"].items() if not v["desc"]]
    print("  without a definition:", missing or "none")
