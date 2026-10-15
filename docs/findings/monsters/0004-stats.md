# 0004 — Monster stats: hit points, defence, experience, resistances, MonProp and the mod effects

> **Subsystem:** monsters/stats
> **Question:** once a monster is placed with its level and its special mods, which stats does it get, from which draws on its unit seed, and how do difficulty, the player count, MonProp and the mods change them?
> **Date:** 2026-10-14, Phase 2 2026-10-15   **Plan:** 0025 (Phase 1, static reading; existing logs of run:2026-10-14-mon-special re-read; Phase 1b cross-check; Phase 2 run:2026-10-15-mon-stats)   **Status:** answered (Phase 1); Phase 1b done 2026-10-14 (§ Leads used); Phase 2 done 2026-10-15 (§ 11, § 12)

Names of structs and fields are ours. "Unit seed" is the monster's own seed at `Unit+0x20` ([rng/0002](../rng/0002-seed-tree.md)).
`RNG_Range(s, n)` and `RNG_RangeB(s, n)` return `low % n` after one step, or 0 with **no step** when `n < 1` (signed),
per [rng/0001](../rng/0001-rng-core.md). `d` is the difficulty (`game+0x6D`, clamped to 0..2), `L` the MonLvl column
set: `L = (game+0x6A ≠ 0 || game+0x74 ≠ 0)` ([monsters/0001 § 5](0001-level-pool.md#5-the-monster-level-sub_00573cb0_monstatsinit)).
"Stat *n*" is `ItemStatCost` row *n*: 6 `hitpoints`, 7 `maxhp` (both `ValShift` 8), 12 `level`, 13 `experience`,
16 `item_armor_percent`, 20 `toblock`, 25 `damagepercent`, 31 `armorclass`, 36 `damageresist`, 37 `magicresist`, 39/41/43/45
fire/light/cold/poison resist, 48–63 the elemental damage and length stats, 67 `velocitypercent`, 68 `attackrate`, 69
`other_animrate`, 74 `hpregen`, 100 `monster_playercount`, 119 `item_tohit_percent`, 352 `last_sent_hp_pct`
([ItemStatCost](../../tables/ItemStatCost.md)). `SetStat` is `sub_00627260_UnitSetStat` (replaces the base value);
`AddStat` is `sub_006272B0_UnitAddStat` (`STATLIST_AddStat` on the unit's list, nothing when the value is 0). The
register arguments of the handlers were read in the disassembly; the decompiler hides most of them. Phase 1 was written
from the code only; no community text was read before § Leads used.

## Answer (summary)

- [C] **MonProp layout.** The loader's field descriptor (`sub_00658720_MonPropLoad`, built on the stack before the call at
  `0x006594B3`) maps `prop<k>` to `+0x04 + 0x60·d + 0x10·(k−1)` (type 0x13, linked to `properties`), `par<k>` to `+0x08…`
  (s32), `min<k>`/`max<k>` to `+0x0C…`/`+0x10…` (s32) and `chance<k>` to `+0x124 + 6·d + (k−1)` (type 4, u8). Layout (a) of
  [MonProp](../../tables/MonProp.md) is the game's; the archivist's diff of all 13 records is the second path.
  (fn:sub_00658720_MonPropLoad@0x00658720, 0x00658744–0x00659308, struct:MonPropRec+0x124)
- [C] **DifficultyLevels member order.** The descriptor of `sub_00617D90_DifficultyLevelsLoad` names every column with its
  offset: `MonsterFreezeDivisor` `+0x14`, `MonsterColdDivisor` `+0x18`, `AiCurseDivisor` `+0x1C`, `LifeStealDivisor` `+0x28`,
  `ManaStealDivisor` `+0x2C`, `UniqueDamageBonus` `+0x30`, `ChampionDamageBonus` `+0x34`, which is the `.txt` order the
  archivist chose. The record index is the difficulty: every reader goes through `sub_00611D30_DifficultyRec(game+0x6D)`
  `[I]`. The monster readers are `MonsterSkillBonus` (`+0x10`, skill levels at creation) and `ChampionDamageBonus` (`+0x34`,
  in the `champion`, `berserk` and `strong` handlers, uniques included); **`UniqueDamageBonus` has no reader** found `[I]`.
  (fn:sub_00617D90_DifficultyLevelsLoad@0x00617D90, 0x00617DA0–0x006180B2, fn:sub_00611D30_DifficultyRec@0x00611D30, struct:DifficultyLevelsRec+0x34)
- [C] **Hit points** (`sub_00573CB0_MonStatsInit`, 0x00573F7E–0x00573FC8): `lo, hi` = MonLvl `HP[L][d]` × MonStats
  `minHP[d]`/`maxHP[d]` / 100 (`sub_00483360_MulDiv`), or the raw MonStats cells for a `noRatio` class;
  `base = lo + RangeB(unit seed, hi − lo + 1)`; `hp = base + MulDiv(base, g_PlayerHpPct[n], 100)`, capped at `0x7FFFFF`;
  stats 7 and 6 = `hp << 8`. With a reversed or empty range (`hi < lo`) the draw makes **no step** and `base = lo`.
  Reproduced bit-exact (draw, unit seed, stats) for every creation of the run; the reversed-range branch was not met (§ 12).
  (fn:sub_006538A0_MonLvlStats@0x006538A0, fn:sub_00483360_MulDiv@0x00483360, data:g_PlayerHpPct@0x006E1590, run:2026-10-15-mon-stats)
- [C] **Player count** (`sub_00573930_MonPlayerBonus`): `n = max(1, PlayerCount(game))` for a class with MonStats
  `Align` 0, else `n = 1` and no bonus. `g_PlayerHpPct` and `g_PlayerXpPct` are both `0, 0, 50, 100, …, 350` for `n` = 0..8,
  i.e. **+50 % per player beyond the first**, for HP and experience alike. It is applied **once, at creation**: `n` is stored
  as stat 100, and `PlayerCount` has only two callers (this one and the TC drop code), so a live monster is never rescaled.
  Second path: the run changed `/players` 13 times in nine games and read stats 7, 12, 13 and 100 of every live monster
  each time; all equal the creation values (§ 12). (run:2026-10-15-mon-stats, fn:sub_00573930_MonPlayerBonus@0x00573930, fn:sub_00535790_PlayerCount@0x00535790, data:g_PlayerXpPct@0x006E15B4)
- [C] **Defence and experience** are set at creation: stat 31 = MonLvl `AC[L][d]` × MonStats `AC[d]` / 100; stat 13 =
  `x + MulDiv(x, g_PlayerXpPct[n], 100)` with `x` = MonLvl `XP[L][d]` × MonStats `Exp[d]` / 100 (raw cells for `noRatio`).
  **To-hit and damage are not stats of the created monster**: `sub_005A4F50_MonAttackStats` computes them from MonLvl
  `TH`/`DM` × the MonStats attack columns at attack time, from the current level stat (§ 9). No draw for AC, XP, TH, damage.
  (fn:sub_00573CB0_MonStatsInit@0x00573CB0, 0x00573FCD–0x00573FF1, fn:sub_005A4F50_MonAttackStats@0x005A4F50, tbl:MonLvl.txt:AC, tbl:MonLvl.txt:XP, run:2026-10-15-mon-stats; to-hit and damage `[I]`, out of scope)
- [C] **Resistances and block** are the MonStats cells of difficulty `d`, set as they are (stats 36, 37, 39, 41, 43, 45; stat
  20 from `ToBlock`); no hell adjustment is applied at creation. Blank cells are used as the value 0 everywhere at creation.
  (0x00573E83–0x00573F03, tbl:MonStats.txt:ResFi, tbl:MonStats.txt:ToBlock, run:2026-10-15-mon-stats)
- [C] **Classic nightmare and hell** (`sub_0063EEF0_MonClassicDiffAdjust`, a classic game with `d` > 0 and `Align` ≠ 1):
  max HP × 1/2, AC × 10/12, experience × 10/17 (nightmare) or 10/26 (hell), and the **level stat is rewritten to MonStats
  `Level` (normal) + 25·d**. The halving of stat 7 goes through the unit's stat callback (§ 11), which scales the current HP
  (stat 6) and recomputes hpregen (stat 74) with it; Phase 1's "stat 6 keeps the unhalved value" was wrong. This answers the
  classic `aura` question: the handler reads `Level + 25·d + 3` (`leveladd`). Second path: in classic hell the run logged
  five aura uniques of class 48 (`Level` 18, `Level(H)` 78) drawing their aura with level 71 = 18 + 50 + 3, not 81.
  (fn:sub_0063EEF0_MonClassicDiffAdjust@0x0063EEF0, data:g_ClassicDiffAdjust@0x006EA9F0, run:2026-10-15-mon-stats)
- [C] **MonProp** (0x00574177–0x00574220): the class's row (`MonStats.MonProp`), difficulty `d`, slots 1..6 until the first
  `prop < 0`. A slot with `chance` 0 is **applied with no draw**; a slot with `chance` > 0 steps the unit seed once and applies
  when `low % 100 < chance`. An applied slot goes to `PROP_ApplyBlock` (mode 0, flags `0x40`), whose value roll draws on the
  **unit seed** when `min ≠ max` (the stock `thorns` slots). Every monster of the class gets it, specials or not. The
  `irongolem` row is never read: `sub_00573470_MonPropRec` is the only reader and no class names the row.
  The slot's stats go to a stat list of flags `0x40` attached to the unit's list. Reproduced in nightmare and hell
  (`thorns` 15..20 with its unit-seed roll, `crush` 15 and 25); the `chance` > 0 branch is not reached on stock data.
  (fn:sub_00573470_MonPropRec@0x00573470, fn:PROP_ApplyBlock@0x0065FD70, tbl:MonProp.txt:chance1, run:2026-10-15-mon-stats)
- [C] **Mod effects** are in § 8 (per handler, with the `constants` rows they read). Main points: `hpmultiply` adds
  `constants[4+d]` % (champion), `[7+d]` % (unique) or `[1+d]` % (group member) to max HP; `leveladd` is level + 3, experience
  × 5 (group members too); `champion` is level − 1, experience − 2·(xp/5), damage % and to-hit % × `ChampionDamageBonus`/100,
  velocity; the enchantments add MonLvl `DM` × `constants` % elemental damage and their resistances.
  (fn:sub_005A0DC0_UModHpMultiply@0x005A0DC0, fn:sub_005A0E40_UModLevelAdd@0x005A0E40, fn:sub_005A0E80_UModChampion@0x005A0E80, fn:sub_005A1990_UModFire@0x005A1990, tbl:MonUMod.txt:constants, run:2026-10-15-mon-stats). `[C]` for every handler the run met; `berserk` (39) is `[C]` on a forced path
  (run:2026-10-15-berserk-forced: 33 berserkers, every stat write and the level + 3 predicted); `poisonhit` (23) was not
  met and stays `[I]` (§ 12).
- [C] **Order on the unit seed.** In `MonStatsInit`: the appearance pick (1 step with a region variant set, else one per
  MonStats2 component with a count ≥ 1), `Range(4)` for classes 311/312, the HP draw, the MonProp draws, then the
  MonEquip draws. All of them come **before** the special-mod draws of [monsters/0003](0003-special-monsters.md) (champion
  roll, picks, `rndname`). In run:2026-10-14-mon-special, 4 149 of 4 429 creations moved the unit seed by exactly 2 between
  its initialisation and the end of the creation (appearance pick + HP draw), consistent with this.
  Phase 2 predicts every one of these draws and compares the unit seed after each (MonEquip, met by no class of the run,
  stays an ADR-0004 seed oracle). (fn:sub_005739D0_MonComponentsPick@0x005739D0, fn:sub_005D6B60_MonEquipInit@0x005D6B60, 0x00573F8F, 0x005741C2, run:2026-10-14-mon-special, run:2026-10-15-mon-stats)
- [C] **The stat callback** (§ 11). `MonStatsInit` first gives the unit a new stat list with the callback
  `sub_0055B800_MonStatCallback` (`sub_00626D40_UnitStatListCreate`, 0x00573E62). Its stat-7 case runs on every later change of
  max HP (classic adjustment, `MonHpAddPct`): with `old` > 0, `new ≠ old` and `cur` = stat 6 > 0, stat 6 =
  `clamp(trunc(float32(new / max(old, 256) · cur)), 1, new)`, and for a class with `DamageRegen` `r` ≠ 0 stat 74 =
  `((new >> 8)·r) >> 4`. It explains the flag-0 `hpmultiply` calls, where hpregen grows with max HP although the handler
  writes no stat 74. (fn:sub_0055B800_MonStatCallback@0x0055B800, 0x0055B8EC–0x0055B998, run:2026-10-15-mon-stats)
- [C] **The x87 control word** for that division and product is the CRT start-up's: 53-bit precision (`_PC_53`, written
  once by `CRT_setdefaultprecision`), round to nearest (never changed); no game code changes either persistently. The run
  excludes chop and 24-bit precision; the 53 bits rest on the code (§ 11). (fn:CRT_setdefaultprecision@0x0068E70A, run:2026-10-15-mon-stats)
- [I] **The `willowisp1` halving** of the stat-25 bonus is signed `÷ 2` toward zero (`cdq; sub; sar 1`), § 8. (0x005A0FC8–0x005A0FCF)
- [I] **`UniqueDamageBonus` and `HireableBossDamagePercent` have no reader.** A full trace of all 23 call sites of
  `sub_00611D30_DifficultyRec` and of every reference to `g_pDifficultyLevels` finds no read of `+0x30` or `+0x38`
  (§ 1). Absence cannot be reproduced on stock data, where the two damage-bonus columns are equal.
  (fn:sub_00611D30_DifficultyRec@0x00611D30, data:g_pDifficultyLevels@0x0096C8AC)
- **Boundary for Phase 2** (recommended here, accepted by the architect): model in full the creation stats (HP, AC, XP, resistances, block, level, the
  constants, hpregen, MonProp, every handler's stat writes); take MonEquip's item creation as a **boundary oracle**
  (it draws on the game seed through item creation); leave to-hit and damage (attack time), skills and AI, and the aura's
  combat effect out of scope, logging only the skill ids and levels set at creation (§ 10).

## Leads used

Phase 1b (2026-10-14, ADR-0007), after Phase 1 was written. Downloads in the scratchpad only; prose, no code.

- [L] src:d2dfg-blizzard § MonLvl.txt: `HP`, `AC`, `XP` are percentage multipliers of MonStats `minHP`/`maxHP`, `AC`, `Exp`;
  `TH` multiplies `A1TH`/`A2TH`; `DM` multiplies the attack and `El` damage. **held** (`MulDiv(MonLvl, MonStats, 100)`, § 4; `S1TH`
  and `S1MinD/MaxD` too).
- [L] src:d2dfg-blizzard § MonLvl.txt: the plain columns serve "Non-Ladder Battle.net / Singleplayer / Open Battle.net / TCP",
  the `L-` columns "only the Ladder Battle.net game type". **contradicted**
  Detail: 1.14d picks the `L-` set when `game+0x6A ≠ 0 || game+0x74 ≠ 0`, and `game+0x6A` was 3 in every single-player run
  ([monsters/0001 § 5](0001-level-pool.md#5-the-monster-level-sub_00573cb0_monstatsinit)), so single player uses `L-`. The two sets
  differ in `AC(N)`, `AC(H)` and `HP(H)` only ([MonLvl](../../tables/MonLvl.md)); a nightmare or hell creation
  separates them. Phase 2: every single-player nightmare and hell creation of the run whose two column sets differ
  (§ 12) matches the `L-` values and not the plain ones. (0x00573F41, fn:sub_006538A0_MonLvlStats@0x006538A0, run:2026-10-15-mon-stats)
- [L] src:d2dfg-blizzard § monstats.txt `noRatio`: 1 uses the MonStats cells, 0 the MonLvl scaling. **held** (§ 4).
- [L] src:d2dfg-blizzard § monstats.txt `minHP`/`maxHP` "Life when spawned", `AC`, `Exp`, `ResDm`…`ResPo`, `ToBlock`. **held with
  refinement**: scaled by MonLvl unless `noRatio`, plus the player-count %; resistances and block as they are (§ 2).
- [L] src:d2dfg-blizzard § monstats.txt `DamageRegen`: "Regeneration Rate = (Life * DamageRegen) / 16". **held with refinement**:
  stat 74 = `(hp << 8)·r >> 12`, i.e. Life × r / 16 in 1/256 units, with the overflow branch and the fatal checks of § 2.
- [L] src:d2dfg-blizzard § monstats.txt `Sk1lvl` "base skill level" and § difficultylevels.txt `MonsterSkillBonus` "adds skill
  levels to skills used by monsters". **held** (§ 2).
- [L] src:d2dfg-blizzard § difficultylevels.txt `ChampionDamageBonus`: % modifier of a champion's damage and attack rating.
  **held with refinement**: it scales the `champion`/`berserk` bonuses and the `strong` bonus of uniques and minions (§ 8).
- [L] src:d2dfg-blizzard § difficultylevels.txt `UniqueDamageBonus`: % modifier of a unique's damage and attack rating.
  **not covered** (architect ruling, plan 0025 Phase 1): the full xref of Phase 2 finds no reader of `+0x30` (§ 1), and the
  unique `strong` bonus reads `ChampionDamageBonus` (§ 8, reproduced). The columns are equal in stock data, so play cannot
  tell the two apart; only a forced-path run (ADR-0010) could.
- [L] src:d2dfg-blizzard § MonProp.txt: `chance` 0 means "always applied"; `par`, `min`, `max` per property func. **held** (§ 7;
  the layout from the descriptor, § 1).
- [L] src:arreat-summit-monster-pages (basics): "when a monster is created, its Hit Points are multiplied … (Number of Players +
  1) / 2"; experience `X·(n + 1)/2`. **held** (`+50 %` per player beyond the first, § 3). "as they leave the game, the monsters
  become easier": **held with refinement**: only monsters created afterwards; a live monster keeps its stats (§ 3).
- [L] src:maxroll-player-settings: life and experience `(n + 1)/2`; "Monster's Stats are determined by the PS they are spawned
  on"; damage and attack rating + 6.25 % per player from P2. **held** for life, experience and the spawn rule; **held with
  refinement** for damage: `8·(n − 1)/128` = 6.25 % per player, but only in an expansion game in nightmare and hell, at
  attack time (§ 9). (D2R page.)
- [L] src:arreat-summit-bonuses, hit points: minions ×2/×1.75/×1.5, champions ×3/×2.5/×2, uniques ×4/×3/×2. **held**
  (`constants` 1–9 through `MonHpAddPct`, § 8).
- [L] src:arreat-summit-bonuses, level: champion + 2, unique and minions + 3. **held** for champion, ghostly, fanatic,
  possessed (`leveladd` + 3, `champion` − 1) and uniques/minions; **contradicted** for berserkers: `berserk` does not call the
  `champion` part, so a berserker is + 3 (its experience × 5, which the page does give). Required Phase 2 case, not met by
  run:2026-10-15-mon-stats (12 champion-mod picks, none `berserk`); met on a forced path in plan 0027 Phase 3: all 33
  berserkers of run:2026-10-15-berserk-forced end at the pre-handler level + 3, all 56 champion-member calls at + 2 (§ 12).
- [L] src:arreat-summit-bonuses, experience: berserker × 5, other champions × 3, unique and minions × 5. **held** (§ 8).
- [L] src:arreat-summit-bonuses: champion +90/75/66 % damage and +67/56/49 % attack rating, + 20 movement; ghostly the same, DR
  set to 80, +33–50 % cold; fanatic + 100 movement, − 70 % defence; berserker +270/225/198 % damage and attack rating, life ¼ of a
  champion's; possessed life 2× a champion's, + 20 movement; Willowisp damage halved. **held**, with one refinement: the fanatic
  and `fast` movement is `clamp(2048/Velocity − 128, 10, 100)`, 100 only for a `Velocity` ≤ 9 class (§ 8).
- [L] src:arreat-summit-bonuses, Extra Strong: unique +135/112/99 % damage, +90/75/66 % AR; minion +67/56/49 %, +45/37/33 %.
  **held** (`CDB × constants` 12–15, truncated, § 8).
- [L] src:arreat-summit-bonuses, enchantments: +66 % min / +100 % max of the element, + 75 resist, minions +33–50 % in
  nightmare and hell, cold length `4 + mlvl × 0.2` s, mana × 256 damage, Magic Resistant cold/fire/lightning + 40 then magic + 20
  for Mana Burn, Stone Skin DR + 50 with defence doubled, the "no third immunity" rule. **held with refinement**: the % applies to
  MonLvl `DM` of the monster level, not to the monster's damage; cold length is `5·ℓ + 100` frames (§ 8).
- [L] src:arreat-summit-bonuses, Spectral Hit: cold, fire, lightning resist **+ 40** each if < 75 %. **contradicted**: the
  handler adds **20** (`0x005A1370`, mod 27). Phase 2 reproduced it (§ 12), e.g. a `spectralhit` unique of class 5 going
  from 0/0/0 to 20/20/20 cold/fire/lightning. (fn:sub_005A1370_UModResist@0x005A1370, run:2026-10-15-mon-stats)
- Not covered by any source read: the HP draw itself and its no-step rule for reversed ranges, the classic nightmare/hell
  factors and the `Level + 25·d` level, the per-component appearance draw, MonProp's `chance` draw, the `MulDiv` branches.
- Searched and not used: "Diablo II monster life players setting formula" found diablowiki "Player Settings" (blocked by
  Cloudflare, not read) and the maxroll page above.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00573CB0` | `sub_00573CB0_MonStatsInit` | level, the base stats, HP draw, skills, MonProp, MonEquip | C |
| `0x006538A0` | `sub_006538A0_MonLvlStats` | MonLvl × MonStats (or raw MonStats for `noRatio`) by mask, into `MonLvlStatsOut` | C |
| `0x00483360` | `sub_00483360_MulDiv` | `a·b/c` with the overflow branches below | C |
| `0x00573930` | `sub_00573930_MonPlayerBonus` | player count, its HP/XP %, `MonsterSkillBonus`, difficulty | C |
| `0x005738F0` | `sub_005738F0_PlayerHpPct` | `n < 9 ? g_PlayerHpPct[n] : (n − 2)·50` | C |
| `0x00573910` | `sub_00573910_PlayerXpPct` | `n < 9 ? g_PlayerXpPct[n] : 10·n + 260` | C |
| `0x005739D0` | `sub_005739D0_MonComponentsPick` | appearance: a region variant set, or one draw per component | C |
| `0x006647C0` | `sub_006647C0_MonCompCount` | MonStats2 component count `m2+0x15+k` | C |
| `0x0063EEF0` | `sub_0063EEF0_MonClassicDiffAdjust` | classic nightmare/hell: HP, AC, XP factors; level = `Level` + 25·d | C |
| `0x00573470` | `sub_00573470_MonPropRec` | the class's MonProp record, or 0 | C |
| `0x005D6B60` | `sub_005D6B60_MonEquipInit` | MonEquip rows of the class: one draw per row, item creation | I |
| `0x005D30A0` | `sub_005D30A0_MonEquipFirstRow` | MonStats `+0x2A` → first `monequip` record (0x1C B) | I |
| `0x0056DEB0` | `sub_0056DEB0_UnitSkillAdd` | add a skill at a level (RNG only on the player branch) | I |
| `0x005A0D20` | `sub_005A0D20_MonHpAddPct` | max HP += `MulDiv`-like(maxHP, pct, 100); stats 7 and 6 | C |
| `0x005A4F50` | `sub_005A4F50_MonAttackStats` | attack-time to-hit, damage, elemental damage (not creation) | I |
| `0x005A4F20` | `sub_005A4F20_PlayerDmgBonus` | expansion nightmare/hell damage bonus per player count | I |
| `0x006272B0` | `sub_006272B0_UnitAddStat` | `STATLIST_AddStat(unit+0x5C, stat, v, param)` if `v ≠ 0` | C |
| `0x00625D10` | `sub_00625D10_UnitGetMaxHp` | stat 7 (layer 0) of the unit's list | C |
| `0x00463900` | `sub_00463900_MonClassCheck` | class id or −1 | I |
| `0x00658720` | `sub_00658720_MonPropLoad` | `monprop` descriptor + `DATATBLS_LoadTable` | C |
| `0x00617D90` | `sub_00617D90_DifficultyLevelsLoad` | `difficultylevels` descriptor + load | C |
| `0x0055B800` | `sub_0055B800_MonStatCallback` | the unit's stat-change callback; stat 7 rescales 6 and 74 (§ 11) | C |
| `0x00626D40` | `sub_00626D40_UnitStatListCreate` | new stat list with a change callback (frees the old one) | I |

## Walkthrough

### 1. The two loader descriptors

Each loader builds the 20-byte descriptor entries `{column, type, len, offset, link}` of
[data/0001 § 1](../data/0001-excel-loader.md#1-load-path-of-one-table) on the stack and passes them to `DATATBLS_LoadTable`.

- [C] MonProp (`0x00658744` …, call at `0x006594B3`, record size `0x138`): per slot, `prop` type `0x13` with link
  `0x0096BCD8` (the `properties` link), `par` type 2 (s32), `chance` type 4 (u8), `min` and `max` type 2. Slot 1 normal:
  `prop1` `+0x04`, `par1` `+0x08`, `chance1` `+0x124`, `min1` `+0x0C`, `max1` `+0x10`; `prop1 (N)` `+0x64`, `par1 (N)`
  `+0x68`, `chance1 (N)` `+0x12A`; `prop1 (H)` `+0xC4`, `chance1 (H)` `+0x130`, `par1 (H)` `+0xC8`. `Id` is type `0x12` with
  link `0x0096C85C`. The records go to `g_pMonProp` (`0x0096C860`), the count to `g_nMonProp` (`0x0096C864`), which are
  `DataTables+0xC30`/`+0xC34`. Second path: the archivist's `excel_bin.py diff monprop` places every set cell at these
  offsets. (fn:sub_00658720_MonPropLoad@0x00658720, data:g_pMonProp@0x0096C860, data:g_nMonProp@0x0096C864, tbl:MonProp.txt:chance1)
- [C] DifficultyLevels (`0x00617DA0`–`0x006180B2`, record `0x58`, records to `g_pDifficultyLevels` `0x0096C8AC`, count
  `0x0096C8B0`): the offsets listed in the summary, every field type 2. Second path: the archivist's diff of all 66 cells.
  (fn:sub_00617D90_DifficultyLevelsLoad@0x00617D90, data:g_pDifficultyLevels@0x0096C8AC, tbl:DifficultyLevels.txt:ChampionDamageBonus)
- [I] `g_pDifficultyLevels` has three references: the loader, the unload at `0x006192BA` and `sub_00611D30_DifficultyRec`,
  which returns record `clamp(d, 0, n − 1)`. So every reader passes through it, with `game+0x6D` at every call site read
  here. A scan of the 40 instructions after each of its 22 call sites finds displacements `+0x10` (`0x005739A5`,
  `0x005A6D84`, client `0x004AEB9C`), `+0x14` (`0x0057B2F1`), `+0x18` (`0x0057B00D`), `+0x1C` (`0x005C37A4`, `0x005C3A0C`,
  `0x004EE597`), `+0x28`/`+0x2C` (`0x0057C4AA`), `+0x34` (the three handlers), `+0x3C` (`0x005A2709`), `+0x40` (`0x005C9842`),
  `+0x44..+0x4C` (`0x005787B7`), and none of `+0x30` or `+0x38`. Only `+0x10` and `+0x34` were read as code here.
  (fn:sub_00611D30_DifficultyRec@0x00611D30)
- [I] **Full xref (Phase 2).** `g_pDifficultyLevels` has no other reference (the loader, the unload, `DifficultyRec`). Each
  of the 23 call sites of `DifficultyRec` was followed to every use of the returned pointer: those that keep it in a register
  or a local (`0x0048AE06` `[ebp-0x1C]`, `0x004A8540` `[ebp-0x18]`, `0x005359FB` `[ebp-4]`, `0x0055FC58` `EBX`, `0x005787B7`
  `[ebp-0x18]`, `0x0057C1F9` `[ebp-0x30]`, `0x005A7196` `ESI`, `0x005C9842` `[ebp+8]`) read `+0x00`, `+0x04`, `+0x08`,
  `+0x0C`, `+0x20`, `+0x24`, `+0x3C`, `+0x40`, `+0x44..+0x54`; the record stored at `[ebp-0x30]` by `0x0057C1F9` is part of
  a local block passed to `0x0057C060`, `0x0057C140` and `0x0057BF80`, none of which reads that member; the `+0x30` read at
  `0x00547AA3` is a Levels record (`0x0061DB70`), and the `+0x38` reads near `0x0057C3C2`/`0x0057C4B8` are a damage
  block. So no code reads `UniqueDamageBonus` (`+0x30`) or `HireableBossDamagePercent` (`+0x38`).
  (fn:sub_00611D30_DifficultyRec@0x00611D30, data:g_pDifficultyLevels@0x0096C8AC, 0x0057C206, 0x00547AA3)

### 2. `MonStatsInit` in order

`sub_00574250_MonsterInit` calls `MonStatsInit(game, room, regionEntry)` with `ESI` = unit, after
`sub_00547BC0_MonRegionFindAdd` returned the region entry ([monsters/0001 § 6](0001-level-pool.md#6-who-reads-the-pool-named-for-monstersspawn)).

```c
// fn:sub_00573CB0_MonStatsInit@0x00573CB0 (trimmed, renamed). ms = MonStats record, m2 = MonStats2 record
MonComponentsPick(ECX = regionEntry, EDX = unit);                       // draws (§ 6)
if (class == 311 /*doomknight2*/) mdata->b0E = Range(unit.seed, 4);     // draw
if (class == 312 /*doomknight3*/) mdata->b0E = mdata->b0F = Range(unit.seed, 4);   // draw
MonPlayerBonus(game, room, &pb);                                        // § 3
d = min(game->d, 2); if (HirelingType(unit)) d = 0;
level = ms->Level[d]; (expansion level rule, monsters/0001 § 5)
SetStat(12, level); SetStat(100, max(1, pb.players));
SetStat(36, ms->ResDm[d]); SetStat(37, ms->ResMa[d]); SetStat(39, ms->ResFi[d]);
SetStat(41, ms->ResLi[d]); SetStat(43, ms->ResCo[d]); SetStat(45, ms->ResPo[d]);   // s16 cells, as they are
SetStat(20, ms->ToBlock[d]);                                            // u8
SetStat(68, 100); SetStat(67, 75); SetStat(69, 100); SetStat(352, 128);
MonLvlStats(class, L, d, level, mask 7, &o);                            // HP, AC, XP (§ 4)
base = o.minHp + RangeB(unit.seed, o.maxHp - o.minHp + 1);              // draw
hp = base + MulDiv(base, pb.hpPct, 100); if (hp >= 0x800000) hp = 0x7FFFFF;
SetStat(7, hp << 8); SetStat(6, hp << 8);
SetStat(31, o.ac);
SetStat(13, o.exp + MulDiv(o.exp, pb.xpPct, 100));
r = ms->DamageRegen;                       // +0x1A0 u32; r < 0 -> fatal 222, r & 0xFFFFF000 -> fatal 223
SetStat(74, r == 0 ? 0 : (hp<<8) > 0x7FFFFFFF / r ? ((hp<<8) >> 12) * r : ((hp<<8) * r) >> 12);
MonClassicDiffAdjust(unit, game->expansion, game->d);                   // § 5
... inventory (MonStats +0x0F bit 0), unit flags ...
for k in 0..7: if (ms->Skill[k] >= 0 && ms->Sk_lvl[k] > 0) UnitSkillAdd(unit, ms->Skill[k], ms->Sk_lvl[k] + pb.skillBonus, 0) ...
MonProp slots (§ 7);  MonEquipInit(unit, -1, level, level, 1) (§ 6)
```

- [I] The resistances are read `movsx` (s16), `ToBlock` `movzx` (u8), each at `base + 2·d` / `base + d` of the
  [MonStats stat columns](../../tables/MonStats.md#stat-columns-plan-0025-phase-0); stat 20 is the `ToBlock` cell.
  `Drain`, `coldeffect`, `Crit`, the `A1/A2/S1` and `El*` columns are not read here. (0x00573E83–0x00573F39, tbl:MonStats.txt:ResFi, tbl:MonStats.txt:ToBlock)
- [I] Stat 67 is set to 75 (`push 0x4B`, `push 0x43` at `0x00573F14`), stats 68 and 69 to 100, stat 352 to 128.
- [I] **Skill levels.** For each of the eight `Skill<k>` (`+0x170 + 2k`, s16) ≥ 0 with `Sk<k>lvl` (`+0x198 + k`, s8) > 0, the
  skill is added at `Sk<k>lvl + MonsterSkillBonus` (DifficultyLevels `+0x10`, 0 / 3 / 7 by data); a `Sk<k>mode` (`+0x180 + k`)
  ≥ 0 also sets the skill's mode. `UnitSkillAdd` reaches RNG only through its player branch (`unit->type == 0`). (0x005740E0–0x00574135, fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, tbl:MonStats.txt:Sk1lvl, tbl:DifficultyLevels.txt:MonsterSkillBonus)
- [I] **hpregen** is computed from the HP before the classic adjustment of § 5. A negative `DamageRegen` or one with any bit
  above bit 11 set stops the game with message 222 / 223. (0x00573FF6–0x00574058, tbl:MonStats.txt:DamageRegen)

### 3. The player count (`sub_00573930_MonPlayerBonus`)

```c
// fn:sub_00573930_MonPlayerBonus@0x00573930: ECX game, EDX out (MonPlayerBonus), stack (room, unit)
out = {0, 0, 0, 0, 0};
if (unit is a monster with a MonStats record) {
    if (ms->Align == 0) { n = PlayerCount(game); if (n < 1) n = 1;
                          out.hpPct = PlayerHpPct(n); out.xpPct = PlayerXpPct(n); out.players = n; }
    else out.players = 1;
    rec = DifficultyRec(game->d); if (game->d >= 3) game->d = 2;        // writes the game byte
    out.skillBonus = rec->MonsterSkillBonus; out.difficulty = game->d;
}
```

- [I] `g_PlayerHpPct` (`0x006E1590`) and `g_PlayerXpPct` (`0x006E15B4`) are nine dwords each, `0, 0, 50, 100, 150, 200, 250,
  300, 350`: `(n − 1)·50` for `n` = 1..8. For `n` ≥ 9, HP uses `(n − 2)·50` and XP `10n + 260`, which both give 350 at 9.
  `PlayerCount` (`sub_00535790_PlayerCount`, [items/0001](../items/0001-tc-resolution.md)) is the alive players raised to the
  `/players` setting in game types 1–3. (fn:sub_005738F0_PlayerHpPct@0x005738F0, fn:sub_00573910_PlayerXpPct@0x00573910, data:g_PlayerHpPct@0x006E1590, data:g_PlayerXpPct@0x006E15B4)
- [I] `Align` is MonStats `+0x4C` (0 enemy). Town NPCs, critters, hirelings and player summons (`Align` 1) and `cow`/`camel`
  (2) get no HP or XP bonus and `players` 1. (0x0057396C, tbl:MonStats.txt:Align)
- [I] **No rescale.** `PlayerCount` has two callers, `TC_ResolveDrops` and this function; `MonPlayerBonus` is called by
  `MonStatsInit` and by four attack/skill functions (`0x005E8810`, `0x005E9750`, `0x005F0B00`, `0x005FC450`) that use the
  record but write no HP. Stat 100 keeps the creation count for later readers (crushing blow `0x005BFFC0` reads it with
  `PlayerHpPct`). So the HP, XP and stat 100 of a live monster do not follow a later player-count change.

### 4. `MonLvlStats` and `MulDiv`

```c
// fn:sub_006538A0_MonLvlStats@0x006538A0 (class, L, d, level, mask, out), stdcall
row = &MonLvl[min(level, nMonLvl - 1)];           // a negative row index returns 0, out untouched
d = d < 1 ? 0 : min(d, 2);
ratio = !(ms->flags0C & 0x04 /*noRatio*/);
if (mask & 1) { out.minHp = ratio ? MulDiv(row->hp[L][d], ms->minHP[d], 100) : ms->minHP[d];
                out.maxHp = ratio ? MulDiv(row->hp[L][d], ms->maxHP[d], 100) : ms->maxHP[d]; }
if (mask & 2)   out.ac  = ratio ? MulDiv(row->ac[L][d], ms->AC[d], 100)  : ms->AC[d];
if (mask & 4)   out.exp = ratio ? MulDiv(row->xp[L][d], ms->Exp[d], 100) : ms->Exp[d];
// masks 8/0x10/0x20: to-hit row->th × A1TH/A2TH/S1TH and damage row->dm × A1/A2/S1 Min/MaxD
// masks 0x40/0x80/0x100: El1..3 Min/MaxD × row->dm into out.elMin/elMax, El<e>Dur raw into out.elDur
```

- [I] MonStats cells are read `movsx` (s16), MonLvl cells as dwords; the MonLvl offsets are `0x30 + 0xC·L + 4·d` (HP),
  `0x00 + …` (AC), `0x60 + …` (XP), `0x18 + …` (TH), `0x48 + …` (DM), i.e. `struct:MonLvlRec`. (0x0065395C–0x00653A00, tbl:MonLvl.txt:HP, tbl:MonLvl.txt:L-HP)
- [I] For a `noRatio` class the elemental masks write the raw cells into `s1Min`/`s1Max` (`+0x24`/`+0x28`), not `elMin`/`elMax`,
  so a caller that reads `elMin` gets 0 for such a class. Creation uses mask 7 only. (0x00653BCD–0x00653BE3)
- [I] **`MulDiv(a, b, c)`** (ECX `a`, EDX `b`, stack `c`; signed): `c == 0` → 0. If `a > 0x100000`: `c ≤ a >> 4` →
  `(a / c)·b`, else the 64-bit `a·b / c`. Else if `b > 0x10000`: `c ≤ b >> 4` → `(b / c)·a`, else 64-bit. Else `(a·b) / c`
  in **32 bits** (`imul`, `idiv`, truncation toward zero). On stock data every creation call takes the last branch without
  overflow (largest products: MonLvl HP 10 000 × `maxHP` 9 981; MonLvl XP 160 000 × `Exp` ≤ 6 600 < 2³¹).
  (fn:sub_00483360_MulDiv@0x00483360, 0x00483376–0x004833D7)

### 5. Classic nightmare and hell (`sub_0063EEF0_MonClassicDiffAdjust`)

```c
// fn:sub_0063EEF0_MonClassicDiffAdjust@0x0063EEF0 (unit, expansion, d), stdcall; called once, from MonStatsInit
if (expansion != 0 || d == 0 || ms->Align == 1) return;
for row in g_ClassicDiffAdjust[0..2]:           // {7, 1,2, 1,2}, {31, 10,12, 10,12}, {13, 10,17, 10,26}
    v = STATS_GetUnitStat(unit, row.stat);
    SetStat(row.stat, d == 1 ? MulDiv(v, row.nmMul, row.nmDiv) : MulDiv(v, row.hellMul, row.hellDiv));
SetStat(12, ms->Level[0] + 25 * d);             // MonStats Level (normal), +0xAA
```

- [C] The table writes only stat 7 (max HP), but the unit's stat callback (§ 11) rescales stat 6 (current HP) with it and
  recomputes stat 74, so both end halved (corrected 2026-10-15: Phase 1 said stat 6 kept the unhalved value).
  (0x0063EF40–0x0063EF94, fn:sub_0055B800_MonStatCallback@0x0055B800, run:2026-10-15-mon-stats)
- [I] In a classic game the level
  used for the MonLvl row is still MonStats `Level(N)`/`Level(H)` (§ 2, monsters/0001 § 5); the level **stat** becomes
  `Level + 25·d` afterwards, and every later reader of stat 12 (the mod handlers, the attack code) sees that value.
  (0x0063EF40–0x0063EF94, data:g_ClassicDiffAdjust@0x006EA9F0, tbl:MonStats.txt:Level)
- [I] `d` here is the game byte, not the hireling-forced 0; a hireling (`Align` 1) is skipped anyway. (0x0057405D–0x0057406A, tbl:MonStats.txt:Align)
- [I] **The classic aura level** ([special.md open question](../../specs/monsters/special.md#open-questions),
  [monsters/0003 § Open questions](0003-special-monsters.md#open-questions)): `UModAura` reads stat 12 after `leveladd`, so in a
  classic nightmare/hell game it reads `Level + 25·d + 3`. Both classic aura uniques of run:2026-10-14-mon-special are class 8
  `zombie4` (`Level` 22, `Level(N)` 50): logged 50 = 22 + 25 + 3, and not `Level(N)` + 3 = 53. The run cannot tell this rule
  from "bare `Level(N)`" for this class; a classic unique whose `Level + 25·d ≠ Level(d)` is a Phase 2 case. (fn:sub_005A1650_UModAura@0x005A1650, run:2026-10-14-mon-special)

### 6. Appearance and MonEquip draws

```c
// fn:sub_005739D0_MonComponentsPick@0x005739D0: ECX region entry, EDX unit
if (entry != 0 && entry->nVariants != 0) {
    i = RangeB(unit.seed, entry->nVariants);                 // draw
    copy entry->variant[i] (16 bytes) to MonsterData+0x04;
} else for k in 0..15:                                       // into MonsterData+0x04+k
    c = MonCompCount(unit, k);                               // MonStats2 m2+0x15+k
    v[k] = c < 1 ? 0 : step(unit.seed), (c & (c-1)) == 0 ? low & (c-1) : low % c;   // a draw also when c == 1
```

- [I] The fallback draws for every component with a count ≥ 1, unlike `MonVariantRoll`, which skips counts < 2
  ([monsters/0001 § 4](0001-level-pool.md#4-variant-sets-sub_005bdb20_monvariantrollr-entry-n--3)). (fn:sub_005739D0_MonComponentsPick@0x005739D0, fn:sub_006647C0_MonCompCount@0x006647C0, struct:MonRegionEntry+0x03)
- [I] **MonEquip** (`sub_005D6B60_MonEquipInit(unit, EDX = 0, −1, level, level, 1)`): runs only when the class has a
  `monequip` row with its `oninit` byte set and the unit has an inventory (`unit+0x60`). From the first row of the class whose
  level ≤ the monster level, for each following row of the class: `k` = the number of leading item slots with a location
  1..10 (≤ 3); if `k` > 0, one step of the unit seed picks one (`low & (k−1)` or `low % k`), and when that location is free the
  item is created (`0x00573B20` → `ItemCreate`, which draws on the game seed for the new item's unit seed and on its own
  seeds). (fn:sub_005D6B60_MonEquipInit@0x005D6B60, fn:sub_005D30A0_MonEquipFirstRow@0x005D30A0)

### 7. MonProp at creation

```c
// fn:sub_00573CB0_MonStatsInit@0x00573CB0, 0x0057416A–0x00574220 (trimmed)
rec = MonPropRec(class);                                   // MonStats +0x1A, else 0
if (rec) for k in 0..5:
    slot = &rec->slot[d][k];  if (slot->prop < 0) break;
    c = rec->chance[d][k];
    if (c == 0 || (step(unit.seed), low % 100 < c))        // draw only when c > 0
        PROP_ApplyBlock(0, 0, unit, 0, 0, 0, slot, 0, 0x40, 0);
```

- [I] `d` is the same difficulty as the stats (0 for hirelings). The `% 100` is unsigned (`mul 0x51EB851F`, `shr 5`) on the
  new low word; the compare is `< chance`. Stock `chance` is 0 in every slot, so every set slot applies and no `chance` draw is
  made on stock data. (0x005741B1–0x005741F4, tbl:MonProp.txt:chance1)
- [I] With mode 0, `PROP_ApplyBlock` resets nothing; `PROP_RollValue` draws on the unit's own seed (not an item seed) when
  `min ≠ max`, which in stock data is only `thorns` (`quillrat6..8`, nightmare 15..20, hell 30..40)
  ([items/0006 § 4](../items/0006-properties.md#4-the-handlers-per-func)). The property's stats go into the unit's property list
  with flags `0x40`. (fn:PROP_ApplyBlock@0x0065FD70, fn:PROP_RollValue@0x0065E9E0)
- [I] `sub_00573470_MonPropRec` is the only reader of `g_pMonProp` (`0x005734AC`). `0x004E4640` compares an index with
  `g_nMonProp` but reads another table (`DataTables+0xC3C`). So the `irongolem` row, named by no MonStats record, is never
  applied. (fn:sub_00573470_MonPropRec@0x00573470, data:g_pMonProp@0x0096C860)

### 8. The mod handlers' stat effects

Order: `SpecialModsApply` runs mods 1, 2, 3, 4 (3 has no handler), then the mod list in order; after each, the same
handler with flag 0 on each group member ([monsters/0003 § 4](0003-special-monsters.md#4-specialmodsapply-and-the-per-handler-draw-table)).
`c[i]` is MonUMod `constants` row `i` (`sub_005A00F0_UModConstant`, 0 when `i` ≥ the row count); stock values in
[MonUMod](../../tables/MonUMod.md#interpretation-notes). `CDB` is DifficultyLevels `ChampionDamageBonus` (`+0x34`; 90 / 75 / 66 by data), from the
record of `game+0x6D`. "÷100" is signed 32-bit division
truncating toward zero (`0x51EB851F`, `sar 5`, sign fix). `lvl` is stat 12 at the time of the call.

| Mod (row) | Handler | Flag 1 (the special) | Flag 0 (group member) | Tag |
|---|---|---|---|---|
| 2 `hpmultiply` | `sub_005A0DC0_UModHpMultiply` | `MonHpAddPct(c[4+d])` if the champion flag (`MonsterData+0x16` & 4), else `c[7+d]`; then SetStat(74, 0) | `MonHpAddPct(c[1+d])` | I |
| 4 `leveladd` | `sub_005A0E40_UModLevelAdd` | SetStat(12, lvl + 3); SetStat(13, base 13 × 5) | the same (no flag test) | I |
| 16 `champion` | `sub_005A0E80_UModChampion` | SetStat(12, lvl − 1); SetStat(13, x − 2·(x/5)) (unsigned); AddStat(25, CDB·c[11]÷100, halved if base class 118); AddStat(119, CDB·c[10]÷100); velocity by mod id (below) | nothing | I |
| 36 `ghostly` | `sub_005A1080_UModGhostly` | flag `0x40`; SetStat(36, 80); `champion` part (no velocity); AddStat(54, c[22+d]·DM÷100), AddStat(55, c[25+d]·DM÷100), AddStat(56, 150) | nothing | I |
| 37 `fanatic` | `sub_005A11F0_UModFanatic` | SetStat(16, −70); `champion` part, velocity `clamp(2048/Velocity − 128, 10, 100)` | nothing | I |
| 38 `possessed` | `sub_005A1230_UModPossessed` | flag `0x20`; `MonHpAddPct(100)`; `champion` part, velocity + 20 | nothing | I |
| 39 `berserk` | `sub_005A1280_UModBerserk` | `MonHpAddPct(−75)`; AddStat(25, CDB·300÷100, halved for base class 118); AddStat(119, CDB·300÷100); **no `champion` part** | nothing | C (run:2026-10-15-berserk-forced) |
| 5 `strong` | `sub_005A17E0_UModStrong` | AddStat(25, CDB·c[15]÷100, halved for 118); AddStat(119, CDB·c[13]÷100) | AddStat(25, CDB·c[14]÷100, halved for 118); AddStat(119, CDB·c[12]÷100) | I |
| 6 `fast` | `sub_005A1910_UModFast` | AddStat(67, `clamp(2048/Velocity − 128, 10, 100)`) if `Velocity` > 0 | the same | I |
| 9, 17, 18, 23, 25 enchant | `UModFire`, `UModLightning`, `UModCold`, `UModPoisonHit`, `UModManaHit` | min = c[28+d]·DM÷100, max = c[31+d]·DM÷100 into (48, 49), (50, 51), (54, 55), (57, 58), (62, 63) by AddStat; cold also AddStat(56, 5·ℓ + 100), poison AddStat(59, (5·ℓ + 150)·2), mana both × 256; then `resist` | min c[16+d], max c[19+d], the same stats; no `resist` | I |
| 8 `resist`, 27 `spectralhit`, 28 `stoneskin` (and after each enchant) | `sub_005A1370_UModResist` | below | nothing | I |
| 30 `aura` | `sub_005A1650_UModAura` | aura skill and level ([monsters/0003 § 4](0003-special-monsters.md#4-specialmodsapply-and-the-per-handler-draw-table)) | nothing | I |
| 26 `teleport` | `sub_005A1600_UModTeleport` | adds a skill at level 1 and sets its mode | nothing | I |
| 41 `always_run_ai` | `sub_005A1330_UModAlwaysRunAi` | AI event 7 at frame `game+0xA8 + 75`; no stat | the same | I |

- [I] **`MonHpAddPct(pct)`** (`sub_005A0D20`, `EBX` unit, `EDI` pct): `h` = stat 7 (`sub_00625D10_UnitGetMaxHp`, the 8.8 value);
  `h' = h + q` with `q` = `(h / 100)·pct` when `h > 0x100000`, `(pct / 100)·h` when `pct > 0x10000` and `pct ≥ 1600`, the
  64-bit `h·pct / 100` when `pct > 0x10000` and smaller, else `(h·pct) / 100`; then SetStat(7, h') and SetStat(6, h'). Because
  `h` is HP × 256, a monster with more than 4 096 HP takes the `(h / 100)·pct` branch, which truncates before multiplying.
  The handlers stack: a champion `possessed` gets `c[4+d]` then +100 % of the result. (fn:sub_005A0D20_MonHpAddPct@0x005A0D20, 0x005A0D29–0x005A0DB8)
- [I] `hpmultiply` does nothing when `game+0x6D` ≥ 3. Its flag-1 branch tests `MonsterData+0x16 & 4` through
  `sub_005A0180_MonTypeFlag(unit, 4)`. (0x005A0DDE–0x005A0E34, struct:MonsterData+0x16)
- [I] **Champion velocity** (by the mod id in `EDX`, `0x005A0FE7`–`0x005A1069`), only when MonStats `Velocity` (`+0x32`, u16) > 0:
  36 (`ghostly`) nothing; 37 (`fanatic`) the formula above; any other id (16, 38) AddStat(67, 20). The branch that would add
  −33 for 36 is unreachable (the id is tested for 36 twice). (tbl:MonStats.txt:Velocity)
- [I] Base class 118 is `willowisp1` (`sub_00463860_MonBaseId`, then `sub_00463900_MonClassCheck`; `strong` inlines the
  check as `0 ≤ id < nMonStats`), so Gloams, Burning Souls and Black Souls take half the damage bonus of `champion`,
  `berserk` and `strong`. (0x005A0FB7–0x005A0FCF)
- [I] **The halving is a signed division by 2 truncating toward zero**: `cdq; sub eax, edx; sar eax, 1` on the stat-25
  value already divided by 100 (`÷100` above), i.e. `h = q ÷ 2` with `q = CDB·c ÷ 100`, never `q >> 1`. Only stat 25 is
  halved; stat 119 (to-hit) is not. With stock values `q` ≥ 0, so `÷ 2` and `>> 1` agree there; they differ only for a
  negative odd `q`. No `willowisp1` special was met in run:2026-10-15-mon-stats. (champion 0x005A0FC8–0x005A0FCF,
  berserk 0x005A12FD–0x005A1304, strong 0x005A18E6–0x005A18ED; the AddStat(25) pushes follow at 0x005A0FD3, 0x005A1308,
  0x005A18F1)
- [I] **Enchant base.** `ℓ = clamp(lvl, 1, nMonLvl − 1)` (`lvl < 2` → 1), `DM` = MonLvl `DM[L][d]` of row `ℓ`; `d` from
  `game+0x6D` clamped to 2, `L` as above. Every enchant handler uses this `ℓ` also for the cold and poison lengths. (0x005A1A00–0x005A1AD8, tbl:MonLvl.txt:DM)
- [I] **`resist`** (`sub_005A1370_UModResist`, `EDX` = mod id, flag 1 only): mod 28 first doubles stat 31. Then `k` = how many
  of fire, light, cold, poison, damage and magic resist (stat values) are ≥ 100; when `k` < 2 (fn:sub_005A1370_UModResist@0x005A1370):
  - 8 `resist`: cold, then fire, then lightning: each one < 100 gets + 40, `k` + 1 when it reaches 100, stop when `k` = 2;
  - 9 / 18 / 17 / 23: fire / cold / lightning / poison + 75 (no cap);
  - 25 `manahit`: magic + 20;
  - 27 `spectralhit`: cold, fire, lightning, each < 75 gets + 20, with the same `k` rule;
  - 28 `stoneskin`: damage resist + 50.

  All writes are SetStat of `old + delta`. (fn:sub_005A1370_UModResist@0x005A1370)
- [C] None of these handlers draws on any seed ([monsters/0003 § 4](0003-special-monsters.md#4-specialmodsapply-and-the-per-handler-draw-table)). (fn:sub_005A2120_SpecialModsApply@0x005A2120, run:2026-10-14-mon-special)

### 9. To-hit and damage at attack time (`sub_005A4F50_MonAttackStats`)

- [I] Called with an attack mode in `EDX`; reads stat 12 now, calls `MonLvlStats` with mask `0x10` (mode 5), `0x20` (modes 7, 8)
  or `0x08` (others), adds the skill-damage pair of `0x0056E050`, then: in a classic game with `d` > 0 and `Align` ≠ 1,
  damage × 10/12 and to-hit × 10/15; in an expansion game, `b = sub_005A4F20_PlayerDmgBonus(game, stat 100)` (0 for `d` = 0 or
  `n` < 2, else `8·(n − 1)`, `8n − 16` for `n` ≥ 9) adds `x·b / 128` to each. It writes stats 21, 22 and 19 to a list of the
  unit (`0x00625760(unit, 1)`), and for each `El<e>` whose mode matches, applies it when `El<e>Pct` ≥ 100 or
  `RNG_Range(unit seed, 100) < El<e>Pct` (a draw), with type 10 drawing `Range(unit seed, 5)`.
  (fn:sub_005A4F50_MonAttackStats@0x005A4F50, fn:sub_005A4F20_PlayerDmgBonus@0x005A4F20, data:g_PlayerDmgBonus@0x006E21F4)
- So to-hit, damage and elemental damage are attack-time quantities with draws on the unit seed during combat, not creation
  stats. They are out of the Phase 2 creation model (§ 10).

### 10. Boundary decision for Phase 2 (recommendation)

1. **Model in full**: the appearance pick, the doomknight `Range(4)`, the HP draw and arithmetic, AC, XP, the player
   count, resistances, block, the constant stats, hpregen, the classic adjustment, MonProp (both its `chance` gate and the value
   roll on the unit seed), and every mod handler's stat writes (§ 8). All are integer arithmetic on table cells.
2. **Boundary oracle**: `MonEquipInit`'s item creation (game-seed and item-seed draws belong to `items/*`); log the unit seed
   before and after `MonEquipInit` and assert the one step per row.
3. **Out of scope**: to-hit, damage and elemental damage (attack time, § 9), skills and AI (only the skill id and level set at
   creation are logged and compared), and what an aura does in combat.
4. **Log** stats 6, 7, 12, 13, 20, 31, 36–45, 48–63, 67, 74, 100, 119 and 16, 25 at the end of `MonsterInit` and again after
   `SpecialModsApply`.

### 11. The stat callback (`sub_0055B800_MonStatCallback`)

```c
// MonStatsInit 0x00573E56: before the first SetStat, the unit gets a new stat list with a change callback
UnitStatListCreate(unit, 0, MonStatCallback, game);         // sub_00626D40: frees the old list, allocates the new
// fn:sub_0055B800_MonStatCallback@0x0055B800 (ECX game?, EDX unit, stack (?, stat << 16 | param, old, new))
switch (stat) {                                             // byte table 0x0055BE04, jump table 0x0055BDD8: 7, 9, 11,
case 7:                                                     // 83, 97/107, 98, 126/127, 151, 188, 204 have cases
    if (new == old || old <= 0) break;
    cur = STATS_GetUnitStat(unit, 6); if (cur <= 0) break;
    if (old <= 0x100) old = 0x100;
    v = _ftol((float)(new / old * cur));                     // fild / fidiv / fimul, fstp to a float32, truncated
    SetStat(unit, 6, clamp(v, 1, new));
    if (unit is a monster && (r = MonStats(unit)->DamageRegen) != 0) SetStat(unit, 74, ((new >> 8) * r) >> 4);
}
```

- [C] The stat-7 case is what changes stats 6 and 74 when max HP changes after creation: in `MonClassicDiffAdjust`
  (classic nightmare and hell: stat 6 is halved with it, stat 74 recomputed) and in `MonHpAddPct` (the handler then writes
  stat 6 itself, and `hpmultiply` with flag 1 writes stat 74 = 0; with flag 0 the callback's stat 74 stays). The first
  `SetStat(7)` of `MonStatsInit` has `old` = 0 and does nothing. `tools/monstats.py` models it with a float32 rounding of
  the double-precision product and reproduces every classic nightmare/hell creation and every `hpmultiply` call of the run.
  (fn:sub_0055B800_MonStatCallback@0x0055B800, fn:sub_00626D40_UnitStatListCreate@0x00626D40, 0x00573E62, run:2026-10-15-mon-stats)
- [I] **The x87 control word in force.** The callback computes `fild new` / `fidiv old` / `fimul cur` at the x87 precision
  control (PC) and rounding control (RC) of the thread, stores to float32 (`fstp dword`, rounded by RC), reloads it and
  calls `CRT_ftol2` (`0x00682FD0`: `cvttsd2si` when SSE2 is present, else the x87 `_ftol2` path), which truncates toward
  zero whatever RC is. (0x0055B926–0x0055B935)
  - Game.exe sets the control word once, in the statically linked MSVC CRT start-up: entry `0x00682985` →
    `CRT_tmainCRTStartup` (`0x006827A5`) → `CRT_cinit(1)` (`0x006828E9`–`0x006828EA`, `EBX` = 1 from `0x00682872`) → the
    `_FPinit` pointer `data:g_CRT_FPinit@0x006F2874` = `CRT_fpmath` (`0x00682FAE`) → `CRT_setdefaultprecision` (`0x0068E70A`) =
    `_controlfp_s(NULL, 0x10000 /* _PC_53 */, 0x30000 /* _MCW_PC */)` (`CRT_controlfp_s`, `0x0069C622`). Only the precision field is
    written: 53-bit significand; RC and the exception masks keep the thread's initial value (0x027F on Windows and wine:
    round to nearest, all exceptions masked). `CRT_fpreset` (`0x006ADD36`: `fninit`, the same `_PC_53`, MXCSR 0x1F80)
    has no direct caller.
  - A linear sweep of `.text` (objdump) finds 64 `fldcw`. Each one in code is either half of a save/set/restore pair
    (`fnstcw` to a local, `fldcw` of a modified copy, `fldcw` of the saved word a few instructions later): 14 pairs in
    game code between `0x0047CCDF` and `0x0067A1E9`, and the CRT math helpers from `0x006879DE` to `0x006AE777`; or the
    CRT's own control-word setters (`CRT_ctrlfp` at `0x0069D097`, the `_control87` behind `_controlfp_s`); or a misdecoded
    jump table (`0x006BE0A1`). No game code changes PC or RC persistently.
  - [C] Corroboration: the run excludes round-toward-zero (282 of the 825 logged stat-6 rescales would differ) and a
    24-bit precision control (4 would differ); the model's "double product, float32 store" is PC 53 with RC nearest and
    reproduces all 825 (re-analysis of run:2026-10-15-mon-stats with `tools/monstats.py fpsens`). PC 53 and PC 64 give
    the same result on every logged call, so the run does not separate them; the 53 bits are from the code only.
    (fn:CRT_setdefaultprecision@0x0068E70A, fn:CRT_fpmath@0x00682FAE, fn:CRT_cinit@0x00681C95, fn:CRT_ftol2@0x00682FD0, run:2026-10-15-mon-stats)
  - Outside Game.exe, a renderer DLL could still reset the control word of the thread that creates its device (*Open
    questions*).
- [I] The other cases (9, 11, 83, 97, 98, 107, 126, 127, 151, 188, 204) were not read; no creation stat of the run reaches
  them. (data:0x0055BE04 byte table, 0x0055BDD8)

### 12. Phase 2 results (run:2026-10-15-mon-stats)

`tools/monstats.py check` runs `tools/monspawn.py`'s checker (with `tools/monspecial.py`, the DRLG models and
`tools/monpool.py`) on the same logs, then predicts, per creation, every unit-seed draw of `MonStatsInit` and the stat list
after the classic adjustment, after MonProp and at the exit; per handler call with flag 1 or 0, the stat list after it;
and at each player-count change, stats 7, 12, 13 and 100 of every live monster. Base stats are compared as the set of
non-zero entries. Details and numbers are in [experiments § run:2026-10-15-mon-stats](experiments.md#run2026-10-15-mon-stats).

| Required case (plan 0025) | Result |
|---|---|
| ≥ 500 monsters, three difficulties, classic and expansion, player counts 1, 3 and 8 | 4 571 creations: expansion normal 376, nightmare 1 464, hell 2 206; classic normal 163, nightmare 231, hell 131; counts 1 (908, town NPCs included), 3 (1 550), 8 (2 113) |
| a player-count change during a session (no rescale) | 13 changes in nine games; 302 live monsters compared (stats 7, 12, 13, 100), all equal to their creation values |
| champions, uniques, superuniques with every stat-changing mod met | 16 champion packs, 49 unique groups, 7 superuniques; handlers reproduced: `hpmultiply`, `leveladd`, `champion`, `ghostly`, `fanatic`, `possessed`, `strong`, `fast`, `fire`, `lightning`, `cold`, `manahit`, `resist`, `spectralhit`, `stoneskin` (and the no-stat `rndname`, `teleport`, `aura`) with flags 1 and 0 |
| mods not met | `berserk` 39 (12 champion picks, none drew it; met on a forced path, run:2026-10-15-berserk-forced, 33 berserkers, 0 mismatches), `poisonhit` 23 (unique weight 0 in every difficulty: superunique fixed mods only, none met), base class 118 (`willowisp1`) halving |
| a MonProp row in each difficulty where one exists | nightmare: `thorns` 15..20 (`quillrat8`, value roll on the unit seed, 242 creations) and `crush` 15 (`blunderbore1`, classic); hell: `crush` 25 (classic); normal: **unreachable** (the only normal rows are `baboon6`, which spawns from no normal pool, `druidhawk`, a druid summon, and `irongolem`, never read) |
| a classic `aura` unique (the level question) | classic hell, class 48: 5 aura uniques, level 71 = `Level` 18 + 50 + 3, not `Level(H)` + 3 = 81 |
| Phase 1b: `L-` MonLvl columns in single player | 3 954 nightmare/hell creations where the two sets differ: all match `L-` |
| Phase 1b: Spectral Hit + 20 | 17 `spectralhit` uniques, e.g. class 5 cold/fire/lightning 0/0/0 → 20/20/20, class 58 40/165/40 → 60/165/60 |
| Phase 1b: berserker level + 3 | not met here; met in run:2026-10-15-berserk-forced (33 berserkers + 3, 56 champion members + 2) |
| Phase 0 ruling: reversed or blank MonStats ranges | not met (no `minionspawner1`, `mephistospirit`, `andariel` or `wakeofdestruction` creation) |

- [L] **Re-created monsters.** A monster whose room went inactive is created again, with the same unit id and class,
  through a full `MonsterInit` (a new unit seed and HP draw, which the model predicts), and its stats 7, 12 and 13 then hold
  the values of the first instance while stat 100 is the new instance's. 57 such monsters were met at a player-count
  change. The restore code itself was not read; the model takes the rule from the run, so it stays a lead
  under *Open questions* for `monsters/spawn`. (run:2026-10-15-mon-stats)
- [C] **Champion packs.** Every champion-pack member runs its own `SpecialModsApply` with flag 1 (logged `HST` with the
  champion flag); no flag-0 handler call follows a champion, so a champion leader's `hpmultiply`/`leveladd` group pass reaches
  no pack member (36 champion-pack specials, no flag-0 call after any of them). Flag-0 calls go to the minions of uniques
  and superuniques only; a superunique with the fixed `champion` mod passes mod 16 to its minions too, where it does
  nothing. (fn:sub_005A2120_SpecialModsApply@0x005A2120, run:2026-10-15-mon-stats)

## Data touched

- `tbl:MonStats.txt:Level`, `tbl:MonStats.txt:minHP`, `tbl:MonStats.txt:MaxHP(N)`, `tbl:MonStats.txt:AC`, `tbl:MonStats.txt:Exp`,
  `tbl:MonStats.txt:ResDm` … `tbl:MonStats.txt:ResPo`, `tbl:MonStats.txt:ToBlock`, `tbl:MonStats.txt:DamageRegen`,
  `tbl:MonStats.txt:Velocity`, `tbl:MonStats.txt:Align`, `tbl:MonStats.txt:MonProp`, `tbl:MonStats.txt:Skill1`,
  `tbl:MonStats.txt:Sk1lvl`.
- `tbl:MonLvl.txt:HP`, `tbl:MonLvl.txt:AC`, `tbl:MonLvl.txt:XP`, `tbl:MonLvl.txt:DM`, `tbl:MonLvl.txt:TH` and the `L-` columns.
- `tbl:MonProp.txt:prop1`, `tbl:MonProp.txt:par1`, `tbl:MonProp.txt:chance1`, `tbl:MonProp.txt:min1`, `tbl:MonProp.txt:max1`
  (all difficulties).
- `tbl:DifficultyLevels.txt:MonsterSkillBonus`, `tbl:DifficultyLevels.txt:ChampionDamageBonus`.
- `tbl:MonUMod.txt:constants` rows 1–33.
- `struct:MonLvlRec+0x30`, `struct:MonLvlStatsOut+0x10`, `struct:MonPlayerBonus+0x08`, `struct:MonPropRec+0x124`,
  `struct:DifficultyLevelsRec+0x34`, `struct:ClassicDiffAdjustRow+0x04`, `struct:MonsterData+0x16`, `struct:MonRegionEntry+0x03`.

## Dead ends

- `UniqueDamageBonus` looked like the uniques' counterpart of `ChampionDamageBonus`. The `strong` handler with flag 1 (uniques)
  reads `+0x34` too, and no reader of `+0x30` was found. The two columns are equal in stock data, so nothing changes in play.
- The decompiler shows `MonStatsInit`'s locals `local_18`/`local_20` as uninitialised: they are `MonPlayerBonus.players` and
  `.skillBonus`, written through `EDX` by `sub_00573930`.
- The 3-step creations of run:2026-10-14-mon-special (classes 58, 142, 259, 368, 405) are not MonProp classes; they fit the
  per-component fallback of § 6 (a region entry without variant sets, two components with a count ≥ 1). Not checked further.

## Open questions

- ~~Whether champion-pack members get a champion leader's flag-0 handlers~~ answered in § 12: they do not; each member
  runs its own flag-1 pass.
- ~~What happens to stat 6 after the classic halving of stat 7~~ answered in § 11: the stat callback scales it.
- ~~The `UniqueDamageBonus` and `HireableBossDamagePercent` readers~~ answered in § 1 (full xref): none.
- [L] The restore of a monster from an inactive room: the run shows stats 7, 12 and 13 written back from the first
  instance after a full new `MonsterInit`, and stat 100 kept from the new one (§ 12). Where that restore writes them, and
  whether it saves anything else (mods, current HP), is a `monsters/spawn` question (the `RW3` window of
  [monsters/0002](0002-room-population.md)).
- [L] Whether a renderer resets the x87 control word of the thread that runs the server's monster code (§ 11): Direct3D
  without an FPU-preserve flag sets a 24-bit precision control on the thread that creates the device. Which thread the
  1.14d Direct3D or Glide path creates it on, and with which flags, is unread; the run's configuration (`-w`) excludes PC 24
  for its own thread. A run in Direct3D or Glide mode would settle it with the same `fpsens` re-analysis.
- [L] The noRatio elemental-damage placement of § 4 (written to `+0x24`/`+0x28`, read at `+0x2C`/`+0x30` by the attack code).
  Combat, out of scope; noted for `monsters/combat` if that row is ever planned.
