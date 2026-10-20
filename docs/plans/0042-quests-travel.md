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

#### Phase 2 part 2 — the completion pass (ruled at the part 1 review, 2026-10-17)
- **Owner skill:** reverser (agent-driven, at most two slots); owner play only for the items marked *owner*.
- **Start:** the part 1 tools (`questev.py`, `quests.py`, `quest_sessions.py`); new saves as tool-built recipes set
  just before each step (the `quest-tpc` precedent; the archivist documents them in d2s.md afterwards, backlog). Fix
  the scripted walks first: reach a waypoint, a portal or an NPC by teleporting next to the object, as `clickwarp`
  does for warps.
- **Done when:** `run:YYYY-MM-DD-quests2` reproduces with 0 mismatches under the same checker, which re-checks the
  part 1 logs unchanged, over at least:
  1. **quests, Normal expansion:** every quest step reachable by a talk, an operate, an item use, a level entry or a
     non-boss kill, from a save set just before it; each bit transition predicted from the logged event; the saved
     quest words after *Save and Exit* predicted word by word in each session. The per-quest tables (§ 7–§ 10) are
     raised step by step;
  2. **ten quests in Nightmare or Hell and the Act I–IV quests in a classic game**, by the same steps, with **at least
     one recorded Hell session**;
  3. **waypoints:** 60 activations from mode 0 (`TravelWpNone` and fresh saves; event 1 and the `Sync` 0 draw on the
     object seed predicted, 20 chained pairs); 150 waypoint travels with part 1's 61;
  4. **warps:** 150 level entries with part 1's 2, among them level 120's warp tiles (WRP rows 82 and 83) from both
     creators (`QuestSummit`, `TravelWpFive`), which decides `QUESTS_WarpGate`'s 120 → 118/128 branch both ways, and
     the warp gates into 73, 100 and 132;
  5. **act travel:** `NpcActTravel` 20 events (Warriv and Meshif each way, the Act IV → V travel), packet 0x48 once
     per travel word (7, 15, 28), a type-5 lookup that steps (Meshif's return to 40);
  6. **NPC 266 and 377:** first read where each is placed and when (Flavie at the Blood Moor preset; class 377), then 20
     chained player-seed pairs each; if scripted play cannot place one, that NPC is a named shortfall with the reason;
  7. **the Compelling Orb:** operates with and without `qf2`;
  8. **the rest of question 6–9:** quest timers (logger addition), a death and resurrection (packet 0x41, a low-life
     save), the stub character's double join (a stub save), a portal refused in a town, the Durance, Arcane and lair
     portals, and the creation readers of question 7 (Hratli's `InitFn`s, `InitFn` 52, the Tristram portal, the warp
     gates above).
- **Owner play candidates** (one owner session; plan 0038's d-owner rows may share it): the act-boss quest steps
  (Andariel, Duriel, Mephisto, Diablo, Baal) and the Ancients, which set quest 35's "done in this game" byte and so
  give the summit door's open path; the Nightmare and Hell boss steps; Diablo's `+0x13` reader; the Uber levels
  (133–136) with the portal refusal on 136. What the owner does not play becomes a named shortfall at the part 2
  review; those steps' bits stay `[I]`.
- **Named shortfalls now** (no further attempt in this plan): packet 0x58 on word 33 (the stock client never sends it;
  stays `[I]`); packet 0x48's 20-event floor beyond one case per travel word; the free-cell search's far rings unless a
  logged search needs one; every two-client case (plan 0044).

#### Phase 2 part 3 — the draw-bearing remainder (ruled at the part 2 review, 2026-10-19)
- **Owner skill:** reverser (agent-driven, at most two slots); **the last reproduction pass of this plan**: what it
  does not reach stays `[I]` in this plan, named with the reason, and no part 4 is planned.
- **Why:** part 2 found three misreadings among about twenty talk rows (NPC 266's draw count, the switched-off reward
  writes, word 40's bit map), one of them a draw count. The `[I]` draws that remain sit on the quest seed (it feeds
  the quest drops), the object seed and the level seed, and most of them are reachable by a waypoint hop or a town
  talk, which the part 2 driver does reliably (108 travels, 41 talk steps, 0 mismatches). The volume floors are not
  reopened.
- **Start:** the part 2 tools unchanged; new recipes set just before each step (archivist entry afterwards). A session
  budget of about four hours of game time; within it, the order below is the priority.
- **Done when:** `run:YYYY-MM-DD-quests3` reproduces with 0 mismatches under the same checker, which re-checks the 32
  logs of parts 1 and 2 unchanged, over what it reaches of:
  1. **quest-seed draws reachable by a waypoint or a talk:** word 11's eclipse arm on the first entry to level 44 or 45
     with state 0 (`RandLoHi(quest seed, 15, 17)` at 0x0059EDE1, the Lost City waypoint) and its timer firing (a
     logger line for the timer registration and callback, `0x00543E10`/`0x00543F10`); Anya's reward draw (word 37,
     0x00589937, a talk in Harrogath); the cairn-stone order draw (word 4, 0x00592E90) if a scroll path reaches it
     without walking to the stones; the Dark Wanderer timer's step (word 32, 0x005BD3E6) and the Zoo's draws if their
     triggers are a level entry or talk reachable the same way (read first; otherwise named);
  2. **waypoint activation from mode 0:** first read when `InitFn` 17 creates a waypoint in mode 0, then pick a
     waypoint one hop from where a built save starts (a town or a field waypoint next to a level entry); at least 20
     activations with event 1 and the `Sync` 0 draw on the object seed predicted; chained pairs if a logger line for
     the mode 1 → 2 draw is cheap, otherwise that draw order stays `[I]`;
  3. **act travel through NPCs:** Meshif west (the type-5 lookup that steps, Meshif's return to 40) and Tyrael's
     Act IV → V travel (word 28's branch, packet 0x48 on word 28);
  4. **level-entry (e3) and item-use (e9) quest steps** reachable by a waypoint hop or in town, from a save holding
     the item or set before the entry; the reverser lists the candidates from § 7–§ 10 first;
  5. **cheap travel remainders:** a town portal refused in a town; a death and resurrection (packet 0x41) from
     `QuestDeath` if the driver can be killed within the budget;
  6. unit tests in `tools/test_quests.py` for part 2's checker rules (talk steps, saved words, NPC 266's handler runs,
     word 40's map) and part 3's.
- **Out of this plan** (named shortfalls, `[I]`): the 150-travel, 150-warp, 60-activation and 20-`NpcActTravel`
  floors beyond the above; level 120's warp tiles and `QUESTS_WarpGate`'s 118/128 branch; the gates into 73, 100 and
  132; NPC 377 (no stock placement); Nightmare; classic Acts II and III; kill-triggered and far-operate steps; the
  Durance, Arcane and lair portals; the Compelling Orb's refusal (the client sends no operate); Hratli's `InitFn`s,
  `InitFn` 52 and the Tristram portal; the owner-play steps unless the owner plays them before part 3's review
  (backlog entry to the owner, optional).

### Phase 3 — Spec: quests
- **Owner skill:** spec-writer
- **Start:** after the part 2 review (2026-10-19), in parallel with Phase 2 part 3: the statements part 3 targets are
  written `[I]` and re-tagged from part 3's reviewed raises before the Phase 3 review, which waits for part 3's.
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
- **2026-10-16 — Phase 0 reviewed (architect, `lane/p42a`): accept with fixes**, applied on the lane after merging
  `main` (`134d9df`; backlog conflict kept both sides). Re-runs: `gate.py --full=travel,quest,excel_layout` green (fast
  tier 0 errors, 101 warnings; three surveys equal to their baselines); `test_d2s.py` 44 tests OK; `quest_saves.py
  check workspace/merged/data/global/excel` 14 recipes, 0 bad; `travel_survey.py summary` equal to the `travel`
  baseline. Spot-checks, recomputed from `levels.txt` and `objects.txt` apart from the survey: the 39 waypoint indices
  and the per-act level lists, the 24 `QuestFlag` levels and the one differing row (39: 26 / 40), the 16 `Portal`
  and 18 `Position` levels, the 12 + 1 `SubWaypoint` cells, `Teleport` (0 and 73) and `Quest` (8, 74), the 16
  waypoint rows (`InitFn` 17, `OperateFn` 23, `OperateRange` 2, `Restore` 1, `PopulateFn` 0/2/3), the town portals,
  bit-4 rows and the four `OpenWarp` rows. All match but one label: the Objects table said "Id" for the record index,
  and 410 `Siege Control` has `.txt` `Id` 408 (fixed). The seven handler entries were reread from `g_ObjInitFns` /
  `g_ObjOperateFns` with r2 and match. Tags are honest: data counts `[C]`, readers `[I]` with anchors, the unread
  columns `[L]` (table docs, not specs). Rulings on the five points:
  1. **`DurancePortalOperate`: the name stays for now, the doc's `[L]` is replaced.** Read at the review (objdump):
     the handler reads neither the class nor `Parm0`. It takes the level of the operated unit's room, tests word 22
     bits 13 and 0, and calls `DuranceActTravel` with that level, which does the Act IV travel only on level 102 and
     otherwise calls `0x005BCFD0`; the waypoint-103 mark and the move to 103 are gated on 102 too. So 410 would take
     the `0x005BCFD0` path. Renaming is the reverser's (`re/symbols.csv`), after reading `0x005BCFD0` in Phase 1
     (backlog).
  2. **Raw handler addresses: accepted.** They are data (the u32 the index selects, read twice), the archivist does not
     name functions, and Phase 1 names them; the request was missing `OperateFn` 34 (`0x005846B0`), added (backlog).
  3. **Built removal-item states: accepted as inputs.** The saves are built inputs (no claim that stock play reaches
     word 10 or 18 clear with those items held; d2s.md says so). What they test is the code's branch; Phase 2 should
     also run the counter case (word set, items held) from the same recipe, so the gate is seen both ways (backlog,
     with the reverser's Phase 1 reading).
  4. **Start-act byte in all three difficulties: accepted** on the vendor-save precedent (loaded, run:2026-10-15-vendors).
     d2s.md now states the two consequences: the map seed is reused in any difficulty, and the first save-back keeps
     only the played byte, so Phase 2 starts each difficulty from a fresh copy.
  5. **The four `SubWaypoint` levels: settled, not `[L]`.** drlg/outdoor (reviewed) calls `OutWaypointPlace` on
     levels 3–6 and 42–44 only (objdump finds four call sites, one in Act I, three in Act II), and the `SubWaypoint` pass needs the room bits it sets; on 2, 7, 41 and 134 (and on
     46, whose waypoint has an index) the column is never applied. Levels § Travel restated, `[C]` (134's branch `[I]`).
  Loading the 14 saves stays the first step of Phase 2 (plan 0034 precedent). Phase 0's *Done when* is met but for
  the load; Phase 1 may start.
- **2026-10-17 — Phase 1 and Phase 1b done (reverser, `lane/p42r`, static).** No game run, no slot; Ghidra on the
  lane's copy (`ghidra-p42r`), objdump for the instruction-level reads. The quest code was decompiled whole
  (`[0x00543400, 0x00548200)`, `[0x00586E00, 0x005A0000)`, `[0x005B3000, 0x005BE200)`) and read in four passes (Act I,
  Act II, Act III, Acts IV–V) beside the core and travel reading; every bit write was checked at the pushed constants of
  its call (1592 calls of the five record functions scanned; the 353 setter sites the findings cite all match). Findings:
  [quests/0001](../findings/quests/0001-progression.md) (core § 1–6, per quest § 7–10, draws § 11, creation readers
  § 12, boundary § 13, function index § 14; 142 `[I]`, no `[C]`; 14 lead verdicts) and
  [quests/0002](../findings/quests/0002-travel.md) (48 `[I]`, one `[C]` restating drlg/0005's run; 11 lead verdicts);
  [quests/experiments](../findings/quests/experiments.md) (empty heading). **601 symbols** added (subsystems
  `quests/progression` and `quests/travel`; about 530 are per-quest callbacks, listed by name in quests/0001 § 14);
  types in `re/types/quests.h` (`QuestDesc`, `QuestObject`, `QuestControl`, `QuestEvent`, `QuestTimer`, `PlayerTravel`).

  | Done-when item | Answer | Anchor |
  |---|---|---|
  | registry | 37 + 4 quest objects (ids 37–40 the NPC introductions, inactive), act, word, init, source file; callbacks e0–e12 at `+0xA0`, first/later join `+0xD4`/`+0xD8`, log state `+0xE8`, NPC gate `+0xEC`, chain `+0xF0`; dispatch runs from object 40 down to row 0 | 0001 § 1 `[I]` |
  | event kinds | e0 talk start, e2 talk end, e3 level change (old/new level), e4 item placed, e5 item dropped, e8 hooked death (forced for a fixed superunique/boss list), e9/e10 a leaving player, e11 NPC message (packet `0x31`), e13/e14 joins; e1, e6, e7, e12 never raised; timers every 20th frame (period *p* → *p* + 1 boundaries) | 0001 § 2, § 5 `[I]` |
  | per quest | bit tables with setter, trigger, readers, classic/expansion and difficulty branches, rewards, timers, objects | 0001 § 7–10 `[I]` |
  | game-wide flags | the game record: bit 13 per quest "this game's step done", bit 15 "creator had it done", word 4 bit 11 the cow portal; the first joiner's finished quests are **deactivated for the game** | 0001 § 3 `[I]` |
  | rng/seeds fields | act `+0x094` = the true tomb (quest 12's entry step, the join's tomb index, the lair portal pair); `+0x484` maze only; `+0x474` the Kurast gates only; the level-27 bit no quest code | 0001 § 12 `[I]` |
  | NPC interaction | e11 handlers keyed by `{NPC class, message id}` from packet `0x31`; e0/e2; `NPC_MenuAction`'s imbue, socket, personalise, Hell respec (word 41) and travel; packet `0x58` sets bit 12 (log seen) for any word < 42 | 0001 § 6 `[I]` |
  | travel | waypoint activation = operate (every click sets the bit; five `Sync` 0 rows draw their seed); travel packet `0x49` (10 000 ms real-time gate); NPC act change (words 6/14/26, moved before the words are written); Durance portal; town portal (item `pSpell` 2, one pair per player, town end at the town's type-11 point, five draws; use: party and `QuestFlag`/`QuestFlagEx` gates, 5000 ms gate, owner closes from the town end); warps (`WarpExitPos`, quest gates into 73, 100, 118/128 from 120, 132); death and join placement; `ActLevelSpot` + `COLL_FindFreeNear` (pseudocode) | 0002 `[I]` |
  | draws | quest seed: cairn order, eclipse timer, NPC 331 talk, Dark Wanderer, Anya's reward, the Zoo (+ plan 0032's item draws); **player unit seed: NPC 266 and NPC 377 talks**; travel: the destination's level seed on `Position` levels (every point type but 13), the portal pair's game/object/level seeds, the Sync-0 waypoints; all else none | 0001 § 11, 0002 § 10 `[I]` |
  | creation readers | Hratli InitFns 49/50, InitFn 52, the Tristram portal, Diablo's `+0x13` (Chaos gate), Nihlathak's boss after Anya, the Zoo, the warp gates, the portal quest gate | 0001 § 12 `[I]` |
  | Phase 0 requests | `QuestFlag`/`QuestFlagEx` read by the portal operate (destination level, bit 0); `Portal` (leveldefs `+0x8C`) no reader found; `OperateFn` 15/23/34/43/46 and `InitFn` 11/12/17/29/44 read; `0x005BCFD0` re-opens the Act III bridge and moves nobody, object 410 is never placed (`DurancePortalOperate` keeps its name); the Meshif and Durance removal branches both ways (below) | 0002 § 5–6, 0001 § 10 |

  **Surprises.** (1) The game creator's finished quests are switched off for everyone in the game. (2) NPC talks draw:
  NPC 266 and 377 on the player's unit seed, NPC 331 on the quest seed. (3) Every placement on a `Position` level
  (towns included) steps that level's seed, so waypoint, NPC, portal, death and join arrivals chain with the
  population pass. (4) Real time: the waypoint 10 s and portal 5 s gates and Diablo's end-of-game timer read
  `GetTickCount`. (5) Warps out of the Arreat Summit (to 118 and 128) are refused until the Ancients die.
  (6) The NPC act travel moves the player before it writes the travel words, and NPC 520 (`cain6`) takes a player back
  to Act IV. (7) Word 33 has no writer; rows 7 and 29 share one init (word 29); row 24's init writes word 16.

  **Phase 1b.** Registered `src:arreat-summit-quest-acts` (Quest Basics, act pages I–V) and
  `src:arreat-summit-basics-travel` (Basics' waypoint and portal sections, PvP); three other pages refused the fetch.
  25 verdicts: 6 held, 15 held with refinement, 3 not covered, 1 **contradicted** (the 10-second hostility delay holds
  for waypoints, the portal gate is 5 s). The contradiction is multiplayer only (no hostility with one client), so it is
  not a required Phase 2 case; backlog entry for plan 0044.

  **P2 harness questions** (every line logs `game +0xA8`; the saves are Phase 0's in `workspace/runtime/quest-saves-p42/`
  and plan 0032's; **two slots**: slot A expansion, slot B classic and the Nightmare/Hell runs):
  1. *Dispatch log:* at `QUESTS_DispatchEvent` / `QUESTS_DispatchUnitEvent` entry the block (`+0x04`–`+0x18`), and at
     each callback entry the quest id; at every `QUESTRECORD_SetState`/`ClearState` and `GameQuestSet` the record
     owner, word, bit. The checker predicts each write from the event (0001 § 7–10) and the callback order (object 40
     → row 0). Saves: `questfresh`, `questfreshc` (classic), `questfreshv`.
  2. *Join:* at `QuestsPlayerJoin` entry/exit the joiner's record, the game record and each object's `+0x09`/`+0x0A`;
     predict the deactivations and bit-15 marks. Cases: a `quests: all` creator (`travel-wp1`), a fresh creator
     (`questfresh`), a creator with word 9 bits 0 and 5 and no `ass` (word 9's clear; a built save).
  3. *Per quest*, one Normal expansion pass, each step from the Phase 0 recipe nearest it: the e11 message ids and the
     bits written, the party/near-room credit (one client: the actor and level-wide credit only), and the `Save and
     Exit` words compared word by word. Ten quests again in Nightmare/Hell; Acts I–IV classic (`questfreshc`): Diablo's
     classic bits 6/7 and the status raise, the cube and trade refusal after Diablo.
  4. *Quest-seed draws:* the quest seed in and out of `0x00592E90` (cairn order: ≥ 5 steps, the five classes),
     `0x0059EDC0` (eclipse period 15–17), `0x0059B1C0` (NPC 331, `mod 3`), `0x005BD390` (Dark Wanderer), `0x00589937`
     (Anya), `0x0058E830` (the Zoo, 1–10 draws, the `zoo` row); chained pairs ≥ 20 for the NPC 331 talk.
  5. *Player-seed draws:* the player's unit seed around each talk to NPC 266 (Act I) and NPC 377 (Act II): one step per
     talk, the branch by G1:13 / word 1; ≥ 20 chained pairs each.
  6. *Timers:* `QUESTS_TimerAdd` (fn, period, tick) and each run of `QUESTS_TimersRun`; predict run frames
     (`frame mod 20 = 0`, *p* + 1 boundaries).
  7. *Creation readers:* InitFn 49/50 (Hratli) both ways of G16:13; InitFn 52; the Tristram class-60 portal when quest
     4 is inactive (`travel-wp1`); Diablo's `+0x13` at `sub_005B5210_DiabloQuestFlag` with the seal/boss order both
     ways; the warp gates into 73, 100 and 132, and **120 → 118 refused before the Ancients** (the Phase 1b case); the
     portal `QuestFlag` gate (needs two players: plan 0044, or logged as unreached).
  8. *Waypoints (60 activations, 150 travels):* `WaypointOperate` (object mode before/after, record bit), packet `0x49`
     (tick stamp vs `GetTickCount`), `WaypointTravel` (type 0 or 13), `ActLevelSpot` in/out (level seed `+0x1C4`,
     point, free cell), `COLL_FindFreeNear` with a collision snapshot; the five `Sync` 0 Act V rows (object seed
     draws). Saves `travel-wp1`..`5`, `travel-wpnone`, `travel-tab2`, `travel-tab5d`, `travel-arcane`.
  9. *Act changes (20):* `NPC_MenuAction` action and NPC class, `NpcTravelMove`, `PlayerChangeAct` (both free
     searches, mask `0x1C89` step 5), the destination level seed, the words and waypoint set after the move, player data
     `+0x4C` and its clearing. Saves `travel-act2`..`5`; the counter cases (word 10 or 18 already set with `msf`/`vip`
     or the five Khalim items held: nothing removed).
  10. *Town portals (60):* `ITEMUSE_TownPortal` (refusal in town and on 136), both `SUnitCreate`s (game seed), both
      `UNIT_AnimInit` draws (field 25, partner 25), `LevelPointPick` on the town (type 11), the partner's step-5 search;
      `OBJOP_Portal` both ways (field → town, town → field by the owner: both freed), state 102 for 75 frames, the
      second scroll closing the first pair; a portal on level 120 resetting the Ancients.
  11. *Warps (150 level entries):* `WarpExitPos` (paired warp, free cell, `ExitWalkX/Y`), the walk command's
      `0x0057EEC0` (no draw without state 42).
  12. *Death and join placement:* packet `0x41` (type 0 in town, level-seed step), `sub_005394A0_PlayerPlaceInAct`.

  **Boundary recommendation:** quests/0001 § 13 and quests/0002 § 11 (event entry points; triggers, dialogue message
  ids, party, rooms and `GetTickCount` as inputs; spawns, item creation, DRLG builds and room activation as oracles).

  **Points for the review.** (a) Everything is `[I]`; the per-quest tables come from four parallel passes over one
  decompile, each bit write machine-checked against its call's constants; spot-check a few rows per act. (b) The
  join's deactivation of the creator's finished quests (0x005462C0–0x0054634A) and the forced-death list. (c) The
  NPC-talk draws on the player's seed (0x00596B23, 0x0059E1CE) and the six quest-seed sites (five non-item, plus Anya's reward, an item draw items/0010 already had). (d) The
  `Position`-level seed step for every point type but 13 extends drlg/0005's `[C]` (type 11) to types 0 and 5 as `[I]`.
  (e) Real-time gates as inputs. (f) The contradicted lead (portal 5 s) and its reachability. (g) The research-map rows
  `quests/progression` and `quests/travel` are still to be added (architect).
- **2026-10-17 — Phase 1 and 1b reviewed (architect, `lane/p42r`, `main` `1083b92` merged in as `4ebe5a2`): accept
  with fixes; Phase 2 opens.** Merge: `docs/backlog.md` kept both sides, then `tools/backlog.py migrate` (the
  lane's three entries became files); `re/symbols.csv` kept both sides. Five addresses were named on both sides
  (plan 0039's p39b on `main`, this lane): `0x0058C6D0`, `0x0058C7E0`, `0x0058C9A0`, `0x0058CE30`, `0x005BBBA0`.
  `main`'s names are kept (`sub_0058C6D0_A5Q5_PartyExpGrant`, `sub_0058C7E0_A5Q5_SummitExpGrant`,
  `sub_0058C9A0_A5Q5_AncientDeath`, `sub_0058CE30_A5Q5_Init`, `sub_005BBBA0_ObjInitCompellingOrb`) and quests/0001
  § 14 cites them; the lane's symbols are **596** after the merge (560 `quests/progression`, 36 `quests/travel`).
  Gate green (fast tier 0 errors; the 31 W1 lines of the two findings are filed below).
  **Re-run of the bit-write scan** (my own objdump of the pinned `Game.exe` and a scanner written for the review, not
  the lane's dump): the five record functions have **1592** calls (`GetState` 1149, `SetState` 332, `ClearState` 46,
  `GameQuestSet` 40, `GameQuestGet` 25; the game-record pair takes ECX game, EDX word and a pushed bit). Every
  setter or clearer cited in a § 7–§ 10 bit table was checked against its call's word and bit: **353 of 353 agree**
  (39 take the word or bit in a register and agree on the constant half). Of the 411 writer calls in the three quest
  ranges, 52 are not cited by call address; each sits in a function the tables cite (party credit, `StepBits`, the
  `NpcActTravel` travel words), so the tables are complete at function level. **Trigger spot-checks**, three or more
  per act, read in objdump: Act I word 1 (`0x0058FDD0`: NPC 148, message 0x40 / 0x4C, bit 1 → bit 0, 41:13/41:1,
  stat 5 + 1), word 4 (Gibbet party credit `0x005930B0`), NPC 266's `Range(player seed, 2)` (`0x00596B23`); Act II
  word 14 (`0x0059CD2F`, message 0x1BA with b3 → b4 set, b3 clear; `0x0059CE06` b0, `hst`/`vip`/`msf` removed, G14:13),
  NPC 377's inlined LCG on `Unit+0x20` (`0x0059E1CE`); Act III W16 (`0x005B6F09`, G16:13 `0x005B6F18`), the orb operate
  (`0x005BB980`), row 24's init (`0x005BD368` writes `+0xE0` = 0x10 while `g_QuestDescs` row 24 names word 0x20, read
  from the image); Act IV word 24 (`0x005B36A0`: class 0x16F, message 0x298, bit 0); Act V word 37 (`0x00589580`:
  class 0x201, messages 0x4E94/0x4E9F/0x4EA4, bit 8 at `0x005896F1`, bits 0/1 when 9 is set), the summit gate
  (`0x0058D090`, `QUESTS_WarpGate`'s jump table: 73, 100, 118 with source 120). All agree except the orb (below).
  The 596 symbol addresses are all function starts (595 by a linear sweep; `0x005B8150` after a jump table, read
  at its own address). **Rulings:**
  - (a) **Per-quest tables: accepted.** The four-pass merge holds at the instruction level (above). One trigger was
    misread: the orb's hit counter only advances when the operator holds `qf2` (`0x005BB9B3` exits before the
    increment at `0x005BB9CD`), so both counted operates need `qf2`; quests/0001 § 9 and the summary corrected.
  - (b) **The join: confirmed as read, its consequence corrected.** `0x005462C0`–`0x0054634A` deactivates each flag-0
    descriptor whose word has bit 0 or 15 in the first joiner's record (when `rejoin` = 0 and byte `0x0073150C` is
    set) and sets bit 15 of that word in the game record. But "only forced events still reach it" was wrong: every
    raiser of `QUESTS_DispatchEvent` pushes force 1 (e0 `0x00543D2A`, e2 `0x00543D5C`, e3 `0x00543BA2`, e10
    `0x00543C96`, e11 `0x005443FA`, the re-dispatch `0x005457BF`); only the hook events (e4, e5 at `0x00543D8A`, e8
    outside the forced list) skip a deactivated quest. The handlers' own state tests keep it inert. quests/0001
    summary, § 3 and the first Phase 1b verdict rewritten; P2 question 2 adds the observation (below).
  - (c) **NPC-talk draws: confirmed as read.** `0x00596B23` is `RNG_Range(&player+0x20, 2)` when word 1 bits 0, 13, 1 are
    clear; `0x0059E1CE` steps the LCG on `player+0x20` (`Unit+0x20` is the unit seed, combat/0001). The six
    quest-seed sites: items/0010 § 1 lists five non-item sites (`0x0058E830`, `0x00592E90`, `0x0059B1C0`, `0x0059EDC0`,
    `0x005BD390`), and quests/0001 § 11 places exactly those five; Anya's (`0x00589937`) is an item draw items/0010
    already had (its NPC reward table), so the log's "six non-item" is corrected to five plus Anya's.
  - (d) **The `Position` step for types 0 and 5: accepted at `[I]`.** `LevelPointFind` (`0x0066B2B0`) tests only
    `type == 13` (`0x0066B303`) before `LevelPointPick(type)` on a `Position` level, so types 0, 5 and 11 run the same
    code drlg/0005 confirmed for 11; the argument differs, so it stays `[I]` until P2 sees each type step the seed.
    **The five-draw portal open: accepted at `[I]`.** `PortalObjectCreate` calls `SUnitCreate` (`0x0056D249`), then
    `SetMode(1)` (`0x0056D25C`), then `PortalPartnerCreate` (`0x0056D270`), in the order the finding gives.
  - (e) **Real-time gates as inputs: accepted.** Both read `GetTickCount` (import `0x006CC260`; `0x0054C601` + 10 000,
    `0x005848C1` + 5000). The stamp is written only by `0x0055B720`, whose one caller is `0x005A5E50`, so with one
    client the gates pass unless that path ran. P2 logs the tick and the stamp at each gate as inputs, never frames.
  - (f) **Summit warps: accepted as `[I]`, a required P2 case.** `QUESTS_WarpGate` sends 118 with source 120 (and 128) to
    `0x0058D090`, which returns 1 while quest 35 is active (`+0x09`) and its private "done in this game" byte is 0.
    With the join ruling, a creator who has finished the Ancients has quest 35 deactivated, so the warp is allowed:
    P2 runs both.
  - (g) **NPC 520 to Act IV: confirmed as read** (`0x0057A7C3`: class 0x208, `action` 0, `NpcTravelMove(0x67, 5)`). The
    summary's "with no test" now says "no quest-word test (264 and 520 only for action 0)".
  - (h) **Word 33 and row 24: confirmed, one overclaim.** No constant-word setter names word 33 (my scan agrees), but
    packet `0x58` sets bit 12 of any word < 42, so "word 33 has no writer" becomes "no quest script writes word 33".
    Row 24's `+0xE0` = 16 against word 32 is confirmed from the image (above); presentation only, as the finding says.
  - (i) **The contradicted lead: routed to plan 0044.** Both stamps come from `0x005A5E50` alone, so the waypoint
    "held" and the portal "contradicted" both depend on `0x005A5E50` being the hostility declaration, itself a lead.
    The two verdicts (and "going hostile closes the portal") now carry that condition; plan 0044's case list gets the
    case (its log, 2026-10-17). Not a 0042 Phase 2 case.
  - (j) **Symbols: 596 rows accepted as `I`.** One row per function a finding cites by name (§ 14 lists every one), all
    function starts, `sub_<addr>_<hint>` with an `A<act>Q<n>_` hint or a `QUESTS_`/`OBJOP_`/`OBJINIT_`/`ITEMUSE_` prefix
    for the 42 core ones, no duplicate address or name against `main` after the merge, no W3 among them. The volume is
    the plan's own estimate (ADR-0017: quests are hardcoded, one set of callbacks per quest); naming the callbacks is
    what lets P2's logger and the spec cite them.
  - **P2 questions: accepted with five additions.** (i) Question 2 also logs a deactivated quest's forced e0 and e11
    handler calls (handler runs, `+0x09` = 0, no bit written). (ii) Question 3 adds an orb operate without `qf2` (no
    count) and a packet `0x58` on word 33 (bit 12). (iii) Question 7's summit case runs both ways: a creator without
    word 39 bit 0 (refused) and one with it (quest deactivated, warp allowed). (iv) Questions 8, 9 and 12 each assert
    the destination level seed per point type: 0, 5 and 11 step once on a `Position` level, 13 not at all. (v) The
    gates of question 8 and 10 log `GetTickCount` and the stamp; with one client the stamp is expected unchanged.
    **Slots:** two (A expansion; B classic and the Nightmare/Hell runs), as the plan allows. **Boundary:** accepted as
    recommended (quests/0001 § 13, quests/0002 § 11).
  Research-map rows `quests/progression` and `quests/travel` added under *Game rules (ADR-0017)*. The review request
  and the contradicted-lead entry are closed; the two 2026-10-16 requests to the reverser (Phase 0 additions, the
  column readers) are answered by the Phase 1 table above and closed. Follow-ups filed: the 31 W1 lines and three
  static leftovers to the reverser (backlog).
- **2026-10-17 — Phase 2 (reverser, `lane/p42h`, slots 1 and 2; review requested).** run:2026-10-17-quests
  ([experiments](../findings/quests/experiments.md#run2026-10-17-quests)): 11 sessions, **0 mismatches over
  16 199 checks** under `tools/quests.py check`. Tools: `tools/gdb/questev.py` and `quest-state.gdb` (the logger,
  beside plan 0032's `quests.py`), `tools/quests.py` with `tools/test_quests.py`, `tools/quest_sessions.py` (sessions,
  actions, the save loads), recipe `quest-tpc` (classic, a tome of town portal), three NPC rows in `d2pilot.py`.
  Raises and corrections: [quests/0001 § 15](../findings/quests/0001-progression.md#15-phase-2-run2026-10-17-quests),
  [quests/0002 § 12](../findings/quests/0002-travel.md#12-phase-2-run2026-10-17-quests).

  | Required case | Result |
  |---|---|
  | quest-seed draws chained (≥ 20 pairs) | NPC 331 (Kaelan): 42 chained pairs, one step per talk (Normal 21, Nightmare 21) |
  | player-seed NPC talks 266 and 377 (≥ 20 pairs each) | **shortfall**: neither NPC was in a server unit list (266 `navi` is the Blood Moor's preset centre monster, absent from the run's map; 377 never placed in the towns walked) |
  | town portal open, five draws | **corrected**: three draws (62 opens): gs, the town's level seed (type 11), gs; both ends are created in their mode, no object-seed draw; the town room's first update draws gs for its population (oracle) |
  | level seed per point type: 0, 5, 11 once, 13 never | 0: 22 one step; 11: 334 one step; 13: 28 no step; 5: 11 lookups on level 1, none steps (no group-1 point there: point 0, no draw), a stepping type-5 case not reached |
  | every other kind: seeds unchanged over ≥ 20 events, or named | ≥ 20 events with gs, qs, ps unchanged: waypoint operate 61, waypoint travel and packet 0x49 61 each, portal use 122, summit door 73, packet 0x58 53, NPC move 22, `PlayerChangeLevel` 81, `PlayerChangeAct` 32, `ActLevelSpot` 154, `LevelPointFind` 2 356 (its own level seed predicted apart), dispatches 459 of 503 (the other 44 the Kaelan talks' predicted quest-seed step). Under 20: NpcActTravel 11, packet 0x48 1, warps 2 (named shortfalls); death (packet 0x41), the Durance, Arcane and lair portals: none |
  | summit warp, both ways; 120 → 118 refused | the way back from 120 is the summit door (`OperateFn` 71), not a warp tile: refused for both creators (37 operates without word 39, 36 with every quest done); the door reads quest 35's private "done in this game" byte only, which is 0 in a new game whichever creator; `QUESTS_WarpGate`'s 118/128 branch never ran. Ruling (f)'s "allowed" half does not hold for the door |
  | a switched-off quest's forced e0/e11 handlers without a bit write | 4631 forced callbacks of deactivated quests ran, in 334 dispatches; in 290 of them nothing was written; **quest 11's e11 handler writes word 12 bit 8 while switched off** (44 writes), a correction |
  | orb operate without `qf2` | **shortfall**: the scripted walk to the Kurast Docks waypoint failed (x-orb) |
  | packet 0x58 on word 33 | **shortfall**: the stock client sends 0x58 only for the quest-log entries it shows (26 words, each bit 12 set); word 33 has none |
  | tick and stamp at both gates | 61 packet-0x49 and 122 portal gate reads, stamp 0 each (one client), the pass rule exact |
  | two-player cases (portal party gate, party credit) | out of scope: plan 0044 |

  **Not reached** (Phase 2 done-when): no quest completed (question 3's per-quest pass, the Nightmare/Hell and classic
  quest runs, the `Save and Exit` word comparison beyond the loads); 60 activations (every waypoint met was already in
  mode 2; the Spider Forest walk of x-wpnew did not reach its waypoint); 150 waypoint travels (61); 150 warps
  (2); 20 NPC act changes: 22 (11 each way, Warriv), reached; Hell (the scripted walk to the town waypoint failed
  in five Hell launches, kept as development logs); timers; deaths; the creation readers of question 7 but the door.
  **The saves load:** 18 of the 18 built saves loaded and wrote back (Normal); the quest-word changes are word 40
  bit 10 set by the join (quest 36's first-join callback, `0x0058E4D0`) in the saves with word 40 done, and word 9
  cleared in `QuestBookLost` but kept in `QuestBookHeld` (the word-9 first-join check both ways); `TravelWpNone`
  comes back with waypoint 0 set in all three difficulties. Hashes not pinned in `test_d2s.py`
  (archivist's, backlog).

  Logger revisions and development logs are listed in the run record. Slots 1 and 2 stopped, asides restored.
- **2026-10-17 — Phase 2 part 1 reviewed (architect, `lane/p42h`, `main` `e6f365b` merged in): accept with fixes;
  Phase 2 stays open for part 2.** Merge clean (no `docs/backlog.md` or `re/symbols.csv` conflict; `backlog.py migrate`
  moved nothing; gate green). **Re-runs:** the manifest checks (11 of 11 OK); `tools/quests.py check` over the 11 logs
  under `systemd-run --user --scope -p MemoryMax=4G` gives `SUMMARY mismatches=0 checks=16199 logs=11`, output
  byte-identical to `quests-check.txt` (`6b2c787f…`); `tools/test_quests.py` 7 tests OK; the checker over each of the
  20 development logs, 0 mismatches over 4 677 checks (outside the record, raises nothing). **objdump spot-checks**
  (pinned `Game.exe`): the logger's dispatch call and exit points (`0x00543965`/`0x00543974`, `0x005439F9`/`0x00543A05`),
  both gates (`0x0054C60F` `stamp + 10000`, `0x005848CD` `stamp + 5000`, each `jbe` on `GetTickCount`), the portal
  pair (`0x0056D237`–`0x0056D249` pushes mode 1 to `SUnitCreate`, `0x0056D083`–`0x0056D092` mode 2; `UNIT_SetMode`
  returns at `0x006246A9` without drawing when the mode is unchanged; `ActLevelSpot` type 11 at `0x0056CF6E` before
  `RoomUpdateOne` at `0x0056CF7D`), the summit door (`0x0058D6A0`: `GetQuest(35)`, `+0x18` byte only, message 0x13
  at `0x0058D711`; no `+0x09` read, while `0x0058D090` reads `+0x09` at `0x0058D09A`), quest 11's e11 handler
  (`0x0059AF84` class 0x14B, 0xBA → word 12 bit 7, 0xBB–0xBD → bit 8, no `+0x09` test), `LevelPointPick`'s `n = 0`
  exit (`0x0066AC90`) and `NpcActTravel`'s word-7 branch (`0x00546991` exits before the `+0x4C` write at `0x005469CD`).
  **Rulings:**
  - (a) **Part 1, with a planned part 2.** The run is sound and its corrections stand, but most of the done-when is
    unmet (no quest completed, no activation from mode 0, 61/150 travels, 2/150 warps, no Hell session). Accepted as
    **Phase 2 part 1**; **part 2** is defined in the Phase 2 section above (what it must do, the owner-play
    candidates, the named shortfalls now) and filed to the reverser. Phase 3 waits for part 2's review.
  - (b) **The summit door: correction accepted, scoped.** The door (object 564, `OperateFn` 71) reads only quest 35's
    private "done in this game" byte, so it refused for both creators (37 operates by `QuestSummit`, 36 by
    `TravelWpFive`): `[C]` (code and run). P1 ruling (f)'s "allowed" half is **split**: false for the door; for
    `QUESTS_WarpGate` (`0x0058D090` returns 0 when quest 35 is switched off) it stays `[I]`, unreached. The lane's
    "the way back from 120 is the door, not a warp tile" is narrowed: level 120's warp tiles (WRP rows 82 and 83) were
    logged and never taken (part 2, item 4). quests/0001 § 10's "the summit door the same" (as the Keep door) and the
    P1b verdict on the summit warps are corrected to match.
  - (c) **Town portal, 5 → 3: accepted `[C]`, with its oracle boundary stated.** Both ends are created in their mode
    (the pushed mode argument, `omode` logged), so the `SetMode` calls draw nothing; the draws are game seed, the
    town's level seed (type 11), game seed. The town room's population (`RoomUpdateOne`) is a boundary oracle between
    the two creations: its entry is the asserted field-end state, its exit is logged by logger revisions B and C (4
    opens). In the 5 revision-A opens with population draws (x-lut 3, c-tp 2) the exit is derived from the partner's
    seed, so those 5 do not test the partner's draw; the `[C]` rests on the other 57. The open is a one-shot function
    (ADR-0017), so its evidence is ADR-0003/0004's (entry as input, every draw asserted to the exit) and ADR-0014's
    chaining floor does not apply to it.
  - (d) **Quest 11's e11 handler: correction accepted `[C]`** (code and 44 writes): "a deactivated quest's handlers
    stay inert" is per handler, `[C]` only for the handlers and states the run reached.
  - (e) **Raises.** Accepted: the Kaelan quest-seed step (42 chained pairs), the forced raisers, packet 0x58 for the
    words the client sends, placement (124), the level-seed step per point type (0, 11 one step; 13 none; type 5 as a
    no-draw case), the portal-use, waypoint and gate "no draw" rows, the `+0x4C` narrowing (anchor corrected to the
    word-7 branch). **Scoped:** the dispatch order is raised in part (all 503 dispatches forced; the unforced
    `+0x0A` skip stays `[I]`); the join is `[C]` for the branch reached (first join, `rejoin` 0, byte set, 11 of 11);
    the free-ring search stays raised in part. **Not raised:** packet 0x48 (1 case) and warps (2, under the 20-event
    floor): the rows said "raised in part", now "not raised".
  - (f) **The kept logs: yes, with two manifests added.** The 20 development logs are kept and listed, and the 18 load
    logs, the 18 written-back saves and `loads.txt` are kept; none was hashed. The review added
    `workspace/logs/quests/dev-manifest.sha256` (`fc16bedc…`) and `loads/loads-manifest.sha256` (`017a6997…`),
    cited in the record. Pinning the load hashes in `test_d2s.py` stays the archivist's (backlog).
  **Fixes applied (14):** overclaim 4 (dispatch unforced half; join branch; the "door, not a warp tile" claim and
  ruling (f)'s split; packet 0x48 and warps "raised in part" → "not raised"), miscount 4 (290 dispatches not callbacks; 73 = 37 + 36 operates; five Hell launches, not four;
  eight saves with word 40, not nine), stale cross-reference 2 (quests/0001 § 10's "the summit door the same"; the
  P1b summit-warp verdict), wrong anchor 1 (`0x0054684A` is word 28's branch; Warriv's is `0x00546991`), misread 1
  (quests/0002 § 12 listed a Hell session), omission 1 (the portal oracle's revision-A boundary), tool not kept 1 (no
  manifest for the development and load logs). The review request is closed; part 2 is filed to the reverser.
- **2026-10-19 — Phase 2 part 2 checkpoint (reverser, `lane/p42q`, slot 2; in progress).** run:2026-10-18-quests2:
  18 recorded logs so far, 0 mismatches under the extended `tools/quests.py check` (part 1's 11 logs still 0). Done:
  warps (104), NPC-talk steps of Acts I–IV in Normal, five Act I and four Act III steps in Hell, Act I in classic,
  saved words after *Save and Exit* (12 sessions), the Compelling Orb with `qf2`, NPC 266 (two player-seed steps per
  talk, a correction), the stub character's double join. Running: activations (`x-wpact3`), `h-talk4`, `c-talk4`,
  `x-talk5`. **Resume note:** the driver now supervises each session (watchdogs) after an overnight hang on
  2026-10-18/19 (the machine suspended; the game exited and the driver clicked on); sessions are listed at the end of
  `tools/quest_sessions.py`; `workspace/scratch-p42q/agg.py` lists the talk steps per log; the finding sections hold
  `@@` markers for the activation row and the shortfalls until the final pass.
- **2026-10-19 — Phase 2 part 2 (reverser, `lane/p42q`, slot 2; review requested).** run:2026-10-18-quests2
  ([experiments](../findings/quests/experiments.md#run2026-10-18-quests2)): 21 recorded sessions, **0 mismatches over
  23 348 checks** under the extended `tools/quests.py check`; part 1's 11 logs unchanged (manifest 11 OK) and 0 over
  16 204 under the same checker; 11 development logs 0 over 2 480. Raises and corrections:
  [quests/0001 § 16](../findings/quests/0001-progression.md#16-phase-2-part-2-run2026-10-18-quests2),
  [quests/0002 § 13](../findings/quests/0002-travel.md#13-phase-2-part-2-run2026-10-18-quests2).

  | Part 2 item | Result |
  |---|---|
  | 1. Normal expansion quest steps, saved words | the NPC-talk steps of Acts I–V reached (words 0, 1, 2, 4, 6, 8, 9, 14, 16, 19, 20, 24–27, 35, 40), each write at its call site `[C]`; the saved words after *Save and Exit* predicted word by word in 16 sessions; steps by kill, operate, item use or level entry: **shortfall** |
  | 2. Nightmare/Hell and classic | Hell: 12 quest words in 3 recorded Hell sessions; classic: Acts I and IV (**shortfall** for II and III); Nightmare: none |
  | 3. waypoints | 47 travels (108 with part 1); 0 activations from mode 0 (**shortfall**: the walk did not reach the Spider Forest or Great Marsh waypoints) |
  | 4. warps | 104 (106 with part 1): "no draw" raised `[C]`; level 120's tiles never taken (the door answers), gates into 73/132 not attempted, 83 → 100 allowed once (**shortfalls**) |
  | 5. act travel | 1 `NpcActTravel` (Meshif east: word 15's branch and packet 0x48); Meshif west, Tyrael, more Warriv: **shortfall** |
  | 6. NPC 266 / 377 | 266: 23 talks, 22 chained pairs, **corrected** to two player-seed steps per talk; 377: no stock placement (static scan), **shortfall** with the reason |
  | 7. Compelling Orb | with `qf2`: counted half `[C]`; without: no operate reached the server (**shortfall** server-side) |
  | 8. the rest | stub double join `[C]`; switched-off reward handlers write (correction in part of § 3); `0x0065C3E0` steps clear `[C]`; word 40's message table corrected; timers, death, portal refusals, the remaining portals, Hratli's `InitFn`s, `InitFn` 52, the Tristram portal: **shortfall** |

  Owner play (boss steps, the Ancients, Diablo's `+0x13`, Uber/136) was not played: shortfalls, the owner entry stays
  open. Tools: `quest_sessions.py` (part 2 actions; supervised sessions after the overnight hang), `quests.py`
  (talk steps, saved words, orb, Durance gate, stub join, `npcplace`), `questev.py` revision D (`QK`, `NPCQ` town
  NPCs), `d2pilot.py` (Tyrael row), `quest-newchar.steps`; eleven recipes (archivist entry for d2s.md). Manifests:
  `quests2-manifest.sha256` (`29693c4b…`), `dev-p42q-manifest.sha256` (`af3aefd0…`). One slot used (slot 1 was freed
  late and not taken; a second slot would have doubled the session count). Slot 2 stopped, its aside restored. The
  part 2 backlog entry is left open for the reviewer.
- **2026-10-19 — Phase 2 part 2 reviewed (architect, `lane/p42q` at `f8469e1`, branched from `main` `c0c99f6`; `main`
  not merged in by this review): accept with fixes; Phase 2 stays open for a narrow part 3; Phase 3 may start.**
  **Re-runs:** the three manifests from one path base (`workspace/logs/quests/`): `sha256sum -c` gives 61 of 61 OK
  (`quests2-manifest.sha256`, `29693c4b…`: 21 logs, 20 installed and 17 written saves, the check, the part 1 re-check
  and the `npcplace` output), 20 of 20 (`dev-p42q-manifest.sha256`, `af3aefd0…`) and part 1's 11 of 11
  (`quests-manifest.sha256`); `tools/quests.py check` under `systemd-run --user --scope -p MemoryMax=4G` gives
  `SUMMARY mismatches=0 checks=23348 logs=21` and `mismatches=0 checks=16204 logs=11`, each byte-identical to
  `quests2-check.txt` and `quests2-recheck-part1.txt`, 0 over 39 552 on the 32 logs together, 0 over 2 480 on the 11
  development logs; `tools/test_quests.py` 7 tests OK (none added for part 2's rules). Every `[C]` row of quests/0001
  § 16 and quests/0002 § 13 names a session whose log is in `quests2-manifest.sha256` (all 21 are); the development
  logs back only the "not raised" row. **r2 checks** (pinned `Game.exe`): (1) **NPC 266, two draws per talk:** the
  init `0x00596C40` is referenced twice in the descriptor table (0x007315B8 and 0x007317C8, 0x210 apart: rows 7 and 29
  at 24 bytes a row) and writes `0x00596A90` into the e0 slot (0x00596C57) and `+0xE0` = 29 (0x00596C7E); the handler
  tests the class (266 at 0x00596AAB) and steps the player unit's `+0x20` by `RNG_Range(…, 2)` (0x00596B23) or the
  inline LCG (0x00596B48, `0x6AC690C5`): one draw per run, two runs per talk, **holds**. (2) **The reward handlers test
  the word's bits:** `sub_0058FDD0_A1Q1_NpcMessage` tests NPC 148 (0x0058FDD9), message 0x4C (0x0058FE59),
  `QUESTRECORD_GetState(word, 1)` (0x0058FE6D) and bit 13 (0x0058FE85), then `SetState` b0 (0x0058FF11), `ClearState`
  b1 (0x0058FF20) and word 41's b13 (0x0058FF2F); no `+0x09` read on the path, **holds**. (3) **Word 40's jump table:**
  `0x0058D940` adds `0xFFFFB131` (`− 0x4ECF`), bounds at 5 and jumps through 0x0058D9D0, whose six entries reach
  `push 7, 9, 5, 4, 6, 8` before the one `SetState` at 0x0058D9C7; no NPC or `+0x09` test, **holds**. Spot checks:
  `push 1` at 0x0056A3B7 (`LoadBytes` flag), the stub join's calls at 0x0056A072/0x005344EF with returns 0x0056A077/
  0x005344F4, the orb's `SetState` calls at 0x005BB9F7/0x005BBA14, word 9's at 0x00598BFE (`SetState`) and 0x00598C0D
  (`ClearState`). Recounts: 41 talk-step fires, 12 Hell quest words, eleven recipes, 104 warps, 15 door operates, all
  as stated. The driver's watchdog (`8da839d`) kills the session's own process group and relies on `slots.py stop`
  (driver kill, `wineserver -k`) for the game, which `d2run.py` starts in its own session: adequate.
  **Rulings:**
  - (a) **Part 2 accepted.** The talk-step pass is sound: 41 steps over 20 rows in Normal expansion, Hell and classic,
    each write at its call site, the saved words after *Save and Exit* predicted word by word in 16 sessions, and three
    corrections that hold in the code (above). The raises stand as scoped by the lane ("for the rows and branches
    reached"); the Compelling Orb and packet 0x48 are correctly "raised in part"; the Durance gate is correctly not
    raised on one case (reverser review-fixes 10).
  - (b) **Shortfalls acceptable as named** (no further attempt in this plan; the statements stay `[I]` in Phase 3):
    the volume floors (108 of 150 travels and 106 of 150 warps are past the 20-event floor, and both claims are
    "no draw" one-shots; raised as the lane scoped them); level 120's warp tiles and `QUESTS_WarpGate`'s 118/128 branch
    (the door answers the clicks; the open path needs the Ancients, owner play); the gates into 73, 100 (refusal) and
    132 (quest gates reached only by boss or staff steps); **NPC 377**, whose stock placement does not exist (the
    `npcplace` scan, kept): Phase 3 states its player-seed draw as `[I]` and unreachable on stock data;
    **Nightmare**: the item-2 floor is met by Hell (one recorded Hell session asked for, three recorded; 12 Hell quest
    words against ten quests); **classic Acts II and III**: classic I and IV are reached, and a row whose handler tests
    `game +0x70` keeps its classic half `[I]` unless reached in classic (word 26's 0x4E20 is the case reached in
    expansion only); kill-triggered and far-operate steps, the Durance, Arcane and lair portals, Hratli's `InitFn`s,
    `InitFn` 52 and the Tristram portal (they need combat or long walks the driver does not do reliably: the cost of a
    retry is a lane, the value a few `[I]` rows without draws); the orb's refusal (the stock client sends no operate);
    the owner-play steps (the owner entry stays open, optional; what is played before part 3's review is taken, the
    rest stays `[I]`).
  - (c) **Shortfalls that block a Phase 3 `[C]`** (the spec writes them `[I]` until part 3 raises them): waypoint
    activation from mode 0 (event 1, the `Sync` 0 object-seed draw); the type-5 lookup that steps (Meshif west);
    packet 0x48 and the word-28 branch (two cases); quest timers and the quest-seed draws not yet logged (the eclipse
    arm, Anya's reward, the cairn-stone order, the Dark Wanderer timer, the Zoo); death and resurrection (packet 0x41);
    the level-entry and item-use quest steps.
  - (d) **Part 3: needed, narrow and final** (defined above, filed to the reverser). Cost against value: a part 3
    limited to what a waypoint hop or a town talk reaches costs about one harness lane, one slot or two; its value is
    the draws of (c), which sit on the quest seed (the quest drops' seed), the object seed and the level seed, where an
    `[I]` is least safe: part 2's 266 correction was a draw count read wrong in Phase 1. Everything in (b) is left out
    of it, and no part 4 is planned: what part 3 misses stays `[I]` in this plan.
  - (e) **Phase 3 may start now**, in parallel (Phase 3 *Start* above): the travel spec and the reached talk rows do not
    depend on part 3; the Phase 3 review waits for part 3's review, so the spec is reviewed once with part 3's tags.
    The spec-writer inputs entry is released with these rulings.
  **Fixes applied (6):** miscount 1 (quests/0001 § 16: 17 sessions wrote a save, the 16 that started from a loaded
  save were compared; x-newchar started from the menu); stale cross-reference 4 (the corrections were written only in
  § 16, not where they correct: NPC 266's two draws carried into quests/0001 § 1, § 7 word 29 and its Act I draws
  table, and § 11; word 40's jump-table map into § 10's e11 row and bit table; the reward handlers' switched-off writes
  into § 3; the double-join open question marked answered); omission 1 (five gate-W1 lines without an anchor, quests/0001
  § 16's talk-step table lead and four rows of quests/0002 § 13, reverser review-fixes 7: anchors added). **Routed (1):** omission 1 (no unit test for part 2's
  checker rules: part 3 item 6). Status lines of both findings updated. Reverser review-fixes 12 promoted ("carry a
  correction into the section it corrects", seen at the part 1 review and here). The review request and the part 2
  entry are closed; part 3 is filed to the reverser; the owner entry stays open with a note.
- **2026-10-19 — Phase 3 drafted (spec-writer, `lane/p42s`, from `main` `1679654`); review requested, to follow Phase 2
  part 3's review.** Three specs, all `status: draft`: [quests](../specs/quests/README.md) (overview, C 9 / I 5 / L 2),
  [quests/progression](../specs/quests/progression.md) (C 84 / I 327 / L 7) and [quests/travel](../specs/quests/travel.md)
  (C 55 / I 80 / L 4). Progression has the record (bit grammar, the loader rule and the saved words `[C]`), the registry
  and dispatch order (`[C]` for the forced half), the join (`[C]` for the branch reached and the stub double join),
  timers, NPC interaction, the draws, a section per quest (41 word sections: bit tables with a setter site and a tag per
  row, 35 state diagrams; words 29, 33 and the four introduction objects write no record state), the gates and the
  creation readers; travel has placement, the free-cell search, waypoints, NPC act travel, the Durance and other portals,
  town portals (three draws `[C]`), warps (no draw `[C]`), resurrection, join and the gates. Worked examples from the run
  logs: two NPC 331 talks, one NPC 266 talk, word 1's reward through the saved words, one portal open and its level-seed
  chaining. Ruling (c)'s statements are `[I]` and listed in the review request for the re-tag from part 3; ruling (b)'s
  shortfalls are `[I]`. Open questions: 13 `[L]` over the three files (one new: the cairn order's two readings). Links
  added from items/quest-drops, objects, monsters/spawn, monsters/special, rng/seeds, items/cube, drlg/collision, save/d2s
  and drlg/warps; four glossary terms. Found while writing: save/d2s E1's load rule is stale against run 2 (flagged, not
  edited), and quests/0002's summary still says the portal open draws five times. Research-map change for the architect:
  rows `quests/progression` and `quests/travel` to "draft", review after part 3's review. Backlog: the plan 0044 gates
  entry closed; the rbs2 entry annotated (quests items folded) and left open for the economy lane; the part 2 inputs
  entry annotated, open for the re-tag; review request `2026-10-19-spec-writer-architect-plan-0042-phase-3-quests-spec-review.md`.
- **2026-10-19 — Phase 2 part 3 checkpoint (reverser, `lane/p42r`, slot 2; in progress).** run:2026-10-19-quests3:
  logger revision E (timers, the cairn order, the Dark Wanderer's step and tries, Anya's reward, the quest state byte),
  checker rules and `tools/test_quests.py` (16 tests) committed; recorded so far x-entry (the eclipse arm and timer, the
  bkd order, "Cain lost", level 50, word 37's 113 step, the Dark Wanderer), x-anya, h-anya, nm-anya (Anya's three tables,
  the `tr2` use, the town-portal refusal), x-meshifw (six westward trips, type 5); 0 mismatches; the 32 part 1 and 2
  logs 0 over 39 568 under the extended checker. Found: Meshif's Act III menu has no trade line; Tyrael's menu has no
  travel line (the Act IV → V travel is the red portal, object 566, `0x005B5880`); the Zoo's object 567 is placed
  nowhere. **Resume note:** sessions at the end of `tools/quest_sessions.py` (part 3 block); running x-tyrael3,
  x-death3, x-entry2, h-entry, x-wpact1-0; development logs `dev-p42r-*`; the finding sections hold `@@` markers until
  the final pass.
- **2026-10-19 — Phase 2 part 3 (reverser, `lane/p42r`, slot 2; review requested).** run:2026-10-19-quests3
  ([experiments](../findings/quests/experiments.md#run2026-10-19-quests3)): 13 recorded sessions, **0 mismatches over
  6 167 checks** under the extended `tools/quests.py check` (`quests3-check.txt`, `7cde7b36…`); the 32 part 1 and 2
  logs 0 over 39 568 under the same checker (`quests3-recheck-p12.txt`, `3f2b7de7…`; the 16 beyond part 2's 39 552
  are the new "Cain lost" rule); 12 development logs 0 over 2 498. Raises, corrections and shortfalls:
  [quests/0001 § 17](../findings/quests/0001-progression.md#17-phase-2-part-3-run2026-10-19-quests3),
  [quests/0002 § 14](../findings/quests/0002-travel.md#14-phase-2-part-3-run2026-10-19-quests3).

  | Part 3 item | Result |
  |---|---|
  | 1. quest-seed draws | the eclipse arm (3, periods 15/16/16; **correction**: once per game by the state, not private `+0x01`), the cairn order by the `bkd ` use (3 orders, 28 steps; trigger **refined**), the Dark Wanderer (4 games, 8 tries each; the 7-try branch not reached), Anya's reward in Normal, Nightmare and Hell, each `[C]`; quest timers raised in part (7 runs, one-shots only); the Zoo **unreachable** (object 567 placed by no DS1, created by no code: `objplace`, kept) |
  | 2. waypoint activation from mode 0 | **shortfall**: three attempts (the Cold Plains twice from the camp, the Spider Forest waypoint logged in mode 0 at 110 sub-tiles), no operate; `wpmodes` (kept) shows field waypoints first logged in mode 1/2 after a waypoint arrival and 0 without, `[I]` |
  | 3. act travel | Meshif west: six trips, one Lut Gholein level-seed step each (type 5) `[C]`; Tyrael: **correction**, the travel is the Harrogath portal (object 566, `0x005B5880`), the stock menu has no travel line; five trips, word 28 b0/b13 once, packet 0x48's clear (one case per travel word now: raised in part) |
  | 4. e3 / item-use steps | "Cain lost" on arrival in 40 (from `TownLevelLeave`), word 12 on entering 50, word 37's 112/113/123 steps, the `tr2 ` and `ass ` uses `[C]`; candidates table in § 17; word 40's map holds for 0x4ED0 and 0x4ED3 too |
  | 5. cheap travel remainders | town portal refused in a town (6) `[C]`; death and resurrection (3, Hell) `[C]` for the branch reached |
  | 6. unit tests | `tools/test_quests.py` 19 tests (part 2's talk steps, saved words, NPC 266's runs, word 40's map; part 3's rules) |

  Tools: `questev.py` revision E (`TMA`/`TMR`/`TMX`, `CRN0`/`CRN`, `DWS`/`DWF`, `ANL`/`ANY`, the state byte),
  `quests.py` (part 3 rules, `objplace`, `wpmodes`), `quest_sessions.py` (`use`, `tpuse`, `clickobj`, `walkto`,
  `pathto`, `push`, `toward`; `die` next to monsters; the part 3 block), `d2pilot.py` (Meshif's menu, `tyraelgo`, the
  waypoint walk's stop, `--exclude-xy`, the menu screenshot); four recipes `quest-p3*.json` (archivist entry for
  d2s.md). Manifests: `quests3-manifest.sha256` (43 lines, `1975e350…`), `dev-p42r-manifest.sha256` (26 lines,
  `38d3aaa5…`), one path base (`workspace/logs/quests/`). Symbols: nine quest functions raised to C, one added. One
  slot used; slot 2 stopped, its aside restored. No part 4 is planned: the shortfalls of § 17 and § 14 stay `[I]` in
  this plan. The part 3 backlog entry is left open for the reviewer.
  **Resume note (lane stopped at the owner's usage limit, 2026-10-19):** part 3 is complete as recorded above; nothing
  is left running (slot 2 stopped, aside restored). Logs kept: `workspace/logs/quests/2026-10-19-quests3-*` (13
  sessions with their saves and outputs) and `dev-p42r-*` (12 development logs, 2 screenshots), both manifests checked
  OK. What is left: the architect review only (the review request is filed). Gotchas for any later harness work: Save
  and Exit ends the game process (the watchdog then reports "the game exited"); walking clicks near a town waypoint
  open its menu; the `act` driver does not know the save's name, so copy `<log>.out.d2s` by hand; Harrogath's type-5
  lookup takes its single type-0 point without a draw.
- **2026-10-20 — Phase 2 part 3 reviewed (architect, `lane/p42r` review): accept with fixes.** Anchors spot-checked in
  the image (r2, no Ghidra): the eclipse arm `0x0059EDC0` (gate `+0x0C` = 0 and private `+0x01` = 0, `QUESTS_GetSeed`
  at 0x0059EDD3, `RNG_RandLoHi(15, 17)` at 0x0059EDE1, `QUESTS_TimerAdd` at 0x0059EDEE) behind e3's `+0x0C` = 0 and
  `+0x09` = 1 test (0x0059EE26–0x0059EE32), and the timer `0x0059ED80` calling `0x0059A350`; `0x00592EE1` (the
  order draw's seed); `0x00544840` → `0x00593CB0` at 0x0054488B; `0x0053743D` → `0x00597310`; Harrogath portal's
  word 28 write at 0x005B590F (`QUESTRECORD_SetState`); `LevelPointPick`'s n = 0 exit at 0x0066AC90; the town-portal
  town test at 0x005BE2E2; `UNIT_SetMode`'s unchanged-mode `je` at 0x006246AB. Re-run (kept in the run record): both
  manifests OK, the checker's outputs over the 13 logs and the 32 part 1 and 2 logs byte-identical to the kept files,
  12 development logs 0 over 2 498, 19 tests OK. Nine symbols raised and one added: no clash with `main`.
  **Rulings.** (1) The four corrections hold: the eclipse's once-per-game is the state (the run separates it: the
  second entry to 44 had private `+0x01` cleared and state 1, and drew nothing); the cairn order on the `bkd ` use,
  classes 17–21 in fill order `[C]` (the predicted order is that reading; plan 0042 P3's *Open question* on the other
  reading can close); the Act IV → V travel through object 566; Meshif's menu. (2) Shortfalls ruled final and `[I]` for
  this plan: the Zoo (object 567 placed by no DS1, created by no immediate: `[I]`, a computed class is not excluded),
  waypoint activation from mode 0 (`wpmodes` stays `[I]`), the unreached e3 rows, the 7-try branch, the timer re-arm
  and wrap. (3) The driver deviations are accepted: the logs are continuous, the hand-copied saves are in the manifest
  and the checker re-runs identically. (4) Symbols `QUESTS_TimersRun`/`TimerAdd` at `C` stand as names; the re-arm
  branch stays `[I]` in the text.
  **Fixes applied (3):** quests/0002's summary "town portal creation: five" corrected to three (stale since Phase 2
  § 12; raised by `lane/p42s`); NPC 367's "no travel line" scoped to the state logged, "never offered" `[I]` (the
  client's menu builder was not read; § 5 summary and the § 5 bullet); the checker and logger hashes named in the run
  record's review re-run line.
  **Backlog:** the review request is closed; the rbs2 quests/economy entry is closed (economy part (b) done in
  items/economy by `lane/p43s`, quests parts (a) and (c) folded by `lane/p42s`); the part 3 inputs entry is annotated
  and released to `lane/p42s`; a spec-writer entry is filed for save/d2s E1's stale load rule (assigned to
  `lane/p42s`). The archivist recipe entry stays open. The Phase 3 review follows the re-tag.
