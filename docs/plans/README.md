# Plans index

Next free number: **0050**

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
| [0039](0039-backlog-sweep-4.md) | Backlog sweep 4: the static loose ends and the open questions a reading settles | approved | approved 2026-10-16 (owner, unattended); no slot (P0 archivist, P1a–c static, P2 spec); P1a, P1b and P1c accepted with fixes (2026-10-16, 2026-10-17, 2026-10-17; Phase 1 done); P2 for P1a+P1b accepted with fixes (2026-10-17, `lane/p39s`); P2 round 2 (P1c fold, items/uniques-sets) accepted with fixes (2026-10-17, `lane/p39s2`); complete except data/excel (P1b (a), P1c (a), its 11 W1), folded with plan 0038 Phase 3 |
| [0040](done/0040-drlg-room-lifecycle.md) | Room lifecycle: activation, release, the inactive-unit restore and the wanderers | done | — (closed 2026-10-17; `drlg/lifecycle` reviewed, C 78 / I 70 / L 8; run:2026-10-17-lifecycle, 13 sessions, 2 215 807 checks, 0 mismatches; wiki/levels section added; follow-ups: reverser (town reachability, champion paths, the flag-1 call, symbol tags, the class-522 `0x400` records)) |
| [0041](done/0041-stats-and-states.md) | Stats and states: how a unit's final stats add up, and how timed states live and die (ADR-0014 phase 2) | done | — (closed 2026-10-17; `stats/aggregate` C 64 / I 42 / L 5, `stats/states` C 43 / I 46 / L 6 and the overview C 13 / I 4 / L 3 reviewed; run:2026-10-17-stats, 18 sessions, 0 mismatches; no oracle of plans 0034/0037 replaced; follow-ups: spec-writer (wiki page), reverser (shrine-and-well addendum, checker chaining and tests)) |
| [0042](0042-quests-travel.md) | Quests and travel: the quest state machines, waypoints, town portals and level entry | approved | approved 2026-10-16 (owner, unattended); ADR-0017 accepted; P0 reviewed 2026-10-16, P1/1b reviewed 2026-10-17 (accept with fixes); P2 part 1 (run:2026-10-17-quests) reviewed 2026-10-17 (accept with fixes); P2 part 2 (run:2026-10-18-quests2) reviewed 2026-10-19 (accept with fixes); P2 part 3 (the draw-bearing remainder, final) open, 2 slots; P3 may start in parallel, its review after part 3's; owner play optional |
| [0043](0043-items-economy.md) | Item economy: prices, repair, gold and durability wear | approved | approved 2026-10-16 (owner, unattended); ADR-0017 accepted; P0 reviewed 2026-10-17 (accept with fixes); P1/1b reviewed 2026-10-17 (accept with fixes, `lane/p43r`); P2 reviewed 2026-10-19 (accept with fixes, `lane/p43h`); P3 reviewed 2026-10-19 (accept with fixes, `lane/p43s`; items/economy reviewed); P2b (shortfall remainder, 1 slot, `lane/p43b`) open |
| [0044](0044-multiplayer-branches.md) | Multiplayer branches: the two-client cases of the reviewed specs | approved | approved 2026-10-16 (owner, unattended); ADR-0008 accepted on the port-4000 condition; P1 reviewed 2026-10-17 (accept with fixes; multiplayer/0001, 32 cases, 29 stageable); P2 open, both harness lanes on two non-zero slots; port-4000 precondition met 2026-10-17 (owner's `ufw status verbose`, plan log), so it waits only for two free slots; first step the driver's live test |
| [0045](0045-skills-missiles-machinery.md) | Skills and missiles, the machinery: dispatch, packets, missiles, event handlers (ADR-0014 phase 3, part 1) | proposed | drafted 2026-10-20 (`lane/plans45`); with ADR-0020 (proposed); P0 archivist, P1 three static batches, P1b, P2 two slots, P3 spec, P4 wiki |
| [0046](0046-skills-function-catalogue.md) | Skills and missiles, the function catalogue: every numbered skill and missile function (ADR-0014 phase 3, part 2) | proposed | drafted 2026-10-20; starts after 0045·P1.3's review (P0/P1), its P2 after 0045·P3's; ten static batches, P2 one slot |
| [0047](0047-simulation-shortfalls.md) | Simulation shortfalls: the named remainders of the combat, stats and travel runs | proposed | drafted 2026-10-20; P1 tools and staging (no slot), P2 one slot, P3 re-tag |
| [0048](0048-seed-to-world.md) | Seed to world: the core specs composed end to end, with the last in-chain oracles retired | proposed | drafted 2026-10-20; P0 oracle inventory, P1 models and `tools/chain.py`, P2 one slot, P3 spec, P4 wiki |
| [0049](0049-backlog-sweep-5.md) | Backlog sweep 5: the static loose ends, the recipe register and the gate warnings | proposed | drafted 2026-10-20; no slot (P0 archivist, P1 one static lane, P2 spec) |

## Proposed run order (plans 0045–0049, drafted 2026-10-20, for the owner's approval)

This section proposes a queue for plans 0045–0049. It does not replace the 2026-10-16 table below until the owner
approves the plans. It assumes plan 0043 closes (`lane/c43`) and plan 0042 closes after the reviews of `lane/p42r`
(Phase 2 part 3) and `lane/p42s` (Phase 3) and their re-tag; the branches in flight (`lane/h5b`, `lane/p42r`,
`lane/p42s`, `lane/c43`) are not changed by it.

**Limits** (unchanged): at most **two harness lanes**, on slots **1 and 2** (slot 0 is the owner's), so at most two
games at once; at most **two static Ghidra lanes** (`-Xmx3G` each); heavy replays under `MemoryMax=4G`; lanes past
about 4 h checkpoint and a fresh lane resumes on the same branch.

**Proposed changes to open plans** (owner decisions):
- **0039:** close it; its data/excel fold (P1b (a), P1c (a), the 11 data/excel W1) becomes an item of plan 0038
  Phase 3's data/excel cluster, after H3b.
- **0038:** keep every remaining batch, but run the **core and enabler batches first**: H5b (in flight) → H2a → H2b →
  H2c → H4a → H5d → H1b → H1a → H3b, then the creation-path batches H6e2 → H6e1 → H6b → H6a → H6c → H6f → H6g. The
  family rules of § 7 still hold (H2a → H2b → H2c; H5d after H5b; H1b before H1a; H6e1 and H6e2 one at a time). The
  alternative is to drop the seven H6 batches and leave those statements `[I]`.
- **0044:** unchanged; its P2 takes both slots at the first point both are free, which is expected when H5b ends.
- **0042:** no new phase. The waypoint activation from mode 0, if still short at the close, moves to plan 0047.

| Lane | Queue, in order | Notes |
|---|---|---|
| **architect** | `lane/p42r` → `lane/p42s` → H5b → then each phase below in landing order | Each review fills the ledger row. |
| **archivist** (no slots) | 0049·P0 (item 4 after `lane/p42r` merges) → 0045·P0 → 0046·P0 (after 0045·P1.3's review) | 0045·P0 changes layouts: regenerate the `excel_layout` baseline and merge alone. |
| **reverser, static lane A** (Ghidra 1) | 0045·P1.1 → 0045·P1.2 → 0045·P1.3, with 0045·P1b beside them → 0046·P1 batches | 0045·P1 is the critical path of phase 3. |
| **reverser, static lane B** (Ghidra 2) | 0049·P1 → 0048·P0 → 0048·P1 → 0047·P1's waypoint reading (if 0042 leaves it short) → 0046·P1 batches | 0048·P0 needs no Ghidra and may run in this lane's idle time. |
| **reverser, harness lane H1** (slot 1) | H5b (in flight) → **0044·P2 (both slots)** → 0047·P1 → 0047·P2 → 0048·P2 → **0045·P2 (both slots)** → 0046·P2 | 0047·P1 is tools and staging, no game. A phase whose prerequisite has not landed is skipped, not waited on. |
| **reverser, harness lane H2** (slot 2) | plan 0038 batches in the order above | Yields its slot to 0044·P2 and to 0045·P2 while they run; resumes the next batch after. |
| **spec-writer** | 0042·P3 re-tag (`lane/p42s`) → 0038·P3 clusters as their batches land (drlg/lifecycle first: the H7a entry is released) → 0049·P2 → 0047·P3 → 0045·P3 → 0045·P4 → 0048·P3 → 0048·P4 → 0046·P3 → 0046·P4 | Specs edited by two plans merge one at a time, the earlier plan's first. |

**Why this order.** 0045 is the next simulation phase and the single largest block of value: it retires the most-cited
oracles of the reviewed specs (the skill and missile packets, the event handlers, `MonAttackStats`). Its static
phases fill both Ghidra lanes' near future while the harness lanes finish 0038, 0044 and the cheap 0047 cases, so
0045·P2 starts with its P1 reviewed. 0048 is the core areas' conformance check and needs only one slot. 0049 and 0047·P1
need no slot and clear the backlog and the checkers before the next harness work.

**Phase 4 and 5.** No plan is written for monster AI or animation timing yet: ADR-0016 lets phase (4)'s plan follow
0045·P2's acceptance (ADR-0020, proposed). The architect proposes animation timing first (plan 0045 *Open questions*).

## Run order (unattended queue, set 2026-10-16, plans 0037–0044)

This table replaces the 2026-10-15 table, whose plans (0027–0036) are all done; that table is in git history. The
paragraphs on plans 0037 and 0038 below still hold. Each lane takes the first phase of its queue whose prerequisites
have landed and whose gate is open; a lane that finishes a phase files its review request in the backlog and moves on;
the architect reviews in landing order.

**Limits** (memory, 2026-10-15 and 2026-10-16): at most **two harness lanes** at once, each on its own slot from 1 to 8
(slot 0 is the owner's); at most **two static Ghidra lanes** (`-Xmx3G` each); replays under `MemoryMax=4G`. Give every harness
phase its slots in the prompt.

**Gates** (owner, 2026-10-16: plans 0039–0044 approved to run unattended; ADR-0016, ADR-0017 and ADR-0008 accepted).
0041 is closed (2026-10-17); its optional shrine-and-well addendum waits for an idle slot (backlog). 0042 and 0043 are open (ADR-0017); 0042's P2 part 3 is open (part 2 reviewed 2026-10-19) and its P3 may start; 0043's P2 and P3 are accepted (2026-10-19; items/economy reviewed); its P2b batch (the stock-reachable shortfalls, `lane/p43b`) is open, and the spec is re-tagged when it lands.
0044·P2 runs only after its lane has made TCP port 4000 unreachable from outside loopback, or confirmed it already is,
and recorded how in the run record (the owner's condition on ADR-0008); host and joiner on two non-zero slots. A phase
whose prerequisite has not landed is skipped, not waited on: the lane takes the next phase it can run.

| Lane | Queue, in order | Notes |
|---|---|---|
| **architect** | reviews in landing order: S2c, 0037·P2 resume, 0037·P3, then each phase below | H4b reviewed and merged 2026-10-16. The owner's decisions are recorded under *Gates*. |
| **archivist** (no slots) | 0039·P0 → 0041·P0 → 0042·P0 → 0043·P0 | Each table phase that changes a layout regenerates the `excel_layout` baseline; merge one at a time. 0042·P0's quest saves load in the first free slot or at the start of 0042·P2. |
| **reverser, static lane A** (Ghidra 1) | 0038: S2c (in flight) → S3b → S1a → S1e → S1f (if the S1e review accepts it) → then lane B's queue | The 0038 order is the inventory's § 7. |
| **reverser, static lane B** (Ghidra 2) | 0039·P1a → 0040·P1/1b → 0039·P1b → 0041·P1/1b → 0039·P1c → 0042·P1/1b → 0043·P1/1b → 0044·P1 | 0039's batches fill the gaps while a plan's P1 waits for its gate. 0039·P1a's B11 (b) is the S1f precondition: run it before S1f if lane A gets there first. |
| **reverser, harness lane H1** (one slot) | 0037·P2 resume (accepted 2026-10-17) → 0040·P2 (accepted 2026-10-17) → 0041·P2 → 0042·P2 → 0043·P2 → 0043·P2b → 0042·P2 part 3; while none of these is ready, the next 0038 batch of lane H2's queue | A new plan's P2 starts when its P1 review has landed. A P2 granted two slots takes lane H2's slot when its current batch ends, and 0038 pauses until it gives the slot back. |
| **reverser, harness lane H2** (one slot) | 0038 § 7 (H5c, H4b, H5e, H5a, H6d and H7a done): H5b → H2a → H2b → H5d → H6e2 → H1b → H6e1 → H6b → H6f → H6a → H3b → H4a → H6c → H6g → H1a → H2c | Batches of one logger family run one after another (§ 7). The plan 0038 Phase 2 leftovers (backlog 2026-10-16) ride on the next session that loads their logger. |
| **two-client** (both lanes' slots together) | 0044·P2 | Runs only when both lanes are free: lane H1 between two plan phases and lane H2 between two 0038 batches. |
| **spec-writer** | 0037·P3 (lane open) → 0038·P3 per cluster → 0037·P4 (wiki page, after the 0037 re-tag) → 0039·P2 → 0040·P3 → 0041·P3 → 0042·P3 → 0043·P3 → 0044·P3 | Specs edited by two phases (monsters/stats, player/creation, data/calc, objects, drlg/*) merge one at a time, the earlier plan's first. |

**Plan 0037 (added 2026-10-16, ADR-0014).** The owner's order is plan 0032 (Phase 2, then its spec), then plan 0036,
then 0037. No lane starts a 0037 phase before 0036 closes, even when its own queue is empty. 0037·P2 takes at most two
slots.

**Plan 0038 (added 2026-10-16).** The owner chose the inferred-claims sweep on 2026-10-16 and approved it to run
unattended. It is not a simulation plan, so ADR-0014's block does not apply. Its queue:
- **Phase 0** (architect) accepted on 2026-10-16, with fixes; its review fixed the batch list.
- **Phase 1 static batches** run any time after that review, beside 0036 and 0037.
- **Phase 2 harness batches** never push the harness above **two lanes at once** (OOM, 2026-10-15). Slot 0 stays the
  owner's. 0037·P2 has the slots first:
  - while it holds two, no 0038 batch runs;
  - while it holds one, one 0038 batch may run on one slot;
  - before 0037·P2 starts and after it ends, 0038 may use two.
- **Phase 3** (spec-writer) follows 0036·P2.
