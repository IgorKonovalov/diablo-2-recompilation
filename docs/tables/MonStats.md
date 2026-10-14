# MonStats (`data/global/excel/monstats.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 734 (735 data rows − 1 `Expansion` marker at row 410)   **Record:** 424 B
> **sha256:** `.txt` `a15e1cb876bd9af1e8f54199c9619226cf4835c45c799aed2d432901487ecb7c`, `.bin` `b8c6b72df4c7825a43da33d3e533f2e7e14b268b01c6236e82ab2d800fc75584`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending (pool, level, spawn and stat columns surveyed)

## Purpose

One row per monster class: links to its family (`BaseId`, `NextInClass`), graphics and AI records,
minions, group sizes, per-difficulty level, hit points, damage, resistances, skills and the four
treasure classes per difficulty. Read by `monsters/*` and by drops (`items/tc`).

## Row identity

- `[C]` Key column `Id`. 733 distinct values over 734 rows: **`cr_lancer8` appears twice** (rows 617
  and 723, both `hcIdx` equal to their row).
- `[C]` `+0x000` of each record is the **ordinal of its `Id` among distinct `Id`s** (first occurrence
  wins): equal to the row for rows 0..722, 617 for the second `cr_lancer8`, and row − 1 for rows
  724..733. `hcIdx` (the `.txt` row number) is not compiled.
- `[C]` Every reference to a monster (here `BaseId`, `NextInClass`, `spawn`, `minion1/2`; in
  `levels.bin` the `mon*`, `nmon*`, `umon*`, `cmon*` columns) stores that ordinal. In `levels.bin`,
  *Act 5 - Pandemonium 3* names `overseer6` (row 724) and stores 723. The only references past row 722
  are those three cells.
- `[C]` The `Expansion` marker after data row 409 takes no record.

## Columns

