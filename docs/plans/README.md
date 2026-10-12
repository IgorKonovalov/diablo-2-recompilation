# Plans index

Next free number: **0014**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](done/0002-excel-foundation.md) | Excel foundation: which data the game actually reads | done | — (closed 2026-10-11; `data/excel` reviewed, small spec fixes → backlog) |
| [0003](done/0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | done | — (closed 2026-10-11; `rng/seeds` reviewed, small spec fixes → backlog; harness method → ADR-0003) |
| [0004](0004-items-treasure-classes.md) | Items: treasure class resolution | in-progress | Phase 2 accepted with fixes, F1–F5 done (`542f2a5`): 328/328 calls; champion and party `[I]` (party blocks `reviewed`, plan 0011); Phase 3 (spec) next |
| [0005](0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | in-progress | Phases 1–2 and 4 accepted with fixes, fixes done; Phase 3 (TBL) next (main session) |
| [0006](done/0006-asset-rendering.md) | Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only, ADR-0005) | done | — (closed 2026-10-11; tools-only per ADR-0005; d2char merge → archivist backlog) |
| [0007](done/0007-docs-gate.md) | Docs gate: mechanical checks for anchors, tags, links and parser surveys (ADR-0006) | done | — (closed 2026-10-11; fast + full tier GREEN on `main`, commit hook active) |
| [0008](0008-drlg-overview.md) | DRLG overview: generator dispatch, the room-seed chain and the room tile draws (the k of `rng/seeds` step 6) | approved | P0–P3 accepted (P2 fixes done); Catacombs confirmation run pending (owner plays, non-blocking); P4 spec next (spec-writer) |
| [0009](0009-item-art.md) | Item art: classic-class merge, item art index, colour shifts, per-item sheets (tools-only, ADR-0005) | approved | P1, P2 accepted; P3 (colour shifts) next |
| [0010](0010-items-quality.md) | Items: the quality roll (oracle of plan 0004 replaced by a model) | approved | P0 archivist, then P1 reverser |
| [0011](0011-two-client-harness.md) | Two-client harness: the party NoDrop case and a champion kill | approved | P1 reverser (harness), P2 runs (human may play) |
| [0012](0012-monsters-pool.md) | Monsters: the level's monster pool and monster level | approved | P0 archivist (MonLvl, MonStats spawn columns), then P1 reverser |
| [0013](0013-save-d2s-code.md) | Save files: the code behind the `.d2s` format | approved | P1 reverser (writer/reader anchors), P2 round-trip runs |

Suggested order per lane: **archivist** 0005·P3 (TBL), close 0005; then 0010·P0 and 0012·P0 (table
fields, data only, can go in parallel). **reverser** 0010·P1 → 0011 (harness, then the
party and champion runs; unblocks `items/tc` `reviewed`) → 0012·P1 → 0013·P1 (its Phase 2 can reuse the 0010 drop
runs for the saved-item check). **spec-writer** 0008·P4 now, then follows each plan's reverser phases.
