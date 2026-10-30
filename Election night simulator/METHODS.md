# Methods

How `live_project.py` projects a count, how well that held up on 2020-2024, what it can't do, and the plan for
v1. Numbers are from 2026-10-28 (`--backtest` reproduces them).

## The idea

The visible margin is the margin of the votes counted so far. The final margin also depends on the votes not
yet counted, and in many states those lean the same way every year: mail counted late in Nevada, Wayne County
last in Michigan, Election Day votes after early votes in Kansas. A market that prices off the visible margin,
or that knows the direction but not how far it goes, can be wrong for hours.

## v0: statewide

**Learning from history.** For every 2020, 2022 and 2024 President, Senate and Governor race in the 12 states
(the NYT timelines in `state_timeseries.csv`), at each share counted p (0-1) it computes

    g(p) = (final margin - counted margin at p) / (1 - p)

`g` is how many points more Democratic the uncounted votes were than the counted ones. For example, Michigan
2024 Senate at 46% counted: Rogers +3.2 visible, Slotkin +0.34 final, so g = 3.54 / 0.54 = +6.5. The share
counted is relative to the final total; live, NYT's `eevp` stands in for it.

**Per state.** At the live share counted p, it computes:
- **The mean of g over that state's years.** A year's President and Senate races are averaged first, since
  they count together. 2020 gets half weight because of its pandemic mail.
- **The spread of g:** the state's own year-to-year spread, mixed with the spread across all states (2
  pseudo-years' weight, `POOL_K`), then **doubled** (`SD_SCALE`, calibrated below).
- **A steadiness check:** whether g had the same sign in every year. If not, the output shows `?`.

**Count estimate.**

    final ~ Normal(counted margin + (1 - p) * mean g,  ((1 - p) * sd g)^2 + 0.4^2)

**Starting point**, as a margin:

    6 * Phi^-1(P)

with a 6-point spread (`PRIOR_SD`, roughly a typical statewide forecast miss). P is either:
- the markets' P(non-Republican) at the state's poll close, from mid prices D / (D + R), averaged over venues
  (`P mkt`, the default for edges, so the edge comes only from the count); or
- our margin model's projected margin (`P mod`), give or take 6.1 points: see "Starting from our margin
  model" below. (Until 2026-10-30 this was the win model's probability. The projector forecasts margins, and
  the win chance comes from a separate model that can disagree: GA-Gov +1.2 points but 78% to win.)

**Combined.** The count estimate and the starting point are averaged with weights 1/variance, giving
P(win) = Phi(mean / sd). Early in the count the count estimate is very wide, so the starting point dominates;
late, the count does.

**Edge.** For each venue and each side, it computes P(side) - ask - fee (`utils/fees.py`) per $1 contract and
reports the best. The non-Republican contract is the most traded non-Republican one (Nebraska: Osborn).

## Backtest

Leave-one-year-out: each year's races are projected using only the other years. That means two years of
history instead of the three available live, so it is somewhat pessimistic. The test uses the count alone,
with no starting point, because no 2020-2024 forecasts were archived. 50 races.

**Widening the bands.** Unwidened, the 80% band held only 57% of results. The comparison (all shares counted
from 10% to 90%):

| Bands widened | Results inside the 80% band | Brier | Log loss |
|---|---|---|---|
| x1.0 | 0.57 | 0.143 | 0.605 |
| x1.5 | 0.73 | 0.136 | 0.484 |
| **x2.0 (used)** | **0.82** | **0.134** | 0.446 |
| x2.5 | 0.88 | 0.135 | 0.435 |

Also tried: pulling g toward 0 when a state's years disagree. It lowered the average miss (7.07 -> 6.84 pts)
but raised Brier and log loss at every width, so it is not used.

**By share counted** (x2.0). Columns:
- `miss` is |final - projection| in points.
- `naive` uses the visible margin as the forecast, and "the visible leader wins" for the naive Brier.

| Counted | Races | Miss | Miss, naive | In 80% band | Brier | Brier, naive |
|---|---|---|---|---|---|---|
| 10% | 39 | 13.6 | 17.4 | 0.95 | 0.223 | 0.538 |
| 20% | 41 | 11.7 | 16.6 | 0.85 | 0.216 | 0.537 |
| 30% | 43 | 9.6 | 13.1 | 0.93 | 0.180 | 0.488 |
| 40% | 50 | 8.3 | 10.4 | 0.90 | 0.155 | 0.360 |
| 50% | 50 | 7.8 | 8.5 | 0.86 | 0.148 | 0.300 |
| 60% | 50 | 5.7 | 5.8 | 0.90 | 0.119 | 0.200 |
| 70% | 50 | 4.8 | 4.0 | 0.74 | 0.102 | 0.100 |
| 80% | 50 | 3.3 | 2.9 | 0.62 | 0.068 | 0.140 |
| 90% | 50 | 1.5 | 1.5 | 0.66 | 0.037 | 0.120 |

