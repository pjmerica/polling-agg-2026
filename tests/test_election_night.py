"""docs/election-night.html and its county data, docs/election_night_counties.js (built by
"State election results/scripts/build_election_night.py", 2026-10-23): every race's counties add up
to the whole state, each race has its interactive table on the page, and no template token is left."""
import json
import math
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
PREFIX = "const ELECTION_NIGHT = "


def load():
    text = (DOCS / "election_night_counties.js").read_text(encoding="utf-8")
    assert text.startswith(PREFIX)
    return json.loads(text[len(PREFIX):].rstrip().rstrip(";"))


def test_counties_cover_each_state():
    races = load()["races"]
    assert len(races) >= 10
    for r in races:
        cs = r["counties"]
        assert cs, r["id"]
        assert abs(sum(c["w"] for c in cs) - 1) < 1e-3, r["id"]
        assert len({c["f"] for c in cs}) == len(cs), r["id"]
        assert all(math.isfinite(c["L"]) and c["w"] > 0 for c in cs), r["id"]
        # early/mail splits come as a set
        assert all(("a" in c) == ("la" in c) == ("le" in c) for c in cs), r["id"]


def test_page_has_a_table_for_every_race():
    page = (DOCS / "election-night.html").read_text(encoding="utf-8")
    assert "{{" not in page
    for r in load()["races"]:
        assert f'id="ct-{r["id"]}"' in page, r["id"]
