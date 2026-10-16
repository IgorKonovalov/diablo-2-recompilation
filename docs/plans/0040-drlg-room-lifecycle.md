# 0040 — Room lifecycle: activation, release, the inactive-unit restore and the wanderers

> **Status:** proposed
> **Created:** 2026-10-16
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0015-emulated-reproduction

## TL;DR

**Question:** as players move, which rooms does the server activate and release, and when; what does it keep of the
monsters, objects and ground items of a released room; how does it re-create them when the room comes back, with
which seeds and draws; and when does a populated room spawn a wandering monster? When it is done:
- `docs/findings/drlg/0009-room-lifecycle.md` names the activation and release rules, the inactive records per unit
  type, the restore paths for monsters, special monsters and their minions, objects and items, and the wanderer tick;
- `tools/rooms.py` reproduces the release and restore events of a run, and the wanderer rolls, under ADR-0004;
- `docs/specs/drlg/lifecycle.md` is drafted and reviewed; the restore oracles of objects, monsters/spawn and
  monsters/stats are replaced by the model where the run reaches them.

This is creation-path work (ADR-0002): a restore re-creates monsters and objects through the code the reviewed specs
describe, so a reimplementation that skips it gives a different world after the first walk back.

## Context

- Every reviewed creation spec stops at this edge:
  - [objects § B](../specs/objects/README.md) models the object restore on a revisit (`[C]`, 548 re-creations), but
    the save side (§ B4) is `[I]`, and the monster and item restores are "not modelled here";
  - [monsters/spawn](../specs/monsters/spawn.md) takes the room seed at pass entry from the window, and leaves room
    `+0x78` and `0x0061A4D0` (when a populated room restores) as open questions; the wanderer roll and spawn were never
    reached;
  - [monsters/stats](../specs/monsters/stats.md) takes a re-created monster's stats 7, 12 and 13 from the log
    ("the restore code was not read");
  - [monsters/special](../specs/monsters/special.md) lists the inactive-restore paths of special monsters as unreached;
  - [drlg/room-tiles](../specs/drlg/room-tiles.md) leaves room release and re-activation code-only, with the meanings
    of `0x200000` and `EDX ≠ 0` open; [drlg/preset](../specs/drlg/preset.md) asks who detaches a preset monster's path
    between two room prepares and whether a re-activated room gets its added units twice;
  - [drlg/collision](../specs/drlg/collision.md) takes the near list at activation as an input;
  - plan 0038 defers objects row 5 (the revisit monster and item restores) to "the monsters/spawn and items restore
    models".
- **Code already named** (grep `re/symbols.csv`): `DRLG_RoomActivate` (C), `sub_0061B190_RoomActivateA` and
  `sub_0061B730_RoomActivateB` (I), `sub_0052D160_NewRoomsUpdate` (C), `sub_0052D240_RoomsDeactivate` (I),
  `sub_005433F0_InactiveUnitSaveTest` and `sub_00542E30_InactiveUnitSave` (C), `sub_005418C0_InactiveRecordTake`,
  `sub_00541AC0_InactiveItemsRestore`, `sub_005424F0_InactiveMonstersRestore` (I),
  `sub_00542B40_RoomInactiveUnitsRestore` (I; `[C]` for objects in the objects spec),
  `sub_005A4440_SpecialMonRestore` and `sub_005A46E0_MinionRestore` (I), `sub_00642390_LevelRoomStateRestore` (C),
  `sub_0066B4C0_RoomReleaseWrap`, `sub_0066C100_RoomFree`, `sub_0066F1A0_RoomTilesRelease` (C), `DUNGEON_RoomFree` (I);
  the save lists `0x00541B10` (items) and `0x005421A0` (monsters).
- **The game seed at run time.** [rng/seeds](../specs/rng/seeds.md) leaves open the order of the game seed's consumers
  after game creation's first five draws. The restores, the wanderer roll and the item restores are among them. This
  plan lists the consumers it meets; a full census is not its goal.
- Data: `Levels` `MonWndr` (documented); `Objects` `Restore` and `RestoreVirgins` (documented); MonStats columns a
  restore reads, if any, are named by Phase 1. No table phase is planned; Phase 1 files a backlog entry to the
  archivist if a column has no doc.
- Harness: `d2pilot.py` walks and fights (`explore --walk --melee`); the objects logger already sees the object
  restore. Walking out of a room's range and back is a matter of steps files; nothing new is needed to reach the
  events, except time for the release (Phase 1 finds the rule).
- Leads: search for community notes on monster "reset" and respawn when leaving an area, and on wandering monsters
  (`MonWndr`); register them before use.

## Phases

