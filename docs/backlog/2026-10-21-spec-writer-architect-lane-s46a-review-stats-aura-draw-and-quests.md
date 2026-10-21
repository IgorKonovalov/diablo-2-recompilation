---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../specs/stats/README.md
  - ../specs/stats/states.md
  - ../specs/quests/progression.md
  - ../wiki/stats-and-states.md
  - ../wiki/how-we-know.md
  - ../wiki/quests.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

Not blocking. Please review `lane/s46a` (spec-writer, static docs only), which resolves two backlog entries:

1. **Sanctuary's draw, once per drawing run** ([archive](archive/2026-10-20-architect-spec-writer-stats-aura-draw-once-per-run.md)).
   [stats/README § Draw order](../specs/stats/README.md#draw-order): the `[C]` now states one `RNG_RangeB` per
   drawing run (865 runs, 865 steps; the run did not count units per run), and a new `[I]` paragraph gives once per run
   whatever the number of units hit, from skills/0011 § 3 and stats/0002 § 7's dated note. [states](../specs/stats/states.md):
   the § H table's aura row says "per drawing run" `[C]` and a new row carries the per-unit reading `[I]`; the H step
   note is reworded and a new `[I]` step note added; the reimplementation note now asks for one draw per run that
   draws `[C]`, "once per run, not once per unit hit" `[I]`; the unit-seed row of *Runtime state* says "run". No
   pseudocode or diagram showed a per-unit draw (F3 lists no draw). Wiki: stats-and-states (summary and "Sanctuary's
   draw", plus a "read from the code" bullet for once per run), how-we-know (near line 180).
   Tags: stats/overview I 2 → 3; stats/states I 47 → 50; C and L unchanged. The research map's stats/states row
   (`docs/specs/README.md`, "C 44 / I 47 / L 6", "a damaging aura's hit") is yours to update.
2. **Quests open question on missile do 17, 18, 36** ([archive](archive/2026-10-20-reverser-spec-writer-plan-0046-9a-quests-open-question.md)).
   [quests/progression](../specs/quests/progression.md) W4c: the "not read" clause narrowed; a `[C]` note for do 17
   and do 18 up to their boundary calls (skills/0004 §§ 7, 8, run:2026-10-20-cat-emu-9a under ADR-0021, nothing after a
   boundary covered) and an `[I]` note for their stock rows (288, 332); the open question struck and replaced by an
   `[L]` for do 36 (missile 625) only; Evidence lists skills/0004 and the run. Wiki quests: a paragraph in the word 4
   section and the *Unknown* list narrowed. Tags: quests/progression C 116 → 117, I 321 → 322, L 6 unchanged (the
   research map's row is yours).

Gate fast tier green before commit (0 errors; the 11 W1 warnings are data/excel.md's, not this lane's).
