# PetType (`data/global/excel/pettype.txt` → `pettype.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 20 (no `Expansion` marker)   **Record:** 224 B (`0xE0`)
> **sha256:** `.txt` `144f83f31fac99e371544f3b60c16eb95fb27cd86282c28df45f035314a6699b`, `.bin` `dddd06c2d89abb73798be40d05645d1eb6f187b747a628bad4d547ba978b133f`
> **Doc status:** layout complete (every compiled column placed, `[C]` by diff; plan 0045 Phase 0); semantics `[L]` until
> the summon reading of plan 0045 Phase 1.3

## Purpose

One row per kind of pet: the summons of the class skills (golem, skeleton, valkyrie, spirit wolf, totem, vine, trap,
…), the hireling, and a few internal kinds (`none`, `single`, `invis`, `pettrap`). A Skills row that summons names its
kind in `pettype` ([Skills § Dispatch](Skills.md#dispatch-plan-0045-phase-0)); the kind carries the limit columns
(`group`, `basemax`), the behaviour bits (follow through warps, out-of-range removal, party send, unsummon, automap,
life bar) and the party-UI icon columns. Readers: `skills/dispatch` (summons, plan 0045 Phase 1.3). Leads: no lead;
derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (20) and 20 records of 224 bytes, one per `.txt` row in order; the full-record
  loader allocates 224-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0061909A`).
- `[C]` `idx` equals the row index in all 20 rows (`pt_idx_is_row=20`). The name key `pet type` is not compiled;
  Skills `pettype` stores the row index of the name as a u8 (`+0x0BE`). (tbl:PetType.txt:idx, tbl:Skills.txt:pettype)

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel pettype`: 20 records × 20 mapped
fields = 400 cells, **0 mismatches**. `excel_bin.py unknown … pettype` lists only zero bytes (`+0x005..+0x007`,
`+0x0AF..+0x0B1`, `+0x0BA..+0x0DF`) and `+0x004` bits 6–7 (0 in every record). Offsets are the ones `excel_bin.py
probe` finds; `name` is a string-table index (blank = 5382, [excel-bin.md](../formats/excel-bin.md)); `mclass4` and
`micon4` are blank in every row and placed by the stride of their run. Observed values are from the `.txt`, generated
by script. **Meaning** is the column name's plain reading, `[L]`.

### Identity

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `pet type` | str, 20 distinct, 0 blank | — | pet type name, the key Skills `pettype` uses | — | [C] |
| `idx` | int 0..19 (20 distinct), 0 blank | `+0x000` u32 | pet type id (= row index) | — | [C] |

### Limit and behaviour columns

The six behaviour columns are bits of `+0x004` (bit order = header order: `warp` 0, `range` 1, `partysend` 2,
`unsummon` 3, `automap` 4, `drawhp` 5).

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `group` | int {1}, 17 blank | `+0x008` u16 | pet group: types of one group share a limit (set on `spiritwolf`, `fenris`, `grizzly`) | — | [C] |
| `basemax` | int {0, 1}, 1 blank | `+0x00A` u16 | base count limit of the type (1 on `single` and `hireable`, 0 elsewhere: the limit then comes from the summoning skill's `petmax`) | — | [C] |
| `warp` | int {1}, 5 blank | `+0x004` bit 0 | the pet follows its owner through warps | — | [C] |
| `range` | int {1}, 17 blank | `+0x004` bit 1 | the pet is removed when its owner is out of range | — | [C] |
| `partysend` | int {1}, 7 blank | `+0x004` bit 2 | the pet is sent to party members | — | [C] |
| `unsummon` | int {1}, 8 blank | `+0x004` bit 3 | the pet can be unsummoned | — | [C] |
| `automap` | int {1}, 6 blank | `+0x004` bit 4 | shown on the automap | — | [C] |
| `drawhp` | int {1}, 7 blank | `+0x004` bit 5 | its life bar is drawn | — | [C] |

### UI columns (presentation)

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `name` | str, 12 distinct, 8 blank | `+0x00C` u16 string index | UI name (string key) | — | [C] |
| `icontype` | int {1, 2, 3}, 8 blank | `+0x00E` u8 | icon selection mode | — | [C] |
| `baseicon` | str, 12 distinct, 7 blank | `+0x00F` char[32] | default icon | — | [C] |
| `mclass1` | int 290..426 (4 distinct), 16 blank | `+0x0B2` u16 | monster class that uses `micon1` instead of `baseicon` | `monstats` row index | [C] |
| `micon1` | str, 4 distinct, 16 blank | `+0x02F` char[32] | icon of `mclass1` | — | [C] |
| `mclass2` | int 291..427 (4 distinct), 16 blank | `+0x0B4` u16 | monster class that uses `micon2` | `monstats` row index | [C] |
| `micon2` | str, 4 distinct, 16 blank | `+0x04F` char[32] | icon of `mclass2` | — | [C] |
| `mclass3` | int {292, 561}, 18 blank | `+0x0B6` u16 | monster class that uses `micon3` | `monstats` row index | [C] |
| `micon3` | str {`barbhirable_icon`, `firegolumicon`}, 18 blank | `+0x06F` char[32] | icon of `mclass3` | — | [C] |
| `mclass4` | blank in all rows | `+0x0B8` u16 | monster class that uses `micon4` | `monstats` row index | [C] value; slot by stride `[L]` |
| `micon4` | blank in all rows | `+0x08F` char[32] | icon of `mclass4` | — | [C] value; slot by stride `[L]` |

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `eol` | int {0}, 0 blank | — | end-of-line marker; not compiled | — | [C] |

## The rows and the skills that name them

`[C]` as data: `python3 -I tools/skills_survey.py pettype workspace/merged/data/global/excel` (gate survey `skills`,
`pt_*` keys). Bits: W `warp`, R `range`, P `partysend`, U `unsummon`, A `automap`, H `drawhp`.

| idx | pet type | group | basemax | bits | icontype | mclass | Skills rows naming it (summon; petmax) |
|---:|---|---:|---:|---|---:|---|---|
| 0 | `none` | 0 | 0 | ------ | 0 | — | 78 Bone Wall, 88 Bone Prison (`bonewall`), 199 DiabPrison (`boneprison1`); no petmax |
| 1 | `single` | 0 | 1 | W-P-A- | 0 | — | — |
| 2 | `valkyrie` | 0 | 0 | W-PUAH | 1 | — | 32 Valkyrie (`valkyrie`; 1) |
| 3 | `golem` | 0 | 0 | W-PUAH | 3 | 290 bloodgolem, 291 irongolem, 292 firegolem | 75 Clay Golem, 85 BloodGolem, 90 IronGolem, 94 FireGolem (the four golems; 1) |
| 4 | `skeleton` | 0 | 0 | W-PUAH | 2 | — | 70 Raise Skeleton (`necroskeleton`; `(lvl < 4) ?lvl:(2+lvl/3)`) |
| 5 | `skeletonmage` | 0 | 0 | W-PUAH | 2 | — | 80 Raise Skeletal Mage (`necromage`; the same formula) |
| 6 | `revive` | 0 | 0 | W-PUAH | 2 | — | 95 Revive (no summon; `lvl`) |
| 7 | `hireable` | 0 | 1 | W-P-AH | 0 | 338 act2hire, 359 act3hire, 561 act5hire2 | — |
| 8 | `dopplezon` | 0 | 0 | ---UAH | 0 | — | 28 Dopplezon (`dopplezon`; 1) |
| 9 | `invis` | 0 | 0 | W----- | 0 | — | — |
| 10 | `raven` | 0 | 0 | W----- | 2 | — | 221 Raven (`druidhawk`; `min(lvl,par2)`) |
| 11 | `spiritwolf` | 1 | 0 | W-PUAH | 2 | — | 227 Summon Spirit Wolf (`spiritwolf`; `min(lvl,par3)`) |
| 12 | `fenris` | 1 | 0 | W-PUAH | 2 | — | 237 Summon Fenris (`fenris`; `min(lvl,par3)`) |
| 13 | `totem` | 0 | 0 | W-PUAH | 3 | 423 heartofwolverine, 422 spiritofbarbs | 226 Oak Sage, 236 Heart of Wolverine, 246 Spirit of Barbs (1) |
| 14 | `vine` | 0 | 0 | W-PUAH | 3 | 426 cycleoflife, 427 vinecreature | 222 Plague Poppy, 231 Cycle of Life, 241 Vines (1) |
| 15 | `grizzly` | 1 | 0 | W-PUAH | 1 | — | 247 Summon Grizzly (`druidbear`; 1) |
| 16 | `shadowwarrior` | 0 | 0 | W-PUAH | 1 | — | 268 Shadow Warrior, 279 Shadow Master (1) |
| 17 | `assassintrap` | 0 | 0 | -R---- | 0 | — | 257 Blade Sentinel and the five `… Sentry` rows 261, 262, 271, 272, 276 (5) |
| 18 | `pettrap` | 0 | 0 | -R---- | 0 | — | — |
| 19 | `hydra` | 0 | 0 | -R---- | 0 | — | 62 Hydra (`hydra1`; 99) |

- `[C]` 16 of the 20 kinds are named by 31 Skills rows; `single`, `hireable`, `invis` and `pettrap` by none
  (`pt_types_used_by_skills=16`, `pt_skill_rows=31`, `pt_unused=4`). (tbl:Skills.txt:pettype)
- `[C]` `basemax` is 1 on `single` and `hireable` only; every kind a skill names has `basemax` 0, and every
  summoning row of those kinds except the three `none` rows has a `petmax` (`sk_summon_without_petmax=5`: the three
  `none` rows and the two summons with no `pettype`, 295 Overseer Whip and 300 Impregnate). (tbl:PetType.txt:basemax,
  tbl:Skills.txt:petmax)
- `[C]` `group` 1 is set on the three Druid animal kinds `spiritwolf`, `fenris`, `grizzly` (`pt_group_set=3`).
  (tbl:PetType.txt:group)
- `[C]` The 10 `mclass` cells all resolve to a monstats row, and each `micon_k` is the icon of `mclass_k`'s monster
  (290 `bloodgolem` with `bloodgolumicon`, 338 `act2hire` with `act2hireableicon`, …): the kinds whose members differ
  in their icon, `icontype` 3 (and `hireable`). (tbl:PetType.txt:mclass1)
- `[C]` The Skills `petmax` formula is the skill variable `pets` (71): `SKILLS_CalcVar` returns its value
  ([data/calc § G](../specs/data/calc.md); fn:SKILLS_CalcVar@0x00646460). How the summon code uses it is Phase 1.3.

## Open questions

- `[L]` Which PetType columns the summon code reads and how the limit is computed from `basemax`, `group` and the
  skill's `petmax` (the plan names "the `pettype` limit"). Owner: reverser, plan 0045 Phase 1.3.
- `[L]` Whether `idx` is read at all (it equals the row index).
