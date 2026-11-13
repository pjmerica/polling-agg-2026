# Handoff: Polling Aggregator and Prediction Markets

**Last updated:** 2026-11-12 (rewritten as a current-state guide; the April to October
version is [history/HANDOFF_2026-04_to_10.md](history/HANDOFF_2026-04_to_10.md))
**Live:** https://pjmerica.github.io/polling-agg-2026/ (GitHub Pages from `docs/` on `master`)

Other docs:
- [CHANGELOG.md](CHANGELOG.md): every hand-written change and why.
- [history/](history/): the old handoff and the July to September audits.
- Each project folder below has its own README.
- `Documents/AGENTS.md` (outside this repo): the rules that apply to this repo, pred-arbitrage
  and the model repo, and the list of work still open.

---

## 1. Where things stand (2026-11-12)

The election was Nov 3. The forecast is frozen and the count is still being recorded.

- **The forecast is the record.** The tag `forecast-before-polls-2026` and the release
  `forecast-2026-11-03-6pm-et` hold what was published before the count. No margin or win
  number has changed since 19:30 UTC on Nov 3. Do not re-publish a forecast for 2026.
- **The three refresh workflows are switched off** (Daily refresh, Market refresh, Model
  refresh; disabled 2026-11-12). The election markets settled, the arb board is empty and
  there are no new polls. To run one again: `gh workflow enable "Market refresh"`.
- **The recording jobs run until mid-December** (table below). Do not stop them, and do not
  queue enough other jobs to hit GitHub's 20-job limit: a queued hand-off leaves a gap in the
  vote record.
- **Still to do after the count:** the model evaluation, the 2026 replay, results on the
  pages. `Documents/AGENTS.md` "Still open" has the list.
- **Alaska (fixed 2026-11-12 evening).** Its precinct results had not been recorded since
  Nov 5: Alaska's server failed certificate checks from Linux until that evening, and the
  watched address was a guess that answers 403. The recorder now reads Alaska's results page
  and fetches a missing issuer certificate itself (`Precinct data 2026/README.md`). Alaska runs
  its ranked-choice rounds on **Nov 18**: NYT's totals then become the final round, so check
  the desk and the House page that day. The other states' precinct addresses were never checked
  in a browser; a logged 403 may be a wrong address, not a refusal.

### Workflows

| Workflow | State | What it does |
|---|---|---|
| `election-night.yml` "Election night (cloud)" | running to Dec 15 | `Election night simulator/scripts/cloud_night.py`: NYT counts, 435 district files, both venues' books and the projector, every 30 minutes. State on the orphan branch `election-live` (`status.json` shows the last pass); the archive goes to the release `election-night-2026` each hour. Each job dispatches the next; the cron is the backstop, so cancelled scheduled runs are normal. |
| `precinct-record.yml` "Precinct record" | running to Dec 15 | `Precinct data 2026/`: precinct results and ballot returns for all 50 states, saved when they change, to the same release. |
| `market-archive.yml` "Market archive" | manual | Price history for every Kalshi and Polymarket election market. Re-run once after the count with a new label, one venue at a time. Never delete a superseded copy. |
| `save-6pm-copy.yml` | done (Nov 3) | Made the 6 p.m. Election Day release. |
| `refresh.yml` "Daily refresh" | **off** | Full pipeline (`run_all.py`): polls, markets, arb scan. Was 00:00 and 12:00 UTC. |
| `market-refresh.yml` "Market refresh" | **off** | Markets and arb scan only. Was :41 on odd hours. |
| `model-refresh.yml` "Model refresh" | **off** | Clones the model repo, re-predicts, rebuilds the forecast. Ran after each Daily refresh. |

The three refresh workflows share `concurrency: group: refresh`, run `tests/` before the
pipeline and the dashboard smoke tests after it, and end by checking that Pages serves the
commit (`tools/verify_pages.py`, which also asks GitHub for a rebuild if the Pages build never
ran). GitHub starts this repo's crons late, sometimes by hours.

Two sibling repos record their own pages through Dec 14: `pjmerica/house-night-2026` (every
House race) and `pjmerica/mississippi-night-2026`.

### On the owner's PC

- `StateResults-LateCount` (Windows task): `State election results/scripts/capture_live.py`
  every 30 minutes to Nov 26, a second copy of NYT's files. Since 2026-11-12 the task starts
  again every 30 minutes and at logon if it is not running; before that a restart ended it,
  and Nov 5 to 10 were not captured on the PC.
- `Election night simulator/scripts/archive_download.py`: a read-only local copy of the
  release and git bundles of the four repos. Re-run it while recording continues and once after.
  It does not bundle the model repo or pred-arbitrage yet.
