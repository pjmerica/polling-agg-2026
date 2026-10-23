# Which states' counts swing the most: every state, 2020-2024

*Built by `scripts/volatility.py` from NYT's minute-by-minute statewide results timelines for every
President, Senate and Governor general election from 2020 to 2024: {{N_RACES}} races in the 50 states and DC.
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

{{TOP15}}

## Our eleven competitive states, by national rank

{{COMPETITIVE}}

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

{{BIG_RACES}}

## The biggest moves after election night (6 am ET to the final count)

{{LATE_RACES}}

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

{{ALL_STATES}}
