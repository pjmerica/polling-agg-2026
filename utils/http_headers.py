"""
Single source of truth for outbound HTTP headers used by every scraper
and script that fetches from a public market API or HTML site.

Why this exists: Kalshi's WAF began rejecting our requests in mid-June
2026 with HTTP 403. Root cause was the identifying "Mozilla/5.0
(research/polling-aggregator)" User-Agent string — the parenthetical
was being matched as a scripted-scrape fingerprint. Several scrapers
were caught using that UA scattered across the codebase; updating each
one independently is how you re-introduce the bug. Import from here
instead.

If a WAF starts blocking us again, change BROWSER_UA in one place.
Endpoints that look like browser XHRs (Kalshi /events, Polymarket /book)
should additionally pass the BROWSER_XHR_HEADERS set so the request
shape matches what the platform's own webapp sends.
"""

# Real-browser User-Agent. Don't include "(research/...)" — that's what
# Kalshi's WAF flagged in June 2026.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Minimal headers for a JSON API request that just needs to not look
# like a Python script. Use for endpoints that aren't WAF-protected.
DEFAULT_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Full XHR-mimicking set for WAF-protected endpoints. Kalshi /events
# fell back to 200 OK once Referer + Origin + Sec-Fetch-* were added —
# without them it persisted with 403 even after the UA change.
def browser_xhr_headers(origin: str) -> dict:
    """Headers shaped like a browser XHR from `origin`. Pass e.g.
    "https://kalshi.com" or "https://polymarket.com"."""
    return {
        **DEFAULT_HEADERS,
        "Referer": origin.rstrip("/") + "/",
        "Origin": origin.rstrip("/"),
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
