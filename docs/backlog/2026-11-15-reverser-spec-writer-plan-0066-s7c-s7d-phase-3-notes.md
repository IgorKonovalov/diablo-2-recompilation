---
from: reverser
to: spec-writer
date: 2026-11-15
status: open
context:
  - ../findings/path/0004-per-event-reproduction.md#10-plan-0066-batch-s7c-new-checks-over-the-kept-logs-2026-11-15-lanen66m
  - ../findings/drlg/0009-room-lifecycle.md#115-plan-0066-batch-s7d-new-checks-over-the-kept-logs-2026-11-15-lanen66m
resolution: ""
---

For Phase 3 of plan 0066, with the S7c and S7d rows (no contradiction was found; these are wording and scope notes).
Not blocking.

1. **path/README entry table, "A blocked path is planned again"** (`PathReplan`): its 4 callers are the blocked step
   (0x00650757, `PathStepMove`), two in `PathStepTargetCheck` (0x0065043C, an ended path short of `+0x18` with no
   target, flag 0; 0x006504D7, a target moved more than 5, flag 1) and 0x00649289. The label names only the first
   (path/0004 § 10; anim/movement B5 already gives the target check's replan).
2. **path/README § A table, Leap:** the test mask is "not stated here"; Leap Attack's 400 logged plans carry test
   mask 0 as well as mark 0 (return 0x005DA00C). Vultures plan with test mask 0 after `AiVultureTakeOff`'s
   `PathSetCollMask(path, 0)` (0x005F2FA2), a writer the table does not list.
3. **path/README E3:** "13 through `PathReplan`": the logs also have 7 363 type-13 requests from `MonPathPlanType`
   (machinery D5's default 13); "falls back" is in `MonPathPlanType` (0x005A634E), called by `MonMovePlan`
   (0x005A6449).
4. **path/README E2:** the unit's mode at `PathPlan`'s entry from `PlrModeStartMove` is the old mode; a spec that says
   "mode 19 plans type 8" describes the new mode (`EDI`).
5. **drlg/lifecycle G / H2, "oldest first":** the restore order is the reverse of the save walk (829 restores), and
   unit ids rise along it in 372 of 563 multi-record restores, so "oldest" is the list's order, not the units' age.
6. **path/README § A table, monster row** (added at the Tier A review, 2026-11-16): the wraith's `0x804` is
   `PATH_DynamicCreate`'s own branch (`cmp eax, 0x26` at 0x00649E3E, the store at 0x00649E60), taken before
   `PATH_MonTestMask` is called (0x00649E45); `PATH_MonTestMask` (0x00648480–0x006484D1) has the three arms only. The
   row's cell names the wraith under `PATH_MonTestMask` with that function's anchor alone; § B's pseudocode line
   (`testMask ← PATH_MonTestMask (wraith, base id 38: …)`) has the order right. path/0004 § 10 counts 21 099 plans for
   the function's arms and 27 for the wraith branch.
