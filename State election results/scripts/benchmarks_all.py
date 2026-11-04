"""County benchmarks for every other 2026 Senate and Governor race (election night, 2026-11-03: the data desk
tracks every Senate and Governor race, user call).

Same method as county_benchmarks.py (build_race), with the bases chosen by rule instead of by hand:
  - the 2024 presidential race, and
  - the seat's own last contest: Senate = the 2020 race for the same seat (2022 for Florida's special),
    Governor = 2022 (2024 for New Hampshire and Vermont's two-year terms); its two main candidates are the top
    two finishers, one of them Republican (county_benchmarks.main_pair). A contest without that pair (two of
    one party, uncontested) is left out and the race rests on 2024 alone.
  - turnout weights: the 2022 governor's race, else the 2022 Senate race, else the 2024 presidential race.
Races already in county_benchmarks.json / county_benchmarks_extra.json are skipped, and so is Alaska's
Governor race (Alaska reports by House district; its Senate race has its own benchmark). Written to
    data/processed/county_benchmarks_all.json
which live_project.py reads after the other two. The guides don't read it.

    py "State election results/scripts/benchmarks_all.py"
"""
import datetime as dt
import json
import os

import county_benchmarks as cb
from capture_live import STATE_SLUG

SKIP = {"2026_AK_Governor"}


def exists(src, slug):
    return os.path.exists(os.path.join(cb.NYT, src.format(s=slug)))


def turnout_any(slug):
    for src in ("2022/{s}-governor.json", "2022/{s}-us-senate.json", "2024/{s}-president.json"):
        if exists(src, slug):
            us = cb.units(src, slug)
            return {k: sum(u["votes"].values()) for k, u in us.items()}
    raise FileNotFoundError(slug)


def seat_base(slug, office, special):
    if office == "Senate":
        opts = ["2022/{s}-us-senate.json"] if special else ["2020/{s}-senate.json"]
    else:
        opts = ["2022/{s}-governor.json", "2024/{s}-governor.json"]
    for src in opts:
        if not exists(src, slug):
            continue
        pair = cb.main_pair(src, slug)
        if not pair:
            print(f"  {slug} {office}: {src} has no D/I-vs-R top two; 2024 alone")
            return None
        (dk, _, dn), (rk, _, rn) = pair
        year = src[:4]
        return (f"{year} {office} ({dn}-{rn})", src, dk, rk)
    print(f"  {slug} {office}: no earlier contest in the archive; 2024 alone")
    return None


def main():
    data = cb.g.forecast()
    have = set()
    for name in ("county_benchmarks.json", "county_benchmarks_extra.json"):
        p = os.path.join(cb.OUT, name)
        if os.path.exists(p):
            have |= {r["id"] for r in json.load(open(p, encoding="utf-8"))["races"]}
    cb.turnout = turnout_any                    # build_race's turnout weights: the fallbacks above
    cb.NYT = os.path.join(cb.RAW, "nyt_all")    # every state's 2020-24 results (data/raw/nyt holds the guide states)
    for slug in STATE_SLUG.values():            # state names (county_benchmarks.NAMES holds the guide states)
        cb.NAMES.setdefault(slug, slug.replace("-", " ").title())
    timing = cb.timing_2020()
    races = []
    for r in data["races"]:
        rid = r["id"]
        office = "Senate" if "_Senate" in rid else "Governor" if "_Governor" in rid else None
        if not office or not rid.startswith("2026_") or rid in have or rid in SKIP:
            continue
        slug = STATE_SLUG[r["state"]]
        special = rid.endswith("-S")
        base = seat_base(slug, office, special)
        cfg = dict(id=rid, state=slug, seat=office + (" (special)" if special else ""),
                   bases=[cb.P24] + ([base] if base else []))
        try:
            races.append(cb.build_race(cfg, data, timing))
        except Exception as e:  # noqa: BLE001
            print(f"  {rid}: not built ({type(e).__name__}: {e})")
    out = dict(built=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
               model_run=data["predictions_as_of"], scenario_pts=cb.SCEN, races=races)
    path = os.path.join(cb.OUT, "county_benchmarks_all.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cb.rounded(out), f, separators=(",", ":"))
    print(f"{len(races)} races -> {path}")


if __name__ == "__main__":
    main()
