# Wiki: how Diablo II 1.14d works

These pages explain, for a person who has played Diablo II: Lord of Destruction, how the game builds a level, fills
it with monsters and objects, and decides what drops. They are written in plain prose with diagrams and small worked
examples, and they leave out the addresses, evidence tags and pseudocode that the [specs](../specs/README.md) carry.

Three rules make the pages safe to rely on ([ADR-0012](../adrs/0012-human-wiki.md)):

- **No claims of their own.** Every page restates reviewed specs only. Its front matter lists them, with the date of
  the spec version it was written from, and every section links the spec sections it explains. If a page and a spec
  disagree, the spec is right.
- **Nothing hidden.** Where a spec says something is read from the code but not yet confirmed by a run, or is still
  unknown, the page says so in words. Each topic page ends with a *What is not known yet* section.
- **Not published.** The wiki is part of the repository, like the specs; it is no site and no export.

D2 terms are explained in the [glossary](../glossary.md); each page links it on a term's first use.

## Reading order

Start with randomness: almost everything else is a sequence of random draws on some seed, and the pages after it refer
back to it. Then follow the game from the map to the loot, and on to the characters and the fights between units.

| # | Page | Read this to learn… |
|---|---|---|
| 1 | [Randomness](randomness.md) | how the game's random number generator works, how one game seed becomes a tree of seeds for acts, levels, rooms and units, and why the same seed gives the same map |
| 2 | [Game data](game-data.md) | what the excel tables are, which form of them the game loads, how one table points into another, and how string tables and calc formulas are read |
| 3 | [Levels](levels.md) | how a level is built: acts, levels and rooms, the preset, maze and outdoor generators, room tiles, preset maps, warps and the collision grid, and how rooms are released when no player is near and restored when one comes back |
| 4 | [Monsters](monsters.md) | which monsters a level can have, how a room is populated, packs and minions, champions, uniques and superuniques, and their stats |
| 5 | [Objects](objects.md) | how shrines, chests and other objects are placed and created, what happens when you operate one, and what a chest drops |
| 6 | [Items](items.md) | one monster drop end to end: treasure class, quality and magic find, uniques and sets, affixes and rare names, base stats, ethereal and sockets |
| 7 | [Other item paths](items-other-paths.md) | the items that do not come from a monster drop: socketing and runewords, the Horadric Cube, vendors and gambling, quest drops and rewards |
| 8 | [Prices, repair, gold and wear](economy.md) | what an item costs to buy, sell, gamble and repair and why, how gold is paid, capped, dropped and lost on death, and how items wear out in melee and replenish |
| 9 | [Using items, and the inventory](inventory.md) | what the server does when a player uses an item (the gate, the use kinds, healing and mana potions with their two draws, rejuvenation, identify, the cube), where an item can go (pages, the stash, the belt, stacks), pickup and its reach, which cell a dropped item lands on, and how long an item lies on the ground before the sweep frees it; with what a game session showed, what an emulation showed and what is only read from the code kept apart |
| 10 | [Characters and hirelings](characters.md) | what a new character starts with, how experience and level-up work, how a kill's experience is shared in a party and what the number of players changes, and how hirelings are listed, hired and saved |
| 11 | [Combat](combat.md) | what happens when one unit hits another: the chance to hit, block and avoid, the damage build, resistances and absorb, crushing blow, open wounds, leech and the life change, and whose seed each draw is on |
| 12 | [Stats and states](stats-and-states.md) | how a character's final stats add up from items, set bonuses, passives and states, item requirements and the 136-frame refresh, how a timed state is applied, refreshed, refused, replaced and ended, group clears, the regeneration of life, mana and stamina, auras, and shrines and wells |
| 13 | [Skills and missiles](skills.md) | what the server does when a unit uses a skill: the request and its checks, the start and do functions, mana cost and delay, a skill's melee hit, charge-up skills and the finisher, the item-stat and skill handlers that react to hits and kills, summons, and a missile's creation, flight, collision and hit, with whose seed each draw is on, and the catalogue of the other numbered skill and missile functions: how to find one and which ones draw |
| 14 | [Saves](saves.md) | what a `.d2s` save file holds and how an item is stored in it |
| 15 | [Quests and travel](quests.md) | how the quest record is kept and loaded, which events reach the quest scripts and in what order, how the game creator's finished quests are switched off, a few quests bit by bit, the quest-seed draws, and how waypoints, act changes, town portals, warps and resurrection place a player |
| 16 | [Seed to world](seed-to-world.md) | how the pages above fit together in one game: the order in which the server builds levels, rooms, objects, monsters and drops from the game seed, which seed passes from one step to the next, and what (the player's walk, the fights) has to come from outside |
| 17 | [Animation and timing](animation.md) | how long a unit's actions take on the server: the animation record, the scheduled and every-frame clocks, the rate from speed stats and weapon, breakpoints, the do frame, hit recovery, the block and the get-hit roll, and how far a walking, running or knocked-back unit moves each frame |
| 18 | [Pathing](pathing.md) | how a unit's route is planned: the request and its refusals, the 17 path types and their planners, the two types that draw, the live grid planners read and why it is not the predicted one, corpses on each copy of the grid, who asks for a plan, and which types no stock request reached; with what the games showed, what an emulation showed and what is only read from the code kept apart |
| 19 | [Quirks](quirks.md) | the traps a faithful rebuild must keep, by class (arithmetic width and sign, rounding, wrap, edges, draw order, data-dependent branches, timing, multiplayer, deliberate oddities), the community claims that do not hold, and which entries were seen in play, which reached under emulation and which only read from the code |
| — | [How we know](how-we-know.md) | how the project works: the one binary, the three levels of confidence, runs, bit-exact and emulated reproduction, combat events, two-client games, what "not reachable on stock data" means, the sweep of inferred claims, and what "reviewed" means. Read it any time; it is the only page not based on a spec |

## Why the pages are cut this way

The wiki is one page per topic, except where the amount of material or a spec's fit asks for another cut:

- **Items are split in two.** The ordinary monster drop already draws on five specs (treasure classes, quality,
  uniques and sets, affixes, properties), so [Items](items.md) follows one drop end to end, and
  [Other item paths](items-other-paths.md) covers the four other ways an item is made or changed (sockets and
  runewords, the cube, vendors, quests). The second page links the first for the shared machinery.
- **The item economy gets its own page.** Prices, repair, gold and wear come from one spec
  ([item economy](../specs/items/economy.md)); [Prices, repair, gold and wear](economy.md) covers it, and
  [Other item paths](items-other-paths.md) links it from its vendor section.
- **Using items and the inventory get their own page.** Their specs ([item use](../specs/items/use.md) and
  [inventory](../specs/items/inventory.md)) cover the requests that use, move, pick up and drop an item, which no
  other page holds. [Items](items.md) and [Other item paths](items-other-paths.md) link it for what happens to an item
  after it is made.
- **Characters and hirelings get their own page.** Their specs (new characters and level-up, hirelings) fit no other
  topic. [Saves](saves.md) refers to it for what a new character's save
  holds and how a mercenary is stored.

Everything else is one page per topic. The string tables and calc formulas sit on
[Game data](game-data.md) with the excel tables: all three are about reading the game's data files.

## What the wiki does not cover

Only reviewed specs are covered, and every row of the [research map](../specs/README.md) that is reviewed has a page
here: randomness and seeds, the excel data, string tables and calc formulas, the level generators, monsters, objects,
item creation and the other item paths, the [item economy](../specs/items/economy.md), [item use](../specs/items/use.md) and the
[inventory](../specs/items/inventory.md), new characters, hirelings, saves, [combat formulas](../specs/combat/README.md),
[stats and states](../specs/stats/README.md), [quests and travel](../specs/quests/README.md), the composition of the core
specs, [seed to world](../specs/chain/README.md), [skills and missiles](../specs/skills/README.md) (their machinery, a named
tier of skills and the function catalogue of every other numbered skill and missile function), and
[animation and frame timing](../specs/anim/README.md), and [the path request and its planners](../specs/path/README.md). The room lifecycle
([drlg/lifecycle](../specs/drlg/lifecycle.md)) has no page of its own: it is the section
[Rooms that come and go](levels.md#rooms-that-come-and-go-release-and-restore) of the Levels page. Rows that are not
reviewed get no page.

The plans still open are listed in the [plan index](../plans/README.md). When one of them changes a spec, the page over it
is refreshed.

When a spec is updated after a page was written, the docs gate warns that the page may be stale until it is
refreshed.
