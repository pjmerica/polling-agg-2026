"""County benchmarks for the competitive 2026 Governor and Senate races.

For every county (Maine: its towns added up; Alaska: House districts), the share of the statewide
vote it should cast and what each candidate should get there for any statewide result: a tie (the
benchmark line), a 3-point win either way, and the model's margin. On election night a county that
has finished counting and beats its tie line points to a statewide lead; docs/election-night.html
turns county results into an implied statewide margin.

Method:
  1. Turnout: the county's share of the 2022 statewide vote for governor (the last midterm).
  2. Lean: the county's two-party share for the D/I-side candidate in two recent races (RACES:
     the 2024 presidential race plus the most comparable race for the seat, the same candidate's
     last statewide race where there is one), averaged on the log-odds scale.
  3. A statewide result: one log-odds shift for every county (uniform swing), solved so that the
     turnout-weighted two-party share hits the target.
  4. Early vs Election Day (GA, TX, IA, the states where NYT split every county by vote type; in
     Ohio and Michigan only Hamilton and Wayne are split): the county's gap between its early/mail
     and its Election Day vote in that race, re-centred so the two parts add up to the county's share.
  5. Backtest: the same method predicting every 2022 and 2024 race from the races before it, given
     the true statewide result: how far counties land from their line, and how wrong a statewide
     estimate from one finished county was.

Inputs: data/raw/nyt (fetch_nyt_history.py), data/raw/wayback_2020 (fetch_wayback_2020.py), the
Alaska Division of Elections precinct files (downloaded here into data/raw/ak_doe) and
docs/forecast_data.js. Writes data/processed/county_benchmarks.csv, county_backtest.csv and
county_benchmarks.json (read by build_master.py and build_election_night.py).

    py "State election results/scripts/county_benchmarks.py"
"""
import collections
import csv
import datetime as dt
import glob
import json
import math
import os
import re
import statistics as st
import urllib.request

import build_state_guide as g

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw")
NYT = os.path.join(RAW, "nyt")
OUT = os.path.join(ROOT, "data", "processed")
AK_SRC = {
    "2024": ("https://www.elections.alaska.gov/results/24GENR/ENRbyPrecinct.csv", "ENRbyPrecinct_2024.csv"),
    "2022": ("https://elections.alaska.gov/results/22GENR/Results_per_Precinct_2022_11_30T14_17_52_To%20Excel.txt",
             "Results_per_Precinct_2022.txt"),
}
NAMES = {"georgia": "Georgia", "ohio": "Ohio", "michigan": "Michigan", "texas": "Texas", "kansas": "Kansas",
         "maine": "Maine", "iowa": "Iowa", "nebraska": "Nebraska", "nevada": "Nevada", "oregon": "Oregon",
         "alaska": "Alaska"}

