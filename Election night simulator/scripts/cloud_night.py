"""Election night in the cloud: the NYT recorder, the market recorder and the projector in one loop,
run by GitHub Actions (.github/workflows/election-night.yml) so the night doesn't depend on this PC.

Every pass (2 min on election night, 5 min from Wed Nov 4 18:00 UTC):
  capture_live.poll        NYT's results file for each race, every county (saved when it changes)
  capture_markets          Kalshi and Polymarket best bid/ask for each race
  live_project.run_live    v1/v0 projections, best buys, FLIPs -> live_data.js
then commits the state folder to the orphan branch `election-live` (one commit, amended and
force-pushed, so the branch never grows a history). The Pages copies
(docs/election-night-cloud.html, docs/election-night-desk.html, from build_cloud_pages.py) read
live_data.js straight from that branch, so there is no Pages rebuild per update.

State folder (the `election-live` checkout), all a later job needs to carry on:
  live_data.js                         what the pages read
  status.json                          last pass, per-race NYT file, errors
  projections.csv                      every pass's projections (the pages' charts through the night)
  markets/{ET date}/{venue}.csv        prices (bid/ask only; the PC recorder keeps the full book)
  live/{date}/{race}/{stamp}.json.gz   the latest NYT file per race; older ones go to --archive,
                                       which the workflow uploads as an artifact

A job stops itself before GitHub's 6-hour limit (--minutes) and the workflow starts the next one.

    py "Election night simulator/scripts/cloud_night.py" --state state --minutes 340
    py "Election night simulator/scripts/cloud_night.py" --state %TEMP%/st --minutes 3 --no-push   # local test
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(REPO, "State election results", "scripts"))
sys.path.insert(0, HERE)
import capture_live  # noqa: E402
import capture_markets  # noqa: E402
import live_project  # noqa: E402

END = dt.datetime(2026, 11, 8, 5, 0, tzinfo=dt.timezone.utc)        # Sat night after Nevada's postmark deadline
SLOW_FROM = dt.datetime(2026, 11, 4, 18, 0, tzinfo=dt.timezone.utc)  # Wed 1 pm ET: the late counts move slowly
MARKET_FIELDS = ["ts_utc", "race", "market", "outcome", "bid", "ask", "bid_size", "ask_size", "last", "volume"]
PROBE = "https://static01.nyt.com/elections-assets/pages/data/2026-08-04/results-michigan-us-senate-primary.json"


def log(msg):
    print(f"{dt.datetime.now(dt.timezone.utc):%H:%M:%SZ} {msg}", flush=True)


def git(state, *args, check=True):
    return subprocess.run(["git", "-C", state, *args], check=check, capture_output=True, text=True)


def restore_mtimes(live_dir):
    """A checkout stamps every file with the checkout time; live_project reads a NYT file's mtime as the
    time NYT last changed it, so put back the time in its name."""
    for p in glob.glob(os.path.join(live_dir, "*", "*", "*.json.gz")):
        try:
            t = dt.datetime.strptime(os.path.basename(p)[:16], "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
            os.utime(p, (t.timestamp(), t.timestamp()))
        except ValueError:
            pass


def prune_nyt(live_dir, archive):
    """Keep the newest NYT file per race in the state folder; move the rest to the archive."""
    for d in glob.glob(os.path.join(live_dir, "*", "*")):  # live/{date}/{race}
        files = sorted(glob.glob(os.path.join(d, "*.json.gz")))
        for p in files[:-1]:
            dest = os.path.join(archive, os.path.relpath(p, live_dir))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(p, dest)


def write_markets(state, date, venue, rows):
    if not rows:
        return
    d = os.path.join(state, "markets", date)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{venue}.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MARKET_FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def push(state, msg):
    git(state, "add", "-A")
    if git(state, "rev-parse", "--verify", "HEAD", check=False).returncode == 0:
        git(state, "commit", "--amend", "-q", "-m", msg)
    else:
        git(state, "commit", "-q", "-m", msg)
    r = git(state, "push", "-q", "--force", "origin", "HEAD:election-live", check=False)
    if r.returncode:
        log(f"push failed: {r.stderr.strip()[:300]}")
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True, help="the election-live checkout")
    ap.add_argument("--archive", default="archive", help="older NYT files go here (uploaded as an artifact)")
    ap.add_argument("--date", default="2026-11-03")
    ap.add_argument("--minutes", type=float, default=340, help="stop after this long (GitHub's limit is 360)")
    ap.add_argument("--interval", type=int, help="seconds between passes (default 120, 300 after Wed 1 pm ET)")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    state, archive = os.path.abspath(a.state), os.path.abspath(a.archive)
    os.makedirs(state, exist_ok=True)
    live_dir = os.path.join(state, "live")

    # the recorders and the projector read and write the state folder
    capture_live.OUT = live_dir
    live_project.LIVE = live_dir
    live_project.MARKETS = os.path.join(state, "markets")
    live_project.OUT = os.path.join(state, "projections.csv")
    work = os.path.join(archive, "_work")          # write_dashboard's folder: never the PC's own live_data.js
    live_project.ROOT = work
    restore_mtimes(live_dir)

    try:
        with urllib.request.urlopen(urllib.request.Request(PROBE, headers=capture_live.UA), timeout=30) as r:
            log(f"NYT reachable from here: HTTP {r.status}, {len(r.read()):,} bytes (Aug 4 Michigan primary)")
    except Exception as e:  # noqa: BLE001
        log(f"NYT PROBE FAILED: {e}")

    hist, fc = live_project.load_history(), live_project.load_forecast()
    pa = argparse.Namespace(date=a.date, race=None, pct=None, margin=None, prior_sd=live_project.PRIOR_SD,
                            baseline="market", watch=None, backtest=False)
    slugs_found, last_hash = {}, {}
    kal, poly, found_at = [], [], 0.0
    stop = time.time() + a.minutes * 60
    n = 0
    while True:
        start = time.time()
        now_dt = dt.datetime.now(dt.timezone.utc)
        if now_dt >= END:
            log("past the end of the cloud run; stopping")
            break
        errors = []
        try:
            capture_live.poll(a.date, capture_live.RACES, slugs_found, last_hash)
        except Exception as e:  # noqa: BLE001
            errors.append(f"nyt: {e}")
        try:
            if start - found_at > capture_markets.REDISCOVER or not (kal or poly):
                kal, poly = capture_markets.discover(capture_markets.RACES)
                found_at = start
                log(f"discovered {len(kal)} Kalshi and {len(poly)} Polymarket markets")
            now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            et_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).strftime("%Y-%m-%d")
            for venue, fn, mk in (("kalshi", capture_markets.poll_kalshi, kal),
                                  ("polymarket", capture_markets.poll_polymarket, poly)):
                try:
                    write_markets(state, et_date, venue, fn(mk, now))
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{venue}: {e}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"markets: {e}")
        try:
            live_project.run_live(pa, hist, fc)
            shutil.copyfile(os.path.join(work, "data", "raw", "dashboard", "live_data.js"),
                            os.path.join(state, "live_data.js"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"projector: {type(e).__name__}: {e}")
            traceback.print_exc()
        errors += live_project.ERRORS            # a race whose NYT file or counties didn't parse
        prune_nyt(live_dir, archive)
        n += 1
        status = dict(pass_utc=now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), passes_this_job=n,
                      run=os.environ.get("GITHUB_RUN_ID"), errors=errors,
                      nyt={r: slugs_found.get(r) for r in capture_live.RACES},
                      nyt_files={os.path.basename(d): os.path.basename(sorted(glob.glob(os.path.join(d, "*")))[-1])
                                 for d in glob.glob(os.path.join(live_dir, a.date, "*"))
                                 if glob.glob(os.path.join(d, "*"))})
        with open(os.path.join(state, "status.json"), "w", encoding="utf-8") as f:
            json.dump(status, f, indent=1)
        if errors:
            log("errors: " + "; ".join(errors))
        if not a.no_push:
            push(state, f"election-live {status['pass_utc']}")
        took = time.time() - start
        log(f"pass {n} done in {took:.0f}s")
        interval = a.interval or (300 if now_dt >= SLOW_FROM else 120)
        if time.time() + interval > stop:
            log("job time used up; the workflow starts the next job")
            break
        try:
            fc = live_project.load_forecast()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(max(5.0, interval - took))


if __name__ == "__main__":
    main()
