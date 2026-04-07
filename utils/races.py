"""
Canonical race list for the 2026 election cycle.

Race ID format: {year}-{office}-{state_abbrev}[-{district}]
  Examples:
    2026-SEN-PA          Pennsylvania Senate
    2026-GOV-TX          Texas Governor
    2026-H-PA-07         Pennsylvania's 7th Congressional District

Every scraper normalizes its output to these race_ids so data from
different sources can be joined cleanly.

Sources used to build this list:
  - Senate: https://en.wikipedia.org/wiki/2026_United_States_Senate_elections
  - Governor: https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections
  - House: All 435 districts (use Ballotpedia or official sources for incumbents)

TODO: Verify completeness against official sources. Special elections not included yet.
TODO: Add candidate fields once filing deadlines pass (varies by state, most by spring 2026).
TODO: Add Cook/Sabato/CPVI rating fields for competitiveness filtering.
"""

from dataclasses import dataclass, field
from typing import Optional

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


@dataclass
class Race:
    race_id: str
    year: int
    office: str          # SEN, GOV, H (house)
    state: str           # full state name
    state_abbrev: str
    district: Optional[str] = None    # House only, e.g. "07"
    incumbent_party: Optional[str] = None   # D, R, I
    incumbent_name: Optional[str] = None
    # TODO: add cook_rating, sabato_rating once available


# ---------------------------------------------------------------------------
# 2026 Senate races (Class 2 — 33 seats)
# Source: https://en.wikipedia.org/wiki/2026_United_States_Senate_elections
# ---------------------------------------------------------------------------
SENATE_RACES_2026 = [
    Race("2026-SEN-AK", 2026, "SEN", "Alaska", "AK", incumbent_party="R", incumbent_name="Dan Sullivan"),
    Race("2026-SEN-AL", 2026, "SEN", "Alabama", "AL", incumbent_party="R", incumbent_name="Tommy Tuberville"),
    Race("2026-SEN-AR", 2026, "SEN", "Arkansas", "AR", incumbent_party="R", incumbent_name="Tom Cotton"),
    Race("2026-SEN-CO", 2026, "SEN", "Colorado", "CO", incumbent_party="D", incumbent_name="John Hickenlooper"),
    Race("2026-SEN-DE", 2026, "SEN", "Delaware", "DE", incumbent_party="D", incumbent_name="Chris Coons"),
    Race("2026-SEN-GA", 2026, "SEN", "Georgia", "GA", incumbent_party="D", incumbent_name="Jon Ossoff"),
    Race("2026-SEN-HI", 2026, "SEN", "Hawaii", "HI", incumbent_party="D", incumbent_name="Brian Schatz"),
    Race("2026-SEN-IA", 2026, "SEN", "Iowa", "IA", incumbent_party="R", incumbent_name="Joni Ernst"),
    Race("2026-SEN-ID", 2026, "SEN", "Idaho", "ID", incumbent_party="R", incumbent_name="Mike Crapo"),
    Race("2026-SEN-IL", 2026, "SEN", "Illinois", "IL", incumbent_party="D", incumbent_name="Dick Durbin"),  # retiring
    Race("2026-SEN-KS", 2026, "SEN", "Kansas", "KS", incumbent_party="R", incumbent_name="Jerry Moran"),
    Race("2026-SEN-KY", 2026, "SEN", "Kentucky", "KY", incumbent_party="R", incumbent_name="Mitch McConnell"),  # retiring
    Race("2026-SEN-LA", 2026, "SEN", "Louisiana", "LA", incumbent_party="R", incumbent_name="Bill Cassidy"),
    Race("2026-SEN-ME", 2026, "SEN", "Maine", "ME", incumbent_party="R", incumbent_name="Susan Collins"),
    Race("2026-SEN-MI", 2026, "SEN", "Michigan", "MI", incumbent_party="D", incumbent_name="Gary Peters"),  # retiring
    Race("2026-SEN-MN", 2026, "SEN", "Minnesota", "MN", incumbent_party="D", incumbent_name="Tina Smith"),
    Race("2026-SEN-MS", 2026, "SEN", "Mississippi", "MS", incumbent_party="R", incumbent_name="Roger Wicker"),
    Race("2026-SEN-MT", 2026, "SEN", "Montana", "MT", incumbent_party="R", incumbent_name="Steve Daines"),
    Race("2026-SEN-NC", 2026, "SEN", "North Carolina", "NC", incumbent_party="R", incumbent_name="Thom Tillis"),
    Race("2026-SEN-NE", 2026, "SEN", "Nebraska", "NE", incumbent_party="R", incumbent_name="Deb Fischer"),
    Race("2026-SEN-NH", 2026, "SEN", "New Hampshire", "NH", incumbent_party="D", incumbent_name="Jeanne Shaheen"),  # retiring
    Race("2026-SEN-NJ", 2026, "SEN", "New Jersey", "NJ", incumbent_party="D", incumbent_name="Cory Booker"),
    Race("2026-SEN-NM", 2026, "SEN", "New Mexico", "NM", incumbent_party="D", incumbent_name="Martin Heinrich"),
    Race("2026-SEN-OR", 2026, "SEN", "Oregon", "OR", incumbent_party="D", incumbent_name="Jeff Merkley"),
    Race("2026-SEN-OK", 2026, "SEN", "Oklahoma", "OK", incumbent_party="R", incumbent_name="James Lankford"),
    Race("2026-SEN-RI", 2026, "SEN", "Rhode Island", "RI", incumbent_party="D", incumbent_name="Jack Reed"),
    Race("2026-SEN-SC", 2026, "SEN", "South Carolina", "SC", incumbent_party="R", incumbent_name="Lindsey Graham"),
    Race("2026-SEN-SD", 2026, "SEN", "South Dakota", "SD", incumbent_party="R", incumbent_name="John Thune"),
    Race("2026-SEN-TN", 2026, "SEN", "Tennessee", "TN", incumbent_party="R", incumbent_name="Marsha Blackburn"),
    Race("2026-SEN-TX", 2026, "SEN", "Texas", "TX", incumbent_party="R", incumbent_name="John Cornyn"),
    Race("2026-SEN-VA", 2026, "SEN", "Virginia", "VA", incumbent_party="D", incumbent_name="Mark Warner"),
    Race("2026-SEN-WA", 2026, "SEN", "Washington", "WA", incumbent_party="D", incumbent_name="Patty Murray"),  # retiring
    Race("2026-SEN-WY", 2026, "SEN", "Wyoming", "WY", incumbent_party="R", incumbent_name="John Barrasso"),
]

