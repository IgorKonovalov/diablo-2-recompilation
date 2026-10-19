---
from: architect
to: spec-writer
date: 2026-10-17
status: done
context:
  - ../findings/quests/0002-travel.md
  - ../findings/multiplayer/0001-cases.md#4-the-hostility-declaration-and-the-two-travel-gates
resolution: "Folded into the Phase 3 draft: both gates read the operator's own +0x160, no portal exempt, the hostility refusal ([quests/travel § J](../specs/quests/travel.md#j-operate-gates-and-real-time-gates), § D, § G)."
---

For plan 0042 Phase 3 (quests/travel): quests/0002's real-time gates were corrected at the plan 0044 Phase 1 review (2026-10-17). Both the waypoint (10 000 ms) and portal (5000 ms) gates read the operator's own PlayerData +0x160, set by the hostility declaration 0x005A5E50; no portal is exempt; a player hostile to anyone cannot use a portal it does not own (held). Take § 6, § 9 and the Phase 1b verdicts as they now read, and multiplayer/0001 § 4 for the declaration.
