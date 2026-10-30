# Election night simulator

Goal: on Nov 3, 2026, catch Kalshi and Polymarket prices that misread the vote count. As each state
reports, the projector estimates where the count will finish from what is still uncounted, turns that into
a win probability, and sets it against the live order books after fees.

It covers the 15 competitive Governor and Senate races from `../State election results/competitive_races.md`,
plus Senate and House control (prices only).

That folder has the research (how each state counts, past swings, county benchmarks) and records NYT's
results. This folder records the markets, projects the count and compares the two. **Method and backtest:
[METHODS.md](METHODS.md). Whether 2024's markets misread the count: [MARKET_CHECK.md](MARKET_CHECK.md).**

**2024 in one line:** markets read the count better than v0 at every stage; the big misses were three
Democratic Senate winners priced at 2-17c overnight (WI, MI, NV), while Pennsylvania looked the same and went
the other way. Don't trade v0's edge alone. The opportunity is overnight wide books in close races with a known
late batch, and catching it needs v1.

**Close races, not primaries:**
- Colorado's Republican governor primary was the deepest misread found: Marx went from 93% before the count
  to 2.8c in a tight book, and won by 0.47.
- But across 45 primaries and 57 generals, close races of either kind put the eventual winner under 50c
  about 2 times in 5. The market follows the visible leader.
- A within-night trend of the latest batches did no better than the visible margin. The edge is knowing
  which counties are still out (v1).

Started 2026-10-28.

## Status

