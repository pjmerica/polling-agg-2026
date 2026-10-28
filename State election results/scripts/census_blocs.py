"""Demographic voting blocs from the Census Bureau's latest county estimates, and how each bloc
voted in 2020, 2022 and 2024.

Every county (Alaska: House district) goes to the first bloc it fits, using the American Community
Survey 2020-2024 5-year estimates (the latest that cover every county; via Census Reporter's API,
because api.census.gov now needs a key):

  1. Hispanic-majority            Hispanic 50%+
  2. Black 35%+, large counties   Black 35%+ and 150,000+ people (Fulton, DeKalb, Wayne)
  3. Black 35%+, smaller counties Black 35%+ under 150,000 (Georgia's Black Belt)
  4. Native 25%+                  American Indian / Alaska Native 25%+ (rural Alaska)
  5. College-educated             40%+ of adults 25+ hold a bachelor's degree
  6. Big diverse metros           400,000+ people and under 60% non-Hispanic white
  7. White, non-college           70%+ non-Hispanic white and under 30% with a degree
  8. Everything else

For each state and bloc: its share of the vote and two-party margin in every Governor, Senate and
President race NYT covered in 2020-2024 (Alaska: 2022/2024 House and 2024 President), the
2020->2024 presidential shift against the state's, and what each 2026 candidate needs there for a
statewide tie (the county benchmarks summed by bloc).

Writes data/processed/census_units.csv (every county with its demographics and bloc),
bloc_results.csv and census_blocs.json (read by build_master.py and build_election_night.py).

    py "State election results/scripts/census_blocs.py"
"""
import csv
import datetime as dt
import json
import os
import urllib.request

import county_benchmarks as cb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw", "census")
OUT = os.path.join(ROOT, "data", "processed")
RELEASE = "acs2024_5yr"
API = "https://api.censusreporter.org/1.0/data/show/{rel}?table_ids=B03002,B15003,B19013&geo_ids={geo}"
FIPS = {"georgia": ("GA", "13"), "ohio": ("OH", "39"), "michigan": ("MI", "26"), "texas": ("TX", "48"),
        "kansas": ("KS", "20"), "maine": ("ME", "23"), "iowa": ("IA", "19"), "nebraska": ("NE", "31"),
        "nevada": ("NV", "32"), "oregon": ("OR", "41"), "alaska": ("AK", "02"),
        "south-carolina": ("SC", "45")}
BLOCS = ["Hispanic-majority", "Black 35%+, large counties", "Black 35%+, smaller counties", "Native 25%+",
         "College-educated", "Big diverse metros", "White, non-college", "Everything else"]
RULES = {
    "Hispanic-majority": "Hispanic 50%+",
    "Black 35%+, large counties": "Black 35%+, 150,000+ people",
    "Black 35%+, smaller counties": "Black 35%+, under 150,000 people",
    "Native 25%+": "American Indian / Alaska Native 25%+",
    "College-educated": "40%+ of adults hold a bachelor's degree",
    "Big diverse metros": "400,000+ people, under 60% white",
    "White, non-college": "70%+ white, under 30% with a degree",
    "Everything else": "none of the above",
}
ELECTIONS = [("2020 President", "2020/{s}-president.json"), ("2020 Senate", "2020/{s}-senate.json"),
             ("2022 Governor", "2022/{s}-governor.json"), ("2022 Senate", "2022/{s}-us-senate.json"),
             ("2024 President", "2024/{s}-president.json"), ("2024 Senate", "2024/{s}-us-senate.json")]
# Alaska: the districts were redrawn for 2022, so 2020 can't be lined up. 2022 Governor had an
# independent ex-governor (Walker) splitting the anti-Dunleavy vote, so the House race is the D-vs-R read.
AK_ELECTIONS = [("2022 House", "ak:2022:U.S. Representative", ["Peltola"], ["Palin", "Begich"], "Peltola", "Palin+Begich"),
                ("2024 President", "ak:2024:U.S. President / Vice President", ["Harris"], ["Trump"], "Harris", "Trump"),
                ("2024 House", "ak:2024:U.S. Representative", ["Peltola"], ["Begich"], "Peltola", "Begich")]
SKIP = {("maine", "2024 Senate")}  # King (I) vs Kouzounas (R) with a Democrat also running: not a two-way race


