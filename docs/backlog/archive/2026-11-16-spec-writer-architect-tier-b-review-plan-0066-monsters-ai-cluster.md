---
from: spec-writer
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
resolution: "Architect Tier B review (Sonnet, by owner budget): accept, no fixes."
---

Plan 0066 Phase 3, the monsters/ai cluster part 1 (`lane/n66ai`): monsters/ai/README and monsters/ai/machinery
re-tagged on batches S1m, S1ne and S1o, with their corrections; quirks Q480, Q491, Q518 raised and Q500 citing README n1.
Requested: a **Tier B review, on Sonnet only**, by the owner's budget decision for this lane (the plan's Phase 3 calls
for Tier A per cluster; the owner chose Tier B here). Check: each inventory file's *Phase 3* line partitions its rows
(README 56: 14 / 20 / 1 / 21; machinery 114: 30 / 29 / 3 / 52), each raised statement against its Route cell and
anchor, the judgment calls in the plan log entry, and the spec-writer review-fixes (1, 2, 8, 10 above all). The
catalogue is part 2 (resume note in the plan log). Blocking the merge of `lane/n66ai`.

## Architect review (Tier B, Sonnet, 2026-11-16)

Verdict: **accept**. Sonnet and Tier B by the owner's budget decision (the plan's Phase 3 calls for Tier A per cluster); the
cluster's Tier A is not claimed here.

- Gate GREEN (0 errors); `quirks.py check` 0 errors. Front-matter tags equal the body counts by grep: README C 78 / I 45 / L 10,
  machinery C 87 / I 85 / L 4, quirks C 414 / I 133 / L 3.
- Script: each inventory Phase 3 line partitions its rows exactly once (README 14 / 20 / 1 / 21 = 56; machinery 30 / 29 / 3 / 52
  = 114; no duplicate, gap or extra).
- Sampled: the four corrected rows (README 20, machinery 46, 54, 82) match their corrections entries in the spec text (C4's
  `n` 0 to 1 and unsigned test; `AiParamsFind` head examined last; the two `UModTeleportTry` draws; T30a's writer), with
  the static ones kept `[I]`; C4, E4's find scan, Q480, Q491 and Q518 cite runs that exist in docs/findings/ai/experiments.md
  and say what the claim says.
- Judgment calls: (1) inline `[C] ...; [I] ...` headers: accept, as sim/frame B1. (2) H1n rows 48 and 43 counted split: accept.
  (3) corrected counts only on "correction"/"contradicted" Route cells: accept, as the earlier clusters. (4) 54 and 82 stay
  `[I]` as static readings: accept. (5) E5 whole with an `[I]` pointer, E8a, C2a/C2b bullets: accept. (6) S1m correction 2 as an
  `[I]` Open questions line: accept. (7) Scarab row added to H1's table on S1m's census: accept.
- Not checked (Tier B scope): anchors beyond the sampled ones, and the W4 wiki warnings (80, the refresh entry exists).
