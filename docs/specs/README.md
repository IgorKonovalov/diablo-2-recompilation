# Specs — research map

This is the deliverable. Each subsystem gets a directory `docs/specs/<subsystem>/` containing a
`README.md` (overview, data flow, entry points) plus one file per algorithm. The `architect` owns
this map; the `spec-writer` owns the files under it.

Status values: `not started` · `findings in progress` · `draft spec` · `reviewed`

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `rng`: seed state, step, range, seed tree | — | — | not started |
| `items/tc`: treasure class resolution, picks, NoDrop, player-count scaling | rng | TreasureClassEx, ItemRatio, MonStats | not started |
| `items/quality`: unique/set/rare/magic/superior/normal/low roll; magic find | rng, items/tc | ItemRatio, ItemTypes | not started |
| `items/affixes`: alvl, prefix/suffix selection, rare affix counts, automagic | rng, items/quality | MagicPrefix/Suffix, RarePrefix/Suffix, AutoMagic, ItemTypes | not started |
| `items/uniques-sets`: candidate selection, fallback rules | rng, items/quality | UniqueItems, SetItems, Sets | not started |
| `items/properties`: stat rolls, sockets, ethereal, durability, defense | rng | Properties, ItemStatCost, Weapons/Armor/Misc | not started |
| `monsters/pool`: which monster types a level can host | rng | Levels, MonStats, MonLvl | not started |
| `monsters/spawn`: packs, density, placement, minions | rng, monsters/pool, drlg | Levels, MonStats, MonPlace | not started |
| `monsters/special`: champions, uniques, superuniques, mod rolls | rng | MonUMod, SuperUniques, Unique* | not started |
| `drlg/overview`: act → level → room hierarchy, generator dispatch | rng | Levels, LvlTypes, LvlPrest | not started |
| `drlg/preset`: DS1 preset maps and their substitutions | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/maze`: maze generator (dungeons and caves) | drlg/overview | LvlMaze, LvlPrest | not started |
| `drlg/outdoor`: wilderness generator, borders, paths | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/warps`: inter-level links and placement | drlg/overview | LvlWarp, Levels | not started |
| `objects`: object/shrine/chest placement | rng, drlg | Objects, ObjGroup | not started |
