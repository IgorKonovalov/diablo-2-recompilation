---
from: reverser
to: spec-writer
date: 2026-10-17
status: open
context:
  - ../findings/drlg/0009-room-lifecycle.md
resolution: ""
---

Not blocking; after the architect's review of `lane/rbs3`. New static readings ([I]) the specs may take:
- [drlg/0009 § 6 and § 11.1](../findings/drlg/0009-room-lifecycle.md#111-static-follow-ups-of-the-phase-2-review-lanerbs3). `SpecialMonRestore`'s `SpecialModsApply` pushes 0 for `minions`; the handlers run with flag 1 (0x005A214D, 0x005A21A6). § 6 used to read that 0 as the handler flag. `MinionRestore` passes flag 0 itself, so `rndname` takes no unit-seed step there. Every server write of the champion bit follows `MonMarkSpecial`. The path planner refuses a town target for a hostile monster (0x006483A0), with three routes left open.
- [monsters/0003 § 7](../findings/monsters/0003-special-monsters.md#7-monplace-presets-2-and-3-and-0x110x20), bullet *Every MonPlace row, from the switch*: the full `PresetMonSpawn` row table. `place_group25..100` place nothing in `PresetMonSpawn` even when the DRLG preset pass keeps them. Rows 4 (`navi`), 5 (`bloodraven`), 8 (`maggotqueen1`) and 10/11 (`tentaclehead1`–`3` by level) are placed at the point. [drlg/preset](../specs/drlg/preset.md)'s `place_group` rows may want a pointer.
- [monsters/0003 § S3b, special 43](../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16): the save, the restore and the three-slot packet use of the mod list.

*Annotation (architect, `lane/rbs3` review, 2026-10-17):* accepted with fixes; take these into [drlg/lifecycle](../specs/drlg/lifecycle.md) in its next pass (not blocking):
- **H2b and § H's champion note** (spec L618–621, L669–671): the old wording "the code reading of `SpecialMonRestore` names a flag-0 call; which call applies the flag-1 handlers is open" is superseded. State `[C]` that `SpecialMonRestore` applies the flag-1 handlers through its `SpecialModsApply` call (0x005A4558; handler calls at 0x005A214D, 0x005A21A6; second source the run's 15 champion restores), and `[I]` that its pushed 0 is the `minions` argument (0x005A454E, tested at 0x005A2123). Strike the open question "Which call in `SpecialMonRestore` applies the flag-1 handlers"; keep its minion half (stat 12 does not separate H2c's flag 0, which stays `[I]`).
- **§ F, the dead-champion bullet** (L469–473): replace "as far as its creation paths pass `MonMarkSpecial` … Whether every champion path passes one is open" with the § 11.1 (b) reading, still `[I]` (static only: every server write of `0x04` follows `MonMarkSpecial` on the same unit, no server clear of `0x08`; a block copy of monster data unfollowed). The `[C]` "No logged dead champion was saved" stays as is. Strike the open question "A champion without monster flag `0x08`".
- **The town-follow open question** (L862–866): keep it `[L]`, with the § 11.1 (a) result (the path planner refuses a town target for a non-NPC monster; three routes open) in place of the `inTown` lead, which is answered (two combat readers only).
- **MonPlace** (monsters/special, drlg/preset): "places nothing" is scoped to `PresetMonSpawn`, which both the first spawn and the restore reach through `PresetUnitDispatch`; four other callers are unfollowed (monsters/0003 § 7). Word drlg/preset's `place_group` pointer at that scope.
