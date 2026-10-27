"""The election-night guide as a dashboard page: docs/election-night.html and
docs/election_night_counties.js.

The page is the master guide (build_master.render(html=True)) rendered to HTML inside
scripts/election_night_template.html, with:
  - model and market numbers that refresh from docs/forecast_data.js when the page loads (CI's model
    refresh rewrites that file daily, so the numbers stay current without rebuilding the page);
  - a live table of the 14 races;
  - each state's county benchmarks as an interactive table: a slider for the statewide result, and
    boxes that turn a finished county's result into the statewide margin it implies.

Run after the inputs it reads are fresh:
    py "State election results/scripts/early_vote.py"          (ballots already cast)
    py "State election results/scripts/county_benchmarks.py"   (county data)
    py "State election results/scripts/build_master.py"        (MASTER.md and STATE_BY_STATE.md)
    py "State election results/scripts/build_election_night.py"
"""
import datetime as dt
import html
import json
import os
import re

from markdown_it import MarkdownIt

import build_master
import build_state_guide as g
from census_blocs import BLOCS
from state_curves import CLOSE_ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DOCS = os.path.join(ROOT, "..", "docs")


def close_label(hours):
    if hours >= 24:
        return "midnight"
    h, m = int(hours), int(round((hours - int(hours)) * 60))
    return f"{h - 12 if h > 12 else h}:{m:02d} pm"


def slugify(text, seen):
    s = re.sub(r"[^a-z0-9]+", "-", html.unescape(re.sub(r"<[^>]+>", "", text)).lower()).strip("-")[:60] or "s"
    out, i = s, 2
    while out in seen:
        out, i = f"{s}-{i}", i + 1
    seen.add(out)
    return out


def content():
    text = build_master.render(html=True)
    # the page has its own title, intro and contents
    text = text[text.index("## 1. The states at a glance"):]
    # numbered sections are all top level on the page (MASTER.md mixes # and ##)
    text = re.sub(r"(?m)^## (\d+)\. ", r"# \1. ", text)
    body = MarkdownIt("commonmark", {"html": True}).enable("table").render(text)
    seen, toc = {"live", "doc", "toc", "asof"}, []

    def heading(m):
        lvl, inner = int(m.group(1)), m.group(2)
        hid = slugify(inner, seen)
        if lvl <= 2:
            toc.append((lvl, hid, html.unescape(re.sub(r"<[^>]+>", "", inner))))
        return f'<h{lvl} id="{hid}">{inner}</h{lvl}>'

    body = re.sub(r"<h([1-4])>(.*?)</h\1>", heading, body)
    body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    nav = "".join(f'<a class="t{lvl}" href="#{hid}">{html.escape(t)}</a>' for lvl, hid, t in toc)
    return body, nav


def page_data():
    data = json.load(open(os.path.join(ROOT, "data", "processed", "county_benchmarks.json"), encoding="utf-8"))
    blocs = {s["slug"]: s["unit_blocs"] for s in
             json.load(open(os.path.join(ROOT, "data", "processed", "census_blocs.json"), encoding="utf-8"))["states"]}
    races = []
    for r in data["races"]:
        bl = "D" if r["bases"][0].startswith("2024 President") else g.PARTY.get(r["d"]["party"], "I")
        counties = []
        for c in r["counties"]:
            x = dict(f=c["f"], n=c["n"], w=round(c["w"], 6), L=round(c["L"], 4), b=round(c["b"][0], 1),
                     bl=blocs.get(r["slug"], {}).get(c["f"], ""))
            if "a" in c:
                x.update(a=round(c["a"], 4), la=round(c["la"], 4), le=round(c["le"], 4))
            if c.get("t_mid") is not None and c.get("t_six") is not None:
                x.update(tm=c["t_mid"], ts=c["t_six"])
            counties.append(x)
        races.append(dict(id=r["id"], state=r["state"], slug=r["slug"], seat=r["seat"], unit=r["unit"], d=r["d"], r=r["r"],
                          bases=r["bases"], types=r["types"], bl=bl, model_margin=r["model_margin"], bloc_order=BLOCS,
                          close=close_label(CLOSE_ET[r["slug"]]), counties=counties))
    return dict(built=data["built"], races=races)


def main():
    body, nav = content()
    built = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tmpl = open(os.path.join(HERE, "election_night_template.html"), encoding="utf-8").read()
    page = tmpl.replace("{{TOC}}", nav).replace("{{BUILT}}", built).replace("{{CONTENT}}", body)
    assert not re.search(r"\{\{[A-Z_]+\}\}", page), "unfilled token"
    with open(os.path.join(DOCS, "election-night.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    with open(os.path.join(DOCS, "election_night_counties.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("const ELECTION_NIGHT = " + json.dumps(page_data(), separators=(",", ":")) + ";\n")
    print(f"wrote docs/election-night.html ({len(page) // 1024} KB) and docs/election_night_counties.js")


if __name__ == "__main__":
    main()
