# 0001 — Modes and frames: the mode machine, the animation record, the frame clock and the mode events

> **Subsystem:** anim/timing
> **Question:** when a unit enters a mode, which animation record does it get, how are its frame fields set and
> advanced, on which game frames do its frame events (codes 1–4) and its mode end fall, which mode follows, and does
> any of it draw from an RNG?
> **Date:** 2026-10-27   **Plan:** 0050 (Phase 1, batch P1.1)   **Status:** open (P1.3 movement and the gates
> follows; the rate formulas of `UNIT_AnimSetRate` are in [anim/0002](0002-rates.md))

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p50a`) and objdump. The table
values, call-site counts and event kinds below come from `tools/anim_scan.py`; the RNG reach comes from
`re/ghidra_scripts/RngCallGraph.java` with its new `stop@` roots. Both are kept under `workspace/logs/anim/`
(`p50a-manifest.sha256`, one path base: `p50a-anim-scan.txt` `d6679d5f…`, `p50a-anim-rows.txt` `8e5d2636…`,
`p50a-rng-machine.txt` `c2a9581f…`, `p50a-rng-modes.txt` `7b68d8a1…`, `p50a-strings.txt` `f50af233…`, and `p50a-commands.txt` `9c2ad116…` with the
command lines and the tool revisions: `tools/anim_scan.py` `f2825e83…`, `RngCallGraph.java` `33801ca2…`).
Unit fields are named as in `re/types/game.h` (`struct:Unit+0x44` …); the animation records as in `re/types/anim.h`. Table columns are named as in the table docs; `animdata.d2` and
`monseq.txt` had no format or table doc when this batch was filed, so their fields are named from the code here; plan
0050 Phase 0 has since written [formats/animdata](../../formats/animdata.md) and [MonSeq](../../tables/MonSeq.md), whose
names agree (P1.1 review). 8.8 means frames × 256.

## Answer (summary)

- [I] **Two clocks.** A unit's frame fields (`Unit+0x44` frame, `+0x48` length, `+0x4C` rate, `+0x4E` event byte) are
  advanced per frame by `UNIT_AnimAdvance` only for **monsters in an every-frame mode** (walk, run, knockback,
  sequence, and the attack and skill modes whose MonStats2 `*mv` bit is set). Every other server mode with events
  (all player attack, cast, skill, get-hit, block, death and sequence modes; the other monster A1–S2 modes, get-hit,
  block and death) is **scheduled at its start**: `SUNIT_ScheduleModeEvents` walks the animation in
  8.8 steps once and queues one unit event 0 per frame-event byte (1, 2, 4 with a running index; 3 with index 0) at the
  game frame each falls on, and one event 1 (the mode end) after the last step; monster neutral, S3, S4 and dead
  queue none. A rate change after the start does not move these events unless a catalogue function reschedules
  them. (fn:UNIT_AnimAdvance@0x00623E00,
  fn:SUNIT_ScheduleModeEvents@0x005539B0, data:g_MonModePerFrame@0x006E23D0, tbl:MonStats2.txt:A1mv)
- [I] **The schedule.** With start frame `S` (`UNIT_AnimStartFrame`), rate `r` (`+0x4C`, or `+0x3C` in a sequence),
  length `L` (`+0x48`, or `+0x34`) and the game frame `T` of the call: no frame event and the end at `T + 1` when
  `r = 0`; else for `k = 1, 2, …` while `256·S + k·r < L`, the frames from the last one scanned up to
  `(256·S + k·r) >> 8` (the first step scans from `S`, frames ≥ `0x90` never) fire at `T + k`; the end fires at
  `T + max(2, N + 1)`, `N` the number of steps. For `L > 256·S` that is `T + max(2, ⌈(L − 256·S) / r⌉)`. Afterwards
  `+0x44` holds `T << 8`. (fn:SUNIT_ScheduleModeEvents@0x005539B0, 0x00553A0C–0x00553AF1)
- [I] **The record.** `UNIT_AnimSetRecord` stores in `+0x50` the `animdata.d2` record named token + mode token +
  weapon class (`COMPOSIT_BuildCofName`: the PlrType, MonStats `Code` or object token; the PlrMode, MonMode or ObjMode
  token, remapped `GH` for player modes 18 and 19 and monster mode 13; the weapon class of § 2), found by
  `ANIMDATA_Find` (uppercased, bucket = byte sum & 0xFF, 160-byte records, two-dword compare). A missing name gives
  the table's fallback record: 2048 frames, speed 256, no events. `+0x48 = FramesPerDir << 8`.
  (fn:UNIT_AnimSetRecord@0x00620F00, fn:ANIMDATA_Lookup@0x0066A9B0, fn:ANIMDATA_Find@0x0066A8F0,
  fn:ANIMDATA_Load@0x0066A770, tbl:CharStats.txt:baseWClass, tbl:MonStats.txt:Code, tbl:MonStats2.txt:BaseW)
- [I] **The start frame** is 0 except for a player (by display type, § 2) in A1 or A2, or in S3/S4 while able to
  dual-wield: then the image table `g_AttackStartFrames[wclass][class]` for the weapon's own class code, which is 1
  (hand to hand) or 2 (`1hs`, `1ht`, `stf`, `2hs`, `2ht`) for the Amazon and the Sorceress and 0 for every other cell.
  The per-frame advance also restarts at it after each wrap. (fn:UNIT_AnimStartFrame@0x00623B10,
  data:g_AttackStartFrames@0x006E8E60, `p50a-anim-scan.txt` `START` lines)
- [I] **Mode changes.** `UNIT_SetMode` does nothing for type 5 and, for the same mode, only refreshes (no animation
  restart); a new mode sets `+0x10`, drops the stat lists flagged to end on a mode change and calls `UNIT_AnimInit`.
  The player and monster mode starts then call `SUNIT_AnimInit` (sequence or record, rate, `+0x44 = 0`), cancel the
  unit's events 0 and 1 and queue the new mode's (scheduled, every frame, or none). Player mode ends go to neutral
  (town neutral in town), death to dead (17); monster ends go to neutral by a mode command, walk and run directly,
  knockback to get-hit, death to dead (12). The generic S3 record's frame function would go to S4, but its mode queues
  no event (`schedule` 0, § 10), so in the code read nothing runs it (open question 1). (fn:UNIT_SetMode@0x00624690, fn:SUNIT_AnimInit@0x005533D0,
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:sub_00581020_PlayerModeEnd@0x00581020,
  fn:sub_005A8030_MonModeEndGeneric@0x005A8030)
- [I] **Sequences.** A player sequence (mode 18) uses the image tables `g_PlrSeqTables[Skills seqnum]` (24 entries,
  14 weapon-class columns of 12 bytes); a monster sequence (mode 14) the `monseq` index built at load, chosen by the
  MonStats `Sk<k>mode` ordinal of the used skill. A sequence frame is 6 bytes: mode, frame, direction, event. The
  per-frame advance moves `+0x38` by `+0x3C` (wrapping at `+0x34`), counts `+0x48` down by `+0x3C`, and takes the
  frame's mode, frame and event byte; it ends when `+0x48 ≤ 0`. For a player, whose sequence does not
  advance on the server, `PlrModeSkillFrame` writes the running event's index into `+0x38 >> 8` when a skill is in use.
  (fn:UNIT_SeqInit@0x00621260, fn:UNIT_SeqReadFrame@0x00621210, fn:SEQ_ReadFrame@0x00663410,
  fn:MONSEQ_Load@0x00659C60, data:g_PlrSeqTables@0x007483B8, tbl:Skills.txt:seqnum, tbl:MonStats.txt:Sk1mode)
- [I] **Draws.** In the 171 functions under the animation machine's 29 roots (three indirect stat-list callbacks
  unfollowed, § 11), the only RNG call is
  `UNIT_AnimInit`'s object draw `RangeB(unit seed, FrameDelta[mode] >> 3)` when `Sync` is 0, which sets the object's
  rate to `FrameDelta − (FrameDelta >> 4) + draw` (clamped to `[0, 0x7FFF]`). The mode functions reach draws only
  through other subsystems (skills, combat, death drops, AI, paths), plus two of their own: the player interrupt test
  (`Range(unit seed, 100)` against Concentration's stat 164) and monster death's class-212 area damage.
  (fn:UNIT_AnimInit@0x00624390, 0x00624563, `p50a-rng-machine.txt`, `p50a-rng-modes.txt`, tbl:Objects.txt:Sync,
  tbl:Objects.txt:FrameDelta0)
- [I] **Event order.** Each game frame runs the missile, player, monster, object and item event lists in that order,
  each its every-frame list (newest first) and then the current frame's slot (oldest first); a queued frame is never
  the current one. (fn:sub_005414D0_GameRunUnitEvents@0x005414D0, fn:sub_005416B0_EventQueueAt@0x005416B0)

## Leads used

None. No lead was registered for animation timing when this batch was filed; it reads code only ("no lead; derived
from code"), and [anim/leads](leads.md) was not read before filing. The community cross-check is Phase 1b part 2's;
its rows R1, A3 and A4 (frame advance, start frame) are decided against this finding (plan 0050 log, `lane/p50c`
review).

Questions routed here by other findings: skills/0001's `Unit+0x38` (§ 5) and its "which frame carries code 1 or 2"
(§§ 7–8: the frame whose `animdata.d2` or sequence event byte is 1 or 2, at the game frame the schedule gives it);
skills/0002's place of the missile pass in the frame (§ 6: first).

## Functions

New names (subsystem `anim/timing`) and the existing ones this finding reads; all new rows are I.

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00624690` | `UNIT_SetMode` | mode change, then `UNIT_AnimInit` (§ 3) | C (objects; unchanged) |
| `0x00624390` | `UNIT_AnimInit` | frame fields per unit type (§ 3) | C (objects; unchanged) |
| `0x00623F50` | `UNIT_AnimSetRate` | record and `+0x4C`/`+0x3C` rate (formulas: [anim/0002](0002-rates.md)) | I |
| `0x00620F00` | `UNIT_AnimSetRecord` | `+0x50 = ANIMDATA_Lookup(mode, type, inventory)` (class in a register) | I |
| `0x00623B10` | `UNIT_AnimStartFrame` | the start frame (§ 4) | I |
| `0x00623E00` | `UNIT_AnimAdvance` | the per-frame advance and event byte (§ 8) | I |
| `0x00621310` | `UNIT_AnimAdvanceLoop` | `+0x44 += rate`, wrap at `+0x48`; client callers only (5 sites) | I |
| `0x006217C0` | `UNIT_AnimAtEnd` | sequence: `+0x48 < 1`; else `+0x48 ≤ +0x44 + rate` | I |
| `0x00621260` | `UNIT_SeqInit` | sequence fields, frame 0 read, `+0xC4 |= 0x4000` | I |
| `0x00621210` | `UNIT_SeqReadFrame` | the frame at `+0x38`: mode, frame, event; returns "mode changed" | I |
| `0x006212C0` | `sub_006212C0_UnitSetSeqPos` | `+0x38 = (+0x38 & 0xFF) + n·256` | I |
| `0x00663310` / `0x006633D0` / `0x006633F0` | `sub_00663310_UnitSeqRecord` / `sub_006633D0_UnitSeqLength` / `sub_006633F0_UnitSeqFrames` | the used skill's sequence record, its `+4 << 8`, its `+8` | I |
| `0x00663410` / `0x006634C0` | `SEQ_ReadFrame` / `sub_006634C0_SeqFrameEvent` | 6-byte frame reader; event byte at a position | I |
| `0x00643D00` / `0x006632C0` / `0x00659E30` | `sub_00643D00_SkillSeqIndex` / `sub_006632C0_PlrSeqColumn` / `sub_00659E30_MonSeqRecord` | sequence number, player column, monseq record | I |
| `0x00659C60` | `MONSEQ_Load` | `monseq.bin` and its 12-byte index | I |
| `0x0066A770` / `0x0066A8F0` / `0x0066A9B0` | `ANIMDATA_Load` / `ANIMDATA_Find` / `ANIMDATA_Lookup` | `AnimData.d2` table, find, find-or-fallback | I |
| `0x0064F5B0` / `0x0064F060` / `0x0064F020` | `COMPOSIT_BuildCofName` / `COMPOSIT_WeaponClass` / `COMPOSIT_WeaponClassIndex` | the record name and its weapon class (§ 2) | I |
| `0x00645270` / `0x00645190` | `UNIT_AnimTransform` / `sub_00645190_PlrToMonMode` | the shapeshift states' display type, class and mode (§ 2) | I |
| `0x005533D0` | `SUNIT_AnimInit` | server re-init at a mode start (§ 3) | I |
| `0x005539B0` | `SUNIT_ScheduleModeEvents` | the schedule (§ 7) | I |
| `0x00553B10` / `0x00553C70` / `0x00553DC0` | `sub_00553B10_RescheduleFromPct` / `sub_00553C70_RescheduleSkip` / `sub_00553DC0_RescheduleAt` | catalogue reschedules (§ 7.1) | I |
| `0x00553F00` / `0x00553990` / `0x00553570` | `SUNIT_ModeEveryFrame` / `SUNIT_CancelModeEvents` / `SUNIT_SetMode` | event 0 every frame; cancel events 0 and 1; `0x0057C980` then `UNIT_SetMode` | I |
| `0x005416B0` / `0x005415E0` / `0x00541650` | `sub_005416B0_EventQueueAt` / `sub_005415E0_EventQueueEveryFrame` / `sub_00541650_UnitQueueEveryFrame` | the event queue (§ 6) | I |
| `0x00541240` / `0x00540F60` / `0x00541060` / `0x00541320` | `sub_00541240_MissileEventsRun` / `sub_00540F60_PlayerEventsRun` / `sub_00541060_MonEventsRun` / `sub_00541320_ItemEventsRun` | the list runners (§ 6) | I |
| `0x00581220` / `0x005A7F80` | `sub_00581220_PlayerEventDispatch` / `sub_005A7F80_MonEventDispatch` | `g_PlayerEventFuncs` / `g_MonEventFuncs` by kind | I |
| `0x005811D0` / `0x005A7BA0` / `0x005A7BE0` | `sub_005811D0_PlayerModeFrameEvent` / `sub_005A7BA0_MonModeFrameEvent` / `sub_005A7BE0_MonModeEndEvent` | event 0 and 1 handlers | I |
| `0x005A6B10` | `sub_005A6B10_MonModeEveryFrame` | is the monster mode every-frame? | I |
| `0x005A8030` / `0x005A8520` / `0x005A8330` / `0x005A83E0` / `0x005A73E0` | `sub_005A8030_MonModeEndGeneric` / `sub_005A8520_MonKnockbackEnd` / `sub_005A8330_MonModeEndToS1` / `sub_005A83E0_MonModeEndToS1b` / `sub_005A73E0_MonModeStartNeutral` | monster mode ends and the neutral start (§ 10) | I |
| `0x0057F020` / `0x0057F090` / `0x0057F1F0` / `0x0057F190` / `0x0057FE30` / `0x0057FDC0` / `0x00580C20` | `sub_0057F020_PlrModeStartNeutral` / `sub_0057F090_PlrModeStartMove` / `sub_0057F1F0_PlrModeStartMoveXY` / `sub_0057F190_PlrModeStartMoveUnit` / `sub_0057FE30_PlrModeStartGetHit` / `sub_0057FDC0_PlrModeStartBlock` / `sub_00580C20_PlrModeMoveFrame` | player mode starts and the move frame (§ 9) | I |

