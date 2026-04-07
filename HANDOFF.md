# Handoff — Polling Aggregator & Prediction Markets

## Project Goal
Aggregate all available public polling for every US national race (Senate, House, President) and gubernatorial race. Eventually integrate prediction market prices (Polymarket, Kalshi) and build a forecasting model.

## Current State (as of 2026-04-07)

### Done
- Git repo initialized at `Polling agg and Prediction markets/`
- Directory scaffold: `scrapers/`, `analysis/`, `models/`, `notebooks/`, `utils/`, `data/raw/`, `data/processed/`
- `requirements.txt` with core dependencies
- Skeleton scraper files created (see below) — **not yet implemented**, just stubs with TODOs

### What Needs To Be Done Next (priority order)

1. **Implement `scrapers/fivethirtyeight.py`** — highest priority
   - 538/ABC News publishes polling averages as public CSVs (see URLs in the file)
   - Also scrapes individual poll entries from their data
   - Key output: `data/raw/538_polls.csv`

2. **Implement `scrapers/realclearpolitics.py`**
   - RCP has JSON endpoints behind their pages (documented in the file)
   - Requires finding the hidden API calls via browser DevTools — check Network tab on any RCP polling page
   - Key output: `data/raw/rcp_polls.csv`

3. **Implement `scrapers/polymarket.py`**
   - Polymarket has a public REST API (no auth needed for read)
   - Key output: `data/raw/polymarket_markets.csv`

4. **Build `utils/races.py`** — canonical race list
   - All 2026 Senate races (33 seats up)
   - All 36 gubernatorial races up in 2026
   - House races (all 435, but focus on competitive ones)
   - This becomes the spine — scrapers normalize to these race IDs

5. **Build `analysis/aggregator.py`**
   - Weighted polling average (weight by recency, sample size, pollster grade)
   - Normalize all sources to canonical race IDs from `utils/races.py`

6. **Build `analysis/pollster_grades.py`**
   - Map pollster names to letter grades (source: 538's pollster ratings CSV)

## Data Sources

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| FiveThirtyEight/ABC | Polls + averages | Public CSV | Best structured source |
| RealClearPolitics | Poll aggregation | JSON (scrape) | Need to reverse-engineer API |
| Polymarket | Prediction market | Public REST API | `/markets` endpoint |
| Kalshi | Prediction market | Public REST API | Requires free account for some endpoints |
| Ballotpedia | Race metadata | Scrape / API | Good for candidate names, race status |

## Key Design Decisions
- **Race ID format**: `{year}-{office}-{state}-{district}` e.g. `2026-SEN-PA`, `2026-GOV-TX`, `2026-H-PA-07`
- **All data stored as CSV** in `data/raw/` (one file per source) and `data/processed/` (normalized)
- **No auth/secrets needed** for initial scrapers — all public endpoints
- **Python only** — user prefers Python for analysis

## File Map
```
scrapers/
  fivethirtyeight.py   — stub, needs implementation
  realclearpolitics.py — stub, needs implementation
  polymarket.py        — stub, needs implementation
utils/
  races.py             — stub, needs 2026 race list
analysis/
  aggregator.py        — not yet created
  pollster_grades.py   — not yet created
data/
  raw/                 — empty, scrapers write here
  processed/           — empty, aggregator writes here
```

## Do Not
- Add Claude as co-author on commits
- Use `git commit --no-verify`
- Store API keys in code (use `.env` + `python-dotenv`)
