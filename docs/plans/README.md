# Plans index

Next free number: **0017**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](done/0002-excel-foundation.md) | Excel foundation: which data the game actually reads | done | — (closed 2026-10-11; `data/excel` reviewed, small spec fixes → backlog) |
| [0003](done/0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | done | — (closed 2026-10-11; `rng/seeds` reviewed, small spec fixes → backlog; harness method → ADR-0003) |
| [0004](done/0004-items-treasure-classes.md) | Items: treasure class resolution | done | — (closed 2026-10-12; `items/tc` reviewed, C 38 / I 74 / L 9) |
| [0005](done/0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | done | — (closed 2026-10-12; all phases accepted with fixes; run-time `.tbl` use → reverser backlog) |
| [0006](done/0006-asset-rendering.md) | Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only, ADR-0005) | done | — (closed 2026-10-11; tools-only per ADR-0005; d2char merge → archivist backlog) |
| [0007](done/0007-docs-gate.md) | Docs gate: mechanical checks for anchors, tags, links and parser surveys (ADR-0006) | done | — (closed 2026-10-11; fast + full tier GREEN on `main`, commit hook active) |
| [0008](done/0008-drlg-overview.md) | DRLG overview: generator dispatch, the room-seed chain and the room tile draws (the k of `rng/seeds` step 6) | done | — (closed 2026-10-12; P4 accepted: `drlg/overview` and `drlg/room-tiles` reviewed, `rng/seeds` 6b links k; open points → reverser backlog) |
| [0009](done/0009-item-art.md) | Item art: classic-class merge, item art index, colour shifts, per-item sheets (tools-only, ADR-0005) | done | — (closed 2026-10-12; P4 accepted: 1175 sheets, `render_all.py --only items`; tint pairing `[L]` → reverser backlog) |
| [0010](0010-items-quality.md) | Items: the quality roll (oracle of plan 0004 replaced by a model) | in-progress | P0, P1, P1b accepted; P2 partial accepted 2026-10-13 (no oracle: 328 old + 1393 new calls; MF 100 diminishing `[C]`); P2 rest: MF 1–10, classic, minion/summon kill (owner sessions, characters to build) |
| [0011](done/0011-two-client-harness.md) | Two-client harness: the party NoDrop case and a champion kill | done | — (closed 2026-10-12; party count and champion column `[C]` in items/0001; ADR-0008 proposed, owner: network exposure; `items/tc` tag pass → spec-writer) |
| [0012](done/0012-monsters-pool.md) | Monsters: the level's monster pool and monster level | done | — (closed 2026-10-12; `specs/monsters/pool` reviewed; `boss` and four hireling classes open, need play) |
| [0013](done/0013-save-d2s-code.md) | Save files: the code behind the `.d2s` format | done | — (closed 2026-10-12; `specs/save/d2s` draft until `items/properties`; bit-13 clearer → reverser backlog) |
| [0014](0014-monsters-spawn.md) | Monsters: random population of a room (density, class pick, packs, minions, placement) | in-progress | P0 accepted; P1 accepted 2026-10-13 (monsters/0002, collision as ADR-0004 oracle); P1b reverser next, then P2 runs, P3 spec |
| [0015](done/0015-backlog-sweep.md) | Backlog sweep: static loose ends from the closed plans | done | — (closed 2026-10-12; data/0004, save/0001 §8, items/0003, gate E9; four specs updated) |
| [0016](0016-drlg-preset.md) | DRLG presets: the DS1 unit list, the preset-unit rolls and the LvlPrest columns | in-progress | approved 2026-10-13; P0 accepted with fixes 2026-10-13 (ds1.py units survey); P1 reverser next |

Suggested order per lane: **archivist** the 0016·P0 review fixes (see the plan log); backlog follow-ups: the item-art index fixes (items/0003) and the table-doc fixes (data/0004). **reverser** 0014·P1b, then the owner sessions of 0014·P2 and 0010·P2 (`MfNecro`, `ClassicSorc`, built), then 0016·P1; backlog: the `gf` clamp and the `Woo!` quest words. **spec-writer** follows each plan's reverser phases (0010·P3 after 0010·P2).
