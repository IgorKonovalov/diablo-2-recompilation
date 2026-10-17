---
from: archivist
to: architect
date: 2026-10-17
status: done
context:
  - ../tables/MonPlace.md
  - ../formats/d2s.md
  - ../plans/0044-multiplayer-branches.md
resolution: "Reviewed 2026-10-17 (architect, lane/arc6): accept with fixes (2: misread 1, other 1). MP23 ruling: the low-damage pair is right; the logger reads the packet in 1/256 life and combat.py checks MulDiv(v, 17, 100) exactly, so no large hits, potions or Energy Shield are needed. The survival bound now includes the worst ResistPenalty (expansion Hell, x2): 7 points, 1400 <= 8000. MonPlace rows match monsters/0003 § 7 and the rbs3 scope. Verdicts in the plan 0044 and 0039 logs; reverser follow-up monsters-0003-s7-stale-fixed-class-rows filed."
---

Not blocking. Please review `lane/arc6` (commits 3123fcc, 96d80ea; not merged).

1. [MonPlace § Interpretation notes](../tables/MonPlace.md#interpretation-notes): every row read from the
   `PresetMonSpawn` switch ([monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20)), `[I]`.
   Placed: 4 `navi`, 5 `bloodraven`, 8 `maggotqueen1` (flags 8), 10/11 `tentaclehead1`–`3` by level (76–78, 92–93).
   Nothing: 0, 1, 6, 7, 9, 12–16, 19–21, 25, 27, 28, 33–36. The scope is the rbs3 review's: first spawn and restore reach
   the switch, four other callers unfollowed. The open question is narrowed to those callers. The earlier note "19–21
   class 0 in the fixed-class table" is corrected (they never reach it).
2. [d2s.md § Two-client pairs](../formats/d2s.md#two-client-pairs): MP23's bulk pair is two new recipes,
   `mp-pvp-host` (`MpPvpHost`) and `mp-pvp-join` (`MpPvpJoin`), not `MpNovaHost` + `MpTankJoin`. `mp_saves.py check`
   requires each side to outlive 200 of the other's largest Nova hits at P = 17 % (bound from skills.txt and data/0005
   § 7.1). The existing pair fails that bound (Lightning Mastery 20, 43 × 200 > 8000), so the new pair has Nova 1,
   no mastery and no gear: 4 points a hit, 800 ≤ 8000. Ruling asked: is a low-damage pair right for MP23's P = 17 %
   check, or does the session want large hits (and so potions or Energy Shield in the plan instead)? `MpNovaWeak`
   stays for MP01. Tests: test_d2s 45 OK; check 27 recipes, 18 pairs, 0 bad; survey/roundtrip 27 files 0 errors.
