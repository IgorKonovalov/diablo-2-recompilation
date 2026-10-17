# colors (`data/global/excel/colors.txt` → `colors.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 21   **Record:** 4 B
> **sha256:** `.txt` `4c0e1274eab79daf5ecec10f12fea7fc11cce4db6d37f30ca0b4456dcad632ee`, `.bin` `bcee42342aa6a813dba63c32592e570ff7feba2b13d3840a5e84f9b875e5365c`
> **Doc status:** complete for layout; art and identity columns only; semantics `[L]`

## Purpose

The list of item colour-shift codes (`whit`, `lgry`, … `bwht`). **This doc covers art and identity
only** (plan 0009 Phase 2): the table is nothing but a code list. Unique and set rows
(`chrtransform`, `invtransform`) and affix rows (`transformcolor`) name a row by its code. How a code
becomes a palette remap: [item-palette.md](../formats/item-palette.md) (plan 0009 Phase 3). Leads: no lead; derived from data.

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
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` the game loads this table as one of
  the 15 code lists of `DATATBLS_LoadCodeLists` and writes a `colors.bin` byte-identical to the shipped one, which
  ships in d2exp ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). That a stock run never loads it stays `[I]`: the file ships, so its absence could not show it (data/0001 §
  S1b row 30). (fn:DATATBLS_LoadCodeLists@0x00612750)

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
- `[L]` Index *n* selects the *n*-th 256-byte map of an `items/palette/*.dat` file. The 21 × 256 split
  is `[C]` from the data and a colour-family check agrees with this row order in 159 of 168 maps, but
  the pairing has no code anchor ([item-palette.md](../formats/item-palette.md#which-map-is-which-colour)).

## Open questions

- `[L]` How the game turns a colour index into a palette remap, and which `.dat` serves which view.
  Owner: reverser ([backlog](../backlog.md), plan 0009 Phase 2 entry).
