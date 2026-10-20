# 0040 — Room lifecycle: activation, release, the inactive-unit restore and the wanderers

> **Status:** done (approved 2026-10-16, closed 2026-10-17; P1/1b, P2 and P3 accepted with fixes 2026-10-17)
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
  - [objects § B](../../specs/objects/README.md) models the object restore on a revisit (`[C]`, 548 re-creations), but
    the save side (§ B4) is `[I]`, and the monster and item restores are "not modelled here";
  - [monsters/spawn](../../specs/monsters/spawn.md) takes the room seed at pass entry from the window, and leaves room
    `+0x78` and `0x0061A4D0` (when a populated room restores) as open questions; the wanderer roll and spawn were never
    reached;
  - [monsters/stats](../../specs/monsters/stats.md) takes a re-created monster's stats 7, 12 and 13 from the log
    ("the restore code was not read");
  - [monsters/special](../../specs/monsters/special.md) lists the inactive-restore paths of special monsters as unreached;
  - [drlg/room-tiles](../../specs/drlg/room-tiles.md) leaves room release and re-activation code-only, with the meanings
    of `0x200000` and `EDX ≠ 0` open; [drlg/preset](../../specs/drlg/preset.md) asks who detaches a preset monster's path
    between two room prepares and whether a re-activated room gets its added units twice;
  - [drlg/collision](../../specs/drlg/collision.md) takes the near list at activation as an input;
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
- **The game seed at run time.** [rng/seeds](../../specs/rng/seeds.md) leaves open the order of the game seed's consumers
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
- **Owner skill:** reverser (agent-driven per [harness-play](../../../.claude/skills/reverser/references/harness-play.md);
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
  - the wanderer gate's draw in at least 200 room updates (amended at the Phase 1 review: the gate passes 1 in 32768
    and the roll 3 in 100, so spawns are a named shortfall, not a target; the roll and spawn stay `[I]` unless reached);
  - the Phase 1b cases: one hostile pool monster that followed a player into a town room, freed without a record at
    the town's release and absent at the return (amended at the Phase 1 review).

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
  copy, objdump and r2 for the instruction-level reads. Finding: [drlg/0009](../../findings/drlg/0009-room-lifecycle.md)
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

