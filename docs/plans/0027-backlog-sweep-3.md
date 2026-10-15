# 0027 — Backlog sweep 3: the follow-ups of plans 0021–0026

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** which open backlog entries left by plans 0021–0026 can be closed with the code, the data and one short
round of harness runs? These plans closed with named boundaries. Some boundaries are logged values the model could
now predict: the object marks fed to the collision grid, and the out-room grids the room-tiles model reads. Some are
cases no run reached: levels 39 and 134, the `berserk` mod, one creation logged with both item loggers, and a
superior ethereal item with `dur%`. Several are table-doc follow-ups and one tool crash. This plan works through them
in the manner of [plan 0020](done/0020-backlog-sweep-2.md):
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
  - the objects details blocking `objects` review → [plan 0023](done/0023-objects.md) (closed 2026-10-15; `objects` reviewed);
  - the Acts III–V owner session and the client row-skip counter → [plan 0020](done/0020-backlog-sweep-2.md) Phase 4;
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
- **2026-10-15 — Approved (human).** The owner approved it together with plans 0028–0036 as the unattended queue.
  Phase 1 (archivist) and Phase 2 (reverser) can start.
- **2026-10-15 — Phase 1 landed (archivist, branch `lane/a27p1`).** Tools (`49802bc`): `tools/d2s.py build` writes the
  5-bit `tome` field of `tbk`/`ibk` (0, as the one sample tome), so Wirt's Leg and a Tome of Town Portal in the cube
  build, read back and round-trip; recipes now require `"game": "classic" | "expansion"`, checked against the base's
  status byte (bit `0x20`), and all 13 recipes declare it (no built save changed; `keynova`, `objclassic`, `objnova`,
  which the test's recipe map lacked, now rebuild to their run hashes). `tools/test_d2s.py` `GameTest`: both
  mismatches, a missing key, the tome round trip (23 tests, OK). The plan 0024 harness entry's open part (b):
  `tools/d2run.py --install TAG FILE...` reinstalls the test saves at each launch (`saves.py install` with its own PID
  ignored), tests in `tools/test_slots.py` (33, OK). Table docs, every listed entry struck with its section:
  Skills (`firstSkill` `[C]` for classes 1–6), MagicPrefix/MagicSuffix (`classspecific` on classless types `[C]`, the
  whole-pick reproduction), Levels (`Depend` `[C]` on level 27, 117's link-pick size `[C]`, `MonLvl1` in every
  difficulty `[C]`), LvlPrest (warp slots, outdoor index routes `[C]`), MonProp (`[C]` run-time bullet),
  DifficultyLevels (no `+0x30`/`+0x38` reader `[I]`, `[L]` struck), MonStats (`DamageRegen` in the stat callback
  `[C]`), ItemStatCost (record tail `[I]`), Objects and ObjGroup (Phase 2 readers `[C]`, `Mode1`, slot coverage).
  The D2S fields entry is triaged: (e) answered from items/0005 § 1 in d2s.md, (d) routed to plan 0029.
  Surprise: the LvlPrest *Slots with no `Vis`* bullet was wrong as data, not only as behaviour (`File4` of the
  Basement NW/SE records has no slot cell; corrected, the survey output shows it). `excel_layout` is unchanged: the
  ItemStatCost tail is documented without a layout edit (`keepzero` stays a u32 in `excel_layouts.py`; the doc notes
  the reader treats `+0x051`/`+0x052` as their own bytes). Gate fast tier and the `d2s`, `d2s_roundtrip`,
  `ds1_warps`, `excel_layout` surveys green. Left open: none of the Phase 1 bullets; the harness-play note for the
  reverser is in the backlog.
- **2026-10-15 — Phase 2 done (reverser, static, branch `lane/r27p2`); review requested.** No game run. *Done when*:
  - **Object marks and `COLL_WHTest`:** `tools/objects.py` keeps the `tools/collision.py` grid model, makes every object
    mark (`UNIT_CollMarkRect`, `HasCollision[mode]`, plus `OBJINIT_Portal`'s early mark) and predicts every `COLL_WHTest`.
    On run:2026-10-15-objects all 5767 placer tests and the 92 gold-pile tests (5859) and all 1847 object marks are
    predicted, 0 mismatches (`objects.py check` 150 338 checks; `collision.py check` 279 524 + 28 177 checks). The older
    runs stay at 0: collision 75 812 + 20 537, monspawn 114 363, monspecial 390 144 + 31 485, monstats 62 991.
    InitFn 28's room test was corrected (the running position is the last tested cell). `[C]`
    ([drlg/0005 § 14](../findings/drlg/0005-collision.md#14-plan-0027-phase-2-the-objects-window-on-the-grid-model-2026-10-15),
    [objects/0001 § 14](../findings/objects/0001-object-population.md#14-the-position-tests-and-the-object-marks-on-the-grid-model-plan-0027-phase-2-2026-10-15)).
  - **roomk on predicted grids:** `drlg.py gen` runs the roomk passes on GenModel's out-room grids in the 40 logs with
    `OD0` and `LSUB` (the 38 plus `objects-s29`/`s30`, recorded after the plan 0026 addendum): 2884 type-1 rooms,
    12 974 activations, 434 721 roomk checks, 0 mismatches. The six run:2026-10-11-drlg-roomk logs: 11 734 checks, 0.
    `gen` on every log with `OD0` plus the run:2026-10-15-drlg-outdoor logs: 1 279 642 checks, 0.
  - **9d flag formula:** stated per kind (wall, floor, shadow, bit-2 merge, plus Orient89Unit `0x20`, warp and
    AnimTilesBuild `0x8`s) in [drlg/0002 § Entry flags](../findings/drlg/0002-room-build-draws.md#entry-flags-in-full-and-the-entry-chains-plan-0027-phase-2-2026-10-15),
    `[C]` on 3 684 791 logged entries (and 1 786 086 in the objects logs). Surprise: the entries form real chains, and
    the warp adders re-link an entry into the warp node's list, cutting older entries off the node for the neighbour
    scan. `monstats-s5` exposed it. k did not change on any log.
  - **Transmute and Arcane gate:** the Pandemonium outputs are stubs in this `Game.exe` (`data:g_CubePortalFns@0x006E11C8`,
    `0x00594270`/`0x00594280` return 0), `[C]` with session k1. Level 134 cannot be reached on stock data; architect
    ruling requested (forced path or named boundary). Arcane Sanctuary (74) has no gate besides waypoint bit 16
    (`fn:sub_0049C7F0_WpMenuListBuild@0x0049C7F0`), `[I]`; Phase 3 clicks Act II row 8 with the existing save. Both in
    [save/0002 §§ 5–6](../findings/save/0002-quest-words.md#5-arcane-sanctuary-74-in-the-waypoint-menu-plan-0027-phase-2-2026-10-15); backlog entries for Phase 3.
  - **Addenda:** run:2026-10-15-objects, run:2026-10-14-collision, run:2026-10-13-mon-spawn, run:2026-10-14-mon-special,
    run:2026-10-15-mon-stats, run:2026-10-15-drlg-outdoor.
- **2026-10-15 — Phase 4 part a done (spec-writer, branch `lane/s27p4a`); review requested.** The four specs Phase 2
  settled; all stay `reviewed`. [drlg/collision](../specs/drlg/collision.md): § E6 `WHTest` and the object marks of § F
  (mode after the InitFn and PreOperate, `OBJINIT_Portal`'s early mark) `[C]`; the object rows of the mask table `[C]`
  except `0x804` and the door `0x400`; the *Inputs and oracles* rows for the object marks and tests and for the entry
  flags are now modelled. Tags C 102 → 110, I 56 → 55, L 13 → 12. [drlg/room-tiles](../specs/drlg/room-tiles.md): step 9d
  states the whole flag word per kind (`CellBits`, `SetWallFlags`, floor, shadow), the chains through `+0x20` and the
  9a scan along them, the warp re-links and `0x8`s (10a, 10b), the animation frames (7b) and `Orient89Unit`'s row tables
  with a predicted draw (step 11); § k: the type-1 grids are predicted on the 40 logs. Tags C 72 → 85, I 44 → 46, L 0.
  [objects](../specs/objects/README.md): G4 (marks), F6 and `InitFn` 28's running position `[C]`, the two collision
  rows modelled, the worked example's tests and marks predicted. Tags C 130 → 134, I 57 → 58, L 5 → 4.
  [drlg/outdoor](../specs/drlg/outdoor.md): level 134 unreachable through the cube `[C]` (save/0002 § 6) and a named
  boundary, § M fed to room-tiles. Tags C 166 → 168, I 23 → 24, L 3. Open questions: collision 11, room-tiles 8,
  objects 8, outdoor 3 bullets (struck ones not counted). The spec-writer backlog entry of Phase 2 is struck. Part b
  (monsters/stats, items/affixes, items/properties, items/uniques-sets) waits on Phase 3.
- **2026-10-15 — Phase 3 done (reverser, harness, branch `lane/h27p3`, slot 3); review requested.** *Done when*:
  - **items-chain:** run:2026-10-15-items-chain, 32 logs with both item loggers (`tools/gdb/items-chain.gdb`): 889
    creations reproduced by both passes of `tools/items_chain.py both`, 0 failed; 219 with a pick checked end to end
    (no seed oracle between the pick and the property roll); three superior ethereal `dur%` items (forced ItemRatio
    variant H), `h + ⌊h · dur%/100⌋` `[C]` in items/0006 § 4.
  - **berserk:** run:2026-10-15-berserk-forced (MonUMod edited): 33 berserkers in 33 packs (19 of them seed-asserted by the pack model), `tools/monstats.py` 30 863
    checks, 0 mismatches; level + 3 for berserkers, + 2 for champion members `[C]` (monsters/0004). No frequency claim.
    Surprise: `tools/monspawn.py` took every mon-stats log for an objects log (mon-spawn.py's `RW` lines carry `"os"`
    since plan 0023); fixed to require an `OGC` line.
  - **levels 39 and 134:** 39 reached by the cube recipe (`CowNova`) and reproduced by `drlg.py gen` (0 mismatches),
    with 74 by waypoint in the same session (run:2026-10-15-cow-arcane); 134 stays a named boundary (ruling).
  - **items/0004 (c) and (d):** (c) was already reproduced in run:2026-10-14-uniques-forced; (d), with (b), in
    run:2026-10-15-uniques-tcnamed-forced (TreasureClassEx edited): 108 creations, 0 failed; the first-row rule `[C]`.
  - **optional casket/shrine session:** not run.
  - **slots:** slot 3 ends at `aside: none`; slot 4 unused.
- **2026-10-15 — Phase 3 accepted with fixes (architect, on `lane/h27p3`, after merging main).** Manifests verified;
  every check rerun from the worktree, before and after the merge, 0 mismatches (items-chain 889 both passes / 219 end
  to end; berserk monstats 30 863, monspawn 188 628, collision 15 165; cow-arcane 8 778; tcnamed 108 and 163 TC calls).
  Rulings: (1) variant H is a valid ADR-0010 decision-table edit, but stock and forced sessions shared a non-`-forced`
  id, so the forced sessions are now run:2026-10-15-items-chain-forced and the `dur%` `[C]` cites it; (2) the MonUMod
  row 0 edit taints no claim (only the champion-chance roll reads it; the berserk handler reads no MonUMod cell); (3)
  "end to end" counts the 219 picks checked from both sides (66 `ITEMS_PickMagicAffix`, 153 superior QualityItems),
  ≥ 200 met; (4) the superior ethereal `dur%` `[C]` covers only what the three items show, the `+ 1` order against
  src:arreat-summit-item-pages is `[I]` with the verdict under *Open questions*. Fixes beyond the four: the items/0004
  promotions on run:2026-10-15-uniques-tcnamed-forced are reverted to `[I]` (ADR-0010: only edited data reaches a
  TC-named row, and the edited cells are the claims' input; the (d) case is logged and reproduced, so its *Done when*
  line is met without a tag change); save/0002 § 5 "no quest-word test" back to `[I]` (a `quests: all` save cannot
  separate it); the berserk pack count corrected. The optional casket/shrine session was not run (objects/0001
  § 13.1–13.2 unchanged). Phase 4b (spec-writer) is next, from the corrected spec-writer backlog entry.
- **2026-10-16 — Phase 4 part b done (spec-writer, branch `lane/s27p4b`); review requested.** What Phase 3 settled, with
  the review's narrowing; every spec stays `reviewed`. [monsters/stats](../specs/monsters/stats.md): the `berserk` row
  (flag 1), its § E2 stat-74 part and § G6's berserker level + 3 (champion members + 2) `[C]` on
  run:2026-10-15-berserk-forced (33 berserkers in 33 packs, no frequency or champion-chance claim). Tags C 95 → 99,
  I 57 → 54, L 5. [items/affixes](../specs/items/affixes.md): 219 creations end to end (66 `ITEMS_PickMagicAffix`, 153
  superior `QualityItems`; stock alone 186 / 36), run:2026-10-15-items-chain and run:2026-10-15-items-chain-forced cited
  as separate ids, the `[L]` on the both-loggers run struck. Tags C 111 → 112, I 45, L 5 → 4.
  [items/properties](../specs/items/properties.md): both line sets `[C]`; the superior ethereal `dur%` note is a `[C]` for
  what the three items show (func 13 first, the base stat 73 halved to `⌊max/2⌋ + 1`, stat 72 the re-evaluated 73, the
  three values) and an `[I]` for the `+ 1` order; the contradicted community verdict stays under *Open questions*. Tags
  C 127 → 129, I 35, L 4 → 3. [items/uniques-sets](../specs/items/uniques-sets.md): run:2026-10-15-uniques-tcnamed-forced
  cited as agreeing under § F's `[I]`, tags unchanged (C 70, I 52, L 6); [items/tc](../specs/items/tc.md) likewise under
  *Open questions* (C 43, I 76, L 8). [drlg/outdoor](../specs/drlg/outdoor.md): level 39 `[C]` (run:2026-10-15-cow-arcane,
  drlg/0008 § 15) in *Entry points*, the dispatch table, the border-stamp call sites, H0 and H7; 134 stays the named
  boundary. Tags C 168 → 170, I 24 → 22, L 3. [drlg/collision](../specs/drlg/collision.md): the 74 open question notes the
  waypoint entry and keeps "no quest-word test" code-read (save/0002 § 5 `[I]`), tags unchanged. save/d2s not touched (it
  cites no waypoint menu row). Research-map rows updated for the four changed specs. Open questions: stats 5, affixes 4,
  properties 3 bullets with an `[L]`, uniques-sets 6, outdoor 3 (struck parts not counted). The Phase 4b spec-writer
  entry is struck; filed for the reverser: drlg/0008's lines that still call level 39 `[I]`.
