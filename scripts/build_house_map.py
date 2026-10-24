"""2026 House district shapes for the map page (docs/map.html) -> docs/us_house_2026_geo.js. 2026-10-23.

Every one of the 435 districts on the November 3 2026 ballot, on the maps actually in force:

  * 41 states: the Census Bureau's 119th Congress cartographic boundaries (cb_2024_us_cd119_500k).
    Missouri is one of them: its 2025 map is suspended by the referendum petition and the Supreme
    Court left it suspended in late September, so it votes on the 2022 lines. Virginia votes on its
    2021 map (the state Supreme Court voided the April 2026 referendum on May 8).
  * 9 redrawn states, from the official plan files (SOURCES below): TX, CA, NC, OH, UT, FL, TN, LA
    and AL. Ohio published only a block assignment file, so its districts are dissolved from the
    2020 Census blocks it lists. Alabama votes on its 2023 legislature map, which the Supreme Court
    let stand on June 2 2026.

Each district is clipped to the Census land outline (official plans include lake and coastal water),
simplified, and projected exactly as us-atlas projects the state shapes in docs/us_map_geo.js
(d3.geoAlbersUsa().scale(1300).translate([487.5, 305]), Alaska and Hawaii inset), so the two line up
in the same 975 x 610 frame. Paths are in tenths of a pixel (the page draws them at scale 0.1).

Per district: the SVG path, a label point, whether the 2026 map redrew it, and (when
data/processed/district_demographics_2026.csv exists - scripts/build_district_demographics.py)
its ACS 2020-2024 profile on the 2026 lines and, for redrawn districts, on the old lines.

The raw files live in data/raw/districts_2026/ (gitignored, ~0.5 GB with Ohio's blocks):
    py scripts/build_house_map.py --download     # fetch whatever is missing, then build
    py scripts/build_house_map.py                # build from the files already there
Needs Node (npx runs mapshaper 0.6.102). The shapes don't change before the election, so this runs
once and its output is committed.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw", "districts_2026")
X = os.path.join(RAW, "x")
OUT = os.path.join(ROOT, "docs", "us_house_2026_geo.js")
DEMO = os.path.join(ROOT, "data", "processed", "district_demographics_2026.csv")
MAPSHAPER = "mapshaper@0.6.102"
SIMPLIFY_M = 300          # simplification interval in metres: crisp at a state's zoom, ~1 MB (300 KB gzipped)

FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
        "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS",
        "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
        "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY",
        "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC",
        "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
        "55": "WI", "56": "WY"}
ST_FIPS = {v: k for k, v in FIPS.items()}

# state -> (file under data/raw/districts_2026, district field, source, URL to fetch it from)
SOURCES = {
    "TX": ("x/tx/PLANC2333/PLANC2333.shp", "District",
           "Texas Legislative Council, PLANC2333 (enacted Aug 29 2025)",
           "https://data.capitol.texas.gov/dataset/748c952b-e926-4f44-8d01-a738884b3ec8/resource/"
           "f34a2ca9-e4de-4bb3-a2f2-884076d5a166/download/planc2333_all_files_20260911.zip"),
    "CA": ("x/ca/AB604/AB604.shp", "DISTRICT",
           "California AB 604, the Proposition 50 map (approved Nov 4 2025)",
           "https://sdmg.senate.ca.gov/node/1130"),
    "NC": ("x/nc/SL 2025-95.shp", "DISTRICT", "North Carolina S.L. 2025-95 (Oct 22 2025)",
           "https://www.ncleg.gov/Redistricting/C2025E"),
    "OH": ("x/oh/oh_2025.shp", "CD",
           "Ohio Redistricting Commission plan of Oct 31 2025 (block assignment file + 2020 Census blocks)",
           "https://www.redistricting.ohio.gov/api/public/districtmaps/430/download"),
    "UT": ("ut_2026.geojson", "DISTRICT", "Utah 2026-2032 court-ordered map (Utah Geospatial Resource Center)",
           "https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/"
           "political_us_congress_districts_2026_to_2032/FeatureServer/0/query?where=1%3D1&outFields=*"
           "&outSR=4326&f=geojson"),
    "FL": ("x/fl/EOGPCRP2026.shp", "DISTRICT", "Florida 2026 congressional plan (signed May 4 2026)",
           "https://www.edr.state.fl.us/Content/redistricting/2026redistricting/EOGPCRP2026.zip"),
    "TN": ("x/tn/NewCongressional26.shp", "DISTRICT", "Tennessee map adopted May 7 2026 (Comptroller)",
           "https://comptroller.tn.gov/content/dam/cot/pa/documents/district-maps/congress-districts/"
           "NewCongressional26.zip"),
    "LA": ("x/la/Act_2_(2026_RS).shp", "DISTRICT_I", "Louisiana Act 2 (SB 121) of the 2026 regular session",
           "https://redist.legis.la.gov/2026_Files/Act2Congress/Shapefile/Shapefile%20-%20Act_2_(2026_RS).zip"),
    "AL": ("al_2023_leg.geojson", "DISTRICT",
           "Alabama's 2023 legislature plan, in force again since the Supreme Court's June 2 2026 order (ALGeoHub)",
           "https://services7.arcgis.com/jF2q3LPxL7PETdYk/arcgis/rest/services/2023_CONG_LEGISLATIVE_PLAN/"
           "FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson"),
}
CD119 = ("x/cd119/cb_2024_us_cd119_500k.shp",
         "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_cd119_500k.zip")
OH_BLOCKS = "https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_39_tabblock20.zip"


# ---------------------------------------------------------------- d3.geoAlbersUsa, ported
class ConicEqualArea:
    """d3-geo's geoConicEqualArea with rotate([lambda, 0]), center, scale and translate."""

    def __init__(self, parallels, rotate, center, scale, translate):
        sy0 = math.sin(math.radians(parallels[0]))
        self.n = (sy0 + math.sin(math.radians(parallels[1]))) / 2
        self.c = 1 + sy0 * (2 * self.n - sy0)
        self.r0 = math.sqrt(self.c) / self.n
        self.dl = math.radians(rotate)
        self.k = scale
        cx, cy = self.raw(math.radians(center[0]), math.radians(center[1]))
        self.dx, self.dy = translate[0] - scale * cx, translate[1] + scale * cy

    def raw(self, x, y):
        r = math.sqrt(max(self.c - 2 * self.n * math.sin(y), 0)) / self.n
        x *= self.n
        return r * math.sin(x), self.r0 - r * math.cos(x)

    def __call__(self, lon, lat):
        lam = math.radians(lon) + self.dl
        if abs(lam) > math.pi:
            lam -= round(lam / (2 * math.pi)) * 2 * math.pi
        x, y = self.raw(lam, math.radians(lat))
        return self.dx + self.k * x, self.dy - self.k * y


