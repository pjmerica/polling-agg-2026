# -*- coding: utf-8 -*-
"""PRIMARY model vs market comparison -> docs/primary_model_data.js.

Joins the model repo's primary nominee probabilities
(data/processed/model_primary_predictions_2026.csv, produced by predict_primary.py)
against candidate-level primary markets. Venue per race: KALSHI nominee markets
("Will Ken Paxton be the Republican nominee for Senate in Texas?") PREFERRED (user
decision 2026-07-16), Polymarket win-the-primary markets as fallback. Races with no
market on either venue are still emitted (venue=null) for the page's
"show races without markets" toggle.

Upcoming + just-decided primaries (election_date >= today - 2 days): the inverse of the
general Model-vs-Markets tab, which requires primaries to be DECIDED. The 2-day grace window
(added 2026-07-22, user request) keeps a race on the page through election day and the day
after, since results trickle in rather than posting instantly at midnight.

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
from datetime import date, timedelta

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

# Polymarket phrases candidate primary markets at least two ways:
#   "Will Andy Biggs win the 2026 Arizona Governor Republican primary?"
#   "Will Mike Rogers win the Republican Primary for U.S. Senate in Michigan?"  (no year)
# so: name = text between 'Will' and 'win', require the word 'primary' anywhere after.
MKT_RX = re.compile(r"^will (?P<name>[^?%]+?) win (?:the )?.*?primar", re.I)
# vote-share band markets ("Will Platner win between 70% and 75% of votes in the Maine
# Senate Democratic Primary?") are NOT win-the-primary markets - exclude them
BAND_RX = re.compile(r"\bvotes?\b|%|less than|more than|at least|between", re.I)

# Kalshi's candidate primary markets: "Will Ken Paxton be the Republican nominee for
# Senate in Texas?" (196 such markets incl. 8 Senate races Polymarket lacks). Excluded:
# "...AND General Election winner..." combo markets, CA/AK placement markets ("finish
# 1st/2nd/3rd", "top-four"), county markets, polling-average props.
# '(DFL)' = Minnesota's Democratic-Farmer-Labor suffix: 'the Democratic (DFL) nominee'
KALSHI_RX = re.compile(
    r"^will (?P<name>[^?]+?) be the (?:democratic|republican|gop|dem)\.?"
    r"(?:\s*\([^)]*\))?\s+nominee",
    re.I)
KALSHI_EXCL_RX = re.compile(r"\bAND\b|finish \d|top-four|top four|county|outperform", re.I)

# House nominee events carry NO race_id on their markets - the race lives in the EVENT
# title instead: "WI-07 Republican nominee?" (160 events / 640 candidate markets as of
# 2026-07; requiring race_id made House invisible and produced a wrong "Kalshi has no
# House primary markets" conclusion).
KALSHI_HOUSE_EVENT_RX = re.compile(
    r"^(?P<st>[A-Z]{2})-(?P<di>\d{1,2}|AL)\s+(?P<party>Democratic|Republican)\s+nominee",
    re.I)

def load_kalshi_primary_markets():
    k = pd.read_csv(os.path.join(REPO, "data", "raw", "kalshi_markets.csv"),
                    low_memory=False)
    if "status" in k.columns:
        k = k[k["status"].astype(str).str.lower().eq("active")]
    out = {}

    def add(key, name, r):
        out.setdefault(key, {})[norm_name(name)] = dict(
            prob=float(r.implied_prob), volume=float(getattr(r, "volume", 0) or 0),
            question=str(r.market_title), market_candidate=name)

    for r in k.itertuples():
        t = str(r.market_title)
        if KALSHI_EXCL_RX.search(t) or pd.isna(r.implied_prob):
            continue
        m = KALSHI_RX.match(t)
        if not m:
            continue
        ev = str(r.event_title)
        if "2028" in ev or "2028" in t:
            continue                     # 2028 senate/presidential nominee props
        if pd.notna(r.race_id):
            # statewide (Senate/Governor): race_id present on the market row
            parts = str(r.race_id).split("-")
            if len(parts) < 3 or parts[1] not in OFFICE_FROM_CODE:
                continue
            office, state = OFFICE_FROM_CODE[parts[1]], parts[2].upper()
            district = (str(int(parts[3])) if office == "House" and len(parts) > 3
                        and parts[3].isdigit() else "")
            tl = t.lower()
            party = "DEM" if ("democratic" in tl or " dem" in tl) else "REP"
            base = f"2026_{state}_{office}" + (f"-{district}" if district else "")
            add(base + "_" + party, m.group("name"), r)
        else:
            # House: derive the race from the event title. At-large 'AL' -> district 1
            # (matches the model's race keys).
            me = KALSHI_HOUSE_EVENT_RX.match(ev)
            if not me:
                continue
            di = "1" if me.group("di").upper() == "AL" else str(int(me.group("di")))
            party = "DEM" if me.group("party").lower() == "democratic" else "REP"
            add(f"2026_{me.group('st').upper()}_House-{di}_{party}", m.group("name"), r)
    return out

_STATE_ABBR = {
    'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA',
    'colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA',
    'hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA','kansas':'KS',
    'kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD','massachusetts':'MA',
    'michigan':'MI','minnesota':'MN','mississippi':'MS','missouri':'MO','montana':'MT',
    'nebraska':'NE','nevada':'NV','new hampshire':'NH','new jersey':'NJ','new mexico':'NM',
    'new york':'NY','north carolina':'NC','north dakota':'ND','ohio':'OH','oklahoma':'OK',
    'oregon':'OR','pennsylvania':'PA','rhode island':'RI','south carolina':'SC',
    'south dakota':'SD','tennessee':'TN','texas':'TX','utah':'UT','vermont':'VT',
    'virginia':'VA','washington':'WA','west virginia':'WV','wisconsin':'WI','wyoming':'WY'}

def load_primary_markets(preds=None):
    """preds (optional): the predictions frame, used to resolve OFFICE-LESS orphan
    markets by candidate identity - 'Will Abdul El-Sayed win the 2026 Michigan
    Democratic Primary?' names no office, so the feed scraper left race_id blank; the
    candidate + state + party uniquely identify the model race."""
    cand_lookup = {}
    if preds is not None:
        for r in preds.itertuples():
            cand_lookup.setdefault((r.state, r.party), {})[r.cand_norm] = r.race_id
    p = pd.read_csv(os.path.join(REPO, "data", "raw", "polymarket_markets.csv"),
                    low_memory=False)
    if "closed" in p.columns:
        p = p[~p["closed"].astype(bool)]
    p = p[p["question"].astype(str).str.contains("primary", case=False, na=False)]
    out = {}   # {(model_race_base + _party): {cand_norm: {...}}}
    for r in p.itertuples():
        q = str(r.question)
        if BAND_RX.search(q):
            continue                    # vote-share band market, not a win market
        m = MKT_RX.match(q)
        if not m or pd.isna(r.implied_prob):
            continue
        ql = q.lower()
        party = ("DEM" if "democratic" in ql or "democrat" in ql
                 else "REP" if "republican" in ql else None)
        if party is None:
            continue
        key = None
        if pd.notna(r.race_id):
            parts = str(r.race_id).split("-")       # 2026-GOV-MI[-01]
            if len(parts) < 3 or parts[1] not in OFFICE_FROM_CODE:
                continue
            office, state = OFFICE_FROM_CODE[parts[1]], parts[2].upper()
            district = str(int(parts[3])) if office == "House" and len(parts) > 3 and parts[3].isdigit() else ""
            key = f"2026_{state}_{office}" + (f"-{district}" if district else "") + "_" + party
        else:
            # orphan: resolve by candidate identity within (state, party)
            st = next((ab for nm, ab in _STATE_ABBR.items() if nm in ql), None)
            if st is None:
                continue
            key = cand_lookup.get((st, party), {}).get(norm_name(m.group("name")))
            if key is None:
                continue
        out.setdefault(key, {})[norm_name(m.group("name"))] = dict(
            prob=float(r.implied_prob),
            volume=float(getattr(r, "volume", 0) or 0),
            question=q, market_candidate=m.group("name"))
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
    markets = load_primary_markets(preds)     # Polymarket (fallback venue)
    kalshi = load_kalshi_primary_markets()    # Kalshi nominee markets (preferred)
    today = date.today().isoformat()

    # SHAP explanations (model repo's explain_primary.py; optional)
    exp_path = os.path.join(REPO, "data", "processed",
                            "model_primary_explanations_2026.json")
    explanations = {}
    if os.path.exists(exp_path):
        with open(exp_path, encoding="utf-8") as f:
            explanations = json.load(f).get("races", {})
        print(f"primary explanations loaded: {len(explanations)} races")

    cutoff = (date.today() - timedelta(days=2)).isoformat()   # keep races visible through
                                                                # election day + 2 (results
                                                                # trickle in; don't vanish the
                                                                # page the instant polls close)
    races, n_matched = [], 0
    for rid, g in preds.groupby("race_id"):
        ed = str(g["election_date"].iloc[0])[:10]
        if not ed or ed == "nan" or ed < cutoff:
            continue                            # decided 2+ days ago, or dateless: not comparable
        # venue: KALSHI preferred (user decision 2026-07-16), Polymarket fallback
        book, venue = kalshi.get(rid, {}), "kalshi"
        if not book:
            book, venue = markets.get(rid, {}), "poly"
        if not book:
            venue = None                        # kept: the no-markets toggle shows these
        book_sum = sum(v["prob"] for v in book.values()) if book else 0.0
        full_book = book_sum >= 0.85
        cands = []
        for r in g.itertuples():
            mkt = book.get(r.cand_norm) if book else None
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
        for c in cands:
            c["edge"] = (round(c["model"] - c["market"], 4)
                         if c["market"] is not None else None)
        matched = [c for c in cands if c["market"] is not None]
        if book and not matched:
            venue = None                        # a book exists but no candidate matched
        unmatched_mkt = ([v["market_candidate"] for k, v in book.items()
                          if k not in set(g["cand_norm"])] if book else [])
        top = max(matched, key=lambda c: abs(c["edge"])) if matched else None
        races.append(dict(
            race_id=rid, state=g["state"].iloc[0], office=g["office"].iloc[0],
            district=str(g["district"].iloc[0]).split(".")[0].replace("nan", ""),
            party=g["party"].iloc[0], election_date=ed,
            n_polls=int(g["n_surveys"].iloc[0]),
            venue=(venue if matched else None),
            partial_book=(bool(matched) and not full_book),
            book_sum=(round(book_sum, 3) if matched else None),
            unmatched_market_candidates=unmatched_mkt,
            max_abs_edge=(abs(top["edge"]) if top else 0.0),
            explain=explanations.get(rid),
            # raw win_prob summed across the field, before within-race normalization (model
            # repo's predict_primary.py; added 2026-07-22). A crowded weak-signal field can
            # sum well under 1 - normalizing then manufactures a confident-looking "model"
            # number (e.g. SD-Governor-REP: raw sum 0.064, so a real 3.3% became a
            # normalized 51.8%). low_confidence_field flags races where that's happening so
            # the page can caveat the leader instead of presenting it as a confident pick.
            field_confidence=(g["field_confidence"].iloc[0]
                              if "field_confidence" in g.columns else None),
            low_confidence_field=bool(g["low_confidence_field"].iloc[0])
                                 if "low_confidence_field" in g.columns else False,
            candidates=sorted(cands, key=lambda c: -c["model"]),
        ))
    # market races first; within them thin-poll races (n_polls < 3) sort BELOW everything
    # else regardless of edge size (a 90-pt "edge" off one stale survey is the market
    # knowing something the polls don't). No-market races last (shown via page toggle).
    races.sort(key=lambda r: (r["venue"] is not None, r["n_polls"] >= 3,
                              r["max_abs_edge"]), reverse=True)

    meta = _meta()
    payload = dict(
        generated_at=pd.Timestamp.now().isoformat(),
        predictions_as_of=meta.get("generated_at"),
        polls_as_of=meta.get("polls_max_end_date"),
        note="model = within-race normalized nominee prob; market = KALSHI nominee "
             "markets preferred, Polymarket fallback (per race), vig-normalized across "
             "the race book when >=85% complete; edge = model - market. Upcoming "
             "primaries only; races without any market carry venue=null (page toggle).",
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
