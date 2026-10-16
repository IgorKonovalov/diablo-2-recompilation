# States (`data/global/excel/states.txt` → `states.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 185   **Record:** 60 B (0x3C)
> **sha256:** `.txt` `898806c2b69e55e316ecfed48dde95aa2933829b94fdad234bdabc27bdbc23e1`, `.bin` `534886c9d40229282d69128d30b1c1457a73a21976ba0ca22546bd4a8f373291`
> **Doc status:** combat rows listed (plan 0037 Phase 0); layout complete except `immed`, `attred` and the order of three red bits; semantics for `exp`
> ([items/0010](../findings/items/0010-quest-drops.md)), the flag bits `life` and `meleeonly` and the combat rows ([combat/0001](../findings/combat/0001-formulas.md), plan 0039 A1); everything else columns listed

## Purpose

One row per unit state: the timed or permanent conditions a skill, an aura, a curse or an event puts on a unit
(`freeze`, `poison`, `conversion`, `might`…), with their overlays, sounds, colour tints, flag bits and the stat
and functions they apply. The project needs it for one column so far: `exp` feeds the killer resolution of the quest
TC switch ([items/0010 § 2](../findings/items/0010-quest-drops.md#2-b6-the-quest-tc-switch-and-the-killer); research
map row `items/quest-drops`). The rest is documented as layout only.

## Row identity

- `[C]` The `.bin` is a u32 record count (185) and 185 records of 60 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)); there is no `Expansion` separator row. The `id` cell equals the row
  index in all 185 rows, and the record stores it at `+0x000`.
- `[C]` The table is loaded by the stock game: `states` is in the loader list with a 60-byte record
  ([data/0001 § 4](../findings/data/0001-excel-loader.md), descriptor `0x00618B7D`), and the loader builds per-flag
  bit-sets from it (below).
- `[L]` Other tables name a state by its `state` cell; how each reader resolves it is not read here.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel states`: 185 records × 68
mapped fields = 12 580 cells, **0 mismatches** (gate survey `excel_layout`, `states_cells`/`states_bad`). Offsets were
found with `excel_bin.py probe`. Where a field's high byte is 0 in every row, its width follows its neighbours'
packing; that width is `[L]`.

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
| `group` | int 1..3, 172 blank | `+0x01E` u8 | group number | — | [C] layout |
| — | always 0 | `+0x01F` u8 | no column | — | [C] layout |
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
| `immed` | int 1, 173 blank (12 rows) | **not located** | no byte or bit of the record follows it | — | [C] (absence, data) |
| `attred` | blank in all 185 rows | **not located** | — | — | [C] (absence, data) |
| `eol` | int 0 | — | end-of-line marker; not compiled | — | [C] layout |

### Flag bits (`+0x010`, 40 bits, bit *i* = byte `+0x010 + i/8`, bit `i mod 8`)

| bit | column | bit | column | bit | column | bit | column |
|---|---|---|---|---|---|---|---|
| 0 | `nosend` | 10 | — (0 in every record) | 20 | `rfblue` | 30 | **`exp`** |
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
- ¹ `[L]` `rfred`, `rlred` and `rcred` are 1 on the same two rows, so the data cannot tell bits 26, 27 and 28 apart;
  the layout assigns them in the order of the blue bits (fire 20, cold 21, lightning 22). Only the loader's
  descriptor can settle it.
- `[L]` Bit 10 is 0 in every record; whether it is `immed` or `attred` (both unlocated) is not known from the data.

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
- Besides `exp`, the flag bits `life` and `meleeonly` and the row ids of § Combat readers have code readers; no other
  column has a reader in a finding yet.

## Open questions

- `[L]` Where `immed` goes (1 on 12 rows, no byte or bit follows it), whether `attred` (blank everywhere) owns flag
  bit 10, and the order of the `rfred`/`rlred`/`rcred` bits: the states loader's descriptor (`0x00618B7D`) settles
  all three. Not blocking: no finding reads them.
