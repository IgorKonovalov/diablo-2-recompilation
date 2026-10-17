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
- **2026-10-17 — Phase 1 batch P1b done (reverser, `lane/p39b`, static).** 18 ledger items (B7–B10, B12, Q1–Q3,
  Q16–Q25; the Phase 1 text counts 20). No game run; Ghidra on the lane's copy (`ghidra-p39b`), objdump scans of the whole image, table surveys and
  a re-read of 14 kept level-up logs (sha256 checked against their manifest). B7 (c) was not consumed by plan 0041
  Phase 0 (it listed the gaps and waited for this batch), so it is answered here. 32 symbols added (31 `func`, 1 `data`,
  all `I`). New statements: 8 `[C]` (B10 from code and logs; the rest data checks) and about 50 `[I]`; no `[L]` raised or
  added.

  | Item | Verdict | Anchor or reason |
  |---|---|---|
  | B7 (a) | stale | every `tbl:` table of items/0007, items/0008, player/0001, items/0010 has its doc (gate E4) |
  | B7 (b) | stale | CubeMain § Output record answers it; items/0008's open question struck: [items/0008 § P1b](../findings/items/0008-cube.md#plan-0039-batch-p1b-2026-10-17) |
  | B7 (c) | answered | `STATES_Load`'s descriptor: `attred` = bit 10, `immed` not compiled, `rfred`/`rcred`/`rlred` = 26/27/28: [data/0001 § P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17) `[I]` |
  | B8 | answered | `RareFormat` (1718) with `name1` as `%0`, `name2` as `%1`; `%0 %1` in English: [data/0003 § P1b](../findings/data/0003-string-tables.md#plan-0039-batch-p1b-2026-10-17) `[I]` + `[C]` data |
  | B9 | answered | the reader stores the index unmapped at `ItemData+0x38`, the writer re-runs `RUNEWORD_Match`; *Patience* never matches: [items/0007 § P1b](../findings/items/0007-sockets-runewords.md#plan-0039-batch-p1b-2026-10-17) `[I]` + `[C]` data |
  | B10 | answered | the `CSvBits` clamp (21 bits) on a base **above** `0x1FFFFF`; 364 of 364 written entries predicted: [save/0001 § P1b](../findings/save/0001-d2s-io.md#plan-0039-batch-p1b-2026-10-17) `[C]` |
  | B12 | answered | the cursor branch tests `quest` and stat 356 only; a missing stat is 0; a cursor-held cube counts in Normal only: [items/0010 § P1b](../findings/items/0010-quest-drops.md#plan-0039-batch-p1b-2026-10-17) `[I]` |
  | Q1 | stale | items/0001 § 9 (`[I]`) and data/0001 § S1b (G2 `[C]`) |
  | Q2 | stale | the post-pass is `TC_BuildChestTable`; the walk is items/0001 § 4 (`[C]`); re-read agrees |
  | Q3 | answered | the classic item index map of the version-`0x47` item reader (361 version-0 rows): [data/0001 § P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17) `[I]` |
  | Q16 | stale | items/0005 § Plan 0038 batch S2b (re-read at 0x005C1121–0x005C1165 here, agrees) |
  | Q17 | answered (cell stale) | `UnitStatDelta` = stat − base stat: [items/0008 § P1b](../findings/items/0008-cube.md#plan-0039-batch-p1b-2026-10-17) `[I]`; the output cell is S2c cube 45 |
  | Q18 | answered in part | flag bits 0/2/8/14 = update pending, use in progress, broken, requirements not met `[I]`; `kids[n]` **not determinable statically** (earlier stack contents): [items/0007 § P1b](../findings/items/0007-sockets-runewords.md#plan-0039-batch-p1b-2026-10-17) |
  | Q19 | answered (b stale) | a minion's owner is its boss (`UniqueMinions`), a boss its own: [items/0002 § P1b](../findings/items/0002-quality-roll.md#plan-0039-batch-p1b-2026-10-17) `[I]`; the overrides survey is items/0004 § 10, counts re-derived and the "two quivers" corrected |
  | Q20 | answered | object drop ilvl 1 with no `Levels` record; Cow King quality 0 → case 2 (`[C]` outcome); type 4 = `gold`; flag `0x1000` = monster equipment; `+0x40` reaches no builder; `0x0055CA40` = carry-one / quest duplicate test: [items/0010 § P1b](../findings/items/0010-quest-drops.md#plan-0039-batch-p1b-2026-10-17) `[I]` |
  | Q21 | answered (parts stale) | bit 17 = no death drop and its writers; `game+0x78` = item version; bits `0x04`/`0x10` = forced ethereal / sockets; forced quality on gold/potions → 2: [items/0001 § P1b](../findings/items/0001-tc-resolution.md#plan-0039-batch-p1b-2026-10-17) `[I]`; cow bit (items/0004) and SuperUniques doc stale |
  | Q22 | answered | quest uniques identified by `ItemInitStats`; `nolimit` plays no part: [items/0004 § P1b](../findings/items/0004-uniques-sets.md#plan-0039-batch-p1b-2026-10-17) `[I]` + `[C]` data |
  | Q23 | answered in part, rest moved | the act change counts before the room changes; a gambled unique enters the made set: [items/0009 § P1b](../findings/items/0009-vendors.md#plan-0039-batch-p1b-2026-10-17) `[I]`; `NpcStoreRec` `+0x24..+0x26` writers read, no reader found, **moved** to plan 0043 Phase 1 |
  | Q24 | answered in part | `SpawnMax`, `Act`: no reader in the image (operand scan); `TrapProb`: none among the 89 record fetchers; a kept record pointer stays open: [objects/0001 § P1b](../findings/objects/0001-object-population.md#plan-0039-batch-p1b-2026-10-17) `[I]` |
  | Q25 | answered in part (ids, quest/wp slots stale) | NPC slot *d* = difficulty *d*; corpse u32 uninitialised and unread `[I]`; client `+0x480..+0x482` **not determinable statically** (host bytes); status bit 1 **moved** (client presentation, out of plan): [save/0001 § P1b](../findings/save/0001-d2s-io.md#plan-0039-batch-p1b-2026-10-17) |

  Surprises: the B10 backlog premise was reversed (the base life was above the clamp, not below); monster minions *do*
  have an owner record (their boss), against items/0002's expectation; items/0001's "upgrade bits" are forced ethereal
  and forced sockets, and `ce=` can have no effect at all (classic only, where the ethereal roll does not run);
  `immed` is not compiled at all. Spec notes for Phase 2, the archivist entry, a `d2sio.py` follow-up, the plan 0043
  hand-off and the review request are in the backlog.
- **2026-10-17 — Phase 1 batch P1b reviewed (architect, on `lane/p39b` after merging `main` at `cc59597`). Verdict:
  accept with fixes (applied in the review commit).**
  - **Anchors (objdump), 14 checked, 13 hold.** B10: `D2S_WriteStats` 0x00569605 `mov cl,[edi+0xA]`, `jbe` on 0,
    `cmp cl,0x20; jae` past the clamp, the unsigned branch 0x0056964D–0x00569667 clamps to `[0, 2^bits − 1]` (negative
    to 0), the signed branch to `[−2^(b−1), 2^(b−1) − 1]`. B7 (c): see below. Q3: 0x006334E4 stores the list at
    `0x0096CA78`, 0x00633510 `cmp word [rec+0xF6], 0` with stride `0x1A8`; `0x006335A0` bounds and the fatal NULL test;
    its one `call` at 0x00533310. Q25: 0x0057236C–0x00572370 `[pdata + 4·game+0x6D + 0x60]`; `D2S_WriteCorpses` frame
    `0x2C`, `[ebp−0x2C]` read at 0x0056994E and accessed nowhere else; 0x0056A343 calls the host-byte setter. B12:
    0x0055814F `quest`, 0x0055815E stat `0x164`, `jle` on `Game+0x6D`, no `+0x12B` test on the cursor branch, the
    inventory branch tests `+0x12B` at 0x005581BC. B9: 0x0063087E `RUNEWORD_Match` → `+0x82` or `0xFFFF`; 0x0062D1EA
    stores the read bits at `ItemData+0x38`. B8: 0x0048C8AA `0x6B6`, arguments `[ebp−0x17D8]`, `[ebp−0xFD8]`, NULL.
    Q19: 26 `call 0x58F030` in `.text`; 0x005A0C94–0x005A0CA6 as stated. Q21 bit 17: both readers (0x00542031,
    0x005A6861, load then `shr 0x11`) hold, no `test`/byte form elsewhere; **the writers do not**: `or [reg+0xC4],
    0x20000` occurs 21 times, not five.
  - **B10 log check re-run** (the review's own script over `tools/d2s.py`, under `systemd-run … MemoryMax=4G python3
    -I`): the 14 logs match their manifest; 26 writes, 364 entries; with the code's rule (no clamp for `CSvBits` 0 or
    ≥ 32) every entry is predicted, and the 10 that differ from the base are the stated ones (stat 6 in `LvBarD`/`LvPalD`,
    stat 8 in the three Sorceress logs, two writes each). The 6 entries a naive 32-bit clamp gets wrong are stat 13
    (experience, `CSvBits` 32, a negative s32 base), which the code does not clamp. `[C]` holds.
  - **Ruling 1, B10 `[C]`: accepted.** Code plus 364 logged entries, reproduced here; reversing the backlog's "the base
    is lower" is correct (the base carries the item bonuses). Precision added: the range is `[0, 2^bits − 1]` and
    applies for 0 < `CSvBits` < 32 (§ 4 already said so).
  - **Ruling 2, B7 (c) without a kept script: an objdump re-check is enough.** The review replayed the stores
    independently (its own 60-line scratch script: register constants plus `[ebp−X]` writes from 0x00618100 to the
    `DATATBLS_LoadTable` call): 70 entries ending in `end`, `attred` entry 12 = type `0x1A`, bit `0xA`, field `+0x10`,
    `group` type 3 at `+0x1E`, `rfred`/`rcred`/`rlred` = `0x1A`/`0x1B`/`0x1C`, no `immed` entry. Two independent replays
    agreeing is what a kept tool would give; `[I]` stays (one kind of evidence). No tool is required; if plan 0041 or a
    later table phase needs more stack-built descriptors, the archivist may promote a generic dumper then.
  - **Ruling 3, the two "not determinable statically" verdicts: accepted.** `kids[n]` is stack residue of whatever ran
    before at that depth; only a run or a declared-stack emulation can say more, and the narrowing `[I]` is fair. For
    client `+0x480..+0x482` the verdict stands for the *meaning*, but for a reimplementer the behaviour is settled:
    the spec should state, `[I]`, that the bytes are read from header `0x0CF`/the join record, carried, written back and
    handed to the host callback in a ladder game, and read by no game rule. That is a body statement, not an open
    question (backlog P2 entry (k) already says "host bytes").
  - **Ruling 4, the two moves: accepted, one re-labelled.** `NpcStoreRec` `+0x24..+0x26` → plan 0043 Phase 1 is a
    proper move (named plan, backlog entry with the writer table). Status bit 1 names no plan, so it is not "moved" but
    *out of this plan* (client presentation, as § Context's exclusion list says); the d2s spec keeps it as an open
    question narrowed to the `[I]` facts (set only by the creation screen, `D2S_CheckStatus` never tests it).
  - **Ruling 5, Q24 at `[I]`: accepted.** The review re-ran the whole-image scans: no operand with a `+0xC3`
    displacement at all, and the only byte operand at `+0x170` is the stack array at 0x00694D9E. Wider reads at
    `+0x16C..+0x170` exist (30 non-stack word/dword operands, other structures by context), so "no reader" is an
    operand-scan negative and stays `[I]`, with the computed-address caveat the finding already states.
  - **Ruling 6, Q19 with 20 sites unfollowed: accepted for the question asked, with a fix.** The answer needed was
    whether minions have an owner; that is shown. Fixes: superunique minions reach `UniqueMinions` through
    `SpecialModsApply` (0x005A4B6C–0x005A4B8E → 0x005A2135), which the finding asserted without the path; 0x005A4DD8
    is one record's hard-coded tail, not every superunique (the general self-owner is `SpecialMonPlace`); MonStats party
    minions with `SetBoss` were already linked in monsters/0002 (`[C]`), so `MinionsSpawn`'s three sites are not
    "unfollowed". 17 sites remain unread; follow-up filed (backlog), not blocking.
  - **Fix, Q21 bit 17 (blocking-class error, fixed here).** The finding said "five" writers; there are 21. The five
    read stay as examples, the 16 unread ones are listed (`MonSpawnTry`, three quest drops, 12 skill-code sites), and
    the meaning rests on the two readers. The P2 backlog entry (h) is reworded so the spec does not present the five as
    the full set. Follow-up filed.
  - **Tags.** The other `[C]`s are data checks with named tables (`version` counts, `complete`, `RareFormat`, the
    `unique`/`quest`/`questdiffcheck` survey, the imbue survey) or a run outcome (Cow King `vps` quality 2); all fine.
    No `[L]` raised. Symbols: 32 added, all `I`, no duplicate address or name after the merge (checked; gate agrees).
  - **Count.** P1b has 18 items (B7–B10 = 4, B12, Q1–Q3 = 3, Q16–Q25 = 10); the Phase 1 text's "20" is wrong, as P1a's
    "16" was. Text left as is; P1c's "8" is right.
  - **Phase 2 readiness.** P2 can start now on the P1a and P1b items (both reviewed). Two specs also take P1c items:
    data/excel (Q4) and possibly items/uniques-sets (B5's check against items/0004). Fold those two last, or after P1c,
    so each is edited once; the 0038-first merge rule of Phase 2 still applies.
- **2026-10-17 — archivist follow-ups (`lane/arc4`).** Two backlog entries of this plan cleared: the P1a format and
  table items ([ds1.md](../formats/ds1.md) cell bits 14–15 and 30 `[I]`, the wall/shadow bit-7 survey `[C]`, the
  group `unk` as `ApplyAll`'s variant count `[I]`; [LvlPrest](../tables/LvlPrest.md) the 93 "maze or outdoor" records
  by logged caller `[C]`; [LvlWarp](../tables/LvlWarp.md) column units `[I]`), and the Phase 0 review's per-table
  compare (`sweep_s1b.py compile` now prints identical/differs for the 15 code lists, `compcode` and the four pools,
  key `codetable_identical` = 20; cited in [formats/experiments](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3)).
  No row's verdict changes.
- **2026-10-17 — `lane/arc4` reviewed (architect, after merging `main` at `8d03310`). Verdict: accept with fixes**
  (applied in the review commit). Nine entries checked against their sources: `ToHitCalc` `[I]` (data/calc § G),
  `ToHitFactor` `[C]` and Hell 25 `[C]` (combat/0001 § 15, run:2026-10-16-combat, 1 974 attacks and 33 events), the
  bit-7 survey and the 93 LvlPrest records `[C]` (drlg/0002, drlg/0004 § P1a), LvlWarp units `[I]` (drlg/0007 § P1a),
  `firstPrefix` 747 `[C]` (save/0001 S1a row 101), `+0x025` `[C]` (monsters/0001 pool 9) all hold. Data re-counted:
  `SaveMonsters` 0 for 7 levels, `restore` 698/18/18 with the named rows, Hireling `Version` 60 × 0 and 60 × 100,
  DifficultyLevels 50/35/25. `sweep_s1b.py compile` re-run: `codetable_identical=20`, `bad=0`. The `economy`
  baseline adds six keys and changes none. **Sets ruling:** recording the skills-then-states order as a tool limit is
  accepted (the entry offered it; a property-based order now would be a guess); plan 0041 Phase 1 (e) now names the
  archivist as the consumer of its answer. Fixes: [ds1.md](../formats/ds1.md) said bits 18–19 have no mapping and
  `CellBits` maps 16/17 only, but drlg/0001 § Per-cell decision maps the 18–19 value field to `(v+1)·0x4000` (the
  layer index ORed in at load); table, bullet and *Unknown fields* row corrected, the runtime-flag cells tagged `[I]`.
  [Levels](../tables/Levels.md): level 0 is the null level, not a town. Gate fast tier and `--full=economy,excel_layout`
  green. Follow-up to the reverser for the two finding wordings these came from.
- **2026-10-17, `lane/w1` review (architect): accept.** Findings W1 104 → 0, `main` `f10dca8` merged first (no
  conflict; the S1e and p39b sections add no W1; specs 15, filed to the spec-writer). Sampled more than 60 of the added anchors
  across 20 files (save/0001 22, items/0007 14, the six experiments files 16, data, drlg, rng, monsters, items/0001,
  0002, 0010 and the rest): every `fn:`/`data:` resolves (gate E1), every address is one the same finding already gives that code
  in its own section (save/0001 §§ 7–8 ranges, items/0007 § 6, items/0002 L65, items/0001 `TC_GetByIndex`), every
  `run:` in an experiments file is the enclosing record's own id, and the save/0001 corpus rows cite the writer or
  reader plus the runs whose writes they count (8 + 192 = 200 for rows 24, 45, 86). No anchor chosen for the gate
  alone. The two open-question corrections match their sections: drlg/0006 tomb multipliers are H5e C1 `[C]`;
  drlg/0002's 1 280 `(10,0,0)` fallbacks are § S4a's, over the collision and objects logs (none in roomk).
  `tbl:MonUMod.txt:constants` is documented (MonUMod.md, row 0 `[C]`). The four tag mentions reworded are status
  lines and "would take to `[C]`" phrases, not claims. arc4 wordings (a) and (b) done. Follow-up (reverser): drlg/0002
  rows 9 and 20 stay `[I]` on "no stock key lacks a candidate", which the same S4a fallbacks contradict.

- **2026-10-17 — Phase 2 landed for P1a and P1b (spec-writer, `lane/p39s`, from `main` `8d03310`; review pending).**
  Folded the backlog's P1a entry (its (b) and (g); (a), (c)–(f) were applied by plan 0038 Phase 3 rounds 2 and 3) and
  the P1b entry, with the review's amendments to (f) and (h). No game run, no Ghidra.

  | Spec | Items | {C, I, L} old → new |
  |---|---|---|
  | drlg/collision | P1a (b): Q6, Q7; Q5's S4a answer as G2 text | {110, 55, 12} → {110, 60, 9} |
  | rng/seeds | P1a (g): Q15 | {76, 7, 6} → {78, 9, 4} |
  | data/strings | B8 | {59, 39, 3} → {60, 42, 3} |
  | items/affixes | Q16 (stale, S2b) | {112, 45, 4} → {112, 46, 4} |
  | items/cube | Q17 (cell from S2c cube 45) | {118, 82, 6} → {119, 82, 4} |
  | items/sockets-runewords | B9, Q18 | {79, 77, 9} → {80, 83, 7} |
  | items/quality | Q19 | {63, 37, 4} → {64, 38, 3} |
  | items/quest-drops | B12, Q20 | {80, 82, 6} → {81, 88, 3} |
  | items/tc | Q21 | {45, 77, 8} → {45, 81, 7} |
  | items/vendors | Q23 (and the gambled-unique half of Q22's entry) | {70, 37, 4} → {70, 39, 2} |
  | objects | Q24; Q21's forced-quality pointer | {136, 69, 5} → {136, 71, 4} |
  | save/d2s | B10, Q25 | {88, 144, 5} → {90, 150, 3} |

  - **Corrected:** save/d2s F1's "no clamp hit" (B10: the 21-bit clamp is hit by high life and mana, `[C]`);
    sockets-runewords now states that *Patience* never matches (`[C]` data); items/quality's "two quivers" are the
    base-less types `mboq`/`mxbq`; items/tc's "upgrade bits" are forced ethereal and forced sockets.
  - **Narrowed, not closed:** items/quality (17 `MonSetOwner` sites unfollowed), items/tc (16 of the 21 bit-17 writers),
    objects (`TrapProb` through a kept record pointer), data/strings (the `%n` substitution), rng/seeds (skill and
    missile re-seeds, moved to Simulation phase (3)), sockets-runewords (`kids[n]`, not determinable statically), save/d2s
    (status bit 1, client presentation), items/vendors (`NpcStoreRec` `+0x24..+0x26`, moved to plan 0043).
  - **Held:** data/excel (P1b (a): Q1, Q2 stale, Q3) and items/uniques-sets (Q22: quest uniques identified by
    `ItemInitStats`, `nolimit`), because P1c also edits them (Q4, B5); each is folded once after the P1c review.
  - Research-map rows of the twelve specs updated. Backlog: the P1a entry struck, the P1b entry annotated (done in part,
    the held items named); review request and a W4 wiki follow-up (15 `based_on` dates) filed. Gate green.
- **2026-10-17 — Phase 2 (P1a and P1b folds) reviewed (architect, on `lane/p39s` after merging `main` at `f10dca8`).
  Verdict: accept with fixes (applied in the review commit).**
  - **Tags against the findings.** Every new `[C]` has its accepted source at the same strength: rng/seeds `+0x28`
    `0x40000` and `+0x60` bit 0 (Q15, code plus run:2026-10-16-sweep-roomk, P1a review); data/strings entry 1718 =
    `%0 %1` (data); items/cube G4's cell (S2c cube 45, S2c review ruling 3); sockets-runewords *Patience* (`complete`
    data); items/quality's override survey (data, items/0002 Q19 (b)); quest-drops' no-unique-imbue check (data);
    save/d2s's 21-bit clamp (B10, P1b ruling 1) and the merged affix ids (items/0005 § 1 `[C]`, save side S1a rows 87 and
    101). Every new `[I]` matches a P1a/P1b `[I]` reading; none is stronger than its finding. The two P1b amendments are
    honoured (quality M3 with `SetBoss` minions and the 17 unfollowed sites as a narrowed `[L]`; tc B1 with "21
    writers, five read as examples"), and ruling 3's host bytes are a body `[I]`, ruling 4's status bit 1 an
    out-of-plan `[L]`.
  - **Counts.** All twelve front matters recounted with the review's own script (raw `[C]`/`[I]`/`[L]` after the front
    matter): all match the request's new figures, and the per-spec deltas match the diff statement by statement. No
    `[L]` above *Open questions* in any of the twelve.
  - **Anchors (objdump), 8 checked, all hold.** `0x0055A5E3` `mov cx,[eax+0x78]` stored to the record (tc H7);
    `0x00556D24` `test byte [ebx+0x80],0x4` (forced ethereal); `0x00556C1F`–`0x00556C24` `test cl,0x10; je; xor eax,eax`
    after the `Range(100)` call (forced sockets); `0x0053AF40` `call TownLevelLeave` before `0x0053AF4F` `call
    PlayerChangeAct`, and `0x00538191` the per-frame call (vendors C2); `0x00649E9A` `UNIT_CollMark` under the room-arg
    test and `0x005A7CB1` after `0x005541B0` returns 0 (collision, the two marks); `0x00625560`: stat list `+0x5C`, 0
    with none, `StatListGetStat` − `StatListGetBaseStat` (cube `UnitStatDelta`); `0x0066B4D7` the `+0x60` store in
    `RoomReleaseWrap` (seeds).
  - **Point (1), the two plan 0038 items.** *items/cube G4's output cell `[C]`: accepted.* cube 45 is **raised** in
    items/0008 § Plan 0038 batch S2c and the S2c review accepted the placement model (ruling 3, `InvPlaceItem` I → C,
    scope: the player branch on an empty grid, which the spec keeps). Closing the open question needed a statement, and
    stating it at `[I]` against an accepted `[C]` would understate it. *drlg/collision § G2 edge points at `[I]`:
    accepted.* S4a rows 43 and 44 are raised (`[C]`) in drlg/0005 and accepted, but the drlg/collision cluster still
    waits on H5b and H5d, so the raise of the G2 statements (barriers, merge, and these edge points) stays with plan
    0038 Phase 3. The asymmetry is acceptable: one pre-existing statement closed on an accepted raise, against a new
    text that leaves the raise where it is planned. Plan 0038 Phase 3 must count cube 45 as already applied and raise
    the G2 edge-point statement with rows 43–44 (note in the plan 0038 log).
  - **Point (2), the save/d2s F1 contradiction: accepted.** F1's run sentence now limits "code only" to the param
    branch, and the clamp `[C]` gives the code range, the 364 entries and experience's 32-bit exemption, as the B10
    finding does. Fixes: the follow-on `[I]` (8191.99 after a reload) now cites `D2S_LoadFinish`; the merged-ids `[C]`
    note now also cites S1a rows 87 and 101 for its save-side half, and says the I3/I4 pseudocode re-tag is plan 0038
    Phase 3's.
  - **Point (3), the amendments: accepted** (above).
  - **Point (4), not determinable statically: accepted.** `kids[n]` is narrowed with the reason and the route (a run
    or a declared-stack emulation); the host bytes are a body `[I]` with the reimplementation rule (carry unchanged);
    status bit 1 is an `[L]` labelled out of plan, not "moved".
  - **Point (5), held items: accepted.** data/excel (P1b (a)) and the items/uniques-sets half of Q22 wait for P1c; the
    vendors half of Q22 (the gambled unique marked made) is folded here, which is right, since the open question was
    vendors'. The P1b backlog entry stays annotated, not struck.
  - **Other corrections confirmed:** sockets-runewords *Patience*, quality's "two quivers" (`mboq`/`mxbq`), tc's
    "upgrade bits" (forced ethereal and sockets, `ce=` without effect).
  - **Fix, research map.** Three rows had the new clause spliced into the old one's punctuation (items/tc, items/affixes,
    save/d2s: "…from S2b: both line sets…", "…corpse record: merc header…"); rewritten. The other nine rows are right.
  - **Gate:** fast tier green (the 15 W4 `based_on` warnings are the filed wiki follow-up).
  - **Next:** the owner merges `lane/p39s`; the W4 wiki follow-up; P2 for data/excel and items/uniques-sets after the
    P1c review.
- **2026-10-17 — W4 wiki refresh and rng W1 anchors (spec-writer, `lane/wiki5`, from `main` `4a0d8b2`; review pending).**
  - **Wiki.** Nine pages re-read against `git diff` of each `based_on` spec since the page's date and restated where the
    fold touched them: items, items-other-paths, saves, characters, game-data, randomness, levels, monsters, objects.
    Hedges kept: code-read points are said as "read from the code", the confirmed ones (cube output cell, Patience, the
    21-bit clamp of B10, the populated and client-copy room bits, the override survey) as checked. W4 15 → 0
    (16 dates bumped: rng/README's from the anchor edit below).
  - **Spec W1.** rng/README L34, L36, L49 and rng/seeds L532 now carry their finding's anchors; no tag changed (the
    S1b raises are plan 0038 Phase 3's). data/excel's 11 held for the P1c fold. W1 15 → 11.
  - **Gate:** fast tier green. **Next:** architect review (backlog).
- **2026-10-17 — `lane/wiki5` review (architect): accept with fixes.** Every changed wiki statement traced to its spec
  at the same strength: code-read points are worded "read from the code" (no-death-drop writers, sparkle gold/potions,
  monster owners, staff-mods test, forced ethereal/sockets, runeword save row, stale slot, stat-delta tests, act-change
  count, gambled uniques, Cow King quality, cursor cube, move gate, object ilvl 1, `0x0CF`, status bit 1, NPC slots,
  corpses, `RareFormat`, stored item seeds, initialiser survey, bits 3/14, edge merge, created-dead marks, Objects
  readers); "confirmed" only on `[C]` (save/d2s F1 clamp, 364 entries, 8191.99; I4 merged ids; cube G4, 100 placements
  of 100; Patience; rng/seeds step note 6 populated and client-copy bits). The "own magic find counts twice" sentence
  matches items/quality M3 (`[I]`, `SpecialMonPlace` 0x005A0B9B). rng anchors: all ten `fn:` resolve in
  `re/symbols.csv` (RNG_Step/Range/RangeB/RangePow2/RangePow2Plus/SeedInit/SeedInitOne, DRLG_ActCreate,
  DRLG_RoomCreate, sub_00676150_LinkPick, the last one of drlg/0007's link callbacks); run:2026-10-11-rng-emu has its
  heading in findings/rng/experiments.md; `RNG_Step`'s single static caller makes the ActCreate/RoomCreate steps
  inlined copies. Gate fast tier green, E8 links and E11/W4 `based_on` clean, 22 warnings (11 W1 data/excel held for
  P1c, 11 W3). **Fixes applied on the lane:** (1) items § magic find: "MonStats minions of a champion-pack member" was
  wrong, the spec says party minions of a `SetBoss` leader; "a boss placed by a map preset" restated as the
  special-monster placement (a superunique, for example), and the twice-counted MF scoped to its own kills. (2) items §
  staff mods: the type test applies only when the skill names an item type (affixes I5, `itypea1` ≥ 1). (3) items §
  overrides: the survey lives in items/quality § F, now linked beside uniques-sets § B. (4) saves § item fields: the
  stored prefix is rebased, so "the ids are the merged numbers" now says they come from them. (5) rng/README § Tables:
  the no-table line cited six primitives while 3b76e9b's subject says seven; `fn:RNG_RangePow2Plus@0x00472240` added
  (no tag change). No follow-ups.
- **2026-10-17 — Phase 1 batch P1c done (reverser, `lane/p39c`, static).** 8 ledger items (B3, B5, B6, Q4, Q26–Q29) and
  three reverser follow-ups from the backlog: the P1b review's (a) bit-17 writers and (b) `MonSetOwner` sites, and the
  plan 0038 round-3 review's id-573 survey. No game run. Ghidra ran on the lane's copy (`ghidra-p39c`). The work used
  objdump operand scans of the whole image, `tools/xrefscan.py`, a DS1 survey with `tools/ds1.py`'s unit model, and
  re-reads of kept logs (run:2026-10-13-mon-spawn, run:2026-10-16-hirelings, sha256 checked against the manifest);
  the scratch scripts were not kept. 44 symbols added (39 `func`, 5 `data`, all `I`). New statements: 7 `[C]` and 22
  `[I]`; no `[L]` raised or added.

  | Item | Verdict | Anchor or reason |
  |---|---|---|
  | B3 | stale | the ranges are in monsters/0002 § 7; the cases and `0x0054E2A0` (`PresetFallenVariant`) in monsters/0003 § 7 and § H4b special 65; the superuniques in § 6. Pointer in [monsters/0003 § P1c](../findings/monsters/0003-special-monsters.md#plan-0039-batch-p1c-2026-10-17); table-doc questions filed to the archivist |
  | B5 | stale | (c) and (e) reproduced in run:2026-10-14-uniques-forced, [items/0004 § 10](../findings/items/0004-uniques-sets.md#10-phase-2-reproduction-plan-0019) `[C]`; the spec already states both; (d) ruled d-none 2026-10-14 |
  | B6 | stale | both notes are in harness-play.md ("Every recipe needs `"game"`", "Reinstall before every launch") |
  | Q4 | answered | the 191 `g_pMonStats` reads all index by position (177 bounded, 6 fixed `imp` classes, 5 loader post-pass, 3 alloc/free); none searches by `Id`: [data/0001 § P1c](../findings/data/0001-excel-loader.md#plan-0039-batch-p1c-2026-10-17) `[I]` |
  | Q26 | answered | `MonsterInit` → `MonRegionFindAdd` appends a class new to its level region and rolls its sets on the unit seed; the 1 786 logged creations (1 785 as filed; review re-count) fit the found, appended or stale step count exactly, the 6 and 15 included: [monsters/0002 § P1c](../findings/monsters/0002-room-population.md#plan-0039-batch-p1c-2026-10-17) `[C]` |
  | Q27 | answered (builds on H4b) | `OBJ_OperateDispatch` → `OBJOP_Shrine` (OperateFn 2) → `g_ShrineEffects[20]` → `0x00583050` → nearest qualifying monster (filter and distance read) → `MonMakeSpecial`: [monsters/0003 § P1c](../findings/monsters/0003-special-monsters.md#plan-0039-batch-p1c-2026-10-17) `[I]`; still d-owner for a run |
  | Q28 | answered | 67/68/69/100/352 are MonStatsInit B5 constants and 336 is the B10 MonStats skill at level 1 + `MonsterSkillBonus` (`[C]`, 72 logged blocks); `Share` and the equipment columns have no reader `[I]`; the description is `STRTABLE(g_HireDescStrIdx[HireDesc])` `[I]`, the table `[C]` by data: [hirelings/0001 § P1c](../findings/hirelings/0001-hirelings.md#plan-0039-batch-p1c-2026-10-17) |
  | Q29 | answered | `ExpGrantCapped` is the Ancients reward (a5q5, word 39); 75 % of the death loss actually taken goes onto the corpse and back to its owner, and a player killer takes none; bit `0x20` comes from the class select in an expansion install plus a checkbox: [player/0001 § P1c](../findings/player/0001-creation.md#plan-0039-batch-p1c-2026-10-17) `[I]` |
  | P1b (a) | answered | 30 direct bit-17 writers (20 plain ORs, not 21), by unit kind and MonAI row: [items/0001 § P1c](../findings/items/0001-tc-resolution.md#plan-0039-batch-p1c-2026-10-17) `[I]` |
  | P1b (b) | answered | the 17 sites, each with its monster and owner: [items/0002 § P1c](../findings/items/0002-quality-roll.md#plan-0039-batch-p1c-2026-10-17) `[I]` |
  | id 573 | d-none | only Act IV DS1 ids 5–7 map to 573 and no shipped DS1 uses them (2 274 parsed); the other `PresetUnitCreate` callers add none: [drlg/0004 § P1c](../findings/drlg/0004-preset-units.md#plan-0039-batch-p1c-2026-10-17) `[C]` data + `[I]` |

  Surprises:
  - The hireling spec's "skill 336 at level 1" holds only in Normal: the MonStats skill takes the difficulty's
    `MonsterSkillBonus` (4 in Nightmare, 8 in Hell, logged).
  - P1b's bit-17 count of 21 included a bit-29 OR. Its "12 skill sites" are monster AI self-removals (traps, nests,
    spawners, trapped souls) plus the mosquito nest, which P1b had placed in `UberTristramDrop`.
  - `Share` is copied into the hire entry and never read.
  - The hire description is a hard-coded nine-word string table; `hiredesc.bin` plays no part.
  - The death-loss amount travels through client `+0x508` to the corpse.

  Spec notes for Phase 2, the archivist entry, the reverser residues and the review request are in the backlog.
- **2026-10-17 — Phase 1 batch P1c reviewed (architect, on `lane/p39c` after merging `main` at `345e942`). Verdict:
  accept with fixes (applied in the review commit).** Phase 1 is complete; P2 can finish data/excel and
  items/uniques-sets with the P1c fold.
  - **Merge.** Conflicts in the backlog, this log and `re/symbols.csv`, kept on both sides. Two addresses clashed with
    main's plan 0041 rows: `0x00583C70` keeps main's `OBJOP_Shrine` (lane: `sub_00583C70_ShrineOperate`) and
    `0x006E1850` main's `g_ShrineEffects` (lane: `g_ShrineFns`); monsters/0003 § P1c, the backlog and the Q27 row now
    cite main's names, and the NULL-row fallback `0x005828E0` is named (`SHRINE_Refill`, main's row).
  - **Anchors (objdump on the pinned image), 22 checked, all hold.** Q26: `0x005553A0` `call 0x574250`
    (`MonsterInit`), `0x005742DC` `call 0x547bc0` before `0x005742E4` `call 0x573cb0`, `0x00547C87`
    `cmp byte [eax+0xec],2; jbe`, `0x00547CA1` `call 0x5bdb20`. Bit 17: `0x00458E0E` `or [ebx+0xc4],0x20000000`
    (the bit-29 match), `0x005BBBE9`, `0x005BBC41`, `0x005E02A1`, `0x005B2EC2` (after `call 0x5543b0` with `dl` 2)
    plain ORs, `0x005CC9B4` `or eax,0x4020000` stored at `0x005CC9BD`, `0x005732A3` `or …,0x4020200`; `g_ObjInitFns`
    slot 60 (`0x00731CB0`) = `0x005BBBA0`; `g_MonAiTable` slot `+8` of rows 43, 45, 77, 80, 83, 88, 91, 92, 99, 129 =
    the ten AI functions of the table. 573: `g_Ds1ObjectIds` (s32[5][150]) holds 573 only at act 3 ids 5–7, minimum 0.
    Q27: `g_ObjOperateFns` slot 2 (`0x00732D20`) = `0x00583C70`, `0x006E1940` = `0x00583050`. Q28: `0x00573F16`/`18`
    `push 0x4b; push 0x43`; `g_HireDescStrIdx` = 0, 3371, 3372, 11090, 11088, 11089, 3377, 3376, 3375. Q29:
    `0x0057F80F`–`0x0057F844` (`CLIENT_GetDeathExpLoss`, the `0x100000` split, 75 and 100), `0x00433FF1`
    `or word [eax+0x1ef],0x20`. Ten new function symbols start after an `int3`/`ret`.
  - **Re-runs.** The bit-17 operand scan: 20 plain `or [reg+0xC4],0x20000`, 9 OR-immediates with bit 17 (0x4020000 ×5,
    0x402000E ×3, 0x4020200 ×1) and the register OR: 30, as filed. Q4: 194 operand sites (18 absolute `0x0096C6A8`, 176
    `[reg+0xA78]`), as filed. Q26 (`systemd-run … MemoryMax=4G python3 -I`, an independent script on `tools/monpool.py`):
    the same histogram and the same 14 appends at their predicted step counts, but the table sums to **1 786**, not
    1 785, and the 2-step overlap is 905 appends with no draw (761 also stale), not 45. Fixed in monsters/0002 § P1c
    (a review paragraph), the Q26 row and the backlog.
  - **Ruling 1, Q26 at `[C]`: accepted, scoped.** The code path is read, and the second source is the logs: for the 14
    appends the model predicts an exact step count from the seed (6 to 16), and every one matches. That is a test the
    rule could fail, which a 2-step fit is not. The region state is not modelled, so the `[C]` covers "the extra steps
    are the append's variant roll on the unit seed", not which branch each 2- or 3-step creation took; the review
    paragraph says so. The rule itself was already `[C]` (monsters/0001 S3a pool 22).
  - **Ruling 2, Q28 and the Rogue skill level: accepted.** `[C]` for the five constants and skill 336: MonStatsInit B5
    and B10 read, and the 72 logged blocks agree (level 1/4/8 by difficulty = `Sk1lvl` 1 + `MonsterSkillBonus` 0/3/7).
    The spec's "level 1" is a correction, routed in the P1c fold (d). `Share` and the equipment columns stay `[I]` (one
    xref method); the HireDesc table is `[C]` by data, the lookup path `[I]`.
  - **Ruling 3, Q4 at `[I]` on one operand scan: accepted.** `[I]` is the right level: a single tool, with the copied
    base pointer the stated blind spot. The review's count matches. No raise without a second method (a Ghidra xref
    pass or an emulated reader).
  - **Ruling 4, the P1b corrections: accepted.** 20 plain ORs (the 21st, `0x00458E0E`, sets bit 29), `0x005BBBE9` in the
    compelling-orb object init, `0x005E02A1` in the `MosquitoNest` AI, and the "skill sites" are MonAI self-removals.
    The 21 was the P1b review's own figure; items/0001 § P1b now carries a correction note on its count and
    its "Not read" list. The merged items/tc B1 ("occurs 21 times", the "three quest drops, 12 skill-code sites" split
    and the *Open questions* `[L]`) and the [items](../wiki/items.md) wiki paragraph are routed to the spec-writer in
    the P1c fold (f), worded exactly.
  - **Ruling 5, id 573: accepted, d-none.** Moved in [inventory § 2.6](0038-inventory/README.md#26-moves-made-by-the-batch-reviews)
    as a remainder of drlg-preset 18, with no change to the totals. The `[C]` on the DS1 survey is data plus the table
    re-read; the "other callers add none" bullet stays `[I]`.
  - **Ruling 6, player/0001 *Leads used*: accepted as left.** ADR-0007 asks for the page to be re-read before a verdict
    changes; the code reading stands on its own and the finding says the 75 % agrees in substance. Follow-up to the
    reverser for the re-fetch (backlog).
  - **Ruling 7, no scratch scripts kept: accepted for this batch, with a follow-up.** Every count the batch's tags
    rest on was reproduced here (bit 17, Q4's sites, Q26's fit). Later batches should keep a count-bearing scan in
    `tools/` or give its exact pattern in the finding (backlog follow-up (b)).
  - **Tags.** Seven `[C]` (Q26 ×2, Q28 ×2 and the HireDesc data, the two 573 data bullets) each have code plus logs or
    data; the 22 `[I]` are code readings. No `[L]` added; no `[L]` above *Open questions* in the touched findings.
  - **Symbols.** 44 rows filed; 42 kept, the two clashes resolved to main's names. All `I`, kinds right, each cited
    by its finding; gate fast tier green after the merge.
  - **Fix, gate W1 in the findings (0 on `main` since `lane/w1`).** The batch added 13 W1 warnings: bullets whose
    anchors sit after a sub-list or a wrapped `0)` that the gate reads as a new item, and tag mentions in prose. Fixed
    with each statement's own anchor on its lead line (player/0001 ×3, monsters/0003, drlg/0004, items/0002,
    monsters/0002) or the mention reworded (player/0001 ×2, monsters/0003, data/0001, the review paragraph). Findings
    W1 back to 0; the 11 left are data/excel's, held for P2.
  - **Follow-ups (backlog):** to the reverser, the *Leads used* re-fetch and keeping scan scripts; the P1c fold entry
    to the spec-writer amended (items/tc and wiki wording, `OBJOP_Shrine`, the 1 786 count).
  - **Next:** the owner merges `lane/p39c`; then P2 (the P1c fold, data/excel and items/uniques-sets).
- **2026-10-17 — Phase 2 round 2 (P1c fold and the held uniques-sets half of Q22) done (spec-writer, `lane/p39s2`, from
  `main` `9bdd892`; review pending).** The P1c fold entry (b)–(h) with the review's amendments (the 1 786 re-count,
  `OBJOP_Shrine`, the Rogue skill at 1/4/8, items/tc B1's 20 plain ORs and 30 writers), and P1b (i)'s uniques-sets half.

  | Spec | Items | {C, I, L} |
  |---|---|---|
  | monsters/spawn | Q26 (J1) | {110, 64, 6} → {112, 64, 5} |
  | monsters/special | Q27 (§ J, *Entry points*) | {104, 91, 4} → {104, 93, 3} |
  | hirelings | Q28 (§ E notes E5, § I) | {89, 39, 8} → {92, 41, 6} |
  | player/creation | Q29 (A1, J2, J3) | {81, 39, 5} → {81, 44, 3} |
  | items/tc | P1b review (a) (B1) | {45, 81, 7} → {45, 82, 6} |
  | items/quality | P1b review (b) (M3) | {64, 38, 3} → {64, 39, 2} |
  | drlg/preset | id 573 (§ 6) | {134, 24, 2} → {135, 25, 2} |
  | items/uniques-sets | Q22 held half (C8, C9); B5 stale, no change | {70, 52, 6} → {71, 55, 4} |

  - **Corrected:** hirelings' Rogue skill "level 1" (only in *Open questions*) → 1/4/8 by difficulty; items/tc's "21"
    bit-17 writes and the P1b split ("three quest drops", "12 skill-code sites"); the [items](../wiki/items.md) wiki
    paragraph to match.
  - **Narrowed, not closed:** player/creation (a saved corpse's stat 13 and the create screen's mode word, P1c residues
    (c) and (d)). Closed with a pointer to a reverser residue, no tag: items/tc (`0x005C09E0`'s skill), items/quality
    (`FormationSpawn`'s callers).
  - **Held:** data/excel (P1b (a), P1c (a), its 11 W1), to be folded with plan 0038 Phase 3's re-tag after the S1f
    review.
  - **Wiki (W4 7 → 0, restated):** items, monsters, characters, saves. Research-map rows of the eight rewritten.
    Backlog: the P1b and P1c fold entries annotated (done in part, data/excel held), the W1 entry annotated, review
    request filed. Gate green.
- **2026-10-17 — Phase 2 round 2 reviewed (architect, on `lane/p39s2` after merging `main` at `2783aee`). Verdict:
  accept with fixes (applied in the review commit).** Plan 0039 is complete except data/excel (P1b (a), P1c (a) and
  its 11 W1), which is folded with plan 0038 Phase 3's re-tag.
  - **Merge.** Clean; no backlog duplicates.
  - **Tags against the P1c findings and rulings.** Every new `[C]` and `[I]` matches its finding at the same strength.
    monsters/spawn J1: the rule `[C]` (S3a pool 22) and the fit `[C]` scoped to the 14 appends, the 2- and 3-step
    creations said not to tell the branches apart (ruling 1); 1 725 + 47 + 14 = 1 786. hirelings: the five B5
    constants and skill 336 at 1/4/8 `[C]` (ruling 2; Rogue blocks 22 + 6 + 2), the HireDesc table `[C]` by data, the
    lookup and `Share` `[I]`. items/tc B1: 20 plain ORs, 9 OR-immediates (5 + 3 + 1) and the register OR = 30, and the
    kinds sum to 30 (1 + 2 + 1 + 1 + 1 + 2 + 12 + 5 + 3 + 2) (ruling 4). drlg/preset § 6: the DS1 survey `[C]`, the other
    creators `[I]` (ruling 5). player/creation and monsters/special: all `[I]`, as filed. items/uniques-sets: C8 and
    the two C9 code notes `[I]`, the 17-base survey `[C]` by data.
  - **No `[L]` above *Open questions*** in the eight; front matter recounted (gate E6 green) and the {C, I, L} deltas
    match the added and struck statements.
  - **Anchors (objdump on the pinned image), 8 new ranges checked, all hold:** `0x00535A61`–`0x00535A8A` (new = exp − loss;
    kept = exp − T(L−1) floored at 0 under the clamp; `call 0x5391e0` before the stat-13 write; loss 0 skips all),
    `0x005830C7`–`0x005830CC` (`jmp 0x5a4940`, `MonMakeSpecial`), `0x005827D8` (`lea edx,[eax+0x1f]`), `0x00557E41`
    (`call 0x557450`, `ItemCreateByQuality`), `0x00556A1A` (`call 0x556530`, the only call to `ITEMS_UniqueMarkMade`
    in the image), `0x005740E0`–`0x00574135` (`Sk1lvl` + `[ebp−0x1c]` into `call 0x56deb0`, 8 slots),
    `0x006639C0`–`0x006639D1` (`max(0, [edi+0x4c])` to `[esi+0x28]`), `0x004B6262`–`0x004B6267` (`call 0x663720`).
  - **Research-map rows:** the eight rewritten whole, counts match the front matter.
  - **Wiki:** every changed statement of items, monsters, characters and saves checked against its spec; all hold,
    each code reading worded as such and the region append's confirmation scoped to the 14.
  - **Fixes (4; none to the wiki):** (1) items/quality M3 "the other 17 give these kinds an owner … Three more sites only clear" counted
    the three twice: of the 17, fourteen give an owner and the remaining three clear (miscount). (2) items/tc B1: the
    crow nest's AI test is "reaches", the sarcophagus and mosquito nest's "passes" (items/0001 § P1c) (misread).
    (3) hirelings *Outputs* still named only § G's stats; it now names the stats and skill `MonStatsInit` leaves (§ I)
    (stale cross-reference). (4) the research-map hirelings row carried the finding's stale "(C 42 / I 25)" into the
    rewritten row; dropped (stale cross-reference).
  - **Gate:** green (fast tier), 22 warnings (data/excel's 11 W1, held; 11 W3 from main).
  - **Next:** the owner merges `lane/p39s2`; data/excel goes with plan 0038 Phase 3.
- **2026-10-17 — `lane/arc5` reviewed (architect, after merging `main` at `33d6d37`; the seven archivist entries of
  2026-10-17: the PropParamCell order in `excel_bin.py`, the 0039 P1b/P1c, 0041 P1, 0042 P1 and 0043 P1 readers, the
  plan 0044 pairs). Verdict: accept with fixes (applied in the review commit).**
  - **Merge.** Clean; `backlog.py migrate` moved nothing. `main` had no `test_d2s.py` change, so there was nothing to
    reconcile with `lane/rbs2`; if that lane lands its own base entries first, keep this one (it covers all 36 new
    recipes and the eight legacy ones) and drop the duplicates.
  - **Re-runs.** Gate fast green (53 warnings, all from `main`); `--full excel_layout,stats,economy,quest,travel,d2s`
    green. `test_d2s.py` 45 tests OK. `excel_bin.py diff` Sets 2 144, SetItems 11 684, Runes 7 943, States 12 765, Books
    27 cells, 0 mismatches. `mp_saves.py check`: 25 recipes 0 bad, 17 pairs 0 bad.
  - **Baselines add only what they should.** `excel_layout`: `cells` +185 and `states_cells` +185 = the `attred` bit
    over 185 records; `group` u8 + pad → s16 keeps the count. `stats`: the one new key `flag_attred=0`. No other key moved.
  - **Tags against their findings, same strength:** States (data/0001 P1b descriptor, stats/0002 § 2–4), Sets/Runes/
    SetItems (stats/0001 surprise (e)), Shrines (stats/0002 § 5, monsters/0003 P1c), Objects (objects/0001 P1b,
    quests/0002 § 2 and § 6, stats/0002 § 5), Hireling and HireDesc (hirelings/0001 P1c), d2s.md (save/0001 P1b), Books,
    Npc, MagicPrefix, ItemStatCost and Skills (items/0011 § 1, § 3, § 4), Levels (quests/0002 § 6, Dead ends). All hold
    but the MonPlace and States points below.
  - **Rulings on the lane's points.** (1) **MonPlace:** leaving the unread rows (0, 1, 4–16, 27, 33–36) as an open
    question is right; the composite "`[C]` logged, `[I]` otherwise" bullet is split by case (logged: 17, 18, 23, 29,
    30 in level 111, 31; `[I]`: 22, 32, `deathmauler1` in 110), and H4b's calls with case 36 are now mentioned. Reverser
    follow-up filed. (2) **"22 of 56":** the 22 stands (56 − 34, stats/0002 surprise (f)); the sentence on the other 34
    was stale after `lane/rbs`: its scan gives 27 of them an immediate set or clear site and none to 7 (6, 25, 29, 39,
    116, 164, 171). Rewritten. (3) **The weak joiners** (level 9, 60 life, Fire Bolt 5) are a sound death case for MP01
    and MP14 (b) as staged; "weak enough to die" is a staging estimate the session must record (max life after the
    load, the death itself). For MP23's 200 attack events they would die too often; follow-up to add a strong pair.
    (4) **Shrines `reset × 1200 + 1`** is stats/0002 § 5's `[I]` (0x00583C70, `+0x10`·1 200 + 1) at the same strength;
    the doc now says a column unit is 1200 frames whatever the header's "minutes" says, and cites § 5.
  - **Fixes (4):** (1) MonPlace fixed-class bullet tagged `[C]` over 22 and 32, which no log reached (overclaim).
    (2) MonPlace: H4b's case-36 calls left out (omission). (3) States open question: the 34 rows "have setters listed,
    in functions not read" predates `lane/rbs` (stale cross-reference). (4) Shrines `reset`: no finding link and the
    header's unit unsaid (omission).
  - **Closed:** the review request; `2026-10-17-architect-reverser-test-d2s-recipe-bases` (fixed here; 8 legacy bases).
  - **Filed:** reverser `monplace-remaining-cases` (the unread `PresetMonSpawn` cases and case 36); archivist
    `mp-saves-mp23-strong-pair` (a strong hostile pair for MP23's bulk).
