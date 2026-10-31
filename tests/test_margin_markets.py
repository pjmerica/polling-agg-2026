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


# ---------- Kalshi thresholds (2026-10-30): "margin of victory for Democrats ... at least N points" ----------
from analysis.margin_markets import kalshi_margins, kalshi_race_id, summarize_kalshi  # noqa: E402
from analysis.margin_markets import _bracket_race as KALSHI_BRACKET_EVENT_OK  # noqa: E402


def test_kalshi_two_sided_thresholds():
    # S(x) = P(margin >= x): R 5+ .10 -> S(-5) .90, R 2+ .25 -> S(-2) .75, then D 1+ .60, 4+ .35, 7+ .15
    s = summarize_kalshi({"D": [(1, .60), (4, .35), (7, .15)], "R": [(2, .25), (5, .10)]})
    assert s["med"] == pytest.approx(1 + 3 * (.60 - .5) / (.60 - .35), abs=0.01)  # 2.2, between D 1+ and 4+
    # the published number: each 3-pt stretch at its midpoint, tails closed one step out
    assert s["m"] == pytest.approx(.10 * -6.5 + .15 * -3.5 + .15 * -0.5 + .25 * 2.5 + .20 * 5.5 + .15 * 8.5, abs=0.01)
    assert s["p_d"] == pytest.approx(.75 + (.60 - .75) * 2 / 3, abs=0.001)         # S(0) between -2 and +1
    assert "beyond" not in s
    assert s["lad"][0][3] == -1 and s["lad"][-1][3] == 1
    assert sum(r[2] for r in s["lad"]) == pytest.approx(1.0)


def test_kalshi_noisy_book_is_smoothed():
    # "by 5+" priced above "by 2+": pooled, so the ladder never has a negative bracket
    s = summarize_kalshi({"D": [(2, .40), (5, .45), (8, .10)], "R": [(2, .30)]})
    assert all(r[2] >= 0 for r in s["lad"])


def test_kalshi_one_sided_ladder():
    # the favourite's side only, no winner market: read when the median is inside the ladder ...
    s = summarize_kalshi({"R": [(10, .90), (20, .60), (30, .20)]})
    assert s["med"] == pytest.approx(-30 + 10 * (.80 - .5) / (.80 - .40), abs=0.01)  # -22.5
    assert s["m"] == pytest.approx(.2 * -35 + .4 * -25 + .3 * -15 + .1 * 0, abs=0.01)  # unpriced .1 at its midpoint
    assert s["p_d"] is None and s["lad"][-1][3] == 4
    # ... left out when it would fall in the stretch the ladder doesn't price
    assert summarize_kalshi({"R": [(10, .30), (20, .10), (30, .05)]}) is None
    # with the winner market, the unlisted side gets its chance from it
    s = summarize_kalshi({"R": [(10, .90), (20, .60), (30, .20)]}, {"R": .97, "D": .03})
    assert s["p_d"] == pytest.approx(.03) and s["lad"][-1][3] == 2


def test_kalshi_median_past_the_last_threshold_is_flagged():
    s = summarize_kalshi({"D": [(2, .95), (5, .90), (8, .70)]}, {"D": .97, "R": .03})
    assert s["beyond"] == 8.0 and s["med"] > 8


def test_kalshi_no_average_when_too_much_is_unpriced():
    # Republican side only, no winner market, 35% of the probability in the unpriced stretch
    assert summarize_kalshi({"R": [(10, .65), (20, .50), (30, .20)]}) is None


def _kdf(rows):
    return pd.DataFrame([{"series_ticker": "KXMIDTERMMOV", "event_ticker": ev, "yes_bid": p - .01, "yes_ask": p + .01,
                          "volume": 10, "market_title": f"Will the margin of victory for {who} in {race} be at least {n} percentage points?"}
                         for ev, who, race, n, p in rows])


