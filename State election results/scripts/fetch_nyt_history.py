"""Download NYT election-results JSON for the competitive-race states (2020, 2022, 2024).

Each file holds final county results (2022/2024: split by vote type) and a
statewide timeseries of the count through election week. Raw files go to
data/raw/nyt/{year}/{state}-{race}.json and are not committed.

    py "State election results/scripts/fetch_nyt_history.py"
"""
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "nyt")
BASE = "https://static01.nyt.com/elections-assets/"
UA = {"User-Agent": "Mozilla/5.0"}

STATES = ["alaska", "georgia", "ohio", "kansas", "texas", "nebraska", "maine", "iowa", "michigan",
          "nevada", "oregon"]

# year -> (url template, race slugs). Slugs that don't exist for a state 404 and are skipped.
YEARS = {
    2020: ("2020/data/api/2020-11-03/race-page/{state}/{race}.json", ["president", "senate", "governor"]),
    2022: ("2022/data/2022-11-08/results-{state}-{race}.json", ["us-senate", "governor"]),
    2024: ("pages/data/2024-11-05/results-{state}-{race}.json", ["president", "us-senate", "governor"]),
}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 404):
            return None
        raise


def main():
    for year, (tmpl, races) in YEARS.items():
        os.makedirs(os.path.join(OUT, str(year)), exist_ok=True)
        for state in STATES:
            for race in races:
                path = os.path.join(OUT, str(year), f"{state}-{race}.json")
                if os.path.exists(path):
                    continue
                body = fetch(BASE + tmpl.format(state=state, race=race))
                if body is None:
                    continue
                json.loads(body)  # fail loudly on a non-JSON error page
                with open(path, "wb") as f:
                    f.write(body)
                print(f"{year} {state}-{race}: {len(body):,} bytes")
                time.sleep(0.5)


if __name__ == "__main__":
    main()
