---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/hirelings/0001-hirelings.md
  - ../findings/ai/0007-hirelings.md
resolution: ""
---

[hirelings/0001](../findings/hirelings/0001-hirelings.md) still says `MERCAI_PickSkill` is "named only (ADR-0002)" / "Out of scope": the community-claim verdict "not covered" for the d2dfg-blizzard skill-choice formula (about line 159-161), the Functions row (about line 216, "named only") and the Combat skill choice bullet (about lines 582-584). [ai/0007](../findings/ai/0007-hirelings.md) § 2.4 now reads the formula [I] (0x005E4D30), so those three read stale. Please add a pointer to ai/0007 § 2.4 and re-verdict the d2dfg-blizzard claim (held [I], with the signed truncating /4, the mod (total+1) draw and the DefaultChance fallback). Found by the Tier B check (touched-findings pass), not blocking.