Data: `g_MonModeRecords` `0x006E2260` (21 × 16 B), `g_MonModePerFrame` `0x006E23D0` (16 × 12 B), `g_MonModeEndDirect`
`0x0073C6D0` (16 B), `g_AttackStartFrames` `0x006E8E60` (14 × 7 dwords), `g_PlrSeqTables` `0x007483B8` (24),
`g_PlrSeqColumns` `0x00748418` (14 pairs), `g_WeaponClassTokens` `0x006EB748` (13 pairs), `g_ItemWeaponClassIndex`
`0x007446A0` (count `0x007446E0`, 8), `g_PlrToMonMode` `0x006EB348` (20), `g_MonToPlrMode` `0x006EB308` (16),
`g_PlrModeTokenRemap` `0x00745900` (count `0x00745910`, 2), `g_MonModeTokenRemap` `0x00745914` (count `0x0074591C`,
1), `g_pAnimData` `0x0096C8A4`, `g_pMonSeqIndex` `0x0096C7B4`, `g_MonSeqIndexCount` `0x0096C7B8`,
`g_UnitTypeEventList` `0x006E0B9C`.

## Walkthrough

### 1. The unit's animation fields

| Field | Width | Meaning | Writers read |
|---|---|---|---|
| `struct:Unit+0x30` | ptr | the sequence's frame records, 0 outside a sequence | `UNIT_SeqInit`, `UNIT_AnimInit` (0), `SUNIT_AnimInit` (0) |
| `struct:Unit+0x34` | s32 | sequence length, frames << 8 | `UNIT_SeqInit` |
| `struct:Unit+0x38` | s32 | sequence position, 8.8 | `UNIT_SeqInit` (0), `UNIT_AnimAdvance`, `sub_006212C0_UnitSetSeqPos` |
| `struct:Unit+0x3C` | s32 | sequence step, 8.8 (0x100 at the start) | `UNIT_SeqInit`, `UNIT_AnimSetRate` (anim/0002 § 3.8) |
| `struct:Unit+0x40` | s32 | the mode byte of the current sequence frame | `UNIT_SeqReadFrame` |
| `struct:Unit+0x44` | s32 | frame, 8.8; in a scheduled mode the schedule's game frame `<< 8` | `UNIT_AnimInit`, `SUNIT_AnimInit` (0), `SUNIT_ScheduleModeEvents`, `UNIT_AnimAdvance`, `UNIT_SeqReadFrame` |
| `struct:Unit+0x48` | s32 | length, frames << 8; objects unshifted; sequences the frames left `<< 8` | `UNIT_AnimInit`, `SUNIT_AnimInit`, `UNIT_SeqInit`, `UNIT_AnimAdvance` (sequence) |
| `struct:Unit+0x4C` | s16 | rate, 8.8 per frame, clamped to `[0, 0x7FFF]` | `UNIT_AnimSetRate`, `UNIT_AnimInit` (objects, missiles, items), `0x00621780` (client; one server site, a missile's: [anim/0002 § 5](0002-rates.md#5-who-calls-it-and-the-updateanimrate-bit)) |
| `struct:Unit+0x4E` | u8 | event byte of the frames last crossed (1–4), else 0 | `UNIT_AnimInit` (0), `SUNIT_AnimInit` (0), `UNIT_AnimAdvance`, `UNIT_SeqReadFrame` |
| `struct:Unit+0x50` | ptr | the `animdata.d2` record (`re/types/anim.h` `AnimDataRec`) | `UNIT_AnimSetRecord` |

- [I] `UNIT_AnimFrames` (`sub_00621810_UnitAnimFrames`) returns `+0x44 >> 8` and, for an object, Objects
  `FrameCnt[mode]` (`+0xD8 + 4·mode`), else `+0x48 >> 8`. So an object's `+0x48` is a plain frame count while every
  other type's is 8.8. (fn:sub_00621810_UnitAnimFrames@0x00621810, tbl:Objects.txt:FrameCnt0)

### 2. Records: the token, the lookup and the fallback

- [I] `UNIT_AnimSetRecord(unit, type, class, mode)` = `+0x50 ← ANIMDATA_Lookup(mode, type, unit+0x60 inventory)`, the
  class in `EDX`. `ANIMDATA_Lookup` builds the name with `COMPOSIT_BuildCofName` (its `wsprintf("%s%s%s")` branch:
  token, mode token, weapon class, each with spaces removed), then `ANIMDATA_Find`; on 0 it returns
  `g_pAnimData + 0x404`. (fn:UNIT_AnimSetRecord@0x00620F00, fn:ANIMDATA_Lookup@0x0066A9B0, 0x0066A9FD–0x0066AA02)
- [I] `ANIMDATA_Load` reads `DATA\GLOBAL\AnimData.d2` whole, zeroes a 0x4A4-byte table object and fills 256 block
  pointers by walking `count; count × 0x28 dwords` blocks; it sets the fallback record's frames (`+0x40C`) to 0x800
  and speed (`+0x410`) to 0x100, its name and 144 event bytes staying 0. `ANIMDATA_Find` uppercases the name in place
  (`a`–`z`), takes the block `(sum of the bytes) & 0xFF`, fails fatally on a name or record longer than 8 characters,
  and compares the first two dwords of each 0xA0-byte record. (fn:ANIMDATA_Load@0x0066A770, 0x0066A80A, 0x0066A814,
  fn:ANIMDATA_Find@0x0066A8F0, 0x0066A92E, 0x0066A96A, data:g_pAnimData@0x0096C8A4)
- [I] The record fields read: `+0x08` frames per direction (`+0x48 = +0x08 << 8` at every non-sequence init), `+0x0C`
  the speed that `UNIT_AnimSetRate` scales (anim/0002), `+0x10 + f` the event byte of frame `f`, read only for `f < 0x90`.
  (0x00624470, 0x006244F1, 0x00623E95, 0x00553A40)
- [I] **The name.** `COMPOSIT_BuildCofName(…, mode, class, type, …)` (fn:COMPOSIT_BuildCofName@0x0064F5B0):
  - player (type 0): the PlrType token of the class, the PlrMode token of the mode, and the weapon class
    `COMPOSIT_WeaponClass`; mode 0 or 17 gives `hth`; the PlrMode token is replaced by `GH` for modes 18 and 19
    (`g_PlrModeTokenRemap`); mode 11 (throw) with a weapon class other than `1hs`, `1ht`, `1js`, `1jt`, `1ss`, `1st` gives
    `hth`. (fn:COMPOSIT_BuildCofName@0x0064F5B0, data:g_PlrModeTokenRemap@0x00745900)
  - `COMPOSIT_WeaponClass` for a player: CharStats `baseWClass` unless the right (body location 4) or left (5) item
    is a weapon item of component 5 or 6 (and the mode is not 0 or 17); then, for the Barbarian (class 4) with two
    items of type 45 (`weap`) the dual classes by the primary and the other weapon's item class index (`0x00629FE0`):
    `1js` for 1hs + 1ht, `1jt` for 1ht + 1ht, `1st` for 1ht + 1hs, `1ss` otherwise; for the Assassin (class 6) with two
    such items `ht2`; else the item's one- or two-handed class (`0x00628500` / `0x00628530`, by `0x0063D340`). (fn:COMPOSIT_WeaponClass@0x0064F060,
    tbl:CharStats.txt:baseWClass, tbl:Weapons.txt:wclass, tbl:Weapons.txt:2handedwclass)
  - monster (type 1): MonStats `Code`, the MonMode token (`KB` → `GH`, `g_MonModeTokenRemap`), and MonStats2
    `BaseW`; in mode 0 or 12 `hth` unless MonStats2 `compositeDeath` (flag 16, `+0x006` bit 0). A missing MonStats2
    record gives `hth`. (tbl:MonStats.txt:Code, tbl:MonStats2.txt:BaseW, tbl:MonStats2.txt:compositeDeath,
    fn:sub_004638A0_MonStats2FlagTest@0x004638A0)
  - object (type 2): the object token (`0x0065B570(class, 0)`), the ObjMode token, `hth`.
