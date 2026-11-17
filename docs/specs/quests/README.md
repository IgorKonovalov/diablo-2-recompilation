---
spec: quests/overview
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, save/d2s, items/quest-drops, drlg/collision, drlg/warps, objects]
consumed_by: [items/quest-drops, items/cube, objects, monsters/spawn, monsters/special, rng/seeds, save/d2s]
tags: {C: 14, I: 5, L: 2}
updated: 2026-11-16
---

# Quests and travel: the game rules that move a character through the acts

## Purpose

This subsystem specifies the quest state machines and travel of the server
([ADR-0017](../../adrs/0017-scope-quests-travel-economy.md)): which event sets, clears or reads each bit of a player's
quest record, what the game-wide record holds, which quest events draw on which seed, how a waypoint is activated and
used, how a player changes act, how a town portal opens, works and closes, and where a player lands after any level
change. Quest logic is hardcoded: no excel table the game loads holds quest data, so the specs describe code, with the
tables it reads named where they enter. This page is the map and the shared model; the algorithms are in the two files
below.

## Files

| File | Covers |
|---|---|
| [progression.md](progression.md) | the quest record and its load rule, the 41 quest objects and the event dispatch, the join's game-wide pass, timers, NPC interaction, the quest-seed and player-seed draws, a section per quest (bit table and state diagram), the warp and portal gates, the creation-path readers |
| [travel.md](travel.md) | placement (`ActLevelSpot`, the level-point lookup, the free-cell search), waypoint activation and travel, act change through an NPC, the Durance and other travel portals, town portals (open, use, close), warps, resurrection and join placement, the real-time gates |

