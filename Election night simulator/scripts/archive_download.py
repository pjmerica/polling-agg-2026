"""A local copy of the election record that can't be lost or edited (user 2026-11-05: "download a local file in the
archive folder so we dont lose it and it wont get edited").

Copies every asset of the releases below into Election night simulator/archive/releases/{tag}/ and the whole git
history of each repo into archive/repos/ as a bundle. Re-run any time: it fetches only what's new.

- Nothing local is ever overwritten. An asset whose content changed since the last copy (the files a running job
  re-sends, like precinct-log.csv) is saved beside the old copy as {name}.{updated time}.
- Each download is checked against GitHub's sha256 before it's kept.
- Every file is made read-only. MANIFEST.csv lists each file with its sha256, so a later edit would show.
- The folder is gitignored; it lives on this PC only.

    py "Election night simulator/scripts/archive_download.py"
"""
import csv
import datetime as dt
import hashlib
import json
import os
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(HERE, "..", "archive")
# market-archive-old-versions isn't here: it was uploaded from archive/market-history/, which already holds those files.
# Tags without a release (forecast-before-polls-2026) are in the git bundles.
RELEASES = [("pjmerica/polling-agg-2026", "election-night-2026"), ("pjmerica/polling-agg-2026", "forecast-2026-11-03-6pm-et")]
REPOS = ["pjmerica/polling-agg-2026", "pjmerica/house-night-2026", "pjmerica/mississippi-night-2026", "pjmerica/florida-night-2026"]
MANIFEST = os.path.join(ARCHIVE, "MANIFEST.csv")
COLUMNS = ["kind", "source", "name", "local_path", "bytes", "sha256", "source_updated_utc", "copied_utc"]


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(args[:4]) + ": " + r.stderr.strip()[:300])
    return r.stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def lock(path):
    os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def add(rows):
    new = not os.path.exists(MANIFEST)
    if not new:
        os.chmod(MANIFEST, stat.S_IREAD | stat.S_IWRITE)
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLUMNS)
        if new:
            w.writeheader()
        w.writerows(rows)
    lock(MANIFEST)


def releases(have, now):
    got, skipped, failed = 0, 0, []
    for repo, tag in RELEASES:
        try:
            assets = json.loads(gh("api", f"repos/{repo}/releases/tags/{tag}"))["assets"]
        except RuntimeError as e:
            failed.append((tag, str(e)))
            continue
        d = os.path.join(ARCHIVE, "releases", tag)
        os.makedirs(d, exist_ok=True)
        for a in assets:
            want = (a.get("digest") or "").replace("sha256:", "")
            if want and want in have:
                skipped += 1
                continue
            name = a["name"]
            path = os.path.join(d, name)
            if os.path.exists(path):        # same name, new content: keep both
                stem = a["updated_at"].replace(":", "").replace("-", "")
                path = os.path.join(d, f"{name}.{stem}")
                if os.path.exists(path):
                    skipped += 1
                    continue
            tmp = path + ".part"
            if os.path.exists(tmp):
                os.remove(tmp)
            try:
                gh("release", "download", tag, "--repo", repo, "--pattern", name, "--output", tmp)
            except RuntimeError as e:
                failed.append((name, str(e)))
                continue
            h = sha256(tmp)
            if want and h != want:      # the asset changed mid-download (a job re-sent it): try next run
                os.remove(tmp)
                failed.append((name, "checksum differs from GitHub's; asset probably re-sent during the download"))
                continue
            os.replace(tmp, path)
            lock(path)
            have.add(h)
            add([dict(kind="release", source=f"{repo}@{tag}", name=name, local_path=os.path.relpath(path, ARCHIVE), bytes=os.path.getsize(path),
                      sha256=h, source_updated_utc=a["updated_at"], copied_utc=now)])
            got += 1
            print("copied", tag, name, f"{os.path.getsize(path) / 1e6:.0f} MB", flush=True)
    return got, skipped, failed


def repos(now):
    d = os.path.join(ARCHIVE, "repos")
    os.makedirs(d, exist_ok=True)
    rows, failed = [], []
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%MZ")
    for repo in REPOS:
        name = repo.split("/")[1]
        mirror = os.path.join(d, name + ".git")
        try:
            if os.path.isdir(mirror):
                subprocess.run(["git", "-C", mirror, "remote", "update", "--prune"], check=True, capture_output=True)
            else:
                subprocess.run(["git", "clone", "-q", "--mirror", f"https://github.com/{repo}.git", mirror], check=True, capture_output=True)
            # the mirror tracks the remote; the bundles are the frozen copies (force-pushed branches included as they stood)
            path = os.path.join(d, f"{name}-{stamp}.bundle")
            subprocess.run(["git", "-C", mirror, "bundle", "create", os.path.abspath(path), "--all"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            failed.append((repo, (e.stderr or b"").decode()[:300]))
            continue
        lock(path)
        rows.append(dict(kind="git bundle", source=repo, name=os.path.basename(path), local_path=os.path.relpath(path, ARCHIVE), bytes=os.path.getsize(path),
                         sha256=sha256(path), source_updated_utc="", copied_utc=now))
        print("bundled", repo, f"{os.path.getsize(path) / 1e6:.0f} MB", flush=True)
    add(rows)
    return len(rows), failed


def lock_tree(top):
    n = 0
    for root, _, files in os.walk(top):
        if ".git" + os.sep in root + os.sep:
            continue        # the git mirrors must stay writable to update
        for f in files:
            p = os.path.join(root, f)
            if f.endswith(".part") or p == MANIFEST:
                continue
            if os.stat(p).st_mode & stat.S_IWRITE:
                lock(p)
                n += 1
    return n


def main():
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(ARCHIVE, exist_ok=True)
    have = {r["sha256"] for r in manifest()}
    got, skipped, failed = releases(have, now)
    bundles, bfailed = repos(now)
    locked = lock_tree(ARCHIVE)     # also the older copies already here (market-history, replay-2024, night-records)
    print(f"done: {got} release files copied, {skipped} already here, {bundles} git bundles, {locked} older files made read-only")
    for x in failed + bfailed:
        print("NOT COPIED:", *x)
    sys.exit(1 if failed or bfailed else 0)


if __name__ == "__main__":
    main()
