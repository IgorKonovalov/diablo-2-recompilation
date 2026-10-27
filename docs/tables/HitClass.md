# HitClass (`data/global/excel/HitClass.txt` → `hitclass.bin`)

> **Source archive:** d2exp (`.txt` and `.bin`)   **Rows:** 14 (no `Expansion` marker)   **Record:** 4 B
> **sha256:** `.txt` `57d43b716f248a7f72a4fef39b774569ecaccd644396fe3deebf29206b3b6b30`, `.bin` `ad4b04eb8b90e52eda5b589eee7cc5d509c2a104e7259de541550a8e53dd6d4b`
> **Doc status:** layout complete (plan 0050 Phase 0); meanings `[L]`

## Purpose

The **hit class** code list: `None`, `Hand To Hand` `hth`, `One Hand Swing vs. Small` `1hss`, `… vs. Large` `1hsl`,
the two-hand swings `2hss`/`2hsl`, the thrusts `1ht`/`2ht`, `club`, `staf`, `bow`, `xbow`, `claw` and `Overlay`
`over`. The row index is the number [Weapons](Weapons.md) `hit class` stores; [MonStats2](MonStats2.md) `HitClass` holds
a number in the same range. Readers expected: `anim/timing` and `combat` (plan 0050 Phase 1; the "hit class" that
[combat](../specs/combat/README.md) owes to the animation phase). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (14) and 14 four-byte records, one per `.txt` row in order: `Code` as a
  4-byte space-padded code; row 0 (`None`) has a blank code and stores four spaces.
  `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel hitclass`: 14 records × 1 mapped field =
  **14 cells, 0 mismatches**; `excel_bin.py unknown … hitclass` lists no uncovered byte. (tbl:HitClass.txt:Code)
- `[I]` `hitclass.bin` is loaded only under `-txt`, by `DATATBLS_LoadCodeLists` (call site `0x00612A17`, 4-byte
  record), to resolve the hit-class columns while compiling `.txt`
  ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  fn:DATATBLS_LoadCodeLists@0x00612750). The pinned game's `-direct -txt` compile writes a byte-identical
  `hitclass.bin` ([experiments § run:2026-10-15-cube-saves, addendum 2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3)).
- `[C]` **The row index is the stored hit class of Weapons.** Weapons `hit class` (`+0x13C` u8, a `Code` reference)
  diffs with 0 mismatches as an index of this table's rows (layout `weapons`, gate survey `excel_layout`).

## Columns

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `Hit Class` | str, 14 distinct, len ≤ 24 | — (not compiled) | editor name | — | [C] (absence) |
| `Code` | str, 13 distinct + 1 blank, len ≤ 4 | `+0x000` 4-byte code, space padded | the code other tables name the class by | key of Weapons `hit class` | [C] |

`[C]` The rows and their users (`excel_bin.py` decode of `weapons.bin` and `monstats2.bin`):

| Row | `Code` | `Hit Class` | Weapons `hit class` | MonStats2 `HitClass` (number) |
|---:|---|---|---:|---:|
| 0 | — | None | 0 | 0 |
| 1 | hth | Hand To Hand | 6 | 6 |
| 2 | 1hss | One Hand Swing vs. Small | 27 | 0 |
| 3 | 1hsl | One Hand Swing vs. Large | 86 | 566 |
| 4 | 2hss | Two Hand Swing vs. Small | 18 | 0 |
| 5 | 2hsl | Two Hand Swing vs. Large | 39 | 0 |
| 6 | 1ht | One Hand Thrust | 38 | 0 |
| 7 | 2ht | Two Hand Thrust | 21 | 0 |
| 8 | club | Club | 15 | 0 |
| 9 | staf | Staff | 14 | 0 |
| 10 | bow | Bow | 30 | 0 |
| 11 | xbow | Crossbow | 12 | 0 |
| 12 | claw | Claw | 0 | 37 |
| 13 | over | Overlay | 0 | 0 |

- `[C]` Every one of the 306 Weapons rows names a class (1..11); `claw` and `over` are named by no weapon.
- `[C]` MonStats2 `HitClass` (`+0x014` u8) is an integer column, not a code reference: 1 (6 rows), 3 (566), 12 (37),
  0 blank. Read as this table's rows those are `hth`, `1hsl` and `claw`; that the game reads it that way is `[L]`.

## Interpretation notes

- `[L]` **Two other `HitClass` columns are a different encoding.** Skills `HitClass` (`+0x134` u32: 0 ×351, then 3,
  96, 109, 112, 141, 157 once each) and Missiles `HitClass` (`+0x094` u16: 0 ×492, 2 ×2, 6 ×21, 10 ×47, 32 ×58,
  48 ×7, 64 ×46, 80 ×1, 176 ×10) are not row indices of this table (most values are past row 13). `[I]` A Skills
  row's non-zero `HitClass` is copied into the damage packet's hit-class field `+0x60`
  ([skills/0001](../findings/skills/0001-dispatch.md), [skills/0018](../findings/skills/0018-monster-8c.md)), where the
  elemental damage adds `0x20` fire, `0x30` cold, `0x40` lightning, `0x50` poison, `0x60` stun and a monster's `Crit`
  doubling sets `0x10` when the high nibble is clear (`SKILLS_AddElemToPacket`, `sub_005A5560_MonCritDouble`,
  [combat/0001](../findings/combat/0001-formulas.md)). So the packet's high nibble is a class of its own; whether the
  low nibble (13 in 109, 141, 157 and 3 in the Skills row with 3) is this table's row is `[L]`.
  (fn:SKILLS_AddElemToPacket@0x0056C8E0, fn:sub_005A5560_MonCritDouble@0x005A5560)
- `[L]` By the names, the hit class chooses the hit's sound and graphic by weapon kind and target size (`vs. Small`,
  `vs. Large`). `[I]` The melee delivery picks a hit class from a global counter (`sub_0057CE30_HitClassPick`, no
  draw, [combat/0001](../findings/combat/0001-formulas.md)); which table value it starts from is plan 0050 Phase 1.3.

## Open questions

- `[L]` What the server does with the hit class (it is presentation unless Phase 1 finds a gate) and how Weapons
  `hit class`, MonStats2 `HitClass` and the packet's `+0x60` relate. Plan 0050 Phase 1.3.
