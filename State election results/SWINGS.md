# How far the count moves after polls close: eleven states, 2020-2026

*Built 2026-10-21 by `scripts/build_swings_report.py`; Nevada and Oregon added 2026-10-22. Every table is generated from NYT's
minute-by-minute results timelines (406 races: 293 contested general-election races
2020-2024, plus 2026 primaries, runoffs and specials) and Internet Archive copies of NYT's 2020
county results. No number in a table was typed by hand.*

## How to read this

- **Margin** = Democrat (or independent) minus Republican, in points of all votes counted so far.
  In primaries, it's winner minus runner-up.
- **Move after 2 h** = final margin minus the margin 2 hours after the state's main poll close.
  - Positive: the count moved toward the Democrat/independent after that point.
  - Negative: toward the Republican.
- **Poll close used (ET):** GA 7:00, OH 7:30, MI/TX/KS/ME 8:00, IA/NE 9:00, NV 10:00, OR 11:00, AK midnight.
  Iowa 2020 uses 10:00: its polls closed an hour later until SF 413 (2021).
- **A move is measured only from a point with 3%+ counted.** A handful of early votes is not a margin; Nevada 2020 had 0% at 2 hours.
  - "6 am" means 6 am ET the morning after, roughly the end of election-night counting.
- **What's included:** every statewide office, House seat and ballot measure NYT covered in these eleven states, not only Governor and Senate.
  More races means more examples of how each state's counties report.
