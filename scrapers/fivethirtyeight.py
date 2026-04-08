"""
FiveThirtyEight / ABC News polling data scraper.

STATUS: DEAD AS OF 2026-04-07.
All CSV endpoints return HTML (200 with an HTML page, not CSV data).
538 appears to have discontinued their public data CSVs after ABC News acquired them.

URLs that no longer work:
  https://projects.fivethirtyeight.com/polls/data/senate_polls.csv
  https://projects.fivethirtyeight.com/polls/data/governor_polls.csv
  https://projects.fivethirtyeight.com/polls/data/house_polls.csv
  https://projects.fivethirtyeight.com/pollster-ratings/pollster-ratings.csv

Alternatives:
  - Nate Silver's Silver Bulletin (substack) may publish data separately
  - MIT Election Data and Science Lab (https://electionlab.mit.edu/data) has historical
  - Cook Political Report has ratings but not raw polls
  - The current primary structured polling source for this project is Kalshi (scrapers/kalshi.py)

This file is kept as a reference stub. Recheck in summer 2026 — 538 sometimes activates
data pipelines 6 months before election day.
"""

import requests
import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# TODO: Verify these URLs for the 2026 cycle
ENDPOINTS = {
    "senate": "https://projects.fivethirtyeight.com/polls/data/senate_polls.csv",
    "governor": "https://projects.fivethirtyeight.com/polls/data/governor_polls.csv",
    "house": "https://projects.fivethirtyeight.com/polls/data/house_polls.csv",
    "pollster_ratings": "https://projects.fivethirtyeight.com/pollster-ratings/pollster-ratings.csv",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research/polling-aggregator)"
}


def fetch_csv(url: str) -> pd.DataFrame:
    """Download a CSV from a URL and return as DataFrame."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    from io import StringIO
    return pd.read_csv(StringIO(resp.text))


def normalize_senate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize raw 538 senate CSV to standard schema.

    Standard columns we want:
      race_id, state, office, year, pollster, grade, sample_size,
      methodology, start_date, end_date, candidate, party, pct

    TODO: Implement column mapping once 2026 CSV schema is confirmed.
          2024 columns included: poll_id, pollster, pollster_rating_id,
          fte_grade, methodology, state, start_date, end_date, election_date,
          stage, party, answer, candidate_name, pct, sample_size, ...
    """
    # TODO: map raw columns to standard schema
    # TODO: add race_id using format: 2026-SEN-{state_abbrev}
    raise NotImplementedError("normalize_senate not yet implemented")


def normalize_governor(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Same as normalize_senate but for governor races.
    race_id format: 2026-GOV-{state_abbrev}
    """
    raise NotImplementedError("normalize_governor not yet implemented")


def normalize_house(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Same pattern for house races.
    race_id format: 2026-H-{state_abbrev}-{district_num:02d}
    """
    raise NotImplementedError("normalize_house not yet implemented")


def run():
    """Fetch all 538 polling data and save raw CSVs."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for race_type, url in ENDPOINTS.items():
        print(f"Fetching 538 {race_type} data...")
        # TODO: uncomment once URLs are verified
        # df = fetch_csv(url)
        # df.to_csv(RAW_DATA_DIR / f"538_{race_type}.csv", index=False)
        # print(f"  Saved {len(df)} rows to data/raw/538_{race_type}.csv")
        print(f"  TODO: verify URL for 2026 cycle: {url}")


if __name__ == "__main__":
    run()
