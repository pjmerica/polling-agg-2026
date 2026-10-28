"""Download every NYT results file for the competitive-race states (2022, 2024, 2026 primaries).

The list of file names comes from the Internet Archive's index of static01.nyt.com
(NYT publishes no index). The files themselves are fetched live from NYT.
Saves to data/raw/nyt_more/{election date}/{slug}.json; existing files are skipped.

    py "State election results/scripts/fetch_nyt_more.py"
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "nyt_more")
UA = {"User-Agent": "Mozilla/5.0"}
PREFIXES = ["static01.nyt.com/elections-assets/2022/data/2022-11-08/",
            "static01.nyt.com/elections-assets/pages/data/2024-11-05/",
            "static01.nyt.com/elections-assets/pages/data/2026-"]
STATES = "alaska|georgia|ohio|kansas|texas|nebraska|maine|iowa|michigan|nevada|oregon|south-carolina"
KEEP = re.compile(rf"results-({STATES})[a-z0-9-]*\.json$")
SKIP = re.compile(r"state-(senate|house)|mayor|county-judge")


LIST = os.path.join(OUT, "_file_list.txt")  # cached index: the archive's CDX service is often down


def get(url, timeout=180, tries=1):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def file_list():
    cached = open(LIST).read().split() if os.path.exists(LIST) else []
    # the cache only holds the states listed when it was built; re-query when a state was added
    if cached and all(re.search(rf"results-{s}", "\n".join(cached)) for s in STATES.split("|")):
        return cached
    urls = set(cached)
    for p in PREFIXES:
        cdx = f"https://web.archive.org/cdx/search/cdx?url={p}&matchType=prefix&fl=original&collapse=urlkey&limit=20000"
        for line in get(cdx, tries=5).decode().splitlines():
            u = re.sub(r"^https?://", "", line.strip()).split("?")[0].replace(":80", "")
            if KEEP.search(u) and not SKIP.search(u):
                urls.add(u)
    os.makedirs(OUT, exist_ok=True)
    with open(LIST, "w") as f:
        f.write("\n".join(sorted(urls)))
    return sorted(urls)


def main():
    urls = file_list()
    print(f"{len(urls)} files listed")
    for u in urls:
        date = re.search(r"/(\d{4}-\d{2}-\d{2})/", u).group(1)
        path = os.path.join(OUT, date, os.path.basename(u))
        if os.path.exists(path):
            continue
        try:
            body = get("https://" + u, timeout=60)
            json.loads(body)
        except (urllib.error.HTTPError, ValueError) as e:
            print(f"skip {u}: {e}")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(body)
        time.sleep(0.3)
    print("done")


if __name__ == "__main__":
    main()