def fetch(ab, fp):
    level, kind = ("620", "sldl") if ab == "AK" else ("050", "county")
    path = os.path.join(RAW, f"{RELEASE}_{ab}_{kind}.json")
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        # an honest agent string: Census Reporter answers a bare "Mozilla/5.0" with 403 (2026-10-23)
        req = urllib.request.Request(API.format(rel=RELEASE, geo=f"{level}|04000US{fp}"),
                                     headers={"User-Agent": "polling-agg-2026 (census blocs)"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        json.loads(data)  # fail here, not later, on an error page
        with open(path, "wb") as f:
            f.write(data)
    return path


def demographics(slug):
    """Unit id as county_benchmarks uses it (county FIPS; Alaska: district number) -> demographics."""
    ab, fp = FIPS[slug]
    d = json.load(open(fetch(ab, fp), encoding="utf-8"))
    assert d["release"]["id"] == RELEASE, d["release"]
    out = {}
    for gid, t in d["data"].items():
        if gid.startswith("04000"):
            continue
        e3, e15 = t["B03002"]["estimate"], t["B15003"]["estimate"]
        pop = e3["B03002001"] or 0
        if not pop:
            continue
        uid = str(int(gid[-3:])) if ab == "AK" else gid[-5:]
        name = (f"District {uid} ({cb.AK_HD[int(uid)]})" if ab == "AK"
                else d["geography"][gid]["name"].split(",")[0].replace(" County", ""))
        out[uid] = dict(name=name, pop=int(pop),
                        hisp=(e3["B03002012"] or 0) / pop, wnh=(e3["B03002003"] or 0) / pop,
                        black=(e3["B03002004"] or 0) / pop, aian=(e3["B03002005"] or 0) / pop,
                        asian=(e3["B03002006"] or 0) / pop,
                        ba=sum(e15[f"B15003{n:03d}"] or 0 for n in (22, 23, 24, 25)) / max(1, e15["B15003001"] or 0),
                        income=t["B19013"]["estimate"]["B19013001"])
    return out


def bloc(x):
    if x["hisp"] >= 0.5:
        return "Hispanic-majority"
    if x["black"] >= 0.35:
        return "Black 35%+, large counties" if x["pop"] >= 150_000 else "Black 35%+, smaller counties"
    if x["aian"] >= 0.25:
        return "Native 25%+"
    if x["ba"] >= 0.40:
        return "College-educated"
    if x["pop"] >= 400_000 and x["wnh"] < 0.60:
        return "Big diverse metros"
    if x["wnh"] >= 0.70 and x["ba"] < 0.30:
        return "White, non-college"
    return "Everything else"


def elections(slug):
    """(label, units, D/I-side keys, R keys, D/I name, R name, D/I party letter) per past race."""
    out = []
    if slug == "alaska":
        for label, src, dk, rk, dn, rn in AK_ELECTIONS:
            out.append((label, cb.units(src, slug), dk, rk, dn, rn, "D"))
        return out
    for label, src in ELECTIONS:
        if (slug, label) in SKIP or not os.path.exists(os.path.join(cb.NYT, src.format(s=slug))):
            continue
        pair = cb.main_pair(src, slug)
        if not pair:
            continue
        (dk, dp, dn), (rk, _, rn) = pair
        letter = "D" if dp in ("democrat", "dem") else "I"
        out.append((label, cb.units(src, slug), [dk], [rk], dn, rn, letter))
    return out


def side(u, keys):
    return sum(cb.votes(u, k) for k in keys)


def margin(d, r):
    return 100 * (d - r) / (d + r) if d + r else None


def build():
    bench = json.load(open(os.path.join(OUT, "county_benchmarks.json"), encoding="utf-8"))
    units_rows, result_rows, states = [], [], []
    for slug in FIPS:
        demo = demographics(slug)
        blocs = {k: bloc(x) for k, x in demo.items()}
        races26 = [r for r in bench["races"] if r["slug"] == slug]
        # demographics of each bloc, weighted by population
        comp = {}
        for b in BLOCS:
            ks = [k for k in demo if blocs[k] == b]
            if not ks:
                continue
            pop = sum(demo[k]["pop"] for k in ks)
            comp[b] = dict(units=len(ks), pop=pop,
                           **{f: sum(demo[k][f] * demo[k]["pop"] for k in ks) / pop for f in ("hisp", "black", "wnh", "aian", "asian", "ba")},
                           members=[demo[k]["name"] for k in sorted(ks, key=lambda k: -demo[k]["pop"])])
        # how each bloc voted
        res = []
        for label, us, dk, rk, dn, rn, letter in elections(slug):
            tot = {"D": 0, "R": 0, "all": 0}
            per = {b: {"D": 0, "R": 0, "all": 0} for b in comp}
            unmatched = 0
            for k, u in us.items():
                d, r, a = side(u, dk), side(u, rk), sum(u["votes"].values())
                tot["D"] += d; tot["R"] += r; tot["all"] += a
                b = blocs.get(k)
                if b is None:
                    unmatched += a
                    continue
                per[b]["D"] += d; per[b]["R"] += r; per[b]["all"] += a
            if unmatched > 0.01 * tot["all"]:
                raise SystemExit(f"{slug} {label}: {unmatched} votes in units with no census match")
            res.append(dict(label=label, d=dn, r=rn, letter=letter, state=margin(tot["D"], tot["R"]),
                            blocs={b: dict(margin=margin(v["D"], v["R"]), share=100 * v["all"] / tot["all"] if tot["all"] else None)
                                   for b, v in per.items()}))
            for b, v in per.items():
                result_rows.append(dict(state=cb.NAMES[slug], bloc=b, election=label, d_candidate=dn, r_candidate=rn,
                                        d_votes=v["D"], r_votes=v["R"], all_votes=v["all"],
                                        two_party_margin=round(margin(v["D"], v["R"]), 2) if v["D"] + v["R"] else "",
                                        share_of_state_vote=round(100 * v["all"] / tot["all"], 2) if tot["all"] else ""))
        # 2026: the county benchmarks summed by bloc
        need = []
        for r in races26:
            per = {}
            for c in r["counties"]:
                b = blocs.get(c["f"])
                if b is None:
                    continue
                x = per.setdefault(b, {"w": 0.0, "tie": 0.0, "model": 0.0})
                x["w"] += c["w"]
                x["tie"] += c["w"] * c["tie"]
                x["model"] += c["w"] * c.get("model", c["tie"])
            need.append(dict(id=r["id"], seat=r["seat"], d=r["d"]["name"], r=r["r"]["name"], party=r["d"]["party"],
                             model_margin=r["model_margin"],
                             # the race the benchmark leans on besides 2024 President ("2024 Senate (Allred-Cruz)" -> "2024 Senate")
                             comparable=" ".join(r["bases"][-1].split()[:2]),
                             blocs={b: dict(share=100 * x["w"], tie=100 * (2 * x["tie"] / x["w"] - 1),
                                            model=100 * (2 * x["model"] / x["w"] - 1)) for b, x in per.items()}))
        for k, x in demo.items():
            units_rows.append(dict(state=cb.NAMES[slug], unit=k, name=x["name"], bloc=blocs[k], population=x["pop"],
                                   hispanic=round(100 * x["hisp"], 1), black=round(100 * x["black"], 1),
                                   white_non_hispanic=round(100 * x["wnh"], 1), native=round(100 * x["aian"], 1),
                                   asian=round(100 * x["asian"], 1), bachelors_plus=round(100 * x["ba"], 1),
                                   median_household_income=x["income"]))
        states.append(dict(slug=slug, state=cb.NAMES[slug], unit="House district" if slug == "alaska" else "county",
                           blocs=comp, results=res, races=need, unit_blocs=blocs))
    return dict(built=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), release=RELEASE,
                states=states), units_rows, result_rows


# ---------- markdown ----------

def fm(m, letter="D"):
    if m is None:
        return "-"
    if abs(m) < 0.05:
        return "even"
    return f"{letter if m > 0 else 'R'}+{abs(m):.1f}"


def shift(a, b):
    """Change from margin a to margin b, named by direction."""
    if a is None or b is None:
        return "-"
    s = b - a
    if abs(s) < 0.05:
        return "none"
    return f"{abs(s):.1f} toward {'D' if s > 0 else 'R'}"


def state_markdown(slug, data=None):
    data = data or json.load(open(os.path.join(OUT, "census_blocs.json"), encoding="utf-8"))
    s = next(x for x in data["states"] if x["slug"] == slug)
    unit, units = s["unit"], ("House districts" if s["unit"] == "House district" else "counties")
    order = [b for b in BLOCS if b in s["blocs"]]
    res = {r["label"]: r for r in s["results"]}
    lines = [f"{units.capitalize()} grouped by their demographics in the Census Bureau's latest estimates (American Community "
             "Survey 2020-2024); the rules are at the start of section 4. Margins are two-party; vote shares are of all votes cast.", ""]
    # who is in each bloc
    lines += [f"| Bloc | {units.capitalize()} (largest first) | Hispanic | Black | White | Bachelor's+ | Share of the vote: 2020 / 2022 / 2024 |",
              "|---|---|---|---|---|---|---|"]
    yrs = [next((r for r in s["results"] if r["label"].startswith(y)), None) for y in ("2020", "2022", "2024")]
    for b in order:
        c = s["blocs"][b]
        shares = " / ".join(f"{y['blocs'][b]['share']:.1f}%" if y and b in y["blocs"] and y["blocs"][b]["share"] is not None else "-" for y in yrs)
        mem = c["members"]
        names = ", ".join(mem[:6]) + (f" and {len(mem) - 6} more" if len(mem) > 6 else "")
        lines.append(f"| {b} | {names} | {100 * c['hisp']:.0f}% | {100 * c['black']:.0f}% | {100 * c['wnh']:.0f}% | "
                     f"{100 * c['ba']:.0f}% | {shares} |")
    # how each bloc voted
    labs = [r["label"] for r in s["results"]]
    pres = ("2020 President", "2024 President") if {"2020 President", "2024 President"} <= set(labs) else None
    lines += ["", "**How each bloc voted** (two-party margin; " +
              "; ".join(f"{r['label']}: {r['d']} vs {r['r']}" for r in s["results"]) + ")", ""]
    head = "| Bloc | " + " | ".join(labs) + (" | President, 2020 to 2024 | Relative to the state |" if pres else " |")
    lines += [head, "|" + "---|" * (head.count("|") - 1)]
    rows = [("**Statewide**", None)] + [(b, b) for b in order]
    for name, b in rows:
        cells = []
        for r in s["results"]:
            m = r["state"] if b is None else (r["blocs"].get(b) or {}).get("margin")
            cells.append(fm(m, r["letter"]))
        if pres:
            a, z = res[pres[0]], res[pres[1]]
            ma = a["state"] if b is None else a["blocs"].get(b, {}).get("margin")
            mz = z["state"] if b is None else z["blocs"].get(b, {}).get("margin")
            cells.append(shift(ma, mz))
            if b is None:
                cells.append("")
            else:
                rel = None if ma is None or mz is None else (mz - ma) - (z["state"] - a["state"])
                cells.append("-" if rel is None else ("same" if abs(rel) < 0.05 else f"{abs(rel):.1f} more toward {'D' if rel > 0 else 'R'}"))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    # what 2026 needs
    for r in s["races"]:
        dl = {"DEM": "D", "IND": "I"}.get(r["party"], "D")
        D = cb.g.surname(r["d"])
        comp = res.get(r["comparable"])
        pres = res.get("2024 President") if r["comparable"] != "2024 President" else None
        lines += ["", f"**{r['seat']} 2026: what {D} needs in each bloc for a statewide tie** "
                  f"(the county benchmarks summed by bloc; the model has {fm(r['model_margin'], dl)} statewide)", ""]
        head = (f"| Bloc | Share of the expected vote | {D} at a statewide tie |"
                + (f" {comp['label']} ({comp['d']} vs {comp['r']}) | Change from it |" if comp else "")
                + (" 2024 President |" if pres else ""))
        lines += [head, "|" + "---|" * (head.count("|") - 1)]
        for b in order:
            x = r["blocs"].get(b)
            if not x:
                continue
            cells = [b, f"{x['share']:.1f}%", f"**{fm(x['tie'], dl)}**"]
            if comp:
                mc = comp["blocs"].get(b, {}).get("margin")
                cells += [fm(mc, comp["letter"]), shift(mc, x["tie"])]
            if pres:
                cells.append(fm(pres["blocs"].get(b, {}).get("margin")))
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def summary_markdown(data=None):
    """Cross-state: the 2020 -> 2024 presidential shift by bloc, relative to each state's shift."""
    data = data or json.load(open(os.path.join(OUT, "census_blocs.json"), encoding="utf-8"))
    sts = [s for s in data["states"] if {"2020 President", "2024 President"} <= {r["label"] for r in s["results"]}]
    head = "| Bloc | " + " | ".join(s["state"] for s in sts) + " |"
    out = [head, "|" + "---|" * (head.count("|") - 1)]
    row = ["**Whole state** (actual shift)"]
    for s in sts:
        res = {r["label"]: r for r in s["results"]}
        d = res["2024 President"]["state"] - res["2020 President"]["state"]
        row.append(f"{abs(d):.1f} {'D' if d > 0 else 'R'}")
    out.append("| " + " | ".join(row) + " |")
    for b in BLOCS:
        row = [b]
        for s in sts:
            res = {r["label"]: r for r in s["results"]}
            a, z = res["2020 President"], res["2024 President"]
            ma, mz = a["blocs"].get(b, {}).get("margin"), z["blocs"].get(b, {}).get("margin")
            if ma is None or mz is None:
                row.append("")
                continue
            rel = (mz - ma) - (z["state"] - a["state"])
            row.append("0.0" if abs(rel) < 0.05 else f"{rel:+.1f}")
        if any(c for c in row[1:]):
            out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def main():
    data, units_rows, result_rows = build()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "census_blocs.json"), "w", encoding="utf-8") as f:
        json.dump(cb.rounded(data), f, separators=(",", ":"))
    for name, rows in (("census_units.csv", units_rows), ("bloc_results.csv", result_rows)):
        with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    n = sum(len(s["unit_blocs"]) for s in data["states"])
    print(f"{len(data['states'])} states, {n} counties/districts, {len(result_rows)} bloc results -> {OUT}")


if __name__ == "__main__":
    main()
