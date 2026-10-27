---
from: reverser
to: archivist
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
  - ../../findings/save/experiments.md#run2026-10-27-sweep-d2s-play
resolution: "lane/a50t: tools/d2s.py build gains two opt-in, default-off test-state keys: item \"lone_follower\": true (a follower such as 49 without its head written alone with its own Save Bits) and merc \"name_unchecked\": true (any u16 name id); pinned in tools/test_d2s.py (KeysTest.test_lone_follower_test_state, MercTest.test_name_unchecked_test_state) [d2s format](../../formats/d2s.md#mercenary-saves)"
---

Two `tools/d2s.py build` refusals left plan 0038 batch H1b without a separating input (run:2026-10-27-sweep-d2s-play).
Both refusals are right for a normal recipe; what is asked is an opt-in **test-state key** for each, built as a forced
state (harness-play § The character: the run record then says so), so a later harness batch can feed the reader and
writer the case.

1. **A lone group follower** (save-d2s row 124, "Follower read alone takes the default path", shortfall): `build`
   raises `stat %d without its group head %d` (`tools/d2s.py`, the followers check of the property writer, around
   line 1112) for a property list with `fire-max` (stat 49) and no `fire-min` (48). Wanted: an item key (for example
   `"lone_follower": true` on the item, or a per-property flag) that writes the follower with its own `Save Bits` and
   no head, so the game's reader takes its default path on it.
2. **A mercenary name id past the row's range** (save-d2s row 48, the name reset past `+0x116`, raised in part):
   `build` raises `merc: name … outside 0 .. N` (around line 1569). Wanted: a merc key (for example
   `"name_unchecked": true`) that writes the stored name id as given, so the reader's reset of a name beyond the row's
   `NameLast` can be met.

A pin in `tools/test_d2s.py` for each key is welcome. Not blocking: H1b files both rows as they stand (124 shortfall,
48 in part).
