"""How much the count moves after polls close, for every race NYT covered in the nine states.

Reads data/raw/nyt (2020/2022/2024 Gov/Sen/Pres) and data/raw/nyt_more (all 2022/2024 races,
2026 primaries). One row per race in data/processed/swings.csv:

  winner/runner-up, final margin (winner minus runner-up, % of all votes)
  share counted and margin at +1h, +2h, +3h after the state's main poll close, at midnight ET
  and at 6 am ET the next morning ("end of night"); who led at each point
  when the winner took the lead for good, and how much was counted then
  for generals: the same margins as Democrat/independent minus Republican ("dr")
  2022+: final margin among early/mail ("advance") votes and among Election Day votes

    py "State election results/scripts/swing_analysis.py"
"""
import csv
import datetime as dt
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed", "swings.csv")

STATES = {"alaska": "AK", "georgia": "GA", "ohio": "OH", "kansas": "KS", "texas": "TX",
          "nebraska": "NE", "maine": "ME", "iowa": "IA", "michigan": "MI", "nevada": "NV", "oregon": "OR"}
# main poll close, hours after midnight local ET on election day (AK: 8 pm Alaska = midnight ET)
CLOSE = {"GA": 19.0, "OH": 19.5, "MI": 20.0, "TX": 20.0, "KS": 20.0, "ME": 20.0,
         "IA": 21.0, "NE": 21.0, "NV": 22.0, "OR": 23.0, "AK": 24.0}
REP = {"republican", "gop", "rep"}
MIN_SHARE = 10.0  # who "leads" is only meaningful once some vote is in


def et_offset(day):
    """US Eastern offset for a date: DST from 2nd Sunday of March to 1st Sunday of November."""
    y = day.year
    mar = dt.date(y, 3, 8) + dt.timedelta(days=(6 - dt.date(y, 3, 8).weekday()) % 7)
    nov = dt.date(y, 11, 1) + dt.timedelta(days=(6 - dt.date(y, 11, 1).weekday()) % 7)
    return dt.timezone(dt.timedelta(hours=-4 if mar <= day < nov else -5))


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def races_2020(path, d):
    r = d["data"]["races"][0]
    state = STATES[r["state_slug"]]
    cands = {c["candidate_key"]: dict(name=c["last_name"], party=c["party_id"].lower(), votes=c["votes"])
             for c in r["candidates"]}
    pts = [(ts(t["timestamp"]), t["votes"], {k: s * t["votes"] for k, s in t["vote_shares"].items()})
           for t in r["timeseries"]]
    yield dict(file=path, race_id=r["race_id"], state=state, date=dt.date(2020, 11, 3), kind="G",
               office=r["race_name"], cands=cands, pts=pts, types=None, rcv=False, official="")


def races_new(path, d):
    for r in d["races"]:
        ts_list = (d.get("timeseries") or {}).get(r["nyt_id"])
        if not ts_list:
            continue
        state = r["nyt_id"][:2]
        if state not in CLOSE:
            continue
        meta = r.get("candidate_metadata") or {}
        cands, types = {}, {}
        for c in r["top_reporting_unit"]["candidates"]:
            v = c.get("votes") or {}
            m = meta.get(c["nyt_id"], {})
            cands[c["nyt_id"]] = dict(name=m.get("last_name", c["nyt_id"]),
                                      party=str((m.get("party") or {}).get("nyt_id", "")).lower(),
                                      votes=v.get("votes_round1", v.get("total", 0)))
            types[c["nyt_id"]] = v
        # Ranked-choice races: "total" is the final round. Compare the count with FIRST-round totals,
        # or the "swing" would mix counting with ranked-choice transfers.
        rcv = any("votes_round1" in t for t in types.values())
        initial = [rd for rd in (r.get("rounds") or []) if rd.get("round_type") == "initial"]
        if initial:
            rcv = True
            by_race_id = {m.get("nyt_candidate_race_id"): k for k, m in meta.items()}
            for c in initial[0]["candidates"]:
                k = by_race_id.get(c.get("nyt_candidate_race_id"))
                if k in cands:
                    cands[k]["votes"] = c.get("total", 0)
        pts = []
        for t in ts_list:
            v = {c["nyt_id"]: (c.get("votes") or {}).get("total", 0) for c in t["candidates"] if c.get("votes")}
            stamp = t.get("greatest_updated_at") or t.get("provider_updated_at")
            if stamp and sum(v.values()) > 0:  # RCV timelines end with zeroed points
                pts.append((ts(stamp), t.get("total_votes") or sum(v.values()), v))
        won = (r.get("outcome") or {}).get("won") or []
        official = cands[won[0]]["name"] if won and won[0] in cands else ""
        yield dict(file=path, race_id=r["nyt_id"], state=state, date=dt.date.fromisoformat(r["election_date"]),
                   kind=r.get("race_type_id") or "", office=r.get("office") or "", cands=cands, pts=pts,
                   types=types, rcv=rcv, official=official)


