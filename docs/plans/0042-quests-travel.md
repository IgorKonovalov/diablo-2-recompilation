# 0042 — Quests and travel: the quest state machines, waypoints, town portals and level entry

> **Status:** approved (owner, 2026-10-16; unattended); [ADR-0017](../adrs/0017-scope-quests-travel-economy.md) accepted 2026-10-16
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer, human (fallback only)
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0017-scope-quests-travel-economy

## TL;DR

**Question:** for each quest, which server event sets, clears or reads each bit of its record, per difficulty; which
game-wide quest flags exist and what reads them; how does a player activate and use a waypoint, change act, open and
use a town portal, and where is a player placed on entering a level? When it is done:
- `docs/findings/quests/0001-progression.md` has one bit table per quest (setter, trigger event, readers), the
  game-wide flags, the quest seed's draws and the quest-gated creation code; `docs/findings/quests/0002-travel.md` has
  the waypoint record, act travel, town portals and level-entry placement;
- `tools/quests.py` predicts the quest record and the travel outcomes from a logged event sequence;
- `docs/specs/quests/` is drafted and reviewed; the quest-state oracles of the creation specs are replaced or narrowed.

## Context

- Scope comes from ADR-0017 (accepted 2026-10-16). Research map: a new **Game rules (ADR-0017)** band, rows `quests/progression`
  and `quests/travel`, added when this plan starts.
- **What exists.** [save/0002](../findings/save/0002-quest-words.md): the quest record is 16 bits per quest, block
  *d* is difficulty *d* (`[C]`), the act-travel words and the waypoint tab gate. [items/quest-drops](../specs/items/quest-drops.md)
  (reviewed): the quest seed (game-seed draw 4), the quest drops, imbue, sockets, personalisation, the Hellforge, the
  Cow King, and "when quest bits get set is simulation and an input". [objects § L](../specs/objects/README.md): the
  quest objects, named only.
- **Code already named** (grep `re/symbols.csv`): `QUESTS_InitGame` (C), `QUESTS_GetSeed` (C),
  `QUESTS_DispatchEvent`, `QUESTS_DispatchUnitEvent`, `QUESTS_MonsterDeathEvent`, `QUESTS_ObjectEvent`,
  `sub_00543BD0_QuestsInvItemEvent`, `QUESTS_HookMonster`, `QUESTS_PlayerRecord`, `QUESTS_FindById`,
  `QUESTS_GiveItem`, `sub_00546270_QuestsPlayerJoin`, `sub_00544720_GameQuestSet`/`Get` (I),
  `QUESTRECORD_GetState`/`SetState`/`ClearState` (I); travel: `WAYPOINT_*` (I), `sub_00584E30_WaypointOperate`,
  `sub_00584F60_WaypointTravel`, `sub_005467E0_NpcActTravel`, `sub_00546AC0_DuranceActTravel`,
  `sub_0053ACC0_PlayerChangeAct`, `sub_0053AEC0_PlayerChangeLevel`, `sub_0056D130_PortalObjectCreate`,
  `OBJINIT_Portal` (C), `sub_00584750_DurancePortalOperate`; the client's `sub_0049C*` waypoint menu (presentation,
  named only).
- **Quest-state oracles in reviewed specs** this plan should feed: items/quest-drops (the quest bits at kill time, the
  quest seed on entry), objects (quest-state `InitFn`s, object 582, the Zoo), monsters/spawn (the Chaos Sanctuary gate),
  monsters/special (superunique quest hooks), rng/seeds (Act II tomb fields `+0x094`/`+0x484`, the Act III bit
  `+0x474`, the level-27 bit set at level 6), items/cube (the classic word-26 cow gate), drlg/collision (the Arcane
  Sanctuary waypoint quest word), save/d2s (which slot is which difficulty).
- **Data.** There is no quest table: quest logic is hardcoded. Phase 0 checks which tables the quest and travel code
  reads (the Levels waypoint and town columns, Objects waypoint and portal rows, any quest-reward table the plan 0038
  H1b batch names) and documents the columns not yet covered.
- Leads: `src:arreat-summit-quest-pages` (registered); Phase 1b fetches the per-act quest pages and registers more.

## Phases

### Phase 0 — Travel and quest columns
- **Owner skill:** archivist
- **What:** document the columns the travel and quest code is expected to read, and build the saves Phase 2 starts
  from.
