"""Run all scrapers, regen, and arb scanner (with depth) in sequence.

Modes:
  py run_all.py                 full pipeline (markets + polls + primaries)
  py run_all.py --markets-only  market scrapers + arb scan only (~2-3 min).
                                Used by the fast market-refresh workflow so
                                arb_data.js updates every 2h without paying
                                for the polls scrape each time.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

MARKET_STEPS = [
    ("Kalshi scraper",       [sys.executable, "scrapers/kalshi.py"]),
    ("Polymarket scraper",   [sys.executable, "scrapers/polymarket.py"]),
    ("PredictIt scraper",    [sys.executable, "scrapers/predictit.py"]),
]

POLL_STEPS = [
    ("NYT polls scraper",    [sys.executable, "scrapers/nytimes.py"]),
    # Wikipedia is a supplement to NYT. NYT bulk feed only carries
    # ~86 races and prunes per-district House polls over time;
    # Wikipedia state pages have comprehensive per-district tables.
    # regen_data.py merges both with NYT winning on conflict.
    ("Wikipedia polls",      [sys.executable, "scrapers/wikipedia_polls.py"]),
    ("House incumbents",     [sys.executable, "scrapers/house_incumbents.py"]),
    ("Ballotpedia primaries",[sys.executable, "scrapers/primaries.py"]),
    ("Regen aggregated data",[sys.executable, "scripts/regen_data.py"]),
]

ARB_STEPS = [
    ("Arb scanner (pass 1)", [sys.executable, "scripts/arb_scanner.py"]),
    ("Fetch orderbook depth",[sys.executable, "scripts/fetch_depth.py"]),
    ("Arb scanner (pass 2)", [sys.executable, "scripts/arb_scanner.py"]),
]

if "--markets-only" in sys.argv:
    steps = MARKET_STEPS + ARB_STEPS
else:
    steps = MARKET_STEPS + POLL_STEPS + ARB_STEPS

# Steps that are best-effort supplements rather than critical sources.
# A failure here logs a warning and continues; downstream steps will
# fall back to whatever's already on disk.
NON_FATAL = {"Wikipedia polls"}

# INDEPENDENT SOURCES: one venue going down must not stop the others from being
# scraped. These used to sys.exit() on the first failure, so a Kalshi 403 (its WAF
# blocks past the full 5->60s retry budget a couple of times a week) meant Polymarket
# was never scraped either and the dashboard held BOTH venues' prices until the next
# run ~2h later. Now a failure here is recorded, the remaining steps still run, and
# the run still exits non-zero at the end so CI shows red.
DEFERRED_FAIL = {"Kalshi scraper", "Polymarket scraper"}

failures = []
for name, cmd in steps:
    print(f"\n{'='*60}\n{name}\n{'='*60}", flush=True)
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        if name in NON_FATAL:
            print(f"WARN: {name} failed with exit code {result.returncode} (non-fatal, continuing)", flush=True)
            continue
        if name in DEFERRED_FAIL:
            print(f"ERROR: {name} failed with exit code {result.returncode} "
                  f"(continuing so the other venue still refreshes; run will exit non-zero)",
                  flush=True)
            failures.append((name, result.returncode))
            continue
        print(f"ERROR: {name} failed with exit code {result.returncode}", flush=True)
        sys.exit(result.returncode)

if failures:
    print(f"\nFAILED: {', '.join(n for n, _ in failures)}", flush=True)
    sys.exit(failures[0][1])

print("\nAll done.", flush=True)
