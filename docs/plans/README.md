# Plans index

Next free number: **0053**

Lane runs (agent usage, review verdicts, fix counts by category) are logged in the [lane run ledger](metrics.md).

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
| [0037](done/0037-combat-formulas.md) | Combat formulas: to-hit, damage, resistances, defences and on-hit effects (first simulation plan, ADR-0014) | done | — (closed 2026-10-17; `combat/formulas` reviewed, C 190 / I 139 / L 20; run:2026-10-16-combat with the resume lane, 40 logs, 40 655 events, 0 mismatches; wiki/combat refreshed; follow-ups: reverser (event-9 handler, state 52, *Fleshripper* log, total ≤ 0 counter, fire count), archivist (DifficultyLevels Hell 25)) |
| [0038](0038-inferred-claims-sweep.md) | Inferred-claims sweep: which `[I]` in the reviewed specs one more run, a re-check of kept logs or a static second source raises to `[C]` | approved | approved 2026-10-16 (owner, unattended); **P0 accepted** 2026-10-16 (with fixes; [batch list](0038-inventory/README.md#5-batch-list)); P1 static batches any time; P2 harness batches in the slots 0037·P2 leaves free; P3 re-tag after 0036·P2 |
| [0039](done/0039-backlog-sweep-4.md) | Backlog sweep 4: the static loose ends and the open questions a reading settles | done | — (closed 2026-10-20, owner; P0, P1a–c and P2 rounds 1–2 accepted with fixes; the data/excel fold (P1b (a), P1c (a), its 11 W1) moved to plan 0038 Phase 3's data/excel cluster, after H3b) |
| [0040](done/0040-drlg-room-lifecycle.md) | Room lifecycle: activation, release, the inactive-unit restore and the wanderers | done | — (closed 2026-10-17; `drlg/lifecycle` reviewed, C 78 / I 70 / L 8; run:2026-10-17-lifecycle, 13 sessions, 2 215 807 checks, 0 mismatches; wiki/levels section added; follow-ups: reverser (town reachability, champion paths, the flag-1 call, symbol tags, the class-522 `0x400` records)) |
| [0041](done/0041-stats-and-states.md) | Stats and states: how a unit's final stats add up, and how timed states live and die (ADR-0014 phase 2) | done | — (closed 2026-10-17; `stats/aggregate` C 64 / I 42 / L 5, `stats/states` C 43 / I 46 / L 6 and the overview C 13 / I 4 / L 3 reviewed; run:2026-10-17-stats, 18 sessions, 0 mismatches; no oracle of plans 0034/0037 replaced; follow-ups: spec-writer (wiki page), reverser (shrine-and-well addendum, checker chaining and tests)) |
| [0042](done/0042-quests-travel.md) | Quests and travel: the quest state machines, waypoints, town portals and level entry | done | — (closed 2026-10-20; `quests/progression` C 114 / I 316 / L 6, `quests/travel` C 68 / I 80 / L 4 and the `quests` overview reviewed; run:2026-10-17-quests, run:2026-10-18-quests2 and run:2026-10-19-quests3, 0 mismatches; save/d2s E1's load rule `[C]`; follow-ups: plan 0044 (two-client cases), the owner-play entry (optional), archivist (the quest recipes), spec-writer (a quests wiki page)) |
| [0043](done/0043-items-economy.md) | Item economy: prices, repair, gold and durability wear | done | — (closed 2026-10-20; `items/economy` reviewed, C 125 / I 83 / L 12; run:2026-10-17-economy and run:2026-10-19-economy2, P2b re-tag accepted 2026-10-19; wiki/economy written; follow-ups: plan 0044 (trading, party gold split, game types 1 and 2), plan 0038 (the two `[L]` remainders), archivist (quest recipes in test_d2s, UniqueItems `carry1`), quest-drops event-7 route) |
| [0044](done/0044-multiplayer-branches.md) | Multiplayer branches: the two-client cases of the reviewed specs | done | — (closed 2026-10-20; P1 multiplayer/0001, 32 cases; P2 run:2026-10-20-two-clients, 19 sessions on slots 1 and 2, 0 mismatches, port-4000 precondition met; P3 re-tag `lane/p44s` accepted with fixes: 11 specs, `[C]` +28; plan 0038's d-2c rows recorded in its inventory § 2.6; follow-ups: owner play MP12–MP14, MP17 (optional), reverser agent-stageable shortfalls and MP26's § 6 bullet) |
| [0045](0045-skills-missiles-machinery.md) | Skills and missiles, the machinery: dispatch, packets, missiles, event handlers (ADR-0014 phase 3, part 1) | approved | approved 2026-10-20 (owner); drafted 2026-10-20 (`lane/plans45`); with ADR-0020 (accepted 2026-10-20); P0 archivist, P1 three static batches, P1b, P2 two slots, P3 spec, P4 wiki; **Phase 1 closed 2026-10-20** (P1.1–P1.3 and P1b accepted with fixes); **P2 part 1 accepted with fixes 2026-10-27** (run:2026-10-25-skills, 0 mismatches over 335 618 checks); **P2 part 2 accepted with fixes 2026-10-27** (run:2026-10-27-skills, 0 mismatches; refusals at the request, C2 and Raise Skeleton named short): **Phase 2 done**; **P3 accepted with fixes 2026-10-27** (`lane/s45p3`: skills/README, dispatch, missiles reviewed): 0050·P2, 0046·P2 and 0052's approvability open; P4 (wiki) may start |
| [0046](0046-skills-function-catalogue.md) | Skills and missiles, the function catalogue: every numbered skill and missile function (ADR-0014 phase 3, part 2) | approved | approved 2026-10-20 (owner); drafted 2026-10-20 (`lane/plans45`); P0 accepted 2026-10-20 (`lane/p46a`: function index, 310 entries); P1: fifteen static batches in the plan's order (9a–9d, the classes, 10, 8a–8c), one at a time; all fifteen accepted by 2026-10-21 (9a–9d, the seven classes, 10 `item`, 8a–8c; `lane/p46m15` the last), **P1 closed 2026-10-21** (304 entries by these batches, the six `general` tier-A entries by plan 0045: 310 of 310); P2 open since 0045·P3's review (2026-10-27), one slot (takes the Baal Tentacle stale-word item); P3 released, in the spec-writer queue's order |
| [0047](done/0047-simulation-shortfalls.md) | Simulation shortfalls: the named remainders of the combat, stats and travel runs | done | — (closed 2026-10-25; P1, P2, P2b and P3 (both parts) accepted with fixes; run:2026-10-20-shortfalls and run:2026-10-21-shortfalls2, 0 mismatches; final at `[I]`: the walking block, the magic cap, cold flat absorb, the leech after a defender's handler, the 256 floor, shrines and wells 21 of 50, mode-0 waypoint activations 7 of 20) |
| [0048](done/0048-seed-to-world.md) | Seed to world: the core specs composed end to end, with the last in-chain oracles retired | done | — (closed 2026-10-21; `chain` reviewed, C 89 / I 7 / L 6; run:2026-10-21-chain2, 37 logs, 0 mismatches, 2 189 oracle-free populations; 8 in-chain oracles retired; wiki/seed-to-world written; follow-ups: archivist (MonEquip table doc), chain's six `[L]` for a later plan) |
| [0049](done/0049-backlog-sweep-5.md) | Backlog sweep 5: the static loose ends, the recipe register and the gate warnings | done | — (closed 2026-10-20; P0, P1 and P2 accepted with fixes; ten specs edited (eight from P1's readings); P1 items 6 and 13 optional, open outside the plan) |
| [0050](0050-animation-frame-timing.md) | Animation and frame timing: unit modes, frame counts, rates and breakpoints, movement speed (ADR-0014 phase 4) | approved | approved 2026-10-25 (owner), in effect 2026-10-27 (0045·P2 part 1 accepted; P0/P1/P1b open); drafted 2026-10-25 (`lane/plans50`) ahead of its gate; P0 archivist (`animdata.d2`, `monseq`, the timing columns), P1 three static batches, P1b, P2 one slot, P3 spec, P4 wiki; **P0/P1/P1b start once 0045·P2 is accepted, P2 once 0045·P3 is reviewed** (ADR-0016, ADR-0020); P0, P1b part 1, P1.1, P1.2 and P1.3 accepted with fixes 2026-10-27: **Phase 1's batches done**; **P1b part 2 and P2 (one slot) may start** (P2's gate, 0045·P3's review, open since 2026-10-27) |
| [0051](done/0051-backlog-sweep-6.md) | Backlog sweep 6: the catalogue's column readers, the static optionals and the routing of the rest | done | — (closed 2026-10-27; P0a accepted, P0b, P1a, P1b and the States item 3a fold (`lane/a51f`) accepted with fixes; the sixteen archivist entries closed, the Phase 1a entries annotated for their plan 0038 batches, the two Phase 1b entries closed; P2: the plan 0042 owner play closed at approval, the patch_d2, Diablo-pair and plan 0044 owner entries annotated "stay open" (owner, 2026-10-25); the plan 0044 shortfalls entry stays open for the optional two-client run) |
| [0052](0052-monster-ai.md) | Monster AI: the AI tick, target and skill choice, and the path request it makes (ADR-0014 phase 5) | proposed | first draft 2026-10-25 (`lane/plans50`); approvable since 0045·P3's review (2026-10-27; ADR-0020); **re-drafted 2026-10-27** (`lane/plans52`): P0 archivist, P1.1 machinery then eight to twelve catalogue batches, P1b, P2 one slot (after 0050·P3's review and its own P1.1 and tier reviews), P3a machinery and tier, P3b catalogue, P4 wiki; the path search a boundary with its own plan, drafted at the P1.1 review; **awaiting the owner's approval** and the answers to its eight scoping questions (each with a recommendation), the seventh on [ADR-0022](../adrs/0022-scope-server-frame.md) (proposed) |

## Run order (set 2026-10-25, plans 0038–0052)

Drafted by the architect (`lane/plans50`) with plans 0050–0052 and **approved by the owner on 2026-10-25**: this is
the current queue, and it replaces the 2026-10-20 queue below (kept for its links and rulings). It keeps that queue's rules: each lane takes the first phase of its queue whose
prerequisites have landed and whose gate is open; a phase whose prerequisite has not landed is skipped, not waited
on; a lane that finishes a phase files its review request in the backlog and moves on; the architect reviews in
landing order.

**Limits** (unchanged): at most **two harness lanes**, on slots **1 and 2** (slot 0 is the owner's), so at most two
games at once; at most **two static lanes** and at most **two headless Ghidra** at once (`-Xmx3G` each); heavy replays
under `systemd-run --user --scope -p MemoryMax=4G`; lanes past about 4 h checkpoint, write a resume note, and a fresh
lane resumes on the same branch.

**State on 2026-10-27** (architect, `lane/plans52`; the 2026-10-25 state is in git history). **Done:** plan 0051
(closed); plan 0045 Phase 2 (both parts) and Phase 3 (`lane/s45p3`: skills/README, dispatch and missiles reviewed);
plan 0050 P0, P1b part 1, P1.1 and P1.2; plan 0038 H4a, H5d and H1b, and the Phase 3 monsters and drlg/collision
clusters with their wiki refresh. **Done since:** 0050·P1.3 (accepted with fixes 2026-10-27). **May start now:** 0050·P1b part 2 (static lane B, no Ghidra) and 0050·P2 (one harness slot). **Open, not started:** 0038 H1a (its family
rule met at the H1b review); 0045·P4 (wiki); 0046·P2 (one slot, after 0050·P2 has started: owner, 2026-10-25). **Awaiting the owner:** plan 0052's approval and its
scoping questions, and ADR-0022 (proposed). Still to run after them: plan 0038's batches H1a → H3b → H6e2 → H6e1 →
H6b → H6a → H6c → H6f → H6g (the owner's 2026-10-20 order, family rules of
[§ 7](0038-inventory/README.md#7-priority-order)) and its Phase 3 clusters as their batches land (objects after
H6e2); 0050·P1b part 2, P2, P3 and P4; 0046·P2, P3 and P4.

**Gates of the new plans:** 0051 had none (**closed 2026-10-27**). 0050·P0/P1/P1b open since 0045·P2's acceptance,
0050·P2's since 0045·P3's review (2026-10-27); 0050·P2's own P1.3 review passed (2026-10-27), so it may start. 0052 is approvable since
0045·P3's review; once the owner approves it, its P0 and P1.1 may start, and its P2 waits for 0050·P3's review and its
own P1.1 and tier reviews. 0046·P2 is open since 0045·P3's review. ADR-0022 (if accepted): its plan's tables and static
reading after 0052·P1.1's review, its harness after 0052·P3a's.

| Lane | Queue, in order | Notes |
|---|---|---|
| **architect** | each phase below in landing order (0050·P1b part 2 and 0050·P2 next) → **on the owner's answers:** 0052's status and its run-order rows; at 0052·P1.1's review, draft the path search plan; if ADR-0022 is accepted, draft its plan at 0052·P1.1's review | Each review fills the ledger row. |
| **archivist** (no slots, no Ghidra) | ~~0051·P0a → 0051·P0b~~ → ~~0050·P0~~ (done) → the open archivist entries (the `lane/p50b` MonStats timing entry first, then the H1b and 0045·P2 part 2 entries) → **0052·P0 (awaiting the owner)** → the path search plan's and ADR-0022's table phases, if approved | The `lane/p50b` entry's item 2 survey may add a 0050·P2 case: before 0050·P2 starts. |
| **reverser, static lane A** (Ghidra 1) | ~~0051·P1a~~ → ~~0050·P1.1 → 0050·P1.2~~ (done) → ~~0050·P1.3~~ (done) → **0052·P1 catalogue batches (awaiting the owner)** | 0050·P1 is phase (4)'s critical path. |
| **reverser, static lane B** (Ghidra 2) | ~~0051·P1b~~ → ~~0050·P1b part 1~~ (done) → the static reverser entries (the BuildDamage readings, H1b's host-callback setter, H5d's waypoint mode) → **0052·P1.1 (awaiting the owner; it may start beside 0050·P1.3)** → 0050·P1b part 2 (no Ghidra; may start, P1.3 reviewed) → 0052·P1 batches beside lane A → 0052·P1b | One batch per lane at a time; P1.1 is 0052's critical path. |
| **reverser, harness lane H1** (slot 1) | ~~H4a → H5d → H1b~~ (done) → H1a → plan 0038 batches in the order above → 0046·P2 (one slot) | Yields its slot between batches if a two-client run asks for both. |
| **reverser, harness lane H2** (slot 2) | ~~0045·P2~~ (done) → plan 0038 batches alternating with H1 while 0050·P1.3 was reviewed → **0050·P2** (one slot; may start, P1.3 reviewed 2026-10-27) → plan 0038 batches → the two-client tail (optional, both slots) → **0052·P2 (awaiting the owner; after 0050·P3's review)** | 0050·P2 runs before 0046·P2 (owner, 2026-10-25); 0046·P2 may take whichever slot is free once 0050·P2 has started. |
| **spec-writer** | ~~0045·P3~~ (done) → 0045·P4 (wiki) → 0038·P3 clusters as their batches land → 0050·P3 → 0050·P4 → 0046·P3 → 0046·P4 → **0052·P3a → 0052·P3b → 0052·P4 (awaiting the owner)** | Specs edited by two plans merge one at a time, the earlier plan's first. |

**Why this order.** 0045·P3 opens three gates at once (0050·P2, 0046·P2 and 0052's approval), so it moves ahead of
the 0038 clusters in the spec-writer queue once 0045·P2 is accepted. Plan 0051 needed no slot and filled both static
lanes and the archivist (closed 2026-10-27); its Phase 0 also gives 0045·P3 and 0046·P3 table docs that already link the catalogue's
column readers. 0050 is small and mostly data, and its P1 can run while the harness lanes finish 0045·P2 and the 0038
batches; its P2 takes one slot, so 0038 keeps the other. 0050·P2 goes before 0046·P2 on the harness because it is on
phase (5)'s path and 0046 gates nothing (ADR-0020).

**Owner decisions (2026-10-25):**
- **0050, 0051 and this queue:** approved; 0050's approval takes effect when 0045·P2 is accepted.
- **Spec-writer:** 0045·P3 goes ahead of the remaining 0038 Phase 3 clusters.
- **0052:** its gate is the review of 0045's spec (P3), per ADR-0020 (confirmed); it stays `proposed` until then. Its
  scoping questions stay open until the re-draft at the gate; the owner leans towards pathing as its own part.
- **Movement:** the split is kept: speed and the per-frame step in 0050, the path itself in phase (5).
- **Backlog:** the plan 0042 owner-play entry closed as dropped (0051 Phase 2).
- **The two-client tail** (the plan 0044 shortfalls): optional and deferred; it stays in the queue as optional.
- **Harness:** 0050·P2 runs before 0046·P2.
- **Planning after 0052 (owner, 2026-10-27):** no new plans before then. At the review of 0045·P3, when it re-drafts
  0052, the architect also proposes what follows it. Phase (5) is the last phase of ADR-0014, so anything beyond the
  remaining 0038/0046 tails needs a scope ADR for the owner. The aim is to have that ready before 0052's harness phase
  starts, so the static lanes and the archivist do not go idle while 0052·P2 waits on 0050·P3.

**What follows 0052 (architect's proposal, 2026-10-27, for the owner).** Drafted as
[ADR-0022](../adrs/0022-scope-server-frame.md) (proposed); the candidates it weighs:
1. **The server frame composed** (ADR-0022's decision, *recommended*): `GameTick`'s passes, the per-unit update order,
   the event queue and the timers, checked in frame windows where every entry seed is asserted. It is the one piece
   that lets the resynchronised entries of phases (1)–(5) chain across units, and its first phases are tables and
   static reading that can start at 0052·P1.1's review.
2. **A second inferred-claims sweep** over the simulation and game-rules specs (1 087 `[I]` over eight reviewed rows,
   none in plan 0038's inventory). No ADR needed; recommended as the harness companion once 0038's batches drain.
3. **Player-side game rules** (item use, pickup and the ground drop's placement, corpses, death and respawn, the
   stash): an ADR-0017-style extension; not recommended now (little gain over per-event plans).

The three core areas (items, monster spawning, DRLG) have every row reviewed; their remaining `[I]` are plan 0038's.
Stopping at phase (5) is the fourth option (ADR-0022 § Alternatives).

## Run order (unattended queue, set 2026-10-20, plans 0038–0049)

**Superseded** on 2026-10-25 by the queue above (owner); kept for its rulings and the links that cite it.

The owner approved plans 0045–0049 and ADR-0020 on 2026-10-20 and made this the current queue. It replaces the
2026-10-16 table (plans 0037–0044), which is in git history. Plan 0043 is closed (`lane/c43` merged); plan 0042's
Phase 2 part 3 is accepted (`lane/p42r` merged 2026-10-20) and the plan closes after the review of its Phase 3
(`lane/p42s`) and the re-tag. Each lane takes the first phase of its queue whose prerequisites have landed and whose
gate is open; a phase whose prerequisite has not landed is skipped, not waited on; a lane that finishes a phase files
its review request in the backlog and moves on; the architect reviews in landing order.

**Limits** (unchanged): at most **two harness lanes**, on slots **1 and 2** (slot 0 is the owner's), so at most two
games at once; at most **two static Ghidra lanes** (`-Xmx3G` each); heavy replays under `MemoryMax=4G`; lanes past
about 4 h checkpoint and a fresh lane resumes on the same branch.

**Owner decisions (2026-10-20):**
- **0039:** closed; its data/excel fold (P1b (a), P1c (a), the 11 data/excel W1) is an item of plan 0038 Phase 3's
  data/excel cluster, after H3b.
- **0038:** every remaining batch is kept, **core and enabler batches first**: H5b (accepted 2026-10-20) → H2a (accepted 2026-10-20) → H2b → H2c →
  H4a → H5d → H1b → H1a → H3b, then the creation-path batches H6e2 → H6e1 → H6b → H6a → H6c → H6f → H6g. The family
  rules of [§ 7](0038-inventory/README.md#7-priority-order) still hold (H2a → H2b → H2c; H5d after H5b; H1b before
  H1a; H6e1 and H6e2 one at a time).
- **0044:** closed 2026-10-20 (P3 re-tag accepted; both slots released at P2).
- **Phase order:** simulation phase (4) is **animation and frame timing**, before monster AI, which becomes phase (5)
  (ADR-0014 lets the architect reorder phases 3–5 by plan; recorded in ADR-0020). No plan for either yet.
- **`patch_d2.mpq`:** the 1.14b/1.14d entry stays open and parked.
- **0042:** closed 2026-10-20 (quests specs reviewed after the part 3 re-tag). The waypoint activation from mode 0 stayed short, so it moves to plan 0047.

| Lane | Queue, in order | Notes |
|---|---|---|
| **architect** | `lane/p42s` → H5b → then each phase below in landing order | Each review fills the ledger row. |
| **archivist** (no slots) | 0049·P0 → 0045·P0 → 0046·P0 (after 0045·P1.3's review) | 0045·P0 changes layouts: regenerate the `excel_layout` baseline and merge alone. |
| **reverser, static lane A** (Ghidra 1) | 0045·P1.1 → 0045·P1.2 → 0045·P1.3, with 0045·P1b beside them → 0046·P1 batches | 0045·P1 is the critical path of phase 3. |
| **reverser, static lane B** (Ghidra 2) | 0049·P1 → 0048·P0 → 0048·P1 → 0047·P1's waypoint reading (if 0042 leaves it short) → 0046·P1 batches | 0048·P0 needs no Ghidra and may run in this lane's idle time. |
| **reverser, harness lane H1** (slot 1) | H5b (in flight) → **0044·P2 (both slots)** → 0047·P1 → 0047·P2 → 0047·P2b → 0048·P2 → **0045·P2 (both slots)** → 0046·P2 | 0047·P1 is tools and staging, no game. A phase whose prerequisite has not landed is skipped, not waited on. |
| **reverser, harness lane H2** (slot 2) | plan 0038 batches in the order above | Yields its slot to 0044·P2 and to 0045·P2 while they run; resumes the next batch after. |
| **spec-writer** | 0042·P3 re-tag (`lane/p42s`) → 0044·P3 re-tag → 0038·P3 clusters as their batches land (drlg/lifecycle first: the H7a entry is released) → 0049·P2 → 0047·P3 → 0045·P3 → 0045·P4 → 0048·P3 → 0048·P4 → 0046·P3 → 0046·P4 | Specs edited by two plans merge one at a time, the earlier plan's first. |

**Why this order.** 0045 is the next simulation phase and the single largest block of value: it retires the most-cited
oracles of the reviewed specs (the skill and missile packets, the event handlers, `MonAttackStats`). Its static
phases fill both Ghidra lanes' near future while the harness lanes finish 0038, 0044 and the cheap 0047 cases, so
0045·P2 starts with its P1 reviewed. 0048 is the core areas' conformance check and needs only one slot. 0049 and 0047·P1
need no slot and clear the backlog and the checkers before the next harness work.

**Phases 4 and 5.** Phase (4) is animation and frame timing, phase (5) monster AI (owner, 2026-10-20). Plans
[0050](0050-animation-frame-timing.md) (phase (4)) and [0052](0052-monster-ai.md) (phase (5), a first draft) were
drafted on 2026-10-25, ahead of their gates, at the owner's request: ADR-0016 lets phase (4)'s phases start once
0045·P2 is accepted (ADR-0020), and ADR-0020 lets phase (5)'s plan follow 0045·P3's review.
