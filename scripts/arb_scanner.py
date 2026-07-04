"""
Cross-market arbitrage scanner.

Compares implied probabilities for the same event across Kalshi, PredictIt,
and Polymarket. Flags gaps after estimated fees and computes guaranteed arb
stake ratios where applicable.

Fee assumptions (round-trip): see the FEES dict below — it is the single
source of truth (currently Kalshi 2%, Polymarket 2%, PredictIt 12%).

Arb types:
  guaranteed — Buy YES on one platform + Buy NO on the other for a combined
               cost < $1 after fees, using REAL fillable quotes on both
               legs (ask for the YES leg, NO-ask for the NO leg).
               Locked profit regardless of outcome.

  one-sided  — same outcome priced differently across platforms, but no
               real-quote basket clears fees. You're just getting a better
               price; outcome is still uncertain.

Output: docs/arb_data.js
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"


def _safe_read_csv(path, **kw):
    """Read a CSV defensively. Returns an empty DataFrame if the file is
    missing, zero-byte, or has no columns. Lets the pipeline survive
    transient scraper outages (Kalshi/Polymarket APIs occasionally return
    nothing) without crashing the whole scanner."""
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, **kw)
    except pd.errors.EmptyDataError:
        print(f"  WARNING: {path.name} is empty — treating as no data")
        return pd.DataFrame()

FEES = {
    # Conservative round-trip fee approximation per platform.
    # Kalshi taker fee tops out around 1% each way; Polymarket gas + fee
    # tops out around 1% each way; using 2% per platform leaves a cushion
    # against slippage without burying real arbs under fake-fee math.
    # PredictIt charges 5% on profits + 5% on withdrawals = 12% effective
    # round-trip on profitable trades; left as-is.
    "kalshi":    0.02,
    "predictit": 0.12,
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

def polymarket_url(slug):
    if pd.isna(slug) or not slug:
        return None
    return f"https://polymarket.com/event/{slug}"


# ── loaders ──────────────────────────────────────────────────────────────────

def load_kalshi_general():
    """Dem/Rep win prob per race — pick highest open_interest market per race+party."""
    df = _safe_read_csv(RAW / "kalshi_markets.csv")
    if df.empty or "race_id" not in df.columns or "implied_prob" not in df.columns:
        return pd.DataFrame()
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()

    dem_mask = df["market_title"].str.contains(
        r"Democrat(?:ic)?s?\s+win|Will Democrat(?:ic)?s?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)
    rep_mask = df["market_title"].str.contains(
        r"Republican(?:s)?\s+win|Will Republican(?:s)?\s+win", case=False, na=False
    ) & ~df["market_title"].str.contains("nominee|primary|nominate", case=False, na=False)

    cols = ["implied_prob", "open_interest", "volume", "series_ticker", "market_ticker", "market_title",
            "yes_bid", "yes_ask", "close_time"]
    if "market_ticker" not in df.columns:
        df["market_ticker"] = None
    for c in ("yes_bid", "yes_ask", "close_time", "expected_expiration_time"):
        if c not in df.columns:
            df[c] = None
    # Kalshi's close_time is a safety buffer (often a year past the event);
    # expected_expiration_time is when they actually expect to settle
    # (e.g. 2027-01-04 for 2026 House races — when Congress is seated).
    # Prefer it so days_to_settle / annualized returns aren't understated.
    df["close_time"] = df["expected_expiration_time"].where(
        df["expected_expiration_time"].notna(), df["close_time"]
    )

    def best(g):
        oi = pd.to_numeric(g["open_interest"], errors="coerce").fillna(0)
        idx = oi.idxmax()
        return g.loc[idx, cols]

    dem = df[dem_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    dem = dem.rename(columns={
        "implied_prob": "kalshi_dem",
        "open_interest": "kalshi_oi",
        "volume": "kalshi_volume",
        "series_ticker": "kalshi_series_ticker",
        "market_ticker": "kalshi_dem_ticker",
        "yes_bid": "kalshi_dem_bid",
        "yes_ask": "kalshi_dem_ask",
        "close_time": "kalshi_close_time",
    })

    rep = df[rep_mask].groupby("race_id").apply(best, include_groups=False).reset_index()
    rep = rep.rename(columns={
        "implied_prob": "kalshi_rep",
        "series_ticker": "kalshi_rep_series",
        "market_ticker": "kalshi_rep_ticker",
    })

    merged = dem[["race_id", "kalshi_dem", "kalshi_oi", "kalshi_volume", "kalshi_series_ticker",
                  "kalshi_dem_ticker", "kalshi_dem_bid", "kalshi_dem_ask", "kalshi_close_time"]].merge(
        rep[["race_id", "kalshi_rep", "kalshi_rep_ticker"]], on="race_id", how="inner"
    )
    merged["kalshi_url"] = merged["kalshi_series_ticker"].apply(kalshi_url)
    return merged


def load_predictit_general():
    """Democratic/Republican party contracts per race."""
    df = _safe_read_csv(RAW / "predictit_markets.csv")
    if df.empty or "race_id" not in df.columns or "implied_prob" not in df.columns:
        return pd.DataFrame()
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df = df[df["contract_name"].str.strip().isin(["Democratic", "Republican"])].copy()
    for c in ("best_buy_no", "date_end"):
        if c not in df.columns:
            df[c] = None

    dem = df[df["contract_name"].str.strip() == "Democratic"][
        ["race_id", "implied_prob", "best_buy_yes", "best_sell_yes", "best_buy_no", "date_end", "market_id"]
    ].rename(columns={"implied_prob": "pi_dem", "best_buy_yes": "pi_dem_buy",
                      "best_sell_yes": "pi_dem_sell", "best_buy_no": "pi_dem_buy_no",
                      "date_end": "pi_date_end"})

    rep = df[df["contract_name"].str.strip() == "Republican"][
        ["race_id", "implied_prob"]
    ].rename(columns={"implied_prob": "pi_rep"})

    merged = dem.merge(rep, on="race_id", how="outer")
    merged["pi_url"] = merged["market_id"].apply(predictit_url)
    return merged


def load_polymarket_general():
    """Polymarket Yes prices for Democrat/Republican win questions."""
    df = _safe_read_csv(RAW / "polymarket_markets.csv", dtype={"yes_token_id": str, "no_token_id": str})
    if df.empty or "race_id" not in df.columns:
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

    for c in ("yes_token_id", "no_token_id", "best_bid", "best_ask", "end_date"):
        if c not in df.columns:
            df[c] = None

    keep = ["race_id", "implied_prob", "liquidity", "volume", "_slug", "yes_token_id",
            "no_token_id", "best_bid", "best_ask", "end_date"]
    dem = df[df["is_dem"]][keep].copy()
    rep = df[df["is_rep"]][keep].copy()

    def best_liq(g):
        liq = pd.to_numeric(g["liquidity"], errors="coerce").fillna(0)
        return g.loc[liq.idxmax()]

    if not dem.empty:
        dem = dem.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        dem = dem.rename(columns={
            "implied_prob": "pm_dem", "liquidity": "pm_liq",
            "volume": "pm_volume", "_slug": "pm_dem_slug",
            "yes_token_id": "pm_dem_token", "no_token_id": "pm_dem_no_token",
            "best_bid": "pm_dem_bid", "best_ask": "pm_dem_ask",
            "end_date": "pm_end_date",
        })

    if not rep.empty:
        rep = rep.groupby("race_id").apply(best_liq, include_groups=False).reset_index()
        rep = rep.rename(columns={
            "implied_prob": "pm_rep", "liquidity": "pm_rep_liq",
            "_slug": "pm_rep_slug", "yes_token_id": "pm_rep_token",
        })

    if dem.empty and rep.empty:
        return pd.DataFrame()

    dem_cols = ["race_id", "pm_dem", "pm_liq", "pm_volume", "pm_dem_slug", "pm_dem_token",
                "pm_dem_no_token", "pm_dem_bid", "pm_dem_ask", "pm_end_date"]
    result = dem[dem_cols] if not dem.empty else pd.DataFrame(columns=dem_cols)
    if not rep.empty:
        result = result.merge(rep[["race_id", "pm_rep", "pm_rep_slug", "pm_rep_token"]], on="race_id", how="outer")

    # Require both Dem and Rep markets to be explicitly priced. Earlier
    # versions filled missing sides with 1 - other_side, but those inferred
    # prices aren't actually tradeable — they describe the implied no
    # probability, not a fillable yes ask on a real Polymarket book. The
    # arb scanner should only surface pairs where both legs are real.
    if "pm_rep" in result.columns:
        result = result[result["pm_dem"].notna() & result["pm_rep"].notna()].copy()
    else:
        result = result.iloc[0:0].copy()

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
#
# Ported from pred-arbitrage scripts/arb_scanner.py:compute_arb on 2026-07-03,
# replacing the old midpoint-based compute_arb_math. See
# AGENT_EXECUTION_NOTES.md Findings 1+2 for the full rationale. Key changes:
#
#   1. The basket is now YES + NO on the SAME question across platforms
#      (Buy Dem-YES on cheap platform + Buy Dem-NO on expensive platform).
#      A binary market's YES/NO is a complete 2-state partition, so the old
#      safe_rep() cross-flip guard (3-way-race protection for Dem-YES vs
#      Rep-YES baskets) is no longer needed — Rep prices are display-only.
#      This is NOT the banned "inferred-complement" pattern from HANDOFF's
#      Do-not list: that inferred a PRICE (1 - other side's midpoint) and
#      pretended it was fillable. Here the NO leg is a real, separately
#      quoted contract (Kalshi NO side / Polymarket NO token / PredictIt
#      Buy-No quote) and we only claim "guaranteed" when the winning
#      direction used real quotes on both legs.
#
#   2. Two price layers. DISPLAY (prob_a/prob_b = implied_prob) feeds
#      raw_gap_pp / net_gap_pp only. FILLABLE (bid/ask/no_ask kwargs)
#      feeds the basket math. Midpoints never enter the cost calc unless
#      a leg has no quote data at all (then that direction can't be
#      classified guaranteed anyway).

def compute_arb(prob_a, prob_b, fee_a, fee_b,
                bid_a=None, ask_a=None, bid_b=None, ask_b=None,
                no_ask_a=None, no_ask_b=None,
                no_ask_a_real=False, no_ask_b_real=False):
    """
    Returns arb type, guaranteed return, and stake ratios for the basket
    Buy YES on one platform + Buy NO on the other.

    no_ask_a/no_ask_b: price to BUY the NO side on that platform.
      - Kalshi: 1 - yes_bid is EXACT (unified book: buying NO at 1-p fills
        against the resting YES bid at p) — pass it with no_ask_real=True.
      - Polymarket: gamma has no NO quote; pass the real NO-token book ask
        when fetch_depth got it (real=True), else leave None and we infer
        1 - bid (approximate, real=False).
      - PredictIt: bestBuyNoCost is a real quote — pass real=True.

    arb_type stays binary ("guaranteed" / "one-sided") for dashboard
    compatibility. "guaranteed" requires the winning direction to have
    used REAL quotes on both legs AND clear both platforms' fees.
    """
    prob_a, prob_b = float(prob_a), float(prob_b)

    yes_a_real = bid_a is not None and not pd.isna(bid_a) and bid_a > 0 \
        and ask_a is not None and not pd.isna(ask_a) and ask_a > 0
    yes_b_real = bid_b is not None and not pd.isna(bid_b) and bid_b > 0 \
        and ask_b is not None and not pd.isna(ask_b) and ask_b > 0
    no_a_real = bool(no_ask_a_real) and no_ask_a is not None and not pd.isna(no_ask_a) and no_ask_a > 0
    no_b_real = bool(no_ask_b_real) and no_ask_b is not None and not pd.isna(no_ask_b) and no_ask_b > 0

    # Fallbacks (approximate — only used when real data is missing, and a
    # direction built on them can never be classified "guaranteed").
    bid_a_f = bid_a if yes_a_real else prob_a
    ask_a_f = ask_a if yes_a_real else prob_a
    bid_b_f = bid_b if yes_b_real else prob_b
    ask_b_f = ask_b if yes_b_real else prob_b
    no_ask_a_f = no_ask_a if (no_ask_a is not None and not pd.isna(no_ask_a) and no_ask_a > 0) \
        else max(0.001, 1 - bid_a_f)
    no_ask_b_f = no_ask_b if (no_ask_b is not None and not pd.isna(no_ask_b) and no_ask_b > 0) \
        else max(0.001, 1 - bid_b_f)

    result = {
        "arb_type": "one-sided",
        "guaranteed_return_pct": None,
        "stake_a_pct": None,
        "stake_b_pct": None,
        "stake_a_dollars": None,
        "stake_b_dollars": None,
        "profit_dollars": None,
        "stake_note": None,
        # Audit fields: what you'd actually pay, and whether it's live data.
        "fillable_ask_a": round(ask_a_f, 4),
        "fillable_ask_b": round(ask_b_f, 4),
        "fillable_no_ask_a": round(no_ask_a_f, 4),
        "fillable_no_ask_b": round(no_ask_b_f, 4),
        "arb_uses_live_book": bool(yes_a_real or yes_b_real),
    }

    # Direction 1: Buy YES on A + Buy NO on B. Direction 2: the reverse.
    directions = [
        (ask_a_f, no_ask_b_f, "a", "b", yes_a_real and no_b_real),
        (ask_b_f, no_ask_a_f, "b", "a", yes_b_real and no_a_real),
    ]
    # Floor: a "guaranteed" arb returning less than 0.25% net is noise —
    # a rounding artifact of the fee model, not a trade (10c profit per
    # $100 at best). Tune here if the dashboard feels too quiet/noisy.
    MIN_NET_RETURN = 0.0025

    best = None
    for pay_yes, pay_no, yes_side, no_side, is_real in directions:
        if not (0 < pay_yes < 1 and 0 < pay_no < 1):
            continue
        net = (1.0 - (pay_yes + pay_no)) - fee_a - fee_b
        if net > MIN_NET_RETURN and is_real and (best is None or net > best["net"]):
            best = {"net": net, "pay_yes": pay_yes, "pay_no": pay_no,
                    "yes_side": yes_side, "no_side": no_side}

    if best is not None:
        # Stake split proportional to inverse cost so both outcomes pay
        # the same total (per $100 deployed).
        inv_yes = 1 / best["pay_yes"]
        inv_no = 1 / best["pay_no"]
        s_yes = inv_yes / (inv_yes + inv_no)
        s_no = inv_no / (inv_yes + inv_no)
        sA, sB = (s_yes, s_no) if best["yes_side"] == "a" else (s_no, s_yes)
        result.update({
            "arb_type": "guaranteed",
            "guaranteed_return_pct": round(best["net"] * 100, 2),
            "stake_a_pct": round(sA * 100, 1),
            "stake_b_pct": round(sB * 100, 1),
            "stake_a_dollars": round(sA * 100, 2),
            "stake_b_dollars": round(sB * 100, 2),
            "profit_dollars": round(best["net"] * 100, 2),
            # Caller substitutes {yes_platform}/{no_platform} with names.
            "stake_note": (f"Buy YES on {{{best['yes_side']}}} at {best['pay_yes']*100:.1f}c "
                           f"+ Buy NO on {{{best['no_side']}}} at {best['pay_no']*100:.1f}c"),
        })

    return result


def _assert_scrape_freshness():
    """Fail loudly if any platform's raw CSV is more than MAX_AGE_HOURS old.

    Catches the silent-staleness failure mode where a scraper succeeds
    structurally (exit 0) but the CSV on disk is from a previous run.
    Pred-arb had a real incident (2026-06-21): a 44-day-old Polymarket CSV
    while every refresh reported success. Ported here 2026-07-03.
    """
    MAX_AGE_HOURS = 12
    issues = []
    for name in ("kalshi_markets.csv", "polymarket_markets.csv", "predictit_markets.csv"):
        path = RAW / name
        if not path.exists():
            issues.append(f"{name}: missing")
            continue
        try:
            df = pd.read_csv(path, nrows=1, dtype={"yes_token_id": str, "no_token_id": str})
        except Exception as e:
            issues.append(f"{name}: unreadable ({e})")
            continue
        if "fetched_at" not in df.columns:
            issues.append(f"{name}: no fetched_at column")
            continue
        ts = pd.to_datetime(df["fetched_at"].iloc[0], errors="coerce", utc=True)
        if pd.isna(ts):
            issues.append(f"{name}: unparseable fetched_at")
            continue
        age_h = (datetime.now(timezone.utc) - ts.to_pydatetime()).total_seconds() / 3600
        if age_h > MAX_AGE_HOURS:
            issues.append(f"{name}: stale by {age_h:.1f}h (max {MAX_AGE_HOURS}h)")
    if issues:
        print("FRESHNESS CHECK FAILED — refusing to write arb_data.js:")
        for issue in issues:
            print(f"  - {issue}")
        raise SystemExit(
            "One or more scraper CSVs are stale or missing. The workflow's "
            "commit step will skip; the live dashboard keeps the last good snapshot."
        )


# ── pair builder ──────────────────────────────────────────────────────────────

def _finalize_stake_note(arb_math: dict, platform_a: str, platform_b: str) -> dict:
    """Substitute the {a}/{b} placeholders compute_arb leaves in stake_note."""
    note = arb_math.get("stake_note")
    if note:
        arb_math["stake_note"] = note.replace("{a}", platform_a.title()).replace("{b}", platform_b.title())
    return arb_math


def _settle_fields(settle_a, settle_b, guaranteed_return_pct):
    """settle_date / days_to_settle / annualized return for a pair.

    Uses the LATER of the two legs' dates — capital is locked until both
    settle. Annualized = guaranteed return scaled to a year; the ranking
    metric for "sooner they cash" (a 3pp arb settling in 2 weeks beats a
    6pp arb settling in 4 months).
    """
    dates = []
    for s in (settle_a, settle_b):
        if s is None or (isinstance(s, float) and pd.isna(s)):
            continue
        d = pd.to_datetime(str(s), errors="coerce", utc=True)
        if pd.notna(d):
            dates.append(d)
    out = {"settle_date": None, "days_to_settle": None, "annualized_return_pct": None}
    if not dates:
        return out
    settle = max(dates)
    out["settle_date"] = settle.date().isoformat()
    days = max(1, (settle - pd.Timestamp.now(tz="UTC")).days)
    out["days_to_settle"] = int(days)
    if guaranteed_return_pct is not None and guaranteed_return_pct > 0:
        out["annualized_return_pct"] = round(guaranteed_return_pct / days * 365, 1)
    return out


def make_pair(race_id, label, state, office,
              prob_a, prob_b, platform_a, platform_b,
              url_a=None, url_b=None,
              bid_a=None, ask_a=None, no_ask_a=None, no_ask_a_real=False,
              bid_b=None, ask_b=None, no_ask_b=None, no_ask_b_real=False,
              settle_a=None, settle_b=None,
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

    arb_math = compute_arb(
        prob_a, prob_b, FEES[platform_a], FEES[platform_b],
        bid_a=bid_a, ask_a=ask_a, bid_b=bid_b, ask_b=ask_b,
        no_ask_a=no_ask_a, no_ask_b=no_ask_b,
        no_ask_a_real=no_ask_a_real, no_ask_b_real=no_ask_b_real,
    )
    arb_math = _finalize_stake_note(arb_math, platform_a, platform_b)
    arb_math.update(_settle_fields(settle_a, settle_b, arb_math.get("guaranteed_return_pct")))

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
        # Anything > 20pp is large enough to be worth a second look. Most
        # legit cross-platform gaps are <10pp; >20pp usually indicates a
        # scrape staleness, mismatched outcome, or broken book somewhere.
        "suspicious": bool(raw_gap * 100 > 20),
        "higher_platform": higher,
        "action": action,
        "url_a": url_a,
        "url_b": url_b,
        # Scrape-time quotes, kept on the row so the pass-2 depth join can
        # recompute the basket with live books and fall back to these.
        "bid_a": None if bid_a is None or pd.isna(bid_a) else float(bid_a),
        "ask_a": None if ask_a is None or pd.isna(ask_a) else float(ask_a),
        "no_ask_a": None if no_ask_a is None or pd.isna(no_ask_a) else float(no_ask_a),
        "no_ask_a_real": bool(no_ask_a_real),
        "bid_b": None if bid_b is None or pd.isna(bid_b) else float(bid_b),
        "ask_b": None if ask_b is None or pd.isna(ask_b) else float(ask_b),
        "no_ask_b": None if no_ask_b is None or pd.isna(no_ask_b) else float(no_ask_b),
        "no_ask_b_real": bool(no_ask_b_real),
        "settle_a": settle_a, "settle_b": settle_b,
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
    string for House races, else None.

    Critical: state names that ALSO occur as candidate surnames (Washington,
    Carolina, Jackson) cause false matches when we scan the whole title.
    Example: "Will Wayne Lonny Washington be the Republican nominee for the
    Senate in Oklahoma?" was matching state=WA on the surname "Washington"
    and never reaching "oklahoma". So we restrict the state search to the
    region AFTER the office anchor word ("for the Senate in <STATE>?",
    "for governor of <STATE>?", "for <STATE>-NN?"), which is where the
    actual state name lives in every template we scrape.
    """
    if not isinstance(title, str):
        return (None, None, None)
    t = title.lower()

    # House: "FL-6", "NY-16", "CA-12"
    m = re.search(r"\b([A-Z]{2})[-\s](\d{1,2})\b", title)
    if m and m.group(1) in _STATE_ABBREVS:
        return (m.group(1), "H", str(int(m.group(2))).zfill(2))

    def find_state(text):
        # Match longest-first so "west virginia" beats "virginia".
        for name, abbrev in sorted(_STATES.items(), key=lambda x: -len(x[0])):
            if name in text:
                return abbrev
        return None

    # Office anchor — substring after this is where the state name appears.
    office_word = None
    if "senate" in t or "senator" in t:
        office_word = "SEN"
        anchor_idx = max(t.rfind("senate"), t.rfind("senator"))
        suffix = t[anchor_idx:]
    elif "governor" in t or "gubernatorial" in t:
        office_word = "GOV"
        anchor_idx = max(t.rfind("governor"), t.rfind("gubernatorial"))
        suffix = t[anchor_idx:]
    elif "house" in t or "congress" in t:
        office_word = "H"
        anchor_idx = max(t.rfind("house"), t.rfind("congress"))
        suffix = t[anchor_idx:]
    else:
        office_word = None
        suffix = t  # no anchor → search whole title

    state_ab = find_state(suffix)
    # Fallback: if the anchored search found nothing, search the whole title
    # (covers edge templates we haven't seen yet).
    if not state_ab:
        state_ab = find_state(t)
    if not state_ab:
        return (None, None, None)

    if office_word in ("SEN", "GOV", "H"):
        return (state_ab, office_word, None)
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


