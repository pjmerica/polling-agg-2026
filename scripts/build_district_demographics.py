"""ACS profile of every 2026 House district -> data/processed/district_demographics_2026.csv. 2026-10-23.

Columns: pop, wnh / blk / hsp / asn (shares: White, Black and Asian non-Hispanic; Hispanic of any race),
ba (share of adults 25+ with a bachelor's degree or more), inc (median household income, $), all from
the ACS 2020-2024 5-year estimates - the same tables and definitions as State election
results/scripts/census_blocs.py. api.census.gov now needs a key, so this reads Census Reporter's API.

  * Unchanged districts: the Census Bureau's own estimates for the 119th Congress districts.
  * The 173 districts in the nine redrawn states (scripts/build_house_map.py) have no official
    estimates yet, so they are built from block groups: each 2020 block group goes to the 2026
    district that holds its population centre (Census CenPop2020) and the counts are summed. Median
    income is interpolated from the summed income brackets (B19001), the Census Bureau's method.
    For these districts the old_* columns hold the official figures for the same-numbered district
    on the 2024 lines, so the page can show what the redraw changed.

Check: the same block-group method run on the OLD lines of the nine states, against the official
figures for those districts -> data/processed/district_demographics_check.csv, summary printed.

    py scripts/build_district_demographics.py      (after build_house_map.py has normalised the plans)
"""
import json
import os
import sys
import time
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_house_map import FIPS, RAW, ROOT, SOURCES, ST_FIPS, X, mapshaper  # noqa: E402

RELEASE = "acs2024_5yr"
API = "https://api.censusreporter.org/1.0/data/show/" + RELEASE + "?table_ids={t}&geo_ids={g}"
CACHE = os.path.join(RAW, "acs")
CENPOP = ("https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/CenPop2020_Mean_BG.txt",
          os.path.join(RAW, "CenPop2020_Mean_BG.txt"))
OUT = os.path.join(ROOT, "data", "processed", "district_demographics_2026.csv")
CHECK = os.path.join(ROOT, "data", "processed", "district_demographics_check.csv")
# B19001 brackets: (lower bound, width) for _002 .. _017
BRACKETS = [(0, 10000), (10000, 5000), (15000, 5000), (20000, 5000), (25000, 5000), (30000, 5000),
            (35000, 5000), (40000, 5000), (45000, 5000), (50000, 10000), (60000, 15000), (75000, 25000),
            (100000, 25000), (125000, 25000), (150000, 50000), (200000, None)]


def fetch(tables, geo, tag):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{tag}_{tables.replace(',', '_')}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    for k in range(4):
        try:
            # an honest agent string: Census Reporter answers a bare "Mozilla/5.0" with 403 (2026-10-23)
            req = urllib.request.Request(API.format(t=tables, g=geo),
                                         headers={"User-Agent": "polling-agg-2026 (district demographics)"})
            d = json.loads(urllib.request.urlopen(req, timeout=300).read())
            if "error" in d:
                raise RuntimeError(d["error"])
            json.dump(d, open(path, "w", encoding="utf-8"))
            return d
        except Exception as e:  # noqa: BLE001 - network: retry, then give up loudly
            print(f"  retry {tag} {tables}: {e}")
            time.sleep(5 * (k + 1))
    raise SystemExit(f"Census Reporter: could not fetch {tables} for {geo}")


def counts(d):
    """{geoid: {column: estimate}} over every table in a Census Reporter response."""
    out = {}
    for gid, tabs in d["data"].items():
        row = out.setdefault(gid, {})
        for t in tabs.values():
            row.update({k: (v or 0) for k, v in t["estimate"].items()})
    return out


