"""Dry run of the election-night dashboard on 2024's count.

Replays the Internet Archive's 2024 election-night NYT files (fetch_wayback_full.py; the presidential race in
each state with a 2026 race) through live_project.py in time order, as if they were Tuesday's captures, and
writes the dashboard's data file after each step. Open dashboard.html while it runs.

Everything goes to data/raw/dryrun/ (NYT files, projections.csv), never to the real capture folders. The
market books are today's: copy a real capture (capture_markets.py --once) with its times moved before the
2024 poll closes. So prices don't move, and best buys and FLIPs mean nothing here: this checks the plumbing
and the page, not the edge. 2024 county leans differ from 2026 races' benchmarks, so expect large "over/under"
numbers too.

    py "Election night simulator/scripts/dry_run.py"              # ~100 steps, 2 s apart
    py "Election night simulator/scripts/dry_run.py" --pause 0    # as fast as it goes
    py "Election night simulator/scripts/dry_run.py" --pause 0 --until 2024-11-06T05:30   # stop mid-count
"""
import argparse
import glob
import gzip
import json
import os
import shutil
import sys
import time
from types import SimpleNamespace

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import live_project as lp  # noqa: E402

DATE = "2024-11-05"
FULL = os.path.join(ROOT, "data", "raw", "wayback_full", "2024")
DRY = os.path.join(ROOT, "data", "raw", "dryrun")
REAL_MARKETS = lp.MARKETS


def snapshots():
    """{state slug: [(timestamp, the presidential race dict)]} from the 2024 archive."""
    out = {}
    for race in lp.RACES:
        slug = lp.ABBR[race.split("-")[0]]
        if slug in out:
            continue
        snaps = []
        for p in sorted(glob.glob(os.path.join(FULL, slug, "*.json.gz"))):
            try:
                d = json.load(gzip.open(p))
            except (OSError, ValueError):
                continue
            for r in d.get("races") or []:
                if r.get("office") == "President" and r.get("race_type_id") in (None, "G") \
                        and r.get("reporting_units") and r.get("top_reporting_unit"):
                    snaps.append((os.path.basename(p)[:14], r))
                    break
        out[slug] = snaps
    return out


def market_files():
    """Today's real market capture, re-dated before the 2024 poll closes, -> data/raw/dryrun/markets."""
    days = sorted(glob.glob(os.path.join(REAL_MARKETS, "20*")))
    dst = os.path.join(DRY, "markets", DATE)
    os.makedirs(dst, exist_ok=True)
    if not days:
        print("no market capture yet: run capture_markets.py --once first (the dashboard works without one)")
        return
    for venue in ("kalshi", "polymarket"):
        p = os.path.join(days[-1], f"{venue}.csv")
        if os.path.exists(p):
            df = pd.read_csv(p)
            df = df[df.ts_utc == df.ts_utc.max()]
            df["ts_utc"] = f"{DATE}T22:00:00Z"
            df.to_csv(os.path.join(dst, f"{venue}.csv"), index=False)
    print(f"markets: {os.path.basename(days[-1])}'s last pass")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between steps")
    ap.add_argument("--until", help="stop at this UTC time, e.g. 2024-11-06T05:30 (a mid-count moment)")
    a = ap.parse_args()
    shutil.rmtree(DRY, ignore_errors=True)
    lp.LIVE = os.path.join(DRY, "live")
    lp.MARKETS = os.path.join(DRY, "markets")
    lp.OUT = os.path.join(DRY, "projections.csv")
    snaps = snapshots()
    market_files()
    steps = sorted({ts for s in snaps.values() for ts, _ in s})
    if a.until:
        stop = pd.Timestamp(a.until, tz="UTC").strftime("%Y%m%d%H%M%S")
        steps = [t for t in steps if t <= stop]
    print(f"{len(steps)} steps, {sum(len(s) for s in snaps.values())} snapshots in {len(snaps)} states")
    hist, fc = lp.load_history(), lp.load_forecast()
    args = SimpleNamespace(date=DATE, race=None, pct=None, margin=None, prior_sd=lp.PRIOR_SD,
                           baseline="market", dry_run="2024 presidential count replayed (" +
                           ", ".join(sorted(snaps)) + ")")
    written = {}
    for t in steps:
        for race in lp.RACES:
            slug = lp.ABBR[race.split("-")[0]]
            cur = [s for s in snaps[slug] if s[0] <= t]
            if not cur or written.get(race) == cur[-1][0]:
                continue
            ts, r = cur[-1]
            d = os.path.join(lp.LIVE, DATE, race)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f"{ts[:8]}T{ts[8:]}Z.json.gz")
            with gzip.open(p, "wt", encoding="utf-8") as f:
                json.dump({"races": [r]}, f)
            when = pd.Timestamp(ts, tz="UTC").timestamp()
            os.utime(p, (when, when))              # the file's time is the snapshot's, as if just captured
            written[race] = ts
        args.now = pd.Timestamp(t, tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")     # the replay's clock
        lp.run_live(args, hist, fc)
        time.sleep(a.pause)
    print("\ndone: the dashboard shows the last step")


if __name__ == "__main__":
    main()
