# Agent Execution Notes — Arb Pipeline Audit + Implementation (2026-07-03)

**Written by:** audit agent, 2026-07-03. **Audience:** the next agent picking this up.
**Goal:** find more arbitrage props across Polymarket / Kalshi / PredictIt, faster, with accurate (fillable) math. "The sooner they cash the better" — latency and correctness both matter.

> ## ⚡ STATUS UPDATE (same day): items 1–6 of the execution priority WERE IMPLEMENTED
>
> The audit below was written first; the same session then executed the punch
> list. **Read "What was implemented (2026-07-03)" at the bottom of this file
> first** — it says exactly what changed, what was verified against live
> orderbooks, and what is still open for you. The findings below are kept
> for context/rationale; their "Execute:" instructions are now DONE except
> where the bottom section says otherwise.

Read HANDOFF.md + AUDIT.md first; this file builds on them and does not repeat their content.

---

## Pipeline health check (verified live 2026-07-03)

- GitHub Actions cron: HEALTHY. Twice-daily "Daily refresh" runs all green, ~11–12 min each. Last: 2026-07-03T14:12Z.
- **Latest Pages deploy FAILED** (run 28666540390, "Deployment failed, try again later", GitHub-side transient). Live site is serving the 02:54Z snapshot. Self-heals next cron. Low priority: nothing to fix in-repo; optionally re-run deploy.
- **Local checkout is a week stale** (last pull 2026-06-26). `git pull` before doing anything. Local `data/raw/*.csv` for markets are from May — gitignored, regenerate locally if testing.
- None of AUDIT.md's "Improvements from pred-arbitrage" ports (items A–E, dated 2026-06-21) have landed. All commits since are polls-related. **Those ports are still the top correctness work.**

---

## FINDING 1 (HIGH — new, not in AUDIT.md): candidate-level pairs never get guaranteed-arb math

`scripts/arb_scanner.py` `general_candidate_pairs()` (~line 906) and `primary_pairs()` (~line 1018) hard-code `arb_type: "one-sided"`. The docstring claims "Polymarket / Kalshi don't expose candidate-no as a separately tradeable contract." **That claim is wrong:**

- Every Kalshi binary market has a tradeable NO side (buy NO at `1 - yes_bid`-ish; the orderbook's `no_dollars` stack is real resting liquidity).
- Every Polymarket binary market has a NO token — the scraper already captures `no_token_id` in `polymarket_markets.csv`.
- PredictIt contracts have Buy No prices (`bestBuyNoCost` in the API).

So "Will <candidate> win X?" at 40% on Kalshi and 55% on Polymarket IS a guaranteed basket: buy YES on Kalshi ask + buy NO on Polymarket ask; if combined cost < 1 after fees, profit is locked in both outcomes. Binary same-market YES/NO is a true 2-state partition — no third-candidate caveat (unlike the Dem/Rep cross-flip).

**Execute:** extend the candidate-pair builders to compute guaranteed arb using YES ask on the cheap platform + NO ask on the expensive platform. Requires real ask prices (see Finding 2) — do NOT ship this on midpoints, it will overstate. Flow `no_token_id` through depth_targets so fetch_depth can pull the Polymarket NO book; Kalshi NO ask = 1 − max(yes `no_dollars` stack) is already derivable from the existing orderbook fetch.

**Worry:** resolution-criteria divergence bites hardest exactly here (same candidate name, different fine print — e.g., "wins the race" vs "wins the general election" with runoff/special-election edge cases). Run scrutiny.py on ALL candidate pairs promoted to guaranteed, not just >30pp ones.

## FINDING 2 (HIGH — AUDIT.md item A, confirmed still open): arb math runs on midpoints

`compute_arb_math(prob_a, prob_b, ...)` at scripts/arb_scanner.py:244 takes midpoint implied probs. Real cost is YES ask + NO ask (strictly worse than midpoints). Every "guaranteed_return_pct" on the dashboard is overstated. Pred-arb already has the fixed version (`compute_arb` with bid/ask kwargs) — port per AUDIT.md item A. This is a prerequisite for Finding 1.

## FINDING 3 (HIGH — latency): twice-daily cron is the biggest limit on catching arbs

Arbs decay in minutes-to-hours; the pipeline scans at 00:00 and 12:00 UTC only. The full run takes ~11–12 min, most of it polls scraping (Wikipedia per-state pages, NYT) which the arb scan doesn't need.

**Execute:** split the workflow into two jobs/schedules:
- **Fast market loop** (suggest every 1–2 h; even hourly is ~24 runs × ~4 min = well within free Actions minutes for a public repo): kalshi.py → polymarket.py → predictit.py → arb_scanner pass 1 → fetch_depth → arb_scanner pass 2 → commit docs/arb_data.js only.
- **Full polls refresh** (keep 2×/day): everything else (nytimes, wikipedia_polls, house_incumbents, primaries, regen_data).
Keep the two crons offset from pred-arb's (intentional: don't hit the same APIs simultaneously).
**Worry:** more commits/day of arb_data.js = noisier git history (acceptable; refresh commits are already excluded from CHANGELOG) and more chances of the manual-push race (rebase-retry loop already handles it).

