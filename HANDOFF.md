# Handoff — Polling Aggregator & Prediction Markets
**Last updated:** 2026-04-07  
**Status:** Data pipeline built, scrapers ready to run, race universe complete.

---

## What This Project Does

Aggregates all available public polling and prediction market data for every 2026 US national race — Senate, House, Governor — into a unified dataset keyed by canonical race IDs. Eventually feeds a forecasting model.

---

## Current State at a Glance

| Layer | Status |
|-------|--------|
| Race universe (utils/races.py) | **Complete** — 511 races fully populated |
| House incumbents (data/processed/) | **Done** — all 435 scraped and saved |
| Kalshi scraper | **Ready to run** — not yet executed |
| Polymarket scraper | **Ready to run** — not yet executed |
| Aggregator | **Ready to run** — waits on scraper output |
| Polling data (RCP/538) | **Blocked** — see Data Sources section |
| Forecasting model | **Not started** |

**data/raw/ is empty.** The scrapers have never been run. That's the immediate next step.

---

## Immediate Next Steps (in order)

### Step 1 — Run the Kalshi scraper
```
py -3 scrapers/kalshi.py
```
- Fetches ~616 election series from Kalshi's public REST API
- Takes ~5–10 minutes (polite 0.3s delay between requests)
- Writes: `data/raw/kalshi_markets.csv`

### Step 2 — Run the Polymarket scraper
```
py -3 scrapers/polymarket.py
```
- Scans all active Polymarket markets, filters to US election content
- Takes ~30 seconds
- Writes: `data/raw/polymarket_markets.csv`
- Note: 2026 election coverage is sparse on Polymarket (~17 markets as of 2026-04-07). Mostly control questions (who wins Senate/House), not individual races.

### Step 3 — Run the aggregator
```
py -3 analysis/aggregator.py
```
- Reads both raw CSVs, computes weighted average implied probability per race
- Joins race metadata (state, office, incumbent, open seat flag)
- Writes: `data/processed/aggregated.csv` and `data/processed/combined_raw.csv`
- Prints top 10 most competitive races (closest to 50/50)

### Step 4 — Refresh House incumbents (if stale)
```
py -3 scrapers/house_incumbents.py
```
- Already run once — output is in `data/processed/house_incumbents.json`
- Re-run periodically as more members announce retirements
- Source: congress-legislators GitHub YAML + Ballotpedia non-running list

---

## Race Universe

**Total: 511 races**

### Senate — 37 races
- 35 regular Class 2 seats + 2 special elections
- Special elections:
  - `2026-SEN-FL-S` — Marco Rubio resigned to become Secretary of State
  - `2026-SEN-OH-S` — JD Vance resigned to become VP
- **13 open seats** (incumbent not running):
  - Retiring: Durbin (IL), Ernst (IA), McConnell (KY), Peters (MI), Smith (MN), Daines (MT), Tillis (NC), Shaheen (NH), Murray (WA), Lummis (WY)
  - Running for Governor: Tuberville (AL)
  - Special vacancies: FL, OH

### Governor — 39 races
- **20 open seats** — 16 term-limited, 3 retiring (Reynolds/IA, Walz/MN, Evers/WI)
- Does NOT include LA, MS (odd-year elections), VA, NJ (2025), or states with no 2026 race

### House — 435 races
- **62 known open seats** as of 2026-04-07
- R: 220 seats, D: 217 seats currently held
- Incumbent data: loaded from `data/processed/house_incumbents.json`
- Open seat flag (`open_seat=True`) = incumbent is NOT on the ballot. Reasons:
  - `retiring` — chose not to run
  - `term-limited` — constitutionally barred (governors only; House has no term limits)
  - `running-for-senate` / `running-for-governor` — moving to higher office
  - `resigned` / `died` — vacancy

---

## Data Sources

| Source | Status | Output file |
|--------|--------|-------------|
| **Kalshi** | Live, implemented | `data/raw/kalshi_markets.csv` |
| **Polymarket** | Live, implemented | `data/raw/polymarket_markets.csv` |
| **FiveThirtyEight** | **DEAD** — CSVs return HTML | — |
| **RealClearPolitics** | **BLOCKED** — 403 on all paths | — |
| **NYT** | Not live yet for 2026 | — |
| **congress-legislators** | Live (GitHub YAML) | `data/processed/house_incumbents.json` |
| **Ballotpedia** | Live (scrape-able) | merged into above |

### Getting polling data (RCP workaround)
RCP blocks all programmatic access. Options:
1. **Manual export**: Open RCP race pages in browser → DevTools → Network tab → find `/epolls/json/XXXXX_latest.js` requests → copy those URLs into `scrapers/realclearpolitics.py`'s `RCP_RACE_URLS` dict
2. **Selenium**: `pip install selenium` + chromedriver, implement in `scrapers/realclearpolitics.py` (stub is already there with instructions)
3. **Wait**: NYT typically activates 2026 polling pages by summer 2026

---

## Key Design Decisions

**Race ID format:** `{year}-{office}-{state_abbrev}[-{district}]`
- Regular: `2026-SEN-PA`, `2026-GOV-TX`, `2026-H-PA-07`
- Special: `2026-SEN-FL-S`, `2026-SEN-OH-S`

**`open_seat=True`** means the incumbent is not running. The seat is contested without an incumbent on the ballot. This is the most important predictor of competitiveness after partisanship.

**Prediction market prices** (Kalshi/Polymarket) are stored as `implied_prob` on a 0.0–1.0 scale. Kalshi raw prices are in cents (0–100); the scraper converts to decimal. These are the probability that a specific outcome wins — e.g. `implied_prob=0.87` on a "Will Democrats win Senate race in California?" market = 87% implied probability.

**Weighting in aggregator:** prediction markets weighted by `open_interest` (Kalshi) or `liquidity` (Polymarket). When polls are added later, weight by `f(sample_size, recency, pollster_grade)`.

---

## File Map

```
scrapers/
  kalshi.py            IMPLEMENTED — run me first
  polymarket.py        IMPLEMENTED — run me second
  house_incumbents.py  IMPLEMENTED — re-run to refresh open seat list
  fivethirtyeight.py   stub, DEAD (marked in docstring)
  realclearpolitics.py stub, BLOCKED (instructions in docstring)

utils/
  races.py             COMPLETE — 511 races, all metadata populated
                       loads house incumbents from data/processed/house_incumbents.json

analysis/
  aggregator.py        IMPLEMENTED — run after scrapers

models/                EMPTY — build forecasting model here

data/
  raw/                 EMPTY — populated by running scrapers
  processed/
    house_incumbents.json  435 House members with open seat flags (done)
    house_incumbents.csv   same, human-readable (done)
    aggregated.csv         populated by aggregator (not yet run)
    combined_raw.csv       populated by aggregator (not yet run)

notebooks/             EMPTY — Jupyter notebooks for exploration

requirements.txt       core deps (requests, pandas, numpy, pyyaml, etc.)
```

---

## Installing Dependencies

```
pip install -r requirements.txt
pip install pyyaml   # needed for house_incumbents.py
```

---

## Do Not
- Add Claude as co-author on commits — plain commits only
- Store API keys in code — use `.env` + `python-dotenv`
- Run `git commit --no-verify`
