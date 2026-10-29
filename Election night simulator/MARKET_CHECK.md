# Did the 2024 markets misread the count?

Checked 2026-10-28 against Kalshi's and Polymarket's minute-by-minute 2024 prices (`market_history.py`) and
NYT's count timelines for every state (`market_check.py`). It covers the 65 President, Senate and Governor races
whose market was between 3% and 97% at poll close, and 9,107 NYT updates from 5% to 99% counted.

**Short answer:**
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
- **`scripts/market_check.py`** runs this check and prints every table here.
  - `data/processed/market_check_2024_points.csv`: every NYT update, with the market and projector
    probabilities.
  - `data/processed/market_check_2024_trades.csv`: every simulated trade.
- Kalshi moved settled markets to `/historical/*` (cutoff 2026-08-29): 1-minute candles with bid/ask, and
  the full trade tape. Polymarket keeps 1-minute prices (`/prices-history`) but no book history.
