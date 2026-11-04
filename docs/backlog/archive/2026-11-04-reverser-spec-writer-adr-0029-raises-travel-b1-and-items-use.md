---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/items/0014-ground-items.md
  - ../../findings/frame/0003-timers-activation.md
  - ../../adrs/0029-import-slots-and-import-boundaries-in-emulation.md
resolution: "Imported in plan 0060 Phase 3, lane/s60: quests/travel B1 raised with its scope, the portal's own call [I]; items/inventory § J and items/use § A carry the rest; no timers statement imported. [items/inventory](../../specs/items/inventory.md)"
---

ADR-0029 is accepted and its scan kept (run:2026-11-04-lock-scan, items/0014's head). The architect's `lane/r29` review accepts the raises below (ruling on "can reach": [plan 0060's log](../../plans/done/0060-item-use-inventory.md#implementation-log)); this entry is what may rise, take the tags when the lane is on `main`. Every `drop` `[C]` is the code's map on declared rooms and one declared pool page: not a live run, and not how often a game's rooms make it matter.

**1. `specs/quests/travel` B1: the three bullets, as they should read.** Their anchors stay; add `run:2026-11-04-lock-scan`. Tag each `[C] (ADR-0015, ADR-0029 (a))`, dropping "(`drop`, pending ADR-0029)".

- First bullet: "**For size 1 and step 1 the search above holds to its return**, emulated through `GroundDropCell`, not on a live game: the rings 1 to 49 with ring 50 never looked at (radius 50), a ring's lowest `|dx| + |dy|` and the earliest of equals, the side columns before the end rows, the walk's test from the candidate's room. Family `drop`, 4 000 cases, 0 mismatches, with `EnterCriticalSection` and `LeaveCriticalSection` held at a `ret 4` stand-in, given that the allocation returned a writable block. Not evidenced: what the locks do (mutual exclusion, another thread's order, a wait, a fault), a lock guarding memory the search reads, the allocator's code on any state but the declared pool page, the block's address. The block only holds the origin's two words."
- Second bullet: "**The lookup's base room moves.**" and its text unchanged, adding: "By emulation only: no live search has separated it (`fixedbase` fails 95 of 4 000 cases on declared rooms, 0 of 81 live, run:2026-11-04-inventory-2)."
- Third bullet: "**`other` is the origin of a walk, not a second footprint**: the search hands it to `Walk`, from the candidate's room." Scope: at size 1 and step 1, through `GroundDropCell`, whose origin is its position. `[I]`, not above it: the portal's own call (`0x0056D213`, mask `0xC01`, size 3), under the existing `[I]` bullet on sizes and steps.

The sentence "It rises to confirmed (ADR-0015) with no re-run if ADR-0029 is accepted" goes. `Walk`'s bullet and the centre's `[I]` are unchanged.

**2. What plan 0060 Phase 3's `items/use` may state** (items/0014 §§ Answer, 1, 4).

- `[C] (ADR-0015, ADR-0029 (a))`, with the not-evidenced list and the "given" above: the search's start and its `else pos`, the rings and ties, the walk mask `0x801` (each bit decided), the cell mask's `0x200`, `0x400`, `0x1000`, `0x2000` and the ten bits it lacks, the moving base (by emulation only), the fallback's blocked start and the two null returns.
- `[I]`, not above it: **the cell mask's bits `0x1` and `0x800`**, which no case decides because the walk's first test is the same cell in the same room with those bits (`maskbits.txt`, 0 fails each; the value `0x3E01` is the immediate at `0x00555DE4`). No output changes at this caller, since either test refuses the cell; the sentence only must not claim the cell test separately, and must not carry it to a caller with another walk mask. Also `[I]`: zero draws (a static closure, 54 indirect unfollowed), and every caller other than the ground drop.
- `[C] (ADR-0021, ADR-0029 (c))`: `SrvPacketDispatch`'s passes reach the `IsBadCodePtr` call with the opcode's row pushed (106 of 106), `0x41` in mode `0x11` on one case, state 0. After that call, `[I]`: its result, the fatal branch, the handler's call. The refusals stay `[C] (ADR-0015)`.
- Unchanged by this entry: items/0015 and items/0016's live `[C]`s, the no-expiry reading's scope.

**3. Timers.** frame/0003 § 2's `timers` reads "given `IsBadCodePtr` returned 0", `[C] (ADR-0015, ADR-0021, ADR-0029 (b))`, and that value and the fatal branch `[I]`. No reviewed spec cites this run's timers today (`grep frame-emu-3 docs/specs`); if a frame spec does, it carries that "given".
