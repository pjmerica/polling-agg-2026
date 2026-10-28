"""County reporting order on election night, 2018-2024, and what repeats from year to year.

Inputs (all election-night captures of NYT's results files, with every county's votes so far):
    2018  data/raw/wayback_counties/2018/   9 national captures (fetch_wayback_counties.py)
    2020  data/raw/wayback_2020/            140 captures, one per ~10 minutes (fetch_wayback_2020.py)
    2022  data/raw/wayback_counties/2022/   12-30 captures per state
    2024  data/raw/wayback_counties/2024/   1-9 captures per state
Each capture is compared with the county's final count: NYT's final file (data/raw/nyt/{year}) for
2020-2024; for 2018, which has no final file, the county's largest count in the captures (Nov 9).

Measures, per county and year:
    lateness   county share counted minus the state's share counted, averaged over the captures
               taken while the state was 10-95% counted. Negative = the county runs behind the
               state. It works with sparse captures, because each capture compares the county with
               its own state at the same moment.
    t50, t90   first capture (ET) with half / 90% of the county's final vote (2020: ~10-minute grid;
               other years only when a capture falls in the window, else blank).
Per state and year: the lean of the vote still uncounted, when the state was about 50% and 80% counted
(county lean = the 2026 county benchmarks' D-minus-R lean, county_benchmarks.json, so the same yardstick
is used for every year). Across years: rank correlation of lateness between years, and the counties late
(or early) in every year with captures.

Writes data/processed/county_reporting.csv (county x year), county_reporting.json (for build_master).
    py "State election results/scripts/county_reporting.py"
"""
import re
import datetime as dt
import glob
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
STATES = ["georgia", "ohio", "michigan", "texas", "kansas", "maine", "iowa", "nebraska", "nevada",
          "oregon", "alaska", "south-carolina"]
NAME = {s: s.title() for s in STATES}
YEARS = [2018, 2020, 2022, 2024]
ELECTION_DAY = {2018: dt.date(2018, 11, 6), 2020: dt.date(2020, 11, 3), 2022: dt.date(2022, 11, 8),
                2024: dt.date(2024, 11, 5)}
# main poll close, hours after midnight ET (EST in all four years). Iowa closed at 9 p.m. CT
# (10 p.m. ET) until SF 413 (2021); 8 p.m. CT from 2022.
CLOSE_ET = {"georgia": 19.0, "ohio": 19.5, "michigan": 20.0, "texas": 20.0, "kansas": 20.0,
            "maine": 20.0, "iowa": 21.0, "nebraska": 21.0, "nevada": 22.0, "oregon": 23.0, "south-carolina": 19.0,
            "alaska": 24.0}
WINDOW = (0.10, 0.95)          # state share counted, for the lateness average
FINAL_RACE = {2020: ["president"], 2022: ["us-senate", "governor"], 2024: ["president", "us-senate"]}



def split_name(name):
    """'south-carolina-us-senate' -> ('south-carolina', 'us-senate'): a state slug can hold a hyphen
    (2026-10-27, South Carolina), so split at the race name, not the first hyphen."""
    m = re.match(r"(.+?)-(president|us-senate|senate|governor|us-house.*)$", name)
    return (m.group(1), m.group(2)) if m else tuple(name.split("-", 1))

def close_et(state, year):
    return 22.0 if state == "iowa" and year <= 2020 else CLOSE_ET[state]


def ts_to_et(ts):
    """Wayback timestamp (UTC) -> naive ET datetime (EST, UTC-5)."""
    return dt.datetime.strptime(ts[:14], "%Y%m%d%H%M%S") - dt.timedelta(hours=5)


def hours_after_close(t_et, state, year):
    base = dt.datetime.combine(ELECTION_DAY[year], dt.time()) + dt.timedelta(hours=close_et(state, year))
    return (t_et - base).total_seconds() / 3600


def unit_key(fips, name, state):
    f = str(fips or "")
    if state != "alaska" and len(f) >= 5 and f[2:5] not in ("", "000"):
        return f[:5]
    return f"name:{str(name).strip().lower()}"


