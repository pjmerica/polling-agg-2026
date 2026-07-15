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

- Model-vs-Markets fixes from the 2026-07-14 audit (commit hash added on push). Two classes
  of FAKE edges removed from the tab:
  (1) analysis/model_compare.py summed win_prob_norm over ALTERNATIVE same-party candidates
  (leftover hypothetical primary matchups) — ME-Sen published "87% Dem" (six Dems summed) vs
  Kalshi 51.5, NE-H-02 and two CA races showed 100%. model_dem is now the LEADING Dem's win
  prob renormalized against the LEADING Rep's (matches the market's D/(D+R) vig
  normalization); races with >1 same-party candidate left in the feed get
  `unresolved_field` + a "? FIELD" badge.
  (2) Independent-slot races compared different events: NE-Sen model P(Osborn) was diffed
  against the DEMOCRATIC-party market (fake +21-pt edge). New IND_RX matches both venues'
  independent-win markets; when dem_display != DEM the slot is priced against those
  (`slot_market='IND'`, "I MKT" badge), normalized over the full D+R+I book. Honest NE-Sen
  edge: ~-9 pts.
  Also: MOV-ladder medians anchored at vig-NORMALIZED win probs; margin symmetrization uses
  each party's leading candidate; payload gains `polls_as_of` (newest poll end_date the
  model consumed, from the model repo's new predictions meta sidecar).
- docs/index.html: mv-meta line was rendering raw JS source (string concatenation
  accidentally inside the template literal) — fixed; meta line now also shows "newest poll
  used"; new FIELD/I-MKT badges.
- .github/workflows: market-refresh.yml regenerated docs/model_data.js every 2h but its
  commit step only added `data/ docs/arb_data.js` — the model tab's market side silently
  updated only 2x/day. Now committed. Both workflows: `|| echo` crash-swallowing on
  model_compare replaced with continue-on-error + a post-commit step that fails the run
  loudly (data commits still land).

---

## 2026-07-03

- `[5f25ef4]` arb pipeline rework: real-quote basket math + full Polymarket coverage + 2h market cadence — five coupled changes from the 2026-07-03 audit (see AGENT_EXECUTION_NOTES.md "What was implemented" for the full record). (1) scrapers/polymarket.py: gamma's offset pagination is capped at 2000 AND sorts oldest-first, so the scraper never saw newly listed markets; switched to per-tag_slug queries (elections/politics/us-election), added past-endDate drop. (2) scrapers/kalshi.py: replaced 1,573 per-series requests (~7 min) with one bulk cursor sweep of /events?status=open (~35 requests, <1 min); implied_prob now prefers last_price (matches Kalshi UI); captures close_time + expected_expiration_time; drops past-close markets. (3) scripts/arb_scanner.py: midpoint compute_arb_math replaced with pred-arb's real ASK/NO-ASK compute_arb — basket is now Dem-YES + Dem-NO on the same question (binary partition; safe_rep 3-way guard obsolete and removed); candidate pairs (general_candidate/primary_candidate) get the same basket math instead of hardcoded "one-sided" (the "no NO leg exists" premise was false — Kalshi unified book, PM NO tokens, PI Buy-No quotes); pass 2 recomputes every pair on live depth books incl. real PM NO-token asks; added _assert_scrape_freshness (12h), settle_date/days_to_settle/annualized_return_pct, 0.25% MIN_NET_RETURN floor. Old midpoint math claimed 19 guaranteed arbs up to 6%; honest number on switch day: 3 at ~1%/184d, each verified to the cent against live orderbooks. (4) scripts/fetch_depth.py: parallelized (12 threads, 547 books in seconds). (5) .github/workflows/market-refresh.yml (new) + run_all.py --markets-only: markets+arb loop every 2h on odd hours at :30; both workflows share a concurrency group; actions bumped checkout@v5/setup-python@v6. Dashboard: new sortable "Settles" column (date, days, %/yr annualized on guaranteed rows).

---

## 2026-06-25

