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
- our model's win probability (`P mod`).

The win probability is used rather than the margin model's margin, because the two models can disagree on
the favorite: on Oct 28, Georgia's margin was +0.01 with Bottoms at 71% to win, and Nevada's was Ford +0.6
with Lombardo at 59%. The guides quote the win model.

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

## v1 plan: county x vote type

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
