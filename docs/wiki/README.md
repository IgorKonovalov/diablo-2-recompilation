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
| 9 | [Characters and hirelings](characters.md) | what a new character starts with, how experience and level-up work, and how hirelings are listed, hired and saved |
| 10 | [Combat](combat.md) | what happens when one unit hits another: the chance to hit, block and avoid, the damage build, resistances and absorb, crushing blow, open wounds, leech and the life change, and whose seed each draw is on |
| 11 | [Stats and states](stats-and-states.md) | how a character's final stats add up from items, set bonuses, passives and states, item requirements and the 136-frame refresh, how a timed state is applied, refreshed, refused, replaced and ended, group clears, the regeneration of life, mana and stamina, auras, and shrines and wells |
| 12 | [Saves](saves.md) | what a `.d2s` save file holds and how an item is stored in it |
| — | [How we know](how-we-know.md) | how the project works: the one binary, the three levels of confidence, runs, bit-exact and emulated reproduction, combat events, two-client games, what "not reachable on stock data" means, the sweep of inferred claims, and what "reviewed" means. Read it any time; it is the only page not based on a spec |

## Why the pages are cut this way

The plan for the wiki ([plan 0036](../plans/done/0036-human-wiki-readme.md)) proposed one page per topic. Two changes
were made because of how much material there is:

- **Items are split in two.** The ordinary monster drop already draws on five specs (treasure classes, quality,
  uniques and sets, affixes, properties), so [Items](items.md) follows one drop end to end, and
  [Other item paths](items-other-paths.md) covers the four other ways an item is made or changed (sockets and
  runewords, the cube, vendors, quests). The second page links the first for the shared machinery.
- **The item economy gets its own page.** Prices, repair, gold and wear come from one spec written after the plan
  ([item economy](../specs/items/economy.md)); [Prices, repair, gold and wear](economy.md) covers it, and
  [Other item paths](items-other-paths.md) links it from its vendor section.
- **Characters and hirelings get their own page.** Their specs (new characters and level-up, hirelings) were reviewed
  after the plan was written and fit no other topic. [Saves](saves.md) refers to it for what a new character's save
  holds and how a mercenary is stored.

Everything else is one page per topic as planned. The string tables and calc formulas sit on
[Game data](game-data.md) with the excel tables: all three are about reading the game's data files.

## What the wiki does not cover

Only reviewed specs are covered, and every row of the [research map](../specs/README.md) that is reviewed has a page
here: randomness and seeds, the excel data, string tables and calc formulas, the level generators, monsters, objects,
item creation and the other item paths, the [item economy](../specs/items/economy.md) (plan 0043), new characters, hirelings, saves, and the first two simulation rows,
[combat formulas](../specs/combat/README.md) (plan 0037, closed 2026-10-17) and
[stats and states](../specs/stats/README.md) (plan 0041, closed 2026-10-17). The room lifecycle
([drlg/lifecycle](../specs/drlg/lifecycle.md), reviewed at the close of plan 0040 on 2026-10-17) has no page of its
own: it is the section [Rooms that come and go](levels.md#rooms-that-come-and-go-release-and-restore) of the Levels
page. Rows that are not reviewed get no page; the next simulation phase, skills and missiles, has no row on the
research map yet.

The plans still open are listed in the [plan index](../plans/README.md):
- **0038**, a sweep that tries to confirm inferred claims with another run, a re-check of kept logs or a second code
  path; its batches are still running, and the specs are re-tagged cluster by cluster;
- **0039**, backlog sweep 4: complete but for part of the [excel data](../specs/data/excel.md) spec, which goes with
  plan 0038's re-tag;
- **0042** (quests and travel): its code reading is reviewed, and its runs are next;
- **0043** (item economy): its runs are done and its spec is reviewed; the plan closes at the review of the spec's
  re-tag from the second run;
- **0044**, the multiplayer branches: its code reading is reviewed, and the owner has confirmed that the game's
  network port is closed to everything but the machine itself, so its two-client run waits only for two free slots.

When one of them changes a spec, the page over it is refreshed.

When a spec is updated after a page was written, the docs gate warns that the page may be stale until it is
refreshed.
