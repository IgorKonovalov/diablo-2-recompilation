---
from: spec-writer
to: reverser
date: 2026-10-27
status: open
context:
  - ../specs/skills/dispatch.md#i-the-skill-packet
  - ../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions
  - ../findings/skills/0007-missile-hit-31-59.md#3-hit-31-43-and-55-heals-and-drains
resolution: ""
---

**Which damage Kick's start hit carries** (from the architect's entry on dispatch I4 and Kick, lane/sf2). skills/0003 § 5 reads start 2 (`sub_0056CAF0_SkillSt02Kick`) as building a packet with result 9, flags 2, physical `MinDam << HitShift` and hit class 1, then `ResolveAndQueue(…, 128)`; flags 2 means `COMBAT_ResolveAndQueue` does no weapon build (skills/0001 § 11). skills/0007 § 3 gives `SKILLS_GetPhysMin` a `Kick`-flag branch, `max(str + dex − 20, 1) ÷ 4 << 8` for a player owner (`[C]`, emulated inside hit 43), and `GetPhysMax` the same ÷ 3 (`[I]`). Neither finding says whether start 2 reads the `MinDam` column at `+0x1A8` itself or calls `GetPhysMin/Max`, and the Skills table doc does not give the `Kick` row's `MinDam` (blank would make the start hit's physical 0). Please (1) state which of the two start 2 does, with its instructions; (2) give the `Kick` row's `MinDam`/`MaxDam`/`HitShift`; (3) if run:2026-10-27-skills's 32 Kick events logged the queued hit's physical, say whether it matches. dispatch I4 carries the question under *Open questions* `[L]`.
