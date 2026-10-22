# How far the count moves after polls close: eleven states, 2020-2026

*Built 2026-10-21 by `scripts/build_swings_report.py`; Nevada and Oregon added 2026-10-22. Every table is generated from NYT's
minute-by-minute results timelines ({{N_RACES}} races: {{N_GENERAL}} contested general-election races
2020-2024, plus 2026 primaries, runoffs and specials) and Internet Archive copies of NYT's 2020
county results. No number in a table was typed by hand.*

## How to read this

- **Margin** = Democrat (or independent) minus Republican, in points of all votes counted so far.
  In primaries, it's winner minus runner-up.
- **Move after 2 h** = final margin minus the margin 2 hours after the state's main poll close.
  - Positive: the count moved toward the Democrat/independent after that point.
  - Negative: toward the Republican.
- **Poll close used (ET):** GA 7:00, OH 7:30, MI/TX/KS/ME 8:00, IA/NE 9:00, NV 10:00, OR 11:00, AK midnight.
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

{{STATE_PACE}}

## 3. The biggest moves in competitive races (final margin within 15 pts)

Up to five per state, largest move after 2 h first.

{{BIG_SWINGS}}

What stands out:
- **Georgia 2022:** five statewide Democrats led by 11-15 pts two hours after close (16% counted) and lost by 5-8.
  The early vote was Democratic; Election Day was not (section 6).
- **Kansas 2022:** the Democratic Attorney General candidate led by 18 two hours in and lost by 1.7. Governor Kelly's +20 shrank to a 2.2 win.
- **Michigan:** swings go both ways depending on which big county reports when.
  - 2022 House 7 (Slotkin) was −15.5 at two hours and won by 5.4.
  - 2024 House 3 was +36 at two hours and won by 10.
- **Iowa 2020:** Biden +12 and Greenfield +10 at about half counted; they lost by 8.2 and 6.6.

## 4. Every race where the leader at 2 hours or at midnight lost

General elections only. "Ahead for good" is when the eventual winner took the lead and never gave it back (10%+ counted).

{{COMEBACKS}}

Patterns:
- **Kansas, Iowa, Ohio, Nebraska, Texas:** these reversals mostly ran Democrat → Republican and settled on election night,
  between about 9:40 and 11:45 pm ET.
  - The exception is Texas 2024 House 28, which ran Republican → Democrat (Cuellar, 10:34 pm).
- **Michigan and Georgia 2020:** the reversals ran Republican → Democrat and came **the next day**.
- **Iowa 2022 Auditor and 2024 House 1:** very close races traded the lead late at night.
- **Nebraska 2024 House 2:** the lead changed at 2:46 am.

## 5. Races that moved after election night (1.5+ pts after 6 am ET)

{{LATE_MOVERS}}

- **Alaska, Michigan and Nevada** show large, repeated post-election-night moves. Georgia 2020, Maine and Oregon 2022 show 2-3 pts. One isolated case: Iowa 2024 House 4 moved 6 pts in a race decided by 34.
- **Nevada moved toward Democrats after election night in every statewide race 2020-2024** (17 of 18 races; the exception is 2024 House 4, −1.1): 2022 Senate +3.5 (Cortez Masto went ahead on the Saturday), 2022 Governor +3.2 (Lombardo held on by 1.5), 2024 Senate +1.7, 2024 President +1.6, 2020 President +1.8.
- **Oregon's late count leaned Democratic in 2022 and 2024 (+1.8 to +2.4 in the top races) but Republican in 2020 (−1.5).**
- **Alaska's moves are toward Democrats** (mail ballots).
- **Maine's late moves are toward Republicans:** the last towns to report are small and rural.
- **Michigan 2024 House 12 (Detroit area)** moved 11 pts *less* Democratic after 6 am.
  The late Wayne County batch was not uniformly Democratic that year.

## 6. Why the early lead is misleading: early/mail vs Election Day votes

Margin among early/mail ("advance") votes minus margin among Election Day votes, from NYT's vote-type data. Only states and years where NYT tagged a full share of early votes are shown; Ohio and Michigan 2022 data covered just 2-14% of votes and are left out.

{{EARLY_EDAY}}

- **Georgia 2022 and Iowa 2024 had 24-29-point gaps** between early and Election Day votes. With 40-64% of votes cast early and reported first, that produces the big early Democratic leads.
- **Georgia's gap fell to ~4 pts in 2024** as Republicans voted early. That's why Georgia 2024 barely moved.
- **Texas 2024 had no gap**: Allred did slightly *better* on Election Day. That's why Texas moves least.

## 7. Where the late vote comes from (2020 county detail)

Votes counted after midnight ET and after 6 am ET in 2020, how they split, and the counties they came from.
Computed from Internet Archive copies of NYT's county file, roughly hourly overnight; the snapshot used is shown.

{{COUNTY_2020}}

- **Michigan:**
  - Half the 2020 vote was counted after midnight, breaking Biden +16.
  - The 18% counted after 6 am went **Biden +35**, nearly all Wayne County (+58).
- **Georgia:** the 20% after midnight went Biden +38 (DeKalb +67, Fulton +46).
- **Maine:** the 57% after midnight went Biden +13.5 (Cumberland +41). But the last 24% after 6 am went only +2.5. Rural towns finish last, which is the late Republican move in section 5.
- **Kansas:**
  - After midnight it was mostly Douglas County (Lawrence, +39 Biden), which had reported nothing by midnight.
  - Rural counties outweighed it, so the late vote still went Trump +23.
- **Nebraska:** rural counties that hadn't reported (Platte, Scotts Bluff) made the post-midnight vote Trump +44. Omaha's (Douglas) late votes were slightly Republican that year.
- **Nevada:** almost nothing had posted by midnight ET (the first handful of votes came at 11:53 pm). The 11% still out at 6 am broke **Biden +20**, mostly Clark County (+27). That is the multi-day late-mail tail.
- **Oregon:** the 16% counted after midnight split about evenly (+0.2), and the last 8% after 6 am leaned slightly Republican (−0.9; Clackamas and Marion). That matches Oregon's 2020 late move toward Republicans; 2022 and 2024 went the other way.

## 8. 2026 primaries, runoffs and specials (this year's rules)

{{PRIMARIES_2026}}

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