# (label, source, D/I-side key, R key). Sources are NYT files under data/raw/nyt ({s} = state slug) or
# "ak:<year>:<contest>" for Alaska's precinct files (keys there match candidate names by substring).
P24 = ("2024 President", "2024/{s}-president.json", "harris-k", "trump-d")
RACES = [
    dict(id="2026_GA_Governor", state="georgia", seat="Governor",
         bases=[P24, ("2022 Senate (Warnock-Walker)", "2022/georgia-us-senate.json", "warnock-r", "walker-h")],
         types=("2022 Senate", "2022/georgia-us-senate.json", "warnock-r", "walker-h")),
    dict(id="2026_OH_Governor", state="ohio", seat="Governor",
         bases=[P24, ("2022 Senate (Ryan-Vance)", "2022/ohio-us-senate.json", "ryan-t", "vance-j")]),
    dict(id="2026_OH_Senate-S", state="ohio", seat="Senate (special)",
         bases=[P24, ("2024 Senate (Brown-Moreno)", "2024/ohio-us-senate.json", "brown-s", "moreno-b")]),
    dict(id="2026_MI_Senate", state="michigan", seat="Senate",
         bases=[P24, ("2024 Senate (Slotkin-Rogers)", "2024/michigan-us-senate.json", "slotkin-e", "rogers-m")]),
    dict(id="2026_TX_Senate", state="texas", seat="Senate",
         bases=[P24, ("2024 Senate (Allred-Cruz)", "2024/texas-us-senate.json", "allred-c", "cruz-t")],
         types=("2024 Senate", "2024/texas-us-senate.json", "allred-c", "cruz-t")),
    dict(id="2026_TX_Governor", state="texas", seat="Governor",
         bases=[P24, ("2022 Governor (O'Rourke-Abbott)", "2022/texas-governor.json", "orourke-b", "abbott-g")],
         types=("2024 Senate", "2024/texas-us-senate.json", "allred-c", "cruz-t")),
    dict(id="2026_KS_Senate", state="kansas", seat="Senate",
         bases=[P24, ("2020 Senate (Bollier-Marshall)", "2020/kansas-senate.json", "bollierb", "marshallr")]),
    dict(id="2026_ME_Senate", state="maine", seat="Senate",
         bases=[P24, ("2020 Senate (Gideon-Collins)", "2020/maine-senate.json", "gideons", "collinss")]),
    dict(id="2026_IA_Senate", state="iowa", seat="Senate",
         bases=[P24, ("2022 Senate (Franken-Grassley)", "2022/iowa-us-senate.json", "franken-m", "grassley-c")],
         types=("2024 President", "2024/iowa-president.json", "harris-k", "trump-d")),
    # Osborn's independent coalition doesn't look like a Democrat's, so his own 2024 race is the only base
    dict(id="2026_NE_Senate", state="nebraska", seat="Senate",
         bases=[("2024 Senate (Osborn-Fischer)", "2024/nebraska-us-senate.json", "osborn-d", "fischer-d")]),
    dict(id="2026_NV_Governor", state="nevada", seat="Governor",
         bases=[P24, ("2022 Governor (Sisolak-Lombardo)", "2022/nevada-governor.json", "sisolak-s", "lombardo-j")]),
    dict(id="2026_OR_Governor", state="oregon", seat="Governor",
         bases=[P24, ("2022 Governor (Kotek-Drazan)", "2022/oregon-governor.json", "kotek-t", "drazan-c")]),
    dict(id="2026_AK_Senate", state="alaska", seat="Senate",
         bases=[("2024 President", "ak:2024:U.S. President / Vice President", "Harris/Walz", "Trump/Vance"),
                ("2024 House (Peltola-Begich, first choices)", "ak:2024:U.S. Representative", "Peltola", "Begich")]),
]
SCEN = 3.0  # the "wins by" scenarios, two-party points
BACKTEST_STATES = ["georgia", "ohio", "michigan", "texas", "kansas", "maine", "iowa", "nebraska", "nevada", "oregon"]


def logit(p):
    p = min(max(p, 0.01), 0.99)
    return math.log(p / (1 - p))


def expit(x):
    return 1 / (1 + math.exp(-x))


# ---------- loading results by county ----------

_units, _names = {}, {}


def county_names(slug):
    """FIPS -> county name, from the 2020 presidential file (Maine's 2022/2024 files are by town)."""
    if slug not in _names:
        r = json.load(open(os.path.join(NYT, "2020", f"{slug}-president.json"), encoding="utf-8"))["data"]["races"][0]
        _names[slug] = {c["fips"]: c["name"] for c in r["counties"]}
    return _names[slug]


def nyt_units(path, slug):
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    if "data" in d:  # 2020 race-page format: final county results
        for c in d["data"]["races"][0]["counties"]:
            out[c["fips"]] = {"name": c["name"], "votes": dict(c["results"]), "adv": {}}
        return out
    for u in d["races"][0]["reporting_units"]:
        if u["level"] not in ("county", "township"):
            continue
        fips = f"{u.get('fips_state') or ''}{u.get('fips_county') or ''}"
        if len(fips) != 5:
            continue
        name = u["name"] if u["level"] == "county" else county_names(slug).get(fips, fips)
        x = out.setdefault(fips, {"name": name, "votes": collections.Counter(), "adv": collections.Counter()})
        for c in u["candidates"]:
            v = c.get("votes") or {}
            x["votes"][c["nyt_id"]] += v.get("total") or 0
            if "advance" in v:  # write-ins often lack the split; only the two main candidates need it
                x["adv"][c["nyt_id"]] += v.get("advance") or 0
    return out


