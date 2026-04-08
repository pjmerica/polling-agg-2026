"""
Polling and prediction market aggregator.

Reads from data/raw/ and produces data/processed/aggregated.csv.

Current data sources:
  - Kalshi prediction markets (data/raw/kalshi_markets.csv)
  - Polymarket prediction markets (data/raw/polymarket_markets.csv)

Future sources (when polling data becomes available):
  - RCP polls (data/raw/rcp_polls.csv) — blocked, needs manual export or Selenium
  - 538 polls — data pipeline dead, recheck summer 2026

Output schema (data/processed/aggregated.csv):
  race_id, state, office, district, incumbent_party,
  source, market_title, implied_prob, weight,
  fetched_at

For prediction markets:
  implied_prob: midpoint of bid/ask (Kalshi) or "Yes" price (Polymarket), 0.0-1.0
  weight: based on open_interest/volume (Kalshi) or liquidity (Polymarket)

When polls are added:
  implied_prob: candidate poll share
  weight: f(sample_size, recency, pollster_grade)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def load_kalshi() -> pd.DataFrame:
    """Load and validate Kalshi markets CSV."""
    path = RAW_DIR / "kalshi_markets.csv"
    if not path.exists():
        print("  kalshi_markets.csv not found — run scrapers/kalshi.py first")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Keep only markets with a matched race_id and valid implied probability
    df = df[df["race_id"].notna() & df["implied_prob"].notna()].copy()
    df["source"] = "kalshi"
    # Normalize weight: use open_interest if available, else volume, else 1
    df["weight"] = df.get("open_interest", pd.Series(dtype=float)).fillna(
        df.get("volume", pd.Series(dtype=float))
    ).fillna(1.0)
    return df[["race_id", "source", "market_title", "implied_prob", "weight", "fetched_at"]]


def load_polymarket() -> pd.DataFrame:
    """Load and validate Polymarket markets CSV."""
    path = RAW_DIR / "polymarket_markets.csv"
    if not path.exists():
        print("  polymarket_markets.csv not found — run scrapers/polymarket.py first")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["implied_prob"].notna()].copy()
    df["source"] = "polymarket"
    df["market_title"] = df.get("question", "")
    # Weight by liquidity; Polymarket liquidity is in dollars
    df["weight"] = pd.to_numeric(df.get("liquidity", 1), errors="coerce").fillna(1.0)
    # Polymarket doesn't always have race_ids — those are matched by keyword
    # Only include rows where we can infer a race (has race_id column populated)
    if "race_id" not in df.columns:
        df["race_id"] = None
    df = df[df["race_id"].notna()].copy()
    return df[["race_id", "source", "market_title", "implied_prob", "weight", "fetched_at"]]


def load_rcp_polls() -> pd.DataFrame:
    """Load RCP polls if available."""
    path = RAW_DIR / "rcp_polls.csv"
    if not path.exists():
        print("  rcp_polls.csv not found — see scrapers/realclearpolitics.py for manual export instructions")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # TODO: implement weight calculation when poll data arrives
    # weight = f(sample_size, days_since_poll, pollster_grade)
    return df


def compute_weighted_average(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a weighted average implied_prob per race_id.

    For prediction markets: weights are proportional to open interest / liquidity.
    Higher liquidity = more confident price signal.
    """
    if df.empty:
        return df

    def wavg(group):
        w = group["weight"].values
        p = group["implied_prob"].values
        total_w = w.sum()
        if total_w == 0:
            avg = p.mean()
        else:
            avg = np.average(p, weights=w)
        return pd.Series({
            "implied_prob_avg": round(avg, 4),
            "n_sources": len(group),
            "total_weight": round(total_w, 2),
            "sources": "|".join(group["source"].unique()),
        })

    return df.groupby("race_id").apply(wavg).reset_index()


def attach_race_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Join race metadata (state, office, incumbent) from utils/races.py."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.races import RACE_BY_ID
        meta_rows = []
        for race_id, race in RACE_BY_ID.items():
            meta_rows.append({
                "race_id": race_id,
                "state": race.state,
                "state_abbrev": race.state_abbrev,
                "office": race.office,
                "district": race.district,
                "incumbent_party": race.incumbent_party,
                "incumbent_name": race.incumbent_name,
            })
        meta = pd.DataFrame(meta_rows)
        return df.merge(meta, on="race_id", how="left")
    except Exception as e:
        print(f"  WARNING: could not attach race metadata: {e}")
        return df


def run():
    """Aggregate all available data and write processed output."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading sources...")
    frames = []

    kalshi = load_kalshi()
    if not kalshi.empty:
        print(f"  Kalshi: {len(kalshi)} market rows across {kalshi['race_id'].nunique()} races")
        frames.append(kalshi)

    polymarket = load_polymarket()
    if not polymarket.empty:
        print(f"  Polymarket: {len(polymarket)} market rows across {polymarket['race_id'].nunique()} races")
        frames.append(polymarket)

    rcp = load_rcp_polls()
    if not rcp.empty:
        print(f"  RCP: {len(rcp)} poll rows")
        frames.append(rcp)

    if not frames:
        print("\nNo data loaded. Run the scrapers first:")
        print("  py -3 scrapers/kalshi.py")
        print("  py -3 scrapers/polymarket.py")
        return

    combined = pd.concat(frames, ignore_index=True)

    # Save raw combined view
    combined.to_csv(PROCESSED_DIR / "combined_raw.csv", index=False)
    print(f"\nCombined raw: {len(combined)} rows -> data/processed/combined_raw.csv")

    # Compute weighted averages per race
    avg = compute_weighted_average(combined)
    avg = attach_race_metadata(avg)
    avg["updated_at"] = datetime.now(timezone.utc).isoformat()

    out_path = PROCESSED_DIR / "aggregated.csv"
    avg.to_csv(out_path, index=False)
    print(f"Aggregated: {len(avg)} races -> {out_path}")

    # Quick summary by office
    if "office" in avg.columns:
        print("\nCoverage by office:")
        print(avg.groupby("office")["race_id"].count().to_string())

    # Top competitive races (closest to 50%)
    if "implied_prob_avg" in avg.columns:
        avg["competitiveness"] = (avg["implied_prob_avg"] - 0.5).abs()
        competitive = avg.nsmallest(10, "competitiveness")[
            ["race_id", "state", "office", "implied_prob_avg", "sources", "n_sources"]
        ]
        print("\nTop 10 most competitive races (closest to 50/50):")
        print(competitive.to_string(index=False))


if __name__ == "__main__":
    run()