# ---- captures -> tidy (year, state, capture, key, name, votes) ------------------------------------
def load_2020():
    rows = []
    for p in sorted(glob.glob(os.path.join(RAW, "wayback_2020", "*.json"))):
        d = json.load(open(p, encoding="utf8"))
        ts = os.path.basename(p)[:14]
        for st, s in (d.get("states") or {}).items():
            for c in s.get("counties") or []:
                rows.append((2020, st, ts, "president", unit_key(c.get("fips"), c.get("name"), st),
                             c.get("name"), c.get("votes")))
    return rows


def load_wayback(year):
    rows = []
    for p in sorted(glob.glob(os.path.join(RAW, "wayback_counties", str(year), "*", "*.json"))):
        d = json.load(open(p, encoding="utf8"))
        st = os.path.basename(os.path.dirname(p))
        race = str(d.get("race") or "")
        for u in d.get("units") or []:
            rows.append((year, st, d["capture"], race, unit_key(u.get("fips"), u.get("name"), st),
                         u.get("name"), u.get("votes")))
    return rows


def race_family(year, race):
    r = race.lower()
    if year == 2018:
        return "senate" if "senate" in r else "governor"
    if "-g-p-" in r or "president" in r:
        return "president"
    if "-g-s-" in r or "senate" in r:
        return "us-senate"
    return "governor"


def finals(year):
    """{(state, family): {key: final votes}} from NYT's final files."""
    out = {}
    for p in glob.glob(os.path.join(RAW, "nyt", str(year), "*.json")):
        st, fam = split_name(os.path.basename(p)[:-5])
        fam = {"senate": "us-senate"}.get(fam, fam) if year == 2020 else fam
        d = json.load(open(p, encoding="utf8"))
        agg = {}
        if "data" in d:                       # 2020 layout: data.races[0].counties
            for c in d["data"]["races"][0].get("counties") or []:
                k = unit_key(c.get("fips"), c.get("name"), st)
                agg[k] = agg.get(k, 0) + (c.get("votes") or 0)
        else:                                 # 2022/2024 layout: races[0].reporting_units
            for u in d["races"][0].get("reporting_units") or []:
                if u.get("level") == "state":
                    continue
                k = unit_key((u.get("fips_state") or "") + (u.get("fips_county") or ""), u.get("name"), st)
                agg[k] = agg.get(k, 0) + (u.get("total_votes") or 0)
        out[(st, fam)] = agg
    return out


def tidy():
    rows = load_2020()
    for y in (2018, 2022, 2024):
        rows += load_wayback(y)
    df = pd.DataFrame(rows, columns=["year", "state", "capture", "race", "key", "name", "votes"])
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)
    df["family"] = [race_family(y, r) for y, r in zip(df["year"], df["race"])]
    # sub-county units (Maine towns, some Alaska districts) -> one row per county key
    df = (df.groupby(["year", "state", "capture", "family", "key"], as_index=False)
            .agg(name=("name", "first"), votes=("votes", "sum")))
    fin = {y: finals(y) for y in (2020, 2022, 2024)}

    def final_for(g):
        y, st, fam = g.name
        f = fin.get(y, {}).get((st, fam)) if y in fin else None
        mx = g.groupby("key")["votes"].transform("max")
        if f:
            fv = g["key"].map(f)
            # a unit NYT's final file names differently falls back to its largest captured count
            return fv.where(fv.notna() & (fv > 0), mx)
        return mx
    df["final"] = df.groupby(["year", "state", "family"], group_keys=False).apply(final_for)
    df = df[df["final"] > 0].copy()
    df["frac"] = (df["votes"] / df["final"]).clip(upper=1.0)
    df["t_et"] = df["capture"].map(ts_to_et)
    df["h"] = [hours_after_close(t, s, y) for t, s, y in zip(df["t_et"], df["state"], df["year"])]
    # state share counted at each capture, from the same file's counties
    tot = df.groupby(["year", "state", "capture", "family"]).agg(sv=("votes", "sum"), sf=("final", "sum"))
    df = df.join((tot["sv"] / tot["sf"]).rename("state_frac"), on=["year", "state", "capture", "family"])
    # one family per (year, state, capture): the one with the most units (state files carry the top race)
    return df


