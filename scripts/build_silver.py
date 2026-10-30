"""Silver Bulletin's race-level win chances for the map page's comparison views (2026-10-30).

Nate Silver's 2026 FLIPR forecast publishes race-by-race numbers only to paid subscribers, so
nothing here scrapes it: the numbers are copied by hand into data/silver_bulletin_2026.csv and
this script turns them into docs/silver_data.js (`const SILVER = {...}`), which docs/map.html
reads. Re-run it after every edit to the CSV; tests/test_silver.py fails if the two differ.

CSV columns: race_id (utils/races.py, e.g. 2026-SEN-PA, 2026-GOV-AZ, 2026-H-NY-17), dem, rep,
ind (optional, e.g. NE-Sen's Osborn), as_of (YYYY-MM-DD, the forecast's update date). Chances
may be fractions (0.62) or percents (62). A row with only one side filled gets the rest on the
other major party. Each row is normalized to sum to 1.

    py scripts/build_silver.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.races import RACE_BY_ID  # noqa: E402

CSV = ROOT / "data" / "silver_bulletin_2026.csv"
OUT = ROOT / "docs" / "silver_data.js"
SIDES = (("dem", "D"), ("rep", "R"), ("ind", "I"))


def _num(s):
    s = (s or "").strip().rstrip("%")
    return float(s) if s else None


def build(path=CSV):
    races, dates = {}, set()
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f), start=2):
                rid = (row.get("race_id") or "").strip()
                if not rid or rid.startswith("#"):
                    continue
                if rid not in RACE_BY_ID:
                    raise ValueError(f"{path.name} line {i}: unknown race_id {rid!r}")
                if rid in races:
                    raise ValueError(f"{path.name} line {i}: {rid} listed twice")
                vals = {k: _num(row.get(col)) for col, k in SIDES}
                given = {k: v for k, v in vals.items() if v is not None}
                if not given:
                    raise ValueError(f"{path.name} line {i}: {rid} has no chances")
                pct = any(v > 1 for v in given.values())
                given = {k: v / 100 if pct else v for k, v in given.items()}
                if any(not 0 <= v <= 1 for v in given.values()):
                    raise ValueError(f"{path.name} line {i}: {rid} chances must be 0-1 or 0-100")
                if len(given) == 1:
                    (k, v), = given.items()
                    given["R" if k != "R" else "D"] = 1 - v
                s = sum(given.values())
                if not s:
                    raise ValueError(f"{path.name} line {i}: {rid} chances sum to 0")
                races[rid] = {k: round(v / s, 4) for k, v in sorted(given.items())}
                if (row.get("as_of") or "").strip():
                    dates.add(row["as_of"].strip())
    return {"as_of": max(dates) if dates else "", "races": dict(sorted(races.items()))}


def render(data):
    return "const SILVER = " + json.dumps(data, separators=(",", ":")) + ";\n"


if __name__ == "__main__":
    data = build()
    OUT.write_text(render(data), encoding="utf-8")
    print(f"docs/silver_data.js: {len(data['races'])} races, as of {data['as_of'] or '-'}")
