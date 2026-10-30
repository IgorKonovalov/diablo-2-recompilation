# 0055 — The server frame: the game tick, the unit update order, the event queue and the timers, checked in frame windows (ADR-0022, simulation phase 6)

> **Status:** approved (owner, 2026-10-30: "approve as recommended", all eight scoping questions answered as recommended); drafted 2026-10-30 (architect, `lane/plans54`)
> **Created:** 2026-10-30
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0021-observed-boundaries-in-emulation, 0022-scope-server-frame

## TL;DR

**Question:** in one server frame, in what order does the game visit its passes, its rooms, its units, its event queue
and its timers, and so whose draws come first on a seed two events share? [ADR-0022](../adrs/0022-scope-server-frame.md)
(accepted 2026-10-27) opens this as a sixth simulation phase and asks for its plan; this is that plan. When it is done:
- `docs/findings/frame/` names `GameTick` and every pass it makes, `GameRunUnitEvents` with the per-type event lists
  and their order, the event queue's insertion and run rules, the timers and their periods, the room activation order,
  and the point in the frame where client messages are applied, with the draws of each pass per seed;
- `tools/frame.py` predicts the order of the events in a frame, checked first on the kept logs of plans 0037–0052
  and then in **frame windows** (ADR-0022): runs of consecutive frames in a small scene in which every in-scope event
  of every unit is logged and every entry seed is asserted, none resynchronised;
- `docs/specs/sim/frame.md` (research-map row `sim/frame`) is reviewed, drlg/lifecycle § A points to it, and the chain
  spec's activation-order `[L]` has an answer or a stated limit.

## Context

- **The decision and its gates** (ADR-0022): this plan's tables and static reading may start once plan 0052's P1.1 is
  reviewed (**met 2026-10-27**, `lane/r52`); its harness waits for **plan 0052's P3a** (machinery and tier) to be
  reviewed; 0052's catalogue (P3b), the path search plan ([0054](0054-path-search.md)) and plan 0046 never gate it:
  an AI, path or skill function they have not specified is a boundary oracle (ADR-0004, as ADR-0020). If 0052's P2 or
  P3a moves the AI tick or a unit list this plan's P1 relied on, the architect re-rules at this plan's P1 review
  (ADR-0022 § Negative).
