"""scripts/build_silver.py (2026-10-30): docs/silver_data.js must match the hand-filled CSV, and the
parser must normalize rows and reject typos rather than publish them."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.build_silver import build, render, OUT  # noqa: E402


def test_published_file_matches_the_csv():
    assert OUT.read_text(encoding="utf-8") == render(build()), "re-run py scripts/build_silver.py"


def test_rows_are_normalized(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("race_id,dem,rep,ind,as_of\n"
                 "2026-SEN-MI,62,38,,2026-10-29\n"
                 "2026-GOV-AZ,0.55,,,2026-10-28\n"
                 "2026-SEN-NE,,0.6,0.4,\n", encoding="utf-8")
    d = build(p)
    assert d["as_of"] == "2026-10-29"
    assert d["races"]["2026-SEN-MI"] == {"D": 0.62, "R": 0.38}
    assert d["races"]["2026-GOV-AZ"] == {"D": 0.55, "R": 0.45}
    assert d["races"]["2026-SEN-NE"] == {"I": 0.4, "R": 0.6}


@pytest.mark.parametrize("row", ["2026-SEN-XX,50,50,,", "2026-SEN-MI,,,,", "2026-SEN-MI,150,10,,"])
def test_bad_rows_fail(tmp_path, row):
    p = tmp_path / "s.csv"
    p.write_text("race_id,dem,rep,ind,as_of\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        build(p)
