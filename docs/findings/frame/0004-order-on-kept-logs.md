# 0004 — The server frame, part 4: the order model on the kept logs

> **Subsystem:** sim/frame
> **Question:** does the frame order of frame/0001–0003 (the passes of `GameTick`, the ten walks of
> `GameRunUnitEvents`, the queue order inside a list, the drain after the tick) predict the logged order of every
> frame of the plan 0037–0052 corpus that holds two or more events, and the seed hand-off of every pair of events on
> one seed in one frame? How many of plans 0045 and 0052's resynchronised skill entries does it re-chain, and how
> many cross-type every-frame runs do the kept logs hold?
> **Date:** 2026-11-03   **Plan:** 0055 (Phase 2a)   **Status:** open (review requested)

A replay of kept logs, no game run, no slot, no Ghidra (plan 0055 § Phase 2a). Tool `tools/frame.py`
(`73715f53…`; tests `tools/test_frame.py` `d3e87689…`), reading Phase 0's corpus with `tools/frame_corpus.py`'s
`read_events` (`287f3761…`) and the pinned image by `objdump`. Run record:
[experiments § run:2026-11-03-frame-order](experiments.md#run2026-11-03-frame-order). The plan's checkpoint named the
run `2026-10-30-frame-order`; it ran on 2026-11-03 and carries that date.

## Answer (summary)

- [C] *(Dated note, 2026-11-03: the counts of this bullet are Phase 2a's; [frame/0005](0005-dispatchers.md) § 6 gives the wider model's, 383 349 frames, 17 254 separating pairs and the controls' 42 148, 9 608, 8 885 and 95 events.)* **No order mismatch in the corpus.** Over the 331 frame-stamped corpus logs (6 436 250 events by
  `read_events`), 501 689 frames hold two or more events; in the 192 294 of them that hold two or more events the model
  places, the 1 719 463 placed events (267 695 by their own kind, 1 451 768 by the pair they are nested in) fall in the
  pass order in every frame: 0 mismatches, 0 nesting conflicts. 14 061 consecutive placed pairs separate the order
  (their pass sets do not overlap), 3 105 of them with neither event placed by the anim logger's phase field; by logger
  the separating pairs are anim 13 967, skills 94 and stats, economy and the rest 0, so the frames that test the order are
  those holding such a pair, and the other placed frames (the stats logs' 162 249 among them) agree trivially. Four
  control orders each fail: monsters' walks before players' (17 040 events, 5 997 frames), slot before every-frame
  (9 608, 7 924), missiles after items (110, 46), the drain before the tick (87, 87). (run:2026-11-03-frame-order,
  fn:sub_005414D0_GameRunUnitEvents@0x005414D0, fn:sub_0052D870_GameTick@0x0052D870)
- [C] **The walks in the game's own runs** (frame/0002 § 1, emulated there): the players' slot walk before the
  monsters' (3 007 `PDS` → `MDS` pairs, each placed by its dispatch call site, 0x00540FC4 and 0x005410C4); the
  monsters' every-frame walk before their slot walk (4 637 pairs of an `EF` logged in phase 5 and a later `MDS`);
  the missiles' walks before a player or monster event and before the drain (`MF0` → `SDO0` 6, `MF0` → `CU0` 81);
  the objects' walks after the players' and monsters' slot walks (4 pairs of `PDS` or `MDS` → `OEV`). Not separated
  by any pair: the items' walks, the objects' every-frame against slot order, the missiles' every-frame against
  slot order. (§ 2, run:2026-11-03-frame-order)
- [C] **The order inside a list, in the game's own runs** (frame/0002 § 2, emulated there): a slot list runs its
  records oldest queued first: of the anim logs' slot dispatches matched to a logged queue call (41 178 of 51 842
  `MDS`, 17 476 of 19 125 `PDS`), the 4 566 consecutive `MDS` pairs and 13 `PDS` pairs of one frame are all in queue
  order, none inverted; the reading "newest queued first" fails all 4 579. The missiles' every-frame list runs newest
  created first: 24 652 consecutive pairs of windowed missiles' `MissileDoFrame` lines in 4 710 frames, every one
  newest first, none oldest first. (§ 3, fn:sub_005416B0_EventQueueAt@0x005416B0,
  fn:sub_005415E0_EventQueueEveryFrame@0x005415E0, run:2026-11-03-frame-order)
- [C] **A packet handled after frame N's tick carries the stamp N**, in part (frame/0001 § 5): 87 `SKILLS_CanUse`
  calls from the request handlers (their return addresses in `PLRMSG_SkillAtXY` and `PLRMSG_SkillAtUnit`, both
  reached only from the packet table) are logged after a missile frame of the same stamp; the reading "the drain reads the frame it acts
  before" fails all 87. Scoped to the skill-request handlers. (§ 2, fn:sub_0052CFE0_SrvDrainMessages@0x0052CFE0,
  fn:PLRMSG_SkillAtXY@0x00549AD0, fn:PLRMSG_SkillAtUnit@0x00549BA0, data:g_SrvPacketTable@0x006E0D18,
  run:2026-11-03-frame-order)
