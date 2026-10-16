# compcode (`data/global/excel/compcode.txt` → `compcode.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 115   **Record:** 4 B
> **sha256:** `.txt` `a26b8437a13e5777801d8794ed49d103cdd5d274afbd013f09a107ca11ba2a4b`, `.bin` `dc089b0317e25a2ecc0d42a86c6a763457efa31b2f62ebaa8e125d923c80a1cd`
> **Doc status:** complete for layout; art and identity columns only; semantics `[I]` ([items/0003](../findings/items/0003-item-graphics.md))

## Purpose

A list of 3-character component codes (`nil`, `lit`, `med`, `hev`, `hvy`, `hax`, `axe`, …). **This doc
covers art and identity only** (plan 0009 Phase 2). Leads: no lead; derived from data, then code ([items/0003](../findings/items/0003-item-graphics.md)).

## Row identity

- `[C]` Key column `code`, unique in all 115 rows. `component` (the editor name) is not unique:
  `heavy` names both `hev` (row 3) and `hvy` (row 4).
- `[I]` Unlike the other code lists, `compcode.bin` is loaded in every run: `DATATBLS_LoadCodeLists`
  loads it unconditionally before its `-txt`-only calls (`0x00612750`, call site `0x006127CF`,
  [data/0001 §3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300)).
  What reads it afterwards: see Interpretation notes.
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` it writes a `compcode.bin`
  byte-identical to the shipped one (shipped in patch_d2) ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3).

## Columns

`[C]` `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel compcode`: 115 records × 1
mapped field, 0 mismatches. The 4-byte record is the space-padded code, so every byte is covered.

| Column | Observed type / range | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `component` | str, 114 distinct, len ≤ 17 | — (editor name; not in the record) | description | — | — |
| `code` | str, 115 distinct, len 3 | `+0x000` char[4] code | `[I]` DCC component code of a **monster** layer, by row index from MonStats2 | DCC file names, [MonStats2](MonStats2.md) `HDv`… lists | [C] |

## Interpretation notes

- `[I]` `compcode` is read only for monster components: `COMPCODE_GetCode(i)` (row *i* → its 4-byte code)
  has two callers, both resolving a MonStats2 layer's component list (count `+0x015 + layer`, row bytes
  `+0x026 + 12·layer + n`) to the DCC code of a monster unit. No item path reads it; player worn art takes
  its codes from the item record (`alternategfx`/`code`) and [armtype](armtype.md). ([items/0003](../findings/items/0003-item-graphics.md) § 6,
  fn:COMPCODE_GetCode@0x006117D0, fn:sub_00664860_MonComponentCode@0x00664860,
  fn:sub_00664930_MonStatsComponentCode@0x00664930, tbl:MonStats2.txt:HDv)

- `[C]` 112 of the 115 codes occur as the component part of at least one DCC file name in `merged/`
  (`<token><layer><code>…dcc` under a unit's layer directory); `nil`, `red` and `mlk` don't.
- `[C]` The list is not complete: 69 component codes that occur in DCC names are not in it (for
  example the helm code `cap`, `chars/ba/hd/bahdcap…dcc` in `d2char`). So `compcode` is not the set of
  codes the item art index needs: the index takes the code from the item row (`alternategfx`) or from
  [armtype](armtype.md), and only checks the file exists.

## Open questions

- Answered `[I]` by [items/0003](../findings/items/0003-item-graphics.md): what the game uses `compcode` for (monster components, Interpretation
  notes). Not followed: the per-act code replacement in `sub_00664860_MonComponentCode` (two hard-coded
  tables, items/0003 § 6).
