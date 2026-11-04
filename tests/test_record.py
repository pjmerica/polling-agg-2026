"""The election-night record: a NYT re-stamp isn't a change, new votes are, and every House district has a file name."""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "Election night simulator", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "State election results", "scripts"))
import cloud_night  # noqa: E402
import market_archive  # noqa: E402


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


def _poly(tmp_path, monkeypatch, closed, daily, fail=False):
    """poly_market against a stub of Polymarket that holds daily prices and answers ranges with one point each."""
    v = tmp_path / "market_archive" / "polymarket"
    (v / "hour").mkdir(parents=True)
    (v / "minute").mkdir()
    calls = []

    def get(url):
        calls.append(url)
        if fail:
            return None
        if "interval=max" in url:
            return dict(history=[dict(t=t, p=0.5) for t in daily])
        return dict(history=[dict(t=int(url.split("startTs=")[1].split("&")[0]), p=0.5)])
    monkeypatch.setattr(market_archive, "get", get)
    monkeypatch.setattr(market_archive.time, "sleep", lambda s: None)
    rec = dict(hour=0, minute=0, errors=0)
    market_archive.poly_market(dict(token="tok", event="ca-22-house-election-winner", closed=closed), 3000000, 2000000, 4000000, rec, str(v))
    return rec, calls, v


def test_ranges_stay_under_polymarket_limit():
    r = market_archive.ranges(0, 40 * 86400)
    assert r[0][0] == 0 and r[-1][1] == 40 * 86400 and all(y - x <= 15 * 86400 for x, y in r)
    assert market_archive.ranges(5, 5) == []


def test_closed_market_gets_finer_prices_from_date_ranges(tmp_path, monkeypatch):
    rec, calls, v = _poly(tmp_path, monkeypatch, True, [1000000, 1500000])
    assert rec["hour"] > 0 and (v / "hour" / "tok.csv.gz").exists()
    assert rec["minute"] > 0 and (v / "minute" / "tok.csv.gz").exists()
    assert rec["errors"] == 0 and any("fidelity=1&" in c + "&" for c in calls)


def test_closed_market_with_no_prices_costs_one_request(tmp_path, monkeypatch):
    rec, calls, _ = _poly(tmp_path, monkeypatch, True, [])
    assert len(calls) == 1 and rec == dict(hour=0, minute=0, errors=0)


def test_failed_request_is_counted_not_taken_for_no_prices(tmp_path, monkeypatch):
    rec, _, _ = _poly(tmp_path, monkeypatch, True, [], fail=True)
    assert rec["errors"] == 1