- [C] **Seed hand-offs in one frame.** 1 065 396 pairs of consecutive observations of one seed by two events of one
  frame, in model order (which is the logged order): 1 023 086 handed (the first's value is the second's), 42 310
  stepped 1 to 4 096 draws on, **0 reversed**, 0 off the stream. On the game seed: 440 754 pairs (stats 420 895,
  economy 19 859), 4 675 of them stepped. Each stepped pair separates the logged order from its reverse.
  (§ 4, run:2026-11-03-frame-order)
- [C] **Cross-type every-frame queues the kept logs hold**: 926 monster every-frame records queued during an earlier
  walk of the frame than the monsters' every-frame walk (79 in the missiles' every-frame walk, 847 in the players'
  slot walk), which the model runs that frame; players: none (2 queued in the monsters' slot walk, next frame). The
  kept logs hold no every-frame queue line for objects, items or missiles. (§ 5, fn:SUNIT_ModeEveryFrame@0x00553F00,
  run:2026-11-03-frame-order)
- [C] **The resynchronised entries re-chained.** Of plan 0045's 281 player gaps (part 1 133, part 2 148)
  `tools/skills.py` walked 135; this run's walk, which chains from the latest skill-event exit before the entry,
  re-chains 7 more (all part 2's "nested" class: the enclosing event's exit is the entry), so 142, and 139 stay open.
  Of the 331 monster gaps it re-chains none. Each remaining gap is named with its first link that does not close
  (§ 6): the monster gaps' logs hold no AI line (by `skills.py`'s classes: 268 "not attributed", the unit named
  but its seed moved between the lines; 52 with no line naming the unit; 11 with a defender's line). So of part 1's 3 459 consecutive pairs, 3 155 chain at once, 90 by
  `skills.py`'s walk, 0 more here, and 214 stay open. (run:2026-11-03-frame-order, run:2026-10-25-skills,
  run:2026-10-27-skills)
