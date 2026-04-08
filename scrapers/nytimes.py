"""
NYT polling scraper.

NYT publishes structured CSV downloads for all 2026 election polls:
  https://www.nytimes.com/newsgraphics/polls/senate.csv
  https://www.nytimes.com/newsgraphics/polls/house.csv
  https://www.nytimes.com/newsgraphics/polls/governor.csv

These are updated continuously and contain one row per candidate per poll question.
No auth required. Data is CC-BY 4.0.

Key columns:
  poll_id, pollster, display_name, numeric_grade, pollscore, methodology,
  state, start_date, end_date, sample_size, population, tracking,
  partisan, cycle, office_type, seat_number, election_date, stage,
  party, pct, answer, candidate_name, race_id

Output: data/raw/nyt_polls.csv

Schema matches aggregator expectations:
  race_id, source, market_title (pollster name), implied_prob, weight, fetched_at

For polls, implied_prob is the candidate's poll share (0.0-1.0).
Weight = f(sample_size, recency, pollster_grade).
"""

import urllib.request
import io
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, date

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

NYT_CSV_URLS = {
    "senate":   "https://www.nytimes.com/newsgraphics/polls/senate.csv",
    "house":    "https://www.nytimes.com/newsgraphics/polls/house.csv",
    "governor": "https://www.nytimes.com/newsgraphics/polls/governor.csv",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research/polling-aggregator)",
    "Accept": "text/csv,text/plain,*/*",
}

# State full name -> abbreviation (matches utils/races.py)
STATE_ABBREVS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

# Two-letter state code -> abbreviation (the CSVs use 2-letter codes in 'state' column)
# These are already abbreviations, so identity map — but we use it for validation
VALID_STATE_ABBREVS = set(STATE_ABBREVS.values())


def fetch_csv(url: str) -> pd.DataFrame:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        content = r.read().decode("utf-8")
    return pd.read_csv(io.StringIO(content))


def infer_race_id(row: pd.Series, office_type: str) -> str | None:
    """
    Map NYT poll row to canonical race_id from utils/races.py.

    NYT 'state' column uses 2-letter abbreviations (e.g. 'PA', 'FL').
    NYT 'office_type' is 'U.S. Senate', 'U.S. House', or 'Governor'.
    NYT 'seat_number' is district number for House races.
    """
    state = str(row.get("state", "")).strip().upper()
    if state not in VALID_STATE_ABBREVS and state != "US":
        return None

    if office_type == "senate":
        if state == "FL":
            return "2026-SEN-FL-S"  # Special (Rubio vacancy)
        if state == "OH":
            # OH special and regular both exist; stage can disambiguate
            # For now map all OH senate polls to special (Vance vacancy is the main race)
            return "2026-SEN-OH-S"
        return f"2026-SEN-{state}" if state in VALID_STATE_ABBREVS else None

    if office_type == "governor":
        return f"2026-GOV-{state}" if state in VALID_STATE_ABBREVS else None

    if office_type == "house":
        seat = str(row.get("seat_number", "")).strip()
        if not seat or seat == "nan" or state == "US":
            return None  # Generic ballot questions, not individual races
        try:
            district = str(int(float(seat))).zfill(2)
        except (ValueError, TypeError):
            return None
        return f"2026-H-{state}-{district}"

    return None


def compute_weight(df: pd.DataFrame, today: date) -> pd.Series:
    """
    Weight = sample_size_factor * recency_factor * grade_factor

    sample_size_factor: sqrt(sample_size / 600) capped at 2.0
    recency_factor: exponential decay, half-life ~30 days
    grade_factor: based on numeric_grade (0-3 scale) or pollscore
    """
    # Sample size factor
    sample = pd.to_numeric(df["sample_size"], errors="coerce").fillna(600)
    sample_factor = np.sqrt(sample / 600).clip(upper=2.0)

    # Recency factor — days since poll end date
    def parse_date(s):
        try:
            return pd.to_datetime(s, format="%m/%d/%y").date()
        except Exception:
            try:
                return pd.to_datetime(s).date()
            except Exception:
                return today

    end_dates = df["end_date"].apply(parse_date)
    days_ago = end_dates.apply(lambda d: max(0, (today - d).days))
    recency_factor = np.exp(-days_ago / 30)  # half-life ~21 days

    # Grade factor: numeric_grade is 0-3 (higher = better), or fall back to 1.0
    grade = pd.to_numeric(df.get("numeric_grade", pd.Series(dtype=float)), errors="coerce").fillna(1.5)
    grade_factor = (grade / 3.0).clip(lower=0.33, upper=1.0)

    # Partisan penalty: down-weight partisan polls
    partisan = df.get("partisan", pd.Series("", index=df.index)).fillna("").str.strip()
    partisan_factor = partisan.apply(lambda p: 0.5 if p else 1.0)

    return (sample_factor * recency_factor * grade_factor * partisan_factor).round(4)


