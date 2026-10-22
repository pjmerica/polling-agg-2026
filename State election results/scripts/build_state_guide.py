"""Build STATE_BY_STATE.md: fills the history tables in scripts/state_guide_template.md
from the NYT files, so no number in those tables is typed by hand.

Template tokens: {{HISTORY:<state slug>}}  e.g. {{HISTORY:georgia}}

Per race (2020/2022/2024): when the first votes posted, share of the final vote counted by
midnight ET, who led early and when the lead changed hands, the call time, and the final margin.
Call times: 2022/2024 are AP's (NYT records called_by "ap" and the time it accepted the call);
2020 files hold NYT's own call time, which can differ from AP's (GA 2020: NYT Nov 13, AP Nov 19).

    py "State election results/scripts/build_state_guide.py"
"""
import datetime as dt
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw", "nyt")
ET = dt.timezone(dt.timedelta(hours=-5))  # EST: all of these elections fell after DST ended
ELECTION_DAY = {2020: dt.date(2020, 11, 3), 2022: dt.date(2022, 11, 8), 2024: dt.date(2024, 11, 5)}
REP = {"republican", "gop", "rep"}
RACE_LABEL = {"president": "President", "senate": "Senate", "us-senate": "Senate", "governor": "Governor"}
MIN_SHARE = 3.0  # ignore lead flips while under 3% of the vote is counted (first-batch noise)


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def clock(t, eday):
    """'9:28 pm' on election night, 'Wed 7:31 am' after, 'Nov 23' days later."""
    t = t.astimezone(ET)
    days = (t.date() - eday).days
    hm = t.strftime("%I:%M %p").lstrip("0").lower()
    if days == 0:
        return hm
    if days == 1:
        return f"Wed {hm}"
    return t.strftime("%b %d").replace(" 0", " ")


def load(path):
    year = int(os.path.basename(os.path.dirname(path)))
    state, race = os.path.basename(path)[:-5].split("-", 1)
    d = json.load(open(path, encoding="utf-8"))
    if year == 2020:
        r = d["data"]["races"][0]
        cands = {c["candidate_key"]: (c["last_name"], c["party_id"].lower(), c["votes"]) for c in r["candidates"]}
        pts = [(ts(t["timestamp"]), t["votes"], {k: s * t["votes"] for k, s in t["vote_shares"].items()})
               for t in r["timeseries"]]
        call = r.get("winnerCalledTimestamp")
        call = (dt.datetime.fromtimestamp(call / 1000, dt.timezone.utc), "NYT") if call else None
    else:
        r = d["races"][0]
        meta = r["candidate_metadata"]
        final = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in r["top_reporting_unit"]["candidates"]}
        cands = {k: (meta[k]["last_name"], str((meta[k].get("party") or {}).get("nyt_id", "")).lower(), v)
                 for k, v in final.items() if k in meta}
        pts = []
        for t in next(iter(d["timeseries"].values()), []):
            v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in t["candidates"] if c.get("votes")}
            pts.append((ts(t.get("greatest_updated_at") or t.get("provider_updated_at")),
                        t.get("total_votes") or sum(v.values()), v))
        o = r["outcome"]
        call = (ts(o["winner_accepted_at"][0]), "AP") if o.get("winner_accepted_at") else None
    pts = sorted((p for p in pts if p[1] > 0), key=lambda p: p[0])
    total = sum(v[2] for v in cands.values())
    ranked = sorted(cands, key=lambda k: -cands[k][2])
    reps = [k for k in ranked if cands[k][1] in REP]
    opps = [k for k in ranked if cands[k][1] not in REP]
    return dict(year=year, state=state, race=race, cands=cands, pts=pts, call=call, total=total,
                top=ranked[0], second=ranked[1], rep=reps[0] if reps else None, opp=opps[0] if opps else None)


def party(r, k):
    p = r["cands"][k][1]
    return "R" if p in REP else {"democrat": "D", "dem": "D"}.get(p, "I" if p in ("ind", "independent", "") else p[:3].upper())


