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
| `rng`: seed state, step, range | — | — | reviewed · plan 0001, 0003 (closed) |
| `items/tc`: treasure class resolution, picks, NoDrop, player-count scaling | rng | TreasureClassEx, ItemRatio, MonStats | **reviewed** · [items/tc](items/tc.md) (2026-10-12, updated 2026-10-14; plans 0004 and 0011 done, classic branch from plan 0020; C 43 / I 76 / L 8: party count and champion column `[C]` by run:2026-10-12-tc-party and run:2026-10-12-tc-champion, classic total, scan and throwable refund by run:2026-10-13-quality) |
| `items/quality`: unique/set/rare/magic/superior/normal/low roll; magic find | rng, items/tc | ItemRatio, ItemTypes | **reviewed** · [items/quality](items/quality.md) (2026-10-14; C 61 / I 36 / L 4; § F aligned with items/0004), [items/0002](../findings/items/0002-quality-roll.md) (run:2026-10-12-quality, run:2026-10-13-quality: 1916 rolls, no oracle) · [plan 0010](../plans/done/0010-items-quality.md) done (closed 2026-10-14) |
| `items/affixes`: alvl, prefix/suffix selection, rare affix counts, automagic | rng, items/quality | MagicPrefix/Suffix, RarePrefix/Suffix, AutoMagic, ItemTypes | **reviewed** · [items/affixes](items/affixes.md) (2026-10-14; C 110 / I 45 / L 5), [items/0005](../findings/items/0005-affixes.md) · plan 0021 closed |
| `items/uniques-sets`: candidate selection, fallback rules | rng, items/quality | UniqueItems, SetItems, Sets | **reviewed** · [items/uniques-sets](items/uniques-sets.md) (2026-10-14; C 69 / I 51 / L 6), [items/0004](../findings/items/0004-uniques-sets.md) · plan 0019 closed |
| `items/properties`: stat rolls, sockets, ethereal, durability, defense | rng | Properties, ItemStatCost, Weapons/Armor/Misc | **reviewed** · [items/properties](items/properties.md) (2026-10-14; C 125 / I 36 / L 6), [items/0006](../findings/items/0006-properties.md) · plan 0024 closed |
| `monsters/pool`: which monster types a level can host | rng | Levels, MonStats, MonLvl | reviewed: [monsters/pool](monsters/pool.md) (C 75 / I 31 / L 5), [monsters overview](monsters/README.md) · plan 0012 closed; `boss` open (needs play) |
| `monsters/spawn`: packs, density, placement, minions | rng, monsters/pool, drlg, drlg/collision | Levels, MonStats, MonPlace | reviewed: [monsters/spawn](monsters/spawn.md) (C 107 / I 61 / L 6; position tests modelled by drlg/collision since 2026-10-14; positions, presets/objects window, unit seeds and special mods are ADR-0004 inputs), [monsters/0002](../findings/monsters/0002-room-population.md), [run:2026-10-13-mon-spawn](../findings/monsters/experiments.md#run2026-10-13-mon-spawn) · plan 0014 closed 2026-10-14; `MonSpawnTry` early exits → reverser backlog (not blocking); position oracles → [plan 0017](../plans/done/0017-drlg-collision.md) |
| `monsters/special`: champions, uniques, superuniques, mod rolls, unique name rolls | rng, data/strings | MonUMod, SuperUniques, UniquePrefix/Suffix/Appellation | **reviewed** · [monsters/special](monsters/special.md) (2026-10-14; C 102 / I 85 / L 7), [monsters/0003](../findings/monsters/0003-special-monsters.md) · plan 0018 closed; classic aura level → `monsters/stats` |
| `drlg/overview`: act → level → room hierarchy, generator dispatch, room-type draws (the k of `rng/seeds` step 6, owed by this row) | rng, rng/seeds | Levels, LvlTypes, LvlPrest; fmt: ds1, dt1 | reviewed · [drlg/README](drlg/README.md) + [drlg/room-tiles](drlg/room-tiles.md) · plan 0008 (closed 2026-10-12) |
| `drlg/preset`: DS1 preset maps, their unit lists and keep/drop rolls, `LvlPrest` columns | drlg/overview | LvlPrest; fmt: ds1 | **reviewed** · [drlg/preset](drlg/preset.md) (2026-10-13; C 86 / I 59 / L 2), [drlg/0004](../findings/drlg/0004-preset-units.md) (run:2026-10-13-drlg-preset: 2210 preset rooms, 123 714 checks, no oracle) · [plan 0016](../plans/done/0016-drlg-preset.md) done (closed 2026-10-13) |
| `drlg/maze`: maze generator (dungeons and caves) | drlg/overview | LvlMaze, LvlPrest | **reviewed** · [drlg/maze](drlg/maze.md) (2026-10-15; C 105 / I 26 / L 3), [drlg/0006](../findings/drlg/0006-maze.md) · plan 0022 closed |
| `drlg/outdoor`: wilderness generator, borders, paths, `LvlSub` substitutions (DS1 (e); moved from `drlg/preset` 2026-10-13, since type-2 rooms never read them) | drlg/overview | LvlPrest, LvlSub | draft spec: [drlg/outdoor](drlg/outdoor.md) (C 126 / I 24 / L 6) · plan 0026 Phase 3 accepted with fixes; `reviewed` waits on the drlg/0008 table contents and sub-steps (backlog) |
| `drlg/warps`: inter-level links and placement | drlg/overview | LvlWarp, Levels | **reviewed** · [drlg/warps](drlg/warps.md) (2026-10-15; C 86 / I 35 / L 6), [drlg/0007](../findings/drlg/0007-warps.md) · plan 0022 closed |
| `objects`: object/shrine/chest placement and operation | rng, drlg, drlg/collision | Objects, ObjGroup, Shrines | planned · [plan 0023](../plans/0023-objects.md) (approved 2026-10-14) |

### Enablers (ADR-0002)

| Subsystem | Depends on | Key tables / formats | Status |
|---|---|---|---|
| `data/excel`: which form is loaded (`.bin`/`.txt`), record layout, code→index lookups, TC vs TCEx | — | all excel; fmt: excel-bin | reviewed · plan 0002 (closed) |
| `data/calc`: formula bytecode VM (`*code.bin`) and the columns that index into it | data/excel | itemscode/misscode/skillscode/skilldesccode.bin | not started |
| `data/strings`: string-table lookup by key/index, as used by name rolls | data/excel | fmt: tbl | findings `[I]` ([data/0003](../findings/data/0003-string-tables.md)), crc check `[C]` (run:2026-10-12-d2s-io) |
| `rng/seeds`: game seed → act → level → room → unit seed derivation | rng | — | reviewed · plan 0003 (closed) |
| `drlg/collision`: room collision grid from tiles, logic regions, placement tests used by spawn/objects | drlg/overview | LvlTypes, LvlPrest; fmt: dt1, ds1 | **reviewed** · [drlg/collision](drlg/collision.md) (2026-10-14; C 99 / I 57 / L 13), [drlg/0005](../findings/drlg/0005-collision.md), run:2026-10-14-collision (1439 grids cell for cell, 0 mismatches; one oracle: the pass-entry snapshot) · [plan 0017](../plans/done/0017-drlg-collision.md) done |
| `save/d2s`: save layout, item bitstream, persisted seeds and quest state (also the experiment harness) | items/properties | ItemStatCost; fmt: d2s | **reviewed** · [save/d2s](save/d2s.md) (2026-10-14; C 83 / I 146 / L 6), [save overview](save/README.md) · plan 0013 closed; reviewed after `items/properties` (plan 0024) |

### Creation paths (ADR-0002)

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `items/vendors`: store stock, refresh, vendor ilvl, gambling | items/quality, items/affixes | Npc, Gamble, StorePage, Misc | not started |
| `items/cube`: recipe matching, input checks, output construction, rerolls | items/properties, items/affixes, data/excel | CubeMain, CubeMod, CubeType | not started |
| `items/sockets-runewords`: socket filling, gems/runes/jewels, runeword activation | items/properties | Runes, Gems | not started |
| `items/quest-drops`: quest-state TC switches, first-kill drops, special drops (Countess, cows, Hellforge) | items/tc | TreasureClassEx (mostly hardcoded) | not started |
| `monsters/stats`: HP/damage/AC/XP realisation per difficulty and player count, mod effects | monsters/pool, monsters/special | MonStats, MonLvl, MonProp, DifficultyLevels, MonUMod | **reviewed** · [monsters/stats](monsters/stats.md) (2026-10-15; C 94 / I 54 / L 5), [monsters/0004](../findings/monsters/0004-stats.md) · plan 0025 closed |
| `hirelings`: hireling stock, per-difficulty stats, name rolls | rng, data/strings, monsters/stats | Hireling, HireDesc | not started |
| `player/creation`: starting stats and items, experience curve, level-up | items/properties | CharStats, CharTemplate, Experience | not started |

### Prerequisite formats (archivist, `docs/formats/`)

`excel-bin`, `ds1`, `dt1`, `d2s`, `tbl` (accepted with fixes, plan 0005, closed 2026-10-12).
`d2s` is the save-inspection harness for item `[C]`s: its tags cover the encoding (23 saves, a load test),
while behaviour seen in the runs (checksum enforcement, the header level rewrite) stays `[L]` until anchored.
Format `[C]` tags describe bytes only: a drlg spec needs its own code anchor for behaviour.

### Out of scope (deferred by ADR-0002)

Combat formulas, skills/missiles/states, animation and timing (`animdata.d2`), monster AI,
network protocol, fonts, sound and video. Presentation formats (palettes, DT1 pixels, DC6/DCC/COF)
are decoded as **tooling only** under ADR-0005 (plan 0006): format docs and `tools/` decoders, output in
`workspace/render/`, and no row or spec here. Which cel and colour shift the game picks for an item is read in
[items/0003](../findings/items/0003-item-graphics.md) (`[I]`, plan 0015) as the reference for `tools/item_art.py`;
it stays a finding, not a row (architect, 2026-10-12). A creation
path that touches these specs them only to the depth it needs and lists the rest under *Open
questions*.
