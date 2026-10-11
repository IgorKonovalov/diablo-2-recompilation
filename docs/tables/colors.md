# colors (`data/global/excel/colors.txt` → `colors.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 21   **Record:** 4 B
> **sha256:** `.txt` `4c0e1274eab79daf5ecec10f12fea7fc11cce4db6d37f30ca0b4456dcad632ee`, `.bin` `bcee42342aa6a813dba63c32592e570ff7feba2b13d3840a5e84f9b875e5365c`
> **Doc status:** complete for layout; art and identity columns only; semantics `[L]`

## Purpose

The list of item colour-shift codes (`whit`, `lgry`, … `bwht`). **This doc covers art and identity
only** (plan 0009 Phase 2): the table is nothing but a code list. Unique and set rows
(`chrtransform`, `invtransform`) and affix rows (`transformcolor`) name a row by its code. How a code
becomes a palette remap is plan 0009 Phase 3 (`items/palette/*.dat`). Leads: no lead; derived from data.

## Row identity

- `[C]` Key column `Code`, a 4-character code, unique in all 21 rows. References store the **row index**
  (0..20) as a u8, `0xFF` for a blank cell: [UniqueItems](UniqueItems.md) `+0x038`/`+0x039`,
  [SetItems](SetItems.md) `+0x040`/`+0x041`, and the affix tables' `transformcolor` `+0x056`
  (`excel_bin.py diff` over every record of each).
- `[I]` In a stock run the game does **not** load `colors.bin`: `DATATBLS_LoadCodeLists` loads it only
  under `-txt`, to resolve code cells while compiling `.txt` tables
  ([data/0001 §3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  `0x00612750`, call site `0x00612A90`). The compiled tables carry the row index, so the row **order** is
  what matters at run time.

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel colors`: 21 records × 1 mapped
field, 0 mismatches. The record is 4 bytes and `Code` fills it, so every byte is covered.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `Transform Color` | str, 21 distinct, len ≤ 13 | — (editor name; not in the record) | display name (`White`, `Light Grey`, …) | — | — |
| `Code` | str, 21 distinct, len 4 | `+0x000` char[4] code | colour-shift code | referenced by `chrtransform`, `invtransform`, `transformcolor` | [C] |

## Interpretation notes

- `[C]` Row order: `whit lgry dgry blac lblu dblu cblu lred dred cred lgrn dgrn cgrn lyel dyel lgld dgld
  lpur dpur oran bwht` (indices 0..20).
- `[L]` That index *n* selects the *n*-th 256-byte map of an `items/palette/*.dat` file (8 files of
  21 × 256 bytes) is a lead from the sizes alone; plan 0009 Phase 3 checks it.

## Open questions

- `[L]` How the game turns a colour index into a palette remap, and which `.dat` serves which view.
  Owner: reverser ([backlog](../backlog.md), plan 0009 Phase 2 entry).
