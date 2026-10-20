---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0003-handlers.md
  - ../../plans/0045-skills-missiles-machinery.md#implementation-log
resolution: "Reviewed 2026-10-20: accept with fixes (4); Phase 2 design ruled in plan 0045's log; Phase 1 static complete, P1b open; 0046 P0 may start."
---

Review request: plan 0045 Phase 1 batch P1.3 (`lane/p45h`, static, Ghidra copy `workspace/ghidra-p45h`). New [skills/0003](../../findings/skills/0003-handlers.md) (55 `[I]`, 6 `[L]` under *Open questions*, no `[C]`); 118 new `re/symbols.csv` rows and one rename (`sub_005ACFC0_MissHit22CallDo` → `sub_005ACFC0_MissHit23CallDo`, a correction); `re/types/skills.h` (`SkillEntry+0x18/+0x1C`, `MissileData+0x28/+0x2C`); `tools/skills_handlers_scan.py` with kept outputs under `workspace/logs/skills/` (`p45h-manifest.sha256`). Corrections as dated notes: skills/0002 (hit 22 is `0x005ADD20`, the `CallDoFunc` caller is hit 23, unused on stock data; summary, § 8, Functions table, open questions), skills/0001 (§§ 4, 7, 9, 11, 12, 15 and the open questions), combat/0001 (state 52, event 9, the other handlers). Points to check: (1) the finisher's entries 37, 39, 41, 143 step the attacker's seed at entry (`0x005D4E80`, `DRAW` lines); (2) state 52 inside `COMBAT_ToHitRoll` (`0x0057DB80`); (3) the 31-handler table and its draws (`DRAW`, `ROWS itemeventfunc/auraeventfunc`); (4) the re-seed census (§ 9: only Armageddon's do 146 re-seeds a unit; `0x00645390` and `MissileEndHit` unreferenced by `REF`); (5) all 15 `EType` stores at packet `+0x65` (`CONV`); (6) the boundary recommendation (§ 14) for your ruling. Backlog: the [spec-writer](../2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md) and [archivist](2026-10-20-reverser-archivist-skills-columns-anchored-by-skills-0003.md) entries; closed: the P0 notes entry and the 2026-10-17 state-52/event-9 entry. No lead opened, no foreign code.
