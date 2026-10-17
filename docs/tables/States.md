# States (`data/global/excel/states.txt` → `states.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 185   **Record:** 60 B (0x3C)
> **sha256:** `.txt` `898806c2b69e55e316ecfed48dde95aa2933829b94fdad234bdabc27bdbc23e1`, `.bin` `534886c9d40229282d69128d30b1c1457a73a21976ba0ca22546bd4a8f373291`
> **Doc status:** every row's flags, value columns and naming data listed (plan 0041 Phase 0); combat rows listed (plan 0037 Phase 0); layout complete (`attred`, `immed`, the red bits and `group`'s width from the loader's descriptor, plan 0039 P1b); semantics for `exp`
> ([items/0010](../findings/items/0010-quest-drops.md)), the flag bits `life` and `meleeonly` and the combat rows ([combat/0001](../findings/combat/0001-formulas.md), plan 0039 A1), `group`, `curse`, `plrstaydeath`, `monstaydeath` and `aura` ([stats/0002](../findings/stats/0002-states.md), plan 0041 Phase 1); everything else columns listed

## Purpose

One row per unit state: the timed or permanent conditions a skill, an aura, a curse or an event puts on a unit
(`freeze`, `poison`, `conversion`, `might`…), with their overlays, sounds, colour tints, flag bits and the stat
and functions they apply. Readers so far: `exp` feeds the killer resolution of the quest TC switch
([items/0010 § 2](../findings/items/0010-quest-drops.md#2-b6-the-quest-tc-switch-and-the-killer); research map row
`items/quest-drops`), and the combat code sets and reads the rows of § Combat readers. Plan 0041 (stats and states)
reads the state lifecycle; [§ States by row](#states-by-row-plan-0041-phase-0) lists, for it, what each row carries and
which data names it.

## Row identity

- `[C]` The `.bin` is a u32 record count (185) and 185 records of 60 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)); there is no `Expansion` separator row. The `id` cell equals the row
  index in all 185 rows, and the record stores it at `+0x000`.
- `[C]` The table is loaded by the stock game: `states` is in the loader list with a 60-byte record
  ([data/0001 § 4](../findings/data/0001-excel-loader.md), descriptor `0x00618B7D`), and the loader builds per-flag
  bit-sets from it (below).
