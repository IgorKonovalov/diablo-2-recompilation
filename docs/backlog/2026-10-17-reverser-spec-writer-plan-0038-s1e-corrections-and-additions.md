---
from: reverser
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from reverser → spec-writer: plan 0038 S1e corrections and additions for Phase 3 of [data/calc](../specs/data/calc.md), [data/excel](../specs/data/excel.md), [data/strings](../specs/data/strings.md), [rng](../specs/rng/README.md) and [save/d2s](../specs/save/d2s.md) (after the S1e review). (a) Re-tag per the "Plan 0038 batch S1e" sections of data/0001–0005, rng/0001 and save/0001, citing run:2026-10-17-sweep-emu (rng: run:2026-10-11-rng-emu addendum 2026-10-17); the unreachability sentences of data/strings § C and § G (the 11078 and entry-500 fallbacks are not reached on stock data) are separate claims and keep their own tags. (b) **Correction, data/excel I1 (L522) and data/strings A1/the language note:** "unknown → entry 0" holds for ids ≥ 14 only; id 13 (the only other value a `u8` `use` byte can carry that matches no entry, since `LNG_GetLanguageIndex` clamps only ≥ 14) reads the 0x18 bytes after the table, whose string pointers are 0x4D, 0x42, 0x54, so the string-table load faults; `[C]` for the map, `[I]` for the fault, d-edit (an edited `use` file). (c) data/calc § C quirks: add that consecutive unary minus fails (`- -5` → −1: the second `-` pops the first, which has no operand); `-(-5)` compiles. (d) data/calc § D: keep 4g (the divide error) `[I]` with its instruction anchors; emulation cannot show a fault. (e) data/calc § G2: name the `m1rn`–`m3rn` out-of-range cases (a skilldesc index outside the table, or a description missile outside the missiles table, gives 0, and there is no level test). (f) save/d2s I1/J: the clamp's `[C]` covers the inlined copy at 0x00630F38–0x00630F4E through the identical instruction sequence; cite both. Context: [plan 0038](../plans/0038-inferred-claims-sweep.md#implementation-log)

*Annotation (archive copy, migrated 2026-10-17):* **Partly done 2026-10-17 (spec-writer, `lane/p38s4`, Phase 3 round 4):** (a) for data/calc and rng; (c) `- -5` in § C's quirks; (d) 4g kept `[I]`, with why emulation cannot show it; (e) the `m1rn`–`m3rn` out-of-range cases in § G1's table. **Open:** (a) for data/excel, data/strings and save/d2s, (b) and (f), with their rounds.
