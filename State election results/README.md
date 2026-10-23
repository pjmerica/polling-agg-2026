# State election results

Goal: simulate how election night unfolds in the competitive 2026 Governor/Senate races
(`competitive_races.md`): which counties report when, with what kind of ballots, so that
early returns can be read correctly ("Talarico +6 at 8:15 ET with Harris early vote in"
means X) and projected to a final result.

## Layout

| Path | What |
|---|---|
| `MASTER.md` | **Start here.** The one file to read: states at a glance, betting assessment, ballots already cast, then per state the rules, history, swing data and county benchmarks (built by `scripts/build_master.py`, which also rebuilds STATE_BY_STATE.md) |
| `../docs/election-night.html` | The same guide as a dashboard page ([live](https://pjmerica.github.io/polling-agg-2026/election-night.html)): model and market numbers refresh from `docs/forecast_data.js` on load, and every county table has a statewide-result slider and a box that turns a finished county's result into an implied statewide margin (built by `scripts/build_election_night.py`; data in `docs/election_night_counties.js`) |
| `STATE_BY_STATE.md` | State-by-state guide to how and when votes come in, checked against primary sources (built by `scripts/build_state_guide.py` from `scripts/state_guide_template.md`) |
| `VOLATILITY.md` | Which states' counts swing the most, nationally: every President/Senate/Governor race in all 50 states and DC, 2020-2024, ranked by swing size and by how often the leader during the count lost (built by `scripts/volatility.py` from `fetch_nyt_history.py --all`) |
| `SWINGS.md` | How far the count moved after polls close in every race NYT covered in the eleven states, 2020-2026: biggest swings, comebacks, late movers, early vs Election Day splits, 2020 county detail, 2026 primaries (built by `scripts/swing_analysis.py` + `scripts/build_swings_report.py`) |
| `competitive_races.md` | The races (model favorite at 75% or less), built from `docs/forecast_data.js` by `scripts/build_competitive.py`: 13 races in 11 states as of Oct 22 |
| `reports/Vote count timing in close 2026 races.md` | Rules and history per state (the first nine states): poll closes, ballot order, deadlines, RCV, recounts, past call times |
| `reports/Vote count timing Nevada and Oregon.md` | The same for Nevada and Oregon, added Oct 22 when the model audit put their governor races under 75% |
| `model_audit/MODEL_AUDIT.md` | Audit of the forecast's inputs (Oct 21-22): what was wrong, what was fixed, before/after poll numbers and win chances |
| `research_notes/` | Sourced notes behind the report |
| `scripts/fetch_nyt_history.py` | NYT results JSON for 2020/2022/2024 (11 states; `--all` fetches every state into `data/raw/nyt_all/` for `volatility.py`): final county results (2022/24 split by vote type) and a statewide count timeline |
| `scripts/fetch_wayback_2020.py` | County-by-county count over election week 2020, from Internet Archive captures of NYT's national file (one per 10 min where captured) |
| `scripts/county_benchmarks.py` | County benchmarks: each county's share of the statewide vote (2022) and its expected two-party share at any statewide result (uniform swing on recent results), early/mail vs Election Day where NYT split every county (GA, TX, IA), 2020 reporting speed, and a backtest on every 2022/2024 race -> `data/processed/county_benchmarks.json/.csv`, `county_backtest.csv` |
| `scripts/early_vote.py` | Ballots already cast, from the UF Election Lab tracker -> `data/processed/early_vote_2026.csv` and the guide's section 2c (rerun to refresh) |
| `scripts/census_blocs.py` | Demographic voting blocs from the Census Bureau's ACS 2020-2024 county estimates (via Census Reporter; api.census.gov now needs a key): each county's bloc, how each bloc voted 2020-2024, its 2020->2024 shift against the state's, and what it needs in 2026 -> `data/processed/census_units.csv`, `bloc_results.csv`, `census_blocs.json` |
| `scripts/capture_live.py` | Records NYT's 2026 files every 2 minutes on election night (every county, every change), for all 13 races |
| `scripts/watch_sources.py` | Searches news feeds for AP "What to expect" pieces and county results schedules -> `sources/watch_log.csv` |
| `sources/README.md` | Every source on when/how each state reports (AP 2026 editions, official documents, county schedules) |
| `state_curves.md` | Share counted and visible margin by hour after poll close, per state, 2020-2024 |
| `data/raw/` | Downloads (not committed; includes AP article texts, which are copyright) |

## Scheduled tasks on this PC (Windows Task Scheduler)

| Task | When | What |
|---|---|---|
| `StateResults-SourceWatch` | 8 a.m. and 6 p.m. daily, Oct 22 - Nov 3 | `watch_sources.py` (log: `sources/watch.log`) |
| `StateResults-SlugCheck` | 9 a.m. daily, Oct 28 - Nov 3 | `capture_live.py --once`: confirms NYT's Nov 3 file names (log: `data/raw/live/capture.log`) |
| `StateResults-ElectionNight` | Nov 3 6:30 p.m. ET to Nov 6 noon | `capture_live.py`, every 2 minutes |
| `StateResults-LateCount` | Nov 6 noon to Nov 25 | `capture_live.py`, every 30 minutes (AK count days, ME RCV) |

The PC must be on (tasks are set to wake it from sleep, not from shutdown).
Remove them after the election: `Get-ScheduledTask -TaskName "StateResults-*" | Unregister-ScheduledTask -Confirm:$false`.

## Data we have, and what is missing

| Source | Unit | Timing detail | Vote type |
|---|---|---|---|
| NYT 2020 race files | county (final) | statewide timeline, hundreds of points | absentee vs total per county |
| Wayback 2020 national file | **county, over time** | captures ~10-60 min apart on election night | absentee vs total |
| NYT 2022 race files | county / Maine town (final) | statewide timeline (votes, expected-vote %) | GA: mail / early / Election Day for every county; MI and OH only Wayne and Hamilton; OR all mail |
| NYT 2024 race files | county / Maine town (final) | statewide timeline with "advance" vs total | GA, TX: full split per county; IA, TX pres: advance vs Election Day |
| NYT 2026 primaries | county | statewide timeline | as above; current laws (MI Aug 4 saved) |
| Alaska Division of Elections precinct files, 2022/2024 | precinct -> House district (final) | none | Election Day / absentee / early rows per district (`data/raw/ak_doe/`, downloaded by `county_benchmarks.py`) |
| UF Election Lab early-vote tracker | state (daily) | one file per day in `data/raw/early_vote/` | mail returned, early in person, voters' registered party |
| Census ACS 2020-2024 5-year (Census Reporter API) | county; Alaska House district | none | demographics only: race/ethnicity (B03002), education (B15003), income (B19013), in `data/raw/census/` |

County-level timing for 2022 and 2024 does not survive publicly: state result sites (Clarity etc.)
keep only the latest version, and archive captures of the NYT race files are a handful per race.
2020 is the only year with real county timing; 2022/2024 give the statewide pace and the
early-vs-Election-Day mix. Nov 3, 2026 is recorded by `capture_live.py`.

## Rebuilding

After a model refresh or new early-vote numbers, in this order (from the repo root):

```
py "State election results/scripts/early_vote.py"
py "State election results/scripts/county_benchmarks.py"
py "State election results/scripts/census_blocs.py"
py "State election results/scripts/build_competitive.py"
py "State election results/scripts/build_master.py"
py "State election results/scripts/build_election_night.py"
node tests/dash_smoke.js docs/election-night.html
```

The page's model and market numbers refresh by themselves (they come from `docs/forecast_data.js`,
which CI rewrites); rebuild for new early-vote numbers, text changes or a race crossing 75%.

## Simulator design (to build)

Built so far (Oct 23): step 2 without the errors. `county_benchmarks.py` gives each county's expected
two-party share for any statewide result (uniform swing on the log-odds scale) and, where NYT split
every county by vote type (GA, TX, IA), its early/mail vs Election Day shares. A backtest on every
2022/2024 race puts the typical county miss at 1-5 points. Correlated county errors, release timing
and the Monte Carlo are still to do.

Per state, per county (Maine: town), per vote type (early in person / mail / Election Day / late):

1. **Expected 2026 vote**: 2022/2024 turnout by county and vote type, scaled by 2026
   early-vote returns and the model's turnout.
2. **Expected lean**: county vote-type lean from 2022/2024, shifted so the statewide result
   matches a draw from our forecast (`docs/forecast_data.js` margin and its error), with
   correlated county errors.
3. **Release schedule**: when each county releases each vote type, from the 2020 county
   timing, the 2022/2024/2026 statewide timelines, and each state's rules (GA early vote by
   8 p.m.; IA absentee board batch by 10 p.m. CT; AK absentees Nov 10/13/18; ME RCV; MI Wayne last;
   NV results only after the last voter in line, Election Day drop-offs Wed-Sat; OR Election Day drop-offs Wed-Fri).
4. **Monte Carlo**: thousands of election nights -> at each clock time, the distribution of the
   visible margin, the leader, % counted, and P(current leader wins).
5. **Live mode**: on Nov 3, condition on what has actually reported (from `capture_live.py`)
   and project the remaining vote.
