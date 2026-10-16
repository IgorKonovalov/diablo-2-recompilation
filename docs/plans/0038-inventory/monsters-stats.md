# Plan 0038 inventory: monsters/stats

- **Spec:** [monsters/stats.md](../../specs/monsters/stats.md), read at `main` `e1c807a` (last change to the spec: `e5f7155`).
- **Front matter `I`:** 54; the *count* column sums to 54.
- **Finding:** [monsters/0004](../../findings/monsters/0004-stats.md) (sections given as `§n`; other subsystems' findings named in full).
- **Cluster:** 0c (monsters, hirelings, player). Classes, tiers and batches as in [plan 0038](../0038-inferred-claims-sweep.md#classes).
- Guard rows marked (a-logs) with "0 → d-none" are re-read first: a guard the later logs never took is reclassified d-none by the batch, not raised.

| # | Spec section | Claim | Finding anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/monsters/stats.md#entry-points) | Attack-time to-hit and damage | §9, MonAttackStats 0x005A4F50 | d (d-sim) | d-sim: plan 0037 (monsters/stats § H) | T2 | - | 1 |
| 2 | [Runtime state](../../specs/monsters/stats.md#runtime-state) | SetStat replaces, AddStat adds and skips 0 | §2, UnitSetStat 0x00627260 | a-logs | the 62 991 stat checks of run:2026-10-15-mon-stats use these semantics; list AddStat(…, 0) cases; addendum | T1 | S3a | 1 |
| 3 | [Constants](../../specs/monsters/stats.md#constants) | HP % and XP % for n ≥ 9 | §3, PlayerHpPct 0x005738F0 | d (d-none) | d-none: `/players` stops at 8 | T3 | - | 1 |
| 4 | [Constants](../../specs/monsters/stats.md#constants) | HP cap 0x7FFFFF | §2, 0x00573F7E | d (d-none) | d-none: stock HP stays far below | T3 | - | 1 |
| 5 | [Constants](../../specs/monsters/stats.md#constants) | MonsterSkillBonus 0 / 3 / 7 | §2, DifficultyLevels | b | log the skill list at SIX (new line); H4b sessions in the three difficulties | T1 | H4b | 1 |
| 6 | [Constants](../../specs/monsters/stats.md#constants) | c[i] = 0 beyond the row count | §8, UModConstant 0x005A00F0 | d (d-none) | d-none: no reader asks past row 33 | T3 | - | 1 |
| 7 | [Inputs and oracles](../../specs/monsters/stats.md#inputs-and-oracles) | MonEquipInit seed oracle | §6, MonEquipInit 0x005D6B60 | a-run | H4a Blood Raven (`oninit` row) and a `flyingscimitar` level | T3 | H4a | 1 |
| 8 | [Inputs and oracles](../../specs/monsters/stats.md#inputs-and-oracles) | Out of scope: attack stats, skills, AI | §9 | d (d-sim) | d-sim: plan 0037 | T2 | - | 1 |
| 9 | [A. MulDiv and MonLvlStats](../../specs/monsters/stats.md#a-muldiv-and-monlvlstats) | MulDiv branches beyond the 32-bit one | §2, MulDiv 0x00483360 | a-logs | other MulDiv callers in kept logs (XP, calc, items) with a > 0x100000 or b > 0x10000; none → d-none | T2 | S3a | 1 |
| 10 | [A. MulDiv and MonLvlStats](../../specs/monsters/stats.md#a-muldiv-and-monlvlstats) | level < 0: out untouched | §4 | d (d-none) | d-none | T3 | - | 1 |
| 11 | [A. MulDiv and MonLvlStats](../../specs/monsters/stats.md#a-muldiv-and-monlvlstats) | MulDiv other branches as read (note) | §4 | a-logs | as the A1 row | T2 | S3a | 1 |
| 12 | [A. MulDiv and MonLvlStats](../../specs/monsters/stats.md#a-muldiv-and-monlvlstats) | Cell widths; masks 8–0x100 are attack time | §4, 0x0065395C | d (d-sim) | d-sim: the attack masks belong to plan 0037 | T2 | - | 1 |
| 13 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | MonStatsInit header: the lines tagged inferred | §2 | a-run | follows the doomknight rows | T1 | H4b | 1 |
| 14 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | Classes 311, 312: `Range(4)` draw | §2 | a-run | H4b River of Flame / Chaos Sanctuary sessions (`doomknight2`, `doomknight3`) | T1 | H4b | 2 |
| 15 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | DamageRegen fatal errors | §2, 0x00573FF6 | d (d-edit) | d-edit | T3 | - | 1 |
| 16 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | hpregen overflow branch | §2 | a-logs | find creations in the kept logs where `(hp << 8) × r` passes 2³¹; none → d-none | T3 | S3a | 1 |
| 17 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | Skill loop over 8 slots | §2, UnitSkillAdd 0x0056DEB0 | b | skill list at SIX | T1 | H4b | 1 |
| 18 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | MonEquipInit call | §6 | a-run | H4a Blood Raven | T3 | H4a | 1 |
| 19 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | Reversed HP range: no step | §2 | c | data behaviour: list MonStats rows with max < min; none → d-none | T3 | S3b | 1 |
| 20 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | MonsterSkillBonus by game byte; no draw | §2 | b | skill list at SIX | T1 | H4b | 1 |
| 21 | [B. MonStatsInit in order](../../specs/monsters/stats.md#b-monstatsinit-in-order) | MonEquipInit row walk and one unit-seed step | §6, MonEquipFirstRow 0x005D30A0 | a-run | H4a Blood Raven / `flyingscimitar` | T3 | H4a | 1 |
| 22 | [C. The player count](../../specs/monsters/stats.md#c-the-player-count-sub_00573930_monplayerbonus) | difficulty ≥ 3 written to 2 | §3 | d (d-none) | d-none | T3 | - | 1 |
| 23 | [C. The player count](../../specs/monsters/stats.md#c-the-player-count-sub_00573930_monplayerbonus) | Align 1 and 2 get no bonus | §3, 0x0057396C | a-run | H4b: `/players 8` typed before entering Lut Gholein (camels, Align 2) with `MercNova` (Align 1 mercenary) | T1 | H4b | 1 |
| 24 | [C. The player count](../../specs/monsters/stats.md#c-the-player-count-sub_00573930_monplayerbonus) | Four attack callers; crushing blow reads stat 100 | §3 | d (d-sim) | d-sim: plan 0037 | T2 | - | 1 |
| 25 | [D. Classic nightmare and hell](../../specs/monsters/stats.md#d-classic-nightmare-and-hell-sub_0063eef0_monclassicdiffadjust) | `d` is the game byte; hirelings skipped | §5, 0x0057405D | a-logs | the 9 classic act-variant mercenary loads of run:2026-10-16-hirelings: stats reproduced by MERC_SetLevel with no adjustment | T2 | S3a | 1 |
| 26 | [E. The stat callback](../../specs/monsters/stats.md#e-the-stat-callback-sub_0055b800_monstatcallback-stat-7) | Precision 53 bits | §11, CRT_setdefaultprecision 0x0068E70A | a-logs | `tools/monstats.py fpsens` on the six `berserkf` logs; no 53/64 split → d-none | T3 | S3a | 1 |
| 27 | [E. The stat callback](../../specs/monsters/stats.md#e-the-stat-callback-sub_0055b800_monstatcallback-stat-7) | Final conversion truncates | §11, CRT_ftol2 0x00682FD0 | a-logs | `fpsens` variant with a rounding conversion: count calls that would differ | T1 | S3a | 1 |
| 28 | [E. The stat callback](../../specs/monsters/stats.md#e-the-stat-callback-sub_0055b800_monstatcallback-stat-7) | Other callback cases not read | §11 | d (d-sim) | d-sim: combat stat changes | T3 | - | 1 |
| 29 | [F. MonProp at creation](../../specs/monsters/stats.md#f-monprop-at-creation) | MonProp header; `chance` draw (two lines) | §7 | d (d-none) | d-none: stock `chance` is 0 in every slot | T3 | - | 2 |
| 30 | [F. MonProp at creation](../../specs/monsters/stats.md#f-monprop-at-creation) | No normal MonProp row reachable; one reader | §7, MonPropRec 0x00573470 | c | data behaviour over every MonProp row and normal pool; xref of g_pMonProp | T3 | S3b | 1 |
| 31 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | Notation: CDB and the champion part | §8, UModChampion 0x005A0E80 | a-logs | the champion handler writes of run:2026-10-15-mon-stats; addendum | T1 | S3a | 1 |
| 32 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | Flag 0 of ghostly, fanatic, possessed, berserk | §8 | d (d-none) | d-none: packs get no flag-0 call and no superunique carries 36–39 | T3 | - | 4 |
| 33 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | `poisonhit` row | §8 | d (d-owner) | d-owner: Baal Subject 2 only | T3 | - | 1 |
| 34 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | `always_run_ai` row | §8 | d (d-none) | d-none | T3 | - | 1 |
| 35 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | MonHpAddPct branches for pct > 0x10000 (two lines) | §8, MonHpAddPct 0x005A0D20 | d (d-none) | d-none | T3 | - | 2 |
| 36 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | hpmultiply: nothing at difficulty ≥ 3; champion via MonTypeFlag | §8, MonTypeFlag 0x005A0180 | a-logs | the 198 + 266 hpmultiply calls (champion test) of the kept logs; the ≥ 3 half is d-none | T1 | S3a | 1 |
| 37 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | Mod 36 −33 branch unreachable | §8, 0x005A0FE7 | d (d-none) | d-none | T3 | - | 1 |
| 38 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | fanatic/fast bonus 100 for Velocity ≤ 9 | §8 | a-logs | `fast` calls on classes with Velocity ≤ 9 in the kept logs; none → (a-run) H4b | T1 | S3a | 1 |
| 39 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | `poisonhit` not met (note) | §8 | d (d-owner) | d-owner | T3 | - | 1 |
| 40 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | `willowisp1` halving of stat 25 | §8, 0x005A0FB7 | a-run | H4b seeded hunt with a 118–121 class in the pool (Gloams, Burning Souls, Black Souls) | T3 | H4b | 1 |
| 41 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | Halving is signed ÷ 2, not >> 1 | §8 | d (d-none) | d-none: q ≥ 0 in stock data | T3 | - | 1 |
| 42 | [G. The mod handlers' stat effects](../../specs/monsters/stats.md#g-the-mod-handlers-stat-effects) | UniqueDamageBonus and HireableBossDamagePercent never read | §8, DifficultyRec 0x00611D30 | b | watchpoint on DifficultyLevels +0x30/+0x38 during an H4b session (values equal in stock data) | T3 | H4b | 1 |
| 43 | [H. To-hit and damage at attack time](../../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) | MonAttackStats and the expansion damage bonus (two lines) | §9 | d (d-sim) | d-sim: plan 0037 | T2 | - | 2 |
| 44 | [Outputs](../../specs/monsters/stats.md#outputs) | Skills set at creation | §2 | b | skill list at SIX | T1 | H4b | 1 |
| 45 | [Reimplementation notes](../../specs/monsters/stats.md#reimplementation-notes) | Reversed HP range: no step | §2 | c | as § B | T3 | S3b | 1 |
| 46 | [Reimplementation notes](../../specs/monsters/stats.md#reimplementation-notes) | Unread UniqueDamageBonus | §8 | b | as § G | T3 | H4b | 1 |
| 47 | [Reimplementation notes](../../specs/monsters/stats.md#reimplementation-notes) | MonPlayerBonus writes the difficulty byte | §3 | d (d-none) | d-none | T3 | - | 1 |

**Totals by class:** a-logs 10, a-run 8, b 6, c 3, d-edit 1, d-none 17, d-owner 2, d-sim 7 (sum 54).
