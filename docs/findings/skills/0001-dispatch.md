# 0001 — Skill dispatch: the request, the start checks, the start and do functions, the skill packet

> **Subsystem:** skills/dispatch
> **Question:** when a unit uses a skill, which checks let it start, which function runs on which frame, what does it
> cost, and how does a skill hit build its damage packet (players and monsters, item-granted skills, ammunition and wear)?
> **Date:** 2026-10-20   **Plan:** 0045 (Phase 1, batch P1.1)   **Status:** open (P1.2 missiles and P1.3 handlers,
> summons, re-seeds and tier A follow)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p45r`) and objdump. The counts and
instruction windows below come from `tools/skills_dispatch_scan.py` (sha256 `a26f5993…`), kept under
`workspace/logs/skills/` (`p45r-manifest.sha256`: `dispatch-scan.txt` `2c5c1efd…`, `dispatch-rows.txt` `844d186d…`).
Skills columns are named as in [Skills](../../tables/Skills.md); offsets are record offsets.

## Answer (summary)

- [I] **Request.** Client packets 0x05–0x11 (left skill 0x05–0x0A, right skill 0x0C–0x11; at a location, at a unit
  with or without the walk-to-range step, and a second copy of each that re-reads the packet; 0x0B does nothing) are handled by `PLRMSG_SkillAtXY` and `PLRMSG_SkillAtUnit`. Each
  accepted request adds 1 to the player's stat 328 (`pierce_idx`), runs `SKILLS_CanUse` and, on code 0, starts the
  skill entry's mode with `sub_005809D0_PlayerModeCmd` or `PLAYER_ModeCmdUnit`; a melee-range skill out of reach
  walks to the target instead. (fn:PLRMSG_SkillAtXY@0x00549AD0, fn:PLRMSG_SkillAtUnit@0x00549BA0,
  data:g_SrvPacketTable@0x006E0D18)
- [I] **Start checks** come in three layers: `SKILLS_CanUse` at the request (codes 3 not in game, 7 level 0, 6 aura,
  5 passive, 2 weapon or ammunition or item charges, 1 mana or `startmana`, 4 `restrict`, 8 delay), the target and
  item-charge checks of `SKILLS_StartUsedSkill` at the mode start, and `SKILLS_SrvStart` (room, mana, `InTown`,
  `LineOfSight`), which then calls the `srvstfunc` entry of `g_SkillStartFuncs` (`0x00732140`, bound 0x5B).
  (fn:SKILLS_CanUse@0x00647960, fn:SKILLS_StartUsedSkill@0x0056FAF0, fn:SKILLS_SrvStart@0x0056F640)
- [I] **The do function** (`srvdofunc`, `g_SkillDoFuncs` `0x007322B0`, bound 0xBF) runs from the mode's frame
  function on a frame whose event code is 1 or 2 (players) or on the monster's action frame, once per mode: bit 6
  of `Unit+0xC4` marks the action as done. `SKILLS_SrvDo` also creates the skill's `srvmissile`, pays the cost when
  the start did not, uses ammunition (`decquant`) and sets the delay state. (fn:SKILLS_SrvDo@0x0056F7F0,
  fn:SKILLS_DoUsedSkill@0x0056FC50, fn:sub_00580460_PlrModeSkillFrame@0x00580460)
- [C] Every stock Skills row's `srvstfunc`, `srvdofunc`, `srvprgfunc1..3` and `ItemEffect` (> 1) indexes a non-null
  entry of those two tables: 357 rows, 0 out of table; 64 non-null start entries among ids 1..65 (id 30 null, and
  ids 0 and 66..0x5A null) and 152 non-null do entries (ids 1..152; 53, 138, 142, 145, 146 and 147 used by no stock
  row). The `[C]` is the data join (the tables' bytes read by Ghidra, by the scan and by the review's own PE read, against
  every Skills row); which column indexes which table, and the bounds `0x5B`/`0xBF` (`0x0056F75D`, `0x0056F911`), are
  the code readings of §§ 4, 6 and 12, `[I]`. (data:g_SkillStartFuncs@0x00732140,
  data:g_SkillDoFuncs@0x007322B0, tbl:Skills.txt:srvstfunc, tbl:Skills.txt:srvdofunc)
- [I] **Mana cost** = `(lvlmana · max(lvl − 1, 0) + mana) << manashift` in 1/256 mana; the payment floors it at
  `minmana · 256`, the checks do not. Under `blood_mana` (state 114) it is paid from life. The payment's result is
  ignored: a cost above the unit's mana is not taken and the skill still runs. An item skill uses a charge instead.
  (fn:SKILLS_PayCost@0x0056BFE0, 0x0056F7AF, 0x0056FA7F, fn:SKILLS_ManaOk@0x00647540)
- [I] **Delay**: a player whose skill has `delay` > 0 gets the timed state `skilldelay` (121) until `frame + delay`;
  while it lasts `SKILLS_CanUse` refuses every skill whose own `delay` is ≥ 1, and no other.
  (fn:SKILLS_SetDelayState@0x0056EF90, fn:SKILLS_DelayOk@0x006478F0)
- [I] **The skill packet** of a skill melee hit (start functions 6, 7, 10, 16, 29, 32, 39, 56, 57 and do functions 7,
  13, 67, 150): `COMBAT_MeleeHitTest` with `SKILLS_GetToHit`, then on a hit `ResultFlags`, `HitFlags`, `HitClass`,
  `edPct = calc1`, the conversion `+0x65 = EType`, `+0x68 = calc4` (when calc4 > 0), the elemental roll, and
  `COMBAT_ResolveAndQueue` with SrcDam (0 read as 128). This is the writer of the conversion fields combat/0001 asked
  for. Many of these hits are built in the **start** function and delivered by the do function on the action frame.
  (fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0, 0x005D7FA8, fn:SKILL_MeleeDeliverDo@0x0056F1F0)
- [I] **Correction to combat/0001.** The progressive finisher saves the attacker's seed, calls `RNG_Step`, and
  restores the seed: the step is a peek and the attacker's seed is unchanged by it; the peeked value goes to
  `0x00571AA0` as an argument. (0x005D5368–0x005D538C, fn:COMBAT_PrgFinisher@0x005D5220)
- [I] **Monster skill use**: `sub_005DEAD0_MonAiUseSkill` sets the used skill and `Unit+0xC4` bit 6 and calls
  `sub_005A7C20_MonSetMode`; the mode start `sub_005A75C0_MonModeStartSkill` runs `SKILLS_StartUsedSkill`, the action
  frame `sub_005A7670_MonAttackFrame` runs `SKILLS_DoUsedSkill`. `sub_005A4F50_MonAttackStats` has 6 callers; for the
  four summon classes with a MonStats `SkillDamage` it adds the owner's skill damage and to-hit.
  (fn:sub_005A7670_MonAttackFrame@0x005A7670, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050)

## Leads used

No community document was opened for P1.1–P1.3. *Phase 1b (plan 0045), 2026-10-20:* the pages below were fetched and
read in that session (ADR-0007), after the batch's sections were written, and none shows code. One verdict per compared
claim. The verdict words are evidence-rules' (`held`, `held with refinement`, `contradicted`, `not covered`). A
claim from another game version that differs from 1.14d for that reason only would be marked *version-different* in
its detail. None is marked: no source says its claim is version-specific, and none of their versions can be checked
here. Two sources are Resurrected-era (src:d2dfg-blizzard, src:purediablo-piercing), so a contradiction from them
may be a Resurrected change; the Phase 2 case settles 1.14d only. Agreement adds nothing to a tag. The quick objdump re-reads behind a contradiction or a gap are `tools/skills_crosscheck_reread.py`
(sha256 `8361a4c1…`), kept under `workspace/logs/skills/` (`p45b-manifest.sha256`: `p45b-reread.txt` `427ca8d7…`, the
code windows R1–R7; `p45b-rows.txt` `cbf9c64a…`, the stock-row values compared).

- [L] src:d2dfg-blizzard: the mana cost is `mana` at level 1 plus `lvlmana` per level gained, in 256ths shifted by
  `manashift` (8 = not shifted). **held**
  Detail: `(lvlmana · max(lvl − 1, 0) + mana) << manashift` in 1/256 mana (§ 7).
- [L] src:arreat-summit-skill-trees: Teleport costs 24 mana at level 1 and one less per level (5 at level 20); Charged
  Bolt 3, then +0.5 per level. **held with refinement**
  Detail: § 7's formula on the rows gives both tables (`p45b-rows.txt` `MANA`), except Charged Bolt's level-20 cell
  (page 12, formula 12.5); the cost is kept in 1/256 mana, so half points are real.
- [L] src:d2dfg-blizzard: `minmana` keeps a falling cost from going below it. **held with refinement**
  Detail: the floor binds the payment only; the checks use the unfloored cost, and a failed payment is ignored (§ 7,
  the P1.1 review's Phase 2 case).
- [L] src:d2dfg-blizzard: `startmana` is the mana needed to start, used by some start functions (Inferno 11, Blade
  Fury 26). **held with refinement**
  Detail: `SKILLS_StartManaOk` tests it in `SKILLS_CanUse` for any row, except in state 12; three stock rows set it (§ 2).
- [L] src:arreat-summit-skill-basics: a skill cannot be used without mana, without its required item, during a casting
  delay, or in town. **held with refinement**
  Detail: codes 1, 2 and 8 of `SKILLS_CanUse` at the request; the town test is `SKILLS_SrvStart`'s `InTown`, at the
  start (§§ 2, 4).
- [L] src:d2dfg-blizzard: a row with `InTown` 0 cannot be used in town. **held**
- [L] src:arreat-summit-casting-delays: after casting a delayed spell it cannot be re-cast for a while, a spell with
  no delay can be used meanwhile, and delayed spells are "connected". **held with refinement**
  Detail: state 121 refuses every skill whose own `delay` is ≥ 1, not only the one cast, and no other (§ 8).
- [L] src:arreat-summit-casting-delays: the 23 skills with a delay and their delays in seconds. **held**
  Detail: the 23 stock `delay` rows are the same 23 skills, and each `delay` (frames) is the page's seconds × 25
  (`p45b-rows.txt` `SKILLS delay`); state 121 lasts `delay` frames (§ 8).
- [L] src:arreat-summit-skill-basics: item skill bonuses do not add to synergies. **held**
  Detail: the synergy calcs read `skill('…'.blvl)` (§ 11; the `blvl` code is data/0005's reading).
- [L] src:d2dfg-blizzard: `DmgSymPerCalc`, `EDmgSymPerCalc` and `ELenSymPerCalc` are percentage increases.
  **held with refinement**
  Detail: `x += MulDiv(x, calc, 100)` on min and max apart (the elemental min only when `x > 256` or `EMinLev1` ≠ 0),
  after the level bands; after the shift for skills, before it for missiles (§ 11, data/0005 § 7).
- [L] src:d2dfg-blizzard: `SrcDam` is the weapon damage share in 128ths; `HitShift` scales damage in 256ths
  (8 = 256/256). **held**
- [L] src:d2dfg-blizzard: a `Kick` row computes its physical damage from Strength and Dexterity (a monster's level).
  **held with refinement**
  Detail: `max(x, 1) / 4 << 8` with `x` = `str + dex − 20` for a player, `3 · level` for other units (§ 11).
- [L] src:d2dfg-blizzard: `periodic` and `aura` rows run every `perdelay` frames, minimum 5. **held with refinement**
  Detail: 5 when the calc gives less than 6, on the grid `((frame − 1 + p) / p) · p + 1` (§ 9).
- [L] src:d2dfg-blizzard: with `immediate` the function runs at once when the periodic skill starts. **held**
  Detail: aura select and item auras run `SKILLS_SrvDo` at once (§§ 9, 10).
- [L] src:d2dfg-blizzard: a `passive` row runs no server do function. **held with refinement**
  Detail: `SKILLS_CanUse` refuses it with code 5 at the request (§ 2).
- [L] src:d2dfg-blizzard: `restrict` ties the skill to the States `restrict` column. **held**
  Detail: code 4 of `SKILLS_CanUse` (§ 2).
- [L] src:d2dfg-blizzard: `decquant` uses ammunition each time the server do function runs. **held with refinement**
  Detail: only on `SKILLS_SrvDo`'s paying path (`pay` set); an item cast never uses it (§§ 6, 10, 14).
- [L] src:d2dfg-blizzard: `ItemEffect` is the do function an item trigger runs; `ItemCheckStart` 1 runs the start
  function first. **held with refinement**
  Detail: `ItemEffect` replaces the do function only when > 1 and the effect flag is set; a failed start refuses the
  cast (§ 10).
- [L] src:d2dfg-blizzard: `ItemTarget` 0 the attacker, 1 the caster, 2 a random location within 20 (collision
  tested), 3 a random nearby corpse, 4 the attacker or a previous one. **not covered**
  Detail: § 10 names the helpers without reading them. Re-read for 2 (R5): `0x005FD850` steps the seed at `+0x20` of
  the unit it is given twice per try inline, adds `low % 40 − 20` to x and to y, and tries at most 10 times until
  `0x0064D870` returns 0; so an item Teleport (the one stock `ItemTarget` 2 row) draws 2 to 20 steps that
  [skills/0003 § 2](0003-handlers.md#2-item-event-casts) does not count (its "no draw" sentence). The unit's role (caster or target)
  and 3's corpse pick are unfollowed: a gap, in *Open questions*.
- [L] src:d2dfg-blizzard: `prgstack` 1 runs every `srvprgfunc` up to the charge count, 0 only the count's own.
  **held** (§ 12)
- [L] src:arreat-summit-skill-trees: martial-arts charges build up to three, last for a time limit and are released
  by a normal attack or a finishing move. **held with refinement**
  Detail: the cap 3 and the `auralencalc` timed list (§ 12). The finisher has **six** direct call sites (R6):
  `SKILL_AttackDo` (`0x0056F1CE`), named in § 12, and five in finishing-move functions (R7): start function 25 (Dragon
  Claw, two sites) and do functions 42 (Dragon Talon), 50 (Dragon Tail), 52 (Dragon Flight); those are plan 0046's.
- [L] src:arreat-summit-skill-trees: Phoenix Strike releases only the active charge. **held**
  Detail: Royal Strike's row has no `prgstack`, so only `srvprgfunc n` runs (§ 12, `p45b-rows.txt` `prgstack`).
- [L] src:arreat-summit-skill-trees: Impale raises the chance that the weapon loses durability. **held with refinement**
  Detail: `calc2` chance, `calc3` amount, one draw on the unit's seed, a break at 0 (§ 14).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00549D00`…`0x0054A200` | `sub_00549D00_Pkt05LeftSkillXY` … `sub_0054A200_Pkt11RightSkillUnitAlt2` | client packets 0x05–0x11 (table below) | I |
