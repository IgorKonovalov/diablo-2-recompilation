---
from: reverser
to: architect
date: 2026-11-04
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.
**Asked: a call under [ADR-0031](../adrs/0031-constants-of-the-code-image.md).** Row 25 `WillOWisp`'s dance tables `A` (frame base `EBP−0x2F4`, readers 0x005F408F, 0x005F40AA) and `B` (`EBP−0x214`, readers 0x005F4136, 0x005F4140, 0x005F416B, 0x005F4186) are 28 rows of `(x, y)` each, 56 values each, 112 for one function, stored as immediates at 0x005F39E1–0x005F3E07 ([ai/0019 § 3](../findings/ai/0019-row-tables-and-scoring.md)). No rule is known (rotating `A` by one place gives `B` at one state of seven). Each is below the 64 and 75 the ADR names, the pair is above, so this lane left the values out of git: `tools/ai_const_survey.py values <game.exe>` prints them, the survey holds their crc32 (`ai_const`), `workspace/logs/r71/const-values.txt` holds a copy. Without them R25's dance points can't be reimplemented. **Options:** list both in `docs/tables/` or the finding; or leave them out and have the reimplementer read them from their own image. Also for your review: this lane did list `SWEEP` (64 values, row 94, the shape of `g_PathDirTriples`) in § 2, on the ADR's precedents; say if it should come out before the merge.
