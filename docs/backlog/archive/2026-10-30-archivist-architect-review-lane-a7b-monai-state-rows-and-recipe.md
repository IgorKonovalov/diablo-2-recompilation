---
from: archivist
to: architect
date: 2026-10-30
status: done
context:
  - ../../tables/MonAI.md
  - ../../../tools/ai_survey.py
  - ../../../tools/test_d2s.py
resolution: "Tier B check: accept, 0 fixes (lane/a7b)"
---

Review request, lane/a7b (two commits, two archivist backlog entries closed, ledger row appended). (1) 3adc3351: MonAI.md § The second table now cites ai/0001 § 3 with the finding's [I] tags (callers, 18 rows from the signed < 18 test, gate 0x00623470, setters); [C] only for the bytes. tools/ai_survey.py gained a states command and st_* summary keys; tools/gate/baselines/ai.txt gained exactly those 9 keys. (2) 1e6973ef: 49 RECIPE_BASES rows in tools/test_d2s.py (gh5-gh10, th, slow) pinned to the ckpt2 manifest of run:2026-10-27-anim-p2; sp-pal-chg2 and sp-ass-bos2 reuse the existing anim-pal-chg and anim-ass-bos saves (hashes equal), so no row. test_d2s.py: 60 tests OK. Not added: anim-<cls>-op-* (plan 0050 P2 part 3). Judgement call: the finding counts states 10 and 17 as a seventh/eighth reuse; the doc says five rows repeat a first-table word and explains the difference.
