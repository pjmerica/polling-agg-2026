# Code Audit & To-Do — polling-agg-2026

**Created:** 2026-06-20
**Scope:** every tracked file in the repo (scrapers, scripts, utils, docs,
infra, root). Companion file lives at `pred-arbitrage/AUDIT.md` covering
the sibling repo.

This is a working document. As issues get fixed, move them out of the
**To-do** section at the bottom and into the **Done** section, with the
commit hash so we can find what changed.

---

## Major design decisions (not bugs — for context)

These are choices that affect how the rest of the audit reads. Don't
"fix" any of these without thinking about the second-order consequences.

- **Three sources of arb truth coexist.** `match_type: general` (party-
  level Dem/Rep), `match_type: general_candidate` (per-candidate general
  market), and `match_type: primary_candidate` (per-candidate primary
  market). Each has its own loader + pair function in
  `scripts/arb_scanner.py`. The frontend treats them uniformly.
- **The scanner is run twice.** Pass 1 emits `depth_targets.csv` →
  `fetch_depth` populates orderbook ladders → pass 2 joins depth and
  applies depth-derived spread filters. Don't try to collapse into one
  pass without rewiring how `depth_targets.csv` is built.
- **Fail-fast scrapers + skipped commit step.** If any scraper returns
  zero usable rows, `run_all.py` exits non-zero, the workflow's
  `git add data/ docs/` produces an empty diff, the commit step is
  skipped, and the live dashboard keeps the last good snapshot.
  Ballotpedia's primaries scraper is the one explicit exception (it
  tolerates empty calendars late in the cycle).
- **Inferred-complement was ripped out (2026-06-18).** Loaders no longer
  fill a missing Dem/Rep side with `1 - other_side`. Inferred prices
  aren't tradeable. See `HANDOFF.md` "Do not" list before adding it back.
- **The `FEES` dict is the single source of truth.** Kalshi 2%,
  Polymarket 2%, PredictIt 12%. Frontend reads from `arb_data.js`'s
  `fees` field — don't hard-code anywhere else.

---

## Inventory + per-file notes

Lines are post-fixes from this audit. Smells flagged below; see To-do
section for what was already cleaned vs left.

### Scrapers (`scrapers/`)

| File | LOC | Status | Notes |
|---|---|---|---|
| `__init__.py` | 0 | empty | leave it |
| `kalshi.py` | ~325 | **live, healthy** | Uses `browser_xhr_headers("https://kalshi.com")` after WAF-hardening. 6-retry exponential backoff with 60s cap. Complex `infer_race_id` regex chain — 8 patterns; risky to refactor without a full test sweep. |
| `polymarket.py` | ~375 | **live, healthy** | Uses `DEFAULT_HEADERS`. Pagination via `offset`. Token IDs are 78-digit strings — always read CSV with `dtype={"yes_token_id": str, "no_token_id": str}`. Two `except Exception` blocks on JSON parse of `outcomes` / `outcomePrices` — those fields are JSON-encoded strings; the swallow is acceptable but logs nothing. |
| `predictit.py` | ~220 | **live, healthy** | Uses `DEFAULT_HEADERS`. Single-call REST endpoint. Drops rows with bid-ask spread > 15pp (`SPREAD_THRESHOLD` constant) — that's the broken-book heuristic. |
| `nytimes.py` | ~250 | **live, healthy** | Uses `BROWSER_UA`. Two `except Exception` blocks on date parse — acceptable; dates from CSV have multiple formats. `parse_iso` falls through to empty string. |
| `house_incumbents.py` | ~228 | **live, healthy** | Uses `DEFAULT_HEADERS`. Hits Ballotpedia + the unitedstates/congress-legislators YAML on GitHub Raw. Output read by `utils/races.py` at import time. |
| `primaries.py` | ~434 | **live, healthy** | Already had real-browser UA. Tolerates 0-row scrape (keeps prior `docs/primaries_data.js`). |
| `fivethirtyeight.py` | 99 | **dead stub** | 538 shut down in 2026-04. File raises `NotImplementedError`. Kept for reference. Audit recommends deleting after 2026-12 if not revived. |
| `realclearpolitics.py` | 126 | **dead stub** | RCP blocks programmatic access (403). All functions `NotImplementedError`. Same recommendation as 538. |

