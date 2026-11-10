# 0003 — Player trade: the request, the offer pages, the accepts, the commit and every way out

> **Subsystem:** items/trade (ADR-0033; the row is written in plan 0067 Phase 3)
> **Question:** what does the server do when two players trade, from the request to the commit or the cancel, and
> what would each two-client case of plan 0067 Phase 2 log?
> **Date:** 2026-11-10   **Plan:** 0067 (Phase 1; Phase 2 preparation § 12)   **Status:** answered (static reading; Phase 2 run § 13)

This finding completes [multiplayer/0002](0002-trade-and-party-gold.md) § 2. It covers the whole trade module
(`.\PLAYER\PlrTrade.cpp`, 0x00566B30–0x00568D5B) and every caller of it from outside. Every behavioural claim is a static reading of the pinned
`Game.exe` (objdump and the lane's Ghidra copy `ghidra-n67r`), so it is `[I]`. No session was played. The kept outputs
are in `workspace/logs/n67r/static/`: the module's disassembly (`objdump-trade-module.txt`) and decompile
(`decompile-trade-module.c`), the callers' disassembly, every direct call into the module (`call-sites-trade.txt`,
84 lines), the `0x77` message sites (`pkt77-sites.txt`, 39 lines), the commands (`commands.txt`) and `manifest.txt`
(sha256 of the other 30 files; `sha256sum -c manifest.txt` passes from that directory).

Where § 2 of multiplayer/0002 and this finding differ, this finding holds: the request distance (§ 3), and the gold
offer, which does not un-accept (§ 4). multiplayer/0002 carries a dated note at each place.

## Answer (summary)

- [I] **The state word `PlayerData+0x50` runs 0–16, and three things drive it:** the `0x4F` button packet (buttons 2, 3, 4, 7, 8;
  5, 6 and anything above 8 do nothing), the inventory packets of a trading player, and the event-13 tick
  (`TradeStateTick`), which steps the timed states one or more frames later. Table in § 2.
  (fn:sub_00568060_PktInteractButton@0x00568060, fn:sub_005689D0_TradeStateTick@0x005689D0, 0x00568620)
- [I] **The request** is sent once the requester stands within 8 of the target (a click from 9 to 50 walks there
  first). It needs the requester not busy, no classic end lock, the target not busy, both states 0, neither player
  within 5 000 ms of a closed trade (`+0x58`), and both in a town level. Out of town it clears both interactions.
  There is no hostility, mode or level test of its own. (fn:sub_00548B00_UnitInteract@0x00548B00, 0x00548E00–0x00548E6B,
  fn:sub_00566E60_TradeRequest@0x00566E60)
- [I] **Opening snapshots both inventories.** When the target accepts (button 3), each player gets a trade record
  whose `+0x04` buffer (0x2000 bytes) holds that player's whole item list as the save writes it, and `+0x10` the
  carried gold. Every later cancel, close and abort that reaches `TradeReturnItems` throws away the live inventory of both players
  and rebuilds it from this snapshot, so the items come back as new units. Two ways out do not: a `TradeAbort` whose
  partner does not point back, and waypoint travel (§ 9). (fn:sub_00566B30_TradeRecAlloc@0x00566B30,
  fn:sub_005678F0_TradeReturnItems@0x005678F0, fn:sub_00566CC0_TradeRestoreSnapshot@0x00566CC0)
- [I] **Pages 2 and 1.** An item a player places on page 2 is copied (`ItemCopy`) to the partner's page 1 at the same
  cell, and the pair (original id, copy id) is kept in the placer's record. Taking it off page 2 takes the copy off
  page 1 and sets a 10 000 ms lock in both records. Every inventory move request of a trading player (packets `0x19`,
  `0x1C`–`0x1F`, `0x24`, `0x63`) first puts both players in state 7, which un-accepts both. The same test refuses
  the move when either player has bit 23, when the presser is at 4, for monster equipment (item flag `0x1000`), for a
  cube that holds items, and for a quest item whose code the partner already holds.
  (fn:sub_00568770_TradeShowOffer@0x00568770, fn:sub_00567400_TradeHideOffer@0x00567400,
  fn:sub_00567620_TradeItemTest@0x00567620, fn:sub_00535610_InvMoveInteractTest@0x00535610)
- [I] **A gold offer (button 8) changes no state.** It is clipped to the partner's room under the gold cap, stored at
  the offerer's record `+0x0C`, and sent to both. A player at 4 stays at 4 when the partner changes the amount, and
  the commit takes the amount stored last. An offer above the offerer's carried gold closes the trade. (0x005683DC–0x00568497)
- [I] **The commit** runs when the second player accepts. It tests each side's gold offer against the giver's gold
  and the receiver's cap, then whether both offers fit the partner's page 0 (a scratch copy of each grid, filled in
  the non-player search order), then the quest gate per offered item. Then it sets both states to 9, copies each
  offered item into the partner's page 0 (the player search order), removes both pages 1 and 2, and moves the gold.
  Any failure before the moves cancels with the snapshots. A failure in the moves cancels too, and the snapshots undo the side that already moved.
  (fn:sub_00567C70_TradeCommit@0x00567C70, fn:sub_0063E370_TradeRoomTest@0x0063E370,
  fn:sub_005670E0_TradeMoveItems@0x005670E0)
- [I] **The ways out.** A close (buttons 2 and 3, a gold overspend, a failed offer copy, a deferred close from the
  tick) ends the trade with both inventories restored. A cancel at the commit restores both and leaves the trade open
  at state 3. A player leaving the game, or dying, aborts it with both restored. A level change has no trade code:
  waypoint travel clears the traveller's interaction and leaves both states and records as they were.
  (fn:sub_005679E0_TradeClose@0x005679E0, fn:sub_00567B00_TradeCancel@0x00567B00, fn:sub_00568640_TradeAbort@0x00568640,
  fn:sub_00584F60_WaypointTravel@0x00584F60)
- [I] **Saved mid-trade: the snapshot.** `PLRSAVE_Save` raises a flag when the player's interaction is with another
  player, and the item-list writer then copies the trade record's snapshot instead of the live list. On the route
  that `PLRSAVE_Save` takes for a game byte `+0x6A` of 1 or 2, a player saved mid-trade gets the opening inventory; the two
  other routes (0x00531EB0, 0x00532240) are not followed (§ 10). Whether a leaver is saved depends on `ClientRemove`'s
  argument, unfollowed at its eight callers.
  (fn:PLRSAVE_Save@0x00532400, 0x00532447–0x00532464, fn:sub_00531BB0_SaveItemListOrSnapshot@0x00531BB0,
  fn:sub_005675E0_TradeSnapshotCopy@0x005675E0, fn:sub_00539DA0_ClientRemove@0x00539DA0)
- **Phase 2 cases:** § 11 lists 13 cases with a recipe, logger points and a prediction each, and the ones a stock
  client cannot reach. § 12 holds the logger, the checker, the T13 layout and the run recipe.
- [I] **FIRST and BEST disagree in both directions** under the inventory spec's B1 model: a layout where the room test
  passes and the move fails (T13: four 1 × 2 items into a page with a 2 × 2, a 2 × 4 and two 2 × 3), and layouts where
  the room test refuses a trade that would fit (§ 12.3). (fn:sub_0063E370_TradeRoomTest@0x0063E370,
  fn:sub_005670E0_TradeMoveItems@0x005670E0, `t13-layout.txt`)

## Leads used

- The string `.\PLAYER\PlrTrade.cpp` (0x006E11D8) and multiplayer/0002's function list located the module. Used to
  locate code only. No community document was read for this finding.

## Functions

