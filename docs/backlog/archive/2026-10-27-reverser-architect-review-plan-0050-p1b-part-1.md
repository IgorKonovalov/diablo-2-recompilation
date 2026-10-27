---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../findings/anim/leads.md
resolution: "Accepted with fixes at the lane/p50c review (plan 0050 log, 2026-10-27): Version column per claim (19 D2R-only, 5 1.09-only rows); the tables-not-copied wording corrected; the blind rule widened to P1.1 with a log statement and review check. Hammerman's prose offsets within policy; the source stays a lead."
---

Review plan 0050 Phase 1b part 1 (`lane/p50c`): the blind half of the community cross-check. Six sources registered in docs/sources.md with the version each describes, two more registered as not read; 61 claims staged in [anim/leads](../../findings/anim/leads.md) (R 5, A 15, C 7, D 5, H 10, B 5, M 14), all `[L]`, no verdicts, nothing promoted; seven conflicts named; kept check `tools/anim_leads_check.py` (`331eb0f0…`, output `b185e780…`): the sources' breakpoint tables against their own formulas, 70 of 78 comparisons agree, the 8 others (Druid and Necromancer FCR) need another base. No Ghidra, no harness, no P1 work read. Points for the ruling: (a) is the blind rule in the leads file's header (P1.2 and P1.3 lanes do not read their batch's claims before writing theirs) the right control, or should the file stay out of their reach until P1.3 is written? (b) Hammerman's post in `src:basin-runwalk-thread` names two in-memory offsets of a 1.09 build in prose (not copied, not used): keep the source as a lead, or register it rejected like `pk-pathfinding-thread`? (c) The A4 animation-parameter table and the per-skill delays D4 are table values (P0): decide them from the P0 survey in part 2, as staged. Part 2 (verdicts) runs after P1.3's review. Not blocking.