def lean_map():
    d = json.load(open(os.path.join(PROC, "county_benchmarks.json"), encoding="utf8"))
    out = {}
    for r in d["races"]:
        st = r["slug"]
        for c in r["counties"]:
            k = unit_key(c["f"], c["n"], st)
            # lean in D-minus-R points from the benchmark's D two-party share at a tied state (tie)
            out.setdefault(st, {})[k] = dict(share=c["w"] * 100, lean=(2 * c["tie"] - 1) * 100,
                                             name=c["n"])
    return out


def county_year(df):
    rows = []
    for (y, st, key), g in df.groupby(["year", "state", "key"]):
        g = g.sort_values("t_et")
        w = g[(g["state_frac"] >= WINDOW[0]) & (g["state_frac"] <= WINDOW[1])]
        # one capture cannot rank counties (in an all-or-nothing state every county reads 0% or 100%),
        # so a year needs at least two captures inside the window
        late = float((w["frac"] - w["state_frac"]).mean() * 100) if w["capture"].nunique() >= 2 else np.nan

        def first(th):
            hit = g[g["frac"] >= th]
            if not len(hit):
                return None
            i = g.index.get_loc(hit.index[0])
            # only exact when the capture before it is close (within 45 minutes)
            if i > 0 and (hit["t_et"].iloc[0] - g["t_et"].iloc[i - 1]) > dt.timedelta(minutes=45):
                return None
            return hit["t_et"].iloc[0]
        rows.append(dict(year=y, state=st, key=key, name=g["name"].iloc[0], final=g["final"].max(),
                         n_window=len(w), lateness=late, t50=first(0.5), t90=first(0.9)))
    cy = pd.DataFrame(rows)
    cy["share"] = cy["final"] / cy.groupby(["year", "state"])["final"].transform("sum") * 100
    return cy


def outstanding_lean(df, leans):
    """Lean of the uncounted vote vs the counted vote when the state was ~50% and ~80% counted."""
    out = []
    for (y, st), g in df.groupby(["year", "state"]):
        L = leans.get(st, {})
        caps = g.groupby("capture")["state_frac"].first().sort_values()
        for target in (0.5, 0.8):
            if not len(caps):
                continue
            cap = (caps - target).abs().idxmin()
            sf = caps[cap]
            if abs(sf - target) > 0.12:
                continue
            c = g[g["capture"] == cap]
            lean = c["key"].map(lambda k: L.get(k, {}).get("lean"))
            ok = lean.notna()
            if ok.sum() < 0.5 * len(c):
                continue
            counted = c["votes"].where(ok); left = (c["final"] - c["votes"]).clip(lower=0).where(ok)
            lc = float((lean[ok] * counted[ok]).sum() / counted[ok].sum()) if counted[ok].sum() else np.nan
            lo = float((lean[ok] * left[ok]).sum() / left[ok].sum()) if left[ok].sum() else np.nan
            out.append(dict(year=y, state=st, target=target, state_frac=round(sf * 100, 1),
                            at=ts_to_et(cap), counted_lean=lc, outstanding_lean=lo,
                            gap=lo - lc if pd.notna(lo) and pd.notna(lc) else np.nan))
    return pd.DataFrame(out)


