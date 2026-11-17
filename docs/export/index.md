# Overview

This site describes how Diablo II: Lord of Destruction, version 1.14d for the PC, works inside: how it builds its
levels, which monsters it places in them, how it decides what an item drop is, and how the running game moves,
fights and saves. It is written for people who want to understand the game closely enough to rebuild its logic,
with the same random draws in the same order and the same arithmetic.

It is an unofficial preservation project. It holds no game files, art, text dumps or code: every page describes
behaviour in our own words. See [About](about.md).

## What is here

The topic pages and a glossary, in plain prose with small worked numbers, tables and diagrams. Each page says in
words how sure we are of what it states; [How to read the tags](reading-the-tags.md) explains the wording.

Some pages mention the project's detailed specifications. Those are not part of this site yet, so the mentions are
plain text without a link. This site is also a simplified edition: where a passage could not be published as written,
it was left out. [About](about.md) says what that means, and how the diagrams and animations are drawn.

## Where to start

Read [Randomness](../wiki/randomness.md) first: nearly every other page depends on it. Then follow the groups in
order, or jump to the topic you need. The [Glossary](../glossary.md) explains the terms.

### Foundations

- [Randomness: one seed per thing](../wiki/randomness.md)
- [Game data, tables, strings and formulas](../wiki/game-data.md)

### Building the world

- [How a level is built](../wiki/levels.md)
- [Monsters](../wiki/monsters.md)
- [Objects: shrines, chests, barrels and the rest](../wiki/objects.md)

### Items

- [How an item drops](../wiki/items.md)
- [Items that do not come from a monster drop](../wiki/items-other-paths.md)
- [Prices, repair, gold and wear](../wiki/economy.md)
- [Using items, and the inventory](../wiki/inventory.md)

### Characters and combat

- [Characters and hirelings](../wiki/characters.md)
- [Combat](../wiki/combat.md)
- [Stats and states](../wiki/stats-and-states.md)
- [Skills and missiles](../wiki/skills.md)
- [Saves: what a `.d2s` file holds](../wiki/saves.md)

### The running game

- [Quests and travel: how a character moves through the acts](../wiki/quests.md)
- [Seed to world: how a game is built](../wiki/seed-to-world.md)
- [Animation and timing](../wiki/animation.md)
- [Pathing](../wiki/pathing.md)
- [Monster AI](../wiki/monster-ai.md)
- [The server frame](../wiki/server-frame.md)

### Reference

- [Quirks: the traps a faithful rebuild must keep](../wiki/quirks.md)
- [Glossary](../glossary.md)
