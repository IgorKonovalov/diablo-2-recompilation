# MonStats2 (`data/global/excel/MonStats2.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 609 (610 data rows less one `Expansion` marker)   **Record:** 308 B (`0x134`)
> **sha256:** `.txt` `028483a664eec434d6d54fd933d3245d16ce7ee5271ff9fd1f4612da0e05cf7d`, `.bin` `9d605ca4a2039ce99d899a884fb6a44b4d6ad39d0286299bf5221472e8875d84`
> **Doc status:** columns listed, `.bin` layout complete, semantics partial (the columns the monster pool reads)

## Purpose

One row per monster *appearance* class: the graphics side of a monster (size, hit box, the composite
components and their variants, which animation modes exist, light, palette shift). A `MonStats` record
points at its row through `MonStatsEx` (`+0x018`, [MonStats](MonStats.md)). Plan 0012 needs it because the
level monster pool rolls each entry's appearance sets from this table's component counts, with draws on the
pool's seed between one level's pool and the next ([monsters/0001 § 4](../findings/monsters/0001-level-pool.md),
`monsters/pool`). Everything else here is graphics and client data; no other finding reads it yet.

## Row identity

- `[C]` Rows are addressed by position: the `.bin` record count (609) is the `.txt` data rows less the one
  `Expansion` marker row, and the first field (`+0x000`, u16) holds each record's own index, i.e. the `Id`
  column compiled as an index into this table. (tbl:MonStats2.txt:Id)
- `[C]` The loader reads `monstats2.bin` with 308-byte records
  ([data/0001 §4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), call site
  `0x00658422`).
- `[I]` A MonStats class reaches its record through MonStats `+0x018` (`sub_00451FE0_MonStats2Rec`).
  (fn:sub_00451FE0_MonStats2Rec@0x00451FE0)

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monstats2` decodes
every record and compares it with every mapped cell: **609 records × 142 mapped fields = 86 478 cells, 0
mismatches** (layout `monstats2` in `tools/excel_layouts.py`). A field is `[C]` when a probe over every record
finds only that offset for the column; `[I]` when the column is constant or equal to a sibling, so its slot comes
from the stride of its group; "width `[I]`" when the bytes after a field are zero in every record, so a wider
integer would also fit. **Meaning:** names only, `[L]`, except the rows of § [What the monster pool reads](#what-the-monster-pool-reads) and
the *plan 0046 readers* (plan 0051 Phase 0), which carry their own tags.

Three special encodings (`tools/excel_bin.py` field types `tokcount`, `toklist`, `toksum`):

- `[C]` **Component lists.** Each of the sixteen `HDv` … `S8v` cells is a quoted comma list of component codes
  (`"lit,lit,lit,med,hvy,hvy,hvy"`). It compiles twice: its **count** of non-empty codes as a u8 at
  `+0x015 + k`, and the codes themselves as **twelve u8 row indices of [compcode](compcode.md)** (`nil` 0, `lit` 1,
  `med` 2, `hev` 3, `hvy` 4, …) at `+0x026 + 12·k`, `0xFF` past the last one. *k* is the column's position in
  `HDv, TRv, LGv, Rav, Lav, RHv, LHv, SHv, S1v … S8v`. A blank cell gives count 0 and twelve `0xFF`. A trailing
  empty code is dropped: `act2male` `S1v` = `"lit,nil,nil,fez,nil,nil,rol,nil,nil,"` stores 9. The longest lists
  (`S1v`, `S2v`) fill all 12 slots. (tbl:MonStats2.txt:HDv)
- `[C]` **`+0x025` is computed**, not a column: `Σ over the sixteen lists of max(count − 1, 0)`. It holds for all
  609 records (values 0 ×461, up to 49). (tbl:MonStats2.txt:HDv)
  `[C]` The compiler writes it in the list-column callback `sub_00657010_MonStats2CompList` while it handles
  the last list (`S8v`): the pinned game's own `-direct -txt` compile wrote a `monstats2.bin` byte-identical to the
  shipped one (run:2026-10-15-cube-saves), and the byte equals the sum recomputed in all 609 records
  ([monsters/0001 § S3b](../findings/monsters/0001-level-pool.md#plan-0038-batch-s3b-2026-10-16) pool 9,
  [data/0004](../findings/data/0004-cell-converters.md), fn:sub_00657010_MonStats2CompList@0x00657010,
  run:2026-10-15-cube-saves). `[I]` The cap at 254 is read only (0x00657183); no stock value reaches it (largest 49).
- `[C]` **Bit groups indexed by position.** `HD` … `S8` are bits 0..15 of the u16 at `+0x0E8` in list order;
  `mDT` … `mRN` are bits 0..15 of `+0x0F0` and `dDT` … `dRN` the u8s `+0x0F4` … `+0x103`, both in
  `MonMode.txt` row order (`DT NU WL GH A1 A2 BL SC S1 S2 S3 S4 DD KB SQ RN`); the seven `*mv` columns
  are the bits of the same mode index at `+0x104` (`A1mv` bit 4, `A2mv` 5, `SCmv` 7, `S1mv` 8 …). Columns that
  are constant (`TR`, `A1mv`, `SCmv`, `S3mv`, `S4mv`) take the slot of that order `[I]`.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Id` | str, 609 distinct, len ≤ 17 | `+0x000` u16 index | self | [C] |