- [I] **Shapeshift display.** `UNIT_AnimTransform(unit, &type, &class, &mode)` runs only when `Unit+0xC8` bit 3 is
  set: for the first state in the DataTables `+0x17C` list (count `+0x180`) the unit has, States `gfxtype` 1 makes the
  display type 1 (monster) with class `gfxclass` and, for a player, maps the mode with `sub_00645190_PlrToMonMode`
  (`g_PlrToMonMode`, then down a fallback chain until MonStats2 `mDT`…`mRN` has the mode: 5 and 7 → 4, 6 → 3, 9–11 →
  8, 15 → 2, others → 1); `gfxtype` 2 makes it type 0 with class `gfxclass` and, for a monster, maps with
  `g_MonToPlrMode` (class 6 in mode 4 → 12). The record, the start frame and the rate all use the display values.
  (fn:UNIT_AnimTransform@0x00645270, fn:sub_00645190_PlrToMonMode@0x00645190, tbl:States.txt:gfxtype,
  tbl:States.txt:gfxclass, tbl:MonStats2.txt:mDT)

#### 2.1 The Phase 0 data questions (archivist, `lane/p50z`; folded into P1.1's *Done when* at its review)

The archivist's Phase 0 survey (reported by the orchestrator, 2026-10-27; not read on this lane) raised five data
surprises, (a)–(e) of the plan's P1.1 item. The code read here answers them as follows:

- [I] **Duplicate record names.** `ANIMDATA_Find` walks the name's block from its first record and returns the first
  whose two dwords match, so of two same-named records the one earlier in the file wins (both necessarily sit in the
  same block, the hash being of the name). (fn:ANIMDATA_Find@0x0066A8F0, 0x0066A938–0x0066A96A)
