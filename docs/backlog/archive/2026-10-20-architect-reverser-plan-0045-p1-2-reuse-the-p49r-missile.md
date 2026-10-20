---
from: architect
to: reverser
date: 2026-10-20
status: done
context:
  - ../../plans/0045-skills-missiles-machinery.md
  - ../../findings/quests/0001-progression.md
  - ../../findings/items/0002-quality-roll.md
resolution: "Done (lane/p45m review, 2026-10-20): skills/0002 reuses sub_0056EDE0_MissileCreateAt and g_MissileSrvDoFuncs byte for byte (one row each in re/symbols.csv after the merge, no duplicate address or name), names 0x005ADBB0 sub_005ADBB0_MissileDoFrame, and follows the Srv pattern for the hit, damage and count tables; STATEVENT_Reanimate untouched."
---

Not blocking; for plan 0045 P1.2 (`lane/p45m`, missiles), from the `lane/p49r` review (plan 0049 Phase 1, 2026-10-20). `lane/p49r` named three addresses on or near the missile path. Reuse these names (reverser review-fixes rule 5), do not rename them, and grep `re/symbols.csv` after merging `main`:
- `0x0056EDE0` `sub_0056EDE0_MissileCreateAt` (ECX game, EDX source unit; stack args `(a, b, missile, x, y)`; fills a request and calls `sub_0059FA30_MissileCreate`; `[I]`, [quests/0001 § 7](../../findings/quests/0001-progression.md)).
- `0x0073C768` `g_MissileSrvDoFuncs` (53 slots, entry 0 null, indexed by `pSrvDoFunc` at record `+0x0C`; the dispatch `movsx eax, word [ebx+0xc]` / `mov eax, [eax*4+0x73c768]` / `call eax` at 0x005ADC97–0x005ADCA7, in the unnamed `0x005ADBB0`, which P1.2 may name; entry 13 is `sub_005AEDA0_MissileSpawnOwnedMonster`, row 207 `bonewallmaker`; [items/0002 § Plan 0049 Phase 1 (e)](../../findings/items/0002-quality-roll.md#plan-0049-phase-1-2026-10-20-static)).
- `0x005C09E0` `STATEVENT_Reanimate` (not a missile function: entry 31 of `g_StatEventFuncs`, listed so the batch does not re-read it).
None clashes with `main`: `lane/p45r`'s `sub_0056ECB0_SkillMissileCreate`, `sub_0056EE90_SkillMissileCreateLob` and `SKILLS_SrvDo` are other addresses. The loader's descriptor stores read by p49r (0x00661D97–0x00661E27: `pCltDoFunc` +0x08, `pCltHitFunc` +0x0A, `pSrvDoFunc` +0x0C, `pSrvHitFunc` +0x0E, `pSrvDmgFunc` +0x10) agree with [Missiles](../../tables/Missiles.md).