- **Outputs:** [Levels](../tables/Levels.md) § Travel (the waypoint, town and act columns and which levels have a
  waypoint, per act); [Objects](../tables/Objects.md) § Waypoints and portals (the rows by class, `SubClass` bit 6);
  table docs for any quest table Phase 0 finds loaded; a `tools/d2s.py` recipe set for quest saves: for each quest, a
  save of each class needed with the quest words set to just before each step Phase 1 names (stock tables, built
  quest words: built saves, not forced-path runs), and saves with each act's waypoints set.
- **Done when:** each named section lists its columns with offsets and ranges; `excel_bin.py diff` passes on any new
  table; the quest saves load in the game (first step of Phase 2 if no slot is free, as in plan 0034); the gate is
  green.

### Phase 1 — Read the quests and travel
- **Owner skill:** reverser
- **What:** read `QUESTS_InitGame` and every quest it registers, the event dispatch, and the travel code.
- **Outputs:** `docs/findings/quests/0001-progression.md`, `docs/findings/quests/0002-travel.md`,
  `docs/findings/quests/experiments.md` (empty heading); `re/symbols.csv` rows (subsystems `quests/progression`,
  `quests/travel`); `re/types/quests.h`.
- **Done when:** the findings state, each with addresses and `[I]` or better:
  - **the registry:** the quest descriptor table, how many quests and which act and difficulty each belongs to, the
    callback slots and the event kinds (monster death, object operate, item pickup or use, NPC interaction, level
    entry, player join, timer);
  - **per quest:** a bit table: each bit, the event that sets or clears it, the setter address, the readers (creation
    code, travel, NPC menus as server-side gates), the expansion and classic branches; and the quest's own draws on
    the quest seed or other seeds;
  - **the game-wide flags** (`GameQuestSet`/`Get`), the per-act fields of rng/seeds' open questions, and every
    creation-path reader listed in *Context*;
  - **NPC interaction:** the server side of an NPC talk that changes quest state (the packet, the check, the write);
    the dialogue text and menus are presentation and stay out;
  - **travel:** waypoint activation (the touch test, the record write), waypoint travel (the target position search
    and its draws), act travel through NPCs and the Durance portal, the town portal (scroll and book use, the portal
    object pair, the position search in town and in the field, closing, one per player), level entry through a warp
    (the target point, the free-spot search and its draws), and death or new-game placement in town;
  - for each event kind, the inputs, outputs, draws and seeds, and the chaining reading (ADR-0014 as ADR-0017 applies
    it);
  - the community cross-check (Phase 1b) done;
  - **the boundary recommendation** for Phase 2: the event entry points, the triggers taken as inputs (a kill, an
    operate), the oracles. The architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register the quest walkthroughs and travel documentation; compare blind, quest by quest.
- **Outputs:** `docs/sources.md` entries; verdicts in the findings' *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (agent-driven; **at most two slots**, given in the prompt); owner play is the fallback for a
  step scripted play can't reach (an act boss in Nightmare or Hell)
