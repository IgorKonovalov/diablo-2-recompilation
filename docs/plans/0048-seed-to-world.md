# 0048 — Seed to world: the core specs composed end to end, with the last in-chain oracles retired

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0015-emulated-reproduction

## TL;DR

**Question:** given only a game seed, the difficulty, the game type and the order in which the player's presence
activates rooms, can the reviewed specs, composed, predict everything the server builds: each level's layout, rooms,
presets, warps and waypoints, objects, the monster population with its packs, minions and special monsters and their
creation stats; and, given a dying unit's seed at death, every item it drops down to its last property? The core three
areas are each reviewed, but every reproduction so far checked **one** subsystem with its neighbours as ADR-0004
boundary oracles. A reimplementer composes them. When this plan is done:
- `docs/findings/chain/0001-oracles.md` lists every boundary oracle still named in the core and enabler specs, with
  the model that retires it or the reason it stays an input;
- the in-chain oracles that a model can replace are modelled (`ITEMS_RollStaffMods`, the preset-and-object window's
  monster seeds, the unit-seed variant steps, the object marks into the collision grid, and whatever the inventory
  adds);
- `tools/chain.py` composes the existing models (`tools/drlg.py`, `tools/objects.py`, `tools/monspawn.py`,
  `tools/tc.py`, `tools/items_chain.py` and their neighbours) and checks a run with **no oracle inside the chain**;
- `docs/specs/chain/README.md` states the composition: the call order from the game seed to a populated level and a
  drop, the inputs a reimplementation must supply, and each subsystem's entry contract, with the run behind it.

## Context

- **Why now.** Every core, enabler and creation-path row of the [research map](../specs/README.md) is reviewed. What
  the map cannot show is whether the pieces fit: an entry seed asserted at each subsystem's boundary is not the same as
  the composition reproducing from the game seed. The specs' *Inputs and oracles* tables (items/affixes,
  items/uniques-sets, monsters/spawn, drlg/collision, objects, items/tc, monsters/special) still name, for example:
  `ITEMS_RollStaffMods` (a seed oracle in [items/affixes](../specs/items/affixes.md), "modelled later"); the rare and
  magic builders as oracles inside [items/uniques-sets](../specs/items/uniques-sets.md) (modelled by items/affixes,
  but not chained there); inside the presets-and-objects window, the preset monsters and the monster-spawning object
  `InitFn`s as seed oracles; the grid snapshot at pass entry, whose object marks are logged values; the unit seed
  after `SUnitCreate` (2 steps on 914 of 916 creations, 6 and 15 on a class appended to the region)
  ([monsters/spawn § Inputs and oracles](../specs/monsters/spawn.md)).
- **Research map:** a new row `chain` (seed to world) at the end of the **Core** band, added when the plan starts;
  it depends on every core row. Wiki owner: Phase 4.