| Piece | State |
|---|---|
| Market price capture (`capture_markets.py`) | **Built**, tested on live APIs. The scheduled tasks need registering once by hand (below) |
| Projector v0, statewide (`live_project.py`) | **Built**, backtested. Beats the visible margin in KS, IA, TX, OH, NE, MI, ME; not in GA, OR, NV, AK, SC (`?` flag). **Not better than the markets** (MARKET_CHECK.md): use it as an alert, not a trade signal |
| Historical check, 2024 (`market_history.py`, `market_check.py`) | **Done** 2026-10-28: 65 races, minute prices from both venues against NYT's count |
| Primaries vs the markets (`primary_check.py`) | **Done and published** 2026-10-29: 54 primaries against the 2024 generals, on the dashboard page [primaries-vs-markets.html](https://pjmerica.github.io/polling-agg-2026/primaries-vs-markets.html) |
| Projector v1, county by county (`county_project.py`, wired into `live_project.py`) | **Built and tested 2026-10-29.** Beats v0 and the visible margin in 2020 (also leave-one-state-out) and in 2022 out of sample (miss 1.1 vs v0 4.1, visible 1.9). **Against the 2024 markets it is worse on average** (Brier .050 vs .035; trading every edge lost $1.41 over 29 trades). Only "flips" paid, where v1 gives a side ~50% that the market prices far lower: 3 trades, +$1.21 (Slotkin 15c, Rosen 33c won; one Nevada flip lost). The live table marks these `FLIP`. Weakest where absentees come last inside big counties (MI 2020) and where NYT's expected vote is off (OH 2020) |
| Pre-election Monte Carlo: thousands of simulated nights, a threshold sheet per state | To build, on v1 |
| Election-night console page with alerts | To build |

## Layout

| Path | What |
|---|---|
| `METHODS.md` | How the projector works, the backtest, what it can't do, the v1 plan |
| `scripts/capture_markets.py` | Records Kalshi and Polymarket books every 20 s -> `data/raw/markets/{ET date}/{kalshi,polymarket}.csv` |
| `scripts/live_project.py` | The live table (v1 where the counties line up, v0 beside it), what-ifs, v0 backtest |
| `scripts/county_project.py` | Projector v1: county by county, simulated (METHODS.md) |
| `scripts/county_replay.py` | Replays v1 through the 2020 count (`--tune` tries settings) -> `data/processed/county_replay_2020.csv` |
| `scripts/fetch_wayback_full.py` | Downloads whole Internet Archive captures of NYT's 2022/2024 results files (votes by candidate per county) for the out-of-sample replay -> `data/raw/wayback_full/` |
| `MARKET_CHECK.md` | Did the 2024 markets misread the count? Results, traps (settlement, spreads), what it means for Nov 3 |
| `scripts/market_history.py` | Downloads 2024 minute prices from both venues for every race with an NYT timeline -> `data/raw/market_history/2024/` (about 11 min) |
| `scripts/market_check.py` | The 2024 check -> `data/processed/market_check_2024_{points,trades}.csv` |
| `scripts/build_primaries_page.py` | Builds the dashboard page `docs/primaries-vs-markets.html` (+ `docs/primaries_vs_markets_data.js`) from primary_check.py's output. Rebuild after primary_check.py, then `node tests/dash_smoke.js docs/primaries-vs-markets.html` |
| `scripts/primary_check.py` | Every 2026 Senate/Governor primary with a market against the 2024 generals: how cheap the winner got, and how often the market, the visible leader and the batch trend named the winner -> `data/processed/primary_check_{2026,compare}.csv` |
| `scripts/co_primary_check.py` | The Colorado Republican governor primary (June 30, 2026): count, trend and Marx's price -> `data/processed/co_gov_rep_2026_trend.csv` |
| `scripts/run_markets.cmd` | Wrapper the scheduled tasks call (log: `data/raw/markets/capture.log`) |
| `scripts/register_market_tasks.ps1` | Registers the three `ElectionSim-*` scheduled tasks (run once) |
| `data/processed/live_project_backtest.csv` | Every backtest prediction (state, year, race, share counted, error, P) |
| `data/raw/` | Not committed: market captures, `projections.csv` (every projection printed live) |

**Inputs from `../State election results/`** (read only):
- `data/processed/state_timeseries.csv`: the 2020-2024 NYT count timelines, built by `state_curves.py`.
- `data/raw/live/{date}/{race}/*.json.gz`: NYT's 2026 results files, recorded by `capture_live.py` under the
  `StateResults-ElectionNight` task.
- `state_curves.CLOSE_ET`: each state's poll close.

**Inputs from the repo:**
- `docs/forecast_data.js`: the model's win probabilities.
- `utils/fees.py`: real fees per leg.
- `utils/http_headers.py`: request headers.
- `data/raw/{kalshi,polymarket}_markets.csv`: fee parameters. If these files are missing, Kalshi uses
  multiplier 1 and Polymarket rate 0.04.

## Recording the markets

```
py "Election night simulator/scripts/capture_markets.py" --once      # one pass: check that every market is found
py "Election night simulator/scripts/capture_markets.py"             # every 20 s until Ctrl+C
```

Each pass writes one row per market:
- best bid and ask, with sizes;
- last trade;
- the top 5 levels each side, as `price:size|...`, best first.

Prices are dollars per $1 YES contract. Kalshi's YES ask is 1 minus its best NO bid.

**Which markets are recorded.** Markets come from a reviewed list of events (`RACES`), checked against both
APIs on 2026-10-28. The list is needed because event tickers are not predictable: Kalshi's Kansas Governor is
`GOVPARTYKS-27`, named for the 2027 inauguration.
- Every active market in each event is recorded, and the list is re-read every 30 min.
- Polymarket's placeholder outcomes ("Candidate C", "Option A", no bid) are skipped.
- Nebraska is Republican vs independent (Osborn) on both venues.
- Polymarket lists Alaska per candidate.

**Trade histories** are not recorded. They can be downloaded afterwards: Kalshi `GET /markets/trades`,
Polymarket `data-api.polymarket.com/trades?market=<conditionId>`.

### Scheduled tasks

Register them once (an automated attempt was blocked as persistence, so this is by hand):

```
powershell -ExecutionPolicy Bypass -File "Election night simulator\scripts\register_market_tasks.ps1"
```

| Task | When | What |
|---|---|---|
| `ElectionSim-MarketsCheck` | 9:05 a.m. daily, Oct 29 - Nov 2 | one pass: a daily check, and a pre-election baseline |
| `ElectionSim-Markets` | Nov 3 noon ET to Nov 6 noon ET | every 20 s; the baseline before the first poll close (7 pm ET) |
| `ElectionSim-MarketsLate` | Nov 6 noon to Nov 25 | every 5 min (Nevada's late count, Alaska's count days, Maine ranked-choice) |

The task settings match `StateResults-ElectionNight`: wake the PC, run on battery, start late if missed.
While recording, the script also holds off sleep, as `capture_live.py` does, because this PC's Modern
Standby suspends background programs. Keep the PC plugged in with the lid open on Nov 3.

Remove the tasks after the election:
`Get-ScheduledTask -TaskName "ElectionSim-*" | Unregister-ScheduledTask -Confirm:$false`

## Running the projector

```
py "Election night simulator/scripts/live_project.py"                    # once: every race, latest captures
py "Election night simulator/scripts/live_project.py" --watch 60         # every 60 s
py "Election night simulator/scripts/live_project.py" --race KS-Sen --pct 40 --margin 12    # what-if
py "Election night simulator/scripts/live_project.py" --baseline model   # edges against our model instead
py "Election night simulator/scripts/live_project.py" --backtest         # leave-one-year-out check
```

`--date` (default `2026-11-03`) picks which day's captures to read.

Reading the table (margins are non-Republican minus Republican, in points of all votes; P is the chance the
non-Republican wins):

| Column | Meaning |
|---|---|
| `counted`, `margin` | NYT's share of the expected vote counted (`eevp`) and the visible margin |
| `v1 proj`, `+/-80%`, `P v1` | Projector v1 (county by county): projected final margin, the half-width of its 80% band, and P(win). It starts from the markets' price at poll close by default (`--baseline model` for our model), so its edge comes from the count. Blank where the live counties don't line up with the benchmarks (Alaska's districts); then v0 is used |
| `P v0` | The statewide projector from the same starting point. A `?` before the row means v0 is in use and past years' late votes leaned opposite ways at this point in the count, so the direction is a guess |
| `P mod` | v0 starting from our model's win probability instead |
| `close` | The market price at poll close that `P mkt` starts from: the last capture before the close, averaged over venues |
| `K`, `PM bid/ask` | The non-Republican contract on Kalshi and Polymarket, latest pass |
| `best buy` | The best taker buy across both venues and both sides, with its expected value per $1 contract after fees, and which projector it used (v1 where available). Before the count starts it should sit at about minus the spread. `FLIP`: v1 gives the side 45%+ while the market prices it far lower, with 20%+ counted |

Example: `KS-Sen 40.0% +12.0 | -2.2 7.1 0.35 ...` means that with 40% counted and Hamilton up 12, Kansas's
history projects Marshall by 2.2. That is the early Democratic lead fading.

Maine and Alaska are first-round margins. Ranked-choice tabulation can still change the winner there, and
both settle days or weeks later.

## Election-night checklist

1. Before Nov 3: `ElectionSim-MarketsCheck` runs daily; check `data/raw/markets/capture.log` for 35 Kalshi and
   34 Polymarket markets. `StateResults-SlugCheck` confirms NYT's file names.
2. Nov 3 from noon ET: markets record. From 6:30 pm ET: NYT records (`StateResults-ElectionNight`).
3. From 7 pm ET: `live_project.py --watch 60`. Look at rows marked `FLIP`: v1 gives a side ~50% that the market
   prices far lower, with 20%+ counted. That is the only kind of edge that paid in the 2024 test (Michigan and
   Nevada Senate). Other best buys are v1 rating a longshot higher than the market; those lost in 2024. Treat
   any best buy as a prompt to look, not a trade. That goes double for rows with `?`. The 2024 misses
   were overnight, in wide books, in close races with a known Democratic batch still out (MARKET_CHECK.md):
   check which counties are left before acting. Check depth before sizing: the `bids`/`asks` columns in the
   market CSVs.
   Polymarket counted Maine's King and Vermont's Sanders as Democrats in 2024. Its 2026 Nebraska rules
   exclude independents from the party options, so an Osborn win pays the independent contract (checked
   2026-10-28). Re-read the rules for any other independent.
4. Afterwards: everything is in `data/raw/` (markets, projections) and `../State election results/data/raw/live/`
   (NYT), for the post-mortem.

Not financial advice; see METHODS.md for where the projector is weak.
