# 0050 — Animation and frame timing: unit modes, frame counts, rates and breakpoints, movement speed (ADR-0014 phase 4)

> **Status:** approved 2026-10-25 (owner), in effect 2026-10-27 (plan 0045 Phase 2 part 1 accepted); P0 accepted 2026-10-27; P1 batches P1.1–P1.3 accepted with fixes 2026-10-27; P1b part 2 accepted with fixes 2026-10-27 (Phase 1b done); P2 part 1 accepted with fixes 2026-10-27 (run:2026-10-27-anim, 0 mismatches); **P2 part 2 open** (ruled at the part 1 review); P3 may start beside it, its review waits for part 2's
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
  - 500 monster mode events over at least 20 classes, a sequence monster (mode 14) and a `fast` champion among them (read at the part 1 review as a unit with the `fast` mod, MonUMod row 6: no stock champion takes it, its `champion` cell being empty);
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
  - **the Phase 1b cases** (required, from the 19 `contradicted` verdicts of P1b part 2, all reachable on stock data,
    and the P1b-1 refinement of A1, C1, H1 and B1 ruled at its review;
    [anim/leads § 12](../findings/anim/leads.md#12-verdicts-part-2),
    [backlog](../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md); minimums are estimates):
    **P1b-1** the mode length (A2 contradicted; A1, C1, H1, B1 the counting refinement): attack (an Amazon or
    Sorceress A1 with a start frame and one class without), cast, get-hit and block at two or more rates each, one of
    them a slowed attack (factor ≤ 60) and one a fast one (factor ≥ 157), so A2 separates from both `n` and `n − 1`;
    per action the schedule frame `T`, every kind-0 event's frame, the kind-1 end's frame (`T + n`), the frame of the
    next request and `PlrModeLeaveOk`'s result with `PlrModeEndPending`'s `E`, and the next mode's start frame; for
    get-hit and block the first frame the player acts again; a held Lightning cast (mode 18) as the control, the same
    fields. It settles whether the interval between two actions is `n` or `N = n − 1`, and the spec states the
    sources' count as `N`; **P1b-2** 30 attacks with the factor above 175 (R5);
    **P1b-3** 30 throws (TH) by a non-Barbarian, no −30 (A9); **P1b-4** Charge and Leap Attack rates at two item-IAS
    values, not the attack branch (A10); **P1b-5** Double Swing and Frenzy with two weapons of different speed, one
    rate, base 70, also Frenzy after a missed first swing (A12, A13); **P1b-6** werewolf and werebear attacks with no
    weapon and two weapon classes, `w` against the human A1 record (A14); **P1b-7** lengths and do frames of the
    `DZSC*`, `40SCHTH`, `TGSCHTH`, `VASCHTH` and `NESC*` casts at two FCR values (C2, C4); **P1b-8** a Druid's get-hit
    with a one-handed hammer and with a two-handed sword or axe, an Amazon's block with a wand (H4); **P1b-9** in the
    `GetHitRoll` case, a get-hit in `[hp/16, hp/12)` and a refusal above `hp/12` (H6); **P1b-10** 10 player knockbacks
    with the following mode (neutral) logged, from Blood Raven in Hell (MonProp `bloodraven` `prop1 (H)` `knock`, the
    stock source; the P1.3 review's 30 knockbacks include them) (H10); **P1b-11** 30 blocked hits on a
    player, 10 inside `⌊stat 102 / 8⌋ + 15` frames of the last block start (B5); **P1b-12** 30 repeated casts of a delay
    skill outlasting its cast (Frozen Orb), the do, state 121 and the next do (D2); **P1b-13** a unit under Slows
    Target, path speed unchanged, rate lowered at the cap, 30 events and a movement window (M6, M7, M8); **P1b-14** a
    moving factor below 25 (the floor) and a player's run at the animation base `0x65`, in the movement windows (M11);
    **P1b-15** 30 Charge starts with the path speed logged, one at stat 67 ≤ 50 (M12);
  - **the P1.3 review's cases** (minimums are estimates): 100 `GetHitRoll` calls with the band, the divisor and the
    draws predicted, at least 20 in each of the two drawing bands and over two or more hit classes with different
    divisors; 30 knockbacks (players and monsters, the end frame predicted); the run drain in the run windows above
    (stamina per frame, and a run that turns to a walk at 0 if the pilot can stage it); the first frame of an
    every-frame event queued during a frame's unit-list run (anim/0003's open question: it sets the first step of
    every moving mode and the monster knockback count), logged at 30 or more moving-mode starts; optional: 30
    `PlayerModeAllowed` draws under state 42 and 30 object operate ends (event 1). The step-product wrap
    (`v ≥ 32 768`) is not a case unless a stock source reaches it.

  Rare-branch minimums (about 30 each) may fall short, named in the record with their counts; their claims stay `[I]`.

#### Phase 2 part 2 — the get-hits, blocks and rates part 1 could not stage (ruled at the part 1 review, 2026-10-27)
- **Owner skill:** reverser (agent-driven; one slot from 1–2, given in the prompt; no Ghidra)
- **Why:** run:2026-10-27-anim (part 1) holds 0 mismatches over every compared kind, but rows of the *Done when*
  above that are not rare branches are short because the sessions could not stage them: 84 get-hits in all (no class
  has an FHR rate with 30; a get-hit needs a hit of a sixteenth of max life, and every fragile character died after
  2–9), blocks for the Barbarian and the FBR rates of four classes, throws for three classes, the second weapon type
  of the IAS rates and the Barbarian's third IAS rate, a third FCR rate for three classes. 124 dispatches after a
  catalogue cancel are not compared because the skill's own queue (`sub_005417D0_UnitQueueEvent`) is not logged.
  Each needs a recipe, a session or a breakpoint, not a rerun of part 1's sessions.
- **Start:** part 1's tools (`tools/anim.py` `c2ef2166…`, its `--review` tallies included; logger rev 5;
  `tools/anim_sessions.py` `889dae99…`); part 1's 55 logs stay kept and unchanged, and the floors below count part
  1's events with part 2's. Nothing in part 1's closing check may regress: the closing check of part 2 runs over all
  logs of both parts.
