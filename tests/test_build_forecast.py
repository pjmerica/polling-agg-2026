"""docs/forecast_data.js (forecast page) is built from the per-candidate model outputs, so
independents are real opponents - not dropped from a Dem/Rep sum (2026-10-08: the Model-vs-Markets
D/(D+R) number read CA-6 as 100% Dem because Kevin Kiley runs as an independent)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_forecast as B  # noqa: E402


def test_forecast_keeps_every_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "OUT", str(tmp_path / "forecast_data.js"))
    payload = B.build()
    races = payload["races"]
    assert races, "no races built"
    for r in races:
        assert r["cands"], r["id"]
        wins = [c["win"] for c in r["cands"] if c["win"] is not None]
        assert abs(sum(wins) - 1) < 0.02, (r["id"], sum(wins))
    text = (tmp_path / "forecast_data.js").read_text(encoding="utf-8")
    assert text.startswith("const FORECAST = ")
    json.loads(text[len("const FORECAST = "):].rstrip().rstrip(";"))
    ca6 = next((r for r in races if r["id"] == "2026_CA_House-6"), None)
    if ca6 is not None and any("Kiley" in c["name"] for c in ca6["cands"]):
        dem = sum(c["win"] for c in ca6["cands"] if c["party"] == "DEM")
        assert dem < 0.99, "independent opponent dropped from the race"


def test_same_party_race_has_no_market(tmp_path, monkeypatch):
    """California top-two D-v-D / R-v-R: the party market prices 'a Democrat wins' (~99%), not
    which one, so the forecast must not show it against either candidate (2026-10-20: CA-7 read
    'Markets: Vang 98%')."""
    monkeypatch.setattr(B, "OUT", str(tmp_path / "forecast_data.js"))
    for r in B.build()["races"]:
        c = r["cands"]
        if len(c) >= 2 and c[0]["party"] == c[1]["party"] and c[0]["party"] in ("DEM", "REP"):
            assert r["market"] is None, r["id"]


def test_every_ballot_race_has_a_model_number(tmp_path, monkeypatch):
    """Since 2026-10-23 every race on the ballot is scored: races no pollster covers come from the
    no-polls model (model_fundamentals_predictions_2026.csv, basis "fundamentals") with no margin
    and a note saying so, and no race appears twice. Since 2026-10-27 they carry the no-polls
    model's stress test (the national mood moved 3 and 6 points), summing to 1 like the base odds."""
    if not (ROOT / "data" / "processed" / "model_fundamentals_predictions_2026.csv").exists():
        return  # the model refresh has not written the no-polls file yet
    monkeypatch.setattr(B, "OUT", str(tmp_path / "forecast_data.js"))
    races = B.build()["races"]
    ids = [r["id"] for r in races]
    assert len(ids) == len(set(ids)), "a polled race was also added from the no-polls model"
    assert len(races) >= 500, len(races)   # 506 general-election races on the 2026 ballot
    fund = [r for r in races if r["basis"] == "fundamentals"]
    assert fund
    for r in fund:
        assert r["notes"][0] == B.NOTES["FUND"], r["id"]
        assert r["n_surveys"] == 0, r["id"]
        assert all(c["margin"] is None for c in r["cands"]), r["id"]
        for k in ("win_r3", "win_d3"):
            v = [c[k] for c in r["cands"] if c[k] is not None]
            assert not v or abs(sum(v) - 1) < 0.02, (r["id"], k)


def test_models_split_is_flagged(tmp_path, monkeypatch):
    """Audit item 3 (2026-10-27): where the margin model's favourite is not the win model's, the
    race carries `split` (the margin favourite) and a note, so the forecast page and map can mute
    the model-vs-market gap the way Model vs Markets does."""
    monkeypatch.setattr(B, "OUT", str(tmp_path / "forecast_data.js"))
    for r in B.build()["races"]:
        c = r["cands"]
        if r.get("basis") == "fundamentals" or any(x["margin"] is None for x in c) or len(c) < 2:
            assert not r.get("split"), r["id"]
            continue
        mfav = max(c, key=lambda x: x["margin"])["name"]
        if mfav != c[0]["name"]:
            assert r["split"] == mfav, r["id"]
            assert any(n.startswith("Models split") for n in r["notes"]), r["id"]
        else:
            assert r["split"] is None, r["id"]