def albers_usa(scale=1300, translate=(487.5, 305)):
    x, y = translate
    k = scale
    return {
        "lower48": ConicEqualArea((29.5, 45.5), 96, (-0.6, 38.7), k, (x, y)),
        "AK": ConicEqualArea((55, 65), 154, (-2, 58.5), k * 0.35, (x - 0.307 * k, y + 0.201 * k)),
        "HI": ConicEqualArea((8, 18), 157, (-3, 19.9), k, (x - 0.205 * k, y + 0.212 * k)),
    }


# ---------------------------------------------------------------- inputs
def _get(url, dest, cookie=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **({"Cookie": cookie} if cookie else {})})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    print(f"  downloaded {os.path.basename(dest)} ({os.path.getsize(dest) // 1024} KB)")


def _unzip(zpath, dest, members=None):
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        for m in z.namelist():
            if m.startswith("__MACOSX") or (members and os.path.basename(m) not in members):
                continue
            z.extract(m, dest)


def download():
    """Fetch the plan files that are missing. CA and NC publish theirs behind plan pages, so those
    two are named in the error if absent (download the shapefile zip from the page by hand)."""
    os.makedirs(X, exist_ok=True)
    have = lambda rel: os.path.exists(os.path.join(RAW, rel))  # noqa: E731
    if not have(CD119[0]):
        z = os.path.join(RAW, "cb_2024_us_cd119_500k.zip")
        _get(CD119[1], z)
        _unzip(z, os.path.join(X, "cd119"))
    if not have(SOURCES["TX"][0]):
        z = os.path.join(RAW, "planc2333_all.zip")
        if not os.path.exists(z):
            _get(SOURCES["TX"][3], z)
        _unzip(z, os.path.join(X, "tx"), {"PLANC2333.zip"})
        _unzip(os.path.join(X, "tx", "PLANC2333.zip"), os.path.join(X, "tx"))
    for st, zname, sub in (("FL", "fl_EOGPCRP2026.zip", "fl"), ("LA", "la_act2_2026.zip", "la"),
                           ("TN", "tn_2026.zip", "tn")):
        if not have(SOURCES[st][0]):
            z = os.path.join(RAW, zname)
            if not os.path.exists(z):
                # Tennessee's link sits behind a disclaimer page that only sets this cookie
                _get(SOURCES[st][3], z, cookie="disclaimer--2096581727=true" if st == "TN" else None)
            _unzip(z, os.path.join(X, sub))
    for st, name in (("UT", "ut_2026.geojson"), ("AL", "al_2023_leg.geojson")):
        if not have(SOURCES[st][0]):
            _get(SOURCES[st][3], os.path.join(RAW, name))
    if not have(SOURCES["OH"][0]):
        build_ohio()
    missing = [st for st, s in SOURCES.items() if not have(s[0])]
    if missing:
        raise SystemExit("download these plan shapefiles by hand into data/raw/districts_2026/x/: "
                         + ", ".join(f"{st} ({SOURCES[st][3]})" for st in missing))


