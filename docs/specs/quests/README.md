---
spec: quests/overview
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, save/d2s, items/quest-drops, drlg/collision, drlg/warps, objects]
consumed_by: [items/quest-drops, items/cube, objects, monsters/spawn, monsters/special, rng/seeds, save/d2s]
tags: {C: 9, I: 5, L: 2}
updated: 2026-10-19
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

| File | Covers | Status |
|---|---|---|
| [progression.md](progression.md) | the quest record and its load rule, the 41 quest objects and the event dispatch, the join's game-wide pass, timers, NPC interaction, the quest-seed and player-seed draws, a section per quest (bit table and state diagram), the warp and portal gates, the creation-path readers | draft |
| [travel.md](travel.md) | placement (`ActLevelSpot`, the level-point lookup, the free-cell search), waypoint activation and travel, act change through an NPC, the Durance and other travel portals, town portals (open, use, close), warps, resurrection and join placement, the real-time gates | draft |

Not covered: the quest drops, rewards and item services ([items/quest-drops](../items/quest-drops.md)), the dialogue
text and the quest log's presentation, the AI and combat that decide when a boss dies (inputs here), and every two-client
case (party credit, the portal party and quest-word gates, hostility): [plan 0044](../../plans/0044-multiplayer-branches.md).

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
  place --> e3["quest event 3"]
  e3 --> qobj
  rec --> out["Save and Exit"]
```

## Shared model

- [C] **The record.** A player has one quest record per difficulty, 48 words of 16 bits, block *d* for difficulty *d*;
  the loader clears bits 13 and 14 of words 0–41 and sets bit 15 where bit 1 is set, copies words 42–47, and Save and
  Exit writes the record as it stands ([progression § A](progression.md#a-the-quest-record)). (fn:D2S_ReadQuests@0x0056A370,
  fn:QUESTRECORD_LoadBytes@0x0065C4D0, run:2026-10-18-quests2)
- [I] **The bit grammar.** Bit 0 done, bit 1 done with a reward pending, bits 2–11 log steps, bit 12 seen in the log,
  bit 13 done in this game, bit 14 failed in this game, bit 15 a reward pending from an earlier game; each quest adds its
  own bits ([progression § A](progression.md#a-the-quest-record)). (fn:QUESTRECORD_SetState@0x0065C360)
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
  [travel § Draws by event kind](travel.md#draws-by-event-kind)). (fn:QUESTS_GetSeed@0x005438B0,
  fn:sub_0066AC40_LevelPointPick@0x0066AC40)
- [C] **One placement routine.** The waypoint, NPC and join arrivals and the portals' town ends the runs logged went
  through `ActLevelSpot`: a level point, the subtile `5·t + 3`, then the nearest free cell (124 placements)
  ([travel § A](travel.md#a-placement)). (fn:sub_0061B060_ActLevelSpot@0x0061B060, run:2026-10-17-quests)
- [I] A resurrection and the Durance portal place the player the same way, read from the code.
  (fn:sub_0054C0E0_Pkt41Resurrect@0x0054C0E0, fn:sub_00546AC0_DuranceActTravel@0x00546AC0)

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
two runs reproduce it with 0 mismatches: [run:2026-10-17-quests](../../findings/quests/experiments.md#run2026-10-17-quests)
(16 199 checks, 11 sessions) and [run:2026-10-18-quests2](../../findings/quests/experiments.md#run2026-10-18-quests2)
(23 348 checks, 21 sessions). The talk steps reached, the record's load and save, the dispatch order, the join's pass,
the NPC 331 and NPC 266 draws, the portal's three draws, placement and the "no draw" travel rows are `[C]`; the quest
steps triggered by kills, operates, item use and level entry, the timers, the mode-0 waypoint activation, the stepping
type-5 lookup, packet 0x48, Tyrael's act travel and death are `[I]`, some of them awaiting plan 0042 Phase 2 part 3.

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

- [L] The two-client cases (party credit, the portal's party and quest-word gates, a non-zero travel stamp) are plan 0044's.
- [L] The per-file open questions: [progression](progression.md#open-questions), [travel](travel.md#open-questions).