# ---------------------------------------------------------------------------
# 2026 Gubernatorial races
# Source: https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections
# TODO: Verify full list — approximately 36 governorships up in 2026
# ---------------------------------------------------------------------------
GOVERNOR_RACES_2026 = [
    Race("2026-GOV-AL", 2026, "GOV", "Alabama", "AL", incumbent_party="R"),
    Race("2026-GOV-AK", 2026, "GOV", "Alaska", "AK", incumbent_party="R"),
    Race("2026-GOV-AZ", 2026, "GOV", "Arizona", "AZ", incumbent_party="D"),
    Race("2026-GOV-AR", 2026, "GOV", "Arkansas", "AR", incumbent_party="R"),
    Race("2026-GOV-CA", 2026, "GOV", "California", "CA", incumbent_party="D"),
    Race("2026-GOV-CO", 2026, "GOV", "Colorado", "CO", incumbent_party="D"),
    Race("2026-GOV-CT", 2026, "GOV", "Connecticut", "CT", incumbent_party="D"),
    Race("2026-GOV-FL", 2026, "GOV", "Florida", "FL", incumbent_party="R"),
    Race("2026-GOV-GA", 2026, "GOV", "Georgia", "GA", incumbent_party="R"),
    Race("2026-GOV-HI", 2026, "GOV", "Hawaii", "HI", incumbent_party="D"),
    Race("2026-GOV-ID", 2026, "GOV", "Idaho", "ID", incumbent_party="R"),
    Race("2026-GOV-IL", 2026, "GOV", "Illinois", "IL", incumbent_party="D"),
    Race("2026-GOV-IA", 2026, "GOV", "Iowa", "IA", incumbent_party="R"),
    Race("2026-GOV-KS", 2026, "GOV", "Kansas", "KS", incumbent_party="D"),
    Race("2026-GOV-MA", 2026, "GOV", "Massachusetts", "MA", incumbent_party="R"),
    Race("2026-GOV-MD", 2026, "GOV", "Maryland", "MD", incumbent_party="R"),
    Race("2026-GOV-ME", 2026, "GOV", "Maine", "ME", incumbent_party="D"),
    Race("2026-GOV-MI", 2026, "GOV", "Michigan", "MI", incumbent_party="D"),
    Race("2026-GOV-MN", 2026, "GOV", "Minnesota", "MN", incumbent_party="D"),
    Race("2026-GOV-NE", 2026, "GOV", "Nebraska", "NE", incumbent_party="R"),
    Race("2026-GOV-NV", 2026, "GOV", "Nevada", "NV", incumbent_party="D"),
    Race("2026-GOV-NH", 2026, "GOV", "New Hampshire", "NH", incumbent_party="R"),
    Race("2026-GOV-NM", 2026, "GOV", "New Mexico", "NM", incumbent_party="D"),
    Race("2026-GOV-NY", 2026, "GOV", "New York", "NY", incumbent_party="D"),
    Race("2026-GOV-OH", 2026, "GOV", "Ohio", "OH", incumbent_party="R"),
    Race("2026-GOV-OK", 2026, "GOV", "Oklahoma", "OK", incumbent_party="R"),
    Race("2026-GOV-OR", 2026, "GOV", "Oregon", "OR", incumbent_party="D"),
    Race("2026-GOV-PA", 2026, "GOV", "Pennsylvania", "PA", incumbent_party="D"),
    Race("2026-GOV-RI", 2026, "GOV", "Rhode Island", "RI", incumbent_party="D"),
    Race("2026-GOV-SC", 2026, "GOV", "South Carolina", "SC", incumbent_party="R"),
    Race("2026-GOV-SD", 2026, "GOV", "South Dakota", "SD", incumbent_party="R"),
    Race("2026-GOV-TN", 2026, "GOV", "Tennessee", "TN", incumbent_party="R"),
    Race("2026-GOV-TX", 2026, "GOV", "Texas", "TX", incumbent_party="R"),
    Race("2026-GOV-VT", 2026, "GOV", "Vermont", "VT", incumbent_party="R"),
    Race("2026-GOV-WI", 2026, "GOV", "Wisconsin", "WI", incumbent_party="D"),
    Race("2026-GOV-WY", 2026, "GOV", "Wyoming", "WY", incumbent_party="R"),
    # TODO: verify complete list — some states may be missing or have off-cycle elections
]

