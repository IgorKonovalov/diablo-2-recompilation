# 0067 — Player trade: the trade state machine, its commit and its failures (ADR-0033)

> **Status:** approved (2026-11-10, by the owner, as recommended: ADR-0033 accepted; Phase 2 asked again at Phase 1's review; Phase 1 done; Phase 2 go given by the owner 2026-11-10, to run that night)
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

### 2026-11-10 — Phase 1 (static reading), `lane/n67r`

**Done.** [multiplayer/0003](../findings/multiplayer/0003-trade.md) reads the whole trade module (0x00566B30–0x00568D5B)
and every caller from outside it (`call-sites-trade.txt`: 84 direct calls into the module's 28 entries; the tick's only reference is the
event slot 0x006E1844). Everything is `[I]`; nothing was run. Kept outputs: `workspace/logs/n67r/static/` (31 files;
`manifest.txt` hashes the other 30 and passes `sha256sum -c` from that directory; `commands.txt` holds every command). `re/symbols.csv`: 38 new
`I` rows (subsystem `multiplayer/trade`), and 13 rows from multiplayer/0002 moved to the new finding as evidence.
multiplayer/0002 carries dated notes where 0003 corrects it (the request distance, the gold offer) and on its two
answered open questions.

**The Phase 1 branches**, each read at `[I]` with anchors, or named with the step not followed:
- trade button codes and handlers: 2, 3, 4, 7, 8; 5, 6 and above 8 do nothing (switch table 0x00568620) (0003 § 4);
- request gates: distance (`d ≤ 8`; 9–50 walks first, which corrects 0002), busy, end lock, both states 0, the 5 s end
  windows and the 1 s message rate, town. No hostility or mode test exists in `TradeRequest` (§ 3);
- grid moves: page 2 → a copy on the partner's page 1, the id map, the hide path with its 10 s lock, the change lock on
  seven inventory packets and its five refusals, the belt lock, the 14 `InteractIsPlayer` refusals (§ 5). Not
  followed: when `BeltOverflow`, `CubeDropEmptied` and `PageSwapCursor` reach `TradeShowOffer`;
- accept flags and what resets them: the state table 0–16 and the tick (§ 2). Gold offers change no state (§ 4);
- the commit: gold tests, the room test (scratch grids filled in the FIRST order, where the real placement uses BEST),
  the quest gate, then the moves, then the gold (§§ 7–8);
- cancel paths: buttons 2/3, an overspend, a failed offer copy, the deferred close, the commit's 8 cancels, leaving
  (`ClientRemove`), death (`PlayerDeath`). Each one that reaches `TradeReturnItems` rebuilds both inventories from the opening snapshot; a `TradeAbort` with no back-pointer and waypoint travel do not (§ 9). A
  level change has no trade code: waypoint travel only clears the traveller's interaction (§ 9). Not followed: whether
  the discarded item units are freed, and `ClientRemove`'s argument at its eight callers;
- the save mid-trade: the snapshot from opening, through the interaction flag of `PLRSAVE_Save` on the route at
  0x00532340 (two other routes not followed to `D2S_WriteSave`) (§ 10).

**Case list:** 0003 § 11, 13 cases (T1 = MP31 … T13 optional), each with its recipe, the logger points (a new
`tools/gdb/two-trade.gdb`, read-only) and a prediction, with the reading it separates; the cases a stock client
cannot reach are named there (a death in town, monster equipment, a waypoint packet while trading, an `ItemCopy`
failure, a dead target).

**Judgment calls for the reviewer.** (1) The finding is `multiplayer/0003`, not `items/00NN`, beside 0002 § 2 which it
completes. (2) The snapshot reading ("a cancel rebuilds the whole inventory as new units") rests on `InvUnlinkAll` and
`ItemListReadByVersion` read statically; T2 separates it from "the offered items are returned" (an item moved on
page 0 goes back to its opening cell, every id changes). (3) The FIRST/BEST disagreement of the room test is a reading of
the scratch's owner word (0) against the inventory spec's B1; no layout was searched (T13 optional). (4) No forced
case is proposed, so the open question on ADR-0013 needs no ruling unless the owner wants the waypoint case.

**Handoff.** Phase 2 (if the owner says go): build the logger and `tools/trade_check.py` from § 11, measure the gold
button and the close control in the first session, then run T1–T12. Phase 3 (spec-writer): `items/trade` from 0003
§§ 2–10, at `[I]` throughout if Phase 2 does not run. Review: Tier B.

**Phase 2 cost, for the owner's decision.** No owner play; agent-driven. One static lane-session (no slot) to write
the logger, the checker and the T13 layout search. Then one development session (measures the gold entry and the close
control, shakes the logger down) and three kept hosting sessions, about 45–75 min each with **both slots held**:
(a) T1–T3, T5, T6; (b) T4, T7, T9–T12; (c) T8 (the joiner leaves) and T13 if a layout exists. About 4–5 hours of both
slots on one day, blocking every other harness lane meanwhile, plus a port-4000 re-read per session (`ufwcheck.sh`).
If plan 0065 Phase 2 runs two clients, sharing its set-up saves the development session. Skipping Phase 2 leaves
`items/trade` all `[I]`.

### 2026-11-10 — Owner decision (evening)

- **Phase 2: go**, the hosting sessions to run the night of 2026-11-10. First the static preparation (logger,
  `tools/trade_check.py`, the T13 layout search), then the development session and the three kept sessions on slots 1
  and 2. The port-4000 record (multiplayer/0001 § 5, step 1) is the owner's `sudo ufw status verbose` before the first
  hosting session. Plan 0065's Phase 2 does not share this set-up; it keeps its own.