- [I] **Objects.** The server takes an object's length, start frame and rate from Objects `FrameCnt`, `Start` and
  `FrameDelta` (§ 3) and never looks up its `animdata.d2` record: `UNIT_AnimInit`'s object branch calls neither
  `UNIT_AnimSetRate` nor `UNIT_AnimSetRecord`, and `SUNIT_AnimInit` has no object caller. So a mismatch between the
  two sources has no server effect in the code read. (fn:UNIT_AnimInit@0x00624390, tbl:Objects.txt:FrameCnt0)
- [I] **monseq frames past the record.** A sequence step's `frame` only sets `+0x44 = frame << 8` (`UNIT_SeqReadFrame`);
  the server reads no `animdata.d2` byte by that frame while a sequence is active (both the schedule and the advance
  take the event from the sequence record when `+0x30` is set), so an out-of-range frame is not read through the
  record on the server. (fn:UNIT_SeqReadFrame@0x00621210, fn:SUNIT_ScheduleModeEvents@0x005539B0, 0x00553A48)
- [I] **monseq events against the record's.** For the same reason the event that counts in a sequence is the
  `monseq` (or player table) `event`, never the `animdata.d2` byte of the step's frame. (fn:SEQ_ReadFrame@0x00663410)
- [I] **`eanimdata.d2`.** The only animation-data load is `ANIMDATA_Load`'s `"%s\AnimData.d2"` with `DATA\GLOBAL`
  (the image's one string naming it, `0x006EED5C`, one reference at `0x0066A7B9`; `p50a-strings.txt`, ASCII and
  UTF-16); no code path builds another name,
  so `Game.exe` does not read `eanimdata.d2` through this loader. (fn:ANIMDATA_Load@0x0066A770)

### 3. `UNIT_SetMode`, `UNIT_AnimInit` and `SUNIT_AnimInit`

```c
// fn:UNIT_SetMode@0x00624690, trimmed
if (!unit || unit->type == 5) return 0;
if (unit->mode != mode) {
    sub_0064C040(unit); unit->flagsC4 |= 1; unit->mode = mode;
    sub_006272E0_StatListsDropOnMode(unit);  UNIT_AnimInit(unit);  return 1;
}
if (!(unit->type == 1 && unit->mode == 1)) { sub_0064C040(unit); unit->flagsC4 |= 1; }
return 0;                                    // same mode: no animation restart
```

- [I] A request for the current mode never restarts the animation and never draws. (fn:UNIT_SetMode@0x00624690)
- [I] **`UNIT_AnimInit(unit)`** (fn:UNIT_AnimInit@0x00624390): `+0x4E = 0`, `+0x44 = UNIT_AnimStartFrame(unit) << 8`, then by **display** type
  (`UNIT_AnimTransform`):
  - 0 (player form): mode 3 or 19 → `sub_00620E80_RunVelocityStat` (P1.3); mode ≠ 18: `+0x30 = 0`,
    `UNIT_AnimSetRate`, `+0x48 = rec.frames << 8`; mode 18: `UNIT_SeqInit`, then `UNIT_AnimSetRate`.
  - 1 (monster form): a player shown as a monster in mode 13 or 15 → `RunVelocityStat`; mode ≠ 14: `UNIT_AnimSetRate`,
    `+0x30 = 0`, `+0x48 = rec.frames << 8`; mode 14: `UNIT_SeqInit`, then `UNIT_AnimSetRate`.
  - 2 (object), mode < 8 (else fatal): `+0x48 = FrameCnt[mode]`, `+0x44 = Start[mode] << 8`, rate `+0x4C` =
    `FrameDelta[mode]` when `Sync` ≠ 0; when `Sync` = 0, `FrameDelta − (FrameDelta >> 4) + RangeB(unit seed,
    FrameDelta >> 3)` (`>>` arithmetic on the sign-extended s16; no draw when `FrameDelta >> 3` < 1, objects G2),
    clamped to `[0, 0x7FFF]`. (0x00624500–0x0062456F)
  - 3 (missile): `+0x4C` = Missiles `animrate` (s16 at `+0xA0`) × 256 / 1024 truncated (a 64-bit path above 0x10000),
    `+0x48 = (u8 Missiles +0x178) << 8` (`AnimLen`'s low byte); 0 when the row is missing.
  - 4 (item): mode 3 → `+0x4C = 0`, `+0x48 = 0x1100`, `+0x44 = 0x1000`; mode 5 → `+0x4C = 0x100`, `+0x48 = 0x1100`.
  (fn:UNIT_AnimInit@0x00624390, tbl:Objects.txt:FrameCnt0, tbl:Objects.txt:Start0, tbl:Objects.txt:FrameDelta0,
  tbl:Objects.txt:Sync, tbl:Missiles.txt:animrate, tbl:Missiles.txt:AnimLen)
- [I] No server code advances an object, missile or item frame through these fields: `UNIT_AnimAdvance`'s 11 call
  sites are 7 in the monster mode functions and 4 in client code (`0x00463390`, `0x004B1280`), and
  `UNIT_AnimAdvanceLoop`'s 5 are client code (`0x004C1AD0`, `0x004D2610`–`0x004D30C0`). The missile's own frame is
  [skills/0002](../skills/0002-missiles.md)'s range countdown. (`p50a-anim-scan.txt` `CALL UNIT_AnimAdvance`,
  `CALL UNIT_AnimAdvanceLoop`)
- [I] **`SUNIT_AnimInit(unit)`** (9 call sites: the player mode starts, `PlayerDeath`, `PlayerDeathModeEnd`,
  `MonSetMode`, `MonsterInit`): `+0x4E = 0`; a monster in mode 14 or a player in mode 18 whose used skill has a
  sequence record → `UNIT_SeqInit`, `UNIT_AnimSetRate`, done; otherwise `+0x30 = 0`, `+0x44 = 0`, then
  `UNIT_AnimSetRate` if the unit has a path (`+0x2C`), else `UNIT_AnimSetRecord` only, and `+0x48 = rec.frames << 8`.
  So a scheduled mode starts from `+0x44 = 0` whatever `UNIT_AnimInit` set; the schedule reads the start frame from
  `UNIT_AnimStartFrame` itself. (fn:SUNIT_AnimInit@0x005533D0)

### 4. The start frame

```c
// fn:UNIT_AnimStartFrame@0x00623B10, trimmed (type, class, mode after UNIT_AnimTransform)
if (type == 0 && (mode == 7 || mode == 8 || ((mode == 15 || mode == 16) && UNIT_CanDualWield(unit)))) {
    item = sub_00623990_SkillSrcDamWeapon(unit, 1);
    wc = item ? (sub_00629FE0_ItemWeaponClassIndex(item) & 0xFFFF) : 0;   // Items +0xC0 code -> 1..7, 12; else 0
    return g_AttackStartFrames[wc * 7 + class];
}
return 0;
```

- [I] `g_ItemWeaponClassIndex` maps `bow` 1, `1hs` 2, `1ht` 3, `stf` 4, `2hs` 5, `2ht` 6, `xbw` 7, `ht1` 12; any
  other code (and no weapon) gives 0. The non-zero cells of `g_AttackStartFrames` are row 0 (`hth`) = 1 and rows 2–6
  = 2, for classes 0 and 1 only; rows 1 (`bow`), 7 (`xbw`) and 12 (`ht1`) are 0 for every class. The start frame is
  added at the schedule's start and after each wrap of the per-frame advance; `SKILL_AttackStart` (`0x0056CA40`) is
  its fourth caller. (data:g_AttackStartFrames@0x006E8E60, data:g_ItemWeaponClassIndex@0x007446A0,
  `p50a-anim-scan.txt` `START`, `IWCLS`, `CALL UNIT_AnimStartFrame`)

### 5. Sequences

- [I] **Which record.** `sub_00663310_UnitSeqRecord` (unit in `ESI`) takes the used skill and
  `sub_00643D00_SkillSeqIndex`: for a player the Skills `seqnum` byte (`+0x13`); for a monster the ordinal at MonStats
  `+0x188 + 2k` for the first `k` with Skill`k+1` = the skill (0 when absent or for skill 199, `DiabPrison`). An
  index < 1 means no sequence. A player gets `g_PlrSeqTables[seqnum] + 12 · col`, `col` from
  `sub_006632C0_PlrSeqColumn`: the composit weapon-class index (`g_WeaponClassTokens`: hth 0, bow 1, 1hs 2, 1ht 3, stf
  4, 2hs 5, 2ht 6, xbw 7, 1js 8, 1jt 9, 1ss 10, 1st 11, ht1 12, ht2 13) mapped through `g_PlrSeqColumns` (column order
  hth, 1ht, 2ht, 1hs, 2hs, bow, xbw, stf, 1js … ht2), fatal when unmapped; a monster gets
  `sub_00659E30_MonSeqRecord(ordinal)`. (fn:sub_00663310_UnitSeqRecord@0x00663310,
  fn:sub_00643D00_SkillSeqIndex@0x00643D00, tbl:Skills.txt:seqnum, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode)
