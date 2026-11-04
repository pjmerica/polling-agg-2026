# Election night simulator

Goal: on Nov 3, 2026, catch Kalshi and Polymarket prices that misread the vote count. As each state
reports, the projector estimates where the count will finish from what is still uncounted, turns that into
a win probability, and sets it against the live order books after fees.

It covers 14 competitive Governor and Senate races from `../State election results/competitive_races.md`,
plus Senate and House control (prices only). Oregon Governor was dropped from live tracking on 2026-10-30;
the market recorder still saves its prices.

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
| **Election-night dashboard** (`dashboard.html`, `scripts/run_dashboard.cmd`) | **Built 2026-10-30**, dry-run on 2024's count (`dry_run.py`). Every race live: projection, whether the votes are coming in over or under our model (statewide and county by county), the markets, best buy, FLIP alerts, history through the night |
| Pre-election Monte Carlo: thousands of simulated nights, a threshold sheet per state | To build, on v1 |

## Layout

| Path | What |
|---|---|
| `METHODS.md` | How the projector works, the backtest, what it can't do, the v1 plan |
| `scripts/capture_markets.py` | Records Kalshi and Polymarket books every 20 s -> `data/raw/markets/{ET date}/{kalshi,polymarket}.csv` |
| `dashboard.html` | The election-night dashboard (Races and Map tabs). Open it from this folder; it reads `data/raw/dashboard/live_data.js` every 15 s |
| `county_geo.js`, `scripts/build_county_geo.py` | The map tab's county shapes (us-atlas, same projection as the site's map page). Built once, committed |
| `scripts/run_dashboard.cmd` | Election night in one click: the projector every 30 s, the home server and the public copy |
| `scripts/serve_home.py` | Serves the live dashboard to phones on the home Wi-Fi (port 8765) |
| `scripts/publish_live.py` | Pushes a delayed public copy to `docs/election-night-live.html` every 10 min |
| `scripts/cloud_night.py` | Election night in GitHub Actions: both recorders and the projector every 2 min, state on the `election-live` branch (`.github/workflows/election-night.yml`) |
| `scripts/build_cloud_pages.py` | Writes the Pages copies that read the cloud run: `docs/election-night-cloud.html` (dashboard) and `docs/election-night-desk.html` (data desk) |
| `scripts/dry_run.py` | Replays 2024's archived count through the projector and dashboard (`data/raw/dryrun/`), to check everything before Tuesday |
| `data_dashboard.html` | The data desk: the same projector data, count-first (votes left, what the trailing side needs, desk math, outstanding counties); buy signals optional |
| `scripts/replay_2024.py` | Election night 2024 with real data and real prices for the data desk (`data/raw/replay/`; open `data_dashboard.html#replay`) |
| `scripts/live_project.py` | The live table (v1 where the counties line up, v0 beside it), the dashboard's data file, what-ifs, v0 backtest |
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

## The dashboard

Double-click `scripts\run_dashboard.cmd`. It opens three windows; leave them all open overnight:
- **The projector** (`live_project.py --watch 30`), which writes the data, and opens `dashboard.html` on this PC.
- **The home server** (`serve_home.py`): the same live page for a phone on the home Wi-Fi. The window prints the
  address (`http://<this PC>:8765/dashboard.html`). It serves only the page and its data file. The first time,
  allow Python through Windows Firewall on private networks.
- **The public copy** (`publish_live.py`): every 10 minutes, a delayed copy goes to
  **https://pjmerica.github.io/polling-agg-2026/election-night-live.html**, to share. It has no best buys or
  FLIPs, since a 10-minute-old trade prompt would mislead. It commits through GitHub's API (`gh`), so this
  checkout is never touched. Pages allows about 10 rebuilds an hour, so keep it at 10 minutes. Before the first
  poll close it shows the model's starting point and says when it goes live.

The local and home pages are the fast ones: the data changes every 20 s to 2 min, faster than Pages rebuilds.

- **Header:** how long ago the projector, the markets and NYT last wrote (amber, then red when stale), and the
  Senate and House control prices.
- **Alerts:** FLIPs (one row each), and races where the counted votes run 3+ points off our model.
- **A card per race**, in poll-closing order:
  - the margin on a scale: on screen, projected final with its 80% band, counted votes alone, our model, the
    market at the close;
  - **over/under:** "Turek running 2.6 pts under our model, -2,156 net votes vs expected so far";
  - win chances: projector, model start, market; both books; the best buy; a sparkline of the night.