def _safe_num(v):
    """NaN-safe float or None (module-level; loaders + pair builders)."""
    if v is None:
        return None
    v = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(v) else float(v)


def _quote_fields_kalshi(r):
    """Fillable-quote fields for a Kalshi market row (candidate loaders).
    Kalshi NO ask = 1 - yes_bid is exact (unified book), so it counts as real."""
    bid = _safe_num(r.get("yes_bid"))
    # Prefer expected_expiration_time (actual expected settlement) over
    # close_time (safety buffer, often a year late).
    settle = r.get("expected_expiration_time")
    if settle is None or (isinstance(settle, float) and pd.isna(settle)):
        settle = r.get("close_time")
    return {
        "bid": bid, "ask": _safe_num(r.get("yes_ask")),
        "no_ask": round(1 - bid, 4) if bid is not None and bid > 0 else None,
        "no_ask_real": bid is not None and bid > 0,
        "no_market_id": None,
        "settle": settle,
    }


def _quote_fields_polymarket(r):
    """Fillable-quote fields for a Polymarket market row (candidate loaders).
    No real NO quote at scrape time — pass 2 joins the NO-token book."""
    return {
        "bid": _safe_num(r.get("best_bid")), "ask": _safe_num(r.get("best_ask")),
        "no_ask": None, "no_ask_real": False,
        "no_market_id": r.get("no_token_id"),
        "settle": r.get("end_date"),
    }


