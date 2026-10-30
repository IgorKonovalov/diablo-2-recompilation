---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/done/0053-review-tiers-and-gate-checks.md
resolution: "Fixed in the lane/p53a review commit f4506c2a: monsters/pool and monsters/spawn read '**reviewed** · ', player/creation updated 2026-10-21, stats/aggregate C 65 / I 42 / L 4 (updated 2026-10-20, plan 0047 P1 J4); (4) and (5) settled as map conventions, not exemptions: a spec's own group first after its link (skills row rewritten), a sum in words (combat row), every group gives C, I and L. E15 is an error again (DEMOTED holds only E14). Rule text in evidence-rules.md § Mechanical checks."
---

Plan 0053 Phase 1 adds gate rule E15 (research-map row vs the linked spec: status words, the C/I/L group after the link, the updated date). Six hits in docs/specs/README.md at the branch point 506fb55b (lines are of that file): (1) lines 28 and 29, monsters/pool and monsters/spawn: the Status cell begins 'reviewed: [link]' with no ' · ' after the status word, as every other row has; (2) line 61, player/creation: the row says 'updated 2026-10-20', the spec says updated: 2026-10-21; (3) line 89, stats/aggregate: the row says C 64 / I 42 / L 5, the spec's tags are C 65 / I 42 / L 4; (4) line 88, combat/README: the row's 'C 240 / I 191 / L 24, the five front matters summed' is a sum over five specs, the spec's own tags are C 41 / I 42 / L 5 (false positive of the rule as written; see the plan 0053 Phase 0 log for the proposed exemption); (5) line 91, skills/dispatch: the first group after the skills/README link is 'dispatch C 75 / I 191 / L 10' (a label for the other spec; false positive, proposal in the log). Fix the true ones and decide the rule change for (4) and (5) when copying E15 into evidence-rules.md. Until then E15 stays a warning (tools/gate.py DEMOTED).
