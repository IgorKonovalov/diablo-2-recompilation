# 0001 — Community-known bugs of the 1.14d era, compared with the code and the reviewed specs

> **Subsystem:** quirks
> **Question:** for each of 30 claims from fetched community bug lists, what does the 1.14d `Game.exe` do?
> **Date:** 2026-11-03   **Plan:** 0057   **Status:** answered

## Answer (summary)

Thirty claims from three fetched pages (the owner's bound): 20 `confirmed`, 4 `contradicted`, 3 `not in 1.14d`, 3 `not
found` and held `[L]` under *Open questions*. No claim's agreement raised a tag (ADR-0001, ADR-0007). No emulation and no
harness ran: every row is a code reading, a reviewed statement, or a table read. The pages' claims are leads, and the
statements below are written from the code.

The ones a reimplementer would most plausibly "fix":

- [I] A `manahit` boss drains 256 times the mana the same value does through an `El` column: the mod writes stats 62 and
  63 × 256, and the roll shifts by 8 again. (fn:sub_005A1F90_UModManaHit@0x005A1F90, fn:COMBAT_RollElemStat@0x0057A8E0)
- [I] A monster's line missile carries the monster's stat 19 as `arPct`, and the monster formula adds `arPct` to stat 19,
  so the attack rating counts twice. (fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0, fn:COMBAT_ToHitRoll@0x0057D9B0)
- [I] A summon gets its MonLvl defence and to-hit added whole, with no `noRatio` test.
  (fn:sub_005C49E0_SummonSetLevel@0x005C49E0)
- [I] A player's Smite calls the hit test, draws, then forces the hit bit; a monster's Smite takes its `A2` stats, whatever
  mode it used. (0x005CEBA8, 0x005CEBB0, 0x005CEBB6)
- [I] The knockback chance of Dragon Talon and Psychic Hammer computes `level(target) + slvl − level(target)`, so the
  level difference is always just `slvl`. (0x005D5AEB, 0x005D5AF7, 0x005D31D9, 0x005D31E5)
- [I] Stat 137 (kick damage) counts twice when boots are worn, on the kicks built by `SkillKickPhysDamage`. (fn:sub_00646280_KickItemDamage@0x00646280, fn:sub_005D54B0_SkillKickPhysDamage@0x005D54B0)
- [C] A monster's `Crit` doubles physical and the elemental fields, where a player's critical strike doubles physical only.
  (fn:sub_005A5560_MonCritDouble@0x005A5560, run:2026-10-16-combat)

Four claims do not hold in this image, and a reimplementer must not "restore" them: rows 12, 20, 26 and 28.

## Verdicts

Verdicts are the plan's: `confirmed`, `contradicted`, `not in 1.14d`, `not found`. A row's tag is the tag of the reviewed
statement it rests on, or the inferred tag where this lane read the code. "none" under *Owning spec* means no reviewed spec section
states the behaviour; those rows go to the spec-writer ([backlog entry](../../backlog/2026-11-03-reverser-spec-writer-quirks-community-owning-specs.md)).

| # | Claim (paraphrased) | Source | Verdict | Tag | Anchor | Owning spec section |
|---|---|---|---|---|---|---|
| 1 | Kick skills' knockback uses the target's level for both factors (entries 3, 107) | src:d2-massive-bug-list | confirmed: Dragon Talon's do reads stat 12 of the target (`push edi`) twice | [I] | 0x005D5AEB, 0x005D5AF7, fn:sub_005D5A30_SkillDo42DragonTalon@0x005D5A30 | none |
| 2 | Psychic Hammer has the same formula (entry 5) | src:d2-massive-bug-list | confirmed: both reads `push ebx`, the target | [I] | 0x005D31D9, 0x005D31E5, fn:sub_005D3140_SkillDo33PsychicHammer@0x005D3140 | none |
| 3 | Kick skills receive elemental damage from weapons (entry 4) | src:d2-massive-bug-list | not in 1.14d, on the four `Kick` rows: Kick's start 2 sets flag 2, so `ResolveAndQueue` skips the build. Dragon Talon's hit (start 24, do 42) reaches damage only through `SkillKickPhysDamage`, on a hit bit, as do Dragon Tail's start 27 and Dragon Flight's do 52: it unlinks the damage stats of a `weap` item in either hand, stats 48–55 among them, builds, relinks the primary weapon, and its flag 2 stops a second build. Elemental stats from other items still reach that build | [I] | 0x0057DC28, 0x005D592C, 0x005D54CA, 0x005D57DB–0x005D586A, fn:sub_0056CAF0_SkillSt02Kick@0x0056CAF0, fn:sub_005D5880_DragonTalonHit@0x005D5880, fn:sub_005D54B0_SkillKickPhysDamage@0x005D54B0, fn:sub_00627910_StatListLinkOwner@0x00627910, tbl:ItemTypes.txt:Code, tbl:ItemStatCost.txt:damagerelated | none |
| 4 | The kick damage bonus is added twice (entry 6) | src:d2-massive-bug-list | confirmed, with boots worn only, on the kicks built by `SkillKickPhysDamage` (not Kick's start 2, which reads neither): min and max take stat 137, then the boots' values plus stat 137 | [I] | 0x005D560F, fn:sub_00646280_KickItemDamage@0x00646280 | none |
| 5 | Power Strike's start ignores the skill's attack rating bonus (entry 7) | src:d2-massive-bug-list | confirmed: `COMBAT_MeleeHitTest(target, 0, 0)` | [I] | fn:sub_005DA940_SkillSt06Hit@0x005DA940, fn:SKILLS_GetToHit@0x006449F0 | [skills/catalogue H4](../../specs/skills/catalogue.md) |
| 6 | Smite calls the hit routine and ignores the result (entry 8) | src:d2-massive-bug-list | confirmed for a player caster; the monster branch keeps the result | [I] | 0x005CEBA8, 0x005CEBB0, fn:sub_005CE9F0_SkillDo150Smite@0x005CE9F0 | none |
| 7 | Smite does not set unit flag 64 (entry 9) | src:d2-massive-bug-list | confirmed in do 150 itself: no access to `+0xC4`, where do 2 does `or [edi+0xC4], 0x40`; the callees past `COMBAT_ResolveAndQueue` and `COMBAT_DeliverQueued` are unfollowed | [I] | 0x005CE9F0–0x005CEC50, 0x0056F42A | none |
| 8 | A monster's Smite uses its `A2` damage whatever the mode (entry 10) | src:d2-massive-bug-list | confirmed: mode 5 is passed, and mode 5 selects `A2` | [I] | 0x005CEBB6, fn:sub_005A4F50_MonAttackStats@0x005A4F50 | [monsters/stats § H](../../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) for the mode map |
| 9 | Delayed boss death effects share one timeout id, so one timeout fires them all (entry 12) | src:d2-massive-bug-list | not found: *Open questions* 1 | [L] | fn:sub_005A2620_MonDeathDamage@0x005A2620 | none |
| 10 | `El2` and `El3` take `El1`'s damage (entry 15, first half) | src:d2-massive-bug-list | confirmed | [I] | 0x005A51D7, fn:sub_006538A0_MonLvlStats@0x006538A0 | [monsters/stats § H, H1](../../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) |
| 11 | A monster's critical hit doubles its elemental damage (entry 15, second half) | src:d2-massive-bug-list | confirmed by [combat/damage step 10](../../specs/combat/damage.md): `MonStats.Crit` doubles physical, fire, lightning, magic, cold and poison at the end of `BuildDamage`, and `MISSILE_ApplyDamage` calls the same function. A player's critical strike (step 3) is the case that doubles physical only | [C] for the melee build (reviewed, 89 doublings); [I] for the missile call site | fn:sub_005A5560_MonCritDouble@0x005A5560, 0x0057BD7A, 0x005AD884, run:2026-10-16-combat, tbl:MonStats.txt:Crit | [combat/damage](../../specs/combat/damage.md) step 10 |
| 12 | Melee monsters with life, mana or stamina steal do twice the damage (entry 16) | src:d2-massive-bug-list | contradicted by [combat/reductions](../../specs/combat/reductions.md) § A and [combat/delivery B4](../../specs/combat/delivery.md#b-delivery-combat_applydamage): no field counts twice on the `El` path. A non-hireling monster's life drain is one term of `total`, added to the physical damage, which it does not repeat, and `El` type `life` writes only stats 60 and 61; mana and stamina leave stats 8 and 10 and are not in `total`. What the code can double is a drain already in the packet: `field + (field + roll) × srcdam ÷ 128`. No stock `Skills` row has `EType` life, mana or stam; other writers of those fields are unfollowed | [C] for the life term (reviewed); [I] for mana, stamina (delivery B4 is `[I]`), the `El` write and the packet form | 0x0057C3B9–0x0057C3C7, 0x0057C879–0x0057C889, 0x0057BA71–0x0057BAF3, 0x005A53B5–0x005A53C5, fn:COMBAT_ApplyDamage@0x0057C6C0, fn:COMBAT_ApplyReductions@0x0057C1E0, tbl:Skills.txt:EType | [combat/delivery](../../specs/combat/delivery.md) |
| 13 | Mana drain bosses do 512 times the proper damage (entry 17) | src:d2-massive-bug-list | confirmed with a different factor: 256, capped by the mana the defender holds, § 1, composed from three reviewed halves and the code, not run; nothing read gives 512 | [I] | fn:sub_005A1F90_UModManaHit@0x005A1F90, fn:COMBAT_RollElemStat@0x0057A8E0, 0x0057C879–0x0057C889 | [monsters/stats § G](../../specs/monsters/stats.md) for the ×256; the effect none |
| 14 | A monster with few hit points has no regeneration (entry 21) | src:d2-massive-bug-list | confirmed: stat 74 is `((hp << 8) × r) >> 12`, so 0 while `hp × r < 16` | [I] | 0x00573FF6–0x00574058, tbl:MonStats.txt:DamageRegen | [monsters/stats B8](../../specs/monsters/stats.md#b-monstatsinit-in-order) |
| 15 | Players with more than 99 % physical resistance are immune to crushing blow (entry 22) | src:d2-massive-bug-list | confirmed: `cb − MulDiv(cb, min(stat 36, 100), 100)` for every defender, so `cb` is 0 at 100 or more | [C] for the formula; [I] for the player's divisor 10 | fn:STATEVENT_CrushingBlow@0x005BFFC0 | [combat/delivery E1](../../specs/combat/delivery.md#e-the-stat-events-crushing-blow-open-wounds-freeze) |
| 16 | Summons get extra attack rating and defence, 100 % of MonLvl; `noRatio` is ignored (entry 23) | src:d2-massive-bug-list | confirmed: `UnitAddStat` of stats 31 and 19 with the raw cells; no test of the class bit | [I] | fn:sub_005C49E0_SummonSetLevel@0x005C49E0 | [skills/dispatch L2](../../specs/skills/dispatch.md) |
| 17 | Monsters with ranged attacks have twice the attack rating (entry 24) | src:d2-massive-bug-list | confirmed for line missiles whose record byte `+0x18B` is set, § 2 | [I] | fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0, fn:MISSILE_HitUnit@0x005ADF10, fn:COMBAT_ToHitRoll@0x0057D9B0 | [skills/missiles B2, E1](../../specs/skills/missiles.md), [combat/to-hit A2](../../specs/combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll): each half stated, the sum none |
| 18 | Throwing and shooting skills do not add their attack rating bonus to the missile (entry 25) | src:d2-massive-bug-list | confirmed for both skill creators (flag `0x1000` for a monster owner only, none in the lob form), with one exception read: do 74 (Double Throw) adds `SKILLS_GetToHit` to the missile's stat 19 after creating it. Other creators of a to-hit flag or stat are unfollowed | [I] | 0x005D8943–0x005D896E, fn:sub_005D88B0_SkillDo74DoubleThrow@0x005D88B0, fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0, fn:sub_0056EE90_SkillMissileCreateLob@0x0056EE90, fn:SKILLS_GetToHit@0x006449F0, tbl:Skills.txt:srvdofunc | [skills/README](../../specs/skills/README.md), [skills/missiles B2, B3](../../specs/skills/missiles.md); do 74's add none |
| 19 | Blessed Aim and Penetrate share a state (entry 26) | src:d2-massive-bug-list | confirmed: both rows name `penetrate` in `passivestate`; Blessed Aim's `aurastate` is its own. Do 65 passes that `passivestate` at block `+0x48`, and `AURA_ApplyToTarget` frees that list and clears the state on the unit it applies to, so a running Blessed Aim removes Penetrate's list from its caster. The other direction, Penetrate's refresh against the aura, is not read | [I] | 0x005CEFD5–0x005CEFFD, fn:AURA_ApplyToTarget@0x005CEDC0, fn:SKILLS_RefreshPassive@0x00646D60, tbl:Skills.txt:passivestate, tbl:Skills.txt:aurastate | [skills/catalogue](../../specs/skills/catalogue.md) do 65, [stats/states](../../specs/stats/states.md) `+0x48` |
| 20 | Curse resistance cuts every timed list, Fade's among them (entry 30) | src:d2-massive-bug-list | contradicted by [stats/states B1](../../specs/stats/states.md): the cut runs only `if curse`, the state's `curse` flag, and `fade` has that cell blank | [C] the cut on a player target; [I] the gate | fn:STATE_ApplyTimed@0x0056E970, 0x0056E9C9–0x0056EA4A, tbl:States.txt:curse | [stats/states B1](../../specs/stats/states.md) |
| 21 | After Normal, bosses are picked from `nmon`'s pool, not `umon` (entry 33) | src:d2-massive-bug-list | confirmed: `umon` in Normal, the region pool in Nightmare and Hell | [C] | fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, tbl:Levels.txt:umon1 | [monsters/pool](../../specs/monsters/pool.md) |
| 22 | The chest fix cut act boss drops from 7 to 6 (entry 38) | src:d2-massive-bug-list | confirmed in effect: the stop at 6 holds and the stock boss rows have `Picks` 7. The history and the intent are not decidable from this image | [C] | fn:TC_ResolveDrops@0x0055A6D0, tbl:TreasureClassEx.txt:Picks | [items/tc](../../specs/items/tc.md) `MAX_DROP` |
| 23 | Delayed trapped-soul drops ignore gold and magic find: NULL to the TC function (entry 41) | src:d2-massive-bug-list | not found: *Open questions* 2 | [L] | fn:OBJOP_TrappedSoul@0x005869F0 | [objects](../../specs/objects/README.md) class 380, 381 row |
| 24 | The TC upgrade does not check for the table's last record (entry 44) | src:d2-massive-bug-list | confirmed: no bound check; stock data never reaches it, by a full-table check | [C] | fn:TC_GetByIndex@0x00654E00, tbl:TreasureClassEx.txt:group | [items/tc C2](../../specs/items/tc.md) |
| 25 | Some runeword property codes are misspelled (entry 48) | src:d2-massive-bug-list | not in 1.14d: 0 unknown codes in 508 `T1Code` cells of 169 rows. The page's "stops at the bad code" is not read | [C] for the data | tbl:Runes.txt:T1Code1, tbl:Properties.txt:code | [items/sockets-runewords](../../specs/items/sockets-runewords.md) |
| 26 | Hratli's magic level is 1, by a misspelled header (entry 109) | src:d2-massive-bug-list | contradicted by [items/vendors D3](../../specs/items/vendors.md): the header is right about the cause, the value is 0, the absent-column default | [C] | tbl:Weapons.txt:HratliMagicLvl | [items/vendors D3](../../specs/items/vendors.md) |
| 27 | Prevent Monster Heal is not applied from a mercenary's items (entry 117) | src:d2-massive-bug-list | confirmed: the hook tests a player attacker (`*unit = 0`), and classes 704–709 are excluded | [I] | fn:sub_0057D810_PreventHealHook@0x0057D810 | [combat/to-hit A6](../../specs/combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll) |
| 28 | Eth's target defence reduction goes negative, so it works as "ignores target defence", on bosses too (v1.09 page) | src:flux-decahedron-9 | contradicted by [combat/to-hit A7](../../specs/combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll): the percent is clamped to 0..100 and halved on a boss, player, superunique or hireling | [I] | fn:COMBAT_ToHitTargetMods@0x0057D8A0, tbl:Properties.txt:stat1 | [combat/to-hit A7](../../specs/combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll) |
| 29 | The "n−1" bug: a ranged modifier never reaches its maximum (v1.09 page, said fixed in v1.08) | src:flux-decahedron-9 | not in 1.14d: `lo + Range(hi − lo + 1)` | [C] | fn:PROP_RollValue@0x0065E9E0 | [items/properties D1](../../specs/items/properties.md#d-the-value-roll-and-the-stat-writer) |
| 30 | Cloak of Shadows can crash the game near the Ancients and stationary spawners | src:pd-gamebreaking-bugs | not found: *Open questions* 3 | [L] | fn:sub_005D6520_CloakAreaCb@0x005D6520 | none |

## Leads used

Each row of the table above is the verdict for its lead. Pages:

- [L] src:d2-massive-bug-list: 156 numbered entries; 27 taken, for what a reimplementer would act on. Left out: presentation,
  client and desync reports, exploits, and table balance. Prose and function names only, no code.
- [L] src:flux-decahedron-9: a 2003 column on v1.09, so its claims are old; two taken.
- [L] src:pd-gamebreaking-bugs: read in a saved copy because the live page refuses a fetch; one taken. Its 1.14d rows are crash
  reports with theories, and the guide says it is neither exhaustive nor accurate.
- src:gamestar-nham and src:blizzard-d3-bugs-to-fix could not be fetched and are registered as not read. So "next hit always misses",
  which those search results named, has no claim here: the snippets alone are not a lead (ADR-0007).
- No party claim was taken. `lane/r58a`'s player/0002 was read first, as instructed.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00646280` | `sub_00646280_KickItemDamage` | adds stat 137 and the boots' kick damage to a kick's min and max (fn:sub_00646280_KickItemDamage@0x00646280) | I |
| `0x005D5880` | `sub_005D5880_DragonTalonHit` | to-hit, the kick damage and the queue of one Dragon Talon kick (fn:sub_005D5880_DragonTalonHit@0x005D5880) | I |

## Walkthrough

### 1. The mana drain's factor (row 13)

[I] `UModManaHit` adds `(c·DM ÷ 100) × 0x100` to stats 62 and 63 (0x005A1F90), and `MonAttackStats`' type 7 writes the plain value
(fn:sub_005A4F50_MonAttackStats@0x005A4F50). `BuildDamage`'s monster branch rolls them with `COMBAT_RollElemStat`, which
shifts by 8 (fn:COMBAT_RollElemStat@0x0057A8E0, fn:COMBAT_BuildDamage@0x0057B7D0), scaled by `srcdam ÷ 128`. `Leech` shifts
the field up by 6 and, for a monster attacker, back (fn:COMBAT_Leech@0x0057C420). `ApplyDamage` then subtracts it from stat 8, in 1/256
units, with 0 below 256 (0x0057C879–0x0057C889), so the loss stops at the mana held. So value `v` takes `v` mana by an `El` column and `256·v` by the mod. The 1/256
units, and the mod's write, are the reviewed specs'; the composed factor is this reading. `v << 22` passes through `Leech`: 511
still fits in i32 (2 143 289 344), and 512 reaches 2³¹ and wraps. Whether a wrapped value then reaches a use is not read.

### 2. The monster missile's attack rating (row 17)

[I] `SkillMissileCreate` sets flag `0x1000` with the owner's stat 19 for a monster owner (0x0056ECB0), which becomes the missile's stat
19 (fn:sub_0059FA30_MissileCreate@0x0059FA30). `MISSILE_HitUnit` passes that as `arPct` when the missile's record byte `+0x18B` is set; without it there is no to-hit roll (0x005AE04C–0x005AE06F, fn:MISSILE_HitUnit@0x005ADF10). For a
non-player attacker `AR ← stat 19 + arPct + 5 × stat 2` (fn:COMBAT_ToHitRoll@0x0057D9B0). So the factor is 2 on stat 19 only, the dexterity
term is not doubled, the two stat 19s are read at creation and at the hit, and `SkillMissileCreateLob` sets no flag (fn:sub_0056EE90_SkillMissileCreateLob@0x0056EE90).

### 3. Smite (rows 6–8)

[I] The player branch rolls the weapon damage, calls `COMBAT_MeleeHitTest(target, 0, 0)` at 0x005CEBA8, and does `or ax, 1` at 0x005CEBB0,
so the test's draws run and the hit bit is set whatever it returned. The defence bits it returned stay in the word; how
`ResolveAndQueue` treats a word with both is not followed here. The monster branch passes mode 5 to `MonAttackStats` (0x005CEBB6) and keeps the
test's result. (fn:sub_005CE9F0_SkillDo150Smite@0x005CE9F0)

## Data touched

`tbl:States.txt:curse`, `tbl:Skills.txt:passivestate`, `tbl:Skills.txt:aurastate`, `tbl:Runes.txt:T1Code1`, `tbl:Properties.txt:code`,
`tbl:Properties.txt:stat1`, `tbl:TreasureClassEx.txt:Picks`, `tbl:ItemTypes.txt:Code`. Read at the audit, by hand and not in the tool's output: `tbl:ItemStatCost.txt:damagerelated`, `tbl:Skills.txt:EType`, `tbl:Skills.txt:srvdofunc`. Tool: `tools/quirks_community_check.py`; output
`workspace/logs/r57b-quirks-table-check.txt`, sha256 prefix `5b2248598fbe503b`.

## Dead ends

- [I] The search for a shared timeout started at `UnitQueueEvent`'s callers: of the listed callers named for mods only
  `sub_005A1330_UModAlwaysRunAi` is a `UMod` function, and `MonDeathDamage` calls no queue function. That rules out neither reading of
  row 9, because many callers are unnamed. (fn:sub_005417D0_UnitQueueEvent@0x005417D0, fn:sub_005A2620_MonDeathDamage@0x005A2620)

## Open questions

1. [L] **Row 9, the shared timeout id.** Not settled because the mods' death functions run through a table not walked here. Resolve by
   listing the death slot of `data:g_UModEventFns@0x0073C0B8` and each queue call's event id. src:d2-massive-bug-list also says Fire and Cold
   Enchanted fire twice on Nightmare only (entry 102), not taken.
2. [L] **Row 23, the trapped soul.** `OBJOP_TrappedSoul`'s `r < 90` branch calls `ObjectChestDrop` directly, while `r ≥ 90` queues object events 1 and 9, and
   their handler was not found. Resolve by reading that handler and what it passes as the killer to `TC_ResolveDrops`. (0x00586A9D, 0x00586AB7)
3. [L] **Row 30, the Cloak of Shadows crash.** The area callback applies a timed state and, for a monster that passes `sub_0056E2F0_MonTestN`, re-inits its AI to mode 10
   (fn:sub_005D6520_CloakAreaCb@0x005D6520, fn:sub_005B0E00_MonAiInit@0x005B0E00). The page gives only theories, and which AI would fault was not read. Owner decision 5 forbids provoking it;
   resolve by reading mode 10's dispatch against the Ancients' and the spawners' AI.
