"""County-level election-night history for 2020 from Wayback captures of NYT's national file.

NYT's 2020 national-map-page/president.json carries every county in every state
(votes, absentee votes, expected vote, precincts, last_updated). The Internet
Archive captured it ~900 times over election week. We take at most one capture
per 10 minutes, keep only the competitive-race states, and write
data/raw/wayback_2020/{timestamp}.json (one small file per capture).

    py "State election results/scripts/fetch_wayback_2020.py"
"""
import gzip
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "wayback_2020")
TARGET = "static01.nyt.com/elections-assets/2020/data/api/2020-11-03/national-map-page/national/president.json"
CDX = ("https://web.archive.org/cdx/search/cdx?url=" + TARGET +
       "&from=20201103230000&to=20201110235959&fl=timestamp,statuscode&collapse=timestamp:11")
STATES = {"alaska", "georgia", "ohio", "kansas", "texas", "nebraska", "maine", "iowa", "michigan",
          "nevada", "oregon", "south-carolina"}
COUNTY_KEYS = ["fips", "name", "votes", "absentee_votes", "results", "results_absentee", "eevp",
               "tot_exp_vote", "reporting", "precincts", "last_updated", "absentee_count_progress"]
RACE_KEYS = ["state_slug", "votes", "absentee_votes", "eevp", "tot_exp_vote", "precincts_reporting",
             "precincts_total", "last_updated", "result", "winnerCalledTimestamp"]


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            # some captures are stored gzipped and id_ replays them as-is
            return gzip.decompress(body) if body[:2] == b"\x1f\x8b" else body
        except Exception as e:  # Wayback is flaky; back off and retry
            if i == tries - 1:
                raise
            print(f"  retry {i + 1}: {e}")
            time.sleep(10 * (i + 1))


def main():
    os.makedirs(OUT, exist_ok=True)
    stamps = []
    for attempt in range(5):  # the CDX index sometimes answers with an empty body
        rows = [l.split() for l in get(CDX).decode().splitlines() if l.strip()]
        stamps = [ts for ts, code in rows if code == "200"]
        if stamps:
            break
        time.sleep(30)
    print(f"{len(stamps)} captures to process", flush=True)
    for n, ts in enumerate(stamps, 1):
        path = os.path.join(OUT, f"{ts}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                if STATES <= set(json.load(f)["states"]):
                    continue  # already has every state; re-fetch only when states were added
        try:
            data = json.loads(get(f"https://web.archive.org/web/{ts}id_/https://{TARGET}"))
        except Exception as e:
            print(f"{ts}: skipped ({e})", flush=True)
            continue
        keep = {}
        for race in data["data"]["races"]:
            if race.get("state_slug") in STATES:
                rec = {k: race.get(k) for k in RACE_KEYS}
                rec["counties"] = [{k: c.get(k) for k in COUNTY_KEYS} for c in race.get("counties", [])]
                keep[race["state_slug"]] = rec
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"capture": ts, "states": keep}, f)
        print(f"[{n}/{len(stamps)}] {ts}: {len(keep)} states", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
