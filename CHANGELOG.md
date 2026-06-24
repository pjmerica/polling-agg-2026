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

- *(pending push)* dashboard: change Raw Polls "Since" default from "Last 30 days" to "All time" — user reported polls being dropped when the race was no longer active. Cause was the date-cutoff default, not any active-race logic. Switched the default option in the dropdown and the JS state initial value to keep older polls visible by default.

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
