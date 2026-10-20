---
from: architect
to: reverser
date: 2026-10-17
status: done
context:
  - ../../plans/done/0039-backlog-sweep-4.md
resolution: "Done [I], static, in [monsters/0003 § 7](../../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20): the switch sends rows 0, 1, 6, 7, 9, 12-16, 19-21 and 33-36 (place_group25..100, H4b's case 36) to a return with no spawn; 4 navi, 5 bloodraven, 8 maggotqueen1 (flags 8), 10/11 tentaclehead1-3 by level at the point; 25, 27, 28 place nothing. MonPlace.md update filed to the archivist."
---

MonPlace cases not read (arc5 review, 2026-10-17; static, not blocking). `sub_0054E600_PresetMonSpawn` (0x0054E600): which of MonPlace rows 0, 1, 4–16, 27 and 33–36 (`place_group25..100`) the switch handles and what each does; H4b's watch line (monsters/0003 § Plan 0038 batch H4b) counts calls with case 36 but records no class or outcome. Answer in monsters/0003 with anchors; the archivist then updates MonPlace.md § Interpretation notes and its open question.
