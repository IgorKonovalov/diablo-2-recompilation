# ADR-0033 — Scope: the player-to-player trade

> **Status:** proposed
> **Date:** 2026-11-10
> **Related plan(s):** 0067-player-trade

## Context

[ADR-0025](0025-scope-item-use-inventory.md) brought item use and the inventory into scope and left trading out:
"it would close the last way an item moves between grids, but it is a multi-message flow between two clients, needs
both harness slots and the owner, and adds little the single-player rules do not already specify; it lost on cost and
stays a later plan". [items/inventory](../specs/items/inventory.md) names pages 1 and 2 and the trade test at
0x00535610, and specifies neither.

Since then, plan 0051 Phase 1b read the trade state machine statically
([multiplayer/0002](../findings/multiplayer/0002-trade-and-party-gold.md) § 2, all `[I]`) and wrote the MP31
prediction. Plan 0044's two-client harness ran 19 sessions under ADR-0008. Plan 0061 will catalogue the trade
messages among the rest. The static cost has therefore dropped. The live cost (both slots, two clients, a port-4000
check per session) has not changed.

## Decision

Bring the player-to-player trade into scope as a game-rules row, `items/trade`, beside `items/use`. The row covers the
trade request and its gates, the trade grids (pages 1 and 2), adding and removing items and gold, both accepts, the
commit (the order items and gold move, the room tests, the gold caps), every cancel and failure branch (no room, a
player leaving, a death, a level change), and what the save sees. It covers the server's outcomes only. The client's
trade window and its display stay out, under ADR-0014's outcome rule. Live claims need the two-client harness
(ADR-0008) and are agent-driven, not owner play.

## Consequences

### Positive
- Closes the last item move between grids that the specs only name, and the last open use of pages 1 and 2.
- Reuses the two-client harness, MP31's prediction and plan 0061's message entries.

### Negative
- Every live case needs both slots, so the plan blocks every other harness lane while it runs.
- Most of the value is completeness. A single-player reimplementation never trades, and a multiplayer one can stage
  most outcomes from rules the specs already state (grid placement, gold caps).
- One more row to keep reviewed.

### Neutral
- Trading in a stock single-player game is unreachable, so the row's `[C]` claims all come from two-client runs.

## Alternatives considered

**Keep trading out (ADR-0025's ruling).** It costs nothing and the specs stay complete for single player. It remains a
good option. This ADR is drafted so the owner can choose, not because the architect recommends it over the other
drafted plans.

**Fold the trade into `items/inventory` with no ADR.** It would widen ADR-0025's scope silently, contradicting its
"trading out" sentence. A short ADR keeps each scope statement accurate.
