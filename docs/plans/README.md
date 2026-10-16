# Plans index

Next free number: **0039**

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
| [0027](done/0027-backlog-sweep-3.md) | Backlog sweep 3: the follow-ups of plans 0021–0026 (object marks and out-room grids predicted, items chain run, berserk, levels 39 and 134) | done | — (closed 2026-10-16; object marks and out-room grids predicted; run:2026-10-15-items-chain (889 creations, 219 end to end), -berserk-forced, -cow-arcane (level 39 `[C]`), 0 mismatches; level 134 a named boundary; TC-named cases stay `[I]`) |
| [0028](done/0028-data-strings.md) | Data: string tables at run time, confirmed and specified | done | — (closed 2026-10-15; `specs/data/strings` reviewed, C 59 / I 37 / L 4; run:2026-10-15-strings, 0 mismatches) |
| [0029](done/0029-items-sockets-runewords.md) | Items: socket filling, gems, runes and jewels, runeword activation | done | — (closed 2026-10-15; `items/sockets-runewords` reviewed, C 74 / I 73 / L 9; run:2026-10-15-sockets, 351 inserts, 50 runewords, 0 mismatches) |
| [0030](done/0030-items-cube.md) | Items: the Horadric Cube (recipe matching, input checks, output construction) | done | — (closed 2026-10-16; `items/cube` reviewed, C 118 / I 82 / L 6; run:2026-10-15-cube, 182 transmutes, 0 mismatches) |
| [0031](done/0031-items-vendors.md) | Items: vendor stock and gambling | done | — (closed 2026-10-16; `items/vendors` reviewed, C 70 / I 37 / L 4; run:2026-10-15-vendors, 94 stock builds, 325 gamble windows, 0 mismatches; store seed = game-seed draw 3; level-up, multiplayer and purchases stay `[I]`) |
| [0032](done/0032-items-quest-drops.md) | Items: quest drops, quest rewards and special drops (+ the monsters/pool `boss` case) | done | — (closed 2026-10-16; `items/quest-drops` reviewed, C 71 / I 83 / L 8; run:2026-10-16-quest-drops, 0 mismatches over 53 sessions; items/tc B6 and monsters/pool E4 `boss` `[C]`; Mephisto done, Countess, Hell Hellforge, Cow King stay `[I]` pending the owner addendum) |
| [0033](done/0033-hirelings.md) | Hirelings: stock, names, stats and the saved mercenary (+ the four hireling classes of monsters/pool) | done | — (closed 2026-10-16; `hirelings` reviewed, C 89 / I 39 / L 8; run:2026-10-16-hirelings, 53 hire tables, 49 hires, 33 merc headers, 0 mismatches; monsters/pool E2 hireling classes closed, 560 has no row; items/quality M3 merc MF `[C]`; save/d2s merc header read side `[C]`) |
| [0034](done/0034-player-creation.md) | Player: new character, starting items, experience and level-up | done | — (closed 2026-10-16; `player/creation` reviewed, C 79 / I 39 / L 6; run:2026-10-16-player, 35 new characters, 269 item copies, 20 level-ups, 0 mismatches; class byte > 7 → reverser backlog) |
| [0035](done/0035-data-calc.md) | Data: the calc formulas (`*code.bin`, the compiler and the evaluator) | done | — (closed 2026-10-16; `data/calc` reviewed, C 68 / I 67 / L 3; run:2026-10-16-calc, 44 529 evaluations, 0 mismatches, 14/14 stock opcodes; `max`/`rand`/missile reader/item caller → reverser backlog) |
| [0036](done/0036-human-wiki-readme.md) | A human wiki over the reviewed specs (ADR-0012, not published), and a refreshed main README | done | — (closed 2026-10-16; `docs/wiki/` index plus ten pages over every reviewed spec, README refreshed; two spec rulings → spec-writer backlog) |
| [0037](0037-combat-formulas.md) | Combat formulas: to-hit, damage, resistances, defences and on-hit effects (first simulation plan, ADR-0014) | in-progress | approved 2026-10-16; P0 accepted 2026-10-16 (ElemTypes, MonMode, PlrMode; combat sections; gate survey `combat`); P1/1b accepted with fixes 2026-10-16 (combat/0001 static `[I]`; `HireableBossDamagePercent` has a reader; mercenary case added); P2 harness next, after the static leftovers |
| [0038](0038-inferred-claims-sweep.md) | Inferred-claims sweep: which `[I]` in the reviewed specs one more run, a re-check of kept logs or a static second source raises to `[C]` | approved | approved 2026-10-16 (owner, unattended); P0 inventory (architect) and P1 static batches any time; P2 harness batches in the slots 0037·P2 leaves free; P3 re-tag after 0036·P2 |

