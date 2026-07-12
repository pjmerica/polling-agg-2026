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

## 3. Candidate party corrections + effective-party slot (model repo)

Feed party labels had real errors that distort the model's two-party framing. Fixed via
committed override files **in the model repo** (`Polling prediction model/data/`), applied in
`predict.py`.

**`candidate_party_overrides.csv`** has TWO party columns (this is the key design point):
- **`model_party`** — what the MODEL treats them as (`party_std`). Fills the two-party slot so
  `poll_lead`, two-party margin, and win-prob normalization work.
- **`display_party`** — their REAL affiliation, shown on the dashboard.

Current rows:
- **Dan Osborn (NE-SEN)**: `model_party=DEM`, `display_party=IND`. Osborn is an independent but
  the de-facto main challenger vs Ricketts (NE Democrats didn't field a nominee). Modeling him
  in the DEM slot gives a real two-way (Ricketts ~78 / Osborn ~22); the tab shows **"Dan
  Osborn (I)"**. **User decision 2026-07-12** — do NOT "correct" his model party back to IND,
  it collapses the two-party math. (See model-repo AGENTS.md rule 9.)
- **Kelly Loeffler (GA-SEN)**: REP/REP — plain correction of a bad IND feed tag.

**`dropped_out_2026.csv`** — remove stale poll rows for candidates not in the general:
- **Mike Duggan (MI-GOV)**: withdrew.
- **Cindy Burbank, William Forbes (NE-SEN)**: fringe also-rans in early multi-way ballot tests;
  removed so Osborn is the clean two-way challenger.

**Flow:** `predict.py` sets `party_std`=model_party and carries `display_party` as a separate
column; `features.py` passes it through; `predict.py`/`predict_margin.py`/`explain_2026.py`
emit it; `analysis/model_compare.py` emits `dem_display`; the Model-vs-Markets tab appends
"(I)" when the Dem-slot candidate isn't actually a Democrat.

**Maintenance:** hand-maintained 2026 lists. Candidate drops out, party is wrong, or an
independent is the real challenger → add a row, re-run `refresh_dashboard.py`. Keys are
`cand_key` (features.norm_name → "lastname firstinitial", e.g. `osborn d`).

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
- Model repo `data/candidate_party_overrides.csv` (model_party + display_party),
  `data/dropped_out_2026.csv` — NEW.
- Model repo `predict.py` / `predict_margin.py` / `explain_2026.py` / `features.py` — apply
  the overrides + carry `display_party` through to output.
- `analysis/model_compare.py` — emits `dem_display`; `docs/index.html` — "(I)" marker.

## Next steps / open items
- Population as a **model feature** (flag/adult-downweight) — needs a training-side change +
  retrain (the historical `polls_long_with_results.csv` has a `population` column already).
- Keep `_RAW_REFERENCE` and the 2026 override/dropout CSVs current as the cycle evolves.
- Upstream stage-tag unreliability is a standing feed-quality caveat (see model repo
  HANDOFF.md).