**By state**, 20-80% counted:

| State | Miss | Miss, naive | In 80% band | Brier | Brier, naive |
|---|---|---|---|---|---|
| Kansas | 3.3 | 13.3 | 0.93 | 0.066 | 0.357 |
| Iowa | 6.0 | 13.9 | 0.86 | 0.102 | 0.571 |
| Texas | 4.1 | 7.6 | 0.94 | 0.072 | 0.286 |
| Michigan | 6.1 | 9.2 | 0.79 | 0.348 | 0.714 |
| Nebraska | 5.6 | 8.5 | 0.85 | 0.028 | 0.154 |
| Ohio | 7.1 | 9.1 | 0.82 | 0.166 | 0.393 |
| Maine | 3.5 | 3.6 | 1.00 | 0.030 | 0.036 |
| Nevada | 8.0 | 6.8 | 0.82 | 0.326 | 0.536 |
| South Carolina | 5.5 | 3.0 | 0.86 | 0.022 | 0.000 |
| Alaska | 11.0 | 7.8 | 0.50 | 0.006 | 0.000 |
| Oregon | 13.2 | 9.8 | 0.79 | 0.134 | 0.000 |
| Georgia | 13.8 | 8.9 | 0.67 | 0.302 | 0.333 |

**Reading it:**
- **Where v0 works:** Kansas, Iowa, Texas, Michigan, Nebraska and Ohio. These are the states where the count
  moves the same way every year, and there v0 roughly halves the miss.
- **Where it doesn't:** Georgia, Oregon, Alaska, South Carolina and Nevada (on the margin) are worse than the
  visible margin. Their late direction flipped between years, so a statewide average of g points the wrong
  way about half the time. Projections there carry the `?` flag when the years disagree at that share counted.
- **Nevada's two scores disagree:** it misses by more than naive but has the better Brier score. It is the
  top target in MASTER.md and needs v1.
- **Late in the count (70-90%) v0 adds nothing** and its bands are too narrow (62-74% inside). Late batches
  are lumpy: one county's mail and provisional ballots. Below 20%, the starting point dominates anyway, so the
  real window for v0 is about 20-65% counted.

## What v0 ignores

- **Which counties are out.** At 50% counted in Michigan, missing Wayne and missing the Grand Rapids suburbs
  are very different nights. This is the biggest gap.
- **Ballot type.** It can't tell an early-vote batch from an Election Day batch, and 2026's early vote may
  lean more Democratic than 2022/2024's (`../State election results/data/processed/early_vote_2026.csv` has
  the registered-party mix).
- **Time of night.** The same share counted at 8:30 pm and at 2 am means different ballots.
- **NYT's `eevp` misses.** If NYT's estimate of the total vote is off, so is p.
- **Ranked-choice.** Maine and Alaska use first-round margins.
- **Settlement rules.** Kalshi resolves on who is inaugurated (Kansas Governor: `GOVPARTYKS-27`); Polymarket on
  who wins.

## v1: county by county (built 2026-10-29, `county_project.py`)

v0 sees one number per state. v1 sees every county: how many votes it still has to count (NYT's
`total_expected_vote` minus votes counted) and how its counted votes compare with its benchmark.

1. **Leans.** Each county's lean L_c is its log-odds share at a tied statewide result. Live, these come from
   `county_benchmarks.json` (recent races averaged, uniform swing); in the replay, from the 2024
   presidential result by county.
2. **Statewide shift.** Each county with counted votes implies a statewide shift x_c = logit(counted share) -
   L_c. These are averaged with weight = votes counted x (share counted)^6. A half-counted county is mostly
   one kind of ballot: 2020 Wayne counted Election Day first and absentees last.
3. **Starting point.** The market's price at poll close, or our margin model, is a prior on the shift
   (below).
4. **Projection.** Each county's uncounted votes are projected at expit(L_c + shift + k_c x e_c), where e_c
   is the county's own deviation, trusted more as it counts more.
