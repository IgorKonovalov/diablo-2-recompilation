# D2 data landscape: what to document first

Everything here is `[L]` until verified against the extracted files. Paths are inside the merged
MPQ tree. Tables live in `data/global/excel/`. Whether `.txt`, `.bin` or both ship in 1.14d is
the first thing to check (Plan 0001 phase 3).

## Tables by subsystem (priority order)

**RNG**: none (code only).

**Items / drops**
- `TreasureClassEx`: TC name, group/level, Picks, Unique/Set/Rare/Magic quality modifiers, NoDrop, Item1..10 + Prob1..10
- `ItemRatio`: quality roll constants (Unique, UniqueDivisor, UniqueMin…), per version/class-specific/uber rows
- `ItemTypes`: type hierarchy (Equiv1/Equiv2), Rare/Magic/Normal flags, MaxSock*, StaffMods, BodyLoc
- `Weapons`, `Armor`, `Misc`: base items (code, level=qlvl, magic lvl, type, normcode/ubercode/ultracode, gemsockets, rarity)
- `MagicPrefix`, `MagicSuffix`, `AutoMagic`: affix rows (level, maxlevel, group, frequency, itype/etype, mod1..3)
- `RarePrefix`, `RareSuffix`: rare name parts
- `UniqueItems`, `SetItems`, `Sets`
- `Properties`, `ItemStatCost`: property → stat mapping, stat encoding
- `QualityItems`, `LowQualityItems`, `Gems`, `Runes`, `CubeMain` (later)

**Monsters**
- `MonStats`: per-monster row (Id, BaseId, NextInClass, TreasureClass*, Level per difficulty, minions, spawn flags)
- `MonStats2`: animation and visual side (lower priority)
- `MonLvl`: per-mlvl stat scaling per difficulty
- `MonUMod`, `SuperUniques`, `UniquePrefix`, `UniqueSuffix`, `UniqueAppellation`: special monsters
- `MonProp`, `MonType`, `MonPlace`, `MonPreset`, `MonSeq`

**Levels / DRLG**
- `Levels`: per-area row (Id, Act, DrlgType, LevelType, size per difficulty, MonLvl*, mon1..25/nmon/umon, rangedspawn, NumMon, MonDen*, MonUMin/Max, Waypoint, Vis/Warp links, ObjGrp/ObjPrb)
- `LvlTypes`: tile-file sets per level type (→ DT1 list)
- `LvlPrest`: preset definitions (DS1 files, Populate, Outdoors, Animate, Pops…)
- `LvlMaze`: maze generator parameters (Rooms per difficulty, SizeX/Y, Merge)
- `LvlSub`: substitution groups for outdoor variation
- `LvlWarp`: warp tile definitions
- `Objects`, `ObjGroup`: object placement
- `AutoMap`

**Shared**: `DifficultyLevels`, `Experience`, `CharStats`, `Skills`, `States`, `Missiles`.

## Map and graphics formats (needed for DRLG)

- `.ds1`: preset map (tile layers, walls, floors, shadows, substitutions, objects, NPC paths). Under `data/global/tiles/<act>/…`.
- `.dt1`: tile library (tile headers: orientation, main/sub index, flags; blocks). Layout matters for DRLG; pixel data much less.
- `.dc6`/`.dcc`: sprites (low priority for the mechanics goals).
- `.d2s`: character saves (useful for experiments: inventory inspection, seed state? `[L]`).

## Strings

`data/local/lng/<lang>/*.tbl`: string tables. These are needed to map affix and unique names to
keys. The 1.14d install carries RU and ENG localisation, so check which languages are present.