- **2026-10-17 — Phase 1 and 1b review (architect): accept with fixes.** Main (`4d31287`) merged into the lane first.
  Anchors spot-checked with objdump (13, all resolve): the three surprise ranges 0x005432EF–0x00543303 (`MonTypeFlag(unit,
  0x18)` and dead → no save; champion bit not in the mask), 0x005425F7–0x0054260B (flag `0x400` with record bit `0x100`
  or `0x80` → drop) and 0x0054287F–0x0054288E (alignment 2 → list 8, 1 → list 9, else 0x00542990 `push 0x691`, fatal);
  the wrapper's `sete` at 0x0066B4DE and `ActiveRoomFree`'s `EDX = act +0x50` at 0x0061A9D0; the write at 0x0066F232;
  `GameTick`'s `% 20`, `% 12`, `% 11` (0x0052D913–0x0052D949); `n > 10` at 0x0052D27B; the mode-12 draw and `mod 3` at
  0x00543260–0x00543287; the 7500-frame test (`0x1D4C`, unsigned `jb`) at 0x00542819; the wanderer gate `0x7FFF` and
  `+0x78` at 0x0054F089–0x0054F096 and the roll `× 100`, `< 3`, `+0x2C4 < 3` at 0x0054F024–0x0054F041;
  `SpecialMonRestore` → `SpecialMonPlace` with the saved id (0x005A4444–0x005A4460). Data checked: `SaveMonsters` 0 on
  levels 0, 1, 40, 50, 75, 103, 109; `restore` 698/18/18 over MonStats rows; class 270 is `rogue2` (`restore` 1,
  `Align` 1). Gate green; symbols: 47 `drlg/lifecycle` rows, no duplicate address or name; `lifecycle.h` names no
  existing struct. Tags honest: no `[C]` claimed, the `[L]` are leads and open questions only. Two sources registered.

  **Rulings.**
  1. *Release rule and activation:* accepted at `[I]`. The window is 120–131 frames (first client-free pass 0–11 frames
     after the room change, the 11th at +120); the model states it in frames from `game +0xA8`. The per-distance
     reference counts with enter/leave callbacks are the activation model Phase 2 checks (question 2).
  2. *Surprises:* both read as stated. (a) A dead champion is saved (1 in 3) and restored alive in mode 1 through
     `SpecialMonRestore`: holds, `[I]`, a Phase 2 case with a named shortfall allowed. (b) Flag `0x400`: holds, but
     the finding's "good or neutral / evil" named meanings the code does not give; corrected to numeric alignments
     with the MonStats `Align` mapping (0 → 0, 1 → 2, 2 → 1, from MonSpawnTry). The fatal path is reached only by
     alignment 0, since the earlier test drops 1 and 2. The wanderer is `rogue2` (`Align` 1), so a saved wanderer
     is predicted dropped if `SpawnAtPos` applies the same rule: a static follow-up, not a run question.
  3. *Spec corrections:* (a) the negation is right, but the finding's consequence was wrong for the client: the
     H5c counts (626 `EDX` ≠ 0 of 1516 built-room releases, 890 nested client pairs; 626 + 890 = 1516) mean the
     nested client inner call gets `EDX` 0, so the client DUNGEON act's `+0x50` is non-zero and `0x200000` reads
     "released by the server". Corrected in § 4 (`[I]`); the spec-writer entry is amended. (b) objects § B4's level
     flag is `Levels.SaveMonsters` (leveldefs `+0x94`, [Levels](../../tables/Levels.md) `[C]` offset): accepted.
  4. *§ 10 boundary:* accepted as the Phase 2 boundary, with the amendments below. Also logged as inputs: pin set and
     clear (`0x0061AED0`, every site, not only the read ones), `RoomActivateB` activations, `UnitIsDead`, the state,
     owner and pet tests of the save rule.
  5. *Gaps:* none blocks. The client-copy detach is client-side and out of the server lifecycle; it stays an open
     question. The unread fields stay `[L]` open questions. The 31 pin sites: Phase 2 logs the pin flag as an input
     at every release test, so the model needs no reading of the sites; enumerating them is a static follow-up.
  - *Phase 1b contradicted lead:* the verdict stands, settled by the code reading at `[I]`. The reachability
     statement was wrong: the save test takes the level of the unit's current room (0x005431F9–0x0054322A), so a
     hostile pool monster that follows a player into a town room meets `SaveMonsters` 0 on stock data. That case is a
     required Phase 2 case (added to the done-when). The edited-table case is not needed and could not raise anything
     anyway (ADR-0010 as amended by ADR-0013: a claim only edited data reaches stays `[I]`).

  **Fixes applied on the lane.** drlg/0009: summary `0x400` bullet (numeric alignments, the `Align` mapping, `rogue2`);
  § 4 `0x200000` (server-only, the 626/890 split); § 6 path precedence (flag `0x20` before flag `1`,
  0x0054264A–0x0054266D) and why only alignment 0 reaches the `0x691` test; § 7 the rate; *Leads used* reachability;
  open questions (wanderer alignment as a static read; act `+0x50` as "client act"). Now 48 `[I]`, 15 `[L]`. Plan:
  Phase 2 done-when amended (wanderer spawns a named shortfall; the town-follow case required).

  **P2 questions, amended.** Concrete enough for a logger and a checker: each names its breakpoint sites and fields.
  Changes: Q8 is a static question (above) and stays in the logger only if a saved `0x400` record appears; Q9 is
  the gate's draw on ≥ 200 room updates, each predicted (seed in and out, `low & 0x7FFF`, `+0x78`, `MonWndr`), with
  spawns counted, not targeted; Q10 is "`0x200000` set on every server release, clear on every client release"; add
  Q14 *town follow*: a hostile pool monster in a town room at the town's release (level, `+0xC4` bit `0x2000000`,
  `restore`), asserted freed without a record and absent at the return.

  **P2 opens** (lane H1 queue order, 1 slot).

