# MonMode (`data/global/excel/MonMode.txt` → `monmode.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 16 (no `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `2663c45b5ca74916db0114335babe7fc6dd9d357322892df501f7850e4385b52`, `.bin` `3129eca38b8f1c9c7b2d466f154d2ba11ca20dd9889b732966b0ef71f6639307`
> **Doc status:** layout complete (plan 0037 Phase 0, every byte placed); meanings `[L]`

## Purpose

The sixteen monster animation modes (`death`, `neutral`, `walk`, `gethit`, `attack1`, `attack2`, `block`, `cast`,
`skill1`..`skill4`, `dead`, `knockback`, `sequence`, `run`), each with a two-letter token and a code. The row index
is the **mode number**: [MonStats](MonStats.md) `El<e>Mode`, `Sk<k>mode` and `spawnmode`, [Skills](Skills.md)
`monanim` and `summode`, and [MonStats2](MonStats2.md) `ResurrectMode` store it, and the MonStats2 per-mode columns
(`mDT`..`mRN`, `dDT`..`dRN`, `*mv`) are laid out in this row order. Readers expected: `combat/formulas` (plan 0037), the
mode that selects a monster's `A1`/`A2`/`S1` damage columns and the mode an `El<e>` group fires in; `anim/timing`
(plan 0050), the mode's frames, events and rate ([§ Timing](#timing-plan-0050-phase-0)).

## Row identity

- `[C]` The `.bin` is a u32 record count (16) and 16 records of 52 bytes, one per `.txt` row in order; the count equals
  the 16 `.txt` data rows. `[I]` The stock loader reads it with record size 52 (call site `0x0065B18C`); a second,
  4-byte load (`0x00612B40`) runs only under `-txt`, as a code list for compiling
  ([data/0001 § 3–4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables),
  fn:DATATBLS_LoadCodeLists@0x00612750, fn:DATATBLS_LoadTable@0x006122F0).