def _quote_fields_predictit(r):
    """Fillable-quote fields for a PredictIt contract row (candidate loaders).
    bestBuyNo is a real fillable quote."""
    no_ask = _safe_num(r.get("best_buy_no"))
    return {
        "bid": _safe_num(r.get("best_sell_yes")), "ask": _safe_num(r.get("best_buy_yes")),
        "no_ask": no_ask, "no_ask_real": no_ask is not None,
        "no_market_id": None,
        "settle": r.get("date_end"),
    }


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
    k = _safe_read_csv(RAW / "kalshi_markets.csv")
    if not k.empty and "implied_prob" in k.columns and "market_title" in k.columns:
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
                "market_id": r.get("market_ticker"),
                "raw_title": title,
                **_quote_fields_kalshi(r),
            })

    # ── PredictIt ──
    # market_name = "Who will win the 2026 <State> <Party> Senate nomination?"
    # contract_name = candidate name
    pi = _safe_read_csv(RAW / "predictit_markets.csv")
    if not pi.empty and "implied_prob" in pi.columns:
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
                "market_id": None,
                "raw_title": f"{mn} — {cn}",
                **_quote_fields_predictit(r),
            })

    # ── Polymarket ──
    # "Will <Name> be the <Party> nominee for Senate in <State>?"
    pm = _safe_read_csv(RAW / "polymarket_markets.csv", dtype={"yes_token_id": str, "no_token_id": str})
    if not pm.empty and "implied_prob" in pm.columns:
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
                "market_id": r.get("yes_token_id"),
                "raw_title": title,
                **_quote_fields_polymarket(r),
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["race_id"] = df.apply(
            lambda r: _race_id_from(r["state"], r["office"], r["district"]),
            axis=1,
        )
    return df


