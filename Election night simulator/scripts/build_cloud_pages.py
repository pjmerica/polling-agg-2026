"""The GitHub Pages copies of the two election-night pages, fed by the cloud run (cloud_night.py):

  docs/election-night-cloud.html   dashboard.html       (races, map, best buys, FLIPs)
  docs/election-night-desk.html    data_dashboard.html  (the data desk, 3D map)

The pages themselves are unchanged. A small loader goes in front of them: when a page asks for its data
file (data/raw/dashboard/live_data.js) it gets live_data.js from the orphan branch `election-live`,
fetched rather than loaded as a script because GitHub serves raw files as plain text. From
raw.githubusercontent.com with a fresh query string each time (tested 2026-11-02: that skipped its 5-minute
cache; on election night it didn't, serving one pass for 7 minutes); GitHub's API (60 requests an hour per
address) when raw fails or its copy is over 2.5 minutes old, at most every ~2 minutes. Re-run after editing
either page.

    py "Election night simulator/scripts/build_cloud_pages.py"
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DOCS = os.path.join(ROOT, "..", "docs")
MARKER = '<script>\n"use strict";'

LOADER = """<script>
// Cloud copy (build_cloud_pages.py): the data file comes from the election-live branch, written every
// 2 minutes by cloud_night.py in GitHub Actions. Any script whose src is the live data file is fetched
// from there instead; every other script loads as usual.
(function () {
  const REPO = "pjmerica/polling-agg-2026", BRANCH = "election-live";
  const API = "https://api.github.com/repos/" + REPO + "/contents/live_data.js?ref=" + BRANCH;
  const RAW = "https://raw.githubusercontent.com/" + REPO + "/" + BRANCH + "/live_data.js";
  const MIN_GAP = 30000;                    // the pages ask every 10-15 s; the data changes every 2 min
  // raw's cache can ignore the query string (2026-11-03 election night: the same pass served for 7 minutes
  // while the branch moved on), so a copy older than STALE also asks the API, at most once per API_GAP
  // (~30 an hour, under its 60 an hour per address)
  const STALE = 150000, API_GAP = 115000;
  const genAt = s => { const i = s ? s.indexOf('"generated":"') : -1; return i < 0 ? 0 : Date.parse(s.slice(i + 13, i + 33)) || 0; };
  let text = null, at = 0, apiOffUntil = 0, apiAt = 0;
  async function get() {
    if (text && Date.now() - at < MIN_GAP) return text;
    let t = null;
    try {
      const r = await fetch(RAW + "?t=" + Date.now(), { cache: "no-store" });
      if (r.ok) t = await r.text();
    } catch (e) { /* try the API */ }
    const old = t === null || Date.now() - genAt(t) > STALE;
    if (old && Date.now() > apiOffUntil && Date.now() - apiAt > API_GAP) {
      apiAt = Date.now();
      try {
        const r = await fetch(API, { headers: { Accept: "application/vnd.github.raw" }, cache: "no-cache" });
        if (r.status === 403 || r.status === 429) apiOffUntil = Date.now() + 10 * 60000;
        if (r.ok) { const a = await r.text(); if (t === null || genAt(a) > genAt(t)) t = a; }
      } catch (e) { /* keep raw's copy */ }
    }
    if (t === null && text) return text;
    if (t === null) throw new Error("no data");
    if (text && genAt(t) < genAt(text)) t = text;   // never step back to an older pass
    text = t; at = Date.now();
    return t;
  }
  const native = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, "src");
  const make = document.createElement.bind(document);
  document.createElement = function (tag, opts) {
    const el = make(tag, opts);
    if (String(tag).toLowerCase() !== "script") return el;
    Object.defineProperty(el, "src", {
      configurable: true,
      get() { return native.get.call(el); },
      set(v) {
        if (!/live_data\\.js/.test(String(v))) { native.set.call(el, v); return; }
        get().then(t => {
          window.LIVE = JSON.parse(t.slice(t.indexOf("=") + 1).trim().replace(/;\\s*$/, ""));
          if (el.onload) el.onload(new Event("load"));
        }).catch(() => { if (el.onerror) el.onerror(new Event("error")); });
      },
    });
    return el;
  };
})();
</script>
"""

PAGES = [
    ("dashboard.html", "election-night-cloud.html",
     [("<title>Election Night Live</title>", "<title>Election Night Live (cloud)</title>"),
      ("Is live_project.py --watch still running?", "Is the Election night (cloud) workflow running?"),
      ('"No data yet. Start the projector: py \\"Election night simulator/scripts/live_project.py\\" --watch 30 '
       '(or run scripts/run_dashboard.cmd). " +\n      "This page reads " + SRC + " next to it."',
       '"No data yet: the Election night (cloud) workflow hasn\'t published (branch election-live)."')]),
    ("data_dashboard.html", "election-night-desk.html",
     [("<title>Election Night Data Desk</title>", "<title>Election Night Data Desk (cloud)</title>"),
      ('"Start run_dashboard.cmd (the projector writes it)."',
       '"The Election night (cloud) workflow hasn\'t published yet."'),
      ("Is live_project.py --watch still running?", "Is the Election night (cloud) workflow running?"),
      # buy signals and the Kalshi board on by default here (the local page starts with them off)
      ('const ui = { sel: null, sort: "close", sig: REPLAY,', 'const ui = { sel: null, sort: "close", sig: true,')]),
]


def main():
    for src, dst, edits in PAGES:
        page = open(os.path.join(ROOT, src), encoding="utf-8").read().replace("\r\n", "\n")
        assert page.count(MARKER) == 1, src
        page = page.replace(MARKER, LOADER + MARKER)
        for old, new in edits:
            assert page.count(old) >= 1, (src, old)
            page = page.replace(old, new)
        with open(os.path.join(DOCS, dst), "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print(f"wrote docs/{dst}")


if __name__ == "__main__":
    main()
