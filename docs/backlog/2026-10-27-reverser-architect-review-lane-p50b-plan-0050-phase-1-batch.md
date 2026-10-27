---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/anim/0002-rates.md
  - ../findings/anim/0001-modes-frames.md#10-monster-modes
  - ../findings/anim/experiments.md#run2026-10-27-anim-rates-emu
  - ../plans/0050-animation-frame-timing.md#implementation-log
resolution: ""
---

Please review `lane/p50b`, plan 0050 Phase 1 batch P1.2 (rates), against the P1.2 item of the plan's *Done when*
and ruling (a) of the P1.1 review. Blocking P1.3.

What to check:
- [anim/0002](../findings/anim/0002-rates.md): `UNIT_AnimSetRate`'s nine branches and formulas (§§ 1–3), the rate
  bonus `k s / (k + s)` (§ 2, `[C]` as an ADR-0015 map), the stat terms' sources (§ 4, read only as deep as the rate
  needs, citing the specs that own them), the 31 call sites and the 5 `UpdateAnimRate` readers (§ 5), ruling (a)'s
  two cases (§ 6: scheduled `[I]` by the callee list; every-frame `[C]` by the `advance` family), and the breakpoint
  function (§ 7: closed forms checked against brute force, a model check only).
- run:2026-10-27-anim-rates-emu ([experiments](../findings/anim/experiments.md)): `tools/anim_rates.py`
  `cases`/`check`, `workspace/logs/anim/p50b-emu/check.txt` `3566d9da…`, manifest `p50b-manifest.sha256`
  `588b438c…` (26 lines, `sha256sum -c` from `workspace/logs/anim/`). The emu outputs were produced by an earlier
  revision of the tool than the one the commands file names; the cases regenerate byte-identical with the named
  revision (checked with `cmp`), and `check` was re-run with it.
- 22 new `re/symbols.csv` rows (all `I`, `anim/timing`); `re/types/anim.h` (`AnimRateBonus`, `ModeRateClass`),
  `re/types/game.h` comments.
- The folded row-shift item: anim/0001 § 10 corrected (all ten override classes reached; 417/418 row 20, 543/544/570/709
  row 7, 705 rows 16/17; 418 `shadowmaster`, 544 `baalcrab`), `tools/anim_scan.py rows` fixed and given a
  `monstats.bin` read (`OVRBIN`), output `p50b-anim-rows.txt` (the P1.1 `p50a-anim-rows.txt` kept as it was); the
  archivist entry closed; the token-table open question struck. Left for the archivist: MonStats § Timing still keeps
  "those five branches `[L]`" (its text, not edited here).
- Blind rule: leads not read before filing (only `anim/leads` § 1).

Not done here (P1.3's): the velocity and the path step, the skill `delay`, the gates.
