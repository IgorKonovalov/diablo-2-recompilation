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
