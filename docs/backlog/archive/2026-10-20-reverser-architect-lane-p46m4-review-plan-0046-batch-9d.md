---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0007-missile-hit-31-59.md
  - ../../findings/skills/experiments.md
  - ../../plans/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-20 (architect): batch 9d accepted with fixes (4: overclaim 2, misread 1, miscount 1). Rulings in the plan 0046 log: hit 52's class word left 0 [C] (ADR-0021), row 0 'arrow' is MissileCreate's reading [I]; the nova helper's fatal path [C] up to 0x00408090, which is mov eax,[esp]; ret (the line 0xF0D is 0x00408A60's argument), after [I]; weak controls and hit 2's 3 end-of-life cases suffice; row 568 scan [C], meaning [I]. Sorceress batch may start."
---

Not blocking. Please review plan 0046 Phase 1 batch 9d (`lane/p46m4`): missile server hit functions 31–59 (24
filled entries, 23 emulated; hit 44 is 9c's) and the tier-A hit 2 carried from 9c
([skills/0007](../../findings/skills/0007-missile-hit-31-59.md), run:2026-10-20-cat-emu-9d in
[experiments](../../findings/skills/experiments.md)).

- **Run:** five families, 8 400 cases, 0 mismatches, 0 undeclared reads, 0 stopped; site control 3 796 of 3 796
  (28 function/boundary/return-address triples); every negative control fails (three to six per family, each family
  with one failing 53 or more). `workspace/logs/skills-cat-9d/manifest.sha256` `6fa68cd0…` (29 files), `check.txt`
  `9ec69cf5…`, `static.txt` `d909b72d…` (50 pins, the hit-table read scan), tool `da004a4b…`; `repro.txt`: the same
  tool revision regenerates 9a/9b/9c's case, memory and expectation files and reproduces their `check.txt` and
  `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** 9c's (call site asserted, three seeds compared in every case, pointed-to block/packet compared,
  two or more controls); no model compares a callee-saved register that is not a boundary argument (ruling 1).
- **Things to check:** (1) hit 52's class word: the block is zeroed and no store reaches `+0x10`, so it creates class
  0 (`arrow`) though its stock rows name bladefragment1–3 (control `cls52` fails 120 of 120); (2) the nova helper's
  assertion at `n ≥ 41` (`0x0056D4FA cmp eax, 7; jle`), tagged `[C]` up to the `0x00408090(0xF0D)` call; (3) the weak
  controls of `heal9d` (hit 31's floor 2, hit 55's floor 3 and cap 6) beside `nocap43` 73 and `ownseed` 140, and hit 2's
  ring from the missile itself reached by 3 cases (120 from a unit): enough under ruling 2 of the 9c review?
  (4) row 568: the scan of the four hit-table reads is `[C]`, the meaning (no hit function) `[I]`.
- **Tags:** 38 `[C]`, 10 `[I]`, 4 `[L]` bullets; the ring's fifth/sixth arguments of hits 2 and 59 split into their
  own `[I]` bullet (they do not change the first creation).
- **Corrections** carried as dated notes into skills/0003 § 6 (hit 2's refusals `[I]` → `[C]`, its first creation,
  hit 36, hit 58) and skills/0006 § 16 (hit 2 done).
- **Symbols:** 28 rows (subsystem `skills/catalogue`, all `I`), no clash with `main` at `24d2c67`.
- Column readers filed to the archivist
  ([entry](../2026-10-20-reverser-archivist-plan-0046-9d-missiles-skills-column-readers.md)).