def profile(c):
    """Shares and median income from summed counts."""
    pop = c.get("B03002001", 0)
    adults = c.get("B15003001", 0)
    rec = dict(pop=pop,
               wnh=c.get("B03002003", 0) / pop if pop else None,
               blk=c.get("B03002004", 0) / pop if pop else None,
               hsp=c.get("B03002012", 0) / pop if pop else None,
               asn=c.get("B03002006", 0) / pop if pop else None,
               ba=sum(c.get(f"B15003{n:03d}", 0) for n in (22, 23, 24, 25)) / adults if adults else None)
    if "B19013001" in c:
        rec["inc"] = c["B19013001"] or None
    else:
        rec["inc"] = median_income([c.get(f"B19001{n:03d}", 0) for n in range(2, 18)])
    return rec


def median_income(bins):
    """Linear interpolation inside the bracket holding the middle household (Census method;
    the open top bracket reports its floor)."""
    total = sum(bins)
    if not total:
        return None
    half, cum = total / 2, 0
    for n, (lo, width) in zip(bins, BRACKETS):
        if cum + n >= half:
            if width is None or n == 0:
                return lo
            return round(lo + (half - cum) / n * width)
        cum += n
    return None


def cd119_official():
    d = fetch("B03002,B15003,B19013", "500|01000US", "cd119")
    out = {}
    for gid, c in counts(d).items():
        if not gid.startswith("50000US"):
            continue
        fp, cc = gid[7:9], gid[9:11]
        if fp not in FIPS or not cc.isdigit():
            continue                      # DC, territories, 'ZZ' water pseudo-districts
        out[f"{FIPS[fp]}-{max(int(cc), 1):02d}"] = c
    return out


def block_groups(st, pts):
    """Every block group's counts. Census Reporter caps a request at 10,000 geographies, so big
    states (Texas, California, Florida, Ohio, North Carolina) go in batches of whole counties."""
    fp = ST_FIPS[st]
    per_county = pts[pts["STATEFP"] == fp].groupby("COUNTYFP").size()
    batches, cur, n = [], [], 0
    for county, k in per_county.items():
        if cur and n + k > 8000:
            batches.append(cur)
            cur, n = [], 0
        cur.append(county)
        n += k
    batches.append(cur)
    c = {}
    for i, b in enumerate(batches):
        geo = ",".join(f"150|05000US{fp}{cty}" for cty in b) if len(batches) > 1 else f"150|04000US{fp}"
        for t in ("B03002", "B15003", "B19001"):
            for gid, row in counts(fetch(t, geo, f"bg{fp}_{i}")).items():
                if gid.startswith("15000US"):
                    c.setdefault(gid[7:], {}).update(row)
    return c


def bg_points():
    if not os.path.exists(CENPOP[1]):
        req = urllib.request.Request(CENPOP[0], headers={"User-Agent": "Mozilla/5.0"})
        open(CENPOP[1], "wb").write(urllib.request.urlopen(req, timeout=300).read())
    p = pd.read_csv(CENPOP[1], dtype=str, encoding="utf-8-sig")     # the file starts with a BOM
    p["GEOID"] = p["STATEFP"] + p["COUNTYFP"] + p["TRACTCE"] + p["BLKGRPCE"]
    for c in ("LATITUDE", "LONGITUDE"):                                  # "+32.464466"
        p[c] = p[c].astype(float)
    return p


def assign(points, polygons, tag):
    """GEOID -> district number, by point in polygon (mapshaper). A centre that falls just off a
    clipped shoreline takes the district of the nearest assigned block group."""
    pcsv = os.path.join(CACHE, f"pts_{tag}.csv")
    points[["GEOID", "LATITUDE", "LONGITUDE"]].to_csv(pcsv, index=False)
    out = os.path.join(CACHE, f"pts_{tag}_joined.csv")
    mapshaper("-i", pcsv, "string-fields=GEOID", "-points", "x=LONGITUDE", "y=LATITUDE",
              "-join", polygons, "fields=CD", "-o", out)
    j = pd.read_csv(out, dtype={"GEOID": str})
    miss = j[j["CD"].isna()]
    if len(miss):
        have = j.dropna(subset=["CD"])
        for i, r in miss.iterrows():
            dd = (have["LATITUDE"] - r["LATITUDE"]) ** 2 + (have["LONGITUDE"] - r["LONGITUDE"]) ** 2
            j.at[i, "CD"] = have.loc[dd.idxmin(), "CD"]
    return dict(zip(j["GEOID"], j["CD"].astype(int))), len(miss)


