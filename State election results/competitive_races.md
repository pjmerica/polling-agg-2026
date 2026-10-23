# Competitive 2026 Governor and Senate races

Source: `docs/forecast_data.js` (model run 2026-10-23 03:37 UTC, polls through 2026-10-22). Competitive = the model's favorite has a win probability of 75% or less. Built by `scripts/build_competitive.py`; numbers move with every model refresh, so rebuild before relying on it.

## By state

| State | Competitive races |
|---|---|
| Alaska | Senate |
| Texas | Senate, Governor |
| Georgia | Governor |
| Kansas | Senate |
| Ohio | Governor, Senate (special) |
| Nebraska | Senate |
| Michigan | Senate |
| Iowa | Senate |
| Maine | Senate |
| Nevada | Governor |
| Oregon | Governor |

13 races in 11 states.

## Competitive races (favorite at 75% or less)

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Alaska | Senate | Mary Peltola (DEM) | 51.9% | -0.2 | Dan Sullivan (REP) | Mary Peltola (DEM) 75% | 21 |
| Texas | Senate | James Talarico (DEM) | 55.0% | +1.2 | Ken Paxton (REP) | James Talarico (DEM) 66% | 61 |
| Georgia | Governor | Keisha Lance Bottoms (DEM) | 55.0% | -0.7 | Rick Jackson (REP) | Keisha Lance Bottoms (DEM) 61% | 17 |
| Kansas | Senate | Roger Marshall (REP) | 58.8% | +0.9 | Adam Hamilton (DEM) | Adam Hamilton (DEM) 39% | 14 |
| Ohio | Governor | Amy Acton (DEM) | 58.8% | +0.9 | Vivek Ramaswamy (REP) | Amy Acton (DEM) 82% | 34 |
| Ohio | Senate (special) | Sherrod Brown (DEM) | 59.6% | +0.9 | Jon Husted (REP) | Sherrod Brown (DEM) 69% | 39 |
| Nebraska | Senate | Pete Ricketts (REP) | 62.2% | +3.6 | Dan Osborn (IND) | Dan Osborn (IND) 25% | 15 |
| Michigan | Senate | Abdul El-Sayed (DEM) | 63.4% | +3.0 | Mike Rogers (REP) | Abdul El-Sayed (DEM) 70% | 53 |
| Iowa | Senate | Ashley Hinson (REP) | 68.2% | +0.9 | Josh Turek (DEM) | Josh Turek (DEM) 42% | 34 |
| Maine | Senate | Troy Jackson (DEM) | 68.7% | +1.5 | Susan Collins (REP) | Troy Jackson (DEM) 65% | 27 |
| Nevada | Governor | Joe Lombardo (REP) | 69.5% | +3.3 | Aaron Ford (DEM) | Aaron Ford (DEM) 67% | 14 |
| Oregon | Governor | Tina Kotek (DEM) | 70.1% | +4.5 | Christine Drazan (REP) | Tina Kotek (DEM) 82% | 7 |
| Texas | Governor | Greg Abbott (REP) | 74.0% | +4.9 | Gina Hinojosa (DEM) | Gina Hinojosa (DEM) 31% | 54 |

## Just outside the cut (favorite 75-80%)

Not part of the vote-timing research; listed so a model shift is easy to spot.

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Kansas | Governor | Ty Masterson (REP) | 77.1% | +4.6 | Cindy Holscher (DEM) | Cindy Holscher (DEM) 25% | 7 |
| Wisconsin | Governor | David Crowley (DEM) | 79.5% | +5.4 | Tom Tiffany (REP) | David Crowley (DEM) 80% | 9 |

## Market favors a different candidate

- Nevada Governor: model Joe Lombardo 69.5%, market implies Joe Lombardo about 33%

## Not in the forecast

These Governor/Senate races are on the ballot (`docs/data.js`) but not in the forecast file, so they were not screened: CO-Gov, HI-Gov, ME-Gov, NM-Gov, WY-Gov, CO-Sen, DE-Sen, NJ-Sen, OR-Sen, WV-Sen, WY-Sen.

## Notes from the research that affect these races

- **Nebraska Senate:** no Democratic nominee (Cindy Burbank withdrew in July and backed Osborn). Ballot: Ricketts (R), Osborn (I), Conboy (America First), Richards (Nebraska Working People Party), Marvin (Legal Marijuana NOW; withdrew but stays on the ballot).
- **Alaska Senate** and **Maine Senate** use ranked-choice voting; a winner may not be known until the RCV count (Alaska Nov 18; Maine usually 8-10 days after the election).
- **Georgia Governor:** majority needed or a Dec 1 runoff; two-candidate ballot, so runoff risk is near zero. A margin of 0.5% or less triggers an automatic statewide hand recount (2026 law).
- **Nevada Governor:** Lombardo (R), Aaron Ford (D), Danielle Ford (no party) and "None of these candidates", which is reported but never decides the winner (NRS 293.269). Close races are counted Wednesday to Saturday; the late count has leaned Democratic in every statewide race since 2020.
- **Oregon Governor:** a 2022 rematch (Kotek D vs Drazan R, plus Pacific Green's Brett Smith). Election Day drop-offs, a quarter of the vote, are counted Wednesday to Friday; automatic recount at 0.2%.
- **Texas Governor:** counted with the Senate race; the Texas rules apply unchanged.
