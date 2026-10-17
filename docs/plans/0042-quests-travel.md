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
  NPC-talk draws on the player's seed (0x00596B23, 0x0059E1CE) and the six non-item quest-seed sites. (d) The
  `Position`-level seed step for every point type but 13 extends drlg/0005's `[C]` (type 11) to types 0 and 5 as `[I]`.
  (e) Real-time gates as inputs. (f) The contradicted lead (portal 5 s) and its reachability. (g) The research-map rows
  `quests/progression` and `quests/travel` are still to be added (architect).
