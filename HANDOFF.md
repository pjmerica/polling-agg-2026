# Handoff — Polling Aggregator & Prediction Markets
**Last updated:** 2026-04-08  
**Status:** Data pipeline built, race universe complete, scrapers ready. NYT data endpoint partially reverse-engineered.

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
| NYT scraper | **In progress** — endpoint found, needs implementation |
| RCP scraper | **Needs Selenium** — direct HTTP blocked (403) |
| Aggregator | **Ready to run** — waits on scraper output |
| Forecasting model | **Not started** |

**data/raw/ is empty.** The scrapers have never been run. That is the immediate next step.

---

## Immediate Next Steps (in order)

### Step 1 — Run the Kalshi scraper
```
py -3 scrapers/kalshi.py
```
- Fetches ~616 election series from Kalshi's public REST API (no auth needed)
- Takes ~5–10 minutes (polite 0.3s delay)
- Writes: `data/raw/kalshi_markets.csv`

### Step 2 — Run the Polymarket scraper
```
py -3 scrapers/polymarket.py
```
- Scans all active Polymarket markets, filters to US election content
- ~30 seconds
- Writes: `data/raw/polymarket_markets.csv`
- Note: sparse for 2026 (~17 markets), mostly control questions not individual races

### Step 3 — Implement `scrapers/nytimes.py` (see section below)

### Step 4 — Run the aggregator
```
py -3 analysis/aggregator.py
```
- Reads all raw CSVs, computes weighted average implied probability per race
- Joins race metadata from utils/races.py
- Writes: `data/processed/aggregated.csv` and `data/processed/combined_raw.csv`

---

## NYT Polling Scraper — What We Know

**The polls live at:** `https://www.nytimes.com/polls` (note: NOT `/interactive/polls` — that 404s)

**Individual race pages follow this URL pattern:**
```
https://www.nytimes.com/interactive/polls/{slug}-polls-2026.html
```
Examples found on the /polls index page:
- `louisiana-us-senate-election-polls-2026`
- `pennsylvania-us-house-7-polls-2026`
- `pennsylvania-us-house-8-polls-2026`
- `kentucky-us-house-4-polls-2026`
- `georgia-us-house-13-polls-2026`
- `alabama-us-house-1-polls-2026`
- `new-jersey-us-house-11-special-polls-2026`
- `oregon-governor-election-polls-2026`

**The architecture:** NYT uses SvelteKit (via their "birdkit" wrapper). Pages are server-side rendered and hydrated client-side. Poll data is embedded in the HTML as serialized SvelteKit state — it does NOT require a separate API call to display.

**The data blob:** Found in a `{"type":"data",...}` block inside the page HTML. The navbar data is already confirmed accessible:
```python
svelte_data = re.findall(r'\{"type":"data".*?(?=\{"type":"data"|\s*;\s*\n)', html, re.DOTALL)
```
The first blob contains `navbar` with the list of all race slugs (highlighted races). The second blob should contain the actual poll data for the race — but the regex to extract it cleanly still needs work.

**There is also a static data directory at:**
```
https://static01.nytimes.com/newsgraphics/1l-LoDPzimB8FQ/4e04447c37dc523e45fb5cf2f1c4bcd14f563442/data
```
This path appears in the page source. Individual file paths inside it (e.g. `/polls.json`, `/{slug}.json`) returned 404 — the naming convention isn't confirmed yet.

**There is a GraphQL endpoint** at `https://samizdat-graphql.nytimes.com/graphql/v2` with an `nyt-token` embedded in the page. Not yet tried.

**Recommended approach for implementation:**
1. Fetch `https://www.nytimes.com/polls` → parse all race slugs from the page (they appear as `/interactive/polls/{slug}-polls-2026.html` links)
2. For each slug, fetch the individual race page
3. Extract the SvelteKit data blob — the actual poll entries should be in the second `{"type":"data"...}` block
4. Parse poll rows: pollster, date, sample size, candidates, percentages
5. Normalize to standard schema with `race_id` from utils/races.py

**Slug → race_id mapping:** NYT slugs follow `{state}-{office}-{district}-polls-2026`. Write a regex to extract state + office + district and map to canonical race_id.

---

## RCP Status

Direct HTTP is fully blocked (403 on all paths including root domain). Options:
1. **Selenium**: Implement in `scrapers/realclearpolitics.py` — the stub is there with instructions
2. **Manual**: Open race pages in browser → DevTools → Network → find `/epolls/json/XXXXX_latest.js` requests → copy the numeric race IDs into the scraper
3. **Skip for now**: NYT has polling data too, which is more accessible

---

## Data Sources Summary

| Source | Status | Output |
|--------|--------|--------|
| **Kalshi** | Live, implemented | `data/raw/kalshi_markets.csv` |
| **Polymarket** | Live, implemented | `data/raw/polymarket_markets.csv` |
| **NYT** | Partially reversed, needs scraper | `data/raw/nyt_polls.csv` |
| **RCP** | Blocked (403), needs Selenium | `data/raw/rcp_polls.csv` |
| **538** | Dead — ignore entirely | — |

---

## Race Universe

**Total: 511 races**

- **Senate: 37** (35 regular Class 2 + FL special [Rubio resigned] + OH special [Vance resigned])
  - 13 open seats: Durbin/IL, Ernst/IA, McConnell/KY, Peters/MI, Smith/MN, Daines/MT, Tillis/NC, Shaheen/NH, Murray/WA, Lummis/WY, Tuberville/AL (running for Gov), FL vacancy, OH vacancy
- **Governor: 39** — 20 open seats (16 term-limited, 3 retiring)
- **House: 435** — 62 known open seats, R=220/D=217 currently

**`open_seat=True`** = incumbent is NOT on the ballot (retired, term-limited, running for higher office, or resigned). Seat has no incumbent advantage.

---

## Key Design Decisions

**Race ID format:** `{year}-{office}-{state_abbrev}[-{district}]`
- Regular: `2026-SEN-PA`, `2026-GOV-TX`, `2026-H-PA-07`
- Special elections: `2026-SEN-FL-S`, `2026-SEN-OH-S`

**Prediction market prices** stored as `implied_prob` 0.0–1.0. Kalshi raw prices are 0–100 cents; scraper converts.

**Weighting:** prediction markets by `open_interest`/`liquidity`. Future polls by `f(sample_size, recency, pollster_grade)`.

---

## File Map

```
scrapers/
  kalshi.py            IMPLEMENTED — run first
  polymarket.py        IMPLEMENTED — run second
  nytimes.py           DOES NOT EXIST YET — implement next (see above)
  house_incumbents.py  IMPLEMENTED — re-run to refresh open seat list
  fivethirtyeight.py   stub, DEAD — ignore
  realclearpolitics.py stub, BLOCKED — needs Selenium

utils/
  races.py             COMPLETE — 511 races, all metadata, loads house_incumbents.json

analysis/
  aggregator.py        IMPLEMENTED — run after scrapers

models/                EMPTY — build forecasting model here

data/
  raw/                 EMPTY — run scrapers to populate
  processed/
    house_incumbents.json   done (435 House members)
    house_incumbents.csv    done (human-readable)
    aggregated.csv          not yet (run aggregator)
    combined_raw.csv        not yet (run aggregator)

requirements.txt       pip install -r requirements.txt
                       also: pip install pyyaml
```

---

## Do Not
- Add Claude as co-author on commits — plain commits only
- Store API keys in code — use `.env` + `python-dotenv`
- Touch scrapers/fivethirtyeight.py — 538 is dead, skip it
