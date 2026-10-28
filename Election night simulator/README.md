# Election night simulator

Goal: on Nov 3, 2026, catch Kalshi and Polymarket prices that misread the vote count. As each state
reports, the projector estimates where the count will finish from what is still uncounted, turns that into
a win probability, and sets it against the live order books after fees.

It covers the 15 competitive Governor and Senate races from `../State election results/competitive_races.md`,
plus Senate and House control (prices only).

That folder has the research (how each state counts, past swings, county benchmarks) and records NYT's
results. This folder records the markets, projects the count and compares the two. **Method and backtest:
[METHODS.md](METHODS.md).**

Started 2026-10-28.

## Status

| Piece | State |
|---|---|
| Market price capture (`capture_markets.py`) | **Built**, tested on live APIs. The scheduled tasks need registering once by hand (below) |
| Projector v0, statewide (`live_project.py`) | **Built**, backtested. Trust it in KS, IA, TX, OH, NE, MI, ME; not in GA, OR, NV, AK, SC (`?` flag) |
| Historical check: did markets misread past counts? (2024 price histories vs NYT timelines) | Next |
| Projector v1: county x vote type, from NYT's live county files | To build; needed for Nevada, Georgia and the other `?` states |
| Pre-election Monte Carlo: thousands of simulated nights, a threshold sheet per state | To build, on v1 |
| Election-night console page with alerts | To build |

## Layout

| Path | What |
|---|---|
| `METHODS.md` | How the projector works, the backtest, what it can't do, the v1 plan |
| `scripts/capture_markets.py` | Records Kalshi and Polymarket books every 20 s -> `data/raw/markets/{ET date}/{kalshi,polymarket}.csv` |
| `scripts/live_project.py` | The projector: live table, what-ifs, backtest |
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
| `proj`, `+/-80%` | Projected final margin and the half-width of its 80% band. A `?` before it means past years' late votes leaned opposite ways at this point in the count, so the direction is a guess |
| `P mkt` | Starts from the markets' own price at the state's poll close and adds only what the count says. **This isolates count-reading edges** and is what `best buy` uses by default |
| `P mod` | Starts from our model's win probability instead |
| `close` | The market price at poll close that `P mkt` starts from: the last capture before the close, averaged over venues |
| `K`, `PM bid/ask` | The non-Republican contract on Kalshi and Polymarket, latest pass |
| `best buy` | The best taker buy across both venues and both sides, with its expected value per $1 contract after fees. Before the count starts it should sit at about minus the spread |

Example: `KS-Sen 40.0% +12.0 | -2.2 7.1 0.35 ...` means that with 40% counted and Hamilton up 12, Kansas's
history projects Marshall by 2.2. That is the early Democratic lead fading.

Maine and Alaska are first-round margins. Ranked-choice tabulation can still change the winner there, and
both settle days or weeks later.

## Election-night checklist

1. Before Nov 3: `ElectionSim-MarketsCheck` runs daily; check `data/raw/markets/capture.log` for 35 Kalshi and
   34 Polymarket markets. `StateResults-SlugCheck` confirms NYT's file names.
2. Nov 3 from noon ET: markets record. From 6:30 pm ET: NYT records (`StateResults-ElectionNight`).
3. From 7 pm ET: `live_project.py --watch 60`. Act only on rows without `?` and with a best buy clearly above
   zero. Check depth before sizing: the `bids`/`asks` columns in the market CSVs.
4. Afterwards: everything is in `data/raw/` (markets, projections) and `../State election results/data/raw/live/`
   (NYT), for the post-mortem.

Not financial advice; see METHODS.md for where the projector is weak.
