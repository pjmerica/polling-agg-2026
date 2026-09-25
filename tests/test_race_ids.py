"""Regression cases for race_id / race-list errors (2026-09-25 audit).

Run: py -m pytest tests/
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.nytimes import infer_race_id
from utils.races import GOVERNOR_RACES_2026, RACE_BY_ID, SENATE_RACES_2026


# ── NYT race_id year comes from the poll's cycle, not a hardcoded 2026 ─────
# The feed carries 2025 NJ/VA-Gov and 2028 PA-Sen/NC-Gov polls. Hardcoding 2026 made
# the model score two races decided in Nov 2025 as live, and invented a 2026 PA-Sen race.

@pytest.mark.parametrize("office,state,cycle,seat,want", [
    ("governor", "NJ", 2025, None, "2025-GOV-NJ"),
    ("governor", "VA", 2025, None, "2025-GOV-VA"),
    ("senate", "PA", 2028, None, "2028-SEN-PA"),
    ("governor", "NC", 2028, None, "2028-GOV-NC"),
    ("house", "TX", 2025, 18, "2025-H-TX-18"),       # the Nov 2025 special, not the 2026 seat
    ("house", "TX", 2026, 18, "2026-H-TX-18"),
    ("senate", "FL", 2026, None, "2026-SEN-FL-S"),   # 2026 specials unchanged
    ("senate", "OH", 2026, None, "2026-SEN-OH-S"),
    ("senate", "MI", None, None, "2026-SEN-MI"),     # no cycle -> 2026
])
def test_nyt_race_id_uses_poll_cycle(office, state, cycle, seat, want):
    row = pd.Series({"state": state, "cycle": cycle, "seat_number": seat})
    assert infer_race_id(row, office) == want


# ── the canonical race list is the real 2026 ballot ────────────────────────

def test_race_list_counts():
    assert len(SENATE_RACES_2026) == 35      # 33 Class II + FL and OH specials
    assert len(GOVERNOR_RACES_2026) == 36


@pytest.mark.parametrize("race_id", [
    "2026-SEN-HI", "2026-SEN-WA",                  # Class III (2028)
    "2026-GOV-NJ", "2026-GOV-VA",                  # held Nov 2025
    "2026-GOV-KY", "2026-GOV-MS",                  # 2027
    "2026-GOV-MO", "2026-GOV-NC",                  # 2028
])
def test_off_cycle_races_absent(race_id):
    assert race_id not in RACE_BY_ID
