"""
RealClearPolitics polling data scraper.

STATUS: RCP blocks all programmatic access (returns 403 for all paths including
the main domain). Their anti-scraping is aggressive — they block on IP + UA.

Options to get RCP data:
  1. MANUAL EXPORT (recommended short term):
     - Visit https://www.realclearpolitics.com/epolls/2026/senate/ in browser
     - Open DevTools -> Network -> filter XHR/Fetch
     - Reload the page; look for requests matching: /epolls/json/XXXXX_latest.js
     - Copy those URLs and paste them into RCP_RACE_URLS below
     - Then run: python scrapers/realclearpolitics.py --fetch-from-urls

  2. SELENIUM (medium term):
     - Use selenium with a real browser to bypass 403
     - pip install selenium
     - Needs chromedriver; or use playwright

  3. THIRD-PARTY MIRROR:
     - Wikipedia election articles often embed RCP averages
     - Some datasets on GitHub archive historical RCP data

JSON format (verified for 2024 cycle, likely stable):
  URL: https://www.realclearpolitics.com/epolls/json/{race_id}_latest.js?{timestamp}
  Response is JSONP wrapped: rcview({...}) or plain JSON depending on race
  Key fields: poll[].pollster, poll[].start_date, poll[].end_date,
              poll[].sample, poll[].moe, poll[].candidates[{name, party, value}]
"""

import time
import requests
import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research/polling-aggregator)",
    "Accept": "application/json, text/javascript, */*",
    "Referer": "https://www.realclearpolitics.com/",
}

# TODO: Populate this by scraping the RCP 2026 race index pages
# Format: {race_id_string: rcp_numeric_id}
# Example from 2024: {"2024-SEN-PA": 7322, "2024-SEN-AZ": 7325}
RCP_RACE_IDS: dict[str, int] = {
    # TODO: fill in 2026 race IDs
}

BASE_POLL_URL = "https://www.realclearpolitics.com/epolls/json/{race_id}_latest.js"


def fetch_race_polls(rcp_id: int) -> list[dict]:
    """
    Fetch all polls for a single RCP race ID.

    Returns list of poll dicts.
    TODO: Implement once race IDs are known.
    """
    url = BASE_POLL_URL.format(race_id=rcp_id)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # RCP returns JSONP-ish format: sometimes wrapped in a callback
    # May need to strip the wrapper before parsing
    # TODO: handle JSONP wrapper if present
    data = resp.json()
    return data.get("poll", [])


def parse_polls(raw_polls: list[dict], race_id: str) -> pd.DataFrame:
    """
    Parse raw RCP poll list into standard schema.

    TODO: Map RCP fields to standard schema:
      race_id, state, office, year, pollster, grade, sample_size,
      methodology, start_date, end_date, candidate, party, pct

    RCP raw fields typically include:
      id, type, pollster, start_date, end_date, sample, moe,
      link, candidates (list of {name, party, value})
    """
    # TODO: implement parsing
    raise NotImplementedError("parse_polls not yet implemented")


def scrape_race_index(year: int = 2026) -> dict[str, int]:
    """
    Scrape the RCP race index page to find all race IDs for a given year.

    TODO: Implement this first — it gives you the RCP numeric IDs needed
    to call fetch_race_polls(). Look for <a> tags linking to individual
    race pages; the URL contains the numeric ID.

    Example URL pattern:
      https://www.realclearpolitics.com/epolls/2026/senate/pa/pennsylvania_senate_race-XXXX.html
      The XXXX at the end is the race ID.
    """
    raise NotImplementedError("scrape_race_index not yet implemented")


def run():
    """Fetch all RCP polling data and save raw CSVs."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not RCP_RACE_IDS:
        print("RCP_RACE_IDS is empty — run scrape_race_index() first to populate it.")
        print("TODO: implement scrape_race_index() then populate RCP_RACE_IDS")
        return

    all_polls = []
    for race_id, rcp_id in RCP_RACE_IDS.items():
        print(f"Fetching RCP polls for {race_id} (id={rcp_id})...")
        polls = fetch_race_polls(rcp_id)
        df = parse_polls(polls, race_id)
        all_polls.append(df)
        time.sleep(1.5)  # be polite

    combined = pd.concat(all_polls, ignore_index=True)
    combined.to_csv(RAW_DATA_DIR / "rcp_polls.csv", index=False)
    print(f"Saved {len(combined)} rows to data/raw/rcp_polls.csv")


if __name__ == "__main__":
    run()
