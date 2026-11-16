---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/path/0001-pathplan-register.md#16-plan-0066-batch-s7a-part-2-stores-masks-and-flag-readers-with-a-second-tool-2026-11-16-lanen66n
  - ../../findings/drlg/0009-room-lifecycle.md#13-plan-0066-batch-s7a-part-2-bit-and-caller-scans-with-a-second-tool-2026-11-16-lanen66n
  - ../../findings/frame/0001-tick-and-messages.md#9-plan-0066-batch-s7a-part-2-the-frames-reach-to-the-packet-senders-2026-11-16-lanen66n
resolution: "Done 2026-11-16 in plan 0066 Phase 3, frame cluster (lane/n66pf): path/README's SizeY bullet names the two AI removals, drlg/lifecycle lists ItemPlaceOnGround's 12 calls, sim/frame Outputs states the one-byte 0xB0 send inside the frame, path/README D4 adds flag 0x40 [log](../../plans/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-frame-cluster-re-tagged-spec-writer-lanen66pf)"
---

Plan 0066 batch S7a part 2 (lane/n66n) contradicted three spec statements in part and corrected one; each needs the spec text changed after the review.

1. path/README line 128 (`SizeY` is unused by a monster's footprint): `UNIT_CollUnmarkRect` has no type test and reads `UNIT_GetSizeY`, whose type-1 arm reads MonStats2 `+0x09`; `AiWussie` (0x005EE452) and `AiBaalToStairs` (0x005EF6B7) call it on the AI's own monster, so those removals clear a SizeX x SizeY rectangle. The statement needs a scope (the marks; the CollMark/CollUnmark pair) and the two removals named. Stock data cannot separate it (equal columns).
2. drlg/lifecycle line 156 (`ItemPlaceOnGround`'s callers beyond `CursorDrop`): four callers are missing from the list: `QUESTS_GiveItem` (0x005467B5), `DropEar` (0x0055A286), `PLAYER_CorpseCreate` (0x0057FA7D), `TargetBeltItemToGround` (0x005A3213).
3. sim/frame Outputs line 925 (nothing else leaves the frame but queued packets): `AutosaveTick` sends a one-byte packet 0xB0 through the transmit routine 0x0052B330 inside the frame (chain at 0x0052D8F9, 0x0052D4A9, 0x0052D40E, 0x0052CB88, 0x0053B231), gated on `[0x00883D50]`, not through the queue.
4. path/README D4 line 350 ("the only flag a planner reads is 0x200"): a planner's graph also tests flag 0x40 (`PathFaceDir`, 0x0064862B), outside the 0x0007FF00 that `PathSetType` copies; of the type flags, 0x200 is the only one. A wording fix, filed raised with a correction.

The inventory rows (path-README 17, 38; lifecycle 12; sim-frame 117) carry the S7a notes. Re-tag after the architect's review of S7a.
