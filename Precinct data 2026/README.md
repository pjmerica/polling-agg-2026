# Precinct data 2026

Official precinct results and ballot counts for the Nov 3 2026 general, from each state's own site. The user asked for "individual precinct reporting" and "as much history of when they turned in their ballots", across all 50 states.

## How it runs

`.github/workflows/precinct-record.yml` runs `precinct_record.py` every 2 hours through Dec 15. A file is saved only when its content changed, so the copies show when each state's numbers moved during the late count. Nothing is overwritten: each pass with changes is its own release asset.

To change a state, edit `make_sources.py` and run it (it writes `sources.json`). A pass for some states only: `gh workflow run precinct-record.yml -f states=GA,VA`.

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
| `kind` | `enhanced_voting`, `files`, `counts_only` or `watch` (below) |
| `file` | The file, blank when the source gave none |
| `status` | `new` (changed, so saved), `same`, `nothing yet` (no 2026 general precinct file on the page), `refused 403` (the site refuses this script), or `error ...` |
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
| `counts_only` | A voter-level file reduced to counts; the raw file is never stored |
| `watch` | Reads a state's results page and fetches any 2026 general precinct file that appears on it |

## What each state had on 2026-11-05

**Precinct numbers being recorded (8)**

| State | What's in it |
|---|---|
| GA | Every contest by precinct, split into Election Day, advance, absentee by mail, provisional |
| VA | Results by precinct; turnout by precinct split by Election Day, early, mailed absentee, provisional, post-election; absentee counts by locality, district, age and gender; **a change log with a timestamp to the second for each entry, by precinct, contest and voting method** |
| NC | Results by precinct; ballots returned by precinct, party, method and **return date** |
| HI | Every contest by precinct, split into mail and in-person |
| MN | Every contest by precinct |
| UT | Every contest by precinct |
| ID | Every contest by precinct, plus ballots cast by precinct |
| WA | Every contest by precinct (Excel) |

**Watched: the site answers, no 2026 general precinct file yet (29).** These are AL, CA, CO, CT, DE, FL, IL, IN, KS, KY, LA, MA, MD, MO, MS, ND, NE, NJ, NM, NV, OK, OR, PA, RI, SC, SD, VT, WV, WY. AL, KS, FL, CO, CA, OR and MO have posted precinct files for earlier elections, so those should come after certification. The rest were not checked for a past pattern. Some publish by town or county rather than precinct (VT).

**Refused this script from a home connection (13).** These are AK, AR, AZ, IA, ME, MI, MT, NH, NY, OH, TN, TX, WI. The cloud pass may get a different answer: `precinct-log.csv` is the current state. Refusals are logged and left alone; don't work around them. Those files can be downloaded by hand in a browser and added.

Ohio requires each county board to upload a precinct file after certification, by a 2016 directive (not checked against current rules).

## What isn't here

- **Ballot-return dates** exist only for NC so far, with timestamps by precinct for VA. Other states' ballot-return files aren't surveyed yet.
- **NYT's precinct page** answers 403. It is not probed or worked around.
- **County sites.** Many states' precinct numbers sit on county sites (TX, PA, MI, OH, WI, NJ, NY), which this doesn't read. Third-party sets (UF Election Lab, OpenElections) usually arrive months later.

## Privacy

Only counts go in. NC's absentee file has names and addresses: `nc_counts` reduces it to counts and never writes the raw file. VA's change log names the local official who typed each entry: `drop_column` removes that column. `watch` skips links that look like voter files. `tests/test_precinct_record.py` covers all three.