- **What stays an input, by design** (Phase 0 confirms each): the player's actions (where it walks, so which rooms
  activate in which order and on which frame); a dying unit's seed at death, since combat draws on it (simulation,
  ADR-0014); quest state (plan 0042's records) where a level reads it; the client's settings that the server reads.
  Added at the Phase 0 review (2026-10-20): the game seed at each drop (an item's seed is drawn from it, and every
  server unit created by simulation steps it), of class simulation like the dying unit's seed; and the killer's magic
  find (with a summon's owner's), of a new class, the player's character. Both are logged inputs of Phase 2.
- **No new reading is planned** beyond the oracles the inventory names; each retired oracle is modelled from code the
  specs already cite, emulated (ADR-0015) where its read set is declarable.

## Phases

### Phase 0 — The oracle inventory
- **Owner skill:** reverser (static, no Ghidra needed for most of it)
- **What:** read the *Inputs and oracles* section and every `ORACLE` mark of the core and enabler specs and their
  findings, and list each boundary oracle once.
- **Outputs:** `docs/findings/chain/0001-oracles.md`: per oracle, the spec and section, its kind (seed, value,
  result), whether a reviewed model already replaces it in a chained check, the model that would, or the reason it
  stays an input (one of the input classes in *Context*, or a simulation phase); the composition order as a first
  diagram.
- **Done when:** every `oracle` mention in `docs/specs/{items,monsters,drlg,objects,rng,data}/` is either in the list
  or a historical sentence (the list says which), with a kept `grep` command that recounts them; the architect's
  review rules which oracles Phase 1 retires.

### Phase 1 — Retire the in-chain oracles
- **Owner skill:** reverser
- **What:** model each oracle the Phase 0 review assigned, and write `tools/chain.py`.
- **Outputs:** the models in their subsystem tools (for example `ITEMS_RollStaffMods` in the affixes model), emulation
  cases where used, sections in each owning finding, `tools/chain.py` (`gen` from a seed, `check` against logs),
  `tools/gdb/chain.gdb` (the existing loggers' entry and exit lines only, with the seed asserts at each boundary).
- **Done when:** each assigned oracle is modelled `[I]` or better with addresses; `tools/chain.py check` passes on the
  kept logs of the subsystem runs where they hold what the composition needs (named in the finding), with the formerly
  oracled callees predicted; each one not modelled is named with the reason.

### Phase 2 — The end-to-end run
- **Owner skill:** reverser (agent-driven; **one slot**, a second only when no other harness lane runs)
- **What:** fresh games from known `-seed` values, with the composition's boundary loggers, walking each act's levels.
- **Done when:** `run:YYYY-MM-DD-chain` reproduces with **0 mismatches**, the only inputs being those Phase 0 kept,
  over at least: 40 levels with every generator kind (preset, maze, outdoor) and every act, in all three difficulties
  and both game types, at least one level of each of the game type's acts in each difficulty; 2 000 room populations end to end from the game
  seed (no seed oracle in the window); 300 objects' creations; 100 special monsters with their mods and creation
  stats; 500 drops predicted from the dying unit's logged seed through TC, quality, affix, unique or set and property
  rolls with **no** builder oracle; the record lists each input and each remaining oracle with its count.

### Phase 3 — Spec: seed to world
- **Owner skill:** spec-writer
- **What:** write `docs/specs/chain/README.md`; update each core spec's *Inputs and oracles* table where an oracle is
  retired (a link to the model, not a restatement).
- **Done when:** the spec follows the template; it has the composition as a sequence diagram from the game seed to a
  populated level and a drop, the list of inputs a reimplementation supplies, each subsystem's entry contract (seed,
  arguments, state read) by link, and worked examples from the run; every statement is tagged; the architect's review
  passes.

### Phase 4 — Wiki page: how a game is built
- **Owner skill:** spec-writer
- **What:** `docs/wiki/seed-to-world.md` (ADR-0012), linking the levels, monsters and items pages in build order.
- **Done when:** `based_on` current; the architect's review passes.

## Resources and limits

- **Static:** Phase 0 needs no Ghidra; Phase 1 holds **one** Ghidra lane (`-Xmx3G`) when it reads or emulates.
- **Harness:** Phase 2 takes **one slot from 1–2** (two only when no other harness lane runs); at most two games at
  once across all plans; ~~the end-to-end logger sets only entry and exit breakpoints~~ (amended at the Phase 1 review:
  `tools/gdb/chain.gdb` keeps the full loggers, because the checkers consume the lines inside each boundary; the smoke
  session and the caps of the Phase 1 review's ruling 5 bound its volume); no per-frame path, ADR-0014 § Log volume
  applies by analogy.
- **Replays:** `tools/chain.py check` over many kept logs runs under `MemoryMax=4G`.
- **Rotation:** past about 4 h the lane checkpoints and a fresh lane resumes.
- **Estimate** (an estimate): Phase 0 one short lane; Phase 1 one or two lane runs; Phase 2 one or two lane runs.

## Open questions

- **Activation order as an input.** A reimplementation that wants the same world for the same seed must activate rooms
  in the same order; whether order changes anything beyond seeds already chained per room is for Phase 0 to state.
- **Vendors and hirelings.** Their builders (`HIRE_BuildStock` among them) are creation paths, not the chain; they are
  listed by Phase 0 and left as they are.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`.
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 done, review requested (reverser, `lane/p48a`, static, no Ghidra, no harness).**
  [chain/0001](../findings/chain/0001-oracles.md) lists **31 boundary oracles** of the core and enabler specs (seed 21,
  seed and result 3, result 2, value 5; first named in items 9, monsters 8, drlg 7, objects 6, data 1), each with its
  status: 11 already replaced in a chained check, 1 modelled behind a switch, 10 Phase 1 candidates, 5 inputs, 4 off the
  chain. Surprises: `ITEMS_RollStaffMods` is already modelled (plan 0038 batch S2b, `--staff model`, still not the
  default), and the object marks into the collision grid were modelled in plan 0027 Phase 2; what stays of the snapshot
  is the player, walk-in, item and corpse marks. Activation order is an input beyond the per-room seeds (game seed,
  object-region seed, near lists). Two input classes not in *Context* are proposed: the game seed at a drop and the
  killer's magic find. Recount: the kept grep (162 lines, 169 matches, 22 files on `ad130d7`) and
  `tools/oracle_ledger.py`, which checks the finding's § 6 ledger line for line (25 structural, 3 "no oracle", 134
  naming an oracle). Proposed retirements for the review to rule: oracles 2, 16, 17 (46), 14, 22, 19, 21, 20, 7, 6, 13
  ([§ 4](../findings/chain/0001-oracles.md#4-proposed-phase-1-retirements-for-the-architects-ruling)). Five spec
  passages that lag the models are listed for Phase 3 (§ 5).
- **2026-10-20 — Phase 0 reviewed (architect): accept with fixes; Phase 1 can start.** `main` merged into `lane/p48a`
  (no conflict); `tools/oracle_ledger.py` after the merge: 162 lines, 22 files, the same hash
  `fc6af974…`, 0 differences (cfix and p49r touched no spec under the six directories), S 25, N 3, 134 naming an
  oracle, only oracle 31 named by no line. Spot checks: anchors of oracles 2, 7, 13, 14, 16, 17, 19, 20, 21, 22 and the
  § 3.1 bullets resolve in `re/symbols.csv`; the rows of 14, 15, 16–21 agree with monsters/spawn, objects and
  drlg/collision *Inputs and oracles*; the kinds, statuses and first-named tallies recount.
  Fix: oracle 14's variant roll is already modelled by `tools/mon_sweep.py pool` (plan 0038 batch S3a, 4568 of 4568
  unit seeds at `MonStatsInit` entry), not only "to model"; § 2 row 14 and § 4 item 3 now say so (omission 1).
  **Phase 1 assignment** (all ten proposed, in this order): (1) oracle 2, `--staff model` the default of
  `tools/items_chain.py`, `tools/affixes.py` and `tools/chain.py`; (2) oracle 14, chain the S3a region-append model
  into `tools/monspawn.py` (moved ahead of 16 and 17, whose monster creations need it); (3) oracles 16 and 17, the
  window's preset monsters and `InitFn` 46 through the monsters chain inside `tools/objects.py`'s window (47–69 stay
  named as unreached; 79 and 582 take their class from quest state, an input); (4) oracle 22, the `Orient89Unit`
  creation; (5) oracle 19's DRLG parts from `tools/drlg.py gen` (the Chaos Sanctuary test stays quest state); (6) oracle
  21, another room's seed as chain state; (7) oracle 20, the grid snapshot composed, with the barrier grid
  (`LOGIC_BarrierGridBuild` 0x0066C870, emulated under ADR-0015 or named not modelled) and the type-11 point from the
  drlg/warps point list in the same step; the player, walk-in, item and corpse marks stay logged inputs, counted;
  (8) oracle 7, the gold piles' items; (9) oracle 6, an object's drop; (10) oracle 13, MonEquip's item creation,
  `[I]` at best, and it may close as "not modelled, unreached" if no stock row reaches it (archivist entry
  [MonEquip table doc](../backlog/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md), not blocking).
  Not assigned: 8, 12, 18, 24, 25 (inputs) and 9, 10, 11, 23 (off the chain), as proposed.
  **Rulings.** (a) The S and N line classes of chain/0001 § 6 meet the Phase 0 *Done when*: a structural use or a "no
  oracle" statement names no oracle, so "in the list or a historical sentence" applies to the 134 naming lines; no plan
  amendment. (b) The two input classes of § 3.3 are accepted and added to *Context* above. (c) Oracle 31 stays listed
  with no line of its own: its paragraph is historical (plan 0017 replaced it), and `oracle_ledger.py` reporting
  `[31]` is the expected output. (d) Activation order: accepted as an input beyond the per-room seeds, `[I]` as stated
  (§ 3.2); the open question is answered. (e) The stale *grid snapshot* row of monsters/spawn (object marks "still
  logged") is a wrong statement in a reviewed spec, routed now to the spec-writer
  ([entry](../backlog/archive/2026-10-20-architect-spec-writer-monsters-spawn-stale-object-marks-row.md)); the other four
  passages of § 5 stay Phase 3's. (f) Research map: the Core row `chain` is added (findings in progress).
- **2026-10-20 — Phase 1 done, review requested (reverser, `lane/p48r`, static, Ghidra copy, no harness).**
  [chain/0002](../findings/chain/0002-retirements.md) records each assigned oracle, in the assigned order, on kept logs
  only (133 item logs, 62 world logs; input lists and every output hashed in `workspace/logs/chain-p1/manifest.txt`,
  `8c219e82…`). `tools/chain.py` is written: `gen` builds the seed tree, the four game-creation draws, the monster
  regions and every level seed from `-seed N` (the rng/seeds worked example reproduced in `tools/test_chain.py`);
  `check` runs the item chain, `tools/tc.py` (quality modelled) and the world chain (`tools/monspawn.py` with
  `tools/objects.py`, `tools/drlg.py`, `tools/monstats.py`) per log and lists every oracle still taken. **Over the 195
  logs: 0 sub-checks failed**; 8 519 of 8 553 unit seeds and 1 253 of 1 265 objects windows predicted with no oracle
  inside. Retired: **2** (staff mods the default), **14** (unit seed after `SUnitCreate`: FindAdd on tracked regions
  plus `MonStatsInit`'s draws), **16** (the presets window's monsters: the class case `sub_0054E490_PresetClassSpawn`,
  the MonPlace fixed rows with `LevelClassVariant`, tile units), **17** (InitFn 46, read in the disassembly; its
  direction draw is never stored), **22** (the `Orient89Unit` units come as presets; the objects under catapults 432 and
  433 modelled), **21** (another room's seed as chain state), **7** (gold items' seeds and marks; 69 of 71 spots),
  **6** (an object's drop: the unit seed is tc.py's `TCEND`, the game seed predicted from the items). **13** modelled
  `[I]`, unreached; `tools/monstats.py` read `oninit` at the wrong offset, so the old oracle never fired (corrected).
  **19** read (the gate's four DRLG tests), its logged inputs checked against the reading on 1 265 gates, still
  logged; **20** named, not modelled (R3: composed grid = snapshot in 3 871 of 3 998 pass rooms; the barrier grid read
  and probed, 258 of 307; the type-11 point's rule not carried). Corrections to chain/0001 § 2: InitFns 54 and 62 were
  reached (7 and 4 calls); oracle 22's creation is a preset unit's. Surprises: the model needed no change for the odd
  unit-seed step counts (6 to 17): all are FindAdd appends or MonProp; `L` does not change the HP draw count. 8 symbols
  added (`sub_0054E490_PresetClassSpawn`, `sub_0054E3A0_PresetRetryAllowed`, the gate's six DRLG tests);
  `OBJINIT_CityDamnedSpawns` raised to `C`. `tools/gdb/chain.gdb` written (not run). Review request:
  [entry](../backlog/archive/2026-10-20-reverser-architect-review-plan-0048-phase-1-in-chain-oracles.md).
- **2026-10-20 — Phase 1 review (architect, on `lane/p48r` after merging `main`): accept with fixes (5).** Re-run on
  the merged tree under `MemoryMax=4G`: `tools/chain.py check` over the 195 logs, 0 sub-checks failed; every summary
  line equals `final-check.txt` but one: **1 250** of 1 265 objects windows oracle-free (was 1 253), because `main`'s
  objects/0001 § S4b row 25 made the nine monster-creating `InitFn`s seed oracles (`InitFn` 18: 3 windows here).
  `tools/test_chain.py` 11 tests OK; `sha256sum -c` clean on `manifest.txt` (`8c219e82…`, unchanged) and both input
  lists (195 logs); the lane head's tools equal `tools-final.sha256` (4 differ on the merged tree, as expected).
  Controls re-run, each failing as claimed: `i46-stored` 10, `state-stale` 2, `lcv-off` 25, `overlay-off` 19; the kept
  `findadd-none` output holds the 416 monspawn mismatches stated. Anchors checked in the image: `cmp byte [ebx+4], 0` at
  0x005D6BA5, `sub_0066BB20_DrlgRoomPopLevelId`'s `0x800000` / `[+0x58] → +0x1D0`, `sub_0054E490_PresetClassSpawn`'s
  class bound; `re/symbols.csv` has no duplicate address after the merge. Review outputs: `workspace/logs/chain-p1/review-*.txt`,
  `review-manifest.txt` (`f0dd87f8…`); chain/0002 § 14.
  **Fixes** (written into chain/0002 and monsters/0004): (1) oracle 14 headed "retired in part", with the final
  8 519 of 8 553 and the 34-creation remainder named; (2) oracle 7 headed "retired in part" (the spot `[I]`, 2 of 71
  from the log); (3) the Answer's counts of 14, 16 and 17 were the intermediate steps' — the final ones added (311
  class-case presets; 1 253 then 1 250 windows); (4) § 11's `[C]` (`oninit` at `+0x04`) had only the code reading:
  its second source is now the full-table check of `monequip.bin` against `monequip.txt` (45 of 45 rows,
  `+0x04` = `oninit`, `+0x02` = `level`), run at the review; (5) § 1's `[I]` on what `gen` stops at had no anchor
  (gate W1): anchored.
  **Rulings.** (1) **The equality chain is acceptable for `[C]`.** Where `tools/objects.py` takes a seed at
  `OPUX`/`MTX`/`OCX` and `tools/monspawn.py` or `tools/tc.py` predicts and asserts it at the same line, both run in
  one `check`, a failed assert fails the run, and the window counts as oracle-free only when every taken line was
  asserted; the composed value therefore equals the model's, and the `lcv-off` and `i46-stored` controls show the
  asserts are live. No model has to carry the value for Phase 1 or Phase 2. Phase 3's spec states the single call
  order, not the two checkers; a log-free world build from `gen` would need the hand-off and is out of this plan.
  (2) **Oracles 13, 19 and 20 stay Phase 2 inputs; no follow-up phase before Phase 2.** Phase 2 must: count each in
  the run record by name; for 19, assert every `OG` line's DRLG inputs against chain/0002 § 7's reading
  (`gate_inputs`) and count `LevelRoomCount` reads; for 20, keep `SN`, `LG0` and `NWW` as inputs, report the R3
  residue per pass room by bit, and for every object-bit cell (`0x400`, `0x404`) that no window mark explains (14 on
  the kept logs) name the creation line nearest before the snapshot, or list the cell as unexplained (a named item,
  not blocking); for 13, include at least one session that creates class 267 or 234 — a reproduced creation raises the
  MonEquip model to `[C]`, otherwise it stays `[I]`, named unreached. The 34 unit seeds taken (classes appended by
  creations outside the model) are a counted remainder: the record gives, per class, the creation that appended it.
  The windows holding `InitFn` 18, 54 or 62, and the 2 gold spots, are counted remaining oracles and do not count
  toward the 2 000 oracle-free room populations. (3) **`chain.gdb`'s volume**: the full loggers are accepted (the
  *Resources* line is amended above). Phase 2's first session is a smoke session (one act, one difficulty, at most
  20 minutes of game time) that records lines per tag, MB per game minute and wall time per game minute before any
  counted session; the run record then sets a cap per session (raw log at most 500 MB; the kept world logs are at
  most 13 MB each), `MONSPAWN_WATCH` empty, and a session that reaches the cap stops logging and is kept as a
  development log. (4) **The `oninit` fix changes no earlier result**: no `SI0` log (11 mon-stats, 9 H4b, 6
  forced-berserk) creates class 234 or 267; `tools/monstats.py check` re-run on the 9 H4b logs (35 461 checks) and the
  6 forced-berserk logs (30 863), 0 mismatches, no MonEquip oracle hit (the H4b session 5b DRLG mismatches are the
  second-game ones recorded at H4b, the same with `main`'s tools). (5) **Stale spec passages, routed to Phase 3**
  (its *What* already updates each core spec's *Inputs and oracles* table; none states a wrong behaviour, they name
  as oracles what is now modelled): items/affixes § I, its table row and the `ORACLE` markers of D4, E7, G4, H2 and
  the D4/E7 example rows; items/properties *Inputs* (`ITEMS_RollStaffMods`) and § 875's sentence; player/creation's
  staff-mods row, its § 350 sentence and Example 1; monsters/stats' MonEquip row, B12 and its three diagrams (and the
  `oninit` byte at `+0x04`); monsters/spawn's rows "seed of another room" and "unit seed after `SUnitCreate`";
  monsters/special's unit-seed row; drlg/collision's "seed of another room" row and the gold-drop sentence of § F;
  objects/README's rows for the presets window's monsters, the monster `InitFn`s (46), `TC_ResolveDrops` and the gold
  drop, and `InitFn` 46's row; drlg/room-tiles' `Orient89Unit` step 11 and its § 746 sentence (the creation is a
  preset unit's, `[I]`). No entry to the spec-writer now.
  **Phase 1 is done; Phase 2 may start in one slot** when plan 0044 releases one (the queue's order holds). Ledger
  rows added (usage TBD). Review request [closed](../backlog/archive/2026-10-20-reverser-architect-review-plan-0048-phase-1-in-chain-oracles.md).
- **2026-10-20 — Phase 2 paused at the owner's request: checkpoint and resume note (reverser, `lane/p48h`, harness
  slot 1).** Not a phase close; no review requested yet.
  **Smoke session** (`p2-s1-4801-smoke`, UniqNova, Normal, Act I, `tools/gdb/chain.gdb`): 36 406 lines, 7.8 MB,
  3.45 game minutes (game frames of the `PLR` lines, 25 per second) in 8.4 wall minutes from game entry: **2.26 MB per
  game minute, 2.4 wall minutes per game minute**; the largest tags `TINIT` 1.66 MB, `CB` 0.98 MB, `SN` 0.72 MB,
  `LSUB` 0.47 MB (`chain_sessions.py volume`). Cap per session set at 500 MB raw (a 15-minute session writes about
  15 MB, so no session is near it), `MONSPAWN_WATCH` empty, wall limit 15 minutes.
  **Sessions kept** (`workspace/logs/chain-p2/`, `manifest-ckpt1.txt` `bf6a3a70…`, tools in `out/tools-ckpt1.sha256`,
  paths from the repository root): smoke, xn2 (Halls of the Dead 2), xn3 (Spider Forest), xn4 (City of the Damned),
  xn5 (Crystalline Passage), xm1 (Catacombs 2, Nightmare), raven-xn (Cold Plains to the Burial Grounds). Development
  logs: `dev-p2-s1-4803-xn3-aborted` (the driver restarted), `dev-p2-s1-4812-xm2-paused` (cut by this pause). No log
  holds `internal-error:` (gdb's i387 assertion).
  **`tools/chain.py check` on the six counted logs** (`out/ckpt1-check.txt`): 0 sub-checks failed; 300 room populations
  end to end with no oracle; 36 (level, difficulty, game type) built (DrlgType 1: 14, 2: 8, 3: 14; Normal expansion acts
  I–V, Nightmare expansion acts I and IV); 1 994 objects created (421 populate, 1 573 preset); 242 monster drops with an
  item, 336 item creations reproduced from both line sets; specials 6 champion packs, 10 unique packs, 13 mod rolls.
  **raven-xn** fails on one logger error (`LOGERR collision MemoryError`, a corpse re-dump `DCR` on a freed room, fixed
  in `tools/gdb/collision.py` as `DCRF`); it is a development log for the counts. It holds the first **oracle 13**
  case: Blood Raven (267), `MonEquipInit` with one `oninit` row, the unit seed after it predicted at `SIX` by the model
  (one location draw; `--cf monequip-off` fails it), the item it creates reproduced by the item chain.
  **Tool fixes on the way** (commits `cc613e4`..`7778dcb`): the `RC` tag of `drlg-gen.py` and `affixes.py` collide in
  one log (each reader skips the other's); objects resync stops at `OPU0` (a cascade of 16 on xn2); a locked chest
  reaching its OperateFn with only the lock bit cleared and no key is a counted oracle (xn2, the writer not read);
  Izual's creation increments the special count (taken, counted); a presets-window monster or request whose predicates
  took a value no longer confirms its window — on the Phase 1 logs **1 241** objects windows oracle-free (was 1 250),
  512 populations (`out/p1world-check.txt`). New logged inputs: `TCR gseed` (the game seed at each drop), `PLR gf`;
  the killer's and owner's magic find are the existing `QKMF`/`QOMF`/`QMF` lines.
  **Next (resume):** `python3 -I tools/chain_sessions.py run --slot 1 --tag p48h --saves workspace/runtime/p48h-chars
  --run p2 xm2 xm3 xm4 xm5 xh1 xh2 xh3 xh4 xh5 raven-xn2 cn1 cn2 cn3 cn4 cm1 cm2 cm3 cm4 ch1 ch2 ch3 ch4` (saves built
  from `uniqnova.json` / `uniqclassic.json`, see the session driver); then `chain.py check --o20` over all counted logs,
  the run record `run:2026-10-20-chain` (no `experiments.md` entry written yet), and the review request. Maze waypoints
  finish their level in 5–8 minutes; about 70 oracle-free populations per 15-minute outdoor session, so 2 000 needs
  roughly 25 more sessions.
- **2026-10-21 — Phase 2 run 1 recorded; review requested (reverser, `lane/p48h`, harness slot 1).** Not a phase
  close: the bar is not met. Resumed after the 2026-10-20 20:12 out-of-memory kill (no resume note for it): of the
  note's queue, xm2, xh1, xh2, cn1, cn2, cm1, cm3 and ch1 had finished cleanly; xm5 was cut and is kept as
  `dev-p2-s1-4815-xm5-oom`; the other 14 (raven-xn2, xm3, xm4, xm5, xh3, xh4, xh5, cn3, cn4, cm2, cm4, ch2, ch3, ch4)
  ran in two batches. xh4 sat through a machine suspend (23:17 to 06:19) and checks clean. No log holds
  `internal-error:`. Record [run:2026-10-20-chain](../findings/chain/experiments.md#run2026-10-20-chain), finding
  [chain/0003](../findings/chain/0003-end-to-end-run.md); 28 counted logs, manifest `manifest-final.txt`
  (`e47bb1b1…`).
  **Result** (`tools/chain.py check --o20` over the 28, under `MemoryMax=4G`): 26 logs pass; **2 mismatches** (cn4,
  cm4: one `COLL_WHTest` of the objects model each, a live monster's bits the log does not place; candidate a
  `MonSpawnTry` monster that walked, `[I]`). Met: 156 levels built, every DrlgType, every act of each game type in each
  difficulty; 9 057 objects; 44 champion and 110 unique packs, 147 mods rolls; 849 monster drops with an item (951
  items), 2 514 TC calls and 1 286 item creations, 0 failed. **Short**: 1 385 of 2 000 oracle-free populations. Ruling
  2's items: oracle 13 reached (classes 267 and 234, `--cf monequip-off` fails both; MonEquip raised to `[C]` in
  chain/0002 § 11), oracle 19 counted and its gate inputs asserted, oracle 20's residue by bit with 0 unexplained
  object-bit cells, oracle 14's remainder 0 of 8 588. Checker scope change (`dfe3e5e`): a chest's interact byte set or
  cleared before its operate is taken and counted (3 cases), Phase 1 world summary unchanged.
  **Next:** the architect rules on the two mismatches and the shortfall. Proposed: a `chain.gdb` line for a moving
  monster's marks between windows (or the cells under each objects-model `COLL_WHTest`), cn4 and cm4 re-run on their
  seeds, and about 13 more outdoor sessions on slot 1 for the populations.
