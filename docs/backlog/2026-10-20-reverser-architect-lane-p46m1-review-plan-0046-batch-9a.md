---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../plans/0046-skills-function-catalogue.md
  - ../findings/skills/0004-missile-do-1-18.md
  - ../findings/skills/experiments.md#run2026-10-20-cat-emu-9a
resolution: ""
---

Review `lane/p46m1` (from main `e90913a`; Ghidra copy `workspace/ghidra-p46m1`, no harness): [plan 0046](../plans/0046-skills-function-catalogue.md)
Phase 1 batch **9a**, missile server do functions 1–18. Blocking 9b (the next batch in the static order).

- **Read.** 17 entries: do 1, 3, 5 tier A (cited, not re-read); do 2, 6–18 read in
  [skills/0004](../findings/skills/0004-missile-do-1-18.md), with the do-1 table slot (a `jmp` thunk, `0x005B0BC0`)
  and the helpers `0x005A9720`, `0x005A9820` (its register convention: EAX period, ESI missile), `0x006416D0`,
  `0x00553490`, `0x00648AD0`, `0x005DB6D0` (Guided Arrow's skill do 10, the writer of do 7's words).
- **Draws.** Only `0x005A9820` (do 8, 10, 17: re-seed of the missile seed to `(SubX + elapsed, 666)`, then two
  `RNG_RangeB(2(r − 1))`) and do 18 (two `RNG_RangeB(2·Param3 + 1)` per gold drop on the missile seed). The rest draw
  nothing before their boundary call.
- **Emulation** (run:2026-10-20-cat-emu-9a, `tools/skills_catalogue_emu.py`): nine families, 13 functions,
  13 800 cases, 0 mismatches, 0 undeclared reads, 0 stops, every negative control failing (homing's weakest, 22).
  Claims by tag in skills/0004: `[C]` for do 2, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18 and the helpers `0x005A9720`,
  `0x005A9820` (up to the cell test), `0x00648AD0`, `0x006416D0` (missile units); do 7 raised in part (gates `[C]`,
  re-plan `[I]`); do 13 `[I]` (not emulated: `SkillSummonClass`'s read set).
- **Ruling asked (1): the `observe` boundary.** These functions end in calls that cannot be emulated with a declared
  read set (MissileCreate, PathPlan, spawns, item creation). A new script, `re/ghidra_scripts/EmuBoundary.java`
  (`EmuTrace.java` unchanged, copied, plus `observe <addr>`), ends a case at a declared callee's entry and prints its
  registers and stack arguments. I read ADR-0015 (1) and (3) as admitting this (no code patched; the claim is the map
  to the call's arguments and the bytes written before it, nothing after), like a harness breakpoint at the callee.
  Please rule whether it meets condition (1) as written or needs an ADR note; if not, the `[C]`s of §§ 3–11 fall to
  `[I]` except where a case returns.
- **Ruling asked (2): naming.** The plan names the output `skills/0003-catalogue.md`; 0003 is P1.3's handlers
  finding, so this batch is `skills/0004-missile-do-1-18.md` (as the lane prompt suggested). Later batches would
  follow as 0005… unless you prefer one file.
- **Symbols.** 23 rows, subsystem `skills/catalogue`; checked against `main` `48e2b26` (no clash: `UnitDistance` is
  `0x006417F0`'s, so `0x006416D0` is `sub_006416D0_UnitEdgeDistance`; the existing `sub_005AEDA0_MissileSpawnOwnedMonster`
  and the P1.2/P1.3 names kept).
- **Dated notes:** skills/0002 § 4 (do 2 raised, do 1 thunk) and § 8 (do 14 raised); quests/0001's open question on
  missiles 288 and 332 answered. No statement of a 0045 spec changes. Backlog: archivist (Missiles `Param*` meanings),
  spec-writer (quests/progression open question).
- **Tooling:** `tools/ghidra.sh emuboundary`, `tooling.md` § emuboundary.
