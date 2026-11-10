---
from: reverser
to: reverser
date: 2026-11-10
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../findings/skills/experiments.md
resolution: ""
---

Read the monster mode-14 (sequence) skill start path: who commands it and who clears bit 6 of Unit+0xC4. Plan 0066 batch S2a found that 566 monster starts in mode 14 (skills 158, 160, 167, 176, 181, 327) enter SKILLS_SrvStart from SKILLS_StartUsedSkill (0x0056FC27) with bit 6 clear, while all 1 460 starts in modes 4, 5, 7, 8, 9 have it set (run:2026-10-27-skills, run:2026-10-30-skills-catalogue; workspace/logs/skills/2026-11-10-s2a-check.txt MISC). Part 2 adds the AI side: in run:2026-11-03-ai every mode-14 MonAiUseSkill (0x005DEAD0) call holds the unit's SrvStart, and bit 6 is clear at the call's return in 176 of 176 logged returns (set at the call in 70), while it is set at the return in all 174 of modes 4, 5, 7, 8, 9 (2026-11-10-s2a-ai.txt AIU). skills/dispatch's entry table (monster modes 4, 5, 7, 8, 9), § E2 ("a monster's AI sets bit 6 itself, and its mode start does not clear it"), § M1 and skills/README § C ("a monster reaches the start and do through its AI with bit 6 set") are wrong for mode 14. Wanted: a read of sub_005A75C0_MonModeStartSkill, sub_005A7C20_MonSetMode and the sequence mode's start (0x0056FAF0 callers for mode 14) naming the store that clears the bit, so Phase 3 of plan 0066 can reword the four places. Not chased by S2a (its rows only).
