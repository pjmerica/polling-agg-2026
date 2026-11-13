# history

Things that are no longer used, kept for reference. Nothing here is run by the pipeline, the
tests or any workflow. Old versions are archived here, not deleted.

| File | What it was |
|---|---|
| `HANDOFF_2026-04_to_10.md` | The handoff guide before the 2026-11-12 rewrite |
| `CHANGELOG_2026-06_to_10.md` | Changelog entries from June to October 2026 (moved 2026-11-13) |
| `AUDIT.md`, `POLL_DATA_AUDIT.md`, `AGENT_EXECUTION_NOTES.md`, `NOTES_FOR_REVIEWER.md` | Audits and review notes, July to September 2026 |
| `old_code/fivethirtyeight.py`, `old_code/realclearpolitics.py` | Poll scraper stubs from April. 538 shut down; the RCP one needed a manual export. Never part of `run_all.py` |
| `old_code/aggregator.py` | The April aggregator. It averaged every market touching a race into one number; `scripts/regen_data.py` replaced it on 2026-09-25 |
| `old_data/aggregated.csv`, `old_data/combined_raw.csv` | The aggregator's last output, 2026-04-14 |
| `old_pages/mismatch_data.js` | Data for the old "Polling vs Markets Mismatch" tab. Not generated since 2026-07-21 and read by no page |

Also removed on 2026-11-13: `models/__init__.py`, an empty file in an otherwise empty folder that
nothing imported (the forecast comes from the separate model repo). It is in git history.

The retired standalone Model vs Markets page stays published at `docs/archive/model.html`.
