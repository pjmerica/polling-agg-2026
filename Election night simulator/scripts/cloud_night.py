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
import concurrent.futures
import csv
import datetime as dt
import glob
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
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
# No job hand-off (about a minute without updates) inside these: a job that would end inside one ends just before
# it instead, and the next job covers the whole window (6:20-11:50 pm ET = first poll close through Iowa/Nebraska;
# the 340-minute job that starts at ~6:15 pm runs to ~11:55 pm).
NO_HANDOFF = [(dt.datetime(2026, 11, 3, 23, 20, tzinfo=dt.timezone.utc), dt.datetime(2026, 11, 4, 4, 50, tzinfo=dt.timezone.utc))]
MARKET_FIELDS = ["ts_utc", "race", "market", "outcome", "bid", "ask", "bid_size", "ask_size", "last", "volume"]
PROBE = "https://static01.nyt.com/elections-assets/pages/data/2026-08-04/results-michigan-us-senate-primary.json"

# ---------- the record, for a 2026 replay later (2026-11-02, user: "save the results as they come in for future races
# as much as possible ... we can also do save states of the model") ----------
# archive/ (each job's), packed and uploaded every hour to the GitHub release RELEASE (permanent; the job artifact
# expires after 90 days):
#   nyt/{date}/{race}/{stamp}.json.gz          every change of our races' NYT files (2-minute checks)
#   states/{date}/{state}/{stamp}.json.gz      every change of NYT's 50 state pages (10-minute checks): every Senate
#                                              and Governor race by county, every House race statewide
#   markets_full/{ET date}/{venue}.csv         the books, 5 levels a side
#   live_data/{stamp}.js.gz                    the projector's output (the pages' data) every 10 minutes
#   inputs/                                    what the projector started from: forecast, benchmarks, early vote, code
# Each upload also carries a copy of the state folder (projections.csv = every pass's projections, the prices).
RELEASE = "election-night-2026"
STATE_EVERY = 600            # seconds between state-page rounds and live_data snapshots
PRICE_EVERY = 20             # between passes, record the books this often (archive only; pages stay on the pass)
UPLOAD_EVERY = 3600
STATES = ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida",
          "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
          "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska",
          "nevada", "new-hampshire", "new-jersey", "new-mexico", "new-york", "north-carolina", "north-dakota", "ohio",
          "oklahoma", "oregon", "pennsylvania", "rhode-island", "south-carolina", "south-dakota", "tennessee", "texas",
          "utah", "vermont", "virginia", "washington", "west-virginia", "wisconsin", "wyoming"]


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
    """Keep the newest NYT file per race in the state folder; move the rest to archive/nyt/."""
    for d in glob.glob(os.path.join(live_dir, "*", "*")):  # live/{date}/{race}
        files = sorted(glob.glob(os.path.join(d, "*.json.gz")))
        for p in files[:-1]:
            dest = os.path.join(archive, "nyt", os.path.relpath(p, live_dir))
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


def write_full_markets(archive, date, venue, rows):
    """Every field the recorder reads, books included (the state folder keeps bid/ask only)."""
    if not rows:
        return
    d = os.path.join(archive, "markets_full", date)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{venue}.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=capture_markets.FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def save_inputs(archive):
    """What the projector starts from, once per job: a 2026 replay can rebuild every pass from these."""
    d = os.path.join(archive, "inputs")
    os.makedirs(d, exist_ok=True)
    res = os.path.join(REPO, "State election results", "data", "processed")
    for src in (os.path.join(REPO, "docs", "forecast_data.js"), os.path.join(res, "county_benchmarks.json"),
                os.path.join(res, "county_benchmarks_extra.json"), os.path.join(res, "early_vote_2026.csv"),
                os.path.join(res, "state_timeseries.csv")):
        if os.path.exists(src):
            with open(src, "rb") as f, gzip.open(os.path.join(d, os.path.basename(src) + ".gz"), "wb") as g:
                g.write(f.read())
    with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as f:
        json.dump(dict(sha=os.environ.get("GITHUB_SHA"), run=os.environ.get("GITHUB_RUN_ID"),
                       started=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       races=live_project.RACES, interval_s=dict(night=120, after=300)), f, indent=1)


