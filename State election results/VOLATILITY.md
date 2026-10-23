# Which states' counts swing the most: every state, 2020-2024

*Built by `scripts/volatility.py` from NYT's minute-by-minute statewide results timelines for every
President, Senate and Governor general election from 2020 to 2024: 255 races in the 50 states and DC.
Every table is generated from that data; no number in a table was typed. Bold states are the eleven
with a competitive 2026 race in this project.*

## Bottom line

- **The most volatile states, overall, are Kansas, Nebraska, Virginia, Michigan, Iowa, Rhode Island, Texas,
  Ohio, North Carolina and Georgia.** "Overall" weighs two things equally: how far the visible margin moves
  while votes are counted, and how often the leader at some point during the count went on to lose.
- **Seven of our eleven competitive states are in the national top ten:** Kansas (1), Nebraska (2),
  Michigan (4), Iowa (5), Texas (7), Ohio (8) and Georgia (10). Nevada is 17th, Alaska 19th, Oregon 33rd and
  Maine 37th (table below).
- **Volatility comes in two shapes, and they call for opposite reads:**
  1. **A big early lead that fades.** In Kansas, Nebraska, Iowa, Ohio, Texas and New York, *every* race
     moved toward the Republican after the first quarter of the vote was counted, typically by 15-30 points.
     Early and mail votes report first and lean Democratic. The direction is reliable, so the early lead
     should be discounted, not believed.
  2. **A late shift that decides close races.** After election night (6 am ET), the count moved toward the
     Democrat in every race in **Nevada** (+1.6 to +3.5), **Michigan** (+0.6 to +7.3) and **Pennsylvania**
     (+0.7 to +12.7). Alaska moved +2 to +17 as its mail ballots were counted. These moves are smaller than the
     early fades but come when the race is close, so they flip leads. Arizona is the mirror image: its late count
     moved toward the Republican in every race.
- **Reversals cluster where both happen in close races.** The leader at 25%, 50% or 75% counted, or at 6 am ET,
  lost in all 5 Iowa races and in 4 of 5 in Kansas, Nebraska, Texas and Ohio.
  Michigan, Georgia, Pennsylvania, Nevada and Wisconsin each had 3 of 5, and Virginia 3 of 4. Wisconsin is the
  clearest case of small swings in very close races: its typical move is 3 points or less, yet in 3 of 5 races a checkpoint leader lost.
- **Rules changed after 2020, the record mail year.** Michigan now processes absentees before Election Day,
  and its 2024 swings were small. Georgia must report early votes by 8 pm. Ohio ended its mail grace period.
  Pennsylvania and Wisconsin still can't process mail before Election Day. Expect the shapes, not the exact sizes.

## How it's measured

For each race, the margin is the Democrat (or the top non-Republican) minus the Republican, in points of the
votes counted so far; a positive move means the count moved toward the Democrat.

| Measure | Definition |
|---|---|
| Move after 25% / 50% / 75% counted | Final margin minus the margin at the first update with at least that share counted. A big first batch can already be past 25% (Texas, Iowa and Oregon often post half or more at once). |
| Move after election night | Final margin minus the margin at 6 am ET the next morning |
| Leader lost | The race's leader at 25%, 50% or 75% counted, or at 6 am ET, lost |
| Lead changes | Changes of leader after 10% was counted; flips that reverse within 10 minutes are ignored |
| Biggest gap | Largest distance between the running margin and the final, once 25% was counted |

**Score.**
- **Size:** the average of the state's percentile ranks on the median size of its four moves.
- **Reversals:** the state's percentile rank on the share of its races whose leader at a checkpoint lost.
- **Overall:** the average of size and reversals. Ties share the middle of their range.

## The 15 most volatile states