- **Map tab** (or `dashboard.html#map`): the US with every tracked state's counties shaded by over/under vs our
  model, the Democrat's counted share, what the model expects, or share counted. It has a Senate / Governor
  switch and labels each state with the projector's win chance. Click a state to zoom into its counties: hover
  for a county's numbers, and the side panel shows the race and its biggest misses. Escape zooms back out.
  Alaska stays a plain state (results by House district).
- **Click a card** (or open `dashboard.html#MI-Sen`) for the race's charts and its county table:
  - win chance and margin through the night;
  - every county's counted share against the share expected if the state lands on our model's margin, the
    share a tie needs, over/under in points and in net votes, and votes left. Sortable, searchable.
- **"Counted votes alone"** is v1's shift from the counted counties only, with no starting point, turned into
  a statewide margin. Comparing it with our model's margin is the over/under. The projected final also uses the
  market's starting point and the uncounted votes.

Alaska reports by House district, so it has no county tracking. Maine reports by town; the projector adds
the towns up into counties (before 2026-10-30 each town overwrote the last).

**Dry run:** `py "Election night simulator/scripts/dry_run.py"` replays the Internet Archive's 2024
presidential count in the 12 states, in time order, with today's market books. Add `--until 2024-11-06T05:30` to
stop mid-count, and `--pause 0` to go fast. The prices don't move and 2024 isn't 2026, so its FLIPs and big
over/unders are meaningless: it checks the plumbing. Run the real projector once afterwards (or just start
`run_dashboard.cmd`) to replace the dry-run data.

## In the cloud (GitHub Actions + Pages, 2026-11-02)

The same night without this PC, readable from anywhere:
- **https://pjmerica.github.io/polling-agg-2026/election-night-cloud.html** (the dashboard: races, map, best buys, FLIPs)
- **https://pjmerica.github.io/polling-agg-2026/election-night-desk.html** (the data desk, 3D map)

How it runs:
- The workflow **Election night (cloud)** (`.github/workflows/election-night.yml`) runs `scripts/cloud_night.py`. Every
  pass it records NYT's county results (`capture_live.poll`), the Kalshi/Polymarket best bid/ask (`capture_markets`)
  and runs the projector (`live_project.run_live`, starting from our margin model since 2026-11-03, user call; the
  market start is computed beside it and shown on the cards). Every 2 minutes, every 5 from Wed Nov 4 1 pm ET;
  it stops after Dec 14 (`END`; was Sat Nov 7, extended 2026-11-04 for the late count).
- **State** lives on the orphan branch `election-live`: `live_data.js`, `status.json` (last pass, which NYT file per
  race, errors), `projections.csv` (the charts' history), `markets/{ET date}/` (bid/ask only) and the newest NYT file
  per race. One commit, amended and force-pushed each pass, so the branch has no history. Older NYT files go into
  each job's artifact `nyt-captures-<run id>` (30 days).
- **Continuity:** GitHub stops a job at 6 hours. Each job runs ~5h40m, then dispatches the next, which waits in the
  `election-night` concurrency group. A job that dies within 20 minutes doesn't dispatch itself; the cron (every
  30 min, through Dec 14 UTC) restarts it. Started by hand 2026-11-02 evening. Nothing inside a pass can
  end a job (every pass is wrapped; a failure is logged and the next pass runs, 2026-11-03).
