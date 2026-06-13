# Handoff — Polling Aggregator & Prediction Markets

**Last updated:** 2026-06-13
**Status:** Live dashboard at https://pjmerica.github.io/polling-agg-2026/.
GitHub Actions runs the full pipeline twice daily (12:00 + 00:00 UTC) and
pushes refreshed `docs/*.js` back to master. Pages auto-redeploys.

If you're picking this up cold, read this top-to-bottom once. The
"Gotchas" section is where most of the weeks-of-pain debugging lives.

---

## What this project does

Aggregates 2026 US election data (Senate, House, Governor) from polling
sources and prediction markets, and surfaces several views in one
dashboard:

| Tab | What it shows |
|---|---|
| **Dashboard** | Per-race summary with implied probability, polling, and source count. |
| **Poll Explorer** | Per-race detail view with the underlying polls and aggregate. |
| **Raw Polls** | Every individual poll. Click a row to filter to that race only. |
| **Polling vs Markets** | Where polling disagrees with prediction-market prices. |
| **Arb Scanner** | Cross-platform price mismatches across Kalshi / Polymarket / PredictIt, with stake sizing and tradeable depth. |
| **Primaries** | 2026 primary calendar from Ballotpedia. Includes type (open/closed/jungle/etc), voting method (FPTP/Runoff/RCV), races on ballot, and runoff date if applicable. |

The sibling repo `pred-arbitrage` is a generalized version of the Arb
Scanner across *every* market category (sports, entertainment, etc.) —
not just elections. Most pipeline-shape fixes here apply there too;
they're kept loosely in sync.

---

## Architecture

### Pipeline (top to bottom — this is what `run_all.py` runs)

```
scrapers/kalshi.py            → data/raw/kalshi_markets.csv
scrapers/polymarket.py        → data/raw/polymarket_markets.csv
scrapers/predictit.py         → data/raw/predictit_markets.csv
scrapers/nytimes.py           → data/raw/nyt_polls.csv
scrapers/house_incumbents.py  → data/processed/house_incumbents.{json,csv}
scrapers/primaries.py         → data/raw/primaries.json + docs/primaries_data.js
scripts/regen_data.py         → docs/data.js + docs/polls_data.js + docs/mismatch_data.js
scripts/arb_scanner.py        → docs/arb_data.js + data/processed/depth_targets.csv
                                (also runs scrutiny.py for >30pp pairs)
scripts/fetch_depth.py        → data/raw/orderbook_depth.csv
scripts/arb_scanner.py        → docs/arb_data.js (re-run, joins depth)
```

The double-run of `arb_scanner.py` around `fetch_depth.py` is
intentional — the scanner emits the depth-target list on pass 1, then
fetch_depth populates the orderbook ladders, then the scanner re-runs
to join depth onto pairs and recompute `suspicion_reasons` /
`criteria_warn` flags that depend on depth data.

### Failure semantics (read this!)

Each scraper raises `SystemExit` if the upstream API returns no usable
rows, which kills `run_all.py` with a non-zero exit code, which causes
the workflow's commit step to be skipped, which means the dashboard
keeps showing the last good data. The HTTP layer in each scraper does
4 retries with 2/4/8s backoff on 403/408/429/5xx/network errors before
raising — so transient blips don't cause this.

`scrapers/primaries.py` is **softer**: if the Ballotpedia calendar
parses to zero matching rows but a prior `docs/primaries_data.js`
exists, it keeps the old data and exits 0. That's because the
Ballotpedia calendar rolls past primaries off as the year progresses,
which legitimately produces zero matches by mid-year — that's not an
outage.

### GitHub Actions

`.github/workflows/refresh.yml`. Schedule: `0 12 * * *` and `0 0 * * *`.
The job:

1. `actions/checkout@v4` — gets the latest master (incl. yesterday's
   tracked `docs/*` and `data/processed/excluded_pairs.json`).
2. `actions/setup-python@v5` + `pip install -r requirements.txt`.
3. `python -u run_all.py`.
4. `git add data/ docs/` + commit + push, with a 3-attempt rebase-retry
   loop to survive race conditions when a manual push lands between
   checkout and push.

The bot's git identity is `github-actions[bot]`. Manual commits from a
maintainer's laptop use whatever local git config is set.

---

## Arb Scanner deep dive

This is the most complex part of the project and where most bugs hide.

### Pair construction (`scripts/arb_scanner.py`)

Two parallel matching paths:

**General-election path.** Joins Kalshi/PredictIt/Polymarket on canonical
`race_id` (e.g. `2026-SEN-PA`). For each race, picks the highest-volume
"Will Dems win X?" / "Will Reps win X?" market per platform, then crosses
them. Computes:

- `raw_gap_pp` — abs difference in implied Dem-win probability.
- `net_gap_pp` — raw gap minus both platforms' fees.
- `arb_type` — `"guaranteed"` if you can buy YES Dem on the cheap
  platform AND buy YES Rep on the expensive platform (or NO Dem,
  equivalently) for a combined cost <1 after fees. Otherwise `"one-sided"`.
- Stake sizing for guaranteed arbs (in `compute_arb_math` /
  `make_pair`).

**Primary-candidate path.** Matches on `(state, office, district, party,
candidate_last, candidate_first)` parsed from market titles —
independent of `race_id`. Catches "Will Zach Wahls be the Democratic
nominee for Senate in Iowa?" priced differently across platforms.
First-initial disambiguation is essential (Chris Sununu vs John E.
Sununu collapsed without it).

### Suspicion + scrutiny pipeline

After both matching paths, each pair runs through several filter layers
in order:

1. **Scraper-time filters** drop unrealistic markets at the source —
   Polymarket markets with liquidity < $200 or bid-ask spread > 20pp get
   dropped before they ever reach the scanner.
2. **Cross-flip safety** (`safe_rep` in `compute_arb_math`) — only
   allows the "1 − P(Rep)" inference for Dem-win probability if the
   same platform's Dem + Rep markets sum to ~1 (within 3pp). This kills
   the 3-way race bug: Nebraska 2026 had Osborn (independent) priced at
   30% on Polymarket, so 1 − P(Rep) ≠ P(Dem), and the cross-flipped
   basket overstated edge by 30pp.
3. **Depth-derived spread filter** (after `fetch_depth`) — pairs where
   either side's live CLOB book has spread > 25pp get dropped. The
   gamma snapshot lags the live book, so this catches stale entries
   that survived (1).
4. **Rules-text scrutiny** (`scripts/scrutiny.py`) — for any pair with
   raw gap > 30pp, fetches both markets' resolution rules and computes a
   text similarity score. <50 dropped, 50–75 tagged `criteria_warn`.
   Plus a hand-curated `data/processed/excluded_pairs.json` for known
   criteria mismatches (Iran nuclear deal is the only entry today;
   Kalshi requires a signed agreement w/ enrichment limits + sanctions
   relief while Polymarket accepts any publicly announced agreement).
5. **Suspicion reasons** — surfaces multiple warning codes
   (`wide_gap`, `wide_spread_a/b`, `one_sided_a/b`, `thin_depth_a/b`,
   `inferred_a/b`, `criteria_warn`) on the dashboard's `⚠ verify`
   badge so the user knows WHY a pair is flagged.

### Fees (round-trip)

`scripts/arb_scanner.py` top:

| Platform | Fee |
|---|---|
| Kalshi | 3% |
| Polymarket | 3% |
| PredictIt | 12% |

Conservative — Kalshi's actual taker fee is 1% each way but real fills
include slippage.

---

## File map

```
.github/workflows/refresh.yml  Daily refresh, schedule + commit logic.

run_all.py                     One-shot entrypoint. Calls each step in order.
requirements.txt               pandas, numpy, requests, beautifulsoup4, lxml, pyyaml.

scrapers/
  kalshi.py            Kalshi v2 trade-api. DO NOT REVERT to v1.
  polymarket.py        gamma-api.polymarket.com. Captures yes_token_id / no_token_id.
  predictit.py         predictit.org/api/marketdata/all/.
  nytimes.py           NYT poll CSVs (Senate/House/Gov).
  house_incumbents.py  Open-seats list (retirements). Read by utils/races.py.
  primaries.py         Ballotpedia calendar + primary-types page. → primaries_data.js.
  fivethirtyeight.py   DEAD STUB — 538 shut down. Don't touch.
  realclearpolitics.py BLOCKED STUB — needs Selenium, low priority.

scripts/
  regen_data.py        Aggregates raw_polls + markets → docs/data.js, polls_data.js,
                       mismatch_data.js.
  arb_scanner.py       The big one. Reads all 3 markets CSVs, produces docs/arb_data.js.
                       Runs twice (pass 1 emits depth targets, pass 2 joins depth).
  fetch_depth.py       Reads depth_targets.csv, fetches Kalshi/Polymarket orderbook
                       ladders, writes orderbook_depth.csv.
  scrutiny.py          Fetches resolution rules + similarity scoring. Caches in
                       data/processed/scrutiny_cache.json (gitignored).

utils/
  races.py             ~511 races with metadata, mapping race_id → state/office/etc.

data/
  raw/                 Scraper outputs (gitignored — regenerated each run).
  processed/
    excluded_pairs.json    Manual scrutiny excludes. TRACKED in git.
    depth_targets.csv      arb_scanner pass-1 output, fetch_depth input.
    scrutiny_cache.json    Gitignored.

docs/                  GitHub Pages site. Tracked.
  index.html           Six-tab dashboard (Dashboard, Poll Explorer, Raw Polls,
                       Polling vs Markets, Arb Scanner, Primaries).
  data.js              Per-race aggregate feed.
  polls_data.js        Raw polls feed.
  mismatch_data.js     Polling-vs-markets feed.
  arb_data.js          Arb pairs feed.
  primaries_data.js    Primaries tab feed (Ballotpedia).
```