| Rank | State | Score (size / reversals) | Races | Typical move after 25% counted | after 50% | after 75% | after election night (6 am ET) | Direction after 25% (+ = toward D) | Races whose leader at 25/50/75% or 6 am lost | Races with a lead change | Counted by 6 am ET | Biggest gap (race, pts) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Kansas** | 87 (79 / 94) | 5 | 22.1 | 12.3 | 4.2 | 0.6 | -22.1 | 4 | 4 | 96% | 2022 Senate (28) |
| 2 | **Nebraska** | 85 (76 / 94) | 5 | 24.8 | 12.2 | 2.0 | 1.4 | -24.8 | 4 | 4 | 96% | 2024 President (37) |
| 3 | Virginia | 83 (77 / 89) | 4 | 14.1 | 12.1 | 4.8 | 0.8 | +13.2 | 3 | 3 | 96% | 2020 President (29) |
| 4 | **Michigan** | 79 (74 / 83) | 5 | 6.7 | 7.2 | 5.4 | 2.3 | +6.7 | 3 | 4 | 93% | 2020 Senate (16) |
| 5 | **Iowa** | 78 (57 / 99) | 5 | 25.9 | 8.7 | 1.7 | 0.0 | -25.9 | 5 | 5 | 100% | 2022 Governor (28) |
| 6 | Rhode Island | 75 (75 / 75) | 5 | 18.7 | 8.8 | 4.1 | 0.8 | +18.7 | 2 | 2 | 97% | 2020 President (31) |
| 7 | **Texas** | 74 (54 / 94) | 5 | 18.6 | 6.7 | 0.9 | 0.4 | -18.6 | 4 | 5 | 99% | 2020 President (20) |
| 8 | **Ohio** | 71 (48 / 94) | 5 | 19.9 | 3.5 | 1.9 | 0.2 | -19.9 | 4 | 4 | 98% | 2020 President (30) |
| 9 | North Carolina | 71 (64 / 77) | 6 | 10.2 | 11.3 | 4.3 | 0.1 | -10.2 | 3 | 4 | 99% | 2022 Senate (27) |
| 10 | **Georgia** | 70 (57 / 83) | 5 | 15.2 | 8.5 | 2.6 | 0.1 | +8.0 | 3 | 3 | 100% | 2020 President (18) |
| 11 | Montana | 70 (68 / 72) | 6 | 9.6 | 5.7 | 3.8 | 2.6 | -9.6 | 2 | 3 | 81% | 2020 Senate (19) |
| 12 | Idaho | 69 (64 / 75) | 5 | 15.3 | 5.4 | 2.3 | 1.5 | -15.3 | 2 | 3 | 90% | 2020 President (35) |
| 13 | Pennsylvania | 67 (51 / 83) | 5 | 8.9 | 0.5 | 3.9 | 1.9 | -8.9 | 3 | 3 | 96% | 2020 President (17) |
| 14 | Minnesota | 65 (64 / 66) | 5 | 23.1 | 5.8 | 4.1 | 0.1 | -23.1 | 1 | 2 | 100% | 2022 Governor (30) |
| 15 | Arizona | 60 (54 / 66) | 5 | 10.3 | 11.0 | 0.3 | 1.2 | -10.3 | 1 | 1 | 68% | 2022 Senate (14) |

## Our eleven competitive states, by national rank

