# Skills (`data/global/excel/skills.txt` → `skills.bin`)

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 357 (no `Expansion` marker)   **Record:** 572 B (`0x23C`)
> **sha256:** `.txt` `465c28e83657540e0d7ae5b0de826d5657be7fba1aa539a85c3ca3aeea34b498`, `.bin` `0b57ba62b6b5c74be6a579adb9327641ecfe880ebc0c217d341c9d5bba89043b`, `skillscode.bin` `d42e1da6ebdf835c0c623f13c77201e3c2a25659dc58eff215af3cacc7ecf30f`
> **Doc status:** layout complete (every compiled column placed, `[C]` by diff); passive and aura rows listed (plan 0041 Phase 0); dispatch columns surveyed (plan 0045 Phase 0); semantics `[C]`/`[I]` for
> the columns the item code, the formula readers and the combat findings read, `[L]` elsewhere until the skills machinery is read ([plan 0045](../plans/done/0045-skills-missiles-machinery.md) Phase 1)

## Purpose

One row per skill: the 210 character-class skills, plus monster, item and internal skills (`Attack`, `Kick`,
`Scroll of Identify`, `Wake Of Destruction Sentry`, …). A row holds the skill's server and client functions, missiles,
aura and passive stats, summon, item-type requirements, level and mana costs, damage and formulas. In this project
the reader so far is `items/affixes`: the staff-mods roll picks class skills by id and tests their item-type
requirement ([items/0005 § 9](../findings/items/0005-affixes.md#9-staff-mods-items_rollstaffmodsitem-ecx-rec-edx-0x005c1260),
plan 0021). The skills machinery (`skills/dispatch`, `skills/missiles`) is [plan 0045](../plans/done/0045-skills-missiles-machinery.md)
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
| `prgstack` | int {1}, 354 blank | `+0x004` bit 7 | progressive-charge values; `[I]` the finisher runs every `srvprgfunc` up to the charge count, not only the last ([skills/0001 § 12](../findings/skills/0001-dispatch.md#12-progressive-charges), [skills/0003 § 1](../findings/skills/0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail)) | — | [C] (the other probe candidates lie inside fields other columns pin) |
| `srvprgfunc1` | int {40, 143}, 355 blank | `+0x030` u16 | server start / do / progressive function number | — | [C] |
| `srvprgfunc2` | int {36, 38, 143}, 353 blank | `+0x032` u16 | server start / do / progressive function number | — | [C] |
| `srvprgfunc3` | int {37, 39, 41}, 353 blank | `+0x034` u16 | server start / do / progressive function number | — | [C] |
| `prgcalc1` | formula, 2 distinct, 355 blank | `+0x038` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgcalc2` | formula, 2 distinct, 354 blank | `+0x03C` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgcalc3` | formula, 3 distinct, 353 blank | `+0x040` s32 calc | progressive-charge values | `skillscode.bin` | [C] |
| `prgdam` | int {1, 2, 4}, 352 blank | `+0x044` u16 | progressive-charge values | — | [C] |
| `srvmissile` | str, 42 distinct, 309 blank | `+0x046` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `decquant` | int {1}, 345 blank | `+0x004` bit 0 | consumes item quantity (throws); `[I]` `SKILLS_SrvDo` calls `PLAYER_UseAmmo` when it pays ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo)) | — | [C] |
| `lob` | int {1}, 354 blank | `+0x004` bit 1 | lobbed missile; `[I]` `SKILLS_SrvDo` creates `srvmissile` with the lob creator ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo), [skills/0002 § 2](../findings/skills/0002-missiles.md#2-creation)); *plan 0046 readers:* `[C]` do 110 (on its `srvmissilea` path) and do 148, 149 create their missile with `sub_0056EE90_SkillMissileCreateLob` when the bit is set, else `SkillMissileCreate` (ADR-0021, up to the creation); no stock row of those batches sets it (the bit is on rows 251, 283, 286) ([skills/0016 § 3](../findings/skills/0016-monster-8a.md#3-the-hits-start-42-47-50-do-83-92-110), [skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63); fn:sub_005CE1B0_SkillDo110MissileSkill@0x005CE1B0, fn:sub_005CDFB0_SkillDo148DoomKnightMissile@0x005CDFB0, fn:sub_005CE0B0_SkillDo149NecromageMissile@0x005CE0B0) | — | [C] |
| `srvmissilea` | str, 93 distinct, 260 blank | `+0x048` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvmissileb` | str, 26 distinct, 330 blank | `+0x04A` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvmissilec` | str, 20 distinct, 337 blank | `+0x04C` u16 index | missiles the server side launches | `missiles:Missile` | [C] |
| `srvoverlay` | str, 7 distinct, 349 blank | `+0x04E` u16 index | overlay (graphic effect); *plan 0046 readers:* `[C]` do 2's overlay block runs for `0 < value ≤ DataTables+0xBC0` (`movzx; test ax, ax; jle`, then `movsx` and `jg`) and, when the found hit's result has bit 0, puts it on the target with `UnitSetOverlayStat` (ADR-0021), `[I]` that the count is the Overlay table's row count ([skills/0012 § 3](../findings/skills/0012-barbarian.md#3-the-melee-functions-start-32-39-do-2-9-70); fn:SKILL_MeleeDeliverDo@0x0056F1F0); `[I]` do 128 puts it on the target when in `(0, overlay count)`, after its boundary ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_005D1800_SkillDo128CryHelp@0x005D1800) | `overlay:overlay` | [C] |
| `aurafilter` | int 2..303747 (18 distinct), 308 blank | `+0x050` u32 | aura target filter bits; *plan 0046 readers:* `[C]` do 6 (Inner Sight, Slow Missiles) passes it to `SKILLS_ForUnitsInRange` (ADR-0021, up to that call) ([skills/0009 § 5](../findings/skills/0009-amazon.md#5-do-6-inner-sight-and-slow-missiles); fn:sub_005DB1C0_SkillDo06AuraInRange@0x005DB1C0); `[C]` do 30 passes it in EDX to `SkillForUnitsNearTarget` (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_005C37C0_SkillDo30Curse@0x005C37C0); `[C]` hit 20 passes it (0 → `0xA783`) to `SKILLS_ForUnitsInRange` (ADR-0021) ([skills/0006 § 13](../findings/skills/0006-missile-hit-1-29.md#13-hit-20-lightning-fury); fn:sub_005AB370_MissHit20UnitsInRange@0x005AB370); `[C]` hit 21 passes `0xA783` when it is non-zero, else 0, to `SkillUnitFilter` (only set or not set; ADR-0021) ([skills/0006 § 12](../findings/skills/0006-missile-hit-1-29.md#12-hit-21-battle-cry-and-hit-18-shouts); fn:sub_005AB500_MissHit21BattleCry@0x005AB500); `[I]` hit 22's filter (0 → `0xA683`), after its boundary ([skills/0006 § 14](../findings/skills/0006-missile-hit-1-29.md#14-hit-22-fist-of-the-heavens-delay); fn:sub_005ADD20_MissHit22Chain@0x005ADD20); `[I]` do 27's area-hit filter, after its boundary ([skills/0005 § 12](../findings/skills/0005-missile-do-19-36-damage.md#12-do-27-tornado); fn:sub_005AFA30_MissDo27PeriodicAreaHit@0x005AFA30) | — | [C] |
| `aurastate` | str, 65 distinct, 283 blank | `+0x080` u16 index | state put on the caster / the aura's targets; *plan 0046 readers:* `[C]` do 65 puts it in the self block when (s16) > 0 and below the States count and calls `AURA_ApplyToTarget` on the caster; do 66, 81, 82 need it in `[0, States count)` (0 admitted), else 0 (ADR-0021, up to `AURA_ApplyToTarget`) ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_005CF3A0_AuraHitDo@0x005CF3A0); `[I]` what `AURA_ApplyToTarget` does with it (fn:AURA_ApplyToTarget@0x005CEDC0); `[C]` do 23, 25, 29 test it in range and pass it in their `STATE_ApplyTimed` block (ADR-0021) ([skills/0008 § 8](../findings/skills/0008-sorceress.md#8-timed-states-do-18-23-25); fn:sub_005C9C10_SkillDo23TimedState@0x005C9C10, fn:sub_005CA4D0_SkillDo29ThunderStorm@0x005CA4D0); `[I]` hit 18's state, put by `UnitApplyAuraState` after its boundary ([skills/0006 § 12](../findings/skills/0006-missile-hit-1-29.md#12-hit-21-battle-cry-and-hit-18-shouts); fn:sub_005D8290_UnitApplyAuraState@0x005D8290); `[C]` do 2 admits it in `(0, States count)` (`jle`: 0 refused) for its caster list and `STATE_Set` (ADR-0021) ([skills/0012 § 3](../findings/skills/0012-barbarian.md#3-the-melee-functions-start-32-39-do-2-9-70); fn:SKILL_MeleeDeliverDo@0x0056F1F0); `[C]` do 116, 120, 124, start 57 and entries 145, 146 admit it in `[0, States count)` (`test ax, ax; jl`: 0 admitted); start 57 then refuses a caster not in it (ADR-0021) ([skills/0013 § 4](../findings/skills/0013-druid.md#4-the-shape-and-timed-state-functions-do-116-120-124), [skills/0013 § 5](../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146), [skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122); fn:sub_005C6EC0_SkillDo116Shapeshift@0x005C6EC0, fn:sub_005C79E0_SkillSt57Rabies@0x005C79E0); `[I]` `sub_0056D790_StateDoFunc` takes the `aurastate` of the skill that queued unit event 5 and runs that state's States `srvactivefunc` ([skills/0013 § 1](../findings/skills/0013-druid.md#1-the-table-slots-the-shared-shape-and-entries-145-and-146); fn:sub_0056D790_StateDoFunc@0x0056D790); `[C]` do 129 (Imp Teleport) and do 137 (fenris rage) return 0 unless it is in `[0, States count)`; do 129 tests it as a gate only, `[I]` its attach and detach helpers set and clear state 143 by the constant `0x8F`; `[I]` do 137 passes it to `0x00570590` after its boundary ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147); fn:sub_005D1AB0_SkillDo129ImpTeleport@0x005D1AB0, fn:sub_005D26F0_SkillDo137FenrisRage@0x005D26F0) | `states:state` | [C] |
| `auratargetstate` | str, 44 distinct, 310 blank | `+0x082` u16 index | state put on the caster / the aura's targets; *plan 0046 readers:* `[C]` hits 16, 17, 19, 21 test it (s16) in `[0, States count)` (hit 21: up to the count itself), else 1; hits 16 and 19 search the unit's lists for it, hit 17 refuses a unit already in it (ADR-0021, up to `STATLIST_Alloc`/`SKILLS_ApplyAuraStats`, `MonFleeFrom`, `SkillUnitFilter`); `[I]` the state put after those boundaries ([skills/0006 § 10](../findings/skills/0006-missile-hit-1-29.md#10-hit-16-and-hit-19-a-timed-state-on-the-unit), [§ 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee), [§ 12](../findings/skills/0006-missile-hit-1-29.md#12-hit-21-battle-cry-and-hit-18-shouts); fn:sub_005AAE10_MissHit16TargetState@0x005AAE10, fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0, fn:sub_005AB110_MissHit19TargetState@0x005AB110); `[C]` do 6: in `[0, States count)` else 0, a word of the block passed to `SKILLS_ForUnitsInRange` (ADR-0021) ([skills/0009 § 5](../findings/skills/0009-amazon.md#5-do-6-inner-sight-and-slow-missiles); fn:sub_005DB1C0_SkillDo06AuraInRange@0x005DB1C0); `[C]` do 30 and 61: the same range test, block `+0x4C`; states 23 and 56 make do 30 divide its length by DifficultyLevels `AiCurseDivisor` (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_005C3400_CurseStateDiffFlag@0x005C3400, fn:sub_005C3F20_SkillDo61Confuse@0x005C3F20); `[C]` do 65's target pass when `aurastate` fails: (s16) ≥ 0 and below the count, then `SKILLS_ForUnitsInRange` (ADR-0021) ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_005CF010_PalAuraDo@0x005CF010); `[C]` do 2 admits it in `[0, States count)` (0 admitted) and looks its list up on the target (ADR-0021) ([skills/0012 § 3](../findings/skills/0012-barbarian.md#3-the-melee-functions-start-32-39-do-2-9-70)); `[C]` do 112 (MonCurseCast) reads it from the curse row it draws (66, 72, 82, 87 or 91), not from its own row 212: below 0 or at the count → 0, else block `+0x4C` (ADR-0021, up to `SkillForUnitsNearTarget`) ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112); fn:sub_005CE2B0_SkillDo112MonCurse@0x005CE2B0); `[C]` do 131 (Overseer Whip, row 295) returns 0 outside `[0, States count)` and puts it, with `auralencalc` as the length, into its `STATE_ApplyTimed` block (ADR-0021) ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70, fn:sub_005D1D70_WhipApplyState@0x005D1D70) | `states:state` | [C] |
| `auralencalc` | formula, 24 distinct, 296 blank | `+0x060` s32 calc | aura duration / radius formula; *plan 0046 readers:* `[C]` do 6's block word (ADR-0021) ([skills/0009 § 5](../findings/skills/0009-amazon.md#5-do-6-inner-sight-and-slow-missiles); fn:sub_005DB1C0_SkillDo06AuraInRange@0x005DB1C0); `[C]` do 30 and 61's length, divided by `AiCurseDivisor` (do 30 for states 23 and 56, do 61 always), block `+0x18` (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_005C37A0_DiffDivide@0x005C37A0); `[C]` the length word of do 23, 25 and 29's `STATE_ApplyTimed` block (ADR-0021) ([skills/0008 § 5](../findings/skills/0008-sorceress.md#5-thunder-storm-start-13-and-do-29), [§ 8](../findings/skills/0008-sorceress.md#8-timed-states-do-18-23-25); fn:sub_005CA030_SkillDo25Enchant@0x005CA030); `[C]` do 2: `frame + max(value, 1)`, the third argument of `STATLIST_Alloc` and the second of `UnitQueueEvent` (ADR-0021), `[I]` a length in frames ([skills/0012 § 3](../findings/skills/0012-barbarian.md#3-the-melee-functions-start-32-39-do-2-9-70)); `[C]` do 120 adds it to the frame **not** raised to 1, do 124 raised to 1, as `STATLIST_Alloc`'s third argument (ADR-0021), `[I]` a length in frames ([skills/0013 § 4](../findings/skills/0013-druid.md#4-the-shape-and-timed-state-functions-do-116-120-124); fn:sub_005C77C0_SkillDo120FeralMaul@0x005C77C0, fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190); `[C]` do 112's block `+0x18`, evaluated for the drawn curse row ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112)); `[C]` do 131's `STATE_ApplyTimed` length ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137)) | `skillscode.bin` | [C] |
| `aurarangecalc` | formula, 15 distinct, 279 blank | `+0x064` s32 calc | aura duration / radius formula; *plan 0046 readers:* `[C]` do 28's scatter `r` when `Param2` ≤ 0 (`max(aurarangecalc, 1)`; ADR-0021, up to `MissileCreate`) ([skills/0005 § 7](../findings/skills/0005-missile-do-19-36-damage.md#7-do-28-volcano-debris); fn:sub_005AFB80_MissDo28Reseed@0x005AFB80); `[I]` do 27's area radius when `Param2` ≤ 0, after its boundary ([skills/0005 § 12](../findings/skills/0005-missile-do-19-36-damage.md#12-do-27-tornado); fn:sub_005AFA30_MissDo27PeriodicAreaHit@0x005AFA30); `[C]` start 8, do 6 and do 12 pass its value to `NearestUnitInRange`/`SKILLS_ForUnitsInRange` (ADR-0021), `[I]` as their search radius ([skills/0009 § 3](../findings/skills/0009-amazon.md#3-start-4-5-8-and-9-ammunition-a-target-and-the-strafe-and-fend-counts), [§ 5](../findings/skills/0009-amazon.md#5-do-6-inner-sight-and-slow-missiles), [§ 7](../findings/skills/0009-amazon.md#7-do-12-and-do-13-strafe-fend-zeal-and-fury); fn:sub_005DACD0_SkillSt08Strafe@0x005DACD0, fn:sub_005DBA40_SkillDo12Strafe@0x005DBA40); `[C]` do 30 and 61 pass it on the stack to `SkillForUnitsNearTarget` (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_0056E780_SkillForUnitsNearTarget@0x0056E780); `[C]` start 12 refuses a target with `DistSq > r·r` (signed) ([skills/0008 § 4](../findings/skills/0008-sorceress.md#4-start-12-and-do-21-telekinesis-and-dragon-flight); fn:sub_005C9030_SkillSt12TargetInRange@0x005C9030); `[C]` do 20 passes it to `SKILLS_ForUnitsInRange` (ADR-0021), `[I]` as the radius ([skills/0008 § 7](../findings/skills/0008-sorceress.md#7-creations-do-17-22-24-26-28-and-do-20); fn:sub_005C9800_SorSkillStaticMin@0x005C9800); `[C]` start 40 (Leap) pulls a target point farther than `range` = its value in to `((x − ux) · range / d + ux, (y − uy) · range / d + uy)` (`imul`, `cdq; idiv`, `d` raised to 1) (ADR-0021, up to `FreeNearFallback`), `[I]` the leap's range ([skills/0012 § 6](../findings/skills/0012-barbarian.md#6-whirlwind-the-leaps-and-double-throw-start-38-40-41-do-74-76-77-78); fn:sub_005D9A10_LeapPoint@0x005D9A10); `[C]` entries 145 and 146 take the shared exit at `UNIT_CancelEvents(game, caster; 5, id)` when it is ≤ 0, `[I]` that the period then ends, and its use as the area radius and the point range after the boundary ([skills/0013 § 5](../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146); fn:sub_005C8380_SkillDo145Hurricane@0x005C8380, fn:sub_005C8520_SkillDo146Armageddon@0x005C8520); `[C]` the fallback of entries 37, 38, 39, 143 and do 51, 54 when `PrgCalcByCharge` gives 0 (§ `prgcalc1`) ([skills/0014 § 5](../findings/skills/0014-assassin.md#5-the-progressive-entries-3641-and-143), [skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54)); `[C]` do 112's radius for `SkillForUnitsNearTarget`, evaluated for the drawn curse row ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112)); `[I]` do 134's area radius, after its boundary ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_005D2320_SkillDo134SiegeStomp@0x005D2320) | `skillscode.bin` | [C] |
| `aurastat1` | str, 35 distinct, 278 blank | `+0x054` u16 index | aura stat 1 and its value formula; *plan 0046 readers:* `[C]` do 6 refuses it (s16) outside `[0, ItemStatCost count)` (a blank −1 refuses), else a block word with `aurastatcalc1` (ADR-0021) ([skills/0009 § 5](../findings/skills/0009-amazon.md#5-do-6-inner-sight-and-slow-missiles); fn:sub_005DB1C0_SkillDo06AuraInRange@0x005DB1C0); `[C]` do 30 and 61 admit −1 (blank) to below the ItemStatCost count (`cmp ax, 0xFFFF; jl`); do 30's block holds `aurastat1..6` at `+0x1C` (the first out-of-range one −1, the rest 0) and their `aurastatcalc1..6` values at `+0x34`; do 61 starts at `aurastat2` (word 0 stays 0) (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_005C37C0_SkillDo30Curse@0x005C37C0); `[C]` do 65's self block: `aurastat1..6` with their `aurastatcalc1..6` values, stopping at the first below 0, none for a player below the mana cost (ADR-0021) ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_005CF010_PalAuraDo@0x005CF010); `[C]` do 23 and 25 admit −1 to below the ItemStatCost count (ADR-0021) ([skills/0008 § 8](../findings/skills/0008-sorceress.md#8-timed-states-do-18-23-25); fn:sub_005C9C10_SkillDo23TimedState@0x005C9C10) | `itemstatcost:Stat` | [C] |
| `aurastatcalc1` | formula, 35 distinct, 284 blank | `+0x068` s32 calc | aura stat 1 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] |
| `aurastat2` | str, 27 distinct, 306 blank | `+0x056` u16 index | aura stat 2 and its value formula; *plan 0046 readers:* as `aurastat1` | `itemstatcost:Stat` | [C] |
| `aurastatcalc2` | formula, 32 distinct, 305 blank | `+0x06C` s32 calc | aura stat 2 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] |
| `aurastat3` | str, 18 distinct, 329 blank | `+0x058` u16 index | aura stat 3 and its value formula; *plan 0046 readers:* as `aurastat1` | `itemstatcost:Stat` | [C] |
| `aurastatcalc3` | formula, 21 distinct, 329 blank | `+0x070` s32 calc | aura stat 3 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] |
| `aurastat4` | str, 7 distinct, 344 blank | `+0x05A` u16 index | aura stat 4 and its value formula; *plan 0046 readers:* as `aurastat1` | `itemstatcost:Stat` | [C] |
| `aurastatcalc4` | formula, 11 distinct, 344 blank | `+0x074` s32 calc | aura stat 4 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] |
| `aurastat5` | str {`coldresist`, `curse_resistance`}, 355 blank | `+0x05C` u16 index | aura stat 5 and its value formula; *plan 0046 readers:* as `aurastat1` | `itemstatcost:Stat` | [C] |
| `aurastatcalc5` | formula, 2 distinct, 355 blank | `+0x078` s32 calc | aura stat 5 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `aurastat6` | str {`damageresist`, `poisonresist`}, 355 blank | `+0x05E` u16 index | aura stat 6 and its value formula; *plan 0046 readers:* as `aurastat1` | `itemstatcost:Stat` | [C] |
| `aurastatcalc6` | formula, 2 distinct, 355 blank | `+0x07C` s32 calc | aura stat 6 and its value formula; *plan 0046 readers:* as `aurastat1` | `skillscode.bin` | [C] value; slot by stride `[L]` |
| `auraevent1` | str, 5 distinct, 347 blank | `+0x084` u16 index | aura event 1 and its handler number; `[I]` registered on the unit as a `g_StatEventFuncs` (`0x007325B0`) record carrying (skill, level) ([skills/0003 § 3](../findings/skills/0003-handlers.md#3-the-stat-event-handlers)); *plan 0046 readers:* `[C]` do 30's block holds `auraevent1..3` and `auraeventfunc1..3` at `+0x50..+0x64` (each `movsx`); do 61 has no event words (ADR-0021) ([skills/0010 § 4](../findings/skills/0010-necromancer.md#4-start-16-do-32-and-the-curses-do-30-do-61); fn:sub_005C37C0_SkillDo30Curse@0x005C37C0) | `events:event` | [C] |
| `auraeventfunc1` | int 1..27 (10 distinct), 347 blank | `+0x08A` u16 | aura event 1's handler: `[I]` the `g_StatEventFuncs` number ([skills/0003 § 3](../findings/skills/0003-handlers.md#3-the-stat-event-handlers)); *plan 0046 readers:* as `auraevent1` | — | [C] |
| `auraevent2` | str {`damagedbymissile`, `damagedinmelee`}, 355 blank | `+0x086` u16 index | aura event 2 (as `auraevent1`, `[I]`); *plan 0046 readers:* as `auraevent1` | `events:event` | [C] |
| `auraeventfunc2` | int {5, 26}, 355 blank | `+0x08C` u16 | aura event 2's handler (as `auraeventfunc1`, `[I]`); *plan 0046 readers:* as `auraevent1` | — | [C] |
| `auraevent3` | str {`damagedbymissile`}, 356 blank | `+0x088` u16 index | aura event 3 (as `auraevent1`, `[I]`); *plan 0046 readers:* as `auraevent1` | `events:event` | [C] |
| `auraeventfunc3` | int {26}, 356 blank | `+0x08E` u16 | aura event 3's handler (as `auraeventfunc1`, `[I]`); *plan 0046 readers:* as `auraevent1` | — | [C] |
| `auratgtevent` | blank in all rows | `+0x090` u16 index | aura target event and handler number | `events:event` | [C] value; slot by stride `[L]` |
| `auratgteventfunc` | blank in all rows | `+0x092` u16 | aura target event and handler number | — | [C] value; slot by stride `[L]` |
| `passivestate` | str, 28 distinct, 328 blank | `+0x094` u16 index | state of a passive skill; *plan 0046 readers:* `[C]` do 65 puts it at the self block's `+0x48` when (s16) > 0 (ADR-0021, up to `AURA_ApplyToTarget`); `[I]` `AURA_ApplyToTarget` removes that state, so the caster loses its passive list while the aura runs ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_005CF010_PalAuraDo@0x005CF010, fn:AURA_ApplyToTarget@0x005CEDC0) | `states:state` | [C] |
| `passiveitype` | str, 7 distinct, 349 blank | `+0x096` u16 index | `[I]` the param of the passive stats: `SKILLS_RefreshPassive` writes `passivestat1..5` = `passivecalc` with this item type as their param ([stats/0002 § 4](../findings/stats/0002-states.md#4-auras-and-passives), fn:SKILLS_RefreshPassive@0x00646D60); "the item type a passive needs" `[L]` by the name | `itemtypes:Code` | [C] |
| `passivestat1` | str, 30 distinct, 306 blank | `+0x098` u16 index | passive stat 1 and its value formula; *plan 0046 readers:* `[C]` do 66, 81, 82's self block: `passivestat1..5` (`movsx`) at `+0x10 + 4i` and, under the mana gate, their `passivecalc1..5` values at `+0x28 + 4i`; do 82 leaves the value 0 for a stat below 0 and goes on (ADR-0021, up to `AURA_ApplyToTarget`) ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_005CF3A0_AuraHitDo@0x005CF3A0, fn:sub_005D0E90_SkillDo82Redemption@0x005D0E90); `[I]` after do 65's self call they go onto the returned list; `[C]` do 47 (Cloak of Shadows): `passivestat1` (`movsx`) and the value of `passivecalc1` are its timed block's `+0x14` and `+0x18` (ADR-0021, up to `STATE_ApplyTimed`) ([skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54); fn:sub_005D6630_SkillDo47Cloak@0x005D6630) | `itemstatcost:Stat` | [C] |
| `passivecalc1` | formula, 22 distinct, 306 blank | `+0x0A4` s32 calc | passive stat 1 and its value formula; *plan 0046 readers:* as `passivestat1` | `skillscode.bin` | [C] |
| `passivestat2` | str, 11 distinct, 331 blank | `+0x09A` u16 index | passive stat 2 and its value formula; *plan 0046 readers:* as `passivestat1` | `itemstatcost:Stat` | [C] |
| `passivecalc2` | formula, 13 distinct, 331 blank | `+0x0A8` s32 calc | passive stat 2 and its value formula; *plan 0046 readers:* as `passivestat1` | `skillscode.bin` | [C] |
| `passivestat3` | str, 7 distinct, 340 blank | `+0x09C` u16 index | passive stat 3 and its value formula; *plan 0046 readers:* as `passivestat1` | `itemstatcost:Stat` | [C] |
| `passivecalc3` | formula, 10 distinct, 340 blank | `+0x0AC` s32 calc | passive stat 3 and its value formula; *plan 0046 readers:* as `passivestat1` | `skillscode.bin` | [C] |
| `passivestat4` | str {`armorclass`, `damagepercent`, `poisonresist`}, 351 blank | `+0x09E` u16 index | passive stat 4 and its value formula; *plan 0046 readers:* as `passivestat1` | `itemstatcost:Stat` | [C] |
| `passivecalc4` | formula, 5 distinct, 351 blank | `+0x0B0` s32 calc | passive stat 4 and its value formula; *plan 0046 readers:* as `passivestat1` | `skillscode.bin` | [C] |
| `passivestat5` | blank in all rows | `+0x0A0` u16 index | passive stat 5 and its value formula; *plan 0046 readers:* as `passivestat1` | `itemstatcost:Stat` | [C] value; slot by stride `[L]` |
| `passivecalc5` | blank in all rows | `+0x0B4` s32 calc | passive stat 5 and its value formula; *plan 0046 readers:* as `passivestat1` | `skillscode.bin` | [C] value; slot by stride `[L]` |
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
| `sumumod` | int {32, 33, 42}, 351 blank | `+0x0E4` u16 | unique mod given to the summon; *plan 0046 readers:* `[I]` do 131's class change applies it when in `(0, 43)`, after its boundary ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_005D1E10_WhipChangeClass@0x005D1E10) | — | [C] |
| `sumoverlay` | str {`dopllezon_appear`, `spawnedminion`}, 355 blank | `+0x0E6` u16 index | overlay (graphic effect); *plan 0046 readers:* `[I]` do 135 puts it on its spawn, after its boundary ([skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147); fn:sub_005D2490_SkillDo135MinionSpawn@0x005D2490) | `overlay:overlay` | [C] |
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
| `immediate` | int {1}, 347 blank | `+0x005` bit 7 | `[I]` an aura select or an item aura with it runs the do function at once ([skills/0001 § 9](../findings/skills/0001-dispatch.md#9-periodic-aura-and-channelled-skills-repeat), [skills/0001 § 10](../findings/skills/0001-dispatch.md#10-item-granted-skills)) | — | [C] |
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
| `LineOfSight` | int {4}, 309 blank | `+0x18F` u8 | `[I]` 1..5 select one of five collision masks for a line test from the target point to the unit at the start; another non-zero value refuses ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart)) | — | [C] |
| `TargetableOnly` | int {1}, 312 blank | `+0x006` bit 4 | `[I]` the start needs a hostile target (or one two other tests accept) ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart)) | — | [C] |
| `SearchEnemyXY` | int {1}, 308 blank | `+0x006` bit 5 | behaviour flag (name reading) | — | [C] |
| `SearchEnemyNear` | int {1}, 337 blank | `+0x006` bit 6 | behaviour flag (name reading) | — | [C] |
| `SearchOpenXY` | int {1}, 347 blank | `+0x006` bit 7 | behaviour flag (name reading) | — | [C] |
| `SelectProc` | int 1..6 (6 distinct), 348 blank | `+0x015` u8 | target selection procedure number | — | [C] |
| `TargetCorpse` | int {1}, 339 blank | `+0x007` bit 0 | `[I]` a dead target is kept only with it, else the target is cleared ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart)) | — | [C] |
| `TargetPet` | int {1}, 354 blank | `+0x007` bit 1 | pet-target flag (name reading); *plan 0046 readers:* `[C]` read by `SkillPetTest`: an owner and a unit, the owner a player or the unit a monster, this bit, and the unit's owner reference giving owner type 0 and the owner's guid; hit 7 (holy bolt) heals a unit that passes (ADR-0021, up to `UnitSetStat`) ([skills/0006 § 6](../findings/skills/0006-missile-hit-1-29.md#6-hit-7-holy-bolt-and-hit-8-blaze); fn:sub_005542C0_SkillPetTest@0x005542C0, fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0) | — | [C] |
| `TargetAlly` | int {1}, 355 blank | `+0x007` bit 2 | `[I]` read by the start's ally test, which refuses only without it; that refusal never fires from `SKILLS_StartUsedSkill` ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart), [skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | — | [C] |
| `TargetItem` | int {1}, 354 blank | `+0x007` bit 3 | `[I]` the request at a unit accepts any target type with it, else only a player, monster or missile ([skills/0001 § 1](../findings/skills/0001-dispatch.md#1-the-request-client-packets-0x050x11)) | — | [C] |
| `AttackNoMana` | int {1}, 316 blank | `+0x007` bit 4 | behaviour flag (name reading) | — | [C] |
| `TgtPlaceCheck` | int {1}, 355 blank | `+0x008` bit 0 | behaviour flag (name reading) | — | [C] |
| `ItemEffect` | int {1, 36, 151}, 285 blank | `+0x16A` u16 | `[I]` an item cast (`ITEMSKILL_Cast`) refuses a row with 0; with the cast's effect flag, a value above 1 replaces `srvdofunc` as the `g_SkillDoFuncs` index (36 on Frost Nova and Nova, 151 on Chain Lightning) ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo), [skills/0001 § 10](../findings/skills/0001-dispatch.md#10-item-granted-skills); § [Function index](#function-index-plan-0046-phase-0)); *plan 0046 readers:* `[C]` `ITEMSKILL_Cast` refuses id 0 and `ItemEffect` 0 with no write (ADR-0021, up to `SKILLS_SrvStart` or `SKILLS_SrvDo`) ([skills/0015 § 5](../findings/skills/0015-item.md#5-itemskill_cast-its-itemtarget-helpers-and-its-callers); fn:ITEMSKILL_Cast@0x005FDA80); `[I]` the effect flag that lets it replace `srvdofunc` is 1 only from stat-event handler 20 without `ItemTgtDo` (the item-use entries, handlers 21 and 30, charges and `SKILLS_SrvDo`'s seven other calls pass 0), so an item Nova, Frost Nova (36) or Chain Lightning (151) runs it only on attack, kill or hit ([skills/0015 § 6](../findings/skills/0015-item.md#6-the-stat-event-handlers-20-21-30); fn:sub_005C0470_StatEv20SkillOnEvent@0x005C0470); `[I]` entry 36 (`0x005D4DB0`, rows 44 and 48) is a nova of the row's `srvmissilea` centred on the cast's target unit ([skills/0014 § 1](../findings/skills/0014-assassin.md#1-the-table-slots-the-shared-shape-the-stock-rows-and-the-callers), [skills/0014 § 5](../findings/skills/0014-assassin.md#5-the-progressive-entries-3641-and-143); fn:sub_005D4DB0_SkillPrgDo36NovaAtTarget@0x005D4DB0) | — | [C] |
| `ItemCltEffect` | int {10, 96}, 354 blank | `+0x16C` u16 | behaviour when cast from an item (charges, procs) | — | [C] |
| `ItemTgtDo` | int {1}, 356 blank | `+0x007` bit 5 | behaviour when cast from an item (charges, procs); *plan 0046 readers:* `[C]` stat-event handler 20 reads it: with it the event's other unit is the cast's caster and target, effect 0, and with no other unit it returns 1 with no cast; handlers 21 and 30 do not test it (ADR-0021, up to `ItemCastAtUnit`) ([skills/0015 § 6](../findings/skills/0015-item.md#6-the-stat-event-handlers-20-21-30); fn:sub_005C0470_StatEv20SkillOnEvent@0x005C0470) | — | [C] |
| `ItemTarget` | int {1, 2, 3, 4}, 351 blank | `+0x120` u16 | `[I]` the item cast's aim: 1 the caster, 2–4 three target helpers that may refuse ([skills/0001 § 10](../findings/skills/0001-dispatch.md#10-item-granted-skills)); *plan 0046 readers:* `[C]` `ITEMSKILL_Cast` switches on its **low byte** only: 1 aims at the caster, 2–4 call the helpers `0x005FD850`, `0x005FD9C0`, `0x005FDA10` (a refusal restores the aim and returns 0), any other value keeps the aim (ADR-0021) ([skills/0015 § 5](../findings/skills/0015-item.md#5-itemskill_cast-its-itemtarget-helpers-and-its-callers); fn:ITEMSKILL_Cast@0x005FDA80) | — | [C] |
| `ItemCheckStart` | int {1}, 355 blank | `+0x008` bit 1 | `[I]` with it the item cast runs `SKILLS_SrvStart` (no cost) first and stops when it fails ([skills/0001 § 10](../findings/skills/0001-dispatch.md#10-item-granted-skills)); *plan 0046 readers:* `[C]` with it `ITEMSKILL_Cast` runs `SKILLS_SrvStart(…, 1)` before `SKILLS_SrvDo`, a failed start ending the cast (ADR-0021) ([skills/0015 § 5](../findings/skills/0015-item.md#5-itemskill_cast-its-itemtarget-helpers-and-its-callers); fn:ITEMSKILL_Cast@0x005FDA80) | — | [C] |
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
| `restrict` | int {1, 2}, 331 blank | `+0x228` u8 | shapeshift restriction; `[I]` 0 refuses while the restricted-state test holds, 1 passes, 2 passes only while it holds and the unit has one of `State1..3` ([skills/0001 § 2](../findings/skills/0001-dispatch.md#2-skills_canuse-16-call-sites-4-of-them-in-the-request-handlers)) | — | [C] |
| `State1` | str {`bear`, `wolf`}, 350 blank | `+0x22A` u16 index | `[I]` the states `restrict` 2 requires, the first invalid one ending the list ([skills/0001 § 2](../findings/skills/0001-dispatch.md#2-skills_canuse-16-call-sites-4-of-them-in-the-request-handlers)) | `states:state` | [C] |
| `State2` | str {`bear`}, 355 blank | `+0x22C` u16 index | as `State1` (`[I]`) | `states:state` | [C] |
| `State3` | blank in all rows | `+0x22E` u16 index | as `State1` (`[I]`) | `states:state` | [C] value; slot by stride `[L]` |
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
| `periodic` | int {1}, 355 blank | `+0x004` bit 6 | `[I]` the start cancels all the unit's event-8 entries, and `SKILLS_QueuePeriodic` queues the row on the `perdelay` grid ([skills/0001 § 9](../findings/skills/0001-dispatch.md#9-periodic-aura-and-channelled-skills-repeat)) | — | [C] |
| `perdelay` | formula, 3 distinct, 335 blank | `+0x128` s32 calc | `[I]` the aura period in frames: `SKILLS_NextPeriodicFrame = ((frame − 1 + p) / p)·p + 1` with `p` = this calc, 5 when it gives less than 6; the item-aura and selected-aura events requeue at it ([stats/0002 § 4](../findings/stats/0002-states.md#4-auras-and-passives), fn:SKILLS_NextPeriodicFrame@0x0056CD50); *plan 0046 readers:* `[C]` the period `p` of do 65, 66, 81 and 82's end word `n + 1 − frame`, `n = ((frame + p − 1) / p)·p + 1` (truncating), `p` raised to 5 when it is 5 or less ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:SKILLS_NextPeriodicFrame@0x0056CD50) | `skillscode.bin` | [C] |
| `finishing` | int {1}, 352 blank | `+0x004` bit 3 | behaviour flag (name reading) | — | [C] |
| `passive` | int {1}, 331 blank | `+0x004` bit 4 | behaviour flag (name reading) | — | [C] |
| `progressive` | int {1}, 351 blank | `+0x004` bit 2 | progressive (charge-up) flag; its readers: § [Function numbers and progressive columns](#function-numbers-and-progressive-columns) | — | [C] (the other probe candidates lie inside fields other columns pin) |
| `general` | int {1}, 351 blank | `+0x008` bit 3 | behaviour flag (name reading) | — | [C] |
| `scroll` | str {`␠`, `1`}, 352 blank | `+0x008` bit 4 | `[I]` a `scroll` row needs the skill entry's quantity (`SkillEntry+0x30`) above 0 ([skills/0001 § 2](../findings/skills/0001-dispatch.md#2-skills_canuse-16-call-sites-4-of-them-in-the-request-handlers)) | — | [C] |
| `calc1` | formula, 65 distinct, 237 blank | `+0x138` s32 calc | general formula 1 (referenced by other formulas); `[I]` the skill hit's `edPct` where a start or do function builds one (`srvstfunc` 32's form, [skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* `[C]` do 10 (Missiles): the scatter radius `r` (ADR-0021, up to `COLL_CellTestAt`) ([skills/0004 § 7](../findings/skills/0004-missile-do-1-18.md#7-do-8-10-17-and-sub_005a9820_misssubnearreseed); fn:sub_005AEA60_MissDo10ScatterBySkill@0x005AEA60); `[C]` hit 7's heal low bound `calc1 << 8` (ADR-0021) ([skills/0006 § 6](../findings/skills/0006-missile-hit-1-29.md#6-hit-7-holy-bolt-and-hit-8-blaze); fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0); `[C]` do 8 (Multiple Shot): the fan size `n`, which sets the start point `x − sx·n/2` and the first group (ADR-0021, up to the inventory call or the first `MissileCreate`), `[I]` that `n` missiles are created in all; do 10 (skill): `[C]` the block's `+0x58` and, when non-zero, its callback, `[I]` the callback adds it to the missile's stat 25 ([skills/0009 § 6](../findings/skills/0009-amazon.md#6-creations-do-8-10-11-14); fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, fn:sub_005DB6D0_SkillDo10GuidedMissile@0x005DB6D0); `[C]` do 17's bolt count `n` (≤ 0: no creation), `[I]` the `n` creations; `[C]` do 22's velocity `MissileSpeedAtLevel + calc1`; do 26's count word; Inferno's block `+0x4C = max(calc1, 1)` (ADR-0021) ([skills/0008 § 3](../findings/skills/0008-sorceress.md#3-inferno-and-arctic-blast-start-11-do-19-0x005c8e30-0x005c8ca0), [§ 7](../findings/skills/0008-sorceress.md#7-creations-do-17-22-24-26-28-and-do-20); fn:sub_005C9300_SkillDo17ChargedBolt@0x005C9300, fn:sub_005C9B50_SkillDo22NovaAtSelf@0x005C9B50, fn:sub_005CA1B0_SkillDo26ChainLightning@0x005CA1B0, fn:sub_005C8CA0_InfernoCreate@0x005C8CA0); `[C]` do 151 (item Chain Lightning) evaluates it before `SkillMissileCreate`, `[I]` and writes it into the missile by `MISSDATA_SetSeedLow` after ([skills/0015 § 4](../findings/skills/0015-item.md#4-do-113-and-do-151); fn:sub_005CA260_SkillDo151ItemChainLightning@0x005CA260); `[C]` start 58's packet `+0x0C` ([skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122); fn:sub_005C7E00_SkillSt58FireClaws@0x005C7E00); `[C]` do 103's run speed at the `Param3` frame, `MulDiv(max(calc1 << 8, 0x100), stat 67, 100)` for `PathSetSpeed` (`calc1 << 8` 32-bit) ([skills/0017 § 4](../findings/skills/0017-monster-8b.md#4-the-hits-and-the-queued-hits-do-100-103-107-108-109-127-start-60); fn:sub_005CD380_SkillDo103DiabRun@0x005CD380) | `skillscode.bin` | [C] |
| `calc2` | formula, 31 distinct, 297 blank | `+0x13C` s32 calc | general formula 2 (referenced by other formulas); `[I]` in `srvstfunc` 32, flat physical damage added to the queued hit after the reductions, `<< 8` ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* `[C]` do 10 (Missiles): the scatter period (ADR-0021) ([skills/0004 § 7](../findings/skills/0004-missile-do-1-18.md#7-do-8-10-17-and-sub_005a9820_misssubnearreseed); fn:sub_005AEA60_MissDo10ScatterBySkill@0x005AEA60); `[C]` hit 7's heal high bound `calc2 << 8` (ADR-0021) ([skills/0006 § 6](../findings/skills/0006-missile-hit-1-29.md#6-hit-7-holy-bolt-and-hit-8-blaze); fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0); `[C]` do 8's block `+0x44` for the first creation, `[I]` its meaning to the missile ([skills/0009 § 6](../findings/skills/0009-amazon.md#6-creations-do-8-10-11-14); fn:sub_005DB410_SkillDo08MultiShot@0x005DB410); `[C]` a monster's Inferno: the used skill's `+0x18 = frame + max(calc2, 1)` (ADR-0021) ([skills/0008 § 3](../findings/skills/0008-sorceress.md#3-inferno-and-arctic-blast-start-11-do-19-0x005c8e30-0x005c8ca0); fn:sub_005C8E30_InfernoStart@0x005C8E30) | `skillscode.bin` | [C] |
| `calc3` | formula, 12 distinct, 336 blank | `+0x140` s32 calc | general formula 3 (referenced by other formulas); `[I]` in `srvstfunc` 32, the attack rate (stat 68 on a new list) ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* `[C]` do 8: the centre group's size (`n` when 0), which sets the first creation's flags (`0x10820` outer, `0x820` centre) (ADR-0021), `[I]` the later groups ([skills/0009 § 6](../findings/skills/0009-amazon.md#6-creations-do-8-10-11-14); fn:sub_005DB410_SkillDo08MultiShot@0x005DB410); `[C]` start 32 passes its value in `EDX` to `sub_0056E520_SkillAttackRateList` (ADR-0021, up to that call), `[I]` which makes it stat 68 ([skills/0012 § 3](../findings/skills/0012-barbarian.md#3-the-melee-functions-start-32-39-do-2-9-70); fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0) | `skillscode.bin` | [C] |
| `calc4` | formula, 11 distinct, 339 blank | `+0x144` s32 calc | general formula 4 (referenced by other formulas); `[I]` the conversion percent stored with `EType` when it is above 0 ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* `[C]` do 28's and do 27's period when `Param1` ≤ 0 (`max(calc4, 1)`; ADR-0021, up to `MissileCreate` and `MISSILE_BuildDamage`) ([skills/0005 § 7](../findings/skills/0005-missile-do-19-36-damage.md#7-do-28-volcano-debris), [§ 12](../findings/skills/0005-missile-do-19-36-damage.md#12-do-27-tornado); fn:sub_005AFB80_MissDo28Reseed@0x005AFB80, fn:sub_005AFA30_MissDo27PeriodicAreaHit@0x005AFA30) | `skillscode.bin` | [C] |
| `Param1` | int -50..3600 (46 distinct), 97 blank | `+0x148` s32 | general parameter 1 | — | [C] |
| `Param2` | int -2..1500 (35 distinct), 119 blank | `+0x14C` s32 | general parameter 2 | — | [C] |
| `Param3` | int -50..4500 (44 distinct), 165 blank | `+0x150` s32 | general parameter 3 | — | [C] |
| `Param4` | int -40..500 (35 distinct), 176 blank | `+0x154` s32 | general parameter 4 | — | [C] |
| `Param5` | int -75..3000 (30 distinct), 239 blank | `+0x158` s32 | general parameter 5 | — | [C] |
| `Param6` | int -1..300 (22 distinct), 257 blank | `+0x15C` s32 | general parameter 6 | — | [C] |
| `Param7` | int -50..250 (19 distinct), 316 blank | `+0x160` s32 | general parameter 7 | — | [C] |
| `Param8` | int 1..125 (23 distinct), 245 blank | `+0x164` s32 | general parameter 8 | — | [C] |
| `InGame` | int {1}, 0 blank | `+0x005` bit 2 | `[I]` `SKILLS_CanUse` refuses a row without it (code 3); set on every stock row ([skills/0001 § 2](../findings/skills/0001-dispatch.md#2-skills_canuse-16-call-sites-4-of-them-in-the-request-handlers)) | — | [C] value; slot `[I]` (1 in every row; `SKILLS_CanUse` tests `+0x005` bit 2, skills/0001 § 2) |
| `ToHit` | int 10..300 (11 distinct), 299 blank | `+0x198` s32 | attack rating bonus (base, per level, formula); *plan 0046 readers:* `[C]` `SKILLS_GetToHit` (emulated in start 7 and do 7): 0 for `lvl ≤ 0`, `(lvl − 1)·LevToHit + ToHit` (32-bit) when `ToHitCalc` is blank (−1), else the calc; start 7 and do 7 pass it to `COMBAT_MeleeHitTest`, start 6 and start 10 pass 0 (ADR-0021, up to `COMBAT_MeleeHitTest`); `[I]` its use as the attack-rating percent there ([skills/0009 § 4](../findings/skills/0009-amazon.md#4-the-melee-hits-start-6-7-10-and-do-7); fn:SKILLS_GetToHit@0x006449F0) | — | [C] |
| `LevToHit` | int 5..35 (9 distinct), 298 blank | `+0x19C` s32 | attack rating bonus (base, per level, formula); *plan 0046 readers:* as `ToHit` | — | [C] |
| `ToHitCalc` | formula, 3 distinct, 354 blank | `+0x1A0` s32 calc | attack rating bonus (base, per level, formula); *plan 0046 readers:* as `ToHit` | `skillscode.bin` | [C] |
| `ResultFlags` | int 1..16385 (7 distinct), 342 blank | `+0x12E` u16 | hit result; `[I]` ORed into the skill hit's packet result ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* `[C]` do 100 (DiabCold) puts `ResultFlags` ORed with 1 at its packet's `+0x04`, `HitFlags` at `+0x00` and a non-zero `HitClass` at `+0x60` before `SKILLS_RollElemDamage` (ADR-0021) ([skills/0017 § 4](../findings/skills/0017-monster-8b.md#4-the-hits-and-the-queued-hits-do-100-103-107-108-109-127-start-60); fn:sub_005CCE80_SkillDo100DiabCold@0x005CCE80); `[C]` `sub_0056E680_SkillHitOrResultFlags` (start 58, start 60, do 122): with bit 0 set no hit test is made and `+0x04` = `ResultFlags`; the caller then sets `+0x00` = `HitFlags` ORed with 2 and `+0x60` = `HitClass` when non-zero (do 122 also ORs `ResultFlags` into `+0x04`); with bit 0 clear, `MeleeHitTest` (ADR-0021) ([skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122), [skills/0017 § 4](../findings/skills/0017-monster-8b.md#4-the-hits-and-the-queued-hits-do-100-103-107-108-109-127-start-60); fn:sub_0056E680_SkillHitOrResultFlags@0x0056E680, fn:sub_005D1570_SkillSt60SuckBlood@0x005D1570); `[C]` (data) of the 357 rows only 239 has `srvstfunc` 58 and only 242 `srvdofunc` 122, both with `ResultFlags` blank (0; recounted by script, the finding writes 358) ([skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122), tbl:Skills.txt:ResultFlags); `[C]` do 134 (Siege Beast Stomp) puts `HitFlags` ORed with 1 at `+0x00`, `ResultFlags` at `+0x04` and a non-zero `HitClass` at `+0x60` before `SkillRollPhys` (ADR-0021) ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137); fn:sub_005D2320_SkillDo134SiegeStomp@0x005D2320) | — | [C] |
| `HitFlags` | int {2}, 354 blank | `+0x130` u32 | hit flags; `[I]` ORed into the skill hit's packet flags ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* as `ResultFlags` | — | [C] |
| `HitClass` | int 3..157 (6 distinct), 351 blank | `+0x134` u32 | hit class; `[I]` the skill hit's hit class when non-zero ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* as `ResultFlags` | — | [C] |
| `Kick` | int {1}, 353 blank | `+0x005` bit 1 | `[C]` `SKILLS_GetPhysMin` gives `max(str + dex − 20, 1) / 4 << 8` for a player owner and `max(3 · level, 1) / 4 << 8` for another owner, instead of the damage columns (emulated inside hit 43) ([skills/0007 § 3](../findings/skills/0007-missile-hit-31-59.md#3-hit-31-43-and-55-heals-and-drains); fn:SKILLS_GetPhysMin@0x00647BC0); `[I]` `SKILLS_GetPhysMax` calls `sub_00644C20_SkillKickDamage` with flag 0, which divides by 3, so the maximum is `… / 3 << 8` ([skills/0007 § 3](../findings/skills/0007-missile-hit-31-59.md#3-hit-31-43-and-55-heals-and-drains); fn:SKILLS_GetPhysMax@0x00647D00, fn:sub_00644C20_SkillKickDamage@0x00644C20); earlier reading [skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet) | — | [C] |
| `HitShift` | int 1..8 (8 distinct), 7 blank | `+0x1A4` u8 | damage shift (fractional damage); *plan 0046 readers:* as `MinDam` | — | [C] |
| `SrcDam` | int {32, 48, 96, 128}, 294 blank | `+0x1A5` u8 | share of weapon damage; `[I]` out of 128, 0 read as 128 by most hit builders (`srvstfunc` 6 passes it as stored) ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet)); *plan 0046 readers:* as `MinDam`; `[C]` start 58 and do 122 pass it (`movzx`) as `COMBAT_BuildDamage`'s fourth argument after `0x0056E680` (§ `ResultFlags`) ([skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122)) | — | [C] |
| `MinDam` | int 1..30 (13 distinct), 328 blank | `+0x1A8` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* `[C]` `SKILLS_GetPhysMin/Max` (emulated inside hit 43) with `Kick` clear and `SrcDam` 0: `MinDam` plus the level bands of `MinLevDam1..5` (levels 2–8, 9–16, 17–22, 23–28, 29+; 0 at `lvl ≤ 1`), plus `MulDiv(v, DmgSymPerCalc, 100)` when that calc is set and non-zero, then `<< HitShift`; the `Max` columns the same; with `SrcDam ≠ 0` `GetPhysMin` first calls `sub_00623990_SkillSrcDamWeapon` (its boundary) ([skills/0007 § 3](../findings/skills/0007-missile-hit-31-59.md#3-hit-31-43-and-55-heals-and-drains); fn:SKILLS_GetPhysMin@0x00647BC0, fn:SKILLS_GetPhysMax@0x00647D00, fn:sub_00623990_SkillSrcDamWeapon@0x00623990) | — | [C] |
| `MinLevDam1` | int 1..10 (9 distinct), 329 blank | `+0x1B0` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MinLevDam2` | int 1..15 (11 distinct), 329 blank | `+0x1B4` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MinLevDam3` | int 1..20 (10 distinct), 329 blank | `+0x1B8` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MinLevDam4` | int 1..26 (11 distinct), 329 blank | `+0x1BC` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MinLevDam5` | int 1..30 (14 distinct), 329 blank | `+0x1C0` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxDam` | int 1..60 (12 distinct), 328 blank | `+0x1AC` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxLevDam1` | int 1..10 (9 distinct), 329 blank | `+0x1C4` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxLevDam2` | int 1..15 (11 distinct), 329 blank | `+0x1C8` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxLevDam3` | int 1..21 (12 distinct), 329 blank | `+0x1CC` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxLevDam4` | int 1..26 (13 distinct), 329 blank | `+0x1D0` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `MaxLevDam5` | int 1..30 (13 distinct), 329 blank | `+0x1D4` s32 | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | — | [C] |
| `DmgSymPerCalc` | formula, 6 distinct, 351 blank | `+0x1D8` s32 calc | physical damage (base, per-level bands, synergy formula); *plan 0046 readers:* as `MinDam` | `skillscode.bin` | [C] |
| `EType` | str, 6 distinct, 257 blank | `+0x1DC` u8 index | elemental damage (type, base, per-level bands, synergy formula); `[I]` also the skill hit's conversion type (`DamagePacket+0x65`), stored by 15 start and do functions ([skills/0001 § 11](../findings/skills/0001-dispatch.md#11-the-skill-packet), [skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | `elemtypes:Code` | [C] |
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
| `ELen` | int 10..200 (8 distinct), 325 blank | `+0x214` s32 | elemental duration (base, per-level bands, synergy formula); *plan 0046 readers:* `[C]` `SKILLS_GetElemLen` (emulated in damage 11 and hit 53): `ELen` plus `(lvl − 1)·ELevLen1` below level 9, `(lvl − 8)·ELevLen2 + 7·ELevLen1` below 17, `(lvl − 16)·ELevLen3 + 8·ELevLen2 + 7·ELevLen1` from 17, plus `MulDiv(len, ELenSymPerCalc, 100)` when that calc is set and non-zero; 0 for an invalid skill or `lvl ≤ 0` ([skills/0005 § 15](../findings/skills/0005-missile-do-19-36-damage.md#15-damage-11-rabies-contagion), [skills/0007 § 8](../findings/skills/0007-missile-hit-31-59.md#8-hit-47-56-and-53-area-hits-and-the-contagion); fn:SKILLS_GetElemLen@0x00644F20) | — | [C] |
| `ELevLen1` | int 5..50 (7 distinct), 334 blank | `+0x218` s32 | elemental duration (base, per-level bands, synergy formula); *plan 0046 readers:* as `ELen` | — | [C] |
| `ELevLen2` | int 5..50 (7 distinct), 332 blank | `+0x21C` s32 | elemental duration (base, per-level bands, synergy formula); *plan 0046 readers:* as `ELen` | — | [C] |
| `ELevLen3` | int 2..50 (8 distinct), 332 blank | `+0x220` s32 | elemental duration (base, per-level bands, synergy formula); *plan 0046 readers:* as `ELen` | — | [C] |
| `ELenSymPerCalc` | formula, 4 distinct, 353 blank | `+0x224` s32 calc | elemental duration (base, per-level bands, synergy formula); *plan 0046 readers:* as `ELen` | `skillscode.bin` | [C] |
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
own tag; plan 0045 Phase 1 read the server readers ([skills/0001](../findings/skills/0001-dispatch.md),
[skills/0003](../findings/skills/0003-handlers.md)), and the meanings cite their sections, `[I]`.
The client columns are presentation and stay out of scope (plan 0045 *Open questions*, "Client-only skills").

### Function numbers and progressive columns

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `srvstfunc` | int 1..65 (64 distinct), 245 blank | `+0x02C` u16 | server start function number; `[I]` an index into `g_SkillStartFuncs` (`0x00732140`), called by `SKILLS_SrvStart` when 0 ≤ n < `0x5B`, a null entry passing ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart)); `[C]` every stock value names a non-null entry ([skills/0001](../findings/skills/0001-dispatch.md#answer-summary)); 1 is `SKILL_AttackStart` ([combat/0001](../findings/combat/0001-formulas.md); fn:SKILL_AttackStart@0x0056CA40); 42 (Fire Hit) is a start function that calls `MonAttackStats` with mode 8 ([combat/0001](../findings/combat/0001-formulas.md)); per number: § [Function index](#function-index-plan-0046-phase-0) | — | [C] |
| `srvdofunc` | int 1..152 (138 distinct), 83 blank | `+0x02E` u16 | server do function number; `[I]` an index into `g_SkillDoFuncs` (`0x007322B0`, 4-byte entries), called by `SKILLS_SrvDo` when 0 ≤ n < `0xBF` ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo)); `[C]` every stock value names a non-null entry ([skills/0001](../findings/skills/0001-dispatch.md#answer-summary)); `[I]` 1 is `SKILL_AttackDo` (`[C]`, [combat](../specs/combat/README.md); fn:SKILL_AttackDo@0x0056F070), 7 (Jab) `0x005DB2D0`, 67 (Charge) `0x005CF900` ([combat/0001](../findings/combat/0001-formulas.md)), 60 `SkillBoneWallDo`, 62 `SkillBonePrisonDo` ([items/0002](../findings/items/0002-quality-roll.md); fn:sub_005C58B0_SkillBoneWallDo@0x005C58B0, fn:sub_005C5D00_SkillBonePrisonDo@0x005C5D00), 98 `SkillMonTeleportDo` ([drlg/0009](../findings/drlg/0009-room-lifecycle.md); fn:sub_005CCC80_SkillMonTeleportDo@0x005CCC80); 58 (Revive), 91, 97, 135 and 140 create or revive monsters ([items/0001](../findings/items/0001-tc-resolution.md)); per number: § [Function index](#function-index-plan-0046-phase-0) | — | [C] |
| `srvprgfunc1` | int {40, 143}, 355 blank | `+0x030` u16 | progressive function 1; `[I]` `COMBAT_PrgFinisher` runs, at charge count `n` (1..3), `srvprgfunc n` through `g_SkillDoFuncs`, and before it `srvprgfunc1..n−1` when `prgstack` is set ([skills/0001 § 12](../findings/skills/0001-dispatch.md#12-progressive-charges), [skills/0003 § 1](../findings/skills/0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail); fn:COMBAT_PrgFinisher@0x005D5220) | — | [C] |
| `srvprgfunc2` | int {36, 38, 143}, 353 blank | `+0x032` u16 | progressive function 2 (as `srvprgfunc1`) | — | [C] |
| `srvprgfunc3` | int {37, 39, 41}, 353 blank | `+0x034` u16 | progressive function 3 (as `srvprgfunc1`) | — | [C] |
| `prgcalc1` | formula, 2 distinct, 355 blank | `+0x038` s32 calc | progressive formula 1; `[I]` the formula of charge count 1 (or of no charge state) for the functions that call `sub_005D3DA0_SkillPrgCalcByCharge` ([skills/0003 § 1](../findings/skills/0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail)); *plan 0046 readers:* `[C]` `sub_005D3DA0_SkillPrgCalcByCharge`: the calc at `+0x34 + 4 · clamp(charges, 1, 3)` (signed) on the progressive path (`progressive`, `aurastate` and `aurastat1` in range, a list of the state on the caster, the charges its `aurastat1` base stat), else `prgcalc1`; read by entries 37, 38, 39, 41, 143 and do 43, 48, 51, 54 (ADR-0021, as part of their maps), which fall back to `aurarangecalc` when it gives 0 (37, 38, 39, 143, do 51, 54) ([skills/0014 § 5](../findings/skills/0014-assassin.md#5-the-progressive-entries-3641-and-143), [skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54); fn:sub_005D3DA0_SkillPrgCalcByCharge@0x005D3DA0) | `skillscode.bin` | [C] |
| `prgcalc2` | formula, 2 distinct, 354 blank | `+0x03C` s32 calc | progressive formula 2; `[I]` charge count 2 (as `prgcalc1`); *plan 0046 readers:* as `prgcalc1` | `skillscode.bin` | [C] |
| `prgcalc3` | formula, 3 distinct, 353 blank | `+0x040` s32 calc | progressive formula 3; `[I]` charge count 3 (as `prgcalc1`); *plan 0046 readers:* as `prgcalc1` | `skillscode.bin` | [C] |
| `prgdam` | int {1, 2, 4}, 352 blank | `+0x044` u16 | `[I]` which progressive damage hook runs when the packet's result has bit `0x1`: 1 `PrgDamEd`, 2 `PrgDamSteal`, 3 `PrgDamFreeze`, 4 `PrgDamRelease` ([combat/0001](../findings/combat/0001-formulas.md); fn:COMBAT_PrgHooksAfterBuild@0x005D3BA0, fn:sub_005D3680_PrgDamEd@0x005D3680) | — | [C] |
| `progressive` | int {1}, 351 blank | `+0x004` bit 2 | a progressive (charge-up) skill; *plan 0046 readers:* `[C]` `SkillSrvMissileByCharge` (emulated inside do 17 and 22): `srvmissilea`, except for a row with this bit, `aurastate` and `aurastat1` in range and a caster list of that state whose base `aurastat1` is 2 (`srvmissileb`) or 3 and more (`srvmissilec`) ([skills/0008 § 7](../findings/skills/0008-sorceress.md#7-creations-do-17-22-24-26-28-and-do-20); fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0) | — | [C] |
| `cltstfunc` | int 0..82 (52 distinct), 250 blank | `+0x0F2` u16 | client start function (presentation) | — | [C] |
| `cltdofunc` | int 0..95 (75 distinct), 224 blank | `+0x0F4` u16 | client do function (presentation) | — | [C] |
| `cltprgfunc1` | int 12..93 (7 distinct), 348 blank | `+0x0F6` u16 | client progressive function 1 (presentation) | — | [C] |
| `cltprgfunc2` | int 9..83 (5 distinct), 351 blank | `+0x0F8` u16 | client progressive function 2 (presentation) | — | [C] |
| `cltprgfunc3` | int 9..15 (5 distinct), 351 blank | `+0x0FA` u16 | client progressive function 3 (presentation) | — | [C] |

### Missiles

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `srvmissile` | str, 42 distinct, 309 blank | `+0x046` u16 index | missile the server function creates; `[I]` `SKILLS_SrvDo` creates it after the do function (the line creator, or the lob creator with `lob`), also on rows with no `srvdofunc` ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo), [skills/0002 § 2](../findings/skills/0002-missiles.md#2-creation)) | `missiles:Missile` | [C] |
| `srvmissilea` | str, 93 distinct, 260 blank | `+0x048` u16 index | second server missile; `[I]` the missile of charge count 1 or less, and of every non-progressive row, for the do functions that call `sub_005D3CF0_SkillSrvMissileByCharge` ([skills/0003 § 1](../findings/skills/0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail)); *plan 0046 readers:* `[C]` do 63 (Poison Explosion) returns 1 when it is outside `[0, Missiles count)` (s16) ([skills/0010 § 5](../findings/skills/0010-necromancer.md#5-corpses-do-31-55-58-59-63); fn:sub_005C5E60_SkillDo63PoisonExpl@0x005C5E60); `[C]` do 85 and do 132 add the caster's MonStats chain position (`+0x04B`, `MONSTATS_GetClassChainPos`), so the n-th class of a chain casts the n-th missile after the named one (ADR-0021, up to `SkillMissileCreate`) ([skills/0016 § 6](../findings/skills/0016-monster-8a.md#6-missiles-and-the-infernos-do-85-88-93-95-111-start-53), [skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63); fn:sub_005CB0C0_SkillDo85ChainMissile@0x005CB0C0, fn:MONSTATS_GetClassChainPos@0x006510C0); `[C]` do 148 and do 149 add the monster-data byte `+0x0E` or `+0x0F` of a monster caster (0 for another type) and test the sum against the Missiles count (ADR-0021), `[I]` that byte being the caster's drawn [MonStats2](MonStats2.md) `S3v` or `S4v` variant ([skills/0018 § 3](../findings/skills/0018-monster-8c.md#3-the-missile-casts-do-130-132-136-139-148-149-and-start-63); fn:sub_005CDFB0_SkillDo148DoomKnightMissile@0x005CDFB0); `[C]` do 151 (item Chain Lightning) creates it when in `[0, Missiles count)` (`movsx`), else 0 ([skills/0015 § 4](../findings/skills/0015-item.md#4-do-113-and-do-151); fn:sub_005CA260_SkillDo151ItemChainLightning@0x005CA260); `[C]` do 134 tests it in `(0, count)` as a gate only, `[I]` so the stock row 301 (−1) returns 0 before its packet ([skills/0018 § 1](../findings/skills/0018-monster-8c.md#1-the-table-slots-the-stock-rows-and-the-callers)) | `missiles:Missile` | [C] |
| `srvmissileb` | str, 26 distinct, 330 blank | `+0x04A` u16 index | third server missile; *plan 0046 readers:* `[C]` `SkillSrvMissileByCharge` (emulated inside do 17 and 22) picks it for a `progressive` row at charge 2 (§ `progressive`) ([skills/0008 § 7](../findings/skills/0008-sorceress.md#7-creations-do-17-22-24-26-28-and-do-20); fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0); `[C]` do 8 and do 10 (Multiple Shot, Guided Arrow) take it, when ≥ 0, for a caster with no inventory (weapon word 0), else `srvmissilea` (ADR-0021, up to the inventory call or the first `MissileCreate`); `[I]` with an inventory, taken when the weapon word (`0x00623C60`) is not 1 ([skills/0009 § 6](../findings/skills/0009-amazon.md#6-creations-do-8-10-11-14); fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, fn:sub_005DB6D0_SkillDo10GuidedMissile@0x005DB6D0) | `missiles:Missile` | [C] |
| `srvmissilec` | str, 20 distinct, 337 blank | `+0x04C` u16 index | fourth server missile; *plan 0046 readers:* `[C]` `SkillSrvMissileByCharge` (emulated inside do 17 and 22) picks it for a `progressive` row at charge 3 or more (§ `progressive`) ([skills/0008 § 7](../findings/skills/0008-sorceress.md#7-creations-do-17-22-24-26-28-and-do-20); fn:sub_005D3CF0_SkillSrvMissileByCharge@0x005D3CF0) | `missiles:Missile` | [C] |
| `cltmissile` | str, 41 distinct, 306 blank | `+0x0E8` u16 index | client missile (presentation) | `missiles:Missile` | [C] |
| `cltmissilea` | str, 102 distinct, 238 blank | `+0x0EA` u16 index | client missile a (presentation) | `missiles:Missile` | [C] |
| `cltmissileb` | str, 36 distinct, 316 blank | `+0x0EC` u16 index | client missile b (presentation) | `missiles:Missile` | [C] |
| `cltmissilec` | str, 17 distinct, 326 blank | `+0x0EE` u16 index | client missile c (presentation) | `missiles:Missile` | [C] |
| `cltmissiled` | str {`vine beast neutral`}, 356 blank | `+0x0F0` u16 index | client missile d (presentation) | `missiles:Missile` | [C] |

### Parameters

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `Param1` | int -50..3600 (46 distinct), 97 blank | `+0x148` s32 | parameter 1 of the skill's functions; `[C]` the skill variables `par1` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` damage 7's stun length `Param1 + (lvl − 1)·Param2` when `dParam1` ≤ 0 (0 for an invalid skill or `lvl ≤ 0`) ([skills/0005 § 14](../findings/skills/0005-missile-do-19-36-damage.md#14-damage-2-3-4-7-8-9-10); fn:sub_005AD3E0_MissDmg07Stun@0x005AD3E0, fn:sub_004E6CA0_SkillParamByLevel@0x004E6CA0); `[C]` hit 28's radius `Param1 + (lvl − 1)·Param2` (ADR-0021, up to `MonFleeFrom`) ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005ABA10_MissHit28WardScare@0x005ABA10); `[C]` start 31: `MulDiv(base, max(stat 67, 50) + Param1, 100)` to `PathSetSpeed` (ADR-0021), `[I]` the charge's speed ([skills/0011 § 5](../findings/skills/0011-paladin.md#5-charge-and-the-missiles-start-31-do-67-73-80); fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0, fn:sub_004C9460_SkillGetParam1@0x004C9460); `[C]` do 144's block `+0x24 = frame + Param1 + (lvl − 1)·Param2` (0 term at `lvl ≤ 0`; ADR-0021, up to `SpawnOwnedMonster`), `[I]` the summons' life in frames ([skills/0008 § 6](../findings/skills/0008-sorceress.md#6-hydra-start-14-and-do-144); fn:sub_005CA910_SkillDo144Hydra@0x005CA910); `[C]` do 103 (DiabRun, row 198, stock `Param1..6` 8, 14, 5, 13, 16, 6) reads `Param1..6` raw: with the used node's bit 1, the caster's `+0x48` = `Param1 << 8` and `0x006212C0(caster, Param2)`; else at the animation frame equal to `Param3` the run (speed from `calc1`), at the frame equal to `Param4` `+0x48` = `Param5 << 8` and `0x006212C0(caster, Param6)`, `Param3` tested first (ADR-0021, up to those calls) ([skills/0017 § 4](../findings/skills/0017-monster-8b.md#4-the-hits-and-the-queued-hits-do-100-103-107-108-109-127-start-60); fn:sub_005CD380_SkillDo103DiabRun@0x005CD380); `[I]` do 72's quality bands `Param1..4`, after its boundary ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75); fn:sub_005D8780_CorpseFindItem@0x005D8780) | — | [C] |
| `Param2` | int -2..1500 (35 distinct), 119 blank | `+0x14C` s32 | parameter 2 of the skill's functions; `[C]` the skill variables `par2` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` the per-level term of `Param1` for damage 7, hit 28 and do 144 (§ `Param1`); damage 9's stun length when `dParam1` ≤ 0 ([skills/0005 § 14](../findings/skills/0005-missile-do-19-36-damage.md#14-damage-2-3-4-7-8-9-10); fn:sub_005AD4A0_MissDmg09StunParam2@0x005AD4A0); `[C]` hit 17's level margin, `Param2 + (owner level + lvl) > unit level` (ADR-0021) ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0); `[C]` do 21's stun flag, `RNG_Range(caster seed, 100) < Param2` (ADR-0021, up to `SkillRollPhys`), `[I]` the stun ([skills/0008 § 4](../findings/skills/0008-sorceress.md#4-start-12-and-do-21-telekinesis-and-dragon-flight); fn:sub_005C98F0_SkillDo21Telekinesis@0x005C98F0); `[C]` do 103's first `0x006212C0` argument (§ `Param1`); `[I]` do 72's second band (§ `Param1`) | — | [C] |
| `Param3` | int -50..4500 (44 distinct), 165 blank | `+0x150` s32 | parameter 3 of the skill's functions; `[C]` the skill variables `par3` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` hit 17's first value to `MonFleeFrom`, `Param3 + (lvl − 1)·Param4` (0 at `lvl ≤ 0`; ADR-0021), `[I]` its meaning to the AI ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0); `[C]` do 103's run frame (§ `Param1`); `[I]` do 69's first potion band and do 72's third band, after their boundaries ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75); fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0) | — | [C] |
| `Param4` | int -40..500 (35 distinct), 176 blank | `+0x154` s32 | parameter 4 of the skill's functions; `[C]` the skill variables `par4` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` hit 17's per-level term of `Param3` (ADR-0021) ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0); `[C]` do 111 (FetishAura) reads it raw, with no id test: `0x0056C210(game, caster; Param4 + 2·lvl, x, y)` at the target point (ADR-0021, up to the allocation inside it), `[I]` the radius of its unit search ([skills/0016 § 6](../findings/skills/0016-monster-8a.md#6-missiles-and-the-infernos-do-85-88-93-95-111-start-53); fn:sub_005CE670_SkillDo111FetishAura@0x005CE670); `[C]` start 27 passes it in `EDX` to `sub_0056E520_SkillAttackRateList` (ADR-0021) ([skills/0014 § 3](../findings/skills/0014-assassin.md#3-the-start-functions-2228); fn:sub_005D7090_SkillSt27DragonTail@0x005D7090); `[C]` entry 145 holds `frame + Param4` in its first argument's slot before its re-arm call, `[I]` the period of the next event 5 ([skills/0013 § 5](../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146); fn:sub_005C8380_SkillDo145Hurricane@0x005C8380); `[C]` do 103's second frame (§ `Param1`); `[I]` do 69's second band and do 72's fourth, after their boundaries ([skills/0012 § 4](../findings/skills/0012-barbarian.md#4-the-corpse-functions-start-33-34-do-69-72-75)) | — | [C] |
| `Param5` | int -75..3000 (30 distinct), 239 blank | `+0x158` s32 | parameter 5 of the skill's functions; `[C]` the skill variables `par5` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` hit 17's second value to `MonFleeFrom`, `Param5 + (lvl − 1)·Param6`; hit 28 passes it flat (ADR-0021), `[I]` its meaning to the AI ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005AAFB0_MissHit17Howl@0x005AAFB0, fn:sub_005ABA10_MissHit28WardScare@0x005ABA10); `[C]` do 103's frame word `Param5 << 8` (§ `Param1`); `[C]` do 141 (Baal Corpse Explode, row 285, stock 40 and a blank `Param6`) writes `(lvl − 1)·Param6 + Param5` (32-bit; 0 for a bad id or `lvl ≤ 0`) at its block's `+0x14` (ADR-0021, up to `0x0056DCC0`), `[I]` the block's radius ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112); fn:sub_005D2E80_SkillDo141BaalCorpse@0x005D2E80) | — | [C] |
| `Param6` | int -1..300 (22 distinct), 257 blank | `+0x15C` s32 | parameter 6 of the skill's functions; `[C]` the skill variables `par6` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` hit 17's per-level term of `Param5`; hit 28 passes it flat (ADR-0021) ([skills/0006 § 11](../findings/skills/0006-missile-hit-1-29.md#11-hit-17-howl-and-hit-28-grim-ward-scare-flee); fn:sub_005ABA10_MissHit28WardScare@0x005ABA10); `[C]` do 103's second `0x006212C0` argument (§ `Param1`); `[C]` do 141's per-level term of `Param5` | — | [C] |
| `Param7` | int -50..250 (19 distinct), 316 blank | `+0x160` s32 | parameter 7 of the skill's functions; `[C]` the skill variables `par7` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)); *plan 0046 readers:* `[C]` do 29 passes it to `NearestUnitInRange` (ADR-0021), `[I]` as the search radius ([skills/0008 § 5](../findings/skills/0008-sorceress.md#5-thunder-storm-start-13-and-do-29); fn:sub_005CA4D0_SkillDo29ThunderStorm@0x005CA4D0); `[C]` do 112 (MonCurseCast) draws one of the curse rows 66, 72, 82, 87, 91 (`k` = the caster's stepped low word mod 5) and fills its block from that row, not from its own row 212 (whose Params it does not read); the drawn row's `Param7` is read only for `k` = 4 (row 91), as the values of stats 67 and 68 (ADR-0021, up to `SkillForUnitsNearTarget`); `[C]` (data) row 91's `Param7` is blank ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112); fn:sub_005CE2B0_SkillDo112MonCurse@0x005CE2B0) | — | [C] |
| `Param8` | int 1..125 (23 distinct), 245 blank | `+0x164` s32 | parameter 8 of the skill's functions; `[C]` the skill variables `par8` and the pair codes read it ([data/calc § G](../specs/data/calc.md#g-variables)) | — | [C] |

### Animation, range and delay

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `anim` | str, 10 distinct, 23 blank | `+0x010` u8 index | player mode the skill puts the caster in; `[I]` a skill with `anim` 18 (the sequence mode) sets its delay only while `Unit+0x38 & 0xFFFFFF00` is 0 ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo)) | `plrmode:Code` | [C] |
| `seqtrans` | str, 10 distinct, 23 blank | `+0x012` u8 index | player mode used for a sequence's transitions | `plrmode:Code` | [C] |
| `monanim` | str, 8 distinct, 0 blank | `+0x011` u8 index | monster mode the skill puts a monster in (`xx` = none) | `monmode:code` | [C] |
| `seqnum` | int 1..41 (23 distinct), 323 blank | `+0x013` u8 | animation sequence number | — | [C] |
| `seqinput` | int {8, 10, 12}, 353 blank | `+0x016` u16 | sequence input frame | — | [C] |
| `range` | str, 4 distinct, 0 blank | `+0x014` u8 keyword | attack range class (`none`, `h2h`, `rng`, `both`); `[I]` `SKILLS_GetRangeType`: 0, 1, 2, and `both` 2 with a missile weapon, else 1 (1 in a `meleeonly` state); a request at a unit for a type-1 skill out of melee reach walks to the target first ([skills/0001 § 1](../findings/skills/0001-dispatch.md#1-the-request-client-packets-0x050x11)) | — | [C] |
| `delay` | formula, 9 distinct, 334 blank | `+0x190` s32 calc | cooldown formula; `[I]` a player whose skill gives `delay` > 0 gets state 121 (`skilldelay`) for that many frames, during which every skill whose own `delay` is ≥ 1 is refused ([skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo), [skills/0001 § 8](../findings/skills/0001-dispatch.md#8-the-delay-state)) | `skillscode.bin` | [C] |

### Costs

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `startmana` | int {6}, 354 blank | `+0x184` u16 | mana needed to start; `[I]` a player is refused below `startmana · 256` mana unless in state 12 (`inferno`) ([skills/0001 § 2](../findings/skills/0001-dispatch.md#2-skills_canuse-16-call-sites-4-of-them-in-the-request-handlers)); *plan 0046 readers:* `[C]` start 11 (Inferno) makes the same test for any caster type: stat 8 below `startmana << 8` (signed) refuses unless the caster has state 12 ([skills/0008 § 3](../findings/skills/0008-sorceress.md#3-inferno-and-arctic-blast-start-11-do-19-0x005c8e30-0x005c8ca0); fn:sub_005C8FA0_SkillSt11Inferno@0x005C8FA0); `[C]` start 26 (Blade Fury), with no state-12 list on the caster: a positive value (`cmp word; jle`) refuses (0) when `STATS_GetUnitStat(caster, 8, 0)` is below `startmana << 8` (ADR-0021), `[I]` stat 8 being mana in 256ths ([skills/0014 § 3](../findings/skills/0014-assassin.md#3-the-start-functions-2228); fn:sub_005D69D0_SkillSt26BladeFury@0x005D69D0) | — | [C] |
| `minmana` | int {0, 1}, 141 blank | `+0x186` u16 | minimum mana cost; `[I]` the payment's floor, `minmana · 256`; the checks do not floor ([skills/0001 § 7](../findings/skills/0001-dispatch.md#7-costs-and-their-rounding)); *plan 0046 readers:* `[C]` the floor `minmana << 8` (s16, signed compare) of `SKILLS_PayCost`'s cost (§ `mana`) | — | [C] |
| `manashift` | int 2..8 (6 distinct), 141 blank | `+0x188` u16 | fixed-point shift of the cost; `[C]` read as the byte at `+0x188`, masked to 5 bits, by the variables `mana`, `usmc`, `mps` ([data/calc § G](../specs/data/calc.md#g-variables)); `[I]` the payment reads it the same way ([skills/0001 § 7](../findings/skills/0001-dispatch.md#7-costs-and-their-rounding)); *plan 0046 readers:* as `mana` | — | [C] |
| `mana` | int 0..76 (39 distinct), 141 blank | `+0x18A` s16 | base mana cost; `[C]` `usmc` = `(lvlmana × (lvl − 1) + mana) << (manashift & 31)`, `mana` = `usmc >> 8` ([data/calc § G](../specs/data/calc.md#g-variables); fn:SKILLS_CalcVar@0x00646460); `[I]` the payment is `(lvlmana · max(lvl − 1, 0) + mana) << (manashift & 31)` in 1/256 mana (s16 terms, s32 arithmetic), floored at `minmana · 256`, and its result is ignored ([skills/0001 § 7](../findings/skills/0001-dispatch.md#7-costs-and-their-rounding)); *plan 0046 readers:* `[C]` `sub_00644B10_SkillManaCost(id, lvl)` = `((lvl − 1)·lvlmana + mana) << (manashift byte & 31)`, `movsx` terms, 32-bit, no floor at level 1; do 65, 66, 81, 82 give a player whose stat 8 is below it no stat values; `[I]` that it is the cost in 1/256 mana ([skills/0011 § 3](../findings/skills/0011-paladin.md#3-the-aura-functions-do-65-66-81-82); fn:sub_00644B10_SkillManaCost@0x00644B10); `[C]` `SKILLS_PayCost` (when the used node is not an item's charge): `mana` and `lvlmana` both 0 → 0; else `cost = (mana + lvlmana · max(lvl − 1, 0)) << (manashift & 31)` (32-bit, `manashift` the byte), raised to `minmana << 8` when greater (signed); a player whose stat 8 is below it → 0, else stat 8 less the cost (`BloodManaPay` in state 114); a non-player → 1 (ADR-0021); none of its three calls tests the result, so the 0 refuses nothing ([skills/0015 § 7](../findings/skills/0015-item.md#7-charges-skills_paycost); fn:SKILLS_PayCost@0x0056BFE0) | — | [C] |
| `lvlmana` | int -3..10 (8 distinct), 141 blank | `+0x18C` s16 | mana cost per level (the `usmc` term above; `[I]` the payment's, [skills/0001 § 7](../findings/skills/0001-dispatch.md#7-costs-and-their-rounding)); *plan 0046 readers:* as `mana` | — | [C] |
| `AttackNoMana` | int {1}, 316 blank | `+0x007` bit 4 | `[I]` when the use check fails with code 1, 2 or 4, the request falls back to the unit's Attack ([skills/0001 § 1](../findings/skills/0001-dispatch.md#1-the-request-client-packets-0x050x11)) | — | [C] |
| `usemanaondo` | int {1}, 355 blank | `+0x008` bit 5 | `[I]` the cost is checked and paid at the do function, not at the start ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart), [skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo)) | — | [C] |

### Start checks: town, item types, hands

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `InTown` | int {1}, 294 blank | `+0x005` bit 0 | `[I]` without it the start and the do refuse in a town room ([skills/0001 § 4](../findings/skills/0001-dispatch.md#4-skills_startusedskill-and-skills_srvstart), [skills/0001 § 6](../findings/skills/0001-dispatch.md#6-skills_srvdo)); *plan 0046 readers:* `[C]` start 40 (Leap) tests it as `+0x05 & g_BitMask32[0]`: when set, a town room does not refuse the target point of a caster that is not a monster (type 1 takes the monster branch with no town test, with or without a target) (ADR-0021) ([skills/0012 § 6](../findings/skills/0012-barbarian.md#6-whirlwind-the-leaps-and-double-throw-start-38-40-41-do-74-76-77-78); fn:sub_005D9D50_SkillSt40Leap@0x005D9D50); `[C]` entries 145 and 146: when clear and the caster's room is a town room (`RoomIsTown`), the branch that ends at `UNIT_UnlinkStatList(caster, list)` or `STATE_Set(caster, aurastate, 0)`, `[I]` that the state is removed and no further period is queued ([skills/0013 § 5](../findings/skills/0013-druid.md#5-the-periodic-states-do-table-entries-145-and-146)) | — | [C] |
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
| `weapsel` | int 1..4 (4 distinct), 342 blank | `+0x168` u16 | weapon selection (which hand or both); `[I]` no server read of `+0x168` ([skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | — | [C] |
| `leftskill` | int {1}, 261 blank | `+0x007` bit 6 | can be the left-hand skill; `[I]` one test, in the client ([skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | — | [C] |
| `repeat` | int {1}, 354 blank | `+0x005` bit 3 | repeats while the button is held (the name's reading); `[I]` no server reader, the only readers are client tests; set on the three `startmana` rows ([skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | — | [C] |
| `TgtPlaceCheck` | int {1}, 355 blank | `+0x008` bit 0 | `[I]` read by the monster AI's target test `sub_005FD470_MonSkillTargetOk`: the target must be dead and its cell free for its pattern; not a player start check ([skills/0003 § 12](../findings/skills/0003-handlers.md#12-routed-questions-from-p11)) | — | [C] |

### Summon columns

| Column | Observed | `.bin` field | Meaning | References | Layout tag |
|---|---|---|---|---|---|
| `summon` | str, 31 distinct, 325 blank | `+0x0BC` u16 index | monster class summoned; *plan 0046 readers:* `[C]` the spawn class (block `+0x08`; do 31: a frame word compared at its boundary, its block after) through `SkillSummonClass`/`SkillSummonRec` (in the MonStats count, else refused) for do 15, 16 ([skills/0009 § 8](../findings/skills/0009-amazon.md#8-do-15-and-do-16-dopplezon-and-valkyrie)), do 31, 56, 57, 60, 62 (do 56 a signed test, then the count; [skills/0010 § 5](../findings/skills/0010-necromancer.md#5-corpses-do-31-55-58-59-63), [§ 6](../findings/skills/0010-necromancer.md#6-summons-do-56-57-60-62)) and do 144 ([skills/0008 § 6](../findings/skills/0008-sorceress.md#6-hydra-start-14-and-do-144)) (ADR-0021, up to `SpawnOwnedMonster`); `[I]` do 144's second and third spawns are `summon + 1`, `summon + 2` (fn:sub_0063EA70_SkillSummonRec@0x0063EA70, fn:sub_0056D940_SpawnOwnedMonster@0x0056D940); `[C]` `sub_0056E620_SkillSummonClass` with `EDX` 1 (start 49, 62, do 84, 87) gives a **monster** caster its own MonStats `spawn`, `spawnx`/`spawny` and `spawnmode` instead; a non-monster caster, and every caster with `EDX` 0 (do 104, 114, 115, 119, 44, 45, 49; do 131's class change, `[I]` after its boundary), gets `summon` and `summode` (ADR-0021) ([skills/0016 § 4](../findings/skills/0016-monster-8a.md#4-moves-and-marks-start-4346-48-49-51-52-do-8991-94-98), [skills/0016 § 5](../findings/skills/0016-monster-8a.md#5-spawns-heals-and-revives-do-84-86-87-96-97), [skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112), [skills/0018 § 5](../findings/skills/0018-monster-8c.md#5-moves-spawns-and-links-start-61-62-do-129-135-140-147), [skills/0013 § 3](../findings/skills/0013-druid.md#3-the-summons-do-114-115-119), [skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54); fn:sub_0056E620_SkillSummonClass@0x0056E620, fn:sub_005CBD10_SkillSt49Nest@0x005CBD10, fn:sub_005CD5D0_SkillDo104DiabPrison@0x005CD5D0, fn:sub_005D2420_SkillSt62MinionSpawner@0x005D2420) | `monstats:Id` | [C] |
| `pettype` | str, 16 distinct, 326 blank | `+0x0BE` u8 index | [PetType](PetType.md) of the summon; `[I]` the type the pet limit counts, and PetType `group` clears the owner's pets of the group's other types ([skills/0003 § 7](../findings/skills/0003-handlers.md#7-summons)); *plan 0046 readers:* `[C]` read `movzx` by do 15, 16, 56, 57, 58, 60, 62: at or past the PetType count it is stored as 0, not refused; read signed by do 31 (`movsx`) and do 144 (s8): below 0 or at or past the count refuses; the spawn block's `+0x1C` (ADR-0021; do 31 builds its block after its boundary, `[I]`) ([skills/0009 § 8](../findings/skills/0009-amazon.md#8-do-15-and-do-16-dopplezon-and-valkyrie), [skills/0010 § 5](../findings/skills/0010-necromancer.md#5-corpses-do-31-55-58-59-63), [§ 6](../findings/skills/0010-necromancer.md#6-summons-do-56-57-60-62), [skills/0008 § 6](../findings/skills/0008-sorceress.md#6-hydra-start-14-and-do-144); fn:sub_005C4B00_SkillDo31RaiseSkeleton@0x005C4B00, fn:sub_005C5100_SkillDo56Golem@0x005C5100); `[C]` do 114, 115, 119 read it `movsx` and **refuse** (0, bit 6 not set) a negative value or one at or past `DataTables+0xBF0`, else block `+0x1C`, `[I]` that count being PetType's row count ([skills/0013 § 3](../findings/skills/0013-druid.md#3-the-summons-do-114-115-119); fn:sub_005C6910_SkillDo114Summon@0x005C6910); `[C]` do 44 and 45's trap helper (`movsx`) and do 49 (`movzx`) store such a value as **0**, no refusal (ADR-0021) ([skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54); fn:sub_005D5E10_TrapSpawn@0x005D5E10, fn:sub_005D6E70_SkillDo49Shadow@0x005D6E70); `[I]` `sub_00575900_PetLimitRefresh` and `sub_0056BD90_PetLimitForSkill` take a player's skills whose `pettype` is above 0 and below the count for each type's limit ([skills/0015 § 10](../findings/skills/0015-item.md#10-pets-when-petmax-falls); fn:sub_00575900_PetLimitRefresh@0x00575900, fn:sub_0056BD90_PetLimitForSkill@0x0056BD90) | `pettype:pet type` | [C] |
| `summode` | str {`NU`, `S1`, `S2`}, 325 blank | `+0x0BF` u8 index | mode the summon spawns in; *plan 0046 readers:* `[C]` block `+0x10`: the mode, `summode` when 0..15, else 1 (the `SkillSummonClass` path); do 56 returns 1 when it is 16 or more (unsigned) (ADR-0021) ([skills/0008 § 6](../findings/skills/0008-sorceress.md#6-hydra-start-14-and-do-144), [skills/0010 § 6](../findings/skills/0010-necromancer.md#6-summons-do-56-57-60-62); fn:sub_005C5100_SkillDo56Golem@0x005C5100); `[C]` (`movsx`, kept in `[0, 16)` else 1) block `+0x10` of do 114 and 119 (do 115 puts 8 there) and `+0x24` of do 114 and 115 ([skills/0013 § 3](../findings/skills/0013-druid.md#3-the-summons-do-114-115-119)); `+0x10` and `+0x24` of do 49 ([skills/0014 § 6](../findings/skills/0014-assassin.md#6-traps-states-and-areas-do-43-44-45-47-48-49-51-54)); do 104 writes it over its level argument's slot and does not pass it on ([skills/0017 § 5](../findings/skills/0017-monster-8b.md#5-the-node-words-the-prison-the-corpse-explosion-and-the-curse-start-54-55-59-64-do-104-141-112)) (ADR-0021); `[I]` do 131's class change likewise ([skills/0018 § 4](../findings/skills/0018-monster-8c.md#4-the-hits-the-curses-and-the-states-do-128-131-133-134-137)) | `monmode:code` | [C] |
| `petmax` | formula, 7 distinct, 329 blank | `+0x0C0` s32 calc | pet count limit formula; `[C]` the skill variable `pets` (71) ([data/calc § G](../specs/data/calc.md#g-variables)); `[I]` the limit `PetAdd` enforces: above it the owner's first pet of the type is removed ([skills/0003 § 7](../findings/skills/0003-handlers.md#7-summons)); *plan 0046 readers:* `[C]` block `+0x20`, the calc's value (the owner's in do 144) (ADR-0021), `[I]` what the spawn does with it ([skills/0009 § 8](../findings/skills/0009-amazon.md#8-do-15-and-do-16-dopplezon-and-valkyrie), [skills/0008 § 6](../findings/skills/0008-sorceress.md#6-hydra-start-14-and-do-144); fn:sub_005DC000_SkillDo15Dopplezon@0x005DC000); `[C]` block `+0x20` of do 114, 115, 119 (ADR-0021) ([skills/0013 § 3](../findings/skills/0013-druid.md#3-the-summons-do-114-115-119)); `[I]` `PetLimitRefresh`'s limit per type: the highest `max(petmax, 1)` over the player's skills of the type, PetType `basemax` for a type none raises ([skills/0015 § 10](../findings/skills/0015-item.md#10-pets-when-petmax-falls)) | `skillscode.bin` | [C] |
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

Moved to § [Function index](#function-index-plan-0046-phase-0) (plan 0046 Phase 0), which lists each number's rows
with their kinds, parameters and batch. (tbl:Skills.txt:srvdofunc)

### Families and the tier-A candidates

`[C]` as data: `skills_survey.py families` and `skills_survey.py tiera` (`fam_*`, `ta_*` keys).

- `[C]` **Family sizes** (stock rows per number; a family of ten rows or more is one the plan's tier A must
  represent): `srvstfunc` 4 × 18 is the only one (47 of its 64 numbers have one row); `srvdofunc` 65 × 17, 2 × 12,
  28 × 12, 18 × 11, 30 × 10 (98 of 138 numbers have one row); no `srvprgfunc` number has more than 2 rows; Missiles
  `pSrvDoFunc` 1 × 551 and 3 × 26 (23 of 34 numbers have one row); no `pSrvHitFunc` or `pSrvDmgFunc` number has ten
  rows (largest 8 and 6). Eight families in all. (tbl:Skills.txt:srvdofunc, tbl:Missiles.txt:pSrvDoFunc)
- `[C]` **The candidates.** The first 22 rows below are the plan's named skills (the general rows and per class; the Druid
  and Assassin pairs are this phase's proposal: 221 Raven and 225 Firestorm, 251 Fire Trauma, which is *Fire Blast*,
  and 259 Fists of Fire, a progressive melee skill with `srvprgfunc`); they cover four of the eight families
  (`srvstfunc` 4, `srvdofunc` 2 and 18, `pSrvDoFunc` 1). One row per uncovered family is added, a class row first:
  56 Meteor (`srvdofunc` 28), 66 Amplify Damage (30), 98 Might (65) and 25 Plague Javelin (its missile's
  `pSrvDoFunc` 3); then none is uncovered (`ta_big_uncovered=0`). The monster skills of the combat logs' attackers
  are not in the excel data: Phase 1.3 adds them from the kept logs. Tier A is fixed (plan 0045 P1.3 review): these 26
rows, the monster skills being those the Phase 2 sessions' attackers use.
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

## Function index (plan 0046 Phase 0)

`[C]` as data: `python3 -I tools/skills_survey.py --index workspace/merged/data/global/excel` (gate survey `skills`,
the `ix_*` keys). One entry per function-table entry a stock row uses, in its table (`[I]`, the code readings of
[skills/0001](../findings/skills/0001-dispatch.md#answer-summary) §§ 4, 6, 10 and 12 and
[skills/0003](../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites) § 9):

- the **start table** `g_SkillStartFuncs` (`0x00732140`), indexed by `srvstfunc`: 64 entries;
- the **do table** `g_SkillDoFuncs` (`0x007322B0`), indexed by `srvdofunc`, by `srvprgfunc1..3` (the progressive
  finisher), by `ItemEffect` when it is above 1 (an item cast with the effect flag) and by States `srvactivefunc`:
  149 entries, of them 138 `srvdofunc` numbers, 7 `srvprgfunc` numbers (none is also a `srvdofunc`), 2 `ItemEffect`
  numbers (36, also Claws of Thunder's `srvprgfunc2`, and 151, named by nothing else) and 3 `srvactivefunc` numbers
  (145 `hurricane`, 146 `armageddon`, 147 `attached`, named by no Skills row: the do entries skills/0001 found used by
  no stock row are these and 53, 138, 142) (`ix_start_entries=64`, `ix_do_entries=149`, `ix_do_*`).

The missile tables are [Missiles § Function index](Missiles.md#function-index-plan-0046-phase-0) (97 entries).
(tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc, tbl:Skills.txt:srvprgfunc1, tbl:Skills.txt:ItemEffect,
tbl:States.txt:srvactivefunc)

The columns of the tables below:

- **Rows**: the Skills rows that name the entry (for a do entry, by column when more than `srvdofunc` names it); the
  States rows are listed and not counted.
- **Row kinds**: the rows by kind, a class code (`ama`, `sor`, `nec`, `pal`, `bar`, `dru`, `ass`), `monster` (no
  `charclass`, neither the `general` bit nor a `1` in `scroll`; 159 MaggotEgg, whose `scroll` bit a single space sets,
  counts here), `item` (the four scroll and book rows) or `general` (rows 0–5, the `general` bit). `ItemEffect` users
  are not counted (an item cast of another row's skill); a `srvactivefunc`-only entry counts the Skills rows whose
  `aurastate` is that state.
- **Batch**: the plan [0046](../plans/0046-skills-function-catalogue.md) Phase 1 batch, by rule: the class with most
  rows (a tie goes to the first in PlayerClass order), else `monster` when a monster row uses it, else `item` (a scroll
  row or an `ItemEffect` cast), else `general`. 12 entries have rows of two classes or more and 22 have class and
  monster rows; the rule puts them with the class (`ix_multiclass=12`, `ix_class_and_monster=22`).
- **Tier A**: `A` when one of the 26 tier-A rows (plan 0045, § [Families](#families-and-the-tier-a-candidates)) names
  it as `srvstfunc`, `srvdofunc` or `srvprgfunc`; these are the functions
  [skills/0003 § 5](../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions) and § 1 read. 9 start and 21
  do entries (`ix_start_tiera`, `ix_do_tiera`).
- **Params, Calcs**: how many of the entry's rows set each of `Param1..8` and `calc1..4` (and `prgcalc1..3` for a
  `srvprgfunc` entry). A set cell is data; which of them the function reads is plan 0046 Phase 1's.

### Batches

| Batch | Entries | Start | Do | Missile do / hit / damage | Reached by tier A |
|---|---:|---:|---:|---|---:|
| `ama` | 17 | 7 | 10 | — | 4 |
| `sor` | 18 | 4 | 14 | — | 5 |
| `nec` | 19 | 7 | 12 | — | 3 |
| `pal` | 15 | 5 | 10 | — | 3 |
| `bar` | 19 | 7 | 12 | — | 2 |
| `dru` | 16 | 3 | 13 | — | 2 |
| `ass` | 29 | 7 | 22 | — | 5 |
| `monster` | 70 | 20 | 50 | — | 0 |
| `missile` | 97 | — | — | 34 / 50 / 13 | 10 |
| `item` | 2 | 0 | 2 | — | 0 |
| `general` | 8 | 4 | 4 | — | 6 |
| all | 310 | 64 | 149 | 34 / 50 / 13 | 40 |

`[C]` as data (`ix_batch_*`, `ix_entries=310`). The `item` entries are do 113 (the four scroll and book rows) and do
151 (Chain Lightning's item cast); the `general` entries are start 1, 2, 3, 65 and do 1, 3, 4, 5, all tier A but
Unsummon's start 3 and do 4. (tbl:Skills.txt:charclass, tbl:Skills.txt:general, tbl:Skills.txt:scroll)

### Start table (`srvstfunc`)

| Number | Rows | Batch | Tier A | Row kinds | Params (rows set) | Calcs (rows set) | Rows |
|---:|---:|---|---|---|---|---|---|
| 1 | 2 | general | A | general 2 | — | — | 0 Attack, 5 Left Hand Swing |
| 2 | 1 | general | A | general 1 | — | — | 1 Kick |
| 3 | 1 | general | — | general 1 | — | — | 3 Unsummon |
| 4 | 18 | ama | A | ama 12, monster 6 | Param1 5, Param2 3, Param3 3, Param4 1, Param7 2, Param8 10 | calc1 6, calc2 2, calc3 1 | 7 Fire Arrow, 11 Cold Arrow, 12 Multiple Shot, 15 Poison Javelin, 16 Exploding Arrow, 20 Lightning Bolt, 21 Ice Arrow, 22 Guided Arrow, 25 Plague Javelin, 27 Immolation Arrow, 31 Freezing Arrow, 35 Lightning Fury, 339 MonBow, 340 MonFireArrow, 341 MonColdArrow, 342 MonExplodingArrow, 343 MonFreezingArrow, 345 SuccubusBolt |
| 5 | 1 | ama | A | ama 1 | Param3 1, Param4 1 | calc1 1 | 10 Jab |
| 6 | 4 | ama | — | ama 2, monster 2 | Param1 1, Param2 1, Param8 2 | calc1 1 | 14 Power Strike, 24 Charged Strike, 344 MonPowerStrike, 347 MonIceSpear |
| 7 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 19 Impale |
| 8 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 26 Strafe |
| 9 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 30 Fend |
| 10 | 1 | ama | — | ama 1 | Param1 1, Param3 1, Param4 1, Param8 1 | calc1 1, calc2 1 | 34 Lightning Strike |
| 11 | 2 | sor | — | sor 1, dru 1 | Param1 2, Param2 2, Param3 2, Param8 2 | calc1 2, calc2 2 | 41 Inferno, 230 Arctic Blast |
| 12 | 2 | sor | — | sor 1, ass 1 | Param1 2, Param2 2, Param7 1 | — | 43 Telekinesis, 275 Dragon Flight |
| 13 | 1 | sor | — | sor 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | — | 57 Thunder Storm |
| 14 | 1 | sor | — | sor 1 | Param1 1, Param2 1, Param8 1 | — | 62 Hydra |
| 15 | 2 | nec | A | nec 2 | Param1 1, Param2 2, Param3 1, Param4 1, Param5 2 | calc1 2 | 70 Raise Skeleton, 80 Raise Skeletal Mage |
| 16 | 1 | nec | — | nec 1 | Param8 1 | — | 73 Poison Dagger |
| 17 | 3 | nec | — | nec 2, monster 1 | Param1 2, Param2 2, Param3 1, Param4 1, Param5 2, Param8 1 | calc1 2, calc2 2, calc3 2 | 74 Corpse Explosion, 83 Poison Explosion, 351 NihlathakCorpseExplosion |
| 18 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 86 Attract |
| 19 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 88 Bone Prison |
| 20 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 90 IronGolem |
| 21 | 1 | nec | — | nec 1 | Param1 1, Param3 1, Param4 1, Param5 1 | calc1 1, calc2 1 | 95 Revive |
| 22 | 1 | ass | — | ass 1 | Param1 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1, calc4 1 | 253 Psychic Hammer |
| 23 | 6 | ass | A | ass 6 | Param1 6, Param2 5, Param3 6, Param4 6, Param5 2, Param6 1, Param7 1, Param8 3 | calc1 3 | 254 Tiger Strike, 259 Fists of Fire, 265 Cobra Strike, 269 Claws of Thunder, 274 Blades of Ice, 280 Royal Strike |
| 24 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1, calc4 1 | 255 Dragon Talon |
| 25 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 260 Dragon Claw |
| 26 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 266 Blade Fury |
| 27 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 270 Dragon Tail |
| 28 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 277 Blade Shield |
| 29 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param7 1, Param8 1 | calc1 1, calc2 1 | 96 Sacrifice |
| 31 | 2 | pal | — | pal 1, monster 1 | Param1 2, Param2 1, Param3 2, Param4 2, Param5 1, Param6 1, Param8 1 | calc1 1 | 107 Charge, 352 SerpentCharge |
| 32 | 5 | bar | A | pal 1, bar 3, monster 1 | Param1 5, Param2 5, Param3 4, Param4 4, Param5 1, Param6 2, Param7 3, Param8 3 | calc1 5, calc2 2, calc4 1 | 116 Conversion, 126 Bash, 139 Stun, 144 Concentrate, 326 BearSmite |
| 33 | 2 | bar | — | bar 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 1, Param6 1 | calc1 2 | 131 Find Potion, 150 Grim Ward |
| 34 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 142 Find Item |
| 35 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1, Param8 1 | calc1 1, calc2 1, calc3 1 | 111 Vengeance |
| 36 | 1 | pal | A | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | calc1 1 | 117 Holy Shield |
| 37 | 3 | pal | — | pal 1, dru 1, monster 1 | Param1 1, Param2 3, Param3 3, Param4 3, Param5 2, Param6 2, Param8 1 | calc1 2, calc2 2 | 106 Zeal, 248 Fury, 328 BloodLordFrenzy |
| 38 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1 | calc1 1 | 151 Whirlwind |
| 39 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param8 1 | calc1 1, calc2 1, calc4 1 | 152 Berserk |
| 40 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 132 Leap |
| 41 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | calc1 1 | 143 Leap Attack |
| 42 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 156 Fire Hit |
| 43 | 1 | monster | — | monster 1 | — | calc1 1 | 159 MaggotEgg |
| 44 | 1 | monster | — | monster 1 | — | — | 161 MagottUp |
| 45 | 1 | monster | — | monster 1 | — | calc1 1 | 162 MagottDown |
| 46 | 1 | monster | — | monster 1 | — | — | 164 AndrialSpray |
| 47 | 1 | monster | — | monster 1 | — | calc1 1 | 165 Jump |
| 48 | 1 | monster | — | monster 1 | — | calc1 1, calc2 1 | 166 Swarm Move |
| 49 | 2 | monster | — | monster 2 | — | — | 167 Nest, 320 EvilHutSpawner |
| 50 | 1 | monster | — | monster 1 | — | — | 168 Quick Strike |
| 51 | 1 | monster | — | monster 1 | — | — | 176 Submerge |
| 52 | 1 | monster | — | monster 1 | — | — | 180 Emerge |
| 53 | 6 | monster | — | monster 6 | Param1 6, Param2 1, Param3 2, Param4 1, Param8 1 | calc1 1, calc2 6, calc3 6, calc4 1 | 178 FetishInferno, 193 DiabLight, 311 mon inferno sentry, 317 Baal Inferno, 319 MegademonInferno, 323 Horror Arctic Blast |
| 54 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 198 DiabRun |
| 55 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 206 Mosquito |
| 56 | 2 | dru | — | dru 2 | Param1 1, Param2 1, Param3 2, Param4 2, Param5 2, Param6 2, Param7 2, Param8 2 | calc1 2, calc2 2 | 232 Feral Rage, 233 Maul |
| 57 | 1 | dru | — | dru 1 | Param8 1 | — | 238 Rabies |
| 58 | 1 | dru | — | dru 1 | Param8 1 | calc1 1 | 239 Fire Claws |
| 59 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 282 Imp Inferno |
| 60 | 1 | monster | — | monster 1 | Param1 1 | calc1 1 | 289 Suck Blood |
| 61 | 1 | monster | — | monster 1 | — | — | 293 Self-resurrect |
| 62 | 1 | monster | — | monster 1 | — | — | 302 MinionSpawner |
| 63 | 2 | monster | — | monster 2 | Param1 2, Param2 2 | calc1 2 | 307 CorpseCycler, 325 VineCycler |
| 64 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | — | 215 MonFrenzy |
| 65 | 2 | general | A | general 2 | — | — | 2 Throw, 4 Left Hand Throw |

### Do table (`srvdofunc`, `srvprgfunc1..3`, `ItemEffect`, States `srvactivefunc`)

| Number | Rows | Batch | Tier A | Row kinds | Params (rows set) | Calcs (rows set) | Rows |
|---:|---:|---|---|---|---|---|---|
| 1 | 2 | general | A | general 2 | — | — | 0 Attack, 5 Left Hand Swing |
| 2 | 12 | bar | A | ama 2, pal 1, bar 4, dru 1, monster 3, general 1 | Param1 7, Param2 7, Param3 6, Param4 6, Param5 3, Param6 3, Param7 4, Param8 7 | calc1 8, calc2 5, calc3 2, calc4 2 | 1 Kick, 14 Power Strike, 19 Impale, 111 Vengeance, 126 Bash, 139 Stun, 144 Concentrate, 152 Berserk, 239 Fire Claws, 326 BearSmite, 344 MonPowerStrike, 347 MonIceSpear |
| 3 | 1 | general | A | general 1 | — | — | 2 Throw |
| 4 | 1 | general | — | general 1 | — | — | 3 Unsummon |
| 5 | 1 | general | A | general 1 | — | — | 4 Left Hand Throw |
| 6 | 2 | ama | — | ama 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 2, Param6 2 | — | 8 Inner Sight, 17 Slow Missiles |
| 7 | 1 | ama | A | ama 1 | Param3 1, Param4 1 | calc1 1 | 10 Jab |
| 8 | 4 | ama | A | ama 1, nec 1, dru 1, monster 1 | Param1 4, Param2 4, Param3 3, Param4 1, Param8 2 | calc1 4, calc2 3, calc3 1 | 12 Multiple Shot, 67 Teeth, 191 PrimePoisonball, 243 Shock Wave |
| 9 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1, Param8 1 | calc1 1, calc4 1 | 147 Frenzy |
| 10 | 3 | ama | — | ama 1, nec 1, monster 1 | Param1 1, Param2 1, Param3 2, Param4 2, Param5 1, Param6 1, Param8 1 | calc1 2 | 22 Guided Arrow, 93 Bone Spirit, 211 MonBoneSpirit |
| 11 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 24 Charged Strike |
| 12 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 26 Strafe |
| 13 | 3 | ama | — | ama 1, pal 1, dru 1 | Param1 1, Param2 3, Param3 3, Param4 3, Param5 2, Param6 2, Param8 1 | calc1 3, calc2 3 | 30 Fend, 106 Zeal, 248 Fury |
| 14 | 1 | ama | — | ama 1 | Param1 1, Param3 1, Param4 1, Param8 1 | calc1 1, calc2 1 | 34 Lightning Strike |
| 15 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param7 1 | calc1 1, calc2 1, calc3 1 | 28 Dopplezon |
| 16 | 1 | ama | — | ama 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1, Param8 1 | calc1 1, calc2 1 | 32 Valkyrie |
| 17 | 4 | sor | — | sor 1, monster 3 | Param1 2, Param2 2, Param8 2 | calc1 4, calc4 1 | 38 Charged Bolt, 186 PrimeBolt, 306 BoltSentry, 322 ImpBolt |
| 18 | 11 | sor | A | sor 3, nec 1, pal 1, dru 1, ass 3, monster 2 | Param1 11, Param2 11, Param3 9, Param4 9, Param5 7, Param6 7, Param7 4, Param8 7 | calc1 2 | 40 Frozen Armor, 50 Shiver Armor, 60 Chilling Armor, 68 Bone Armor, 117 Holy Shield, 209 MonFrozenArmor, 210 MonBoneArmor, 235 Cyclone Armor, 258 Quickness, 267 Fade, 278 Venom |
| 19 | 2 | sor | — | sor 1, dru 1 | Param1 2, Param2 2, Param3 2, Param8 2 | calc1 2, calc2 2 | 41 Inferno, 230 Arctic Blast |
| 20 | 1 | sor | A | sor 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 42 Static Field |
| 21 | 1 | sor | — | sor 1 | Param1 1, Param2 1 | — | 43 Telekinesis |
| 22 | 9 | sor | A | sor 2, nec 1, bar 1, monster 5 | Param1 7, Param2 7, Param3 3, Param4 3, Param5 1, Param6 1, Param8 2 | calc1 1 | 44 Frost Nova, 48 Nova, 92 Poison Nova, 130 Howl, 190 PrimeIceNova, 195 DiabFire, 316 Baal Nova, 346 MephFrostNova, 353 Trap Nova |
| 23 | 4 | sor | — | sor 2, monster 2 | Param1 4, Param2 4, Param3 1, Param4 1, Param5 1, Param7 1, Param8 1 | calc1 1, calc2 1, calc4 1 | 46 Blaze, 58 Energy Shield, 173 SpiderLay, 187 PrimeBlaze |
| 24 | 4 | sor | — | sor 1, monster 3 | Param1 1, Param2 1, Param3 1, Param4 1, Param7 1, Param8 1 | — | 51 Fire Wall, 170 VampireFirewall, 188 PrimeFirewall, 321 CountessFirewall |
| 25 | 1 | sor | — | sor 1 | Param1 1, Param2 1, Param3 1, Param8 1 | — | 52 Enchant |
| 26 | 1 | sor | — | sor 1 | Param1 1, Param3 1, Param4 1, Param5 1, Param8 1 | calc1 1 | 53 Chain Lightning |
| 27 | 1 | sor | A | sor 1 | — | — | 54 Teleport |
| 28 | 12 | sor | A | sor 2, dru 1, monster 9 | Param1 10, Param2 7, Param3 7, Param4 6, Param5 2, Param6 2, Param8 3 | calc1 5, calc2 3, calc4 1 | 56 Meteor, 59 Blizzard, 171 VampireMeteor, 205 MonBlizzard, 213 HellMeteor, 234 Eruption, 284 Baal Taunt, 287 Catapult Charged Ball, 288 Catapult Spike Ball, 303 CatapultBlizzard, 304 CatapultPlague, 305 CatapultMeteor |
| 29 | 1 | sor | — | sor 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | — | 57 Thunder Storm |
| 30 | 10 | nec | A | nec 8, monster 2 | Param1 10, Param2 10, Param3 10, Param4 10, Param5 9, Param6 5 | calc1 2, calc2 1, calc3 1 | 66 Amplify Damage, 71 Dim Vision, 72 Weaken, 76 Iron Maiden, 77 Terror, 82 Life Tap, 87 Decrepify, 91 Lower Resist, 309 Defense Curse, 310 Blood Mana |
| 31 | 2 | nec | A | nec 2 | Param1 1, Param2 2, Param3 1, Param4 1, Param5 2 | calc1 2 | 70 Raise Skeleton, 80 Raise Skeletal Mage |
| 32 | 1 | nec | — | nec 1 | Param8 1 | — | 73 Poison Dagger |
| 33 | 1 | ass | — | ass 1 | Param1 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1, calc4 1 | 253 Psychic Hammer |
| 34 | 3 | ass | — | ass 3 | Param1 3, Param2 3, Param3 3, Param4 3, Param5 1, Param6 1, Param7 1 | calc1 2 | 254 Tiger Strike, 265 Cobra Strike, 280 Royal Strike |
| 35 | 3 | ass | A | ass 3 | Param1 3, Param2 2, Param3 3, Param4 3, Param5 1, Param8 3 | calc1 1 | 259 Fists of Fire, 269 Claws of Thunder, 274 Blades of Ice |
| 36 | 3 | ass | — | ass 1 | Param1 3, Param2 2, Param3 1, Param4 1, Param8 2 | prgcalc3 1 | `srvprgfunc`: 269 Claws of Thunder; `ItemEffect`: 44 Frost Nova, 48 Nova |
| 37 | 1 | ass | — | ass 1 | Param1 1, Param3 1, Param4 1, Param8 1 | prgcalc3 1 | `srvprgfunc`: 269 Claws of Thunder |
| 38 | 2 | ass | A | ass 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 1, Param8 2 | calc1 1, prgcalc2 2, prgcalc3 2 | `srvprgfunc`: 259 Fists of Fire, 274 Blades of Ice |
| 39 | 2 | ass | A | ass 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 1, Param8 2 | calc1 1, prgcalc2 2, prgcalc3 2 | `srvprgfunc`: 259 Fists of Fire, 274 Blades of Ice |
| 40 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | calc1 1, prgcalc2 1, prgcalc3 1 | `srvprgfunc`: 280 Royal Strike |
| 41 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | calc1 1, prgcalc2 1, prgcalc3 1 | `srvprgfunc`: 280 Royal Strike |
| 42 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1, calc4 1 | 255 Dragon Talon |
| 43 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param8 1 | — | 256 Shock Field |
| 44 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc4 1 | 257 Blade Sentinel |
| 45 | 5 | ass | — | ass 5 | Param1 5, Param3 1, Param4 1, Param7 1, Param8 5 | calc4 1 | 261 Charged Bolt Sentry, 262 Wake of Fire Sentry, 271 Lightning Sentry, 272 Inferno Sentry, 276 Death Sentry |
| 46 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 260 Dragon Claw |
| 47 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1, Param8 1 | — | 264 Cloak of Shadows |
| 48 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 266 Blade Fury |
| 49 | 2 | ass | — | ass 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 2, Param6 2 | — | 268 Shadow Warrior, 279 Shadow Master |
| 50 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 270 Dragon Tail |
| 51 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | — | 273 Mind Blast |
| 52 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param7 1 | — | 275 Dragon Flight |
| 54 | 1 | ass | — | ass 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 277 Blade Shield |
| 55 | 3 | nec | — | nec 1, monster 2 | Param1 3, Param2 3, Param3 2, Param4 2, Param5 2, Param8 1 | calc1 3, calc2 3, calc3 3, calc4 1 | 74 Corpse Explosion, 312 mon death sentry, 351 NihlathakCorpseExplosion |
| 56 | 3 | nec | — | nec 3 | Param1 3, Param2 3, Param3 3, Param4 3, Param5 2, Param6 2, Param8 3 | calc1 3 | 75 Clay Golem, 85 BloodGolem, 94 FireGolem |
| 57 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 90 IronGolem |
| 58 | 1 | nec | — | nec 1 | Param1 1, Param3 1, Param4 1, Param5 1 | calc1 1, calc2 1 | 95 Revive |
| 59 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 86 Attract |
| 60 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param8 1 | calc1 1, calc2 1 | 78 Bone Wall |
| 61 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 81 Confuse |
| 62 | 1 | nec | — | nec 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 88 Bone Prison |
| 63 | 1 | nec | — | nec 1 | Param8 1 | — | 83 Poison Explosion |
| 64 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param7 1, Param8 1 | calc1 1, calc2 1 | 96 Sacrifice |
| 65 | 17 | pal | A | pal 14, monster 3 | Param1 17, Param2 17, Param3 16, Param4 16, Param5 10, Param6 10, Param8 1 | — | 98 Might, 99 Prayer, 100 Resist Fire, 103 Thorns, 104 Defiance, 105 Resist Cold, 108 Blessed Aim, 109 Cleansing, 110 Resist Lightning, 113 Concentration, 115 Vigor, 120 Meditation, 122 Fanaticism, 125 Salvation, 296 Barbs Aura, 297 Wolverine Aura, 298 Oak Sage Aura |
| 66 | 4 | pal | A | pal 4 | Param1 4, Param2 4, Param3 2, Param4 2, Param5 4, Param6 3, Param7 2, Param8 3 | — | 102 Holy Fire, 118 Holy Shock, 119 Sanctuary, 123 Conviction |
| 67 | 2 | pal | — | pal 1, monster 1 | Param1 2, Param2 1, Param3 2, Param4 2, Param5 1, Param6 1, Param8 1 | calc1 1 | 107 Charge, 352 SerpentCharge |
| 68 | 5 | bar | — | bar 5 | Param1 5, Param2 5, Param3 3, Param4 3, Param5 1, Param6 1, Param8 4 | — | 138 Shout, 146 Battle Cry, 149 Battle Orders, 154 War Cry, 155 Battle Command |
| 69 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 131 Find Potion |
| 70 | 1 | bar | — | bar 1 | Param1 1, Param5 1, Param8 1 | calc1 1, calc3 1 | 133 Double Swing |
| 71 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 137 Taunt |
| 72 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 142 Find Item |
| 73 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | — | 112 Blessed Hammer |
| 74 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param8 1 | calc1 1 | 140 Double Throw |
| 75 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 150 Grim Ward |
| 76 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1 | calc1 1 | 151 Whirlwind |
| 77 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 132 Leap |
| 78 | 1 | bar | — | bar 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | calc1 1 | 143 Leap Attack |
| 79 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 116 Conversion |
| 80 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | calc1 1, calc2 1, calc4 1 | 121 Fist of the Heavens |
| 81 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1, Param8 1 | — | 114 Holy Freeze |
| 82 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 124 Redemption |
| 83 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 156 Fire Hit |
| 84 | 1 | monster | — | monster 1 | — | calc1 1 | 159 MaggotEgg |
| 85 | 2 | monster | — | monster 2 | — | — | 157 UnHolyBolt, 160 ShamanFire |
| 86 | 1 | monster | — | monster 1 | — | calc1 1 | 162 MagottDown |
| 87 | 1 | monster | — | monster 1 | — | — | 163 MagottLay |
| 88 | 1 | monster | — | monster 1 | — | — | 164 AndrialSpray |
| 89 | 1 | monster | — | monster 1 | — | calc1 1 | 165 Jump |
| 90 | 1 | monster | — | monster 1 | — | calc1 1, calc2 1 | 166 Swarm Move |
| 91 | 2 | monster | — | monster 2 | — | — | 167 Nest, 320 EvilHutSpawner |
| 92 | 1 | monster | — | monster 1 | — | — | 168 Quick Strike |
| 93 | 1 | monster | — | monster 1 | — | — | 172 GargoyleTrap |
| 94 | 1 | monster | — | monster 1 | — | — | 176 Submerge |
| 95 | 5 | monster | — | monster 5 | Param1 5, Param3 1, Param8 1 | calc1 1, calc2 5, calc3 5, calc4 1 | 178 FetishInferno, 311 mon inferno sentry, 317 Baal Inferno, 319 MegademonInferno, 323 Horror Arctic Blast |
| 96 | 2 | monster | — | monster 2 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 179 ZakarumHeal, 182 Bestow |
| 97 | 2 | monster | — | monster 2 | — | — | 181 Resurrect, 327 Resurrect2 |
| 98 | 4 | monster | — | monster 4 | — | — | 184 MonTeleport, 292 Teleport 2, 329 Baal Teleport, 331 Baal Clone Teleport |
| 99 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 192 PrimePoisonNova |
| 100 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 194 DiabCold |
| 101 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 196 FingerMageSpider |
| 102 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1 | 197 DiabWall |
| 103 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 198 DiabRun |
| 104 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | — | 199 DiabPrison |
| 105 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 203 DesertTurret |
| 106 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | — | 204 ArcaneTower |
| 107 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1, calc3 1 | 206 Mosquito |
| 108 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 214 RegurgitatorEat |
| 109 | 2 | monster | — | monster 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 1, Param6 1 | — | 215 MonFrenzy, 328 BloodLordFrenzy |
| 110 | 3 | monster | — | monster 3 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | — | 183 MissileSkill1, 202 HireableMissile, 336 RogueMissile |
| 111 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | — | 177 FetishAura |
| 112 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param7 1 | — | 212 MonCurseCast |
| 113 | 4 | item | — | item 4 | Param1 4, Param2 4, Param3 4, Param4 4, Param5 4, Param6 4 | — | 217 Scroll of Identify, 218 Book of Identify, 219 Scroll of Townportal, 220 Book of Townportal |
| 114 | 1 | dru | A | dru 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1, calc2 1 | 221 Raven |
| 115 | 3 | dru | — | dru 3 | Param1 3, Param2 3, Param3 3, Param4 3, Param5 3, Param6 3 | calc1 3, calc2 3 | 222 Plague Poppy, 231 Cycle of Life, 241 Vines |
| 116 | 3 | dru | — | dru 2, monster 1 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 2, Param6 1 | — | 223 Wearwolf, 228 Wearbear, 350 Delerium Change |
| 117 | 1 | dru | A | dru 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1, Param8 1 | calc1 1 | 225 Firestorm |
| 118 | 2 | dru | — | dru 2 | Param1 2, Param2 2, Param8 2 | calc1 2, calc4 1 | 240 Twister, 245 Tornado |
| 119 | 6 | dru | — | dru 6 | Param1 6, Param2 6, Param3 5, Param4 5, Param5 4, Param6 4, Param7 6, Param8 6 | calc1 6, calc2 6 | 226 Oak Sage, 227 Summon Spirit Wolf, 236 Heart of Wolverine, 237 Summon Fenris, 246 Spirit of Barbs, 247 Summon Grizzly |
| 120 | 2 | dru | — | dru 2 | Param1 1, Param2 1, Param3 2, Param4 2, Param5 2, Param6 2, Param7 2, Param8 2 | calc1 2, calc2 2 | 232 Feral Rage, 233 Maul |
| 121 | 1 | dru | — | dru 1 | Param8 1 | — | 238 Rabies |
| 122 | 1 | dru | — | dru 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1 | calc1 1, calc2 1, calc3 1 | 242 Hunger |
| 123 | 1 | dru | — | dru 1 | Param1 1, Param2 1, Param7 1, Param8 1 | calc4 1 | 244 Volcano |
| 124 | 3 | dru | — | dru 2, monster 1 | Param1 3, Param2 3, Param3 3, Param4 3, Param7 2, Param8 2 | — | 249 Armageddon, 250 Hurricane, 349 Diablogeddon |
| 125 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param4 1, Param8 1 | calc4 1 | 281 Wake Of Destruction Sentry |
| 126 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 282 Imp Inferno |
| 127 | 1 | monster | — | monster 1 | Param1 1 | calc1 1 | 289 Suck Blood |
| 128 | 1 | monster | — | monster 1 | Param1 1, Param2 1 | calc1 1 | 290 Cry Help |
| 129 | 1 | monster | — | monster 1 | — | — | 330 Imp Teleport |
| 130 | 1 | monster | — | monster 1 | Param1 1, Param2 1 | calc1 1, calc4 1 | 294 Vine Attack |
| 131 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1, Param6 1 | calc1 1 | 295 Overseer Whip |
| 132 | 1 | monster | — | monster 1 | — | calc1 1 | 299 Imp Fire Missile |
| 133 | 1 | monster | — | monster 1 | — | — | 300 Impregnate |
| 134 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1 | — | 301 Siege Beast Stomp |
| 135 | 1 | monster | — | monster 1 | — | — | 302 MinionSpawner |
| 136 | 1 | monster | — | monster 1 | — | calc1 1 | 308 DeathMaul |
| 137 | 1 | monster | — | monster 1 | Param1 1, Param2 1 | — | 314 fenris rage |
| 139 | 1 | monster | — | monster 1 | — | — | 318 Baal Cold Missiles |
| 140 | 1 | monster | — | monster 1 | — | — | 315 Baal Tentacle |
| 141 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1, Param5 1 | — | 285 Baal Corpse Explode |
| 143 | 2 | ass | A | ass 2 | Param1 2, Param2 2, Param3 2, Param4 2, Param5 1, Param6 1, Param7 1, Param8 1 | calc1 2, prgcalc2 2, prgcalc3 2 | `srvprgfunc`: 259 Fists of Fire, 280 Royal Strike |
| 144 | 1 | sor | — | sor 1 | Param1 1, Param2 1, Param8 1 | — | 62 Hydra |
| 145 | 0 | dru | — | dru 1 | — | — | States `srvactivefunc`: 144 hurricane (the `aurastate` of 250 Hurricane) |
| 146 | 0 | dru | — | dru 1, monster 1 | — | — | States `srvactivefunc`: 145 armageddon (the `aurastate` of 249 Armageddon, 349 Diablogeddon) |
| 147 | 0 | monster | — | monster 1 | — | — | States `srvactivefunc`: 143 attached (the `aurastate` of 330 Imp Teleport) |
| 148 | 1 | monster | — | monster 1 | — | — | 335 DoomKnightMissile |
| 149 | 1 | monster | — | monster 1 | — | — | 338 NecromageMissile |
| 150 | 1 | pal | — | pal 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc1 1, calc2 1 | 97 Smite |
| 151 | 1 | item | — | — | Param1 1, Param3 1, Param4 1, Param5 1, Param8 1 | calc1 1 | `ItemEffect`: 53 Chain Lightning |
| 152 | 1 | monster | — | monster 1 | Param1 1, Param2 1, Param3 1, Param4 1 | calc2 1, calc3 1 | 193 DiabLight |

## Timing (plan 0050 Phase 0)

The animation, sequence and delay columns, by the layout of [§ Animation, range and delay](#animation-range-and-delay)
(values from the `.bin` over the 357 records; blanks from the `.txt`;
`python3 -I tools/anim_survey.py skills workspace/merged`, survey keys `sk_*`):

| Column | `.bin` field | Observed | Meaning | Tag |
|---|---|---|---|---|
| `anim` | `+0x010` u8, `plrmode` row | 334 set: `SC` 141, `SQ` 116, `A1` 48, `S2` 9, `S1` 6, `TH` 5, `S3` 4, `KK` 3, `A2` 1, `S4` 1; 23 blank store 255 | the player mode of the skill | [C] layout; `[I]` as in [§ Animation, range and delay](#animation-range-and-delay) |
| `seqtrans` | `+0x012` u8, `plrmode` row | 334 set: `SC` 143, `SQ` 98, `A1` 64, then as `anim`; 23 blank store 255 | the mode of a sequence's transitions (name) | [C] layout; `[L]` |
| `monanim` | `+0x011` u8, `monmode` row | 357 set: `xx` 214, `A1` 41, `SC` 29, `S1` 29, `S2` 24, `A2` 11, `S3` 8, `NU` 1 | the monster mode of the skill | [C] layout; `[L]` |
| `seqnum` | `+0x013` u8 | 1..41 in 34 rows (23 distinct), blank 0 | the player sequence's number | [C] layout; `[I]` the index into the code's player sequence tables (below) |
| `seqinput` | `+0x016` u16 | 8, 10, 10, 12 in 4 rows (Charge, Inferno, Arctic Blast, Blade Fury), blank 0 | the sequence's input frame (name) | [C] layout; `[L]` |
| `delay` | `+0x190` s32 calc offset | 23 rows, all constants: 15 (3), 25 (6), 30, 35, 40, 45, 50 (3), 100 (2), 150 (5) | the cooldown in frames | [C] layout; `[I]` the `skilldelay` state ([§ Animation, range and delay](#animation-range-and-delay)) |
| `perdelay` | `+0x128` s32 calc offset | 22 rows: 50 in the 20 Paladin auras, `par3` (Blade Shield), `(100-dm56) * par4/100 + par3` (Thunder Storm) | the period of a periodic skill in frames | [C] layout; `[I]` `SKILLS_NextPeriodicFrame` ([§ Columns](#columns)) |

- `[C]` **`anim` `SQ` and `seqnum`.** Of the 116 rows with `anim` `SQ`, 28 have a `seqnum` (1..41, 19 values) and 88
  have none; those 88 all have a blank `charclass` (monster skills), with `monanim` `xx` 25, `S1` 22, `A1` 20, `SC` 8,
  `A2` 5, `S2` 5, `S3` 3. A monster's sequence comes from its MonStats `Sk<k>mode` cell ([MonSeq](MonSeq.md)), not from
  the Skills row. The 28 numbered rows include the class skills Jab (1), Charge (4), Inferno (6),
  Impale (8), Whirlwind (10), Double Swing and Frenzy (11), Lightning and Chain Lightning (12), Leap (13), Leap Attack
  (14), Double Throw (15), the four Assassin charge-ups (16), Arctic Blast (18), Dragon Flight (21) and Blade Fury (23),
  and monster rows such as DiabRun (22), DesertTurret (26) and QueenDeath (41). Six rows have a `seqnum` with another
  `anim`: Fend (`A1`, 9), Sacrifice (`A1`, 2), Conviction (blank `anim`, 5), Wearwolf and Wearbear (`SC`, 22) and
  Dragon Talon (`KK`, 19) (`sk_seqnum_nonsq=6`).
- `[I]` **`seqnum` indexes a table in the code, not `monseq`** ([anim/0001 § 5](../findings/anim/0001-modes-frames.md#5-sequences)): a player's sequence
  (mode 18) is `g_PlrSeqTables[seqnum]` (24 entries, 0 null; 14 weapon-class columns of 12 bytes), read with no bound
  test; an index < 1 means no sequence. A monster's comes from its MonStats `Sk<k>mode` ordinal into `monseq`, not
  from this column. (fn:sub_00643D00_SkillSeqIndex@0x00643D00, fn:sub_00663310_UnitSeqRecord@0x00663310,
  data:g_PlrSeqTables@0x007483B8, tbl:Skills.txt:seqnum) `[C]` The rows above 23 (DesertTurret 26, QueenDeath 41 and
  the others) have no `charclass`; the values 22 for DiabRun and for the two shape-shifts, and 18 for Arctic Blast and
  two monster rows, show the number is shared across unrelated skills.
- `[I]` **`durability`** (`+0x006` bit 2): at a player mode's end (`PlayerModeEnd`), modes 7, 8, 11 or a used skill
  with this bit refresh the hands (`sub_00580310_HandsRefresh`) before the next mode
  ([anim/0001 § 9](../findings/anim/0001-modes-frames.md#9-player-modes), fn:sub_00581020_PlayerModeEnd@0x00581020, tbl:Skills.txt:durability).
- `[I]` **`interrupt`** (`+0x007` bit 7): `sub_0057EEC0_PlayerModeAllowed`, for a used skill with this bit under state
  42 `concentration`, draws `Range(player unit seed, 100)` against stat 164 `skill_concentration` of that state's list
  and refuses the interrupt below it ([anim/0001 § 11](../findings/anim/0001-modes-frames.md#11-draws-seeds-and-the-chaining-reading-adr-0014),
  0x0057EF7C, tbl:Skills.txt:interrupt). How the gate is used is plan 0050 P1.3.
- `[C]` **No rate column.** No Skills column names an attack, cast or hit-recovery rate; the rate stats reach a skill
  through its `aurastat*`/`passivestat*` columns: 33 cells name `velocitypercent`, `attackrate`, `other_animrate` or
  `item_slow` ([ItemStatCost § Timing](ItemStatCost.md#timing-plan-0050-phase-0), `rate_stat_skill_cells`).

## Open questions

- `[L]` How the per-class lists at `DataTables+0xBA4..+0xBAC` are built at load (their builder is not read). What
  `firstSkill(class)` returns is settled for classes 1–6 in [§ Class blocks](#class-blocks); class 0 was not logged.
- `[L]` Whether `Id` is a u16 or a u32 (`+0x002` is 0 in every record).
- `[L]` Every meaning not tagged in the tables, and what each numbered function reads of its rows (the parameters,
  calcs, missiles and states of § [Function index](#function-index-plan-0046-phase-0)). Owner: reverser, plan
  [0046](../plans/0046-skills-function-catalogue.md) Phase 1, by its batches.
- `[L]` `manashift` is laid out as a u16 (`+0x188`, values 2..8) and read as a byte by the formula variables; whether
  any reader takes the high byte (`+0x189`, 0 in every record).
