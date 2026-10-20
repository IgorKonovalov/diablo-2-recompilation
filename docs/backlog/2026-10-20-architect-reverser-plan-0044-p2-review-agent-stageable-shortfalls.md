---
from: architect
to: reverser
date: 2026-10-20
status: open
context:
  - ../plans/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: ""
---

Out of plan 0044 (Phase 2 review, 2026-10-20), for a later two-client run when both slots are free; none blocks Phase 3. (1) drivers/ufwcheck.sh must exit non-zero on a change (today it always exits 0, and its Policy="ACCEPT" pattern misses the upper-case line); keep it in tools/ next time, not only in the run's drivers. (2) Agent-stageable shortfalls: MP18 (a recipe with a rune and a socketed item for the joiner), MP21 (plan 0040's lifecycle logger merged into a two-client logger), MP27 (a QuestFlag portal session), MP28 (b) and (c) (a pilot route that reaches every Den room), MP30 (an e9/e10 line in quests.py), MP25's offensive auras (a recipe with an 0x8000 aura), MP20's per-player room attribution, MP16 kills just inside d2 6400; MP31 and MP32 need their predictions written first (Phase 1 ruling d). (3) combat.py --no-shield is hand-fed from the recipes; a logged shield flag on the defender would make it a check.