- Remove the `StateResults-*` tasks after Nov 26 (`State election results/README.md`).

### Project folders

| Folder | What it is | Start at |
|---|---|---|
| `scrapers/`, `scripts/`, `analysis/`, `utils/`, `tools/`, `tests/` | The dashboard pipeline (sections 2 to 4) | this file |
| `docs/` | The Pages site | list below |
| `Election night simulator/` | The live projector, the cloud desk, the 2024 replay, the market archive | its `README.md`, `METHODS.md` |
| `State election results/` | How each state counts and reports; county benchmarks; the local capture | `MASTER.md` |
| `Precinct data 2026/` | The precinct record | `README.md` |

### Pages in `docs/`

| Page | Shows | Built by |
|---|---|---|
| `index.html` | Model vs Markets (general, primary), Poll Explorer, Raw Polls, Arb Scanner, Primaries | `scripts/regen_data.py`, `scripts/arb_scanner.py`, `analysis/model_compare*.py` |
| `predictions.html` | The forecast for every race, with the explainer | `scripts/build_forecast.py` -> `forecast_data.js` |
| `map.html` | The forecast map: Margin, Win %, Model vs markets | reads `forecast_data.js` + `data.js` |
| `polls.html`, `primaries-vs-markets.html` | Poll explorer; primaries against markets | the pipeline |
| `election-night.html` | The state-by-state counting guide | `State election results/scripts/build_election_night.py` |
| `election-night-desk.html`, `election-night-cloud.html` | The live desk and dashboard, reading `election-live` | `Election night simulator/scripts/build_cloud_pages.py` |
| `election-night-replay.html` | The 2024 replay | `replay_2024.py --publish` |
| `election-night-live.html` | A delayed public copy, last updated Oct 30 | by hand |

`map.html` and `predictions.html` are mirrored on ezdubsanalytics.com (section 6).

### Rules

- **Plain commits. No Claude co-author line.** Every hand-written commit gets a CHANGELOG entry.
- Python is `py` on the owner's machine.
- Old versions are archived, never deleted (replays, market archives, published pages).
- Every variable shown on a page is defined on that page (`GLOSS` in `map.html`).
- The explainer script is one block, byte-identical in `predictions.html` and `map.html`
  (`tests/test_explainer_shared.py`).

---

## 2. The dashboard pipeline

`run_all.py` runs these in order (`--markets-only` skips the poll scrapers):

```
scrapers/kalshi.py            -> data/raw/kalshi_markets.csv
scrapers/polymarket.py        -> data/raw/polymarket_markets.csv
scrapers/predictit.py         -> data/raw/predictit_markets.csv
scrapers/nytimes.py           -> data/raw/nyt_polls.csv
scrapers/wikipedia_polls.py   -> data/raw/wikipedia_polls.csv
scrapers/house_incumbents.py  -> data/processed/house_incumbents.{json,csv}
scrapers/primaries.py         -> data/raw/primaries.json + docs/primaries_data.js
scripts/regen_data.py         -> docs/data.js + docs/polls_data.js + docs/mismatch_data.js
scripts/arb_scanner.py        -> docs/arb_data.js + data/processed/depth_targets.csv
scripts/fetch_depth.py        -> data/raw/orderbook_depth.csv
scripts/arb_scanner.py        -> docs/arb_data.js (second pass, joins depth)
```

The scanner runs twice on purpose: pass 1 lists the books to fetch, `fetch_depth.py` fetches
them, pass 2 reprices every basket on the live books.

**Failure semantics.** Each scraper raises `SystemExit` when the upstream API returns no usable
rows, which stops `run_all.py`, which skips the commit, so the site keeps its last good data.
The HTTP layer retries 4 times (2/4/8 s) on 403/408/429/5xx and network errors first.
`scrapers/primaries.py` is softer: Ballotpedia's calendar drops past primaries, so an empty
parse with an existing `docs/primaries_data.js` keeps the old data and exits 0. With no open
election market (after Nov 4 2026) the scanner writes an empty board instead of failing.

**Other files.** `utils/races.py` is the one list of races (race_id, state, office).
`utils/election_shapes.py` and `utils/fees.py` are identical copies of pred-arbitrage's.
`analysis/margin_markets.py` reads both venues' margin markets. `tools/linkcheck.py` re-derives
and repairs market links; `tools/health.py` keeps the "Board health" issue.
`scrapers/fivethirtyeight.py` and `scrapers/realclearpolitics.py` are dead stubs.

---

## 3. Arb Scanner deep dive

This is the most complex part of the project and where most bugs hide.

