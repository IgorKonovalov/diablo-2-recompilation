# 0060 — Item use and inventory: potions, scrolls and tomes, belts, stacks, pickup and drop, ground items, identify

> **Status:** approved (owner, 2026-10-30: "approve all of them", every scoping question answered as recommended); drafted 2026-10-30 (architect, `lane/plans57`)
> **Created:** 2026-10-30
> **Owner skill(s):** archivist (phase 0), reverser (phases 1, 2), spec-writer (phases 3, 4)
> **Related ADRs:** 0014-scope-game-simulation, 0017-scope-quests-travel-economy, 0021-observed-boundaries-in-emulation, 0025-scope-item-use-inventory

## TL;DR

What does the server do, end to end, when a player uses, moves, picks up, drops or identifies an item? Which slot an
item can go to (inventory and stash grids, the belt's rows, the cursor), how stacks merge and split, what a potion,
scroll or tome does and in which order, where a dropped item lands, how long a ground item lives, and when charms
count. When this plan is done, `docs/specs/items/use.md` and `docs/specs/items/inventory.md` (row `items/use`) state
it with the request handlers as entry points, the draws in order, and the integer arithmetic.

## Context

- **Scope.** The 2026-10-27 proposal ("player-side game rules, an ADR-0017-style extension; not recommended now")
  named this; the owner's 2026-10-30 instruction opens it. It needs a short scope ADR beside ADR-0017 (question 1).
  The client's UI (drag, tooltips, the belt display) stays out: the claims are the server's outcomes (ADR-0014).
- **Where the pieces live now:** potions' group clear before apply, stats/states B3 (`ItemUseTimedState`, `[I]`) and
  the regeneration tick E2 (stat 74 by sign, `[C]`); charm linking, stats/aggregate § the item refresh
  (`ITEMS_IsActiveCharm`); the starting items' belt and inventory placement, player/creation § E (`ItemToBelt`
  `0x0055E9B0`, `[C]`); scroll and book use as skills, skills/0015 (do 113, `PlayerUseBeltItem` `0x00562390`); the
  town portal tome and its town refusal, quests/travel G1 (`[C]`); gold pickup and the party share, items/economy G
  (`GoldPickup`, `[I]`); Cain's identify cost, items/economy G14 (`[I]`); quantity wear, items/economy; identify's
  attach and the cursor consume, items/quest-drops (`ItemIdentifyAttach` `0x0055FE00`, `CursorItemConsume`
  `0x0055EEA0`, `[C]`); ground items' collision mark, drlg/collision (bit 9, `[C]`); the inactive item record, its
  expiry and the 1 500-frame sweep, drlg/lifecycle (`[C]`/`[I]`); the client request table `g_SrvPacketTable`
  (`0x006E0D18`, items/0008).
- **The gap:** the use dispatch for each `Misc` use type, the potion amounts and their states, the grids and their
  sizes, the placement search (inventory, belt row by belt type, the ground drop's cell search), stacking and splitting,
  pickup rules (ownership, `nopickup`, the cursor), the stash, scroll-of-identify, and the ground item's lifetime when
  its room stays active.
- **Dependencies:** all the cited specs are reviewed. 0055·P1's drain reading helps (the request handlers are queue-1
  packets) but does not gate.

## Phases

### Phase 0 — Tables
- **Owner skill:** archivist
- **What:** table docs for `belts` (record 264 bytes, loader site `0x00660C22`) and `inventory` (240 bytes,
  `0x0065C0F7`), both loaded ([data/0001](../findings/data/0001-excel-loader.md)) and undocumented in `docs/tables/`; the
  `Misc` use columns (`useable`, `stackable`, `pSpell`, `spelldesc`, `calc*`, the potion amounts) and `Books`, with the
  readers already named in `re/symbols.csv`.
- **Done when:** each table the game loads has a doc with its in-memory layout, and the gate's survey covers it.

