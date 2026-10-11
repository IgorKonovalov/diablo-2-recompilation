# 0004 — Items: treasure class resolution

> **Status:** in-progress (approved; Phase 1 unblocked 2026-10-11: plan 0002 named `treasureclassex` the live TC table)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers

## TL;DR

How does a monster kill become a list of items to create? This plan follows the drop path from the
monster's death to the hand-off into item creation. It covers which TC is chosen (difficulty,
champion/unique/quest columns, level-based upgrade), the pick loop (positive and negative `Picks`),
`NoDrop` and its player-count scaling, recursion into sub-TCs, the auto-generated `weapN`/`armoN`
classes, and the quality ratios (`Unique`/`Set`/`Rare`/`Magic`) passed down the chain. Every draw is
tied to the seed it comes from. When it's done, `docs/findings/items/0001-tc-resolution.md` has the code
path at `[I]` or better, `tools/tc.py` reproduces recorded drops bit for bit, and
`docs/specs/items/tc.md` is drafted.

## Context

- Research-map row `items/tc` (core), status `not started`. Dependencies: `rng` is `reviewed`
  (primitives `[C]`). Plan 0002 provides the live TC table and the layouts of `treasureclassex`,
  `itemratio`, `itemtypes`, `weapons`/`armor`/`misc` and `monstats`.
- Corroboration depends on the plan 0003 harness (Phase 2). Phase 1 can start without it.
- A starting point from `rng/0002`: items get their unit seed from a creation parameter
  (`.\ITEMS\Items.cpp`, 0x00558D90, `+0x48`/`+0x4C`) rather than from a room draw. Where that parameter
  is drawn, and from which seed, is the TC→item hand-off this plan has to pin down.
- Leads: none registered yet. If community TC guides are used, register them in `docs/sources.md`
  first, and they stay `[L]` until anchored. Phase 1b compares the finished finding against them.

## Phases

### Phase 1 — Find and read the drop path
- **Owner skill:** reverser
- **What:** Starting from the readers of the TC table pointer (plan 0002) and the `monstats`
  `TreasureClass*` fields, find the drop entry point, TC selection, the pick loop, `NoDrop`, the
  recursion, and the call into item creation.
- **Outputs:** `docs/findings/items/0001-tc-resolution.md`, `re/symbols.csv` rows (subsystem `items/tc`),
  `re/types/` struct(s) for the TC record if the code uses one.
- **Done when:** the finding names, with addresses and `[I]` or better:
  - the drop entry point(s) for monster death, plus where objects and chests call into the same
    resolver (named only; their callers belong to `objects`);
  - TC selection: difficulty column, champion/unique/superunique/quest variants, and any level-based
    TC upgrade, each with its table field;
  - the pick loop: what is drawn, from which seed object, the range-form (guarded `RNG_Range`, or an
    inlined `%`), and the call order, including negative `Picks`;
  - `NoDrop` with player count and party size: the exact integer formula, operand widths, rounding;
  - recursion: depth limit, how quality ratios combine down the chain (max? override?), and how
    `weapN`/`armoN` codes resolve to item lists;
  - the hand-off: the arguments item creation receives (base item, ilvl source, quality ratios, the
    item seed parameter) and where that seed comes from.
  
  Quest-drop special cases met on the path are recorded with their addresses and left for
  `items/quest-drops`.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** After the Phase 1 finding is written, compare its behavioural claims with community TC
  documentation, following `evidence-rules.md` § Community cross-checks (blind first; agreement
  never promotes a tag).
- **Outputs:** `docs/sources.md` entries for each source compared (with the game version it
  describes), verdicts in the *Leads used* section of `findings/items/0001-tc-resolution.md`, and
  backlog entries for each `contradicted` verdict.
- **Done when:** at minimum TC selection (difficulty and monster-type columns, level upgrade),
  negative `Picks`, the `NoDrop` player-count formula, ratio inheritance and `weapN`/`armoN`
  resolution each carry a verdict with a `src:` id, or `not covered` if no registered source
  addresses it. Every `contradicted` claim is either re-read (and the finding corrected) or made a
  required case in the Phase 2 reproduction set.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser
- **What:** Write `tools/tc.py` (it reads tables through `tools/excel_bin.py` and draws through
  `tools/rng.py`), then check it against drops recorded with the plan 0003 harness. Break at the
  resolver, dump the input TC, seed state, player count and the output list.
- **Outputs:** `tools/tc.py`, `run:YYYY-MM-DD-tc-drops` in `docs/findings/items/experiments.md`, and
  promoted tags in the finding.
- **Done when:** `tools/tc.py` reproduces at least 50 recorded resolver calls exactly (output list and
  final seed state). The set must include a negative-`Picks` TC, a recursive TC with ratio
  inheritance, a `weapN`/`armoN` class, and `NoDrop` at two different player counts. The claims it
  covers are promoted to `[C]`.

### Phase 3 — Spec: items/tc
- **Owner skill:** spec-writer
- **What:** Write `docs/specs/items/README.md` (the item-creation overview, as far as it's known) and
  `docs/specs/items/tc.md`: pseudocode with exact draw order, integer semantics and table lookups.
- **Outputs:** the two spec files, plus glossary entries (TC, Picks, NoDrop, ratio).
- **Done when:** the spec follows the template, every statement is tagged, a worked example from
  `run:…-tc-drops` is included, and the architect's review passes.

## Open questions

- Is the resolver shared with gambling and vendor stock, or only with objects? Phase 1 records the
  callers, and `items/vendors` decides.
- Out of scope: quality rolls, ilvl→alvl, affixes and uniques. They start at the hand-off and
  belong to `items/quality` (the next plan in the items chain).

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Approved (human).** No phase started yet.
- **2026-10-11 — Amended (architect).** Added Phase 1b (community cross-check) per the new
  `evidence-rules.md` § Community cross-checks. Phase 2 must include any contradicted claims.
- **2026-10-11 — Phase 1 done (reverser).** [items/0001](../findings/items/0001-tc-resolution.md) written: monster
  death → `MONSTER_DropItems` (TC column: superunique → champion → unique → normal, quest TC4) → `TC_DropByIndex`
  (level upgrade: expansion, diff > 0, not `noRatio`/`boss`) → `TC_ResolveDrops` (pick loop, NoDrop x87 formula,
  64-frame stack, ratio max, hand-off to `sub_0055A550_DropCreateItem`); object chests named (`sub_00585B90_ObjectChestDrop`,
  "Act N Chest A/B/C"). All behaviour `[I]`; the runtime TC layout and the difficulty/expansion fields are `[C]`.
  37 symbols (subsystem `items/tc`), `re/types/tc.h`. Two things for Phase 2: (1) the per-item quality roll
  (`sub_00558640_DropRollQuality`, 0–6 `RNG_RangeB` draws) runs inside the resolver on the **same source-unit seed**,
  so `tools/tc.py` can only reproduce final seed states if it models that roll; Phase 2 needs a plan amendment or a
  hand-off from `items/quality`; (2) the NoDrop formula is x87 floating point, so the FPU precision control must be
  logged. Phase 1b (cross-check) is next.
