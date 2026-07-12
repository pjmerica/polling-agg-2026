"""Curated pollster-partisanship reference + normalizer.

WHY THIS EXISTS
The two poll feeds disagree and are internally inconsistent about which pollsters are
partisan:
  * NYT uses DEM/REP/IND/WFP/NPA; Wikipedia uses D/R/I.
  * Wikipedia's tag often reflects the SPONSOR of a specific poll, not the pollster's own
    lean, so the same pollster flips tags between rows (e.g. Public Policy Polling showing
    both D and I). A neutral pollster fielding a poll for a Democratic client got mislabeled.
  * Some well-known partisan firms carry no tag at all in one or both feeds.

This module is the single source of truth for a POLLSTER'S OWN partisan lean (its house
identity), independent of who sponsored any individual poll. `normalize_partisan(pollster,
feed_tag)` returns one of 'D' / 'R' / 'I' / '' using, in priority order:
  1. the curated REFERENCE below (hand-verified, wins when present),
  2. otherwise the feed tag, mapped to D/R/I (kept, since most feed tags are correct).

Sources for the reference: FiveThirtyEight pollster ratings' partisan-sponsor field, AAPOR
Transparency Initiative membership, and the pollsters' own public descriptions (campaign/
party firms vs. media/academic/independent). Reviewed 2026-07-10. Add rows as new firms
appear; keys are lowercased-alphanumeric so punctuation/spacing doesn't matter.
"""
import re

# pollster (any spelling) -> 'D' | 'R' | 'I'
# 'I' is used ONLY for firms that publicly brand as nonpartisan but are commonly *tagged*
# partisan by a feed in error, so the normalizer can actively CORRECT them to independent.
_RAW_REFERENCE = {
    # ---- Democratic firms (work primarily for Democratic/progressive clients) ----
    "Public Policy Polling": "D", "Impact Research": "D", "Change Research": "D",
    "Data for Progress": "D", "Tavern Research": "D", "GBAO": "D",
    "GBAO Strategies": "D", "Tulchin Research": "D", "Global Strategy Group": "D",
    "GQR": "D", "GQR Research": "D", "Lake Research Partners": "D",
    "Garin-Hart-Yang Research": "D", "Hart Research Associates": "D",
    "Normington Petts": "D", "Blueprint Polling": "D", "Blue Rose Research": "D",
    "Expedition Strategies": "D", "Fairbank, Maslin, Maullin, Metz & Associates": "D",
    "FM3 Research": "D", "Upswing Research": "D", "Clarity Campaign Labs": "D",
    "ALG Research": "D", "Beacon Research": "D", "Data for Progress (D)": "D",
    "Public Policy Polling (D)": "D",
    # ---- Republican firms (work primarily for Republican/conservative clients) ----
    "co/efficient": "R", "Trafalgar Group": "R", "McLaughlin & Associates": "R",
    "Cygnal": "R", "Echelon Insights": "R", "TIPP Insights": "R",
    "Peak Insights": "R", "Pulse Decision Science": "R", "Ragnar Research Partners": "R",
    "Fabrizio, Lee & Associates": "R", "InsiderAdvantage": "R", "Quantus Insights": "R",
    "Remington Research Group": "R", "OnMessage Inc.": "R", "WPA Intelligence": "R",
    "Public Opinion Strategies": "R", "The Tarrance Group": "R", "co/efficient (R)": "R",
    "Meeting Street Insights": "R", "National Research Inc.": "R", "Torchlight Strategies": "R",
    "Spry Strategies": "R", "Victory Insights": "R", "American Pulse Research & Polling": "R",
    "Kaplan Strategies": "R", "Opinion Diagnostics": "R", "Rasmussen Reports": "R",
    "Stratus Intelligence": "R", "Trafalgar Group (R)": "R",
    # ---- Independent / nonpartisan (branding-neutral; correct feed over-tags to I) ----
    "Emerson College": "I", "SurveyUSA": "I", "University of New Hampshire": "I",
    "Quinnipiac University": "I", "Marist College": "I", "Siena College": "I",
    "Monmouth University": "I", "Suffolk University": "I", "YouGov": "I",
    "The Economist / YouGov": "I", "Morning Consult": "I", "Ipsos": "I",
    "Data Orbital": "I", "Noble Predictive Insights": "I", "AtlasIntel": "I",
    "Marquette University Law School": "I", "Muhlenberg College": "I",
    "Fabrizio Ward": "R", "Beacon/Shaw": "I", "Mason-Dixon": "I",
}


def _key(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


REFERENCE = {_key(k): v for k, v in _RAW_REFERENCE.items()}


def map_feed_tag(tag):
    """Any feed spelling (DEM/REP/IND/WFP/NPA/D/R/I) -> 'D' | 'R' | 'I' | ''."""
    t = str(tag).strip().upper()
    if not t:
        return ""
    if t.startswith("D"):
        return "D"
    if t.startswith("R"):
        return "R"
    if t.startswith(("I", "W", "N", "G", "L")):  # IND / WFP / NPA / Green / Lib -> independent/third
        return "I"
    return ""


def normalize_partisan(pollster, feed_tag=""):
    """A pollster's own lean: curated reference wins, else the mapped feed tag."""
    ref = REFERENCE.get(_key(pollster))
    if ref:
        return ref
    return map_feed_tag(feed_tag)


def audit(df):
    """Return a per-pollster audit frame comparing feed tags to the reference.
    df needs 'pollster' and 'partisan' columns. For diagnostics/AUDIT.md only."""
    import pandas as pd
    rows = []
    for pol, g in df.groupby("pollster"):
        feed = {map_feed_tag(t) for t in g["partisan"].fillna("") if map_feed_tag(t)}
        ref = REFERENCE.get(_key(pol), "")
        status = ("no-ref" if not ref else
                  "ok" if feed <= {ref} or not feed else
                  "CORRECTED")
        rows.append(dict(pollster=pol, n=len(g), feed_tags="".join(sorted(feed)) or "-",
                         reference=ref or "-", status=status))
    return pd.DataFrame(rows).sort_values("n", ascending=False)