5. **Simulation.** 4,000 runs, with:
   - the shift's uncertainty (x3, since counties report in a non-random order);
   - county errors;
   - one error shared by all uncounted votes (late ballots as a class differ from their counties'
     benchmarks together);
   - turnout errors on NYT's expected vote.

   The output is the projected final margin and P(the non-Republican wins).

**2020 replay** (`county_replay.py`): every Internet Archive snapshot of NYT's national file, 10 states
(Alaska's districts and Maine's towns don't line up with county leans), 345 state-snapshots. Count only,
no starting point:

| Counted | Miss v1 | Miss, visible | Inside 80% band | Brier v1 | Brier, visible |
|---|---|---|---|---|---|
| 5-20% | 13.8 | 19.7 | 0.63 | 0.460 | 1.000 |
| 20-40% | 6.6 | 16.9 | 0.83 | 0.222 | 0.625 |
| 40-60% | 4.8 | 11.9 | 0.85 | 0.205 | 0.500 |
| 60-80% | 2.7 | 6.3 | 0.78 | 0.135 | 0.393 |
| 80-99% | 0.9 | 1.2 | 0.86 | 0.044 | 0.119 |

**Against v0 on the same snapshots** (20-90% counted, the 12 states with v0 history, 2020 left out of
v0's): average miss **v1 3.6**, v0 5.8, visible 7.9; Brier **v1 0.162**, v0 0.217, visible 0.409.

Examples:
- **Texas 2020 at 22% counted:** the screen showed Biden +15.5; v1 said Trump +5.7 (final Trump +5.6).
- **Georgia at 49%:** the screen showed Trump +14.7; v1 said Biden +0.9 (final Biden +0.2).
- **Michigan and Ohio are still v1's worst** (average misses of 9 and 8 points):
  - Michigan's absentees came last inside each big county.
  - Ohio's expected vote was set too high, so v1 projected Democratic votes that never came.

**Caveats:**
- **The settings were tuned on this same 2020 data,** so these numbers are in-sample.
- **County leans from 2024 are a different year,** much as 2026 will use 2022/2024 benchmarks.

**Leave-one-state-out on 2020.** Settings chosen on 9 states, scored on the 10th:
- held-out average miss **3.4** vs 7.2 for the visible margin;
- Brier **0.137** vs 0.335.

The tuning didn't manufacture the result.

**2022, out of sample** (`county_replay.py --year 2022`; whole Internet Archive captures from
`fetch_wayback_full.py`; county leans from the 2020 and 2024 presidential results only):
- **Coverage:** 17 Senate and Governor races in 10 states, 104 snapshots (complete download). The archive
  kept 2022 mostly at poll close and after midnight, so the test is mostly the late count.
- **20-90% counted:** average miss **v1 1.1**, v0 4.1, visible 1.9. Brier **v1 0.096**, v0 0.166,
  visible 0.159.
- **Nevada 2022 (both races decided in the late count):**
  - Senate: v1 had Cortez Masto at 29-34% through Thursday and 81% by Sunday (she won by 0.8).
  - Governor: v1 had Lombardo at 81-94% from Wednesday morning (he won by 1.5).

**2024 against the markets** (`county_replay.py --markets`; v1 started from the market at poll close,
as the live tool runs):
- **Coverage:** 67 snapshots in 21 races (complete download). The archive kept 2-12 per state.
- **Brier:** v1 0.050, market **0.035**. **The market reads the count better than v1 on average.**
- **Trading v1's 5c+ edges on Kalshi:** 29 trades, -$1.41 in total. They split:
  - **"Flips" with 20%+ counted** (v1 gives the side it buys 45%+ while the market prices it far lower):
    3 trades, **+$1.21**.
    - Michigan Senate, Wed 1:15 am ET, 62% counted: Slotkin at 15c, v1 55%. **+84c.**
    - Nevada Senate, Wed 3:50 pm, 85%: Rosen at 33c, v1 48%. **+66c.**
    - Nevada Senate, Wed 7:00 pm: v1 swung to Brown at 27c. **-28c.**
    - A flip at 6% counted (Georgia President) lost 26c; hence the 20% floor.
  - **Every other edge:** v1 merely rated a longshot higher than the market. 26 trades, **-$2.62**, mostly
    Arizona Senate (v1 said buy Lake), Pennsylvania Senate at 98% (v1 gave Casey 19%), and the presidential
    races where v1's early read was noisier than the market's.

**The shared late-ballot error is set to 0.3**, not 0.45:
- 2020 alone preferred 0.45, because its pandemic mail swung the late counts hard.
- At 0.45, every 2022 result fell inside the 80% band.
- In 2024, v1 at 0.45 overpriced longshots (Brier 0.058).

**The live table marks FLIP** (`live_project.is_flip`) only when all four hold, the 2024 test's own terms:
v1 gives the side 45%+ (after the fee), the edge after fees is 5c or more, the side sells for 40c or less
(all three flips were bought at 33c or less), and 20%+ is counted (every backtest is weakest under 20%).
Before 2026-10-30 only the 45% and 20% checks ran; since the best buy is the highest of four edges even when
negative, that flagged 28 of the 59 2024 snapshots with 20%+ counted, mostly 99c favourites. With all four,
the replay flags exactly the three flips above (`tests/test_live_flip.py`).

**What v1 is for:** spotting the moment the market prices the visible leader while the uncounted votes
point the other way. It is not for shaving longshots, and on average it is not better than the market.
The flip rule was found on the 2024 test set (3 cases, 2 won), so treat a FLIP as a prompt to look at
which counties are left, not a trading rule.

## Starting from our margin model (2026-10-30)

The table's `P mod` column, and the best buy under `--baseline model`, start v1 (or v0) from our margin
model instead of the market:
- **Prior:** the model's projected margin for the non-Republican (`docs/forecast_data.js`, `cands[].margin`,
  points of all votes), with a 6.1-point standard deviation. That is the model's held-out 2018-24 miss (MAE
  4.85, model repo HANDOFF 2026-10-29) x 1.25.