| `0x005496F0` | `sub_005496F0_PktReadXY` | reads the 5-byte location form, validates the point | I |
| `0x00549830` | `sub_00549830_PktReadUnit` | reads the 9-byte unit form (type ≤ 5, guid), validates the unit | I |
| `0x00549AD0` | `PLRMSG_SkillAtXY` | request at a location: `CanUse`, mode command | I |
| `0x00549BA0` | `PLRMSG_SkillAtUnit` | request at a unit: `CanUse`, range walk, mode command | I |
| `0x00549960` | `sub_00549960_DualAttackAlternate` | Attack with two weapons alternates with Left Hand Swing | I |
| `0x00549A60` | `sub_00549A60_NoManaMsg` | code-1 refusal: a message to the client | I |
| `0x00647960` | `SKILLS_CanUse` | the request checks, codes 0–8 | I |
| `0x00647640` | `sub_00647640_SkillAmmoOk` | Throw / Left Hand Throw / Left Hand Swing items; scroll uses | I |
| `0x00643F80` | `SKILLS_WeaponTypeOk` | `itypea*`/`etypea*` against the two hands | I |
| `0x00647540` | `SKILLS_ManaOk` | mana (or life under state 114, or charges) against the cost | I |
| `0x00644060` | `SKILLS_RestrictOk` | `restrict` 0/1/2 with `State1..3` | I |
| `0x006440F0` | `SKILLS_StartManaOk` | `startmana`, except in state 12 | I |
| `0x00647840` | `SKILLS_ItemChargesOk` | the granting item's stat 204 charges | I |
| `0x006478F0` | `SKILLS_DelayOk` | state 121 against the skill's `delay` | I |
| `0x00645460` | `SKILLS_GetRangeType` | `range`, `both` resolved by the weapon | I |
| `0x00580A70` | `PLAYER_ModeCmdUnit` | `sub_005809D0_PlayerModeCmd` with a target unit | I |
| `0x0057FE90`, `0x0057FEF0` | `sub_0057FE90_PlrModeStartSkillXY`, `sub_0057FEF0_PlrModeStartSkillUnit` | player skill-mode starts | I |
| `0x00580460` | `sub_00580460_PlrModeSkillFrame` | player skill-mode frame function | I |
| `0x005A75C0` | `sub_005A75C0_MonModeStartSkill` | monster mode start (A1, A2, SC, S1, S2, …) | I |
| `0x005A8670` | `sub_005A8670_MonSeqFrame` | monster sequence-mode (14) frame function | I |
| `0x0056FAF0` | `SKILLS_StartUsedSkill` | target and charge checks, `SrvStart` | I |
| `0x0056CC60` | `SKILLS_TargetCheck` | `TargetableOnly`, `TargetCorpse` | I |
| `0x0056F640` | `SKILLS_SrvStart` | room, mana, town, line of sight, `srvstfunc`, cost | I |
| `0x0056FC50` | `SKILLS_DoUsedSkill` | `SrvDo` of the used skill, then the periodic queue | I |
| `0x0056F7F0` | `SKILLS_SrvDo` | `srvdofunc`, `srvmissile`, cost, ammunition, delay | I |
| `0x0056C160` | `SKILLS_SrvManaCheck` | the server-side mana test | I |
| `0x0056BFE0` | `SKILLS_PayCost` | mana, blood-mana life or a charge | I |
| `0x005D2B60` | `sub_005D2B60_BloodManaPay` | the life payment under state 114 | I |
| `0x0056EF90` | `SKILLS_SetDelayState` | state 121 until `frame + delay` | I |
| `0x0056F020` | `sub_0056F020_SkillDelayFromCalc` | evaluates `delay` and sets the state | I |
| `0x0056CDA0` | `SKILLS_QueuePeriodic` | unit event 8 on the `perdelay` grid | I |
| `0x0056D2C0` | `SKILLS_GetTargetXY` | the target unit's position or the path target | I |
| `0x00645950` | `SKILLS_LineOfSightOk` | `COLL_LineTest` from the target to the unit | I |
| `0x0056D790` | `sub_0056D790_StateDoFunc` | unit event 5: the do function named by the aura state's States record | I |
| `0x0056D810` | `sub_0056D810_CallDoFunc` | calls a do-table entry by number (two missile callers) | I |
| `0x005FDA80` | `ITEMSKILL_Cast` | item-event cast (`ItemEffect`, `ItemTarget`, `ItemCheckStart`) | I |
| `0x0056F1F0` | `SKILL_MeleeDeliverDo` | `srvdofunc` 2: overlay, target state, self state, delivery | I |
| `0x005D7EA0` | `sub_005D7EA0_SkillSt32Hit` | `srvstfunc` 32 (Bash, Stun, Concentrate, Conversion, BearSmite) | I |
| `0x005DA940` | `sub_005DA940_SkillSt06Hit` | `srvstfunc` 6 (Power Strike, Charged Strike, …) | I |
| `0x005DAB40` | `sub_005DAB40_SkillSt07ImpaleHit` | `srvstfunc` 7 (Impale): hit, then weapon wear | I |
| `0x0056E520` | `sub_0056E520_SkillAttackRateList` | a plain stat list with stat 68 (attack rate) on the unit | I |
| `0x005C6CC0` | `SKILLS_ApplyAuraStats` | `aurastat1..6` with their calcs into a list | I |
| `0x0056C8E0` | `SKILLS_AddElemToPacket` | one element's damage and length into the packet | I |
| `0x00647BC0`, `0x00647D00` | `SKILLS_GetPhysMin`, `SKILLS_GetPhysMax` | the skill's physical min and max | I |
| `0x0056E050`, `0x0056E000` | `sub_0056E050_MonOwnerSkillDamage`, `sub_0056E000_SkillDamagePair` | MonStats `SkillDamage` | I |
| `0x005D3490` | `sub_005D3490_PrgChargeHitDo` | `srvdofunc` 34: hit, then a charge | I |
| `0x005D35D0` | `sub_005D35D0_PrgChargeHitDualDo` | `srvdofunc` 35: the dual-claw form of 34 | I |
| `0x005D3320` | `SKILLS_AddProgressiveCharge` | the charge state, its stat capped at 3 | I |
| `0x00650E70`, `0x00650E60` | `sub_00650E70_Copy64Out`, `sub_00650E60_Copy64In` | copy 8 bytes out and back (the finisher's seed save) | I |
| `0x00553540` | `UNIT_GetTargetUnit` | the unit's current target, 0 for itself | I |
| `0x00540E60` | `UNIT_CancelEvents` | removes queued unit events of a type (and parameter) | I |
| `0x0056ECB0`, `0x0056EE90` | `sub_0056ECB0_SkillMissileCreate`, `sub_0056EE90_SkillMissileCreateLob` | the `srvmissile` creation (P1.2) | I |
| `0x00620250`, `0x00620210` | `UNIT_GetUsedSkill`, `UNIT_SetUsedSkill` | `SkillList+0x10` | I |
| `0x00620190`, `0x006201D0` | `UNIT_GetLeftSkill`, `UNIT_GetRightSkill` | `SkillList+0x08`, `+0x0C` | I |
| `0x006439B0` | `sub_006439B0_SkillFindByOwner` | the entry with skill id `EDX` and owner item (−1 own) | I |
| `0x00643860` | `SKILLS_GetEntryMode` | `SkillEntry+0x08` | I |
| `0x00643B00` | `SKILLS_GetItemSkillInfo` | owner, id, level and charges of an item skill entry | I |
| `0x00732140` | `g_SkillStartFuncs` | `srvstfunc` table | C |
| `0x007322B0` | `g_SkillDoFuncs` | `srvdofunc` (and `srvprgfunc`, `ItemEffect`) table | C |
| `0x006E1740` | `g_PlayerModeStartFuncs` | per player mode {start at a location, start at a unit} | I |
| `0x00732C10` | `g_PlayerModeFrameFuncs` | per player mode frame function | I |

## Walkthrough

### 1. The request: client packets 0x05–0x11

`sub_0054D750_SrvPacketDispatch` indexes `g_SrvPacketTable` (`{handler, flag}` by packet id). The skill entries:

| Id | Handler | Skill | Target | Calls |
|---|---|---|---|---|
| 0x05 | `0x00549D00` | left | location | `PLRMSG_SkillAtXY` |
| 0x06 | `0x00549D80` | left | unit | `PLRMSG_SkillAtUnit(…, walk = 1)` |
| 0x07 | `0x00549E00` | left | unit | `PLRMSG_SkillAtUnit(…, walk = 0)` |
| 0x08, 0x09, 0x0A | `0x00549E80`, `0x00549EE0`, `0x00549F40` | left | as 0x05, 0x06, 0x07 | re-read the packet, then the handler of 0x05/0x06/0x07 |
| 0x0B | `0x00549FA0` | — | — | returns 0 for a length of 1, else 3; does nothing |
| 0x0C | `0x00549FC0` | right | location | `PLRMSG_SkillAtXY` |
| 0x0D, 0x0E | `0x0054A040`, `0x0054A0C0` | right | unit | `PLRMSG_SkillAtUnit(…, 1)`, `(…, 0)` |
| 0x0F, 0x10, 0x11 | `0x0054A140`, `0x0054A1A0`, `0x0054A200` | right | as 0x0C, 0x0D, 0x0E | as 0x08–0x0A |

- [I] The table is read by the dispatcher at `0x0054D772`–`0x0054D80C`; the handler addresses are in
  `dispatch-scan.txt` (`PKT` lines). (data:g_SrvPacketTable@0x006E0D18, fn:sub_0054D750_SrvPacketDispatch@0x0054D750)
- [I] Handler names: fn:sub_00549D00_Pkt05LeftSkillXY@0x00549D00, fn:sub_00549D80_Pkt06LeftSkillUnit@0x00549D80,
  fn:sub_00549E00_Pkt07LeftSkillUnitNoWalk@0x00549E00, fn:sub_00549E80_Pkt08LeftSkillXYAlt@0x00549E80,
  fn:sub_00549EE0_Pkt09LeftSkillUnitAlt@0x00549EE0, fn:sub_00549F40_Pkt0ALeftSkillUnitAlt2@0x00549F40,
  fn:sub_00549FA0_Pkt0BNoop@0x00549FA0, fn:sub_00549FC0_Pkt0CRightSkillXY@0x00549FC0,
  fn:sub_0054A040_Pkt0DRightSkillUnit@0x0054A040, fn:sub_0054A0C0_Pkt0ERightSkillUnitNoWalk@0x0054A0C0,
  fn:sub_0054A140_Pkt0FRightSkillXYAlt@0x0054A140, fn:sub_0054A1A0_Pkt10RightSkillUnitAlt@0x0054A1A0,
  fn:sub_0054A200_Pkt11RightSkillUnitAlt2@0x0054A200.
- [I] The location form is 5 bytes (`x` u16 at +1, `y` u16 at +3); `sub_005496F0_PktReadXY` refuses any other length
  (3) and validates the point (`0x00548EF0`); on a bad point it sends at most one reply per 25 frames
  (`PlayerData+0x168` holds the last frame). The unit form is 9 bytes (type u32 at +1, at most 5; guid u32 at +5),
  validated by `0x00548F80` (the unit exists, same act, `0x00548EF0` on its position).
  (fn:sub_005496F0_PktReadXY@0x005496F0, fn:sub_00549830_PktReadUnit@0x00549830)
- [I] A handler with no left (`SkillList+0x08`) or right (`+0x0C`) skill returns 3. Otherwise the plain and shift
  handlers add 1 to the player's base stat 328 (`pierce_idx`) **before** the checks, every request. (0x00549D50,
  struct:SkillList+0x08, tbl:ItemStatCost.txt:Stat)
