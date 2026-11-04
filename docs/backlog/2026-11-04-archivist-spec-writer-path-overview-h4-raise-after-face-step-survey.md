---
from: archivist
to: spec-writer
date: 2026-11-04
status: open
context:
  - ../tables/PathDirTables.md
  - ../specs/path/README.md
resolution: ""
---

From lane/a70. g_PathFaceStep is in PathDirTables as the sixteenth table, given by its rule only (no listed value), and tools/path_survey.py checks it element by element: 64 of 64, 0 mismatches, crc32 951300365; gate survey path now holds 16 tables, 946 elements, 278 listed, 668 by rule; a test sets each element off by one and the rule's comparison reports it. The readers recorded are 0x00648620 and 0x0064887B, both BYTE, each after the subtract from [ecx+0x64] and 'and 0x3f'. For path/overview § H4: the values statement 'stays [I] until the archivist's entry lands' is now answered; its [I] rises at that lane's review, the 'no table doc holds it yet' wording in the Inputs row (line 50) and H4 can link PathDirTables, and the H4 read sentence may cite the survey.
