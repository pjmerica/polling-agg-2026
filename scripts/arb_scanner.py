"""
Cross-market arbitrage scanner.

Compares implied probabilities for the same event across Kalshi, PredictIt,
and Polymarket. Flags gaps after estimated fees and computes guaranteed arb
stake ratios where applicable.

Fee assumptions (round-trip):
  Kalshi:    ~7%  (maker/taker on entry + exit)
  PredictIt: ~15% (10% on profits + 5% withdrawal)
  Polymarket: ~2% (low-fee CLOB)

Arb types:
  guaranteed — pA_dem + pB_rep < 1 (or pA_rep + pB_dem < 1) after fees.
               You can buy both sides and lock in a profit regardless of outcome.
               Stake ratio: sA / sB = (1 - pB) / (1 - pA)
               Guaranteed return % = 1/(pA + pB) - 1  (approx, ignoring fees)

  one-sided  — same outcome priced differently across platforms.
               You're just getting a better price; outcome is still uncertain.

Output: docs/arb_data.js
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

FEES = {
    "kalshi":    0.03,
    "predictit": 0.12,
    "polymarket": 0.03,
}

# URL templates
def kalshi_url(series_ticker):
    if pd.isna(series_ticker) or not series_ticker:
        return None
    return f"https://kalshi.com/markets/{series_ticker}"

def predictit_url(market_id):
    if pd.isna(market_id) or not market_id:
        return None
    return f"https://www.predictit.org/markets/detail/{int(market_id)}"

def polymarket_url(slug):
    if pd.isna(slug) or not slug:
        return None
    return f"https://polymarket.com/event/{slug}"


# ── loaders ──────────────────────────────────────────────────────────────────

def load_kalshi_general():
    """Dem/Rep win prob per race — pick highest open_interest market per race+party."""
    path = RAW / "kalshi_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()

    dem_mask = df["market_title"].str.contains(
        r"Democrat(?:ic)?s?\s+win|Will Democrat(?:ic)?s?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)
    rep_mask = df["market_title"].str.contains(
        r"Republican(?:s)?\s+win|Will Republican(?:s)?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)

    def best(g):
        oi = pd.to_numeric(g["open_interest"], errors="coerce").fillna(0)
        idx = oi.idxmax()
        return g.loc[idx, ["implied_prob", "open_interest", "volume", "series_ticker", "market_title"]]

    dem = df[dem_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    dem = dem.rename(columns={
        "implied_prob": "kalshi_dem",
        "open_interest": "kalshi_oi",
        "volume": "kalshi_volume",
        "series_ticker": "kalshi_series_ticker",
    })

    rep = df[rep_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    rep = rep.rename(columns={"implied_prob": "kalshi_rep", "series_ticker": "kalshi_rep_ticker"})

    merged = dem[["race_id", "kalshi_dem", "kalshi_oi", "kalshi_volume", "kalshi_series_ticker"]].merge(
        rep[["race_id", "kalshi_rep", "kalshi_rep_ticker"]], on="race_id", how="outer"
    )
    merged["kalshi_url"] = merged["kalshi_series_ticker"].apply(kalshi_url)
    return merged


def load_predictit_general():
    """Democratic/Republican party contracts per race."""
    path = RAW / "predictit_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df = df[df["contract_name"].str.strip().isin(["Democratic", "Republican"])].copy()

    dem = df[df["contract_name"].str.strip() == "Democratic"][
        ["race_id", "implied_prob", "best_buy_yes", "best_sell_yes", "market_id"]
    ].rename(columns={"implied_prob": "pi_dem", "best_buy_yes": "pi_dem_buy", "best_sell_yes": "pi_dem_sell"})

    rep = df[df["contract_name"].str.strip() == "Republican"][
        ["race_id", "implied_prob"]
    ].rename(columns={"implied_prob": "pi_rep"})

    merged = dem.merge(rep, on="race_id", how="outer")
    merged["pi_url"] = merged["market_id"].apply(predictit_url)
    return merged


def load_polymarket_general():
    """Polymarket Yes prices for Democrat/Republican win questions."""
    path = RAW / "polymarket_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)

    if "race_id" not in df.columns:
        return pd.DataFrame()

    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df["implied_prob"] = pd.to_numeric(df["implied_prob"], errors="coerce")
    df = df.dropna(subset=["implied_prob"])

    q = df["question"].str.lower()
    df["is_dem"] = q.str.contains(r"democrat|democratic", na=False) & ~q.str.contains(r"republican", na=False)
    df["is_rep"] = q.str.contains(r"republican", na=False) & ~q.str.contains(r"democrat|democratic", na=False)
    df = df[~q.str.contains("nominee|primary|nominate|advance", na=False)]

    # Prefer new event_slug column if present; fall back to condition_id for legacy CSVs.
    slug_col = "event_slug" if "event_slug" in df.columns else ("url_slug" if "url_slug" in df.columns else None)
    if slug_col is None:
        df["_slug"] = df.get("condition_id", "")
    else:
        df["_slug"] = df[slug_col].fillna("").astype(str)
        # Fallback to market_slug when event_slug is blank
        if "market_slug" in df.columns:
            mask = df["_slug"].eq("")
            df.loc[mask, "_slug"] = df.loc[mask, "market_slug"].fillna("").astype(str)

    dem = df[df["is_dem"]][["race_id", "implied_prob", "liquidity", "volume", "_slug"]].copy()
    rep = df[df["is_rep"]][["race_id", "implied_prob", "liquidity", "volume", "_slug"]].copy()

    def best_liq(g):
        liq = pd.to_numeric(g["liquidity"], errors="coerce").fillna(0)
        return g.loc[liq.idxmax()]

    if not dem.empty:
        dem = dem.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        dem = dem.rename(columns={"implied_prob": "pm_dem", "liquidity": "pm_liq", "volume": "pm_volume", "_slug": "pm_dem_slug"})

    if not rep.empty:
        rep = rep.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        rep = rep.rename(columns={"implied_prob": "pm_rep", "liquidity": "pm_rep_liq", "_slug": "pm_rep_slug"})

    if dem.empty and rep.empty:
        return pd.DataFrame()

    result = dem[["race_id", "pm_dem", "pm_liq", "pm_volume", "pm_dem_slug"]] if not dem.empty \
        else pd.DataFrame(columns=["race_id", "pm_dem", "pm_liq", "pm_volume", "pm_dem_slug"])
    if not rep.empty:
        result = result.merge(rep[["race_id", "pm_rep", "pm_rep_slug"]], on="race_id", how="outer")

    # Prefer dem slug for the URL; fall back to rep slug.
    if "pm_rep_slug" in result.columns:
        result["pm_url"] = result["pm_dem_slug"].where(
            result["pm_dem_slug"].notna() & (result["pm_dem_slug"] != ""),
            result["pm_rep_slug"],
        ).apply(polymarket_url)
    else:
        result["pm_url"] = result["pm_dem_slug"].apply(polymarket_url)
    return result


def get_race_meta():
    import sys
    sys.path.insert(0, str(ROOT))
    try:
        from utils.races import RACE_BY_ID
        rows = []
        for race_id, r in RACE_BY_ID.items():
            lbl = f"{r.state_abbrev}-{str(r.district).zfill(2)}" if r.office == "H" else f"{r.state_abbrev} {r.office}"
            rows.append({"race_id": race_id, "state": r.state, "state_abbrev": r.state_abbrev,
                         "office": r.office, "label": lbl})
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"  WARNING: could not load race metadata: {e}")
        return pd.DataFrame(columns=["race_id", "state", "state_abbrev", "office", "label"])


# ── arb math ──────────────────────────────────────────────────────────────────

def compute_arb_math(prob_a, prob_b, prob_a_rep, prob_b_rep, fee_a, fee_b):
    """
    Determine arb type and compute stake ratios.

    guaranteed arb: exists when buying Dem on one side and Rep on the other
    locks in profit regardless of outcome.

    For guaranteed arb: buy Dem at pA on platform A, buy Rep at (1-pB_dem) on platform B.
    This costs pA + (1 - pB_dem). If cost < 1, you profit.

    Stake ratio (per $1 total):
      sA = (1 - pB_rep) / (2 - pA_dem - pB_rep)    [stake on platform A, dem side]
      sB = (1 - pA_dem) / (2 - pA_dem - pB_rep)    [stake on platform B, rep side]
    Guaranteed profit % (pre-fee) = 1 - pA_dem - pB_rep

    one-sided arb: same outcome priced differently — just buy the cheaper one.
    Edge = abs(pA - pB)
    """
    result = {
        "arb_type": "one-sided",
        "guaranteed_return_pct": None,
        "stake_a_pct": None,
        "stake_b_pct": None,
        "stake_a_dollars": None,
        "stake_b_dollars": None,
        "profit_dollars": None,
        "stake_note": None,
    }

    # Check if we can construct a guaranteed arb:
    # Case 1: buy Dem on A (cheaper), buy Rep on B
    # We need Rep price on B = 1 - pm_dem (or pi_rep if available)
    rep_b = prob_b_rep if prob_b_rep is not None and not pd.isna(prob_b_rep) else (1 - prob_b)
    rep_a = prob_a_rep if prob_a_rep is not None and not pd.isna(prob_a_rep) else (1 - prob_a)

    # Try Dem on A + Rep on B
    cost1 = prob_a + rep_b
    cost2 = prob_b + rep_a  # Dem on B + Rep on A

    best_cost = min(cost1, cost2)
    if best_cost < 1.0:
        gross_return = 1.0 - best_cost
        net_return = gross_return - fee_a - fee_b
        if net_return > 0:
            result["arb_type"] = "guaranteed"
            result["guaranteed_return_pct"] = round(net_return * 100, 2)
            if cost1 <= cost2:
                # Buy Dem on A, Rep on B
                denom = 2 - prob_a - rep_b
                sA = (1 - rep_b) / denom if denom > 0 else 0.5
                sB = (1 - prob_a) / denom if denom > 0 else 0.5
                result["stake_a_pct"] = round(sA * 100, 1)
                result["stake_b_pct"] = round(sB * 100, 1)
                result["stake_a_dollars"] = round(sA * 100, 2)
                result["stake_b_dollars"] = round(sB * 100, 2)
                result["profit_dollars"] = round(net_return * 100, 2)
                result["stake_note"] = f"Buy Dem on A ({round(sA*100,1)}% of bankroll) + Buy Rep on B ({round(sB*100,1)}%)"
            else:
                denom = 2 - prob_b - rep_a
                sB = (1 - rep_a) / denom if denom > 0 else 0.5
                sA = (1 - prob_b) / denom if denom > 0 else 0.5
                result["stake_a_pct"] = round(sA * 100, 1)
                result["stake_b_pct"] = round(sB * 100, 1)
                result["stake_a_dollars"] = round(sA * 100, 2)
                result["stake_b_dollars"] = round(sB * 100, 2)
                result["profit_dollars"] = round(net_return * 100, 2)
                result["stake_note"] = f"Buy Rep on A ({round(sA*100,1)}% of bankroll) + Buy Dem on B ({round(sB*100,1)}%)"

    return result


# ── pair builder ──────────────────────────────────────────────────────────────

def make_pair(race_id, label, state, office,
              prob_a, prob_b, platform_a, platform_b,
              prob_a_rep=None, prob_b_rep=None,
              url_a=None, url_b=None,
              extra=None):
    if pd.isna(prob_a) or pd.isna(prob_b):
        return None
    prob_a, prob_b = float(prob_a), float(prob_b)
    raw_gap = abs(prob_a - prob_b)
    net_gap = raw_gap - FEES[platform_a] - FEES[platform_b]

    if prob_a > prob_b:
        action = f"Buy Dem on {platform_b.title()}, Sell Dem on {platform_a.title()}"
        higher = platform_a
    else:
        action = f"Buy Dem on {platform_a.title()}, Sell Dem on {platform_b.title()}"
        higher = platform_b

    arb_math = compute_arb_math(
        prob_a, prob_b,
        float(prob_a_rep) if prob_a_rep is not None and not pd.isna(prob_a_rep) else None,
        float(prob_b_rep) if prob_b_rep is not None and not pd.isna(prob_b_rep) else None,
        FEES[platform_a], FEES[platform_b]
    )

    row = {
        "race_id": race_id,
        "label": label,
        "state": state,
        "office": office,
        "pair": f"{platform_a}/{platform_b}",
        "platform_a": platform_a,
        "platform_b": platform_b,
        f"{platform_a}_dem": round(prob_a, 4),
        f"{platform_b}_dem": round(prob_b, 4),
        "raw_gap_pp": round(raw_gap * 100, 2),
        "net_gap_pp": round(net_gap * 100, 2),
        "profitable": bool(net_gap > 0),
        "suspicious": bool(raw_gap * 100 > 40),
        "higher_platform": higher,
        "action": action,
        "url_a": url_a,
        "url_b": url_b,
        **arb_math,
    }
    if extra:
        row.update(extra)
    return row


# ── primary candidate matching ────────────────────────────────────────────────

import re

_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


_STATE_ABBREVS = set(_STATES.values())


def _extract_state_office(title: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse (state_abbrev, office, district) from a primary market title.

    office ∈ {'SEN', 'GOV', 'H'} or None. district is the zero-padded district
    string for House races, else None. The match is purely textual so it works
    whether or not the scraper tagged a race_id.
    """
    if not isinstance(title, str):
        return (None, None, None)
    t = title.lower()

    # House: "FL-6", "NY-16", "CA-12"
    m = re.search(r"\b([A-Z]{2})[-\s](\d{1,2})\b", title)
    if m and m.group(1) in _STATE_ABBREVS:
        return (m.group(1), "H", str(int(m.group(2))).zfill(2))

    state_ab = None
    for name, abbrev in sorted(_STATES.items(), key=lambda x: -len(x[0])):
        if name in t:
            state_ab = abbrev
            break
    if not state_ab:
        return (None, None, None)

    if "senate" in t or "senator" in t:
        return (state_ab, "SEN", None)
    if "governor" in t or "gubernatorial" in t:
        return (state_ab, "GOV", None)
    # House-without-district fallback
    if "house" in t or "congress" in t:
        return (state_ab, "H", None)
    return (state_ab, None, None)


