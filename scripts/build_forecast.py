"""Forecast page data -> docs/forecast_data.js (rendered by docs/predictions.html). 2026-10-08.

Since 2026-10-23 every race on the ballot: the poll model's races (basis "polls") plus, for the
races no pollster covers, the no-polls model's (basis "fundamentals",
data/processed/model_fundamentals_predictions_2026.csv from the model repo's
models/fundamentals/predict_unpolled.py), with no stress test and a note saying so.

Every race the general-election model predicts, with EVERY candidate (independents included),
the model's win probability and projected margin, the +/-3-pt polling-miss stress test, the
per-race explainer (model_explanations_2026.json), and the market price for context.

Unlike docs/model_data.js (Model vs Markets), this is not a D-vs-R comparison: candidate-level
numbers come straight from the model outputs, so an independent like Kevin Kiley (CA-6) or Dan
Osborn (NE-Sen) is shown as the real opponent rather than dropped from a Dem/Rep sum.

Called at the end of analysis/model_compare.py (so every CI path that refreshes the model data
rebuilds this too); runnable standalone:  python scripts/build_forecast.py
"""
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from utils.races import RACE_BY_ID  # noqa: E402

PROC = os.path.join(REPO, "data", "processed")
OUT = os.path.join(REPO, "docs", "forecast_data.js")

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
OFFICE_CODE = {"Senate": "SEN", "Governor": "GOV", "House": "H"}

# races where the November number is not a normal two-candidate general
NOTES = {
    "LA_House": ("Louisiana's House races are an all-party first round on Nov 3, with a "
                 "Dec 12 runoff between the top two if nobody tops 50%. The polls are split "
                 "multi-candidate fields, so treat these numbers with extra caution."),
    "RCV": ("Ranked-choice race: the model uses the final-round head-to-head polls "
            "between the two expected finalists."),
    "FUND": ("No public polls in this race, so this is the no-polls model: which party holds the "
             "seat, its past results (the new map's lean where districts were redrawn), the national "
             "environment, fundraising and the candidates' experience."),
    "SAME_PARTY": ("Several candidates share a party here, and the no-polls model can barely tell "
                   "them apart, so read the party's combined chance rather than any one candidate's."),
}


def _party_books():
    """Each venue's vetted party-winner book by agg race id (analysis/model_compare's loaders,
    the same prices data.js carries), for the market column of races the poll model skips."""
    try:
        from analysis.model_compare import load_party_markets, norm_pair
    except Exception:
        return {}, None
    books = {}
    for name, csv, col in (("kalshi", "kalshi_markets.csv", "market_title"),
                           ("polymarket", "polymarket_markets.csv", "question")):
        p = os.path.join(REPO, "data", "raw", csv)
        if os.path.exists(p):
            try:
                books[name] = load_party_markets(p, col)
            except Exception:
                books[name] = {}
    return books, norm_pair


def _fund_races(seen, books, norm_pair):
    """Races no pollster covers, from the no-polls model (models/fundamentals/predict_unpolled.py
    in the model repo, 2026-10-23), so every race on the ballot has a model number."""
    fpath = os.path.join(PROC, "model_fundamentals_predictions_2026.csv")
    if not os.path.exists(fpath):
        return []
    fund = pd.read_csv(fpath)
    epath = os.path.join(PROC, "model_fundamentals_explanations_2026.json")
    explain = json.load(open(epath, encoding="utf-8")).get("races", {}) if os.path.exists(epath) else {}
    out = []
    for rid, g in fund.groupby("race_id", sort=False):
        if rid in seen:
            continue
        first = g.iloc[0]
        st, off, di = first["state"], first["office"], first["district"]
        aid = _agg_id(st, off, di)
        meta = RACE_BY_ID.get(aid)
        cands = [dict(name=r.candidate,
                      party=str(r.display_party if pd.notna(r.display_party) else r.party)[:3].upper(),
                      win=_num(r.win_prob_norm), win_r3=None, win_d3=None, margin=None,
                      poll_avg=None, n_polls=0)
                 for r in g.sort_values("win_prob_norm", ascending=False).itertuples()]
        notes = [NOTES["FUND"]]
        parties = [c["party"] for c in cands if c["party"] in ("DEM", "REP")]
        if len(parties) != len(set(parties)):
            notes.append(NOTES["SAME_PARTY"])
        if st == "LA" and off == "House":
            notes.append(NOTES["LA_House"])
        market = None
        dem = next((c for c in cands if c["party"] == "DEM"), None)
        # same-party top two: the party market says nothing about which one (the polled rule below)
        same_top = len(cands) >= 2 and cands[0]["party"] == cands[1]["party"] and cands[0]["party"] in ("DEM", "REP")
        if dem and norm_pair and parties.count("DEM") == 1 and not same_top:
            qs = []
            for b in books.values():
                bk = b.get(aid) or {}
                d, r_ = (bk.get("DEM") or {}).get("prob"), (bk.get("REP") or {}).get("prob")
                if d is not None:
                    qs.append(norm_pair(d, r_))
            qs = [q for q in qs if q is not None]
            if qs:
                market = dict(prob=round(sum(qs) / len(qs), 4), side="DEM", name=dem["name"])
        out.append(dict(
            id=rid, agg_id=aid, state=st, state_name=STATE_NAMES.get(st, st), office=off,
            district=("" if pd.isna(di) else str(di).split(".")[0]), special=(str(di) == "S"),
            incumbent=(meta.incumbent_name if meta else None),
            incumbent_party=(meta.incumbent_party if meta else None),
            open_seat=(bool(meta.open_seat) if meta else None),
            fragile=False, n_surveys=0, basis="fundamentals", cands=cands, market=market,
            notes=notes, explain=explain.get(rid)))
    return out


