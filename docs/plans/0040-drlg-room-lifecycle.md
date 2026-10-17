# 0040 — Room lifecycle: activation, release, the inactive-unit restore and the wanderers

> **Status:** approved (owner, 2026-10-16; unattended)
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
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038.

- **2026-10-17 — Phase 1 and Phase 1b done (reverser, `lane/p40r`, static).** No game run, no slot; Ghidra on the lane's
  copy, objdump and r2 for the instruction-level reads. Finding: [drlg/0009](../findings/drlg/0009-room-lifecycle.md)
  (46 `[I]`, 0 `[C]`, 14 `[L]`: 8 lead verdicts and 6 open questions). 47 symbols added (45 functions, 2 data, subsystem
  `drlg/lifecycle`); types in `re/types/lifecycle.h` (views of the active and DRLG room, the four inactive records).

  | Done-when item | Answer | Anchor |
  |---|---|---|
  | activation | a reference count per DRLG room at near-list distance 0..3, moved by `ClientRoomChange`; gaining distance 1 activates (`RoomActivateA`), 2 sets status 2, 3 loads the files; the new rooms are populated or restored at the start of the next frame; the server activates the near list of each client's room, the union over clients; the client act also builds one status-2 room every 5 ticks and releases at status 4 | drlg/0009 § 2, § 3 `[I]` |
  | `RoomActivateA`/`B` | A: neighbour step, re-seed, type init, `DRLG_RoomActivate`, act counters; B: the on-demand variant (DT1 list and DS1 too, no-op when built), used by warps, waypoints, level points, preset level build; its rooms get no reference | § 2 `[I]` |
  | release | every 12th frame; the 11th client-free pass in a row (room `+0x78` = 0), if not portal-pinned (`0x400000`), status ≥ 2, and in towns and level 120 every room of the level at status ≥ 2: **120–131 frames** after the last client's room change; frees the active room, unlinks it from the neighbours, `RoomTilesRelease(EDX 1)` through the wrapper, `DUNGEON_RoomFree` | § 4 `[I]` |
  | `0x200000`, `EDX ≠ 0` | set iff the tiles were freed with the active room (the wrapper passes the negation of its `EDX`, called only by `ActiveRoomFree`); no reader found; corrects drlg/room-tiles' wording ("with the act's `+0x50`") | § 4 `[I]` |
  | inactive records | monsters (0x5C), units (0x34: objects, type 5, kept player corpses), items (serialised bytes + expiry) under one room record per released room, oldest first; the monster save rule (eight tests, one room draw per mode-12 monster, `low mod 3 = 0`), objects § B4 confirmed with its level flag named (`Levels.SaveMonsters`), items always, missiles freed | § 5 `[I]` |
  | restores | monsters (saved unit id, `MonSpawnTry` / `SpecialMonPlace` / `MinionRestore`, then stats 13 and 7 from the record, stat 6 = saved life within 7500 frames else the maximum, stat 12 not written), then items (`ItemCreateFromSave`: game-seed draw, saved seed kept, expiry `max(saved, frame + 15000)`), then objects § 13.5; `0x0061A4D0` = active-room flags bit 1 ("restored", once per activation); room `+0x78` = clients whose near set holds the room | § 3, § 6 `[I]` |
  | wanderer tick | room draw, `low & 0x7FFF = 0`, `+0x78` = 0, `MonWndr`; roll `low mod 100 < 3` and region `+0x2C4` < 3; act I list (270); target list 8 | § 7 `[I]` |
  | preset questions | the server's `PresetUnitSpawn` moves the DS1 path into the monster (zeroing it); a re-activated room never re-dispatches its preset list | § 8 `[I]` |
  | seed consumers | release: one room draw per dead monster; walk: the tick, then the restore's monster, item and object draws in that order | § 9 `[I]` |
  | boundary | event entry points, models and oracles | § 10 (recommendation; the architect rules) |

  **Surprises.** (1) A dead champion is saved (1 in 3) and restored **alive** by `SpecialMonRestore` (mode 1). (2) A
  record with flag `0x400` (target lists 8 and 9; wanderers are put in list 8) is dropped at the restore when its
  alignment is good or neutral, and reaches the fatal error `0x691` when evil. (3) `RoomActivateB` rooms carry no
  reference, so only the idle timer releases them; with `+0x78` = 0 they are the rooms where wanderers can appear.

  **Phase 1b.** Searched for area reset, respawn, healing after leaving and wandering monsters; registered
  `src:pk-boss-heal-thread` and `src:d2io-pmh-thread`, re-read `src:d2dfg-blizzard` (Levels, monstats2, objects).
  8 verdicts: 2 held, 4 held with refinement, 1 not covered, 1 **contradicted** (`SaveMonsters` 0 leaves monsters
  "injured": in 1.14d a non-preset monster of such a level is freed at the release). The contradicted case is not
  reachable on stock data (only the towns and the Harem have `SaveMonsters` 0), so it is not a required Phase 2 case;
  backlog entry filed for the ruling.

  **P2 harness questions** (what Phase 2 must log and check; the logger needs the frame counter `game +0xA8` on every line):
  1. *Release timing:* every `ClientRoomChange` (`0x00537B50`: client, old and new room), every idle count
     (`0x0052D276` return) and test (`0x0052D284`), every free (`0x0052D2BB`): the model predicts each release frame
     (11 passes, 120–131 frames), the town and level-120 rule and portal pins (`0x0061BAC0`).
  2. *References and activation:* `DrlgRefMove` and the enter/leave callbacks (`0x00744384`/`0x00744394` targets): the
     model predicts refs, status and every activation; `RoomActivateB` activations logged as inputs.
  3. *Client lists:* `0x0061A660`/`0x0061A700` (room, client, count): `+0x78` per room.
  4. *Save rule:* at `0x0052D2A9` per unit: type, class, mode, dead flag, `+0xC4`/`+0xC8`/`+0xD0`, alignment, `udead`
     states, owner, region; the room seed in and out of `0x00543260` (the mode-12 draw): predict save, keep or free.
  5. *Records:* the fields at the exits of `0x005421A0`, `0x00542E10` (`0x00542E30`) and `0x00541B10`.
  6. *Restores:* per record at `0x00542563` and the creation calls (`0x00542689`, `0x005426C3`, `0x005426E9`): unit id
     reused, the game-seed draw of `SUnitCreate`, `MonsterInit` through the monsters/stats model, stats 6, 7, 12, 13 at
     `0x00542809`–`0x0054284A` and after; both sides of the 7500-frame rule (a revisit under and over 7500 frames);
     specials and minions through the monsters/special model; items at `0x00541AE8` (expiry, seed, the game-seed draw,
     socketed children, position); objects § 13.5 again.
  7. *A dead champion restored alive* (§ 6): a champion killed, its room released and restored. Rare; a shortfall is
     named.
  8. *A saved wanderer:* the record flags (`0x400`, alignment) and the outcome (dropped or the fatal `0x691`).
  9. *The wanderer gate:* the tick on every room of every walk, with `+0x78`; ≥ 200 gated updates, ≥ 30 spawns.
  10. *`0x200000`:* set on every server release and on the nested client release only.
  11. *The preset path:* preset unit `+0x10` before and after `PresetUnitSpawn` (`0x0055596C`), server and client copies.
  12. *Region counts* before and after `MonRegionUnitLeave` at a restore (`0x00542954`).
  13. *Level 108:* the drop rule while quest 23's byte `+0x13` is set, if a session reaches it (not required).

  **Points for the review.** (a) Everything is `[I]`; the release timing and the seed consumers are stated in frames and
  draw sites, ready for Phase 2. (b) The two surprises of the monster restore (dead champion alive; flag `0x400`
  dropped or fatal) rest on instruction-level reads (0x005432EF–0x00543303, 0x005425F7–0x0054260B,
  0x0054287F–0x0054288E). (c) The correction to drlg/room-tiles (the wrapper negates `EDX`) and the naming of objects
  § B4's level flag (`Levels.SaveMonsters`). (d) The contradicted lead and its stock-data reachability.