def next_morning(df, min_share=0.5, below=0.9):
    """Counties still counting the next morning: below 90% of their final vote at the first capture
    between 6 a.m. and 2 p.m. ET the day after the election (one capture per year and state)."""
    out = []
    for (y, st), g in df.groupby(["year", "state"]):
        lo = dt.datetime.combine(ELECTION_DAY[y] + dt.timedelta(days=1), dt.time(6))
        hi = lo + dt.timedelta(hours=8)
        caps = sorted(c for c, t in g.groupby("capture")["t_et"].first().items() if lo <= t <= hi)
        if not caps:
            continue
        c = g[g["capture"] == caps[0]].dropna(subset=["frac"]).reset_index(drop=True)
        c["share"] = c["final"] / c["final"].sum() * 100
        slow = c[(c["frac"] < below) & (c["share"] >= min_share)]
        out.append(dict(year=y, state=st, at=str(c["t_et"].iloc[0]), state_frac=float(c["state_frac"].iloc[0]),
                        counties=[dict(key=r.key, name=r.name, frac=round(float(r.frac) * 100),
                                       share=round(float(r.share), 1))
                                  for r in slow.sort_values("share", ascending=False).itertuples()]))
    return out


def summarize(cy, leans):
    res = {}
    for st in STATES:
        c = cy[cy["state"] == st]
        if c.empty:
            continue
        L = leans.get(st, {})
        piv = c.pivot_table(index="key", columns="year", values="lateness")
        yrs = [y for y in YEARS if y in piv.columns and piv[y].notna().sum() >= 3]
        share = c.groupby("key")["share"].mean()
        big = share[share >= 0.3].index
        corr = {}
        for i, a in enumerate(yrs):
            for b in yrs[i + 1:]:
                x = piv.loc[piv.index.isin(big), [a, b]].dropna()
                if len(x) >= 5:
                    corr[f"{a}-{b}"] = round(float(x[a].rank().corr(x[b].rank())), 2)
        n_yrs = piv[yrs].notna().sum(axis=1)
        always_late = [k for k in piv.index if n_yrs[k] >= 2 and (piv.loc[k, yrs].dropna() < -5).all()]
        always_early = [k for k in piv.index if n_yrs[k] >= 2 and (piv.loc[k, yrs].dropna() > 5).all()]
        lean_corr = {}
        for y in yrs:
            x = c[(c["year"] == y) & c["key"].isin(big)].assign(lean=lambda t: t["key"].map(
                lambda k: L.get(k, {}).get("lean"))).dropna(subset=["lateness", "lean"])
            if len(x) >= 5:
                lean_corr[y] = round(float(x["lateness"].rank().corr(x["lean"].rank())), 2)
        res[st] = dict(years=yrs, rank_corr=corr, always_late=always_late, always_early=always_early,
                       lean_corr=lean_corr)
    return res


# ---- the guide's text (build_master.py) ---------------------------------------------------------
# Reporting rules that shape the county order, from reports/Vote count timing in close 2026 races.md
# and reports/Vote count timing Nevada and Oregon.md (sources cited there).
RULES = {
    "georgia": "Since SB 189 (2024) every county must report all advance and absentee votes by 8 p.m. or within an "
               "hour of its last poll closing; 2018-2022 had no such deadline. Metro Election Day precincts come last.",
    "ohio": "Boards may pre-process and pre-scan absentees but not tabulate or release anything before polls close at "
            "7:30 p.m. (ORC 3509.06). Every county's first dump is mail plus early in-person votes.",
    "michigan": "No result may be released before 8 p.m. (MCL 168.765a). Jurisdictions of 5,000+ may now tabulate "
                "absentees up to 8 days early, wider than in 2018-2022. AP: Wayne, Oakland, Macomb, Kent, Genesee and "
                "Washtenaw release relatively few results in their first updates.",
    "texas": "Counties of 100,000+ may count early ballots from the end of early voting but release nothing before 7 p.m. "
             "local; early-vote totals post first and Election Day totals are due within 24 hours. El Paso and Hudspeth "
             "close at 9 p.m. ET.",
    "kansas": "Advance ballots report first. Four Mountain-time counties close at 9 p.m. ET. Sedgwick adds drop-box and "
              "polling-place mail in a Wednesday update; mail postmarked by Nov 3 counts through Nov 6 (injunction).",
    "maine": "About 500 towns, not counties, report, with two business days to file; the county rows here add up the "
             "towns. A Senate race under 50% goes to a central ranked-choice count 8-10 days later.",
    "iowa": "Each county's absentee board releases one absentee total, only when its count is complete (target 10 p.m. "
            "CT). Polls closed at 10 p.m. ET in 2018 and 2020 and 9 p.m. ET from 2022.",
    "nebraska": "All polls close at 9 p.m. ET. More than three-quarters of counties report all or nearly all early votes "
                "first; Douglas and Lancaster report few Election Day votes at first, and Douglas has 15,000-18,000 "
                "ballots left after election night.",
    "nevada": "Nothing is released until the last voter in line statewide has voted. Election Day drop-off mail is not "
              "counted that night (Clark: about 54,000-57,000 ballots, posted from Wednesday); Washoe then posts at "
              "3 p.m. and 8 p.m. ET daily.",
    "oregon": "All-mail. The first drop, about 11 p.m. ET, holds about two-thirds of the vote; Election Day drop-offs "
              "(about 25% of ballots, 31-32% in Multnomah and Washington) are counted Wednesday to Friday.",
    "south-carolina": "Polls close at 7 p.m. ET statewide. Absentee ballots may be tabulated from 7 a.m. on Election "
                      "Day but nothing is released before 7 p.m.; mail must arrive by 7 p.m. In 2020 Richland, "
                      "Greenville, Lexington, York and Beaufort were still counting mail after midnight.",
    "alaska": "Election night counts only Election Day votes and early votes cast through Oct 29; absentees are counted on "
              "Nov 10, 13 and 18. Alaska reports by House district, not county.",
}


