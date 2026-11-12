"""Snapshots official precinct results and ballot counts for the 2026 general, into the release election-night-2026.

Run by .github/workflows/precinct-record.yml. Each pass reads sources.json, saves a file only when its content has changed,
and never overwrites an older copy: every pass with changes is its own asset, precinct-record-{stamp}.tar.gz. So the record
shows when each state's numbers moved during the late count. precinct-state.json and precinct-log.csv carry the hashes and
the history across passes. README.md defines every column.

Only counts go in. Voter-level files (NC's absentee list has names and addresses) are reduced to counts here and the raw
file is never written. A site that refuses this script (403, or a "prove you are human" page) is logged as "refused" and
left alone.
"""
import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

RELEASE = "election-night-2026"
END = dt.datetime(2026, 12, 15, 5, tzinfo=dt.timezone.utc)
UA = {"User-Agent": "polling-agg election record (research)", "Accept-Encoding": "gzip"}
MAX_BYTES = 400_000_000
HERE = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(10**8)
# Fields that change on every publish even when no number did.
VOLATILE = re.compile(rb'"(createdAt|asOf|lastUpdated|publishDate|publishVersionId|nextUpdateAt|blobName)"\s*:\s*("[^"]*"|null)')
PRECINCT_WORD = re.compile(r"precinct|prct|[_-]pct|by.?ward|election.?district|statement.?of.?(the.?)?vote", re.I)
GENERAL_WORD = re.compile(r"general|\bnov|11.?03.?2026|2026.?11.?03", re.I)
NOT_RESULTS = re.compile(r"voter|absentee|ballot.?return|history|roster|registr|poll.?book|signature|primary|runoff|special|polling.?place|boundar|shapefile", re.I)
FILE_EXT = re.compile(r"\.(xlsx?|csv|zip|txt|pdf|json|tsv)$", re.I)
NC_KEYS = ["county_desc", "precinct_desc", "cong_dist_desc", "voter_party_code", "ballot_req_delivery_type", "ballot_req_type", "ballot_rtn_dt", "ballot_rtn_status"]


CHALLENGE = re.compile(rb"awswaf|Human Verification|cf-challenge|captcha", re.I)


class Refused(Exception):
    pass


def is_challenge(b):
    """A "prove you are human" page served in place of the file. That is a refusal: it is logged and not worked around."""
    head = b[:4000]
    return b"<html" in head.lower() and bool(CHALLENGE.search(head))


def get(url, attempts=3):
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                b = r.read(MAX_BYTES + 1)
                if len(b) > MAX_BYTES:
                    raise ValueError(f"over {MAX_BYTES} bytes")
                return gzip.decompress(b) if r.headers.get("content-encoding") == "gzip" else b
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 451):
                raise Refused(str(e.code)) from e
            last = e
            if e.code == 404:
                break
        except (OSError, ValueError) as e:
            last = e
        time.sleep(3 * (i + 1))
    raise last


def stable(b):
    """The bytes to compare: without the fields that change on every publish."""
    return VOLATILE.sub(b"", b)


def safe_name(s):
    return re.sub(r"[^\w.-]+", "_", s).strip("_")[:120]


def nc_counts(zip_bytes):
    """NC's absentee + early file -> counts by precinct, party, method, return date. No names or addresses survive."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    c = collections.Counter()
    with z.open(z.namelist()[0]) as h:
        for r in csv.DictReader(io.TextIOWrapper(h, encoding="latin-1", newline="")):
            c[tuple((r.get(k) or "").strip() for k in NC_KEYS)] += 1
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(NC_KEYS + ["ballots"])
    for k, v in sorted(c.items()):
        w.writerow(list(k) + [v])
    return out.getvalue().encode()


def drop_column(data, column):
    """A CSV without one column. Virginia's change log names the local official who typed each entry: not needed here."""
    src = io.StringIO(data.decode("utf-8-sig", "replace"), newline="")
    out = io.StringIO()
    r, w = csv.reader(src), csv.writer(out, lineterminator="\n")
    head = next(r, [])
    if column not in head:
        return data
    i = head.index(column)
    w.writerow([x for j, x in enumerate(head) if j != i])
    for row in r:
        w.writerow([x for j, x in enumerate(row) if j != i])
    return out.getvalue().encode()


