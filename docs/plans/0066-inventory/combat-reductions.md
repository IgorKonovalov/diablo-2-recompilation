# Plan 0066 inventory: combat/reductions

- **Spec:** [combat/reductions](../../specs/combat/reductions.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 25; the *Count* column sums to 25.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 59 | Runtime state | (, combat/0001 § 12b (e)) | tbl:ItemStatCost.txt:Stat | c | an xref scan with a second tool (r2) of the stat-id immediates in the four reduction functions and the table rows at `0x00732980` | S5b | 1 |
| 2 | 66 | Constants | resistance floor — −100 (below −99) | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | `COMBAT_ResistFor` emulated with resistance inputs below −99 (stat getters as observed boundaries), against `tools/combat.py` | S5e | 1 |
| 3 | 69 | Constants | PvP percent; hireling against hireling — for 17 between two players, physical and lightning ; … | `0x0057C0B6` | c-emu | `COMBAT_DamagePercent` emulated: a hireling and a bit-31 attacker on a player, two hirelings; the 17 and 25 branches | S5e | 1 |
| 4 | 70 | Constants | prime evil against a bit-31 unit — for 200 , for 400 | `0x0057C129` | c-emu | `COMBAT_DamagePercent` emulated: prime-evil attacker, bit-31 non-hireling defender; the 400 branch | S5e | 1 |
| 5 | 88 | A. COMBAT_ApplyReductions | DispatchEvent(11 absorbdamage, unit: def, other: att, pkt) ; | `fn:UNIT_DispatchEvent@0x005C0C30` | d-none | a scope note: the event-11 handlers were not read; raising it is new reading (and an Energy Shield session) | – | 1 |
| 6 | 100 | A. COMBAT_ApplyReductions | A1. frameRate is packet +, which the missile path sets from the missile's stat 327. | – | a-logs | the `md` events of the c37p2 logs: packet `+0x54` against the missile's logged stat 327, a counter in `tools/combat.py` | S5a | 1 |
| 7 | 103 | A. COMBAT_ApplyReductions | logged unit had one. | `fn:UNIT_DispatchEvent@0x005C0C30` | d-none | a scope note (handlers not read, none logged) | – | 1 |
| 8 | 128 | A. COMBAT_ApplyReductions | A2. DamagePercent(ctx) → i32: | `fn:COMBAT_DamagePercent@0x0057C060` | c-emu | `COMBAT_DamagePercent` emulated over every branch (unit type, hireling type, flags, `IsBoss` as observed boundaries) against the model | S5e | 1 |
| 9 | 145 | A. COMBAT_ApplyReductions | hireling were not reached. | `0x0057C129` | c-emu | as row 4, plus the two-hireling 25 case | S5e | 1 |
| 10 | 146 | A. COMBAT_ApplyReductions | meaning is not named by the finding. | `0x0057C0B6` | d-none | a scope note: the bit's meaning is not named | – | 1 |
| 11 | 153 | A. COMBAT_ApplyReductions | A2. "Boss" is MonStats boss (+ bit 6), not a unique or superunique. | `fn:MONSTATS_IsBoss@0x0063E9F0` | a-logs | c37p2 and c37r mercenary attacks (`ha`) on uniques and superuniques logged P = 100 against Andariel's; plus a full MonStats `boss` column check | S5a | 1 |
| 12 | 158 | A. COMBAT_ApplyReductions | A3. LengthImmunities(ctx): | `fn:COMBAT_LengthImmunities@0x0057C140` | c-emu | `COMBAT_LengthImmunities` emulated: stats 153 and 118, states 131 and 133 as observed `HasState` returns | S5e | 1 |
| 13 | 168 | A. COMBAT_ApplyReductions | met. | `fn:COMBAT_LengthImmunities@0x0057C140` | c-emu | as row 12 (stat 118, states 131 and 133) | S5e | 1 |
| 14 | 221 | B. The rows (g_DamageResistTable) | if row.pierceStat ≥ 0 and (r < 100 or not ctx.defIsMon): ; | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | `COMBAT_ResistFor` emulated with pierce stats 333–336 on the attacker, monster and player defenders | S5e | 1 |
| 15 | 229 | B. The rows (g_DamageResistTable) | if r < −99: r ← −100 ; | `fn:COMBAT_ResistFor@0x0057BE00:` | c-emu | as row 2 | S5e | 1 |
| 16 | 233 | B. The rows (g_DamageResistTable) | … row is 0 and HasState(att, 47) and def is undead: r ← 0 ; sanctuary, | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | `COMBAT_ResistFor` emulated: state 47 on the attacker, an undead defender, row 0 | S5e | 1 |
| 17 | 250 | B. The rows (g_DamageResistTable) | … The cap is the same code path as the other rows, read from the code. | – | d-edit | no stock writer gives stat 37 near 75 (plan 0047 ruling 2); the S5e cases could include it at no cost | – | 1 |
| 18 | 253 | B. The rows (g_DamageResistTable) | Sanctuary (state 47) zeroes physical resistance against undead; not met. | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | as rows 14 and 16 | S5e | 1 |
| 19 | 264 | B. The rows (g_DamageResistTable) | if f > 0: ; for fire and lightning , | run:2026-10-20-shortfalls | c-emu | `COMBAT_Absorb` emulated on row 3 (cold) with stat 149 set, against the model | S5e | 1 |
| 20 | 272 | B. The rows (g_DamageResistTable) | … is read from the code: the flat-absorb hits below assert the field, not the heal. | `fn:COMBAT_Absorb@0x0057BF10` | a-logs | p47h and p47b flat-absorb hits (fire 113, lightning 51): the delivery's heal from packet `+0x48`, a new check case in `tools/combat.py` | S5a | 1 |
| 21 | 278 | B. The rows (g_DamageResistTable) | … all misses), so its row rests on the code's one path, final for plan 0047. | – | c-emu | as row 19 | S5e | 1 |
| 22 | 325 | Reimplementation notes | for the penalty before the cap ; | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | as row 2 | S5e | 1 |
| 23 | 330 | Reimplementation notes | the immunity ; | `fn:COMBAT_ResistFor@0x0057BE00` | c-emu | as row 14 | S5e | 1 |
| 24 | 334 | Reimplementation notes | reached, so the steal percents are not scaled by P. | `fn:COMBAT_ApplyReductions@0x0057C1E0` | a-logs | the mercenary's hits on Andariel (P 50, 35, 25) in run:2026-10-16-combat: the steal percents left unscaled, a counter | S5a | 1 |
| 25 | 335 | Reimplementation notes | No minimum damage. Nothing in this path keeps a hit above 0. | `fn:COMBAT_ApplyReductions@0x0057C1E0` | a-logs | p47h `CombatDR` events: fields and total at or below 0 kept unclamped through the reductions, a counter in `tools/combat.py` | S5a | 1 |

**Totals by class:** a-logs 5, c 1, c-emu 15, d-edit 1, d-none 3 (sum 25).
