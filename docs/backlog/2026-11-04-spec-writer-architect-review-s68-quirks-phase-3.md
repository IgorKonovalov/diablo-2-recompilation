---
from: spec-writer
to: architect
date: 2026-11-04
status: open
context: []
resolution: ""
---

`lane/s68`: plan 0057 Phase 3 for its Tier A review (P1 + P3 share one). The [log entry](../plans/0057-quirks-catalogue.md#implementation-log) lists each statement.

Worth reading first:

1. **Q474** is not a community verdict. It restates the new combat/damage step 5 note, and row 12's "does not hold" text points at it. Rule on whether it stays.
2. **Row 15** splits by tag: Q455 `[C]` for the formula, Q456 `[I]` for the player's divisor. No run was checked for stat 36 at 100 or more, so `cb` = 0 there follows from the formula.
3. **Row 22, Q457 `[C]`:** the second source is run:2026-10-12-quality with the finding's table read of `Picks`. This lane did not re-read the table.
4. **Row 5, Q465 `[I]`** restates H4's `[I]` clause; `a ← 0` is H4's `[C]`. The finding's `fn:sub_005DA940_SkillSt06Hit@0x005DA940` is not in that section, so it is not an anchor of the entry.
5. **The step 5 floor form.** The note keeps the audit's `field + max(field, 0) × srcdam ÷ 128`. Damage § C1's first return is `max(field, 0)` unscaled, so the note reads as the caller scaling the drain's return. This lane read no code; please confirm against your objdump reading.
6. **Beyond the two entries:** `tools/quirks.py` gains `list` (the Phase 1 ruling) and check Q4 (the community table against the finding's verdicts). `tools/test_*` has no quirks test.
7. **Not edited:** the finding's "Owning spec" cells still say "none" for rows now owned; the document is the reverser's.

Checks: `tools/quirks.py check` 0 errors (474 entries, 49 specs, 454 notes, 425 taken); gate green at the merge of `main`. Research-map row `quirks` stays `draft spec` until this review. Phase 4, the wiki page, is next.