- **2026-10-17 — Phase 2 checkpoint (reverser, `lane/p40h`, slot 1; in progress, not for review).** Tools:
  `tools/gdb/rooms.{gdb,py}`, `tools/rooms.py check` (with `tools/test_rooms.py`), `tools/rooms_sessions.py`. Sessions
  of run:2026-10-17-lifecycle (logs `workspace/logs/rooms/lifecycle-*.log`): 13 played (n-cold, n-catacombs,
  n-farooze, nm-dark, nm-spider, h-highlands, h-flayer, n-long, nm-long, cls-n-cold, cls-nm-jail, town-n, town-n2);
  the 12 first check with **0 mismatches** over 1 882 803 checks (2 234 releases, 1 245 restores of re-activated
  rooms, 1 926 monsters restored of which 195 special and 254 damaged, 75 over 7500 frames, 876 items, 1 653 objects
  of which 536 operated, 10 128 wanderer-gate draws, 541 039 reference callbacks; acts I–V, three difficulties, maze
  29 and 35, classic Normal and Nightmare). Corrections the run makes to drlg/0009: an item restore takes **two**
  game-seed draws (type 4), a simple (compact) item comes back with start seed 0; a client visit between two release
  passes does not reset the idle count; a room activated by `RoomActivateB` after the walk passed and released
  before the next walk is never populated (+0x60 bit 0 clear); every logged champion carries `0x08` (MonMarkSpecial),
  so the 0x18 test frees dead champions (6 seen) and the "dead champion restored alive" surprise is not reachable on
  stock data; restored minions get the flag-0 handlers of mods 1–4 (+3 level), specials the flag-1 ones.
  **Shortfalls so far:** the town-follow case (two `town` sessions: no hostile monster entered a town room; the
  scripted walk-and-lure does not converge), wanderer roll/spawn (0 of 3 051 eligible draws passed, as expected),
  expired item records (0), pets/owned, `+0xD0` < 8, necro summons, `restore` 0, the `0x400` and level-108 records.
  **Resume:** write the run record (experiments.md), the drlg/0009 Phase 2 section with the `[C]` raises and the
  corrections above, the manifest, and the review request; the town-follow case needs owner play or a static
  answer (whether town rooms block monster movement), named as a shortfall otherwise. Slot 1 stopped.

