"""Model vs market comparison -> docs/model_data.js (rendered by docs/model.html).

Joins the polling-prediction-model's win probabilities (predictions_2026.csv, produced by
predict.py in the sibling "Polling prediction model" repo) against Kalshi and Polymarket
party-level race markets ("Will Democrats/Republicans win the X race?"), for races whose
state PRIMARY IS ALREADY DECIDED (per data/raw/primaries.json Ballotpedia dates) — hypo
matchups from unresolved primaries make model probabilities apples-to-oranges vs markets.

Market probabilities are vig-normalized per venue: dem_norm = D / (D + R), so a venue
quoting D 52 / R 49 shows as D 51.5. Raw quotes are kept alongside.

    python analysis/model_compare.py [--preds path\to\predictions_2026.csv]
"""
import argparse
import json
import os
import re
from datetime import date

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_PREDS = os.path.join(REPO, "..", "..", "Polling prediction model",
                             "predictions_2026.csv")

OFFICE_CODE = {"Senate": "SEN", "House": "H", "Governor": "GOV"}

PARTY_RX = re.compile(r"^will (the )?(democrat|republican)\w*s? win the .*"
                      r"(race|senate|house|governor|gubernatorial)", re.I)

def market_race_id(row):
    """model race key -> feed race_id format: 2026_ME_Senate -> 2026-SEN-ME,
    2026_AL_House-1 -> 2026-H-AL-01."""
    off = OFFICE_CODE[row["office"]]
    rid = f"2026-{off}-{row['state']}"
    di = str(row["district"]) if pd.notna(row["district"]) else ""
    di = di.split(".")[0]
    if row["office"] == "House" and di not in ("", "nan"):
        rid += f"-{int(di):02d}"
    return rid

def load_party_markets(path, title_col):
    df = pd.read_csv(path, low_memory=False)
    df = df[df["race_id"].notna()].copy()
    if "status" in df.columns:
        df = df[df["status"].astype(str).str.lower().eq("active")]
    if "closed" in df.columns:
        df = df[~df["closed"].astype(bool)]
    df = df[df[title_col].astype(str).str.match(PARTY_RX)]
    df["party"] = df[title_col].str.extract(r"(?i)(democrat|republican)")[0].str.upper().str[:3]
    df["party"] = df["party"].map({"DEM": "DEM", "REP": "REP"})
    keep = df.dropna(subset=["party", "implied_prob"])
    # one row per race+party: highest-volume market wins if duplicated
    vol = "volume" if "volume" in keep.columns else None
    if vol:
        keep = keep.sort_values(vol, ascending=False)
    keep = keep.drop_duplicates(subset=["race_id", "party"], keep="first")
    out = {}
    for r in keep.itertuples():
        d = out.setdefault(r.race_id, {})
        d[r.party] = dict(prob=float(r.implied_prob),
                          volume=float(getattr(r, vol) or 0) if vol else None)
    return out

def decided_primary_states(today=None):
    """States whose LAST scheduled primary/runoff date (Ballotpedia) is before today."""
    with open(os.path.join(REPO, "data", "raw", "primaries.json"), encoding="utf-8") as f:
        pr = json.load(f)
    today = today or date.today().isoformat()
    last = {}
    for r in pr.get("races", []):
        st, dt = r.get("state_abbrev"), r.get("date_iso")
        if st and dt:
            last[st] = max(last.get(st, ""), dt)
    return {st for st, dt in last.items() if dt < today}, last

def norm_pair(d, r):
    """Vig-normalized DEM probability from raw D and R quotes (either may be missing)."""
    if d is not None and r is not None and (d + r) > 0:
        return d / (d + r)
    return d  # single-sided quote: use as-is

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", default=DEFAULT_PREDS)
    args = ap.parse_args()

    preds = pd.read_csv(args.preds)
    decided, last_primary = decided_primary_states()
    print(f"states with decided primaries: {len(decided)} "
          f"(of {len(last_primary)} with known dates)")

    kalshi = load_party_markets(os.path.join(REPO, "data", "raw", "kalshi_markets.csv"),
                                "market_title")
    poly = load_party_markets(os.path.join(REPO, "data", "raw", "polymarket_markets.csv"),
                              "question")
    print(f"party-level race markets: kalshi {len(kalshi)} races, polymarket {len(poly)}")

    rows = []
    for rid, g in preds.groupby("race_id"):
        st = g["state"].iloc[0]
        if st not in decided:
            continue
        mrid = market_race_id(g.iloc[0])
        dem = g[g["party"] == "DEM"]
        rep = g[g["party"] == "REP"]
        model_dem = float(dem["win_prob_norm"].sum()) if len(dem) else None
        k, p = kalshi.get(mrid, {}), poly.get(mrid, {})
        if not k and not p:
            continue          # nothing to compare against
        kd = k.get("DEM", {}).get("prob"); kr = k.get("REP", {}).get("prob")
        pdm = p.get("DEM", {}).get("prob"); pr_ = p.get("REP", {}).get("prob")
        row = dict(
            race_id=rid, market_race_id=mrid, state=st,
            office=g["office"].iloc[0],
            district=str(g["district"].iloc[0]).split(".")[0].replace("nan", ""),
            primary_date=last_primary.get(st),
            dem_name=(dem["candidate"].iloc[0] if len(dem) else None),
            rep_name=(rep["candidate"].iloc[0] if len(rep) else None),
            n_polls=int(g["n_polls"].sum()),
            model_dem=model_dem,
            kalshi_dem_raw=kd, kalshi_rep_raw=kr,
            kalshi_dem=norm_pair(kd, kr),
            kalshi_volume=(k.get("DEM", {}).get("volume") or 0) + (k.get("REP", {}).get("volume") or 0),
            poly_dem_raw=pdm, poly_rep_raw=pr_,
            poly_dem=norm_pair(pdm, pr_),
            poly_volume=(p.get("DEM", {}).get("volume") or 0) + (p.get("REP", {}).get("volume") or 0),
        )
        for venue in ("kalshi", "poly"):
            mv = row[f"{venue}_dem"]
            row[f"edge_{venue}"] = (round(model_dem - mv, 4)
                                    if (mv is not None and model_dem is not None) else None)
        rows.append(row)

    rows.sort(key=lambda r: -max(abs(r.get("edge_kalshi") or 0), abs(r.get("edge_poly") or 0)))
    payload = dict(
        generated_at=pd.Timestamp.now().isoformat(),
        note="model_dem = model's normalized DEM win prob; venue *_dem are vig-normalized "
             "(D/(D+R)); edge = model - market (positive = model likes DEM more than market). "
             "Only races in states whose primaries (incl. runoffs) are already decided.",
        decided_states=sorted(decided),
        races=rows,
    )
    out = os.path.join(REPO, "docs", "model_data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("const MODEL_COMPARE = ")
        json.dump(payload, f)
        f.write(";\n")
    print(f"wrote {out}: {len(rows)} comparable races")
    if rows:
        top = rows[0]
        print("biggest edge:", top["race_id"], "model_dem", round(top["model_dem"], 3),
              "kalshi", top["kalshi_dem"], "poly", top["poly_dem"])

if __name__ == "__main__":
    main()
