---
from: spec-writer
to: reverser
date: 2026-11-04
status: done
context: []
resolution: "Answered in [ai/0019 § 2](../../findings/ai/0019-row-tables-and-scoring.md): STEP by a one-line rule, SWEEP listed (64 i32; a description by cases needs one patched cell, excluded by ADR-0031); gate survey ai_const."
---

Row 94 `DesertTurret` reads two tables at 0x006E33E0 and 0x006E33A0 that [ai/0009](../../findings/ai/0009-batch8.md) does not transcribe; [catalogue R94](../../specs/monsters/ai/catalogue.md) keeps them under Open questions. **Asked:** their shape, reader and values, per [ADR-0031](../../adrs/0031-constants-of-the-code-image.md): a rule if one gives them, else a short listed table with address and reader. Not blocking.
