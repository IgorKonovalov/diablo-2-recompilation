# 0006 — Catalogue batch 5 (summons): the think functions of AI rows 67, 84, 86, 101–112 and 143, state row 7, and H3's owner pair

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 5 (the summons: 67 `NecroPet`, 84 `BoneWall`, 86 `Hydra`, 101–112 the
> assassin and druid summons, 143 `ShadowMasterNoInit`, and state row 7), what do its init and think functions do:
> which `aip` slots and MonStats columns they read, which AI-control words they keep, which draws they make on which
> seed and in which order, and which command, skill or path request they end in? And for H3 (plan 0052 § Context):
> which unit's skill level does `MonOwnerSkillDamage` read for a summon's attack stats?
> **Date:** 2026-10-30   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 5)   **Status:** for review (`lane/r52f`)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52f`, symbols replayed from
`re/symbols.csv` with the scratch `__fastcall` signatures of batch 4 carried on, `b5-sym-scratch.csv`, built by
`b5-scratch.py`; a reading aid, not symbol rows; decompiles `b5-decompile-main.c`, `b5-decompile-pet.c`,
`b5-decompile-extra.c`) and objdump (`b5-asm.txt`: the ranges `0x005E0390`–`0x005E0430`, `0x005E3900`–`0x005E3930`,
`0x005E3EA0`–`0x005E4D30`, `0x005E9E60`–`0x005E9F10` and `0x005EA290`–`0x005EDC00`, which hold no function of another
batch), then emulation of the twenty-three init and think functions that have a declarable path to their first callee
under ADR-0015/ADR-0021 (§ 4, run:2026-10-30-ai-cat-emu-5). Kept outputs are under `workspace/logs/r52f/` (manifest
`manifest.sha256`, one path base: that directory; the emulation under `emu/`, its own manifest; the development run
under `emu/dev-1/`, its own manifest and tool copy). Stock values come from `b5-rows.txt` (`python3 -I
tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for the 16 rows, 32 records). Every register
argument quoted below was read from objdump (`b5-asm.txt`); the multiplier sites and RNG calls per function are
counted by `b5-draws.py` (`b5-draws.txt`), the 34 `RNG_Range` call windows are `b5-rngsites.txt`, and the callers of
the batch's functions are `b5-helper-refs.txt` (a scan of the whole image's objdump for a `call`, `jmp` or `push` of
each address; other reference forms, a pointer in a data table, not scanned). The machinery is
[ai/0001](0001-machinery.md), the notation and the helpers of batches 1–4 are [ai/0002](0002-pool-a.md) § Notation
and § 4, [ai/0003](0003-pool-b.md), [ai/0004](0004-pool-c.md) and [ai/0005](0005-pool-d.md); names below are
`re/symbols.csv` names.

