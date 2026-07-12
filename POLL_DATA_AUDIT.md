# Poll Data Audit — population labels, pollster partisanship, candidate parties

**Date:** 2026-07-10 · **Scope:** the raw poll feeds (`data/raw/nyt_polls.csv`,
`data/raw/wikipedia_polls.csv`), how they're normalized in `scripts/regen_data.py`, and how
the model repo consumes them. Written so the next agent can pick up all of it.

## 1. Population labels (LV / RV / A / V) — NEW, now end-to-end

Every poll now carries a surveyed-population tag:
- **LV** = likely voters, **RV** = registered voters, **A** = all adults, **V** = voters.

**Where it flows:**
- `scrapers/nytimes.py` — the NYT CSV already has a `population` column; we now pass it
  through to `data/raw/nyt_polls.csv` (was being dropped). Values: mostly `lv`, some `rv`,
  few `a`.
- `scrapers/wikipedia_polls.py` — `parse_population()` extracts the tag from the sample cell
  (`"468 (LV)"` → `lv`). Added to each emitted row.
- `scripts/regen_data.py` — carries `population` onto each poll object in `polls_data.js`.
- `docs/index.html` — teal **LV/RV/A** badge on the Raw Polls rows and Poll Explorer cards,
  plus a **Population** filter dropdown on the Raw Polls tab. Hover shows the full name.

**Quality note:** LV polls are generally the most predictive near an election; A (adult) polls
are the least election-relevant. The model does NOT yet use population as a feature — it's
display-only for now. Candidate feature for a future model batch: down-weight or flag A polls.

## 2. Pollster partisanship — audited + normalized

**The problem found:** the two feeds were inconsistent and partly wrong.
- NYT tags `DEM/REP/IND/WFP/NPA`; Wikipedia tags `D/R/I` — different vocabularies.
- Wikipedia's tag often reflected the **sponsor** of an individual poll, not the pollster's
  own house lean, so the *same pollster flipped tags between rows* (Public Policy Polling
  showed both `D` and `I`; a neutral pollster fielding for a partisan client got mislabeled).
- Several well-known partisan firms carried **no tag** in one or both feeds.

**The fix:** `scrapers/pollster_partisanship.py` — a curated reference of ~70 hand-verified
firms (Democratic / Republican / Independent house leans, from 538 pollster ratings, AAPOR
membership, and firms' public descriptions) plus `normalize_partisan(pollster, feed_tag)`:
1. curated reference wins when the pollster is known (corrects bad feed tags),
2. else the feed tag mapped to `D/R/I` (kept — most feed tags are right).

`regen_data.py` now emits a clean **`partisan_lean`** (`D`/`R`/`I`/`''`) per poll; the Raw
Polls badge uses it ("D-lean" / "R-lean" / "I-lean", hover = full name).

**Audit result on current data:** of pollsters appearing in the feed — 55 confirmed OK vs the
reference, **5 CORRECTED** (contradictory feed tags resolved: Public Policy Polling, Change
Research, Data for Progress → D; Opinion Diagnostics, Kaplan Strategies → R), 318 had no
reference entry but a single consistent feed tag (left as-is). Only **2 hard cross-feed
conflicts** existed (Kaplan Strategies, Opinion Diagnostics — both resolved to R).

**To extend:** add rows to `_RAW_REFERENCE` in `scrapers/pollster_partisanship.py`. Keys are
lowercased-alphanumeric, so spelling/punctuation variants collapse automatically. Top
un-referenced firms by volume (safe to add if you verify): Alaska Survey Research (D),
Evitarus (D), Harper Polling (R), Big Data Poll (R), EMC Research (D).

## 3. Candidate party corrections (model repo)

Feed party labels had a handful of real errors that distort the model's two-party framing.
Fixed via committed override files **in the model repo** (`Polling prediction model/data/`),
applied inside `predict.py`:

- **`candidate_party_overrides.csv`** — audited feed errors:
  - **Dan Osborn (NE-SEN)**: NYT labeled him **DEM**; he runs as an **independent** → set to
    IND (OTH). This mattered: he was being treated as the Democratic nominee.
  - **Kelly Loeffler (GA-SEN)**: one feed tagged IND → REP.
- **`dropped_out_2026.csv`** — candidates who ended their campaigns; their stale poll rows are
  removed so they don't linger as phantom options:
  - **Mike Duggan (MI-GOV)**: ended his independent bid → excluded.

Verified after regen: Osborn now OTH in `predictions_2026.csv` (NE-Sen two-party framing
correct), Duggan removed from MI-GOV.

**Maintenance:** these are 2026-specific, hand-maintained lists. When a candidate drops out or
a party label is wrong, add a row and re-run `refresh_dashboard.py`. Keys are `cand_key`
(features.norm_name → "lastname firstinitial", e.g. `osborn d`).

## 4. General Raw-Polls sanity checks (all clean or explained)

- **implied_prob** all within [0,1]; no nulls. ✔
- **No polls dated after their election**; no year mismatches (from the earlier dataset audit). ✔
- **Cross-source duplicates**: collapsed in `regen_data.py` (name-overlap dedup + a
  content-level dedup net on race/pollster/date/candidate/pct). ✔
- **Multi-question polls** (named matchup + generic ballot under one poll_id) correctly render
  as separate rows — this was the "8 vs 6" confusion, not a bug.
- **Stage tags imperfect upstream**: a few genuine primary/jungle-primary polls are labeled
  `general` in the feed (e.g. CA-14). The model drops the junk/generic answers those polls are
  dominated by, so impact is limited, but the feed's `stage` column is not 100% trustworthy.
- **Party conflicts**: 37 candidate/party disagreements across feeds — 31 are the
  "Generic Democrat/Republican" placeholders (feeds split DEM vs IND; model filters these
  anyway); 6 were real candidates, now handled by the override/dropout files above.

## Files touched
- `scrapers/nytimes.py` — pass through `population`.
- `scrapers/wikipedia_polls.py` — `parse_population()` + emit `population`.
- `scrapers/pollster_partisanship.py` — NEW: curated reference + `normalize_partisan()` + `audit()`.
- `scripts/regen_data.py` — emit `population` and normalized `partisan_lean` per poll.
- `docs/index.html` — population badges/filter; partisan badge uses normalized lean.
- Model repo `data/candidate_party_overrides.csv`, `data/dropped_out_2026.csv` — NEW.
- Model repo `predict.py` — applies both override files.

## Next steps / open items
- Population as a **model feature** (flag/adult-downweight) — needs a training-side change +
  retrain (the historical `polls_long_with_results.csv` has a `population` column already).
- Keep `_RAW_REFERENCE` and the 2026 override/dropout CSVs current as the cycle evolves.
- Upstream stage-tag unreliability is a standing feed-quality caveat (see model repo
  HANDOFF.md).
