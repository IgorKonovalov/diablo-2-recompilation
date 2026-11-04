# 0007 — The server frame, part 7: the frame-window batch

> **Subsystem:** sim/frame
> **Question:** with every LCG step logged by site (`XS`) and the chain's rule of the `lane/p55b` review applied (arithmetic, class, touch table, per-`KD` even, draw-free kinds, order), do the pack and maze windows of the stock game chain with nothing resynchronised, and how many shared-seed pairs run in the predicted order?
> **Date:** 2026-11-04   **Plan:** 0055 (Phase 2b)   **Status:** open (predictions committed; the kept sessions follow)

## Predictions (committed before any kept log of the batch exists)

Tools: logger rev 2 (`tools/gdb/frame.py`), reader rev 2 (`tools/frame_xs.py`, `tools/frame_window.py` tables), runner `tools/frame_sessions.py`, all at the commit that adds this file. The dev sessions `dev-2026-11-04-frame2-*` (5501 pack; 5503 pack and maze) are the basis; none of their figures is cited as a result.

- [I] **Scenes, one scene per fresh process:** `pack1` (seed 5501: Blood Moor's Fallen by `explore`, three windows of 500 frames, the second covering a frame ≡ 0 mod 8192, the third with `FRAME_HOOKS=1`), `maze` (seed 5503: `explore` stopped at level 2, then the descend to the Den of Evil, three windows), `pack` (5505), `maze` (5505) as the pairs need. The town's three windows of `run:2026-11-04-frame` stand (a log with no `XS` is read with no touch allowed).
- [I] **(a) whole and (c) carried:** every window; pack 30 to 60 lines per frame (dev 5501: 36.3 and 40.0; stop 123.9), maze 55 to 100 (dev 5503: 79.5, 56.3, 68.7; stop 152.7); stops per frame 45 to 70; 15 to 25 frames per wall second. The 5503 *pack* was 177 to 203 lines per frame in the dev session (41 `UE0` a frame: a crowd) and is not used; a kept pack window over 123.9 stops that session.
- [I] **Arithmetic:** 0 `arith` failures in every window (the dev windows: 0 of 8 over 5 windows once the client steps are not applied to the chained seeds and the fresh-seed ambiguity is read). A failure is a mismatch to trace; a mismatch traced to the logger is Q2's trigger.
- [I] **Class:** every touch is at a site of the committed `TOUCH` table under its trigger. The dev sessions showed kill, room, `killev` and owner touches and **no defender touch**; the defender rows are the specs' (combat/to-hit, items/economy § H) and are predicted to be met in some window without being known to be. A site not in the tables fails its window; the window is then uncounted, and the site, traced to a spec, goes in by a commit for the next one.
- [I] **Client steps** (between the ticks, `PASSDRAW` rows marked `client`): hundreds per window (dev: 840 to 850 per 500 frames in the 5501 pack), applied to no chained seed, counted apart. The chain holding with the client steps not applied is the test that they are on the client's copies of the room seeds (a server room seed would otherwise be off by the 86 steps the reader first applied).
- [I] **`KD`:** per `KD`, the game-seed steps at `UnitSeedInit`+0x41 and `ItemSeedInit`+0xF are even, two per dropped item, 0 on a NoDrop (dev: 13 `KD`, counts 0, 0, 2, 2, 2…); sub-missile creations in the same event are at other sites and are not counted. A champion's or unique's kill: more items, still even.
- [I] **Draw-free:** no `own` step in a kind 11 or kind 6 event (dev: 17 kind-11 runs per scene-window, 0 with an own step; kind 6 runs few).
- [I] **Order:** 0 rank inversions, 0 slot inversions, 0 every-frame inversions (dev: about 5 300 `UE0`, all placed).
- [I] **Shared-seed pairs** (two units' top-level events with a game-seed step in one frame): 1 to 3 per 500 frames in the pack, about as many in the maze; **fewer than 20 after the three sessions is likely** (the p55b rate was about 1.3 per 250 frames) and is a stop. All handed and in rank order.
- [I] **Timers:** `T20`, `D12`, `U11` each on its period in every window; `S1500` met by the town window of the pilot run; a `mod 8192` frame in the first pack session's second window with `SaveGameClients` logged as a boundary oracle; a room activation in each pack window.
- [I] **Maze/hook window:** the `FRAME_HOOKS=1` window places the 65 universal hooks by the open event's rank in `WEND`; a hook never reached in the scene is named as not reached.
- [I] **Chained events:** pack 5 000 to 6 000 and maze 3 000 to 6 000 per 500-frame window.

## Answer (summary)

_(filled after the kept sessions)_

## Leads used

None.

## Functions

No new name and no symbol row.

## Open questions

- `[L]` the extents of the table rows are the next symbol of `re/symbols.csv`, not the function's own end; a row that is wider than its function would accept a neighbour's step. The kept windows' touch sites are listed by `tools/frame_sites_list.py`.
