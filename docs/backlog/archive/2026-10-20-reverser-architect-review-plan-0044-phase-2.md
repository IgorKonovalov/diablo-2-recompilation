---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/done/0044-multiplayer-branches.md#implementation-log
  - ../../findings/multiplayer/experiments.md#run2026-10-20-two-clients
  - ../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (9); port-4000 precondition met as the owner's condition asks (owner's 2026-10-17 root listing; no-root re-read and hashes before live-1 and before each of the 18 later sessions, 20 entries, 0 FAILED; no rule changed); the four checker changes ruled the checker's errors; Phase 2 done, Phase 3 may start. Plan 0044 log, 2026-10-20 review entry."
---

Review plan 0044 Phase 2 (`lane/p44h`): run:2026-10-20-two-clients, 19 two-client sessions on slots 1 and 2 after the
port-4000 precondition (the owner's 2026-10-17 listing plus the no-root re-read and rule-file hashes before every
session, all unchanged). The driver's live test passed (six steps) before any case session. Every checker reports 0
mismatches (`workspace/logs/p44h-run/check-run.txt`). Done-when counts: 417 party kills with drops, 46 vendor stock
events with two players, 385 party experience shares, 12 quest-bit writes with both players present, 230 player
against player attack events. Shortfalls named in the record (MP12–MP14, MP17, MP18, MP21, MP27, MP28 b/c, MP30, MP31,
MP32, parts of MP20, MP23, MP24, MP25). Checker changes to rule on: `combat.py --no-shield` (66 melee events whose
defender holds no shield), `monstats.py` live players from PLRS, `vendors.py` reading the renamed ETB tags, `tc.py`'s
owner for a monster killer, and the new `tools/mp_check.py` (xpshare, gates, aura, quests). Not blocking.
