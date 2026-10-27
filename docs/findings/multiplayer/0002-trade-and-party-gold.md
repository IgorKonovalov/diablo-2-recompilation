# 0002 — Player-to-player trade and the party gold share: the readings behind MP31 and MP32

> **Subsystem:** cross-cutting (multiplayer cases MP31, MP32; items/economy for the gold share)
> **Question:** what does the server do when two players trade an item and gold, and when a partied player picks up
> gold, so that the two-client cases MP31 and MP32 of [multiplayer/0001](0001-cases.md) § 2 can carry a prediction?
> **Date:** 2026-10-27   **Plan:** 0051 (Phase 1b)   **Status:** answered (static reading; the two-client run is not
> taken)

All addresses are in the pinned `Game.exe`. Every behavioural claim here is a static reading (objdump of the image and
the lane's Ghidra copy `ghidra-p51s`), so it is inferred. No session was played. The kept outputs are in `workspace/logs/p51s/static/`
(`findstring-plrtrade.txt`, `objdump-trade-gold.txt`, `call-sites.txt` with every direct call of the functions
counted below, the commands in `commands.txt`; `manifest.txt` holds their sha256).

## Answer (summary)

- [I] **The party gold share is an equal split with the remainder to the picker.** `GoldPickup` sends a pile through
  `PartyGoldShare` when the picker is in a party and the pile has no player owner. `PartyGoldShare` counts the party
  members in the picker's level that are not dead (the picker included), `n`. When `n ≤ 1` the picker takes the pile
  alone, clipped at its gold cap. Otherwise `share = amount / n` (signed, truncated). Each other member in the level
  gets `min(share, cap − gold)`, and whatever a member cannot hold goes back to the picker's part. The picker gets
  `amount − (members paid) × share + (their overflow)`, clipped at its own cap, and the rest is returned and dropped
  as a pile. No draw. (fn:sub_0055C850_GoldPickup@0x0055C850, fn:sub_00540900_PartyGoldShare@0x00540900,
  fn:sub_00540650_PartyGoldClip@0x00540650)
- [I] **Who counts and who is paid are tested differently.** The count skips dead members (`UnitIsDead`: flag `+0xC6`
  bit 0, or player mode 0 or 17). The payment loop tests the **picker's** mode (`ECX = ESI` at 0x00540A73 and
  0x00540A7E), not the member's. So a dead member in the level is paid a share but was not counted. With three in the
  level and one dead, `n = 2`, both others get `amount / 2`, and the picker keeps `amount mod 2` (with neither member
  at its cap; a member's overflow comes back to the picker). (0x00540A5A–0x00540ABA,
  fn:sub_005541B0_UnitIsDead@0x005541B0, fn:sub_00451F70_UnitGetMode@0x00451F70)
- [I] **A trade between players is a state machine on `PlayerData+0x50`, driven by the `0x4F` button packet.**
  Interacting with a player in town (distance test ≤ 50) sends a request: the requester gets state 1, the target 2.
  Button 3 (the target accepts) opens both windows (state 3) and gives each a trade record whose `+0x10` holds the gold
  at opening. Button 8 offers gold. Button 4 checks "accept" (3 → 4). When both are at 4, the trade commits. Button 7
  takes both back from 4 to 3, and button 2 closes. (fn:sub_0054C7C0_Pkt4FButton@0x0054C7C0,
  fn:sub_00568060_PktInteractButton@0x00568060, fn:sub_00566E60_TradeRequest@0x00566E60,
  fn:sub_00567020_TradeOpen@0x00567020, fn:sub_00566B30_TradeRecAlloc@0x00566B30)
- [I] **The gold offer is clipped to what the partner can hold.** An offer above the offerer's carried gold (unsigned
  compare) closes the trade (state 9), unless either side is `TradeBlocked`, when the button does nothing
  (0x005683EB–0x00568409). Otherwise, if the partner's gold plus the offer passes the partner's cap, the
  offer becomes `cap − gold(partner)`. The amount is stored at the offerer's trade record `+0x0C` and sent to both
  clients. Only carried gold (stat 14) is read, not the stash. (0x005683DC–0x00568497)