def _load():
    return json.load(open(os.path.join(PROC, "county_reporting.json"), encoding="utf-8"))


def _pts(v, signed=True):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return f"{v:+.0f}" if signed else f"{v:.0f}"


def _lean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    return "even" if abs(v) < 0.5 else (f"D+{v:.0f}" if v > 0 else f"R+{-v:.0f}")


def _clock(s, year):
    if not isinstance(s, str) or s in ("", "None", "NaT", "nan"):
        return ""
    t = dt.datetime.fromisoformat(s)
    day = "" if t.date() == ELECTION_DAY[year] else (" Wed" if (t.date() - ELECTION_DAY[year]).days == 1
                                                     else f" {t.strftime('%a')}")
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}{day}"


def _strength(r):
    return "strong" if r >= 0.6 else "moderate" if r >= 0.3 else "weak"


def state_markdown(slug):
    d = _load()
    s = d["summary"].get(slug)
    rows = [r for r in d["counties"] if r["state"] == slug]
    if not s or not rows:
        return "_No county-level election-night captures for this state._"
    cy = pd.DataFrame(rows)
    leans = lean_map().get(slug, {})
    cap = d["captures"].get(slug, {})
    yrs = [y for y in YEARS if str(y) in cap]
    unit = "district" if slug == "alaska" else "county"
    out = [f"**Rules that set the order.** {RULES[slug]}", "",
           "**How far each " + unit + " ran ahead of (+) or behind (-) the statewide count**, in points of its own "
           "vote counted, averaged over the captures taken while the state was 10-95% counted. Captures per year: "
           + ", ".join(f"{y} {cap[str(y)]}" for y in yrs) + ". "
           "2020 has a capture every ~10 minutes; the other years only a handful, so a single number there can rest on "
           "two or three captures. 2018 has no final file, so its shares are of the Nov 9 count, which slightly "
           "overstates how complete late counties were. Lean = the county's D-minus-R lean at a tied statewide result "
           "(the benchmarks above).", ""]
    share = cy.groupby("key")["share"].mean()
    keep = share[share >= 1.0].sort_values(ascending=False).index[:16]
    piv = cy.pivot_table(index="key", columns="year", values="lateness")
    order = piv.loc[piv.index.isin(keep)].mean(axis=1).sort_values(ascending=False).index
    t20 = cy[cy["year"] == 2020].set_index("key")
    head = ["County" if unit == "county" else "District", "Share of vote", "Lean"] + [str(y) for y in yrs] + \
           (["2020: half in", "2020: 90% in"] if 2020 in yrs else [])
    out += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for k in order:
        name = cy.loc[cy["key"] == k, "name"].iloc[0]
        cells = [str(name), f"{share[k]:.1f}%", _lean(leans.get(k, {}).get("lean"))]
        cells += [_pts(piv.loc[k, y]) if y in piv.columns else "" for y in yrs]
        if 2020 in yrs:
            cells += [_clock(t20["t50"].get(k), 2020) if k in t20.index else "",
                      _clock(t20["t90"].get(k), 2020) if k in t20.index else ""]
        out.append("| " + " | ".join(cells) + " |")
    rest = cy[~cy["key"].isin(keep)]
    if len(rest):
        rw = rest.groupby("year").apply(lambda g: np.average(g["lateness"].dropna(), weights=g.loc[g["lateness"].notna(), "final"])
                                        if g["lateness"].notna().any() else np.nan, include_groups=False)
        n_rest = rest["key"].nunique()
        cells = [f"The other {n_rest}", f"{100 - share[keep].sum():.1f}%", ""] + [_pts(rw.get(y)) for y in yrs]
        cells += ["", ""] if 2020 in yrs else []
        out.append("| " + " | ".join(cells) + " |")
    # what repeats
    big = set(keep)
    late = [cy.loc[cy["key"] == k, "name"].iloc[0] for k in s["always_late"] if k in big]
    early = [cy.loc[cy["key"] == k, "name"].iloc[0] for k in s["always_early"] if k in big]
    notes = []
    if s["rank_corr"]:
        notes.append("**Same order each year?** Rank correlation of the counties' lateness between years: "
                     + ", ".join(f"{k} {v:+.2f} ({_strength(v)})" for k, v in s["rank_corr"].items()) + ".")
    if late:
        notes.append(f"**Behind the state in every year with captures:** {', '.join(late)}.")
    if early:
        notes.append(f"**Ahead of the state every year:** {', '.join(early)}.")
    if s["lean_corr"]:
        notes.append("**Do Democratic-leaning counties report later?** Rank correlation of lateness with lean (negative ="
                     " the more Democratic the county, the later it reports): "
                     + ", ".join(f"{y} {v:+.2f}" for y, v in s["lean_corr"].items()) + ".")
    ol = [r for r in d["outstanding"] if r["state"] == slug]
    if ol:
        notes.append("**Which way the uncounted vote leaned** (county leans weighted by the votes still out vs those "
                     "already counted):")
        notes.append("")
        notes.append("| Year | State counted | Time (ET) | Counted vote | Vote still out | Gap |")
        notes.append("|---|---|---|---|---|---|")
        for r in sorted(ol, key=lambda r: (r["year"], r["target"])):
            notes.append(f"| {r['year']} | {r['state_frac']:.0f}% | {_clock(r['at'], r['year'])} | "
                         f"{_lean(r['counted_lean'])} | {_lean(r['outstanding_lean'])} | "
                         f"{'D' if r['gap'] > 0 else 'R'} {abs(r['gap']):.0f} pts |")
    mo = sorted((r for r in d.get("morning", []) if r["state"] == slug), key=lambda r: r["year"])
    if mo:
        notes += ["", f"**Still counting the next morning** ({'counties' if unit == 'county' else 'districts'} with "
                      "0.5%+ of the vote below 90% of their final "
                      "count at the first capture after 6 a.m. ET):", ""]
        for r in mo:
            names = ", ".join(f"{c['name']} {c['frac']}%" for c in r["counties"][:8]) or "none"
            more = f" and {len(r['counties']) - 8} more" if len(r["counties"]) > 8 else ""
            notes.append(f"- **{r['year']}** ({_clock(r['at'], r['year'])}, state {r['state_frac'] * 100:.0f}% "
                         f"counted): {names}{more}.")
        rep = _repeat_stragglers(mo)
        if rep:
            notes.append(f"- **In two or more years:** {', '.join(rep)}.")
    return "\n".join(out + [""] + notes)


