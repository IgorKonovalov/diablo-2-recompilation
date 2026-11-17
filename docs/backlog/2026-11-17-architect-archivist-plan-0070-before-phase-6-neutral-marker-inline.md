---
from: architect
to: archivist
date: 2026-11-17
status: open
context:
  - ../plans/0070-redacted-public-export.md
resolution: ""
---

Before plan 0070 Phase 6 (from the Phase 3 review, 2026-11-17; Tier B check). Not blocking Phase 3. (1) **Neutral schematic marker.** The marker `d2recon-schematic/1` carries the working repository's project name (its README title) into every published illustration file, and `schematic.json` names our tools (`"tool": "maze_anim"`): both tie the export to the working repository (ADR-0035's no-tie rule; missed at the Phase 2 review). Rename the marker to a neutral string (e.g. `schematic-only/1`) in `tools/anim_common.py`, `tools/export_check.py` and the fixtures under `tools/gate/fixtures/export/` (regenerate the binary ones with the tools), and drop the `tool` key from the published `schematic.json` (or make the check refuse it). Also: the TC illustration's calc text names a tool option (`--mlvl overrides`); reword in schematic mode. (2) **Embed the GIF inline** (owner decision 6: animations are needed). The builder writes `![Animation: <id>](/illustrations/<id>/<gif>)` (root-absolute) plus the step-through link; X8 accepts a root-absolute `/illustrations/<id>/<file>` target that X11 allows and nothing else; `workspace/export-repo/site/astro.config.mjs` gets a small rehype step that prefixes `SITE_BASE` to `img` sources starting `/illustrations/`; `check-site-links.mjs` resolves `img src` as it does links. Tests for each. Done when: both tests files and the gate are green, the first cut checks 0 failures, and `grep -r d2recon workspace/export/site` is empty.
