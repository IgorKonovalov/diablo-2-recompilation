# 0050 — Animation and frame timing: unit modes, frame counts, rates and breakpoints, movement speed (ADR-0014 phase 4)

> **Status:** approved 2026-10-25 (owner), in effect 2026-10-27 (plan 0045 Phase 2 part 1 accepted); P0, P1 and P1b open, P2 after 0045·P3's review
> **Created:** 2026-10-25
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0005-presentation-formats-tools-only, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans, 0021-observed-boundaries-in-emulation

## TL;DR

**Question:** when a unit enters a mode (attack, kick, throw, cast, skill sequence, get-hit, block, walk, run,
death, an object's operate), how many game frames does the mode last, on which frames do its events fall (the
event codes 1 and 2 on which a player's do function runs, a monster's action frame, `Unit+0x4E` of a sequence), how do
the rate stats and states change those numbers (attack rate and IAS with the weapon's speed, faster cast rate, faster
hit recovery, faster block rate, velocity and the slowing states), and how far does a moving unit advance per frame?
And how do these numbers gate the timing that the reviewed specs take as inputs today: the frame a skill's do function
runs on, hit recovery, knockback and stun lengths, the block's length? This is phase (4) of
[ADR-0014](../adrs/0014-scope-game-simulation.md), in the order the owner set on 2026-10-20
([ADR-0020](../adrs/0020-skills-phase-in-two-plans.md) § Neutral). When it is done:
- `docs/formats/animdata.md` and `tools/animdata.py` decode `animdata.d2`; the mode and timing columns of the tables
  are documented, with a gate survey;
- `docs/findings/anim/0001-modes-frames.md`, `0002-rates.md` and `0003-movement-gates.md` name the code;
- `tools/anim.py` reproduces mode, event and movement events of a run per event;
- `docs/specs/anim/` is reviewed, and the action frame that [skills/dispatch](../findings/skills/0001-dispatch.md#5-the-frame-when-the-do-function-runs)
  and plan 0045's run take as a logged input, and combat's "owed to animation" lengths, have a model.

**Boundary.** Which mode a unit enters and when is an input here: for a player, the request (plan 0045); for a
monster, the AI's choice (phase (5), plan [0052](0052-monster-ai.md)). The path a moving unit follows is phase (5)'s;
its speed along that path and the steps per frame are this plan's. Animation playback, which cel is drawn, and every
client-side display of timing stay out (ADR-0005, ADR-0014 § Time): timing enters as frame counts and event frames.

## Context

- **The gate (ADR-0016 as amended by ADR-0020).** Phase (3)'s P2 is plan 0045's P2. **Phases 0, 1 and 1b of this plan
  may start only once plan 0045 Phase 2 is accepted** (`lane/p45h`, in flight on harness slot 2, paused at the owner's
  request with its resume list in the 0045 log). **Phase 2 starts only once plan 0045's spec is reviewed** (0045·P3:
  `skills/dispatch` and `skills/missiles`), because the P2 boundary (which skill inputs are modelled and which are
  oracles) is ruled against that spec. If 0045·P3's review moves a boundary Phase 1 relied on, the architect re-rules
  Phase 2's boundary at the Phase 1 review, or in a dated amendment. This plan is drafted ahead of its gate at the
  owner's request (2026-10-25); the owner approved it on 2026-10-25, effective at the gate.