- `[L]` Other tables name a state by its `state` cell; how each reader resolves it is not read here.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel states`: 185 records × 69
mapped fields = 12 765 cells, **0 mismatches** (gate survey `excel_layout`, `states_cells`/`states_bad`). Offsets were
found with `excel_bin.py probe`. Where a field's high byte is 0 in every row, its width follows its neighbours'
packing; that width is `[L]`, except `group`, whose s16 width is the descriptor's `[I]` ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17)).

Observed type and range are computed over `states.txt` (185 rows).

| Column | Observed type / range | Record | Meaning | References | Tag |
|---|---|---|---|---|---|
| `state` | str, 185 distinct, 0 blank | — | the row's name; not compiled (the record holds `id`) | — | [C] layout |
| `id` | int 0..184, = row index | `+0x000` u16 | state id | — | [C] layout |
| `overlay1`..`overlay4` | str; 74 / 31 / 4 / 3 distinct; 109 / 145 / 181 / 182 blank | `+0x002`, `+0x004`, `+0x006`, `+0x008` u16 | overlay rows; blank → −1 | `overlay.txt:overlay` | [C] layout |
| `castoverlay` | str, 16 distinct, 160 blank | `+0x00A` u16 | overlay row; blank → −1 | `overlay.txt:overlay` | [C] layout |
| `removerlay` | str, 1 distinct (`teleport`), 184 blank | `+0x00C` u16 | overlay row; blank → −1 | `overlay.txt:overlay` | [C] layout |
| `pgsvoverlay` | str, 6 distinct, 179 blank | `+0x00E` u16 | overlay row; blank → −1 | `overlay.txt:overlay` | [C] layout |
| 40 flag columns | int 1 or blank | `+0x010`..`+0x014`, bits 0..39 | flag bits; table below | — | [C] layout |
| — | always 0 | `+0x015` u8, `+0x016` u16 | no column | — | [C] layout |
| `stat` | str, 29 distinct, 130 blank | `+0x018` u16 | [ItemStatCost](ItemStatCost.md) row; blank → −1 | `itemstatcost.txt:Stat` | [C] layout |
| `setfunc` | int 1..19, 19 distinct, 159 blank | `+0x01A` u16 | function number | — | [C] layout |
| `remfunc` | int 1..12, 12 distinct, 167 blank | `+0x01C` u16 | function number | — | [C] layout |
| `group` | int 1..3, 172 blank | `+0x01E` s16 (`+0x01F`, its high byte, is 0 in every record) | exclusion group (§ Interpretation notes) | — | [C] layout; width [I] (descriptor type 3) |
| `colorpri` | int 70..100, 4 distinct, 178 blank | `+0x020` u8 | — | — | [C] layout |
| `colorshift` | int 73..108, 4 distinct, 178 blank | `+0x021` u8 | — | — | [C] layout |
| `light-r`, `light-g`, `light-b` | int 128..255, 215..255, 128..255; 178 blank each | `+0x022`, `+0x023`, `+0x024` u8 | — | — | [C] layout |
| — | always 0 | `+0x025` u8 | no column | — | [C] layout |
| `onsound` | str, 37 distinct, 142 blank | `+0x026` u16 | `sounds.txt` row; blank → **0** | `sounds.txt:Sound` | [C] layout |
| `offsound` | str, 1 distinct (`druid_morph`), 183 blank | `+0x028` u16 | `sounds.txt` row; blank → 0 | `sounds.txt:Sound` | [C] layout |
| `itemtype` | str, 2 distinct (`mele`, `weap`), 183 blank | `+0x02A` u16 | [ItemTypes](ItemTypes.md) row; blank → **0** | `itemtypes.txt:Code` | [C] layout |
| `itemtrans` | str, 2 distinct (`cgrn`, `cred`), 183 blank | `+0x02C` u8 | [colors](colors.md) row; blank → −1 | `colors.txt:Code` | [C] layout |
| `gfxtype` | int 1..2, 178 blank | `+0x02D` u8 | — | — | [C] layout |
| `gfxclass` | int 0..431, 6 distinct, 178 blank | `+0x02E` u16 | — | — | [C] layout |
| `cltevent` | str, 1 distinct (`hitbymissile`), 184 blank | `+0x030` u16 | `events.txt` row; blank → −1 | `events.txt:event` | [C] layout |
| `clteventfunc` | int 1, 184 blank | `+0x032` u16 | function number | — | [C] layout |
| `cltactivefunc` | int 85..90, 6 distinct, 179 blank | `+0x034` u16 | function number | — | [C] layout |
| `srvactivefunc` | int 145..147, 3 distinct, 182 blank | `+0x036` u16 | function number | — | [C] layout |
| `skill` | str, 2 distinct (`Holy Shield`, `redemption`), 183 blank | `+0x038` u16 | [Skills](Skills.md) row, key matched case-insensitively (`redemption` → 124); blank → −1 | `skills.txt:skill` | [C] layout |
| `missile` | str, 2 distinct, 183 blank | `+0x03A` u16 | `missiles.txt` row; blank → −1 | `missiles.txt:Missile` | [C] layout |
| `immed` | int 1, 173 blank (12 rows) | — (not compiled) | `[I]` the descriptor has no entry for it, so the compiler ignores the column ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17)); no byte or bit of the record follows it `[C]` (data) | — | [I] |
| `attred` | blank in all 185 rows | flag bit 10 (`+0x011` bit 2) | `[I]` descriptor entry 12, type `0x1A` bit 10 ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17)); 0 in every record | — | [C] layout (all 0); bit [I] |
| `eol` | int 0 | — | end-of-line marker; not compiled | — | [C] layout |

### Flag bits (`+0x010`, 40 bits, bit *i* = byte `+0x010 + i/8`, bit `i mod 8`)

| bit | column | bit | column | bit | column | bit | column |
|---|---|---|---|---|---|---|---|
| 0 | `nosend` | 10 | `attred` ² | 20 | `rfblue` | 30 | **`exp`** |
| 1 | `aura` | 11 | `curse` | 21 | `rcblue` | 31 | `shatter` |
| 2 | `hide` | 12 | `curable` | 22 | `rlblue` | 32 | `life` |
| 3 | `transform` | 13 | `plrstaydeath` | 23 | `rpblue` | 33 | `udead` |
| 4 | `pgsv` | 14 | `monstaydeath` | 24 | `stambarblue` | 34 | `green` |
| 5 | `active` | 15 | `bossstaydeath` | 25 | `armred` | 35 | `nooverlays` |
| 6 | `remhit` | 16 | `disguise` | 26 | `rfred` ¹ | 36 | `noclear` |
| 7 | `damblue` | 17 | `restrict` | 27 | `rcred` ¹ | 37 | `bossinv` |
| 8 | `damred` | 18 | `blue` | 28 | `rlred` ¹ | 38 | `meleeonly` |
| 9 | `attblue` | 19 | `armblue` | 29 | `rpred` | 39 | `notondead` |

- `[C]` Every flag column above agrees with its bit over all 185 records (the diff above). Each is 1 on 1 to 32 rows
  (`aura` 32, `curse` 26, `monstaydeath` 14, …).
- ¹ `[I]` `rfred` is bit 26, `rcred` bit 27 and `rlred` bit 28 in the loader's descriptor (`STATES_Load`
  0x00618100, read up to its `DATATBLS_LoadTable` call at 0x00618B7D), the order of the blue bits (fire 20, cold 21,
  lightning 22). The data alone cannot tell them apart: the three are 1 on the same two rows (29, 61).
  ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17), fn:STATES_Load@0x00618100, tbl:States.txt:rfred)
- ² `[I]` `attred` is flag bit 10 (descriptor entry 12); it is blank in every row and bit 10 is 0 in every record
  `[C]`. (fn:STATES_Load@0x00618100, tbl:States.txt:attred)

## Combat rows (plan 0037 Phase 0)

The rows the on-hit effects are expected to set, chosen **by their `state` names** (`[L]`). Each row's id is its row
index (§ Row identity); the fields are § Columns (`[C]`, `excel_bin.py diff`, 0 mismatches). From
`python3 -I tools/combat_survey.py states workspace/merged/data/global/excel` (gate survey `combat`), `[C]` as data.

| Row id | `state` | `stat` (`+0x018`) | `setfunc` / `remfunc` / `srvactivefunc` | Flag columns set | Expected effect by name (`[L]`, plan 0037 Phase 0) |
|---:|---|---|---|---|---|
| 1 | `freeze` | — | 0 / 0 / 0 | `hide`, `monstaydeath`, `blue`, `shatter`, `udead` | freeze from cold damage |
| 2 | `poison` | — | 0 / 0 / 0 | `life`, `green` | poison damage over time |
| 11 | `cold` | `velocitypercent` (67) | 0 / 0 / 0 | `blue` | chill (slowed by cold) |
| 21 | `stunned` | — | 0 / 0 / 0 | — | stun |
| 24 | `slowed` | — | 0 / 0 / 0 | — | slow target |
| 52 | `preventheal` | — | 0 / 0 / 0 | `life` | prevent monster heal |
| 54 | `uninterruptable` | — | 0 / 7 / 0 | — | — |
| 62 | `openwounds` | — | 0 / 0 / 0 | `active`, `life` | open wounds bleed |
| 86 | `justhit` | — | 0 / 0 / 0 | `nosend` | hit recovery marker |
| 107 | `shatter` | — | 0 / 0 / 0 | `hide`, `monstaydeath`, `bossstaydeath`, `shatter`, `udead` | frozen-death shatter |
| 115 | `burning` | — | 0 / 0 / 0 | — | fire over time |

- `[C]` All eleven names exist. Only `cold` names a stat (`velocitypercent`, stat 67); the others store the blank
  index. (tbl:States.txt:stat, tbl:States.txt:state)
- **(plan 0039 A1)** The "Expected effect" column is the plan 0037 Phase 0 reading by name; the code readings that
  replace it for the rows read are § Combat readers below. Rows 24 `slowed` and 86 `justhit` were not met by the
  combat reading and stay names. Crushing blow and deadly strike set no state (combat/0001 §§ 5, 10).

### Combat readers (plan 0037 Phase 1, plan 0039 A1)

From [combat/0001](../findings/combat/0001-formulas.md) §§ 7–10, 12b (d) and 14 (static reading), and § 15 where run:2026-10-16-combat reproduced
the case. A state is set "until `frame + length`" from the game frame `Game+0xA8`.

| Row | `state` | Set or read by | What the code does | Tag |
|---:|---|---|---|---|
| 1 | `freeze` | `COMBAT_ApplyFreeze` | on a monster that can be frozen: state 1 until `frame + length` (length divided by `MonsterFreezeDivisor`), a mode change, and a timer at `frame + 1 + length`; players, bosses, uniques and hirelings get state 11 instead | [I] |
| 2 | `poison` | `COMBAT_ApplyPoison` | stat 74 (`hpregen`) = −damage until `frame + length`; an existing poison is replaced (length restarted) only when the new damage ≥ the old | [I] |
| 11 | `cold` | `COMBAT_ApplyCold` | until `frame + length`, with stats 67, 68, 69 = the monster's `coldeffect` (−50 for others); a longer chill extends, a shorter one does not shorten | [I] |
| 21 | `stunned` | `COMBAT_ApplyStun` | until `frame + length` (hireling length capped at 13, others at 250); a unique needs a draw `r ≥ 90`, a boss or `Velocity` 0 is never stunned | [I] |
| 47 | `sanctuary` | `COMBAT_ResistFor` | an attacker under it zeroes an undead defender's physical resistance | [I] |
| 52 | `preventheal` | `MonRegenEvent` | with it and a non-negative regeneration, a monster's tick changes nothing | [I] |
| 54 | `uninterruptable` | `COMBAT_MeleeHitTest`, `COMBAT_ApplyFreeze` | a hit sets no get-hit (`res & 4`); a monster under it is not frozen | [I] |
| 62 | `openwounds` | `STATEVENT_OpenWounds` | `STATE_ApplyTimed` for 200 frames with stat 74 = −damage | [C] |
| 92 | `death_delay` | `COMBAT_ApplyDamage` | blocks the absorb heal | [I] |
| 101 | `holyshield` | `UNIT_GetDefense` | adds the skill's defence calc | [I] |
| 107 | `shatter` | `COMBAT_ApplyCold` | after a chill, one draw on the defender's seed: `r < 20` on a monster without the MonStats2 flag sets it, else clears it | [I] |
| 115 | `burning` | `COMBAT_ApplyBurn` | as `poison`, with the burn damage and length | [I] |
| 131, 133 | `shrine_resist_fire`, `shrine_resist_poison` | `COMBAT_LengthImmunities` | zero the burn (131) and poison (133) lengths of a hit | [I] |

(fn:COMBAT_ApplyFreeze@0x0057B230, fn:COMBAT_ApplyPoison@0x0057AC50, fn:COMBAT_ApplyCold@0x0057AF80,
fn:COMBAT_ApplyStun@0x0057AAE0, fn:COMBAT_ResistFor@0x0057BE00, fn:sub_005A6920_MonRegenEvent@0x005A6920,
fn:COMBAT_MeleeHitTest@0x0057EC10, fn:STATEVENT_OpenWounds@0x005BFE60, fn:STATE_ApplyTimed@0x0056E970,
fn:COMBAT_ApplyDamage@0x0057C6C0, fn:UNIT_GetDefense@0x006223F0, fn:COMBAT_ApplyBurn@0x0057ADD0,
fn:COMBAT_LengthImmunities@0x0057C140, run:2026-10-16-combat, tbl:States.txt:state)

- `[C]` Open wounds: state 62 for 200 frames with stat 74 = `−dmg`, reproduced on 246 events, the bleed ending at the
  application frame + 200 (11 windows). (fn:STATEVENT_OpenWounds@0x005BFE60, run:2026-10-16-combat)
- `[C]` **Flag bit 32 (`life`)** is read by the monster's regeneration tick: a monster carrying a state of that set
  (`poison`, `preventheal`, `openwounds` in stock data) regenerates by its full stat 74 minus the base list's, so the
  bleed or poison counts and the base regeneration does not. Reproduced in 6 181 monster ticks (combat/0001 § 15, [combat/delivery](../specs/combat/delivery.md) E4).
  (fn:sub_005A6920_MonRegenEvent@0x005A6920, 0x005A6935–0x005A6A2B, run:2026-10-16-combat, tbl:States.txt:life)
- `[I]` **Flag bit 38 (`meleeonly`)** is read by `UNIT_HasStateFlag(attacker, 38)` at `0x0056F19A`: an attacker with
  such a state (`wolf` 139, `bear` 140) delivers its melee hit directly, without the charged-skill finisher.
  (fn:UNIT_HasStateFlag@0x0063A7B0, fn:sub_0056C2D0_AttackDeliverMeleeOnly@0x0056C2D0, tbl:States.txt:meleeonly)

## States by row (plan 0041 Phase 0)

What each row carries and which data names it, for the state code plan 0041 Phase 1 reads. Fields are § Columns
(`[C]` layout, `excel_bin.py diff`, 12 765 cells, 0 mismatches); the rows and counts are
`python3 -I tools/stats_survey.py states workspace/merged/data/global/excel` (gate survey `stats`), `[C]` as data.
Meanings `[L]` unless a line cites a finding. (tbl:States.txt:state)

**Layout gaps.** Closed by plan 0039 Phase 1b ([data/0001 § Plan 0039 batch P1b](../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17)): `attred` is flag bit 10, `immed` (1 on 12 rows: 3–5, 8,
33, 37, 40–42, 48, 49, 52; survey key `col_immed`) is not compiled, and bits 26–28 are `rfred`, `rcred`, `rlred`
`[I]` (§ Columns).

### Flag bits by row

Bit *i* is byte `+0x010 + i/8`, bit `i mod 8` (§ Flag bits). Each count is survey key `flag_<column>`.

| bit | column | rows | row ids |
|---:|---|---:|---|
| 0 | `nosend` | 13 | 12, 64–66, 68, 70, 85–86, 97, 111, 160, 170–171 |
| 1 | `aura` | 32 | 3–5, 8, 26, 28–29, 32–37, 40–51, 147–149, 157, 161–163 |
| 2 | `hide` | 9 | 1, 63, 99, 104, 107, 119, 154, 173, 184 |
| 3 | `transform` | 8 | 63, 93, 101, 119, 139–140, 176–177 |
| 4 | `pgsv` | 6 | 122–127 |
| 5 | `active` | 6 | 47, 62, 88, 143–144, 150 |
| 6 | `remhit` | 1 | 153 |
| 7 | `damblue` | 9 | 27, 33, 42, 49, 89, 117, 129, 140, 148 |
| 8 | `damred` | 3 | 16, 19, 60 |
| 9 | `attblue` | 7 | 16, 27, 40, 49, 129, 139, 148 |
| 10 | `attred` | 0 | — |
| 11 | `curse` | 26 | 9, 19, 23, 27, 55–61, 89, 113–114, 128–137, 141, 156 |
| 12 | `curable` | 13 | 9, 19, 23, 27, 55–61, 113–114 |
| 13 | `plrstaydeath` | 3 | 105, 108, 118 |
| 14 | `monstaydeath` | 14 | 1, 63, 96, 98–99, 104–105, 107, 118, 143, 154, 172–173, 184 |
| 15 | `bossstaydeath` | 12 | 63, 96, 98–99, 104–105, 107, 118, 143, 154, 172–173 |
| 16 | `disguise` | 7 | 63, 93, 119, 139–140, 176–177 |
| 17 | `restrict` | 3 | 139–140, 177 |
| 18 | `blue` | 4 | 1, 11, 44, 90 |
| 19 | `armblue` | 11 | 10, 15, 20, 26, 37, 88–89, 95, 128, 140, 153 |
| 20 | `rfblue` | 4 | 3, 8, 131, 159 |
| 21 | `rcblue` | 5 | 4, 8, 132, 159, 179 |
| 22 | `rlblue` | 4 | 5, 8, 130, 159 |
| 23 | `rpblue` | 3 | 133, 159, 178 |
| 24 | `stambarblue` | 2 | 136, 180 |
| 25 | `armred` | 4 | 17, 29, 113, 156 |
| 26 | `rfred` | 2 | 29, 61 |
| 27 | `rcred` | 2 | 29, 61 |
| 28 | `rlred` | 2 | 29, 61 |
| 29 | `rpred` | 1 | 61 |
| 30 | `exp` | 3 | 53, 57, 59 |
| 31 | `shatter` | 3 | 1, 107, 184 |
| 32 | `life` | 3 | 2, 52, 62 |
| 33 | `udead` | 13 | 1, 63, 96, 99, 104, 107, 118–119, 143, 154, 172–173, 184 |
| 34 | `green` | 1 | 2 |
| 35 | `nooverlays` | 4 | 14, 117, 120, 151 |
| 36 | `noclear` | 2 | 14, 151 |
| 37 | `bossinv` | 1 | 63 |
| 38 | `meleeonly` | 2 | 139–140 |
| 39 | `notondead` | 2 | 172–173 |

- `[C]` Rows 128–137 (`shrine_armor` … `shrine_experience`) all set `curse` (bit 11) and none sets `curable` (bit 12);
  `curable` is set on 13 rows, all of which also set `curse`. (tbl:States.txt:curse)
- `[C]` `aura` (bit 1) is set on 32 rows; 29 `convicted` sets it though no Skills row names it, and 147–149 (`barbs`,
  `wolverine`, `oaksage`) and 161–163 (their `…control` rows) split the druid spirits' target and caster states.

### Value columns by row

| Column | `.bin` field | Rows (value: row ids) | Survey key |
|---|---|---|---|
| `group` | `+0x01E` s16 | 1: 10, 14, 20, 86, 88; 2: 157, 159; 3: 117, 120, 139, 140, 176, 177 | `col_group` = 13 |
| `setfunc` | `+0x01A` u16 | 1: 122–127; 2: 153; 3: 13; 4: 98; 5: 142; 6: 14; 7: 144; 8: 151; 9: 134; 10: 99; 11: 150; 12: 146; 13: 143; 14: 139, 140; 15: 96; 16: 117, 120; 17: 172; 18: 173; 19: 121 | `col_setfunc` = 26 |
| `remfunc` | `+0x01C` u16 | 1: 122–127; 2: 98; 3: 14; 4: 144; 5: 151; 6: 134; 7: 54; 8: 146; 9: 143; 10: 110; 11: 117, 120; 12: 121 | `col_remfunc` = 18 |
| `srvactivefunc` | `+0x036` u16 | 145: 144; 146: 145; 147: 143 | `col_srvactivefunc` = 3 |
| `cltactivefunc` | `+0x034` u16 | 85: 62; 86: 47; 87: 88; 88: 143; 89: 150; 90: 144 | `col_cltactivefunc` = 6 |
| `clteventfunc` | `+0x032` u16 | 1: 20 (with `cltevent` `hitbymissile`) | `col_clteventfunc` = 1 |
| `skill` | `+0x038` u16 | 99 `redeemed` → `redemption`, 101 `holyshield` → `Holy Shield` | `col_skill` = 2 |
| `missile` | `+0x03A` u16 | 172 `restinpeace` → `redemption`, 173 `corpseexp` → `corpseexplosion` | `col_missile` = 2 |
| `itemtype` | `+0x02A` u16 | 16 `enchant` → `weap`, 31 `venomclaws` → `mele` | `col_itemtype` = 2 |

`stat` (`+0x018` u16 [ItemStatCost](ItemStatCost.md) row, blank −1) is set on 55 rows (`col_stat`), 29 distinct stats:

| stat | state rows |
|---|---|
| 9 `maxmana` | 32 `battleorders` |
| 10 `stamina` | 136 `shrine_stamina` |
| 11 `maxstamina` | 41 `stamina` |
| 19 `tohit` | 129 `shrine_combat` |
| 25 `damagepercent` | 19 `weaken`, 33 `might`, 42 `concentration`, 117 `maul` |
| 31 `armorclass` | 17 `innersight`, 128 `shrine_armor` |
| 36 `damageresist` | 9 `amplifydamage` |
| 39 `fireresist` | 3 `resistfire`, 131 `shrine_resist_fire` |
| 41 `lightresist` | 5 `resistlight`, 8 `resistall`, 61 `lowerresist`, 130 `shrine_resist_lightning` |
| 43 `coldresist` | 4 `resistcold`, 132 `shrine_resist_cold` |
| 45 `poisonresist` | 133 `shrine_resist_poison`, 159 `fade` |
| 51 `lightmaxdam` | 46 `holyshock` |
| 57 `poisonmindam` | 31 `venomclaws` |
| 67 `velocitypercent` | 11 `cold`, 44 `holywindcold`, 82 `increasedspeed` |
| 68 `attackrate` | 25 `fetishaura`, 49 `fanaticism`, 120 `feralrage`, 157 `quickness` |
| 119 `item_tohit_percent` | 40 `blessedaim`, 148 `wolverine` |
| 161 `skill_handofathena` | 87 `slowmissiles` |
| 162 `skill_staminapercent` | 47 `sanctuary` |
| 165 `skill_enchant` | 16 `enchant` |
| 167 `skill_conviction` | 29 `convicted` |
| 169 `skill_frenzy` | 94 `frenzy`, 103 `monfrenzy` |
| 170 `skill_decrepify` | 60 `decrepify` |
| 171 `skill_armor_percent` | 10 `frozenarmor`, 15 `concentrate`, 20 `chillingarmor`, 26 `shout`, 37 `defiance`, 88 `shiverarmor`, 89 `battlecry`, 101 `holyshield`, 113 `defense_curse`, 156 `cloaked` |
| 318 `progressive_damage` | 122 `progressive_damage` |
| 319 `progressive_steal` | 123 `progressive_steal` |
| 320 `progressive_other` | 124 `progressive_other` |
| 321 `progressive_fire` | 125 `progressive_fire` |
| 322 `progressive_cold` | 126 `progressive_cold` |
| 323 `progressive_lightning` | 127 `progressive_lightning` |

- `[C]` Six progressive rows 122–127 each name the stat of the same name (318–323) and share `setfunc` 1 and `remfunc`
  1. Of the shrine rows, 128–133 and 136 name a stat, 134 `shrine_skill`, 135 `shrine_mana_regen` and 137
  `shrine_experience` none (134 has `setfunc` 9 and `remfunc` 6 instead). (tbl:States.txt:stat)
- `[L]` A state's `stat` is the stat its list carries for the overlay and tooltip; whether the state code reads it,
  and what a state's stat list holds otherwise (the aura and passive calcs of [Skills](Skills.md#passive-and-aura-columns-plan-0041-phase-0)), is
  Phase 1.

### Which data names a row

Every data column that stores a States row index (by the layouts of `tools/excel_layouts.py`, each `[C]` by its
`diff`), with the rows it names. 129 of the 185 rows are named by one of them (`rows_named`); a row can be named by
several.

| Source | Cells | State rows named | Survey key |
|---|---:|---|---|
| [Skills](Skills.md) `aurastate` | 74 | 65 rows: 3–5, 8, 10, 13–16, 20, 22, 26, 28, 30–38, 40–43, 45–51, 63, 88, 94, 95, 101, 103, 117, 119, 120, 122–127, 138–140, 143–145, 150, 151, 153, 157–159, 161–163, 174, 177 | `src_skills_aurastate` |
| Skills `auratargetstate` | 47 | 44 rows: 3–5, 8, 9, 17, 19, 23, 24, 26–28, 32–34, 36, 37, 40–42, 44, 45, 48, 49, 51, 53, 55–61, 84, 87, 89, 112–114, 141, 147–149, 156 | `src_skills_auratargetstate` |
| Skills `passivestate` | 29 | 28 rows: 64–83, 97, 111, 152, 155, 160, 181–183 | `src_skills_passivestate` |
| Skills `State1`, `State2` | 7, 2 | 139 `wolf`, 140 `bear` (the shapeshift restriction) | `src_skills_state1`, `src_skills_state2` |
| [Misc](Misc.md) `state` | 14 | 17 `innersight` (`hrb`), 100 `healthpot` (`hp1`–`hp5`), 106 `manapot` (`mp1`–`mp5`), 178 `antidote` (`yps`), 179 `thawing` (`wms`), 180 `staminapot` (`vps`) | `src_misc_state` |
| Misc `cstate1`, `cstate2` | 2, 1 | 1 `freeze` (`wms`), 2 `poison` (`yps`); 11 `cold` (`wms`) | `src_misc_cstate1`, `src_misc_cstate2` |
| [Weapons](Weapons.md), [Armor](Armor.md) `state`, `cstate1`, `cstate2` | 0 | — | — |
| [Sets](Sets.md#bonus-blocks-plan-0041-phase-0) full-bonus blocks with the property `state` | 6 | 175 `fullsetgeneric` (`FParam5`–`7` of five sets), 176 `monsterset` (Trang-Oul's Avatar `FParam5`) | `src_sets_fparam5..7` |

- `[C]` Rows named: 119 by Skills, 9 by items (Misc), 2 by Sets; 56 by no data column: 0, 6, 7, 12, 18, 21, 25, 29, 39,
  52, 54, 62, 85, 86, 90–93, 96, 98, 99, 102, 104, 105, 107–110, 115, 116, 118, 121, 128–137, 142, 146, 154,
  164–173, 184. (tbl:Skills.txt:aurastate, tbl:Misc.txt:state)
- `[C]` **No monster-mod column names a state.** Two checks agree. By the headers: the only `.txt` columns whose
  name says state are Misc `state`, `cstate1`, `cstate2` and Skills `aurastate`, `auratargetstate`, `passivestate`,
  `State1..3` (each a States index in its layout), and the only property that takes a state, `state`, appears only
  in the six Sets blocks above (no MonProp, unique, runeword or affix row uses it). By the cells: a scan of every `.txt`
  cell against the 185 `state` names finds hits only in the columns above and in columns that hold another key with
  the same spelling: property codes (`freeze`, `thorns`, `fade`), skill names in property params (`aura`
  `Sanctuary`, `hit-skill` `Decrepify`), element and monster-mod names (MonUMod `uniquemod` `berserk`, `cold`).
  `[L]` So a state a monster mod puts on a unit, like the on-hit states of § Combat readers, comes from code
  (plan 0041 Phase 1).
- **Rows set by code, from findings.** `[C]` 165–169 `itemset1`–`itemset5` hold a set item's `aprop` pairs
  ([SetItems § Property block](SetItems.md#property-block-plan-0024-phase-1), data:g_SetAPropStates@0x006EDB40).
  `[I]` 1, 2, 11, 21, 47, 52, 54, 62, 92, 101, 107, 115, 131 and 133 have the readers of § Combat readers; 53, 57 and
  59 (`exp`) the quest-TC reader of § Interpretation notes.
- `[L]` **Shrines.** Shrines has no state column. The ten timed effects (codes 6–15, `Duration in frames` > 0,
  [Shrines § Effects](Shrines.md#effects-plan-0041-phase-0)) match the ten rows 128–137 by name: 6 → 128
  `shrine_armor`, 7 → 129 `shrine_combat`, 8 → 131 `shrine_resist_fire`, 9 → 132 `shrine_resist_cold`, 10 → 130
  `shrine_resist_lightning`, 11 → 133 `shrine_resist_poison`, 12 → 134 `shrine_skill`, 13 → 135
  `shrine_mana_regen`, 14 → 136 `shrine_stamina`, 15 → 137 `shrine_experience` (`shrine_pairs` = 10; for 7 of them
  the state is the code + 122; fire, cold and lightning are in another order). The pairing is a name reading until the shrine
  operate is read.

## Interpretation notes

- `[I]` **`exp` is flag bit 30, and the quest TC switch reads it.** The states loader builds 40 bit-sets at
  `DataTables+0xCC + 4i`, set *i* holding the states whose flag bit *i* is set; set 30 (`DataTables+0x144`) is the bit
  the loader's descriptor gives the column `exp`. `MONSTER_DropItems` uses it to resolve a non-player killer: a killer
  that carries a state of that set is credited to the owner of that state's stat list (the caster) for the quest-TC
  test of [MonStats § Quest TCs](MonStats.md#quest-tcs-plan-0032-phase-0). In the shipped data `exp` is 1 on rows 53
  `conversion`, 57 `attract` and 59 `confuse`. ([items/0010 § 2](../findings/items/0010-quest-drops.md#2-b6-the-quest-tc-switch-and-the-killer);
  fn:sub_00611D60_StatesMaskBuild@0x00611D60, fn:sub_0063A690_UnitHasExpState@0x0063A690,
  fn:MONSTER_DropItems@0x005A6600, 0x00618B77, tbl:States.txt:exp)
- `[C]` The flag bit of `exp` agrees between the finding (bit 30 from the descriptor) and the data (`+0x013` bit 6
  over all 185 records), a code anchor plus data behaviour.
- `[L]` The column name suggests the experience credit of a kill by a converted or confused monster also goes to the
  caster; only the quest-TC reader has been read.
- `[I]` **`udead` is flag bit 33** (the loader's bit-set at `DataTables+0x150` = `0xCC + 4·33`): when a room is
  released, a dead monster that carries any state of that set is not saved (`InactiveMonsterSaveTest` step 2). In the
  shipped data 13 rows set it (§ Flag bits by row). (fn:sub_005431F0_InactiveMonsterSaveTest@0x005431F0,
  fn:sub_0063A130_UnitHasStateInMask@0x0063A130, tbl:States.txt:udead;
  [drlg/0009 § 5](../findings/drlg/0009-room-lifecycle.md#5-the-inactive-records))
- `[I]` **`group` is an exclusion group, cleared by `STATE_GroupClear`.** Called by the item-use states (potions),
  five skill functions and the `state` stat callback before they apply a state, it clears every other state of the
  same non-zero `group` on the unit and frees its list; the apply itself (`STATE_ApplyTimed`) does not look at it.
  ([stats/0002 § Answer](../findings/stats/0002-states.md#answer-summary), fn:STATE_GroupClear@0x0056C740,
  tbl:States.txt:group)
- `[I]` **`curse` (bit 11)** is read by `STATE_ApplyTimed` through `STATES_IsCurse`: a curse is refused when the
  target's `curse_resistance` (109) is ≥ 100 or the target is in 57 `attract`, its duration is shortened by stat 109
  percent, and a new curse replaces any curse list (flag `0x20`) on the target.
  ([stats/0002 § 2](../findings/stats/0002-states.md#2-apply-state_applytimed-structtimedstatereq0x1c),
  fn:STATES_IsCurse@0x0063A420, fn:STATE_ApplyTimed@0x0056E970, tbl:States.txt:curse)
- `[I]` **`plrstaydeath` (bit 13) and `monstaydeath` (bit 14)** keep a state through death: `STATES_StaysOnDeath`
  tests the first for a player and the second for any other unit, in the default remove callback and in the death
  purge. ([stats/0002 § 3](../findings/stats/0002-states.md#3-removal-and-expiry), fn:STATES_StaysOnDeath@0x0063A4A0,
  fn:STATE_DefaultRemoveCB@0x0056E900, tbl:States.txt:plrstaydeath)
- `[I]` **`aura` (bit 1)** is what the two aura events test: an item aura (stat 151) needs the skill's `aura` bit and an
  `aurastate`, and `EVENT_SelectedAuraTick` runs the unit's selected right skill when it has the `aura` bit. The
  masteries 127–129 set `aura` with no `aurastate`; no code read gives the bit an effect for them.
  ([stats/0002 § 4](../findings/stats/0002-states.md#4-auras-and-passives), fn:ITEMAURA_Start@0x005BF510,
  fn:EVENT_SelectedAuraTick@0x0056FCB0)
- Besides these, the flag bits `exp`, `udead`, `life` and `meleeonly` and the row ids of § Combat readers have code
  readers; no other column has a reader in a finding yet.

## Open questions

- `[L]` What `setfunc`, `remfunc`, `srvactivefunc` and the flag bits without a reader above do. Of the 56 rows no data
  column names (§ Which data names a row), [stats/0002 § Phase 0 surprise (f)](../findings/stats/0002-states.md#phase-0-surprise-f-the-56-rows-no-data-names)
  places 22 (set or tested by code it reads). Of the other 34 (0, 6, 12, 18, 21, 25, 29, 39, 54, 86, 90–93, 96, 98,
  99, 102, 104, 105, 108–110, 116, 118, 121, 142, 146, 154, 164, 171–173, 184), its setters scan
  ([§ Surprise (f) setters scan](../findings/stats/0002-states.md#surprise-f-setters-scan-plan-0041-p1-review-follow-up-b-2026-10-17), `lane/rbs`)
  gives 27 an immediate set or clear site, some in named functions (21 `COMBAT_ApplyStun`, 92 `COMBAT_GetHit`, 96
  and 173 `sub_005C07A0_SkillReviveDo`, 105 `sub_005543B0_MonAlignSet`, 118, and 154 cleared only by
  `sub_00579AA0_MercRevive`; row 0's site marks a stat list as no state rather than setting one), most in functions
  not read; it finds no site for 7 (6, 25, 29, 39, 116, 164, 171), which stay open.
