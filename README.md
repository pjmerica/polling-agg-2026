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

A GitHub Actions workflow (`.github/workflows/refresh.yml`) runs twice
daily (**12:00 + 00:00 UTC** — 08:00 and 20:00 ET) and:

1. Scrapes Kalshi, Polymarket, PredictIt, NYT polls, and Ballotpedia.
2. Aggregates polls per race, matches markets across platforms, and computes
   cross-platform price gaps.
3. Filters out fake "arbs" caused by broken books, stale prices, mismatched
   resolution criteria, and 3-way race partition errors. The
   `scripts/scrutiny.py` module fetches each market's resolution rules for
   any pair > 30pp gap and drops pairs whose criteria diverge.
4. Commits the refreshed `docs/*.js` data feeds back to master.

GitHub Pages auto-redeploys from `/docs`. Cron is best-effort — actual
fire time can lag 5–30 min.

If any scraper returns empty data (transient outage or API change), the
run fails fast and the commit step is skipped, so the live dashboard
keeps showing the last good snapshot rather than going stale silently.
Ballotpedia's primaries scraper is the one exception — it tolerates an
empty calendar (which happens naturally late in the cycle) and keeps the
prior `docs/primaries_data.js`.

## Running locally

Requires **Python 3.12** (the version pinned in
`.github/workflows/refresh.yml`).

```bash
pip install -r requirements.txt
python run_all.py
```

A full run takes ~10–15 minutes — most of that is the Polymarket scrape
and `scripts/fetch_depth.py` polling orderbooks for every matched pair.
During iterative development you can re-run just one step against the
already-cached CSVs in `data/raw/`:

```bash
python scripts/regen_data.py     # rebuild docs/data.js + polls_data.js
python scripts/arb_scanner.py    # re-score arb pairs
```

Outputs land in `data/raw/` (gitignored) and `docs/` (tracked).
Open `docs/index.html` directly to view the dashboard.

## Documentation

- [`HANDOFF.md`](./HANDOFF.md) — full architecture, file map, gotchas,
  failure semantics, and history of known bugs.

## License

See [`LICENSE`](./LICENSE). All rights reserved — personal project, not
open source. No license is granted to copy, modify, or redistribute.
