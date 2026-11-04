# 0006 — The server frame, part 6: frame windows on the harness

> **Subsystem:** sim/frame (run:2026-11-04-frame)
> **Question:** does a stock game, logged in full over 250 or more consecutive frames in a small scene, chain every entry seed to the previous logged reading with nothing resynchronised, and in which order do shared-seed events run?
> **Date:** 2026-11-04   **Plan:** 0055 (Phase 2b)   **Status:** open (reviewed 2026-11-04, `lane/p55b`: the town pilot passes; the pack pilot's (b) is decided by the review below: every mismatch traced at `[I]`, none to the logger, not Q2's trigger; the batch is next, plan 0055's log)

## Predictions (committed before the kept session's log exists)

Tool revision: `tools/gdb/frame.py` and `tools/frame_window.py` at the commit that adds this file (the smoke sessions
`dev-2026-11-04-frame*` found two defects, both fixed and committed first: the post-call SV1 sites firing without an entry, and the
reader not printing its outcome mix). The model is the reader's chain: a seed object's entry reading equals its previous logged
reading (handed), a draw before an `FP` or `TM` site is located, every other difference is a mismatch.

Pilot (Act I town, normal, seed 5501, slot 1, first window of 250 frames, a fresh process):

- [I] (a) whole: an `FT0` and an `FT1` for each of 250 consecutive frames, 0 unparsed lines, every pair closed. (run:2026-11-04-frame)
- [I] (b) unmoved: 0 mismatches, 0 located. The game seed does not move in the town window (a dev window showed 0 game-seed (run:2026-11-04-frame)
  moves in 750 frames), so it is handed at every reading; unit seeds move in about 4 to 10 `UE0` events. Chained events 450 to 750.
- [I] (c) carried: about 10 s wall, about 25 frames per wall second (the stock rate), 7.5 to 9.5 lines per frame (0.5 to 0.6 of (run:2026-11-04-frame)
  `estimate13` mid, 15.9), about 19.4 stops per frame, `QE`+`QF` per `UE0` near 0.53, the session far below 177 860 lines.
- [I] Timers in the window: `T20` 12 or 13, `D12` 21, `U11` 22 or 23, `S1500` 0, no `RC`, no `SV0`, no shared-seed pair. (run:2026-11-04-frame)
- [I] What the town window cannot test: with the game seed never drawing, the game-seed chain is tested only as "unchanged". (run:2026-11-04-frame)

### Predictions for the pack pilot (committed before its kept log exists)

Tool revision `8f026bf2` plus this file's commit. Cold Plains by the waypoint, seed 5501, slot 1, first window of 250 frames,
a pack in range (the runner waits for three live monsters within 22 sub-tiles), Nova by the pilot. The dev sessions
`dev-2026-11-04-frame-g` and `-h` (the same scene) are the basis; they showed 15 000 to 18 000 lines per window.

- [I] (a) whole: passes (the one logger defect the dev sessions showed, a second `UE1` at the join of the callback path, is fixed). (run:2026-11-04-frame)
- [I] (c) carried: passes; 55 to 75 lines per frame (1.3 to 1.8 times `estimate13` mid 41.3; the 3x stop is 124.0), 70 to 90 stops (run:2026-11-04-frame)
  per frame, 20 to 25 frames per wall second, the session far below 177 860 lines.
- [I] (b) unmoved: **does not pass**. The dev windows held 8 and 10 mismatches over 6 400 to 7 500 chained events, all on
  monsters' own seeds (stepped 1 to 14), none on the game seed or a player's. The reading to test: a monster's seed is
  drawn inside another unit's event (a Nova missile's hit, a kill's drop roll: the dev trace `FRAME_TRACE` showed five
  `0x0055879F`-`0x0055891A` steps of a dead monster's seed inside a missile's `UE0`/`UE1`) and the chain keyed by the event's
  own unit cannot see it. Predicted: 5 to 15 mismatches, every one a unit seed of type 1 stepped inside a window in which a
  missile (type 3) event was open between the two readings; none on `G`, none on a player.
- [I] Chained events 5 000 to 9 000 in the window; shared-seed pairs 0 to 5. (run:2026-11-04-frame)

## Answer (summary)

- [C] **The Act I town pilot passes all three tests** (run:2026-11-04-frame, `2026-11-04-frame-s1-5501-town.log` `dfbd4401…`, first window frames 501-750):
  (a) 250 consecutive `FT0`/`FT1` pairs, no gap or repeat, 0 unparsed lines, every pair closed; (b) 0 mismatches, 0 located draws,
  0 reversed-inside, 413 chained events (426 `UE0`), 852 entry and 852 exit readings; (c) 10.0 s wall for 250 frames,
  25.1 frames per wall second, no crash, hang, lost input or watchdog stop. The two further town windows of the session
  (the walk, 17 `MSG0`, and the `mod 1500` frame 1500) also pass (a) and (b): 573 and 557 chained events, 0 mismatches, 0 located.
