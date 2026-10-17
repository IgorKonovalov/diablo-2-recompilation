# Lane run ledger

**What it is for:** spotting slow or wasteful lanes and the review fixes that keep recurring, so that the
fixes turn into rules in each lane's `references/review-fixes.md`. It holds process data only (agent
usage, verdicts, fix counts), never game data.

**Keeping it current.** The orchestrator appends one row when it merges a lane (and one for its review),
with the usage figures the agent run reports. The architect fills the verdict and the fix count with
its categories in each review, using the categories below. A run whose usage is unknown gets no row.

## Runs

Seeded on 2026-10-17 from the agent usage of the lanes and reviews run 2026-10-16/17. Dates are the
lane's landing (or the review's) date in its plan log. Four runs with no lane name were dropped. A lane
row carries the verdict it received and the fixes its review applied; a review row carries the verdict it
gave, and holds the fixes only when its lane's row is not in the export.

| Date | Lane | Plan · phase | Kind | Agent tokens | Tool uses | Wall min | Slot / Ghidra | Verdict | Fixes |
|---|---|---|---|--:|--:|--:|---|---|---|
| 2026-10-16 | `lane/h37p2` review | 0037 P2 | architect-review | 121 914 | 49 | 10 | — | gave accept with fixes | 4: overclaim 1, miscount 1, omission 1, other 1 (lane row not in the export; fixes counted here) |
| 2026-10-16 | `lane/s4b` review | 0038 S4b | architect-review | 188 222 | 74 | 12 | — | gave accept with fixes | 5: miscount 3, stale cross-reference 1, omission 1 (lane row not in the export; fixes counted here) |
| 2026-10-16 | `lane/s1b` review | 0038 S1b | architect-review | 155 153 | 59 | 10 | — | gave accept with fixes | 2: omission 1, tool not kept 1 (lane row not in the export; fixes counted here) |
| 2026-10-16 | `lane/h4b` review | 0038 H4b | architect-review | 167 494 | 65 | 12 | — | gave accept with fixes | 5: overclaim 2, omission 1, stale cross-reference 1, other 1 (lane row not in the export; fixes counted here) |
| 2026-10-16 | `lane/p37s` | 0037 P3 | spec-writer | 320 892 | 104 | 26 | — | accept with fixes | 8: overclaim 2, under-claim 1, wrong anchor 1, omission 2, stale cross-reference 1, misread 1 |
| 2026-10-16 | `lane/s2c` | 0038 S2c | reverser-static | 647 883 | 213 | 52 | no slot | accept with fixes | 3: overclaim 1, miscount 1, stale cross-reference 1 |
| 2026-10-16 | `lane/s2c` review | 0038 S2c | architect-review | 184 467 | 73 | 11 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p37s` review | 0037 P3 | architect-review | 210 873 | 66 | 14 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p39a` | 0039 P0 | archivist | 229 994 | 105 | 18 | — | accept with fixes | 6: overclaim 2, miscount 1, misread 1, under-claim 1, stale cross-reference 1 |
| 2026-10-16 | `lane/p38s` | 0038 P3 round 1 | spec-writer | 262 957 | 74 | 19 | — | accept with fixes | 3: misread 1, overclaim 1, stale cross-reference 1 |
| 2026-10-16 | `lane/p39a` review | 0039 P0 | architect-review | 119 654 | 46 | 8 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p38s` review | 0038 P3 round 1 | architect-review | 157 104 | 54 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/wiki1` | 0038 P3 wiki | wiki | 114 645 | 28 | 6 | — | accept with fixes | 4: overclaim 1, bookkeeping splice 1, misread 1, stale cross-reference 1 |
| 2026-10-16 | `lane/s3b` | 0038 S3b | reverser-static | 407 300 | 193 | 35 | no slot | accept with fixes | 3: overclaim 1, miscount 1, other 1 |
| 2026-10-16 | `lane/wiki1` review | 0038 P3 wiki | architect-review | 102 723 | 28 | 6 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p41a` | 0041 P0 | archivist | 276 597 | 76 | 19 | — | accept with fixes | 5: misread 1, overclaim 2, omission 1, other 1 |
| 2026-10-16 | `lane/s3b` review | 0038 S3b | architect-review | 140 599 | 70 | 12 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p41a` review | 0041 P0 | architect-review | 120 597 | 32 | 9 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/p39r` | 0039 P1a | reverser-static | 481 581 | 260 | 55 | Ghidra (lane copy) | accept with fixes | 2: misread 1, omission 1 |
| 2026-10-16 | `lane/s1a` | 0038 S1a | reverser-static | 401 636 | 121 | 22 | no slot, no Ghidra | accept with fixes | 4: omission 1, misread 2, miscount 1 |
| 2026-10-16 | `lane/p42a` | 0042 P0 | archivist | 257 665 | 75 | 15 | — | accept with fixes | 5: misread 1, omission 2, under-claim 2 |
| 2026-10-16 | `lane/p39r` review | 0039 P1a | architect-review | 131 451 | 57 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/wiki2` | 0037 P4 | wiki | 179 646 | 37 | 10 | — | accept with fixes | 12: misread 6, overclaim 5, omission 1 |
| 2026-10-16 | `lane/p42a` review | 0042 P0 | architect-review | 108 767 | 43 | 8 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/s1a` review | 0038 S1a | architect-review | 137 679 | 58 | 8 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/h5e` | 0038 H5e | reverser-harness | 357 058 | 242 | 96 | slot 1 | accept with fixes | 4: overclaim 2, miscount 1, other 1 |
| 2026-10-16 | `lane/wiki2` review | 0037 P4 | architect-review | 171 261 | 26 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-16 | `lane/h5e` review | 0038 H5e | architect-review | 149 480 | 77 | 13 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p38s2` | 0038 P3 round 2 | spec-writer | 198 859 | 93 | 15 | — | accept with fixes | 1: misread 1 |
| 2026-10-17 | `lane/p43a` | 0043 P0 | archivist | 291 168 | 132 | 20 | — | accept with fixes | 5: under-claim 1, omission 2, misread 2 |
| 2026-10-17 | `lane/p38s2` review | 0038 P3 round 2 | architect-review | 115 818 | 34 | 5 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p43a` review | 0043 P0 | architect-review | 122 706 | 30 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/wiki3` | 0038 P3 round 2 wiki | wiki | 101 211 | 22 | 5 | — | accept with fixes | 3: misread 1, wrong anchor 1, overclaim 1 |
| 2026-10-17 | `lane/p40r` | 0040 P1/P1b | reverser-static | 391 179 | 129 | 29 | Ghidra (lane copy) | accept with fixes | 5: overclaim 1, misread 2, omission 2 |
| 2026-10-17 | `lane/h37r` | 0037 P2 resume | reverser-harness | 141 760 | 83 | 30 | slot 2 | accept with fixes | 5: misread 1, overclaim 1, wrong anchor 1, tool not kept 1, omission 1 (second batch only; the first batch's row is not in the export) |
| 2026-10-17 | `lane/wiki3` review | 0038 P3 round 2 wiki | architect-review | 75 294 | 30 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p40r` review | 0040 P1/P1b | architect-review | 136 893 | 66 | 11 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/h5a` | 0038 H5a | reverser-harness | 325 139 | 139 | 41 | slot 1 | accept with fixes | 2: miscount 1, stale cross-reference 1 |
| 2026-10-17 | `lane/h37r` review | 0037 P2 resume | architect-review | 173 486 | 79 | 13 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/h5a` review | 0038 H5a | architect-review | 166 915 | 72 | 9 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p37t` | 0037 P3 re-tag + P4 | spec-writer | 125 960 | 45 | 12 | — | accept with fixes | 4: overclaim 2, misread 1, other 1 |
| 2026-10-17 | `lane/p37t` review | 0037 P3 re-tag + P4 | architect-review | 125 811 | 48 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p38s3` | 0038 P3 round 3 | spec-writer | 326 440 | 63 | 18 | — | accept with fixes | 3: overclaim 1, misread 1, other 1 |
| 2026-10-17 | `lane/p39b` | 0039 P1b | reverser-static | 528 258 | 303 | 44 | Ghidra (lane copy) | accept with fixes | 5: miscount 1, omission 1, overclaim 1, misread 1, other 1 |
| 2026-10-17 | `lane/p38s3` review | 0038 P3 round 3 | architect-review | 202 892 | 56 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/s1e` | 0038 S1e | reverser-static | 600 587 | 209 | 78 | Ghidra (lane copy) | accept with fixes | 6: tool not kept 1, overclaim 3, omission 1, misread 1 |
| 2026-10-17 | `lane/p39b` review | 0039 P1b | architect-review | 155 600 | 62 | 9 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/arc4` | 0039 follow-ups | archivist | 160 062 | 92 | 18 | — | accept with fixes | 2: stale cross-reference 1, misread 1 |
| 2026-10-17 | `lane/wiki4` | 0038 P3 round 3 wiki | wiki | 157 890 | 38 | 7 | — | accept with fixes | 3: misread 1, overclaim 1, omission 1 |
| 2026-10-17 | `lane/wiki4` review | 0038 P3 round 3 wiki | architect-review | 95 552 | 22 | 5 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/arc4` review | 0039 follow-ups | architect-review | 117 992 | 53 | 6 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/s1e` review | 0038 S1e | architect-review | 206 902 | 110 | 16 | Ghidra (lane copy, re-run) | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p41r` | 0041 P1/P1b | reverser-static | 441 644 | 157 | 32 | Ghidra (lane copy) | accept with fixes | 7: symbol clash 1, omission 3, wrong anchor 1, misread 2 |
| 2026-10-17 | `lane/p39s` | 0039 P2 | spec-writer | 278 695 | 142 | 23 | — | accept with fixes | 3: bookkeeping splice 1, omission 2 |
| 2026-10-17 | `lane/w1` | 0039 W1 anchors | reverser-static | 192 321 | 69 | 14 | no Ghidra | accept | 0 |
| 2026-10-17 | `lane/w1` review | 0039 W1 anchors | architect-review | 97 729 | 30 | 4 | — | gave accept | — (on the lane row) |
| 2026-10-17 | `lane/p39s` review | 0039 P2 | architect-review | 167 318 | 61 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p41r` review | 0041 P1/P1b | architect-review | 188 450 | 73 | 11 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/wiki5` | 0039 W4 wiki + rng W1 | wiki | 215 486 | 79 | 13 | — | accept with fixes | 6: misread 2, overclaim 1, omission 1, stale cross-reference 1, miscount 1 |
| 2026-10-17 | `lane/wiki5` review | 0039 W4 wiki + rng W1 | architect-review | 131 478 | 55 | 7 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p39c` | 0039 P1c | reverser-static | 481 832 | 234 | 36 | Ghidra (lane copy) | accept with fixes | 5: miscount 1, overclaim 1, symbol clash 1, wrong anchor 1, omission 1 |
| 2026-10-17 | `lane/p39c` review | 0039 P1c | architect-review | 160 398 | 67 | 12 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/loop` | improvement loop (ledger, review-fixes, ADR-0018) | architect | 207 597 | 43 | 10 | — | merged on owner request, no review | — |
| 2026-10-17 | `lane/s1f` | 0038 S1f | reverser-static | 476 395 | 157 | 53 | Ghidra (lane copy) | accept with fixes | 3: omission 2, stale cross-reference 1 |
| 2026-10-17 | `lane/s1f` review | 0038 S1f | architect-review | 198 740 | 91 | 14 | Ghidra (lane copy) | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p39s2` | 0039 P2 round 2 | spec-writer | 201 174 | 81 | 19 | — | accept with fixes | 4: misread 1, miscount 1, stale cross-reference 2 |
| 2026-10-17 | `lane/p39s2` review | 0039 P2 round 2 | architect-review | 157 435 | 44 | 6 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p38s4` | 0038 P3 round 4 | spec-writer | 243 273 | 74 | 17 | — | accept with fixes | 2: overclaim 2 (drlg/preset L154 done at the review) |
| 2026-10-17 | `lane/p38s4` review | 0038 P3 round 4 | architect-review | 153 056 | 55 | 9 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p42r` | 0042 P1/P1b | reverser-static | 551 952 | 191 | 45 | Ghidra (lane copy) | accept with fixes | 7: overclaim 3, misread 2, miscount 1, symbol clash 1 (2 commits; usage unknown) |
| 2026-10-17 | `lane/p42r` review | 0042 P1/P1b | architect-review | 224 353 | 113 | 23 | — | gave accept with fixes | — (on the lane row) |
| 2026-10-17 | `lane/p43r` | 0043 P1/P1b | reverser-static | 429 692 | 202 | 38 | Ghidra (lane copy) | accept with fixes | 5: overclaim 2, omission 2, miscount 1 |
| 2026-10-17 | `lane/p43r` review | 0043 P1/P1b | architect-review | 192 590 | 65 | 13 | — | gave accept with fixes | — (on the lane row) |

