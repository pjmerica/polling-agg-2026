# Sources: when and how results get reported

For each competitive-race state, the sources that say **when** results come in and **what is in each
batch**. Compiled 2026-10-21; keep adding as new pieces appear (see "Watching for new sources").

**Status labels**
- **read**: we read the document itself.
- **snippet**: known only from a search-result summary; confirm before relying on it.
- **pending**: not published yet.

## The main source: AP "Decision Notes: What to expect in [state]"

AP publishes one per state before every election. Each one covers:
- poll-close times;
- what share of the vote was cast early;
- which ballots and counties come in the first update;
- when AP reported the first votes last time, and how far the count got by the end of the night;
- recount rules.

The **Nov 3, 2026 general-election editions are not out yet** (checked 2026-10-21). AP usually posts
them in the last one to two weeks before the election. The 2026 primary editions below were written
under this year's laws. Full texts are saved locally in `data/raw/ap_2026/` and are not committed,
because they are AP copyright.

| State | AP 2026 edition (status: read) | What it says about reporting |
|---|---|---|
| Alaska | [Aug 17 primary](https://www.washingtonpost.com/politics/2026/08/17/alaska-primary-senate-house-governor/ea0f3d20-9a34-11f1-9cc) (text via WTOP) | Polls close midnight ET; one Aleutian location closes 1 a.m. ET. **First update** is a mix of Election Day and early in-person votes; nearly all of those are in by the last update of the night, and the **bulk of mail votes comes in the following days**. 2024 primary: first results 1:03 a.m. ET; the night ended 4:58 a.m. ET at ~89% counted; 100% reached 12 days later. |
| Georgia | [May 18 primary](https://www.usnews.com/news/politics/articles/2026-05-18/ap-decision-notes-what-to-expect-in-georgias-primaries) | Polls close 7 p.m. ET. Counties release mail and early in-person results at the start of the night; **more than half the counties release all or almost all of them in the first update**. 2022 primary: first results 7:13 p.m.; last update 3:29 a.m. at ~99%. Says "no automatic recount", but that predates the June 2026 law (see conflicts below). |
| Ohio | [May 4 primary](https://www.clickondetroit.com/news/politics/2026/05/04/ap-decision-notes-what-to-expect-in-ohios-state-primaries/) | Polls close 7:30 p.m. ET. **All 88 counties release all or almost all early and absentee results in the first update**, in most cases before any Election Day results. 2024 presidential primary: first results 7:36 p.m.; ~90% by 10:19 p.m.; last update 1:28 a.m. at >99%. Automatic recount below 0.25% statewide. |
| Kansas | [Aug 3 primary](https://wtop.com/news/2026/08/ap-decision-notes-what-to-expect-in-the-kansas-state-primary/) | Polls close 8 p.m. ET in most of the state and 9 p.m. ET in the Mountain-time part. 2022 governor primary: first results 8:24 p.m.; past halfway ~10:02 p.m.; last update 3:31 a.m. at ~96%. |
| Texas | [Mar 2 primary](https://www.clickondetroit.com/news/politics/2026/03/02/ap-decision-notes-what-to-expect-in-the-texas-state-primaries/) | Most polls close 8 p.m. ET, the far west 9 p.m. ET. **AP makes no statewide call before 9 p.m. ET.** A large share of results posts between 8 and 9 p.m. Counties release all or nearly all early and absentee results in the first update, before any Election Day results. 2024 Senate primary: first results 8:09 p.m.; last update 4:41-5:46 a.m. at 96-98%. Recount automatic only on a tie; a loser may request one if within 10% of the leader's vote. |
| Nebraska | [May 11 primary](https://wtop.com/news/2026/05/ap-decision-notes-what-to-expect-in-nebraskas-primaries/) | All polls close 9 p.m. ET. **More than three-quarters of the 93 counties release all or nearly all early and absentee votes in the first update**, often before any Election Day votes. Nearly two-thirds, including Douglas and Lancaster, release few or no Election Day votes in it. 2024 Senate primary: first results 9:00 p.m.; ~90% by 12:10 a.m.; ~98% at 1:35 a.m. |
| Maine | [Jun 8 primary](https://wtop.com/news/2026/06/ap-decision-notes-what-to-expect-in-maines-state-primary/) | Polls close 8 p.m. ET. 2024 general: first results 8:44 p.m.; ~50% by 12:54 a.m.; counting stopped 4:11 a.m.; ~90% by 3:13 p.m. the next day. Recount automatic only on a tie (2025 law); requests are free within 1% or 1,000 votes. |
| Iowa | [Jun 2 primary](https://wtop.com/government/2026/06/ap-decision-notes-what-to-expect-in-iowas-state-primary/) | Polls close 9 p.m. ET. **Nearly all counties release absentee-by-mail results at the start of the night**; counties vary on when they release in-person absentee results. 2022 primary: first results 9:12 p.m.; last update 2:29 a.m. at >99%. Recount on request if under 0.15% (statewide/federal). |
| Michigan | [Aug 3 primary](https://wtop.com/news/2026/08/ap-decision-notes-what-to-expect-in-michigans-state-primary/) | Polls close 8 p.m. ET (9 p.m. ET in four UP counties). The first updates statewide mix mail, early in-person and Election Day votes. **Wayne, Oakland, Macomb, Kent, Genesee and Washtenaw release relatively few results of any type in their first updates.** 2024 Senate primary: first results 8:03 p.m.; past halfway 12:03 a.m.; ~95% by 4:12 a.m. Automatic recount at 0.1% or less. |

Earlier general-election editions, used in the report: [Ohio 2024](https://www.pbs.org/newshour/politics/what-to-expect-in-ohio-on-election-day),
[Iowa 2024](https://srnnews.com/ap-decision-notes-what-to-expect-in-iowa-on-election-day/),
[Kansas 2024](https://www.aol.com/ap-decision-notes-expect-kansas-221653746.html),
[Nebraska](https://www.pbs.org/newshour/politics/what-to-expect-in-nebraska-on-election-day). These give 2020 benchmarks:
- Ohio: first votes 7:39 p.m., ~95% counted by midnight.
- Iowa: first votes 9:11 p.m. CT, ~82% counted by 11 p.m. CT.
- Nebraska: first votes 9:02 p.m. ET, ~71% counted by midnight.

## Official state sources

| State | Source | Status | What it says |
|---|---|---|---|
| Alaska | [Division of Elections 2026 General Media Packet](https://www.elections.alaska.gov/doc/mp/2026/MediaPacket-2026-General.%20V3.pdf) and [counting system and schedule](https://www.elections.alaska.gov/ballot-counting-process/counting-system-and-schedule/) | read | First results 8:45-9:00 p.m. Alaska time (~12:45-1:00 a.m. ET); later updates announced on social media and email. Count days Nov 10, 13, 18; RCV tabulation Nov 18; certification target Nov 25. Confirmed by [Alaska Public Media, Oct 5](https://alaskapublic.org/news/politics/elections/2026-10-05/what-to-know-about-alaskas-general-election). |
| Ohio | [Directive 2026-22](https://www.ohiosos.gov/assets/directive-2026-22-unofficial-official-canvass-checklist.pdf), the canvass checklist for the May 2026 primary | read | Start tabulating absentees after 7:31 p.m.; log in by 7:45 p.m.; **upload absentee totals by 8 p.m.** (partial if necessary); then "upload summary level files at assigned intervals until 100 percent of precincts are reported". |
| Ohio | [Directive 2026-48](https://www.ohiosos.gov/assets/dir2026-48-canvass-and-certification-of-the-november-3-2026-general-election.pdf), canvass for **Nov 3, 2026** | snippet | Same 8 p.m. absentee upload. Absentee scanning (not tabulating) allowed from Oct 6. ohiosos.gov blocks downloads and no archive copy exists; read it in a browser. Earlier directives assign large counties (e.g. Cuyahoga, Franklin, Summit) to a **15-minute ("quarter-hour") upload cycle**; the 2026 list is not confirmed. |
| Texas | [SOS Advisory 2026-21](https://www.sos.texas.gov/elections/laws/advisory2026-21-november-3-election-law-calendar.shtml), Nov 3 election calendar | read | Deadlines: mail ballots received by 5 p.m. Nov 4; military/overseas, cures and provisional ID by Nov 9; local canvass Nov 6-17. Gives no posting times. |
| Georgia | [SB 189 (2024)](https://gov.georgia.gov/document/2024-signed-legislation/sb-189/download) | read | By law, early in-person and pre-Election-Day absentee votes are counted and reported by 8 p.m. ET, or within 1 hour of the county's last poll closing. |
| Michigan | [MCL 168.765a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-168-765a) | read | Absentee tabulation allowed up to 8 days before; no results released before 8 p.m. |
| Iowa | [Iowa Code §53.23](https://www.legis.iowa.gov/docs/code/53.23.pdf) | read | Absentee board staffed to finish by 10 p.m. CT; it **releases nothing until its whole count is done**, so each county's absentee vote lands as one lump. |
| Nebraska | [Neb. Rev. Stat. 32-1027](https://nebraskalegislature.gov/laws/statutes.php?statute=32-1027); [SoS 2022 release](https://sos.nebraska.gov/sites/default/files/doc/news-releases/Media%20Release%20November%208%2C%202022%2C%20General%20Election%20is%20less%20than%20a%20month%20away.pdf) | read / snippet | Early ballots may be counted from 24 hours before polls open; in larger counties the first results posted are early voting, Election Day ballots later. |
| Maine | [21-A §760-B](https://legislature.maine.gov/legis/statutes/21-a/title21-Asec760-B.html); [Press Herald, Jun 3 2026](https://www.pressherald.com/2026/06/03/it-could-take-days-to-know-the-winners-of-the-maine-primaries-heres-why/) | read | No absentee counting or results before 8 p.m. ~500 towns report on their own; there is no central live feed, and AP and the Bangor Daily News collect results from clerks. |
| Kansas | [K.A.R. 7-36](https://sos.ks.gov/) (cited in research notes) | read | Election-night returns include advance ballots counted that day; late-arriving mail and provisionals are counted at the canvass. |

## County release schedules

No county has published a **Nov 3, 2026** posting-time schedule yet (searched 2026-10-21). What exists:

| County | Source | Status | What it says |
|---|---|---|---|
| Sedgwick, KS (Wichita) | [2026 primary final-unofficial release](https://www.sedgwickcounty.org/communications/news-releases/final-unofficial-election-night-results-for-2026-primary-election/) | snippet | Election night includes early in-person, advance by mail and all Election Day in-person ballots. **Mail ballots dropped off on Election Day come in a Wednesday-afternoon update.** Provisionals are counted at the canvass. |
| Johnson, KS (Overland Park) | [2026 primary partial results, update 2](https://www.jocoelection.org/sites/default/files/2026-08/PR2026%20Unofficial%20Partial%20Results%20-%20Advance%20and%20Election%20Day%20Update%202_0.pdf); [Nov 3 page](https://www.jocoelection.org/events-elections/november-3-2026-general-election) | read (Nov page) | Primary updates were labeled "Advance and Election Day". The Nov page has no schedule yet. The research notes report early votes posting around 7:30 p.m. CT. |
| Douglas, NE (Omaha) | [3 News Now](https://www.3newsnow.com/news/investigations/high-turnout-delayed-early-ballot-reporting-in-douglas-county-election-commissioner-says) | read (undated, likely 2024) | Early ballots were released "in several phases". **About 18,000 votes were left after election night**, including 4,600 provisionals and 7,400 drop-box ballots from Election Day. A 2024 schedule of 8:00, 8:45, 9:45, 10:45 and 11:45 p.m. CT is snippet-only. |
| Franklin, OH (Columbus) | search summary of local reporting | snippet | The initial release is the absentee batch, and results could run into the early hours. |
| Harris, TX (Houston) | [KHOU, 2024](https://khou.com/article/news/politics/inside-politics/texas-politics/harris-county-late-election-results/287-75cffb28-971f-405d-bf9a-06acf9920f41) | snippet | Central count at NRG Stadium; in 2024 the administrator hoped to finish around 1-2 a.m. |
| Tarrant, TX (Fort Worth) | [Nov 3, 2026 results page](https://www.tarrantcountytx.gov/en/elections/past-election-information/2026-archives/november-3--2026--joint-general-and-special-election-results.html) | snippet | Page is up: graphical election-night reporting, cumulative and precinct reports. No times. |
| Polk, IA (Des Moines) | [WHO 13](https://digital-release.who13.com/?p=713830); [auditor site](https://polkelectionia.gov) | snippet | Absentee results are typically the first released (2024 comment by the auditor). |
| Portland, ME | [Bangor Daily News 2020](https://bangordailynews.com/2020/11/02/politics/how-to-follow-maines-election-results-with-us-on-tuesday/) | snippet | Usually among the first complete towns, but in 2022 its absentee tallies were still out at midnight. Some towns report only the next day. |
| Detroit / Wayne, MI | [WDIV, Oct 14 2026](https://www.clickondetroit.com/news/local/2026/10/14/why-arent-michigan-election-results-instant-how-our-votes-are-counted/); [Bridge Michigan](https://bridgemi.com/michigan-government/want-faster-election-results-michigans-new-absentee-ballot-count-option-helps/) | read / snippet | 1,500+ clerks report independently. Flint skipped pre-processing in the Aug 2026 primary and its results came the next morning. No Detroit schedule found. |

Not found anywhere: schedules for Fulton, DeKalb, Cobb and Gwinnett (GA), Cuyahoga (OH), Dallas, Bexar and
Travis (TX), Lancaster and Sarpy (NE), Linn and Johnson (IA), Oakland and Kent (MI).

## Conflicts to keep in mind

- **Georgia recounts.** AP (May 2026) says Georgia has no automatic recount. The June 2026 special-session law
  adds an automatic hand recount for Governor/Lt. Governor at 0.5% or less ([Fox 5](https://www.fox5atlanta.com/news/georgia-election-bill-deadlines-new-law-delays-ballot-qr-code-removal)).
  The AP piece predates the law.
- **Nebraska recounts.** AP: automatic at 1% of the **total vote**. Statute 32-1119: 1% of the **leading candidate's** votes.
  Use the statute.
- **Maine recounts.** The research notes cite §737-A request rules; AP adds that recounts became automatic on a tie under a 2025 law.
- **Iowa first results.** AP gives 12 minutes after close (2022 primary) and 71 minutes (2020 general: first votes 9:11 p.m. CT).
  Both are right: NYT's timelines show first votes at 9:10 p.m. ET in 2022 and 10:13 p.m. ET in 2020. 2020 was the slow year.

## Watching for new sources

`scripts/watch_sources.py` searches Google News and Bing News for:
- AP "What to expect" pieces for the nine states;
- results-schedule news for the large counties;
- secretary-of-state election-night announcements.

New items go to `sources/watch_log.csv`. AP **general-election** editions for our states are also listed in
`sources/NEW_AP_GENERAL.md`. Windows task `StateResults-SourceWatch` runs it twice a day through Nov 3.
When an AP general edition appears: read it (WTOP and local TV station sites republish AP and load fine;
apnews.com and US News block scripts), save the text to `data/raw/ap_2026/`, and update the table above.
