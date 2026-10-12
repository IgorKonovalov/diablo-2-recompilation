# MonStats (`data/global/excel/monstats.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 734 (735 data rows − 1 `Expansion` marker at row 410)   **Record:** 424 B
> **sha256:** `.txt` `a15e1cb876bd9af1e8f54199c9619226cf4835c45c799aed2d432901487ecb7c`, `.bin` `b8c6b72df4c7825a43da33d3e533f2e7e14b268b01c6236e82ab2d800fc75584`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending

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
| `+0x00A` | u16 | 0 in every record | unknown |
| `+0x00F` bits 5–7 | bits | 0 in every record | unknown |
| `+0x025` | u8 | 0 | unknown |
| `+0x02A` | u16 | 0 | unknown |
| `+0x036` | u32 | 0 | unknown |
| `+0x04A` | u16 | 0 | unknown |
| `+0x055`, `+0x0A7`, `+0x10D`, `+0x16B` | u8 | 0 | unknown (gaps before u16 groups) |
| `+0x188 + 2k`, k = 0..7 | s16 | sequence ordinal for `Sk(k+1)mode = seq_*`, else −1 | `[C]` derived from `SknMode` |

## Interpretation notes

- `[C]` **TC columns store (TreasureClassEx row + 161)**, u16, for all 4 362 non-blank cells; a blank
  cell stores 0. The +161 is the runtime TC index: 0 empty, 1–160 auto item-type TCs
  ([data/0001 §7](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time)). The order of the twelve fields is `TreasureClass1..4`, then `(N)`, then `(H)`, from
  `+0x086`.
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
(see [Columns](#columns)). A meaning is `[I]` only where a finding anchors it; readings of the names are
`[L]` and wait for plan 0012 Phase 1.

| Column | `.bin` field | Data | Meaning | Meaning tag |
|---|---|---|---|---|
| `enabled` | `+0x00F` bit 1 | 1 on 703 records, 0 on 31: `chaoshorde1..4`, `darkguard1..5`, `bloodmage1..5`, `firebeast`, `iceglobe`, `lightningbeast`, `poisonorb`, `familiar`, `evilhole2..5`, `suckernest1..4`, `spiritmummy`, `wolfrider1..3`. No `Levels` pool, critter, `minion1/2` or `spawn` cell names a disabled record | name: the class may be created | [L] |
| `Level`, `Level(N)`, `Level(H)` | `+0x0AA`, `+0x0AC`, `+0x0AE` u16 | 0..110 each; `Level` ≤ `Level(N)` ≤ `Level(H)` in all 734 records; all three 0 in 150 records (124 of them enabled, 53 `npc`). No `Levels` pool entry has `Level` 0 | name: the class's monster level per difficulty; whether it or `Levels.MonLvl*` wins is plan 0012 Phase 1 | [L] |
| `Rarity` | `+0x02E` u8 | 0..2: enabled records 0 ×187, 1 ×422, 2 ×94. Pool entries (`mon*`): 1 ×419, 2 ×118, 0 ×3 (the three `ancientbarb*` of *Mountain Top*) | name: a weight in the pool pick | [L] |
| `isSpawn` | `+0x00C` bit 0 | 1 on 570 records; 141 enabled records have 0. In the pools only the three `ancientbarb*` of *Mountain Top* have 0 | name: may be placed by random population | [L] |
| `MinGrp`, `MaxGrp` | `+0x02F`, `+0x030` u8 | `MinGrp` ≤ `MaxGrp` in every record; (0,0) on 8, (1,1) on 286, widest (5,10) | name: group size range | [L] |
| `PartyMin`, `PartyMax` | `+0x02C`, `+0x02D` u8 | `PartyMin` ≤ `PartyMax` in every record; (0,0) on 656. Every record with `PartyMax` > 0 has `minion1`; `radament` has `minion1` with `PartyMax` 0 | name: minion count range | [L] |
| `minion1`, `minion2` | `+0x026`, `+0x028` u16 monster ordinal | set on 79 and 9 records; all resolve to enabled records | name: the minion classes | [L] |
| `spawn` | `+0x020` u16 monster ordinal | set on 52 records (31 of them with `isSpawn` 0); all resolve to enabled records | name: the class a spawner creates | [L] |
| `noRatio` | `+0x00C` bit 2 | 1 on 31 records, all player summons and pets (`claygolem` … `bear`) | blocks the TC level upgrade on drops (items/0001 §4) | [I] |
| `boss` | `+0x00C` bit 6 | 1 on 25 records: the act bosses, their uber and clone forms, `summoner`, `izual`, `bloodraven`, `griswold`, `radament`, `nihlathakboss` and `putriddefiler1..5`. The `putriddefiler*` are the only `boss` classes in any `Levels` pool (10 cells, Act 5 temples) | blocks the TC level upgrade on drops (items/0001 §4); other uses `[L]` | [I] |
| `primeevil` | `+0x00C` bit 7 | 1 on 12 records: `andariel`, `duriel`, `mephisto`, `diablo`, `diabloclone`, `baalcrab`, `baalclone` and the five `uber*` act bosses | name | [L] |
| `killable` | `+0x00D` bit 7 | 1 on 634 records; 83 enabled records have 0 | name | [L] |
| `npc` | `+0x00D` bit 0 | 1 on 59 records; none in any `Levels` pool | name | [L] |

- `[I]` `noRatio` and `boss` gate the drop's TC level upgrade: both bits are tested before
  `TC_DropByIndex` walks forward (fn:TC_DropByIndex@0x0055AFA0, tbl:MonStats.txt:noRatio, tbl:MonStats.txt:boss;
  [items/0001 §4](../findings/items/0001-tc-resolution.md#4-level-upgrade--tc_dropbyindex-0x0055afa0-and-tc_getbyindex-0x00654e00)).
- `[C]` Data only: the levels' `MonLvl*` are not a copy of the pool classes' `Level*`. Over the 540 `mon*`
  entries `Level` equals the level's `MonLvl1` 245 times and `MonLvl1Ex` 248 times; over the 686 `nmon*`
  entries `Level(N)` equals `MonLvl2` 4 times and `MonLvl2Ex` 389 times, `Level(H)` equals `MonLvl3` 8 times
  and `MonLvl3Ex` 366 times. Which value a spawned monster gets is a code question. (tbl:MonStats.txt:Level, tbl:Levels.txt:MonLvl1Ex)

## Open questions

- Answered `[I]` in [data/0001 §8](../findings/data/0001-excel-loader.md#8-answers-to-the-archivists-phase-1-questions): monster
  references are used as record positions, so with the duplicate `cr_lancer8` *Pandemonium 3*'s
  `mon1` = 723 is the second `cr_lancer8`, not `overseer6`. A runtime check is still open on the
  reverser side.
- Answered `[C]` in [data/0001 §7–8](../findings/data/0001-excel-loader.md#7-treasure-classes-at-load-time): the 161 TC indices below
  TreasureClassEx row 0 are the empty TC (0) and the auto item-type TCs (1–160).
- `[L]` The unknown zero fields above: padding or runtime-filled (backlog → reverser).
