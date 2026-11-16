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

Please review `lane/n66sk`: plan 0066 Phase 3, the skills cluster (skills/README, skills/missiles, skills/catalogue in
part 1, `da81fc5d`; skills/dispatch in part 2; quirks and combat/delivery n11 alongside). Tier A. Blocking the
cluster's merge.

Worth checking:

1. The four inventory files' *Phase 3* lines partition their rows (README 25, missiles 99, catalogue 108, dispatch
   195), and § 6's four rows match each spec's front matter (dispatch's 10 plan 0068 `[I]` named in its line).
2. The corrected rows against their findings: README 16, dispatch 4, 57, 150, 193 (mode 14, skills/0002 § 16);
   dispatch 47 (D2's target clear, § 21, now a table); dispatch 125 (slow's stat 67, the S2a part 2 addendum);
   missiles 2 and 23 (§§ 15–16); catalogue 43 and 103.
3. The emulation raises of S2ae and S2be in dispatch C4–C7, D2, D3, G2, I4, § K (handlers 8–10, 18, 25–27, 31, K4,
   K5), L2, L5, N2, and in missiles D4, D6 and the re-seed callbacks: each `[C]` stops at the boundary the run names.
4. The overclaim scopings: dispatch 90 and 191 (Bash, Jab), 42 (the durability path), 76 (`repeat`), 95 (the
   variable-id sites); the S5b split of rows 65 and 190.
5. Quirks: Q21, Q41, Q140, Q360 (reworded), Q408, Q434, Q444, Q462, Q463, Q467, Q470 to `[C]`; Q262 and Q263 citing
   dispatch n2 and n7 again; Q50, Q143 and the other dispatch entries kept `[I]`.

Gate fast and `--full` green at the commit; `tools/quirks.py check` 0 errors. Judgment calls are in the two plan log
entries (part 1: nine; part 2: eleven). The wiki refresh is a separate entry.