---

## Common gotchas (the hard-won list)

**Pipeline shape**
- **GitHub Pages deploys from `/docs` on push to master.** No build step.
- **`data/raw/` is gitignored**, so fresh checkouts have no scraper
  output. Don't write logic that depends on `data/raw/*.csv` existing
  before the scraper runs. Use `_safe_read_csv` everywhere a script
  reads these files — it tolerates missing/empty CSVs.
- **The workflow may race against your local push.** The commit step
  has a rebase-retry loop, but content conflicts on auto-generated
  `docs/*.js` files still produce merge-conflict markers in the file
  (`<<<<<<<`). That broke the Primaries tab once (commit `40ac159`).
  If you're pushing manually during a cron window, rebase and check
  the auto-gen files have no markers.

**Data shapes**
- **Polymarket `yes_token_id` / `no_token_id` are 78-digit ints.**
  Always read with `dtype={"yes_token_id": str, "no_token_id": str}` —
  pandas silently corrupts them to floats in scientific notation
  otherwise, breaking CLOB orderbook lookups. Same for
  `orderbook_depth.csv` and `depth_targets.csv`: use
  `dtype={"market_id": str}`.
- **Kalshi v2 prices are decimals** (0.42 = 42¢). v1 used 0–100. Don't
  mix.
- **PredictIt contract sums often exceed 1.0** because each contract is
  an independent Yes/No bet. A "guaranteed" arb that includes PredictIt
  may be an artifact, not a real arb.
- **Polymarket gamma snapshots lag the live CLOB book.** A market with
  tight gamma quotes can have a wide live book by the time fetch_depth
  polls it. The depth-derived spread filter in arb_scanner.py is the
  backup.
- **Kalshi orderbook semantics.** The `/orderbook` endpoint returns
  `yes_dollars` and `no_dollars` which are stacks of resting BUY
  orders, not asks. Best YES bid = max price in `yes_dollars`. Best
  YES ask = 1 − (max price in `no_dollars`). The earlier interpretation
  (yes_dollars = YES asks) inverted both sides and made every market
  look like a $0.001 + $0.001 guaranteed-99.8%-return basket. Fixed in
  `fetch_depth.py`.

**Matching**
- **Same-surname candidates** (Sununu, Kennedy, Bush) need first-initial
  disambiguation. Already handled in `_first_initial()`.
- **Substring state-name matching catches the wrong state.** Naive
  `for name in STATE_NAME_TO_ABBREV: if name in q` matches "virginia"
  inside "west virginia" because dict iteration is alphabetical. Sort
  longest-first.
- **Surnames that ARE state names.** `_extract_state_office` for
  primary candidates used to scan the whole title for state names. A
  candidate named "Wayne Lonny Washington" running in Oklahoma got
  classified as `race_id=2026-SEN-WA`. Fix: only scan the substring
  AFTER the office anchor word ("Senate" / "Governor" / "House").
- **Polymarket cross-cycle race collisions.** Kalshi ticker
  `SENATEOH-28` (2028 regular cycle) and `SENATEOHS-26` (2026 special)
  both got tagged `2026-SEN-OH`. Fixed by extracting the year from
  `event_ticker` and rejecting non-2026 events; specials get `-S`
  suffix.
- **Polymarket outcomes / outcomePrices come as JSON-encoded strings**,
  not lists. Always `json.loads` them or `zip()` iterates characters and
  silently produces None.

**Broken-book heuristics (the bid-ask spread one)**
- **Polymarket**: drop markets with liquidity < $200 OR spread > 20pp.
- **PredictIt**: drop contracts where `bestBuyYes - bestSellYes > 15pp`
  OR the book is one-sided. PredictIt's API reports the entire
  $0.01–$0.99 range as bid/ask when nothing's trading; midpoint
  averaging produces fictional ~$0.50 prices.
- **Kalshi**: drop markets where `yes_ask - yes_bid > 30pp`. Same
  reasoning.

**Three-way race partition bug**
- Cross-flipping "Will Reps win" → `1 - prob` to compare against "Will
  Dems win" only works in a true 2-way race. With a serious independent
  (e.g. Osborn in NE 2026 at 30%), the basket "YES Dem on A + NO Rep on
  B" does NOT pay $1 in every outcome — it can pay $1 in the Indep
  case (NO Rep wins) but $0 in the Indep case (YES Dem loses). The
  apparent arb is illusory.
