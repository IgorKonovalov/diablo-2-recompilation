# 0048 — Seed to world: the core specs composed end to end, with the last in-chain oracles retired

> **Status:** done (closed 2026-10-21; approved 2026-10-20 by the owner)
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

- **Why now.** Every core, enabler and creation-path row of the [research map](../../specs/README.md) is reviewed. What
  the map cannot show is whether the pieces fit: an entry seed asserted at each subsystem's boundary is not the same as
  the composition reproducing from the game seed. The specs' *Inputs and oracles* tables (items/affixes,
  items/uniques-sets, monsters/spawn, drlg/collision, objects, items/tc, monsters/special) still name, for example:
  `ITEMS_RollStaffMods` (a seed oracle in [items/affixes](../../specs/items/affixes.md), "modelled later"); the rare and
  magic builders as oracles inside [items/uniques-sets](../../specs/items/uniques-sets.md) (modelled by items/affixes,
  but not chained there); inside the presets-and-objects window, the preset monsters and the monster-spawning object
  `InitFn`s as seed oracles; the grid snapshot at pass entry, whose object marks are logged values; the unit seed
  after `SUnitCreate` (2 steps on 914 of 916 creations, 6 and 15 on a class appended to the region)
  ([monsters/spawn § Inputs and oracles](../../specs/monsters/spawn.md)).
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
  order of the [plans index](../README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 0 done, review requested (reverser, `lane/p48a`, static, no Ghidra, no harness).**
  [chain/0001](../../findings/chain/0001-oracles.md) lists **31 boundary oracles** of the core and enabler specs (seed 21,
  seed and result 3, result 2, value 5; first named in items 9, monsters 8, drlg 7, objects 6, data 1), each with its
  status: 11 already replaced in a chained check, 1 modelled behind a switch, 10 Phase 1 candidates, 5 inputs, 4 off the
  chain. Surprises: `ITEMS_RollStaffMods` is already modelled (plan 0038 batch S2b, `--staff model`, still not the
  default), and the object marks into the collision grid were modelled in plan 0027 Phase 2; what stays of the snapshot
  is the player, walk-in, item and corpse marks. Activation order is an input beyond the per-room seeds (game seed,
  object-region seed, near lists). Two input classes not in *Context* are proposed: the game seed at a drop and the
  killer's magic find. Recount: the kept grep (162 lines, 169 matches, 22 files on `ad130d7`) and
  `tools/oracle_ledger.py`, which checks the finding's § 6 ledger line for line (25 structural, 3 "no oracle", 134
  naming an oracle). Proposed retirements for the review to rule: oracles 2, 16, 17 (46), 14, 22, 19, 21, 20, 7, 6, 13
  ([§ 4](../../findings/chain/0001-oracles.md#4-proposed-phase-1-retirements-for-the-architects-ruling)). Five spec
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
  [MonEquip table doc](../../backlog/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md), not blocking).
  Not assigned: 8, 12, 18, 24, 25 (inputs) and 9, 10, 11, 23 (off the chain), as proposed.
  **Rulings.** (a) The S and N line classes of chain/0001 § 6 meet the Phase 0 *Done when*: a structural use or a "no
  oracle" statement names no oracle, so "in the list or a historical sentence" applies to the 134 naming lines; no plan
  amendment. (b) The two input classes of § 3.3 are accepted and added to *Context* above. (c) Oracle 31 stays listed
  with no line of its own: its paragraph is historical (plan 0017 replaced it), and `oracle_ledger.py` reporting
  `[31]` is the expected output. (d) Activation order: accepted as an input beyond the per-room seeds, `[I]` as stated
  (§ 3.2); the open question is answered. (e) The stale *grid snapshot* row of monsters/spawn (object marks "still
  logged") is a wrong statement in a reviewed spec, routed now to the spec-writer
  ([entry](../../backlog/archive/2026-10-20-architect-spec-writer-monsters-spawn-stale-object-marks-row.md)); the other four
  passages of § 5 stay Phase 3's. (f) Research map: the Core row `chain` is added (findings in progress).
- **2026-10-20 — Phase 1 done, review requested (reverser, `lane/p48r`, static, Ghidra copy, no harness).**
  [chain/0002](../../findings/chain/0002-retirements.md) records each assigned oracle, in the assigned order, on kept logs
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
  [entry](../../backlog/archive/2026-10-20-reverser-architect-review-plan-0048-phase-1-in-chain-oracles.md).
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
  rows added (usage TBD). Review request [closed](../../backlog/archive/2026-10-20-reverser-architect-review-plan-0048-phase-1-in-chain-oracles.md).
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
  `internal-error:`. Record [run:2026-10-20-chain](../../findings/chain/experiments.md#run2026-10-20-chain), finding
  [chain/0003](../../findings/chain/0003-end-to-end-run.md); 28 counted logs, manifest `manifest-final.txt`
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
- **2026-10-21 — Phase 2 run 1 reviewed (architect, on `lane/p48h` after merging `main`): accept with fixes (4);
  Phase 2 not done, run 2 on slot 1.** Re-run on the merged tree under `MemoryMax=4G`: `sha256sum -c
  manifest-final.txt` clean (`e47bb1b1…`, 127 lines); `tools/chain.py check --o20` over the 28 logs equals
  `out/final-check.txt` byte for byte (paths aside, `79c3a7a7…`) and `final-o20.json` is identical; the same check
  without cn4 and cm4: 26 logs, 0 sub-checks failed. Anchors read in the image: `0x005504B3` and `0x00550B89` are
  `call 0x64D800` (`COLL_WHTest`, mask `push 0x3F11`, w and h `+ 6`), `0x005D6BA5` `cmp byte [ebx+4], 0`, `0x00574235`
  `call 0x5D6B60` (`MonEquipInit` from `MonStatsInit`); every cited address is in `re/symbols.csv`. Oracle 19, 20 and
  14 counts recounted from the re-run, equal to the record. Review outputs `workspace/logs/chain-p2/out/review-*`,
  `review-manifest.txt` (`5ba2d005…`).
  **Fixes** (written into chain/0003, chain/0002 and the run record): (1) **misread**: chain/0003 § 2 said neither
  candidate's footprint overlaps the tested rectangle, reading it as anchored at (x, y); `COLL_WHTest` centres it
  (`tools/collision.py wh_test`), so cn4's unit 522 stands on the rectangle's top-left cell and cm4's two class-189
  units' footprints overlap its left columns. The candidates are not fresh monsters that walked: each is a monster
  the population pass made in mode 1 and a `MonSpawnTry` request re-made in mode 3 after its room's release and return
  (same unit id, same request seed), and the re-creations have no `CM` line and no modelled mark; the game's bits are
  exactly those of the monsters on their re-creation cells (`[I]`). § 2, the Answer, Open question 1 and the record
  corrected. (2) **overclaim**: the 1 385 populations and the coverage counts included cn4's (117) and cm4's (46)
  populations and counts, logs that fail; on the 26 passing logs: **1 222** populations, 148 levels (every kind, every
  act of each game type in each difficulty), 8 231 objects, 41 champion and 108 unique packs, 142 mods rolls, 745
  drops with an item (843 items); the shortfall is 778 (about 16 sessions, not 13). (3) **overclaim**: oracle 13's
  raise covered model branches no case reached; the stock table's two `oninit` rows (`monequip.bin` rows 0 and 1) are
  level 0 with one location each, so the `[C]` is **in part** (one row, n = 1, the masked step, one item) and the level
  skip, a second row, n of 2 or 3 (`RangeB`) and an occupied location stay `[I]`, unreachable with the stock table
  (chain/0002 § 11 and its Answer). (4) **omission**: xh4's 1 962 lines after its last frame-stamped `PLR` line are
  of unknown time (before the suspend or after the resume); the record now says so and scopes the session.
  **Rulings.** (1) **The two mismatches: neither proposed route.** Not the moving monster's marks (the cause is the
  re-creation, fix 1), and not the test as a simulation input: taking a `COLL_WHTest` result would have hidden exactly
  this model gap, and stays refused. Route: find the mark call a mode-3 re-creation takes (the mode-1 creation's `PM`
  lines return to `0x006494D5`; the re-creations log none), add it to `tools/gdb/chain.gdb`, model the marks in
  the objects grid as for in-pass creations (`creation_mark`), and re-check cn4 and cm4 **on their kept logs**: if both
  pass they count, populations included, with the marks there checked only through the later tests (say so); the new
  logs compare the marks line for line. Count the re-creations in every log. A test that only a moved monster
  explains would then be logged as a simulation input (that unit's marks), not taken as the test's result.
  (2) **More sessions: approved**, on slot 1, new seeds, weighted to outdoor waypoints, until the passing logs hold
  2 000 populations (778 more, 615 if cn4 and cm4 pass); recount after each batch from the kept check output.
  (3) **The chest interact byte (`dfe3e5e`): legitimate as a counted remaining oracle, not a hidden gap of the bar.**
  The creation's byte is still asserted at its creation line; the taken byte is the operate's, after the player's
  interaction, and drives only `OperateFn` 4's locked test and that chest's drop (object-source drops, outside the
  bar's 500 monster drops and its 300 creations); the branch takes only the two forms seen with mode and sparkle
  equal, so any other change still fails. It is a gap of the operate path, named (chain/0003 Open question 2) and
  counted by kind; run 2 reads the writer if a static pass finds it cheaply, else it stays for Phase 3's *Open
  questions*. (4) **xh4 is admissible as a reproduction.** A suspend stops the game, wine, gdb and its logger together,
  so no line is lost or reordered; no model reads wall time (the game frame and every seed are logged or predicted),
  and every line the check consumes is reproduced, including whatever ran after the resume. It is not admissible for
  timing (MB or wall minutes per game minute), and a session crossing a suspend is named in its record, as here.
  (5) **Oracle 13**: reached, raised in part (fix 3); the control is live and the unit seed after the draw is a 64-bit
  value, so neither case matches by chance. (6) **Oracles 19, 20, 14**: counted as ruling 2 of the Phase 1 review asked;
  accepted. **Done-when**: not met — 2 mismatches, 1 222 of 2 000 populations; everything else met on the 26 passing
  logs. **Next: run 2 on slot 1** with (a) the re-creation marks logged and modelled, (b) cn4 and cm4 re-checked on
  their logs, (c) about 16 new sessions, (d) one `chain.py check` over every counted log (run 1's 28 and run 2's) with
  run 2's tools, 0 sub-checks failed, and the Phase 1 world logs re-checked for regressions, (e) the record's counts
  from passing logs only, then the review request. Review request
  [closed](../../backlog/archive/2026-10-21-reverser-architect-review-plan-0048-phase-2-run-1-end.md); ledger row added.
- **2026-10-21 — Phase 2 run 2 paused at the owner's request: checkpoint and resume note (reverser, `lane/p48r2`,
  harness slot 1).** Not a phase close; no review requested yet; no run record written yet.
  **The mark call a re-creation takes** (static reading, objdump of the pinned image, `[I]` until the record): the
  mode-3 re-creations are the revisit restore's. A room whose driver flag bit 0 is set gets no RW window:
  `sub_0052D0F0_RoomUpdateOne` (`0x0052D142`) and `sub_0052D160_NewRoomsUpdate` (`0x0052D205`) call
  `sub_00542B40_RoomInactiveUnitsRestore` directly, whose monsters go through `sub_005B30E0_SpawnWithId` to
  `sub_005B2A00_MonSpawnTry` with request flags `0x62` / `0x6A` / `0xE2`; flag `0x20` makes the `SUnitCreate` create
  flags 3 (`0x005B2E10`; the `MU0` "mode" field is these create flags), bit 0 runs `sub_00554850_SUnitPathCreate`,
  and its monster branch marks through the **same** `UNIT_CollMark` calls as a pass creation (`PATH_DynamicCreate` at
  `0x00649E9A`, `sub_005A7C20_MonSetMode` at `0x005A7CB1`, both into `COLL_PatternMark` returning to `0x006494D5`), then
  MonSpawnTry's alignment refresh (`0x005B2EAB`). No `CM` line was logged only because `tools/gdb/collision.py` logs
  marks inside an RW1..PX window, and the restore runs outside one. A record restored dead (`a10` = 12) has no
  MonSetMode mark (`0x005541B0` is the dead test at `0x005A7CA7`); for MonStats2 `deadCol` 0 the corpse call
  (`sub_00649F70_UnitCorpseColl`, `RectOrWH` 3×3 `0x8000` at `0x00649FD8`) and SUnitCreate's corpse re-mark
  (`0x0055546F`..`0x005554A3`) follow; `deadCol` 1 keeps the one live mark. The dead sequence was first predicted
  wrong (from the code alone) and corrected from run 2's first log (`out/dev-r2-xn1-check-deadlist0.txt`: 18 dead
  re-creations mismatched, every alive one matched).
  **Tools** (commit `53ffb95`, with the dead-sequence fix): `tools/gdb/collision.py` logs
  `CMR0 {th, room}` .. `CM` .. `CMRX` around the two restore calls; `tools/objects.py` `recreation` predicts each
  re-creation's marks (MonStats / MonStats2 rows, `MonTables`), compares them with the logged lines inside a scope
  and applies them to the objects grid (on run 1's logs, which have no scope, applied unchecked: "checked only
  through the later tests"); `tools/chain.py --cf recreation-off` (control); `tools/chain_sessions.py` `PLAN2` (16 run-2
  rows, seeds 4861..4912, mostly outdoor waypoints).
  **(b) cn4 and cm4 pass on their kept logs** (`out/r2ckpt1-check.txt`): 0 sub-checks failed, cn4 118 and cm4 47
  oracle-free populations (the record's 117 and 46 plus each failing window, now predicted); `--cf recreation-off`
  restores exactly run 1's two mismatches (`out/dev-r2-cf-recreation-off-*.txt`). Run 1's 28 logs with the
  pre-fix tools: 0 sub-checks failed, 1 387 populations, 5 348 re-creations, every other count equal to
  `final-check.txt` (`out/dev-r2-r1logs-check.txt`); the Phase 1 world logs: 0 failed, summary equal but the new
  re-creation lines (`out/dev-r2-p1world-check.txt`). Both are development outputs: they must be re-run with the
  final tools.
  **Sessions** (`workspace/logs/chain-p2/`, `manifest-r2-ckpt1.txt` `0c7beb21…`, paths relative to that directory;
  tools in `out/tools-r2-ckpt1.sha256`): `p2r2-s1-4861-r2-xn1` (City of the Damned, 94 populations, 288
  re-creations compared: 254 alive, 32 dead `deadCol` 0, 2 `deadCol` 1, 0 mismatches) and `p2r2-s1-4862-r2-xn2`
  (Cold Plains, 73), both 15 minutes, no `internal-error:`. `p2r2-s1-4871-r2-xm1.pilot.txt` and its empty shots
  directory are a stub: the driver was stopped for the pause before r2-xm1's game launched (no log). Passing
  populations now **1 554** (26 run-1 logs 1 222, cn4 and cm4 165, run 2 167): **446 to go**.
  Chest interact-byte writer (ruling 3): not read (no cheap static anchor); stays in chain/0003's Open questions.
  Slot 1 stopped, the `p48r2` aside restored (the saves directory is empty, as before the run).
  **Next (resume):** on `lane/p48r2`, slot 1: `python3 -I tools/saves.py --slot 1 aside p48r2`, then
  `python3 -I tools/chain_sessions.py run --slot 1 --tag p48r2 --saves workspace/runtime/p48h-chars --run p2r2
  r2-xm1 r2-xh1 r2-cn1 r2-cm1 r2-ch1 r2-xn3 r2-xm2` (queued, in this order; then r2-xn4 r2-xm3 r2-xh2 r2-xh3 r2-cn2
  r2-cm2 r2-ch2 if the populations are still short), recounting from a kept check after each batch, until the
  passing logs hold 2 000. Then: (d) one `chain.py check --o20` over run 1's 28 logs and every run-2 log with the
  final tools, under `MemoryMax=4G`, 0 sub-checks failed, and the Phase 1 world logs re-checked
  (`cd workspace/logs/chain-p1 && … check $(awk '{print $2}' inputs-world.sha256)`); the re-creation counts per log;
  the run record (new id, `run:2026-10-21-chain2`), chain/0003 updates (§ 2, the Answer, Open question 1 closed by
  the reading above, the counts from passing logs only), a final manifest, and the review request in
  `docs/backlog/`.
- **2026-10-21 — Phase 2 run 2 recorded; review requested (reverser, `lane/p48r2`, harness slot 1).** Resumed from the
  pause note: the slot-1 aside `p48r2` set, the queued seven sessions run in order (r2-xm1 r2-xh1 r2-cn1 r2-cm1 r2-ch1
  r2-xn3 r2-xm2), each checked alone as it finished; the passing logs held 2 000 after them, so the optional seven
  were not run. No log holds `internal-error:`; r2-cn1's game process ended on its own at game frame 10 920 (cause not
  shown; the log checks clean). Record [run:2026-10-21-chain2](../../findings/chain/experiments.md#run2026-10-21-chain2),
  finding [chain/0003](../../findings/chain/0003-end-to-end-run.md) updated; manifest `manifest-r2-final.txt`
  (`e1d9e622…`, 169 lines), tools `out/tools-r2-final.sha256` (commit `53ffb95`'s, unchanged since the checkpoint).
  **Result** (`tools/chain.py check --o20` over run 1's 28 logs and run 2's 9, under `MemoryMax=4G`): **37 logs, 0
  sub-checks failed**, and each log alone the same. **2 189** oracle-free room populations (run 1's logs 1 387, run 2's
  802); 176 levels (DrlgType 1: 65, 2: 36, 3: 75), every act of each game type in each difficulty; 13 056 objects; 63
  champion and 162 unique packs, 217 mods rolls; 1 314 drops with an item (1 492 items), 3 784 TC calls and 1 913 item
  creations, 0 failed. Re-creations 7 290: 1 903 compared line for line with the logged marks (1 729 alive, 166 dead
  `deadCol` 0, 8 `deadCol` 1), 5 284 applied unchecked on run 1's logs, 103 made no unit. Phase 1 world logs: 62 logs,
  0 failed, summary equal to run 1's but four re-creation lines. Controls: `--cf recreation-off` restores exactly run
  1's cn4 and cm4 mismatches and fails r2-xn1 (63); `--cf monequip-off` fails the two new Blood Raven cases (r2-xn2,
  r2-xm1). A first Phase 1 re-check resolved `../../../tools` through the `workspace` symlink to the main checkout's
  tools; kept as `dev-r2-p1world-check-maintools.txt` and re-run with the worktree's.
  **Done-when, as the run reads it:** 0 mismatches; 2 189 of 2 000 populations; every other count met on the same
  logs; the record lists each input and remaining oracle with its count. Chest interact-byte writer (ruling 3): not
  read; chain/0003 Open question 2, for Phase 3. Slot 1 stopped, the `p48r2` aside restored (saves directory empty).
  **Next:** the architect reviews run 2 and rules on the Phase 2 close.
- **2026-10-21 — Phase 2 run 2 reviewed (architect, on `lane/p48r2`, not merged with `main`, which touches no chain
  finding or tool): accept with fixes (4); Phase 2 closed; Phase 3 released.** Re-run with the worktree's tools under
  `MemoryMax=4G`: `chain.py check --o20` over run 1's 28 logs and run 2's 9, `chain: 37 logs, 0 sub-checks failed`,
  `out/review-r2-check.txt` byte-identical to `r2final-check.txt` and `review-r2-o20.json` to `r2final-o20.json`
  (`out/review-r2-manifest.txt`, `6d83a5e5…`); `sha256sum -c manifest-r2-final.txt` clean (`e1d9e622…`, 169 lines),
  `manifest-final.txt` clean, `out/tools-r2-final.sha256` (`797865e9…`) matches the worktree's tools, which are
  unchanged since `53ffb95`. The 37 per-log checks each 0 failed; the five control outputs each fail as recorded;
  `r2final-p1world-check.txt` differs from run 1's `p1world-check-final.txt` by the four re-creation lines only, and
  `dev-r2-p1world-check-maintools.txt` is byte-identical to run 1's (the main-tools run, kept as dev). Anchors read in
  the image: `0x0052D142` and `0x0052D205` are `call 0x542B40` (returns `0x0052D147`, `0x0052D20A`), `0x005B2E10`
  `test cl, 0x20` then `mov eax, 3`, `0x00649E9A` and `0x005A7CB1` `call 0x649400` (`UNIT_CollMark`), `0x005A7CA7`
  `call 0x5541B0`, `0x00649FD8` after `push 0x8000; push 3; push 3`, `0x005B2EAB` `call 0x5543B0`; each named
  function is in `re/symbols.csv`. Counts recounted from the re-run: 2 189 populations (323, 593, 264, 450, 263, 296),
  176 levels (65, 36, 75; every act of each game type in each difficulty), 13 056 objects, 7 290 re-creations, oracle
  13 at 4.
  **Fixes** (written into the run record and chain/0003): (1) **omission**: the record's list of inputs and remaining
  oracles left out the re-creations' own input: each one's class, unit id, cell and alive or dead state are taken from
  the log (`MT0`, `MU0`, `a10`), chain/0001's oracle 25 (the restored monster's AI and movement, a simulation input);
  now listed with its count (7 290, 103 made no unit), and chain/0003 § 2 scopes the marks' `[C]` to the marks made
  from it. (2) **overclaim**: the dead sequences' `[C]` counted r2-xn1's 34 dead cases, the log the sequence was
  corrected from; it rests on the 140 of the other eight logs (134 `deadCol` 0, 6 `deadCol` 1), said in § 2 and the
  Answer. (3) **omission**: `--cf recreation-off`'s 63 mismatches on r2-xn1 are a floor, not 288: after each mismatch
  `tools/objects.py` `resync` skips to the next `RW1`/`OO0`/`OGC`/`OPU0`, so the rest of that restore stretch is not
  tested; said in the record and § 2. (4) **misread**: the renamed stub's line in `manifest-r2-ckpt1.txt` does not
  "no longer resolve": it fails `sha256sum -c`, the name now holding the session's pilot; the stub's hash (`e3b0c442…`)
  is in `manifest-r2-final.txt` under its new name. Corrected in the record.
  **Rulings.** (1) **The 5 284 re-creations applied unchecked on run 1's logs are admissible** for the 0-mismatch
  result and the population count, not as evidence for the marks. They are model predictions entering the grid, not
  values taken from the log at a test; a wrong or missing mark that a later `COLL_WHTest` reads fails it, one no test reads
  changes nothing the run claims (the oracle-20 snapshot comparison only counts, and its residue has no cell with a
  model-only bit: every key is `-0000`); the populations are windows with no oracle inside, and the re-creations sit outside windows. The marks' `[C]` stands on the 1 903 compared (the dead
  ones on 140, fix 2) and the restored state is oracle 25's input (fix 1). (2) **cn4 and cm4 count**: they pass on
  their kept logs with the route the run-1 review ruled, their marks checked through the later tests (said in § 2),
  and `--cf recreation-off` restores exactly their run-1 mismatches. (3) **r2-cn1 is admissible**: the game process
  exited on its own at frame 10 920, gdb saw a normal exit, the log is whole to that line and checks clean, and no
  model reads anything after it; the cause stays unknown and is not a claim. (4) **The first Phase 1 re-check** (main's
  tools through the `workspace` symlink) is a development output, rightly kept and not cited; the cited re-check is
  the worktree's. A lane that runs from a log directory calls its own worktree's `tools/` by absolute path. (5) **The
  chest interact-byte writer** stays a counted oracle of the operate path (run-1 ruling 3; 7 cases, three kinds),
  outside the bar; it goes to Phase 3's *Open questions* as chain/0003 Open question 2, no reverser entry now.
  **Done-when**: met on the 37 passing logs: 0 mismatches; 176 levels (40 asked) with every generator kind, every act
  of each game type in each difficulty; 2 189 populations (2 000); 13 056 objects (300); 63 champion and 162 unique
  packs with 217 mods rolls (100 special monsters); 1 314 drops with an item (500) with no builder oracle; the record
  lists each input and remaining oracle with its count (after fix 1). **Phase 2 closed.**
  **Next: Phase 3** (spec-writer, [entry](../../backlog/archive/2026-10-21-architect-spec-writer-plan-0048-phase-3-seed-to-world-spec.md)):
  `docs/specs/chain/README.md` and the *Inputs and oracles* updates, the re-creation marks in the owning spec, the
  chest writer and oracle 13's unreached branches under *Open questions*; then Phase 4. Reverser `review-fixes.md`
  rule 6 extended (a kept file renamed under a manifest's name; seen with `lane/p46m9`'s overwritten dev outputs).
  Review request [closed](../../backlog/archive/2026-10-21-reverser-architect-review-plan-0048-phase-2-run-2.md); the
  lane's two ledger rows added (the review's row is the orchestrator's, with its usage).
- **2026-10-21 — Phase 3 written, review requested (spec-writer, `lane/s48p3`, static, no harness).**
  [specs/chain](../../specs/chain/README.md) (`draft`, C 89 / I 7 / L 6): the call order A–H from the game seed to a
  populated level and a drop, as a flowchart and a sequence diagram; the inputs by class with run 2's counts (oracle 25:
  7 290 re-creations, 103 no unit); the retired oracles linked to their models and the remaining ones counted; an
  entry-contract table; four worked examples from kept logs (`-seed 4802` to level 57, one oracle-free population of
  it, a gold drop, two r2-xn2 re-creations with their marks). Re-creation marks in
  [drlg/lifecycle § H5](../../specs/drlg/lifecycle.md#h5-the-grid-marks-of-a-re-created-monster): `[C]` on the 1 903
  compared, the dead sequences on the 140 outside r2-xn1, the call path `[I]`. *Inputs and oracles* and the stale
  passages of the Phase 1 review's ruling 5 and chain/0001 § 5 updated in 13 specs. 6 open questions, the chest
  interact-byte writer and MonEquip's unreachable branches among them. Phase 4 not started. Review request
  [entry](../../backlog/archive/2026-10-21-spec-writer-architect-review-plan-0048-phase-3-seed-to-world.md).
- **2026-10-21 — Phase 3 reviewed (architect, on `lane/s48p3`, not merged with `main`, whose `lane/s46d` merge touches
  combat/delivery only): accept with fixes (2); Phase 3 done; Phase 4 released.** Worked examples re-read from the kept
  logs: example 1 (`tools/chain.py gen --seed 4802 --diff 0 --exp 1 --levels 57`, under `MemoryMax=4G`) prints the
  game seed, the four draws, `levelSeedBase` `e0a791e4` and level 57's `e0a7921d:0000029a` and pool 374, 101, 101, equal
  to `GAME`, `OGC` and `LC0` (lines 47, 49, 2073); example 2's `RW0` (3944), `P0` (3959) and `PX` (4152) seeds, the
  wanderer `0x14BE`, the eight slots, the 27 game-seed steps to `PA`, the three creations' game and unit seeds and the
  group draw equal the log, and a check of the log listing its oracle-free populations names this one (line 3959, level
  57, 3 creations); example 3's two game-seed steps and the unit-seed step recomputed with `Step`, stat 14 = 31 at
  `IIS1`, the next `TCR`'s `gseed` `a15d299b:15eb20e3`; example 4's scope `CMR0` 39133 .. `CMRX` 39176, the room seed's
  three draws per record recomputed, and both records' `CM` sequences in order. Per-log outputs of both logs: 0
  sub-checks failed. Every count of § Inputs, the remaining-oracle table, the step notes and H5 agrees with
  run:2026-10-21-chain2's record; every `fn:`/`data:` anchor added in the 14 specs resolves in `re/symbols.csv` with its
  name; the three diagrams state nothing the text does not; the six `[L]` of chain and objects' new one are under *Open
  questions*; the tags recount to the front matters; the gate is green before and after the fixes.
  **Fixes.** (1) **overclaim**: objects *Inputs and oracles*, the operate monster spawn row said its creation "is the
  monsters chain's once the operate's frame and seeds are given"; chain/0001 oracle 8 says *would be*, and the chain
  counts those creations outside the model; the row now says so. (2) **overclaim**: drlg/room-tiles step 11's `[C]`
  header carried note 11's `[I]` preset-unit reading; split out with its own `[I]` (room-tiles I 33 → 34).
  **Rulings.** (1) **The re-creation marks** follow the `lane/p48h` and `lane/p48r2` rulings: H5's `[C]` is on the
  1 903 compared, the dead sequences on the 140 outside r2-xn1 (the 166 and 8 are observation counts, the scoping bullet
  says which carry the evidence), the marks scoped to oracle 25's values, the 5 284 unchecked admitted for the result
  only, the `recreation-off` 63 a floor, the call path `[I]`; accepted. (2) **items/tc and items/quality's "quality roll
  oracle" wording stays**: each passage is scoped to a named pre-chain run (run:2026-10-11-tc-drops' replay, worked
  example 1's table, the 266 MF-0 rolls) and true of it; both specs already state the roll modelled (items/tc's 9 184
  calls, items/quality's resolver totals), chain/0001 marks oracle 5 *chained* before plan 0048, and the chain spec's
  retired table links items/quality. A later edit of either spec may relabel the worked-example row; no entry now.
  items/cube and monsters/pool (oracles 9, 10, 23) are off the chain and rightly untouched. (3) **chain is `reviewed`**
  (front matter set at this review). (4) **Phase 4 may start**: [entry](../../backlog/archive/2026-10-21-architect-spec-writer-plan-0048-phase-4-seed-to-world-wiki.md),
  with the W4 warnings this phase's edits left on eight wiki pages folded in.
  Research map: the `chain` row (spec link, `reviewed`, counts) and the count rows of drlg/lifecycle, drlg/collision,
  drlg/room-tiles, objects and monsters/stats rewritten; dates bumped on drlg/README, monsters/spawn, monsters/special and
  items/affixes. Spec-writer `review-fixes.md` rule 9 extended (the finding's mood). Review request
  [closed](../../backlog/archive/2026-10-21-spec-writer-architect-review-plan-0048-phase-3-seed-to-world.md); the lane's
  ledger row added (the review's row is the orchestrator's, with its usage).
- **2026-10-21 — Phase 4 written, review requested (spec-writer, `lane/s48p4`).**
  [wiki/seed-to-world](../../wiki/seed-to-world.md) over [specs/chain](../../specs/chain/README.md): the call order A–H in
  prose with two diagrams, the inputs by class, how the composition was checked, three worked examples, traps and open
  questions; `based_on` chain, rng/seeds, drlg/room-tiles, drlg/lifecycle, monsters/stats and objects (2026-10-21);
  linked from the wiki index. The W4 warnings the Phase 3 edits left on characters, items, items-other-paths, levels,
  monsters, objects, randomness and saves cleared (gate W4 17 -> 0), restating only the stale passages. The Phase 4
  [entry](../../backlog/archive/2026-10-21-architect-spec-writer-plan-0048-phase-4-seed-to-world-wiki.md) closed; review
  [request](../../backlog/archive/2026-10-21-spec-writer-architect-review-plan-0048-phase-4-seed-to-world.md).
- **2026-10-21 — Phase 4 reviewed (architect, on `lane/s48p4`, not merged with `main`): accept with fixes (6); Phase 4
  done; plan 0048 closed.** Every count on [wiki/seed-to-world](../../wiki/seed-to-world.md) and the eight restated pages
  checked against the specs they cite: the inputs table against chain § Runtime state (37, 18 459, 6/25/2 and 53,
  3 784 twice, 20 109, 7 290 and 103, 473 and 479, 952/49/3, 35), the retired and remaining oracles against chain
  § Inputs and oracles (4 883 gates, 4 723 of 4 883, 2/2/7, 3/4/3, 34 and 12, 35, 8, 1, 7 with 2/3/2), step notes
  (176, 311, 13 056 = 2 888 + 10 168, 12 580 of 12 580, 63/162/217, 1 314 and 1 492, 3 784, 1 913), the three worked
  examples against chain § Worked example 1–3, H5's 1 903 and 140 against drlg/lifecycle, the gold piles' 71 of 71 and
  69 of 71 against objects § H row 28 and the chain, MonEquip's classes 234 and 267 and four creations against
  monsters/stats § B12, the hire-list oracle's 16 entries against items/vendors C1, and the 11 staff-mods oracles
  against player/creation. All agree. The chain's `[I]` (activation order, pass-entry game seed, the walk trap, the
  Orient89 preset unit, H5's call path, the gold piles' spot, MonEquip's other branches) read as code readings on the
  page. The two diagrams state nothing the text does not.
  **Fixes.** (1) **overclaim**: the page's opening said a recorded game was rebuilt "with every room, monster, object
  and drop predicted" from the game seed alone; it now says 37 games were rebuilt with 0 mismatches given the
  recording's walk and fight results and a few counted values still read from it. (2) **overclaim**: the inputs
  table's activation row stated what the walk decides flat; chain § Runtime state tags that row `[I]`, now "read from
  the code". (3) **misread**: "the game seed steps once for every unit the server creates" dropped chain E's "other
  than a player". (4) **misread**: the act, level and room seeds were said to "depend only on the game seed"; they
  depend on the seed the game was created with (the map seed), not on the stepping game seed. (5) **under-claim**: the
  re-creation marks' "which calls make the marks, in which order, is read from the code" (seed-to-world § F and levels)
  put the marks' order under the `[I]`; H5 compared the marks in order line for line (`[C]`), only the call path is
  `[I]`. (6) **other**: the Orient89 preset-unit reading was called "read from the code" in the same sentence that says
  the code adding the preset unit is not read (seed-to-world § C and levels); now "inferred", as room-tiles note 11.
  **Rulings.** (1) The `characters` paragraph on the Sorceress's staff mods and the `items-other-paths` hire-list
  restatement are scoped to their runs and true; accepted. (2) The monsters page's open question keeps spawn's own
  list (snapshot residue and the type-11 point) without the barrier grid, as monsters/spawn does; the seed-to-world
  page names the barrier grid from the chain. (3) **Plan 0048 closes.** All five phases accepted. The plan's open
  question on activation order is answered in chain § Runtime state (`[I]`: the game seed, `O` and the near lists
  depend on it; the level and room seeds do not); the vendors-and-hirelings question was left as stated (off the
  chain). Left open outside the plan: the archivist entry
  [MonEquip table doc](../../backlog/2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md) and chain's six
  `[L]` (the chest interact-byte writer, MonEquip's unreachable branches by a forced-path run, oracle 19's room flags,
  oracle 20's model side, the other monster-creating `InitFn`s and MonPlace rows, a log-free world build), for a later
  plan. Research map: the `chain` row's wiki cell set to the page. Spec-writer `review-fixes.md` rules 2 and 8 extended.
  Review [request](../../backlog/archive/2026-10-21-spec-writer-architect-review-plan-0048-phase-4-seed-to-world.md)
  closed; the lane's ledger row added.
