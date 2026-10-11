# 0004 — Items: treasure class resolution

> **Status:** in-progress (approved; Phase 1 unblocked 2026-10-11: plan 0002 named `treasureclassex` the live TC table)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction

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
  `tools/rng.py`), then check it against drops recorded with the plan 0003 harness (ADR-0003). The
  quality roll is a **boundary oracle** (ADR-0004), not modelled here. Breakpoints log, per resolver
  call:
  - at `TC_ResolveDrops` entry: TC index, source unit (type, class, seed `+0x20`), killer, `ilvl`,
    `noNoDrop`, `game+0x6A`, `game+0x6D`, `game+0x70`, and the inputs of the NoDrop scaling (party count,
    player count, the source's `monster_playercount`);
  - at `0x0055A93B` (the NoDrop `fild`): the x87 control word (`$fctrl`), and at `0x0055A9B9` the
    resulting `NoDrop'`;
  - **oracle** `sub_00558640_DropRollQuality`: source seed on entry and on exit, its arguments (item
    index, `ilvl`, the four ratio words) and the returned quality;
  - around `sub_0055A550_DropCreateItem`: the source seed before and after, and the created unit
    (item index, quality, unique/set index, flags). items/0001 claims creation does not touch the
    source seed, so the checker asserts that before == after;
  - at return: the output count and the final source seed.

  `tools/tc.py` asserts the predicted source seed at every oracle entry and at the end. A missing exit
  line is a failure.
- **Producing drops:** the harness so far only reaches town (ADR-0003 § Negative). Kills come from
  a steps file (walk, attack) on a fixed `-seed`, or, if scripted combat is impractical, from a
  human playing the isolated display (`:7`) while gdb logs. Determinism is not required for the
  check, because every call carries its own inputs, but the record must say which method produced it.
  Set the second player count with `/players N` **before** the monsters spawn, since
  `monster_playercount` caps the count at its value at spawn time.
- **Outputs:** `tools/tc.py`, `tools/gdb/tc-drops.gdb`, `run:YYYY-MM-DD-tc-drops` in
  `docs/findings/items/experiments.md` (naming the oracle), promoted tags in the finding, and answers
  to items/0001's open questions on precision control, `game+0x6A` and creation stepping the source seed.
- **Done when:** `tools/tc.py` reproduces at least 50 recorded resolver calls exactly: every oracle-entry
  seed, the output list (item, quality from the oracle, unique/set index, flags) and the final source
  seed. The set includes a negative-`Picks` TC (champion), a recursive TC with ratio inheritance, a
  `weapN`/`armoN` class, a unique-monster or superunique TC, `NoDrop` at two player counts with
  `NoDrop'` matching the model, and at least one call after a level upgrade (Nightmare or Hell; skip
  only if no such save can be made, and say so). The set also includes three cases from Phase 1b: (a) **NoDrop party
  test** (`contradicted` in items/0001): a kill with a partied second player in the killer's level but far from the
  killer (well beyond two screens), with `party` and `NoDrop'` logged at `TC_ResolveDrops`. A second partied player in
  another level is optional. This needs a second client. If the harness can't run one in this phase, say so in the run
  record, leave the claim `[I]`, and file a backlog entry that blocks `items/tc` from reaching `reviewed` until it is
  run. (b) A level upgrade where the base TC's own `level` is above the monster's mlvl, showing the walk keeps the
  base TC. Find a stock monster/TC pairing with the archivist's table tools; if the stock tables have none, say so.
  (c) A `noRatio` monster killed in Nightmare or Hell, showing no level upgrade. If no stock `noRatio` monster can be
  reached, say so. The FPU control word is recorded and the NoDrop model
  uses that precision. In-scope claims are promoted to `[C]` and cite the oracle. The classic-game
  branches stay `[I]` unless a classic character is also run.

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
  belong to `items/quality` (the next plan in the items chain). That plan must re-run the
  `run:…-tc-drops` logs with the quality oracle replaced by its model (ADR-0004).

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

- **2026-10-11 — Amended (architect).** Phase 2 rewritten for the Phase 1 report. The quality roll
  shares the source seed, so it is a logged boundary oracle with an entry-seed assertion (ADR-0004),
  and stays out of scope. Added logging for the x87 control word, `game+0x6A` and the source seed around
  item creation. Added the drop-producing method (scripted, or human on `:7`), `/players` before spawn,
  and unique/superunique and level-upgrade cases to the required set.

- **2026-10-11 — Phase 1b done (reverser).** Cross-checked [items/0001](../findings/items/0001-tc-resolution.md#leads-used)
  against two registered sources, `src:pd-item-generation` and `src:hrus-mf-guide` (both 1.10/1.11 LoD); 15 verdicts:
  4 held, 7 held with refinement, 2 not covered (superunique TC source, ratio inheritance), 2 contradicted (the same
  claim in both sources: partied players count fully only "within two screens"). Re-read: 1.14d counts party members in
  the killer's **level** (`0x005405A0`, room → level id), no distance test; the finding keeps its claim and gains the
  re-read, and a backlog entry asks the architect to make it a required Phase 2 case. No tag changed. Four helper
  symbols added (`items/tc`). Other sources (PureDiablo wiki/tutorial pages, Arreat Summit, Amazon Basin) were
  unreachable (HTTP 403) or had no mechanics, and are not registered. Awaiting architect review.
- **2026-10-11 — Phase 1b reviewed (architect).** Accepted with fixes 1–4 (sent to the reverser: the backlog step
  number, links from the `contradicted` verdicts to their backlog entry, the SKILL.md wording on settling a
  contradiction, and the D2R note in `docs/sources.md`). The NoDrop party re-read was confirmed by an independent
  read-only decompile of `0x005405A0`; it stays `[I]`. Phase 2 gains three required cases (Done when): party in the
  same level, base TC above mlvl, `noRatio` in NM/Hell.
