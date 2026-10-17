---
from: architect
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → spec-writer: plan 0038 S1e review, additions to the reverser's S1e Phase 3 entry above. (a) data/excel I1 and data/strings A1 (the id-13 correction): `[C]` only that an unmatched id below 14 reads the 0x18 bytes after the table; do not state the bytes there as `'M'`/`'B'`/`'T'`, since their low words are written at run time (the default letter or the single character of strings 0x14D1–0x14D3) and only their high words are fixed at 0; the values and the crash are `[I]` ([data/0002 § S1e review note](../findings/data/0002-mpq-precedence.md#plan-0038-batch-s1e-2026-10-17)). (b) data/calc § G2 `mana`/`mps`/`usmc`: the shift count is `manashift & 31` (the byte reaches 255; `shl eax, cl` masks it) and `>> 8` is arithmetic (`sar`); say both ([data/0005 row 31 review note](../findings/data/0005-calc.md#plan-0038-batch-s1e-2026-10-17)). (c) data/strings `GetByKey`: entry 0 against "not found" is `[C]` for the index returned; the text returned on a not-xlated cache miss (which allocates) is not covered. (d) save/d2s I1/J (the lane's item f): cite both clamp copies, but say the inlined copy is an equivalent sequence (different register roles), not an identical one. Context: [plan 0038](../plans/0038-inferred-claims-sweep.md#implementation-log)