def build_ohio():
    """Ohio published a block assignment file only: dissolve the 2020 Census blocks it lists."""
    z = os.path.join(RAW, "oh_2025_adopted.zip")
    if not os.path.exists(z):
        _get(SOURCES["OH"][3], z)
    _unzip(z, os.path.join(X, "oh"))
    baf = pd.read_excel(os.path.join(X, "oh", "October 31 2025 CD BAF.xlsx"), dtype=str)
    baf.columns = ["GEOID20", "CD"]
    baf.dropna().to_csv(os.path.join(X, "oh", "oh_baf.csv"), index=False)
    bz = os.path.join(RAW, "oh_blocks", "tl_2020_39_tabblock20.zip")
    if not os.path.exists(bz):
        os.makedirs(os.path.dirname(bz), exist_ok=True)
        _get(OH_BLOCKS, bz)
    _unzip(bz, os.path.join(RAW, "oh_blocks"))
    mapshaper(os.path.join(RAW, "oh_blocks", "tl_2020_39_tabblock20.shp"),
              "-join", os.path.join(X, "oh", "oh_baf.csv"), "keys=GEOID20,GEOID20",
              "field-types=GEOID20:str,CD:number", "-dissolve", "CD",
              "-o", os.path.join(X, "oh", "oh_2025.shp"), big=True)


def mapshaper(*args, big=False):
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("needs Node.js: npx runs " + MAPSHAPER)
    env = dict(os.environ)
    if big:
        env["NODE_OPTIONS"] = "--max-old-space-size=8192"
    res = subprocess.run([npx, "-y", MAPSHAPER, *args], capture_output=True, text=True, env=env)
    if res.returncode:
        raise SystemExit(f"mapshaper failed: {res.stderr[-2000:]}")
    return res.stdout


# ---------------------------------------------------------------- geometry
def normalise():
    """One lon/lat GeoJSON of all 435 districts with ST and CD, water clipped off."""
    norm = os.path.join(X, "norm")
    os.makedirs(norm, exist_ok=True)
    cd119 = os.path.join(RAW, CD119[0])
    land = os.path.join(norm, "us_land.json")
    mapshaper(cd119, "-filter", "+STATEFP <= 56", "-dissolve", "-o", land, "format=geojson")
    redrawn = sorted(ST_FIPS[s] for s in SOURCES)
    base = os.path.join(norm, "base.json")
    mapshaper(cd119, "-filter", f"+STATEFP <= 56 && STATEFP != '11' && {json.dumps(redrawn)}.indexOf(STATEFP) < 0",
              "-each", "FIPS=STATEFP, CD=CD119FP == '00' ? 1 : +CD119FP", "-filter-fields", "FIPS,CD",
              "-o", base, "format=geojson")
    feats = []
    for f in json.load(open(base, encoding="utf-8"))["features"]:
        f["properties"] = {"ST": FIPS[f["properties"]["FIPS"]], "CD": int(f["properties"]["CD"]), "rd": 0}
        feats.append(f)
    for st, (rel, field, _src, _url) in SOURCES.items():
        out = os.path.join(norm, f"{st}.json")
        mapshaper(os.path.join(RAW, rel), "-proj", "wgs84", "-each", f"CD=+{field}", "-filter-fields", "CD",
                  "-clip", land, "-dissolve", "CD", "-o", out, "format=geojson")
        got = json.load(open(out, encoding="utf-8"))["features"]
        for f in got:
            f["properties"] = {"ST": st, "CD": int(f["properties"]["CD"]), "rd": 1}
        feats += got
        print(f"  {st}: {len(got)} districts from {rel}")
    merged = os.path.join(norm, "all.json")
    json.dump({"type": "FeatureCollection", "features": feats}, open(merged, "w", encoding="utf-8"))
    simple = os.path.join(norm, "all_simple.json")
    mapshaper(merged, "-simplify", f"interval={SIMPLIFY_M}", "keep-shapes", "-o", simple,
              "format=geojson", "precision=0.00001", big=True)
    # state outlines dissolved from the same simplified districts, so borders sit on district edges
    outlines = os.path.join(norm, "states_simple.json")
    mapshaper(simple, "-dissolve", "ST", "-o", outlines, "format=geojson", "precision=0.00001", big=True)
    return (json.load(open(simple, encoding="utf-8"))["features"],
            json.load(open(outlines, encoding="utf-8"))["features"])


