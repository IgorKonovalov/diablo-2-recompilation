# Plans index

Next free number: **0037**

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
| [0010](done/0010-items-quality.md) | Items: the quality roll (oracle of plan 0004 replaced by a model) | done | — (closed 2026-10-14; `specs/items/quality` reviewed, C 61 / I 34 / L 4; SetMin/RareMin swap → reverser, ItemRatio uber pairs → archivist) |
| [0011](done/0011-two-client-harness.md) | Two-client harness: the party NoDrop case and a champion kill | done | — (closed 2026-10-12; party count and champion column `[C]` in items/0001; ADR-0008 proposed, owner: network exposure; `items/tc` tag pass → spec-writer) |
| [0012](done/0012-monsters-pool.md) | Monsters: the level's monster pool and monster level | done | — (closed 2026-10-12; `specs/monsters/pool` reviewed; `boss` and four hireling classes open, need play) |
| [0013](done/0013-save-d2s-code.md) | Save files: the code behind the `.d2s` format | done | — (closed 2026-10-12; `specs/save/d2s` reviewed 2026-10-14 after `items/properties`; bit-13 clearer → reverser backlog) |
| [0014](done/0014-monsters-spawn.md) | Monsters: random population of a room (density, class pick, packs, minions, placement) | done | — (closed 2026-10-14; `specs/monsters/spawn` reviewed, C 94 / I 64 / L 6; `MonSpawnTry` early exits → reverser backlog; positions → plan 0017) |
| [0015](done/0015-backlog-sweep.md) | Backlog sweep: static loose ends from the closed plans | done | — (closed 2026-10-12; data/0004, save/0001 §8, items/0003, gate E9; four specs updated) |
| [0016](done/0016-drlg-preset.md) | DRLG presets: the DS1 unit list, the preset-unit rolls and the LvlPrest columns | done | — (closed 2026-10-13; `drlg/preset` reviewed, C 86 / I 59 / L 2; Acts III/V session and the river-object row-skip count → reverser backlog) |
| [0017](done/0017-drlg-collision.md) | DRLG collision: the room collision grid, logic regions and the spawn position tests | done | — (closed 2026-10-14; `specs/drlg/collision` reviewed, C 99 / I 57 / L 13; run:2026-10-14-collision 0 mismatches; room-tiles 9d flag gap → reverser) |
| [0018](done/0018-monsters-special.md) | Monsters: champions, uniques and superuniques (mods, minions, names) | done | — (closed 2026-10-14; `monsters/special` reviewed, C 102 / I 85 / L 7; run:2026-10-14-mon-special 390 144 checks, 0 mismatches) |
| [0019](done/0019-items-uniques-sets.md) | Items: unique and set selection, and the creation fallbacks | done | — (closed 2026-10-14; `items/uniques-sets` reviewed, C 69 / I 51 / L 6; run:2026-10-14-uniques and -uniques-forced, 0 mismatches) |
| [0020](done/0020-backlog-sweep-2.md) | Backlog sweep 2: doc follow-ups, the classic TC replay and the Acts III–V owner session | done | — (closed 2026-10-15; P4 run:2026-10-15-acts-3-5, 155 215 checks, 0 mismatches, every case reproduced; drlg/preset revision → spec-writer backlog) |
| [0021](done/0021-items-affixes.md) | Items: affixes (alvl, magic and rare affix picks, rare names, automagic) | done | — (closed 2026-10-14; `items/affixes` reviewed, C 110 / I 45 / L 5; run:2026-10-14-affixes, 3 102 creations, 0 mismatches) |
| [0022](done/0022-drlg-maze-warps.md) | DRLG: the maze generator, act links and warps | done | — (closed 2026-10-15; `drlg/maze` C 105 / I 26 / L 3 and `drlg/warps` C 86 / I 35 / L 6 reviewed; run:2026-10-15-drlg-maze, 189 355 checks, 0 mismatches) |
| [0023](done/0023-objects.md) | Objects: population, placement and creation rolls (retires the objects window oracle) | done | — (closed 2026-10-15; `objects` reviewed, C 130 / I 57 / L 5; run:2026-10-15-objects, 142 540 checks, 0 mismatches) |
| [0024](done/0024-items-properties.md) | Items: base stats and properties (ItemInitStats, the property roll, ethereal, sockets) | done | — (closed 2026-10-14; `items/properties` reviewed, C 125 / I 36 / L 6; run:2026-10-14-props and -props-forced, 2 281 creations, 0 mismatches; `save/d2s` reviewed) |
| [0025](done/0025-monsters-stats.md) | Monsters: stats per level, difficulty and player count; mod effects | done | — (closed 2026-10-15; `monsters/stats` reviewed, C 94 / I 54 / L 5; run:2026-10-15-mon-stats, 4 571 creations, 0 mismatches) |
| [0026](done/0026-drlg-outdoor.md) | DRLG: the outdoor generator (act layouts, borders, paths, LvlSub) | done | — (closed 2026-10-15; `drlg/outdoor` reviewed, C 166 / I 23 / L 3; run:2026-10-15-drlg-outdoor, 572 211 checks, 0 mismatches) |
| [0027](0027-backlog-sweep-3.md) | Backlog sweep 3: the follow-ups of plans 0021–0026 (object marks and out-room grids predicted, items chain run, berserk, levels 39 and 134) | in-progress | P1 and P2 accepted and merged 2026-10-15 (level 134 a named boundary); P3 (reverser, harness) next, then P4 |
| [0028](done/0028-data-strings.md) | Data: string tables at run time, confirmed and specified | done | — (closed 2026-10-15; `specs/data/strings` reviewed, C 59 / I 37 / L 4; run:2026-10-15-strings, 0 mismatches) |
| [0029](done/0029-items-sockets-runewords.md) | Items: socket filling, gems, runes and jewels, runeword activation | done | — (closed 2026-10-15; `items/sockets-runewords` reviewed, C 74 / I 73 / L 9; run:2026-10-15-sockets, 351 inserts, 50 runewords, 0 mismatches) |
| [0030](0030-items-cube.md) | Items: the Horadric Cube (recipe matching, input checks, output construction) | in-progress | P0, P1 and P1b accepted and merged 2026-10-15 (CubeMain, cube saves; items/0008, C 2 / I 57); P2 (reverser, harness) after 0029·P2 |
| [0031](0031-items-vendors.md) | Items: vendor stock and gambling | in-progress | P0, P1 and P1b accepted 2026-10-15 (Npc, Gamble, StorePage, vendor columns; items/0009, C 1 / I 42); P2 (reverser, harness) next, its first step loads the vendor saves |
| [0032](0032-items-quest-drops.md) | Items: quest drops, quest rewards and special drops (+ the monsters/pool `boss` case) | in-progress | approved 2026-10-15; P0 (archivist: quest bits in saves) next; P2 after 0031·P2 (NPC action) |
| [0033](0033-hirelings.md) | Hirelings: stock, names, stats and the saved mercenary (+ the four hireling classes of monsters/pool) | in-progress | P0 (with fixes), P1 and P1b accepted 2026-10-15 (Hireling, HireDesc, merc key; hirelings/0001, C 11 / I 50); P2 after 0031·P2, its first step loads the merc saves |
| [0034](0034-player-creation.md) | Player: new character, starting items, experience and level-up | in-progress | P1 and P1b accepted with fixes 2026-10-15 (player/0001, C 3 / I 41; boundary: chain to props.py, ItemCreate oracle fallback); P0 (archivist: CharStats, Experience, CharTemplate) next, then P2 |
| [0035](0035-data-calc.md) | Data: the calc formulas (`*code.bin`, the compiler and the evaluator) | in-progress | P1 accepted 2026-10-15 (data/0005, encoding and compiler `[C]`: 1 790 cells, four pools rebuilt, 0 mismatches; evaluator `[I]`); P0 (archivist: formula docs, registers `SURVEY calc` as the gate survey) next, then P2 |
| [0036](0036-human-wiki-readme.md) | A human wiki over the reviewed specs (ADR-0012, not published), and a refreshed main README | in-progress | approved 2026-10-15; **last in the queue**: P0 (archivist: gate rules) any time, P1–P2 (spec-writer) after the other plans' specs |

