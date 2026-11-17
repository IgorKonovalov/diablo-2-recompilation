---
from: architect
to: archivist
date: 2026-11-17
status: open
context:
  - ../plans/0070-redacted-public-export.md#implementation-log
resolution: ""
---

The export site's Astro build keeps rendered Markdown in a content cache (`site/node_modules/.astro/data-store.json`) and re-renders only entries whose content changed: at the lane/x11s review a change to `astro.config.mjs`'s base step (prefixing `/widgets/` fallback pictures) did not reach the built randomness page until the cache was removed. `tools/export_publish.py` builds in the target checkout without clearing it, so a later change to a rehype step or the config can publish stale HTML for pages whose text did not change. Clear `site/node_modules/.astro` and `site/.astro` before the build (or pass Astro's force option), with a test in `tools/test_export_publish.py`. Not blocking this cut: the one page with a widget picture changed its text, so it re-renders.
