# Competitive 2026 Governor and Senate races

Source: `docs/forecast_data.js` (model run 2026-10-27 17:04 UTC, polls through 2026-10-25). Competitive = the model's favorite has a win probability of 75% or less. Built by `scripts/build_competitive.py`; numbers move with every model refresh, so rebuild before relying on it.

## By state

| State | Competitive races |
|---|---|
| Alaska | Senate |
| Ohio | Governor, Senate (special) |
| Texas | Senate |
| Nevada | Governor |
| Michigan | Senate |
| Kansas | Senate |

7 races in 6 states.

## Competitive races (favorite at 75% or less)

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Alaska | Senate | Dan Sullivan (REP) | 54.5% | -0.4 | Mary Peltola (DEM) | Mary Peltola (DEM) 74% | 21 |
| Ohio | Governor | Amy Acton (DEM) | 55.8% | +1.3 | Vivek Ramaswamy (REP) | Amy Acton (DEM) 79% | 34 |
| Texas | Senate | Ken Paxton (REP) | 62.5% | -1.1 | James Talarico (DEM) | James Talarico (DEM) 66% | 65 |
| Ohio | Senate (special) | Sherrod Brown (DEM) | 64.5% | +0.8 | Jon Husted (REP) | Sherrod Brown (DEM) 68% | 41 |
| Nevada | Governor | Joe Lombardo (REP) | 65.0% | +0.0 | Aaron Ford (DEM) | Aaron Ford (DEM) 75% | 16 |
| Michigan | Senate | Abdul El-Sayed (DEM) | 70.8% | +3.2 | Mike Rogers (REP) | Abdul El-Sayed (DEM) 69% | 56 |
| Kansas | Senate | Roger Marshall (REP) | 73.7% | +0.9 | Adam Hamilton (DEM) | Adam Hamilton (DEM) 40% | 15 |

## Just outside the cut (favorite 75-80%)

Not part of the vote-timing research; listed so a model shift is easy to spot.

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Vermont | Governor | Phil Scott (REP) | 75.7% | +1.9 | Amanda Janoo (DEM) | Amanda Janoo (DEM) 23% | 6 |
| Iowa | Senate | Ashley Hinson (REP) | 77.2% | +3.0 | Josh Turek (DEM) | Josh Turek (DEM) 42% | 35 |
| Nebraska | Senate | Pete Ricketts (REP) | 78.0% | +2.7 | Dan Osborn (IND) | Dan Osborn (IND) 28% | 18 |

## Market favors a different candidate

- Alaska Senate: model Dan Sullivan 54.5%, market implies Dan Sullivan about 26%
- Texas Senate: model Ken Paxton 62.5%, market implies Ken Paxton about 34%
- Nevada Governor: model Joe Lombardo 65.0%, market implies Joe Lombardo about 25%

## Not in the forecast

These Governor/Senate races are on the ballot (`docs/data.js`) but not in the forecast file, so they were not screened: none.

## Notes from the research that affect these races

- **Nebraska Senate:** no Democratic nominee (Cindy Burbank withdrew in July and backed Osborn). Ballot: Ricketts (R), Osborn (I), Conboy (America First), Richards (Nebraska Working People Party), Marvin (Legal Marijuana NOW; withdrew but stays on the ballot).
- **Alaska Senate** and **Maine Senate** use ranked-choice voting; a winner may not be known until the RCV count (Alaska Nov 18; Maine usually 8-10 days after the election).
- **Georgia Governor:** majority needed or a Dec 1 runoff; two-candidate ballot, so runoff risk is near zero. A margin of 0.5% or less triggers an automatic statewide hand recount (2026 law).
- **Nevada Governor:** Lombardo (R), Aaron Ford (D), Danielle Ford (no party) and "None of these candidates", which is reported but never decides the winner (NRS 293.269). Close races are counted Wednesday to Saturday; the late count has leaned Democratic in every statewide race since 2020.
- **Oregon Governor:** a 2022 rematch (Kotek D vs Drazan R, plus Pacific Green's Brett Smith). Election Day drop-offs, a quarter of the vote, are counted Wednesday to Friday; automatic recount at 0.2%.
- **Texas Governor:** counted with the Senate race; the Texas rules apply unchanged.
