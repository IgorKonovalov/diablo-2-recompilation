# 0027 — Backlog sweep 3: the follow-ups of plans 0021–0026

> **Status:** draft
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** which open backlog entries left by plans 0021–0026 can be closed with the code, the data and one short
round of harness runs? These plans closed with named boundaries. Some boundaries are logged values the model could
now predict: the object marks fed to the collision grid, and the out-room grids the room-tiles model reads. Some are
cases no run reached: levels 39 and 134, the `berserk` mod, one creation logged with both item loggers, and a
superior ethereal item with `dur%`. Several are table-doc follow-ups and one tool crash. This plan works through them
in the manner of [plan 0020](0020-backlog-sweep-2.md):
1. data docs and the tool fixes;
2. the static code reads and the model switch-overs on logs already recorded;
3. one harness round for the runtime cases;
4. the spec edits.

When it is done, every entry listed below is struck or carries a **Plan:** pointer. drlg/collision and
drlg/room-tiles no longer take the object marks and the out-room grids from the log, and the cases the harness round
reaches are `[C]`.

## Context

- Entries in scope (all in [backlog](../backlog.md)):
  - **archivist**, table docs: the plan 0021 Phase 2 results (Skills `firstSkill`, MagicPrefix and MagicSuffix); the
    plan 0022 Phase 2 follow-ups (Levels `Depend`, LvlPrest); the plan 0025 Phase 2 results (MonProp, DifficultyLevels,
    `DamageRegen`); the plan 0026 Phase 2 follow-ups (b) and (c) (Levels outdoor sizes, LvlPrest index routes); the
    ItemStatCost record tail (`+0x051`, `+0x05E..+0x13F`); the plan 0023 Phase 2 results (Objects `Mode1` and the
    other columns objects/0001 § 12 names);
  - **archivist**, tools: `tools/d2s.py build` crashing on a Tome of Town Portal (`tbk`, `KeyError: 'tome'`, plan 0026
    follow-up (a)); a status-byte check, so a recipe built as classic cannot come out as an expansion character (two
    runs were mislabelled: run:2026-10-15-drlg-maze s4, run:2026-10-15-objects s7–s8); the open parts of the plan
    0024 harness-findings entry ((a) is done by `tools/d2run.py`'s 1030×800 float rule);
  - **reverser**, static: feed the object marks of `tools/objects.py` into the collision model; switch `drlg.py roomk`
    to the predicted out-room grids (architect ruling: run the roomk passes inside `gen` on the 38 logs with both `OD0`
    and `LSUB`); the room-tiles 9d entry-flag formula (`sub_0066DB20_RoomTileSetFlags`, cell bits 28, 17, 16); why the
    Pandemonium key transmute did nothing in single-player hell (level 134); what gates Arcane Sanctuary (74) in the
    waypoint menu (the Canyon half of that entry is answered);
  - **reverser**, harness: one items run with both `tools/gdb/affixes.gdb` and `tools/gdb/props.gdb` (the logger tag
    clash ETH0/ETH1 vs ETH0/ETHR/ETHX, listed in [items/experiments](../findings/items/experiments.md), is fixed first),
    including a superior ethereal item with `dur%`; a forced-path run (ADR-0010) for `berserk`; the outdoor windows of
    levels 39 and 134 once the tool fix and the transmute read allow them; the plan 0019 ladder-row and TC-named
    disabled-row cases (items/0004 (c) and (d), forced path);
  - **spec-writer**: the edits these produce in drlg/collision, drlg/room-tiles, objects, drlg/outdoor,
    monsters/stats, items/affixes, items/properties and items/uniques-sets.
- Out of scope, routed elsewhere or left open:
  - the objects details blocking `objects` review → [plan 0023](done/0023-objects.md) (in flight);
  - the Acts III–V owner session and the client row-skip counter → [plan 0020](0020-backlog-sweep-2.md) Phase 4;
  - the `*code.bin` formats → `data/calc`, no plan; the 1.14d `patch_d2.mpq` question → no plan (needs the signed
    patch executable);
  - the 2026-10-11 D2S fields entry: triage only in Phase 1 (strike what plan 0013 and `save/d2s` answered, route the
    rest);
  - multiplayer, the Direct3D/Glide control-word question, and the paths stock data never reach → spec *Open questions*.
- Slots: Phase 3 needs at most two slots (ADR-0011). Phases 1 and 2 need none, and can run side by side.

## Phases

### Phase 1 — Table docs, tool fixes and backlog triage
- **Owner skill:** archivist
- **What:** apply the table-doc follow-ups above, fix the `tbk` crash, add the classic status-byte check to
  `tools/d2s.py build` (or `tools/saves.py install`), and triage the 2026-10-11 D2S fields entry.
- **Outputs:** [Skills](../tables/Skills.md), [MagicPrefix](../tables/MagicPrefix.md), [Levels](../tables/Levels.md),
  [LvlPrest](../tables/LvlPrest.md), [MonProp](../tables/MonProp.md), [DifficultyLevels](../tables/DifficultyLevels.md),
  [ItemStatCost](../tables/ItemStatCost.md), [Objects](../tables/Objects.md); `tools/d2s.py` with a test in
  `tools/test_d2s.py`; the backlog.
- **Done when:**
  - each listed table-doc entry is struck, with the doc section it landed in;
  - `tools/d2s.py build` writes a recipe with a `tbk` in the cube, and the written file loads (`tools/d2s.py` round
    trip);
  - building a classic recipe on an expansion base, or the reverse, is refused, with a test;
  - the D2S fields entry is struck, or split into answered and routed parts.

### Phase 2 — Static reads and model switch-overs
- **Owner skill:** reverser
- **What:** feed the object marks into the collision model, move `roomk` onto the predicted out-room grids, read the
  room-tiles entry flags, the Pandemonium key refusal and the Arcane Sanctuary gate. Logs already recorded only.
- **Outputs:** `tools/collision.py`, `tools/objects.py`, `tools/drlg.py`; [drlg/0005](../findings/drlg/0005-collision.md),
  [drlg/0002](../findings/drlg/0002-room-build-draws.md), [objects/0001](../findings/objects/0001-object-population.md),
  [save/0002](../findings/save/0002-quest-words.md) or the cube finding; run-record addenda.
- **Done when:**
  - `collision.py check` on run:2026-10-15-objects takes the object marks from `tools/objects.py`, and all 5 767
    object `COLL_WHTest` results are predicted, 0 mismatches; the older collision and monspawn runs stay at 0;
  - `drlg.py gen` runs the roomk passes on the 38 logs with `OD0` and `LSUB` from predicted grids, 0 mismatches, and
    the six run:2026-10-11-drlg-roomk logs stay at 0;
  - the 9d flag formula is stated per entry kind (floor, wall, shadow, bit-2 merge) with anchors, `[C]` against the
    logged entry flags;
  - the transmute refusal and the Arcane gate are each named with an address and a tag, and the recipe change a run
    needs is in the backlog for Phase 1 or 3;
  - each re-analysis is recorded as a dated addendum to the run whose logs it uses (architect ruling 2026-10-15).

### Phase 3 — One harness round
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md); at
  most two slots)
