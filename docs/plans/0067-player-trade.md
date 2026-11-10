# 0067 — Player trade: the trade state machine, its commit and its failures (ADR-0033)

> **Status:** draft (2026-11-10, architect; waits for the owner's approval and for ADR-0033)
> **Created:** 2026-11-10
> **Owner skill(s):** human, reverser, spec-writer
> **Related ADRs:** 0008-two-client-harness, 0014-scope-game-simulation, 0025-scope-item-use-inventory, 0026-scope-in-game-message-layer, 0033-scope-player-trade

## TL;DR

**Question:** what does the server do when two players trade, from the request to the commit or the cancel? When this
plan is done, a new game-rules row `items/trade` is reviewed. It specifies the request and its gates, the trade grids
(pages 1 and 2), adding and removing items and gold, both accepts, the commit's order and room tests, and every cancel
and failure branch, from the code and from two-client runs. Its wiki page exists. This plan exists so the owner can
choose; the architect ranks it last of the four drafted on 2026-11-10 (ADR-0033 § Negative).

## Context

- **What exists:**
  - [multiplayer/0002](../findings/multiplayer/0002-trade-and-party-gold.md) § 2 reads the trade state machine
    statically (all `[I]`), and § 3 predicts MP31.
  - [items/inventory](../specs/items/inventory.md) names pages 1 and 2 and the trade test at 0x00535610 and leaves
    them unspecified (ADR-0025).
  - [economy](../specs/items/economy.md) gives the trade price (`ItemTradePrice`).
  - Plan 0061 will catalogue the trade messages.
- **Dependencies:** items/inventory, items/use and items/economy are reviewed. Plan 0061's catalogue is helpful, not
  required: Phase 1 reads the trade handlers itself and cites 0061's entries if they exist.
- **Live cost:** every live case needs both slots and the port-4000 precondition (ADR-0008). If plan 0065 Phase 2 runs,
  this plan's Phase 2 should share its two-client set-up and run right after it.

## Phases

### Phase 0 — Accept ADR-0033
- **Owner skill:** human
- **Done when:** ADR-0033 is `accepted` (or this plan is abandoned).

### Phase 1 — Static reading
- **Owner skill:** reverser (static, Ghidra; no slot)
- **What:** complete multiplayer/0002 § 2 into a trade finding:
  - every trade button code and its handler;
  - the request gates (distance, mode, town, hostility, a player already trading);
  - the grid moves into and out of pages 1 and 2, and the gold offer;
  - the accept flags and what resets them;
  - the commit's order of item and gold moves, its room and cap tests;
  - every cancel path (button, leaving, death, level change, a full inventory at commit);
  - what is saved if a player exits mid-trade.

  Name the functions in `re/symbols.csv`. Write one prediction per Phase 2 case.
- **Outputs:** a new finding `docs/findings/items/00NN-trade.md` (or multiplayer/0003), `re/symbols.csv`, the case
  list with predictions.
- **Done when:** each branch above is read at `[I]` with anchors, or named with the step not followed. The case list
  gives every case its recipe, its logger points and its prediction. Review: Tier B.

### Phase 2 — Two-client runs
- **Owner skill:** reverser (harness, slots 1 and 2; agent-driven)
- **What:** after the port-4000 re-read, run the cases:
  - MP31 (an item and gold);
  - a cancel by each player;
  - a commit with no room;
  - a gold offer past the receiver's cap;
  - a player leaving mid-trade;
  - an accept reset by a change after the accept.

  Each case runs with a trade logger and a check built in Phase 1.
- **Outputs:** `run:<date>-trade`; the finding's run section.
- **Done when:** each case has a kept log and a check, with 0 mismatches or a named contradiction. Each case not
  reached is named with its reason. Review: Tier B.

### Phase 3 — The spec
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/trade.md` (row `items/trade`), and replace items/inventory's "trading is not
  specified here" with a link.
- **Done when:** the spec is reviewed (Tier A) and `python3 -I tools/gate.py --full` is green.

### Phase 4 — Wiki
- **Owner skill:** spec-writer (wiki lane, Opus)
- **What:** a trade section in [wiki/inventory](../wiki/inventory.md) (ADR-0012).
- **Done when:** reviewed (Tier A, ADR-0030); the review closes the plan.

## Open questions

- Whether the trade's duplication guards (an item in two grids at once, a commit racing a pickup) are reachable on stock
  clients. If a case needs a forced client message, it is a forced run under ADR-0013 and the owner rules on it at
  Phase 1's review.
- Whether to run Phase 2 at all, or specify the trade at `[I]` from Phase 1 alone. A Phase 1–3 plan with no slot would
  cost far less. The architect recommends asking again at Phase 1's review.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_
