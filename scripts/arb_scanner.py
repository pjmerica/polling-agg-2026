"""
Cross-market arbitrage scanner.

Compares implied probabilities for the same event across Kalshi, PredictIt,
and Polymarket. Flags gaps that exceed a threshold after estimated fees.

Fee assumptions (round-trip):
  Kalshi:    ~7%  (maker/taker on entry + exit)
  PredictIt: ~15% (10% on profits + 5% withdrawal)
  Polymarket: ~2% (low-fee CLOB)

Output: docs/arb_data.js — array of {pair, race_id, label, prob_a, prob_b, raw_gap_pp, net_gap_pp, profitable, action}
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

FEES = {
    "kalshi":    0.07,
    "predictit": 0.15,
    "polymarket": 0.02,
}


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
        return g.loc[idx, ["implied_prob", "open_interest", "market_title"]]

    dem = df[dem_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    dem = dem.rename(columns={"implied_prob": "kalshi_dem", "open_interest": "kalshi_oi"})

    rep = df[rep_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    rep = rep.rename(columns={"implied_prob": "kalshi_rep"})

    return dem[["race_id", "kalshi_dem", "kalshi_oi"]].merge(
        rep[["race_id", "kalshi_rep"]], on="race_id", how="outer"
    )


def load_predictit_general():
    """Democratic/Republican party contracts per race."""
    path = RAW / "predictit_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df = df[df["contract_name"].str.strip().isin(["Democratic", "Republican"])].copy()

    dem = df[df["contract_name"].str.strip() == "Democratic"][
        ["race_id", "implied_prob", "best_buy_yes", "best_sell_yes"]
    ].rename(columns={"implied_prob": "pi_dem", "best_buy_yes": "pi_dem_buy", "best_sell_yes": "pi_dem_sell"})

    rep = df[df["contract_name"].str.strip() == "Republican"][
        ["race_id", "implied_prob"]
    ].rename(columns={"implied_prob": "pi_rep"})

    return dem.merge(rep, on="race_id", how="outer")


def load_polymarket_general():
    """
    Polymarket Yes prices for Democrat/Republican win questions.
    For 'Will Democrats win X' -> dem prob = implied_prob (Yes price).
    For 'Will Republicans win X' -> rep prob = implied_prob.
    We prefer the Dem-framed question when available.
    """
    path = RAW / "polymarket_markets.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)

    # Parse implied_prob from prices field (stored as JSON-like string)
    def parse_prob(row):
        try:
            prices_raw = str(row.get("prices", ""))
            # Strip brackets and split on comma
            prices_raw = prices_raw.strip("[]").replace('"', "").replace("'", "")
            parts = [p.strip() for p in prices_raw.split(",")]
            outcomes_raw = str(row.get("outcomes", ""))
            outcomes_raw = outcomes_raw.strip("[]").replace('"', "").replace("'", "")
            outcomes = [o.strip() for o in outcomes_raw.split(",")]
            pairs = dict(zip(outcomes, [float(p) for p in parts]))
            if "Yes" in pairs:
                return pairs["Yes"]
            for k, v in pairs.items():
                if k.lower() != "no":
                    return v
        except Exception:
            pass
        return None

    if "implied_prob" not in df.columns or df["implied_prob"].isna().all():
        df["implied_prob"] = df.apply(parse_prob, axis=1)

    if "race_id" not in df.columns:
        return pd.DataFrame()

    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df["implied_prob"] = pd.to_numeric(df["implied_prob"], errors="coerce")
    df = df.dropna(subset=["implied_prob"])

    # Classify as dem or rep question
    q = df["question"].str.lower()
    df["is_dem"] = q.str.contains(r"democrat|democratic", na=False) & ~q.str.contains(r"republican", na=False)
    df["is_rep"] = q.str.contains(r"republican", na=False) & ~q.str.contains(r"democrat|democratic", na=False)

    # Keep only general win questions (not nominee/primary)
    df = df[~q.str.contains("nominee|primary|nominate|advance", na=False)]

    dem = df[df["is_dem"]][["race_id", "implied_prob", "liquidity"]].copy()
    rep = df[df["is_rep"]][["race_id", "implied_prob", "liquidity"]].copy()

    # Best by liquidity per race
    def best_liq(g):
        liq = pd.to_numeric(g["liquidity"], errors="coerce").fillna(0)
        return g.loc[liq.idxmax()]

    if not dem.empty:
        dem = dem.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        dem = dem.rename(columns={"implied_prob": "pm_dem", "liquidity": "pm_liq"})

    if not rep.empty:
        rep = rep.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        rep = rep.rename(columns={"implied_prob": "pm_rep", "liquidity": "pm_rep_liq"})

    if dem.empty and rep.empty:
        return pd.DataFrame()

    result = dem[["race_id", "pm_dem", "pm_liq"]] if not dem.empty else pd.DataFrame(columns=["race_id", "pm_dem", "pm_liq"])
    if not rep.empty:
        result = result.merge(rep[["race_id", "pm_rep"]], on="race_id", how="outer")
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


# ── arb computation ───────────────────────────────────────────────────────────

def make_pair(race_id, label, state, office,
              prob_a, prob_b, platform_a, platform_b,
              extra=None):
    """Generate one arb row for a pair of platforms."""
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
        "higher_platform": higher,
        "action": action,
    }
    if extra:
        row.update(extra)
    return row


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
            extra={
                "pi_dem_buy": r.get("pi_dem_buy"),
                "pi_dem_sell": r.get("pi_dem_sell"),
                "kalshi_oi": r.get("kalshi_oi"),
            }
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
                extra={"pm_liq": r.get("pm_liq"), "kalshi_oi": r.get("kalshi_oi")}
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
                extra={"pm_liq": r.get("pm_liq"), "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell")}
            )
            if row:
                rows.append(row)

    arb = pd.DataFrame(rows).sort_values("raw_gap_pp", ascending=False)

    profitable = arb[arb["profitable"]]
    print(f"\nTotal cross-market pairs: {len(arb)}")
    print(f"Profitable after fees: {len(profitable)}")
    if not profitable.empty:
        print(profitable[["pair", "label", "raw_gap_pp", "net_gap_pp", "action"]].to_string(index=False))

    print(f"\nTop 20 gaps:")
    print(arb[["pair", "label", "raw_gap_pp", "net_gap_pp"]].head(20).to_string(index=False))

    # Write JS
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
