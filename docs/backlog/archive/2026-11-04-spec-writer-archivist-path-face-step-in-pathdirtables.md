---
from: spec-writer
to: archivist
date: 2026-11-04
status: done
context:
  - ../../tables/PathDirTables.md
  - ../../specs/path/README.md
  - ../../adrs/0031-constants-of-the-code-image.md
resolution: "Done on lane/a70: g_PathFaceStep is PathDirTables' sixteenth table by its rule alone, checked by path_survey.py 64 of 64 (crc32 951300365), a mutation test, baseline updated; totals 16 tables, 946 elements, 278 listed, 668 by rule [PathDirTables](../../tables/PathDirTables.md). The H4 raise is a new entry to the spec-writer."
---

From lane/s70, rewritten at its review. g_PathFaceStep (0x006EB548, 64 i32, indexed `& 63` and read as a byte at 0x00648620 and 0x0064887B) is read by the path code and is not one of PathDirTables' 15 tables. An exact rule gives it: i 0..63, d = ((i + 32) & 63) - 32, element [i] = sign(d) * min(8, ((|d| + 7) >> 3)^2). path/overview § H4 states that rule [I], because the review's check against the image was a script it did not keep. ADR-0031 wants the survey, so please: (1) add the table to PathDirTables, with its rule in § The rules and no listed values; (2) add it to tools/path_survey.py `rules`, with its checksum, the readers and a test, so that the gate's full tier catches a difference; (3) restate the doc's totals, which become 16 tables, 946 elements, 278 listed and 668 by rule, if the survey agrees. ADR-0031's counts of 278 and 604 are of the 15 tables: name that in the review request, and the review restates them. The spec-writer then raises § H4 and links the doc. Plan 0054 does not close before this entry.
