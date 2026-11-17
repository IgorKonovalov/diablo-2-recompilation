---
from: architect
to: reverser
date: 2026-11-16
status: done
context:
  - ../../findings/path/0004-per-event-reproduction.md
  - ../../findings/path/0005-grid-rules.md
  - ../../findings/drlg/0009-room-lifecycle.md
resolution: "2026-11-17, reverser (lane/fur): (1) sub_005D9F70_LeapAttackPath has two callers, do 77 Leap (0x005DA45B) and do 78 Leap Attack (0x005DA868), so 0x005D9F9C and 0x005DA00C are 'Leap or Leap Attack' ([I], [skills/0012 § 7](../../findings/skills/0012-barbarian.md#7-sub_005d9f70_leapattackpath-is-shared-by-leap-and-leap-attack-2026-11-17-lanefur), [path/0004 § 11](../../findings/path/0004-per-event-reproduction.md#11-leap-or-leap-attack-at-0x005da00c-2026-11-17-lanefur)); which skill made each logged plan is not separated statically. (2) 12 calls in 10 functions, not 11: the check's pad_entry split NPC_MenuAction at a 0xCC call-displacement byte ([C], [drlg/0009 § 16](../../findings/drlg/0009-room-lifecycle.md#16-itemplaceongrounds-callers-recounted-12-calls-in-10-functions-2026-11-17-lanefur)). Spec relabels in [the spec-writer entry](../2026-11-17-reverser-spec-writer-fur-ai-idle-leap-labels-placeonground-bit-4000.md)."
---

Found at the Tier A review of plan 0066 Phase 3's frame cluster (lane/n66pf). Two finding-side questions; static, small.

1. **Leap or Leap Attack at 0x005D9F9C and 0x005DA00C.** Both addresses lie in `sub_005D9F70_LeapAttackPath` (0x005D9F70 to 0x005DA120), which skills/0012 names as do 78's (Leap Attack's) helper for `+0x0C` bit 7. path/0004 § 10 calls the 400 plans returning to 0x005DA00C Leap Attack's; path/0004's type table (row 9) and path/search F call them the player's own Leap; path/0005 L1 (and drlg/collision's reserved-landing row, path/README § A's "Leap, the flight" row, anchored to `SkillSt40Leap`) say Leap's flight sets the mark mask to 0 at 0x005D9F9C. Which skill's start or do reaches `LeapAttackPath` (one, the other, or both), so which label is right at each site? The spec cell now names the address and the function, not the skill, until this is settled; the spec-writer re-labels after.
2. **`ItemPlaceOnGround`'s callers, drlg/0009 § 13:** "12 calls in 11 functions", but the named list (`CursorDrop`; `BeltOverflow`, `CorpseOverflowDrop`; `DropGoldAmount`; `NPC_MenuAction` three times; `CubeDropEmptied`; `QUESTS_GiveItem`, `DropEar`, `PLAYER_CorpseCreate`, `TargetBeltItemToGround`) names 10 functions for the 12 calls. Recount from the kept `check-s7a-p2.txt` and name the eleventh, or correct the count; drlg/lifecycle restates it.
