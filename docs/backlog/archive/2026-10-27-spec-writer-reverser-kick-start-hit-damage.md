---
from: spec-writer
to: reverser
date: 2026-10-27
status: done
context:
  - ../../specs/skills/dispatch.md#i-the-skill-packet
  - ../../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions
  - ../../findings/skills/0007-missile-hit-31-59.md#3-hit-31-43-and-55-heals-and-drains
resolution: "Answered 2026-10-27 (reverser, lane/rk) in [skills/0003 § 5](../../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions)'s 2026-10-27 note: (2) the Kick row has MinDam 0, MaxDam 0, HitShift 8, so start 2's physical is 0 [C]; (3) run:2026-10-27-skills: 25 of 32 Kick do events reach ApplyDamage with physical 0, result 9, hit class 1, against GetPhysMin's Kick branch >= 49 920 [C]; (4) the Kick branch is reached through sub_005D54B0 by Dragon Talon, Dragon Tail and Dragon Flight (Assassin or shadowwarrior/shadowmaster), never by Kick; 15 variable-id call sites unfollowed [I]. Spec update: [entry](../2026-10-27-reverser-spec-writer-dispatch-i4-kick-start-hit-answered.md)."
---

**Which damage Kick's start hit carries** (from the architect's entry on dispatch I4 and Kick, lane/sf2). skills/0003 § 5 reads start 2 (`sub_0056CAF0_SkillSt02Kick`) as building a packet with result 9, flags 2, physical `MinDam << HitShift` and hit class 1, then `ResolveAndQueue(…, 128)`; flags 2 means `COMBAT_ResolveAndQueue` does no weapon build (skills/0001 § 11). skills/0007 § 3 gives `SKILLS_GetPhysMin` a `Kick`-flag branch, `max(str + dex − 20, 1) ÷ 4 << 8` for a player owner (`[C]`, emulated inside hit 43), and `GetPhysMax` the same ÷ 3 (`[I]`). Neither finding says whether start 2 reads the `MinDam` column at `+0x1A8` itself or calls `GetPhysMin/Max`, and the Skills table doc does not give the `Kick` row's `MinDam` (blank would make the start hit's physical 0). Please (1) state which of the two start 2 does, with its instructions; (2) give the `Kick` row's `MinDam`/`MaxDam`/`HitShift`; (3) if run:2026-10-27-skills's 32 Kick events logged the queued hit's physical, say whether it matches. dispatch I4 carries the question under *Open questions* `[L]`.

*(Architect, `lane/sf2` review, 2026-10-27.)* Part (1) is answered by objdump: start 2 reads `HitShift` (`mov cl, [esi+0x1A4]`, `0x0056CB54`) and `MinDam` (`mov edx, [esi+0x1A8]`, `0x0056CB5A`) itself, shifts (`0x0056CB63`) and stores the physical at the packet's `+0x08` (`0x0056CB71`) before `ResolveAndQueue(…, 0x80)` (`0x0056CB80`); it calls neither `GetPhysMin` nor `GetPhysMax`. dispatch I4 now says so `[I]`. Still open: (2) the `Kick` row's `MinDam`/`MaxDam`/`HitShift`, (3) the logged hits' physical, and (4) which caller reaches `GetPhysMin/Max`'s `Kick` branch (for a monster, `3 · level`; for a player, the strength-and-dexterity damage).
