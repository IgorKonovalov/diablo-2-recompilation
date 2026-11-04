# 0015 — Item use and inventory: the first harness run (ground drops, the monster drop's `+0x24`, two forced requests)

> **Subsystem:** items/use
> **Question:** on a live game, does a drop's cell, its `+0x24` expiry and its sweep match items/0014's reading; what do `0x18` to page 4 with no stash open and `0x23` past `numboxes` do?
> **Date:** 2026-11-04   **Plan:** 0060 (Phase 2, first lane run)   **Status:** for review (`lane/p60`)

Wine session under gdb on slot 2, one fresh process (`harness-play.md` § Fresh process, rule 1), logger `tools/gdb/inventory.gdb` with `tools/gdb/inventory.py` and `tools/gdb/pilot.py`, driven by `tools/inventory_sessions.py` (session `main`), predicted and checked by `tools/inventory_check.py` against `tools/item_inventory.py`. Run record: [experiments.md § run:2026-11-04-inventory](experiments.md). Tools at `main` + commit `ae44be8c` (the predictions file `0015-predictions-main.pred` was committed, `b14f3e1e`, before the check ran; the checker was then edited once, see § Mismatches).

## Answer (summary)

- [C] **A monster's or chest's drop has item data `+0x24 = 0` at creation, 27 of 27** (`DropCreateItem` after `ItemCreate`, `0x0055A6B4`), and five of them (ids 58, 64, 65, 66, 67, created at frames 2 698..5 013) were listed in every sweep dump from the first after their creation to the last (frame 22 500), 12 to 14 dumps each, `+0x24 = 0` every time and none freed (79 sightings in all). The claim of items/0014 § 3 that no expiry is written on that path holds on a live game, for the stock path `ItemCreate`'s `DropCreateItem` caller. (run:2026-11-04-inventory, `check-main.txt`, 0x0055A6B4, 0x00558BB7, fn:sub_0055A550_DropCreateItem@0x0055A550)
- [C] **A player's drop is swept at the first multiple of 1 500 at or past `frame + 15000`:** 4 drops of quality 2 (frames 3659..3863, `+0x24` 18659..18863) were freed at the sweep of frame 19 500 (`0x00558BEC`), each with the control, five monster drops lying beside them, still there at 21 000 and 22 500. Scope: quality 2 only, one sweep, no message or seed logged (not read). (`2026-11-04-inventory-s2-6001-main.log`, 0x00558BEC)
- [C] **`ItemPlaceOnGround`'s expiry, 10 of 10: `+0x24 = frame + 15000`**, quality 2 potions of the `hpot` type. Quality 4, 5..9, gold, filler and quest bases were not dropped, so the other branches stay at items/0014's emulation. (fn:sub_00558AA0_ItemPlaceOnGround@0x00558AA0, 0x00558B2B)
- [C] **A monster's drop that sat in a room that went inactive came back with a non-zero `+0x24`:** three drops (ids 55, 56, 57 at frames 2171..2290) reappeared at the same class and cell as ids 60, 61, 59 at the sweep of frame 3 000 with `+0x24 = 17 766` each. 17 766 = 2 766 + 15 000 fits `max(saved, frame + 15 000)` for a restore at frame 2 766 (items/0014 § 3 row 3); the restore's frame and the saved value were not logged, so the `max` and the "saved" half stay `[I]`, and no later sweep reached them (the room went inactive again before 17 766). This was met by the run, not predicted: the committed predictions did not cover it. (check-main.txt, fn:sub_00541990_InactiveItemRestoreOne@0x00541990)
- [C] **The ground drop's cell search, 37 of 37 cases to the cell**: the model `ground_drop_cell` over the logged collision window gave the logged cell for 23 starts at `(x + 2, y + 3)`, 13 ring-1 results and 1 ring-2 result, (no seed was logged around a drop: the "no draw" half stays `[I]`). The controls that fail on this batch: `nooffset` 37, `offset32` 37, `first` 13, `noitembit` 12, `leq` 11, `capsfirst` 8, `linecellmask` 4. **Not separated: `noline` and `fixedbase` fail 0 of 37**, so this run does not decide the walk mask or the moving base room; no case had a blocked walk, a fallback or a null room. This is a second route for the start, the masks' item bit and the ring order up to ring 2. (run:2026-11-04-inventory, fn:sub_00555DA0_GroundDropCell@0x00555DA0, 0x00555DA0, 0x00555DF5)
- [C] **`0x18` to page 4 with no stash open, in town (level 103): accepted** (handler return 0, the item on page 4 at the cell sent), as items/0013 § 5 reads and against a model that refuses a closed stash. One case, an edited request (forced, below). (fn:sub_0054ABB0_Pkt18CursorToPage@0x0054ABB0, `ARM`, `PKR`)
- [C] **`0x23` with box 12 on a 12-box belt (a Heavy Belt, `numboxes` 12): the item stays in box 12.** The server does not test `numboxes`, as items/0013 § 6 reads. One case, an edited request (forced); whether a smaller belt's overflow later takes it was not run. (fn:sub_0054B3E0@0x0054B3E0, `ARM`, `PKR`)
- **Not run, stays short (§ Short):** the potion doubling and its two draws (items/0012 cases 1..4), items/0012 cases 5..20, items/0013 cases 1..5, 8..13, 15..25, items/0014 cases 3, 4, 6, 9 (the return to a deactivated room), 10..20.

