# PlrMode (`data/global/excel/PlrMode.txt` → `plrmode.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` d2exp (a mixed-archive pair, [README](README.md#source-and-shape))   **Rows:** 20 (no `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `23106da08603bc215624e2837f3990b5ed4b5521bbe8b4a80b0ea6b6502fb8e3`, `.bin` `1279e74a55c4c3890a689564c573cf6fb154d631724d66ba01ed8559cebbda2d`
> **Doc status:** layout complete (plan 0037 Phase 0, every byte placed); meanings `[L]`

## Purpose

The twenty player animation modes (`Death`, `Neutral`, `Walk`, `Run`, `Get Hit`, `Town Neutral`, `Town Walk`,
`Attack1`, `Attack2`, `Block`, `Cast`, `Throw`, `Kick`, `Skill1`..`Skill4`, `Dead`, `Sequence`, `Knock back`), each
with a two-letter token and a code. The row index is the **mode number** that [Skills](Skills.md) `anim` and
`seqtrans` store. Readers expected: `combat/formulas` (plan 0037), the attack modes of a player's normal attack, throw
and kick; `anim/timing` (plan 0050), the mode's frames, events and rate ([§ Timing](#timing-plan-0050-phase-0)).

## Row identity

- `[C]` The `.bin` is a u32 record count (20) and 20 records of 52 bytes, one per `.txt` row in order; the count equals
  the 20 `.txt` data rows. `[I]` The stock loader reads it with record size 52 (call site `0x0065AE3E`); a 4-byte load
  (`0x00612BB6`) runs only under `-txt` ([data/0001 § 3–4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables),
  fn:DATATBLS_LoadCodeLists@0x00612750).
- `[C]` **The row index is the stored mode number, resolved by `Code`.** Skills `anim` and `seqtrans` diff with 0
  mismatches as indices of this table's `Code` rows; the 116 `anim` cells and 98 `seqtrans` cells `SQ` store 18,
  which only `Code` gives (`SQ` is no `Token`). (tbl:Skills.txt:anim, tbl:PlrMode.txt:Code)
- `[C]` `Name` and `Code` are unique; `Token` is not (`GH` three times, rows 4, 18, 19).
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` it writes a `plrmode.bin`
  byte-identical to the shipped one (shipped in d2exp), so this layout is the one the binary's compiler produces
  ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). The `-txt`-only code-list load of the same `.txt` adds no file of its own.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel plrmode`: 20 records × 2 mapped
fields = **40 cells, 0 mismatches**; `excel_bin.py unknown … plrmode` lists only `+0x024` (16 B, zero in every
record). Same shape as [ObjMode](ObjMode.md) and [MonMode](MonMode.md).

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `Name` | str ≤ 12 chars, 20 distinct | `+0x000` `char[32]` | mode name | — | [C] |
| `Token` | str 2 chars, 18 distinct (`GH` ×3) | `+0x020` 4-byte code, space padded | animation token | — | [C] |
| `Code` | str 2 chars, 20 distinct | — (not compiled) | the code Skills names the mode by | key of Skills `anim`, `seqtrans` | [C] (absence) |
| — | — | `+0x024` 16 B | zero in every record | — | [C] value |

- `[C]` **The mixed-archive pair agrees.** The shipped `.bin` is d2exp's; the d2exp `.txt` has only `Name` and `Token`,
  and the patch_d2 `.txt` adds `Code` with `Name` and `Token` unchanged (identical cells in all 20 rows). So the diff
  of the patch_d2 `.txt` against the d2exp `.bin` is 40 cells, 0 mismatches, and either `.txt` may be cited for
  `Name`/`Token`; `Code` exists only in the patch_d2 `.txt` and only feeds compiling. (tbl:PlrMode.txt:Token)
- `[C]` The record holds `Token`: rows 18 `Sequence` (code `SQ`) and 19 `Knock back` (code `KB`) store `GH  `.

`[C]` The rows and their users (`python3 -I tools/combat_survey.py codes workspace/merged/data/global/excel`):

| Row | `Code` | `Token` | `Name` | Skills `anim` | Skills `seqtrans` |
|---:|---|---|---|---:|---:|
| 0 | DT | DT | Death | 0 | 0 |
| 1 | NU | NU | Neutral | 0 | 0 |
| 2 | WL | WL | Walk | 0 | 0 |
| 3 | RN | RN | Run | 0 | 0 |
| 4 | GH | GH | Get Hit | 0 | 0 |
| 5 | TN | TN | Town Neutral | 0 | 0 |
| 6 | TW | TW | Town Walk | 0 | 0 |
| 7 | A1 | A1 | Attack1 | 48 | 64 |
| 8 | A2 | A2 | Attack2 | 1 | 1 |
| 9 | BL | BL | Block | 0 | 0 |
| 10 | SC | SC | Cast | 141 | 143 |
| 11 | TH | TH | Throw | 5 | 5 |
| 12 | KK | KK | Kick | 3 | 3 |
| 13 | S1 | S1 | Skill1 | 6 | 6 |
| 14 | S2 | S2 | Skill2 | 9 | 9 |
| 15 | S3 | S3 | Skill3 | 4 | 4 |
| 16 | S4 | S4 | Skill4 | 1 | 1 |
| 17 | DD | DD | Dead | 0 | 0 |
| 18 | SQ | GH | Sequence | 116 | 98 |
| 19 | KB | GH | Knock back | 0 | 0 |

