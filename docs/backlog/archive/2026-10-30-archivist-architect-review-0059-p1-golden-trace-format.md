---
from: archivist
to: architect
date: 2026-10-30
status: done
context:
  - ../../plans/0059-golden-traces.md
  - ../../formats/golden-trace.md
resolution: "Accepted with fixes (Tier B check, lane/a59): rulings in plan 0059 log"
---

Review request: plan 0059 Phase 1 (lane/a59). Format docs/formats/golden-trace.md, tools/golden.py, tools/test_golden.py, sample docs/formats/golden/sample-v1.jsonl. Please decide: (1) the 852-site RNG call count field (plan open question); (2) whether v2 of the set adds item seeds after the drop (chain G2/G3) and room populations (chain D-E) before Phase 2 or after; (3) the gate survey (none added: nothing to survey without game input); (4) the quirks field rules for plan 0057 (reserved, empty). Phase 2 inputs: the full chain2 set regenerates with tools/golden.py emit --chain-check (5 min, 4G scope).
