# Notes for the Reviewer — polling-agg-2026

**Audience**: senior engineer doing a code-correctness + onboarding +
security review. Start here, then go to `HANDOFF.md` for architecture
and `AUDIT.md` for the prioritized to-do list.

**Status**: live at https://pjmerica.github.io/polling-agg-2026/.
Daily cron at 12:00 and 00:00 UTC. Most recent runs in
[GitHub Actions](https://github.com/pjmerica/polling-agg-2026/actions).

This is a working personal project, not a production system. Owner is
the only user; no auth, no PII, no user-provided input flows through
the pipeline. Failure modes are bounded: at worst the live dashboard
shows a stale snapshot.

---

## What this project is, in one paragraph

US 2026 election dashboard. Scrapes Kalshi / Polymarket / PredictIt
markets plus NYT polls and Ballotpedia primary calendars. Aggregates
per-race implied probabilities, surfaces polling-vs-market mismatches,
runs an arb scanner across the three platforms, lists 2026 primary
dates. Outputs several `docs/*.js` files; a single-page dashboard
(`docs/index.html`) renders six tabs (Dashboard, Poll Explorer, Raw
Polls, Polling vs Markets, Arb Scanner, Primaries).

The sibling repo
[`pred-arbitrage`](https://github.com/pjmerica/pred-arbitrage) is the
generalized version covering every Kalshi/Polymarket/PredictIt
market (sports, entertainment, crypto, etc.) — this one is
elections-only.

---

## The minimum mental model

```
scrapers/* ──→ regen_data.py ──→ docs/data.js + polls_data.js + mismatch_data.js
            └─→ arb_scanner ──┬─→ depth_targets.csv → fetch_depth.py → arb_scanner (pass 2) → docs/arb_data.js
                              └─→ scrutiny.py (resolution-text similarity check on >30pp pairs)
scrapers/primaries.py ───────────────────→ docs/primaries_data.js
```

Three matching paths for elections (live in `scripts/arb_scanner.py`):
- **general** — party-level Dem/Rep markets, joined on canonical
  race_id (`2026-SEN-OH` etc.)
- **general_candidate** — per-candidate general markets
- **primary_candidate** — per-candidate primary markets

The same election logic was hand-ported into pred-arb on 2026-06-18
as `scripts/elections.py` over there. The two are now somewhat
drifted — see "Cross-repo drift" below.

---

## ⚠ Most important thing to know before reviewing

**This repo is missing several real improvements that landed in the
sibling pred-arbitrage repo on 2026-06-21.** Those changes fix bugs
that ALSO exist here:

| Improvement | Status here | Status in pred-arb | Severity |
|---|---|---|---|
| Arb math uses real ASK / NO ASK (not midpoints) | midpoint only | real bid/ask | **HIGH** — overstates guaranteed-arb returns |
| Display price = `last_price` (matches Kalshi UI) | midpoint | last_price | MEDIUM — UI inconsistency |
| Scrape freshness guard | none | `_assert_scrape_freshness()` | MEDIUM — silent staleness mode possible |
| Live Polymarket CLOB freshen (pre-matching) | partial (depth-time override only) | full pre-match freshen | MEDIUM — stale gamma prices can produce fake arbs |
| Past-settle-date / past-close-date filters | none | scraper-level filters | LOW — dead-prop noise |
| Polymarket NO orderbook fetch | inferred `1 - YES_bid` | real CLOB NO fetch | LOW — accurate enough for tight books |

**Why they're not ported here yet**: scope discipline. We just spent
a long session debugging the same issues in pred-arb; copy-paste port
without re-verification is risky. Tracked in `AUDIT.md` under
"Improvements from pred-arbitrage that should be ported here" with
file-level references for the next session.

If you see "midpoint-based guaranteed arb of 6.65%" on this dashboard
and it doesn't reproduce when you sanity-check against the actual
Kalshi/Polymarket asks, that's the bug. The pred-arb HANDOFF has the
worked example (look up "Somaliland").

---

## Cross-repo drift — what's intentional vs accidental

**Intentional**:
- Independent crons (12:00 vs 12:30 UTC) so the two repos don't hit
  Polymarket / Kalshi APIs simultaneously.
- Independent dashboards at different URLs.
- Pred-arb covers all markets; this one focuses on elections only.

**Accidental / should converge**:
- `utils/http_headers.py` is duplicated; should stay in lockstep.
- `FEES` dict in `scripts/arb_scanner.py` is duplicated; both at
  2%/12%/2% as of 2026-06-21. Manual sync risk.
- Today's pred-arb improvements (see table above) are real fixes that
  apply here too.

`AUDIT.md` to-do #6 (and pred-arb's matching #6) tracks the
cross-repo sync mechanism options.

---

## What's likely to surprise you

### 1. Six tabs, not five

Dashboard, Poll Explorer, Raw Polls, Polling vs Markets, Arb Scanner,
Primaries. The Polling vs Markets tab is being replaced by a "Model
vs Markets" tab once the owner's probabilistic model is ready — see
`AUDIT.md` "Planned work tracker" + the `models/` empty package.

### 2. PredictIt fees are 12%, not 3%

`scripts/arb_scanner.py:FEES` has PredictIt at 0.12 (5% on profits +
~5-7% effective withdrawal). Kalshi and Polymarket are at 2% each.
Any PredictIt-leg "guaranteed arb" needs a much bigger raw gap to
clear fees. This is intentional and matches pred-arb.

### 3. `analysis/aggregator.py` is orphan code

Not imported anywhere. References `rcp_polls.csv` which doesn't
exist. Kept because the user's planned model work may use it as a
starting point. If still unused by 2026-09, delete. See `AUDIT.md`
to-do #4.

### 4. Two stub scrapers (538, RCP) raise NotImplementedError

`scrapers/fivethirtyeight.py` and `scrapers/realclearpolitics.py`
are dead stubs (538 shut down 2026-04, RCP blocks programmatic
access). Kept as reference for resurrection if either comes back.
Delete after 2026-12 per `AUDIT.md` to-do #5.

### 5. `regen_data.py` runs at import

The file has no `if __name__ == "__main__":` guard — the script body
runs at module import. Already broken once (you can't import it from
a test or interactive session). `AUDIT.md` to-do #6.

### 6. Polymarket scraper here uses a different pagination strategy than pred-arb

This repo's `scrapers/polymarket.py` paginates with `/events?offset=`
capped at 2000 — same constraint as pred-arb, but no comment block
explaining the keyset-is-broken story. Worth backporting that
explanation if you're going to touch this scraper.

---

## Where to look for what

| You want to know... | Read this |
|---|---|
| What does each tab show? | `README.md` "What it shows" |
| Full architecture + every file | `HANDOFF.md` |
| What's broken / what's next | `AUDIT.md` "To-do" |
| What pred-arb has that this doesn't | `AUDIT.md` "Improvements from pred-arbitrage that should be ported here" |
| Election arb logic | `scripts/arb_scanner.py` (loaders + pair builders for general/general_candidate/primary_candidate) |
| Today's commit log (Jun 21) | `git log --since=2026-06-21 --oneline` — note: light, most of today's work was in the sibling pred-arb repo |

---

## Code-correctness signals

Things I'm reasonably confident about:

- The election matching guards (state surname disambiguation,
  primary-vs-general routing, first-initial dedup) are well-tested by
  past false-pair incidents — each guard exists for a specific bug.
- `_safe_read_csv` is used consistently to tolerate missing/empty
  scraper output without crashing the pipeline.
- The race registry (`utils/races.py`) covers 35 Senate + 36 Governor
  + 435 House races. Static for the 2026 cycle.
- `scripts/scrutiny.py` resolution-rules similarity check correctly
  drops pairs whose markets describe different outcomes (Iran
  nuclear deal is the only manual exclude today).

Things I'd want a second pair of eyes on:

- The arb math (`compute_arb_math`). Uses midpoints. Pred-arb's
  rewrite to use real bid/ask should be ported here — that's
  `AUDIT.md` "Improvements from pred-arbitrage" item A.
- The pipeline's two-pass arb_scanner structure (run, fetch_depth,
  run again). Subtle: the depth-targets file produced by pass 1 is
  what fetch_depth consumes; if you collapse the passes you also
  have to rewire that.
- `docs/index.html` is ~1,680 lines of inline JS. No bundler. The
  six tabs share a few global state vars (`filterOffice`,
  `searchQ`, etc.) — manageable but easy to break.

---

## Security surface

Identical to pred-arb. No secrets, no auth, no user input, public
read-only dashboard. Workflow has `contents: write` only. Market
titles flow into `innerHTML` (low-risk XSS surface since titles are
platform-curated). See pred-arb's NOTES_FOR_REVIEWER for the longer
discussion.

---

## How to know if something's broken

1. **GitHub Actions tab** — last "Daily refresh" should be ✓.
   ~10-15 min runtime is normal (longer than pred-arb because more
   data sources).
2. **Live dashboard timestamps** — each tab has its own "updated"
   timestamp; all should be < 24h.
3. **Ballotpedia primaries scraper occasionally fail-tolerates** —
   if the calendar parse returns 0 rows mid-cycle, the scraper
   intentionally keeps the prior `docs/primaries_data.js` instead of
   failing. This is the one place the pipeline doesn't fail-fast on
   empty data.

---

## Today's session summary (2026-06-21)

This repo got very little direct work today (per user's
"don't touch polling-agg" instruction while we worked through
pred-arb). The relevant updates here are:
- This NOTES_FOR_REVIEWER.md (new)
- `AUDIT.md` cross-repo drift section + "Improvements from
  pred-arbitrage" punch list (added)

For the full play-by-play of what happened in pred-arb today, see
`pred-arbitrage/AUDIT.md` "2026-06-21" entries and
`pred-arbitrage/NOTES_FOR_REVIEWER.md`.

---

## If you have 15 minutes

1. Read this file (you're doing it).
2. Read `AUDIT.md` "Improvements from pred-arbitrage" — that's the
   highest-leverage open work.
3. Glance at the most recent GitHub Actions run.

## If you have an hour

4. Read `HANDOFF.md` top to bottom. Architecture + every gotcha.
5. Read `scripts/arb_scanner.py:run` (the main pipeline) and
   `compute_arb_math` (the math).
6. Read `pred-arbitrage/HANDOFF.md` "Arb math" section — explains
   the bug fix we should port here.

## If you have a half-day

7. Port the high-priority items from "Improvements from pred-arbitrage"
   (especially A: real-ASK arb math, and B: freshness guard). Both
   are roughly mechanical copy-paste with small adaptations.
8. Pin `requirements.txt` (`AUDIT.md` to-do #2).
9. Decide on `docs/polls.html` (orphan? still served from Pages?).
