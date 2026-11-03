"""Hours after poll close to first votes / 50% / 90% / 95% of the final count, per state, 2022 and 2024,
from State election results/data/processed/state_timeseries.csv (NYT timelines). Prints the CG_PACE literal
for the data desk's Tonight's count roadmap (data_dashboard.html); paste it over the old one.

    py "Election night simulator/scripts/count_pace.py"
"""
import json
import os

import pandas as pd

TS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "State election results", "data",
                  "processed", "state_timeseries.csv")
# the race with the full timeline each year (2024 presidential files run only 8 pm - 5:40 am ET)
PICK = {
    "GA": ("georgia", "us-senate", "president"), "SC": ("south-carolina", "us-senate", "president"),
    "OH": ("ohio", "us-senate", "us-senate"), "MI": ("michigan", "governor", "us-senate"),
    "TX": ("texas", "governor", "us-senate"), "KS": ("kansas", "us-senate", "president"),
    "ME": ("maine", "governor", "us-senate"), "IA": ("iowa", "us-senate", "president"),
    "NE": ("nebraska", "governor", "us-senate"), "NV": ("nevada", "us-senate", "us-senate"),
    "AK": ("alaska", "us-senate", "president"),
}
NAME = {"us-senate": "Senate", "governor": "Governor", "president": "President"}
# 2024 presidential timelines start at 8 pm ET: first votes from AP's Decision Notes instead
AP_FIRST_2024 = {"GA": 4 / 60, "SC": 19 / 60}


def main():
    d = pd.read_csv(TS)
    out = {}
    for st, (slug, r22, r24) in PICK.items():
        row = {}
        for yr, race in ((2022, r22), (2024, r24)):
            g = d[(d.state == slug) & (d.year == yr) & (d.race == race)].sort_values("hours_after_close")

            def at(p):
                x = g[g.pct_of_final >= p]
                return round(float(x.hours_after_close.iloc[0]), 3) if len(x) else None
            e = dict(race=NAME[race], first=round(max(0.0, float(g.hours_after_close.iloc[0])), 3),
                     h50=at(50), h90=at(90), h95=at(95))
            if yr == 2024 and st in AP_FIRST_2024:
                e["first"] = round(AP_FIRST_2024[st], 3)
            if e["h95"] is None:   # the timeline ended first
                e["end"] = round(float(g.hours_after_close.iloc[-1]), 3)
                e["end_pct"] = round(float(g.pct_of_final.iloc[-1]), 1)
            row[str(yr)] = e
        out[st] = row
    print("const CG_PACE = " + json.dumps(out, separators=(",", ":")) + ";")


if __name__ == "__main__":
    main()
