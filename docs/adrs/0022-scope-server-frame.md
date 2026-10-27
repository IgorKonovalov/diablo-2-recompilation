# ADR-0022 — After phase (5): the server frame composed, so simulation events chain across units

> **Status:** proposed (architect, 2026-10-27, at the re-draft of plan 0052; for the owner's decision before 0052·P2 starts)
> **Date:** 2026-10-27
> **Amends:** [ADR-0014](0014-scope-game-simulation.md) (adds a sixth simulation phase after its five), [ADR-0016](0016-pipelined-simulation-phases.md) (its static gate, for this phase only)
> **Related plan(s):** [0052-monster-ai](../plans/0052-monster-ai.md) (phase (5), the gate); [0048-seed-to-world](../plans/done/0048-seed-to-world.md) (the creation-side composition this mirrors)

## Context

ADR-0014 opens simulation in five phases; phase (5), monster AI, is plan 0052, and the owner ruled on 2026-10-27 that
anything beyond the remaining plan 0038 and 0046 tails needs a scope ADR, ready before 0052's harness phase so that
the static lanes and the archivist do not go idle while it waits on 0050·P3. The three priority areas of the project
are reviewed: every core row of the [research map](../specs/README.md) (items, monster spawning, DRLG) is `reviewed`,
and their remaining `[I]` are plan 0038's. Plan 0048 composed them from the game seed to a populated world
([chain](../specs/chain/README.md), C 89 / I 7 / L 6).

Simulation has no such composition. Each phase reproduces **events** and, by ADR-0014, may take an event's entry seed
as a logged input when the draws before it belong to code out of scope. Those resynchronised entries are the largest
weakness ADR-0014 names, and the runs show their size: at a skill start or do, the caster's seed equals its previous
exit in 3 155 of 3 459 consecutive pairs of plan 0045's first run; over both its runs, 135 of 281 player gaps could be
walked draw by draw and 331 monster gaps were left to the AI ([skills/dispatch § P1](../specs/skills/dispatch.md#p-draws-and-seeds-per-event-kind)).
Plan 0052 explains a monster's own draws; what it does not explain is **the order** in which one frame visits rooms,
units, missiles, the event queue and the timers, which decides whose draws come first on any seed two units share
(the game seed of a drop or a summon, a defender's seed hit twice in one frame).

That order is barely specified. [drlg/lifecycle § A](../specs/drlg/lifecycle.md#a-the-frame) gives `GameTick` at `[I]`
with "two per-frame passes", "unit events" and "two more passes" unnamed; plan 0050 named the event queue
(`sub_005415E0_EventQueueEveryFrame`, `sub_005416B0_EventQueueAt`, `SUNIT_ScheduleModeEvents`) without a frame-level
model; the quest timers run on `frame mod 20` (`QUESTS_TimersRun`, `[C]`). The chain spec's last `[L]` says a
log-free world build "would need the activation order as an input record". The remaining `[I]` of the simulation and
game-rules specs (1 087 against 829 `[C]` over their eight reviewed rows, 2026-10-27) are not in plan 0038's inventory,
which predates them.

## Decision

Simulation gains a **sixth phase, the server frame**, opened by its own plan in the order of ADR-0014: the game tick
(`GameTick` and every pass it makes), the per-unit update order and its lists (players, monsters, objects, missiles,
items, the inactive units), the event queue and the mode events it fires, the timers (quest, room release, level
unload, the item sweep), and the room activation order within a frame. Its evidence is ADR-0014's per-event
reproduction with one addition: a **frame window**, a stated run of consecutive frames in a small scene (one player,
a bounded set of units), in which every in-scope event of every unit is logged and every entry seed is asserted,
none resynchronised, so that the composition is checked as plan 0048 checked the creation chain. A window's length and
its scene are in the record; ADR-0014's log-volume rule applies to everything outside windows. The gates follow
ADR-0016 with one change: the plan's tables and static reading may start once **plan 0052's P1.1 (the machinery) is
reviewed**, not its Phase 2, because the static reading consumes only the AI tick, its caller and the unit lists that
P1.1 names; its harness waits, as ADR-0016 requires, for **plan 0052's P3a (machinery and tier) to be reviewed**; the AI catalogue (0052·P3b), the path search plan and plan 0046 never
gate it, and an AI, path or skill function they have not specified is a boundary oracle under ADR-0004 (as ADR-0020).
The research-map row `sim/frame` is added when the plan is drafted. The network protocol, client prediction and
wall-clock pacing stay out (ADR-0014 § Time): the frame is the server's counter.

## Consequences

### Positive

- The resynchronised entries of every earlier phase can be re-checked as chained ones inside frame windows, and the
  kept logs of plans 0037–0052 become test sets for the order model, as the combat logs did for phase (2).
- A reimplementer gets the loop that runs the specified parts, not only the parts.
- Its first phases are tables (the unit lists, the timer periods) and static reading of a few callers of known
  functions; gated on 0052·P1.1's review, they fill the static lanes and the archivist while 0052·P2 waits on
  0050·P3.
- The chain spec's activation-order `[L]` and drlg/lifecycle § A's unnamed passes get an owner.

### Negative

- **The static gate is earlier than ADR-0016's.** If plan 0052's P2 or P3a moves the AI tick or a unit list the
  frame plan's P1 relied on, its static work is partly wasted; the architect re-rules at the frame plan's P1 review,
  as ADR-0016 provides for its own case.

- **Frame windows are per-frame logging.** ADR-0014 keeps the injected logger in reserve for such cases; gdb on every
  in-scope event of every unit for a stated window may still stall the thread enough to change the frames that follow
  (ADR-0003 § Negative). The windows will be short and the scenes small, and a window that cannot be logged whole
  falls back to resynchronised events, which is where we are today. The injected-logger ADR may be needed (plan 0052
  question 3 proposes one ADR for both).
- **It depends on every earlier model at once.** A window chains only if each event in it is modelled; an
  unspecified catalogue function or AI ends the chain at its call (a boundary oracle), so early windows will be
  scenes chosen to avoid them, and the claim is limited to those scenes.
- **Scope grows again.** The research map's "done" point moves out again, for a part with no creation-path
  payoff: the three priority areas gain nothing directly.
- **The order may be partly non-deterministic under wine.** Client messages arrive between frames by wall-clock
  time; the record must take each client message as a logged input, and a claim about message order is out of scope.

### Neutral

- Evidence rules, the tags and ADR-0014's per-event rules are unchanged; a frame window is a stricter case of
  chaining, not a new evidence form.
- Plans 0038, 0046 and 0052's catalogue and path search run beside it; the static lanes take whichever has work.
- If the owner prefers, the sweep in the first alternative below can run as a plan beside this phase without an ADR.

## Alternatives considered

**An inferred-claims sweep over the simulation and game-rules specs, as plan 0038 did for the creation specs.** It
needs no ADR (it is inside the scope ADR-0014 and ADR-0017 set) and has a large target (1 087 `[I]` over eight rows,
quests/progression alone 322), but it lost as *the next scope* because most of those `[I]` are draw-order claims that
stay `[I]` for exactly the reason this ADR addresses (resynchronised entries); a sweep before the frame is composed
would raise the tables and arithmetic and leave the draw order where it is. It remains the recommended companion plan
for the harness slots once 0038's batches drain.

**Player-side game rules (item use from the belt and inventory, pickup and the ground drop's placement, corpses,
death and respawn, the stash).** It would be an ADR-0017-style extension and closes visible gaps (save/d2s's ground
positions are `[L]`), but it lost because those rules are mostly client requests the server checks one at a time,
which per-event reproduction already handles plan by plan; they gain little from a new phase, and less than the
frame order does for every phase already specified.

**Stop at phase (5).** The deliverable would then be complete for its stated aim, with the resynchronised entries as
a named limit. It lost because the cost of the frame phase's static work is low and it is the one piece that turns the
phase specs into a runnable server loop; the owner may still choose it, in which case the lanes finish 0038, 0046 and
0052 and the project closes.