- **Caveats:**
  1. **2020 was a record mail year.** Its late swings (Michigan, Georgia, Alaska) were larger than 2022/2024.
  2. **The rules have changed since then:**
     - Michigan now counts absentees before Election Day.
     - Georgia must report early votes by 8 pm.
     - Ohio ended its late-mail window.
  3. **NYT's 2024 presidential timelines** stop at 5:40 am Wednesday. Their "final" is still the certified result.
  4. **Ranked-choice races (Alaska, Maine)** are measured on **first-round** votes and marked [RCV, 1st round].
     The official winner can differ (see Maine's 2026 primary below).
  5. **Shares under ~10% counted are noise.** The biggest-swing tables require at least 10% counted at the 2-hour mark.

## 1. Bottom line, state by state

| State | Typical election-night move (from the data below) | After election night | What drives it |
|---|---|---|---|
| **Kansas** | **Largest and most consistent toward Republicans**: all 10 races in 2022 moved 5+ pts after 2 h, by a median of −19 | Under 1 pt | Advance (mail/early) votes come first and lean D; rural Election Day precincts follow |
| **Iowa** | Huge in the first hour (median −13 to −29 after 1 h), small after 2 h (~3/4 counted by then) | Under 1 pt | Each county's absentee batch lands early and leans D; Election Day is ~25-30 pts more R |
| **Nebraska** | −7 to −9 pts after 2 h, every year | ~0-1 pt (Omaha's leftovers) | Early votes first in most counties; Omaha and Lincoln post their Election Day votes late |
| **Ohio** | −3 to −6 after 2 h (2022/2024); −11 in 2020 | ~0 | All 88 counties dump early votes first, by law by 8 pm |
| **Georgia** | 2022: −3 after 2 h, but up to −20 down-ballot; 2024: ~0; 2020: +16 | 2020: +2; since then ~0 | Early votes must be reported by 8 pm (since 2024). In 2020, Atlanta-area mail came overnight |
| **Michigan** | Biggest **two-way** swings: 2020 +21 toward D; 2024 Senate D early, R overnight, D at the end | **Up to +7 (2020)**, +2 (2022), ~0 (2024) | Wayne/Detroit and other big counties report late |
| **Maine** | +5 to +8 toward the non-Republican after 2 h | **0 to −3 back toward R after 6 am** | Big towns (Portland, Cumberland County) report through the night; small rural towns last |
| **Texas** | Smallest: −1 to −3.4 after 2 h | Under 0.5 | 62-79% is counted in the first one or two hours (early vote) |
| **Nevada** | Nothing posts until ~11:50 pm-1 am ET. The first big drop leaned D in 2020 and 2022 (2022 Senate +12.6 with 44% in), then Election Day votes moved it to R by morning (−2.7) | **Toward D in 17 of 18 races 2020-2024**, every statewide one (median +3.2 in 2022, +1.8 in 2020 and 2024) | Election Day drop-offs and late mail, mostly Clark County, counted Wed-Sat |
| **Oregon** | First release at 11 pm ET holds 55-84% of the vote; 2022 then moved toward R overnight (Governor Kotek +9.8 → +1.1) | **+1.0 (2022) and +0.5 (2024) median toward D; −1.5 in 2020** | Election Day drop-box ballots, counted Wed-Fri |
| **Alaska** | (Polls close at midnight ET) | **+16 (2020), +2 to +3 (2022/2024) toward D** | Mail ballots are counted Nov 10-18 |

## 2. Pace and typical move, by state and year

Median over every contested general-election race in that state and year.

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Georgia | 2020 | 2 | 10% / 32% / 79% / 94% | +5.1 | +15.7 | +2.3 | 2 of 2 |
| Georgia | 2022 | 22 | 27% / 54% / 93% / 100% | -14.3 | -3.1 | +0.0 | 11 of 22 |
| Georgia | 2024 | 15 | 30% / 69% / 99% / 100% | -0.5 | +0.2 | +0.0 | 5 of 15 |
| Ohio | 2020 | 1 | 47% / 64% / 95% / 96% | -18.2 | -10.7 | +0.1 | 1 of 1 |
| Ohio | 2022 | 21 | 29% / 56% / 97% / 98% | -18.7 | -6.0 | +0.2 | 12 of 21 |
| Ohio | 2024 | 17 | 41% / 61% / 97% / 98% | -10.2 | -3.1 | +0.1 | 3 of 17 |
| Michigan | 2020 | 2 | 13% / 24% / 50% / 81% | +20.5 | +20.6 | +7.2 | 2 of 2 |
| Michigan | 2022 | 16 | 7% / 15% / 48% / 93% | +0.6 | +5.3 | +2.0 | 11 of 15 |
| Michigan | 2024 | 15 | 9% / 13% / 46% / 98% | -2.7 | -2.8 | +0.0 | 6 of 10 |
| Texas | 2020 | 2 | 66% / 79% / 91% / 99% | -6.4 | -3.4 | +0.4 | 0 of 2 |
| Texas | 2022 | 41 | 35% / 64% / 82% / 99% | -5.8 | -3.4 | +0.1 | 15 of 41 |
| Texas | 2024 | 33 | 70% / 74% / 88% / 100% | -1.3 | -1.0 | +0.2 | 3 of 33 |
| Kansas | 2020 | 2 | 35% / 57% / 80% / 92% | -20.4 | -8.7 | -0.5 | 2 of 2 |
| Kansas | 2022 | 10 | 13% / 23% / 93% / 97% | -18.0 | -18.9 | +0.7 | 10 of 10 |
| Kansas | 2024 | 5 | 30% / 58% / 87% / 96% | -9.0 | -10.6 | +0.4 | 3 of 5 |
| Maine | 2020 | 2 | 2% / 9% / 35% / 71% | - | +7.8 | -3.0 | 2 of 2 |
| Maine | 2022 | 3 | 2% / 21% / 63% / 83% | +12.3 | +5.4 | -0.0 | 2 of 3 |
| Maine | 2024 | 6 | 1% / 5% / 33% / 72% | - | +7.4 | -1.7 | 3 of 5 |
| Iowa | 2020 | 2 | 49% / 87% / 87% / 100% | -18.6 | -2.2 | -0.4 | 0 of 2 |
| Iowa | 2022 | 11 | 24% / 71% / 94% / 100% | -28.5 | -2.2 | -0.0 | 2 of 11 |
| Iowa | 2024 | 5 | 10% / 75% / 90% / 99% | -14.0 | +0.5 | +0.0 | 2 of 5 |
| Nebraska | 2020 | 2 | 34% / 49% / 62% / 88% | -12.8 | -8.7 | +0.1 | 1 of 2 |
| Nebraska | 2022 | 7 | 39% / 50% / 74% / 96% | -13.0 | -6.9 | +1.1 | 6 of 7 |
| Nebraska | 2024 | 8 | 32% / 47% / 59% / 95% | -15.3 | -7.0 | +0.4 | 6 of 8 |
| Nevada | 2020 | 1 | - / 0% / 0% / 85% | - | - | +1.8 | 0 of 0 |
| Nevada | 2022 | 11 | - / - / - / 82% | - | - | +3.2 | 0 of 0 |
| Nevada | 2024 | 6 | - / - / - / 87% | - | - | +1.8 | 0 of 0 |
| Oregon | 2020 | 2 | 82% / 84% / 82% / 90% | -3.2 | -3.2 | -1.5 | 0 of 2 |
| Oregon | 2022 | 8 | 55% / 63% / 55% / 71% | +1.7 | +1.3 | +1.0 | 0 of 8 |
| Oregon | 2024 | 9 | 65% / 68% / 65% / 77% | +0.8 | +0.4 | +0.5 | 0 of 9 |
| Alaska | 2020 | 2 | - / - / - / 37% | - | - | +16.0 | 0 of 0 |
| Alaska | 2022 | 2 | - / 56% / - / 77% | - | +6.1 | +2.2 | 2 of 2 |
| Alaska | 2024 | 2 | - / 30% / - / 73% | - | +4.1 | +2.6 | 1 of 2 |

## 3. The biggest moves in competitive races (final margin within 15 pts)

Up to five per state, largest move after 2 h first.

**Georgia**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 Lieutenant Governor | 16.3% / +15.2 | 90.3% / -5.6 | 99.2% / -5.3 | -5.0 | **-20.2** | +0.4 |
| 2022 Attorney General | 16.3% / +14.6 | 90.0% / -5.9 | 98.8% / -5.3 | -5.3 | **-19.9** | +0.0 |
| 2022 Labor Commissioner | 16.3% / +13.1 | 90.3% / -7.5 | 99.1% / -6.9 | -6.8 | **-19.9** | +0.2 |
| 2022 Insurance Commissioner | 16.3% / +11.6 | 90.1% / -8.9 | 98.8% / -8.3 | -8.2 | **-19.8** | +0.1 |
| 2022 Agriculture Commissioner | 16.3% / +11.5 | 90.0% / -8.8 | 98.8% / -8.1 | -8.1 | **-19.6** | +0.0 |

**Ohio**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 13 | 32.9% / +28.7 | 97.6% / +5.1 | 98.0% / +5.2 | +5.3 | **-23.4** | +0.2 |
| 2022 House 1 | 40.7% / +20.2 | 97.0% / +4.8 | 97.4% / +4.9 | +5.5 | **-14.6** | +0.6 |
| 2024 House 13 | 44.3% / +13.9 | 72.1% / +6.4 | 98.1% / +2.1 | +2.2 | **-11.7** | +0.1 |
| 2022 House 15 | 31.3% / -2.7 | 96.3% / -15.0 | 97.4% / -14.5 | -13.9 | **-11.2** | +0.6 |
| 2022 House 7 | 48.5% / +0.4 | 95.5% / -11.7 | 98.0% / -10.9 | -10.7 | **-11.1** | +0.2 |

**Michigan**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 House 3 | 13.5% / +36.2 | 59.6% / +14.5 | 96.4% / +9.7 | +9.9 | **-26.3** | +0.2 |
| 2022 House 8 | 13.5% / -11.8 | 49.5% / -1.4 | 93.4% / +6.8 | +10.3 | **+22.1** | +3.5 |
| 2020 Senate | 23.8% / -19.2 | 49.2% / -11.9 | 80.1% / -5.6 | +1.7 | **+20.9** | +7.3 |
| 2022 House 7 | 22.2% / -15.5 | 53.6% / -11.3 | 96.9% / +3.5 | +5.4 | **+20.9** | +1.9 |
| 2020 President | 23.3% / -17.6 | 49.8% / -10.6 | 81.9% / -4.3 | +2.8 | **+20.4** | +7.1 |

**Texas**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 House 15 | 15.0% / -44.9 | 84.6% / -16.7 | 99.7% / -14.3 | -14.2 | **+30.7** | +0.1 |
| 2022 Attorney General | 42.9% / +0.2 | 82.0% / -11.3 | 98.1% / -10.2 | -9.8 | **-10.0** | +0.4 |
| 2022 Agriculture Commissioner | 43.0% / -2.8 | 81.9% / -14.2 | 98.1% / -13.0 | -12.7 | **-9.8** | +0.4 |
| 2022 Lieutenant Governor | 42.9% / -0.5 | 82.0% / -11.8 | 98.1% / -10.7 | -10.3 | **-9.8** | +0.4 |
| 2022 Railroad Commissioner | 43.0% / -5.0 | 81.9% / -16.2 | 98.2% / -15.2 | -14.8 | **-9.8** | +0.4 |

**Kansas**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 Treasurer | 13.2% / +9.3 | 93.4% / -11.8 | 98.1% / -13.4 | -12.8 | **-22.0** | +0.7 |
| 2022 Attorney General | 13.2% / +18.1 | 93.5% / -0.7 | 98.1% / -2.4 | -1.7 | **-19.7** | +0.7 |
| 2022 Governor | 24.5% / +20.3 | 92.1% / +3.0 | 96.7% / +1.5 | +2.2 | **-18.1** | +0.8 |
| 2022 House 3 | 51.7% / +24.0 | 95.7% / +12.2 | 96.9% / +11.7 | +12.2 | **-11.9** | +0.5 |
| 2020 Senate | 56.2% / -2.7 | 81.0% / -10.9 | 91.7% / -11.0 | -11.4 | **-8.7** | -0.4 |

**Maine**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2020 President | 10.5% / +1.2 | 41.8% / +5.4 | 73.1% / +12.3 | +9.1 | **+7.9** | -3.2 |
| 2022 House 2 [RCV, 1st round] | 24.3% / -3.0 | 63.6% / +3.0 | 81.8% / +4.6 | +3.7 | **+6.8** | -0.8 |
| 2022 Governor | 21.3% / +7.9 | 63.1% / +9.4 | 83.2% / +13.2 | +13.2 | **+5.4** | -0.0 |

**Iowa**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 1 | 59.9% / +0.6 | 97.2% / -6.8 | 98.6% / -6.6 | -6.8 | **-7.4** | -0.2 |
| 2024 House 1 | 74.0% / -5.6 | 87.7% / +1.5 | 98.6% / -0.1 | -0.2 | **+5.4** | -0.1 |
| 2024 House 3 | 89.8% / -0.5 | 95.4% / -2.2 | 99.9% / -3.9 | -3.8 | **-3.3** | +0.0 |
| 2020 President | 86.1% / -5.5 | 86.1% / -5.5 | 99.7% / -7.3 | -8.2 | **-2.7** | -0.9 |
| 2022 House 3 | 94.2% / +1.8 | 99.8% / -0.7 | 99.8% / -0.7 | -0.7 | **-2.5** | -0.0 |

**Nebraska**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 President (district 1) | 44.1% / +1.3 | 55.7% / -1.9 | 94.8% / -13.4 | -13.0 | **-14.3** | +0.3 |
| 2024 Senate | 50.1% / +1.5 | 61.4% / -1.9 | 96.1% / -7.6 | -6.7 | **-8.2** | +0.9 |
| 2024 President (district 2) | 70.7% / +9.9 | 76.2% / +8.4 | 94.0% / +4.2 | +4.6 | **-5.3** | +0.4 |
| 2024 House 2 | 70.9% / +2.5 | 76.4% / +1.2 | 94.0% / -2.4 | -1.9 | **-4.4** | +0.5 |
| 2022 House 2 | 67.4% / +0.0 | 77.4% / -1.7 | 93.4% / -4.4 | -2.7 | **-2.7** | +1.7 |

**Oregon**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 5 | 58.3% / -5.6 | 57.5% / -5.1 | 69.0% / -4.5 | -2.1 | **+3.5** | +2.4 |
| 2024 House 4 | 73.3% / +10.5 | 73.3% / +10.5 | 82.3% / +8.9 | +7.8 | **-2.7** | -1.1 |
| 2022 Governor | 62.8% / +1.0 | 52.6% / +0.9 | 73.4% / +1.1 | +3.4 | **+2.4** | +2.4 |
| 2022 House 4 | 72.9% / +9.8 | 32.7% / -0.0 | 85.1% / +8.1 | +7.5 | **-2.3** | -0.7 |
| 2022 Senate | 63.0% / +13.3 | 59.8% / +14.5 | 73.5% / +13.1 | +14.9 | **+1.7** | +1.8 |

**Alaska**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 President | 30.0% / -18.2 | -% / - | 72.1% / -15.4 | -13.1 | **+5.1** | +2.2 |
| 2024 House 1 [RCV, 1st round] | 30.5% / -5.2 | -% / - | 73.3% / -5.0 | -2.0 | **+3.2** | +2.9 |


What stands out:
- **Georgia 2022:** five statewide Democrats led by 11-15 pts two hours after close (16% counted) and lost by 5-8.
  The early vote was Democratic; Election Day was not (section 6).
- **Kansas 2022:** the Democratic Attorney General candidate led by 18 two hours in and lost by 1.7. Governor Kelly's +20 shrank to a 2.2 win.
- **Michigan:** swings go both ways depending on which big county reports when.
  - 2022 House 7 (Slotkin) was −15.5 at two hours and won by 5.4.
  - 2024 House 3 was +36 at two hours and won by 10.
- **Iowa 2020:** Biden +12 and Greenfield +10 one hour after the close (about half counted); both trailed by midnight and lost by 8.2 and 6.6.

## 4. Every race where the leader at 2 hours or at midnight lost

General elections only. "Ahead for good" is when the eventual winner took the lead and never gave it back (10%+ counted).

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Georgia 2020 President | GA-G-P-2020-11-03 | Trump (32.3%) | Trump (79.6%) | Trump (94.4%) | Biden +0.2 | Nov 5 9:32 pm (99.0% in) |
| Georgia 2022 Agriculture Commissioner | GA-G-agriculture_commissioner-2022-11-08 | Hemingway (16.3%) | Harper (90.0%) | Harper (98.8%) | Harper +8.1 | 9:31 pm (44.5% in) |
| Georgia 2022 Attorney General | GA-G-attorney_general-2022-11-08 | Jordan (16.3%) | Carr (90.0%) | Carr (98.8%) | Carr +5.3 | 9:31 pm (45.7% in) |
| Georgia 2022 Insurance Commissioner | GA-G-insurance_commissioner-2022-11-08 | Laws Robinson (16.3%) | King (90.1%) | King (98.8%) | King +8.2 | 9:31 pm (43.9% in) |
| Georgia 2022 Labor Commissioner | GA-G-labor_commissioner-2022-11-08 | Boddie (16.3%) | Thompson (90.3%) | Thompson (99.1%) | Thompson +6.8 | 9:31 pm (44.4% in) |
| Georgia 2022 Lieutenant Governor | GA-G-LG-2022-11-08 | Bailey (16.3%) | Jones (90.3%) | Jones (99.2%) | Jones +5.0 | 9:32 pm (66.7% in) |
| Georgia 2022 Senate | GA-G-S-2022-11-08 | Warnock (55.6%) | Walker (93.7%) | Warnock (99.5%) | Warnock +1.0 | Wed 12:17 am (94.3% in) |
| Ohio 2020 President | OH-G-P-2020-11-03 | Biden (63.6%) | Trump (94.7%) | Trump (96.2%) | Trump +8.0 | 10:00 pm (73.3% in) |
| Ohio 2022 House 7 | OH-G-H-7-2022-11-08 | Diemer (48.5%) | Miller (95.5%) | Miller (98.0%) | Miller +10.7 | 9:42 pm (51.9% in) |
| Michigan 2020 President | MI-G-P-2020-11-03 | Trump (23.3%) | Trump (49.8%) | Trump (81.9%) | Biden +2.8 | Wed 9:02 am (90.6% in) |
| Michigan 2020 Senate | MI-G-S-2020-11-03 | James (23.8%) | James (49.2%) | James (80.1%) | Peters +1.7 | Wed 3:52 pm (96.9% in) |
| Michigan 2022 House 7 | MI-G-H-7-2022-11-08 | Barrett (22.2%) | Barrett (53.6%) | Slotkin (96.9%) | Slotkin +5.4 | Wed 2:32 am (95.1% in) |
| Michigan 2022 House 8 | MI-G-H-8-2022-11-08 | Junge (13.5%) | Junge (49.5%) | Kildee (93.4%) | Kildee +10.3 | Wed 12:21 am (52.2% in) |
| Michigan 2024 House 8 | MI-G-H-8-2024-11-05 | - (0.3%) | Junge (29.8%) | McDonald Rivet (100.0%) | McDonald Rivet +6.6 | Wed 12:05 am (32.7% in) |
| Michigan 2024 President | MI-G-P-2024-11-05 | Harris (12.7%) | Trump (46.4%) | Trump (95.6%) | Trump +1.4 | 10:38 pm (24.6% in) |
| Michigan 2024 Senate | MI-G-S-2024-11-05 | Slotkin (12.6%) | Rogers (46.0%) | Rogers (95.7%) | Slotkin +0.3 | Wed 7:31 am (97.5% in) |
| Texas 2022 Attorney General | TX-G-attorney_general-2022-11-08 | Garza (42.9%) | Paxton (82.0%) | Paxton (98.1%) | Paxton +9.8 | 10:02 pm (49.7% in) |
| Texas 2024 House 28 | TX-G-H-28-2024-11-05 | Furman (45.8%) | Cuellar (86.1%) | Cuellar (100.0%) | Cuellar +5.6 | 10:34 pm (65.6% in) |
| Kansas 2022 Attorney General | KS-G-attorney_general-2022-11-08 | Mann (13.2%) | Kobach (93.5%) | Kobach (98.1%) | Kobach +1.7 | 11:37 pm (91.6% in) |
| Kansas 2022 House 1 | KS-G-H-1-2022-11-08 | Beard (21.3%) | Mann (86.3%) | Mann (96.1%) | Mann +35.3 | 10:05 pm (41.9% in) |
| Kansas 2022 House 2 | KS-G-H-2-2022-11-08 | Schmidt (26.8%) | LaTurner (91.9%) | LaTurner (97.3%) | LaTurner +15.3 | 10:14 pm (56.2% in) |
| Kansas 2022 Senate | KS-G-S-2022-11-08 | Holland (38.8%) | Moran (92.3%) | Moran (96.6%) | Moran +23.0 | 10:05 pm (58.0% in) |
| Kansas 2022 Treasurer | KS-G-treasurer-2022-11-08 | Rogers (13.2%) | Johnson (93.4%) | Johnson (98.1%) | Johnson +12.8 | 10:05 pm (54.1% in) |
| Maine 2022 House 2 [RCV, 1st round] | ME-G-H-2-2022-11-08 | Poliquin (24.3%) | Golden (63.6%) | Golden (81.8%) | Golden +3.7 | 10:02 pm (30.8% in) |
| Maine 2024 House 2 [RCV, 1st round] | ME-G-H-2-2024-11-05 | - (5.9%) | Theriault (34.0%) | Golden (72.3%) | Golden +0.6 | Wed 2:02 am (62.1% in) |
| Iowa 2022 Attorney General | IA-G-attorney_general-2022-11-08 | Miller (71.1%) | Bird (94.3%) | Bird (99.6%) | Bird +1.7 | 11:10 pm (79.5% in) |
| Iowa 2022 Auditor | IA-G-auditor-2022-11-08 | Sand (71.1%) | Halbur (94.3%) | Sand (99.6%) | Sand +0.2 | Wed 2:01 am (99.6% in) |
| Iowa 2022 House 1 | IA-G-H-1-2022-11-08 | Bohannan (59.9%) | Miller-Meeks (97.2%) | Miller-Meeks (98.6%) | Miller-Meeks +6.8 | 11:04 pm (61.9% in) |
| Iowa 2022 House 3 | IA-G-H-3-2022-11-08 | Axne (94.2%) | Nunn (99.8%) | Nunn (99.8%) | Nunn +0.7 | 11:24 pm (98.6% in) |
| Iowa 2024 House 1 | IA-G-H-1-2024-11-05 | Miller-Meeks (74.0%) | Bohannan (87.7%) | Miller-Meeks (98.6%) | Miller-Meeks +0.2 | Wed 12:25 am (96.8% in) |
| Nebraska 2022 House 2 | NE-G-H-2-2022-11-08 | Vargas (67.4%) | Bacon (77.4%) | Bacon (93.4%) | Bacon +2.7 | 11:43 pm (67.5% in) |
| Nebraska 2024 House 2 | NE-G-H-2-2024-11-05 | Vargas (70.9%) | Vargas (76.4%) | Bacon (94.0%) | Bacon +1.9 | Wed 2:46 am (83.8% in) |
| Nebraska 2024 Initiative | NE-I-83085-NE-2024-11-05 | Against (50.1%) | For (61.4%) | For (96.1%) | For +9.9 | 11:00 pm (50.6% in) |
| Nebraska 2024 Initiative | NE-I-83084-NE-2024-11-05 | For (50.1%) | For (61.4%) | Against (96.1%) | Against +2.0 | Wed 1:26 am (79.6% in) |
| Nebraska 2024 President (district 1) | NE-G-P-CD_1-2024-11-05 | Harris (44.1%) | Trump (55.7%) | Trump (94.8%) | Trump +13.0 | 11:20 pm (52.7% in) |
| Nebraska 2024 Senate | NE-G-S-2024-11-05 | Osborn (50.1%) | Fischer (61.4%) | Fischer (96.1%) | Fischer +6.7 | 11:25 pm (57.1% in) |
| Nevada 2022 Secretary of State | NV-G-secretary_of_state-2022-11-08 | - (-%) | - (-%) | Marchant (82.3%) | Aguilar +2.3 | Nov 10 9:35 pm (87.9% in) |
| Nevada 2022 Senate | NV-G-S-2022-11-08 | - (-%) | - (-%) | Laxalt (82.2%) | Cortez Masto +0.8 | Nov 12 9:14 pm (96.9% in) |
| Nevada 2022 Treasurer | NV-G-treasurer-2022-11-08 | - (-%) | - (-%) | Fiore (82.3%) | Conine +1.7 | Nov 10 10:58 pm (89.7% in) |
| Nevada 2024 Senate | NV-G-S-2024-11-05 | - (-%) | - (-%) | Brown (86.6%) | Rosen +1.6 | Nov 7 2:47 am (92.4% in) |
| Oregon 2022 House 4 | OR-G-H-4-2022-11-08 | Hoyle (72.9%) | Skarlatos (32.7%) | Hoyle (85.1%) | Hoyle +7.5 | Wed 12:02 am (72.9% in) |
| Alaska 2022 Senate [RCV, 1st round] | AK-G-S-2022-11-08 | Tshibaka (55.8%) | - (-%) | Tshibaka (77.3%) | Murkowski +0.8 | Nov 18 10:08 pm (98.6% in) |
| Alaska 2024 Measure | AK-I-83139-AK-2024-11-05 | Yes (30.4%) | - (-%) | Yes (73.4%) | No +0.2 | Nov 18 7:01 pm (97.8% in) |

Patterns:
- **Kansas, Iowa, Ohio, Nebraska, Texas:** these reversals mostly ran Democrat → Republican and settled on election night,
  between about 9:40 and 11:45 pm ET.
  - The exception is Texas 2024 House 28, which ran Republican → Democrat (Cuellar, 10:34 pm).
- **Michigan and Georgia 2020:** the reversals ran Republican → Democrat and came **the next day**.
- **Iowa 2022 Auditor and 2024 House 1:** very close races traded the lead late at night.
- **Nebraska 2024 House 2:** the lead changed at 2:46 am.
- **Led at 6 am and lost (the new column):** Nevada's 2022 Senate, Secretary of State and Treasurer and 2024 Senate. In each, the Republican led when election night ended and the Democrat passed them on Nov 7-12 as late mail was counted. Also Michigan 2020 President and Senate and 2024 Senate, Georgia 2020 President, and Alaska 2022 Senate (first-choice count).

## 5. Races that moved after election night (1.5+ pts after 6 am ET)

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Alaska 2020 President | 36.8% | -26.7 | -10.1 | **+16.6** |
| Alaska 2020 Senate | 37.3% | -28.0 | -12.7 | **+15.3** |
| Michigan 2024 House 12 | 68.5% | +55.4 | +44.2 | **-11.2** |
| Nevada 2022 House 2 | 71.8% | -29.5 | -21.9 | **+7.5** |
| Michigan 2020 Senate | 80.1% | -5.6 | +1.7 | **+7.3** |
| Michigan 2020 President | 81.9% | -4.3 | +2.8 | **+7.1** |
| Iowa 2024 House 4 | 87.3% | -40.5 | -34.4 | **+6.1** |
| Michigan 2022 House 12 | 74.5% | +50.3 | +44.6 | **-5.7** |
| Michigan 2022 House 3 | 88.4% | +8.3 | +12.9 | **+4.6** |
| Michigan 2022 House 6 | 86.2% | +27.4 | +31.8 | **+4.4** |
| Michigan 2024 House 4 | 92.8% | -15.7 | -11.7 | **+4.0** |
| Nevada 2022 Attorney General | 83.5% | +4.3 | +7.9 | **+3.6** |
| Nevada 2022 Senate | 82.2% | -2.7 | +0.8 | **+3.5** |
| Michigan 2022 House 8 | 93.4% | +6.8 | +10.3 | **+3.5** |
| Nevada 2022 Secretary of State | 82.3% | -1.1 | +2.3 | **+3.4** |
| Maine 2020 President | 73.1% | +12.3 | +9.1 | **-3.2** |
| Nevada 2022 Governor | 82.2% | -4.7 | -1.5 | **+3.2** |
| Nevada 2022 Lieutenant Governor | 82.3% | -6.9 | -3.7 | **+3.2** |
| Nevada 2022 House 3 | 86.9% | +0.8 | +4.0 | **+3.2** |
| Alaska 2024 House 1 [RCV, 1st round] | 73.3% | -5.0 | -2.0 | **+2.9** |
| Nevada 2022 Controller | 82.4% | -7.0 | -4.1 | **+2.9** |
| Nevada 2024 House 2 | 83.2% | -21.9 | -19.0 | **+2.9** |
| Nevada 2022 Treasurer | 82.3% | -1.1 | +1.7 | **+2.8** |
| Michigan 2022 House 4 | 95.7% | -14.6 | -11.9 | **+2.7** |
| Nevada 2022 House 1 | 87.4% | +2.9 | +5.6 | **+2.7** |
| Maine 2020 Senate | 69.7% | -5.9 | -8.6 | **-2.7** |
| Maine 2024 House 1 | 71.4% | +24.8 | +22.3 | **-2.6** |
| Georgia 2020 President | 94.4% | -2.2 | +0.2 | **+2.4** |
| Oregon 2022 House 1 | 68.0% | +33.6 | +36.0 | **+2.4** |
| Oregon 2022 House 5 | 69.0% | -4.5 | -2.1 | **+2.4** |
| Oregon 2022 Governor | 73.4% | +1.1 | +3.4 | **+2.4** |
| Michigan 2022 Governor | 93.4% | +8.2 | +10.5 | **+2.3** |
| Michigan 2022 Secretary of State | 93.4% | +11.6 | +13.9 | **+2.3** |
| Michigan 2022 Attorney General | 93.5% | +6.3 | +8.6 | **+2.3** |
| Alaska 2022 House 1 [RCV, 1st round] | 77.3% | +20.7 | +23.0 | **+2.3** |
| Alaska 2024 President | 72.1% | -15.4 | -13.1 | **+2.2** |
| Texas 2022 House 8 | 94.8% | -39.7 | -37.5 | **+2.2** |
| Alaska 2022 Governor | 77.4% | -28.3 | -26.1 | **+2.2** |
| Texas 2022 House 14 | 97.5% | -38.1 | -40.3 | **-2.2** |
| Michigan 2022 House 10 | 96.1% | -2.6 | -0.5 | **+2.1** |
| Georgia 2020 Senate | 94.5% | -3.9 | -1.8 | **+2.1** |
| Maine 2024 President (district 1) | 71.3% | +23.9 | +21.8 | **-2.1** |
| Michigan 2024 House 10 | 92.3% | -8.1 | -6.1 | **+2.0** |
| Nevada 2024 House 3 | 90.1% | +0.8 | +2.7 | **+2.0** |
| Nevada 2024 House 1 | 90.6% | +5.6 | +7.5 | **+1.9** |
| Michigan 2022 House 7 | 96.9% | +3.5 | +5.4 | **+1.9** |
| Oregon 2024 Attorney General | 77.2% | +7.0 | +8.9 | **+1.9** |
| Maine 2024 President | 73.2% | +8.8 | +6.9 | **-1.8** |
| Oregon 2022 Senate | 73.5% | +13.1 | +14.9 | **+1.8** |
| Oregon 2024 President | 76.4% | +12.6 | +14.4 | **+1.8** |
| Nevada 2020 President | 84.9% | +0.6 | +2.4 | **+1.8** |
| Nebraska 2020 Senate | 84.6% | -40.1 | -38.3 | **+1.8** |
| Oregon 2024 Secretary of State | 77.1% | +10.8 | +12.6 | **+1.8** |
| Nebraska 2022 House 2 | 93.4% | -4.4 | -2.7 | **+1.7** |
| Nevada 2022 House 4 | 86.5% | +3.1 | +4.8 | **+1.7** |
| Nevada 2024 Senate | 86.6% | -0.1 | +1.6 | **+1.7** |
| Maine 2024 President (district 2) | 73.3% | -7.9 | -9.5 | **-1.6** |
| Nevada 2024 President | 86.5% | -4.7 | -3.1 | **+1.6** |
| Nebraska 2020 President | 92.1% | -17.5 | -19.1 | **-1.6** |
| Oregon 2020 President | 90.4% | +17.6 | +16.1 | **-1.5** |
| Oregon 2020 Senate | 90.6% | +19.1 | +17.6 | **-1.5** |

- **Alaska, Michigan and Nevada** show large, repeated post-election-night moves. Georgia 2020, Maine and Oregon 2022 show 2-3 pts. One isolated case: Iowa 2024 House 4 moved 6 pts in a race decided by 34.
- **Nevada moved toward Democrats after election night in every statewide race 2020-2024** (17 of 18 races; the exception is 2024 House 4, −1.1): 2022 Senate +3.5 (Cortez Masto went ahead on the Saturday), 2022 Governor +3.2 (Lombardo held on by 1.5), 2024 Senate +1.7, 2024 President +1.6, 2020 President +1.8.
- **Oregon's late count leaned Democratic in 2022 and 2024 (+1.8 to +2.4 in the top races) but Republican in 2020 (−1.5).**
- **Alaska's moves are toward Democrats** (mail ballots).
- **Maine's late moves are toward Republicans:** the last towns to report are small and rural.
- **Michigan 2024 House 12 (Detroit area)** moved 11 pts *less* Democratic after 6 am.
  The late Wayne County batch was not uniformly Democratic that year.

## 6. Why the early lead is misleading: early/mail vs Election Day votes

Margin among early/mail ("advance") votes minus margin among Election Day votes, from NYT's vote-type data. Only states and years where NYT tagged a full share of early votes are shown; Ohio and Michigan 2022 data covered just 2-14% of votes and are left out.

| State | Year | Races | Early/mail share of votes (median) | Early/mail margin minus Election Day margin (median, range) | Top-of-ticket example |
|---|---|---|---|---|---|
| Georgia | 2022 | 22 | 64% | +24.0 (+12 to +27) | Governor: early/mail +2.2, Election Day -25.0; Senate: early/mail +10.1, Election Day -15.4 |
| Georgia | 2024 | 15 | 76% | +4.4 (-4 to +14) | President: early/mail -0.7, Election Day -7.2 |
| Michigan | 2022 | 2 | 40% | +19.5 (+15 to +24) |  |
| Texas | 2024 | 33 | 80% | +0.4 (-10 to +19) | President: early/mail -13.2, Election Day -15.8; Senate: early/mail -9.3, Election Day -5.2 |
| Iowa | 2024 | 5 | 40% | +28.5 (+21 to +30) | President: early/mail +4.4, Election Day -25.4 |

- **Georgia 2022 and Iowa 2024 had 24-29-point gaps** between early and Election Day votes. With 40-64% of votes cast early and reported first, that produces the big early Democratic leads.
- **Georgia's gap fell to ~4 pts in 2024** as Republicans voted early. That's why Georgia 2024 barely moved.
- **Texas 2024 had no gap**: Allred did slightly *better* on Election Day. That's why Texas moves least.

## 7. Where the late vote comes from (2020 county detail)

Votes counted after midnight ET and after 6 am ET in 2020, how they split, and the counties they came from.
Computed from Internet Archive copies of NYT's county file, roughly hourly overnight; the snapshot used is shown.
The share still to count is measured against the certified total. The split and the counties cover what was counted by
the last archive copy (Nov 10, 3:15 pm ET), which holds 95-99.9% of the certified vote (Nevada 95%, Maine 96%, Ohio and
Kansas 97%). Alaska is left out: its last copy predates most of its count.

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Georgia | midnight ET | 20% | +38.2 | DeKalb 5.5% (+67); Fulton 5.0% (+46); Gwinnett 2.2% (+26); Cobb 2.0% (+18) | 12:00 AM |
| Georgia | 6 am ET | 6% | +42.7 | Fulton 1.6% (+56); DeKalb 1.0% (+70); Chatham 0.5% (+42); Houston 0.4% (+18) | 5:52 AM |
| Ohio | midnight ET | 5% | -7.7 | Lucas 0.7% (-5); Franklin 0.5% (+31); Cuyahoga 0.3% (+36); Tuscarawas 0.3% (-12) | 12:00 AM |
| Ohio | 6 am ET | 2% | - (counted after Nov 10, not in the archive) | - | 5:52 AM |
| Michigan | midnight ET | 50% | +15.7 | Wayne 10.8% (+48); Macomb 5.1% (+13); Oakland 4.9% (+27); Kent 2.6% (+31) | 12:00 AM |
| Michigan | 6 am ET | 18% | +35.0 | Wayne 7.3% (+58); Macomb 2.3% (+10); Oakland 1.9% (+26); Kent 1.4% (+50) | 5:52 AM |
| Texas | midnight ET | 9% | -7.2 | Harris 1.6% (+5); Fort Bend 1.0% (+5); Dallas 0.7% (+25); Travis 0.5% (+18) | 12:00 AM |
| Texas | 6 am ET | 1% | +23.4 | Webb 0.4% (+25); Tarrant 0.2% (+17); Hunt 0.1% (-49); Fort Bend 0.1% (+21) | 5:52 AM |
| Kansas | midnight ET | 20% | -23.2 | Douglas 4.2% (+39); Sedgwick 1.4% (+9); Finney 0.8% (-25); Geary 0.7% (-15) | 12:00 AM |
| Kansas | 6 am ET | 8% | -33.3 | Sedgwick 1.4% (+9); Lyon 0.5% (-37); Neosho 0.3% (-65); Johnson 0.3% (+12) | 5:52 AM |
| Maine | midnight ET | 58% | +13.5 | Cumberland 15.6% (+41); York 10.0% (+17); Penobscot 5.4% (-10); Kennebec 4.2% (+0) | 12:00 AM |
| Maine | 6 am ET | 27% | +2.5 | York 4.3% (+8); Cumberland 3.5% (+17); Penobscot 2.0% (-28); Sagadahoc 1.8% (+12) | 5:52 AM |
| Iowa | midnight ET | 14% | -25.8 | Story 3.0% (+17); Jasper 1.2% (-22); Pottawattamie 1.1% (-48); Wapello 0.6% (-29) | 12:00 AM |
| Iowa | 6 am ET | under 0.5% | - | - | 5:52 AM |
| Nebraska | midnight ET | 30% | -44.1 | Douglas 5.0% (-10); Lancaster 2.6% (-23); Scotts Bluff 1.6% (-44); Platte 1.6% (-56) | 12:00 AM |
| Nebraska | 6 am ET | 5% | -31.7 | Platte 1.6% (-56); Douglas 1.2% (+8); Sarpy 0.2% (-35); Dakota 0.1% (-45) | 5:52 AM |
| Nevada | midnight ET | 100% | +2.7 | Clark 64.9% (+10); Washoe 17.6% (+5); Douglas 2.4% (-29); Lyon 2.1% (-41) | 12:00 AM |
| Nevada | 6 am ET | 15% | +20.1 | Clark 8.1% (+27); Washoe 1.1% (+11); Douglas 0.4% (-31); Nye 0.2% (-37) | 5:52 AM |
| Oregon | midnight ET | 18% | +0.2 | Clackamas 3.7% (-11); Washington 3.5% (+20); Multnomah 2.8% (+47); Marion 1.4% (-14) | 12:00 AM |
| Oregon | 6 am ET | 9% | -0.9 | Clackamas 3.7% (-11); Washington 1.7% (+24); Marion 1.1% (-14); Deschutes 0.4% (-17) | 5:52 AM |

- **Michigan:**
  - Half the 2020 vote was counted after midnight, breaking Biden +16.
  - The 18% counted after 6 am went **Biden +35**, nearly all Wayne County (+58).
- **Georgia:** the 20% after midnight went Biden +38 (DeKalb +67, Fulton +46).
- **Maine:** the 58% after midnight went Biden +13.5 (Cumberland +41). But the last 27% after 6 am went only +2.5. Rural towns finish last, which is the late Republican move in section 5.
- **Kansas:**
  - After midnight it was mostly Douglas County (Lawrence, +39 Biden), which had reported nothing by midnight.
  - Rural counties outweighed it, so the late vote still went Trump +23.
- **Nebraska:** rural counties that hadn't reported (Platte, Scotts Bluff) made the post-midnight vote Trump +44. Omaha's (Douglas) late votes were slightly Republican that year.
- **Nevada:** almost nothing had posted by midnight ET (the first handful of votes came at 11:53 pm). The 15% still out at 6 am broke **Biden +20** (the part counted by Nov 10), mostly Clark County (+27). That is the multi-day late-mail tail.
- **Oregon:** the 18% counted after midnight split about evenly (+0.2), and the last 9% after 6 am leaned slightly Republican (−0.9; Clackamas and Marion). That matches Oregon's 2020 late move toward Republicans; 2022 and 2024 went the other way.

## 8. 2026 primaries, runoffs and specials (this year's rules)

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Georgia | 2026-03-10 | U.S. House | GA-S_T-H-14-2026-03-10 | 54.6 / 85.3 / 99.9 / 99.9 | Harris +2.5 | 1.9 | 7:35 pm (24.8%) |
| Georgia | 2026-04-07 | U.S. House | GA-S_NSR-H-14-2026-04-07 | 41.0 / 74.2 / 99.9 / 99.9 | Fuller +11.8 | 11.17 | 7:37 pm (27.5%) |
| Georgia | 2026-05-19 | Governor | GA-D-G-2026-05-19 | 23.9 / 43.2 / 97.6 / 99.8 | Bottoms +37.6 | 45.89 | 7:46 pm (18.4%) |
| Georgia | 2026-05-19 | U.S. House | GA-D-H-1-2026-05-19 | 33.7 / 55.4 / 99.9 / 99.9 | Griggs +9.8 | 11.98 | 7:46 pm (12.2%) |
| Georgia | 2026-05-19 | Supreme Court | GA-L-SC-justice_bethel_seat-2026-05-19 | 27.4 / 44.5 / 97.9 / 99.9 | Bethel +2.2 | 6.25 | 8:05 pm (27.9%) |
| Georgia | 2026-05-19 | Supreme Court | GA-L-SC-justice_warren_seat-2026-05-19 | 24.3 / 44.6 / 97.9 / 99.9 | Warren +18.6 | 22.52 | 7:44 pm (10.1%) |
| Georgia | 2026-05-19 | Governor | GA-R-G-2026-05-19 | 24.7 / 49.7 / 98.3 / 99.9 | Jones +5.8 | 2.71 | 7:37 pm (12.2%) |
| Georgia | 2026-05-19 | U.S. House | GA-R-H-1-2026-05-19 | 33.3 / 52.0 / 100.0 / 100.0 | Kingston +35.1 | 39.07 | 7:25 pm (13.9%) |
| Georgia | 2026-05-19 | U.S. Senate | GA-R-S-2026-05-19 | 26.2 / 49.7 / 98.3 / 99.9 | Collins +10.3 | 12.89 | 7:36 pm (12.5%) |
| Georgia | 2026-07-28 | U.S. House | GA-S_T-H-13-2026-07-28 | 49.1 / 92.6 / 99.9 / 99.9 | Scott +8.6 | 12.42 | 7:05 pm (10.7%) |
| Ohio | 2026-05-05 | Secretary of State | OH-D-SOS-2026-05-05 | 26.5 / 53.1 / 96.7 / 99.4 | Russo +34.8 | 36.6 | 8:03 pm (21.5%) |
| Ohio | 2026-05-05 | U.S. House | OH-R-H-9-2026-05-05 | 15.4 / 51.2 / 92.9 / 99.7 | Merrin +18.8 | 18.44 | 8:01 pm (13.7%) |
| Ohio | 2026-05-05 | Secretary of State | OH-R-SOS-2026-05-05 | 20.6 / 59.8 / 97.9 / 99.6 | Sprague +40.4 | 39.73 | 8:04 pm (14.7%) |
| Michigan | 2026-08-04 | U.S. House | MI-D-H-12-2026-08-04 | 1.1 / 15.0 / 40.5 / 94.2 | Tlaib +57.1 | 38.57 | 9:18 pm (13.6%) |
| Michigan | 2026-08-04 | U.S. House | MI-D-H-13-2026-08-04 | 2.4 / 5.6 / 47.9 / 93.0 | McKinney +3.8 | 26.21 | 11:33 pm (47.9%) |
| Michigan | 2026-08-04 | U.S. House | MI-D-H-7-2026-08-04 | 13.2 / 30.1 / 58.4 / 100.0 | Lawrence +14.9 | 5.95 | 8:42 pm (10.1%) |
| Michigan | 2026-08-04 | U.S. Senate | MI-D-S-2026-08-04 | 5.9 / 23.1 / 60.9 / 98.3 | El-Sayed +0.9 | 6.31 | 9:01 pm (15.2%) |
| Texas | 2026-03-03 | Comptroller | TX-D-COMP-2026-03-03 | 28.4 / 44.4 / 75.1 / 96.0 | Eckhardt +45.0 | 44.04 | 8:14 pm (11.0%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-18-2026-03-03 | 63.3 / 63.6 / 65.6 / 91.9 | Menefee +1.8 | 5.38 | 8:54 pm (63.3%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-23-2026-03-03 | 2.1 / 49.0 / 65.2 / 91.9 | Padilla Stout +24.9 | 36.49 | 9:20 pm (43.3%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-24-2026-03-03 | 44.8 / 44.8 / 72.7 / 95.7 | Burge +21.9 | 21.2 | 8:03 pm (43.8%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-33-2026-03-03 | - / - / 65.6 / 79.7 | Allred +10.8 | - | 10:30 pm (65.6%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-38-2026-03-03 | 59.5 / 59.5 / 59.5 / 90.9 | McDonough +23.4 | 21.95 | 8:55 pm (59.5%) |
| Texas | 2026-03-03 | U.S. House | TX-D-H-9-2026-03-03 | 54.8 / 59.4 / 61.1 / 96.4 | Gutierrez +37.4 | 33.88 | 8:43 pm (54.8%) |
| Texas | 2026-03-03 | U.S. Senate | TX-D-S-2026-03-03 | 37.4 / 48.8 / 73.2 / 95.7 | Talarico +6.2 | 7.29 | 8:40 pm (31.7%) |
| Texas | 2026-03-03 | Supreme Court | TX-D-SC-7-2026-03-03 | 26.3 / 42.3 / 72.9 / 95.6 | Hawkins +51.2 | 51.4 | 8:17 pm (11.8%) |
| Texas | 2026-03-03 | Supreme Court | TX-D-SC-chief_justice-2026-03-03 | 15.5 / 42.3 / 72.8 / 95.6 | Ellis +53.6 | 55.27 | 8:17 pm (11.7%) |
| Texas | 2026-03-03 | Comptroller | TX-R-COMP-2026-03-03 | 28.6 / 51.7 / 77.8 / 97.7 | Huffines +33.7 | 37.16 | 8:03 pm (10.5%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-18-2026-03-03 | 59.6 / 59.9 / 62.1 / 96.7 | Whitfield +10.2 | 9.75 | 8:17 pm (19.2%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-19-2026-03-03 | 37.4 / 58.0 / 79.6 / 99.8 | Sell +21.7 | 23.72 | 8:56 pm (37.3%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-2-2026-03-03 | 30.8 / 62.3 / 67.4 / 98.4 | Toth +15.1 | 18.37 | 8:41 pm (30.8%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-23-2026-03-03 | 3.4 / 55.9 / 73.7 / 98.5 | Herrera +1.6 **(comeback)** | -5.55 | Wed 2:26 am (87.1%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-33-2026-03-03 | 61.8 / 61.8 / 61.8 / 85.2 | Gillespie +13.2 | 12.53 | 8:01 pm (61.8%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-38-2026-03-03 | 63.6 / 63.6 / 63.6 / 95.5 | Bonck +28.0 | 30.71 | 8:55 pm (63.6%) |
| Texas | 2026-03-03 | U.S. House | TX-R-H-9-2026-03-03 | 43.8 / 65.5 / 72.6 / 99.2 | Mealer +4.6 | 6.44 | 8:58 pm (43.8%) |
| Texas | 2026-03-03 | U.S. Senate | TX-R-S-2026-03-03 | 36.7 / 52.7 / 79.8 / 97.8 | Cornyn +1.2 | 2.14 | 8:04 pm (10.3%) |
| Texas | 2026-05-26 | Attorney General | TX-democrat-AG-2026-05-26 | 52.8 / 67.3 / 84.8 / 99.5 | Johnson +21.0 | 19.05 | 8:05 pm (14.2%) |
| Texas | 2026-05-26 | U.S. House | TX-democrat-H-35-2026-05-26 | 54.5 / 54.5 / 83.7 / 91.9 | Garcia +27.7 | 18.49 | 8:27 pm (43.9%) |
| Texas | 2026-05-26 | Attorney General | TX-republican-AG-2026-05-26 | 57.3 / 72.7 / 92.4 / 99.7 | Middleton +10.5 | 11.48 | 8:05 pm (13.1%) |
| Texas | 2026-05-26 | U.S. House | TX-republican-H-35-2026-05-26 | 49.9 / 49.9 / 91.8 / 82.9 | De La Cruz +15.2 | 8.98 | 8:59 pm (49.9%) |
| Texas | 2026-05-26 | Railroad Commissioner | TX-republican-RR-term_exp_2032-2026-05-26 | 55.8 / 72.4 / 92.4 / 99.7 | French +1.1 | 3.16 | 8:09 pm (10.3%) |
| Texas | 2026-05-26 | U.S. Senate | TX-republican-S-2026-05-26 | 57.1 / 72.3 / 92.8 / 99.7 | Paxton +27.6 | 26.98 | 8:04 pm (11.3%) |
| Kansas | 2026-08-04 | Governor | KS-D-G-2026-08-04 | 36.3 / 59.1 / 91.8 / 97.4 | Holscher +10.1 | 6.98 | 8:18 pm (26.4%) |
| Kansas | 2026-08-04 | Governor | KS-R-G-2026-08-04 | 21.7 / 50.4 / 88.4 / 98.3 | Masterson +20.8 | 20.57 | 8:19 pm (10.6%) |
| Maine | 2026-06-09 | Governor | ME-D-G-2026-06-09 | 0.7 / 18.0 / 59.1 / 83.4 | Shah +3.7 (1st round) **- Pingree won the ranked-choice count** | 0.4 | 9:56 pm (16.9%) |
| Maine | 2026-06-09 | U.S. Senate | ME-D-S-2026-06-09 | 0.7 / 17.6 / 61.6 / 83.2 | Platner +52.9 | 54.43 | 9:35 pm (10.0%) |
| Maine | 2026-06-09 | Governor | ME-R-G-2026-06-09 | 1.4 / 16.7 / 56.2 / 77.6 | Charles +18.0 (1st round) | 22.24 | 9:43 pm (10.5%) |
| Iowa | 2026-06-02 | U.S. Senate | IA-D-S-2026-06-02 | 47.3 / 91.7 / 99.8 / 100.0 | Turek +25.3 | 25.03 | 9:20 pm (24.0%) |
| Iowa | 2026-06-02 | Governor | IA-R-G-2026-06-02 | 34.4 / 90.8 / 99.6 / 100.0 | Lahn +0.8 | 0.82 | 9:19 pm (12.5%) |
| Iowa | 2026-06-02 | U.S. Senate | IA-R-S-2026-06-02 | 33.7 / 92.7 / 99.5 / 99.9 | Hinson +48.4 | 49.2 | 9:19 pm (13.0%) |
| Nebraska | 2026-05-12 | U.S. House | NE-D-H-2-2026-05-12 | 64.1 / 70.0 / 87.0 / 88.8 | Powell +2.4 **(comeback)** | -0.71 | 11:46 pm (86.9%) |
| Oregon | 2026-05-19 | Governor | OR-D-G-2026-05-19 | 60.4 / 61.3 / 60.4 / 72.9 | Kotek +80.5 | 81.1 | 11:00 pm (49.3%) |
| Oregon | 2026-05-19 | U.S. House | OR-D-H-3-2026-05-19 | 61.3 / 61.9 / 61.3 / 73.1 | Dexter +80.9 | 83.67 | 11:00 pm (57.6%) |
| Oregon | 2026-05-19 | U.S. Senate | OR-D-S-2026-05-19 | 60.1 / 60.9 / 60.1 / 72.5 | Merkley +87.0 | 87.3 | 11:00 pm (49.2%) |
| Oregon | 2026-05-19 | Measure | OR-I-83580-OR-2026-05-19 | 60.3 / 61.3 / 60.3 / 73.0 | No +66.0 | 66.36 | 11:00 pm (45.8%) |
| Oregon | 2026-05-19 | Governor | OR-R-G-2026-05-19 | 61.9 / 63.2 / 61.9 / 75.3 | Drazan +7.5 | 10.84 | 11:00 pm (42.8%) |
| Oregon | 2026-05-19 | U.S. Senate | OR-R-S-2026-05-19 | 62.2 / 63.6 / 62.2 / 75.8 | Smith +2.4 | 3.59 | 11:00 pm (43.2%) |

What 2026 shows:
- **Fast states stayed fast.**
  - Georgia: about 98-100% counted by midnight.
  - Iowa: 91-93% counted **two hours** after close.
  - Ohio: 93-98% by midnight.
- **Kansas:** 88-92% by midnight.
- **Texas primaries were slower:** 73-80% by midnight in the March statewide primaries, 85-93% in the May runoffs. Primaries are run by the parties, so this may not carry over to November.
- **Michigan and Maine are still slow:** 40-62% by midnight.
- **Michigan's Senate primary:** El-Sayed led by 6.3 two hours in and won by 0.9. The late count narrowed it a lot.
- **Comebacks this year:**
  - Texas 23rd District Republican primary: Herrera took the lead for good at 2:26 am.
  - Nebraska 2nd District Democratic primary: Powell took the lead for good at 11:46 pm with 87% counted.
- **Maine's Democratic governor primary is a ranked-choice reversal:**
  - Shah led the first round 58,551 to 50,492.
  - Pingree won the ranked-choice count 111,750 to 86,950.
  - So a first-round lead in Maine is not safe when it's short of 50%.

## 9. What this suggests for the competitive Nov 3 races (inference)

These are rules of thumb drawn from the tables above, not forecasts.

| Race | What history suggests |
|---|---|
| **Kansas Senate** (Marshall R vs Hamilton D) | Expect Hamilton ahead early. A Hamilton lead under ~10-15 pts at 2 h (~10 pm ET) has historically been erased: Kelly's +20 became +2.2 in 2022. |
| **Iowa Senate** (Hinson R vs Turek D) | Ignore the first hour (Democratic absentee batches). By 11 pm ET ~75% is in. The margin moved only ~2 more pts in 2022/2024, but 19 in 2020, when only half was in by then. |
| **Nebraska Senate** (Ricketts R vs Osborn I) | Osborn led by 18 at 9 pm in 2024 and lost by 6.7. Expect a 7-9 pt move toward Ricketts after the first two hours. |
| **Ohio Governor and Senate** | Expect Acton/Brown leads at 7:30-9:30 pm to shrink 3-6 pts (11 in 2020) as Election Day votes come in. Almost nothing moves after midnight. |
| **Georgia Governor** | Since early votes now report by 8 pm, the 2024 pattern (little movement after 2 h) is the best guide. Down-ballot 2022 shows how big the early Democratic lead can look when the early vote is strongly D. |
| **Michigan Senate** | Expect the lead to change hands, possibly twice. The final answer may need Wayne County's late batch (Wednesday morning in 2024). |
| **Texas Senate** | The early-vote dump is most of the vote. The margin at 10 pm ET (2 h after close) has been within ~1-3.5 pts of the final (median). |
| **Maine Senate** | Expect Jackson to gain through the night (+5-8 after 2 h historically), then give back 0-3 pts as rural towns finish. If no one tops 50%, the ranked-choice count decides, and the first-round leader can lose. |
| **Alaska Senate** | Sullivan likely leads election night. Mail counted Nov 10-18 moved the margin 2-3 pts toward Democrats in 2022/2024 (16 in 2020). Then ranked-choice tabulation. |

## Reproduce

```
py "State election results/scripts/fetch_nyt_history.py"     # 2020-2024 top races
py "State election results/scripts/fetch_nyt_more.py"        # all 2022/2024 races, 2026 primaries
py "State election results/scripts/fetch_wayback_2020.py"    # 2020 county snapshots
py "State election results/scripts/swing_analysis.py"        # -> data/processed/swings.csv
py "State election results/scripts/build_swings_report.py"   # -> SWINGS.md
```
