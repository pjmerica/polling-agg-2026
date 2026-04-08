# Handoff — Polling Aggregator & Prediction Markets

## Project Goal
Aggregate all available public polling for every US national race (Senate, House, President) and gubernatorial race. Eventually integrate prediction market prices (Polymarket, Kalshi) and build a forecasting model.

## Current State (as of 2026-04-07)

### Done
- Git repo initialized at `Polling agg and Prediction markets/`
- Directory scaffold: `scrapers/`, `analysis/`, `models/`, `notebooks/`, `utils/`, `data/raw/`, `data/processed/`
- `scrapers/kalshi.py` — **fully implemented**. Fetches all 616 Kalshi election series, matches race_ids, parses nested markets and prices. Has NOT been run yet (user chose not to execute). Run with: `py -3 scrapers/kalshi.py`
- `scrapers/polymarket.py` — **fully implemented**. Scans all Polymarket active markets, filters to election content. Run with: `py -3 scrapers/polymarket.py`
- `scrapers/fivethirtyeight.py` — **DEAD**. 538 CSVs return HTML, not data. Marked as dead in docstring.
- `scrapers/realclearpolitics.py` — **BLOCKED**. RCP returns 403 on all paths. Needs Selenium or manual export (see file for instructions).
- `utils/races.py` — canonical race list scaffold. Senate and Gov races are **partially populated** (see below). House races are **auto-generated stubs** (no incumbents yet).
- `analysis/aggregator.py` — **implemented**. Reads Kalshi + Polymarket CSVs, computes weighted average implied_prob per race, attaches race metadata, outputs to `data/processed/aggregated.csv`.

### What Still Needs To Be Done (priority order)

1. **Populate `utils/races.py` with verified 2026 race data** — IN PROGRESS
   - Senate: 33 races listed, incumbents partially filled (see notes below)
   - Governor: 36 races listed, incumbents need verification
   - House: **all 435 need incumbent party + name data** from a real source
   - Source to use: Ballotpedia, Wikipedia, or @unitedstates/congress-legislators GitHub dataset

2. **Run the scrapers to populate data/raw/**
   - `py -3 scrapers/kalshi.py`
   - `py -3 scrapers/polymarket.py`

3. **Run the aggregator**
   - `py -3 analysis/aggregator.py`
   - Output: `data/processed/aggregated.csv`

4. **Add polling data source** — RCP blocked, 538 dead
   - Option A: Use Selenium to scrape RCP (see `scrapers/realclearpolitics.py`)
   - Option B: Find another polling aggregator (NYT pages not live yet for 2026)
   - Option C: Manually export from RCP browser and drop CSVs in `data/raw/`

5. **Build forecasting model** (`models/`)
   - Combine prediction market implied_prob with polling averages
   - Weight by: market liquidity, poll recency, sample size, pollster grade

## Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| Kalshi | **Live** — implemented | 616 election series, best structured source |
| Polymarket | **Live** — implemented | Sparse for 2026 (~17 markets), mostly control questions |
| FiveThirtyEight | **Dead** | CSVs return HTML. Recheck summer 2026. |
| RealClearPolitics | **Blocked (403)** | Needs Selenium or manual browser export |
| NYT | **Not live** | 2026 pages 404. Check back closer to election. |
| Ballotpedia | Untested | Good for candidate/race metadata, scrape-able |

## Key Design Decisions
- **Race ID format**: `{year}-{office}-{state_abbrev}[-{district}]`
  - e.g. `2026-SEN-PA`, `2026-GOV-TX`, `2026-H-PA-07`
- **All data stored as CSV** in `data/raw/` (one file per source) and `data/processed/` (normalized)
- **Python only** — user prefers Python
- **No Claude co-author on commits** — commits look like normal user commits

## File Map
```
scrapers/
  kalshi.py            — IMPLEMENTED, not yet run
  polymarket.py        — IMPLEMENTED, not yet run
  fivethirtyeight.py   — stub, marked DEAD
  realclearpolitics.py — stub, marked BLOCKED
utils/
  races.py             — canonical race list (needs verification + House incumbents)
analysis/
  aggregator.py        — IMPLEMENTED, not yet run
data/
  raw/                 — EMPTY (scrapers not run yet)
  processed/           — EMPTY (aggregator not run yet)
```

## 2026 Race Notes

### Senate (Class 2 — 33 seats up)
All 33 races are listed in `utils/races.py`. Incumbents to double-check:
- Dick Durbin (IL-D) — retiring, open seat
- Mitch McConnell (KY-R) — retiring, open seat
- Gary Peters (MI-D) — retiring, open seat
- Jeanne Shaheen (NH-D) — retiring, open seat
- Patty Murray (WA-D) — retiring, open seat

### Governor (36 races)
See `utils/races.py`. Incumbents partially filled but need verification per state.

### House (435 races)
Auto-generated stubs in `utils/races.py` via `generate_house_races()`. No incumbent data.
Need to populate `incumbent_party` and `incumbent_name` for all 435.
Best source: https://github.com/unitedstates/congress-legislators

## Do Not
- Add Claude as co-author on commits
- Use `git commit --no-verify`
- Store API keys in code (use `.env` + `python-dotenv`)
