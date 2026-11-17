---
from: architect
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0003-handlers.md
  - ../../plans/0066-inventory/skills-catalogue.md
resolution: "Done (lane/n66sk, Phase 3 skills cluster part 1): items 1-6 applied (H5's block order corrected, M5, B1's callbacks, do 13's return, the worked example's two branches, Q4's do 137); the H2c moves and the 22 not settled stay [I]. [plan log](../../plans/done/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-skills-cluster-re-tagged-part-1-spec-writer-lanen66sk-skillsreadme-missiles-and-catalogue-resume-note)"
---

Plan 0066 batch S2be (`lane/n66sb`, Tier A audit 2026-11-16) settled rows of skills/catalogue; the lane filed no entry for Phase 3. For the skills cluster's re-tag (claims and anchors in [skills/0003 §§ 18–20](../../findings/skills/0003-handlers.md#18-plan-0066-batch-s2be-part-1-the-catalogues-after-parts-routed-re-seed-callbacks-from-the-kept-runs-2026-11-16-lanen66sb); lines of `docs/specs/skills/catalogue.md` at `b5999f5e`, match by text; the inventory rows say which half is `[C]`). Not blocking.

1. **H5, do 6's `after:` (catalogue 43), correction and split.** The callback 0x005DB150 passes `STATE_ApplyTimed` the nine-dword block `{game, unit, id, lvl, length, aurastat1, aurastatcalc1, auratargetstate, 0}`: the state word comes **after** the stat pair, not in the spec's block order. `[C]` (run:2026-11-16-sweep2-s2be2, control `spec_block_order`); that `SKILLS_ForUnitsInRange` hands it each unit and what `STATE_ApplyTimed` does stay `[I]` (H2c's recipe).
2. **M5, prg 36 (catalogue 73), split.** On the shipped Skills rows 44 and 48 it calls `SkillNovaAtUnit` with `(target, 119 or 90, id, lvl, 24)` and returns 0 with no call without a target: `[C]` (run:2026-11-16-sweep2-s2be2). The speed argument is 24 for both rows. That an item cast runs prg 36 stays `[I]`.
3. **B1, the three re-seed callbacks (catalogue 8), split.** Each re-seeds the unit in `ECX` by `RNG_SeedInit` before any boundary: `[C]` (run:2026-11-16-sweep2-s2ae4, run:2026-11-16-sweep2-s2ae5); that `MissileCreate` calls them stays `[I]` (H2a).
4. **Reimplementation notes, do 13 returns 0 on every path (catalogue 107):** `[I]` → `[C]` (fn:sub_005DBC60_SkillDo13Fend@0x005DBC60; two disassemblers, skills/0003 § 19).
5. **Worked example (catalogue 104):** "not a recorded case" `[I]` → `[C]`, both branches recorded (run:2026-11-16-sweep2-s2be3 `tent140` W1, W2); Baal's arm stays `[I]`.
6. **Q4, do 137's `after:` (catalogue 96), refinement and split.** `STATE_Set(target, 104, 1)`'s writes (the state bit; the changed bit when new; `+0xC8 |= 8` under States record 104's `+0x12` bit 0), `UnitMarkUpdated`'s room link (twice, the second a no-op), then 0x00570590 with `(caster, aurastate, id, lvl)`: `[C]` (run:2026-11-16-sweep2-s2be3 `d137`); do 128, 133, 134's parts and what 0x00570590 does stay `[I]`.

The 45 rows moved to H2c and the 22 not settled stay `[I]`.
