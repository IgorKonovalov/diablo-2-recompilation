# ADR-0020 — Simulation phase 3 (skills and missiles) in two plans: the machinery, then the function catalogue

> **Status:** accepted 2026-10-20 (owner)
> **Date:** 2026-10-20
> **Amends:** [ADR-0014](0014-scope-game-simulation.md) (what "the phase's spec is reviewed" means for phase 3), [ADR-0016](0016-pipelined-simulation-phases.md) (which P2 opens phase 4)
> **Related plan(s):** [0045-skills-missiles-machinery](../plans/done/0045-skills-missiles-machinery.md), [0046-skills-function-catalogue](../plans/0046-skills-function-catalogue.md)

## Context

ADR-0014 opens each simulation phase with "its own plan", and gates the next phase on that phase's spec being
reviewed; ADR-0016 lets the next phase's tables and static reading start once the previous phase's Phase 2 run is
accepted. Phases 1 and 2 each fitted one plan (0037, 0041). Phase 3 does not. Skills.txt has 357 rows; `srvstfunc`
takes 64 distinct values, `srvdofunc` 138 ([Skills](../tables/Skills.md), the `srvstfunc` and `srvdofunc` rows), and
the progressive functions, the 684 Missiles rows and their server do, hit and damage functions come on top. ADR-0014's
own Negative section already names this ("some 350 skill rows with hardcoded per-skill functions").

Two things in phase 3 differ in kind. The **machinery** (the start and do dispatch, mana, delay and cooldown, the
damage packet a skill builds, missile creation, motion, collision and hit, the stat-event handlers, summons, the
re-seed sites of [rng/0002 § Plan 0039 batch P1a](../findings/rng/0002-seed-tree.md#plan-0039-batch-p1a-2026-10-16))
is shared by every skill and is what combat, stats, data/calc, rng/seeds and items/economy are waiting on as value or
boundary oracles. The **function catalogue** (what each of some 200 numbered functions does: which states, which
missiles, which units, which draws) is long, mostly independent per function, and better suited to static reading and
emulation (ADR-0015) than to scripted play, which casts few targeted skills
([harness-play](../../.claude/skills/reverser/references/harness-play.md)).

Read literally, ADR-0014 would hold monster AI (phase 4) until every one of those functions has a reviewed spec, and
ADR-0016 would hold phase 4's table work until the catalogue's harness run is accepted, although AI needs the
machinery (how a monster's skill use is dispatched) and not the catalogue.

## Decision

Phase 3 is delivered by **two plans**. Plan 0045 (**machinery**) specifies the dispatch, the packets, missile
creation, motion, collision and hit, the event handlers, summons and the re-seed sites, with a named tier of
representative skills reproduced per event; plan 0046 (**catalogue**) specifies every numbered skill and missile
function, from the code with its draws listed, raised to `[C]` by emulation (ADR-0015) or by harness events where a
representative of its family is reachable. For the gates, **phase 3's P2 is 0045's P2** (ADR-0016: phase 4's
table and static phases may start once it is accepted) and **phase 3's reviewed spec is 0045's** (`skills/dispatch`
and `skills/missiles`; ADR-0014: phase 4's harness phase and phase 5's plan may follow it). Plan 0046 runs beside
phase 4 and never blocks it. A catalogue function that phase 4 or 5 needs and 0046 has not specified is taken by that
plan as a boundary oracle under ADR-0004, named in its spec, exactly as earlier phases took later phases' inputs.

## Consequences

### Positive

- The oracles the reviewed specs carry for skills (a skill's packet and `SrcDam`, a missile's packet, the event
  handlers, `MonAttackStats`, `PLAYER_UseAmmo`) are replaced by one plan of normal size, as soon as possible.
- The catalogue gets a method that fits it: static reading in batches, emulation for coverage, harness only for a
  sample per family, so the harness slots are not spent on 200 functions.
- Monster AI is not held back by functions it does not call.

### Negative

- **Two plans edit one spec directory.** `docs/specs/skills/` is written by 0045 and extended by 0046. Merges go one
  at a time, the machinery first, and 0046's P3 cannot change a 0045 statement without that statement's own review.
- **A reviewed phase with an unfinished catalogue.** A reader of the research map sees phase 3 "reviewed" while many
  per-skill rows are `[I]` or not yet specified. The map keeps a separate row for the catalogue so this stays visible.
- **More boundary oracles in phase 4.** An AI that uses a skill whose function the catalogue has not reached logs that
  function's outputs as an oracle, and its `[C]` covers only the AI's choice.
- **Representative bias.** The machinery's `[C]` is earned on the tier-A skills; a function family whose members use
  the machinery differently (an unusual missile loop) is found only when 0046 reads it, and may reopen a 0045
  statement.

### Neutral

- Evidence rules, ADR-0014's per-event evidence, the chaining floors and ADR-0015's conditions are unchanged.
- The architect may still reorder phases 4 and 5 by plan (ADR-0014). On accepting this ADR (2026-10-20) the owner
  set the order: **phase (4) is animation and frame timing, phase (5) monster AI**, since skill and combat timing need
  frame counts first. That is a plan-order choice under ADR-0014, recorded here, not part of this decision.

## Alternatives considered

**One plan for all of phase 3.** It lost because its Phase 1 would be several weeks of static work before any spec,
its Phase 2 would need far more sessions than two slots give, and every reviewed spec waiting on skill packets would
wait for the last per-skill function.

**One plan per character class.** It lost because the machinery is shared: each class plan would re-read the dispatch
and the missile code, and the first one would carry the whole machinery review anyway. Classes remain the natural
batch unit inside plan 0046.

**Leave ADR-0014 as written and scope phase 3 to the machinery only, dropping the catalogue.** It lost because a
reimplementation needs each skill's effect; without the catalogue the deliverable could create every item and monster
but not resolve most skill uses.