Not covered: the quest drops, rewards and item services ([items/quest-drops](../items/quest-drops.md)), the dialogue
text and the quest log's presentation, the AI and combat that decide when a boss dies (inputs here). The two-client
cases are [plan 0044](../../plans/done/0044-multiplayer-branches.md)'s; its run reached the Den's party credit
([progression § Word 1](progression.md#word-1-the-level-8-monster-region-and-the-hell-respec-offer-quest-object-1)),
hostility and the two gates with a declared stamp ([travel § J](travel.md#j-operate-gates-and-real-time-gates)).

## Data flow

```mermaid
flowchart TD
  save[".d2s quest and waypoint records"] --> load["loader rule"]
  load --> rec["player records, one per difficulty"]
  create["game creation"] --> qobj["41 quest objects, quest seed,<br/>game record"]
  join["first join"] --> off["the creator's finished quests<br/>switched off for the game"]
  rec --> join
  ev["events: talk, message, level change,<br/>item, death, leave, timer, operate"] --> qobj
  qobj --> rec
  qobj --> grec["game record"]
  grec --> readers["object inits, spawn gate,<br/>warp gates"]
  click["waypoint, NPC menu, scroll,<br/>warp, resurrect, join"] --> place["placement:<br/>ActLevelSpot"]
  place --> lseed["level seed of Position levels"]
  place -->|"level change within one act"| e3["quest event 3"]
  e3 --> qobj
  rec --> out["Save and Exit"]
```

## Shared model

- [C] **The record.** A player has one quest record per difficulty, 48 words of 16 bits, block *d* for difficulty *d*;
  the loader clears bits 13 and 14 of words 0–41 and sets bit 15 where bit 1 is set, copies words 42–47, and Save and
  Exit writes the record as it stands ([progression § A](progression.md#a-the-quest-record)). (fn:D2S_ReadQuests@0x0056A370,
  fn:QUESTRECORD_LoadBytes@0x0065C4D0, run:2026-10-18-quests2)
- [C] **The bit grammar, as far as the kept logs test it.** `SetState` and `ClearState` set or clear one bit of the
  word (430 and 38 logged writes, each next write's old word as predicted); bit 0 is done and bit 1 done with a reward
  pending, by their writers (the reward message sets bit 0 and clears bit 1 on words 1, 2, 4, 6, 9, 20, 25, 27 and 37);
  bit 13 is done in this game, on the player and the game record; bit 15 is a reward pending from an earlier game, by
  word 9's first-join clear ([progression § A](progression.md#a-the-quest-record)). (fn:QUESTRECORD_SetState@0x0065C360,
  fn:QUESTRECORD_ClearState@0x0065C3A0, run:2026-10-19-quests3, [quests/0001 § 18](../../findings/quests/0001-progression.md#18-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-2026-11-15-lanen66g))
- [I] Bits 2–11 are log steps, bit 12 seen in the log and bit 14 failed in this game; each quest adds its own bits. No
  kept log met a step bit at a `ClearSteps`. (fn:QUESTRECORD_SetState@0x0065C360)
- [C] **The events reach quests in a fixed order**, from quest object 40 down to row 0, and the talk, message and
  level-change events are forced, so they reach a quest the join switched off
  ([progression § B](progression.md#b-events-and-dispatch)). (fn:QUESTS_DispatchEvent@0x005438E0, run:2026-10-17-quests)
- [C] **The game creator's history shapes the game**: at the first join every quest the joining player had finished is
  switched off for the game and marked in the game record
  ([progression § C](progression.md#c-the-join-and-the-game-creators-history)). (fn:sub_00546270_QuestsPlayerJoin@0x00546270,
  run:2026-10-17-quests)
- [I] **Draws.** Quest events draw on the quest seed (NPC 331, the eclipse, the cairn order, Anya's reward, the Dark
  Wanderer, the Zoo, and the item draws of [items/quest-drops](../items/quest-drops.md)) and on the player's unit seed
  (NPCs 266 and 377); travel draws on the destination level's seed, the game seed of the portal objects and, for five
  waypoint rows, the object's seed ([progression § G](progression.md#g-the-draws),
  [travel § Draws by event kind](travel.md#draws-by-event-kind)). The draws of kill events (the cairn order aside) are
  read from the code. (fn:QUESTS_GetSeed@0x005438B0, fn:sub_0066AC40_LevelPointPick@0x0066AC40)
- [C] In the 1 111 logged talk, message, level-change and leave dispatches the quest seed moves only at the drawing sites
  named above (NPC 331's talk 45 times, Anya's reward 3, the eclipse 3) and the player seed only in NPC 266's talk (23);
  the cairn-order and Dark Wanderer fetches (0x00592EE6, 0x005BD3E2) lie inside timer runs (3 and 4), with one
  0x005BD3E2 fetch outside any logged event
  ([progression § G](progression.md#g-the-draws)). (fn:QUESTS_GetSeed@0x005438B0, run:2026-10-19-quests3, [quests/0001 § 18](../../findings/quests/0001-progression.md#18-plan-0066-batch-s3a-the-kept-quest-logs-re-checked-2026-11-15-lanen66g))
- [C] The quest-seed draws the runs reached (NPC 331's talk, the eclipse arm, the cairn order on the `bkd ` use, the
  Dark Wanderer timer, Anya's reward in the three difficulties) and NPC 266's two player-seed draws were each predicted
  from the seed before them ([progression § G](progression.md#g-the-draws)). (run:2026-10-17-quests,
  run:2026-10-18-quests2, run:2026-10-19-quests3)
- [C] The Zoo's quest-seed draws and NPC 377's player-seed draw are not reached through stock placement: no DS1 places
  object 567, no DS1 that a LvlPrest row names places NPC 377 or its placeholders, and no Levels, SuperUniques or
  Hireling class cell names 377 (two DS1 readers, the tables read as `.txt` and `.bin`). A class computed at run time is
  not excluded ([progression § G](progression.md#g-the-draws)). (fn:sub_0058E830_A5Q6_ZooInit@0x0058E830, 0x0059E1CE,
  [quests/0001 § 21](../../findings/quests/0001-progression.md#21-plan-0066-batch-s3c-part-2-the-game-records-data-flow-the-placement-scans-with-a-second-parser-2026-11-16-lanen66p))
- [C] **One placement routine.** The waypoint, NPC and join arrivals and the portals' town ends the runs logged went
  through `ActLevelSpot`: a level point, the subtile `5·t + 3`, then the nearest free cell (124 placements)
  ([travel § A](travel.md#a-placement)). (fn:sub_0061B060_ActLevelSpot@0x0061B060, run:2026-10-17-quests)
- [C] A resurrection places the player the same way, at the town's type-0 point with one level-seed step: three in
  Hell ([travel § I](travel.md#i-death-resurrection-and-joining)). (fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0,
  run:2026-10-19-quests3)
- [I] The Durance portal places the player the same way, read from the code. (fn:sub_00546AC0_DuranceActTravel@0x00546AC0)

## Inputs and oracles

| Item | Kind | Tag |
|---|---|---|
| the trigger of a quest step (a kill, an operate, a level change, the client's dialogue message) and of a travel (a click, a packet) | input | [C] for the talk steps (run:2026-10-18-quests2: 41 steps predicted from the logged message) |
| party membership, the players' rooms and near lists, held items | input | [I] (fn:sub_00540510_PartyForEach@0x00540510) |
| `GetTickCount()` at the two travel gates and in Diablo's end timer | input, real time | [C] for the travel gates, one client (run:2026-10-17-quests) |
| units, objects, portals and items a quest creates; levels, acts and rooms built on arrival; a town room's first population | oracle | [C] (run:2026-10-17-quests: the portal's population oracle, 9 opens) |
| the collision grid read by a free-cell search | input, logged | [C] (run:2026-10-17-quests: 545 searches) |

## Evidence and status

The reading is [quests/0001](../../findings/quests/0001-progression.md) and [quests/0002](../../findings/quests/0002-travel.md);
three runs reproduce it with 0 mismatches: [run:2026-10-17-quests](../../findings/quests/experiments.md#run2026-10-17-quests)
(16 199 checks, 11 sessions), [run:2026-10-18-quests2](../../findings/quests/experiments.md#run2026-10-18-quests2)
(23 348 checks, 21 sessions) and [run:2026-10-19-quests3](../../findings/quests/experiments.md#run2026-10-19-quests3)
(6 167 checks, 13 sessions). `[C]`: the talk steps reached, the record's load and save, the dispatch order, the join's
pass, the quest timers (one-shots), the quest-seed draws of NPC 331, the eclipse arm, the cairn order on the `bkd ` use,
the Dark Wanderer and Anya's reward, the NPC 266 draws, the level-entry and item-use steps reached, the portal's three
draws and its refusal in a town, placement, Meshif's stepping type-5 return, the Harrogath portal, packet 0x48's clear,
the resurrection's move and the "no draw" travel rows. [Plan 0066](../../plans/done/0066-simulation-inferred-claims-sweep.md)
added, from new checks over the kept logs, second-tool scans of the code image and tables, and an emulation of the
free-cell search: the logged boss credits, services and object steps, the event raisers, the registry, the game record's
writers, the timer cadence, the stock placement scans and the free-cell search at other sizes and steps. `[I]` for this
plan: the kill steps the logs do not hold (party credit, the region tests, most log-state steps), boss events and far
operates, the timer re-arm and wrap, the Zoo's draws (the object is placed by no stock DS1), the mode-0 waypoint
activation, NPC 367's travel branch, the unreached level-entry rows and the Dark Wanderer's 7-try branch.

## Cross-references

| Spec | What it takes from here |
|---|---|
| [items/quest-drops](../items/quest-drops.md) | the quest bits at kill time and the quest seed's non-item draws ([progression § G](progression.md#g-the-draws)) |
| [objects](../objects/README.md) | the quest `InitFn`s' game-record and private-state reads ([progression § Creation-path readers](progression.md#creation-path-readers)) |
| [monsters/spawn](../monsters/spawn.md) | the Chaos Sanctuary gate ([progression § Word 26](progression.md#word-26-diablo-the-seals-and-the-harrogath-portal-quest-object-23)) |
| [monsters/special](../monsters/special.md) | the forced death list and quest hooks ([progression § B](progression.md#b-events-and-dispatch)) |
| [rng/seeds](../rng/seeds.md) | act `+0x094` as the true tomb ([progression § Creation-path readers](progression.md#creation-path-readers)) |
| [items/cube](../items/cube.md) | the cow-portal gate words ([progression § Word 4](progression.md#word-4-cain-the-cairn-stones-tristram-and-the-cow-king-quest-object-4)) |
| [drlg/collision](../drlg/collision.md), [drlg/warps](../drlg/warps.md) | the level-point lookup and warp pairing used by placement ([travel § A](travel.md#a-placement), [travel § H](travel.md#h-warps)) |
| [save/d2s](../save/d2s.md) | the record's load rule and the saved words ([progression § A](progression.md#a-the-quest-record)) |

## Open questions

- [L] The two-client cases not reached by run:2026-10-20-two-clients (plan 0044): party credit beyond the Den's partied
  member in town, the portal's party and quest-word gates, and the un-declare path.
- [L] The per-file open questions: [progression](progression.md#open-questions), [travel](travel.md#open-questions).