# Titles that include any of these phrases are NOT general-election
# candidate-win markets even if they mention a name + an office. These all
# come from real Kalshi/Polymarket titles we don't want to pair:
#   - "Will Ken Paxton win Harris County?"  (county-level)
#   - "Will X finish 3rd in Texas?"          (placement, not winning)
#   - "Will X drop out of the Texas Senate race"
#   - "Will X endorse Y in the runoff"
#   - "Will X win Lieutenant Governor"       (no Senate/Gov/House mapping)
_GEN_CAND_EXCLUDE = re.compile(
    r"\b(county|finish\s+\d|drop\s+out|endorse|lieutenant|runoff\s+before|primary\s+runoff)\b",
    re.IGNORECASE,
)

# "Will the Mike Duggan party win the governorship in Michigan" and
# "Will an independent win the X Senate race" are aggregate party/independent
# markets, not candidate-win — skip.
_GEN_CAND_SUBJECT_SKIP = re.compile(
    r"^(the\s+|an?\s+independent\b)",
    re.IGNORECASE,
)


def load_general_candidates():
    """
    Tidy frame of candidate-level GENERAL-election win markets across
    Kalshi / Polymarket / PredictIt. Mirrors load_primary_candidates() but
    targets the "Will <Name> win the 2026 <State> Senate race?" template
    family instead of the "be the nominee" family.

    The matching key downstream is (state, office, district, last_name,
    first_initial) — same as primaries, minus party (general-election
    candidates are unambiguous across parties; the surname carries the
    identity).
    """
    rows = []

    # ── Kalshi ──
    # Templates seen in production:
    #   "Will Dan Sullivan win the 2026 Alaska Senate race?"
    #   "Will Adam Crum win the 2026 Alaska governor election?"
    #   "Will Mary Peltola win the 2026 Alaska Senate race?"
    # _extract_state_office handles the "Alaska Senate" / "Alaska governor"
    # suffix, including the same-surname-as-state guard.
    k = _safe_read_csv(RAW / "kalshi_markets.csv")
    if not k.empty and "implied_prob" in k.columns and "market_title" in k.columns:
        k = k[k["implied_prob"].notna() & k["market_title"].notna()].copy()
        pat = re.compile(
            r"^Will\s+(.+?)\s+win\s+the\s+2026\s+(.+?)\??$",
            re.IGNORECASE,
        )
        for _, r in k.iterrows():
            title = str(r["market_title"])
            if _GEN_CAND_EXCLUDE.search(title):
                continue
            m = pat.match(title.strip())
            if not m:
                continue
            name = m.group(1).strip()
            tail = m.group(2).strip()
            if _GEN_CAND_SUBJECT_SKIP.match(name):
                continue
            # Tail must reference Senate / governor / House for office mapping.
            if not re.search(r"\b(senate|senator|governor|gubernatorial|house|congress)\b", tail, re.IGNORECASE):
                continue
            state, office, district = _extract_state_office(title)
            if not state or not office:
                continue
            last = _canonical_last_name(name)
            if not last:
                continue
            rows.append({
                "state": state, "office": office, "district": district,
                "candidate_last": last,
                "candidate_first": _first_initial(name),
                "candidate_name": name,
                "platform": "kalshi",
                "prob": float(r["implied_prob"]),
                "url": kalshi_url(r.get("series_ticker")),
                "volume": pd.to_numeric(r.get("volume"), errors="coerce"),
                "oi": pd.to_numeric(r.get("open_interest"), errors="coerce"),
                "market_id": r.get("market_ticker"),
                "raw_title": title,
                **_quote_fields_kalshi(r),
            })

    # ── Polymarket ──
    # Templates seen in production:
    #   "Will Rick Caruso win the California Governor Election in 2026?"
    #   "Will Dan Sullivan win the Alaska Senate race in 2026?"
    #   "Will Adam Crum win the 2026 Alaska governor election?"
    # Two orderings of the year token — match both.
    pm = _safe_read_csv(RAW / "polymarket_markets.csv", dtype={"yes_token_id": str, "no_token_id": str})
    if not pm.empty and "implied_prob" in pm.columns:
        pm = pm[pm["implied_prob"].notna()].copy()
        pat = re.compile(
            r"^Will\s+(.+?)\s+win\s+(?:the\s+)?(?:(?:2026\s+)?(.+?)(?:\s+in\s+2026)?)\??$",
            re.IGNORECASE,
        )
        slug_col = "event_slug" if "event_slug" in pm.columns else ("market_slug" if "market_slug" in pm.columns else None)
        for _, r in pm.iterrows():
            title = str(r.get("question", ""))
            if _GEN_CAND_EXCLUDE.search(title):
                continue
            m = pat.match(title.strip())
            if not m:
                continue
            name = m.group(1).strip()
            tail = m.group(2).strip()
            if _GEN_CAND_SUBJECT_SKIP.match(name):
                continue
            # Reject nominee/primary just in case the upstream pre-filter ever
            # changes shape.
            if re.search(r"\b(nominee|primary|nominate|advance)\b", title, re.IGNORECASE):
                continue
            if not re.search(r"\b(senate|senator|governor|gubernatorial|house|congress)\b", tail, re.IGNORECASE):
                continue
            state, office, district = _extract_state_office(title)
            if not state or not office:
                continue
            last = _canonical_last_name(name)
            if not last:
                continue
            slug = r.get(slug_col) if slug_col else None
            rows.append({
                "state": state, "office": office, "district": district,
                "candidate_last": last,
                "candidate_first": _first_initial(name),
                "candidate_name": name,
                "platform": "polymarket",
                "prob": float(r["implied_prob"]),
                "url": polymarket_url(slug),
                "volume": pd.to_numeric(r.get("volume"), errors="coerce"),
                "oi": pd.to_numeric(r.get("liquidity"), errors="coerce"),
                "market_id": r.get("yes_token_id"),
                "raw_title": title,
                **_quote_fields_polymarket(r),
            })

    # ── PredictIt ──
    # market_name templates seen:
    #   "Who will win the 2026 election for governor of California?"
    #   "Who will win the 2026 election for U.S. Senate in Iowa?"
    # contract_name = candidate name. We exclude party-only markets
    # ("Which party will win the 2026 US Senate election in X?") and
    # nomination markets.
    pi = _safe_read_csv(RAW / "predictit_markets.csv")
    if not pi.empty and "implied_prob" in pi.columns:
        pi = pi[pi["implied_prob"].notna()].copy()
        for _, r in pi.iterrows():
            mn = str(r.get("market_name", ""))
            cn = str(r.get("contract_name", ""))
            ml = mn.lower()
            if "nomination" in ml or "primary" in ml:
                continue
            if ml.startswith("which party"):
                continue
            if "who will win" not in ml and "who wins" not in ml:
                continue
            # Skip catch-all contracts.
            cn_norm = cn.lower().strip()
            if cn_norm in ("any other", "any other candidate", "no nominee", "other"):
                continue
            state, office, district = _extract_state_office(mn)
            if not state or not office:
                continue
            last = _canonical_last_name(cn)
            if not last:
                continue
            rows.append({
                "state": state, "office": office, "district": district,
                "candidate_last": last,
                "candidate_first": _first_initial(cn),
                "candidate_name": cn.strip(),
                "platform": "predictit",
                "prob": float(r["implied_prob"]),
                "url": predictit_url(r.get("market_id")),
                "volume": None, "oi": None,
                "market_id": None,
                "raw_title": f"{mn} — {cn}",
                **_quote_fields_predictit(r),
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["race_id"] = df.apply(
            lambda r: _race_id_from(r["state"], r["office"], r["district"]),
            axis=1,
        )
    return df


def general_candidate_pairs(meta_df):
    """
    Cross-platform GENERAL-election candidate pairs.

    Matching key: (state, office, district, candidate_last, candidate_first).
    Same shape as primary_pairs but no party in the key — general-election
    candidates are uniquely identified by name.

    Emits "one-sided" rows: there's no Dem-yes vs Rep-yes complement to
    compute a guaranteed-arb basket from. A real arb here would be Buy
    candidate-yes on the cheap side + Buy candidate-no (or competing
    candidate) on the expensive side, but Polymarket / Kalshi don't expose
    candidate-no as a separately tradeable contract in this template — the
    yes-vs-yes price gap is the actionable signal.
    """
    cands = load_general_candidates()
    if cands.empty:
        return []

    # Dedup: keep highest-rank market per (race, candidate, platform).
    cands["_rank"] = cands[["volume", "oi"]].fillna(0).max(axis=1)
    cands["district"] = cands["district"].fillna("")
    cands["candidate_first"] = cands["candidate_first"].fillna("")
    sort_cols = ["state", "office", "district", "candidate_last",
                 "candidate_first", "platform", "_rank", "prob"]
    cands = cands.sort_values(sort_cols, ascending=[True, True, True, True, True, True, False, False])
    dedup_key = ["state", "office", "district", "candidate_last", "candidate_first", "platform"]
    cands = cands.drop_duplicates(subset=dedup_key)

    meta_map = {r["race_id"]: r for _, r in meta_df.iterrows()} if not meta_df.empty else {}

    out = []
    key_cols = ["state", "office", "district", "candidate_last", "candidate_first"]
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
                net_gap = raw_gap - FEES[pa] - FEES[pb]
                cheaper = pa if prob_a < prob_b else pb
                expensive = pb if prob_a < prob_b else pa
                # Real YES+NO basket math (2026-07-03). These templates DO
                # have tradeable NO sides (Kalshi unified book, Polymarket
                # NO token, PredictIt Buy-No quote) — the old hardcoded
                # "one-sided" was wrong. `is True` guards the bool(NaN)
                # footgun (see HANDOFF Python footguns).
                arb_math = compute_arb(
                    prob_a, prob_b, FEES[pa], FEES[pb],
                    bid_a=_safe_num(ra.get("bid")), ask_a=_safe_num(ra.get("ask")),
                    bid_b=_safe_num(rb.get("bid")), ask_b=_safe_num(rb.get("ask")),
                    no_ask_a=_safe_num(ra.get("no_ask")), no_ask_b=_safe_num(rb.get("no_ask")),
                    no_ask_a_real=ra.get("no_ask_real") is True,
                    no_ask_b_real=rb.get("no_ask_real") is True,
                )
                arb_math = _finalize_stake_note(arb_math, pa, pb)
                arb_math.update(_settle_fields(ra.get("settle"), rb.get("settle"),
                                               arb_math.get("guaranteed_return_pct")))
                action = (
                    f"Buy {ra['candidate_name']} on {cheaper.title()} "
                    f"({min(prob_a, prob_b)*100:.1f}%), fade on "
                    f"{expensive.title()} ({max(prob_a, prob_b)*100:.1f}%)"
                )
                state, office, district = key[0], key[1], key[2] or None
                rid = _race_id_from(state, office, district or None)
                meta = meta_map.get(rid, {}) if rid else {}
                if isinstance(meta, dict):
                    label = meta.get("label") or (rid or f"{state} {office}")
                    state_name = meta.get("state", state)
                else:
                    label = getattr(meta, "label", None) or (rid or f"{state} {office}")
                    state_name = getattr(meta, "state", state)
                out.append({
                    "match_type": "general_candidate",
                    "race_id": rid,
                    "label": label,
                    "state": state_name,
                    "office": office,
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
                    "suspicious": bool(raw_gap * 100 > 20),
                    "higher_platform": expensive,
                    "action": action,
                    **arb_math,
                    "url_a": ra.get("url"), "url_b": rb.get("url"),
                    "volume_a": None if pd.isna(ra.get("volume")) else float(ra.get("volume")),
                    "volume_b": None if pd.isna(rb.get("volume")) else float(rb.get("volume")),
                    "market_id_a": ra.get("market_id"),
                    "market_id_b": rb.get("market_id"),
                    "market_no_id_a": ra.get("no_market_id"),
                    "market_no_id_b": rb.get("no_market_id"),
                    "bid_a": _safe_num(ra.get("bid")), "ask_a": _safe_num(ra.get("ask")),
                    "no_ask_a": _safe_num(ra.get("no_ask")), "no_ask_a_real": ra.get("no_ask_real") is True,
                    "bid_b": _safe_num(rb.get("bid")), "ask_b": _safe_num(rb.get("ask")),
                    "no_ask_b": _safe_num(rb.get("no_ask")), "no_ask_b_real": rb.get("no_ask_real") is True,
                    "settle_a": ra.get("settle"), "settle_b": rb.get("settle"),
                    "question_a": ra.get("raw_title", ""),
                    "question_b": rb.get("raw_title", ""),
                })
    return out


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
                net_gap = raw_gap - FEES[pa] - FEES[pb]
                cheaper = pa if prob_a < prob_b else pb
                expensive = pb if prob_a < prob_b else pa
                # Real YES+NO basket math (2026-07-03). These templates DO
                # have tradeable NO sides (Kalshi unified book, Polymarket
                # NO token, PredictIt Buy-No quote) — the old hardcoded
                # "one-sided" was wrong. `is True` guards the bool(NaN)
                # footgun (see HANDOFF Python footguns).
                arb_math = compute_arb(
                    prob_a, prob_b, FEES[pa], FEES[pb],
                    bid_a=_safe_num(ra.get("bid")), ask_a=_safe_num(ra.get("ask")),
                    bid_b=_safe_num(rb.get("bid")), ask_b=_safe_num(rb.get("ask")),
                    no_ask_a=_safe_num(ra.get("no_ask")), no_ask_b=_safe_num(rb.get("no_ask")),
                    no_ask_a_real=ra.get("no_ask_real") is True,
                    no_ask_b_real=rb.get("no_ask_real") is True,
                )
                arb_math = _finalize_stake_note(arb_math, pa, pb)
                arb_math.update(_settle_fields(ra.get("settle"), rb.get("settle"),
                                               arb_math.get("guaranteed_return_pct")))
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
                    "suspicious": bool(raw_gap * 100 > 20),
                    "higher_platform": expensive,
                    "action": action,
                    **arb_math,
                    "url_a": ra.get("url"), "url_b": rb.get("url"),
                    "volume_a": None if pd.isna(ra.get("volume")) else float(ra.get("volume")),
                    "volume_b": None if pd.isna(rb.get("volume")) else float(rb.get("volume")),
                    "market_id_a": ra.get("market_id"),
                    "market_id_b": rb.get("market_id"),
                    "market_no_id_a": ra.get("no_market_id"),
                    "market_no_id_b": rb.get("no_market_id"),
                    "bid_a": _safe_num(ra.get("bid")), "ask_a": _safe_num(ra.get("ask")),
                    "no_ask_a": _safe_num(ra.get("no_ask")), "no_ask_a_real": ra.get("no_ask_real") is True,
                    "bid_b": _safe_num(rb.get("bid")), "ask_b": _safe_num(rb.get("ask")),
                    "no_ask_b": _safe_num(rb.get("no_ask")), "no_ask_b_real": rb.get("no_ask_real") is True,
                    "settle_a": ra.get("settle"), "settle_b": rb.get("settle"),
                    "question_a": ra.get("raw_title", ""),
                    "question_b": rb.get("raw_title", ""),
                })
    return out


