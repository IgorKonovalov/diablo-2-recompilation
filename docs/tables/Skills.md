# Skills (`data/global/excel/skills.txt` → `skills.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 357 (no `Expansion` marker)   **Record:** 572 B (`0x23C`)
> **sha256:** `.txt` `465c28e83657540e0d7ae5b0de826d5657be7fba1aa539a85c3ca3aeea34b498`, `.bin` `0b57ba62b6b5c74be6a579adb9327641ecfe880ebc0c217d341c9d5bba89043b`, `skillscode.bin` `d42e1da6ebdf835c0c623f13c77201e3c2a25659dc58eff215af3cacc7ecf30f`
> **Doc status:** layout complete (every compiled column placed, `[C]` by diff); semantics `[I]` only for the columns
> the item code reads (`Id`, `itypea1`, the class blocks), `[L]` elsewhere (no skills subsystem is planned)

## Purpose

One row per skill: the 210 character-class skills, plus monster, item and internal skills (`Attack`, `Kick`,
`Scroll of Identify`, `Wake Of Destruction Sentry`, …). A row holds the skill's server and client functions, missiles,
aura and passive stats, summon, item-type requirements, level and mana costs, damage and formulas. In this project
the reader so far is `items/affixes`: the staff-mods roll picks class skills by id and tests their item-type
requirement ([items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260),
plan 0021). Other readers (skills, missiles, monster AI) are out of scope. Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (357) and 357 records of 572 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The full-record loader allocates 572-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0061787B`);
  a 2-byte `skills` load (`0x00612E15`) runs only under `-txt`.
- `[C]` `Id` equals the row index in all 357 rows. The name key `skill` is not compiled; other tables' skill columns
  (`reqskill1`, `sumskill1`, and this table's own) store the row index of the name.
- `[I]` The item code addresses the records as `DataTables+0xB98` with stride `0x23C`, by skill id
  ([items/0005 § Data touched](../findings/items/0005-affixes.md#data-touched)).

## Class blocks

- `[C]` By data, each class's 30 skills are one run of consecutive ids: `ama` 6–35, `sor` 36–65, `nec` 66–95, `pal`
  96–125, `bar` 126–155, `dru` 221–250, `ass` 251–280. The 147 classless rows are ids 0–5, 156–220 and 281–356.
  (tbl:Skills.txt:charclass)
- `[C]` Within a run, the five skills `first + 5(t − 1)` … `first + 5(t − 1) + 4` share one `reqlevel` for t = 1..6
  (1, 6, 12, 18, 24, 30) in every class except `bar`, whose blocks 2–5 mix two adjacent levels (e.g. ids 131–135 hold
  `reqlevel` 1 and 6). (tbl:Skills.txt:reqlevel)
- `[I]` The staff-mods roll draws a skill as `low % 5 + (tier − 1)·5 + firstSkill(class)` with tier 1..6 (a base tier
  of at most 5 by ilvl, then a −2..+1 step; at most 4 on a low-quality item), so a tier is one five-skill block of the class run, and accepts it when
  its `itypea1` (`+0x18`) is empty or the item is of that type; after 6 failed tries the last skill drawn is used.
  (fn:sub_005C0F90_StaffModsRoll@0x005C0F90, fn:ITEMS_RollStaffMods@0x005C1260,
  [items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260))
- `[C]` `firstSkill(class)` is the first id of the class run above: the value `0x006460F0(class, 0)` returns was
  logged on all 74 staff-mods rolls of run:2026-10-14-affixes, 36, 66, 96, 126, 221 and 251 for classes 1–6. Class 0
  (`ama`, 6) was not logged and stays `[I]` by the same reader. (0x005C1285–0x005C128A, tbl:Skills.txt:charclass,
  run:2026-10-14-affixes, [items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260))
- `[C]` By data, 50 class skills name an `itypea1`: 23 `ama` (`miss`, `spea`, `jave`), 1 `nec` (`knif`), 8 `pal`
  (`mele`, `shld`), 9 `bar` (`mele`, `thro`), 9 `ass` (`h2h`, `mele`); no `sor` or `dru` skill has one.
  (tbl:Skills.txt:itypea1)

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel skills`: 357 records × 238 mapped
fields = 84 966 cells, **0 mismatches** (703 calc cells are expressions: offset present, bytecode not decoded).
`excel_bin.py unknown … skills` lists only zero bytes (`+0x002`, `+0x009..+0x00B`, `+0x00D..+0x00F`, `+0x036`,
`+0x0A2`, `+0x0CE`, `+0x126`, `+0x16E`, `+0x196`, `+0x1A6`, `+0x1DD..+0x1DF`, `+0x229`) and `+0x008` bit 7 (0 in every
record). Offsets are the ones `excel_bin.py probe` finds; the calc offsets come from a scan for s32 slots that are −1
exactly on blank cells and decode the constant cells. Observed values are from the `.txt` (357 rows). **Meaning** is the
column name's plain reading, `[L]`, unless it carries its own tag. The 15 `*… desc`/`*Param… Description` comment
columns are not listed (not compiled).

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `skill` | str, 357 distinct, 0 blank | — (key; record holds `Id`) | skill name, the key other tables use | — | [C] |
| `Id` | int 0..356 (357 distinct), 0 blank | `+0x000` u16 | skill id; `[I]` the layer of stat 107 `item_singleskill` set by the staff mods ([items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260)) | — | [C] |
| `charclass` | str, 7 distinct, 147 blank | `+0x00C` u8 index | owning character class (blank = none); see *Class blocks* | `playerclass:Code` | [C] |
| `skilldesc` | str, 221 distinct, 135 blank | `+0x194` u16 index | row of `skilldesc` (UI description) | `skilldesc:skilldesc` | [C] |
| `srvstfunc` | int 1..65 (64 distinct), 245 blank | `+0x02C` u16 | server start / do / progressive function number | — | [C] |
| `srvdofunc` | int 1..152 (138 distinct), 83 blank | `+0x02E` u16 | server start / do / progressive function number | — | [C] |
| `prgstack` | int {1}, 354 blank | `+0x004` bit 7 | progressive-charge values | — | [C] (the other probe candidates lie inside fields other columns pin) |
| `srvprgfunc1` | int {40, 143}, 355 blank | `+0x030` u16 | server start / do / progressive function number | — | [C] |
| `srvprgfunc2` | int {36, 38, 143}, 353 blank | `+0x032` u16 | server start / do / progressive function number | — | [C] |
| `srvprgfunc3` | int {37, 39, 41}, 353 blank | `+0x034` u16 | server start / do / progressive function number | — | [C] |
| `prgcalc1` | formula, 2 distinct, 355 blank | `+0x038` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgcalc2` | formula, 2 distinct, 354 blank | `+0x03C` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgcalc3` | formula, 3 distinct, 353 blank | `+0x040` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgdam` | int {1, 2, 4}, 352 blank | `+0x044` u16 | progressive-charge values | — | [C] |
| `srvmissile` | str, 42 distinct, 309 blank | `+0x046` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `decquant` | int {1}, 345 blank | `+0x004` bit 0 | consumes item quantity (throws) | — | [C] |
| `lob` | int {1}, 354 blank | `+0x004` bit 1 | lobbed missile | — | [C] |
| `srvmissilea` | str, 93 distinct, 260 blank | `+0x048` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvmissileb` | str, 26 distinct, 330 blank | `+0x04A` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvmissilec` | str, 20 distinct, 337 blank | `+0x04C` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvoverlay` | str, 7 distinct, 349 blank | `+0x04E` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `aurafilter` | int 2..303747 (18 distinct), 308 blank | `+0x050` u32 | aura target filter bits | — | [C] |
| `aurastate` | str, 65 distinct, 283 blank | `+0x080` u16 index | state put on the caster / the aura's targets | `states:state` | [C] |
| `auratargetstate` | str, 44 distinct, 310 blank | `+0x082` u16 index | state put on the caster / the aura's targets | `states:state` | [C] |
| `auralencalc` | formula, 24 distinct, 296 blank | `+0x060` s32 calc | aura duration / radius formula | `skillscode.bin` | [C] |
| `aurarangecalc` | formula, 15 distinct, 279 blank | `+0x064` s32 calc | aura duration / radius formula | `skillscode.bin` | [C] |
| `aurastat1` | str, 35 distinct, 278 blank | `+0x054` u16 index | aura stat 1 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc1` | formula, 35 distinct, 284 blank | `+0x068` s32 calc | aura stat 1 and its value formula | `skillscode.bin` | [C] |
| `aurastat2` | str, 27 distinct, 306 blank | `+0x056` u16 index | aura stat 2 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc2` | formula, 32 distinct, 305 blank | `+0x06C` s32 calc | aura stat 2 and its value formula | `skillscode.bin` | [C] |
| `aurastat3` | str, 18 distinct, 329 blank | `+0x058` u16 index | aura stat 3 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc3` | formula, 21 distinct, 329 blank | `+0x070` s32 calc | aura stat 3 and its value formula | `skillscode.bin` | [C] |
| `aurastat4` | str, 7 distinct, 344 blank | `+0x05A` u16 index | aura stat 4 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc4` | formula, 11 distinct, 344 blank | `+0x074` s32 calc | aura stat 4 and its value formula | `skillscode.bin` | [C] |
| `aurastat5` | str {`coldresist`, `curse_resistance`}, 355 blank | `+0x05C` u16 index | aura stat 5 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc5` | formula, 2 distinct, 355 blank | `+0x078` s32 calc | aura stat 5 and its value formula | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `aurastat6` | str {`damageresist`, `poisonresist`}, 355 blank | `+0x05E` u16 index | aura stat 6 and its value formula | `itemstatcost:Stat` | [C] |
| `aurastatcalc6` | formula, 2 distinct, 355 blank | `+0x07C` s32 calc | aura stat 6 and its value formula | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `auraevent1` | str, 5 distinct, 347 blank | `+0x084` u16 index | aura event 1 and its handler number | `events:event` | [C] |
| `auraeventfunc1` | int 1..27 (10 distinct), 347 blank | `+0x08A` u16 | aura event 1 and its handler number | — | [C] |
| `auraevent2` | str {`damagedbymissile`, `damagedinmelee`}, 355 blank | `+0x086` u16 index | aura event 2 and its handler number | `events:event` | [C] |
| `auraeventfunc2` | int {5, 26}, 355 blank | `+0x08C` u16 | aura event 2 and its handler number | — | [C] |
| `auraevent3` | str {`damagedbymissile`}, 356 blank | `+0x088` u16 index | aura event 3 and its handler number | `events:event` | [C] |
| `auraeventfunc3` | int {26}, 356 blank | `+0x08E` u16 | aura event 3 and its handler number | — | [C] |
| `auratgtevent` | blank in all rows | `+0x090` u16 index | aura target event and handler number | `events:event` | [C] value; slot by stride `[L]` |
| `auratgteventfunc` | blank in all rows | `+0x092` u16 | aura target event and handler number | — | [C] value; slot by stride `[L]` |
| `passivestate` | str, 28 distinct, 328 blank | `+0x094` u16 index | state of a passive skill | `states:state` | [C] |
| `passiveitype` | str, 7 distinct, 349 blank | `+0x096` u16 index | item type a passive needs | `itemtypes:Code` | [C] |
| `passivestat1` | str, 30 distinct, 306 blank | `+0x098` u16 index | passive stat 1 and its value formula | `itemstatcost:Stat` | [C] |
| `passivecalc1` | formula, 22 distinct, 306 blank | `+0x0A4` s32 calc | passive stat 1 and its value formula | `skillscode.bin` | [C] |
| `passivestat2` | str, 11 distinct, 331 blank | `+0x09A` u16 index | passive stat 2 and its value formula | `itemstatcost:Stat` | [C] |
| `passivecalc2` | formula, 13 distinct, 331 blank | `+0x0A8` s32 calc | passive stat 2 and its value formula | `skillscode.bin` | [C] |
| `passivestat3` | str, 7 distinct, 340 blank | `+0x09C` u16 index | passive stat 3 and its value formula | `itemstatcost:Stat` | [C] |
| `passivecalc3` | formula, 10 distinct, 340 blank | `+0x0AC` s32 calc | passive stat 3 and its value formula | `skillscode.bin` | [C] |
| `passivestat4` | str {`armorclass`, `damagepercent`, `poisonresist`}, 351 blank | `+0x09E` u16 index | passive stat 4 and its value formula | `itemstatcost:Stat` | [C] |
| `passivecalc4` | formula, 5 distinct, 351 blank | `+0x0B0` s32 calc | passive stat 4 and its value formula | `skillscode.bin` | [C] |
| `passivestat5` | blank in all rows | `+0x0A0` u16 index | passive stat 5 and its value formula | `itemstatcost:Stat` | [C] value; slot by stride `[L]` |
| `passivecalc5` | blank in all rows | `+0x0B4` s32 calc | passive stat 5 and its value formula | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `passiveevent` | blank in all rows | `+0x0B8` u16 index | passive event and handler number | `events:event` | [C] value; slot by stride `[L]` |
| `passiveeventfunc` | blank in all rows | `+0x0BA` u16 | passive event and handler number | — | [C] value; slot by stride `[L]` |
| `summon` | str, 31 distinct, 325 blank | `+0x0BC` u16 index (case-insensitive) | monster class summoned | `monstats:Id` | [C] |
| `pettype` | str, 16 distinct, 326 blank | `+0x0BE` u8 index | pet type of the summon | `pettype:pet type` | [C] |
| `petmax` | formula, 7 distinct, 329 blank | `+0x0C0` s32 calc | pet count formula | `skillscode.bin` | [C] |
| `summode` | str {`NU`, `S1`, `S2`}, 325 blank | `+0x0BF` u8 index | mode the summon spawns in | `monmode:code` | [C] |
| `sumskill1` | str, 14 distinct, 341 blank | `+0x0C4` u16 index (case-insensitive) | skill 1 given to the summon and its level formula | `skills:skill` | [C] |
| `sumsk1calc` | formula, 4 distinct, 341 blank | `+0x0D0` s32 calc | skill 1 given to the summon and its level formula | `skillscode.bin` | [C] |
| `sumskill2` | str, 7 distinct, 348 blank | `+0x0C6` u16 index (case-insensitive) | skill 2 given to the summon and its level formula | `skills:skill` | [C] |
| `sumsk2calc` | formula, 5 distinct, 348 blank | `+0x0D4` s32 calc | skill 2 given to the summon and its level formula | `skillscode.bin` | [C] |
| `sumskill3` | str, 7 distinct, 350 blank | `+0x0C8` u16 index (case-insensitive) | skill 3 given to the summon and its level formula | `skills:skill` | [C] |
| `sumsk3calc` | formula, 7 distinct, 350 blank | `+0x0D8` s32 calc | skill 3 given to the summon and its level formula | `skillscode.bin` | [C] |
| `sumskill4` | str {`Critical Strike`, `Death Sentry`, `Lightning Sentry`}, 352 blank | `+0x0CA` u16 index (case-insensitive) | skill 4 given to the summon and its level formula | `skills:skill` | [C] |
| `sumsk4calc` | formula, 3 distinct, 352 blank | `+0x0DC` s32 calc | skill 4 given to the summon and its level formula | `skillscode.bin` | [C] |
| `sumskill5` | str {`Death Sentry`}, 356 blank | `+0x0CC` u16 index (case-insensitive) | skill 5 given to the summon and its level formula | `skills:skill` | [C] |
| `sumsk5calc` | formula, 1 distinct, 356 blank | `+0x0E0` s32 calc | skill 5 given to the summon and its level formula | `skillscode.bin` | [C] |
| `sumumod` | int {32, 33, 42}, 351 blank | `+0x0E4` u16 | unique mod given to the summon | — | [C] |
| `sumoverlay` | str {`dopllezon_appear`, `spawnedminion`}, 355 blank | `+0x0E6` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `stsuccessonly` | int {1}, 340 blank | `+0x005` bit 4 | sound | — | [C] |
| `stsound` | str, 62 distinct, 207 blank | `+0x0FC` u16 index | sound | `sounds:Sound` | [C] |
| `stsoundclass` | str, 14 distinct, 339 blank | `+0x0FE` u16 index | sound | `sounds:Sound` | [C] |
| `stsounddelay` | int {1}, 346 blank | `+0x005` bit 5 | sound | — | [C] |
| `weaponsnd` | int {1}, 352 blank | `+0x005` bit 6 | sound | — | [C] |
| `dosound` | str, 10 distinct, 343 blank | `+0x100` u16 index | sound | `sounds:Sound` | [C] |
| `dosound a` | str {`druidpod_walk1_1`, `paladin_charge`, `weapon_1ht_1`}, 354 blank | `+0x102` u16 index | sound | `sounds:Sound` | [C] |
| `dosound b` | str {`druidpod_neutral_1`, `weapon_2ht_1`}, 355 blank | `+0x104` u16 index | sound | `sounds:Sound` | [C] |
| `tgtoverlay` | str, 5 distinct, 352 blank | `+0x108` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `tgtsound` | str, 5 distinct, 350 blank | `+0x10A` u16 index | sound | `sounds:Sound` | [C] |
| `prgoverlay` | str, 6 distinct, 351 blank | `+0x10C` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `prgsound` | str, 6 distinct, 351 blank | `+0x10E` u16 index | sound | `sounds:Sound` | [C] |
| `castoverlay` | str, 19 distinct, 307 blank | `+0x106` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `cltoverlaya` | str, 5 distinct, 352 blank | `+0x110` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `cltoverlayb` | str {`bear_undo`, `wolf_undo`}, 355 blank | `+0x112` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `cltstfunc` | int 0..82 (52 distinct), 250 blank | `+0x0F2` u16 | client start / do / progressive function number | — | [C] |
| `cltdofunc` | int 0..95 (75 distinct), 224 blank | `+0x0F4` u16 | client start / do / progressive function number | — | [C] |
| `cltprgfunc1` | int 12..93 (7 distinct), 348 blank | `+0x0F6` u16 | client start / do / progressive function number | — | [C] |
| `cltprgfunc2` | int 9..83 (5 distinct), 351 blank | `+0x0F8` u16 | client start / do / progressive function number | — | [C] |
| `cltprgfunc3` | int 9..15 (5 distinct), 351 blank | `+0x0FA` u16 | client start / do / progressive function number | — | [C] |
| `cltmissile` | str, 41 distinct, 306 blank | `+0x0E8` u16 index | missiles the client side draws | `missiles:Missile` | [C] |
| `cltmissilea` | str, 102 distinct, 238 blank | `+0x0EA` u16 index | missiles the client side draws | `missiles:Missile` | [C] |
| `cltmissileb` | str, 36 distinct, 316 blank | `+0x0EC` u16 index | missiles the client side draws | `missiles:Missile` | [C] |
| `cltmissilec` | str, 17 distinct, 326 blank | `+0x0EE` u16 index | missiles the client side draws | `missiles:Missile` | [C] |
| `cltmissiled` | str {`vine beast neutral`}, 356 blank | `+0x0F0` u16 index | missiles the client side draws | `missiles:Missile` | [C] |
| `cltcalc1` | formula, 11 distinct, 339 blank | `+0x114` s32 calc | client-side formula | `skillscode.bin` | [C] |
| `cltcalc2` | formula, 5 distinct, 351 blank | `+0x118` s32 calc | client-side formula | `skillscode.bin` | [C] |
| `cltcalc3` | int {3, 6, 15}, 353 blank | `+0x11C` s32 calc | client-side formula | `skillscode.bin` | [C] |
| `warp` | int {1}, 355 blank | `+0x008` bit 6 | behaviour flag (name reading) | — | [C] |
| `immediate` | int {1}, 347 blank | `+0x005` bit 7 | behaviour flag (name reading) | — | [C] |
| `enhanceable` | int {1}, 11 blank | `+0x006` bit 1 | behaviour flag (name reading) | — | [C] |
| `attackrank` | int 0..10 (11 distinct), 0 blank | `+0x18E` u8 | AI attack rank | — | [C] |
| `noammo` | int {1}, 356 blank | `+0x006` bit 0 | behaviour flag (name reading) | — | [C] |
| `range` | str {`both`, `h2h`, `none`, `rng`}, 0 blank | `+0x014` u8 keyword | keyword `none`/`h2h`/`rng`/`both`, stored as its position 0..3 | — | [C] |
| `weapsel` | int {1, 2, 3, 4}, 342 blank | `+0x168` u16 | weapon selection mode | — | [C] |
| `itypea1` | str, 9 distinct, 303 blank | `+0x018` u16 index | `[I]` first item-type requirement: the staff-mod skill test reads `+0x18` and accepts the skill when it is empty or the item is of that type ([items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260)) | `itemtypes:Code` | [C] |
| `itypea2` | str {`miss`}, 355 blank | `+0x01A` u16 index | item types the skill needs (a: first hand, b: second hand) | `itemtypes:Code` | [C] |
| `itypea3` | blank in all rows | `+0x01C` u16 index | item types the skill needs (a: first hand, b: second hand) | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypea1` | str {`tpot`}, 355 blank | `+0x024` u16 index | item types the skill refuses | `itemtypes:Code` | [C] |
| `etypea2` | blank in all rows | `+0x026` u16 index | item types the skill refuses | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `itypeb1` | str {`h2h`, `mele`, `thro`}, 352 blank | `+0x01E` u16 index | item types the skill needs (a: first hand, b: second hand) | `itemtypes:Code` | [C] |
| `itypeb2` | blank in all rows | `+0x020` u16 index | item types the skill needs (a: first hand, b: second hand) | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `itypeb3` | blank in all rows | `+0x022` u16 index | item types the skill needs (a: first hand, b: second hand) | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypeb1` | blank in all rows | `+0x028` u16 index | item types the skill refuses | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypeb2` | blank in all rows | `+0x02A` u16 index | item types the skill refuses | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `anim` | str, 10 distinct, 23 blank | `+0x010` u8 index | player / monster animation mode and sequence | `plrmode:Code` | [C] |
| `seqtrans` | str, 10 distinct, 23 blank | `+0x012` u8 index | player / monster animation mode and sequence | `plrmode:Code` | [C] |
| `monanim` | str, 8 distinct, 0 blank | `+0x011` u8 index | player / monster animation mode and sequence | `monmode:code` | [C] |
| `seqnum` | int 1..41 (23 distinct), 323 blank | `+0x013` u8 | player / monster animation mode and sequence | — | [C] |
| `seqinput` | int {8, 10, 12}, 353 blank | `+0x016` u16 | player / monster animation mode and sequence | — | [C] |
| `durability` | int {1}, 344 blank | `+0x006` bit 2 | behaviour flag (name reading) | — | [C] |
| `UseAttackRate` | int {1}, 205 blank | `+0x006` bit 3 | behaviour flag (name reading) | — | [C] |
| `LineOfSight` | int {4}, 309 blank | `+0x18F` u8 | behaviour flag (name reading) | — | [C] |
| `TargetableOnly` | int {1}, 312 blank | `+0x006` bit 4 | behaviour flag (name reading) | — | [C] |
| `SearchEnemyXY` | int {1}, 308 blank | `+0x006` bit 5 | behaviour flag (name reading) | — | [C] |
| `SearchEnemyNear` | int {1}, 337 blank | `+0x006` bit 6 | behaviour flag (name reading) | — | [C] |
| `SearchOpenXY` | int {1}, 347 blank | `+0x006` bit 7 | behaviour flag (name reading) | — | [C] |
| `SelectProc` | int 1..6 (6 distinct), 348 blank | `+0x015` u8 | target selection procedure number | — | [C] |
| `TargetCorpse` | int {1}, 339 blank | `+0x007` bit 0 | behaviour flag (name reading) | — | [C] |
| `TargetPet` | int {1}, 354 blank | `+0x007` bit 1 | behaviour flag (name reading) | — | [C] |
| `TargetAlly` | int {1}, 355 blank | `+0x007` bit 2 | behaviour flag (name reading) | — | [C] |
| `TargetItem` | int {1}, 354 blank | `+0x007` bit 3 | behaviour flag (name reading) | — | [C] |
| `AttackNoMana` | int {1}, 316 blank | `+0x007` bit 4 | behaviour flag (name reading) | — | [C] |
| `TgtPlaceCheck` | int {1}, 355 blank | `+0x008` bit 0 | behaviour flag (name reading) | — | [C] |
| `ItemEffect` | int {1, 36, 151}, 285 blank | `+0x16A` u16 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemCltEffect` | int {10, 96}, 354 blank | `+0x16C` u16 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemTgtDo` | int {1}, 356 blank | `+0x007` bit 5 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemTarget` | int {1, 2, 3, 4}, 351 blank | `+0x120` u16 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemCheckStart` | int {1}, 355 blank | `+0x008` bit 1 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemCltCheckStart` | int {1}, 355 blank | `+0x008` bit 2 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemCastSound` | str, 16 distinct, 309 blank | `+0x122` u16 index | sound | `sounds:Sound` | [C] |
| `ItemCastOverlay` | str, 9 distinct, 344 blank | `+0x124` u16 index | overlay (graphic effect) | `overlay:overlay` | [C] |
| `skpoints` | blank in all rows | `+0x170` s32 calc | skill-point cost formula | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `reqlevel` | int 1..30 (6 distinct), 0 blank | `+0x174` u16 | character level required | — | [C] |
| `maxlvl` | int {20}, 147 blank | `+0x12C` u16 | highest level | — | [C] |
| `reqstr` | blank in all rows | `+0x176` u16 | attribute requirement | — | [C] value; slot by stride `[L]` |
| `reqdex` | blank in all rows | `+0x178` u16 | attribute requirement | — | [C] value; slot by stride `[L]` |
| `reqint` | blank in all rows | `+0x17A` u16 | attribute requirement | — | [C] value; slot by stride `[L]` |
| `reqvit` | blank in all rows | `+0x17C` u16 | attribute requirement | — | [C] value; slot by stride `[L]` |
| `reqskill1` | str, 130 distinct, 211 blank | `+0x17E` u16 index | prerequisite skill | `skills:skill` | [C] |
| `reqskill2` | str, 24 distinct, 331 blank | `+0x180` u16 index | prerequisite skill | `skills:skill` | [C] |
| `reqskill3` | blank in all rows | `+0x182` u16 index | prerequisite skill | `skills:skill` | [C] value; slot by stride `[L]` |
| `restrict` | int {1, 2}, 331 blank | `+0x228` u8 | shapeshift restriction | — | [C] |
| `State1` | str {`bear`, `wolf`}, 350 blank | `+0x22A` u16 index | states the restriction refers to | `states:state` | [C] |
| `State2` | str {`bear`}, 355 blank | `+0x22C` u16 index | states the restriction refers to | `states:state` | [C] |
| `State3` | blank in all rows | `+0x22E` u16 index | states the restriction refers to | `states:state` | [C] value; slot by stride `[L]` |
| `delay` | int 15..150 (9 distinct), 334 blank | `+0x190` s32 calc | cast delay formula | `skillscode.bin` | [C] |
| `leftskill` | int {1}, 261 blank | `+0x007` bit 6 | behaviour flag (name reading) | — | [C] |
| `repeat` | int {1}, 354 blank | `+0x005` bit 3 | behaviour flag (name reading) | — | [C] (the other probe candidates lie inside fields other columns pin) |
| `checkfunc` | int 1..6 (6 distinct), 339 blank | — (not compiled) | check function number | — | [C] (no field) |
| `nocostinstate` | int {1}, 355 blank | — (not compiled) | behaviour flag (name reading) | — | [C] (no field) |
| `usemanaondo` | int {1}, 355 blank | `+0x008` bit 5 | behaviour flag (name reading) | — | [C] |
| `startmana` | int {6}, 354 blank | `+0x184` u16 | mana cost terms | — | [C] |
| `minmana` | int {0, 1}, 141 blank | `+0x186` u16 | mana cost terms | — | [C] |
| `manashift` | int 2..8 (6 distinct), 141 blank | `+0x188` u16 | mana cost terms | — | [C] |
| `mana` | int 0..76 (39 distinct), 141 blank | `+0x18A` s16 | mana cost terms | — | [C] |
| `lvlmana` | int -3..10 (8 distinct), 141 blank | `+0x18C` s16 | mana cost terms | — | [C] |
| `interrupt` | int {1}, 22 blank | `+0x007` bit 7 | behaviour flag (name reading) | — | [C] |
| `InTown` | int {1}, 294 blank | `+0x005` bit 0 | behaviour flag (name reading) | — | [C] |
| `aura` | int {1}, 331 blank | `+0x004` bit 5 | behaviour flag (name reading) | — | [C] |
| `periodic` | int {1}, 355 blank | `+0x004` bit 6 | behaviour flag (name reading) | — | [C] |
| `perdelay` | formula, 3 distinct, 335 blank | `+0x128` s32 calc | periodic delay formula | `skillscode.bin` | [C] |
| `finishing` | int {1}, 352 blank | `+0x004` bit 3 | behaviour flag (name reading) | — | [C] |
| `passive` | int {1}, 331 blank | `+0x004` bit 4 | behaviour flag (name reading) | — | [C] |
| `progressive` | int {1}, 351 blank | `+0x004` bit 2 | behaviour flag (name reading) | — | [C] (the other probe candidates lie inside fields other columns pin) |
| `general` | int {1}, 351 blank | `+0x008` bit 3 | behaviour flag (name reading) | — | [C] |
| `scroll` | str {`␠`, `1`}, 352 blank | `+0x008` bit 4 | behaviour flag (name reading) | — | [C] |
| `calc1` | formula, 65 distinct, 237 blank | `+0x138` s32 calc | general formula 1 (referenced by other formulas) | `skillscode.bin` | [C] |
| `calc2` | formula, 31 distinct, 297 blank | `+0x13C` s32 calc | general formula 2 (referenced by other formulas) | `skillscode.bin` | [C] |
| `calc3` | formula, 12 distinct, 336 blank | `+0x140` s32 calc | general formula 3 (referenced by other formulas) | `skillscode.bin` | [C] |
| `calc4` | formula, 11 distinct, 339 blank | `+0x144` s32 calc | general formula 4 (referenced by other formulas) | `skillscode.bin` | [C] |
| `Param1` | int -50..3600 (46 distinct), 97 blank | `+0x148` s32 | general parameter 1 | — | [C] |
| `Param2` | int -2..1500 (35 distinct), 119 blank | `+0x14C` s32 | general parameter 2 | — | [C] |
| `Param3` | int -50..4500 (44 distinct), 165 blank | `+0x150` s32 | general parameter 3 | — | [C] |
| `Param4` | int -40..500 (35 distinct), 176 blank | `+0x154` s32 | general parameter 4 | — | [C] |
| `Param5` | int -75..3000 (30 distinct), 239 blank | `+0x158` s32 | general parameter 5 | — | [C] |
| `Param6` | int -1..300 (22 distinct), 257 blank | `+0x15C` s32 | general parameter 6 | — | [C] |
| `Param7` | int -50..250 (19 distinct), 316 blank | `+0x160` s32 | general parameter 7 | — | [C] |
| `Param8` | int 1..125 (23 distinct), 245 blank | `+0x164` s32 | general parameter 8 | — | [C] |
| `InGame` | int {1}, 0 blank | `+0x005` bit 2 | behaviour flag (name reading) | — | [C] value; slot `[L]` (1 in every row: the last free bit of the flag run) |
| `ToHit` | int 10..300 (11 distinct), 299 blank | `+0x198` s32 | attack rating bonus (base, per level, formula) | — | [C] |
| `LevToHit` | int 5..35 (9 distinct), 298 blank | `+0x19C` s32 | attack rating bonus (base, per level, formula) | — | [C] |
| `ToHitCalc` | formula, 3 distinct, 354 blank | `+0x1A0` s32 calc | attack rating bonus (base, per level, formula) | `skillscode.bin` | [C] |
| `ResultFlags` | int 1..16385 (7 distinct), 342 blank | `+0x12E` u16 | hit result / hit flags / hit class | — | [C] |
| `HitFlags` | int {2}, 354 blank | `+0x130` u32 | hit result / hit flags / hit class | — | [C] |
| `HitClass` | int 3..157 (6 distinct), 351 blank | `+0x134` u32 | hit result / hit flags / hit class | — | [C] |
| `Kick` | int {1}, 353 blank | `+0x005` bit 1 | behaviour flag (name reading) | — | [C] |
| `HitShift` | int 1..8 (8 distinct), 7 blank | `+0x1A4` u8 | damage shift (fractional damage) | — | [C] |
| `SrcDam` | int {32, 48, 96, 128}, 294 blank | `+0x1A5` u8 | share of weapon damage | — | [C] |
| `MinDam` | int 1..30 (13 distinct), 328 blank | `+0x1A8` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MinLevDam1` | int 1..10 (9 distinct), 329 blank | `+0x1B0` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MinLevDam2` | int 1..15 (11 distinct), 329 blank | `+0x1B4` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MinLevDam3` | int 1..20 (10 distinct), 329 blank | `+0x1B8` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MinLevDam4` | int 1..26 (11 distinct), 329 blank | `+0x1BC` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MinLevDam5` | int 1..30 (14 distinct), 329 blank | `+0x1C0` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxDam` | int 1..60 (12 distinct), 328 blank | `+0x1AC` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxLevDam1` | int 1..10 (9 distinct), 329 blank | `+0x1C4` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxLevDam2` | int 1..15 (11 distinct), 329 blank | `+0x1C8` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxLevDam3` | int 1..21 (12 distinct), 329 blank | `+0x1CC` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxLevDam4` | int 1..26 (13 distinct), 329 blank | `+0x1D0` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `MaxLevDam5` | int 1..30 (13 distinct), 329 blank | `+0x1D4` s32 | physical damage (base, per-level bands, synergy formula) | — | [C] |
| `DmgSymPerCalc` | formula, 6 distinct, 351 blank | `+0x1D8` s32 calc | physical damage (base, per-level bands, synergy formula) | `skillscode.bin` | [C] |
| `EType` | str, 6 distinct, 257 blank | `+0x1DC` u8 index | elemental damage (type, base, per-level bands, synergy formula) | `elemtypes:Code` | [C] |
| `EMin` | int 0..150 (25 distinct), 265 blank | `+0x1E0` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMinLev1` | int 0..48 (23 distinct), 266 blank | `+0x1E8` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMinLev2` | int 0..48 (28 distinct), 266 blank | `+0x1EC` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMinLev3` | int 0..79 (31 distinct), 266 blank | `+0x1F0` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMinLev4` | int 0..81 (40 distinct), 266 blank | `+0x1F4` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMinLev5` | int 0..100 (41 distinct), 266 blank | `+0x1F8` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMax` | int 2..200 (33 distinct), 269 blank | `+0x1E4` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMaxLev1` | int 1..48 (23 distinct), 269 blank | `+0x1FC` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMaxLev2` | int 1..48 (32 distinct), 269 blank | `+0x200` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMaxLev3` | int 1..81 (35 distinct), 269 blank | `+0x204` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMaxLev4` | int 1..83 (43 distinct), 269 blank | `+0x208` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EMaxLev5` | int 1..100 (50 distinct), 269 blank | `+0x20C` s32 | elemental damage (type, base, per-level bands, synergy formula) | — | [C] |
| `EDmgSymPerCalc` | formula, 59 distinct, 293 blank | `+0x210` s32 calc | elemental damage (type, base, per-level bands, synergy formula) | `skillscode.bin` | [C] |
| `ELen` | int 10..200 (8 distinct), 325 blank | `+0x214` s32 | elemental duration (base, per-level bands, synergy formula) | — | [C] |
| `ELevLen1` | int 5..50 (7 distinct), 334 blank | `+0x218` s32 | elemental duration (base, per-level bands, synergy formula) | — | [C] |
| `ELevLen2` | int 5..50 (7 distinct), 332 blank | `+0x21C` s32 | elemental duration (base, per-level bands, synergy formula) | — | [C] |
| `ELevLen3` | int 2..50 (8 distinct), 332 blank | `+0x220` s32 | elemental duration (base, per-level bands, synergy formula) | — | [C] |
| `ELenSymPerCalc` | formula, 4 distinct, 353 blank | `+0x224` s32 calc | elemental duration (base, per-level bands, synergy formula) | `skillscode.bin` | [C] |
| `aitype` | int 1..13 (9 distinct), 325 blank | `+0x230` u16 | AI use type / bonus | — | [C] |
| `aibonus` | int {-3, 3}, 355 blank | `+0x232` s16 | AI use type / bonus | — | [C] |
| `cost mult` | int 256..896 (6 distinct), 147 blank | `+0x234` s32 | price multiplier | — | [C] |
| `cost add` | int 0..64000 (7 distinct), 0 blank | `+0x238` s32 | price addend | — | [C] |

### Encodings particular to this table

- `[C]` **Packed flags** `+0x004..+0x008`: 39 columns, one bit each, in the bit order of the table above (not the
  header order). `scroll` holds `1` on four rows and a single space on `MaggotEgg`; all five have the bit set, so a bit
  is set by any non-zero cell value (a space parses as −16, [excel-bin.md](../formats/excel-bin.md#integers)).
- `[C]` **`range`** is a keyword stored as its position in the list `none`, `h2h`, `rng`, `both` (0..3; 271/43/41/2
  rows). The list is not a table.
- `[C]` **Case-insensitive name lookups**: `summon` (`ClayGolem`, `BloodGolem`, `IronGolem`, `FireGolem` → monstats
  `claygolem` …) and `sumskill1`/`sumskill2` (`dodge`, `holy fire`, `avoid` → `Dodge`, `Holy Fire`, `Avoid`) store the
  row index of a key that differs only in case. (tbl:Skills.txt:summon, tbl:Skills.txt:sumskill1)
- `[C]` **Calc columns** (36: `prgcalc1..3`, `auralencalc`, `aurarangecalc`, `aurastatcalc1..6`, `passivecalc1..5`,
  `petmax`, `sumsk1calc..5`, `cltcalc1..3`, `perdelay`, `calc1..4`, `skpoints`, `delay`, `ToHitCalc`,
  `DmgSymPerCalc`, `EDmgSymPerCalc`, `ELenSymPerCalc`) are s32 offsets into `skillscode.bin`, −1 when blank, as in
  [excel-bin.md § Calc columns](../formats/excel-bin.md#calc-columns-formulas). Their bytecode is `data/calc`.
- `[C]` Not compiled: `checkfunc` (1..6 on 18 rows; no offset under any integer encoding) and `nocostinstate` (1 on
  `Wearwolf` and `Wearbear`; no byte or bit follows it). Both may be compile-time only or read by name `[L]`.

## Combat survey (plan 0037 Phase 0)

Which rows carry each column that by its name feeds damage or to-hit, and the normal attack's row. Offsets are
§ [Columns](#columns) (`[C]`, `excel_bin.py diff`); the counts are
`python3 -I tools/combat_survey.py skills workspace/merged/data/global/excel` (gate survey `combat`) over the 357 rows,
`[C]` as data. Only band 1 of each per-level group is counted (bands 2–5 have the same blank counts, § Columns). Meanings `[L]`.

| Column | `.bin` field | Rows set | Values |
|---|---|---:|---|
| `ToHit` | `+0x198` s32 | 58 | 10..300 |
| `LevToHit` | `+0x19C` s32 | 59 | 5..35 |
| `ToHitCalc` | `+0x1A0` calc | 3 | 3 formulas |
| `HitShift` | `+0x1A4` u8 | 350 | 1..8 |
| `SrcDam` | `+0x1A5` u8 | 63 | 32, 48, 96, 128 |
| `MinDam`, `MaxDam` | `+0x1A8`, `+0x1AC` s32 | 29, 29 | 1..30, 1..60 |
| `MinLevDam1`, `MaxLevDam1` | `+0x1B0`, `+0x1C4` s32 | 28, 28 | 1..10, 1..10 |
| `DmgSymPerCalc` | `+0x1D8` calc | 6 | 6 formulas |
| `EType` | `+0x1DC` u8 [ElemTypes](ElemTypes.md) row | 100 | `fire` 35, `cold` 22, `ltng` 20, `mag` 13, `pois` 8, `stun` 2 |
| `EMin`, `EMax` | `+0x1E0`, `+0x1E4` s32 | 92, 88 | 0..150, 2..200 |
| `EMinLev1`, `EMaxLev1` | `+0x1E8`, `+0x1FC` s32 | 91, 88 | 0..48, 1..48 |
| `EDmgSymPerCalc` | `+0x210` calc | 64 | 59 formulas |
| `ELen`, `ELevLen1` | `+0x214`, `+0x218` s32 | 32, 23 | 10..200, 5..50 |
| `ELenSymPerCalc` | `+0x224` calc | 4 | 4 formulas |
| `HitFlags` | `+0x130` u32 | 3 | always 2 |
| `HitClass` | `+0x134` u32 | 6 | 3..157 |
| `Kick` | `+0x005` bit 1 | 4 | 1 |
| `range` | `+0x014` keyword | 357 | `none` 271, `h2h` 43, `rng` 41, `both` 2 |
| `weapsel` | `+0x168` u16 | 15 | 1..4 |
| `srvstfunc`, `srvdofunc` | `+0x02C`, `+0x02E` u16 | 112, 274 | 1..65, 1..152 |

- `[C]` 152 rows set `MinDam`, `EMin` or `SrcDam`. The 63 `SrcDam` rows are Amazon 18, Assassin 10, Barbarian 9,
  Druid 7, Paladin 5, Necromancer 1 and 13 with no `charclass` (monster and general skills). (tbl:Skills.txt:SrcDam,
  tbl:Skills.txt:EType)
- `[C]` **The normal attack row.** Row 0 `Attack` (`Id` 0, no `charclass`): `anim` `A1`, `monanim` `A1`, `range`
  `both`, `srvstfunc` 1, `srvdofunc` 1, `HitShift` 8, `SrcDam` 128, `ToHit` 0, `MinDam` 0, `EType` blank. The other
  general rows: `Kick` (1) `anim` `KK`, `srvdofunc` 2, `SrcDam` 0, `range` `h2h`; `Throw` (2) `TH`, `srvdofunc` 3,
  `SrcDam` 128, `rng`; `Left Hand Throw` (4) `S4`, `srvdofunc` 5, `SrcDam` 0, `rng`; `Left Hand Swing` (5) `S3`,
  `srvdofunc` 1, `SrcDam` 0, `both`; all `HitShift` 8. (tbl:Skills.txt:anim, tbl:Skills.txt:srvdofunc)
- `[L]` By the names, `SrcDam` is the share of weapon damage out of 128 a skill uses (128 for the plain attack and
  throw) and `HitShift` the fixed-point shift of the skill's own damage (8 = whole points). `ToHitCalc` feeds
  `SKILLS_GetToHit` ([data/calc](../specs/data/calc.md) open question). A skill's own damage packet is ADR-0014
  phase (3); plan 0037 takes it as an input.

## Open questions

- `[L]` How the per-class lists at `DataTables+0xBA4..+0xBAC` are built at load (their builder is not read). What
  `firstSkill(class)` returns is settled for classes 1–6 in [§ Class blocks](#class-blocks); class 0 was not logged.
- `[L]` Whether `Id` is a u16 or a u32 (`+0x002` is 0 in every record).
- `[L]` Every meaning not tagged in the table; none is needed by the item, monster or DRLG subsystems so far.
