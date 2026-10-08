"""Regression tests for scrapers/wikipedia_polls.py stage/party/question parsing (2026-10-07).

Wikipedia's 'Post-primary endorsements' sub-heading sits inside the General election section,
and the scraper used to read 'primary' in it and tag every general poll table after it as a
primary poll (3,000+ rows; VA-Sen Warner v Mizusawa and NC-11 Balkcom v Ager never reached the
model). Party context also leaked from an 'Independents' heading into the general section, and
separate matchup tables from one poll shared a single question_id.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scrapers"))
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup  # noqa: E402

import wikipedia_polls as W  # noqa: E402


def test_post_primary_heading_is_not_a_stage():
    assert W.infer_section_context("Post-primary endorsements") == ("", "")
    assert W.infer_section_context("Eliminated in primary") == ("", "")
    assert W.infer_section_context("General election") == ("general", "")
    assert W.infer_section_context("Republican primary") == ("primary", "REP")
    assert W.infer_section_context("Democratic primary runoff") == ("primary runoff", "DEM")


_TABLE = """<table class="wikitable"><tr><th>Poll source</th><th>Date(s) administered</th>
<th>Sample size</th><th>Margin of error</th><th>{a} (D)</th><th>{b} (R)</th></tr>
<tr><td>Acme Polling</td><td>June 10–16, 2026</td><td>600 (LV)</td><td>± 4%</td>
<td>51%</td><td>{pct}%</td></tr></table>"""


def _page(*sections):
    return BeautifulSoup("".join(sections), "html.parser")


def test_general_tables_after_post_primary_heading_stay_general(monkeypatch):
    html = ("<h2>Republican primary</h2>"
            "<h2>Independents</h2>"
            "<h2>General election</h2><h4>Post-primary endorsements</h4><h3>Polling</h3>"
            + _TABLE.format(a="Mark Warner", b="Bert Mizusawa", pct=33)
            + _TABLE.format(a="Mark Warner", b="Kim Farington", pct=31))
    monkeypatch.setattr(W, "fetch_page", lambda url: html)
    rows = W._scrape_state_race("https://example.org", "2026-SEN-VA")
    assert rows, "no rows parsed"
    assert {r["stage"] for r in rows} == {"general"}
    # party comes from the (D)/(R) annotations, never the leaked 'Independents' context
    assert {r["party"] for r in rows} == {"DEM", "REP"}
    # two matchup tables from one poll are two questions; Warner keeps both numbers
    assert len({r["question_id"] for r in rows}) == 2
    assert sum(r["candidate"] == "Mark Warner" for r in rows) == 2