- **What:** write `tools/quests.py` (model and `check`; `tools/questdrops.py` stays plan 0032's), extend plan 0032's
  `tools/gdb/quests.gdb` and its handler (or add a `quest-state.gdb` beside it), and steps files that walk each quest
  step from the Phase 0 saves (`quest-load.steps` and `quest-cowportal.plan` are precedents); log a run.
- **Done when:** `run:YYYY-MM-DD-quests` reproduces with **0 mismatches** over at least:
  - every quest completed once in Normal in an expansion game, each of its bit transitions predicted from the logged
    event, and the saved quest words after *Save and Exit* predicted word by word;
  - ten quests in Nightmare or Hell, and the Act I–IV quests in a classic game;
  - every creation-path reader of *Context* observed reading a state this run set, at least once;
  - 60 waypoint activations, 150 waypoint travels, 60 town portals (creation, both ends' positions, use, closing),
    150 level entries through warps, 20 act changes through NPCs, positions and draws predicted;
  - **chaining:** for every event kind that draws, at least 20 chained pairs; a kind with none keeps its draw order
    `[I]`;
  - the Phase 1b cases.

  A quest step that neither scripted play nor the owner reaches is named in the record with the reason; its bits stay
  `[I]`. In-scope claims go to `[C]`, citing the run.

### Phase 3 — Spec: quests
- **Owner skill:** spec-writer
- **What:** write `docs/specs/quests/README.md`, `quests/progression.md` (a section per quest) and `quests/travel.md`;
  narrow or close the quest-state open questions in items/quest-drops, objects, monsters/spawn, monsters/special,
  rng/seeds, items/cube, drlg/collision and save/d2s.
- **Done when:** the spec follows the template; every statement is tagged; each quest has its bit table and a state
  diagram; the travel paths are pseudocode with their draws; worked examples from the run. The architect's review
  passes.

## Open questions

- **Two clients.** Per-player quest state in a party, shared quest events and the party record stay `[I]` (plan 0044).
- **Owner play.** The Uber Tristram and Pandemonium events (levels 133–136) and the late-act bosses in Hell may need
  the owner; plan 0038's d-owner rows could share those sessions.
- **The order of phases.** This plan does not wait for any simulation phase: a quest step's trigger (a kill, an
  operate, a talk) is an input. A boss fight's mechanics are combat's.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`; gated on ADR-0017.
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038. ADR-0017 accepted the same day.
- **2026-10-16 — Phase 0 landed (archivist, `lane/p42a`), review requested.**
  - [Levels § Travel](../tables/Levels.md#travel-plan-0042-phase-0): `Act`, `Waypoint`, `QuestFlag`/`QuestFlagEx`,
    `Portal`, `Position`, `SubWaypoint`, `Teleport`, `IsInside`/`Quest` with offsets and stock ranges; the 39 waypoint
    indices per act (I 0–8, II 9–17, III 18–26, IV 27–29, V 30–38, town first, `[C]` data); towns are the code's list
    (`LevelIsTown`), not a column. Readers named only for `Waypoint` (`[I]`), `Position` (`[C]`) and `SubWaypoint`
    (`[I]`); `QuestFlag`/`QuestFlagEx` (values 11, 13, 21, 39 and the cow level's 26 / 40, the only differing row),
    `Portal` (16 levels, Acts I–II and 134), `Teleport` and the act byte stay `[L]` for Phase 1.
  - [Objects § Waypoints and portals](../tables/Objects.md#waypoints-and-portals-plan-0042-phase-0): the 16 waypoint
    rows (bit 6 = `OperateFn` 23 = `InitFn` 17, `[C]` data), the town portals 59/60 (bit 2, `OperateFn` 15, `InitFn`
    11 vs 12), the bit-4 portals 298 and 342, and the handler address of each index read from `g_ObjInitFns` /
    `g_ObjOperateFns`. Surprise: **410 `Siege Control` shares `OperateFn` 46 (`DurancePortalOperate`) and `Parm0` 18
    with the hellgate 342**; 100 (Duriel's Lair portal) and 377 (Guild Portal) share `OperateFn` 43.
  - **No quest table.** No excel table the game loads (data/0001's 86, `docs/tables/README.md`) holds quest data;
    nothing to document. The plan 0038 H1b batch names no quest-reward table either.
  - `tools/travel_survey.py` (`levels`, `objects`, `summary`), registered as gate survey `travel` with its baseline;
    `excel_layout` is unchanged (no layout edit).
  - Saves ([d2s.md § Quest and travel saves](../formats/d2s.md#quest-and-travel-saves)): 14 new recipes, built into
    `workspace/runtime/quest-saves-p42/` with `tools/quest_saves.py build` (which also rebuilds the 9 plan 0032 quest
    saves to their hashes): `travel-wp1`..`5` (each act's waypoints plus the five towns, every quest done),
    `travel-wpnone`, `travel-tab2` and `travel-tab5d` (save/0002's per-word tab gate run case), `travel-arcane`
    (index 16 with the Act II quests open), `travel-act2`..`5` (just before the Warriv, Meshif, Durance and Tyrael act
    changes, with the quest items the Meshif and Durance branches remove), and the classic `questfreshc`.
    `quest_saves.py check` compares each with its intended state (14 / 0 bad); `test_d2s.py` 44 tests OK.
  - **Not loaded.** No harness slot is free for this lane (no games here), so, as in plan 0034, loading the 14 saves
    (`quest-load.steps`, *Save and Exit*, compare and pin the hashes in `test_d2s.py`) is **the first step of Phase 2**.
  - **Pending Phase 1:** a save per quest step for every step Phase 1 names that the existing findings do not
    (all quests but the boss TCs, imbue, Hellforge, socket, personalisation, cow level and act travel); class-specific
    steps (none known); the `0x00483F80` reward bits; Warriv's offer test (`0x0058FB50`, word 0 bit 0); words 0, 8, 16,
    24, 29–34, 41. The recipe pattern is `travel-act3`: `quest_bits` for the step's words, start act, the step's items.
  - Commits: `8ec6710` (recipes, `quest_saves.py`, tests), `a24e356` (table sections, `travel_survey.py`, gate), and
    this entry with d2s.md.