def ak_file(year):
    url, name = AK_SRC[year]
    path = os.path.join(RAW, "ak_doe", name)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


# Alaska House districts (2022 plan, used 2022-2026), named after their largest precincts in 2024
AK_HD = {1: "Ketchikan, Wrangell", 2: "Sitka, Petersburg, Craig", 3: "Juneau: Mendenhall Valley; Haines",
         4: "Juneau, Douglas", 5: "Kodiak, Cordova", 6: "Homer, Kasilof, Anchor Point", 7: "Kenai, Soldotna",
         8: "Sterling, Nikiski", 9: "South Anchorage, Girdwood", 10: "Anchorage: Oceanview", 11: "Anchorage: Hillside",
         12: "Anchorage: Southeast", 13: "Anchorage: South Midtown", 14: "Anchorage: North Midtown",
         15: "Anchorage: Southwest", 16: "Anchorage: West", 17: "Anchorage: Downtown",
         18: "Anchorage: JBER, Government Hill", 19: "Anchorage: Airport Heights, Mountain View",
         20: "Anchorage: University", 21: "Anchorage: East", 22: "Anchorage: Northeast", 23: "Eagle River",
         24: "Chugiak, Peters Creek", 25: "Palmer, Butte", 26: "Knik-Goose Bay", 27: "Wasilla, Meadow Lakes",
         28: "Mat-Su: Seldon, Lakes", 29: "Fishhook, Valdez", 30: "Big Lake, Willow, Houston", 31: "Fairbanks",
         32: "Fairbanks, Badger, Fort Wainwright", 33: "North Pole area", 34: "Fairbanks: Steese, Farmers Loop",
         35: "Fairbanks: Chena, University", 36: "Goldstream, Delta Junction, Tok", 37: "Aleutians, Dillingham",
         38: "Bethel", 39: "Nome, Unalakleet", 40: "Utqiagvik, Kotzebue"}


def ak_hd(precinct):
    """House district of an Alaska precinct row: '01-600 Ketchikan No. 1', 'District 1 - Absentee'.
    The statewide 'HD99 Fed Overseas Absentee' row (federal-only ballots, a few hundred) is left out."""
    m = re.match(r"(\d\d)-\d\d\d ", precinct) or re.match(r"District (\d+)\s", precinct)
    return str(int(m.group(1))) if m else None


def ak_place(precinct):
    return re.sub(r"\s+No\.\s*\d+$", "", re.sub(r"^\d\d-\d\d\d\s+", "", precinct)).strip()


def ak_units(year, contest):
    rows = []  # (precinct, candidate, votes)
    if year == "2024":
        for r in csv.DictReader(open(ak_file("2024"), encoding="utf-8", errors="replace")):
            if r["Contest_title"] == contest:
                rows.append((r["Precinct_name"], r["candidate_name"], int(r["total_votes"] or 0)))
    else:  # tab-separated blocks: contest title, a "Precinct" header, one row per precinct
        lines = open(ak_file("2022"), encoding="utf-16").read().splitlines()
        cands = None
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.split("\t")]
            if cells[0] == "Precinct":
                cands = [c.strip('"') for c in cells[1:]] if lines[i - 1].startswith(contest) else None
                continue
            if cands is None or not ak_hd(cells[0]):
                continue
            for name, n in zip(cands, cells[1:]):
                if name:
                    rows.append((cells[0], name, int(n.replace(",", "") or 0)))
    out, places = {}, collections.defaultdict(collections.Counter)
    for prec, cand, n in rows:
        hd = ak_hd(prec)
        if not hd:
            continue
        out.setdefault(hd, {"votes": collections.Counter(), "adv": {}})["votes"][cand] += n
        if re.match(r"\d\d-\d\d\d ", prec):
            places[hd][ak_place(prec)] += 1
    for hd, u in out.items():
        u["name"] = f"District {hd} ({AK_HD.get(int(hd), places[hd].most_common(1)[0][0] if places[hd] else '?')})"
    if not out:
        raise SystemExit(f"Alaska {year}: no rows for contest {contest!r}")
    return out