- **The pages** are `dashboard.html` / `data_dashboard.html` unchanged, plus a loader (`build_cloud_pages.py`) that
  fetches `live_data.js` from `raw.githubusercontent.com/.../election-live/` with a fresh query string (that skips
  raw's 5-minute cache: a pass was served 18 s after its push), GitHub's API if raw fails. No Pages rebuilds per
  update. Re-run `build_cloud_pages.py` after editing either page.
- **They are public** and show best buys and FLIPs (the 10-minute-delayed `election-night-live.html` doesn't).
- **Differences from the PC:** fee multipliers default to 1 (the market CSVs aren't in CI); the market record is
  bid/ask only; the PC's recorders keep running and keep the full record.
- **Check it:** the Actions tab, or `status.json` on the branch. Stop it: disable the workflow
  (`gh workflow disable election-night.yml`) and cancel the running job.
- **A fix mid-night** (a wrong NYT address in `capture_live.RACES`, a parser change): a job reads the code once, when it
  starts. Push the fix to master, then `gh run cancel <running id>` and `gh workflow run election-night.yml`; about a
  minute without updates. A race whose file doesn't parse shows 0% and is listed under `errors` in `status.json`; the
  other races keep updating (live_project `_safe`, 7fa94503).
- **A wrong NYT file name needs no fix any more** (2026-11-03): a race that no guessed name finds is read from NYT's
  page for its whole state (`results-{state}.json`, matched by office, the regular election before a special;
  identical to the race file on 2024 Pennsylvania Senate). `status.json` shows "state page results-...json" for it.
  NYT requests run in parallel with a 30 s timeout, so one slow file holds up no other race.
- **Markets:** a race whose Kalshi or Polymarket lookup fails at a re-discovery (every 30 min) keeps the markets it had;
  Kalshi markets that are paused or closed but not settled are kept too (only "active" before 2026-11-03).
- **Hand-offs** come every ~5h45m and cost about a minute of updates each. None between 6:20 and 11:50 pm ET on Nov 3
  (`NO_HANDOFF`): a job that would end inside it ends at ~6:15 pm and the next covers the window. Expected after the
  restart at 12:20 am ET Nov 3 (run 41583297519, on b0200f71): ~6 am, ~11:45 am, ~5:25 pm, ~6:15 pm (a short job),
  ~11:57 pm, ~5:40 am ET.
- **The record, for a 2026 replay** (user: "save the results as they come in for future races as much as possible ...
  save states of the model"): each job's `archive/` holds every change of the tracked races' NYT files, NYT's 50 state
  pages every 10 minutes when they change (every Senate and Governor race by county, every House and legislative race
  statewide; checked on 2024 Texas: 222 races, 254 counties), the full books (5 levels a side, every pass and every 20 s
  between passes since 2026-11-03, `markets_full/{date}/{venue}-{run}.csv`), the projector's inputs (forecast,
  benchmarks, early vote, state timelines, code version) and its output every 10 minutes. Every hour it is packed with a
  copy of the state folder into `night-<run>-<n>.tar.gz` and attached to the release **election-night-2026** (permanent;
  uploaded in the background, so passes don't wait). The job artifact (90 days) is the backup, kept only when a
  release upload failed (`upload_failed` in the workspace) or the job didn't finish cleanly: the next job can't start
  until this one ends, so an artifact upload would lengthen every hand-off. To rebuild the night:
  `gh release download election-night-2026` and unpack every file into one folder, oldest first (a book file grows
  through the job and is re-sent whole each hour, so the later copy holds the earlier). Before 2026-11-03 6:15 pm ET
  the books were `{venue}.csv` and sent only in each job's first hourly upload: those keep one hour per job, and unpack
  them per file, since every job used the same name.

## The data desk (`data_dashboard.html`, 2026-11-02)

A second page on the same projector data, built around the count rather than the markets. Open it next to (or
instead of) `dashboard.html` once `run_dashboard.cmd` is running; it reloads every 10 s. Phones on the home
Wi-Fi: `http://<this PC>:8765/data_dashboard.html` (`serve_home.py` prints it).

- **Each card:** on-screen margin, projected final with its 80% band (county by county or statewide), win
  chance and what it started from (the market at poll close, or our model when no prices were captured),
  votes counted, **votes left** (NYT's expected vote), **what the trailing candidate needs** of the two-party vote
  still out, counties reporting, **desk math** (the final margin if every county's remaining votes split like
  its counted votes, the expected share where it has counted under 5%) and over/under vs our model.
- **Alerts:** "Lead change" (projected leader differs from the on-screen leader, 60%+, 10-99% counted),
  "Off expected" (counted counties point 3+ points away from the expectation), FLIPs when signals are on.
- **Click a card:** margin and win-chance charts through the night, desk math, and every county sorted by votes
  left (counted share, expected, tie line, over/under, net vs expected, net from the votes still out).
- **Buy signals** are off by default live (one button turns them on). Signals at 98%+ counted carry a warning:
  the county projector keeps 5-20% for the trailing side of a finished close race (its turnout error applies to
  the whole expected vote; the 2024 test's Casey-at-98% loss), so those are not edges.

**2024 replay** (`scripts/replay_2024.py`, then open `data_dashboard.html#replay`): election night 2024 on a
moving clock, 5 minutes a step to 5 am ET, then 30 minutes to the following Monday, with real data at every step:
- 12 races (the Senate race where the state had one, else President): NYT's statewide count timeline,
  the archive's county captures (v1 runs only while one is within 3 points of the final vote of the count;
  otherwise v0), county leans and v0 history from other years only;
- Kalshi's minute bid/ask and Polymarket's minute price, the starting point at poll close, and the live
  best-buy and FLIP rules. It flags the real cases: Slotkin at 20-21c at 1:20 am (won), Rosen at 31c Wednesday
  afternoon (won), then Brown for hours (lost). Most other signals are the longshot kind that lost in 2024;
- "Show results" reveals each race's real result. It writes `data/raw/replay/live_data.js` only, never the live
  file. `--pause` (default 2 s), `--step`, `--until 2024-11-06T06:25` (1:25 am ET).

**On GitHub Pages, with a time slider:** https://pjmerica.github.io/polling-agg-2026/election-night-replay.html.
`replay_2024.py --publish` computes the whole night at once (about 3 minutes) and writes
`docs/election_night_replay_2024.js` (every step; county tables stored once per capture; ~2.9 MB) and
`docs/election-night-replay.html` (a copy of `data_dashboard.html` that loads it). Drag the bar, press Play
(1 / 2.5 / 7 steps a second), jump to key moments (polls close, the Michigan and Nevada flips), or step with
the arrow keys (Shift: an hour overnight). `#step70` in the address opens a given step. Locally,
`data_dashboard.html#replay` plays the same file. Re-run `--publish` after changing `data_dashboard.html`.

**3D map** (the "3D map" button, live and replay): every tracked state's counties drawn flat (shaded by the
counted Democratic share, or by share counted) with a column on each county: **net votes vs expected** (default),
**points over/under**, or **votes still out**. Blue columns: the Democratic side running ahead of the expected
margin there; red: behind. "All states" or one state at a time (the camera flies there); drag to rotate,
right-drag or Ctrl to tilt, scroll to zoom, hover a column for the county, click it for the race's detail
below. The side panel lists each race's implied margin vs the expectation. Live, the expectation is our model
and the columns follow the projector's county data; in the replay, each state shows its latest archived capture
(time on the right). It draws with deck.gl 8.9.35 from jsdelivr (needs the internet) and `county_geo.js`
(Oregon and Alaska have no county shapes).

### How it works tab (2026-11-02)

The data desk's last tab (user: "write an explainer ... of what this is and how everything is wired"): what the page is,
a wiring diagram (NYT files and state pages, Kalshi/Polymarket -> the cloud run and projector -> the `election-live`
branch and the `election-night-2026` release -> the pages; the PC backup), timing (lag, hand-offs, cadence, the pills),
each tab, the Kalshi board's columns and warnings, the projector in brief, a definition of every number on the cards,
and what to do when something looks wrong. Static HTML in `data_dashboard.html`, so it is in the local page, the cloud
desk and the replay; a line at the top says which copy you are looking at. Update it when the wiring changes.

### Kalshi board (2026-11-02)

On the data desk, under the alerts, whenever "Buy signals" is on (the cloud desk starts with it on): every race and side
where a Kalshi price is 3c+ off our projection after Kalshi's fee (0.07 x p x (1 - p)). Per row: buy which YES, the ask,
our chance, the edge, **pay up to** (the highest ask that still leaves a 3c edge after the fee: a limit price), **held**
(updates in a row the edge has been 5c+, and for how long: an edge that lasts one update is usually NYT catching up with a
market that already saw the votes), and warnings (prices 5+ min old, under 20% or 98%+ counted, statewide projector only,
not a FLIP). FLIP rows first. Cards show both Kalshi sides; the win chart has a Kalshi line beside the two-venue market.
With the board showing, FLIP alerts aren't repeated above it; off-expected alerts are one grouped line. The projector now
sends both sides of each book (`r_bid`/`r_ask`) and Kalshi's bid/ask in the history; the replay mirrors the D book.
Checked on the 2024 replay: at 1:20 am it lists FLIP Slotkin YES 20c, ours 55%, +34c, pay up to 50c.

### Over/under map (2026-11-02)

The data desk's flat map tab (user: "colored blue or red if the votes come in not as expected ... more of a static map as
another tab next to cards and 3d map"): every tracked state's counties, blue where the Democrat (Osborn in Nebraska) is
running ahead of the share expected there if the state lands on our model's margin, red where the Republican is, full
colour at 10 points; grey until a county reports; faded while it is under 95% counted (a part-counted county is mostly
one kind of vote), or "Finished counties only". Click a state to zoom; hover a county for its numbers; the side panel has
each race's net votes against expectation. In the 2024 replay "expected" is the market's margin at poll close.

### Splits & turnout view (2026-11-02)

The data desk's third view (user: "some kind of monitor on split ticket voting, and turnout. Especially for georgia/texas").
- **Ticket-splitting** where a state has a Senate and a Governor race (Georgia, Ohio, Kansas, Texas): in a county counted
  in both races the same ballots carry both, so the gap between the two Democrats' two-party shares is the splitting
  there, whatever kind of votes are in. Shown against the gap our model's two margins imply in the same counties,
  statewide, by county type (the share the Democrat needs there for a tied state) and for the counties with the biggest
  effect. GA Senate is tracked for this only (Ossoff is safe): `State election results/scripts/benchmarks_extra.py`
  writes its benchmark to `county_benchmarks_extra.json`, which the guide builders don't read. Checked on 2022 Georgia
  (Warnock vs Abrams): the view gives Warnock +8.5 pts ahead, the real gap.
- **Turnout against 2022:** 2022 total, ballots cast before Election Day (`early_vote_2026.csv`, UF Election Lab; refresh
  with `early_vote.py`), NYT's expected vote, counted so far; finished counties (95%+) against their 2022 vote by county
  type; "turnout mix" = how far this year's turnout pattern alone moves the margin from 2022's (each county's lean held
  at its tie-line value), for finished counties and for NYT's expected vote.
- The projector adds `v22` (2022 votes) and `nexp` (NYT's expected vote) to each county and a `turnout` block to each race.
  The 2024 replay page was not re-published: it has one race per state and no 2022 bases in its bundle.

## Running the projector

```
py "Election night simulator/scripts/live_project.py"                    # once: every race, latest captures
py "Election night simulator/scripts/live_project.py" --watch 60         # every 60 s
py "Election night simulator/scripts/live_project.py" --race KS-Sen --pct 40 --margin 12    # what-if
py "Election night simulator/scripts/live_project.py" --baseline market  # start from the market at poll close instead
py "Election night simulator/scripts/live_project.py" --backtest         # leave-one-year-out check
```

`--date` (default `2026-11-03`) picks which day's captures to read.

Reading the table (margins are non-Republican minus Republican, in points of all votes; P is the chance the
non-Republican wins):

| Column | Meaning |
|---|---|
| `counted`, `margin` | NYT's share of the expected vote counted (`eevp`) and the visible margin |
| `v1 proj`, `+/-80%`, `P v1` | Projector v1 (county by county): projected final margin, the half-width of its 80% band, and P(win). It starts from our margin model by default since 2026-11-03 (`--baseline market` for the markets' price at poll close, which makes its edge come from the count alone). Blank where the live counties don't line up with the benchmarks (Alaska's districts); then v0 is used |
| `P v0` | The statewide projector from the same starting point. A `?` before the row means v0 is in use and past years' late votes leaned opposite ways at this point in the count, so the direction is a guess |
| `P mod` | The same projection started from **our margin model** instead of the market (v1 where it runs, else v0): the model's projected margin from `docs/forecast_data.js`, give or take 6.1 points (its held-out 2018-24 miss). Before the count it is the margin model's own chance, which can differ from the win chance on the forecast page (a separate model): GA-Gov is +1.2 points but 78% |
| `close` | The market price at poll close that `P mkt` starts from: the last capture before the close, averaged over venues |
| `K`, `PM bid/ask` | The non-Republican contract on Kalshi and Polymarket, latest pass |
| `best buy` | The best taker buy across both venues and both sides, with its expected value per $1 contract after fees, and which projector it used (v1 where available). Before the count starts it should sit at about minus the spread. `FLIP`: v1 gives the side 45%+, it sells for 40c or less, the edge after fees is 5c+, and 20%+ is counted |

Example: `KS-Sen 40.0% +12.0 | -2.2 7.1 0.35 ...` means that with 40% counted and Hamilton up 12, Kansas's
history projects Marshall by 2.2. That is the early Democratic lead fading.

Maine and Alaska are first-round margins. Ranked-choice tabulation can still change the winner there, and
both settle days or weeks later. Our model's margin there is the final-round head-to-head, so `P mod` mixes
the two.

**Market or model as the starting point.** The default is `model` since 2026-11-03 (user call: "I want to use my
model for the margin and win % chances"); the market start is computed beside it (`mkt`, `p_mstart`, `mkt_proj` in
the data; "Market start" on the cards). `--baseline market` makes the best-buy edge come from the count alone. The
model start adds the model's disagreement with the market, which is untested: there are no
archived 2022/2024 forecasts. A stand-in with the model's error size helps most under 50% counted and barely
matters after (METHODS.md). When `P mod` and `P v1` agree and both differ from the market, the count and the
model point the same way.

## Election-night checklist

1. Before Nov 3: `ElectionSim-MarketsCheck` runs daily; check `data/raw/markets/capture.log` for 35 Kalshi and
   34 Polymarket markets. `StateResults-SlugCheck` confirms NYT's file names.
2. Nov 3 from noon ET: markets record. From 6:30 pm ET: NYT records (`StateResults-ElectionNight`).
3. Before 7 pm ET: start `scripts\run_dashboard.cmd` and leave its window open. Watch the dashboard's header:
   all three feeds should stay under a few minutes old. Look at rows marked `FLIP`: v1 gives a side ~50% that the market
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