- **What:** log the runtime cases no run has reached.
- **Logging:** both item loggers in one session (`affixes.gdb` and `props.gdb`, the tag clash fixed); `mon-stats.gdb`
  for the `berserk` run; `drlg-outdoor.gdb` for levels 39 and 134.
- **Done when:**
  - a run `run:YYYY-MM-DD-items-chain` holds creations with both line sets, and `tools/items_chain.py` checks at
    least 200 of them end to end with no seed oracle between the affix pick and the property roll, 0 mismatches,
    including at least one superior ethereal item with `dur%` (forced path if needed, ADR-0010);
  - a forced-path run `run:YYYY-MM-DD-berserk-forced` (MonUMod edited so `berserk` is drawn) shows at least 10
    `berserk` champions with their stats reproduced by `tools/monstats.py`, 0 mismatches; no frequency claim;
  - levels 39 and 134 are each generated at least once and reproduced by `drlg.py gen`, or stay named boundaries
    with the reason;
  - the items/0004 (c) ladder row picked in single player and (d) TC-named disabled row (forced path) are logged
    and reproduced by `tools/uniques.py`, or stay open with the reason;
  - if slots allow: one session targeting a casket group (Objects class 1 or 79) and an orientation-2 shrine, so
    objects/0001 § 13.1–13.2 move to `[C]` (optional, architect ruling 2026-10-15);
  - every slot used ends at `aside: none`.

### Phase 4 — Spec edits
- **Owner skill:** spec-writer
- **What:** apply what Phases 2 and 3 settle to the specs named in Context; the reviewed specs stay reviewed when
  the edits only promote tags or replace logged inputs.
- **Outputs:** [drlg/collision](../specs/drlg/collision.md), [drlg/room-tiles](../specs/drlg/room-tiles.md),
  [objects](../specs/objects/README.md), [drlg/outdoor](../specs/drlg/outdoor.md),
  [monsters/stats](../specs/monsters/stats.md), [items/affixes](../specs/items/affixes.md),
  [items/properties](../specs/items/properties.md), [items/uniques-sets](../specs/items/uniques-sets.md).
- **Done when:** each spec's *Inputs and oracles* row and open question touched by Phases 2–3 is updated, with tag
  counts; every spec-writer entry from this plan is struck; the architect's review passes.

## Open questions

- Whether a stock-data `berserk` run is worth adding later for a frequency claim (not needed for a reimplementation).
- Whether the Pandemonium key transmute needs a multiplayer game; if so, level 134 stays a boundary (no multiplayer
  harness).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_
