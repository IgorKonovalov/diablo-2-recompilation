---
from: spec-writer
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../plans/0066-inventory/README.md
resolution: ""
---

Please review `lane/n66pf`: plan 0066 Phase 3, the frame / path / lifecycle / party cluster (sim/frame, path/README, path/search, drlg/lifecycle, player/party's S7a rows; drlg/collision E4 from the S7e refinements). Tier A. Blocking the cluster's merge.

Worth checking:

1. The five inventory files' new *Phase 3* lines partition their rows (frame 127, path-README 79, path-search 36, lifecycle 78, party 25 with row 12 the combat cluster's), and § 6's five rows match each spec's front matter.
2. The five corrected rows against their findings: frame 117 (Outputs, frame/0001 § 9), frame 33 (D6, frame/0007 S7b, still `[I]`), path/README 17 (`SizeY`, path/0001 § 16), lifecycle 2 (`RoomActivateB`'s fifth family, drlg/0009 § 12) and 12 (`ItemPlaceOnGround`'s callers, § 13).
3. The emulation raises from run:2026-11-16-sweep2-s7e: frame D9 (the null tail at frame −2 as the code's map, the fault `[I]`), E2a, E3a, E6, F3, I1's no-control return; path/README B4 and H3; lifecycle I1's gate tests and the monsters/spawn K1 mirror (review-fixes 8; spawn has no 0066 inventory file).
4. The overclaim splits the lane made against filed raises (judgment call 1 in the plan log): frame 37, 79, 85, 95, 99 and lifecycle 75.
5. Quirks: Q275, Q487, Q500, Q502, Q523, Q526 to `[C]`; Q500 citing sim/frame n8 alone, monsters/ai/README n1 a weaker duplicate until the monsters/ai cluster.

Gate fast and `--full` green at the commit; `tools/quirks.py check` 0 errors. Judgment calls are in the plan log entry.
