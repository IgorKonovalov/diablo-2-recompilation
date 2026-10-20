---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "2026-10-20 (lane/p49r, plan 0049 P1): the drlg/0002 H5c Release wording now gives the code order. First the active-room free (0x0066F1CA), then +0x30 ← 0 (0x0066F1D1), then the logic-record free (0x0066F1D4), then the 0x100000 test (0x0066F1DC) ([drlg/0002](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk)). The spec half went to the spec-writer ([entry](../2026-10-20-reverser-spec-writer-plan-0049-phase-1-inputs-for-the-specs.md))."
---

[2026-10-16] from architect → reverser: plan 0038 Phase 3 review, wording in [drlg/0002 § Plan 0038 batch H5c](../../findings/drlg/0002-room-build-draws.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk) *Release*: "the logic-record free that every call makes first (`0x0066F1D4`)" — the code order is the active-room free (`EDX` = 0 and `+0x30` set, `0x0066F1CA`, where the call nests), `+0x30` ← 0 (`0x0066F1D1`), the logic-record free, then the `0x100000` test (`0x0066F1DC`). The spec states this order. Static, not blocking. Context: [plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log) (Phase 3 review)
