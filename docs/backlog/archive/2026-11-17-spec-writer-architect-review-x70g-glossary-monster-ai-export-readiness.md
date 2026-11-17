---
from: spec-writer
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "Tier A review: accept with fixes 2 (sparkle flag name; skill rule cites ADR-0035 and the dropped See link). Plan 0070 log 2026-11-17."
---

Review request (Tier A, Opus, owner's choice for plan 0070) for lane/x70g.

(1) `docs/glossary.md`: the 29 entries the first cut dropped (27 X1, 2 X3) now carry their offsets and addresses in trailing evidence-only parentheticals (`game+0x7C`, `NpcStoreCtl+0x08`, ...), so the definition sentence stands alone; the working text keeps every offset. Changed for that: Item seed, Made-uniques set, Store seed, Monster region, Logic box, Collision grid, Near list, Map seed (its See link now the rng seeds spec instead of finding rng 0002), Level seed base, Game seed, DRLG room / active room, Room type, DT1 mask, k, File rotation (link label reworded), Warp points, Trade state, Ground expiry, Ethereal (flag as a bare 0x400000 parenthetical), Object-region seed, Sparkle chest, Quest seed, Stat list, Start/do function, Path type, testMask/markMask, Path speed, AI state, Tier AI (no plan number; now also links the wiki's tier-AI section). The preamble note is out of the body; its rule moved to the spec-writer skill, step 6. The method-only entries (Boundary oracle, Retired oracle, First boundary, Activation-order record, Tier AI) stay: wiki pages in the cut use the terms (seed-to-world, objects, monsters, characters, pathing, skills, monster-ai).

(2) `docs/wiki/monster-ai.md`: *The first call* and *Past the first call* now lose nothing in the cut: the four X9 units reworded ("logger" to "the logging", the table header's revision key), and link-only parentheticals that sat on a line of their own joined to their sentence (they left a stray full stop in the cut; six of them: two in *Past the first call*, four in earlier sections). The three *shorts* items dropped for the same word are reworded too.

Cut (`workspace/export-x70g`): glossary 29 of 161 units dropped before, 0 of 159 after; monster-ai 20 of 354 (7 report lines) before, 0 after; `export_check` 0 failures. Please check that the reworded sentences keep the original's claims and tags.
