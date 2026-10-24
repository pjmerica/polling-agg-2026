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


def test_house_district_map_matches_the_ballot():
    """docs/us_house_2026_geo.js (scripts/build_house_map.py, 2026-10-23): one shape per House race on
    the 2026 lines, the nine redrawn states flagged, and an ACS profile for every district."""
    geo = load("us_house_2026_geo.js", "const US_HOUSE = ")
    races = load("data.js", "const RACES = ")
    house = {f"{r['state_abbrev']}-{int(r['district']):02d}" for r in races if r["office"] == "H"}
    assert set(geo["districts"]) == house, set(geo["districts"]) ^ house
    assert len(geo["districts"]) == 435
    redrawn = {k[:2] for k, d in geo["districts"].items() if d["rd"]}
    assert redrawn == {"TX", "CA", "NC", "OH", "UT", "FL", "TN", "LA", "AL"}, redrawn
    assert sum(d["rd"] for d in geo["districts"].values()) == 173
    for k, d in geo["districts"].items():
        assert d["d"].startswith("M") and d["d"].endswith("z"), k
        assert 0 <= d["lx"] <= 975 and 0 <= d["ly"] <= 610, k
        pop, *shares, inc = d["demo"]["now"]
        assert pop > 500_000 and inc > 20_000, k
        assert all(0 <= s <= 1 for s in shares) and sum(shares[:4]) <= 1.001, k
        assert ("old" in d["demo"]) == bool(d["rd"]), k
    assert len(geo["states"]) == 50 and len(geo["boxes"]) == 50