def history_row(r):
    eday = ELECTION_DAY[r["year"]]
    a, b = r["top"], r["second"]
    margin = 100 * (r["cands"][a][2] - r["cands"][b][2]) / r["total"]
    result = f"{r['cands'][a][0]} ({party(r, a)}) +{margin:.1f}"
    first = clock(r["pts"][0][0], eday) if r["pts"] else "-"
    if r["year"] == 2024 and r["race"] == "president":
        first = "(timeline starts 8:00 pm)"
    midnight = dt.datetime.combine(eday + dt.timedelta(days=1), dt.time(0), ET)
    at_mid = max([p[1] for p in r["pts"] if p[0] <= midnight], default=0)
    mid = f"{min(100, 100 * at_mid / r['total']):.0f}%"
    # lead changes between the top two finishers, after MIN_SHARE of the vote is in
    # denominator: the running count can exceed the final top-two-round total (AK RCV races)
    denom = max([r["total"]] + [p[1] for p in r["pts"]])
    seq, prev = [], None
    for t, tot, v in r["pts"]:
        share = 100 * tot / denom
        if share < MIN_SHARE:
            continue
        lead = a if v.get(a, 0) >= v.get(b, 0) else b
        if lead != prev:
            seq.append((lead, t, share))
            prev = lead
    if not seq:
        leads = "-"
    else:
        # a lead held under 10 minutes is a near-tie trade, not a real change: collapse runs of those
        parts, i = [f"{r['cands'][seq[0][0]][0]} led first"], 1
        while i < len(seq):
            j = i
            while j + 1 < len(seq) and (seq[j + 1][1] - seq[j][1]).total_seconds() < 600:
                j += 1
            lead, t, share = seq[j]
            if j > i:
                parts.append(f"lead traded {clock(seq[i][1], eday)}-{clock(t, eday)}, "
                             f"{r['cands'][lead][0]} ahead from {clock(t, eday)} ({share:.0f}% in)")
            else:
                parts.append(f"{r['cands'][lead][0]} ahead {clock(t, eday)} ({share:.0f}% in)")
            i = j + 1
        leads = "; ".join(parts)
    if r["year"] == 2024 and r["race"] == "president":
        leads += " (timeline ends 5:40 am Wed)"
    call = f"{clock(r['call'][0], eday)} ({r['call'][1]})" if r["call"] else "-"
    return f"| {r['year']} | {RACE_LABEL.get(r['race'], r['race'])} | {first} | {mid} | {leads} | {call} | {result} |"


def history(state):
    races = [load(p) for p in sorted(glob.glob(os.path.join(RAW, "*", f"{state}-*.json")))]
    races.sort(key=lambda r: (r["year"], r["race"]))
    lines = ["| Year | Race | First votes (ET) | Counted by midnight ET | Who led, and when the lead changed (ET) | Called (ET) | Final |",
             "|---|---|---|---|---|---|---|"]
    lines += [history_row(r) for r in races]
    return "\n".join(lines)


DOCS = os.path.join(ROOT, "..", "docs")
PARTY = {"DEM": "D", "REP": "R", "IND": "I"}
SUFFIX = {"jr.", "jr", "sr.", "ii", "iii", "iv"}


def surname(name):
    words = [w for w in name.split() if w.lower() not in SUFFIX]
    return words[-1] if words else name


def forecast():
    """The forecast page's data (docs/forecast_data.js): model win chances plus its market column."""
    s = open(os.path.join(DOCS, "forecast_data.js"), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].strip().rstrip(";"))


def fill_numbers(text, data=None):
    """Model and market numbers come from the published forecast, never typed:
    {{MODEL:<race id>}} 'Bottoms 55.0%' (the model's favorite), {{MARKET:<race id>}} the market's
    chance for that same candidate, {{MATCHUP:<race id>}} 'Bottoms (D) 55.0% vs Jackson (R)',
    {{ASOF}} the model run and market refresh times."""
    data = data or forecast()
    races = {r["id"]: r for r in data["races"]}

    def fav(rid):
        r = races[rid]
        return r, sorted(r["cands"], key=lambda c: -(c.get("win") or 0))

    def model(m):
        r, c = fav(m.group(1))
        return f"{surname(c[0]['name'])} {100 * c[0]['win']:.1f}%"

    def market(m):
        r, c = fav(m.group(1))
        mk = r.get("market")
        if not mk or mk.get("prob") is None:
            return "no market"
        p = mk["prob"] if mk["name"] == c[0]["name"] else 1 - mk["prob"]
        return f"{surname(c[0]['name'])} {100 * p:.0f}%"

    def matchup(m):
        r, c = fav(m.group(1))
        a, b = c[0], c[1]
        return (f"{surname(a['name'])} ({PARTY.get(a['party'], a['party'])}) {100 * a['win']:.1f}% vs "
                f"{surname(b['name'])} ({PARTY.get(b['party'], b['party'])})")

    asof = (f"Model numbers: forecast run of {data['predictions_as_of'][:16].replace('T', ' ')} UTC. "
            f"Market numbers: {data['generated_at'][:16].replace('T', ' ')} UTC refresh.")
    text = re.sub(r"\{\{MODEL:([\w-]+)\}\}", model, text)
    text = re.sub(r"\{\{MARKET:([\w-]+)\}\}", market, text)
    text = re.sub(r"\{\{MATCHUP:([\w-]+)\}\}", matchup, text)
    return text.replace("{{ASOF}}", asof)


def main():
    tmpl = open(os.path.join(HERE, "state_guide_template.md"), encoding="utf-8").read()
    out = fill_numbers(tmpl)
    for state in ["alaska", "georgia", "ohio", "kansas", "texas", "nebraska", "maine", "iowa", "michigan",
                  "nevada", "oregon"]:
        out = out.replace("{{HISTORY:%s}}" % state, history(state))
    assert "{{" not in out, "unfilled token in template"
    with open(os.path.join(ROOT, "STATE_BY_STATE.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote STATE_BY_STATE.md")


if __name__ == "__main__":
    main()