- [I] `g_PlrSeqTables` (data:g_PlrSeqTables@0x007483B8) has 24 entries (0 null): 207 non-empty `{frames, length, frames}` entries holding 3 450 frame
  records; their event bytes are 0, 1 (432) or 3 (12). The table is indexed by `seqnum` with no bound test; the 25 stock
  rows with a `charclass` and a `seqnum` have at most 23, and the 4 rows above 23 have no `charclass`
  (`p50a-anim-rows.txt` `SEQNUM`), so only a player using one of those would read past the table. (`p50a-anim-scan.txt` `PSEQ`/`PSEQF`, `SCAN pseq entries=207 frames=3450`)
- [I] `MONSEQ_Load` loads `monseq` (6-byte records: u16 `sequence`, then `mode`, `frame`, `dir`, `event` bytes),
  sizes the index by the last record's `sequence` + 1 and, per record, sets the sequence's first-record pointer once and
  increments both its count fields. So `length = frames =` the sequence's row count. (fn:MONSEQ_Load@0x00659C60,
  data:g_pMonSeqIndex@0x0096C7B4)
- [I] **`UNIT_SeqInit`**: when a record exists, `+0x30 = record frames`, `+0x34 = length << 8`, `+0x38 = 0`,
  `+0x3C = 0x100`, `+0x48 = frames << 8`, `UNIT_SeqReadFrame(0)`, `+0xC4 |= 0x4000`. `UNIT_SeqReadFrame(prev)`
  reads the frame at `+0x38 >> 8`: `+0x40 = mode`, `+0x44 = frame << 8`, `+0x4E =` that frame's event when
  `+0x38 = prev`, else the last non-zero event of frames `(prev >> 8) + 1 … +0x38 >> 8` (0 when the position wrapped
  below `prev`); it returns whether `+0x40` changed. (fn:UNIT_SeqInit@0x00621260, fn:UNIT_SeqReadFrame@0x00621210,
  fn:SEQ_ReadFrame@0x00663410)
- [I] **`Unit+0x38`** is the sequence position of an advancing (monster) sequence. Its other writer,
  `sub_006212C0_UnitSetSeqPos(unit, n)` (`+0x38 = (+0x38 & 0xFF) + 256·n`), has 32 call sites: 19 client, 12 in the
  server skill range, and `PlrModeSkillFrame`, which at every player frame event of a unit with a used skill writes the event's index
  `b` (0x00580482–0x00580488; with no used skill it returns 2 first, 0x00580475). So for a player, `+0x38 >> 8` is the index of the code-1/2/4 event being run (0 for the
  first): skills/0001's `anim` 18 delay gate (`+0x38 & 0xFFFFFF00` = 0) means "on the first event", and do 35's parity
  is the event's. This answers skills/0001's open question on `Unit+0x38`. (fn:sub_006212C0_UnitSetSeqPos@0x006212C0,
  fn:sub_00580460_PlrModeSkillFrame@0x00580460, `p50a-anim-scan.txt` `CALLS sub_006212C0_UnitSetSeqPos`)

### 6. The event queue and the frame order

- [I] `sub_005416B0_EventQueueAt` (behind `sub_005417D0_UnitQueueEvent(game, unit, kind, frame, a, b)`) accepts kinds
  below 15, raises a frame ≤ the current one (`Game+0xA8`) to the current + 1, and appends the record to slot
  `frame & 63` of the unit type's list (`g_UnitTypeEventList`: player 0, monster 1, missile 2, object 3, item 4); the
  record allocator (`0x00540DF0`) also links it at the head of the unit's own chain (`Unit+0xDC`, next `+0x24`), the
  chain `UNIT_CancelEvents` walks. A frame of −1 goes to `sub_005415E0_EventQueueEveryFrame`: head of the type's every-frame
  list, flag 4. (fn:sub_005416B0_EventQueueAt@0x005416B0, fn:sub_005415E0_EventQueueEveryFrame@0x005415E0,
  struct:Game+0xA8, struct:Game+0xB8, struct:Unit+0xDC)
- [I] `sub_005414D0_GameRunUnitEvents` runs, in order: missiles (`+0xA0C`, then slot `+0x204`), players (`+0xA04`,
  `+0x004`), monsters (`+0xA08`, `+0x104`), objects (`+0xA10`, `+0x304`), items (`+0xA14`, `+0x404`). A slot list is
  walked from its oldest record and only records whose frame equals the current one run (then are freed); the
  every-frame list is walked from its newest. The object lists run through `sub_00541160_ObjEventsRun` (dispatch
  `0x00586AD0`). This answers skills/0002's "where the missile pass sits": first.
  (0x005414EE–0x00541589, fn:sub_00540F60_PlayerEventsRun@0x00540F60, fn:sub_00541060_MonEventsRun@0x00541060)