| `Height` | int 0..4 (5 distinct) | `+0x00B` u8 | — | [C] |
| `OverlayHeight` | int 0..4 (5 distinct) | `+0x00C` u8 | — | [C] |
| `pixHeight` | int 32..144 (11 distinct) | `+0x00D` u8 | — | [C] |
| `SizeX` | int 0..3 (4 distinct) | `+0x008` u8 | *plan 0046 readers:* `[C]` read `movsx` by `UNIT_GetSizeX` for a type-1 unit (0 without a row; 2 for a player): the size argument of start 40's `FreeNearFallback` (ADR-0021) ([skills/0012 § 6](../findings/skills/0012-barbarian.md#6-whirlwind-the-leaps-and-double-throw-start-38-40-41-do-74-76-77-78); fn:UNIT_GetSizeX@0x00620510) | [I] |
| `SizeY` | int 0..3 (4 distinct) | `+0x009` u8 | — | [I] |
| `spawnCol` | int 1..3 (3 distinct), 589 blank | `+0x00A` u8 | — | [C] |
| `MeleeRng` | int 0..6 (6 distinct) | `+0x00E` u8 | *plan 0046 readers:* `[C]` as a map: `sub_00622870_UnitMeleeReach` gives a monster this byte (through MonStats `MonStatsEx`; 0 without a row), and start 9 and do 13 search at that plus 4; the value `0xFF` sends it to `0x0064F380` instead (ADR-0021 boundaries) ([skills/0009 § 3](../findings/skills/0009-amazon.md#3-start-4-5-8-and-9-ammunition-a-target-and-the-strafe-and-fend-counts), [§ 7](../findings/skills/0009-amazon.md#7-do-12-and-do-13-strafe-fend-zeal-and-fury); fn:sub_00622870_UnitMeleeReach@0x00622870, fn:sub_005DAE30_SkillSt09Fend@0x005DAE30, fn:sub_005DBC60_SkillDo13Fend@0x005DBC60); `[I]` that this is the monster's melee reach (the column name; stock 0..6, so the `0xFF` branch is synthetic only) | [C] (width [I]) |
| `BaseW` | str, 8 distinct, len ≤ 3 | `+0x010` char[4] | — | [C] |
| `HitClass` | int 1..12 (3 distinct) | `+0x014` u8 | — | [C] |
| `HDv` | list of 1..7 codes (19 distinct), 465 blank | `+0x015` u8 count; `+0x025` u8 Σ(count − 1), all 16; `+0x026` u8[12] `compcode` rows | `compcode:code` | [C] |
| `TRv` | list of 1..7 codes (7 distinct), 13 blank | `+0x016` u8 count; `+0x032` u8[12] `compcode` rows | `compcode:code` | [C] |
| `LGv` | list of 1..4 codes (8 distinct), 516 blank | `+0x017` u8 count; `+0x03E` u8[12] `compcode` rows | `compcode:code` | [C] |
| `Rav` | list of 1..4 codes (11 distinct), 479 blank | `+0x018` u8 count; `+0x04A` u8[12] `compcode` rows | `compcode:code` | [C] |
| `Lav` | list of 1..4 codes (11 distinct), 484 blank | `+0x019` u8 count; `+0x056` u8[12] `compcode` rows | `compcode:code` | [C] |
| `RHv` | list of 1..11 codes (20 distinct), 523 blank | `+0x01A` u8 count; `+0x062` u8[12] `compcode` rows | `compcode:code` | [C] |
| `LHv` | list of 1..4 codes (16 distinct), 560 blank | `+0x01B` u8 count; `+0x06E` u8[12] `compcode` rows | `compcode:code` | [C] |
| `SHv` | list of 1..5 codes (5 distinct), 574 blank | `+0x01C` u8 count; `+0x07A` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S1v` | list of 1..12 codes (17 distinct), 360 blank | `+0x01D` u8 count; `+0x086` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S2v` | list of 1..12 codes (12 distinct), 467 blank | `+0x01E` u8 count; `+0x092` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S3v` | list of 1..4 codes (5 distinct), 539 blank | `+0x01F` u8 count; `+0x09E` u8[12] `compcode` rows | `compcode:code`; *plan 0046 readers:* `[I]` skill do 148 (DoomKnightMissile) adds the caster's monster-data byte `+0x0E` to its `srvmissilea` ([skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63)), and that byte is component 10's (`S3`) drawn variant, in `[0, count)` (MonsterData `+0x04 + k`, [monsters/0004 § 6](../findings/monsters/0004-stats.md#6-appearance-and-monequip-draws)); `[C]` (data) the five classes with that skill (`doomknight2`, `doomknight3`, `dkmag1..3`) have `S3v` `pos,fir,col,unh` (count 4) on their MonStats2 row, and `undeadmissile1..4` are consecutive Missiles rows (fn:sub_005CDFB0_SkillDo148DoomKnightMissile@0x005CDFB0, fn:sub_005739D0_MonComponentsPick@0x005739D0) | [C] |
| `S4v` | list of 1..4 codes (8 distinct), 562 blank | `+0x020` u8 count; `+0x0AA` u8[12] `compcode` rows | `compcode:code`; *plan 0046 readers:* `[I]` skill do 149 (NecromageMissile) adds the byte `+0x0F`, component 11's (`S4`) drawn variant, as `S3v` for do 148; `[C]` (data) its one class, `necromage`, has `S4v` `pos,cld,fir,lht` (count 4), and `necromage1..4` are consecutive Missiles rows ([skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63); fn:sub_005CE0B0_SkillDo149NecromageMissile@0x005CE0B0) | [C] |
| `S5v` | list of 1..4 codes (7 distinct), 577 blank | `+0x021` u8 count; `+0x0B6` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S6v` | list of 1..1 codes (1 distinct), 605 blank | `+0x022` u8 count; `+0x0C2` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S7v` | list of 1..1 codes (1 distinct), 597 blank | `+0x023` u8 count; `+0x0CE` u8[12] `compcode` rows | `compcode:code` | [C] |
| `S8v` | list of 1..1 codes (1 distinct), 592 blank | `+0x024` u8 count; `+0x0DA` u8[12] `compcode` rows | `compcode:code` | [C] |
| `HD` | int, always 1, 463 blank | `+0x0E8` bit 0 | — | [C] |
| `TR` | int, always 1 | `+0x0E8` bit 1 | — | [I] |
| `LG` | int, always 1, 513 blank | `+0x0E8` bit 2 | — | [C] |
| `RA` | int, always 1, 477 blank | `+0x0E8` bit 3 | — | [C] |
| `LA` | int, always 1, 482 blank | `+0x0E8` bit 4 | — | [C] |
| `RH` | int, always 1, 509 blank | `+0x0E8` bit 5 | — | [C] |
| `LH` | int, always 1, 559 blank | `+0x0E8` bit 6 | — | [C] |
| `SH` | int, always 1, 574 blank | `+0x0E8` bit 7 | — | [C] |
| `S1` | int, always 1, 337 blank | `+0x0E9` bit 0 | — | [C] |
| `S2` | int, always 1, 463 blank | `+0x0E9` bit 1 | — | [C] |
| `S3` | int, always 1, 535 blank | `+0x0E9` bit 2 | — | [C] |
| `S4` | int, always 1, 562 blank | `+0x0E9` bit 3 | — | [C] |
| `S5` | int, always 1, 577 blank | `+0x0E9` bit 4 | — | [C] |
| `S6` | int, always 1, 605 blank | `+0x0E9` bit 5 | — | [I] |
| `S7` | int, always 1, 597 blank | `+0x0E9` bit 6 | — | [I] |
| `S8` | int, always 1, 578 blank | `+0x0E9` bit 7 | — | [C] |
| `TotalPieces` | int 1..11 (11 distinct) | `+0x0EC` u32 | — | [C] (width [I]) |
| `mDT` | int, always 1, 90 blank | `+0x0F0` bit 0 | — | [C] |
| `mNU` | int, always 1, 24 blank | `+0x0F0` bit 1 | — | [C] |
| `mWL` | int, always 1, 133 blank | `+0x0F0` bit 2 | — | [C] |
| `mGH` | int, always 1, 206 blank | `+0x0F0` bit 3 | — | [C] |
| `mA1` | int, always 1, 159 blank | `+0x0F0` bit 4 | — | [C] |
| `mA2` | int, always 1, 392 blank | `+0x0F0` bit 5 | — | [C] |
| `mBL` | int, always 1, 558 blank | `+0x0F0` bit 6 | — | [C] |
| `mSC` | int, always 1, 568 blank | `+0x0F0` bit 7 | — | [C] |
| `mS1` | int, always 1, 371 blank | `+0x0F1` bit 0 | — | [C] |
| `mS2` | int, always 1, 549 blank | `+0x0F1` bit 1 | — | [C] |
| `mS3` | int, always 1, 584 blank | `+0x0F1` bit 2 | — | [C] |
| `mS4` | int, always 1, 594 blank | `+0x0F1` bit 3 | — | [C] |
| `mDD` | int, always 1, 85 blank | `+0x0F1` bit 4 | — | [C] |
| `mKB` | int, always 1, 232 blank | `+0x0F1` bit 5 | — | [C] |
| `mSQ` | int, always 1, 225 blank | `+0x0F1` bit 6 | — | [C] |
| `mRN` | int, always 1, 552 blank | `+0x0F1` bit 7 | — | [C] |
| `dDT` | int 1..16 (4 distinct) | `+0x0F4` u8 | — | [C] |
| `dNU` | int 1..16 (4 distinct) | `+0x0F5` u8 | — | [C] |
| `dWL` | int 1..16 (4 distinct) | `+0x0F6` u8 | — | [C] |
| `dGH` | int 1..8 (3 distinct) | `+0x0F7` u8 | — | [C] |
| `dA1` | int 1..16 (4 distinct) | `+0x0F8` u8 | — | [C] |
| `dA2` | int 1..8 (3 distinct) | `+0x0F9` u8 | — | [I] |
| `dBL` | int 1..8 (3 distinct) | `+0x0FA` u8 | — | [I] |
| `dSC` | int 1..8 (3 distinct) | `+0x0FB` u8 | — | [I] |
| `dS1` | int 1..16 (4 distinct) | `+0x0FC` u8 | — | [C] |
| `dS2` | int 1..16 (4 distinct) | `+0x0FD` u8 | — | [C] |
| `dS3` | int 1..8 (3 distinct) | `+0x0FE` u8 | — | [I] |
| `dS4` | int 1..8 (3 distinct) | `+0x0FF` u8 | — | [I] |
| `dDD` | int 1..16 (4 distinct) | `+0x100` u8 | — | [C] |
| `dKB` | int 1..8 (3 distinct) | `+0x101` u8 | — | [I] |
| `dSQ` | int 1..8 (3 distinct) | `+0x102` u8 | — | [I] |
| `dRN` | int 1..16 (4 distinct) | `+0x103` u8 | — | [C] |
| `A1mv` | always blank | `+0x104` bit 4 | — | [I] |
| `A2mv` | int, always 1, 591 blank | `+0x104` bit 5 | — | [C] |
| `SCmv` | always blank | `+0x104` bit 7 | — | [I] |
| `S1mv` | int, always 1, 598 blank | `+0x105` bit 0 | — | [C] |
| `S2mv` | int, always 1, 605 blank | `+0x105` bit 1 | — | [C] |
| `S3mv` | always blank | `+0x105` bit 2 | — | [I] |
| `S4mv` | always blank | `+0x105` bit 3 | — | [I] |
| `noGfxHitTest` | int, always 1, 598 blank | `+0x004` bit 0 | — | [I] |
| `htTop` | int -150..-60 (4 distinct), 598 blank | `+0x10E` s16 | — | [C] (width [I]) |
| `htLeft` | int -80..-20 (5 distinct), 598 blank | `+0x110` s16 | — | [C] (width [I]) |
| `htWidth` | int 40..145 (5 distinct), 598 blank | `+0x112` s16 | — | [C] (width [I]) |
| `htHeight` | int 70..160 (4 distinct), 598 blank | `+0x114` s16 | — | [C] (width [I]) |
| `restore` | int 0..2 (3 distinct) | `+0x130` u32 | [§ Inactive-room save](#inactive-room-save-plan-0040-phase-1) | [C] (width [I]) |
| `automapCel` | int, always 1258, 608 blank | `+0x118` u32 | — | [C] (width [I]) |
| `noMap` | int, always 1, 592 blank | `+0x004` bit 1 | — | [C] |
| `noOvly` | int, always 1, 587 blank | `+0x004` bit 2 | — | [C] |
| `isSel` | int, always 1, 79 blank | `+0x004` bit 3 | — | [C] |
| `alSel` | int, always 1, 592 blank | `+0x004` bit 4 | — | [C] |
| `noSel` | int, always 1, 580 blank | `+0x004` bit 5 | — | [C] |
| `shiftSel` | int, always 1, 604 blank | `+0x004` bit 6 | — | [C] |
| `corpseSel` | int, always 1, 215 blank | `+0x004` bit 7 | *plan 0046 readers:* `[C]` as a map: the corpse tests `0x00645510` and `0x00645680` (starts 15, 17, 21) refuse a monster without flag bit 7 ([skills/0010 § 3](../findings/skills/0010-necromancer.md#3-the-start-functions-15-17-18-19-20-21); fn:sub_00645510_MonCorpseTest@0x00645510, fn:sub_00645680_MonCorpseTestDead@0x00645680, fn:sub_004638A0_MonStats2FlagTest@0x004638A0); `[I]` so Raise Skeleton and the corpse explosions take only a `corpseSel` monster (the bit is this column by the layout); `[C]` as a bit test, flag 7 of `sub_004638A0_MonStats2FlagTest` in `sub_006455E0_CorpseTest` and `sub_00645590_CorpseTestF12` (starts 33, 34, do 69, 72, 75; do 137), `[I]` that flag 7 is this column (the layout) ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75), [skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_006455E0_CorpseTest@0x006455E0) | [C] |
| `isAtt` | int, always 1, 122 blank | `+0x005` bit 1 | — | [C] |
| `revive` | int, always 1, 220 blank | `+0x005` bit 0 | *plan 0046 readers:* `[C]` as a map: `0x005C3300` (start 21) refuses a monster without flag bit 8, up to its `0x0056E2F0` boundary (ADR-0021) ([skills/0010 § 3](../findings/skills/0010-necromancer.md#3-the-start-functions-15-17-18-19-20-21); fn:sub_005C3300_ReviveTargetTest@0x005C3300, fn:sub_005C3350_SkillSt21Revive@0x005C3350); `[I]` so Revive needs a `revive` monster (the bit is this column by the layout) | [C] |
| `critter` | int, always 1, 599 blank | `+0x005` bit 5 | — | [C] |
| `small` | int, always 1, 534 blank | `+0x005` bit 2 | *plan 0046 readers:* `[C]` damage function 14 reads it as flag 10 through `sub_004638A0_MonStats2FlagTest`: with `large` and Missiles `dParam1` it picks a monster's knockback chance (`dParam1` < 1: `dParam2` if small, else none; 1: small 2·`dParam2`, large none, else `dParam2`; ≥ 2: small 3·`dParam2`, large `dParam2`, else 2·`dParam2`) ([skills/0005 § 16](../findings/skills/0005-missile-do-19-36-damage.md#16-damage-5-13-14); fn:sub_005AD630_MissDmg14KnockBySize@0x005AD630); `[I]` skill do 75's second test (§ `large`) | [C] |
| `large` | int, always 1, 435 blank | `+0x005` bit 3 | *plan 0046 readers:* `[C]` damage function 14's flag 11 (the chance rule under `small`) ([skills/0005 § 16](../findings/skills/0005-missile-do-19-36-damage.md#16-damage-5-13-14); fn:sub_005AD630_MissDmg14KnockBySize@0x005AD630); `[C]` hit 47 (molten boulder) returns 2 (keep rolling) on a unit that is not a monster with this flag, and calls `MISSILE_BuildDamage` for one (or at the end of life), its boundary (ADR-0021); `[I]` the area hit after it, so the boulder explodes on `large` monsters only ([skills/0007 § 8](../findings/skills/0007-missile-hit-31-59.md#8-hit-47-56-and-53-area-hits-and-the-contagion); fn:sub_005AC550_MissHit47Boulder@0x005AC550); `[I]` skill do 75 (Grim Ward) creates `srvmissilec` for a corpse with this bit, else `srvmissileb` with `small`, else `srvmissilea`, after its boundary ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75); fn:sub_005D89B0_SkillDo75GrimWard@0x005D89B0) | [C] |
| `soft` | int, always 1, 206 blank | `+0x005` bit 4 | *plan 0046 readers:* `[C]` as a bit test, flag 12 through `sub_00621F60_MonStats2Flag12`, the last test of `sub_00645590_CorpseTestF12` (start 33, do 69, 75; do 137), `[I]` that flag 12 is this column (the layout) ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75), [skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_00645590_CorpseTestF12@0x00645590) | [C] |
| `inert` | int, always 1, 524 blank | `+0x006` bit 1 | — | [C] |
| `objCol` | int, always 1, 606 blank | `+0x006` bit 2 | — | [C] |
| `deadCol` | int, always 1, 596 blank | `+0x006` bit 3 | — | [C] |
| `unflatDead` | int, always 1, 600 blank | `+0x006` bit 4 | — | [C] |
| `Shadow` | int, always 1, 21 blank | `+0x005` bit 6 | — | [C] |
| `noUniqueShift` | int, always 1, 503 blank | `+0x005` bit 7 | — | [C] |
| `compositeDeath` | int, always 1, 467 blank | `+0x006` bit 0 | — | [C] |
| `localBlood` | int 1..2 (2 distinct), 458 blank | `+0x11C` u8 | — | [C] |
| `Bleed` | int 1..2 (2 distinct), 290 blank | `+0x11D` u8 | — | [C] |
| `Light` | int 3..15 (9 distinct), 509 blank | `+0x11E` u8 | — | [C] |
| `light-r` | int 0..255 (9 distinct) | `+0x11F` u8 | — | [C] |
| `light-g` | int 0..255 (10 distinct) | `+0x120` u8 | — | [C] |
| `light-b` | int 0..255 (7 distinct) | `+0x121` u8 | — | [C] |
| `Utrans` | int 2..255 (3 distinct), 594 blank | `+0x122` u8 | — | [C] |
| `Utrans(N)` | int 3..255 (3 distinct), 594 blank | `+0x123` u8 | — | [C] |
| `Utrans(H)` | int 4..255 (3 distinct), 594 blank | `+0x124` u8 | — | [C] (width [I]) |
| `Heart` | str, always 'xxx' | `+0x128` char[4] | — | [I] |
| `BodyPart` | str, always 'xxx' | `+0x12C` char[4] | — | [I] |
| `InfernoLen` | int 1..14 (4 distinct) | `+0x108` u8 | *plan 0046 readers:* `[I]` `sub_005CC3B0_InfernoEnd` (the end of skill do 95 and do 152, after its `CancelEvents` boundary) queues the next event at `frame + InfernoLen` (11 without a row) ([skills/0016 § 6](../findings/skills/0016-monster-8a.md#6-missiles-and-the-infernos-do-85-88-93-95-111-start-53); fn:sub_005CC3B0_InfernoEnd@0x005CC3B0) | [C] |
| `InfernoAnim` | int 6..11 (4 distinct), 584 blank | `+0x109` u8 | *plan 0046 readers:* `[I]` read by `sub_005CC440_InfernoAnim`, which skill do 95 (and do 126) call after a created missile ([skills/0016 § 6](../findings/skills/0016-monster-8a.md#6-missiles-and-the-infernos-do-85-88-93-95-111-start-53), [skills/0017 § 3](../findings/skills/0017-monster-8b.md#3-the-missile-casts-do-99-101-102-105-106-125-126-152); fn:sub_005CC440_InfernoAnim@0x005CC440) | [C] |
| `InfernoRollback` | int 6..15 (4 distinct), 591 blank | `+0x10A` u8 | — | [C] |
| `ResurrectMode` | str, 3 distinct, len ≤ 2 | `+0x10B` u8 index | monmode:code | [C] |
| `ResurrectSkill` | str, always 'SkeletonRaise', 578 blank | `+0x10C` s16 index | skills:skill | [C] (width [I]) |
| `EOL` | int, always 0 | — (not compiled) | — | — |

### Fields with no `.txt` column

| offset | size | observed | tag |
|---|---|---|---|
| `+0x002` | 2 | 0 in every record | unknown (high half of a u32 `Id`, or padding) |
| `+0x007` | 1 | 0 | unknown; `+0x004`..`+0x006` bits 21..23 are also 0 in every record |
| `+0x00F` | 1 | 0 | unknown (padding before `BaseW`, or the high byte of `MeleeRng`) |
| `+0x025` | 1 | Σ(count − 1) of the component lists | `[C]` computed (above) |
| `+0x0E6` | 2 | 0 | unknown (after the last token slot) |
| `+0x0EA` | 2 | 0 | unknown (the high half of the component-flag u32) |
| `+0x0F2`, `+0x106`, `+0x116`, `+0x125` | 2, 2, 2, 3 | 0 | unknown (padding after a bit group or before an aligned field) |

## Record layout (308 bytes)

`+0x000` `Id` u16 · `+0x004` flags (`noGfxHitTest` … `unflatDead`, bits 0..20) · `+0x008` `SizeX`, `SizeY`,
`spawnCol`, `Height`, `OverlayHeight`, `pixHeight`, `MeleeRng` (u8) · `+0x010` `BaseW` char[4] · `+0x014`
`HitClass` u8 · `+0x015` 16 × u8 component counts · `+0x025` u8 Σ(count − 1) · `+0x026` 16 × 12 u8 component
codes · `+0x0E8` `HD`..`S8` bits · `+0x0EC` `TotalPieces` · `+0x0F0` `mDT`..`mRN` bits · `+0x0F4` `dDT`..`dRN` u8 ·
`+0x104` `*mv` bits · `+0x108` `InfernoLen`, `InfernoAnim`, `InfernoRollback`, `ResurrectMode` (u8) · `+0x10C`
`ResurrectSkill` s16 · `+0x10E` `htTop`, `htLeft`, `htWidth`, `htHeight` (s16) · `+0x118` `automapCel` u32 ·
`+0x11C` `localBlood`, `Bleed`, `Light`, `light-r/g/b`, `Utrans` ×3 (u8) · `+0x128` `Heart`, `BodyPart`
char[4] · `+0x130` `restore` u32. Every byte is either a mapped field or listed above.

## What the monster pool reads

From [monsters/0001](../findings/monsters/0001-level-pool.md) (plan 0012), with this doc's layout:

- `[C]` `+0x015`..`+0x024` are the sixteen component counts that `sub_005BDB20_MonVariantRoll` draws over: set 0
  takes `Range(R, count)` for each component with count ≥ 2 (0 otherwise), and further sets reroll one or two
  components with count > 1. These are exactly the counts of the `HDv` … `S8v` lists (data, above), so a
  reimplementation can compute them from the `.txt`. (monsters/0001 § 4, fn:sub_005BDB20_MonVariantRoll@0x005BDB20,
  tbl:MonStats2.txt:HDv, run:2026-10-12-mon-pool)
- `[I]` `+0x025` is the exponent of the variant cap, `cap = (1 << (b & 31)) − nVariants`. By data `b` = Σ(count − 1)
  of the lists, so a class with no list longer than one code (461 records) gets **one** appearance set, a class
  with exactly one extra code (Σ = 1) at most two, and Σ ≥ 2 never binds the three sets. The finding saw 0, 16 and
  49 in the logged regions, all values of this column. (monsters/0001 § 4, fn:sub_005BDB20_MonVariantRoll@0x005BDB20)
- `[I]` `+0x0EC` is `TotalPieces`: `sub_00547BC0_MonRegionFindAdd` adds a class not yet in its level's region only
  while the region has fewer than 13 entries **and `TotalPieces` > 2** (218 of 609 records). By data `TotalPieces`
  equals the number of set component flags `HD`..`S8` in 562 of 609 rows, not all. (monsters/0001 § 6,
  fn:sub_00547BC0_MonRegionFindAdd@0x00547BC0, tbl:MonStats2.txt:TotalPieces)

## Footprint and collision columns (plan 0017 Phase 0)

`python3 -I tools/mon_survey.py collision workspace/merged/data/global/excel` (gate survey `mon_collision`). The
**pool classes** are the 362 classes of [MonStats § Spawn columns](MonStats.md#spawn-columns-plan-0014-phase-0):
every class named by a `mon`, `nmon` or `umon` slot of a level whose `MonDen` for that difficulty is non-zero. A
class reaches its row here through MonStats `MonStatsEx`. The 362 classes use 271 distinct rows. The command also
prints the normal (240), nightmare/hell (342) and `umon` (234) subsets. Counts are `[C]` by that command.

| Column | `.bin` | pool classes (362) | every MonStats class (734) | every MonStats2 row (609) |
|---|---|---|---|---|
| `SizeX` | `+0x008` u8 | 0: 1, 2: 238, 3: 123 | 0: 45, 1: 13, 2: 449, 3: 227 | 0: 45, 1: 12, 2: 356, 3: 196 |
| `SizeY` | `+0x009` u8 | equal to `SizeX` in every class | equal to `SizeX` in every class | equal to `SizeX` in every row |
| `spawnCol` | `+0x00A` u8 | 1: 3, 2: 3, blank 356 | 1: 10, 2: 4, 3: 6, blank 714 | 1: 10, 2: 4, 3: 6, blank (0) 589 |
| `objCol` | `+0x006` bit 2 | none | 3 | 3 |
| `deadCol` | `+0x006` bit 3 | none | 13 | 13 |
| `inert` | `+0x006` bit 1 | 3 | 86 | 85 |
| `unflatDead` | `+0x006` bit 4 | none | 9 | 9 |

- `[C]` **`spawnCol` on the pool classes:** 1 on `frogdemon1`, `frogdemon2`, `frogdemon3` (MonStats ordinals 247–249, `SizeX` 2),
  named in levels 77 and 78 (`frogdemon1..3`) and 93 (`frogdemon3`) by `mon`, `nmon` and `umon`. 2 on `crownest1`,
  `crownest2`, `crownest3` (ordinals 206–208, `SizeX` 3), named in levels 4, 6 (`mon`, `nmon`) and 43. No pool class has
  3. Outside the pool: 1 on `hellmeteor` (153) and on `tentacle1..3`, `tentaclehead1..3` (258–263); 2 on
  `crownest4`; 3 on `barricadedoor1/2`, `prisondoor`, `barricadetower`, `barricadewall1/2`.
- `[I]` **Which classes take the tile placement.** `MonSpawnTry` sends a `spawnCol` 1 class to
  `sub_005B2700_SpawnPosOnTile` unless its class is 258..263 or 153. The data shows that these excluded ordinals are
  exactly the other seven `spawnCol` 1 classes. So **only `frogdemon1..3` reach the tile placement**, all
  three are pool classes, and the plan 0014 logs had none of them (the branch is "not reached" in monsters/0002).
  The `spawnCol` → mask map (0: `0x3C01`, 1: `0x01C0`, 2: `0x3F11`, 3: 0) is the finding's. In the pool it gives
  `0x01C0` to the frog demons and `0x3F11` to the crow nests. (fn:sub_005B2A00_MonSpawnTry@0x005B2A00,
  fn:sub_005B2700_SpawnPosOnTile@0x005B2700, [monsters/0002](../findings/monsters/0002-room-population.md) § 6,
  tbl:MonStats2.txt:spawnCol)
- `[C]` `SizeX` and `SizeY` are equal in every row, so the data cannot tell which of `+0x008` and `+0x009` is which.
  The layout tag stays `[I]`. monsters/0002 reads the footprint at `+0x008` (s8) and calls it `SizeX`. No pool class has
  `SizeX` 1, and only `baaltaunt` (a `umon` class) has 0.
- `[C]` `objCol` is set on no pool class. monsters/0002's `objCol` branch for class 528 (`evilhut`) is outside the
  pool by data too.
- `[I]` **`SizeX` → footprint** ([drlg/0005 §§ 4–5](../findings/drlg/0005-collision.md#4-collisiontest-and-the-footprints)).
  The spawn test (`CollisionTest`, size = `SizeX` read at `+0x008` as a signed byte) checks one cell for 0 and 1, the
  plus (centre and four neighbours) for 2, and the 3×3 square for 3. The mark uses a *pattern* from
  `g_CollPatternBySize` {0: 0, 1: 1, 2: 1, 3: 2} (any larger size gives 1; an `npc` that is not `interact` takes 3 for
  1 and 4 for 2; wraiths take 5). Pattern 0 marks nothing (so `baaltaunt` neither marks nor blocks), 1 marks the plus
  with `0x100` and the centre with `0x1000`, 2 marks the 3×3 square with `0x100` and the plus with `0x1000`.
  Monsters therefore block a default-mask (`0x3C01`) spawn only through their `0x1000` cells. The grid bits are in
  [drlg/0005 § 6](../findings/drlg/0005-collision.md#6-the-u16-word-bit-by-bit). (fn:sub_0064D9B0_CollisionTest@0x0064D9B0,
  fn:PATH_PatternFromSize@0x00648580, data:g_CollPatternBySize@0x006EB3DC, fn:COLL_PatternMark@0x0064EA90,
  fn:UNIT_GetSizeX@0x00620510, tbl:MonStats2.txt:SizeX)
- `[I]` `UNIT_GetSizeY` reads a monster's `+0x009` (`SizeY`), but only object marks use a Y size, so no monster
  footprint depends on it. (fn:UNIT_GetSizeY@0x006205A0, [drlg/0005 § 5](../findings/drlg/0005-collision.md#5-unit-marks))
- `[I]` **`spawnCol` → spawn test mask:** 0 (and 4+) `0x3C01`, 1 `0x01C0`, 2 `0x3F11`, 3 `0`; per-bit readers in
  [drlg/0005 § 6](../findings/drlg/0005-collision.md#6-the-u16-word-bit-by-bit). (fn:sub_005B2A00_MonSpawnTry@0x005B2A00)

## Combat columns (plan 0037 Phase 0)

The columns that by their names say which attack modes a monster has and how it is hit, for `combat/formulas`.
Offsets are the [Columns](#columns) table's (`excel_bin.py diff`, `[C]`); the counts are
`python3 -I tools/combat_survey.py monstats2 workspace/merged/data/global/excel` (gate survey `combat`), `[C]` as data,
over the 609 rows. Meanings `[L]`.

| Column(s) | `.bin` field | Rows with the bit or value | Tag |
|---|---|---|---|
| `mDT` … `mRN` (mode available) | `+0x0F0` u16, bit *k* = [MonMode](MonMode.md) row *k* | `DT` 519, `NU` 585, `WL` 476, `GH` 403, `A1` 450, `A2` 217, `BL` 51, `SC` 41, `S1` 238, `S2` 60, `S3` 25, `S4` 15, `DD` 524, `KB` 377, `SQ` 384, `RN` 57 | [C] |
| `dDT` … `dRN` (directions per mode) | `+0x0F4 + k` u8 | 1..16 (§ Columns) | [C] |
| `A1mv` … `S4mv` (moves while in mode) | `+0x104` bits by mode index | § Columns | [C]/[I] |
| `MeleeRng` | `+0x00E` u8 | 0 ×537, 1 ×17, 2 ×20, 3 ×14, 4 ×15, 6 ×6 | [C] (width [I]) |
| `HitClass` | `+0x014` u8 | 3 ×566, 12 ×37, 1 ×6 | [C] |
| `BaseW` | `+0x010` 4-byte code | `hth` ×541, `1hs` ×26, `bow` ×16, `2hs` ×13, `1ht` ×6, `2ht` ×5, `fgt` ×1, `mgk` ×1 | [C] |
| `isAtt` | `+0x005` bit 1 | 487 | [C] |
| `small`, `large`, `soft` | `+0x005` bits 2, 3, 4 | 75, 174, 403 | [C] |

- `[C]` 380 rows have `mA1` or `mA2` and `MeleeRng` 0; so a 0 there is the common case for an attacking monster, not a
  "no melee" marker by data. (tbl:MonStats2.txt:MeleeRng, tbl:MonStats2.txt:mA1)
- `[C]` The MonStats side (which records with `A1`/`A2`/`S1` damage or an `El<e>Mode` have the mode bit here) is in
  [MonStats § Combat columns](MonStats.md#combat-columns-plan-0037-phase-0): no record with `S1` damage has `mS1`, and 27
  `El1` groups name a mode their row lacks. (tbl:MonStats2.txt:mS1)
- `[I]` `sub_0046C140_MonModeAllowed` reads the `+0xF0` mode bits of a class for the mod picks (`mA1`, `mWL`;
  [monsters/0003](../findings/monsters/0003-special-monsters.md)), so the bit order is the code's mode number.
  (fn:sub_0046C140_MonModeAllowed@0x0046C140)
- `[L]` By the names, `HitClass` is the class of the monster's hit (sound and graphics), `BaseW` its weapon class for
  the animation, `small`/`large`/`soft` the hit and knockback size, `isAtt` "can be attacked". `HitClass` stays with
  the animation phase (ADR-0014 phase 5); the combat code's reads are plan 0037 Phase 1.

## Inactive-room save (plan 0040 Phase 1)

- `[I]` `restore` (`+0x130`, read as a byte, the row reached through `MonStats.MonStatsEx`) is the last test of
  `InactiveMonsterSaveTest` when a room is released: 0 or a missing row → the monster is not saved; 2 → saved; 1 →
  the outcome of the earlier tests stands (the level's `SaveMonsters`, the dead-mode draw, `udead` states, ownership,
  unique or minion). (fn:sub_005431F0_InactiveMonsterSaveTest@0x005431F0, tbl:MonStats2.txt:restore,
  tbl:MonStats.txt:MonStatsEx; [drlg/0009 § 5](../findings/drlg/0009-room-lifecycle.md#5-the-inactive-records))
- `[C]` By data, through `MonStatsEx`, `restore` is 1 for 698 MonStats rows, 0 for 18 (`familiar`, `natalya`, the
  traps, `act2guard2`, `seventombs`, `izualghost` and the druid summons) and 2 for 18 (`barricadetower`, the eight
  `minionspawner*`, the four catapults, `act5pow`, the three `injuredbarb*`, `demonspawner`) (`.txt` read by
  script, tbl:MonStats2.txt:restore).

## Timing (plan 0050 Phase 0)

The mode flags and the timing columns, from the layout ([§ Record layout](#record-layout-308-bytes)); values from the
`.bin` over the 609 records (`python3 -I tools/anim_survey.py monsters workspace/merged`; survey keys `mon_*`):

| Column | `.bin` field | Observed | Meaning | Tag |
|---|---|---|---|---|
| `BaseW` | `+0x010` 4-byte code | `hth` 541, `1hs` 26, `bow` 16, `2hs` 13, `1ht` 6, `2ht` 5, `fgt` 1, `mgk` 1 | the weapon class: the third part of the `animdata.d2` record name | [C] layout; the join `[C]`, the game's use `[L]` |
| `HitClass` | `+0x014` u8 | 1 ×6, 3 ×566, 12 ×37 | read as [HitClass](HitClass.md) rows: `hth`, `1hsl`, `claw` | [C] layout; `[L]` |
| `mDT` … `mRN` | `+0x0F0` u16, bit *k* = [MonMode](MonMode.md) row *k* | set in `DT` 519, `NU` 585, `WL` 476, `GH` 403, `A1` 450, `A2` 217, `BL` 51, `SC` 41, `S1` 238, `S2` 60, `S3` 25, `S4` 15, `DD` 524, `KB` 377, `SQ` 384, `RN` 57 records | the class has mode *k* | [C] layout; `[C]` in the 603 records a MonStats row names, every set bit outside `SQ` names an existing `animdata.d2` record (below); the other 6 (`diabloclone` and the five `uber*` rows) have no MonStats `Code` to build a name from and are not checked |
| `dDT` … `dRN` | `+0x0F4 + k` u8 | 1, 4, 8 or 16 in every record and mode (8 the most common: 498..562 per mode) | directions of mode *k* | [C] layout; `[L]` |
| `A1mv`, `A2mv`, `SCmv`, `S1mv`, `S2mv`, `S3mv`, `S4mv` | `+0x104` bits by mode index (`A1mv` bit 4 … `S4mv` bit 11) | set in 0, 18, 0, 11, 4, 0, 0 records | the monster moves while in that mode | [C]/[I] layout ([§ Columns](#columns)); `[L]` |
| `InfernoLen` | `+0x108` u8 | 1 ×601, 14 ×6, 6, 7 | frames to the next inferno event | [C] layout; `[I]` `sub_005CC3B0_InfernoEnd` ([§ Columns](#columns)) |
| `InfernoAnim` | `+0x109` u8 | 6..11 in 25 records, blank 0 | the inferno's animation frame test | [C] layout; `[I]` `sub_005CC440_InfernoAnim` ([§ Columns](#columns)) |
| `InfernoRollback` | `+0x10A` u8 | 6..15 in 18 records, blank 0 | the frame an inferno rolls back to (name) | [C] layout; `[L]` (no reader read) |
| `ResurrectMode` | `+0x10B` u8, `monmode` row | `NU` 568, `xx` 31, `S1` 10 | the mode of a resurrected monster | [C] layout; `[L]` |
| `ResurrectSkill` | `+0x10C` s16, `skills` row | 158 (`SkeletonRaise`) in 31, −1 otherwise | the skill a resurrection plays | [C] layout; `[L]` |

- `[C]` **Every flagged mode has animation data.** For the 734 MonStats rows, each set `m<mode>` bit outside `SQ`
  (5 109 in all) names an `animdata.d2` record `<MonStats Code><MonMode token><BaseW>` (5 057) or, failing that,
  `<…>HTH` (52, the death modes of the `GM`, `FE` and `FK` classes); `mon_miss=0`
  ([MonMode § Timing](MonMode.md#timing-plan-0050-phase-0)). The 31 `ResurrectMode` `xx` rows are the 31 with
  `ResurrectSkill` `SkeletonRaise`, whose sequence is `seq_skeletonraise` ([MonSeq](MonSeq.md)) by the name.
- `[L]` Whether `d<mode>` matches the COF's direction count, and what the `*mv` bits do to the movement step, is plan
  0050 Phases 1.1 and 1.3.

## Interpretation notes

- `[C]` `HD` … `S8` (component present) and the `*v` lists are not the same thing by data: `HD` is set in 146 rows
  and `HDv` non-blank in 144. Which one the client uses to draw is graphics code, not read.
- `[L]` By the names: `m*` = the monster has animation mode *, `d*` = that mode's direction count, `*mv` = the
  monster can move in that mode, `Utrans*` = palette shift per difficulty, `ht*` = hit box, `Inferno*`,
  `Resurrect*` = special animation and skill data. No code anchor (graphics and client side).

## Open questions

- `[L]` Meaning of every column outside § What the monster pool reads; owners are graphics and `monsters/spawn`.
- `[L]` The integer widths marked "width `[I]`" (`MeleeRng`, `TotalPieces`, `restore`, `automapCel`, the `ht*`
  quartet): only a reader of the record fixes them.
