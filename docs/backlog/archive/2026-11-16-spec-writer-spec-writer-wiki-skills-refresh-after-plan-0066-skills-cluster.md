---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../specs/README.md
  - ../../wiki/skills.md
resolution: "Refreshed in lane/fuw: [wiki/skills](../../wiki/skills.md) states the packet table and request counter, dual-wield alternation, the logged code-0 paths, checks 7 to 10 under emulation, the start's logged path and the target test (bit 1 and TargetCorpse, no dead target), the once-per-mode flag and mode 14's clear, the monster's absent request check, slow's stat 67 = −v, the handlers run under emulation, the summon level's clamps and noRatio, Impale's wrapped break test, the at-a-point creators and MissileCreate to its allocation; based_on bumped."
---

Plan 0066 Phase 3, the skills cluster (`lane/n66sk`, parts 1 and 2), updated skills/README, skills/missiles,
skills/catalogue, skills/dispatch and quirks (Q21, Q41, Q140, Q360, Q408, Q434, Q444, Q462, Q463, Q467, Q470; Q262 and
Q263 now cite dispatch n2 and n7) on 2026-11-16, so wiki/skills carries W4 for all four specs. What changed for a
reader: the request path (packet table, request counter, checks C4–C7, `TargetCheck`, the ally test) and the logged
start, do, payment and delay paths are confirmed; **a monster in mode 14 has bit 6 cleared by its start**, so its do
runs on a code 1 or 2 like a player's; D2's target clear no longer speaks of a "dead" target: `+0xC4` bit 1 and `TargetCorpse` decide it (dispatch
D2's table); slow's block carries stat 67 = −v; handlers 6–10, 14–19, 25–27 and 31 are confirmed to their boundaries;
the summon level's clamps and the missing `noRatio` test are confirmed; weapon wear's break test is a wrapped sign
test; on the missiles side the at-a-point creators (two monster AIs, no shrine), `MissileCreate` up to its allocation
and the critical chain's later steps are confirmed. Refresh the page against the specs (spec-writer review-fixes 1: a
page follows the spec that carries the raise) and bump `based_on`. Not blocking.
