"""The election-night record: a NYT re-stamp isn't a change, new votes are, and every House district has a file name."""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "Election night simulator", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "State election results", "scripts"))
import cloud_night  # noqa: E402


def race(votes=100, eevp=50, status="too_early"):
    return dict(nyt_id="MS-G-S", race_call_status=status, updated_at="a", outcome={"won": []}, reporting_units=[
        dict(nyt_id="MS-state", total_votes=votes, eevp=eevp, total_expected_vote=200, updated_at="a",
             candidates=[dict(nyt_id="colom-s", votes=dict(total=votes)), dict(nyt_id="hydesmith-c", votes=dict(total=0))])])


def test_restamp_is_not_a_change():
    a, b = race(), race()
    b["updated_at"] = "b"
    b["reporting_units"][0]["updated_at"] = "b"
    b["reporting_units"][0]["nyt_model_estimates"] = {"id": "new"}
    assert cloud_night.vote_sig([a]) == cloud_night.vote_sig([b])


def test_votes_share_and_call_are_changes():
    base = cloud_night.vote_sig([race()])
    assert cloud_night.vote_sig([race(votes=101)]) != base
    assert cloud_night.vote_sig([race(eevp=51)]) != base
    assert cloud_night.vote_sig([race(status="called")]) != base


def test_house_files_at_large_and_numbered():
    fc = {"a": dict(agg_id="2026-H-AK-01"), "b": dict(agg_id="2026-H-OH-09"), "c": dict(agg_id="2026-SEN-OH-S"), "d": dict()}
    assert cloud_night.house_files(fc) == {"AK-01": "alaska-us-house-at-large", "OH-09": "ohio-us-house-9"}