- [I] A record without a callback goes to the type's dispatch: players `g_PlayerEventFuncs[kind](a, b)` (kind 0 →
  `sub_005811D0_PlayerModeFrameEvent`, which calls `g_PlayerModeFrameFuncs[mode](a, b)` and on a return of 2
  `sub_00581020_PlayerModeEnd`; kind 1 → `PlayerModeEnd`); monsters `sub_005A7F80_MonEventDispatch`, which drops
  every kind but 3, 4, 5, 8 and 12 while the monster has state 1 (`freeze`) and is alive, then
  `g_MonEventFuncs[kind](a, b)` (kind 0 → `sub_005A7BA0_MonModeFrameEvent`: the mode record's frame function, called
  with the game and unit only (no code or index), **its return value unused**: passed back through the dispatch to
  `sub_00541060_MonEventsRun`, which does not test it, 0x005410C4–0x005410C9; kind 1 → `sub_005A7BE0_MonModeEndEvent`:
  the record's end function). With no mode record or no function in it, both handlers (and `MonSetMode`, 0x005A7DFD)
  call `0x005A7B30`: clear the used skill and, unless the unit is dead (`sub_005541B0_UnitIsDead`) in a mode other
  than DT and DD, `MonModeStartNeutral`. A dropped scheduled
  record is still freed, so a frozen monster loses those frame events and its mode end. (fn:sub_00581220_PlayerEventDispatch@0x00581220,
  fn:sub_005A7F80_MonEventDispatch@0x005A7F80, data:g_PlayerEventFuncs@0x006E1810, data:g_MonEventFuncs@0x006E2490)

### 7. The schedule

```c
// fn:SUNIT_ScheduleModeEvents@0x005539B0 (ECX game, EDX unit), trimmed
t = game->frame;  S = UNIT_AnimStartFrame(unit) << 8;
if (unit->pSeqFrames) { r = unit->seqRate;  L = unit->seqLength; }
else                  { r = unit->animRate; L = unit->animLength; }   // s16 sign-extended
if (r == 0) { UnitQueueEvent(1, game->frame + 1, 0, 0); return; }
f = S >> 8;  n = 0;  acc = S + r;
while (acc < L) {
    t += 1;
    for (; f <= (acc >> 8) && f < 0x90; f++) {
        e = unit->pSeqFrames ? SeqFrameEvent(f << 8) : unit->pAnimData->events[f];
        if (e == 1 || e == 2 || e == 4) UnitQueueEvent(0, t, e, n++);
        else if (e == 3)                UnitQueueEvent(0, t, 3, 0);
    }
    acc += r;
}
if (t == game->frame) t += 1;
UnitQueueEvent(1, t + 1, 0, 0);
unit->animFrame = game->frame << 8;
```

- [I] All comparisons are signed 32-bit; the events queued are kinds 0 and 1 only (13 `UnitQueueEvent` sites in the
  scheduler range `0x005539B0`–`0x00553F20`, `p50a-anim-scan.txt` `QEV`). The event-byte switch is a four-entry jump
  table at `0x00553AFC` (codes 1, 2, 4 → `0x00553A82`, 3 → `0x00553A9A`), outside Ghidra's function body.
  (0x00553A7B, 0x00553A8F, 0x00553AA5)
- [I] **Derived frame numbers** (from the loop of fn:SUNIT_ScheduleModeEvents@0x005539B0, not observed): frame `f ≥ S` fires at `T + k_f`, `k_f` the least
  `k ≥ 1` with `256·S + k·r ≥ 256·f`, provided `256·S + k_f·r < L`; so the first step carries frame `S` and the frames
  up to `(256·S + r) >> 8`. The frames after the last step's (`> (256·S + N·r) >> 8`) are never scanned. The end is at
  `T + N + 1` (`N ≥ 1` steps) or `T + 2` (`N = 0`), and no frame event shares its frame. Illustration (not a run):
  `L = 16·256`, `S = 0`, `r = 256`, an event byte at frame 8 → frames 0–1 at `T + 1`, frame 8 at `T + 8`, the end at
  `T + 16`.
- [I] **Callers** (6): the player starts for get-hit (`0x0057FE30`), block (`0x0057FDC0`), the skill modes
  (`sub_0057FE90_PlrModeStartSkillXY`, `sub_0057FEF0_PlrModeStartSkillUnit`) and death (`sub_00580EC0_PlayerDeath`),
  and `MonSetMode` for a scheduled monster mode. Each first cancels the unit's events 0 and 1
  (`SUNIT_CancelModeEvents`); the skill starts schedule **before** `SKILLS_StartUsedSkill`, so a start function can
  still reschedule. (`p50a-anim-scan.txt` `CALL SUNIT_ScheduleModeEvents`, 0x0057FED3)

#### 7.1 Reschedules (catalogue)

- [I] Three variants cancel events 0 and 1 and rebuild the schedule from an elapsed position `p` (in frames, counted
  as `p << 8` against `L`, no start frame): the same steps (`p·256 + k·r < L`, scanning to `(p·256 + k·r) >> 8`), but
  the scan starts at frame `p − 1`, every code 1–4 is queued with `b = 0`, and there is no `0x90` cap; the end as
  above:
  `sub_00553B10_RescheduleFromPct(pct)`: `p = (T − (+0x44 >> 8)) · (100 − pct) / 100` (signed division), `+0x44 =
  (T − p) << 8`; callers do 42 (Dragon Talon), 12 (Strafe), 13 (Fend) through `0x0056E210`.
  `sub_00553C70_RescheduleSkip(n)` (`n > 0` only): `p = T − (+0x44 >> 8) − n`; callers Inferno create/start and Blade
  Fury do/start. `sub_00553DC0_RescheduleAt(n)`: `p = n`, `+0x44 = (T − n) << 8`; callers do 67 (Charge), do 76
  (Whirlwind), Leap Attack. These are catalogue paths (plan 0046) and boundary oracles here.
  (fn:sub_00553B10_RescheduleFromPct@0x00553B10, fn:sub_00553C70_RescheduleSkip@0x00553C70,
  fn:sub_00553DC0_RescheduleAt@0x00553DC0, `p50a-anim-scan.txt` `CALL SUNIT_Reschedule*`)

### 8. The per-frame advance

```c
// fn:UNIT_AnimAdvance@0x00623E00, trimmed
unit->animEvent = 0;
if (unit->pSeqFrames) {
    prev = unit->seqPos;  unit->flagsC4 &= ~0x4000;
    unit->seqPos += unit->seqRate;  if (unit->seqPos >= unit->seqLength) unit->seqPos -= unit->seqLength;
    unit->animLength -= unit->seqRate;
    if (UNIT_SeqReadFrame(prev)) unit->flagsC4 |= 0x4000;
    return;
}
f = unit->animFrame >> 8;  if (unit->animRate >= 0x100) f += 1;     // 16-bit signed compare
unit->animFrame += unit->animRate;
while (unit->animFrame >= unit->animLength) {
    for (; f < (unit->animLength >> 8); f++) take(f);
    unit->animFrame -= unit->animLength;  f = 0;
    unit->animFrame += UNIT_AnimStartFrame(unit) << 8;
}
for (; f <= (unit->animFrame >> 8); f++) take(f);
// take(f): if pAnimData && f < 0x90 && events[f] in 1..4: animEvent = events[f]   (the last one wins)
```

- [I] With a rate below 0x100 the frame the unit stood on is scanned again, so an event byte can be taken on two
  consecutive frames; at 0x100 or more each frame is taken once. (0x00623E58–0x00623E6E)
- [I] `UNIT_AnimAtEnd`: in a sequence `+0x48 < 1`; else `+0x48 ≤ +0x44 + +0x4C`, i.e. the next advance would reach the
  length. The every-frame monster frame functions call it after advancing. (fn:UNIT_AnimAtEnd@0x006217C0)

### 9. Player modes

| Mode | Start (xy / unit) | Frame | Events | End → |
|---|---|---|---|---|
| 0 DT | — / `PlayerDeath` | `0x0057F070` (returns 1) | scheduled | `PlayerDeathModeEnd(17)` |
| 1 NU, 5 TN | `PlrModeStartNeutral` | `0x0057F080` (returns 1) | none | — |
| 2 WL, 3 RN, 6 TW, 19 KB | `PlrModeStartMoveXY` / `…MoveUnit` | `PlrModeMoveFrame` | every frame | neutral on arrival (§ 9.1) |
| 4 GH | `PlrModeStartGetHit` | `0x0057FE20` (returns 1) | scheduled | neutral |
| 9 BL | `PlrModeStartBlock` | `0x0057FE20` | scheduled | neutral |
| 7, 8, 10–16, 18 | `PlrModeStartSkillXY` / `…Unit` | `PlrModeSkillFrame` | scheduled | neutral |
| 17 DD | `PlayerDeathModeEnd` | `0x0057F070` | — | — |

(data:g_PlayerModeStartFuncs@0x006E1740, data:g_PlayerModeFrameFuncs@0x00732C10, `p50a-anim-scan.txt` `PMODE`)

- [I] `PlrModeStartNeutral(mode)`: mode 5 when the unit's room is a town, else the requested 1; cancel events 0 and 1;
  `SUNIT_SetMode`; clear the used skill. No event is queued. (fn:sub_0057F020_PlrModeStartNeutral@0x0057F020)
- [I] `PlrModeStartGetHit` / `PlrModeStartBlock`: `SUNIT_SetMode(4 or 9)`, `SUNIT_AnimInit`, clear the used skill,
  cancel, schedule. The get-hit and block lengths are therefore the schedule of their records at their rates (anim/0002 § 3.2).
  (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30, fn:sub_0057FDC0_PlrModeStartBlock@0x0057FDC0)
- [I] `PlrModeStartSkillXY`: path target, `SUNIT_SetMode`, `SUNIT_AnimInit`, cancel, schedule, clear `+0xC4` bit 6,
  `SKILLS_StartUsedSkill`. `PlrModeSkillFrame` then runs the do function on event code 1 or 2 with bit 6 clear
  (skills/0001 § 5); codes 3 and 4 do nothing there. (fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90)
- [I] **`PlayerModeEnd`** (event 1, or a frame function's 2): for modes 7, 8, 11, or a used skill with Skills `+0x06`
  bit 2 (`durability`; the mask byte `0x006CE270` = 4), `sub_00580310_HandsRefresh` and `0x00580380`; then mode 0 → `PlayerDeathModeEnd(17, 0, 0)`;
  mode 19 → (no cursor item) `PlayerModeAllowed(4, 1, 0)` and `g_PlayerModeStartFuncs[4].xy(4, −1, 0)` (get-hit);
  every other mode → `PlrModeStartNeutral(1, 0, 0)`. (fn:sub_00581020_PlayerModeEnd@0x00581020, 0x005810A2)

#### 9.1 Moving modes

- [I] `PlrModeStartMove` (mode in `EAX`): run (3) with stat 10 (stamina) 0, walk (2) and town walk (6) become 6 in a
  town, else 2; knockback (19) sets path type 8; then the path plan, clear the used skill; if the path refuses,
  neutral; else `SUNIT_SetMode`, cancel, `SUNIT_ModeEveryFrame` (event 0 every frame). No `UNIT_AnimAdvance` runs for
  a player. (fn:sub_0057F090_PlrModeStartMove@0x0057F090, fn:SUNIT_ModeEveryFrame@0x00553F00)
- [I] `PlrModeMoveFrame` steps the path (`sub_00554CA0_UnitMoveStep`, P1.3); in run, a failed stamina drain
  (`sub_0057F240_RunStaminaDrain`) restarts the move as a walk; it records a position history; on arrival (2) it sets neutral (or runs the queued interact or skill command) and returns 2, so
  `PlayerModeEnd` then sees mode 1 or 5. Its knockback branch (19 → get-hit) is therefore not reached from this path,
  and no event 1 is queued for mode 19. (fn:sub_00580C20_PlrModeMoveFrame@0x00580C20)

### 10. Monster modes

`sub_005A7C20_MonSetMode(game, cmd, flag)`, `cmd = {mode, unit, target unit, x, y, …}`:

- [I] An assert (fatal) under state 54 (`uninterruptable`); for a mode other than 3 sets the path target, plans the move
  (`sub_005A63F0_MonMovePlan`) and the attack stats (`sub_005A4F50_MonAttackStats`); runs the record's start; a 0
  clears the used skill and starts neutral. Then `+0xC4 |= 0x80000`, `SUNIT_AnimInit`, cancel events 0 and 1, and, by
  the record of the unit's **resulting** mode: `schedule` 0 → no event; else every-frame
  (`sub_005A6B10_MonModeEveryFrame`) → `SUNIT_ModeEveryFrame`, else `SUNIT_ScheduleModeEvents`.
  (fn:sub_005A7C20_MonSetMode@0x005A7C20, 0x005A7DE7–0x005A7E2B)
- [I] `sub_005A6B10_MonModeEveryFrame(mode)` (`g_MonModePerFrame`): always for WL, KB, SQ, RN; never for DT, NU, GH, BL,
  DD; for A1, A2, SC, S1–S4 when the MonStats2 `*mv` bit of the mode (`+0x104`) is set.
  (fn:sub_005A6B10_MonModeEveryFrame@0x005A6B10, tbl:MonStats2.txt:A2mv, `p50a-anim-scan.txt` `MPF`)

| Row | Mode | Start | Frame | End | `schedule` |
|---:|---|---|---|---|---:|
| 0 | DT | `MonDeathEvent`: `SUNIT_SetMode(0)`, death cleanup and drop | `0x005A7350`: unless moving (`0x0063E8D0`), mode 12 at once; moving: step, advance, 12 at the end | `0x005A72B0`: mode 12, `UNIT_DispatchEvent(13)`; `SplEndDeath` 1 changes the class to `minion1` (`MonChangeClass`), 2 kills the owner | 1 |
| 1 | NU | `MonModeStartNeutral` | `0x005A6DE0` (`UNIT_CancelEvents(0, 0)`: the unit's kind-0 events) | — | 0 |
| 2 | WL | `0x005A7520` (path refused → 0) | `0x005A8490`: blaze and spider-lay trails, step; arrival → generic end | — | 1 |
| 3 | GH | `0x005A7580`: not from 0/12; `MonModeAllowed(3)` | `0x005A6DE0` | generic | 1 |
| 4, 5, 7, 8, 9 | A1, A2, SC, S1, S2 | `MonModeStartSkill` | `MonAttackFrame` | generic | 1 |
| 6 | BL | `0x005A77C0` | `0x005A6DE0` | generic | 1 |
| 10 | S3 | `0x005A7490` | `0x005A74A0`: step, advance; at the end mode 11 (no event runs it: `schedule` 0) | (`ret`) | 0 |
| 11 | S4 | `0x005A74E0`: AI event at `T + 15` | `0x005A6DE0` | — | 0 |
| 12 | DD | `0x005A7390`: cancel events 8, 9 | `0x005A6DE0` | — | 0 |
| 13 | KB | `0x005A77D0`: `MonModeAllowed(3)` and `(13)`, path type 8, plan | `0x005A8630`: step, advance; at the end `MonKnockbackEnd` | `MonKnockbackEnd` | 1 |
| 14 | SQ | `0x005A7870`: clear bit 6, `SKILLS_StartUsedSkill` | `MonSeqFrame` | generic | 1 |
| 15 | RN | `0x005A7550` | `0x005A84F0`: step; arrival → generic end | — | 1 |

(data:g_MonModeRecords@0x006E2260, `p50a-anim-scan.txt` `MMODE`)

- [I] **Class overrides** (`sub_005A78A0_MonModeRecord`, only when MonStats `SplGetModeChart` is set): classes 243
  (`diablo`), 333 (`diabloclone`) and 705 (`uberdiablo`) take attack records for S3 (row 17) and S4 (row 16); 403
  (`trappedsoul1`) takes rows 18 (A1, A2: end `MonModeEndToS1`) and 19 (S1, S2: end `MonModeEndToS1b`), both ending in
  a mode-8 command whose `cmd` byte is 101 with MonStats2 `+0x105` bit 0 (`S1mv`) else 100; 417 (`shadowwarrior`) and
  418 (`shadowmaster`) row 20 for S4; 543 (`baalthrone`), 544 (`baalcrab`), 570 (`baalclone`) and 709 (`uberbaal`)
  row 7 for S3. All ten classes have `SplGetModeChart` set (the `.txt` and the `monstats.bin` byte `+0x1A5`), so
  every branch is reached on stock data (`p50b-anim-rows.txt` `OVR`, `OVRBIN`). *2026-10-27 (plan 0050 P1.2, `lane/p50b`):* corrected; the P1.1 text read the `.txt`
  one row off from record 410 on (the `Expansion` marker row was kept, `tools/anim_scan.py` `rows`, fixed), which
  named 418 and 544 wrongly and left 417, 543, 570, 705 and 709 "unreached" ([backlog](../../backlog/archive/2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md)).
  (fn:sub_005A78A0_MonModeRecord@0x005A78A0, 0x005A7923–0x005A7990, tbl:MonStats.txt:SplGetModeChart)
- [I] **`MonAttackFrame`**: with no used skill, an every-frame mode steps, advances and returns 2 at the end, and
  strikes (`MON_MeleeHit`, `COMBAT_DeliverQueued`) only on a frame whose event byte is 1 (mode 14: bit 6 set); a
  scheduled mode strikes on **each** of its scheduled events (any code 1–4). With a used skill it runs
  `SKILLS_DoUsedSkill` on every call, scheduled or every-frame (and a second time on the arrival frame of a move-first
  skill when the event byte is 1, or bit 6 set in mode 14), then advances. Since `MonModeFrameEvent` ignores the 2,
  an every-frame attack or skill mode with no end call of its own lasts until another command.
  (fn:sub_005A7670_MonAttackFrame@0x005A7670, 0x005A76DF–0x005A7741)
- [I] **`MonModeEndGeneric`** (the end of GH, BL, A1–S2, SQ; walk and run on arrival): for a `SplEndGeneric` base class
  in its listed mode (110 `vulture1` S1, 247 `frogdemon1` SQ, 136 `batdemon1` S3/S4, 230/231 any, 118 `willowisp1`
  WL, 403 any) only the AI event, unless frozen and alive; else, when `g_MonModeEndDirect[mode]` is 0 (all but WL and
  RN), the delayed hit of state 54 (`0x005544B0`), clear the used skill and a neutral command (`cmd` mode 1, the target
  kept, `0x6400`); WL and RN go to `UNIT_SetMode(1)` directly and then the AI event unless frozen and alive.
  (fn:sub_005A8030_MonModeEndGeneric@0x005A8030, data:g_MonModeEndDirect@0x0073C6D0, tbl:MonStats.txt:SplEndGeneric)
- [I] **`MonKnockbackEnd`**: path stop; if `MonModeAllowed(3)` refuses, the AI event at `T + 1`; base class 78
  (`sandleaper1`) the AI event at `T + 15` (`T + 45` stunned); else clear the used skill, `Unit+0xB0 = 0xA0` and a
  get-hit command (`cmd` mode 3, `0x6400`). (fn:sub_005A8520_MonKnockbackEnd@0x005A8520, struct:Unit+0xB0)
- [I] `MonModeStartNeutral` (also the refusal fallback): `SUNIT_SetMode(1)`; when the next AI event is not later
  than now, re-queue it at `T + 45` under state 21 (`stunned`), else at `T +` MonStats `aidel` (`aidel(N)`/`aidel(H)` by difficulty
  when `Game+0x6A` or `Game+0x74` is non-zero; 15 when 0). The AI delay is phase (5)'s.
  (fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0, tbl:MonStats.txt:aidel, struct:Game+0x6A)

### 11. Draws, seeds and the chaining reading (ADR-0014)

- [I] **Animation machine.** `RngCallGraph` over 29 roots (the functions of §§ 1–8 and `SUNIT_SetMode`), stopping at
  the fatal and allocator entries and at `0x005544B0`: 171 functions, one RNG call (`0x00624563 → RNG_RangeB` in
  `UNIT_AnimInit`), three indirect calls (the stat-list remove and stat-changed callbacks under
  `StatListsDropOnMode`, whose targets are stats/states'). `0x005544B0` is reached only from `EventQueueAt`'s
  kind-2 branch for a monster under state 54; the schedulers queue kinds 0 and 1 only (§ 7). (`p50a-rng-machine.txt`
  `summary: functions=171 rng=1 unclassified=1 indirect=3`)
- [I] **Object animation start**: one draw on the object's unit seed per `UNIT_SetMode` to a new mode when `Sync` = 0,
  after `StatListsDropOnMode`; its value is the rate (§ 3), which no server code reads back. Chained: the object's
  unit seed (objects G2). Players, monsters, missiles and items draw nothing at an animation start.
  (fn:UNIT_AnimInit@0x00624390, 0x00624563)
- [I] **Mode functions.** Over the player and monster mode tables (39 roots), stopping also at the skill, combat,
  path and AI entries (`SKILLS_StartUsedSkill`, `SKILLS_DoUsedSkill`, `MON_MeleeHit`, `COMBAT_DeliverQueued`,
  `MonAttackStats`, `PathPlan`, `MonMovePlan`, `UnitMoveStep`, `0x005B1740`, the mode commands, `UnitInteract`): 2 355
  functions, 128 with draws, 118 indirect calls unfollowed (`p50a-rng-modes.txt` `summary`), reached through the death paths (`PlayerDeath`'s item handling, `PlayerDeathModeEnd`'s
  corpse and the portal close that updates rooms, `MonDeathEvent`'s drops through `TC_ResolveDrops` and its area
  damage) and the walk frame's state trails (`MissileCreate`). Of the mode functions' own calls:
  - `sub_0057EEC0_PlayerModeAllowed` (from `PlayerModeEnd` and every unforced mode command): for a used skill with Skills
    `interrupt` under state 42 (`concentration`), `Range(player unit seed, 100)` against stat 164
    (`skill_concentration`) of that state's list; below it the interrupt is refused. P1.3 reads it as a gate.
    (0x0057EF7C, tbl:Skills.txt:interrupt)
  - `sub_005A6FF0_MonDeathEvent`: base class 212 (`bonefetish1`) only, after a death missile, `RangeB(unit seed, …)`
    for its area damage (0x005A726C, then `0x0057E090` → `MISSILE_ApplyDamage`); a death detail, not timing.
  - `0x005A6B70` (under `MonAttackFrame`'s no-skill branch, base class 63 `quillrat1`): a **local** seed
    (`RNG_SeedInitOne`, `RNG_SeedInit(…, 0x53454953)`, high word the unit guid) for the spread of its missiles; no game
    or unit seed. (`p50a-rng-modes.txt`)
- [I] **Event kinds** (ADR-0014; fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:UNIT_AnimAdvance@0x00623E00):
  - *mode start*: inputs the mode, the unit's type, class, transform states, used skill, weapon items, the record
    (tables), the stats behind the rate (P1.2), `Game+0xA8`; outputs `+0x10`, the frame fields, the queued events 0/1;
    draws: the object unit-seed draw only.
  - *frame event* (kind 0): inputs the code `a` and index `b`; outputs the mode frame function's effects (the do, the
    melee hit); draws: those of the do and the hit (plans 0045, 0037), none of the animation's.
  - *mode end* (kind 1): inputs the mode; outputs the next mode (§§ 9–10) and its start; draws: the next start's,
    `PlayerModeAllowed`'s, the AI's.
  - *frame advance* (every-frame monsters): `UNIT_AnimAdvance`, no draw.
  Chaining: the animation adds no seed of its own; an object's start draw chains on its unit seed.

### 12. Boundary recommendation (preliminary, for the P1.3 review)

- Oracles: the mode request (players, plan 0045), the AI's command (monsters, plan 0052), the path step's result (2 =
  arrived; phase (5)), the catalogue reschedules of § 7.1 (plan 0046), and the rate value until P1.2's model.
- Event entry points to log: `SUNIT_ScheduleModeEvents` (in: `T`, `S`, `r`, `L`, the record name; out: the queued
  `(kind, frame, a, b)` list), `UNIT_AnimInit` (type, mode, record, `+0x44`/`+0x48`/`+0x4C`, the object seed before and
  after), the kind 0/1 dispatch (frame, unit, code, index), `UNIT_AnimAdvance` for every-frame monsters (per frame:
  a log window, ADR-0014 § Log volume).

## Data touched

- Tables: tbl:CharStats.txt:baseWClass, tbl:MonStats.txt:Code, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode,
  tbl:MonStats.txt:SplGetModeChart, tbl:MonStats.txt:SplEndGeneric, tbl:MonStats.txt:SplEndDeath,
  tbl:MonStats2.txt:BaseW, tbl:MonStats2.txt:compositeDeath, tbl:MonStats2.txt:mDT, tbl:MonStats2.txt:A1mv,
  tbl:Objects.txt:FrameCnt0, tbl:Objects.txt:FrameDelta0, tbl:Objects.txt:Start0, tbl:Objects.txt:Sync,
  tbl:Missiles.txt:animrate, tbl:Missiles.txt:AnimLen, tbl:Skills.txt:seqnum, tbl:Skills.txt:interrupt,
  tbl:Skills.txt:durability, tbl:States.txt:gfxtype, tbl:States.txt:gfxclass, tbl:Weapons.txt:wclass, tbl:Weapons.txt:2handedwclass; the PlrMode,
  MonMode and ObjMode tokens; `animdata.d2` ([formats/animdata](../../formats/animdata.md): `+0x00` name, `+0x08` frames,
  `+0x0C` speed, `+0x10` events); `monseq.txt` ([MonSeq](../../tables/MonSeq.md): `sequence`, `mode`, `frame`, `dir`,
  `event`); the PlrType and object-type
  tokens (`0x0065B480`, `0x0065B570`; [PlrType](../../tables/PlrType.md), [ObjType](../../tables/ObjType.md)).
- Unit: struct:Unit+0x10, struct:Unit+0x2C, struct:Unit+0x30 … struct:Unit+0x50 (§ 1), struct:Unit+0xB0,
  struct:Unit+0xC4 (bits 0, 6, 14, 19), struct:Unit+0xC8 (bit 3), struct:Unit+0xDC; game: struct:Game+0xA8, struct:Game+0xB8.

## Dead ends

- Ghidra's cross-references to `UnitQueueEvent` list 2 sites in `SUNIT_ScheduleModeEvents`; the two frame-event calls
  sit in jump-table case blocks outside the function body. The objdump scan (`QEV`) finds all four.
- `sub_005A7BA0_MonModeFrameEvent` looks like `sub_005811D0_PlayerModeFrameEvent` but never tests the frame
  function's return; do not assume a monster mode ends on a 2.

## Open questions

- [L] What ends an every-frame monster attack or skill mode (`*mv` set, `MonAttackFrame`), given the ignored 2, and
  what ends a generic S3 (row 10, `schedule` 0: `MonSetMode` queues no event, so its frame function `0x005A74A0`
  and its S4 transition are run by nothing read; the class overrides for S3, rows 7 and 17, are scheduled); the AI
  command (phase (5), plan 0052) is the likely path. Phase 2 logs it (plan 0050 P1.1 review, ruling (b)).
- [L] Whether the `PlayerModeEnd` knockback → get-hit branch is reached at all (no event 1 is queued for mode 19, and
  the move frame sets neutral first); other callers of `PlayerModeEnd` than `0x005811D0` and the event table: none
  by the call scan.
- [L] The intra-frame order of a unit's every-frame event against its slot events when both exist (only the list order
  of § 6 is read).
- ~~The format and table docs for `animdata.d2` and `monseq`.~~ *2026-10-27 (P1.1 review):* written by plan 0050
  Phase 0 ([formats/animdata](../../formats/animdata.md), [MonSeq](../../tables/MonSeq.md)).
- ~~The PlrType and object-type token tables have no doc.~~ *2026-10-27 (P1.2, `lane/p50b`):* written by plan 0050's
  archivist entry ([PlrType](../../tables/PlrType.md), [ObjType](../../tables/ObjType.md)).
- ~~`UNIT_AnimSetRate`'s branches.~~ *2026-10-27 (P1.2):* read in [anim/0002 §§ 1–3](0002-rates.md).
- [L] `sub_0064C040` (called by `UNIT_SetMode`) and `0x0057C980` (by `SUNIT_SetMode`) are not read.