### Phase 1 — Read activation, release, the restores and the wanderer tick
- **Owner skill:** reverser
- **What:** read the room driver from activation to release and back, the inactive records of every unit type, the
  restore paths, and the wanderer tick.
- **Outputs:** `docs/findings/drlg/0009-room-lifecycle.md`; `re/symbols.csv` rows (subsystem `drlg/lifecycle`);
  `re/types/` additions (the inactive record per unit type, the room's lists and flags it touches).
- **Done when:** the finding states, each with addresses and `[I]` or better:
  - **activation:** which rooms a player's position activates (the range, the act's room lists, the near list), on
    which frame, client and server told apart; what `RoomActivateA`/`B` add to `DRLG_RoomActivate`;
  - **release:** when a room is released (distance, a timer in frames, the player count), what is freed
    (`RoomTilesRelease`, the collision grid, the unit lists), and the meaning of room-tiles' `0x200000` and `EDX ≠ 0`;
  - **the inactive records:** for monsters, special monsters, minions, objects (objects § B4 confirmed or corrected) and
    ground items: the save test, the record fields, the order, and what is lost (life, mode, a corpse, a summon);
  - **the restores:** for each unit type, the re-creation path, every draw on every seed (unit, room, game,
    object-region), the fields written back, and stats 7, 12 and 13 of a re-created monster; the special monster and
    minion restores; the item restore (does an item get a new seed, or its saved one); when `0x0061A4D0` lets a
    populated room restore, and room `+0x78`;
  - **the wanderer tick:** its gate (`MonWndr`, the room seed test of monsters/spawn, room `+0x78`), its draws, its
    pick, its spawn;
  - **the preset questions** of drlg/preset: who detaches a preset monster's path between prepares; whether a
    re-activated room's added units come twice;
  - **game-seed consumers** met on these paths, in order;
  - **the boundary recommendation** for Phase 2: the event entry points, the oracles (unit creation through the
    reviewed models, AI and movement of the restored monsters as boundary oracles), the breakpoint sites. The architect
    rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register documentation of area reset, monster respawn and wandering monsters; compare
  blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  **1 slot**, 2 allowed when the queue leaves one free; given in the prompt)
- **What:** write `tools/rooms.py` (model and `check`), `tools/gdb/rooms.gdb` and its handler, and steps files that
  walk out of a room's range and back after killing part of a pack, operating objects and dropping items; log a run.
- **Evidence:** a release and a restore are one-shot functions per room (ADR-0004): the room's seeds are asserted on
  entry and exit, every re-created unit chains to the reviewed model of its type (`tools/monspawn.py`,
  `tools/monspecial.py`, `tools/monstats.py`, `tools/objects.py`, the item chain) or is a named boundary oracle. The
  release time is checked in game frames from the logged frame counter.
- **Done when:** `run:YYYY-MM-DD-rooms` reproduces with **0 mismatches** over at least:
  - 300 room releases and 200 re-activations with a restore, in at least three acts, two difficulties, one maze and one
    outdoor level, and a classic game;
  - 400 monsters restored (at least 40 champions, uniques or minions, and 30 that were damaged before the release), with
    stats 7, 12 and 13 predicted rather than logged;
  - 150 objects restored (at least 30 operated before the release), confirming objects § B4;
  - 60 ground items restored, with their seeds and fields;
  - 30 wanderer rolls that spawn, and the wanderer gate in at least 200 room updates;
  - the Phase 1b cases.

  A rare branch (a minion restored without its boss, a corpse, a summon) that falls short is named with its count in
  the record and stays `[I]`; it does not block. In-scope claims go to `[C]`, citing the run. Plan 0038's deferred
  objects row 5 is re-checked against the run.

### Phase 3 — Spec: drlg/lifecycle
- **Owner skill:** spec-writer
- **What:** write `docs/specs/drlg/lifecycle.md` and link it from the drlg README, objects § B, monsters/spawn,
  monsters/stats, monsters/special, drlg/room-tiles and drlg/preset (their open questions narrowed or closed).
- **Done when:** the spec follows the template, every statement is tagged; it has the activation and release rules,
  the record layouts as tables, each restore as pseudocode with its draw order, the wanderer tick as pseudocode, a
  state diagram of a room's life, and a worked example of one room released and restored from the run. The architect's
  review passes.

## Open questions

- **AI and movement.** A restored monster's AI and path are phase 4 of ADR-0014. Their draws are boundary oracles
  here, as in plan 0037.
- **Multiplayer.** With two players the activation range is the union of theirs; this plan reads it and leaves it
  `[I]` (plan 0044).
- **Timing.** If the release depends on a timer, sessions under breakpoints stretch it; the claim is stated in frames
  from the logged counter (ADR-0014 § Time applies by analogy).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`.