- [I] **The commit re-checks gold and room, then moves copies and gold.** For each side with an offer, it cancels
  (state 5, the offers zeroed, items returned) if the offerer now holds less than the offer, or if the partner would
  pass the cap. It also cancels if the room test fails (the message tells which side), or if the partner may not
  receive an offered item (`ItemQuestGate`). Otherwise both get state 9 and the `0x800000` flag at `Unit+0xC8`. Each
  item on the offerer's trade page (page 2) is **copied** (`ItemCopy`) into the partner's inventory (page 0, mode 4),
  and the originals are removed. Then each offer is taken from the offerer's carried gold and given to the partner
  through `PlayerGiveGold`. (fn:sub_00567C70_TradeCommit@0x00567C70, fn:sub_005670E0_TradeMoveItems@0x005670E0,
  fn:sub_005672D0_TradeItemsAllowed@0x005672D0, fn:sub_00567B00_TradeCancel@0x00567B00,
  fn:sub_0055B060_PlayerGiveGold@0x0055B060)
- **MP31 and MP32 predictions:** § 3. They wait for the two-client run with both slots, as plan 0051's Open questions
  says. Nothing here is raised.

## Leads used

- The string `.\PLAYER\PlrTrade.cpp` (0x006E11D8): its 80 references locate the trade module, 0x00564CD0–0x00568C01
  (`tools/ghidra.sh findstring PlrTrade`). Used to locate code only.
