---
spec: items/affixes
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, items/quality, items/uniques-sets, data/excel]
consumed_by: [items/properties, items/vendors, items/cube, save/d2s]
tags: {C: 110, I: 45, L: 5}
updated: 2026-10-14
---

# Affixes: alvl, magic and rare picks, automagic, and the other builders

## Purpose

Once item creation has settled an item's quality (or a unique or set build has fallen back), this spec says what
the quality's builder draws on the **item seed** and which rows it chooses. Rows come from `MagicPrefix`,
`MagicSuffix`, `RarePrefix`, `RareSuffix`, `QualityItems` and `LowQualityItems`. After the switch it also gives the
`AutoMagic` row an expansion item gets. The builders are the magic (4), rare (6), superior (3), low (1) and normal (2)
cases of `sub_00557450_ItemCreateByQuality` and the fallback steps of
[items/uniques-sets § E](uniques-sets.md#e-failure-durability-and-the-fallback-chain). Each pick filters the rows
against the item's affix level (alvl), its type, its version and the affixes already on it, then makes one weighted
draw. The spec covers row selection only. The property values a chosen row gives (`mod1code`..`mod3code`) and the
post-switch ethereal and socket rolls belong to the `items/properties` spec (`docs/specs/items/properties.md`). This
spec starts where [items/uniques-sets](uniques-sets.md) ends. Primitives are those of [rng](../rng/README.md).

```mermaid
flowchart LR
  CB["sub_00557450_ItemCreateByQuality<br/>switch, item seed S, 666"] -->|6| R["ITEMS_BuildRare<br/>names, count, slots"]
  CB -->|4| M["ITEMS_BuildMagic<br/>prefix pick, suffix pick"]
  CB -->|3| SU["ITEMS_BuildSuperior<br/>QualityItems row"]
  CB -->|1| LO["ITEMS_BuildLow<br/>LowQualityItems row"]
  CB -->|2| NO["ITEMS_BuildNormal"]
  R --> SM["ITEMS_RollStaffMods"]
  M --> SM
  SU --> SM
  LO --> SM
  NO --> SM
  SM --> J["join"]
  J --> EX["ethereal, sockets<br/>items/properties"]
  EX --> AM["automagic pick<br/>expansion, not 5 or 7"]
  AM --> X["return"]
```

## Entry points

| When | Function | Tag |
|---|---|---|
| The switch of `ItemCreateByQuality` or a fallback step reaches quality 6 | fn:ITEMS_BuildRare@0x005C21A0 → fn:ITEMS_BuildRareAffixes@0x005C1BF0 | [C] |
| … quality 4 | fn:ITEMS_BuildMagic@0x005565E0 | [C] |
| … quality 3 | fn:ITEMS_BuildSuperior@0x005C2AD0 → fn:ITEMS_BuildSuperiorPick@0x005C2970 | [C] |
| … quality 1 | fn:ITEMS_BuildLow@0x005C2FB0 → fn:ITEMS_BuildLowPick@0x005C2D40 | [C] |
| … quality 2 | fn:sub_00556F30_ItemBuildNormalCase@0x00556F30 → fn:ITEMS_BuildNormal@0x00556E80 | [C] |
| After the join, expansion item, quality not 5 or 7 | the automagic step of fn:sub_00557450_ItemCreateByQuality@0x00557450 (0x005579A8–0x00557A0C) → fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940 | [C] |

- [C] Every builder above was entered from a drop in run:2026-10-14-affixes, and the model of this spec reproduced
  all 3 102 logged creations (366 magic, 105 rare, 35 superior, 31 low and 2 472 normal builds, 36 automagic picks)
  with 0 mismatches, over classic Nightmare, expansion Nightmare and expansion Normal. The builder entry seed is
  `{S, 666}`, as [items/uniques-sets § A](uniques-sets.md#a-the-item-seed-at-entry) sets it.
  (fn:sub_00557450_ItemCreateByQuality@0x00557450, run:2026-10-14-affixes,
  [items/0005 § Phase 2 results](../../findings/items/0005-affixes.md#phase-2-results-run2026-10-14-affixes))
- [I] Qualities 8 (crafted) and 9 have builders in the same switch, but the drop quality roll returns only 1..7, so
  no drop reaches them. They belong to `items/cube`. (fn:sub_005C21D0_ItemBuildCrafted@0x005C21D0,
  fn:sub_005C1BC0_PickRareNameByVersion@0x005C1BC0, fn:ITEMS_DropRollQuality@0x00558640,
  [items/0005 § 11](../../findings/items/0005-affixes.md#11-qualities-8-and-9-not-on-the-drop-path))
- [I] Vendors, gambling, the cube and imbue reach the same builders by other paths, some with forced affixes. This
  spec covers the builders as a drop reaches them; those callers belong to `items/vendors` and `items/cube`.
  (fn:ITEMS_PickMagicAffix@0x005C1560, struct:ItemCreateRec+0x68)

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:MagicPrefix.txt:spawnable (`+0x54` u8), tbl:MagicPrefix.txt:version (`+0x22` u16) | the first two filter tests |
| tbl:MagicPrefix.txt:level (`+0x58` i32), tbl:MagicPrefix.txt:maxlevel (`+0x60` i32) | the level window against alvl; also a weight factor on `magic lvl` bases |
| tbl:MagicPrefix.txt:rare (`+0x64` u8) | excludes the row on qualities 6, 8, 9 when 0 |
| tbl:MagicPrefix.txt:itype1..7 (`+0x6A` i16 each), tbl:MagicPrefix.txt:etype1..5 (`+0x78` i16 each), tbl:MagicPrefix.txt:mod1code (`+0x24` i32) | the type test |
| tbl:MagicPrefix.txt:frequency (`+0x82` u8) | the weight; 0 is never a candidate |
| tbl:MagicPrefix.txt:classspecific (`+0x66` u8, 0xFF blank) | the class test |
| tbl:MagicPrefix.txt:group (`+0x5C` i32) | group exclusion; for `automagic`, the base's group |
| the same columns of tbl:MagicSuffix.txt:level and tbl:AutoMagic.txt:group | the suffix and automagic blocks (one shared 0x90-byte record) |
| tbl:RarePrefix.txt:version (`+0x0E` u16), tbl:RarePrefix.txt:itype1 (`+0x10`, 7 × i16), tbl:RarePrefix.txt:etype1 (`+0x1E`, 4 × i16), and RareSuffix alike | the rare name test (0x48-byte record) |
| tbl:QualityItems.txt:armor … tbl:QualityItems.txt:belt (bytes `+0x000..+0x009`) | the superior type test |
| tbl:LowQualityItems.txt:Name (row count only) | the low-quality row range |
| tbl:Weapons.txt:level (`+0x0FD` u8, qlvl), tbl:Weapons.txt:magic lvl (`+0x140` u8), tbl:Weapons.txt:auto prefix (`+0x0F8` u16) | alvl, weights, automagic group (same offsets in [Armor](../../tables/Armor.md), [Misc](../../tables/Misc.md)) |
| tbl:Weapons.txt:stackable (`+0x132`), tbl:Weapons.txt:hasinv (`+0x137`), tbl:Weapons.txt:nodurability (`+0x113`), tbl:Weapons.txt:durability (`+0x112`) | type test, superior row range, low-quality durability |
| tbl:ItemTypes.txt:Throwable, tbl:ItemTypes.txt:Class (`+0x21`, 7 = none), tbl:ItemTypes.txt:StaffMods (`+0x1F`, 7 = none), tbl:ItemTypes.txt:Rare, tbl:ItemTypes.txt:MaxSock1, `Equiv1`/`Equiv2` | type tests, class test, staff mods, the rare gate |
| tbl:Skills.txt:charclass, tbl:Skills.txt:itypea1 (`+0x18`) | staff mods: the class's skill run and each skill's item-type requirement |

- [I] Not read by any pick: `levelreq`, `class`, `classlevelreq`, `transformcolor` and the price columns of the
  magic tables; the rare record's `+0x000..+0x00B`. (fn:ITEMS_PickMagicAffix@0x005C1560,
  fn:ITEMS_PickRareName@0x005C1AB0, tbl:MagicPrefix.txt:levelreq,
  [items/0005 § Data touched](../../findings/items/0005-affixes.md#data-touched))
- [I] Every list in a type column ends at its first value < 1, so the `0xFFFF` (−1) that the `.bin` holds in absent
  `etype4`/`etype5` columns ends the list like a blank. (fn:ITEMS_MagicAffixTypeOk@0x0065E620,
  tbl:MagicSuffix.txt:etype4, [AutoMagic § Code semantics](../../tables/AutoMagic.md#code-semantics-items0005))

### Runtime state

| State | Type | Source |
|---|---|---|
| `item.seed` | `Seed` at struct:ItemData+0x04; `{S, 666}` at each builder entry | [items/uniques-sets § A, § E](uniques-sets.md#a-the-item-seed-at-entry) |
| `item.quality` | u32 at struct:ItemData+0x00 | the switch or the fallback step |
| `ilvl` | i32, from fn:ITEMS_GetItemLevel@0x006281E0 (raised to at least 1) | the resolver's item level |
| `itemVersion` | u16 at struct:ItemData+0x30 | ≥ 100 expansion game, 1..99 classic game, never 0 on a drop |
| `prefix[0..2]`, `suffix[0..2]` | u16 merged ids at struct:ItemData+0x38, `+0x3E`; 0 none | cleared before the switch; written by the picks |
| `rareName1`, `rareName2` | u16 merged rare ids at struct:ItemData+0x32, `+0x34` | the rare name picks |
| `autoAffix` | u16 merged id at `ItemData+0x36` | the automagic step |
| `item.fileIndex` | i32 at struct:ItemData+0x28 | the superior or low-quality row |
| `rec` | the creation record, `struct:ItemCreateRec` | `+0x68` forced prefixes, `+0x74` forced suffixes (0 on a drop), `+0x0C` ilvl, `+0x80` flags |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| `VERSION_EXP` | 100: a row with `version` ≥ 100 needs an item of version ≥ 100 | 0x005C16D3–0x005C16F0, fn:ITEMS_RareNameTypeOk@0x0065E710 | [C] |
| `ALVL_MAX` | 99, in the alvl formula and the clamp | 0x005C1671–0x005C16C2 | [C] |
| `RARE_COUNT` | `{3, 4, 4, 5, 5, 5, 6, 6}` (`int[8]`) | data:g_RareAffixCountTable@0x006E3014 | [C] |
| `RARE_SIDE_MAX` | 3 prefixes, 3 suffixes | 0x005C1CB1–0x005C1E16 | [C] |
| `TYPE_JEWEL` | 58 (`jewl`) | 0x005C1C6F–0x005C1C77 | [I] |
| `CLASS_NONE` | 7, the "no class" value of `Class` and `StaffMods` | fn:sub_0062C0B0_ItemTypeClass@0x0062C0B0, fn:sub_0062BBD0_ItemTypeStaffMods@0x0062BBD0 | [C] |
| `CAND_CAP` | 511 stored candidates per pick | fn:sub_005C0D00_AffixCandAdd@0x005C0D00 | [I] |
| `STAT_SOCKETS` | 194 (`item_numsockets`) | fn:ITEMS_MagicAffixTypeOk@0x0065E620 | [I] |

- [C] The model uses each `[C]` constant above and reproduces every logged pick, count and slot with it.
  (run:2026-10-14-affixes)

### Inputs and oracles

The Phase 2 model of plan 0021 (`tools/affixes.py check`, chained after `tools/uniques.py`) covers every selection
from the builder's entry to its return, and the automagic pick. It treats the callees below as ADR-0004 boundaries:
it asserts the item seed on entry to each, then takes the logged exit seed and result. Every confirmed statement
of this spec holds under them. [C] (run:2026-10-14-affixes,
[items/0005 § Boundary](../../findings/items/0005-affixes.md#boundary-for-phase-2-recommendation-the-architect-rules))

| Input | Kind | What this spec needs | Owner | Tag |
|---|---|---|---|---|
| `sub_0065FEC0_ItemApplyProps` | seed oracle | entry seed: after each magic pick's draw, after all rare picks, after the superior row, after the automagic pick; it draws a row's property values on the item seed | `items/properties` | [C] (fn:sub_0065FEC0_ItemApplyProps@0x0065FEC0, run:2026-10-14-affixes) |
| `ITEMS_RollStaffMods` | seed oracle | entry seed: the builder's last draw; § I gives its draws as read | this spec (§ I), modelled later | [C] (fn:ITEMS_RollStaffMods@0x005C1260, run:2026-10-14-affixes) |
| the ethereal roll `sub_00556CA0_ItemRollEthereal` and the socket roll `sub_00556B60_ItemRollSockets` | logged boundary | entry seed: the join seed; exit seed: the automagic pick's entry seed | `items/properties` | [C] (fn:sub_00556CA0_ItemRollEthereal@0x00556CA0, fn:sub_00556B60_ItemRollSockets@0x00556B60, run:2026-10-14-affixes) |
| the builder entry seed `{S, 666}` and the quality | value input | the switch or the fallback step | [items/uniques-sets](uniques-sets.md#e-failure-durability-and-the-fallback-chain) | [C] (fn:sub_00557450_ItemCreateByQuality@0x00557450, run:2026-10-14-affixes) |

## Algorithm

All arithmetic is signed 32-bit unless a step says otherwise. "Low" is `item.seed.low` after the step just made.
Section A fixes the id spaces, B the affix level, C one magic-affix pick, D to H the builders, I the staff mods,
J the automagic step after the switch, K classic games.
[I] (fn:sub_00557450_ItemCreateByQuality@0x00557450, [items/0005 § Walkthrough](../../findings/items/0005-affixes.md#walkthrough))

### A. Merged affix ids

```mermaid
flowchart LR
  subgraph magic["g_MagicAffixInfo, 0x90-byte records"]
    S["magicsuffix rows 0..746<br/>ids 1..747"] --> P["magicprefix rows 0..668<br/>ids 748..1416"] --> AU["automagic rows 0..35<br/>ids 1417..1452"]
  end
  subgraph rare["g_RareAffixInfo, 0x48-byte records"]
    RS["raresuffix rows 0..154<br/>ids 1..155"] --> RP["rareprefix rows 0..45<br/>ids 156..201"]
  end
```

```
A1. magic ← magicsuffix ++ magicprefix ++ automagic             [C] (fn:sub_00633730_LoadMagicAffixes@0x00633730, data:g_MagicAffixInfo@0x0096CA7C, run:2026-10-14-affixes)
    id(block, row) = blockStart + row + 1                       ; 0 means "none"
A2. rare ← raresuffix ++ rareprefix                             [C] (fn:sub_00633F40_LoadRareAffixes@0x00633F40, data:g_RareAffixInfo@0x0096CAA0, run:2026-10-14-affixes)
    id(block, row) = blockStart + row + 1
A3. record(id) = base + (id − 1) × stride, for 1 ≤ id ≤ count  [C] (fn:MAGICAFFIX_GetRecord@0x00633EE0, run:2026-10-14-affixes)
```

Step notes:

- A1–A2. With stock data (747 suffix, 669 prefix, 36 automagic rows; 155 rare suffix, 46 rare prefix rows) suffix
  row r is id r + 1, prefix row r id 748 + r, automagic row r id 1417 + r; rare suffix row r id r + 1, rare prefix row
  r id 156 + r. Every logged candidate, chosen id and rare name matched this numbering. [C]
  (fn:sub_00633730_LoadMagicAffixes@0x00633730, fn:sub_00633F40_LoadRareAffixes@0x00633F40, run:2026-10-14-affixes)
- A1. The item data holds these merged ids unchanged (`ITEMS_SetPrefix` → `+0x38 + 2i`, `ITEMS_SetSuffix` →
  `+0x3E + 2i`, `ITEMS_SetRareName1` → `+0x32`, `ITEMS_SetRareName2` → `+0x34`, `ITEMS_SetAutoAffix` → `+0x36`). A
  save stores block-relative ids instead (`save/d2s`). [C] (fn:ITEMS_SetPrefix@0x00627EF0,
  fn:ITEMS_SetSuffix@0x00627FB0, fn:ITEMS_SetAutoAffix@0x00627F50, struct:ItemData+0x32, run:2026-10-14-affixes)
- A1. `magicsuffix` row 0 is a real row with id 1; `magicprefix` row 0 is blank and never a candidate (`frequency` 0,
  no `itype`). [I] (tbl:MagicPrefix.txt:frequency, [items/0005 § 1](../../findings/items/0005-affixes.md#1-the-merged-affix-arrays-and-the-ids-0x00633730-0x00633f40))

### B. The affix level (alvl)

```
B1. qlvl: i32 ← base.level                                     ; u8, ITEMS_GetQLvl          [C] (fn:ITEMS_PickMagicAffix@0x005C1560, 0x005C1664–0x005C16C2, run:2026-10-14-affixes, all of B1–B4)
    i: i32 ← ITEMS_GetItemLevel(item)                          ; ilvl, at least 1
    if i ≤ qlvl: i ← qlvl                                      ; i = max(ilvl, qlvl), signed
B2. m: i32 ← base.magicLvl                                     ; u8 `magic lvl`
    if m ≠ 0:
      alvl ← i + m
B3. else:
      h: i32 ← qlvl ÷ 2                                        ; qlvl ≥ 0, so floor
      if i < 99 − h: alvl ← i − h
      else:          alvl ← 2 × i − 99
B4. if alvl ≤ 1: alvl ← 1
    else if alvl ≥ 99: alvl ← 99
```

Step notes:

- B1–B4. Every comparison is signed 32-bit. `magic lvl` replaces the `qlvl/2` rule entirely: such a base gets
  `max(ilvl, qlvl) + m` with no subtraction. [C] (0x005C1671–0x005C16C2, fn:ITEMS_GetQLvl@0x00628740,
  tbl:Weapons.txt:level, tbl:Weapons.txt:magic lvl, run:2026-10-14-affixes)
- B1. alvl is recomputed in every pick, never stored. For one item all picks see the same value: prefixes,
  suffixes, the rare slots and the automagic pick. [C] (0x005C1664, run:2026-10-14-affixes)
- B1. The same formula holds in a classic game: the picks branch on item version 0, which no drop creates, not on
  100 (§ K). [C] (fn:sub_005C18E0_PickMagicAffixByVersion@0x005C18E0, run:2026-10-14-affixes)
- B2. Stock bases with `magic lvl`: the staves, wands and orbs with 1, the circlets `ci0`..`ci3` with 3, 8, 13, 18.
  [I] (tbl:Armor.txt:magic lvl, [items/0005 § 2](../../findings/items/0005-affixes.md#2-alvl-0x005c16340x005c16c2))

### C. One magic-affix pick — `ITEMS_PickMagicAffix`

`PickMagicAffix(item, needSpawnable, mustRoll, applyProps, isPrefix, forcedId, autoGroup) → id` is called through
`sub_005C18E0_PickMagicAffixByVersion` (autoGroup 0) or `sub_005C1940_PickAutoAffixByVersion`. [C]
(fn:ITEMS_PickMagicAffix@0x005C1560, fn:sub_005C18E0_PickMagicAffixByVersion@0x005C18E0,
fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940, run:2026-10-14-affixes)

```mermaid
flowchart TD
  E["entry: block = automagic, prefix or suffix"] --> D1["draw 1: Step item.seed"]
  D1 --> R{"low bit 0 = 1<br/>or mustRoll"}
  R -->|no| Z(("return 0"))
  R -->|yes| F["alvl, then filter every row of the block<br/>in table order"]
  F --> C{"any candidate"}
  C -->|no| Z
  C -->|yes| D2["draw 2: x = Range W + 1"]
  D2 --> W["walk: subtract weights,<br/>first to go below 0 wins,<br/>x = W takes the last"]
  W --> AP{"applyProps"}
  AP -->|yes| PR["ItemApplyProps<br/>items/properties"]
  AP -->|no| RET(("return id"))
  PR --> RET
```

```
C1. block ← automagic if autoGroup ≠ 0                                    [C] (0x005C1560–0x005C15FD, run:2026-10-14-affixes)
            else magicprefix if isPrefix else magicsuffix
C2. Step(item.seed)                                                       [C] draw#1, always (0x005C15FD–0x005C1645, run:2026-10-14-affixes)
    if (low & 1) = 0 and not mustRoll: return 0                           ; no affix
C3. alvl ← § B; m ← base.magicLvl                                         [C] (0x005C1664, run:2026-10-14-affixes)
C4. n: i32 ← 0; W: i32 ← 0                                                [C] (0x005C16D3–0x005C17AD, run:2026-10-14-affixes, all of C4a–C4i)
    for row in 0 ..< len(block):  r ← block[row]
C4a.  if needSpawnable and r.spawnable = 0: continue                      ; u8
C4b.  if r.version ≥ 100 and itemVersion < 100: continue                  ; u16 against u16
C4c.  forced ← forcedId > 0 and row = forcedId − 1
      if not forced:
        if r.level > alvl: continue                                       ; i32
        if r.maxlevel ≠ 0 and r.maxlevel < alvl: continue
C4d.  if r.rare = 0 and item.quality ∈ {6, 8, 9}: continue                ; u8
C4e.  if not MagicAffixTypeOk(item, r): continue                          ; C5
C4f.  if autoGroup ≠ 0 and r.group ≠ autoGroup: continue
C4g.  if r.frequency = 0: continue                                        ; u8
C4h.  if r.classspecific ≠ 0xFF and typeClass(item) ≠ 7                   ; u8; 7 = no class
         and r.classspecific ≠ typeClass(item): continue
C4i.  if GroupTaken(item, r.group): continue                              ; C6
      if forced: id ← blockStart + row; go to C8                          ; [I] no weighted draw (0x005C180B–0x005C181B)
      w: i32 ← r.frequency × r.level if m ≠ 0 else r.frequency
      if n < 511: cand[n] ← (blockStart + row, r); n ← n + 1             ; [I] weight added even past the cap (0x005C0D00)
      W ← W + w
C7. if n ≤ 0: return 0                                                    [C] (0x005C1821, run:2026-10-14-affixes)
    x: i32 ← Range(item.seed, W + 1)                                      [C] draw#2 (fn:RNG_RangeOffset@0x00472280, 0x005C1828–0x005C1839, run:2026-10-14-affixes)
    for k in 0 ..< n:                                                     [C] (0x005C185A–0x005C189E, run:2026-10-14-affixes)
      x ← x − weight(cand[k])                                             ; same rule as w
      if x < 0: break
    if k = n: k ← n − 1                                                   ; x = W: the last candidate
    id ← cand[k].id
C8. if applyProps: ItemApplyProps(item, record(id + 1))                   [C] ORACLE, items/properties (fn:sub_0065FEC0_ItemApplyProps@0x0065FEC0, run:2026-10-14-affixes)
    return id + 1
```

**C5. The type test `MagicAffixTypeOk(item, r)`**, in order:

```
C5a. if itemVersion < 100 and (base.stackable or ItemTypes[type].Throwable): return false      [I] (fn:ITEMS_MagicAffixTypeOk@0x0065E620, 0x0065E62D, all of C5a–C5b)
C5b. if not base.hasinv or ItemMaxSockets(item) = 0:
       if r.mod1code ≥ 0 and (mod1code out of range, or no Properties record,
                              or the property's first stat = 194): return false
C5c. for t in r.etype1..5 while t ≥ 1: if ITEMS_UnitIsType(item, t): return false                [C] (fn:ITEMS_MagicAffixTypeOk@0x0065E620, fn:ITEMS_UnitIsType@0x00629BB0, run:2026-10-14-affixes, all of C5c–C5d)
C5d. for t in r.itype1..7 while t ≥ 1: if ITEMS_UnitIsType(item, t): return true
     return false                                                                               ; an empty itype list refuses
```

**C6. `GroupTaken(item, g)`**: walk `prefix[0..2]` up to the first empty slot, then `suffix[0..2]` likewise; true if
any record there has `group` = g. [C] (fn:sub_005C1500_AffixGroupTaken@0x005C1500, run:2026-10-14-affixes)

Step notes:

- C2. **Draw 1 happens on every pick**, also when `mustRoll` is set (its bit is then ignored), and before the scan, so
  a pick that finds no candidate still costs one step. A pick costs exactly 1 step (no roll, or no candidate) or 2,
  plus whatever the property oracle draws. [C] (0x005C15FD, 0x005C1839, 0x005C18A3, run:2026-10-14-affixes)
- C4. The tests run in the order written, each a `continue`. `spawnable`, `rare`, `frequency` and `classspecific`
  are read as bytes, `version` as u16, `level`, `maxlevel` and `group` as signed 32-bit. [C]
  (0x005C16D3–0x005C17AD, run:2026-10-14-affixes)
- C4c. `maxlevel` 0 means no upper bound. The level window compares with alvl, not ilvl. In 962 of 999 logged picks the
  candidate set differs from the rows with `level` ≤ ilvl + 2, and each reproduces with alvl. [C]
  (0x005C16FE–0x005C1713, run:2026-10-14-affixes)
- C4d. A rare item never gets a row whose `rare` is 0. The automagic pick runs this test too, so a rare item cannot
  get one of the 7 `automagic` rows whose `rare` is 0. [C] (0x005C173F, tbl:AutoMagic.txt:rare,
  run:2026-10-14-affixes)
- C4h. **A class-specific row is not refused on a classless type.** The test refuses only an item whose type has a
  class other than the row's. The row's `itype` list keeps it off other items. 22 of the 26 logged class-specific
  picks sat on a classless type (for example the prefix *Raging* on a `hal`). [C] (0x005C1781–0x005C179E,
  fn:sub_0062C0B0_ItemTypeClass@0x0062C0B0, tbl:MagicPrefix.txt:classspecific, tbl:ItemTypes.txt:Class,
  run:2026-10-14-affixes)
- C4i. **Group exclusion spans both tables** and sees every affix already set on the item, so a picked row also
  excludes itself. Stock prefix groups (101–142), suffix groups (1–45) and automagic groups (300–305) do not overlap,
  so the cross-table comparisons never bite with stock data. [C] (fn:sub_005C1500_AffixGroupTaken@0x005C1500,
  tbl:MagicPrefix.txt:group, tbl:AutoMagic.txt:group, run:2026-10-14-affixes)
- C4i. **The forced row** (`forcedId` > 0, block-relative) skips only the level window. It still passes every other
  test, and when it does the pick returns it with no draw 2. If it fails a test the pick continues as an ordinary one.
  On the drop path `forcedId` is always 0, because `sub_0055A550_DropCreateItem` zeroes the record and nothing on the
  path writes `+0x68..+0x7C`. [I] (0x005C16FE–0x005C1713, 0x005C180B–0x005C181B, struct:ItemCreateRec+0x68)
- C4i. Every logged pick on the drop path had `forcedId` 0. [C] (fn:ITEMS_PickMagicAffix@0x005C1560,
  run:2026-10-14-affixes)
- C4. **Weights.** `frequency` alone, or `frequency × level` when the base has `magic lvl`, the same rule in the sum
  and in the walk. 989 logged picks drew over unequal weights, 51 of them with `frequency × level`. [C]
  (0x005C17CE–0x005C17EA, 0x005C185A–0x005C187C, tbl:MagicPrefix.txt:frequency, run:2026-10-14-affixes)
- C4. **Candidate cap.** Only the first 511 candidates are stored, while every weight is summed. With stock data no
  base has more than 165 type-eligible rows in one block, so the cap is unreachable. [I]
  (fn:sub_005C0D00_AffixCandAdd@0x005C0D00)
- C5a. A classic item refuses stackable bases and `Throwable` types. With stock data only classic throwing weapons
  then have no affix and no rare name at all; none dropped as magic or rare in the run. [I] (0x0065E62D,
  fn:sub_006289F0_ItemBaseStackable@0x006289F0, fn:sub_0062BA80_ItemTypeThrowable@0x0062BA80, tbl:Weapons.txt:stackable)
- C5b. **The socket test.** On a base that cannot hold sockets (`hasinv` = 0, or the type's max sockets = 0), a row
  whose first property is the `sock` property (first stat 194, `item_numsockets`) is refused. No row was refused this
  way in the run. [I] (0x0065E64E, fn:sub_00629900_ItemBaseHasInv@0x00629900,
  fn:sub_0062BC20_ItemMaxSockets@0x0062BC20, tbl:MagicPrefix.txt:mod1code, tbl:Weapons.txt:hasinv)
- C5c–C5d. `ITEMS_UnitIsType` tests the `Equiv1`/`Equiv2` closure of the base's `type` and `type2`. Any `etype`
  match refuses before the `itype` list is read. The 27 `magicsuffix` rows with no `itype` can never be picked. [C]
  (fn:ITEMS_UnitIsType@0x00629BB0, tbl:MagicPrefix.txt:itype1, tbl:MagicPrefix.txt:etype1, run:2026-10-14-affixes)
- C7. **The last candidate wins a draw of exactly W.** `Range(W + 1)` returns 0..W. When x = W no subtraction goes
  below 0, and the walk leaves with the last candidate, so the last candidate's effective weight is its weight + 1.
  12 logged picks drew x = W. [C] (0x005C188B, run:2026-10-14-affixes)

### D. The magic builder — `ITEMS_BuildMagic`

```
D1. p ← 0; s ← 0; sufMust ← false                                       [C] (fn:ITEMS_BuildMagic@0x005565E0, 0x005565E0–0x005566A7, run:2026-10-14-affixes, all of D1–D4)
    if rec.forcedPrefix[0] < 0: sufMust ← true                          ; never on a drop
    else:
      p ← PickMagicAffix(item, needSpawnable 1, mustRoll (rec.forcedPrefix[0] > 0),
                         applyProps 1, prefix, rec.forcedPrefix[0], 0)
      prefix[0] ← p
      if p = 0: sufMust ← true
      else if rec.forcedSuffix[0] < 0: go to D3                         ; never on a drop
D2. if rec.forcedSuffix[0] > 0: sufMust ← true
    s ← PickMagicAffix(item, 1, sufMust, 1, suffix, rec.forcedSuffix[0], 0)
    suffix[0] ← s
D3. if p = 0 and s = 0: return false                                    ; → superior fallback
D4. set item flag 0x10; RollStaffMods(item, rec)                        ; ORACLE, § I
    return true
```

Step notes:

- D1–D2. On a drop both forced values are 0: the prefix pick's draw 1 decides (bit 0) whether a prefix is tried, and
  the suffix pick must roll when no prefix was set (no roll, or no candidate). So a magic item has a prefix only, a
  suffix only, or both. When both blocks have candidates the shares are 1/4 both, 1/4 prefix only, 1/2 suffix
  only; an empty prefix block shifts every item to suffix only. [C] (0x005565E0–0x005566A7,
  run:2026-10-14-affixes)
- D1–D2. **The prefix's properties come before the suffix pick**, because each pick applies its row's properties
  itself (`applyProps` 1). Order on the item seed: prefix draw 1, prefix draw 2, prefix properties, suffix draw 1,
  suffix draw 2, suffix properties, staff mods. [C] (fn:ITEMS_BuildMagic@0x005565E0, run:2026-10-14-affixes)
- D3. The builder fails only when both slots are 0, which on a drop needs an empty suffix block for the item (the
  suffix pick must roll). No failed magic build was logged. [I] (0x00556673–0x00556684, 0x0055667D)

### E. The rare builder — `ITEMS_BuildRare` → `ITEMS_BuildRareAffixes`

```mermaid
flowchart TD
  G{"ItemTypes Rare"} -->|0| F(("fail"))
  G -->|1| N1["rare name 1: rareprefix, uniform"]
  N1 --> N2["rare name 2: raresuffix, uniform"]
  N2 --> NC{"both found"}
  NC -->|no| F
  NC -->|yes| CT["count: jewel 3 + low mod 2,<br/>else RARE_COUNT low and 7"]
  CT --> L{"slot i < count<br/>and a side open"}
  L -->|yes| SD{"both sides open"}
  SD -->|yes| B["Step: bit 0 = 1 suffix, else prefix"]
  SD -->|no| O["the open side"]
  B --> PK["PickMagicAffix mustRoll 1, applyProps 0"]
  O --> PK
  PK -->|"id"| ST["set slot; side full at 3 closes it"]
  PK -->|"0"| CL["close the side, retry the slot"]
  ST --> L
  CL --> L
  L -->|no| PR["properties: p0 s0 p1 s1 p2 s2"]
  PR --> SM["RollStaffMods"]
```

```
E1. if not ItemTypes[type].Rare: return false                                     [I] (fn:ITEMS_BuildRare@0x005C21A0, fn:sub_0062E990_ItemTypeRare@0x0062E990)
E2. n1 ← PickRareName(prefix, item); n2 ← PickRareName(suffix, item)                [C] (fn:ITEMS_BuildRareAffixes@0x005C1BF0, 0x005C1BF0–0x005C1C59, run:2026-10-14-affixes)
    if n1 = 0 or n2 = 0: return false                                             ; → magic fallback
    rareName1 ← n1; rareName2 ← n2
E3. if base type = 58:                                                            [I] (0x005C1C6F–0x005C1C77, fn:ITEMS_GetBaseType@0x0062B400)
      count: i32 ← 3 + Range(item.seed, 2)                                        ; draw (RNG_RangeOffset)
    else:                                                                         [C] (0x005C1C77–0x005C1CAE, data:g_RareAffixCountTable@0x006E3014, run:2026-10-14-affixes)
      Step(item.seed); count ← RARE_COUNT[low & 7]                                ; draw
E4. np ← 0; ns ← 0; preDone ← false; sufDone ← false; i ← 0                        [C] (0x005C1CB1–0x005C1E16, run:2026-10-14-affixes, all of E4–E5)
    while i < count:
      if preDone and sufDone: break
      if preDone: side ← suffix
      else if sufDone: side ← prefix
      else: Step(item.seed); side ← suffix if (low & 1) = 1 else prefix          ; draw, only while both sides are open
      a ← PickMagicAffix(item, needSpawnable 1, mustRoll 1, applyProps 0, side,
                         rec.forced<side>[n<side>], 0)                            ; § C: 2 draws when it finds a row
      if a = 0: close side; continue                                              ; the slot is retried, i unchanged
      store a in the side's next slot; n<side> ← n<side> + 1
      if n<side> > 2: close side
      i ← i + 1
E5. if np = 0 and ns = 0: return false                                            ; [I] (0x005C1E71)
E6. set item flag 0x10                                                            [C] (0x005C1E16–0x005C1E70, run:2026-10-14-affixes)
    for k in 0 ..< 3:
      if prefix[k] ≠ 0: ItemApplyProps(item, record(prefix[k]))                   ; ORACLE, items/properties
      if suffix[k] ≠ 0: ItemApplyProps(item, record(suffix[k]))
E7. RollStaffMods(item, rec); return true                                         ; ORACLE, § I
```

**E2. `PickRareName(isPrefix, item)`**:

```
R1. if itemVersion < 100 and (base.stackable or ItemTypes[type].Throwable): no row passes    [I] (0x0065E71D–0x0065E737)
R2. cand ← every row r of the block, in table order, with                                  [C] (fn:ITEMS_PickRareName@0x005C1AB0, fn:ITEMS_RareNameTypeOk@0x0065E710, run:2026-10-14-affixes)
      not (r.version ≥ 100 and itemVersion < 100),
      no etype1..4 (while ≥ 1) that the item is,
      one itype1..7 (while ≥ 1) that the item is
R3. if cand is empty: return 0                                                             [I] no draw (0x005C1B7E)
R4. k ← Range(item.seed, len(cand)); return cand[k].id                                     [C] draw (fn:RNG_RangeOffset@0x00472280, run:2026-10-14-affixes)
```

Step notes:

- E2. **The names come first**: `name1` from `rareprefix`, then `name2` from `raresuffix`, both before the count and
  every affix. They depend on the item's type and version only, never on its affixes. All 105 logged rares drew both
  names before the count. [C] (0x005C1C06, 0x005C1C26, fn:ITEMS_PickRareName@0x005C1AB0, run:2026-10-14-affixes)
- R2–R4. A name pick has no level and no weight: one uniform draw over the type-eligible rows (cap 511). `rareprefix`
  `Warp` and `Rift` name no `itype`, so they are never picked. [C] (fn:ITEMS_PickRareName@0x005C1AB0,
  tbl:RarePrefix.txt:itype1, tbl:RareSuffix.txt:etype1, run:2026-10-14-affixes)
- R2. The rare `version` cell is 0 in every stock row, so its test always passes. [I] (fn:ITEMS_RareNameTypeOk@0x0065E710,
  tbl:RarePrefix.txt:version)
- R3. Only classic throwing weapons have no name candidate with stock data; none was logged as rare. [I] (0x005C1B7E)
- E3. The count is 3 with probability 1/8, 4 with 2/8, 5 with 3/8, 6 with 2/8. Counts 3, 4, 5 and 6 were drawn 14,
  16, 41 and 34 times over the 105 logged rares. [C] (data:g_RareAffixCountTable@0x006E3014, run:2026-10-14-affixes)
- E3. Jewels get 3 or 4. No rare jewel was logged. [I] (0x005C1C77)
- E4. **A side runs out, the slot is retried.** A pick that returns 0 closes its side without consuming the slot; a
  side also closes after its third affix. With one side closed no side step is drawn. The loop ends after `count`
  filled slots or when both sides are closed, so a rare has at most 3 prefixes and 3 suffixes. Two logged rares ran a
  side out: a `buc` at ilvl 1 (count 6) whose third suffix pick found no row, with the prefix side full, ended at 5
  affixes; an `lgl` at ilvl 2 (count 5) whose suffix side closed at slot 3 retried the slot as a prefix and reached 5.
  [C] (0x005C1DA6–0x005C1DB8, run:2026-10-14-affixes)
- E4. A rare has fewer affixes than its count only when both sides run out; no logged rare had fewer than 3. [C]
  (0x005C1CB1–0x005C1E16, run:2026-10-14-affixes)
- E4. Each slot pick has `mustRoll` 1, so its draw 1 is spent with the bit ignored. With a side step, a filled slot
  costs 3 draws; a slot on the only open side costs 2. [C] (0x005C1CB1–0x005C1E16, run:2026-10-14-affixes)
- E4. The two fatal checks for a fourth prefix or suffix (error lines 0x31D and 0x32E) are unreachable. [I]
  (0x005C1CB1–0x005C1E16)
- E6. **All picks come before all properties.** The properties are applied in the order prefix 0, suffix 0, prefix
  1, suffix 1, prefix 2, suffix 2, skipping empty slots. [C] (0x005C1E16–0x005C1E70, run:2026-10-14-affixes)
- E2, E5. A failed rare build (no name, or no affix) falls back to magic with the item seed reset to `{S, 666}`
  ([items/uniques-sets § E](uniques-sets.md#e-failure-durability-and-the-fallback-chain)), discarding the rare
  builder's draws. Not reached in the run. [I] (0x005C1E71, fn:sub_00557380_ItemFallbackMagic@0x00557380)

### F. The superior builder — `ITEMS_BuildSuperior` → `ITEMS_BuildSuperiorPick`

```
F1. n: i32 ← count(QualityItems)                                          ; 8 rows with stock data   [C] (fn:ITEMS_BuildSuperiorPick@0x005C2970, run:2026-10-14-affixes, all of F1–F4)
    if ItemTypes[type].Throwable or base.nodurability: n ← 4
    tried[0..9] ← false
F2. loop:
      repeat:
        if n < 1: row ← 0                                                 ; no draw
        else: row ← Range(item.seed, n)                                   ; draw (RNG_Range inlined)
      until not tried[row]
F3.   if QualityItemTypeOk(item, QualityItems[row]):
        item.fileIndex ← row
        ItemApplyProps(item, QualityItems[row])                           ; ORACLE, items/properties
        RollStaffMods(item, rec)                                          ; ORACLE, § I
        return true
F4.   tried[row] ← true
      if every row < n is tried: return false                             ; → normal fallback
```

**`QualityItemTypeOk(item, q)`** reads the record's ten flag bytes: byte 1 (`weapon`) for an item that is type 45
(`weap`, with `Equiv`) whose base type is none of 24, 25, 26, 27, 35; byte 0 (`armor`) for a type-50 (`armo`) item
whose base type is none of 2, 15, 16, 19; else the byte of the exact base type: 2 → 2 (`shield`), 24 → 3 (`scepter`),
25 → 4 (`wand`), 26 → 5 (`staff`), 27 and 35 → 6 (`bow`), 15 → 7 (`boots`), 16 → 8 (`gloves`), 19 → 9 (`belt`).
[C] (fn:sub_0065E7D0_QualityItemTypeOk@0x0065E7D0, tbl:QualityItems.txt:weapon, tbl:QualityItems.txt:armor,
run:2026-10-14-affixes)

Step notes:

- F2. Each draw is one step; a tried row is redrawn, so the number of steps is not fixed. The run logged 40 rows
  refused by the type test and 22 redraws of a tried row. [C] (fn:ITEMS_BuildSuperiorPick@0x005C2970,
  run:2026-10-14-affixes)
- F1. A throwable or `nodurability` base draws from the first 4 rows only, which hold no `dur%` property with stock
  data. [C] (fn:ITEMS_BuildSuperiorPick@0x005C2970, tbl:Weapons.txt:nodurability, run:2026-10-14-affixes)
- F1. `tried` is a 10-byte buffer; a `QualityItems` table of more than 10 rows would overflow it. Stock has 8. [I]
  (fn:ITEMS_BuildSuperiorPick@0x005C2970, [QualityItems](../../tables/QualityItems.md#interpretation-notes))
- F. `ITEMS_BuildSuperior` reads the item version and discards it, then calls the pick. [I]
  (fn:ITEMS_BuildSuperior@0x005C2AD0)

### G. The low-quality builder — `ITEMS_BuildLow` → `ITEMS_BuildLowPick`

```
G1. row ← Range(item.seed, count(LowQualityItems)); item.fileIndex ← row    [C] draw (fn:ITEMS_BuildLowPick@0x005C2D40, 0x005C2D80, run:2026-10-14-affixes)
G2. if the item has durability:                                             [I] (fn:ITEMS_BuildLowPick@0x005C2D40, all of G2–G4)
      M: i32 ← max(1, base.durability × 33 ÷ 100)                           ; u8 column, unsigned
      maxdurability ← M
      durability ← max(1, Range(unit.seed, M ÷ 2) + M ÷ 2)                  ; UNIT seed, not item seed
G3. if item is type 45 (weapon): each damage stat ← stat × 75 ÷ 100         ; signed; floors 2/1/2/1
      if the type is throwable: the throw damage alike
    else if item is type 50 (armour): defense ← max(1, defense × 75 ÷ 100)
G4. RollStaffMods(item, rec)                                                ; ORACLE, § I, always called
    return true for a weapon or an armour, else false                       ; false → normal fallback
```

Step notes:

- G1. The row draw is the low builder's only draw on the item seed; the durability draw of G2 steps the unit seed at
  `Unit+0x20`, which the item-seed model never sees. [C] (fn:ITEMS_BuildLowPick@0x005C2D40, 0x005C2F93,
  run:2026-10-14-affixes)
- G2. `durability` goes through `RNG_RangeB` on the unit seed. [I] (fn:RNG_RangeB@0x0045C3E0,
  tbl:Weapons.txt:durability)

### H. The normal builder — `ITEMS_BuildNormal`

```
H1. if base type = 13 (charm): CharmForcedAffixes(item, rec)                 [I] (fn:ITEMS_BuildNormal@0x00556E80, fn:sub_00556A60_CharmForcedAffixes@0x00556A60)
    else if type 40 or 7 (body parts): item.fileIndex ← (from the base)
    else if type 22 (scroll) or 18 (book): suffix[0] ← a fixed id by base code   ; table at 0x0096CC60
H2. tail jump to RollStaffMods(item, rec)                                    [C] ORACLE (0x00556F24, fn:ITEMS_RollStaffMods@0x005C1260, run:2026-10-14-affixes)
```

Step notes:

- H1. For any other base the normal builder draws nothing of its own on the item seed. [C]
  (fn:ITEMS_BuildNormal@0x00556E80, run:2026-10-14-affixes)
- H1. `CharmForcedAffixes` picks a prefix and then a suffix through § C with the record's forced ids (on a drop both
  0, so as in D1–D2), and raises a fatal error (line 0x372) if both are 0. A charm reaches the normal builder only at
  the end of a failed magic → superior chain, which was not logged. [I] (fn:sub_00556A60_CharmForcedAffixes@0x00556A60)
- H2. The tail jump returns from the staff-mods roll straight into `sub_00556F30_ItemBuildNormalCase`. [C]
  (0x00556F24, fn:sub_00556F30_ItemBuildNormalCase@0x00556F30, run:2026-10-14-affixes)

### I. Staff mods — `ITEMS_RollStaffMods`

Called last by every builder above: magic, rare and superior on success only, low always, normal through the tail
jump. [C] (fn:ITEMS_RollStaffMods@0x005C1260, 0x0055669D, 0x005C1E3E, 0x005C2AAA, 0x005C2F98, 0x00556F24,
run:2026-10-14-affixes)

The reproduction keeps this roll as an oracle, so its draws below are as read, not reproduced.

```
I1. c ← ItemTypes[type].StaffMods                                           [I] (fn:ITEMS_RollStaffMods@0x005C1260, fn:sub_0062BBD0_ItemTypeStaffMods@0x0062BBD0)
    if c ≥ 7 or class c has no skills: return                              ; no draw
    first ← firstSkill(c); ilvl ← rec.ilvl (rec+0x0C)
    bonus ← ilvl if rec.flags (rec+0x80) & 0x20 else 0                     ; 0 on a drop
I2. t ← low % 100 + bonus after one Step                                   [I] (fn:sub_005C0F90_StaffModsRoll@0x005C0F90, all of I2–I6)
    mods ← 3 if t ≥ 91, 2 if t ≥ 71, 1 if t ≥ 31, else (1 if bonus ≠ 0 else 0)
I3. tier ← 5 if ilvl ≥ 37 and expansion, else 4 if ilvl ≥ 25, 3 if ≥ 19, 2 if ≥ 12, else 1
    for each mod:
I4.   u ← low % 100 after one Step
      t' ← tier + 1 if u ≥ 81, tier if u ≥ 31, tier − 1 if u ≥ 11, else tier − 2
      t' ← max(t', 1); on a low-quality item t' ← min(t', 4)
I5.   up to 6 tries, one Step each:
        skill ← low % 5 + (t' − 1) × 5 + first
        accept if not a repeat and (Skills[skill].itypea1 is empty or the item is of that type)
      if all 6 fail: keep the last skill drawn
I6.   unless the item is a low-quality expansion item:
        v ← low % 100 + bonus ÷ 2 after one Step; level ← 3 if v ≥ 90, 2 if v ≥ 60, else 1
      set stat 107 (item_singleskill), layer skill, to that level
```

Step notes:

- I1. `firstSkill(c)` is the first id of the class's 30-id `Skills` run: logged on all 74 staff-mods rolls for
  classes 1 to 6 (36, 66, 96, 126, 221, 251). Class 0 (`ama`, 6) was not logged. [C] (0x005C1285–0x005C128A,
  tbl:Skills.txt:charclass, run:2026-10-14-affixes, [Skills § Class blocks](../../tables/Skills.md#class-blocks))
- I2–I6. Every `low % k` uses the unsigned low word; all draws are on the item seed. [I]
  (fn:sub_005C0F90_StaffModsRoll@0x005C0F90)
- I1. The classic body `sub_005C0D70_StaffModsRollV0` (item version 0 only) has no bonus, tier 4 at most, a try loop
  that runs until a non-repeat other than 0x49, and an unconditional level draw. [I]
  (fn:sub_005C0D70_StaffModsRollV0@0x005C0D70)

### J. After the switch: ethereal, sockets, automagic

```
J1. q ← item.quality; if q < 1 or q > 9: return false                                 [I] (0x00557943–0x005579A2)
J2. if itemVersion ≥ 100: EtherealRoll(item, rec)                                       [C] BOUNDARY, items/properties (fn:sub_00556CA0_ItemRollEthereal@0x00556CA0, run:2026-10-14-affixes)
J3. if q ∈ 1..3: SocketRoll(item, rec)                                                  [C] BOUNDARY, items/properties (fn:sub_00556B60_ItemRollSockets@0x00556B60, run:2026-10-14-affixes)
J4. g ← base.autoPrefix                                                                 [C] (0x005579A8–0x00557A0C, fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940, run:2026-10-14-affixes)
    if itemVersion ≥ 100 and q ∉ {5, 7} and g ≠ 0:
      id ← PickMagicAffix(item, needSpawnable 0, mustRoll 1, applyProps 0, prefix, 0, autoGroup g)
      if id > 0:
        autoAffix ← id
        ItemApplyProps(item, record(id))                                                 ; ORACLE, items/properties
J5. return true
```

Step notes:

- J2–J3. What the ethereal and socket rolls draw is specified in `items/properties`. This spec needs only their
  place: after the builder and its staff mods, before the automagic pick. [C] (0x00557943–0x005579A3,
  run:2026-10-14-affixes, [items/0005 § 12](../../findings/items/0005-affixes.md#12-where-the-draws-sit-on-the-item-seed))
- J4. The automagic pick is a § C pick over the `automagic` block with `autoGroup` = the base's `auto prefix`. It
  makes draw 1 with the bit ignored and, with candidates, draw 2. It runs the level window on the same alvl, the
  `rare` test, the type test, `frequency`, the class test and group exclusion. The 36 logged automagic rows were all
  on class items, on qualities 2 (10), 3 (1), 4 (22) and 6 (3). [C] (fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940,
  tbl:Weapons.txt:auto prefix, tbl:AutoMagic.txt:group, run:2026-10-14-affixes)
- J4. **The automagic pick does not test `spawnable`** (`needSpawnable` 0). Every stock `automagic` row has
  `spawnable` 1, so no run can show the difference. [I] (0x005579DF, tbl:AutoMagic.txt:spawnable)
- J4. Qualities 5 and 7 skip the step; 1, 2, 3, 4, 6, 8 and 9 take it (jump table at 0x00557A58). A skip on 5 or 7
  was not logged. [I] (0x005579B3–0x005579BF)
- J4. A classic item never reaches the pick. [C] (0x005579A2, run:2026-10-14-affixes)
- J4. A base whose group has no eligible row gets no automagic and still spends draw 1. With stock data no base and
  ilvl has such a group. `automagic` group 301 is named by no base, so its rows never drop. [I] (0x005579A2,
  tbl:AutoMagic.txt:group)

### K. Classic games and item version 0

- [C] A classic game's items have a version of 1..99, never 0, so they take the same pick, rare and low bodies as
  expansion items; only the `version` ≥ 100 tests and the classic stackable/throwable refusal (C5a, R1) differ. The
  version dispatchers branch on 0. 120 magic and 18 rare classic builds reproduce with § B to § E.
  (fn:sub_005C18E0_PickMagicAffixByVersion@0x005C18E0, fn:sub_0062A670_ItemGetVersion@0x0062A670,
  run:2026-10-14-affixes)
- [I] The version-0 bodies use other rules: `sub_005C12F0_PickMagicAffixV0` (alvl = ilvl + 2, a uniform draw, no
  `frequency`), `sub_005C1E80_ItemBuildRareV0` (count `4 + low % 3`, up to 252 redraws per slot),
  `sub_005C19A0_PickRareNameV0` and `sub_005C2AF0_ItemBuildLowV0` (`durability/3`, no staff mods). No drop reaches
  them. (fn:sub_005C12F0_PickMagicAffixV0@0x005C12F0, fn:sub_005C1E80_ItemBuildRareV0@0x005C1E80,
  fn:sub_005C19A0_PickRareNameV0@0x005C19A0, fn:sub_005C2AF0_ItemBuildLowV0@0x005C2AF0)
- [I] So the `frequency` 0, `version` 0 rows of both magic tables are never candidates on the drop path, in either
  game type. (tbl:MagicPrefix.txt:version, tbl:MagicPrefix.txt:frequency)

### Draw order on the item seed

```mermaid
sequenceDiagram
  participant B as builder
  participant I as item.seed
  participant O as oracles and boundaries
  Note over I: S, 666 at builder entry
  alt magic
    B->>I: prefix draw 1, bit 0
    B->>I: prefix draw 2, Range W + 1, if rolled and found
    B->>O: prefix ItemApplyProps
    B->>I: suffix draw 1, draw 2
    B->>O: suffix ItemApplyProps
  else rare
    B->>I: name 1 Range, name 2 Range
    B->>I: count draw
    loop each slot
      B->>I: side step, only while both sides are open
      B->>I: pick draw 1, draw 2
    end
    B->>O: ItemApplyProps p0 s0 p1 s1 p2 s2
  else superior
    B->>I: row draws until an untried row passes
    B->>O: ItemApplyProps
  else low
    B->>I: row draw
  end
  B->>O: RollStaffMods
  O->>O: ethereal roll if expansion, socket roll if quality 1 to 3
  B->>I: automagic draw 1, draw 2
  B->>O: automagic ItemApplyProps
```

- [C] From the builder entry `{S, 666}` the item seed sees, in order: the builder's draws with its property calls (the
  magic builder interleaved per pick, the rare builder all picks first), the staff mods, the ethereal roll, the socket
  roll, then the automagic pick and its properties. Every oracle entry seed and every join and return seed matched
  this order. (fn:ITEMS_BuildMagic@0x005565E0, fn:ITEMS_BuildRareAffixes@0x005C1BF0,
  fn:ITEMS_BuildSuperiorPick@0x005C2970, fn:ITEMS_BuildLowPick@0x005C2D40, run:2026-10-14-affixes)
- [C] A failed builder's draws are discarded: the next fallback step resets the item seed to `{S, 666}`
  ([items/uniques-sets § E](uniques-sets.md#e-failure-durability-and-the-fallback-chain)). 24 magic builds after a
  failed set started from that reset. (fn:sub_00557380_ItemFallbackMagic@0x00557380, run:2026-10-14-affixes)

## Outputs

At the return of `ItemCreateByQuality`:

| Quality | Written by this spec | Tag |
|---|---|---|
| 4 magic | `prefix[0]` and/or `suffix[0]` (merged ids), flag 0x10, their properties | [C] (fn:ITEMS_BuildMagic@0x005565E0, run:2026-10-14-affixes) |
| 6 rare | `rareName1`, `rareName2` (merged rare ids), up to 3 prefixes and 3 suffixes, flag 0x10, their properties | [C] (fn:ITEMS_BuildRareAffixes@0x005C1BF0, run:2026-10-14-affixes) |
| 3 superior | `fileIndex` = the `QualityItems` row, its properties | [C] (fn:ITEMS_BuildSuperiorPick@0x005C2970, run:2026-10-14-affixes) |
| 1 low | `fileIndex` = the `LowQualityItems` row; durability and damage or defense lowered | [C] row (fn:ITEMS_BuildLowPick@0x005C2D40, run:2026-10-14-affixes) |
| every builder | the staff-mods skills (stat 107) of a class item | [C] placement (fn:ITEMS_RollStaffMods@0x005C1260, run:2026-10-14-affixes) |
| expansion, not 5 or 7 | `autoAffix` (merged id in the automagic block) and its properties | [C] (fn:sub_005C1940_PickAutoAffixByVersion@0x005C1940, run:2026-10-14-affixes) |

- [C] Every logged chosen id, rare name, rare count, superior and low row, and the item seed at the join and at the
  return matched the model. (0x00557943, run:2026-10-14-affixes)

## Worked example

Seeds are `low:high` in hex. Each example was checked by `python3 -I tools/affixes.py check -v <log>` (0
mismatches); the draws were recomputed with `Step` of [rng](../rng/README.md#algorithm), the weights from the stock
tables with `tools/affixes.py`'s loader. Log lines are records of `tools/gdb/affixes.py`; the logs are in
`workspace/logs/` (not in git, sha256 in the run's manifest). In a log, `AFC` carries the seed after draw 1 and
`AFX` the seed after draw 2.

### Example 1: a magic item with a prefix and a suffix

`affixesn-2303-normal.log` lines 3298–3318, [run:2026-10-14-affixes](../../findings/items/experiments.md#run2026-10-14-affixes).
Expansion Normal, item 276 `ob1` (a sorceress orb: qlvl 1, `magic lvl` 1, `auto prefix` 303), ilvl 1, item version
101, quality 4, entry seed `9087d8f7:0000029a`. [C] (run:2026-10-14-affixes)

alvl: `i = max(1, 1) = 1`; `m = 1`, so `alvl = 2` (§ B2; `AFC … "alvl":2,"m":1`). Weights are `frequency × level`,
and every candidate here has `level` 1.

| Step | Draw | Seed after | Value |
|---|---|---|---|
| D1 prefix, C2 | 1 | `b79ee8ad:3c485aa3` | bit 0 = 1 → roll |
| C4 | — | — | 7 candidates, W = 20 (below) |
| C7 | 2 | `8440b7c4:4c963916` | `0x8440b7c4 mod 21 = 5` → id 1410 |
| C8 | oracle | `c359e2ea:372960ef` | prefix properties |
| D2 suffix, C2 | 3 | `7ff49f01:517abdf3` | bit 0 = 1 → roll (mustRoll 0: a prefix is set) |
| C4 | — | — | 2 candidates, W = 8 |
| C7 | 4 | `c6efa9b8:355e8965` | `0xc6efa9b8 mod 9 = 4` → id 740 |
| C8 | oracle | `c6efa9b8:355e8965` | suffix properties (no draw here) |
| D4 | oracle | `1fed7c74:51e5808f` | staff mods, class 1, `firstSkill` 36 (`STFC`) |

Prefix walk, x = 5 (`AFC … "ids":[1013,1302,1410,1411,1412,1413,1414]`):

| Candidate | Id (prefix row) | Weight | x after | Outcome |
|---|---|---|---|---|
| 0 | 1013 (265) *Glimmering* | 1 | 4 | |
| 1 | 1302 (554) *Septic* | 3 | 1 | |
| 2 | 1410 (662) *Lizard's* | 4 | −3 | **chosen** |

Suffix walk, x = 4: candidates 293 (suffix row 292) and 740 (row 739), both *of Energy*, group 23, weight 4 each;
`4 − 4 = 0` is not below 0, `0 − 4 = −4` → **740**. Row 740 has `maxlevel` 4, row 293 none: two rows of one group
can both be candidates until one is on the item. The join seed is `1fed7c74:51e5808f` (`ICJ`). [C] (run:2026-10-14-affixes)

### Example 2: a rare item

`affixesn-2301-normal.log` lines 5721–5754, [run:2026-10-14-affixes](../../findings/items/experiments.md#run2026-10-14-affixes).
Expansion Normal, item 68 `sbw` (qlvl 1, no `magic lvl`, `auto prefix` 0), ilvl 5, item version 101, quality 6, entry
seed `2734d95a:0000029a`. alvl: `i = 5`, `h = 0`, `5 < 99` → 5. [C] (run:2026-10-14-affixes)

| Step | Draw | Seed after | Value |
|---|---|---|---|
| E2 name 1 | 1 | `4589e4dc:105a4b0b` | 36 rare prefix candidates, `0x4589e4dc mod 36 = 0` → id 156 (rareprefix row 0, *Beast*) |
| E2 name 2 | 2 | `3e5b2857:1d0108bd` | 14 rare suffix candidates, `0x3e5b2857 mod 14 = 1` → id 41 (raresuffix row 40, *dart*) |
| E3 count | 3 | `992203b0:1a021c78` | `low & 7 = 0` → `RARE_COUNT[0]` = 3 |
| E4 slot 0 side | 4 | `cd61f2e8:3fdedc6e` | bit 0 = 0 → prefix |
| C2 | 5 | `545148f6:55a9dc7b` | mustRoll: the bit is ignored |
| C7 | 6 | `3b8561c9:232b0ec3` | 13 candidates, W = 70, `mod 71 = 28` → id 986 *Iron* |
| E4 slot 1 side | 7 | `d3465e70:18d3654f` | prefix |
| C2, C7 | 8, 9 | `3f9ae9bc:487560a0` | 11 candidates, W = 54, `mod 55 = 3` → id 933 *Jagged* |
| E4 slot 2 side | 10 | `fd8cfe4c:1a877a90` | prefix |
| C2, C7 | 11, 12 | `89f1abf6:4883142f` | 9 candidates, W = 36, `mod 37 = 16` → id 1156 *Beryl* |
| E6 | oracle × 3 | `8bf26748:45da467f` | properties of 986, 933, 1156, in that order |
| E7 | oracle | `8bf26748:45da467f` | staff mods (no `StaffMods` class: nothing drawn) |

Slot 0 walk, x = 28: *Jagged* 9 → 19, *Deadly* 9 → 10, *Bronze* 8 → 2, *Iron* 8 → −6, so **986**. Slot 1 drops
*Bronze* (group 110, taken by *Iron*); x = 3 < 9 → *Jagged*. Slot 2 drops *Deadly* (group 105, taken by *Jagged*); x =
16 runs through *Sharp* 9, *Azure* 2, *Tangerine* 4 and ends on *Beryl* (4). The third prefix closes the prefix side,
and with i = 3 = count the loop ends: 3 prefixes, no suffix. The names were drawn before the count and every
affix. [C] (run:2026-10-14-affixes)

### Example 3: an automagic pick

The item of Example 1, lines 3319–3325. The join seed `1fed7c74:51e5808f` goes through the ethereal roll (a logged
boundary; quality 4 takes no socket roll), which hands the automagic pick `c35f85d3:0d511944`. [C] (run:2026-10-14-affixes)

| Step | Draw | Seed after | Value |
|---|---|---|---|
| J4, C2 | 1 | `004bc4a3:517d17c7` | mustRoll: the bit is ignored |
| C4 | — | — | block `automagic`, group 303, alvl 2: one candidate, id 1426 (automagic row 9, *of the Jackal*), weight `6 × 1` |
| C7 | 2 | `be791936:001f9a30` | W = 6, `0xbe791936 mod 7 = 5` → 5 − 6 < 0 → **1426** |
| J4 | oracle | `8d4260be:4f71e1d0` | automagic properties; the return seed (`ICX`) |

A single candidate still costs both draws. [C] (run:2026-10-14-affixes)

## Reimplementation notes

- **Draw 1 of every pick is spent**, even when `mustRoll` makes its bit irrelevant (every rare slot, the automagic
  pick) and even when no candidate exists. [C] (0x005C15FD–0x005C1645, run:2026-10-14-affixes)
- **`Range(W + 1)`, not `Range(W)`.** The last candidate in table order gets one extra unit of weight. [C]
  (0x005C1828–0x005C189E, run:2026-10-14-affixes)
- **alvl, not ilvl.** The level window and the weights use alvl (§ B); the community rule "qlvl ≤ ilvl + 2, uniform"
  describes only the version-0 body. Do not port it. [C] (0x005C1664–0x005C16C2, run:2026-10-14-affixes)
- **`magic lvl` bases weight by `frequency × level`**, not `frequency`. [C] (0x005C17CE–0x005C17EA, run:2026-10-14-affixes)
- **Rares have 3 to 6 affixes, not 2 to 6**, and the names do not depend on the affixes: both names are drawn first.
  [C] (data:g_RareAffixCountTable@0x006E3014, run:2026-10-14-affixes)
- **A failed rare pick does not use up the slot.** Close the side and retry on the other one; draw no side step once
  a side is closed. [C] (0x005C1DA6–0x005C1DB8, run:2026-10-14-affixes)
- **Magic properties come inside each pick, rare properties after all picks.** Swapping the two orders changes every
  later draw. [C] (fn:ITEMS_BuildMagic@0x005565E0, fn:ITEMS_BuildRareAffixes@0x005C1BF0, run:2026-10-14-affixes)
- **`classspecific` does not keep a row off classless items.** Only the row's `itype` list does. [C]
  (0x005C1781–0x005C179E, run:2026-10-14-affixes)
- **The automagic pick runs after the ethereal and socket rolls,** on the same item seed, and uses the same alvl as
  the builder's picks. [C] (0x005579A8–0x00557A0C, run:2026-10-14-affixes)
- **The low-quality durability draw is on the unit seed.** Putting it on the item seed shifts the staff mods and
  everything after. [I] (fn:ITEMS_BuildLowPick@0x005C2D40)
- **Superior draws are not a fixed count.** Redraw a tried row; stop when every row of the range is tried. [C]
  (fn:ITEMS_BuildSuperiorPick@0x005C2970, run:2026-10-14-affixes)
- **Ids are merged indices + 1.** A prefix id is not a `magicprefix` row number; subtract the block start and 1. [C]
  (fn:MAGICAFFIX_GetRecord@0x00633EE0, run:2026-10-14-affixes)
- **Ghidra's decompile of the weighted walk shows a draw of W as "no affix".** The disassembly takes the last
  candidate; follow the disassembly. [C] (0x005C188B, run:2026-10-14-affixes)

## Evidence

- [findings/items/0005-affixes.md](../../findings/items/0005-affixes.md): the builders, the picks and the automagic step
  read from the code (Phase 1), the community cross-check (Phase 1b, *Leads used*), and the reproduction
  (*Phase 2 results*).
- [findings/items/experiments.md § run:2026-10-14-affixes](../../findings/items/experiments.md#run2026-10-14-affixes):
  51 stock sessions (41 with creations), 3 102 creations, 0 mismatches.
- [findings/items/0004-uniques-sets.md](../../findings/items/0004-uniques-sets.md): the switch, the fallback chain and
  the post-switch steps named (§ 8).
- [findings/items/0006-properties.md](../../findings/items/0006-properties.md): the property roll and the ethereal and
  socket rolls this spec treats as oracles and boundaries (plan 0024).
- Tables: [MagicPrefix](../../tables/MagicPrefix.md) (and [MagicSuffix](../../tables/MagicSuffix.md)),
  [RarePrefix](../../tables/RarePrefix.md) (and [RareSuffix](../../tables/RareSuffix.md)),
  [AutoMagic](../../tables/AutoMagic.md), [QualityItems](../../tables/QualityItems.md),
  [LowQualityItems](../../tables/LowQualityItems.md), [Skills](../../tables/Skills.md),
  [ItemTypes](../../tables/ItemTypes.md), [Weapons](../../tables/Weapons.md), [Armor](../../tables/Armor.md),
  [Misc](../../tables/Misc.md), [Properties](../../tables/Properties.md).
- Specs: [rng](../rng/README.md) (`Step`, `Range`), [items/uniques-sets](uniques-sets.md) (the switch, the entry seed,
  the fallbacks), [items/quality](quality.md) (the quality code). `items/properties` (`docs/specs/items/properties.md`,
  plan 0024): the property values, ethereal and sockets.
- `tools/affixes.py` (`check`, `survey`), the reference model; `tools/affix_survey.py`, the candidates per base.

## Open questions

- [L] **Not reached in the run**, so still code-read: a rare jewel (count `3 + low % 2`), the classic
  stackable/throwable refusal (C5a, R1), the socket test (C5b), an empty rare name list, a failed magic builder, the
  charm path of the normal builder, automagic skipped on qualities 5 and 7, the forced rows and the version-0 bodies.
  A forced-path run (ADR-0010) or the `items/cube` and `items/vendors` paths could reach the forced rows and the charm.
- [L] **Automagic and `spawnable`.** The pick passes `needSpawnable` 0, but every stock `automagic` row has
  `spawnable` 1; ruled unreachable with stock data (plan 0021 Phase 1 review). Only modded data would show it.
- [L] **The staff-mods skill test** (§ I5) was read from a decompile whose condition grouping is awkward (an
  out-of-range skill index also reads as accepted). It needs a re-read in the disassembly at 0x005C1125, or the
  model of `items/properties`, before § I can be reproduced. Class 0 (`ama`) `firstSkill` was not logged.
- [L] **The automagic `class_affix` in a save** (record + 1) was not checked: no session wrote a save. `save/d2s`.
- [L] **The stitch with `items/properties`.** This spec's reproduction takes the ethereal and socket rolls' exit
  seeds from the log; plan 0024 models them. A chained check of both models over one run's logs would close the
  join-to-automagic gap.