def capture_states(archive, date, last_hash):
    """NYT's page for every state, saved when it changes. Missing pages (404) are skipped quietly."""
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def one(st):
        return st, capture_live.fetch(f"https://static01.nyt.com/elections-assets/pages/data/{date}/results-{st}.json")
    saved = 0
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for fut in concurrent.futures.as_completed([ex.submit(one, st) for st in STATES]):
            try:
                st, body = fut.result()
            except Exception as e:  # noqa: BLE001
                log(f"state page: {e}")
                continue
            if not body:
                continue
            h = hashlib.sha1(body).hexdigest()
            if h == last_hash.get(st):
                continue
            last_hash[st] = h
            d = os.path.join(archive, "states", date, st)
            os.makedirs(d, exist_ok=True)
            with gzip.open(os.path.join(d, f"{stamp}.json.gz"), "wb") as f:
                f.write(body)
            saved += 1
    return saved


def snapshot_live(archive, live_js):
    d = os.path.join(archive, "live_data")
    os.makedirs(d, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with open(live_js, "rb") as f, gzip.open(os.path.join(d, f"{stamp}.js.gz"), "wb") as g:
        g.write(f.read())


_uploading = None
UPLOAD_FAILED = "upload_failed"   # in the workspace; the workflow keeps the archive as an artifact when it exists


def failed(msg):
    log(msg)
    with open(UPLOAD_FAILED, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} {msg}\n")


def record_prices(archive, kal, poly, until):
    """Between passes: poll both venues every PRICE_EVERY seconds into markets_full until `until` (user 2026-11-03:
    "record them as much as possible"). One poll at a time, so Kalshi sees the pass's own request rate.
    Never raises; leaves at least the last poll's length before `until` so the next pass starts on time."""
    took = 15.0
    while kal or poly:
        t0 = time.time()
        if t0 + took + 2 > until:
            break
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        et_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).strftime("%Y-%m-%d")
        for venue, fn, mk in (("kalshi", capture_markets.poll_kalshi, kal),
                              ("polymarket", capture_markets.poll_polymarket, poly)):
            if not mk:
                continue
            try:
                write_full_markets(archive, et_date, venue, fn(mk, now))
            except Exception as e:  # noqa: BLE001
                log(f"price record {venue}: {e}")
        took = time.time() - t0
        rest = PRICE_EVERY - took
        if time.time() + max(rest, 0) + took + 2 > until:
            break
        if rest > 0:
            time.sleep(rest)
    time.sleep(max(0.0, until - time.time()))