def units(src, slug):
    src = src.format(s=slug)  # "2024/{s}-president.json" is one file per state
    if src not in _units:
        if src.startswith("ak:"):
            _, year, contest = src.split(":", 2)
            _units[src] = ak_units(year, contest)
        else:
            _units[src] = nyt_units(os.path.join(NYT, src), slug)
    return _units[src]


def votes(u, key):
    """A candidate's votes in a unit: exact key, or (Alaska) every key containing it."""
    v = u["votes"]
    return v[key] if key in v else sum(n for k, n in v.items() if key.lower() in k.lower())


def two_party(u, d, r):
    a, b = votes(u, d), votes(u, r)
    return a / (a + b) if a + b > 0 else None


# ---------- the method ----------

def solve(L, w, target):
    """Log-odds shift s with sum_c w_c * expit(L_c + s) = target (w sums to 1)."""
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if sum(w[k] * expit(L[k] + mid) for k in w) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def split(a, la, le, share):
    """Early/mail and Election Day two-party shares that keep the county's gap between them and add
    up (with early/mail making up `a` of the two-party vote) to `share`."""
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if a * expit(la + mid) + (1 - a) * expit(le + mid) < share:
            lo = mid
        else:
            hi = mid
    u = (lo + hi) / 2
    return expit(la + u), expit(le + u)


def margin(share):
    return 100 * (2 * share - 1)


def target(m):
    return (1 + m / 100) / 2


def turnout(slug):
    src = "ak:2022:Governor" if slug == "alaska" else "2022/{s}-governor.json"
    us = units(src, slug)
    return {k: sum(u["votes"].values()) for k, u in us.items()}


