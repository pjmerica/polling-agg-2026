"""Every published forecast, one row per race per publish, from git history (model repo CONCERNS #20).

    python tools/forecast_history.py [--since 2026-10-01] [--out data/processed/forecast_history.csv]

docs/forecast_data.js is rewritten by every Model refresh and Market refresh run, and each commit
of it holds the model's odds and the market price for every race at that moment. This walks those
commits and writes them as a tidy table, so the post-election edge backtest (model vs market vs
result) is a join on race_id and time instead of digging through the history by hand.

Columns: commit, committed_at (UTC), generated_at, predictions_as_of, race_id, office, state,
district, basis (polls / fundamentals), leader, leader_party, leader_win, dem_win (the DEM-slot
candidates' summed chance), market_prob and market_side (the forecast page's market column: the
Kalshi/Polymarket average for that side), split (models split), fragile.
"""
import argparse
import csv
import json
import os
import subprocess
from datetime import datetime, timezone

FILE = "docs/forecast_data.js"
COLS = ["commit", "committed_at", "generated_at", "predictions_as_of", "race_id", "office", "state",
        "district", "basis", "leader", "leader_party", "leader_win", "dem_win", "market_prob",
        "market_side", "split", "fragile"]


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def payload(commit):
    text = git("show", f"{commit}:{FILE}").decode("utf-8")
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))


def rows(commit, when, p):
    for r in p.get("races", []):
        c = [x for x in r.get("cands", []) if x.get("win") is not None]
        if not c:
            continue
        lead = max(c, key=lambda x: x["win"])
        m = r.get("market") or {}
        yield dict(commit=commit, committed_at=when, generated_at=p.get("generated_at"),
                   predictions_as_of=p.get("predictions_as_of"), race_id=r["id"], office=r.get("office"),
                   state=r.get("state"), district=r.get("district"), basis=r.get("basis"),
                   leader=lead["name"], leader_party=lead["party"], leader_win=lead["win"],
                   dem_win=round(sum(x["win"] for x in c if x["party"] == "DEM"), 4),
                   market_prob=m.get("prob"), market_side=m.get("side"),
                   split=r.get("split") or "", fragile=int(bool(r.get("fragile"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-01")
    ap.add_argument("--out", default="data/processed/forecast_history.csv")
    a = ap.parse_args()
    log = git("log", f"--since={a.since}", "--format=%H %ct", "--", FILE).decode().split("\n")
    commits = [(h, datetime.fromtimestamp(int(t), timezone.utc).isoformat(timespec="seconds"))
               for h, t in (ln.split(" ") for ln in log if ln.strip())][::-1]     # oldest first, UTC
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    n, bad = 0, 0
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for commit, when in commits:
            try:
                p = payload(commit)
            except (subprocess.CalledProcessError, ValueError, KeyError):
                bad += 1          # an older layout or a broken commit: skipped, counted
                continue
            for r in rows(commit[:10], when, p):
                w.writerow(r)
                n += 1
    print(f"{len(commits)} commits of {FILE} since {a.since} ({bad} unreadable) -> {n} rows in {a.out}")


if __name__ == "__main__":
    main()