## Timing (plan 0050 Phase 0)

The table has no timing column: a mode's frame count, speed and event bytes are in `animdata.d2`
([animdata](../formats/animdata.md)), one record per class token, mode `Token` and weapon class. `[C]` The join
(`python3 -I tools/anim_survey.py players workspace/merged`; survey keys `plr_*`): for each of the 7 class tokens of
`plrtype.txt` (`AM`, `SO`, `NE`, `PA`, `BA`, `DZ`, `AI`), each row's `Token` (`+0x020`, 4-byte code) and each of the
14 `weaponclass.txt` codes, the record `<class><Token><wclass>`. Rows 18 and 19 store `GH`, so they name row 4's
records and are not counted again. 756 record names start with a class token; 755 are joined, 1 is not (`AMWK1HS`,
mode token `WK`, which no row has; [cof § Files](../formats/cof.md#files) has its COF). Every row 0..17 has records
(`plr_modes_none=0`).

| Row | `Code` | Records (7 classes) | Classes with one | `frames` | `speed` | Event bytes (value: count, frames) |
|---:|---|---:|---:|---|---|---|
| 0 | DT | 7 | 7 | 20..28 | 176..256 | — |
| 1 | NU | 62 | 7 | 6..8 | 96..184 | — |
| 2 | WL | 62 | 7 | 8..10 | 136..288 | — |
| 3 | RN | 62 | 7 | 8 | 168..256 | — |
| 4 | GH | 62 | 7 | 5..8 | 192..256 | 1: 4, frame 0 |
| 5 | TN | 62 | 7 | 10..16 | 64..128 | — |
| 6 | TW | 62 | 7 | 8..10 | 128..288 | — |
| 7 | A1 | 62 | 7 | 11..24 | 208..256 | 1: 48, frames 6..14; 2: 14, frames 6..11 |
| 8 | A2 | 46 | 7 | 12..24 | 208..256 | 1: 46, frames 6..14 |
| 9 | BL | 25 | 7 | 3..6 | 88..256 | — |
| 10 | SC | 62 | 7 | 14..20 | 208..256 | 1: 47, frames 7..13; 2: 15, frames 9..13 |
| 11 | TH | 24 | 7 | 12..20 | 256 | 2: 24, frames 6..10 |
| 12 | KK | 62 | 7 | 12..13 | 224..256 | 1: 62, frames 4..6 |
| 13 | S1 | 57 | 7 | 9..17 | 208..256 | 1: 42, frames 2..10 |
| 14 | S2 | 11 | 2 | 8..14 | 128..256 | 1: 1, frame 9; 2: 10, frame 4 |
| 15 | S3 | 14 | 2 | 10..12 | 256 | 1: 4, frames 7..8 |
| 16 | S4 | 6 | 2 | 12..16 | 208..256 | 1: 2, frame 6; 2: 4, frames 8..9 |
| 17 | DD | 7 | 7 | 1 | 256 | — |

- `[C]` In every class the bow and crossbow `A1` records carry event 2 and every melee weapon class 1 ([animdata § Event bytes](../formats/animdata.md#event-bytes)). Per class and weapon
  class the frame counts differ (Amazon `A1`: `hth` 13, `1hs` 16, `2hs` 20, `bow` 14; the full grid is the tool's
  `players` output).
- `[I]` **Which record a player reads** ([anim/0001 § 2](../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback)):
  the [PlrType](PlrType.md) token of the class, this table's `Token` of the mode (replaced by `GH` for rows 18 and 19,
  `g_PlrModeTokenRemap`) and the weapon class: CharStats `baseWClass` unless a weapon is in the right or left hand, then
  the weapon's (or a dual class); rows 0 and 17 take `hth`, row 11 (`TH`) with a weapon class other than `1hs`, `1ht`,
  `1js`, `1jt`, `1ss`, `1st` takes `hth`. A name with no record gets the built-in fallback (2048 frames, speed 256, no
  events). Row 18 (`SQ`) reads its frames from a sequence table indexed by Skills `seqnum`, not from `animdata.d2`
  ([anim/0001 § 5](../findings/anim/0001-modes-frames.md#5-sequences)). (fn:COMPOSIT_BuildCofName@0x0064F5B0, fn:UNIT_AnimSetRecord@0x00620F00)
- `[I]` **How the mode runs** ([anim/0001 § 9](../findings/anim/0001-modes-frames.md#9-player-modes)): rows 0, 4, 7–16 and 18 queue their frame events
  (codes 1–4) and their end once, at the mode start (`SUNIT_ScheduleModeEvents`); rows 2, 3, 6 and 19 run a move frame
  every game frame; rows 1, 5 and 17 queue nothing. A mode's end goes to neutral (town neutral in a town); row 0 goes to
  row 17. The rates (`frames` and `speed` against the rate stats) are plan 0050 P1.2. (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  fn:sub_00581020_PlayerModeEnd@0x00581020)

## Interpretation notes

- `[L]` The normal attack (Skills row 0, `Attack`) has `anim` `A1`, `Kick` (row 1) `KK`, `Throw` (row 2) `TH`, `Left
  Hand Swing` (row 5) `S3` and `Left Hand Throw` (row 4) `S4` ([Skills § Combat survey](Skills.md#combat-survey-plan-0037-phase-0)).
  Which mode the attack code tests (for example `A1` against `A2` for the two weapon swings) is plan 0037 Phase 1.

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load (as for [ObjMode](ObjMode.md#open-questions)).
