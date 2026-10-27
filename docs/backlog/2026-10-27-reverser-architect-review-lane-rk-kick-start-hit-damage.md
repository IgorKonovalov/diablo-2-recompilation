---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions
  - archive/2026-10-27-spec-writer-reverser-kick-start-hit-damage.md
resolution: ""
---

Review lane/rk: the backlog entry on Kick's start-hit damage (raised by the lane/sf2 review, plan 0038 log). skills/0003 § 5's 2026-10-27 note and two Answer bullets: the Kick row's values [C] (tbl), the 25 logged ApplyDamage packets against MinDam << HitShift [C] (run:2026-10-27-skills, tools/kick_hits.py, new), the Kick branch's callers [I] (xrefscan, objdump). New symbol sub_005D54B0_SkillKickPhysDamage (I). Kept outputs workspace/logs/rk/ (rk-manifest.sha256). Static only: no Ghidra, no harness; the log rescan under MemoryMax=4G. Ledger row added with usage '—'.