# ── main ──────────────────────────────────────────────────────────────────────

def run():
    _assert_scrape_freshness()
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

    def _num(v):
        """NaN-safe float or None."""
        if v is None:
            return None
        v = pd.to_numeric(v, errors="coerce")
        return None if pd.isna(v) else float(v)

    def _kalshi_no_ask(bid):
        # Kalshi's book is unified: buying NO at (1 - yes_bid) fills against
        # the resting YES bid, so this is an EXACT fillable NO ask, not the
        # banned midpoint-complement inference.
        b = _num(bid)
        return (round(1 - b, 4), True) if b is not None and b > 0 else (None, False)

    # ── Kalshi vs PredictIt ──
    kpi = kalshi.merge(pi, on="race_id", how="inner")
    for _, r in kpi.iterrows():
        k_no, k_no_real = _kalshi_no_ask(r.get("kalshi_dem_bid"))
        row = make_pair(
            r["race_id"], r.get("label", r["race_id"]), r.get("state", ""), r.get("office", ""),
            r.get("kalshi_dem"), r.get("pi_dem"),
            "kalshi", "predictit",
            url_a=r.get("kalshi_url"), url_b=r.get("pi_url"),
            bid_a=_num(r.get("kalshi_dem_bid")), ask_a=_num(r.get("kalshi_dem_ask")),
            no_ask_a=k_no, no_ask_a_real=k_no_real,
            bid_b=_num(r.get("pi_dem_sell")), ask_b=_num(r.get("pi_dem_buy")),
            no_ask_b=_num(r.get("pi_dem_buy_no")), no_ask_b_real=_num(r.get("pi_dem_buy_no")) is not None,
            settle_a=r.get("kalshi_close_time"), settle_b=r.get("pi_date_end"),
            extra={
                "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell"),
                "kalshi_oi": r.get("kalshi_oi"),
                "volume_a": r.get("kalshi_volume"), "volume_b": None,
                "market_id_a": r.get("kalshi_dem_ticker"),
                "market_id_b": None,
            },
        )
        if row:
            rows.append(row)

    # ── Kalshi vs Polymarket ──
    if not pm.empty and "pm_dem" in pm.columns:
        kpm = kalshi.merge(pm, on="race_id", how="inner")
        for _, r in kpm.iterrows():
            k_no, k_no_real = _kalshi_no_ask(r.get("kalshi_dem_bid"))
            row = make_pair(
                r["race_id"], r.get("label", r["race_id"]), r.get("state", ""), r.get("office", ""),
                r.get("kalshi_dem"), r.get("pm_dem"),
                "kalshi", "polymarket",
                url_a=r.get("kalshi_url"), url_b=r.get("pm_url"),
                bid_a=_num(r.get("kalshi_dem_bid")), ask_a=_num(r.get("kalshi_dem_ask")),
                no_ask_a=k_no, no_ask_a_real=k_no_real,
                bid_b=_num(r.get("pm_dem_bid")), ask_b=_num(r.get("pm_dem_ask")),
                # Real PM NO ask arrives via the NO-token book in pass 2.
                no_ask_b=None, no_ask_b_real=False,
                settle_a=r.get("kalshi_close_time"), settle_b=r.get("pm_end_date"),
                extra={
                    "pm_liq": r.get("pm_liq"), "kalshi_oi": r.get("kalshi_oi"),
                    "volume_a": r.get("kalshi_volume"), "volume_b": r.get("pm_volume"),
                    "market_id_a": r.get("kalshi_dem_ticker"),
                    "market_id_b": r.get("pm_dem_token"),
                    "market_no_id_b": r.get("pm_dem_no_token"),
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
                url_a=r.get("pi_url"), url_b=r.get("pm_url"),
                bid_a=_num(r.get("pi_dem_sell")), ask_a=_num(r.get("pi_dem_buy")),
                no_ask_a=_num(r.get("pi_dem_buy_no")), no_ask_a_real=_num(r.get("pi_dem_buy_no")) is not None,
                bid_b=_num(r.get("pm_dem_bid")), ask_b=_num(r.get("pm_dem_ask")),
                no_ask_b=None, no_ask_b_real=False,
                settle_a=r.get("pi_date_end"), settle_b=r.get("pm_end_date"),
                extra={
                    "pm_liq": r.get("pm_liq"),
                    "pi_dem_buy": r.get("pi_dem_buy"), "pi_dem_sell": r.get("pi_dem_sell"),
                    "volume_a": None, "volume_b": r.get("pm_volume"),
                    "market_id_a": None,
                    "market_id_b": r.get("pm_dem_token"),
                    "market_no_id_b": r.get("pm_dem_no_token"),
                },
            )
            if row:
                rows.append(row)

    # Tag general-election (party-level) pairs, then append candidate-level
    # general pairs and primary-candidate pairs.
    for row in rows:
        row.setdefault("match_type", "general")

    gen_cand = general_candidate_pairs(meta)
    print(f"\nGeneral-election candidate cross-platform pairs: {len(gen_cand)}")
    if gen_cand:
        top = sorted(gen_cand, key=lambda r: -r["raw_gap_pp"])[:10]
        print("Top general-candidate gaps:")
        for r in top:
            print(f"  {r['pair']:>22}  {r['candidate']:20} {r['label']:14} "
                  f"gap={r['raw_gap_pp']:5.1f}pp  "
                  f"{r['platform_a']}={r['prob_a']*100:5.1f}%  {r['platform_b']}={r['prob_b']*100:5.1f}%")
    rows.extend(gen_cand)

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

    # ── emit depth_targets.csv (consumed by scripts/fetch_depth.py) ──
    # Includes Polymarket NO tokens (market_no_id_*) so fetch_depth pulls
    # the real NO book — needed for exact YES+NO basket math in pass 2.
    targets = []
    for _, r in arb.iterrows():
        for side in ("a", "b"):
            plat = r.get(f"platform_{side}")
            if plat not in ("kalshi", "polymarket"):
                continue
            for col in (f"market_id_{side}", f"market_no_id_{side}"):
                mid = r.get(col)
                if mid is not None and not (isinstance(mid, float) and pd.isna(mid)):
                    targets.append({"platform": plat, "market_id": mid})
    if targets:
        td = pd.DataFrame(targets)
        td["market_id"] = td["market_id"].astype(str)
        td = td.drop_duplicates()
        proc = ROOT / "data" / "processed"
        proc.mkdir(parents=True, exist_ok=True)
        td.to_csv(proc / "depth_targets.csv", index=False)
        print(f"\nWrote {len(td)} unique depth targets to data/processed/depth_targets.csv")

    # ── join orderbook depth if fetched ──
    depth_path = RAW / "orderbook_depth.csv"
    if depth_path.exists():
        depth = pd.read_csv(depth_path, dtype={"market_id": str}).drop_duplicates(subset=["platform", "market_id"], keep="last")
        for side in ("a", "b"):
            # Ensure the NO-token column exists even when no row set it
            # (e.g. a run where candidate paths matched nothing).
            if f"market_no_id_{side}" not in arb.columns:
                arb[f"market_no_id_{side}"] = None
            for col in (f"market_id_{side}", f"market_no_id_{side}"):
                arb[col] = arb[col].apply(
                    lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
                )
            d = depth.rename(columns={
                "platform": f"platform_{side}",
                "market_id": f"market_id_{side}",
                "best_bid": f"depth_{side}_best_bid",
                "best_ask": f"depth_{side}_best_ask",
                "best_bid_size": f"depth_{side}_best_bid_size",
                "best_ask_size": f"depth_{side}_best_ask_size",
                "depth_bid_at_1pp": f"depth_{side}_bid_1pp",
                "depth_ask_at_1pp": f"depth_{side}_ask_1pp",
                "max_buy_size_at_3pp_edge": f"depth_{side}_max_at_3pp",
            })[[f"platform_{side}", f"market_id_{side}",
                f"depth_{side}_best_bid", f"depth_{side}_best_ask",
                f"depth_{side}_best_bid_size", f"depth_{side}_best_ask_size",
                f"depth_{side}_bid_1pp", f"depth_{side}_ask_1pp",
                f"depth_{side}_max_at_3pp"]]
            arb = arb.merge(d, on=[f"platform_{side}", f"market_id_{side}"], how="left")
            # Join the NO-token book (Polymarket only — Kalshi NO is derived
            # from the same book; PredictIt has no orderbook).
            dno = depth.rename(columns={
                "platform": f"platform_{side}",
                "market_id": f"market_no_id_{side}",
                "best_bid": f"depth_no_{side}_best_bid",
                "best_ask": f"depth_no_{side}_best_ask",
            })[[f"platform_{side}", f"market_no_id_{side}",
                f"depth_no_{side}_best_bid", f"depth_no_{side}_best_ask"]]
            arb = arb.merge(dno, on=[f"platform_{side}", f"market_no_id_{side}"], how="left")
        joined = arb[["depth_a_best_ask", "depth_b_best_ask"]].notna().any(axis=1).sum()
        print(f"Joined orderbook depth onto {joined}/{len(arb)} pairs")

        # ── recompute basket math on LIVE books (2026-07-03) ──
        # Pass-1 math ran on scrape-time quotes; the depth fetch is fresher
        # and includes the real Polymarket NO-token ask. Priority per leg:
        # live book > scrape-time quote > display prob (never guaranteed).
        def _recompute(row):
            pa_, pb_ = row.get("platform_a"), row.get("platform_b")
            legs = {}
            for side in ("a", "b"):
                plat = row.get(f"platform_{side}")
                bid = row.get(f"depth_{side}_best_bid")
                ask = row.get(f"depth_{side}_best_ask")
                bid = float(bid) if pd.notna(bid) else row.get(f"bid_{side}")
                ask = float(ask) if pd.notna(ask) else row.get(f"ask_{side}")
                no_ask = row.get(f"depth_no_{side}_best_ask")
                if pd.notna(no_ask):
                    no_ask, no_real = float(no_ask), True
                elif plat == "kalshi" and bid is not None and not pd.isna(bid) and bid > 0:
                    no_ask, no_real = round(1 - float(bid), 4), True  # unified book — exact
                else:
                    no_ask = row.get(f"no_ask_{side}")
                    no_real = row.get(f"no_ask_{side}_real") is True
                legs[side] = (bid, ask, no_ask, no_real)
            prob_a = row.get("prob_a")
            if prob_a is None or pd.isna(prob_a):
                prob_a = row.get(f"{pa_}_dem")
            prob_b = row.get("prob_b")
            if prob_b is None or pd.isna(prob_b):
                prob_b = row.get(f"{pb_}_dem")
            if prob_a is None or pd.isna(prob_a) or prob_b is None or pd.isna(prob_b):
                return None
            am = compute_arb(
                prob_a, prob_b, FEES[pa_], FEES[pb_],
                bid_a=legs["a"][0], ask_a=legs["a"][1],
                bid_b=legs["b"][0], ask_b=legs["b"][1],
                no_ask_a=legs["a"][2], no_ask_b=legs["b"][2],
                no_ask_a_real=legs["a"][3], no_ask_b_real=legs["b"][3],
            )
            am = _finalize_stake_note(am, pa_, pb_)
            am.update(_settle_fields(row.get("settle_a"), row.get("settle_b"),
                                     am.get("guaranteed_return_pct")))
            return am
        recomputed = arb.apply(_recompute, axis=1)
        n_upgraded = n_downgraded = 0
        for idx, am in recomputed.items():
            if am is None:
                continue
            was = arb.at[idx, "arb_type"]
            for k, v in am.items():
                arb.at[idx, k] = v
            if was != am["arb_type"]:
                if am["arb_type"] == "guaranteed":
                    n_upgraded += 1
                else:
                    n_downgraded += 1
        print(f"Live-book recompute: {n_upgraded} pairs upgraded to guaranteed, "
              f"{n_downgraded} downgraded")

        # Defense in depth: even if a scraper missed a wide-spread market at
        # scrape time (gamma snapshots lag the live CLOB book), the
        # fetch_depth pull is fresh. Drop any pair where the depth-derived
        # spread on EITHER side exceeds 25pp — those quotes can't be filled.
        def wide_spread(row, side):
            bb = row.get(f"depth_{side}_best_bid")
            ba = row.get(f"depth_{side}_best_ask")
            if pd.isna(bb) or pd.isna(ba) or bb is None or ba is None:
                return False  # no depth data; trust the scraper-level filter
            return (ba - bb) > 0.25
        before = len(arb)
        arb = arb[~arb.apply(lambda r: wide_spread(r, "a") or wide_spread(r, "b"), axis=1)]
        if before != len(arb):
            print(f"Dropped {before - len(arb)} pairs with wide depth-derived spread (>25pp)")

        # Build suspicion_reasons array per pair. Anything > 20pp gap gets
        # flagged, AND we tag additional warning signs based on depth so the
        # dashboard can show WHY a pair is suspicious.
        def reasons(row):
            rs = []
            if (row.get("raw_gap_pp") or 0) > 20:
                rs.append("wide_gap")
            for side in ("a", "b"):
                bb = row.get(f"depth_{side}_best_bid")
                ba = row.get(f"depth_{side}_best_ask")
                if pd.notna(bb) and pd.notna(ba) and (ba - bb) > 0.15:
                    rs.append(f"wide_spread_{side}")
                if pd.notna(ba) and pd.isna(bb):
                    rs.append(f"one_sided_{side}")
                m3 = row.get(f"depth_{side}_max_at_3pp")
                if pd.notna(m3) and m3 < 20:
                    rs.append(f"thin_depth_{side}")
            return rs
        arb["suspicion_reasons"] = arb.apply(reasons, axis=1)
        arb["suspicious"] = arb["suspicion_reasons"].apply(lambda rs: len(rs) > 0)

        # Scrutinize >30pp pairs against each market's official rules.
        # Pairs whose resolution criteria differ are dropped; borderline
        # ones get tagged criteria_warn.
        try:
            from scripts.scrutiny import scrutinize as _scrutinize
        except ImportError:
            try:
                import sys as _sys
                _sys.path.insert(0, str(ROOT))
                from scripts.scrutiny import scrutinize as _scrutinize
            except Exception:
                _scrutinize = None
        if _scrutinize is not None:
            scrut = _scrutinize(arb.to_dict(orient="records"), threshold_pp=30)
            # Candidate-level pairs promoted to guaranteed get scrutinized
            # regardless of gap size — resolution-criteria divergence risk
            # is highest exactly there (same candidate name, different fine
            # print: runoffs, specials, withdrawal rules). Cheap: scrutiny
            # caches rules text for 7 days.
            promoted = [r for r in arb.to_dict(orient="records")
                        if r.get("match_type") in ("general_candidate", "primary_candidate")
                        and r.get("arb_type") == "guaranteed"]
            if promoted:
                scrut.update(_scrutinize(promoted, threshold_pp=0))
            def apply_scrut(row):
                k = (str(row.get("market_id_a")), str(row.get("market_id_b")))
                return scrut.get(k)
            arb["_scrut"] = arb.apply(apply_scrut, axis=1)
            drop_mask = arb["_scrut"].apply(lambda s: bool(s) and s.get("action") == "drop")
            n_drop = int(drop_mask.sum())
            if n_drop:
                print(f"Dropped {n_drop} pairs after rules-text scrutiny (criteria mismatch)")
            arb = arb[~drop_mask].copy()
            def merge_scrut(row):
                s = row.get("_scrut")
                rs = list(row.get("suspicion_reasons") or [])
                if s and s.get("action") == "warn":
                    rs.append(f"criteria_warn:{s.get('reason')}")
                return rs
            arb["suspicion_reasons"] = arb.apply(merge_scrut, axis=1)
            arb["criteria_score"] = arb["_scrut"].apply(lambda s: s.get("criteria_score") if s else None)
            arb["suspicious"] = arb["suspicion_reasons"].apply(lambda rs: len(rs) > 0)
            arb = arb.drop(columns=["_scrut"])
    else:
        print("No depth file found yet — run scripts/fetch_depth.py to populate it.")

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
