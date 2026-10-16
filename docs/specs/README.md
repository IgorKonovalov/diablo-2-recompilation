# Specs — research map

This is the deliverable. Each subsystem gets a directory `docs/specs/<subsystem>/` containing a
`README.md` (overview, data flow, entry points) plus one file per algorithm. The `architect` owns
this map; the `spec-writer` owns the files under it.

Status values: `not started` · `findings in progress` · `draft spec` · `reviewed`

Scope is set by [ADR-0001](../adrs/0001-target-toolchain-evidence-sources.md) and extended by
[ADR-0002](../adrs/0002-scope-creation-paths-and-enablers.md) and [ADR-0014](../adrs/0014-scope-game-simulation.md).
The table has four bands. **Core** is the original goal. **Enablers** are systems the core can't be reproduced
without. **Creation paths** are other callers into the core item and monster code. **Simulation** is the game run
over time, checked per event (ADR-0014). Core rows come first, so "the original three areas are done" stays visible.

[Plan 0038](../plans/0038-inferred-claims-sweep.md) (approved 2026-10-16) sweeps the `[I]` claims of the reviewed specs
toward `[C]`. It changes no row's status. The counts in the rows below change only when its Phase 3 re-tags a spec.

### Core

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `rng`: seed state, step, range | — | — | reviewed · plan 0001, 0003 (closed) |
| `items/tc`: treasure class resolution, picks, NoDrop, player-count scaling | rng | TreasureClassEx, ItemRatio, MonStats | **reviewed** · [items/tc](items/tc.md) (2026-10-12, updated 2026-10-16; plans 0004 and 0011 done, classic branch from plan 0020; C 45 / I 77 / L 8 (2026-10-16 pass: § J chest tier per the ruling, tier as `ilvl` `[I]`, the exact cut open): B6 quest TC `[C]` (single player) by run:2026-10-16-quest-drops; party count and champion column `[C]` by run:2026-10-12-tc-party and run:2026-10-12-tc-champion, classic total, scan and throwable refund by run:2026-10-13-quality) |
| `items/quality`: unique/set/rare/magic/superior/normal/low roll; magic find | rng, items/tc | ItemRatio, ItemTypes | **reviewed** · [items/quality](items/quality.md) (2026-10-14, updated 2026-10-16; C 63 / I 37 / L 4; C1 chest drops roll at `ilvl` 0–2 `[I]`; § F aligned with items/0004, vendors bypass the drop roll; M3 a mercenary's kill counts its owner's MF, run:2026-10-16-hirelings), [items/0002](../findings/items/0002-quality-roll.md) (run:2026-10-12-quality, run:2026-10-13-quality: 1916 rolls, no oracle) · [plan 0010](../plans/done/0010-items-quality.md) done (closed 2026-10-14) |
| `items/affixes`: alvl, prefix/suffix selection, rare affix counts, automagic | rng, items/quality | MagicPrefix/Suffix, RarePrefix/Suffix, AutoMagic, ItemTypes | **reviewed** · [items/affixes](items/affixes.md) (2026-10-14, updated 2026-10-16; C 112 / I 45 / L 4: both line sets end to end in run:2026-10-15-items-chain), [items/0005](../findings/items/0005-affixes.md) · plan 0021 closed; plan 0027 closed 2026-10-16 |
| `items/uniques-sets`: candidate selection, fallback rules | rng, items/quality | UniqueItems, SetItems, Sets | **reviewed** · [items/uniques-sets](items/uniques-sets.md) (2026-10-15; C 70 / I 52 / L 6), [items/0004](../findings/items/0004-uniques-sets.md) · plan 0019 closed |
| `items/properties`: stat rolls, sockets, ethereal, durability, defense | rng | Properties, ItemStatCost, Weapons/Armor/Misc | **reviewed** · [items/properties](items/properties.md) (2026-10-15, updated 2026-10-16; C 129 / I 35 / L 3: items-chain run, superior ethereal `dur%` in run:2026-10-15-items-chain-forced), [items/0006](../findings/items/0006-properties.md) · plan 0024 closed; plan 0027 closed 2026-10-16 |
| `monsters/pool`: which monster types a level can host | rng | Levels, MonStats, MonLvl | reviewed: [monsters/pool](monsters/pool.md) (updated 2026-10-16; C 81 / I 29 / L 3: E4 `boss` test `[C]` by run:2026-10-16-quest-drops; E2 logged for hireling classes 271, 338, 359, 561; 560 has no `Hireling` row), [monsters overview](monsters/README.md) (C 14 / I 1) · plan 0012 closed; plan 0033 closed 2026-10-16; `boss` closed by plan 0032 |
| `monsters/spawn`: packs, density, placement, minions | rng, monsters/pool, drlg, drlg/collision | Levels, MonStats, MonPlace | reviewed: [monsters/spawn](monsters/spawn.md) (updated 2026-10-16; C 110 / I 64 / L 6; position tests modelled by drlg/collision since 2026-10-14; positions, presets/objects window, unit seeds and special mods are ADR-0004 inputs), [monsters/0002](../findings/monsters/0002-room-population.md), [run:2026-10-13-mon-spawn](../findings/monsters/experiments.md#run2026-10-13-mon-spawn) · plan 0014 closed 2026-10-14; `MonSpawnTry` early exits → reverser backlog (not blocking); position oracles → [plan 0017](../plans/done/0017-drlg-collision.md) |
| `monsters/special`: champions, uniques, superuniques, mod rolls, unique name rolls | rng, data/strings | MonUMod, SuperUniques, UniquePrefix/Suffix/Appellation | **reviewed** · [monsters/special](monsters/special.md) (2026-10-14; C 102 / I 85 / L 7), [monsters/0003](../findings/monsters/0003-special-monsters.md) · plan 0018 closed; classic aura level → `monsters/stats` |
| `drlg/overview`: act → level → room hierarchy, generator dispatch, room-type draws (the k of `rng/seeds` step 6, owed by this row) | rng, rng/seeds | Levels, LvlTypes, LvlPrest; fmt: ds1, dt1 | reviewed · [drlg/README](drlg/README.md) + [drlg/room-tiles](drlg/room-tiles.md) · plan 0008 (closed 2026-10-12) |
| `drlg/preset`: DS1 preset maps, their unit lists and keep/drop rolls, `LvlPrest` columns | drlg/overview | LvlPrest; fmt: ds1 | **reviewed** · [drlg/preset](drlg/preset.md) (2026-10-13; revised 2026-10-15 from run:2026-10-15-acts-3-5, C 98 / I 44 / L 2), [drlg/0004](../findings/drlg/0004-preset-units.md) (run:2026-10-13-drlg-preset: 2210 preset rooms, 123 714 checks, no oracle) · [plan 0016](../plans/done/0016-drlg-preset.md) done (closed 2026-10-13) |
| `drlg/maze`: maze generator (dungeons and caves) | drlg/overview | LvlMaze, LvlPrest | **reviewed** · [drlg/maze](drlg/maze.md) (2026-10-15; C 105 / I 26 / L 3), [drlg/0006](../findings/drlg/0006-maze.md) · plan 0022 closed |
| `drlg/outdoor`: wilderness generator, borders, paths, `LvlSub` substitutions (DS1 (e); moved from `drlg/preset` 2026-10-13, since type-2 rooms never read them) | drlg/overview | LvlPrest, LvlSub | **reviewed** · [drlg/outdoor](drlg/outdoor.md) (2026-10-15, updated 2026-10-16; C 170 / I 22 / L 3: level 39 in run:2026-10-15-cow-arcane, 134 a named boundary), [drlg/0008](../findings/drlg/0008-outdoor.md) · plan 0026 closed; plan 0027 closed 2026-10-16 |
| `drlg/warps`: inter-level links and placement | drlg/overview | LvlWarp, Levels | **reviewed** · [drlg/warps](drlg/warps.md) (2026-10-15, updated 2026-10-16; C 91 / I 30 / L 5; level 27 side 1 index 1 `[C]` by run:2026-10-15-acts-3-5), [drlg/0007](../findings/drlg/0007-warps.md) · plan 0022 closed |
| `objects`: object/shrine/chest placement and operation | rng, drlg, drlg/collision | Objects, ObjGroup, Shrines | **reviewed** · [objects](objects/README.md) (2026-10-15, updated 2026-10-16; C 136 / I 69 / L 5; J3 `[C]` scoped to the drop's shape, the tier `[I]`; Hell Hellforge `[C]`; § L quest objects from plan 0032), [objects/0001](../findings/objects/0001-object-population.md) · plan 0023 closed |

### Enablers (ADR-0002)

| Subsystem | Depends on | Key tables / formats | Status |
|---|---|---|---|
| `data/excel`: which form is loaded (`.bin`/`.txt`), record layout, code→index lookups, TC vs TCEx | — | all excel; fmt: excel-bin | reviewed · plan 0002 (closed) |
| `data/calc`: formula bytecode VM (`*code.bin`) and the columns that index into it | data/excel | itemscode/misscode/skillscode/skilldesccode.bin | **reviewed** · [data/calc](data/calc.md) (2026-10-16; C 77 / I 66 / L 3; `min`/`max`/`rand`, `MISS_CalcVar` 0–18/28–42, `EvalMissile` and the `DimReturns` cap `[C]` by run:2026-10-16-calc-emu (ADR-0015)), [data/0005](../findings/data/0005-calc.md), run:2026-10-16-calc (44 529 evaluations, 0 mismatches) · [plan 0035](../plans/done/0035-data-calc.md) done |
| `data/strings`: string-table lookup by key/index, as used by name rolls | data/excel | fmt: tbl | **reviewed** · [data/strings](data/strings.md) (2026-10-15, updated 2026-10-16; C 59 / I 39 / L 3), [data/0003](../findings/data/0003-string-tables.md) · plan 0028 closed |
| `rng/seeds`: game seed → act → level → room → unit seed derivation | rng | — | reviewed · [rng/seeds](rng/seeds.md) (updated 2026-10-16; C 62 / I 16 / L 5; game-creation draws 1–5 `[C]`) · plan 0003 (closed) |
| `drlg/collision`: room collision grid from tiles, logic regions, placement tests used by spawn/objects | drlg/overview | LvlTypes, LvlPrest; fmt: dt1, ds1 | **reviewed** · [drlg/collision](drlg/collision.md) (2026-10-14; C 110 / I 55 / L 12), [drlg/0005](../findings/drlg/0005-collision.md), run:2026-10-14-collision (1439 grids cell for cell, 0 mismatches; one oracle: the pass-entry snapshot) · [plan 0017](../plans/done/0017-drlg-collision.md) done |
| `save/d2s`: save layout, item bitstream, persisted seeds and quest state (also the experiment harness) | items/properties | ItemStatCost; fmt: d2s | **reviewed** · [save/d2s](save/d2s.md) (2026-10-16; C 88 / I 144 / L 5: merc header read side run-checked, write side and dead flag `[I]`), [save overview](save/README.md) · plan 0013 closed; reviewed after `items/properties` (plan 0024); plan 0033 closed 2026-10-16 |
| `drlg/lifecycle`: room activation and release, the inactive records, the restore of monsters, objects and ground items, the wanderer tick | drlg/overview, monsters/spawn, monsters/special, monsters/stats, objects | Levels (`MonWndr`), Objects (`Restore`, `RestoreVirgins`) | not started · [plan 0040](../plans/0040-drlg-room-lifecycle.md) (approved 2026-10-16) |

### Creation paths (ADR-0002)

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `items/vendors`: store stock, refresh, vendor ilvl, gambling | items/quality, items/affixes | Npc, Gamble, StorePage, Misc | **reviewed** · [items/vendors](items/vendors.md) (2026-10-16; C 70 / I 37 / L 4), [items/0009](../findings/items/0009-vendors.md) (C 35 / I 34), run:2026-10-15-vendors (94 stock builds, 325 gamble windows, 9206 items, 0 mismatches; `HIRE_BuildStock` oracle) · [plan 0031](../plans/done/0031-items-vendors.md) done |
| `items/cube`: recipe matching, input checks, output construction, rerolls | items/properties, items/affixes, data/excel | CubeMain (CubeMod, CubeType are not loaded, data/0001) | **reviewed** · [items/cube](items/cube.md) (2026-10-16; C 118 / I 82 / L 6), [items/0008](../findings/items/0008-cube.md), run:2026-10-15-cube (182 transmutes, 0 mismatches) · [plan 0030](../plans/done/0030-items-cube.md) done |
| `items/sockets-runewords`: socket filling, gems/runes/jewels, runeword activation | items/properties | Runes, Gems | **reviewed** · [items/sockets-runewords](items/sockets-runewords.md) (2026-10-15, updated 2026-10-16; C 79 / I 77 / L 9), [items/0007](../findings/items/0007-sockets-runewords.md), run:2026-10-15-sockets (351 inserts, 50 runewords, 0 mismatches) · [plan 0029](../plans/done/0029-items-sockets-runewords.md) done |
| `items/quest-drops`: quest-state TC switches, first-kill drops, special drops (Countess, cows, Hellforge), quest rewards (imbue, sockets) | items/tc | TreasureClassEx (mostly hardcoded) | **reviewed** · [items/quest-drops](items/quest-drops.md) (2026-10-16; C 80 / I 82 / L 6; B6 single player, the quest seed (game-seed draw 4) and its scripted draws, imbue, Larzuk magic, personalize, the Hellforge in all three difficulties, Mephisto done, the Countess (Normal, Nightmare), the Cow King's potions for a qualifying killer, the 356 `≥` boundary `[C]` by run:2026-10-16-quest-drops and its owner-played addendum; the Countess in Hell, the Cow King's refusals, party and pet killers `[I]`), [items/0010](../findings/items/0010-quest-drops.md) · [plan 0032](../plans/done/0032-items-quest-drops.md) closed 2026-10-16; owner addendum done and re-tagged 2026-10-16 |
| `monsters/stats`: HP/damage/AC/XP realisation per difficulty and player count, mod effects | monsters/pool, monsters/special | MonStats, MonLvl, MonProp, DifficultyLevels, MonUMod | **reviewed** · [monsters/stats](monsters/stats.md) (2026-10-15, updated 2026-10-16; C 102 / I 58 / L 5; G7 narrowed, `HireableBossDamagePercent`'s reader `[C]` for 50 and 35 by run:2026-10-16-combat, § H's draws `[C]`: `berserk` in run:2026-10-15-berserk-forced), [monsters/0004](../findings/monsters/0004-stats.md) · plan 0025 closed; plan 0027 closed 2026-10-16 |
| `hirelings`: hireling stock, per-difficulty stats, name rolls | rng, data/strings, monsters/stats | Hireling, HireDesc | **reviewed** · [hirelings](hirelings/README.md) (2026-10-16; C 89 / I 39 / L 8), [hirelings/0001](../findings/hirelings/0001-hirelings.md) (C 42 / I 25), run:2026-10-16-hirelings (53 hire tables, 49 hires, 33 merc headers, 0 mismatches) · [plan 0033](../plans/done/0033-hirelings.md) done (closed 2026-10-16); classic hires, Greiz hire, free merc, written header not run (`[I]`) |
| `player/creation`: starting stats and items, experience curve, level-up | items/properties | CharStats, CharTemplate, Experience | **reviewed** · [player/creation](player/creation.md) (2026-10-16; C 81 / I 39 / L 5), [player/0001](../findings/player/0001-creation.md), run:2026-10-16-player (35 new characters, 269 item copies, 32 kills, 20 level-ups, 0 mismatches) · [plan 0034](../plans/done/0034-player-creation.md) done |

### Prerequisite formats (archivist, `docs/formats/`)

`excel-bin`, `ds1`, `dt1`, `d2s`, `tbl` (accepted with fixes, plan 0005, closed 2026-10-12).
`d2s` is the save-inspection harness for item `[C]`s: its tags cover the encoding (23 saves, a load test),
while behaviour seen in the runs (checksum enforcement, the header level rewrite) stays `[L]` until anchored.
Format `[C]` tags describe bytes only: a drlg spec needs its own code anchor for behaviour.

### Simulation (ADR-0014)

Rows are added when each phase's plan starts: (1) combat formulas, (2) stats and states, (3) skills and missiles,
(4) monster AI, (5) animation timing. Expected later rows: `stats/aggregate`, `skills/dispatch`, `skills/missiles`,
`monsters/ai`, `anim/timing`; each plan may split or rename its row. A simulation `[C]` is a per-event reproduction
with logged inputs at a named boundary; stat values are value oracles until `stats/aggregate` models them. Phase (2) is drafted as
[plan 0041](../plans/0041-stats-and-states.md) (approved 2026-10-16; rows `stats/aggregate` and `stats/states` when it
starts); [ADR-0016](../adrs/0016-pipelined-simulation-phases.md) (accepted 2026-10-16) lets its table and static phases
start before plan 0037's spec is reviewed.

| Subsystem | Depends on | Key tables | Status |
|---|---|---|---|
| `combat/formulas`: to-hit, physical and elemental damage, resistances and caps, block, avoid and evade, damage reduction and absorb, crushing blow, deadly strike, open wounds, leech, difficulty penalties; player against monster and monster against player | monsters/stats, player/creation, items/properties, data/calc | MonStats, MonStats2, MonLvl, DifficultyLevels, CharStats, ItemStatCost, Weapons, Armor, Skills, ElemTypes | **reviewed** · [combat](combat/README.md) (2026-10-16; overview, to-hit, damage, reductions, delivery; C 173 / I 142 / L 22), [combat/0001](../findings/combat/0001-formulas.md), run:2026-10-16-combat (19 sessions, 15 358 events, 0 mismatches) · [plan 0037](../plans/0037-combat-formulas.md) (P0, P1/1b, P2 and P3 accepted 2026-10-16; open for the P2 resume lane and the re-tag of the shortfalls) |

### Game rules (ADR-0017)

[ADR-0017](../adrs/0017-scope-quests-travel-economy.md) (accepted 2026-10-16) brings quest progression, travel and the
item economy into scope beside the simulation phases. Rows are added when each plan starts: `quests/progression`
and `quests/travel` ([plan 0042](../plans/0042-quests-travel.md)), `items/economy` ([plan 0043](../plans/0043-items-economy.md)).
Until then, quest state, prices, repair and gold amounts stay inputs or named-only edges of the specs above.
Multiplayer branches ([plan 0044](../plans/0044-multiplayer-branches.md); ADR-0008 accepted 2026-10-16 on the port-4000
condition) add no row: they re-tag
existing ones.

### Out of scope (ADR-0002, ADR-0005, ADR-0014)

The network protocol, sound, fonts, video, rendering and input handling. Wall-clock timing, frame pacing and the
client's prediction or display of values are out as well: simulation claims are stated in game frames and from the
server's outcomes (ADR-0014). Presentation formats (palettes, DT1 pixels, DC6/DCC/COF) are decoded as **tooling only**
under ADR-0005 (plan 0006): format docs and `tools/` decoders, output in `workspace/render/`, and no row or spec here.
Animation timing enters as frame counts and hit frames (ADR-0014 phase 5); animation playback does not. Which cel and
colour shift the game picks for an item is read in [items/0003](../findings/items/0003-item-graphics.md) (`[I]`, plan
0015) as the reference for `tools/item_art.py`; it stays a finding, not a row (architect, 2026-10-12). Player against
player and hostile states are specified from the code (`[I]`) until a two-client run reaches them (the two-client
harness, [ADR-0008](../adrs/0008-two-client-harness.md), accepted 2026-10-16; plan 0044). A spec that touches a simulation phase not yet planned
specifies it only to the depth it needs and lists the rest under *Open questions*.
