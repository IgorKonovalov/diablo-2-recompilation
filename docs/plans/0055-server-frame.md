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
  reviewed; 0052's catalogue (P3b), the path search plan ([0054](done/0054-path-search.md)) and plan 0046 never gate it:
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
  the lines per frame against frame/0003 § 9's estimate (`estimate13`, mid queue rates), and the measured queue rate
  (`QE`+`QF` per `UE0`) against its stated inputs (P1 review). A failure of (a), (b) or (c), or a measured session above ten times plan
  0045's 17 786 lines (177 860), is Q2's trigger: the architect drafts the injected-logger ADR. Slow but passing is a
  pass; the architect re-plans the session count from the measured rate. The town pilot is estimated at 15.9 lines
  and 32.9 breakpoint stops per frame (1.3 times plan 0045's highest carried rate, 12.45 lines per frame), the pack and
  maze at 41.3 and 50.9 lines (3.3 and 4.1 times it; 58.3 and 67.9 stops), so **the first window
  of each other scene is a pilot** by the same three tests; a failure there is Q2's trigger for that scene, and the
  passed scenes' windows still count. A scene whose measured lines per frame exceed three times its estimate (town
  47.6, pack 123.9, maze 152.7) stops after that window for the architect to re-rule its floors.
- **Done when** (confirmed at the P1.1 review, 2026-10-30): `run:YYYY-MM-DD-frame` reproduces with **0 mismatches** over at
  least **10 windows of at least 250 consecutive frames** each, in at least **three scenes** with **at least two windows
  each** (the Act I town; Blood Moor or Cold Plains with a pack; Den of Evil with Corpsefire), at least **5 000 chained
  events** in all (frame/0001 § 7 estimates 12 800–42 300 for ten windows; the floor stays until the pilot measures),
  each window chained from its first frame to its last, a passing pilot counting as a town window; every session in
  single player (one game in the process) from a fresh process, `g_HitClassCounter` logged at each `FT0`; the pack's and
  Corpsefire's monster kinds in plan 0052 P3a's reviewed tier (else the lane names a substitute scene in its prompt
  request and the architect rules; **ruled at the `lane/s52a` review, 2026-11-04:** in Blood Moor and Cold Plains only `fallen1` (row 6) and `fallenshaman1` (row 13, with its Fallen) are in the tier, so the pack is a Fallen or shaman pack, and Fallen past their first call are a consistency check, `[I]`. Corpsefire is `zombie1`, AI row 3, **not in the tier**, and so are Den of Evil's `zombie1` and `brute1` beside its tier `fallenshaman1`. The scene stands without a substitute, as an exception named here: row 3's map is `[C]` (ai/0002 § 2.2), its first boundary holds over 216 decisions with 129 drawing pairs (run:2026-11-03-ai), and under ADR-0022 a think the reviewed tier does not hold is a boundary oracle: its entry and exit seeds logged and taken as given, the window counted for the order of events and not as evidence of the think. Brute, `quillrat1`, `corruptrogue1` and `cr_lancer1` beside a pack are the same. Row 7's chain is short, so a window with brutes names them), the player using only specified skill functions; at least one window holds each timer's period (a frame `mod 20`, `mod 12`,
  `mod 11`) and one a room activation; at least 20 shared-seed pairs (two units' events on the game seed in one frame)
  in the right order. The record states the lines per window against P1.1's estimate.
  A window that cannot be logged whole falls back to resynchronised events and is named, not counted.
  *Added at the P1 review (2026-10-30):* the lines are frame/0003 § 9's closed design (`TM`, `TQ`, `RU0`/`RU1`, `RC`,
  `RR`, `QE`/`QF`, with P1.1's and P1.2's), and the record states lines per window against `estimate13`; at least one
  window holds a frame `≡ 0 (mod 1 500)` (the expiry sweep); a window that holds a frame `≡ 0 (mod 8 192)` logs
  `SaveGameClients` there as a boundary oracle (frame/0003 § 3: the save's seed is not read); the record counts the
  kind-11 and kind-6 runs whose entry and exit seeds are equal on every seed logged (their draw-free reading, § 6–7),
  and names any activation made during a `NewRoomsUpdate` walk (frame/0003 open question 2).
  *Ruled at the `lane/p55b` review (2026-11-04):* **a unit's seed stepped in another unit's event is a result of the window, not a logger failure, and is not Q2's trigger.** Q2's answer is the owner's: a window that cannot be logged whole, breakpoints that move the frames that follow (a mismatch traced to the logger), or the volume. "A failure of (a), (b) or (c)" above is read inside that answer: (b) fails on a mismatch that stays untraced or is traced to the logger. The chain "the model's chain" asserts is the rule in this plan's log entry of that date: every step of a chained seed is logged by site and applied by the LCG, and a step on a unit's seed outside its own event must be at a site and under a trigger named before the log exists. The Done-when's "0 mismatches" holds under that rule.

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
   leaves once its batches drain. No ADR is needed. The owner decides now whether to queue it. *(Owner, 2026-10-30, later: **owner 2026-10-30: may be drafted, as `draft` only, never started** (no plan after the approved roster is approved or started).)*
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
  [backlog entry](../backlog/archive/2026-10-30-architect-reverser-ai-0001-frame-corrections.md) (also the 0x0052D8F2 call site
  and `GameTickAlt` unreached); Phase 3 cites frame/0001, not ai/0001 § 1, for the passes. **(4) One game and
  `g_HitClassCounter`:** Q5's one-game scope stands; the counter is a process-wide input of the frame model, not a
  reason to widen it: the spec states it as process state (0 at load, carried across games), every window session
  starts from a fresh single-player process and logs the counter at `FT0`. **P1.2: go** (static lane B, when a headless
  Ghidra frees; both in use on 2026-10-30). Its additions from this review: name `0x0064C370` and say which of its
  callers run in a frame. ADR-0022's early gate needs no re-ruling: 0052's P2 and P3a have not landed, so nothing P1.1 used has moved.
- **2026-10-30 — Companion sweep drafted only (owner; recorded by the architect, `lane/appr2`).** "You can draft plans but do not start them": the Q6 companion `[I]` sweep may still be drafted after this plan's Phase 2a lands, as `draft` only, and is not approved or started; this plan runs to completion as approved.
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
- **2026-10-30 — P1.3 the timers and the activation order (reverser, static, `lane/r55c`; review requested, closes
  Phase 1).** [frame/0003](../findings/frame/0003-timers-activation.md), [frame/experiments](../findings/frame/experiments.md)
  (run:2026-10-30-frame-emu-3), 20 new `re/symbols.csv` rows (all functions, all `I`, subsystem `sim/frame`), new tool
  `tools/frame_timers.py` (`adds`, `cbscan`, the five families' cases, check and manifest), `tools/frame_volume.py
  estimate13` (its `estimate` unchanged); static outputs under `workspace/logs/r55c/static/` (manifest `abfc7c4d…`, 80
  lines), emulation under `workspace/logs/r55c/emu/` (manifest `269cde48…`, 21 lines), development runs under
  `workspace/logs/r55c/dev/` (five manifests, each passing from `dev/`). Totals taken after merging `main` `11102c87`
  (gate green). Found: the four periodic calls draw nothing of their own; the quest timers run **newest registered
  first** (a front push), 26 registrations of 21 callbacks, 6 of which draw through quest content (spawns, the
  Tristram portal's level point, the Dark Wanderer's quest-seed step); the unload test can **build** a vis level
  (`DRLG_LevelCreate`, on that level's seed); the 1 500-frame sweep frees items `expiry ≤ frame` before records
  `expiry < frame`, act by act. An act's room list is **newest first** (`DUNGEON_RoomCreate`'s head push, one caller),
  so a frame's new rooms are populated in reverse creation order, acts 0..4, the next frame; a room created during
  the walk itself waits for its act's next walk (a reading; open question 2). `ClientsRoomSync` draws on per-room and
  per-level seeds only, by direct reach. The activation-order record (frame/0003 § 5): per frame each client's new
  room at pass 5, every on-demand activation and the pins; derivable from those with the near lists, but the room of
  each player needs movement, so without a movement model it is a logged input (the chain spec's `[L]` answered with
  that limit). Added scope: player kind 11 and kind 6 are **draw-free** by direct reach (kind 6's `Unit+0xA4` is the
  overhead chat record), so both are modelled events, not boundary oracles. Five emulated maps `[C]` (1 300 cases, 0
  mismatches, every boundary asserted with its call site; separating counts per half in frame/0003 § 8). The window log
  design is closed (`TM`, `TQ`, `RU0`/`RU1`, `RC`, `RR`, and the queue line moved to `EventQueueAt`'s entry, which
  frame/0002 § 8's site missed for `UnitTeleport`); **the re-estimate**: 15.9–50.9 lines per frame at the mid queue
  rates (14.9–57.2 low to high), 39 653–127 231 for ten windows, a three-window session 0.67–2.15 plan-0045 sessions;
  Q2's 177 860 not met at any rate; 32.9–67.9 breakpoint stops per frame. Dev-run note: an `EmuBoundary` memory-spec
  `bytes` directive of 0x1000 bytes or more is not re-applied per case (frame/0003 *Dead ends*).
- **2026-10-30 — P1.3 review, the P1 review (architect, Tier A: rulings asked; `lane/r55c`).** **Accept with fixes
  (8)**, written into the lane's files. Anchors spot-checked against the pinned image by objdump: `QUESTS_TimerAdd`'s
  front push (0x00543F51 head load, 0x00543F6D next, 0x00543F83 head store) and `QUESTS_TimersRun`'s unsigned
  `jae` (0x00543E6E) and `AL` test (0x00543E87); the periodic calls (0x0052D912–0x0052D96C, signed `idiv` by 20, 12,
  11; the unload per act slot); the sweep tick (0x0052D316–0x0052D33D: `idiv` 1 500, items then records, acts 0..4),
  the items' signed `jg` (0x00558BEA, so `≤`) and the records' `jle` (0x00542AFF, so `<`); `DUNGEON_RoomCreate`'s head
  push and flag (0x0061991F–0x00619925); `NewRoomsUpdate`'s flag test, head read, wanderer call, bit tests and flag
  clear (0x0052D1A9–0x0052D21D, `RoomRestoredGet`/`Set` on bit 1); `ClientsRoomSync`'s `0x80001FFF` mask and the save
  call (0x0052D45C, 0x0052D4AE–0x0052D4BD); both kind-6 handlers' unsigned `ja` and re-queue (0x00580B8B–0x00580BC8);
  kind 11's body (0x00580BE6–0x00580C08) and its first queue at +250 (0x00534B1D); the prune's `PetRemove(guid, 0)`
  (0x005755FB) and the two release tests (0x00575132, 0x005748CC); `EventQueueAt`'s register use from both callers
  (0x005417E8, 0x0054181A) and the frame −1 call's return 0x005416DC. A full objdump call count matches every count the
  finding gives (`DUNGEON_RoomCreate` 1, `EventQueueAt` 2, `EventQueueEveryFrame` 3, `ActiveRoomFree` 2, `ActRoomsHead`
  11, `QUESTS_TimerAdd` 26). Kept manifests pass (static `abfc7c4d…` 80 lines, emu `269cde48…` 21, the five dev
  manifests), `check.txt` matches § 8's 19 separating counts, the tool hashes match, `frame_volume.py estimate` still
  equals P1.1's `volume-estimate.txt` byte for byte and `estimate13` its kept output; the 20 symbol rows clash with none;
  gate green. Fixes: **overclaim 1**: `ClientsRoomSync` "never the game seed" holds with the two saves stopped; the
  frame-8 192 `SaveGameClients` (0x0052D4BD) and `AutosaveTick` carry the 28 RNG functions of the item paths, whose seed
  is not read (summary, § 3). **misread 1**: kind 11 "first 250 frames after its placement" where its first run is at
  +250 (summary). **omission 5**: the frame's shared seeds listed in one place (summary bullet: the game seed, each
  level's seed, the object-region seed of chain/0001 § 3.2, the quest seed; the request's list lacked the last two);
  a room created during the walk in a later act is walked in the same pass, in an earlier act the next frame (§ 4 and
  summary); `DUNGEON_RoomCreate`'s call of the act's `+0x4C` (0x0061994B–0x00619954; open question 7, the writer
  unread); `TM`'s 0.224 assumes one loaded act and leaves out the sweep, and a `QE` line is a request (a kind ≥ 15 at
  0x005416B7 queues nothing) (§ 9); `re/types/lifecycle.h`'s `DungeonActFrame` given `+0x10`, `+0x4C`, `+0x54`.
  **stale cross-reference 1**: Phase 2b's pilot paragraph still gave P1.1's "2.5–2.9 times" and frame/0001 § 7 as the
  estimate (now `estimate13`'s per-scene values and stops). Rulings: **(1) the draw table**: accepted with the shared
  seeds above, `[I]` by direct reach; a pair of events on one seed in one frame is a shared-seed pair for any of the
  four, and Phase 2b's 20-pair floor stays on the game seed. The frames `≡ 0 (mod 8 192)` are a boundary until the
  save's seed is read. **(2) the closed log design** (frame/0003 § 9) is Phase 2b's; the floors stay and gain (Phase 2b
  *Added at the P1 review*): a window holding a multiple of 1 500, the save frame as a boundary oracle, the kind-11 and
  kind-6 seed-equality counts, and any in-walk activation named. **(3) 0055 Q1** stands at 10 windows × 250 frames,
  three scenes, two per scene, 5 000 chained events: the new estimate (15.9–50.9 lines per frame, 3 965–12 723 per
  window) moves no floor; Q2's volume test is not met at the high rates (42 902 < 177 860); the 820–1 700 stops per game
  second are what the pilot's *carried* test measures, and the three-times stop is now per scene (47.6, 123.9, 152.7).
  **(4) kinds 11 and 6** are modelled draw-free events, not boundary oracles: the stops are justified (the pet release
  only under a non-zero `PetRemove` argument, read at both tests; `UninterruptibleEnd` only for a monster's kind 2), the
  prune branch needs a dead pet, which no planned scene holds, so the windows test the live-pet half only; the packets
  stay outside the model. **(5) the activation-order record** (§ 5) answers the chain spec's activation `[L]` with its
  limit: Phase 3 restates it as `[I]` from (a)–(c), (a) a logged input until a movement model exists (plans 0050 and
  0054); the per-level seed makes the order of activations within a level part of the record, which (a)–(c) already
  give. **(6) ADR-0022's early gate**: plan 0052 landed P1.2 batch 4 (`f3005398`, ai/ only) since the P1.2 review;
  P1.3 cites drlg/0009, monsters/0002, quests/0001, drlg/0005 and no 0052 output; no re-ruling. **The EmuBoundary
  problem**: a scan of the 421 memory specs under `workspace/logs/` finds per-case directives of 0x1000 bytes or more in
  six earlier kept runs (sweep-s1e `calcvar`, `eval`; sweep-s1f `calcvar2`, `varroll`; calc-emu `eval`, EmuCall;
  p51s `calcemu/eval`); no case writes into any of them, so only a store by the emulated code could carry between
  cases, and these are table readers: no kept claim is known to move. Routed as a tools fix and a byte-for-byte re-run
  ([backlog entry](../backlog/archive/2026-10-30-architect-reverser-emu-page-directive-reapply.md)); `const` directives are
  written once by design. **The frame/0002 § 8 correction** is right (two `EventQueueAt` callers, three
  `EventQueueEveryFrame` callers, the return test) and is carried by a dated note there. **Phase 2a: go** (reverser, no
  game, no slot, no Ghidra; replays under `MemoryMax=4G`; P0 accepted, P1 reviewed). **Phase 2b: gate unchanged**: P1
  is reviewed; it waits on plan 0052's P3a review (ADR-0022, ADR-0016), and its pilot uses plan 0056's runner library.

- **2026-11-03 — PetType `partysend` readers (archivist, `lane/a63`).** [PetType](../tables/PetType.md) `partysend` links the
  two readers of [frame/0003 § 6](../findings/frame/0003-timers-activation.md) (`PlrPetsStatusSend`, `PetListPrune`), `[I]`.
  Backlog entry closed.
- **2026-11-03 — The emulator spec re-apply fix and the re-run (reverser, static, `lane/r55e`; review requested).**
  Closes the [backlog entry](../backlog/archive/2026-10-30-architect-reverser-emu-page-directive-reapply.md) of the P1 review,
  and, beside it, the [States count entry](../backlog/archive/2026-10-30-architect-reverser-states-unreached-58-vs-56.md).
  Record: [run:2026-11-03-emu-spec-reapply](../findings/frame/experiments.md#run2026-11-03-emu-spec-reapply).
  **Cause**: Ghidra 12.1.2's `MemoryPageBank.setPage` keeps the caller's byte array as the page, with no copy, when a
  chunk is a whole page at buffer offset 0, so a directive that starts on a 4 KiB boundary and is 0x1000 bytes or more
  shared its first page with the spec's own array; stores there survived into the next case's re-apply. **Fix**:
  `EmuTrace.java`, `EmuBoundary.java` and `EmuCall.java` write a fresh copy of each per-case directive for every case
  (`const` unchanged, written once). **Test**: `tools/emu_zerotest.py`, the kept form of `r55c/dev/zerotest`: three
  identical `RNG_Range` cases on a seed inside the directive, plus a first-case `w`; 19 script-and-spec runs (lengths
  0x800 to 0x46230, `bytes` and `load`, aligned and unaligned) all pass with the fix; the pre-fix control copies fail
  exactly the 11 aligned long ones (each case drawing from the previous case's seed) and pass the other 8.
  **Re-run**: the six kept emulations the entry names (`sweep-s1e` `calcvar`, `eval`; `sweep-s1f` `calcvar2`,
  `varroll`; `calc-emu/eval` under EmuCall; `p51s/emu/calcemu` `eval`) are byte-identical with the fixed scripts; no
  finding changes. `tools/emu_spec_scan.py` over the 483 memory specs under `workspace/logs/` finds those six and
  twelve `lane/r55c` development specs, nothing else. **For the batch lanes**: no kept `ai-cat-emu-*` run (plan 0052,
  `workspace/logs/r52*/emu/`, 233 `.mem` files, through `r52h`; `r52i` had written none at the scan) holds a directive
  of 0x1000 bytes or more, per-case or `const`, and their per-case `w` writes were always fresh arrays, so none needs a
  re-run; from now on the batch lanes run the fixed scripts. **States**: stats/0002 surprise (f) now says it lists 59
  rows (the 56, plus 57/100/106 named by Misc) and why 175 `fullsetgeneric` and 176 `monsterset`, archaeology/0002's two
  more, stay out (named by Sets `state` parameters; set by the stat 98 callback), from a kept comparison
  (`workspace/logs/r55e/states-reconcile.txt`). No symbol changes.
- **2026-10-30 — Phase 2a checkpoint, not started in substance (reverser, `lane/p55a`; owner pause).** Paused on the
  owner's token-budget stop before any tool was written: no `tools/frame.py`, no replay, no run record, no finding,
  nothing kept under `workspace/logs/`. Read so far: this plan's Phase 2a and the P1 review (Phase 2a go),
  `tools/frame_corpus.py` (`read_events` gives per log `(frame, kind, unit type, unit id, entry seeds, exit seeds,
  line, sub)`, a begin/end pair folded at the begin's line) and the corpus block of `docs/inventory.md` (331 stamped
  corpus logs, 9 stamped loggers; `stats`, `economy*` and `h6b` without unit ids, `h6b` without seeds). **Resume
  steps** for a fresh lane on this branch: (1) read the pass order in frame/0001 § 2 and § 5 (the drain runs before
  `GameTick`; check at which point each logger reads its frame number relative to `GameTick`'s `Game+0xA8`
  increment, since a drain event logged before the increment carries the previous frame), frame/0002 §§ 1–2 (the ten
  walks: missiles, players, monsters, objects, items, then each type's every-frame list newest first and its slot
  oldest first) and frame/0003 §§ 1–4 (the periodic calls after the room sync); (2) write `tools/frame.py` (the plan's
  name) with tests: a kind-to-pass map per logger, kept in the tool with its anchor per kind, each logged event given
  its pass rank from its kind and unit type (nested events take their caller's pass), `check` predicting the order of
  every frame with two or more events and the seed hand-off of each same-seed pair in a frame; (3) dev runs under
  `workspace/logs/p55a/dev/`, the kept run as run:2026-10-30-frame-order under `workspace/logs/p55a/` with a manifest,
  each replay `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/frame.py …`, one session at a time;
  (4) count per logger and kind the events compared, the mismatches (0 or each explained), the limits (no unit id,
  no seed), the re-chained resynchronised entries of plans 0045 and 0052 (Done-when), and the cross-type every-frame
  runs per receiving type that the kept logs hold (P1.2 review ruling 1); (5) findings in frame/0004 and the run in
  frame/experiments, the lane's usage row, the review request.
- **2026-11-03 — Phase 2a the order model on the kept logs (reverser, `lane/p55a`; review requested).**
  [frame/0004](../findings/frame/0004-order-on-kept-logs.md), [frame/experiments](../findings/frame/experiments.md)
  (run:2026-11-03-frame-order; the checkpoint's name `2026-10-30-frame-order`, run on 2026-11-03 and dated so), new
  tool `tools/frame.py` (`73715f53…`: `kinds`, `reach`, `check`, `rechain`) with `tools/test_frame.py` (18 tests);
  kept outputs under `workspace/logs/p55a/` (manifest `11056497…`, 8 lines), development runs under
  `workspace/logs/p55a/dev/` (manifest `dabf2b83…`, 39 lines, passing from `dev/`). No symbol rows. Totals taken after
  merging `main` `dda63dfd`. The model: 21 ranks per stamp (`GameTick`'s passes, the ten walks, the drain after the
  tick), a kind-to-pass map of 115 kinds over six logger families with an anchor per kind (the hook's direct-call
  reach to pass roots, the return address's, a dispatch call site, anim's logged phase, the unit type; nested events
  take their pair's set). Found, over the 331 frame-stamped corpus logs (6 436 250 events): **0 mismatches** in the
  192 294 frames with two or more placed events (1 719 463 placed, 267 695 by their own kind), 14 061 separating pairs
  (3 105 without the logged phase), four control orders failing (17 040, 9 608, 110 and 87 events); the slot lists
  oldest queued first (4 579 pairs, 0 inverted) and the missiles' every-frame list newest first (24 652 pairs, 0 oldest
  first) in the game's own runs; a skill request in the drain carries the preceding tick's stamp (87 pairs; frame/0001
  § 5 raised in part); 1 065 396 one-frame seed hand-offs, 1 023 086 handed, 42 310 stepped, 0 reversed, 0 off (game
  seed: 440 754, 4 675 stepped). **Done-when:** the 309 395 other frames of the 501 689 with two or more events hold
  fewer than two placed events (74 of the 89 hooks are reached through pointers the reach does not follow), so they
  test nothing; the record names it as the limit (frame/0004 § 1, open question 1). Re-chained: 7 more player resyncs
  (part 2's "nested" class), so 142 of the 281 player gaps; 0 of the 331 monster gaps (no AI line in their logs); of
  the 3 459 pairs 3 155 + 90 chain, 214 stay open, each named with its first unclosed link (`rechain-gaps.txt`).
  Cross-type every-frame queues the kept logs hold (P1.2 review ruling 1): monsters 926 (79 in the missiles'
  every-frame walk, 847 in the players' slot walk), players 0; objects, items and missiles none logged. Limits per
  logger: stats, economy (all three) and h6b carry no unit id, h6b no seed; combat, two-combat, economy-hire and h6b
  have no frame with two placed events. frame/0002 §§ 1–2's walk and list order and frame/0001 § 5's stamp carry dated
  `[C]`-in-part notes. **Review request (architect):** the model's ranks and the kind map's rules (is the
  return-address rule a fair anchor; the `EF` phase as an observation, not a prediction, and the 3 105 pairs without
  it); the Done-when reading (0 mismatches where anything is placed, the unplaced frames as the stated limit, or a
  re-scope); the 7 nested re-chains; the dated notes in frame/0001 and frame/0002. The research-map row and the plans
  index are not touched (architect's files).
- **2026-11-03 — Phase 2a Tier B check (architect, `lane/p55a`): accept with fixes (2); Phase 2a met in part.** Fixes:
  overclaim 1 (frame/0004's headline now says the order is tested by the 14 061 separating pairs, anim 13 967 and skills
  94, and that the stats logs' 162 249 placed frames hold none; the Done-when "every frame" is not met as written),
  omission 1 (the thin items of frame/0002's part-`[C]` note carry their pair counts, 7 and 7, 4 by call site). Rulings:
  (a) the stated limit does not meet the Done-when as written; the second clause (re-chains and a reason per remaining
  gap) is met; (b) the return-address anchor is a fair `[I]` placement, used for the six listed functions only, with the
  caveat that "closes" cannot see pointer-table callers; (c) the `EF` phase is rightly an observation. **Re-scope
  (architect, plan owner):** Phase 2a stays open as *met in part*. Its remainder is closed by either of two steps,
  recorded here as **P2a-ii**: a static read of the dispatchers behind the pointer tables that reach the 74 open hooks
  (reverser, no game, one Ghidra; the cheaper cross-check, queued for the next free static lane after 0054·P1), and
  Phase 2b's `UE0`/`UE1` lines, which close it by observation. Phase 2a closes when P2a-ii lands or 2b's first window
  places the open hooks, whichever first. The research map's `sim/frame` row says "P2a met in part".
- **2026-11-03 — Phase 2a-ii the static dispatcher read (reverser, static, `lane/r55f`; review requested).**
  [frame/0005](../findings/frame/0005-dispatchers.md), [frame/experiments](../findings/frame/experiments.md)
  (run:2026-11-03-frame-order-2), `tools/frame.py` (`9d6487a6…`; the check on `a21171fc…`, commit `966613c8`) with
  `tools/test_frame.py` (23 tests); kept outputs under `workspace/logs/r55f/` (manifest `2109a8b4…`, 24 lines), development
  runs under `dev/` (`e72339cd…`, 18 lines). No symbol rows. Declared: 35 tables, 20 iterators, 5 registrars, 18 quest
  field offsets, 2 one-off callbacks, 18 block stores, 7 host roots, 12 dead functions. **Found:** of the 74 open hooks, 9
  close (8 through a declared edge, `PayGold` by a dead caller) and 65 do not: each reaches 19 of the 21 ranks and keeps 50
  open functions, callbacks whose client-side registrars were not read, so the tool gives each every rank (`universal`).
  Closing them could not narrow them, because the reach has no calling context. **Replay:** 501 689 frames with two or more
  events; 383 349 hold two or more closed sets (192 294 in Phase 2a), 0 mismatches, 0 nesting conflicts; 17 254 separating
  pairs (14 061), 9 029 without the logged phase (3 105), anim 16 935, skills 319, the other loggers 0; four controls fail;
  hand-offs unchanged, 0 reversed; `check --direct` reproduces Phase 2a. Three passes `[C]` by pair count: `PathStep`
  monsters' half 3 820, `UNIT_AnimAdvance` 568, `RunStaminaDrain` 90. **Done-when: not met as written.** 118 340 frames hold
  fewer than two closed sets. Counting universal events, 501 659 frames place two or more and 494 897 place all, which tests
  nothing and is not offered as meeting it. **Remains for Phase 2b:** the 65 universal hooks, by its `UE0`/`UE1` lines; the
  second clause stands as ruled. **Review request (architect):** whether this closes P2a-ii with the remainder moved to
  Phase 2b; the rule that a hook left open takes every rank; rank 21 for everything outside `GameTick`, and
  `CreateClassSelect` as a judgement root; the stack-block match, read by name only. The research-map row and the plans index
  are not touched (architect's files).
- **2026-11-03 — Phase 2a-ii Tier B check (architect, `lane/r55f`): accept with fixes (3); P2a-ii closed, Phase 2a stays *met in part*.** Fixes: overclaim 2 (frame/0005's three-hook `[C]` and the run's conclusion now say the pairs show the order against the logged neighbours, not the rank within the set; the summary says the frames without a separating pair agree trivially), omission 1 (the per-hook pair counts overlap by the 43 `DR0` → `PS0` pairs, and `RunStaminaDrain`'s 90 are split by anchor kind; frame/0004's headline carries a dated pointer to the wider counts). Rulings: (1) P2a-ii is closed as the static step it was; Phase 2a's Done-when is still not met as written (118 340 frames hold fewer than two closed sets, 65 hooks open), so Phase 2a stays open as met in part and closes at Phase 2b's first window that places the 65 hooks by `UE0`/`UE1`; the second clause stays met. (2) A hook left open takes every rank: sound (only widens), `[I]`, tests nothing, and its events are not counted as placed. (3) Rank 21 outside `GameTick` is a fair `[I]` for the single-player corpus (the scope is stated); `CreateClassSelect` as a root adds a rank to its callees only and cannot close a hook falsely. (4) The stack-block match can only add false edges, which widen a set; `[I]` stands, and its 18 are in the kept `reads/edges.txt`. `PayGold`'s closure rests on 0x00578ED0 having no reference, checked by the tool at each start and recorded `[I]` in items/0011; `PayGold` has no pair and stays `[I]`. The research map's `sim/frame` row says "P2a met in part; P2a-ii landed, 9 of 74 hooks closed, 65 to Phase 2b".
- **2026-11-04 — Owner decision.** This plan counts as current under the owner's order to finish current plans and start no new ones: Phase 2b, Phase 3 and Phase 4 run after plan 0052's Phase 3a.
- **2026-11-04 — Phase 2b tool preparation (reverser, no game, `lane/p55a`).** ADR-0022 holds the harness runs until plan 0052's
  Phase 3a is reviewed; nothing was launched (no game, slot or wine), no finding, no `re/symbols.csv` row, no prediction. **Built:**
  `tools/gdb/frame.gdb` and `tools/gdb/frame.py` (the logger, rev 1), `tools/frame_window.py` with the `window` and
  `window-selftest` subcommands of `tools/frame.py` (the reader and checker), `tools/frame_sessions.py` (the session runner),
  `tools/frame_volume.py` (`estimate13_rows` split out of `estimate13`, whose output is byte for byte unchanged),
  `tools/test_frame_window.py` (12 tests, no game, no gdb). **Logger:** the closed lines of frame/0003 § 9 with P1.1's
  and P1.2's: `FT0` (frame = `Game+0xA8` + 1, the pre-increment value in `pre`, the game seed, `g_HitClassCounter` at
  `0x0088CAD0`), `FT1`, `FP` (the seven pass calls and `0x0052D96C`, written when the game seed differs from the last
  logged one), `ACL`, `UE0`/`UE1` (the 20 sites of frame/0002 § 8, the unit and game seeds), `MSG0`/`MSG1` (opcode, length,
  the first 24 bytes, the player seed), `SYS`, `RU0`/`RU1` (the loop's per-room call and next-room load, and
  `RoomUpdateOne`'s entry and rets), `TM` (four sites), `TQ0`/`TQ1`, `RC`, `RR`, `QE`, `QF` (not when the return address is
  `0x005416DC`), `SV0`/`SV1` (`SaveGameClients` at `0x0052CA10` and its three returns), and `WIN`/`WEND`/`HB`. Outside a
  window only `FT0` and `FT1` stop (the other breakpoints are disabled; `HB` every 250th frame); a window opens at an `FT0`
  from `FRAME_WINDOWS` or from lines the runner appends to `FRAME_CTL`, including a `cover=M` window that puts a frame
  `≡ 0 (mod M)` in its middle. **No write** (rule 17): the logger reads memory and registers and enables or disables its own
  breakpoints; every `stop()` returns False; `tools/test_frame_window.py` runs the handlers over a fake read-only memory
  (a write raises) and greps the source. Sites not in `re/symbols.csv` or a finding are 33 derived addresses, each checked
  against the binary by the test: five pass calls inside frame/0001 § 3's range (`0x0052D8E6`, `0x0052D8F2`,
  `0x0052D8F9`, `0x0052D900`, `0x0052D907`), the 20 instructions after the unit-event calls, the four `ret 8` of
  `SrvPacketDispatch`, the returns of `SaveGameClients` (`0x0052D430`, `0x0052D4C2`, `0x00530446`) and the timer callback
  (`0x00543E87`); `ACL` is cut to the act and the return (the finding's period and counter have no named site). All `[I]`.
  **Reader:** `python3 -I tools/frame.py window [--pilot] [--allow-stray] LOG ...` tests (a) whole (an `FT0` and `FT1` for each
  of `len` consecutive frames, no gap, repeat or reorder, every pair closed in its frame and nested, every line stamped with
  its frame, 0 lines it cannot parse), (b) unmoved (each seed object's reading against the previous *logged* reading:
  handed, stepped k, reversed, off; never resynchronised; a draw before an `FP` or `TM` site is listed apart as located),
  and prints what the record states: lines per frame against `estimate13` mid (and the 3x stop), stops per frame, the hit
  count per breakpoint, `QE`+`QF` per `UE0` against the stated mid rates, chained events, windows per scene, each timer's
  period seen, room activations and those inside a `NewRoomsUpdate` walk, frames `mod 1500` and `mod 8192`, shared-seed
  pairs (consecutive game-seed-drawing unit events of two units in a frame, handed and in pass order), kind-11 and kind-6
  draw-free runs, the session's lines against Q2's 177 860, and the Done-when floors. `--pilot` judges the first window by
  (a), (b) and (c) (WEND ok, no `LOGERR` or `CAP`). **Negative controls** (`window-selftest`, 11 checks): a gap, a repeat, an
  unclosed pair, a game seed off by one, a unit seed off by one, a reversed pair, an unparsed line, stray text and a lost
  `FT1` each fail the test they are for; the clean synthetic window passes. **Runner:** `tools/frame_sessions.py` on
  `tools/harness_runner.py`: `list`, `plan SCENE`, `build`, `gate LOG` and `run --slot N ... SCENE` for `town`, `pack`
  (Cold Plains, `farm --sweep --wp 1,2`) and `maze` (Den of Evil: `explore` out of town, then `farm --descend 0,1,2,3
  --descend-to 8`), each one fresh single-player process (`enter-normal.steps`), Teleport hops and Nova only; it does not
  launch without `--launch` (`--dry` prints the plan), refuses slot 0, and runs the pilot gate after each scene's first
  window (stop on a failed (a)/(b)/(c) or lines per frame above 3x the scene's estimate). **The command a harness lane runs
  first** (the pilot, slot N from its prompt): `python3 -I tools/frame_sessions.py build --saves SAVES` then
  `python3 -I tools/frame_sessions.py run --slot N --tag p55 --saves SAVES --run YYYY-MM-DD-frame --pilot-only --launch town`;
  its log is `workspace/logs/frame/<run>-s<N>-5501-town.log`, judged again by
  `python3 -I tools/frame.py window --pilot <that log>`. A smoke session of the logger first (harness-play.md § Before the
  batch) is that same run under a `dev-` run name. **Untested without a game:** every `gdb` behaviour (the breakpoint syntax and
  `enabled` flips are those of `tools/gdb/ai.py`; gdb's own `hit_count` is expected to stay 0 for a `stop()` that answers
  False, so `WEND.hits` is the hit count per breakpoint and `ghits` a cross-check the first session shows); that `ECX` is
  the game at `FT0` and `ESI` the record at all 20 `UE0` sites (read from the disassembly and frame/0002 § 8, not run);
  the stops per frame the game survives under gdb (the pilot's (c)); that `d2run.py` hands `FRAME_CTL` to gdb (it copies
  `os.environ`); `pilot.py`'s own breakpoints sit beside these and add stops the hit counts do not include; the Act I
  town's waypoint screen position (`--wp-x/--wp-y`), the route out of the town to Blood Moor, which `LvlWarp` row is the Den
  of Evil's entrance, whether Nova and the character's level suit the pack, that `hop` is the right command in town, the
  `mod 8192` window (`--long`, a 5.5 minute wait for the frame), and whether the pack's and Corpsefire's monster kinds are
  in plan 0052 P3a's reviewed tier. The chain's reading of "unmoved" (entry equals the previous logged exit, an `FP` or `TM`
  step located not counted) is this lane's; the architect confirms it at the pilot review.

- **2026-11-04 — Phase 2b the pilots (reverser, `lane/p55b`, slot 1; stopped at Q2's trigger for the pack scene).** run:2026-11-04-frame,
  frame/0006, tools at `8f026bf2` (frame.py `a6ecf7cd…`). **Town pilot (Act I, seed 5501, frames 501-750): passes (a), (b), (c)**: 250 consecutive
  `FT0`/`FT1` pairs, 0 unparsed lines; 0 mismatches, 0 located draws, 413 chained events (426 `UE0`); 10.0 s wall, 25.1 frames per wall second,
  7.17 lines per frame (0.45 of `estimate13` mid 15.9), 18.2 stops per frame (32.9), `QE`+`QF` per `UE0` 0.90 (stated mid 1.35); `WEND.hits` is the per-breakpoint count
  (`ghits` is empty). The session's two further windows (a walk with 17 `MSG0`; the `mod 1500` frame 1500) pass (a) and (b): 573 and 557 chained events. **Pack pilot (Cold Plains,
  frames 1280-1529): (a) and (c) pass, (b) fails**: 8 mismatches in 3 369 chained events, unit seeds stepped 1 to 8 between two logged readings (7 on monsters, 1 on the player,
  type 0 id 1, 4 steps); 34.98 lines per frame (0.85 of 41.3), 46.0 stops per frame, 24.0 frames per wall second, 2 shared-seed pairs (2 handed, 2 in pass order), 9 room activations (1 in a
  `NewRoomsUpdate` walk). A traced development session (`FRAME_TRACE=1`, `dev-2026-11-04-frame-h`) attributed 8 monster-seed steps to the drop-quality code (0x00558640-0x005589A0) inside an open
  missile `UE0`: a kill's roll drawn on the dead monster's seed, outside the monster's own events; the steps of 1, 3 and 5 have no trace line (the six RNG entries only). The player's step is untraced. **Stop for
  the architect: the injected-logger ADR for the pack (the chain keyed by an event's own unit cannot hold where a handler draws another unit's seed).** The maze and the batch were not run; floors met so far: 3 town windows (750 frames,
  1 543 chained events), 2 shared pairs, 1 `mod 1500` frame. Tool defects found by the smoke sessions and fixed with tests: `SV1` after skipped calls, the second `UE1` at the callback path's join, the recipe starting in Act IV (new
  `framenova.json`, the runner refuses a first level other than 1), Teleport not casting in town (the town window walks), the waypoint position (`--wp-at`, 4884,5629 for seed 5501; another seed moves the town), `--view-h 0`, a
  monsters-near wait before the pack window. Predictions (committed before the kept logs) missed on the town's chained events and `QE`+`QF` per `UE0` (taken from an Act IV window), the pack's lines per frame and chained events, and "no
  mismatch on a player". No symbol row, no ledger row. Slot 1 stopped, saves restored. Branch not merged.

- **2026-11-04 — Phase 2b the pilots: review and ruling (architect, Tier A, `lane/p55b`): accept with fixes (12).** Fixes, written into the lane's files: **misread 1** (Q2's trigger: frame/0006's summary, status, § 5 and the run's conclusion read a mismatch as the trigger; Q2 is a mismatch *traced to the logger*). **overclaim 1** ("the same units step the same amounts" in a run with no trace hooks: the traced dev-h shares neither; the untraced dev-g does, on 7 of 8, one input script replayed, and that is what is stated). **wrong anchor 1** (`0x0055891A` for the trace's range, whose fifth site is `0x0055894F`; the function named). **miscount 2** (the sessions' 2 321 and 10 037 logger lines were early first checks, 6 782 and 10 038; "one `mod 1500` frame (town)" where the pack's window holds frame 1500 too). **omission 5** (what the trace covers: 8 of 34 steps on 2 of 10 units; rule 18: the 852 sites of `tools/gdb/lcg-sites.txt`, and the draws in combat/to-hit, items/tc, items/economy § H, so both `[L]` on the steps are closed; ADR-0028 item 1's case list; item 7's separation line; the pack's kinds unclassified against the `lane/s52a` ruling). **stale cross-reference 1** (frame/0003's shared seeds, a dated note: a fifth kind, the P1 review's own miss; ADR-0022's context names it). **other 1** (the manifest "passes": `…-s1.bg.txt` was appended 17 s after it, 12 of 13 lines pass, no count rests on it). Checked and held: the callback path's `UE1` pairing (objdump: all ten callback sites are `call eax; jmp` to the dispatch call's next instruction), `SV1` only after `SV0`; the recipe's one change from `specnova.json`, the act byte (128 for 131); predictions committed before each kept log (`abb7ebb6` before the town's, `241adf4a` before the pack's), their misses kept; manifests and logs by hash; `-ns` (`tools/d2run.py` line 342, no `--sound` in the runner). "Reproduce" is not read as confirmation: it is one input script.

  **Ruling 1, Q2: not a logger problem. No ADR, nothing for the owner.** The logger kept up and moved nothing. The mismatches are the reader's: it keyed each seed to its own unit's events, and the game draws on a defender's and a dead monster's seed in another unit's event, as the reviewed specs state draw by draw and as ADR-0022's context says ("a defender's seed hit twice in one frame"). The window found what a window exists to find. (b) reads: every entry chains, every mismatch is traced, none to the logger. **The pack pilot's (b) is met at `[I]`** for all 8: the attribution is [frame/0006 § 6](../findings/frame/0006-frame-windows.md) (seven kills' drops on the dead monster's seed inside a missile's event, one-to-one with the seven monsters queued kind 12 and kind 1 by another unit's event, the game-seed steps 6, 6, 6, 6, 0, 2, 0 as `Act 1 Champ A` and `Act 1 H2H A` say; the player's 4 are monster 28's melee hit, block and armour wear). All counts from the kept log, all readings `[I]`; the `XS` lines below hold the sites. That window is not counted towards the floors: it has no sites and it is not a Fallen or shaman pack (`corruptrogue1`, `cr_lancer1`, with `brute1` in the level).

  **Ruling 2, the chain's rule (reader rev 2), so that a mismatch can still fail.** Accepting any step in another unit's event would test nothing. A chained seed is the game seed or a unit's seed from its first reading in a window. *What is logged:* `XS` for every step, at all 852 LCG sites. *What the reader asserts, each of which fails the window:*
  1. **Arithmetic.** It keeps each chained seed's value and applies the LCG at each `XS` whose low word matches it; every logged reading must equal that value exactly. A seed that moves with no `XS`, an `XS` too many or a write fails. A low word two seeds share (a new missile's `Init` of the game seed's low) is resolved by each one's next reading; neither resolving fails.
  2. **Class.** Each step is `own` (that unit's event is open), `game` (the game seed, inside an open pair), or `touch` (another unit's event is open). A step with no pair open fails unless its site is listed as a pass draw (frame/0001 §§ 3–4, frame/0003 §§ 1–3). **The "located" reading is struck as an exemption by position:** it has been 0 in every window, and a draw before an `FP` or `TM` line passes only by its site.
  3. **Touch table.** A `touch` is good only at a site or return address in a table in `tools/frame_window.py`, committed before the kept log, each row with its `fn:` and spec, and only under its trigger: **kill**: on a unit with a `KD` line inside the open event, the sites of `TC_ResolveDrops` and `ITEMS_DropRollQuality` (and the unit's own death handlers, combat/delivery E5); **defender**: on the unit an open melee or missile event delivers to, the sites of `COMBAT_DefenceRoll`, `COMBAT_ApplyCold`, `COMBAT_DurabilityLoss`/`ITEMS_DurabilityLossRoll`, `GetHitRoll`, the mode test's draw, and the stat events on the defender; **owner**: on a missile's owner inside that missile's event, the to-hit, leech, stun and stat-event sites (combat/overview, skills/missiles). Any other site fails. A kept window's failure is not repaired afterwards: the window is not counted; the site, once traced to a spec, is added by a commit for the *next* window.
  4. **Game seed, predicted.** Inside an event with a `KD`, its steps are even and 2 per item (items/tc H7). A missile's first reading is `Init(low)` of a game-seed step in that event (skills/missiles C3, predicted value, not a "first"); other units' first readings stay named firsts.
  5. **Order, predicted, the plan's own question.** Within a frame the walks run in rank order; slot events run in their `QE` order, a cancelled record skipped; an every-frame walk runs newest `QF` first, where both are in the window. The review's reading of the kept logs: 5 264 `UE0`, 0 rank inversions, 1 484 slot events placed, 0 inverted (frame/0006 § 6, `tools/frame_foreign.py`).
  6. **Draw-free kinds.** Kind 11 and kind 6: no `own` step.

  *Oracles, counts not predicted:* a unit's `own` draws (AI, skill do, missile own: their specs' claims, ADR-0022's boundary), the number of drop draws on a dead monster (items/tc `[C]` over 9 265 calls; the spec cites it). *A log with no `XS` lines* is read with no touch allowed, so the town's three windows stand as passed and count, and the pack's 8 stay listed. **Negative controls** in `window-selftest`, each failing its test: a step with no `XS`; an extra `XS`; a touch at an unlisted site; a listed site with no trigger; a kill's odd game-seed steps; a missile's first reading off by one; an inverted rank; an inverted slot order; a step with no pair open at an unlisted site. The record states per window: touches per class and site, entries whose seed had moved against those it had not (ADR-0028 item 7), and order pairs.

  **Ruling 3, the volume.** `XS` adds a line per server-thread step. The kept pack window's known steps are about 3.7 a frame (game seed 862, of them 514 in three room updates; unit seeds 57, of them 32 the touches; over 250 frames), and item, room, new-monster and missile-local seeds and the client thread are not known. Estimate, not measured: 40 to 60 lines per frame for the pack (35.0 now), stops 55 to 90 (46.0), bursts at a room activation. **The stop rule is unchanged** (pack 123.9, maze 152.7, town 47.6), and so is Q2's 177 860 a session. Slow and passing is a pass.

  **Ruling 4, the scenes and the floors. All stay; Done-when is not changed.** (i) **The pack is Blood Moor's Fallen:** `fallen1` (19) is in level 2's pool for every seed tried (5501–5508, `tools/monpool.py pool`), and Cold Plains on 5501 holds none of the tier's. Zombies and quill rats beside it are the ruled boundary oracles, named per window. (ii) **The maze's route** is the same process: Blood Moor is on the way to the Den. `explore --any-level` walks in a town (`tools/d2pilot.py`; the runner's `explore --hops` does not), then the window, then `farm --descend 0,1,2,3 --descend-to 8`. So it needs no `--wp-at`, and a new map seed costs one session and no calibration. If the walk out fails three dev tries, the fallback is Cold Plains on 5503 (pool 43, 58, 165: shamans) with one objects log for its waypoint. (iii) **Seeds.** The Done-when does not name seeds and does not need to, but a session on one seed with one script repeats itself (the kept window and dev-g share 7 of 8 mismatches): run each session on another map seed, 5501, 5503, 5505. (iv) **Pairs.** The rate is about 1.3 shared-seed pairs per 250 frames (2, 1, 1 in the three pack logs, one kept). **Pack and maze windows take 500 frames** (the floor is "at least 250"): two pack and two maze per session, about 100 000 lines a session. Town 3 + 8 = 11 windows after two sessions and about 21 pairs by that rate; a third session if the pairs are short. 5 000 chained events are met in the first session by the kept rate. **If three sessions leave fewer than 20 pairs the lane stops** with the measured rate, and the floor goes to the owner with the architect's options. (v) **The town's walk** for "teleports in town" is accepted: Teleport does not cast there, and the window's point (a player's messages, 17 `MSG0`) stands. (vi) **Phase 2a's remainder:** the first session's last window sets `FRAME_HOOKS=1`: the 65 universal hooks as count-only breakpoints, the histogram of each against the open event's rank in `WEND`. This places them, and closes Phase 2a under the P2a-ii ruling when each is placed or named as not reached.

  **Next, a harness lane (one slot, fresh processes, no sharing, ADR-0028's case list):** (1) logger rev 2, in `tools/gdb/frame.py`, no write (rule 17): `XS {fr, site, low, ra}` at the sites of `tools/gdb/lcg-sites.txt`, enabled with the window, lines only from the thread that hit `FT0`, other threads counted in `WEND.hits`. `low` is `EAX`, except `0x004F2959` (`ESI`) and `0x005F7C17` (`[ESI]`): the review's scan finds `EAX` ready for the other 850, and the lane's test recounts it with objdump. `ra` is the caller when the site is in one of rng/0001's seven primitives, by each one's stack offset. `KD {fr, ty, id}` at `sub_005A6830_MonDeathDrop`'s entry. `FRAME_TRACE` removed. `FRAME_HOOKS`. (2) Reader rev 2 as Ruling 2 with its controls, plus what P1.2's ruling 1 asked and the reader lacks: cross-type every-frame runs per receiving type; kinds per window from the `MON` lines. Re-run it over the kept logs and state the result. (3) Runner: `near` filters by class; the route of Ruling 4; 500-frame pack and maze windows. (4) One dev session: the first `XS` window, measure lines and stops per frame; list its touch sites, name each from the specs (rule 18), commit the table. (5) **Commit predictions**, then kept sessions on 5501, 5503, 5505 as needed. Predict: lines and stops per frame; every touch in the table; each `KD`'s game-seed steps even and 0 on a NoDrop; a champion's kill 6 when all three picks land; no `own` step in kinds 11 and 6; 0 rank and slot inversions; pairs per session. The first `XS` window of a scene is its pilot by (a), (b), (c). (6) **Stops:** a mismatch traced to the logger (now Q2 is live: stop, the architect drafts the ADR); a mismatch no spec names (stop for the architect); a scene over 3 × its estimate; three sessions. A mismatch on a spec'd draw is not a stop: that window is uncounted and the batch goes on. (7) frame/0006's next parts, the run record, the floors counted with each named, this log. **Estimate, not measured:** about 300 k tokens (harness mean 348 k; tools about 80 k, the dev session and table 60 k, sessions and record 160 k), then a Tier A review, Phase 3 and Phase 4 as planned.

  **Specs:** no `[I]` raised by the pilots conflicts with a reviewed spec: the kill's draws match items/tc, the block and wear combat/to-hit and items/economy § H, anim/timing N2. Nothing to route. Phase 3 states the fifth shared-seed kind. **The owner decides nothing now.** New tool: `tools/frame_foreign.py` (`3adda14c…`), the review's reading of a kept log.

- **2026-11-04 — Phase 2b the batch, checkpoint (reverser, `lane/p55c`, slot 1): rotated at the dev session; no kept session, no claim.** Commits: `1125fd17` (logger rev 2: `XS` at the 852 sites of `tools/gdb/lcg-sites.txt`, `KD` at 0x005A6830, `FRAME_HOOKS` with `tools/gdb/frame-hooks.txt` = the 65 `universal` rows of frame/0005; reader rev 2 `tools/frame_xs.py`, tables `PASSDRAW`/`TOUCH` in `tools/frame_window.py`, both empty until the table commit; 12 controls in `window-selftest`, 25 tests) and the checkpoint commit after it (hooks armed only in a window opened `hooks=1`; the runner's `pm` scene, `gate2`, class filter; `tools/frame_sites_list.py`). The objdump recount (`tools/test_frame_window.py` `test_sites_against_the_binary`): 852 sites, EAX the multiplicand on every path at 850, the two others are 0x004F2959 (ESI) and 0x005F7C17 ([ESI]); six sites lie in rng/0001's primitives (not seven), return-address offsets 0, 12, 12, 12, 16, 16 = 4 × pushes. **Dev findings (logs `dev-2026-11-04-frame2-{a,w,w2,b}-s1-*`, development only):** (1) the character starts beside Warriv and the stash; `explore --any-level` clicked them (dialog, stash), so the runner walks two hops east and two south first, after which `explore` leaves town for Blood Moor in about 21 s and the pack (`fallen1` 19, `fallenshaman1` 58 in the `MON` lines, tier by AI name) is in range in 15-176 s; never press Escape (it opens the game menu and the next clicks exit the game). (2) Dev b, seed 5501: two 500-frame pack windows, both whole and carried; 36.3 and 40.0 lines per frame (3x estimate 124.0), 47.3 stops per frame, 18.9 frames per wall second; chain arithmetic held (no `arith` failure in the first 20 listed); **no touch site is listed yet**, so 346 and more failures are the empty tables. (3) What the empty tables show (window 1, `tools/frame_sites_list.py`): kill touches on monsters (type 1) at `TC_ResolveDrops`+0x339 (0x0055AA09) and six `ITEMS_DropRollQuality` sites (0x0055879F, 0x00558822, 0x005588AA, 0x0055891A, 0x0055894F, 0x00558974) inside a missile (type 3, kind 0) event, as the p55b review read; the **`even` rule failed on 1 of 10 KD events as first built (game-seed steps 1, 0, 0, 3, 2, 1, 0, 0, 0, 2)**, so the rule "even inside an event with a KD" needs the steps counted per KD, between the `KD` line and the next `UE1` or the next `KD`, not for the whole event (a missile event also creates sub-missiles, one game-seed step each, skills/missiles C3): the reader change and its control go in before the kept log, then the claim is stated as the review wrote it. (4) **Room-seed steps the ruling's three triggers do not cover**: `RoomWandererTick`+0x1b (0x0054F07B), `MonSpawnTry`+0x1ec/0x225/0x23d/0x260/0x28a, `SpawnPosPick`+0x69/0xAE, `MonRegionPickClass`+0xAF, `SpawnTypeRoll`+0xCD, `RoomObjectsPopulate`+0x80 on a room's seed inside another room's `RU0`, and **between ticks** (after `FT1`, before the next `FT0`, no pair open) `UnitInit`+0x9D (0x0046606D, 217 steps in window 1), `ClientMonCreate`+0x120, `ClientMonIsChampion`+0x7EC, `ClientCritterCreate`, `ClientCritters`, `UNIT_AnimInit`+0x1D8 on room seeds, and in a tick with no pair open `InactiveMonsterSaveTest`+0x72 (0x00543262). The reader now carries `in_frame`; those between-tick steps are the main loop's client code, to be listed as pass-draw rows (`PASSDRAW`, with their specs: monsters/0001's client critters, drlg/lifecycle) and the in-RU0 room steps need a fourth trigger (`room`: another room's seed inside an open `RU0`) that the review did not name: **architect to confirm** (or the batch stops at the table commit). **Next, in order:** (a) fix the `even` counting and add its control; (b) one more dev session on seed 5503 (the maze leg: `farm --descend` ran out with "no way down" after `explore --any-level` had already carried the player to level 3 and 17, so the maze needs `explore` stopped at level 2 (`killbg` at the level wait) before the descend, and `--descend-to 8` checked); (c) fill `TOUCH` and `PASSDRAW` from `frame_sites_list.py` with `fn:` and spec for each location (rule 18: combat/to-hit, items/tc, items/economy § H, drlg/lifecycle, monsters), commit the table; (d) commit predictions; (e) kept sessions on 5501, 5503, 5505 (`frame_sessions.py run --slot 1 --tag p55c --saves SAVES --run 2026-11-04-frame2 --seed N --launch pm`), the `FRAME_HOOKS=1` window and a `cover=8192` window in the first; (f) the finding (next free number frame/0007), `experiments.md`, the floors. Slot 1 stopped, saves restored, nothing running. Tokens at the checkpoint: about 250 k. **Rotated.**
