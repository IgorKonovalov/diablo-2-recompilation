# Specs — research map

This is the deliverable. Each subsystem gets a directory `docs/specs/<subsystem>/` containing a
`README.md` (overview, data flow, entry points) plus one file per algorithm. The `architect` owns
this map; the `spec-writer` owns the files under it.

Status values: `not started` · `findings in progress` · `draft spec` · `reviewed`

Scope is set by [ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md) and extended by
[ADR-0002](../adrs/0002-scope-creation-paths-and-enablers.md). The table has three bands. **Core**
is the original goal. **Enablers** are systems the core can't be reproduced without.
**Creation paths** are other callers into the core item and monster code. Core rows come first,
so "the original three areas are done" stays visible.

### Core

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `rng`: seed state, step, range, seed tree | — | — | not started |
| `items/tc`: treasure class resolution, picks, NoDrop, player-count scaling | rng | TreasureClassEx, ItemRatio, MonStats | not started |
| `items/quality`: unique/set/rare/magic/superior/normal/low roll; magic find | rng, items/tc | ItemRatio, ItemTypes | not started |
| `items/affixes`: alvl, prefix/suffix selection, rare affix counts, automagic | rng, items/quality | MagicPrefix/Suffix, RarePrefix/Suffix, AutoMagic, ItemTypes | not started |
| `items/uniques-sets`: candidate selection, fallback rules | rng, items/quality | UniqueItems, SetItems, Sets | not started |
| `items/properties`: stat rolls, sockets, ethereal, durability, defense | rng | Properties, ItemStatCost, Weapons/Armor/Misc | not started |
| `monsters/pool`: which monster types a level can host | rng | Levels, MonStats, MonLvl | not started |
| `monsters/spawn`: packs, density, placement, minions | rng, monsters/pool, drlg, drlg/collision | Levels, MonStats, MonPlace | not started |
| `monsters/special`: champions, uniques, superuniques, mod rolls, unique name rolls | rng, data/strings | MonUMod, SuperUniques, UniquePrefix/Suffix/Appellation | not started |
| `drlg/overview`: act → level → room hierarchy, generator dispatch | rng, rng/seeds | Levels, LvlTypes, LvlPrest | not started |
| `drlg/preset`: DS1 preset maps and their substitutions | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/maze`: maze generator (dungeons and caves) | drlg/overview | LvlMaze, LvlPrest | not started |
| `drlg/outdoor`: wilderness generator, borders, paths | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/warps`: inter-level links and placement | drlg/overview | LvlWarp, Levels | not started |
| `objects`: object/shrine/chest placement and operation | rng, drlg, drlg/collision | Objects, ObjGroup, Shrines | not started |

### Enablers (ADR-0002)

| Subsystem | Depends on | Key tables / formats | Status |
|---|---|---|---|
| `data/excel`: which form is loaded (`.bin`/`.txt`), record layout, code→index lookups, TC vs TCEx | — | all excel; fmt: excel-bin | not started |
| `data/calc`: formula bytecode VM (`*code.bin`) and the columns that index into it | data/excel | itemscode/misscode/skillscode/skilldesccode.bin | not started |
| `data/strings`: string-table lookup by key/index, as used by name rolls | data/excel | fmt: tbl | not started |
| `rng/seeds`: game seed → act → level → room → unit seed derivation | rng | — | not started |
| `drlg/collision`: room collision grid from tiles, placement tests used by spawn/objects | drlg/overview | LvlTypes, LvlPrest; fmt: dt1, ds1 | not started |
| `save/d2s`: save layout, item bitstream, persisted seeds and quest state (also the experiment harness) | items/properties | ItemStatCost; fmt: d2s | not started |

### Creation paths (ADR-0002)

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `items/vendors`: store stock, refresh, vendor ilvl, gambling | items/quality, items/affixes | Npc, Gamble, StorePage, Misc | not started |
| `items/cube`: recipe matching, input checks, output construction, rerolls | items/properties, items/affixes, data/excel | CubeMain, CubeMod, CubeType | not started |
| `items/sockets-runewords`: socket filling, gems/runes/jewels, runeword activation | items/properties | Runes, Gems | not started |
| `items/quest-drops`: quest-state TC switches, first-kill drops, special drops (Countess, cows, Hellforge) | items/tc | TreasureClassEx (mostly hardcoded) | not started |
| `monsters/stats`: HP/damage/AC/XP realisation per difficulty and player count, mod effects | monsters/pool, monsters/special | MonStats, MonLvl, MonProp, DifficultyLevels, MonUMod | not started |
| `hirelings`: hireling stock, per-difficulty stats, name rolls | rng, data/strings, monsters/stats | Hireling, HireDesc | not started |
| `player/creation`: starting stats and items, experience curve, level-up | items/properties | CharStats, CharTemplate, Experience | not started |

### Prerequisite formats (archivist, `docs/formats/`)

`excel-bin` (exists), `ds1`, `dt1`, `tbl`, `d2s`. DS1/DT1 and `d2s` come first: `drlg/collision`
and every `[C]` promotion that needs a runtime experiment are blocked on them.

### Out of scope (deferred by ADR-0002)

Combat formulas, skills/missiles/states, animation and timing (`animdata.d2`), monster AI,
network protocol, presentation formats (DC6/DCC/COF, palettes, fonts, sound, video). A creation
path that touches these specs them only to the depth it needs and lists the rest under *Open
questions*.