`[C]` layout tags are by data behaviour: `python3 -I tools/excel_bin.py diff <excel-dir> monstats` decodes every record and compares it with every mapped cell (blank cells and encoding rules as in [excel-bin.md](../formats/excel-bin.md#cell-encoding-rules)). A field is tagged `[C]` when the column's values pin its offset (a probe over every record finds no other offset that fits), `[I]` when the column is constant or identical to a sibling column, so its position comes from the neighbouring fields or the stride of its group. Widths are `[C]` with the same proviso; signedness is `[I]` (`s` where the column holds negative values). **Meaning:** no column semantics are claimed here; they come from reverser findings. The 29 boolean columns at `+0x00C..+0x00F` are single bits; their bit
positions are pinned by the data except where noted.

| Column | Observed type / range | `.bin` field | References | Layout tag |
|---|---|---|---|---|
| `Id` | str, 733 distinct, len ≤ 17 | `+0x000` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `hcIdx` | int 0..733 (734 distinct) | — (editor row number; +0x000 is the distinct-Id ordinal instead (differs after the duplicate Id cr_lancer8)) | — | — |
| `BaseId` | str, 264 distinct, len ≤ 17 | `+0x002` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `NextInClass` | str, 442 distinct, len ≤ 16, 291 blank | `+0x004` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `TransLvl` | int 0..7 (8 distinct) | `+0x04D` u8 | — | [C] |
| `NameStr` | str, 454 distinct, len ≤ 26, 6 blank | `+0x006` u16 string index | string tables | [C] |
| `MonStatsEx` | str, 603 distinct, len ≤ 17 | `+0x018` u16 index | `monstats2:Id` | [C] |
| `MonProp` | str, 12 distinct, len ≤ 14, 716 blank | `+0x01A` u16 index | `monprop:Id` | [C] |
| `MonType` | str, 55 distinct, len ≤ 13, 128 blank | `+0x01C` u16 index | `montype:type` | [C] |
| `AI` | str, 146 distinct, len ≤ 15 | `+0x01E` u16 index | `monai:AI` | [C] |
| `DescStr` | str, 24 distinct, len ≤ 25, 631 blank | `+0x008` u16 string index | string tables | [C] |
| `Code` | str, 210 distinct, len ≤ 2 | `+0x010` char[4] code | — | [C] |
| `enabled` | int, always 1, 31 blank | `+0x00F` bit 1 | — | [C] |
| `rangedtype` | int, always 1, 594 blank | `+0x00F` bit 4 | — | [C] |
| `placespawn` | int, always 1, 730 blank | `+0x00E` bit 7 | — | [C] |
| `spawn` | str, 47 distinct, len ≤ 12, 682 blank | `+0x020` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `spawnx` | int -2..8 (4 distinct), 682 blank | `+0x022` s8 | — | [C] |
| `spawny` | int -2..5 (5 distinct), 682 blank | `+0x023` s8 | — | [C] |
| `spawnmode` | str, 2 distinct, len ≤ 2, 682 blank | `+0x024` u8 index | `monmode:code` | [C] |
| `minion1` | str, 57 distinct, len ≤ 11, 655 blank | `+0x026` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `minion2` | str, 8 distinct, len ≤ 11, 725 blank | `+0x028` u16 index (distinct-key ordinal) | `monstats:Id` | [C] |
| `SetBoss` | int, always 1, 671 blank | `+0x00C` bit 4 | — | [C] |
| `BossXfer` | int, always 1, 693 blank | `+0x00C` bit 5 | — | [C] |
| `PartyMin` | int 1..5 (5 distinct), 656 blank | `+0x02C` u8 | — | [C] |
| `PartyMax` | int 1..9 (9 distinct), 656 blank | `+0x02D` u8 | — | [C] |
| `MinGrp` | int 0..7 (8 distinct), 4 blank | `+0x02F` u8 | — | [C] |
| `MaxGrp` | int 0..10 (10 distinct), 4 blank | `+0x030` u8 | — | [C] |
| `sparsePopulate` | int, always 40, 733 blank | `+0x031` u8 | — | [C] |
| `Velocity` | int 0..15 (16 distinct), 4 blank | `+0x032` u16 | — | [C] |
| `Run` | int 0..20 (18 distinct), 4 blank | `+0x034` u16 | — | [C] |
| `Rarity` | int 0..2 (3 distinct), 4 blank | `+0x02E` u8 | — | [C] |
| `Level` | int 0..110 (49 distinct), 150 blank | `+0x0AA` u16 | — | [C] |
| `Level(N)` | int 1..110 (41 distinct), 150 blank | `+0x0AC` u16 | — | [C] |
| `Level(H)` | int 1..110 (32 distinct), 150 blank | `+0x0AE` u16 | — | [C] |
| `MonSound` | str, 136 distinct, len ≤ 15, 78 blank | `+0x014` u16 index | `monsounds:Id` | [C] |
| `UMonSound` | str, 137 distinct, len ≤ 15, 78 blank | `+0x016` u16 index | `monsounds:Id` | [C] |
| `threat` | int 1..14 (12 distinct), 144 blank | `+0x04E` u8 | — | [C] |
| `aidel` | int 1..15 (3 distinct), 18 blank | `+0x04F` u8 | — | [C] |
| `aidel(N)` | int 1..15 (9 distinct), 18 blank | `+0x050` u8 | — | [C] |
| `aidel(H)` | int 1..15 (10 distinct), 18 blank | `+0x051` u8 | — | [C] |
| `aidist` | always blank | `+0x052` u8 | — | [I] |
| `aidist(N)` | int, always 40, 732 blank | `+0x053` u8 | — | [C] |
| `aidist(H)` | int, always 46, 732 blank | `+0x054` u8 | — | [C] |
| `aip1` | int 0..250 (45 distinct), 160 blank | `+0x056` u16 | — | [C] |
| `aip1(N)` | int 0..250 (50 distinct), 160 blank | `+0x058` u16 | — | [C] |
| `aip1(H)` | int 0..250 (53 distinct), 160 blank | `+0x05A` u16 | — | [C] |
| `aip2` | int 0..150 (38 distinct), 172 blank | `+0x05C` u16 | — | [C] |
| `aip2(N)` | int 0..125 (46 distinct), 172 blank | `+0x05E` u16 | — | [C] |
| `aip2(H)` | int 0..99 (47 distinct), 172 blank | `+0x060` u16 | — | [C] |
| `aip3` | int 0..500 (48 distinct), 206 blank | `+0x062` u16 | — | [C] |
| `aip3(N)` | int 0..350 (56 distinct), 206 blank | `+0x064` u16 | — | [C] |
| `aip3(H)` | int 0..200 (52 distinct), 206 blank | `+0x066` u16 | — | [C] |
| `aip4` | int 0..200 (38 distinct), 269 blank | `+0x068` u16 | — | [C] |
| `aip4(N)` | int 0..200 (48 distinct), 269 blank | `+0x06A` u16 | — | [C] |
| `aip4(H)` | int 0..200 (48 distinct), 269 blank | `+0x06C` u16 | — | [C] |
| `aip5` | int 0..150 (34 distinct), 394 blank | `+0x06E` u16 | — | [C] |
| `aip5(N)` | int 0..125 (36 distinct), 394 blank | `+0x070` u16 | — | [C] |
| `aip5(H)` | int 0..120 (36 distinct), 394 blank | `+0x072` u16 | — | [C] |
| `aip6` | int 0..100 (20 distinct), 589 blank | `+0x074` u16 | — | [C] |
| `aip6(N)` | int 0..100 (27 distinct), 589 blank | `+0x076` u16 | — | [C] |
| `aip6(H)` | int 0..100 (25 distinct), 589 blank | `+0x078` u16 | — | [C] |
| `aip7` | int 3..100 (16 distinct), 628 blank | `+0x07A` u16 | — | [C] |
| `aip7(N)` | int 3..100 (18 distinct), 628 blank | `+0x07C` u16 | — | [C] |
| `aip7(H)` | int 4..100 (20 distinct), 628 blank | `+0x07E` u16 | — | [C] |
| `aip8` | int 5..279 (10 distinct), 660 blank | `+0x080` u16 | — | [C] |
| `aip8(N)` | int 5..66 (10 distinct), 653 blank | `+0x082` u16 | — | [C] |
| `aip8(H)` | int 5..80 (13 distinct), 653 blank | `+0x084` u16 | — | [C] |
| `MissA1` | str, 50 distinct, len ≤ 22, 639 blank | `+0x03A` u16 index | `missiles:Missile` | [C] |
| `MissA2` | str, 26 distinct, len ≤ 18, 687 blank | `+0x03C` u16 index | `missiles:Missile` | [C] |
| `MissS1` | str, 5 distinct, len ≤ 22, 726 blank | `+0x03E` u16 index | `missiles:Missile` | [C] |
| `MissS2` | str, 2 distinct, len ≤ 23, 732 blank | `+0x040` u16 index | `missiles:Missile` | [C] |
| `MissS3` | always blank | `+0x042` u16 index | `missiles:Missile` | [I] |
| `MissS4` | always blank | `+0x044` u16 index | `missiles:Missile` | [I] |
| `MissC` | str, 2 distinct, len ≤ 23, 726 blank | `+0x046` u16 index | `missiles:Missile` | [C] |
| `MissSQ` | str, always 'raven2', 733 blank | `+0x048` u16 index | `missiles:Missile` | [C] |
| `Align` | int 1..2 (2 distinct), 619 blank | `+0x04C` u8 | — | [C] |
| `isSpawn` | int, always 1, 164 blank | `+0x00C` bit 0 | — | [C] |
| `isMelee` | int, always 1, 304 blank | `+0x00C` bit 1 | — | [C] |
| `npc` | int, always 1, 675 blank | `+0x00D` bit 0 | — | [C] |
| `interact` | int, always 1, 687 blank | `+0x00D` bit 1 | — | [C] |
| `inventory` | int, always 1, 704 blank | `+0x00F` bit 0 | — | [C] |
| `inTown` | int, always 1, 625 blank | `+0x00D` bit 2 | — | [C] |
| `lUndead` | int, always 1, 636 blank | `+0x00D` bit 3 | — | [C] |
| `hUndead` | int, always 1, 709 blank | `+0x00D` bit 4 | — | [C] |
| `demon` | int, always 1, 549 blank | `+0x00D` bit 5 | — | [C] |
| `flying` | int, always 1, 664 blank | `+0x00D` bit 6 | — | [C] |
| `opendoors` | int, always 1, 412 blank | `+0x00C` bit 3 | — | [C] |
| `boss` | int, always 1, 709 blank | `+0x00C` bit 6 | — | [C] |
| `primeevil` | int, always 1, 722 blank | `+0x00C` bit 7 | — | [C] |
| `killable` | int, always 1, 100 blank | `+0x00D` bit 7 | — | [C] |
| `switchai` | int, always 1, 149 blank | `+0x00E` bit 0 | — | [C] |
| `noAura` | int, always 1, 729 blank | `+0x00F` bit 3 | — | [C] |
| `nomultishot` | int, always 1, 723 blank | `+0x00E` bit 1 | — | [C] |
| `neverCount` | int, always 1, 657 blank | `+0x00E` bit 2 | — | [C] |
| `petIgnore` | int, always 1, 722 blank | `+0x00E` bit 3 | — | [C] |
| `deathDmg` | int, always 1, 720 blank | `+0x00E` bit 4 | — | [C] |
| `genericSpawn` | int, always 1, 679 blank | `+0x00E` bit 5 | — | [C] |
| `zoo` | int, always 1, 582 blank | `+0x00E` bit 6 | — | [C] |
| `SendSkills` | int, always 2, 732 blank | `+0x16C` u32 | — | [C] |
| `Skill1` | str, 76 distinct, len ≤ 26, 349 blank | `+0x170` u16 index | `skills:skill` | [C] |
| `Sk1mode` | str, 46 distinct, len ≤ 21, 349 blank | `+0x180` u8 index; `+0x188` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk1lvl` | int 0..15 (13 distinct), 349 blank | `+0x198` u8 | — | [C] |
| `Skill2` | str, 38 distinct, len ≤ 19, 592 blank | `+0x172` u16 index | `skills:skill` | [C] |
| `Sk2mode` | str, 17 distinct, len ≤ 20, 592 blank | `+0x181` u8 index; `+0x18A` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk2lvl` | int 0..20 (11 distinct), 592 blank | `+0x199` u8 | — | [C] |
| `Skill3` | str, 20 distinct, len ≤ 24, 630 blank | `+0x174` u16 index | `skills:skill` | [C] |
| `Sk3mode` | str, 11 distinct, len ≤ 15, 630 blank | `+0x182` u8 index; `+0x18C` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk3lvl` | int 1..7 (6 distinct), 630 blank | `+0x19A` u8 | — | [C] |
| `Skill4` | str, 16 distinct, len ≤ 19, 660 blank | `+0x176` u16 index | `skills:skill` | [C] |
| `Sk4mode` | str, 11 distinct, len ≤ 19, 660 blank | `+0x183` u8 index; `+0x18E` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk4lvl` | int 1..20 (7 distinct), 660 blank | `+0x19B` u8 | — | [C] |
| `Skill5` | str, 11 distinct, len ≤ 19, 689 blank | `+0x178` u16 index | `skills:skill` | [C] |
| `Sk5mode` | str, 8 distinct, len ≤ 18, 689 blank | `+0x184` u8 index; `+0x190` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk5lvl` | int 1..5 (5 distinct), 689 blank | `+0x19C` u8 | — | [C] |
| `Skill6` | str, 5 distinct, len ≤ 16, 720 blank | `+0x17A` u16 index | `skills:skill` | [C] |
| `Sk6mode` | str, 4 distinct, len ≤ 15, 720 blank | `+0x185` u8 index; `+0x192` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk6lvl` | int 1..8 (4 distinct), 720 blank | `+0x19D` u8 | — | [C] |
| `Skill7` | str, 3 distinct, len ≤ 10, 726 blank | `+0x17C` u16 index | `skills:skill` | [C] |
| `Sk7mode` | str, 2 distinct, len ≤ 2, 726 blank | `+0x186` u8 index; `+0x194` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk7lvl` | int 1..3 (2 distinct), 726 blank | `+0x19E` u8 | — | [C] |
| `Skill8` | str, 2 distinct, len ≤ 14, 731 blank | `+0x17E` u16 index | `skills:skill` | [C] |
| `Sk8mode` | str, 2 distinct, len ≤ 2, 731 blank | `+0x187` u8 index; `+0x196` s16 index (distinct-key ordinal) | `monmode:code`, `monseq:sequence` | [C] |
| `Sk8lvl` | int 5..30 (2 distinct), 731 blank | `+0x19F` u8 | — | [C] |
| `Drain` | int 15..100 (2 distinct), 257 blank | `+0x0A0` u8 | — | [C] |
| `Drain(N)` | int 15..100 (7 distinct), 259 blank | `+0x0A1` u8 | — | [C] |
| `Drain(H)` | int 15..100 (8 distinct), 260 blank | `+0x0A2` u8 | — | [C] |
| `coldeffect` | int -50..0 (8 distinct), 146 blank | `+0x168` s8 | — | [C] |
| `coldeffect(N)` | int -50..0 (10 distinct), 155 blank | `+0x169` s8 | — | [C] |
| `coldeffect(H)` | int -50..33 (11 distinct), 158 blank | `+0x16A` s8 | — | [C] |
| `ResDm` | int 20..90 (9 distinct), 674 blank | `+0x144` s16 | — | [C] |
| `ResMa` | int 20..90 (7 distinct), 684 blank | `+0x14A` s16 | — | [C] |
| `ResFi` | int -50..100 (16 distinct), 612 blank | `+0x150` s16 | — | [C] |
| `ResLi` | int 15..90 (12 distinct), 630 blank | `+0x156` s16 | — | [C] |
| `ResCo` | int 15..90 (13 distinct), 603 blank | `+0x15C` s16 | — | [C] |
| `ResPo` | int -50..1000 (19 distinct), 543 blank | `+0x162` s16 | — | [C] |
| `ResDm(N)` | int 10..100 (16 distinct), 660 blank | `+0x146` s16 | — | [C] |
| `ResMa(N)` | int 15..90 (13 distinct), 666 blank | `+0x14C` s16 | — | [C] |
| `ResFi(N)` | int -50..100 (17 distinct), 585 blank | `+0x152` s16 | — | [C] |
| `ResLi(N)` | int 15..100 (14 distinct), 592 blank | `+0x158` s16 | — | [C] |
| `ResCo(N)` | int 15..100 (14 distinct), 568 blank | `+0x15E` s16 | — | [C] |
| `ResPo(N)` | int -50..1000 (21 distinct), 516 blank | `+0x164` s16 | — | [C] |
| `ResDm(H)` | int 10..100 (18 distinct), 262 blank | `+0x148` s16 | — | [C] |
| `ResMa(H)` | int 10..145 (12 distinct), 594 blank | `+0x14E` s16 | — | [C] |
| `ResFi(H)` | int -50..145 (26 distinct), 362 blank | `+0x154` s16 | — | [C] |
| `ResLi(H)` | int 15..145 (20 distinct), 370 blank | `+0x15A` s16 | — | [C] |
| `ResCo(H)` | int 15..1000 (32 distinct), 337 blank | `+0x160` s16 | — | [C] |
| `ResPo(H)` | int -50..1000 (27 distinct), 342 blank | `+0x166` s16 | — | [C] |
| `DamageRegen` | int 0..15 (9 distinct), 19 blank | `+0x1A0` u32 | — | [C] |
| `SkillDamage` | str, 4 distinct, len ≤ 18, 730 blank | `+0x0A8` u16 index | `skills:skill` | [C] |
| `noRatio` | int, always 1, 703 blank | `+0x00C` bit 2 | — | [C] |
| `NoShldBlock` | int, always 1, 716 blank | `+0x00F` bit 2 | — | [C] |
| `ToBlock` | int 0..75 (50 distinct), 205 blank | `+0x0A3` u8 | — | [C] |
| `ToBlock(N)` | int 3..75 (49 distinct), 200 blank | `+0x0A4` u8 | — | [C] |
| `ToBlock(H)` | int 3..75 (50 distinct), 200 blank | `+0x0A5` u8 | — | [C] |
| `Crit` | int, always 5, 184 blank | `+0x0A6` u8 | — | [C] |
| `minHP` | int 10..9981 (149 distinct), 141 blank | `+0x0B0` u16 | — | [C] |
| `maxHP` | int 10..9981 (150 distinct), 140 blank | `+0x0B6` u16 | — | [C] |
| `AC` | int 2..251 (50 distinct), 140 blank | `+0x0BC` u16 | — | [C] |
| `Exp` | int 1..6460 (145 distinct), 198 blank | `+0x0D4` u16 | — | [C] |
| `A1MinD` | int 0..295 (83 distinct), 267 blank | `+0x0DA` u16 | — | [C] |
| `A1MaxD` | int 0..442 (99 distinct), 270 blank | `+0x0E0` u16 | — | [C] |
| `A1TH` | int 5..3001 (51 distinct), 270 blank | `+0x0C2` u16 | — | [C] |
| `A2MinD` | int 0..178 (64 distinct), 566 blank | `+0x0E6` u16 | — | [C] |
| `A2MaxD` | int 0..271 (59 distinct), 566 blank | `+0x0EC` u16 | — | [C] |
| `A2TH` | int 5..376 (36 distinct), 566 blank | `+0x0C8` u16 | — | [C] |
| `S1MinD` | int 1..100 (4 distinct), 705 blank | `+0x0F2` u16 | — | [C] |
| `S1MaxD` | int 2..130 (4 distinct), 705 blank | `+0x0F8` u16 | — | [C] |
| `S1TH` | int 95..250 (5 distinct), 705 blank | `+0x0CE` u16 | — | [C] |
| `MinHP(N)` | int 10..6427 (73 distinct), 142 blank | `+0x0B2` u16 | — | [C] |
| `MaxHP(N)` | int 10..6427 (79 distinct), 142 blank | `+0x0B8` u16 | — | [C] |
| `AC(N)` | int 5..245 (42 distinct), 141 blank | `+0x0BE` u16 | — | [C] |
| `Exp(N)` | int 5..6460 (52 distinct), 198 blank | `+0x0D6` u16 | — | [C] |
| `A1MinD(N)` | int 0..180 (30 distinct), 263 blank | `+0x0DC` u16 | — | [C] |
| `A1MaxD(N)` | int 0..260 (39 distinct), 263 blank | `+0x0E2` u16 | — | [C] |
| `A1TH(N)` | int 4..5000 (39 distinct), 270 blank | `+0x0C4` u16 | — | [C] |
| `A2MinD(N)` | int 0..190 (24 distinct), 572 blank | `+0x0E8` u16 | — | [C] |
| `A2MaxD(N)` | int 0..320 (29 distinct), 572 blank | `+0x0EE` u16 | — | [C] |
| `A2TH(N)` | int 4..300 (26 distinct), 572 blank | `+0x0CA` u16 | — | [C] |
| `S1MinD(N)` | int 40..120 (5 distinct), 705 blank | `+0x0F4` u16 | — | [I] |
| `S1MaxD(N)` | int 50..180 (7 distinct), 705 blank | `+0x0FA` u16 | — | [I] |
| `S1TH(N)` | int 95..250 (5 distinct), 705 blank | `+0x0D0` u16 | — | [I] |
| `MinHP(H)` | int 10..6500 (76 distinct), 141 blank | `+0x0B4` u16 | — | [C] |
| `MaxHP(H)` | int 10..6600 (84 distinct), 141 blank | `+0x0BA` u16 | — | [C] |
| `AC(H)` | int 5..334 (48 distinct), 140 blank | `+0x0C0` u16 | — | [C] |
| `Exp(H)` | int 5..6460 (59 distinct), 198 blank | `+0x0D8` u16 | — | [C] |
| `A1MinD(H)` | int 0..400 (39 distinct), 263 blank | `+0x0DE` u16 | — | [C] |
| `A1MaxD(H)` | int 0..440 (41 distinct), 263 blank | `+0x0E4` u16 | — | [C] |
| `A1TH(H)` | int 6..5000 (42 distinct), 270 blank | `+0x0C6` u16 | — | [C] |
| `A2MinD(H)` | int 0..190 (26 distinct), 572 blank | `+0x0EA` u16 | — | [C] |
| `A2MaxD(H)` | int 0..320 (30 distinct), 572 blank | `+0x0F0` u16 | — | [C] |
| `A2TH(H)` | int 6..350 (25 distinct), 572 blank | `+0x0CC` u16 | — | [C] |
| `S1MinD(H)` | int 40..120 (5 distinct), 705 blank | `+0x0F6` u16 | — | [I] |
| `S1MaxD(H)` | int 50..180 (7 distinct), 705 blank | `+0x0FC` u16 | — | [I] |
| `S1TH(H)` | int 95..250 (5 distinct), 705 blank | `+0x0D2` u16 | — | [I] |
| `El1Mode` | str, 3 distinct, len ≤ 2, 439 blank | `+0x0FE` u8 index | `monmode:code` | [C] |
| `El1Type` | str, 10 distinct, len ≤ 4, 439 blank | `+0x101` u8 index | `elemtypes:Code` | [C] |
| `El1Pct` | int 0..100 (20 distinct), 514 blank | `+0x104` u8 | — | [C] |
| `El1MinD` | int 5..500 (48 distinct), 522 blank | `+0x10E` u16 | — | [C] |
| `El1MaxD` | int 10..571 (53 distinct), 522 blank | `+0x120` u16 | — | [C] |
| `El1Dur` | int 7..3000 (18 distinct), 635 blank | `+0x132` u16 | — | [C] |
| `El1Pct(N)` | int 5..100 (21 distinct), 439 blank | `+0x105` u8 | — | [C] |
| `El1MinD(N)` | int 1..500 (22 distinct), 447 blank | `+0x110` u16 | — | [C] |
| `El1MaxD(N)` | int 10..600 (30 distinct), 447 blank | `+0x122` u16 | — | [C] |
| `El1Dur(N)` | int 7..3000 (21 distinct), 591 blank | `+0x134` u16 | — | [C] |
| `El1Pct(H)` | int 5..100 (22 distinct), 439 blank | `+0x106` u8 | — | [C] |
| `El1MinD(H)` | int 1..500 (25 distinct), 447 blank | `+0x112` u16 | — | [C] |
| `El1MaxD(H)` | int 15..600 (32 distinct), 447 blank | `+0x124` u16 | — | [C] |
| `El1Dur(H)` | int 7..3000 (21 distinct), 591 blank | `+0x136` u16 | — | [C] |
| `El2Mode` | str, 3 distinct, len ≤ 2, 694 blank | `+0x0FF` u8 index | `monmode:code` | [C] |
| `El2Type` | str, 6 distinct, len ≤ 4, 694 blank | `+0x102` u8 index | `elemtypes:Code` | [C] |
| `El2Pct` | int 0..100 (6 distinct), 707 blank | `+0x107` u8 | — | [C] |
| `El2MinD` | int 5..50 (5 distinct), 711 blank | `+0x114` u16 | — | [C] |
| `El2MaxD` | int 25..120 (7 distinct), 711 blank | `+0x126` u16 | — | [C] |
| `El2Dur` | int 25..75 (2 distinct), 729 blank | `+0x138` u16 | — | [C] |
| `El2Pct(N)` | int 10..100 (7 distinct), 694 blank | `+0x108` u8 | — | [C] |
| `El2MinD(N)` | int 5..100 (7 distinct), 694 blank | `+0x116` u16 | — | [C] |
| `El2MaxD(N)` | int 10..160 (10 distinct), 694 blank | `+0x128` u16 | — | [C] |
| `El2Dur(N)` | int 50..500 (4 distinct), 724 blank | `+0x13A` u16 | — | [C] |
| `El2Pct(H)` | int 10..100 (8 distinct), 694 blank | `+0x109` u8 | — | [C] |
| `El2MinD(H)` | int 5..120 (8 distinct), 694 blank | `+0x118` u16 | — | [C] |
| `El2MaxD(H)` | int 15..190 (11 distinct), 694 blank | `+0x12A` u16 | — | [C] |
| `El2Dur(H)` | int 50..1000 (5 distinct), 724 blank | `+0x13C` u16 | — | [C] |
| `El3Mode` | always blank | `+0x100` u8 index | `monmode:code` | [I] |
| `El3Type` | always blank | `+0x103` u8 index | `elemtypes:Code` | [I] |
| `El3Pct` | always blank | `+0x10A` u8 | — | [I] |
| `El3MinD` | always blank | `+0x11A` u16 | — | [I] |
| `El3MaxD` | always blank | `+0x12C` u16 | — | [I] |
| `El3Dur` | always blank | `+0x13E` u16 | — | [I] |
| `El3Pct(N)` | always blank | `+0x10B` u8 | — | [I] |
| `El3MinD(N)` | always blank | `+0x11C` u16 | — | [I] |
| `El3MaxD(N)` | always blank | `+0x12E` u16 | — | [I] |
| `El3Dur(N)` | always blank | `+0x140` u16 | — | [I] |
| `El3Pct(H)` | always blank | `+0x10C` u8 | — | [I] |
| `El3MinD(H)` | always blank | `+0x11E` u16 | — | [I] |
| `El3MaxD(H)` | always blank | `+0x130` u16 | — | [I] |
| `El3Dur(H)` | always blank | `+0x142` u16 | — | [I] |
| `TreasureClass1` | str, 67 distinct, len ≤ 15, 250 blank | `+0x086` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass2` | str, 31 distinct, len ≤ 15, 250 blank | `+0x088` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass3` | str, 31 distinct, len ≤ 15, 250 blank | `+0x08A` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass4` | str, 5 distinct, len ≤ 9, 729 blank | `+0x08C` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass1(N)` | str, 67 distinct, len ≤ 19, 253 blank | `+0x08E` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass2(N)` | str, 31 distinct, len ≤ 19, 253 blank | `+0x090` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass3(N)` | str, 31 distinct, len ≤ 19, 253 blank | `+0x092` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass4(N)` | str, 5 distinct, len ≤ 13, 729 blank | `+0x094` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass1(H)` | str, 70 distinct, len ≤ 19, 250 blank | `+0x096` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass2(H)` | str, 34 distinct, len ≤ 19, 250 blank | `+0x098` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass3(H)` | str, 34 distinct, len ≤ 19, 250 blank | `+0x09A` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TreasureClass4(H)` | str, 5 distinct, len ≤ 13, 729 blank | `+0x09C` u16 index (+161) | `treasureclassex:Treasure Class` | [C] |
| `TCQuestId` | int 6..40 (5 distinct), 729 blank | `+0x09E` u8 | — | [C] |
| `TCQuestCP` | int 0..5 (3 distinct), 729 blank | `+0x09F` u8 | — | [C] |
| `SplEndDeath` | int 1..2 (2 distinct), 725 blank | `+0x1A4` u8 | — | [C] |
| `SplGetModeChart` | int, always 1, 714 blank | `+0x1A5` u8 | — | [C] |
| `SplEndGeneric` | int, always 1, 707 blank | `+0x1A6` u8 | — | [C] |
| `SplClientEnd` | int, always 1, 697 blank | `+0x1A7` u8 | — | [C] |
| `*eol` | int, always 0 | — (comment / end-of-line column; not compiled) | — | — |

`S1MinD(N)`/`(H)`, `S1MaxD(N)`/`(H)`, `S1TH(N)`/`(H)` equal each other in every row, so the two are told
apart only by the column order of their group `[I]`. The `El3*` and `MissS3/4`, `aidist` columns are
blank everywhere and placed by stride `[I]`.

### Fields with no `.txt` column

| offset | type | observed | tag |
|---|---|---|---|
| `+0x00A` | u16 | 0 in every record | `[I]` padding: no descriptor entry, no writer found |
| `+0x00F` bits 5–7 | bits | 0 in every record | `[I]` padding: no descriptor entry, no writer found |
| `+0x025` | u8 | 0 | unknown |
| `+0x02A` | s16 | 0 | `[I]` first `monequip` row of the class, −1 if none, written at load by `MONEQUIP_Load` |
| `+0x036`, `+0x038` | s16 each | 0 | `[I]` walk and run values derived at load from the animation data and `Velocity`/`Run` (`sub_00650F00_MonStatsSpeeds`) |
| `+0x04A`, `+0x04B` | u8 each | 0 | `[I]` length of the class chain (`BaseId` → `NextInClass`) and the record's position in it, written at load (`sub_00651040_MonClassChain`) |
| `+0x055`, `+0x0A7`, `+0x10D`, `+0x16B` | u8 | 0 | unknown (gaps before u16 groups) |
| `+0x188 + 2k`, k = 0..7 | s16 | sequence ordinal for `Sk(k+1)mode = seq_*`, else −1 | `[C]` derived from `SknMode` |

`[I]` The fillers and padding verdicts are [data/0004](../findings/data/0004-cell-converters.md) (field
descriptor listing, writer search; [data/0004 §3](../findings/data/0004-cell-converters.md#3-runtime-fillers-of-no-column-fields), fn:MONEQUIP_Load@0x00659E60,
fn:sub_00650F00_MonStatsSpeeds@0x00650F00, fn:sub_00651040_MonClassChain@0x00651040). A padding verdict
holds for readers reached right after a table lookup; readers through a cached record pointer were not
covered (data/0004 *Open questions*). `.bin` holds 0 in every filled field, so a reader of the `.bin`
alone must compute them as the loader does.

## Interpretation notes

- `[C]` **TC columns store (TreasureClassEx row + 161)**, u16, for all 4 362 non-blank cells; a blank
  cell stores 0. The +161 is the runtime TC index: 0 empty, 1–160 auto item-type TCs
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). The order of the twelve fields is `TreasureClass1..4`, then `(N)`, then `(H)`, from
  `+0x086`.
- `[I]` **Which TC a monster drops from** ([items/0001 §3](../findings/items/0001-tc-resolution.md#3-monster-tc-selection--monster_dropitems-0x005a6600)):
  the field is `+0x086 + 8·diff + 2·k`; k = 0 `TreasureClass1` for a normal monster or a minion, k = 1
  `TreasureClass2` for a champion, k = 2 `TreasureClass3` for a unique, and for a superunique the
  `superuniques` record's TC (`+0x2C + 2·diff`), falling back to `TreasureClass3` when the record is missing.
  `TreasureClass4` (k = 3) is the quest TC: it replaces whichever TC was chosen when `TCQuestId` ≠ 0, the
  `TreasureClass4` cell is set, the killer resolves to a player, and none of the quest states
  (`TCQuestId`, 15), (`TCQuestId`, 1), (`TCQuestId`, `TCQuestCP`) is 1. `TCQuestId` is the quest argument and
  `TCQuestCP` the third state argument of that test; what the states mean is left to `items/quest-drops` (fn:MONSTER_DropItems@0x005A6600, tbl:MonStats.txt:TreasureClass1,
  tbl:MonStats.txt:TCQuestId, tbl:MonStats.txt:TCQuestCP). `[C]` for normal, minion, unique and superunique
  monsters in Normal and Nightmare: 317 of 317 logged drop calls took the predicted base TC
  (run:2026-10-11-tc-drops; champion and Hell were not observed).
- `[C]` `MonType` blank → 0 and `MonSound`/`UMonSound` blank → 0 (the target tables have an empty-key
  row 0); `MonStatsEx`, `MonProp`, `AI`, `Skill*`, `Miss*`, `SkillDamage`, monster refs blank → −1.
- `[C]` `SknMode`: a `monmode` code stores its index (`A1` → 4, `S1` → 8…), blank stores 0 (not −1),
  and a `seq_*` name stores 14 (`xx`, the sequence mode) plus the sequence ordinal at `+0x188 + 2k`.
- `[C]` `spawnx`/`spawny` hold −2 for `suckernest1..4` (`0xFE`): signed bytes.
- `[C]` One cell differs from the `.txt`: `uberandariel` `NameStr = Lilith` stores 5382 (key not
  found) although the shipped `patchstring.tbl` has `Lilith` ([tbl.md](../formats/tbl.md)). Listed by
  `diff` as the only explained mismatch.

## Pool and level columns (plan 0012 Phase 0)

The columns the level's monster pool and the monster level may read, with what the data alone shows.
Counts are by `python3 -I tools/mon_survey.py monstats <excel-dir>` over the 734 decoded records
(the `.bin`, which is what the game loads); every column here is laid out and diffs with 0 mismatches
(see [Columns](#columns)). A meaning is `[I]` or `[C]` only where a finding anchors it (plan 0012 Phase 1:
[monsters/0001](../findings/monsters/0001-level-pool.md)); readings of the names are `[L]`.

| Column | `.bin` field | Data | Meaning | Meaning tag |
|---|---|---|---|---|
| `enabled` | `+0x00F` bit 1 | 1 on 703 records, 0 on 31: `chaoshorde1..4`, `darkguard1..5`, `bloodmage1..5`, `firebeast`, `iceglobe`, `lightningbeast`, `poisonorb`, `familiar`, `evilhole2..5`, `suckernest1..4`, `spiritmummy`, `wolfrider1..3`. No `Levels` pool, critter, `minion1/2` or `spawn` cell names a disabled record | not tested by the pool build ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3); stock data names no disabled class in a pool, so no run can show it; what reads it is open | [C] data; [I] not tested by the pool |
| `Level`, `Level(N)`, `Level(H)` | `+0x0AA`, `+0x0AC`, `+0x0AE` u16 | 0..110 each; `Level` ≤ `Level(N)` ≤ `Level(H)` in all 734 records; all three 0 in 150 records (124 of them enabled, 53 `npc`). No `Levels` pool entry has `Level` 0 | the monster level, indexed by difficulty: always in normal, in classic games, for `noRatio` and hireling classes; otherwise (expansion nightmare/hell) `Levels.MonLvl2Ex/3Ex` wins ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5) | [C] for the logged cases (expansion nightmare/hell `MonLvlEx`, classic nightmare/hell, expansion normal, `noRatio`, hireling 271); [I] for hirelings 338/359/560/561, classic normal, `boss` and the no-record fallback |
| `Rarity` | `+0x02E` u8 | 0..2: enabled records 0 ×187, 1 ×422, 2 ×94. Pool entries (`mon*`): 1 ×419, 2 ×118, 0 ×3 (the three `ancientbarb*` of *Mountain Top*) | **not** used by the pool pick; copied into the pool entry and summed, the weight of the spawn-time class pick (0 = never picked) ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3, § 6) | [C] (pool), [I] (spawn pick) |
| `isSpawn` | `+0x00C` bit 0 | 1 on 570 records; 141 enabled records have 0. In the pools only the three `ancientbarb*` of *Mountain Top* have 0 | a picked pool class is kept only if set; a dropped pick still counts ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3) | [C] |
| `MinGrp`, `MaxGrp` | `+0x02F`, `+0x030` u8 | `MinGrp` ≤ `MaxGrp` in every record; (0,0) on 8, (1,1) on 286, widest (5,10) | critter count `RangeB(MaxGrp − MinGrp) + MinGrp` ([monsters/0001](../findings/monsters/0001-level-pool.md) § 7); the random group size: [§ Spawn columns](#spawn-columns-plan-0014-phase-0) | [C] |
| `PartyMin`, `PartyMax` | `+0x02C`, `+0x02D` u8 | `PartyMin` ≤ `PartyMax` in every record; (0,0) on 656. Every record with `PartyMax` > 0 has `minion1`; `radament` has `minion1` with `PartyMax` 0 | the MonStats minion count: [§ Spawn columns](#spawn-columns-plan-0014-phase-0) | [C] |
| `minion1`, `minion2` | `+0x026`, `+0x028` u16 monster ordinal | set on 79 and 9 records; all resolve to enabled records | the minion classes: [§ Spawn columns](#spawn-columns-plan-0014-phase-0) | [C] |
| `spawn` | `+0x020` u16 monster ordinal | set on 52 records (31 of them with `isSpawn` 0); all resolve to enabled records | name: the class a spawner creates | [L] |
| `noRatio` | `+0x00C` bit 2 | 1 on 31 records, all player summons and pets (`claygolem` … `bear`) | blocks the TC level upgrade on drops (items/0001 §4); keeps the MonStats `Level*` in expansion nightmare/hell ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5) | [I] (TC), [C] (level) |
| `boss` | `+0x00C` bit 6 | 1 on 25 records: the act bosses, their uber and clone forms, `summoner`, `izual`, `bloodraven`, `griswold`, `radament`, `nihlathakboss` and `putriddefiler1..5`. The `putriddefiler*` are the only `boss` classes in any `Levels` pool (10 cells, Act 5 temples) | blocks the TC level upgrade on drops (items/0001 §4); keeps the MonStats `Level*` like `noRatio` ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5); other uses `[L]` | [I] |
| `primeevil` | `+0x00C` bit 7 | 1 on 12 records: `andariel`, `duriel`, `mephisto`, `diablo`, `diabloclone`, `baalcrab`, `baalclone` and the five `uber*` act bosses | name | [L] |
| `killable` | `+0x00D` bit 7 | 1 on 634 records; 83 enabled records have 0 | name | [L] |
| `npc` | `+0x00D` bit 0 | 1 on 59 records; none in any `Levels` pool | name | [L] |

- `[I]` `noRatio` and `boss` gate the drop's TC level upgrade: both bits are tested before
  `TC_DropByIndex` walks forward (fn:TC_DropByIndex@0x0055AFA0, tbl:MonStats.txt:noRatio, tbl:MonStats.txt:boss;
  [items/0001 §4](../findings/items/0001-tc-resolution.md#4-level-upgrade--tc_dropbyindex-0x0055afa0-and-tc_getbyindex-0x00654e00)).
- `[C]` Data only: the levels' `MonLvl*` are not a copy of the pool classes' `Level*`. Over the 540 `mon*`
  entries `Level` equals the level's `MonLvl1` 245 times and `MonLvl1Ex` 248 times; over the 686 `nmon*`
  entries `Level(N)` equals `MonLvl2` 4 times and `MonLvl2Ex` 389 times, `Level(H)` equals `MonLvl3` 8 times
  and `MonLvl3Ex` 366 times. (tbl:MonStats.txt:Level, tbl:Levels.txt:MonLvl1Ex)
- Which value a spawned monster gets is settled (`[C]` for the logged cases, `[I]` for the rest, below): `d = min(difficulty, 2)` (0 for the five hireling classes),
  `level = Level/Level(N)/Level(H)[d]`, replaced by the level's `MonLvl1Ex/2Ex/3Ex[d]` only in an expansion game with
  `d > 0` and neither `noRatio` nor `boss`. `[C]`: expansion nightmare/hell (`MonLvlEx`), classic nightmare/hell
  (MonStats), expansion normal (MonStats), `noRatio`, hireling 271. `[I]`: hirelings 338, 359, 560, 561, classic
  normal, `boss`, and the no-level-record fallback. ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5, fn:sub_00573CB0_MonStatsInit@0x00573CB0, run:2026-10-12-mon-pool-p2)
- `[C]` `rangedtype` (`+0x00F` bit 4) is what the `rangedspawn` first-pick redraw tests (Levels § Monster pool
  columns). ([monsters/0001](../findings/monsters/0001-level-pool.md) § 3, tbl:MonStats.txt:rangedtype, run:2026-10-12-mon-pool)
- `[C]` `MonStatsEx` (`+0x018`) is the link the pool follows to the class's `monstats2` record, whose component
  counts drive the variant (appearance) rolls ([MonStats2](MonStats2.md)). ([monsters/0001](../findings/monsters/0001-level-pool.md) § 4, fn:sub_00451FE0_MonStats2Rec@0x00451FE0)
- `[C]` Monster references in pools, critters and the monster init are record positions (`g_pMonStats + 0x1A8·i`):
  *Pandemonium 3*'s 723 is the second `cr_lancer8` at run time too, closing the runtime check below.
  ([monsters/0001](../findings/monsters/0001-level-pool.md) § 8, run:2026-10-12-mon-pool)

## Spawn columns (plan 0014 Phase 0)

The columns the room population pass (`monsters/spawn`) may read for a group, with what the data alone shows.
Counts are over the 734 decoded records and over the **362 pool classes**: the distinct classes named by a `mon`,
`nmon` or `umon` slot of a level whose `MonDen` for that difficulty is non-zero (the classes the population pass
can pick; [Levels § Spawn survey](Levels.md#spawn-survey-per-difficulty-plan-0014-phase-0)). Per-difficulty counts
come from `python3 -I tools/mon_survey.py spawn <excel-dir>`; the rest are ad hoc over the same decoded records.
Every column here is laid out and diffs with 0 mismatches ([Columns](#columns)). A meaning is `[I]` or `[C]`
only where a finding anchors it; readings of the names are `[L]`.

| Column | `.bin` field | Data (all records / pool classes) | Meaning | Meaning tag |
|---|---|---|---|---|
| `MinGrp`, `MaxGrp` | `+0x02F`, `+0x030` u8 | `MinGrp` ≤ `MaxGrp` everywhere. Pool classes: `MinGrp` 1..7, `MaxGrp` 1..10, commonest (2,3) ×76, (2,4) ×59, (3,4) ×53, (1,2) ×45, (1,1) ×36; widest `hellbovine` (5,10), `swarm4/5` (7,9). The 8 records with (0,0) (`gorgon1..4`, `chaoshorde1..4`) are in no pool | critter count `RangeB(MaxGrp − MinGrp) + MinGrp` ([monsters/0001](../findings/monsters/0001-level-pool.md) § 7); the size of a normal random group, uniform in `[MinGrp, MaxGrp]`: a leader plus `MinGrp − 1 + RangeB(leader seed, MaxGrp − MinGrp + 1)` members, with (1,1) forced when `BaseId` is `fallen1` or `scarab1` ([monsters/0002](../findings/monsters/0002-room-population.md) § 5, fn:sub_0054DF80_SpawnGroup@0x0054DF80, run:2026-10-13-mon-spawn) | [C] |
| `PartyMin`, `PartyMax` | `+0x02C`, `+0x02D` u8 | `PartyMin` ≤ `PartyMax` everywhere. Pool classes: 0..4 / 0..8; (0,0) on 306 of 362. In the pools, `PartyMax` > 0 exactly when `minion1` is set (55 classes in nightmare/hell, 36 in normal); outside them `radament` has `minion1` with (0,0) | the MonStats minions of every monster created without request flag `0x40` (each member of a normal group, champion-pack members; not the special boss): `RandRangeIncl(unit seed, PartyMin, PartyMax)` of them, no draw when `PartyMin ≥ PartyMax`, nothing unless `minion1` is a valid class. A unique's 3..6 minions do not use these columns ([monsters/0002](../findings/monsters/0002-room-population.md) § 5, § 6, fn:sub_005B2830_MinionsSpawn@0x005B2830, run:2026-10-13-mon-spawn) | [C] |
| `minion1`, `minion2` | `+0x026`, `+0x028` u16 monster ordinal | set on 79 / 9 records. `minion1` names the class itself on 31 records (22 pool classes: `fallen1..4`, `fetish*`, `fetishblow*`, `scarab1..7`); otherwise a related class (`fallenshaman*` → `fallen*`, `cantor*` → `zealot*`, `overseer*` → `minion*`, `unraveler*` → `skeleton*`, `siegebeast*` → `imp*`). `minion2` only on the `fetishshaman*` (and `fetish11`), always a `fetishblow*` | the classes of the MonStats minions above, alternating `minion1`, `minion2` (`minion2` only when valid), radius 4 around the unit; a unique boss's minions are `minion1`, or its own class when `minion1` is not valid ([monsters/0002](../findings/monsters/0002-room-population.md) § 5, § 6, fn:sub_005B2830_MinionsSpawn@0x005B2830, fn:sub_005A0BB0_UniqueMinionClass@0x005A0BB0, run:2026-10-13-mon-spawn) | [C] |
| `SetBoss` | `+0x00C` bit 4 | 63 records, 43 pool classes; every `SetBoss` record has `minion1`. 16 records have `minion1` without `SetBoss` (`unraveler1..4`, `cantor1..6`, `doomknight3`, `dkmag1..3`, `radament`, `bloodraven`) | when set, `MinionsSpawn` links each minion to its leader (calls `0x0058F030`/`0x0058F100`); what the link does is not read ([monsters/0002](../findings/monsters/0002-room-population.md) § 6, fn:sub_005B2830_MinionsSpawn@0x005B2830) | [I] |
| `BossXfer` | `+0x00C` bit 5 | 41 records, 28 pool classes; always with `SetBoss` | passed as an argument to the link call `0x0058F030` above; its effect is not read ([monsters/0002](../findings/monsters/0002-room-population.md) § 6, fn:sub_005B2830_MinionsSpawn@0x005B2830) | [I] |
| `spawn` | `+0x020` u16 monster ordinal | 52 records; 15 pool classes: `sandmaggot1..7` → `maggotegg*`, `vilemother1..5` → `vilechild*`, `crownest1..3` → `foulcrow*` | with `placespawn`, a `% 100 > 20` roll in the class pick substitutes the `spawn` class (fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, [monsters/0001](../findings/monsters/0001-level-pool.md) § 6); other uses (spawner monsters) [L] | [I] substitution |
| `placespawn` | `+0x00E` bit 7 | 4 records, `crownest1..4` (`spawn` = `foulcrow1..4`); 3 pool classes (`crownest1..3`). No record has `placespawn` without `spawn` | gates the substitution above | [I] |
| `spawnx`, `spawny` | `+0x022`, `+0x023` s8 | set exactly on the 52 `spawn` records. (0,0) ×25, (0,3) ×13, (8,0) ×5 (`maggotqueen*`), (0,2) ×4, (−2,−2) ×4 (`suckernest*`), (2,5) ×1 (`evilhut`) | name: offset of the spawned unit from the spawner | [L] |
| `spawnmode` | `+0x024` u8 `monmode` index | `S1` on 19 `spawn` records (`sandmaggot*`, `maggotegg*`, `maggotqueen*`, `bloodraven`), `NU` on the other 33; blank (255) on the 682 without `spawn` | name: the spawned unit's starting mode | [L] |
| `isMelee` | `+0x00C` bit 1 | 430 records, 213 pool classes (18 of them also `rangedtype`) | name | [L] |
| `npc` | `+0x00D` bit 0 | 59 records, 0 pool classes | name | [L] |
| `inTown` | `+0x00D` bit 2 | 109 records (54 also `npc`), 0 pool classes | name | [L] |
| `interact` | `+0x00D` bit 1 | 47 records, 0 pool classes | name | [L] |
| `Align` | `+0x04C` u8 | 0 on 619 records, 1 on 113 (town NPCs, critters, hirelings, player summons), 2 on 2 (`cow`, `camel`); 0 on every pool class | read after each creation by `MonSpawnTry`: 1 → `0x005543B0(2)` and unit `+0xC4` \|= `0x20000`, 2 → `0x005543B0(1)`, else `0x005543B0(0)`; the callee is named only, so "alignment (enemy / ally / neutral)" stays a reading of the name ([monsters/0002](../findings/monsters/0002-room-population.md) § 6, fn:sub_005B2A00_MonSpawnTry@0x005B2A00) | [I] read; meaning [L] |
| `isSpawn` | `+0x00C` bit 0 | 570 records; all 362 pool classes but the three `ancientbarb*` | kept by the pool build only if set ([MonStats § Pool and level columns](#pool-and-level-columns-plan-0012-phase-0)) | [C] |
| `rangedtype` | `+0x00F` bit 4 | 140 records, 113 pool classes | the `rangedspawn` first-pick redraw ([MonStats § Pool and level columns](#pool-and-level-columns-plan-0012-phase-0)) | [C] |
| `sparsePopulate` | `+0x031` u8 | 40 on one record, `evilhut`; 0 elsewhere (in no pool) | when non-zero, a normal group spawns only if a game-seed roll `low mod 100 ≤ sparsePopulate`; a failed roll spawns nothing. Stock data never reaches the roll (`evilhut` is in no pool), and the community describes the opposite sense ([monsters/0002](../findings/monsters/0002-room-population.md) § 5, 0x0054EE4D, 0x0054EE8C) | [I] |
| `genericSpawn` | `+0x00E` bit 5 | 55 records, 41 pool classes (`deathmauler*`, `frozenhorror*`, `imp*` …) | name | [L] |
| `zoo` | `+0x00E` bit 6 | 152 records, 119 pool classes | name | [L] |
| `neverCount` | `+0x00E` bit 2 | 77 records, 1 pool class (`baaltaunt`, a `umon` entry) | read after each creation by `MonSpawnTry`, with request flag 8, for the region live-count update `0x00547D90`; that callee is named only, so whether the unit is left out of the count is a reading of the name ([monsters/0002](../findings/monsters/0002-room-population.md) § 6, fn:sub_005B2A00_MonSpawnTry@0x005B2A00) | [I] read; meaning [L] |
| `threat` | `+0x04E` u8 | pool classes: 10 ×343, 12 ×11, 11 ×7, 0 ×1 | name | [L] |
| `killable`, `opendoors`, `switchai` | `+0x00D` bit 7, `+0x00C` bit 3, `+0x00E` bit 0 | 634 / 322 / 585 records; 361 / 215 / 349 pool classes | name | [L] |

- `[C]` Data only: no pool class has `npc`, `inTown`, `interact`, `petIgnore`, `primeevil` or a non-zero `Align`;
  four have `boss` (`putriddefiler1..4`, Act 5 temples). (tbl:MonStats.txt:npc, tbl:MonStats.txt:Align)
- Plan 0014 Phase 1 settled which of these the population pass reads ([monsters/0002](../findings/monsters/0002-room-population.md); linked in the table
  above by plan 0020 Phase 1). No function of that finding reads `spawnx`, `spawny`, `spawnmode`, `isMelee`,
  `genericSpawn` or `zoo`, so those meanings stay `[L]`; `threat` was not looked for. ([monsters/0002](../findings/monsters/0002-room-population.md) § Data touched)

## Stat columns (plan 0025 Phase 0)

The columns that by their names feed a monster's stats, grouped as `monsters/stats` will need them. The offsets are
the [Columns](#columns) table's (`excel_bin.py diff`, `[C]`); the survey is
`python3 -I tools/mon_survey.py stats <excel-dir> <class|record|all> <normal|nightmare|hell|all>`, which prints one
class's cells for a difficulty beside the [MonLvl](MonLvl.md) row of its level, its [MonProp](MonProp.md) slots and
the [DifficultyLevels](DifficultyLevels.md) row; `all all` formats every record in every difficulty (2 202 blocks,
0 errors) and prints the counts below (gate survey `mon_stats`). **Meanings stay `[L]`** until plan 0025 Phase 1.

### Per-difficulty column groups

`[C]` Every per-difficulty column is a triple whose normal, nightmare and hell fields sit at `base + w·d`
(`w` the field width, `d` = 0, 1, 2). Names are irregular: the hit-point columns are `minHP`/`maxHP` in normal but
`MinHP(N)`/`MaxHP(N)`/`MinHP(H)`/`MaxHP(H)` otherwise; every other triple is `X`, `X(N)`, `X(H)`. (tbl:MonStats.txt:minHP, tbl:MonStats.txt:MinHP(N))

| Group | Columns (normal name) | Field (`d` = difficulty) |
|---|---|---|
| level | `Level` | `+0x0AA + 2d` u16 |
| hit points | `minHP`, `maxHP` | `+0x0B0 + 2d`, `+0x0B6 + 2d` u16 |
| armour class, experience | `AC`, `Exp` | `+0x0BC + 2d`, `+0x0D4 + 2d` u16 |
| to-hit | `A1TH`, `A2TH`, `S1TH` | `+0x0C2 + 2d`, `+0x0C8 + 2d`, `+0x0CE + 2d` u16 |
| damage | `A1MinD`, `A1MaxD`, `A2MinD`, `A2MaxD`, `S1MinD`, `S1MaxD` | `+0x0DA`, `+0x0E0`, `+0x0E6`, `+0x0EC`, `+0x0F2`, `+0x0F8` (+ `2d`) u16 |
| resistances | `ResDm`, `ResMa`, `ResFi`, `ResLi`, `ResCo`, `ResPo` | `+0x144 + 6k + 2d` s16 (`k` = 0..5 in that order) |
| other | `Drain`, `ToBlock`, `coldeffect` | `+0x0A0 + d`, `+0x0A3 + d` u8; `+0x168 + d` s8 |
| elemental attack `e` = 1..3 | `El<e>Pct`, `El<e>MinD`, `El<e>MaxD`, `El<e>Dur` | `+0x104 + 3(e−1) + d` u8; `+0x10E`, `+0x120`, `+0x132` `+ 6(e−1) + 2d` u16 |

`[C]` One value for all difficulties: `El<e>Mode` (`+0x0FE + e−1`, `monmode` index, blank 255), `El<e>Type`
(`+0x101 + e−1`, `elemtypes` index, blank 0), `Crit` (`+0x0A6`), `DamageRegen` (`+0x1A0` u32), `SkillDamage`
(`+0x0A8`, `skills` index, blank 0xFFFF), `MonProp` (`+0x01A`), `Skill1..8` and `Sk1lvl..Sk8lvl` (`+0x198 + k`).
(tbl:MonStats.txt:El1Mode, tbl:MonStats.txt:DamageRegen)

- `[I]` The level triple is the class's monster level in each difficulty, replaced by the level's `MonLvl*Ex` in an
  expansion game in nightmare and hell (§ Pool and level columns), and the level picks the [MonLvl](MonLvl.md) row
  (`sub_006538A0_MonLvlStats`, MonLvl.md § Interpretation notes). The survey shows the MonLvl row of the MonStats level
  only, without the `MonLvlEx` replacement. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_006538A0_MonLvlStats@0x006538A0)

### Blank patterns

`[C]` A blank stat cell compiles to 0 (`excel_bin.py diff`); whether the code treats 0 as "none" or as a value is
`[L]`. Records (of 734) whose cells of a group are all blank / some blank, per difficulty
(`mon_survey.py stats … all all`):

| Group | normal | nightmare | hell |
|---|---|---|---|
| level | 150 / 0 | 150 / 0 | 150 / 0 |
| hit points | 139 / 3 | 142 / 0 | 141 / 0 |
| `AC`, `Exp` | 139 / 60 | 141 / 57 | 140 / 58 |
| `A1*` (`MinD`, `MaxD`, `TH`) | 261 / 18 | 260 / 13 | 260 / 13 |
| `A2*` | 566 / 0 | 572 / 0 | 572 / 0 |
| `S1*` | 705 / 0 | 705 / 0 | 705 / 0 |
| resistances (six) | 433 / 288 | 405 / 311 | 184 / 476 |
| `Drain`, `coldeffect`, `ToBlock` | 138 / 156 | 147 / 144 | 148 / 144 |
| `El1*` (`Pct`, `MinD`, `MaxD`, `Dur`) | 513 / 129 | 439 / 159 | 439 / 159 |
| `El2*` | 707 / 22 | 694 / 30 | 694 / 30 |
| `El3*` | 734 / 0 | 734 / 0 | 734 / 0 |

`[C]` Data only, over the fifteen "core" cells (`Level`, `minHP`, `maxHP`, `AC`, `Exp` × three difficulties):

- **114 records are blank in all fifteen**: the town NPCs, critters and other non-combat classes (`cain1..5`,
  `akara`, `chicken`, `rat`, `bird1`, `act2male` …, the `darkguard*`/`bloodmage*` and `gorgon*`/`chaoshorde*`
  classes). None has `boss` or `primeevil`; 52 have `npc`, 69 `inTown`, 92 `enabled`, 28 `killable`.
- **91 records are blank in some**, in a few patterns:
  - `Level` and `Exp` blank, hit points and `AC` set (30): the player summons and pets (`claygolem` … `firegolem`,
    `necroskeleton`, `necromage`, `valkyrie`, `dopplezon`, the assassin traps and shadows, the druid summons),
    plus `rogue1`;
  - `Exp` blank only (26): the bone prisons and walls, the Act 5 barricades and doors, `act5barb1/2`, `act5pow`,
    the `ancientbarb*`, the `baaltentacle*`, `baalclone`, `navi`, `rogue2`, `rogue3`;
  - hit points, `AC` and `Exp` blank, `Level` set (25): the hirelings (`roguehire`, `act2hire`, `act3hire`,
    `act5hire1/2`), the `evilhole*`, the missile traps, `hellmeteor`, `spiritmummy`, `ancientstatue1..3`,
    `injuredbarb*`, `baaltaunt`, `baalcrabstairs`, `demonhole`;
  - `Level` blank only (4): `suckernest1..4`;
  - six single records: `window1/2` (normal `minHP` blank, `maxHP` set), `compellingorb` (normal `Exp` blank),
    `trap-melee` and `act2guard3` (`Level`, `Exp` and some nightmare/hell cells blank), `mephistospirit`
    (`maxHP` and `AC` blank in all three, normal `minHP` 1267).
- The level triple is all-blank or all-set in every record, and so are `A2*`, `S1*` and `El3*` (never set). The
  resistance and elemental cells are often blank in normal and set in hell: a blank there reads as 0.
- Value checks: `Level` ≤ `Level(N)` ≤ `Level(H)` and `Level(H)` ≤ 110 (the last MonLvl row) in every record. `minHP`
  > `maxHP` in two cells (`mephistospirit` normal 1267 > blank; `minionspawner1` normal 151 > 106);
  `El1MinD(N)` 60 > `El1MaxD(N)` 33 in `andariel` and `uberandariel`; `wakeofdestruction` has `El1` values with
  `El1Mode` and `El1Type` blank. No `A1/A2/S1` `MinD` > `MaxD`. How the code orders a reversed range is a reverser
  question. (tbl:MonStats.txt:minHP, tbl:MonStats.txt:El1MinD(N))
- Resistances of 100 or more, counted as (record, column) cells: normal 23 (`ResFi` 1, `ResPo` 22), nightmare 93,
  hell 517; the maxima are 1000 (`ResPo` in all three difficulties, `ResCo(H)`) and otherwise 145 (`ResMa(H)`,
  `ResFi(H)`, `ResLi(H)`).

### Boss, prime evil and npc rows

- `[I]` `boss` (25 records; list in § Pool and level columns) is read by code: it blocks the TC level upgrade and keeps
  the MonStats `Level*` in expansion nightmare/hell (§ Pool and level columns). All 25 have the core stats set; the
  six `uber*` bosses and `diabloclone` have `Level` 110 in all three difficulties. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:MonStats.txt:boss)
- `[L]` `primeevil` (12 records, all also `boss`) and `npc` (59 records) have no reader named. Only 7 `npc` records
  have core stats (`rogue1`, `rogue2`, `rogue3`, `navi`, `ancientstatue1..3`); the other 52 are blank in all fifteen.
- `[C]` 18 records name a [MonProp](MonProp.md) row (12 distinct rows: the six `blunderbore*` share one, `mephisto`
  and `ubermephisto` share one). (tbl:MonStats.txt:MonProp)

## Open questions

- Answered `[I]` in [data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions): monster
  references are used as record positions, so with the duplicate `cr_lancer8` *Pandemonium 3*'s
  `mon1` = 723 is the second `cr_lancer8`, not `overseer6`. Confirmed at run time `[C]` by
  [monsters/0001 § 8](../findings/monsters/0001-level-pool.md) (runtime record 723 = `monstats.bin` record 723).
- Answered `[C]` in [data/0001 §7–8](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time): the 161 TC indices below
  TreasureClassEx row 0 are the empty TC (0) and the auto item-type TCs (1–160).
- Answered `[I]` by [data/0004](../findings/data/0004-cell-converters.md) for `+0x00A`, `+0x00F` bits 5–7,
  `+0x02A`, `+0x036`/`+0x038`, `+0x04A`/`+0x04B` (§ Fields with no `.txt` column). Still open: `+0x025` and the
  four single gap bytes, and whether a reader reaches the padding through a cached record pointer.