- [I] `PLRMSG_SkillAtXY` (`EAX` = the skill entry): only when the player's mode is neither 0 (death) nor 17 (dead).
  With `UNIT_CanDualWield`, `sub_00549960_DualAttackAlternate` may swap the entry (below). `c = SKILLS_CanUse`; when
  `c` is 1, 2 or 4 and the skill has `AttackNoMana` (`+0x07` bit 4), the entry becomes the unit's own skill 0 (Attack)
  and `c` is recomputed. If the entry's mode (`SkillEntry+0x08`) is non-zero: `c = 0` →
  `sub_005809D0_PlayerModeCmd(entry, mode, x, y, force 0)`; `c = 1` → `sub_00549A60_NoManaMsg` (a message to the
  client); any other code does nothing. (fn:PLRMSG_SkillAtXY@0x00549AD0, 0x00549B20–0x00549B40)
- [I] `PLRMSG_SkillAtUnit` does the same `CanUse` and fallback, then requires `c = 0`, a mode, and either `TargetItem`
  (`+0x07` bit 3) or a target type 0, 1 or 3 (player, monster, missile). A target in state 143 (`attached`) is
  replaced by `0x00552FD0`'s unit. With `walk` = 1 and a target: `SKILLS_GetRangeType` 1 (h2h) and the target out of
  `sub_00622C40_InMeleeRange` → `0x00548A50` (a mode-3 run to the target through `PLAYER_ModeCmdUnit`, and the skill
  id kept by `0x00641F20`) instead of the skill. Otherwise `PLAYER_ModeCmdUnit(entry, mode, type, guid, 0)`.
  (fn:PLRMSG_SkillAtUnit@0x00549BA0, fn:SKILLS_GetRangeType@0x00645460)
- [I] `SKILLS_GetRangeType`: the `range` keyword (0 none, 1 h2h, 2 rng, 3 both); `both` gives 2 when `0x0064F460`
  (the unit has a missile weapon) is true, else 1, and 1 again for a player in a `meleeonly` state. The walk branch
  also tests the value 4, which no keyword gives. (fn:SKILLS_GetRangeType@0x00645460, tbl:Skills.txt:range)
- [I] **Dual-wield alternation.** For the entry of skill 0 (Attack) with an item in each hand (body locations 4 and 5,
  each a weapon, type 45, and neither failing `0x0062A4E0` nor of base type 38): when `SkillEntry+0x24` of the
  Attack entry is 0 the request uses the unit's skill 5 (Left Hand Swing) and sets `+0x24 = 5`; else it uses Attack
  and sets `+0x24 = 0`. (fn:sub_00549960_DualAttackAlternate@0x00549960, 0x005499F4–0x00549A30, struct:SkillEntry+0x24)

### 2. `SKILLS_CanUse` (16 call sites, 4 of them in the request handlers)

```c
// fn:SKILLS_CanUse@0x00647960 (unit, entry), trimmed
if (!rec || !(rec->b05 & 0x04 /*InGame*/))       return 3;
if (SKILLS_GetSkillLevel(unit, entry, 1) == 0)   return 7;
if (rec->b04 & 0x20 /*aura*/)                    return 6;
if (rec->b04 & 0x10 /*passive*/)                 return 5;
if (!sub_00647640_SkillAmmoOk(entry, unit))      return 2;
if (!SKILLS_WeaponTypeOk(entry, unit))           return 2;
if (!SKILLS_ManaOk(entry, unit))                 return 1;
if (!SKILLS_RestrictOk(entry, unit))             return 4;
if (!SKILLS_StartManaOk(entry, unit))            return 1;
if (!SKILLS_ItemChargesOk(unit, entry))          return 2;
return SKILLS_DelayOk(unit, entry) ? 0 : 8;
```

- [I] The order and codes are as above. All 357 stock rows have `InGame` set, so code 3 is
  only the null-record case on stock data. (fn:SKILLS_CanUse@0x00647960, tbl:Skills.txt:InGame)
