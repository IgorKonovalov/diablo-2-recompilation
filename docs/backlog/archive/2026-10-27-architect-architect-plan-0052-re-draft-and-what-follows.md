---
from: architect
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0052-monster-ai.md
  - ../../plans/README.md
  - ../../plans/done/0045-skills-missiles-machinery.md#implementation-log
resolution: "2026-10-27 (architect, lane/plans52): plan 0052 re-drafted at its gate, status proposed, eight scoping questions with recommendations for the owner (pathing its own plan, one plan with the spec in two parts, the logger ADR only if needed, hirelings and summons in, one slot, the gate confirmed, ADR-0022 next, stock-row coverage); the handed-over items H1-H6 folded in; ADR-0022 (proposed) drafts what follows (the server frame composed), with the sweep and player-side rules weighed in its alternatives and the plans README; run order updated (state on 2026-10-27, 0052 items awaiting the owner)."
---

**Re-draft plan 0052 (monster AI) at its gate, and propose what follows it.** The 0045·P3 review (`lane/s45p3`, accepted with fixes 2026-10-27) opened 0052's approvability (ADR-0020); per the run order the architect re-drafts 0052 now, outside that review: settle the six scoping questions of the first draft (the owner leans towards pathing as its own part), fold in what plan 0045 handed over (the 171 + 160 monster caster gaps of skills/dispatch § P, which point at the AI; `MonAiUseSkill`'s choice as the input skills/dispatch § M1 takes; the Raven class's owner skill-damage pair), and keep 0052·P2 after 0050·P3's review (ADR-0016). Then hand 0052 to the owner for approval: the owner approves it, not the architect. Per the owner's 2026-10-27 decision (plans README, *Planning after 0052*), the re-draft also proposes what follows 0052: phase (5) is ADR-0014's last phase, so anything beyond the remaining 0038/0046 tails needs a scope ADR for the owner, ready before 0052·P2 starts so the static lanes and the archivist do not go idle.