| Rank | State | Score (size / reversals) | Races | Typical move after 25% counted | after 50% | after 75% | after election night (6 am ET) | Direction after 25% (+ = toward D) | Races whose leader at 25/50/75% or 6 am lost | Races with a lead change | Counted by 6 am ET | Biggest gap (race, pts) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Kansas** | 87 (79 / 94) | 5 | 22.1 | 12.3 | 4.2 | 0.6 | -22.1 | 4 | 4 | 96% | 2022 Senate (28) |
| 2 | **Nebraska** | 85 (76 / 94) | 5 | 24.8 | 12.2 | 2.0 | 1.4 | -24.8 | 4 | 4 | 96% | 2024 President (37) |
| 4 | **Michigan** | 79 (74 / 83) | 5 | 6.7 | 7.2 | 5.4 | 2.3 | +6.7 | 3 | 4 | 93% | 2020 Senate (16) |
| 5 | **Iowa** | 78 (57 / 99) | 5 | 25.9 | 8.7 | 1.7 | 0.0 | -25.9 | 5 | 5 | 100% | 2022 Governor (28) |
| 7 | **Texas** | 74 (54 / 94) | 5 | 18.6 | 6.7 | 0.9 | 0.4 | -18.6 | 4 | 5 | 99% | 2020 President (20) |
| 8 | **Ohio** | 71 (48 / 94) | 5 | 19.9 | 3.5 | 1.9 | 0.2 | -19.9 | 4 | 4 | 98% | 2020 President (30) |
| 10 | **Georgia** | 70 (57 / 83) | 5 | 15.2 | 8.5 | 2.6 | 0.1 | +8.0 | 3 | 3 | 100% | 2020 President (18) |
| 17 | **Nevada** | 58 (33 / 83) | 5 | 2.3 | 2.3 | 1.3 | 1.8 | -2.3 | 3 | 3 | 85% | 2022 Governor (12) |
| 19 | **Alaska** | 57 (85 / 28) | 4 | 9.8 | 11.7 | 5.2 | 8.8 | +9.8 | 0 | 0 | 55% | 2020 President (20) |
| 33 | **Oregon** | 40 (52 / 28) | 5 | 6.7 | 4.5 | 1.9 | 1.8 | -6.7 | 0 | 0 | 76% | 2020 Senate (23) |
| 37 | **Maine** | 38 (48 / 28) | 5 | 4.8 | 3.4 | 2.4 | 1.9 | +4.8 | 0 | 2 | 73% | 2020 President (9) |

- **Kansas, Nebraska, Iowa, Ohio, Texas:** the early-lead-fades shape, every race. Election night settles them, so the swing
  plays out in two or three hours.
- **Michigan:** both shapes. In 2020 it moved +16 toward the Democrat after the first quarter and another +7 after 6 am.
  In 2024, with early processing allowed, the first quarter was already close to the final, but the count still moved
  about 5 points toward the Democrat after half was in (Wayne County reports late).
- **Georgia:** the direction has flipped by year: toward the Democrat in 2020 and 2024's President race, toward the Republican in 2022.
  Since 2024 the 8 pm early-vote rule front-loads the count.
- **Nevada:** small moves (about 2 points) but always the same way after election night, toward the Democrat, and enough to change the
  leader in 3 of 5 races (`STATE_BY_STATE.md` section 11).
- **Alaska:** the largest late moves in the country in 2020 (+15 to +17 after 6 am ET), when most of the vote was counted after
  election night. No statewide leader lost in these years, though.
- **Oregon and Maine:** below the national median. Oregon's first release is most of the vote; Maine's town-by-town count moves a few
  points toward the non-Republican, without changing the leader in these races.

## The biggest single-race swings (races decided by 10 points or less)