- The `0x4F` button packet: located through the handler of [items/0008](../items/0008-cube.md) (`Pkt4FButton`, size 7,
  the button at `+1`, the parameter `(u16 +3) << 16 | u16 +5`). Used to locate code only.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0055C850` | `sub_0055C850_GoldPickup` | a gold pile picked up (ESI the picker, stack: game, pile) | I |
| `0x00540900` | `sub_00540900_PartyGoldShare` | the party split; returns the part nobody could hold | I |
| `0x00540650` | `sub_00540650_PartyGoldClip` | one member's part: `min(share, cap − gold)` and the overflow | I |
| `0x005405A0` | `sub_005405A0_PartyForEachInLevel` | the callback over party members in the unit's level | C (existing) |
| `0x005404F0` | `sub_005404F0_PartyCountAliveCb` | counts a member unless `UnitIsDead` | I (existing) |
| `0x00451F70` | `sub_00451F70_UnitGetMode` | `Unit+0x10`, 0 for NULL (fn:sub_00451F70_UnitGetMode@0x00451F70) | I |
| `0x00568060` | `sub_00568060_PktInteractButton` | the button switch (trade buttons 2, 3, 4, 7, 8) | I (existing) |
| `0x00566E60` | `sub_00566E60_TradeRequest` | requester state 1, target 2, both in town (fn:sub_00566E60_TradeRequest@0x00566E60) | I |
| `0x00567020` | `sub_00567020_TradeOpen` | both states 3 (fn:sub_00567020_TradeOpen@0x00567020) | I |
| `0x00566B30` | `sub_00566B30_TradeRecAlloc` | the trade record; `+0x10` = carried gold at opening (fn:sub_00566B30_TradeRecAlloc@0x00566B30) | I |
| `0x00566BF0` | `sub_00566BF0_TradeRecFree` | frees the record and its list (fn:sub_00566BF0_TradeRecFree@0x00566BF0) | I |
| `0x005679E0` | `sub_005679E0_TradeClose` | returns items, frees both records, sets the states (fn:sub_005679E0_TradeClose@0x005679E0) | I |
| `0x00567B00` | `sub_00567B00_TradeCancel` | the offers zeroed, items returned, both states 5 (fn:sub_00567B00_TradeCancel@0x00567B00) | I |
| `0x00567C70` | `sub_00567C70_TradeCommit` | the checks and the exchange | I |
| `0x005670E0` | `sub_005670E0_TradeMoveItems` | copies one side's page-2 items into the other's inventory | I |
| `0x00567070` | `sub_00567070_TradeItemRename` | an ear's or a personalised item's name on the copy (fn:sub_00567070_TradeItemRename@0x00567070) | I |
| `0x005672D0` | `sub_005672D0_TradeItemsAllowed` | `ItemQuestGate` for each offered item (fn:sub_005672D0_TradeItemsAllowed@0x005672D0) | I |
| `0x005678F0` | `sub_005678F0_TradeReturnItems` | puts back the items of an open trade (fn:sub_005678F0_TradeReturnItems@0x005678F0) | I |
| `0x005689D0` | `sub_005689D0_TradeStateTick` | the timed state steps (event 13; pointer at 0x006E1844) (fn:sub_005689D0_TradeStateTick@0x005689D0) | I |
| `0x00597A20` | `sub_00597A20_TradeBlocked` | `Unit+0xC8` bit 22 or 23, or an item still pending (fn:sub_00597A20_TradeBlocked@0x00597A20) | I |

## Walkthrough

### 1. The gold pickup and the party share (MP32)

`GoldPickup` (ESI = the picker, stack: game, the pile; two call sites, 0x0055D04C and 0x00563668, callers not
followed):

```c
// fn:sub_0055C850_GoldPickup@0x0055C850 (0x0055C859–0x0055C92A), signed 32-bit
cap = PLAYER_GoldCap(picker); gold = stat14(picker); amt = stat14(pile);
give = amt; rest = 0;
if (amt + gold > cap) { give = cap - gold; rest = amt - give; }
owner = UnitGetOwner(game, pile);                 // the stored guid, only when pile +0xC8 bit 10
if (owner && owner->type == 0)  UnitAddGoldStat(picker, 14, give);           // a player's pile: never shared
else if (PartyIdOfUnit(picker) != 0xFFFF) rest = PartyGoldShare(game, picker, amt);   // the whole pile
else  { add give to stat 14 with the 0 / cap guard (items/0011 § 6) }
... remove the pile; if (rest > 0) DropGold(rest)
```

- [I] The split is entered with the **unclipped** pile `amt`, and its return replaces `rest`. (0x0055C8D1–0x0055C8DC)
- [I] A pile whose owner is a player (`Unit+0xC8` bit 10 and a type-0 unit found by the stored guid) goes to the
  picker alone, even in a party. Which piles carry a player owner (a player's own dropped gold) is not read here.
  (0x0055C89C–0x0055C8C2, fn:sub_00552FD0_UnitGetOwner@0x00552FD0)

```c
// fn:sub_00540900_PartyGoldShare@0x00540900, ECX game, EDX picker, stack amt; ret 4
n = 0; PartyForEachInLevel(game, picker, PartyCountAliveCb, &n);    // members in the picker's level, not dead
if (n <= 1) { clip amt at the picker's cap; add with the 0 / cap guard; return the excess; }
party = PartyFind(game, PartyIdOfUnit(picker));
if (!party) { clip; UnitAddGoldStat(picker, 14, give); return the excess; }
share = amt / n;                                  // idiv: truncated toward zero
lvl = level of picker's room;  left = amt;
for (m in party->members)                         // node {unit id +0, next +4}
  if (u = GameFindUnit(game, 0, m.id), u && u != picker && room(u) && level(u) == lvl
      && mode(picker) != 0 && mode(picker) != 17) {
    PartyGoldClip(u, share, &give, &over);        // give = min(share, cap(u) - gold(u)), over = share - give
    UnitAddGoldStat(u, 14, give);
    left += over - share;
  }
clip left at the picker's cap; UnitAddGoldStat(picker, 14, give); return the excess;
```

- [I] The count. `PartyForEachInLevel` calls the counter once for the unit itself when it has no room or no party.
  Otherwise it calls it for each member found in the unit's level, the picker included. `PartyCountAliveCb` adds 1
  unless `UnitIsDead`: flag byte `+0xC6` bit 0, or a player in mode 0 or 17, or a monster in mode 0 or 12.
  (0x005405A0–0x00540646, 0x005404F0–0x00540509, 0x005541B0–0x005541F6)
- [I] The paid set. A member is paid when it is found, is not the picker, has a room and is in the same level. The
  two mode calls take `ECX = ESI`, the picker (`mov ecx, esi` at 0x00540A73 and 0x00540A7E). So a member's own death
  is not tested here, and the payment loop can pay more members than `n` counted. (0x00540A47–0x00540AC7)
- [I] The member clip. `PartyGoldClip` (ECX = member, EAX = share, stack: &give, &over) sets `give = share`,
  `over = 0`. When `gold + share > cap` (signed `jle`), it sets `give = cap − gold` and `over = share − give`.
  (0x00540650–0x0054068F)
- [I] `UnitAddGoldStat` writes 0 when an add would pass the cap or go negative (items/0011 § 6). Every amount it gets
  here was clipped first, so the 0 write is not reached on a share. (fn:sub_0053FF00_UnitAddGoldStat@0x0053FF00)
- [I] **Arithmetic.** All signed 32-bit; `amt ≥ 0` (a pile's stat 14). With `p` members paid, the picker's part is
  `left = amt − p·share + Σ over`. While every paid member was counted, `p ≤ n − 1` and `left ≥ amt − (n − 1)·⌊amt/n⌋
  ≥ ⌊amt/n⌋ ≥ 0`. Each dead member in the level adds one to `p` and nothing to `n`. With one, `p = n` and
  `left = amt − n·⌊amt/n⌋ = amt mod n ≥ 0`. With two or more, `left` goes below 0 once `p·⌊amt/n⌋ > amt + Σ over`
  (for `n = 2`, `amt = 2` and two dead members, `left = 2 − 3·1 = −1`). The final add then takes gold from the picker
  or writes 0 (`UnitAddGoldStat`'s negative guard, items/0011 § 6). That branch needs four players in one party and
  is not checked here (Open questions). The subtraction can wrap only there: at the worst case (`n = 2`, six dead
  members, `p = 7`, no member at its cap) `left = amt − 7·⌊amt/2⌋` is −2 147 483 644 for `amt = 858 993 459` and
  would be −2 147 483 650 (below −2³¹, so it wraps) for `amt = 858 993 460`. (0x00540A1A–0x00540A23, 0x00540AB4–0x00540ABA, 0x00540ADF–0x00540B00)

### 2. The trade state machine (MP31)

- [I] **Request.** `UnitInteract` reaches `TradeRequest(game, requester, target)` at 0x00548E6B for a player target
  at distance ≤ 50 (`cmp eax, 0x32` at 0x00548E00, after the `0x005678A0` test). `TradeRequest` needs neither player
  busy (`PlayerIsBusy`) nor the classic end lock. It rate-limits on `PlayerData+0x54` and `+0x58` (1000 and 5000 ms
  windows). It needs both in a town level (`LevelIsTown`), sets each one's interaction to the other
  (`0x00554120(unit, 0, other id)`), and sets the states, requester 1 and target 2. Outside town it clears both
  interactions. (0x00566E60–0x00567013)
- [I] **The buttons** (`PktInteractButton`, jump table 0x00568620 over button − 2; the presser is EDX, the partner
  is found by the presser's interaction id):
  - **2:** if both are in states {1, 2}, or neither is `TradeBlocked`, it closes with `TradeClose(…, 9)`.
    (0x00568175–0x005681F7)
  - **3** (accept the request): if either is `TradeBlocked`, a presser in state 7 or 8 goes to 14 or 15 and any other
    state closes the trade with 12. Otherwise `A4Q2_ClassicEndLock` closes it with 9, and a presser not in state 2
    or a partner not in state 1 closes it with 12. Else `TradeOpen` (both 3) and two `TradeRecAlloc` calls; when the
    second fails, the first record is freed and errors are sent. `TradeRecAlloc` returns 0 when the player already
    has a record. (0x005681FC–0x005683D7)
  - **4** (accept): when either is `TradeBlocked` it sends message 0xBEE and stops; the end lock closes with 9. A
    presser not in state 3 gets message 0xBD2, and one with an item on the cursor gets 0xBD7. Otherwise the presser
    goes to 4, and if the partner is at 4 the trade commits (`TradeCommit(EAX presser; game, partner, pd presser,
    pd partner)`) and both `+0x58` get the tick. (0x00568499–0x00568573)
  - **7:** each side at 4 goes back to 3. (0x0056857F–0x005685C2)
  - **8** (gold, parameter = the amount): the Answer's gold-offer bullet. The unsigned `cmp [ebp+0xC], eax; jbe` at 0x005683E6, the
    cap clip at 0x0056843C–0x00568448, the store at 0x00568467.
  - 5 and 6 do nothing; 0x12–0x14 are the stash gold buttons and 0x17–0x18 the cube's (items/0008).
- [I] **The change lock.** `TradeItemTest` (from 0x00535676 and 0x00535697) puts both players in state 7 when an
  item moves in an open trade, and sets bit 22 of the presser's `Unit+0xC8`. The tick (`TradeStateTick`, event 13)
  steps 7 → 8. From 8 it clears bit 22 and either waits in state 11 until the record's `+0x14` time has passed, or
  goes back to 3. `0x00567400` (called from 0x0056063F) sets both records' `+0x14` to now + 10 000 ms and puts any
  side at 4 back to 3. So a change in the offer un-accepts both sides and holds the window about 10 s. Which item
  moves call `0x00567400` is not followed. (fn:sub_00567620_TradeItemTest@0x00567620, 0x005689D0–0x00568C3E,
  0x00567400–0x00567618)

```c
// fn:sub_00567C70_TradeCommit@0x00567C70, EAX = A (the presser), stack: game, B, pdA, pdB; ret 0x10
for (X, Y) in ((A, B), (B, A)):                       // first A's offer, then B's
  o = pdX->trade->offer;                              // +0x0C
  if (o) { if (stat14(X) < o) return TradeCancel();                       // signed jge at 0x00567C96 / 0x00567D3D
           if ((u32)(stat14(Y) + o) > (u32)GoldCap(Y)) { TradeCancel(); msg 0xA2D/0xA2E or 0xA41/0xA42; return; } }
if (!RoomTest(game->+0x1C, A, B, &side)) { both offers = 0; msg by side; return TradeCancel(); }   // 0x0063E370
if (!TradeItemsAllowed(A → B) || !TradeItemsAllowed(B → A)) return TradeCancel();
A->+0xC8 |= 0x800000; B->+0xC8 |= 0x800000; pdA->state = pdB->state = 9; queue event 13 for both;
if (!TradeMoveItems(A, B)) return TradeCancel();
if (!TradeMoveItems(B, A)) return TradeCancel();
for (X, Y) in ((A, B), (B, A)):
  if (o = pdX->trade->offer) { if (stat14(X) >= o) UnitAddGoldStat(X, 14, -o); PlayerGiveGold(game, Y, o); }
free both interactions and records; send 0x0D to both
```

- [I] `TradeMoveItems(X, Y)` walks X's inventory. For each item on page 2 (X's offer), it makes `ItemCopy` and renames the
  copy (`TradeItemRename`: an ear, base type 7, gets a personal name, an ear level and flag `0x8000`; an item with
  flag `0x1000000` gets the name only; the unit the name comes from, in `EDI`, is not followed). It then sets mode 4
  and page 0. It then places the copy in Y's inventory
  (`InvPlaceItem(game, Y, id, 0, 0, 1, 1, 0)`). A failed placement returns 0 with messages 0x9D1/0x9D2. A second pass
  removes X's items on page 1 (the view of Y's offer) and page 2. So Y receives the `ItemCopy` unit, not X's item;
  whether its unit id differs is not read here (`ItemCopy` not followed). (0x005670E0–0x0056729D, 0x00567070–0x005670D6)
- [I] **Gold at the commit.** The give does not depend on the take: `PlayerGiveGold` is called whether or not the
  `stat14(X) ≥ o` test passed (0x00567F68 `jl` skips only the take). The cancel tests above reached the commit with
  `stat14(X) ≥ o`, and nothing between them changes carried gold, so the take runs. `PlayerGiveGold` clips at the
  cap and drops the rest (items/0011 § 6). The cap test before it (unsigned) leaves nothing to drop.
  (0x00567F4A–0x00567FCC, fn:sub_0055B060_PlayerGiveGold@0x0055B060)
- [I] The trade reads carried gold (stat 14) only. The stash (stat 15) is not offered, tested or moved. (`push 0xe`
  before each `STATS_GetUnitStat` at the sites above, e.g. 0x005683DE, 0x00567C8B, 0x00567F5E)

### 3. The predictions for MP31 and MP32

[multiplayer/0001](0001-cases.md) § 2, rows MP31 and MP32, now name these. Every expected value is inferred until the
two-client run; a run raises a statement only where the case separates it from a wrong reading (review-fix 10).

- **MP32 (party gold).** H and J partied, both alive, in one level; H picks up a monster's pile of `A` (no player
  owner):
  - J's stat 14 rises by `min(⌊A/2⌋, cap(J) − gold(J))`. H's rises by `A − ⌊A/2⌋` plus J's overflow, clipped at H's
    cap, and anything past that is dropped at H. An odd `A` separates "the remainder to the picker" from an even split
    or "the remainder to the member". `A` above J's cap room separates the overflow return. (§ 1)
  - J in another level, or not partied: H alone, as items/0011 § 6. J dead in the level (counter case): `n = 1`, H
    alone; nothing is paid to J, because the `n ≤ 1` path never reaches the payment loop. The "paid but not counted"
    branch needs a third player (a living member and a dead one besides the picker), so two clients can't stage it.
  - Loggers: `GoldPickup` entry (pile amount), `PartyGoldShare` entry/return (0x00540900, `ret 4` at 0x00540B0E),
    `PartyGoldClip` (0x00540650) and the stat-14 writes of both players.
- **MP31 (trade).** H requests J in town; J accepts (button 3); H puts an item `X` on the trade page; J offers `g`
  gold (button 8); both press accept (button 4):
  - After button 3: both `PlayerData+0x50` = 3, both records' `+0x10` = carried gold at that moment.
  - After button 8: J's record `+0x0C` = `min(g, cap(H) − gold(H))`, or the trade closes (state 9 on both) if
    `g > gold(J)`.
  - After the second accept: H holds `gold(H) + g`, J holds `gold(J) − g`, and J's inventory holds a copy of `X`
    (the `ItemCopy` unit; its unit id is to be logged) while H no longer has `X`. Both states 9, then 10, then 0 on the
    tick (`TradeStateTick`). A change of the offer after one accept un-accepts both (states 7 → 8 → 3, or 11 for
    about 10 s) before the commit.
  - Counter cases: `g` above J's carried gold (closes); `g` above H's room (clipped at button 8); J's inventory with
    no room for `X` (cancel, state 5, nothing moved, the offers zeroed).
  - Loggers: `PktInteractButton` entry (button, parameter, presser), `TradeCommit` entry and the
    `TradeCancel`/`TradeClose` entries, `TradeMoveItems` returns, stat 14 of both, and the item lists (the copy's
    unit id).

## Data touched

- struct:Unit+0x10 (mode), struct:Unit+0xC8 (bits 10, 22, 23), `Unit+0xC6` bit 0 (the dead flag), `Unit+0x80`
  (party data, through `PartyIdOfUnit`).
- `PlayerData+0x50` (the trade state, 0–16), `+0x54`/`+0x58` (request ticks), `+0x5C` (the trade record:
  `+0x00` a pool handle, `+0x04` its allocation, `+0x08` the list of shown items, `+0x0C` the gold offer, `+0x10` gold
  at opening, `+0x14` the change-lock time).
- Stat 14 (`gold`, carried) only; stat 15 (`goldbank`) is not read by either path.

## Dead ends

- The decompiler shows `PartyGoldShare`'s mode test on the member. The disassembly loads `ECX` from `ESI`, the picker,
  for both calls (0x00540A73, 0x00540A7E). The decompile listing loses the register arguments of these
  `__fastcall`-like helpers, so the claims above come from the disassembly.

## Open questions

- [L] Whether the "paid but not counted" branch of `PartyGoldShare` (a dead member in the level) is reached in play,
  and what the picker gets when two or more dead members are paid (`left` below 0, then `UnitAddGoldStat` of a
  negative amount). Needs a party of three (one dead) or four (two dead), so it is out of the two-client run.
- [L] Which item moves call `0x00567400` (the 10 s lock) and `TradeItemTest`: their two callers (0x0056063F inside
  `InvPlaceItem`'s range, and 0x00535676/0x00535697) are not followed.
- [L] The room test `0x0063E370` and its "which side" output, and `0x005678A0` before the request: not read.
- [L] The client messages: the codes sent through `0x0053CAB0` (`DL` = 6, 9, 10, 12, 13 at the sites above) are
  not mapped to client behaviour.