def _race_id_from(state: str | None, office: str | None, district: str | None) -> str | None:
    if not state or not office:
        return None
    if office == "H":
        if not district:
            return None
        return f"2026-H-{state}-{district}"
    return f"2026-{office}-{state}"


def _canonical_last_name(name: str) -> str | None:
    if not isinstance(name, str):
        return None
    n = re.sub(r"[^\w\s'\-]", " ", name).strip()
    # Drop trailing Jr/Sr/III etc.
    parts = [p for p in n.split() if p.lower() not in ("jr", "sr", "jr.", "sr.", "ii", "iii", "iv")]
    if not parts:
        return None
    return parts[-1].lower()


def _first_initial(name: str) -> str | None:
    """
    First initial of the given name, stripping common prefixes like 'Dr.', 'Mr.',
    and parsing out middle-initial-only forms ('John E. Sununu' -> 'j').
    Used together with last name to disambiguate candidates who share a surname
    (e.g. Chris Sununu vs John E. Sununu).
    """
    if not isinstance(name, str):
        return None
    n = re.sub(r"[^\w\s'\-]", " ", name).strip()
    parts = [p for p in n.split()
             if p.lower() not in ("jr", "sr", "jr.", "sr.", "ii", "iii", "iv",
                                   "dr", "mr", "mrs", "ms", "the", "rep", "sen", "gov")]
    if not parts:
        return None
    return parts[0][0].lower() if parts[0] else None


