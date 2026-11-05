"""The election-night record: a NYT re-stamp isn't a change, new votes are, and every House district has a file name."""
import csv
import gzip
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


def _poly(tmp_path, monkeypatch, closed, daily, fail=False, hourly=(), vol=0, trade=None):
    """poly_market against a stub of Polymarket. daily and hourly are what interval=max returns; a date range answers one point
    at its start, inside trade=(first, last) if given."""
    v = tmp_path / "market_archive" / "polymarket"
    (v / "hour").mkdir(parents=True)
    (v / "minute").mkdir()
    calls = []

    def get(url):
        calls.append(url)
        if fail:
            return None
        if "interval=max" in url:
            return dict(history=[dict(t=t, p=0.5) for t in (daily if "fidelity=1440" in url else hourly)])
        t = int(url.split("startTs=")[1].split("&")[0])
        return dict(history=[dict(t=t, p=0.5)] if not trade or trade[0] <= t <= trade[1] else [])
    monkeypatch.setattr(market_archive, "get", get)
    monkeypatch.setattr(market_archive.time, "sleep", lambda s: None)
    rec = dict(hour=0, minute=0, errors=0)
    market = dict(token="tok", event="ca-22-house-election-winner", closed=closed, vol=vol)
    market_archive.poly_market(market, 30000000, 20000000, 10000000, 40000000, rec, str(v))
    return rec, calls, v


def test_ranges_stay_under_polymarket_limit():
    r = market_archive.ranges(0, 40 * 86400)
    assert r[0][0] == 0 and r[-1][1] == 40 * 86400 and all(y - x <= 15 * 86400 for x, y in r)
    assert market_archive.ranges(5, 5) == []


def test_closed_market_gets_finer_prices_from_date_ranges(tmp_path, monkeypatch):
    rec, calls, v = _poly(tmp_path, monkeypatch, True, [15000000, 15500000])
    assert rec["hour"] > 0 and (v / "hour" / "tok.csv.gz").exists()
    assert rec["minute"] > 0 and (v / "minute" / "tok.csv.gz").exists()
    assert rec["errors"] == 0 and any("fidelity=1&" in c + "&" for c in calls)


def test_trading_after_the_last_daily_price_is_kept(tmp_path, monkeypatch):
    """Polymarket's daily prices can stop days before trading did: the market's real last week must not be cut off."""
    stop = 15000000 + 5 * 86400
    rec, calls, _ = _poly(tmp_path, monkeypatch, True, [14000000, 15000000], trade=(14000000, stop))
    assert rec["last"] > 15000000 + 86400
    ends = [int(c.split("endTs=")[1].split("&")[0]) for c in calls if "fidelity=1&" in c + "&"]
    assert max(ends) == rec["last"]


def test_market_under_a_day_old_is_kept(tmp_path, monkeypatch):
    """A short market has no daily price at all, though it traded."""
    rec, _, _ = _poly(tmp_path, monkeypatch, True, [], hourly=[15000000, 15003600])
    assert rec["hour"] > 0 and rec["minute"] > 0


def test_traded_market_interval_max_cannot_see_is_kept(tmp_path, monkeypatch):
    rec, _, _ = _poly(tmp_path, monkeypatch, True, [], vol=70000)
    assert rec["hour"] > 0


def test_closed_market_that_never_traded_stops_early(tmp_path, monkeypatch):
    rec, calls, _ = _poly(tmp_path, monkeypatch, True, [])
    assert len(calls) == 2 and rec == dict(hour=0, minute=0, errors=0)


def test_failed_request_is_counted_not_taken_for_no_prices(tmp_path, monkeypatch):
    rec, _, _ = _poly(tmp_path, monkeypatch, True, [], fail=True)
    assert rec["errors"] == 2


def test_kalshi_candles_read_in_both_api_shapes(tmp_path):
    live = dict(end_period_ts=1, yes_bid=dict(close_dollars="0.40"), yes_ask=dict(close_dollars="0.42"), price=dict(close_dollars="0.41"), volume_fp="5.00", open_interest_fp="9.00")
    old = dict(end_period_ts=2, yes_bid=dict(close="0.40"), yes_ask=dict(close="0.42"), price=dict(close="0.41"), volume="5.00", open_interest="9.00")
    none = dict(end_period_ts=3, yes_bid=dict(close="0.40"), yes_ask=dict(close="0.42"), price=dict(close=None), volume="0.00", open_interest="9.00")
    p = str(tmp_path / "k.csv.gz")
    market_archive.write_kalshi(p, [live, old, none])
    with gzip.open(p, "rt") as f:
        rows = list(csv.reader(f))
    assert rows[1][1:] == ["0.40", "0.42", "0.41", "5.00", "9.00"] == rows[2][1:]
    assert rows[3][1:] == ["0.40", "0.42", "", "0.00", "9.00"]


def test_older_market_open_on_election_night_gets_that_night_by_the_minute():
    """2024 general-election markets stayed open until inauguration: their last 9 days aren't election night."""
    o = market_archive.stamp("2024-01-05T00:00:00")
    c = market_archive.stamp("2025-01-20T15:00:00")
    w = market_archive.older_windows(o, c)
    night = market_archive.stamp("2024-11-06T03:00:00")
    assert any(a <= night <= b for a, b in w) and any(a <= c <= b for a, b in w)
    assert not any(a <= market_archive.stamp("2022-11-09T03:00:00") <= b for a, b in w)


def test_older_market_that_closed_at_the_election_has_one_window():
    c = market_archive.stamp("2024-11-06T12:00:00")
    assert market_archive.older_windows(c - 30 * 86400, c) == [(c - market_archive.LAST_DAYS, c + 3600)]


def test_failed_kalshi_request_is_counted(monkeypatch):
    monkeypatch.setattr(market_archive, "get", lambda url: None)
    monkeypatch.setattr(market_archive.time, "sleep", lambda s: None)
    rec = dict(errors=0)
    assert market_archive.kalshi_candles(dict(series="S", ticker="T"), 0, 3600, 60, rec) == [] and rec["errors"] == 1