**Totals over the seed (61 rows, 32 reviews):** 135 fixes. overclaim 32, misread 32,
omission 26, miscount 12, stale cross-reference 10, other 8, under-claim 5, wrong anchor 4, tool not
kept 3, bookkeeping splice 2, symbol clash 1, scope creep 0. Overclaim and misread tie; with under-claim,
fixes to a tag's strength (37) are the largest family. Every review but one (`lane/w1`) asked for fixes;
none rejected.

**By kind** (runs, mean agent tokens, mean wall minutes, fixes per reviewed run): reverser-static 10,
457 k, 40 min, 3.9; reverser-harness 3, 275 k, 56 min, 3.7; spec-writer 6, 252 k, 19 min, 3.7; archivist
5, 243 k, 18 min, 4.6; wiki 5, 154 k, 8 min, 5.6; architect-review 32, 145 k, 9 min.

## Fix categories

Each fix is counted once, in the first category that fits, in this order.

| Category | Definition |
|---|---|
| overclaim | A tag or wording stronger than the evidence: a code reading worded or tagged as confirmed, a "never"/"every" that the run cannot separate from an alternative, a meaning the code does not give, a `[C]` covering a remainder no case reached. |
| under-claim | A tag weaker than evidence the repository already holds: an `[L]` where a finding states `[I]` with addresses, a raise the accepted ledger allows but the text left out. |
| misread | A statement the code, data or spec contradicts: a wrong branch outcome, condition, order, label or consequence. |
| miscount | A count not recounted: item totals, writer or call-site counts, totals taken against a stale baseline, numbers in a commit subject or primitive list. |
| omission | Something the reading reached or the request asked for that the text left out: a path, a case, a citation, a request item. |
| wrong anchor | An address, `fn:`, section or link that does not point at what the sentence claims, or a conclusion with no anchor where the gate needs one. |
| stale cross-reference | Text copied from, or left behind by, another doc that has since moved: a struck open question still open, a status, a superseded reading. |
| symbol clash | Two lanes name one address differently, or one name is used for two addresses. |
| bookkeeping splice | A merge or edit splices new text into old punctuation or structure: research-map rows, bullets run together, lost table headers. |
| tool not kept | A claim rests on a scratch script, an unhashed output, an unseeded generator or a log outside `workspace/logs/`. |
| scope creep | Work outside the lane's phase or ownership. None in the seed. |
| other | Labels, wording or conventions that change no claim (for example a remainder called "moved" with no destination plan, timing in seconds instead of frames). |

## How to read it

- Compare rows of one kind only: a harness run's wall minutes include game sessions, and a static batch's
  tokens scale with its statement count (see the plan's batch table).
- A lane is slow or wasteful when its tokens or minutes sit well above its kind's mean without a larger
  batch to explain them, or when its review needed many fixes of one category.
- A category that recurs across rows of one kind is a candidate for that lane's `review-fixes.md`; the
  architect promotes any fix seen twice (architect skill).
- Fix counts are the reviewer's classification, not a measure of the lane's quality: a review that reads
  more finds more. Read them as a trend over many rows.
