"""Regression cases for fake-arb incidents in the Arb Scanner tab.

Run: py -m pytest tests/
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.election_shapes import party_win_side
from scripts import arb_scanner as arb


# ── party-win legs: allowlist, not "mentions democrat" (2026-09-24) ────────

@pytest.mark.parametrize("title,side", [
    ("Will the Democratic Party win the WI-03 House seat?", "dem"),
    ("Will the Democrats win the Maine Senate race in 2026?", "dem"),
    ("Will a Democrat win the House race for WI-3?", "dem"),              # Kalshi raw
    ("Will Democratics win the Senate race in Alaska?", "dem"),           # Kalshi raw
    ("Will the Republican party win the governorship in Nevada", "rep"),  # Kalshi raw
])
def test_party_win_accepts_plain_winner(title, side):
    assert party_win_side(title) == side


@pytest.mark.parametrize("title", [
    # All three "guaranteed" arbs on 2026-09-24 (56-81%) were these:
    "Will the Republican Party candidate win the 2026 Rhode Island Senate election by 45% or more?",
    "Will the Democratic Party candidate win the 2026 New Mexico Senate election by 0%-3%?",
    "Will Democrats win the Alaska Governor election and Republicans win the Alaska Senate election?",
    "Will the Kansas 2026 Senate race be within 5%?",
])
def test_party_win_rejects_derivatives(title):
    assert party_win_side(title) is None


def test_polymarket_loader_ignores_margin_buckets(tmp_path, monkeypatch):
    rows = [
        # The margin bucket has far more liquidity — it used to win.
        {"race_id": "2026-SEN-RI", "question": "Will the Democratic Party candidate win the 2026 Rhode Island Senate election by 45% or more?",
         "implied_prob": 0.02, "liquidity": 90000, "volume": 1, "event_slug": "ri-mov", "market_slug": "ri-mov-45"},
        {"race_id": "2026-SEN-RI", "question": "Will the Democrats win the Rhode Island Senate race in 2026?",
         "implied_prob": 0.96, "liquidity": 5000, "volume": 1, "event_slug": "ri-winner", "market_slug": "ri-dem"},
        {"race_id": "2026-SEN-RI", "question": "Will the Republicans win the Rhode Island Senate race in 2026?",
         "implied_prob": 0.04, "liquidity": 5000, "volume": 1, "event_slug": "ri-winner", "market_slug": "ri-rep"},
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "polymarket_markets.csv", index=False)
    monkeypatch.setattr(arb, "RAW", tmp_path)
    out = arb.load_polymarket_general()
    assert len(out) == 1
    r = out.iloc[0]
    assert r["pm_dem"] == 0.96
    assert r["pm_url"] == "https://polymarket.com/event/ri-winner/ri-dem"


# ── Kalshi ticker/title state disagreement ────────────────────────────────

@pytest.mark.parametrize("race_id,title,ok", [
    ("2026-SEN-LA", "Kentucky Senate winner? Will Republicans win the Senate race in Kentucky?", False),
    ("2026-SEN-LA", "Louisiana Senate winner? Will Republicans win the Senate race in Louisiana?", True),
    ("2026-H-WI-03", "WI-03 House winner? Will Democratic win the House race for WI-3?", True),
])
def test_kalshi_race_id_must_match_title_state(race_id, title, ok):
    assert arb.race_id_agrees_with_title(race_id, title) is ok


# ── stake sizing must hedge ───────────────────────────────────────────────

def test_stakes_buy_equal_contracts():
    """YES 1.2c on B + NO 4c on A. The old 1/price split put $77 on the
    1.2c leg — 6,400 vs 575 contracts."""
    r = arb.compute_arb(0.96, 0.012, 0.02, 0.02,
                        bid_a=0.95, ask_a=0.97, bid_b=0.011, ask_b=0.012,
                        no_ask_a=0.04, no_ask_a_real=True,
                        no_ask_b=0.99, no_ask_b_real=True)
    assert r["arb_type"] == "guaranteed" and r["yes_leg"] == "b"
    assert abs(r["stake_a_dollars"] / 0.04 - r["stake_b_dollars"] / 0.012) / (r["stake_a_dollars"] / 0.04) < 0.01
    assert abs(r["stake_a_dollars"] + r["stake_b_dollars"] - 100) < 0.02
    cost = 0.052
    assert abs(r["profit_dollars"] - 100 * (1 - cost - 0.04) / cost) < 0.05


# ── links ─────────────────────────────────────────────────────────────────

def test_kalshi_url_pins_event():
    assert arb.kalshi_url("HOUSEWI3", "HOUSEWI3-26") == "https://kalshi.com/markets/housewi3/housewi3-26"
    assert arb.kalshi_url("HOUSEWI3") == "https://kalshi.com/markets/housewi3"


def test_polymarket_url_deep_links_market():
    assert arb.polymarket_url("ev", "mk") == "https://polymarket.com/event/ev/mk"
    assert arb.polymarket_url("ev", float("nan")) == "https://polymarket.com/event/ev"


# ── real per-leg fees (2026-09-24) ─────────────────────────────────────────

from utils.fees import leg_fee, kalshi_spec, polymarket_spec, predictit_spec, FEE_SAFETY_MARGIN


def test_fee_formulas():
    assert abs(100 * leg_fee("polymarket", polymarket_spec(0.07), 0.5) - 1.75) < 1e-9   # Polymarket docs example
    assert abs(leg_fee("kalshi", kalshi_spec(1), 0.5) - 0.0175) < 1e-9
    assert abs(leg_fee("predictit", predictit_spec(), 0.4) - 0.11) < 1e-9
    assert leg_fee("kalshi", None, 0.5) == 0.02                                          # unknown -> flat


def test_compute_arb_real_fees_clear_a_thin_basket():
    kw = dict(bid_a=0.41, ask_a=0.43, bid_b=0.55, ask_b=0.57,
              no_ask_a=0.58, no_ask_a_real=True, no_ask_b=0.53, no_ask_b_real=True)
    flat = arb.compute_arb(0.43, 0.56, 0.02, 0.02, **kw)
    real = arb.compute_arb(0.43, 0.56, 0.02, 0.02, **kw,
                           leg_fees=("kalshi", kalshi_spec(1), "polymarket", polymarket_spec(0.04)))
    assert flat["arb_type"] == "one-sided"            # 4c gross vs 4c flat fees
    assert real["arb_type"] == "guaranteed"           # real fees ~2.2c + 0.5c margin
    fees = 0.07 * 0.43 * 0.57 + 0.04 * 0.53 * 0.47 + FEE_SAFETY_MARGIN
    assert abs(real["guaranteed_return_pct"] - 100 * (0.04 - fees) / 0.96) < 0.01


# 2026-09-25: other cycles and Mexico's Baja California got 2026 US ids.
from scrapers.polymarket import infer_race_id as pm_race_id


@pytest.mark.parametrize("q, rid", [
    ("Will the Democrats win the Kentucky governor race in 2027?", None),
    ("Will Juan Carlos Hank win the 2027 Baja California Governor Election?", None),
    ("Will Roxana Higuera win the 2027 Baja California Sur Governor Election?", None),
    ("Will the Democrats win the Maine Senate race in 2026?", "2026-SEN-ME"),
])
def test_polymarket_race_id_rejects_other_cycles(q, rid):
    assert pm_race_id(q) == rid


# 2026-09-25: other offices and multi-state combos are not party-win legs.
@pytest.mark.parametrize("title", [
    "Will the Democratic Party candidate win the 2026 Vermont Lieutenant Governor election?",
    "Will the Democratic party win the Lt. Gov race in Alabama?",
    "Will the Democratic party win the Attorney General race in Arizona?",
    "Will the Democrats win the Arizona Secretary of State race in 2026?",
    "Will Democrats win the Texas, Michigan, and Maine Senate seats?",
    "Will Democrats win the governorships of Pennsylvania, Michigan, Wisconsin, Georgia, Arizona, AND Nevada?",
])
def test_party_win_rejects_other_offices_and_combos(title):
    assert party_win_side(title) is None


def test_party_win_west_virginia_is_one_state():
    assert party_win_side("Will the Democrats win the West Virginia Senate race in 2026?") == "dem"


def test_polymarket_loader_keeps_every_equivalent_dem_market(tmp_path, monkeypatch):
    # 2026-09-25: the winner event and the margin event both list a plain
    # "Democratic candidate wins" market; both must be paired (AR-Gov traded
    # at 2.7c vs 0.25c and the liquidity pick flipped between runs).
    rows = [
        {"race_id": "2026-GOV-AR", "question": "Will the Democrats win the Arkansas governor race in 2026?",
         "implied_prob": 0.027, "liquidity": 13000, "volume": 1, "event_slug": "ar-winner", "market_slug": "ar-dem"},
        {"race_id": "2026-GOV-AR", "question": "Will the Democratic Party candidate win the 2026 Arkansas gubernatorial election?",
         "implied_prob": 0.0025, "liquidity": 13100, "volume": 1, "event_slug": "ar-mov", "market_slug": "ar-mov-dem"},
        {"race_id": "2026-GOV-AR", "question": "Will the Republicans win the Arkansas governor race in 2026?",
         "implied_prob": 0.97, "liquidity": 13000, "volume": 1, "event_slug": "ar-winner", "market_slug": "ar-rep"},
    ]
    pd.DataFrame(rows).to_csv(tmp_path / "polymarket_markets.csv", index=False)
    monkeypatch.setattr(arb, "RAW", tmp_path)
    out = arb.load_polymarket_general()
    assert sorted(out["pm_dem"]) == [0.0025, 0.027]
