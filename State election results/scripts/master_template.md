# Election night, Nov 3, 2026: master guide

*One file to read through. It covers the competitive Governor and Senate races (our model's favorite at 75% or
less): 13 races in eleven states. For each state it covers how votes are counted and reported, when results arrive, how far the count has moved in
past elections, and where that creates opportunities as results come in.*

*Built by `scripts/build_master.py` from `STATE_BY_STATE.md` (rules, checked against primary sources)
and the swings analysis ({{N_RACES}} races, 2020-2026, from NYT's minute-by-minute timelines). Every table is
generated from data. {{ASOF}} They move daily. Nevada, Oregon and Texas Governor were added on
Oct 22, when the model audit (`model_audit/MODEL_AUDIT.md`) moved them under 75%. County benchmarks, ballots
already cast, census voting blocs and the Oct 23 open-item checks were added on Oct 23.*

*The same guide is a page on the dashboard, [election-night.html](https://pjmerica.github.io/polling-agg-2026/election-night.html).
There the model and market numbers update with each forecast run, and every county table has a slider for the
statewide result plus a box that turns a county's finished result into an implied statewide margin.*

**Contents**
1. The states at a glance
2. Which state is the best opportunity as results come in
3. What is certain and what isn't, ballots already cast, patterns across states
4. State by state: rules, how results come in, history, swing data, county benchmarks, census voting blocs
5. Cross-state tables, including how reliable county benchmarks have been and how each bloc moved 2020-2024
6. Corrections, open questions, sources

---

## 1. The states at a glance

{{GUIDE:1}}

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
| Special case | **Oregon Governor** | Nevada's mirror image: Kotek's numbers look **worst** at the end of election night (detail below) | The market already prices {{MARKET:2026_OR_Governor}}, and it's thin (Kalshi ~130K contracts; Polymarket ~$113K liquidity, Oct 19). Only interesting if election night shows Drazan ahead or Kotek's price drops. |
| Avoid during the count | **Georgia** | Fast (94-98% counted by midnight in 2022 and 2024; 80% in 2020), and its direction has flipped by year: toward the Democrat in 2020 and 2024, toward the Republican in 2022. | Little time and no reliable direction to trade. |

**1. Nevada Governor** (Lombardo R vs Ford D; model {{MODEL:2026_NV_Governor}}, market {{MARKET:2026_NV_Governor}}, so the market favors Ford)
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

**2. Michigan Senate** (El-Sayed D vs Rogers R; model {{MODEL:2026_MI_Senate}}, market {{MARKET:2026_MI_Senate}})
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
- The Ohio Governor gap (model {{MODEL:2026_OH_Governor}}, market {{MARKET:2026_OH_Governor}}) is a **pre-election** disagreement, not a live-count one.

**4. Maine Senate** (Jackson D vs Collins R; model {{MODEL:2026_ME_Senate}}, market {{MARKET:2026_ME_Senate}})
- **Slow:** only 29-63% is counted by midnight ET.
- **Repeating pattern:** in every top race we have, the count moved 4-8 pts toward the non-Republican after the first two hours, then 0-3 pts back after 6 am. Most of that move happens while under a quarter of the vote is in, so the window is the first two hours.
- **Liquid:** ~4.4M Kalshi contracts; ~$2.3M Polymarket volume.
- **Ranked-choice wrinkle:** if no one tops 50% of *all* ballots (blanks count against the leader), the ranked-choice count decides about a week later, a second chance for prices to be wrong.

**Special case: Alaska Senate** (Peltola D vs Sullivan R)
- **The disagreement:** our model says {{MODEL:2026_AK_Senate}}; the market says {{MARKET:2026_AK_Senate}}.
- **What the count pattern implies:** Sullivan should lead on election night. Mail counted Nov 10-18 has moved the margin 2-3 pts toward Democrats (16 in 2020). That pattern **agrees with the market's direction**.
- **The trade it suggests:** if Sullivan's election-night lead pushes the market toward him, that may be a better entry for a Peltola position than today.

**Special case: Oregon Governor** (Kotek D vs Drazan R; model {{MODEL:2026_OR_Governor}}, market {{MARKET:2026_OR_Governor}})
- **The first release** at 11 pm ET holds most of the vote and showed Kotek's high point in 2022 (+9.8). By 1 am she was down to +1.0.
- **Wednesday to Friday** (Multnomah and Washington Election Day drop-offs) took her back to +3.7 by Friday midday; the final was +3.4.
- **The rule of thumb:** a Drazan lead under ~2 points at the end of election night is at real risk, and a Kotek lead should grow.

### How these states compare nationally

From `VOLATILITY.md`, which measures every President, Senate and Governor race in the 50 states and DC, 2020-2024. A state ranks high when its visible margin moves a lot during the count *and* its leader at some point often lost.
- **National top ten:** {{VOL_TOP10}}.
- **Our eleven, by national rank:** {{VOL_OURS}}.
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
  - **County benchmarks** (end of each state section, and the calculator on the dashboard page) turn a finished county's result into an implied statewide margin. In past races the largest county alone was usually within 2 points of the statewide result, but 4-5 points off in four races and 7 in one (section 5). Use several counties.
  - The full simulator in the README, which turns "X% counted, these counties out" into a projected final, is still to build. Until then the tables in this file are rules of thumb.
- **2026 differs from history:** new laws (Michigan pre-processing, Georgia's 8 pm rule, Ohio's ended grace period), Clark County's new ballots, slower USPS postmarks (Oregon rejected 13% of its late mail in May for late postmarks) and a more Democratic early vote. Expect the patterns, not the exact sizes.

---

## 3. What is certain and what isn't, ballots already cast, patterns across states

### Is there any source that says for certain when votes will be counted?

{{GUIDE:2b}}

### Ballots already cast

{{GUIDE:2c}}

### Patterns across states

{{GUIDE:2}}

---

# 4. State by state

In poll-closing order. Each state has five parts:
- rules and how results get reported, checked against primary sources: ✔ re-read, ◐ read by a researcher, ○ secondary;
- generated history tables;
- the swing data for that state;
- **county benchmarks**: each county's expected share of the statewide vote, and what each candidate needs there for a statewide tie or a 3-point win either way. Uniform swing on recent results, explained in each table's notes (`scripts/county_benchmarks.py`).
- **voting blocs**: counties grouped by demographics, how each group voted in 2020-2024 and what it needs to give in 2026 (`scripts/census_blocs.py`).

**How the voting blocs are built.** The demographics are the Census Bureau's latest county estimates, the American Community Survey 2020-2024, which cover every county (Alaska: every House district). Each county goes to the **first** bloc it fits:

| # | Bloc | Rule |
|---|---|---|
| 1 | Hispanic-majority | Hispanic 50%+ |
| 2 | Black 35%+, large counties | Black 35%+ and 150,000+ people |
| 3 | Black 35%+, smaller counties | Black 35%+, under 150,000 people |
| 4 | Native 25%+ | American Indian / Alaska Native 25%+ |
| 5 | College-educated | 40%+ of adults 25+ hold a bachelor's degree |
| 6 | Big diverse metros | 400,000+ people and under 60% non-Hispanic white |
| 7 | White, non-college | 70%+ non-Hispanic white, under 30% with a degree |
| 8 | Everything else | none of the above |

- These are places, not people: a "Hispanic-majority" county's swing mixes its Hispanic and non-Hispanic voters. The tables show which way places like that moved, not how any group of voters did.
- The 2026 rows sum the county benchmarks by bloc. On election night, compare a bloc's finished counties with its line.

{{STATE:georgia}}
{{STATE:ohio}}
{{STATE:michigan}}
{{STATE:texas}}
{{STATE:kansas}}
{{STATE:maine}}
{{STATE:iowa}}
{{STATE:nebraska}}
{{STATE:nevada}}
{{STATE:oregon}}
{{STATE:alaska}}

# 5. Cross-state tables

### Pace and typical move, every state and year

{{PACE_ALL}}

### Early/mail vs Election Day margins

Shown only where NYT tagged a full share of early votes.

{{EARLY_EDAY}}

### How reliable county benchmarks have been

The county benchmarks' method, run on every 2022 and 2024 race here, predicting each from the races before it. It is given the true statewide result, so this measures only how far counties stray from uniform swing. In 2026 the statewide result is unknown and turnout can shift, so real misses will be larger.
- **Typical county miss:** the vote-weighted root-mean-square gap between a county's actual two-party margin and its benchmark.
- **Largest county alone:** the statewide margin you would have estimated from the biggest county's final result, minus the real one.

{{COUNTY_BACKTEST}}

**What it says:**
- **The typical county miss is 1-5 points.** Nebraska's 2024 Senate race is the exception: Osborn's independent coalition missed by 8, and 82% of the vote was in counties off by 5+.
- **One county is not enough.**
  - Wayne County alone would have put Harris 4.0 points too low in 2024; Johnson County, Kansas, would have put Kelly 4.3 too low in 2022.
  - Douglas County, Nebraska would have put Osborn 7.2 too low.
  - Among the five largest counties, a single county's error reached 9-10 points (Kansas and Iowa 2022 governor races).
- **Several finished counties together are much better than any one.** The page's calculator averages them by size.

### How each voting bloc moved, 2020 to 2024

The 2020-to-2024 presidential shift in each bloc **minus the state's own shift** (points of two-party margin). Positive means the bloc moved toward the Democrat relative to the whole state, negative toward the Republican. Alaska is left out: its House districts were redrawn for 2022.

{{BLOC_SUMMARY}}

**What it says:**
- **The 2024 move toward Trump was concentrated in Hispanic and minority urban places.** Hispanic-majority counties moved 4.7 points more than Texas as a whole and 7.1 more than Kansas. Wayne County (Detroit) moved 4.3 more than Michigan.
- **College-educated counties moved least:** 0.1-2.3 points less than their states everywhere but Nebraska.
- **Georgia is the exception:** its Black-majority counties, large and small, moved less than the state.
- **Mostly white, non-college counties moved less than Texas and Nevada** (by 5.5 and 4.0) because they were already near their ceiling (R+65 and R+49 in 2020).
- **For 2026 (inference):** the swing-back questions are the Hispanic counties in Texas and Kansas and Wayne County in Michigan. Each state's "what it needs" table puts a number on them, such as Talarico's line in Texas's Hispanic-majority counties against Allred's 2024 result there.

---

# 6. Corrections, open questions, sources

### Corrections to earlier statements in this project

{{GUIDE:14}}

**Also corrected later:**
- Maine's first-round leader *can* lose the ranked-choice count: the 2026 Democratic governor primary went to Pingree after Shah led round one.
- Ranked-choice races are now measured on first-round votes in the swing data.
- Iowa 2020: polls closed at 10 pm ET that year (9 pm CT, an hour later than now), so its first votes came 13 minutes after the close, not 73. The swing tables now use that close.
- Michigan's model probability moved from 73.0% to 76.3% on Oct 21, just above the 75% cut. On Oct 22 it fell to 63.4% after the model audit fixed duplicated and mismatched poll inputs and the model was retrained (`model_audit/MODEL_AUDIT.md`).

### Still unconfirmed

{{GUIDE:15}}

### Sources

{{GUIDE:16}}

**Market liquidity figures:** pred-arb's `data/raw/kalshi_markets.csv` and `polymarket_markets.csv`, fetched 2026-10-19/20.
**Swing data:** `SWINGS.md`, `data/processed/swings.csv`.