**Notation** as ai/0002–0005: `G`, `U`, `t` = `ctx+0x08`, `dist` = `ctx+0x14`, `melee` = `ctx+0x18`, `ctl` =
`ctx+0x00`, `M` = `ctx+0x1C`, `T` = `G+0xA8` (the frame), `d` = `G+0x6D`; `aipK` the s16 at `M + 0x56 + 6(K−1) + 2d`,
and `aipK[n]`, `aipK[m]`, `aipK[h]` its Normal, Nightmare and Hell cells read at a fixed offset (`M + 0x56 + 6(K−1)`,
`+2`, `+4`) whatever the difficulty; `SkillK` the s16 at `M + 0x170 + 2(K−1)`, `SkKmode` the byte at
`M + 0x180 + (K−1)`; `draw` one inline step of the acting unit's seed `U+0x20/+0x24`, mod 100; `Range(n)` =
`RNG_Range` on the unit's seed; `v14`, `v18`, `v1C` = `AiCtl+0x14/+0x18/+0x1C`. `O` = `MonsterOwner(U)` (ECX the
unit). Helper short names as before: `SetMode(m, x, y)` (`MonAiSetMode`; `SetMode(0, 0, 0)` commands mode 0, DT, the
summon's end), `SetModeAtUnit(m, u)`, `Idle(n)`, `Delay(n)`, `Walk(t, f)`, `Run(t)` (`MonAiRunToUnit`),
`StepAway(o, n, f)`, `UseSkill(mode, skill, t, x, y)`, `SeqSkill(skill, t, x, y)`, `Ovr(type, param, byte)`,
`FindHostile(&d, &m)`, `FindTarget(ctl, &d, &m)` (`MonAiFindTarget`), `Search(blk, cb, kind)`, `EdgeDist(a, b)`
(`UnitEdgeDistance`), `Dist(a, b)` (`AiDistUnits`), `InTown(u)` (`RoomIsTown(UnitGetRoom(u))`). Skills columns by
offset ([Skills](../../tables/Skills.md)): `+0x048` `srvmissilea`, `+0x064` `aurarangecalc`, `+0x080` `aurastate`,
`+0x082` `auratargetstate`, `+0x0BC` `summon`, `+0x0BE` `pettype`, `+0x144` `calc4`, `+0x14C` `Param2`, `+0x190`
`delay`, `+0x1DC` `EType`, `+0x230` `aitype`, `+0x232` `aibonus`.

## Answer (summary)

- [I] **The batch.** Twenty-three entries (15 think, 8 init functions) for sixteen table rows and state row 7 (ai-rows of P1.1):
  rows 67 and state row 7 share `AiNecroPet` (0x005E4CF0); 84 has an init (0x005E0390); 101 and 104 share the init
  0x005EA290; 105, 106, 107 and 102 have their own init; 110 and 111 share the init 0x005EC6A0; 106 and 143 share the
  think 0x005EB970 with different inits (0x005EB490, 0x005EB5C0). Row kinds: 0 for 67, 84, 101–104, 108, 109 and 112
  (the think runs with no search), 2 for 86, 105–107, 110, 111 and 143 (they run without a target too); no kind-1 row.
  Eighteen helpers sit beside them (and `SkillLevelClamped`, H3's, outside the ranges), among them two shared by most druid and necromancer summons: the pet mover
  `AiPetMove` (0x005E3EA0, 25 call sites) and the pet guard `AiPetGuard` (0x005E45D0, 13 call sites), both called only
  from this batch's functions (`b5-helper-refs.txt`). (data:g_MonAiTable@0x0073CA18, data:g_MonAiStateRows@0x0073D358,
  fn:sub_005B1650_MonAiTargetByKind@0x005B1650)
- [I] **H3: the owner pair reads the owner.** `MonAttackStats(ECX unit, EDX mode)` calls
  `MonOwnerSkillDamage(ECX unit; &blk)` with `blk` three zeroed words (0x005A4F8A–0x005A4F9A). It returns at once
  unless the unit is a monster with an owner `O = MonsterOwner(unit)`, a class below the MonStats count and a
  `SkillDamage` (MonStats `+0xA8`, s16) `s` with `0 < s ≤ Skills count` (`cmp esi,[edx+0xba0]; jg`: `s` equal to the
  count passes); then `SkillDamagePair(ESI s, EDI O; &blk)` (0x0056E0A4–0x0056E0AB). That pair takes **the owner** for
  every term: `lvl = SkillLevelClamped(O, s)` (0x00644AA0, its two stack words the pushed `EDI`/`ESI`,
  0x0056E004–0x0056E006), then `blk[0] = SKILLS_GetPhysMin(O, s, lvl, 1) >> 8`, `blk[1] = SKILLS_GetPhysMax(O, s, lvl,
  1) >> 8` (`sar`, arithmetic), `blk[2] = SKILLS_GetToHit(O, s, lvl)` (0x0056E00B–0x0056E03D). `SkillLevelClamped(u,
  s)`: the entry `SKILLS_FindUnitSkill(u, s)` (none: 0), its base level `+0x28`, plus `0x00644180(entry)` when the
  entry's `+0x34` is −1, then `max(0, ·)` and `min(·, ExpMaxLevel(0))` (0x00644AB1–0x00644AF2). The summon's own level
  is not read. Four stock records have a `SkillDamage`: 419 `druidhawk` (Raven, skill 221), 420 `spiritwolf` (227), 421
  `fenris` (237), 428 `druidbear` (247) (tbl:MonStats.txt:SkillDamage). (fn:sub_005A4F50_MonAttackStats@0x005A4F50,
  fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050, fn:sub_0056E000_SkillDamagePair@0x0056E000,
  fn:sub_00644AA0_SkillLevelClamped@0x00644AA0)
- [I] **The shapes.** Timed summons end by `SetMode(0, 0, 0)` when their `v14` timer passes: 84 `BoneWall` (`v14 =
  T + Param2` of `Skill1`) and 86 `Hydra` (`v14` set elsewhere), 102 `BladeCreeper` (`v14 = T + calc4`). Charged
  summons count `v18` down: 101 `AssassinSentry` and 104 `DeathSentry` load `v18 = calc4(Skill1, level)` shots and
  die at 0, or when the owner is gone or in town. The followers (67, 105–112) keep near the owner through
  `AiPetGuard` and `AiPetMove`, pick a target near the owner and attack it (67, 107, 108, 112 by mode 4 or a skill,
  110 and 111 by `Skill1` on a timer in `v18`); 105 `ShadowWarrior` and 106/143 `ShadowMaster` copy or pick assassin
  skills and score them (§§ 2.10, 2.11); 103 `InvisoPet` teleports (skill 292, `Teleport 2`) around the owner;
  109 `Totem` stays by the owner and teleports to it when farther than `aip3`. (§ 2, fn:sub_005E45D0_AiPetGuard@0x005E45D0,
  fn:sub_005E3EA0_AiPetMove@0x005E3EA0, fn:sub_005EA2B0_AiSentryCharge@0x005EA2B0)
- [C] **The decision maps of the twenty-three emulated functions** (§ 4) from their declared inputs to the first
  callee they reach (or, for the five inits that call nothing, the return) match the emulation in all 5 520 cases of
  23 families: the callee, its call site, its register and stack arguments, the unit seed and `v14`/`v18`/`v1C`. Full
  maps: 84's init and think, 86, 102's init and its think's Skill1 bound, the inits of 101/104, 107 and 110/111, 106
  and 143's think up to the skill-list test, 108's class dispatch. Entry calls only: 67 (and state row 7), 101, 103,
  104, 105 and its init, 106's and 143's inits (with their `AiCtl` stores), 107, 109, 110, 111, 112. The `le`, `d0`,
  `cmp` and `u16` controls and the site control fail every case they separate. The `[C]` ends at that callee
  (ADR-0021). (run:2026-10-30-ai-cat-emu-5, § 4)
- [I] **Draws.** Every draw of the batch's functions is on the acting unit's seed: 12 multiplier-constant loads for 11
  inline steps (row 103 loads it three times for its two steps, its first step with a power-of-two and a modulo
  branch; rows 86, 107's init and 67's two branches one each, 109 two, 106 three), 34 `RNG_Range` calls, each with `ECX` = `U + 0x20` (`b5-rngsites.txt`: a `lea ecx,[r+0x20]` or `add
  ecx,0x20` in the window, or a register set so earlier, 0x005E4C59, 0x005EADD8, 0x005EC219, 0x005EC266); no
  `RNG_RangeB`, `RNG_RangePow2` or `RNG_RandLoHi` (`b5-draws.txt`). Per decision 0–3 in the small rows; row 106/143
  draws in a loop over the unit's skills (§ 2.11), at most two per skill plus three after it. Draws on other seeds can
  come only from callees (the target searches, the move helpers, `PetMove`'s own `Range` draws on the unit seed are
  counted above). No function loops over units with a draw (P1.1 review, reopen condition (b)): the two search
  callbacks, `AiShadowMasterCb` (0x005EB6D0) and `AiPetCrowdCb` (0x005E3900), have no multiplier site and no RNG call in
  their bodies (`b5-draws.txt`: `AiShadowMasterCb 0 0 0 0 7 0 1`, the one `+0x24` store being `param[9] = unit`,
  0x005EB7CA; `AiPetCrowdCb 0 0 0 0 1 0 0`), and none of their direct calls is an RNG entry; their callees are not
  followed. (§§ 2, 3)
- [I] **The `aip8` cells of rows 105 and 106 are three parameters, not a per-difficulty value.** The inits of 105, 106
  and 143 read `aip8[n]` (`+0x80`: 268 `Shadow Warrior`, 279 `Shadow Master`) as a skill id and keep the owner's level
  in it in `v1C`; row 105 reads `aip8[h]` (64) as the cap of its `v18` counter and `AiShadowSkillRoll` reads `aip8[m]`
  and `aip8[h]` (5, 64) as the bounds of the same counter; row 106 reads `aip1[n]`, `aip1[m]`, `aip1[h]`, `aip2[n]`,
  `aip2[m]`, `aip2[h]` at fixed offsets too (0x005EAF72, 0x005EAFFC, 0x005EAE2A, 0x005EAE59, 0x005EB4D2, 0x005EB5EC;
  § 2.11). So `shadowmaster`'s `aip8` = 279 in Normal only is the skill id, read in every difficulty. (tbl:MonStats.txt:aip8)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batches 1–4 (ai/0001–0005) and the
findings named in place are cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005E0390` | `sub_005E0390_AiBoneWallInit` | row 84's init: `v14 = T + Param2(Skill1)` | I (map `[C]`, § 4) |
| `0x005E0400` | `sub_005E0400_AiBoneWall` | row 84 `BoneWall` think | I (map `[C]`, § 4) |
| `0x005E3900` | `sub_005E3900_AiPetCrowdCb` | `AiPetMove` kind 4's callback: counts the other pets within 2 | I |
| `0x005E3EA0` | `sub_005E3EA0_AiPetMove` | `(ECX game, EDX ref; pet, kind, a, speed, dist)`: the summons' move toward or around the owner, kinds 0–5 | I |
| `0x005E45D0` | `sub_005E45D0_AiPetGuard` | `(ECX game, EDX pet; target, owner, melee, ctx, flag, dist)`: picks the `AiPetMove` kind from the owner's distance and state | I |
| `0x005E4830` | `sub_005E4830_AiNecroPetMelee` | row 67's think when `v14` = 0 | I |
| `0x005E4AC0` | `sub_005E4AC0_AiNecroPetRanged` | row 67's think when `v14` ≠ 0 (`Skill1`) | I |
| `0x005E4CF0` | `sub_005E4CF0_AiNecroPet` | row 67 `NecroPet` and state row 7 think | I (entry call `[C]`, § 4) |
| `0x005E9E60` | `sub_005E9E60_AiHydra` | row 86 `Hydra` think | I (map `[C]`, § 4) |
| `0x005EA290` | `sub_005EA290_AiSentryInit` | rows 101, 104 init: `v14 = T`, `v18 = −1` | I (map `[C]`, § 4) |
| `0x005EA2B0` | `sub_005EA2B0_AiSentryCharge` | `(ECX game, EDX unit; ctx, use)`: the sentries' shot count in `v18`; 1 = the sentry was ended | I (entry call `[C]` inside rows 101, 104, § 4) |
| `0x005EA3D0` | `sub_005EA3D0_AiAssassinSentry` | row 101 `AssassinSentry` think | I (entry call `[C]`, § 4) |
| `0x005EA510` | `sub_005EA510_AiBladeCreeperInit` | row 102's init: `v14 = −1`, `v18 = 1`, `v1C = 0` | I (map `[C]`, § 4) |
| `0x005EA540` | `sub_005EA540_AiBladeCreeper` | row 102 `BladeCreeper` think | I (Skill1 bound `[C]`, § 4) |
| `0x005EA7A0` | `sub_005EA7A0_AiInvisoPet` | row 103 `InvisoPet` think | I (entry call `[C]`, § 4) |
| `0x005EA980` | `sub_005EA980_AiDeathSentry` | row 104 `DeathSentry` think | I (entry call `[C]`, § 4) |
| `0x005EAB20` | `sub_005EAB20_AiShadowSkillAllowed` | `(unit, skill)`: a skill whose `summon` is not the unit's class and whose `pettype` the unit's pets do not hold | I |
| `0x005EABF0` | `sub_005EABF0_AiShadowSkillFits` | `(unit, skill, ctx)`: the skill's `aitype` against the target and melee state, and its states | I |
| `0x005EAD50` | `sub_005EAD50_AiShadowSkillRoll` | row 105's skill try: three `Range` draws and the `v18` counter | I |
| `0x005EAF00` | `sub_005EAF00_AiShadowWarriorSkLvl` | `v1C / 3 + level / 2`, at least 1 | I |
| `0x005EAF50` | `sub_005EAF50_AiShadowWarriorInit` | row 105's init: `v1C` = the owner's level in `aip8[n]` | I (entry call `[C]`, § 4) |
| `0x005EAFA0` | `sub_005EAFA0_AiShadowWarrior` | row 105 `ShadowWarrior` think | I (entry call `[C]`, § 4) |
| `0x005EB420` | `sub_005EB420_AiShadowMasterSkLvl` | `(owner, v1C)`: `level / 2 + v1C / 2` in `[1, 24]` | I |
| `0x005EB490` | `sub_005EB490_AiShadowMasterInit` | row 106's init: `v14 = v18 = 0`, `v1C`, the skill list copied from the class | I (entry call `[C]`, § 4) |
| `0x005EB5C0` | `sub_005EB5C0_AiShadowMasterNoInitInit` | row 143's init: `v1C`, the left and right skill only | I (entry call `[C]`, § 4) |
| `0x005EB650` | `sub_005EB650_AiShadowPriorityTarget` | `(ECX self, EDX u)`: a living monster with MonStats `+0x0D` bit 7 set and bit 0 clear that is a boss, a prime evil or of a type flag | I |
| `0x005EB6D0` | `sub_005EB6D0_AiShadowMasterCb` | row 106's search callback: counts and the nearest hostile within 32, 10 and the owner's 10 | I |
| `0x005EB7F0` | `sub_005EB7F0_AiStateGroupHeld` | `(ECX unit, EDX state)`: the unit holds another state of the same States group | I |
| `0x005EB8B0` | `sub_005EB8B0_AiShadowUseSkill` | row 106's skill use (`UseSkill` with the skill's mode, or `RunToUnitFlags` for a melee-range skill out of reach) | I |
| `0x005EB970` | `sub_005EB970_AiShadowMaster` | rows 106 `ShadowMaster` and 143 `ShadowMasterNoInit` think | I (skill-list test `[C]`, § 4) |
| `0x005EC6A0` | `sub_005EC6A0_AiVinesInit` | rows 110, 111 init: `v14 = 0` | I (map `[C]`, § 4) |
| `0x005EC6C0` | `sub_005EC6C0_AiVines` | row 110 `Vines` think | I (entry call `[C]`, § 4) |
| `0x005EC8C0` | `sub_005EC8C0_AiCycleOfLife` | row 111 `CycleOfLife` think | I (entry call `[C]`, § 4) |
| `0x005ECB70` | `sub_005ECB70_AiRavenInit` | row 107's init: `v14 = −1`, `v18 = aip3 + 1`, `v1C` = one draw's bit 0 | I (map `[C]`, § 4) |
| `0x005ECBC0` | `sub_005ECBC0_AiRavenCircle` | `(ECX game, EDX unit; owner, byte, type)`: a mode-1 command around the owner | I |
| `0x005ECC10` | `sub_005ECC10_AiRaven` | row 107 `Raven` think | I (entry call `[C]`, § 4) |
| `0x005ECEE0` | `sub_005ECEE0_AiSpiritWolf` | row 108 for class 420 `spiritwolf` | I (entry call `[C]` inside row 108, § 4) |
| `0x005ED2A0` | `sub_005ED2A0_AiFenris` | row 108 for any other class (421 `fenris`) | I (entry call `[C]` inside row 108, § 4) |
| `0x005ED710` | `sub_005ED710_AiDruidWolf` | row 108 `DruidWolf` think: the class dispatch | I (map `[C]`, § 4) |
| `0x005ED730` | `sub_005ED730_AiDruidBear` | row 112 `DruidBear` think | I (entry call `[C]`, § 4) |
| `0x005ED9E0` | `sub_005ED9E0_AiTotem` | row 109 `Totem` think | I (entry call `[C]`, § 4) |
| `0x00644AA0` | `sub_00644AA0_SkillLevelClamped` | `(unit, skill)`: the unit's level in the skill, bonus included for its own entry, in `[0, ExpMaxLevel(0)]` | I |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`ai-rows.txt` of P1.1, `b5-rows.txt`): 67 `NecroPet` (9 records: `claygolem`, `bloodgolem`,
  `irongolem`, `firegolem`, `valkyrie`, `necroskeleton`, `necromage`, `wolf`, `bear`), 84 `BoneWall` (1), 86 `Hydra`
  (3), 101 `AssassinSentry` (4: `wakeofdestruction`, `chargeboltsentry`, `lightningsentry`, `infernosentry`), 102
  `BladeCreeper` (1), 103 `InvisoPet` (1), 104 `DeathSentry` (1), 105 `ShadowWarrior` (1), 106 `ShadowMaster` (1), 107
  `Raven` (1, `druidhawk`), 108 `DruidWolf` (2: `spiritwolf`, `fenris`), 109 `Totem` (3), 110 `Vines` (1,
  `plaguepoppy`), 111 `CycleOfLife` (2: `cycleoflife`, `vinecreature`), 112 `DruidBear` (1); 143 no record: 32
  records. State row 7 is reached through `AiCtl.state` = 7, which no immediate `MonAiInit` call passes (ai/0001 § 3).
  (tbl:MonStats.txt:AI, data:g_MonAiStateRows@0x0073D358)
- [I] **The PetType rows** ([PetType](../../tables/PetType.md)) group these summons; the AI is the record's: `golem`
  (records 289–292), `valkyrie`, `skeleton`, `skeletonmage` and `revive` (a revived monster keeps its own AI row,
  `MonAiInit` state 0, ai/0001 § 3) go to 67 or their own row; `raven` 107, `spiritwolf` and `fenris` 108, `totem`
  109, `vine` 110/111, `grizzly` 112, `shadowwarrior` 105/106, `assassintrap` 101/104, `hydra` 86, `invis` 103;
  `dopplezon` (356) has AI `Idle` (row 1, P1.1). (tbl:PetType.txt:mclass1, tbl:MonStats.txt:AI)
- [I] None of the 13 rows whose records disagree on which `aip` slots they set (MonStats § AI columns) is in this
  batch; values differ only in rows 67 (`aip1` 60 to 90; `aip2`..`aip4` set on `necroskeleton` and `necromage` only),
  101 (`aip4` 15, 25, 25, 13), and 108 (`aip3` 14/25, `aip4` 20/24, `aip5` 26/30); the rest are one record or share every
  value (`b5-rows.txt`, values `[C]` as data). Rows 105 and 106 read `aip8`'s three cells as three parameters (§ 2.10,
  § 2.11). (tbl:MonStats.txt:aip1, tbl:MonStats.txt:aip4, tbl:MonStats.txt:aip8)
- [I] **The `Sk lvl` 0 records** (plan 0052 P1.2, folded in at the `lane/a52` review): `bloodgolem` (`BloodGolem`,
  Skill1) and `bonewall` (`Bone Wall`, Skill1), `chargeboltsentry` and `infernosentry` (Skill2 `Shock Field` and `Wake
  of Fire Sentry`), `druidhawk` (`Raven`, Skill1). Row 67 reads `Skill1` only in its ranged branch (`v14` ≠ 0),
  which a golem takes only if its `v14` is set (open question); row 84 reads `Skill1`'s `Param2` (a table cell, not the
  level); row 101 uses `Skill1` only; row 107 passes `Skill1` to `SKILLS_GetUnitSkill(O, ·)` and reads the **owner's**
  level in it (§ 2.9). So in this batch a `Sk lvl` of 0 never feeds a level the think function reads.
  (fn:sub_005E4AC0_AiNecroPetRanged@0x005E4AC0, fn:sub_005E0390_AiBoneWallInit@0x005E0390,
  fn:sub_005ECC10_AiRaven@0x005ECC10)

### 2. The think and init functions

#### 2.1 Row 84 `BoneWall` (init 0x005E0390, think 0x005E0400) and row 86 `Hydra` (fn:sub_005E9E60_AiHydra@0x005E9E60, 0x005E9E60)

```c
init84: if (M && (s = Skill1) > 0) {                        // movzx; test ax,ax; jle (s16)
            rec = (s < SkillsCount) ? SkillsRec + 0x23C·s : 0;
            v14 = T + (rec ? rec->Param2 : 0); }
think84: if (v14 < T) SetMode(0, 0, 0); else Idle(15);      // signed
think86: if (v14 < T) return SetMode(0, 0, 0);
         if (t && dist < 25 && draw < 60) return UseSkill(Sk1mode, Skill1, t, 0, 0);
         Idle(10);
```

- [C] As written, with every compare signed; row 86's draw at the constant 60 (no `aip`), one step, only when `t` is
  set and `dist < 25`. (run:2026-10-30-ai-cat-emu-5, `bwinit`, `bwall`, `hydra`; 0x005E03A0–0x005E03F1,
  0x005E040B–0x005E0424, 0x005E9E75–0x005E9F01)
- [I] The bone wall's life is its `Skill1`'s `Param2` in frames from its AI init (the stock `Bone Wall` row);
  the hydra's `v14` is not set by its row (no init): its writer is not read here. (tbl:Skills.txt:Param2,
  fn:sub_005E9E60_AiHydra@0x005E9E60)

#### 2.2 Row 67 `NecroPet` (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0, 0x005E4CF0) and state row 7

```c
UNIT_CancelEvents(G, U; 2, 0);
if (v14 != 0) NecroPetRanged(ctx); else NecroPetMelee(ctx);
```

- [C] The entry call `UNIT_CancelEvents(2, 0)` from 0x005E4CFD with `ECX` game, `EDX` the unit, before any test.
  (run:2026-10-30-ai-cat-emu-5, `necropet`)
- [I] **Melee** (0x005E4830): with no owner, `PetMove(GameFindUnit(v1C); U, 3, 0, 0, 0)` when the remembered owner
  guid `v1C` still finds a unit, else `Idle(10)`. Else `v1C = O+0x0C` (the owner's guid); `r = Dist(U, O)`; `r > 50`:
  `PetMove(O; U, 3, …)` (kind 3, the teleport); the run speed `s = Run·100/Velocity − 100` (100 when `Velocity` < 1 or
  `s` > 99); `r ≥ 29`: `PetMove(O; U, 0, 0, s, 0)`. Inside 29: the target is `FindTarget(ctl)` (dropped if its
  `+0xC4` bit 30 is set) or the owner-near hostile of 0x005DDE50 (radius 24) when the distance it returns is at most 6, else the
  found target when within 36; dropped when `AiApproachPointTest` fails; then **draw#1** `≥ 15` gives `AiPetGuard(t, O,
  melee, ctx, 0, 7)`, `< 15` gives `(…, 1, 8)`; when that commands nothing and `t` is set outside town: in melee
  **`Range(100)` ≥ 80** idles 10, else `SetModeAtUnit(4, t)`; out of melee `Ovr(0, 0, 12)` and `Walk13(t, 7)`. No `t`
  or in town: `WanderRingDirect(O, 4)`, or `Idle(20)` when only the unit is in town. (fn:sub_005E4830_AiNecroPetMelee@0x005E4830, 0x005E4830–0x005E4ABC,
  fn:sub_005DD7F0_MonAiFindTarget@0x005DD7F0, fn:sub_005DC640_AiApproachPointTest@0x005DC640)
- [I] **Ranged** (0x005E4AC0): the same owner block; the target is the hostile of `FindHostile` within 15, else the
  `FindTarget` one when no line of sight blocks (`UnitLineBlocked(U, t, 4)` = 0) and within 20; draw#1 as melee's
  for `AiPetGuard`; then outside town **`Range(100)` < 80** uses `UseSkill(Sk1mode, Skill1, t, 0, 0)`, else a second
  **`Range(100)` ≥ 75** gives `T56(t, 3, 0)`, else `Idle(10)`. (0x005E4AC0–0x005E4CE8)
- [I] Which code sets `v14` for a necromancer's pet is not read (row 67 has no init; the summon skill's do function
  or `SpawnOwnedMonster` are candidates): open question. (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0)

#### 2.3 The pet guard `AiPetGuard` (0x005E45D0) and the pet mover `AiPetMove` (0x005E3EA0)

- [I] **Guard** `(ECX game, EDX pet; t, O, melee, ctx, flag, dist)`: `dist += PlayerData-based 0x00574F40(O) >> 1`,
  capped at 36; `r = Dist(pet, O)`. With `r < 2`, the owner in mode 1 and no `melee`: `PetMove(kind 5)`. With `t` and
  the pet outside town: 0 (the caller acts) while `r ≤ 80`, else kind 3. Otherwise the kind is 2 (stand), set to 0
  when the owner walks or runs (modes 2, 3, 6) or its path has a target point off both axes, 1 when the two are in
  different logic regions or `r > dist`, 3 when `r > 50`; when the owner's path is within 28 of its player-data point
  (`+0x14C`) kind 1 with `r ≤ 29`, or kind 2, become 4; with `flag` and kind 2 the guard returns 0; else
  `PetMove(kind, 0, 0, dist)`. No draw in the guard itself (`b5-draws.txt`: `AiPetGuard 0 0 0 0 21 0 0`).
  (fn:sub_005E45D0_AiPetGuard@0x005E45D0, 0x005E45D0–0x005E482A, fn:sub_0061B130_LogicRegionIdAt@0x0061B130)
- [I] **Mover** `(ECX game, EDX ref; pet, kind, a, speed, dist)`, returning 1 when it commanded: kind 0 walks to a
  point eight subtiles out in the owner's direction class (an eight-direction search of free points in the owner's
  region), kind 1 runs toward the owner's path target with `speed`, or `40 + Range(40)` when `speed` is 0, kind 2
  wanders: **`Range(100)` < 10** gives `WanderRingDirect(ref, 3 + Range(3))`, kind 3 teleports the pet next to the
  owner (`SpawnPosPick` for class 363 or 0, `UnitTeleport`, `+0xC8 |= 0x10000`, `Idle(5)`), kind 4 steps away when
  another pet of the owner stands within 2 (`AiPetCrowdCb` over the owner's pet list `0x00574DE0`), kind 5
  `Ovr(7, 0, 0)` and `WanderNearUnit(ref, dist)`. Its three `Range` calls are on the pet's seed (0x005E41E8,
  0x005E438E, 0x005E43A0). (fn:sub_005E3EA0_AiPetMove@0x005E3EA0, 0x005E3EA0–0x005E45C8, fn:sub_00554EA0_UnitTeleport@0x00554EA0)

#### 2.4 Rows 101 `AssassinSentry` (fn:sub_005EA3D0_AiAssassinSentry@0x005EA3D0, 0x005EA3D0) and 104 `DeathSentry` (fn:sub_005EA980_AiDeathSentry@0x005EA980, 0x005EA980), init 0x005EA290, the charge 0x005EA2B0

```c
init: v14 = T; v18 = -1;
charge(ctx, use):                                      // 1: the sentry was ended
    if (!O || !UnitGetRoom(O) || InTown(O)) { SetMode(0,0,0); return 1; }
    if (v18 < 0) { if (Skill1 not a Skills row) goto end;
                   sk = SKILLS_GetUnitSkill(U, Skill1); if (!sk) { SetMode(0,0,0); return 1; }
                   v18 = EvalCalc(U, calc4, Skill1, SkillLevel(U, sk, 1)); }
    if (v18 > 0) { if (use) v18--; return 0; }
end: SetMode(0,0,0); return 1;
think101: if (charge(ctx,0)) return; sk = SKILLS_GetUnitSkill(U, Skill1); if (!sk) return SetMode(0,0,0);
    if (HasState(U, 12)) STATE_Set(U, 12, 0);
    h = FindHostile(&d, &m); if (!h || d >= aip4) return Idle(aip3);
    if (Range(100) >= aip1) return Idle(aip2);                   // draw#1
    if (charge(ctx,1)) return; UNIT_CancelEvents(2,0); UseSkill(SkillMode(sk), Skill1, h, 0, 0);
think104: if (charge(ctx,0)) return; sk = Skill1's unit skill; lvl = SkillLevel(U, sk, 1); if (!sk || lvl < 1) return;
    h = FindHostile(&d, &m); if (!h) return Idle(aip2);
    c = CorpsePickNear(Skill1, lvl); r = SkillParam3ByLevel(...) / 2;
    if (c && c->guid != v14 && EdgeDist(h, c) < r) { if (charge(ctx,1)) return; v14 = c->guid; return UseSkill(9, Skill1, c, 0, 0); }
    if (d < aip4 && Range(100) < aip3) { if (charge(ctx,1)) return; return UseSkill(14, Skill2, h, 0, 0); }   // draw#1
    Idle(aip2);
```

- [C] The init's two stores and return; the entry call of both thinks: `charge` reaches `MonsterOwner` from 0x005EA2C1
  with `ECX` the unit, before any test. (run:2026-10-30-ai-cat-emu-5, `sentinit`, `asentry`, `dsentry`)
- [I] As written; the sentries' `aip1` is 100 in all four records, so row 101's draw never refuses (one draw per
  shot); `v18` is the shot count from `calc4` at the sentry's own level. Row 104's `v14` is the last corpse it
  exploded (so it never explodes the same corpse twice running); its mode 9 and 14 are passed as immediates.
  (fn:sub_005EA2B0_AiSentryCharge@0x005EA2B0, 0x005EA2B0–0x005EA3C4, 0x005EA3D0–0x005EA507, 0x005EA980–0x005EAB14, tbl:Skills.txt:calc4)

#### 2.5 Row 102 `BladeCreeper` (init 0x005EA510, think 0x005EA540)

```c
init: v14 = -1; v18 = 1; v1C = 0;
think: s = Skill1; if (s < 0 || s >= SkillsCount || !rec(s) || !(sk = SKILLS_GetUnitSkill(U, s))) return SetMode(0,0,0);
    lvl = SkillLevel(U, sk, 1);
    if (v14 < 0) v14 = EvalCalc(U, calc4, s, lvl) + T;
    if (T > v14) return SetMode(0,0,0);
    if (v1C == 0 && 0 <= srvmissilea < MissilesCount) { p = O ? O : U;
        m = MissileCreateAt(s, lvl, srvmissilea, U.x, U.y); if (m) { UnitSetOwner(m, U); stat 19 += PlayerBaseToHit(p);
            stat 119 += p.stat119 + mastery bonus of p's weapon; } v1C = 1; }
    if (!(prm = AiParamsHead())) return Idle(3);
    Ovr(15, 0, 20); walk to point v18 ? (prm+0x14,+0x18) : (prm+0x0C,+0x10); if refused { v18 = !v18; walk to the other; }
    if both refused and !WanderNearUnit(O, 5) Idle(5);
```

- [C] The init; the think's Skill1 bound (`s < 0` by `jl`, `s ≥ count` by `jge`, a null record) to `SetMode(0, 0, 0)`
  at 0x005EA58F or `SKILLS_GetUnitSkill(ECX unit, EDX s)` at 0x005EA5A1, Skill1 sign-extended (`movsx`).
  (run:2026-10-30-ai-cat-emu-5, `bladeinit`, `blade`)
- [I] The rest as written (0x005EA5A6–0x005EA79A): the creeper shuttles between the two points of its parameter
  record until its `calc4` life passes; the stats 19 and 119 go on the missile's owner chain (the creeper), from the
  owner's to-hit (fn:sub_0058EE80_AiParamsHead@0x0058EE80, fn:sub_0056EDE0_MissileCreateAt@0x0056EDE0).

#### 2.6 Row 103 `InvisoPet` (0x005EA7A0)

```c
O = MonsterOwner(U); r = aip1; om = O ? O->mode : 0; if (om == 3) r /= 2;     // owner running
if (T <= v14 && om != 3 && !AiMonState3or19(U)) return Idle(aip2);
x = O.x + R(2r) - r; y = O.y + R(2r) - r;          // R(n): one inline step, & (n-1) when n is a power of 2, else mod n; 0 for n < 1
UseSkill(9, 292, 0, x, y); v14 = T + aip2;          // 292 Teleport 2
```

- [C] The entry call `MonsterOwner` from 0x005EA7C0, before any test. (run:2026-10-30-ai-cat-emu-5, `inviso`)
- [I] As written: two steps per teleport (0x005EA884, 0x005EA8A1, 0x005EA903); `r / 2` is a signed division (`cdq;
  sub; sar`, 0x005EA7F2–0x005EA7F5, rounds toward zero). With no owner the function reads `[0]` (`*O`, `mov eax,[ebx]` at 0x005EA836): a fault on that path,
  which the stock summon reaches only if its owner is gone. (fn:sub_005EA7A0_AiInvisoPet@0x005EA7A0, 0x005EA7A0–0x005EA97C)

#### 2.7 Rows 110 `Vines` (0x005EC6C0) and 111 `CycleOfLife` (0x005EC8C0), init 0x005EC6A0

- [C] The init stores `v14 = 0` and returns; both thinks call `MonsterOwner` first (0x005EC6DD, 0x005EC8DD).
  (run:2026-10-30-ai-cat-emu-5, `vinit`, `vines`, `cycle`)
- [I] **Vines** (poppy): no owner → `Idle(25)`. Farther than `aip5` (edge distance) from the owner, `PetMove(kind 3,
  dist 6)` first. Outside town: the `FindHostile` target dropped when `d ≥ aip2`; `AiPetGuard(t, O, m, ctx, 0, 6)`;
  then a target in state 2 or with stat 45 = 100 is stepped away from (`StepAway(t, (u8)aip4, 0)`), a non-melee one
  walked to (`Walk(t, 7)`), a melee one hit with `UseSkill(Sk1mode, Skill1, t, 0, 0)` once `T > aip1 + v18` (then
  `v18 = T`); else `Idle(aip3)`. In town: `AiPetGuard(0, O, 0, ctx, 0, 6)` or `Idle(aip3)`. No draw.
  (fn:sub_005EC6C0_AiVines@0x005EC6C0, 0x005EC6C0–0x005EC8B5)
- [I] **CycleOfLife**: no owner → return (no command). The target is the corpse of `0x005D2F80(O, r)` with `r =
  calc of aurarangecalc` clamped to `[5, 50]` when `Skill1` > 0, kept while its edge distance is below `aip2`; the
  class word (426, 427) picks the owner's life (stat 6 against its maximum) or mana (stat 8): at full, no cast. A corpse
  in melee range, the owner short of the stat and `T > aip1 + v18`: `UseSkill(8, Skill1, c, 0, 0)`, `v18 = T`; else
  with an event target in `melee`, **`Range(100)` < 25** steps away (`StepAway(t, (u8)aip4, 0)`); else `Idle(aip3)`
  without a corpse or `Walk(c, 7)`. (fn:sub_005EC8C0_AiCycleOfLife@0x005EC8C0, 0x005EC8C0–0x005ECA9C, tbl:Skills.txt:aurarangecalc)

#### 2.8 Row 109 `Totem` (0x005ED9E0)

```c
if (!O) return Idle(10);
h = OwnerNearHostile(ctl, &d, &m, 24);                                   // 0x005DDE50
if (m && h && draw < aip1 && StepAway(h, 6, 1)) return;                 // draw#1
if (draw < aip2) { h = 0; m = 0; }                                      // draw#1 or #2
e = EdgeDist(U, O);
if (e > aip3 && UnitTeleport(room(O), O.x, O.y, 0, 0)) return Idle(25);
if (e > aip4) { owner mode 2 or 6: PetMove(kind 0) ; mode 3: PetMove(kind 0, speed 60) }  // each returns on a command
if (!AiPetGuard(h, O, m, ctx, 0, 6)) Idle(25);
```

- [C] The entry call `MonsterOwner` from 0x005ED9EF. (run:2026-10-30-ai-cat-emu-5, `totem`)
- [I] As written: one or two inline steps (0x005EDA3D, 0x005EDA96), the first only when `m` and `h` are set.
  (fn:sub_005ED9E0_AiTotem@0x005ED9E0, 0x005ED9E0–0x005EDBF5)

#### 2.9 Row 107 `Raven` (init 0x005ECB70, think 0x005ECC10, circle 0x005ECBC0)

```c
init: v14 = -1; v18 = aip3 + 1; v1C = draw-step low & 1;        // one inline step (no mod)
think: if (!O || !M) return Idle(10);
    if (v14 == -1) { v14 = 3; if (Skill1 >= 0) v14 = SkillParam5ByLevel(Skill1, SkillLevel(O, SKILLS_GetUnitSkill(O, Skill1), 1)); }
    else if (v14 == 0) return UnitKilled(U, 1);                  // hits used up
    r = Dist(U, O); if (r > 50) return PetMove(O; U, 3, 0, 0, 0);
    s = run speed as § 2.2; if (r > 28) return PetMove(O; U, 0, 0, s, 0);
    FindTarget(ctl, &e, &m'); ...; mid = (aip2 + aip1) / 2;
    if (t && v18 < T && Range(100) < aip4 && dist < aip5) {        // draw#1
        if (melee) { SetModeAtUnit(4, t); v14--; v18 = T + 10·aip3; return; }
        return Walk(t, 0); }
    if (aip1 >= r && r >= aip2) { circle(O, 4, v1C ? 5 : 6) or flip v1C and circle again; }   // each returns on a command
    if (!WalkAround(ctl, O, mid)) PetMove(O; U, 1, 0, 0, 0);    // 0x005DE6F0
```

- [C] The init: its stores and one seed step, `v1C` the step's low word bit 0, `v18` = `aip3` (s16) + 1 by difficulty.
  The think's entry call `MonsterOwner` from 0x005ECC27. (run:2026-10-30-ai-cat-emu-5, `ravinit`, `raven`)
- [I] The think as written (0x005ECC10–0x005ECED6): `v14` is the raven's hit count, read from `Skill1` (`Raven`) at
  **the owner's** level in it (`SkillParam5ByLevel`), and the raven dies (`UnitKilled(U, 1)`) when it reaches 0;
  each attack is `SetModeAtUnit(4, t)` with the cooldown `v18 = T + 10·aip3`. So every raven attack runs mode 4 through
  `MonSetMode`, whose `MonAttackStats` adds the owner pair of the Answer's H3 bullet (`SkillDamage` = `Raven`, the
  owner's level in it): **the inputs of H3's 2 218 Raven calls are the owner's skill entry for skill 221, the owner's
  level in it, and the Raven rows of `SKILLS_GetPhysMin`, `GetPhysMax` and `GetToHit`** (fn:sub_005A7C20_MonSetMode@0x005A7C20,
  fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050). The 2 218 calls themselves are Phase 2's (plan 0052 § P2).

#### 2.10 Row 105 `ShadowWarrior` (init 0x005EAF50, think 0x005EAFA0)

- [C] The init stores `v1C = 1` and calls `MonsterOwner` (0x005EAF64); the think calls `UNIT_CancelEvents(2, 0)`
  first (0x005EAFCF). (run:2026-10-30-ai-cat-emu-5, `swinit`, `swarrior`)
- [I] **Init**: with an owner, `v1C` = the owner's level in skill `aip8[n]` (`SKILLS_GetUnitSkill(O, aip8[n])`, 268,
  0x005EAF72). **Think**: no owner → `Idle(100)`. `cap = clamp(aip8[h], 1, 256)`; `v18 += −1 − aip4`, reset to 0 when
  below 0 or above `64·cap`. The event target is dropped when `dist > aip1` or the owner is farther than `aip2`;
  `AiPetGuard(t, O, melee, ctx, 0, 6)`. With a target and both owner skills set: the owner's right and left skills are
  added to the unit at `AiShadowWarriorSkLvl` (`v1C / 3 + level / 2`, at least 1) (0x00647280, `.\Ai\AiThink4.cpp`
  lines 0xB59, 0xB5A), **`Range(2)`** picks one of the two, `p = clamp(aip3 − 2·max(v1C, 1), 5, 100)`, in melee
  **`Range(100)` < p** replaces it with the unit's skill 0 (its attack); `AiShadowSkillRoll` tries it, then the other;
  failing both, the skill-0 entry (added at level 1 when missing). The chosen skill: not a melee-range type (`RangeType
  ≠ 1`) or in melee: `UseSkill(SkillMode(sk), id, t, 0, 0)` and `v14 = T + 18 + delay(sk, level) / 3`; else `Run(t)`.
  No target: `Idle(25)`. (fn:sub_005EAFA0_AiShadowWarrior@0x005EAFA0, 0x005EAFA0–0x005EB41C)
- [I] **`AiShadowSkillRoll`** `(owner, skill, id, melee, ctx)`: 0 when the id is not the owner's class's skill
  (`0x00645040(id)` ≠ `O+0x04`) or `AiShadowSkillFits` refuses; 1 for id 0; else with `q = 0x006459F0(id, level)`:
  **`Range(100)` > 100 − 160·q/100** refuses, `T < v14` refuses, then `v18` is reset to `lo = clamp(aip8[m], 1, 128)`
  when outside `[lo, 32·clamp(aip8[h], 1, 256)]`, **`Range(v18)`** against **`Range(100)`**: the second below the
  first refuses; else `v18 += (320 − v1C)·q / (v1C + 100)` and 1. So three draws per tried skill.
  (fn:sub_005EAD50_AiShadowSkillRoll@0x005EAD50, 0x005EAD50–0x005EAEFA)

#### 2.11 Rows 106 `ShadowMaster` and 143 `ShadowMasterNoInit` (think 0x005EB970; inits 0x005EB490, 0x005EB5C0)

- [C] Both inits' stores before their `MonsterOwner` call (106: `v14 = v18 = 0`, `v1C = 1`, 0x005EB4B4; 143: `v1C =
  1`, 0x005EB5D6); the think: `U+0xA8` (the skill list head) zero → `Idle(100)` at 0x005EB9B8, else `MonsterOwner`
  from 0x005EB9C8. (run:2026-10-30-ai-cat-emu-5, `sminit`, `sm2init`, `smaster`)
- [I] **Inits**: for a player owner (`O+0x00` = 0), `v1C` = the owner's level in `aip8[n]` (279); the skill-0 entry is
  added at level 1 when missing, and the left and right skills set to 0; row 106's init then copies every skill of the
  unit's class (`0x00646140` count, `0x006460F0` per index) that `AiShadowSkillAllowed` admits, at
  `AiShadowMasterSkLvl(O, v1C)` (`level/2 + v1C/2`, in `[1, 24]`). Row 143's init does not copy them: 143 is the
  record-less row whose think is 106's (ai/0001 § 3: no MonStats record names it). (fn:sub_005EB490_AiShadowMasterInit@0x005EB490, 0x005EB490–0x005EB5B8,
  0x005EB5C0–0x005EB644)
- [I] **Think**: `CancelEvents(2, 0)`; farther from the owner than `aip2[h]²` (DistSq) and `AiPetGuard(0, O, melee,
  ctx, 0, 6)` commanding: return. A pending sequence (`v14 > 0`): the unit's target unit (or the event's) gets
  `AiShadowUseSkill(v18)` and `v14−−`. Then, unless a target within `aip2[m]` (or none) holds it, **a loop over the
  unit's skills**: an `aitype` 1 (self state) skill whose `aurastate` the unit lacks and whose state group it does
  not hold (or **`Range(100)` < 4** when it does) gets **draw < 60** and `UseSkill(skill's mode, id, 0, 0, 0)` (or
  `RunToUnitFlags` for a melee-range skill out of melee); an `aitype` 6 skill with no left skill set gets **draw < 20**
  to become the left skill. Then the owner's target, the nearest hostile of `Search(blk, AiShadowMasterCb, 1)`
  (within 32: counts within 10 of the unit and of the owner, the nearest, a priority target), `p = clamp(aip3 −
  2·max(v1C, 1), 5, 100)` with **`Range(100)` < p** in melee for the plain attack, a crowd test (**`Range(32)` <
  2·count** when more than 3 hostiles are within 10: run to the owner or step away 8), and **the scoring loop**: per
  skill a score from `aibonus`, `reqlevel/4`, the level, the target's resistance to the skill's `EType` (stats 36, 39,
  41, 37, 43, 45: `−res/10` by the `0x66666667` multiply), and per `aitype` (1–8, 11–13) its terms and one
  **`Range(aip2[n])`** draw (20 for `shadowmaster`), the five best kept in a frame table; last a draw `& 3` picks among
  them, and `AiShadowUseSkill` runs the choice. `Idle(15)` when nothing commands. The loop runs over skills, not
  units, with at most two draws per skill in the first loop and one in the second (`b5-draws.txt`: 3 inline steps,
  14 `RNG_Range`). (fn:sub_005EB970_AiShadowMaster@0x005EB970, 0x005EB970–0x005EC694, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0)

#### 2.12 Rows 108 `DruidWolf` (0x005ED710; 0x005ECEE0, 0x005ED2A0) and 112 `DruidBear` (0x005ED730)

- [C] Row 108 is a class dispatch: class 420 (`spiritwolf`, `cmp [edx+4],0x1a4; jne`) jumps to 0x005ECEE0, any other
  class to 0x005ED2A0; each calls `MonsterOwner` first (0x005ECEFD, 0x005ED2BD). Row 112 calls `MonsterOwner` first
  (0x005ED747). (run:2026-10-30-ai-cat-emu-5, `dwolf`, `bear`)
- [I] **Spirit wolf**: no owner → with the remembered owner found and `Skill1` set, `UseSkill(Sk1mode, Skill1, 0,
  U.x, U.y)` (its `Teleport 2`), an event at `T + 6` and `Delay(8)`; else `Idle(10)`. In town: `AiPetGuard(0, O, …)` or
  `Idle(33)`. Else the target of 0x005DDE50 within `aip4` or the `FindTarget` one, each kept if
  `AiApproachPointTest` passes; farther than 50 from the owner with `Skill1`: the teleport (event `T + 4`, `Delay(10)`);
  the `PetMove` and `AiPetGuard(…, 1, 6)` chain by the distance and the owner's mode; then in melee `SetModeAtUnit(4,
  t)` and `Delay(aip1)`, a target within `aip4` of the owner `Ovr(0, s, 0)` and `Run(t)`, farther than 10
  `WalkToward(O, 8, 6)`, else `Idle(15)`; no target: **`Range(100)` < `aip2`** wanders (`Ring(10)`), else `Idle(15)`.
  (fn:sub_005ECEE0_AiSpiritWolf@0x005ECEE0, 0x005ECEE0–0x005ED29A)
- [I] **Fenris** (0x005ED2A0): the same frame with `Skill2` as the teleport; then, unless state 138 is set or
  **`Range(100)` ≥ `aip3`** with a target and `v14` = 0, the corpse `0x005D2F80(O, 10)` within `aip4/2` is eaten with
  `UseSkill(Sk1mode, Skill1, c, 0, 0)` in melee (`v14 = 0`) or run to (`v14 = 1`, `v18` = its guid); then as the
  wolf, with **`Range(100)` < `aip2`** for the wander. Two draws at most. (fn:sub_005ED2A0_AiFenris@0x005ED2A0, 0x005ED2A0–0x005ED70A)
- [I] **Bear**: the owner block as § 2.2 (kinds 3 and 0 at 50 and 28, kind 0 by the owner's mode beyond 18); the
  target of 0x005DDE50 within 28 or `FindTarget`'s within 28, kept if `AiApproachPointTest` passes; out of melee
  **`Range(100)` < `aip2`** sets `Ovr(0, s, 40)`, then `WalkToUnitOrZero(t)`; in melee **`Range(100)` < `aip3`** uses
  `SeqSkill(Skill1, t, 0, 0)` (`BearSmite`), else `SetModeAtUnit(4, t)` and `Delay(aip1)`; no target: `Idle(15)`
  within 16, else `PetMove(kind 0)`. (fn:sub_005ED730_AiDruidBear@0x005ED730, 0x005ED730–0x005ED9DA)

### 3. Callers and the helpers

- [I] **Callers** (`b5-helper-refs.txt`): no direct reference to the 23 table and state-row entries (they are reached
  through `g_MonAiTable`/`g_MonAiStateRows` and `MonAiInit`); `AiPetMove` from 25 sites and `AiPetGuard` from 13, all
  in this batch's functions; `AiNecroPetMelee`/`Ranged` once each, from 0x005E4D1D/0x005E4D12; `AiSentryCharge` 5
  times (rows 101, 104); `AiShadowSkillAllowed` twice (0x005EAC2C in `AiShadowSkillFits`, 0x005EB55F in row 106's
  init), `AiShadowSkillFits` once (0x005EADB0), `AiShadowSkillRoll` twice (0x005EB227, 0x005EB25C),
  `AiShadowWarriorSkLvl` twice, `AiShadowMasterSkLvl` once, `AiShadowPriorityTarget` twice, `AiShadowMasterCb` pushed
  once (0x005EBD53), `AiStateGroupHeld` twice, `AiShadowUseSkill` 4 times, `AiRavenCircle` twice, the wolf and fenris
  entries once each by jumps from row 108 (0x005ED721, 0x005ED727), `AiPetCrowdCb` pushed twice inside `AiPetMove`
  (0x005E3D8D, 0x005E44C4). `MonOwnerSkillDamage` is called once, from `MonAttackStats` (0x005A4F9A); `SkillDamagePair`
  once (0x0056E0AB); `SkillLevelClamped` once (0x0056E006). The hireling think (state row 4, batch 6) uses
  `0x005E3930`, not `AiPetMove` (`b5-helper-refs.txt`: its five calls lie in 0x005E5446–0x005E561C).
  (fn:sub_005E0400_AiBoneWall@0x005E0400, fn:sub_005E3900_AiPetCrowdCb@0x005E3900, fn:sub_005EA290_AiSentryInit@0x005EA290, fn:sub_005EA510_AiBladeCreeperInit@0x005EA510, fn:sub_005EA540_AiBladeCreeper@0x005EA540, fn:sub_005EAB20_AiShadowSkillAllowed@0x005EAB20, fn:sub_005EABF0_AiShadowSkillFits@0x005EABF0, fn:sub_005EAF00_AiShadowWarriorSkLvl@0x005EAF00, fn:sub_005EAF50_AiShadowWarriorInit@0x005EAF50, fn:sub_005EB420_AiShadowMasterSkLvl@0x005EB420, fn:sub_005EB5C0_AiShadowMasterNoInitInit@0x005EB5C0, fn:sub_005EB650_AiShadowPriorityTarget@0x005EB650, fn:sub_005EB6D0_AiShadowMasterCb@0x005EB6D0, fn:sub_005EB7F0_AiStateGroupHeld@0x005EB7F0, fn:sub_005EB8B0_AiShadowUseSkill@0x005EB8B0, fn:sub_005EC6A0_AiVinesInit@0x005EC6A0, fn:sub_005ECB70_AiRavenInit@0x005ECB70, fn:sub_005ECBC0_AiRavenCircle@0x005ECBC0, fn:sub_005ED710_AiDruidWolf@0x005ED710)
- [I] No function of the batch calls the action helpers 0x005DF850, 0x005DF990, 0x005DFA00 or 0x005DFBF0 (`grep -c
  'call   0x5df850\|call   0x5df990\|call   0x5dfa00\|call   0x5dfbf0' b5-asm.txt`: 0); row 102 calls
  `AiParamsHead` (0x0058EE80) once. (`b5-asm.txt`)

### 4. Emulation (run:2026-10-30-ai-cat-emu-5)

- [C] Twenty-three families, 240 cases each, 5 520 cases, all matching, none stopped, no traced access outside the
  declared memory (`emu/check.txt`). Each case runs one function on a declared image (the docstring of
  `tools/ai_cat_emu5.py`) and ends at the first observed callee or, for the five inits that call nothing, at the
  return; the checker compares the callee, the call site (the return address), `ECX`/`EDX` where the callee takes them,
  the stack arguments, the unit seed and `v14`/`v18`/`v1C`. Controls: `le` (each draw compared with `<=`), `d0`
  (every `aip` from the Normal column), `cmp` (every compare that is not a draw with its strictness switched), `u16`
  (Skill1 read unsigned) fail every case they separate, and the site control (each call site one byte later) fails
  every case that ends at a callee (the return families have no site; the control separates nothing there)
  (run:2026-10-30-ai-cat-emu-5):

  | family | row | outcomes (site: cases) | drew | `le` | `d0` | `cmp` | `u16` | compares met at equality (`EDGES`) |
  |---|---:|---|---:|---:|---:|---:|---:|---|
  | `bwinit` | 84 init | return 240 | 0 | 0 | 0 | 51 | 94 | `s<=0` 35, `s<count` 25 |
  | `bwall` | 84 | SetMode 100, Idle 140 | 0 | 0 | 0 | 44 | 0 | `v14<T` 44 |
  | `necropet` | 67, st 7 | CancelEvents 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `hydra` | 86 | SetMode 62, UseSkill 51, Idle 127 | 121 | 21 | 0 | 58 | 0 | `v14<T` 52, `dist<25` 10, `draw<60` 21 |
  | `sentinit` | 101, 104 init | return 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `asentry` | 101 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `bladeinit` | 102 init | return 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `blade` | 102 | SetMode 162, GetUnitSkill 78 | 0 | 0 | 0 | 12 | 46 | `s<count` 12 |
  | `inviso` | 103 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `dsentry` | 104 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `swinit` | 105 init | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `swarrior` | 105 | CancelEvents 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `sminit` | 106 init | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `sm2init` | 143 init | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `smaster` | 106, 143 | Idle 116, MonsterOwner 124 | 0 | 0 | 0 | 0 | 0 | — |
  | `vinit` | 110, 111 init | return 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `vines` | 110 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `cycle` | 111 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `ravinit` | 107 init | return 240 | 240 | 0 | 153 | 0 | 0 | — |
  | `raven` | 107 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `dwolf` | 108 | MonsterOwner at 0x005ECF02 91, at 0x005ED2C2 149 | 0 | 0 | 0 | 0 | 0 | — |
  | `bear` | 112 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |
  | `totem` | 109 | MonsterOwner 240 | 0 | 0 | 0 | 0 | 0 | — |

  The `le` … `u16` columns count the cases each control separates (it passed none). Every threshold compare of the
  covered maps is met at equality in at least one case (the `EDGES` lines of `check.txt`), so each has a strictness
  control. **Edges with no control:** the `==`/`!=` and null tests (row 102's null record and 84's, both met by a
  records pointer that puts the case's record at address 0; row 106's skill-list test; row 108's class test, met at
  419, 420 and 421; the hydra's target test) and the sign tests of `s < 0`: a wrong reading of these gives another
  boundary or site on the cases that hold the other value, but no control moves their edge. The entry families take
  no draw and no compare before their call: no control separates them, and their `[C]` is the call's site and
  arguments and the `AiCtl` words stored before it. Not covered: every callee and everything after it.
  (run:2026-10-30-ai-cat-emu-5)
- [I] **The development run** (rule 6): `emu/dev-1/` (5 520 cases, all matching, every control failing every case it
  separates, with the case writer before two tunings: a Skills count of 0x10000 for `bwinit` and `blade`, where dev-1's
  `u16` control separated nothing in `blade`, and `hydra` seeds with a first draw of 59–61, where dev-1 met `draw<60`
  at equality twice), checked by its own copy of the tool (`dev-1/ai_cat_emu5.py.rev`); the models are the same in both
  runs, and no kept output was written over a development one. (run:2026-10-30-ai-cat-emu-5)
- [I] Not emulated past their entry call: every follower (rows 67, 101, 103–107, 109–112 and 143) reaches
  `MonsterOwner` or `UNIT_CancelEvents` before any test or draw; `MonsterOwner` looks the owner up by guid
  (`GameFindUnit`, ai/0004 § 2.15), a read set not declarable in a small image. Phase 2's logs reproduce them (row 67
  is the batch's tier AI). (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip8 (`+0x56 + 6(k−1) + 2d`, and the fixed cells of rows 105, 106),
  tbl:MonStats.txt:Skill1 … Skill3 (`+0x170 + 2(k−1)`), tbl:MonStats.txt:Sk1mode, Sk2mode (`+0x180`, `+0x181`),
  tbl:MonStats.txt:Velocity (`+0x32`), tbl:MonStats.txt:Run (`+0x34`), tbl:MonStats.txt:SkillDamage (`+0xA8`, H3),
  the MonStats flags byte `+0x0D` (bits 0, 7; `AiShadowPriorityTarget`), the MonStats and Skills counts
  (`g_pDataTables+0xA80`, `+0xBA0`) and the Skills records (`+0xB98`), the Missiles count (`+0xB6C`), the States
  count and records (`+0xC4`, `+0xBC`, record `+0x1E` the group).
- tbl:Skills.txt:srvmissilea (`+0x048`), tbl:Skills.txt:aurarangecalc (`+0x064`), tbl:Skills.txt:aurastate (`+0x080`),
  tbl:Skills.txt:auratargetstate (`+0x082`), tbl:Skills.txt:summon (`+0x0BC`), tbl:Skills.txt:pettype (`+0x0BE`),
  tbl:Skills.txt:calc4 (`+0x144`), tbl:Skills.txt:Param2 (`+0x14C`), tbl:Skills.txt:reqlevel (`+0x174`),
  tbl:Skills.txt:delay (`+0x190`), tbl:Skills.txt:EType (`+0x1DC`), tbl:Skills.txt:aitype (`+0x230`),
  tbl:Skills.txt:aibonus (`+0x232`).
- struct:AiCtl+0x00, struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtx+0x14, struct:AiCtx+0x18,
  struct:Unit+0x04, struct:Unit+0x10, struct:Unit+0xA8 (the skill list), struct:Unit+0xC4, struct:Unit+0xC8,
  struct:Game+0x6D, struct:Game+0xA8.

## Dead ends

- Ghidra's decompile of `SkillDamagePair` drops the two stack words of `SkillLevelClamped` (the pushed `ESI`/`EDI`
  read as callee saves) and shows `SKILLS_GetUnitSkill()` without arguments in rows 105 and 106's inits; objdump gives
  both (0x0056E003–0x0056E006, 0x005EAF6F–0x005EAF7B).

## Open questions

- Who sets `v14` of a necromancer pet (row 67's ranged branch, § 2.2) and of the hydra (row 86's timer, § 2.1): the
  summoning skills' do functions or `SpawnOwnedMonster` (ai/0001 § 3), not read here.
- Row 103 reads its owner without a null test after `MonsterOwner` (0x005EA836): whether an owner-less inviso pet can
  reach an AI event (the summon is removed with its owner) is not read.
- `MonOwnerSkillDamage` admits `SkillDamage` equal to the Skills count (`jg`, 0x0056E0A2); no stock record is at the
  bound (the four stock values are 221, 227, 237, 247): what `SKILLS_GetPhysMin` does with an index one past the table
  is not read (ADR-0010: only edited data reaches it).
- The `0x00574F40` term of `AiPetGuard`'s distance (half of a player-data word) and `0x005DE6F0`'s walk around the
  owner (row 107) are named by their calls only.
