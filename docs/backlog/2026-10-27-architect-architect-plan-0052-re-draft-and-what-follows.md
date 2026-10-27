---
from: architect
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0052-monster-ai.md
  - ../plans/README.md
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
resolution: ""
---

**Re-draft plan 0052 (monster AI) at its gate, and propose what follows it.** The 0045·P3 review (`lane/s45p3`, accepted with fixes 2026-10-27) opened 0052's approvability (ADR-0020); per the run order the architect re-drafts 0052 now, outside that review: settle the six scoping questions of the first draft (the owner leans towards pathing as its own part), fold in what plan 0045 handed over (the 171 + 160 monster caster gaps of skills/dispatch § P, which point at the AI; `MonAiUseSkill`'s choice as the input skills/dispatch § M1 takes; the Raven class's owner skill-damage pair), and keep 0052·P2 after 0050·P3's review (ADR-0016). Then hand 0052 to the owner for approval: the owner approves it, not the architect. Per the owner's 2026-10-27 decision (plans README, *Planning after 0052*), the re-draft also proposes what follows 0052: phase (5) is ADR-0014's last phase, so anything beyond the remaining 0038/0046 tails needs a scope ADR for the owner, ready before 0052·P2 starts so the static lanes and the archivist do not go idle.
