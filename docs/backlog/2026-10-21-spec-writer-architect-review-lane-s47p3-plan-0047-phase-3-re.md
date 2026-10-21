---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../plans/0047-simulation-shortfalls.md#implementation-log
resolution: ""
---

Review lane/s47p3: plan 0047 Phase 3 (re-tag) of combat, stats/states, stats/README and quests/travel from run:2026-10-20-shortfalls, as accepted at the 2026-10-21 Phase 2 review (rulings 1, 2, 7, 8).

Raised to [C] with run:2026-10-20-shortfalls cited (each split from its remainder):
- combat/to-hit: C3 evade, weapon block, dodge, avoid on a player defender (46/50/172/103 rolls), a moving player rolls only evade; A6 prevent-heal's no draw (271 state-52 lines); `--no-shield-log` stated as a model input (88 mismatches without it: 70 claw Assassins, 18 CombatDR that check nothing about the refusal). Stay [I]: the mode-2 block exception (6, final), the weapon-block skill check 13/12, the unusable shield (`sub_0063C8F0_InvItemQuery`, "usable" in BlockChance), a monster defender's moving modes.
- combat/reductions: B1 magic immunity 36; B2 lightning cap 42, cold cap 31 over two runs (ruling 2); B3 fire flat absorb 113, negative absorbed amount 186. Stay [I]: cold and lightning flat absorb (Phase 2b), the magic cap (unstageable, ruling 2 of Phase 1, final).
- combat/delivery: B4 total <= 0 leaves life unchanged (488 + 113 + 32); E1 crushing blow on champions k = 4 (52), champions carry 0x08; E3 freeze on a melee hit (81). Stay [I]: open wounds on 0x04 alone, D3 inside the nested delivery, the freeze missile terms.
- combat/README: the run under the same boundary (18 737 / 31 logs, 0 mismatches), the champion 1/8 note. New [I]: a monster's own MonAttackStats inside its attack (also combat/damage § E, ruling 4).
- stats/states: B1 the attract refusal on a monster target (71/71, 151/151); D1 groups 1-2 (43); F4 the aura end by the skill switch (59 of 61; 120 on/off events); the H apply row adds 239 monster requests. Stay [I] and named Phase 2b: the curse cut, group 3 (12 unchecked, not withdrawn, review fix 4), the 256 floor, expiries 153/300, shrines and wells 15/50.
- stats/README: the run's [C] paragraph; shortfall bullet rewritten.
- quests/travel: one dated [I] C1 note (1 of 20 mode-0 activations; Phase 2b).

Tags (before -> after): combat/README {C36 I42 L5} -> {C38 I42 L5}; to-hit {C33 I27 L3} -> {C39 I30 L5}; damage {C34 I29 L4} -> {C34 I30 L5}; reductions {C40 I25 L4} -> {C45 I24 L5}; delivery {C52 I54 L4} -> {C59 I49 L3}; stats/states {C44 I51 L6} -> {C47 I52 L6}; stats/README {C14 I3 L3} -> {C15 I3 L3}; quests/travel {C74 I84 L4} -> {C74 I86 L4} (recounted with the gate's own counter).

Wiki: combat.md, stats-and-states.md, quests.md (based_on 2026-10-21), how-we-know.md (process: the second run, final against carried shortfalls, a count met over two runs).

Please also update the research map rows (docs/specs/README.md) for combat and stats/states (the shortfall counts and Phase 2b), which this lane does not edit. No spec-writer backlog entry was open for this plan.
