# Did the 2024 markets misread the count?

Checked 2026-10-28 against Kalshi's and Polymarket's minute-by-minute 2024 prices (`market_history.py`) and
NYT's count timelines for every state (`market_check.py`). It covers the 65 President, Senate and Governor races
whose market was between 3% and 97% at poll close, and 9,107 NYT updates from 5% to 99% counted.

**Primaries are not worse; close races are.**
- The Colorado Republican governor primary (section below) was the deepest misread found: Marx, the eventual
  winner, traded at 2.8c in a tight book.
- But across 54 primaries and 57 generals (section "Primaries vs general elections"), close races of either
  kind put the eventual winner under 50c in 3 of 6 primaries and 4 of 10 generals.
- Every primary is on the dashboard page
  [Primaries vs the markets](https://pjmerica.github.io/polling-agg-2026/primaries-vs-markets.html).
- Primaries just have fewer close races.

**Short answer for 2024:**
- **Mostly no.** Markets read the count better than the statewide projector (v0) at every stage, and didn't
  lag it.
- **The exceptions were few and large.** Three eventual winners traded under 20c after half the vote was
  counted, all Democratic Senate candidates whose late votes came from big-city absentee and mail counts.
- **v0 couldn't tell those three from Pennsylvania**, which looked the same and went the other way.
- **So the opportunity is real but narrow,** and catching it needs the county-level projector (v1), not v0.

## How the test worked

At every NYT update, the script took:
- **What the live tool would have printed two minutes later:** `live_project.project()`, using each state's
  2020 and 2022 history only (2024 left out), starting from the market's own price at poll close.
- **What the market charged at that minute.** For Kalshi that is the real bid and ask. For Polymarket it is
  the minute price, plus or minus the larger of 1c and Kalshi's half-spread, since no Polymarket book
  history survives.
- **A trade whenever the edge after today's fees beat 3c, 5c or 10c:** 1 contract, at most one per race,
  venue and side per 15 minutes, settled on how the contract actually resolved.

NYT's timestamps are when NYT posted. AP and Decision Desk, which traders watch, are often faster, so the
market had at least the projector's information.

**Two traps found along the way:**
- **Settlement.** Polymarket's 2024 Maine and Vermont "another party" contracts resolved **No** although the
  independents (King, Sanders) won: Polymarket counted them as Democrats. Settling on the count made $56 of
  fake profit, so those contracts are left out. This is the same kind of fine print as Kalshi's "sworn in"
  rule.
  - **Checked 2026-10-28:** Polymarket's 2026 Nebraska rules now say independents "will not be encompassed by
    the 'Democrat' or 'Republican' options regardless of any affiliation", so an Osborn win resolves its
    independent contract Yes.
  - Kalshi's contract names Osborn (`SENATENE-26-DOSB`) and resolves on who is sworn in.
- **Spreads.** In the minutes that matter, the books blow out. Michigan Senate at 5 am ET was bid 0.30 / ask
  0.88 on Kalshi. With an assumed 1c Polymarket spread, Polymarket showed +15c per contract; with a realistic
  spread it shows +2c.

## Who was closer to the result

Brier score (lower is better). Each race is weighted equally: its updates are averaged first.

| Counted | Races | Market | Projector (v0) |
|---|---|---|---|
| 5-20% | 52 | **0.038** | 0.043 |
| 20-40% | 59 | **0.032** | 0.039 |
| 40-60% | 61 | **0.028** | 0.038 |
| 60-80% | 63 | **0.032** | 0.034 |
| 80-99% | 57 | **0.025** | 0.030 |

When the two differed by 3+ points (4,177 updates), the market moved toward the projector in the next 30
minutes only 35% of the time, with a correlation of +0.01. **The markets were not slow to absorb what v0
knows.**

## Trading v0 mechanically

| Edge needed | Venue | Trades | Races | Won | Avg P&L per contract |
|---|---|---|---|---|---|
| 3c | Kalshi | 441 | 32 | 20% | -1.3c |
| 5c | Kalshi | 384 | 23 | 19% | -0.3c |
| 10c | Kalshi | 300 | 15 | 18% | +1.1c |
| 5c | Polymarket | 420 | 26 | 26% | +2.6c |

Breakeven. Split by how wide Kalshi's book was at the time (5c threshold, both venues; trades in brackets):

| Counted | Tight book (spread 5c or less) | Wide book |
|---|---|---|
| 5-40% | -19.2c (58) | +16.4c (20) |
| 40-70% | -6.3c (148) | +18.0c (71) |
| 70-99% | -2.6c (390) | +20.8c (117) |

- **Where the book was tight,** the market was right and v0 lost.
- **The gains came only from wide books,** the volatile overnight stretches, and nearly all from three races.
  Wide-book prices also give little size.

By race (Kalshi, 5c):

| Race | Trades | P&L | v0 bought | Result |
|---|---|---|---|---|
| MI-Senate | 30 | **+17.05** | Slotkin (D) from 5c | Slotkin won by 0.3 |
| WI-Senate | 25 | **+14.85** | Baldwin (D) from 17c | Baldwin won by 0.9 |
| NV-Senate | 16 | **+4.32** | mostly Rosen (D) from 4c | Rosen won by 1.6 |
| PA-Senate | 76 | **-13.13** | Casey (D) from 3c to 70c | McCormick (R) won by 0.2 |
| AZ-Senate | 67 | **-8.68** | Lake (R) from 4c to 30c | Gallego (D) won by 2.4 |
| MI, PA, WI President | 79 | -9.69 | Harris (D) | Trump won all three |
| 17 others | 91 | -2.42 | | |

## Where the markets really were wrong

These are the eventual winners priced under 50c after half the vote was counted (mid price: Kalshi where
its spread was 10c or less, otherwise Polymarket). 5 of 65 races.

| Race | Winner | Lowest price | When | Minutes under 30c | Minutes under 15c |
|---|---|---|---|---|---|
| WI-Senate | Baldwin (D) | **2c** | Wed 1:14 am ET | 212 | 37 |
| MI-Senate | Slotkin (D) | **5c** | Wed 2:09 am ET | 221 | 72 |
| NV-Senate | Rosen (D) | **16.5c** | Wed 2:48 pm ET | 88 | 0 |
| PA-Senate | McCormick (R) | 44c | Tue 10:48 pm ET | 0 | 0 |
| NJ-Senate | Kim (D) | 49.8c | Wed 9:01 am ET | 0 | 0 |

New Jersey's Kim won by 9.6 points, so his 49.8c is almost certainly a thin or stale quote, not a real
mispricing.

**The pattern:**
- All three big misses are Democratic Senate candidates running ahead of Harris in close states, with the
  Democratic vote counted last: Milwaukee's central absentee count and Detroit's absentees, both overnight,
  and Clark County mail Wednesday through Saturday.
- The markets extrapolated the top of the ticket and the visible margin.
- **Pennsylvania looked the same overnight** (Philadelphia counted late) **and went the other way by 0.2
  points.** v0 bought all four races alike, because a statewide average can't tell them apart.
- **Telling them apart needs county counts:** how many Milwaukee or Wayne County votes are left, and how
  Democratic they are. That is v1.

## 2026 primaries: the Colorado Republican governor race (June 30)

This was the worst misread found so far: Marx against Kirkmeyer, about $650K traded on each on Kalshi
(`scripts/co_primary_check.py`).

- **Before the count:** Marx was a 93-94% favorite.
- **Early returns:** Kirkmeyer led, by 5 points at 44% counted.
- **The market dumped Marx:** 15c at 72% counted, and a low of **2.8c at 8:44 pm MT** (77% counted,
  Kirkmeyer +2.2).
- **The book was tight, not thin:** the median Kalshi spread while Marx was under 15c was 2.7c. He spent
  **177 minutes under 15c** and 229 under 30c.
- **Result:** Marx won by **0.47 points**.

| Time (MT) | Counted | Visible margin (Marx - Kirkmeyer) | Last 15% of the count broke | If the rest breaks like that | Marx, Kalshi |
|---|---|---|---|---|---|
| 7:23 pm | 44% | -5.1 | -5.2 | -5.1 | 69c |
| 7:34 pm | 65% | -2.7 | +1.0 | -1.4 | 25c |
| 7:53 pm | 75% | -2.6 | +0.2 | -1.9 | 15c |
| 8:51 pm | 77% | -2.1 | +1.1 | -1.4 | **5c** |
| 9:17 pm | 81% | -1.5 | +3.0 | -0.7 | 12c |
| 10:04 pm | 82% | -1.5 | +2.8 | -0.8 | **6c** |
| 11:06 pm | 85% | -1.0 | +4.8 | -0.1 | 17c |
| 11:23 pm | 86% | -0.8 | +10.2 | +0.7 | 39c |
| 12:11 am | 87% | -0.8 | +10.0 | +0.6 | 37c |
| Wed 7:13 am | 89% | -0.3 | +10.9 | +0.9 | 55c |

**What went wrong in the market.** From 7:34 pm, the votes coming in were breaking toward Marx while the
visible margin still showed Kirkmeyer. The market priced the visible margin and threw away a 93% starting
point.

**What a projector would have said, honestly:**
- Until about 9 pm, the trend still pointed to Kirkmeyer by 1.2-1.9 with about 22% left. That says Marx
  is underpriced (roughly one in three, not 5-15c), not that Marx wins.
- From 9:17 pm it was near a coin flip, while the market stayed at 6-12c.
- From 11:20 pm the trend had Marx ahead, while the market was still at 37-39c.

**Caveats:**
- The 15% trend rule was chosen after the fact. Its readings flicker (-0.7 at 9:00 pm), because batches are
  lumpy by county.
- NYT published no live estimate for this primary (`nyt_model_estimates` is empty at all 317 points).
- v0 has no primary history.

**Lessons for Nov 3:**
- **Keep the starting point.** `live_project.py`'s default, starting from the market's own price at poll
  close, is exactly what the market abandoned here.
- **The within-night trend is not the fix.** Tested on every primary and on 2024 (next section), it was no
  better than the visible margin.

## Primaries vs general elections: is it only primaries?

**No, it's close races.** `scripts/primary_check.py` covers:
- **The 2026 primaries:** 80 Senate and Governor primaries considered, of which 54 had an NYT timeline and a
  market and were decided on the night. The dashboard page
  [Primaries vs the markets](https://pjmerica.github.io/polling-agg-2026/primaries-vs-markets.html) has
  every race.
- **Left out:**
  - 17 had no usable timeline or went to a runoff. Texas Republican Senate and Oklahoma Republican governor
    also had markets that settled on the runoff winner.
  - 5 had no market with $1,000+ traded.
  - 3 Maine ranked-choice races had no first-round majority, so tabulation decided them days later.
  - 1 (Florida Democratic Senate) had no NYT file.
- **The comparison:** the 2024 generals above, measured the same way.

Fixed along the way (2026-10-29):
- **Runoff dates.** The primary model lists some states' runoff date (TX, GA, AL, SC, SD), so files are now
  looked up on every primary night.
- **A name collision.** Kalshi listed both Hannah and Chellie Pingree for Maine, and last-name matching had
  priced the winner with the dead contract. Matching is now by full name.

**All races:**

| | Races | Winner under 50c after half counted | Under 20c | Under 10c | Market favorite right | Visible leader right | Trend right |
|---|---|---|---|---|---|---|---|
| 2026 primaries | 54 | 3 (6%) | 1 (2%) | 1 (2%) | 97.2% | 97.8% | 96.8% |
| 2024 generals | 57 | 5 (9%) | 3 (5%) | 2 (4%) | 96.1% | 94.6% | 94.5% |

The "right" columns are the share of NYT updates, between 50% and 95% counted, on which each signal named
the eventual winner. Each race is weighted equally. "Trend" is the visible margin plus the rest of the vote
breaking like the last 15% of the count.

**Close races only** (final margin under 3 points):

| | Races | Winner under 20c | Under 50c | Market favorite right | Visible leader right | Trend right |
|---|---|---|---|---|---|---|
| 2026 primaries | 6 | 1 | 3 | 78% | 83% | 80% |
| 2024 generals | 10 | 3 | 4 | 78% | 75% | 77% |

**The close races, one by one:**
- **2026 primaries:**
  - Colorado R governor: Marx, lowest price 2.8c.
  - Rhode Island R governor: Guckian, 10c at poll close and a low of 20.5c after half counted. He won by 1.1.
  - Wisconsin D governor: Crowley, 4.8c at poll close and a low of 25.5c after half counted. He won by 0.46.
  - Iowa R governor: Lahn, 67c.
  - Michigan D Senate: El-Sayed, 77c.
  - Vermont D governor: Janoo, 97c.
- **2024 generals:**
  - Senate: WI 2c, MI 5c, NV 16.5c, PA 44c, AZ 68.5c.
  - President: PA, GA, WI, MI and NH, all 78c or more.

**Reading it:**
- **Primaries are not misread more.** Most are blowouts with nothing to misread. In close races the eventual
  winner traded under 50c in 3 of 6 primaries and 4 of 10 generals, and in both the market's favorite was
  wrong on about a fifth of the updates past the halfway mark (78% right in each).
- **The market mostly follows the visible leader.** Its worst nights (Colorado, Michigan Senate, Wisconsin
  Senate) are exactly the races where the visible leader was wrong for most of the count: right on 0%, 0.4%
  and 11% of the updates. It beat the visible margin mainly in Nevada Senate (81% vs 38%).
- **The within-night trend is no general fix.** Across all races it matched the visible margin (96.8% vs
  97.8% in primaries, 94.5% vs 94.6% in generals). It helped in Colorado and Nevada and hurt in Wisconsin's
  D governor primary (56% vs 96%) and Kentucky's D Senate primary (49% vs 82%). Batches are lumpy by county,
  so the last 15% of the count says little about the next 15%.
- **The edge is knowing when the visible leader will flip,** which takes knowing which counties are still
  out and how they vote. That is v1.

**2022 midterms could not be checked.**
- Kalshi had no election markets in 2022.
- Polymarket's 2022 markets ran on an automated market maker before its order book existed:
  `/prices-history` and the trade API return nothing for them, and the public Polygon RPC endpoints refused
  connections from this machine.
- They were small anyway: Pennsylvania Senate 2022 traded $181K in its whole life.

## What this means for Nov 3

1. **Don't trade v0's edge on its own, and never into a tight book.** On 2024 evidence the market is right
   there.
2. **The opportunity is the overnight wide-book window in close races where a known Democratic batch is still
   out.** The 2026 analogs:
   - Michigan Senate: Wayne County.
   - Nevada Governor: Clark mail from Wednesday on.
   - Late mail in Maine and Alaska. For both, read the rules on independents and ranked-choice first.
   - The Kansas, Iowa, Ohio and Texas fades run the other way: the early Democratic lead shrinks, and
     MASTER.md says the market likely prices that already.
3. **v1 is the priority:** remaining votes by county and ballot type from NYT's live county files.
   Re-running this check with v1 on the 2024 data is the test before trusting it.
4. Buying a 5c contract that pays $1 wins big when right. But in 2024 the same signal also bought Casey and
   Lake. Size so that a Pennsylvania doesn't wipe out a Michigan.

## Files

- **`scripts/market_history.py`** downloads the prices into
  `data/raw/market_history/2024/{ST}-{office}/{kalshi,polymarket}.csv` (not committed, 4 MB, about 11
  minutes). `index.csv` lists each contract and how it settled.
- **`scripts/primary_check.py`** runs every 2026 Senate/Governor primary with a market, against the 2024
  generals.
  - Downloads go to `data/raw/primaries/2026/` (NYT files and minute prices, cached).
  - It writes `data/processed/primary_check_2026.csv` (per race) and `primary_check_compare.csv`.
- **`scripts/co_primary_check.py`** runs the Colorado primary check: it downloads NYT's file and both
  venues' minute prices into `data/raw/primaries/` and writes `data/processed/co_gov_rep_2026_trend.csv`.
- **`scripts/market_check.py`** runs the 2024 check and prints every 2024 table here.
  - `data/processed/market_check_2024_points.csv`: every NYT update, with the market and projector
    probabilities.
  - `data/processed/market_check_2024_trades.csv`: every simulated trade.
- Kalshi moved settled markets to `/historical/*` (cutoff 2026-08-29): 1-minute candles with bid/ask, and
  the full trade tape. Polymarket keeps 1-minute prices (`/prices-history`) but no book history.
