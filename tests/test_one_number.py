"""Audit item 2 (2026-10-27): every page shows the SAME model number for a race. The Model vs
Markets tab (docs/model_data.js), the forecast page and map (docs/forecast_data.js) and the
Dashboard tab (docs/data.js) all read the model repo's race-level win probabilities
(data/processed/model_predictions_2026.csv, win_prob_norm). Before this the tab used D/(D+R) of
each party's leading candidate and disagreed with the forecast page by the third-party share (and
by up to 15 pts where the per-candidate model's raw odds summed far from 1)."""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PRED = ROOT / "data" / "processed" / "model_predictions_2026.csv"
TOL = 0.0015      # the pages round to 4 decimals


def _js(name, var):
    text = (DOCS / name).read_text(encoding="utf-8")
    start = text.index(f"const {var} = ") + len(f"const {var} = ")
    return json.JSONDecoder().raw_decode(text[start:])[0]


@pytest.fixture(scope="module")
def preds():
    if not PRED.exists():
        pytest.skip("no model predictions in this checkout")
    return pd.read_csv(PRED)


@pytest.fixture(scope="module")
def dem_chance(preds):
    # the model's party (a Dem-slot independent such as Osborn is DEM here, IND on the pages)
    return preds[preds["party"] == "DEM"].groupby("race_id")["win_prob_norm"].sum()


def _same(a, b):
    return a is not None and b is not None and abs(a - b) <= TOL


def test_forecast_page_shows_the_published_odds(preds):
    want = {(r.race_id, r.candidate): r.win_prob_norm for r in preds.itertuples()}
    bad = [(r["id"], c["name"], c["win"], round(want[(r["id"], c["name"])], 4))
           for r in _js("forecast_data.js", "FORECAST")["races"] if r.get("basis") != "fundamentals"
           for c in r["cands"] if (r["id"], c["name"]) in want
           and not _same(c["win"], want[(r["id"], c["name"])])]
    assert not bad, f"forecast page differs from the published odds: {bad[:8]}"


def test_model_vs_markets_shows_the_published_odds(dem_chance):
    bad = [(r["race_id"], r["model_dem"], round(dem_chance.get(r["race_id"], 0.0), 4))
           for r in _js("model_data.js", "MODEL_COMPARE")["races"]
           if r.get("model_dem") is not None
           and not _same(r["model_dem"], dem_chance.get(r["race_id"], 0.0))]
    assert not bad, f"Model vs Markets differs from the published odds: {bad[:8]}"


def test_dashboard_shows_the_published_odds(preds, dem_chance):
    agg = {}
    for r in _js("forecast_data.js", "FORECAST")["races"]:
        agg[r["agg_id"]] = r["id"]
    polled = set(preds["race_id"])
    bad = []
    for d in _js("data.js", "RACES"):
        rid = agg.get(d.get("race_id"))
        p = d.get("model_dem_prob")
        if rid not in polled or p is None or d.get("prob_source") != "model":
            continue
        if not _same(p, dem_chance.get(rid, 0.0)):
            bad.append((d["race_id"], p, round(dem_chance.get(rid, 0.0), 4)))
    assert not bad, f"Dashboard differs from the published odds: {bad[:8]}"
