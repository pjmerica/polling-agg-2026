"""The GitHub Pages copies of the two election-night pages, fed by the cloud run (cloud_night.py):

  docs/election-night-cloud.html   dashboard.html       (races, map, best buys, FLIPs)
  docs/election-night-desk.html    data_dashboard.html  (the data desk, 3D map)

The pages themselves are unchanged. A small loader goes in front of them: when a page asks for its data
file (data/raw/dashboard/live_data.js) it gets live_data.js from the orphan branch `election-live`,
fetched rather than loaded as a script because GitHub serves raw files as plain text. GitHub's API first
(no cache; 60 requests an hour per address, and unchanged files don't count), raw.githubusercontent.com
(cached up to 5 minutes) when the API refuses. Re-run after editing either page.

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
  let text = null, at = 0, apiOffUntil = 0;
  async function get() {
    if (text && Date.now() - at < MIN_GAP) return text;
    let t = null;
    if (Date.now() > apiOffUntil) {
      try {
        const r = await fetch(API, { headers: { Accept: "application/vnd.github.raw" }, cache: "no-cache" });
        if (r.ok) t = await r.text();
        else if (r.status === 403 || r.status === 429) apiOffUntil = Date.now() + 10 * 60000;
      } catch (e) { /* fall through to raw */ }
    }
    if (t === null) {
      const r = await fetch(RAW + "?t=" + Date.now(), { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      t = await r.text();
    }
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
       '"The Election night (cloud) workflow hasn\'t published yet."')]),
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
