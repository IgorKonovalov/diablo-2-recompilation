---
from: architect
to: spec-writer
date: 2026-11-19
status: done
context:
  - ../../specs/path/search.md#a2-directions
  - ../../plans/0070-redacted-public-export.md
  - ../../tables/PathDirTables.md
resolution: "lane/x16s: search § A2 states the octant by cases, [C] as an equality on column 0 of the image's 25 cells (25 of 25, the table doc's listing, which tools/test_path_survey.py compares with the image), the table staying listed under ADR-0031's owner ruling ([search § A2](../../specs/path/search.md#a2-directions)); row 31's path block placed on wiki/pathing after path-search-toy-room, its caption pointing to § A2 ([plan 0070 log](../../plans/0070-redacted-public-export.md#implementation-log))."
---

State in spec-path/search § A2 the rule of PathDirOctant (column 0 of g_DirOctant) over the 25 cells, so the path widget (plan 0070 Phase 11 row 31, tools/widgets/path/) computes only from a rule the page states (ADR-0037). The lane/x16c review recomputed one description over the 25 listed values in PathDirTables, 25 of 25: with dx', dy' the cell's terms after PathDirCell's cut and clamp, a term whose double is at most the other's size is set to 0, the direction is the step of g_PathSearchStep8 with the signs left, and the cell (0, 0) gives 6. Note "octant" in the usual sense differs on the 8 cells (±2, ±1) and (±1, ±2) (the straight direction wins at 2:1). The table doc keeps its listing (ADR-0031 owner ruling); this is a spec sentence, recomputed over the table, tag [C] on the table's listing and the emulation (run:2026-11-03-path-emu-2). Until it lands, the row 31 widget block stays out of the cut (workspace/phase11/blocks-batch3-x16c.md marks it held).