def analyse(r):
    cands = r["cands"]
    order = sorted(cands, key=lambda k: -cands[k]["votes"])
    if len(order) < 2:
        return None
    a, b = order[0], order[1]
    total = sum(c["votes"] for c in cands.values())
    pts = sorted((p for p in r["pts"] if p[1] > 0), key=lambda p: p[0])
    if not pts or total == 0:
        return None
    denom = max([total] + [p[1] for p in pts])
    tz = et_offset(r["date"])
    close = dt.datetime.combine(r["date"], dt.time(0), tz) + dt.timedelta(hours=CLOSE[r["state"]])
    midnight = dt.datetime.combine(r["date"] + dt.timedelta(days=1), dt.time(0), tz)
    morning = dt.datetime.combine(r["date"] + dt.timedelta(days=1), dt.time(6), tz)
    reps = [k for k in order if cands[k]["party"] in REP]
    opps = [k for k in order if cands[k]["party"] not in REP]
    general = r["kind"] == "G" and reps and opps
    rep, opp = (reps[0], opps[0]) if general else (None, None)

    def at(when):
        best = None
        for p in pts:
            if p[0] <= when:
                best = p
        return best

    def margin(p, x, y):
        return 100 * (p[2].get(x, 0) - p[2].get(y, 0)) / p[1]

    row = dict(year=r["date"].year, date=r["date"].isoformat(), state=r["state"], race_id=r["race_id"],
               kind=r["kind"], office=r["office"], winner=cands[a]["name"], winner_party=cands[a]["party"],
               runner_up=cands[b]["name"], final_margin=round(100 * (cands[a]["votes"] - cands[b]["votes"]) / total, 2),
               final_dr=round(100 * (cands[opp]["votes"] - cands[rep]["votes"]) / total, 2) if general else "",
               rcv="yes" if r["rcv"] else "",
               official_winner=r["official"],  # ranked-choice winner can differ from the first-round leader
               first_votes_et=pts[0][0].astimezone(tz).strftime("%m-%d %H:%M"))
    checkpoints = [("1h", close + dt.timedelta(hours=1)), ("2h", close + dt.timedelta(hours=2)),
                   ("3h", close + dt.timedelta(hours=3)), ("midnight", midnight), ("night_end", morning)]
    for name, when in checkpoints:
        p = at(when)
        row[f"pct_{name}"] = round(100 * p[1] / denom, 1) if p else ""
        row[f"margin_{name}"] = round(margin(p, a, b), 2) if p else ""
        row[f"dr_{name}"] = round(margin(p, opp, rep), 2) if (p and general) else ""
        row[f"leader_{name}"] = (cands[a]["name"] if p[2].get(a, 0) >= p[2].get(b, 0) else cands[b]["name"]) \
            if (p and 100 * p[1] / denom >= MIN_SHARE) else ""
    # when did the winner take the lead for good (after MIN_SHARE counted)
    last_change, last_pct = None, None
    prev = None
    for p in pts:
        share = 100 * p[1] / denom
        if share < MIN_SHARE:
            continue
        lead = a if p[2].get(a, 0) >= p[2].get(b, 0) else b
        if lead != prev:
            if lead == a:
                last_change, last_pct = p[0], share
            prev = lead
    row["winner_lead_for_good_et"] = last_change.astimezone(tz).strftime("%m-%d %H:%M") if last_change else ""
    row["pct_when_winner_took_lead"] = round(last_pct, 1) if last_pct is not None else ""
    # vote types (2022+): margin winner minus runner-up among advance and Election Day votes
    # Statewide units often carry only "total" and "advance"; Election Day (incl. provisionals) = total - advance.
    def vt(k, key):
        v = (r["types"] or {}).get(k, {})
        if key == "eday" and "advance" in v and "total" in v and "votes_round1" not in v:
            return v.get("election_day_in_person", v["total"] - v["advance"])
        return v.get(key)
    for kind, key in (("advance", "advance"), ("eday", "eday")):
        va, vb = vt(a, key), vt(b, key)
        tot = sum(vt(k, key) or 0 for k in cands)
        row[f"{kind}_margin"] = round(100 * (va - vb) / tot, 2) if (va is not None and vb is not None and tot) else ""
        row[f"{kind}_share"] = round(100 * tot / total, 1) if tot else ""
    return row


def main():
    rows = []
    files = glob.glob(os.path.join(RAW, "nyt", "*", "*.json")) + glob.glob(os.path.join(RAW, "nyt_more", "*", "*.json"))
    seen = set()
    for path in sorted(files):
        d = json.load(open(path, encoding="utf-8"))
        gen = races_2020(path, d) if "data" in d else races_new(path, d)
        for r in gen:
            if r["race_id"] in seen:  # same race in both folders
                continue
            seen.add(r["race_id"])
            x = analyse(r)
            if x:
                rows.append(x)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} races -> {OUT}")


if __name__ == "__main__":
    main()
