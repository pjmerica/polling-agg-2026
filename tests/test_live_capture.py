"""Election-night recorders, offline (2026-11-03).

capture_live.from_state_page: a race whose own NYT file isn't found under any name we guessed is read from NYT's
page for its whole state. It must pick the race by office, the regular election before a special (2024 Nebraska
listed NE-G-S-... and NE-S_W-S-...), never a President district race, and come back in the race-file shape
live_project.latest_nyt reads.
capture_markets.discover: a race whose lookup fails keeps the markets it had, so one API error doesn't drop its
prices until the next discovery 30 minutes later."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "State election results" / "scripts"))
sys.path.insert(0, str(ROOT / "Election night simulator" / "scripts"))
import capture_live  # noqa: E402
import capture_markets  # noqa: E402


def _race(nyt_id, office):
    return {"nyt_id": nyt_id, "office": office, "candidate_metadata": {},
            "top_reporting_unit": {"candidates": [], "eevp": 0}, "reporting_units": []}


def _page(*races):
    return json.dumps({"races": list(races)}).encode()


def test_state_page_picks_the_regular_senate_race(monkeypatch):
    page = _page(_race("NE-G-P-CD_2-2026-11-03", "U.S. Senate"), _race("NE-S_W-S-2026-11-03", "U.S. Senate"),
                 _race("NE-G-S-2026-11-03", "U.S. Senate"), _race("NE-G-G-2026-11-03", "Governor"))
    monkeypatch.setattr(capture_live, "fetch", lambda url: page if url.endswith("results-nebraska.json") else None)
    got = json.loads(capture_live.from_state_page("2026-11-03", "NE-Sen", {}))
    assert [r["nyt_id"] for r in got["races"]] == ["NE-G-S-2026-11-03"]
    got = json.loads(capture_live.from_state_page("2026-11-03", "NE-Gov", {}))
    assert got["races"][0]["nyt_id"] == "NE-G-G-2026-11-03"


def test_state_page_takes_a_special_when_it_is_the_only_one(monkeypatch):
    page = _page(_race("OH-S_W-S-2026-11-03", "U.S. Senate"), _race("OH-G-G-2026-11-03", "Governor"))
    monkeypatch.setattr(capture_live, "fetch", lambda url: page)
    got = json.loads(capture_live.from_state_page("2026-11-03", "OH-Sen", {}))
    assert got["races"][0]["nyt_id"] == "OH-S_W-S-2026-11-03"


def test_state_page_missing_or_without_the_race(monkeypatch):
    monkeypatch.setattr(capture_live, "fetch", lambda url: None)
    assert capture_live.from_state_page("2026-11-03", "GA-Gov", {}) is None
    monkeypatch.setattr(capture_live, "fetch", lambda url: _page(_race("WY-G-H-1-2026-11-03", "U.S. House")))
    assert capture_live.from_state_page("2026-11-03", "WY-Gov", {}) is None
    assert capture_live.from_state_page("2026-11-03", "michigan-us-senate-primary", {}) is None   # --race slugs


def test_poll_falls_back_and_records_the_source(monkeypatch, tmp_path):
    page = _page(_race("GA-G-G-2026-11-03", "Governor"))
    monkeypatch.setattr(capture_live, "fetch", lambda url: page if url.endswith("results-georgia.json") else None)
    monkeypatch.setattr(capture_live, "OUT", str(tmp_path))
    found, hashes = {}, {}
    capture_live.poll("2026-11-03", {"GA-Gov": ["georgia-governor"]}, found, hashes)
    capture_live.poll("2026-11-03", {"GA-Gov": ["georgia-governor"]}, found, hashes)     # unchanged: not saved again
    assert found == {}                       # the race file names are still tried next pass
    assert capture_live.FROM_STATE["GA-Gov"] == "state page results-georgia.json"
    assert len(list((tmp_path / "2026-11-03" / "GA-Gov").glob("*.json.gz"))) == 1


def test_discover_keeps_a_race_whose_lookup_fails(monkeypatch):
    def get(url, body=None, tries=3):
        raise OSError("HTTP Error 503")
    monkeypatch.setattr(capture_markets, "get", get)
    monkeypatch.setattr(capture_markets.time, "sleep", lambda s: None)
    prev = ([dict(race="GA-Gov", ticker="GOVPARTYGA-26-D", outcome="Democratic")],
            [dict(race="GA-Gov", token="1", market="dem", outcome="Democratic")])
    kal, poly = capture_markets.discover({"GA-Gov": ("GOVPARTYGA-26", "georgia-governor-winner-2026")}, prev)
    assert kal == prev[0] and poly == prev[1]
