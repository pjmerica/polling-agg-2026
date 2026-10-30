"""analysis/margin_markets.py (2026-10-30): Polymarket margin ladders -> the market's median margin
for the map's Margin view. Republican brackets mirror to negative margins, open-ended brackets are
closed with the neighbouring width, broken or short ladders and first-round ladders are dropped."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.margin_markets import parse_ladders, summarize  # noqa: E402


def _df(rows, rid="2026-H-AZ-06", what="AZ-06 House election"):
    return pd.DataFrame([{"question": f"Will the {party} Party candidate win the 2026 {what} by {b}?",
                          "race_id": rid, "implied_prob": p, "volume": 100} for party, b, p in rows])


AZ6 = [("Democratic", "6% or more", 0.10), ("Democratic", "3%-6%", 0.25), ("Democratic", "0%-3%", 0.25),
       ("Republican", "0%-3%", 0.20), ("Republican", "3%-6%", 0.12), ("Republican", "6% or more", 0.08)]


def test_ladder_signed_toward_the_democrat():
    br = parse_ladders(_df(AZ6))["2026-H-AZ-06"]
    assert (None, -6.0, 0.08, 100.0) in br and (6.0, None, 0.10, 100.0) in br and (-3.0, -0.0, 0.20, 100.0) in br
    s = summarize(br)
    assert s["p_d"] == pytest.approx(0.60)
    # cumulative from the Republican end: 0.08 + 0.12 + 0.20 = 0.40, so the median sits in D 0-3
    assert 0 < s["m"] < 3 and s["m"] == pytest.approx(0.1 / 0.25 * 3, abs=0.01)
    assert s["top"][:2] in ([3.0, 6.0], [0.0, 3.0])
    assert s["lad"][0][3] == -1 and s["lad"][-1][3] == 1          # open ends flagged
    assert s["lad"][0][0] == -9.0 and s["lad"][-1][1] == 9.0      # closed with the 3-pt width
    assert s["vol"] == 600


def test_short_broken_and_first_round_ladders_dropped():
    assert summarize(parse_ladders(_df(AZ6[:3]))["2026-H-AZ-06"]) is None
    assert summarize(parse_ladders(_df([(a, b, p / 10) for a, b, p in AZ6]))["2026-H-AZ-06"]) is None
    assert parse_ladders(_df(AZ6, rid="2026-SEN-ME", what="Maine Senate election first round")) == {}
    assert parse_ladders(_df(AZ6, rid="2028-PRES")) == {}


ONE_SIDED = [("Republican", "0%-5%", 0.30), ("Republican", "5%-10%", 0.30), ("Republican", "10%-15%", 0.20),
             ("Republican", "15%-20%", 0.12), ("Republican", "20% or more", 0.08)]


def test_one_sided_ladder_takes_the_other_side_from_the_winner_market():
    br = parse_ladders(_df(ONE_SIDED, rid="2026-SEN-MS", what="Mississippi Senate election"))["2026-SEN-MS"]
    assert summarize(br) is None                                # no winner book: can't tell
    s = summarize(br, {"R": 0.87, "D": 0.13})
    assert s["p_d"] == pytest.approx(0.13)
    assert [x[3] for x in s["lad"]].count(2) == 1               # the unlisted Democratic side
    assert s["top"][3] != 2
    # from the Republican end: 0.08, 0.12, 0.2 of 0.87 ... the median lands in R 5-10, not R 10-15
    assert -10 < s["m"] < -5
    # KS-Sen 2026-10-10: Republican-only ladder but the winner market has the Democrat at 54%
    assert summarize(br, {"R": 0.465, "D": 0.535}) is None
