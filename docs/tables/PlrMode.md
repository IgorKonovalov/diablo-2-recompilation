# PlrMode (`data/global/excel/PlrMode.txt` → `plrmode.bin`)

> **Source archive:** `.txt` patch_d2, `.bin` d2exp (a mixed-archive pair, [README](README.md#source-and-shape))   **Rows:** 20 (no `Expansion` marker)   **Record:** 52 B (`0x34`)
> **sha256:** `.txt` `23106da08603bc215624e2837f3990b5ed4b5521bbe8b4a80b0ea6b6502fb8e3`, `.bin` `1279e74a55c4c3890a689564c573cf6fb154d631724d66ba01ed8559cebbda2d`
> **Doc status:** layout complete (plan 0037 Phase 0, every byte placed); meanings `[L]`

## Purpose

The twenty player animation modes (`Death`, `Neutral`, `Walk`, `Run`, `Get Hit`, `Town Neutral`, `Town Walk`,
`Attack1`, `Attack2`, `Block`, `Cast`, `Throw`, `Kick`, `Skill1`..`Skill4`, `Dead`, `Sequence`, `Knock back`), each
with a two-letter token and a code. The row index is the **mode number** that [Skills](Skills.md) `anim` and
`seqtrans` store. Readers expected: `combat/formulas` (plan 0037), the attack modes of a player's normal attack, throw
and kick; animation timing is ADR-0014 phase (5).

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

## Interpretation notes

- `[L]` The normal attack (Skills row 0, `Attack`) has `anim` `A1`, `Kick` (row 1) `KK`, `Throw` (row 2) `TH`, `Left
  Hand Swing` (row 5) `S3` and `Left Hand Throw` (row 4) `S4` ([Skills § Combat survey](Skills.md#combat-survey-plan-0037-phase-0)).
  Which mode the attack code tests (for example `A1` against `A2` for the two weapon swings) is plan 0037 Phase 1.

## Open questions

- `[L]` Whether the 16 zero bytes at `+0x024` are filled at load (as for [ObjMode](ObjMode.md#open-questions)).
