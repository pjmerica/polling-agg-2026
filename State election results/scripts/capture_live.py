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
tried per race and the first that answers 200 is kept.
"""
import argparse
import datetime as dt
import gzip
import hashlib
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

# race key -> candidate NYT slugs, most likely first
RACES = {
    "AK-Sen": ["alaska-us-senate"],
    "GA-Gov": ["georgia-governor"],
    "OH-Gov": ["ohio-governor"],
    "OH-Sen": ["ohio-us-senate-special", "ohio-us-senate"],
    "KS-Sen": ["kansas-us-senate"],
    "TX-Sen": ["texas-us-senate"],
    "NE-Sen": ["nebraska-us-senate"],
    "ME-Sen": ["maine-us-senate"],
    "IA-Sen": ["iowa-us-senate"],
    "MI-Sen": ["michigan-us-senate"],
    "NV-Gov": ["nevada-governor"],
    "OR-Gov": ["oregon-governor"],
    "TX-Gov": ["texas-governor"],
}


def fetch(url):
    # cache-buster: the CDN otherwise serves stale copies for a minute or more
    req = urllib.request.Request(f"{url}?t={int(time.time())}", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def poll(date, races, slugs_found, last_hash):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for race, slugs in races.items():
        tries = [slugs_found[race]] if race in slugs_found else slugs
        for slug in tries:
            try:
                body = fetch(BASE.format(date=date, slug=slug))
            except Exception as e:
                print(f"{now} {race}: error {e}")
                break
            if body is None:
                continue
            slugs_found[race] = slug
            h = hashlib.sha1(body).hexdigest()
            if h != last_hash.get(race):
                last_hash[race] = h
                d = os.path.join(OUT, date, race)
                os.makedirs(d, exist_ok=True)
                with gzip.open(os.path.join(d, f"{now}.json.gz"), "wb") as f:
                    f.write(body)
                print(f"{now} {race} ({slug}): saved {len(body):,} bytes")
            break
        else:
            print(f"{now} {race}: no file yet ({', '.join(slugs)})")


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
    while True:
        poll(a.date, races, slugs_found, last_hash)
        sys.stdout.flush()
        if a.once or (until and dt.datetime.now(dt.timezone.utc) >= until):
            break
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