- **What is known:**
  - [ai/0001 § 1](../findings/ai/0001-machinery.md#1-the-tick-its-caller-and-the-order) (`[I]`):
    `ServerGamesFrame` runs one frame per interval over 1 024 game slots and calls `GameTick` for each live game
    (`GameTickAlt` is its other caller); `GameTick` increments `Game+0xA8`, runs two act passes, `NewRoomsUpdate`,
    `GameRunUnitEvents`, the client room sync and the timers; `GameRunUnitEvents` runs missiles, players, monsters,
    objects, items, each type's every-frame list and then its slot list (records due this frame, oldest first, freed
    after their run); `MonEventDispatch` drops most kinds while a unit is frozen. § 11 lists the unit lists (the hash
    lists, the room lists, the event lists, the target lists, the clients).
  - [drlg/lifecycle § A](../specs/drlg/lifecycle.md#a-the-frame): the frame at `[I]` with "two per-frame passes" and
    "two more passes" unnamed; the release pass every 12 frames `[C]` (run:2026-10-17-lifecycle); the quest timers
    every 20 (`QUESTS_TimersRun`, `[C]`), the level-unload tick every 11, the item expiry sweep every 1 500.
  - [anim/timing](../specs/anim/timing.md) (reviewed, plan 0050): the event queue's entry points
    (`EventQueueAt`, `EventQueueEveryFrame`, `MonEventsRun`, `SUNIT_ScheduleModeEvents` `[C]`) and the mode events
    they carry; the frame's own model is not there.
  - [skills/dispatch § P1](../specs/skills/dispatch.md#p-draws-and-seeds-per-event-kind): the resynchronised entries
    this phase exists to re-chain: at a skill start or do, the caster's seed equals its previous exit in 3 155 of 3 459
    consecutive pairs (plan 0045's first run); 135 of 281 player gaps walked draw by draw; 331 monster gaps left to the
    AI (plan 0052's H1).
  - [chain](../specs/chain/README.md)'s last `[L]`: a log-free world build "would need the activation order as an input
    record".
  - Client messages: `SrvClientMsgDispatch` and `SrvPacketDispatch` are named (items/economy, items/cube); where in the
    frame they run is not.
- **Research map row:** `sim/frame` (Simulation band), added with this draft (ADR-0022). Wiki owner: Phase 4.

## Phases

Data first, then code, then spec.

### Phase 0 — The kept-log corpus
- **Owner skill:** archivist (no Ghidra, no slot)
- **What:** an index of the kept logs of plans 0037–0052 (the runs their findings name, by `run:` id) that says, per
  log, whether its events carry a frame number and a unit id, which event kinds it holds and how many, and which seeds
  it records at entry and exit; a reader that turns every frame-stamped log into one event stream per session
  (frame, unit type and id, event kind, entry and exit seed).
- **Outputs:** `tools/frame_corpus.py` (gate survey `frame`) and a block in `docs/inventory.md` for the corpus (no game
  data in git: the logs stay under `workspace/`).
- **Done when:** every kept log of the listed runs is classified, the reader parses every frame-stamped one with counts
  matching the run records, and the gate is green.

### Phase 1 — The frame, in three static batches
- **Owner skill:** reverser (static; one Ghidra per batch, batches one at a time per lane, two lanes at most)
- **What and done when:** each batch names its functions with addresses at `[I]` or better, lists the draws of each pass
  per seed (an RNG call graph from the pass with the unit-event functions and the specified phases' entries as stops),
  and emulates (ADR-0015, ADR-0021) the pure list and queue operations it can declare an image for.
  - **P1.1 the tick and the messages.** `ServerGamesFrame` (the interval, the slot order, `GameTickAlt`'s role),
    `GameTick`'s passes each named (the two act passes, the two after the room sync, `ActUnitsFrameReset`), where
    client messages are drained relative to `GameTick` and in which order within a drain, and whether two games share
    any state a frame touches; **the frame-window log design** for Phase 2b (which events, which lines, the volume per
    frame in a small scene) and the window and scene proposal.
  - **P1.2 the unit events and the queue.** `GameRunUnitEvents` in full: the per-type event lists (`Game+0xB8`,
    `g_UnitTypeEventList`) and the event function table of each unit type (the monsters' `g_MonEventFuncs` and the
    others'), the every-frame and slot lists, the insertion order of `EventQueueAt` and `EventQueueEveryFrame`, what
    happens to an event queued during a pass for the current frame, a unit freed or moved during a pass, and the
    freeze drop; the inactive units' events (drlg/lifecycle's save and restore).
  - **P1.3 the timers and the activation order.** `QUESTS_TimersRun` (every 20), `RoomsDeactivate` (every 12), the
    level-unload tick (every 11), the every-frame call `0x0052D310` and its 1 500-frame sweep, the 7 500-frame test;
    `ClientsRoomSync` and `NewRoomsUpdate`: the order in which a frame's newly active rooms are populated, and the
    order of an act's rooms (`ActRoomsHead`) that the passes walk; **the activation-order record** the chain spec asks
    for (what a log-free build would take as input, or why it cannot be derived).
    Added at the P1.2 review: player kind 11's two callees (`0x005406A0`, `0x00575630`) and kind 6's `Unit+0xA4` record
    read for their draws (frame/0002 open question 2), and the window volume re-estimated with the queue line
    (frame/0002 § 8) beside P1.3's own `RU0`/`RU1` and `TM` lines.
- **The P1 review** (one review after P1.3, or one per batch as the lanes land) rules the frame model's draw table (the
  shared-seed points: the game seed's draws in a frame, a seed hit by two units' events), the window design and Phase 2's
  floors, and re-rules ADR-0022's early gate if plan 0052 has moved anything P1 used.

### Phase 2a — The order model on the kept logs (no game)
- **Owner skill:** reverser (no slot, no Ghidra; replays under the memory limit)
- **Starts when:** P1 is reviewed. It is a replay of kept logs, not a harness run, so ADR-0022's harness gate does not
  apply (§ Scoping questions 3).
- **What:** `tools/frame.py` (the order model and `check`) over Phase 0's corpus: for every frame with two or more
  logged events, the predicted order of the logged events against the logged order; for every pair of events on one
  seed in one frame, the seed handed from the first to the second.
- **Done when:** 0 mismatches over every frame-stamped frame of the corpus with two or more events; the record counts
  how many of the resynchronised entries of plans 0045 and 0052 (the 3 459 pairs, the 281 player and 331 monster gaps)
  the order model re-chains, and names why each remaining one does not (its log holds no line for the event between).

### Phase 2b — Frame windows
- **Owner skill:** reverser (harness; **one slot** from 1–2, given in the prompt)
- **Starts when:** plan 0052's P3a is reviewed (ADR-0022, ADR-0016), and P1 is reviewed.
- **What:** `tools/gdb/frame.gdb` and its handler. A **window** is a stated run of consecutive frames in a small scene
  (one player, a bounded set of units): every in-scope event of every unit is logged with its entry and exit seed,
  every entry seed is asserted against the model's chain, none resynchronised; each client message is a logged input
  with the frame it is applied in. An unspecified catalogue, AI or path function ends the chain at its call (a boundary
  oracle); scenes are chosen to avoid them, and the claim is limited to the scenes run. Outside windows, ADR-0014's log
  volume rules apply.
- **The pilot** (ruled at the P1.1 review, 2026-10-30): the first session's first window, in the Act I town. It passes
  when (a) it is **whole**: an `FT0` and an `FT1` for each of 250 consecutive frame numbers, no gap or repeat, every
  opened line pair closed in its frame, 0 lines the reader cannot parse; (b) it is **unmoved**: every entry seed chains,
  every mismatch is traced, and none is traced to the logger (a breakpoint that changes a value or an order); (c) it is
  **carried**: the window completes inside one harness session (the rotation bound) with no crash, hang, lost input or
  watchdog stop. The record states wall seconds per window, frames per wall second, gdb's hit count per breakpoint and
  the lines per frame against frame/0001 § 7. A failure of (a), (b) or (c), or a measured session above ten times plan
  0045's 17 786 lines (177 860), is Q2's trigger: the architect drafts the injected-logger ADR. Slow but passing is a
  pass; the architect re-plans the session count from the measured rate. The town pilot runs at about plan 0045's
  highest carried rate (12.45 lines per frame), the pack and maze estimates at 2.5–2.9 times it, so **the first window
  of each other scene is a pilot** by the same three tests; a failure there is Q2's trigger for that scene, and the
  passed scenes' windows still count. A scene whose measured lines per frame exceed three times its estimate stops
  after that window for the architect to re-rule its floors.
- **Done when** (confirmed at the P1.1 review, 2026-10-30): `run:YYYY-MM-DD-frame` reproduces with **0 mismatches** over at
  least **10 windows of at least 250 consecutive frames** each, in at least **three scenes** with **at least two windows
  each** (the Act I town; Blood Moor or Cold Plains with a pack; Den of Evil with Corpsefire), at least **5 000 chained
  events** in all (frame/0001 § 7 estimates 12 800–42 300 for ten windows; the floor stays until the pilot measures),
  each window chained from its first frame to its last, a passing pilot counting as a town window; every session in
  single player (one game in the process) from a fresh process, `g_HitClassCounter` logged at each `FT0`; the pack's and
  Corpsefire's monster kinds in plan 0052 P3a's reviewed tier (else the lane names a substitute scene in its prompt
  request and the architect rules), the player using only specified skill functions; at least one window holds each timer's period (a frame `mod 20`, `mod 12`,
  `mod 11`) and one a room activation; at least 20 shared-seed pairs (two units' events on the game seed in one frame)
  in the right order. The record states the lines per window against P1.1's estimate.
  A window that cannot be logged whole falls back to resynchronised events and is named, not counted.

### Phase 3 — Spec: the server frame
- **Owner skill:** spec-writer
- **What:** `docs/specs/sim/frame.md` (the tick, the passes, the unit-event order, the queue, the timers, the activation
  order, the message drain, the draw table per pass) with the frame as pseudocode; drlg/lifecycle § A reduced to a link
  and its room parts; the chain spec's activation-order `[L]` answered or restated; skills/dispatch § P1 and
  monsters/ai (if P3a has landed) updated with the re-chained counts.
- **Done when:** the spec follows the template; every statement tagged; the frame and the queue as pseudocode with the
  draw order per pass; the architect's review passes. Specs edited by two plans merge one at a time, the earlier
  plan's first.

### Phase 4 — Wiki page: the server frame
- **Owner skill:** spec-writer
- **What:** `docs/wiki/server-frame.md` (ADR-0012) over the reviewed spec; the levels, combat, skills and monster AI
  pages linked.
- **Done when:** `based_on` dates current (gate W4); no claim of its own; the architect's review passes.

## Scoping questions for the owner

The owner answers these with the approval. Each carries the architect's recommendation; the phases above are drafted on
the recommendations, and an answer that differs changes the phase it names.

1. **Windows and scenes.** *Recommendation:* at least 10 windows of at least 250 frames (about 10 s each), three scenes
   (town, an outdoor level with a pack, a maze level with a boss), 5 000 chained events, as Phase 2b states; the numbers
   are confirmed or changed at the P1 review once P1.1 has estimated the lines per frame.
2. **The injected logger.** *Recommendation: not now.* Phase 2b tries gdb first, with its first session a pilot window.
   The architect drafts the logger ADR for the owner (one ADR for this plan and plan 0052, as 0052 question 3 proposed)
   only if the pilot cannot log a window whole, the breakpoints move the frames that follow (a mismatch traced to the
   logger), or P1.1's estimate is more than ten times plan 0045's per-session lines.
3. **Phase 2a before 0052·P3a.** *Recommendation: yes.* ADR-0022 gates this plan's harness; a replay of kept logs uses no
   slot and no game, so it may run once P1 is reviewed. It gives the order model its first test set well before the
   windows. Confirm the reading.
4. **Client messages.** *Recommendation:* the point in the frame where messages are applied, and their order within a
   drain, are in (static and in the windows); the frame a message arrives in is a logged input, and no claim is made
   about arrival (ADR-0014 § Time, ADR-0022).
5. **More than one game.** *Recommendation: one game.* `ServerGamesFrame`'s slot loop and interval are read statically;
   P1.1 checks that two games share no state a frame touches, and the order across games is out of scope.
6. **The companion sweep** (ADR-0022's first alternative: an inferred-claims sweep over the simulation and game-rules
   specs, 1 087 `[I]` over eight rows on 2026-10-27). *Recommendation:* the architect drafts it as its own plan after
   this plan's Phase 2a lands, so its draw-order targets can use the order model; it takes the harness slots plan 0038
   leaves once its batches drain. No ADR is needed. The owner decides now whether to queue it.
7. **Run order across 0052, 0054 and this plan.** *Recommendation:* static lane A keeps 0052's catalogue (tier batches
   first, since they gate 0052·P2); static lane B takes this plan's P1.1–P1.3, then plan 0054's P1 batches, then 0052's
   remaining batches beside lane A; the archivist takes this plan's P0, then 0054's P0; harness lane H2 keeps 0052·P2
   when it opens, plan 0054's P2 takes a free slot, and Phase 2b follows 0052·P3a. The architect writes the run order
   into the plans README on the owner's answer.
8. **Wiki.** *Recommendation:* its own short page (Phase 4), since the frame is the loop the other pages' parts run in.

## Resources and limits

- **Static:** at most **two static lanes** and **two headless Ghidra** at once across all plans, `-Xmx3G` each. P1
  holds one Ghidra per batch; P0 and P2a need none.
- **Harness:** at most **two harness lanes** at once, on **slots 1 and 2** (slot 0 is the owner's); Phase 2b takes one,
  and no two-client case is required (party branches stay `[I]` from the code).
- **Replays:** Phase 2a and any heavy replay under `systemd-run --user --scope -p MemoryMax=4G`; the corpus is read one
  session at a time.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (not measured): P0 one lane run; P1 three; P2a one; P2b two to three lane runs of 6–12 sessions; P3 one;
  P4 one.

## Open questions

- **Frames the kept logs cannot place.** Logs that carry no frame number (P0 finds which) cannot test the order model;
  Phase 2a's claim is limited to the stamped ones.
- **Non-determinism under wine.** If two windows of one scene from one save diverge with every logged input equal, the
  divergence is a message-arrival effect (ADR-0022 § Negative) or a missed input; the record says which.
- **The per-unit order within a list.** Whether a list's order is insertion order or a hash order (the unit hash lists
  key on `guid & 0x7F`) decides how much of a window a reimplementer must reproduce from creation; P1.2 answers it.
  *Answered at P1.2 (reviewed 2026-10-30):* queue order, not a hash order (frame/0002 § 2).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans54`).** Status `draft`; the plan ADR-0022 calls for, drafted on unpause;
  its static gate (0052·P1.1 reviewed) is met; eight scoping questions for the owner.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr`).** "Approve as recommended": all eight
  scoping questions answered as recommended. Q1 the window and scene floor as Phase 2b states (confirmed or changed at
  the P1 review); Q2 no injected logger now (gdb first, pilot window); **Q3 Phase 2a may run before 0052·P3a** (once P1
  is reviewed; reading confirmed); Q4 the message drain point and order in, arrival out; Q5 one game; **Q6 the
  companion `[I]` sweep is queued** as its own plan, drafted by the architect after this plan's Phase 2a lands; Q7 run
  order as recommended; Q8 its own wiki page. Run order
  ([plans README](README.md#run-order-set-2026-10-25-plans-00380052)): **P0 ready to start now** (the archivist is
  free); P1 in static lane B when a static lane frees (both busy on 2026-10-30: `lane/r52b`, `lane/h6gs`); P2a after
  P1's review; P2b after 0052·P3a's review. Status `approved`.
- **2026-10-30 — Phase 0 landed (archivist, `lane/a55`; review requested).** `tools/frame_corpus.py` (`index`, `summary`,
  `read`, `check`), gate survey `frame` (opt-in, 81 s) with its baseline, and the *Kept-log corpus* block of
  [`docs/inventory.md`](../inventory.md). Result (`[C]`, by script): of 1 657 `*.log` files under `workspace/logs/`, 1 597
  are harness logs; the 79 runs plans 0037-0052 name (77 with a run section) attribute **1 574** of them to 72 runs, by name,
  glob or the `.lst` and manifest files the sections name; **331 are frame-stamped** (6 805 992 lines, 9 of the 72 loggers:
  `anim`, `stats`, `skills`, `combat`, `economy`, `economy2`, `economy-hire`, `two-combat`, `h6b`), **1 243 are not** and cannot
  test the order model (open question 1 answered). Unit ids: `anim`, `skills`, `combat` and `two-combat` carry `{u,t,id}`
  on part of their kinds; `stats`, `economy*` and `h6b` stamp frames but carry **no unit id**, so for them the model can
  check order by frame and seed chain only; `h6b` (`RPE`, `RPS`) also holds no seed. Entry and exit seeds exist as `TAG0`
  and `TAG1`/`TAGX` pairs in 327 of the 337 stamped logs (the reader folds a pair into one event at the begin's frame).
  The reader consumes every stamped line of all 337 stamped logs (the 331 in the corpus plus those outside it) (6 469 457 events, 0 unparsed, 0 left over) and its
  per-kind counts equal two run records exactly (combat 0037 P2: 15 358 events over 19 logs; skills 2026-10-27: `MAS.seed`
  13 905, `CU.code` 1 340, `MC.owner` 19 667, the last with one begin that has no end line excluded). **Gaps:** (1) the
  anim, stats and economy run records state tallies that do not map to a line kind one to one, so their counts are
  not compared to the reader; (2) attribution by manifest is wide (a sweep manifest names 1 295 logs; a log can belong to
  several runs, listed in the index); (3) 5 harness logs are named by a run's directory only (development logs) and 18 by
  no run (plan 0046's 2026-10-30 catalogue logs among them), so they are indexed but not counted; (4) five runs name no
  harness log (four emulated runs and `sweep-emu2`), two named runs (`d2s-samples`, `cube-saves`) have no section.
- **2026-10-30 — P1.1 the tick and the messages (reverser, static, `lane/r55`; review requested).**
  [frame/0001](../findings/frame/0001-tick-and-messages.md), [frame/experiments](../findings/frame/experiments.md)
  (run:2026-10-30-frame-emu), 48 new `re/symbols.csv` rows (39 functions, 9 data; all `I`, subsystem `sim/frame`), new
  tools `tools/frame_emu.py`, `tools/frame_globals.py`, `tools/frame_volume.py`; static outputs under
  `workspace/logs/r55/static/` (manifest `07094f49…`, 19 lines), emulation under `workspace/logs/r55/emu/` (manifest
  `60d57be2…`, 10 lines). Totals taken after merging `main` `ae673b64` (the branch then merged `main` `e4fa8a2e`, gate green; P1.1 review). Found: `ServerGamesFrame` ticks every live game
  once per 40 ms (`1000 / 25`), slot order, at most one interval of debt; `GameTickAlt` is unreached (its only caller is
  an unreferenced stub). `GameTick`'s seven passes are named: the "two act passes" are the act light clock
  (`ActsClockPass`) and a frames-per-second counter, the "two more" the updated-unit reset (`ActUnitsFrameReset`, which
  walks only the units marked this frame, newest first per room) and the room-removal clear. None of the four draws of
  its own; their routes to a draw are `EquipReqRefresh` (on an act clock change) and `UnitFree` (an inventory item at
  the reset). Client messages are drained before the frame from three FIFO queues (system, in-game packets of every
  client in arrival order, host), never inside `GameTick`. Two games share no seed; the one behavioural coupling is the
  process-wide `g_HitClassCounter`. The empty-game close (`1500 < frame < 7500`, the "7 500-frame test") is in the
  post-frame flush, not `GameTick` (P1.3 may cite it from here). Three emulated maps `[C]` (840 cases, 0 mismatches).
  **The lines-per-frame estimate for the P1 review:** 12.5–36.3 lines per frame (town, outdoor pack, maze boss), 3 100–
  9 100 per 250-frame window, 31 000–91 000 for ten windows, against plan 0045's measured 4.09 lines per frame and
  17 786 per session: 0055 Q2's ten-times trigger is not met on volume (a whole Phase 2b run is 1.8–5.1 plan-0045
  sessions); the rate per frame (310–910 breakpoint stops per game second) is what the pilot window must show gdb can
  carry. Window design and scene proposal in frame/0001 § 7. Corrections for other findings: drlg/0009 § 1 (dated note
  added); ai/0001 §§ 1 and 11 (the unnamed passes; `Room+0x1C` is the updated-unit list, not all units) left to its
  owner lane (`lane/r52b` active) or Phase 3.
- **2026-10-30 — P1.1 reviewed (architect, Tier A, `lane/r55`): accept with fixes (5).** Anchors spot-checked on the
  pinned image with objdump: `GameTick`'s eleven call sites 0x0052D8DF–0x0052D96C and its three signed `idiv`s,
  `ServerGamesFrame`'s slot range `0x00882D38`–`0x00883D38` and its one `GameTick` call 0x0052FD19, the drain's queue
  order (0x0052CFFF, 0x0052D02C, 0x0052D05C), the four drain and three frame call sites, the mark's front push
  (0x0064C0AD–0x0064C0B5), `HitClassPick`'s byte counter (0x0057CE30, 0x0057CE4F), the stub 0x00564C70 with no reference
  (raw dword scan: 0); both manifests pass `sha256sum -c` (19 and 10 lines), `check.txt` as filed. Fixes, written into the
  lane's files: **omission 2**: the updated list's unlink (`0x0064C370`, 30 call sites, unlinks at 0x0064C42D and clears
  bit `0x2000`), so the list holds the units marked this frame *and still in the room* (frame/0001 summary, § 3.3, open
  question 6); the breakpoint stops beyond the logged lines (at least 9 a frame from the conditional sites; § 7).
  **overclaim 1**: `g_HitClassCounter` "changes behaviour across games" scoped to what is read: a byte, 0 at load, one
  store, never reset; it decides the element nibble only for a hit with two or more element fields above 0, and the
  one server reader found is indifferent to it (summary, § 6). **wrong anchor 1**: `lifecycle.h`'s clock counter
  comment left out the flag-0 condition of the act steps. **miscount 1** (reverser rule 3, the `main` named): the P1.1 entry named only the
  first `main` merged (`ae673b64`), not `e4fa8a2e`. Rulings: **(1) Q2, the logger:** the volume trigger is not met (a
  three-window session estimates 0.5–1.5 plan-0045 sessions); the rate is not a Q2 trigger by itself, but the pilot's
  pass and fail tests are now Phase 2b's *The pilot* (whole, unmoved, carried; the first window of each scene a pilot),
  and a measured session over 177 860 lines replaces the estimate in Q2's volume test. **(2) Q1, windows and scenes:**
  confirmed as Phase 2b now states (10 × 250 frames, three scenes with two windows each, 5 000 chained events, timers,
  one room activation, 20 shared-seed pairs); the scenes are the lane's (Act I town pilot, Blood Moor or Cold Plains,
  Den of Evil with Corpsefire), held to 0052 P3a's tier. **(3) ai/0001 §§ 1 and 11:** not edited here (`lane/r52c` is
  active in `docs/findings/ai/`); routed to the reverser as
  [backlog entry](../backlog/2026-10-30-architect-reverser-ai-0001-frame-corrections.md) (also the 0x0052D8F2 call site
  and `GameTickAlt` unreached); Phase 3 cites frame/0001, not ai/0001 § 1, for the passes. **(4) One game and
  `g_HitClassCounter`:** Q5's one-game scope stands; the counter is a process-wide input of the frame model, not a
  reason to widen it: the spec states it as process state (0 at load, carried across games), every window session
  starts from a fresh single-player process and logs the counter at `FT0`. **P1.2: go** (static lane B, when a headless
  Ghidra frees; both in use on 2026-10-30). Its additions from this review: name `0x0064C370` and say which of its
  callers run in a frame. ADR-0022's early gate needs no re-ruling: 0052's P2 and P3a have not landed, so nothing P1.1 used has moved.
- **2026-10-30 — P1.2 the unit events and the queue (reverser, static, `lane/r55b`; review requested).**
  [frame/0002](../findings/frame/0002-unit-events-queue.md), [frame/experiments](../findings/frame/experiments.md)
  (run:2026-10-30-frame-emu-2), 29 new `re/symbols.csv` rows (all functions, all `I`, subsystem `sim/frame`), new
  tools `tools/frame_queue_emu.py`, `tools/frame_events.py`, `re/ghidra_scripts/CallersUp.java` (`tools/ghidra.sh
  callersup`); `re/types/anim.h` (`UnitEvent` flags, `EventCtl`, `EventBlock`); static outputs under
  `workspace/logs/r55b/static/` (manifest `99488028…`, 52 lines), emulation under `workspace/logs/r55b/emu/`
  (manifest `b1b00fea…`, 19 lines), development runs under `workspace/logs/r55b/dev/` (three manifests, each passing
  from `dev/`). Totals taken after merging `main` `49a5dec7` (gate green). Found: `GameRunUnitEvents` makes ten
  walks, missiles, players, monsters, objects, items, each every-frame list (newest first: a front push) and then
  its current slot (oldest queued first: a tail append; only records due this frame run, each freed after its run);
  list order is queue order, not a hash order (open question 3 answered). A timed record queued in a pass never runs
  in that frame (frame raised to current + 1); an every-frame one runs in it only if its list is walked later. A
  freed record is never run after it (the walker's saved next is moved on); a record freed while running is freed
  after its run; a freed unit loses every record at once; a room change touches no record. Frame −1 drops the
  callback. The four event tables are listed per kind; the freeze drop keeps kinds 3, 4, 5, 8, 12. The pass and the
  queue draw nothing of their own, except `EventQueueAt`'s state-54 branch for a monster's AI event
  (`UninterruptibleEnd`, kill or hit under state 92). Inactive units keep no record but a shrine's earliest kind-5
  frame. `0x0064C370` is `UnitRoomUnlink`: 16 server callers reach a `GameTick` pass by Ghidra's references, 2 from the
  AI table, 1 through an unfollowed quest callback, 6 client-only, 4 unreferenced sites (frame/0001 open question 6
  answered there by a dated note). Six emulated families `[C]` (1 400 cases, 0 mismatches, byte for byte over the
  control, both blocks and the units; six negative controls, `cancel`'s separating only 3 cases). The window's `UE0`/
  `UE1` sites (20, four per runner) and the queue line the § 7 estimate did not count: frame/0002 § 8.
- **2026-10-30 — P1.2 review (architect, Tier A: rulings asked; `lane/r55b`).** **Accept with fixes (9)**, written
  into the lane's files. Anchors spot-checked against the pinned image by objdump: the ten head loads and calls of
  `GameRunUnitEvents` (0x005414EE–0x00541589, each head read after the previous walk returns), `EventQueueAt`'s signed
  bound, frame −1 push of callback 0 (0x005416D5) and raise (0x005416E9), `EventQueueEveryFrame`'s front push
  (0x00541633–0x00541646), the cancel loops (0x00540E60–0x00540F50), the player runner's four call sites (§ 8), the
  freeze byte map of `MonEventDispatch` (0x005A7FE8: kinds 3, 4, 5, 8, 12 direct), `UnitRoomUnlink`'s tail
  (0x0064C42D, 0x0064C432), the 30 direct calls (a full objdump count), the two `g_MonAiTable` think pointers (rows 131
  and 138, 16-byte rows), the shrine save and restore (0x00542FE4–0x00543005, 0x00542C5A–0x00542C87); kept manifests
  (static `99488028…` 52 lines, emu `b1b00fea…` 19 lines, the three dev manifests) pass, tool hashes match, the 29
  symbol rows clash with none, gate green. Fixes: **under-claim 1**: the cross-type every-frame case was already
  logged: anim/0001's `ef-first` check (run:2026-10-27-anim) has 658 monster starts queued during the missile or player
  walks that ran in that frame, so frame/0002's every-frame half for players and monsters is `[C]`, raised in part
  (objects, items, missiles stay `[I]`); the Dead ends bullet corrected. **overclaim 2**: "the next record of the chain is
  read before each free" sat inside the `cancel` `[C]` though no case can separate it (`EventFree` leaves `+0x24`), now
  its own `[I]`; kind 12 "the timed stat-list expiry of every type" scoped to players, monsters and items (the object
  table's entries 12–14 are null, fatal in its dispatch). **omission 3**: `cancel`'s thin control: the review scored
  three more wrong readings against the kept `cancel.out` (`tools/frame_queue_controls.py`, new; `a` compared at 0
  separates 10, callback 0 as "any" 3, chain oldest first 5, each failing every case it separates; experiments
  addendum); the dispatches' kind bounds (players and monsters unsigned, objects and items none, so a negative kind
  `EventQueueAt` accepts is dropped at dispatch); the shrine restore's `+0x14 ≠ 0` test (0x00542C5A). **stale
  cross-reference 3**: frame/0001 § 3.3's "is P1.2's" and its § 7 `UE` row now point at frame/0002 §§ 7–8;
  skills/0003's "a fifth list" given a dated note (items); this plan's open question 3 marked answered, and the
  research-map row and plans index brought to "P1.1 and P1.2 reviewed, P1.3 next" (left stale since the P1.1 review).
  Rulings: **(1) the cross-type case**: `[I]` is acceptable where no log holds it (objects, items, missiles); for
  monsters it is `[C]` already (above). Phase 2b's record counts the cross-type every-frame runs it logs (a record
  queued by an earlier type's walk run in the same frame) per receiving type, which is the route to raise the
  objects' and items' half. **(2) the window volume** is re-estimated at **P1.3**, not at the pilot: P1.3 closes the log
  design (`RU0`/`RU1`, `TM`) and re-runs `tools/frame_volume.py estimate` with the queue line (`UnitQueueEvent` and
  `EventQueueEveryFrame` entries, one per queued event) and a stated queue rate per run event, so that the pilot's
  "three times its estimate" stop and Q2's volume test compare a measurement with an estimate of every line logged.
  **(3) the open questions**: none gates P1.3 or Phase 2a (2a orders logged events; the queue order holds whatever a
  handler does or which block a record uses). frame/0002's question 2 (player kind 11's `0x005406A0` and
  `0x00575630`, every 30 frames for every player, and kind 6's `Unit+0xA4` record) is **added to P1.3's scope**: read for
  draws by direct reach before the pilot, or ruled boundary oracles at the P1 review; questions 1 and 4 bear on the
  choice of Phase 2b scenes only; 3 is logged by `UE0`; 5 and 6 are bounds. **The thin `cancel` control** is sufficient
  with the added readings: every half of the map has a separating case that a wrong reading fails, and the claim is
  byte for byte, so no reading matches by chance; the lane's next emulation family states the separating count per
  half, not per family. **P1.3: go** (static lane B; one Ghidra), with question 2 above and the re-estimate added to its
  done-when. ADR-0022's early gate: plan 0052 has landed only P1.2 batch 3 since P1.1 (`49a5dec7`), which P1.2 does not
  use; no re-ruling.
