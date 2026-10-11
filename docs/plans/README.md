# Plans index

Next free number: **0006**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](0002-excel-foundation.md) | Excel foundation: which data the game actually reads | draft | Phases 1 (archivist) and 2 (reverser), in parallel |
| [0003](0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | draft | Phase 1 (reverser) |
| [0004](0004-items-treasure-classes.md) | Items: treasure class resolution | draft | waits on 0002 Phase 2 (live TC table) |
| [0005](0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | draft | Phase 1 (archivist), after 0002 Phase 1 |

Suggested order per lane: **archivist** 0002·P1 → 0005·P1–3 → 0005·P4 (needs the 0003 harness);
**reverser** 0003·P1 → 0002·P2 → 0003·P2 → 0004·P1 → 0004·P2; **spec-writer** follows each plan's
reverser phases. Next in line after these (not yet planned): `items/quality`, `drlg/overview`,
`monsters/pool`.
