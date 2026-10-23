"""US state shapes for the map page (docs/map.html) -> docs/us_map_geo.js. 2026-10-23.

Decodes us-atlas's state TopoJSON, already projected to Albers USA in a 975 x 610 frame with Alaska
and Hawaii inset (Census Bureau cartographic boundaries, ISC licence), into one SVG path per state plus
a label point. Adds the tile-grid layout the House tab draws (one tile per state, its districts as
equal squares inside it) and label boxes for the small Northeastern states.

The shapes don't change, so this runs once and its output is committed; the page reads
forecast_data.js and data.js when it loads.

    py scripts/build_map_geo.py
"""
import json
import os
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
URL = "https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/states-albers-10m.json"
OUT = os.path.join(ROOT, "docs", "us_map_geo.js")

FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
        "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
        "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
        "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
        "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}

# House tab: (column, row) of each state's tile. The common "statebins" tile grid, compacted to 7 rows:
# Alaska and Hawaii bottom-left as on a real map, Vermont, New Hampshire and Maine sharing the top row.
TILES = {"VT": (9, 0), "NH": (10, 0), "ME": (11, 0),
         "WA": (0, 1), "ID": (1, 1), "MT": (2, 1), "ND": (3, 1), "MN": (4, 1), "IL": (5, 1), "WI": (6, 1), "MI": (7, 1),
         "NY": (8, 1), "RI": (9, 1), "MA": (10, 1),
         "OR": (0, 2), "NV": (1, 2), "WY": (2, 2), "SD": (3, 2), "IA": (4, 2), "IN": (5, 2), "OH": (6, 2), "PA": (7, 2),
         "NJ": (8, 2), "CT": (9, 2),
         "CA": (0, 3), "UT": (1, 3), "CO": (2, 3), "NE": (3, 3), "MO": (4, 3), "KY": (5, 3), "WV": (6, 3), "VA": (7, 3),
         "MD": (8, 3), "DE": (9, 3),
         "AZ": (1, 4), "NM": (2, 4), "KS": (3, 4), "AR": (4, 4), "TN": (5, 4), "NC": (6, 4), "SC": (7, 4),
         "AK": (0, 5), "OK": (3, 5), "LA": (4, 5), "MS": (5, 5), "AL": (6, 5), "GA": (7, 5),
         "HI": (0, 6), "TX": (3, 6), "FL": (8, 6)}
# Small states labelled in boxes east of the map, north to south (box centre); the rest are labelled on the state
CALLOUTS = {"VT": (950, 140), "NH": (950, 166), "MA": (950, 192), "RI": (950, 218), "CT": (950, 244),
            "NJ": (950, 270), "DE": (950, 296), "MD": (950, 322)}


def arcs_of(topo):
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    out = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            pts.append((x * sx + tx, y * sy + ty))
        out.append(pts)
    return out


def ring(arcs, idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def area_centroid(pts):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-9:
        return abs(a) / 2, pts[0]
    return abs(a) / 2, (cx / (3 * a), cy / (3 * a))


def path(polys):
    parts = []
    for rings in polys:
        for pts in rings:
            seq, last = [], None
            for x, y in pts:
                p = (round(x, 1), round(y, 1))
                if p != last:
                    seq.append(p)
                    last = p
            if len(seq) >= 3:
                parts.append("M" + "L".join(f"{x:g},{y:g}" for x, y in seq) + "Z")
    return "".join(parts)


# label points where the largest polygon's centroid sits badly (checked against the rendered map)
LABEL_FIX = {"FL": (812, 488), "MI": (676, 180), "LA": (575, 456), "HI": (300, 560), "AK": (130, 520)}


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    topo = json.loads(urllib.request.urlopen(req, timeout=60).read())
    arcs = arcs_of(topo)
    states = {}
    for g in topo["objects"]["states"]["geometries"]:
        ab = FIPS[g["id"]]
        polys = [[ring(arcs, r) for r in p] for p in (g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]])]
        best = max((area_centroid(p[0]) for p in polys), key=lambda t: t[0])[1]
        lx, ly = LABEL_FIX.get(ab, best)
        states[ab] = dict(name=g["properties"]["name"], d=path(polys), lx=round(lx, 1), ly=round(ly, 1))
    assert len(states) == 51, len(states)
    data = dict(source=URL, viewBox=[0, 0, 975, 610], states=states, callouts=CALLOUTS, tiles=TILES)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("const US_MAP = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB, {len(states)} states)")


if __name__ == "__main__":
    main()