def upload(archive, state, uploaded, n, final=False):
    """Pack the archive files not uploaded yet, plus a copy of the state folder, and attach them to the release.
    Runs in the background so the 2-minute passes don't wait (the final one waits). -> True when started or done.
    Only in GitHub Actions (needs GH_TOKEN)."""
    global _uploading
    if not os.environ.get("GH_TOKEN") or not os.environ.get("GITHUB_REPOSITORY"):
        return True
    if _uploading and _uploading.is_alive():
        if not final:
            return False                       # the last one is still going: try again next pass
        _uploading.join()
    # uploaded maps path -> size when packed: the full-book CSVs are appended every pass, so a file that grew is
    # packed again (a set of paths sent each one only in the job's first upload)
    size = {p: os.path.getsize(p) for p in glob.glob(os.path.join(archive, "**", "*"), recursive=True)
            if os.path.isfile(p) and os.sep + "_work" + os.sep not in p}
    new = [p for p, sz in size.items() if uploaded.get(p) != sz]
    stage = tempfile.mkdtemp(prefix="state-")  # the state folder changes every pass: pack a copy
    shutil.copytree(state, os.path.join(stage, "state"), ignore=shutil.ignore_patterns(".git"))
    run = os.environ.get("GITHUB_RUN_ID", "local")
    name = os.path.join(os.path.dirname(archive), f"night-{run}-{n:02d}{'-final' if final else ''}.tar.gz")

    def go():
        try:
            with tarfile.open(name, "w:gz") as t:
                for p in new:
                    t.add(p, arcname=os.path.relpath(p, archive))
                t.add(os.path.join(stage, "state"), arcname="state")
            r = subprocess.run(["gh", "release", "upload", RELEASE, name, "--clobber",
                                "--repo", os.environ["GITHUB_REPOSITORY"]], capture_output=True, text=True)
            if r.returncode:
                failed(f"release upload failed: {r.stderr.strip()[:300]}")
                return
            uploaded.update({p: size[p] for p in new})
            log(f"uploaded {os.path.basename(name)}: {len(new)} new files, {os.path.getsize(name) / 1e6:.1f} MB")
        except Exception as e:  # noqa: BLE001
            failed(f"release upload failed: {e}")
        finally:
            shutil.rmtree(stage, ignore_errors=True)
            if os.path.exists(name):
                os.remove(name)
    _uploading = threading.Thread(target=go, daemon=False)
    _uploading.start()
    if final:
        _uploading.join()
    return True


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

    save_inputs(archive)
    hist, fc = live_project.load_history(), live_project.load_forecast()
    pa = argparse.Namespace(date=a.date, race=None, pct=None, margin=None, prior_sd=live_project.PRIOR_SD,
                            baseline="model", watch=None, backtest=False)
    slugs_found, last_hash = {}, {}
    kal, poly, found_at = [], [], 0.0
    state_hash, uploaded, n_up = {}, {}, 0
    last_states = last_snap = 0.0
    last_up = time.time()
    stop = time.time() + a.minutes * 60
    for w0, w1 in NO_HANDOFF:
        end = dt.datetime.fromtimestamp(stop, dt.timezone.utc)
        early = (w0 - dt.timedelta(minutes=5)).timestamp()
        if w0 < end < w1 and early - time.time() > 25 * 60:
            stop = early
            log(f"ending at {w0 - dt.timedelta(minutes=5):%H:%MZ} so the next job covers {w0:%H:%M}-{w1:%H:%MZ} unbroken")
    n = 0
    while True:
        start = time.time()
        now_dt = dt.datetime.now(dt.timezone.utc)
        if now_dt >= END:
            log("past the end of the cloud run; stopping")
            break
        errors = []
        # nothing in a pass may end the job: a job that dies early doesn't hand off, and the cron backstop
        # restarts it only every 30 minutes
        try:
            try:
                capture_live.poll(a.date, capture_live.RACES, slugs_found, last_hash)
            except Exception as e:  # noqa: BLE001
                errors.append(f"nyt: {e}")
            try:
                if start - found_at > capture_markets.REDISCOVER or not (kal or poly):
                    kal, poly = capture_markets.discover(capture_markets.RACES, (kal, poly))
                    found_at = start
                    log(f"discovered {len(kal)} Kalshi and {len(poly)} Polymarket markets")
                now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                et_date = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).strftime("%Y-%m-%d")
                for venue, fn, mk in (("kalshi", capture_markets.poll_kalshi, kal),
                                      ("polymarket", capture_markets.poll_polymarket, poly)):
                    try:
                        rows = fn(mk, now)
                        write_markets(state, et_date, venue, rows)
                        write_full_markets(archive, et_date, venue, rows)
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
            if time.time() - last_states >= STATE_EVERY:
                last_states = time.time()
                try:
                    k = capture_states(archive, a.date, state_hash)
                    if k:
                        log(f"state pages: {k} changed")
                except Exception as e:  # noqa: BLE001
                    errors.append(f"state pages: {e}")
            live_js = os.path.join(state, "live_data.js")
            if time.time() - last_snap >= STATE_EVERY and os.path.exists(live_js):
                last_snap = time.time()
                snapshot_live(archive, live_js)
            n += 1
            status = dict(pass_utc=now_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), passes_this_job=n,
                          run=os.environ.get("GITHUB_RUN_ID"), errors=errors,
                          nyt={r: slugs_found.get(r) or capture_live.FROM_STATE.get(r) for r in capture_live.RACES},
                          nyt_files={os.path.basename(d): os.path.basename(sorted(glob.glob(os.path.join(d, "*")))[-1])
                                     for d in glob.glob(os.path.join(live_dir, a.date, "*"))
                                     if glob.glob(os.path.join(d, "*"))})
            with open(os.path.join(state, "status.json"), "w", encoding="utf-8") as f:
                json.dump(status, f, indent=1)
            if errors:
                log("errors: " + "; ".join(errors))
            if not a.no_push:
                push(state, f"election-live {status['pass_utc']}")
            if time.time() - last_up >= UPLOAD_EVERY:
                n_up += 1
                if upload(archive, state, uploaded, n_up):
                    last_up = time.time()
        except Exception as e:  # noqa: BLE001
            log(f"pass failed, carrying on: {type(e).__name__}: {e}")
            traceback.print_exc()
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
        record_prices(archive, kal, poly, time.time() + max(5.0, interval - took))
    upload(archive, state, uploaded, n_up + 1, final=True)


if __name__ == "__main__":
    main()
