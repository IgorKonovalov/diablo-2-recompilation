# 0039 — Backlog sweep 4: the static loose ends and the open questions a reading settles

> **Status:** proposed
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
