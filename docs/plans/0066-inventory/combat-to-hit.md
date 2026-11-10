# Plan 0066 inventory: combat/to-hit

- **Spec:** [combat/to-hit](../../specs/combat/to-hit.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 33; the *Count* column sums to 33.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 47 | Entry points | A player's normal attack or a skill's melee hit, … | `0x0057EC16` | a-logs | the `EV0` return addresses of every melee event in the c37p2, c37r and p47h logs: the set of callers, a counter in `tools/combat.py` | S5a | 1 |
| 2 | 50 | Entry points | A missile reaching a unit (phase (3); the to-hit … | `fn:MISSILE_HitUnit@0x005ADF10` | c | an xref scan with a second tool (r2 `axt`) of `COMBAT_ToHitRoll` and `COMBAT_DefenceRoll` callers from the two missile functions | S5b | 1 |
| 3 | 70 | Runtime state | arPct — 0 for a monster's melee test, the missile's stat … | `0x005AE05F` | b | a new `combat.py` logger line at the `MISSILE_HitUnit` to-hit call (`arPct`, missile stat 19) on monster line-missile hits; a checker case | H5b | 1 |
| 4 | 77 | Runtime state | (combat/0001 § 12b (e), ) | tbl:ItemStatCost.txt:Stat | c | an xref scan with a second tool of the stat-id immediates in the to-hit, defence and avoid functions | S5b | 1 |
| 5 | 86 | Constants | attacker-monster range bonus — 2 | `fn:COMBAT_MeleeHitTest@0x0057EC10` | b | a logger line at `sub_00622C40_InMeleeRange` entry (reach, both positions) in a monster-attack session; a checker case | H5b | 1 |
| 6 | 110 | A. The chance to hit (COMBAT_ToHitRoll) | TargetMods(att, def, AR, DEF) ; § A7, | `fn:COMBAT_ToHitTargetMods@0x0057D8A0` | c-emu | `COMBAT_ToHitTargetMods` emulated (stats 115, 116, 123, 124; type flags and `IsDemon`/`IsUndead` as observed boundaries) against the model | S5e | 1 |
| 7 | 141 | A. The chance to hit (COMBAT_ToHitRoll) | ; the formula from pct on is . | – | b | a logger line at `SKILLS_GetMasteryBonus`'s return in a `CombatBar` session, plus a stat-179 item; pct composed in the checker | H5b | 1 |
| 8 | 151 | A. The chance to hit (COMBAT_ToHitRoll) | flag. | `fn:sub_0056ECB0_SkillMissileCreate@0x0056ECB0` | b | as row 3: the monster line missile's `THV` AR against stat 19 at creation and at the hit | H5b | 1 |
| 9 | 157 | A. The chance to hit (COMBAT_ToHitRoll) | … player attacker (unit = 0), so stat 117 on a mercenary's items applies no state. | – | c-emu | `sub_0057D810_PreventHealHook` emulated with a hireling attacker carrying stat 117; `STATE_ApplyTimed` an observed boundary | S5e | 1 |
| 10 | 161 | A. The chance to hit (COMBAT_ToHitRoll) | for 120 000 frames with stat 31 = 0. | `fn:sub_0057D810_PreventHealHook@0x0057D810` | a-logs | the state-52 `STA` lines of p47h (`abs-n-plains`, 271): length 120 000 and stat 31 = 0, a check case | S5a | 1 |
| 11 | 170 | A. The chance to hit (COMBAT_ToHitRoll) | A7. TargetMods(att, def, AR, DEF): | `fn:COMBAT_ToHitTargetMods@0x0057D8A0` | c-emu | as row 6 | S5e | 1 |
| 12 | 181 | A. The chance to hit (COMBAT_ToHitRoll) | attack-rating bonuses against demons and undead. No run reached these stats. | `0x0057D8BA` | c-emu | as row 6 | S5e | 1 |
| 13 | 186 | A. The chance to hit (COMBAT_ToHitRoll) | … the client's character screen uses plain ÷ 100 instead of MulDiv. A reimplementation uses A2–A3. | – | c | an exhaustive xref scan with a second tool of `sub_00583740_AttackRatingCalc` and the client function: no attack-path caller | S5b | 1 |
| 14 | 192 | B. Defence (UNIT_GetDefense) | B1. Defense(u) → i32: | `fn:UNIT_GetDefense@0x006223F0` | c-emu | `UNIT_GetDefense` emulated with stats 16, 171, 182 and state 101 (the Holy Shield calc an observed boundary) against the model | S5e | 1 |
| 15 | 202 | B. Defence (UNIT_GetDefense) | zero for every logged unit and stay | `fn:UNIT_GetDefense@0x006223F0` | c-emu | as row 14 | S5e | 1 |
| 16 | 220 | C. The hit test and the defence rolls | C1. MeleeHitTest(att, def, arPct: i32, rangeExtra: i32) → result: u16: | `fn:COMBAT_MeleeHitTest@0x0057EC10` | a-logs | the packet result word at `AD0` against the `DRR` labels and `THR` outcome in c37p2, c37r and p47h, a checker case | S5a | 1 |
| 17 | 244 | C. The hit test and the defence rolls |  | `fn:COMBAT_MeleeHitTest@0x0057EC10` | a-logs | as row 16, with the `KB0`, crit and kill outcomes for bits 0x2, 0x8, 0x2000 | S5a | 1 |
| 18 | 246 | C. The hit test and the defence rolls | . | – | a-logs | p47h evade rolls: the result word after an evade, melee (no bit) and missile (`0x200`), a checker case | S5a | 1 |
| 19 | 248 | C. The hit test and the defence rolls | C1. The range test is sub_00622C40_InMeleeRange with the reach above; state 54 is uninterruptable. | – | c | the call target at the range test read with a second tool, and States.txt row 54 named `uninterruptable` | S5b | 1 |
| 20 | 257 | C. The hit test and the defence rolls | … ≠ 2: b ← b ÷ 3 ; moving, not walking; mode 3 (, 48), | `0x0057E00B` | c-emu | `COMBAT_DefenceRoll` emulated with a player defender in mode 2 and `UnitIsMoving` true: the chance undivided | S5e | 1 |
| 21 | 265 | C. The hit test and the defence rolls | if neither hand holds a usable shield: return 0 ; the shield test: | `fn:sub_0063C8F0_InvItemQuery@0x0063C8F0` | c | the writers of item flags `0x100` and `0x4000` read against `0x0062A4E0`'s test (a writer/reader pair) | S5b | 1 |
| 22 | 283 | C. The hit test and the defence rolls | … session the plan allowed was spent, so the count is final and the exception stays | – | c-emu | as row 20 | S5e | 1 |
| 23 | 289 | C. The hit test and the defence rolls | Kerke's Sanctuary beside a two-handed weapon. Which flag each layout sets is not read. | – | d-none | a scope note: which flag each layout sets is not read | – | 1 |
| 24 | 304 | C. The hit test and the defence rolls | see Open questions. | `0x0057DFD5` | c-emu | `0x00621190` emulated over every player and monster mode against the reading | S5e | 1 |
| 25 | 312 | C. The hit test and the defence rolls | … def.mode ∈ {2, 3}) or (def is a monster and def.mode ∈ {2, 15}) ; | `0x0057DD60` | c-emu | `COMBAT_AvoidRoll` emulated with a monster defender in modes 2, 15 and others, evade stat set | S5e | 1 |
| 26 | 320 | C. The hit test and the defence rolls | if wb > 0 and CurrentSkillCheck(def) = 13: ; | `0x0057DDAB` | d-none | a scope note: the meaning of the value 13 is not read | – | 1 |
| 27 | 337 | C. The hit test and the defence rolls | … monster defender with these stats was not logged, so its moving modes (2, 15) are | `0x0057DD60` | c-emu | as row 25 | S5e | 1 |
| 28 | 340 | C. The hit test and the defence rolls | with two claws in the hands; what the value stands for is not read. | `0x0057DDAB` | d-none | as row 26 | – | 1 |
| 29 | 346 | C. The hit test and the defence rolls | blocked. The missile path itself belongs to phase (3). | `fn:MISSILE_HitUnit@0x005ADF10` | a-logs | the c37p2 and p47h `md` events: a block roll only when the packet's phys is above 0, a counter in `tools/combat.py` | S5a | 1 |
| 30 | 352 | Outputs | blocked, dodged, avoided, evaded, weapon block, or 0. | `struct:DamagePacket+0x04` | a-logs | as row 16 | S5a | 1 |
| 31 | 354 | Outputs | and dodge or avoid). | `fn:COMBAT_DefenceRoll@0x0057DFB0` | a-logs | per-event counts of `THR` and `DRR` draws per seed in every kept combat log: at most 1 and 3 | S5a | 1 |
| 32 | 393 | Reimplementation notes | differs. | `fn:COMBAT_ToHitRoll@0x0057D9B0` | a-logs | the c37p2 to-hit and block checks by difficulty (N, NM, H) under the model with no difficulty term, a per-difficulty count | S5a | 1 |
| 33 | 395 | Reimplementation notes | the block. | `fn:COMBAT_MeleeHitTest@0x0057EC10` | a-logs | c37p2: misses with no `DRR` line, mode-3 events with a `DRB` and no `THR`, a counter | S5a | 1 |

**Totals by class:** a-logs 10, b 4, c 5, c-emu 11, d-none 3 (sum 33).
