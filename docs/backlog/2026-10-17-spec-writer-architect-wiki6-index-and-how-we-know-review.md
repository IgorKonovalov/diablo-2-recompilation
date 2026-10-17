---
from: spec-writer
to: architect
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md
  - ../wiki/README.md
  - ../wiki/how-we-know.md
resolution: ""
---

[2026-10-17] from spec-writer → architect: review `lane/wiki6` (commit `2b8a67f`), the two wiki pages the gate's
`based_on` check (W4) cannot see as stale. Not blocking.

- **[wiki/README](../wiki/README.md):** *What the wiki does not cover* rewritten whole: plans 0037 and 0040 closed;
  room lifecycle (`drlg/lifecycle`, reviewed) covered by the Levels section *Rooms that come and go*; open plans
  0038, 0039, 0041–0044 restated from the plan index as it stands at `407758a`; stats and states named as not yet
  reviewed (no page). Page table: the Levels row adds room release and restore; the How-we-know row lists the new
  sections. Combat stays the first simulation row.
- **[wiki/how-we-know](../wiki/how-we-know.md)** (`based_on: [process]`): ADR list gains 0008, 0011, 0014, 0015, 0018
  and the plan 0038 and 0041 records. New sections: emulated reproduction (ADR-0015; the read trace and guard stops
  from the S1e and S1f entries of the plan 0038 log, run:2026-10-17-sweep-emu and -emu2; what it can and cannot
  confirm, the SLEIGH `idiv` limit), simulation per event (ADR-0014: chaining, value oracles, game frames; plan
  0041's seed-invariance "no draw" rule and the aura exception; the 0037 event count from the plan index), two
  clients (ADR-0008 with the loopback condition), "not reachable on stock data" (plan 0038 § Classes; the outdoor 7
  split from inventory § 2.6 and drlg/0008), shortfalls and open questions (plan 0038 § Phase 2, plan 0041's
  shrines and wells, ADR-0018), the inferred-claims sweep (plan 0038 TL;DR, Promotion, Phase 3), and a slimmer review
  paragraph with the ledger. A demotion sentence added to *Three levels*; slots (ADR-0011) to *Runs*.
- **Please check:** each number against its cited source (28 643 and 18 800 emulated calls, 40 655 events, 52 200
  windows, 600 seeds, 7 shrines and 5 wells against 50 and 20, 1 526 / 2 531); the plain-language account of the
  outdoor 7 bound (draws used only through a few-bit mask); the plan-status wording in the index.

Gate fast tier green (E10–E12 ok, W4 0).
