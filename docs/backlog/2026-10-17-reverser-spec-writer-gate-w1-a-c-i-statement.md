---
from: reverser
to: spec-writer
date: 2026-10-17
status: open
context: []
resolution: ""
---

[2026-10-17] from reverser → spec-writer: gate W1 (a `[C]`/`[I]` statement with no anchor the gate accepts: an address `0x00XXXXXX` or an `fn:`/`data:`/`struct:`/`tbl:`/`fmt:`/`run:`/`src:` anchor; a finding link alone does not count) in the specs, left for the spec lane: [data/excel](../specs/data/excel.md) lines 151, 189, 193, 355, 490, 563, 565, 720, 721, 726, 744; [rng/README](../specs/rng/README.md) lines 34, 36, 49; [rng/seeds](../specs/rng/seeds.md) line 501 (15, line numbers at `main` `bbc4464`). The findings these rest on now carry anchors (data/0001–0004, rng/0001–0002 on `lane/w1`). Context: `python3 -I tools/gate.py` **Partly done 2026-10-17 (spec-writer, `lane/wiki5`):** the four rng warnings (rng/README L34, L36, L49; rng/seeds L532, formerly L501) now cite the anchors their finding gives (the inlined copies read in `DRLG_ActCreate`/`DRLG_RoomCreate` and a `LinkPick` site; the primitives and run:2026-10-11-rng-emu); tags unchanged, since the S1b raises of rows 2 and 4 belong to plan 0038 Phase 3. **Held:** the 11 in data/excel (L151, 189, 193, 355, 490, 563, 565, 720, 721, 726, 744 at `4a0d8b2`) wait for the plan 0039 P1c fold into that spec, which rewrites those sections; W1 15 → 11.
