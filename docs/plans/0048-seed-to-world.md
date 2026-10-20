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
  once across all plans; the end-to-end logger sets only entry and exit breakpoints (no per-frame path, ADR-0014 § Log
  volume applies by analogy).
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
