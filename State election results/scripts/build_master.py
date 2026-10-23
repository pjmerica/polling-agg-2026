"""Build MASTER.md: the one file to read. Stitches together, per state, the rules and history from
STATE_BY_STATE.md, that state's swing data from the swings analysis and its county benchmarks,
around the text in scripts/master_template.md.

Tokens in the template:
  {{GUIDE:<n>}}     a numbered top-level section of STATE_BY_STATE.md (e.g. 1, 2, 2b, 2c, 12, 13, 14)
  {{STATE:<slug>}}  that state's STATE_BY_STATE.md section plus its swing tables and county benchmarks
  {{PACE_ALL}} {{EARLY_EDAY}}   cross-state tables from the swings analysis
  {{COUNTY_BACKTEST}}           how county benchmarks did in past races (county_benchmarks.py)

County benchmarks come from data/processed/county_benchmarks.json (run county_benchmarks.py first).
Runs the guide builder too, so everything is regenerated from data. render(html=True) is the
dashboard page's version (build_election_night.py).

    py "State election results/scripts/build_master.py"
"""
import csv
import os
import re

import build_state_guide
import build_swings_report as sw
import county_benchmarks as cb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SLUG = {"georgia": "GA", "ohio": "OH", "michigan": "MI", "texas": "TX", "kansas": "KS",
        "maine": "ME", "iowa": "IA", "nebraska": "NE", "alaska": "AK", "nevada": "NV", "oregon": "OR"}


def guide_sections(text):
    parts = re.split(r"(?m)^## (\S+?)\. ", text)
    # parts: [preamble, num, body, num, body, ...]
    out = {}
    for num, body in zip(parts[1::2], parts[2::2]):
        title, _, rest = body.partition("\n")
        out[num] = (title.strip(), rest.strip().rstrip("-").strip())
    return out


def swing_block(rows, code, slug):
    rs = [r for r in rows if r["state"] == code]
    blocks = [("How fast it counts and how far it moves (all contested general-election races, median)", sw.state_pace(rs)),
              ("Biggest moves in competitive races", sw.big_swings(rs)),
              ("Every race where the leader at 2 hours or at midnight lost", sw.comebacks(rs)),
              ("Races that moved 1.5+ pts after 6 am ET", sw.late_movers(rs))]
    if code != "AK":  # Alaska's last 2020 archive copy predates its absentee count
        blocks.append(("Where the late vote came from (2020, county detail)", sw.county_2020([slug])))
    blocks.append(("2026 primaries, runoffs and specials", sw.primaries(rs)))
    out = []
    for title, table in blocks:
        n_rows = table.count("\n| ") - 1  # data rows below the header/separator
        if n_rows < 1 or not table.strip():
            continue
        out.append(f"#### {title}\n\n{table}\n")
    return "\n".join(out)


def render(html=False):
    """MASTER.md's text. html=True: model and market numbers become live spans, and each county table
    a placeholder for the page's interactive version."""
    rows = sw.load()
    sections = guide_sections(build_state_guide.render(fill=False))
    tmpl = open(os.path.join(HERE, "master_template.md"), encoding="utf-8").read()

    def guide(m):
        title, body = sections[m.group(1)]
        return f"{body}"

    def state(m):
        slug = m.group(1)
        num = next(n for n, (t, _) in sections.items() if t.lower().startswith(slug))
        title, body = sections[num]
        name = title.split(":")[0]
        return (f"## {title}\n\n{body}\n\n### The swing data: {name}\n\n"
                f"{swing_block(rows, SLUG[slug], slug)}\n\n### County benchmarks: {name}\n\n"
                f"{cb.state_markdown(slug, html=html)}\n\n---\n")

    out = re.sub(r"\{\{GUIDE:(\w+)\}\}", guide, tmpl)
    out = re.sub(r"\{\{STATE:(\w+)\}\}", state, out)
    out = out.replace("{{PACE_ALL}}", sw.state_pace(rows)).replace("{{EARLY_EDAY}}", sw.early_eday(rows))
    out = out.replace("{{COUNTY_BACKTEST}}", cb.backtest_markdown())
    out = build_state_guide.fill_numbers(out, html=html).replace("{{N_RACES}}", str(len(rows)))
    # national volatility ranks (scripts/volatility.py)
    vol = list(csv.DictReader(open(os.path.join(ROOT, "data", "processed", "volatility_states.csv"), encoding="utf-8")))
    vol.sort(key=lambda x: int(x["rank"]))
    out = out.replace("{{VOL_TOP10}}", ", ".join(x["name"] for x in vol[:10]))
    out = out.replace("{{VOL_OURS}}", ", ".join(f"{x['name']} {x['rank']}" for x in vol if x["competitive"] == "True"))
    out = out.replace("{{VOL_N}}", str(len(vol)))
    assert "{{" not in out, "unfilled token"
    return out


def main():
    build_state_guide.main()
    out = render()
    with open(os.path.join(ROOT, "MASTER.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote MASTER.md")


if __name__ == "__main__":
    main()