def _repeat_stragglers(mo):
    seen = {}
    for r in mo:
        for c in r["counties"]:
            seen.setdefault(c["key"], [c["name"], 0])[1] += 1
    return [n for n, k in sorted(seen.values(), key=lambda v: -v[1]) if k >= 2]


def summary_markdown():
    d = _load()
    rows = ["| State | Years with captures | Same county order each year? | Late vote leaned (state ~80% counted) | "
            "Big counties behind every year | Still counting next morning, 2+ years |", "|---|---|---|---|---|---|"]
    for st in STATES:
        s = d["summary"].get(st)
        if not s:
            continue
        cy = [r for r in d["counties"] if r["state"] == st]
        names = {r["key"]: r["name"] for r in cy}
        share = pd.DataFrame(cy).groupby("key")["share"].mean()
        late = [names[k] for k in s["always_late"] if share.get(k, 0) >= 1.0]
        rc = s["rank_corr"]
        if not rc:
            same = "one year only"
        elif len(rc) == 1:
            v = next(iter(rc.values())); same = f"{_strength(v)} ({v:+.2f})"
        else:
            same = (f"{_strength(min(rc.values()))} to {_strength(max(rc.values()))} "
                    f"({min(rc.values()):+.2f} to {max(rc.values()):+.2f})")
        ol = [r for r in d["outstanding"] if r["state"] == st and r["target"] == 0.8]
        lean = ", ".join(f"{r['year']} {'D' if r['gap'] > 0 else 'R'}{abs(r['gap']):.0f}" for r in ol) or ""
        caps = d["captures"].get(st, {})
        mo = [r for r in d.get("morning", []) if r["state"] == st]
        rep = _repeat_stragglers(mo)
        rows.append(f"| {NAME[st]} | {', '.join(f'{y} ({n})' for y, n in caps.items())} | {same} | {lean} | "
                    f"{', '.join(late[:5]) or 'none'} | {', '.join(rep[:5]) or 'none'} |")
    return "\n".join(rows)