- Mitigation: `safe_rep` in `arb_scanner.compute_arb_math` only allows
  the cross-flip when same-platform Dem + Rep prices sum to within 3pp
  of 1.0. Otherwise the pair stays "one-sided" with no guaranteed-arb
  claim.

**Resolution-criteria divergence**
- Same-topic markets can have different resolution criteria. Iran
  nuclear deal: Kalshi requires a signed agreement WITH specific
  enrichment limits + sanctions relief; Polymarket accepts any publicly
  announced agreement. Same gap, different bets.
- Mitigation: `scripts/scrutiny.py` fetches rules text + similarity
  score for any pair > 30pp. Below 50, dropped. 50–75 tagged
  `criteria_warn`. Plus manual `excluded_pairs.json` for known cases.

**Date / cycle**
- **Ballotpedia's calendar rolls past dates off** as the year goes on.
  By mid-summer most state primaries are gone. `primaries.py` is
  written to tolerate this — if calendar parse yields 0 rows and a prior
  `docs/primaries_data.js` exists, keep the old data and exit 0.

---

## Do not

- **Add Claude as co-author on commits.** Plain commits only.
- **Revert Kalshi to v1.** Endpoints stopped returning markets weeks ago.
- **Touch `scrapers/fivethirtyeight.py`.** 538 shut down. Stub stays
  for historical reference.
- **Read `polymarket_markets.csv` without `dtype={"yes_token_id": str,
  "no_token_id": str}`.** Numerical corruption is silent.
- **Hide the `⚠ verify` badge or remove `suspicion_reasons` from the
  dashboard.** The whole point is that the user sees WHY a pair is
  suspect before staking.
- **Replace `_safe_read_csv` with bare `pd.read_csv`.** Scraper outages
  will crash the matcher otherwise.

---

## Recent work (post-2026-05-15)

In rough order:
- **Scraper resilience pass**: `_safe_read_csv` everywhere, fail-fast on
  empty API responses, 4-attempt retry with exponential backoff on
  transient HTTP errors (403/408/429/5xx + network errors).
- **Suspicion + scrutiny pipeline**: dropped suspicious threshold from
  40pp → 20pp, added per-pair `suspicion_reasons` array with detailed
  badges in the dashboard.
- **`scripts/scrutiny.py`**: rules-text similarity scoring for >30pp
  pairs, with hand-curated `excluded_pairs.json` for known
  criteria-mismatch pairs.
- **Cross-flip safety** for 3-way races in `compute_arb_math`.
- **Polymarket / PredictIt broken-book heuristics** at scrape time.
- **State / cycle disambiguation fixes**: surname-state false matches,
  cross-cycle Kalshi tickers.
- **Polling tab UX**: race-click pinning (`rawPinnedRaceId` /
  `rawPinnedStateAbbrev`) with blue banner + "show all polls" escape.
- **Primaries tab** (new): Ballotpedia calendar + state types,
  Type/Method/Races on ballot/Runoff columns, glossary modal, pill
  tooltips. Wired into `run_all.py`.
- **Workflow hardening**: rebase-retry on push, race-condition fixes,
  Node 20 deprecation warning ignored (advisory, not blocking).

---

## Open work / known issues

- **Node 20 deprecation** — GitHub will force Node 24 from June 2026.
  Currently advisory only. Bumping `actions/checkout` and
  `actions/setup-python` to their Node-24-compatible versions before
  then is the fix.
- **`scrapers/realclearpolitics.py`** is a stub blocked by 403. Would
  need a Selenium-based scraper. Low priority.
- **`scrapers/fivethirtyeight.py`** dead — 538 shut down. Stub remains.
- **The Primaries tab's "View polls" link** filters Raw Polls by
  `state_abbrev` (exact match). For a *specific* race within a
  multi-race primary day there's currently no deep-link — the table row
  is the primary, not the race.
- **Pred-arbitrage repo is loosely synced.** Most pipeline-shape fixes
  here are also pushed there, but verify before assuming.

---

## When something breaks at 3am

1. Check **Actions** tab: https://github.com/pjmerica/polling-agg-2026/actions
2. Click the failing run, expand the failing step.
3. **HTTP 403 / network error**: usually transient. Re-trigger via
   "Run workflow." If it recovers, no action needed.
4. **`pandas.errors.EmptyDataError`** or `KeyError: 'implied_prob'`:
   one of the CSVs is empty/missing. Check which scraper raised. Most
   likely a real upstream outage — wait for the next cron.
5. **Merge-conflict markers (`<<<<<<<`) in a `docs/*.js` file**: pull
   master, re-run the relevant scraper locally, push the clean file.
6. **`Ballotpedia returned no primary rows AND no prior data`**:
   means the calendar AND the tracked `docs/primaries_data.js` are
   both gone. Restore primaries_data.js from a previous commit.