## Run order (unattended queue, set 2026-10-15)

The owner approved plans 0027–0036 together, to run without them. Phases with the human owner are gone: plan 0020
Phase 4 is agent-driven, with owner play as the fallback. Each lane takes the first phase of its queue whose
prerequisites have landed. A lane that finishes a phase files its review request in the backlog and moves on; the
architect reviews in landing order. Harness budget: 3–4 slots (ADR-0011). Give every harness phase its slots in the
prompt.

| Lane | Queue, in order | Notes |
|---|---|---|
| **archivist** (no slots) | 0027·P1 → 0029·P0 → 0030·P0 → 0031·P0 → 0033·P0 → 0034·P0 → 0032·P0 → 0035·P0 → 0036·P0 | 0027·P1 first: its `tbk` fix unblocks 0030 and 0032's cow recipes. Each table phase regenerates the `excel_layout` baseline; merge one at a time. |
| **reverser, static** (Ghidra; parallel copies allowed) | 0027·P2 → 0029·P1/1b → 0030·P1/1b → 0031·P1/1b → 0033·P1/1b → 0034·P1/1b → 0032·P1/1b → 0035·P1 | A P1 needs its P0's table doc only for column names; it can start before P0 merges if the lane reads the `.txt` header. |
| **reverser, harness** (slots) | 0020·P4 · 0027·P3 · 0028·P1 → 0029·P2 → 0030·P2 → 0031·P2 → 0033·P2 → 0032·P2 → 0034·P2 → 0035·P2 | The first three are independent, so give them separate slots. 0031·P2 lands the `d2pilot.py npc` action, which 0033·P2 and 0032·P2 need. 0030·P2 needs 0029's socket model. |
| **spec-writer** | 0028·P2 · 0027·P4 · each plan's spec phase after its P2 → 0036·P1 → 0036·P2 | 0036 runs last, over whatever is `reviewed` when it starts. |

Earlier suggested orders (plans 0021–0026) are superseded by this table.