### Scripts (`scripts/`)

| File | LOC | Status | Notes |
|---|---|---|---|
| `arb_scanner.py` | ~1,310 | **live, hot path** | The longest file in the repo. Three matching paths, depth-aware suspicion flags, rules-text scrutiny escalation. **Audit recommendation: break into 3-4 files (`loaders.py`, `pair_builders.py`, `suspicion.py`, `cli.py`)** but not as a quick fix — needs a careful refactor pass. |
| `regen_data.py` | ~175 | **live, hardened in this audit** | Was a top-level script (no `main()` guard); ran at import. Now uses `_safe_read_csv` for all 3 CSV reads, narrowed bare `except:` to typed exceptions, added `na=False` to `str.startswith` guard. |
| `fetch_depth.py` | ~195 | **live, healthy** | Uses `DEFAULT_HEADERS`. `_http_json` swallows exceptions and returns None — caller handles None correctly. |
| `scrutiny.py` | ~195 | **live, healthy** | Uses `DEFAULT_HEADERS`. Caches rules text for 7 days. SequenceMatcher-based similarity scoring. PredictIt rules fetch is a no-op — there's no public endpoint for it. |

### Utils (`utils/`)

| File | LOC | Status | Notes |
|---|---|---|---|
| `__init__.py` | 0 | empty | leave it |
| `races.py` | ~722 | **live, healthy** | 35 Senate + 36 Governor + 435 House race definitions. `HOUSE_KNOWN_OPEN` is a hand-curated list of 31 open seats — gets re-derived from `house_incumbents.py` output when present. One acceptable `except Exception` on the JSON load. |
| `http_headers.py` | 54 | **new in this audit** | Single source of truth for HTTP headers across every scraper. `BROWSER_UA`, `DEFAULT_HEADERS`, `browser_xhr_headers(origin)`. If a WAF blocks us again, change one constant. |

### Analysis (`analysis/`)

| File | LOC | Status | Notes |
|---|---|---|---|
| `__init__.py` | 0 | empty | leave it |
| `aggregator.py` | 237 | **orphan** | Not imported by anything. References `rcp_polls.csv` which doesn't exist. **Audit recommendation: keep for now** — the planned Model vs Markets work may use it as a starting point. If not used by 2026-09, delete. |

### Models (`models/`)

Currently an empty package (`__init__.py`). This is where the Model vs
Markets tab will live; see the "Planned work" section.

### Notebooks (`notebooks/`)

Untracked. Local-only experimentation.

### Docs (`docs/`)

| File | LOC | Status | Notes |
|---|---|---|---|
| `index.html` | ~1,680 | **live, hot** | Inline JS, no bundler. Reads `RACES`, `POLLS`, `MISMATCH`, `ARB`, `PRIMARIES`, `RACES_BY_STATE` globals. ~25 `innerHTML` writes — XSS surface if a market title gets adversarial. Search debounce added in this audit. |
| `polls.html` | 279 | **orphan?** | Standalone page that imports `polls_data.js`. Not linked from `index.html`. Audit suggests checking whether it's deployed and used. |
| `*_data.js` | generated | tracked but auto-built | `data.js`, `polls_data.js`, `mismatch_data.js`, `arb_data.js`, `primaries_data.js`. Committed by the daily refresh workflow. |

### Infra

| File | Status | Notes |
|---|---|---|
| `run_all.py` | clean | Hard-coded step list, fail-fast on first non-zero exit. |
| `requirements.txt` | **unpinned** | 6 packages, no versions. `pandas`, `numpy`, `requests`, `beautifulsoup4`, `lxml`, `pyyaml`. **Audit recommendation: pin** — a breaking change in pandas would silently break the cron. |
| `.github/workflows/refresh.yml` | clean | 12:00 + 00:00 UTC cron, `workflow_dispatch` for manual runs, retry-with-rebase commit loop. Node 24 forced runtime. |
| `LICENSE` | clean | All-rights-reserved. |
| `README.md` | clean | Updated 2026-06-13. |
| `HANDOFF.md` | clean | Updated 2026-06-18 with three-matching-paths + fee change + bool(NaN) gotchas. |
| `.gitignore` | hardened in this audit | Added `*.log` after a stray `polymarket.log` was found tracked. |