### Pair construction (`scripts/arb_scanner.py`)

Three parallel matching paths. Each emits rows with a different
`match_type` so the dashboard can present them distinctly:

**1. General-election party path** (`match_type: "general"`). Joins
Kalshi/PredictIt/Polymarket on canonical `race_id` (e.g. `2026-SEN-PA`).
For each race, picks the highest-volume "Will Dems win X?" / "Will Reps
win X?" market per platform, then crosses them. Computes:

- `raw_gap_pp` — abs difference in implied Dem-win probability (DISPLAY
  prices; never used in basket math).
- `net_gap_pp` — raw gap minus both platforms' fees.
- `arb_type` — `"guaranteed"` (since 2026-07-03) means: Buy Dem-YES on one
  platform at the real ASK + Buy Dem-NO on the other at the real NO-ASK
  for combined cost < $1 after fees, with net return > 0.25%, using REAL
  quotes on both legs (Kalshi NO = 1 − yes_bid, exact on its unified book;
  Polymarket NO = the NO token's live orderbook ask; PredictIt NO =
  bestBuyNoCost). Otherwise `"one-sided"`. The old midpoint-based
  Dem-YES + Rep-YES basket (and its `safe_rep` 3-way-race guard) is gone —
  the same-question YES/NO basket is a binary partition, immune to
  independents.
- Stake sizing for guaranteed arbs (in `compute_arb` / `make_pair`).
- `settle_date` / `days_to_settle` / `annualized_return_pct` — later leg's
  settlement (Kalshi `expected_expiration_time`, NOT `close_time` which is
  a year-late buffer), and return annualized over the lock-up. The
  dashboard's "Settles" column sorts on this.

Both Kalshi and Polymarket loaders inner-join Dem and Rep; only races
with both sides explicitly priced reach the scanner. See the "Do not"
list for why inferring a missing side from `1 - other_side` was ripped
out.

**2. General-election candidate path** (`match_type: "general_candidate"`,
added 2026-06-18 — `load_general_candidates` + `general_candidate_pairs`).
Catches per-candidate general markets like "Will Dan Sullivan win the
2026 Alaska Senate race?" priced across Kalshi / Polymarket / PredictIt.
Matching key is `(state, office, district, candidate_last,
candidate_first)` — no party in the key because general-election
candidate names are unambiguous (the surname carries identity).

~~These rows are emitted as `arb_type: "one-sided"`~~ **CORRECTED
2026-07-03**: the old claim that "neither Kalshi nor Polymarket lists
P(candidate loses) as tradeable" was wrong — every Kalshi binary market
has a NO side (unified book), every Polymarket binary market has a NO
token (we scrape `no_token_id`), and PredictIt quotes Buy-No. Candidate
pairs now run the same real-quote YES+NO basket math as general pairs
and are promoted to `"guaranteed"` when the books justify it. Every
promoted candidate pair is additionally run through rules-text scrutiny
at threshold 0 (criteria-divergence risk is highest on same-name
candidate markets: runoffs, specials, withdrawal rules).