- **2026-10-17 — Phase 2 landed (reverser, `lane/p40h`, slot 1; review pending).** run:2026-10-17-lifecycle
  ([experiments](../../findings/drlg/experiments.md#run2026-10-17-lifecycle)): 13 sessions, **0 mismatches** over
  2 215 807 checks under `tools/rooms.py check`. Raises and corrections in
  [drlg/0009 § 11](../../findings/drlg/0009-room-lifecycle.md#11-phase-2-run2026-10-17-lifecycle).

  | Done-when item | Target | Run |
  |---|---|---|
  | room releases | 300 | 2 440 (acts I–V; Normal, Nightmare, Hell; mazes 29 and 35; outdoor; classic Normal and Nightmare) |
  | re-activations with a restore | 200 | 1 362 restores of a re-activated room (1 414 re-activations) |
  | monsters restored | 400; 40 special; 30 damaged; stats 7, 12, 13 predicted | 2 035; 199; 255; all predicted (stat 12 by the monsters/stats model) |
  | 7500-frame rule, both sides | — | 1 931 under, 104 over |
  | objects restored | 150, 30 operated | 1 760, 603 operated; objects § B4 save rule on 3 023 objects |
  | ground items restored | 60, seeds and fields | 876 (seed rule corrected, below) |
  | wanderer gate draws | 200 | 11 064 (3 211 eligible; no pass, no spawn: shortfall) |
  | town-follow case | required | **shortfall**: two town sessions released the town's rooms, but no hostile monster was in a town room |

  **Corrections to Phase 1 claims** (drlg/0009 § 11):
  1. An item restore takes **two** game-seed draws, and a simple item comes back with start seed 0.
  2. A client visit that falls between two passes does not reset the idle count.
  3. A `RoomActivateB` room can be released before it is populated.
  4. The save test's `0x18` mask is "special or minion". Every logged champion carries `0x08`, so a dead champion is
     never saved: surprise (1) is unreachable on the logged data.
  5. Restored specials carry stat 12 as the flag-1 handlers give it, and restored minions as the flag-0 handlers of
     mods 1–4 give it.

  **Not reached:**
  - the wanderer roll and spawn;
  - an expired item;
  - pets, `+0xD0` < 8, necromancer summons, `restore` 0;
  - kept units, `0x400` records, level 108, player corpses.

  Plan 0038's deferred objects row 5 (the revisit monster and item restores) is answered by § 11.

  **Tooling:**
  - `tools/gdb/rooms.{gdb,py}`;
  - `tools/rooms.py` and `tools/test_rooms.py`;
  - `tools/rooms_sessions.py`;
  - a section in tooling.md.

  No symbol rows changed (tags in `re/symbols.csv` left for the review). Slot 1 is stopped.

- **2026-10-17 — Phase 2 review (architect): accept with fixes.** Main (`3e169e4`) merged into the lane first
  (`docs/backlog.md` kept both sides and migrated; experiments.md kept both run sections). Re-runs:
  `rooms-lifecycle-manifest.sha256` (`da0c0d7d…`) verifies all 13 logs; the tool hashes match the record (`rooms.gdb`
  `726e3453`, `rooms.py` gdb `45da126c`, `rooms.py` `4f816bd1`, `rooms_sessions.py` `ba25cac1`, `pilot.py` `1ad48a4c`);
  `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/rooms.py check workspace/logs/rooms/lifecycle-*.log`
  over the whole run gives `SUMMARY mismatches=0 checks=2215807`, byte-identical to `rooms-lifecycle-check.txt`
  (`042c01ee…`); `tools/test_rooms.py` 9 tests OK. Each recorded log is one game (one `GP` line, frames from 0, never
  decreasing). Logger addresses spot-checked with objdump on the pinned `game.exe` (13, all resolve): RT 0x0052D289
  after the `RoomReleaseAllowed` call, FREE 0x0052D2BB the `ActiveRoomFree` call, WG 0x0054F089 `test eax, 0x7FFF`,
  the `0x18` test's return 0x005432FB, the three creation calls 0x00542689/0x005426C3/0x005426E9 (`MinionRestore`,
  `SpecialMonRestore`, `SpawnWithId`), PSU0/PSUX 0x0055596C/0x00555971 around `PtrMove`, RM0 0x0061A12B the
  `DrlgRefMove` call, IRC 0x005419C8 after `ItemCreateFromSave`, the mode-12 `mod 3` 0x00543287, TRX 0x0066F239 after
  the `0x200000` write. Two checker mutations (scratch copies, the special path or the minion path given the other
  handler flag) measured what stat 12 separates (ruling 3).

  **Rulings.**
  1. *Town-follow case:* accepted as a **shortfall**; it does not block P3. The run adds the other half: every
     monster the save test met in a `SaveMonsters` 0 level (120 in level 1, 52 in level 103, all town NPCs) carried
     `+0xC4` bit `0x2000000` and was saved. Whether a pool monster can enter a town room at all is a static question
     with a lead (MonStats `inTown`, `+0x0D` bit 2, on no pool class), routed to the reverser; not cheap at the review.
     If the reverser finds it reachable, it becomes an owner-play candidate for a P2 addendum; if not, the Phase 1b
     verdict stands at `[I]` as unreachable on stock data.
  2. *Dead champion:* the observation is `[C]` (15 champions in 30 save tests, all with `0x08`; the 6 dead freed by
     the `0x18` test); "never on stock data" stays `[I]`. Counted at the review: `MonMarkSpecial` has four callers
     (0x005A0B61 in `SpecialMonPlace` after every successful creation; 0x005A487B; 0x005A48F4 in
     `ChampionMemberMark`, skipped when monster data `+0x16` bit `0x04` is already set, 0x005A48EB; 0x005A496E in
     `MonMakeSpecial`). Whether every champion path passes one is routed to the reverser. § 5 test 5 and the § 6
     surprise reworded (the mask is `0x08` or `0x10`; the surprise needs a special without them).
  3. *Stat 12 of restored specials:* the lane's contradiction holds for **champions** only. With the special path
     given flag 0 the checker gives 15 mismatches (the champion restores, one level high each); uniques do not
     separate the flag. So: champion stat 12 = the flag-1 result, `[C]` (15); § 6's "`SpecialModsApply(flag 0)`" is
     marked contradicted for champions. The minion half was overclaimed: with the minion path given flag 1 the checker
     also gives 0 mismatches, so stat 12 does not separate it, and "flag-0 handlers for minions" stays the § 6 reading
     at `[I]`; the minion stat-12 value is `[C]` (144). Which call applies the flag-1 handlers is routed.
  4. *Item restore:* two game-seed draws (876 of 876; one draw would fail every item) and start seed 0 for a simple
     item (587) are `[C]`. Two halves of the § 11 item bullets were under `[C]` without a case and are split out:
     the expired-item drop and the 0-expiry kept (no quest item saved), and in the record bullet the quest 0 and the
     gold above 10000 expiry (branch counts at the review: magic 66, qualities 5–9 21, filler 27, gold up to 10000
     437, else 796). § 6, § 9 and § 10 still said "one game-seed draw" and "keeps its seed": corrected in place.
  5. *120–131 frames:* the narrowing is right (2 224 releases at the first eligible pass, every value 120–131 seen).
     Added the remainder: 82 later (a refused test, or a visit between two passes) and 134 with no logged client
     leave. § 4's frames bullet and the summary now say "the last change a pass saw". The level-120 half of the town
     rule was not reached and is marked `[I]`.
  6. *Procedural mishap:* the record discloses it, and the recorded logs are clean (checked above), so no claim
     depends on it. But "its partial log" was ambiguous and the deletion breaks the keep-everything rule: reworded to
     say it was the overlapped launch's log and should have been kept with the development logs; `smoke1.log` added to
     the development list. A process fix, not a blocking one.
  7. *Symbols:* 27 `drlg/lifecycle` rows raised `I` → `C`, each logged and predicted by the run with the code reading
     as the second source: `ClientRoomChange`, `RoomClientEnter`/`Leave`, `RoomClientAdd`/`Remove`, `DrlgRefMove`,
     `DrlgRefAddNear`/`RemoveNear`, `g_DrlgRefEnterFns`/`LeaveFns`, `DrlgEnter0`/`Enter1Activate`/`Enter2`,
     `DrlgLeave3Release`, `RoomIdleCount`, `RoomReleaseAllowed`, `DrlgRoomReleaseTest`, `DrlgRoomPinFlag`,
     `ActiveRoomFree`, `InactiveMonsterSaveTest`, `InactiveRecordSave`, `InactiveMonsterSave`, `InactiveItemSave`,
     `ItemGroundExpiry`, `InactiveItemRestoreOne`, `SpawnWithId`, `PtrMove`; the drlg/0009 *Functions* tags follow.
     Left at `I`: `RoomPinSet` (no clear call seen), the status helpers (`DrlgRefAdd`, `DrlgStatusRecompute`,
     `DrlgStatusSet`: checked only through the model's status), `RoomRestoredGet`/`Set`, the AI save/restore (a
     boundary), the client loop, `ActIsClient`, `ActLevelsUnloadTick`, `ActRoomsHead`, `LevelSaveMonsters`,
     `InactiveRoomRecordFind`, the target lists, `UnitRelocate`, `DiabloQuestFlag`.
  - Also split: the wanderer gate's `+0x78` and `MonWndr` conditions (no draw passed, so they never decided; summary
    and § 11 now `[I]` for them, the draw itself `[C]` on 11 064). The act `+0x50` open question narrowed to the name.
    experiments.md: "corrects four" → five; "a dead champion saved (none can be …)" reworded.

  **Fixes applied on the lane** (12): overclaim 5 (wanderer gate conditions; item restore drop and 0-expiry; item
  record quest and gold expiry; level-120 half; minion handler flag); under-claim 2 (the dead-champion observation;
  the act `+0x50` values); stale cross-reference 1 (§ 4, § 5, § 6, § 9, § 10 left with Phase 1 text the run
  corrected); miscount 1 ("corrects four"); omission 2 (the release remainder and the town saves; `smoke1.log`);
  tool not kept 1 (the deleted partial log). Gate green.

  **Follow-ups.** Reverser (static): the town reachability (`inTown` readers), the champion paths and `MonMarkSpecial`,
  the flag-1 call in `SpecialMonRestore`, and the tool items (kept partial logs; the town-save census and the expiry
  branches in `rooms.py check`). Spec-writer: P3 opens with this review's rulings; the room-tiles amendment's hold is
  lifted by § 11's `0x200000` bullet. The Phase 1 follow-up (a) is answered by the run for the values.

  **P3 opens** (spec-writer queue order).

- **2026-10-17 — Phase 3 written (spec-writer, `lane/p40s`; review pending).** [drlg/lifecycle](../../specs/drlg/lifecycle.md),
  status `draft`, **{C 78, I 68, L 8}**, from drlg/0009 (§§ 1–9 and § 11) and the P1 and P2 rulings. Sections: A the
  frame; B activation (reference counts per distance, enter/leave callbacks, status, `RoomActivateA`/`B`, client copy);
  C the client lists (`+0x78`); D the new-rooms walk; E release (idle count, the narrowed 120–131-frame wording, the
  release test with pin, status and town conditions, the free, `0x200000`); F the save rule (monster tests in order,
  the mode-12 room draw, objects, items, type 5, missiles); G the records (room, unit, item tables; the monster record as
  a table and a `packet-beta`; item expiry); H the restore (order, the three monster paths, stats 13/7/6 and the
  7500-frame rule, stat 12 per path with the champion flag-1 result, the items' two game-seed draws and start seed 0
  for a simple item); I the wanderer tick; J the preset path and list; the draw order across seeds. Diagrams: a room's
  life and the activation states (`stateDiagram-v2`), the release decision and the save rule (`flowchart TD`), the
  monster record (`packet-beta`), the restore's draw order (`sequenceDiagram`), the wanderer gate. Worked example: one
  Cold Plains room of session `n-cold` released at frame 5460 (129 frames after the leave; four dead monsters
  drawn, one saved; corrected at the review) and restored at 6570 (a corpse in mode 12, an item, an object), every seed step re-derived.
  - Review splits carried: the wanderer gate's `+0x78`/`MonWndr` conditions `[I]` (the draw `[C]`); the expired-item drop
    and 0 expiry `[I]`; quest-item and gold-above-10000 expiry `[I]`; the level-120 half `[I]`; champion stat 12 the
    flag-1 result `[C]`, the minion handler flag `[I]`; the dead-champion observation `[C]`, "not saved on stock data"
    `[I]`. *Open questions* (8 `[L]`): the town-follow case (with the 172 town saves as context), a champion without
    `0x08`, the flag-1 call, the wanderer roll/spawn and alignment, the unreached branches, the client detach and act
    `+0x50`, the unread fields, multiplayer.
  - Linked specs (tags old → new): room-tiles {C 120, I 32, L 0} → {121, 32, 0} (the `EDX`/`0x200000` bullet split into
    `[C]` by run:2026-10-17-lifecycle and "no reader" `[I]`; open question struck; runtime-state row); objects
    {136, 71, 4} → {138, 71, 4} (B4 names `Levels.SaveMonsters`, its save test `[C]`; B5 and the inputs row point to
    lifecycle § H); monsters/spawn {112, 64, 5} → {112, 64, 4} (`+0x78`/`0x0061A4D0` question struck); monsters/stats
    {103, 57, 5} → {104, 57, 4} (the re-created stats row `[C]`, the open question struck); monsters/special
    {104, 93, 3} → {106, 92, 3} (restore entry points `[C]`, the champion stat-12 bullet); drlg/preset {136, 24, 2} →
    {137, 23, 2} (server detach `[C]`, 49 moves); drlg README and rng/seeds link the spec; glossary: *room release /
    inactive record*, *wanderer*.
  - Research map: the `drlg/lifecycle` row set to `draft`; the overview, preset, objects, spawn, special and stats rows
    rewritten whole. Wiki: [levels](../../wiki/levels.md) (the release flag, both passages), [monsters](../../wiki/monsters.md)
    and [objects](../../wiki/objects.md) restated where the reviewed specs changed; no lifecycle section yet, since ADR-0012
    covers reviewed specs only (a levels.md section after the review).
  - Backlog closed: the P3-opens entry, the reverser's (b)/(c), the room-tiles 626 entry. Review requested.

- **2026-10-17 — Phase 3 review (architect): accept with fixes; plan 0040 closed.** Main (`eb125f8`) merged into the
  lane first (clean). Gate green before and after the fixes. Read against drlg/0009 §§ 1–9 and § 11 and the P1 and P2
  rulings at the same strength: the P2 splits are carried (the minion handler flag, the wanderer gate's `+0x78` and
  `MonWndr` conditions, the item-expiry and expired-drop branches, the level-120 half `[I]`; the 120–131 window narrowed
  to a visit a pass saw, with the 82 later and 134 unlogged releases). Worked example: all four seed steps of the release
  (four mode-12 draws chained on the room seed, `low mod 3` = 2, 1, 0, 1) and the restore's gate draw, three placement
  draws, the monster's game-seed draw, the item's two and the object's one re-derived with `Step` from `rng`; each
  matches the spec and the `n-cold` log lines (MR0/MRC/IRC/RSX at frame 6570). Diagrams: one claim was only in a diagram
  (the monster record's `+0x58` next link and its padding), now rows of the table; the others restate tagged text. No
  `[L]` above *Open questions* (E5). Anchors spot-checked with objdump on the pinned `game.exe` (22, all resolve):
  `n > 10` at 0x0052D27B, the gate's `test eax, 0x7FFF` at 0x0054F089 and `+0x78` at 0x0054F096, `PtrMove` into record
  `+0x24` at 0x00542098, back at 0x00541EA2, `PresetUnitSpawn`'s at 0x0055596C, the path precedence at
  0x0054264A–0x0054266D (flag `0x20` overrides `1`), the wrapper's `sete` at 0x0066B4DE, `EDX = act +0x50` at 0x0061A9D0,
  the `0x200000` write at 0x0066F232, `MonMarkSpecial` from 0x005A0B61, the restore tail 0x005427FB–0x00542916 (stat
  order 13, 7, 6; the 7500 test unsigned), `ItemGroundExpiry` 0x00558A10 (branch order as G1; stat 14 `jle`, signed),
  the item drop `jg` (signed) at 0x00541ADF and the expiry floor `jge` (signed max) at 0x005419F7, and
  0x0061B390/0x0061B490/0x0061B4F0/0x0061B560/0x0061B5B0/0x0061B6F0/0x0061BB10 for ruling 1.

  **Rulings on the lane's four points.**
  1. *§ B from the checker model:* the spec may not rest on `tools/rooms.py` alone, since a spec cites findings, and
     drlg/0009 § 2 said only "mirrors". Read at the review and written into drlg/0009 § 2 as a new `[I]` line
     (0x0061B5C3–0x0061B5EE: decrement with no zero test, leave callback on every decrement, recurse **after**, null
     entries skipped; the add walk recurses before its enter test; leave 3's early return at status 4; `Recompute`'s
     early return; enter 2's `0x1000000`/type-2 `0x2000000`/status > 2 test). The model the checker replays is exactly
     this reading, and § 11's 634 982 predicted callbacks (kind, room, refs and status at entry) are the second source,
     so B2–B9 keep `[C]`, now with the instruction anchors and a pointer to § 2.
  2. *Objects B4 raised to `[C]`:* accepted for the branches the run met, overclaimed for the rest. Counted at the
     review from the `US`/`USD` lines: 3 023 objects, the starting flag set on all (653 by the preset flag alone, in
     `SaveMonsters` 0 levels), `Restore` 0 15, `RestoreVirgins` on a used object 30, the sparkle bit `0x02` on none, and no
     unit of any type with both flags clear. So objects B4's header is `[C]` "on the branches the run met", and a new
     `[I]` bullet names the sparkle refusal, the both-clear refusal and classes 59/60; lifecycle § F's objects bullet and
     F2's starting value (`[C]` when either flag is set, `[I]` when both are clear) say the same. Objects
     {138, 71, 4} → {138, 72, 4}.
  3. *drlg/preset's server detach `[C]`:* accepted (49 moves, the finding's summary tags the detach `[C]`); the
     no-second-dispatch note stays `[I]`. Lifecycle § J now says the run's moves are the **server-copy** half of the
     detach drlg/preset note 4 saw (the 19 units were logged in both copies; the client copy's detach is open).
  4. *"If saved" before `+0xC8 |= 0x200`:* read at the review: `test [rec+0x14], 0x200; or [unit+0xC8], 0x200`
     (0x005428F9–0x00542903), so the bit is carried over from the record's saved `+0xC8`. drlg/0009 § 6 and lifecycle H3
     now say so, `[I]` (the restored unit's `+0xC8` is not among the checked fields).

  **Recounts.** Gate E6 green on the 7 linked specs; lifecycle {C 78, I 68, L 8} → {C 78, I 70, L 8} after the fixes
  (F2's both-clear half, the `+0x58` row); room-tiles {121, 32, 0}, monsters/spawn {112, 64, 4}, monsters/stats
  {104, 57, 4}, monsters/special {106, 92, 3} and drlg/preset {137, 23, 2} match the lane's deltas (each checked against
  its diff). Research-map rows checked whole; the objects and lifecycle rows rewritten for this review.

  **Wiki.** levels, monsters and objects checked against the specs: the monsters page said a re-created monster
  "keeps" its level (a minion's first restore comes back 3 higher): reworded; the "still in review" phrases closed;
  objects names the two unmet refusals; levels' *What is not known yet* still said the server detach was "by the
  code": now confirmed. **New levels.md section** *Rooms that come and go: release and restore* (ADR-0012, written at the
  review now that the spec is reviewed) with a *Room lifecycle* bullet under *What is not known yet*; `based_on` adds
  drlg/lifecycle on levels, monsters and objects.

  **Fixes applied** (8): overclaim 2 (objects B4 and lifecycle § F/F2 over unmet branches; § J's whole detach), wrong
  anchor 1 (§ B resting on the checker model, finding line added), omission 2 (the "if saved" condition; the `+0x58` row
  shown only in a diagram), misread 1 (wiki monsters "keeps" the level), miscount 1 (this log's "two of four dead
  monsters drawn": all four were), stale cross-reference 1 (levels' "by the code" detach).

  **Close.** drlg/lifecycle `reviewed`; plan status `done`, moved to `done/`, links rewritten; index and research-map
  rows set. Request closed. Follow-ups filed: reverser (symbol tags the spec now leans on: `RoomsDeactivate`,
  `InactiveMonstersRestore`, `RoomInactiveUnitsRestore`, `RoomWandererTick`, `DrlgRefAdd`, `DrlgStatusRecompute` at `I`;
  three `0x400` records of class 522 with alignment 2 saved in `h-highlands` at frames 9636, 9828 and 13008 and never
  restored, the cheapest route to the `0x400` drop); the P2 follow-ups (town reachability, champion paths, the flag-1
  call) stay open in their own entry.

- **2026-10-17 — post-close: the P2 review follow-ups, reviewed with `lane/rbs3` (architect).** The static answers are in
  [drlg/0009 § 11.1](../../findings/drlg/0009-room-lifecycle.md#111-static-follow-ups-of-the-phase-2-review-lanerbs3);
  the full review is in the [plan 0038 log](../0038-inferred-claims-sweep.md#implementation-log) (`lane/rbs3` review).
  The plan stays closed; nothing here reopens a phase.
  - (1) **Town-follow case: stays a named Phase 2 shortfall.** The path planner refuses a town target room for a
    non-NPC monster (`sub_006483A0`, read at the review), but three routes stay open. No P2 addendum and no owner-play
    candidate now: the recipe would be a guess, and the static remainder (the `0x40000` branch, the knockback, teleport
    and placement writers) is cheaper and could settle it. Routed to the static sweep queue
    ([rbs3 review static remainders](../../backlog/archive/2026-10-17-architect-reverser-rbs3-review-static-remainders.md) (1));
    a harness case, if that read finds a route in, would be a plan 0038 harness batch, not a 0040 addendum.
  - (2) **The dead champion "not saved on stock data" stays `[I]`.** Every server write of champion bit `0x04` follows
    `MonMarkSpecial` (0x005A0375, `or [esi+0x16], dx` with `EDX` = 8 from 0x005A034A, read at the review), but the
    universal half is a code reading only: the run's 6 dead champions all carried `0x08`, which is the claim itself, not
    a second source for "no other path", and a block copy of monster data is unfollowed. The `[C]` "no logged dead
    champion was saved" stands.
  - (3) **§ 6 corrected; the flag-1 call raised.** The lane's § 6 correction stands. The review raised "SpecialMonRestore
    applies the flag-1 handlers through `SpecialModsApply` (0x005A4558)" to `[C]`: the code reading plus the run's 15
    champion restores, which flag 0 would miss. "The pushed 0 is `minions`" stays `[I]`. drlg/lifecycle repeats the
    old wording (H2b note, § H champion bullet, two open questions): routed to the spec-writer (annotated
    [rbs3 lifecycle and MonPlace readings](../../backlog/archive/2026-10-17-reverser-spec-writer-rbs3-lifecycle-and-monplace-readings.md)).
  - (4) `rooms.py check` re-run at the review: 0 mismatches over 2 215 807 checks; census and expiry branches as kept.

- **2026-10-17 — post-close: the town-follow static remainder and the close follow-ups, reviewed with `lane/rbs4`
  (architect).** The reading is [drlg/0009 § 11.2](../../findings/drlg/0009-room-lifecycle.md#112-the-town-follow-static-remainder-lanerbs4);
  the full review is in the [plan 0038 log](../0038-inferred-claims-sweep.md#implementation-log) (`lane/rbs4` review).
  The plan stays closed.
  - (1) **Town-follow: now a plan 0038 harness batch, H7a (`lifecycle`).** § 11.2 shows two routes in by code reading,
    all `[I]`: the walk's room update `PathRoomUpdate` (0x0064FAD0) has no town test, so the planner's target test is the
    only barrier on a planned walk; `UnitTeleport` and the Teleport do function (0x005CA360) test the caster's level only.
    The `0x40000` branch reaches a monster only through 9 unfollowed `MonAiPathOverride` calls. As the `lane/rbs3`
    ruling set, a route in makes it a plan 0038 harness batch, not a 0040 addendum. Recipe (b), a Blood Moor chaser
    whose route crosses a camp room, goes first, after an offline geometry check picks the seed and points; recipe (c),
    a teleporting unique, waits on a static read of the AI's teleport target. Not owner play: both are scripted
    recipes for the `rooms.gdb` family. Until H7a runs, the case stays a named shortfall in the spec's *Open
    questions* (spec-writer entry [rbs4 town-follow and outdoor 7](../../backlog/archive/2026-10-17-architect-spec-writer-rbs4-town-follow-and-outdoor-7.md)).
  - (2) **The `0x400` drop rides on H7a** (close follow-ups item (2); entry closed).
  - (3) **Symbols:** `DrlgRefAdd` and `DrlgStatusRecompute` raised to `C`; `RoomsDeactivate`, `InactiveMonstersRestore`
    and `RoomInactiveUnitsRestore` raised **in part** (the unreached branches § 11 lists stay `[I]`, written into
    drlg/0009 § Functions at the review). `RoomWandererTick` and `DrlgStatusSet` stay `I`.
