# compcode (`data/global/excel/compcode.txt` → `compcode.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 115   **Record:** 4 B
> **sha256:** `.txt` `a26b8437a13e5777801d8794ed49d103cdd5d274afbd013f09a107ca11ba2a4b`, `.bin` `dc089b0317e25a2ecc0d42a86c6a763457efa31b2f62ebaa8e125d923c80a1cd`
> **Doc status:** complete for layout; art and identity columns only; semantics `[L]`

## Purpose

A list of 3-character component codes (`nil`, `lit`, `med`, `hev`, `hvy`, `hax`, `axe`, …). **This doc
covers art and identity only** (plan 0009 Phase 2). Leads: no lead; derived from data.

## Row identity

- `[C]` Key column `code`, unique in all 115 rows. `component` (the editor name) is not unique:
  `heavy` names both `hev` (row 3) and `hvy` (row 4).
- `[I]` Unlike the other code lists, `compcode.bin` is loaded in every run: `DATATBLS_LoadCodeLists`
  loads it unconditionally before its `-txt`-only calls (`0x00612750`, call site `0x006127CF`,
  [data/0001 §3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)).
  What reads it afterwards is not traced.

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel compcode`: 115 records × 1
mapped field, 0 mismatches. The 4-byte record is the space-padded code, so every byte is covered.

| Column | Observed type / range | `.bin` field | Meaning (`[L]`) | References | Layout tag |
|---|---|---|---|---|---|
| `component` | str, 114 distinct, len ≤ 17 | — (editor name; not in the record) | description | — | — |
| `code` | str, 115 distinct, len 3 | `+0x000` char[4] code | DCC component code | DCC file names | [C] |

## Interpretation notes

- `[C]` 112 of the 115 codes occur as the component part of at least one DCC file name in `merged/`
  (`<token><layer><code>…dcc` under a unit's layer directory); `nil`, `red` and `mlk` don't.
- `[C]` The list is not complete: 69 component codes that occur in DCC names are not in it (for
  example the helm code `cap`, `chars/ba/hd/bahdcap…dcc` in `d2char`). So `compcode` is not the set of
  codes the item art index needs: the index takes the code from the item row (`alternategfx`) or from
  [armtype](armtype.md), and only checks the file exists.

## Open questions

- `[L]` What the game uses `compcode` for at run time (it is loaded unconditionally). Owner: reverser
  ([backlog](../backlog.md), plan 0009 Phase 2 entry).
