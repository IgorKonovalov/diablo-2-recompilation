---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../specs/combat/delivery.md
  - ../plans/0046-skills-function-catalogue.md#implementation-log
resolution: ""
---

Not blocking. Review lane/s46c: combat/delivery A2/A3 from plan 0046 batch `ass` (skills/0014 §§ 1, 4, 5,
run:2026-10-21-cat-emu-ass), the released spec-writer entry
([archive](archive/2026-10-21-reverser-spec-writer-combat-delivery-a3-finisher-callers-and-progressiv.md)), with the
`lane/p46m11` review's wording.

- Entry points: a new row for the finishing moves' calls of `COMBAT_PrgFinisher`, [C] for the six call sites
  (`static.txt`) and for do 42, 46, 50's calls as boundaries (ADR-0021).
- A2, new bullets: the six direct callers (`SKILL_AttackDo` and do 42 `0x005D5A8C`, do 46 `0x005D6399`/`0x005D63E1`,
  do 50 `0x005D71F2`, do 52 `0x005D79DF`; start 25 calls it nowhere) [C]; what do 42, 46, 50 pass (do 42 no null test,
  do 46 finisher only with a hit and `DeliverQueued` with none, do 50 only with a hit) [C] up to those calls; do 52's
  no-null-test call and the finisher's null return [I]; after the finisher each move delivers (do 46: one
  `DeliverQueued` on either path; do 42's last-kick `RNG_Range(caster, 100)`; do 50's fire area hit) [I].
- A3 pseudocode: `PrgFinisher(att, hit)` with the null test [I]; entries 37/143, 39, 41, 36 and 40 rewritten from
  skills/0014 § 5 in the anchored order (record, missile, target point, count), each [C] up to its first creation
  (40 whole), the steps after it marked [I] inline; 38 [C] up to `DeliverQueued` or `SkillRollPhys`, its rolls and area
  hit [I]. Was one [I] header per entry.
- A3 bullets: the at-entry step of 37, 39, 41, 143 before the record test and the local-seed draws up to the first
  creation [C] (split from 38's rolls, which stay [I]); 38's own delivery [C] up to `DeliverQueued`, the later empty
  `DeliverQueued` [I]; the ring count untested [C] up to the first creation, `⌈64/n⌉` and n = 0 endless [I]; a negative
  count is not endless, ends by the signed index wrapping past −2³¹ after about 2³¹/|4n| passes [I], not run; the rings'
  `SkillGetParam2(280) + 1` write [I]; `ItemEffect` 36 (Nova, Frost Nova) runs entry 36 [I].
- Reimplementation notes: the peek bullet split (peek [I]; entries' at-entry step [C]; 38's draws [I]); new bullets on
  the finishing-move callers ([C]/[I]) and the untested ring count [I].
- Evidence: skills/0014 §§ 1, 4, 5 and the run; skills/0001 § 12 and skills/0003 § 1 dated notes cited.
- Open questions: the run bullet rewritten whole (the finisher itself and the entries past their first creation not
  run); new [L]: whether stock data gives a ring 0 or a negative count.

Tags: combat/delivery {C59 I49 L3} -> {C74 I58 L4} (the gate's own counter; by hand +15 C, +9 I net of 4 removed [I]
headers, +1 L). Research map (yours): the combat row's summed figure "C 215 / I 176 / L 23" becomes C 230 / I 185 /
L 24, and the row could name plan 0046 `ass` (finisher callers and entries 36–41, 143 [C] up to their boundaries).

Not changed: combat/README B5 and its draws note still say the normal attack's finisher, which stays true (the
finishing moves are skill do functions, outside its attack event); I left it and can add a pointer if you want one.
Wiki: docs/wiki/combat.md states nothing about the finisher or progressive entries, so no page and no `based_on` changed.
No other open spec-writer entry is combat/delivery-only (the rest are items and objects), so none was folded in.
