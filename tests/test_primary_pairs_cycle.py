"""Primary-nominee pairs only for races on the 2026 ballot.

The 2027 Kentucky governor primary (Kalshi KXGOVKYNOMR-27, Polymarket
kentucky-governor-republican-primary-winner-2027) parsed to 2026-GOV-KY and
was paired as a 2.1% basket on 2026-10-27. Kentucky has no 2026 governor race.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import arb_scanner as A  # noqa: E402


def _cands(state, office, last, first):
    rows = []
    for plat, prob in (("kalshi", 0.055), ("polymarket", 0.11)):
        rows.append(dict(state=state, office=office, district=None, party="REP",
                         candidate_last=last, candidate_first=first,
                         candidate_name=f"{first} {last}", platform=plat, prob=prob,
                         url="", volume=1.0, oi=1.0, market_id=plat, raw_title=f"Will {last} be the Republican nominee",
                         race_id=A._race_id_from(state, office, None)))
    return pd.DataFrame(rows)


def test_off_ballot_race_not_paired(monkeypatch):
    monkeypatch.setattr(A, "load_primary_candidates", lambda: _cands("KY", "GOV", "massie", "T"))
    assert A.primary_pairs(A.get_race_meta()) == []


def test_on_ballot_race_still_paired(monkeypatch):
    monkeypatch.setattr(A, "load_primary_candidates", lambda: _cands("GA", "GOV", "jones", "B"))
    out = A.primary_pairs(A.get_race_meta())
    assert len(out) == 1 and out[0]["race_id"] == "2026-GOV-GA"