| Race | Final margin | Biggest gap after 25% counted | Move after 25% | after 50% | after 75% | after 6 am ET | Lead changes | A checkpoint leader lost |
|---|---|---|---|---|---|---|---|---|
| Ohio 2020 President | -8.0 | **29.9** | -29.9 | -19.8 | -5.1 | +0.1 | 1 | yes |
| Minnesota 2022 Governor | +7.7 | **29.7** | -29.7 | -10.4 | -4.1 | -0.1 | 0 | no |
| Minnesota 2020 President | +7.1 | **27.1** | -27.1 | -6.7 | -5.3 | -0.1 | 0 | no |
| North Carolina 2022 Senate | -3.2 | **26.8** | -22.5 | -14.4 | -1.6 | +0.4 | 1 | yes |
| Iowa 2020 President | -8.2 | **26.3** | -26.3 | -18.3 | -6.1 | -0.9 | 1 | yes |
| Nebraska 2024 Senate | -6.7 | **24.8** | -24.8 | -8.2 | -2.0 | +0.9 | 1 | yes |
| New York 2022 Governor | +6.4 | **24.2** | -24.2 | -12.0 | -3.9 | +0.9 | 0 | no |
| Iowa 2020 Senate | -6.6 | **24.1** | -24.1 | -16.4 | -3.5 | +0.0 | 1 | yes |
| Minnesota 2020 Senate | +5.2 | **23.1** | -23.1 | -5.8 | -4.9 | -0.1 | 0 | no |
| Texas 2020 President | -5.6 | **20.0** | -20.0 | -6.7 | -5.4 | +0.5 | 1 | yes |
| Ohio 2022 Senate | -6.1 | **19.9** | -19.9 | -3.3 | +1.0 | +0.5 | 1 | yes |
| Texas 2020 Senate | -9.6 | **18.9** | -18.9 | -5.7 | -5.0 | +0.4 | 1 | yes |
| Georgia 2020 President | +0.2 | **17.7** | +14.8 | +14.9 | +8.2 | +2.4 | 2 | yes |
| Minnesota 2024 President | +4.3 | **17.4** | +17.4 | -5.8 | +0.8 | -0.2 | 1 | yes |
| Georgia 2022 Governor | -7.5 | **17.4** | -17.3 | -2.4 | +0.2 | +0.0 | 1 | yes |
| Georgia 2020 Senate | -1.8 | **17.3** | +15.2 | +13.7 | +7.5 | +2.1 | 0 | no |
| Pennsylvania 2020 President | +1.2 | **16.7** | +8.5 | +16.0 | +14.5 | +12.7 | 2 | yes |
| Georgia 2022 Senate | +1.0 | **16.7** | -16.7 | -1.7 | +1.0 | +0.1 | 2 | yes |
| Michigan 2020 Senate | +1.7 | **16.2** | +16.2 | +13.0 | +8.7 | +7.3 | 3 | yes |
| New Mexico 2024 President | +6.0 | **16.0** | +16.0 | -3.2 | +0.3 | +0.4 | 3 | yes |
| Michigan 2020 President | +2.8 | **15.7** | +15.7 | +13.4 | +9.1 | +7.1 | 1 | yes |
| North Carolina 2020 President | -1.4 | **14.8** | -14.8 | -14.1 | -6.2 | +0.1 | 1 | yes |
| Pennsylvania 2024 Senate | -0.2 | **14.3** | -13.6 | -0.1 | +1.3 | +0.8 | 1 | yes |
| North Carolina 2020 Governor | +4.5 | **13.8** | -13.8 | -13.1 | -5.8 | +0.1 | 0 | no |
| Pennsylvania 2024 President | -1.7 | **13.7** | -13.7 | +0.4 | +1.5 | +0.7 | 1 | yes |

## The biggest moves after election night (6 am ET to the final count)

| Race | Counted by 6 am ET | Final margin | Move after 6 am ET | 6 am leader lost |
|---|---|---|---|---|
| Alaska 2020 President | 36.8% | -10.1 | **+16.6** | no |
| Alaska 2020 Senate | 37.3% | -12.7 | **+15.3** | no |
| Pennsylvania 2020 President | 77.5% | +1.2 | **+12.7** | yes |
| Maryland 2022 Senate | 75.8% | +31.7 | **+10.1** | no |
| Maryland 2022 Governor | 75.9% | +32.5 | **+9.8** | no |
| Mississippi 2020 President | 66.7% | -16.5 | **+8.8** | no |
| Mississippi 2020 Senate | 66.6% | -10.0 | **+8.2** | no |
| Michigan 2020 Senate | 80.1% | +1.7 | **+7.3** | yes |
| New Jersey 2020 President | 63.5% | +15.9 | **-7.1** | no |
| Michigan 2020 President | 81.9% | +2.8 | **+7.1** | yes |
| New Jersey 2020 Senate | 63.8% | +16.3 | **-6.4** | no |
| Maryland 2024 President | 81.9% | +28.8 | **+5.9** | no |
| Maryland 2020 President | 68.4% | +33.2 | **+5.5** | no |
| Washington 2020 Governor | 81.5% | +13.4 | **-5.5** | no |
| New York 2020 President | 82.2% | +23.1 | **+5.4** | no |
| Indiana 2020 President | 85.3% | -16.1 | **+5.0** | no |
| Washington 2020 President | 81.3% | +19.2 | **-5.0** | no |
| Maryland 2024 Senate | 81.9% | +11.8 | **+4.9** | no |
| Arizona 2020 President | 77.9% | +0.3 | **-4.7** | no |
| South Dakota 2020 President | 90.3% | -26.2 | **+4.5** | no |
| South Dakota 2020 Senate | 90.3% | -31.5 | **+4.5** | no |
| Connecticut 2024 President | 80.9% | +14.5 | **+4.3** | no |
| Connecticut 2024 Senate | 81.1% | +18.9 | **+4.1** | no |
| Utah 2022 Senate | 67.2% | -10.4 | **+4.0** | no |
| Indiana 2020 Governor | 75.1% | -24.5 | **+3.8** | no |