- [I] `sub_00647640_SkillAmmoOk`: a `scroll` row (`+0x08` bit 4; the four identify and town-portal scrolls and books)
  needs `SkillEntry+0x30` > 0. Skill 2 (Throw): the thrown item in the hand (`0x0063C9B0`; with dual wield the other
  hand's item when the first is empty) must be throwable (`sub_0062BA80_ItemTypeThrowable`) and the result is its stat
  125 (`item_throwable`): the test passes when `sub_0062BA80_ItemTypeThrowable` is non-zero, else when the item has
  stat 125. Skill 4 (Left Hand Throw): the same on the other hand. Skill 5 (Left Hand Swing): dual wield and a weapon
  (type 45) in the hand. Any other skill passes. (fn:sub_00647640_SkillAmmoOk@0x00647640, struct:SkillEntry+0x30,
  tbl:ItemStatCost.txt:Stat)
- [I] `SKILLS_WeaponTypeOk`: a row with neither `itypea1` (`+0x18`) nor `etypea1` (`+0x24`) above 0 passes. Else it
  tests the two hands with `0x00643D90` in both orders (for skills 4 and 5 the primary weapon is removed from its hand
  first). (fn:SKILLS_WeaponTypeOk@0x00643F80, tbl:Skills.txt:itypea1, tbl:Skills.txt:etypea1)
- [I] `SKILLS_ManaOk`: an item skill (`SkillEntry+0x34` ≠ −1) needs `+0x38` (charges) > 0. Else `lvl = clamp(base
  (+0x28) + bonus (0x00644180), 0, sub_00611830_ExpMaxLevel(0))`, `cost = (lvlmana · max(lvl − 1, 0) + mana) <<
  manashift`; under state 114 `cost ≤ stat 6` (life), else `srvdofunc` 116 (the shapeshifts) with `Unit+0xC8` bit 3 passes,
  else `cost ≤ stat 8`. (fn:SKILLS_ManaOk@0x00647540)
- [I] `SKILLS_RestrictOk` (`+0x228`): 0 → refuse while `0x0063A510` is true; 1 → pass; 2 → pass only while
  `0x0063A510` is true and the unit has one of `State1..3` (`+0x22A`, the first negative ends the list); any other
  value passes. `0x0063A510` was not read (a "restricted state" test by its use). (fn:SKILLS_RestrictOk@0x00644060,
  tbl:Skills.txt:restrict)
- [I] `SKILLS_StartManaOk`: a player with `startmana` > 0 and `stat 8 < startmana · 256` is refused unless it is in
  state 12 (`inferno`). The three stock rows with `startmana` are Inferno, Arctic Blast and Blade Fury, the
  channelled skills: the first frame needs `startmana`, the following ones only the per-use cost.
  (fn:SKILLS_StartManaOk@0x006440F0, tbl:Skills.txt:startmana, dispatch-rows.txt)
- [I] `SKILLS_ItemChargesOk`: an item skill passes only if the inventory item whose guid is `+0x34` has a non-zero low
  byte of stat 204 at layer `skill · 64 + (level & 0x3F)`; a missing item passes. (fn:SKILLS_ItemChargesOk@0x00647840,
  struct:SkillEntry+0x34)
- [I] `SKILLS_DelayOk`: a player in state 121 passes only if the skill's `delay` calc gives < 1 (§ 8).
  (fn:SKILLS_DelayOk@0x006478F0)

### 3. The mode command and the mode start

- [I] `sub_005809D0_PlayerModeCmd(entry, mode, x, y, force)` (`ECX` game, `EDX` player): unless `force`,
  `sub_0057EEC0_PlayerModeAllowed(mode, 1, entry)` must pass; a non-zero entry becomes the used skill
  (`UNIT_SetUsedSkill`, `SkillList+0x10`); then `g_PlayerModeStartFuncs[mode].xy(mode, x, y)`. `PLAYER_ModeCmdUnit` is
  the same with the target unit (`GameFindUnit`; "StartModeID: Bad Target" when missing) and the `.unit` slot; for a
  player it first zeroes `PlayerData+0x150` and `+0x154`. (fn:sub_005809D0_PlayerModeCmd@0x005809D0,
  fn:PLAYER_ModeCmdUnit@0x00580A70, data:g_PlayerModeStartFuncs@0x006E1740)
- [I] Modes 7, 8, 10–16 and 18 (A1, A2, SC, TH, KK, S1–S4, sequence) use the skill starts
  `sub_0057FE90_PlrModeStartSkillXY` / `sub_0057FEF0_PlrModeStartSkillUnit` and the frame function
  `sub_00580460_PlrModeSkillFrame` (`dispatch-scan.txt`, `PMODE` lines). Both starts set the path target, clear
  `Unit+0xC4` bit 6 (0x0057FED8, 0x0057FF4C) and call `SKILLS_StartUsedSkill`. (fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90,
  fn:sub_0057FEF0_PlrModeStartSkillUnit@0x0057FEF0, data:g_PlayerModeFrameFuncs@0x00732C10)
- [I] The refusal path of the start functions puts a player into mode 5 (town neutral) with `force` = 1:
  `sub_005809D0_PlayerModeCmd(0, 5, 0, 0, 1)` at `0x0056FB49`, `0x0056FC41`, `0x0056F6DB` and `0x0056F8AE`.

### 4. `SKILLS_StartUsedSkill` and `SKILLS_SrvStart`

```c
// fn:SKILLS_StartUsedSkill@0x0056FAF0 (ECX game, EDX unit), trimmed
entry = UNIT_GetUsedSkill(unit); if (!entry) return 0;
id = *(int16*)entry->pRecord;
if (!SKILLS_TargetCheck(id, game, unit)) { if (player) PlayerModeCmd(0, 5, 0, 0, 1); return 0; }
lvl = SKILLS_GetSkillLevel(unit, entry, 1);
if (SKILLS_GetItemSkillInfo(entry, &owner, &id2, &lvl, &charges) && charges == 0) return 0;   // item skill: its own level
rec = Skills[id];
tgt = UNIT_GetTargetUnit(game, unit);
if (tgt && !(rec->b07 & 0x04 /*TargetAlly*/) && sub_00554D20_SkillAllyTest(tgt, id)) return 0;
if (!(rec->b05 & 0x01 /*InTown*/) && RoomIsTown(UnitGetRoom(unit))) { UNIT_SetUsedSkill(unit, 0); if (player) PlayerModeCmd(0,5,0,0,1); return 0; }
r = SKILLS_SrvStart(id, lvl, 0);
if (player && r == 0) PlayerModeCmd(0, 5, 0, 0, 1);
return r;
```

- [I] As above. `SKILLS_TargetCheck`: no target passes; a `TargetableOnly` (`+0x06` bit 4) skill needs a hostile
  target or `0x005542C0` or `sub_00554D20_SkillAllyTest`; a target with `+0xC4` bit 1 keeps the target only when the
  skill has `TargetCorpse` (`+0x07` bit 0; the monster-in-mode-12 case keeps it only then too), otherwise the target is
  cleared (`0x00620C10(unit, 0)`) and the check passes. (fn:SKILLS_StartUsedSkill@0x0056FAF0,
  fn:SKILLS_TargetCheck@0x0056CC60, fn:SKILLS_GetItemSkillInfo@0x00643B00)

```c
// fn:SKILLS_SrvStart@0x0056F640 (id, lvl, noCost; ECX game, EDX unit), trimmed
if (!game || !unit || !UnitGetRoom(unit)) return 0;
if (!rec || (!noCost && !SKILLS_SrvManaCheck(unit))) return 0;
if (!(rec->b05 & 0x01) && (no room || town)) { UNIT_SetUsedSkill(unit, 0); if (player) PlayerModeCmd(0,5,0,0,1); return 0; }
if (rec->LineOfSight && SKILLS_GetTargetXY(&x, &y)) {
    mask = {1: 0x0004, 2: 0x1C09, 3: 0x0180, 4: 0x0804, 5: 0x0805}[rec->LineOfSight];   // other values: return 0
    if (!SKILLS_LineOfSightOk(x, y, unit, mask)) return 0;
}
st = rec->srvstfunc; if (st < 0 || st >= 0x5B) return 0;
if (g_SkillStartFuncs[st] == 0) r = 1;
else { r = g_SkillStartFuncs[st](id, lvl); if (!r) return 0;
       if (!(rec->b08 & 0x20 /*usemanaondo*/) && !noCost) SKILLS_PayCost(id, lvl); }   // result ignored
if (rec->b04 & 0x40 /*periodic*/) UNIT_CancelEvents(8, 0);
return r;
```

- [I] As above. A row with no start function pays nothing here: its cost is paid by
  `SKILLS_SrvDo` (§ 6), as is the cost of the two `usemanaondo` rows (Plague Javelin, Blade Fury). `noCost` = 1 comes from `ITEMSKILL_Cast` (§ 10); the callers at `0x005CAF72` and
  `0x005CDF70` (inside do functions 83 and 109) were not read. (fn:SKILLS_SrvStart@0x0056F640, dispatch-scan.txt `CALLS`)
  *2026-10-20 (P1.3):* read in [skills/0003 § 4](0003-handlers.md#4-skills_srvstart-and-skills_paycost-inside-do-functions):
  both deliver or drop the queued hit and call `SKILLS_SrvStart(id, lvl, 0)` again, so the start function (and its
  cost) runs once more inside the do frame. (fn:sub_005CAF30_SkillDo83DeliverRestart@0x005CAF30,
  fn:sub_005CDF10_SkillDo109Frenzy@0x005CDF10)
- [I] `SKILLS_LineOfSightOk(x, y, unit, mask)` is `COLL_LineTest(room, (x, y) → unit position, mask) == 0`.
  (fn:SKILLS_LineOfSightOk@0x00645950, tbl:Skills.txt:LineOfSight)
- [I] `SKILLS_SrvManaCheck` reads the **used skill** (`UNIT_GetUsedSkill`), not the id passed: a non-player passes; an item
  skill needs charges > 0; else the cost of § 7 with `lvl = max(GetSkillLevel(unit, entry, 1) − 1, 0)` against
  stat 8, with the same `srvdofunc` 116 exception and **no** state-114 branch (unlike `SKILLS_ManaOk`).
  (fn:SKILLS_SrvManaCheck@0x0056C160)

### 5. The frame: when the do function runs

```c
// fn:sub_00580460_PlrModeSkillFrame@0x00580460 (event, ...; EDX player), trimmed
entry = UNIT_GetUsedSkill(unit); if (!entry) return 2;                 // 2: end the mode
sub_006212C0(unit, ...);
f = entry->flags;
if ((f & 1) && UnitMoveStep() == 2) { entry->flags = f | 2; SKILLS_DoUsedSkill(); }      // move first, do on arrival
else if (!(unit->c4 & 0x40) && (event == 1 || event == 2)) SKILLS_DoUsedSkill();
return UnitIsDead() ? 2 : 1;
```

- [I] The player's frame function runs from unit event 0 (`g_PlayerEventFuncs[0]` → `0x005811D0`, which calls
  `g_PlayerModeFrameFuncs[Unit+0x10]` and ends the mode on 2). The do runs on an event code of 1 or 2 while
  `Unit+0xC4` bit 6 is clear, or on arrival for a move-first entry. Which frame carries code 1 or 2 is the animation
  data's (phase (4)); here it is a logged input. (fn:sub_00580460_PlrModeSkillFrame@0x00580460,
  data:g_PlayerEventFuncs@0x006E1810, struct:SkillEntry+0x0C)
