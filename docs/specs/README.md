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
| `items/tc`: treasure class resolution, picks, NoDrop, player-count scaling | rng | TreasureClassEx, ItemRatio, MonStats | draft spec · [items/tc](items/tc.md) (plan 0004 P3 accepted 2026-10-12, 328 calls `[C]`); party ≥ 2 and champion → plan 0011, blocks `reviewed` |
| `items/quality`: unique/set/rare/magic/superior/normal/low roll; magic find | rng, items/tc | ItemRatio, ItemTypes | findings `[I]` ([items/0002](../findings/items/0002-quality-roll.md)) · plan 0010 P1 accepted, P2 next |
| `items/affixes`: alvl, prefix/suffix selection, rare affix counts, automagic | rng, items/quality | MagicPrefix/Suffix, RarePrefix/Suffix, AutoMagic, ItemTypes | not started |
| `items/uniques-sets`: candidate selection, fallback rules | rng, items/quality | UniqueItems, SetItems, Sets | not started |
| `items/properties`: stat rolls, sockets, ethereal, durability, defense | rng | Properties, ItemStatCost, Weapons/Armor/Misc | not started |
| `monsters/pool`: which monster types a level can host | rng | Levels, MonStats, MonLvl | not started · plan 0012 (approved) |
| `monsters/spawn`: packs, density, placement, minions | rng, monsters/pool, drlg, drlg/collision | Levels, MonStats, MonPlace | not started |
| `monsters/special`: champions, uniques, superuniques, mod rolls, unique name rolls | rng, data/strings | MonUMod, SuperUniques, UniquePrefix/Suffix/Appellation | not started |
| `drlg/overview`: act → level → room hierarchy, generator dispatch, room-type draws (the k of `rng/seeds` step 6, owed by this row) | rng, rng/seeds | Levels, LvlTypes, LvlPrest; fmt: ds1, dt1 | findings in progress · plan 0008 (P0–P3 accepted: k per room `[C]` by run:2026-10-11-drlg-roomk, dispatch and preset file index `[C]` by run:2026-10-12-drlg-gen; P4 spec next) |
| `drlg/preset`: DS1 preset maps and their substitutions | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/maze`: maze generator (dungeons and caves) | drlg/overview | LvlMaze, LvlPrest | not started |
| `drlg/outdoor`: wilderness generator, borders, paths | drlg/overview | LvlPrest, LvlSub | not started |
| `drlg/warps`: inter-level links and placement | drlg/overview | LvlWarp, Levels | not started |
| `objects`: object/shrine/chest placement and operation | rng, drlg, drlg/collision | Objects, ObjGroup, Shrines | not started |

### Enablers (ADR-0002)

| Subsystem | Depends on | Key tables / formats | Status |
|---|---|---|---|
| `data/excel`: which form is loaded (`.bin`/`.txt`), record layout, code→index lookups, TC vs TCEx | — | all excel; fmt: excel-bin | reviewed · plan 0002 (closed) |
| `data/calc`: formula bytecode VM (`*code.bin`) and the columns that index into it | data/excel | itemscode/misscode/skillscode/skilldesccode.bin | not started |
| `data/strings`: string-table lookup by key/index, as used by name rolls | data/excel | fmt: tbl | not started |
| `rng/seeds`: game seed → act → level → room → unit seed derivation | rng | — | reviewed · plan 0003 (closed) |
| `drlg/collision`: room collision grid from tiles, placement tests used by spawn/objects | drlg/overview | LvlTypes, LvlPrest; fmt: dt1, ds1 | not started · fmt ds1/dt1 documented (plan 0005 P1–2); sub-tile flag meaning `[L]` until this row anchors it |
| `save/d2s`: save layout, item bitstream, persisted seeds and quest state (also the experiment harness) | items/properties | ItemStatCost; fmt: d2s | not started · prerequisite ready: fmt d2s documented (header, checksum, stat and item bitstreams incl. property lists; plan 0005 P4, accepted with fixes); writer/reader code anchors open (backlog D2S (a)); code anchors → plan 0013 (approved) |

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

`excel-bin`, `ds1`, `dt1`, `d2s`, `tbl` (accepted with fixes, plan 0005, closed 2026-10-12).
`d2s` is the save-inspection harness for item `[C]`s: its tags cover the encoding (23 saves, a load test),
while behaviour seen in the runs (checksum enforcement, the header level rewrite) stays `[L]` until anchored.
Format `[C]` tags describe bytes only: a drlg spec needs its own code anchor for behaviour.

### Out of scope (deferred by ADR-0002)

Combat formulas, skills/missiles/states, animation and timing (`animdata.d2`), monster AI,
network protocol, fonts, sound and video. Presentation formats (palettes, DT1 pixels, DC6/DCC/COF)
are decoded as **tooling only** under ADR-0005 (plan 0006): format docs and `tools/` decoders, output in
`workspace/render/`, and no row or spec here. A creation
path that touches these specs them only to the depth it needs and lists the rest under *Open
questions*.