# ---------------------------------------------------------------------------
# House races — all 435 districts
# TODO: Populate this. Recommended approach:
#   1. Fetch from Ballotpedia's structured data or Cook Political Report
#   2. Or use the @unitedstates/congress-legislators dataset on GitHub
#      https://github.com/unitedstates/congress-legislators
#   For now, generate placeholders programmatically.
# ---------------------------------------------------------------------------

# Seat counts per state (apportionment after 2020 census)
HOUSE_SEATS = {
    "AL": 7, "AK": 1, "AZ": 9, "AR": 4, "CA": 52, "CO": 8, "CT": 5,
    "DE": 1, "FL": 28, "GA": 14, "HI": 2, "ID": 2, "IL": 17, "IN": 9,
    "IA": 4, "KS": 4, "KY": 6, "LA": 6, "ME": 2, "MD": 8, "MA": 9,
    "MI": 13, "MN": 8, "MS": 4, "MO": 8, "MT": 2, "NE": 3, "NV": 4,
    "NH": 2, "NJ": 12, "NM": 3, "NY": 26, "NC": 14, "ND": 1, "OH": 15,
    "OK": 5, "OR": 6, "PA": 17, "RI": 2, "SC": 7, "SD": 1, "TN": 9,
    "TX": 38, "UT": 4, "VT": 1, "VA": 11, "WA": 10, "WV": 2, "WI": 8,
    "WY": 1,
}


def generate_house_races(year: int = 2026) -> list[Race]:
    """Generate placeholder Race objects for all 435 House districts."""
    state_name_by_abbrev = {v: k for k, v in STATE_ABBREVS.items()}
    races = []
    for abbrev, n_seats in HOUSE_SEATS.items():
        state_name = state_name_by_abbrev.get(abbrev, abbrev)
        for district in range(1, n_seats + 1):
            district_str = f"{district:02d}"
            race_id = f"{year}-H-{abbrev}-{district_str}"
            races.append(Race(
                race_id=race_id,
                year=year,
                office="H",
                state=state_name,
                state_abbrev=abbrev,
                district=district_str,
                # TODO: add incumbent_party, incumbent_name from data source
            ))
    return races


HOUSE_RACES_2026 = generate_house_races(2026)

# ---------------------------------------------------------------------------
# Combined lookup
# ---------------------------------------------------------------------------
ALL_RACES_2026: list[Race] = SENATE_RACES_2026 + GOVERNOR_RACES_2026 + HOUSE_RACES_2026
RACE_BY_ID: dict[str, Race] = {r.race_id: r for r in ALL_RACES_2026}


def get_race(race_id: str) -> Race:
    if race_id not in RACE_BY_ID:
        raise KeyError(f"Unknown race_id: {race_id}")
    return RACE_BY_ID[race_id]


if __name__ == "__main__":
    print(f"Senate races: {len(SENATE_RACES_2026)}")
    print(f"Governor races: {len(GOVERNOR_RACES_2026)}")
    print(f"House races: {len(HOUSE_RACES_2026)}")
    print(f"Total: {len(ALL_RACES_2026)}")
