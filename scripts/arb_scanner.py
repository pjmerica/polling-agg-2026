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
    "kalshi":    0.07,
    "predictit": 0.15,
    "polymarket": 0.02,
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

def polymarket_url(condition_id):
    if pd.isna(condition_id) or not condition_id:
        return None
    return f"https://polymarket.com/event/{condition_id}"


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
        return g.loc[idx, ["implied_prob", "open_interest", "series_ticker", "market_title"]]

    dem = df[dem_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    dem = dem.rename(columns={
        "implied_prob": "kalshi_dem",
        "open_interest": "kalshi_oi",
        "series_ticker": "kalshi_series_ticker",
    })

    rep = df[rep_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    rep = rep.rename(columns={"implied_prob": "kalshi_rep", "series_ticker": "kalshi_rep_ticker"})

    merged = dem[["race_id", "kalshi_dem", "kalshi_oi", "kalshi_series_ticker"]].merge(
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

    dem = df[df["is_dem"]][["race_id", "implied_prob", "liquidity", "condition_id"]].copy()
    rep = df[df["is_rep"]][["race_id", "implied_prob", "liquidity", "condition_id"]].copy()

    def best_liq(g):
        liq = pd.to_numeric(g["liquidity"], errors="coerce").fillna(0)
        return g.loc[liq.idxmax()]

    if not dem.empty:
        dem = dem.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        dem = dem.rename(columns={"implied_prob": "pm_dem", "liquidity": "pm_liq", "condition_id": "pm_dem_condition"})

    if not rep.empty:
        rep = rep.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        rep = rep.rename(columns={"implied_prob": "pm_rep", "liquidity": "pm_rep_liq", "condition_id": "pm_rep_condition"})

    if dem.empty and rep.empty:
        return pd.DataFrame()

    result = dem[["race_id", "pm_dem", "pm_liq", "pm_dem_condition"]] if not dem.empty \
        else pd.DataFrame(columns=["race_id", "pm_dem", "pm_liq", "pm_dem_condition"])
    if not rep.empty:
        result = result.merge(rep[["race_id", "pm_rep", "pm_rep_condition"]], on="race_id", how="outer")

    result["pm_url"] = result["pm_dem_condition"].apply(polymarket_url)
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
        "higher_platform": higher,
        "action": action,
        "url_a": url_a,
        "url_b": url_b,
        **arb_math,
    }
    if extra:
        row.update(extra)
    return row


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
            extra={"pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell"), "kalshi_oi": r.get("kalshi_oi")},
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
                extra={"pm_liq": r.get("pm_liq"), "kalshi_oi": r.get("kalshi_oi")},
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
                extra={"pm_liq": r.get("pm_liq"), "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell")},
            )
            if row:
                rows.append(row)

    arb = pd.DataFrame(rows).sort_values(["arb_type", "raw_gap_pp"], ascending=[True, False])

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
