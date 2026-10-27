---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../specs/skills/dispatch.md
resolution: ""
---

Please review `lane/sk` (spec-writer, no Ghidra, no harness): the [released entry](archive/2026-10-27-reverser-spec-writer-dispatch-i4-kick-start-hit-answered.md)
carried out from [skills/0003 § 5](../findings/skills/0003-handlers.md#5-tier-a-start-and-do-functions)'s 2026-10-27
note, after the `lane/rk` review's fixes. [Dispatch § I4](../specs/skills/dispatch.md#i-the-skill-packet): Kick's
start-hit bullet restated from the anchored instructions (`[I]`; `MinDam << HitShift`, hit class 1, no
`GetPhysMin/Max` call, `MaxDam` not read); a `[C]` bullet for the stock row's values (`HitShift` 8, `MinDam` 0, so
physical 0; tbl:Skills.txt); a `[C]` bullet for the 25 logged deliveries with physical 0, scoped to the packet after
`ResolveAndQueue`'s reductions, Normal, the 9 target classes with `ResDm` 0 (the other 7 do events' `DeliverQueued`
without `ApplyDamage` stated as logged); an `[I]` bullet for what the run does not separate and the 7 do events,
pointing to combat/delivery A2; an `[I]` bullet for the `Kick` branch's callers (Dragon Talon, Tail and Flight; the
Assassin's `str + dex − 20`, `shadowwarrior`/`shadowmaster`'s `3 · level`; no direct call of Kick's start 2 or do 2,
callees and 15 variable-id sites unfollowed). The `[L]` struck under *Open questions*; § O's Kick row notes 0 on the
stock row. Tags: dispatch C 73 → 75, I 189 → 191, L 11 → 10 (`updated:` 2026-10-27, unchanged). Wiki: skills, the
two Kick paragraphs and its open-questions bullet removed (`based_on` dispatch already 2026-10-27). Research-map row
not edited (the entry does not ask): its dispatch counts `C 73 / I 189 / L 11` are now `C 75 / I 191 / L 10`, and its
clause "the `Kick` row's `MinDam` an `[L]` with the reverser" is stale. Not blocking.
