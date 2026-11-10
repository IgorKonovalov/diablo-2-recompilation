---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S2.md
  - ../formats/golden-trace.md#case
resolution: ""
---

**Golden-set defect (plan 0064 P3 triage, S2 rows 2 and 3): the `drop` cases carry no magic-find input.** items/quality § C (M1–M3) and chain § Algorithm row G make the killer's magic find (its stat 80, plus its owner's for a hireling or summon) an input of the quality roll, and conformance § Drops says the killer is given; but `tools/golden.py` `drop_case` reads only the `TCR`, `PLAYERS`, `PARTY` and `CAP` lines and drops the `QKMF` (kmf), `QOMF` (omf) and `QMF` (mf) lines the kept logs hold between `QIN` and `QOUT` (`p2r2-s1-4861-r2-xn1.log`: 26 `QKMF kmf=472`; `p2r2-s1-4891-r2-cn1.log`: 18 `QKMF kmf=250`; `tools/quality.py` reads them, so the project's own replay never needed the input). The S2 implementer could reproduce 136 cases only by fitting 472 (expansion) and 250 (classic) from the printed diffs. Ask: (1) add the inputs to every `drop` case whose call logs them, as the stat values the spec composes, e.g. `killer_mf` (QKMF) and `owner_mf` (QOMF, when logged), with a cross-check against `QMF` at emit (refuse the case on disagreement, as `quality.py` does); say in fmt:golden-trace § Case what an absent value means (no quality roll read it, or a killer with no stat read, M1); (2) re-emit the v1 full set (version or set digest as the format's rules require) and update § Set v1; (3) tell the orchestrator so the S2 sandbox and its `cases.jsonl` are rebuilt before the Phase 5 re-run. The conformance page's wording follows in a spec-writer entry.
