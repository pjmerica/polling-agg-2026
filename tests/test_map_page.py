"""docs/map.html (2026-10-23): the state shapes and House tile grid in docs/us_map_geo.js
(scripts/build_map_geo.py) cover every state that has a race, so no race can drop off the map."""
import json
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"


def load(name, prefix):
    text = (DOCS / name).read_text(encoding="utf-8")
    assert text.startswith(prefix)
    return json.loads(text[len(prefix):].rstrip().rstrip(";"))


def test_every_race_state_is_on_the_map():
    geo = load("us_map_geo.js", "const US_MAP = ")
    races = load("data.js", "const RACES = ")
    assert len(geo["states"]) == 51
    assert all(s["d"].startswith("M") and s["d"].endswith("Z") for s in geo["states"].values())
    states = {r["state_abbrev"] for r in races}
    assert states <= set(geo["states"]), states - set(geo["states"])
    house = {r["state_abbrev"] for r in races if r["office"] == "H"}
    assert house <= set(geo["tiles"]), house - set(geo["tiles"])
    # tiles never overlap
    assert len({tuple(v) for v in geo["tiles"].values()}) == len(geo["tiles"])