## Forced states and edits (a review rules on these)

- **Two requests were edited in flight.** `tools/gdb/inventory.py` overwrites, once, the packet's page dword (`+0x0D`) of the next `0x18` with 4, and the box dword (`+0x05`) of the next `0x23` with 12, at the handler's entry; each writes an `ARM` line (`was` 0 and 8, `now` 4 and 12). The client UI cannot send either (no stash is open, the belt has no box 12). Everything after is the game's own code. These two outcomes are the server's answer to a crafted request (ADR-0014 scope), not a state a player reaches.
- No other game memory is written. The character is a built recipe (`tools/d2s_recipes/inv-sor.json`, a belt of 12 potions, 12 potions in the inventory), every skill and quest as `combatsor.json`; the Act IV start is the recipe's.

## Mismatches

- **Main prediction: 86 predictions, 0 mismatches against the logs, 6 explained.** The committed file predicted the 6 player drops made in the Act IV town (frames 100..1000, `+0x24` 15 100..16 000) freed at the sweep of frame 16 500. They were not: the character had left the town, its rooms were inactive, and no later sweep dump lists them. The prediction did not condition on the room staying active; this is the harness's error, not the game's. The checker was changed after that first check (the item is classed "room inactive at every later sweep: not a sweep case" when no later dump lists it and no free is logged); the committed predictions are unchanged and the first check's count (6 mismatches) is in `experiments.md`. The 4 drops made in the active room are the sweep cases that decide.
- The development checker run on `dev-…-drops1.log` (10 drops, all predicted) is a development log.

## Short

- The walk mask (`noline`) and the moving base (`fixedbase`): no drop beside a wall or at a room's edge, so cases 3, 4 of items/0014 stay with the emulation (ADR-0029 pending); the `drop` statements stay `[I]` beyond ring 2 and for the fallback and null returns, and `[C]` only for what the table above lists.
- Draws: no seed was logged around a drop or a move; "no draw" for a drop stays the closure reading `[I]`.
- Case 8's "removal message" and "no draw" were not logged; case 9's `max(saved, ·)`, the player's drop past half its life, and the sweep of a restored item: not run.
- The potion doubling (the highest-value remainder after § above) and the rest of the 65 cases: the lane ran to the checkpoint with the ground and the two requests first, as ranked.

## Functions

| Address | Name | Role here | Tag |
|---|---|---|---|
| `0x00555DA0` | `sub_00555DA0_GroundDropCell` | the search: start, masks, rings 0..2 observed in 37 cases | C for those (raised in `re/symbols.csv`; the walk, the moving base, fallback and null returns unobserved: `[I]`) |
| `0x00558AA0` | `sub_00558AA0_ItemPlaceOnGround` | the expiry write, quality 2 `+15000` only observed in 10 cases | C for that branch (raised; other branches `[I]`/emulation) |
| `0x0054ABB0` | `sub_0054ABB0_Pkt18CursorToPage` | page 4 in town, no stash open: accepted, 1 case | I (one forced case; not raised) |
| `0x0054B3E0` | `sub_0054B3E0_Pkt23CursorToBelt` | box 12 stays on a 12-box belt, 1 case | I (one forced case; not raised) |
| `0x00558B90` | `sub_00558B90_ActExpiredItemsFree` | the sweep: 4 frees at the predicted frame | I (owned by frame/0003; the claim above is the item case) |

## Open questions

- `[L]` The restore's frame and `saved` for the three restored monster drops: log `0x00541990`'s locals in the next run.
- `[L]` A drop that ends in ring 3 or later, beside a wall, with a null room: a session that stands at a wall (a planner over the collision window, not built).