- [C] **The pack pilot fails (b)** (`…-5501-pack.log` `35915470…`, frames 1280-1529, Cold Plains by the waypoint, Nova): (a) passes, (c) passes, (run:2026-11-04-frame)
  (b) shows **8 mismatches in 3 369 chained events** by the reader's rule at that revision (an entry equals the previous logged reading of that unit), every one a unit seed stepped between two logged readings (stepped 1, 1, 3, 4,
  5, 5, 5, 8): seven on monsters (type 1) and one on the player (type 0, id 1). The lane read this as Q2's trigger; the review rules it is not (§ 6). The maze scene was not run.
- [I] **What the traced draws are.** In a development session of the same scene with `FRAME_TRACE=1` (`dev-2026-11-04-frame-h`, 10 mismatches, 34 steps in all), 8 steps had a trace line, on two of the ten units: 5 of unit 20's 8 and 3 of unit 18's 14. They are
  steps of a monster's seed at return addresses 0x0055879F to 0x0055894F in `ITEMS_DropRollQuality` (fn:ITEMS_DropRollQuality@0x00558640) inside an open
  missile (type 3) `UE0` pair: a kill's drop roll drawn on the dead monster's seed, as items/quality and items/tc state for `src.seed`. The other 26 steps had no trace line:
  the trace covers the six RNG entries only (0x0045C370, 0x0045C390, 0x0045C3E0, 0x00472210, 0x00472240, 0x00472280), not the inlined steps, among them `TC_ResolveDrops`' pick draw (0x0055AA03-0x0055AA3F).
  The logger writes nothing (rule 17, the test). *Corrected at the review:* the same units did not step the same amounts in the traced run: dev-h's ten mismatches are other units and amounts, and it shares no game-seed value with the kept window. The untraced dev-g does: 7 of its 8 mismatches are the kept window's units and amounts, and the two logs share a first run of 10 game-seed values with their windows opened 10 frames apart. That is one input script replayed, read as "breakpoints that stop at other frames moved nothing there", `[I]`, not as a second source for what the steps are.
- [I] **All 8 of the kept window are attributed by the review** (§ 6): seven kills' drops on the dead monster's seed in a missile's event, and one monster's melee hit on the player. No site is logged for any of them in the kept log. (run:2026-11-04-frame)
- [I] **The chain keyed by an event's own unit cannot hold in a scene with hits.** Unit seeds are drawn inside other units' events, as combat/to-hit, combat/delivery, items/economy § H and items/tc already state per draw (rule 18), and ADR-0022's context names the case ("a defender's seed hit twice in one frame"). It is a result of the window about the reader's model, not about the logger. The architect's ruling and the chain's new rule are in plan 0055's log. (run:2026-11-04-frame)

## Leads used

None.

## Functions

No new name and no symbol row. Named by the review: `ITEMS_DropRollQuality`, `TC_ResolveDrops`, `sub_005A6FF0_MonDeathEvent`, `COMBAT_DefenceRoll`, `COMBAT_DurabilityLoss`, `ITEMS_DurabilityLossRoll` (rows exist).

## Walkthrough

### 1. What the smoke sessions found (tools, not the game)

Four tool defects, each fixed and committed with a test where no game is needed (`tools/test_frame_window.py`, 16 tests): (1) `SV1` was logged at the three
instructions after the `SaveGameClients` calls, which the branch that skips a call also reaches (2 `SV1` per frame, no `SV0`): it is now logged only after an
`SV0`; (2) the callback path of every unit-event site jumps to the dispatch call's next instruction, so both `UE1` breakpoints fire for one event
(0x00540FB4 jumps to 0x00540FC9, and the nine like it): the second logs nothing (4 `LOGERR` in the first pack window); (3) the `SpecNova` recipe starts in
Act IV (difficulty byte 131; `RL` `lid` 103), so the first "town" session was the Pandemonium Fortress: the frame sessions use `tools/d2s_recipes/framenova.json`
(128) and refuse a session whose first level is not 1 (that log is kept as `dev-act4-*`, its window passed all three tests as well); (4) Teleport does not cast
in a town room (`InTown` clear), the hop did nothing and no message was sent: the town's second window walks (`hop --walk --hop-times`).
The Act I waypoint is at (4884, 5629) for map seed 5501 (an `OU0` of an objects log; the player starts at (4863, 5653)); another seed moves the town, so the
sessions use seed 5501. The pack scene waits for three live monsters within 22 sub-tiles (the `MON` line) before its window. The reader prints each window's
mismatches, located draws and outcome mix. The smoke sessions needed `--view-h 0` (the display shows 600 rows).

