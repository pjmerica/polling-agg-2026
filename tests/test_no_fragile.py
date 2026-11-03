"""The per-race Fragile flag and the "If the polls are off" stress table are gone from every page
(user call, 2026-11-02). The Senate and House control odds carry a note instead: a polling miss
moves races together. Fails if either comes back."""
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
PAGES = ["map.html", "predictions.html", "index.html"]


def test_no_fragile_flag_or_stress_table():
    for name in PAGES:
        t = (DOCS / name).read_text(encoding="utf-8")
        for bad in (">Fragile<", "FRAGILE<", "Fragile:", "polls are' : '", "polls are off</h4>", "national mood is' : '"):
            assert bad not in t, (name, bad)


def test_chambers_note_correlated_misses():
    for name in ("map.html", "predictions.html"):
        assert "Races move together: when polls miss" in (DOCS / name).read_text(encoding="utf-8"), name
