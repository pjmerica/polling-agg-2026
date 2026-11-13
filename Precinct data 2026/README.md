# Precinct data 2026

Official precinct results and ballot counts for the Nov 3 2026 general, from each state's own site. The user asked for "individual precinct reporting" and "as much history of when they turned in their ballots", across all 50 states.

## How it runs

`.github/workflows/precinct-record.yml` runs `precinct_record.py` every 2 hours through Dec 15. GitHub starts this repo's scheduled runs hours late, so each job takes three passes 2 hours apart and then dispatches the next job; the cron only restarts the chain if it breaks. `precinct-log.csv` shows every pass. A file is saved only when its content changed, so the copies show when each state's numbers moved during the late count. Nothing is overwritten: each pass with changes is its own release asset.

To change a state, edit `make_sources.py` and run it (it writes `sources.json`). A pass for some states only: `gh workflow run precinct-record.yml -f states=GA,VA -f chain=false` (it waits for the running job to end).

## Where the data is

On the release `election-night-2026`:

- `precinct-record-{stamp}.tar.gz`: the files that changed in that pass, as `{state}/{file}/{stamp}-{file}`.
- `precinct-log.csv`: every pass and every source.
- `precinct-state.json`: the current hash of each file.

### `precinct-log.csv` columns

| Column | Meaning |
|---|---|
| `pass_utc` | When the pass ran (UTC) |
| `state` | Two-letter state |
| `kind` | `enhanced_voting`, `files`, `linked`, `counts_only` or `watch` (below) |
| `file` | The file, blank when the source gave none |
| `status` | `new` (changed, so saved), `same`, `nothing yet` (no 2026 general precinct file on the page), `refused 403` (the site refuses this script), or `error ...` (`refused challenge` inside it: the site answered with a "prove you are human" page, which is not saved) |
| `bytes` | File size |
| `sha` | First 16 characters of the content hash |

### `precinct-state.json` fields, per `{state}/{file}`

| Field | Meaning |
|---|---|
| `sha` | Content hash, leaving out stamps that change on every publish |
| `first` | The pass that first saved this file |
| `changed` | The pass that last saved a changed copy |
| `copies` | How many copies have been saved |
| `bytes` | Size of the latest copy |

### Source kinds

| Kind | What it does |
|---|---|
| `enhanced_voting` | Results software used by GA, VA, UT, ID and WA: the election record, its published reports, and the whole-state export |
| `files` | Fixed file addresses |
| `linked` | Reads a results page and fetches every file it links under a named folder (Alaska) |
| `counts_only` | A voter-level file reduced to counts; the raw file is never stored |
| `watch` | Reads a state's results page and fetches any 2026 general precinct file that appears on it |

## What each state had on 2026-11-05

**Precinct numbers being recorded (9; Alaska since 2026-11-12)**

| State | What's in it |
|---|---|
| GA | Every contest by precinct, split into Election Day, advance, absentee by mail, provisional |
| VA | Results by precinct; turnout by precinct split by Election Day, early, mailed absentee, provisional, post-election; absentee counts by locality, district, age and gender; **a change log with a timestamp to the second for each entry, by precinct, contest and voting method** |
| NC | Results by precinct; ballots returned by precinct, party, method and **return date** |
| HI | Every contest by precinct, split into mail and in-person |
| AK | Every contest by precinct, split into Election Day, absentee, early, questioned and remote (`GA_ENR_Precinct_State_of_Alaska.csv`); the summary; one report per House district (`HD*.pdf`); **the ballot-by-ballot record with every ranking** (`CVR_Export.zip`, no voter names), which is what the ranked-choice rounds are run from |
| MN | Every contest by precinct |
| UT | Every contest by precinct |
| ID | Every contest by precinct, plus ballots cast by precinct |
| WA | Every contest by precinct (Excel) |

