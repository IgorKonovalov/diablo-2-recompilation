---
from: reverser
to: architect
date: 2026-10-19
status: open
context:
  - ../plans/0042-quests-travel.md
  - ../findings/quests/experiments.md#run2026-10-19-quests3
  - ../findings/quests/0001-progression.md#17-phase-2-part-3-run2026-10-19-quests3
  - ../findings/quests/0002-travel.md#14-phase-2-part-3-run2026-10-19-quests3
resolution: ""
---

Review plan 0042 Phase 2 part 3 (run:2026-10-19-quests3, `lane/p42r`, slot 2): the run record, quests/0001 § 17,
quests/0002 § 14, the corrections carried into the sections they correct, and the plan log entry. The lane's final
commit carries the totals, the two manifests and the re-check of the 32 part 1 and 2 logs.

Asked of the review in particular:
- **Corrections:** (1) word 11's eclipse is once per game by the quest state (`QUESTS_SetStep(1)` when the eclipse
  starts), not by private `+0x01`, which the timer clears (quests/0001 § 8); (2) the cairn order is drawn on the use of
  the decoded scroll `bkd ` (`0x00544840` → `0x00593CB0`), the trigger "scroll send" refined (§ 7, § 11); (3) the
  expansion Act IV → V travel is the Harrogath portal (object 566, `0x005B5880`), not NPC 367's menu, which the stock
  client does not offer (quests/0002 § 5; screenshot kept); (4) Meshif's Act III menu has no trade line (driver only).
- **Shortfall rulings:** the Zoo (object 567 placed by no DS1 and created by no code: unreachable, like NPC 377);
  waypoint activation from mode 0 (three attempts, no operate; the mode reading kept as `[I]` through `wpmodes`);
  the e3 rows listed as not reached in § 17's candidates table; the Dark Wanderer's 7-try branch
  (`low & 1` was 0 in all four games).
- **Driver deviations:** x-entry and x-entry2 were finished by hand-run `quest_sessions.py act` commands inside the
  same game (the logs are continuous; the written saves copied beside the logs by hand); h-entry likewise from the
  Kurast Docks onwards, and x-wpact3r-0's Save and Exit; x-wpactr-0 was stopped by hand.

Totals (from the kept check outputs): 13 recorded sessions, 0 mismatches over 6 167 checks (`quests3-check.txt`,
`7cde7b36…`); the 32 part 1 and 2 logs 0 over 39 568 (`quests3-recheck-p12.txt`, `3f2b7de7…`); 12 development logs
0 over 2 498. Manifests from `workspace/logs/quests/`: `quests3-manifest.sha256` (43 lines, `1975e350…`) and
`dev-p42r-manifest.sha256` (26 lines, `38d3aaa5…`). Blocking the Phase 3 review (the quests spec is re-tagged from the
part 3 raises once this review rules).
