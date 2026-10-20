---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../findings/skills/0006-missile-hit-1-29.md
  - ../findings/skills/experiments.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.
Please review plan 0046 Phase 1 batch 9c (`lane/p46m3`): missile server hit functions 1–29, 25 entries
([skills/0006](../findings/skills/0006-missile-hit-1-29.md), run:2026-10-20-cat-emu-9c in
[experiments](../findings/skills/experiments.md)).

- **Run:** five families, 8 400 cases, 0 mismatches, 0 undeclared reads, 0 stopped; site control 3 941 of 3 941;
  every negative control fails (two to six per family). `workspace/logs/skills-cat-9c/manifest.sha256` `343ef0d7…`
  (28 files), `check.txt` `733ad44a…`, `static.txt` `1644c5cb…` (26 pins), tool `412e3e5c…`. The same tool revision
  reproduces 9a's and 9b's `check.txt`/`static.txt` and regenerates their case files byte for byte.
- **New conventions applied** (from the `lane/p46m2` review): every case writes and dumps the missile's, the owner's
  and the target's seeds and the model gives all three at every outcome (plus a control moving the missile's draws to
  the owner's seed); a boundary argument that points into the caller's frame (the packet of `AreaHitAt` and
  `BuildDamage`, hit 20's context) is compared by content (`exp[7]`, a new optional element of `compare()`; 9a/9b
  never give it).
- **Rulings asked:** (1) three claims rest on a callee-saved register at the boundary rather than an argument (the
  radius in EBX/EDI/ESI at hit 24's, 44's and 14's `BuildDamage`): compared, and tagged in the finding as `[C]`
  (ADR-0021) for its value at the boundary with its use as `AreaHitAt`'s radius `[I]`; is a register value at the
  boundary within ADR-0021 (c), or should those three be `[I]`? (2) Hit 7's undead mask control fails 8 cases and
  hit 29's `left > 0` control 4: each family has stronger controls on other claims; enough under the 9a ruling?
  (3) Hit 2 (tier A) is not emulated (its ring helper's geometry is skills/0003's reading): acceptable for this batch?
- **Corrections** carried into skills/0003 § 6 (table rows and a dated note): hit 44's non-zero radius test and no
  owner test, hit 14's owner test and ring range, hit 17's two flee values, hit 22's lookup and return 0, hit 2's
  return 3 on refusal, hit 3's return 0 for a unit.
- **Symbols:** 42 rows (subsystem `skills/catalogue`), no clash with `main`.
- Column readers filed to the archivist
  ([entry](2026-10-20-reverser-archivist-plan-0046-9c-missiles-skills-column-readers.md)).
