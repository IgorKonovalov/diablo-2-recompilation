# ADR-0002 — Scope: every item and monster creation path, plus the systems the core depends on

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0001-bootstrap (unchanged); later plans are ordered by the research map

## Context

ADR-0001 sets the goal as seed-for-seed reimplementation of item creation, monster spawning and
level generation. The research map lists 15 subsystems under those three headings. Once the
extracted data was surveyed (97 excel tables in `workspace/merged/`, `data/global/tiles/`,
`data/local/lng/`, `animdata.d2`), two gaps showed up:

1. **The core can't be reproduced without some systems the map leaves out.** Monster and object
   placement checks room collision, and collision is built from DT1 tiles laid out by DS1 presets.
   `[C]` promotion depends on runtime experiments, and those need the `.d2s` save and its item
   bitstream (seed control, checking generated items), as ADR-0001 § Negative already notes.
   Unique monster names are rolled from `uniqueprefix`/`uniquesuffix`/`uniqueappellation` while
   the monster spawns, so they probably consume RNG mid-spawn (a lead from the table structure,
   not yet anchored in code). Which excel form the game reads (`.bin` vs `.txt`) and what the
   `*code.bin` formula bytecode holds are open backlog questions that sit under every
   table-driven spec.
2. **Items and monsters get created by more callers than the three headings name.** Vendors,
   gambling, the Horadric Cube, runewords and socketing, quest drops, object drops and
   hirelings all build items or units through the same machinery. They are new entry points
   into code the core specs will already describe, so covering them costs little extra.
   A reimplementation without them would be visibly incomplete.

Beyond that is full game simulation: combat formulas, skills, missiles and states, the animation
and timing model, monster AI, and the network protocol. Presentation formats (DC6/DCC/COF,
palettes, fonts, sound, video) are beyond that again. They are large, and under the evidence
rules each claim is expensive. None of them is needed to generate the same items, monsters or
maps from the same seed.

## Decision

We extend the scope in two steps and defer the rest. **Enablers** (DS1/DT1 formats and room
collision, `.d2s` and the item bitstream, `.tbl` string tables, the excel loader and the calc
bytecode VM, seed derivation from game to act to level to room) become research-map rows. They
are scheduled as early as their dependants need them, and DS1/DT1 and `.d2s` come first.
**Creation paths** (vendors and gambling, the Horadric Cube, runewords and gems, quest drops,
monster stat realisation, hirelings, character creation and progression) become research-map
rows ordered after the core spec each one calls into. **Game simulation and presentation formats
stay out of scope.** A later ADR may add them once at least one item spec has been reviewed and
accepted.

## Consequences

### Positive
- The DRLG and spawn specs can reach seed-for-seed fidelity because collision is in scope.
- `[C]` promotion gets a concrete path: the `.d2s` harness is planned work, not an assumption.
- Every way an item or monster comes into existence gets one consistent spec, reusing the core.

### Negative
- The archivist's load grows by at least four formats (DS1, DT1, `.d2s`, `.tbl`) before the DRLG
  and spawn specs can close, and DS1/DT1 are not small formats.
- Quest drops and parts of the cube are hardcoded logic with no table behind them. They are
  pure reverser work, and the 1.14d inlining makes them slow to find.
- The map grows from 15 rows to about 27, which pushes back the point where we can say "the
  original three areas are done". The map keeps the core rows first so that point stays visible.
- The boundary is a judgment call. Some creation paths call into combat or skill code (for
  example, cube recipes that check stats, or skill-based item mods). Those calls are specced
  only to the depth the creation path needs, and the rest goes to *Open questions*.

### Neutral
- Evidence rules, sources policy and the 1.14d-only target are unchanged.
- Formats are documented under `docs/formats/` (archivist). The research map lists only the
  *behaviour* built on them (collision, serialisation), plus a prerequisite-formats list.

## Alternatives considered

### Keep the original 15 rows and handle enablers ad hoc inside them
Rejected because collision and the save harness each feed several subsystems. Burying them
inside one row would hide a blocking dependency and duplicate the work.

### Take in game simulation now (combat, skills, AI)
Rejected because it multiplies the reverser's work several times over before a single core spec
has passed review, and seed-deterministic generation needs none of it.

### Enablers only, no creation paths
Rejected because the creation paths reuse core code almost entirely. Leaving them out saves
little, and the spec would have holes a reimplementer runs into immediately (vendors, cube).