- [I] `Unit+0xC4` bit 6 is set by 124 `or [reg+0xC4], 0x40` sites in the image (79 in the server skill range
  `0x0056B000`–`0x005E0000`: most do functions, `SKILL_MeleeDeliverDo` at `0x0056F42A`, `SKILLS_SrvDo` at `0x0056F98A`
  when it creates the srvmissile, `sub_005DEAD0_MonAiUseSkill` at `0x005DEB08`) and cleared by 17 (9 in that range);
  `dispatch-scan.txt` `C4SET`/`C4CLR` lists them. So a second code-1/2 frame of the same mode does not repeat a do
  function that set it. (dispatch-scan.txt, 0x0057FED8)
- [I] **Monsters.** The monster mode record (`sub_005A78A0_MonModeRecord`, table `0x006E2260`, 16 bytes per mode)
  gives the start (+0), frame (+4) and end (+8) functions; event 0 calls the frame function through `0x005A7BA0`
  (`g_MonEventFuncs[0]`). Modes 4, 5, 7, 8 and 9 (A1, A2, SC, S1, S2) start with `sub_005A75C0_MonModeStartSkill`
  and frame with `sub_005A7670_MonAttackFrame`; mode 14 (sequence) starts with `0x005A7870` and frames with
  `sub_005A8670_MonSeqFrame`. (fn:sub_005A78A0_MonModeRecord@0x005A78A0, data:g_MonEventFuncs@0x006E2490)
- [I] `sub_005A75C0_MonModeStartSkill`: path planning when `0x005A6B10` is true (and, when `0x00648780` refuses, only
  for monster class 110 — the other classes return 0); then, with a used skill, `SKILLS_StartUsedSkill`.
  `sub_005A7670_MonAttackFrame`: with no used skill, the plain attack (`MON_MeleeHit`, delivery) as combat/0001 § 2
  reads it; with one, the move-first branch as for players, else `SKILLS_DoUsedSkill` **with no event-code test**
  (the monster frame function is the action-frame handler). `sub_005A8670_MonSeqFrame`: the move-first branch, then
  the do when `Unit+0x4E` is 4, or when no move-first do ran, bit 6 is clear and `Unit+0x4E` is 1 or 2.
  (fn:sub_005A75C0_MonModeStartSkill@0x005A75C0, fn:sub_005A8670_MonSeqFrame@0x005A8670)
- [I] `SKILLS_DoUsedSkill` = `SKILLS_SrvDo(id, GetSkillLevel(unit, used, 1), pay 1, item 0, effect 0)` then
  `SKILLS_QueuePeriodic(id, lvl, 0)`. (fn:SKILLS_DoUsedSkill@0x0056FC50)

### 6. `SKILLS_SrvDo`

```c
// fn:SKILLS_SrvDo@0x0056F7F0 (id, lvl, pay, item, effect; ECX game, EDX unit), trimmed
actor = unit->type == 0 || unit->type == 1;
if (actor) {
    used = UNIT_GetUsedSkill(unit);
    if (used && !(used->flags & 1) && !(rec->b05 & 0x01) && (no room || town)) { refuse as in § 4; return 0; }
    if (!item && (!used || id(used) != id || GetSkillLevel(unit, used, 1) < 1)) {
        e = SKILLS_GetUnitSkill(unit, id); if (!e || GetSkillLevel(unit, e, 1) < 1) return 0; }
}
do = rec->srvdofunc; if (do < 0 || do >= 0xBF) return 0;
if (actor && (rec->b08 & 0x20) && !SKILLS_SrvManaCheck(unit)) return 0;               // usemanaondo
if (effect && item && rec->ItemEffect > 1) do = rec->ItemEffect;
r = g_SkillDoFuncs[do] ? g_SkillDoFuncs[do](id, lvl) : 0;
if (rec->srvmissile >= 0 && MissileRec(rec->srvmissile)) {
    unit->c4 |= 0x40; dx = dy = 0;
    if (item && effect && GetTargetXY(&tx, &ty) && tx && ty) { dx = tx - subX; dy = ty - subY; tx += dx; ty += dy; }
    (rec->b04 & 0x02 /*lob*/ ? SkillMissileCreateLob : SkillMissileCreate)(unit, id, lvl, dx, dy, tx, ty, 0);
    r = 1;
} else if (!r) return 0;
if (pay) {
    if (actor) { if (!g_SkillStartFuncs[rec->srvstfunc] || (rec->b08 & 0x20)) SKILLS_PayCost(id, lvl);   // result ignored
                 if (rec->b04 & 0x01 /*decquant*/) PLAYER_UseAmmo(); }
    d = SKILLS_EvalCalc(unit, rec->delay, id, lvl);
    if (d > 0 && unit->type == 0 && (rec->anim != 18 || (*(u32*)(unit + 0x38) & 0xFFFFFF00) == 0))
        SKILLS_SetDelayState(game, unit, d);
}
return r;
```

- [I] As above. Branches the spec needs: the `ItemEffect` override applies only to item casts
  with the effect flag (§ 10); the srvmissile is created after the do function and with `PLAYER_UseAmmo` gated off
  (`useAmmo` argument 0), so `decquant` is the only ammunition use of this path; a sequence-anim (`anim` 18) skill sets
  its delay only while `Unit+0x38 & 0xFFFFFF00` is 0 (what `+0x38` holds was not read). (fn:SKILLS_SrvDo@0x0056F7F0,
  tbl:Skills.txt:srvmissile, tbl:Skills.txt:decquant, tbl:Skills.txt:delay)
- [I] Callers (8): `SKILLS_DoUsedSkill`, `EVENT_SelectedAuraTick` (two), `EVENT_ItemAuraTick`,
  `sub_0056FF10_AuraSelect` (the right-skill aura select, from `sub_005701B0_PlayerSetSkill`), `ITEMAURA_Start`,
  `ITEMSKILL_Cast`, and `sub_005394A0_PlayerPlaceInAct`. (fn:SKILLS_SrvDo@0x0056F7F0, dispatch-scan.txt `CALLS SKILLS_SrvDo`)

### 7. Costs and their rounding

```c
// fn:SKILLS_PayCost@0x0056BFE0 (id, lvl; EDX unit), trimmed
if (!unit || unit->type != 0) return 1;                       // only players pay
used = UNIT_GetUsedSkill(unit);
if (used && id(used) == id && used->ownerItem != -1) return UseCharge(unit);
if (rec && (rec->mana || rec->lvlmana)) {
    cost = (rec->lvlmana * max(lvl - 1, 0) + rec->mana) << (rec->manashift & 31);   // s16 * s32, then shl
    if (cost < rec->minmana * 0x100) cost = rec->minmana * 0x100;
    if (UNIT_HasState(unit, 114)) return BloodManaPay(unit, cost);
    if (cost <= stat8) { UnitAddStat(unit, 8, -cost); return 1; }
}
return 0;
```

- [I] Integer semantics: `mana` and `lvlmana` are s16, `manashift` is the low byte of `+0x188` (shift count & 31),
  the product and sum are s32, the shift is a logical left shift of the s32; stat 8 is mana in 1/256. The floor at
  `minmana · 256` applies only to the payment; seven stock rows have a negative `lvlmana` (Magic Arrow, Guided Arrow,
  Dopplezon, Teleport, Bone Prison, Summon Resist, Double Swing), the rows where the floor can bind.
  (fn:SKILLS_PayCost@0x0056BFE0, tbl:Skills.txt:lvlmana, tbl:Skills.txt:minmana, dispatch-rows.txt)
- [I] `lvl` in the payment is the level passed by the caller (the start's or the do's `lvl`); the checks of § 2 and § 4
  recompute it from the entry. (fn:SKILLS_PayCost@0x0056BFE0, fn:SKILLS_ManaOk@0x00647540)
- [I] **The result is not tested** by `SKILLS_SrvStart` (`0x0056F7AA`, then `0x0056F7AF` loads the periodic mask) nor
  by `SKILLS_SrvDo` (`0x0056FA7A`, then `0x0056FA7F` loads the `decquant` mask): when the floored cost exceeds the
  mana, nothing is taken and the skill runs. The third caller is a do function (`0x005D6B48`, in `0x005D69D0`), not
  read. (dispatch-scan.txt `SITE`, `CALLS SKILLS_PayCost`) *2026-10-20 (P1.3):* `0x005D69D0` is `srvstfunc` 26 (Blade
  Fury), not a do function; it pays per fragment, its result unused too
  ([skills/0003 § 4](0003-handlers.md#4-skills_srvstart-and-skills_paycost-inside-do-functions);
  fn:sub_005D69D0_SkillSt26BladeFury@0x005D69D0).
- [I] **Blood Mana.** `sub_005D2B60_BloodManaPay`: if `cost ≤ stat 6` the life is reduced by `cost`, and when the new
  life is below `Param5 · 256` of the skill that made the state (Blood Mana, row 310, `Param5` 40) the state's list is
  removed; else the state is removed, life is set to 256 and the payment fails (ignored as above).
  (fn:sub_005D2B60_BloodManaPay@0x005D2B60, tbl:Skills.txt:Param5, tbl:States.txt:state)
- [I] **Charges.** An item skill's use calls `sub_0056BEC0_UseCharge` (items/0011: charges −1, no draw).
  (fn:sub_0056BEC0_UseCharge@0x0056BEC0)

### 8. The delay state

- [I] `SKILLS_SetDelayState(game; EAX = d, EDI = unit)`: a player with `d` ≠ 0 gets (or reuses) a timed stat list of
  state 121 (`skilldelay`, flags 2, `STATE_DefaultRemoveCB`), its end set to `game+0xA8 + d`, and a unit event 12 at
  that frame (the timed-list expiry, `EVENT_TimedListExpire`). (fn:SKILLS_SetDelayState@0x0056EF90,
  fn:EVENT_TimedListExpire@0x00580800)
- [I] `SKILLS_DelayOk` refuses only a skill whose own `delay` calc (`+0x190`, at its current level) is ≥ 1; a skill with
  no delay is usable during another skill's delay. 23 stock rows have a `delay`. (fn:SKILLS_DelayOk@0x006478F0,
  dispatch-rows.txt)

