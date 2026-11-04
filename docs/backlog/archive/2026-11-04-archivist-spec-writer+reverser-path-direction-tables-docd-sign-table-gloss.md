---
from: archivist
to: spec-writer, reverser
date: 2026-11-04
status: done
context:
  - ../../tables/PathDirTables.md
  - ../../specs/path/README.md
  - ../../specs/path/search.md
  - ../../findings/path/0001-pathplan-register.md
resolution: "Done at the lane/a54 review, which owns the corrections it finds in a reviewed spec: g_PathSignTable confirmed at 0x006480AF-0x006480ED (x takes the entry at dx + 9 dy, y the entry at dy + 9 dx; sign(a) when |a| >= |b|, else 0); path/0001 section 5 and its data row corrected with a dated note, specs/path/README.md C3's step line corrected; PathDirTables linked from both path specs, the closed-entry sentence of specs/path/search.md replaced, the word-read shapes written. Nothing left for the reverser: the emulations read the table and no result moves. The one gap the check found goes by its own entry, PathFaceDir."
---

From lane/a54. The direction and step tables are now in [PathDirTables](../../tables/PathDirTables.md) (values, addresses, element widths read from the reading instructions, indexes), by tools/path_survey.py dirtables. Two things for the other lanes. (1) spec-writer: link PathDirTables from the Tables section of specs/path/search.md (it still says the values are pending this entry) and from specs/path/README.md; the search.md table rows give 'i32' shapes where three tables are read as WORDs (g_PathStep8Long, g_T15Step, g_PathDir8: the low 16 bits of each dword). (2) Both: g_PathSignTable is not the sign of dx and of dy. By script, for a, b in -4..4 (81 of 81) the entry at a + 9 b is sign(a) when |a| >= |b|, else 0; so the PathTargetExtendPlayer step (g_PathSignTable[dx + 9 dy], g_PathSignTable[dy + 9 dx]) is (sign dx, 0) when |dx| > |dy|, (0, sign dy) when |dy| > |dx|, and (sign dx, sign dy) only at |dx| = |dy|. specs/path/README.md line 265 writes step <- (sign dx, sign dy) and path/0001 section 5 and its data row say 'the signs of dx and dy' / 'the sign of dx'. The emulations read the table, so their checks stand; the wording (and the spec's pseudocode as a reimplementer would read it) does not. Needs a dated correction in path/0001 and the spec line.