- `[306c0bd]` polls: section-context party/stage + whole-poll dedup — user reported OK Gov 6/23/26 Pulse Decision Science appearing twice (an orphan Wiki "poll" with just Drummond next to the proper NYT poll with Mazzei + Drummond). Two underlying bugs: (a) the OK Gov Wikipedia table doesn't put `(R)` on column headers because everyone in the "Republican primary" section is implicitly REP — our scraper had no fallback so party came back NaN and stage came back 'general' even for primary tables. (b) per-candidate dedup left orphans when names differed in spelling: NYT had "Genter Drummond" (their typo), Wiki had "Gentner Drummond"; Mike Mazzei matched both so he was dropped from Wiki, leaving a 1-candidate Wiki poll that rendered as a duplicate. Fix (a): new `infer_section_context()` reads enclosing `<h2>/<h3>/<h4>` headings for "Republican primary" / "primary runoff" / etc. and feeds (stage, party) defaults into `parse_poll_table()`; per-candidate column header annotation still wins when present. Senate and Governor scrapers share `_scrape_state_race()` helper that walks DOM in order. House + mayoral updated to track section state too. Fix (b): regen dedup is now whole-poll — if ANY candidate in a Wiki poll matches NYT for the same (race_id, pollster, end_date), drop the ENTIRE Wiki poll instead of just the candidates that matched. OK Gov 6/23/26 now correctly shows one poll (NYT version). MI Sen Zenith 6/14/26 still correctly shows 3 head-to-head matchups. Older OK Gov primary polls now show party=REP and stage=primary (were NaN/general).
- `[177c773]` polls: fix Wiki candidate party + source-aware dedup — user reported MI Sen 6/14/26 Zenith Research poll appearing 3+ times in Raw Polls with Mike Rogers tagged as DEM. Two bugs: (a) wikipedia scraper was inheriting the pollster's partisan tag onto every candidate, so a "(D)" sponsor made Mike Rogers REP show up as DEM; (b) candidate names kept the "(R)" / "(D)" suffix in headers so dedup against NYT's bare-name format never fired (NYT has "Mike Rogers", Wiki had "Mike Rogers (R)"). Fix (a): new `extract_candidate_party()` parses party from the column header annotation, `clean_candidate_header()` strips the suffix from the name; per-row party is looked up by candidate. Fix (b): regen dedup is now source-aware — drops wikipedia rows only when an NYT row exists for the same `(race_id, pollster, end_date, candidate)`, and explicitly does NOT collapse within-source dups (NYT's multi-question polls intentionally repeat the same candidate across head-to-head matchups; collapsing them broke per-question grouping in polls_data.js). MI Sen Zenith now correctly shows 3 head-to-head polls (Stevens/El-Sayed/McMorrow each vs Rogers) with Rogers properly tagged REP.
- `[42b4c03]` polls: mayoral coverage + Raw Polls source sub-tab — user asked to surface generic-ballot + mayoral polls (we had 1,099 generic-ballot rows already in production but no dashboard surface, and no mayoral coverage at all). Three changes: (1) `scrapers/wikipedia_polls.py` adds `scrape_mayoral()` + a `MAYORAL_RACES` list of (year, city, slug) tuples — 12 cities curated from probe-confirmed Wikipedia pages (NYC, Boston, Detroit, Pittsburgh, Cleveland, Seattle, Atlanta, Minneapolis, Buffalo 2025; LA + Miami 2026; Chicago 2027). race_id pattern `YYYY-MAYOR-<slug>`, stage='mayoral'. NYC smoke test: 38 distinct polls, 157 rows. (2) `scripts/regen_data.py` emits a new `docs/other_polls_data.js` feed (parallel to `polls_data.js`) carrying the three nationwide-ish stages: generic_ballot, approval, mayoral. (3) `docs/index.html` Raw Polls tab gets a Source dropdown at the top: 'Races' (default, existing per-race feed) ↔ 'Generic ballot / Approval / Mayoral'. Flipping Source rebinds `RAW_POLLS`, hides the Office filter (doesn't apply), and resets pinned-race state. Stage dropdown also gained generic_ballot/approval/mayoral options. Approval intentionally scoped out for this commit: the Wikipedia approval page I'd targeted produces 0 rows because it isn't laid out with a poll-source-header table; needs a separate page discovery pass (logged as future work).

## 2026-06-24

- `[7510b76]` regen: skip non-race-shaped race_ids — first production run of 3ac04c9 succeeded scraping 5955 wikipedia rows but regen crashed on `IndexError: list index out of range` at `race_id.split('-')[2]`. The wikipedia scraper produces `2026-GENERIC` and `2026-APPROVAL` race_ids for nationwide ballot / approval polls, which only have 2 hyphen-separated parts vs the 3+ that polls_data.js's per-race output requires. Added a `len(parts) < 3 → continue` guard before the split. Stage tags (`generic_ballot` / `approval`) still preserved on the rows for a future Raw Polls sub-tab. Wikipedia merge itself was working: 2,135 cross-source dedups, 8,799 polls after dedup — fix unblocks that data shipping.
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