- [I] *(Dated note, 2026-11-03: the counts of this bullet are Phase 2a's; [frame/0005](0005-dispatchers.md) replaces them, and fn:sub_00578ED0_NpcHealDead@0x00578ED0 is one of the callers that had kept a hook open.)* **The limit.** Phase 2a's Done-when ("0 mismatches over every frame-stamped frame with two or more events") is
  not met as written: see the 309 395 frames below. The model places an event only when its pass follows from its kind: 15 of the 89 hooked functions
  of the kind map have a direct-call reach that closes on pass roots; 74 reach a function with no direct caller that
  is no pass root: pointer-reached callbacks (skill, mode, AI, missile, quest) that the reach does not follow, and
  for the shared functions also the client's own loops (0x0044EFA0, 0x0044CF20). Most events are placed only through the pair they
  are nested in, and frames whose events are all unplaced (309 395 of the 501 689) test nothing. The combat (75 logs),
  two-combat (2), economy-hire (1) and h6b (10) logs have no frame with two placed events. (§ 1, `reach.txt`, run:2026-11-03-frame-order)

## Leads used

None. The model is frame/0001–0003's reading; the logs are the corpus of plan 0055 Phase 0.

## Functions

No new name. The pass roots of the reach, all in `re/symbols.csv`:

| Address | Name | Role here | Tag |
|---|---|---|---|
| `0x0052D870` | `sub_0052D870_GameTick` | the passes' order | I |
| `0x005414D0` | `sub_005414D0_GameRunUnitEvents` | the ten walks | I |
| `0x00540F60` | `sub_00540F60_PlayerEventsRun` | slot-branch dispatch 0x00540FC4 (`PDS`) | I |
| `0x00541060` | `sub_00541060_MonEventsRun` | slot-branch dispatch 0x005410C4 (`MDS`) | I |
| `0x005ADBB0` | `sub_005ADBB0_MissileDoFrame` | the missiles' walks (`MF0`) | C |
| `0x0052CFE0` | `sub_0052CFE0_SrvDrainMessages` | the drain | I |
| `0x006E0D18` | `g_SrvPacketTable` | packet handlers: the drain | C |

## Walkthrough

### 1. The model

- [I] **Ranks.** One stamp N (`Game+0xA8` as every logger reads it at the line) covers `GameTick(N)` and the drain
  that follows it: `GameTick` increments the counter before its first pass (0x0052D87B), and the host loop drains
  before it calls `ServerGamesFrame` (frame/0001 § 1, § 5). The ranks: 1 `ActsClockPass`, 2 `GameFpsStats`, 3
  `NewRoomsUpdate`, 4..13 the ten walks (missiles, players, monsters, objects, items; each every-frame then slot),
  14 `ClientsRoomSync`, 15 `ActUnitsFrameReset`, 16 `ActsRoomRemovalsClear`, 17..20 the periodic calls, 21 the drain.
  (fn:sub_0052D870_GameTick@0x0052D870, 0x0052D8DF–0x0052D96C, 0x005414EC–0x00541589)
- [I] **The kind map** (`KINDS` in `tools/frame.py`; `kinds.tsv`, 115 kinds of six logger families). Each kind
  names its hooked function and a rule: the hook's direct-call reach up to pass roots (GameTick's passes, the five
  runners, the four event tables, `MissileDoFrame`, the drain and its dispatchers, the packet table's handlers, opcodes 0 to 0x66);
  the reach of the function that holds the line's own return address, when it closes; a call site (`PDS`, `MDS`:
  the dispatch calls inside the runners' slot branches, after the mode tests at 0x00540F63 and 0x00541063); anim's
  `EF` phase field (`ph` k in 1..10 is walk k; 11 is outside the walks); the unit type (combat `RGN`, stats `AU0`,
  h6b `RPE`); or a skipped bookkeeping line (a window, a dump). Where the roots are event tables of two types (the aura
  ticks, `g_PlayerEventFuncs[8]` and `g_MonEventFuncs[8]`), the event's unit type keeps its own two walks.
  (fn:sub_00540F60_PlayerEventsRun@0x00540F60, fn:sub_00541060_MonEventsRun@0x00541060)
- [I] **The reach** (`reach.txt`): 15 hooks close, all by one root: the regeneration and timed-list events
  (`g_PlayerEventFuncs[3]`, `[12]`; `g_MonEventFuncs[3]`), the aura ticks, two object events
  (`g_ObjEventFns[1]`, `[7]`), the item replenish (`g_ItemEventFuncs[3]`), `MissileDoFrame`, and five store
  services reached only from packet handler 0x31 (`NPC_BuyItem`, `NPC_SellItem`, `sub_00578050_NpcRepair`,
  `NPC_CainIdentify`, `MERC_Resurrect`). The other 74 reach a function with no direct caller that is no root. Of the
  return-address rule, six functions close: `PLRMSG_SkillAtXY` and `PLRMSG_SkillAtUnit` (`CU0`, the drain, 707 and
  504 events), `EVENT_SelectedAuraTick` (`SDO0`, 174, the players' and monsters' walks), `PLAYER_CorpseCreate`
  (`MSET`, 33, the players' walks), `sub_00562DA0_ItemEventDispatch` (`RP0`, 346, the items' walks) and
  `NPC_TradeOpen` (`SWW`, 8, the drain). (fn:NPC_BuyItem@0x00577830, fn:PLRMSG_SkillAtXY@0x00549AD0,
  fn:EVENT_SelectedAuraTick@0x0056FCB0, data:g_SrvPacketTable@0x006E0D18)
- [I] **Nesting.** An event logged between the begin and end lines of a pair whose set is placed takes the
  intersection of its own set with the pair's (an open event takes the pair's). An empty intersection would be a
  mismatch; none occurs. (run:2026-11-03-frame-order)
- [I] **The test.** Per frame, the placed events in logged order are placed greedily at the lowest rank of their set
  not below the last; one that cannot be placed is a mismatch. A frame is the pair (game, stamp); the stamp never
  falls inside a log (331 segments for 331 logs), so each log is one game. (run:2026-11-03-frame-order)

### 2. The order of the passes and walks

