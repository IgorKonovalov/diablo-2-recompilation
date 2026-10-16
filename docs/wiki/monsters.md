---
based_on:
  - docs/specs/monsters/README.md 2026-10-16
  - docs/specs/monsters/pool.md 2026-10-16
  - docs/specs/monsters/spawn.md 2026-10-16
  - docs/specs/monsters/special.md 2026-10-15
  - docs/specs/monsters/stats.md 2026-10-16
  - docs/specs/drlg/collision.md 2026-10-15
---

# Monsters

This page explains how the game decides which monsters exist. It covers which classes each [level](../glossary.md) can host, how
a room gets filled the first time it becomes active, which of those monsters become champions, uniques or
[superuniques](../glossary.md), and what level, hit points, defence and experience each one is created with. It restates the
reviewed monster specs: the overview in [monsters/README](../specs/monsters/README.md#data-flow), the level pools
in [pool](../specs/monsters/pool.md#purpose), room population in [spawn](../specs/monsters/spawn.md#purpose),
special monsters in [special](../specs/monsters/special.md#purpose) and stats in
[stats](../specs/monsters/stats.md#purpose). The specs carry the exact arithmetic and [draw](../glossary.md) order; this page tells
the story. Where something is read from the code but not yet seen in a test run, or is still unknown, the page
says so.

## The big picture

There are four stages, and they use different [seeds](../glossary.md):

1. **At game creation** the game builds a [monster pool](../glossary.md) for every level from one seed taken from
   the [game seed](../glossary.md). It holds up to 13 classes per level.
2. **When a [room](../glossary.md) is activated for the first time**, the server's
   [population pass](../glossary.md) makes a number of attempts. Each attempt passes a density roll, picks a class
   from the pool and decides between a normal group and a [special](../glossary.md) one.
3. **Each monster is created** with its level and its hit points, defence and experience. These are set once,
   at that moment.
4. **A random special** becomes a champion or a unique by a roll on its own unit seed. It gets its [mods](../glossary.md) and its [minions](../glossary.md),
   and the mods change its stats. On the client side, a name is rolled from a small seed the server sends.

```mermaid
flowchart TD
  gc["Game created"] --> pools["Monster pools for all levels<br/>one region seed from the game seed"]
  act["Room activated for the first time"] --> gate{"Level has a density?"}
  gate -->|"no"| none["no random monsters"]
  gate -->|"yes"| att["Attempts per logic box<br/>density roll on the game seed"]
  pools --> pick
  att --> pick["Pick a class by rarity<br/>room seed"]
  pick --> typ{"Normal or special?<br/>room seed"}
  typ -->|"normal"| grp["Leader, group members, minions"]
  typ -->|"special"| boss["Boss placed"]
  boss --> cu{"Champion or unique?<br/>boss's own seed"}
  cu -->|"champion"| pack["one champion mod,<br/>pack of 1 to 3"]
  cu -->|"unique"| uniq["1 + difficulty mods,<br/>3 to 6 minions"]
  preset["Map preset"] --> su["Superunique or preset special"]
  grp --> create["Each monster created:<br/>level, hit points, defence, experience"]
  pack --> create
  uniq --> create
  su --> create
  create --> mods["Mod effects on the specials' stats"]
  mods --> name["Client builds the display name"]
```

Population draws on three seeds. The room's seed gives the class picks, the normal-or-special roll and every
position. The game seed gives the density roll of each attempt and one step for each monster created. The
leader's or boss's own unit seed gives the group size, the minion counts, the champion roll and the size of a
[champion pack](../glossary.md)
([spawn § Algorithm](../specs/monsters/spawn.md#algorithm),
[README § Data flow](../specs/monsters/README.md#data-flow)). That each monster's unit seed is made from one
game-seed draw is read from the code. Its exact value after creation is still taken from the logs (see
[Placement](#placement-where-each-monster-stands)).

## Which monsters a level can have: the pool

Every level gets a [monster region](../glossary.md) at game creation. It holds the level's pool plus copies of
its density and unique-count columns from `Levels`. All regions are built in one pass, in level id order, from
one region seed. That seed is set from the game seed's first draw after the game's seeds are initialised, and it
is thrown away when the build ends
([pool § A](../specs/monsters/pool.md#a-the-region-seed-sub_00547d20_monregionsinit),
[pool § B](../specs/monsters/pool.md#b-the-region-build-sub_005479c0_monregionsbuild)).

What this means for a player: **the pool is fixed per game, not per visit.** It depends on the game seed and the
difficulty only. The [map seed](../glossary.md) and the order in which you enter levels do not change it
([pool § Reimplementation notes](../specs/monsters/pool.md#reimplementation-notes)).

How one level's pool is picked ([pool § C](../specs/monsters/pool.md#c-the-pool-pick-sub_005475e0_monregionpool)):

- Normal difficulty picks from the level's `mon` columns. Nightmare and hell pick from `nmon`, in classic and
  expansion alike.
- The number of picks is the smallest of `NumMon`, 13 and the number of candidates. Each pick takes a random
  remaining slot, so a slot is never taken twice. A class named in two slots can still end up in the pool twice,
  and every test run had 6 to 10 regions that held one class twice.
- In a level with `rangedspawn` set, the first pick is redrawn up to 20 times until it lands on a ranged class.
  After 20 redraws the last class drawn is kept, whatever it is.
- A picked class whose `isSpawn` is 0 is dropped after the pick, and the pick still counts. *Mountain Top* holds
  three such classes, so its pool is empty.
- `Rarity` is only copied at this stage. It is used later, when a room picks from the pool.

The candidate count is read from the code as the number of *leading* filled slots, stopping at the first blank.
Stock data has no gaps, so a test run cannot tell this apart from "the number of filled slots". The nightmare and
hell pools were checked in natural games for one seed only. A classic normal game was not logged; by the code it
reads `mon` like an expansion game.

### Appearance sets

Each kept entry also gets up to three [appearance sets](../glossary.md), one variant per body component, drawn on
the same region seed. Every set after the first differs from the first in at most two components. These draws
come between one level's picks and the next level's, so a reimplementation has to make them even if it never
draws a monster. If it skips them, every later level's pool comes out wrong
([pool § D](../specs/monsters/pool.md#d-appearance-sets-sub_005bdb20_monvariantroll),
[pool § Draw order on R](../specs/monsters/pool.md#draw-order-on-r)).

A short example from the spec's worked example ([pool § Worked example](../specs/monsters/pool.md#worked-example),
`-seed 1`, normal, expansion): *Act 1 - Wilderness 2* has four candidates, `brute1`, `corruptrogue1`,
`fallenshaman1` and `cr_lancer1`, and `NumMon` 3. The three draws take `brute1`, then `fallenshaman1`, then
`cr_lancer1`, so `corruptrogue1` is left out of that game's pool for that level.

## Monster level per difficulty

The [monster level](../glossary.md) (mlvl) is set each time the server creates a monster. It depends on the
class and the level the monster stands in
([pool § E](../specs/monsters/pool.md#e-the-monster-level-sub_00573cb0_monstatsinit)):

| Game | Normal | Nightmare and hell |
|---|---|---|
| Expansion | MonStats `Level` | the area's `MonLvl2Ex` / `MonLvl3Ex` |
| Classic | MonStats `Level` | MonStats `Level(N)` / `Level(H)` |

The exceptions are as follows:

- Classes with `noRatio` (player summons and pets) and `boss` classes keep MonStats `Level(N)`/`Level(H)` even
  in expansion nightmare and hell. The `boss` rule was seen with Andariel: level 49 in nightmare and 75 in hell,
  not her area's 43 and 73. That the other `boss` classes behave the same is read from the code, since only
  Andariel was created in a run.
- A [mercenary](../glossary.md) is created at its normal-difficulty `Level` (1) in every difficulty, and its
  level and stats are then overwritten from the hireling table.
- The classic area-level columns `MonLvl1..3` gave no monster's level in any logged game, and by the code they
  never do. In expansion normal the area's `MonLvl1Ex` is not used either.

The logged cases from the spec: in *Jail Level 1*, two classes with MonStats levels 10/40/70 are created at 41
(nightmare) and 71 (hell) in an expansion game, and at 40 and 70 in a classic game. In *Stony Field*, expansion
normal, `zombie2` gets 2 (its MonStats `Level`), not the area's 4.

Still open or unconfirmed: a classic normal game was not logged, so its levels rest on the code. When the
monster's level has no `Levels` record the code returns 1, but this was never exercised. Town NPCs in expansion
nightmare or hell would take their town's blank area level, 0, which their MonStats level also gives, so the runs
cannot tell the two sources apart.

## Critters are not population

Ambient [critters](../glossary.md) such as chickens and bugs are a separate, client-side draw for each room, on
the room's seed. They never read the monster pool. Each of up to four critter slots makes one roll against its
percentage. A slot that passes creates `MinGrp` plus a random amount below `MaxGrp − MinGrp`, so `MaxGrp` itself
is never reached when the two differ. The draws made while each critter is created are not read yet, so the slots
after the first one that creates critters are not predicted
([pool § F](../specs/monsters/pool.md#f-critters-sub_0046c460_clientcritters-not-from-the-pool)).

## When a room is populated, and how many attempts

The population pass runs on the server only, once per room, the first time it is activated. The wanderer tick, the
room's preset monsters and objects come first, then the pass, and then the room is marked as populated
([spawn § A](../specs/monsters/spawn.md#a-when-the-pass-runs-and-the-room-seed-before-it)). That the client
never runs this pass is read from the code. On the client, the room's own content is the critter draw.

**The gate** ([spawn § B](../specs/monsters/spawn.md#b-the-gate)). A level whose density (`MonDen` for the
difficulty) is 0 gets no random population, and neither does a room flagged "no population" by the map
generator. The gate also counts every room of the level that reaches it. That count is the level's "rooms
visited", which the special catch-up below uses. A test for Chaos Sanctuary that closes the gate when a quest
byte is set is read from the code but was not exercised.

**Density** ([spawn § C](../specs/monsters/spawn.md#c-density-attempts-per-logic-box)). The room is split into its
[logic boxes](../glossary.md). Each box gets `(5h ÷ 3) × (5w ÷ 3)` attempts, where `h` and `w` are its size in
tiles, so an 8 × 8-tile box gets 169 attempts. Each attempt draws on the game seed and passes when
`draw mod 100000 ≤ MonDen`, a chance of `(MonDen + 1)/100000`. The test is "at most", so a draw equal to the
density passes. A density above 10000 is clamped to 10000, and the stock maximum is 2200.

## Picking a class, and normal versus special

**The class pick** ([spawn § D](../specs/monsters/spawn.md#d-the-class-pick)) is a weighted draw on the room seed
over the pool's `Rarity` values, so a class with `Rarity` 0 is never picked. A class flagged `placespawn` (in
stock data the three crow nests) turns into its `spawn` class with a further room draw: 79 times in 100 for a
normal pick, 99 in 100 for the special pick of nightmare and hell. In normal difficulty the special class comes
from the level's `umon` columns with no substitution.

**Normal or special** ([spawn § E](../specs/monsters/spawn.md#e-the-type-roll-and-the-1--2-fold)) depends on the
level's live count of specials, compared with its `MonUMin` and `MonUMax`:

```mermaid
flowchart TD
  s["live special count of the level"] --> a{"below MonUMin?"}
  a -->|"yes"| d1{"room draw below<br/>visited share of rooms?"}
  d1 -->|"yes"| sp["special"]
  d1 -->|"no"| b
  a -->|"no"| b{"below MonUMax?"}
  b -->|"yes"| d2{"room draw at most 5<br/>(6 in 100)?"}
  d2 -->|"yes"| sp
  d2 -->|"no"| last["one more room draw,<br/>always normal"]
  b -->|"no"| last
  last --> nm["normal group"]
```

- While the level has fewer specials than `MonUMin`, an attempt that passed density is special with a chance of
  about the explored fraction of the level (rooms visited ÷ rooms). The catch-up therefore grows as you explore,
  but it is not a guarantee.
- Below `MonUMax`, a flat 6 in 100 applies to every attempt that passed density. A community page describes 5 in
  100 per room, with `MonUMax` capping successful attempts. In 1.14d it is per attempt, and a run caught a special
  at exactly the boundary value.
- A level with `MonUMin` = `MonUMax` = 0 gets no random champions or uniques.
- The last draw can return a "type 1", but the pass turns it into a normal group. The champion-formation
  branch for type 1 is never reached. The draw still happens.
- The count is live and builds up over the game. It goes up for each random boss, each champion-pack member, each
  preset special and each superunique. The increments for random bosses and pack members are confirmed by a run.
  The preset and superunique increments, and the decrease when a special leaves its level, are read from the code
  only.

## Groups and minions

**A normal group** ([spawn § F](../specs/monsters/spawn.md#f-the-normal-group)) is a leader plus a uniform
`MinGrp … MaxGrp` total, drawn on the leader's seed. Members whose placement fails are simply missing. Fallen and
scarab classes always form a group of one, and their company comes from their minions instead.

**Minions** ([spawn § I](../specs/monsters/spawn.md#i-monstats-minions)): every leader, group
member and champion-pack member of a class with `minion1` brings `PartyMin … PartyMax` minions of `minion1`, or
of `minion1` and `minion2` in turn. A shaman-type class therefore brings its own party for each member. Bosses,
unique minions and minions themselves bring none. The minion count is drawn on the leader's seed *before* its
group size.

The `sparsePopulate` column would add a roll on the game seed before a group. Stock data never reaches it, because
the only class with a value is the evil hut, which appears only as a map preset. What the roll does is read from
the code only: the group would spawn with probability `(value + 1)/100`, and nothing would take its place.
Community descriptions disagree with this, and no stock-data run can settle it.

The code read for this pass has no read of the [player count](../glossary.md). Group sizes, minions and density do not scale with
players by that code, but multiplayer games were not logged
([spawn § Open questions](../specs/monsters/spawn.md#open-questions)).

## Placement: where each monster stands

A leader or boss gets a random point in its logic box: up to 20 tries of two room draws each, rejecting points too
close to the level's [warp points](../glossary.md) or its waypoint point (the level's `WarpDist`). Then a placement test checks the exact point. Group members,
minions and pack members are placed in growing square rings around their leader, each ring starting at a random
cell. The walk tests cells against the room's [collision grid](../glossary.md)
([spawn § H](../specs/monsters/spawn.md#h-placement-spawnpospick-and-monspawntry)). Points to know:

- Every placement costs room draws, even when it fails. An exact placement still makes 3 room draws, and the
  random point's test is made twice: once as a probe, once to create the monster.
- The grid changes as the pass runs. A monster just placed blocks later ones through its centre mark, so a later group
  member may have to take another cell.
- The near-warp test can activate another room in the middle of the pass and, in some levels, step that level's
  seed ([drlg/collision](../specs/drlg/collision.md#i-nearwarptestgame-room-x-y-and-its-side-effects)).

Each creation steps the game seed once ([spawn § J](../specs/monsters/spawn.md#j-creation-and-the-unit-seed)).
The new monster's own seed comes from that step. On 914 of 916 logged creations it was 2 steps past its starting
value when the pass first drew on it, and 6 and 15 steps on the other two. The spawn spec takes that seed as an input. The stats
spec names the two usual steps, the appearance pick and the hit-point draw
([stats § B](../specs/monsters/stats.md#b-monstatsinit-in-order)); the creations that start from another seed are
still taken from the logs.

**Wanderers** ([spawn § K](../specs/monsters/spawn.md#k-wanderers-the-tick)). Every room in the update walk takes one
room-seed draw per tick; that it goes on after the room is populated is read from the code. Rarely (1 in 32 768 ticks), and only in a level with `MonWndr` set, a
wanderer roll follows. It never fired in a run, so the rest of it is read from the code only: its class list holds
one class, for Act I only. By the code, `MonWndr` gates only this roll, and watching it in play found no other read
of it. It does not decide whether monsters roam, which is what a community page says.

## Champions and uniques

When the type roll says "special", the pass makes a **second** class pick: from the level's `umon` columns in
normal difficulty, from the pool in nightmare and hell. It places the boss and only then decides what the boss is
([spawn § G](../specs/monsters/spawn.md#g-the-special-group-boss-champion-or-unique),
[special § A](../specs/monsters/special.md#a-champion-or-unique)):

- **Champion** when a draw of `Range(100)` on the boss's own seed is below 20 (the `constants` value of MonUMod row
  0), so 20 in 100. A champion gets exactly one champion mod, then a
  champion pack of 1 to 3 more monsters of its class.
- **Unique** otherwise. A unique gets `1 + difficulty` unique mods (1, 2 or 3) and 3 to 6 minions.

**The mod picks** ([special § B](../specs/monsters/special.md#b-the-weighted-picks)) are weighted draws over the
`MonUMod` rows allowed for this monster, by the difficulty's `cpick` or `upick` weight. With stock data every weight
is 1 (champion) or 6 (unique), so the allowed candidates are equally likely:

| | Classic | Expansion |
|---|---|---|
| Champion mods | `champion` only | `champion`, `ghostly`, `fanatic`, `possessed`, `berserk` |
| Unique mods | 12 in normal, 13 in nightmare and hell (`resist` joins) | the same |

A row can also be refused for the class. `teleport` needs the class to have the `A1` mode, `fast` the `WL` mode, and
`multishot` a class that is neither `isMelee` nor `nomultishot`. The one stock exclusion, `lightning` on
sand leapers, is read from the code but was never rolled in a run. A unique never gets the same mod twice. A unique's
mod count costs one extra draw (`Range(1)`, which always gives 0 but still steps the seed).

**Pack members and preset champions** ([special § F](../specs/monsters/special.md#f-champion-pack-members-and-preset-champions))
are not rolled. Each one always gets mod 16 `champion`, whatever the boss drew. Each counts as a special, and each
brings its own MonStats minions if its class has them. They are not linked to the boss as minions.

**Map presets** ([special § H](../specs/monsters/special.md#h-monplace-presets)) can also make specials. One preset
kind makes a unique, its class picked as for a random special, at a random point of the room, with no champion roll. Another makes a champion
at the preset point, with mod 16 and a champion pack. Both were reproduced in Tristram.

## Unique minions and mod transfer

A unique's 3 to 6 minions are of its `minion1` class, or of its own class when it has none. `PartyMin`/`PartyMax`
play no part here. As each minion is created, it copies the boss's mods that have `xfer` set. With stock data that is
every unique mod except `aura`, so **a unique's minions carry its rolled mods, except the aura**. The minion's own
mods, if any, stay first in its list
([special § E](../specs/monsters/special.md#e-unique-minions-and-transfer)).

Read from the code, not yet confirmed by a run: the copy is the list the server sends and other code reads, but the
effects reach a minion through the boss's mod handlers running on each group member, and a minion's own handlers are
never called for its copied list.

## Mod handlers and the name seed

After the minions, each special runs its mod handlers in a fixed order: the always-run mods `rndname`,
`hpmultiply`, (`light`, which has no handler) and `leveladd`, then its own list in slot order. A mod listed twice runs
twice ([special § C](../specs/monsters/special.md#c-mod-handlers),
[special § D](../specs/monsters/special.md#d-per-mod-draws)).

- `rndname` is the only handler that draws on a lasting seed. It steps the special's unit seed once and keeps the
  low 16 bits as the [name seed](../glossary.md). Champions and pack members run it too.
- `aura` draws on a *local* seed made from the name seed, which no other seed sees. It picks one of the aura rows
  whose minimum level the monster has reached: Might, Holy Fire, Blessed Aim, Holy Freeze, Conviction and
  Fanaticism from level 0, and Holy Shock from level 20. The aura table itself is read from the game's code, and a
  Thorns row needs level 999.
- Every other handler only writes stats (see [What the mods do](#what-the-mods-do-to-stats)).

The [draw order](../specs/monsters/special.md#draw-order-on-the-unit-seed) on the boss's seed is: for a champion,
the champion roll, its one pick, `rndname`, then the pack size. For a unique, the champion roll, `Range(1)`, one draw
per mod, the minion count, then `rndname`.

## Superuniques

A superunique is placed by a [preset unit](../glossary.md) in the map and built from its
`SuperUniques` row ([special § G](../specs/monsters/special.md#g-superuniques)):

1. **Placement.** At the preset point, or anywhere in the room when the row's `AutoPos` is set. A row with `Stacks`
   0 can be placed only once per game. That refusal is read from the code but was not reached in a run.
2. **Fixed mods** `Mod1`–`Mod3` are written as they are and skip the eligibility tests. That they skip the tests is
   read from the code.
3. **Extra mods**: `difficulty` unique picks, so 0, 1 or 2, with no `Range(1)` before them. An extra never repeats a
   fixed mod.
4. **Minions**: `MinGrp + d … MaxGrp + d`, where `d` is the difficulty. Rakanishu (8 and 8 in his row) got 8, 9 and 10
   minions in normal, nightmare and hell. A row with both bounds 0 still makes one draw and gets no minion.
5. **A tail per record** for a few superuniques, such as Radament's extra skeletons, the Countess's set-up and
   various quest hooks. All the tails are read from the code only.
6. Mod 22 `questcomplete` is appended last.

Also read from the code only: the `thief` mod is dropped from a row's fixed mods, a fixed `aura` would run its
handler a second time, and a superunique that already holds 5 or more mods gets nothing below placement.

## Names

The name is built on the client ([special § I](../specs/monsters/special.md#i-names)):

- A **random unique** rolls its name from the name seed the server sends. The client keeps only the low byte of that
  seed, so **only 256 random-unique names can exist**. It draws a suffix and then a prefix. Then, with 50 in 100, it
  discards that pair and draws an appellation, a new suffix and a new prefix, giving a name of prefix, suffix and appellation
  (in one recorded game, from the keys `Fire`, `lust` and `the Mauler`). Every name roll of a test run followed this.
  The roll runs on its own seed, so by the code it cannot affect any server seed.
- A **champion** shows a word for its champion mod in front of the class name. A **superunique** shows its row's
  `Name`. Both are read from the code. Where a unique's random colour is drawn is not known.

## Stats at creation: hit points, defence, experience

Every monster gets its stats once, when it is created
([stats § B](../specs/monsters/stats.md#b-monstatsinit-in-order)). In order:

1. The appearance pick (one draw on the unit seed).
2. The player bonus, then the level, the resistances and block straight from `MonStats` for the difficulty. Blank
   cells count as 0.
3. Hit points, defence and experience as `MonLvl` value × `MonStats` value ÷ 100, from the `MonLvl` row of the
   monster level ([stats § A](../specs/monsters/stats.md#a-muldiv-and-monlvlstats)). `noRatio` classes take the
   `MonStats` value as it is.
4. One hit-point draw between the scaled minimum and maximum. It still steps the seed when the two are equal.
5. The player bonus added to hit points and experience, then the regeneration value.
6. In classic nightmare and hell, the classic factors (below). Then skills, [MonProp](../glossary.md) and monster
   equipment.

A surprise from the runs: **single-player games read the `MonLvl` columns prefixed `L-`**, which a community
source reserves for ladder games. In 3 954 nightmare and hell creations where the two column sets differ, every one
matched `L-`. The two sets differ only in nightmare and hell defence and in hell hit points.

The game stores hit points times 256. Read from the code but never reached: a hit-point cap for very large values,
the case of a minimum above the maximum, and the overflow branches of the arithmetic. Skills get the difficulty's
`MonsterSkillBonus` added to their level, also read from the code only.

**MonProp** ([stats § F](../specs/monsters/stats.md#f-monprop-at-creation)) gives every monster
of a class its row's properties for the difficulty, special or not, with any value range rolled on the unit seed.
On stock data only `thorns` has a range, and a test run reproduced it. Stock `chance` is 0 everywhere, so the
`chance` roll is never reached. No normal-difficulty row can be reached on stock data, by the code read. Monster
equipment (`MonEquip`) is read from the code only. No class that has it was met.

## The player count

([stats § C](../specs/monsters/stats.md#c-the-player-count-sub_00573930_monplayerbonus))
The player count is the number of living players, raised to the `/players` setting. Hostile
monsters get **+50 % hit points and +50 % experience for each player beyond the first**, so +350 % at 8 players.
Town NPCs, critters, hirelings, summons and a few neutral classes get no bonus; this is read from the code.

**The count is applied once, at creation.** A test run changed `/players` 13 times and compared 302 live monsters
at each change: none changed. Monsters created after the change get the new count. A monster that is re-created when
its room comes back from inactive keeps some of its first instance's values (level, max hit points, experience). The
code that does this is not read yet, so it is an open question. The formula above 8 players is read from the code
only.

## Classic nightmare and hell

A classic (non-expansion) nightmare or hell monster first gets its stats from the `MonLvl` row of its MonStats
`Level(N)`/`Level(H)`, and is then cut down
([stats § D](../specs/monsters/stats.md#d-classic-nightmare-and-hell-sub_0063eef0_monclassicdiffadjust)):

| Stat | Nightmare | Hell |
|---|---|---|
| Max hit points | × 1/2 | × 1/2 |
| Defence | × 10/12 | × 10/12 |
| Experience | × 10/17 | × 10/26 |

Its level stat is then rewritten to its normal `Level` + 25 × difficulty. So **a classic nightmare or hell monster
uses two levels**: one chose its base stats, the other is what everything later sees, including the mods' level
bonus, the enchant damage and the aura. In classic hell a run logged aura uniques whose `Level` is 18 drawing their
aura at level 71 (18 + 50 + 3).

When max hit points change, current hit points follow in proportion
([stats § E](../specs/monsters/stats.md#e-the-stat-callback-sub_0055b800_monstatcallback-stat-7)). The calculation
is done in floating point and truncated. The run settles the rounding mode. That the precision is 53 bits rests on
the code. Whether a graphics renderer could change that precision is an open question.

## What the mods do to stats

The handlers run in the order of [Mod handlers](#mod-handlers-and-the-name-seed). "Group member" means a minion of a
unique or superunique. Champion-pack members run their own pass as champions
([stats § G](../specs/monsters/stats.md#g-the-mod-handlers-stat-effects)). A selection (percentages from `MonUMod`'s
constants, normal / nightmare / hell):

| Mod | On the special | On its minions |
|---|---|---|
| `hpmultiply` (always) | champion +200 / +150 / +100 % hit points; unique +300 / +200 / +100 % | +100 / +75 / +50 % |
| `leveladd` (always) | level + 3, experience × 5 | the same |
| `champion` | level − 1, experience − 2/5, more damage and to-hit (scaled by [CDB](../glossary.md)), speed + 20 if the class has a `Velocity` | nothing |
| `possessed` | + 100 % hit points on top, then the champion part | nothing |
| `berserk` | − 75 % hit points, large damage and to-hit bonus, no champion part | nothing |
| `fire` / `cold` / `lightning` | enchant damage from the level's `MonLvl` damage, resistance + 75 | weaker enchant, no resistance |
| `spectralhit` | cold, fire, lightning resistance + 20 each (below 75) | nothing |
| `stoneskin` | defence × 2, damage resistance + 50 | nothing |

Notes the spec makes a point of:

- **Spectral Hit adds 20, not the 40 of community pages.** Seen in 17 uniques of a run.
- **A berserker ends at + 3 levels**, every other champion at + 2 (`leveladd` + 3, `champion` − 1). This was shown
  by a forced test run with edited data, which backs the handler only, not how often `berserk` appears.
- **Mod order matters.** The resistance mods stop adding once two resistances are already at 100 or more, and each
  mod checks this when it runs, so an earlier mod can block a later one.
- The `ChampionDamageBonus` column (90 / 75 / 66) also scales a unique's `strong` bonus. That `UniqueDamageBonus`
  is never read comes from the code; the two columns are equal in stock data, so play cannot tell them apart.
- Read from the code only: the `poisonhit` and `always_run_ai` handlers, the halving for will-o'-wisp classes, and
  the `ghostly`/`fanatic`/`possessed`/`berserk` handlers on group members.

To-hit and damage are not creation stats. They are computed each time the monster enters an attack mode
([stats § H](../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only)). The random draws of that
step are confirmed by the combat run: one draw of 100 for each elemental group of that attack mode whose chance is between 1 and 99, one
draw of 5 for one element type, and nothing else. The formulas of the values it writes are read from the code only,
because the combat run took those values as given. By the code, the expansion adds 6.25 % damage per player beyond the
first in nightmare and hell only, and a `noRatio` class (a summon or pet) ends up with no elemental damage at attack
time, because its elemental values are written to one place and read from another. The attack itself is on the
[combat](combat.md) page.

## Worked examples

### A room in Dark Wood

Copied from [spawn § Worked example](../specs/monsters/spawn.md#worked-example): `-seed 1`, expansion hell, level 5
*Dark Wood*, one room of a recorded game.

The region holds three classes: `fallen2` (rarity 2), `cr_lancer2` (1) and `quillrat2` (2), rarity sum 5. Density
is 520, `MonUMin` 7, `MonUMax` 9, and the level already has 7 specials. The room has one 8 × 8-tile box:
`(40 ÷ 3) × (40 ÷ 3) = 169` attempts.

| Attempt | Density draw | Class | Type roll | Result |
|---|---|---|---|---|
| 1–45 | above 520 | — | — | nothing |
| 46 | 504, passes | `Range(5) + 1` = 4 → `quillrat2` | 7 specials is not below `MonUMin` 7, so no catch-up; below `MonUMax`: 51 > 5; last draw 24 → 1 → normal | leader + `Range(3)` = 2 members |
| 90 | 31 | 5 → `quillrat2` | 70, then 17 → normal | a group of one |
| 100 | 520, equal to the density, passes | 2 → `fallen2` | 34, then 92 → normal | fallen: group of one, plus `2 + Range(3)` = 2 `fallen2` minions |
| 101–169 | above 520 | — | — | nothing |

During attempt 46, member 2's ring walk finds member 1 standing on a cell and moves on to the next one. The room ends
with seven monsters: three `quillrat2`, one more `quillrat2`, and a `fallen2` with two `fallen2` minions. The level's
special count stays at 7.

### A unique group and its name

Copied from [special § Example 2](../specs/monsters/special.md#example-2-a-unique-group-expansion-nightmare):
expansion nightmare, *Arreat Plateau*, a random boss of class `blunderbore6`.

| # | Draw on the boss's seed | Result |
|---|---|---|
| 1 | `Range(100)` | 36, not below 20: **unique** |
| 2 | `Range(1)` | 0; mod count 0 + 1 + 1 = 2 |
| 3 | 13 candidates of weight 6, total 78: `Range(78)` | 21 → `resist` |
| 4 | 12 left, total 72: `Range(72)` | 68 → `aura` |
| 5 | minion count `Range(4)` | 0 → 3 minions, each copying `resist` (not `aura`) |
| 6 | `rndname` step | name seed 33102 |
| — | `aura` on a local seed from 33102, level 63, 7 rows | 6 → Holy Shock |

On the client, 33102 keeps its low byte, 78. On a seed made from 78 it draws suffix 37 (`BangUM`) and prefix 47
(`DoomUM`), then `Range(100)` = 55, which is not below 50, so there is no appellation. The name is "Doom Bang".

### A possessed champion's stats

Copied from [stats § Example 2](../specs/monsters/stats.md#example-2-a-champion-sk_archer7-class-576-frozen-tundra-mod-possessed):
`sk_archer7` in *Frozen Tundra*, expansion hell, `/players 8`, monster level 81 (the area's `MonLvl3Ex`). The `MonLvl`
row 81 gives hit points 5722, defence 1581 and experience 45759. The class's hell `MonStats` give 70, 100, 100 and 95.

| Step | Value |
|---|---|
| hit-point range | 4005 … 5722; draw 65 → base 4070 |
| + 350 % for 8 players | 18315 hit points (stored as 4688640) |
| defence, experience | 1581; 43471 + 152148 = 195619 |
| `hpmultiply`, champion in hell (+100 %) | stored 9377240 |
| `leveladd` | level 84, experience 978095 |
| `possessed` (+100 %) | stored 18754440 |
| champion part | level 83, experience 586857; damage + 66, to-hit + 49, speed 75 + 20 = 95 |

## What is not known yet

Each spec's *Open questions* has the full list: [pool](../specs/monsters/pool.md#open-questions),
[spawn](../specs/monsters/spawn.md#open-questions), [special](../specs/monsters/special.md#open-questions),
[stats](../specs/monsters/stats.md#open-questions). The ones that bear on this page:

- **Pools:** the classic normal game (pool and monster level) and the no-record fallback are not logged. Natural
  nightmare and hell pools are checked for one seed, with Act I visited.
- **Population:** what `sparsePopulate` really does (unreachable on stock data, and the community sources
  disagree), and multiplayer games, which were not logged. Also the rare creations whose unit seed is 6 or 15 steps on
  instead of 2 (their seed is taken from the logs), an unidentified room field the wanderer roll tests, and when a populated room restores its
  inactive monsters. Many guard exits and rare branches were never reached: the evil hut object, the tentacle-head
  minions, the wanderer spawn, and others listed in the spec. Monster positions also depend on inputs no spec yet
  produces end to end, namely the object marks on the collision grid and one waypoint point.
- **Specials:** whether a `MonUMod` row with `champion` 0 could ever be a champion mod (no stock row tests it, and a
  community source claims it can). What calls the code that turns an existing monster into a special. Where a unique's
  colour is drawn. The superunique tails, the `lightning` exclusion, `thief`, the `Stacks` refusal, Blood Raven's and
  the act bosses' fixed names, and the restore of inactive specials are read from the code only.
- **Stats:** what a monster re-created from an inactive room keeps, whether a graphics renderer can change the
  floating-point precision of the hit-point rescale, the will-o'-wisp halving, and the unreached branches (`poisonhit`,
  `always_run_ai`, monster equipment, a `MonProp` slot with a chance, more than 8 players, the overflow branches).
  The formulas of the attack-time to-hit and damage values were not asserted by a run.

## Where to read more

- The specs: [monsters overview](../specs/monsters/README.md#data-flow),
  [pool](../specs/monsters/pool.md#reimplementation-notes), [spawn](../specs/monsters/spawn.md#reimplementation-notes),
  [special](../specs/monsters/special.md#reimplementation-notes), [stats](../specs/monsters/stats.md#reimplementation-notes).
  Each *Reimplementation notes* section lists the traps for someone rebuilding the system.
- The [glossary](../glossary.md) for D2 terms.
- Related wiki pages: [randomness](randomness.md) (seeds and draws), [levels](levels.md) (rooms, logic boxes, the
  collision grid), [objects](objects.md) (what fills a room before the monsters), [items](items.md) (what a monster
  drops) and [how we know](how-we-know.md).
