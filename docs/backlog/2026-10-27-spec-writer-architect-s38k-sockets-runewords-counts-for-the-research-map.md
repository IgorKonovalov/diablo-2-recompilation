---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/items/sockets-runewords.md
  - ../specs/items/properties.md
resolution: ""
---

Plan 0038 Phase 3 (`lane/s38k`), the **items/sockets-runewords** cluster (batches S2c, H2b and H6b, all accepted),
with the one rule-8 companion line in items/properties: old and new `{C, I, L}` for the research-map rows and the
wiki's `based_on` dates (gate W4). Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [items/sockets-runewords](../specs/items/sockets-runewords.md) | {C 80, I 83, L 7} | **{C 128, I 84, L 7}** | 2026-10-17 → 2026-10-27 |
| [items/properties](../specs/items/properties.md) | {C 152, I 22, L 3} | **{C 153, I 22, L 3}** (F6's no-clamp half for qualities 2 and 3, from H2b sock 44) | 2026-10-21 → 2026-10-27 |

- **Research map:** the items/sockets-runewords row says the spec is ready for the Phase 3 re-tag; rewrite it whole
  (spec-writer rule 6). The items/properties row's counts move by one `[C]`.
- **Wiki (W4, done on this lane):** [wiki/items-other-paths](../wiki/items-other-paths.md) lists
  `items/sockets-runewords.md 2026-10-27` (the level test, the unidentified parent, the indestructible line and the
  ladder-only branches, the reader's refill and the loaded runeword, the socket-count caps refreshed);
  [wiki/items](../wiki/items.md) lists `items/properties.md 2026-10-27` (no text depends on F6).
- **The C rise** (80 → 128) is mostly splits: a statement raised in part becomes a `[C]` bullet and an `[I]` one, and
  the pseudocode blocks (B1, B2, B5–B6, C1, D1, D3, E1, E4, F1, F2) carry inline `[I]` on the lines no run reached.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers
  rule: sock 1 L284 (0x00563441) and the golem and other reader sites; sock 9 (d-2c, the trade window); sock 12 L174
  (no target without an inventory reached the test); sock 17 L237's `p5` clear (the empty slot is `[C]`, the clear and
  its reason `[I]`); sock 18's 253 half; sock 29 (d-none on the socket path); sock 38 L481's ranged half, L482, L507;
  the S2c remainders (sock 2's creation record, sock 4's `itype4..6`/`etype`, sock 6's `+0x084`, sock 14's general
  reason, sock 26's Zod, sock 43's cap of 0, sock 47's `hasinv` condition); H2b's write clamp and quality branches.
