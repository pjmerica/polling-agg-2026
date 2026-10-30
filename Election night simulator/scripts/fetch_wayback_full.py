"""Download Internet Archive captures of NYT's 2022 and 2024 results files WHOLE (every race, every county,
votes by candidate), for replaying projector v1 (county_replay.py) out of sample.

State election results/scripts/fetch_wayback_counties.py kept only each county's total votes, which is
enough for reporting order but not for v1, which needs the candidates. The raw files are saved gzipped
and unparsed:
    data/raw/wayback_full/{year}/{state}/{timestamp}-results-{state}{suffix}.json.gz
Existing files are skipped, so a re-run only fetches what is missing.

    py "Election night simulator/scripts/fetch_wayback_full.py" [2022 2024]
"""
import gzip
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "wayback_full")
UA = {"User-Agent": "polling-agg research (github.com/pjmerica/polling-agg-2026)"}
STATES = ["alaska", "georgia", "ohio", "kansas", "texas", "nebraska", "maine", "iowa", "michigan",
          "nevada", "oregon", "south-carolina"]
EXTRA_2024 = ["wisconsin", "pennsylvania", "arizona", "north-carolina"]   # where 2024's misreads were
WINDOW = {2022: ("20221108230000", "20221115000000"), 2024: ("20241105230000", "20241112000000")}
BASE = {2022: "static01.nyt.com/elections-assets/2022/data/2022-11-08/results-{s}{r}.json",
        2024: "static01.nyt.com/elections-assets/pages/data/2024-11-05/results-{s}{r}.json"}
SUFFIX = {2022: ["", "-us-senate", "-governor"], 2024: ["", "-president", "-us-senate"]}


def get(url, timeout=240, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (404, 403):
                return None
        except requests.RequestException:
            pass
        time.sleep(5 * (i + 1))
    return None


def main():
    years = [int(a) for a in sys.argv[1:]] or [2022, 2024]
    for year in years:
        states = STATES + (EXTRA_2024 if year == 2024 else [])
        frm, to = WINDOW[year]
        for st in states:
            for suf in SUFFIX[year]:
                target = BASE[year].format(s=st, r=suf)
                r = get(f"https://web.archive.org/cdx/search/cdx?url={target}&from={frm}&to={to}"
                        f"&fl=timestamp&filter=statuscode:200", timeout=120)
                caps = sorted(set(r.text.split())) if r else []
                print(f"{year} {st}{suf}: {len(caps)} captures", flush=True)
                for ts in caps:
                    p = os.path.join(OUT, str(year), st, f"{ts}-results-{st}{suf}.json.gz")
                    if os.path.exists(p):
                        continue
                    s = get(f"https://web.archive.org/web/{ts}id_/https://{target}")
                    if s is None or not s.content.lstrip().startswith(b"{"):
                        continue
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with gzip.open(p, "wb") as f:
                        f.write(s.content)
                    time.sleep(1.5)


if __name__ == "__main__":
    main()
