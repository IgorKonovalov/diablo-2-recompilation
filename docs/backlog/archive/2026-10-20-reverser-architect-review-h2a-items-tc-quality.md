---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20
  - ../../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20
  - ../../findings/items/experiments.md#run2026-10-20-sweep-items-tc
resolution: "Accepted with fixes at the lane/h2a review (architect, 2026-10-20): checkers re-run on the kept logs (manifest passes; tc.py 873/873, quality.py 720/720 and the clamp counterfactuals as filed, uniques.py 1022/1022); row count 15 rows / 17 statements, 12 raised and 5 in part, stands; tc 34 decided by the missing SEL line (0x0055AB35 joins every scan exit, so a reading without the stop logs one); the clamp correction carried; the tool additions accepted; the 5 hireling rolls of the aborted H6d log count. Fix: the spec-writer entry gains the two open questions and the wiki lines the corrections contradict; entry released. Rulings in the plan 0038 log."
---

Review plan 0038 batch H2a (items: tc and quality, `lane/h2a`, `main` `5a7feb3` merged), run:2026-10-20-sweep-items-tc. 12 scripted sessions on slot 2 (the harness part ran before the pause; the write-up is static, no slot used). Checks, all 0 mismatches: `sweep_h2a.py logs` 0 bad, `tc.py replay` 873/873, `quality.py check` 720/720, `uniques.py check` 1022/1022, `test_sweep_h2a.py` 9 OK. Manifest `workspace/logs/h2a/items-tc-manifest.sha256` (12 logs, `sha256sum -c` from `workspace/logs/h2a`); every check output in `workspace/logs/h2a/check/`, cited by sha256 in the run record and its 2026-10-20 addendum.

Ledger of the 15 rows (17 statements): **raised 12** (tc 1, 2, 11, 34 L361, 37, 45, 47, 59, 71; quality 22 ×2, 23); **raised in part 5** (tc 22: `bonewall` fatal unreached; tc 34 L388: `Picks = 0` d-none as row 13; tc 60: one `mul=` product, the equivalence half d-none, signedness `[I]`; tc 70: game types 2 and 3 only; quality 20: owner-carrying monster killers only); **shortfall 0**.

Points for the ruling:
- (a) **Row count.** The lane's resume note proposed tc 34 "raised" for both statements and counted "13 raised, 4 in part of 17 rows (18 statements)". The batch is 15 rows, 17 statements (§ 5); L388 carries the `Picks = 0` half, so it is filed raised in part (rule 8), giving 12 + 5.
- (b) **tc 34 discriminates by a missing line.** With `Picks` −2 and classic total 1 the stop falls on the frame's last pick, so the frame ends either way; what separates the stop is that `NEG roll=1 total=1` goes to `TCEND` with no `SEL` (0x0055AB35), while each of the 62 other negative picks is followed by `SEL`.
- (c) **Correction (rule 12):** items/0002's Answer line, § 4, § 7, the open question and the header said the D6 clamp "never acted"; it acts in 667 rolls (39 H2a + 628 S2a set: affixes 479, uniques 66, props 43, items-chain 40), never in the plan 0010 runs. The S2a review did not have this split; `check-clamp-s2a-perlog.txt` gives it.
- (d) **Tool additions after the run** (additions only): `quality.py` key `{"clamp": "before-mf"}` and `sweep_h2a.py` `goldtypes`; quality 23's "magic find before the minimum" stands on the new counterfactual (D6 before D5 breaks 138 rolls). The game's roll is unchanged (`check-quality-r2.txt` = `check-quality.txt`).
- (e) **quality 20's hireling rolls:** 5 of its 39 are in an aborted H6d log under `workspace/logs/h6d/failed/`, which is in the H6d run list; the raise does not depend on them (34 + 6 + 85 remain).
- (f) **Symbols** `MonDeathEvent`, `MonDeathDrop`, `MonDropNoNoDrop`, `CorpseFindItem`, `DropGoldFind` I → C on the logged entries and return addresses plus `sweep_h2a.py static`.

Not blocking. Spec-writer entry filed: `2026-10-20-reverser-spec-writer-h2a-items-tc-quality-spec-updates.md` (to be released with the review).
