# Competitive 2026 Governor and Senate races

Source: `docs/forecast_data.js` (model run 2026-10-27 20:58 UTC, polls through 2026-10-27). Competitive = the model's favorite has a win probability of 75% or less. Built by `scripts/build_competitive.py`; numbers move with every model refresh, so rebuild before relying on it.

## By state

| State | Competitive races |
|---|---|
| Iowa | Senate |
| Kansas | Senate, Governor |
| Nevada | Governor |
| Nebraska | Senate |
| Texas | Senate |
| Alaska | Senate |
| South Carolina | Senate |
| Georgia | Governor |
| Maine | Senate |
| Ohio | Senate (special), Governor |

12 races in 10 states.

## Competitive races (favorite at 75% or less)

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Iowa | Senate | Josh Turek (DEM) | 50.4% | +0.5 | Ashley Hinson (REP) | Josh Turek (DEM) 41% | 36 |
| Kansas | Senate | Adam Hamilton (DEM) | 50.5% | +1.2 | Roger Marshall (REP) | Adam Hamilton (DEM) 40% | 15 |
| Nevada | Governor | Joe Lombardo (REP) | 58.7% | -0.6 | Aaron Ford (DEM) | Aaron Ford (DEM) 78% | 17 |
| Nebraska | Senate | Pete Ricketts (REP) | 58.8% | +0.8 | Dan Osborn (IND) | Dan Osborn (IND) 28% | 19 |
| Texas | Senate | James Talarico (DEM) | 63.8% | +3.1 | Ken Paxton (REP) | James Talarico (DEM) 66% | 67 |
| Alaska | Senate | Mary Peltola (DEM) | 63.9% | +2.2 | Dan Sullivan (REP) | Mary Peltola (DEM) 74% | 21 |
| South Carolina | Senate | Darline Graham (REP) | 68.0% | +2.2 | Annie Andrews (DEM) | Annie Andrews (DEM) 22% | 11 |
| Georgia | Governor | Keisha Lance Bottoms (DEM) | 70.8% | +0.0 | Rick Jackson (REP) | Keisha Lance Bottoms (DEM) 62% | 18 |
| Maine | Senate | Troy Jackson (DEM) | 71.8% | +3.4 | Susan Collins (REP) | Troy Jackson (DEM) 62% | 30 |
| Kansas | Governor | Ty Masterson (REP) | 71.9% | +2.3 | Cindy Holscher (DEM) | Cindy Holscher (DEM) 28% | 8 |
| Ohio | Senate (special) | Sherrod Brown (DEM) | 72.0% | +3.1 | Jon Husted (REP) | Sherrod Brown (DEM) 69% | 42 |
| Ohio | Governor | Amy Acton (DEM) | 74.1% | +2.7 | Vivek Ramaswamy (REP) | Amy Acton (DEM) 78% | 35 |

## Just outside the cut (favorite 75-80%)

Not part of the vote-timing research; listed so a model shift is easy to spot.

| State | Race | Model favorite | Model win % | Model margin (pts, separate model) | Main opponent | Market (side priced) | Surveys |
|---|---|---|---|---|---|---|---|
| Oregon | Governor | Tina Kotek (DEM) | 77.0% | +4.1 | Christine Drazan (REP) | Tina Kotek (DEM) 81% | 7 |
| Oklahoma | Governor | Mike Mazzei (REP) | 78.2% | +5.4 | Cyndi Munson (DEM) | Cyndi Munson (DEM) 12% | 3 |
| Michigan | Senate | Abdul El-Sayed (DEM) | 79.4% | +4.9 | Mike Rogers (REP) | Abdul El-Sayed (DEM) 69% | 57 |

## Market favors a different candidate

- Iowa Senate: model Josh Turek 50.4%, market implies Josh Turek about 41%
- Kansas Senate: model Adam Hamilton 50.5%, market implies Adam Hamilton about 40%
- Nevada Governor: model Joe Lombardo 58.7%, market implies Joe Lombardo about 22%

## Not in the forecast

These Governor/Senate races are on the ballot (`docs/data.js`) but not in the forecast file, so they were not screened: none.

## Notes from the research that affect these races

- **Nebraska Senate:** no Democratic nominee (Cindy Burbank withdrew in July and backed Osborn). Ballot: Ricketts (R), Osborn (I), Conboy (America First), Richards (Nebraska Working People Party), Marvin (Legal Marijuana NOW; withdrew but stays on the ballot).
- **Alaska Senate** and **Maine Senate** use ranked-choice voting; a winner may not be known until the RCV count (Alaska Nov 18; Maine usually 8-10 days after the election).
- **Georgia Governor:** majority needed or a Dec 1 runoff; two-candidate ballot, so runoff risk is near zero. A margin of 0.5% or less triggers an automatic statewide hand recount (2026 law).
- **Nevada Governor:** Lombardo (R), Aaron Ford (D), Danielle Ford (no party) and "None of these candidates", which is reported but never decides the winner (NRS 293.269). Close races are counted Wednesday to Saturday; the late count has leaned Democratic in every statewide race since 2020.
- **Oregon Governor:** a 2022 rematch (Kotek D vs Drazan R, plus Pacific Green's Brett Smith). Election Day drop-offs, a quarter of the vote, are counted Wednesday to Friday; automatic recount at 0.2%.
- **Texas Governor:** counted with the Senate race; the Texas rules apply unchanged.
