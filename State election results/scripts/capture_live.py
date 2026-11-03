"""Record election-night results for the competitive races, every county, every change.

Polls NYT's results JSON for each race every INTERVAL seconds and saves a gzipped
copy whenever the content changes:
    data/raw/live/{date}/{race}/{UTC timestamp}.json.gz
That is the county-by-county reporting history we cannot get for past elections.

    py "State election results/scripts/capture_live.py"                # 2026-11-03 general
    py "State election results/scripts/capture_live.py" --once         # one pass (test)
    py "State election results/scripts/capture_live.py" --date 2026-08-04 --race michigan-us-senate-primary --once

Leave it running from before 7 p.m. ET on Nov 3; it keeps going until stopped
(Ctrl+C). The NYT slugs for 2026 are not published yet - several spellings are
tried per race and the first that answers 200 is kept. A race none of them finds is
read from NYT's page for its whole state (results-{state}.json: every Senate and
Governor race by county, in the same shape), so a wrong guess doesn't lose the race.
"""
import argparse
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "live")
BASE = "https://static01.nyt.com/elections-assets/pages/data/{date}/results-{slug}.json"
UA = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}
INTERVAL = 120
TIMEOUT = 30            # seconds per request; the races are fetched in parallel, so one slow file holds up no other
WORKERS = 8

# race key -> candidate NYT slugs, most likely first
RACES = {
    "AK-Sen": ["alaska-us-senate"],
    "GA-Gov": ["georgia-governor"],
    # added 2026-11-02 for the split-ticket view (against GA-Gov); not a competitive race
    "GA-Sen": ["georgia-us-senate"],
    "OH-Gov": ["ohio-governor"],
    "OH-Sen": ["ohio-us-senate-special", "ohio-us-senate", "ohio-us-senate-special-election", "ohio-senate-special"],
    "KS-Sen": ["kansas-us-senate"],
    # entered the 75% list with the 2026-10-27 evening retrain: recorded too
    "KS-Gov": ["kansas-governor"],
    "SC-Sen": ["south-carolina-us-senate"],
    "TX-Sen": ["texas-us-senate"],
    "NE-Sen": ["nebraska-us-senate"],
    "ME-Sen": ["maine-us-senate"],
    "IA-Sen": ["iowa-us-senate"],
    "MI-Sen": ["michigan-us-senate"],
    "NV-Gov": ["nevada-governor"],
    "OR-Gov": ["oregon-governor"],
    "TX-Gov": ["texas-governor"],
}

# The fallback (2026-11-03): NYT's state page lists every race in the state; a Senate or Governor race there is
# identical to the race's own file (checked on 2024 Pennsylvania Senate: top line, candidates and all 68 units the
# same). Special elections carry their own id there (2024 Nebraska: NE-G-S-... regular, NE-S_W-S-... special), so
# the race is matched by office, the regular election first.
STATE_SLUG = {"AK": "alaska", "AL": "alabama", "AR": "arkansas", "AZ": "arizona", "CA": "california",
              "CO": "colorado", "CT": "connecticut", "DE": "delaware", "FL": "florida", "GA": "georgia",
              "HI": "hawaii", "IA": "iowa", "ID": "idaho", "IL": "illinois", "IN": "indiana", "KS": "kansas",
              "KY": "kentucky", "LA": "louisiana", "MA": "massachusetts", "MD": "maryland", "ME": "maine",
              "MI": "michigan", "MN": "minnesota", "MO": "missouri", "MS": "mississippi", "MT": "montana",
              "NC": "north-carolina", "ND": "north-dakota", "NE": "nebraska", "NH": "new-hampshire",
              "NJ": "new-jersey", "NM": "new-mexico", "NV": "nevada", "NY": "new-york", "OH": "ohio",
              "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania", "RI": "rhode-island", "SC": "south-carolina",
              "SD": "south-dakota", "TN": "tennessee", "TX": "texas", "UT": "utah", "VA": "virginia",
              "VT": "vermont", "WA": "washington", "WI": "wisconsin", "WV": "west-virginia", "WY": "wyoming"}
OFFICE_NAME = {"Sen": "U.S. Senate", "Gov": "Governor"}
FROM_STATE = {}         # race -> the state page it was read from on the last pass (cloud_night.py's status.json)


