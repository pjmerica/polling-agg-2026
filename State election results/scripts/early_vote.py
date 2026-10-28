"""Ballots already cast in the twelve states, from the University of Florida Election Lab's 2026
early-vote tracker (https://election.lab.ufl.edu/early-vote/2026-early-voting/), which compiles each
state's own files.

Downloads the tracker's national CSV into data/raw/early_vote/US_<date>.csv (one copy per day, so the
build history is kept) and writes data/processed/early_vote_2026.csv. build_state_guide.py puts the
table in STATE_BY_STATE.md section 2c; rerun this script to refresh it before rebuilding.

    py "State election results/scripts/early_vote.py"
"""
import csv
import datetime as dt
import glob
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
URL = "https://election.lab.ufl.edu/data-downloads/earlyvote/2026/US.csv"
RAW = os.path.join(ROOT, "data", "raw", "early_vote")
OUT = os.path.join(ROOT, "data", "processed", "early_vote_2026.csv")
ORDER = ["GA", "SC", "OH", "MI", "TX", "KS", "ME", "IA", "NE", "NV", "OR", "AK"]
# What a 0 means in the tracker: not reported, or no such category this early
NOTES = {
    "GA": "Nearly all in person; Georgia has no party registration.",
    "OH": "In person estimated by the tracker (a ballot sent and received the same day); no party registration.",
    "MI": "Mail and clerk-office absentee only; Michigan's early in-person voting starts later (at least 9 days before Nov 3). No party registration.",
    "TX": "Texas doesn't report requests, so mail = mail ballots returned; no party registration.",
    "ME": "Absentee only (Maine counts in-person absentee as absentee); as of Oct 20.",
    "NV": "Nevada mails every active voter a ballot, so requests are ballots sent.",
    "OR": "All-mail state: requests are ballots sent to every voter.",
    "AK": "No party breakdown.",
}


def fetch(today=None):
    today = today or dt.date.today().isoformat()
    path = os.path.join(RAW, f"US_{today}.csv")
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if not data.startswith(b"state,"):
            raise SystemExit(f"unexpected download from {URL}: {data[:80]!r}")
        with open(path, "wb") as f:
            f.write(data)
    return path


def num(r, k):
    try:
        return int(float(r[k]))
    except (KeyError, ValueError):
        return 0


def rows(path=None):
    path = path or sorted(glob.glob(os.path.join(RAW, "US_*.csv")))[-1]
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["state_abbv"] not in ORDER:
            continue
        t22, voted = num(r, "turn_2022"), num(r, "voted_all")
        out.append(dict(state=r["state"], abbv=r["state_abbv"], as_of=r["last_update"], voted=voted,
                        pct_of_2022=round(100 * voted / t22, 1) if t22 else "", turnout_2022=t22,
                        mail_requested=num(r, "request_all"), mail_returned=num(r, "accept_all"),
                        in_person=num(r, "inperson_all"), dem=num(r, "voted_dem"), rep=num(r, "voted_rep"),
                        other=num(r, "voted_none"), source=r["data_source"], file=os.path.basename(path)))
    out.sort(key=lambda x: ORDER.index(x["abbv"]))
    return out


def table(data=None):
    """Markdown table for the guide (latest download)."""
    data = data or rows()

    def k(n):
        return f"{n / 1000:,.0f}K" if n >= 1000 else (str(n) if n else "-")

    out = ["| State | As of | Already voted | Share of 2022's total vote | Mail returned / sent or requested | Early in person | "
           "Voters' registered party (D / R / other) | Note |",
           "|---|---|---|---|---|---|---|---|"]
    for r in data:
        party = f"{k(r['dem'])} / {k(r['rep'])} / {k(r['other'])}" if r["dem"] or r["rep"] else "-"
        mail = f"{k(r['mail_returned'])} / {k(r['mail_requested'])}" if r["mail_requested"] else k(r["mail_returned"])
        out.append(f"| {r['state']} | {r['as_of']} | {k(r['voted'])} | {r['pct_of_2022']}% | {mail} | {k(r['in_person'])} | "
                   f"{party} | {NOTES.get(r['abbv'], '')} |")
    return "\n".join(out)


def main():
    path = fetch()
    data = rows(path)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)
    print(f"{len(data)} states from {os.path.basename(path)} -> {OUT}")


if __name__ == "__main__":
    main()
