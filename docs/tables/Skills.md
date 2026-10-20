# Skills (`data/global/excel/skills.txt` → `skills.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 357 (no `Expansion` marker)   **Record:** 572 B (`0x23C`)
> **sha256:** `.txt` `465c28e83657540e0d7ae5b0de826d5657be7fba1aa539a85c3ca3aeea34b498`, `.bin` `0b57ba62b6b5c74be6a579adb9327641ecfe880ebc0c217d341c9d5bba89043b`, `skillscode.bin` `d42e1da6ebdf835c0c623f13c77201e3c2a25659dc58eff215af3cacc7ecf30f`
> **Doc status:** layout complete (every compiled column placed, `[C]` by diff); passive and aura rows listed (plan 0041 Phase 0); dispatch columns surveyed (plan 0045 Phase 0); semantics `[C]`/`[I]` for
> the columns the item code, the formula readers and the combat findings read, `[L]` elsewhere until the skills machinery is read ([plan 0045](../plans/0045-skills-missiles-machinery.md) Phase 1)

## Purpose

One row per skill: the 210 character-class skills, plus monster, item and internal skills (`Attack`, `Kick`,
`Scroll of Identify`, `Wake Of Destruction Sentry`, …). A row holds the skill's server and client functions, missiles,
aura and passive stats, summon, item-type requirements, level and mana costs, damage and formulas. In this project
the reader so far is `items/affixes`: the staff-mods roll picks class skills by id and tests their item-type
requirement ([items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260),
plan 0021). The skills machinery (`skills/dispatch`, `skills/missiles`) is [plan 0045](../plans/0045-skills-missiles-machinery.md)
and the function catalogue [plan 0046](../plans/0046-skills-function-catalogue.md); their columns are § [Dispatch](#dispatch-plan-0045-phase-0).
Monster AI's choice of skill is ADR-0014 phase (5). Leads: no lead; derived from data.

## Row identity

- `[C]` The `.bin` is a u32 record count (357) and 357 records of 572 bytes, one per `.txt` row in order
  ([excel-bin.md](../formats/excel-bin.md)). The full-record loader allocates 572-byte records
  ([data/0001 § 4](../findings/data/0001-excel-loader.md#4-record-size-corroboration-all-88-bin-tables), `0x0061787B`);
  a 2-byte `skills` load (`0x00612E15`) runs only under `-txt`.
- `[C]` `Id` equals the row index in all 357 rows. The name key `skill` is not compiled; other tables' skill columns
  (`reqskill1`, `sumskill1`, and this table's own) store the row index of the name.
- `[I]` The item code addresses the records as `DataTables+0xB98` with stride `0x23C`, by skill id
  ([items/0005 § Data touched](../findings/items/0005-affixes.md#data-touched)).
- `[C]` **The pinned game's compile gives the shipped file.** Under `-direct -txt` it writes a `skills.bin`
  byte-identical to the shipped one (shipped in d2exp and patch_d2), so this layout is the one the binary's compiler
  produces ([experiments § run:2026-10-15-cube-saves, addendum
  2026-10-16](../formats/experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3), plan
  0039 A3). The `-txt`-only code-list load of the same `.txt` adds no file of its own.

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
| `passiveitype` | str, 7 distinct, 349 blank | `+0x096` u16 index | `[I]` the param of the passive stats: `SKILLS_RefreshPassive` writes `passivestat1..5` = `passivecalc` with this item type as their param ([stats/0002 § 4](../findings/stats/0002-states.md#4-auras-and-passives), fn:SKILLS_RefreshPassive@0x00646D60); "the item type a passive needs" `[L]` by the name | `itemtypes:Code` | [C] |
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
| `perdelay` | formula, 3 distinct, 335 blank | `+0x128` s32 calc | `[I]` the aura period in frames: `SKILLS_NextPeriodicFrame = ((frame − 1 + p) / p)·p + 1` with `p` = this calc, 5 when it gives less than 6; the item-aura and selected-aura events requeue at it ([stats/0002 § 4](../findings/stats/0002-states.md#4-auras-and-passives), fn:SKILLS_NextPeriodicFrame@0x0056CD50) | `skillscode.bin` | [C] |
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
  throw) and `HitShift` the fixed-point shift of the skill's own damage (8 = whole points). A skill's own damage
  packet is ADR-0014 phase (3); plan 0037 takes it as an input.
- `[I]` `ToHitCalc` is evaluated by `SKILLS_GetToHit` and its value is the attack-rating percent a skill's melee hit
  passes to the hit test ([data/calc § G](../specs/data/calc.md#g-variables),
  [combat/to-hit § A](../specs/combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll); fn:SKILLS_GetToHit@0x006449F0,
  0x005C76B0, tbl:Skills.txt:ToHitCalc).

## Passive and aura columns (plan 0041 Phase 0)

The columns that give a passive skill's and an aura's stat list, for the stat code plan 0041 Phase 1 reads. Offsets
and widths are § Columns (`[C]`, `excel_bin.py diff`, 84 966 cells, 0 mismatches); the rows and counts are
`python3 -I tools/stats_survey.py skills workspace/merged/data/global/excel` (gate survey `stats`), `[C]` as data.
A calc cell is an s32 offset into `skillscode.bin` (−1 blank) whose bytecode [data/calc](../specs/data/calc.md)
evaluates; the formulas below are the `.txt` cells. **Meanings `[L]`** (the column names).
(tbl:Skills.txt:passive, tbl:Skills.txt:aurastate)

| Column | `.bin` field | Rows set (of 357) | Values | Survey key |
|---|---|---:|---|---|
| `passive` | `+0x004` bit 4 | 26 | 1 | `sk_passive` |
| `aura` | `+0x004` bit 5 | 26 | 1 | `sk_aura` |
| `passivestate` | `+0x094` u16 [States](States.md) row, blank −1 | 29 | 28 distinct states | `sk_passivestate` |
| `passiveitype` | `+0x096` u16 [ItemTypes](ItemTypes.md) row | 8 | `axe`, `blun`, `h2h` ×2, `pole`, `swor`, `thro`, `spea` | `sk_passiveitype` |
| `passivestat1..5` | `+0x098`, `+0x09A`, `+0x09C`, `+0x09E`, `+0x0A0` u16 [ItemStatCost](ItemStatCost.md) row | 51, 26, 17, 6, 0 | 30, 11, 7, 3, 0 distinct stats | `sk_passivestat1`, `sk_passivestat_cells` = 100 |
| `passivecalc1..5` | `+0x0A4`, `+0x0A8`, `+0x0AC`, `+0x0B0`, `+0x0B4` s32 calc | 51, 26, 17, 6, 0 | 22, 13, 10, 5, 0 distinct formulas | `sk_passivecalc_cells` = 100 |
| `aurastate` | `+0x080` u16 States row | 74 | 65 distinct states | `sk_aurastate` |
| `auratargetstate` | `+0x082` u16 States row | 47 | 44 distinct states | `sk_auratargetstate` |
| `aurastat1..6` | `+0x054`, `+0x056`, `+0x058`, `+0x05A`, `+0x05C`, `+0x05E` u16 ItemStatCost row | 79, 51, 28, 13, 2, 2 | 35, 27, 18, 7, 2, 2 distinct stats | `sk_aurastat1`, `sk_aurastat_cells` = 175 |
| `aurastatcalc1..6` | `+0x068`, `+0x06C`, `+0x070`, `+0x074`, `+0x078`, `+0x07C` s32 calc | 73, 52, 28, 13, 2, 2 | 35, 32, 21, 11, 2, 2 distinct formulas | `sk_auracalc_cells` = 170 |
| `auralencalc` | `+0x060` s32 calc | 61 | 24 distinct formulas | `sk_auralencalc` |
| `aurarangecalc` | `+0x064` s32 calc | 78 | 15 distinct formulas | `sk_aurarangecalc` |
| `aurafilter` | `+0x050` u32 | 49 | 18 distinct values, `0x2`…`0x4A283` | `sk_aurafilter` |
| `auraevent1..3`, `auraeventfunc1..3` | `+0x084..+0x088` u16 `events` row, `+0x08A..+0x08E` u16 | 10, 2, 1 | 5 events, functions 1..27 | `sk_auraevent1` |

- `[C]` Every `passivestat` has its `passivecalc` (`sk_passivestat_without_calc` = 0). Six `aurastat` cells have no
  calc (the `progressive_*` stat of 254, 259, 265, 269, 274, 280; `sk_aurastat_without_calc` = 6) and one calc has
  no stat (117 `Holy Shield` `aurastatcalc2`, `sk_auracalc_without_stat` = 1). (tbl:Skills.txt:aurastatcalc2)
- `[C]` **Three rows set both `passive` and `aura`:** 127 `Sword Mastery`, 128 `Axe Mastery`, 129 `Mace Mastery`
  (`.txt` cells 1 and 1, `+0x004` = `0x30`); they have passive columns only, no aura column. 134 `Pole Arm Mastery`
  and the other masteries set `passive` alone. Whether the aura bit changes anything for them is Phase 1.
- `[C]` The passive columns reach beyond the `passive` rows: 28 rows have a `passivestat1` and no `passive` bit
  (`sk_passivestat_no_flag`): 15 summons and sentries (32 `Valkyrie`, 62 `Hydra`, 70 `Raise Skeleton`, 75
  `Clay Golem`, 80, 85, 90, 94, 95, 227, 237, 247, 257, 268, 279), the spirits 226, 236, 246, eight paladin auras
  (100, 102, 105, 108, 110, 114, 118, 122) and 264 `Cloak of Shadows`, 267 `Fade`. `[L]` For a summon the list
  reads as the summoned monster's stats.
- `[C]` The aura columns reach beyond the `aura` rows: 51 rows have an `aurastate` and no `aura` bit
  (`sk_aurastate_no_flag`), and none of the 26 `aura` rows has an `auralencalc` (`sk_auralencalc_aura` = 0), while
  57 of the 61 `auralencalc` rows also name an `aurastate` or `auratargetstate` (armours, shouts, curses,
  shapeshifts; the other four are 55, 189, 212, 348). `[L]` An `aura` row is a
  permanent aura, the others a timed state whose length is `auralencalc`.
- `[C]` The 13 rows whose `aurafilter` is `0x2` or `0x3` are the curses (66, 71, 72, 76, 77, 81, 82, 86, 87, 91,
  150 `Grim Ward`, 309, 310); each has an `auratargetstate`, no `aurastate`, and an `auralencalc`.
- `[C]` Of the `passive` rows, 224 `Shape Shifting` has neither `passivestate` nor `passivestat1`, 69 `Skeleton
  Mastery` and 79 `Golem Mastery` a state but no stat (`sk_passive_no_state_no_stat` = 1).

### The `passive` rows

| id | skill | class | `passivestate` | `passiveitype` | `passivestat` = `passivecalc` |
|---:|---|---|---|---|---|
| 9 | Critical Strike | ama | `criticalstrike` | — | `passive_critical_strike` = `dm12` |
| 13 | Dodge | ama | `dodge` | — | `passive_dodge` = `dm12` |
| 18 | Avoid | ama | `avoid` | — | `passive_avoid` = `dm12` |
| 23 | Penetrate | ama | `penetrate` | — | `item_tohit_percent` = `ln12` |
| 29 | Evade | ama | `evade` | — | `passive_evade` = `dm12` |
| 33 | Pierce | ama | `pierce` | — | `skill_pierce` = `dm12` |
| 37 | Warmth | sor | `warmth` | — | `manarecoverybonus` = `ln12` |
| 61 | Fire Mastery | sor | `firemastery` | — | `passive_fire_mastery` = `ln12` |
| 63 | Lightning Mastery | sor | `lightningmastery` | — | `passive_ltng_mastery` = `ln12` |
| 65 | Cold Mastery | sor | `coldmastery` | — | `passive_cold_pierce` = `ln12` |
| 69 | Skeleton Mastery | nec | `skel_mastery` | — | — |
| 79 | Golem Mastery | nec | `golem_mastery` | — | — |
| 89 | Summon Resist | nec | `summonresist` | — | `passive_summon_resist` = `dm12` |
| 127 | Sword Mastery | bar | `swordmastery` | `swor` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 128 | Axe Mastery | bar | `axemastery` | `axe` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 129 | Mace Mastery | bar | `macemastery` | `blun` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 134 | Pole Arm Mastery | bar | `polearmmastery` | `pole` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 135 | Throwing Mastery | bar | `throwingmastery` | `thro` | `passive_mastery_throw_th` = `ln12`; `passive_mastery_throw_dmg` = `ln34`; `passive_mastery_throw_crit` = `dm56` |
| 136 | Spear Mastery | bar | `spearmastery` | `spea` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 141 | Increased Stamina | bar | `increasedstamina` | — | `skill_passive_staminapercent` = `ln12` |
| 145 | Iron Skin | bar | `ironskin` | — | `skill_armor_percent` = `ln12` |
| 148 | Increased Speed | bar | `increasedspeed` | — | `velocitypercent` = `dm12` |
| 153 | Natural Resistance | bar | `naturalresistance` | — | `fireresist` = `dm12`; `lightresist` = `dm12`; `coldresist` = `dm12`; `poisonresist` = `dm12` |
| 224 | Shape Shifting | dru | — | — | — |
| 252 | Claw Mastery | ass | `clawmastery` | `h2h` | `passive_mastery_melee_th` = `ln12`; `passive_mastery_melee_dmg` = `ln34`; `passive_mastery_melee_crit` = `dm56` |
| 263 | Weapon Block | ass | `weaponblock` | `h2h` | `passive_weaponblock` = `dm12` |

### The `aura` rows

`auralencalc` is blank on all of them. The three masteries 127–129 (aura bit, no aura column) are in the table above.

| id | skill | class | `aurastate` / `auratargetstate` | `aurarangecalc` | `aurafilter` | `aurastat` = `aurastatcalc` |
|---:|---|---|---|---|---|---|
| 98 | Might | pal | `might` / `might` | `ln12` | `0x12003` | `damagepercent` = `ln34` |
| 99 | Prayer | pal | `prayer` / `prayer` | `ln12` | `0x12003` | `hitpoints` = `edns` |
| 100 | Resist Fire | pal | `resistfire` / `resistfire` | `ln12` | `0x12003` | `fireresist` = `dm34`; `maxfireresist` = `skill('Resist Fire'.blvl)` |
| 102 | Holy Fire | pal | `holyfire` / — | `ln12` | `0xA783` | — |
| 103 | Thorns | pal | `thorns` / `thorns` | `ln12` | `0x12003` | `thorns_percent` = `ln34` |
| 104 | Defiance | pal | `defiance` / `defiance` | `ln12` | `0x12003` | `skill_armor_percent` = `ln34` |
| 105 | Resist Cold | pal | `resistcold` / `resistcold` | `ln12` | `0x12003` | `coldresist` = `dm34`; `maxcoldresist` = `skill('Resist Cold'.blvl)` |
| 108 | Blessed Aim | pal | `blessedaim` / `blessedaim` | `ln12` | `0x12003` | `item_tohit_percent` = `ln34` |
| 109 | Cleansing | pal | `cleansing` / `cleansing` | `ln12` | `0x12003` | `item_poisonlengthresist` = `100-dm34`; `hitpoints` = `skill('Prayer'.edns)` |
| 110 | Resist Lightning | pal | `resistlight` / `resistlight` | `ln12` | `0x12003` | `lightresist` = `dm34`; `maxlightresist` = `skill('Resist Lightning'.blvl)` |
| 113 | Concentration | pal | `concentration` / `concentration` | `ln12` | `0x12003` | `damagepercent` = `ln34`; `skill_concentration` = `par5` |
| 114 | Holy Freeze | pal | `holywind` / `holywindcold` | `ln12` | `0x4A283` | `velocitypercent` = `-dm34`; `attackrate` = `-dm34`; `other_animrate` = `-dm34` |
| 115 | Vigor | pal | `stamina` / `stamina` | `ln12` | `0x12003` | `staminarecoverybonus` = `ln34`; `skill_staminapercent` = `ln34`; `velocitypercent` = `dm56` |
| 118 | Holy Shock | pal | `holyshock` / — | `ln12` | `0xA783` | — |
| 119 | Sanctuary | pal | `sanctuary` / — | `ln12` | `0xE786` | `item_undeaddamage_percent` = `ln34`; `item_undead_tohit` = `ln56`; `skill_bypass_undead` = `1` |
| 120 | Meditation | pal | `meditation` / `meditation` | `ln12` | `0x12001` | `manarecoverybonus` = `ln34`; `hitpoints` = `skill('Prayer'.edns)` |
| 122 | Fanaticism | pal | `fanaticism` / `fanaticism` | `ln12` | `0x12003` | `attackrate` = `dm34`; `item_tohit_percent` = `toht`; `damagepercent` = `ln56/2` |
| 123 | Conviction | pal | `conviction` / `conviction` | `ln12` | `0xA583` | `skill_armor_percent` = `-dm56`; `fireresist` = `"-min(ln34,150)"`; `coldresist` = `"-min(ln34,150)"`; `lightresist` = `"-min(ln34,150)"` |
| 124 | Redemption | pal | `redemption` / — | `ln12` | `0x1102` | — |
| 125 | Salvation | pal | `resistall` / `resistall` | `ln12` | `0x12003` | `fireresist` = `dm34`; `coldresist` = `dm34`; `lightresist` = `dm34` |
| 127 | Sword Mastery | bar | `—` / — | `—` | `0x0` | — |
| 128 | Axe Mastery | bar | `—` / — | `—` | `0x0` | — |
| 129 | Mace Mastery | bar | `—` / — | `—` | `0x0` | — |
| 296 | Barbs Aura | — | `barbscontrol` / `barbs` | `ln12` | `0x10103` | `thorns_percent` = `ln34` |
| 297 | Wolverine Aura | — | `wolverinecontrol` / `wolverine` | `ln12` | `0x10103` | `item_tohit_percent` = `ln34`; `damagepercent` = `ln56` |
| 298 | Oak Sage Aura | — | `oaksagecontrol` / `oaksage` | `ln12` | `0x10103` | `item_maxhp_percent` = `ln34` |

- `[C]` The 23 `aura` rows other than 127–129 all have an `aurastate`, an `aurarangecalc` and an `aurafilter`; 19 an
  `auratargetstate` (not 102 `Holy Fire`, 118 `Holy Shock`, 119 `Sanctuary`, 124 `Redemption`). `aurafilter`
  `0x12003` is on 13 of them. (tbl:Skills.txt:aurafilter)

Passive columns on the `aura` rows (`sk_passivestat1_aura` = 11, `sk_passivestate_aura` = 7, `sk_passiveitype_aura` = 3):
the three masteries of § The `passive` rows, and eight paladin auras, none with a `passiveitype`. `[C]` as data
(tbl:Skills.txt:passivestat1).

| id | skill | `passivestate` | `passivestat` = `passivecalc` |
|---:|---|---|---|
| 100 | Resist Fire | `passive_resistfire` | `maxfireresist` = `skill('Resist Fire'.blvl)/2` |
| 102 | Holy Fire | — | `firemindam` = `enms*par5/256`; `firemaxdam` = `exms*par5/256` |
| 105 | Resist Cold | `passive_resistcold` | `maxcoldresist` = `skill('Resist Cold'.blvl)/2` |
| 108 | Blessed Aim | `penetrate` | `item_tohit_percent` = `skill('Blessed Aim'.blvl) * par8` |
| 110 | Resist Lightning | `passive_resistltng` | `maxlightresist` = `skill('Resist Lightning'.blvl)/2` |
| 114 | Holy Freeze | — | `coldmindam` = `enms*par5/256`; `coldmaxdam` = `exms*par5/256` |
| 118 | Holy Shock | — | `lightmindam` = `1`; `lightmaxdam` = `exms*par5/256` |
| 122 | Fanaticism | — | `damagepercent` = `ln56` |

- `[C]` 108 `Blessed Aim`'s `passivestate` is `penetrate`, the state of the Amazon passive 23 `Penetrate`; the three
  resist auras' passive stat is the maximum resistance, also set by their `aurastat2`. `[L]` By the names the passive
  list is what the paladin carries himself whether or not the aura is selected. Phase 1.

### Other rows with these columns

123 rows without the `passive` or `aura` bit carry one of the columns (by id; `sk_rows_listed` = 172 in all):

| Kind (by the columns set) | Rows |
|---|---|
| timed state (an `aurastate` or `auratargetstate`, not a curse filter) | 61: 8, 17, 28, 40, 46, 50, 52, 57, 58, 60, 68, 90, 116, 117, 130, 137, 138, 144, 146, 147, 149, 151, 152, 155, 173, 187, 196, 209, 210, 215, 222, 223, 228, 231, 232, 233, 235, 238, 241, 249, 250, 254, 258, 259, 264, 265, 267, 268, 269, 274, 277, 278, 279, 280, 294, 295, 314, 328, 330, 349, 350 |
| curse (`auratargetstate`, `aurafilter` 2 or 3) | 13: 66, 71, 72, 76, 77, 81, 82, 86, 87, 91, 150, 309, 310 |
| stat list only (`passivestat` or `aurastat`, no state) | 15: 32, 62, 70, 75, 80, 85, 94, 95, 226, 227, 236, 237, 246, 247, 257 |
| `aurarangecalc` only (a radius) | 34: 26, 34, 35, 41, 42, 43, 53, 55, 56, 74, 83, 121, 132, 171, 177, 189, 212, 229, 230, 244, 245, 251, 256, 270, 273, 275, 285, 301, 305, 307, 312, 325, 348, 351 |

- `[L]` The kinds are a grouping by which cells are set, for orientation; which code reads each column, and for
  which kind, is Phase 1 (a skill's own effect is ADR-0014 phase 3).

## Charge cost columns (plan 0043 Phase 0)

`cost mult` (`+0x234` s32) and `cost add` (`+0x238` s32), [§ Columns](#columns) (`[C]`, `excel_bin.py diff`). Counts
from `python3 -I tools/economy_survey.py skills workspace/merged/data/global/excel` (gate survey `economy`), `[C]` as
data. `[I]` The price function reads them, with `reqlevel`, in three terms (plan 0043 Phase 1):

- **Stat terms** ([items/0011 § 3](../findings/items/0011-economy.md#3-the-value-terms) step 5): for an item stat whose ItemStatCost `Encode` is 1 (param = a skill: 97
  `item_nonclassskill`, 107 `item_singleskill`), 2 (skill on event: 195–199, 201) or 3 (charged: 204–213), the
  skill's `cost mult`/`cost add` replace the stat's own `Multiply`/`Add`: `X·cost mult·v/1024 + cost add` on the buy
  and repair values and `/4096` on the sell value; for Encode 2 and 3, `v` is the **skill level** from the param, and
  the charge count does not enter. (fn:sub_00628E70_PriceStatTerms@0x00628E70 0x00628F35, tbl:Skills.txt:cost mult)
- **Staff mods** (same section): for each stat 107 entry, `(cost mult·X/1024 + cost add)·(2v − 1)` (`/4096` for the
  sell value), unless the item type's `StaffMods` byte is 7. (fn:sub_0062EDD0_PriceStaffModTerm@0x0062EDD0)
- **Recharge** ([items/0011 § 4](../findings/items/0011-economy.md#4-mode-steps-the-npc-row-quantity-and-the-result)): a repair adds, for each charged skill with `c` of `x` charges,
  `(x − c)·(t + cost add)/x` with `K = level + 2·(reqlevel/6) + 2`, `t = cost mult·K·10000/1024`; this is added after
  the Npc multipliers. (fn:sub_00628D30_RechargeCost@0x00628D30, tbl:Skills.txt:reqlevel)

- `[C]` **The 210 class skills, and only they**, have a `cost mult` (the 147 rows with no `charclass` have it blank and
  `cost add` 0). No row has a `cost add` without a `cost mult`.
- `[C]` **`cost mult` is a function of `reqlevel`**: 256, 384, 512, 640, 768, 896 for `reqlevel` 1, 6, 12, 18, 24, 30
  (256 + 128·k for the k-th tier), on every one of the 210 rows.
- `[C]` **`cost add` mostly follows the same tiers**: 1000, 3000, 8000, 16000, 32000, 64000. 13 rows break it: 131
  *Find Potion* carries the value of the tier above (`reqlevel` 1, 3000), and 12 carry the value of the tier below: 231 *Cycle of Life*, 232 *Feral
  Rage*, 233 *Maul*, 261 *Charged Bolt Sentry*, 262 *Wake of Fire Sentry*, 263 *Weapon Block* (12, 3000), 236 *Heart
  of Wolverine*, 237 *Summon Fenris*, 266 *Blade Fury*, 267 *Fade* (18, 8000), 241 *Vines*, 271 *Lightning Sentry*
  (24, 16000). (`reqlevel`, `cost mult`, `cost add`): (1, 256, 1000) ×35, (1, 256, 3000) ×1, (6, 384, 3000) ×37,
  (12, 512, 3000) ×6, (12, 512, 8000) ×28, (18, 640, 8000) ×4, (18, 640, 16000) ×30, (24, 768, 16000) ×2,
  (24, 768, 32000) ×32, (30, 896, 64000) ×35.
- `[C]` **Every skill a `charged` property names has a cost**: 112 distinct skills are named by 268 `charged` cells
  (MagicSuffix 205, UniqueItems 38, Runes 24, SetItems 1; MagicPrefix none), all resolve, and all 112 have a
  `cost mult`. ItemStatCost 204 `item_charged_skill`, the stat a `charged` property writes, has its own
  `Multiply`/`Add` cells ([ItemStatCost § Price](ItemStatCost.md#price-plan-0043-phase-0)), but `[I]` its `Encode` 3
  makes the price take the skill's costs instead ([items/0011 § 3](../findings/items/0011-economy.md#3-the-value-terms)).

## Dispatch (plan 0045 Phase 0)

The columns the skill machinery reads, by their names: the function numbers, the missiles, the parameters, the
animation and timing columns, the costs, the start checks and the summon columns. Offsets are those of
§ [Columns](#columns) (`[C]`, `excel_bin.py diff`), repeated here with the observed values (from the `.txt`, by
script). The counts are `python3 -I tools/skills_survey.py skills workspace/merged/data/global/excel` (gate survey
`skills`, the `sk_*` keys), `[C]` as data. **Meaning** is the column name's plain reading, `[L]`, unless it carries its
own tag; which code reads each column, and how, is plan 0045 Phase 1.1 ([skills/0001](../plans/0045-skills-missiles-machinery.md#phase-1--read-the-machinery)).
The client columns are presentation and stay out of scope (plan 0045 *Open questions*, "Client-only skills").

### Function numbers and progressive columns

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `srvstfunc` | int 1..65 (64 distinct), 245 blank | `+0x02C` u16 | server start function number; `[I]` 1 is `SKILL_AttackStart` ([combat/0001](../findings/combat/0001-formulas.md); fn:SKILL_AttackStart@0x0056CA40); 42 (Fire Hit) is a start function that calls `MonAttackStats` with mode 8 ([combat/0001](../findings/combat/0001-formulas.md)) | — | [C] |
| `srvdofunc` | int 1..152 (138 distinct), 83 blank | `+0x02E` u16 | server do function number; `[I]` an index into the do-function table at `0x007322B0` (4-byte entries, `0x007322B0 + 4·n`): 1 is `SKILL_AttackDo` (`[C]`, [combat](../specs/combat/README.md); fn:SKILL_AttackDo@0x0056F070), 7 (Jab) `0x005DB2D0`, 67 (Charge) `0x005CF900` ([combat/0001](../findings/combat/0001-formulas.md)), 60 `SkillBoneWallDo`, 62 `SkillBonePrisonDo` ([items/0002](../findings/items/0002-quality-roll.md); fn:sub_005C58B0_SkillBoneWallDo@0x005C58B0, fn:sub_005C5D00_SkillBonePrisonDo@0x005C5D00), 98 `SkillMonTeleportDo` ([drlg/0009](../findings/drlg/0009-room-lifecycle.md); fn:sub_005CCC80_SkillMonTeleportDo@0x005CCC80); 58 (Revive), 91, 97, 135 and 140 create or revive monsters ([items/0001](../findings/items/0001-tc-resolution.md)) | — | [C] |
| `srvprgfunc1` | int {40, 143}, 355 blank | `+0x030` u16 | progressive function 1; `[I]` `COMBAT_PrgFinisher` runs `srvprgfunc1..3` through the do-function table `0x007322B0` on a charged state ([combat/0001](../findings/combat/0001-formulas.md); fn:COMBAT_PrgFinisher@0x005D5220) | — | [C] |
| `srvprgfunc2` | int {36, 38, 143}, 353 blank | `+0x032` u16 | progressive function 2 (as `srvprgfunc1`) | — | [C] |
| `srvprgfunc3` | int {37, 39, 41}, 353 blank | `+0x034` u16 | progressive function 3 (as `srvprgfunc1`) | — | [C] |
| `prgcalc1` | formula, 2 distinct, 355 blank | `+0x038` s32 calc | progressive formula 1 | `skillscode.bin` | [C] |
| `prgcalc2` | formula, 2 distinct, 354 blank | `+0x03C` s32 calc | progressive formula 2 | `skillscode.bin` | [C] |
| `prgcalc3` | formula, 3 distinct, 353 blank | `+0x040` s32 calc | progressive formula 3 | `skillscode.bin` | [C] |
| `prgdam` | int {1, 2, 4}, 352 blank | `+0x044` u16 | `[I]` which progressive damage hook runs when the packet's result has bit `0x1`: 1 `PrgDamEd`, 2 `PrgDamSteal`, 3 `PrgDamFreeze`, 4 `PrgDamRelease` ([combat/0001](../findings/combat/0001-formulas.md); fn:COMBAT_PrgHooksAfterBuild@0x005D3BA0, fn:sub_005D3680_PrgDamEd@0x005D3680) | — | [C] |
| `progressive` | int {1}, 351 blank | `+0x004` bit 2 | a progressive (charge-up) skill | — | [C] |
| `cltstfunc` | int 0..82 (52 distinct), 250 blank | `+0x0F2` u16 | client start function (presentation) | — | [C] |
| `cltdofunc` | int 0..95 (75 distinct), 224 blank | `+0x0F4` u16 | client do function (presentation) | — | [C] |
| `cltprgfunc1` | int 12..93 (7 distinct), 348 blank | `+0x0F6` u16 | client progressive function 1 (presentation) | — | [C] |
| `cltprgfunc2` | int 9..83 (5 distinct), 351 blank | `+0x0F8` u16 | client progressive function 2 (presentation) | — | [C] |
| `cltprgfunc3` | int 9..15 (5 distinct), 351 blank | `+0x0FA` u16 | client progressive function 3 (presentation) | — | [C] |

### Missiles

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `srvmissile` | str, 42 distinct, 309 blank | `+0x046` u16 index | missile the server function creates | `missiles:Missile` | [C] |
| `srvmissilea` | str, 93 distinct, 260 blank | `+0x048` u16 index | second server missile | `missiles:Missile` | [C] |
| `srvmissileb` | str, 26 distinct, 330 blank | `+0x04A` u16 index | third server missile | `missiles:Missile` | [C] |
| `srvmissilec` | str, 20 distinct, 337 blank | `+0x04C` u16 index | fourth server missile | `missiles:Missile` | [C] |
| `cltmissile` | str, 41 distinct, 306 blank | `+0x0E8` u16 index | client missile (presentation) | `missiles:Missile` | [C] |
| `cltmissilea` | str, 102 distinct, 238 blank | `+0x0EA` u16 index | client missile a (presentation) | `missiles:Missile` | [C] |
| `cltmissileb` | str, 36 distinct, 316 blank | `+0x0EC` u16 index | client missile b (presentation) | `missiles:Missile` | [C] |
| `cltmissilec` | str, 17 distinct, 326 blank | `+0x0EE` u16 index | client missile c (presentation) | `missiles:Missile` | [C] |
| `cltmissiled` | str {`vine beast neutral`}, 356 blank | `+0x0F0` u16 index | client missile d (presentation) | `missiles:Missile` | [C] |

### Parameters

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `Param1` | int -50..3600 (46 distinct), 97 blank | `+0x148` s32 | parameter 1 of the skill's functions; `[C]` the skill variables `par1` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param2` | int -2..1500 (35 distinct), 119 blank | `+0x14C` s32 | parameter 2 of the skill's functions; `[C]` the skill variables `par2` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param3` | int -50..4500 (44 distinct), 165 blank | `+0x150` s32 | parameter 3 of the skill's functions; `[C]` the skill variables `par3` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param4` | int -40..500 (35 distinct), 176 blank | `+0x154` s32 | parameter 4 of the skill's functions; `[C]` the skill variables `par4` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param5` | int -75..3000 (30 distinct), 239 blank | `+0x158` s32 | parameter 5 of the skill's functions; `[C]` the skill variables `par5` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param6` | int -1..300 (22 distinct), 257 blank | `+0x15C` s32 | parameter 6 of the skill's functions; `[C]` the skill variables `par6` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param7` | int -50..250 (19 distinct), 316 blank | `+0x160` s32 | parameter 7 of the skill's functions; `[C]` the skill variables `par7` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `Param8` | int 1..125 (23 distinct), 245 blank | `+0x164` s32 | parameter 8 of the skill's functions; `[C]` the skill variables `par8` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |

### Animation, range and delay

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `anim` | str, 10 distinct, 23 blank | `+0x010` u8 index | player mode the skill puts the caster in | `plrmode:Code` | [C] |
| `seqtrans` | str, 10 distinct, 23 blank | `+0x012` u8 index | player mode used for a sequence's transitions | `plrmode:Code` | [C] |
| `monanim` | str, 8 distinct, 0 blank | `+0x011` u8 index | monster mode the skill puts a monster in (`xx` = none) | `monmode:code` | [C] |
| `seqnum` | int 1..41 (23 distinct), 323 blank | `+0x013` u8 | animation sequence number | — | [C] |
| `seqinput` | int {8, 10, 12}, 353 blank | `+0x016` u16 | sequence input frame | — | [C] |
| `range` | str, 4 distinct, 0 blank | `+0x014` u8 keyword | attack range class (`none`, `h2h`, `rng`, `both`) | — | [C] |
| `delay` | formula, 9 distinct, 334 blank | `+0x190` s32 calc | cooldown formula (the delay before the skill can be used again) | `skillscode.bin` | [C] |

### Costs

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `startmana` | int {6}, 354 blank | `+0x184` u16 | mana needed to start | — | [C] |
| `minmana` | int {0, 1}, 141 blank | `+0x186` u16 | minimum mana cost | — | [C] |
| `manashift` | int 2..8 (6 distinct), 141 blank | `+0x188` u16 | fixed-point shift of the cost; `[C]` read as the byte at `+0x188`, masked to 5 bits, by the variables `mana`, `usmc`, `mps` ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |
| `mana` | int 0..76 (39 distinct), 141 blank | `+0x18A` s16 | base mana cost; `[C]` `usmc` = `(lvlmana × (lvl − 1) + mana) << (manashift & 31)`, `mana` = `usmc >> 8` ([data/calc § G](../specs/data/calc.md#g-variables); fn:SKILLS_CalcVar@0x00646460) | — | [C] |
| `lvlmana` | int -3..10 (8 distinct), 141 blank | `+0x18C` s16 | mana cost per level (the `usmc` term above) | — | [C] |
| `AttackNoMana` | int {1}, 316 blank | `+0x007` bit 4 | the skill falls back to a plain attack without mana | — | [C] |
| `usemanaondo` | int {1}, 355 blank | `+0x008` bit 5 | the mana is taken at the do function, not at the start | — | [C] |

### Start checks: town, item types, hands

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `InTown` | int {1}, 294 blank | `+0x005` bit 0 | usable in town | — | [C] |
| `itypea1` | str, 9 distinct, 303 blank | `+0x018` u16 index (code) | item type required, group A, 1; `[I]` the staff-mods roll tests it (§ [Class blocks](#class-blocks)) | `itemtypes:Code` | [C] |
| `itypea2` | str {`miss`}, 355 blank | `+0x01A` u16 index (code) | item type, group A, 2 | `itemtypes:Code` | [C] |
| `itypea3` | blank in all rows | `+0x01C` u16 index (code) | item type, group A, 3 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `itypeb1` | str {`h2h`, `mele`, `thro`}, 352 blank | `+0x01E` u16 index (code) | item type, group B, 1 | `itemtypes:Code` | [C] |
| `itypeb2` | blank in all rows | `+0x020` u16 index (code) | item type, group B, 2 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `itypeb3` | blank in all rows | `+0x022` u16 index (code) | item type, group B, 3 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypea1` | str {`tpot`}, 355 blank | `+0x024` u16 index (code) | excluded item type, group A, 1 | `itemtypes:Code` | [C] |
| `etypea2` | blank in all rows | `+0x026` u16 index (code) | excluded item type, group A, 2 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypeb1` | blank in all rows | `+0x028` u16 index (code) | excluded item type, group B, 1 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `etypeb2` | blank in all rows | `+0x02A` u16 index (code) | excluded item type, group B, 2 | `itemtypes:Code` | [C] value; slot by stride `[L]` |
| `weapsel` | int 1..4 (4 distinct), 342 blank | `+0x168` u16 | weapon selection (which hand or both) | — | [C] |
| `leftskill` | int {1}, 261 blank | `+0x007` bit 6 | can be the left-hand skill | — | [C] |
| `repeat` | int {1}, 354 blank | `+0x005` bit 3 | repeats while the button is held | — | [C] |
| `TgtPlaceCheck` | int {1}, 355 blank | `+0x008` bit 0 | the target position is checked before the start | — | [C] |

### Summon columns

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `summon` | str, 31 distinct, 325 blank | `+0x0BC` u16 index | monster class summoned | `monstats:Id` | [C] |
| `pettype` | str, 16 distinct, 326 blank | `+0x0BE` u8 index | [PetType](PetType.md) of the summon | `pettype:pet type` | [C] |
| `summode` | str {`NU`, `S1`, `S2`}, 325 blank | `+0x0BF` u8 index | mode the summon spawns in | `monmode:code` | [C] |
| `petmax` | formula, 7 distinct, 329 blank | `+0x0C0` s32 calc | pet count limit formula; `[C]` the skill variable `pets` (71) ([data/calc § G](../specs/data/calc.md#g-variables)) | `skillscode.bin` | [C] |
| `sumskill1` | str, 14 distinct, 341 blank | `+0x0C4` u16 index | skill 1 given to the summon | `skills:skill` | [C] |
| `sumsk1calc` | formula, 4 distinct, 341 blank | `+0x0D0` s32 calc | level formula of `sumskill1` | `skillscode.bin` | [C] |
| `sumskill2` | str, 7 distinct, 348 blank | `+0x0C6` u16 index | skill 2 given to the summon | `skills:skill` | [C] |
| `sumsk2calc` | formula, 5 distinct, 348 blank | `+0x0D4` s32 calc | level formula of `sumskill2` | `skillscode.bin` | [C] |
| `sumskill3` | str, 7 distinct, 350 blank | `+0x0C8` u16 index | skill 3 | `skills:skill` | [C] |
| `sumsk3calc` | formula, 7 distinct, 350 blank | `+0x0D8` s32 calc | level formula of `sumskill3` | `skillscode.bin` | [C] |
| `sumskill4` | str {`Critical Strike`, `Death Sentry`, `Lightning Sentry`}, 352 blank | `+0x0CA` u16 index | skill 4 | `skills:skill` | [C] |
| `sumsk4calc` | formula, 3 distinct, 352 blank | `+0x0DC` s32 calc | level formula of `sumskill4` | `skillscode.bin` | [C] |
| `sumskill5` | str {`Death Sentry`}, 356 blank | `+0x0CC` u16 index | skill 5 | `skills:skill` | [C] |
| `sumsk5calc` | formula, 1 distinct, 356 blank | `+0x0E0` s32 calc | level formula of `sumskill5` | `skillscode.bin` | [C] |

### What the survey shows

- `[C]` **Function numbers.** `srvstfunc` is set on 112 rows (64 numbers, 1..65), `srvdofunc` on 274 (138 numbers,
  1..152): 91 rows have both, 21 only a `srvstfunc`, 62 neither. 50 rows name a server missile and have no
  `srvdofunc` (6 Magic Arrow, 36 Fire Bolt, 47 Fire Ball, 251 Fire Trauma, the monster bolts and arrows …): which code
  creates their missile is Phase 1.1. `srvprgfunc1..3` are set on 4 rows (259 Fists of
  Fire, 269 Claws of Thunder, 274 Blades of Ice, 280 Royal Strike; 7 numbers: 36–41 and 143); all four have the
  `progressive` bit, which two more rows have (254 Tiger Strike, 265 Cobra Strike, with `prgdam` but no
  `srvprgfunc`). `prgdam` is set on 5 rows (1 on one, 2 on one, 4 on three); `prgcalc1` on 2 rows that are not
  progressive (256 Shock Field, 266 Blade Fury). (tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvprgfunc1,
  tbl:Skills.txt:prgdam)
- `[C]` **Client functions** (counted only): `cltstfunc` 107 rows, `cltdofunc` 133, `cltprgfunc1..3` 9/6/6.
  (tbl:Skills.txt:cltdofunc)
- `[C]` **Missiles.** `srvmissile` 48 rows, `srvmissilea` 97, `srvmissileb` 27, `srvmissilec` 20, all resolving;
  148 rows name at least one, 145 distinct missiles in all (every one with a Missiles `pSrvDoFunc`,
  [Missiles § Survey](Missiles.md#survey-plan-0045-phase-0)). Client: `cltmissile` 51, `cltmissilea..d`
  119/41/31/1. (tbl:Skills.txt:srvmissile)
- `[C]` **Parameters.** Rows set: `Param1..8` 260/238/192/181/118/100/41/112. (tbl:Skills.txt:Param1)
- `[C]` **Animation.** `anim` and `seqtrans` are set on 334 rows (10 modes each; `SC` 141 and `SQ` 116 for `anim`);
  `monanim` on all 357 (`xx` on 214); `seqnum` on 34 (1..41), one of them without `seqtrans`. `delay` is a formula on
  23 rows (15 Poison Javelin … 279 Shadow Master). `range`: `none` 271, `h2h` 43, `rng` 41, `both` 2.
  (tbl:Skills.txt:anim, tbl:Skills.txt:delay, tbl:Skills.txt:range)
- `[C]` **Costs.** `mana`, `lvlmana`, `manashift` and `minmana` are set on the same 216 rows; `mana` 0..76, never
  negative; `lvlmana` −3..10, negative on 7 (6 Magic Arrow, 22 Guided Arrow, 28 Dopplezon, 54 Teleport, 88 Bone
  Prison, 89 Summon Resist, 133 Double Swing); `manashift` 8 on 169 rows, 2..7 on the rest; `startmana` 6 on 3 rows.
  `AttackNoMana` 41 rows, `usemanaondo` 2 (25 Plague Javelin, 266 Blade Fury). (tbl:Skills.txt:mana,
  tbl:Skills.txt:lvlmana)
- `[C]` **Start checks.** `InTown` 63 rows; `leftskill` 96; `repeat` 3 (41 Inferno, 230 Arctic Blast, 266 Blade Fury);
  `TgtPlaceCheck` 2 (181 Resurrect, 327 Resurrect2). Item types: `itypea1` 54 rows (`mele` 17, `miss` 11, `spea` 8,
  `h2h` 6, `jave` 4, `thro` 3, `shld` 2, `weap` 2, `knif` 1), `itypea2` 2 (`miss`), `itypeb1` 5 (`h2h`, `mele`,
  `thro`), `etypea1` 2 (`tpot`); `itypea3`, `itypeb2/3`, `etypea2`, `etypeb1/2` blank. `weapsel` 15 rows (1..4).
  (tbl:Skills.txt:InTown, tbl:Skills.txt:itypea1, tbl:Skills.txt:weapsel)
- `[C]` **Summons.** `summon` 32 rows (all resolving), `summode` 32, `pettype` 31, `petmax` 28; `pettype` without
  `summon` on 95 Revive; `summon` without `pettype` on 295 Overseer Whip and 300 Impregnate; `summon` without `petmax`
  on those two and the three `none` rows (78 Bone Wall, 88 Bone Prison, 199 DiabPrison). Every `sumskill` has its
  `sumsk…calc` (16/9/7/5/1 rows). The rows and their kinds: [PetType § The rows](PetType.md#the-rows-and-the-skills-that-name-them).
  (tbl:Skills.txt:summon, tbl:Skills.txt:pettype)

### Rows per function number

`[C]` as data (`skills_survey.py skills`); a row is listed once per number. What each number does is plan 0045 Phase 1
(the machinery and tier A) and plan [0046](../plans/0046-skills-function-catalogue.md) (the catalogue).
(tbl:Skills.txt:srvdofunc)

#### `srvstfunc` (`+0x02C`): 112 rows, 64 numbers

| Number | Rows | Row ids and names |
|---:|---:|---|
| 1 | 2 | 0 Attack, 5 Left Hand Swing |
| 2 | 1 | 1 Kick |
| 3 | 1 | 3 Unsummon |
| 4 | 18 | 7 Fire Arrow, 11 Cold Arrow, 12 Multiple Shot, 15 Poison Javelin, 16 Exploding Arrow, 20 Lightning Bolt, 21 Ice Arrow, 22 Guided Arrow, 25 Plague Javelin, 27 Immolation Arrow, 31 Freezing Arrow, 35 Lightning Fury, 339 MonBow, 340 MonFireArrow, 341 MonColdArrow, 342 MonExplodingArrow, 343 MonFreezingArrow, 345 SuccubusBolt |
| 5 | 1 | 10 Jab |
| 6 | 4 | 14 Power Strike, 24 Charged Strike, 344 MonPowerStrike, 347 MonIceSpear |
| 7 | 1 | 19 Impale |
| 8 | 1 | 26 Strafe |
| 9 | 1 | 30 Fend |
| 10 | 1 | 34 Lightning Strike |
| 11 | 2 | 41 Inferno, 230 Arctic Blast |
| 12 | 2 | 43 Telekinesis, 275 Dragon Flight |
| 13 | 1 | 57 Thunder Storm |
| 14 | 1 | 62 Hydra |
| 15 | 2 | 70 Raise Skeleton, 80 Raise Skeletal Mage |
| 16 | 1 | 73 Poison Dagger |
| 17 | 3 | 74 Corpse Explosion, 83 Poison Explosion, 351 NihlathakCorpseExplosion |
| 18 | 1 | 86 Attract |
| 19 | 1 | 88 Bone Prison |
| 20 | 1 | 90 IronGolem |
| 21 | 1 | 95 Revive |
| 22 | 1 | 253 Psychic Hammer |
| 23 | 6 | 254 Tiger Strike, 259 Fists of Fire, 265 Cobra Strike, 269 Claws of Thunder, 274 Blades of Ice, 280 Royal Strike |
| 24 | 1 | 255 Dragon Talon |
| 25 | 1 | 260 Dragon Claw |
| 26 | 1 | 266 Blade Fury |
| 27 | 1 | 270 Dragon Tail |
| 28 | 1 | 277 Blade Shield |
| 29 | 1 | 96 Sacrifice |
| 31 | 2 | 107 Charge, 352 SerpentCharge |
| 32 | 5 | 116 Conversion, 126 Bash, 139 Stun, 144 Concentrate, 326 BearSmite |
| 33 | 2 | 131 Find Potion, 150 Grim Ward |
| 34 | 1 | 142 Find Item |
| 35 | 1 | 111 Vengeance |
| 36 | 1 | 117 Holy Shield |
| 37 | 3 | 106 Zeal, 248 Fury, 328 BloodLordFrenzy |
| 38 | 1 | 151 Whirlwind |
| 39 | 1 | 152 Berserk |
| 40 | 1 | 132 Leap |
| 41 | 1 | 143 Leap Attack |
| 42 | 1 | 156 Fire Hit |
| 43 | 1 | 159 MaggotEgg |
| 44 | 1 | 161 MagottUp |
| 45 | 1 | 162 MagottDown |
| 46 | 1 | 164 AndrialSpray |
| 47 | 1 | 165 Jump |
| 48 | 1 | 166 Swarm Move |
| 49 | 2 | 167 Nest, 320 EvilHutSpawner |
| 50 | 1 | 168 Quick Strike |
| 51 | 1 | 176 Submerge |
| 52 | 1 | 180 Emerge |
| 53 | 6 | 178 FetishInferno, 193 DiabLight, 311 mon inferno sentry, 317 Baal Inferno, 319 MegademonInferno, 323 Horror Arctic Blast |
| 54 | 1 | 198 DiabRun |
| 55 | 1 | 206 Mosquito |
| 56 | 2 | 232 Feral Rage, 233 Maul |
| 57 | 1 | 238 Rabies |
| 58 | 1 | 239 Fire Claws |
| 59 | 1 | 282 Imp Inferno |
| 60 | 1 | 289 Suck Blood |
| 61 | 1 | 293 Self-resurrect |
| 62 | 1 | 302 MinionSpawner |
| 63 | 2 | 307 CorpseCycler, 325 VineCycler |
| 64 | 1 | 215 MonFrenzy |
| 65 | 2 | 2 Throw, 4 Left Hand Throw |

#### `srvdofunc` (`+0x02E`): 274 rows, 138 numbers

| Number | Rows | Row ids and names |
|---:|---:|---|
| 1 | 2 | 0 Attack, 5 Left Hand Swing |
| 2 | 12 | 1 Kick, 14 Power Strike, 19 Impale, 111 Vengeance, 126 Bash, 139 Stun, 144 Concentrate, 152 Berserk, 239 Fire Claws, 326 BearSmite, 344 MonPowerStrike, 347 MonIceSpear |
| 3 | 1 | 2 Throw |
| 4 | 1 | 3 Unsummon |
| 5 | 1 | 4 Left Hand Throw |
| 6 | 2 | 8 Inner Sight, 17 Slow Missiles |
| 7 | 1 | 10 Jab |
| 8 | 4 | 12 Multiple Shot, 67 Teeth, 191 PrimePoisonball, 243 Shock Wave |
| 9 | 1 | 147 Frenzy |
| 10 | 3 | 22 Guided Arrow, 93 Bone Spirit, 211 MonBoneSpirit |
| 11 | 1 | 24 Charged Strike |
| 12 | 1 | 26 Strafe |
| 13 | 3 | 30 Fend, 106 Zeal, 248 Fury |
| 14 | 1 | 34 Lightning Strike |
| 15 | 1 | 28 Dopplezon |
| 16 | 1 | 32 Valkyrie |
| 17 | 4 | 38 Charged Bolt, 186 PrimeBolt, 306 BoltSentry, 322 ImpBolt |
| 18 | 11 | 40 Frozen Armor, 50 Shiver Armor, 60 Chilling Armor, 68 Bone Armor, 117 Holy Shield, 209 MonFrozenArmor, 210 MonBoneArmor, 235 Cyclone Armor, 258 Quickness, 267 Fade, 278 Venom |
| 19 | 2 | 41 Inferno, 230 Arctic Blast |
| 20 | 1 | 42 Static Field |
| 21 | 1 | 43 Telekinesis |
| 22 | 9 | 44 Frost Nova, 48 Nova, 92 Poison Nova, 130 Howl, 190 PrimeIceNova, 195 DiabFire, 316 Baal Nova, 346 MephFrostNova, 353 Trap Nova |
| 23 | 4 | 46 Blaze, 58 Energy Shield, 173 SpiderLay, 187 PrimeBlaze |
| 24 | 4 | 51 Fire Wall, 170 VampireFirewall, 188 PrimeFirewall, 321 CountessFirewall |
| 25 | 1 | 52 Enchant |
| 26 | 1 | 53 Chain Lightning |
| 27 | 1 | 54 Teleport |
| 28 | 12 | 56 Meteor, 59 Blizzard, 171 VampireMeteor, 205 MonBlizzard, 213 HellMeteor, 234 Eruption, 284 Baal Taunt, 287 Catapult Charged Ball, 288 Catapult Spike Ball, 303 CatapultBlizzard, 304 CatapultPlague, 305 CatapultMeteor |
| 29 | 1 | 57 Thunder Storm |
| 30 | 10 | 66 Amplify Damage, 71 Dim Vision, 72 Weaken, 76 Iron Maiden, 77 Terror, 82 Life Tap, 87 Decrepify, 91 Lower Resist, 309 Defense Curse, 310 Blood Mana |
| 31 | 2 | 70 Raise Skeleton, 80 Raise Skeletal Mage |
| 32 | 1 | 73 Poison Dagger |
| 33 | 1 | 253 Psychic Hammer |
| 34 | 3 | 254 Tiger Strike, 265 Cobra Strike, 280 Royal Strike |
| 35 | 3 | 259 Fists of Fire, 269 Claws of Thunder, 274 Blades of Ice |
| 42 | 1 | 255 Dragon Talon |
| 43 | 1 | 256 Shock Field |
| 44 | 1 | 257 Blade Sentinel |
| 45 | 5 | 261 Charged Bolt Sentry, 262 Wake of Fire Sentry, 271 Lightning Sentry, 272 Inferno Sentry, 276 Death Sentry |
| 46 | 1 | 260 Dragon Claw |
| 47 | 1 | 264 Cloak of Shadows |
| 48 | 1 | 266 Blade Fury |
| 49 | 2 | 268 Shadow Warrior, 279 Shadow Master |
| 50 | 1 | 270 Dragon Tail |
| 51 | 1 | 273 Mind Blast |
| 52 | 1 | 275 Dragon Flight |
| 54 | 1 | 277 Blade Shield |
| 55 | 3 | 74 Corpse Explosion, 312 mon death sentry, 351 NihlathakCorpseExplosion |
| 56 | 3 | 75 Clay Golem, 85 BloodGolem, 94 FireGolem |
| 57 | 1 | 90 IronGolem |
| 58 | 1 | 95 Revive |
| 59 | 1 | 86 Attract |
| 60 | 1 | 78 Bone Wall |
| 61 | 1 | 81 Confuse |
| 62 | 1 | 88 Bone Prison |
| 63 | 1 | 83 Poison Explosion |
| 64 | 1 | 96 Sacrifice |
| 65 | 17 | 98 Might, 99 Prayer, 100 Resist Fire, 103 Thorns, 104 Defiance, 105 Resist Cold, 108 Blessed Aim, 109 Cleansing, 110 Resist Lightning, 113 Concentration, 115 Vigor, 120 Meditation, 122 Fanaticism, 125 Salvation, 296 Barbs Aura, 297 Wolverine Aura, 298 Oak Sage Aura |
| 66 | 4 | 102 Holy Fire, 118 Holy Shock, 119 Sanctuary, 123 Conviction |
| 67 | 2 | 107 Charge, 352 SerpentCharge |
| 68 | 5 | 138 Shout, 146 Battle Cry, 149 Battle Orders, 154 War Cry, 155 Battle Command |
| 69 | 1 | 131 Find Potion |
| 70 | 1 | 133 Double Swing |
| 71 | 1 | 137 Taunt |
| 72 | 1 | 142 Find Item |
| 73 | 1 | 112 Blessed Hammer |
| 74 | 1 | 140 Double Throw |
| 75 | 1 | 150 Grim Ward |
| 76 | 1 | 151 Whirlwind |
| 77 | 1 | 132 Leap |
| 78 | 1 | 143 Leap Attack |
| 79 | 1 | 116 Conversion |
| 80 | 1 | 121 Fist of the Heavens |
| 81 | 1 | 114 Holy Freeze |
| 82 | 1 | 124 Redemption |
| 83 | 1 | 156 Fire Hit |
| 84 | 1 | 159 MaggotEgg |
| 85 | 2 | 157 UnHolyBolt, 160 ShamanFire |
| 86 | 1 | 162 MagottDown |
| 87 | 1 | 163 MagottLay |
| 88 | 1 | 164 AndrialSpray |
| 89 | 1 | 165 Jump |
| 90 | 1 | 166 Swarm Move |
| 91 | 2 | 167 Nest, 320 EvilHutSpawner |
| 92 | 1 | 168 Quick Strike |
| 93 | 1 | 172 GargoyleTrap |
| 94 | 1 | 176 Submerge |
| 95 | 5 | 178 FetishInferno, 311 mon inferno sentry, 317 Baal Inferno, 319 MegademonInferno, 323 Horror Arctic Blast |
| 96 | 2 | 179 ZakarumHeal, 182 Bestow |
| 97 | 2 | 181 Resurrect, 327 Resurrect2 |
| 98 | 4 | 184 MonTeleport, 292 Teleport 2, 329 Baal Teleport, 331 Baal Clone Teleport |
| 99 | 1 | 192 PrimePoisonNova |
| 100 | 1 | 194 DiabCold |
| 101 | 1 | 196 FingerMageSpider |
| 102 | 1 | 197 DiabWall |
| 103 | 1 | 198 DiabRun |
| 104 | 1 | 199 DiabPrison |
| 105 | 1 | 203 DesertTurret |
| 106 | 1 | 204 ArcaneTower |
| 107 | 1 | 206 Mosquito |
| 108 | 1 | 214 RegurgitatorEat |
| 109 | 2 | 215 MonFrenzy, 328 BloodLordFrenzy |
| 110 | 3 | 183 MissileSkill1, 202 HireableMissile, 336 RogueMissile |
| 111 | 1 | 177 FetishAura |
| 112 | 1 | 212 MonCurseCast |
| 113 | 4 | 217 Scroll of Identify, 218 Book of Identify, 219 Scroll of Townportal, 220 Book of Townportal |
| 114 | 1 | 221 Raven |
| 115 | 3 | 222 Plague Poppy, 231 Cycle of Life, 241 Vines |
| 116 | 3 | 223 Wearwolf, 228 Wearbear, 350 Delerium Change |
| 117 | 1 | 225 Firestorm |
| 118 | 2 | 240 Twister, 245 Tornado |
| 119 | 6 | 226 Oak Sage, 227 Summon Spirit Wolf, 236 Heart of Wolverine, 237 Summon Fenris, 246 Spirit of Barbs, 247 Summon Grizzly |
| 120 | 2 | 232 Feral Rage, 233 Maul |
| 121 | 1 | 238 Rabies |
| 122 | 1 | 242 Hunger |
| 123 | 1 | 244 Volcano |
| 124 | 3 | 249 Armageddon, 250 Hurricane, 349 Diablogeddon |
| 125 | 1 | 281 Wake Of Destruction Sentry |
| 126 | 1 | 282 Imp Inferno |
| 127 | 1 | 289 Suck Blood |
| 128 | 1 | 290 Cry Help |
| 129 | 1 | 330 Imp Teleport |
| 130 | 1 | 294 Vine Attack |
| 131 | 1 | 295 Overseer Whip |
| 132 | 1 | 299 Imp Fire Missile |
| 133 | 1 | 300 Impregnate |
| 134 | 1 | 301 Siege Beast Stomp |
| 135 | 1 | 302 MinionSpawner |
| 136 | 1 | 308 DeathMaul |
| 137 | 1 | 314 fenris rage |
| 139 | 1 | 318 Baal Cold Missiles |
| 140 | 1 | 315 Baal Tentacle |
| 141 | 1 | 285 Baal Corpse Explode |
| 144 | 1 | 62 Hydra |
| 148 | 1 | 335 DoomKnightMissile |
| 149 | 1 | 338 NecromageMissile |
| 150 | 1 | 97 Smite |
| 152 | 1 | 193 DiabLight |

#### `srvprgfunc1..3` (`+0x030..+0x034`): 4 rows, 7 numbers

| Number | Rows | Row ids and names |
|---:|---:|---|
| 36 | 1 | 269 Claws of Thunder |
| 37 | 1 | 269 Claws of Thunder |
| 38 | 2 | 259 Fists of Fire, 274 Blades of Ice |
| 39 | 2 | 259 Fists of Fire, 274 Blades of Ice |
| 40 | 1 | 280 Royal Strike |
| 41 | 1 | 280 Royal Strike |
| 143 | 2 | 259 Fists of Fire, 280 Royal Strike |

### Families and the tier-A candidates

`[C]` as data: `skills_survey.py families` and `skills_survey.py tiera` (`fam_*`, `ta_*` keys).

- `[C]` **Family sizes** (stock rows per number; a family of ten rows or more is one the plan's tier A must
  represent): `srvstfunc` 4 × 18 is the only one (47 of its 64 numbers have one row); `srvdofunc` 65 × 17, 2 × 12,
  28 × 12, 18 × 11, 30 × 10 (98 of 138 numbers have one row); no `srvprgfunc` number has more than 2 rows; Missiles
  `pSrvDoFunc` 1 × 551 and 3 × 26 (23 of 34 numbers have one row); no `pSrvHitFunc` or `pSrvDmgFunc` number has ten
  rows (largest 8 and 6). Eight families in all. (tbl:Skills.txt:srvdofunc, tbl:Missiles.txt:pSrvDoFunc)
- `[C]` **The candidates.** The 22 rows below are the plan's named skills (the general rows and per class; the Druid
  and Assassin pairs are this phase's proposal: 221 Raven and 225 Firestorm, 251 Fire Trauma, which is *Fire Blast*,
  and 259 Fists of Fire, a progressive melee skill with `srvprgfunc`); they cover four of the eight families
  (`srvstfunc` 4, `srvdofunc` 2 and 18, `pSrvDoFunc` 1). One row per uncovered family is added, a class row first:
  56 Meteor (`srvdofunc` 28), 66 Amplify Damage (30), 98 Might (65) and 25 Plague Javelin (its missile's
  `pSrvDoFunc` 3); then none is uncovered (`ta_big_uncovered=0`). The monster skills of the combat logs' attackers
  are not in the excel data: Phase 1.3 adds them from the kept logs. The plan's Phase 1 review fixes the list.
  (tbl:Skills.txt:srvdofunc, tbl:Skills.txt:skill)

| Group | Id | Skill | `srvstfunc` | `srvdofunc` | `srvprgfunc` | `anim` | `range` | Server missiles (`pSrvDoFunc` / `pSrvHitFunc`) |
|---|---:|---|---:|---:|---|---|---|---|
| general | 0 | Attack | 1 | 1 | - | A1 | both | — |
| general | 1 | Kick | 2 | 2 | - | KK | h2h | — |
| general | 2 | Throw | 65 | 3 | - | TH | rng | — |
| general | 4 | Left Hand Throw | 65 | 5 | - | S4 | rng | — |
| general | 5 | Left Hand Swing | 1 | 1 | - | S3 | both | — |
| sor | 48 | Nova | - | 22 | - | SC | none | `nova` 1 / - |
| sor | 44 | Frost Nova | - | 22 | - | SC | none | `frostnova` 1 / - |
| sor | 42 | Static Field | - | 20 | - | SC | none | — |
| sor | 54 | Teleport | - | 27 | - | SC | none | — |
| sor | 36 | Fire Bolt | - | - | - | SC | none | `firebolt` 1 / - |
| bar | 126 | Bash | 32 | 2 | - | A1 | h2h | — |
| bar | 130 | Howl | - | 22 | - | SC | none | `howl` 1 / 17 |
| ama | 10 | Jab | 5 | 7 | - | SQ | h2h | — |
| ama | 12 | Multiple Shot | 4 | 8 | - | A1 | rng | `multipleshotarrow` 1 / -, `multipleshotbolt` 1 / - |
| nec | 70 | Raise Skeleton | 15 | 31 | - | SC | none | — |
| nec | 68 | Bone Armor | - | 18 | - | SC | none | — |
| pal | 102 | Holy Fire | - | 66 | - | - | none | — |
| pal | 117 | Holy Shield | 36 | 18 | - | SC | none | — |
| dru | 221 | Raven | - | 114 | - | SC | none | — |
| dru | 225 | Firestorm | - | 117 | - | SC | none | `firestormmaker` 23 / - |
| ass | 251 | Fire Trauma | - | - | - | S2 | rng | `bomb in air` 1 / 36 |
| ass | 259 | Fists of Fire | 23 | 35 | 143/38/39 | SQ | h2h | `fistsoffirefirewall` 1 / - |
| added (family) | 56 | Meteor | - | 28 | - | SC | none | `meteorcenter` 1 / 14 |
| added (family) | 66 | Amplify Damage | - | 30 | - | SC | none | — |
| added (family) | 98 | Might | - | 65 | - | - | none | — |
| added (family) | 25 | Plague Javelin | 4 | - | - | TH | rng | `plaguejavelin` 3 / 2 |

## Open questions

- `[L]` How the per-class lists at `DataTables+0xBA4..+0xBAC` are built at load (their builder is not read). What
  `firstSkill(class)` returns is settled for classes 1–6 in [§ Class blocks](#class-blocks); class 0 was not logged.
- `[L]` Whether `Id` is a u16 or a u32 (`+0x002` is 0 in every record).
- `[L]` Every meaning not tagged in the tables. The dispatch columns' readers (the start checks, the do and progressive
  function tables, the costs and their rounding, the summon limit) are plan 0045 Phase 1.1 and 1.3; the per-number
  behaviour is plan 0046. Owner: reverser.
- `[L]` `manashift` is laid out as a u16 (`+0x188`, values 2..8) and read as a byte by the formula variables; whether
  any reader takes the high byte (`+0x189`, 0 in every record).
