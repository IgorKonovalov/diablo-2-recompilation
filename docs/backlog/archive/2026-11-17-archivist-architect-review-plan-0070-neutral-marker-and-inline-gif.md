---
from: archivist
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "Tier B accept with fixes (1): X4 skip narrowed [plan log](../../plans/0070-redacted-public-export.md)"
---

Tier B check of lane/x70m: the neutral marker schematic-only/1 (no tool key in schematic.json, refused by X11), the inline GIF (builder image target, X8 root-absolute only, RE_ABS skip, astro.config.mjs rehype step in the workspace export repo), fixtures regenerated. Look at: tools/export_check.py (MARKER, tool-key refusal, RE_ILLUS, RE_ABS), tools/export_build.py illustration_block, workspace/export-repo/site/astro.config.mjs. Not done: site build (no npm). ADR-0036 names no marker string and needs no change. Also, the plan's earlier ruling line still shows the old marker as history.
