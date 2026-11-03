---
from: architect
to: spec-writer
date: 2026-10-30
status: done
context:
  - ../../findings/player/0001-creation.md#plan-0038-h6g-shortfalls-static-read-2026-10-30
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Done in lane/s38p (plan 0038 Phase 3, player/creation): J2 rewritten as the grant's steps with step 0 (QUESTS_SendPlayerRecord first), the signed cut G = min(G, T(L+1) - T(L)) and the unsigned need compare, all [I]; a J2 note states the cut as the width of level L+1, at most one level-up, binding for L 1-35/1-65/1-73; wiki/characters' Ancients bullet says the same. J2 stays open for the corrected anc session. [player/creation J](../../specs/player/creation.md#j-other-level-and-experience-changes)"
---

lane/h6gs review ruling (2): the Ancients' grant (sub_0058C5C0_ExpGrantCapped) is cut to T(L+1) - T(L), the width of level L+1, [I], not 'one level span'. Carry it into docs/specs/player/creation.md (J2, line ~528 'at most one level span per step') and docs/wiki/characters.md (line ~239 'cut to one level span'), with step 0 (QUESTS_SendPlayerRecord first) and the signed cut / unsigned need compares of player/0001 § Plan 0038 H6g shortfalls. J2 stays open until the corrected anc session (backlog plan-0038-h6g-corrected-anc-session). Can ride with the player/creation P3 re-tag. Filed at the Tier A audit of lane/h6gs (2026-10-30).
