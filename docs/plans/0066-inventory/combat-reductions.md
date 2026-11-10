# Plan 0066 inventory: combat/reductions

- **Spec:** [combat/reductions](../../specs/combat/reductions.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 25; the *Count* column sums to 25.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 59 | Runtime state | (, combat/0001 § 12b (e)) | tbl:ItemStatCost.txt:Stat | ? | ? | ? | 1 |
| 2 | 66 | Constants | resistance floor — −100 (below −99) | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 3 | 69 | Constants | PvP percent; hireling against hireling — for 17 between two players, physical and lightning ; … | `0x0057C0B6` | ? | ? | ? | 1 |
| 4 | 70 | Constants | prime evil against a bit-31 unit — for 200 , for 400 | `0x0057C129` | ? | ? | ? | 1 |
| 5 | 88 | A. COMBAT_ApplyReductions | DispatchEvent(11 absorbdamage, unit: def, other: att, pkt) ; | `fn:UNIT_DispatchEvent@0x005C0C30` | ? | ? | ? | 1 |
| 6 | 100 | A. COMBAT_ApplyReductions | A1. frameRate is packet +, which the missile path sets from the missile's stat 327. | – | ? | ? | ? | 1 |
| 7 | 103 | A. COMBAT_ApplyReductions | logged unit had one. | `fn:UNIT_DispatchEvent@0x005C0C30` | ? | ? | ? | 1 |
| 8 | 128 | A. COMBAT_ApplyReductions | A2. DamagePercent(ctx) → i32: | `fn:COMBAT_DamagePercent@0x0057C060` | ? | ? | ? | 1 |
| 9 | 145 | A. COMBAT_ApplyReductions | hireling were not reached. | `0x0057C129` | ? | ? | ? | 1 |
| 10 | 146 | A. COMBAT_ApplyReductions | meaning is not named by the finding. | `0x0057C0B6` | ? | ? | ? | 1 |
| 11 | 153 | A. COMBAT_ApplyReductions | A2. "Boss" is MonStats boss (+ bit 6), not a unique or superunique. | `fn:MONSTATS_IsBoss@0x0063E9F0` | ? | ? | ? | 1 |
| 12 | 158 | A. COMBAT_ApplyReductions | A3. LengthImmunities(ctx): | `fn:COMBAT_LengthImmunities@0x0057C140` | ? | ? | ? | 1 |
| 13 | 168 | A. COMBAT_ApplyReductions | met. | `fn:COMBAT_LengthImmunities@0x0057C140` | ? | ? | ? | 1 |
| 14 | 221 | B. The rows (g_DamageResistTable) | if row.pierceStat ≥ 0 and (r < 100 or not ctx.defIsMon): ; | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 15 | 229 | B. The rows (g_DamageResistTable) | if r < −99: r ← −100 ; | `fn:COMBAT_ResistFor@0x0057BE00:` | ? | ? | ? | 1 |
| 16 | 233 | B. The rows (g_DamageResistTable) | … row is 0 and HasState(att, 47) and def is undead: r ← 0 ; sanctuary, | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 17 | 250 | B. The rows (g_DamageResistTable) | … The cap is the same code path as the other rows, read from the code. | – | ? | ? | ? | 1 |
| 18 | 253 | B. The rows (g_DamageResistTable) | Sanctuary (state 47) zeroes physical resistance against undead; not met. | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 19 | 264 | B. The rows (g_DamageResistTable) | if f > 0: ; for fire and lightning , | run:2026-10-20-shortfalls | ? | ? | ? | 1 |
| 20 | 272 | B. The rows (g_DamageResistTable) | … is read from the code: the flat-absorb hits below assert the field, not the heal. | `fn:COMBAT_Absorb@0x0057BF10` | ? | ? | ? | 1 |
| 21 | 278 | B. The rows (g_DamageResistTable) | … all misses), so its row rests on the code's one path, final for plan 0047. | – | ? | ? | ? | 1 |
| 22 | 325 | Reimplementation notes | for the penalty before the cap ; | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 23 | 330 | Reimplementation notes | the immunity ; | `fn:COMBAT_ResistFor@0x0057BE00` | ? | ? | ? | 1 |
| 24 | 334 | Reimplementation notes | reached, so the steal percents are not scaled by P. | `fn:COMBAT_ApplyReductions@0x0057C1E0` | ? | ? | ? | 1 |
| 25 | 335 | Reimplementation notes | No minimum damage. Nothing in this path keeps a hit above 0. | `fn:COMBAT_ApplyReductions@0x0057C1E0` | ? | ? | ? | 1 |