def _agg_id(state, office, district):
    rid = f"2026-{OFFICE_CODE[office]}-{state}"
    di = "" if pd.isna(district) else str(district).split(".")[0]
    if di == "S":
        return rid + "-S"
    if office == "House" and di not in ("", "nan"):
        return rid + f"-{int(di):02d}"
    return rid


def _num(v, nd=4):
    return None if v is None or pd.isna(v) else round(float(v), nd)


def build(compare_rows=None, predictions_as_of=None, polls_as_of=None):
    preds = pd.read_csv(os.path.join(PROC, "model_predictions_2026.csv"))
    mpath = os.path.join(PROC, "model_margin_predictions_2026.csv")
    margins = pd.read_csv(mpath) if os.path.exists(mpath) else pd.DataFrame()
    epath = os.path.join(PROC, "model_explanations_2026.json")
    explain = json.load(open(epath, encoding="utf-8")).get("races", {}) if os.path.exists(epath) else {}
    mk = {r["race_id"]: r for r in (compare_rows or [])}
    mg = ({(r.race_id, r.candidate): r for r in margins.itertuples()} if len(margins) else {})

    races = []
    for rid, g in preds.groupby("race_id", sort=False):
        g = g.copy()
        # +/-3-pt stress test: raw per-candidate probabilities, normalised within the race
        for col in ("win_prob_R3", "win_prob_D3"):
            if col in g.columns:
                s = g[col].sum()
                g[col + "_n"] = g[col] / s if s > 0 else None
        first = g.iloc[0]
        st, off, di = first["state"], first["office"], first["district"]
        aid = _agg_id(st, off, di)
        meta = RACE_BY_ID.get(aid)
        cands = []
        for r in g.sort_values("win_prob_norm", ascending=False).itertuples():
            m = mg.get((rid, r.candidate))
            cands.append(dict(
                name=r.candidate,
                party=str(r.display_party if pd.notna(r.display_party) else r.party)[:3].upper(),
                win=_num(r.win_prob_norm),
                win_r3=_num(getattr(r, "win_prob_R3_n", None)),
                win_d3=_num(getattr(r, "win_prob_D3_n", None)),
                margin=_num(m.pred_margin, 2) if m is not None else None,
                poll_avg=_num(r.poll_avg, 1),
                n_polls=int(r.n_polls) if pd.notna(r.n_polls) else 0,
            ))
        c = mk.get(rid, {})
        mkt = [v for v in (c.get("kalshi_dem"), c.get("poly_dem")) if v is not None]
        # same-party top two (California top-two D-v-D / R-v-R): the party market prices "a
        # Democrat wins" (~99%) and says nothing about WHICH one, so it is no comparison for
        # either candidate (2026-10-20: CA-7 showed "Markets: Vang 98%" against Matsui)
        if len(cands) >= 2 and cands[0]["party"] == cands[1]["party"] and cands[0]["party"] in ("DEM", "REP"):
            mkt = []
        notes = []
        if st == "LA" and off == "House":
            notes.append(NOTES["LA_House"])
        if (st == "ME" and off in ("Senate", "House")) or st == "AK":
            notes.append(NOTES["RCV"])
        races.append(dict(
            id=rid, agg_id=aid, state=st, state_name=STATE_NAMES.get(st, st), office=off,
            district=("" if pd.isna(di) else str(di).split(".")[0]),
            special=(str(di) == "S"),
            incumbent=(meta.incumbent_name if meta else None),
            incumbent_party=(meta.incumbent_party if meta else None),
            open_seat=(bool(meta.open_seat) if meta else None),
            fragile=bool(first.get("bias_fragile", 0)),
            n_surveys=int(g["n_surveys"].max()) if "n_surveys" in g and g["n_surveys"].notna().any() else None,
            basis="polls",
            cands=cands,
            market=(dict(prob=round(sum(mkt) / len(mkt), 4),
                         side=c.get("slot_market") or "DEM",
                         name=c.get("dem_name")) if mkt else None),
            notes=notes,
            explain=explain.get(rid),
        ))
    books, norm_pair = _party_books()
    races += _fund_races({r["id"] for r in races}, books, norm_pair)
    payload = dict(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        predictions_as_of=predictions_as_of, polls_as_of=polls_as_of, races=races)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const FORECAST = ")
        json.dump(payload, f, separators=(",", ":"))
        f.write(";\n")
    print(f"wrote {OUT}: {len(races)} races")
    return payload


if __name__ == "__main__":
    build()