def load_primary_candidates():
    """
    Build a tidy frame of primary-nominee rows across all three platforms,
    keyed on (state, office, party, candidate_last_name) extracted from the
    market title itself. race_id is derived from the state+office but is not
    required to exist on the source row — that way candidates named in
    untagged markets still get matched.
    """
    rows = []

    # ── Kalshi ──
    # "Will <Name> be the <Party> nominee for the Senate in <State>?"
    # "Will <Name> be the <Party> nominee for FL-6?"
    try:
        k = pd.read_csv(RAW / "kalshi_markets.csv")
    except FileNotFoundError:
        k = pd.DataFrame()
    if not k.empty:
        k = k[k["implied_prob"].notna() & k["market_title"].notna()].copy()
        pat = re.compile(
            r"^Wil[l]?\s+(.+?)\s+be\s+the\s+(Democratic|Republican)\s+nominee",
            re.IGNORECASE,
        )
        for _, r in k.iterrows():
            title = str(r["market_title"])
            m = pat.match(title)
            if not m:
                continue
            name = m.group(1).strip()
            party = "DEM" if m.group(2).lower().startswith("d") else "REP"
            state, office, district = _extract_state_office(title)
            if not state or not office:
                continue
            last = _canonical_last_name(name)
            if not last:
                continue
            rows.append({
                "state": state, "office": office, "district": district,
                "party": party, "candidate_last": last,
                "candidate_first": _first_initial(name),
                "candidate_name": name,
                "platform": "kalshi",
                "prob": float(r["implied_prob"]),
                "url": kalshi_url(r.get("series_ticker")),
                "volume": pd.to_numeric(r.get("volume"), errors="coerce"),
                "oi": pd.to_numeric(r.get("open_interest"), errors="coerce"),
                "raw_title": title,
            })

    # ── PredictIt ──
    # market_name = "Who will win the 2026 <State> <Party> Senate nomination?"
    # contract_name = candidate name
    try:
        pi = pd.read_csv(RAW / "predictit_markets.csv")
    except FileNotFoundError:
        pi = pd.DataFrame()
    if not pi.empty:
        pi = pi[pi["implied_prob"].notna()].copy()
        party_pat = re.compile(r"\b(Democratic|Republican|Democrat|Republicans?)\b", re.IGNORECASE)
        for _, r in pi.iterrows():
            mn = str(r.get("market_name", ""))
            cn = str(r.get("contract_name", ""))
            ml = mn.lower()
            if "nomination" not in ml and "primary" not in ml:
                continue
            pm_ = party_pat.search(mn)
            if not pm_:
                continue
            party = "DEM" if pm_.group(1).lower().startswith("d") else "REP"
            state, office, district = _extract_state_office(mn)
            if not state or not office:
                continue
            # Skip non-candidate contracts like "Any other candidate"
            if cn.lower().strip() in ("any other", "any other candidate", "no nominee", "other"):
                continue
            last = _canonical_last_name(cn)
            if not last:
                continue
            rows.append({
                "state": state, "office": office, "district": district,
                "party": party, "candidate_last": last,
                "candidate_first": _first_initial(cn),
                "candidate_name": cn.strip(),
                "platform": "predictit",
                "prob": float(r["implied_prob"]),
                "url": predictit_url(r.get("market_id")),
                "volume": None, "oi": None,
                "raw_title": f"{mn} — {cn}",
            })

    # ── Polymarket ──
    # "Will <Name> be the <Party> nominee for Senate in <State>?"
    try:
        pm = pd.read_csv(RAW / "polymarket_markets.csv")
    except FileNotFoundError:
        pm = pd.DataFrame()
    if not pm.empty:
        pm = pm[pm["implied_prob"].notna()].copy()
        pat = re.compile(
            r"^Will\s+(.+?)\s+be\s+the\s+(Democratic|Republican)\s+nominee",
            re.IGNORECASE,
        )
        slug_col = "event_slug" if "event_slug" in pm.columns else ("market_slug" if "market_slug" in pm.columns else None)
        for _, r in pm.iterrows():
            title = str(r.get("question", ""))
            m = pat.match(title)
            if not m:
                continue
            name = m.group(1).strip()
            if name.lower().startswith(("any other", "another person", "a candidate not")):
                continue
            party = "DEM" if m.group(2).lower().startswith("d") else "REP"
            state, office, district = _extract_state_office(title)
            if not state or not office:
                continue
            last = _canonical_last_name(name)
            if not last:
                continue
            slug = r.get(slug_col) if slug_col else None
            rows.append({
                "state": state, "office": office, "district": district,
                "party": party, "candidate_last": last,
                "candidate_first": _first_initial(name),
                "candidate_name": name,
                "platform": "polymarket",
                "prob": float(r["implied_prob"]),
                "url": polymarket_url(slug),
                "volume": pd.to_numeric(r.get("volume"), errors="coerce"),
                "oi": pd.to_numeric(r.get("liquidity"), errors="coerce"),
                "raw_title": title,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["race_id"] = df.apply(
            lambda r: _race_id_from(r["state"], r["office"], r["district"]),
            axis=1,
        )
    return df


def primary_pairs(meta_df):
    """
    Cross-platform primary candidate pairs.

    Matching key is (state, office, district, party, candidate_last_name)
    parsed from the title, so candidates get matched even when the source
    platform didn't tag a race_id. race_id is looked up after the match for
    metadata (state name, label, office badge) — it's a guide, not a gate.
    """
    cands = load_primary_candidates()
    if cands.empty:
        return []

    # Dedup: if the same platform lists a candidate in >1 market for the same
    # (state, office, district, party), keep the one with highest volume/OI
    # then highest prob.
    cands["_rank"] = cands[["volume", "oi"]].fillna(0).max(axis=1)
    cands["district"] = cands["district"].fillna("")
    cands["candidate_first"] = cands["candidate_first"].fillna("")
    sort_cols = ["state", "office", "district", "party", "candidate_last", "candidate_first", "platform", "_rank", "prob"]
    cands = cands.sort_values(sort_cols, ascending=[True, True, True, True, True, True, True, False, False])
    dedup_key = ["state", "office", "district", "party", "candidate_last", "candidate_first", "platform"]
    cands = cands.drop_duplicates(subset=dedup_key)

    meta_map = {r["race_id"]: r for _, r in meta_df.iterrows()} if not meta_df.empty else {}

    out = []
    # Match on first initial + last name to disambiguate same-surname candidates
    # like Chris Sununu vs John E. Sununu.
    key_cols = ["state", "office", "district", "party", "candidate_last", "candidate_first"]
    for key, grp in cands.groupby(key_cols):
        if len(grp) < 2:
            continue
        platforms = grp.set_index("platform")
        available = list(platforms.index)
        for i, pa in enumerate(available):
            for pb in available[i + 1:]:
                ra = platforms.loc[pa]
                rb = platforms.loc[pb]
                prob_a = float(ra["prob"])
                prob_b = float(rb["prob"])
                raw_gap = abs(prob_a - prob_b)
                net_gap = raw_gap - FEES.get(pa, 0.03) - FEES.get(pb, 0.03)
                cheaper = pa if prob_a < prob_b else pb
                expensive = pb if prob_a < prob_b else pa
                action = f"Buy {ra['candidate_name']} on {cheaper.title()} ({min(prob_a, prob_b)*100:.1f}%), fade on {expensive.title()} ({max(prob_a, prob_b)*100:.1f}%)"
                state, office, district, party, last, first = key
                rid = _race_id_from(state, office, district or None)
                meta = meta_map.get(rid, {}) if rid else {}
                if isinstance(meta, dict):
                    label = meta.get("label") or (rid or f"{state} {office}")
                    state_name = meta.get("state", state)
                else:
                    label = getattr(meta, "label", None) or (rid or f"{state} {office}")
                    state_name = getattr(meta, "state", state)
                out.append({
                    "match_type": "primary_candidate",
                    "race_id": rid,
                    "label": label,
                    "state": state_name,
                    "office": office,
                    "party": party,
                    "candidate": ra["candidate_name"],
                    "pair": f"{pa}/{pb}",
                    "platform_a": pa,
                    "platform_b": pb,
                    f"{pa}_dem": round(prob_a, 4),
                    f"{pb}_dem": round(prob_b, 4),
                    "prob_a": round(prob_a, 4),
                    "prob_b": round(prob_b, 4),
                    "raw_gap_pp": round(raw_gap * 100, 2),
                    "net_gap_pp": round(net_gap * 100, 2),
                    "profitable": bool(net_gap > 0),
                    "suspicious": bool(raw_gap * 100 > 40),
                    "higher_platform": expensive,
                    "action": action,
                    "arb_type": "one-sided",
                    "guaranteed_return_pct": None,
                    "stake_a_pct": None, "stake_b_pct": None,
                    "stake_a_dollars": None, "stake_b_dollars": None,
                    "profit_dollars": None, "stake_note": None,
                    "url_a": ra.get("url"), "url_b": rb.get("url"),
                    "volume_a": None if pd.isna(ra.get("volume")) else float(ra.get("volume")),
                    "volume_b": None if pd.isna(rb.get("volume")) else float(rb.get("volume")),
                    "question_a": ra.get("raw_title", ""),
                    "question_b": rb.get("raw_title", ""),
                })
    return out


# ── main ──────────────────────────────────────────────────────────────────────

def run():
    print("Loading markets...")
    kalshi = load_kalshi_general()
    pi = load_predictit_general()
    pm = load_polymarket_general()
    meta = get_race_meta()

    print(f"  Kalshi: {len(kalshi)} races")
    print(f"  PredictIt: {len(pi)} races")
    print(f"  Polymarket: {len(pm)} races")

    def add_meta(df):
        return df.merge(meta, on="race_id", how="left")

    kalshi = add_meta(kalshi)
    pi = add_meta(pi)
    pm = add_meta(pm) if not pm.empty else pm

    rows = []

    # ── Kalshi vs PredictIt ──
    kpi = kalshi.merge(pi, on="race_id", how="inner")
    for _, r in kpi.iterrows():
        row = make_pair(
            r["race_id"], r.get("label", r["race_id"]), r.get("state", ""), r.get("office", ""),
            r.get("kalshi_dem"), r.get("pi_dem"),
            "kalshi", "predictit",
            prob_a_rep=r.get("kalshi_rep"), prob_b_rep=r.get("pi_rep"),
            url_a=r.get("kalshi_url"), url_b=r.get("pi_url"),
            extra={
                "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell"),
                "kalshi_oi": r.get("kalshi_oi"),
                "volume_a": r.get("kalshi_volume"), "volume_b": None,  # PredictIt: no volume API
            },
        )
        if row:
            rows.append(row)

    # ── Kalshi vs Polymarket ──
    if not pm.empty and "pm_dem" in pm.columns:
        kpm = kalshi.merge(pm, on="race_id", how="inner")
        for _, r in kpm.iterrows():
            row = make_pair(
                r["race_id"], r.get("label", r["race_id"]), r.get("state", ""), r.get("office", ""),
                r.get("kalshi_dem"), r.get("pm_dem"),
                "kalshi", "polymarket",
                prob_a_rep=r.get("kalshi_rep"), prob_b_rep=r.get("pm_rep"),
                url_a=r.get("kalshi_url"), url_b=r.get("pm_url"),
                extra={
                    "pm_liq": r.get("pm_liq"), "kalshi_oi": r.get("kalshi_oi"),
                    "volume_a": r.get("kalshi_volume"), "volume_b": r.get("pm_volume"),
                },
            )
            if row:
                rows.append(row)

    # ── PredictIt vs Polymarket ──
    if not pm.empty and "pm_dem" in pm.columns:
        pipm = pi.merge(pm, on="race_id", how="inner")
        for _, r in pipm.iterrows():
            row = make_pair(
                r["race_id"], r.get("label", r["race_id"]), r.get("state", ""), r.get("office", ""),
                r.get("pi_dem"), r.get("pm_dem"),
                "predictit", "polymarket",
                prob_a_rep=r.get("pi_rep"), prob_b_rep=r.get("pm_rep"),
                url_a=r.get("pi_url"), url_b=r.get("pm_url"),
                extra={
                    "pm_liq": r.get("pm_liq"),
                    "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell"),
                    "volume_a": None, "volume_b": r.get("pm_volume"),
                },
            )
            if row:
                rows.append(row)

    # Tag general-election pairs, then append primary-candidate pairs.
    for row in rows:
        row.setdefault("match_type", "general")

    prim = primary_pairs(meta)
    print(f"\nPrimary candidate cross-platform pairs: {len(prim)}")
    if prim:
        top = sorted(prim, key=lambda r: -r["raw_gap_pp"])[:10]
        print("Top primary candidate gaps:")
        for r in top:
            print(f"  {r['pair']:>22}  {r['candidate']:20} {r['label']:14} "
                  f"gap={r['raw_gap_pp']:5.1f}pp  "
                  f"{r['platform_a']}={r['prob_a']*100:5.1f}%  {r['platform_b']}={r['prob_b']*100:5.1f}%")
    rows.extend(prim)

    arb = pd.DataFrame(rows).sort_values(["arb_type", "raw_gap_pp"], ascending=[True, False])

    # Volume is exposed in JSON so the dashboard can filter live.
    arb["volume_a"] = pd.to_numeric(arb.get("volume_a"), errors="coerce")
    arb["volume_b"] = pd.to_numeric(arb.get("volume_b"), errors="coerce")

    guaranteed = arb[arb["arb_type"] == "guaranteed"]
    profitable = arb[arb["profitable"]]
    print(f"\nTotal cross-market pairs: {len(arb)}")
    print(f"Guaranteed arb (after fees): {len(guaranteed)}")
    print(f"Profitable one-sided (after fees): {len(profitable[profitable['arb_type']=='one-sided'])}")
    if not guaranteed.empty:
        print("\nGuaranteed arb opportunities:")
        print(guaranteed[["pair", "label", "raw_gap_pp", "guaranteed_return_pct", "stake_note"]].to_string(index=False))

    def clean(v):
        if isinstance(v, float) and np.isnan(v):
            return None
        return v

    records = [{k: clean(v) for k, v in row.items()} for row in arb.to_dict(orient="records")]

    out = ROOT / "docs" / "arb_data.js"
    with open(out, "w") as f:
        f.write("const ARB = ")
        json.dump({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "fees": FEES,
            "races": records,
        }, f, separators=(",", ":"))
        f.write(";")
    print(f"\nWrote {len(records)} pairs to docs/arb_data.js")


if __name__ == "__main__":
    run()
