"""After a push, wait until GitHub Pages serves the files just committed (model repo CONCERNS #40).

    python tools/verify_pages.py docs/forecast_data.js docs/model_data.js [--minutes 20]

On 2026-08-06 a Pages build sat in "building" for 3+ hours and every later push queued behind it,
so the live site served a withdrawn candidate at 99% while git looked clean and the workflow was
green. A green push is not a deploy. This polls the live copy of each file (with a cache-busting
query) until its bytes match the committed file, and fails the job if they still differ after
--minutes, so a stuck deploy shows up as a failed run instead of a silent stale site.
"""
import argparse
import hashlib
import subprocess
import sys
import time
import urllib.request

SITE = "https://pjmerica.github.io/polling-agg-2026/"


def committed(path, rev="HEAD"):
    # the bytes git committed (LF), not the working copy's line endings
    return subprocess.run(["git", "show", f"{rev}:{path}"], check=True, capture_output=True).stdout


def acceptable(path):
    """Our commit's copy, or origin/master's: another workflow may push a newer one after ours."""
    ok = {hashlib.sha256(committed(path)).hexdigest()}
    if subprocess.run(["git", "fetch", "-q", "origin", "master"], capture_output=True).returncode == 0:
        try:
            ok.add(hashlib.sha256(committed(path, "origin/master")).hexdigest())
        except subprocess.CalledProcessError:
            pass
    return ok


def live(path, bust):
    url = SITE + path.removeprefix("docs/") + f"?v={bust}"
    req = urllib.request.Request(url, headers={"User-Agent": "polling-agg deploy check", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--minutes", type=float, default=20)
    a = ap.parse_args()
    deadline = time.time() + a.minutes * 60
    pending = set(a.files)
    while pending and time.time() < deadline:
        for f in sorted(pending):
            try:
                got = hashlib.sha256(live(f, int(time.time()))).hexdigest()
            except Exception as e:  # a transient fetch error is not a verdict
                print(f"  {f}: fetch failed ({e}); retrying")
                continue
            if got in acceptable(f):
                print(f"live: {f} matches the commit")
                pending.discard(f)
        if pending:
            time.sleep(30)
    if pending:
        print(f"::error::GitHub Pages still serves an older copy of {sorted(pending)} "
              f"{a.minutes:.0f} min after the push. Check the Pages build (Actions > pages-build-deployment).")
        sys.exit(1)


if __name__ == "__main__":
    main()
