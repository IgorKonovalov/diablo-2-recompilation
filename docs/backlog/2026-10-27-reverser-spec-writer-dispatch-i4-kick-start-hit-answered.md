---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../specs/skills/dispatch.md#i-the-skill-packet
  - ../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions
resolution: ""
---

Released by lane/rk (reverser, 2026-10-27), once its architect review accepts it. Replace dispatch I4's Kick *Open questions* [L] with skills/0003 § 5's 2026-10-27 note: (a) [C] the stock Kick row (skills.bin row 1) has MinDam 0, MaxDam 0, the level bands 0, DmgSymPerCalc blank and HitShift 8, so start 2's physical is 0 << 8 = 0 (tbl:Skills.txt:MinDam); (b) [C] run:2026-10-27-skills: 25 of Kick's 32 do events reach COMBAT_ApplyDamage, each with result 9, physical 0 and hit class 1, which separates start 2's MinDam << HitShift from GetPhysMin's Kick branch (at least 49 920 for SkillsBarH); that the start stores MinDam << HitShift rather than nothing stays the code's [I] (0x0056CB54-0x0056CB71); the 7 deliveries with no ApplyDamage are not read [I]; (c) [I] GetPhysMin/Max's Kick branch (the +0x05 bit 0x02, set in rows 1, 255, 270, 275) is reached through sub_005D54B0_SkillKickPhysDamage from start 24/do 42 (Dragon Talon), start 27 (Dragon Tail) and do 52 (Dragon Flight), for an Assassin (str + dex - 20) or shadowwarrior/shadowmaster (3 · level, their MonStats Dragon Flight); Kick itself never reaches it; GetPhysMax's branch is sub_00644C20_SkillKickDamage's only call (0x00647D41); 15 call sites with a variable skill id are unfollowed. wiki/skills carries the same question.