## Run order (unattended queue, set 2026-10-15)

The owner approved plans 0027–0036 together, to run without them. Phases with the human owner are gone: plan 0020
Phase 4 is agent-driven, with owner play as the fallback. Each lane takes the first phase of its queue whose
prerequisites have landed. A lane that finishes a phase files its review request in the backlog and moves on; the
architect reviews in landing order. Harness budget: 3–4 slots (ADR-0011), and since 2026-10-15 at most two harness lanes at once (OOM). Give every harness phase its slots in the
prompt.

| Lane | Queue, in order | Notes |
|---|---|---|
| **architect** | 0038·P0 (now; up to four parallel copies, one per cluster) | Phase 0's review fixes the 0038 batch list; no 0038 batch starts before it. |
| **archivist** (no slots) | 0027·P1 → 0029·P0 → 0030·P0 → 0031·P0 → 0033·P0 → 0034·P0 → 0032·P0 → 0035·P0 → 0036·P0 → 0037·P0 | 0027·P1 first: its `tbk` fix unblocks 0030 and 0032's cow recipes. Each table phase regenerates the `excel_layout` baseline; merge one at a time. |
| **reverser, static** (Ghidra; parallel copies allowed) | 0027·P2 → 0029·P1/1b → 0030·P1/1b → 0031·P1/1b → 0033·P1/1b → 0034·P1/1b → 0032·P1/1b → 0035·P1 → 0037·P1/1b; 0038·P1 (S1–S4) any time after the 0038·P0 review | A P1 needs its P0's table doc only for column names; it can start before P0 merges if the lane reads the `.txt` header. 0038's static batches take no slot and run in parallel copies beside any other phase. |
| **reverser, harness** (slots) | 0020·P4 · 0027·P3 · 0028·P1 → 0029·P2 → 0030·P2 → 0031·P2 → 0033·P2 → 0032·P2 → 0034·P2 → 0035·P2 → 0037·P2 ‖ 0038·P2 (H1 → H6, Phase 0 order) | The first three are independent, so give them separate slots. 0038·P2 runs only in what 0037·P2 leaves free: never more than two harness lanes in total. 0031·P2 lands the `d2pilot.py npc` action, which 0033·P2 and 0032·P2 need. 0030·P2 needs 0029's socket model. |
| **spec-writer** | 0028·P2 · 0027·P4 · each plan's spec phase after its P2 → 0036·P1 → 0036·P2 → 0037·P3 · 0038·P3 (per cluster, once its batches are accepted) | 0036 runs over whatever is `reviewed` when it starts. 0038·P3 and 0037·P3 merge monsters/stats, player/creation and data/calc one at a time. |

Earlier suggested orders (plans 0021–0026) are superseded by this table.

**Plan 0037 (added 2026-10-16, ADR-0014).** The owner's order is plan 0032 (Phase 2, then its spec), then plan 0036,
then 0037. No lane starts a 0037 phase before 0036 closes, even when its own queue is empty. 0037·P2 takes at most two
slots.

**Plan 0038 (added 2026-10-16).** The owner chose the inferred-claims sweep on 2026-10-16 and approved it to run
unattended. It is not a simulation plan, so ADR-0014's block does not apply. Its queue:
- **Phase 0** (architect) starts now. Its review fixes the batch list.
- **Phase 1 static batches** run any time after that review, beside 0036 and 0037.
- **Phase 2 harness batches** never push the harness above **two lanes at once** (OOM, 2026-10-15). Slot 0 stays the
  owner's. 0037·P2 has the slots first:
  - while it holds two, no 0038 batch runs;
  - while it holds one, one 0038 batch may run on one slot;
  - before 0037·P2 starts and after it ends, 0038 may use two.
- **Phase 3** (spec-writer) follows 0036·P2.