---

## Bugs and risks worth tracking

### Latent regressions (high signal-to-noise)

1. **HTTP header drift** — fixed in this audit. Six files used to have
   their own `HEADERS = {"User-Agent": "...(research/polling-aggregator)"}`
   constant; updating Kalshi's UA in June 2026 left them all out of sync
   and was a latent regression of the bug we'd just spent a day fixing.
   Now everyone imports from `utils/http_headers.py`.
2. **`bool(NaN) is True` footgun** — already documented in HANDOFF.
   Audit scan found no other live offenders in either repo.
3. **Inferred-complement reintroduction** — already in HANDOFF "Do not"
   list. Watch for someone re-adding a "fill the missing side" branch
   to a loader.
4. **Fee drift between repos** — was already drifted (polling-agg 2%,
   pred-arb 3%) at audit time. Fixed in this pass. No automated check
   to keep them in sync — consider a `tests/test_cross_repo.py` or a
   shared `FEES.json` if the two stay coupled.

### Defensive coverage gaps

1. **`docs/polls.html` is an orphan** — verify it's actually served
   from Pages or remove it. (To check, hit
   `https://pjmerica.github.io/polling-agg-2026/polls.html` — if 404,
   delete.)
2. **`analysis/aggregator.py`** — orphan code, references nonexistent
   `rcp_polls.csv`. Either revive (likely as part of Model vs Markets)
   or delete.
3. **`requirements.txt` is unpinned.** A pandas 3.0 release with API
   breaks would silently break the daily refresh.
4. **`polymarket.py` swallows JSON parse errors silently** at lines
   ~214 (in `outcomes` / `outcomePrices` decode). If the gamma API
   changes that field's shape we'd see rows with empty prices and no
   indication of why. Consider logging the offending row id.
5. **Polymarket gamma snapshots lag the live CLOB book.**
   `fetch_depth` is the mitigation. Audit didn't find any path where a
   stale gamma price drives stake sizing without depth.

### Low-priority cleanup

1. **`scripts/arb_scanner.py` is 1310 lines.** Split into 3-4 files.
   Not urgent; the logic is well-commented.
2. **`scripts/regen_data.py` runs at import.** Wrap in `if __name__ ==
   "__main__":` so the file can be imported by tests.
3. **Bare/broad exception blocks** — 7 found in audit, all narrowed or
   noted in this pass. Future refactor: replace `except Exception:`
   that swallow with `print(..., file=sys.stderr)` calls.
4. **No tests anywhere.** Cron is the only safety net. Even a single
   `tests/test_smoke.py` that runs each scraper's first 5 rows through
   the matcher would catch shape regressions.

### Security surface (small but present)