### Phase 1 — Static, in three batches
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G`; emulation where a value decides)
- **What:** P1.1 the use request and the dispatch by use type (potions, rejuvenation, scrolls and tomes, identify,
  keys, the other `pSpell` kinds), each with its draws; P1.2 the grids, the placement search, belt rows, stacking and
  splitting, the cursor, pickup and its refusals, the stash; P1.3 the ground drop's cell search, ground-item lifetime
  and despawn in an active room, and the item request handlers' order inside one drain.
- **Outputs:** `docs/findings/items/00NN-use-inventory.md` (the next free items number); `re/symbols.csv`; a
  `tools/inventory.py` model.
- **Done when:** each batch names its functions with `[I]` or better, the draws per seed, and a list of harness cases
  for Phase 2; one Tier B check per batch. P1.1 also reads the bodies of
  `g_ItemUseFns` entries 1 (test `0x005BE130`, use `0x005BE230`), 4, 7 (`0x005BF0C0`), 8 (`0x005BF060`) and the rejuvenation
  and elixir amounts (flat or percent), and what `useable`, `belt` and the warning columns gate
  ([Misc § Item-use columns](../tables/Misc.md#item-use-columns-plan-0060-phase-0)); P1.2 names the readers of `belts`
  (the row for a worn belt: `Armor.belt` `[I]` matches the box counts; first or second set) and `inventory` (the row
  for a unit and page; first or second set; stash 6 × 4 or 6 × 8; `gridX`/`gridY` width), closing the Open question
  ([Belts](../tables/Belts.md), [Inventory](../tables/Inventory.md)).

### Phase 2 — Harness (one slot)
- **Owner skill:** reverser (harness, one of slots 1–2; MemoryMax=4G)
- **What:** the Phase 1 cases with logged inputs: uses of each potion and scroll kind, belt fills by belt type, stack
  merges, pickups refused and accepted, drops in crowded cells, ground items left past the lifetime.
- **Done when:** each case is predicted by `tools/inventory.py` before it is checked, with 0 mismatches or each
  mismatch explained, and the counts meet the Done-when Phase 1 sets.

### Phase 3 — Spec
- **Owner skill:** spec-writer (Opus)
- **Outputs:** `docs/specs/items/use.md`, `docs/specs/items/inventory.md`; links from the cited specs; row `items/use`.
- **Done when:** a Tier A review accepts it.

### Phase 4 — Wiki
- **Owner skill:** spec-writer (wiki; Sonnet)
- **Done when:** `docs/wiki/items.md` (or its own page) covers it, no claims of its own.

## Resources and limits

- Static batches fit lane A or B when 0052's catalogue or 0055/0054 frees one; never a third static lane. One harness
  slot for one or two lane runs. One Ghidra per batch.
- **Estimate:** P0 one archivist run; P1 three reverser runs; P2 one or two; P3 one or two; P4 one.

## Owner questions (recommendations)

1. **Scope ADR.** *Recommendation: a short ADR beside ADR-0017* ("item use and inventory as game rules; the server's
   outcomes only, the UI out"), drafted by the architect when the plan is approved.
2. **Stash and the cube's moves.** *Recommendation: the stash in; the cube's grid as an inventory page in, its
   transmute stays items/cube's.*
3. **Trading.** *Recommendation: out* (multiplayer/0002 covers the trade test; a full trade flow is a later plan).
4. **Ground-item lifetime.** *Recommendation: in*, it is a server timer a reimplementation must keep.
5. **One slot, after which plans?** *Recommendation: after 0050·P2 part 3 and 0046·P2*, before the companion sweep,
   on whichever slot frees.

## Open questions

- Which of `belts` and `inventory`'s columns the server reads (the client reads the screen coordinates): settled in
  Phase 0's reader survey and Phase 1.2.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 4 (high value, large; scope ADR needed);
  five owner questions.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr2`).** "Approve all of them": all five questions as recommended: the scope ADR is [ADR-0025](../adrs/0025-scope-item-use-inventory.md) (accepted with this approval: the server's outcomes only, beside ADR-0017); the stash in, the cube's grid as an inventory page in, its transmute items/cube's; trading out; the ground-item lifetime in; the slot after 0050·P2 part 3 and 0046·P2, (the companion sweep it was to precede may be drafted but not started, owner 2026-10-30). P0 takes the archivist after 0059·P2 per the run order. Status `approved`.
- **2026-10-30 — Phase 0 landed (archivist, `lane/a60`).** [Belts](../tables/Belts.md) and [Inventory](../tables/Inventory.md) written with their in-memory layouts (`LAYOUTS["belts"]` 14 records × 65 fields, `LAYOUTS["inventory"]` 32 × 72, 0 mismatches; both in the gate's `excel_layout` survey, baseline updated, tables 74 to 76); [Misc § Item-use columns](../tables/Misc.md#item-use-columns-plan-0060-phase-0) lists the use columns with the `g_ItemUseFns` entries read from the pinned image (`[C]`, entries 1..11, only 1 has a `test`) and the handlers the findings name; Books was already complete ([Books](../tables/Books.md)). Surprises: the `inventory`/`belts` `.bin` carry a second set (rows 16..31, 7..13) for the other screen layout; the Druid and Assassin rows are 14 and 15, not 5 and 6; `autobelt` is a subset of `belt` but 8 beltable rows lack it; the bodies of use entries 1, 4, 7, 8 are unread (folded into Phase 1 Done-when). The server-side reader survey for `belts`/`inventory` is the findings' scope notes only, no new xref (no Ghidra in this lane).
