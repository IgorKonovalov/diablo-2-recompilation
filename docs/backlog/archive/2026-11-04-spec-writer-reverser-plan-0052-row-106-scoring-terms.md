---
from: spec-writer
to: reverser
date: 2026-11-04
status: done
context: []
resolution: "Answered in [ai/0019 § 1](../../findings/ai/0019-row-tables-and-scoring.md): each aitype's terms, target, skips and draws, the locals (the word is 0x0063A2B0, not 0x005EA2B0), the EType map; checked as a model over the instructions, 6 000 cases, run:2026-11-04-r71-sm. No log has the row."
---

Row 106 `ShadowMaster`'s second skill loop (0x005EBF12–0x005EC539): the score's base and the list it fills are in [catalogue R106](../../specs/monsters/ai/catalogue.md) steps 12 to 14, read from the instructions, with [the dated correction in ai/0006 § 2.11](../../findings/ai/0006-summons.md). **Asked:** each `aitype`'s terms, target and skips: the table at 0x005EC660 (13 cases), the locals set at 0x005EBDFB–0x005EBE69 (`UnitLifePct`, `DistSq(U, t)`, the `aip1[h]` and 0x005EA2B0 word, `UnitLineBlocked`, the search counts), and the `EType` map of the resistance term (the byte table at 0x005EC650). A reimplementation cannot pick the same skill or make the same draws without them: each kept record draws once. Not blocking row 143 or any other row.
