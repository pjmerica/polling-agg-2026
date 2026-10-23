# Election night, Nov 3, 2026: master guide

*One file to read through. It covers the competitive Governor and Senate races (our model's favorite at 75% or
less): 13 races in eleven states. For each state it covers how votes are counted and reported, when results arrive, how far the count has moved in
past elections, and where that creates opportunities as results come in.*

*Built by `scripts/build_master.py` from `STATE_BY_STATE.md` (rules, checked against primary sources)
and the swings analysis (406 races, 2020-2026, from NYT's minute-by-minute timelines). Every table is
generated from data. Model numbers: forecast run of 2026-10-22 18:05 UTC. Market numbers: 2026-10-22 22:52 UTC refresh. They move daily. Nevada, Oregon and Texas Governor were added on
Oct 22, when the model audit (`model_audit/MODEL_AUDIT.md`) moved them under 75%.*

**Contents**
1. The states at a glance
2. Which state is the best opportunity as results come in
3. What is certain and what isn't, plus patterns across states
4. State by state: rules, how results come in, history, swing data
5. Cross-state tables
6. Corrections, open questions, sources

---

## 1. The states at a glance

Listed in poll-closing order.

| # | State | Competitive race(s) | Model favorite (win %) | Market, same candidate | Polls close (ET) | First votes usually appear | Who usually leads early | A close race is usually settled |
|---|---|---|---|---|---|---|---|---|
| 1 | Georgia | Governor | Bottoms (D) 55.0% vs Jackson (R) | Bottoms 61% | 7:00 pm | 7:03-7:14 pm | Democrat, then Republican by ~8:30-9:40 pm | Election night / early Wed; an automatic hand recount if within 0.5% |
| 2 | Ohio | Governor; Senate (special) | Acton (D) 54.9% vs Ramaswamy (R); Brown (D) 59.6% vs Husted (R) | Acton 84%; Brown 69% | 7:30 pm | 7:37-7:39 pm | Democrat, then Republican by ~8:25-10:00 pm | Election night (11 pm-12:30 am) |
| 3 | Michigan | Senate | El-Sayed (D) 63.4% vs Rogers (R) | El-Sayed 70% | 8:00 pm (4 western UP counties 9:00 pm) | 8:03-8:20 pm | 2024: Democrat until ~10:45 pm, Republican overnight, Democrat Wed morning. 2020: Republican until Wed | Wednesday midday to afternoon |
| 4 | Texas | Senate; Governor | Talarico (D) 55.0% vs Paxton (R); Abbott (R) 74.0% vs Hinojosa (D) | Talarico 67%; Abbott 68% | 8:00 pm (El Paso and Hudspeth 9:00 pm) | ~8:00-8:09 pm | Democrat until 8:31-8:37 pm (2020 President: until 9:29 pm), then Republican | Election night; AP calls no statewide race before 9 pm |
| 5 | Kansas | Senate | Marshall (R) 58.8% vs Hamilton (D) | Marshall 62% | 8:00 pm (Mountain-time counties up to 9:00 pm) | 8:08-8:10 pm | Democrat until ~9:35-10:05 pm | Election night if clear; Wednesday if close (2022 Governor: 1:24 pm Wed) |
| 6 | Maine | Senate (ranked-choice) | Jackson (D) 71.6% vs Collins (R) | Jackson 66% | 8:00 pm | 8:08-8:44 pm | Whoever leads the early towns; the count then moves 4-8 pts toward the non-Republican | First round: Wed/Thu. If no one tops 50% of all ballots: ranked-choice count, about 8-10 days |
| 7 | Iowa | Senate | Hinson (R) 68.2% vs Turek (D) | Hinson 57% | 9:00 pm (10:00 pm until 2021) | 2-13 min after the close (2020: 10:13 pm) | Democrat until ~10:00-11:30 pm | Election night |
| 8 | Nebraska | Senate | Ricketts (R) 62.2% vs Osborn (I); no Democrat on the ballot | Ricketts 74% | 9:00 pm (whole state) | 9:00-9:08 pm | 2024: Osborn until ~11:25 pm. 2022 Governor: Democrat until 9:51 pm. 2020: Republican | Around midnight; Omaha leftovers counted Friday and the following week |
| 9 | Nevada | Governor | Lombardo (R) 69.5% vs Ford (D) | Lombardo 34% (the market favors Ford) | 10:00 pm (nothing posts until the last voter in line has voted) | 11:50 pm-1:00 am | Democrat in the first big drop in 2020 and 2022 (2022: +11-13 with 44% counted), about even in 2024; the Republican gains overnight as Election Day votes post | Fri-Sat after Election Day (2020, 2022, 2024) |
| 10 | Oregon | Governor | Kotek (D) 70.1% vs Drazan (R) | Kotek 83% | 11:00 pm (Malheur County, Mountain time, 10:00 pm) | 10:00-11:10 pm | Democrat (2022 Governor: +9.8 in the first release, +1.0 by 1 am ET, +3.4 final) | Thursday (2022 Governor: AP at 85% counted); close House races 5-9 days |
| 11 | Alaska | Senate (ranked-choice) | Peltola (D) 51.9% vs Sullivan (R) | Peltola 75% | midnight (one Aleutian site 1:00 am) | ~12:45-1:10 am (2:47 am in 2020) | Republican on election night; mail counted later moves toward the Democrat | Nov 18 (ranked-choice day); calls in 2020/2022 came Nov 11-23 |

Notes on the table:
- **Market column:** the market's chance for the model's favorite (where the market priced the other candidate, 100 minus that price). Under 50% means the market favors the other candidate: Nevada.
- **"Who usually leads early"** comes from the history tables below, not from rules.
- **The cut moves with the model.** The audit's retrain (Oct 22) brought Nevada, Oregon and Texas Governor under 75%; Texas Governor is the closest to the line. See `competitive_races.md`.

---

## 2. Which state is the best opportunity as results come in

*My assessment from the data in this file. It is judgment, not a forecast and not financial advice. Market
traders also know that early leads mislead, so any edge comes from knowing **how much** and **when** the
count moves more precisely than the market does, and from acting faster.*

### What makes a state good for betting during the count

1. **A long window of incomplete results:** the market trades for hours on partial counts.
2. **A reporting order that repeats** from year to year, so the direction of the coming votes is predictable.
3. **Lead changes:** prices swing hardest when the visible leader flips.
4. **Enough liquidity** to get in and out.
5. **A close race:** if it isn't, there's nothing to trade.

### Ranking

| Rank | State | Why | Main risks |
|---|---|---|---|
| **1** | **Nevada Governor** | The longest window and the most consistent late direction in the data. Close races are decided Wednesday to Saturday, and the post-election-night count moved toward the Democrat in every statewide race since 2020. It's also the biggest model-market disagreement (detail below). | 2024's tail was about half of 2022's. Clark's new print-and-scan ballots are untested at general-election turnout. Thinner market than Michigan or Maine. First numbers only at ~1-2 am ET. |
| **2** | **Michigan Senate** | Long window, repeating order and liquid (detail below) | Late batches aren't always Democratic: the 2026 primary narrowed late against El-Sayed (6.3 → 0.9), and 2024's late move was ~0. |
| **3** | **Kansas, Nebraska, Iowa, Ohio, Texas: fade the early Democratic/independent lead** | The **most reliable direction** in the national data. In every 2020-2024 race in these five states, the count moved toward the Republican after the first quarter was in, usually by 15-30 pts. The leader at some point lost in 4 or 5 of each state's 5 races. All five are in the national top eight for volatility (`VOLATILITY.md`). They settle **on election night**, so money turns over quickly. | The window is short: Ohio and Texas post most of their vote in the first hour or two. Thinner markets in Kansas and Nebraska (Kansas ~2.2M Kalshi contracts; Nebraska not on Kalshi in our data). 2026's early vote may be more Democratic than before, so early leads may be bigger, and so may the fade. Most likely already priced in by sharp traders. |
| **4** | **Maine Senate** | Slow count, liquid market, a repeating early pattern, and ranked-choice complications (detail below) | Nationally it's one of the calmer counts: its 4-8 point move happens while little is counted, and no 2020-2024 Maine race had a leader who went on to lose (`VOLATILITY.md`). No live state feed; towns report piecemeal to AP. The ranked-choice count resolves ~8-10 days later. |
| Special case | **Alaska Senate** | Big model-market disagreement (detail below) | Settles only after Nov 18 (ranked-choice count), possibly later with a recount, so money is tied up for weeks. The model's poll inputs in Alaska are thin. |
| Special case | **Oregon Governor** | Nevada's mirror image: Kotek's numbers look **worst** at the end of election night (detail below) | The market already prices Kotek 83%, and it's thin (Kalshi ~130K contracts; Polymarket ~$113K liquidity, Oct 19). Only interesting if election night shows Drazan ahead or Kotek's price drops. |
| Avoid during the count | **Georgia** | Fast (94-98% counted by midnight in 2022 and 2024; 80% in 2020), and its direction has flipped by year: toward the Democrat in 2020 and 2024, toward the Republican in 2022. | Little time and no reliable direction to trade. |

**1. Nevada Governor** (Lombardo R vs Ford D; model Lombardo 69.5%, market Lombardo 34%, so the market favors Ford)
- **Long window:**
  - Nothing posts until the last voter in line has voted. First votes came at 11:53 pm-12:55 am ET in 2020-2024, and the first big drop at ~1-2 am.
  - Election Day drop-offs (54,000-57,000 in Clark in 2022/2024) are counted Wednesday to Saturday, and more than 100,000 ballots were left after election night each time.
  - AP called every close statewide race since 2020 on day 3 or 4.
- **Repeating direction:**
  - After election night, the count moved toward the Democrat in every statewide race since 2020: 2022 Senate +3.5, 2022 Governor +3.2, 2020 President +1.8, 2024 Senate +1.7, 2024 President +1.6.
  - In votes, about 24,000-31,000 in the two Senate races.
- **Lead changes:**
  - 2022 Senate: Laxalt led from ~4 am Wednesday until Cortez Masto went ahead at 9:14 pm ET Saturday.
  - 2024 Senate: the lead traded twice overnight before Rosen pulled ahead for good.
- **Liquidity:** ~1.07M contracts traded on Kalshi; ~$378K liquidity on Polymarket (Oct 19). That is less than Michigan or Maine, but tradeable.
- **The trade it suggests:**
  - Lombardo's numbers look their best on Wednesday morning, when Election Day in-person votes are in and the drop-offs aren't.
  - If the price moves toward him then, the count still to come has favored the Democrat every time.
  - The research puts the line at **~25,000-30,000 votes (about 2-2.5 points)**: a smaller Lombardo lead on Wednesday morning is at risk, a larger one should hold.
  - Watch Clark's and Washoe's counts of Election Day drop-offs, and whether the Secretary of State again publishes outstanding ballots by county.

**2. Michigan Senate** (El-Sayed D vs Rogers R; model El-Sayed 63.4%, market El-Sayed 70%)
- **Long window:** only 46-50% is counted by midnight ET in every recent general. The 2024 Senate race was called at 3:12 pm the next day.
- **Repeating order:** Wayne County (Detroit) and the other big counties report late.
  - 2020: the 18% counted after 6 am went Biden +35, almost all Wayne.
- **Lead changes:**
  - 2024 Senate: Slotkin led until 10:44 pm, Rogers led overnight, Slotkin retook it at 7:31 am.
  - 2020 Senate: James led until Wednesday afternoon.
  - Prices swing hardest at those moments.
- **Liquid:** ~3.3M contracts traded on Kalshi; ~$577K liquidity on Polymarket (as of Oct 19-20).

**3. Fade the early lead: Kansas, Nebraska, Iowa, Ohio, Texas**
- **Every race moved the same way.** After the first update with a quarter of the vote in, the margin moved toward the Republican in all 25 of these states' 2020-2024 top races:

  | State | Move after the first quarter, every race |
  |---|---|
  | Kansas | −9 to −27 |
  | Nebraska | −9 to −37 |
  | Iowa | −15 to −28 |
  | Ohio | −6 to −30 |
  | Texas | −6 to −20 |

- **Examples:**
  - **Kansas 2022:** every race moved 5+ pts toward Republicans after 2 hours (median 19). Governor Kelly's +20 became a 2.2-point win.
  - **Nebraska 2024:** Osborn led by **18** at 9:00 pm and lost by 6.7. The lead changed at about 11:25 pm, and the race was called at 12:06 am.
  - **Iowa:** the first-hour margin moved a median 13-29 pts by the end.
  - **Ohio 2020:** Biden was +21.9 at the first update with a quarter in; Trump won by 8.0.
  - **Texas 2020:** Biden was +14.4 at that point; Trump won by 5.6.
- **Timing:** Ohio and Texas do most of the move within about two hours of the close, though Texas still moved 2-4 points after 10 pm. Kansas, Nebraska and Iowa take two to three hours.
- **When a lead is safe** (from 2020-2024; each state's section has the detail):

  | State | Lead the Democrat/independent needed to be safe |
  |---|---|
  | Texas | ~7+ pts at 9 pm, ~4+ at 10 pm |
  | Kansas | ~8+ at 10:30 pm |
  | Iowa | ~2+ at 11 pm |
  | Nebraska | ~9+ at midnight |
  | Ohio | ~1+ at 10 pm in 2022/2024; in 2020 the count moved 8 more pts toward the Republican after 10 pm |
- **2026:** Talarico and Hinojosa (Texas), Acton and Brown (Ohio), Hamilton (Kansas), Osborn (Nebraska) and Turek (Iowa) should all lead early.
- The Ohio Governor gap (model Acton 54.9%, market Acton 84%) is a **pre-election** disagreement, not a live-count one.

**4. Maine Senate** (Jackson D vs Collins R; model Jackson 71.6%, market Jackson 66%)
- **Slow:** only 29-63% is counted by midnight ET.
- **Repeating pattern:** in every top race we have, the count moved 4-8 pts toward the non-Republican after the first two hours, then 0-3 pts back after 6 am. Most of that move happens while under a quarter of the vote is in, so the window is the first two hours.
- **Liquid:** ~4.4M Kalshi contracts; ~$2.3M Polymarket volume.
- **Ranked-choice wrinkle:** if no one tops 50% of *all* ballots (blanks count against the leader), the ranked-choice count decides about a week later, a second chance for prices to be wrong.

**Special case: Alaska Senate** (Peltola D vs Sullivan R)
- **The disagreement:** our model says Peltola 51.9%; the market says Peltola 75%.
- **What the count pattern implies:** Sullivan should lead on election night. Mail counted Nov 10-18 has moved the margin 2-3 pts toward Democrats (16 in 2020). That pattern **agrees with the market's direction**.
- **The trade it suggests:** if Sullivan's election-night lead pushes the market toward him, that may be a better entry for a Peltola position than today.

**Special case: Oregon Governor** (Kotek D vs Drazan R; model Kotek 70.1%, market Kotek 83%)
- **The first release** at 11 pm ET holds most of the vote and showed Kotek's high point in 2022 (+9.8). By 1 am she was down to +1.0.
- **Wednesday to Friday** (Multnomah and Washington Election Day drop-offs) took her back to +3.7 by Friday midday; the final was +3.4.
- **The rule of thumb:** a Drazan lead under ~2 points at the end of election night is at real risk, and a Kotek lead should grow.

### How these states compare nationally

From `VOLATILITY.md`, which measures every President, Senate and Governor race in the 50 states and DC, 2020-2024. A state ranks high when its visible margin moves a lot during the count *and* its leader at some point often lost.
- **National top ten:** Kansas, Nebraska, Virginia, Michigan, Iowa, Rhode Island, Texas, Ohio, North Carolina, Georgia.
- **Our eleven, by national rank:** Kansas 1, Nebraska 2, Michigan 4, Iowa 5, Texas 7, Ohio 8, Georgia 10, Nevada 17, Alaska 19, Oregon 33, Maine 37.
- **Volatility isn't the same as opportunity.**
  - The biggest swings (Kansas, Nebraska, Iowa) are also the most predictable and settle within hours, so they're probably priced in.
  - Nevada's swings are small (about 2 points) but always in the same direction. They play out over days, and they changed the leader in 3 of its 5 races.

### Practical cautions

- **Settlement rules differ by platform** (see `AGENTS.md`):
  - Kalshi election markets resolve on who is **sworn in**; Polymarket resolves on who **wins**.
  - These all delay settlement:
    - ranked-choice counts (Alaska Nov 18, Maine about a week later);
    - recounts: automatic in Georgia's governor race at 0.5% or less, Michigan at 0.1%, Ohio at 0.25%, Oregon at 0.2%, and Nebraska at 1% of the leader's vote. Nevada recounts only on demand, by Dec 1;
    - late mail: Alaska to Nov 13, Oregon to Nov 10, Nevada to Nov 7, Kansas to Nov 6, Texas to Nov 4.
  - Nevada's statewide canvass is Nov 24. Oregon's governor result is never certified by the Secretary of State; the House Speaker publishes it before the 2027 Legislature.
- **Fees are real per leg** (`utils/fees.py`). Small edges disappear.
- **The tools that make this usable are already set up:**
  - The election-night recorder (`capture_live.py`) saves every county every 2 minutes from 6:30 pm ET. It now includes Nevada, Oregon and Texas Governor, and keeps running for three weeks.
  - The next step is the simulator in the README, which turns "X% counted, these counties out" into a projected final.
  - Without the simulator, the tables in this file are rules of thumb.
- **2026 differs from history:** new laws (Michigan pre-processing, Georgia's 8 pm rule, Ohio's ended grace period), Clark County's new ballots, slower USPS postmarks (Oregon rejected 13% of its late mail in May for late postmarks) and a more Democratic early vote. Expect the patterns, not the exact sizes.

---

## 3. What is certain and what isn't, plus patterns across states

### Is there any source that says for certain when votes will be counted?

**No.** No state, county, AP or anyone else publishes a guaranteed timetable for when each batch of votes will post. What exists falls into three tiers.

**Tier 1: set by law or official schedule.** These are the only firm times, and they are mostly limits and deadlines, not posting times.

| State | Firm rule | Source |
|---|---|---|
| All 11 | No results before polls close (Michigan, Maine, Georgia, Iowa, Nebraska, Texas, Nevada and Oregon statutes checked; Ohio by directive) | Statutes ✔ |
| Nevada | No mail-ballot results until **all polling places are closed and all votes cast**: voters in line at 7 pm PT still vote, so the first results wait for the last one. Mail counting **must finish by day 7, Tue Nov 10** | [NRS 293.269935, 293.269931, 293.305](https://www.leg.state.nv.us/NRS/NRS-293.html) ✔ |
| Oregon | Nothing before 8 pm local; drop sites open until at least 8 pm; mailed ballots postmarked by Nov 3 count through **Tue Nov 10** | [ORS 260.705](https://www.oregonlegislature.gov/bills_laws/ors/ors260.html), [254.470](https://www.oregonlegislature.gov/bills_laws/ors/ors254.html) ✔ |
| Georgia | Early-vote and pre-Monday absentee results **must be reported by 8:00 pm** or within 1 hour of the county's last poll closing | SB 189 ✔ |
| Ohio | Each county must **upload absentee totals by 8:00 pm**, then update at assigned intervals until done | Directive 2026-22 ✔ |
| Iowa | Absentee boards staffed to finish **by 10:00 pm CT**; each county's absentee result is released only when complete | Iowa Code 53.23 ✔ |
| Texas | Counting may not stop once begun; results due **within 24 hours** of polls closing | SOS 2022 ✔ |
| Alaska | Count days **Nov 10, 13, 18**; ranked-choice tabulation after the day-15 count; first results "anticipated" 8:45-9:00 pm Alaska time | Media Packet ✔ |
| Maine | Town returns due **within 2 business days**; ranked-choice count only after all towns' ballots reach Augusta | §711 ✔ |
| All 11 | Canvass and certification deadlines (see each state) | Statutes ✔ |

**Even these slip.**
- Harris County missed Texas's 24-hour deadline in March 2022 ✔.
- Chatham County, GA showed "all precincts reporting" in 2024 while its early votes were missing ◐.
- Flint skipped early processing in Aug 2026 and reported the next morning ○.

**Tier 2: officials' stated plans.**
- **Firm only to the extent the county keeps to them.**
  - Sedgwick County's "Wednesday afternoon" update for drop-box ballots ✔.
  - Douglas County, NE's past release schedule (8:00, 8:45, 9:45, 10:45, 11:45 pm CT; search-summary only ○).
- **Published for Nov 3:** Multnomah, Washington and Clackamas counties in Oregon (section 12) ◐. Washoe County (Reno) says it posts by noon and 5 pm PT each day after the election ○.
- **Not published yet:** the large counties in the other nine states, and Clark County (Las Vegas).
- **Historical habit, not plans:** AP's previews describe what counties have done before ("tend to release ... in the first vote update").

**Tier 3: history.**
- The tables in each section are measured, not promised: NYT's timelines, accurate to the minute for 2020-2024.
- They are the best guide to *shape* (what reports first, when leads change). But each year differs with turnout mix, law changes and staffing.

**The only way to know the 2026 timing is to record it.** `capture_live.py` runs on election night and saves every county's results every 2 minutes, so we will have Nov 3 to the minute. That will also give real data for future elections.

### Patterns across states

1. **The first batch is mostly early and mail votes**: in Georgia (required by law), Ohio, Texas, Kansas, Iowa and
   Nebraska (AP 2026 previews ✔). Where those votes lean Democratic, the Democrat leads early and the lead shrinks
   as Election Day precincts report. The size of the shrink is in each state's table.
2. **Michigan, Alaska, Nevada and Oregon run the other way at the end.**
   - Michigan's largest counties (Wayne/Detroit above all) report late.
   - Alaska counts most mail ballots days later.
   - Nevada and Oregon count late mail and Election Day drop-offs for days. From the end of election night to the
     final count, Nevada moved 1.6-3.5 points toward the Democrat in every top race of 2020-2024. Oregon's 2022
     Governor race went from Kotek +1.0 to +3.4, though Oregon 2020 moved 1.3 points the other way.
3. **Maine is slow because ~500 towns report separately.** Only 29-63% was counted by midnight in 2020-2024.
   The late towns have moved the count 4-8 points toward the non-Republican after the first two hours in every
   race we have.
4. **This year, early Democratic leads may be bigger than usual.** The early electorate is more Democratic than
   in 2024, so don't read an inflated early lead as a landslide. Early-vote numbers so far:

   | State | What's known | Source |
   |---|---|---|
   | Ohio | The early electorate is about 27 points more Democratic than at the same point in 2024. Early in-person voting is at 72% of 2024's pace, mail at 25%. | CNN, Oct 11 ○ |
   | Maine | 101,777 absentee ballots returned, 53% from Democrats. | Oct 17 ◐ |
   | Michigan | More than **440,000 ballots returned by Oct 13** (6% of active voters); about **2.08 million absentee ballots requested**, up 20% on 2022. | [MI SoS release, Oct 13](https://www.michigan.gov/sos/resources/news/2026/10/13/three-weeks-before-election-day-6-percent-of-voters-have-already-cast-their-ballot) ✔ |
   | Georgia | First-day early voting (Oct 13) set a midterm record: 188,667 in person, against 134,962 in 2022. | [Fox 5](https://www.fox5atlanta.com/news/georgia-early-voting-sets-record-more-than-188k-voters) ○ |

   On the other side, Democratic mail-ballot requests are down sharply in some states, because of worry about the
   USPS (NBC/Penn early-vote analysis, Oct 9 ○). That could shrink the mail share of the first batch.
5. **Mail-ballot deadlines.** Five of the eleven states count domestic mail ballots that arrive after Election
   Day, if postmarked by it:
   - Alaska: 10 days.
   - Oregon: 7 days, to Tue Nov 10.
   - Nevada: to 5 pm PT Sat Nov 7; ballots with no readable postmark to Fri Nov 6.
   - Kansas: 3 days.
   - Texas: to 5 pm Nov 4. The Supreme Court left those deadlines to the states in
   *Watson v. RNC*, June 29, 2026 ✔. The executive order restricting USPS ballot delivery is frozen for
   Nov 3: the Supreme Court left the lower court's freeze in place, per Votebeat, Sept 15 ✔.

---

# 4. State by state

In poll-closing order. Each state has three parts:
- rules and how results get reported, checked against primary sources: ✔ re-read, ◐ read by a researcher, ○ secondary;
- generated history tables;
- the swing data for that state.

## Georgia: Governor

**Race.**
- Keisha Lance Bottoms (D) vs Rick Jackson (R); open seat.
- Model: Bottoms 55.0%. Market: Bottoms 61%.
- Ballot: two candidates. The Libertarian Party failed to qualify for the 2026 ballot (its petition drive fell short in July: [AJC](https://www.ajc.com/politics/2026/07/libertarians-wont-be-on-the-ballot-in-georgia-meaning-likely-no-runoffs/), [WABE](https://www.wabe.org/georgia-libertarians-end-efforts-to-get-on-2026-general-election-ballot/) ○). Only write-ins could add a third name, so runoff risk is close to zero.
- A majority is required. A general-election runoff, if needed, is **Tue Dec 1** ✔ ([georgia.gov](https://georgia.gov/events/2026-12-01/election-day-general-election-runoff)).

**Rules for Nov 3**
- Polls close 7:00 pm ET.
- Absentee ballots are due at poll close. Military and overseas ballots postmarked by Election Day count if received within the 3 days after, so by Fri Nov 6 ✔.
- Counties may begin processing absentee ballots at 8:00 am on the third Monday before the election (Oct 12) ✔. Nothing may be disclosed before 7:00 pm ✔ ([O.C.G.A. 21-2-386 via FindLaw](https://codes.findlaw.com/ga/title-21-elections/ga-code-sect-21-2-386/)).
- The same section gives counties until **5:00 pm the day after the election** to report verified absentee returns, before a state performance review can be triggered ✔.
- **SB 189 (2024) ✔**:
  - Every absentee ballot accepted by the Monday before, and every early in-person vote, must be tabulated and **reported by 8:00 pm, or within one hour of the county's last poll closing**, whichever is later.
  - Source: [SB 189 text](https://gov.georgia.gov/document/2024-signed-legislation/sb-189/download).

**How results are reported.**
- 159 counties report to the Secretary of State's results site.
- More than half the counties release all or almost all mail and early in-person votes in their first update (AP May 2026 ✔).
- The Secretary of State projected 70-75% of the vote reported by 8 pm in 2024 ◐.
- Trap: in 2024 Chatham County showed "all precincts reporting" while its early votes were missing ◐. Watch the expected-vote share, not the precinct count.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 7:14 pm | 80% | Biden led first; Trump ahead 7:40 pm (5% in); lead traded 7:59 pm-8:05 pm, Trump ahead from 8:05 pm (11% in); Biden ahead Nov 5 (99% in) | Nov 13 (NYT) | Biden (D) +0.2 |
| 2020 | Senate | 7:14 pm | 79% | Ossoff led first; Perdue ahead 7:36 pm (5% in) | Nov 6 (NYT) | Perdue (R) +1.8 |
| 2022 | Governor | 7:03 pm | 94% | Abrams led first; Kemp ahead 8:34 pm (43% in) | Wed 12:49 am (AP) | Kemp (R) +7.5 |
| 2022 | Senate | 7:03 pm | 94% | Warnock led first; lead traded 9:00 pm-9:03 pm, Warnock ahead from 9:03 pm (63% in); Walker ahead 9:39 pm (75% in); lead traded 11:21 pm-11:22 pm, Walker ahead from 11:22 pm (91% in); Warnock ahead Wed 12:17 am (94% in) | - | Warnock (D) +1.0 |
| 2024 | President | before 8:00 pm (timeline starts 8:00 pm) | 98% | Trump led first (timeline ends 5:40 am Wed) | Wed 12:46 am (AP) | Trump (R) +2.2 |

What the curves show (`state_curves.md`):
- **2022 Governor:** Abrams was +9.0 one hour after close with 27% counted. Kemp led from 8:34 pm and won by 7.5.
- **2022 Senate:** Warnock was +16.5 at one hour; the lead traded hands for three hours and he finished +1.0.
- **2020:** the very late count (Atlanta-area mail) took Biden from −15 at two hours after close to +0.2.
- **2024:** about 98% was counted by midnight, the fastest of the eleven states.

**After election night**

| Date | Event |
|---|---|
| Fri Nov 6 | Military/overseas ballots due ✔; county registrars must decide every provisional ballot "not later than three days following the ... election" ✔ ([O.C.G.A. 21-2-419(c)(1)](https://codes.findlaw.com/ga/title-21-elections/ga-code-sect-21-2-419/)) |
| Mon Nov 9, 5 pm | County certification ✔ ([Cobb Courier](https://cobbcountycourier.com/2026/10/which-comes-first-after-election-day-certification-or-a-recount/)) |
| within 2 business days of Nov 9 | **If the Governor margin is 0.5% or less, the Secretary of State must order a full hand recount in every county**, with no request needed ✔ (law signed June 25, 2026, [Fox 5](https://www.fox5atlanta.com/news/georgia-election-bill-deadlines-new-law-delays-ballot-qr-code-removal); [Cobb Courier](https://cobbcountycourier.com/2026/10/which-comes-first-after-election-day-certification-or-a-recount/)). U.S. Senate recounts still need a request. |
| Fri Nov 20 | State certification (17 days after) ✔ |
| Tue Dec 1 | Runoff, if no majority ✔ |

**What to expect** (inference):
- Expect a large Democratic-leaning batch between 7:00 and 8:00 pm, then Republican-leaning rural Election Day precincts.
- The 2022 Governor lead changed at about 43% counted (8:34 pm).
- Watch for metro Atlanta's late batches: after 9:00 pm the count moved **toward the Democrat** in 2024 (+3.2) and 2020 (+15.5), and barely at all in 2022.
- A race inside ~2 points is likely called around midnight to 1 am, as in 2022 (12:49 am) and 2024 (12:46 am).
- Inside 0.5%, there is no final result before the hand recount, around Nov 18-20.

### The swing data: Georgia

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Georgia | 2020 | 2 | 10% / 32% / 79% / 94% | +5.1 | +15.7 | +2.3 | 2 of 2 |
| Georgia | 2022 | 22 | 27% / 54% / 93% / 100% | -14.3 | -3.1 | +0.0 | 11 of 22 |
| Georgia | 2024 | 15 | 30% / 69% / 99% / 100% | -0.5 | +0.2 | +0.0 | 5 of 15 |

#### Biggest moves in competitive races

**Georgia**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 Lieutenant Governor | 16.3% / +15.2 | 90.3% / -5.6 | 99.2% / -5.3 | -5.0 | **-20.2** | +0.4 |
| 2022 Attorney General | 16.3% / +14.6 | 90.0% / -5.9 | 98.8% / -5.3 | -5.3 | **-19.9** | +0.0 |
| 2022 Labor Commissioner | 16.3% / +13.1 | 90.3% / -7.5 | 99.1% / -6.9 | -6.8 | **-19.9** | +0.2 |
| 2022 Insurance Commissioner | 16.3% / +11.6 | 90.1% / -8.9 | 98.8% / -8.3 | -8.2 | **-19.8** | +0.1 |
| 2022 Agriculture Commissioner | 16.3% / +11.5 | 90.0% / -8.8 | 98.8% / -8.1 | -8.1 | **-19.6** | +0.0 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Georgia 2020 President | GA-G-P-2020-11-03 | Trump (32.3%) | Trump (79.6%) | Trump (94.4%) | Biden +0.2 | Nov 5 9:32 pm (99.0% in) |
| Georgia 2022 Agriculture Commissioner | GA-G-agriculture_commissioner-2022-11-08 | Hemingway (16.3%) | Harper (90.0%) | Harper (98.8%) | Harper +8.1 | 9:31 pm (44.5% in) |
| Georgia 2022 Attorney General | GA-G-attorney_general-2022-11-08 | Jordan (16.3%) | Carr (90.0%) | Carr (98.8%) | Carr +5.3 | 9:31 pm (45.7% in) |
| Georgia 2022 Insurance Commissioner | GA-G-insurance_commissioner-2022-11-08 | Laws Robinson (16.3%) | King (90.1%) | King (98.8%) | King +8.2 | 9:31 pm (43.9% in) |
| Georgia 2022 Labor Commissioner | GA-G-labor_commissioner-2022-11-08 | Boddie (16.3%) | Thompson (90.3%) | Thompson (99.1%) | Thompson +6.8 | 9:31 pm (44.4% in) |
| Georgia 2022 Lieutenant Governor | GA-G-LG-2022-11-08 | Bailey (16.3%) | Jones (90.3%) | Jones (99.2%) | Jones +5.0 | 9:32 pm (66.7% in) |
| Georgia 2022 Senate | GA-G-S-2022-11-08 | Warnock (55.6%) | Walker (93.7%) | Warnock (99.5%) | Warnock +1.0 | Wed 12:17 am (94.3% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Georgia 2020 President | 94.4% | -2.2 | +0.2 | **+2.4** |
| Georgia 2020 Senate | 94.5% | -3.9 | -1.8 | **+2.1** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Georgia | midnight ET | 20% | +38.2 | DeKalb 5.5% (+67); Fulton 5.0% (+46); Gwinnett 2.2% (+26); Cobb 2.0% (+18) | 12:00 AM |
| Georgia | 6 am ET | 6% | +42.7 | Fulton 1.6% (+56); DeKalb 1.0% (+70); Chatham 0.5% (+42); Houston 0.4% (+18) | 5:52 AM |

#### 2026 primaries, runoffs and specials

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


---

## Ohio: Governor and Senate special election

**Races.**

| Race | Candidates | Model | Market |
|---|---|---|---|
| Governor (open) | Amy Acton (D) vs Vivek Ramaswamy (R) | Acton 54.9% | Acton 84% |
| Senate special | Sherrod Brown (D) vs Jon Husted (R, appointed) | Brown 59.6% | Brown 69% |

**Rules for Nov 3**
- **Deadlines and ballot processing:**
  - Polls close 7:30 pm.
  - **Absentee ballots must reach the board by poll close.** SB 293 ended the post-Election-Day grace period, effective March 20, 2026 ✔ ([ORC 3509.05](https://codes.ohio.gov/ohio-revised-code/section-3509.05)).
  - Military and overseas ballots postmarked by the day before Election Day get 4 more days ✔ (Directive 2026-22, for the May primary).
  - Boards may scan absentees from Oct 6 but **may not tabulate before 7:31 pm** (Directive 2026-48 ○, 2026-22 ✔).
- **Reporting duties:**
  - Each board must **upload absentee totals by 8:00 pm** (partial if necessary), then upload updates "at assigned intervals until 100 percent of precincts are reported" ✔ ([Directive 2026-22](https://www.ohiosos.gov/assets/directive-2026-22-unofficial-official-canvass-checklist.pdf)).
  - Earlier directives put the big counties on a 15-minute upload cycle; the 2026 list is not confirmed ○.
- **After the polls close:**
  - Provisional voters have 4 days to cure, so to Sat Nov 7 ✔ ([ORC 3505.181](https://codes.ohio.gov/ohio-revised-code/section-3505.181)).
  - County canvass starts day 5-15 and **must finish by day 21, Tue Nov 24** ✔ ([ORC 3505.32](https://codes.ohio.gov/ohio-revised-code/section-3505.32)).
  - Automatic recount if the margin is under 0.25% statewide ✔ (AP May 2026).

**How results are reported.**
- 88 counties.
- "All 88 counties tend to release all or almost all of their early and absentee voting results in the first vote update of the night, in most cases before any in-person Election Day results" ✔ (AP May 2026).
- 2024 primary: first results 7:36 pm, ~90% counted by 10:19 pm ✔.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 7:39 pm | 95% | Biden led first; Trump ahead 10:00 pm (73% in) | Wed 12:07 am (NYT) | Trump (R) +8.0 |
| 2022 | Governor | 7:39 pm | 96% | Whaley led first; DeWine ahead 8:03 pm (11% in) | 9:03 pm (AP) | DeWine (R) +25.1 |
| 2022 | Senate | 7:39 pm | 96% | Ryan led first; Vance ahead 9:28 pm (48% in) | 11:20 pm (AP) | Vance (R) +6.1 |
| 2024 | President | before 8:00 pm (timeline starts 8:00 pm) | 95% | Harris led first; Trump ahead 8:24 pm (41% in) (timeline ends 5:40 am Wed) | 9:08 pm (AP) | Trump (R) +11.2 |
| 2024 | Senate | 7:37 pm | 95% | Moreno led first; Brown ahead 8:02 pm (18% in); lead traded 8:18 pm-8:25 pm, Brown ahead from 8:25 pm (38% in); Moreno ahead 8:57 pm (49% in) | 11:28 pm (AP) | Moreno (R) +3.6 |

What the curves show:

| Race | Early lead (1 hour after close) | When the Republican took the lead | Final |
|---|---|---|---|
| 2022 Senate | Ryan +13.2, 28% counted | 9:28 pm | Vance +6.1 |
| 2024 Senate | Brown +4.5, 41% counted | 8:57 pm | Moreno +3.6 |
| 2020 President | Biden +10.2 | 10:00 pm | Trump +8.0 |

- AP's preview says "around 9:30 pm" for 2020 as well, but NYT's timeline shows 10:00 pm.
- About 95% of the vote is counted by midnight.
- After election night only provisional ballots remain: 137,879 were outstanding in 2024 ○.
- With the domestic grace period gone, there is very little late mail; 1,564 late absentees arrived in the May 2026 primary ○.

**What to expect** (inference):
- Brown and Acton will lead the 7:35-8:00 pm batch, probably by more than Brown's 2024 early lead, because the early vote is more Democratic this year.
- Neither lead means much until Election Day precincts are mostly in (~9:30-10:30 pm).
- A race decided by 3-4+ points is likely called 11 pm-12:30 am.

### The swing data: Ohio

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Ohio | 2020 | 1 | 47% / 64% / 95% / 96% | -18.2 | -10.7 | +0.1 | 1 of 1 |
| Ohio | 2022 | 21 | 29% / 56% / 97% / 98% | -18.7 | -6.0 | +0.2 | 12 of 21 |
| Ohio | 2024 | 17 | 41% / 61% / 97% / 98% | -10.2 | -3.1 | +0.1 | 3 of 17 |

#### Biggest moves in competitive races

**Ohio**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 13 | 32.9% / +28.7 | 97.6% / +5.1 | 98.0% / +5.2 | +5.3 | **-23.4** | +0.2 |
| 2022 House 1 | 40.7% / +20.2 | 97.0% / +4.8 | 97.4% / +4.9 | +5.5 | **-14.6** | +0.6 |
| 2024 House 13 | 44.3% / +13.9 | 72.1% / +6.4 | 98.1% / +2.1 | +2.2 | **-11.7** | +0.1 |
| 2022 House 15 | 31.3% / -2.7 | 96.3% / -15.0 | 97.4% / -14.5 | -13.9 | **-11.2** | +0.6 |
| 2022 House 7 | 48.5% / +0.4 | 95.5% / -11.7 | 98.0% / -10.9 | -10.7 | **-11.1** | +0.2 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Ohio 2020 President | OH-G-P-2020-11-03 | Biden (63.6%) | Trump (94.7%) | Trump (96.2%) | Trump +8.0 | 10:00 pm (73.3% in) |
| Ohio 2022 House 7 | OH-G-H-7-2022-11-08 | Diemer (48.5%) | Miller (95.5%) | Miller (98.0%) | Miller +10.7 | 9:42 pm (51.9% in) |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Ohio | midnight ET | 5% | -7.7 | Lucas 0.7% (-5); Franklin 0.5% (+31); Cuyahoga 0.3% (+36); Tuscarawas 0.3% (-12) | 12:00 AM |
| Ohio | 6 am ET | 2% | - (counted after Nov 10, not in the archive) | - | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Ohio | 2026-05-05 | Secretary of State | OH-D-SOS-2026-05-05 | 26.5 / 53.1 / 96.7 / 99.4 | Russo +34.8 | 36.6 | 8:03 pm (21.5%) |
| Ohio | 2026-05-05 | U.S. House | OH-R-H-9-2026-05-05 | 15.4 / 51.2 / 92.9 / 99.7 | Merrin +18.8 | 18.44 | 8:01 pm (13.7%) |
| Ohio | 2026-05-05 | Secretary of State | OH-R-SOS-2026-05-05 | 20.6 / 59.8 / 97.9 / 99.6 | Sprague +40.4 | 39.73 | 8:04 pm (14.7%) |


---

## Michigan: Senate

**Race.**
- Abdul El-Sayed (D) vs Mike Rogers (R); open seat.
- Model: El-Sayed 63.4%. Market: El-Sayed 70%.
- In the Aug 4 primary El-Sayed led Stevens 48.5-47.5 with 96% counted on Wednesday morning, and AP called it just before 10 am Wednesday ✔ ([FOX 2 via Fox 4](https://www.fox4news.com/news/abdul-el-sayed-projected-defeat-haley-stevens-democratic-senate-primary-race.amp)).

**Rules for Nov 3**
- **Polls and early processing:**
  - Polls close 8:00 pm ET. The Central-time part of the Upper Peninsula along the Wisconsin border closes at 9:00 pm ET ✔ (AP Aug 2026). AP doesn't name the counties; Gogebic, Iron, Dickinson and Menominee come from the research notes ◐.
  - Cities and townships of 5,000+ (or county boards) may **process and tabulate absentee ballots 7 am-8 pm on any of the 8 days before Election Day**. Any jurisdiction may do so on the Monday before. No results before 8 pm ✔ ([MCL 168.765a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-168-765a)).
  - Early in-person voting runs at least 9 days ◐.
- **Deadlines:**
  - Absentees are due at 8 pm on Election Day.
  - Military and overseas ballots postmarked by Election Day count if received **within 6 days** ✔ ([MCL 168.759a(18)](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-168-759a)).
- **Canvass and recount:**
  - County canvass by **day 14, Tue Nov 17**. If a county fails, the state board certifies ✔ ([MCL 168.822](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-168-822)).
  - **Automatic statewide recount at a margin of 0.1% or less** of total votes ✔ ([MCL 168.880a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-168-880a)). The old 2,000-vote rule is gone.

**How results are reported.**
- 83 counties and more than 1,500 local clerks report on their own timelines (WDIV, Oct 14 ○).
- The first updates mix mail, early and Election Day votes.
- "Wayne, Oakland, Macomb, Kent, Genesee and Washtenaw counties tend to release relatively few results from any vote type in their first vote updates" ✔ (AP Aug 2026).
- Aug 2024 primary: past halfway at 12:03 am, ~95% by 4:12 am ✔.
- Flint did not pre-process in the Aug 2026 primary, and its results came the next morning ○.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 8:09 pm | 50% | Trump led first; Biden ahead Wed 9:02 am (91% in) | Wed 4:42 pm (NYT) | Biden (D) +2.8 |
| 2020 | Senate | 8:20 pm | 49% | James led first; Peters ahead Wed 1:04 pm (95% in); James ahead Wed 2:13 pm (96% in); Peters ahead Wed 3:52 pm (97% in) | Wed 9:13 pm (NYT) | Peters (D) +1.7 |
| 2022 | Governor | 8:05 pm | 48% | Whitmer led first | Wed 1:26 am (AP) | Whitmer (D) +10.5 |
| 2024 | President | 8:07 pm | 46% | Harris led first; lead traded 10:34 pm-10:38 pm, Trump ahead from 10:38 pm (25% in) (timeline ends 5:40 am Wed) | Wed 12:54 pm (AP) | Trump (R) +1.4 |
| 2024 | Senate | 8:07 pm | 46% | Slotkin led first; Rogers ahead 10:44 pm (25% in); Slotkin ahead Wed 7:31 am (97% in) | Wed 3:12 pm (AP) | Slotkin (D) +0.3 |

What the curves show:

| Race | Early | Overnight | End |
|---|---|---|---|
| 2024 Senate | Slotkin +12.6 at one hour (9% in) | Rogers led from 10:44 pm through the night (−4.6 at 73% in) | Slotkin retook the lead at 7:31 am Wed; AP called it 3:12 pm Wed |
| 2020 Senate | James led | James −19 at two hours after close | Peters went ahead only on Wednesday afternoon |

- Only 46-50% is counted by midnight in every year.

**What to expect** (inference):
- An El-Sayed lead in the first hour or two is likely and means little.
- Rogers may lead late on election night while the rural and Election Day vote outruns Wayne County.
- After midnight the count moved **3.5-13.6 points toward the Democrat** in every top race 2020-2024. Even in 2024, the calmest year, a Rogers lead of 3 points at midnight would have flipped.
- Expect no call before Wednesday unless the margin is wide (2022 Governor, +10.5: 1:26 am).

### The swing data: Michigan

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Michigan | 2020 | 2 | 13% / 24% / 50% / 81% | +20.5 | +20.6 | +7.2 | 2 of 2 |
| Michigan | 2022 | 16 | 7% / 15% / 48% / 93% | +0.6 | +5.3 | +2.0 | 11 of 15 |
| Michigan | 2024 | 15 | 9% / 13% / 46% / 98% | -2.7 | -2.8 | +0.0 | 6 of 10 |

#### Biggest moves in competitive races

**Michigan**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 House 3 | 13.5% / +36.2 | 59.6% / +14.5 | 96.4% / +9.7 | +9.9 | **-26.3** | +0.2 |
| 2022 House 8 | 13.5% / -11.8 | 49.5% / -1.4 | 93.4% / +6.8 | +10.3 | **+22.1** | +3.5 |
| 2020 Senate | 23.8% / -19.2 | 49.2% / -11.9 | 80.1% / -5.6 | +1.7 | **+20.9** | +7.3 |
| 2022 House 7 | 22.2% / -15.5 | 53.6% / -11.3 | 96.9% / +3.5 | +5.4 | **+20.9** | +1.9 |
| 2020 President | 23.3% / -17.6 | 49.8% / -10.6 | 81.9% / -4.3 | +2.8 | **+20.4** | +7.1 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Michigan 2020 President | MI-G-P-2020-11-03 | Trump (23.3%) | Trump (49.8%) | Trump (81.9%) | Biden +2.8 | Wed 9:02 am (90.6% in) |
| Michigan 2020 Senate | MI-G-S-2020-11-03 | James (23.8%) | James (49.2%) | James (80.1%) | Peters +1.7 | Wed 3:52 pm (96.9% in) |
| Michigan 2022 House 7 | MI-G-H-7-2022-11-08 | Barrett (22.2%) | Barrett (53.6%) | Slotkin (96.9%) | Slotkin +5.4 | Wed 2:32 am (95.1% in) |
| Michigan 2022 House 8 | MI-G-H-8-2022-11-08 | Junge (13.5%) | Junge (49.5%) | Kildee (93.4%) | Kildee +10.3 | Wed 12:21 am (52.2% in) |
| Michigan 2024 House 8 | MI-G-H-8-2024-11-05 | - (0.3%) | Junge (29.8%) | McDonald Rivet (100.0%) | McDonald Rivet +6.6 | Wed 12:05 am (32.7% in) |
| Michigan 2024 President | MI-G-P-2024-11-05 | Harris (12.7%) | Trump (46.4%) | Trump (95.6%) | Trump +1.4 | 10:38 pm (24.6% in) |
| Michigan 2024 Senate | MI-G-S-2024-11-05 | Slotkin (12.6%) | Rogers (46.0%) | Rogers (95.7%) | Slotkin +0.3 | Wed 7:31 am (97.5% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Michigan 2024 House 12 | 68.5% | +55.4 | +44.2 | **-11.2** |
| Michigan 2020 Senate | 80.1% | -5.6 | +1.7 | **+7.3** |
| Michigan 2020 President | 81.9% | -4.3 | +2.8 | **+7.1** |
| Michigan 2022 House 12 | 74.5% | +50.3 | +44.6 | **-5.7** |
| Michigan 2022 House 3 | 88.4% | +8.3 | +12.9 | **+4.6** |
| Michigan 2022 House 6 | 86.2% | +27.4 | +31.8 | **+4.4** |
| Michigan 2024 House 4 | 92.8% | -15.7 | -11.7 | **+4.0** |
| Michigan 2022 House 8 | 93.4% | +6.8 | +10.3 | **+3.5** |
| Michigan 2022 House 4 | 95.7% | -14.6 | -11.9 | **+2.7** |
| Michigan 2022 Governor | 93.4% | +8.2 | +10.5 | **+2.3** |
| Michigan 2022 Secretary of State | 93.4% | +11.6 | +13.9 | **+2.3** |
| Michigan 2022 Attorney General | 93.5% | +6.3 | +8.6 | **+2.3** |
| Michigan 2022 House 10 | 96.1% | -2.6 | -0.5 | **+2.1** |
| Michigan 2024 House 10 | 92.3% | -8.1 | -6.1 | **+2.0** |
| Michigan 2022 House 7 | 96.9% | +3.5 | +5.4 | **+1.9** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Michigan | midnight ET | 50% | +15.7 | Wayne 10.8% (+48); Macomb 5.1% (+13); Oakland 4.9% (+27); Kent 2.6% (+31) | 12:00 AM |
| Michigan | 6 am ET | 18% | +35.0 | Wayne 7.3% (+58); Macomb 2.3% (+10); Oakland 1.9% (+26); Kent 1.4% (+50) | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Michigan | 2026-08-04 | U.S. House | MI-D-H-12-2026-08-04 | 1.1 / 15.0 / 40.5 / 94.2 | Tlaib +57.1 | 38.57 | 9:18 pm (13.6%) |
| Michigan | 2026-08-04 | U.S. House | MI-D-H-13-2026-08-04 | 2.4 / 5.6 / 47.9 / 93.0 | McKinney +3.8 | 26.21 | 11:33 pm (47.9%) |
| Michigan | 2026-08-04 | U.S. House | MI-D-H-7-2026-08-04 | 13.2 / 30.1 / 58.4 / 100.0 | Lawrence +14.9 | 5.95 | 8:42 pm (10.1%) |
| Michigan | 2026-08-04 | U.S. Senate | MI-D-S-2026-08-04 | 5.9 / 23.1 / 60.9 / 98.3 | El-Sayed +0.9 | 6.31 | 9:01 pm (15.2%) |


---

## Texas: Senate and Governor

**Races.**

| Race | Candidates | Model | Market |
|---|---|---|---|
| Senate (open) | James Talarico (D) vs Ken Paxton (R). Paxton beat Cornyn in the May 26 runoff ✔ (AP, May 27). | Talarico 55.0% | Talarico 67% |
| Governor | Greg Abbott (R, incumbent) vs Gina Hinojosa (D) | Abbott 74.0% | Abbott 68% |

Both races are on the same ballot and counted together, so everything below applies to both.

**Rules for Nov 3**
- **Polls and early counting:**
  - Polls close 7 pm local: 8:00 pm ET in most of the state, 9:00 pm ET in the westernmost part (AP Mar 2026 ✔). That part is El Paso and Hudspeth counties ◐.
  - **AP will not call a statewide race until 9 pm ET** ✔.
  - Counties over 100,000 people may start counting early ballots after early voting ends. Nothing is released before polls close ◐ (Elec. Code 87.0241; the statute site blocks scripts).
  - **Hard deadlines on the count itself ✔** ([SOS statement, Mar 1 2022](https://www.sos.texas.gov/about/newsreleases/2022/030122.shtml)):
    - All counties must report early and Election Day results **within 24 hours of polls closing**. Precinct records must be delivered within 24 hours under §66.053, and missing that is a misdemeanor.
    - Once counting starts it must continue without stopping until all ballots are counted (§65.002).
    - Harris County still missed the 24-hour deadline in the March 2022 primary.
- **Deadlines ✔** ([SOS Advisory 2026-21](https://www.sos.texas.gov/elections/laws/advisory2026-21-november-3-election-law-calendar.shtml)):

  | Date | Deadline |
  |---|---|
  | Wed Nov 4, 5:00 pm | Domestic mail ballots postmarked by Election Day must arrive |
  | Mon Nov 9 | Other late ballots (military/overseas) |
  | Fri Nov 13 | Voter registrar finishes reviewing provisional ballots |
  | Mon Nov 16 | Last day the early-voting ballot board may meet to qualify late, provisional and corrected ballots |
  | Nov 6-17 | Local canvass window (it must be done by **Tue Nov 17**, which settles the Nov 14 vs Nov 17 conflict in the report) |
  | Sat Nov 21 | Earliest state canvass |

- **Recount:** automatic only on a tie. A losing candidate may request one if within **10% of the leading candidate's vote** ✔ (AP Mar 2026).

**How results are reported.**
- 254 counties.
- Counties release all or nearly all early and absentee results in the first update, before Election Day results ✔ (AP).
- In 2024, 75.8% voted early in person, 3.3% by mail and 20.3% on Election Day ◐ (federal EAC survey).
- Harris County (Houston) counts centrally and has run past midnight; in 2024 its target was 1-2 am ○.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 7:34 pm | 91% | Trump led first; Biden ahead 8:02 pm (10% in); lead traded 9:13 pm-9:29 pm, Trump ahead from 9:29 pm (75% in) | Wed 1:20 am (NYT) | Trump (R) +5.6 |
| 2020 | Senate | 7:35 pm | 91% | Hegar led first; lead traded 8:26 pm-8:31 pm, Cornyn ahead from 8:31 pm (46% in) | 10:07 pm (NYT) | Cornyn (R) +9.6 |
| 2022 | Governor | 8:00 pm | 84% | O’Rourke led first; Abbott ahead 8:37 pm (31% in) | 10:56 pm (AP) | Abbott (R) +10.9 |
| 2024 | President | 8:00 pm | 88% | Harris led first; Trump ahead 8:07 pm (18% in) (timeline ends 5:40 am Wed) | 9:13 pm (AP) | Trump (R) +13.7 |
| 2024 | Senate | 8:00 pm | 88% | Allred led first; lead traded 8:15 pm-8:24 pm, Allred ahead from 8:24 pm (42% in); Cruz ahead 8:34 pm (56% in) | 11:39 pm (AP) | Cruz (R) +8.5 |

What the curves show:
- **Most of the vote arrives in the first hour:** 62-67% was counted one hour after close in 2020 and 2024.
- **The early Democratic lead usually lasts about half an hour, but not always:**
  - 2024 Senate: Allred led until 8:34 pm.
  - 2020 Senate: Hegar led until 8:31 pm.
  - 2022 Governor: O'Rourke led until 8:37 pm.
  - **2020 President: Biden led until 9:29 pm, with 75% counted, and lost by 5.6.**
- **The count keeps moving toward the Republican well after the first hour.** In every top race 2020-2024, what was left moved:

  | From | Share counted then | Rest of the count moved toward the Republican by |
  |---|---|---|
  | 8:30 pm | 25-45% | 8.5-18.6 pts |
  | 9:00 pm | 36-67% | 3.8-6.7 pts |
  | 10:00 pm | 63-79% | 1.9-3.6 pts |
- One odd point: in 2020 NYT recorded first votes at 7:34 pm ET, before polls closed at 8 pm ET. It was a few hundred votes, probably an early county post. Treat 8:00 pm as the real start.

**What to expect** (inference):
- An early Talarico lead means little: Biden was +5.0 at 8:30 pm in 2020 and lost by 5.6.
- Judging from 2020-2024, Talarico needs a lead of about **7+ points at 9:00 pm, or 4+ at 10:00 pm**, to be safe. The same arithmetic applies to Hinojosa against Abbott (O'Rourke 2022 led until 8:37 pm and lost by 10.9).
- A margin under ~2 points likely pushes the call past midnight. Late mail (to Nov 4) and provisionals matter only within ~0.5 points.

### The swing data: Texas

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Texas | 2020 | 2 | 66% / 79% / 91% / 99% | -6.4 | -3.4 | +0.4 | 0 of 2 |
| Texas | 2022 | 41 | 35% / 64% / 82% / 99% | -5.8 | -3.4 | +0.1 | 15 of 41 |
| Texas | 2024 | 33 | 70% / 74% / 88% / 100% | -1.3 | -1.0 | +0.2 | 3 of 33 |

#### Biggest moves in competitive races

**Texas**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 House 15 | 15.0% / -44.9 | 84.6% / -16.7 | 99.7% / -14.3 | -14.2 | **+30.7** | +0.1 |
| 2022 Attorney General | 42.9% / +0.2 | 82.0% / -11.3 | 98.1% / -10.2 | -9.8 | **-10.0** | +0.4 |
| 2022 Agriculture Commissioner | 43.0% / -2.8 | 81.9% / -14.2 | 98.1% / -13.0 | -12.7 | **-9.8** | +0.4 |
| 2022 Lieutenant Governor | 42.9% / -0.5 | 82.0% / -11.8 | 98.1% / -10.7 | -10.3 | **-9.8** | +0.4 |
| 2022 Railroad Commissioner | 43.0% / -5.0 | 81.9% / -16.2 | 98.2% / -15.2 | -14.8 | **-9.8** | +0.4 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Texas 2022 Attorney General | TX-G-attorney_general-2022-11-08 | Garza (42.9%) | Paxton (82.0%) | Paxton (98.1%) | Paxton +9.8 | 10:02 pm (49.7% in) |
| Texas 2024 House 28 | TX-G-H-28-2024-11-05 | Furman (45.8%) | Cuellar (86.1%) | Cuellar (100.0%) | Cuellar +5.6 | 10:34 pm (65.6% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Texas 2022 House 8 | 94.8% | -39.7 | -37.5 | **+2.2** |
| Texas 2022 House 14 | 97.5% | -38.1 | -40.3 | **-2.2** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Texas | midnight ET | 9% | -7.2 | Harris 1.6% (+5); Fort Bend 1.0% (+5); Dallas 0.7% (+25); Travis 0.5% (+18) | 12:00 AM |
| Texas | 6 am ET | 1% | +23.4 | Webb 0.4% (+25); Tarrant 0.2% (+17); Hunt 0.1% (-49); Fort Bend 0.1% (+21) | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
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


---

## Kansas: Senate

**Race.**
- Roger Marshall (R, incumbent) vs Adam Hamilton (D), plus minor candidates.
- Model: Marshall 58.8%. Market: Marshall 62%.

**Rules for Nov 3**
- **Polls:**
  - Polls close 7 pm Central (8:00 pm ET) in most of the state.
  - The four Mountain-time counties (KSN ○; usually listed as Greeley, Hamilton, Sherman and Wallace, not officially confirmed here) close at 6 pm MT by default, 7 pm MT at the latest, so 8:00-9:00 pm ET ✔ ([K.S.A. 25-106](https://www.ksrevisor.gov/statutes/chapters/ch25/025_001_0006.html)).
- **The 3-day mail grace period is back for Nov 3** ✔:
  - The 2025 law (SB 4) that ended it was blocked by a Douglas County judge on July 16, 2026.
  - The Court of Appeals refused to suspend that order on July 27, and the Kansas Supreme Court declined emergency review ([KCTV5](https://www.kctv5.com/2026/07/31/kansas-supreme-court-upholds-mail-ballot-grace-period-ahead-primary-election/)).
  - The Court of Appeals refused again for the general election ([Democracy Docket](https://www.democracydocket.com/news-alerts/gop-bid-to-scrap-kansas-mail-ballot-grace-period-fails-again/)).
  - So ballots **postmarked by Election Day count if they arrive within 3 days (by Fri Nov 6)**.
  - The case is still on appeal; check for news before Nov 3.
- **Canvass and recount:**
  - County canvass on the Monday after (Nov 9), or any business day up to 13 days after (Nov 16) ✔ ([K.S.A. 25-3104](https://www.ksrevisor.gov/statutes/chapters/ch25/025_031_0004.html)).
  - No automatic recount. A candidate may request one in writing by **5 pm the day after the last county canvass**. For a general-election race decided by **0.5% or less**, no bond is required and the state pays ✔ ([K.S.A. 25-3107](https://www.ksrevisor.gov/statutes/chapters/ch25/025_031_0007.html)).

**How results are reported.**
- 105 counties.
- Election-night returns include advance ballots; late mail and provisionals are counted at the canvass ◐.
- **Sedgwick County (Wichita)**, in its Aug 2026 primary notice: "An additional update to the unofficial results is expected to be released Wednesday afternoon. This update will include mail ballots retrieved from drop boxes or polling locations on Election Day. Provisional ballots will be reviewed and counted at the ... Canvass" ✔ ([Sedgwick County](https://www.sedgwickcounty.org/communications/news-releases/final-unofficial-election-night-results-for-2026-primary-election/)).
- Johnson County (Overland Park) posts updates labeled "Advance and Election Day" ✔.
- 2022 primary: first results 8:24 pm, halfway ~10:02 pm, 96% at 3:31 am ✔ (AP Aug 2026).

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 8:09 pm | 80% | Biden led first; Trump ahead 9:34 pm (53% in) | 10:00 pm (NYT) | Trump (R) +14.6 |
| 2020 | Senate | 8:10 pm | 81% | Bollier led first; Marshall ahead 9:39 pm (53% in) | 10:58 pm (NYT) | Marshall (R) +11.4 |
| 2022 | Governor | 8:08 pm | 92% | Kelly led first | Wed 1:24 pm (AP) | Kelly (D) +2.2 |
| 2022 | Senate | 8:08 pm | 92% | Moran led first; Holland ahead 9:09 pm (30% in); Moran ahead 10:05 pm (58% in) | 9:00 pm (AP) | Moran (R) +23.0 |
| 2024 | President | 8:10 pm | 87% | Trump led first; Harris ahead 8:16 pm (6% in); Trump ahead 8:36 pm (8% in); Harris ahead 8:46 pm (30% in); Trump ahead 9:39 pm (47% in) (timeline ends 5:40 am Wed) | 10:39 pm (AP) | Trump (R) +16.1 |

What the curves show:

| Race | Early | Lead changed | Final |
|---|---|---|---|
| 2020 Senate | Bollier +8.1 at one hour (34% in) | Marshall ahead 9:39 pm | Marshall +11.4 |
| 2022 Governor | Kelly +18.1 at one hour (14% in) | Never; called 1:24 pm Wed | Kelly +2.2 |
| 2024 President | Harris ahead with 30% in | Trump ahead 9:39 pm | Trump +16.1 |

- About 80-92% is counted by midnight.
- Late mail under the grace period was roughly 2,000-2,800 ballots in Nov 2024, about 0.2% of the vote (sources conflict ○).

**What to expect** (inference):
- Hamilton will very likely lead until about 10 pm; that tells you little. At 9:30 pm the Democrat led **every** top race 2020-2024, and the rest of the count then moved 17-28 points toward the Republican.
- Even at 10:00 pm a Democratic lead wasn't safe: Holland led the 2022 Senate race then (39% counted) and lost by 23.
- At 10:30 pm (about two-thirds counted) the rest still moved 4-8 points toward the Republican. Hamilton needs a lead of about **8+ points at 10:30 pm** to be in good shape (Kelly 2022 was +9.2 then and won by 2.2).
- A margin of ~5+ points has been called on election night. A margin of 2-3 points may wait until Wednesday.

### The swing data: Kansas

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Kansas | 2020 | 2 | 35% / 57% / 80% / 92% | -20.4 | -8.7 | -0.5 | 2 of 2 |
| Kansas | 2022 | 10 | 13% / 23% / 93% / 97% | -18.0 | -18.9 | +0.7 | 10 of 10 |
| Kansas | 2024 | 5 | 30% / 58% / 87% / 96% | -9.0 | -10.6 | +0.4 | 3 of 5 |

#### Biggest moves in competitive races

**Kansas**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 Treasurer | 13.2% / +9.3 | 93.4% / -11.8 | 98.1% / -13.4 | -12.8 | **-22.0** | +0.7 |
| 2022 Attorney General | 13.2% / +18.1 | 93.5% / -0.7 | 98.1% / -2.4 | -1.7 | **-19.7** | +0.7 |
| 2022 Governor | 24.5% / +20.3 | 92.1% / +3.0 | 96.7% / +1.5 | +2.2 | **-18.1** | +0.8 |
| 2022 House 3 | 51.7% / +24.0 | 95.7% / +12.2 | 96.9% / +11.7 | +12.2 | **-11.9** | +0.5 |
| 2020 Senate | 56.2% / -2.7 | 81.0% / -10.9 | 91.7% / -11.0 | -11.4 | **-8.7** | -0.4 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Kansas 2022 Attorney General | KS-G-attorney_general-2022-11-08 | Mann (13.2%) | Kobach (93.5%) | Kobach (98.1%) | Kobach +1.7 | 11:37 pm (91.6% in) |
| Kansas 2022 House 1 | KS-G-H-1-2022-11-08 | Beard (21.3%) | Mann (86.3%) | Mann (96.1%) | Mann +35.3 | 10:05 pm (41.9% in) |
| Kansas 2022 House 2 | KS-G-H-2-2022-11-08 | Schmidt (26.8%) | LaTurner (91.9%) | LaTurner (97.3%) | LaTurner +15.3 | 10:14 pm (56.2% in) |
| Kansas 2022 Senate | KS-G-S-2022-11-08 | Holland (38.8%) | Moran (92.3%) | Moran (96.6%) | Moran +23.0 | 10:05 pm (58.0% in) |
| Kansas 2022 Treasurer | KS-G-treasurer-2022-11-08 | Rogers (13.2%) | Johnson (93.4%) | Johnson (98.1%) | Johnson +12.8 | 10:05 pm (54.1% in) |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Kansas | midnight ET | 20% | -23.2 | Douglas 4.2% (+39); Sedgwick 1.4% (+9); Finney 0.8% (-25); Geary 0.7% (-15) | 12:00 AM |
| Kansas | 6 am ET | 8% | -33.3 | Sedgwick 1.4% (+9); Lyon 0.5% (-37); Neosho 0.3% (-65); Johnson 0.3% (+12) | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Kansas | 2026-08-04 | Governor | KS-D-G-2026-08-04 | 36.3 / 59.1 / 91.8 / 97.4 | Holscher +10.1 | 6.98 | 8:18 pm (26.4%) |
| Kansas | 2026-08-04 | Governor | KS-R-G-2026-08-04 | 21.7 / 50.4 / 88.4 / 98.3 | Masterson +20.8 | 20.57 | 8:19 pm (10.6%) |


---

## Maine: Senate (ranked-choice)

**Race and ballot.**
- Troy Jackson (D) vs Susan Collins (R, incumbent).
- Model: Jackson 71.6%. Market: Jackson 66%.
- Only Collins and Jackson are printed on the ballot.
- **Six declared write-in candidates make this a ranked-choice race** ✔ (Spectrum News, Aug 26): Andrews, Olson, Oswald, Steinberger, Turcotte, Webb.
- Votes for an undeclared write-in, such as Graham Platner (who withdrew July 10), count as blank ✔.
- The 2025 voter-ID referendum (Question 1) failed about 64-36, so absentee rules are unchanged ✔.

**Rules for Nov 3**
- Polls close 8:00 pm. Absentees are due at poll close.
- Absentees must reach the town clerk "before the polls are closed" ✔ ([§755](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec755.html)).
- Towns may opt to process absentees from the 7th day before Election Day, with notice at least 30 days ahead. Ballots "may not be counted ... and election results may not be obtained or released until after the polls have closed" ✔ ([§760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html)).
- **Majority rule ✔** ([21-A §723-A](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec723-A.html)):
  - A first-round win needs first choices on **"more than 50% of all ballots cast for the particular office,"** counting ballots whose first choice is blank or overvoted.
  - So blanks and write-ins pull a two-way leader under 50%. In 2024 ME-02 that forced a ranked-choice round ◐.
- **If no one has a majority:**
  - Memory devices and ballots from every town go to Augusta.
  - The Secretary of State runs the ranked-choice count, livestreamed, in about a week ◐.
- The Secretary of State tabulates and certifies to the Governor **within 20 days** ✔ ([§722](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec722.html)).
- **Recount requests:**
  - Due within 5 business days after the election. In ranked-choice races only the top 3 may request one ✔ ([§737-A](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec737-A.html)).
  - No deposit and no charge if the margin is 1% or less of the total votes, or not more than 1,000 votes, whichever is less ✔.
  - Automatic only on a tie (2025 law, per AP Jun 2026 ✔; not found in §737-A itself).

**How results are reported.**
- About 500 municipalities count and report on their own; there is no live state feed.
- AP and the Bangor Daily News collect town results ○. Clerks must file the attested return with the Secretary of State **within 2 business days**; after 5 pm on day 2 the state may send a courier ✔ ([§711](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec711.html)).
- 2024 general: first results 8:44 pm, ~50% by 12:54 am, counting stopped 4:11 am, ~90% by 3:13 pm Wednesday ✔ (AP Jun 2026).

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 8:34 pm | 42% | Trump led first; lead traded 9:55 pm-10:07 pm, Biden ahead from 10:07 pm (12% in); Trump ahead 10:19 pm (13% in); Biden ahead 11:02 pm (26% in) | Wed 3:06 am (NYT) | Biden (D) +9.1 |
| 2020 | Senate | 8:37 pm | 29% | Collins led first | Wed 1:52 pm (NYT) | Collins (R) +8.6 |
| 2022 | Governor | 8:08 pm | 63% | Mills led first | Wed 1:01 am (AP) | Mills (D) +13.2 |
| 2024 | President | 8:44 pm | 33% | Trump led first; Harris ahead 10:29 pm (11% in) (timeline ends 5:40 am Wed) | Wed 4:23 pm (AP) | Harris (D) +6.9 |
| 2024 | Senate | 8:44 pm | 33% | King led first | Nov 7 (AP) | King (I) +17.4 |

What the curves show:
- Maine is the slowest of the in-person states: 29-63% counted by midnight.
- In every race in our data, the count moved **toward the non-Republican after the first two hours**:

  | Race | Change after the first two hours |
  |---|---|
  | 2020 Senate | +7.7 |
  | 2022 Governor | +5.4 |
  | 2024 Senate | +4.2 |
  | 2020 President | +7.9 |
  | 2024 President | +7.4 |

  This corrects the report, which guessed Maine would show no pattern.

**Ranked-choice timing, past races** (2022, 2024 ✔; 2018 ◐)

| Race | Result date |
|---|---|
| 2018 ME-02 | Nov 15 |
| 2022 ME-02 | Nov 16, after tabulation on Nov 15 |
| 2024 ME-02 | Nov 15 (Golden 50.35%); a recount followed |

In all three, the first-round leader won. But in the **June 2026 Democratic governor primary**, Shah led the first round 58,551-50,492 and **Pingree won the ranked-choice count 111,750-86,950** (NYT results file). A first-round lead short of 50% is not safe. In the Senate race only two names are printed, so transfers come only from write-ins and blanks, and a reversal is far less likely than in a multi-candidate primary.

**What to expect** (inference):
- Collins will likely look better early than at the end.
- If Jackson leads first choices but sits under 50% of all ballots, expect the ranked-choice count around Nov 11-13.
- The write-ins are tiny, so the ranked-choice count mostly confirms the first-round leader.
- A margin under 1% adds a free recount request and pushes the result into late November.

### The swing data: Maine

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Maine | 2020 | 2 | 2% / 9% / 35% / 71% | - | +7.8 | -3.0 | 2 of 2 |
| Maine | 2022 | 3 | 2% / 21% / 63% / 83% | +12.3 | +5.4 | -0.0 | 2 of 3 |
| Maine | 2024 | 6 | 1% / 5% / 33% / 72% | - | +7.4 | -1.7 | 3 of 5 |

#### Biggest moves in competitive races

**Maine**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2020 President | 10.5% / +1.2 | 41.8% / +5.4 | 73.1% / +12.3 | +9.1 | **+7.9** | -3.2 |
| 2022 House 2 [RCV, 1st round] | 24.3% / -3.0 | 63.6% / +3.0 | 81.8% / +4.6 | +3.7 | **+6.8** | -0.8 |
| 2022 Governor | 21.3% / +7.9 | 63.1% / +9.4 | 83.2% / +13.2 | +13.2 | **+5.4** | -0.0 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Maine 2022 House 2 [RCV, 1st round] | ME-G-H-2-2022-11-08 | Poliquin (24.3%) | Golden (63.6%) | Golden (81.8%) | Golden +3.7 | 10:02 pm (30.8% in) |
| Maine 2024 House 2 [RCV, 1st round] | ME-G-H-2-2024-11-05 | - (5.9%) | Theriault (34.0%) | Golden (72.3%) | Golden +0.6 | Wed 2:02 am (62.1% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Maine 2020 President | 73.1% | +12.3 | +9.1 | **-3.2** |
| Maine 2020 Senate | 69.7% | -5.9 | -8.6 | **-2.7** |
| Maine 2024 House 1 | 71.4% | +24.8 | +22.3 | **-2.6** |
| Maine 2024 President (district 1) | 71.3% | +23.9 | +21.8 | **-2.1** |
| Maine 2024 President | 73.2% | +8.8 | +6.9 | **-1.8** |
| Maine 2024 President (district 2) | 73.3% | -7.9 | -9.5 | **-1.6** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Maine | midnight ET | 58% | +13.5 | Cumberland 15.6% (+41); York 10.0% (+17); Penobscot 5.4% (-10); Kennebec 4.2% (+0) | 12:00 AM |
| Maine | 6 am ET | 27% | +2.5 | York 4.3% (+8); Cumberland 3.5% (+17); Penobscot 2.0% (-28); Sagadahoc 1.8% (+12) | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Maine | 2026-06-09 | Governor | ME-D-G-2026-06-09 | 0.7 / 18.0 / 59.1 / 83.4 | Shah +3.7 (1st round) **- Pingree won the ranked-choice count** | 0.4 | 9:56 pm (16.9%) |
| Maine | 2026-06-09 | U.S. Senate | ME-D-S-2026-06-09 | 0.7 / 17.6 / 61.6 / 83.2 | Platner +52.9 | 54.43 | 9:35 pm (10.0%) |
| Maine | 2026-06-09 | Governor | ME-R-G-2026-06-09 | 1.4 / 16.7 / 56.2 / 77.6 | Charles +18.0 (1st round) | 22.24 | 9:43 pm (10.5%) |


---

## Iowa: Senate

**Race.**
- Ashley Hinson (R) vs Josh Turek (D); open seat after Ernst retired ✔ (AP Jun 2026).
- Model: Hinson 68.2%. Market: Hinson 57%. The market is much less sure than the model.

**Rules for Nov 3 ✔**
- **Polls and deadlines:**
  - Polls close 8 pm CT (9:00 pm ET).
  - Absentees must be **received before the polls close**; there is no postmark rule ([Iowa Code 53.17](https://www.legis.iowa.gov/docs/code/53.17.pdf)).
- **Absentee counting** ([53.23](https://www.legis.iowa.gov/docs/code/53.23.pdf)):
  - One absentee board per county, staffed to finish **by 10:00 pm CT** (11:00 pm ET).
  - The board "shall not release the results of its tabulation on election day until all of the ballots it is required to count on that day have been counted," so each county's absentees land as one batch ✔.
  - A county that missed 10:00 pm at the last general election must start counting absentees the day before (Mon Nov 2), and still release nothing until Election Day ✔.
- **Canvass and recount:**
  - County canvass: **first Tuesday after the election, Nov 10** ([50.24](https://www.legis.iowa.gov/docs/code/50.24.pdf)).
  - State canvass within 27 days, by Nov 30 ([50.38](https://www.legis.iowa.gov/docs/code/50.38.pdf)).
  - Recount: for statewide or federal office, the state orders one on a written request **only if the margin is under 0.15%**. The request is due 5 pm the day after the county canvass ([50.48](https://www.legis.iowa.gov/docs/code/50.48.pdf)). That day is Nov 11, Veterans Day; whether the holiday moves the deadline is not settled.

**How results are reported.**
- 99 counties.
- "Nearly all counties release the results of absentee-by-mail voting at the start of the night"; counties vary on in-person absentee ✔ (AP Jun 2026).
- 2022 primary: first results 9:12 pm, last update 2:29 am ✔.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 10:13 pm | 86% | Biden led first; Trump ahead 11:29 pm (71% in) | Wed 12:25 am (NYT) | Trump (R) +8.2 |
| 2020 | Senate | 10:14 pm | 87% | Greenfield led first; Ernst ahead 11:29 pm (66% in) | Wed 12:38 am (NYT) | Ernst (R) +6.6 |
| 2022 | Governor | 9:10 pm | 95% | Reynolds led first; DeJear ahead 9:34 pm (5% in); Reynolds ahead 10:09 pm (32% in) | 9:00 pm (AP) | Reynolds (R) +18.5 |
| 2022 | Senate | 9:10 pm | 95% | Franken led first; Grassley ahead 10:19 pm (41% in) | 11:03 pm (AP) | Grassley (R) +12.2 |
| 2024 | President | 9:02 pm | 90% | Harris led first; Trump ahead 10:03 pm (34% in) (timeline ends 5:40 am Wed) | 10:40 pm (AP) | Trump (R) +13.3 |

What the curves show:
- **The Democrat leads early every time, then the lead ends between 10:00 and 11:30 pm:**

  | Race | Early lead | Lead ended | Final |
  |---|---|---|---|
  | 2020 Senate | Greenfield | 11:29 pm | Ernst +6.6 |
  | 2022 Senate | Franken +15.5 at one hour | 10:19 pm | Grassley +12.2 |
  | 2024 President | Harris +15.3 at one hour | 10:03 pm | Trump +13.3 |

- About 86-95% is counted by midnight. Almost nothing changes after election night.
- First votes come within minutes of the close: 9:02-9:12 pm in 2022/2024 and 10:13 pm in 2020. **Iowa's polls closed an hour later until 2021** (9 pm CT, 10 pm ET); SF 413 moved the close to 8 pm CT from 2022 ✔ ([KCRG](https://www.kcrg.com/2021/03/08/gov-reynolds-signs-election-reform-bill-limiting-length-of-absentee-election-day-voting/)). So 2020 was not a slow year: its first votes came 13 minutes after its close.
- That also means 2020's "midnight" was only 2 hours after the close. The 86-87% counted by then is the same pace as 2022/2024.

**What to expect** (inference):
- Turek will lead early, likely by double digits.
- The meaningful read is at about 11:00 pm. At 10:30 pm (about half counted) the rest still moved 4-9 points toward the Republican in 2022/2024. By 11:00 pm (three-quarters counted) it moved under 2 points.
- With 86-95% counted by midnight, a call is likely on election night unless the margin is under ~1-2 points.

### The swing data: Iowa

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Iowa | 2020 | 2 | 49% / 87% / 87% / 100% | -18.6 | -2.2 | -0.4 | 0 of 2 |
| Iowa | 2022 | 11 | 24% / 71% / 94% / 100% | -28.5 | -2.2 | -0.0 | 2 of 11 |
| Iowa | 2024 | 5 | 10% / 75% / 90% / 99% | -14.0 | +0.5 | +0.0 | 2 of 5 |

#### Biggest moves in competitive races

**Iowa**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 1 | 59.9% / +0.6 | 97.2% / -6.8 | 98.6% / -6.6 | -6.8 | **-7.4** | -0.2 |
| 2024 House 1 | 74.0% / -5.6 | 87.7% / +1.5 | 98.6% / -0.1 | -0.2 | **+5.4** | -0.1 |
| 2024 House 3 | 89.8% / -0.5 | 95.4% / -2.2 | 99.9% / -3.9 | -3.8 | **-3.3** | +0.0 |
| 2020 President | 86.1% / -5.5 | 86.1% / -5.5 | 99.7% / -7.3 | -8.2 | **-2.7** | -0.9 |
| 2022 House 3 | 94.2% / +1.8 | 99.8% / -0.7 | 99.8% / -0.7 | -0.7 | **-2.5** | -0.0 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Iowa 2022 Attorney General | IA-G-attorney_general-2022-11-08 | Miller (71.1%) | Bird (94.3%) | Bird (99.6%) | Bird +1.7 | 11:10 pm (79.5% in) |
| Iowa 2022 Auditor | IA-G-auditor-2022-11-08 | Sand (71.1%) | Halbur (94.3%) | Sand (99.6%) | Sand +0.2 | Wed 2:01 am (99.6% in) |
| Iowa 2022 House 1 | IA-G-H-1-2022-11-08 | Bohannan (59.9%) | Miller-Meeks (97.2%) | Miller-Meeks (98.6%) | Miller-Meeks +6.8 | 11:04 pm (61.9% in) |
| Iowa 2022 House 3 | IA-G-H-3-2022-11-08 | Axne (94.2%) | Nunn (99.8%) | Nunn (99.8%) | Nunn +0.7 | 11:24 pm (98.6% in) |
| Iowa 2024 House 1 | IA-G-H-1-2024-11-05 | Miller-Meeks (74.0%) | Bohannan (87.7%) | Miller-Meeks (98.6%) | Miller-Meeks +0.2 | Wed 12:25 am (96.8% in) |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Iowa | midnight ET | 14% | -25.8 | Story 3.0% (+17); Jasper 1.2% (-22); Pottawattamie 1.1% (-48); Wapello 0.6% (-29) | 12:00 AM |
| Iowa | 6 am ET | under 0.5% | - | - | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Iowa | 2026-06-02 | U.S. Senate | IA-D-S-2026-06-02 | 47.3 / 91.7 / 99.8 / 100.0 | Turek +25.3 | 25.03 | 9:20 pm (24.0%) |
| Iowa | 2026-06-02 | Governor | IA-R-G-2026-06-02 | 34.4 / 90.8 / 99.6 / 100.0 | Lahn +0.8 | 0.82 | 9:19 pm (12.5%) |
| Iowa | 2026-06-02 | U.S. Senate | IA-R-S-2026-06-02 | 33.7 / 92.7 / 99.5 / 99.9 | Hinson +48.4 | 49.2 | 9:19 pm (13.0%) |


---

## Nebraska: Senate

**Race.**
- Pete Ricketts (R, incumbent) vs Dan Osborn (Independent).
- **No Democrat on the ballot:**
  - Nominee Cindy Burbank filed to withdraw on July 17, and the Secretary of State confirmed her removal on July 21.
  - The state Democratic Party voted not to fill the vacancy; party chair Jane Kleeb endorsed Osborn (Ballotpedia, Nebraska Examiner, WOWT ○).
  - Before the primary, Burbank said she would back Osborn if she had no path to victory.
  - Our forecast data also has no Democrat.
- Model: Ricketts 62.2%. Market: Ricketts 74%.

**Rules for Nov 3 ✔**
- **Polls:** close 8 pm Central and 7 pm Mountain, so **9:00 pm ET everywhere** ([Neb. Rev. Stat. 32-908](https://nebraskalegislature.gov/laws/statutes.php?statute=32-908)).
- **Early ballots:** due at poll close.
  - Counting boards may convene no earlier than the second Friday before the election and may open approved envelopes from that day (Fri Oct 23) ✔.
  - They may begin counting "no earlier than twenty-four hours prior to the opening of the polls" ✔ ([32-1027](https://nebraskalegislature.gov/laws/statutes.php?statute=32-1027)).
- **Voter ID:** voters without photo ID vote provisionally and must present ID to the county by the **Tuesday after the election, Nov 10** ✔ (§32-1002.01, read via an unofficial statute mirror).
- **Recount:**
  - Automatic when the margin is **1% or less of the votes received by the leading candidate** (offices with more than 500 votes cast) ([32-1119](https://nebraskalegislature.gov/laws/statutes.php?statute=32-1119)).
  - AP's summary, "1% of the total vote," is slightly wrong; use the statute.
- **State canvass:** fourth Monday after the election, **Mon Nov 30** ([32-1037](https://nebraskalegislature.gov/laws/statutes.php?statute=32-1037)).

**How results are reported.**
- 93 counties.
- "More than three-quarters" of counties release all or nearly all early votes in the first update, often before any Election Day votes.
- "Nearly two-thirds" of counties, **including Douglas (Omaha) and Lancaster (Lincoln)**, release few or no Election Day votes in their first report ✔ (AP May 2026).
- Douglas County had about **18,000 ballots uncounted after election night** in one recent general (likely 2024). They included 4,600 provisionals and 7,400 drop-box ballots from Election Day, and were counted in the days after ✔ (3 News Now; the article is undated).

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 9:07 pm | 62% | Trump led first; Biden ahead 9:19 pm (26% in); Trump ahead 9:35 pm (28% in) | 9:01 pm (NYT) | Trump (R) +19.1 |
| 2020 | Senate | 9:08 pm | 65% | Sasse led first | 9:01 pm (NYT) | Sasse (R) +38.3 |
| 2022 | Governor | 9:07 pm | 74% | Blood led first; Pillen ahead 9:51 pm (39% in) | 11:52 pm (AP) | Pillen (R) +23.4 |
| 2024 | President | 9:00 pm | 61% | Harris led first; Trump ahead 10:20 pm (44% in) (timeline ends 5:40 am Wed) | 9:01 pm (AP) | Trump (R) +20.6 |
| 2024 | Senate | 9:00 pm | 61% | Osborn led first; lead traded 11:15 pm-11:25 pm, Fischer ahead from 11:25 pm (57% in) | Wed 12:06 am (AP) | Fischer (R) +6.7 |

What the curves show:
- **2024 Senate:** Osborn led the 9:00 pm first update by **18 points with 25% counted** and was +9.5 one hour after close. Fischer took the lead at ~11:25 pm and won by 6.7; the call came 12:06 am.
- The report said there was "no evidence the 2024 first batch was Osborn-led statewide." The data shows it was; that statement was wrong.
- Only 61-74% is counted by midnight.

**What to expect** (inference):
- Osborn will likely lead the first hour or two. Ricketts gains as rural Election Day precincts report.
- An Osborn lead at 11:30 pm (55-60% counted) is not safe. After 11:30 pm the rest moved 2-11 points toward the Republican in every top race; 2024 Senate moved 6.3 (Osborn +1.5 at 11:00 pm, lost by 6.7).
- After midnight it still moved 2-9 points. Osborn needs a lead of roughly **9+ points at midnight** to be safe.
- Douglas County's leftover ballots favor Osborn and are counted later in the week.

### The swing data: Nebraska

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Nebraska | 2020 | 2 | 34% / 49% / 62% / 88% | -12.8 | -8.7 | +0.1 | 1 of 2 |
| Nebraska | 2022 | 7 | 39% / 50% / 74% / 96% | -13.0 | -6.9 | +1.1 | 6 of 7 |
| Nebraska | 2024 | 8 | 32% / 47% / 59% / 95% | -15.3 | -7.0 | +0.4 | 6 of 8 |

#### Biggest moves in competitive races

**Nebraska**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 President (district 1) | 44.1% / +1.3 | 55.7% / -1.9 | 94.8% / -13.4 | -13.0 | **-14.3** | +0.3 |
| 2024 Senate | 50.1% / +1.5 | 61.4% / -1.9 | 96.1% / -7.6 | -6.7 | **-8.2** | +0.9 |
| 2024 President (district 2) | 70.7% / +9.9 | 76.2% / +8.4 | 94.0% / +4.2 | +4.6 | **-5.3** | +0.4 |
| 2024 House 2 | 70.9% / +2.5 | 76.4% / +1.2 | 94.0% / -2.4 | -1.9 | **-4.4** | +0.5 |
| 2022 House 2 | 67.4% / +0.0 | 77.4% / -1.7 | 93.4% / -4.4 | -2.7 | **-2.7** | +1.7 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Nebraska 2022 House 2 | NE-G-H-2-2022-11-08 | Vargas (67.4%) | Bacon (77.4%) | Bacon (93.4%) | Bacon +2.7 | 11:43 pm (67.5% in) |
| Nebraska 2024 House 2 | NE-G-H-2-2024-11-05 | Vargas (70.9%) | Vargas (76.4%) | Bacon (94.0%) | Bacon +1.9 | Wed 2:46 am (83.8% in) |
| Nebraska 2024 Initiative | NE-I-83085-NE-2024-11-05 | Against (50.1%) | For (61.4%) | For (96.1%) | For +9.9 | 11:00 pm (50.6% in) |
| Nebraska 2024 Initiative | NE-I-83084-NE-2024-11-05 | For (50.1%) | For (61.4%) | Against (96.1%) | Against +2.0 | Wed 1:26 am (79.6% in) |
| Nebraska 2024 President (district 1) | NE-G-P-CD_1-2024-11-05 | Harris (44.1%) | Trump (55.7%) | Trump (94.8%) | Trump +13.0 | 11:20 pm (52.7% in) |
| Nebraska 2024 Senate | NE-G-S-2024-11-05 | Osborn (50.1%) | Fischer (61.4%) | Fischer (96.1%) | Fischer +6.7 | 11:25 pm (57.1% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Nebraska 2020 Senate | 84.6% | -40.1 | -38.3 | **+1.8** |
| Nebraska 2022 House 2 | 93.4% | -4.4 | -2.7 | **+1.7** |
| Nebraska 2020 President | 92.1% | -17.5 | -19.1 | **-1.6** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Nebraska | midnight ET | 30% | -44.1 | Douglas 5.0% (-10); Lancaster 2.6% (-23); Scotts Bluff 1.6% (-44); Platte 1.6% (-56) | 12:00 AM |
| Nebraska | 6 am ET | 5% | -31.7 | Platte 1.6% (-56); Douglas 1.2% (+8); Sarpy 0.2% (-35); Dakota 0.1% (-45) | 5:52 AM |


---

## Nevada: Governor

**Race.**
- Joe Lombardo (R, incumbent) vs Aaron D. Ford (D, attorney general). Also on the ballot: Danielle Ford (no party) and the "None of these candidates" line ◐ ([Clark County Fall 2026 newsletter](https://www.clarkcountynv.gov/adobe/assets/urn:aaid:aem:228bc80b-da3b-42da-bc72-25cce75470d1/original/as/cced-newsletter-fall2026.pdf)).
- Model: Lombardo 69.5%. Market: Lombardo 34%. **The market favors Ford; the model favors Lombardo.** That is the largest model-market disagreement on this list.
- "None of these candidates" votes are posted in every result but never decide the winner; only votes for named candidates count ✔ ([NRS 293.269](https://www.leg.state.nv.us/NRS/NRS-293.html)). The researcher found no majority or runoff rule, so it's a plurality race ◐.
- No Senate race in Nevada this year. NV-1, NV-3 and the down-ballot statewide races come out of the same county batches.
- Latest public poll found: Noble Predictive Insights (Oct 7-13) Lombardo 40, Ford 37, 23% undecided ○ ([KTNV](https://www.ktnv.com/news/new-poll-shows-lombardo-has-slight-lead-in-2026-governor-matchup)).

**Rules for Nov 3 ✔** ([NRS chapter 293](https://www.leg.state.nv.us/NRS/NRS-293.html), revised 9/9/2026, re-read 2026-10-22)
- **Polls:**
  - Open 7 am-7 pm PT, so they close at **10:00 pm ET** (293.273).
  - Voters in line at 7 pm still vote (293.305).
- **Nothing is released until everyone has voted.** "No voting results of mail ballots may be released until all polling places are closed and all votes have been cast on the day of the election"; releasing them early is a misdemeanor (293.269935(3)).
  - So the first numbers wait for the last voter in line anywhere in the state.
  - Clark County: results are "available ... after the Nevada Secretary of State has indicated all statewide voting has finished" ◐ ([Clark 2026 election page](https://www.clarkcountynv.gov/government/departments/elections/26g-info)).
- **Mail ballots** (293.269921):
  - Dropped off by poll close, or postmarked by Election Day and received by **5 pm PT Sat Nov 7** (8 pm ET).
  - No readable postmark: received by **5 pm PT Fri Nov 6**.
- **Other deadlines:**
  - Signature cure by **5 pm PT Mon Nov 9**, the 6th day (293.269927(6)).
  - Mail counting may start 15 days before (Mon Oct 19) and **must be finished by the 7th day after, Tue Nov 10** (293.269931).
  - Provisional ballots are never in the election-night results. Envelopes stay sealed until 8 am Wed Nov 4, and voter ID is due **5 pm Fri Nov 6** (293.3085). Same-day registrants vote provisionally ◐ ([Clark 2026 dates](https://www.clarkcountynv.gov/adobe/assets/urn:aaid:aem:a5950eb8-cb6d-404e-a533-b4856da8aa86/original/as/2026-dates.pdf)).
- **Canvass and recount:**
  - County canvass by the 10th day, **Fri Nov 13** (293.387).
  - Statewide canvass by the Supreme Court justices on the 4th Tuesday, **Tue Nov 24** (293.395).
  - **No automatic recount** (none found by the researcher ◐). A defeated candidate may demand one, prepaying the cost, within 3 working days of the canvass (293.403). That's **5 pm Tue Dec 1** after the Thanksgiving and Family Day holidays ◐ (Clark's calendar).
  - A recount must start within 5 days of the demand and finish within 5 days of starting (293.405).
- **What changed since 2024:**
  - Nothing in the counting rules: 2022 and 2024 ran on the same clock (AB 321, 2021). 2020 did not; it had a 7-day mail window ○.
  - 2025 bills on voter ID and stricter mail deadlines were vetoed ○ ([Nevada Independent](https://thenevadaindependent.com/article/how-different-will-nevadas-elections-look-in-2026)).
  - The state Supreme Court upheld counting no-postmark ballots on Oct 28, 2024 ○. *Watson v. RNC* keeps the 4-day window for federal races too ✔.
  - New: Clark County in-person voters mark on a device, print a paper ballot and scan it ◐. Officials expect fewer unclear marks to adjudicate. It was first used statewide in the June 2026 primary, so it's untested at general-election turnout ○.

**How results are reported.**
- 16 counties plus Carson City. **Clark (Las Vegas) cast 69% of the 2020 vote** ◐ (AP 2020 preview). It was 66% of the 2026 early ballots by Oct 20, with Washoe (Reno) 21% and the rural counties 13% ○ ([Nevada Independent](https://thenevadaindependent.com/article/the-early-voting-blog-2026-general)).
- **Election night:**
  - The first release is early in-person votes plus mail processed before Election Day.
  - Election Day in-person votes come overnight; Clark's 2024 overnight update came at 1:32 am PT ○.
- **Election Day drop-offs are not counted on election night.** "Clark is not counting drop boxes tonight," a Secretary of State spokeswoman said in 2022 ○. Clark's Election Day drop-off pile was about 54,000-57,000 in 2022 and 2024 ○.
- **Ballots left after election night:**
  - 2022: more than 144,000 in Clark and Washoe 18 hours after polls closed ○.
  - 2024: about 112,000 on Wednesday, including about 12,000 Clark ballots needing cures ○.
- **After election night:**
  - Washoe posts "by noon and 5 p.m. each day" PT (3 pm and 8 pm ET) ○ ([This Is Reno](https://thisisreno.com/2026/10/washoe-voting-mail-ballot-delays/)).
  - Clark has no 2026 schedule yet. In 2024 it posted "by 8 p.m." PT (11 pm ET) Thursday to Saturday; the decisive 2022 Saturday drop came at about 9:15 pm ET ○.
  - After the June 2026 primary the Secretary of State published each county's outstanding ballots ○. If it does so again in November, that is the best live gauge of what's left.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 11:53 pm | 0% | Trump led first; Biden ahead Wed 1:32 am (58% in) | Nov 7 (NYT) | Biden (D) +2.4 |
| 2022 | Governor | Wed 12:41 am | 0% | Sisolak led first; Lombardo ahead Wed 3:35 am (73% in) | Nov 11 (AP) | Lombardo (R) +1.5 |
| 2022 | Senate | Wed 12:41 am | 0% | Cortez Masto led first; Laxalt ahead Wed 3:57 am (76% in); Cortez Masto ahead Nov 12 (97% in) | Nov 12 (AP) | Cortez Masto (D) +0.8 |
| 2024 | President | Wed 12:55 am | 0% | Trump led first (timeline ends 5:40 am Wed) | Nov 9 (AP) | Trump (R) +3.1 |
| 2024 | Senate | Wed 12:54 am | 0% | Brown led first; Rosen ahead Wed 1:02 am (69% in); Brown ahead Wed 1:44 am (71% in); Rosen ahead Nov 7 (92% in) | Nov 9 (AP) | Rosen (D) +1.6 |

What the curves show:

| Race | End of election night (6 am ET) | Final | Move after election night |
|---|---|---|---|
| 2022 Senate | Laxalt +2.7 (82% in) | Cortez Masto +0.8 | +3.5 toward D. She took the lead for good at 9:14 pm ET Saturday, with 97% counted |
| 2022 Governor | Lombardo +4.7 | Lombardo +1.5 | +3.2 toward D |
| 2024 Senate | Brown +0.1 (87% in) | Rosen +1.6 | +1.7 toward D; Rosen led for good from 2:47 am ET Thursday (Wednesday night in Nevada) |
| 2024 President | Trump +4.7 | Trump +3.1 | +1.6 toward D |
| 2020 President | Biden +0.6 (85% in) | Biden +2.4 | +1.8 toward D |

- First votes came 11:53 pm-12:55 am ET in 2020-2024. The first big drop (44-78% of the vote) came around 1-2 am.
- In 2022 that drop leaned Democratic (Senate +12.6 with 44% in), and Election Day votes pulled it to Laxalt by about 4 am. In 2024 it was about even.
- **Every statewide race since 2020, and 17 of 18 races overall, moved toward the Democrat after election night** (`SWINGS.md`). In votes, the tail moved the Senate margin by about 27,000-31,000 in 2022 and 24,000-25,000 in 2024 (report).
- AP called the close races on day 3 or 4: 2020 President Sat 12:13 pm; 2022 Governor Fri evening; 2022 Senate Sat night; 2024 Senate and President 12:15 am Sat ◐.

**After election night** (PT; ET is 3 hours later)

| Date | Event |
|---|---|
| Wed Nov 4, 8 am | Provisional envelopes may be opened |
| Wed-Sat | Clark's Election Day drop-offs and late mail; Washoe at noon and 5 pm each day |
| Fri Nov 6, 5 pm | Deadline for mail with no readable postmark, and for provisional voters' ID |
| Sat Nov 7, 5 pm | Deadline for postmarked mail |
| Mon Nov 9, 5 pm | Signature cure deadline; cured ballots post Tue-Thu (7,000-12,000 in Clark in 2022/2024 ○) |
| Tue Nov 10 | Mail count must be finished |
| Fri Nov 13 | County canvass, including provisionals |
| Tue Nov 24 | Statewide canvass (Supreme Court) |
| Tue Dec 1, 5 pm | Recount demand deadline |

**What to expect** (inference):
- Nothing before ~11:50 pm ET; the first meaningful numbers around 1-2 am ET.
- The first big drop mixes Republican-leaning early in-person votes with Democratic-leaning mail, so it may be close or lean Ford.
- Election Day in-person votes overnight should lean Lombardo. **His numbers will look best on Wednesday morning.**
- The Wednesday-Saturday count (Election Day drop-offs, late mail, cures) should lean Ford. Expect a move somewhere between 2024's ~1.7 and 2022's ~3.5 points.
- **A Lombardo lead under ~25,000-30,000 votes (about 2-2.5 points) on Wednesday morning is at risk; a larger one should hold** (report's estimate from the 2022 and 2024 tails).
- Expect AP on Friday or Saturday. Inside ~1 point, wait for the Nov 9 cure deadline or the Nov 13 canvass.

### The swing data: Nevada

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Nevada | 2020 | 1 | - / 0% / 0% / 85% | - | - | +1.8 | 0 of 0 |
| Nevada | 2022 | 11 | - / - / - / 82% | - | - | +3.2 | 0 of 0 |
| Nevada | 2024 | 6 | - / - / - / 87% | - | - | +1.8 | 0 of 0 |

#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Nevada 2022 Secretary of State | NV-G-secretary_of_state-2022-11-08 | - (-%) | - (-%) | Marchant (82.3%) | Aguilar +2.3 | Nov 10 9:35 pm (87.9% in) |
| Nevada 2022 Senate | NV-G-S-2022-11-08 | - (-%) | - (-%) | Laxalt (82.2%) | Cortez Masto +0.8 | Nov 12 9:14 pm (96.9% in) |
| Nevada 2022 Treasurer | NV-G-treasurer-2022-11-08 | - (-%) | - (-%) | Fiore (82.3%) | Conine +1.7 | Nov 10 10:58 pm (89.7% in) |
| Nevada 2024 Senate | NV-G-S-2024-11-05 | - (-%) | - (-%) | Brown (86.6%) | Rosen +1.6 | Nov 7 2:47 am (92.4% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Nevada 2022 House 2 | 71.8% | -29.5 | -21.9 | **+7.5** |
| Nevada 2022 Attorney General | 83.5% | +4.3 | +7.9 | **+3.6** |
| Nevada 2022 Senate | 82.2% | -2.7 | +0.8 | **+3.5** |
| Nevada 2022 Secretary of State | 82.3% | -1.1 | +2.3 | **+3.4** |
| Nevada 2022 Governor | 82.2% | -4.7 | -1.5 | **+3.2** |
| Nevada 2022 Lieutenant Governor | 82.3% | -6.9 | -3.7 | **+3.2** |
| Nevada 2022 House 3 | 86.9% | +0.8 | +4.0 | **+3.2** |
| Nevada 2022 Controller | 82.4% | -7.0 | -4.1 | **+2.9** |
| Nevada 2024 House 2 | 83.2% | -21.9 | -19.0 | **+2.9** |
| Nevada 2022 Treasurer | 82.3% | -1.1 | +1.7 | **+2.8** |
| Nevada 2022 House 1 | 87.4% | +2.9 | +5.6 | **+2.7** |
| Nevada 2024 House 3 | 90.1% | +0.8 | +2.7 | **+2.0** |
| Nevada 2024 House 1 | 90.6% | +5.6 | +7.5 | **+1.9** |
| Nevada 2020 President | 84.9% | +0.6 | +2.4 | **+1.8** |
| Nevada 2022 House 4 | 86.5% | +3.1 | +4.8 | **+1.7** |
| Nevada 2024 Senate | 86.6% | -0.1 | +1.6 | **+1.7** |
| Nevada 2024 President | 86.5% | -4.7 | -3.1 | **+1.6** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Nevada | midnight ET | 100% | +2.7 | Clark 64.9% (+10); Washoe 17.6% (+5); Douglas 2.4% (-29); Lyon 2.1% (-41) | 12:00 AM |
| Nevada | 6 am ET | 15% | +20.1 | Clark 8.1% (+27); Washoe 1.1% (+11); Douglas 0.4% (-31); Nye 0.2% (-37) | 5:52 AM |


---

## Oregon: Governor

**Race.**
- Tina Kotek (D, incumbent; also the Working Families nominee) vs Christine Drazan (R; also the Libertarian nominee), a rematch of 2022. Pacific Green nominee Brett Smith is the only other name ○ ([Wikipedia](https://en.wikipedia.org/wiki/2026_Oregon_gubernatorial_election)).
- Model: Kotek 70.1%. Market: Kotek 83%.
- In 2022 Kotek won by 66,727 votes (3.4 points) while independent Betsy Johnson took 8.6%. Smith polls 3-6%, so this year is closer to a two-way race ○.
- Recent polls: Kotek 46-44 (Oregonian/DHM) and 46-42 (GBAO, a Kotek internal), after three polls with Drazan ahead by 1-4 ○ ([OPB, Oct 8](https://www.opb.org/article/2026/10/08/new-polls-kotek-may-lead/)).

**Rules for Nov 3 ✔** ([ORS chapter 254](https://www.oregonlegislature.gov/bills_laws/ors/ors254.html), 2025 edition, re-read 2026-10-22)
- **Everyone votes by mail.** Drop sites stay open until at least 8 pm PT, **11:00 pm ET** (254.470(1)). Most of Malheur County is on Mountain time and closes at 10:00 pm ET ○.
- **Results:**
  - No tally may be made public before 8 pm ([ORS 260.705](https://www.oregonlegislature.gov/bills_laws/ors/ors260.html)).
  - Each county must post to the state results site at least once between 8 pm and midnight PT (11 pm-3 am ET), and after Election Day "as frequently as possible" ◐ ([OAR 165-007-0550](https://www.law.cornell.edu/regulations/oregon/Or-Admin-Code-SS-165-007-0550)).
  - No count of ballots remaining is required.
- **Mail:**
  - A mailed ballot counts if it arrives by 8 pm Election Day, or if its postal indicator shows it was mailed by Election Day and it arrives **within 7 calendar days, by Tue Nov 10** (254.470(6)(e)).
  - A ballot with no or an unreadable postmark counts as mailed on Election Day if it arrives by Nov 10 (254.470(8)).
- **Processing:** counties may open envelopes and scan ballots as they arrive (254.478); nothing is released before 8 pm.
- **Deadlines:**
  - Signature cure by the 21st day, **Tue Nov 24** (254.431).
  - County abstracts by the 27th day, **Mon Nov 30** (254.545). Multnomah, Washington and Clackamas plan to certify that day ◐.
  - The Secretary of State canvasses every office **except Governor** by Dec 10 (254.555). The governor's returns go to the House Speaker, who opens and publishes them before the 2027 Legislature ◐ (Oregon Constitution, Art. V §4).
- **Automatic recount** if the top two are within one-fifth of 1% of their combined vote ✔ ([ORS 258.280](https://www.oregonlegislature.gov/bills_laws/ors/ors258.html)): about 3,800-4,000 votes this year (2022: 3,535) ◐.
- **The live risk is the post office.** Since a December 2025 USPS rule, a postmark can come a day or more after mailing. In the May 2026 primary Oregon rejected **7,314 grace-period ballots (13.1%) for late postmarks**, up from 9.5% in 2024 ◐ (Oregon SOS). The Secretary of State is urging voters to mail by Oct 27 or use a drop box ○.

**How results are reported.**
- 36 counties. State site: results.oregonvotes.gov; most counties also post on their own sites.
- **The first release, just after 11 pm ET, is mostly ballots received through about Monday** ◐ (AP 2024 preview). 55-82% of the final vote was counted within an hour of the close in 2020-2024 (NYT data).
- **Election Day drop-offs are a quarter of the vote** (2024: 568,046 ballots, 24.6%), more in Multnomah (31.9%) and Washington (30.8%) ◐. They're counted Wednesday to Friday after signature checks.
- **2026 county schedules** ◐ (PT; ET +3 hours):

  | County | Election night | Wed Nov 4-Fri Nov 6 | Later |
  |---|---|---|---|
  | Multnomah (Portland) | 8:00 pm, 10:00 pm, midnight | Daily at 6 pm | Thu Nov 12 (after the postmark deadline), Wed Nov 25 (cures), Mon Nov 30 (certify) |
  | Washington | 8:00 pm, 10:00 pm, midnight | **Wednesday and Friday only**, 4 pm | Fridays Nov 13, 20, 27; certify Nov 30 |
  | Clackamas | 8:00 pm, 9:30 pm, 11:30 pm | Daily at 5 pm ("tentative") | Nov 10, 17, 25 |

  Lane and Marion haven't published schedules.
- **Clackamas is the slow county:** about 65,000 ballots were left at the end of Wednesday in 2024 ◐.
- **The postmarked tail is small:** 13,596 ballots (0.6%) in 2024, against 34,442 (1.7%) in 2022 ◐.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | 11:07 pm | 82% | Biden led first | 11:00 pm (NYT) | Biden (D) +16.1 |
| 2020 | Senate | 11:07 pm | 83% | Merkley led first | 11:01 pm (NYT) | Merkley (D) +17.6 |
| 2022 | Governor | 11:03 pm | 53% | Kotek led first | Nov 10 (AP) | Kotek (D) +3.4 |
| 2022 | Senate | 11:03 pm | 60% | Wyden led first | 11:46 pm (AP) | Wyden (D) +14.9 |
| 2024 | President | 10:00 pm | 65% | Harris led first (timeline ends 5:40 am Wed) | 11:23 pm (AP) | Harris (D) +14.4 |

What the curves show:
- **2022 Governor:**
  - Kotek was +9.8 in the first release at 11:03 pm ET (34% in) and +1.1 at the end of election night (73% in).
  - The Wednesday-Friday count added +2.4 (she reached +3.7 by Friday midday ○), and the final was +3.4.
  - AP called it Thu Nov 10, about 9:00-9:30 pm ET, with 85% counted ○. The Oregonian and OPB projected it late Wednesday morning ○.
- **2022 Senate and 2024 President** moved +1.8 toward the Democrat after election night; **2020 moved −1.5**.
- **Later ballots were more Democratic by registration in 2024:** D+8.5 among ballots received through Monday morning, D+11.0 through Election Day evening, D+14.3 for the last drop-offs and **D+17.7 for post-Election Day mail** ◐ (researcher's tally of the SOS daily return reports).
- **Close House races:** OR-5 2022 was called on day 5 and OR-6 2022 on day 6; OR-5 2024 took until day 9 ○.

**After election night**

| Date | Event |
|---|---|
| Wed Nov 4-Fri Nov 6, 7-9 pm ET | Election Day drop-offs: Washington Wednesday and Friday at 7 pm ET, Clackamas daily at 8 pm, Multnomah daily at 9 pm |
| Tue Nov 10 | Postmarked mail deadline; Clackamas update |
| Thu Nov 12 | Multnomah's postmark-deadline update |
| Tue Nov 24 | Signature cure deadline |
| Mon Nov 30 | County abstracts and certification |

**What to expect** (inference):
- Kotek will very likely lead the 11 pm ET first release. As in 2022, her margin may shrink through the night.
- The Wednesday-Friday count, dominated by Multnomah and Washington drop-offs, should widen a Kotek margin by about 1-2.5 points. **Her numbers will look worst at the end of election night.**
- **A Drazan lead under ~2 points at the end of election night is at real risk.**
- Late in the week, Clackamas or Marion batches can shave a few tenths, as between Friday and the final count in 2022.
- A 2022-like race is callable Wednesday or Thursday. Inside ~1 point, wait for the Nov 10 postmark deadline and Multnomah's Nov 12 update.
- Washington County, which posts only Wednesday and Friday, is the biggest blind spot.
- The Oregonian and OPB have projected 1-6 days before AP, and prices may move on them.

### The swing data: Oregon

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Oregon | 2020 | 2 | 82% / 84% / 82% / 90% | -3.2 | -3.2 | -1.5 | 0 of 2 |
| Oregon | 2022 | 8 | 55% / 63% / 55% / 71% | +1.7 | +1.3 | +1.0 | 0 of 8 |
| Oregon | 2024 | 9 | 65% / 68% / 65% / 77% | +0.8 | +0.4 | +0.5 | 0 of 9 |

#### Biggest moves in competitive races

**Oregon**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2022 House 5 | 58.3% / -5.6 | 57.5% / -5.1 | 69.0% / -4.5 | -2.1 | **+3.5** | +2.4 |
| 2024 House 4 | 73.3% / +10.5 | 73.3% / +10.5 | 82.3% / +8.9 | +7.8 | **-2.7** | -1.1 |
| 2022 Governor | 62.8% / +1.0 | 52.6% / +0.9 | 73.4% / +1.1 | +3.4 | **+2.4** | +2.4 |
| 2022 House 4 | 72.9% / +9.8 | 32.7% / -0.0 | 85.1% / +8.1 | +7.5 | **-2.3** | -0.7 |
| 2022 Senate | 63.0% / +13.3 | 59.8% / +14.5 | 73.5% / +13.1 | +14.9 | **+1.7** | +1.8 |


#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Oregon 2022 House 1 | 68.0% | +33.6 | +36.0 | **+2.4** |
| Oregon 2022 House 5 | 69.0% | -4.5 | -2.1 | **+2.4** |
| Oregon 2022 Governor | 73.4% | +1.1 | +3.4 | **+2.4** |
| Oregon 2024 Attorney General | 77.2% | +7.0 | +8.9 | **+1.9** |
| Oregon 2022 Senate | 73.5% | +13.1 | +14.9 | **+1.8** |
| Oregon 2024 President | 76.4% | +12.6 | +14.4 | **+1.8** |
| Oregon 2024 Secretary of State | 77.1% | +10.8 | +12.6 | **+1.8** |
| Oregon 2020 President | 90.4% | +17.6 | +16.1 | **-1.5** |
| Oregon 2020 Senate | 90.6% | +19.1 | +17.6 | **-1.5** |

#### Where the late vote came from (2020, county detail)

| State | After | Share of final vote still to count | How those votes split (Biden minus Trump) | Biggest contributors: share of state vote (their split) | Snapshot used (ET) |
|---|---|---|---|---|---|
| Oregon | midnight ET | 18% | +0.2 | Clackamas 3.7% (-11); Washington 3.5% (+20); Multnomah 2.8% (+47); Marion 1.4% (-14) | 12:00 AM |
| Oregon | 6 am ET | 9% | -0.9 | Clackamas 3.7% (-11); Washington 1.7% (+24); Marion 1.1% (-14); Deschutes 0.4% (-17) | 5:52 AM |

#### 2026 primaries, runoffs and specials

| State | Date | Race | NYT race id | Counted 1 h / 2 h / midnight / 6 am | Leader at the end, margin | Margin at 2 h | Ahead for good from (ET) |
|---|---|---|---|---|---|---|---|
| Oregon | 2026-05-19 | Governor | OR-D-G-2026-05-19 | 60.4 / 61.3 / 60.4 / 72.9 | Kotek +80.5 | 81.1 | 11:00 pm (49.3%) |
| Oregon | 2026-05-19 | U.S. House | OR-D-H-3-2026-05-19 | 61.3 / 61.9 / 61.3 / 73.1 | Dexter +80.9 | 83.67 | 11:00 pm (57.6%) |
| Oregon | 2026-05-19 | U.S. Senate | OR-D-S-2026-05-19 | 60.1 / 60.9 / 60.1 / 72.5 | Merkley +87.0 | 87.3 | 11:00 pm (49.2%) |
| Oregon | 2026-05-19 | Measure | OR-I-83580-OR-2026-05-19 | 60.3 / 61.3 / 60.3 / 73.0 | No +66.0 | 66.36 | 11:00 pm (45.8%) |
| Oregon | 2026-05-19 | Governor | OR-R-G-2026-05-19 | 61.9 / 63.2 / 61.9 / 75.3 | Drazan +7.5 | 10.84 | 11:00 pm (42.8%) |
| Oregon | 2026-05-19 | U.S. Senate | OR-R-S-2026-05-19 | 62.2 / 63.6 / 62.2 / 75.8 | Smith +2.4 | 3.59 | 11:00 pm (43.2%) |


---

## Alaska: Senate (ranked-choice)

**Race and ballot ✔** ([Ballotpedia, Sept 14](https://news.ballotpedia.org/2026/09/14/alaska-voters-to-decide-on-the-second-u-s-senate-general-election-using-ranked-choice-voting/); [Wikipedia](https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Alaska))
- Four names on the Nov 3 ballot (ranked-choice):
  - Mary Peltola (D)
  - **Dan S. Sullivan** (R, incumbent)
  - **Daniel J. Sullivan Jr.**, a Petersburg resident registered Republican with no relation to the incumbent. The Division of Elections' sample ballot lists him as "Sullivan, Daniel J. Jr." with no party.
  - Gerald Heikes (R), who advanced after the fourth-place finisher, David Leslie (D), withdrew before the Aug 31 deadline.
- **Aug 18 top-four primary:**

  | Candidate | Share | Votes |
  |---|---|---|
  | Peltola | 49.5% | 82,244 |
  | Dan S. Sullivan | 41.4% | 68,726 |
  | Daniel J. Sullivan Jr. | 2.5% | 4,107 |
  | Leslie | 1.1% | 1,850 |
  | Heikes | 1.1% | 1,741 |

  Peltola led by 8.1 points in an all-party primary.
- Model: Peltola 51.9%, the closest race on our list. Market: Peltola 75%.
- **Why the second Sullivan matters on election night** (inference):
  - Votes for the second Sullivan and for Heikes are first-round votes that are not the incumbent's.
  - They make it less likely that anyone tops 50% of first choices, so the ranked-choice count on Nov 18 is more likely.
  - Their second choices should mostly transfer to the incumbent, so a first-round Peltola lead can shrink in the final round.
  - Results feeds show **two "Sullivan" lines**. Read them by candidate ID, never by name (our recorder stores NYT's candidate IDs).

**Rules for Nov 3 ✔** ([2026 General Media Packet](https://www.elections.alaska.gov/doc/mp/2026/MediaPacket-2026-General.%20V3.pdf); [counting page](https://www.elections.alaska.gov/ballot-counting-process/counting-system-and-schedule/))
- Polls close 8 pm Alaska time, which is **midnight ET**. One Aleutian polling place closes 1:00 am ET (AP Aug 2026).
- **First results are expected 8:45-9:00 pm Alaska time (12:45-1:00 am ET).** After that, updates come at no set times and are announced on Facebook, X and by email.
- **Election-night results contain** first-choice votes from Election Day precincts and early in-person votes.
- **Mail and most absentee ballots are counted later:**
  - "nearly all in-person Election Day results and in-person early voting results are released by the last update of the night, with the bulk of mail voting results released in the days following" ✔ (AP Aug 2026).
  - 2024 primary: the night ended at ~89% counted, and 100% came 12 days later ✔.
- **Count calendar ✔:**

  | Date | Event |
  |---|---|
  | Nov 10 | Count |
  | Nov 13 | Count; last day for domestic mail to arrive (postmarked by Election Day) |
  | Nov 18 | Last day for overseas ballots; final count; **ranked-choice tabulation if no one has 50% + 1** |
  | Nov 25 | Target certification date |

- **The 7-day count (Nov 10)** covers absentee, early and questioned ballots, and "there may be additional counting days between day 7-10" ✔.
- **No cure process and no signature check:** "State law does not provide for a cure process"; signature verification is "not required in Alaska Statutes" ✔ (Media Packet).
  - SB 64 would have added tracking and curing. It was vetoed April 30, and the override failed 38-22 on May 4 (40 needed) ✔ ([Alaska Public Media](https://alaskapublic.org/news/politics/alaska-legislature/2026-05-04/veto-override-vote-on-elections-bill-fails-as-two-southeast-alaska-lawmakers-flip)).
- **Recounts:** must be requested within 5 days after certification ✔. The state pays if the margin is under 0.5% ◐. Recounts are automatic only on a tie ◐.

**How results are reported.**
- Statewide results from the Division of Elections, reported by state House district, not county.

**History** (generated from NYT data)

| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |
|---|---|---|---|---|---|---|
| 2020 | President | Wed 2:47 am | 0% | Trump led first | Nov 11 (NYT) | Trump (R) +10.1 |
| 2020 | Senate | Wed 2:49 am | 0% | Sullivan led first | Nov 11 (NYT) | Sullivan (R) +12.7 |
| 2022 | Governor | Wed 1:09 am | 0% | Dunleavy led first | Nov 23 (AP) | Dunleavy (R) +26.1 |
| 2022 | Senate | Wed 1:09 am | 0% | Tshibaka led first; Murkowski ahead Nov 18 (99% in) | Nov 23 (AP) | Murkowski (R) +7.4 |
| 2024 | President | Wed 1:07 am | 0% | Trump led first (timeline ends 5:40 am Wed) | Wed 4:59 pm (AP) | Trump (R) +13.1 |

What the curves show:
- **2020** (a mail-heavy year): Sullivan was ~−28 at the end of election night with ~37% counted and won by 12.7. The count moved **~15 points toward the Democrat** as mail came in.
- **2022 Governor** moved ~2 points the same way; **2024 President** ~2 points (NYT's 2024 timeline ends Wednesday morning).
- **2022 Senate:** Tshibaka led the first-choice count until Nov 18; Murkowski won the ranked-choice count, and AP called it Nov 23.
- **2024 House** (not in our files): Begich won the ranked-choice count on Nov 20, 51.3-48.7 ✔.

**What to expect** (inference):
- Sullivan will likely lead on election night. A deficit of a few points for Peltola at 3-4 am ET is consistent with a toss-up race.
- The count shifts toward her on Nov 10-18 as mail is counted.
- With minor candidates on the ballot, a ranked-choice round is likely. The formal answer will probably come **Nov 18**.

### The swing data: Alaska

#### How fast it counts and how far it moves (all contested general-election races, median)

| State | Year | Races | Counted 1 h / 2 h / midnight / 6 am (median) | Median move after 1 h | after 2 h | after 6 am | Races that moved 5+ pts after 2 h |
|---|---|---|---|---|---|---|---|
| Alaska | 2020 | 2 | - / - / - / 37% | - | - | +16.0 | 0 of 0 |
| Alaska | 2022 | 2 | - / 56% / - / 77% | - | +6.1 | +2.2 | 2 of 2 |
| Alaska | 2024 | 2 | - / 30% / - / 73% | - | +4.1 | +2.6 | 1 of 2 |

#### Biggest moves in competitive races

**Alaska**

| Race | 2 h after close: counted / margin | Midnight ET | 6 am ET | Final | Move after 2 h | Move after 6 am |
|---|---|---|---|---|---|---|
| 2024 President | 30.0% / -18.2 | -% / - | 72.1% / -15.4 | -13.1 | **+5.1** | +2.2 |
| 2024 House 1 [RCV, 1st round] | 30.5% / -5.2 | -% / - | 73.3% / -5.0 | -2.0 | **+3.2** | +2.9 |


#### Every race where the leader at 2 hours or at midnight lost

| Race | NYT race id | Led at 2 h (share counted) | Led at midnight ET | Led at 6 am ET | Winner, final margin | Winner ahead for good from (ET) |
|---|---|---|---|---|---|---|
| Alaska 2022 Senate [RCV, 1st round] | AK-G-S-2022-11-08 | Tshibaka (55.8%) | - (-%) | Tshibaka (77.3%) | Murkowski +0.8 | Nov 18 10:08 pm (98.6% in) |
| Alaska 2024 Measure | AK-I-83139-AK-2024-11-05 | Yes (30.4%) | - (-%) | Yes (73.4%) | No +0.2 | Nov 18 7:01 pm (97.8% in) |

#### Races that moved 1.5+ pts after 6 am ET

| Race | Counted at 6 am ET | Margin at 6 am | Final | Move after 6 am |
|---|---|---|---|---|
| Alaska 2020 President | 36.8% | -26.7 | -10.1 | **+16.6** |
| Alaska 2020 Senate | 37.3% | -28.0 | -12.7 | **+15.3** |
| Alaska 2024 House 1 [RCV, 1st round] | 73.3% | -5.0 | -2.0 | **+2.9** |
| Alaska 2022 House 1 [RCV, 1st round] | 77.3% | +20.7 | +23.0 | **+2.3** |
| Alaska 2024 President | 72.1% | -15.4 | -13.1 | **+2.2** |
| Alaska 2022 Governor | 77.4% | -28.3 | -26.1 | **+2.2** |


---


# 5. Cross-state tables

### Pace and typical move, every state and year

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

### Early/mail vs Election Day margins

Shown only where NYT tagged a full share of early votes.

| State | Year | Races | Early/mail share of votes (median) | Early/mail margin minus Election Day margin (median, range) | Top-of-ticket example |
|---|---|---|---|---|---|
| Georgia | 2022 | 22 | 64% | +24.0 (+12 to +27) | Governor: early/mail +2.2, Election Day -25.0; Senate: early/mail +10.1, Election Day -15.4 |
| Georgia | 2024 | 15 | 76% | +4.4 (-4 to +14) | President: early/mail -0.7, Election Day -7.2 |
| Michigan | 2022 | 2 | 40% | +19.5 (+15 to +24) |  |
| Texas | 2024 | 33 | 80% | +0.4 (-10 to +19) | President: early/mail -13.2, Election Day -15.8; Senate: early/mail -9.3, Election Day -5.2 |
| Iowa | 2024 | 5 | 40% | +28.5 (+21 to +30) | President: early/mail +4.4, Election Day -25.4 |

---

# 6. Corrections, open questions, sources

### Corrections to earlier statements in this project

Things said earlier in this project (in chat, the report or the notes) that the checks above changed:

| Earlier claim | What checking found |
|---|---|
| Michigan: "Rogers likely leads early" (report) | In 2024 the Democrat led for the first ~2.5 hours (to 10:44 pm). The Republican led overnight, and the Democrat retook the lead Wednesday morning. |
| Ohio: Trump in 2020 and Vance in 2022 both overtook "around 9:30 pm" (AP, report) | 2022: 9:28 pm ✔. 2020: 10:00 pm in NYT's timeline. |
| Georgia 2024 AP call "12:58 am" (report) | 12:46 am, the AP call as recorded by NYT. |
| Ohio 2022 Senate call "~11:14 pm" (report, single source) | 11:20 pm (AP via NYT). |
| Nebraska: no evidence the 2024 first batch was Osborn-led (notes) | Osborn led the first update by 18 points with 25% counted. |
| Maine: "no strong timing pattern" (report) | Every race moved 4-8 points toward the non-Republican after the first two hours. |
| Alaska: "the later count moved 6-18 points toward the non-Republican" (chat) | About 2 points (2022 Governor, 2024 President) to ~15 points (2020) from the end of election night to final. |
| "The Internet Archive saved NYT's 2020 file ~900 times during election week" (chat) | ~900 captures over two years; **140 in election week**, about 25 of them on election night. |
| "Ohio, Kansas, Iowa, Nebraska: the Democrat/independent leads the first hour by 5-20 points" (chat) | True one hour after close for Ohio (Senate/President), Kansas (except 2022 Senate), Iowa and Nebraska 2024. Not Nebraska 2020 (Republican from the start), Nebraska 2022 Governor (the Democrat led only until 9:51 pm) or Ohio 2022 Governor (Republican from 8:03 pm). |
| Texas local canvass deadline: Nov 14 or Nov 17 (report conflict) | Nov 17; the official calendar is the 14th day after the election ✔. |
| Texas recount rules "not researched" (report) | Automatic only on a tie; request allowed within 10% of the leader's vote ✔. |
| Nebraska recount "1% of total vote" (AP) | 1% of the leading candidate's votes (statute) ✔. |
| Georgia "no automatic recount" (AP, May 2026) | Out of date. June 2026 law: automatic full hand recount for Governor at 0.5% or less ✔. |
| Iowa "first results 12 minutes vs 71 minutes" (conflict); this guide's earlier "2020 was the slow year" | Neither: Iowa polls closed at 10 pm ET in 2020 (9 pm CT; moved to 8 pm CT from 2022 by SF 413). First votes came 2-13 minutes after the close in all three years. |
| Georgia: "the Libertarian withdrew" (report) | The Libertarian Party never qualified for the ballot (July 2026). The outcome is the same: a two-candidate race. |
| Nebraska: "Burbank withdrew and endorsed Osborn" (report) | She withdrew July 17. The state party (chair Jane Kleeb) endorsed Osborn and declined to replace her. Burbank had said she'd back him if she had no path. |
| Kansas recounts: request-only, the requester pays (report) | Request-only, but in a general election decided by 0.5% or less the state pays and no bond is needed (K.S.A. 25-3107). |
| Kansas 2020 Senate "AP call shortly after 10 pm" (report) | NYT's own call was 10:58 pm; AP's exact time is still unconfirmed. |
| Nevada, Oregon and Texas Governor "just outside the 75% cut" (this guide, Oct 21) | The model audit's retrain (Oct 22) put all three inside it. They're now covered: sections 6, 11 and 12. |
| Nevada "no automatic recount" vs Oregon (report) | Confirmed in both statutes: Nevada recounts only on demand (NRS 293.403); Oregon recounts automatically at 0.2% (ORS 258.280) ✔. |
| Texas: "the Democrat leads for the first 15-35 min"; "a Talarico lead of 4+ at 8:30 pm is good shape"; "after the first hour the count moves another 2-4 points" (this guide, Oct 21) | Biden led Texas until 9:29 pm in 2020, and was +5.0 at 8:30 pm before losing by 5.6. After 9 pm the rest moved 3.8-6.7 pts toward the Republican. A safe lead is ~7+ pts at 9 pm or 4+ at 10 pm (section 6). |
| Kansas: "if Hamilton still leads at 9:30-10 pm, the race is genuinely close" (this guide) | At 9:30 pm the Democrat led every top race 2020-2024, and Holland led at 10 pm in 2022 and lost by 23. A safe lead is ~8+ pts at 10:30 pm (section 7). |
| Nebraska: "if Osborn still leads at 11:30 pm, the race is close" (this guide) | After 11:30 pm the rest moved 2-11 pts toward the Republican in every top race. A safe lead is ~9+ pts at midnight (section 10). |
| 2020 county detail: Nevada "11% still out at 6 am" (SWINGS.md) | 15% of the certified vote: the last archive copy, used as the final, held only 95% of Nevada's votes. All shares are now measured against certified totals. |
| Swing tables: Nevada 2020 "moved +86 after 2 hours" | Noise from a handful of early votes; a move is now measured only from a point with 3%+ counted. |
| History tables: every 2024 presidential row said "timeline starts 8:00 pm" | Only Georgia and Ohio report before 8 pm. The real first votes elsewhere: Texas 8:00 pm, Iowa 9:02 pm, Oregon 10:00 pm, Nevada 12:55 am, Alaska 1:07 am. |
| Comebacks table counted only the leader at 2 hours or at midnight (SWINGS.md) | It now includes the leader at 6 am, which adds Nevada's 2022 Senate, Secretary of State and Treasurer races and its 2024 Senate race. |
| Master guide: Maine "moved 5-8 pts"; "Georgia and Ohio 93-99% by midnight" | 4-8 pts (2024 Senate moved 4.2); Georgia and Ohio 94-98% in 2022 and 2024, but Georgia 2020 only 80%. |

**Also corrected later:**
- Maine's first-round leader *can* lose the ranked-choice count: the 2026 Democratic governor primary went to Pingree after Shah led round one.
- Ranked-choice races are now measured on first-round votes in the swing data.
- Iowa 2020: polls closed at 10 pm ET that year (9 pm CT, an hour later than now), so its first votes came 13 minutes after the close, not 73. The swing tables now use that close.
- Michigan's model probability moved from 73.0% to 76.3% on Oct 21, just above the 75% cut. On Oct 22 it fell to 63.4% after the model audit fixed duplicated and mismatched poll inputs and the model was retrained (`model_audit/MODEL_AUDIT.md`).

### Still unconfirmed

- **Not out yet:**
  - AP's Nov 3 "What to expect" previews, including Nevada's and Oregon's (Oregon's 2024 edition came Oct 25). The watcher is checking twice a day.
  - Most counties' posting schedules for Nov 3. Exceptions: Multnomah, Washington and Clackamas (Oregon) and Washoe (Nevada) have published theirs; Clark County (Nevada) has not.
- **Nevada:**
  - Whether the Secretary of State will again publish each county's outstanding ballots, as after the June primary.
  - How Clark's new print-and-scan ballots perform at general-election turnout.
  - Several facts rest on search-result summaries, because nvsos.gov and the Review-Journal block scripts (marked ○).
- **Oregon:**
  - Lane and Marion county schedules.
  - Which parts of Malheur County keep Pacific time.
  - When the House Speaker will publish the governor result (it's never certified by the Secretary of State).
- **Ohio's Nov 3 directive (2026-48):** its full text, including which counties report every 15 minutes, could not be downloaded. ohiosos.gov blocks scripts.
- **Georgia:** voters' own deadline to fix an absentee or provisional problem (the county's 3-day decision deadline, Nov 6, is confirmed).
- **Alaska:** the western Aleutian poll-close time in ET; the AP preview says 1 am ET.
- **Kansas:** whether the Secretary of State takes the grace-period case further before Nov 3.
- **Turnout by vote method** this year in each state. It controls how big the early leads will be.

### Sources

| Source | Where |
|---|---|
| AP 2026 "What to expect" previews | Listed with links in `sources/README.md`; texts in `data/raw/ap_2026/` (not committed) |
| Statutes and official calendars | Linked inline above |
| NYT results files 2020-2024 | `data/raw/nyt/` |
| Rebuilding the history tables | `py "State election results/scripts/build_state_guide.py"` |
| Full research report with all citations | `reports/Vote count timing in close 2026 races.md` (the first nine states) and `reports/Vote count timing Nevada and Oregon.md` (Oct 22) |
| Nevada and Oregon statutes re-read 2026-10-22 | [NRS ch. 293](https://www.leg.state.nv.us/NRS/NRS-293.html) (revised 9/9/2026); [ORS ch. 254](https://www.oregonlegislature.gov/bills_laws/ors/ors254.html), [258](https://www.oregonlegislature.gov/bills_laws/ors/ors258.html), [260](https://www.oregonlegislature.gov/bills_laws/ors/ors260.html) (2025 edition) |

**Market liquidity figures:** pred-arb's `data/raw/kalshi_markets.csv` and `polymarket_markets.csv`, fetched 2026-10-19/20.
**Swing data:** `SWINGS.md`, `data/processed/swings.csv`.
