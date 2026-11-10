# Plan 0066 inventory: combat/damage

- **Spec:** [combat/damage](../../specs/combat/damage.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 35; the *Count* column sums to 35.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 44 | Entry points | A monster's to-hit and damage stats, at its attack … — for its draws, for its stats | run:2026-10-16-combat | a-logs | the `MAS1` stats of the 5 060 c37p2 calls (and p47h) against a new monsters/stats § H output model from MonStats and MonLvl | S5a | 1 |
| 2 | 71 | Runtime state | (combat/0001 § 12b (e), ) | tbl:ItemStatCost.txt:Stat | c | an xref scan with a second tool of the stat-id immediates in the builder and its rolls | S5b | 1 |
| 3 | 78 | Constants | unarmed min/max — 1 / 2 | `fn:COMBAT_RollPhysical@0x0057B420` | a-logs | a counter of kept monster builds whose stats 21 or 22 fall below 1 or 2 (no weapon, the clamp biting); none means an unarmed-player case | S5a | 1 |
| 4 | 79 | Constants | burn constant — 316 | `0x0057BC2F` | c-emu | step 7 (`0x0057BC2F`–`0x0057BC8A`) emulated as a bounded piece with burn above 0 and `srcdam` not 128, against the model | S5e | 1 |
| 5 | 80 | Constants | conversion minimum length — 50 frames | `0x0057BCB2` | c-emu | the conversion piece (`0x0057BCB2`–`0x0057BD71`) emulated over every `convType`, lengths below 50 | S5e | 1 |
| 6 | 87 | A. COMBAT_BuildDamage in order | BuildDamage(att, def, pkt, critFlag: i32, srcdam: i32): | `fn:COMBAT_BuildDamage@0x0057B7D0` | a-logs | the whole-packet compare at `BD1` over every kept build (c37p2, c37r, p47h, p47b); steps 1, 8, 9 are rows 7, 10, 11 | S5a | 1 |
| 7 | 89 | A. COMBAT_BuildDamage in order | 1. link the weapon's stat lists to att; pkt.flags /= | `0x0057B82A` | c-emu | `sub_0057B660_UndeadDmgBonus` and `sub_0057B6A0_DmgVsMonType` emulated (blunt and other weapons, stat-180 lists) plus the stat-120 write | S5e | 1 |
| 8 | 107 | A. COMBAT_BuildDamage in order | … × srcdam ÷ 128 ; drain rolls, draws as § C; the base: note 5, | – | c-emu | the step-5 drain piece emulated with a drain field already in the packet, `COMBAT_RollElemStat` run inside | S5e | 1 |
| 9 | 120 | A. COMBAT_BuildDamage in order | if pkt.stunLen = 0: pkt.stunLen += stat(att, 66) × srcdam ÷ 128 ; | `0x0057BB60` | a-logs | a counter of kept builds with stat 66 or a stun `El` group and `stunLen` at `BD1`, which the checker already compares | S5a | 1 |
| 10 | 124 | A. COMBAT_BuildDamage in order | 8. if att is a player or a hireling and not (pkt.result & ): | `0x0057BC8D` | a-logs | the event-3 `EVH` lines in player and hireling builds and none in monster builds, over every kept combat log, a counter | S5a | 1 |
| 11 | 126 | A. COMBAT_BuildDamage in order | 9. if pkt.convType ≠ 0: Convert(pkt) ; § D, | `0x0057BCB2` | c-emu | as row 5 | S5e | 1 |
| 12 | 136 | A. COMBAT_BuildDamage in order | oracle, so step 1's composition is | `fn:sub_0057B660_UndeadDmgBonus@0x0057B660` | c-emu | as row 7 | S5e | 2 |
| 13 | 145 | A. COMBAT_BuildDamage in order | unit had stat 337, so the chain order is | `fn:RNG_RangeOffset@0x00472280` | a-logs | `bar-n-plains` builds with `BDC` mastery crit and stat 141 both above 0: the draw order already modelled, a counter; stat 337 if any p47h Amazon build had it | S5a | 1 |
| 14 | 146 | A. COMBAT_BuildDamage in order | ); | `0x0057B8A9` | a-logs | as row 13 | S5a | 1 |
| 15 | 147 | A. COMBAT_BuildDamage in order | 3. The doubling applies to physical damage only, and only when step 2 ran. | `0x0057B8A9` | a-logs | the deadly-strike doublings of c37p2: elements unchanged in the `BD1` packet, a counter | S5a | 1 |
| 16 | 150 | A. COMBAT_BuildDamage in order | physical damage at the hit (overview § B, B4). | – | b | a logger line at `sub_0064A850_MissileCritRoll` (owner seed, chances) in a physical-missile session (`CombatAma` arrows) | H5b | 1 |
| 17 | 161 | A. COMBAT_BuildDamage in order | writers of these fields are unfollowed. | `0x0057BA71` | c | an exhaustive scan with a second tool of the writers of packet `+0x38`, `+0x3C`, `+0x40` before the build | S5b | 1 |
| 18 | 168 | A. COMBAT_BuildDamage in order | for the general formula, the constant 316 itself | `0x0057BC2F` | c-emu | as row 4 | S5e | 1 |
| 19 | 172 | A. COMBAT_BuildDamage in order |  | `fn:UNIT_DispatchEvent@0x005C0C30` | c | the event-3 handler list read with a second tool (the stat-event table) | S5b | 1 |
| 20 | 175 | A. COMBAT_BuildDamage in order | … overlay 54 on the defender is put only when the hit-class flag was already taken. | run:2026-10-16-combat | c-emu | `sub_005A5560_MonCritDouble` emulated with the hit-class flag free and taken (`PacketHitClassSet` observed) | S5e | 1 |
| 21 | 178 | A. COMBAT_BuildDamage in order | melee build's. | `0x005AD884` | a-logs | c37p2 and p47h `md` events from monsters with MonStats `Crit` above 0: the doubling draw at `0x005AD884`, a counter | S5a | 1 |
| 22 | 186 | B. The physical roll (COMBAT_RollPhysical) | if att holds no weapon: mn ← max(mn, 1); mx ← max(mx, 2) ; | `fn:COMBAT_RollPhysical@0x0057B420` | a-logs | as row 3 | S5a | 1 |
| 23 | 226 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) | … v ← (v × srcdam) ÷ 128 ; signed, toward zero; on the no-draw path | – | c-emu | `COMBAT_RollElemStat` with its caller's scale emulated: a positive field, no stat, `srcdam` not 128 | S5e | 1 |
| 24 | 234 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) |  | `0x0057B932` | c-emu | as row 23 (elements by multiply and divide, physical by `MulDiv`, negative products) | S5e | 1 |
| 25 | 238 | C. One element (COMBAT_RollElemStat, COMBAT_RollRange) |  | `0x0057A8F7` | c-emu | as row 23 | S5e | 1 |
| 26 | 243 | D. Conversion | D1. Convert(pkt): | `0x0057BCB2` | c-emu | as row 5 | S5e | 1 |
| 27 | 259 | D. Conversion | (skills/0003 § 12). | `fn:sub_005D7EA0_SkillSt32Hit@0x005D7EA0` | c | an exhaustive scan with a second tool (r2) of byte stores to packet `+0x65` and dword stores to `+0x68` | S5b | 1 |
| 28 | 263 | D. Conversion | and no logged event converted, so § D is unexercised. | `struct:DamagePacket+0x65` | a-logs | `BD0` packet `+0x65` = 0 in every kept build, a counter | S5a | 1 |
| 29 | 273 | E. A monster's attack stats (MonAttackStats) | ) The stats it writes were value inputs of the run, so their formulas stay | run:2026-10-16-combat | a-logs | as row 1 | S5a | 1 |
| 30 | 278 | E. A monster's attack stats (MonAttackStats) | only when its El<e>Mode equals the mode passed. | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | a-logs | `MAS0` mode against the unit's new mode and the column set picked, in the row-1 model over the kept calls | S5a | 1 |
| 31 | 283 | E. A monster's attack stats (MonAttackStats) | the call is not read. | `fn:sub_005A4F50_MonAttackStats@0x005A4F50` | a-run | `combat_sessions.py` sessions in the Act II desert (`sandraider2` packs) counting inner `MAS` calls past the floor | H5a | 1 |
| 32 | 286 | E. A monster's attack stats (MonAttackStats) |  | `0x00653BC2` | c | a writer/reader pair: `MonLvlStats` output `+0x24`/`+0x28` against `MonAttackStats` reads at `+0x2C`/`+0x30`, with a second tool | S5b | 1 |
| 33 | 290 | E. A monster's attack stats (MonAttackStats) | 316/317 and 315; 12 frze sets nothing. | `0x005A5300` | a-logs | the 167 `El` applications' `MAS1` stats by element type against ElemTypes, in the row-1 model | S5a | 1 |
| 34 | 334 | Reimplementation notes | for the player's physical-only doubling | `0x0057B8A9` | a-logs | as row 15 | S5a | 1 |

**Totals by class:** a-logs 15, a-run 1, b 1, c 5, c-emu 13 (sum 35).