def timing_2020():
    """Share of each county's certified 2020 presidential vote counted by midnight and 6 am ET, from
    the Internet Archive copies of NYT's national file (fetch_wayback_2020.py)."""
    utc = dt.timezone.utc
    points = {"mid": dt.datetime(2020, 11, 4, 5, 0, tzinfo=utc), "six": dt.datetime(2020, 11, 4, 11, 0, tzinfo=utc)}
    seen = {}
    for path in sorted(glob.glob(os.path.join(RAW, "wayback_2020", "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        t = dt.datetime.strptime(d["capture"], "%Y%m%d%H%M%S").replace(tzinfo=utc)
        for name, when in points.items():
            if t <= when:
                for slug, s in d["states"].items():
                    for c in s.get("counties", []):
                        seen.setdefault((slug, c["fips"]), {})[name] = c.get("votes") or 0
    out = {}
    for slug in NAMES:
        if slug == "alaska":  # 2020 used the old House districts and reported absentees a week later
            continue
        final = {c["fips"]: c["votes"] for c in json.load(open(os.path.join(NYT, "2020", f"{slug}-president.json"),
                                                                  encoding="utf-8"))["data"]["races"][0]["counties"]}
        for fips, tot in final.items():
            x = seen.get((slug, fips))
            if x and tot:
                out[(slug, fips)] = {k: round(min(100.0, 100 * v / tot), 1) for k, v in x.items()}
    return out


def forecast_sides(data, rid):
    """D/I-side and Republican candidate from the forecast, and the model's margin for the D/I side
    (each candidate's margin comes from a separate model; half their difference, as in
    build_competitive.py)."""
    r = next(x for x in data["races"] if x["id"] == rid)
    cs = sorted(r["cands"], key=lambda c: -(c.get("win") or 0))
    rep = next(c for c in cs if c["party"] == "REP")
    dem = next(c for c in cs if c["party"] != "REP")
    m = (dem["margin"] - rep["margin"]) / 2 if dem.get("margin") is not None and rep.get("margin") is not None else None
    return dem, rep, m


def build_race(cfg, data, timing):
    slug = cfg["state"]
    t = turnout(slug)
    bases = []
    for label, src, d, r in cfg["bases"]:
        us = units(src, slug)
        bases.append((label, {k: two_party(u, d, r) for k, u in us.items()}, us))
    keys = [k for k in t if t[k] > 0 and all(b[1].get(k) is not None for b in bases)]
    dropped = sorted(set(t) - set(keys))
    if dropped:
        print(f"  {cfg['id']}: left out {dropped} (no turnout or no base result)")
    tot = sum(t[k] for k in keys)
    w = {k: t[k] / tot for k in keys}
    L = {k: sum(logit(b[1][k]) for b in bases) / len(bases) for k in keys}
    names = {k: bases[0][2][k]["name"] for k in keys}
    dem, rep, model_m = forecast_sides(data, cfg["id"])
    shifts = {"tie": solve(L, w, 0.5), "d3": solve(L, w, target(SCEN)), "r3": solve(L, w, target(-SCEN))}
    if model_m is not None:
        shifts["model"] = solve(L, w, target(model_m))
    typ = {}
    if cfg.get("types"):
        label, src, d, r = cfg["types"]
        us = units(src, slug)
        for k in keys:
            u = us.get(k)
            if not u or d not in u["adv"] or r not in u["adv"]:
                continue
            da, ra = u["adv"].get(d, 0), u["adv"].get(r, 0)
            de, re_ = votes(u, d) - da, votes(u, r) - ra
            if da + ra <= 0 or de + re_ <= 0:
                continue
            typ[k] = dict(a=(da + ra) / (da + ra + de + re_), la=logit(da / (da + ra)), le=logit(de / (de + re_)))
    counties = []
    for k in sorted(keys, key=lambda k: -w[k]):
        row = dict(f=k, n=names[k], w=w[k], v=t[k], L=L[k], b=[margin(b[1][k]) for b in bases])
        for name, s in shifts.items():
            row[name] = expit(L[k] + s)
        if k in typ:
            row.update(typ[k])
            row["tie_adv"], row["tie_eday"] = split(typ[k]["a"], typ[k]["la"], typ[k]["le"], row["tie"])
        tm = timing.get((slug, k))
        if tm:
            row["t_mid"], row["t_six"] = tm.get("mid"), tm.get("six")
        counties.append(row)
    lean_m = margin(sum(w[k] * expit(L[k]) for k in keys))
    model_m = round(model_m, 2) if model_m is not None else None
    return dict(id=cfg["id"], slug=slug, state=NAMES[slug], seat=cfg["seat"],
                unit="House district" if slug == "alaska" else "county",
                d=dict(name=dem["name"], party=dem["party"]), r=dict(name=rep["name"], party=rep["party"]),
                bases=[b[0] for b in bases], types=cfg["types"][0] if cfg.get("types") else None,
                lean_margin=lean_m, model_margin=model_m, turnout_2022=tot, counties=counties)


# ---------- backtest ----------

def main_pair(src, slug):
    """(D/I-side key, R key) of a past race: the top two finishers, one of them Republican."""
    d = json.load(open(os.path.join(NYT, src.format(s=slug)), encoding="utf-8"))
    if "data" in d:
        cs = sorted(d["data"]["races"][0]["candidates"], key=lambda c: -c["votes"])
        top = [(c["candidate_key"], c["party_id"].lower(), c["last_name"]) for c in cs[:2]]
        rep = {"republican"}
    else:
        r = d["races"][0]
        meta = r.get("candidate_metadata") or {}
        cs = sorted(r["top_reporting_unit"]["candidates"], key=lambda c: -((c.get("votes") or {}).get("total") or 0))
        top = [(c["nyt_id"], str((meta.get(c["nyt_id"], {}).get("party") or {}).get("nyt_id", "")).lower(),
                meta.get(c["nyt_id"], {}).get("last_name", c["nyt_id"])) for c in cs[:2]]
        rep = {"gop"}
    reps = [t for t in top if t[1] in rep]
    opps = [t for t in top if t[1] not in rep]
    if len(reps) != 1 or len(opps) != 1:
        return None
    return opps[0], reps[0]


def backtest():
    rows = []
    for slug in BACKTEST_STATES:
        def have(f):
            return os.path.exists(os.path.join(NYT, f.format(s=slug)))
        targets = [f for f in ("2022/{s}-governor.json", "2022/{s}-us-senate.json", "2024/{s}-us-senate.json",
                               "2024/{s}-president.json") if have(f)]
        for tgt in targets:
            if slug == "maine" and tgt.startswith("2024/{s}-us-senate"):
                continue  # King (I), Kouzounas (R) and Costello (D): not a two-way race
            pair = main_pair(tgt, slug)
            if not pair:
                continue
            if tgt.startswith("2022"):
                base_files = ["2020/{s}-president.json"] + (["2020/{s}-senate.json"] if have("2020/{s}-senate.json") else [])
            else:
                same = "2022/{s}-us-senate.json" if have("2022/{s}-us-senate.json") else "2022/{s}-governor.json"
                base_files = ["2020/{s}-president.json", same]
            bases = []
            for f in base_files:
                p = main_pair(f, slug)
                if not p:
                    continue
                us = units(f, slug)
                bases.append({k: two_party(u, p[0][0], p[1][0]) for k, u in us.items()})
            tu = units(tgt, slug)
            act = {k: two_party(u, pair[0][0], pair[1][0]) for k, u in tu.items()}
            tv = {k: votes(u, pair[0][0]) + votes(u, pair[1][0]) for k, u in tu.items()}
            keys = [k for k in tu if act[k] is not None and tv[k] > 0 and all(b.get(k) is not None for b in bases)]
            tot = sum(tv[k] for k in keys)
            w = {k: tv[k] / tot for k in keys}
            L = {k: sum(logit(b[k]) for b in bases) / len(bases) for k in keys}
            true_t = sum(w[k] * act[k] for k in keys)
            s = solve(L, w, true_t)
            err = {k: margin(expit(L[k] + s)) - margin(act[k]) for k in keys}
            rmse = math.sqrt(sum(w[k] * err[k] ** 2 for k in keys))
            off5 = 100 * sum(w[k] for k in keys if abs(err[k]) > 5)
            top = sorted(keys, key=lambda k: -w[k])[:5]
            ext = {}
            for k in top:  # statewide estimate from this one county's final result
                sk = logit(act[k]) - L[k]
                ext[k] = margin(sum(w[j] * expit(L[j] + sk) for j in keys)) - margin(true_t)
            yr = tgt[:4]
            office = "President" if "president" in tgt else ("Senate" if "senate" in tgt else "Governor")
            rows.append(dict(state=NAMES[slug], race=f"{yr} {office} ({pair[0][2]}-{pair[1][2]})",
                             true_margin=round(margin(true_t), 1), counties=len(keys),
                             rmse=round(rmse, 1), vote_off_5=round(off5, 0),
                             largest=tu[top[0]]["name"], largest_share=round(100 * w[top[0]], 1),
                             largest_err=round(ext[top[0]], 1),
                             top5_median_abs_err=round(st.median(abs(e) for e in ext.values()), 1),
                             top5_max_abs_err=round(max(abs(e) for e in ext.values()), 1)))
    return rows


# ---------- outputs ----------

def fmt_m(m, d, r):
    """+3.2 -> 'Talarico +3.2'; -3.2 -> 'Paxton +3.2'."""
    if m is None:
        return "-"
    if abs(m) < 0.05:
        return "tie"
    return f"{g.surname(d) if m > 0 else g.surname(r)} +{abs(m):.1f}"


def race_markdown(race, bt, html=False):
    d, r = race["d"]["name"], race["r"]["name"]
    pd = g.PARTY.get(race["d"]["party"], race["d"]["party"])
    unit = race["unit"]
    cs = race["counties"]
    show, cum = [], 0.0
    for c in cs:
        if len(show) >= 15 or (cum >= 0.75 and len(show) >= 8):
            break
        show.append(c)
        cum += c["w"]
    rest = cs[len(show):]
    typed = any("tie_adv" in c for c in show)
    timed = any(c.get("t_mid") is not None for c in show)
    # the first base's own parties: the 2024 presidential race is D vs R; Nebraska's base is Osborn (I)
    bl = "D" if race["bases"][0].startswith("2024 President") else pd
    head = (f"| {unit.capitalize()} | Share of state vote (2022) | {race['bases'][0]} (two-party margin) | "
            f"**Tie line**: {g.surname(d)} share (margin) | If {g.surname(d)} wins by {SCEN:.0f} | If {g.surname(r)} wins by {SCEN:.0f} |"
            + (f" At a tie: early/mail vs Election Day margin ({race['types']} mix) |" if typed else "")
            + (" 2020: counted by midnight / 6 am ET |" if timed else ""))
    ncol = head.count("|") - 1
    out = [head, "|" + "---|" * ncol]
    for c in show:
        b = c["b"][0]
        cells = [c["n"], f"{100 * c['w']:.1f}%", f"{bl if b > 0 else 'R'} +{abs(b):.1f}",
                 f"**{100 * c['tie']:.1f}%** ({fmt_m(margin(c['tie']), d, r)})",
                 f"{100 * c['d3']:.1f}% ({fmt_m(margin(c['d3']), d, r)})",
                 f"{100 * c['r3']:.1f}% ({fmt_m(margin(c['r3']), d, r)})"]
        if typed:
            cells.append(f"{fmt_m(margin(c['tie_adv']), d, r)} / {fmt_m(margin(c['tie_eday']), d, r)} "
                         f"({100 * c['a']:.0f}% early/mail)" if "tie_adv" in c else "-")
        if timed:
            cells.append(f"{c['t_mid']:.0f}% / {c['t_six']:.0f}%" if c.get("t_mid") is not None and c.get("t_six") is not None else "-")
        out.append("| " + " | ".join(cells) + " |")
    plural = {"county": "counties", "House district": "House districts"}[unit]
    if rest:
        w = sum(c["w"] for c in rest)
        tie = sum(c["w"] * c["tie"] for c in rest) / w
        out.append(f"| All other {len(rest)} {plural if len(rest) != 1 else unit} | {100 * w:.1f}% | | "
                   f"{100 * tie:.1f}% ({fmt_m(margin(tie), d, r)}) | | |" + (" |" if typed else "") + (" |" if timed else ""))
    lines = [f"#### {race['state']} {race['seat']}: {g.surname(d)} ({pd}) vs {g.surname(r)} (R)", ""]
    src = " and ".join(race["bases"]) + (", averaged" if len(race["bases"]) > 1 else "")
    lines.append(f"- **Lean from:** {src}; turnout from the 2022 governor race "
                 f"({race['turnout_2022']:,} votes). Shares and margins are two-party ({g.surname(d)} vs {g.surname(r)}).")
    lines.append(f"- **The tie line** is what {g.surname(d)} needs in each {unit} for a statewide tie. A finished {unit} "
                 f"above it means {g.surname(d)} is running ahead of a tie statewide; below it, {g.surname(r)} is.")
    lines.append(f"- **Only a finished {unit} is a fair test.** A partial count is skewed by vote type: early and mail "
                 "ballots usually come first, Election Day votes later, and late mail or drop-offs last.")
    if race["model_margin"] is not None:
        lines.append(f"- **Model:** {fmt_m(race['model_margin'], d, r)} statewide (the separate margin model). "
                     f"The dashboard page's slider shows every {unit} at any statewide result.")
    if typed:
        lines.append(f"- **Early/mail vs Election Day** columns use the {race['types']} split by vote type, so the early "
                     f"batch can be read before Election Day votes arrive. 2026's mix differs; treat them as rough.")
    if race["slug"] == "alaska":
        lines.append("- **Alaska reports by House district**, not county. The lean is first-choice votes; the "
                     "ranked-choice count can change the winner. Absentee ballots are counted Nov 10-18, so on election "
                     "night every district shows only part of its vote. No backtest: the districts were redrawn for 2022.")
    if bt:
        rm = st.median(b["rmse"] for b in bt)
        errs = ", ".join(f"{abs(b['largest_err']):.1f} ({b['race'].split(' (')[0]})" for b in bt)
        lines.append(f"- **How reliable:** in {len(bt)} past races here (2022-2024), counties landed a typical "
                     f"**{rm:.1f} pts** from their line even when the statewide result was known. A statewide estimate from "
                     f"{bt[0]['largest']} alone was off by {errs} (backtest in section 5).")
    # the dashboard page draws the full, adjustable table in place of the static one
    table = f'<div class="ctool" id="ct-{race["id"]}"></div>' if html else "\n".join(out)
    return "\n".join(lines) + "\n\n" + table


def state_markdown(slug, data=None, html=False):
    """Markdown for one state's races (build_master.py puts it in each state's section)."""
    data = data or json.load(open(os.path.join(OUT, "county_benchmarks.json"), encoding="utf-8"))
    bt = [b for b in data["backtest"] if b["state"] == NAMES[slug]]
    parts = [race_markdown(r, bt, html) for r in data["races"] if r["slug"] == slug]
    return "\n\n".join(parts)


def signed(x):
    return "0.0" if abs(x) < 0.05 else f"{x:+.1f}"


def backtest_markdown(data=None):
    data = data or json.load(open(os.path.join(OUT, "county_benchmarks.json"), encoding="utf-8"))
    out = ["| State | Race | Final two-party margin (D/I minus R) | Typical county miss (weighted RMSE, pts) | Vote in counties missed by 5+ pts | "
           "Largest county (share) | Statewide estimate from it alone: error | Five largest counties: median / worst error |",
           "|---|---|---|---|---|---|---|---|"]
    for b in data["backtest"]:
        out.append(f"| {b['state']} | {b['race']} | {b['true_margin']:+.1f} | {b['rmse']:.1f} | {b['vote_off_5']:.0f}% | "
                   f"{b['largest']} ({b['largest_share']:.0f}%) | {signed(b['largest_err'])} | {b['top5_median_abs_err']:.1f} / {b['top5_max_abs_err']:.1f} |")
    return "\n".join(out)


def rounded(x):
    """Six decimals is far below anything the tables show; keeps the committed JSON small."""
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, dict):
        return {k: rounded(v) for k, v in x.items()}
    if isinstance(x, list):
        return [rounded(v) for v in x]
    return x


def main():
    data = g.forecast()
    timing = timing_2020()
    races = []
    for cfg in RACES:
        print("race", cfg["id"])
        races.append(build_race(cfg, data, timing))
    bt = backtest()
    out = dict(built=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
               model_run=data["predictions_as_of"], scenario_pts=SCEN, races=races, backtest=bt)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "county_benchmarks.json"), "w", encoding="utf-8") as f:
        json.dump(rounded(out), f, separators=(",", ":"))
    cols = ["race", "state", "unit", "fips_or_district", "name", "share_of_state_vote_2022", "votes_2022",
            "lean_margin", "base1_margin", "base2_margin", "tie_d_share", "d_wins_by_3_d_share", "r_wins_by_3_d_share",
            "model_d_share", "early_mail_share_of_2party", "tie_early_margin", "tie_eday_margin",
            "pct_counted_midnight_2020", "pct_counted_6am_2020"]
    with open(os.path.join(OUT, "county_benchmarks.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in races:
            for c in r["counties"]:
                wr.writerow([r["id"], r["state"], r["unit"], c["f"], c["n"], round(100 * c["w"], 3), c["v"],
                             round(margin(expit(c["L"])), 2), round(c["b"][0], 2), round(c["b"][1], 2) if len(c["b"]) > 1 else "",
                             round(100 * c["tie"], 2), round(100 * c["d3"], 2), round(100 * c["r3"], 2),
                             round(100 * c["model"], 2) if "model" in c else "",
                             round(100 * c["a"], 1) if "a" in c else "",
                             round(margin(c["tie_adv"]), 2) if "tie_adv" in c else "",
                             round(margin(c["tie_eday"]), 2) if "tie_eday" in c else "",
                             c.get("t_mid", ""), c.get("t_six", "")])
    with open(os.path.join(OUT, "county_backtest.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(bt[0]))
        wr.writeheader()
        wr.writerows(bt)
    print(f"{len(races)} races, {sum(len(r['counties']) for r in races)} county rows, {len(bt)} backtests -> {OUT}")


if __name__ == "__main__":
    main()