- **Plan 0046 never gates this plan** (ADR-0020). Phase 1 of 0046 read all 310 functions (closed 2026-10-21); its spec
  is not written. A **catalogue function** this plan needs and plan 0046 has not specified (no reviewed
  `skills/catalogue` entry when this plan's Phase 2 is ruled) is taken as a **boundary oracle under ADR-0004**: its
  outputs that this plan reads (the mode it sets, the frame word it writes, the event it queues) are logged at the
  call, named in the spec's *Inputs* with the 0046 finding section that reads it, and taken as given; the `[C]` of the
  event covers this plan's code only. Known cases: do 103 (`DiabRun`, row 198) writes the caster's frame word
  `+0x48` from `Param1`/`Param5` and calls `0x006212C0` ([skills/0017 § 4](../findings/skills/0017-monster-8b.md));
  do 109's `sub_005CDD30_AnimNextEventByte` test; do 95's `sub_005CC440_InfernoAnim` and `InfernoLen`
  ([skills/0016 § 6](../findings/skills/0016-monster-8a.md)); start 31 (Charge) through `sub_00648690_PathSetSpeed`
  ([skills/0011 § 5](../findings/skills/0011-paladin.md)). When 0046·P3 is reviewed, its model replaces the oracle in
  the kept logs where they hold what it needs (ADR-0014 § Evidence).
- **Research map rows** (Simulation band, added with this plan's draft per the architect's rule 8): `anim/timing`
  (modes, frames, events, rates and breakpoints) and `anim/movement` (speed and per-frame steps, run and walk, the
  slowing states); the spec-writer may merge them at P3. Wiki owner: Phase 4.
- **What the reviewed specs and findings already give** (grep `re/symbols.csv`, 2026-10-25):
  - the player mode frame functions `g_PlayerModeFrameFuncs` `0x00732C10` and `sub_00580460_PlrModeSkillFrame`
    (the do function runs on event code 1 or 2 while `Unit+0xC4` bit 6 is clear); the monster mode record
    `sub_005A78A0_MonModeRecord` (table `0x006E2260`, start/frame/end per mode), `sub_005A7670_MonAttackFrame`,
    `sub_005A8670_MonSeqFrame` (`Unit+0x4E` 1, 2 or 4) ([skills/0001 § 5](../findings/skills/0001-dispatch.md#5-the-frame-when-the-do-function-runs), `[I]`);
  - `UNIT_SetMode` `0x00624690` → `UNIT_AnimInit` `0x00624390`: an object's animation start draws
    `RangeB(unit seed, FrameDelta[mode] >> 3)` when `Sync` is 0 (`[C]`, [objects](../specs/objects/README.md) G2), and a
    player's draws nothing ([player/0001](../findings/player/0001-creation.md)); so an animation start is an RNG event
    for objects at least;
  - `sub_00621810_UnitAnimFrames`, `sub_006633B0_UnitAnimData`, `sub_005CDD30_AnimNextEventByte`,
    `sub_005CF8C0_ChargeAnimIndex` (named by plan 0046, `[I]`); `sub_0056E5B0_UnitWalkVelocity` (`WalkVelocity << 8`),
    `sub_00620E80_RunVelocityStat`, `sub_00650F00_MonStatsSpeeds` (MonStats `+0x036`/`+0x038` at load),
    `sub_00648690_PathSetSpeed`, `sub_006486C0_PathGetSpeed`, `sub_006486D0_PathSetMaxSpeed`,
    `sub_006502D0_PathVelocityStep`; `sub_0057CB00_GetHitRoll` in delivery ([combat/delivery](../specs/combat/delivery.md));
  - the skill `delay` and `perdelay` (`SKILLS_NextPeriodicFrame` `0x0056CD50`, `[C]`), state lengths in frames
    (`STATLIST_SetExpireFrame`, [stats/states](../specs/stats/states.md)).
- **Inputs owed to this phase by name:** [combat](../specs/combat/README.md) *Open questions* "Owed to phase (5),
  animation" (hit recovery, knockback and stun lengths in time, the hit class, the get-hit and durability draws; the
  label predates the 2026-10-20 swap); [combat/delivery](../specs/combat/delivery.md) L659 (hit recovery and knockback
  timing); skills/0001 § 5 and its *Open questions* (which frame of a mode carries event code 1 or 2, `Unit+0x4E`);
  skills/0003 § 14 (the action frame a logged input of 0045·P2); [MonMode](../tables/MonMode.md) and
  [PlrMode](../tables/PlrMode.md) (timing deferred); the `HitClass` code list (ADR-0014 phase list).
- **Data.** `animdata.d2` sits in the base and patch archives ([mpq](../formats/mpq.md), one entry each); it has no
  format doc and no parser. [cof](../formats/cof.md) decodes COF headers (its `rate` field `[L]`, its trigger frames).
  `monseq` (1 010 rows) has no table doc. Columns already named in the table docs: CharStats `WalkVelocity`,
  `RunVelocity`, `RunDrain`, `BlockFactor`, `MinimumCastingDelay`; MonStats `Velocity`, `Run`; MonStats2 `HitClass`,
  `InfernoLen`, `InfernoAnim`, `InfernoRollback`, `ResurrectMode`; Skills `anim`, `seqtrans`, `monanim`, `seqnum`,
  `seqinput`, `delay`, `perdelay`; States and ItemStatCost `velocitypercent`, ItemStatCost `UpdateAnimRate`; Weapons
  `speed`, `hitclass`; Objects `FrameDelta`, `CycleAnim`, `Mode*`; Missiles `AnimLen`, `AnimSpeed`, `animrate`
  (missile animation: client side unless Phase 1 finds a server reader).
- **Tools to build on:** `tools/cof.py`, `tools/excel_bin.py`, `tools/d2pilot.py` (walk, run, attack, cast, `hunt`,
  `objop`), `tools/combat.py` and `tools/gdb/combat.gdb` (get-hit and block lines), plan 0045's `tools/skills.py` and
  `tools/gdb/skills.gdb` (on `lane/p45h`; they log the action frame), `tools/stats.py` (the rate stats' values),
  `tools/callee_writes.py`, `tools/ghidra.sh emutrace` (ADR-0015, ADR-0021). Tool-built saves with stock rate items
  (ADR-0013 § Neutral) give each breakpoint.
- **Leads:** none registered for timing. Phase 1b searches (ADR-0007: fetched in session only) for the community
  breakpoint tables and formulas (attack speed with the weapon speed modifier, the cast, hit-recovery and block
  frame tables, run and walk speeds, the animation data guides). Much of that folklore was measured on 1.09–1.13;
  it is compared blind and promotes nothing.

## Phases

### Phase 0 — `animdata.d2`, `monseq` and the timing columns
- **Owner skill:** archivist
- **What:** decode the animation data file and document every table column that names a mode, a frame or a rate.
- **Outputs:**
  - `docs/formats/animdata.md` (new): the layout (the lookup by COF name, the record: name, frames per direction,
    animation speed, the per-frame event bytes), the record count per archive and which archive wins (the precedence
    of [data/excel](../specs/data/excel.md) and the MPQ docs), the event byte values seen; meanings `[L]` until a
    finding anchors them; `tools/animdata.py` (parse, dump, `survey`, registered as gate survey `animdata`);
  - [cof](../formats/cof.md): a section comparing a COF's own trigger frames and `rate` with the `animdata.d2` record
    of the same name, as data only;
  - `docs/tables/MonSeq.md` (new) and `docs/tables/HitClass.md` (new): every column with offset, width and value range;
  - § Timing sections in [PlrMode](../tables/PlrMode.md), [MonMode](../tables/MonMode.md),
    [ObjMode](../tables/ObjMode.md) (the stale "animation timing is ADR-0014 phase (5)" lines rewritten),
    [CharStats](../tables/CharStats.md), [MonStats](../tables/MonStats.md), [MonStats2](../tables/MonStats2.md)
    (the mode flags and the timing columns), [Weapons](../tables/Weapons.md) (`speed`, `wclass`, `2handedwclass`),
    [Skills](../tables/Skills.md) (the timing columns above), [States](../tables/States.md),
    [ItemStatCost](../tables/ItemStatCost.md) (the rate stats: velocity, attack rate, IAS, FHR, FBR, FCR and any
    other row with `UpdateAnimRate`), [Objects](../tables/Objects.md) (`FrameDelta`, `CycleAnim`, `Mode*`);
  - `tools/anim_survey.py` (gate survey `anim`): for each player class, monster token and object, and each mode and
    weapon class, the record the tables' tokens name and whether `animdata.d2` holds it; frames and speed per record;
    the Skills rows per `anim`/`monanim`/`seqnum`; the `monseq` sequences with their lengths and event frames.
- **Done when:** each section lists every column it claims with offset, width and value range; both surveys' `SURVEY`
  lines match the docs; the token-to-record join is printed with its misses; meanings stay `[L]` unless a finding
  anchors them; the `excel_layout` baseline is regenerated if a layout changed; the gate is green. **Merge order:**
  after plan 0051 Phase 0 (it edits Skills, Missiles, MonStats, MonStats2, CharStats and States too), one at a time.

### Phase 1 — Read the timing code
- **Owner skill:** reverser
- **What:** read the mode machine and its frame counter, the rate terms, and the movement step, and say where each
  gates combat and skill timing.
- **Outputs:** `docs/findings/anim/0001-modes-frames.md`, `docs/findings/anim/0002-rates.md`,
  `docs/findings/anim/0003-movement-gates.md`, `docs/findings/anim/experiments.md` (empty heading); `re/symbols.csv`
  rows (subsystems `anim/timing`, `anim/movement`); `re/types/anim.h` (the unit's animation fields).
- **Done when:** the findings state, each with addresses and `[I]` or better:
  - **P1.1 modes and frames:** `UNIT_SetMode` and `UNIT_AnimInit` per unit type (player, monster, object; missiles and
    items if the server keeps a frame for them); how the record is found (the token from type, class, mode and weapon
    class, `UnitAnimData`, the fallback when no record exists); the unit's frame fields (the accumulator, the rate,
    the length; `+0x48` among them) and the per-frame advance, with integer widths and rounding; the event byte read
    per frame (codes 1, 2 and any other) and when the mode ends; the mode transitions at the end (attack to neutral,
    get-hit to neutral, death to dead, the sequence modes); the monster mode table `0x006E2260` per mode; the
    sequences (`monseq`, `seqtrans`, `seqnum`, mode 14, `Unit+0x4E`); every RNG draw made by animation code (the
    object `Sync` draw and any other), with its seed;
  - **P1.2 rates:** the rate of each mode from the stats and the weapon: attack rate and IAS with the weapon's `speed`
    (one-handed, two-handed, dual wield, kick, throw), the skill rate terms (sequence skills, skills that raise or
    lower attack speed), cast rate with `MinimumCastingDelay`, hit-recovery rate, block rate, the caps and floors, the
    stat recompute that triggers a rate change (`UpdateAnimRate`) and whether a rate change applies to a mode in
    progress; monsters (MonStats speeds, the `fast` mod, the champion and unique bonuses, the difficulty terms if any);
    the **breakpoints** are derived from the formula and stated as a function, not copied; where the formula is a pure
    function, its cases are emulated (ADR-0015, ADR-0021) over the stock input range so the derived tables are
    checked against the binary;
  - **P1.3 movement and the gates:** walk and run velocity (CharStats, MonStats, `MonStatsSpeeds` at load, stat 67 and
    the slowing states, `RunDrain`), `PathSetSpeed`, `PathVelocityStep` and the position advance per frame in its
    fixed-point units; then each gate: the frame the do function runs on (skills/0001 § 5), the attack's delivery
    frame (combat/0001 § 2), missile creation on the action frame, hit recovery (the get-hit mode and its length,
    `GetHitRoll`), knockback and stun lengths, the block mode's length, the skill `delay` against the animation, an
    object's operate frames; the get-hit and durability draws combat names;
  - for each event kind (mode start, frame event, mode end, rate change, movement step), its inputs, outputs, draws,
    seeds and the chaining reading (ADR-0014);
  - the community cross-check (Phase 1b) done;
  - **the boundary recommendation** for Phase 2: what stays an oracle (the AI's mode choice, the request, catalogue
    functions not specified by plan 0046, the path), the event entry points, the log windows (the frame advance and
    the movement step are per-frame paths: ADR-0014 § Log volume). The architect rules at the review.
- **Batches.** Run as **P1.1**, **P1.2** and **P1.3**, each its own lane and review, in that order; lanes rotate past
  about 4 h. P1.2's emulation runs in the same lane's Ghidra.

### Phase 1b — Community cross-check
- **Owner skill:** reverser (no Ghidra)
- **What:** search for and register the breakpoint tables, the attack-speed and cast formulas, the hit-recovery and
  block frames and the run and walk speeds; compare blind against P1.2 and P1.3.
- **Outputs:** `docs/sources.md` entries, each with the game version it describes; verdicts in the findings'
  *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2; agreement promotes nothing. May run beside any P1 batch, and lands before Phase 2's last
  session batch.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (agent-driven; **one slot** from 1–2, given in the prompt; a second only when no plan 0038
  batch, 0045 or 0046 session needs it)
- **What:** write `tools/anim.py` (model and `check`), `tools/gdb/anim.gdb` and its handler, the character recipes
  (tool-built, stock rate items, ADR-0013 § Neutral), and log a run.
- **Done when:** `run:YYYY-MM-DD-anim` reproduces with **0 mismatches** over at least (minimums are estimates, to be
  confirmed at the P1.3 review):
  - 1 500 player mode events across all seven classes, each with its start frame, its event frames and its end frame
    predicted: A1, A2 (or the class's second attack), kick, throw, cast, get-hit, block, walk and run, a sequence
    skill; at least 30 per class and mode the pilot can stage;
  - the rates: for each class, attacks at three or more IAS values on two weapon types, casts at three or more FCR
    breakpoints, get-hits at three or more FHR breakpoints, blocks at two or more FBR breakpoints, each at least 30
    events; a rate change in the middle of a mode (a stat change from an item swap or a state), if Phase 1 says it
    applies;
  - 500 monster mode events over at least 20 classes, a sequence monster (mode 14) and a `fast` champion among them;
  - 100 object animation starts with the `Sync` draw predicted (and chained);
  - 200 movement windows (walk and run per class, monsters walking and running), positions per logged frame in a
    stated window, 50 under a slowing state;
  - **chaining (ADR-0014):** for every event kind that draws, at least 20 chained pairs; a kind with none keeps its
    draw-order claims at `[I]`;
  - **the oracle replacement:** plan 0045's skills run (its action frames), run:2026-10-16-combat and the plan 0047
    runs (their get-hit and block events) re-checked with the action frame and the get-hit length modelled where the
    logs hold what the model needs; the record names what could and could not be replaced;
  - the Phase 1b cases.

  Rare-branch minimums (about 30 each) may fall short, named in the record with their counts; their claims stay `[I]`.

### Phase 3 — Spec: animation and frame timing
- **Owner skill:** spec-writer
- **What:** `docs/specs/anim/README.md`, `anim/timing.md` and `anim/movement.md` (or one file, as the spec-writer
  chooses at the start); update skills/dispatch (the do frame), combat (hit recovery, knockback and stun lengths,
  block, the "owed to phase (5)" question relabelled and answered), stats/states (the rate and velocity effects of
  states), objects (`FrameDelta` and the `Sync` draw), monsters/stats (the speeds) where this plan answers them.
- **Done when:** the spec follows the template; every statement is tagged; it has the mode machine as a state diagram
  per unit type, the frame advance as pseudocode with its integer widths, the rate formula and the breakpoints derived
  from it as a function with worked examples from the run, the movement step as pseudocode; the architect's review
  passes. Merges after any open 0045 spec change to the same files (specs edited by two plans merge one at a time, the
  earlier plan's first).

### Phase 4 — Wiki page: animation and timing
- **Owner skill:** spec-writer
- **What:** `docs/wiki/animation.md` (ADR-0012) over the reviewed spec, with the reading-order row in the wiki
  index; combat and skills pages cross-linked.
- **Done when:** `based_on` dates current (gate W4); no claim of its own; the architect's review passes.

## Resources and limits

- **Harness:** at most **two harness lanes** at once across all plans, on **slots 1 and 2** (slot 0 is the owner's).
  Phase 2 takes **one** of them; it never runs while plan 0045·P2 holds both.
- **Static:** at most **two static lanes** at once across all plans, and at most **two headless Ghidra** at once,
  `-Xmx3G` each. Phase 1 holds one Ghidra for its three batches; P0 and P1b need none.
- **Replays:** the oracle-replacement re-checks of the kept logs and any heavy replay run under
  `systemd-run --user --scope -p MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (an estimate, not a measured figure): P0 one lane run; P1 three lane runs; P2 one to two lane runs of
  10–20 sessions.

## Open questions

- ~~**Movement's place.**~~ Decided 2026-10-25 (owner): a unit's speed and per-frame step are this plan's, the path it
  follows is phase (5)'s.
- **One row or two.** `anim/timing` and `anim/movement` are proposed; the spec-writer may merge them at P3.
- **Client-side timing.** The client's own animation clock, its interpolation and any display of attack speed are
  presentation and stay out (ADR-0014 § Time). A client function that computes the same rate separately counts as a
  second code path (evidence rule 1) only if Phase 1 finds one.
- **Two clients.** Party-wide rate auras on another player's unit stay `[I]` unless a later two-client run reaches them.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-25 — Drafted (architect, `lane/plans50`).** Status `proposed`, ahead of its gate (0045·P2) at the owner's
  request.
- **2026-10-25 — Approved (owner, via the orchestrator).** Approved as drafted, effective when plan 0045 Phase 2 is
  accepted; the movement split kept (speed here, the path in phase (5)); Phase 2 runs before plan 0046 Phase 2 on the
  harness; the 2026-10-25 run order of the [plans index](README.md#run-order-set-2026-10-25-plans-00380052) is current.
- **2026-10-27 — In effect (architect, at the plan 0045 Phase 2 part 1 review).** Plan 0045 Phase 2 part 1
  (`lane/p45h`, run:2026-10-25-skills) is accepted with fixes, with a part 2 filed for the models and sessions it
  lacked ([0045 log](0045-skills-missiles-machinery.md#implementation-log)). That acceptance is the one this plan's
  approval waited for: **Phases 0, 1 and 1b are open**. Phase 2 still waits for 0045·P3's review, which waits for 0045
  Phase 2 part 2's review.
- **2026-10-27 — Phase 1, batch P1.1 landed for review (reverser, `lane/p50a`, static, Ghidra copy `ghidra-p50a`).**
  [anim/0001](../findings/anim/0001-modes-frames.md) reads the mode machine, all `[I]`: the `animdata.d2` record by
  token, mode token and weapon class (with a built-in fallback of 2048 frames, speed 256, no events), the attack
  start-frame table (Amazon and Sorceress only), `UNIT_SetMode`/`UNIT_AnimInit` per unit type, the unit's frame fields
  (`re/types/game.h`, new `re/types/anim.h`), sequences (player tables in the image, `monseq` for monsters), the
  player and monster mode tables with their ends, and the event lists' order in a frame. **Surprise:** most server
  modes are not advanced frame by frame; `SUNIT_ScheduleModeEvents` queues the frame events (codes 1–4) and the mode
  end at the start, from the start frame, rate and length, and only monster every-frame modes advance with
  `UNIT_AnimAdvance`. The animation machine draws once (an object's start when `Sync` is 0). Second surprise: the
  monster frame event ignores a frame function's 2. 75 symbols (`anim/timing`); `tools/anim_scan.py` and the `stop@`
  root of `RngCallGraph.java`; outputs kept under `workspace/logs/anim/` (`p50a-manifest.sha256`). Archivist entry
  for the `animdata.d2`/`monseq`/token docs filed; review requested
  ([backlog](../backlog/2026-10-27-reverser-architect-review-lane-p50a-plan-0050-phase-1-batch.md)). P1.2 (rates:
  `UNIT_AnimSetRate`, already named) is next. The five data questions of Phase 0's survey (`lane/p50z`) are answered
  from the code in anim/0001 § 2.1.
