"""Model vs market comparison -> docs/model_data.js (rendered by docs/model.html).

Joins the polling-prediction-model's win probabilities (predictions_2026.csv, produced by
predict.py in the sibling "Polling prediction model" repo) against Kalshi and Polymarket
party-level race markets ("Will Democrats/Republicans win the X race?"), for races whose
state PRIMARY IS ALREADY DECIDED (per data/raw/primaries.json Ballotpedia dates) — hypo
matchups from unresolved primaries make model probabilities apples-to-oranges vs markets.

Market probabilities are vig-normalized per venue: dem_norm = D / (D + R), so a venue
quoting D 52 / R 49 shows as D 51.5. Raw quotes are kept alongside.

    python analysis/model_compare.py [--preds path/to/predictions_2026.csv]
"""
import argparse
import json
import os
import re
from datetime import date

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MODEL_REPO = os.path.join(REPO, "..", "..", "Polling prediction model")

def _first_existing(*paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[0]

# Committed snapshots in THIS repo first (lets the GitHub Action refresh the market side on
# its own); the sibling model-repo outputs are the fallback for local runs.
DEFAULT_PREDS = _first_existing(
    os.path.join(REPO, "data", "processed", "model_predictions_2026.csv"),
    os.path.join(MODEL_REPO, "predictions_2026.csv"))
DEFAULT_MARGIN_PREDS = _first_existing(
    os.path.join(REPO, "data", "processed", "model_margin_predictions_2026.csv"),
    os.path.join(MODEL_REPO, "margin_predictions_2026.csv"))

OFFICE_CODE = {"Senate": "SEN", "House": "H", "Governor": "GOV"}

STATE_ABBR = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
    'Connecticut':'CT','Delaware':'DE','District of Columbia':'DC','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY',
    'Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
    'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH',
    'New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND',
    'Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
    'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA',
    'Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
}
_STATES_RX = "|".join(sorted(STATE_ABBR, key=len, reverse=True))

# Kalshi "margin of victory" ladders (race_id is NaN in the feed for these — parsed from titles):
#   Will the margin of victory for Democrats in the U.S. Senate election in Maine be at least 4 percentage points?
#   Will the margin of victory for Republicans in the governor election in Ohio be at least 6 percentage points?
#   Will the margin of victory for Democrats in the Wisconsin's 3rd District House election be at least 2 percentage points?
MOV_RX = re.compile(
    r"^Will the margin of victory for (Democrats|Republicans) in the "
    r"(?:U\.S\. Senate election in (?P<sen>" + _STATES_RX + r")"
    r"|governor election in (?P<gov>" + _STATES_RX + r")"
    r"|(?P<hst>" + _STATES_RX + r")(?:'s (?P<dist>\d+)\w{2} District)? House election)"
    r" be at least (?P<n>\d+) percentage points", re.I)

def parse_mov_markets(kalshi_csv):
    """-> {model_race_id: {'DEM': [(threshold, prob, volume), ...], 'REP': [...]}}"""
    k = pd.read_csv(kalshi_csv, low_memory=False)
    k = k[k["status"].astype(str).str.lower().eq("active")]
    out = {}
    for r in k.itertuples():
        m = MOV_RX.match(str(r.market_title))
        if not m:
            continue
        party = "DEM" if m.group(1).lower().startswith("dem") else "REP"
        if m.group("sen"):
            rid = f"2026_{STATE_ABBR[m.group('sen')]}_Senate"
        elif m.group("gov"):
            rid = f"2026_{STATE_ABBR[m.group('gov')]}_Governor"
        else:
            di = m.group("dist") or "1"     # at-large House = district 1 in our race ids
            rid = f"2026_{STATE_ABBR[m.group('hst')]}_House-{int(di)}"
        if pd.isna(r.implied_prob):
            continue
        out.setdefault(rid, {}).setdefault(party, []).append(
            (int(m.group("n")), float(r.implied_prob), float(r.volume or 0)))
    return out

def ladder_median(ladder, p_win=None):
    """Implied MEDIAN margin from an 'at least N' ladder [(N, P(margin>=N), vol)].

    Anchored at (0, p_win) when the party-level win prob is known. Returns None if the
    ladder never reaches 50% (that party is not the market favorite)."""
    pts = sorted(ladder)
    xs = [0.0] + [float(n) for n, _, _ in pts] if p_win is not None else [float(n) for n, _, _ in pts]
    ps = ([float(p_win)] if p_win is not None else []) + [p for _, p, _ in pts]
    ps = pd.Series(ps).cummin().tolist()          # enforce monotone non-increasing
    if not ps or ps[0] < 0.5:
        return None
    for i in range(len(ps) - 1):
        if ps[i] >= 0.5 > ps[i + 1]:
            x0, x1, p0, p1 = xs[i], xs[i + 1], ps[i], ps[i + 1]
            return x0 + (x1 - x0) * (p0 - 0.5) / (p0 - p1) if p0 > p1 else x0
    return xs[-1]   # still >=50% at the top rung: margin at least the highest threshold

