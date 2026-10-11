# Plans index

Next free number: **0010**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](done/0002-excel-foundation.md) | Excel foundation: which data the game actually reads | done | — (closed 2026-10-11; `data/excel` reviewed, small spec fixes → backlog) |
| [0003](done/0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | done | — (closed 2026-10-11; `rng/seeds` reviewed, small spec fixes → backlog; harness method → ADR-0003) |
| [0004](0004-items-treasure-classes.md) | Items: treasure class resolution | in-progress | Phase 2 accepted with fixes (2026-10-11; F1–F5 → reverser): 328/328 calls; champion and party `[I]` (party blocks `reviewed`); Phase 3 (spec) after the fixes |
| [0005](0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | in-progress | Phases 1–2 and 4 accepted with fixes, fixes done; Phase 3 (TBL) next (main session) |
| [0006](done/0006-asset-rendering.md) | Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only, ADR-0005) | done | — (closed 2026-10-11; tools-only per ADR-0005; d2char merge → archivist backlog) |
| [0007](done/0007-docs-gate.md) | Docs gate: mechanical checks for anchors, tags, links and parser surveys (ADR-0006) | done | — (closed 2026-10-11; fast + full tier GREEN on `main`, commit hook active) |
| [0008](0008-drlg-overview.md) | DRLG overview: generator dispatch, the room-seed chain and the room tile draws (the k of `rng/seeds` step 6) | approved | P0, P0b, P1 accepted; P2 next (harness) |
| [0009](0009-item-art.md) | Item art: classic-class merge, item art index, colour shifts, per-item sheets (tools-only, ADR-0005) | approved | P1, P2 accepted; P3 (colour shifts) next |

Suggested order per lane: **archivist** 0005·P3 (TBL), close 0005;
**reverser** 0004·P1b → 0004·P2 (runtime runs per ADR-0003, quality roll as oracle per ADR-0004); **spec-writer** follows each plan's
reverser phases. Then **reverser** 0008·P1 → P3 once past 0004·P2 (plan 0008 approved; its
Phases 0 and 0b are archivist work that can go first). Next in line after these (not yet planned): `items/quality`, `monsters/pool`.