- **Alaska 2020** counted most of its vote after election night.
- **Pennsylvania 2020** is the classic "red mirage": Trump led by 11.5 points with 78% counted at 6 am ET, and Biden won by 1.2.
- **Maryland** counts a large share of its mail ballots after Election Day. In 2022 they moved both statewide races about 10 points toward the Democrat.
- **New Jersey 2020** went the other way: its late-counted ballots were less Democratic than the early mail.

## Caveats

- Only 2020-2024, and only President, Senate and Governor: 4-7 races per state, so a state's typical move is the median of a few races.
- NYT's 2024 **presidential** timelines stop at 5:40 am ET on the Wednesday. For that race, "after election night" runs from the last point
  before 6 am. Senate and Governor timelines run to certification.
- **Left out:**
  - three 2020 Senate races whose NYT timelines record only one candidate's vote share, or none (Massachusetts, New Mexico, West Virginia);
  - races with two candidates of the same party in the top two (California top-two, Alaska 2022 Senate).
- Ranked-choice races (Alaska, Maine) are measured on first-round votes.
- 2020 was a record mail year, so its late swings in Michigan, Pennsylvania, Wisconsin and Georgia were larger than in 2022 and 2024.

## All states

| Rank | State | Score (size / reversals) | Races | Typical move after 25% counted | after 50% | after 75% | after election night (6 am ET) | Direction after 25% (+ = toward D) | Races whose leader at 25/50/75% or 6 am lost | Races with a lead change | Counted by 6 am ET | Biggest gap (race, pts) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Kansas** | 87 (79 / 94) | 5 | 22.1 | 12.3 | 4.2 | 0.6 | -22.1 | 4 | 4 | 96% | 2022 Senate (28) |
| 2 | **Nebraska** | 85 (76 / 94) | 5 | 24.8 | 12.2 | 2.0 | 1.4 | -24.8 | 4 | 4 | 96% | 2024 President (37) |
| 3 | Virginia | 83 (77 / 89) | 4 | 14.1 | 12.1 | 4.8 | 0.8 | +13.2 | 3 | 3 | 96% | 2020 President (29) |
| 4 | **Michigan** | 79 (74 / 83) | 5 | 6.7 | 7.2 | 5.4 | 2.3 | +6.7 | 3 | 4 | 93% | 2020 Senate (16) |
| 5 | **Iowa** | 78 (57 / 99) | 5 | 25.9 | 8.7 | 1.7 | 0.0 | -25.9 | 5 | 5 | 100% | 2022 Governor (28) |
| 6 | Rhode Island | 75 (75 / 75) | 5 | 18.7 | 8.8 | 4.1 | 0.8 | +18.7 | 2 | 2 | 97% | 2020 President (31) |
| 7 | **Texas** | 74 (54 / 94) | 5 | 18.6 | 6.7 | 0.9 | 0.4 | -18.6 | 4 | 5 | 99% | 2020 President (20) |
| 8 | **Ohio** | 71 (48 / 94) | 5 | 19.9 | 3.5 | 1.9 | 0.2 | -19.9 | 4 | 4 | 98% | 2020 President (30) |
| 9 | North Carolina | 71 (64 / 77) | 6 | 10.2 | 11.3 | 4.3 | 0.1 | -10.2 | 3 | 4 | 99% | 2022 Senate (27) |
| 10 | **Georgia** | 70 (57 / 83) | 5 | 15.2 | 8.5 | 2.6 | 0.1 | +8.0 | 3 | 3 | 100% | 2020 President (18) |
| 11 | Montana | 70 (68 / 72) | 6 | 9.6 | 5.7 | 3.8 | 2.6 | -9.6 | 2 | 3 | 81% | 2020 Senate (19) |
| 12 | Idaho | 69 (64 / 75) | 5 | 15.3 | 5.4 | 2.3 | 1.5 | -15.3 | 2 | 3 | 90% | 2020 President (35) |
| 13 | Pennsylvania | 67 (51 / 83) | 5 | 8.9 | 0.5 | 3.9 | 1.9 | -8.9 | 3 | 3 | 96% | 2020 President (17) |
| 14 | Minnesota | 65 (64 / 66) | 5 | 23.1 | 5.8 | 4.1 | 0.1 | -23.1 | 1 | 2 | 100% | 2022 Governor (30) |
| 15 | Arizona | 60 (54 / 66) | 5 | 10.3 | 11.0 | 0.3 | 1.2 | -10.3 | 1 | 1 | 68% | 2022 Senate (14) |
| 16 | Florida | 60 (54 / 66) | 5 | 9.1 | 5.7 | 5.0 | 0.0 | -9.1 | 1 | 3 | 100% | 2022 Governor (17) |
| 17 | **Nevada** | 58 (33 / 83) | 5 | 2.3 | 2.3 | 1.3 | 1.8 | -2.3 | 3 | 3 | 85% | 2022 Governor (12) |
| 18 | Wisconsin | 58 (32 / 83) | 5 | 0.8 | 3.1 | 3.0 | 0.2 | -0.2 | 3 | 4 | 99% | 2022 Senate (8) |
| 19 | **Alaska** | 57 (85 / 28) | 4 | 9.8 | 11.7 | 5.2 | 8.8 | +9.8 | 0 | 0 | 55% | 2020 President (20) |
| 20 | Washington | 56 (52 / 60) | 6 | 10.0 | 3.8 | 2.1 | 1.4 | -0.4 | 1 | 1 | 67% | 2024 Senate (16) |
| 21 | New York | 55 (81 / 28) | 5 | 22.7 | 12.3 | 3.0 | 1.7 | -22.7 | 0 | 0 | 91% | 2022 Governor (24) |
| 22 | Utah | 54 (48 / 60) | 6 | 14.3 | 3.5 | 0.9 | 1.0 | -13.0 | 1 | 1 | 66% | 2020 President (31) |
| 23 | New Mexico | 53 (37 / 70) | 4 | 13.0 | 2.3 | 0.7 | 0.4 | -4.0 | 1 | 2 | 99% | 2024 President (16) |
| 24 | Maryland | 45 (61 / 28) | 5 | 6.2 | 1.7 | 6.1 | 5.9 | -6.2 | 0 | 0 | 76% | 2020 President (14) |
| 25 | South Dakota | 44 (60 / 28) | 5 | 4.3 | 4.9 | 4.0 | 3.6 | +4.3 | 0 | 0 | 90% | 2020 President (9) |
| 26 | Missouri | 44 (59 / 28) | 6 | 11.3 | 6.2 | 4.2 | 0.1 | -11.3 | 0 | 6 | 99% | 2024 Governor (14) |
| 27 | Connecticut | 44 (59 / 28) | 5 | 4.4 | 5.8 | 4.1 | 1.5 | +4.4 | 0 | 0 | 87% | 2020 President (9) |
| 28 | Delaware | 43 (26 / 60) | 6 | 12.1 | 0.7 | 0.1 | 0.2 | +0.1 | 1 | 2 | 99% | 2020 Senate (23) |
| 29 | Illinois | 43 (57 / 28) | 5 | 6.8 | 6.6 | 1.6 | 2.3 | -6.8 | 0 | 0 | 93% | 2022 Governor (11) |
| 30 | Hawaii | 42 (57 / 28) | 5 | 4.4 | 4.4 | 3.1 | 2.6 | -4.4 | 0 | 0 | 86% | 2022 Governor (8) |
| 31 | Louisiana | 42 (56 / 28) | 3 | 4.9 | 9.8 | 8.2 | 0.0 | +4.9 | 0 | 0 | 100% | 2024 President (19) |
| 32 | Mississippi | 42 (55 / 28) | 4 | 2.4 | 5.4 | 2.8 | 4.4 | +2.4 | 0 | 0 | 77% | 2020 President (9) |
| 33 | **Oregon** | 40 (52 / 28) | 5 | 6.7 | 4.5 | 1.9 | 1.8 | -6.7 | 0 | 0 | 76% | 2020 Senate (23) |
| 34 | Tennessee | 40 (52 / 28) | 5 | 16.3 | 5.5 | 1.6 | 0.2 | +16.3 | 0 | 0 | 100% | 2024 President (21) |
| 35 | Kentucky | 39 (49 / 28) | 4 | 1.7 | 7.4 | 2.8 | 0.9 | -1.7 | 0 | 2 | 98% | 2022 Senate (21) |
| 36 | New Jersey | 39 (49 / 28) | 4 | 4.4 | 4.3 | 1.4 | 3.7 | -4.4 | 0 | 2 | 79% | 2024 President (8) |
| 37 | **Maine** | 38 (48 / 28) | 5 | 4.8 | 3.4 | 2.4 | 1.9 | +4.8 | 0 | 2 | 73% | 2020 President (9) |
| 38 | Colorado | 37 (46 / 28) | 5 | 13.7 | 2.3 | 2.1 | 0.6 | -13.7 | 0 | 0 | 79% | 2022 Governor (16) |
| 39 | Arkansas | 35 (42 / 28) | 5 | 11.5 | 6.5 | 0.3 | 0.2 | -11.5 | 0 | 2 | 99% | 2022 Senate (16) |
| 40 | California | 33 (38 / 28) | 6 | 3.7 | 3.3 | 0.8 | 3.0 | -3.1 | 0 | 0 | 55% | 2020 President (16) |
| 41 | Alabama | 33 (37 / 28) | 5 | 5.3 | 2.2 | 4.7 | 0.0 | +3.8 | 0 | 0 | 99% | 2024 President (9) |
| 42 | Oklahoma | 32 (36 / 28) | 5 | 12.0 | 2.3 | 2.6 | 0.0 | -12.0 | 0 | 1 | 100% | 2020 President (25) |
| 43 | Indiana | 31 (33 / 28) | 6 | 6.3 | 1.1 | 1.6 | 0.9 | +6.3 | 0 | 0 | 93% | 2024 Senate (13) |
| 44 | New Hampshire | 31 (33 / 28) | 7 | 3.3 | 3.8 | 1.1 | 0.8 | -3.3 | 0 | 2 | 82% | 2024 Governor (8) |
| 45 | South Carolina | 31 (33 / 28) | 5 | 1.7 | 2.5 | 2.8 | 0.3 | -0.0 | 0 | 0 | 98% | 2022 Senate (8) |
| 46 | North Dakota | 28 (28 / 28) | 6 | 4.0 | 4.5 | 1.6 | 0.0 | -2.4 | 0 | 1 | 100% | 2020 President (22) |
| 47 | West Virginia | 26 (24 / 28) | 5 | 7.0 | 1.6 | 0.2 | 0.2 | -7.0 | 0 | 0 | 98% | 2020 Governor (18) |
| 48 | Vermont | 25 (21 / 28) | 7 | 2.5 | 2.8 | 1.2 | 0.1 | -0.4 | 0 | 0 | 99% | 2024 President (10) |
| 49 | Wyoming | 25 (21 / 28) | 5 | 3.9 | 4.1 | 1.0 | 0.0 | +3.9 | 0 | 0 | 100% | 2020 President (11) |
| 50 | Massachusetts | 24 (19 / 28) | 4 | 2.2 | 0.1 | 0.4 | 1.0 | -1.3 | 0 | 0 | 88% | 2024 Senate (3) |
| 51 | District of Columbia | 20 (12 / 28) | 1 | 1.6 | 1.4 | 0.5 | 0.1 | +1.6 | 0 | 0 | 67% | 2020 President (2) |
