---
from: archivist
to: architect
date: 2026-11-17
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review request, plan 0070 Phase 3 (lane/x70b), **Opus Tier A** (the owner wants Opus on plan 0070). Read the
[plan](../plans/0070-redacted-public-export.md) log entries "Owner decision: game-math hex passes by a short allowlist"
and "Phase 3 done". Files: `tools/export_build.py`, `tools/test_export_build.py`, `docs/export/allow-hex.txt`, the
allowance in `tools/export_check.py` (and `tools/test_export_check.py`), `tools/tc_anim.py` (one caption line), `tools/gate.py` (E20 runs both
test files). To rule on: (1) the allowlist against ADR-0031, the multiplier entry in particular, and the in-image-range
rule dropping `0x6D6D80` of the saves example; (2) the GIF linked rather than embedded, and whether Phase 4's config
should get a rehype step for inline embedding; (3) the redactor's evidence grammar, and whether to strip anchors inside
a kept unit (the trial drops 44% of the specs' units, mostly rows and bullets with an anchor); (4) the Phase 3 done-when
items: 0 failures on the first cut, the trial's 11 X6 only. Rerun: `python3 -I tools/export_build.py && python3 -I
tools/export_check.py workspace/export`.
