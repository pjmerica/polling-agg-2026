"""Publish a delayed copy of the election-night dashboard to GitHub Pages, for sharing.

Every --interval minutes (default 10) this commits two files to master through GitHub's API (`gh api`):
  docs/election-night-live.html        dashboard.html with <body data-public="1">
  docs/election_night_live_data.js     the projector's latest data/raw/dashboard/live_data.js, minus best buys
                                       and FLIPs (a 10-minute-old "buy at 15c" would mislead)
  docs/county_geo.js                   the map tab's county shapes (unchanged after the first publish)
-> https://pjmerica.github.io/polling-agg-2026/election-night-live.html

Through the API, not git: the local checkout (and the scheduled tasks writing into it) is never touched.
Pages allows about 10 rebuilds an hour for a site published from a branch, and the repo's own refresh
workflows rebuild too, so keep the interval at 10 minutes or more. Skips a pass when nothing changed or
when the projector has stopped writing (the page then shows its age). Ctrl+C stops it.

    py "Election night simulator/scripts/publish_live.py"            # every 10 min until Ctrl+C
    py "Election night simulator/scripts/publish_live.py" --once     # one update now
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO_SLUG = "pjmerica/polling-agg-2026"
BRANCH = "master"
DATA = os.path.join(ROOT, "data", "raw", "dashboard", "live_data.js")
PAGE = os.path.join(ROOT, "dashboard.html")
OUT_PAGE = "docs/election-night-live.html"
OUT_DATA = "docs/election_night_live_data.js"
GEO = os.path.join(ROOT, "county_geo.js")       # the map tab's county shapes (build_county_geo.py)
OUT_GEO = "docs/county_geo.js"
URL = "https://pjmerica.github.io/polling-agg-2026/election-night-live.html"


def gh(method, path, body=None):
    """GitHub REST call through the gh CLI (its stored login) -> parsed JSON; raises on an HTTP error."""
    cmd = ["gh", "api", "-X", method, f"repos/{REPO_SLUG}/{path}"]
    if body is not None:
        cmd += ["--input", "-"]
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None, capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"{method} {path}: {(r.stderr or r.stdout).strip()[:300]}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def public_files():
    """(page html, data js, the data's 'generated' time) for the public copy, or None without data."""
    if not os.path.exists(DATA):
        return None
    s = open(DATA, encoding="utf-8").read()
    data = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if data.get("dry_run"):
        raise SystemExit("live_data.js is from a dry run: run the real projector first (run_dashboard.cmd)")
    for r in data["races"]:
        r["best"] = None                       # stale trade prompts stay private
    data["public"] = True
    page = open(PAGE, encoding="utf-8").read().replace("<body>", '<body data-public="1">', 1)
    page = page.replace("<title>Election Night Live</title>", "<title>Election Night Live</title>\n"
                        '<meta name="description" content="Live 2026 election-night projections, county by county, '
                        'against the prediction markets. Delayed about 10 minutes.">', 1)
    js = "window.LIVE = " + json.dumps(data, separators=(",", ":")) + ";\n"
    return page, js, data["generated"]


def commit(files, message):
    """One commit on master with {path: text}; retried if another push lands in between."""
    for attempt in range(5):
        head = gh("GET", f"git/ref/heads/{BRANCH}")["object"]["sha"]
        base = gh("GET", f"git/commits/{head}")["tree"]["sha"]
        tree = [dict(path=p, mode="100644", type="blob",
                     sha=gh("POST", "git/blobs", dict(content=t, encoding="utf-8"))["sha"])
                for p, t in files.items()]
        new_tree = gh("POST", "git/trees", dict(base_tree=base, tree=tree))["sha"]
        c = gh("POST", "git/commits", dict(message=message, tree=new_tree, parents=[head]))["sha"]
        try:
            gh("PATCH", f"git/refs/heads/{BRANCH}", dict(sha=c, force=False))
            return c
        except RuntimeError as e:              # not a fast-forward: a workflow pushed meanwhile
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(3)
    raise RuntimeError("could not update master after 5 tries")


def to_et(t):
    try:
        from zoneinfo import ZoneInfo
        return t.astimezone(ZoneInfo("America/New_York"))
    except Exception:                          # noqa: BLE001 - no tz database on this Python: Nov 3 is EST
        return t - dt.timedelta(hours=5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=10, help="minutes between updates (keep >= 10)")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    last = None
    print(f"publishing to {URL}")
    while True:
        stamp = dt.datetime.now().strftime("%H:%M")
        try:
            got = public_files()
            if got is None:
                print(f"{stamp} no data yet (start the projector)")
            else:
                page, js, generated = got
                h = hashlib.sha1((page + js).encode()).hexdigest()
                age = (dt.datetime.now(dt.timezone.utc) -
                       dt.datetime.fromisoformat(generated.replace("Z", "+00:00"))).total_seconds()
                if h == last:
                    print(f"{stamp} unchanged, skipped")
                elif age > 1800 and not a.once:
                    print(f"{stamp} the projector last wrote {age / 60:.0f} min ago: skipped (is it running?)")
                else:
                    et = to_et(dt.datetime.fromisoformat(generated.replace("Z", "+00:00"))).strftime("%H:%M")
                    files = {OUT_PAGE: page, OUT_DATA: js}
                    if os.path.exists(GEO):            # unchanged shapes make an identical blob: no repo growth
                        files[OUT_GEO] = open(GEO, encoding="utf-8").read()
                    c = commit(files, f"election night live: {et} ET")
                    last = h
                    print(f"{stamp} published {c[:8]} (data from {et} ET); live in about a minute")
        except SystemExit:
            raise
        except Exception as e:                 # noqa: BLE001 - keep going all night
            print(f"{stamp} failed, will retry: {type(e).__name__}: {e}")
        sys.stdout.flush()
        if a.once:
            break
        time.sleep(a.interval * 60)


if __name__ == "__main__":
    main()