## FINDING 4 (CRITICAL — verified live 2026-07-03): Polymarket scrape misses most of the market universe, including ALL new listings

`scrapers/polymarket.py` paginates `/events?offset=` with no `order` param. Verified live today:

- Gamma hard-caps offset at 2000 (HTTP 422 beyond; confirmed in today's cron log: "Error at offset 2100 … stopping pagination").
- **Gamma's default sort is id ASCENDING = oldest first.** Page 1 events were created Dec 2024. So the scraper sees only the ~2,100 OLDEST active events. Every event created after that window filled is INVISIBLE — i.e., newly listed 2026 election markets (where fresh mispricings live) never enter the pipeline, and coverage decays over time.
- Pred-arb has the same bug (documented in its `fetch_all_events()` docstring: keyset endpoint is broken, reverted to capped offset). It affects BOTH repos.

**Verified fixes (probed live today, all work):**
- `order=id&ascending=false` is honored → newest-first pagination works.
- `tag_slug=elections` → 825 active events / 11,359 markets — fits entirely under the 2000-offset cap.
- `tag_slug=politics` → 1,365 events / 14,269 markets — also fits.
- `tag_slug=us-election` → 52 events / 746 markets.

**Execute (this repo):** replace the blind pagination in `fetch_all_active_markets()` with tag-filtered pagination: union of `tag_slug=elections` + `tag_slug=politics` (dedup by event id), keep the existing keyword+exclude filter as a secondary sieve. That covers the full election universe INCLUDING new listings, in fewer requests (~22 pages vs 21 today, but complete).
**Execute (pred-arb):** needs the general fix — two-pass scrape (default oldest-first 2000 + `order=id&ascending=false` newest-first 2000, dedup) and/or per-tag queries for its categories; or the clob.polymarket.com/markets rewrite its AUDIT already tracks. Flag this to the user — pred-arb is currently blind to every market listed after ~mid-June 2026 beyond the first 2000.
**Expected impact:** this is the single biggest "find more props" lever found in this audit. Today's scan found 6,113 election-keyword markets in the old window; the elections tag alone has 11,359 markets.

## FINDING 5 (HIGH — efficiency): Kalshi scraper is ~7 of the pipeline's ~10.5 minutes

Verified from today's cron log (banner timestamps): Kalshi scrape 14:12:24→14:19:20 (~7 min) because it makes **one HTTP request per series (1,573 series today) + 0.2s sleep each**. Polymarket ~3s, PredictIt ~1s, NYT ~2s, Wikipedia ~2m11s, house_incumbents+primaries ~3s, regen ~5s, arb pass 1 ~2s, fetch_depth (372 books, serial, 0.1s sleep) ~66s, pass 2 ~2s.

**Execute:** replace per-series fetching with bulk cursor pagination: `GET /trade-api/v2/events?status=open&with_nested_markets=true&limit=200` + `cursor` param (modern endpoint, returns all ~5k open events / ~40k markets in ~25-40 requests — this is what pred-arb uses; see its scrapers/kalshi.py). Filter to election series locally using the same ELECTION_KEYWORDS/ticker patterns. Expected: 7 min → well under 1 min, and no more per-series WAF retry stalls.
**Worry:** verify nested market field names match (`yes_bid_dollars` etc. are the same on this endpoint) and that series_ticker is derivable from each event (`event.series_ticker` field exists). Smoke-test row counts before/after: today's baseline is 1,573 series scanned and the row count in the "Saved N market rows" log line.

## FINDING 6 (MEDIUM — directly serves "sooner they cash"): no settlement dates anywhere in arb output

Kalshi's API has `close_time`/`expected_expiration_time`, Polymarket has `endDate` (already scraped into the CSV), PredictIt has `dateEnd` per contract. None of it reaches `docs/arb_data.js`. The dashboard cannot rank arbs by time-to-settlement, but capital lock-up time is THE variable for arb yield: a 3pp guaranteed arb settling in 2 weeks annualizes ~80%; the same 3pp settling Nov 2026 annualizes ~9%.

**Execute:**
- kalshi.py: capture `close_time` (and `expected_expiration_time` if present) into the CSV.
- predictit.py: capture contract `dateEnd`.
- polymarket.py: `end_date` already captured — just flow it through.
- arb_scanner.py: emit `settle_date_a/b` (min of the two as `settle_date`), `days_to_settle`, and `annualized_return_pct = guaranteed_return_pct / days_to_settle * 365` on every pair; sort/filter by it in the dashboard (new column + "settles before" filter).
- Also add AUDIT item E's past-date filters while touching this (drop close_date/endDate < today at scrape time).
**Worry:** primaries mostly settle mid-2026 (soon = good arb targets); generals settle 2026-11-03. Beware Kalshi `close_time` sometimes being the trading-close not settlement — display both if they differ materially.

## FINDING 7 (LOW-MED — health): "Found 0 non-running incumbents" in today's log

`scrapers/house_incumbents.py` Ballotpedia fetch returned 0 rows today (log 14:21:40). It soft-continues; races.py presumably falls back to its hand-curated open-seats list. Check whether Ballotpedia changed its page shape; if the parse is dead, open-seat House races may be mis-flagged. Not arb-critical. Verify by running the scraper locally and diffing `data/processed/house_incumbents.json` against git history.

## Current output snapshot (from today's 14:12Z cron, pass 2)

- Kalshi 109 races, PredictIt 66 races, Polymarket 491 races (general party-level path)
- 7 general-candidate pairs, 100 primary-candidate pairs, 305 total pairs → 304 after depth filter
- **19 "guaranteed" arbs after fees** (midpoint math — see Finding 2, real number will be lower once ask-based math lands), 18 profitable one-sided
- Depth joined onto 305/305 pairs; 1 dropped for wide spread

### Reality check on those 19 "guaranteed" arbs

All 19 are kalshi/polymarket House generals, midpoint math, best 6.0% (2026-H-CO-08), five at ≤0.5%. Expect several to vanish under real ask-based math (Finding 2). All settle ~2026-11-03 — a 6% return locked for 4 months is ~18% annualized BEFORE slippage; the sub-1% ones are dead money. This is why Finding 6 (settle dates + annualized column) matters: primary-market arbs settling in weeks are worth more per dollar than bigger-gap November arbs. 142/304 pairs involve PredictIt (no orderbook, unverifiable, 12% fee) — info-only, as designed.

---

## Exact pred-arb port references (paths verified 2026-07-03)

All in `c:\Users\pjmer\Documents\Pred Arbitrage\`:

| What | Where | Notes |
|---|---|---|
| Real bid/ask arb math | `scripts/arb_scanner.py:43` `compute_arb(prob_a, prob_b, fee_a, fee_b, bid_a, ask_a, ..., no_bid_b, no_ask_b)` | Two price layers: display (raw/net gap only) vs fillable (arb math). Emits `fillable_*` fields + `arb_uses_live_book` + `yes_a_real`/`no_b_real` flags. Taxonomy: guaranteed / pre-fee / price-gap / one-sided. Port this wholesale to replace polling-agg's `compute_arb_math` (arb_scanner.py:244). |
| Freshness guard | `scripts/arb_scanner.py:254` `_assert_scrape_freshness()`, `MAX_AGE_HOURS = 12` | Reads `fetched_at` col of each raw CSV; SystemExit if stale. Call at top of polling-agg's `run()`. |
| Kalshi last_price display | `scrapers/kalshi.py:181-220` | `implied_prob = last_price` first, fallback midpoint→ask→bid. Display-layer only. Polling-agg equivalent: `scrapers/kalshi.py:237-245` (currently midpoint-first). |
| Live CLOB freshen | `scripts/freshen_polymarket.py` | 16 worker threads re-fetch clob book pre-matching. Port as run_all step after polymarket.py. Uses last_price for Kalshi display parity (comment at :201). |
| NO-token orderbook fetch | pred-arb's fetch_depth/freshen flow | Polling-agg's `depth_targets.csv` only carries the YES token. Add `no_token_id` (already in polymarket_markets.csv) so `fetch_depth.py` pulls real NO asks. Kalshi NO ask needs no extra fetch: already derivable in `_kalshi_yes_book` (`1 - max(no_dollars)`) — expose it as `no_ask` instead of only folding it into `best_ask`. |

## Additional findings (smaller, fix while in the area)

- **`fetch_depth.py` is serial** (372 books × ~0.15s = ~66s/run). Parallelize with `concurrent.futures.ThreadPoolExecutor(16)` like pred-arb's freshen script → ~8s. Matters more once the fast-loop cadence increases.
- **`FEES.get(pa, 0.03)` stale default** in `general_candidate_pairs` (arb_scanner.py:889) and `primary_pairs` (:984) — the 0.03 fallback predates the 2% fee change. All platforms are always in FEES, so it's dead-but-misleading; use `FEES[pa]`.
- **predictit.py doesn't capture `bestBuyNoCost` / `bestSellNoCost`.** The API returns them. Capturing the NO ask gives PredictIt legs a real fillable NO price (PredictIt YES/NO are separately quoted books) — needed if candidate baskets ever include a PI leg, and improves the one-sided display honesty.
- **polymarket.py comment/code mismatch**: run() comment says "spread > 30pp" but code enforces `(ba - bb) <= 0.20`. Fix the comment (code is right per HANDOFF).
- **scrutiny.py skips any PredictIt pair** (scripts/scrutiny.py:157) and only inspects >30pp gaps. When Finding 1 promotes candidate pairs to guaranteed, call `scrutinize(promoted_pairs, threshold_pp=0)` on them — cheap (7-day cache) and the criteria-divergence risk is highest exactly there.
- **Kalshi scraper doesn't pass `status=open`** when fetching events per series — it relies on downstream filters. When switching to the bulk `/events` endpoint (Finding 5), use `status=open` explicitly and keep AUDIT item E's `close_date < today` drop as defense.
- **Node 20 deprecation warnings** still printing in Actions (advisory). Bump `actions/checkout@v5` / `actions/setup-python@v6` (or whatever is Node-24-native at execution time) — AUDIT.md open item, unchanged.
- **Local repo hygiene**: `analysis/aggregator.py` (orphan), `docs/polls.html` (orphan?), unpinned `requirements.txt` — all still open per AUDIT.md to-do; none block arb work.

## Workflow split spec (Finding 3, concrete)

Create a second workflow `market-refresh.yml` (or a second job in refresh.yml gated on schedule):

- **market-refresh**: cron `30 */2 * * *` (offset from pred-arb's 12:30 and from this repo's full run; every 2h to start — hourly later if API behavior stays clean). Steps: kalshi → polymarket → predictit → arb_scanner (pass 1) → fetch_depth → arb_scanner (pass 2) → commit `docs/arb_data.js data/processed/depth_targets.csv` only.
- **full refresh** (existing, keep 0 0/12 * * *): everything, including polls + primaries + regen_data.
- Guard against overlap: `concurrency: { group: refresh, cancel-in-progress: false }` on BOTH workflows so a market run queues behind a full run instead of racing the commit.
- After Finding 5 (fast Kalshi) + parallel fetch_depth, the market loop should complete in ~2–3 min.
- Keep scrapers fail-fast so a bad scrape never overwrites good arb_data.js (existing semantics — don't weaken).

## Execution priority (do in this order)

1. **Polymarket tag-based scrape** (Finding 4) — biggest new-props lever; small diff; also flag the same bug to the user for pred-arb.
2. **Port real bid/ask `compute_arb` + NO-token depth flow** (Finding 2 + port refs) — correctness prerequisite for everything that follows. Smoke test: rerun pipeline, compare guaranteed list before/after; expect several sub-1% arbs to die.
3. **Candidate-level guaranteed baskets** (Finding 1) — new guaranteed props from existing data. Run scrutiny on every promoted pair. Verify top 3 by hand against live books before trusting (use `c:\Users\pjmer\Documents\audit_arbs.py`).
4. **Kalshi bulk-events scrape** (Finding 5) — 7 min → <1 min.
5. **Workflow split + 2h market cadence** (Finding 3 spec above) — latency win; depends on 4 to be cheap.
6. **Settle dates + annualized return + dashboard column/filter** (Finding 6) — turns the arb tab into a capital-efficiency ranking ("sooner they cash").
7. **Freshness guard + last_price display + CLOB freshen port** (AUDIT items B/C/D) — hygiene + display parity.
8. Smaller items above as convenient.

## Standing worries (verify these whenever results look too good)

- Re-read `HANDOFF.md` "Common gotchas" + "Do not" before touching loaders — every guard exists for a specific past incident (bool(NaN), inferred-complement, orderbook semantics, token-id dtype, state-name matching).
- Kalshi orderbook `yes_dollars`/`no_dollars` are BUY stacks, not asks (fetch_depth.py docstring). Reintroducing the ask interpretation makes everything a fake 99% arb.
- PredictIt multi-contract sums >1 → "guaranteed" arbs with a PI leg are usually counting artifacts. Never promote a PI-leg pair to guaranteed off midpoints.
- Resolution-criteria divergence (Iran-deal class). `excluded_pairs.json` is the manual escape hatch; scrutiny.py is the automatic one. Candidate-name matches across platforms can still resolve differently (runoffs, specials, withdrawal rules).
- Two sessions of history say: **verify with live orderbooks before believing any new arb class** — `audit_arbs.py` reports REAL/THIN/DUST/ILLUSORY per pair.
- Don't break `docs/index.html` — it's the live site. Any new arb_data.js fields must be additive; the dashboard ignores unknown fields safely.
- GitHub Pages deploy occasionally fails transiently ("try again later") — the next cron self-heals; only investigate if two consecutive deploys fail.

---
---

# What was implemented (2026-07-03, same session as the audit)

Everything below is COMMITTED. Verification status is stated per item. If a
cron breaks after this lands, start with "Rollback / debug map" at the end.

## 1. Polymarket tag-based scrape — DONE (`scrapers/polymarket.py`)

- `fetch_all_active_markets()` now queries `tag_slug=elections` + `politics` +
  `us-election` (each gets its own 2000-offset window), dedups events by id
  and markets by id. The old blind oldest-first pagination is gone.
- Added past-`end_date` drop in `run()`; fixed the 30pp/20pp comment mismatch;
  capped the question-list log spam at 20.
- **Verified live:** 6,602 election markets found (was 6,113 from the
  truncated oldest-2100-events window), 1,536 saved after quality filters.
  Coverage now includes newly listed markets, which the old scrape
  structurally never saw.
- **Watch for:** the per-tag WARNING if a tag universe grows past the
  2000-offset cap — then add a second pass with `order=id&ascending=false`
  (param verified working 2026-07-03).

## 2. Kalshi bulk scrape + last_price + close dates — DONE (`scrapers/kalshi.py`)

- New `fetch_all_open_events()`: one cursor-paginated sweep of
  `/events?status=open&with_nested_markets=true&limit=200` (~35 requests for
  ~7k events), filtered to the election series set from the (cheap, 2-request)
  series list. The per-series loop (1,573 requests + sleeps ≈ 7 min) is kept
  as dead code for single-series debugging only.
- `implied_prob` is now `last_price` first (matches Kalshi's UI — AUDIT item C),
  falling back to tight-spread midpoint → ask → bid. Display-layer only.
- Captures `close_time` + `expected_expiration_time`; drops markets whose
  close_time is already past (175 dropped on first run).
- **Verified live:** 11,591 market rows in well under a minute (was ~7 min).
  Race-id loader counts match the pre-change baseline (108/65/491 vs 109/66/491
  — the drift is past-date drops + last_price semantics, checked by hand).

## 3. PredictIt NO quotes + dates — DONE (`scrapers/predictit.py`)

- Captures `bestBuyNoCost`/`bestSellNoCost` (real fillable NO quotes) and
  contract `dateEnd`. PredictIt dateEnd is often "N/A"/approximate — treated
  as such downstream (coerced, NaT-safe).

## 4. Real-quote arb math + candidate baskets — DONE (`scripts/arb_scanner.py`)

This is the big one. Read the new comments at the top of the "arb math"
section — they're written to be the reference. Summary:

- **`compute_arb_math` (midpoints) is GONE.** Replaced with `compute_arb`,
  ported from pred-arb: basket = Buy YES on one platform + Buy NO on the
  other, priced at real ASK / NO-ASK. `arb_type: "guaranteed"` now requires
  the winning direction to have REAL quotes on both legs AND clear fees AND
  return > 0.25% net (`MIN_NET_RETURN` floor — tune there).
- **The `safe_rep` partition check is gone** — no longer needed. The old
  basket was Dem-YES + Rep-YES (needs the 2-way-race assumption); the new
  basket is Dem-YES + Dem-NO on the same question (binary partition, immune
  to third-party candidates). Rep prices are display/join-gate only now.
  NOTE: this is NOT the banned inferred-complement pattern (HANDOFF Do-not):
  that inferred a PRICE from the opposite party's midpoint. Kalshi NO ask =
  1 − yes_bid is EXACT (unified book); Polymarket NO ask comes from the real
  NO-token orderbook; PredictIt from bestBuyNoCost.
- **Candidate-level pairs (general_candidate + primary_candidate) now get
  real basket math too** — the hardcoded `arb_type: "one-sided"` was based on
  a false premise ("no NO leg exists"). Any candidate pair whose books
  justify it is promoted to guaranteed, and every promoted candidate pair is
  run through scrutiny.py at threshold 0 (criteria-divergence risk is
  highest there).
- **Two-pass flow now matters more:** pass 1 computes on scrape-time quotes;
  pass 2 recomputes every pair on live depth books (`_recompute` in `run()`),
  including real Polymarket NO-token asks (NO tokens flow through
  `depth_targets.csv` via new `market_no_id_a/b` fields).
- **`_assert_scrape_freshness()`** (AUDIT item B) ported; runs at the top of
  `run()`; 12h max age on the three market CSVs.
- **Settle fields on every pair:** `settle_date` (LATER of the two legs —
  capital is locked until both settle), `days_to_settle`,
  `annualized_return_pct` (the "sooner they cash" ranking metric). Kalshi
  settle uses `expected_expiration_time` (e.g. 2027-01-04 for House races —
  when Congress is seated), NOT `close_time` (a safety buffer a year late).
- `FEES.get(pa, 0.03)` stale defaults → `FEES[pa]`.

**Verified against LIVE orderbooks** (scratchpad script, 2026-07-03 ~19:00Z):
the pipeline's 3 guaranteed arbs' fillable prices matched live books to the
cent:
  - 2026-H-CO-08: Kalshi YES ask 81c (250 avail) + PM NO ask 14c (25 avail) → 1.0% net, 2.0%/yr
  - 2026-H-TX-35: Kalshi YES 44c + PM NO 51c → 1.0% net
  - 2026-SEN-WV: PM YES 0.3c (10 shares — dust, correctly flagged thin_depth_b) + Kalshi NO 94.7c → 1.0% net
Compare: the old midpoint math claimed **19 guaranteed arbs up to 6.0%**.
The honest number today is 3 at ~1%/184d. That is the fix working, not a
regression — do not "fix" it back.

## 5. fetch_depth parallelized — DONE (`scripts/fetch_depth.py`)

ThreadPoolExecutor(12); 547 books (now incl. PM NO tokens) in seconds
instead of ~66s serial. `delay` param removed from `run()`.

## 6. Workflow split — DONE (`.github/workflows/market-refresh.yml` NEW)

- Fast loop: `run_all.py --markets-only` (new flag: market scrapers + arb
  passes only) every 2h at :30 on ODD hours. Commits `data/ docs/arb_data.js`
  with message prefix `market refresh:`.
- Both workflows share `concurrency: group: refresh` (queue, not cancel) so
  they never race each other's commit.
- Odd-hour offset avoids the full refresh (00/12 UTC) and pred-arb's cron
  (12:30 UTC).
- Bumped `actions/checkout@v5` + `actions/setup-python@v6` in BOTH workflows
  (Node-24 native — kills the deprecation warnings). **NOT yet verified in
  CI** — if the first run fails on action resolution, pin back to v4/v5 and
  the Node warning returns (harmless).

## 7. Dashboard — DONE (additive only, `docs/index.html`)

New sortable "Settles" column (after Guaranteed Return): settle date,
days out, and green `%/yr` annualized on guaranteed rows. Header tooltip
explains the metric. colspan bumped 13→14. CHANGELOG updated.

## Still OPEN for the next agent (priority order)

1. **Watch the first few cron runs** (both workflows) — Actions tab. Risks:
   the v5/v6 action bumps (see §6); the freshness guard tripping on the fast
   loop if a scraper starts silently failing (that's it working as designed —
   fix the scraper, don't relax the guard).
2. **Flag the Polymarket pagination bug to pred-arb** (its scrape is still
   blind to new listings — same fix applies; see memory note
   `reference-polymarket-pagination` and Finding 4 above).
3. **PredictIt-leg guaranteed arbs now possible** (real Buy-No quotes flow
   in). None surfaced on day one. When one does: PI has an 850-share/contract
   cap and 5% profit fee — our flat 12% is conservative, but verify the first
   few by hand; there is no PI orderbook so size-at-price is unknown.
4. **AUDIT item D (live CLOB freshen pre-matching) intentionally NOT ported.**
   The pass-2 depth recompute covers arb-math accuracy; the freshen would
   only improve match-stage display prices. Revisit if stale gamma quotes
   start producing bogus PAIRS (not bogus arbs — those are covered).
5. **"Found 0 non-running incumbents"** (Finding 7) still unverified.
6. Old AUDIT.md hygiene items unchanged: pin requirements.txt, smoke test,
   split arb_scanner into modules (it grew again today), polls.html decision,
   aggregator.py triage.

## Rollback / debug map

- Fast-loop cron failing? Disable `market-refresh.yml` in the Actions UI —
  the full refresh.yml alone restores the pre-2026-07-03 cadence.
- Freshness guard SystemExit in arb_scanner: one of the three market CSVs
  is >12h old — a scraper upstream failed structurally-silently. Check its
  step output first.
- Zero/too-few Polymarket markets: check the per-tag counts in the log
  (`tag=elections: N events`). If a tag 404s or returns 0, Polymarket
  renamed it — probe `/events?tag_slug=...` by hand.
- Kalshi rows collapse: check "Got N open events total" (expect ~7k) and
  "Found N election-related series" (expect ~1.5k). Cursor pagination
  stopping early shows as a low event count.
- Guaranteed arbs look inflated again: check `arb_uses_live_book` and the
  fillable_* fields in arb_data.js — if fillable == implied_prob on both
  legs, quotes stopped flowing and everything degraded to display prices
  (which can never be guaranteed — so actually you'd see ZERO guaranteed;
  inflation means a real math bug. Re-run the scratchpad verifier:
  `%TEMP%\claude\...\scratchpad\verify_guaranteed.py` or rewrite it, it's 40 lines).
