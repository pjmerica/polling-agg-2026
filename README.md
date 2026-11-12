# polling-agg-2026

Polls, a forecast and prediction-market prices for every 2026 US Senate, House and Governor
race, plus the election-night desk and the record of the count. Published at
[pjmerica.github.io/polling-agg-2026](https://pjmerica.github.io/polling-agg-2026/).

**Status (2026-11-12):** the election was Nov 3. The forecast is frozen as published before
the count (tag `forecast-before-polls-2026`). The poll, market and model refreshes are switched
off. The count is still being recorded, through Dec 15.

## The pages

| Page | What it shows |
|---|---|
| [Main dashboard](https://pjmerica.github.io/polling-agg-2026/) | Model vs Markets (general and primary), Poll Explorer, Raw Polls, Arb Scanner, Primaries |
| [Forecast](https://pjmerica.github.io/polling-agg-2026/predictions.html) | The model's prediction for every race: each candidate, margin, win chance, and what drives it |
| [Forecast map](https://pjmerica.github.io/polling-agg-2026/map.html) | Senate, House and Governor maps by margin, win chance, or model against the markets |
| [Counting guide](https://pjmerica.github.io/polling-agg-2026/election-night.html) | How and when each state counts and reports its votes |
| [Election desk](https://pjmerica.github.io/polling-agg-2026/election-night-desk.html) | The live count against the model, county by county, with both markets' prices |
| [2024 replay](https://pjmerica.github.io/polling-agg-2026/election-night-replay.html) | Election night 2024 replayed minute by minute |

## What is in the repo

| Folder | What it is |
|---|---|
| `scrapers/`, `scripts/`, `analysis/`, `utils/` | The dashboard pipeline: scrape polls and markets, match them, scan for arbitrage, build the data files |
| `docs/` | The GitHub Pages site |
| `Election night simulator/` | The live projector, the cloud desk, the 2024 replay, the market price archive |
| `State election results/` | State-by-state counting guides and county benchmarks |
| `Precinct data 2026/` | Precinct results and ballot returns for all 50 states |
| `tests/`, `tools/` | Regression tests, page smoke tests, link and deploy checks |
| `history/` | Older handoff notes and audits |

The forecast itself comes from a separate repo, `pjmerica/Polls-prediction-model`.

## The raw record

Everything recorded on and after election night is on the release
[`election-night-2026`](https://github.com/pjmerica/polling-agg-2026/releases/tag/election-night-2026):
NYT's count as it changed, all 435 districts by county, both markets' order books, the
projector's inputs and outputs, precinct files and market price history. Its notes say what is
where and list the known gaps.

## Running the dashboard pipeline locally

Python 3.12.

```bash
pip install -r requirements.txt
python run_all.py                # everything, 10 to 15 minutes
python run_all.py --markets-only # markets and arb scan only
python -m pytest tests -q
```

Outputs land in `data/raw/` (gitignored) and `docs/` (tracked). If a scraper gets no usable
data the run stops and nothing is committed, so the site keeps its last good copy.

## Documentation

- [`HANDOFF.md`](./HANDOFF.md): what is running, the pipeline, the arb scanner, gotchas.
- [`CHANGELOG.md`](./CHANGELOG.md): every hand-written change and why.
- Each project folder has its own README.

## License

See [`LICENSE`](./LICENSE). All rights reserved: a personal project, not open source. No
license is granted to copy, modify, or redistribute.