### 9. Periodic, aura and channelled skills; `repeat`

- [I] `SKILLS_QueuePeriodic(id, lvl, selected)`: only for `periodic` or `aura` rows; `p = perdelay` calc, 5 when the
  calc gives less than 6; it cancels the unit's event-8 queue (all of it when `selected`, else that skill's) and queues
  event 8 at `((frame − 1 + p) / p)·p + 1` with `(id, lvl)`, or `(−1, 0)` for the selected right-skill aura. This is the
  grid stats/0002 confirmed for auras (`SKILLS_NextPeriodicFrame`, `[C]` there). (fn:SKILLS_QueuePeriodic@0x0056CDA0,
  fn:EVENT_SelectedAuraTick@0x0056FCB0)
- [I] A `periodic` row's start (`SKILLS_SrvStart`) cancels **all** the unit's event-8 entries first. The two stock
  `periodic` rows are Thunder Storm and Blade Shield; the channelled rows (Inferno, Arctic Blast, Blade Fury) are the
  `startmana` rows of § 2, not `periodic`. (fn:SKILLS_SrvStart@0x0056F640, tbl:Skills.txt:periodic)
- [I] `repeat` (`+0x05` bit 3): no server reader was found by the instruction patterns tried (a `test` of
  `[reg+0x5]` with the mask byte `0x006CE274`, or with the immediate 8, in `0x00530000`–`0x00660000`); the two hits
  are a missile record test (`0x005ADC43`) and stat-list code. It stays an open question.
  *2026-10-20 (P1.2):* the `0x005ADC43` hit is `MissileDoFrame`'s test of Missiles `SrcTown` (`+0x05` bit 3), not
  a Skills reader ([skills/0002 § 4](0002-missiles.md#4-each-frame)).
  *2026-10-20 (P1.3):* with the bit-mask-table form of the test, the only Skills `repeat` readers are the client's;
  the three `repeat` rows are the three `startmana` rows ([skills/0003 § 12](0003-handlers.md#12-routed-questions-from-p11)).
- [I] **Aura select.** `sub_0056FF10_AuraSelect(_, id)` (from `sub_005701B0_PlayerSetSkill`) for an `aura` row with an
  `aurastate`: without `immediate` (`+0x05` bit 7) it sets the state and a plain list carrying the skill (stat 350)
  and level (stat 351); with it, it runs `SKILLS_SrvDo(id, lvl, 1, 0, 0)` at once; then `SKILLS_QueuePeriodic(id, lvl, 1)`.
  (fn:sub_0056FF10_AuraSelect@0x0056FF10)

### 10. Item-granted skills

- [I] **Charged skills** are skill entries with `ownerItem` ≠ −1 (`SkillEntry+0x34`): `SKILLS_ManaOk` and
  `SKILLS_SrvManaCheck` test `charges` (`+0x38`) instead of mana, `SKILLS_ItemChargesOk` tests the item's stat 204,
  `SKILLS_StartUsedSkill` refuses at 0 charges and uses the entry's own level (`+0x28`), and `SKILLS_PayCost` spends a
  charge. (struct:SkillEntry+0x34, struct:SkillEntry+0x38)
- [I] **Item auras** (stat 151): `ITEMAURA_Start` queues event 9 on the grid and, for an `immediate` row, runs
  `SKILLS_SrvDo(id, lvl, 1, item 1, 0)`; `EVENT_ItemAuraTick` repeats it while stat 151 at that layer is > 0 (stats/0002
  § 4). (fn:ITEMAURA_Start@0x005BF510, fn:EVENT_ItemAuraTick@0x0056FE40)
- [I] **Item-event casts** ("chance to cast"): `ITEMSKILL_Cast(id, lvl, target, x, y, …, effect)` refuses id 0 and a
  row with `ItemEffect` (`+0x16A`) 0. It saves the caster's target and path point, aims at the given unit or point,
  then by `ItemTarget` (`+0x120`): 1 the caster itself, 2 `0x005FD850`, 3 `0x005FD9C0`, 4 `0x005FDA10` (each may
  refuse). Then, unless `ItemCheckStart` (`+0x08` bit 1) is set and `SKILLS_SrvStart(id, lvl, noCost 1)` fails,
  `SKILLS_SrvDo(id, lvl, pay 0, item 1, effect)`. It restores the target, the point and `Unit+0xC4` bit 6 as they were.
  Its two callers `0x005FDCA0` (at a unit) and `0x005FDD60` (at a point) skip a caster in state 54
  (`uninterruptable`) and are reached from the stat-event handlers at `0x005BF170`–`0x005C0670` (P1.3).
  (fn:ITEMSKILL_Cast@0x005FDA80, tbl:Skills.txt:ItemEffect, tbl:Skills.txt:ItemTarget)
- [I] *2026-10-20 (Phase 1b):* the `ItemTarget` 2 helper draws. `0x005FD850` steps the seed at `+0x20` of the unit
  it is given twice per try, inline (`low % 40 − 20` added to x and to y). It tries at most 10 times, until
  `0x0064D870` returns 0. The one stock `ItemTarget` 2 row is Teleport. Which unit it is given (caster or target) is
  unfollowed, and so are 3's and 4's helpers (`p45b-reread.txt` R5). (0x005FD900–0x005FD98A)
- [I] So an item cast pays no mana, uses no ammunition and sets no delay (`pay` = 0), and with the effect flag runs
  the do function `ItemEffect` when it is > 1: Frost Nova and Nova (36), Chain Lightning (151); the other 69 stock
  `ItemEffect` rows hold 1. (fn:SKILLS_SrvDo@0x0056F7F0, dispatch-rows.txt)

### 11. The skill packet

```c
// fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0 (srvstfunc 32; id, lvl; ECX game, EDX unit), trimmed
tgt = UNIT_GetTargetUnit(game, unit); if (!tgt || RoomIsTown(UnitGetRoom(tgt))) return 0;
sub_0056E520_SkillAttackRateList(unit, SKILLS_EvalCalc(unit, rec->calc3, id, lvl));    // stat 68 on a new list
memset(&p, 0, 0x70);
p.result = COMBAT_MeleeHitTest(tgt, SKILLS_GetToHit(unit, id, lvl), 0);
if (p.result & 1) {
    p.result |= rec->ResultFlags;  p.flags |= rec->HitFlags;  if (rec->HitClass) p.hitClass = rec->HitClass;
    p.edPct = SKILLS_EvalCalc(unit, rec->calc1, id, lvl);
    if (rec->EType && (c4 = SKILLS_EvalCalc(unit, rec->calc4, id, lvl)) > 0) { p.convType = rec->EType; p.convPct = c4; }
    SKILLS_RollElemDamage(id, lvl);                                // into p
}
COMBAT_ResolveAndQueue(tgt, &p, rec->SrcDam ? rec->SrcDam : 128);
if ((q = sub_0057D690_QueuedHitFind())) q->phys += SKILLS_EvalCalc(unit, rec->calc2, id, lvl) << 8;
if (rec->aurastate valid) { own list of the state (flags 4); STATE_Set; SKILLS_ApplyAuraStats(rec, id, lvl); }
return 1;
```

- [I] As above (the conversion store is at `0x005D7FA8`). The packet's physical damage and the
  weapon terms are built inside `COMBAT_ResolveAndQueue` (combat/0001 § 5: the builder runs when the result has 0x1
  and none of 0x8380 and `flags & 2` is clear), with `edPct` = calc1 added to stat 25 there and the conversion read at
  `0x0057BCB2`–`0x0057BCE0`. `calc2` is added **after** the reductions, to the queued hit's physical, in 1/256.
  (fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0, fn:COMBAT_ResolveAndQueue@0x0057DBF0, struct:DamagePacket+0x65,
  struct:DamagePacket+0x68, struct:DamagePacket+0x0C)
- [I] **The conversion writers.** `dispatch-scan.txt` (`CONV` lines) finds 39 reads of `EType` (`+0x1DC`) in the server
  skill range, 15 of them followed by a byte store to the stack: in start functions 6, 7, 10, 16, 29, 32, 39, 56 and
  do functions 7, 13, 67, 150, and in three helpers `0x005D6200`, `0x005D8B10`, `0x005DA660`. The store is the
  packet's `+0x65` in start functions 6 (`0x005DA9F9`), 7 (`0x005DAC35`) and 32 (`0x005D7FA8`) (packet at `ebp−0x7C`,
  store at `ebp−0x17`); the other twelve were not each mapped to the packet. *2026-10-20 (P1.3):* all fifteen store
  the packet's `+0x65` ([skills/0003 § 12](0003-handlers.md#12-routed-questions-from-p11), `handlers-scan.txt` `CONV`). Stock data: Concentrate (`mag`, calc4 =
  Berserk's level), Berserk (`mag`, 100), Vengeance, Power Strike and others give `EType`.
  (dispatch-scan.txt, tbl:Skills.txt:EType, tbl:Skills.txt:calc4)
- [I] `SKILLS_RollElemDamage(id, lvl)` (`ECX` unit, `EDX` packet): `len = GetElemLen`, `min = GetElemMin`,
  `max = GetElemMax` (all with the synergy flag 1; data/0005 § 6 reads them), `v = RNG_RangeB(unit seed, max − min) +
  min` (one draw on the **unit's** seed, `+0x20`), then `SKILLS_AddElemToPacket(EType, v, len)`.
  (fn:SKILLS_RollElemDamage@0x0056E0C0, fn:SKILLS_GetElemMin@0x00644D50)
- [I] `SKILLS_AddElemToPacket(type, v, len, *outOverlay, *outType)`: type 10 draws `RNG_Step(unit seed)` and maps
  `low & 3` through `0x006E1278` (a second draw, only for type 10), with `len` 50 when < 1; then 1 fire `+0x10`
  (`hitClass` 0x20), 2 lightning `+0x1C` (0x40), 3 magic `+0x20`, 4 cold `+0x24` and `coldLen = len` (0x30), 5 poison
  `+0x28` and `poisonLen = len` (0x50), 6/7/8 life/mana/stamina steal, 9 stun `+0x44 += v + len` (0x60), 11 burn
  `+0x14` and `burnLen`, 12 cold `+0x24` and `freezeLen = len` (0x30), any other the physical `+0x08`. Each adds `v`
  to the field. (fn:SKILLS_AddElemToPacket@0x0056C8E0, struct:DamagePacket+0x60)
- [I] **Start, then do.** `srvstfunc` 32 builds and queues the hit at the **mode start**; the row's `srvdofunc` 2
  (`SKILL_MeleeDeliverDo`, shared by Kick, Power Strike, Impale, Vengeance, Bash, Stun, Concentrate, Berserk, Fire
  Claws, BearSmite and two monster rows) runs on the action frame: with a `srvoverlay` and a queued hit with 0x1 it puts
  the overlay on the target; with an `auratargetstate` and a hit it applies that state for `max(auralencalc, 1)` frames
  (a timed list, event 12, `SKILLS_ApplyAuraStats`); with an `aurastate` it sets it on the unit; it sets `Unit+0xC4`
  bit 6 and calls `COMBAT_DeliverQueued`. So the to-hit, defence and damage draws of such a skill happen at the start
  frame, the delivery (and its draws) at the action frame. (fn:SKILL_MeleeDeliverDo@0x0056F1F0,
  tbl:Skills.txt:srvoverlay, tbl:Skills.txt:auratargetstate)
  *2026-10-21 (plan 0046 batch `bar`), emulated:* start 32 and do 2 are reproduced up to their boundaries (`[C]` under
  ADR-0021; [skills/0012](0012-barbarian.md) § 3): start 32 up to `0x0056E520(ECX unit, EDX calc3)` after the target
  and town tests; do 2 up to `UnitSetOverlayStat`, `STATLIST_Alloc`, `UnitQueueEvent`, `STATE_Set` or
  `COMBAT_DeliverQueued`. Refinements of the bullet above: the overlay test is `0 < srvoverlay ≤ DataTables+0xBC0`;
  each of the overlay and `auratargetstate` blocks returns **1 without delivering** (bit 6 not set) when
  `sub_0057D690_QueuedHitFind(caster, target)` finds no `+0xAC` node naming both, and 0 without a target; the "0x1"
  is the found node's packet `+0x04` bit 0;
  `auratargetstate` admits 0, `aurastate` refuses it. Everything after those calls stays as read above, `[I]`.
  (fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0, fn:SKILL_MeleeDeliverDo@0x0056F1F0)
- [I] `srvstfunc` 6 (`sub_005DA940_SkillSt06Hit`): the same shape with to-hit 0 (the attack rating alone), no flags, no
  calc2/calc3, and SrcDam passed as stored (0 not replaced). `srvstfunc` 7 (Impale) is § 14.
  (fn:sub_005DA940_SkillSt06Hit@0x005DA940)
- [I] `SKILLS_GetPhysMin/Max(unit, id, lvl, withWeapon)` (summon damage, missiles, several do functions): a `Kick`
  row (`+0x05` bit 1) gives `max(…, 1) / 4 << 8` of `str + dex − 20` (a player) or `3 · level` (others); otherwise
  `w = SrcDam · weapon min / 128` when SrcDam and `withWeapon` (the weapon's min from the item for a player whose
  `0x0063D340` returns 2, else stat 21), `x = w + LevelBands(lvl, MinLevDam1..5) + MinDam`, `x += MulDiv(x,
  DmgSymPerCalc, 100)` when that calc is non-zero, `x << HitShift`. (fn:SKILLS_GetPhysMin@0x00647BC0,
  0x00647CA6–0x00647CF1, fn:SKILLS_LevelBands@0x00644B70)
- [I] The mastery bonus enters a skill hit through the builder (`SKILLS_GetMasteryBonus` from `COMBAT_BuildDamage` and
  `COMBAT_ToHitRoll`, combat/0001 § 5) and through the missile path (`0x0064B860`, read by P1.2:
  [skills/0002 § 3](0002-missiles.md#3-the-damage-the-missile-carries)); the synergies enter through
  the calcs (`DmgSymPerCalc`, `EDmgSymPerCalc`, `skill('…'.blvl)` terms in calc1–calc4). (fn:SKILLS_GetMasteryBonus@0x00645830)

### 12. Progressive charges

- [I] `srvdofunc` 34 (`sub_005D3490_PrgChargeHitDo`; Tiger Strike, Cobra Strike, Royal Strike) needs an `aurastate` and
  an `aurastat1`; it zeroes a packet, `COMBAT_MeleeHitTest(tgt, SKILLS_GetToHit)`, `COMBAT_ResolveAndQueue` with SrcDam
  (0 → 128), and on a queued hit with 0x1 `SKILLS_AddProgressiveCharge`, then `COMBAT_DeliverQueued`.
  `srvdofunc` 35 (`sub_005D35D0_PrgChargeHitDualDo`; Fists of Fire, Claws of Thunder, Blades of Ice) clears or sets
  `Unit+0xC4` bit 6 by the dual-claw test and the parity of `Unit+0x38 >> 8`, then calls 34.
  (fn:sub_005D3490_PrgChargeHitDo@0x005D3490, fn:sub_005D35D0_PrgChargeHitDualDo@0x005D35D0)
- [I] `SKILLS_AddProgressiveCharge`: a timed list of the `aurastate` lasting `auralencalc` frames (refreshed; event 12),
  carrying stats 350/351 (skill, level); `aurastat1` += 1 capped at 3; when it changed, `aurastat2` += `aurastatcalc2`
  and the state is set and sent. (fn:SKILLS_AddProgressiveCharge@0x005D3320, tbl:Skills.txt:aurastat1)
- [I] **The finisher** (`COMBAT_PrgFinisher`, from `SKILL_AttackDo` at `0x0056F1CE`): for a queued hit with 0x1 and the
  target in melee range it sets bit 6 and walks the progressive state list (`DataTables+0x16C`, count `+0x170`); for a
  state with a list, a skill and a level `max(stat 351, current level)` > 0 and an `aurastat1`, `n = clamp(charges, 1,
  3)`; **it copies the attacker's seed out (`0x005D5374`), calls `RNG_Step` on it (`0x005D537B`), keeps the result
  (`[ebp−0x24]`) and copies the seed back (`0x005D538C`)**; with `prgstack` it runs `srvprgfunc1..n−1` with the charge
  stat set to 1..n−1, then (always) `srvprgfunc n` from `g_SkillDoFuncs`, and calls `0x00571AA0` with the kept value as
  its third argument; then frees the list. So the finisher's own step leaves the attacker's seed as it was; the
  `srvprgfunc` entries it calls may draw (not read; P1.3 / plan 0046). *2026-10-20 (P1.3):* they do: entries 37, 39, 41
  and 143 step the attacker's seed once at entry and 38 draws `RangeB` on it twice (three times for `EType` 10);
  `0x00571AA0` is a client message ([skills/0003 § 1](0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail);
  0x005D4E80, fn:sub_00571AA0_UnitMsgA3@0x00571AA0). combat/0001's "draws at least once more on the
  attacker's seed" is corrected there. (fn:COMBAT_PrgFinisher@0x005D5220, 0x005D5368–0x005D538C,
  0x005D544E–0x005D5465, fn:sub_00650E70_Copy64Out@0x00650E70, fn:sub_00650E60_Copy64In@0x00650E60, dispatch-scan.txt `SITE`)
  *2026-10-20 (Phase 1b):* `SKILL_AttackDo` is one of **six** direct callers. Five more sites are in finishing-move
  functions: start function 25 (Dragon Claw, two sites) and do functions 42 (Dragon Talon), 50 (Dragon Tail) and 52
  (Dragon Flight). Those functions are not read; they are plan 0046's (`p45b-reread.txt` R6, R7; src:arreat-summit-skill-trees
  in *Leads used*). (0x005D5A8C, 0x005D6399, 0x005D63E1, 0x005D71F2, 0x005D79DF)
  *2026-10-21 (plan 0046 batch `ass`):* the two sites `0x005D6399` and `0x005D63E1` are in **do 46** (Dragon Claw's do
  function `0x005D6340`, one per frame parity), not in start 25: start 25 (`0x005D6330`) is the 16-byte test
  `UNIT_GetTargetUnit ≠ 0` and calls nothing else. Each of the five passes `QueuedHitFind(caster, target)`'s result
  (do 42 and do 52 with no null test); do 42's, do 46's and do 50's calls are `[C]` as boundaries under ADR-0021
  ([skills/0014](0014-assassin.md) § 4). (fn:sub_005D6340_SkillDo46DragonClaw@0x005D6340,
  fn:sub_005D6330_SkillSt25HasTarget@0x005D6330, run:2026-10-21-cat-emu-ass)

### 13. Monster skill use

- [I] `sub_005DEAD0_MonAiUseSkill(mode < 16, …)`: `sub_005A7E60_MonCmdInit`, the used skill = the unit's entry for the
  chosen id with owner −1, `Unit+0xC4 |= 0x40`, `0x00649070(path, 1)`, then `sub_005A7C20_MonSetMode`; on failure
  `0x005DE080(10)`. The AI's choice of skill and mode is phase (5) and an input here.
  (fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0, fn:sub_005A7C20_MonSetMode@0x005A7C20)
- [I] Since bit 6 is set by the AI command and the monster mode start does not clear it, a monster's do runs only
  through the paths of § 5 that do not test it: `sub_005A7670_MonAttackFrame` (no test) and the mode-14 `Unit+0x4E = 4`
  case. The bit-6 test of the mode-14 code-1/2 case then only matters for a mode entered otherwise.
  (0x005DEB08, fn:sub_005A7670_MonAttackFrame@0x005A7670, fn:sub_005A8670_MonSeqFrame@0x005A8670)
- [I] `sub_005D9C80_MonSkillAttackDo` has one caller, the monster branch of `srvstfunc` 40 (Leap, `0x005D9D50`): with a
  target, `MonAttackStats(mode 4)`, `MON_MeleeHit`, `COMBAT_DeliverQueued`, and two writes to the used entry, then a leap
  past the target. (fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80, dispatch-scan.txt `CALLS`)
- [I] `sub_005A4F50_MonAttackStats` (monsters/0004 § 9) has 6 callers: `sub_005A7C20_MonSetMode`, start function 42
  (`0x005CAE40`, Fire Hit), do functions 150 (`0x005CE9F0`), 67 (`0x005CF900`, Charge) and 7 (`0x005DB2D0`, Jab), and
  `sub_005D9C80_MonSkillAttackDo`. Its first step `sub_0056E050_MonOwnerSkillDamage`: a monster with an owner whose
  MonStats `SkillDamage` (`+0xA8`) is a skill row gets `min = SKILLS_GetPhysMin(owner?, skill, lvl, 1) >> 8`, `max =
  SKILLS_GetPhysMax(…) >> 8`, `toHit = SKILLS_GetToHit(…)`, with `lvl` from `0x00644AA0` (the entry's `baseLevel`
  plus the bonus when it is the unit's own, clamped to `[0, ExpMaxLevel(0)]`); these three are added to the A1/A2/S1
  min, max and to-hit before the classic and player-count adjustments. Which unit (`EDI`/`ESI`) is read for the level
  is register-passed and not resolved here. (fn:sub_005A4F50_MonAttackStats@0x005A4F50,
  fn:sub_0056E000_SkillDamagePair@0x0056E000, tbl:MonStats.txt:SkillDamage)

### 14. Ammunition and weapon wear

- [I] `PLAYER_UseAmmo` (players only; 5 callers): with a bow (type 27) or crossbow (type 35) in use it takes the item in
  hand 4 or 5 that is stackable, throwable or has stat 125 (the quiver); with any other weapon only the weapon itself
  qualifies (the hand item must equal it). Then `sub_0056C310_ItemConsumeOne`. Callers: `SKILLS_SrvDo` (`decquant`,
  12 stock rows), the two skill missile creators when their `useAmmo` argument is set (§ 6 passes 0), and two skill
  functions, `sub_005DAA40_SkillWeaponWear` and `0x005DACD0` (`srvstfunc` 8, Strafe). (fn:PLAYER_UseAmmo@0x0056C3F0,
  dispatch-scan.txt `CALLS PLAYER_UseAmmo`, dispatch-rows.txt)
- [I] **Wear is Impale's.** `sub_005DAA40_SkillWeaponWear` has one caller, `srvstfunc` 7 (`sub_005DAB40_SkillSt07ImpaleHit`):
  after a hit (to-hit `SKILLS_GetToHit`, physical `COMBAT_RollPhysical(…, calc1, …, SrcDam)`, the elemental roll,
  SrcDam 128 to `ResolveAndQueue`), if the weapon has durability it calls the wear with `chance = calc2` and `amount =
  calc3`. The wear, for a weapon (type 45): a non-stackable one with durability draws `RNG_Step` inline on the
  **unit's** seed and, when `low % 100 < chance`, sets durability (stat 72) to `dur − amount` if that is > 0, else
  breaks the item (`sub_0055F850_ItemBreak`); a stackable one with quantity (stat 70) > 0 draws the same way and uses
  ammunition. No draw when the weapon fails those tests. (fn:sub_005DAA40_SkillWeaponWear@0x005DAA40,
  fn:sub_005DAB40_SkillSt07ImpaleHit@0x005DAB40, tbl:Skills.txt:calc2)

### 15. Draws, seeds and the chaining reading (ADR-0014)

| Event | Entry | Draws (this batch) | Seed |
|---|---|---|---|
| request | `PLRMSG_SkillAt*` | none (stat 328 +1) | — |
| start | `SKILLS_SrvStart` | whatever the `srvstfunc` draws; for a skill hit: to-hit, defence, build and `SKILLS_RollElemDamage` (1, or 3 for type 10) | unit; target's for defence |
| do | `SKILLS_SrvDo` | the `srvdofunc`'s; `SKILL_MeleeDeliverDo` → `COMBAT_DeliverQueued` (combat/0001 § 11) | attacker, defender |
| cost, delay, periodic | `SKILLS_PayCost`, `SKILLS_SetDelayState`, `SKILLS_QueuePeriodic` | none read | — |
| wear (Impale) | `sub_005DAA40_SkillWeaponWear` | 1 | unit |
| finisher | `COMBAT_PrgFinisher` | its own step is restored (net 0); its `srvprgfunc` calls draw (*2026-10-20*, skills/0003 § 1) | attacker |
| monster attack stats | `sub_005A4F50_MonAttackStats` | monsters/0004 § 9 | monster |

- [I] Reading for Phase 2: a skill hit built at the start and delivered at the action frame is **two events** on the
  attacker's seed with frames between them; whether anything draws on that seed in between (the player's own defence
  rolls, a monster's AI) is what the chaining test of ADR-0014 measures. The request, cost, delay and queue steps hold
  no draw site of their own (callees not followed: `0x00548EF0`, `0x00548F80`, `0x0063A510`, `0x00643D90`).
  (fn:SKILLS_SrvStart@0x0056F640, fn:SKILLS_SrvDo@0x0056F7F0)

### 16. Branches

- [I] Player against monster: only players pay costs, use ammunition, get the delay state and pass the request checks;
  monsters reach `SKILLS_SrvStart`/`SKILLS_SrvDo` with the same table calls and the `actor` checks of § 6.
  (fn:SKILLS_PayCost@0x0056BFE0, fn:SKILLS_SetDelayState@0x0056EF90)
- [I] The functions of §§ 1–8 as read (callees named as not followed in § 15 excepted) hold no difficulty, expansion
  or player-count test; the expansion and player-count terms of a monster skill hit are `MonAttackStats`'
  (monsters/0004 § 9). (fn:SKILLS_CanUse@0x00647960, fn:SKILLS_SrvStart@0x0056F640, fn:SKILLS_SrvDo@0x0056F7F0,
  fn:sub_005A4F50_MonAttackStats@0x005A4F50)

## Data touched

`tbl:Skills.txt:srvstfunc`, `srvdofunc`, `srvprgfunc1..3`, `prgstack`, `srvmissile`, `lob`, `decquant`, `srvoverlay`,
`aurastate`, `auratargetstate`, `auralencalc`, `aurastat1`, `aurastat2`, `aurastatcalc2`, `periodic`, `aura`, `passive`,
`perdelay`, `immediate`, `InTown`, `InGame`, `LineOfSight`, `range`, `itypea1`, `etypea1`, `TargetableOnly`,
`TargetCorpse`, `TargetAlly`, `TargetItem`, `AttackNoMana`, `scroll`, `usemanaondo`, `ItemEffect`, `ItemTarget`,
`ItemCheckStart`, `mana`, `lvlmana`, `manashift`, `minmana`, `startmana`, `restrict`, `State1..3`, `delay`, `anim`,
`monanim`, `ResultFlags`, `HitFlags`, `HitClass`, `calc1..calc4`, `SrcDam`, `EType`, `Kick`, `MinDam`, `MinLevDam1..5`,
`DmgSymPerCalc`, `HitShift`, `Param5`; `tbl:MonStats.txt:SkillDamage`; `tbl:States.txt` rows 12, 54, 114, 121, 143;
`tbl:ItemStatCost.txt` stats 6, 8, 21, 25, 68, 70, 72, 125, 151, 204, 328, 350, 351.
`struct:SkillList+0x10`, `struct:SkillEntry+0x0C`, `struct:SkillEntry+0x34`, `struct:SkillEntry+0x38`,
`struct:DamagePacket+0x65`, `struct:DamagePacket+0x68`; `Unit+0xA8`, `Unit+0xC4` bit 6, `Unit+0x4E` (0x005A8670).

## Dead ends

- `0x005D32F0` looked like `srvstfunc` 23 by a miscount of the table base; the table base is `0x00732140` (entry 1 =
  `SKILL_AttackStart` `0x0056CA40`), and the scan prints every entry.
- A first count of `or [reg+0xC4], 0x40` gave 146 because the pattern also matched `0x400` and `0x4000`; the anchored
  scan gives 124.

## Open questions

- ~~Who reads `repeat` on the server.~~ *2026-10-20 (P1.3):* no server Skills reader by the mask-table pattern; three
  client tests ([skills/0003 § 12](0003-handlers.md#12-routed-questions-from-p11)).
- ~~Which record the ally test's inner lookup reads.~~ *2026-10-20 (P1.3):* the same skill id (`ECX = [ebp+0xC]`), so
  the refusal never fires from `SKILLS_StartUsedSkill` ([skills/0003 § 12](0003-handlers.md#12-routed-questions-from-p11)).
- [L] What `Unit+0x38` holds (the sequence-delay gate of § 6 and the dual-claw parity of `srvdofunc` 35).
- [L] *2026-10-20 (Phase 1b):* the `ItemTarget` helpers' draws. 2 (`0x005FD850`) steps the seed at `+0x20` of
  the unit it is given 2 to 20 times; which unit that is (caster or target) is unfollowed. Whether 3 (`0x005FD9C0`,
  a corpse pick through `0x0056E390`) or 4 (`0x005FDA10`) draws is not read. Phase 2 meets 2 only through an item
  Teleport cast.
- [L] Which frame of a mode carries event code 1 or 2, and `Unit+0x4E` for monsters: phase (4) (animation timing);
  Phase 2 logs it.
- ~~The `srvprgfunc` entries the finisher calls (36–41, 143) and `0x00571AA0`.~~ *2026-10-20:* read in
  [skills/0003 § 1](0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail).
- ~~`TgtPlaceCheck`, `prgcalc1..3`, `prgdam`, `weapsel`/`leftskill`.~~ *2026-10-20:* `prgcalc` by charge count
  (skills/0003 § 1), `prgdam` is combat/0001's `COMBAT_PrgHooksAfterBuild`, `TgtPlaceCheck` a monster AI test,
  `weapsel`/`leftskill` client-side ([skills/0003 § 12](0003-handlers.md#12-routed-questions-from-p11)). The to-hit term
  `SKILLS_GetToHit` (`0x006449F0`) is data/0005's reading.
- ~~`SKILLS_SrvStart`'s callers inside do functions 83 and 109 and `SKILLS_PayCost`'s inside `0x005D69D0`.~~
  *2026-10-20:* [skills/0003 § 4](0003-handlers.md#4-skills_srvstart-and-skills_paycost-inside-do-functions).
