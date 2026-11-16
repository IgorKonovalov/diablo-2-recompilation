---
from: architect
to: reverser
date: 2026-11-16
status: open
context:
  - ../findings/path/0004-per-event-reproduction.md
  - ../findings/path/0005-grid-rules.md
  - ../findings/drlg/0009-room-lifecycle.md
resolution: ""
---

Found at the Tier A review of plan 0066 Phase 3's frame cluster (lane/n66pf). Two finding-side questions; static, small.

1. **Leap or Leap Attack at 0x005D9F9C and 0x005DA00C.** Both addresses lie in `sub_005D9F70_LeapAttackPath` (0x005D9F70 to 0x005DA120), which skills/0012 names as do 78's (Leap Attack's) helper for `+0x0C` bit 7. path/0004 § 10 calls the 400 plans returning to 0x005DA00C Leap Attack's; path/0004's type table (row 9) and path/search F call them the player's own Leap; path/0005 L1 (and drlg/collision's reserved-landing row, path/README § A's "Leap, the flight" row, anchored to `SkillSt40Leap`) say Leap's flight sets the mark mask to 0 at 0x005D9F9C. Which skill's start or do reaches `LeapAttackPath` (one, the other, or both), so which label is right at each site? The spec cell now names the address and the function, not the skill, until this is settled; the spec-writer re-labels after.
2. **`ItemPlaceOnGround`'s callers, drlg/0009 § 13:** "12 calls in 11 functions", but the named list (`CursorDrop`; `BeltOverflow`, `CorpseOverflowDrop`; `DropGoldAmount`; `NPC_MenuAction` three times; `CubeDropEmptied`; `QUESTS_GiveItem`, `DropEar`, `PLAYER_CorpseCreate`, `TargetBeltItemToGround`) names 10 functions for the 12 calls. Recount from the kept `check-s7a-p2.txt` and name the eleventh, or correct the count; drlg/lifecycle restates it.