`_GEN_CAND_EXCLUDE` and `_GEN_CAND_SUBJECT_SKIP` regexes drop noise
templates ("Will X win Harris County?", "Will X finish 3rd?", "Will X
endorse Y in the runoff?", "Will an independent win X?", "Will the
Mike Duggan party win the governorship?"). Lt. Governor markets are
also dropped because `_extract_state_office` only maps SEN/GOV/H.

**3. Primary-candidate path** (`match_type: "primary_candidate"`,
`load_primary_candidates` + `primary_pairs`). Matches on `(state,
office, district, party, candidate_last, candidate_first)` parsed from
market titles — independent of `race_id`. Catches "Will Zach Wahls be
the Democratic nominee for Senate in Iowa?" priced differently across
platforms. First-initial disambiguation is essential (Chris Sununu vs
John E. Sununu collapsed without it).

### Suspicion + scrutiny pipeline

After the matching paths, each pair runs through several filter layers
in order:

1. **Scraper-time filters** drop unrealistic markets at the source —
   Polymarket markets with liquidity < $200 or bid-ask spread > 20pp get
   dropped before they ever reach the scanner.
2. **Depth-derived spread filter** (after `fetch_depth`) — pairs where
   either side's live CLOB book has spread > 25pp get dropped. The
   gamma snapshot lags the live book, so this catches stale entries
   that survived (1).
3. **Rules-text scrutiny** (`scripts/scrutiny.py`) — for any pair with
   raw gap > 30pp, fetches both markets' resolution rules and computes a
   text similarity score. <75 tagged `criteria_warn` (and a guaranteed pair
   is downgraded). Low scores no longer DROP pairs (2026-09-24): Kalshi and
   Polymarket boilerplate differs so much that identical questions score
   5-13. Only `excluded_pairs.json` entries are dropped.
   Plus a hand-curated `data/processed/excluded_pairs.json` for known
   criteria mismatches (Iran nuclear deal is the only entry today;
   Kalshi requires a signed agreement w/ enrichment limits + sanctions
   relief while Polymarket accepts any publicly announced agreement).
4. **Suspicion reasons** — surfaces multiple warning codes
   (`wide_gap`, `wide_spread_a/b`, `one_sided_a/b`, `thin_depth_a/b`,
   `criteria_warn`) on the dashboard's `⚠ verify` badge so the user
   knows WHY a pair is flagged.

### Fees

Guaranteed-basket math charges each leg its platform's real taker fee at the price it trades
(`utils/fees.py`, identical copy in pred-arbitrage), plus a 0.5c margin per basket. A basket
needs a net return of 0.25% or more to be "guaranteed".

| Platform | Taker fee | Where the parameters come from |
|---|---|---|
| Kalshi | 0.07 x multiplier x P(1-P) | `fee_multiplier` per series, from `/series` (event overrides from `/events/fee_changes`) |
| Polymarket | rate x p(1-p) | each market's `feeSchedule.rate` when `feesEnabled`; politics is 0.04 |
| PredictIt | 10% of profit + 5% withdrawal | no API; conservative model |

The flat `FEES` dict at the top of `scripts/arb_scanner.py` (Kalshi 2%, Polymarket 2%,
PredictIt 12%) is only the fallback when a leg's parameters are unknown, and drives the
display-level "Net gap". It is exported to `docs/arb_data.js`; the dashboard explainer text
(search "Net gap subtracts" in `docs/index.html`) must match it.

---

## 4. Common gotchas (the hard-won list)

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

**Python footguns**
- **`bool(float('nan')) is True`.** NaN is a non-zero float in Python, so
  `bool(NaN)` returns True. Anywhere we read an "optional flag" column
  out of a pandas DataFrame (e.g. a column that's True for some rows
  and NaN for the rest), `bool(row.get('flag'))` will fire on every
  NaN row too. Use `row.get('flag') is True` (or `pd.notna(...) and
  ...`). This bug caused 100% of arb pairs to flag as suspicious in
  June 2026.
- **`row.get('col_that_does_not_exist')` on a pandas Series returns
  `None`, not the default**, even when you pass a default. Worse: if
  the column EXISTS in the DataFrame but is NaN for this row,
  `row.get(...)` returns NaN. Combine with the bool-NaN gotcha above
  and any conditional on Series row data needs an explicit value check.
- **`pd.read_csv` of a 0-byte file raises `EmptyDataError`.** Always go
  through `_safe_read_csv`.

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
  backup, and since 2026-07-03 the pass-2 recompute reprices every
  basket on the live books anyway.
- **Polymarket gamma pagination is capped and oldest-first.** `offset`
  hard-caps at 2000 (HTTP 422 beyond, since ~mid-June 2026), the
  `/events/keyset` replacement ignores its cursor (probed 2026-06-21),
  and the DEFAULT sort is id ascending = oldest events first — an
  unfiltered scan never sees newly listed markets. That's why
  `scrapers/polymarket.py` queries per `tag_slug` (each tag gets its own
  2000-offset window). If a tag's universe outgrows the cap, the scraper
  prints a WARNING — then add a second pass with
  `order=id&ascending=false` (verified working 2026-07-03).
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
- Fixed 2026-07-03: baskets are YES and NO on the SAME question (a binary partition), so an
  independent cannot break them. The `safe_rep` guard that used to cover this is gone. Never
  build a basket from "Dem YES" on one platform and "Rep YES" on the other.

**Resolution-criteria divergence**
- **Party-win markets (verified 2026-09-25).** Kalshi resolves on the party of the person SWORN IN or inaugurated for the 2027 term. Polymarket resolves on the winner of the November election. They differ only if the winner dies, withdraws, switches party or the result is overturned before January. The risk is rare but real; treat party-win "guaranteed" baskets as near-certain, not certain.
- Same-topic markets can have different resolution criteria. Iran
  nuclear deal: Kalshi requires a signed agreement WITH specific
  enrichment limits + sanctions relief; Polymarket accepts any publicly
  announced agreement. Same gap, different bets.
- Mitigation: `scripts/scrutiny.py` fetches both rules texts for any pair over 30pp (and for
  every promoted candidate pair) and scores their similarity. A score under 75 tags
  `criteria_warn` and downgrades a guaranteed pair. Low scores never drop a pair (since
  2026-09-24): only `data/processed/excluded_pairs.json` entries are dropped.

**Date / cycle**
- **Ballotpedia's calendar rolls past dates off** as the year goes on.
  By mid-summer most state primaries are gone. `primaries.py` is
  written to tolerate this — if calendar parse yields 0 rows and a prior
  `docs/primaries_data.js` exists, keep the old data and exit 0.

---

## 5. Do not

- **Pick an election market leg by "the title mentions Democrat".** Use
  `utils/election_shapes.party_win_side` (identical copy in pred-arbitrage).
  Polymarket lists margin-of-victory buckets, "within 5%", "closest race"
  and governor+Senate combo markets under the same race; substring matching
  made them the Dem-win leg (3 fake 56-81% arbs + a wrong AK-Sen model
  comparison, 2026-09-24).
- **Size stakes by inverse price.** A hedge buys equal CONTRACTS on both
  legs, so dollars are proportional to price (`compute_arb`, 2026-09-24).
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
- **Reintroduce the "inferred-complement" fallback** in
  `load_kalshi_general` / `load_polymarket_general`. Earlier versions
  filled a missing Dem (or Rep) side with `1 - other_side` and tagged
  the row `kalshi_dem_inferred` / `pm_dem_inferred`. The intent was to
  keep one-sided races on the dashboard. The problem: an inferred price
  is the *implied no probability*, NOT a fillable yes ask on a real
  market book. The arb scanner would then surface "guaranteed arbs"
  against a leg that physically can't be traded — pure noise. The
  loaders now inner-join Dem and Rep so only races with both sides
  explicitly priced reach the scanner. If you want to surface
  one-sided coverage somewhere, do it in the Polling vs Markets tab or
  a separate "coverage" view — never feed it back into arb math.
  **Clarification (2026-07-03):** the new arb math's Kalshi NO ask
  (`1 − yes_bid`) is NOT this pattern. The ban is on inferring a
  DIFFERENT market's price from a midpoint; `1 − yes_bid` on the SAME
  Kalshi market is exact (its YES and NO books are one book — buying NO
  at 1−p literally fills against the resting YES bid at p). Polymarket
  NO asks come from the real NO-token book; never infer those from
  midpoints either (that's `no_ask_real=False`, which blocks the
  guaranteed label by design).

---

## 6. Mirrored on ezdubsanalytics.com (2026-10-31)

`docs/map.html` and `docs/predictions.html` also appear on the user's site,
ezdubsanalytics.com (repo `pjmerica/ez-dubs-website`), as **"The EZ Dub Election
Forecast"** under a Politics menu: `/dashboards/politics-map/` and
`/dashboards/politics-forecast/`. Nothing here pushes to it. That repo's
`scripts/pull_politics.py` runs every two hours (`politics-pull.yml`), fetches
this repo's **published Pages site** (so a change shows there after the Pages
deploy, within about two hours) and:

- copies `forecast_data.js`, `data.js`, `us_map_geo.js` and
  `us_house_2026_geo.js` byte for byte, checking each is `const NAME = <json>;`;
- rebuilds both pages from the published HTML: the markup and the **last inline
  `<script>`** verbatim, the `.top` header dropped, the site's nav and footer
  around it, this page's CSS re-themed to the site's newsprint look.

So changes made here reach the site on their own. What it relies on, which is
worth keeping in mind when editing these two pages:

- **The page logic stays in one inline `<script>`** at the end of `<body>`, and
  the data files keep their `const NAME = {...};` form.
- **The element ids** its `PAGES` table lists (`map`, `metric`, `src`, `tabs`,
  `tally`, `legend`, `detail`, `rows`, `thead`, `more`, `drawer`, `d-body`,
  `tip`, `title`, `lede`, `asof`; on predictions.html `chambers`, `grid`,
  `count`, `q`).
- **Colours as hex literals** in the script. It maps each known one to a
  newsprint colour; a new hex still works but shows in this page's colour there
  until added to its `JS_HEX`. The map's `const PCOL = {...};` statement is
  swapped whole (a required match), as are `function ink(col)` and the
  `const pill = v => ...` line (optional).
- **Links between the two pages** (`map.html#...`, `predictions.html#...`) are
  rewritten to the site's URLs. A link from either page to any OTHER page here
  (index.html, polls.html, election-night.html) has no counterpart on the site,
  so it stops that page rebuilding until the site's script is taught about it.

If something it relies on changes, that site page is not rebuilt (its last good
version stays live, the data keeps updating) and the site's workflow goes red.
Nothing here breaks.

---

## 7. When something breaks

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