def aggregate(bg, cd_of):
    sums = {}
    for gid, row in bg.items():
        cd = cd_of.get(gid)
        if cd is None:
            continue
        s = sums.setdefault(cd, {})
        for k, v in row.items():
            s[k] = s.get(k, 0) + v
    return sums


def main():
    official = cd119_official()
    assert len(official) == 435, len(official)
    pts = bg_points()
    rows, check = [], []
    for did, c in official.items():
        st = did[:2]
        if st not in SOURCES:
            rows.append(dict(id=did, redrawn=0, method="official", **profile(c)))
    norm = os.path.join(X, "norm")
    for st in SOURCES:
        fp = ST_FIPS[st]
        bg = block_groups(st, pts)
        p = pts[pts["STATEFP"] == fp]
        # 2026 lines: the normalised plan (unclipped shapes would also do; the shoreline fallback
        # covers the few centres the Census land clip leaves outside)
        new_of, miss_new = assign(p, os.path.join(norm, f"{st}.json"), f"{st}_new")
        old_shp = os.path.join(norm, f"{st}_old.json")
        mapshaper(os.path.join(RAW, "x", "cd119", "cb_2024_us_cd119_500k.shp"), "-filter", f"STATEFP == '{fp}'",
                  "-each", "CD=CD119FP == '00' ? 1 : +CD119FP", "-filter-fields", "CD", "-o", old_shp,
                  "format=geojson")
        old_of, miss_old = assign(p, old_shp, f"{st}_old")
        n_bg = len(bg)
        unplaced = sum(1 for g in bg if g not in new_of)
        print(f"  {st}: {n_bg} block groups, {unplaced} without a centre point; "
              f"{miss_new} / {miss_old} centres placed by nearest neighbour (new / old lines)")
        for cd, s in sorted(aggregate(bg, new_of).items()):
            did = f"{st}-{cd:02d}"
            old = profile(official[did]) if did in official else {}
            rows.append(dict(id=did, redrawn=1, method="block groups", **profile(s),
                             **{"old_" + k: v for k, v in old.items()}))
        for cd, s in sorted(aggregate(bg, old_of).items()):
            did = f"{st}-{cd:02d}"
            est, off = profile(s), profile(official[did])
            check.append(dict(id=did, **{f"{k}_bg": est[k] for k in est}, **{f"{k}_official": off[k] for k in off}))
    out = pd.DataFrame(rows).sort_values("id")
    assert len(out) == 435 and out["id"].is_unique, len(out)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    ch = pd.DataFrame(check)
    ch.to_csv(CHECK, index=False)
    print(f"wrote {OUT}: {len(out)} districts ({int(out['redrawn'].sum())} from block groups)")
    print("block-group method vs the official figures, on the OLD lines of the nine redrawn states "
          f"({len(ch)} districts):")
    for k in ("wnh", "blk", "hsp", "asn", "ba"):
        e = (ch[f"{k}_bg"] - ch[f"{k}_official"]).abs() * 100
        print(f"  {k}: median miss {e.median():.2f} pts, worst {e.max():.2f} ({ch.loc[e.idxmax(), 'id']})")
    e = (ch["pop_bg"] / ch["pop_official"] - 1).abs() * 100
    print(f"  pop: median miss {e.median():.2f}%, worst {e.max():.2f}% ({ch.loc[e.idxmax(), 'id']})")
    e = (ch["inc_bg"] / ch["inc_official"] - 1).abs() * 100
    print(f"  inc: median miss {e.median():.2f}%, worst {e.max():.2f}% ({ch.loc[e.idxmax(), 'id']})")


if __name__ == "__main__":
    main()