def links_on_page(html, base):
    """Links on a state's results page that look like its 2026 general precinct results, on that state's own site."""
    host = ".".join(urllib.parse.urlparse(base).hostname.split(".")[-2:])
    found = {}
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, text = m.group(1).strip(), re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()
        url = urllib.parse.urljoin(base, href.replace("&amp;", "&"))
        parts = urllib.parse.urlparse(url)
        if "{" in url or not parts.hostname or not parts.hostname.endswith(host) or not FILE_EXT.search(parts.path):
            continue
        whole = urllib.parse.unquote(url) + " " + text
        if "2026" in whole and PRECINCT_WORD.search(whole) and GENERAL_WORD.search(whole) and not NOT_RESULTS.search(whole):
            found[url] = text
    return found


def report_files(election):
    """{report name: file name} from one read of an election record."""
    return {r.get("reportName") or r["blobName"]: r["blobName"] for c in election.get("publicReportCategories") or [] for r in c.get("reports") or [] if r.get("blobName")}


def enhanced_voting(src):
    """Georgia-type sites: the election record, its published reports, and the whole-state export when there is one."""
    host, s, e = src["host"], src["jurisdiction"], src["election"]
    rec = get(f"https://{host}/results/public/api/elections/{s}/{e}")
    yield "election.json", rec, stable(rec)
    d = json.loads(rec)
    reports = report_files(d)
    # Virginia re-publishes every minute or two, and each publish lists only some of its reports (the change log rarely).
    # Files from earlier publishes stay served, so keep reading the listing until every report has shown up.
    deadline = time.time() + 60 * src.get("wait_minutes", 0)
    while any(w not in reports for w in src.get("wait_for", [])) and time.time() < deadline:
        time.sleep(45)
        reports = {**reports, **report_files(json.loads(get(f"https://{host}/results/public/api/elections/{s}/{e}")))}
    for report, name in reports.items():
        b = get(f"https://{host}/cdn/results/{d['jurisdictionId']}/{urllib.parse.quote(name)}")
        label = safe_name(report) + os.path.splitext(name)[1].lower()
        if label.endswith(".csv"):
            b = drop_column(b, "Username")
        yield label, b, b
    try:
        b = get(f"https://{host}/cdn/results/{s}/export-{e}.json")
        yield "export.json", b, stable(b)
    except urllib.error.HTTPError as x:
        if x.code != 404:
            raise


def files(src):
    missing = []
    for url in src["urls"]:
        try:
            b = get(url)
        except urllib.error.HTTPError as e:  # one missing file must not cost the rest of the list
            missing.append(f"{url.rsplit('/', 1)[-1]} {e.code}")
            continue
        yield safe_name(urllib.parse.unquote(url.rsplit("/", 1)[-1])), b, b
    if missing:
        raise ValueError("missing: " + ", ".join(missing))


def links_matching(html, base, pattern):
    """Every link on a page, on that state's own site, whose address matches the source's pattern."""
    host = ".".join(urllib.parse.urlparse(base).hostname.split(".")[-2:])
    pat, found = re.compile(pattern, re.I), set()
    for m in re.finditer(r"""href=["']([^"']+)["']""", html, re.I):
        url = urllib.parse.urljoin(base, m.group(1).strip().replace("&amp;", "&")).split("#")[0]
        parts = urllib.parse.urlparse(url)
        if parts.scheme == "https" and parts.hostname and parts.hostname.endswith(host) and pat.search(parts.path):
            found.add(url)
    return sorted(found)


def linked(src):
    """The files a results page links to under a known folder. The page names them, so a renamed or added file (Alaska's
    ranked-choice reports, its final copies) is picked up without a change here."""
    problems, n = [], 0
    for page in src["pages"]:
        for url in links_matching(get(page).decode("utf-8", "replace"), page, src["match"]):
            name = safe_name(urllib.parse.unquote(url.rsplit("/", 1)[-1]))
            try:
                b = get(url)
            except (urllib.error.HTTPError, Refused) as e:  # one file must not cost the rest
                problems.append(f"{name} {getattr(e, 'code', None) or 'refused ' + str(e)}")
                continue
            if is_challenge(b):
                problems.append(f"{name} refused challenge")
                continue
            n += 1
            yield name, b, b
    if problems:
        raise ValueError("missing: " + ", ".join(problems))
    if not n:
        raise ValueError("no file linked from the page matches")


def counts_only(src):
    if src["reducer"] == "nc":
        out = nc_counts(get(src["url"]))
    elif src["reducer"] == "server":  # the state's own server does the counting; individual rows never reach this script
        out = get(src["url"])
    else:
        raise ValueError(src["reducer"])
    yield src["name"], out, out


