---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/save/experiments.md#run2026-10-27-sweep-d2s-load
resolution: "lane/h1a review 2026-10-27: accept with fixes (5). Ledger as filed (raised 32, in part 4, shortfall 8, d-none 2: 46); player-creation 20/34 d-none with a null-unit reach condition; the swap ruled a stock-path observation of the server's reader with a single-player reach note; the 139 gf and 50 ladder halves d-none; legacy rows shortfalls; data-calc 19 raised (S1b). Totals static 567, harness 519, blocked 421 (d-none 295), 1 526. Spec-writer entry released; save/d2s and items/uniques-sets ready for Phase 3. See the plan 0038 log."
---

Review lane/h1a, plan 0038 batch H1a (d2s-load), run:2026-10-27-sweep-d2s-load, harness slot 2. 46 statements: raised 32, raised in part 4, shortfall 8, proposed d-none 2 (player-creation 20, 34: no class-7 player is ever made; both class-7 loads halt at line 1210, crash reports kept). Halves proposed d-none: save-d2s 139's gf half (no stock CSvParam), 50's ladder test (host callback only). Method to check: tool-built saves swapped in after the character screen read its list (tools/h1a_sessions.py; the client's list filter 0x0043C8A0 would refuse bad magic, short files and version 97). Check: systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_h1a.py check workspace/merged/data/global/excel workspace/runtime/h1a $(ls workspace/logs/h1a/h1a-s2-2720*.log) -> 410 comparisons over 38 cases, 0 failing; byte-compare with workspace/logs/h1a/check/sweep-h1a-check.txt; sha256sum -c h1a-manifest.sha256 and h1a-manifest-dev.sha256 from workspace/logs/h1a. tools/d2sio.py changed (file-only code model 4/6/5/7, the error-map table, context=, UNPARSED, UNTERMINATED): the H1b logs re-check byte-identical once ' context=None' is dropped (check/sweep-h1b-recheck-h1a.txt) and the 2026-10-12 logs keep main's totals. S1b piece run (data-calc 19 hover half met, rng-seeds 11 one caller more; rows stay S1b). Symbols: ten readers I -> C (rule 14), four added (I). Archivist entry for the legacy layouts and d2s.py gaps; spec-writer entry held for this review.
