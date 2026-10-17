# ADR-0017 — Quest progression, travel and the item economy enter scope, beside the five simulation phases

> **Status:** accepted (owner, 2026-10-16)
> **Date:** 2026-10-16
> **Amends:** [ADR-0002](0002-scope-creation-paths-and-enablers.md) (scope), alongside [ADR-0014](0014-scope-game-simulation.md) (whose five phases are unchanged)
> **Related plan(s):** [0042-quests-travel](../plans/0042-quests-travel.md), [0043-items-economy](../plans/0043-items-economy.md)

## Context

The reviewed creation specs take the quest state as an input in many places. [items/quest-drops](../specs/items/quest-drops.md)
says when quest bits get set is simulation and an input; [objects](../specs/objects/README.md) takes the quest-state
`InitFn`s and object 582 as value oracles; [monsters/spawn](../specs/monsters/spawn.md) takes the Chaos Sanctuary gate
test as an oracle; [rng/seeds](../specs/rng/seeds.md) leaves the Act II tomb fields, the Act III bit and the level-27
bit open; [items/cube](../specs/items/cube.md) reads the classic word-26 gate for the cow portal; the collision spec's
Arcane Sanctuary waypoint depends on a quest word. The quest record's layout and the act-travel gates are already
read ([save/0002](../findings/save/0002-quest-words.md)), and some forty quest, waypoint and portal functions are
named in `re/symbols.csv` (`QUESTS_*`, `WAYPOINT_*`, `sub_00584E30_WaypointOperate`, `sub_0056D130_PortalObjectCreate`).

The economy is named and stopped at the same edge. [items/vendors § I](../specs/items/vendors.md) names
`sub_0062FDC0_ItemTradePrice`, `sub_00578050_NpcRepair` and `sub_0062FE60_RepairCost` and calls them "game economy,
not item creation (ADR-0002)". The hirelings spec names the hire and resurrect costs, quest-drops leaves
`sub_0055A090_DropGoldAmount` (Baal's, Wirt's and the quest chests' gold) open, and combat/0001 names
`ITEMS_DurabilityLossRoll` and `COMBAT_DurabilityLoss` without modelling them.

Neither area is one of [ADR-0014](0014-scope-game-simulation.md)'s five phases (combat, stats and states, skills and
missiles, AI, animation timing), and neither is a creation path under ADR-0002. A reimplementation that has every
creation path but no quest progression, no waypoints and no prices is not a playable game, and those are the gaps a
reimplementer meets first after the world generator.

## Decision

Two areas enter scope as research-map rows of their own, outside ADR-0014's phase order:

- **Quest progression and travel:** which server event sets, clears or reads each bit of the quest record, per quest
  and per difficulty; the game-wide quest flags; the quest seed's draws; which creation code reads the quest state;
  the waypoint record (activation and travel); act travel; town portals (creation, placement, pairing, closing); and
  where a player is placed on entering a level.
- **The item economy:** buy, sell, gamble and repair prices; hire and resurrect costs; gold amounts (monster and object
  gold piles, the scripted quest gold, the player's death loss) and the gold caps; durability wear, ammunition and
  quantity consumption, and repair.

Evidence follows the form of each claim. A **one-shot function** (a price, a repair cost, a gold amount, a waypoint or
portal placement) is reproduced as a creation path is, under [ADR-0003](0003-runtime-experiments.md) and
[ADR-0004](0004-boundary-oracles-in-reproduction.md). An **event-driven change** (a quest bit set by a kill, an
operate or a dialogue; a durability point lost on a hit) is reproduced per event under ADR-0014's rule: logged inputs
at a named boundary, seeds asserted on exit, chained pairs per event kind, time in game frames. What triggers an event
(a kill, an attack, an operate) is an input; its own mechanics belong to their phase. NPC dialogue text, the quest log,
cinematics and every other presentation stay out ([ADR-0005](0005-presentation-formats-tools-only.md)). Multiplayer
branches follow ADR-0014 § Multiplayer. Neither row waits for a simulation phase, and no simulation phase waits for
them.

## Consequences

### Positive

- The quest-state oracles of six reviewed specs get a model that can replace them, as ADR-0014 lets later phases
  replace earlier oracles.
- A reimplementer gets the loop between creation paths: travel between levels, the quest gates, the prices of what the
  creation specs make.
- The price function is one-shot and deterministic, so it reaches `[C]` cheaply with the existing vendor tooling.

### Negative

- **Quests are hardcoded.** There is no quest table; 1.14d inlines each quest's callbacks. The reverser load is close
  to plan 0032's (pure code, slow to find), multiplied by every quest.
- **Reaching quest events costs harness time.** Many quest steps follow a boss kill or a long walk. Tool-built saves
  set just before a step (stock tables, built quest words) cut most of it, but some steps need owner play, as plan
  0032's addendum did.
- **Scope keeps growing.** The research map gets two to four more rows, and the "done" point moves again.
- **Event-driven parts share ADR-0014's weaknesses:** resynchronised events, log volume, non-repeatable sessions.

### Neutral

- Evidence rules, tags, anchors and the sources policy are unchanged.
- Battle.net, ladder and realm rules stay out (ADR-0009).
- Rows are added to the research map when each plan starts, under a new **Game rules (ADR-0017)** band.

## Alternatives considered

**Leave both out, as ADR-0002 did.** It lost because both are now the largest edge left in the reviewed specs (quest
state is an input in six of them), and the cost ADR-0002 feared, work before a single core spec was reviewed, no
longer applies.

**Make quests a sixth simulation phase after AI.** It lost because the quest code is not built on stats, skills or AI:
a quest step is triggered by an event those phases produce, and that event can be logged as an input today. Waiting
for phase 4 would hold the creation specs' quest oracles open for the longest possible time.

**Fold the economy into the vendors spec.** It lost because prices, repair, gold amounts and durability wear are read
by vendors, hirelings, quest-drops, combat and the player alike; one row keeps them in one place.