def watch(src):
    """A state's results pages: fetch whatever 2026 general precinct file has appeared on them."""
    for page in src["pages"]:
        html = get(page).decode("utf-8", "replace")
        for url in links_on_page(html, page):
            b = get(url)
            yield "file-" + safe_name(urllib.parse.unquote(url.rsplit("/", 1)[-1])), b, b


KINDS = {"enhanced_voting": enhanced_voting, "files": files, "counts_only": counts_only, "watch": watch, "linked": linked}


def fetch(item):
    state, src = item
    rows, status = [], "ok"
    try:
        for name, data, compare in KINDS[src["kind"]](src):
            rows.append((name, data, hashlib.sha256(compare).hexdigest()))
    except Refused as e:
        status = f"refused {e}"
    except Exception as e:  # one state's failure must not cost the others
        status = re.sub(r"\s+", " ", f"error {type(e).__name__}: {e}")[:200]
    return state, src, rows, status


def run_gh(*a):
    return subprocess.run(["gh", *a, "--repo", os.environ["GITHUB_REPOSITORY"]], capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--states", default="", help="comma list; default all")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    if now >= END:
        print("past the end of the record")
        return 0
    os.makedirs(a.out, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%MZ")
    sp, lp = os.path.join(a.out, "precinct-state.json"), os.path.join(a.out, "precinct-log.csv")
    if a.upload:
        for f in ("precinct-state.json", "precinct-log.csv"):
            r = run_gh("release", "download", RELEASE, "--pattern", f, "--dir", a.out, "--clobber")
            if r.returncode:
                print(f"{f}: starting fresh ({(r.stderr or '').strip()[:100]})")
    state = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    sources = json.load(open(os.path.join(HERE, "sources.json"), encoding="utf-8"))
    wanted = set(filter(None, a.states.split(",")))
    items = [(s, x) for s, xs in sorted(sources.items()) for x in xs if not wanted or s in wanted]
    with ThreadPoolExecutor(8) as ex:
        done = list(ex.map(fetch, items))
    tar_path = os.path.join(a.out, f"precinct-record-{stamp}.tar.gz")
    changed, log = 0, []
    with tarfile.open(tar_path, "w:gz") as t:
        for st, src, rows, status in done:
            for name, data, sha in rows:
                key = f"{st}/{name}"
                old = state.get(key)
                new = not old or old["sha"] != sha
                if new:
                    info = tarfile.TarInfo(f"{st}/{name}/{stamp}-{name}")
                    info.size, info.mtime = len(data), int(now.timestamp())
                    t.addfile(info, io.BytesIO(data))
                    changed += 1
                    state[key] = {"sha": sha, "first": (old or {}).get("first", stamp), "changed": stamp, "copies": (old or {}).get("copies", 0) + 1, "bytes": len(data)}
                log.append([stamp, st, src["kind"], name, "new" if new else "same", len(data), sha[:16]])
            if status != "ok" or not rows:
                log.append([stamp, st, src["kind"], "", status if status != "ok" else "nothing yet", 0, ""])
    head = not os.path.exists(lp)
    with open(lp, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if head:
            w.writerow(["pass_utc", "state", "kind", "file", "status", "bytes", "sha"])
        w.writerows(log)
    json.dump(state, open(sp, "w", encoding="utf-8"), indent=0, sort_keys=True)
    by = collections.Counter(r[4].split(" ")[0] for r in log)
    print(f"{stamp}: {len(items)} sources, {changed} files changed; {dict(by)}")
    for r in log:
        if r[4] not in ("same", "nothing yet"):
            print(" ", r[1], r[3] or r[2], r[4], r[5])
    if not changed:
        os.remove(tar_path)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### Precinct record {stamp}\n\n{changed} files changed. {dict(by)}\n\n| State | File or kind | Status | Bytes |\n|---|---|---|---|\n")
            for r in log:
                f.write(f"| {r[1]} | {r[3] or r[2]} | {r[4]} | {r[5]} |\n")
    if a.upload:
        if changed:
            r = run_gh("release", "upload", RELEASE, tar_path)
            if r.returncode:
                print("upload failed:", r.stderr[:300])
                return 1  # state stays as it was, so the next pass captures these again
        r = run_gh("release", "upload", RELEASE, sp, lp, "--clobber")
        if r.returncode:
            print("state upload failed:", r.stderr[:300])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
