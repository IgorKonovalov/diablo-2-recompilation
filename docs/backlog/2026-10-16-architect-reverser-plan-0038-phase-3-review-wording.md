---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 Phase 3 review, wording in [drlg/0002 § Plan 0038 batch H5c](../findings/drlg/0002-room-build-draws.md#plan-0038-batch-h5c-run2026-10-16-sweep-roomk) *Release*: "the logic-record free that every call makes first (`0x0066F1D4`)" — the code order is the active-room free (`EDX` = 0 and `+0x30` set, `0x0066F1CA`, where the call nests), `+0x30` ← 0 (`0x0066F1D1`), the logic-record free, then the `0x100000` test (`0x0066F1DC`). The spec states this order. Static, not blocking. Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log) (Phase 3 review)