- [C] 0 mismatches in 192 294 frames (counts in the summary; run:2026-11-03-frame-order). The separating pairs by
  kind and rule (`check.txt`):

  | first → second | pairs |
  |---|---:|
  | `EF` [phase] → `MDS` [site] | 4 637 |
  | `EF` [phase] → `EF` [phase] | 3 530 |
  | `PDS` [site] → `MDS` [site] | 3 007 |
  | `PDS` [site] → `EF` [phase] | 2 779 |
  | `MF0` [reach] → `CU0` [return] | 81 |
  | `EF` [phase] → `PDS` [site] | 7 |
  | `MF0` [reach] → `SDO0` [return] | 6 |
  | `MH0` [nested] → `CU0` [return] | 5 |
  | `PDS` [site] → `OEV` [reach], `EF` → `OEV`, `MDS` → `OEV` | 3, 3, 1 |
  | `MH0` [nested] → `SDO0`, `MC0` [nested] → `CU0` | 1, 1 |

  The phase field is the logger's observation of the runner (breakpoints at the ten walk calls), not a prediction;
  the 3 105 pairs without it are each a prediction of both events' passes. (run:2026-11-03-frame-order)
- [C] **The stamp.** The 87 `MF0`/`MH0`/`MC0` → `CU0` pairs put a skill request (return addresses in
  `PLRMSG_SkillAtXY` and `PLRMSG_SkillAtUnit`) after a missile frame of the same stamp; the control "drain before the tick" fails each. So the drain
  after tick N reads N. Scoped to those handlers. (fn:sub_0052CFE0_SrvDrainMessages@0x0052CFE0,
  run:2026-11-03-frame-order)

### 3. The order inside a list

- [C] **Slot lists, oldest queued first.** A `PDS`/`MDS` dispatch (unit, kind, `a`, `b`, frame) is matched to the
  oldest pending record with those fields queued by a logged call: `SCH`/`RSC`'s `q` list (the scheduler's 13
  `UnitQueueEvent` sites) or `CQ` (the catalogue's), its frame raised to the queue frame + 1 when not later (as
  `EventQueueAt`), and a `CAN` of the unit and kind cancelling its pending records (9 812). In the 4 080 frames with
  two or more matched `MDS` and the 13 with two `PDS`, consecutive dispatches are in queue order 4 566 and 13 times,
  inverted 0. A wrong reading "newest queued first" fails each of the 4 579. (fn:sub_005416B0_EventQueueAt@0x005416B0,
  fn:sub_005417D0_UnitQueueEvent@0x005417D0, run:2026-11-03-frame-order)
- [I] The `CAN` line does not log the cancel's `a` filter; the match treats every logged cancel as of the whole kind,
  which can only leave a later dispatch unmatched (1 649 `PDS` and 10 664 `MDS` are unmatched in all, most queued by
  sites the logger does not hook). (fn:UNIT_CancelEvents@0x00540E60)
- [C] **The missiles' every-frame list, newest first.** In a frame, the first `MF0` line of each windowed missile
  (skills logger; at most eight windowed at once) against the line of its creation (`MC1`, the latest before the
  frame for that pointer): 24 652 consecutive pairs in 4 710 frames, all newer missile first. The reading "oldest
  first" fails all. A guid-descending order would predict the same (guids grow with creation), so the log does not
  separate the front push from such an order; frame/0002 § 2.2's emulation does.
  (fn:sub_005415E0_EventQueueEveryFrame@0x005415E0, fn:sub_0059FA30_MissileCreate@0x0059FA30,
  run:2026-11-03-frame-order)

### 4. Seed hand-offs

- [C] An event's entry seeds are observed at its line, its exit seeds at its end line; consecutive observations of
  one seed object by two events of one frame are a hand-off (`check.txt`, by family and object;
  run:2026-11-03-frame-order):

  | family | object | pairs | handed | stepped |
  |---|---|---:|---:|---:|
  | stats | game seed | 420 895 | 420 367 | 528 |
  | stats | the player's seed | 415 679 | 413 975 | 1 704 |
  | stats | a hireling's or monster's seed | 3 108 | 3 081 | 27 |
  | economy | game seed | 19 859 | 15 712 | 4 147 |
  | economy | the player's seed | 19 816 | 18 813 | 1 003 |
  | economy | a unit's seed | 312 | 276 | 36 |
  | combat | a unit's seed | 90 610 | 58 583 | 32 027 |
  | skills | a unit's seed (pointer; type and id) | 73 770; 3 665 | 71 128; 3 665 | 2 642; 0 |
  | anim | a unit's seed | 17 682 | 17 486 | 196 |

  None reversed, none off the stream within 4 096 steps. A unit's seed object is its pointer and type (the server's
  and the client's copies of one unit share type and id; a freed unit's pointer is reused within a frame, as a missile
  ended and a summon created at 48554240 in frame 700 of `2026-10-25-skills-dru-1.log`). A stepped pair says that
  something unlogged drew on that seed between the two events; it is no mismatch. (run:2026-11-03-frame-order)

