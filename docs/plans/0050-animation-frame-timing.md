# 0050 — Animation and frame timing: unit modes, frame counts, rates and breakpoints, movement speed (ADR-0014 phase 4)

> **Status:** approved 2026-10-25 (owner), in effect 2026-10-27 (plan 0045 Phase 2 part 1 accepted); P0 accepted 2026-10-27; P1 batches P1.1–P1.3 accepted with fixes 2026-10-27; P1b part 2 and P2 open (P2's gate, 0045·P3's review, open since 2026-10-27)
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
    - **and the Phase 0 surprises** (folded in at the P0 review, [log](#implementation-log)), each answered with its
      address or left open with the reason: (a) which record the lookup takes for the 29 duplicate names of
      [animdata](../formats/animdata.md#layout) (9 differ: `3DNUHTH`, `64A1HTH`, `64NUHTH`, `MINUHTH`, `VM*`); (b) for
      objects, whether the frame advance reads Objects `FrameCnt<k>`/`FrameDelta<k>` or the record's `frames`/`speed`
      (they agree in 1 173 and 609 of 1 483 modes, [Objects § Timing](../tables/Objects.md#timing-plan-0050-phase-0));
      (c) what a `monseq` step at or past its user's record frame count does (249 steps: `K9`, `OS`, `ST`); (d) where
      `Unit+0x4E` comes from, given that `monseq` events and the record's event bytes agree in 81 of 805 set steps and
      event 4 is only in `monseq` ([MonSeq](../tables/MonSeq.md#sequences)); (e) whether `eanimdata.d2` is read (no
      string names it).
  - **P1.2 rates:** the rate of each mode from the stats and the weapon: attack rate and IAS with the weapon's `speed`
    (one-handed, two-handed, dual wield, kick, throw), the skill rate terms (sequence skills, skills that raise or
    lower attack speed), cast rate with `MinimumCastingDelay`, hit-recovery rate, block rate, the caps and floors, the
    stat recompute that triggers a rate change (`UpdateAnimRate`) and whether a rate change applies to a mode in
    progress; monsters (MonStats speeds, the `fast` mod, the champion and unique bonuses, the difficulty terms if any);
    the **breakpoints** are derived from the formula and stated as a function, not copied; where the formula is a pure
    function, its cases are emulated (ADR-0015, ADR-0021) over the stock input range so the derived tables are
    checked against the binary; and anim/0001 § 10's class overrides re-read on the `.bin` rows (the
    [`SplGetModeChart` row-shift entry](../backlog/archive/2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md),
    folded at the `lane/a51f` review): the records classes 417, 543, 570, 705 and 709 take, and 418/544 named
    `shadowmaster`/`baalcrab`;
  - **P1.3 movement and the gates:** walk and run velocity (CharStats, MonStats, `MonStatsSpeeds` at load, stat 67 and
    the slowing states, `RunDrain`), `PathSetSpeed`, `PathVelocityStep` and the position advance per frame in its
    fixed-point units; then each gate: the frame the do function runs on (skills/0001 § 5), the attack's delivery
    frame (combat/0001 § 2), missile creation on the action frame, hit recovery (the get-hit mode and its length,
    `GetHitRoll`), knockback and stun lengths, the block mode's length, the skill `delay` against the animation, an
    object's operate frames; the get-hit and durability draws combat names;
    the hit class (`sub_0057CE30_HitClassPick`: which of Weapons `hit class`, MonStats2 `HitClass` and the packet's
    `+0x60` it starts from, and whether the server gates anything on it; [HitClass](../tables/HitClass.md#open-questions),
    folded in at the P0 review);
    - **and the `lane/a50t` review's two reads** ([log](#implementation-log)): what `MonStatsSpeeds` (anim/0002 § 3.5)
      writes as the walk base `+0x036` for a class with no walk record (the seven classic `9A` rows and the `E9` rows,
      [MonStats § Timing](../tables/MonStats.md#timing-plan-0050-phase-0) `[L]`), and whether the moving branch
      writes `+0x4C` for a `Velocity`-0 class in S1 (a path or none); and anim/0002's open question on a negative
      rate stat closed, citing [ItemStatCost § Timing](../tables/ItemStatCost.md#timing-plan-0050-phase-0)'s survey;
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
- **Boundary** (anim/0003 § 9, ruled at the P1.3 review, [log](#implementation-log)): **oracles** (ADR-0004,
  ADR-0021) are the mode request (plan 0045), the AI's command and its velocity block (plan 0052), the path plan (its
  points, the replan and the target revalidation's `PathPlan` calls, `0x00679720`; phase (5)), the collision test
  `0x0064FF90`'s result per crossed subtile, the catalogue speed writers of anim/0003 § 1 and the reschedules of
  anim/0001 § 7.1, and the client. **Modelled:** the speeds, the step, the snap and the collision walk's arithmetic
  (the halved increment, the 10-crossing exit), the run drain, the knockback point and its length, the gates of
  anim/0003 §§ 5–6, `GetHitRoll` with its draws, `PlayerModeAllowed`'s draw, the hit-class nibbles and the object
  operate end. **Log windows:** the step per frame of one unit per window (position before and after, `+0x7C`, the
  direction, the point index, `UnitMoveStep`'s return), not every unit every frame (ADR-0014 § Log volume);
  `COMBAT_GetHit` at entry (result bits, `+0x60`, total, max HP, the defender's seed) and the mode command it issues
  with the seed before and after `PlayerModeAllowed`; `PlrModeLeaveOk`'s result; object event 1.
- **Done when:** `run:YYYY-MM-DD-anim` reproduces with **0 mismatches** over at least (minimums are estimates,
  confirmed as estimates at the P1.3 review):
  - 1 500 player mode events across all seven classes, each with its start frame, its event frames and its end frame
    predicted: A1, A2 (or the class's second attack), kick, throw, cast, get-hit, block, walk and run, a sequence
    skill; at least 30 per class and mode the pilot can stage;
  - the rates: for each class, attacks at three or more IAS values on two weapon types, casts at three or more FCR
    breakpoints, get-hits at three or more FHR breakpoints, blocks at two or more FBR breakpoints, each at least 30
    events; a rate change in the middle of a mode (a stat change from an item swap or a state), if Phase 1 says it
    applies;
  - 500 monster mode events over at least 20 classes, a sequence monster (mode 14) and a `fast` champion among them;
  - **required (the P1.2 review ruling (g)):** a classic monster (class < 410, not `npc`) in an S1–S4 mode, its `+0x4C`
    at the moving rate from its walk base (anim/0002 § 3.4) and its schedule predicted, at least 30 events over two or
    more classes, one under a stat 67 change (a `fast` or champion mod, or a slowing state); and a class ≥ 410 monster
    in an S1–S4 mode at the default or attack rate, at least 30 events;
  - optional (the `lane/a50t` review ruling): a classic `9A` trap (326–330, 355 or 369) in S1, its `+0x036` and `+0x4C`
    logged and its schedule predicted, at least 30 events; it counts toward the classic classes above when its rate
    is the moving one. The two-frame records' lost event (`r ≥ 512`) is not a case: no stock source reaches it;
  - 100 object animation starts with the `Sync` draw predicted (and chained);
  - 200 movement windows (walk and run per class, monsters walking and running), positions per logged frame in a
    stated window, 50 under a slowing state;
  - **chaining (ADR-0014):** for every event kind that draws, at least 20 chained pairs; a kind with none keeps its
    draw-order claims at `[I]`;
  - **the oracle replacement:** plan 0045's skills run (its action frames), run:2026-10-16-combat and the plan 0047
    runs (their get-hit and block events) re-checked with the action frame and the get-hit length modelled where the
    logs hold what the model needs; the record names what could and could not be replaced;
  - the Phase 1b cases;
  - **the P1.3 review's cases** (minimums are estimates): 100 `GetHitRoll` calls with the band, the divisor and the
    draws predicted, at least 20 in each of the two drawing bands and over two or more hit classes with different
    divisors; 30 knockbacks (players and monsters, the end frame predicted); the run drain in the run windows above
    (stamina per frame, and a run that turns to a walk at 0 if the pilot can stage it); the first frame of an
    every-frame event queued during a frame's unit-list run (anim/0003's open question: it sets the first step of
    every moving mode and the monster knockback count), logged at 30 or more moving-mode starts; optional: 30
    `PlayerModeAllowed` draws under state 42 and 30 object operate ends (event 1). The step-product wrap
    (`v ≥ 32 768`) is not a case unless a stock source reaches it.

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
  lacked ([0045 log](done/0045-skills-missiles-machinery.md#implementation-log)). That acceptance is the one this plan's
  approval waited for: **Phases 0, 1 and 1b are open**. Phase 2 still waits for 0045·P3's review, which waits for 0045
  Phase 2 part 2's review.
- **2026-10-27 — Phase 0 landed (archivist, `lane/p50z`).** `animdata.d2` decoded and the timing columns documented;
  no Ghidra, no harness. What was produced:
  - [formats/animdata](../formats/animdata.md) and `tools/animdata.py` (`survey`, `dump`, `compare`, `dups`; gate
    survey `animdata`): 256 hash blocks (`u32` count + 160-byte records: `name` char[8], `frames` u32, `speed` u32,
    144 event bytes), every record in block `sum(name bytes) & 0xFF`, the file consumed exactly; layout `[C]`, meanings
    `[L]`. Copies: d2data 2 563 records, d2exp 3 558 (wins by the precedence, `[I]`), patch_d2 none; d2exp adds 973
    names and changes 4 values. Event bytes 1 ×433, 2 ×148, 3 ×4.
  - [cof](../formats/cof.md#animdatad2-against-the-cof-fields-data-only): for all 3 500 joined names the COF
    `frames_per_dir`, frame bytes and `rate` equal the record's `frames`, events and `speed` (data only).
  - [MonSeq](../tables/MonSeq.md) and [HitClass](../tables/HitClass.md) (new; layouts `monseq` 5 050 cells and
    `hitclass` 14 cells, 0 mismatches; `excel_layout` baseline regenerated: 71 tables, 951 693 cells, 0 unexplained).
  - § Timing in PlrMode, MonMode, ObjMode (the stale "phase (5)" lines rewritten), CharStats, MonStats, MonStats2,
    Weapons, Skills, States, ItemStatCost and Objects, each column with offset, width and range.
  - `tools/anim_survey.py` (gate survey `anim`): the token-to-record joins with their misses: players 755 of 756 names
    (`AMWK1HS` unjoined), monsters 5 109 flagged modes all joined (5 057 by `BaseW`, 52 by `HTH`), objects 1 483 of
    1 603 flagged modes (120 misses); the Skills `anim`/`monanim`/`seqnum` rows; the rate stats and their users; the 60
    `monseq` sequences with lengths and event steps.
  - **Surprises for Phase 1.1** (written here, not into its *Done when*, per the lane's instruction to keep this plan's
    edits to a log entry; the architect may fold them in): (a) 29 duplicate record names, 9 with different content
    (`3DNUHTH`, `64A1HTH`, `VM*`): which one the lookup takes; (b) for objects the table and the record disagree:
    `FrameCnt<k>` equals `frames` in 1 173 of 1 483 modes and `FrameDelta<k>` equals `speed` in 609 (0 in 421): which
    one the server's frame advance reads; (c) 249 `monseq` steps name a frame at or past the user's record (`K9`
    shadow warriors on 2-frame records, `OS`, `ST`); (d) `monseq` events agree with the record's event byte at the same
    frame in only 81 of the 805 steps where either is set; event 4 exists only in `monseq`; (e) `eanimdata.d2` (d2exp,
    3 531 records, a subset with equal values) is named by no string in `Game.exe`.
  - Merge order: after plan 0051 Phase 0 (already on main at the branch point, 0e3f501).
- **2026-10-27 — Phase 0 reviewed (architect, `lane/p50z`): accept with fixes.** `main` (0848879) merged into the
  lane first (the metrics conflict kept both sides; `backlog.py archive` moved nothing). Re-run under
  `systemd-run --user --scope -p MemoryMax=4G`: `animdata.py survey`, `anim_survey.py summary` and `excel_bin.py
  survey` print their baselines byte for byte (71 tables, 951 693 cells, 0 unexplained); the two `SURVEY` lines quoted
  in [formats/animdata](../formats/animdata.md#tools) equal the baselines. An independent parse of the merged file
  (256 blocks, 160-byte records, the size sum, `hash_bad=0`, event bytes 1 ×433, 2 ×148, 3 ×4, the four speed-0
  records) and `animdata.py compare` over the archive copies (d2data → d2exp: 973 names added, 3 frames and 1 speed
  changed; `eanimdata.d2` a 3 520-name subset with equal values; patch_d2-classic's copy has d2exp's hash) agree with
  the doc. Fixes (5), written into the documents:
  1. [formats/animdata](../formats/animdata.md#files): "`[L]` Nothing names it in `Game.exe`" split: the string check
     is `[C]` (`animdata` occurs, ASCII or UTF-16LE, only in `%s\AnimData.d2`), whether the file is read stays `[L]`.
  2. [formats/animdata](../formats/animdata.md#layout): "the six `VM*` names" lists five (`animdata.py dups`: 9
     differing names = `3DNUHTH`, `64A1HTH`, `64NUHTH`, `MINUHTH` + five `VM*`).
  3. [MonStats2 § Timing](../tables/MonStats2.md#timing-plan-0050-phase-0): the `m<mode>` row's `[C]` "every set bit
     names a record" scoped to the 603 records a MonStats row names; `diabloclone` and the five `uber*` rows have no
     `Code` to build a name from and were not checked.
  4. [Weapons § Timing](../tables/Weapons.md#timing-plan-0050-phase-0): `speed` "0 ×105 set" was the 105 blanks; no
     cell is set to 0 (10 values in 201 rows).
  5. Phase 1.3's *Done when* gains the hit class (HitClass's open question pointed there and was not in it).
  Rulings:
  - (a) **"d2exp wins by the precedence `[I]`" stands.** data/0002's precedence is `[I]`, and d2exp is opened by
    `MPQ_OpenCoreArchives` in every game; the string `%s\AnimData.d2` is at file offset `0x2EED5C`, which is VA
    `0x006EED5C` in `.rdata` (VA = offset + `0x400000`, objdump section map). Which code opens it stays Phase 1.1's.
  - (b) **The layout rows are `[C]`** by the data-format rule (every byte read, every check passing, three files);
    every meaning is `[L]` or carries a finding's `[I]` (skills/0001 § 5, combat/0001, data/0001, the reviewed specs
    for the base rate stats and the `Sync` draw), spot-checked against `re/symbols.csv`.
  - (c) **No game data dumped.** The § Timing tables are per-mode aggregates; HitClass's 14-row code list and MonSeq's
    six sample sequences are short illustrative rows; the full grids stay in the tools' output.
  - (d) **The five surprises are folded into P1.1's *Done when*** as one sub-item under P1.1 (lines added, none
    changed, so `lane/p50a` merges cleanly). Archivist rule 9 stands; when a prompt limits a lane's plan edits to the
    log, the lane lists them there and the review folds them, as here. Not counted as a lane fix.
- **2026-10-27 — P1b part 1: sources registered and claims staged, no verdicts (reverser, `lane/p50c`; no Ghidra, no
  harness, P1 work on other branches not read).** P1.2 and P1.3 have not run, so this part does only the blind half
  of Phase 1b; **part 2 (one verdict per claim against P1.2 and P1.3) runs after P1.3's review.** Registered in
  [sources](../sources.md), each with the version it describes: `maxroll-d2r-breakpoints` and
  `maxroll-d2r-attack-speed` (D2R, patch 2.4 and later), `basin-wiki-animation` (LoD 1.10+ with D2R notes, nine
  pages by revision), `basin-runwalk-thread` (February 2003, 1.09 era; Hammerman's two in-memory offsets of that
  build read in prose, not copied, not used), `basin-movement-clarification` (2012, 1.13 era), `pd-breakpoints` (no
  patch named, classic-era tables); not read: `lurker-movement-thread` (HTTP 409/406) and `gustafsson-movement-speed`
  (archive refused). No page with game code was met. Staged in [anim/leads](../findings/anim/leads.md): **61
  claims**, all `[L]`, each with source, version and the batch that decides it: rates R 5, attack A 15, cast C 7,
  delays D 5, hit recovery, stun and knockback H 10, block B 5, movement M 14 (`grep -cE` in its § 11). Seven
  conflicts are named in the rows (A1/A2 the `− 1` inside or outside the ceiling; C2 against C3; D1/D2 the delay from
  the action frame or after the cast; H4 three "one-handed swinging" lists; H5/H6 the hit-recovery threshold; M6/M7
  Slows Target's speed effect; M12/M13 Charge speed). **Kept check** `tools/anim_leads_check.py` (`331eb0f0…`): the
  sources' FCR, FHR and FBR tables against their own formula, 39 cases × 2 sources, 70 agree, 8 differ (the Druid's
  three forms and the Necromancer's FCR, reproduced only with bases 15 and 16), output
  `workspace/logs/anim-leads/p50c-leads-check.txt` (`b185e780…`, `manifest.sha256`); a check of community claims
  against each other, not of the game. **Gaps** (no lead found): monster frames and rates, the `fast` mod, object
  operate frames, `monseq` sequences; part 2 records them "no lead". The `animdata.d2` format guides are left to
  Phase 0. Review request: [backlog](../backlog/archive/2026-10-27-reverser-architect-review-plan-0050-p1b-part-1.md).
- **2026-10-27 — P1b part 1 reviewed: accept with fixes (architect, `lane/p50c` review; `main` merged first, ledger
  rows kept on both sides; no Ghidra, no harness).** Re-run: `python3 -I tools/anim_leads_check.py` (`331eb0f0…`)
  byte-identical to the kept output (`b185e780…`, `sha256sum -c manifest.sha256` OK), `SUMMARY … agree=70 differ=8
  alt_base_found=8`, the 8 ALT lines the Druid's three forms (base 15) and the Necromancer (base 16) in both sources;
  case counts 12 FCR + 16 FHR + 11 FBR = 39 as C3, H3 and B3 state. The § 11 grep gives 61 (R 5, A 15, C 7, D 5, H 10,
  B 5, M 14); every row `[L]` with an empty verdict, no `[C]` or `[I]` in the file, nothing promoted. No hex offset in
  the commit; the longest quote is 66 characters (the Basin's "required EIAS" formula); the six registry rows are
  summaries. **Rulings.** (a) **Hammerman's post:** within the sources policy. ADR-0001 names offset lists among the
  community documentation usable as leads; what it bars is decompiled or reconstructed code, the reason
  `pk-pathfinding-thread` is rejected (structs and code that walks them). Two field offsets named in prose are an
  offset list of a 1.09 build, which ADR-0001 also says does not transfer; `src:basin-runwalk-thread` stays a
  registered lead, the offsets stay uncopied and unused, and M11 (the mode factors, no offset) stays staged. (b) **The
  blind rule:** the header note is the control, widened and made checkable; the file is not withheld. A lane must
  merge `main`, the claims restate public pages any lane could fetch, and the blind-first rule is about order, which a
  log statement and the reviewer can check; keeping the file on an unmerged branch would strand part 2's bookkeeping.
  The rule now covers every Phase 1 batch, P1.1 included (R1, A3 and A4 are frame-advance and start-frame claims, now
  batched P1.1 too): a P1 lane reads only § 1 before filing, says "leads not read before filing" in its log entry, and
  its review checks that the finding cites no leads row and states no community number or formula without an address.
  (c) **Version scope:** each claim now carries a **Version** column from its sources; 19 rows are **D2R 2.4+ only**
  and 5 **1.09 only**. A code disagreement on such a row is written `contradicted (version: D2R)` or `(version: 1.09)`
  and is not a community error, and it stays a required Phase 2 case when reachable on stock data (the run settles
  1.14d; the version note does not excuse the code reading). (d) A4 and D4 are decided from the P0 survey in part 2,
  as staged. **Fixes (3), written into `anim/leads`:** (1) the Version column and its § 1, § 2 and § 11 text, with
  the kept greps (19, 5); (2) § 2's "the breakpoint tables are not copied" corrected: they are not in the file but are
  transcribed as numbers into the check; (3) the blind rule widened to P1.1 with the log statement and review check,
  and P1.1 added to R1, A3 and A4's batch (the plan's own Phase 1b text named only P1.2 and P1.3; the gap was the
  plan's). Ledger: accept with fixes, 3 (omission 2, misread 1). The review request is closed. Part 2 (verdicts) runs
  after P1.3's review.
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
  ([backlog](../backlog/archive/2026-10-27-reverser-architect-review-lane-p50a-plan-0050-phase-1-batch.md)). P1.2 (rates:
  `UNIT_AnimSetRate`, already named) is next. The five data questions of Phase 0's survey (`lane/p50z`) are answered
  from the code in anim/0001 § 2.1.

- **2026-10-27 — Phase 1, batch P1.1 reviewed: accept with fixes (architect, `lane/p50a` review; static, objdump
  only, no Ghidra, no harness).** `main` merged into the lane twice (0e3f501 → 0848879, then d24d839 with P0 and P1b
  part 1; ledger and log conflicts kept both sides; `backlog.py archive` moved nothing). Judged against the plan as on
  `main` **with the P0 fold** (P1.1's sub-item (a)–(e), landed with `lane/p50z`). Re-run: `tools/anim_scan.py` (scan
  and rows) byte-identical to the kept outputs (`d6679d5f…`, `8e5d2636…`); `sha256sum -c p50a-manifest.sha256` OK
  (6 files); tool hashes equal `p50a-commands.txt`'s. objdump of the pinned `Game.exe`: `SUNIT_ScheduleModeEvents`
  (`0x005539B0`) as § 7 states (one `T` step per `acc < L` pass, the inner scan to `acc >> 8` capped at `0x90`, the
  jump table `0x00553AFC` 1, 2, 4 → `0x00553A82` with the running index, 3 → `0x00553A9A` with 0, the end at `T + N + 1`
  or `T + 2`, `+0x44 = T << 8`), so `T + max(2, ⌈(L − 256·S)/r⌉)` for `L > 256·S` holds; `UNIT_AnimAdvance`
  (`0x00623E00`) as § 8 (the 16-bit signed `0x100` test, the wrap restarting the scan at 0 and the position at the
  start frame, the last event byte winning); its 11 call sites, 7 monster (`0x005A736C`, `0x005A74AC`, three in
  `MonAttackFrame`, `0x005A863C`, `0x005A8720`) and 4 client; `UNIT_AnimSetRate` calls neither the event queue nor
  the cancel; the fallback `+0x40C = 0x800`, `+0x410 = 0x100` returned as `+0x404`; `ANIMDATA_Find`'s forward walk
  returning the first match; the image's one `AnimData` string at `0x006EED5C` and no `eanimdata`; the five runners in
  the order missile, player, monster, object, item, every-frame list then slot; `0x005A7BA0` calling the frame
  function with ECX/EDX only and `sub_00541060_MonEventsRun` not testing the result (`0x005410C4`); the
  `PlrModeSkillFrame` write of `b` at `0x00580482`; `g_MonModeRecords`, `g_MonModePerFrame` and `g_MonModeEndDirect`
  dumped and equal to § 10. 75 rows, all `I`, `anim/timing`; no duplicate address or name after both merges; no `[C]`
  and no raise. `RngCallGraph.java`: `stop@` is parsed before roots and only consulted for callees, so a call without
  it runs as before (backward-compatible). **Blind check (the `lane/p50c` ruling, applied on P1.1's behalf):** the
  finding cites no [anim/leads](../findings/anim/leads.md) row and states no community number or formula without an
  address; the lane ran before the file existed on `main` and was told not to read `lane/p50c` — **leads not read
  before filing**. Not a lane fix.
  **Fixes (7), written into the documents:** (1) anim/0001 summary and § 10: the generic S3 (row 10, `schedule` 0)
  queues no event, so its frame function and "S3 to S4" are run by nothing read; open question 1 widened; (2)
  `re/types/anim.h` `MonModeRec.pfnFrame` "2 ends the mode" → the return is not read; (3) `re/types/game.h` bit 19's
  "§ 4" → § 10; (4) `anim.h`'s `MON_ModeEveryFrame` → `sub_005A6B10_MonModeEveryFrame`; (5) § 5 and skills/0001's dated
  note: `PlrModeSkillFrame` writes the index only with a used skill (`0x00580475` returns 2 first); (6) the Draws
  summary names the 3 unfollowed indirect calls, § 11 the mode graph's 118; (7) § 6: the frame function gets no code
  or index, the return's path to `MonEventsRun`, the object runner `sub_00541160_ObjEventsRun`, and the no-record
  fallback `0x005A7B30`. Not counted (left stale by the P0 and P1b merges): the header's and *Data touched*'s "no
  format doc", § 2.1's "under review", open question 4, *Leads used* (now naming R1, A3, A4), and a dated note on the
  archivist entry (items 1–2 met by P0; 3–4 remain).
  **Rulings.** (a) **Two clocks** stand `[I]`. Phase 2 logs a scheduled mode at `SUNIT_ScheduleModeEvents` (the
  queued list, once per start) and the kind 0/1 dispatch, and `UNIT_AnimAdvance` only in windows for every-frame
  monsters; P1.2 answers "does a rate change apply to a mode in progress" as two cases: a scheduled mode keeps its
  events (bar the § 7.1 reschedules), an every-frame monster's next advance takes the new rate (P1.2 to read).
  (b) **The ignored 2** (and the generic S3) **stay an open question of anim/0001 for Phase 2 to log**, not routed:
  what ends the mode is the AI command if anything, which § 12 already names as plan 0052's oracle; Phase 2 records
  the mode's end event per every-frame attack it meets, and plan 0052 takes it over only if the log shows the AI
  command. (c) **The RNG scope** is accepted as stated: "only draw" holds over the 171-function graph with its stops
  and 3 unfollowed callbacks (stats/states'), now in the text; the mode-function graph stays reported by entry, its
  draws belong to the subsystems named; `PlayerModeAllowed`'s draw is P1.3's gate. (d) The archivist entry stays
  open for items 3–4, non-blocking. (e) The dated notes in skills/0001 and skills/0002 stand (0001 scoped by fix 5).
  (f) **§ 2.1 meets the P0 fold** (a)–(e), each `[I]` with its address: first record in the block wins, objects
  never read their record on the server, a sequence's frame and event come from the sequence record, only
  `%s\AnimData.d2` is loaded. Ledger: lane row filled (usage from the orchestrator), accept with fixes, 7 (misread 2,
  omission 2, overclaim 1, wrong anchor 1, symbol clash 1). The review request is closed. **P1.2 may start** once this
  lane is merged into `main`.
- **2026-10-27 — Archivist entry items 3–4 folded (archivist, `lane/a51f`; no Ghidra, no harness).** The anim/0001
  readers entry ([archive](../backlog/archive/2026-10-27-reverser-archivist-p50a-animdata-monseq-readers.md)), whose
  items 1–2 Phase 0 had met:
  - Item 3: [PlrType](../tables/PlrType.md) and [ObjType](../tables/ObjType.md) (new; layouts `plrtype` 14 cells and
    `objtype` 1 146 cells, 0 mismatches; the ObjMode shape, `Token` at `+0x020`, 16 zero bytes; `excel_layout`
    baseline regenerated: 73 tables, 952 853 cells, 0 unexplained). The token's use `[I]` from anim/0001 § 2.
  - Item 4: anim/0001 linked from the § Timing notes of PlrMode, MonMode, ObjMode, MonStats2 (`compositeDeath`,
    `*mv`, `m<mode>` under a shape-shift), MonStats (`SplGetModeChart`, `SplEndGeneric`, `SplEndDeath`, `aidel`;
    the old `aidel` scope note replaced), Objects (`FrameCnt`, `Start`, `FrameDelta`, `Sync`: the server's object
    frame fields come from the table, the old `[L]` answered) and Skills (`seqnum`, `durability`, `interrupt`; the
    `seqnum` `[L]` answered). Tags are the finding's.
  - `tools/anim_survey.py` gains the finding's rules as counts (anim baseline regenerated, 60 keys):
    `mon_rule_miss=0` (by the game's monster name, `hth` in DT/DD without `compositeDeath`, every flagged mode outside
    `xx` has a record) and `obj_objtype_token_ne=16`, `obj_objtype_hit=1491` (the ObjType token differs from the
    Objects `Token` in 16 records; under it 1 491 of the 1 603 flagged object modes have a record, against 1 483).
  - Surprise, for the reverser ([backlog](../backlog/archive/2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md)):
    anim/0001 § 10's `SplGetModeChart` data is one row off from record 410 on (`anim_scan.py rows` keeps the
    `Expansion` row). By the `.bin` all ten override classes have the column set, so the five branches § 10 calls
    unreached (417, 543, 570, 705, 709) are reached, and 418/544 are `shadowmaster`/`baalcrab`. MonStats § Timing
    states the data and leaves those branches `[L]`. For P1.2's *Done when*: re-check § 10 once that entry is answered.
- **2026-10-27 — Archivist entry items 3–4 reviewed (architect, `lane/a51f` at `727653f`): accept with fixes (3).**
  `main` `e88e8e2` merged first (one conflict, `metrics.md`, both sides kept; `backlog.py archive` a no-op). Both
  surveys re-run under `MemoryMax=4G` reproduce their baselines (`excel_layout` 73 tables, `plrtype_cells=14`,
  `objtype_cells=1146`, 0 bad; `anim` 60 keys with `mon_rule_miss=0`, `obj_objtype_token_ne=16`,
  `obj_objtype_hit=1491`). Rulings:
  (a) **The row shift holds.** Read on `monstats.bin` (424-byte records, `+0x1A5`): 20 records have
  `SplGetModeChart` 1, all ten switch classes among them (243, 333, 403, 417, 418, 543, 544, 570, 705, 709), and
  the `.txt` read without dropping the `Expansion` line gives `deathsentry`, `shadowwarrior`, `ancientbarb3`,
  `baalthrone`, `injuredbarb3`, `ubermephisto` and `uberduriel` blank or set exactly as § 10 reports. The entry to
  the reverser stands; MonStats § Timing's `[C]` data and `[L]` branches are right. Folded into P1.2's item list
  (§ Phase 1), as the archivist's log asked.
  (b) **The new tables.** PlrType and ObjType are layout-complete; their token use is `[I]` from anim/0001 § 2
  (`0x0065B480`, `0x0065B570` in its *Data touched*; record sizes `0x0065AE26`/`0x0065B216` in data/0001 § 4).
  ObjType's record-*k* pairing is data `[C]` with the code half `[L]`, which is right. Three illustrative rows each;
  no dump. The rule count models KB's `GH` token implicitly: `monmode.bin` row 13 already stores `GH`, so the
  remap is a no-op on stock data (checked: 0 misses with it applied).
  (c) **Spot-checks of the seven Timing notes against anim/0001 § 2, § 3, § 5, § 9, § 10 and § 11:** the
  `SplEndGeneric`/`SplEndDeath` counts (27; 8 + 1) and the disguise rows (63, 93, 119, 139, 140, 176, 177, on
  `states.bin` byte `+0x12` bit 0) recomputed. Fixes: (1) MonStats `aidel`: the re-queue's condition (the next AI
  event not later than now) and the 18 blank rows added (omission); (2) PlrMode: row 19's get-hit branch of
  `PlayerModeEnd`, not reached from its move frame (§ 9.1), added (omission); (3) the States `disguise` struck
  question linked `#columns` for § Flag bits; now `#flag-bits-0x010-40-bits-bit-i--byte-0x010--i8-bit-i-mod-8` there, in the plan 0051 log and in the closed
  States entry (wrong anchor).
  (d) **The gate's slug.** Not a gate bug: `gh_slug` gives the heading GitHub's anchor (`*i*` is emphasis, `+`,
  `=` and `/` drop), the gate resolves it, and the gate stays green with the precise link. No entry.
  (e) anim/0001's open question on the token tables is the reverser's to strike; it rides with the row-shift entry.
  Ledger: lane row filled (usage from the orchestrator), review row added with "—" usage. The review request is
  closed. P1.2 is not held.
- **2026-10-27 — Phase 1, batch P1.2 landed for review (reverser, `lane/p50b`, static, Ghidra copy `ghidra-p50b`;
  `main` merged at 51757b68 before filing; leads not read before filing, only `anim/leads` § 1).**
  [anim/0002](../findings/anim/0002-rates.md) reads `UNIT_AnimSetRate`: nine branches chosen by display type and mode
  through three image tables (player; monster class < 410; ≥ 410): cast `spd · min(100 + B_FCR, 175) / 100`; block
  `max(1, spd · (B_FBR + 50 or 100 under Holy Shield) / 100)`; get-hit `spd · (B_FHR + 50) / 100`; knockback the walk
  base; moving `vbase · max(B_FRW + stat 67, 25) / 100` (signed) with the path speed; attack `base · clamp(B_IAS + stat
  68 + dual-wield mean − 30 in a player sequence, 15, 175) / 100`, the base being a shapeshift form's human-equivalent
  speed under `meleeonly`; fixed (death) `spd`; default `spd · clamp(stat 69, 15, 175) / 100`; floor 0, cap 0x7FFF;
  only cast and attack write the sequence step. The bonus `B = k s / (k + s)` (k 120; 150 for FRW) is `[C]` as an
  ADR-0015 map (3 413 cases). **Ruling (a)'s two cases:** a scheduled mode keeps its queued events (`[I]`: no queue or
  cancel among the 19 callees; only the § 7.1 reschedules rebuild); an every-frame monster's next advance takes the new
  rate (`[C]` as a map, 1 200 emulated advance pairs, run:2026-10-27-anim-rates-emu). 31 call sites (24 server, 7
  client); `UpdateAnimRate` is tested by the server only in do 30, its helper, do 61 and do 71; no stat write hooks the
  rate. No difficulty term; `MinimumCastingDelay` is not a column of this data. Breakpoints stated as a function
  (§ 7), with the closed forms checked against brute force over every stock record pair. Surprises: a classic
  monster's S1–S4 always take the moving rate; a negative factor (FCR ≤ −55, FHR or FBR ≤ −36) wraps to the maximum
  rate. 22 symbols, `tools/anim_rates.py`, outputs `workspace/logs/anim/p50b-*` (`p50b-manifest.sha256`). Also the
  folded row-shift item: anim/0001 § 10 corrected (all ten override classes reached; 418 `shadowmaster`, 544
  `baalcrab`), `anim_scan.py rows` fixed with a `.bin` read, the archivist entry closed
  ([archive](../backlog/archive/2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md)), the token-table
  open question struck. Review requested
  ([backlog](../backlog/archive/2026-10-27-reverser-architect-review-lane-p50b-plan-0050-phase-1-batch.md)).
- **2026-10-27 — Phase 1, batch P1.2 reviewed (architect, `lane/p50b` at `85b6b3a2`; static, objdump, no Ghidra
  decompile, no harness): accept with fixes (6).** `main` `450accc9` merged first (one conflict, `metrics.md`, both
  sides kept; `backlog.py archive` a no-op). Checks: `p50b-manifest.sha256` (`588b438c…`, 27 lines) passes
  `sha256sum -c`; the case files regenerate byte-identical; both families re-emulated under
  `systemd-run --user --scope -p MemoryMax=4G` on `ghidra-p50b` (`-Xmx3G`): `bonus.out` and `advance.out` byte-identical,
  `check.txt` byte-identical (`3566d9da…`, bonus 3 413 and advance 2 400 cases, 0 bad). **Negative control:** one bonus
  output raised by 1 (case 500, `s` 380: 92 for 91) and one advance frame raised by 1 (case 7: 99 for 98) give
  `bad=1` in each family, `SCAN check bad=2`. `tables`, `uar`, `data` and `bp` re-run byte-identical (`CHECK … bad=0`
  ×3; the SOSCHTH FCR 9 and 200 rows re-derived by hand: `B` 8 and 75, lengths 13 and 8); `calls` re-runs with the same
  31 sites and differs only in five enclosing-symbol labels, the lane's own new rows (the kept output predates them).
  Objdump: the three mode-class tables and `g_AnimRateBonus` dumped and equal to § 1 and § 2; `AnimRateBonus`'s
  `imul; cdq; idiv` and its `type == 1 && s ≠ 0` test; cast, get-hit, block, attack and default divide unsigned
  (`mul 0x51EB851F; shr 5`), moving and its path speed signed (`imul; sar 5` plus the sign bit); cast capped only
  above, attack and default clamped 15..175, moving floored at 25; the `0x7FFF` cap (`cmp; jl`) and the floor on every
  branch; state `0x65` (101) giving 100 for 50 in block; the 31 call sites (`call`/`jmp 0x623f50` over `.text`, no
  other reference); `UpdateAnimRate`: no immediate test of ItemStatCost `+0x5` bit 1 outside the 14 mask-byte sites;
  the `SUNIT_ScheduleModeEvents` first-step test (`0x00553A16`, `jge` past the event loop) behind "no frame event"; the
  `MonModeRecord` jump tables behind § 10's correction. Symbols: 22 rows, all `I`, no duplicate address, none raised
  (review-fix 14). **Blind rule:** the finding cites no `anim/leads` row and no community number without an address;
  the log above says "leads not read before filing". Met.
  **Fixes (6), written into the documents:** (1) anim/0002 § 1: block too goes through the floor and cap (it joins at
  `0x00624369`), not "every branch but block" (misread); (2) the summary's `[C]` bonus: `s` named by the call
  (`sub_00625500_UnitGetStat(unit, stat, 0)`), "the unit's full stat" left as the § 2 reading `[I]` (overclaim,
  a meaning inside a map `[C]`); (3) § 5 `UpdateAnimRate`: the other nine sites are 2 MonStats2, 2 Missiles, 2 Skills,
  1 local and 2 unidentified client records, not "MonStats2, Missiles, Skills or MonStats2-local" (miscount); (4) § 5:
  the second `+0x4C` writer `0x00621780` (17 sites, 16 client, one server on a missile in
  `sub_005CC2E0_InfernoMissileRange`), also in anim/0001 § 1's field table (omission); (5) § 3.2: under Holy Shield
  the block factor wraps from FBR −55, not −36 (omission); (6) the review request's "26 lines" for the manifest's 27
  (miscount).
  **Rulings.** (a) The bonus `[C]` stands as an ADR-0015 map within its boundary (`s = −k` and the role of
  `UnitGetStat` outside it); no symbol is raised by it. (b) **Ruling (a)'s two cases are answered:** a scheduled mode
  keeps its queued events `[I]` (no queue or cancel among the 19 direct callees, rechecked; the helpers below them are
  the lane's reading, so `[I]` is the right tag); `UNIT_AnimAdvance` taking the rate at each call is `[C]` as a map (1 114 of 1 120 changed
  pairs separate it from the old rate); that the every-frame monster's next advance then runs at the new rate stays
  `[I]` (the per-frame call is anim/0001 § 10's reading). Phase 2 keeps its "rate change in the middle of a mode" case.
  (c) The breakpoint function is a check of the algebra only, as stated; it raises nothing. (d) **Surprise: a classic
  monster's S1–S4 take the moving rate** (walk base `+0x36`, factor floored at 25 and uncapped, the record's speed
  unused, and no write without a path). It holds on the tables and the `0x19A` tests; it is a **Phase 2 required
  case**, now in Phase 2's *Done when*: ruling (g) below. (e) **Surprise: negative factors wrap to the maximum
  rate.** It holds on the unsigned divides (cast, get-hit, block, attack and default; moving is signed and floored at
  25). Not a required case: whether a stock source reaches FCR ≤ −55 or FHR/FBR ≤ −36 is unsurveyed; the survey goes to
  the archivist (entry below, item 2); a reachable source becomes a Phase 2 case then. (f) **Surprise: no frame
  event when `r ≥ 256 (F − S)`.** It holds on `0x00553A16`. Not a required case for players: the start frames (1 or 2)
  are only those of player A1/A2 (anim/0001 § 4), and over the 568 stock records with an event 1–4 none reaches it at
  a factor ≤ 175 with `S` 0 or 2 (`S` 1: only 2-frame monster records, whose start is 0); review computation
  `noev2.py` over `animdata.d2` (scratch, `e1124ff6…`, output `4691c9ec…`). The one stock path left is (d)'s uncapped
  classic-monster S1/S2 on the 2-frame records `K9S1HTH`, `K9S2HTH`, `E9S2HTH` (event at frame 1, `r ≥ 512` needed):
  the archivist names their classes (item 3), and ruling (g)'s case covers it if one reaches. (g) Phase 2 required
  case: a classic monster (< 410, not `npc`) in S1–S4 at the moving rate, 30 events over two or more classes, one under
  a stat 67 change, and a class ≥ 410 monster in S1–S4 at the default or attack rate, 30 events. (h) **The MonStats
  § Timing `[L]` on the five branches** is the archivist's:
  [entry](../backlog/archive/2026-10-27-architect-archivist-p50b-monstats-timing-branches-and-rate-stat-minima.md) (item 1,
  with items 2–3 above), non-blocking. (i) The row-shift fix holds: anim/0001 § 10's ten classes match the two
  byte-indexed jump tables (`0x005A79C4`, `0x005A7A80`) and `OVRBIN`; the archivist entry's closure stands.
  Ledger: lane row filled (usage from the orchestrator), accept with fixes, 6 (miscount 2, omission 2, overclaim 1,
  misread 1); review row added with "—" usage. The review request is closed
  ([archive](../backlog/archive/2026-10-27-reverser-architect-review-lane-p50b-plan-0050-phase-1-batch.md)).
  **P1.3 may start** once this lane is merged into `main`.
- **2026-10-27 — the P1.2 review's archivist entry folded (archivist, `lane/a50t`; no Ghidra, no harness).**
  [Entry](../backlog/archive/2026-10-27-architect-archivist-p50b-monstats-timing-branches-and-rate-stat-minima.md).
  `tools/anim_survey.py` gains the sections `ratemin` and `twoframe` (baseline `tools/gate/baselines/anim.txt`
  regenerated by rerunning `summary`: the six `rate_src_*` and four `twoframe_*` keys are new, every old key unchanged).
  (1) [MonStats § Timing](../tables/MonStats.md#timing-plan-0050-phase-0): the `SplGetModeChart` `[L]` is replaced by
  anim/0001 § 10's per-class reading `[I]`. (2) **No stock source makes a rate-bonus stat negative** `[C]`
  ([ItemStatCost § Timing](../tables/ItemStatCost.md#timing-plan-0050-phase-0)): 353 property blocks over the item
  tables, cubemain and monprop write 93, 96, 99, 102 or 105, all with `min`/`max` ≥ 3 (lowest: FRW 3 on *of Inertia*);
  no Skills, States, Misc or `op stat` cell names one of the five. So FCR ≤ −55, FHR/FBR ≤ −36, FBR ≤ −55 under Holy
  Shield and `s = −k` are not reached by stock data: no Phase 2 case from ruling (e). (3) The `K9`/`E9` rows
  ([MonStats § Timing](../tables/MonStats.md#timing-plan-0050-phase-0) table): of the classic classes (< 410) only 332
  `invisospawner` (`mS1`, `S1mv` 0, `Velocity` 0, walk record `K9WLHTH` speed 256) reaches one of the three records
  (`K9S1HTH`); 153 `hellmeteor` has `K9` but no S mode, and no `E9` row is below 410 (410 `wakeofdestruction` and 415
  `infernosentry` are the first). At `vbase` 256 `r ≥ 512` needs `B_FRW + stat 67 ≥ 200` against the 75 a `Velocity`-0
  monster keeps. **Surprise for ruling (f)/(g):** the review's three records miss four more two-frame S records with
  an event: `K9S3HTH`, `K9S4HTH` (event at frame 1; no classic row flags S3/S4) and `9AS1HTH`, `9AS2HTH` (event 2 at
  **frame 0**, which also fires nothing at `r ≥ 256 (F − S)`): seven classic `9A` rows (traps 326–330, 369 and 355
  `seventombs`) flag `mS1` (327, 328 also `mS2`), all `Velocity` 0 with no walk record, so their walk base is what the
  load reads for a missing record (not read, `[L]` in the table doc). For ruling (g)'s Phase 2 case, if the architect
  wants it: `invisospawner` S1 and a `9A` trap S1, with the stat 67 they carry. anim/0002 open question 3 is answered
  by the ItemStatCost bullet (the reverser's to close in the finding).
- **2026-10-27 — `lane/a50t` reviewed (architect): accept with fixes (3).** `main` merged first (`062bc473`, the ledger
  conflict kept both sides; `backlog.py archive` clean). Static only (no harness, no Ghidra). `anim_survey.py summary`
  reproduces `tools/gate/baselines/anim.txt` key for key; `ratemin` and `twoframe` rerun. A review script of its own over
  the excel `.txt` files (scratch, not kept) gives the same: 15 property codes write the five stats, 353 blocks (uniqueitems
  192, runes 50, setitems 53, magicsuffix 37, sets 10, cubemain 4, monprop 4, gems 3), none negative or non-integer, the
  lowest 3 (*of Inertia* `move1`). No cell outside `itemstatcost`/`properties` names one of the five. The 24 `K9`/`E9`/`9A`
  rows, their `m<mode>` bits, `*mv` bits and `Velocity` match the MonStats table row for row. Note that
  the survey's row numbers skip the `Expansion` marker row (*Stormchaser* is record 226).
  `python3 -I tools/test_d2s.py`: 47 tests, the two new ones pass, and the two failures already on `main` remain.
  **Rulings.** (a) Item 1 stands: the `SplGetModeChart` `[I]` is anim/0001 § 10's reading, class for class.
  (b) Item 2's `[C]` stands for the data (the counts and minima); its table's "factor < 0" and "divide fault" columns
  quote anim/0002 § 2 and § 3.1–3.2, and the bullet's step to "no stock combination" is `[I]` as written. Ruling (e)
  gets no Phase 2 case. (c) **The item 3 surprise does not add a required case.** Losing a two-frame record's event
  needs `r ≥ 512`: at walk base 256 that is `B_FRW + stat 67 ≥ 200`. A `Velocity`-0 class keeps the new-monster
  75 (the `champion`/`fast` terms need `Velocity` > 0), and no stock monprop block writes stat 96. So no stock
  source reaches it, which is the same outcome as ruling (f). **A `9A` trap's S1 is a Phase 2 optional case** (now in
  *Done when*), for its run-time `+0x036`/`+0x4C`. The `invisospawner` is not a case: its walk base is the `K9WLHTH`
  record, which leaves nothing to settle. (d) **Two static reads are now in P1.3's *Done when*:** the walk base
  `MonStatsSpeeds` gives a class with no walk record (MonStats § Timing's `[L]`), with the moving branch's write for a
  `Velocity`-0 class in S1, and closing anim/0002's open question on a negative rate stat. The lane had left these as
  "the reverser's to close" with no route. (e) The 0045 part 2 links match their findings: skills/0001 § 18 and
  monsters/0004 § 9 (26 425 / 26 383, mask `0x40 + e` at `0x005A51D7`), and skills/0002 § 12 (271 `blaze` at level 2,
  `25 · 2 + 90` = 140). (f) The d2s keys are opt-in and default off, and each refusal path is tested. The two old
  `test_d2s.py` failures are not this lane's and are not an architect fix: each missing `RECIPE_BASES` row needs a
  base save and a built hash. They are routed:
  [archivist entry](../backlog/2026-10-27-architect-archivist-test-d2s-recipe-bases-and-mp-saves-pin.md). The 13
  recipes are three plan 0051 P1a mp recipes and ten `skills-*` recipes; `travel-tab2` is not one.
  **Fixes:** the Missiles `VelLev` row gains the review note that a level-1 `spike1` separates the term, with its C2
  entry (omission); the P1.3 reads of ruling (d) (omission); the request's `travel-tab2` (misread, in the request only).
  No game data is dumped: the new tables give row ids, names and counts. The review request is closed. Ledger: lane row
  filled (usage from the orchestrator), review row added with "—" usage.
- **2026-10-27 — Phase 1, batch P1.3 landed for review (reverser, `lane/p50d`, static, Ghidra copy `ghidra-p50d`;
  no harness, no emulation; leads not read before filing, only `anim/leads` § 1).**
  [anim/0003](../findings/anim/0003-movement-gates.md) reads movement and the gates, all `[I]`: the path speed
  `(pbase · max(B_FRW + stat 67, 25)) / 100` with `pbase` = `WalkVelocity << 8` or MonStats `Velocity << 8` (no mode
  argument, so a monster runs at its walk base unless the AI's command carries a velocity); the player's run as a
  mode-scoped stat-67 list (+50 on stock data); the per-frame step `(d · ((v · 0x400) >> 6)) >> 12` (`v / 16`
  subtiles per frame on an axis: walk 0.375, run 0.5625, knockback 1), the point snap, the collision walk and the
  stop; no acceleration for units; the run drain; knockback (planner type 8, `n = (+0x90 >> 1) + 1` subtiles, 3 or 6;
  a player's ends with the path, a monster's with its animation). The gates: the do, the attack's delivery, the
  `srvmissile` and the skill delay all start at the first code-1/2 event; hit recovery and block are their modes'
  schedules; `COMBAT_GetHit`'s dispatch per unit type; `PlrModeLeaveOk` (get-hit and block cannot be left but for
  death or neutral) and `PlayerModeAllowed` (P1.1 ruling (c): a get-hit during a non-interruptible skill never starts;
  under Concentration one `Range(player seed, 100)` against stat 164); the block animation's `lastblockframe` gate
  (`frame − stat 95 > ⌊stat 102 / 8⌋ + 15`); `GetHitRoll`'s 0–2 `RangePow2` on the defender's seed with the divisor by
  hit class; stun skips the roll; an object's operate mode 1 lasts `FrameCnt1` frames and turns to 2 without an
  animation start. **The hit class** (folded at P0): the packet's `+0x60`, low nibble from the attacker's weapon,
  MonStats2 or Missiles `HitClass`, an element nibble from a global counter in `COMBAT_GetHit`; the server gate found
  is `GetHitRoll`'s divisor. **Corrections:** anim/0001 § 1 (object `FrameCnt` is shifted << 8 at load, so its
  `+0x48` is 8.8) and combat/0001 § 6 (the delivery calls `UnitBaseHitClass`, not `HitClassPick`), as dated notes.
  23 symbols (12 `anim/movement`, 11 `anim/timing`), `re/types/anim.h` `PathMove`, `tools/anim_moves.py`, outputs
  `workspace/logs/anim/p50d-*` (`p50d-manifest.sha256`). Boundary recommendation in anim/0003 § 9. Archivist entry
  ([backlog](../backlog/2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md)); review
  requested ([backlog](../backlog/archive/2026-10-27-reverser-architect-review-lane-p50d-plan-0050-phase-1-batch.md));
  **Phase 1b part 2 runs after this review.**
  *Addendum (same lane, after merging `main` `ee8273b7` with the `lane/a50t` review's two reads):* anim/0003 § 1.1:
  `MonStatsSpeeds` reads the fallback record for a class with no walk record, so the `9A` and `E9` rows get walk base
  256 (run 128 below 410), and a `Velocity`-0 classic class in S1 has a path (`SUnitPathCreate`) and so `+0x4C` 192
  at `X` 75 with path speed 0; anim/0002's negative-rate-stat open question struck, citing ItemStatCost § Timing.
  Archivist entry item 3 added (the MonStats `[L]`).
- **2026-10-27 — Phase 1 batch P1.3 reviewed (architect, `lane/p50d` at `ae55f39a`; static, objdump, no Ghidra, no
  harness): accept with fixes (4).** `main` merged first (already up to date); `backlog.py archive` clean. The manifest
  passes `sha256sum -c` (7 lines, from `workspace/logs/anim/`); `tools/anim_moves.py` (`4f68385e…`) reruns `tables`,
  `calls` and `model` under `systemd-run --user --scope -p MemoryMax=4G` byte for byte, and the `p50d-monstatsspeeds.asm`
  command reproduces. Objdump checks: the step at 0x00650330–0x00650345 is `imul ecx, edi; sar 6; imul; sar 0xC` on
  both axes, signed, with `k = [ebp+0xC]` passed in `ECX` at 0x00650899 and the acceleration every fifth call
  (0x006502E6–0x00650320); the collision walk's 10-crossing exit at 0x0065022F–0x0065023D; `PathSetAccel`'s two call
  or jump sites (0x0059FDCC in `MissileCreate`, 0x004CD97E client) and no image pointer to it; the speed
  `(pbase · X) / 100` by `0x51EB851F` and `sar 5` with the sign fix (0x006241A9–0x006241C9); the drain
  (`RunDrain · 2`, `speed / 10 + 1` signed, stat 154 by `0xAE147AE1`, floor 1; 0x0057F283–0x0057F2F7);
  `GetHitRoll`'s jump table at 0x0057CBF8 decoded (1 → 16, 2 → 8, 3 → 16, 4 → 32, 5 → 64, 6 → 8, 7 → 16, 8 → 32,
  9 → 16, 10 → 8, 11 → 8, 12 → 16; above 12 → 16), the signed `D/2` and `D/4`, and two `RNG_RangePow2` calls on
  `def+0x20` with `n` 2 and 4 (`low & (n − 1)`, rng/0001: so the bands get hit with 3/8, 3/4, 1 as stated); the
  Concentration draw is `RNG_Range(player+0x20, 100)` at 0x0057EF7C against stat 164 of state 42's list, a draw below
  it refusing; the eight `shl [edi+0xD8…0xF4], 8` at 0x00640E33–0x00640E64; and 0x0057D5EA calls 0x00623C20
  (`UnitBaseHitClass`: weapon `+0x13C` via 0x0062A180, 1 without one, MonStats2 `+0x14`, else 0) under `+0x64` = 0 and
  an empty low nibble. Also read: the knockback distance 10 for base class 78 else 5 (0x005A783F–0x005A784B), the
  block gate (0x0057D282–0x0057D2D6), `g_HitClassElements` (36→48, 16→32, 28→64, 40→80, twice).
  **The corrections stand:** anim/0001 § 1 (an object's `+0x48` is 8.8, `re/types/game.h` with it) and combat/0001
  § 6 (`UnitBaseHitClass` at the delivery, `HitClassPick` in `COMBAT_GetHit`), each as a dated note. **Blind rule:**
  no `anim/leads` row is cited, no community number or formula appears without an address, and *Leads used* states
  that leads were not read before filing. **P1.3's *Done when* is met:** the speeds (CharStats, MonStats,
  `MonStatsSpeeds`, stat 67, the slowing states, `RunDrain`), `PathSetSpeed` and the step in 16.16 units, each gate
  (do, delivery, `srvmissile`, hit recovery and `GetHitRoll`, knockback and stun lengths, block, `delay`, the object
  operate), the get-hit and durability draws, the hit class (folded at P0: its sources, and the server gate found is
  `GetHitRoll`'s divisor; `Unit+0xB0`'s readers stay an open question, which the item's "whether" allows), the
  `lane/a50t` items (§ 1.1's walk base 256 and the `Velocity`-0 S1 write; anim/0002's question struck citing
  ItemStatCost § Timing), the movement-step event kind, and § 9.
  **Rulings.** (a) **§ 9's boundary is accepted** with one addition, the collision test `0x0064FF90`'s result per
  crossed subtile as an oracle (the grid is drlg/collision's), and is **folded into Phase 2's text** (a *Boundary*
  item) with five new cases under *Done when* (`GetHitRoll` bands, knockbacks, the run drain in the run windows, the
  every-frame event's first frame, and optional Concentration draws and object operate ends); the minimums stay
  estimates. (b) The step-product wrap (`v ≥ 32 768`) is not a Phase 2 case unless a stock source reaches it; it
  stays anim/0003's open question. (c) The global hit-class counter changes no server outcome found (every high
  nibble gives `D` 16), so Phase 2 logs `+0x60` but need not model the counter beyond the nibble it logs. (d) **With
  P1.3 accepted, Phase 1's three batches are done.** Phase 1's last *Done when* item (Phase 1b) closes with P1b
  part 2. **P1b part 2 (the verdicts on `anim/leads` against P1.1–P1.3) may start now.** **0050·P2 (harness, one
  slot) may start now:** its gate, 0045·P3's review, has been open since 2026-10-27, and Phase 1b need only land
  before Phase 2's last session batch.
  **Fixes (applied in anim/0003):** § 2's move bullet gains the collision walk's increment (`0x00678F00` halves both
  axes until each is within one subtile), the free-crossing count at `+0x1D4`, and the 10th crossing's exit, which
  takes the full step unchecked and sets flag `0x8` (omission); § 2's wrap bound names the sign case (+4096 wraps at
  `v` 32 768, −4096 does not) (omission); § 6.1's block gate writes stat 95 only when the test passes, and otherwise
  returns at 0x0057D3BD (omission); the function table's "§ 6.7" for § 6.5, and that heading's level (stale
  cross-reference). The review request is closed. Ledger: the lane row filled (usage from the orchestrator), the
  review row added with "—" usage.
