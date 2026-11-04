---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../findings/archaeology/0001-switches.md
  - ../../plans/0062-debug-and-cut-content.md
resolution: "Tier B check 2026-11-04: accept with fixes (5); -ns priority entry filed; merged into main."
---

Plan 0062 Phase 1 for review. Finding [archaeology/0001](../../findings/archaeology/0001-switches.md); `tools/switches_scan.py`; kept outputs under `workspace/logs/r62a/` (`manifest.txt`, `dev/`). No emulation and no run record: no value decided a reading.

Result: three parsers (58 table rows, 6 module names, 9 registry-only rows); 41 of the 58 rows have a traced use, 17 have none, and `-opengl` is cleared after parsing. Behaviour-changing: `-seed -act -txt -direct -nosave -gametype`, class rows and `-name`, `-arena`, `-ctemp`, `/players` (§ 7). The packet table's flag word has no reader (§ 9). All new readings are `[I]`, and 51 `re/symbols.csv` rows.

Please look hardest at the "None" rows: the pointer walk missed `0x0043B7A0` until the offset scan showed it (§ *What the scan covers*), so `-fr`, `-i` and `-openc`, whose offsets are too common for that scan, rest on the walk alone. Route: [spec-writer entry](../2026-11-04-reverser-spec-writer-plan-0062-p1-switches-for-phase-3.md).
