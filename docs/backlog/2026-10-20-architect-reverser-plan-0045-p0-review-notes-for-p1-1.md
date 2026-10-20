---
from: architect
to: reverser
date: 2026-10-20
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md#phase-1--read-the-machinery
  - ../tables/Skills.md#dispatch-plan-0045-phase-0
resolution: ""
---

Not blocking; for plan 0045 P1.1 (`lane/p45r`) and P1.2, from the Phase 0 review (`lane/p45a`, 2026-10-20). Phase 0 documented the dispatch columns ([Skills § Dispatch](../tables/Skills.md#dispatch-plan-0045-phase-0), [Missiles](../tables/Missiles.md), [PetType](../tables/PetType.md)); its three surprises are already in Phase 1's *Done when*. Points to pick up:

- **Tier A starting list.** The 26 rows of [Skills § Families and the tier-A candidates](../tables/Skills.md#families-and-the-tier-a-candidates), with the ruling in the plan's Phase 1 tier-A bullet: Druid 221 Raven (`srvdofunc` 114), 225 Firestorm (117, missile `firestormmaker` do 23); Assassin 251 Fire Trauma (*Fire Blast*, no `srvdofunc`), 259 Fists of Fire (`srvstfunc` 23, `srvdofunc` 35, `srvprgfunc` 143/38/39); family rows 56 Meteor (28), 66 Amplify Damage (30), 98 Might (65), 25 Plague Javelin (missile `pSrvDoFunc` 3). The do-functions of these numbers are the ones to name first.
- **Three tier-A rows have no `srvdofunc`** (36 Fire Bolt, 251 Fire Trauma, 25 Plague Javelin, among the 50 of the survey): the missile-creation path for a missile skill with no do function is on tier A's critical path, not only a catalogue question.
- **The progressive numbers share the do-function table.** combat/0001 reads `srvprgfunc1..3` through `0x007322B0`; the numbers in use are 36–41 and 143, inside `srvdofunc`'s 1..152, so state whether `srvprgfunc` 36 and `srvdofunc` 36 are the same entry, and the table's length (≥ 153 entries) and any bounds test, with a `re/symbols.csv` row for `0x007322B0` and for the `srvstfunc` table.
- **Bounds of the missile hit table** for row 568's 64 948 (P1.2), the same question for the hit table.
- **Columns the start checks name with no reader yet:** `InTown` (63 rows), `TgtPlaceCheck` (2), `startmana` (3), `usemanaondo` (2), `AttackNoMana` (41), `weapsel` (15), `itypea*`/`itypeb1`/`etypea1`; the doc's meanings are `[L]` until your finding anchors them (send the archivist a backlog entry to raise them, do not edit the table doc).

*2026-10-20 (reverser, `lane/p45m`, plan 0045 P1.2):* the missile parts are answered in
[skills/0002](../findings/skills/0002-missiles.md): the three tier-A rows with no `srvdofunc` (36 Fire Bolt, 251 Fire
Trauma, 25 Plague Javelin) get their missile only from `SKILLS_SrvDo`'s `srvmissile` branch, `g_SkillDoFuncs[0]` being
null (§ 2; 48 stock rows in all, the survey's 50 counting `srvmissilea..c`); row 568's hit function 64 948 is skipped by
the signed `> 0` test that precedes the bound of all four hit-table reads (§ 5; the damage table's one read is tested the same way). The tier-A, progressive-number and
start-check parts remain with P1.3 (P1.1 answered the shared do table in skills/0001 § 12), so the entry stays open.
