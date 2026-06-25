# Changelog

All notable changes to the polling-agg-2026 codebase. Each entry pairs
a short summary with the commit hash so the full diff is reachable via
`git show <hash>`.

**Rule (adopted 2026-06-24)**: every hand-written commit must add an
entry here. Data-refresh commits from the workflow (subjects starting
with `data refresh:`) are autonomous and excluded — they're noise in
this view.

Format: `[hash] commit subject — one-sentence summary of WHY.`

---

## Unreleased

(nothing pending)

---

## 2026-06-24

- *(pending push)* regen: skip non-race-shaped race_ids — first production run of 3ac04c9 succeeded scraping 5955 wikipedia rows but regen crashed on `IndexError: list index out of range` at `race_id.split('-')[2]`. The wikipedia scraper produces `2026-GENERIC` and `2026-APPROVAL` race_ids for nationwide ballot / approval polls, which only have 2 hyphen-separated parts vs the 3+ that polls_data.js's per-race output requires. Added a `len(parts) < 3 → continue` guard before the split. Stage tags (`generic_ballot` / `approval`) still preserved on the rows for a future Raw Polls sub-tab. Wikipedia merge itself was working: 2,135 cross-source dedups, 8,799 polls after dedup — fix unblocks that data shipping.
- `[3ac04c9]` polls: Wikipedia supplement to NYT bulk feed — NYT's bulk house.csv only covers ~86 races (probed live: 2966 rows, of which 2183 are nationwide-ballot rows with state="US", leaving ~783 actual per-district polls — vs ~435 House districts that should be covered). New `scrapers/wikipedia_polls.py` fetches per-state "2026 United States House/Senate/Governor election in <State>" Wikipedia pages, walks `<table class="wikitable">` elements within each `<h3>District N</h3>` section, parses the polling tables (Poll source / Date(s) administered / Sample / MoE / candidate columns). NY-13 smoke test recovers all 3 polls user remembered (Mercury Public Affairs, Data for Progress, Upswing Research). `scripts/regen_data.py` now concats NYT + Wikipedia and dedups on `(race_id, pollster, end_date, candidate)` with NYT winning on conflict — handles within-NYT duplicates from multi-question polls (e.g. with-leaners + without-leaners variants) too. `run_all.py` runs it after the NYT step and treats failure as non-fatal (network/Wikipedia changes don't break the pipeline). `.gitignore` un-ignores `data/raw/wikipedia_polls.csv`. 5-state local smoke test: 1,252 wiki rows / 53 races / 107 pollsters; total dashboard race count went from 137 to 151. Also tags stage='generic_ballot' and stage='approval' for the nationwide pages so a future Raw Polls sub-tab can route them separately. AUDIT to-do #1 (Wikipedia supplement) now done.
- `[0698a26]` polls: archive historical polls, drop cycle filter, add year filter to dashboard — NY-13 polls were missing because (a) NYT pruned them from its bulk house.csv between May and June, and (b) we'd been overwriting the local CSV every run with no archive. Three changes: (1) `.gitignore` un-ignores `data/raw/nyt_polls.csv` so production cron commits it back to the repo, giving the scraper an archive to merge against. (2) `scrapers/nytimes.py` switched to append-mode: read existing CSV, concat with fresh scrape, dedup by `(poll_id, question_id, candidate)`, keep new on conflict. Cycle filter removed so all historical polls flow through. (3) `scripts/regen_data.py` dropped its 2026-only filter (kept the parse-validity filter). (4) `docs/index.html` added a Years dropdown to the Raw Polls tab (default "2025 + 2026", options 2023/2024/2025/2026/All). Confirmed locally: NY-13 reappears with 1 poll; total published races went from 121 to 137 with 85 of them gaining 2025 polls.
- `[22ef3f1]` dashboard: Raw Polls 'Since' default = All time + introduce CHANGELOG.md — user reported polls being dropped when the race was no longer active. Cause was the date-cutoff default at 30 days, not any active-race logic. Switched the default option to All time and matched the JS initial state. Also created CHANGELOG.md and backfilled 2026-06-20 + 2026-06-21 entries.

## 2026-06-21

- `[68ab115]` audit prep: NOTES_FOR_REVIEWER + flag cross-repo drift in AUDIT — added top-level NOTES_FOR_REVIEWER.md. Added prominent "Improvements from pred-arbitrage that should be ported here" section to AUDIT.md with 6 items (real-ASK arb math, freshness guard, last_price display, CLOB freshen, dead-prop filters, cross-repo sync) — flags that this repo is behind pred-arb on those fixes.

## 2026-06-20

- `[ff44692]` audit pass: unify HTTP headers, harden regen_data, debounce search, AUDIT.md — created utils/http_headers.py with BROWSER_UA + DEFAULT_HEADERS + browser_xhr_headers. Migrated 6 files to import from it (kalshi, polymarket, predictit, nytimes, house_incumbents, fetch_depth, scrutiny). Hardened regen_data.py: bare except: → typed, direct pd.read_csv → _safe_read_csv, na=False on str.startswith filter. Removed polymarket.log junk file. Added 150ms debounce on dashboard search inputs.
- `[f48f995]` arb_scanner: candidate-level general-election matching + fee tune — new general_candidate match_type that joins per-candidate general markets across Kalshi/Polymarket/PredictIt on (state, office, district, last, first_initial). Synced FEES from 3%/12%/3% to 2%/12%/2% (matches pred-arb).
- `[70eb245]` arb_scanner: drop inferred-complement fallback — kalshi/polymarket loaders no longer fill a missing Dem/Rep side with 1 - other_side. Inferred prices aren't tradeable; they were inflating arb counts.
- `[fb3848e]` arb_scanner: fix every pair showing as suspicious (bool(NaN) is True) — Python footgun. `bool(float('nan'))` is True because NaN is a non-zero float. Two spots: make_pair's extra dict and the reasons() function. Switched to `is True` and `pd.notna() and ...` checks.

## Earlier

For commits before 2026-06-20, see `git log --before=2026-06-20` and
`AUDIT.md` "Recent work (post-2026-05-15)" section.

---

## How to update this file

When you add a commit:

1. If the entry deserves its own line (most code commits do), add it
   under the dated section for today. Format:
   `` - `[hash]` <commit subject> — <one-sentence WHY> ``
2. Data-refresh commits from the workflow get NO entry. They're
   autonomous.
3. If you're in the middle of a multi-commit feature, add entries to
   the **Unreleased** section at the top and move them under the
   dated section when the feature ships.