New rows are `I` with this finding as evidence. Rows multiplayer/0002 named and this finding reads further carry
this finding as evidence now.

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00566B30` | `sub_00566B30_TradeRecAlloc` | the record (0x18 bytes) and its snapshot: `+0x00` bytes written, `+0x04` the 0x2000-byte buffer, `+0x08` the offer map, `+0x0C` the gold offer, `+0x10` carried gold, `+0x14` the lock time; 0 when the player has one (fn:sub_00566B30_TradeRecAlloc@0x00566B30) | I |
| `0x00566BF0` | `sub_00566BF0_TradeRecFree` | frees the record, its buffer and its map (fn:sub_00566BF0_TradeRecFree@0x00566BF0) | I |
| `0x00566C80` | `sub_00566C80_TradeReloadNotifyCb` | per other player: a 6-byte packet naming the reloaded player (fn:sub_00566C80_TradeReloadNotifyCb@0x00566C80) | I |
| `0x00566CC0` | `sub_00566CC0_TradeRestoreSnapshot` | cancels event 9, reads the snapshot back (version `0x60`), resets carried gold to `+0x10` (fn:sub_00566CC0_TradeRestoreSnapshot@0x00566CC0) | I |
| `0x00566D90` | `sub_00566D90_TradeEventMsg` | the 40-byte `0x5A` event to the requester (`DL` the event, a player's name or none) (fn:sub_00566D90_TradeEventMsg@0x00566D90) | I |
| `0x00566E20` | `sub_00566E20_InvHasCubeContents` | 1 when an item of the player is on page 3 (fn:sub_00566E20_InvHasCubeContents@0x00566E20) | I |
| `0x00566E60` | `sub_00566E60_TradeRequest` | the request gates and states 1 and 2 (§ 3) (fn:sub_00566E60_TradeRequest@0x00566E60) | I |
| `0x00567020` | `sub_00567020_TradeOpen` | both states 3, `0x77` code 6 to both (fn:sub_00567020_TradeOpen@0x00567020) | I (existing) |
| `0x00567070` | `sub_00567070_TradeItemRename` | an ear's or a personalised copy's name (fn:sub_00567070_TradeItemRename@0x00567070) | I |
| `0x005670E0` | `sub_005670E0_TradeMoveItems` | copies one side's page 2 into the other's page 0, then removes its pages 1 and 2 (§ 8) (fn:sub_005670E0_TradeMoveItems@0x005670E0) | I |
| `0x005672D0` | `sub_005672D0_TradeItemsAllowed` | `ItemQuestGate` per page-2 item (fn:sub_005672D0_TradeItemsAllowed@0x005672D0) | I |
| `0x00567330` | `sub_00567330_CubeInteractEnd` | clears a cube interaction (the module's one cube helper) (fn:sub_00567330_CubeInteractEnd@0x00567330) | I |
| `0x00567350` | `sub_00567350_TradeOfferMapAdd` | adds (original id, copy id) to the placer's record `+0x08` (fn:sub_00567350_TradeOfferMapAdd@0x00567350) | I |
| `0x005673C0` | `sub_005673C0_TradeOfferMapFind` | finds the copy id of an original id (fn:sub_005673C0_TradeOfferMapFind@0x005673C0) | I |
| `0x00567400` | `sub_00567400_TradeHideOffer` | an item left page 2: the copy off page 1, the 10 000 ms lock, a 4 back to 3 (§ 5) (fn:sub_00567400_TradeHideOffer@0x00567400) | I |
| `0x005675E0` | `sub_005675E0_TradeSnapshotCopy` | copies the snapshot into the save buffer when it fits (fn:sub_005675E0_TradeSnapshotCopy@0x005675E0) | I |
| `0x00567620` | `sub_00567620_TradeItemTest` | the change lock and the move refusals (§ 5) (fn:sub_00567620_TradeItemTest@0x00567620) | I (existing) |
| `0x00567840` | `sub_00567840_TradeBeltLock` | 0 while in a player interaction with an item in the belt (fn:sub_00567840_TradeBeltLock@0x00567840) | I |
| `0x005678F0` | `sub_005678F0_TradeReturnItems` | discards the live inventory and rebuilds it from the snapshot (§ 9) (fn:sub_005678F0_TradeReturnItems@0x005678F0) | I |
| `0x005679E0` | `sub_005679E0_TradeClose` | both restored, records freed, the presser's final state and the partner's 9 (fn:sub_005679E0_TradeClose@0x005679E0) | I |
| `0x00567B00` | `sub_00567B00_TradeCancel` | both restored, offers 0, records kept, states 5 (fn:sub_00567B00_TradeCancel@0x00567B00) | I |
| `0x00567C70` | `sub_00567C70_TradeCommit` | the checks and the exchange (§ 8) (fn:sub_00567C70_TradeCommit@0x00567C70) | I |
| `0x00568640` | `sub_00568640_TradeAbort` | a player leaving or dying: both restored, both states 9 (fn:sub_00568640_TradeAbort@0x00568640) | I |
| `0x00568760` | `sub_00568760_TradeAbortThunk` | a jump to `TradeAbort` (the death path) (fn:sub_00568760_TradeAbortThunk@0x00568760) | I |
| `0x00568770` | `sub_00568770_TradeShowOffer` | an item placed on page 2: its copy on the partner's page 1 (§ 5) (fn:sub_00568770_TradeShowOffer@0x00568770) | I |
| `0x005689D0` | `sub_005689D0_TradeStateTick` | the timed steps (§ 2) (fn:sub_005689D0_TradeStateTick@0x005689D0) | I |
| `0x00568D10` | `sub_00568D10_TradeSelfReload` | a record, a reload from it and a free; no reference to it found (fn:sub_00568D10_TradeSelfReload@0x00568D10) | I |
| `0x00597A20` | `sub_00597A20_TradeBlocked` | `Unit+0xC8` bit 22 or 23, or a queued item update whose unit still exists (fn:sub_00597A20_TradeBlocked@0x00597A20) | I |
| `0x0063E370` | `sub_0063E370_TradeRoomTest` | both offers against scratch copies of the partners' page 0 (§ 8) (fn:sub_0063E370_TradeRoomTest@0x0063E370) | I |
| `0x0063E100` | `sub_0063E100_InvScratchCopyGrid` | copies a player's page-0 cells into a scratch inventory (fn:sub_0063E100_InvScratchCopyGrid@0x0063E100) | I |
| `0x0063E2E0` | `sub_0063E2E0_InvScratchFitOffer` | places each page-2 item of a unit into a scratch grid (fn:sub_0063E2E0_InvScratchFitOffer@0x0063E2E0) | I |
| `0x0063E1C0` | `sub_0063E1C0_InvScratchPlace` | `InvSpotFindBySize` on the scratch, then marks the cells (fn:sub_0063E1C0_InvScratchPlace@0x0063E1C0) | I |
| `0x0063E0B0` | `sub_0063E0B0_InvUnlinkAll` | removes every item from an inventory, cursor word 0 (fn:sub_0063E0B0_InvUnlinkAll@0x0063E0B0) | I |
| `0x00531BB0` | `sub_00531BB0_SaveItemListOrSnapshot` | the save's item list: the snapshot when flagged and present, else `ITEMS_WriteInventoryList` (fn:sub_00531BB0_SaveItemListOrSnapshot@0x00531BB0) | I |
| `0x00535610` | `sub_00535610_InvMoveInteractTest` | the inventory packets' interaction test: trade, NPC or none (fn:sub_00535610_InvMoveInteractTest@0x00535610) | I |
| `0x005350F0` | `sub_005350F0_InteractEndOnDeath` | `PlayerDeath`'s end of an interaction; a player one aborts the trade (fn:sub_005350F0_InteractEndOnDeath@0x005350F0) | I |
| `0x005351C0` | `sub_005351C0_InteractEndForcedMove` | `A4Q2_EndMovePlayer`'s end of an interaction; a player one presses button 6 (fn:sub_005351C0_InteractEndForcedMove@0x005351C0) | I |
| `0x00539DA0` | `sub_00539DA0_ClientRemove` | a client leaves the game: save, then the player's interactions ended (fn:sub_00539DA0_ClientRemove@0x00539DA0) | I |
| `0x00563350` | `sub_00563350_ItemCopySockets` | copies an item's socketed children into its copy (fn:sub_00563350_ItemCopySockets@0x00563350) | I |
| `0x0055FA40` | `sub_0055FA40_InvBookSkillsRebuild` | tome and scroll skill quantities recounted over page 0 (fn:sub_0055FA40_InvBookSkillsRebuild@0x0055FA40) | I |
| `0x0055F9C0` | `sub_0055F9C0_ItemBookSkillRemove` | an item's book skill taken off its owner (fn:sub_0055F9C0_ItemBookSkillRemove@0x0055F9C0) | I |
| `0x0055FCC0` | `sub_0055FCC0_InvDetachWorn` | detaches worn items and active charms, then `InvUnlinkAll` (fn:sub_0055FCC0_InvDetachWorn@0x0055FCC0) | I |
| `0x00557FD0` | `sub_00557FD0_ItemFreeNotify` | tells every player, then frees the unit (fn:sub_00557FD0_ItemFreeNotify@0x00557FD0) | I |
| `0x00463720` | `sub_00463720_UnitTestFlags` | `Unit+0xC8 & EDX ≠ 0` (fn:sub_00463720_UnitTestFlags@0x00463720) | I |
| `0x0053CAB0` | `sub_0053CAB0_SendTrade77` | packet `0x77`, 2 bytes, `DL` the code (fn:sub_0053CAB0_SendTrade77@0x0053CAB0) | I |
| `0x0053CAD0` | `sub_0053CAD0_SendTrade78` | packet `0x78`, 21 bytes: the partner's name and unit id (fn:sub_0053CAD0_SendTrade78@0x0053CAD0) | I |
| `0x0053CBE0` | `sub_0053CBE0_SendGold79` | packet `0x79`, 6 bytes: which side, the amount (fn:sub_0053CBE0_SendGold79@0x0053CBE0) | I |
| `0x0053B3D0` | `sub_0053B3D0_SendUnitPacket6` | a 6-byte packet, opcode in `DL`, a unit id (fn:sub_0053B3D0_SendUnitPacket6@0x0053B3D0) | I |
| `0x0053C850` | `sub_0053C850_SendEvent5A` | packet `0x5A`, 40 bytes (fn:sub_0053C850_SendEvent5A@0x0053C850) | I |
| `0x00621000` | `sub_00621000_UnitMarkChanged` | `Unit+0xC8` bits 0 (and 1 for a player) (fn:sub_00621000_UnitMarkChanged@0x00621000) | I |
| `0x00628170` | `sub_00628170_ItemDataFlags14` | sets or clears bits of ItemData `+0x14` (fn:sub_00628170_ItemDataFlags14@0x00628170) | I |
| `0x0063CC70` | `sub_0063CC70_InvQueueItemUpdate` | appends an item id to the inventory's update list (fn:sub_0063CC70_InvQueueItemUpdate@0x0063CC70) | I |

## Walkthrough

### 1. How the server reaches the trade code

[I] `call-sites-trade.txt` lists every direct `call` or `jmp` to the 28 function entries of the module from 0x00566B30
up, 84 lines. Those from outside the module, with the event slot, are every way in
(`findptr.txt`: the tick's only reference is the event table slot 0x006E1844):

| Entry | From | What |
|---|---|---|
| `TradeRequest` | `UnitInteract` 0x00548E6B | the request (§ 3) |
| `PktInteractButton` | `Pkt4FButton` 0x0054C7F0; `InteractEndForcedMove` 0x00535244 | the buttons (§ 4) |
| `InvMoveInteractTest` → `TradeItemTest` | packets `0x19` 0x0054AD46, `0x1C` 0x0054AEFE, `0x1D` 0x0054AFE7, `0x1E` 0x0054B0B0, `0x1F` 0x0054B189, `0x24` 0x0054B481, `0x63` 0x0054D5DB | the change lock (§ 5) |
| `TradeShowOffer` | `InvPlaceItem` 0x005603D9; `BeltOverflow` 0x00560BF2, `CubeDropEmptied` 0x00563B62, `PageSwapCursor` 0x00561E0D | page 2 → partner's page 1 (§ 5) |
| `TradeHideOffer` | `InvItemToCursor` 0x0056063F | off page 2 (§ 5) |
| `TradeBeltLock` | packets `0x1C` 0x0054AF10, `0x1D` 0x0054AFCC | § 5 |
| `InteractIsPlayer` | 14 sites, listed in § 5 | refusals while trading |
| `TradeAbort` | `ClientRemove` 0x0053A091; via the thunk, `InteractEndOnDeath` 0x00535169 | § 9 |
| `TradeSnapshotCopy` | `SaveItemListOrSnapshot` 0x00531BD6 | § 10 |
| `TradeEventMsg` | `PlayerHostileToggle` 0x005A5F37 | a message only |
| `CubeInteractEnd` | 0x00535196, 0x00535269 | the cube, not the trade |
| `TradeStateTick` | event 13, slot 0x006E1844 | § 2 |

- [I] No other entry exists in the direct calls; the module's internal calls make up the other lines. Indirect calls into the module were looked for only at
  the tick (`findptr`), and at `TradeSelfReload` (0x00568D10), which has no reference of any kind (`findptr2.txt`).
  (0x00568D10–0x00568D5B)

### 2. The states, the flags and the tick

[I] Writers of `PlayerData+0x50` (`PlayerData` = `Unit+0x14`, fn:UNIT_GetPlayerData@0x006221A0), all in the module:

| State | Set by | Left by |
|---|---|---|
| 0 | the tick from 10 or 13 | the request |
| 1 / 2 | `TradeRequest`: requester 1, target 2 | button 3 (open), button 2 or 3 (close) |
| 3 | `TradeOpen`; button 7 from 4; the tick from 6, from 8 with no lock, from 11 once the lock passed; `TradeShowOffer` and `TradeHideOffer` when either side is at 4 | button 4 (to 4); a move request (to 7) |
| 4 | button 4 at 3 | button 7, a move (7), `TradeShowOffer`/`TradeHideOffer` (3), the commit (9) |
| 5 | `TradeCancel` | the tick: 5 → 6 (+1 frame) → 3, bits 22 and 23 cleared |
| 7 | `TradeItemTest`, both players | the tick: 7 → 8 (+1); at 8 bit 22 cleared, then 11 (+125 frames) when the record's `+0x14` is set, else 3 |
| 9 | `TradeClose` (the partner, and the presser on code 9), `TradeAbort` (both), the commit (both) | the tick: 9 → 10 (+1) → 0 |
| 11 | the tick from 8 | the tick, every 25 frames: once `GetTickCount() > +0x14` (unsigned), 3, bits 22 and 23 cleared, `+0x14` = 0, `0x77` code `0x0F` |
| 12 | `TradeClose` with code 12 (the presser) | the tick: 12 → 13 (+4) → 0 |
| 14 / 15 / 16 | button 3 while blocked, from 7 / 8 | the tick: 14 → 15 (+1); 15 → 16 (+5), bit 22 cleared; 16: `TradeClose(…, 12)` when both are in {1, 2} or neither is blocked, else again in 5 frames |

(0x005689D0–0x00568C90, the switch table 0x00568CE4; every tick re-queue is `UnitQueueEvent(13, frame + n)`,
fn:sub_005417D0_UnitQueueEvent@0x005417D0)

- [I] Unit flags `+0xC8`: bit 22 is set on the mover by `TradeItemTest` (0x0056779C) and cleared at state 8 or 15;
  bit 23 is set on both by `TradeClose`, `TradeCancel` and the commit, and cleared with bit 22 when the tick reaches
  3 from 6 or 11, or 0. `TradeBlocked` is either bit, or an item id in the inventory's update list
  (`InvQueueItemUpdate`, read through `0x0063CBB0`/`0x0063CD20`) that `GameFindUnit` still finds. (0x00597A20–0x00597A8F,
  0x00568C93–0x00568CD7)
- [I] A state of 4 or less is not touched by the tick (`cmp` with 4 at 0x005689E5, the `4 < state` test). States 5
  and 6 queue nothing at 6, so 6 → 3 happens on the tick queued at 5. (0x00568C6A–0x00568C9A)

### 3. The request

- [I] `UnitInteract`'s player-target case: with `d = UnitInteractDistance(requester, target)`, `d > 50` (unsigned)
  does nothing, `9 ≤ d ≤ 50` starts a walk (`InteractWalkTo`), and `d ≤ 8` calls `TradeRequest(game, requester,
  target)`, except that a target in mode `0x11` with neither unit in a live player interaction goes to
  `PLAYER_CorpsePickup`. *This corrects multiplayer/0002's "distance test ≤ 50": 50 is the walk bound.*
  (0x00548DF9–0x00548E6B, fn:sub_00641530_UnitInteractDistance@0x00641530, player/0001 § Rows 3 and 30)
- [I] `TradeRequest` (`EDX` requester, stack target), in order (`t` = `GetTickCount`, every difference unsigned)
  (fn:sub_00566E60_TradeRequest@0x00566E60):
  1. requester `PlayerIsBusy` (an interaction, a cursor item or `PlayerData+0x4C`), or `A4Q2_ClassicEndLock`: return,
     no message. (0x00566E6A–0x00566E82)
  2. target busy: if `t − req+0x54 > 1000`, event `8` to the requester naming the target, `req+0x54 = t`. (0x00566EA8–0x00566ECF)
  3. `t − target+0x58 < 5000` (the target ended a trade under 5 s ago): if `req+0x54 + 1000 < t`, event `9` naming the
     target and `req+0x54 = t`. (0x00566EDB–0x00566F02)
  4. either state ≠ 0: return. (0x00566F10–0x00566F1E)
  5. `t − req+0x58 < 5000`: if `t > req+0x54 + 1000`, event `9` with no name and `req+0x54 = t`. (0x00566F24–0x00566F4C)
  6. both in a town level (`LevelIsTown` of each room's level): both interactions set (kind 0, the other's id),
     `0x77` code 0 to the requester and 1 to the target, states 1 and 2. Otherwise both interactions cleared.
     (0x00566F58–0x0056700A)
- [I] No hostility test: `TradeRequest`'s callees are the busy, end-lock, tick, room, town and interaction functions
  above and the message senders (xrefs1.txt). `PlayerHostileToggle` reaches the module only through `TradeEventMsg`.
  (0x005A5F37)

### 4. The buttons

[I] `PktInteractButton(button, param)` (`EDX` presser; `Pkt4FButton` passes `u16 +1` and `(u16 +3) << 16 | u16 +5`).
The stash (`0x12`–`0x14`) and cube (`0x17`, `0x18`) buttons are taken first. Any other button needs an interaction of
kind 0: no interaction at all gives `0x77` code `0x0C`, another kind code `0x0D` and a return of 3. When the partner's
unit is gone, a blocked presser gets nothing, else code `0x0C` (0x005685C7–0x005685EB). The switch table 0x00568620 holds 7 entries for buttons 2–8: 2 → 0x00568175, 3 → 0x005681FC,
4 → 0x00568499, 5 and 6 → 0x005684FD (the exit), 7 → 0x0056857F, 8 → 0x005683DC; above 8 the `ja` exits.
(`jumptable-568620.txt`, 0x0056816E)

- [I] **2:** when both states are in {1, 2}, or neither player is `TradeBlocked`: `TradeClose(…, 9)` and both `+0x58`
  = `t`. (0x00568175–0x005681F7)
- [I] **3:** when either is blocked: a presser in 7 goes to 14, in 8 to 15, else `TradeClose(…, 12)`. Else the end
  lock closes with 9, and a presser not in 2 or a partner not in 1 closes with 12. Else `TradeOpen` (both 3), then
  `TradeRecAlloc` twice (a second failure frees the first record), then `0x78` with each one's partner name and id.
  So pressing 3 inside an open trade (state 3) closes it with 12. (0x005681FC–0x005683D7)
- [I] **4:** either blocked: `0x77` code 6 to the presser; end lock: close 9; presser not at 3: code 6; an item on the
  presser's cursor: code 6. Else code `0x05`, the presser to 4, and if the partner is at 4,
  `TradeCommit(presser = A, partner = B)` and both `+0x58` = `t`. (0x00568499–0x00568573)
  *Corrected at Phase 2's preparation (`lane/n67p`): the pushed `0xBEE`, `0xBD2`, `0xBD7` and `0xBDC` that the first
  text gave as codes are `PlrTrade.cpp` line arguments of the client lookup 0x005531C0 (`EDX` = 0x006E11D8, the file
  name); the `0x77` code is `DL` at the send. The first three reach the one send at 0x005684F8 with `DL` 6 (the jumps
  from 0x00568529 and 0x0056857A to 0x005684E8). The same holds for every 4-digit "code" of the commit (§ 8).*
- [I] **7:** each side at 4 goes to 3, codes to both. (0x0056857F–0x005685C2)
- [I] **8** (`param` the amount, u32): when `stat14(presser) < param` (unsigned, 0x005683E6), and neither is blocked,
  `TradeClose(…, 9)`. Otherwise `param` is clipped to `GoldCap(partner) − stat14(partner)` when the sum passes the cap
  (unsigned, 0x0056843C–0x00568448). If the presser has a record, `+0x0C = param` and `0x79` goes to both
  (0x00568467). **No state is read or written**: a partner at 4 stays at 4, and the commit reads `+0x0C` as stored
  last. Before the window opens (no record), button 8 stores nothing but can still close the trade on an overspend.
  *This corrects multiplayer/0002 § 3's "a change of the offer after one accept un-accepts both", which holds for an
  item and not for gold.* (0x005683DC–0x00568497)

### 5. The offer pages and the change lock

- [I] **Placing on page 2.** `InvPlaceItem` calls `TradeShowOffer(item)` after a successful placement when the owner
  is a player and the item's page is 2 (the flag at 0x005602AE, its test at 0x005603CD, the call 0x005603D9). `TradeShowOffer` (`EDX` the placer): no player
  interaction: code `0x0C`; partner gone: code `0x0C`. Else `ItemCopy`, the copy in mode 4 on page 1, and
  `InvPlaceItem(game, partner, copy, x, y, exact, 1, 0)` at the original's cell (`PathGetX`/`Y` of its path, or `+0x0C`/`+0x10`
  of a static path). On success it copies socketed children (`ItemCopySockets`), adds (original id, copy id) to the
  placer's record map, and when either state is 4 sends `0x79` four times and calls `TradeOpen` (both 3). On failure
  it frees the copy (`ItemFreeNotify`) and `TradeClose(…, 9)`. (0x00568770–0x005689CD)
- [I] Its three other callers (`BeltOverflow`, `CubeDropEmptied`, `PageSwapCursor`) were not read for when they reach
  it. (0x00560BF2, 0x00563B62, 0x00561E0D)
- [I] **Taking off page 2.** `InvItemToCursor` calls `TradeHideOffer(item)` when the owner is a player, the page was
  2 and its `param_3` is 1 (the page flags 0x005605AC–0x005605C5, the tests 0x00560620 and 0x00560634, the call 0x0056063F). `TradeHideOffer`: no player interaction: code; partner gone: code.
  Else it finds the copy in the placer's map and calls `InvItemToCursor(partner, copy, …, 1, 1, 0, 1)`. That takes
  the copy off page 1, and page 1 never sets the cursor word (0x00560603–0x0056060E). The map entry is not removed: the loop after it
  is empty (0x005674D4–0x005674D9). Then both records' `+0x14` = `t + 10 000`, codes to both, and when either state is
  4, `0x79` four times and `TradeOpen`. Whether the copy unit is freed is not followed. (0x00567400–0x005675D8)
- [I] **The change lock.** `InvMoveInteractTest` (0x00535610), called by the seven inventory packets of § 1 before
  they move anything: no interaction and `PlayerData+0x4C` ≠ 0, or an interaction whose unit is gone (cleared), returns 0;
  kind 1 (an NPC) goes to `0x00573140`; every other case goes to `TradeItemTest(item)`. `TradeItemTest`, in order:
  1. no interaction: returns `state ≤ 4` (`setle`); kind ≠ 0: returns 1; partner gone: returns `state ≤ 4`.
     (0x0056763F–0x00567671, 0x00567829–0x0056783B)
  2. the partner has no record, the end lock, or bit 23 on the mover or the partner (`UnitTestFlags(…, 0x800000)`):
     returns 0, nothing else. (0x0056767D–0x005676BA)
  3. `r = (mover's state ≠ 4)`. For an item: a base with `quest` (Items `+0x12A`): a cube (`box `) while the mover has an item on page 3
     gives `r = 0` and event `0x0A` to the mover; then `PlayerFindItemByCode(partner, code)` found gives `r = 0`. A base
     without `quest` and item flag `0x1000` gives `r = 0`; otherwise `ITEMS_GetQuality` is called and its result unused.
     (0x005676E4–0x00567793, items/0010 for `PlayerFindItemByCode` and flag `0x1000`)
  4. **Whatever `r` is**: bit 22 on the mover, both states 7, event 13 for both at the next frame, `0x77` code 6 to both,
     return `r`. (0x00567798–0x00567826)

  A return of 0 makes the packet handler return without the move (`je` at 0x0054AD4D for `0x19`). So a refused move
  still un-accepts both players. The test runs on the pick-up from page 0 too, not only on pages 1 and 2.
- [I] `0x18` (cursor to page) does not call the test; it places on page 2 only while `InteractIsPlayer` holds (the
  inventory spec's E1), and an accept needs an empty cursor (button 4), so a pick-up (`0x19`) with its lock comes
  before any placement. (fn:sub_0054ABB0_Pkt18CursorToPage@0x0054ABB0, 0x00568499–0x00568573)
- [I] **The belt lock.** For body slot 8 (the belt), `0x1C` and `0x1D` call `TradeBeltLock` after the change lock:
  in a player interaction it returns 0 when any item's location byte (ItemData `+0x69`) is 2, the belt
  (`InvGridPut`'s writer, 0x0063B1CF). So the belt cannot be taken off or swapped while it holds a potion, and the
  states still went to 7. (0x0054AF07–0x0054AF17, 0x00567840–0x00567897, `objdump-locbyte.txt`)
- [I] **Refused while trading.** `InteractIsPlayer` (an interaction of kind 0 whose unit exists) is tested by
  `Pkt17CursorDrop`, `Pkt18CursorToPage`, `PlayerUseInvItem`, `PlayerUseItemOnItem`, `PlayerUseBeltItem`,
  `0x005628C0`, `0x0054C380` (a 17-byte packet), `0x0054C800` (the gold drop: busy and in a player interaction
  returns 3), `Pkt61MercItem`, `A2Q6_StaffPartyCredit`, `A3Q5_OrbPartyPass`, `ItemUseIdentify` and `UnitInteract`
  (twice, § 3); 14 sites (xrefs4.txt). What each refusal returns is read only for `0x0054C800` and `0x0054C380`.
  (0x0054C380–0x0054C3D7, 0x0054C800–0x0054C86C)

### 6. The trade record and the snapshot

- [I] `TradeRecAlloc` (`EBX` the player) returns 0 when `PlayerData+0x5C` is set. Else it allocates the record and a
  buffer, writes `+0x00 = SaveItemListOrSnapshot(buffer, 0x2000, 0, 0, 0)`, the player's live item list in the save
  format, and stops the game (error `0x809`) if that is below 1. Then `+0x08 = +0x0C = +0x14 = 0` and
  `+0x10 = stat14(player)`. (0x00566B30–0x00566BDC)
- [I] `TradeRestoreSnapshot` (`EDX` the player): calls the empty `0x0063BE30` for 1–12, cancels the player's event 9,
  reads the buffer back with `ItemListReadByVersion(buffer, 0x60, 0x2000, 0, …)`, and when carried gold is above 0 and
  the player's mode is neither 0 nor 17, sets carried gold to `+0x10` by two adds (`−gold`, then `+0x10`). A player
  with 0 gold, or dead, keeps the current gold. (0x00566CC0–0x00566D89, fn:sub_005337F0_ItemListReadByVersion@0x005337F0)

### 7. The gold offer at the commit

Unchanged from multiplayer/0002 § 2: each side's offer is tested (`stat14(giver) < offer`, signed `jge` → cancel;
`stat14(receiver) + offer > GoldCap(receiver)`, unsigned → cancel with codes), first A's, then B's, and moved last.
[I] (0x00567C70–0x00567D8C, 0x00567F4A–0x00567FCC)

### 8. The commit

```c
// fn:sub_00567C70_TradeCommit@0x00567C70 (trimmed); A = EAX, the second to accept; B the partner
gold tests (§ 7)                                              // a failure: TradeCancel
side = 0; if (!TradeRoomTest(game->+0x1C, A, B, &side)) {     // 0x00567DD0
    pdA.rec->offer = pdB.rec->offer = 0;
    0x77 to A then B: 0x0A, 9 when side == 0 (A's offer does not fit B), 9, 0x0A when side == 1; TradeCancel; return; }
if (!TradeItemsAllowed(…) || !TradeItemsAllowed(…)) { TradeCancel; return; }   // 0x00567E94, 0x00567EA9
A, B: +0xC8 |= 0x800000; both states 9; event 13 for both at frame + 1
if (!TradeMoveItems(A → B)) { TradeCancel; return; }           // 0x00567F17
if (!TradeMoveItems(B → A)) { TradeCancel; return; }           // 0x00567F3D
gold: A's offer, then B's; both interactions cleared; both records freed; book skills recounted; 0x77 code 0x0D to both
```

- [I] **The room test.** `TradeRoomTest(pool, A, B, &side)` makes two scratch inventories (`0x40` bytes, magic
  `0x01020304`, `+0x08` owner **0**) and copies into them the page-0 cells of A and of B (`InvScratchCopyGrid`:
  `InvRowForUnit(unit, 0, 1)`, the same grid size, `memcpy`). It then places A's page-2 items, in A's item-list order,
  into B's copy (`InvScratchFitOffer(A, B's copy, row of B)`); a failure sets `side = 0`. Then B's into A's copy;
  a failure sets `side = 1`. Each placement is `InvSpotFindBySize(scratch, item, row, &x, &y, 0)` followed by the
  cells set to `−1`, so the offers pack one after another. Returns 1 only when both fit; frees both scratches.
  (0x0063E370–0x0063E47F, 0x0063E100–0x0063E1B8, 0x0063E2E0–0x0063E367, 0x0063E1C0–0x0063E2D6)
- [I] **Two search orders.** A scratch's owner is 0, so `InvSpotFindBySize` takes the non-player orders (FIRST) of
  the inventory spec's B1. The real placement in `TradeMoveItems` goes into the player's own inventory through
  `InvPlaceAnywhere`, whose search takes the player orders (BEST). The two can disagree on a crowded page. A test that
  passes with a placement that fails ends in `TradeMoveItems` returning 0 and a cancel (below). A test that fails where
  the placement would fit refuses a trade that fits. Both exist under the B1 model (§ 12.3, the T13 search). (0x0063E3B4, 0x0063E3F1,
  fn:sub_0063B850_InvSpotFindBySize@0x0063B850, fn:sub_0063B950_InvPlaceAnywhere@0x0063B950, items/inventory § B1)
- [I] **`TradeMoveItems(X → Y)`.** First pass over X's item list: for each item on page 2, `ItemCopy`; a copy of 0
  skips the item (the `while` at 0x00567137–0x00567150), and the second pass still removes the original. Otherwise
  `TradeItemRename`, mode 4, page 0, `InvPlaceItem(game, Y, copy, 0, 0, anywhere, 1, 0)`. A failed placement:
  codes, return 0. Socketed children are copied after it (`ItemCopySockets`); a failure there: codes, return 0.
  Second pass: every item of X on page 1 or 2 is removed (page 2 first loses its book skill), with a packet and
  `0x0055DF10(item, 0)` (not followed). Returns 1. (0x005670E0–0x005672A0)
- [I] **A failure after the first move.** When `TradeMoveItems(A → B)` succeeded and `(B → A)` fails, A's offer is
  already in B's page 0 and A's pages are empty. `TradeCancel` then rebuilds both inventories from their opening
  snapshots, which brings A's items back and drops B's copies. The gold has not moved. So the snapshot undoes a half
  commit. (0x00567F3D–0x00567F4A, § 9)

### 9. The ways out

- [I] **`TradeReturnItems(game, player)`** (the stack argument is popped by `ret 4` and never read): when the player
  has a record, a `0x92` packet naming the player to it and to each other player (`TradeReloadNotifyCb`). Then for
  every item in the inventory list: in mode 0, `ItemBookSkillRemove`; then `InvQueueItemUpdate` and ItemData `+0x14`
  bit 0. The cursor item the same. Then `InvDetachWorn` (worn items and active charms detached, then
  `InvUnlinkAll`: every item removed from the inventory, the cursor word 0) and `TradeRestoreSnapshot`. So the whole
  inventory (pages, body, belt, cube, stash, cursor) is replaced by the opening snapshot, and every item comes back as
  a unit read from the bytes. Whether the old units are freed is not followed. (0x005678F0–0x005679D6,
  0x0055FCC0–0x0055FDA3, 0x0063E0B0–0x0063E0F9)
- [I] **`TradeClose(game, presser, partner, pdP, pdQ, code)`**: both marked changed, bit 23 on both, both
  interactions cleared, `TradeReturnItems` for both, both records freed, presser state = `code` (9 or 12), partner 9,
  book skills recounted, `0x77` code `0x0C` to both, both event 13 cancelled and queued at frame + 1.
  Callers: buttons 2, 3, 4 and 8, `TradeShowOffer`'s failed copy, and the tick at 16. (0x005679E0–0x00567AF3, xrefs1.txt)
- [I] **`TradeCancel(pdA, pdB)`** (the commit's 8 failures): book skills recounted, both marked changed, bit 23 on
  both, both offers 0, `TradeReturnItems` for both, `0x79` four times, `0x77` code 6 to both, both states 5, event 13
  at frame + 1. The records and interactions stay: after 5 → 6 → 3 the window is open again with empty pages
  and no offers. (0x00567B00–0x00567C62)
- [I] **`TradeAbort(game, leaver)`**: only when the leaver's interaction is kind 0 with a unit that exists, and that
  unit's interaction points back at the leaver. Then: the leaver's interaction cleared, leaver state 9 and event 13,
  `TradeReturnItems` for the leaver and the partner, both records freed, `0x77` code `0x0C` to the partner, the
  partner's interaction cleared, partner state 9 and event 13. When the partner's interaction does not point back,
  only the leaver's interaction is cleared: no state, no restore, the records kept. (0x00568640–0x00568759)
- [I] **Leaving the game.** `ClientRemove` saves first when its argument is 1 (`SaveClients`, 0x00539E03), and later, for
  the client's player, calls `0x005407A0`, `0x005746D0`, `TownPlayerRemove`, `QuestsInvItemEvent` and `TradeAbort` (0x0053A091)
  before the unit is freed. Its eight callers (xrefs2.txt) were not read for the argument they pass.
  (fn:sub_00539DA0_ClientRemove@0x00539DA0, fn:sub_0052C900_SaveClients@0x0052C900)
- [I] **Death.** `PlayerDeath` calls `InteractEndOnDeath` (0x00581012): kind 0 goes to `TradeAbort` through the thunk;
  kinds 1, 2 and the cube have their own ends. (0x005350F0–0x0053519B, fn:sub_00580EC0_PlayerDeath@0x00580EC0)
- [I] **The Act IV end move** calls `InteractEndForcedMove`, whose kind-0 case presses button 6, which the switch
  ignores. The trade is not ended there. (0x00535244, 0x005B4A96)
- [I] **A level change.** No caller of the module sits in a level-change path (§ 1). `Pkt49WaypointTravel` and
  `WaypointTravel` clear the traveller's interaction of any kind (`PlayerClearInteract`, 0x0054C622, 0x0054C669,
  0x00584FCD) with no busy or trade test of their own. `WaypointTravelCheck` (object, act, distance, waypoint bit) was
  not re-read for one. So a waypoint packet from a trading player would leave town with both states and records as they
  were, and the partner's interaction still pointing at the traveller; that partner's later `TradeAbort` would find no
  back-pointer. A stock client's trade window may never send it (Open questions).
  (fn:sub_0054C5D0_Pkt49WaypointTravel@0x0054C5D0, fn:sub_00584F60_WaypointTravel@0x00584F60)
- [I] `TradeSelfReload` (0x00568D10) would allocate a record (a fresh snapshot), reload from it, free it, recount
  book skills and queue event 13: a reload of a player's own inventory. No reference to it was found (§ 1).

### 10. The save mid-trade

- [I] `PLRSAVE_Save` sets a local flag to 1 when `PlayerGetInteract` returns non-zero and the kind is 0
  (0x00532447–0x00532464), and passes it to each of its three routes (0x005324C2, 0x005324DF, 0x005324F2). On the
  route at 0x00532340 (taken when the game's byte `+0x6A` is 1 or 2, 0x0053249D–0x005324AD) it becomes `D2S_WriteSave`'s fourth stack argument (0x0053236C–0x00532371),
  and `D2S_WriteSave` passes that as `D2S_WriteItemList`'s third (0x00569BC5–0x00569BD3). The two other routes (the calls to 0x00531EB0 at 0x005324D2 and to 0x00532240 at 0x005324EB) were
  not followed to `D2S_WriteSave`. (fn:PLRSAVE_Save@0x00532400, fn:D2S_WriteSave@0x00569AD0, `objdump-plrsave-save.txt`)
- [I] `SaveItemListOrSnapshot(buf, room, flag, …)` (`EDX` the unit): when `flag ≠ 0`, the unit is a player and
  `TradeSnapshotCopy` returns non-zero, the list is the snapshot. `TradeSnapshotCopy` copies the record's `+0x00`
  bytes from `+0x04` when the player has a record and `+0x00 ≤ room` (signed), and returns that count. Otherwise
  `ITEMS_WriteInventoryList` writes the live list. `D2S_WriteMercItems` passes flag 0. (0x00531BB0–0x00531BFB,
  0x005675E0–0x00567616, 0x005699DD)
- [I] So a player saved with an open trade record (from the target's accept to the end) is saved with the items as
  they were at opening, and the carried gold as it is (the trade moves no gold before the commit). In the request phase
  (no record) the live list is saved. Corpses' lists pass the flag through (0x00569962–0x00569976) and a corpse unit
  was not checked against the player test.

### 11. The Phase 2 case list

**Common set-up** (ADR-0008, [tooling § Two clients](../../../.claude/skills/reverser/references/tooling.md)): slot 1
hosts with gdb (H), slot 2 joins (J); `tools/ufwcheck.sh … || exit 1` before each hosting session; both characters
level 9 or more, in the Rogue Encampment, from `tools/d2s.py`-built saves with known items at known cells. Steps
through `d2pilot.py join … trade request|accept|give:inv:c,r>tr:c,r|ok|key:K|xy:X,Y|sleep:S|shot:P`. The gold-offer
button, its entry box and the trade window's close control are not measured yet: the first session measures them
(an `xy:` token and screenshots) and records which button codes the stock client sends for "close" and for the
gold entry.

**Logger** (new `tools/gdb/two-trade.gdb` + `.py`, on the host, read-only, ADR-0003): at every point it prints both
players' unit ids, `PlayerData+0x50`, `+0x54`, `+0x58`, `Unit+0xC8` bits 22 and 23, stat 14, the record pointer and
its `+0x00`, `+0x0C`, `+0x10`, `+0x14`, and the `Game+0xA8` frame.

| Point | Address | Extra fields |
|---|---|---|
| `TRQ` | `TradeRequest` entry 0x00566E60 | requester, target, `GetTickCount` |
| `TRB` | `PktInteractButton` entry 0x00568060 | button, param, presser |
| `TRO` | `TradeOpen` 0x00567020; `TradeRecAlloc` returns 0x00566BDC / 0x00566BE2 | record, `+0x00` |
| `TIT` | `TradeItemTest` entry 0x00567620 and its four `ret` 0x0056765D, 0x0056768E, 0x00567826, 0x0056783B | item id, code, page; `EAX` |
| `TSO` / `THO` | `TradeShowOffer` 0x00568770, `TradeHideOffer` 0x00567400 | item id, page, cell; the copy id after `InvPlaceItem`, 0x005688AF (0x005688E3, first given here, is the failure path's `ret`; § 12.1) |
| `TCM` | `TradeCommit` 0x00567C70; after its `TradeRoomTest` call 0x00567DDD and its two `TradeMoveItems` calls 0x00567F1C, 0x00567F42 (the callee `ret`s first given here are moved to the caller, § 12.1) | `EAX`, `side`; both item lists (id, code, page, cell, mode) |
| `TCX` / `TCL` / `TAB` | `TradeCancel` 0x00567B00, `TradeClose` 0x005679E0, `TradeAbort` 0x00568640 | the close code |
| `TRS` | `TradeRestoreSnapshot` 0x00566CC0 entry and `ret` 0x00566D89 | both item lists after |
| `TTK` | `TradeStateTick` entry 0x005689D0 | the state before |
| `TSV` | `TradeSnapshotCopy` `ret` 0x005675F9 / 0x00567616, `SaveItemListOrSnapshot` entry 0x00531BB0 | flag, `EAX`, the buffer's sha256 |
| `ITL` | `INV` dump of both players at `TCM`, at `TRS` `ret`, and when either state returns to 0 or 3 | |

**Checker** (new `tools/trade_check.py`): replays each case's `TRB`/`TIT` lines through the § 2 state table and the
§ 4–9 rules, and checks every state, offer, gold and item-list line; for a commit it predicts J's or H's received
cell with the inventory spec's B1 (player order) from the logged grid. 0 mismatches or a named contradiction per
case (review-fix 10: each case names the reading it separates).

| Case | Recipe | Prediction (each inferred until the run; anchors in §§ 2–10) | Separates |
|---|---|---|---|
| T1 (MP31) | H requests J; J accepts; H gives item `X` (page 0 → page 2); J offers `g ≤ gold(J)`; H `ok`, then J `ok` | `TRQ` states 1/2; J's button 3 → both 3, two records with `+0x10` = each gold; `TIT` at H's pick-up: both 7 → 8 → 3 within 2–3 frames; `TSO`: a copy `X'` on J's page 1 at `X`'s cell; J's `+0x0C = min(g, cap(H) − gold(H))`; J's `ok` makes `A = J`: `side` untouched, both 9; J holds a new unit (id ≠ `X`, ≠ `X'`) at the B1 cell of J's page 0; H's `X` and J's `X'` gone; gold H `+g`, J `−g`; 9 → 10 → 0, bits 22/23 clear at 0 | the copy (a new unit) against a moved unit; the received cell (BEST) |
| T2 | open as T1, H gives `X`, moves another item `Y` on page 0 to another cell; J closes the window (stock control) | the logged button is 2 or 3: 2 → `TradeClose(…, 9)`, 3 → `(…, 12)`; both inventories rebuilt: `X` and `Y` back at their opening cells, every item id of both players new, J's `X'` gone, gold = opening gold; presser 12 → 13 → 0 (or 9 → 10 → 0), partner 9 → 10 → 0; `+0x58` = the close tick | the snapshot restore against a "return the offered items" reading (`Y`'s cell and the new ids) |
| T3 | (a) J with an NPC menu open, H requests; (b) H requests J again within 5 s of T2's close; (c) both in the Blood Moor, H requests | (a) event 8 to H, no state; (b) event 9, no state, `+0x54` = `t`; (c) both interactions cleared, states 0 | each gate alone |
| T4 | J's page 0 as § 12.3's layout plus its `gcv`; H gives its `gax` (2 × 4: no two adjacent free columns), H `ok`, J `ok` last | `side = 1` (B = H's offer into A = J's grid fails), `0x77` codes 9 to J, `0x0A` to H, offers 0, `TCX`, both restored (new ids), states 5 → 6 → 3, records kept; nothing moved | the room test before any move |
| T5 | H near the cap (`cap(H) − gold(H) = c`); J offers `g > c`, then (second part) `g' > gold(J)` | `+0x0C = c`; commit H at exactly `cap(H)`, nothing dropped; `g'` → `TradeClose(…, 9)` at once, both restored | the clip at button 8 against a clip at the commit |
| T6 | open, H gives `X`, H `ok` (4); J offers `g1`, then `g2` | H stays 4 through both `TRB 8`; J `ok` commits with `g2` | gold does not un-accept |
| T7 | open, H gives `X`, J `ok` (4); H takes `X` back off page 2; J presses `ok` within 10 s and again after | `TIT`: both 7; `THO`: `X'` off J's page 1, both `+0x14` = `t + 10 000`; ticks 7 → 8 → 11 → … → 3 after `t + 10 000`; J's `ok` during 7/8/11 answered with `0x77` code 6, state kept; after, accepted | the 10 s lock on a removal |
| T8 | open, J gives `Z`, J offers `g`; J exits (*Save and Exit*) | `TSV` with flag 1 and a copy of `+0x00` bytes before `TAB`; `TAB` leaver J: both 9, H restored; J's save (read back with `tools/d2s.py`) holds `Z` at its opening cell and J's opening gold | the saved snapshot against the live list |
| T9 | open; J (a belt holding a potion) tries to take the belt off | `TIT` → both 7; then the move refused, the belt worn | the belt lock, and a refused move still un-accepting |
| T10 | open; J picks up its cube holding an item | `TIT` returns 0, event `0x0A` to J, both 7 | the cube test |
| T11 | both hold a cube (empty); open; J picks up its cube | `TIT` returns 0 (`PlayerFindItemByCode(H, box)`), both 7 | the quest-code test |
| T12 | open, H gives `X`, H `ok`; J gives `W` (pick-up, place on page 2) | `TIT` both 7 (H's 4 lost); `TSO` with neither at 4: no `TradeOpen`; 7 → 8 → 3 (no lock, `+0x14` = 0) | an addition un-accepts, without the lock |
| T13 | H's four `wnd` (1 × 2) into J's page 0 laid out as § 12.3 finds (FIRST fits all four, BEST the first three); J gives its `gcv`, H `ok`, J `ok` (A = J) | `TRT` 1; `TMV` A → B (J's `gcv` into H) 1, then B → A 0 at the fourth wand (`0x77` codes `0x0A` to the giver, 9 to the receiver), `TCX` at 0x00568050, both restored: the half commit undone | the two search orders |

**Logger points per case.** T1: all points. T2: `TRB`, `TCL`, `TRS`, `ITL`, `TTK`. T3: `TRQ`. T4: `TCM`, `TCX`, `TRS`, `TTK`.
T5: `TRB`, `TCM`, `TCL`. T6: `TRB`, `TCM`. T7: `TIT`, `THO`, `TTK`, `TRB`. T8: `TSV`, `TAB`, `TRS`. T9–T12: `TIT`, `TSO`,
`TTK`. T13: `TCM`, `TCX`, `TRS`.

Not reachable on a stock client, so out of Phase 2 unless the owner rules otherwise (ADR-0013): a death in town (no
damage in town is a lead, not read here), monster equipment (flag `0x1000`) in a player's inventory, a waypoint packet
from a trading player (§ 9), an `ItemCopy` failure, and the request from a dead target.

### 12. Phase 2 preparation

Static work of plan 0067 Phase 2 before any hosting session (`lane/n67p`, 2026-11-10): no Ghidra, no wine, no game
launched. Kept outputs: `workspace/logs/n67p/static/` (`commands.txt` holds every command; `manifest.txt` hashes the
other files and passes `sha256sum -c` from that directory).

#### 12.1 Corrections to §§ 4, 8 and 11

- [I] **The 4-digit "codes" are source lines.** Every `0x77` send of the module is preceded by
  `push <n>; mov edx, 0x6E11D8; call 0x005531C0` (the client lookup with `PlrTrade.cpp`'s name and a line number),
  then `mov dl, <code>`. The first text read `0xBEE`, `0xBD2`, `0xBD7`, `0xBDC` (button 4), `0xA51`/`0xA52`,
  `0xA56`/`0xA57` (the room test) and `0x9D1`/`0x9D2` (a failed move) as codes; they are the line numbers. § 4's
  button 4, § 8's sketch and § 11's T4, T7 and T13 rows now give the `DL` codes. (0x005684E3–0x0056853B,
  0x00567E05–0x00567E72, 0x00567268–0x00567294)
- [I] **What each refusal of the commit sends**, `0x77` to A, then to B: `B`'s cap passed by A's offer: `0x0A`, 9
  (0x00567CF1, 0x00567D0B); A's cap passed by B's offer: 9, `0x0A` (0x00567D97, 0x00567DB2); the room test with
  side 0: `0x0A`, 9 (0x00567E54, 0x00567E6E); with side 1: 9, `0x0A` (0x00567E0F, 0x00567E29). A failed move sends
  `0x0A` to the giver and 9 to the receiver (0x00567275, 0x00567290). So in each of these the player without room gets
  9 and the other `0x0A`. The exchange sends `0x0D` to both (0x00568012, 0x0056802C).
- [I] **Logger addresses.** § 11's `TSO` point 0x005688E3 is `TradeShowOffer`'s failure `ret`; the copy is read after
  `InvPlaceItem` at 0x005688AF (`EAX` the result, the copy at `[ebp+8]`, the original in `EDI`). The room test's and
  the two moves' results are read in the commit, after each call (0x00567DDD: `EAX` and `side` at `[ebp−4]`;
  0x00567F1C and 0x00567F42: `AL`), not at the callees' `ret`s. (fn:sub_00568770_TradeShowOffer@0x00568770,
  fn:sub_00567C70_TradeCommit@0x00567C70)
- [I] **The scratch placement is visible.** `InvScratchPlace` holds `InvSpotFindBySize`'s result at 0x0063E228:
  `EAX`, the item in `EBX`, the cell at `[ebp−8]` and `[ebp+0xC]`, the scratch in `EDI` (its owner word at `+8`,
  written 0 at 0x0063E3B4 and 0x0063E3F1). The logger prints each scratch cell, so every commit with an offer on a
  page that is not empty separates FIRST from BEST, not only T13. (`objdump-scratch.txt`, 0x0063E1C0–0x0063E2D6)

#### 12.2 The logger and the checker

- **`tools/gdb/two-trade.gdb`** sources `pilot.py`, `two-players.py` and the new **`tools/gdb/two-trade.py`**, so it
  loads in one gdb session with the host driver's two-client files (`gdb-load.txt`: the three `armed` lines and
  `TRDY`, no error). It only reads memory and registers (`readonly-grep.txt`: no `write_memory`, no register
  assignment; ADR-0003). Each entry line and its after line (taken at the call's return address, matched by the stack
  pointer) carry every player's state, record and item list. The points are § 11's, with the § 12.1 moves, plus
  `SCP` (scratch cells), `TMP` (each real placement, 0x0056718D), `TMS`/`TG9`/`TEV` (the `0x77`, `0x79` and `0x5A`
  sends with their return site), `TBL` (the belt lock), `TSC` (the snapshot copy's count and sha256, 0x00531BDB) and
  `CRM` (`ClientRemove`'s arguments, the open question of § 10). `bpcheck.txt`: all 39 addresses decode as
  instruction starts from their function's start. The ready line is `TRDY` (review-fix 16).
- **`tools/trade_check.py check`** replays each event against its rule (`R-request`, `R-button2/3/4/7/8`,
  `R-itemtest`, `R-show`, `R-hide`, `R-commit` with the FIRST scratch cells and the BEST placements from
  `tools/item_inventory.py`'s B1 model, `R-cancel`, `R-close`, `R-abort`, `R-tick` with its frame delays, `R-save`)
  and each case against its expectations (`trade_check.py cases`: 13 cases, 32 expectations). The cases are cut at the
  `start` marks that `trade_check.py mark` writes. `tools/test_trade_check.py` (16 tests, `test-trade-check.txt`):
  the models, the search's determinism, a synthetic T1 log that checks clean and six mutations of it, a tick log and
  a cancel log with one mutation each (every mutation is named by its rule), and an unmet expectation.

#### 12.3 T13: FIRST and BEST disagree, in both directions

- [I] **Layouts exist where the room test passes and the move fails, and where the room test refuses a trade that
  would fit.** `trade_check.py layout` (seed 67, 40 000 random page-0 layouts built from the eight item sizes of
  weapons, armor and misc, offers of 2 to 4 items, every order of each offer tried) under the inventory spec's B1–B4
  model and § 8's reading (scratch owner 0, FIRST; the player's page, BEST): 248 layouts with FIRST fitting and BEST
  not (8 of them for every order of the offer), 1 064 with BEST fitting and FIRST not (5 for every order).
  (`t13-layout.txt`, fn:sub_0063E370_TradeRoomTest@0x0063E370, fn:sub_0063B850_InvSpotFindBySize@0x0063B850,
  fn:sub_005670E0_TradeMoveItems@0x005670E0)
- [I] **The T13 layout** (every order alike, the offer being four items of one size): page 0 holds a 2 × 2 at (3, 1),
  a 2 × 4 at (7, 0), a 2 × 3 at (0, 1) and a 2 × 3 at (5, 0); the offer is four 1 × 2. FIRST places them at (2, 0),
  (2, 2), (9, 0), (9, 2). BEST places the first three at (9, 0), (9, 2) and (2, 1), which leaves (2, 0) and (2, 3)
  apart, and the fourth fails. (`t13-layout.txt`, `t13-recipe-check.txt`, fn:sub_0063B850_InvSpotFindBySize@0x0063B850,
  0x0063E228)
- [I] **The reverse case** (not a Phase 2 case): page 0 with a 2 × 1 at (5, 0), 1 × 4 at (1, 0), 1 × 3 at (3, 1),
  1 × 3 at (9, 0); three 2 × 2 offered. FIRST fails the third, BEST places all three. (`t13-layout.txt`,
  fn:sub_0063B850_InvSpotFindBySize@0x0063B850)
- [I] **The recipes.** `TrJoinB` (`tools/d2s_recipes/mp-trade-join13.json`) holds that layout as `cap`, `gax`, `axe`,
  `axe`, plus a `gcv` at (4, 3); `TrHostB` holds four `wnd` at (0..3, 0) and a `gax` at (8, 0). With J accepting last
  (A = J), J's `gcv` fits H (FIRST (7, 0), BEST (7, 3)), the room test passes, `TradeMoveItems(J → H)` succeeds and
  `(H → J)` fails at the fourth wand: a half commit, cancelled at 0x00568050 and undone by the snapshots (§ 8). With H
  last (A = H) the first move fails (0x00567F32). The same pair gives T4: H's `gax` fits no two adjacent free columns of
  J's page 0, so side 1. (`t13-recipe-check.txt`; `mp-saves-check.txt`: each recipe's page 0 exactly as listed)

#### 12.4 Run recipe for the harness lane (plan text)

What follows is the plan for the hosting sessions. Each expected outcome is § 11's prediction, inferred until the run.

**Characters** (`tools/mp_saves.py build workspace/merged/data/global/excel workspace/runtime/mp-saves-n67`; pairs in
`mp_saves.py pairs`; `mp-saves-build.txt` hashes, pinned in `tools/test_d2s.py`). All are level 80 expansion
Sorceresses (cap 800 000):

| Save | Recipe | Page 0 (col, row) | Other |
|---|---|---|---|
| `TrHost` (H) | `mp-trade-host` | `wnd` (0,0) = X, `gcv` (5,0) = Y, `box` (8,0), empty | gold 795 000 |
| `TrJoin` (J) | `mp-trade-join` | `wnd` (0,0) = W, `gcv` (2,0), `box` (8,0) | a `gcv` in the cube; a belt of `rvl`; gold 100 000 |
| `TrHostB` (H) | `mp-trade-host13` | four `wnd` (0..3,0), `gax` (8,0) | gold 10 000 |
| `TrJoinB` (J) | `mp-trade-join13` | § 12.3's layout, `gcv` (4,3) = Z | gold 100 000 |

**Every session** (ADR-0008; harness-play § Slots, § Before the batch). `R=workspace/logs/<run>`, `L=$R/<s>-host.log`:

```bash
tools/ufwcheck.sh <s> workspace/logs/p44h-run/ufw-baseline.sha256 $R/ufw.log || exit 1
python3 -I tools/saves.py --slot 1 aside <tag>; python3 -I tools/saves.py --slot 2 aside <tag>
setsid python3 -I tools/d2run.py --slot 1 --seed 1 --gdb tools/gdb/two-trade.gdb --steps tools/gdb/two-host-normal.steps \
    --after 4000 --install <tag> <H.d2s> --log $L > $R/<s>-host.out 2>&1 < /dev/null &   # wait for TRDY, then PLR
setsid python3 -I tools/d2run.py --slot 2 --seed 1 --steps tools/gdb/two-join.steps --after 4000 \
    --install <tag> <J.d2s> --log $R/<s>-join.log > $R/<s>-join.out 2>&1 < /dev/null &  # wait for the joiner in PLRS
python3 -I tools/d2pilot.py join $L where --slot 2
python3 -I tools/d2pilot.py join $L follow --slot 2 --me join --lead host --near-lead 4 --time 30   # within 8
# per case: python3 -I tools/trade_check.py mark $L Tn   (just before the case's first action)
# end: copy what the case needs (T8: the joiner's save), then
python3 -I tools/slots.py stop 2; python3 -I tools/slots.py stop 1
python3 -I tools/saves.py --slot 1 restore <tag>; python3 -I tools/saves.py --slot 2 restore <tag>
python3 -I tools/trade_check.py check $L --excel workspace/merged/data/global/excel > $R/<s>-check.txt
```

Trade actions are `d2pilot.py join $L trade TOKEN… --slot N --me host|join --lead join|host` (tooling § Two clients):
`request` (a click on the other player, its screen point from PLRS), `accept` (320,103), `ok` (318,461),
`'give:inv:c,r,w,h>tr:c,r,w,h'` (quoted), `xy:X,Y`, `key:K`, `sleep:S`, `shot:P`. A cell (c, r) of the own inventory
is at (432 + 29c, 330 + 29r) for 1 × 1 (tools/joiner.py `INV`); the paper-doll belt at (562,252) (tools/d2pilot.py
`EQUIP`). No new `.steps` file is needed: the request click is computed from PLRS, and the controls not measured yet
become `xy:`/`key:` tokens once the dev session has measured them. Between cases wait 6 s (the 5 000 ms end windows,
§ 3).

**Dev session** (`dev-` logs; pair `TrHost`/`TrJoin`). It measures, from screenshots (`shot:`) and the `TRB` lines:
1. **the gold button** of the own offer and its entry box: the click point, how the amount is typed (digits, then
   `key:Return` or an OK point), and whether one `TRB` 8 comes per keystroke or one per entry (Open questions);
2. **the trade window's close control**: `key:Escape` first, else the window's close button; which button the
   client sends (2 or 3);
3. that the paper-doll belt point (562,252) and the inventory cells are where the trade screen draws them;
4. the smoke (harness-play § Before the batch): `TRDY`, then at least one `TRQ`, `TRB`, `TRA`, `TIT`, `TSO`, `TSP`,
   `TTK`, `TCM`, `SCP`, `TRT`, `TMP`, `TMV`, `TMS` in a one-scroll trade, and `trade_check.py check` runs on it.

**Session (a)**, `TrHost`/`TrJoin`: T1, T3 (b), T2, T6, T5, T3 (a), T3 (c).
- T1: H `request`; J `accept`; H `'give:inv:0,0,1,2>tr:0,0,1,2'`; J gold 500 (gold tokens); H `ok`; J `ok`.
- T3 (b), at once after T1's commit (both `+0x58` = t): H `request` → event 9 named.
- T2 (after 6 s): open; H gives X; H moves Y `xy:577,330 xy:577,417` (page 0 (5,0) → (5,3)); J closes (the measured
  control).
- T6: open; H gives X; H `ok`; J gold 300, then 400 (H stays at 4); J `ok`.
- T5: open; J gold 9 000 (clipped to H's room), H `ok`, J `ok`: H ends at 800 000. Then open again; J gold 150 000
  (above J's gold): close 9.
- T3 (a): J `d2pilot.py npc $L akara trade --slot 2 --me join --stay`; H `request` → event 8; J `key:Escape`.
- T3 (c): both to the Cold Plains by waypoint (as `workspace/logs/p44h-run/drivers/meet.sh`), J follows H within 8;
  H `request` → both interactions cleared (`TQN`).

**Session (b)**, `TrHost`/`TrJoin`: T7, T12, T9, T10, T11.
- T7: open; H gives X; J `ok`; H takes X back (`xy:111,345 xy:432,345`); J `ok` at once (refused, code 6), and
  again after 11 s (accepted); close.
- T12: open; H gives X; H `ok`; J `'give:inv:0,0,1,2>tr:0,0,1,2'` (W); then close.
- T9: open; J `xy:562,252` (the belt, which holds potions); then put back with a second click if it moved; close.
- T10: open; J `xy:679,345` (its cube, holding a `gcv`): refused, event `0x0A`; close.
- T11: open; H `xy:679,345` (its empty cube, J holding a cube): refused, no event; close.

**Session (c)**, `TrHostB`/`TrJoinB`: T4, T13, T8 (in one window: a cancel leaves it open at 3, § 9).
- T4: H `request`; J `accept`; H `'give:inv:8,0,2,4>tr:0,0,2,4'`; H `ok`; J `ok` → side 1, cancel, 5 → 6 → 3.
- T13: in the same window H gives the four `wnd` (`'give:inv:0,0,1,2>tr:0,0,1,2'`, then (1,0), (2,0), (3,0) to
  tr (1,0), (2,0), (3,0)); J `'give:inv:4,3>tr:9,3'` (Z); H `ok`; J `ok` (A = J) → `TMV` 1 then 0, cancel at
  0x00568050.
- T8: in the same window J gives Z again and offers 2 000 gold; J leaves: `d2pilot.py join $L leave --slot 2` (SAVE
  AND EXIT). If the dev session finds that Escape closes the trade window (item 2), `leave` would close the trade first
  and log `TCL`, not `TAB`: then J leaves by a dropped connection (`slots.py stop 2`, as MP11 did), and T8's save claim
  rests on the host's `TSV`/`TSC` lines alone. Then copy `workspace/wineprefix-2/drive_c/users/$USER/Saved Games/Diablo II/TrJoinB.d2s` to
  `$R/c-TrJoinB-after.d2s` before `slots.py stop 2`, and read it with `tools/d2s.py dump`: Z at (4,3) and gold
  100 000 (the opening list and carried gold, § 10).

**Logs kept per session**: `$R/<s>-host.log`, `<s>-host.marks.tsv`, `<s>-join.log`, both `.out`, `ufw.log`, the
screenshots, `<s>-check.txt`, (c) the joiner's save copy; one `manifest.sha256` per directory (review-fix 6). Dev
logs under `$R/dev/` with their own manifest.

### 13. Phase 2 run (run:2026-11-10-trade, `lane/n67h`)

Slots 1 (host, gdb, `tools/gdb/two-trade.gdb`) and 2 (joiner), Normal, expansion, agent-driven; the record is
[experiments § run:2026-11-10-trade](experiments.md#run2026-11-10-trade). Logs `workspace/logs/n67h/{dev/d1,a,b,c}/`
(each with its `manifest.sha256`; `sha256sum -c` passes from the directory), checks `a-check.txt`, `b-check.txt`,
`c-check.txt` (`trade_check.py check`, `--excel workspace/merged/data/global/excel`). Claims below rest on those checked
logs; every case's anchors are the log's `TRB`/`TIT`/`TTK`/`TCM` lines and the § 2–9 addresses.

**Results by case** (a checked log each; "met" = the checker's `E-` expectations):

| Case | Log | Result |
|---|---|---|
| T1 | a | 0 mismatches, 4/4 met: the copy `X'` on J's page 1, the new unit at J's received cell, gold moved, 9 → 10 → 0. |
| T2 | a | 0 mismatches, 2/2 met: the close (below) gives `TradeClose(…, 9)`, both inventories rebuilt (`TRS`), new ids. Variant: X was spent in T1, so H offered `gcv`; the cube was picked up (a `TIT`, item code 549). |
| T3 (a) | a | event 8 to H, no state (`TEV` 8 at f 13549); J had Deckard Cain's menu open. |
| T3 (b) | a | event 9 named, `+0x54` = `t` (f 3614, 80 frames after T2's close); 1 of 3 expectations for that segment. |
| T3 (c) | - | not reached: the logger sources no `pilot.py` object lines, so `d2pilot wp` cannot find the town waypoint, and no exit coordinates are known; `TQN` never appeared. |
| T4 | c | 0 mismatches, 2/2 met: side 1, `0x77` 9 then `0x0A`, `TCX`, both restored, 5 → 6 → 3. |
| T5 | a | 0 mismatches, 2/3 met. First part: J's entry of 9 000 was clipped, H ended at exactly 800 000, nothing dropped. Second part (`g'` above J's gold) not reached: the client clamps the entry to J's own gold before it sends button 8 (`TRB` 8 with `param` 95 000 for an entry of 150 000, J holding 99 500 minus the 4 500 already given), so no overspend reaches the server. |
| T6 | a | 0 mismatches; `E-offer-at-4` unmet, see below; `E-exchange` met in the rerun. |
| T7 | b | 0 mismatches, 4/4 met: 7 → 8 → 11, J's `ok` at 7/8/11 answered code 6, state kept, 11 → 3 after the lock, then accepted. |
| T8 | c | 0 mismatches, 2/2 met: `TSV` flag 1 and `TSC` before `TAB`, both restored. J left by a killed client (`slots.py stop 2`), see below. |
| T9 | b | 0 mismatches, 2/2 met: `TIT` 1 → both 7, `TBL` 0, the belt stays worn. |
| T10 | b | 0 mismatches, 1/1 met: `TIT` returns 0, event `0x0A`. |
| T11 | b | 0 mismatches, 1/1 met: `TIT` returns 0, no event. |
| T12 | b | 0 mismatches, 3/3 met: H's 4 lost, no `TradeOpen` for the second offer, 7 → 8 → 3 with no lock. |
| T13 | c | 3/3 met; 2 mismatches, below. `TMV` 1 then 0, `0x77` `0x0A`/9, `TCX`, both restored. |

Session totals from the kept check output: a 547 events, 318 checks, 0 mismatches, 12 unmet lines (the segments
below); b 362 events, 203 checks, 0 mismatches, 0 unmet; c 400 events, 218 checks, 2 mismatches, 0 unmet. Session a's
`unmet` lines come from case segments, not from rules: a `T3` mark whose request never reached the server (marked
`fail`), one `T3` segment per sub-case (each only meets its own sub-case's expectation), T6's first segment (below)
and T5's second part.

**Open items measured (dev session `dev/d1` and the kept sessions).**
- [C] **The gold entry.** The coin button of the inventory (window point (494,461)) opens a box "How much gold would you
  like to offer?"; the digits are typed with `key:N` and `key:Return` sends it. One `TRB` 8 comes per entry (`param` =
  the amount), not per keystroke (dev, f 2432: `TRB` 8 `param` 500; a, f 4528, 4680). The click on the coin sends `TRB` 7
  first (a, f 4434, 4586, 6356). (a: `TRB`/`TRBR` lines; `0x00568060` is the button handler.)
- [C] **The close control.** `key:Escape` with the trade open, and the trade window's own circle button at (371,461),
  both send button 2 (dev: f 4384 and f 5762) and `TradeClose` code 9 (`TCL` `code` 9); T2's "2 → 9" branch is the one
  taken, the "3 → 12" branch is not reached (button 3 is the accept). With no panel open, Escape opens the game menu,
  not a close: a second Escape closes it. [run:2026-11-10-trade]
- [C] **The belt and the cells.** The paper-doll belt at (562,252) is where the trade screen draws it (T9, b: `TIT` item
  code 460, `TBL`); the cube at (679,345), the grid cells at (432 + 29c, 330 + 29r) and the trade grids' (97, 100 + ...) hit
  as drawn (T1, T7, T10-T13). [run:2026-11-10-trade]
- [C] **The logger smoke.** Every tag `trade_check.py` reads appeared in the dev or kept logs except `TQN` (T3 (c), not
  reached). `TAB` and `CRM` came from the killed joiner (the end of b, and c), `TEV` from T3, `THO` from T7, `TBL` from T9. [run:2026-11-10-trade]
- [C] **`ClientRemove`'s arguments** in the two disconnects (b, f 4389; c, f 3193): `edx` 3, `a1` 1, the `a2` a
  pointer (`CRM`, site 0x0052CB86).

**Contradictions and refinements, named.**
- [C] **A gold entry un-accepts the partner by its button 7.** The stock client sends `TRB` 7 when the coin is clicked
  (before the entry), and a 7 at state 4 sets the partner to 3 (a, f 4434: H 4 → 3; § 4's button 7). T6's separation, "H
  stays at 4 through a `TRB` 8", needs a 8 with the partner at 4: not reached, because the entry box closes when the
  partner presses `ok` (a, rerun: H `ok` at f 6463, then J's Return gave a `TRB` 7 and a gold of 0). So § 4's claim that
  a button 8 (the gold) does not un-accept stays `[I]`: only the 7 that precedes it is observed. [run:2026-11-10-trade]
- [I] **T13's tick delays.** In c the cancel's ticks 5 → 6 → 3 ran in one logged frame (f 2371, log lines 1198-1205) where
  the rule (§ 2: +1 frame each) and T4's cancel (f 1447, 1447, 1448, 1448) give two. The checker reports the two
  `R-tick/delay` mismatches (lines 1202, 1204) and nothing else. Not resolved: the frame word read at the logger points
  (`Game+0xA8`) may be the outer loop's, with catch-up steps inside it after the five placements of that commit; the
  states and the order (5, 6, 3, bits 22/23 cleared) match. The delay rule stays `[I]` and the spec states it with this
  exception. [run:2026-11-10-trade]
- [I] **T8's save claim.** J's `TrJoinB.d2s` was not rewritten during the session (its mtime is the install's), so the
  after-copy (`c/c-TrJoinB-after.d2s`) carries no evidence; the claim rests on the host's `TSV` (flag 1) and `TSC` lines.
  The leaver was a killed client, so `TAB` was logged (leaver J), not the *Save and Exit* route. [run:2026-11-10-trade]

**Recipe changes** (for § 12.4 as run): X is spent in T1, so later cases of session a offer `gcv` (5,0) and move the
cube; after a commit both clients keep the inventory panel open (it shifts the view, so a `request` click misses),
close it with `key:Escape` only when it is open, and check that the `TRQ` count rose; `d2pilot npc` did not find the
town NPCs on this logger (no `pilot.py` object lines), so J clicked an NPC by `xy:` (Deckard Cain at 385,395 from
the start position); T6's second part and T5's second part are unreachable on the stock client.

## Data touched

- `PlayerData` (`Unit+0x14`) `+0x4C` (busy), `+0x50` (state 0–16), `+0x54` (request rate tick), `+0x58` (trade end
  tick), `+0x5C` (the record).
- The record (`PlrTrade.cpp` lines `0x806`/`0x807`): `+0x00` snapshot bytes, `+0x04` the buffer (0x2000), `+0x08` the
  offer map (nodes `{original id, copy id, next}`, line `0xC5B`), `+0x0C` the gold offer, `+0x10` gold at opening,
  `+0x14` the lock time (`GetTickCount` + 10 000).
- struct:Unit+0xC8 (bits 0, 1, 22, 23), `Unit+0x60` (inventory), `Unit+0x64`/`+0x68`/`+0x6C` (the interaction: unit id,
  kind, valid).
- The inventory's `+0x08` owner, `+0x0C` item list, `+0x1C`/`+0x20` (cleared by `InvUnlinkAll`), `+0x2C`/`+0x30` (the
  update list); ItemData `+0x14` (flags), `+0x64` (next), `+0x69` (location: 1 page, 2 belt, 3/4 body).
- tbl:Misc.txt:quest (`+0x12A`), stat 14 (`gold`) only; `GoldCap` (fn:PLAYER_GoldCap@0x00622E70).

## Dead ends

- The decompiler shows `TradeReturnItems(1)` and `(0)`: the argument is pushed and popped (`ret 4`) but never read
  (no `[ebp+8]` in 0x005678F0–0x005679D6). Leaver and partner are restored alike.
- A first awk over the `0x77` sites took the last `mov dl` before each call and missed `xor dl, dl` (code 0 at
  0x00566FCA). The kept `pkt77-sites.txt` resets on every call other than `PlayerGetClient`.
- `0x00568D16` looked like a fourth `TradeRecAlloc` caller: it is the unreferenced `TradeSelfReload`.
- `pkt77-sites.txt` pairs each `0x77` call with the code set before it in the listing. A jump into a shared tail
  carries another code: the partner-gone path sets `0x0C` at 0x005685E9 and jumps to 0x005684F6, which the file lists
  as code 6. Every code this finding states was re-read at its site.

## Open questions

- Answered in § 13: the close is button 2 (code 9), the gold entry sends one button 8 per entry, after a 7. What stays
  open: a button 8 with the partner at 4 (the entry box closes when the partner accepts).
- [L] Whether the stock client lets a trading player send `0x49` (waypoint travel), or reach `0x0054C380`; if a case
  needs a forced message it is an ADR-0013 run, which the owner rules on at Phase 1's review.
- [L] Whether the old item units are freed after `TradeReturnItems` (`InvQueueItemUpdate`, ItemData `+0x14` bit 0, and
  the update list's consumer), and whether the hidden copy of `TradeHideOffer` is freed. The callers of
  `0x0063CBB0` and the free path of `0x0055DF10` would settle it.
- [L] The two save routes not followed to `D2S_WriteSave` (0x00531EB0, 0x00532240), which decide the flag on a host
  callback or single-player save; and `ClientRemove`'s argument at each of its eight callers. T8 logs the route taken.
