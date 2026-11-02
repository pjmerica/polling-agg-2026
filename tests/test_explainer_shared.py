"""The race explainer ("What's driving this prediction", 2026-11-01) is one block of JavaScript that
docs/map.html and docs/predictions.html both carry. They used to have separate copies that drifted
(the map showed every input's definition, the forecast page hid them behind a click), so:

  - the block must be byte-identical in the two pages;
  - run under node against the published docs/forecast_data.js, it must render every race's win and
    margin explainers without throwing, and always explain the race's favourite (the model repo
    explains the leading Democrat, so a losing Democrat's block is flipped to the winner's side).

The second test needs node and skips without it. It checks code against the data's SHAPE only, never
its numbers, so a data hiccup cannot block a refresh that runs the test suite first.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"
START = "  // ===== EXPLAINER: what's driving"
END = "  // ===== end of the shared explainer block =====\n"


def block(name):
    text = (DOCS / name).read_text(encoding="utf-8")
    assert text.count(START) == 1 and text.count(END) == 1, f"{name}: explainer block markers missing"
    return text[text.index(START):text.index(END) + len(END)]


def test_block_is_identical_in_both_pages():
    a, b = block("map.html"), block("predictions.html")
    assert a == b, "the explainer block differs between map.html and predictions.html; copy one over the other"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_block_explains_every_race(tmp_path):
    script = tmp_path / "xp_check.js"
    script.write_text(
        (DOCS / "forecast_data.js").read_text(encoding="utf-8") + "\n"
        + "(function () {\n" + block("map.html") + r"""
  const o = { col: () => '#000', inputsHref: '#inputs' };
  const out = { rendered: 0, flipped: 0, problems: [] };
  for (const r of FORECAST.races) {
    if (!r.cands || !r.cands.length) continue;
    r.cands = r.cands.slice().sort((a, b) => (b.win || 0) - (a.win || 0));
    for (const k of ['win', 'margin']) {
      let html;
      try { html = XP.pane(r, k, o); } catch (e) { out.problems.push(`${r.id} ${k}: ${e.message}`); continue; }
      const b = r.explain && r.explain[k];
      if (!b) continue;
      out.rendered++;
      // the summary names whoever the block explains first: it must be the favourite when the
      // favourite is one of the two candidates compared
      const m = /The (?:model gives|margin model has) <b>([^<]+)<\/b>/.exec(html);
      const fav = r.cands[0].name, pair = [r.explain.candidate, b.vs];
      const sur = n => n.split(/\s+/).filter(w => !/^(jr\.?|sr\.?|ii|iii|iv)$/i.test(w)).pop();  // as the page shows it
      if (!m) out.problems.push(`${r.id} ${k}: no summary sentence`);
      else if (b.vs && pair.includes(fav) && sur(fav) !== m[1]) out.problems.push(`${r.id} ${k}: explains ${m[1]}, favourite is ${fav}`);
      if (b.vs === fav && r.explain.candidate !== fav) out.flipped++;
      if (/NaN|undefined/.test(html)) out.problems.push(`${r.id} ${k}: NaN or undefined in the output`);
    }
  }
  console.log(JSON.stringify(out));
})();
""", encoding="utf-8")
    run = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stderr[-2000:]
    out = json.loads(run.stdout.strip().splitlines()[-1])
    assert out["rendered"] > 100, out
    assert not out["problems"], out["problems"][:10]
