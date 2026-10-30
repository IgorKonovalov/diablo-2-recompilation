# MonStats (`data/global/excel/monstats.txt`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 734 (735 data rows − 1 `Expansion` marker at row 410)   **Record:** 424 B
> **sha256:** `.txt` `a15e1cb876bd9af1e8f54199c9619226cf4835c45c799aed2d432901487ecb7c`, `.bin` `b8c6b72df4c7825a43da33d3e533f2e7e14b268b01c6236e82ab2d800fc75584`
> **Doc status:** columns listed, `.bin` layout complete, semantics pending (pool, level, spawn, stat and combat columns surveyed; stat-column readers `[I]` from plan 0025 Phase 1)

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
| `AI` | str, 146 distinct, len ≤ 15 | `+0x01E` u16 index | `monai:AI`: the [MonAI](MonAI.md) row, also the `g_MonAiTable` row ([§ AI columns](#ai-columns-plan-0052-phase-0)) | [C] |
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
| `Run` | int 0..20 (18 distinct), 4 blank | `+0x034` u16 (read signed by Charge, § [Readers at creation](#readers-at-creation-and-at-attack-time-plan-0025-phase-1)) | — | [C] |
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
| `+0x02A` | s16 | 0 | `[I]` first `monequip` row of the class, −1 if none, written at load by `MONEQUIP_Load` (the rows: [MonEquip](MonEquip.md)) |
| `+0x036`, `+0x038` | s16 each | 0 | `[I]` walk and run values derived at load from the animation data and `Velocity`/`Run` (`sub_00650F00_MonStatsSpeeds`) |
| `+0x04A`, `+0x04B` | u8 each | 0 | `[I]` length of the class chain (`BaseId` → `NextInClass`) and the record's position in it, written at load (`sub_00651040_MonClassChain`); *plan 0046 readers:* `[C]` skill do 85 and do 132 add `+0x04B` to `srvmissilea` through `MONSTATS_GetClassChainPos` (0 for a class out of range), so the n-th class of a chain casts the n-th missile after the named one (ADR-0021) ([skills/0016 § 6](../findings/skills/0016-monster-8a.md#6-missiles-and-the-infernos-do-85-88-93-95-111-start-53), [skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63); fn:MONSTATS_GetClassChainPos@0x006510C0, fn:sub_005CB0C0_SkillDo85ChainMissile@0x005CB0C0) |
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
  `TCQuestCP` the third state argument of that test; what the states mean per boss is [items/0010 § 3](../findings/items/0010-quest-drops.md#3-the-three-bits-for-the-five-quest-tc-classes) (§ Quest TCs below) (fn:MONSTER_DropItems@0x005A6600, tbl:MonStats.txt:TreasureClass1,
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
  `diff` as the only explained mismatch. `[C]` The pinned game's own `-txt` compile stores 11154 (`Lilith`,
  `patchstring` entry 1154) in that cell, the one byte pair of its `monstats.bin` that differs from the shipped file,
  so the converter rule holds here too (why the shipped cell differs stays a lead, [tbl.md](../formats/tbl.md))
  ([experiments § cube-saves addendum 2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3),
  [data/0004 § S1b](../findings/data/0004-cell-converters.md#plan-0038-batch-s1b-2026-10-16), fn:STRTABLE_KeyToIndex@0x006117B0).

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
| `spawn` | `+0x020` u16 monster ordinal | set on 52 records (31 of them with `isSpawn` 0); all resolve to enabled records | the class a monster's summon skill creates ([§ Spawn columns](#spawn-columns-plan-0014-phase-0), *plan 0046 readers*) | [C] (skill summon) |
| `noRatio` | `+0x00C` bit 2 | 1 on 31 records, all player summons and pets (`claygolem` … `bear`) | blocks the TC level upgrade on drops (items/0001 §4); keeps the MonStats `Level*` in expansion nightmare/hell ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5) | [I] (TC), [C] (level) |
| `boss` | `+0x00C` bit 6 | 1 on 25 records: the act bosses, their uber and clone forms, `summoner`, `izual`, `bloodraven`, `griswold`, `radament`, `nihlathakboss` and `putriddefiler1..5`. The `putriddefiler*` are the only `boss` classes in any `Levels` pool (10 cells, Act 5 temples) | blocks the TC level upgrade on drops (items/0001 §4); keeps the MonStats `Level*` like `noRatio` ([monsters/0001](../findings/monsters/0001-level-pool.md) § 5); in combat, the hireling percent, the stun and freeze exemptions, crushing blow's divisor 8 and the stat 115/116 target modifiers ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)) | [I] |
| `primeevil` | `+0x00C` bit 7 | 1 on 12 records: `andariel`, `duriel`, `mephisto`, `diablo`, `diabloclone`, `baalcrab`, `baalclone` and the five `uber*` act bosses | an attacker with it deals 200 % to a hireling and 400 % to some other defenders (`COMBAT_DamagePercent`, [§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)) | [I] |
| `killable` | `+0x00D` bit 7 | 1 on 634 records; 83 enabled records have 0 | 0 makes the monster take no damage: `COMBAT_ApplyDamage` returns before any change ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)) | [I] |
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
| `spawn` | `+0x020` u16 monster ordinal | 52 records; 15 pool classes: `sandmaggot1..7` → `maggotegg*`, `vilemother1..5` → `vilechild*`, `crownest1..3` → `foulcrow*` | with `placespawn`, a `% 100 > 20` roll in the class pick substitutes the `spawn` class (fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, [monsters/0001](../findings/monsters/0001-level-pool.md) § 6); *plan 0046 readers:* `[C]` `sub_0056E620_SkillSummonClass` with `EDX` 1 (start 49, 62, do 84, 87) takes a **monster** caster's own `spawn` (s16) as the class, one outside the MonStats count replaced by `0x0058F710`'s link fallback (the data `+0x28` link's `+0x3C`, else −1); with `EDX` 0 (do 104, 114, 115, 119, 44, 45, 49) or a non-monster caster the Skills `summon` serves (ADR-0021; `[I]` do 131's class change calls it with `EDX` 0 after its boundary, [skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137)) ([skills/0016 § 4](../findings/skills/0016-monster-8a.md#4-moves-and-marks-start-4346-48-49-51-52-do-8991-94-98), [skills/0016 § 5](../findings/skills/0016-monster-8a.md#5-spawns-heals-and-revives-do-84-86-87-96-97), [skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147); fn:sub_0056E620_SkillSummonClass@0x0056E620, fn:sub_0063EA70_SkillSummonRec@0x0063EA70) | [I] substitution; [C] summon class |
| `placespawn` | `+0x00E` bit 7 | 4 records, `crownest1..4` (`spawn` = `foulcrow1..4`); 3 pool classes (`crownest1..3`). No record has `placespawn` without `spawn` | gates the substitution above | [I] |
| `spawnx`, `spawny` | `+0x022`, `+0x023` s8 | set exactly on the 52 `spawn` records. (0,0) ×25, (0,3) ×13, (8,0) ×5 (`maggotqueen*`), (0,2) ×4, (−2,−2) ×4 (`suckernest*`), (2,5) ×1 (`evilhut`) | *plan 0046 readers:* `[C]` `SkillSummonClass` with `EDX` 1 adds them (s8) to a monster caster's position; start 49 and start 62 write the point into the used node's `+0x1C`/`+0x20`, and do 135 passes the node's point to `SpawnAtPos` (ADR-0021); `[I]` do 91 spawns there after its boundary; do 84 and do 87 pass no point pointers (do 87 steps one cell towards the target) ([skills/0016 § 4](../findings/skills/0016-monster-8a.md#4-moves-and-marks-start-4346-48-49-51-52-do-8991-94-98), [skills/0016 § 5](../findings/skills/0016-monster-8a.md#5-spawns-heals-and-revives-do-84-86-87-96-97), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147); fn:sub_005CBD10_SkillSt49Nest@0x005CBD10, fn:sub_005D2490_SkillDo135MinionSpawn@0x005D2490) | [C] (the node words, do 135); [I] (do 91) |
| `spawnmode` | `+0x024` u8 `monmode` index | `S1` on 19 `spawn` records (`sandmaggot*`, `maggotegg*`, `maggotqueen*`, `bloodraven`), `NU` on the other 33; blank (255) on the 682 without `spawn` | *plan 0046 readers:* `[C]` the mode (s8; 1 outside `[0, 16)`) `SkillSummonClass` gives a monster caster with `EDX` 1: the used node's `+0x24` in start 49 and 62, the spawn mode of do 84 and do 87 (ADR-0021) ([skills/0016 § 4](../findings/skills/0016-monster-8a.md#4-moves-and-marks-start-4346-48-49-51-52-do-8991-94-98), [skills/0016 § 5](../findings/skills/0016-monster-8a.md#5-spawns-heals-and-revives-do-84-86-87-96-97), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147); fn:sub_005CAFA0_SkillDo84MaggotEgg@0x005CAFA0, fn:sub_005CB3C0_SkillDo87MaggotLay@0x005CB3C0) | [C] |
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
| `killable` | `+0x00D` bit 7 | 634 records; 361 pool classes | 0: no damage taken ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)) | [I] |
| `opendoors`, `switchai` | `+0x00C` bit 3, `+0x00E` bit 0 | 322 / 585 records; 215 / 349 pool classes | name | [L] |

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
0 errors) and prints the counts below (gate survey `mon_stats`). The code readings are in
[§ Readers at creation and at attack time](#readers-at-creation-and-at-attack-time-plan-0025-phase-1).

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

`[C]` A blank stat cell compiles to 0 (`excel_bin.py diff`); `[I]` creation uses it as the value 0 (§ Readers). Records (of 734) whose cells of a group are all blank / some blank, per difficulty
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
  `El1Mode` and `El1Type` blank. No `A1/A2/S1` `MinD` > `MaxD`. `[I]` A reversed HP range makes no draw and gives the low cell (§ Readers). (tbl:MonStats.txt:minHP, tbl:MonStats.txt:El1MinD(N))
- Resistances of 100 or more, counted as (record, column) cells: normal 23 (`ResFi` 1, `ResPo` 22), nightmare 93,
  hell 517; the maxima are 1000 (`ResPo` in all three difficulties, `ResCo(H)`) and otherwise 145 (`ResMa(H)`,
  `ResFi(H)`, `ResLi(H)`).

### Boss, prime evil and npc rows

- `[I]` `boss` (25 records; list in § Pool and level columns) is read by code: it blocks the TC level upgrade and keeps
  the MonStats `Level*` in expansion nightmare/hell (§ Pool and level columns; the byte test re-read in
  [items/0010 § 7](../findings/items/0010-quest-drops.md#7-the-boss-exception-of-monsterspool-e4)). All 25 have the core stats set; the
  six `uber*` bosses and `diabloclone` have `Level` 110 in all three difficulties. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:MonStats.txt:boss)
- `[I]` `primeevil` (12 records, all also `boss`) is read by `MONSTATS_IsPrimeEvil` in the combat percent ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1);
  fn:MONSTATS_IsPrimeEvil@0x0063EDC0). **(plan 0039 A1; it was `[L]`, no reader named.)**
- `[L]` `npc` (59 records) has no reader named. Only 7 `npc` records
  have core stats (`rogue1`, `rogue2`, `rogue3`, `navi`, `ancientstatue1..3`); the other 52 are blank in all fifteen.
- `[C]` 18 records name a [MonProp](MonProp.md) row (12 distinct rows: the six `blunderbore*` share one, `mephisto`
  and `ubermephisto` share one). (tbl:MonStats.txt:MonProp)

### Readers at creation and at attack time (plan 0025 Phase 1)

From [monsters/0004](../findings/monsters/0004-stats.md) §§ 2–5 and § 9 (static reading); the formulas are the
finding's, linked here by column. `d` is the difficulty (0 for a hireling), `L` the MonLvl column set
([MonLvl § Code semantics](MonLvl.md#code-semantics-plan-0025-phase-1)), `n` the player count.

| Columns | Read | What the code does with them | Tag |
|---|---|---|---|
| `Level`, `Level(N)`, `Level(H)` | creation | stat 12 and the MonLvl row (§ Pool and level columns); in a classic nightmare/hell game the stat is then rewritten to `Level` (normal) + 25·d | I |
| `minHP`/`maxHP` (and `(N)`/`(H)`) | creation | `lo, hi` = MonLvl `HP` × cell / 100 (raw cells for `noRatio`); one `RangeB(unit seed, hi − lo + 1)`; **a reversed or empty range makes no step and gives `lo`**; then + `n`-player %, cap `0x7FFFFF`, stats 7 and 6 = `hp << 8` | I |
| `AC`, `Exp` | creation | stat 31 = MonLvl `AC` × cell / 100, stat 13 = MonLvl `XP` × cell / 100 + `n`-player %; no draw | I |
| `ResDm`, `ResMa`, `ResFi`, `ResLi`, `ResCo`, `ResPo` | creation | stats 36, 37, 39, 41, 43, 45 as they are (s16), no hell adjustment | I |
| `ToBlock` | creation | stat 20 (u8) | I |
| `DamageRegen` | creation, and every later max-HP change | stat 74 = Life × r / 16 in 1/256 units; negative or above 12 bits is fatal. Also read by the stat callback: on each later change of max HP (stat 7: the classic adjustment, `MonHpAddPct`), stat 74 = `((maxhp >> 8)·r) >> 4` (below) | I (callback C) |
| `Align` | creation | 0: player-count bonus; else no bonus and `players` 1; 1 also skips the classic adjustment | I |
| `Skill1..8`, `Sk1lvl..Sk8lvl`, `Sk1mode..` | creation | each `Skill` ≥ 0 with `Sk lvl` > 0 is added at `Sk lvl` + DifficultyLevels `MonsterSkillBonus` | I |
| `MonProp` | creation | the [MonProp](MonProp.md#code-semantics-plan-0025-phase-1) row, applied to every monster of the class | I |
| `Velocity` | creation (mods); hit time | the champion/fanatic/`fast` velocity bonus, only when > 0; 0 makes the monster unstunnable ([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1)) | I |
| `Velocity` (plan 0046) | skill target test | `[C]` as a map: the corpse test `0x00645510` (starts 15 and 21) refuses a monster whose `+0x032` word is 0; a class outside the MonStats count reads it through a null record (0x0064557F), unmodelled; why the test reads it is an open question of the finding ([skills/0010 § 3](../findings/skills/0010-necromancer.md#3-the-start-functions-15-17-18-19-20-21); fn:sub_00645510_MonCorpseTest@0x00645510) | C |
| `Run` (plan 0046) | Charge (start 31) | `[C]` as a map: a monster caster's base is `+0x034` read **signed** (`movsx`) `<< 8`, then `0x00649050(path)`, into `MulDiv(base, max(stat 67, 50) + Param1, 100)` (Skills `Param1`) for `sub_00648690_PathSetSpeed` (ADR-0021 boundaries); `[I]` that this is the charge's run speed; the layout's u16 and the signed read agree on the stock values 0..20 ([skills/0011 § 5](../findings/skills/0011-paladin.md#5-charge-and-the-missiles-start-31-do-67-73-80); fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0) | C |
| `BaseId` (plan 0046) | skill target tests | `[C]` as a map: do 131 (Overseer Whip) draws only for a monster target whose `MonClassCheck(MonBaseId)` is 453 (`minion1`); do 133 (Impregnate) refuses 546 (`putriddefiler1`) and 551 (`painworm1`) through `sub_005D2140_ImpregnateTest` (ADR-0021); `[I]` do 129's attach helper takes an imp (base 492) and a base-435 or 441 target (`barricadetower`, `siegebeast1`), and `sub_0063EFA0_SpawnClassByBase` (do 140's class) switches on the caster's base ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147), [skills/0018 § 7](../findings/skills/0018-monster-8c.md#7-case-writer-restrictions-and-what-stays-unreached); fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70, fn:sub_005D18E0_ImpAttach@0x005D18E0, fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0) | C (do 131, 133); I (do 129, 140) |
| `A1TH`/`A2TH`/`S1TH`, `A1MinD`…`S1MaxD`, `El<e>*` | **attack time** | to-hit and damage = MonLvl `TH`/`DM` × cell / 100 from the current level stat, with the classic or player-count factors; `El<e>Pct` < 100 draws on the unit seed per attack; out of the creation model | I |
| `Drain`, `coldeffect`, `Crit`, `NoShldBlock` | not at creation; hit time | [§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1) | I |

(fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_006538A0_MonLvlStats@0x006538A0, fn:sub_00573930_MonPlayerBonus@0x00573930,
fn:sub_0063EEF0_MonClassicDiffAdjust@0x0063EEF0, fn:sub_005A4F50_MonAttackStats@0x005A4F50, tbl:MonStats.txt:minHP,
tbl:MonStats.txt:Align)

- `[C]` **`DamageRegen` in the stat callback** (plan 0025 Phase 2). `MonStatsInit` gives the monster a stat list whose
  change callback `sub_0055B800_MonStatCallback` handles stat 7: on every change of max HP after creation (`old` > 0,
  `new ≠ old`, current HP > 0) it rescales stat 6 and, for a class with `DamageRegen` `r` ≠ 0, sets stat 74 =
  `((new >> 8)·r) >> 4`. So hpregen follows max HP through the classic nightmare/hell adjustment and the `hpmultiply`
  mod with flag 0, although neither writes stat 74 itself. Reproduced on every classic nightmare/hell creation and
  every `hpmultiply` call of the run. (fn:sub_0055B800_MonStatCallback@0x0055B800, 0x0055B8EC–0x0055B998,
  tbl:MonStats.txt:DamageRegen, run:2026-10-15-mon-stats,
  [monsters/0004 § 11](../findings/monsters/0004-stats.md#11-the-stat-callback-sub_0055b800_monstatcallback))
- `[I]` **Blank cells** are used as the value 0 everywhere at creation (no "none" test). The reversed ranges of
  § Blank patterns: `minionspawner1` (151 > 106) and `mephistospirit` (1267 > blank) take `lo` with no HP draw;
  `andariel`'s `El1MinD(N)` > `El1MaxD(N)` is an attack-time cell. Each is a required plan 0025 Phase 2 case if a run
  meets the class (Phase 0 ruling 5). (0x00573F7E–0x00573FC8, tbl:MonStats.txt:El1MinD(N))

## Quest TCs (plan 0032 Phase 0)

`python3 -I tools/quest_survey.py tcs workspace/merged/data/global/excel` (gate survey `quest`) lists every record
with `TCQuestId` ≠ 0 or a `TreasureClass4` cell, from `monstats.bin`; the counts are `[C]`.

| record | `Id` | `TCQuestId` | `TCQuestCP` | `TreasureClass4` / `(N)` / `(H)` | quest of that word, by the lead |
|---|---|---|---|---|---|
| 156 | `andariel` | 6 | 1 | `Andarielq`, `Andarielq (N)`, `Andarielq (H)` | Sisters to the Slaughter |
| 211 | `duriel` | 14 | 5 | `Durielq`, `Durielq (N)`, `Durielq (H)` | The Seven Tombs |
| 242 | `mephisto` | 22 | 0 | `Mephistoq`, `Mephistoq (N)`, `Mephistoq (H)` | The Guardian |
| 243 | `diablo` | 26 | 0 | `Diabloq`, `Diabloq (N)`, `Diabloq (H)` | Terror's End |
| 544 | `baalcrab` | 40 | 0 | `Baalq`, `Baalq (N)`, `Baalq (H)` | Eve of Destruction |

- `[C]` Exactly five records have a quest TC, and each has both a `TCQuestId` and all three `TreasureClass4` cells;
  every cell resolves to a TreasureClassEx row and differs from the record's `TreasureClass1` of the same difficulty
  (`quest_tc_classes=5`, `tc4_resolved=15`, `tc4_differs_tc1=15`). No other record has a `TCQuestId`.
- `[I]` **`TCQuestId` is a quest word of the save's quest record.** B6 passes it as the quest argument *q* of
  `QUESTRECORD_GetState`, which reads bit `16·q + s` of the player's record for the game's difficulty, that is bit
  *s* of word *q* of `Woo!` block *d* ([save/0002](../findings/save/0002-quest-words.md)). So B6 reads bits 15, 1 and
  `TCQuestCP` of word 6 (Andariel), 14, 22, 26 or 40 of the killer's record for the current difficulty.
  (fn:MONSTER_DropItems@0x005A6600, fn:QUESTRECORD_GetState@0x0065C310, tbl:MonStats.txt:TCQuestId)
- `[L]` The quest names per word (last column) come from `src:trevin-d2s-109` (its quest table); our code shows only
  the act grouping of the words. They agree with what the code does with words 10, 18 and 22 (the Horadric Staff
  parts, Khalim's parts, the Durance portal; save/0002).
- **What the save shows** (data only; `[C]` for the bits): the owner-played Nightmare save of run:2026-10-12-quality
  ([save/0002 § Corroboration](../findings/save/0002-quest-words.md#corroboration-data)) holds, after Andariel's and
  Duriel's kills, word 6 = bits 0, 3, 4, 13 and word 14 = bits 0, 2, 5, 13: Duriel's word has bit 5, his
  `TCQuestCP`, which his death script sets ([items/0010 § 3](../findings/items/0010-quest-drops.md#3-the-three-bits-for-the-five-quest-tc-classes)).
- `[I]` **The three bits B6 tests, per boss** ([items/0010 § 3](../findings/items/0010-quest-drops.md#3-the-three-bits-for-the-five-quest-tc-classes)).
  B6 uses `TreasureClass4` only when bits 15, 1 and `TCQuestCP` of word `TCQuestId` are all clear. Bit 1 is "done in
  this game, reward not yet taken"; bit 15 is set only by the save loader, as the copy of a saved bit 1, and is never
  cleared for these words; bit `TCQuestCP` is each script's own marker. Andariel (word 6, CP 1): her kill sets bit 1
  and Warriv's talk turns bit 1 into bit 0, so the quest TC returns in every later game once the quest is reported in
  the game it was done in, and never again if the game was saved before the report (bit 15). Duriel (14, CP 5): bit 5
  is set at the kill and never cleared. Mephisto (22), Diablo (26), Baal (40) (CP 0): the kill sets bit 0. So for
  those four the quest TC is used until the first kill in that difficulty. (fn:MONSTER_DropItems@0x005A6600,
  fn:QUESTRECORD_LoadBytes@0x0065C4D0, fn:sub_00596210_A1Q6_SetKilled@0x00596210,
  fn:sub_00595C60_A1Q6_NpcMessage@0x00595C60, fn:sub_0059D050_A2Q6_DurielDeath@0x0059D050,
  fn:sub_005BC140_A3Q6_SetDone@0x005BC140, tbl:MonStats.txt:TCQuestCP)
- `[I]` **Whose record.** The record read is that of the **resolved killer** only, never the party's: a player
  killer as is; a monster killer (summon, hireling) becomes its owner, overridden by the caster of a state whose
  [States](States.md) `exp` column is set when the killer carries one; a killer that is still not a player keeps the
  normal TC. The drop runs before the boss's quest script sees the death, so the kill that sets the bits still gets the
  quest TC. ([items/0010 § 2](../findings/items/0010-quest-drops.md#2-b6-the-quest-tc-switch-and-the-killer);
  fn:QUESTS_PlayerRecord@0x00543520, fn:sub_0063A690_UnitHasExpState@0x0063A690, fn:sub_0057CCB0_UnitKilled@0x0057CCB0,
  tbl:States.txt:exp)
- `[C]` The quest TCs' rows: Andariel's, Mephisto's, Diablo's and Baal's pick 7 with `NoDrop` 19 or 15 from an act's
  equipment and good TCs; Duriel's picks 5 with `NoDrop` 0 (`tsc` and `Durielq - Base`); each Hell row adds one item
  code (`tes`, `ceh`, `bet`, `fed`). Baal's Normal and Nightmare quest TCs draw from the next difficulty's Act 1 TCs,
  as his base TCs do.
- `[C]` **Quest items** (`quest_survey.py items`): 26 weapons/misc rows have a `quest` cell, 25 of them
  `questdiffcheck` 1 (all but the Horadric Cube `box`), 12 of those simple (`compactsave` 1), which store stat 356
  (`questitemdifficulty`, 2 bits) in a save ([d2s.md](../formats/d2s.md)). `[C]` The `quest` cell minus 1 is a
  **quest object id** (`g_QuestDescs` `+0x10`), not a record word: the item event and the item hook look the object
  up by `quest − 1`, and the gate's own `{word, quest}` pairs agree ([items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items), fn:QUESTS_FindById@0x00543640, data:g_QuestDescs@0x00731510, data:g_QuestItemWordGate@0x00731FEC). `[I]`
  Through `g_QuestDescs` the object is the record word itself only in Act I (`hdm` 4 → object 3, word 3); later it
  shifts (`hfh` 25 → object 24, word 27). `[I]` `questdiffcheck` gives the item stat
  356 = the game difficulty at creation, and such an item counts as held (for a script's "needs the item" test) only
  at stat 356 ≥ the current difficulty ([items/0010 § 5](../findings/items/0010-quest-drops.md#5-quest-items);
  fn:sub_00557AB0_ItemInitStats@0x00557AB0, fn:sub_00558110_PlayerFindItemByCode@0x00558110, tbl:Misc.txt:questdiffcheck).

## Combat columns (plan 0037 Phase 0)

The columns the combat code is expected to read when a monster attacks or is hit. This section extends
[§ Stat columns](#stat-columns-plan-0025-phase-0), whose [per-difficulty groups](#per-difficulty-column-groups) give
every offset (`[C]`, `excel_bin.py diff`) and whose [blank patterns](#blank-patterns) count the all-blank records; the
counts here are per attack mode and per column, from
`python3 -I tools/combat_survey.py monstats workspace/merged/data/global/excel` (gate survey `combat`), `[C]` as data.
"Set" means a non-blank `.txt` cell (a blank compiles to 0). A record's MonStats2 row is the one its `MonStatsEx` names.
**Meanings stay `[L]`** except the attack-time reading of [monsters/0004 § 9](../findings/monsters/0004-stats.md#9-to-hit-and-damage-at-attack-time-sub_005a4f50_monattackstats)
and the combat readers of [combat/0001](../findings/combat/0001-formulas.md), both at the end
([§ Combat readers](#combat-readers-plan-0037-phase-1-plan-0039-a1), plan 0039 A1).

### Per-mode damage and to-hit

| Mode | Columns (normal name; `+2d` per difficulty) | Records set n / nm / h | of them with the MonStats2 mode bit | `MaxD` = 0 while set |
|---|---|---|---|---|
| `A1` | `A1MinD` `+0x0DA`, `A1MaxD` `+0x0E0`, `A1TH` `+0x0C2` (u16) | 473 / 474 / 474 | `mA1`: 460 / 461 / 461 | 11 records in every difficulty |
| `A2` | `A2MinD` `+0x0E6`, `A2MaxD` `+0x0EC`, `A2TH` `+0x0C8` (u16) | 168 / 162 / 162 | `mA2`: 162 / 156 / 156 | 2 records |
| `S1` | `S1MinD` `+0x0F2`, `S1MaxD` `+0x0F8`, `S1TH` `+0x0CE` (u16) | 29 / 29 / 29 | `mS1`: 0 | none |

- `[C]` Value ranges when set (n / nm / h): `A1MaxD` 0..442 / 0..260 / 0..440, `A1TH` up to 3001 / 5000 / 5000;
  `A2MaxD` 0..271 / 0..320 / 0..320; `S1MinD` 1..100 / 40..120 / 40..120, `S1MaxD` 2..130 / 50..180 / 50..180,
  `S1TH` 95..250. (tbl:MonStats.txt:A1MaxD, tbl:MonStats.txt:S1TH)
- `[C]` The 11 records with `A1` cells set and `A1MaxD` 0 in all three difficulties are the hirelings and summons
  `navi`, `rogue2`, `rogue3`, `shadowwarrior`, `shadowmaster`, `spiritwolf`, `fenris`, `druidbear` and `fetishblow6..8`.
  (tbl:MonStats.txt:A1MaxD)
- `[C]` **No `S1` record has the `S1` mode.** The 29 records with `S1` cells (`sandraider1..10`, `scarab1..8`,
  `clawviper6..10`, `cr_lancer6..8` with the duplicate `cr_lancer8`, `duriel`, `uberduriel`) all have a `seq_*`
  `Sk1mode` (skills `Fire Hit`, `Jab`, `Charge`) and the MonStats2 `mSQ` bit, and none has `mS1`.
  (tbl:MonStats.txt:S1MinD, tbl:MonStats.txt:Sk1mode, tbl:MonStats2.txt:mSQ)
- `[C]` Records whose MonStats2 row has the mode but no cell of that mode in any difficulty: `A1` 110, `A2` 113, `S1`
  287 (mostly the non-combat and skill-only classes; a blank compiles to 0).

### Elemental attack groups `El1`..`El3`

`El<e>Mode` (`+0x0FE + e−1`, MonMode row, blank 255) and `El<e>Type` (`+0x101 + e−1`, [ElemTypes](ElemTypes.md) row,
blank 0) hold one value for all difficulties; `El<e>Pct`, `El<e>MinD`, `El<e>MaxD`, `El<e>Dur` one per difficulty
(§ Per-difficulty column groups).

| Group | Mode set (by [MonMode](MonMode.md) code) | Type set (by [ElemTypes](ElemTypes.md) code) | Mode present in the MonStats2 row |
|---|---|---|---|
| `El1` | 295: `A1` 230, `A2` 53, `S1` 12 | 295: `pois` 72, `cold` 56, `fire` 52, `ltng` 49, `mag` 20, `mana` 19, `stun` 11, `stam` 9, `rand` 6, `life` 1 | 268 |
| `El2` | 40: `A2` 19, `A1` 13, `SC` 8 | 40: `ltng` 24, `fire` 5, `cold` 4, `pois` 4, `frze` 2, `mag` 1 | 40 |
| `El3` | 0 | 0 | — |

| Group | Cells set n / nm / h: `Pct` · `MinD` · `MaxD` · `Dur` | Type set, `MinD` and `MaxD` blank (n / nm / h) |
|---|---|---|
| `El1` | 220 / 295 / 295 · 212 / 287 / 287 · 212 / 287 / 287 · 99 / 143 / 143 | 84 / 8 / 8 |
| `El2` | 27 / 40 / 40 · 23 / 40 / 40 · 23 / 40 / 40 · 5 / 10 / 10 | 17 / 0 / 0 |

- `[C]` Ranges when set: `El1Pct` 0..100, `El1MinD` 1..500, `El1MaxD` 10..600, `El1Dur` 7..3000 (all difficulties
  together); `El2Pct` 0..100, `El2MinD` 5..120, `El2MaxD` 10..190, `El2Dur` 25..1000. (tbl:MonStats.txt:El1Pct,
  tbl:MonStats.txt:El2Dur)
- `[C]` `El<e>Dur` is set only with the types `pois` (76 groups), `cold` (58), `stun` (11), `rand` (6), `frze` (2) and
  `ltng` (1), counting a group once per record. (tbl:MonStats.txt:El1Dur)
- `[C]` The 27 `El1` groups whose mode the MonStats2 row lacks: `succubus1..8` and `succubuswitch1..9` (`A2`, `mag`;
  their rows have no `mA2`) and `sandraider1..10` (`S1`, `fire`/`cold`; sequence monsters, above).
  (tbl:MonStats.txt:El1Mode, tbl:MonStats2.txt:mA2)
- `[C]` One record has `El1` cells with `El1Mode` and `El1Type` blank: `wakeofdestruction` (§ Blank patterns).

### Other combat columns

| Column | `.bin` field | Set n / nm / h | Values when set | Tag |
|---|---|---|---|---|
| `Drain` | `+0x0A0 + d` u8 | 477 / 475 / 474 | 15..100 (2 / 7 / 8 distinct) | [C] |
| `coldeffect` | `+0x168 + d` s8 | 588 / 579 / 576 | −50..0, −50..0, −50..33 | [C] |
| `ToBlock` | `+0x0A3 + d` u8 | 529 / 534 / 534 | 0..75, 3..75, 3..75 | [C] |
| `NoShldBlock` | `+0x00F` bit 2 | 18 records | 1 | [C] |
| `noRatio` | `+0x00C` bit 2 | 31 records | 1 | [C] |
| `Crit` | `+0x0A6` u8 | 550 records | always 5 | [C] |
| `DamageRegen` | `+0x1A0` u32 | 715 records | 0..15, non-zero in 673 | [C] |
| `SkillDamage` | `+0x0A8` u16 `skills` row, blank `0xFFFF` | 4 records | `Raven`, `Summon Fenris`, `Summon Grizzly`, `Summon Spirit Wolf` | [C] |
| `isMelee` | `+0x00C` bit 1 | 430 records | 1 | [C] |
| `rangedtype` | `+0x00F` bit 4 | 140 records | 1 | [C] |
| `deathDmg` | `+0x00E` bit 4 | 14 records | 1 | [C] |
| `MissA1`, `MissA2`, `MissS1`, `MissC` | `+0x03A`, `+0x03C`, `+0x03E`, `+0x046` u16 `missiles` row | 95, 47, 8, 8 records | of them `rangedtype`: 71, 21, 0, 8 | [C] |

- `[C]` All 18 `NoShldBlock` records have `ToBlock` > 0 in some difficulty (534 records do); 76 of the 534 have the
  MonStats2 `mBL` bit. (tbl:MonStats.txt:NoShldBlock, tbl:MonStats.txt:ToBlock)
- `[C]` 48 `rangedtype` records have `MissA1` and `MissA2` blank; 21 records are both `isMelee` and `rangedtype`.
  (tbl:MonStats.txt:rangedtype, tbl:MonStats.txt:MissA1)

### What is anchored so far

- `[I]` **The attack-time reader.** `sub_005A4F50_MonAttackStats` takes the attack mode and asks `MonLvlStats` for mask
  `0x10` in mode 5 (`A2`), `0x20` in modes 7 and 8 (`SC`, `S1`) and `0x08` otherwise; the masks select the `A2`, `S1`
  and `A1` triples, each scaled by the MonLvl `TH`/`DM` of the current level unless `noRatio`. It writes stats 21, 22
  and 19, and applies each `El<e>` whose `El<e>Mode` equals the mode, always when `El<e>Pct` ≥ 100, else after
  `RNG_Range(unit seed, 100) < El<e>Pct`; type 10 (`rand`) draws `Range(unit seed, 5)`. The other columns of this
  section: § Combat readers below. ([monsters/0004 § 4](../findings/monsters/0004-stats.md#4-monlvlstats-and-muldiv) and
  [§ 9](../findings/monsters/0004-stats.md#9-to-hit-and-damage-at-attack-time-sub_005a4f50_monattackstats);
  fn:sub_005A4F50_MonAttackStats@0x005A4F50, fn:sub_006538A0_MonLvlStats@0x006538A0, tbl:MonStats.txt:El1Pct)
- *Plan 0045 Phase 2 part 2* ([skills/0001 § 18](../findings/skills/0001-dispatch.md#18-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills),
  [monsters/0004 § 9](../findings/monsters/0004-stats.md#9-to-hit-and-damage-at-attack-time-sub_005a4f50_monattackstats)):
  `[C]` the mode's column choice above (`A2` for mode 5, `S1` for 7 and 8, `A1` otherwise; raw cells for `noRatio`) and
  stats 21, 22, 19 hold on 26 425 logged calls, another column set giving other values in 26 383 of them; the unit seed
  steps only by the `El<e>` chance rolls (run:2026-10-27-skills). `[I]` (objdump) For each `El<e>` the call passes
  `MonLvlStats` the mask `0x40 + e`, not `0x40 << e`, so **`El2` and `El3` are applied with El1's minimum, maximum and
  length**; their `El<e>Mode`, `El<e>Pct` and `El<e>Type` are their own. So `El2MinD`, `El2MaxD`, `El2Dur` and `El3MinD`, `El3MaxD`, `El3Dur`
  (each with its `(N)`/`(H)` cells) have no reader in `MonAttackStats`; no logged call applied an `El2` or `El3`. (0x005A51D7,
  0x005A5252–0x005A527A, fn:sub_005A4F50_MonAttackStats@0x005A4F50, tbl:MonStats.txt:El2MinD)
- `[I]` For a `noRatio` class the elemental masks write the raw `El<e>` cells to the output's `+0x24`/`+0x28`, not to
  the elemental slots (monsters/0004 § 4). `MonAttackStats` reads the elemental min and max at `+0x2C`/`+0x30`, so a
  `noRatio` monster's `El` attack has min = max = 0 and keeps only its duration (`+0x34`)
  ([combat/0001 § 12](../findings/combat/0001-formulas.md#12-branches-difficulty-game-type-players-hirelings-player-against-player),
  0x00653BC2–0x00653C2D, 0x005A5160, struct:MonLvlStatsOut+0x2C).
- `[I]` **The mode `MonAttackStats` sees** (plan 0037 Phase 0 question): `MonSetMode` passes the new mode for every mode
  but 3; mode 5 reads `A2`, 7 and 8 read `S1`, every other mode (14 `sequence` included) `A1`. So a sequence monster's
  `S1` triple and an `El<e>` with `El<e>Mode` `S1` (the 10 `sandraider*`) or `A2` without an `A2` mode (the 17
  `succubus*`) apply only through a skill do-function that passes that mode (Fire Hit 8, Charge 4/5/8, Jab 8, …), never
  through a plain mode change ([combat/0001 § 12b (a)](../findings/combat/0001-formulas.md#12b-answers-to-the-archivists-phase-0-questions-backlog-2026-10-16-ae),
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:sub_005A4F50_MonAttackStats@0x005A4F50, tbl:MonStats.txt:El1Mode).
- `[L]` By the names: `ToBlock` the monster's block chance (read at creation as stat 20, § Readers; the block roll
  reads stat 20), `DamageRegen` its life regeneration (read at creation, § Readers). **(plan 0039 A1)** `Drain`, `coldeffect`, `NoShldBlock` and `Crit` left this lead: they have
  readers, below.
- `[I]` **(plan 0045 P1.1)** `SkillDamage` (`+0x0A8`): for a monster with an owner whose own class names a skill here (the
  four summon classes), `MonAttackStats` adds that skill's physical minimum and maximum (`SKILLS_GetPhysMin/Max >> 8`)
  and its to-hit to the A1/A2/S1 attack before the classic and player-count adjustments (which unit's skill level is
  read is not resolved there)
  ([skills/0001 § 13](../findings/skills/0001-dispatch.md#13-monster-skill-use); fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050).

### Combat readers (plan 0037 Phase 1, plan 0039 A1)

From [combat/0001](../findings/combat/0001-formulas.md) §§ 4, 5, 7–10 and 12b (static reading), and § 15 for the cases
run:2026-10-16-combat reproduced. `d` is the game's difficulty. The flag tests go through `MONSTATS_IsBoss`
(`+0x0C` bit 6), `MONSTATS_IsPrimeEvil` (`+0x0C` bit 7), `MONSTATS_IsDemon` (`+0x0D` bit 5) and `MONSTATS_IsUndead`
(`+0x0D` bit 3 **or** bit 4, so `lUndead` and `hUndead` count alike in combat). (fn:MONSTATS_IsBoss@0x0063E9F0,
fn:MONSTATS_IsPrimeEvil@0x0063EDC0, fn:MONSTATS_IsDemon@0x0063E940, fn:MONSTATS_IsUndead@0x0063E990)

- `[C]` **`Crit`** (`+0xA6`): for a monster attacker with `Crit` ≠ 0, one inlined draw on the attacker's seed in the
  damage build, and `(u8)(low % 100) < Crit` doubles physical, fire, lightning, magic, cold and poison (overlay 54 on
  the defender, packet `+0x60 |= 0x10`). Reproduced in 89 doublings. (fn:sub_005A5560_MonCritDouble@0x005A5560,
  run:2026-10-16-combat, tbl:MonStats.txt:Crit)
- `[I]` **`Drain`** (`+0xA0 + d`): the leech factor `D` of a **monster defender** in `COMBAT_Leech`; `D = 0` means
  nobody leeches from it, `D ≠ 100` scales every gain by `D / 100`. A non-monster defender counts as 100.
  ([combat/0001 § 9](../findings/combat/0001-formulas.md#9-leech-stun-cold-freeze-poison-burn),
  fn:COMBAT_Leech@0x0057C420, tbl:MonStats.txt:Drain)
- `[I]` **`coldeffect`** (`+0x168 + d`, s8): read by `sub_0057AF30_MonColdEffect` when the monster is chilled. 0 means
  no chill (cold returns at once); otherwise the chill sets stats 67, 68 and 69 to it, and a value < 0 also lets
  `MonsterColdDivisor` divide the length. **Freeze needs `coldeffect` < 0** (`COMBAT_ApplyFreeze`), then
  `MonsterFreezeDivisor` divides its length. Non-monsters use −50. (fn:sub_0057AF30_MonColdEffect@0x0057AF30,
  fn:COMBAT_ApplyCold@0x0057AF80, fn:COMBAT_ApplyFreeze@0x0057B230, tbl:MonStats.txt:coldeffect)
- `[I]` **`NoShldBlock`** (`+0x0F` bit 2): a monster's block chance is stat 20 (from `ToBlock`) when this bit is set or
  it holds a shield, else 0; capped at 75. ([combat/0001 § 4](../findings/combat/0001-formulas.md#4-block-evade-weapon-block-dodge-avoid),
  fn:sub_00622720_UnitBlockChance@0x00622720, tbl:MonStats.txt:NoShldBlock)
- `[I]` **`Velocity`** (`+0x32`) = 0 makes `COMBAT_ApplyStun` return without stunning. (fn:COMBAT_ApplyStun@0x0057AAE0,
  0x0057AB17–0x0057AB44, tbl:MonStats.txt:Velocity)
- `[I]` **`killable`** (`+0x0D` bit 7) = 0: `COMBAT_ApplyDamage` returns for that monster defender before the
  reductions, the events and any life change. (fn:COMBAT_ApplyDamage@0x0057C6C0, 0x0057C6D5–0x0057C78E,
  tbl:MonStats.txt:killable)
- `[I]` **`boss`**: the percent `P` is `HireableBossDamagePercent` for a hireling hitting a boss; a boss is never
  stunned, gets cold instead of freeze, takes crushing blow at divisor 8 (like superuniques; 4 otherwise); stat 115
  (target defence to 0) does not apply to it, and stat 116 (target defence reduced) is halved against it. Open
  wounds does **not** test `boss` (only the champion/unique type flags). (fn:COMBAT_DamagePercent@0x0057C060,
  fn:COMBAT_ApplyStun@0x0057AAE0, fn:COMBAT_ApplyFreeze@0x0057B230, fn:STATEVENT_CrushingBlow@0x005BFFC0,
  fn:COMBAT_ToHitTargetMods@0x0057D8A0, tbl:MonStats.txt:boss)
- `[I]` **`primeevil`**: an attacker with it against a defender with `Unit+0xC4` bit 31 deals `P` = 200 % to a hireling
  defender and 400 % otherwise. (fn:COMBAT_DamagePercent@0x0057C060, 0x0057C129–0x0057C132, tbl:MonStats.txt:primeevil)
- `[I]` **`demon`**: stat 121 adds to the attacker's enhanced damage and stat 123 to its attack rating against a demon,
  and packet flag `0x200` bypasses the demon's DR, MDR and absorb. **`lUndead`/`hUndead`**: stat 122 and the blunt +50 %
  (`UndeadDmgBonus`), stat 124 to attack rating, packet flag `0x100` bypasses, and an attacker under state 47
  (sanctuary) zeroes the undead's physical resistance. Flag `0x400` bypasses for a monster that is neither.
  ([combat/0001 § 7](../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions),
  fn:COMBAT_BuildDamage@0x0057B7D0, fn:sub_0057B660_UndeadDmgBonus@0x0057B660, fn:COMBAT_ToHitTargetMods@0x0057D8A0,
  fn:COMBAT_ApplyReductions@0x0057C1E0, fn:COMBAT_ResistFor@0x0057BE00, tbl:MonStats.txt:demon, tbl:MonStats.txt:lUndead)

## Timing (plan 0050 Phase 0)

The columns that name a monster's animation, its modes and its speeds (values from the `.bin` over the 734 records;
`python3 -I tools/anim_survey.py monsters workspace/merged` and `monseq`, survey keys `mon_*` and `seq_*`):

| Column | `.bin` field | Observed | Meaning | Tag |
|---|---|---|---|---|
| `Code` | `+0x010` 4-byte code | 210 distinct (`SK` 49, `CR` 24, `xx` 23, …) | the animation token: the first part of the `animdata.d2` record name | [C] layout; the join below `[C]`, the game's use `[L]` |
| `MonStatsEx` | `+0x018` u16, `monstats2` row | 0..603, set in all 734 | the [MonStats2](MonStats2.md#timing-plan-0050-phase-0) row whose `m<mode>` bits and `BaseW` complete the record name | [C] layout |
| `Velocity` | `+0x032` u16 | 0..15 (16 distinct), 4 blank (`gorgon1..4`); 0 in 99 | walk speed | [C] layout; `[I]` readers in [§ Readers at creation](#readers-at-creation-and-at-attack-time-plan-0025-phase-1) (the bonus, the stun test) |
| `Run` | `+0x034` u16 | 0..20 (18 distinct), 4 blank; 0 in 99; below `Velocity` in 7 | run speed | [C] layout; `[C]` as a map, Charge's base ([§ Readers](#readers-at-creation-and-at-attack-time-plan-0025-phase-1)) |
| — | `+0x036`, `+0x038` s16 | 0 in the file | walk and run values derived at load from the animation data and `Velocity`/`Run` | `[I]` (`sub_00650F00_MonStatsSpeeds`, [§ Fields with no `.txt` column](#fields-with-no-txt-column)) |
| `Sk1mode`..`Sk8mode` | `+0x180 + k` u8, `monmode` row; `+0x188 + 2k` s16, `monseq` ordinal | 775 cells set: mode 14 (`xx`) 319, `S1` 112, `S2` 106, `A1` 93, `SC` 62, `A2` 48, `S3` 24, `S4` 6, `NU` 5; ordinal 1..59 in the 319 `xx` cells, −1 otherwise | the mode skill *k* plays, or the sequence | [C] layout ([§ Columns](#columns)) |
| `spawnmode` | `+0x024` u8, `monmode` row | 52 set: `NU` 33, `S1` 19; blank 255 | the mode a spawned monster starts in | [C] layout; `[L]` |
| `El1Mode`..`El3Mode` | `+0x0FE + e` u8, `monmode` row | `El1Mode` 295 set (`A1` 230, `A2` 53, `S1` 12), `El2Mode` 40 (`A2` 19, `A1` 13, `SC` 8), `El3Mode` none; blank 255 | the mode the elemental attack adds to | [C] layout ([§ Combat columns](#combat-columns-plan-0037-phase-0)) |

- `[C]` **The record join.** Each row's `Code` + the [MonMode](MonMode.md#timing-plan-0050-phase-0) `token` of every mode
  its MonStats2 `m<mode>` bit sets + MonStats2 `BaseW` (else `HTH`) names an `animdata.d2` record for all 5 109 flagged
  modes outside `xx` (5 057 with `BaseW`, 52 with `HTH`); per mode in [MonMode § Timing](MonMode.md#timing-plan-0050-phase-0).
- `[C]` **The sequences.** The 319 `xx` cells name 54 of the 60 `monseq` sequences; 249 of the 5 408 (row, step) pairs
  name a frame at or past the row's record ([MonSeq § Sequences](MonSeq.md#sequences)).
- `[I]` **The mode columns the mode machine reads** ([anim/0001 § 10](../findings/anim/0001-modes-frames.md#10-monster-modes); values from the
  [§ Columns](#columns) rows):
  - `SplGetModeChart` (`+0x1A5` u8, 1 in 20 rows): only when it is set does `sub_005A78A0_MonModeRecord` test the
    class against its override switch, which gives the ten classes below their own mode records for some of
    `A1`, `A2`, `S1`–`S4` (fn:sub_005A78A0_MonModeRecord@0x005A78A0, tbl:MonStats.txt:SplGetModeChart). `[C]` By the
    `.bin` all ten classes the switch names have the column set: 243 `diablo`, 333 `diabloclone`, 403 `trappedsoul1`,
    417 `shadowwarrior`, 418 `shadowmaster`, 543 `baalthrone`, 544 `baalcrab`, 570 `baalclone`, 705 `uberdiablo`, 709
    `uberbaal`. `[I]` What each branch gives is [anim/0001 § 10](../findings/anim/0001-modes-frames.md#10-monster-modes)'s
    reading (corrected at P1.2 for the one-row shift of the P1.1 text,
    [backlog](../backlog/archive/2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md)): 243, 333
    and 705 take the attack mode records (`g_MonModeRecords` rows) 17 (S3) and 16 (S4); 403 takes rows 18 (A1, A2) and 19 (S1, S2), both
    ending in a mode-8 command whose `cmd` byte is 101 with MonStats2 `S1mv` set, else 100; 417 and 418 row 20 for S4;
    543, 544, 570 and 709 row 7 for S3. (fn:sub_005A78A0_MonModeRecord@0x005A78A0, 0x005A7923–0x005A7990)
  - `SplEndGeneric` (`+0x1A6` u8, 1 in 27 rows): at the end of a listed mode of a listed base class (110 `vulture1` S1,
    247 `frogdemon1` SQ, 136 `batdemon1` S3/S4, 230/231 any, 118 `willowisp1` WL, 403 any) `MonModeEndGeneric` only
    queues the AI event instead of the neutral command. (fn:sub_005A8030_MonModeEndGeneric@0x005A8030,
    tbl:MonStats.txt:SplEndGeneric)
  - `SplEndDeath` (`+0x1A4` u8, 1 or 2 in 9 rows): at the end of `DT`, after mode 12, 1 changes the class to its
    `minion1`, 2 kills the owner. (0x005A72B0, tbl:MonStats.txt:SplEndDeath)
  - `aidel`, `aidel(N)`, `aidel(H)` (`+0x04F`..`+0x051` u8, 1..15, 0 in the 18 blank rows): when the next AI
    event is not later than now, `MonModeStartNeutral` re-queues it at `T +` the delay of the difficulty (15 when the
    cell is 0), or at `T + 45` under state 21 `stunned`. The AI itself is
    phase (5)'s ([plan 0052](../plans/0052-monster-ai.md)). (fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0,
    tbl:MonStats.txt:aidel)
- `[C]` A new monster's stat 67 `velocitypercent` is 75, and the `champion`/`possessed` (+20) and `fast`/`fanatic`
  (`clamp(2048 ÷ Velocity − 128, 10, 100)`) mods add to it only when `Velocity` > 0
  ([monsters/stats](../specs/monsters/stats.md), [ItemStatCost § Timing](ItemStatCost.md#timing-plan-0050-phase-0)).
- `[C]` **The two-frame S1–S4 records with an event** (plan 0050 P1.2 review; `python3 -I tools/anim_survey.py twoframe
  workspace/merged`, keys `twoframe_*`): seven, all speed 256 — `K9S1HTH`, `K9S2HTH`, `K9S3HTH`, `K9S4HTH` (event 2 at
  frame 1), `E9S2HTH` (event 1 at frame 1), `9AS1HTH`, `9AS2HTH` (event 2 at frame 0). 24 MonStats records have `Code`
  `K9`, `E9` or `9A` (case-insensitive), 10 of them classes below 410. Every MonStats2 `S1mv`..`S4mv` bit of the 24 is
  0, and none has the `npc` bit. Per row (record index, `Id`, the `m<mode>` bits set among the listed records,
  `Velocity`):

  | Code | Below 410 | `m<mode>` set | `Velocity` | Walk record |
  |---|---|---|---:|---|
  | `K9` | 153 `hellmeteor` | none | 0 | `K9WLHTH`, speed 256 |
  | `K9` | 332 `invisospawner` | `mS1` | 0 | `K9WLHTH`, speed 256 |
  | `9A` | 326 `trap-firebolt`, 329 `trap-poisoncloud`, 330 `trap-lightning`, 355 `seventombs`, 369 `trap-nova` | `mS1` | 0 | none |
  | `9A` | 327 `trap-horzmissile`, 328 `trap-vertmissile` | `mS1`, `mS2` | 0 | none |
  | `9A` | 366 `compellingorb` | none | 0 | none |

  | Code | From 410 | `m<mode>` set | `Velocity` | Walk record |
  |---|---|---|---:|---|
  | `E9` | 410 `wakeofdestruction`, 415 `infernosentry` | `mS2` (and `mS1`, whose `E9S1HTH` has 15 frames and no event) | 0 | none |
  | `K9` | 414 `invisopet`, 516–519 `catapultspotter1..4` | `mS1` | 0 | `K9WLHTH`, speed 256 |
  | `K9` | 417 `shadowwarrior`, 418 `shadowmaster` | `mS1`..`mS4` | 0 | `K9WLHTH`, speed 256 |
  | `K9` | 425 `plaguepoppy`, 426 `cycleoflife`, 427 `vinecreature` | `mS1` | 7 | `K9WLHTH`, speed 256 |
  | `K9` | 545 `baaltaunt`, 574 `worldstoneeffect` | none | 12 | `K9WLHTH`, speed 256 |

  Every row is its own `BaseId` but 517–519 (base 516, `Velocity` 0), so `Velocity` scales nothing and the derived
  walk base (`+0x036`) of the `K9` rows is the walk record's speed, 256 `[I]` ([anim/0002 § 3.5](../findings/anim/0002-rates.md#35-the-monster-walk-and-run-base-monstatsspeeds-at-load),
  fn:sub_00650F00_MonStatsSpeeds@0x00650F00). `[I]` By anim/0002 a class below 410 takes the moving branch in S1–S4
  (`r = vbase · max(B_FRW + stat 67, 25) / 100`, no cap on the factor, only with a path) and a mode whose `*mv` bit is
  0 is scheduled; a scheduled mode fires no frame event once `r ≥ 256 (F − S)`, 512 for these
  two-frame records from frame 0 ([anim/0002 § 7](../findings/anim/0002-rates.md#7-the-breakpoint-function-derived-not-copied));
  with `vbase` 256, `r ≥ 512` needs `B_FRW + stat 67 ≥ 200`, against the new-monster 75 that the
  `champion`/`fast` terms leave unchanged at `Velocity` 0 (the bullet above). So the classic candidates are the
  `invisospawner`'s S1 and, their walk base being 256 too (next bullet), the seven `9A` rows' S1 (and S2 for
  `trap-horzmissile` and `trap-vertmissile`); from 410 the S1–S4
  rate is capped at 175 (`r ≤ 448`) except through a move-first skill ([anim/0002 § 1](../findings/anim/0002-rates.md#1-entry-the-record-and-the-order-of-the-tests)).
  (tbl:MonStats.txt:Code, tbl:MonStats2.txt:S1mv, tbl:MonStats.txt:Velocity)
  Whether a `9A` row or the `invisospawner` reaches stat 67 ≥ 200 at run time (an aura or state) and runs S1 with a path
  is a run-time question, not a data one.
- `[I]` **The `9A` and `E9` rows' walk base** ([anim/0003 § 1.1](../findings/anim/0003-movement-gates.md#11-a-class-with-no-walk-record-the-lanea50t-reviews-reads),
  answering this section's former `[L]`). These rows have no walk record; `sub_00650F00_MonStatsSpeeds` takes the walk
  speed with `ANIMDATA_Lookup(mode 2, type 1, base class, no inventory)`, which returns the table's fallback record
  when the name has no record (frames 2048, speed 256,
  [anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback)). So a class
  whose `<Code>WL<BaseW>` record is missing gets walk base `+0x036` = 256, scaled by `Velocity(i) / Velocity(b)` only
  when its base row `b ≠ i` and `Velocity(b) > 0` (unsigned `div`), then `0 → 0`, capped at `0x7FFF`; below class 410
  its run base `+0x038` is `+0x036(b) / 2` (signed), 128 for such a base, and from 410 the `RN` lookup, falling back to
  256 the same way. Every `9A` and `E9` row is its own `BaseId` (above), so the eight classic `9A` rows (326–330, 355,
  366, 369; the finding names the seven with `mS1`; `compellingorb` 366 has the code in lower case, `9a`, and no walk
  record under either case) get walk base 256 and run base 128, and the two `E9` rows (410, 415) walk base 256 and,
  from the `RN` lookup with no `E9RN` record, run base 256.
  (fn:sub_00650F00_MonStatsSpeeds@0x00650F00, fn:ANIMDATA_Lookup@0x0066A9B0, 0x00650F80–0x00650F9D,
  0x00650FBE–0x00650FD4, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:BaseId)
- How `Velocity`/`Run` and stat 67 become the per-frame step is [anim/0003 § 1–2](../findings/anim/0003-movement-gates.md#1-velocities) `[I]` (plan 0050 Phase 1.3); how the rate stats change a
  monster's modes is [anim/0002](../findings/anim/0002-rates.md) `[I]`.

## AI columns (plan 0052 Phase 0)

The columns the monster AI reads or may read, with what the data alone shows. Survey: `python3 -I tools/ai_survey.py
summary|rows <excel-dir>` (gate survey `ai`); per AI row the records, slots and skills are in the
[MonAI index](MonAI.md#the-index). Offsets and widths are the § Columns table's (`[C]` by diff). Meanings are `[L]`
unless a finding is cited.

| Columns | `.bin` field | Observed (734 records) | What is anchored | Tag |
|---|---|---|---|---|
| `AI` | `+0x01E` u16 | 146 of the 148 [MonAI](MonAI.md) rows; none blank; every cell resolves to the row of the same name (case-exact) | the index of `g_MonAiTable` on `MonAiEntryGet`'s `EDX` = 0 branch (the other branch reads a second table, [MonAI § The second table](MonAI.md#the-second-table-at-0x0073d358-found-at-the-lanea52-review)), whose `+8` word is the AI function ([items/0001](../findings/items/0001-tc-resolution.md), fn:sub_005B15D0_MonAiEntryGet@0x005B15D0, data:g_MonAiTable@0x0073CA18) | [C] data; use [I] |
| `aidel`, `aidel(N)`, `aidel(H)` | `+0x04F`..`+0x051` u8 | Normal: 15 (710 records), 1 (5), 6 (1), 0 (18 blank); Nightmare and Hell take 9 and 10 values (Nightmare mostly 14, Hell mostly 13); 455 records differ between difficulties | `MonModeStartNeutral` (also the refusal fallback) sets mode 1; **when the next AI event is not later than now**, it re-queues the event at `T + 45` under state 21 (`stunned`), else at `T +` the delay (`aidel(N)`/`aidel(H)` by difficulty when `Game+0x6A` or `Game+0x74` is non-zero), **15 when the cell is 0**; the finding names no re-queue when the next event is later than now ([anim/0001 § 10](../findings/anim/0001-modes-frames.md#10-monster-modes), fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0, struct:Game+0x6A) | [I] |
| `aidist`, `aidist(N)`, `aidist(H)` | `+0x052`..`+0x054` u8 | set on 2 records only: 242 `mephisto` and 704 `ubermephisto`, 0 / 40 / 46 | none | [L] |
| `aip1`..`aip8` (each n, N, H) | `+0x056 + 6(k−1) + 2d` u16 | records with slot k non-zero: 573, 551, 526, 461, 327, 144, 106, 82 (k = 1..8); 588 records set a slot; 497 differ between difficulties; blank and 0 both store 0 | the AI parameters per difficulty (plan 0052 P1 reads them per AI); the inactive save keeps "AI parameters" ([drlg/lifecycle § G](../specs/drlg/lifecycle.md#g-the-records), fn:sub_00541FE0_InactiveMonAiSave@0x00541FE0) | layout [C]; meaning [L] |
| `Skill1..8`, `Sk1mode..Sk8mode`, `Sk1lvl..Sk8lvl` | `+0x170` u16, `+0x180` u8 and `+0x188` s16, `+0x198` u8 | 393 records name a skill, 775 cells in 97 AI rows; 319 of the cells give a `seq_*` mode (`xx` and a sequence); 5 cells have `Sk lvl` 0 | at creation each `Skill` ≥ 0 with `Sk lvl` > 0 is added at `Sk lvl` + `MonsterSkillBonus` (§ Readers at creation, [monsters/0004](../findings/monsters/0004-stats.md)); which skill the AI uses and when is plan 0052's | [I] creation; AI use [L] |
| `switchai` | `+0x00E` bit 0 | 585 records | none | [L] |
| `threat` | `+0x04E` u8 | 1..14, 144 blank (§ Columns) | none | [L] |

- `[C]` The five `Sk lvl` 0 cells: `bloodgolem` (290) `BloodGolem`, `bonewall` (344) `Bone Wall`, `chargeboltsentry`
  (411) `Shock Field`, `infernosentry` (415) `Wake of Fire Sentry`, `druidhawk` (419) `Raven`: all summon records
  (MonAI reach S). `[I]` The creation reader above skips them; whether the summon code gives them a level is plan 0052's
  summons batch. (tbl:MonStats.txt:Sk1lvl)
- `[C]` `shadowmaster` (418) sets `aip8` to 279 in Normal (0 in Nightmare and Hell), the Skills row of Shadow Master;
  row 143 `ShadowMasterNoInit` labels its `*aip8` `summoning skill` (a lead, [MonAI § Leads](MonAI.md#leads)).
  (tbl:MonStats.txt:aip8)
- `[C]` In 13 AI rows the records disagree on which `aip` slots they set (`ai_aip_slots_differ=13`): 1, 8, 11, 30, 35,
  36, 61, 67, 114, 119, 122, 133, 142. A catalogue entry reads each record's slots, not one per AI.
  (tbl:MonStats.txt:aip1)

- `[I]` **Readers named by the pool-A batch** ([ai/0002](../findings/ai/0002-pool-a.md) § 2, plan 0052 P1.2 batch 1, AI
  rows 2-16 and 142; the per-AI meanings stay in the finding, this table claims none):
  - `aip1`..`aip8`: each think function of those rows reads its slots per record and difficulty, one pseudocode block per
    row (§ 2.1-2.15; e.g. row 8 `aip5` and `aip6`, row 11 `aip1` and `aip5`).
  - `aidel`, `aidel(N)`, `aidel(H)`: row 8 (`SandRaider`, § 2.7) waits `aidel[d] + 1` frames at its overlay.
  - `Velocity`, `Run`: row 11 (`Baboon`, § 2.10) takes a speed bonus `Run * 100 / Velocity - 100` when the quotient is at
    least 100, capped at 120 (both read from `+0x32` and `+0x34`; a `Velocity` of 0 gives no bonus).
  - `Skill1`..`Skill3`, `Sk1mode`..`Sk3mode`: row 8 `Skill1` (Fire Hit); row 13 `Skill1` (Resurrect, mode 14, no
    `Sk1mode`) and `Skill2` with `Sk2mode`; row 15 `Skill1..3`; rows 16 and 142 `Skill1` (§ 2.7, 2.11, 2.13-2.15).

- `[I]` **Readers named by the pool-B batch** ([ai/0003](../findings/ai/0003-pool-b.md) § 2, plan 0052 P1.2 batch 2, AI rows 17-30; the per-AI
  meanings stay in the finding, this table claims none):
  - `lUndead` (`+0x0D` bit 3): `sub_005F2A00_AiGreaterMummyCb`, row 22's corpse and wounded search (§ 2.6), unless the
    searcher is Radament (MonStats row 229), which takes any undead through `MONSTATS_IsUndead`.
    (fn:sub_005F2A00_AiGreaterMummyCb)
  - `Velocity` (`+0x32`) and `Run` (`+0x34`): `sub_005F4A70_AiVampire`, row 28 ([§ 2.12](../findings/ai/0003-pool-b.md#212-row-28-vampire-0x005f4a70)): the
    flee override parameter `clamp(Run * 100 / Velocity - 100, 0, 120)` for the step away while fleeing (state 2). The
    guard "only when `Velocity` > 0" is the reverser's request wording, not in § 2.12 (routed, backlog 2026-10-30).
    (fn:sub_005F4A70_AiVampire@0x005F4A70)
  - `Skill4` (`+0x176`) and `Sk4mode` (`+0x183`): the vampire's Fireball and VampireMissile pair, drawn 50/50 with
    `Skill1`/`Sk1mode`.
  - `aip1`..`aip6`, read per record and difficulty, by row (finding section in brackets): 17 `aip1` (§ 2.1); 18 `aip3`,
    `aip4` (§ 2.2); 19 `aip2` (§ 2.3); 20 `aip3`, `aip5` (§ 2.4); 21 `aip1`, `aip2`, `aip3`, `aip5` (§ 2.5); 22 `aip1`..`aip5`
    (§ 2.6); 23 `aip1`..`aip5` (§ 2.7); 24 `aip3`, `aip5` (§ 2.8); 25 `aip1`..`aip3` (§ 2.9); 26 `aip1`..`aip5` (§ 2.10); 27
    `aip2`..`aip6` (§ 2.11); 28 `aip1`..`aip5` (§ 2.12); 29 `aip1`..`aip5` (§ 2.13); 30 `aip1`..`aip4` (§ 2.14). Row 28's
    `aip5` is a bit set, not a count: bit 0 the Fireball/Missile pair, bit 1 `Skill2`, bit 2 `Skill3` (3 in `vampire1`, 5 in
    `vampire2`, 7 in `vampire3`, `vampire4` and `vampire6`..`vampire9`, 1 in `vampire5`).

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
- ~~(plan 0037 Phase 0) Which mode a **sequence** monster's `S1` triple is read in, and which offsets the attack code
  reads for a `noRatio` class's `El<e>` damage~~ answered `[I]` by combat/0001 § 12b (a), (b) ([§ What is anchored so
  far](#what-is-anchored-so-far)): `A1` in the sequence mode 14, `S1` only through a do-function passing 7 or 8; the
  `noRatio` `El` min and max are 0. Which mode a sequence's frames run under is plan 0037's Phase 2 case.
