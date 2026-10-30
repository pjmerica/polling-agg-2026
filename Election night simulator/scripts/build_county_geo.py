"""County shapes for the dashboard's map tab -> Election night simulator/county_geo.js. 2026-10-30.

us-atlas's county TopoJSON (Census Bureau cartographic boundaries), already projected to Albers USA in the same
975 x 610 frame as docs/us_map_geo.js, decoded with scripts/build_map_geo.py's helpers into one SVG path per
county for the states with a tracked race (live_project.RACES), plus every state's outline for context and each
tracked state's bounding box (for zooming). Alaska is left out: its results come by House district, not county.

The shapes don't change, so this runs once and its output is committed (publish_live.py copies it to docs/).

    py "Election night simulator/scripts/build_county_geo.py"
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REPO = os.path.join(ROOT, "..")
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, HERE)
from build_map_geo import FIPS, arcs_of, path, ring  # noqa: E402
import live_project as lp  # noqa: E402

URL = "https://cdn.jsdelivr.net/npm/us-atlas@3.0.1/counties-albers-10m.json"
OUT = os.path.join(ROOT, "county_geo.js")


def polys_of(g, arcs):
    return [[ring(arcs, r) for r in p] for p in (g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]])]


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "polling-agg-2026 county map build"})
    topo = json.loads(urllib.request.urlopen(req, timeout=60).read())
    arcs = arcs_of(topo)
    want = {r.split("-")[0] for r in lp.RACES} - {"AK"}
    abbr = {v: k for k, v in FIPS.items()}
    states, counties = {}, {}
    for g in topo["objects"]["states"]["geometries"]:
        st = FIPS.get(g["id"])
        if st:
            states[st] = dict(name=g["properties"]["name"], d=path(polys_of(g, arcs)))
    for g in topo["objects"]["counties"]["geometries"]:
        st = FIPS.get(str(g["id"])[:2])
        if st not in want:
            continue
        polys = polys_of(g, arcs)
        counties.setdefault(st, {})[str(g["id"])] = path(polys)
        xs = [x for p in polys for rg in p for x, _ in rg]
        ys = [y for p in polys for rg in p for _, y in rg]
        b = states[st].setdefault("bbox", [1e9, 1e9, -1e9, -1e9])
        b[:] = [min(b[0], min(xs)), min(b[1], min(ys)), max(b[2], max(xs)), max(b[3], max(ys))]
    for st in want:
        states[st]["bbox"] = [round(v, 1) for v in states[st]["bbox"]]
        states[st]["counties"] = counties[st]
    data = dict(source=URL, viewBox=[0, 0, 975, 610], states=states)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.COUNTY_GEO = " + json.dumps(data, separators=(",", ":")) + ";\n")
    n = sum(len(c) for c in counties.values())
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB, {n} counties in {len(want)} states)")
    missing = {st: abbr.get(st) for st in want if st not in counties}
    if missing:
        print("no counties for", missing)


if __name__ == "__main__":
    main()
