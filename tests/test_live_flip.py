"""Election night FLIP rule (Election night simulator/scripts/live_project.py, 2026-10-30).

A FLIP must be the 2024 test's kind of trade: v1 gives the side 45%+, the market sells it cheap (40c or
less) and the edge after fees is 5c+, with 20%+ counted. The earlier rule only checked the 45%, so the best
buy on a decided race (a 99c favourite at a -0.3c edge) was flagged. Replaying the 2024 snapshots
(county_market_2024.csv, Kalshi books) must flag only the three flips MARKET_CHECK.md describes."""
import sys
from pathlib import Path

import pandas as pd

SIM = Path(__file__).resolve().parent.parent / "Election night simulator"
sys.path.insert(0, str(SIM / "scripts"))
import live_project as lp  # noqa: E402


def _bt(p_win, ask_d, ask_r):
    spec = lp.kalshi_spec(1)
    books = {"kalshi": {"D": dict(ask=ask_d, spec=spec), "R": dict(ask=ask_r, spec=spec)}}
    return lp.best_trade(p_win, books)


def test_favourite_at_99c_is_not_a_flip():
    bt = _bt(0.003, 0.01, 0.99)          # v1 says R 99.7%, R sells at 99c
    assert bt[1] == "R"
    assert not lp.is_flip({"p_win": 0.003}, bt, 98.0)


def test_cheap_side_v1_rates_near_even_is_a_flip():
    bt = _bt(0.55, 0.15, 0.86)           # Slotkin, Michigan 2024: 15c, v1 55%
    assert bt[1] == "D"
    assert lp.is_flip({"p_win": 0.55}, bt, 62.0)
    assert not lp.is_flip({"p_win": 0.55}, bt, 15.0)     # too early in the count
    assert not lp.is_flip(None, bt, 62.0)                # v0 only


def test_2024_replay_flags_only_the_three_flips():
    d = pd.read_csv(SIM / "data" / "processed" / "county_market_2024.csv").dropna(subset=["k_bid", "k_ask"])
    flagged = []
    for r in d.itertuples():
        bt = _bt(r.p_v1, r.k_ask, 1 - r.k_bid)
        if lp.is_flip({"p_win": r.p_v1}, bt, r.counted):
            flagged.append((r.race, bt[1]))
    assert len(flagged) == 3, flagged
    assert all(race in ("MI-Senate", "NV-Senate") for race, _ in flagged), flagged
