# polling-agg-2026

A live dashboard that aggregates **2026 US election data** — polling and
prediction-market prices — into one view. Published at
[pjmerica.github.io/polling-agg-2026](https://pjmerica.github.io/polling-agg-2026/).

## What it shows

Six tabs:

- **Dashboard** — per-race summary with implied probability and source counts.
- **Poll Explorer** — per-race detail with the underlying polls.
- **Raw Polls** — every individual poll. Click a row to filter to that race only.
- **Polling vs Markets** — where polling disagrees with prediction-market prices.
- **Arb Scanner** — cross-platform price mismatches across Kalshi / Polymarket / PredictIt,
  with stake sizing and tradeable depth.
- **Primaries** — 2026 primary calendar from Ballotpedia, with primary type
  (open/closed/jungle/etc), voting method (FPTP/Runoff/RCV), races on ballot,
  and runoff date if applicable.

## How it works

A GitHub Actions workflow (`.github/workflows/refresh.yml`) runs twice daily
and:

1. Scrapes Kalshi, Polymarket, PredictIt, NYT polls, and Ballotpedia.
2. Aggregates polls per race, matches markets across platforms, and computes
   cross-platform price gaps.
3. Filters out fake "arbs" caused by broken books, stale prices, mismatched
   resolution criteria, and 3-way race partition errors.
4. Commits the refreshed `docs/*.js` data feeds back to master.

GitHub Pages auto-redeploys from `/docs`.

## Running locally

```bash
pip install -r requirements.txt
python run_all.py
```

Outputs land in `data/raw/` (gitignored) and `docs/` (tracked).
Open `docs/index.html` directly to view the dashboard.

## Documentation

- [`HANDOFF.md`](./HANDOFF.md) — full architecture, file map, gotchas,
  failure semantics, and history of known bugs.

## License

Personal project. No license granted.