### 2. Figures the record states

| | town window 1 | pack window 1 |
|---|---|---|
| frames | 501-750 | 1280-1529 |
| wall s, frames per wall s | 10.0, 25.1 | 10.4, 24.0 |
| lines, per frame | 1 792, 7.17 | 8 744, 34.98 |
| `estimate13` mid, ratio | 15.9, 0.45 | 41.3, 0.85 |
| stops, per frame | 4 542, 18.2 | 11 497, 46.0 |
| `estimate13` stops | 32.9 | 58.3 |
| `QE`+`QF` per `UE0` (stated mid) | 0.90 (1.35) | 0.19 (1.01) |
| `UE0` / chained events | 426 / 413 | 3 699 / 3 369 |
| mismatches / located | 0 / 0 | 8 / 0 |
| shared-seed pairs (handed, in pass order) | 0 | 2 (2, 2) |
| timers `T20`, `D12`, `U11` seen of due | 12/12, 21/21, 23/23 | 13/13, 21/21, 23/23 |
| room activations (`RC`; in a `NewRoomsUpdate` walk) | 0 | 9 (1) |

gdb's own hit count: `WEND.ghits` is `{}` in every window, so the per-breakpoint count is `WEND.hits` (town window 1: `FT0` 250, `FP` 2 000, `ACL` 250, `UE0` 426,
`UE1` 426, `SV1` 500 (hits; none logged), `TM` 56, `QE` 381, `SYS` 2). The session's logger lines: 6 782 (town; 6 026 in its three windows), 10 038 (pack), far below Q2's 177 860. (*Corrected at the review:* 2 321 and 10 037 were the first checks, taken before the log was complete; the first check is kept under `first/` as it stood.)
Draw-free kind-11 runs (entry and exit seeds equal on every seed logged): 8 of 8 in the town window, 8 of 8 in the pack window.

### 3. Predictions against the outcome

The town predictions (committed before the kept log) missed on two figures: 413 chained events against 450 to 750 and `QE`+`QF` per `UE0` 0.90 against about 0.53,
because they were taken from the Act IV smoke window. The pack predictions held for (a), (c) lines per frame missed (35.0 against 55 to 75), chained events missed
(3 369 against 5 000 to 9 000), mismatches 8 against 5 to 15 held, and "none on a player" **failed**: one mismatch is the player's (`('U', 0, 1)` stepped 4, 66 `UE0`/`UE1` lines between).
The player's step is untraced (no trace line in the kept log, none in the dev runs).

### 4. What the zeros test, and what they cannot

- [I] The town window: the game seed never moved (0 `G UE0`, 0 `FP`/`TM` with a draw), 6 `UE0` moved a unit seed. Its 0 mismatches test that no unit seed (run:2026-11-04-frame)
  moves outside its own events in a quiet town and that the game seed is unchanged; the reader's negative controls (a gap, a repeat, an unclosed pair, a seed off by one,
  a reversed pair, an unparsed line, stray text, a lost `FT1`; `window-selftest`) each fail the test they are for. The town cannot test a draw order.
- [I] The pack window has 11 `UE0` that moved the game seed and 16 that moved a unit seed, 2 shared-seed pairs: the chain was tested where seeds move, and it failed where another unit's event moves a seed. (run:2026-11-04-frame)
- [I] Boundary oracles: none were declared in the town or the pack window. *Classified at the review:* the window's monsters are `corruptrogue1` (class 43) and `cr_lancer1` (165), with `brute1` (28) in the level, from the `MON` lines and `tools/monpool.py pool` for seed 5501 (level 3: 28, 165, 43). None is in plan 0052 P3a's tier, so this is not the Fallen or shaman pack the `lane/s52a` ruling asks for, and the window does not count towards the pack's floors. (run:2026-11-04-frame)
- [I] Separation (ADR-0028 item 7): of the pack window's 3 369 chained events, 3 356 entries are `UE0`, and only the 8 mismatched ones and the entries after the 16 seed-moving `UE0` could have told a step from no step; the rest compare a seed nothing drew on. The rank and slot orders (§ 6) are the window's other test. (run:2026-11-04-frame)

### 5. Not done

The maze scene, the batch (the floors: 10 windows of 250 frames in three scenes with two windows each, 5 000 chained events, 20 shared-seed pairs; a `mod 8192` frame is logged only if a window holds one) and the
`lane/s52a` scene-kind bookkeeping (tier kinds against boundary oracles) were not run: the lane stopped at the pack pilot. Met so far: one town session of 3 windows (750 frames, 1 543 chained events), `mod 1500` frames in the town's third window and the pack's (frame 1500 in both), no `mod 8192`, and in the pack window, which does not count: 2 shared-seed pairs, 9 room activations (1 in a walk).

