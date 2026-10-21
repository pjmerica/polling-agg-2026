# Maine: vote counting, reporting order and timing, and RCV, for the Nov 3, 2026 general election (US Senate, Governor)

Research date: 2026-10-21. Several primary sources (maine.gov/sos news releases, mainemorningstar.com) returned HTTP 403 to the fetch tool. Where that happened, the facts come from search snippets or secondary outlets, and they are marked as such. The statute text was read directly at legislature.maine.gov.

## 1. 2026 ballot: who is running, and how likely the Senate race goes to RCV rounds

### Takeaway
On the 2026 ballot, the Senate race is Susan Collins (R, incumbent) vs. Troy Jackson (D). Jackson replaced Graham Platner, who withdrew on July 10. Six declared write-in candidates have filed, so it is a ranked-choice ballot. Blank and write-in first choices count in the majority denominator. A tight two-way race can therefore still fall below 50% and trigger an RCV round, as ME-02 did in 2024. The Governor race is Pingree (D) / Charles (R) / Bennett (I) and is decided by plurality, with no RCV.

### Cited Findings
- General-election candidates: Susan Collins (R), seeking a sixth term, and Troy Jackson (D), former state Senate president, chosen by a nominating convention on July 25, 2026 to replace Graham Platner — [Wikipedia: 2026 US Senate election in Maine](https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Maine)
- Platner withdrew on July 10, 2026. Primary was June 9, 2026, and Collins was the only Republican to qualify — [Wikipedia](https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Maine)
- Independents: Tim Rich did not qualify and Phillip Rench withdrew. No independent is listed on the general ballot — [Wikipedia](https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Maine)
- On July 19, 2026, Shenna Bellows, Nirav Shah, Dan Kleban and Jordan Wood withdrew from the Democratic replacement contest. They had been seeking the nomination at the convention — [Wikipedia](https://en.wikipedia.org/wiki/2026_United_States_Senate_election_in_Maine)
- "Six write-in candidates file for Maine U.S. Senate race, prompting ranked-choice voting" (Aug 26, 2026). Names from the search snippet:
  - Brent Andrews of York (unaffiliated)
  - Sigrid Ann Olson of Cape Elizabeth (Democrat)
  - Gina Oswald of Strong (independent)
  - The other three were not visible; the article returned 403
  - Source: [Maine Morning Star (snippet only)](https://mainemorningstar.com/2026/08/26/six-write-in-candidates-file-for-maine-u-s-senate-race-prompting-ranked-choice-voting/)
- Statute (§723-A):
  - A candidate wins outright with more than 50% of first-place rankings, counted across all ballots cast for the office, including blank or overvoted first rankings (per the fetched summary of the statute text).
  - Otherwise the last-place candidate is eliminated round by round.
  - Last-place ties are decided by lot.
  - Source: [21-A MRSA §723-A](https://legislature.maine.gov/statutes/21-A/title21-Asec723-A.html)
- 2024 ME-02 precedent: Golden "fell shy of a majority with less than 49% of the votes cast because about 12,000 ballots were either blank or had write-in candidates", so an RCV round was needed — [AP Race Call via nationalnewswatch](https://nationalnewswatch.com/2024/11/15/ap-race-call-democrat-jared-golden-wins-reelection-to-u-s-house-in-maines-2nd-congressional-district)
- FairVote expects the Senate and ME-02 races to be close, so they could go to an RCV tally — [FairVote](https://fairvote.org/which-maine-elections-will-use-ranked-choice-voting-this-november/)
- Polls disagree. Marist (Oct 2026) has Jackson 51, Collins 47. A late-September survey had Collins 48, Jackson 46, undecided 6. Cook rates the race a Toss Up — [Marist](https://maristpoll.marist.edu/polls/midterm-elections-in-maine-october-2026/); [Cook](https://www.cookpolitical.com/senate/race/488601) (search-snippet summary)
- Governor 2026 general: Hannah Pingree (D), Bobby Charles (R), Rick Bennett (I).
  - It uses "the traditional plurality voting system", because RCV applies only to primaries and federal general elections.
  - Pingree won the June primary after 4 RCV rounds, 56–44 over Nirav Shah.
  - Source: [Wikipedia: 2026 Maine gubernatorial election](https://en.wikipedia.org/wiki/2026_Maine_gubernatorial_election)

### Inferences
- In a Collins–Jackson race, a first-round majority needs more than 50% of all Senate ballots, not just of the two-candidate vote, if blanks count in the denominator as the statute summary and the 2024 ME-02 case indicate.
- Using 2024 ME-02 as a rough guide, blank/write-in ballots could be around 2–3% statewide. On that assumption, the leader needs roughly a 51.5%+ two-way share to avoid RCV.
  - The 2024 figure was about 12k blank/write-in out of about 403k ME-02 ballots, roughly 3%. That denominator is inferred from the 197,151 + 194,445 final round plus exhausted ballots, so it is approximate.
  - A Senate race polling within ±2 has a meaningful chance (in my judgment, plausibly around 40–60%) of going to an RCV round, even with only two printed names.
- If an RCV round is needed, write-in and blank ballots mostly exhaust or redistribute in small numbers. The round-1 leader is very likely to win. That is why AP or media may call the race before tabulation when the lead is large enough (FairVote says this happened in 2024; see section 4).
- Two caveats about the 2024 example:
  - AP actually waited for RCV in 2024 ME-02, because the margin was under 1%.
  - FairVote's "as happened in 2024" may refer to the presidential race or ME-01. This is unclear.

### Gaps
- Could not read the full Maine Morning Star write-in article (403). The three other write-in names were not seen.
- Could not access the SoS official 2026 general candidate list.
- The exact wording of the §723-A majority denominator was summarized by the fetch tool, not quoted verbatim. Confirm it at the statute link before relying on it.

## 2. Election-night mechanics: poll close, absentee deadline, pre-processing, who reports results

### Takeaway
- Polls close at 8 p.m. ET statewide.
- Absentee ballots must reach the town clerk by 8 p.m. on Election Day.
- Towns may process (but not count) absentees from 7 days before Election Day if they gave 30 days' notice. No counts or results may be obtained before the polls close.
- Results are counted and reported by each municipality, not by county. Media and AP gather them through the night. Towns have 2 business days to file official returns with the SoS.

### Cited Findings
- Polls close at 8 p.m. Municipal officials tally results, which are reported throughout the evening — [Press Herald, June 3, 2026](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- Completed absentee ballots must be returned to municipal clerks by 8:00 p.m. on Election Day. Requests are accepted through Thursday, Oct 29, 2026 — [Central Maine / Kennebec Journal, Oct 20, 2026](https://www.centralmaine.com/2026/10/20/democrats-dominating-maine-absentee-voting-so-far/)
- Only ballots received by 8 p.m. on Election Day are counted, regardless of postmark. Absentees are not counted until after 8 p.m. — SoS guidance via search snippet: [Maine SoS Absentee Guide](https://www.maine.gov/sos/elections-voting/absentee-guide)
- Early processing (§760-B):
  - A municipality may begin processing absentee ballots on the 7th day before Election Day.
  - Processing hours run 7 a.m.–9 p.m.
  - Notice must reach the SoS and municipal party chairs at least 30 days before Election Day (by 5 p.m. on day 30). Without it, the town may not process early.
  - The SoS posts the list of participating towns at least one week before processing starts.
  - Source: [21-A MRSA §760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html)
- Prohibition on early results (§760-B and §759(6)):
  - Absentee ballots "may not be counted, voter intent may not be determined," and results may not be "obtained or released until after the polls have closed".
  - Towns with high-speed tabulators may not view results before polls close.
  - Sources: [§760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html); [§759](https://legislature.maine.gov/statutes/21-A/title21-Asec759.html)
  - §760-B refers to "high-speed ballot tabulator" equipment during early processing, which suggests ballots may be scanned in advance. The statute does not say so outright (fetch-tool reading).
- Election-day processing (§759(7)): a clerk who processes on Election Day must post notice at least 7 days before, giving the start times — [§759](https://legislature.maine.gov/statutes/21-A/title21-Asec759.html)
- Most recent amendments to both sections: PL 2025 c. 397 (§759 §47, §760-B §48). §760-B was also amended in 2021 and 2023 — [§759](https://legislature.maine.gov/statutes/21-A/title21-Asec759.html); [§760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html)
- Counting methods vary by town: some count by hand, others use tabulators — [SoS absentee video 2024 (PDF transcript, snippet)](https://www.maine.gov/sos/sites/maine.gov.sos/files/content/assets/Absentee-20Voting-20Video-202024-20Update.pdf)
- Returns deadline (§711(3)):
  - The clerk files the attested return "within 2 business days after election day".
  - If it is not delivered by 5 p.m. on the 2nd business day, the SoS may send a courier, and the town pays for it.
  - Source: [21-A MRSA §711](https://legislature.maine.gov/statutes/21-A/title21-Asec711.html)
- Towns have two days to report to the state, but "enough data typically comes in on election night for the state to know if a ranked-choice runoff is needed". Chief Deputy SoS Kate McBrien: "We will be able to announce, 'Here are the races that are going to RCV,' and what day we're planning to start that." If that is not known on election night, the announcement comes the next morning — [Press Herald](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- Reporting units are municipalities; CD2 alone has "more than 370 towns" — [Maine SoS release, Nov 15, 2018](https://www.maine.gov/sos/news/2018/CD2rankedchoiceresult.111518.html)
- Absentee volume and partisanship to date. As of Oct 17, 2026, 101,777 absentee ballots had been returned and accepted (about 11% of registered voters).
  - Party split so far:
    - Democrats 53%, unaffiliated about 25%.
    - 17% of registered Democrats have returned ballots vs. 7% of Republicans.
  - Prior cycles at the same point:
    - 2022: about 77,700 returned. Democrats were 54% at this point and finished at 49% of the absentee vote.
    - 2024: just under 130,000 returned. Democrats were 47% at this point and finished at 42%.
  - Rejected so far: 775 ballots (0.76%).
  - Source: [Central Maine, Oct 20, 2026](https://www.centralmaine.com/2026/10/20/democrats-dominating-maine-absentee-voting-so-far/)

### Inferences
- There is no statewide pre-count of absentees. Each town reports a combined absentee + in-person total once it finishes, so Maine does not show a strong "early blue then red" pattern in timing.
- Small hand-count towns (rural, often more Republican) may report later at night, while big tabulator towns (Portland, Lewiston, Bangor) may report earlier. This is a common pattern, but no source here quantifies it for Maine.
- Absentees lean Democratic. Their effect depends on whether a given town reports them together with or separately from in-person ballots. No source here confirms the practice.

### Gaps
- Did not verify whether the SoS posts any unofficial results on election night or only days later. The assignment premise says it posts later, but no source in this session confirmed that.
  - Media (BDN, Press Herald, AP) compile town-by-town results on election night, but I found no source text describing the AP stringer process.
- The figure of "about 500 municipalities" statewide was not verified in this session.
- The list of towns doing early processing in 2026 (posted on the SoS site) was not retrieved.

## 3. RCV tabulation process and timeline; certification; recounts

### Takeaway
- If no candidate exceeds 50% of first choices, the SoS has law enforcement collect sealed memory devices (tabulator towns) and paper ballots in locked boxes (hand-count towns) from every municipality and bring them to Augusta.
- Central tabulation runs 9 a.m.–5 p.m. and is livestreamed. It historically starts around 3–7 days after the election, and results arrive about 7–10 days after the election.
- Certification must happen within 20 days.
- A recount request is due within 5 business days and is limited to the top three candidates in RCV races. There is no deposit if the margin is ≤1% or ≤1,000 votes, whichever is less.

### Cited Findings
- Collection and handling:
  - The SoS uses law enforcement to collect materials.
  - Tabulator towns send sealed packages containing memory devices.
  - Hand-count towns send actual ballots in locked metal boxes to Augusta.
  - Materials are kept in a locked room.
  - Staff work 9 a.m.–5 p.m., loading ballots into a high-speed tabulator, unsealing and uploading memory devices, and hand-entering unreadable ballots.
  - The process is livestreamed on YouTube.
  - Each race's formula takes about 10–15 minutes to run. The office gives 2 hours' notice before the final step.
  - "The process usually takes about a week… It can be longer. It can be shorter" (McBrien). It can take up to two weeks statewide.
  - Statewide runoffs take longer because more municipalities are involved.
  - Source: [Press Herald, June 3, 2026](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- The state waits until all votes are processed and verified before running the first RCV tally. Results could come "anywhere from election night to the following week", or about ten days if close — [FairVote](https://fairvote.org/which-maine-elections-will-use-ranked-choice-voting-this-november/)
- June 2026 primary (statewide precedent):
  - Tabulation began Friday, June 12, at 1 p.m. (3 days after the June 9 primary) at Department of Public Safety HQ in Augusta.
  - The target was before Juneteenth (June 19). Delays, including sending law enforcement to retrieve ballots from South Berwick, pushed the final count back a day.
  - The count finished 10 days after Election Day, "similar to… previous statewide counts… since 2018".
  - Sources: [search summary of Maine Morning Star / Press Herald / SoS](https://www.pressherald.com/2026/06/12/ranked-choice-tabulation-starts-in-key-maine-primary-races/); [Maine Monitor](https://themainemonitor.org/inside-final-day-ranked-choice-voting-count/)
- June 2026: one city "inadvertently sent the wrong flash drive", causing a rescan. This is a partisan outlet's account — [The Maine Wire](https://www.themainewire.com/2026/06/maine-ranked-choice-count-marred-by-flash-drive-error-delayed-results-and-ballot-rescanning-as-bellows-offers-no-public-explanation/)
- Cost of the June 2026 RCV tabulation (3 primary races): $245,932.63 — [WABI, Sept 14, 2026](https://www.wabi.tv/2026/09/14/ranked-choice-tabulation-maines-primary-cost-more-than-245000/)
- Bellows ran in the June 2026 Democratic governor primary (eliminated in RCV round 2). She recused herself from the June tabulation, which was run by McBrien and Deputy SoS Julie Flynn — [Press Herald](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- Certification (§722): "Within 20 days after an election, the Secretary of State shall tabulate the election returns" and submit the certified tabulation to the Governor. RCV races are tabulated under §723-A. The tabulation is final when sent, except for contests with a pending recount — [21-A MRSA §722](https://legislature.maine.gov/statutes/21-A/title21-Asec722.html)
- 2024 certification deadline: Nov 25, 2024 (22 days after the Nov 3 election; the deadline may reflect weekend/holiday rules) — [BDN, Nov 13, 2024 (snippet)](https://www.bangordailynews.com/2024/11/13/politics/shenna-bellows-narrates-ranked-choice-tabulations-live/)
- Recount rules (§737-A):
  - Deadline:
    - A non-winning candidate must request a recount in writing "within 5 business days after the election".
    - In RCV races, only a candidate in the top three at the end of the penultimate round may request one.
  - Deposit for federal/statewide races:
    - None if the margin is ≤1% of total votes or ≤1,000 votes, "whichever is less".
    - Otherwise the greater of $5,000 or 10% of the estimated first-stage cost.
  - Process:
    - The recount is held "as soon as reasonably possible".
    - For multicounty offices the SoS may retrieve ballots in stages until the requester concedes.
    - For US Senate, disputed ballots that could affect the outcome go to the US Senate, not the state supreme court.
  - Source: [21-A MRSA §737-A](https://legislature.maine.gov/statutes/21-A/title21-Asec737-A.html)
- An automatic recount occurs only in an exact tie — [Press Herald](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- The SoS must post the full cast vote record once certified results are reported — [§723-A](https://legislature.maine.gov/statutes/21-A/title21-Asec723-A.html)

### Inferences
- A statewide Senate RCV round would need materials from every municipality, not just the roughly 370 in CD2. Expect the result about 7–12 days after Nov 3, i.e. roughly Nov 10–15, 2026.
- Collection would likely start Nov 4–6 and central tabulation around Nov 6–10. Nov 11 (Veterans Day) may slow things.
- If the margin is under 1% or under 1,000 votes, a free recount and certification-level delays are possible, as in 2024 ME-02, which was resolved on Dec 4.

### Gaps
- The SoS rules (Chapter 535, RCV procedures) on transport timing were not read.
- No SoS statement specific to the Nov 2026 general-election RCV timeline was found. The SoS "General Election is two months away" release returned 403.

## 4. Historical record 2018–2024 (dates, calls, RCV durations)

### Takeaway
Every RCV general so far (ME-02 2018, 2022 and 2024) produced a result 7–12 days after the election, and the round-1 leader won each time. Clear-majority statewide races were called on election night (Gov 2022) or the next day (Sen 2020).

### Cited Findings
- **2018 ME-02 (Golden vs. Poliquin, with Bond and Hoar):**
  - Nov 7: ballots to be collected from clerks Thursday (Nov 8) and tabulation to begin Friday (Nov 9).
  - Nov 9: count begun in Augusta.
  - Nov 15: result announced after "5 1/2 days of processing results from the more than 370 towns". Final round: Golden 139,231, Poliquin 136,326. Tabulated at noon at the Elkins Building.
  - Nov 26: Poliquin requested a recount. Certified totals: Golden 142,440, Poliquin 138,931 (six towns' results had not uploaded properly).
  - Sources: [BDN Nov 7 2018](https://bangordailynews.com/2018/11/07/politics/maines-toss-up-2nd-district-appears-headed-to-a-ranked-choice-count/); [SoS Nov 15 2018](https://www.maine.gov/sos/news/2018/CD2rankedchoiceresult.111518.html); [SoS Nov 26 2018](https://www11.maine.gov/sos/news/2018/poliquinrecount.html)
  - The recount was later terminated, and a federal court challenge occurred: [SoS: recount terminated](https://www.maine.gov/sos/news/2018/recountcd2terminated.html) (title only; details not read).
- **2020 US Senate (Collins vs. Gideon + 2 others):**
  - Collins won a majority of first-place votes in a 4-candidate field, so no RCV rounds were needed.
  - At 95% reporting, Collins led about 51–42.
  - Gideon conceded on Wednesday, Nov 4, and AP called the race "shortly after Gideon conceded".
  - Source: [PBS NewsHour/AP](https://www.pbs.org/newshour/politics/gop-sen-susan-collins-wins-reelection-in-maine)
  - Note: final polls had shown Gideon ahead, so the result moved against the polling.
- **2022 Governor (Mills vs. LePage, plurality):** AP called it for Mills on election night, Nov 8, 2022 — [WHRO/NPR](https://whro.org/national-news/2022-11-09/maine-gov-janet-mills-wins-second-term-defeating-former-gop-gov-paul-lepage)
- **2022 ME-02 (Golden vs. Poliquin vs. Bond):**
  - Election-night totals: Golden 48%, Poliquin 45%, Bond 7%.
  - The SoS announced RCV on Nov 9.
  - The RCV result came on Wednesday, Nov 16, one day late, because three memory sticks (Bangor, Hampden, Anson) failed to upload and about 17,000 paper ballots were run on site.
  - Final: Golden 165,136, Poliquin 146,142 (about 53–47).
  - Sources: [Spectrum News](https://spectrumlocalnews.com/me/maine/news/2022/11/16/golden-declared-victor-in-2nd-cd-race); [BDN](https://www.bangordailynews.com/2022/11/16/politics/jared-golden-wins-3rd-term/); [WAGM Nov 9 2022](https://www.wagmtv.com/2022/11/09/secretary-state-announces-ranked-choice-tabulation-congressional-district-2/); [WABI](https://www.wabi.tv/2022/11/16/ranked-choice-tabulation-results-congressional-district-2-expected-wednesday-night/)
- **2024 ME-02 (Golden vs. Theriault, 2 names plus write-ins/blanks):**
  - Golden declared victory on Nov 6 without an AP call.
  - The round-1 gap was 1,414 votes, with Golden under 49% because of about 12,000 blank/write-in ballots.
  - Tabulation began Tuesday, Nov 12 (one week after Election Day), and the result was announced Friday, Nov 15: Golden 50.35% (197,151 vs. 194,445).
  - AP called it for Golden on Nov 15 at 8:50 p.m. ET. Earlier that day AP had held off pending SoS information on whether the result would survive a recount.
  - Theriault had requested a recount, which the SoS confirmed on Nov 22. He ended it and conceded on Dec 4, 2024.
  - Sources: [Fox News](https://www.foxnews.com/politics/toss-up-maine-house-race-moves-ranked-choice-tabulation-golden-theriault-separated-1414-votes.amp); [WABI Nov 15 2024](https://www.wabi.tv/2024/11/15/maine-awaits-results-ranked-choice-voting-tabulation-second-congressional-district); [AP race call](https://nationalnewswatch.com/2024/11/15/ap-race-call-democrat-jared-golden-wins-reelection-to-u-s-house-in-maines-2nd-congressional-district); [WABI Nov 22 2024](https://www.wabi.tv/2024/11/22/recount-will-be-held-maines-2nd-congressional-district-race-heres-when-it-begins/); [Maine Morning Star](https://mainemorningstar.com/?p=6364); [Maine Public Nov 6 2024](https://www.mainepublic.org/politics/2024-11-06/jared-golden-declares-victory-in-maines-2nd-district-but-a-potential-recount-looms)
- **2024 President:** Maine paused RCV for presidential elections ("ranked voting in presidential election put on hold in Maine"); details were not read — [PBS](https://www.pbs.org/newshour/politics/ranked-voting-in-presidential-election-put-on-hold-in-maine)

### Inferences
- RCV timing: Election Day to result was 9 days in 2018 (Nov 6 to Nov 15), 8 days in 2022 (Nov 8 to Nov 16), 10 days in 2024 (Nov 5 to Nov 15) and 10 days in the June 2026 primary.
  - A Senate RCV result in 2026 would most likely come around Nov 11–14.
  - That would be followed by a possible recount if the margin is under 1% (no deposit).
- In none of the three RCV generals did RCV reverse the round-1 leader. With only write-ins as third options in 2026, a reversal would be even less likely.
- AP calls in close RCV races have waited for tabulation, and in 2024 they also waited on recount durability.

### Gaps
- Not found: % of votes reported by midnight for any of these races; exact AP call times for 2020 Sen, 2022 Gov and 2024 President; the direction of in-count shifts (early vs. late towns).
- 2018 AP call date was not found.
- 2024 presidential results timing was not researched. PBS covers only the RCV pause.

## 5. Law changes since 2022 affecting 2026

### Takeaway
- The Nov 2025 Question 1, which would have required photo ID, ended ongoing absentee status for seniors and voters with disabilities, limited drop boxes, cut 2 days of absentee voting and banned prepaid postage, failed by roughly 60–64% No. Absentee rules for 2026 are therefore unchanged by it.
- Both absentee-processing statutes were amended by PL 2025 c. 397. Its content was not reviewed.

### Cited Findings
- Question 1 (Nov 4, 2025) was rejected. AP called it at about 50% counted with No at 60–40. NBC showed about 64–36 with 98.9% in — [Maine Public](https://www.mainepublic.org/politics/2025-11-04/mainers-reject-voter-id-absentee-ballot-restrictions-as-question-1-fails); [NBC](https://www.nbcnews.com/politics/2025-elections/maine-ballot-measures); [Fox Baltimore/Sinclair](https://foxbaltimore.com/news/nation-world/no-on-1-campaign-declares-victory-against-voter-id-referendum-in-maine)
- Question 1 would have eliminated two days of absentee voting, barred phone and family absentee requests, ended automatic absentee status for seniors and people with disabilities, banned prepaid return postage and limited drop boxes — [Sinclair syndicate](https://foxbaltimore.com/news/nation-world/no-on-1-campaign-declares-victory-against-voter-id-referendum-in-maine)
- §759 and §760-B were amended by PL 2023 c. 304 and PL 2025 c. 397 — [§759](https://legislature.maine.gov/statutes/21-A/title21-Asec759.html); [§760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html)

### Inferences
- The question's text implies Maine already has ongoing (automatic) absentee status for seniors and people with disabilities, and drop boxes. These stay in place for 2026.

### Gaps
- The enacting law and year for ongoing absentee status (believed to be 2023) were not verified.
- Drop box statute details were not verified.
- The content of PL 2025 c. 397 was not reviewed.

## 6. What the SoS office has said about 2026 timing

### Takeaway
No Nov 2026-specific timing statement was retrieved. For the June 2026 primary, the office (McBrien) said RCV races are identified on election night or the next morning, tabulation usually takes "about a week" and statewide counts can take up to two weeks.

### Cited Findings
- McBrien's statements on timing — [Press Herald June 3 2026](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/)
- WABI: first-choice results should be clear from municipal reports on election night, but the full RCV process could take more than a week — [WABI June 5 2026](https://www.wabi.tv/2026/06/05/when-maine-ranked-choice-results-could-come-which-race-may-be-first/)

### Inferences
- Bellows recused herself from the June count because she was a gubernatorial candidate. She is not a November candidate (she lost the primary and withdrew from the Senate replacement contest), so she may oversee the November count directly. This is not confirmed.

### Gaps
- The SoS 2026 general-election press releases (maine.gov/sos/news) were blocked (403).
- The official results page (maine.gov/sos/cec/elec/results) was not accessed in this session.
