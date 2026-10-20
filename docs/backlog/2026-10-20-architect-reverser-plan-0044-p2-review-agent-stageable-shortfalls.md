---
from: architect
to: reverser
date: 2026-10-20
status: open
context:
  - ../plans/done/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/experiments.md#run2026-10-20-two-clients
resolution: ""
---

Out of plan 0044 (Phase 2 review, 2026-10-20), for a later two-client run when both slots are free; none blocks Phase 3. (1) drivers/ufwcheck.sh must exit non-zero on a change (today it always exits 0, and its Policy="ACCEPT" pattern misses the upper-case line); keep it in tools/ next time, not only in the run's drivers. (2) Agent-stageable shortfalls: MP18 (a recipe with a rune and a socketed item for the joiner), MP21 (plan 0040's lifecycle logger merged into a two-client logger), MP27 (a QuestFlag portal session), MP28 (b) and (c) (a pilot route that reaches every Den room), MP30 (an e9/e10 line in quests.py), MP25's offensive auras (a recipe with an 0x8000 aura), MP20's per-player room attribution, MP16 kills just inside d2 6400; MP31 and MP32 need their predictions written first (Phase 1 ruling d). (3) combat.py --no-shield is hand-fed from the recipes; a logged shield flag on the defender would make it a check. (4) Added at the plan 0044 close (Phase 3 review, 2026-10-20): the plan 0047 case logged in plan 0044 after its run, open wounds on a player (stat 135 comes only from item properties, so only a hostile player wounds a player): player B, hostile, wearing an open-wounds item (tool-built, ADR-0013 Neutral), hits player A; the stats logger's state and tick lines on A ([plan 0047 log](../plans/0047-simulation-shortfalls.md#implementation-log)).

2026-10-20, reverser (`lane/mp26`): (1) done statically. `tools/ufwcheck.sh <session> <baseline> <log>` is the fixed successor of `drivers/ufwcheck.sh` (the run copy is kept unchanged, manifest hash `47c1d42d…`): it exits 1 with `UFW-CHANGED` unless ufw is active and enabled, the line is exactly `DEFAULT_INPUT_POLICY="DROP"`, `ENABLED=yes` and every baseline hash checks, and exits 2 on a missing argument or baseline; it reads only the input-policy line (the unchanged file also holds `DEFAULT_OUTPUT_POLICY="ACCEPT"`). Self-test in `workspace/logs/mp26/check-mp26.txt` § C ([experiments](../findings/multiplayer/experiments.md#run2026-10-20-two-clients), the precondition). (2)–(4) stay open: they need both harness slots.
