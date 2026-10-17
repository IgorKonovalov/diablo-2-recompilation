---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/0001-cases.md
resolution: ""
---

From the plan 0044 Phase 1 review (2026-10-17), for Phase 2's start: (1) the driver's live test is Phase 2's first step, after the port-4000 record (§ 5, human entry); calibrate the hostile button, exit item, trade accept box and trade grid; (2) name 0x005A5E50 (the hostility toggle) and 0x00535B10 (operator hostile to any player) in re/symbols.csv, merging main first; (3) add PlayerData +0x38 (pair list: +0x00 unit id, +0x08 stamp, +0x10 next) and +0x160 (travel tick) to re/types/save.h; (4) write MP25's prediction before any session reaches it, and MP31-MP32's once plan 0043 Phase 1 is accepted, else name them as shortfalls (ruling d); (5) before each session after the first, log the no-root ufw re-read (systemctl is-active ufw, /etc/default/ufw, sha256 of the /etc/ufw rule files) against the record.

*2026-10-17 (reverser, `lane/rbs2`):* (2) done: `sub_005A5E50_PlayerHostileToggle` and `sub_00535B10_PlayerHostileToAny` in `re/symbols.csv` (main merged at 3e169e4, no earlier name). (3) done: `PlayerPair` (`+0x00` unit id, `+0x04` relation flags, bit 8 hostile, `+0x08` stamp, `+0x10` next) and PlayerData `+0x38`, `+0x160` in `re/types/save.h`. (4) MP25's prediction is written ([multiplayer/0001 § 4](../findings/multiplayer/0001-cases.md#mp25-prediction-which-aurafilter-bits-pass-a-player-2026-10-17-lanerbs2)); MP31–MP32 wait for plan 0043 Phase 1's acceptance. (1) and (5) are Phase 2 session steps (harness, owner), left for the plan 0044 Phase 2 lane.