1. **`innerHTML` writes in `docs/index.html`.** Market titles,
   candidate names, and poll questions flow into the DOM via
   `innerHTML`. If an attacker could inject HTML into a Kalshi market
   title (they can't directly — those titles are platform-curated),
   it'd render in our dashboard. Low risk; mitigation is to use
   `textContent` for fields we trust to be plain text.
2. **No auth on the dashboard.** Public read-only site, no user data.
   Acceptable.
3. **GitHub Actions has `contents: write` only.** No secrets used,
   no third-party tokens. Minimal blast radius.

---

## Planned work tracker

### Model vs Markets tab (NEW, replacing Polling vs Markets)

User is building a probabilistic model that will produce per-race
implied probabilities. Once ready, it will replace the existing
Polling vs Markets tab. Concrete steps when ready:

- [ ] Add `models/` package that exports a `predict(race_id) ->
      {dem_prob, rep_prob, confidence, last_updated}` interface.
- [ ] Add `scripts/regen_model.py` that runs the model over all
      `RACE_BY_ID` and writes `docs/model_data.js`.
- [ ] Hook into `run_all.py` after `regen_data` but before
      `arb_scanner` (so the model output is fresh when the dashboard
      reloads).
- [ ] Replace the existing Polling vs Markets tab in `docs/index.html`
      (tab id + render function — search for `MISMATCH` references).
      Keep the existing tab functional until the model is wired.
- [ ] Update HANDOFF.md "What this project does" to describe the new
      tab.
- [ ] Update README.md "What it shows" similarly.

Don't delete `mismatch_data.js` generation in `regen_data.py` until the
model tab is live and stable; that file is still feeding the current
tab.

---

## To-do (open)

Highest leverage first. Each item is a self-contained piece of work.

1. **Decide on `docs/polls.html`.** Either link it from `index.html` as
   a dedicated Poll Explorer URL (it already exists) or delete it.
2. **Pin `requirements.txt`.** Use the versions from the GHA runner's
   pip cache as the floor: `pandas>=2.2,<3.0`, `numpy>=2.0,<3.0`,
   `requests>=2.31`, `beautifulsoup4>=4.12`, `lxml>=5.0`, `pyyaml>=6.0`.
3. **Add a smoke test.** One file, runs in <30s in CI: invoke each
   scraper with `--limit 5` (need to add the flag), assert the CSV
   shape, run the matcher on the truncated data, check `arb_data.js`
   has at least one row. Add a `tests` job to the workflow that runs
   on PR.
4. **Triage `analysis/aggregator.py`.** Either revive as part of Model
   vs Markets prep or delete.
5. **Delete the dead stubs (`fivethirtyeight.py`, `realclearpolitics.py`)
   if 538/RCP haven't come back online by 2026-12.**
6. **Wrap `regen_data.py` in `if __name__ == "__main__":`.** Top-level
   script execution makes it un-importable.
7. **Log silently-swallowed JSON parse failures in `polymarket.py`.**
   Add a `print(f"WARN: skipped market {row.get('id')}: {e}",
   file=sys.stderr)` to each `except Exception:` block.
8. **Refactor `scripts/arb_scanner.py` (1310 LOC) into multiple
   files.** Suggested split: `loaders.py` (lines 71-233 ish),
   `arb_math.py` (compute_arb_math), `pair_builders.py` (make_pair,
   primary_pairs, general_candidate_pairs), `suspicion.py` (reasons
   function + scrutiny merge), `cli.py` (run() + main).
9. **Switch trusted-text writes in `docs/index.html` from
   `innerHTML` to `textContent`.** Only do this for fields where the
   value is known plain text (candidate, label, state, office). Leave
   `innerHTML` where we intentionally inject HTML (badges, links).
10. **Add a shared cross-repo check.** Either a `tests/` directory in
    one repo that points to both, or a CI step that fails if
    `polling-agg/scripts/arb_scanner.py:FEES !=
    pred-arbitrage/scripts/arb_scanner.py:FEES`. Same for the headers
    file.
11. **Document `models/` placeholder.** Add a README in `models/`
    explaining the planned interface.

---

## Done (in this audit pass)

Commit hash to be filled at push time.

- Created `utils/http_headers.py` with `BROWSER_UA`, `DEFAULT_HEADERS`,
  `browser_xhr_headers(origin)`. Single source of truth for outbound
  request headers.
- Migrated six files to import from it: `scrapers/kalshi.py`,
  `scrapers/polymarket.py`, `scrapers/predictit.py`, `scrapers/nytimes.py`,
  `scrapers/house_incumbents.py`, `scripts/fetch_depth.py`,
  `scripts/scrutiny.py`. All seven now send the same real-browser UA.
  (Earlier in this audit pass, six of them still leaked the old
  `(research/polling-aggregator)` UA that triggered the Kalshi WAF — a
  latent regression of a bug we'd just spent a day fixing.)
- Hardened `scripts/regen_data.py`:
  - Switched three direct `pd.read_csv` calls to a local
    `_safe_read_csv` wrapper.
  - Narrowed two bare `except:` blocks to typed exceptions in
    `parse_iso`.
  - Added `na=False` to the `str.startswith('2026')` mask so NaN
    end_dates don't blow up the filter.
  - Added an early-exit when Kalshi data is missing so the
    mismatch-data generation step doesn't crash.
- Removed `polymarket.log` from tracking (1-line junk file).
- Added `*.log` to `.gitignore`.
- Added debounce on the three search input handlers in
  `docs/index.html` (`#search`, `#p-search`, `#raw-search`). 150ms
  delay; numeric filters left as-is.