### 6. The review's attribution of the 8 (2026-11-04, `lane/p55b`)

From the kept log (`35915470…`) by `python3 -I tools/frame_foreign.py` (a review tool, `3adda14c…`; its output is the same each run), which holds a step count, the `QE` lines and the game-seed steps, no site. Each count below is the kept log's; what the draws are is a reading of the reviewed specs, so all `[I]`. (run:2026-11-04-frame)

| unit (class, mods) | steps | queued on it between the readings, inside | game-seed steps of that event |
|---|---:|---|---:|
| 1:23 (`corruptrogue1`, champion) | 5 | kind 12 at +4, kind 1 at +24, frame 1304, missile 384 | 6 |
| 1:22 (same) | 5 | same, frame 1306, missile 367 | 6 |
| 1:24 (same) | 8 | same, frame 1306, missile 360 | 6 |
| 1:21 (same) | 5 | same, frame 1307, missile 362 | 6 |
| 1:29 (`corruptrogue1`) | 1 | same, frame 1452, missile 437 | 0 |
| 1:31 (`cr_lancer1`) | 3 | same, frame 1513, missile 512 | 2 |
| 1:30 (`cr_lancer1`) | 1 | same, frame 1521, missile 484 | 0 |
| 0:1 (the player) | 4 | none on it; between the readings, monster 28's melee hit, frame 1440 | 2 (monster 28's own event) |

- [I] **Seven are kills.** The two queue lines inside one missile's event are the monster's death (`MON` shows mode 0, then 12 at the kind-1 frame; the unit runs nothing after its kind 1). The window has exactly seven monsters so queued by another unit's event, and they are exactly the seven mismatches on monsters: a one-to-one match neither side of which the reader used. The steps are `TC_ResolveDrops` and `ITEMS_DropRollQuality` on `src.seed` (items/tc § Draw order; items/quality). (fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0, fn:TC_ResolveDrops@0x0055A6D0, fn:ITEMS_DropRollQuality@0x00558640)
- [I] **The tables separate them.** A champion (mod 16) takes `TreasureClass2`, `Act 1 Champ A`: `Picks` −2, one `Act 1 Citem A` and two `Act 1 Cpot A`, so three item picks, and each of the four champions' events steps the game seed 6 = 3 × 2. A plain unit takes `TreasureClass1`, `Act 1 H2H A`, `Picks` 1, `NoDrop` 100: one step and no game-seed step when the pick is NoDrop (29, 30), or an item, 2 game-seed steps (31). Two game-seed draws per dropped item is items/tc H7. (tbl:TreasureClassEx.txt:Picks, tbl:MonStats.txt:TreasureClass1) Read at each group's row A; neither the level walk nor the step counts were replayed through `tools/tc.py`.
- [I] **The player's 4 is monster 28's melee hit in its attack-frame event** (frame 1440, mode 4 beside the player, kind 0): one shield block `Range(100)` on the defender's seed (combat/to-hit C2; the recipe's *Lidless Wall*) and armour wear, `RangeB(7)`, `RangeB(W)` and one step on the defender's seed (items/economy § H), with `GetHitRoll` drawing nothing below `hp ÷ D` (anim/timing M2; no `QE` on the player). (fn:COMBAT_DefenceRoll@0x0057DFB0, fn:COMBAT_DurabilityLoss@0x0057D3D0, fn:ITEMS_DurabilityLossRoll@0x00559E30) The same event steps monster 28's own seed 10 and the game seed 2, and queues its kind 1 at +24; `MON` lists it in mode 0 at frame 1452 and in mode 12 at frame 1464: it reads as dying in its own event, with one item, on the recipe's *Wartraveler* (`thorns`). That cause is a reading with nothing logged for it. No other composition of 4 is excluded by this log.
- [I] **Order, the kept lines:** over the four windows' 5 264 `UE0`, 0 frames run a walk of a lower rank after a higher one; 1 484 slot events whose `QE` is in the window run in queue order, 0 inverted (town 1 119, pack 365). This is the plan's own question and the reader did not test it; the next lane's does. (run:2026-11-04-frame)

## Open questions

- `[L]` the sites of the 8 (§ 6 is a count and a reading): the next lane's `XS` lines hold them. The inlined steps are the 852 sites of `tools/gdb/lcg-sites.txt` (rng/0001; `tools/gdb/player.py` and `tools/gdb/stats.py` already read that list).
- `[L]` sound: every session ran with `-ns` (the runner's default, no `--sound`); no figure here is known to depend on it, and none was run with sound.
