"""County-level election-night history for 2018, 2022 and 2024 from Wayback captures of NYT's
results files (2020 is fetch_wayback_2020.py: a dense national file, one capture per 10 minutes).

What the archive holds (checked 2026-10-26):
  2018  int.nyt.com/.../2018/api/1/races/2018-11-06.json - every race with its counties; 9 captures,
        Nov 6 6:38 p.m. ET to Nov 8 11:40 p.m. ET. Plus one capture each of a few per-state files.
  2022  static01.nyt.com/.../2022/data/2022-11-08/results-{state}[-us-senate|-governor].json -
        about 12-14 captures of each state's file and 0-15 of each race file, Nov 8 6:47 p.m. ET on.
  2024  static01.nyt.com/.../pages/data/2024-11-05/results-{state}[-president|-us-senate].json -
        only 1-9 per state (the 554 captures of results-president.json carry no counties).
For each capture and competitive-race state, the top statewide race's county (or town / district)
units are kept: name, FIPS, votes so far, precincts reporting, expected-vote share where NYT had it.
Writes data/raw/wayback_counties/{year}/{state}/{timestamp}-{file}.json; existing files are skipped.

    py "State election results/scripts/fetch_wayback_counties.py" [2018 2022 2024]
"""
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "raw", "wayback_counties")
UA = {"User-Agent": "polling-agg research (github.com/pjmerica/polling-agg-2026)"}
STATES = ["alaska", "georgia", "ohio", "kansas", "texas", "nebraska", "maine", "iowa", "michigan",
          "nevada", "oregon", "south-carolina"]
WINDOW = {2018: ("20181106230000", "20181112000000"),
          2022: ("20221108230000", "20221115000000"),
          2024: ("20241105230000", "20241112000000")}
# top statewide race to read, in order of preference
OFFICES = {2018: ["Senate", "Governor"], 2022: ["us-senate", "governor"], 2024: ["president"]}


def get(url, tries=4, timeout=240):
    err = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            err = e
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def captures(target, year):
    frm, to = WINDOW[year]
    url = (f"https://web.archive.org/cdx/search/cdx?url={target}&from={frm}&to={to}"
           f"&fl=timestamp&filter=statuscode:200")
    return sorted(set(get(url, timeout=120).text.split()))


def snapshot(ts, target):
    return get(f"https://web.archive.org/web/{ts}id_/https://{target}").json()


# ---- 2018: one national file, every race ----------------------------------------------------------
def extract_2018(d):
    out = {}
    for st in STATES:
        races = [r for r in d.get("races", []) if r.get("state_slug") == st
                 and r.get("election_type") == "general" and r.get("counties")]
        for office in OFFICES[2018]:
            pick = [r for r in races if r.get("office") == office]
            if pick:
                r = max(pick, key=lambda r: r.get("votes") or 0)
                out[st] = dict(race=r["race_slug"], poll_time=r.get("poll_time"),
                               generated=d.get("generated"),
                               units=[dict(fips=c.get("fips"), name=c.get("name"), votes=c.get("votes"),
                                           precincts_reporting=c.get("reporting"),
                                           precincts_total=c.get("precincts"))
                                      for c in r["counties"]])
                break
    return out


def fetch_2018():
    files = ["int.nyt.com/applications/elections/2018/api/1/races/2018-11-06.json"] + [
        f"int.nyt.com/applications/elections/2018/api/1/races/{s}/2018-11-06.json" for s in STATES]
    for target in files:
        tag = target.split("/races/")[1].replace("/", "_").replace(".json", "")
        try:
            caps = captures(target, 2018)
        except RuntimeError as e:
            print("  CDX failed:", e); continue
        print(f"2018 {tag}: {len(caps)} captures", flush=True)
        for ts in caps:
            todo = [s for s in STATES if not os.path.exists(os.path.join(OUT, "2018", s, f"{ts}-{tag}.json"))]
            if not todo:
                continue
            try:
                ex = extract_2018(snapshot(ts, target))
            except (RuntimeError, ValueError) as e:
                print("   skip", ts, e); continue
            for st, v in ex.items():
                p = os.path.join(OUT, "2018", st, f"{ts}-{tag}.json")
                os.makedirs(os.path.dirname(p), exist_ok=True)
                json.dump(dict(capture=ts, source=target, **v), open(p, "w"))
            time.sleep(1.5)


# ---- 2022 / 2024: per-state files -----------------------------------------------------------------
def extract_new(d, year):
    races = [r for r in d.get("races", []) if r.get("reporting_units")]
    for office in OFFICES[year]:
        pick = [r for r in races if office in (r.get("url") or "") or office in (r.get("nyt_id") or "")
                or (r.get("office") or "").lower().replace(" ", "-").replace("u.s.", "us") == office]
        if not pick:
            pick = [r for r in races if office.replace("us-", "") in (r.get("office") or "").lower()]
        if pick:
            r = max(pick, key=lambda r: sum(u.get("total_votes") or 0 for u in r["reporting_units"]))
            units = [dict(fips=(u.get("fips_state") or "") + (u.get("fips_county") or ""),
                          fips_suffix=u.get("fips_suffix"), name=u.get("name"), level=u.get("level"),
                          votes=u.get("total_votes"), eevp=u.get("eevp"),
                          precincts_reporting=u.get("precincts_reporting"),
                          precincts_total=u.get("precincts_total"))
                     for u in r["reporting_units"] if u.get("level") != "state"]
            return dict(race=r.get("nyt_id") or r.get("url"), office=r.get("office"),
                        updated=(d.get("resultsMeta") or {}).get("updated_at")
                        or (d.get("resultsMeta") or {}).get("timestamp"), units=units)
    return None


def fetch_new(year):
    base = {2022: "static01.nyt.com/elections-assets/2022/data/2022-11-08/results-{s}{r}.json",
            2024: "static01.nyt.com/elections-assets/pages/data/2024-11-05/results-{s}{r}.json"}[year]
    suffixes = {2022: ["", "-us-senate", "-governor"], 2024: ["", "-president", "-us-senate"]}[year]
    for st in STATES:
        for suf in suffixes:
            target = base.format(s=st, r=suf)
            tag = f"results-{st}{suf}"
            try:
                caps = captures(target, year)
            except RuntimeError as e:
                print("  CDX failed:", e); continue
            print(f"{year} {tag}: {len(caps)} captures", flush=True)
            for ts in caps:
                p = os.path.join(OUT, str(year), st, f"{ts}-{tag}.json")
                if os.path.exists(p):
                    continue
                try:
                    ex = extract_new(snapshot(ts, target), year)
                except (RuntimeError, ValueError) as e:
                    print("   skip", ts, e); continue
                if ex:
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    json.dump(dict(capture=ts, source=target, **ex), open(p, "w"))
                time.sleep(1.5)


def main():
    years = [int(a) for a in sys.argv[1:]] or [2018, 2022, 2024]
    for y in years:
        fetch_2018() if y == 2018 else fetch_new(y)


if __name__ == "__main__":
    main()
