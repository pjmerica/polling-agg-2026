"""Build MASTER.md: the one file to read. Stitches together, per state, the rules and history from
STATE_BY_STATE.md and that state's swing data from the swings analysis, around the text in
scripts/master_template.md.

Tokens in the template:
  {{GUIDE:<n>}}     a numbered top-level section of STATE_BY_STATE.md (e.g. 1, 2, 2b, 12, 13, 14)
  {{STATE:<slug>}}  that state's STATE_BY_STATE.md section plus its swing tables
  {{PACE_ALL}} {{EARLY_EDAY}}   cross-state tables from the swings analysis

Runs both builders first, so everything is regenerated from data.

    py "State election results/scripts/build_master.py"
"""
import os
import re

import build_state_guide
import build_swings_report as sw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SLUG = {"georgia": "GA", "ohio": "OH", "michigan": "MI", "texas": "TX", "kansas": "KS",
        "maine": "ME", "iowa": "IA", "nebraska": "NE", "alaska": "AK"}


def guide_sections():
    text = open(os.path.join(ROOT, "STATE_BY_STATE.md"), encoding="utf-8").read()
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


def main():
    build_state_guide.main()
    rows = sw.load()
    sections = guide_sections()
    tmpl = open(os.path.join(HERE, "master_template.md"), encoding="utf-8").read()

    def guide(m):
        title, body = sections[m.group(1)]
        return f"{body}"

    def state(m):
        slug = m.group(1)
        num = next(n for n, (t, _) in sections.items() if t.lower().startswith(slug))
        title, body = sections[num]
        return (f"## {title}\n\n{body}\n\n### The swing data: {title.split(':')[0]}\n\n"
                f"{swing_block(rows, SLUG[slug], slug)}\n\n---\n")

    out = re.sub(r"\{\{GUIDE:(\w+)\}\}", guide, tmpl)
    out = re.sub(r"\{\{STATE:(\w+)\}\}", state, out)
    out = out.replace("{{PACE_ALL}}", sw.state_pace(rows)).replace("{{EARLY_EDAY}}", sw.early_eday(rows))
    assert "{{" not in out, "unfilled token"
    with open(os.path.join(ROOT, "MASTER.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote MASTER.md")


if __name__ == "__main__":
    main()