- `[C]` **The row index is the stored mode number.** The MonStats `El<e>Mode`, `spawnmode` and `Sk<k>mode`, Skills
  `monanim`/`summode` and MonStats2 `ResurrectMode` fields diff with 0 mismatches as indices of this table's rows
  (`excel_bin.py diff`, gate survey `excel_layout`); MonStats2's `mDT`..`mRN` bits follow the row order
  ([MonStats2 § Columns](MonStats2.md#columns)). (tbl:MonStats.txt:El1Mode, tbl:Skills.txt:monanim,
  tbl:MonStats2.txt:ResurrectMode)
- `[C]` `name`, `token` and `code` are each unique except `token` (`GH` twice, rows 3 and 13).
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` it writes a `monmode.bin`
  byte-identical to the shipped one (shipped in d2exp and patch_d2), so this layout is the one the binary's compiler
  produces ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). The `-txt`-only code-list load of the same `.txt` adds no file of its own.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monmode`: 16 records × 2 mapped
fields = **32 cells, 0 mismatches**; `excel_bin.py unknown … monmode` lists only `+0x024` (16 B, zero in every record).
The record has ObjMode's shape ([ObjMode](ObjMode.md)).

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `name` | str ≤ 9 chars, 16 distinct | `+0x000` `char[32]` | mode name | — | [C] |
| `token` | str 2 chars, 15 distinct (`GH` ×2) | `+0x020` 4-byte code, space padded (`DT  `) | animation token (names the mode's graphics) | — | [C] |
| `code` | str 2 chars, 16 distinct | — (not compiled) | the code other tables name the mode by | key of the references above | [C] (absence) |
| — | — | `+0x024` 16 B | zero in every record | — | [C] value |

- `[C]` **The record holds `token`, not `code`.** They differ only in row 13: `knockback` has token `GH`, code `KB`, and
  its record stores `GH  `. (tbl:MonMode.txt:token, tbl:MonMode.txt:code)
- `[C]` Whether a reference resolves by `code` or by `token` cannot be told from the data: the only row where they
  differ (13, `KB`) is named by no cell, and `GH` resolves to row 3 either way. The layouts use `code`.

`[C]` The rows and their users (`python3 -I tools/combat_survey.py codes workspace/merged/data/global/excel`, counts of
non-blank cells naming the row):

| Row | `code` | `token` | `name` | MonStats `El<e>Mode` | MonStats `Sk<k>mode` | MonStats `spawnmode` | Skills `monanim` | Skills `summode` | MonStats2 `ResurrectMode` |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 0 | DT | DT | death | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | NU | NU | neutral | 0 | 5 | 33 | 1 | 10 | 568 |
| 2 | WL | WL | walk | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | GH | GH | gethit | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | A1 | A1 | attack1 | 243 | 93 | 0 | 41 | 0 | 0 |
| 5 | A2 | A2 | attack2 | 72 | 48 | 0 | 11 | 0 | 0 |
| 6 | BL | BL | block | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | SC | SC | cast | 8 | 62 | 0 | 29 | 0 | 0 |
| 8 | S1 | S1 | skill1 | 12 | 112 | 19 | 29 | 21 | 10 |
| 9 | S2 | S2 | skill2 | 0 | 106 | 0 | 24 | 1 | 0 |
| 10 | S3 | S3 | skill3 | 0 | 24 | 0 | 8 | 0 | 0 |
| 11 | S4 | S4 | skill4 | 0 | 6 | 0 | 0 | 0 | 0 |
| 12 | DD | DD | dead | 0 | 0 | 0 | 0 | 0 | 0 |
| 13 | KB | GH | knockback | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | xx | xx | sequence | 0 | 0 | 0 | 214 | 0 | 31 |
| 15 | RN | RN | run | 0 | 0 | 0 | 0 | 0 | 0 |

`Sk<k>mode` counts only the cells that name a mode; the others name a `monseq` sequence (`seq_*`) and store 0 here
([MonStats § Columns](MonStats.md#columns)). 1 841 cells in all.

## Timing (plan 0050 Phase 0)

The table has no timing column: a mode's frame count, speed and event bytes are in `animdata.d2`
([animdata](../formats/animdata.md)), one record per monster token, mode `token` (`+0x020`, 4-byte code) and weapon
class. `[C]` The join (`python3 -I tools/anim_survey.py monsters workspace/merged`; survey keys `mon_*`): for each of
the 734 MonStats rows (every one has a `Code` and a `MonStatsEx`), each mode whose [MonStats2](MonStats2.md) `m<mode>`
bit is set, the record `<Code><token><BaseW>`, else `<Code><token>HTH`. 5 109 flagged modes outside `xx`: 5 057 find
the `BaseW` record, 52 the `HTH` one (the death modes `DT`/`DD` of the `GM`, `FE` and `FK` classes, whose `BaseW` is
`2hs` or `1hs`), none finds nothing (`mon_miss=0`). `xx` is flagged on 492 rows and has no record of its own (a
sequence names other modes' frames, [MonSeq](MonSeq.md)). 1 143 record names are used, of 1 214 that start with a
MonStats `Code`.

| Row | `code` | Rows with the bit | Distinct records | `frames` | `speed` | Event bytes (value: records, frames) |
|---:|---|---:|---:|---|---|---|
| 0 | DT | 645 | 158 | 1..200 | 0..256 | — |
| 1 | NU | 711 | 211 | 1..60 | 0..256 | — |
| 2 | WL | 599 | 157 | 1..29 | 56..344 | — |
| 3 | GH | 524 | 104 | 1..16 | 96..260 | 1: 7, frame 0 |
| 4 | A1 | 571 | 119 | 2..38 | 96..260 | 1: 96, frames 3..19; 2: 21, 0..16; 3: 2, 14 |
| 5 | A2 | 275 | 53 | 2..38 | 48..256 | 1: 39, 1..18; 2: 14, 1..12; 3: 1, 16 |
| 6 | BL | 78 | 13 | 2..10 | 96..256 | 1: 1, frame 5 |
| 7 | SC | 61 | 16 | 2..19 | 152..256 | 1: 7, 7..11; 2: 16, 3..16 |
| 8 | S1 | 287 | 89 | 1..129 | 40..256 | 1: 7, 3..24; 2: 11, 0..11; 3: 1, 3 |
| 9 | S2 | 82 | 21 | 2..130 | 128..256 | 1: 4, 1..15; 2: 7, 0..11 |
| 10 | S3 | 35 | 13 | 2..23 | 128..256 | 1: 3, 6..13; 2: 3, 1..14 |
| 11 | S4 | 20 | 6 | 1..21 | 152..256 | 1: 2, 4; 2: 1, 1 |
| 12 | DD | 650 | 162 | 1..3 | 128..256 | — |
| 13 | KB | 498 | 86 | 1..16 | 96..260 | 1: 6, frame 0 (the `GH` records: `KB`'s token is `GH`) |
| 14 | xx | 492 | 0 | — | — | — |
| 15 | RN | 73 | 19 | 1..22 | 80..272 | — |

- `[I]` **The code's per-mode table.** `sub_005A78A0_MonModeRecord` returns a 16-byte record per mode from the table at
  `0x006E2260` (start, frame and end functions at `+0`, `+4`, `+8`): `A1`, `A2`, `SC`, `S1`, `S2` start with
  `sub_005A75C0_MonModeStartSkill` and frame with `sub_005A7670_MonAttackFrame`, which runs the do function with no
  event-code test; `xx` (14) starts at `0x005A7870` and frames with `sub_005A8670_MonSeqFrame`
  ([skills/0001 § 5](../findings/skills/0001-dispatch.md#5-the-frame-when-the-do-function-runs),
  fn:sub_005A78A0_MonModeRecord@0x005A78A0).
- `[I]` **How often the frame function runs** ([anim/0001 § 10](../findings/anim/0001-modes-frames.md#10-monster-modes)): every game frame for `WL`,
  `KB`, `xx` and `RN`, and for `A1`, `A2`, `SC`, `S1`–`S4` when the MonStats2 `*mv` bit of the mode is set; else once
  per frame event (codes 1–4) of the record, queued at the mode start with the end after the last step
  (`SUNIT_ScheduleModeEvents`); `NU`, `S3`, `S4` and `DD` queue nothing (their record's `schedule` is 0).
  (fn:sub_005A6B10_MonModeEveryFrame@0x005A6B10, fn:sub_005A7C20_MonSetMode@0x005A7C20)
- `[I]` **The game's name** ([anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback)): MonStats `Code`, this
  table's `token` (`KB` → `GH`, `g_MonModeTokenRemap`) and MonStats2 `BaseW`, except `hth` in rows 0 and 12 unless
  MonStats2 `compositeDeath`, and `hth` with no MonStats2 record; a name with no record gets the built-in fallback
  (2048 frames, speed 256), not an `HTH` retry. `[C]` By that rule every flagged mode outside `xx` names a record too
  (`mon_rule_miss=0`; the 52 `HTH` joins above are death modes without `compositeDeath`). (fn:COMPOSIT_BuildCofName@0x0064F5B0)

## Interpretation notes

- `[L]` By the names, rows 4, 5 and 8 (`A1`, `A2`, `S1`) are the modes the MonStats damage triples `A1*`, `A2*`, `S1*`
  belong to, and an `El<e>Mode` names the mode in which the `El<e>` damage is added (A1, A2, S1 and SC are the only
  ones named, [MonStats § Combat columns](MonStats.md#combat-columns-plan-0037-phase-0)). Which mode number the
  attack code compares with is plan 0037 Phase 1.
- `[L]` `sequence` (`xx`) is the mode of a `monseq` sequence skill (214 Skills `monanim` cells).

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load, as for [ObjMode](ObjMode.md#open-questions).
- `[L]` Which column the `-txt` code-list load (`0x00612B40`, 4-byte record) reads; it decides whether a reference
  resolves by `code` or `token` when they differ (row 13). Not reachable on stock data.