def fetch(url):
    # cache-buster: the CDN otherwise serves stale copies for a minute or more
    req = urllib.request.Request(f"{url}?t={int(time.time())}", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def race_file(date, race, slugs, slugs_found):
    """-> (slug, body) from the first slug that answers, or (None, None). Network errors propagate."""
    for slug in ([slugs_found[race]] if race in slugs_found else slugs):
        body = fetch(BASE.format(date=date, slug=slug))
        if body is not None:
            return slug, body
    return None, None


def from_state_page(date, race, pages):
    """The race out of NYT's page for its whole state, as {"races": [race]} (what a race file holds and
    live_project.latest_nyt reads), or None. pages caches each state's page for this pass."""
    st, off = (race.split("-") + [""])[:2]
    slug, office = STATE_SLUG.get(st), OFFICE_NAME.get(off)
    if not slug or not office:
        return None
    if slug not in pages:
        pages[slug] = fetch(BASE.format(date=date, slug=slug))
    if not pages[slug]:
        return None
    rs = [r for r in json.loads(pages[slug]).get("races") or []
          if r.get("office") == office and "CD_" not in str(r.get("nyt_id")) and r.get("top_reporting_unit")]
    if not rs:
        return None
    rs.sort(key=lambda r: "-G-" not in str(r.get("nyt_id")))      # the regular election before a special
    return json.dumps({"races": rs[:1], "source": f"results-{slug}.json"}, sort_keys=True).encode()


def poll(date, races, slugs_found, last_hash):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    got, missing = {}, []
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(race_file, date, race, slugs, slugs_found): race for race, slugs in races.items()}
        for fut in concurrent.futures.as_completed(futs):
            race = futs[fut]
            try:
                slug, body = fut.result()
            except Exception as e:  # noqa: BLE001  - a network error: try the race again next pass
                print(f"{now} {race}: error {e}")
                continue
            if body is None:
                missing.append(race)
            else:
                got[race] = (slug, body)
    pages = {}
    for race in missing:                       # no file under any name we tried: the state page
        try:
            body = from_state_page(date, race, pages)
        except Exception as e:  # noqa: BLE001
            print(f"{now} {race}: state page error {e}")
            body = None
        if body is None:
            FROM_STATE.pop(race, None)
            print(f"{now} {race}: no file yet ({', '.join(races[race])})")
            continue
        FROM_STATE[race] = f"state page {json.loads(body)['source']}"
        got[race] = (None, body)
    for race, (slug, body) in got.items():
        if slug:
            slugs_found[race] = slug
            FROM_STATE.pop(race, None)
        h = hashlib.sha1(body).hexdigest()
        if h != last_hash.get(race):
            last_hash[race] = h
            d = os.path.join(OUT, date, race)
            os.makedirs(d, exist_ok=True)
            with gzip.open(os.path.join(d, f"{now}.json.gz"), "wb") as f:
                f.write(body)
            print(f"{now} {race} ({slug or FROM_STATE.get(race)}): saved {len(body):,} bytes")


def keep_awake():
    """Hold off sleep while the capture runs (2026-10-28). This PC sleeps in Modern Standby (S0 low
    power idle), which throttles or suspends background programs: once the idle timer fired, the
    2-minute captures would stall for hours. ES_CONTINUOUS | ES_SYSTEM_REQUIRED keeps the system
    awake (the display may still turn off) until the process exits. Closing the lid can still
    sleep the machine, so leave it open and plugged in."""
    if os.name == "nt":
        import ctypes
        if not ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001):
            print("WARNING: could not hold off sleep; keep the PC awake by hand")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-11-03")
    ap.add_argument("--race", help="a single NYT slug to record instead of the competitive races")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=INTERVAL)
    ap.add_argument("--until", help="stop at this UTC time, e.g. 2026-11-06T17:00")
    a = ap.parse_args()
    races = {a.race: [a.race]} if a.race else RACES
    until = dt.datetime.fromisoformat(a.until).replace(tzinfo=dt.timezone.utc) if a.until else None
    slugs_found, last_hash = {}, {}
    if not a.once:
        keep_awake()
    while True:
        poll(a.date, races, slugs_found, last_hash)
        sys.stdout.flush()
        if a.once or (until and dt.datetime.now(dt.timezone.utc) >= until):
            break
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