- **What:** (1) **the get-hit route** (an estimate, the lane may change the numbers, not the route): a high-life
  character per class (clvl 60 or more, life 1 000 or more, a hit of 63 or more reaching `GetHitRoll`'s bands) in a
  Nightmare area whose melee hits fall between `maxHP / 16` and a quarter of life (the lane picks it from one
  development session's `GH` totals), the belt and the inventory filled with stock full rejuvenation potions
  (`rvl`) and the pilot's `--drink-in-burst` at a higher life threshold, so that one potion buys several get-hits;
  the three FHR tiers per class as part 1's t0–t2 (0, 24, 48) or other stock values where two tiers give one rate;
  (2) longer `bk-` sessions (split in two where the session cap cut part 1's to 10 hops) for two FBR rates per class;
  (3) F4 Throw sessions for the Necromancer, Paladin and Druid; (4) set-2 attacks (the weapon swap pressed and its
  record checked in the log) at three IAS values per class, and a third IAS rate for the Barbarian; (5) a third FCR
  rate for the Amazon, Barbarian and Assassin (another stock FCR value where two tiers give one rate); (6) logger
  rev 6: `sub_005417D0_UnitQueueEvent` called from 0x005B0000–0x005EFFFF logged (its kind, frame and arguments), so
  that the checker takes that queue as an ADR-0004 oracle (logged, taken as given) and compares the dispatches after
  a catalogue cancel, the excuse window of part 1's checker removed; (7) the rare branches below, staged where a
  recipe reaches them.
- **Done when:** `run:YYYY-MM-DD-anim` (part 2) reproduces with **0 mismatches** over its logs and part 1's, and, with
  part 1, the following are met or named short with counts (minimums are estimates):
  - get-hits: for each class, 30 or more at each of three FHR rates (the `RATES` line's `get-hit rates30` ≥ 3),
    each with its schedule, its end and the first frame the player acts again (P1b-1's get-hit half at two or more
    rates); P1b-8's Druid get-hits with a one-handed hammer and a two-handed sword, 30 each;
  - blocks: two FBR rates of 30 for every class (`block rates30` ≥ 2);
  - throws: 30 per class for the seven classes (P1b-3 counted with them);
  - attacks: three IAS rates of 30 on each of two weapon types (two records) per class; casts: three FCR rates of
    30 per class (`cast rates30` ≥ 3);
  - the catalogue queue: in part 2's rev 6 logs every dispatch after a catalogue cancel compared
    (`dispatch-catalogue-queued` 0 there, 30 or more such dispatches); part 1's 124, whose logs lack the queue, stay
    uncompared and are named;
  - P1b-1's restart against the request frame (`rv-req-*`) for every class and action mode, the held Lightning
    control among them;
  - rare branches (about 30 each; short ones named with counts, their claims stay `[I]`): 30 player knockbacks
    (mode 19 starts with the end predicted; class 462 or another stock source); a run that turns to a walk at 0
    stamina (a low-stamina recipe on a long run); P1b-2 (30 attacks with the factor above 175: Burst of Speed
    extended); P1b-13 (a stock item or skill with Slows Target, or named unreachable with the survey); P1b-14 (a
    moving factor below 25 by stacked stock slows, or named unreachable); P1b-7's `VASCHTH` (or the reason no
    stock form reaches it); P1b-15 (a Charge at stat 67 ≤ 50).
  Not part 2 cases, ruled at the part 1 review: the object-start and `PlayerModeAllowed` chaining (the plan's own
  clause: a kind with no chained pair keeps its draw-order claims `[I]`), the optional `PlayerModeAllowed` draws under
  state 42 and the object operate ends, and a Frenzy after a missed first swing.

### Phase 3 — Spec: animation and frame timing
- **Owner skill:** spec-writer
- **Start:** after the Phase 2 part 1 review (2026-10-27), in parallel with Phase 2 part 2 (plan 0045's precedent):
  the statements part 2 targets are written `[I]` and re-tagged from part 2's reviewed raises; **the Phase 3 review
  waits for part 2's review**.
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
  [archivist entry](../backlog/archive/2026-10-27-architect-archivist-test-d2s-recipe-bases-and-mp-saves-pin.md). The 13
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
  ([backlog](../backlog/archive/2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md)); review
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
- **2026-10-27 — `lane/a2t` review (architect): accept.** The archivist's fix for the two old `test_d2s.py` failures
  ([request](../backlog/archive/2026-10-27-archivist-architect-review-lane-a2t-testd2s-recipe-bases.md)). After merging
  `main`, `python3 -I tools/test_d2s.py` runs 47 tests, OK. Under `tools/` the lane touches only `tools/test_d2s.py`:
  13 `RECIPE_BASES` rows, the `test_mp_saves_check` pin and its docstring line. No recipe, builder or `mp_saves.py`
  line changed. All ten `skills-*` hashes equal their saves in `2026-10-27-skills-manifest.sha256`, checked by script.
  `mp-sock-join`, `mp-wound-join` and `mp-pal-conv` were built twice into the review scratchpad, and both builds give the
  pinned hashes. `mp_saves.py check` gives `recipes=30 bad=0 pairs=21 pairs_bad=0`, the figure the `lane/p51r` review
  accepted for plan 0051 P1a. **`workspace/runtime/`:** the mp saves have no manifest. Nothing under
  `mp-saves-p44` or `mp-saves-p44h` is newer than 2026-10-20, and no `MpSockJoin`, `MpWoundJoin` or `MpPalConv` exists
  anywhere in `workspace/`. That is consistent with the blocked build never running. No fixes. The request is closed.
  Ledger: lane row filled (usage from the orchestrator), review row added with "—" usage.
- **2026-10-27 — anim/0003's table links folded (archivist, `lane/a3f`; no Ghidra, no harness).** From the reverser's
  p50d entry ([backlog](../backlog/archive/2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md)),
  every reader `[I]` as the finding: [Objects § Timing](../tables/Objects.md#timing-plan-0050-phase-0) gains the
  load-time `FrameCnt` `<< 8` (`0x00640E33`–`0x00640E64`, an object's length is 8.8) and the chest operate end (event 1
  `FrameCnt1 + 1` frames on, mode 2 without an animation start), with a reader row;
  [HitClass](../tables/HitClass.md#open-questions)'s open question is answered (the attacker's low nibble, the element
  nibble in `COMBAT_GetHit`, `GetHitRoll`'s divisor), its old "the delivery picks from the counter" sentence replaced
  per anim/0003's correction of combat/0001 § 6, and the Weapons, MonStats2 and Missiles hit-class rows link it
  (Missiles has no § Timing: its column row); MonStats § Timing's `9A`/`E9` `[L]` is replaced by § 1.1's reading, walk
  base 256 and run 128 below 410. **Surprises:** the entry's "Missiles gives the low nibble" differs from the finding
  (the whole `+0x60` under the packet's high nibble), and the finding's "seven classic `9A` rows" are the `mS1` ones;
  an eighth (`compellingorb` 366) gets the same base. The docs follow the finding and say both. No survey baseline
  changed. Review request: [backlog](../backlog/archive/2026-10-27-archivist-architect-review-lane-a3f-p50d-table-links.md).
- **2026-10-27 — `lane/a3f` review (architect): accept with fixes.** After merging `main`, objdump on the pinned
  `Game.exe` checks the `FrameCnt` shifts (`0x00640E33`–`0x00640E64`, `shl [edi+0xD8..0xF4], 8`), the chest queue
  (`0x0058639A`: `FrameCnt1 >> 8` + frame + 1, `Mode1` at `+0x140`), event 1 (`0x005814A7` `Mode2` `+0x141`,
  `0x005814B7` `HasCollision2` `+0x122`), the missile hit (`0x005AD868`–`0x005AD875`: `HitClass | (+0x60 & 0xF0)`
  stored whole), `GetHitRoll`'s jump table at `0x0057CBF8` (8, 32, 64, 16 as the docs) and `MonStatsSpeeds`' walk and
  run lookups. The tables were read with `python3 -I`: `hitclass.txt`'s row order, Missiles `HitClass`'s values, the
  ten `9A`/`E9` rows, MonStats2's and `animdata.d2`'s (no `9AWL`, `E9WL` or `E9RN` record). Every new reader is `[I]`,
  with one `[C]` data count; no game data dumped. **Rulings:** (1) Missiles `HitClass` sets the whole `+0x60`: the
  docs follow the finding over the entry, and the data adds to it, as 122 of the 192 set rows carry a high nibble of
  their own. (2) `compellingorb` 366 as the eighth `9A` row is accepted: it has no `mS1`, which is why the finding
  names seven, and it shares the fallback walk base. (3) The divisor rows' names match `hitclass.txt`'s order (2
  `1hss`, 6 `1ht`, 10 `bow`, 11 `xbow`; 4 `2hss`, 8 `club`; 5 `2hsl`). (4) anim/0003 § 6.5 is not internally
  inconsistent. Its prose and the binary (`+0x122`) agree on `HasCollision2`, and the `HasCollision0` anchor was a
  slip. It is fixed in place in anim/0003 (§ 6.5 with a dated note, and Data touched) and in Objects § Timing,
  with `Mode2` and `FrameCnt1` added. No reverser entry. **Fixes (4):** MonStats names `compellingorb`'s code `9a`,
  in lower case (misread). HitClass and Missiles carry the high-nibble count (omission). MonStats gives the `E9`
  rows' run base 256 (omission). The anchors (wrong anchor). The review request is closed. Ledger: the lane row
  filled (usage from the orchestrator), the review row added with "—" usage.
- **2026-10-27 — Phase 1b part 2: the verdicts (reverser, `lane/p50v`; no Ghidra, no harness, objdump once).** Each
  of the 61 [anim/leads](../findings/anim/leads.md) claims has one verdict, written in the *Leads used* of
  [anim/0001](../findings/anim/0001-modes-frames.md#leads-used) (R1, A3, A4), [anim/0002](../findings/anim/0002-rates.md#leads-used)
  (29 rate, attack, cast, hit-recovery and block rows) and [anim/0003](../findings/anim/0003-movement-gates.md#leads-used)
  (29 gate, delay, H5–H10, B4, B5 and movement rows), each with the finding's section and address, and in the leads'
  Verdict column with a new § 12. **Counts:** held 7, held with refinement 29, contradicted 23 (9 plain; 11
  `(version: D2R)`, 3 `(version: 1.09)`, ruling (c) of the `lane/p50c` review), not covered 2 (A11: the rollback
  percentages are catalogue values; D5: the item cast's delay path is not read). By topic: R 2/2/1/0 (held, refined,
  contradicted, not covered), A 2/5/7/1, C 0/4/3/0, D 2/1/1/1, H 0/6/4/0, B 0/3/2/0, M 1/8/5/0. A4 and D4 are decided
  from the P0 data (ruling (d)): the Basin attack page re-fetched (rev 65669, unchanged), all 69 rows equal the
  records, the code's start frames and first code-1/2 events; the 23 delays equal Skills `delay` at 25 a second.
  **Kept check:** `tools/anim_leads_check.py code` (`80fb5fae…`; part 1's default run still byte-identical to
  `p50c-leads-check.txt`): the 39 tables × 2 sources against the code's model (`tools/anim_rates.py` rates and
  `sched_len`) over the records the code looks up: every change point equal (78/78), the tables' frame count one below
  the code's `⌈256 (F − S) / r⌉` in 76, equal in the 2 Lightning tables (a sequence); output
  `workspace/logs/anim-leads/p50v-code.txt` (`99e7b983…`), `p50v-commands.txt`, `p50v-manifest.sha256`. **Main
  findings:** the one-frame offset on every record mode (P1b-1, the largest case); the records settle C2/C3 for the
  tables (Druid cast 15 frames at 208, Necromancer 16) and against C2's and C4's Druid, form and vampire rows; Slows
  Target sets stats 68/69 only, so no velocity effect (M6–M8); a player's knockback ends in neutral (H10); the block
  animation's gate is a cooldown (B5); the throw has no −30 (A9); Charge and Leap Attack take no IAS (A10); the
  shapeshift base uses the human A1 record per weapon (A14). One objdump read: `RunVelocityStat`'s class is the unit's
  real class (0x0062449F), cited in M14. **Phase 2:** the 23 contradicted claims are all reachable on stock data and
  are written into *Done when* as cases P1b-1 … P1b-15
  ([backlog](../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md)). No tag changed; nothing
  promoted; `re/symbols.csv` untouched. "No lead" recorded for monster frames and rates, the `fast` mod, object operate
  frames and `monseq`. Review requested
  ([backlog](../backlog/archive/2026-10-27-reverser-architect-review-plan-0050-p1b-part-2.md)).
- **2026-10-27 — `lane/p50v` review (architect): accept with fixes; Phase 1b done.** After merging `main` (the plan
  log and ledger conflicts kept both sides; `backlog.py archive` clean), `tools/anim_leads_check.py code` was rerun
  under `MemoryMax=4G` and is byte-identical to `p50v-code.txt` (`SUMMARY anim_leads_code tab=78 thresholds_equal=78
  table_minus_n_is_-1=76 table_minus_n_is_0=2 basin=69 basin_match=69 delay_rows=23 delay_match=23`), the default run
  byte-identical to `p50c-leads-check.txt`, and `sha256sum -c p50v-manifest.sha256` and `manifest.sha256` pass; the
  six input hashes in `p50v-commands.txt` match. One verdict per Id: 61 across the three *Leads used*, none twice,
  checked by script. No `[C]`/`[I]` changed in the lane's diff, `re/symbols.csv` and `docs/specs/` untouched.
  **Rulings:** (a) **P1b-1 is a counting difference, not a shown contradiction.** The schedule queues the steps `T +
  1` … `T + N` that carry every frame event and the end at `T + N + 1 = T + n` (anim/0001 § 7,
  fn:SUNIT_ScheduleModeEvents@0x005539B0), so `N = n − 1` whenever the ceiling is 2 or more: the sources' count is
  `N`, the frames with the end's frame left out, and A1's own source names that convention ("the first and last
  frame are the same"). The 76 rows agree on the rate and on every change point; a constant offset cannot tell a
  different count from a different behaviour, and the code does not say which of `n` and `n − 1` is observed as the
  interval between two actions (`PlrModeLeaveOk` lets A1, A2, SC and TH be left while the end is queued). A1, C1,
  H1 and B1 move from `contradicted (version: D2R)` to **held with refinement**; the Lightning tables' `n` is the
  sources' own exception and stays for the case to explain. **A2 stays contradicted:** its `− 1` inside the ceiling
  gives `n − 2` below 256 and up to `n` above, so it differs from both readings. P1b-1 stays a required Phase 2 case
  and now names what settles it: per action the schedule frame `T`, every kind-0 event's frame, the kind-1 end's
  frame, the next request's frame with `PlrModeLeaveOk`'s result and `PlrModeEndPending`'s `E`, the next mode's start
  (for get-hit and block, the first frame the player acts), a slowed (factor ≤ 60) and a fast (≥ 157) attack for A2,
  and a held Lightning cast as the control. Counts after the move: **held 7, held with refinement 33, contradicted 19
  (9 plain, 7 `(version: D2R)`, 3 `(version: 1.09)`), not covered 2** (A11, D5), greps in leads § 12. (b) The
  version rulings of the `lane/p50c` review are applied as written: all 19 D2R-only and 5 1.09-only rows checked, every
  contradicted one among them carries its version, and no D2R-only difference is counted as a community error. (c)
  **P1b-10 is not conditional:** MonProp's one `knock` row is `bloodraven` `prop1 (H)`, a stock source of a player
  knockback in Hell, and the P1.3 review's 30 knockbacks already include players; a shortfall is named in the record
  under the rare-branch rule. The other 18 contradicted claims are reachable on stock data as filed (P1b-2 Fanaticism
  or Burst of Speed with a fast weapon; P1b-14 chill with a stat-67 curse). (d) The vocabulary fits the evidence rules
  (one of the four verdicts per compared claim, `contradicted` with its backlog entry), with (a)'s reading of
  `contradicted`: a disagreement the code itself shows, not a count the rows cannot separate. (e) A11 and D5 not
  covered is right: the reschedule percentages are catalogue values (plan 0046) and the item cast's delay path is
  unread; neither is a Phase 2 case. **Fixes (4), written into the findings, leads § 12, Phase 2's *Done when* and the
  cases entry:** A1, C1, H1, B1's verdicts and details (overclaim); A2's detail, `n − 2` below 256 (omission); an
  address or `fn:` added to the 28 verdicts that cited only a section (omission); P1b-10's stock source named and the
  condition dropped (omission). **Phase 1b's *Done when* is met** (one verdict per claim; every reachable
  contradicted claim a required Phase 2 case; agreement promotes nothing), so Phase 1b is done. **For 0050·P2
  (`lane/p50e`):** merge `main` for the cases P1b-1 … P1b-15 in *Done when* and the cases entry; P1b-1 now logs the
  next request and `PlrModeLeaveOk`'s result besides the frames, and the spec (Phase 3) states the sources' count as
  `N = n − 1` whatever the run finds; P1b-10 needs a Hell game with Blood Raven. The review request is closed.
  Ledger: the lane row filled (usage from the orchestrator), the review row added with "—" usage.
- **2026-10-27 — Phase 2, first lane run: checkpoint and resume note (reverser, `lane/p50e`; harness slot 2, no
  Ghidra; rotated at about 4 h).** Built: `tools/gdb/anim.gdb` with `tools/gdb/anim.py` (rev 4: the rate exit, the
  schedule and its queue at the 13 call sites, the slot-list dispatches, cancels, mode sets, every-frame starts with
  the event runner's phase, object animation starts and queues, the windowed path steps with the collision results,
  the windowed advances, the run drain, `GetHitRoll` with its max-HP boundary, `COMBAT_GetHit`, `PlayerModeAllowed`,
  `PlrModeLeaveOk` with `PlrModeEndPending`'s `E`, the delay state, unit frees); `tools/anim.py` (`check`, the model
  of anim/0001–0003, and the oracle replays `replay-skills`, `replay-combat`); `tools/anim_sessions.py` (recipes
  `tools/d2s_recipes/anim-*.json`, sessions, driver); `tools/xdrive.py` `rhold`. The record is
  [run:2026-10-27-anim](../findings/anim/experiments.md#run2026-10-27-anim) (in progress); no finding claim is raised
  yet.
  **Checkpoint** (`2026-10-27-anim-check-ckpt1.txt`, 31 sessions, `tools/anim.py` `b3fca053…`): `CHECK anim` 0 mismatched in every kind: 186 016 rate calls (record name, frames, speed, `+0x4C`), 17 896 schedules (start frame 17 398, queued lists, lengths, rates), 29 207 queued events fired at their frames and 29 182 dispatches all queued, 2 507 advances and 1 109 sequence advances, 70 019 path steps (68 327 point indices, 95 907 path speeds against the rate call), 27 919 run-drain frames, 4 226 `GetHitRoll` calls, 19 830 `PlayerModeAllowed` seeds, 440 object animation starts, 299 block gates, 3 050 knockback ends, 715 `PlrModeEndPending` values and 7 437 every-frame first runs.
  Against *Done when* so far: 4 846 player mode events, every class (530–1 013 each): A1 1 913, cast 1 466, kick 533, sequence 498 (mode 18), block 244, throw 91 (Amazon and Barbarian), S2 59, get-hit 38, death 4; met for 1 500 and per class and mode except get-hit (all classes), throw (Amazon 38, others none), block for most classes; the rates: three tiers logged for every class (IAS, FCR, FBR and FRW at three values; FHR has no get-hit events at t1–t2), so the get-hit breakpoints are short. 13 050 monster schedule events over 39 classes (met), sequence monsters (1 109 sequence advances), 444 monster knockback ends; ruling (g) met: classic S1–S4 at the moving rate 1 266 rate calls over `fallen1` and `fallen2` (632 S1/S2 schedules), 17 under a stat
  67 change, class ≥ 410 S1–S4 584 at the attack or default rate; 292 object starts with the `Sync` draw (met) but no chained pair; 4 611 movement windows (met; walk and run per class, monsters walking, running, knocked back), 104 under a slowing state (met); `GetHitRoll` 4 226 calls, the drawing bands 386 and 425, divisors 8, 16, 32, 64 (met); P1b-9 (37 get-hits in `[hp/16, hp/12)`, 237 refusals above `hp/12`) and P1b-11 (299 blocked hits, 40 inside the window) met; the `fast` champion not yet identified in the tallies.
  **Preliminary readings** (for the closing run to confirm; none is a claim yet): (1) P1b-1: of the held actions
  that followed within 3 frames of the end, the next cast started at `T + n − 1` 360 times and at `T + n` 73, the
  next attack 66 and 33, while held Lightning (mode 18) started at `T + n` 70 times and `T + n − 1` once: the
  back-to-back interval of a normal mode is the sources' `N = n − 1` (`PlrModeLeaveOk` passes while the end is
  queued), Lightning's is `n`, the sources' own exception. (2) The every-frame start's first run (anim/0003's open
  question): 7 437 starts, every one in its own frame when queued before the type's every-frame list is walked (the
  runner's phase below 3 for players, 5 for monsters) and in the next frame otherwise (`ef-first`, 0 mismatched).
  (3) P1b-12: after Frozen Orb's delay state the next do came at `d + 7` frames 16 times (7 = its cast's do frame),
  i.e. the delay runs from the do (D1). (4) P1b-11: 299 blocked hits on a player, 40 inside the gate; the gate decides
  the block command, and the command's mode test refused it 15 times. (5) The `MonStatsSpeeds` run base below class
  410 is scaled by `Run(i) / Run(b)` too (anim/0002 § 3.5's "then scaled the same way by `Run`"; the first model
  revision missed it, class 6 `zombie2` showed it). (6) The oracle replays: plan 0045's do frames 2 435 of 2 436; the
  combat and plan 0047 `GetHitRoll` draws 3 547 of 3 636 and 2 596 of 2 667, every miss a monster defender drawing
  nothing where the model draws (freeze or stun, not in those logs).
  **Resume (next lane, same branch and worktree, slot 2, aside tag `p50e`, saves
  `workspace/logs/anim/saves-2026-10-27-anim/`):** keep `tools/gdb/anim.py` at rev 4 unless a case needs a line (then
  rev 5, named per session in the record). Sessions owed: (a) the get-hit coverage (FHR at three breakpoints per
  class, 30 each): the life-40 `gh-` sessions gave only 2–8 get-hits each before the character died; design a
  character that survives being hit (more life with heavier hitters, e.g. Act II–III Normal at life 120–200, or
  Prayer for the Paladin), else name the shortfall; (b) `mon-4` … `mon-6` (more classes, chilled walkers toward the
  50 slowed windows, Frozen Orb toward 30 delay intervals); (c) P1b-2 (Fanaticism or Burst of Speed with a fast
  weapon), P1b-3 by a second non-Barbarian (the Assassin's throws: give `tkf` the F4 Throw in set 2), P1b-4/P1b-15
  (Charge, Leap Attack), P1b-5 (Double Swing and Frenzy with two weapons), P1b-6 and the form casts of P1b-7
  (werewolf, werebear), P1b-8 (a Druid with a one-handed hammer and a two-handed sword; an Amazon with a wand and a
  shield), P1b-10 (Blood Raven in Hell: a Hell-proof character and the route from Cold Plains to the Burial Grounds),
  P1b-13 (Slows Target), P1b-14 (a moving factor below 25); (d) the chaining minimum (20 chained pairs per drawing
  kind): `GetHitRoll` has 86 chained of 526 consecutive pairs and the object starts none (other draws on the same
  seed come between); either log the intervening draws or keep the draw order `[I]`; (e) then the closing check over
  every kept log, the findings' run sections (anim/0001–0003, raising what the run separates, review-fix 14's symbol
  raises), the review-fixes pass, the review request and the ledger row.
- **2026-10-27 — Phase 2, second lane run: run closed (reverser, `lane/p50e` after its rotation; harness slot 2,
  no Ghidra; objdump reads of `UNIT_SeqReadFrame`, `SEQ_ReadFrame`, `UNIT_AnimInit`'s rate calls and the `+0x4E`
  stores).** 24 more sessions (batch 5: get-hit variants gh2/gh4/gh4n, block and throw `bk-`, the P1b specials
  `sp-`, `p8-`, `br-hell`, `mon-4`, `mon-5`), logger rev 5 for 18 of them (the wolf and bear states), pilot
  `--drink-in-burst`; the checker gained the dual-wield class and term, the shapeshift display and wereform base,
  and two oracle classifications (a catalogue skill's own queue after its cancel; a do's store to `+0x4E`). The record
  is [run:2026-10-27-anim](../findings/anim/experiments.md#run2026-10-27-anim), **closed**: the closing check over all
  55 kept logs has 0 mismatches in every kind (rate 298 373, schedules 25 848, queued events 42 542, steps 99 241,
  `GetHitRoll` 7 195 …), the checkpoint's 31 logs still 0 under the closing checker, the three replays byte-identical.
  The findings' run sections raise to `[C]`: anim/0001 the record, start frame, schedule and dispatch, the advance,
  the object draw (not its chaining), the per-frame order; anim/0002 every rate branch (not the floors and the cap),
  the dual-wield, sequence and shapeshift terms, the monster walk and run base; anim/0003 the step, the speeds (not
  the floor), the run drain (not the turn to a walk), the monster knockback end, `GetHitRoll` (not the divisors 32 and
  64), the block gate, `PlrModeEndPending`, the delay's start. 21 symbols raised to `C` in `re/symbols.csv` and the
  Functions tables (review-fix 14). **Short** (record's Covers, the rare-branch rule): get-hits per class (84 in
  all; every fragile character died after 2–9: a get-hit needs a hit of a sixteenth of life), so the FHR
  breakpoints; blocks for the Barbarian (11) and the FBR breakpoints for four classes; throws for the Necromancer
  (22), Paladin (3) and Druid (0); the second weapon type of the IAS rates; three FCR rates for the Amazon,
  Barbarian, Assassin; object-start and `PlayerModeAllowed` chaining (0 chained of 7; no draw met); player
  knockbacks (2 mode-19 starts); a run turning to a walk; P1b-2 (31 calls above 175), P1b-13 (not staged), P1b-14 (no
  factor below 25), `VASCHTH`, a slowed Charge. A `fast` champion is not reachable as named (MonUMod `fast` has no
  `champion` cell); the mod is met on superuniques and their minions (9 300 calls). **Readings:** P1b-1, a held
  normal action restarts at `T + N` (`N = n − 1`: casts 448 against 103 at `T + n`), held Lightning at `T + n` (68,
  never `T + N`), get-hit and block never before `T + n`; 23 A1 restarts separate A2. P1b-12, the next cast starts at
  the do plus the delay (72 of 73). P1b-10, 12 of Blood Raven's 13 knockback results put the player in neutral in the
  same frame. The every-frame first run answered (anim/0003's open question, closed). The P1b cases entry is closed;
  review requested ([backlog](../backlog/archive/2026-10-27-reverser-architect-review-plan-0050-phase-2.md)).
- **2026-10-27 — Phase 2 (part 1) reviewed (architect, `lane/p50e` at `16c783e7`; `main` merged first, `c9981432`, the
  ledger conflict kept both sides; static, objdump, no Ghidra, no harness): accept with fixes (5); Phase 2 part 2
  filed.** Re-checked: `2026-10-27-anim-manifest.sha256` (324 lines, `39ba842a…`) passes from `workspace/logs/anim/`;
  `check` over the 55 logs, `summary` and the three replays, rerun under `systemd-run --user --scope -p MemoryMax=4G`
  with `tools/anim.py` `4241197a…`, are byte-identical to the kept outputs (every kind 0 mismatched: rate 298 373,
  schedules 25 848, queued events 42 542, steps 99 241, `GetHitRoll` 7 195). objdump on the pinned image: the
  catalogue cancels' returns 0x005CBDED, 0x005CFAAA, 0x005D1503, 0x005DA2AA (each `UNIT_CancelEvents` at 0x00540E60
  followed by `sub_005417D0_UnitQueueEvent`: 0x005CFABE, 0x005D1517, 0x005DA2BE), the `+0x4E` stores 0x005CB48E,
  0x005CB989, 0x005CD51E, `UNIT_AnimInit`'s rate-call returns 0x00624469, 0x006244C5, 0x006244E3 with its `+0x48`
  writes 0x00624473 and 0x006244F4, the start-frame read 0x005539CC, the dispatch sites 0x00540FC4 and 0x005410C4:
  all resolve. MonUMod read with `python3 -I`. The review added `tools/anim.py check --review` (`c2ef2166…`; without
  the flag the output is byte-identical) and kept `2026-10-27-anim-check-review.txt` (`d08c92a9…`,
  `2026-10-27-anim-review-manifest.sha256`).
  - **Fixes (5):** (1) *misread:* the catalogue exclusion was filed as "124 kind-1 dispatches" and "a boundary
    oracle": they are 110 kind 0 and 14 kind 1, 0–4 frames after the unit's latest catalogue cancel, and since the
    skill's own queue is not logged they are an uncompared catalogue path, not an ADR-0004 oracle (anim/0001's
    schedule bullet and the record corrected; part 2 logs the queue). (2) *overclaim:* P1b-1's `[C]` "the sources'
    count `N` is the interval between two held normal actions": the `--review` tallies show the next action starting
    in its request's frame (1 816 of 2 084 first action requests after a cast, 23 of them before `T + N`) and
    `PlrModeLeaveOk` returning 1 at all 5 633 first requests, so `N` is the client's held-request cadence, not a server
    gate; the starts before `T + N` the record counted (8 and 15) are block and get-hit requests (anim/0001's P1b-1
    bullet, anim/0003's mode-tests bullet and the record rewritten). (3) *under-claim:* four functions whose logged
    output the run compares left I (review-fix 14): `sub_00650150_PathStepCollide` (the step over the logged collision
    results at 0x00650215), `sub_005A8520_MonKnockbackEnd` (541 logged ends, `kb-end`), `SKILLS_SetDelayState` (the
    next cast at its logged frame plus `d`, 72 of 73), `SUNIT_ModeEveryFrame` (9 682 logged starts, `ef-first`):
    raised to `C` in `re/symbols.csv` and the Functions tables (anim/0001 rows split, anim/0003, skills/0001), so the
    run raises 25. (4) *tool not kept:* `dev-p50e-manifest.sha256` listed its own hash, a line that cannot pass, so
    `sha256sum -c` failed; the line removed (70 lines). (5) *misread:* the record's MonUMod champion rows "16, 36, 37,
    39" left out 38 (`possessed`).
  - **Ruling (a): the two classifications.** The `+0x4E` one stands: the three stores are where the checker says, the
    two cases are a catalogue write (plan 0046) and anim/0001 keeps that reading `[I]`, while 1 451 other sequence
    advances are compared. The dispatch one is a legitimate scope exclusion, not an oracle, and it does not hide a
    model gap in what part 1 claims: each of the cancel sites queues its own event at once, and every excused dispatch
    lies 0–4 frames after one. But the checker's window is unbounded (any later dispatch of that unit), which a model
    gap could hide behind; part 2 logs `UnitQueueEvent` from catalogue code and removes the window.
  - **Ruling (b): P1b-1.** A2 is contradicted (23 A1 restarts separate it) and Lightning's control holds (`T + n` 68,
    never `T + N`). What the spec states: the server starts the next action in the frame of its request, whatever
    the frame (the mode request is an oracle); the stock client's held request comes at `T + N` for a normal action and
    at `T + n` for Lightning, `[C]` as an observation of that input; the client's rule is not read. Get-hit and block
    are never left before `T + n` (§ 6.2's refusal the reading, `[I]`). The breakpoint tables' `N` is therefore the interval a held
    button gives, stated as such.
  - **Ruling (c): P1b-12** accepted: under D2 no cast could start inside the D1 window (the state still on), and 72
    start at the logged `SKILLS_SetDelayState` frame plus `d`. **P1b-10** accepted as an observation (12 of 13 Blood
    Raven knockbacks put the player in neutral in the hit's frame, the cause `[I]`), met for its 10; the player's
    knockback length (mode 19, 2 starts) is a part 2 rare branch.
  - **Ruling (d): the `fast` champion.** The claim is right: MonUMod row 6 `fast` has an empty `champion` cell, and the
    rows with `champion` 1 are 16 and 36–39. The *Done when* item is read as a unit with the `fast` mod (the plan text
    amended), met by the 9 300 rate calls of superuniques and minions carrying mod 6.
  - **Ruling (e): Phase 2 part 1 accepted; a Phase 2 part 2 is filed** (above, with its *Done when*), as plan 0045's
    part 2. The rare-branch rule does not cover the get-hits, blocks, throws and rate tiers: they are common events the
    sessions could not stage, and the spec's breakpoint tables need them. **The get-hit fix:** a high-life character
    per class (clvl 60+, life 1 000+) in a Nightmare area whose melee hits fall between `maxHP / 16` and a quarter of
    life, with stock full rejuvenation potions in the belt and inventory and the pilot drinking early, so that each
    potion buys several get-hits; not a high-defence character (it lowers the hit count, not the cost per get-hit).
    The object-start and `PlayerModeAllowed` chaining, the optional state-42 draws and operate ends are not part 2
    cases (the plan's own clause keeps them `[I]`); the player knockbacks, the run's turn to a walk, P1b-2, -7's
    `VASCHTH`, -13, -14 and -15 are part 2's rare branches, named short if unreached.
  - **Ruling (f): the 21 raises** hold under review-fix 14 (each a function whose logged return or effect the check
    compares, the consumer agreeing); with fix (3), 25. `sub_0057EDD0_PlrModeLeaveOk` (no refusal reached),
    `sub_0057EEC0_PlayerModeAllowed` (no draw), the two event dispatchers (only their call is logged) and the path base
    and run-velocity helpers (not logged; their value is compared only through the rate exit) stay I.
  - **Ruling (g): the leads' Verdict column** (request point 5) is not edited: verdicts record the blind cross-check
    of P1b; the run's outcomes live in the findings' run sections, which the spec cites.
  - **Gates.** Phase 2 part 1 accepted, so **0050·P3 (the spec) may start now**, beside part 2 (the statements part 2
    targets written `[I]`, re-tagged from part 2's reviewed raises); **0050·P3's review waits for part 2's review**.
    0052·P2 stays closed (gated on 0050·P3's review). **0050·P2 part 2** may start on one harness slot. The P1b
    cases entry stays closed (its remaining cases are part 2's); the review request is closed.
- **2026-10-27 — `lane/a4t` reviewed (architect, at `65923cc2`; `main` merged first, already up to date): accept.** The diff under `tools/` is `tools/test_d2s.py` alone; all 134 `anim-*` `RECIPE_BASES` pins equal the manifest's `saves-2026-10-27-anim/<SAVES name>.d2s` lines by script (bases and row comments match `tools/anim_sessions.py` SAVES, no manifest save left over), 10 rebuilt into the scratchpad give the pinned bytes, `test_d2s` 60 OK; the row comments name the save, which with the block's manifest name locates the entry, so they stand; the review request is closed.
