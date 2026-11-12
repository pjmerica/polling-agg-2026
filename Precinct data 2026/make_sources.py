"""Writes sources.json. Run by hand after changing a state's entry."""
import json
import os
from urllib.parse import quote

EV = {
    "GA": ("results.sos.ga.gov", "Georgia", "11032026GeneralAndSpecialElection"),
    "VA": ("enr.elections.virginia.gov", "Virginia", "2026-November-General"),
    "UT": ("electionresults.utah.gov", "Utah", "General11032026"),
    "ID": ("results.voteidaho.gov", "id", "nov2026"),
    "WA": ("results.votewa.gov", "washington", "20261103"),
}
FILES = {
    "MN": ["https://electionresultsfiles.sos.mn.gov/20261103/allracesbyprecinct.txt"],
    "HI": ["https://elections.hawaii.gov/wp-content/results/2026%20General/media.txt", "https://elections.hawaii.gov/wp-content/results/2026%20General/precinct.pdf"],
    "NC": ["https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2026_11_03/results_pct_20261103.zip"],
}
PAGES = {
    "AL": ["https://www.sos.alabama.gov/alabama-votes/voter/election-data"],
    "AR": ["https://results.enr.clarityelections.com/AR/"],
    "AZ": ["https://azsos.gov/elections/results-data"],
    "CA": ["https://statewidedatabase.org/election.html"],
    "CO": ["https://www.sos.state.co.us/pubs/elections/Results/Archives.html"],
    "CT": ["https://portal.ct.gov/sots/election-services/statement-of-vote/statement-of-vote"],
    "DE": ["https://elections.delaware.gov/results/"],
    "FL": ["https://dos.fl.gov/elections/data-statistics/elections-data/precinct-level-election-results/"],
    "IA": ["https://sos.iowa.gov/elections/results/index.html"],
    "ID": ["https://voteidaho.gov/election-results/"],
    "IL": ["https://www.elections.il.gov/electionoperations/downloadvotetotals.aspx"],
    "IN": ["https://www.in.gov/sos/elections/election-results/"],
    "KS": ["https://sos.ks.gov/elections/election-results.html"],
    "KY": ["https://www.elect.ky.gov/results/2020-2029/Pages/2026.aspx"],
    "LA": ["https://electionstatistics.sos.la.gov/"],
    "MA": ["https://electionstats.state.ma.us/"],
    "MD": ["https://elections.maryland.gov/elections/2026/election_data/index.html"],
    "ME": ["https://www.maine.gov/sos/elections-voting/results"],
    "MI": ["https://mvic.sos.state.mi.us/votehistory/Index"],
    "MO": ["https://www.sos.mo.gov/elections/s_default"],
    "MS": ["https://www.sos.ms.gov/elections-voting/election-results"],
    "MT": ["https://sosmt.gov/elections/results/"],
    "ND": ["https://www.sos.nd.gov/elections/election-results"],
    "NE": ["https://electionresults.nebraska.gov/"],
    "NH": ["https://www.sos.nh.gov/elections/elections/election-results"],
    "NJ": ["https://www.nj.gov/state/elections/election-information-results.shtml"],
    "NM": ["https://www.sos.nm.gov/voting-and-elections/election-results/"],
    "NV": ["https://www.nvsos.gov/sos/elections/election-resources"],
    "NY": ["https://elections.ny.gov/2026-election-results"],
    "OH": ["https://www.ohiosos.gov/elections/election-results-and-data/2026/"],
    "OK": ["https://oklahoma.gov/elections.html"],
    "OR": ["https://sos.oregon.gov/elections/Pages/electionhistory.aspx"],
    "PA": ["https://www.electionreturns.pa.gov/ReportCenter/Reports"],
    "RI": ["https://elections.ri.gov/elections/results/"],
    "SC": ["https://www.enr-scvotes.org/SC/"],
    "SD": ["https://sdsos.gov/elections-voting/election-resources/election-history/default.aspx"],
    "TN": ["https://sos.tn.gov/elections/results"],
    "TX": ["https://www.sos.state.tx.us/elections/historical/elections.shtml"],
    "VT": ["https://sos.vermont.gov/elections/election-info-resources/elections-results-data/"],
    "WI": ["https://elections.wi.gov/elections/election-results"],
    "WV": ["https://sos.wv.gov/elections/Pages/default.aspx"],
    "WY": ["https://sos.wyo.gov/Elections/"],
}
out = {}
for st, (h, j, e) in EV.items():
    out.setdefault(st, []).append({"kind": "enhanced_voting", "host": h, "jurisdiction": j, "election": e})
for st, u in FILES.items():
    out.setdefault(st, []).append({"kind": "files", "urls": u})
for st, p in PAGES.items():
    out.setdefault(st, []).append({"kind": "watch", "pages": p})
# Alaska: the results page links every file. During the count they sit under /enr/26GENR/results/ (precinct CSV with
# vote method, summary, one PDF per House district, the ballot-by-ballot record with every ranking); in 2024 the final
# copies and the ranked-choice round reports went to /results/24GENR/ under other names, so both folders are matched.
out["AK"] = [{"kind": "linked", "pages": ["https://www.elections.alaska.gov/election-results/"], "match": r"/(enr|results)/26GENR/.+\.(csv|pdf|zip|txt|json|xlsx?|html?)$"}]
out["VA"][0].update(wait_for=["Election Turnout", "Election Results", "Election Change Log Report"], wait_minutes=30)
out["NC"].append({"kind": "counts_only", "reducer": "nc", "url": "https://s3.amazonaws.com/dl.ncsbe.gov/ENRS/2026_11_03/absentee_20261103.zip", "name": "ballot-returns-by-precinct.csv"})
PA_QUERY = (
    "$select=countyname,congressional,party,ballot_status,ballotreturneddate,count(*) as ballots"
    "&$group=countyname,congressional,party,ballot_status,ballotreturneddate"
    "&$order=countyname,congressional,party,ballot_status,ballotreturneddate&$limit=2000000"
)
out.setdefault("PA", []).append({"kind": "counts_only", "reducer": "server", "name": "ballot-returns-by-date.csv", "url": "https://data.pa.gov/resource/nbwd-pfn4.csv?" + quote(PA_QUERY, safe="$=&,*()")})
# Pages that show ballot counts by county, saved when they change.
out["WA"].append({"kind": "files", "urls": ["https://www.sos.wa.gov/elections/data-research/election-data-and-maps/ballot-return-statistics"]})
out["FL"].append({"kind": "files", "urls": ["https://countyfilesvbm-ev.floridados.gov/VoteByMailEarlyVotingReports/PublicStats"]})
# UF Election Lab's compiled ballot counts: the national file and each state's county file (none for AK, AL, NH).
UF = "https://election.lab.ufl.edu/data-downloads/earlyvote/2026"
out["US"] = [{"kind": "files", "urls": [f"{UF}/US.csv"] + [f"{UF}/{s}_county.csv" for s in sorted(set(out) - {"AK", "AL", "NH", "US"})]}]
assert len(out) == 51, sorted(out)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
print(len(out), "states", sum(len(v) for v in out.values()), "sources")