def main():
    df = tidy()
    # keep, per (year, state, capture), the race family with the most units
    n = df.groupby(["year", "state", "capture", "family"])["key"].transform("size")
    best = n == df.assign(n=n).groupby(["year", "state", "capture"])["n"].transform("max")
    df = df[best].reset_index(drop=True)
    # one name per county key: 2022/2024 Maine (and some Alaska) files report towns, so the aggregated row
    # would carry a town's name; prefer the county-level years' names
    pref = df.assign(_p=df["year"].map({2020: 0, 2018: 1}).fillna(2)).sort_values("_p")
    df["name"] = df["key"].map(pref.groupby("key")["name"].first())
    leans = lean_map()
    cy = county_year(df)
    ol = outstanding_lean(df, leans)
    summ = summarize(cy, leans)
    cov = (df.groupby(["year", "state"])["capture"].nunique().unstack(0).reindex(STATES))
    cy.to_csv(os.path.join(PROC, "county_reporting.csv"), index=False)
    out = dict(built=dt.date.today().isoformat(),
               captures={st: {str(y): int(v) for y, v in r.dropna().items()} for st, r in cov.iterrows()},
               counties=json.loads(cy.assign(t50=cy["t50"].astype(str), t90=cy["t90"].astype(str))
                                   .to_json(orient="records")),
               outstanding=json.loads(ol.assign(at=ol["at"].astype(str)).to_json(orient="records")) if len(ol) else [],
               morning=next_morning(df),
               summary=summ)
    json.dump(out, open(os.path.join(PROC, "county_reporting.json"), "w"), indent=0, default=str)
    print("captures per state and year:\n", cov.fillna(0).astype(int).to_string())
    for st, s in summ.items():
        print(f"{st:9} years {s['years']} rank corr {s['rank_corr']} lean~lateness {s['lean_corr']} "
              f"| always late {len(s['always_late'])} early {len(s['always_early'])}")
    if len(ol):
        print(ol.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
