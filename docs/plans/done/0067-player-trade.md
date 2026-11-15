# 0067 — Player trade: the trade state machine, its commit and its failures (ADR-0033)

> **Status:** done (closed 2026-11-15 at the Phase 4 review; approved 2026-11-10 by the owner, as recommended: ADR-0033 accepted, Phase 2 run on the owner's go)
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
  - [multiplayer/0002](../../findings/multiplayer/0002-trade-and-party-gold.md) § 2 reads the trade state machine
    statically (all `[I]`), and § 3 predicts MP31.
  - [items/inventory](../../specs/items/inventory.md) names pages 1 and 2 and the trade test at 0x00535610 and leaves
    them unspecified (ADR-0025).
  - [economy](../../specs/items/economy.md) gives the trade price (`ItemTradePrice`).
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
- **What:** a trade section in [wiki/inventory](../../wiki/inventory.md) (ADR-0012).
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

**Done.** [multiplayer/0003](../../findings/multiplayer/0003-trade.md) reads the whole trade module (0x00566B30–0x00568D5B)
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

### 2026-11-10 — Phase 2 preparation (static), `lane/n67p`

**Done** (no Ghidra, no wine, no game launched). [multiplayer/0003](../../findings/multiplayer/0003-trade.md) § 12 holds
it; kept outputs `workspace/logs/n67p/static/` (`commands.txt`, `manifest.txt`).
- **Logger** `tools/gdb/two-trade.gdb` + `tools/gdb/two-trade.py`: § 11's points, read-only (ADR-0003), loading in one
  gdb session with `pilot.py` and `two-players.py` (`gdb-load.txt`); ready line `TRDY`. Added to § 11's list: each
  scratch cell of the room test (`SCP`, 0x0063E228), each real placement (`TMP`), the `0x77`/`0x79`/`0x5A` sends with
  their site, the belt lock, the snapshot copy's sha256 and `ClientRemove`'s arguments. All 39 addresses decode as
  instruction starts (`bpcheck.txt`).
- **Checker** `tools/trade_check.py` (`check`, `mark`, `layout`, `cases`): one rule per event kind from §§ 2–10 and
  32 expectations over the 13 cases; `tools/test_trade_check.py` 16 tests OK.
- **T13**: the search finds both disagreements under B1 (40 000 layouts, seed 67: 248 where the test passes and the
  move fails, 8 of them for every order of the offer; 1 064 the other way, 5 for every order). The T13 layout and T4
  share one character pair. § 11's T4, T7 and T13 rows and § 8's sketch are updated.
- **Correction** (§ 12.1, carried into §§ 4, 8, 11 and multiplayer/0002): the 4-digit "codes" were `PlrTrade.cpp`
  line numbers of the client lookup; the `0x77` codes are now given. § 11's `TSO` and `TCM` addresses moved to the
  points that hold the values.
- **Characters**: four recipes (`mp-trade-host`, `-join`, `-host13`, `-join13`) in `tools/mp_saves.py` (two pairs,
  `check`: recipes 34, pairs 23, 0 bad) and pinned in `tools/test_d2s.py` (built twice, byte-identical).
- **Run recipe** for the harness lane: § 12.4 (per session the commands, the tokens, the marks, the logs kept).

**What the dev session must still measure** (§ 12.4): (1) the gold button, how its entry box takes the amount, and
whether the client sends one button 8 per keystroke or per entry; (2) the trade window's close control (Escape or
the window's button) and the button code it sends, which also decides T8's way out; (3) that the paper-doll belt
point (562,252) and the inventory cells sit where the trade screen draws them; (4) the logger smoke with every tag the
checker reads.

**Judgment calls for the reviewer.** (1) T13 uses J accepting last, so the first move (J's `gcv` into H) succeeds and
the second fails: one case shows both the BEST failure and the snapshot undoing a half commit (§ 8). (2) T4 and T13
share a pair and one trade window, T8 closing it; T10 and T11 share `TrHost`/`TrJoin` with H's cube empty and J's
holding a `gcv`, so T10's refusal is told by event `0x0A` and T11's by its absence. (3) `tools/test_d2s.py`'s
`test_every_recipe_has_a_base` already failed on `main` for 11 other recipes (`ai-*`, `combatsor-nomerc`,
`framenova`, `inv-sor`, `inv-sor2`, `path-*`); this lane adds its four and leaves those, which are not this plan's.

**Handoff.** Phase 2's harness lane (slots 1 and 2): the dev session, then sessions (a), (b), (c) of § 12.4, each
checked with `trade_check.py check … --excel workspace/merged/data/global/excel`. Review of this preparation: Tier B.

### 2026-11-10 — Phase 2 runs (harness), `lane/n67h`

Slots 1 and 2, no owner play. The port-4000 precondition is the owner's `sudo ufw status verbose` of 2026-11-10
(transcribed by the orchestrator; active, deny incoming, no 4000 rule) with the no-root baseline; every session passed
`tools/ufwcheck.sh` (`UFW-OK`). Record: [experiments § run:2026-11-10-trade](../../findings/multiplayer/experiments.md#run2026-11-10-trade);
results: [multiplayer/0003 § 13](../../findings/multiplayer/0003-trade.md#13-phase-2-run-run2026-11-10-trade-lanen67h).

- **Dev session:** the gold entry (coin at (494,461), digits, Return; one `TRB` 8 per entry, after a 7), the close
  (Escape or the circle at (371,461): button 2, code 9), the belt and cells, and the logger smoke (every tag the checker
  reads, except `TQN`) are measured.
- **Kept sessions:** a (T1, T2, T3 a/b, T5, T6), b (T7, T9–T12), c (T4, T8, T13). `trade_check.py`: 0 mismatches in a and
  b; 2 in c (T13's cancel ticks ran in one logged frame, f 2371, where the rule gives +1 each; named, not resolved).
- **Not reached, named:** T3 (c) (no waypoint route on this logger), T5's `g' > gold(J)` (the client clamps the entry),
  T6's 8-alone (a 7 precedes every entry; the box closes when the partner accepts), T8's *Save and Exit* route (Escape
  closes the trade; J left by a killed client, so `TAB` and the host's `TSV`/`TSC` carry the claim, J's save was not
  rewritten). Not forced: no ADR-0013 case run.
- **Handoff to Phase 3:** the spec states the checked rules at `[C]` where a case is met (T1, T2, T4, T7, T9–T13, T3 a/b,
  T5 first part, T8 `TSV`), the gold button 8 as `[I]` (observed only after a 7), the tick-delay rule with the T13
  exception, and the client-side clamp of the gold entry. The finding's § 12.4 recipe changes are in § 13. **Review: Tier B.**

### 2026-11-10 — Phase 3 (the spec), `lane/n67s`

**Done** (no Ghidra, no slot, no game). [items/trade](../../specs/items/trade.md) is written as a draft: C 53 / I 74 / L 9.
Sections: A the states and the tick (state diagram), B the request, C the buttons, D the offer pages and the change lock,
E the gold offer, F the commit (diagram of its order; the FIRST room test against the BEST moves; the half commit
undone by the snapshots), G the record and the snapshot, H the ways out, I the save mid-trade; a worked example from
T13 and T4 (session c), ten reimplementation notes, nine open questions.
- **Tags.** `[C]` only where a checked log of run:2026-11-10-trade covers the branch, each naming its case: the request's
  busy and end-window refusals (T3 a, b), the opening and records, the accept and its refusal at 7/8/11 (T7), button 7,
  the gold clip (T5 first part), the change lock on 19 item tests with the cube, quest-code and belt refusals (T9–T11),
  the offer copy (T12's no-reopen), the removal lock (T7), the commit's FIRST scratch cells and BEST placements (T1, T4,
  T5, T6, T13), the room refusal (T4), the half commit (T13), the exchange, the 5 closes, the 2 cancels, the 2 aborts
  of a killed joiner and their 8 snapshot copies at the save. `[I]`: T3 (c)'s town test, T5's overspend, a button 8
  at a partner's 4 (T6), the save's route and file (T8), the tick's frame delays, states 12–16, death, waypoint travel.
  The counts of item tests (19) and button 8s (113) were taken from the kept host logs (`workspace/logs/n67h/{a,b,c}/host.log`).
- **The T13 contradiction** is the first open question, `[L]`, with the frame-word lead; A1 keeps the delays `[I]`.
- **items/inventory**: the Purpose's "trading is out" and the note "Trading is not specified here" now link
  items/trade (dated; the note keeps its `[I]`, tag counts unchanged); `consumed_by` gains items/trade.
- **Research map**: a new `items/trade` row (draft spec); the ADR-0033 paragraph and the out-of-scope line no longer
  say trading is out or that the row is to come; the quirks row's counts.
- **Quirks**: Q530–Q538 from the spec's notes n1–n8 and n10 (class 8: 7 entries, class 9: 2), n9 (real time, not
  frames) skipped as wall-clock like quests/travel's; coverage row, class and coverage totals and front matter
  updated. `tools/quirks.py check`: 538 entries, 58 specs, 522 notes, 490 taken, 0 errors.
- **Glossary**: *Trade snapshot*, *Trade state*.

**Judgment calls for the reviewer.** (1) The quirks page says each entry restates a statement of a reviewed spec;
Q530–Q538 cite a draft, because E18 requires the coverage now; the research-map row says so. (2) A finding of § 13 the
spec adds: at both drops `ClientRemove` saved the host as well as the leaver with flag 1, each through two calls (rooms
`0x8000` and 7 348), read from the host logs' `TSV`/`TSC` lines (I2). (3) The logged button 8s came at states 3, 6, 8
and 11 too, not only 3 (E1's `[C]` line); none at a partner's 4. (4) The "client clamps the gold entry" and "one 8
per entry, after a 7" observations are stated `[C]` in § E as client behaviour seen in the run, since they decide which
server branches a stock client reaches; the window itself stays out (ADR-0033).

**Handoff.** Review: **Tier A** (the Phase 3 done-when); on acceptance the row turns `reviewed`. Phase 4 (the wiki
section in wiki/inventory) follows the review.

### 2026-11-10 — Phase 3 Tier A review (`lane/n67s`): accept with fixes

**Verdict: accept with fixes (6).** [items/trade](../../specs/items/trade.md) is promoted to `reviewed` (C 53 / I 75 / L 9);
the research-map row and the plans index say so. Checked: `trade_check.py check` re-run on a, b and c gives the kept
totals (547/318/0, 362/203/0, 400/218/2); every manifest passes `sha256sum -c`. 28 `[C]` statements sampled over §§ A–I
and the entry points, 23 against the host log lines of their case and 5 (A1's steps, B2.6, C3, F2, F1.7) through the re-run checker alone (the T3 a/b events and
frames, the T4 and T13 `TMS` order and `TCX` sites, the T7 lock and ticks, T12's states, T5's clip, the five closes,
the two cancels and aborts, the drops' `TSV`/`TSC`). The partly reached cases (T3 (c), T5's overspend, T6's 8 at 4,
T8's route, the tick delays) are `[I]`; T13's contradiction is the first open question and every `[L]` is under *Open
questions*; the diagrams add no claim; the items/inventory note is dated.
- **overclaim (2).** (a) T7's refused accept "at 7, 8 and 11" (A1, C4 twice, the research-map row): the log holds one
  refused button 4, at 11 (b f 1769); 7 and 8 lasted a frame each. Now `[C]` at 11, `[I]` for the rest. The same words
  in multiplayer/0003 § 13's T7 row, passed at the `lane/n67h` check, are corrected there. (b) E1's client bullet ("one
  8 per entry, always after a 7", "the client clamps"): restated as what the server received, with the counts (7 of
  113 button 8s carry an amount, each after a 7 of the presser; 106 carry 0; no amount above the presser's gold).
- **misread (1).** G2 and D1: T2's cube was not picked up; its item test returned 0 (quest code, J holding a cube),
  so it is a third refused cube move, not an item the restore brought back. § 13's T2 row is corrected with it.
- **tool not kept (1).** The 19 item tests, the 113 button 8s and the drops' saves (two calls per player, 8 snapshot
  copies) were read from the host logs and stood in no finding (judgment call 2). Ruling: the numbers go into the
  finding first. A dated addendum to multiplayer/0003 § 13 now holds them, from the kept
  `workspace/logs/n67h/review-n67s/recount.py` (output and manifest beside it), and the spec cites it.
- **omission (1).** "The caller above `SaveItemListOrSnapshot` was not logged": the `TSV` site 0x005697D2 lies inside
  `D2S_WriteItemList`; the entry points and I2 now say so, and the `PLRSAVE_Save` route stays `[I]`.
- **stale cross-reference (1).** The plans index still said "P2 go … hosting that night".
- **Judgment calls.** (1) Accepted: the quirks entries cite a spec that this review promotes, so Q530–Q538 restate a
  reviewed statement from this commit on; the quirks row's "a draft until its Tier A review" is dropped. (3) Accepted
  as reworded: ADR-0033 leaves out the client's window and display, not the messages the server receives; the packets
  a stock client sent decide which server branches the run reached, and they are logged at the server's handler. The
  client's own clamp is not a spec rule.
- **Gates.** `tools/quirks.py check`: 538 entries, 0 errors. `tools/gate.py --full`: green.
- **Ledger** (for the orchestrator's row): accept with fixes; overclaim 2, misread 1, tool not kept 1, omission 1,
  stale cross-reference 1. Next: Phase 4, the wiki section (spec-writer).

### 2026-11-10 — Phase 4 (the wiki section), `lane/n67w`

**Done** (no Ghidra, no slot, no game). [wiki/inventory](../../wiki/inventory.md) gains `## Trading between players`
from [items/trade](../../specs/items/trade.md) (reviewed, `updated: 2026-11-10`, added to `based_on`): how a trade opens,
offers and what locks, gold, both accepts (state diagram), the commit (flow diagram; the first-fit room test against the
best-spot moves, both directions, T13 as the worked table), the snapshot undo, every way out (table), the save
mid-trade. Each statement says whether a case of run:2026-11-10-trade reached it ("seen", with the run's scope stated
at the top of the section) or it is read from the code; the T13 tick mismatch is named as an open question.
Stale text closed: the page's intro ("trading … out of scope"), the "Trading is not specified" line of *What is not
known yet* (now three trade bullets from the spec's open questions), the pages paragraph, *Random draws* (a row: the
trade's copies' draws unknown), *Where to read more*; wiki/README's row 9 and its coverage paragraphs.

**Judgment calls for the reviewer.** (1) "Seen" in the trade section means the trade run, defined there; the page's
*How sure* table, which describes the two item runs, gets a one-line pointer instead of a third row. (2) Message codes,
button numbers and state numbers are left out; states are named in words (open, accepted, changed, locked, ended).

**Handoff.** Review: **Tier A** (ADR-0030, wiki lane); the review closes the plan.

### 2026-11-15 — Phase 4 Tier A review (`lane/n67w`): accept with fixes; plan closed

**Verdict: accept with fixes (8)**, applied on the branch. The section restates [items/trade](../../specs/items/trade.md)
section by section; every "seen" was read against the spec's `[C]` notes and every "read from the code" against its
`[I]` pseudocode. No `[L]` is stated as fact (the T13 lead is named as a lead under *What is not known yet*), the
section carries no history or dates, and the three diagrams illustrate statements the text makes. Judgment calls: (1)
the one-line pointer from *How sure* to the section's own definition of "seen" stands; (2) leaving out the codes and
state numbers stands.

Fixes, all in [wiki/inventory](../../wiki/inventory.md) unless named:

1. *How a trade opens*: the corpse case of B1 (a dead target within 8 is picked up, no request) added. (omission)
2. *How a trade opens*: "nothing happens if … either player is already in a trade" contradicted B2: a target in a trade
   is busy and the asker gets the step-2 message; the silent return is step 4, either state not back to idle, after the
   end-window tests. Split into two bullets in the code's order. (misread)
3. *Offers*: "any move … un-accepts both" scoped: D1's early refusal (no partner record, the end lock, bit 23) refuses
   with no state change. (overclaim)
4. *The commit*, step 2, and *What is not known yet*: T4's `side` 1 is the offer of B, the player who accepted first;
   the page said "the second accepter's side" and listed the unreached side 0 as "the giver's side". Both renamed by
   whose offer failed. (misread)
5. *The gold*: the overspend's exception is "either player Blocked" (bit 22, bit 23 or the update list), and a blocked
   overspend falls through to the clip and the store; the page said "unless a move is pending". (misread)
6. *Every way a trade ends*: "the server saves first" for any leave; `ClientRemove` saves when its argument is 1, seen
   for the dropped client, unread at its other callers. Scoped. (overclaim)
7. *The commit*, step 4: the move order and the new copies carried no tag; marked seen (T13, the exchanges). (omission)
8. Stale text the section made stale: [wiki/how-we-know](../../wiki/how-we-know.md)'s "trading between players is not read
   yet", [wiki/economy](../../wiki/economy.md)'s "trading between players (a two-client plan)" and the matching `[L]` of
   [items/economy](../../specs/items/economy.md#open-questions), now pointing at items/trade § E (economy `updated`
   2026-11-15, its wiki `based_on` and research-map row with it; the `[L]` count unchanged). (stale cross-reference)

**Plan open questions.** Both settled by the phases: Phase 2 ran (the owner's go, 2026-11-10), and no case needed a
forced client message; the unreached branches a written packet would reach are items/trade's open questions.

**Close.** Status done, moved to `docs/plans/done/`, the plans index, the research map (`items/trade` row and the
ADR-0033 paragraph) and the root README updated. No backlog entry was answered by this phase.

**Gates.** `tools/gate.py`: green.

**Ledger** (for the orchestrator's row): accept with fixes; overclaim 2, misread 3, omission 2, stale cross-reference 1.
Promoted: none new; fixes 2, 4 and 5 recur under spec-writer rule 3 and fix 8 under rule 7, whose *Seen* lists gain
this review.