def _rings(geom):
    if geom is None:
        return []
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return polys


def _area(ring):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1])) / 2


def _quantise(ring, proj):
    out, last = [], None
    for lon, lat in ring:
        x, y = proj(lon, lat)
        p = (round(x * 10), round(y * 10))
        if p != last:
            out.append(p)
            last = p
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def _path(polys):
    """Relative SVG path in tenth-pixel integers: 'M x y l dx dy dx dy ... z' per ring."""
    parts = []
    for rings in polys:
        for pts in rings:
            seq = [f"M{pts[0][0]} {pts[0][1]}l"]
            px, py = pts[0]
            steps = []
            for x, y in pts[1:]:
                steps.append(f"{x - px} {y - py}")
                px, py = x, y
            seq.append(" ".join(steps).replace(" -", "-"))
            parts.append("".join(seq) + "z")
    return "".join(parts)


def _polylabel(rings):
    """Pole of inaccessibility (mapbox/polylabel): the label point deepest inside the polygon.
    Rings are thinned to ~300 points first - plenty for placing a label, and pure Python."""
    import heapq
    rings = [r[::max(1, len(r) // 300)] for r in rings]
    rings = [r for r in rings if len(r) >= 3] or rings
    outer = rings[0]
    xs, ys = [p[0] for p in outer], [p[1] for p in outer]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    w, h = maxx - minx, maxy - miny
    cell = min(w, h)
    if cell == 0:
        return outer[0]
    precision = max(5.0, max(w, h) / 100)

    def dist(x, y):
        inside, best = False, float("inf")
        for ring in rings:
            for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
                if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                    inside = not inside
                dx, dy = bx - ax, by - ay
                t = 0 if dx == dy == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
                best = min(best, (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2)
        return (1 if inside else -1) * math.sqrt(best)

    q, h2 = [], cell / 2
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            d = dist(x + h2, y + h2)
            heapq.heappush(q, (-(d + h2 * math.sqrt(2)), x + h2, y + h2, h2, d))
            y += cell
        x += cell
    a = _area(outer) or 1
    cx = sum((x0 + x1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in zip(outer, outer[1:] + outer[:1])) / (6 * a)
    cy = sum((y0 + y1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in zip(outer, outer[1:] + outer[:1])) / (6 * a)
    best = (dist(cx, cy), cx, cy)
    while q:
        _neg, x, y, hh, d = heapq.heappop(q)
        if d > best[0]:
            best = (d, x, y)
        if -_neg - best[0] <= precision:
            continue
        hh /= 2
        for ddx in (-hh, hh):
            for ddy in (-hh, hh):
                nd = dist(x + ddx, y + ddy)
                heapq.heappush(q, (-(nd + hh * math.sqrt(2)), x + ddx, y + ddy, hh, nd))
    return best[1], best[2]


# d3.geoAlbersUsa's inset clip boxes (x0, y0, x1, y1) in px for scale 1300 / translate (487.5, 305):
# the far Aleutians and the Northwestern Hawaiian Islands fall outside them, as in us-atlas
INSETS = {"AK": (487.5 - 0.425 * 1300, 305 + 0.120 * 1300, 487.5 - 0.214 * 1300, 305 + 0.234 * 1300),
          "HI": (487.5 - 0.214 * 1300, 305 + 0.166 * 1300, 487.5 - 0.115 * 1300, 305 + 0.234 * 1300)}


def _projected(geom, st, P):
    proj = P.get(st, P["lower48"])
    polys = []
    for poly in _rings(geom):
        rings = [_quantise(r, proj) for r in poly]
        rings = [r for r in rings if len(r) >= 3 and abs(_area(r)) >= 4]   # >= 0.04 px^2
        if rings and st in INSETS:
            x0, y0, x1, y1 = (v * 10 for v in INSETS[st])
            cx = sum(p[0] for p in rings[0]) / len(rings[0])
            cy = sum(p[1] for p in rings[0]) / len(rings[0])
            if not (x0 <= cx <= x1 and y0 <= cy <= y1):
                continue
        if rings:
            polys.append(rings)
    return polys


def outlines(features):
    P = albers_usa()
    return {f["properties"]["ST"]: _path(_projected(f["geometry"], f["properties"]["ST"], P)) for f in features}


def project(features):
    P = albers_usa()
    out, boxes = {}, {}
    for f in features:
        st, cd = f["properties"]["ST"], f["properties"]["CD"]
        polys = _projected(f["geometry"], st, P)
        if not polys:
            raise SystemExit(f"{st}-{cd}: nothing left after simplification")
        biggest = max(polys, key=lambda p: abs(_area(p[0])))
        lx, ly = _polylabel(biggest)
        did = f"{st}-{cd:02d}"
        out[did] = dict(d=_path(polys), lx=round(lx / 10, 1), ly=round(ly / 10, 1),
                        rd=f["properties"]["rd"])
        xs = [x for p in polys for x, _ in p[0]]
        ys = [y for p in polys for _, y in p[0]]
        b = boxes.setdefault(st, [math.inf, math.inf, -math.inf, -math.inf])
        b[:] = [min(b[0], min(xs)), min(b[1], min(ys)), max(b[2], max(xs)), max(b[3], max(ys))]
    return out, {st: [round(v / 10, 1) for v in b] for st, b in boxes.items()}


def check_alignment(boxes):
    """The districts' state extents must sit on the us-atlas state shapes (same projection)."""
    import re
    src = open(os.path.join(ROOT, "docs", "us_map_geo.js"), encoding="utf-8").read()
    states = json.loads(src[src.index("{"):src.rindex("}") + 1])["states"]
    worst = []
    for st, b in boxes.items():
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", states[st]["d"])]
        xs, ys = nums[0::2], nums[1::2]
        ref = [min(xs), min(ys), max(xs), max(ys)]
        off = max(abs(a - c) for a, c in zip(b, ref))
        worst.append((off, st))
    worst.sort(reverse=True)
    print("  alignment with us_map_geo.js, largest bbox offsets (px):",
          ", ".join(f"{st} {off:.1f}" for off, st in worst[:6]))
    # Alaska's far Aleutians and small coastal islands differ between the 1:10m and 1:500k outlines
    bad = [(off, st) for off, st in worst if off > (12 if st in ("AK", "HI") else 4)]
    if bad:
        raise SystemExit(f"district shapes do not line up with the state map: {bad}")


def demographics():
    if not os.path.exists(DEMO):
        print("  (no district demographics yet - run scripts/build_district_demographics.py)")
        return {}
    d = pd.read_csv(DEMO)
    cols = ["pop", "wnh", "blk", "hsp", "asn", "ba", "inc"]
    out = {}
    for r in d.itertuples():
        rec = {"now": [None if pd.isna(getattr(r, c)) else (round(getattr(r, c), 3) if c not in ("pop", "inc")
                                                               else int(getattr(r, c))) for c in cols]}
        if getattr(r, "old_pop", None) is not None and not pd.isna(r.old_pop):
            rec["old"] = [None if pd.isna(getattr(r, "old_" + c)) else
                          (round(getattr(r, "old_" + c), 3) if c not in ("pop", "inc") else int(getattr(r, "old_" + c)))
                          for c in cols]
        out[r.id] = rec
    return out


def main():
    if "--download" in sys.argv:
        download()
    feats, state_feats = normalise()
    districts, boxes = project(feats)
    assert len(districts) == 435, len(districts)
    check_alignment(boxes)
    states = outlines(state_feats)
    assert len(states) == 50, len(states)
    demo = demographics()
    for did, rec in demo.items():
        if did in districts:
            districts[did]["demo"] = rec
    data = dict(viewBox=[0, 0, 975, 610], unit=0.1, districts=districts, states=states, boxes=boxes,
                demo_fields=["pop", "wnh", "blk", "hsp", "asn", "ba", "inc"],
                demo_source="ACS 2020-2024 5-year (Census Reporter); redrawn districts by block group",
                sources={st: s[2] for st, s in SOURCES.items()},
                base_source="U.S. Census Bureau, cb_2024_us_cd119_500k (119th Congress)")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("const US_HOUSE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB, {len(districts)} districts, "
          f"{sum(v['rd'] for v in districts.values())} redrawn, {len(demo)} with demographics)")


if __name__ == "__main__":
    main()
