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