### 5. Cross-type every-frame queues (P1.2 review ruling 1)

- [C] anim's `EF` line is `SUNIT_ModeEveryFrame`'s entry, which queues the unit's mode every-frame record
  (`UnitQueueEveryFrame`, 0x00553F19); its phase is the walk it was queued in. Of 73 567 `EF` lines with a phase
  (2 932 more from logger revisions without one): monsters 926 queued in an earlier walk than their every-frame walk
  (missiles' every-frame 79, players' slot 847), 64 617 in their own or a later walk; players none earlier, 2 in the
  monsters' slot walk, 8 022 outside the walks. The model runs the 926 in the frame they were queued in (frame/0002
  § 2.4); that they ran then is anim/0001's `ef-first` check (run:2026-10-27-anim), not this run's. Objects, items and
  missiles: no every-frame queue line in any kept log, so their half stays with Phase 2b. (fn:SUNIT_ModeEveryFrame@0x00553F00,
  run:2026-11-03-frame-order)

### 6. The resynchronised entries

- [C] `rechain` walks each resync listed in the kept gap files of run:2026-10-27-skills (`part1-gaps.txt`: part 1's
  logs; `gaps.txt`: part 2's), from the latest `SST1`/`SDO1` of the unit before the entry, over every line naming the
  unit's seed (entry or exit, any role), each link equal or, for a single-draw line (`THR`, `DRR`), one step:

  | gaps | listed | re-chained | open: skills.py's reason |
  |---|---:|---:|---|
  | part 1 player | 43 | 0 | defender 31, no line 11, not attributed 1 |
  | part 1 monster | 171 | 0 | not attributed 131, no line 33, defender 7 |
  | part 2 player | 103 | 7 | defender 60, not attributed 13, off the stream 11, nested 10, no line 2 |
  | part 2 monster | 160 | 0 | not attributed 137, no line 19, defender 4 |

  The 7 are all of the "nested" class: an item cast's do event nested inside a delivery left `skills.py`'s walk
  starting from the inner exit, where the outer event's exit equals the next entry (`2026-10-27-skills-barh-1.log`
  n=1267: `SDO1` n=1253 `5e2291ee:46ed5501`, `SST0` n=1267 the same). Per gap, the first link that does not close is in
  `rechain-gaps.txt`. (run:2026-11-03-frame-order, run:2026-10-27-skills)
- [I] Why the rest do not close: the monster gaps' logs hold no line for the AI events between (monster kind 2,
  `sub_005B1740_MonAiEvent`, run in the monsters' slot walk; plan 0052's H1); the player gaps' defender class needs
  the defence rolls logged outside an open span (combat/0001), and the off-stream ones a reseed between.
  (fn:sub_005B1740_MonAiEvent@0x005B1740, run:2026-10-27-skills)

## Data touched

None (logs only). `struct:Game+0xA8` is the stamp every logger reads.

## Dead ends

- A first pass placed `EF` lines from logger revisions 1 and 2, which carry no phase, outside the walks: 2 277 false
  `MDS` mismatches in `dev-2026-10-27-dev-smoke.log` and others (dev run 2). Such lines are unplaced from dev run 3 on.
- Matching slot dispatches without the `CAN` lines gave 4 inverted pairs, each a record cancelled and queued again
  (`2026-10-27-anim-p2-mon-7.log` line 8 254: unit 54425600's kind-1 record of line 7 808 cancelled at 8 065, queued
  again at 8 066; dev run 2). Dev run 3 applies the cancels.
- Seed objects keyed by type and id gave 4 "off" hand-offs between the server's and the client's copy of the player
  (rev-4 `CanUse` lines from the client's button check, return 0x004D9FCA, carry no `cl` flag; dev run 4), and keyed
  by pointer alone 20 "off" across a pointer reused in the frame (a missile freed, a summon created; dev run 5). Keyed
  by pointer and type, none.

## Open questions

1. *(2026-11-03: answered in part by [frame/0005](0005-dispatchers.md), run:2026-11-03-frame-order-2: 9 of the 74 close, 65 stay open at every rank; 383 349 frames now hold two or more closed sets, 0 mismatches, 17 254 separating pairs.)* The 74 open hooks: the pass of a pointer-reached function needs its table's dispatcher read (the skill, mode, AI and
   missile function tables) or a phase marker in the logger. Phase 2b's window logs carry `UE0`/`UE1` per event run
   (frame/0001 § 7, frame/0003 § 9), which places every line between them.
2. The objects', items' and missiles' every-frame cross-type runs: no kept line; Phase 2b counts them (ruling 1).
