# Election night, Nov 3, 2026: master guide

*One file to read through. It covers the competitive Governor and Senate races (our model's favorite at 75% or
less): 13 races in eleven states. For each state it covers how votes are counted and reported, when results arrive, how far the count has moved in
past elections, and where that creates opportunities as results come in.*

*Built by `scripts/build_master.py` from `STATE_BY_STATE.md` (rules, checked against primary sources)
and the swings analysis ({{N_RACES}} races, 2020-2026, from NYT's minute-by-minute timelines). Every table is
generated from data. {{ASOF}} They move daily. Nevada, Oregon and Texas Governor were added on
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
| **3** | **Maine Senate** | Slow count, liquid market, a repeating intra-night pattern, and ranked-choice complications (detail below) | No live state feed; towns report piecemeal to AP. The ranked-choice count resolves ~8-10 days later, and the first-round leader can lose (2026 primary). |
| **4** | **Kansas, Nebraska, Iowa: fade the early Democratic/independent lead** | The **most consistent election-night direction** in the data (detail below). All three settle **on election night**, so money turns over quickly. | Thinner markets (Kansas ~2.2M Kalshi contracts; Nebraska not on Kalshi in our data). 2026's early vote may be more Democratic than before, so early leads may be bigger, and so may the fade. Most likely already priced in by sharp traders. |
| Special case | **Alaska Senate** | Big model-market disagreement (detail below) | Settles only after Nov 18 (ranked-choice count), possibly later with a recount, so money is tied up for weeks. The model's poll inputs in Alaska are thin. |
| Special case | **Oregon Governor** | Nevada's mirror image: Kotek's numbers look **worst** at the end of election night (detail below) | The market already prices {{MARKET:2026_OR_Governor}}, and it's thin (Kalshi ~130K contracts; Polymarket ~$113K liquidity, Oct 19). Only interesting if election night shows Drazan ahead or Kotek's price drops. |
| Avoid during the count | **Texas (Senate and Governor), Georgia, Ohio** | They count fast: Texas ~62-79% counted in the first hour or two; Georgia and Ohio 93-99% by midnight. | Little time for mispricing. The Ohio Governor gap (model {{MODEL:2026_OH_Governor}}, market {{MARKET:2026_OH_Governor}}) is a **pre-election** disagreement, not a live-count one. |

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

**3. Maine Senate** (Jackson D vs Collins R; model {{MODEL:2026_ME_Senate}}, market {{MARKET:2026_ME_Senate}})
- **Slow:** only 29-63% is counted by midnight ET.
- **Repeating pattern:** in every race we have, the count moved 5-8 pts toward the non-Republican after the first two hours, then 0-3 pts back after 6 am.
- **Liquid:** ~4.4M Kalshi contracts; ~$2.3M Polymarket volume.
- **Ranked-choice wrinkle:** if no one tops 50% of *all* ballots (blanks count against the leader), the ranked-choice count decides about a week later, a second chance for prices to be wrong.

**4. Kansas, Nebraska, Iowa**
- **Kansas:** in 2022 **every** race moved 5+ pts toward Republicans after 2 hours (median 19). Governor Kelly's +20 became a 2.2-point win.
- **Nebraska:** Osborn led by **18** at 9:00 pm in 2024 and lost by 6.7. The lead changed at about 11:25 pm, and the race was called at 12:06 am.
- **Iowa:** the first-hour margin moved a median 13-29 pts by the end.

**Special case: Alaska Senate** (Peltola D vs Sullivan R)
- **The disagreement:** our model says {{MODEL:2026_AK_Senate}}; the market says {{MARKET:2026_AK_Senate}}.
- **What the count pattern implies:** Sullivan should lead on election night. Mail counted Nov 10-18 has moved the margin 2-3 pts toward Democrats (16 in 2020). That pattern **agrees with the market's direction**.
- **The trade it suggests:** if Sullivan's election-night lead pushes the market toward him, that may be a better entry for a Peltola position than today.

**Special case: Oregon Governor** (Kotek D vs Drazan R; model {{MODEL:2026_OR_Governor}}, market {{MARKET:2026_OR_Governor}})
- **The first release** at 11 pm ET holds most of the vote and showed Kotek's high point in 2022 (+9.8). By 1 am she was down to +1.0.
- **Wednesday to Friday** (Multnomah and Washington Election Day drop-offs) took her back to +3.7 by Friday midday; the final was +3.4.
- **The rule of thumb:** a Drazan lead under ~2 points at the end of election night is at real risk, and a Kotek lead should grow.

### Practical cautions

- **Settlement rules differ by platform** (see `AGENTS.md`):
  - Kalshi election markets resolve on who is **sworn in**; Polymarket resolves on who **wins**.
  - These all delay settlement:
    - ranked-choice counts (Alaska Nov 18, Maine about a week later);
    - recounts: automatic in Georgia's governor race at 0.5% or less, Michigan at 0.1%, Ohio at 0.25%, Oregon at 0.2%, and Nebraska at 1% of the leader's vote. Nevada recounts only on demand, by Dec 1;
    - late mail: Alaska, Oregon to Nov 10, Nevada to Nov 7, Kansas to Nov 6, Texas to Nov 4.
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

{{GUIDE:2b}}

### Patterns across states

{{GUIDE:2}}

---

# 4. State by state

In poll-closing order. Each state has three parts:
- rules and how results get reported, checked against primary sources: ✔ re-read, ◐ read by a researcher, ○ secondary;
- generated history tables;
- the swing data for that state.

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

---

# 6. Corrections, open questions, sources

### Corrections to earlier statements in this project

{{GUIDE:14}}

**Also corrected later:**
- Maine's first-round leader *can* lose the ranked-choice count: the 2026 Democratic governor primary went to Pingree after Shah led round one.
- Ranked-choice races are now measured on first-round votes in the swing data.
- Michigan's model probability moved from 73.0% to 76.3% on Oct 21, just above the 75% cut. On Oct 22 it fell to 63.4% after the model audit fixed duplicated and mismatched poll inputs and the model was retrained (`model_audit/MODEL_AUDIT.md`).

### Still unconfirmed

{{GUIDE:15}}

### Sources

{{GUIDE:16}}

**Market liquidity figures:** pred-arb's `data/raw/kalshi_markets.csv` and `polymarket_markets.csv`, fetched 2026-10-19/20.
**Swing data:** `SWINGS.md`, `data/processed/swings.csv`.