- **On the county scale:** the margin is turned into a two-party margin (divided by the counted two-party
  share, or 0.97 before 1,000 votes), and then into the uniform county shift that produces it
  (`county_project.margin_shift`). Its standard error is the shift change for +/-1 sd of margin.
- **Why the margin, not the win chance:** the projector forecasts margins. The forecast page's win chance comes
  from a separate model and can disagree. In GA-Gov the margin model has +1.2 points (58% at a 6.1 sd), while
  the win model has 78%.
- **Maine and Alaska:** the model's margin is the final ranked-choice round, but the count is the first round.

**Not backtested against history.** There are no archived 2022/2024 forecasts, and the model repo keeps no
held-out margins per race. As a stand-in, v1 was run on the 2022/2024 snapshots (36 races, 181 snapshots)
with prior = final margin + N(0, 6.1), 5 draws each. This is a model with the real model's error size but no
shared bias with the count:

| Counted | Miss, no start | Miss, from model | Brier, no start | Brier, from model | Brier, prior alone |
|---|---|---|---|---|---|
| 5-25% | 3.95 | 3.28 | 0.165 | 0.146 | 0.138 |
| 25-50% | 4.41 | 3.91 | 0.087 | 0.072 | 0.075 |
| 50-75% | 0.77 | 0.76 | 0.057 | 0.058 | 0.115 |
| 75-99% | 0.55 | 0.53 | 0.042 | 0.041 | 0.159 |

The model matters under 50% counted and fades as the count takes over, as intended. The 80% bands stay
about as wide (96% inside, as with no start; v1 is wide on these years).

This says nothing about whether the model beats the market's price at the close, which is the real
question for trading. Against 2024's markets v1 started from the market. A real model would also share
polling errors with the market. The default stays `market`; read `P mod` as a second opinion.

## v1 next steps (from the original plan)

From `../State election results/README.md` "Simulator design". For each county (Maine: town), and each
vote type where NYT splits them:

1. **Remaining votes.** Live, NYT's county units carry `total_expected_vote`, `votes_remaining`,
   `eevp_by_vote_type` and precinct file paths (seen in the Aug 4 Michigan primary capture).
2. **How each county is running.** Compare its counted result with `county_benchmarks.csv` for the **same**
   ballot type. Pool these into a statewide swing, weighted by votes counted and pulled toward the starting
   point.
3. **Project the rest.** Apply that swing to each county's uncounted votes of each type. County errors are
   correlated and sized from the benchmark backtest (1-5 pt typical miss); turnout uncertainty comes from the
   expected vote.
4. **Replay before Nov 3.** Run it on the 2020 Wayback county captures, the only dense county timing, and
   check calibration as above.
5. **Monte Carlo.** Run it forward from release timing (`county_reporting.json`) to simulate whole nights
   and print a threshold sheet per state.

Precinct files would sharpen Nevada (Clark) and Michigan (Wayne) further.
