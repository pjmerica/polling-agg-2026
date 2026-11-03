"""County benchmarks for races the election-night projector tracks but the guides don't cover.

Same method as county_benchmarks.py (build_race), written to a separate file so build_master.py,
build_election_night.py, census_blocs.py and county_reporting.py, which read every race in
county_benchmarks.json, don't grow sections for races outside the competitive list:
    data/processed/county_benchmarks_extra.json
live_project.py reads both files.

GA Senate (2026-11-02): Ossoff is a safe favourite, but with the Governor race on the same ballot it measures
ticket-splitting (the data desk's "Splits & turnout" view).

    py "State election results/scripts/benchmarks_extra.py"
"""
import datetime as dt
import json
import os

import county_benchmarks as cb

EXTRA = [
    dict(id="2026_GA_Senate", state="georgia", seat="Senate",
         bases=[cb.P24, ("2020 Senate (Ossoff-Perdue)", "2020/georgia-senate.json", "ossoffj", "perdued")],
         types=("2022 Senate", "2022/georgia-us-senate.json", "warnock-r", "walker-h")),
]


def main():
    data = cb.g.forecast()
    timing = cb.timing_2020()
    races = [cb.build_race(cfg, data, timing) for cfg in EXTRA]
    out = dict(built=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
               model_run=data["predictions_as_of"], scenario_pts=cb.SCEN, races=races)
    path = os.path.join(cb.OUT, "county_benchmarks_extra.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cb.rounded(out), f, separators=(",", ":"))
    print(f"{len(races)} races -> {path}")


if __name__ == "__main__":
    main()
