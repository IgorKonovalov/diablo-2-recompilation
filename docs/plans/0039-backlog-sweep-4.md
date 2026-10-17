# 0039 — Backlog sweep 4: the static loose ends and the open questions a reading settles

> **Status:** approved (owner, 2026-10-16; unattended)
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0006-docs-gate, 0007-fetched-leads-only

## TL;DR

**Question:** which of the backlog's open entries and the reviewed specs' `[L]` open questions can be closed by
reading the binary, by a table survey or by an offline sweep of our own models, with no game run? When it is done:
- every item of the ledger below carries one verdict: **answered** (a finding addendum with anchors, `[I]` or better),
  **stale** (already answered; the backlog entry struck with a pointer), **moved** (to a named plan, with the reason) or
  **not determinable statically** (the evidence for that, and the question stays open);
- the archivist's open table-doc entries are done, and the backlog holds no entry that is already answered;
- the specs' *Open questions* reflect the answers.

It takes **no harness slot**. It keeps the static lanes and the archivist busy while plans 0037 and 0038 hold the
harness.

## Context

- The backlog has 33 unstruck entries (survey 2026-10-16). Nine belong to plan 0037 (Phase 2 resume, Phase 3, the
  two contradiction entries that close with its reviews) and eight to plan 0038 (its Phase 2 leftovers, its tooling
  and the spec corrections its Phase 3 applies). This plan takes the rest. At least five of them look answered and
  were never struck.
- The reviewed specs list about 170 open questions. Plan 0038 sweeps `[I]` statements toward `[C]`; it does not
  touch `[L]` open questions. About 50 of those are marked as a static reading (a writer, a caller, a field meaning, a
  survey). The others need a run (plan 0038 or the plans below), two clients (plan 0044), owner play, a simulation
  phase, or are out of scope.
- Questions about rooms that are released and re-activated go to [plan 0040](0040-drlg-room-lifecycle.md); the act
  and quest fields of `rng/seeds` go to [plan 0042](0042-quests-travel.md); gold amounts go to
  [plan 0043](0043-items-economy.md).
- Method precedent: [plan 0015](done/0015-backlog-sweep.md), [plan 0020](done/0020-backlog-sweep-2.md) and
  [plan 0027](done/0027-backlog-sweep-3.md).

## The ledger

Each row is one item. `B` rows are backlog entries (named by date and lane), `Q` rows are spec open questions (named
by spec and topic). The batch column says which Phase 1 batch takes it.

