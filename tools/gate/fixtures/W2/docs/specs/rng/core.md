---
spec: rng/core
status: draft
tags: {C: 0, I: 1, L: 1}
---

# RNG core

## Algorithm

| Step | Function | Tag |
|---|---|---|
| step | fn:RNG_Next@0x0045A1B0 | |

- [I] Seeds are 64-bit. (data:g_pLevels@0x0096C888)

See [the finding](../../findings/rng/0001-core.md#0001--rng-core-seed--step--range--notes-1) and
[its second summary](../../findings/rng/0001-core.md#answer-summary-1).

## Open questions

- [L] Whether the carry is ever zero.
