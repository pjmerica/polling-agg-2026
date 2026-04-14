"""
Cross-market arbitrage scanner.

Compares implied probabilities for the same event across Kalshi, PredictIt,
and Polymarket. Flags gaps that exceed a threshold after estimated fees.

Fee assumptions:
  Kalshi:    ~7% round-trip (maker/taker on entry + exit)
  PredictIt: ~10% on profits + 5% on withdrawal -> ~15% effective round-trip
  Polymarket: ~2% round-trip (low fee CLOB)

Output: docs/arb_data.js
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

# Effective round-trip fee per platform (rough estimate)
FEES = {
    "kalshi":    0.07,
    "predictit": 0.15,
    "polymarket": 0.02,
}


def load_kalshi_general():
    """
    Extract Kalshi Democrat/Republican win probabilities per race.
    Use the highest open_interest market for each race+party.
    """
    path = RAW / "kalshi_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()

    # Identify party from title
    dem_mask = df["market_title"].str.contains(
        r"Democrat(?:ic)?s?\s+win|Will Democrat(?:ic)?s?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)
    rep_mask = df["market_title"].str.contains(
        r"Republican(?:s)?\s+win|Will Republican(?:s)?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)

    dem = df[dem_mask].copy()
    rep = df[rep_mask].copy()

    def best(g):
        oi = pd.to_numeric(g["open_interest"], errors="coerce").fillna(0)
        idx = oi.idxmax()
        return g.loc[idx, ["implied_prob", "open_interest", "market_title"]]

    dem_agg = dem.groupby("race_id").apply(best, include_groups=False).reset_index()
    dem_agg = dem_agg.rename(columns={"implied_prob": "kalshi_dem", "open_interest": "kalshi_oi_dem", "market_title": "kalshi_title_dem"})

    rep_agg = rep.groupby("race_id").apply(best, include_groups=False).reset_index()
    rep_agg = rep_agg.rename(columns={"implied_prob": "kalshi_rep", "open_interest": "kalshi_oi_rep", "market_title": "kalshi_title_rep"})

    merged = dem_agg.merge(rep_agg, on="race_id", how="outer")
    merged["source"] = "kalshi"
    return merged


def load_predictit_general():
    """
    Extract PredictIt Democrat/Republican implied probs per race.
    PredictIt contract_name is 'Democratic' or 'Republican'.
    """
    path = RAW / "predictit_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()

    # Only party-level general election contracts (not candidate-specific)
    party_mask = df["contract_name"].str.strip().isin(["Democratic", "Republican"])
    df = df[party_mask].copy()

    dem = df[df["contract_name"].str.strip() == "Democratic"][["race_id", "implied_prob", "best_buy_yes", "best_sell_yes"]].copy()
    rep = df[df["contract_name"].str.strip() == "Republican"][["race_id", "implied_prob", "best_buy_yes", "best_sell_yes"]].copy()

    dem = dem.rename(columns={"implied_prob": "pi_dem", "best_buy_yes": "pi_dem_buy", "best_sell_yes": "pi_dem_sell"})
    rep = rep.rename(columns={"implied_prob": "pi_rep", "best_buy_yes": "pi_rep_buy", "best_sell_yes": "pi_rep_sell"})

    merged = dem.merge(rep, on="race_id", how="outer")
    merged["source"] = "predictit"
    return merged


def get_race_meta():
    """Load race metadata from utils/races.py."""
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


def compute_arb_opportunities(combined):
    """
    For each race with both Kalshi and PredictIt data, compute:
      - raw gap: abs(kalshi_dem - pi_dem)
      - net gap after fees: raw_gap - (kalshi_fee + pi_fee)
      - which side to buy/sell for each platform
    """
    rows = []
    for _, r in combined.iterrows():
        k_dem = r.get("kalshi_dem")
        pi_dem = r.get("pi_dem")
        k_rep = r.get("kalshi_rep")
        pi_rep = r.get("pi_rep")

        if pd.isna(k_dem) or pd.isna(pi_dem):
            continue

        raw_gap = abs(k_dem - pi_dem)
        net_gap = round(raw_gap - FEES["kalshi"] - FEES["predictit"], 4)

        # Direction
        if k_dem > pi_dem:
            action = "Buy Dem on PredictIt, Sell Dem (Buy Rep) on Kalshi"
            direction = "kalshi_higher"
        else:
            action = "Buy Dem on Kalshi, Sell Dem (Buy Rep) on PredictIt"
            direction = "pi_higher"

        rows.append({
            "race_id": r["race_id"],
            "state": r.get("state", ""),
            "state_abbrev": r.get("state_abbrev", ""),
            "office": r.get("office", ""),
            "label": r.get("label", r["race_id"]),
            "kalshi_dem": round(float(k_dem), 4),
            "kalshi_rep": round(float(k_rep), 4) if not pd.isna(k_rep) else None,
            "pi_dem": round(float(pi_dem), 4),
            "pi_rep": round(float(pi_rep), 4) if not pd.isna(pi_rep) else None,
            "pi_dem_buy": round(float(r["pi_dem_buy"]), 4) if not pd.isna(r.get("pi_dem_buy", float("nan"))) else None,
            "pi_dem_sell": round(float(r["pi_dem_sell"]), 4) if not pd.isna(r.get("pi_dem_sell", float("nan"))) else None,
            "raw_gap_pp": round(raw_gap * 100, 2),
            "net_gap_pp": round(net_gap * 100, 2),
            "profitable": bool(net_gap > 0),
            "direction": direction,
            "action": action,
            "kalshi_oi": r.get("kalshi_oi_dem"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    return pd.DataFrame(rows)


def run():
    print("Loading Kalshi general election markets...")
    kalshi = load_kalshi_general()
    print(f"  {len(kalshi)} races with Kalshi party probs")

    print("Loading PredictIt general election markets...")
    pi = load_predictit_general()
    print(f"  {len(pi)} races with PredictIt party probs")

    meta = get_race_meta()

    # Merge all on race_id
    combined = kalshi.merge(pi, on="race_id", how="inner")
    combined = combined.merge(meta, on="race_id", how="left")
    print(f"  {len(combined)} races with data on both platforms")

    arb = compute_arb_opportunities(combined)
    arb = arb.sort_values("raw_gap_pp", ascending=False)

    profitable = arb[arb["profitable"]]
    print(f"\nPotentially profitable after fees: {len(profitable)} / {len(arb)} races")
    if not profitable.empty:
        print(profitable[["label", "kalshi_dem", "pi_dem", "raw_gap_pp", "net_gap_pp", "action"]].to_string(index=False))

    print(f"\nAll gaps (top 20):")
    print(arb[["label", "kalshi_dem", "pi_dem", "raw_gap_pp", "net_gap_pp"]].head(20).to_string(index=False))

    # Write JS data file
    out = ROOT / "docs" / "arb_data.js"
    records = arb.to_dict(orient="records")
    # Clean NaN for JSON
    def clean(v):
        if isinstance(v, float) and np.isnan(v):
            return None
        return v
    records = [{k: clean(v) for k, v in row.items()} for row in records]

    with open(out, "w") as f:
        f.write("const ARB = ")
        json.dump({
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "fees": FEES,
            "races": records,
        }, f, separators=(",", ":"))
        f.write(";")
    print(f"\nWrote {len(records)} races to docs/arb_data.js")


if __name__ == "__main__":
    run()