**Watched: the site answers, no 2026 general precinct file yet (30).** These are AL, AR, AZ, CA, CO, CT, DE, FL, IL, IN, KS, KY, LA, MA, MD, MO, MS, ND, NE, NJ, NM, OK, OR, PA, RI, SC, SD, VT, WV, WY. AL, KS, FL, CO, CA, OR and MO have posted precinct files for earlier elections, so those should come after certification. The rest were not checked for a past pattern. Some publish by town or county rather than precinct (VT).

**Refused the cloud job (11).** These are IA, ME, MI, MT, NH, NV, NY, OH, TN, TX, WI, as of the first pass. Refusals are logged and left alone; don't work around them. Those files can be downloaded by hand in a browser and added. `precinct-log.csv` is the current state.

**Alaska (fixed 2026-11-12): two faults, nothing saved for nine days.**

1. *Alaska's server.* From Nov 5 to the 21:06 UTC pass on Nov 12, all 126 passes failed with "unable to get local issuer certificate". By the 23:06 UTC pass the same address, same code, answered normally, and a runner test at 23:46 could not reproduce the error. So the fault was on Alaska's side and it was corrected that evening. The error text is what Linux reports when a server leaves out its issuer's certificate; browsers and Windows fetch the missing one themselves, which is why the site looked fine from a PC. That reading fits but can't be proved after the fact. `get()` now does what a browser does (`context_with_issuer`): it fetches the certificate the server's own certificate names and verifies as usual, to a root the machine already trusts. Tested against a server with an incomplete chain (accepted) and self-signed, untrusted-root and wrong-host ones (still rejected).
2. *Our address.* The job watched `/results/26GENR/`, a guess from 2024's final folder. It has no listing and answers 403, so even with a working certificate nothing would have been saved. The files are linked from `https://www.elections.alaska.gov/election-results/` and sit under `/enr/26GENR/results/` during the count. The job now reads that page and takes every file it links under `/enr/26GENR/` or `/results/26GENR/`, so the ranked-choice round reports (Nov 18) and the final copies are picked up under whatever names they get.

Copies start with the Nov 11 publish; Alaska's earlier publishes (Nov 3-10) were not kept by anyone here. The ballot-count report under `/wp-content/uploads/` answers scripts with a "prove you are human" page and is left alone.

The lesson for the 11 refusing states and the 30 watched ones: their addresses were also written before the election and never checked in a browser. A 403 on a folder is not always a refusal.

Ohio requires each county board to upload a precinct file after certification, by a 2016 directive (not checked against current rules).

## Ballots cast and when

| Source | What's in it | Date of return? |
|---|---|---|
| NC | Ballots by precinct, party, method | Yes, by day |
| PA | Mail ballots by county, congressional district, party, status | Yes, by day |
| VA | Change log of the count, by precinct, contest, method | When entered, to the second (not when the voter returned it) |
| US (UF Election Lab) | `US.csv` and `{state}_county.csv`: requested and accepted ballots by county in 47 states, split by party, age, race and gender where the state reports them. `US.csv` names each state's source. Licensed CC BY-NC-ND (non-commercial, credit UF) | No, totals only |
| WA, FL | Each state's ballot-count page, saved when it changes | Only as the copies change |

Copies from before this record exist only for UF's national file: `State election results/data/raw/early_vote/` has Oct 23, Oct 27, Nov 2 and Nov 3.

## What isn't here

- **Ballot-return dates in other states.** `US.csv` lists every state's source; GA, TX, OH, WI and others may have daily files, not yet read. Voter-level files must be reduced to counts.
- **NYT's precinct page** answers 403. It is not probed or worked around.
- **County sites.** Many states' precinct numbers sit on county sites (TX, PA, MI, OH, WI, NJ, NY), which this doesn't read. Third-party sets (UF Election Lab, OpenElections) usually arrive months later.

## Privacy

Only counts go in. NC's absentee file has names and addresses: `nc_counts` reduces it to counts and never writes the raw file. PA's has birth months and home coordinates: its server counts them and the rows never arrive. VA's change log names the local official who typed each entry: `drop_column` removes that column. `watch` skips links that look like voter files. `tests/test_precinct_record.py` covers all three.
