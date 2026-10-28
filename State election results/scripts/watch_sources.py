"""Watch for new sources on when results get reported, for the competitive-race states.

Searches Google News and Bing News RSS for AP "Decision Notes: What to expect" pieces and
election-night results-schedule announcements, and appends anything new to
sources/watch_log.csv. AP's general-election previews (title like "What to expect in Ohio
on Election Day" or "...general election") are flagged and listed in
sources/NEW_AP_GENERAL.md so they can be read and summarized into sources/README.md.

apnews.com blocks scripts, so this records title, date, outlet and link only.

    py "State election results/scripts/watch_sources.py"
"""
import csv
import datetime as dt
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "sources")
LOG = os.path.join(SRC, "watch_log.csv")
ALERT = os.path.join(SRC, "NEW_AP_GENERAL.md")
UA = {"User-Agent": "Mozilla/5.0"}

STATES = ["Alaska", "Georgia", "Ohio", "Kansas", "Texas", "Nebraska", "Maine", "Iowa", "Michigan",
          "Nevada", "Oregon", "South Carolina"]
# Largest / slowest-reporting jurisdictions (see the report), for results-schedule announcements
COUNTIES = ["Fulton County Georgia", "DeKalb County Georgia", "Franklin County Ohio", "Cuyahoga County",
            "Detroit", "Wayne County Michigan", "Oakland County Michigan", "Harris County", "Dallas County",
            "Tarrant County", "Johnson County Kansas", "Sedgwick County", "Douglas County Nebraska",
            "Lancaster County Nebraska", "Polk County Iowa", "Portland Maine",
            "Clark County Nevada", "Washoe County", "Multnomah County", "Washington County Oregon"]

QUERIES = [f'"AP Decision Notes" "what to expect" {s}' for s in STATES]
QUERIES += [f'"{c}" election results November 3 release update' for c in COUNTIES]
QUERIES += [f'{s} secretary of state election night results "November 3" when' for s in STATES]

PRIMARY = re.compile(r"primar|runoff|special|caucus", re.I)
AP_GENERAL = re.compile(r"what to expect", re.I)


def rss(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    for i in root.iter("item"):
        link = i.findtext("link") or ""
        if "bing.com" in link:  # Bing wraps the real URL in a redirect
            link = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url", [link])[0]
        src = i.find("source")
        yield dict(title=(i.findtext("title") or "").strip(), date=(i.findtext("pubDate") or "")[:16],
                   outlet=(src.text if src is not None else ""), link=link)


def main():
    os.makedirs(SRC, exist_ok=True)
    seen = set()
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            seen = {r["title"] for r in csv.DictReader(f)}
    new = []
    for q in QUERIES:
        qs = urllib.parse.quote(q)
        for url in (f"https://news.google.com/rss/search?q={qs}&hl=en-US&gl=US&ceid=US:en",
                    f"https://www.bing.com/news/search?q={qs}&format=rss&count=50"):
            try:
                items = list(rss(url))
            except Exception as e:
                print(f"query failed ({q[:40]}...): {e}")
                continue
            for it in items:
                if not it["title"] or it["title"] in seen:
                    continue
                if "2026" not in it["date"]:
                    continue
                seen.add(it["title"])
                it["query"] = q
                it["found_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
                it["ap_general"] = bool(AP_GENERAL.search(it["title"]) and "Decision Notes" in it["title"]
                                        and any(s in it["title"] for s in STATES)
                                        and not PRIMARY.search(it["title"]))
                new.append(it)
    write_header = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["found_utc", "date", "title", "outlet", "link", "query", "ap_general"])
        if write_header:
            w.writeheader()
        w.writerows(new)
    general = [n for n in new if n["ap_general"]]
    if general:
        with open(ALERT, "a", encoding="utf-8") as f:
            for n in general:
                f.write(f"- {n['found_utc']}: [{n['title']}]({n['link']}) ({n['date']})\n")
    print(f"{len(new)} new items, {len(general)} AP general-election previews")
    for n in general:
        print("  AP:", n["title"])


if __name__ == "__main__":
    main()
