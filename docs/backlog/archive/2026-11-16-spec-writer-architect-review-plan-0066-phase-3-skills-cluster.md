---
from: spec-writer
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
resolution: "Accepted (Sonnet review by budget decision); verdict in the entry"
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

## Verdict (architect, 2026-11-16): accept

Downgraded from Tier A to a Sonnet review by the owner's budget decision; checked by script and sampling, not a full read.

- Gate fast green (0 errors; the one W7 warning, quirks 792 `Total` 487 against 489, is in a table this branch did not touch);
  `tools/quirks.py check` 0 errors (538 checked).
- Front matter counts of skills/README (36/22/1), missiles (125/60/6), catalogue (290/94/7), dispatch (204/173/10) match
  the body tag counts by grep; quirks C 422 / I 125 / L 3 matches too.
- The four *Phase 3* lines partition their rows exactly once (script: 25, 99, 108; dispatch 189 listed plus the six
  corrected rows 4, 47, 57, 125, 150, 193 = 195); the bucket counts match each list; § 6 rows sum to the lines (dispatch 48+74+6+67).
- Six samples hold: dispatch row 150 and Q-mode-14 text (static `MonModeStartSeq` 0x005A7884 plus logs, skills/0002 § 16);
  dispatch row 125 stat 67 (S2a part 2 addendum, 246 of 246); dispatch row 130 `h26w` (run:2026-11-16-sweep2-s2ae7/8
  exist in experiments.md, § 23-24); missiles row 23 (33 sites, six bodies, matches § 15-16); missiles Q21 (static plus
  the 684-row data check); README row 16 (corrected, ammunition left `[I]`). Every sampled run id resolves.
- Judgment calls, ruled consistent with the cluster-pattern ruling (a)-(d) and the anim, combat, stats and items
  precedents: part 1 (1)-(9) accepted as written (header bullets keep `[I]` with a `[C]` bullet; corrected rows with a
  `[C]` statement count corrected; 77, README 25 and catalogue 108 whole with one new `[I]` pointer so Q143 and Q50 keep
  their tag per note; 29, 69, 81, 82 split; 91's cell marks stay `[I]`). Part 2 (eleven calls) sampled: the plan 0068
  10 `[I]` named in the line, rows 65 and 190 split on S5b, and the overclaim scopings (90, 191, 42, 76, 95) accepted;
  not each re-read.
- Not checked (budget): the 11 Q-tag raises beyond Q21, and the remaining S2ae/S2be raises (C4-C7, D2, I4, § K, L2,
  L5, N2); the promotion re-check was by the sampled spot checks only.