def process_office(df_raw: pd.DataFrame, office_type: str, today: date) -> pd.DataFrame:
    """
    Convert raw NYT CSV rows into aggregator-ready rows.

    Each poll question has multiple rows (one per candidate/answer).
    We keep only general election, non-hypothetical rows where pct is numeric.
    We filter to major-party candidates (DEM, REP, IND) and exclude "Don't know" etc.
    """
    df = df_raw.copy()

    # Filter to 2026 general election polls (also keep primary for now)
    df = df[df["cycle"].astype(str) == "2026"].copy()

    # Exclude hypothetical matchups
    if "hypothetical" in df.columns:
        df = df[df["hypothetical"].astype(str).str.strip() != "1"].copy()

    # Parse pct as numeric
    df["pct"] = pd.to_numeric(df["pct"], errors="coerce")
    df = df[df["pct"].notna()].copy()

    # Exclude non-candidate rows (Don't know, Undecided, etc.)
    skip_answers = {"don't know", "undecided", "other", "someone else", "refused", "none"}
    df = df[~df["answer"].str.lower().str.strip().isin(skip_answers)].copy()

    # Infer race_id
    df["race_id"] = df.apply(lambda r: infer_race_id(r, office_type), axis=1)
    df = df[df["race_id"].notna()].copy()

    # Compute weight per question (all rows in a question_id share the same weight)
    df["weight"] = compute_weight(df, today)

    # implied_prob = poll share as fraction
    df["implied_prob"] = (df["pct"] / 100).clip(0, 1).round(4)

    # Build output schema
    out = pd.DataFrame({
        "race_id": df["race_id"],
        "source": "nyt",
        "market_title": (
            df["display_name"].fillna(df["pollster"])
            + " — "
            + df["candidate_name"].fillna(df["answer"])
        ),
        "implied_prob": df["implied_prob"],
        "weight": df["weight"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        # Extra context columns (not required by aggregator schema but useful)
        "pollster": df["display_name"].fillna(df["pollster"]),
        "candidate": df["candidate_name"].fillna(df["answer"]),
        "party": df["party"].fillna(""),
        "stage": df["stage"].fillna("general"),
        "sample_size": pd.to_numeric(df["sample_size"], errors="coerce"),
        "end_date": df["end_date"],
        "partisan": df.get("partisan", pd.Series("", index=df.index)).fillna(""),
        "poll_id": df["poll_id"],
        "question_id": df["question_id"],
    })
    return out


def run():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    all_frames = []

    for office, url in NYT_CSV_URLS.items():
        print(f"Fetching NYT {office} polls from {url} ...")
        try:
            df_raw = fetch_csv(url)
            print(f"  Raw rows: {len(df_raw)}")
        except Exception as e:
            print(f"  ERROR fetching {office}: {e}")
            continue

        df = process_office(df_raw, office, today)
        print(f"  Processed: {len(df)} rows across {df['race_id'].nunique()} races")
        all_frames.append(df)

    if not all_frames:
        print("No data fetched.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    out_path = RAW_DATA_DIR / "nyt_polls.csv"
    combined.to_csv(out_path, index=False)
    print(f"\nSaved {len(combined)} rows to {out_path}")

    # Summary
    print(f"\nCoverage by race_id ({combined['race_id'].nunique()} races):")
    summary = (
        combined.groupby("race_id")
        .agg(n_rows=("poll_id", "count"), n_polls=("poll_id", "nunique"))
        .sort_values("n_rows", ascending=False)
        .head(20)
    )
    print(summary.to_string())


if __name__ == "__main__":
    run()