def test_kalshi_events_to_races(tmp_path):
    races = {"2026-SEN-FL-S", "2026-H-WY-01", "2026-H-CA-40", "2026-SEN-AK"}
    assert kalshi_race_id("FL", "SEN", races) == "2026-SEN-FL-S"     # Florida votes only in its special
    assert kalshi_race_id("WY", "AL", races) == "2026-H-WY-01"
    assert kalshi_race_id("TX", "SEN", races) is None
    rows = [("KXMIDTERMMOV-AKSENMPEL", "Mary Peltola", "the Alaska Senate election", n, p) for n, p in ((2, .45), (4, .22), (6, .10))]
    rows += [("KXMIDTERMMOV-AKSENDSUL", "Dan Sullivan", "the Alaska Senate election", n, p) for n, p in ((2, .27), (4, .18))]
    # California top-two between two Republicans: no party margin to show
    rows += [("KXMIDTERMMOV-CA40YKIM", "Young Kim", "CA-40", n, p) for n, p in ((1, .6), (5, .4), (10, .2))]
    rows += [("KXMIDTERMMOV-CA40KCAL", "Ken Calvert", "CA-40", n, p) for n, p in ((1, .3), (5, .1))]
    path = tmp_path / "k.csv"
    _kdf(rows).to_csv(path, index=False)
    cands = {"2026-SEN-AK": [("Mary Peltola", "DEM"), ("Dan Sullivan", "REP")],
             "2026-H-CA-40": [("Young Kim", "REP"), ("Ken Calvert", "REP")]}
    out = kalshi_margins(path, cands=cands, races=races)
    assert set(out) == {"2026-SEN-AK"}
    assert 0 < out["2026-SEN-AK"]["m"] < 2 and out["2026-SEN-AK"]["vol"] == 50
    # a name the forecast can't place drops the race rather than guessing its side
    assert kalshi_margins(path, cands={}, races=races) == {}


def test_kalshi_brackets_beat_thresholds(tmp_path):
    # KXGENERALMOV: straight bets on the margin, used ahead of the KXMIDTERMMOV thresholds for the same race
    races = {'2026-SEN-TX', '2026-SEN-OH-S'}
    cands = {'2026-SEN-TX': [('James Talarico', 'DEM'), ('Ken Paxton', 'REP')]}
    q = 'Will the margin of victory for {} in the 2026 U.S. Senate election in Texas be {}?'
    rows = [dict(series_ticker='KXGENERALMOV', event_ticker='KXGENERALMOV-SENATETX-26', market_title=q.format(w, b),
                 yes_bid=p - .01, yes_ask=p + .01, volume=100)
            for w, b, p in [('James Talarico', 'between 0% and 2%', .18), ('James Talarico', 'between 2% and 4%', .20),
                            ('James Talarico', 'between 4% and 6%', .15), ('James Talarico', 'at least 6%', .17),
                            ('Ken Paxton', 'between 0% and 2%', .16), ('Ken Paxton', 'between 2% and 4%', .06),
                            ('Ken Paxton', 'at least 4%', .08)]]
    rows += [dict(series_ticker='KXMIDTERMMOV', event_ticker='KXMIDTERMMOV-TXSEND', yes_bid=p - .01, yes_ask=p + .01, volume=5,
                  market_title=f"Will the margin of victory for Democrats in the Texas Senate election be at least {n} percentage points?")
             for n, p in ((2, .5), (5, .3), (8, .1))]
    path = tmp_path / 'k.csv'
    pd.DataFrame(rows).to_csv(path, index=False)
    out = kalshi_margins(path, cands=cands, races=races)
    s = out['2026-SEN-TX']
    assert s['src'] == 'brackets' and s['vol'] == 700
    # midpoints, the open ends closed with the 2-pt width: Paxton 4+ at -5, Talarico 6+ at +7
    exp = (.08 * -5 + .06 * -3 + .16 * -1 + .18 * 1 + .20 * 3 + .15 * 5 + .17 * 7) / 1.0
    assert s['m'] == pytest.approx(exp, abs=0.02)
    assert KALSHI_BRACKET_EVENT_OK('KXGENERALMOV-SENATEOHS-26', races) == '2026-SEN-OH-S'
