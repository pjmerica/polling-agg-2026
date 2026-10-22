# Election night, Nov 3, 2026: master guide

*One file to read through. It covers the competitive Governor and Senate races (our model's favorite at 75% or
less) in nine states: how each state counts and reports, when results arrive, how far the count has moved in
past elections, and where that creates opportunities as results come in.*

*Built by `scripts/build_master.py` from `STATE_BY_STATE.md` (rules, checked against primary sources)
and the swings analysis (345 races, 2020-2026, from NYT's minute-by-minute timelines). Every table is
generated from data. Model and market numbers are from 2026-10-21 evening; they move daily.*

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
| **1** | **Michigan Senate** | Best combination of all five (detail below) | Late batches aren't always Democratic: the 2026 primary narrowed late against El-Sayed (6.3 → 0.9), and 2024's late move was ~0. Model now 76%, so the race may not be that close. |
| **2** | **Maine Senate** | Slow count, liquid market, a repeating intra-night pattern, and ranked-choice complications (detail below) | No live state feed; towns report piecemeal to AP. The ranked-choice count resolves ~8-10 days later, and the first-round leader can lose (2026 primary). |
| **3** | **Kansas, Nebraska, Iowa: fade the early Democratic/independent lead** | The **most consistent direction** in the data (detail below). All three settle **on election night**, so money turns over quickly. | Thinner markets (Kansas ~2.2M Kalshi contracts; Nebraska not on Kalshi in our data). 2026's early vote may be more Democratic than before, so early leads may be bigger, and so may the fade. Most likely already priced in by sharp traders. |
| Special case | **Alaska Senate** | **Biggest model-market disagreement** (detail below) | Settles only after Nov 18 (ranked-choice count), possibly later with a recount, so money is tied up for weeks. The model's poll inputs in Alaska are thin. |
| Avoid during the count | **Texas, Georgia, Ohio** | Count fast: Texas ~62-79% counted in the first hour or two; Georgia and Ohio 93-99% by midnight. | Little time for mispricing. The Ohio Governor model-market gap (model 57% vs market 77% for Acton) is a **pre-election** disagreement, not a live-count one. |

**1. Michigan Senate** (El-Sayed D vs Rogers R; model El-Sayed 76.3%, market 69%)
- **Long window:** only 46-50% is counted by midnight ET in every recent general. The 2024 Senate race was called at 3:12 pm the next day.
- **Repeating order:** Wayne County (Detroit) and the other big counties report late.
  - 2020: the 18% counted after 6 am went Biden +35, almost all Wayne.
- **Lead changes:**
  - 2024 Senate: Slotkin led until 10:44 pm, Rogers led overnight, Slotkin retook it at 7:31 am.
  - 2020 Senate: James led until Wednesday afternoon.
  - Prices swing hardest at those moments.
- **Liquid:** ~3.3M contracts traded on Kalshi; ~$577k liquidity on Polymarket (as of Oct 19-20).

**2. Maine Senate** (Jackson D vs Collins R; model Jackson 69.1%, market 65%)
- **Slow:** only 29-63% is counted by midnight ET.
- **Repeating pattern:** in every race we have, the count moved 5-8 pts toward the non-Republican after the first two hours, then 0-3 pts back after 6 am.
- **Liquid:** ~4.4M Kalshi contracts; ~$2.3M Polymarket volume.
- **Ranked-choice wrinkle:** if no one tops 50% of *all* ballots (blanks count against the leader), the ranked-choice count decides about a week later, a second chance for prices to be wrong.

**3. Kansas, Nebraska, Iowa**
- **Kansas:** in 2022 **every** race moved 5+ pts toward Republicans after 2 hours (median 19). Governor Kelly's +20 became a 2.2-point win.
- **Nebraska:** Osborn led by **18** at 9:00 pm in 2024 and lost by 6.7. The lead changed at about 11:25 pm, and the race was called at 12:06 am.
- **Iowa:** the first-hour margin moved a median 13-29 pts by the end.

**Special case: Alaska Senate** (Peltola D vs Sullivan R)
- **The disagreement:** our model says 50.6% Peltola; the market says **75%**.
- **What the count pattern implies:** Sullivan should lead on election night, and mail counted Nov 10-18 has moved the margin 2-3 pts toward Democrats (16 in 2020). That pattern **agrees with the market's direction**.
- **The trade it suggests:** if Sullivan's election-night lead pushes the market toward him, that may be a better entry for a Peltola position than today.

### Practical cautions

- **Settlement rules differ by platform** (see `AGENTS.md`):
  - Kalshi election markets resolve on who is **sworn in**; Polymarket resolves on who **wins**.
  - Ranked-choice counts (Alaska Nov 18, Maine about a week later), recounts (automatic in Georgia's governor race at 0.5% or less, Michigan at 0.1%, Ohio at 0.25%, Nebraska at 1% of the leader's vote) and late mail (Alaska, Texas to Nov 4, Kansas to Nov 6) all delay settlement.
- **Fees are real per leg** (`utils/fees.py`). Small edges disappear.
- **The tools that make this usable are already set up:**
  - The election-night recorder (`capture_live.py`) saves every county every 2 minutes from 6:30 pm ET.
  - The next step is the simulator in the README, which turns "X% counted, these counties out" into a projected final.
  - Without the simulator, the tables in this file are rules of thumb.
- **2026 differs from history:** new laws (Michigan pre-processing, Georgia's 8 pm rule, Ohio's ended grace period) and a more Democratic early vote. Expect the patterns, not the exact sizes.

---

## 3. What is certain and what isn't, plus patterns across states

### Is there any source that says for certain when votes will be counted?

{{GUIDE:2b}}

### Patterns across states

{{GUIDE:2}}

---

# 4. State by state

In poll-closing order. Each state has three parts:
- rules and how results get reported, checked against primary sources: ✔ re-read today, ◐ read by a researcher, ○ secondary;
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

{{GUIDE:12}}

**Also corrected later:**
- Maine's first-round leader *can* lose the ranked-choice count: the 2026 Democratic governor primary went to Pingree after Shah led round one.
- Ranked-choice races are now measured on first-round votes in the swing data.
- Michigan's model probability moved from 73.0% to 76.3% on Oct 21, just above the 75% cut.

### Still unconfirmed

{{GUIDE:13}}

### Sources

{{GUIDE:14}}

**Market liquidity figures:** pred-arb's `data/raw/kalshi_markets.csv` and `polymarket_markets.csv`, fetched 2026-10-19/20.
**Swing data:** `SWINGS.md`, `data/processed/swings.csv`.
