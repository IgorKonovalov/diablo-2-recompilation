# ADR-0014 — Game simulation enters scope, in five phases, with per-event reproduction as its evidence

> **Status:** accepted
> **Date:** 2026-10-16
> **Amends:** [ADR-0002](0002-scope-creation-paths-and-enablers.md) (its deferral of game simulation; presentation formats stay as ADR-0005 left them)
> **Related plan(s):** [0037-combat-formulas](../plans/0037-combat-formulas.md) (the first simulation plan)

## Context

[ADR-0002](0002-scope-creation-paths-and-enablers.md) kept "game simulation and presentation formats" out of scope
until at least one item spec was reviewed. That condition has been met many times over: every core, enabler and
creation-path row of the [research map](../specs/README.md) is `reviewed` except `items/quest-drops` (plan 0032, in
progress). The owner has decided to bring simulation in. The creation specs already stop at its edge in several
places, each recorded as an open question:

- [monsters/stats § H](../specs/monsters/stats.md#h-to-hit-and-damage-at-attack-time-reference-only) gives the
  attack-time to-hit and damage of a monster as reference only, `[I]`, with draws on the unit seed during combat;
- [player/creation](../specs/player/creation.md) takes `UnitGetMaxHp/Mana/Stamina` with item bonuses as named value
  inputs, because how the bonuses add up is not part of it;
- [data/calc](../specs/data/calc.md) evaluates the skill and missile formulas but leaves what they compute in combat out;
- the backlog holds a contradicted community claim that waits for a combat plan (CharStats `ToHitFactor`: a level
  bonus in the community account, an attack-rating term in 1.14d's `sub_00622560_PlayerBaseToHit`).

Simulation differs from everything specified so far in how it can be checked. A creation path is a one-shot function:
given a seed and its inputs, it runs to completion, and a model replays it draw for draw (ADR-0003, ADR-0004). Combat,
skills, states and AI run once per game frame, over time, on many units at once. Their draws interleave with the AI
and movement of every other unit, and under wine the frame on which an event happens depends on wall-clock timing and
on how long each breakpoint stalls the thread ([ADR-0003](0003-runtime-experiments.md) § Negative, "Throughput and
timing"). A session can't be replayed frame for frame, and logging every frame would produce logs no checker could
use. ADR-0004 makes the entry-seed assertion mandatory, but in simulation the draws made on a seed between two
in-scope events usually belong to code that is out of scope at that point (another unit's AI, or a skill not yet
modelled).

Combat is also the most heavily documented part of the game in the community (Arreat Summit, Amazon Basin and Phrozen
Keep guides, calculators, forum threads), and much of that folklore was derived from 1.09 and 1.10 code, so its
numbers and formulas may not hold for 1.14d.

## Decision

**Scope.** Game simulation enters scope in five phases, each opened by its own plan in this order: (1) **combat
formulas** (to-hit, physical and elemental damage, resistances and their caps, block, avoid and evade, crushing blow,
deadly strike, open wounds, life and mana leech, damage reduction and absorb, monster against player and player
against monster, the difficulty penalties); (2) **stats and states** (how item, skill, aura and state bonuses
aggregate into a unit's final stats, including `UnitGetMaxHp/Mana/Stamina`); (3) **skills and missiles** (skill
dispatch, missile creation and motion, on top of `data/calc`); (4) **monster AI** (and the pathing it drives);
(5) **animation timing** (`animdata.d2`, attack and cast rates, hit frames, as frame counts). A later phase's plan is
written only once the earlier phase's spec is reviewed. The architect may reorder phases 3–5 by plan, not by ADR. The
network protocol, sound, fonts, video, rendering and input handling stay out. Presentation formats stay tools-only
([ADR-0005](0005-presentation-formats-tools-only.md)): timing comes in as frame counts and hit frames, and animation
playback does not.

**Evidence: per-event reproduction.** A simulation claim reaches `[C]` by reproducing **events**, never whole frames
or sessions. An event is one call of a named in-scope entry point (for example one attack resolved against one target,
or one damage-over-time tick). For each logged event the experiment records, at that boundary: the inputs the Phase 1
finding names (each stat value the formula reads, the attacker's damage packet, the difficulty, the game type, the
frame number where the claim depends on it), the state of every seed the event draws on, on entry and on exit, and the
event's outputs (hit, block or avoid, the damage per type after each reduction, the life and mana changes, any state
applied and its duration). The model predicts every draw and every output from the logged inputs, and **asserts the
logged exit seed**: the exit assertion checks the draw count, and the outputs check the ranges and the arithmetic.

This changes [ADR-0004](0004-boundary-oracles-in-reproduction.md) in one respect, for simulation only. The entry seed
of an event may be a **logged input** instead of an asserted prediction, provided the draws before it on that seed are
out-of-scope simulation. Two in-scope events in a row on the same seed are **chained**: the second event's entry is
asserted against the first one's predicted exit. The checker reports how many events it chained and how many it
resynchronised, and a resynchronisation without an exit assertion proves nothing, as ADR-0004 says. Stat values read
from the unit are **value oracles**, as data/calc's review ruled for plan 0035: logged, named in the record and taken
as given. A `[C]` covers the formula between the inputs and the outputs, not how the inputs came to be. When a later
phase's plan delivers a model of an oracled input (the stats and states aggregation for the stat values, the skills
plan for a skill's damage packet), it re-runs the kept logs with that oracle replaced, where the logs hold what its
model needs.

**Time.** Every timing claim is stated in **game frames**, as the frame counter the server code reads. Durations
(open wounds, cold, freeze, poison, regeneration) are checked from the logged frame numbers at the start and at the end
of the state. No claim is made about wall-clock time, frame pacing, catch-up frames or the client's prediction.
Only server-side outcomes are evidence. A client-side display value (the character screen's chance to hit, damage
numbers) is presentation. It counts as a second code path (evidence rule 1) only when the client computes it in a
separate function.

**Log volume.** A run bounds its logs. No breakpoint goes on a per-frame path (the frame loop, the RNG step, the stat
recompute) except in a window whose length the record states. Breakpoint conditions filter events to those involving
the logged character or its target. A session stops logging an event kind once it reaches the cap the plan sets for
that kind. A stat is read at an event only if the finding names it as an input of that event's formula. The record
states the event counts per kind and the log sizes. A session is not repeatable, so its raw log is kept in
`workspace/logs/` with a manifest hash for as long as any `[C]` cites it.

**Multiplayer.** Combat code is written for a server with several clients. Single-player runs (with `/players N` for
player-count scaling) back `[C]` for everything they reach. Player against player and hostile states need two clients
([ADR-0008](0008-two-client-harness.md), still proposed): until ADR-0008 is accepted, those branches are read from the
code and stay `[I]`.

**Sources.** The sources policy is unchanged ([ADR-0001](0001-target-toolchain-evidence-sources.md),
[ADR-0007](0007-fetched-leads-only.md)). Community combat documentation is used as leads, registered in
`docs/sources.md` with the game version it describes, and compared blind with a verdict per claim
(evidence-rules § Community cross-checks). Combat is held to the items standard: cross-checks are expected, every
`contradicted` verdict reachable on stock data becomes a required harness case, and agreement promotes nothing. A
calculator is used only through its prose and stated formulas. Its source code is third-party code and is not read,
and its outputs are not evidence.

## Consequences

### Positive

- The open edges of the reviewed specs (monster attack stats, the item-bonus maxima, what the calc formulas compute)
  get a home, and a reimplementer gets a game and not only a world generator.
- Per-event reproduction keeps the project's standard: every draw and every output of an in-scope event is checked
  against the binary, without replaying sessions that wine can't replay.
- The phase order lets each phase oracle the next one's inputs, so combat formulas can reach `[C]` before stat
  aggregation exists, as the creation plans did with ADR-0004.
- Stating time in game frames keeps wine's pacing out of every claim.

### Negative

- **Resynchronised entry seeds weaken the check.** A resynchronised event proves its own draws, not that the
  in-scope code drew nothing between two events. An extra draw in a path that only ever runs just before an
  out-of-scope draw would go unseen. Chaining reduces this and the checker reports it, but a phase can reach `[C]`
  with most events resynchronised.
- **Log size and harness time.** A pack fight produces dozens of events per second. Each one stops the thread for
  gdb's Python handler and several stat reads, and the pause changes the fight itself (monsters act in the frames
  the game catches up). Caps and filters bound the logs, but reaching the rarer branches (crushing blow on a boss,
  open wounds ending a monster, a capped resistance) takes many sessions. Combat sessions also risk the character's
  death, which ends the session, because breakpoints never write memory (ADR-0003).
- **No session is repeatable.** A mismatch can't be re-run identically. The kept log is the only evidence of it, and
  the logs grow over the phases.
- **Value oracles hide input errors.** If a stat's identity or encoding is wrong (a shifted value, a stat read from
  the wrong list), the formula model can still pass on the logged values while the stats claim is wrong. Input
  identities stay `[I]` until the stats and states phase consumes them.
