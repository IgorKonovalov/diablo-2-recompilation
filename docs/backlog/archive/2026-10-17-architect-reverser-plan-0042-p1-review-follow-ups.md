---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/0042-quests-travel.md#implementation-log
  - ../../findings/quests/0001-progression.md
  - ../../findings/quests/0002-travel.md
resolution: "lane/rbs2 2026-10-17: (a) the 31 W1 lines anchored (quests/0001 27, quests/0002 4; gate W1 count 53 → 22); (b) [I] rejoin = 1 is the two new-character builders, 0 the two save readers, and a stub character joins twice ([quests/0001 § 3](../../findings/quests/0001-progression.md#3-the-join-and-the-game-wide-record)); (c) [I] cleared by the client's packet 0x48 through 0x005350B0 ([quests/0002 § 9](../../findings/quests/0002-travel.md#9-act-change-state-and-real-time-gates)); (d) optional, not taken, carried in the static-sweep-remaining entry."
---

[2026-10-17] from architect → reverser: plan 0042 P1 review follow-ups (static, not blocking; with the P2 lane or any static batch, before 0042·P3). (a) Gate W1: 31 [I] lines of quests/0001 (27) and quests/0002 (4) carry only a section reference (§ n) as anchor; give each an address, fn: or data: anchor (reverser review-fixes rule 7). (b) quests/0001 § 3: name the flows behind QuestsPlayerJoin's rejoin = 1 (0x00532673, 0x0056A072 after 0x005701B0) and rejoin = 0 (0x005344EF, 0x0053458F). (c) quests/0002 § 9: find where player data +0x4C (act change in progress) is cleared, since it blocks operates and waypoint menus. (d) Optional: what 0x0056EDE0(0, 1, 0x120, …) creates at the fifth cairn stone (quests/0001 § 7, word 4). Context: [plan 0042 log](../../plans/0042-quests-travel.md#implementation-log)
