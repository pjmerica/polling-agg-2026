# -*- coding: utf-8 -*-
"""PRIMARY model vs market comparison -> docs/primary_model_data.js.

Joins the model repo's primary nominee probabilities
(data/processed/model_primary_predictions_2026.csv, produced by predict_primary.py)
against Polymarket candidate-level primary markets ("Will X win the 2026 Michigan
Democratic Senate primary?"). Kalshi has no downballot-primary markets with usable race
ids as of 2026-07 (its "nominee" markets are 2028-VP trivia) - Polymarket only for now.

Only UPCOMING primaries (election_date >= today): the inverse of the general Model-vs-
Markets tab, which requires primaries to be DECIDED.

Market normalization: candidate quotes within one primary race form a book; when the
matched book sums to >= 0.85 the quotes are vig-normalized (prob / book_sum), else used
raw and flagged partial_book.

    python analysis/model_compare_primary.py
"""
import argparse
import json
import os
import re
import unicodedata
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

DEFAULT_PREDS = _first_existing(
    os.path.join(REPO, "data", "processed", "model_primary_predictions_2026.csv"),
    os.path.join(MODEL_REPO, "primary_predictions_2026.csv"))

OFFICE_FROM_CODE = {"SEN": "Senate", "H": "House", "GOV": "Governor"}

def norm_name(s):
    """Match the model repo's features.norm_name: 'lastname firstinitial'."""
    if s is None or (isinstance(s, float) and s != s):
        return None
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    parts = [w for w in s.split() if w]
    if not parts:
        return None
    last = parts[-1]
    fi = parts[0][0] if parts[0] != last else ""
    return f"{last} {fi}".strip()

MKT_RX = re.compile(r"^will (?P<name>.+?) win the 2026 .*?primary", re.I)

def load_primary_markets():
    p = pd.read_csv(os.path.join(REPO, "data", "raw", "polymarket_markets.csv"),
                    low_memory=False)
    if "closed" in p.columns:
        p = p[~p["closed"].astype(bool)]
    p = p[p["race_id"].notna()]
    p = p[p["question"].astype(str).str.contains("primary", case=False, na=False)]
    out = {}   # {(model_race_base, party): {cand_norm: {...}}}
    for r in p.itertuples():
        m = MKT_RX.match(str(r.question))
        if not m or pd.isna(r.implied_prob):
            continue
        q = str(r.question).lower()
        party = ("DEM" if "democratic" in q or "democrat" in q
                 else "REP" if "republican" in q else None)
        if party is None:
            continue
        parts = str(r.race_id).split("-")       # 2026-GOV-MI[-01]
        if len(parts) < 3 or parts[1] not in OFFICE_FROM_CODE:
            continue
        office, state = OFFICE_FROM_CODE[parts[1]], parts[2].upper()
        district = str(int(parts[3])) if office == "House" and len(parts) > 3 and parts[3].isdigit() else ""
        base = f"2026_{state}_{office}" + (f"-{district}" if district else "")
        key = (base + "_" + party)
        out.setdefault(key, {})[norm_name(m.group("name"))] = dict(
            prob=float(r.implied_prob),
            volume=float(getattr(r, "volume", 0) or 0),
            question=str(r.question), market_candidate=m.group("name"))
    return out

def _meta():
    p = os.path.join(REPO, "data", "processed", "model_primary_predictions_meta.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", default=DEFAULT_PREDS)
    args = ap.parse_args()
    preds = pd.read_csv(args.preds)
    preds["cand_norm"] = preds["candidate"].map(norm_name)
    markets = load_primary_markets()
    today = date.today().isoformat()

    # SHAP explanations (model repo's explain_primary.py; optional)
    exp_path = os.path.join(REPO, "data", "processed",
                            "model_primary_explanations_2026.json")
    explanations = {}
    if os.path.exists(exp_path):
        with open(exp_path, encoding="utf-8") as f:
            explanations = json.load(f).get("races", {})
        print(f"primary explanations loaded: {len(explanations)} races")

    races, n_matched = [], 0
    for rid, g in preds.groupby("race_id"):
        ed = str(g["election_date"].iloc[0])[:10]
        if not ed or ed == "nan" or ed < today:
            continue                            # decided or dateless: not comparable
        book = markets.get(rid, {})
        if not book:
            continue
        book_sum = sum(v["prob"] for v in book.values())
        full_book = book_sum >= 0.85
        cands = []
        for r in g.itertuples():
            mkt = book.get(r.cand_norm)
            cands.append(dict(
                candidate=r.candidate, n_polls=int(r.n_surveys),
                poll_avg=(round(float(r.poll_avg), 1) if r.poll_avg == r.poll_avg else None),
                model=round(float(r.win_prob_norm), 4),
                market_raw=(round(mkt["prob"], 4) if mkt else None),
                market=(round(mkt["prob"] / book_sum, 4) if mkt and full_book
                        else (round(mkt["prob"], 4) if mkt else None)),
                volume=(mkt["volume"] if mkt else None),
            ))
            if mkt:
                n_matched += 1
        matched = [c for c in cands if c["market"] is not None]
        if not matched:
            continue
        for c in cands:
            c["edge"] = (round(c["model"] - c["market"], 4)
                         if c["market"] is not None else None)
        unmatched_mkt = [v["market_candidate"] for k, v in book.items()
                         if k not in set(g["cand_norm"])]
        top = max(matched, key=lambda c: abs(c["edge"]))
        races.append(dict(
            race_id=rid, state=g["state"].iloc[0], office=g["office"].iloc[0],
            district=str(g["district"].iloc[0]).split(".")[0].replace("nan", ""),
            party=g["party"].iloc[0], election_date=ed,
            n_polls=int(g["n_surveys"].iloc[0]),
            partial_book=(not full_book), book_sum=round(book_sum, 3),
            unmatched_market_candidates=unmatched_mkt,
            max_abs_edge=abs(top["edge"]),
            explain=explanations.get(rid),
            candidates=sorted(cands, key=lambda c: -c["model"]),
        ))
    # thin-poll races (n_polls < 3) sort BELOW everything else regardless of edge size:
    # a 90-pt "edge" off one stale survey (CT-Gov REP: 1 poll vs a 97% market favorite)
    # is the market knowing something the polls don't, not alpha
    races.sort(key=lambda r: (r["n_polls"] >= 3, r["max_abs_edge"]), reverse=True)

    meta = _meta()
    payload = dict(
        generated_at=pd.Timestamp.now().isoformat(),
        predictions_as_of=meta.get("generated_at"),
        polls_as_of=meta.get("polls_max_end_date"),
        note="model = within-race normalized nominee prob; market = Polymarket quote, "
             "vig-normalized across the race book when the book is >=85% complete; "
             "edge = model - market. Upcoming primaries only.",
        races=races,
    )
    out = os.path.join(REPO, "docs", "primary_model_data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("const PRIMARY_COMPARE = ")
        json.dump(payload, f)
        f.write(";\n")
    print(f"wrote {out}: {len(races)} upcoming primary races, "
          f"{n_matched} candidate-market matches")
    if races:
        t = races[0]
        print("biggest edge:", t["race_id"], t["candidates"][0]["candidate"],
              "model", t["candidates"][0]["model"], "market", t["candidates"][0]["market"])

if __name__ == "__main__":
    main()