def market_margin_dem(ladders, kalshi_dem_raw=None, kalshi_rep_raw=None):
    """Signed (DEM minus REP) market-implied median margin from the two party ladders."""
    d = ladder_median(ladders.get("DEM", []), kalshi_dem_raw) if ladders.get("DEM") else None
    r = ladder_median(ladders.get("REP", []), kalshi_rep_raw) if ladders.get("REP") else None
    if d is not None:
        return round(d, 1)
    if r is not None:
        return round(-r, 1)
    return None

PARTY_RX = re.compile(r"^will (the )?(democrat|republican)\w*s? win the .*"
                      r"(race|senate|house|governor|gubernatorial)", re.I)

def market_race_id(row):
    """model race key -> feed race_id format: 2026_ME_Senate -> 2026-SEN-ME,
    2026_AL_House-1 -> 2026-H-AL-01."""
    off = OFFICE_CODE[row["office"]]
    rid = f"2026-{off}-{row['state']}"
    di = str(row["district"]) if pd.notna(row["district"]) else ""
    di = di.split(".")[0]
    if di == "S":                                   # special election (own market race_id)
        rid += "-S"
    elif row["office"] == "House" and di not in ("", "nan"):
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
    ap.add_argument("--margin-preds", default=DEFAULT_MARGIN_PREDS)
    args = ap.parse_args()

    preds = pd.read_csv(args.preds)
    mpreds = pd.read_csv(args.margin_preds) if os.path.exists(args.margin_preds) else None
    # 2025-26 mid-decade redistricting: House fundamentals (prior margin, incumbency joins)
    # key on district numbers that describe OLD boundaries in these states — flag them.
    rd_path = os.path.join(REPO, "data", "processed", "redistricted_2026.csv")
    redrawn = (set(pd.read_csv(rd_path)["state"]) if os.path.exists(rd_path) else set())
    decided, last_primary = decided_primary_states()
    print(f"states with decided primaries: {len(decided)} "
          f"(of {len(last_primary)} with known dates)")

    kalshi_csv = os.path.join(REPO, "data", "raw", "kalshi_markets.csv")
    kalshi = load_party_markets(kalshi_csv, "market_title")
    poly = load_party_markets(os.path.join(REPO, "data", "raw", "polymarket_markets.csv"),
                              "question")
    mov = parse_mov_markets(kalshi_csv)
    print(f"party-level race markets: kalshi {len(kalshi)} races, polymarket {len(poly)}; "
          f"kalshi margin-of-victory ladders: {len(mov)} races")

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
            redistricted=bool(g["office"].iloc[0] == "House" and st in redrawn),
            # pick flips under a +/-3pt national poll shift => treat as no-edge (poll errors
            # are cycle-correlated; see the model repo's HANDOFF.md)
            bias_fragile=bool(g["bias_fragile"].max()) if "bias_fragile" in g.columns else None,
            office=g["office"].iloc[0],
            district=str(g["district"].iloc[0]).split(".")[0].replace("nan", ""),
            primary_date=last_primary.get(st),
            dem_name=(dem["candidate"].iloc[0] if len(dem) else None),
            rep_name=(rep["candidate"].iloc[0] if len(rep) else None),
            # distinct surveys the MODEL used (n_polls is a per-candidate row count that
            # over-sums; n_surveys = pollster+date pairs the model ingested for this race)
            n_polls=(int(g["n_surveys"].iloc[0]) if "n_surveys" in g.columns
                     else int(g["n_polls"].sum())),
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

        # --- margin model + models-agree flag + Kalshi margin-of-victory comparison ---
        row["model_margin_dem"] = None
        row["models_agree"] = None
        if mpreds is not None:
            mg = mpreds[mpreds["race_id"] == rid]
            md_ = mg[mg["party"] == "DEM"]["pred_margin"]
            mr_ = mg[mg["party"] == "REP"]["pred_margin"]
            if len(md_) and len(mr_):
                # per-candidate margins aren't race-consistent; symmetrize to a signed D-R number
                row["model_margin_dem"] = round((float(md_.iloc[0]) - float(mr_.iloc[0])) / 2, 2)
            if len(mg) and model_dem is not None:
                margin_pick = mg.loc[mg["pred_margin"].idxmax()]
                win_pick_party = "DEM" if model_dem >= 0.5 else "REP"
                row["margin_pick_party"] = margin_pick["party"]
                row["margin_pick_name"] = margin_pick["candidate"]
                row["models_agree"] = bool(margin_pick["party"] == win_pick_party)
        mm = market_margin_dem(mov[rid], kd, kr) if rid in mov else None
        row["kalshi_margin_dem"] = mm
        row["margin_edge"] = (round(row["model_margin_dem"] - mm, 1)
                              if (mm is not None and row["model_margin_dem"] is not None) else None)
        rows.append(row)

    rows.sort(key=lambda r: -max(abs(r.get("edge_kalshi") or 0), abs(r.get("edge_poly") or 0)))
    payload = dict(
        generated_at=pd.Timestamp.now().isoformat(),
        # market side refreshes every Action run; the MODEL side only when predictions are
        # re-run locally — surface both timestamps so staleness is visible on the page.
        predictions_as_of=pd.Timestamp(os.path.getmtime(args.preds), unit="s").isoformat(),
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
