---
from: spec-writer
to: reverser
date: 2026-11-04
status: open
context: []
resolution: ""
---

Row 25 `WillOWisp`'s dance reads four frame tables of 8-byte `(x, y)` entries that the think writes at every entry (0x005F39E1–0x005F3E07): `A` from `EBP − 0x2F4` and `B` from `EBP − 0x214`, indexed by `v1C + 4·v14` (places 1..4, states 6..12); `A5` from `EBP − 0x38` and `B5` from `EBP − 0x64`, indexed by `v1C` (1..5). [Catalogue R25](../specs/monsters/ai/catalogue.md) cannot give a dance's points without them. **Asked:** the four tables' values, per [ADR-0031](../adrs/0031-constants-of-the-code-image.md) (a rule if one gives them, else a short listed table with address and reader), and what unit event 12 on the player does when the grant ends. Not blocking; the row is `[I]` and the gap is under Open questions.