| # | Item | Batch |
|---|---|---|
| B1 | 2026-10-11 reverser → reverser, drlg/0001 leftovers: DS1 (c) bits 14–15 and 30; the LvlSub side of DS1 (e) and the group `unk`; strike the collision-bit part (answered in drlg/0005). Path `action` is moved to the AI phase. | P1a |
| B2 | 2026-10-11 archivist → reverser, LvlTypes/LvlMaze: lvlmaze `Rooms`, `Rooms(N)`, `Rooms(H)`; what loading a `"0"` LvlTypes cell as a DT1 name does. `Merge` is answered (drlg/maze B6). | P1a |
| B3 | 2026-10-12 archivist → reverser, MonPreset/MonPlace preset monsters: check against monsters/0002 and 0003; strike if answered (MonPlace cases `0x11`–`0x20` are in plan 0038 H4b). | P1c |
| B4 | 2026-10-13 archivist → reverser, plan 0016 survey (f): which LvlPrest `Def`s each generator reaches, by caller. (b) is moved to the AI phase. | P1a |
| B5 | 2026-10-14 reverser → reverser, plan 0019 contradicted verdicts (c) and (e): check against items/0004; strike if answered. | P1c |
| B6 | 2026-10-15 archivist → reverser, the two harness-tool notes for `harness-play.md`: check; strike if present. | P1c |
| B7 | 2026-10-15 archivist → reverser, table-doc sweep follow-ups: (a) `tbl:` links in items/0007, items/0008, player/0001, items/0010; (b) items/0008's `ilvl` question from the CubeMain doc; (c) the States layout gaps (`immed`, `attred`, flag bit 10, the `rfred`/`rlred`/`rcred` bit order) from the field descriptor at `0x00618B7D`. Plan 0041 Phase 0 consumes (c). | P1b |
| B8 | 2026-10-15 spec-writer → reverser: how the client joins a rare item's two name texts (data/strings open question). | P1b |
| B9 | 2026-10-15 spec-writer → reverser: the two `Runeword95` rows (Passion, Patience) and the save reader (also items/sockets-runewords). | P1b |
| B10 | 2026-10-16 reverser → reverser: what `D2S_WriteHeader`'s stat pass writes for stats 6, 8 and 10 (the Hell `0x1FFFFF` life). | P1b |
| B11 | 2026-10-16 architect → reverser (H5c review): (a) drlg/0007 § 2, `RoomNeighboursEnsure` skips `WarpPairLink` for level 133; (b) can a stock outdoor border give a bit-2 wall cell without bit 7 next to a neighbour entry without flag `0x1` (the S1f precondition). | P1a |
| B12 | 2026-10-16 architect → reverser: the cursor branch of `sub_00558110_PlayerFindItemByCode` (items/0010 § 5). | P1b |
| A1 | 2026-10-16 reverser → archivist: the combat table readers of combat/0001 into DifficultyLevels, MonStats, ElemTypes, States and ItemStatCost; raise the matching `[L]` lines. | P0 |
| A2 | 2026-10-16 reverser → archivist: LvlPrest `Outdoors` has a reader (`sub_0066BA70_RoomIsOutdoors`); the LvlTypes `Act` reader sits in unreferenced code. | P0 |
| A3 | 2026-10-16 reverser → archivist: the run:2026-10-15-cube-saves addendum and the code-list tables shipped as `.bin`. | P0 |
| A4 | 2026-10-16 spec-writer → archivist: `tools/gate.py --also` given twice. | P0 |
| A5 | 2026-10-13 reverser → archivist (two entries, MonStats/Levels links and the `umon` count): both say "answered (architect, 2026-10-14)"; strike. | P0 |
| Q1 | data/excel: the auto-TC details (names, fields, item filter, entry probability) into a finding. | P1b |
| Q2 | data/excel: the TC post-pass `0x0065A2C0` and the group/level walk of `TC_GetByIndex`. | P1b |
| Q3 | data/excel: the u16 list at `0x0096CA78`. | P1b |
| Q4 | data/excel: monster references used as positions, classified over all readers of `g_pMonStats` (xref survey). | P1c |
| Q5 | drlg/collision: which neighbour bit-2 nodes `LOGIC_BarrierGridBuild` reads; the `LOGIC_EdgeMerge` coordinates. | P1a |
| Q6 | drlg/collision: the writers of bits 3 and 14. | P1a |
| Q7 | drlg/collision: monsters created dead and `deadCol`; who calls `UNIT_CollMark` in `SUnitCreate`; whether the post-create refresh runs on every path. | P1a |
| Q8 | drlg/maze: callers of `MazeRoomAdd` and `0x00670E70`; whether a stock seed reaches `MazeLevelPlace`'s fatal error (an offline seed sweep with `tools/drlg.py`). | P1a |
| Q9 | drlg/outdoor: the writer of adjacency node `+0xC`; the five functions with no caller. | P1a |
| Q10 | drlg/preset: who reads room flag `0x80000` (Outdoors); compare with A2. | P1a |
| Q11 | drlg/preset: the consumer of `Def` 108 and level 17 data `+0xF0`. | P1a |
| Q12 | drlg/room-tiles: the writer of bits `0x20000` and `0x40000` on neighbours' entries. | P1a |
| Q13 | drlg/room-tiles: a DS1 cell that is a border of one view and interior to another (an offline survey of the presets). | P1a |
| Q14 | drlg/warps: `WarpPairLink`'s second argument and `0x0066BDA0`; the units of the `Select*`, `ExitWalk*` and `Offset*` columns; whether a stock level can have more than 9 warp points (an offline sweep). | P1a |
| Q15 | rng/seeds: DRLG room `+0x60` bit 0; who sets `+0x28` bit `0x40000`; which creation paths pass non-zero seeds `+0x48`/`+0x4C`; the other initialiser sites (about 20 of 76 covered). | P1a |
| Q16 | items/affixes: re-read the staff-mods skill test at `0x005C1125`. | P1b |
| Q17 | items/cube: the search order of `InvPlaceItem` for the output cell; stat-delta ops 11–14 and 23–26. | P1b |
| Q18 | items/sockets-runewords: what the stale `kids[n]` word holds; flag bits 0, 2, 8, 14. | P1b |
| Q19 | items/quality: the owner of a summon's or a minion's kill (`monsterData+0x28`); which stock rows the § F overrides change (a survey). | P1b |
| Q20 | items/quest-drops: the `ilvl` of an object drop in a level with no Levels record; which `ItemCreateByQuality` case takes the Cow King's quality 0; `ITEMS_GetType` = 4 and flag `0x1000` in the service tests; whether the imbue's `+0x40` reaches the rare build; `0x0055CA40` (the holder test). | P1b |
| Q21 | items/tc: the meanings of monster `+0xC4` bit 17, `game+0x78`, the hellbovine bit and upgrade bits `0x04`/`0x10`; a forced quality on a gold or potion entry (objects' sparkle chest); the stale "superuniques has no table doc" line (it has one). | P1b |
| Q22 | items/uniques-sets: `nolimit` and auto-identification. | P1b |
| Q23 | items/vendors: why a cross-act change counts the leaving player in town; whether a gambled unique enters the made-uniques set; `NpcStoreRec` `+0x24..0x26`. | P1b |
| Q24 | objects: which code reads Objects `TrapProb`, `SpawnMax` and `Act` (the `InitFn` callee scan past depth 3). | P1b |
| Q25 | save/d2s: the affix and name id mappings (prefix rebasing, rare name 1/2, the low and superior index, automagic `class_affix`); client `+0x480`–`0x482`, status bit 1, the corpse record's first u32; which quest, waypoint and NPC slot is which difficulty (check against save/0002). | P1b |
| Q26 | monsters/spawn: which `SUnitCreate` callee makes the 6 and 15 unit-seed steps. | P1c |
| Q27 | monsters/special: what calls `MonMakeSpecial` from `0x00583050` (plan 0038 H4b found the Warping Shrine; name the path). | P1c |
| Q28 | hirelings: which `MonStatsInit` write sets the leftover stats 67, 68, 69, 100, 352 and the Rogue skill 336; what `Share`, `Head`/`Torso`/`Weapon`/`Shield` do; where the description text comes from. | P1c |
| Q29 | player/creation: what triggers `ExpGrantCapped`; whether part of the death loss comes back with the corpse; the path that sets status bit `0x20`. | P1c |

**Out of this plan:** the spec corrections already filed for plan 0038 Phase 3 and plan 0037 Phase 3; the `[L]`
questions that need a run (plan 0038, plans 0040–0043), two clients (plan 0044) or owner play; client presentation
(the `Outdoors` lighting, a unique's colour, fonts) and edited-data-only cases, which stay where they are.

## Phases

### Phase 0 — Table-doc entries
- **Owner skill:** archivist
- **What:** close A1–A5.
- **Outputs:** the table docs named in A1–A3, a dated addendum to run:2026-10-15-cube-saves in
  `docs/formats/experiments.md`, the `gate.py` fix (repeat `--also` accepted, or stated in `--help`), the backlog
  entries struck with pointers.
- **Done when:** A1–A5 are struck with pointers; every raised `[L]` → `[I]` line in A1 cites the combat/0001 anchor;
  `python3 -I tools/gate.py` is green, with `--full` if a layout changed.

### Phase 1 — Static readings, in three batches
- **Owner skill:** reverser (static; Ghidra and r2; no slot; at most one batch per Ghidra lane)
- **What:** read the code behind each ledger item of the batch and write the answer into the owning finding as a dated
  addendum (or a new section), with anchors and a tag; name new functions in `re/symbols.csv`.
  - **P1a, DRLG and seeds:** B1, B2, B4, B11, Q5–Q15 (16 items). Offline sweeps with our models (`tools/drlg.py`,
    `tools/outdoor_replay.py`, `tools/maze_replay.py`) are allowed for Q8, Q13 and Q14: they report how many seeds or
    presets they covered, and a "never reached" result from them is `[I]`, not a proof.
  - **P1b, items, data and saves:** B7–B10, B12, Q1–Q3, Q16–Q25 (20 items).
  - **P1c, monsters, hirelings, player, stale checks:** B3, B5, B6, Q4, Q26–Q29 (8 items).
- **Outputs:** addenda in `docs/findings/drlg/`, `items/`, `data/`, `save/`, `monsters/`, `hirelings/`, `player/` and
  `rng/`; `re/symbols.csv` rows; the backlog entries struck or annotated.
- **Done when:** every item of the batch has one of the four verdicts (answered, stale, moved, not determinable
  statically), recorded in the batch's log entry here as a table (item, verdict, anchor or reason); each answer is
  `[I]` or better with an address; each `stale` cites where the answer already was; each `moved` names the plan; a
  community lead used is registered in `docs/sources.md` and compared blind; the gate is green.

### Phase 2 — Specs
- **Owner skill:** spec-writer
- **What:** fold the answers into the owning specs: an answered open question leaves *Open questions* and becomes a
  tagged statement in the body (or a narrowed open question), a `not determinable statically` one gets its reason.
- **Outputs:** the specs touched by the ledger; tag counts updated in their headers; the research-map counts are the
  architect's (backlog).
- **Done when:** every answered ledger item is reflected in its spec, with the finding anchor; no spec gains an `[L]`
  in its body; the gate is green. Specs that plan 0038 Phase 3 also edits are merged one at a time, 0038's first when
  both are ready.

## Open questions

- **Stale entries addressed to other lanes.** The backlog rule is that the addressee strikes its entry. This plan
  gives each one to its addressee's phase (A5 to the archivist, B3, B5, B6 to the reverser), so no lane strikes
  another's entry.
- **Offline sweeps as evidence.** A model sweep shows what the model does; it is a second source only where the model
  is already `[C]` for that path (the replay tools are, for the generators they reproduce). The batch states this per
  use.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`. Built from the backlog and open-question
  surveys of 2026-10-16.
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038.
- **2026-10-16 — Phase 0 landed (archivist, `lane/p39a`, from `main` `7df5039`; review pending).** No game run, no
  Ghidra. A1–A5 all closed:

  | # | Verdict | Where |
  |---|---|---|
  | A1 | answered | § Combat readers in [DifficultyLevels](../tables/DifficultyLevels.md#combat-readers-plan-0037-phase-1-plan-0039-a1), [MonStats](../tables/MonStats.md#combat-readers-plan-0037-phase-1-plan-0039-a1), [States](../tables/States.md#combat-readers-plan-0037-phase-1-plan-0039-a1), [ItemStatCost](../tables/ItemStatCost.md#combat-readers-plan-0037-phase-1-plan-0039-a1); [ElemTypes § Code semantics](../tables/ElemTypes.md#code-semantics-plan-0037-phase-1-plan-0039-a1) |
  | A2 | answered | [LvlPrest](../tables/LvlPrest.md) `Outdoors` row and open question; [LvlTypes](../tables/LvlTypes.md) § Columns |
  | A3 | answered | [experiments § cube-saves addendum 2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3); the ten code-list docs and compcode; [tbl.md](../formats/tbl.md) and MonStats for `Lilith` |
  | A4 | answered | `tools/gate.py` (`--also` repeatable), `tools/test_gate.py` |
  | A5 | stale | both 2026-10-13 entries struck with pointers (already answered 2026-10-14) |

  - **A1.** Every line raised from `[L]` cites combat/0001 (section link plus `fn:` anchors). Lines that § 15
    (run:2026-10-16-combat, accepted) reproduces are `[C]`: `ResistPenalty`, the steal divisors,
    `HireableBossDamagePercent` 50/35 (Hell 25 `[I]`), MonStats `Crit`, States row 62, crushing blow and open wounds as
    handlers; the rest `[I]`. **Correction:** DifficultyLevels said `HireableBossDamagePercent` had no reader (plan 0025
    xref); the bullet now says why the walk missed it (`ReduceCtx+0x04`). `UniqueDamageBonus` "no reader" stands.
    Surprises: `DeathExpPenalty` already had a reader in player/0001 (added in passing); 20 of the 104 Phase 0 combat
    stats are not in § 12b (e): 6–10, 117 and 316/317 have readers elsewhere in the finding, and 81, 114, 137, 150,
    156, 159/160, 305–308, 358 were met by no reader (pierce is 333–336 only). The data agrees with the `itemeventfunc`
    reading (only stats 134–136 use funcs 14–16, both slots). MonStats' sequence-mode/`noRatio` open question is
    answered from § 12b (a), (b).
  - **A2.** `[I]`, citing drlg/0004 S4b row 27 and drlg/0002 S4b row 19. What the two callers of
    `DungeonRoomIsOutdoors` do with the answer stays open in LvlPrest.
  - **A3.** `sweep_s1b.py compile` rerun gives the S1b numbers (90 written, 88 identical, `cubemain` the probe's,
    `monstats` 2 bytes); a per-table compare adds that all 15 code lists, `compcode` and the four `*code.bin` were
    written byte-identical and all ship as `.bin` (d2exp, patch_d2 or both). No table doc said otherwise, so the
    "if a doc says otherwise" fix had nothing to fix; the docs now cite the addendum, and "a stock run never loads
    them" stays `[I]`. The `Lilith` cell's compiled 11154 is `[C]` in tbl.md and MonStats; tbl.md keeps its `[L]` on
    how the shipped file was made.
  - **A4.** `nargs="+", action="extend"`; the new test fails on the old parser. Gate green (`--full=excel_layout,combat`
    green after the table edits; no baseline changed).
- **2026-10-16 — Phase 0 reviewed (architect, on `lane/p39a` after merging `main` at S2c and the 0037 Phase 3 combat
  spec). Verdict: accept with fixes (applied in the review commit).** Anchors: `0x0057C0FE` (`mov esi,[esi+4]` then
  `mov eax,[esi+0x38]` after `MONSTATS_IsBoss`), `0x0057B00D`/`0x0057B012` (`DifficultyRec`, `+0x18`, `idiv`),
  `0x0057B2F1`/`0x0057B2F6` (`+0x14`), `0x0057C4B1`/`0x0057C4C1` (`+0x28`/`+0x2C`, `idiv`), `0x005A2709`/`0x005A2716`
  (`+0x3C`), `0x0056F19A` (`push 0x26`, `UNIT_HasStateFlag`), `sub_0066BA70` (type 1 → 1, type 2 → `flags & 0x80000`),
  the two `call 0x0061AA40` at `0x00460EEA`/`0x005DD9A1`, and `0x006429E0` with no `call`/`jmp` and no absolute
  pointer to it in `.text` (dead) all resolve in the pinned binary (objdump). Re-runs: `sweep_s1b.py compile` (same
  line), an independent code-list compare (20 of 20 identical), `tools/test_gate.py` (23 OK), `gate.py
  --full=excel_layout,combat` green, fast tier green.
  - **The `[C]` lines against combat/0001 § 15 and the combat spec:** `HireableBossDamagePercent` 50/35 (Hell `[I]`),
    the steal divisors for player attackers, MonStats `Crit`, States 62, crushing blow and open wounds hold. Fixes:
    `ResistPenalty` applies to every non-monster defender (players **and hirelings**, reductions B2), and its counts
    were misread: 138 and 208 are the classic Nightmare and Hell events, not "expansion and classic"; the steal
    bullet's "monster and hireling attackers are not divided" is `[I]` (delivery C1), split out of the `[C]`. One raise
    the lane missed: States flag bit 32 (`life`) in the monster tick is `[C]` (§ 15, 6 181 ticks, delivery E4); row 52
    `preventheal` stays `[I]` (no tick under it was asserted apart).
  - **`HireableBossDamagePercent` correction:** right, and consistent with monsters/0004 § 1 and monsters/stats; the
    struck open question that still said "no reader" for both columns now carries the correction, and the correction
    bullet links monsters/0004 § 1.
  - **"Not read" wording (ItemStatCost):** ruled a scope note, not a claim, so it carries no tag now ("combat/0001
    reads none of these"); "no reader" would need a full xref.
  - **Code-list `[C]` and the `[L]` in tbl.md:** the `[C]` stands (a run's written output byte-compared with the
    shipped file, plus the loader anchor); reproduced independently. tbl.md's `[L]` on how the shipped file was made
    stays: it is a statement about the producer's toolchain, outside what our binary can show, and a table doc may
    keep a lead.
  - **LvlPrest `Outdoors`:** narrowing, not striking, is right; the two callers are Q10 of Phase 1 (P1a), which
    already names A2.
  - **A1 basis:** every raised line cites combat/0001 by section and `fn:`; the `DeathExpPenalty` reader from
    player/0001 is in scope (a DifficultyLevels column, cited). Follow-up filed: the per-table code-list compare
    into `sweep_s1b.py` (archivist).
- **2026-10-16 — Phase 1 batch P1a done (reverser, `lane/p39r`, static).** 15 ledger items (B1, B2, B4, B11, Q5–Q15). No
  game run; Ghidra on the lane's copy; offline sweeps over kept logs and the `tools/drlg.py` models (scratch scripts,
  not kept). B11 (b) first, for the S1f judgement: **no stock border reaches the merge remap.** 27 symbols added.

  | Item | Verdict | Anchor or reason |
  |---|---|---|
  | B1 | answered (part stale, part moved) | bits 14–15 are the top of the sub-index byte, bit 30 has no reader, `LvlSub` group `unk` is `ApplyAll`'s variant count (unreached), no code views the substitution layer: [drlg/0001 § P1a](../findings/drlg/0001-ds1-dt1-readers.md#plan-0039-batch-p1a-2026-10-16) `[I]`; collision bits stale (drlg/0005); path `action` moved to the AI phase |
  | B2 | answered in part; rest stale | a `"0"` DT1 load logs an open error and relocates an empty buffer: outcome **not determinable statically**; no checked stock room has such a bit (drlg/0001 § P1a) `[I]`; `Rooms`/`Merge` stale (drlg/0006 § Answer) |
  | B4 | answered | three callers of `PresetInstanceCreate`; the logged `Def`s by caller split the 93 ambiguous records 30 maze / 60 outdoor / 1 both / 2 never logged (783, 795): [drlg/0004 § P1a](../findings/drlg/0004-preset-units.md#plan-0039-batch-p1a-2026-10-16) `[C]` |
  | B11 (a) | answered | `RoomNeighboursEnsure` skips `WarpPairLink` for level 133 (0x0066C39B): [drlg/0007 § P1a](../findings/drlg/0007-warps.md#plan-0039-batch-p1a-2026-10-16) `[I]` |
  | B11 (b) | answered: no | every stock wall and shadow cell has bit 7 (2077 DS1s, `[C]` data), so every kind-0 entry has flag `0x1` and wall/shadow merges return at 0x0066E754; the H5c logs agree merge by merge (2203 of 2203): [drlg/0002 § P1a](../findings/drlg/0002-room-build-draws.md#plan-0039-batch-p1a-2026-10-16) `[I]` + `[C]` |
  | Q5 | stale | answered in drlg/0005 § Plan 0038 batch S4a |
  | Q6 | answered | no writer of grid bits 3 and 14 (tiles: no DT1 bit 3; 103 writer call sites; `UNIT_GetCollMask`): [drlg/0005 § P1a](../findings/drlg/0005-collision.md#plan-0039-batch-p1a-2026-10-16) `[I]` |
  | Q7 | answered | created-dead monsters honour `deadCol` (0x00555481); the two marks are `PATH_DynamicCreate` and `MonSetMode`; every type-1 creation is in `MonSpawnTry` or `MERC_Create`, both run `MonAlignSet` (drlg/0005 § P1a) `[I]` |
  | Q8 | answered | `MazeRoomAdd`/`0x00670E70` dead code; sweep of 408 000 maze builds: the fatal only with equal tomb fields, which the act draw excludes (0x00642ED7): [drlg/0006 § P1a](../findings/drlg/0006-maze.md#plan-0039-batch-p1a-2026-10-16) `[I]` |
  | Q9 | answered | node `+0xC` written once, to 0 (0x0066B7D5); the five functions are dead code: [drlg/0008 § P1a](../findings/drlg/0008-outdoor.md#plan-0039-batch-p1a-2026-10-16) `[I]` |
  | Q10 | stale, consumers added | reader found at plan 0038 S4b; its client and server callers named in drlg/0004 § P1a `[I]` |
  | Q11 | answered | the `+0xF0` points (level 17, main 10, sub 23–27; trigger corrected) have no live reader (getter chain unreferenced): drlg/0004 § P1a `[I]` |
  | Q12 | answered | `0x40000` = added to the client automap (0x00457D04); `0x20000` = client draw lists: drlg/0002 § P1a `[I]` |
  | Q13 | stale | drlg/0004 § Shared DS1 buffers (no shipped DS1 is cut two ways) |
  | Q14 | answered | `WarpPairLink`'s first stack argument has no effect; `0x0066BDA0` appends to the source room's near list (and the warp node is on the source room); `Offset*`/`ExitWalk*` subtiles, `Select*` pixels; > 9 points not in stock data (1452 logged builds): drlg/0007 § P1a `[I]` |
  | Q15 | answered (residue noted) | `+0x28` `0x40000` = client act copy `[C]`; `+0x60` bit 0 = populated, kept across a release `[C]`; seeds `+0x48`/`+0x4C` only from the version-`0x47` item list `[I]`; the 76 initialiser functions classified; the skill and missile re-seeds of units stay unread (a skills subject): [rng/0002 § P1a](../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16) |

  Surprises: drlg/warps F1's "marked … gets a warp node" describes the wrong room (the node is on the source room, the
  destination joins the source's near list); drlg/0004's level-17 points were read as "orientation 10" (main index 10,
  gated by level, not `Def`). Spec notes for Phase 2 and the review request are in the backlog.
- **2026-10-16 — Phase 1 batch P1a reviewed (architect, on `lane/p39r` after merging `main` at the plan 0041 Phase 0
  review). Verdict: accept with fixes (applied in the review commit).**
  - **B11 (b), spot-checked.** An independent scan (the review's own script over `tools/ds1.py parse`, not the lane's)
    of the 2043 `LvlPrest` `File1..6` DS1s gives 152 587 wall cells (bit 0) and 13 279 shadow cells (bit 27), none
    without bit 7. It also finds no non-zero wall cell without bit 0 and no floor cell with bit 0 or 27. For the 34
    `LvlSub` DS1s it gives 2 492 + 26 walls and 216 + 91 shadows, all with bit 7; the second figures are `trees.ds1`,
    whose layers parse whole when padded. These are the lane's 2 518 and 307. The data claim is `[C]`. Disassembly
    (objdump): `0x0066E747` loads `g_Bit2OrientRow[o]`; `0x0066E754` `test al,1` on `[E+0x14]`. With the flag set,
    an entry of orientation 8 or 9 goes to `call 0x66DB20` (`RoomTileSetFlags`) then `ret 0x18`, and any other
    orientation jumps to the shared epilogue `0x0066E933`. The bit-7 test `test byte [ebp+0x14],0x80` is at
    `0x0066E781`. The code reading holds.
  - **One gap, fixed.** The bullet said "returns at its flag test", but the 8/9 case first calls `RoomTileSetFlags`
    (the reached flag-`0x1` exit; the spec has it). It also covered floors only through row −1. Floors without flag
    `0x1` could still meet the `E.o ∈ {8, 9}` edge test or an orientation-3 test unless E.o is known. Added `[I]`: a
    floor scans only kind-1 entries (room-tiles step 9), every kind-1 entry is an orientation-0 floor, and row −1
    writes 0 back. With o = E.o = 0, none of those tests fires.
  - **Other anchors (objdump):** `0x0066C39B` `cmp [eax+0x1D0],0x85` (B11 a); `0x0066FC2A` `GridCellOp` with op 3
    (`LvlSubStamp`'s wall `set`); `0x0067D391` the `0x40002` floor `set`; `0x0067D4F2` `GridBorderOp` with `0x4`;
    `0x00457CF9`/`0x00457D04` `test`/`or eax,0x40000` then the store to `[esi+0x14]` (Q12). Also `0x004DDE86`
    `or [eax+0x14],0x20000`; `0x0066B7D5` `mov [eax+0xC],0` (Q9); `0x00555481` `MonStats2FlagTest(class, 0x13)`
    (Q7); `0x00666DE6` `cmp [eax+0x1D0],0x11` and `0x006669F3` `cmp al,0xA` (Q11); `0x0066B47C` `test byte
    [esi+4],0x10` → `or [edi+0x28],0x40000` (Q15); `0x006194F5` `push 1` (client copy). `0x0061AD10` has no `call`
    or `jmp` in `.text` and no little-endian pointer anywhere in the file. In `WarpPairRoomFind`, `0x0066BF0C`–`0x0066BF1C`
    calls `RoomNearListAppend` with `EAX` = `EDI` = `srcRoom`, then `RoomWarpNodeAdd(D, m)`. That function prepends
    the node to `[edi+0x4C]` with `LevelWarpRec(…, 'b')`. So the drlg/warps F1 correction holds. All resolve, and all
    27 new symbols are `I`.
  - **Tags.** The `[C]`s have named second sources: B4 (xrefs and 89 357 `PIC` lines), the Q15 `+0x28` and `+0x60`
    rules (code and two runs), the B11 (b) data survey and the H5c merge counts. The Q8 and Q14 sweeps stay `[I]` as
    the plan requires. No `[L]` is raised; findings keep two leads where they were.
  - **Ruling on B11 (b), S1f and the 11 room-tiles rows.** The answer settles H5c ruling 4's precondition. The 11
    merge rows (room-tiles 4, 14, 15, 28, 30, 37) move from a-run shortfall to **d-edit** and leave the S1f candidates
    (42 → 31), recorded in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews). Emulating
    a path that stock data cannot enter adds no stock evidence. The S1e lane can still propose it as a modding aid,
    but not as an `[I]` → `[C]` route for these rows. The spec states the unreachability as `[I]`, with the `[C]` data
    survey and the `[C]` log counts as its basis. The pseudocode of 9c stays as the `[I]` code reading for edited data,
    and the *Open questions* entry on the unreached branches is closed with that pointer. Routed to the spec-writer
    (backlog, the P1a Phase 2 entry, item (a)).
  - **Q15 residue.** The skill and missile re-seed sites are moved to Simulation phase (3) (skills and missiles) of the
    research map, which now names them. That gives the "moved" half a destination.
  - **Bookkeeping.** P1a covers 15 items; the Phase 1 text said 16 (B11 counted twice), and the text is left as is. B1,
    B2 and B4 are struck correctly. B11's (a)(b) annotation is merged into the H5c review entry. Gate green.
- **2026-10-17 — archivist follow-ups (`lane/arc4`).** Two backlog entries of this plan cleared: the P1a format and
  table items ([ds1.md](../formats/ds1.md) cell bits 14–15 and 30 `[I]`, the wall/shadow bit-7 survey `[C]`, the
  group `unk` as `ApplyAll`'s variant count `[I]`; [LvlPrest](../tables/LvlPrest.md) the 93 "maze or outdoor" records
  by logged caller `[C]`; [LvlWarp](../tables/LvlWarp.md) column units `[I]`), and the Phase 0 review's per-table
  compare (`sweep_s1b.py compile` now prints identical/differs for the 15 code lists, `compcode` and the four pools,
  key `codetable_identical` = 20; cited in [formats/experiments](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3)).
  No row's verdict changes.