- **Combat is multiplayer-shaped.** Player against player, party effects and hostile states stay `[I]` while
  ADR-0008 is proposed. Single player runs server and client in one process, so breakpoints in shared code fire for
  both and the checker has to tell them apart.
- **Scope and cost.** Five phases at the current pace is a large amount of reverser work. Skills (phase 3) alone cover
  some 350 skill rows with hardcoded per-skill functions. The research map's "done" point moves out again, and the
  creation rows keep their place at the top of the map so that it stays visible.
- **Folklore pressure.** Community combat numbers are plentiful and confidently stated. A finding that agrees with
  them gains nothing, and a reviewer has to check that no number entered a spec from a lead.

### Neutral

- Evidence rules 1–3, the tags and the anchor forms are unchanged. Per-event reproduction is an operational reading of
  rule 4 for simulation, as ADR-0004 is for creation paths. ADR-0004 still governs creation paths unchanged.
- Forced-path runs ([ADR-0013](0013-forced-path-runs-cell-level.md)) apply as written. Tool-built saves with stock
  affixes (its Neutral section) are the normal way to give a test character a combat stat.
- Research-map rows are added when each phase's plan starts, under a new **Simulation (ADR-0014)** band. The
  expected rows are `combat/formulas` (plan 0037), `stats/aggregate`, `skills/dispatch` and `skills/missiles`,
  `monsters/ai` and `anim/timing`. Each plan may split or rename its row.
- Plans 0032 and 0036 run before any simulation plan.

## Alternatives considered

**Replay whole sessions from a recorded input stream.** It lost because the game's frame pacing under wine depends on
wall-clock time and on breakpoint stalls, so the same inputs don't produce the same frames, and a mismatch late in a
session could not be localised to a formula.

**Keep ADR-0004's mandatory entry assertion and model everything drawn between events.** It lost because that pulls
AI, movement and every skill into the combat plan, the scope creep ADR-0004 was written to avoid. Combat would wait
for all five phases before its first `[C]`.

**An injected logger instead of gdb for the hot paths** (ADR-0003's reserve). It lost for now because per-event
breakpoints with filters and caps keep the logs bounded without putting our code in the process. It stays in reserve,
behind its own ADR, if a phase (likely AI or missile motion) needs per-frame observation.

**Stats and states first, then combat.** It lost because the owner wants combat formulas first, and value oracles let
combat be checked before aggregation is modelled. Aggregation then has a ready test set in the kept combat logs.
