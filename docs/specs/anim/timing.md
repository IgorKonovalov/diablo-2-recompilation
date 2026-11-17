---
spec: anim/timing
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, stats/aggregate, stats/states, monsters/stats, skills/dispatch, combat/overview, combat/delivery, objects]
consumed_by: [anim/movement, skills/dispatch, skills/missiles, combat/overview, combat/delivery, objects, sim/frame]
tags: {C: 175, I: 86, L: 22}
updated: 2026-11-17
---

# Animation timing: modes, records, the schedule, the frame advance, rates, breakpoints and the gates

## Purpose

When a unit enters a mode, the server looks up the mode's animation record, sets the unit's frame fields, computes
its rate from the unit's stats and weapon, and either **schedules** the mode's frame events and its end on the game
frames they fall on, or (for a monster's every-frame modes) **advances** the frame once per game frame. The frame
events run the do function, the melee strike and the sequence steps; the end starts the next mode. This page
specifies that machinery for players, monsters and objects, the rate of every mode and the breakpoints it gives, and
the gates that sit on it: the do frame, the skill delay, hit recovery, the block, the get-hit roll and the player's
mode tests. How far a moving unit gets per frame is [anim/movement](movement.md). Which mode a unit is asked to
enter, and when, is an input: the request for a player ([skills/dispatch § B](../skills/dispatch.md#b-the-request)),
the AI's command for a monster (phase (5)). Overview and boundary: [anim](README.md).

```mermaid
flowchart LR
  req["mode request or AI command<br/>(oracle)"] --> set["UNIT_SetMode<br/>§ C"]
  set --> init["UNIT_AnimInit / SUNIT_AnimInit<br/>record § B, start frame § D"]
  init --> rate["UNIT_AnimSetRate<br/>§ J"]
  rate --> sch{"scheduled or<br/>every frame?"}
  sch -->|scheduled| q["SUNIT_ScheduleModeEvents<br/>kind 0 per event byte, kind 1 end § E"]
  sch -->|every frame| ef["SUNIT_ModeEveryFrame<br/>UNIT_AnimAdvance § F"]
  q --> run["GameRunUnitEvents § H"]
  ef --> run
  run --> fe["frame event: do, strike § L"]
  run --> end1["mode end: next mode § I"]
```

## Entry points

| When | Function | Tag |
|---|---|---|
| A unit's mode changes | fn:UNIT_SetMode@0x00624690 → fn:UNIT_AnimInit@0x00624390 | [C] (run:2026-10-30-anim-p3b: every new-mode set followed by one `UNIT_AnimInit` rate call or an object start, 280 292; [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) |
| A server player or monster mode starts | fn:SUNIT_AnimInit@0x005533D0 | [C] (run:2026-10-30-anim-p3b: its rate call precedes all 46 722 schedules, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) |
| A scheduled mode's events are queued | fn:SUNIT_ScheduleModeEvents@0x005539B0 | [C] (run:2026-10-27-anim: 25 848 schedules) |
| An every-frame mode starts | fn:SUNIT_ModeEveryFrame@0x00553F00 | [C] (run:2026-10-27-anim: 9 682 starts) |
| Each game frame, the unit event lists run | fn:sub_005414D0_GameRunUnitEvents@0x005414D0 | [C] (run:2026-10-30-frame-emu-2, families `tick` and `run`) |
| An every-frame monster's frame advances | fn:UNIT_AnimAdvance@0x00623E00 | [C] (run:2026-10-27-anim, run:2026-10-27-anim-p2: 4 110 advances over both parts) |
| A unit's rate is (re)computed | fn:UNIT_AnimSetRate@0x00623F50 | [C] (run:2026-10-27-anim: 298 373 calls) |
| A player's mode ends | fn:sub_00581020_PlayerModeEnd@0x00581020 | [C] (run:2026-10-30-anim-p3b: 10 718 kind-1 dispatches, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k); `g_PlayerEventFuncs[1]` is this function, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| A monster's mode command | fn:sub_005A7C20_MonSetMode@0x005A7C20 | [C] the start's order, rate, cancels, then schedule or every-frame event (run:2026-10-30-anim-p3b, 140 936 starts, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k); [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)); [I] that each logged start is `MonSetMode`'s (`SUNIT_AnimInit`'s callers not scanned) |
| A hit reaches the defender's mode | fn:COMBAT_GetHit@0x0057CEE0 | [C] the commands by result bit (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); [I] the town return and the kill branch (M1) |
| The get-hit decision | fn:sub_0057CB00_GetHitRoll@0x0057CB00 | [C] (run:2026-10-27-anim: 7 195 calls) |
| A player mode request is tested | fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0 | [C] (run:2026-10-30-anim-p3b: 26 574 `PlrModeLeaveOk` and 50 321 `PlayerModeAllowed` returns at the requests, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) |

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| `animdata.d2` (fmt:animdata#layout: `name`, `frames`, `speed`, `events`) | the record of a mode: length, speed, the event byte of each frame (§ B) |
| tbl:PlrType.txt:Token, tbl:MonStats.txt:Code, tbl:ObjType.txt:Token | the first part of the record name (§ B) |
| tbl:PlrMode.txt:Token, tbl:MonMode.txt:token, tbl:ObjMode.txt:Token | the mode token of the name (§ B) |
| tbl:CharStats.txt:baseWClass, tbl:Weapons.txt:wclass, tbl:Weapons.txt:2handedwclass, tbl:MonStats2.txt:BaseW | the weapon class of the name (§ B) |
| tbl:MonStats2.txt:compositeDeath, tbl:MonStats2.txt:mDT (the `m<mode>` bits), tbl:MonStats2.txt:A1mv (the `*mv` bits) | the death record, the modes a class has, the every-frame attack and skill modes (§§ B, I) |
| tbl:States.txt:gfxtype, tbl:States.txt:gfxclass, tbl:States.txt:meleeonly | the shapeshift display and its attack base (§§ B, J) |
| tbl:Skills.txt:seqnum, tbl:Skills.txt:seqtrans, tbl:Skills.txt:UseAttackRate, tbl:Skills.txt:interrupt, tbl:Skills.txt:delay, tbl:Skills.txt:durability | sequences, the rate branch, the mode tests, the delay (§§ G, J, L, M) |
| tbl:MonStats.txt:Sk1mode, tbl:MonStats.txt:Skill1, `monseq` (tbl:MonSeq.txt:sequence, `mode`, `frame`, `event`) | a monster's sequence (§ G) |
| tbl:MonStats.txt:SplGetModeChart, tbl:MonStats.txt:SplEndGeneric, tbl:MonStats.txt:SplEndDeath, tbl:MonStats.txt:aidel | the monster mode overrides and ends (§ I) |
| tbl:Objects.txt:FrameCnt0, tbl:Objects.txt:Start0, tbl:Objects.txt:FrameDelta0, tbl:Objects.txt:Sync, tbl:Objects.txt:Mode1, tbl:Objects.txt:Mode2, tbl:Objects.txt:FrameCnt1 | an object's frame fields, its start draw and its operate end (§§ C, I) |
| tbl:Missiles.txt:animrate, tbl:Missiles.txt:AnimLen | a missile's frame fields (§ C) |
| tbl:ItemStatCost.txt:Stat (stats 67–69, 93, 95, 96, 99, 102, 105, 164), tbl:ItemStatCost.txt:damagerelated | the rate terms (§ J), the block gate (§ M) |
| tbl:Weapons.txt:speed, tbl:Weapons.txt:hitclass, tbl:MonStats2.txt:HitClass, tbl:Missiles.txt:HitClass (codes: [HitClass](../../tables/HitClass.md)) | the attack rate (§ J), the hit class (§ M) |

### Runtime state

| State | Type | Source |
|---|---|---|
| struct:Unit+0x44 | i32, frame 8.8 (a scheduled mode: the schedule's game frame `<< 8`) | § C, § E, § F |
| struct:Unit+0x48 | i32, length, frames `<< 8` (a sequence: the frames left `<< 8`) | § C, § G |
| struct:Unit+0x4C | i16, rate 8.8 per game frame, clamped to `[0, 0x7FFF]` | § J |
| struct:Unit+0x4E | u8, the event byte of the frames last crossed (1–4), else 0 | § F, § G |
| struct:Unit+0x50 | the `animdata.d2` record (`AnimDataRec`) | § B |
| struct:Unit+0x30, struct:Unit+0x34, struct:Unit+0x38, struct:Unit+0x3C, struct:Unit+0x40 | a sequence's frames, length `<< 8`, position 8.8, step 8.8, current frame's mode | § G |
| struct:Unit+0xC4 | bit 6 (the do ran), bit 14 (sequence mode changed), bit 19 (monster mode command) | § G, § L |
| struct:Unit+0x20 | the unit seed (`Seed64`, [rng](../rng/README.md)) | the object start draw (§ C), the get-hit roll (§ M) |
| struct:Game+0xA8 | i32, the current game frame `T` | § E, § H |
| the unit's stat lists | stats 67, 68, 69, 93, 96, 99, 102, 105 as the aggregate holds them ([stats/aggregate](../stats/aggregate.md)) | § J |

### Inputs and oracles

| Input | How it enters | Tag |
|---|---|---|
| The mode request (a player's packet, the pilot's client) and the AI's command | logged and taken as given (ADR-0004); the server's handling from the request on is specified | [C] (run:2026-10-27-anim) |
| A catalogue function's own event queue after a cancel, kinds 0 with `a ≠ 0` and 1 (§ E1) | logged at the call (logger rev 6) and taken as given (ADR-0004); the dispatches after it compared | [C] (fn:sub_005417D0_UnitQueueEvent@0x005417D0, run:2026-10-27-anim-p2) |
| A catalogue function's reschedule (§ E3), its queued kinds 2 and 12, its writes of the frame word or `+0x4E` | outputs taken as given (plan 0046's catalogue); the reschedules' rebuilt lists are compared with E3 | [C] the 893 logged reschedules of `RescheduleSkip` and `RescheduleAt` equal E3 (fn:sub_00553DC0_RescheduleAt@0x00553DC0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); [I] the kinds 2 and 12, logged but their dispatches not, and the writes, not compared (fn:sub_005417D0_UnitQueueEvent@0x005417D0) |
| The stats behind the rate | values of the aggregate | [C] (run:2026-10-27-anim) |

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| fallback record | 2 048 frames, speed 256, no event byte | fn:ANIMDATA_Load@0x0066A770 (0x0066A80A, 0x0066A814) | [C] (4 834 returns in play, run:2026-11-16-sweep2-H6d) |
| event-byte scan bound | frames `< 0x90` (144) | fn:SUNIT_ScheduleModeEvents@0x005539B0 (0x00553A40) | [C] (run:2026-11-16-sweep2-s6e, family `sched`: 158 cases with events past 0x90) |
| rate bonus `k` | 120 (stats 93, 99, 102, 105), 150 (stat 96) | data:g_AnimRateBonus@0x006E8E24 | [C] (run:2026-10-27-anim-rates-emu) |
| attack and default factor clamp | 15..175 | fn:UNIT_AnimSetRate@0x00623F50 | [C] the attack's 175 (run:2026-10-27-anim); the attack's 15 at `X` 10 and the default's 15 (run:2026-11-16-sweep2-H6d); [I] the attack floor's threshold for `X` 11–14, the default's 175 |
| cast factor cap | 175 | fn:UNIT_AnimSetRate@0x00623F50 (0x00623FDA–0x00623FE1) | [C] (run:2026-10-27-anim) |
| player sequence attack term | −30 | 0x00624290–0x0062429B | [C] (run:2026-10-27-anim) |
| block gate | `⌊stat 102 / 8⌋ + 15` frames | 0x0057D282–0x0057D2D6 | [C] (run:2026-10-27-anim) |
| `PlrModeEndPending` slack | 5 frames | fn:sub_0057ED70_PlrModeEndPending@0x0057ED70 | [I] |

## Algorithm

### A. The two clocks and the event kinds

```mermaid
flowchart TD
  start["mode start"] --> k{"unit type and mode"}
  k -->|"player: attack, cast, skill, GH, BL, DT, SQ"| S["scheduled at the start<br/>kind 0 per event byte, kind 1 end"]
  k -->|"player: WL, RN, TW, KB"| M["every frame: move frame<br/>no animation advance"]
  k -->|"monster: WL, RN, KB, SQ, *mv attack or skill"| E["every frame: step and UNIT_AnimAdvance"]
  k -->|"monster: other A1–S2, GH, BL, DT"| S
  k -->|"monster: NU, S3, S4, DD"| N["no event queued"]
  k -->|"object, missile, item"| O["fields set, no server advance"]
```

- A1. [C] **Two clocks.** A player's attack, cast, skill, get-hit, block, death and sequence modes, and a monster's
  A1–S2, get-hit, block and death modes outside its `*mv` bits, are **scheduled** at their start: one pass of
  `SUNIT_ScheduleModeEvents` queues a unit event of kind 0 per frame-event byte on the game frame it falls on and one
  event of kind 1 (the mode end). A monster's walk, run, knockback and sequence modes, and its A1, A2, SC and S1–S4
  modes whose MonStats2 `*mv` bit is set, run an **every-frame** event that steps and calls `UNIT_AnimAdvance`.
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:SUNIT_ModeEveryFrame@0x00553F00, fn:UNIT_AnimAdvance@0x00623E00,
  data:g_MonModePerFrame@0x006E23D0, tbl:MonStats2.txt:A1mv, run:2026-10-30-anim-p3b) Every player and monster start
  of the 131 logs falls on the clock stated, with 0 mismatches (players schedule modes 0, 4, 7, 9–12, 14–16 and 18 and
  run 2, 3 and 19 every frame; S1 127 times and S2 16 times every frame by `*mv`; [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)). The schedule and the
  advance themselves are E1's and F1's. [C] (run:2026-10-27-anim)
- A2. [C] A player's walk, run, town walk and knockback run an every-frame event too, which steps the path but never
  calls `UNIT_AnimAdvance` (`PlrModeMoveFrame` reaches no advance); a monster's neutral, S3, S4 and dead mode records
  have `schedule` 0. Of `UNIT_AnimAdvance`'s 11 call sites the 7 at or above 0x00520000 are all in the monster mode
  functions, and the other 4 and all 5 of `UNIT_AnimAdvanceLoop`'s lie below it, so no advance at or above it reaches
  an object, a missile or an item (a second tool, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)). (fn:sub_0057F090_PlrModeStartMove@0x0057F090,
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:UNIT_AnimAdvanceLoop@0x00621310) [I] That the sites below 0x00520000 are
  client code is the symbol names' reading, so objects, missiles and items getting no server advance rests on it.
  (fn:UNIT_AnimAdvance@0x00623E00)
- A3. [I] **Event kinds** (ADR-0014): *mode start* (inputs the mode, type, class, transform states, used skill, weapon
  items, record, the rate's stats and `T`; outputs `+0x10`, the frame fields, the queued kind-0/1 events; the object
  start draw only), *frame event* (kind 0 with code `a` and index `b`; outputs the mode frame function's effects),
  *mode end* (kind 1; outputs the next mode and its start), *frame advance* (every-frame monsters; no draw), *rate
  change* (§ J; no draw, no queued event). (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:UNIT_AnimAdvance@0x00623E00,
  fn:UNIT_AnimSetRate@0x00623F50) [C] The draws in it: a second tool finds none under the advance (27 functions), the
  rate (101) or the schedule (34), and the object start draw is the only one at a start ([anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)). The input and output
  lists stay as read. (fn:UNIT_AnimInit@0x00624390)

### B. The animation record

```
B1. UNIT_AnimSetRecord(unit, type, class, mode):                  [C] (fn:UNIT_AnimSetRecord@0x00620F00, fn:ANIMDATA_Lookup@0x0066A9B0, fn:COMPOSIT_BuildCofName@0x0064F5B0, run:2026-10-27-anim, all of B1)
      (type, class, mode) are the display values (B3)
      name ← token(type, class) ‖ modeToken(type, mode) ‖ weaponClass(unit, type, class, mode)   ; spaces removed
      unit.+0x50 ← ANIMDATA_Find(name) or, when none, the fallback record (2 048 frames, speed 256, no event)
          ; [C] none for an absent name (run:2026-11-16-sweep2-s6e); the fallback's values: 4 834 returns in play (run:2026-11-16-sweep2-H6d)

B2. ANIMDATA_Find(name):                                          [C] (fn:ANIMDATA_Find@0x0066A8F0, run:2026-11-16-sweep2-s6e, all of B2)
      uppercase name in place ('a'..'z')
      block: u8 ← (sum of the name's bytes) & 0xFF
      for each record of that block, in order:
        fatal if the name is longer than 8 characters          ; inside the loop: an empty block returns none
        fatal if the record's name is longer than 8 characters ; [I] read from the code, no stock record (0x0066A94D–0x0066A957)
        if the record's first two dwords equal the name's: return it
      return none
```

- B1. [C] **The name**, met at all 298 373 logged rate calls: a player's PlrType token, the PlrMode token (`GH` for
  modes 18 and 19), and `COMPOSIT_WeaponClass` (CharStats `baseWClass` without a weapon, the item's one- or
  two-handed class, `hth` in modes 0 and 17 and for a throw with a class other than `1hs`, `1ht`, `1js`, `1jt`, `1ss`,
  `1st`, the dual classes `1ss` and `ht2`); a monster's MonStats `Code`, the MonMode token (`KB` → `GH`) and MonStats2
  `BaseW` (`hth` in modes 0 and 12 without `compositeDeath`); a shapeshifted player's display class with the mode
  mapped through `g_PlrToMonMode` and its fallback chain. (fn:COMPOSIT_BuildCofName@0x0064F5B0,
  fn:COMPOSIT_WeaponClass@0x0064F060, fn:UNIT_AnimTransform@0x00645270, data:g_PlrToMonMode@0x006EB348,
  tbl:CharStats.txt:baseWClass, tbl:MonStats2.txt:BaseW, run:2026-10-27-anim)
- B1. [C] **The dual classes** (an ADR-0015 map on a declared inventory and item image, 6 400 cases): for the
  Barbarian (class 4) with two enabled weapon items (type 45) in the hands, the class indices of the *primary* hand
  and the other give `1js` for 2 with 3, `1jt` for 3 with 3, `1st` for 3 with 2 and `1ss` for any other pair; the
  Assassin (class 6) with two such items gets `ht2`. The primary is `INV_GetPrimaryWeapon`'s hand (body location 5
  tested first); with none, the right hand is written as primary at inventory `+0x1C` and used.
  (fn:COMPOSIT_WeaponClass@0x0064F060, 0x0064F1E5–0x0064F2D5, 0x0063D1D0, run:2026-11-16-sweep2-s6f,
  [anim/0001 § 2](../../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback))
- B1. [C] **The fallback record is returned in play:** 4 834 times in 11 sessions (`MonStatsSpeeds` at the load 4 202,
  `UNIT_AnimSetRecord` 632 for classes FS, BN and MO in mode 14), each with frames 2 048, speed 256 and the name and
  144 event bytes zero, its name absent from `animdata.d2`. (fn:ANIMDATA_Lookup@0x0066A9B0, 0x0066AA02, 0x00650F4D,
  0x00650FB3, 0x00620F40, run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d))
- B1. [I] Which Items codes carry the class indices 2 and 3 (`1hs` and `1ht` by the stock code map) is
  `g_ItemWeaponClassIndex`'s runtime content; no case separates them.
  A right hand that is not an item unit returns 0 with the index unwritten (0x0064F121). An object's name is its
  ObjType token, the ObjMode token and `hth`, but the server never looks an object's record up (C3).
  (fn:COMPOSIT_WeaponClass@0x0064F060, data:g_ItemWeaponClassIndex@0x007446A0, fn:ANIMDATA_Lookup@0x0066A9B0,
  run:2026-10-27-anim)
- B2. [C] **Duplicate names.** Of two records with one name (29 names in `animdata.d2`, 9 with different content), the
  one earlier in its block wins (87 of 87 duplicate cases, run whole on the stock file). (fn:ANIMDATA_Find@0x0066A8F0,
  run:2026-11-16-sweep2-s6e) [I] That the block order is the file's (the loader's walk, not run), and that only
  `%s\AnimData.d2` under `DATA\GLOBAL` is loaded (d2exp's copy by the archive precedence; `eanimdata.d2` is not read
  by this loader). (fn:ANIMDATA_Load@0x0066A770, [formats/animdata](../../formats/animdata.md#layout))
- B2. [I] The compare is of the first two dwords of the 8-byte buffers, bytes after the NUL included; no stock name
  leaves room for such bytes. (fn:ANIMDATA_Find@0x0066A8F0)
- B2. [I] **The COF bundles are not a source.** The client loads `cmncof_a*.d2` into its own COF cache, which only its
  drawing reads; 11 bundle COFs differ from `animdata.d2` in frames per direction and 2 in event frames, and none of
  that reaches the server's mode lengths, which come from `animdata.d2` alone. (fn:sub_0046F310_CofBundleLoadAct@0x0046F310,
  [data/0006 § 4](../../findings/data/0006-loaded-tables-and-bundles.md#4-the-cof-bundles-plan-item-4),
  [formats/cofbundle](../../formats/cofbundle.md#layout))
- B3. [C] **The shapeshift display.** With `Unit+0xC8` bit 3 set, the first state of the DataTables transform list
  that the unit has decides: States `gfxtype` 1 shows a player as a monster of class `gfxclass` (its mode mapped by
  `g_PlrToMonMode` and the MonStats2 fallback); the record, the start frame and the rate all take the display values
  (758 transformed calls of the werewolf and werebear, display classes 430 and 431). (fn:UNIT_AnimTransform@0x00645270,
  fn:sub_00645190_PlrToMonMode@0x00645190, tbl:States.txt:gfxtype, run:2026-10-27-anim)
- B3. [C] **The fallback's steps** (ADR-0015 maps, every callee run): down 5, 7 → 4; 6 → 3; 9–11 → 8; 15 → 2;
  others → 1 until MonStats2 `mDT`…`mRN` has the mode (bit `m` of the u16 at `+0xF0` is the `m<mode>` column on all
  609 rows), over the 20 player modes on all 734 stock MonStats classes. `gfxtype` 2 shows a monster as a player of
  class `gfxclass`, its mode mapped by `g_MonToPlrMode`, except display class 6 in monster mode 4, which takes player
  mode 12 (0x00645328–0x0064533E). A form of the other kind (`gfxtype` 1 on a monster, 2 on a player) sets the display
  type and class and keeps the mode. (fn:sub_00645190_PlrToMonMode@0x00645190, fn:UNIT_AnimTransform@0x00645270,
  data:g_MonToPlrMode@0x006EB308, run:2026-11-16-sweep2-s6e-2)
- B4. [C] A record's `frames` gives `+0x48 = frames << 8` at every non-sequence start (all 45 913 non-sequence
  schedules and 907 first every-frame advances of run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)), and the schedule reads its event
  byte for frame `f` only for `f < 0x90` (0x00553A40, run:2026-11-16-sweep2-s6e). (0x00624470, 0x006244F1) [I] Its
  `speed` is the base of the rate (§ J), and the advance's own `0x90` bound (F1) is read from the code. (0x00623E95)

### C. The mode start

```
C1. UNIT_SetMode(unit, mode) → bool:                              [C] (fn:UNIT_SetMode@0x00624690, run:2026-10-30-anim-p3b, all of C1 but the lines marked)
      if unit is null or unit.type = 5: return 0                  ; [I] no stock case (fn:UNIT_SetMode@0x00624690)
      if unit.mode = mode: refresh only (no animation start); return 0
      unit.mode ← mode;  drop the stat lists flagged to end on a mode change   ; [I] the drop (fn:UNIT_SetMode@0x00624690)
      UNIT_AnimInit(unit);  return 1

C2. UNIT_AnimInit(unit):                                          [C] (fn:UNIT_AnimInit@0x00624390, run:2026-10-30-anim-p3b, run:2026-11-16-sweep2-s6e-3, run:2026-11-16-sweep2-H6d, all of C2)
      +0x4E ← 0;  +0x44 ← UNIT_AnimStartFrame(unit) << 8;  (type, class, mode) ← display values
      type 0 (player form):  if mode ∈ {3, 19}: RunVelocityStat (anim/movement A2)
                             if mode ≠ 18: +0x30 ← 0; UNIT_AnimSetRate; +0x48 ← rec.frames << 8
                             else:         UNIT_SeqInit; UNIT_AnimSetRate
      type 1 (monster form): a player shown in mode 13 or 15: RunVelocityStat    ; shapeshifted: 833 rate calls equal (H6d)
                             if mode ≠ 14: UNIT_AnimSetRate; +0x30 ← 0; +0x48 ← rec.frames << 8
                             else:         UNIT_SeqInit; UNIT_AnimSetRate
      type 2 (object, mode < 8 else fatal):
        +0x48 ← Objects.FrameCnt[mode]                            ; already << 8 at load
        +0x44 ← Objects.Start[mode] << 8
        fd: i32 ← (i16) Objects.FrameDelta[mode]
        if Objects.Sync ≠ 0: +0x4C ← fd
        else:
          d: i32 ← 0
          if (fd >> 3) ≥ 1: d ← RNG.RangeB(seed: unit.seed, n: fd >> 3)       ; draw#1
          +0x4C ← clamp(fd − (fd >> 4) + d, 0, 0x7FFF)                       ; >> arithmetic
      type 3 (missile): +0x4C ← Missiles.animrate × 256 ÷ 1024; +0x48 ← (u8 AnimLen) << 8 ; 0 without a row
                        ; ÷ truncates toward zero (0x0062464D–0x00624659): a negative animrate rounds up
      type 4 (item): mode 3: +0x4C ← 0, +0x48 ← 0x1100, +0x44 ← 0x1000;  mode 5: +0x4C ← 0x100, +0x48 ← 0x1100

C3. SUNIT_AnimInit(unit):                                         [C] (fn:SUNIT_AnimInit@0x005533D0, run:2026-10-30-anim-p3b, run:2026-11-16-sweep2-s6e-3, all of C3)
      +0x4E ← 0
      if (monster in mode 14 or player in mode 18) and the used skill has a sequence record:
        UNIT_SeqInit; UNIT_AnimSetRate; return
      +0x30 ← 0;  +0x44 ← 0
      if unit has a path (+0x2C): UNIT_AnimSetRate
      else UNIT_AnimSetRecord(unit, unit.type, unit.class, unit.mode)   ; the unit's own +0, +4, +0x10
      +0x48 ← rec.frames << 8
```

- C1. [C] In `UNIT_SetMode`, a request for the mode the unit is already in runs no `UNIT_AnimInit` (no draw; 42 445
  same-mode sets against 280 292 new-mode starts). A server mode start still resets the frame through C3
  (`+0x44 ← 0`), so a monster restarted in its mode by a new hit starts its animation again (F1; 9 restarts whose first
  advance starts from 0 after `SUNIT_AnimInit`'s rate call only). (fn:UNIT_SetMode@0x00624690,
  fn:SUNIT_AnimInit@0x005533D0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- C2. [C] The branch by display type and mode, at all logged `UNIT_AnimInit` rate calls (0x00624444 674, 0x00624469
  32 626, 0x006244C5 4 486, 0x006244E3 238 566), with `+0x30` set at the sequence calls, clear at the player call and
  still set at 4 460 monster calls (cleared after the rate, as the pseudocode orders it); the object branch at 1 481
  object starts (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); the missile and item branches as an ADR-0015 map (1 500 cases: the
  truncating divide, the row bound, item modes 3 and 5; run:2026-11-16-sweep2-s6e-3). (fn:UNIT_AnimInit@0x00624390)
- C2. [C] **The object start draw.** At 725 logged object animation starts the rate is
  `FrameDelta − (FrameDelta >> 4) + draw` with draw#1 `RangeB(object seed, FrameDelta >> 3)` when `Sync` is 0 (490 starts) and no draw otherwise
  (235), and `+0x44`, `+0x48` as C2. (fn:UNIT_AnimInit@0x00624390, 0x00624563, tbl:Objects.txt:Sync,
  tbl:Objects.txt:FrameDelta0, run:2026-10-27-anim) The draw's place in the object seed's draw order is
  [objects § G](../objects/README.md#g-creation-sunitcreate-for-an-object)'s; no chained pair of two start draws on
  one object was logged (7 pairs, each with another draw between). [I] (run:2026-10-27-anim)
- C2. [C] An object's server frame fields come from the Objects row, never from its `animdata.d2` record: the object
  branch, [0x00624504, 0x0062459D), calls only the Objects row lookup (0x00640E90) and `RNG_RangeB`, neither
  `UNIT_AnimSetRate` nor `UNIT_AnimSetRecord`. The Objects loader shifts the eight `FrameCnt` dwords left by 8, so an
  object's `+0x48` is 8.8 like every other type's (eight `shl … 8`). (fn:UNIT_AnimInit@0x00624390,
  fn:sub_0063F690_ObjectsLoad@0x0063F690, 0x00640E33–0x00640E64, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] So a disagreement between the two
  (`FrameCnt` equals the record's `frames` in 1 173 of 1 483 joined modes) has no server effect.
  ([Objects § Timing](../../tables/Objects.md#timing-plan-0050-phase-0))
- C2. [C] No advance at or above 0x00520000 reaches an object, a missile or an item (its 7 sites there are monster
  mode functions, A2), and the item branch stores constants. ([anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] That no other server code reads the rate back
  for these types: an offset scan of `+0x4C` cannot type the unit. For a missile its own frame is
  [skills/missiles](../skills/missiles.md)'s range countdown. (fn:UNIT_AnimInit@0x00624390)
- C3. [C] **A scheduled mode starts from C3's `+0x44 ← 0`**, written before its rate call whatever C2 set
  (run:2026-11-16-sweep2-s6e-3, 335 path cases); the schedule reads the start frame from `UNIT_AnimStartFrame` itself
  (§ E; 45 913 schedules). C3's second rate call, after C2 has written the new `+0x48`, is the one that sets the rate a
  schedule uses (all 168 starts whose two rates differ). (fn:SUNIT_AnimInit@0x005533D0,
  fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [C] The rate call leaves `+0x44`
  as at its entry (48 118 of 48 118 logged calls), and at `SUNIT_AnimInit`'s 17 005 calls `+0x44` is 0 at entry and
  exit. (fn:UNIT_AnimSetRate@0x00623F50, run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d)) [I] That it is still 0 when the schedule reads it: the
  schedule's entry value is not logged.

### D. The start frame

```
D1. UNIT_AnimStartFrame(unit) → i32:                              [C] (fn:UNIT_AnimStartFrame@0x00623B10, data:g_AttackStartFrames@0x006E8E60, run:2026-10-27-anim, all of D1)
      if display type = 0 and (mode ∈ {7, 8} or (mode ∈ {15, 16} and UNIT_CanDualWield(unit))):   ; the S3/S4 half returns 0: see D1 below
        item ← SkillSrcDamWeapon(unit, 1)
        wc: i32 ← item ? ItemWeaponClassIndex(item) : 0    ; bow 1, 1hs 2, 1ht 3, stf 4, 2hs 5, 2ht 6, xbw 7, ht1 12, else 0
        return g_AttackStartFrames[wc × 7 + class]
      return 0
```

- D1. [C] The return equals `g_AttackStartFrames[wclass][class]` at all 25 149 logged schedules that read it: 1 or 2
  in the Amazon's and the Sorceress's A1 with a weapon, 0 elsewhere.
  (data:g_AttackStartFrames@0x006E8E60, run:2026-10-27-anim)
- D1. [C] The table's non-zero cells are those two classes' only: 1 for hand to hand, 2 for `1hs`, `1ht`, `stf`,
  `2hs` and `2ht`; rows `bow`, `xbw` and `ht1` are 0 for every class (a second read, the 12 non-zero cells exactly;
  [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)). The S3/S4 dual-wield half reads its cell only for classes 4 and 6 (the trace's 0x00623BED), and every
  class-4/6 cell is 0, so that half returns 0 whatever the weapon class (`BAS31SS`, `AIS4HT2` met in the run).
  (data:g_AttackStartFrames@0x006E8E60, data:g_ItemWeaponClassIndex@0x007446A0, run:2026-11-16-sweep2-s6e-3,
  run:2026-10-27-anim) [C] The start frame is added at the schedule's start (E1) and after each wrap of the advance
  (F1; 478 wraps with start frame 1). (fn:UNIT_AnimAdvance@0x00623E00, run:2026-11-16-sweep2-s6e-3)

### E. The schedule

```mermaid
flowchart TD
  s0["T ← Game+0xA8, S ← start frame, r, L"] --> z{"r = 0?"}
  z -->|yes| e0["kind 1 at T + 1"]
  z -->|no| loop{"256·S + k·r < L?"}
  loop -->|"yes: step k at T + k"| scan["scan frames up to (256·S + k·r) >> 8<br/>queue kind 0 per event byte 1–4"]
  scan --> loop
  loop -->|no| end1["kind 1 at T + max(2, N + 1)"]
```

```
E1. SUNIT_ScheduleModeEvents(game, unit):                         [C] (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-27-anim, all of E1)
      T: i32 ← game.frame;  t: i32 ← T;  S: i32 ← UNIT_AnimStartFrame(unit) << 8
      if unit.+0x30 ≠ 0: r ← unit.+0x3C; L ← unit.+0x34            ; a sequence
      else:              r ← (i32)(i16) unit.+0x4C; L ← unit.+0x48
      if r = 0: UnitQueueEvent(kind 1, frame T + 1); return        ; [C] no logged rate is 0; run:2026-11-16-sweep2-s6e, 40 cases
      f: i32 ← S >> 8;  n: i32 ← 0;  acc: i32 ← S + r
      while acc < L:                                               ; signed 32-bit compares
        t ← t + 1
        while f ≤ (acc >> 8) and f < 0x90:                       ; [C] the 0x90 bound, run:2026-11-16-sweep2-s6e
          e ← unit.+0x30 ? SeqFrameEvent(f << 8) : rec.events[f]
          if e ∈ {1, 2, 4}: UnitQueueEvent(kind 0, frame t, a: e, b: n); n ← n + 1
          else if e = 3:    UnitQueueEvent(kind 0, frame t, a: 3, b: 0)
          f ← f + 1
        acc ← acc + r
      if t = T: t ← t + 1                                          ; [C] no step: E2, run:2026-11-16-sweep2-s6e
      UnitQueueEvent(kind 1, frame t + 1)
      unit.+0x44 ← T << 8
```

- E1. [C] All 25 848 logged schedules (players and monsters, sequences among them) queue exactly E1's kind-0 list and
  kind-1 end from the start frame, the rate and the length of the unit's last rate call and record, and the 42 542
  queued events fire at their frames unless cancelled first; no dispatch fires an event the schedulers did not queue
  (42 449 dispatches). (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:sub_00581220_PlayerEventDispatch@0x00581220,
  fn:sub_005A7F80_MonEventDispatch@0x005A7F80, run:2026-10-27-anim)
- E1. [C] **The catalogue's own queue after a cancel** (Phase 2 part 2, logger rev 6): a catalogue skill function's
  `UnitQueueEvent` calls of kind 0 with `a ≠ 0` and of kind 1 are logged at the call and taken as given (ADR-0004), and
  the dispatches after its `UNIT_CancelEvents` call are compared like a schedule's: the 83 dispatches of an event so
  queued fire at the queued frames with the queued arguments (Charge), and all 134 dispatches 0–4 frames after a
  catalogue cancel match a queued event of one source or the other (the schedulers' or the catalogue's); an unqueued
  dispatch there would be a mismatch, and none occurs. (fn:sub_005417D0_UnitQueueEvent@0x005417D0,
  fn:UNIT_CancelEvents@0x00540E60, fn:sub_00581220_PlayerEventDispatch@0x00581220, run:2026-10-27-anim-p2) [I] Part 1's 124 such dispatches (110 kind 0, 14 kind 1),
  whose logs lack the queue, stay an **uncompared catalogue path** (plan 0046); the catalogue's kinds 2 and 12 are
  logged but not compared. (run:2026-10-27-anim)
- E1. [C] Over both parts (81 logs) the closing check holds `sched` 34 647 schedules, `fire` 56 941 and `dispatch`
  56 800 with 0 mismatches. (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-27-anim-p2)
- E2. [C] **The length.** For `L = 256 F` and `F > S` the end fires at `T + n`, `n(r) = max(2, ⌈256 (F − S) / r⌉)`, at
  every logged rate (25 848 lengths). (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-27-anim)
- E2. [C] **The event frames**, derived from E1's loop: with `N = ⌈256 (F − S) / r⌉ − 1` steps, frame `f ≥ S` fires
  at `T + k_f`, `k_f = max(1, ⌈256 (f − S) / r⌉)`, only when `k_f ≤ N`; the first step carries frame `S` and every
  frame up to `(256 S + r) >> 8`; frames after the last step's are never scanned; no frame event shares the end's
  frame. When `r ≥ 256 (F − S)` (no step) no frame event fires at all, not even frame `S`'s, and the end is at `T + 2`.
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, 0x00553A16, 0x00553A0C–0x00553AF1) The closed forms equal the logged kind-0
  list and end at all 45 913 non-sequence schedules (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); the `k_f ≤ N` drop and the
  no-step case, which no logged schedule meets, hold at 1 115 emulated schedules (128 with an event past the last step,
  104 with no step and an event; run:2026-11-16-sweep2-s6e).
- E2. [C] On stock data a player never reaches the no-event case: of the 323 player records with an event none
  reaches `r ≥ 256 (F − S)` at factor 175 (smallest margin 832, `BAGHXBW`; a full-table check, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)).
  (fn:SUNIT_ScheduleModeEvents@0x005539B0) [I] A two-frame monster record would need `r ≥ 512`, which no stock source
  gives. ([plan 0050 log](../../plans/done/0050-animation-frame-timing.md#implementation-log), P1.2 review rulings (f)
  and `lane/a50t` (c))
- E3. [C] **Reschedules (catalogue).** `RescheduleSkip` and `RescheduleAt` cancel kinds 0 and 1 and rebuild the
  list from an elapsed position `p` (frames): steps `256 p + k r < L`, the scan from frame `p − 1`, every code 1–4
  queued with `b = 0`, no `0x90` bound, the end as E1. `RescheduleSkip(n > 0)`: `p = T − (+0x44 >> 8) − n` (Inferno,
  Blade Fury), then `+0x44 = (T − p) << 8`; `RescheduleAt(n)`: `p = n`, `+0x44 = (T − n) << 8` (Charge, Whirlwind,
  Leap Attack). Their logged lists equal this at 819 and 74 reschedules. (fn:sub_00553C70_RescheduleSkip@0x00553C70,
  fn:sub_00553DC0_RescheduleAt@0x00553DC0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] The third, `RescheduleFromPct(pct)`,
  rebuilds the same way with `p = (T − (+0x44 >> 8)) · (100 − pct) / 100` (signed) and `+0x44 = (T − p) << 8`
  (Dragon Talon, Strafe, Fend); no logged reschedule reaches it. The arguments of all three are catalogue values
  (plan 0046). (fn:sub_00553B10_RescheduleFromPct@0x00553B10)
- E4. [C] **Callers.** `SUNIT_ScheduleModeEvents` has six call sites: the player starts for get-hit, block, the two
  skill starts and death, and `MonSetMode` for a scheduled monster mode; each first cancels the unit's kinds 0 and 1
  (a second read, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l); in all 140 936 logged starts the cancels precede the schedule, run:2026-10-30-anim-p3b,
  [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)). The skill starts schedule **before** `SKILLS_StartUsedSkill`, so a start function can still reschedule
  (88 player starts reschedule after it in the frame). (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30,
  fn:sub_0057FDC0_PlrModeStartBlock@0x0057FDC0, fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90,
  fn:sub_00580EC0_PlayerDeath@0x00580EC0, fn:sub_005A7C20_MonSetMode@0x005A7C20, 0x0057FED3)

### F. The per-frame advance (every-frame monsters)

```
F1. UNIT_AnimAdvance(unit):                                       [C] (fn:UNIT_AnimAdvance@0x00623E00, run:2026-10-27-anim, all of F1)
      +0x4E ← 0
      if +0x30 ≠ 0: the sequence advance (G3); return
      f: i32 ← +0x44 >> 8;  if (i16) +0x4C ≥ 0x100: f ← f + 1      ; 16-bit signed compare
      +0x44 ← +0x44 + +0x4C
      while +0x44 ≥ +0x48:
        for f ..< (+0x48 >> 8): take(f)
        +0x44 ← +0x44 − +0x48;  f ← 0;  +0x44 ← +0x44 + (UNIT_AnimStartFrame(unit) << 8)   ; [C] a start frame ≠ 0: run:2026-11-16-sweep2-s6e-3
      for f ... (+0x44 >> 8): take(f)
      ; take(f): if f < 0x90 and rec.events[f] ∈ 1..4: +0x4E ← rec.events[f]     (the last one wins)

F2. UNIT_AnimAtEnd(unit) → bool:                                   [C] (fn:UNIT_AnimAtEnd@0x006217C0, run:2026-11-16-sweep2-s6e)
      sequence: +0x48 < 1;  else: +0x48 ≤ +0x44 + (i32)(i16) +0x4C      ; a 32-bit add; fatal on a null unit
```

- F1. [C] 4 110 consecutive advances of windowed every-frame monsters (knockback among them) give the next `+0x44` and
  event byte (2 924 of them part 1's under the restart rule below). (fn:UNIT_AnimAdvance@0x00623E00,
  run:2026-10-27-anim, run:2026-10-27-anim-p2)
- F1. [C] **A restart is not an advance.** When a new hit restarts a monster's every-frame mode in the same mode (a
  mode start of the unit between two advances; the first cases were knockbacks, mode 13), the next advance starts from
  `+0x44` 0, not from the previous position plus the rate; two advances pair only with no mode start of that unit
  between them (15 restarts over the 81 logs by that rule, a mode start of the unit between two advances; 3 in part
  1's). (fn:UNIT_AnimAdvance@0x00623E00, run:2026-10-27-anim-p2) [C] The 0 is C3's `+0x44 ← 0`, which `MonSetMode`
  reaches whether or not `UNIT_SetMode` saw a new mode (C1, I2): over the 131 logs, 9 restarts by a narrower rule (a
  same-mode set followed by an advance of that unit) run `SUNIT_AnimInit`'s rate call only and advance from `+0x44` 0.
  (fn:SUNIT_AnimInit@0x005533D0, fn:sub_005A7C20_MonSetMode@0x005A7C20, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- F1. [C] Below a rate of `0x100` the frame the unit stood on is scanned again, so one event byte can be taken on two
  consecutive frames; at `0x100` or more each frame is taken once (604 emulated cases below `0x100`).
  (0x00623E58–0x00623E6E, run:2026-11-16-sweep2-s6e-3)
- F1. [I] A wrap on a record whose frame count is at or below the start frame never ends: the loop subtracts `+0x48`
  and adds `S << 8` back (0x00623ED1–0x00623EE8). Whether a stock record reaches it is not checked.
  (fn:UNIT_AnimAdvance@0x00623E00)
- F1. [C] **The advance reads the rate at its call** (an ADR-0015 map: 1 200 emulated pairs, the second call at a new
  rate, 0 mismatches; 1 114 of the 1 120 changed pairs would mismatch at the old rate). (fn:UNIT_AnimAdvance@0x00623E00,
  run:2026-10-27-anim-rates-emu) So an every-frame monster re-computed mid-mode advances at the new rate from its
  next advance on (the slowed monster windows of the run among them). [C] (run:2026-10-27-anim)
- F2. [C] A rate call leaves `+0x48` as at its entry (48 118 of 48 118 logged calls, 25 059 of them with a changed
  record and a non-zero length; J2). (run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d)) [I] The every-frame monster frame functions call F2 after advancing;
  the length `+0x48` stays the start's, so a rate change shortens such a mode only through the frame position (no
  monster call outside `UNIT_AnimInit`'s own changed its record in the logged sessions). (fn:UNIT_AnimAtEnd@0x006217C0)

### G. Sequences

```
G1. Which sequence record:                                        [C] (fn:sub_00663310_UnitSeqRecord@0x00663310, fn:sub_00643D00_SkillSeqIndex@0x00643D00, run:2026-11-16-sweep2-s6f, all of G1)
      player:  idx ← Skills[used].seqnum;  monster: idx ← MonStats.Sk<k>mode ordinal, k the first with Skill<k> = used
               (0 when absent or for skill 199)
      if idx < 1: no sequence
      player:  g_PlrSeqTables[idx] + 12 × column(weapon class)    ; no bound test on idx
               column: COMPOSIT_WeaponClass's index through g_PlrSeqColumns, fatal when unmapped
      monster: the monseq sequence of that ordinal (MonSeqRecord: 0 ≤ idx < count)

G2. UNIT_SeqInit(unit):                                            [C] (fn:UNIT_SeqInit@0x00621260, run:2026-11-16-sweep2-s6f, all of G2)
      +0x30 ← frames;  +0x34 ← length << 8;  +0x38 ← 0;  +0x3C ← 0x100;  +0x48 ← frames << 8
      UNIT_SeqReadFrame(0);  +0xC4 |= 0x4000
      ; the record is looked up three times (0x006633B0, 0x006633D0, 0x006633F0), the second and third after
      ; +0x30 is written, so a player's column then comes from the mode at +0x40, not +0x10

G3. the sequence advance (in UNIT_AnimAdvance, monster mode 14):   [C] (fn:UNIT_AnimAdvance@0x00623E00, fn:UNIT_SeqReadFrame@0x00621210, fn:SEQ_ReadFrame@0x00663410, run:2026-10-27-anim, all of G3)
      prev ← +0x38;  +0xC4 &= ~0x4000
      +0x38 ← +0x38 + +0x3C;  if +0x38 ≥ +0x34: +0x38 ← +0x38 − +0x34
      +0x48 ← +0x48 − +0x3C
      the frame at +0x38 >> 8: +0x40 ← mode;  +0x44 ← frame << 8
      +0x4E ← the last non-zero event of the rows (prev >> 8) + 1 … (+0x38 >> 8)   ; its own row's when +0x38 = prev; 0 after a wrap
      if +0x40 changed: +0xC4 |= 0x4000
      ; the mode ends when +0x48 < 1 (F2)
```

- G1. [C] `MONSEQ_Load` sets a sequence's length and frame count to its row count (it adds 1 to both fields per row,
  0x00659DB6–0x00659DC5). The player tables have 207 non-empty entries, each with length = frames; the 25 stock rows
  with a `charclass` and a `seqnum` stay within the 24 entries (`seqnum` ≤ 23). (fn:MONSEQ_Load@0x00659C60,
  data:g_PlrSeqTables@0x007483B8, tbl:Skills.txt:seqnum, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] A sequence frame is 6 bytes (mode, frame,
  direction, event, after a u16 sequence id). (fn:MONSEQ_Load@0x00659C60)
- G1. [I] For a non-player unit `SkillSeqIndex` reads the MonStats record with no null test (0x00643D2A–0x00643D31), so
  a class out of range faults; and when `COMPOSIT_WeaponClass` leaves its index unwritten (B1: a right hand that is
  not an item unit) the column lookup searches with an uninitialised local. Neither is reached on stock data.
  (fn:sub_00643D00_SkillSeqIndex@0x00643D00, fn:sub_006632C0_PlrSeqColumn@0x006632C0)
- G2. [C] The three lookups can disagree: in 9 of 223 emulated starts the length or the count came from another record
  than the frames. (fn:UNIT_SeqInit@0x00621260, run:2026-11-16-sweep2-s6f) The logged monster starts show `+0x38` 0
  and `+0x34 = +0x48 = rows << 8` at their first advance (301 starts; run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)).
- G3. [C] 1 453 logged monster sequence advances (mode 14, the `monseq` rows of the used skill) give the next position,
  length, frame, event byte and mode. (fn:SEQ_ReadFrame@0x00663410, run:2026-10-27-anim)
- G3. [C] The only stores of 0 to `+0x4E` besides the advance are do 87's (0x005CB48E), do 89's (0x005CB989) and do
  103's (0x005CD51E) (an exhaustive scan with a second tool, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)). (fn:sub_005CB3C0_SkillDo87MaggotLay@0x005CB3C0)
  [I] In two advances the byte was 0 where the rows give 1: read as the do of that event clearing it, a catalogue
  write after the advance (plan 0046), not the advance's result. (run:2026-10-27-anim)
- G4. [C] **The event of a sequence is the sequence row's**, never the `animdata.d2` byte of the row's frame, in the
  advance: with `+0x30` set, `UNIT_AnimAdvance` took every output from the sequence rows while `+0x50` pointed at
  undeclared memory and no read of it was traced (1 500 cases, 647 with an event). (fn:UNIT_AnimAdvance@0x00623E00,
  fn:UNIT_SeqReadFrame@0x00621210, run:2026-11-16-sweep2-s6f) [I] The schedule reads the sequence record too while
  `+0x30` is set (0x00553A48 → 0x006634C0, not run), and a row's `frame` only sets `+0x44`; so `monseq` steps whose frame
  lies past the user's record (249 on stock data) read nothing through the record.
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, 0x00553A48)
- G5. [C] **A player's sequence** (mode 18) is scheduled once from its step `+0x3C` and length `+0x34` (E1) and is not
  advanced on the server; at each of its frame events `PlrModeSkillFrame` writes the running event's index `b` into
  `+0x38 >> 8` when a skill is in use. So for a player `+0x38 >> 8` is the index of the code-1/2/4 event being run (0
  for the first), which is what skills/dispatch's sequence delay gate and do 35's parity read.
  (fn:sub_00580460_PlrModeSkillFrame@0x00580460, 0x00580482–0x00580488, fn:sub_006212C0_UnitSetSeqPos@0x006212C0;
  the writer and its readers `SKILLS_SrvDo` 0x0056FAB4 and do 35 0x005D3659 by a second read, with no server advance of
  a player, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l))

### H. The event queue and the frame order

```mermaid
flowchart LR
  mis["missiles"] --> plr["players"] --> mon["monsters"] --> obj["objects"] --> itm["items"]
  subgraph each["each type"]
    ef["every-frame list<br/>newest first"] --> slot["slot T & 63<br/>oldest first, frame = T only"]
  end
```

- H1. [C] `UnitQueueEvent(game, unit, kind, frame, a, b)` takes kinds below 15, raises a frame at or below the current
  one to the current + 1, and appends the record to slot `frame & 63` of the unit type's list; a frame of −1 puts it
  at the head of the type's every-frame list. (fn:sub_005417D0_UnitQueueEvent@0x005417D0,
  fn:sub_005416B0_EventQueueAt@0x005416B0, fn:sub_005415E0_EventQueueEveryFrame@0x005415E0, struct:Game+0xA8,
  run:2026-10-30-frame-emu-2: family `qat`, 400 cases, the refused kinds, the raise, the slot and the every-frame head)
- H1. [C] A queued kind-0 event with `a ≠ 0` and a kind-1 event fire at the queued frame with the queued `(a, b)`,
  from the schedulers (E1) and from the catalogue's own calls (E1, 83 dispatches). Kinds 2 and 12 are not compared:
  `[I]`. (fn:sub_005417D0_UnitQueueEvent@0x005417D0, fn:sub_00581220_PlayerEventDispatch@0x00581220,
  fn:sub_005A7F80_MonEventDispatch@0x005A7F80, run:2026-10-27-anim, run:2026-10-27-anim-p2)
- H2. [C] Each game frame runs the missile, player, monster, object and item lists in that order, each its
  every-frame list (newest first) and then the current frame's slot (oldest first, only records whose frame equals
  the current one, then freed), so a unit's every-frame event runs before its slot events of that frame (an emulation
  of the runners: families `tick`, the ten walks in order, and `run`, the every-frame list before the slot and the
  slot's due records only); the frame around it, and how far windows test this order, are
  [sim/frame § D and § K](../sim/frame.md#d-the-unit-events-the-control-the-pass-the-runners). (fn:sub_005414D0_GameRunUnitEvents@0x005414D0, 0x005414EE–0x00541589, run:2026-10-30-frame-emu-2)
- H2. [C] **Monsters' every-frame walk before their slot walk, in the game's own runs:** 4 637 logged pairs in the kept corpus and 207 adjacent walks in the counted windows, none inverted; for the other types the emulation above holds the order. ([sim/frame D5 and D7](../sim/frame.md#d-the-unit-events-the-control-the-pass-the-runners), run:2026-11-03-frame-order, run:2026-11-04-frame2, fn:sub_005414D0_GameRunUnitEvents@0x005414D0)
- H2. [C] **The first run of an every-frame event**: in the frame it is queued when queued before its type's
  every-frame list is walked (the runner's phase below 3 for players, below 5 for monsters), else in the next frame
  (9 682 starts; every player start ran next-frame). So the first step of a moving mode and the first knockback
  advance run in the start's frame only when the start comes before the type's list. (fn:SUNIT_ModeEveryFrame@0x00553F00,
  fn:sub_005415E0_EventQueueEveryFrame@0x005415E0, run:2026-10-27-anim)
- H3. [C] **Dispatch, the ends.** A player's kind-1 record runs `PlayerModeEnd` (`g_PlayerEventFuncs[1]`), and each of
  the 10 718 logged player kind-1 dispatches is followed in its frame by the next mode I1 gives; a monster's kind-1
  record runs its mode record's end function (DT → 12 at 4 520, GH, BL and A1–S2 → 1 at 23 483). A monster's kind-0
  record runs the mode record's frame function, called with the game and unit only, and **its return is not used**:
  neither `MonModeFrameEvent` nor `MonEventDispatch` tests it, and both runner sites overwrite `EAX` first.
  (fn:sub_00581220_PlayerEventDispatch@0x00581220, fn:sub_005A7F80_MonEventDispatch@0x005A7F80,
  fn:sub_005A7BA0_MonModeFrameEvent@0x005A7BA0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k), [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l))
- H3. [I] A player's kind-0 record runs the mode's frame function and, on its return of 2, `PlayerModeEnd`.
  `MonEventDispatch` drops every kind but 3, 4, 5, 8 and 12 while a living monster has state 1 (`freeze`); a dropped
  scheduled record is freed, so a frozen monster loses those frame events and its mode end (no frozen dispatch is
  logged). (fn:sub_005811D0_PlayerModeFrameEvent@0x005811D0, fn:sub_005A7F80_MonEventDispatch@0x005A7F80, 0x005410C4)
- H3. [C] With no mode record or no function in it, the monster handlers call `0x005A7B30`: clear the used skill and,
  unless the unit is dead outside DT and DD, start neutral; both handlers and `MonSetMode` (0x005A7DFD) call it (a
  second read, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)). (fn:sub_005A7BE0_MonModeEndEvent@0x005A7BE0, fn:sub_005A7B30_MonModeNullRecord@0x005A7B30)

### I. The mode machines

#### I1. Players

```mermaid
stateDiagram-v2
  NU: NU or TN (neutral)
  ACT: A1 A2 SC TH KK S1-S4 SQ (scheduled)
  GH: GH get-hit (scheduled)
  BL: BL block (scheduled)
  MOV: WL RN TW (every frame)
  KB: KB knockback (every frame)
  DT: DT death (scheduled)
  NU --> ACT: request
  NU --> MOV: request
  ACT --> NU: kind 1 end
  ACT --> ACT: request accepted
  ACT --> GH: hit
  GH --> NU: kind 1 end
  BL --> NU: kind 1 end
  MOV --> NU: path arrival
  MOV --> MOV: run at 0 stamina to walk
  KB --> NU: path arrival
  DT --> DD: kind 1 end
```

| Mode | Start | Events | End → | Tag |
|---|---|---|---|---|
| 1 NU, 5 TN | `PlrModeStartNeutral` (5 in a town room) | none | — | [C] (fn:sub_0057F020_PlrModeStartNeutral@0x0057F020, run:2026-10-30-anim-p3b: 1 in the field 20 201, 5 in a town 131, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k); the start table, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 2 WL, 3 RN, 6 TW, 19 KB | `PlrModeStartMove` | every frame (`PlrModeMoveFrame`) | neutral on arrival | [C] 2, 3 and 19: every start queues an every-frame event and no schedule, and the arrival sets the mode in its frame (fn:sub_0057F090_PlrModeStartMove@0x0057F090, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k), [anim/experiments § S6b](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-part-2-and-batch-s6b-new-tallies-over-the-same-131-logs-lanen66k)); [I] 6, not met |
| 4 GH, 9 BL | `PlrModeStartGetHit`, `PlrModeStartBlock` | scheduled | neutral | [C] (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30, run:2026-10-30-anim-p3b: 756 GH and 1 442 BL starts, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) |
| 7, 8, 10–16, 18 | `PlrModeStartSkillXY` / `…Unit` | scheduled (`PlrModeSkillFrame`) | neutral | [C] modes 7, 10–12, 14–16 and 18 (fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); [I] 8 and 13, not met |
| 0 DT | `PlayerDeath` | scheduled | 17 DD | [C] (fn:sub_00580EC0_PlayerDeath@0x00580EC0, run:2026-10-30-anim-p3b: 41 death starts, 39 ends, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) |

(data:g_PlayerModeStartFuncs@0x006E1740, data:g_PlayerModeFrameFuncs@0x00732C10)

- I1. [C] `PlayerModeEnd` (kind 1, or a frame function's 2): for modes 7, 8, 11 or a used skill whose Skills row (by
  the record's id, `0 ≤ id < count`) has `durability` (`+0x06` bit 2) it calls the hand refresh first (`HandsRefresh`,
  `EDX` the unit); then mode 0 calls `PlayerDeathModeEnd(17)`; mode 19 with no game is fatal, with an item on the
  cursor returns, else calls `PlayerModeAllowed(4, 1, 0)`; every other mode calls `PlrModeStartNeutral` (an ADR-0021
  map to those calls, 1 600 cases; fn:sub_00580310_HandsRefresh@0x00580310, run:2026-11-16-sweep2-s6f). The next mode
  at the logged ends: mode 0 → 17 (39), every other mode → neutral (10 679) (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)).
  (fn:sub_00581020_PlayerModeEnd@0x00581020, tbl:Skills.txt:durability) [I] Past those calls: the refresh's second
  call (0x00580380), and mode 19's get-hit start when `PlayerModeAllowed` passes.
  (fn:sub_00581020_PlayerModeEnd@0x00581020)
- I1. [C] `PlrModeStartMove`: a walk sets 2 in the field (1 930) and a run keeps 3 in a town (981); a run with
  stamina 0 becomes a walk ([anim/movement § D](movement.md#d-the-run-drain): 75 turns in the drain's frame). Every
  move start queues an every-frame event and no schedule, and on arrival `PlrModeMoveFrame` sets the mode in the
  step's frame. (fn:sub_0057F090_PlrModeStartMove@0x0057F090, fn:sub_00580C20_PlrModeMoveFrame@0x00580C20,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k), [anim/experiments § S6b](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-part-2-and-batch-s6b-new-tallies-over-the-same-131-logs-lanen66k)) [I] A walk and a town walk become 6 in a town (no 6 met); knockback sets path
  type 8; a refused path gives neutral; otherwise `SUNIT_SetMode`, cancel, `SUNIT_ModeEveryFrame`. `PlrModeMoveFrame`
  steps ([anim/movement § C](movement.md#c-who-steps)), drains a run ([anim/movement § D](movement.md#d-the-run-drain)),
  and on arrival sets neutral (or runs the queued interact or skill) and returns 2; so `PlayerModeEnd` sees mode 1 or
  5 and its knockback branch is not reached from this path, and no kind-1 event is queued for mode 19.
  (fn:sub_0057F090_PlrModeStartMove@0x0057F090, fn:sub_00580C20_PlrModeMoveFrame@0x00580C20)
- I1. [C] `PlrModeStartGetHit` and `PlrModeStartBlock`: `SUNIT_SetMode(4 or 9)`, `SUNIT_AnimInit`, clear the used
  skill, cancel, schedule; `PlrModeStartSkillXY`: path target, `SUNIT_SetMode`, `SUNIT_AnimInit`, cancel, schedule,
  clear `+0xC4` bit 6, `SKILLS_StartUsedSkill`. (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30,
  fn:sub_0057FDC0_PlrModeStartBlock@0x0057FDC0, fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90; the rate, cancel and
  schedule order in every logged start, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k); the rest by a second read, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l))

#### I2. Monsters

```mermaid
stateDiagram-v2
  NU: NU neutral (no event)
  WR: WL RN (every frame)
  ATK: A1 A2 SC S1 S2 SQ BL GH (scheduled unless *mv)
  KB: KB knockback (every frame)
  DT: DT death (scheduled)
  NU --> WR: AI command
  NU --> ATK: AI command
  WR --> NU: arrival, UNIT_SetMode 1
  ATK --> NU: generic end, neutral command
  KB --> GH_cmd: MonKnockbackEnd
  GH_cmd --> ATK
  DT --> DD: end
```

| Row | Mode | Frame function | End | `schedule` | Tag |
|---:|---|---|---|---:|---|
| 0 | DT | not moving: mode 12 at once; moving: step, advance, 12 at the end | mode 12, event 13; `SplEndDeath` | 1 | [C] the record and its call sequences (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)); [I] "moving" as `0x0063E8D0`'s result and the `SplEndDeath` branches |
| 1 | NU | `UNIT_CancelEvents(0, 0)` | — | 0 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 2, 15 | WL, RN | trails, step; arrival → generic end | — | 1 | [C] the step and the generic end on a return of 2 (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)); [I] "trails" as the meaning of WL's state 13 and 22 calls |
| 3, 6 | GH, BL | `UNIT_CancelEvents(0, 0)` (0x005A6DE0), run at a frame event of the record | generic | 1 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 4, 5, 7, 8, 9 | A1, A2, SC, S1, S2 | `MonAttackFrame` | generic | 1 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 10, 11 | S3, S4 | S3: step, advance, at the end mode 11; S4: `UNIT_CancelEvents(0, 0)` (0x005A6DE0) | S3: a bare `ret` (0x005A74D0); S4: — | 0 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 12 | DD | `UNIT_CancelEvents(0, 0)` (0x005A6DE0), never queued | — | 0 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 13 | KB | step, advance; at the end `MonKnockbackEnd` | `MonKnockbackEnd` | 1 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |
| 14 | SQ | `MonSeqFrame` | generic | 1 | [C] (data:g_MonModeRecords@0x006E2260, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) |

(data:g_MonModeRecords@0x006E2260, data:g_MonModeEndDirect@0x0073C6D0)

- I2. [C] `MonSetMode(game, cmd, flag)`: fatal under state 54; for a mode other than 3, the path target, the move plan
  and the attack stats; the record's start (0 → clear the used skill and start neutral); then `+0xC4 |= 0x80000`,
  `SUNIT_AnimInit`, `MonModeVelocity` (0x005A7DBF; [anim/movement § A3](movement.md#a-speeds)),
  `UNIT_SetUsedSkill(unit, 0)` again (0x005A7DDE), cancel kinds 0 and 1, and by the record of the **resulting** mode:
  `schedule` 0 → no event, else every frame (A1) or `SUNIT_ScheduleModeEvents`. (fn:sub_005A7C20_MonSetMode@0x005A7C20,
  0x005A7DE7–0x005A7E2B, fn:sub_005A6B10_MonModeEveryFrame@0x005A6B10; the order by a second read, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l); the rate,
  cancels and event by the resulting mode with 0 mismatches, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- I2. [C] **Class overrides.** When MonStats `+0x1A5` (`SplGetModeChart`) is non-zero (0x005A78EF), a class switch
  gives: 243, 333 and 705 attack records for S3 (row 17) and S4 (row 16); 403 rows 18 (A1, A2) and 19 (S1, S2); 417
  and 418 row 20 for S4; 543, 544, 570 and 709 row 7 for S3. All ten have `SplGetModeChart` set; ten more stock rows
  set it with no case of the switch (404, 546–550, 559, 571–573), so they keep the plain records.
  (fn:sub_005A78A0_MonModeRecord@0x005A78A0, 0x005A7923–0x005A7990, tbl:MonStats.txt:SplGetModeChart; the jump tables
  and a full-table check, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] Rows 18 and 19 each end in a mode-8 command. (fn:sub_005A78A0_MonModeRecord@0x005A78A0)
- I2. [C] **`MonAttackFrame`, no used skill, scheduled.** A code-1 kind-0 event of a no-skill A1 or A2 is followed in
  its frame by a hit of the attacker in 18 160 of 18 637 dispatches; a code-2 event by none, in 2 248 of 2 248
  dispatches. (fn:sub_005A7670_MonAttackFrame@0x005A7670,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] A code-1 event strikes through `MON_MeleeHit` and
  `COMBAT_DeliverQueued` (the code reading). The reading that every code 1–4 strikes is contradicted for code 2;
  codes 3 and 4 keep it, untested. Which test drops code 2, and so whether a code-2 event reaches the strike's
  to-hit test and its draw at all, is not read: the frame function gets no code (`MonModeFrameEvent` passes only `ECX`
  and `EDX`, 0x005A7BD2–0x005A7BD6), so the drop lies below `MON_MeleeHit` or in its gates.
  (fn:sub_005A7BA0_MonModeFrameEvent@0x005A7BA0)
- I2. [I] An every-frame mode steps, advances and strikes only on a frame whose event byte is 1 (mode 14: bit 6 set).
  With a used skill it runs `SKILLS_DoUsedSkill` on every call, then advances. (fn:sub_005A7670_MonAttackFrame@0x005A7670,
  0x005A76DF–0x005A7741)
- I2. [C] **`MonModeEndGeneric`** (GH, BL, A1–S2, SQ; WL and RN on arrival): the kind-1 ends of GH, BL and A1–S2
  give the neutral command (23 483), and WL and RN arrivals go to `UNIT_SetMode(1)` directly (0x005A8281, 85 507).
  (fn:sub_005A8030_MonModeEndGeneric@0x005A8030, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] A `SplEndGeneric` base class in
  its listed mode gets only the AI event (unless frozen and alive); otherwise, when `g_MonModeEndDirect[mode]` is 0
  (all but WL and RN), the delayed hit of state 54 and the used skill's clear come before the neutral command; WL and
  RN get the AI event after their mode set. (fn:sub_005A8030_MonModeEndGeneric@0x005A8030, tbl:MonStats.txt:SplEndGeneric)
- I2. [C] **`MonKnockbackEnd`** runs in the frame the knockback's advance reaches the length (541 ends, 3 585
  knockback frames, none ending earlier). (fn:sub_005A8520_MonKnockbackEnd@0x005A8520, fn:UNIT_AnimAtEnd@0x006217C0,
  run:2026-10-27-anim) [C] Each of the 726 logged knockback ends of run:2026-10-30-anim-p3b is followed by the get-hit
  command (mode 3). ([anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] Its other branches: path stop; when `MonModeAllowed(3)` refuses, the AI event at
  `T + 1`; base class 78 the AI event at `T + 15` (`T + 45` stunned); and before the command, clear the used skill and
  `Unit+0xB0 = 0xA0`. (fn:sub_005A8520_MonKnockbackEnd@0x005A8520, struct:Unit+0xB0)
- I2. [I] `MonModeStartNeutral`: `SUNIT_SetMode(1)`; when the next AI event is not later than now, re-queue it at `T +
  45` under state 21 (`stunned`), else at `T +` MonStats `aidel` (by difficulty; 15 when 0). The AI's delay itself is
  phase (5)'s. (fn:sub_005A73E0_MonModeStartNeutral@0x005A73E0, tbl:MonStats.txt:aidel)

#### I3. Objects

```mermaid
stateDiagram-v2
  M0: mode 0
  M1: mode 1 operating
  M2: mode 2 opened
  M0 --> M1: operate, UNIT_SetMode, start draw if Sync is 0
  M1 --> M2: event 1 at FrameCnt1 + 1, no UNIT_SetMode
```

- I3. [I] After a chest's drops `OBJOP_Chest` sets mode 1 (when `Mode1` is set) and queues object event 1 at `frame +
  (FrameCnt1 >> 8) + 1`; event 1 sets `Unit+0x10 = 2` when the object is still in mode 1 and the row has `Mode2`,
  **without** `UNIT_SetMode` (no animation start, so no start draw), and unmarks the footprint when
  `HasCollision2` is 0. The same queue form appears at 46 sites, two of them read. (fn:OBJOP_Chest@0x00585F60,
  fn:sub_00581490_ObjEvOperateEnd@0x00581490, 0x0058639A–0x005863B7, tbl:Objects.txt:FrameCnt1, tbl:Objects.txt:Mode2)
  [C] None of the 161 logged object event-1 dispatches is followed by a mode set or an animation start of that object.
  (fn:sub_00581490_ObjEvOperateEnd@0x00581490, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))

### J. The rate (`UNIT_AnimSetRate`)

```mermaid
flowchart TD
  a["display type, class, mode<br/>set the record"] --> c{"cast?<br/>SC, or SQ with seqtrans SC"}
  c -->|yes| rc["spd · min(100 + B_FCR, 175) / 100"]
  c -->|no| b{"block?"}
  b -->|yes| rb["max(1, spd · (B_FBR + 50 or 100) / 100)"]
  b -->|no| g{"get-hit?"}
  g -->|yes| rg["spd · (B_FHR + 50) / 100"]
  g -->|no| k{"knockback?"}
  k -->|yes| rk["vbase, path speed 0x1000"]
  k -->|no| m{"moving?"}
  m -->|yes| rm["vbase · max(B_FRW + stat 67, 25) / 100<br/>and the path speed"]
  m -->|no| at{"attack?"}
  at -->|yes| ra["base · clamp(B_IAS + 68 + terms, 15, 175) / 100"]
  at -->|no| fx{"fixed?<br/>DT, DD"}
  fx -->|yes| rf["spd"]
  fx -->|no| rd["spd · clamp(stat 69, 15, 175) / 100"]
```

```
J1. AnimRateBonus(unit, i) → i32:                                  [C] (fn:sub_00621740_AnimRateBonus@0x00621740, data:g_AnimRateBonus@0x006E8E24, run:2026-10-27-anim-rates-emu, all of J1)
      (k, stat) ← (120, 93) | (120, 99) | (120, 105) | (120, 102) | (150, 96)     ; i = 0..4: IAS, FHR, FCR, FBR, FRW
      s: i32 ← UnitGetStat(unit, stat, 0)
      return s = 0 ? 0 : (k × s) ÷ (k + s)                        ; signed imul, idiv toward zero

J2. UNIT_AnimSetRate(unit):                                        [C] (fn:UNIT_AnimSetRate@0x00623F50, run:2026-10-27-anim, run:2026-11-16-sweep2-H6d, all of J2 but the lines marked)
      if unit is null or unit.type ≥ 4: return
      (type, class, mode) ← display values;  UNIT_AnimSetRecord(unit, type, class, mode);  spd: u32 ← rec.speed
      if IsCast(type, mode):              X ← min(100 + B_FCR, 175);  q ← (spd × X) mod 2³² ÷ 100 (unsigned)
      else if (type, mode) ∈ {(0, 9), (1, 6)}:
                                          X ← B_FBR + (HasState(unit, 101) ? 100 : 50);  q ← max(1, (spd × X) mod 2³² ÷ 100)   ; [I] the 1: no case
      else if (type, mode) ∈ {(0, 4), (1, 3)}:
                                          X ← B_FHR + 50;  q ← (spd × X) mod 2³² ÷ 100
      else if (type, mode) ∈ {(0, 19), (1, 13)}:
                                          q ← vbase(type, class, mode);  PathSetSpeed(path, 0x1000)
      else if IsMove(type, mode, class):
                                          if no path: return                                ; +0x4C kept; [I] no case
                                          X ← max(B_FRW + stat67, 25)                         ; the floor 25: monster calls only
                                          q ← (vbase × X) ÷ 100 (signed);  PathSetSpeed(path, (pbase × X) ÷ 100)   ; anim/movement A1
      else if IsAttack(type, mode, class):
                                          WeaponListsRelink2(unit, 1)
                                          X ← B_IAS + stat68
                                          if UNIT_CanDualWield(unit) and both hands hold a usable weapon (type 45):
                                            X ← X + (stat68(R) + stat68(L)) ÷ 2 − stat68(R)       ; R body location 4, L 5
                                          if unit.type = 0 and unit.mode = 18: X ← X − 30        ; the real type and mode
                                          X ← clamp(X, 15, 175)                               ; the floor 15 met at X 10; [I] X 11–14
                                          base ← (HasStateFlag(unit, 38) and w ← WereformAttackBase(unit), w ≠ 0) ? w : spd
                                          q ← (base × X) mod 2³² ÷ 100 (unsigned)
      else if IsFixed(type, mode, class): q ← spd
      else:                               q ← (spd × clamp(stat69, 15, 175)) ÷ 100 (unsigned)
      q ← q ≤ 0 ? 0 : min(q, 0x7FFF);  +0x4C ← (i16) q             ; signed test, then the cap; [I] neither reached
      if cast or attack: +0x3C ← (i32)(i16) q                     ; the sequence step
```

- J1. [C] The bonus map holds over 3 413 emulated cases (`s` from −119 to 65 535 and random values); that `s` is the
  unit's full stat is the reading of `UnitGetStat(unit, stat, 0)`, `[I]`. For `s ≥ 0` the bonus rises from 0 toward
  `k` and never reaches it. (fn:sub_00621740_AnimRateBonus@0x00621740, run:2026-10-27-anim-rates-emu)
- J1. [C] For `−k < s < 0` the bonus is negative and unbounded below (the signed divide: 832 negative emulated calls
  equal, where an unsigned divide changes 798 and a floor divide 562). No stock property block makes a rate-bonus stat
  negative (353 blocks write the five stats, all with `min`/`max` ≥ 3; a full-table check, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)).
  (0x00621769–0x00621777, run:2026-10-27-anim-rates-emu, run:2026-11-16-sweep2-s6e-3,
  [ItemStatCost § Timing](../../tables/ItemStatCost.md#timing-plan-0050-phase-0)) [I] `s = −k` divides by zero; and
  since other negative sources (slows, curses) are not scanned, that the negative cases and the wraps below are not
  reached on stock data is not shown. (fn:sub_00621740_AnimRateBonus@0x00621740)
- J2. [C] **Every branch** holds at all 298 373 logged exits, `+0x4C` and (cast and attack) the 39 901 sequence steps
  `+0x3C`: cast (players 4 672, monsters 33), block (1 150, 233; Holy Shield's 100 in the Paladin's rates), get-hit
  (173, 3 526), knockback (2, 1 331), moving (3 191, 123 060), attack (7 532, 27 664), fixed (72, 7 698), default
  (9 129, 108 907). The attack clamp's 175 is reached by 31 player and 74 monster calls (Burst of Speed with two fast
  katars, Double Swing). (fn:UNIT_AnimSetRate@0x00623F50, run:2026-10-27-anim)
- J2. [C] **The floors met.** Under a Holy Freeze slow (session `sp-pal-slow`) the moving floor 25 is reached by 105
  monster calls (`X` −15, −9, 5 and 8) and the attack floor 15 by 111 monster calls, all at `X` 10; the default
  branch's floor 15 by 139 monster and 14 player calls (stat 69 at −4 and 0). Each rate equals the model, and the
  controls (a floor of 24 or 26, 14 or 16, or none) differ in all of them. No player reaches the moving or the attack
  floor (least logged `X` 150 and 80). (0x00624128–0x006241D4, run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d))
- J2. [I] The attack floor's threshold for `X` 11–14 (one input value met), the default branch's 175, block's floor 1
  and the `0x7FFF` cap are reached by no logged call (48 118 rate calls in H6d), nor is a moving call with no path.
  Cast, get-hit, block, attack and default divide unsigned, so a negative factor would wrap to the cap (FCR ≤ −55,
  FHR or FBR ≤ −36, FBR ≤ −55 under Holy Shield); moving divides signed. (0x00623FF6–0x00624016, 0x00624369–0x00624381,
  0x00623FE9–0x00624007)
- J2. [C] **The record is set again at every call**, so a mid-mode call can change `+0x50`: the record changes at
  logged mid-mode calls (players 52 from `ITEMS_AttachToOwner` and 54 from `SKILLS_ApplyAuraStats`, monsters 1 390),
  its frame count with it at 1 355. (0x00623FAF, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [C] It never changes `+0x48`, which
  only the mode starts write: kept in 25 059 of 25 059 logged record-changing calls with a non-zero length, 72 of them
  outside `UNIT_AnimInit`'s own calls, all players. (run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d)) [I] The monster half: no monster call outside
  `UNIT_AnimInit`'s own changed its record in those sessions. Objects and missiles never reach J2 (their start
  branches do not call it). (fn:sub_006214A0_AnimRateIsMove@0x006214A0)
- J3. [C] **Which branch a mode takes** is the mode-class tables (players; monsters below class 410; from 410): player
  A1, A2, TH, KK attack; SC cast (SQ too when its `seqtrans` is SC); BL block; GH get-hit; KB knockback; WL, RN, TW
  moving; DT, DD fixed; S1–S4 and SQ moving with a move-first skill, attack with `UseAttackRate`, else default; NU, TN
  default. Monster A1, A2 attack; SC cast; BL block; GH get-hit; KB knockback; WL, RN moving; DT, DD fixed; S1–S4
  **always moving below class 410** and like the player's from 410; SQ (14) like S1–S4 by the used skill in both
  tables; an `npc` row is moving only in WL and RN. Below 410, S1–S4 carry the skill flags as well, but the move flag
  is tested first. `AnimRateIsMove` and `AnimRateIsAttack` are fatal for a unit type other than 0 and 1 (0x006214C5,
  0x00621598), and `AnimRateIsAttack`'s skill branch returns the masked byte (8); `AnimRateIsFixed`, `AnimRateIsCast`
  and the mode tests 0x00621680 and 0x006216B0 return 0 for those types. (An ADR-0015 map of the four predicates and
  the two mode tests over types 0–5, every mode and both class ranges, 2 019 cases.)
  (fn:sub_006216E0_AnimRateIsCast@0x006216E0, fn:sub_006214A0_AnimRateIsMove@0x006214A0,
  fn:sub_00621580_AnimRateIsAttack@0x00621580, fn:sub_00621630_AnimRateIsFixed@0x00621630,
  data:g_PlrModeRateClass@0x006E8A00, run:2026-11-16-sweep2-s6e) [I] The table column names of the bytes read:
  MonStats `+0x0D` bit 0 as `npc`, Skills `+0x06` bit 3 as `UseAttackRate`, `+0x12` as `seqtrans`.
  (tbl:Skills.txt:UseAttackRate, tbl:MonStats.txt:npc)
- J3. [C] The `npc` rule (classes 257 and 405 in S1–S4 take the default branch, 70 calls) and a classic monster's
  S1–S4 at the moving rate (1 818 calls over classes 6, 19, 20, 111, 180 and 190, 19 under a changed stat 67) are met.
  (run:2026-10-27-anim)
- J4. [C] **The dual-wield term** `(R + L) ÷ 2 − R` (toward zero) replaces the right hand's stat 68 by the two hands'
  mean, over the dual-wield calls of Double Swing, Frenzy, A1 and S3/S4; **the sequence term**
  `− 30` applies to a player whose real mode is 18 with an attack-rate skill (Jab, Double Swing, Frenzy, Fists of
  Fire); Charge and Leap Attack take the default branch (no `UseAttackRate`). 186 dual-wield attack calls equal the
  term (152 with the hands' stat 68 differing; the control without it differs in 141 of the 152). The right hand's
  stat 68 is the one replaced also when the left weapon is the linked one (the term subtracts the right hand's whichever
  is linked), read from the code: `[I]` (which hand the skill links is not logged). (0x00624211–0x0062428E,
  0x00624290–0x0062429B, run:2026-10-27-anim, run:2026-11-16-sweep2-H6d)
- J4. [C] **The shapeshift base.** Under state flag 38 (`meleeonly`) a transformed player's attack base is `w = (+0x48 &
  ~0xFF) ÷ D` (signed), `D` 19 without a weapon, else `HumanAttackFrames(unit, weapon) = (F_h << 8) ÷ ((spd_h · (100 +
  stat93(weapon) + stat68(weapon))) ÷ 100)` from the player's own A1 record with that weapon's class; `+0x48` is the
  previous mode's length at `UNIT_AnimInit`'s calls and the new one at `SUNIT_AnimInit`'s (235 calls; 50 separate the
  two lengths). The previous mode's length is the live `+0x48` its start wrote, not its current record's: at 3 074 init
  attack calls the rate equals the model fed that value, which differs from the previous record's length in 34 (run:2026-11-16-sweep2-H6d). (fn:sub_00646170_WereformAttackBase@0x00646170, fn:sub_0062A710_HumanAttackFrames@0x0062A710,
  tbl:States.txt:meleeonly, run:2026-10-27-anim)
- J4. [I] `HumanAttackFrames` takes speed 45 when the name has no record, and a zero divisor faults.
  (0x0062A7EB–0x0062A822)
- J5. [C] A new monster's stats 67, 68, 69 are 75, 100, 100 (13 693 plain monsters at their start; 2 others start at
  75, 95, 100, unexplained); in stat 67, `champion` and `possessed` monsters start at 95, `fast` ones at the clamp
  below and the two logged `fanatic` units at 175 (75 and the clamp only), and 74 units fit none of these values ([anim/movement § A](movement.md#a-speeds) A3). (fn:sub_00573CB0_MonStatsInit@0x00573CB0,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k), [anim/experiments § S6b](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-part-2-and-batch-s6b-new-tallies-over-the-same-131-logs-lanen66k))
- J5. [I] **Where the terms come from** (to the depth the rate needs): stats 67, 68, 69 are 100 on a new player; a
  weapon's stat 68 is `−speed`; stats 68 and 93 are `damagerelated`, so only the weapon
  the attack uses counts after `WeaponListsRelink2`; `champion` and `possessed` add 20 to stat 67, `fast` and
  `fanatic` `clamp(2048 ÷ Velocity − 128, 10, 100)` ([monsters/stats § G](../monsters/stats.md#g-the-mod-handlers-stat-effects));
  chill sets 67, 68 and 69 to the cold effect; Slows Target's state carries 68 and 69 only; a monster's mode command can
  carry a velocity into stat 67 (anim/movement A3). No difficulty, player-count or game field is read.
  (fn:PLAYER_InitBaseStats@0x005706D0, fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_00623C80_WeaponListsRelink2@0x00623C80,
  fn:COMBAT_ApplyCold@0x0057AF80, fn:sub_005C0310_StatEv19Slow@0x005C0310, tbl:ItemStatCost.txt:damagerelated)
- J6. [C] **Who recomputes it.** 31 call sites (a second tool: raw bytes, r2, objdump and Ghidra agree), 24 at or
  above 0x00520000, none in `ITEMS_DetachFromOwner`. ([anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] Their roles: the mode starts, equip, auras, curses,
  chill on and off, the slows, state ends, the skill stat lists, a monster's mode-command velocity; no stat write hooks
  it (an unequip leaves the rate to the next call), and ItemStatCost `UpdateAnimRate` is tested by the server only in four curse and
  Taunt paths, which gate their own call. (fn:UNIT_AnimSetRate@0x00623F50, fn:ITEMS_DetachFromOwner@0x0055C730,
  fn:sub_005C35C0_CurseApplyCb@0x005C35C0, tbl:ItemStatCost.txt:UpdateAnimRate)
- J7. [C] **A rate change in a scheduled mode** moves no queued event: the events fire at their queued frames whatever
  rate call comes after (`fire`). (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-27-anim) [C] Behind it:
  `UNIT_AnimSetRate`'s 19 direct callees include neither the queue nor the cancel, and their closure (101 functions)
  reaches no queue, cancel or scheduler entry; only E3's reschedules rebuild the list, from the rate at their call.
  (fn:UNIT_AnimSetRate@0x00623F50, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l))

### K. Breakpoints (derived)

The breakpoints are not a table in the game: they follow from E2's length and J2's rate. The statements below are
derived formulas. Their inputs are `[C]`: the length `n(r)` (E2, every logged rate), the rate branches (J2) and the
bonus map (J1). `tools/anim_rates.py bp` checks the closed forms against E1's loop and brute force over every stock
(frames, speed) pair, a check of the algebra. `[C]` The closed forms also equal the game's logged schedules: K1 at all
45 913 non-sequence schedules, K2 at the 39 550 plain-rate ones and K3 at 9 919 cast, get-hit and block ones
(run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)); K3's attack form equals a brute force through J1 and J2 at 1 297 362 targets
(run:2026-11-16-sweep2-s6e-3). (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:UNIT_AnimSetRate@0x00623F50) `[I]` At the
factor floors (15, 25, block's 1) no logged schedule checks them: they stay derived only (the rates at 15 and 25 are
J2's monster calls).

```mermaid
flowchart LR
  s["item stat s"] --> B["B = ⌊k s / (k + s)⌋<br/>(J1)"]
  B --> X["factor X = base + B (+ terms)<br/>clamped (J2)"]
  X --> r["r = ⌊spd · X / 100⌋<br/>(J2)"]
  r --> n["n = max(2, ⌈256 (F − S) / r⌉)<br/>(E2)"]
  n --> N["N = n − 1: the sources' count<br/>(§ L, held request)"]
```

```
K1. Length and event frame at rate r (F frames, start S, F > S):      [C] (derived from E1 and E2, run:2026-10-30-anim-p3b, run:2026-11-16-sweep2-s6e, fn:SUNIT_ScheduleModeEvents@0x005539B0, all of K1)
      n(r) ← max(2, ⌈256 (F − S) / r⌉);  N(r) ← n(r) − 1
      frame f ≥ S fires at T + max(1, ⌈256 (f − S) / r⌉) when that is ≤ N(r)

K2. The least factor for a length ≤ m (r = ⌊spd · X / 100⌋):          [C] (derived, run:2026-10-30-anim-p3b, fn:UNIT_AnimSetRate@0x00623F50, all of K2)
      R_m ← ⌈256 (F − S) / m⌉;  X_m ← ⌈100 · R_m / spd⌉
      the breakpoints of a record are the X_m of every m its factor range [X_lo, X_hi] reaches:
        attack and default 15..175; cast 100..175 (FCR ≥ 0); get-hit and block 50 upward; block under Holy Shield 100 upward

K3. The least item stat for a bonus ≥ y:                               [C] (derived from J1, run:2026-10-30-anim-p3b, run:2026-11-16-sweep2-s6e-3, fn:sub_00621740_AnimRateBonus@0x00621740, all of K3)
      y ← X_m − base       ; base 100 cast, 50 get-hit and block, 100 under Holy Shield
      s_min ← ⌈k · y / (k − y)⌉   for 0 < y < k  (none for y ≥ k: the bonus never reaches k)
      attack: if X_m = 15 (the clamp's floor): no IAS is needed, whatever stat68 and the terms are
              else y ← X_m − stat68 (− the dual and sequence terms), the IAS needed is s_min with k 120
```

- K1. [I] Block's `max(1, …)` and the moving and knockback branches (which do not divide `spd`) are outside K2; a
  sequence's `F` is its row count with `S` 0 (a player sequence is scheduled from its step, G5).
  (fn:UNIT_AnimSetRate@0x00623F50)
- K2. [C] A gain shows only when it lowers `⌈256 (F − S) / r⌉`: between two `X_m` every factor gives the same length,
  and a breakpoint is met at the listed value or above: `X_n ≤ X < X_{n−1}` at all 39 550 plain-rate schedules, 28 922
  of them exactly at `X_n`. (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- K3. [I] Illustrations from stock records (`p50b-bp.txt`, the tool's model, not a run): `SOSCHTH` (14 frames, speed
  256, event at frame 7) at FCR 0, 9, 20, 37, 63, 105, 200 lasts 14, 13, 12, 11, 10, 9, 8 frames (`n`; the last at the
  cap, any FCR ≥ 200 the same); `PAGHHTH` (5 frames) at FHR 0, 7, 15, 27, 48, 86, 200 lasts 10, 9, 8, 7, 6, 5, 4.
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, [anim/0002 § 7](../../findings/anim/0002-rates.md#7-the-breakpoint-function-derived-not-copied))
  [C] In the logs, `SOSC1HS` and `SOSCSTF` (the same 14 frames, speed 256, event at 7) at FCR 0, 20, 40 and 50 last 14,
  12, 11 and 11 frames, and `PAGH1HS` (the same 5 frames, 256) at FHR 0, 24 and 48 lasts 10, 8 and 6; the `HTH` records
  themselves and the other tiers are not logged. (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- K3. [C] The schedule lengths equal `n(r)` at every logged rate (`sched-len` 34 647 over the 81 logs of parts 1 and 2,
  46 722 over the 131 logs of parts 1–3, 0 mismatches): three FCR rates of 30 events for the Sorceress, Necromancer,
  Paladin and Druid; three FBR rates of 30 for the Paladin and Druid; one A1 record per class at three IAS rates of 30;
  get-hits at an FHR rate with 30 starts for the Barbarian (two rates) and the Paladin. (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  run:2026-10-27-anim, run:2026-10-27-anim-p2, run:2026-10-30-anim-p3b)
- K3. [C] **The get-hit FHR tiers of five classes** (FHR 0, 24 and 48 from the same stock rate items in every part,
  single player; part 3 added clvl 99 builds in Act I Nightmare to the starts of parts 1 and 2, whose builds and
  difficulties differ): the get-hit schedule lasts `n(r)` at three FHR rates with 30 starts or more each, counted
  over parts 1–3, for the Amazon (rates 128 / 179 / 215: 32 / 40 / 33 starts), the Necromancer (38 / 32 / 42), the
  Sorceress (50 / 35 / 38), the Assassin (40 / 42 / 52) and the Druid (rates 124 / 173 / 208: 49 / 35 / 32; its 179 is
  the werewolf form's); the closing check over the 131 logs holds `sched-len` 46 722 and `ghr` 13 932 with 0
  mismatches. (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:sub_00621740_AnimRateBonus@0x00621740,
  run:2026-10-30-anim-p3, run:2026-10-30-anim-p3b)
- K3. [I] **Recorded short** (not a mismatch): three FHR rates of 30 for the Barbarian (it has two) and the Paladin
  (it has one), which part 3 did not build; and, survivability-bound at part 2's build and not part 3's target, a third FCR rate
  for the Amazon, Barbarian and Assassin, a second weapon type of the IAS rates, and two FBR rates of 30 for the
  classes the records do not name (part 1 had two for three classes; part 2's record names the Paladin and Druid at
  three). Their breakpoints stand on K1–K3 and the `[C]` inputs only. (run:2026-10-27-anim-p2,
  run:2026-10-30-anim-p3b)

### L. The frame events as gates

- L1. [C] **The kind-0 events of a scheduled player mode fire at the frames E1 gives** (A1, cast, kick, throw,
  sequence, get-hit and block among the 7 092 scheduled player modes). (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  run:2026-10-27-anim) [I] `PlrModeSkillFrame` runs the used skill's do on an event of code 1 or 2 while `Unit+0xC4`
  bit 6 is clear (the start cleared it; most do functions set it), so the do runs at `T + max(1, ⌈256 (f − S) / r⌉)`
  for the first frame `f ≥ S` whose event byte (or sequence event) is 1 or 2 within the scanned steps, and again at a
  later code-1/2 event only if the do left bit 6 clear; codes 3 and 4 do nothing there. A move-first skill runs its
  do on the arrival frame of its step instead ([skills/dispatch § E](../skills/dispatch.md#e-the-do-frame-and-skills_srvdo)).
  (fn:sub_00580460_PlrModeSkillFrame@0x00580460)
- L2. [I] **The attack's delivery** is on the do frame: a player's normal attack is skill 0's do, which runs the hit
  test, the build, the queue and `COMBAT_DeliverQueued` in that call; a monster's plain attack strikes in
  `MonAttackFrame` (I2). A skill's `srvmissile` is created by `SKILLS_SrvDo` after the do function in the same call,
  so on the do frame. (fn:SKILL_AttackDo@0x0056F070, fn:SKILLS_SrvDo@0x0056F7F0, fn:sub_005A7670_MonAttackFrame@0x005A7670)
  [C] 18 168 of 18 347 logged monster A1 and A2 hits fall in a frame of the attacker's kind-0 dispatch; a player's
  melee hit is not separated there from missile hits. (fn:COMBAT_GetHit@0x0057CEE0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- L3. [C] **The skill delay runs from the do.** With Frozen Orb held, 72 of the 73 next casts that start within 3
  frames of the delay state's end start exactly at the `SKILLS_SetDelayState` frame (the do's) plus `d`, one 3 frames
  later; the frames from the mode start to the do are not part of the delay. (fn:SKILLS_SetDelayState@0x0056EF90,
  fn:SKILLS_SrvDo@0x0056F7F0, tbl:Skills.txt:delay, run:2026-10-27-anim)
- L4. [C] **The interval between two actions (P1b-1).** The schedule's last event step is at `T + N` and its end at
  `T + n`, `N = n − 1` (E2). **The server starts the next action in the frame of its request**, whatever that frame:
  of the first action requests after a cast's start, 1 816 of 2 084 are followed by the next scheduled mode in their
  own frame, 23 of them two or more frames before `T + N`; after A1 1 685 of 2 332, after a throw 90 of 149, after a
  kick 368 of 569 likewise (the rest start it from a later request). (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, run:2026-10-27-anim)
- L4. [C] **The stock client's held request** (an observation of the oracle input, not a server rule) comes at `T + N`
  for a held normal action and at `T + n` for held Lightning: the next scheduled mode within 3 frames of the end
  started at `T + N` 448 times and at `T + n` 103 after a cast, 107 and 63 after A1, 36 and 2 after a throw, and after
  held Lightning (mode 18) at `T + n` 68 times, never at `T + N`. So a breakpoint table's frame count `N` is the
  interval a held button gives with this client. (run:2026-10-27-anim)
- L4. [I] The client's own rule for when it sends a held request is not read (ADR-0005: the client is presentation and
  an oracle). (run:2026-10-27-anim) [C] For the other player modes, the first request after `T` and the next start are
  tallied over the 131 logs for get-hit (756), block (1 442), S2 (536), S3 (11) and S4 (21); no A2 or S1 action is
  logged. (fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, run:2026-10-30-anim-p3b, [anim/experiments § S6b](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-part-2-and-batch-s6b-new-tallies-over-the-same-131-logs-lanen66k))
- L5. [C] **Get-hit and block are never left before `T + n`**: over the 131 logs the next mode set after a player's
  get-hit (756) or block (1 442) start comes at its end (746, 1 436) or is a death (10, 5), and `PlrModeLeaveOk`
  refuses 781 requests, all from GH, BL and DT; the reading is its refusal of every request but death and neutral from
  GH and BL (M4). (fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, run:2026-10-27-anim, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))

### M. Hit recovery, the block, the get-hit roll, the mode tests, stun and the hit class

```
M1. COMBAT_GetHit(defender, packet; attacker), the timing part:     [I] (fn:COMBAT_GetHit@0x0057CEE0, 0x0057CEE0–0x0057D3BD, all of M1; the parts logged: M1 below)
      if the defender is in a town room and not (attacker is a monster with MonStats +0x00D bit 2): return
      if result & 1 (hit):
        if not packet.+0x64 and (packet.+0x60 & 0xF0) = 0: packet.+0x60 ← HitClassPick(packet, packet.+0x60)
        defender.+0xB0 ← packet.+0x60
      if HasState(defender, 54): (if result & 2: STATE_Set(92, 1)); return
      player defender, by result bits in this order, each returning:
        0x80 dodged, 0x100 avoided, 0x200 evaded (their skills' modes or events)
        0x8010 blocked: unless 0x4000: if frame − stat95 > stat102 ÷ 8 + 15:
                          block command (mode 9);  then stat95 ← frame
        0x2 killed: mode 0 (unless in DT or DD)
        0x8 knockback: PLAYER_ModeCmdUnit(19, attacker)
        0x4 get-hit: if stunned (state 21's list) or GetHitRoll(def, pkt, pkt.+0x60) = 0:
                       PlayerModeCmd(4, unforced)           ; passes M4's two tests first
      monster defender (not in DT or DD): knockback → get-hit without a KB mode; base class 78 adds 0x8 unless frozen;
        0x2 → UnitKilled;  0x8 → command 13;  0x10 → block mode 6 unless 0x4000, classes 243, 333, 705 or no BL mode;
        0x4 → command 3 if stunned or GetHitRoll = 0

M2. GetHitRoll(def, pkt, hc) → i32 (0 get hit, 1 not):              [C] (fn:sub_0057CB00_GetHitRoll@0x0057CB00, run:2026-10-27-anim, all of M2)
      if HasState(def, 1) or (pkt.poison ≠ 0 and pkt.poison = pkt.total) or pkt.total < 0x100: return 1
      hp: i32 ← UnitGetMaxHp(def)                                  ; 1/256 units, as the total
      D: i32 ← hc ∈ {2, 6, 10, 11} ? 8 : hc ∈ {4, 8} ? 32 : hc = 5 ? 64 : 16   ; hc is the whole +0x60; [C] 32: 4 of 38 calls separate it, run:2026-10-30-anim-p3b; [I] 64 not separated
      if pkt.total < hp ÷ D: return 1
      if pkt.total < hp ÷ (D ÷ 2) and RNG.RangePow2(seed: def.seed, n: 2) = 0: return 1    ; draw#1
      if pkt.total < hp ÷ (D ÷ 4) and RNG.RangePow2(seed: def.seed, n: 4) = 0: return 1    ; draw#2 (or the only one)
      if def is a monster and not MonModeAllowed(def.class, 3): return 1    ; [C] 28 separating calls, run:2026-10-30-anim-p3b
      return 0
```

- M1. [C] **The block gate.** For 867 blocked hits on a player the block command is issued exactly when `frame − stat
  95 > ⌊stat 102 / 8⌋ + 15` (618 open, 249 shut); of the 618 the mode test refused 51. (0x0057D282–0x0057D2D6,
  fn:COMBAT_GetHit@0x0057CEE0, run:2026-10-27-anim) [C] Stat 95 is written only when the test passes, whether or not
  the command is accepted: at the next hit it is the open gate's frame (1 440, 185 of them after a refused command) and
  unchanged after a shut one (18 759). (0x0057D3BD, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] The division by 8 is signed
  toward zero (stat 102 is never negative in the logs); the block result itself is combat's
  ([combat/to-hit](../combat/to-hit.md)). (0x0057D282–0x0057D2D6)
- M1. [C] **What the logs hold of M1**, the commands by result bit over the 131 logs: a player get-hit command iff the roll is 0 or the player is
  stunned (955 of 4 760 rolls; the 2 stunned get-hits roll nothing), a block at an open gate, mode 19 at a knockback; a
  monster's command 3 iff the roll is 0 (3 651 of 4 566), command 13 at a knockback (919); under state 54 (22 hits) no
  command. The town return and the kill branch are not separated. (fn:COMBAT_GetHit@0x0057CEE0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- M1. [C] **A player's knockback (P1b-10).** Of 15 hits on a player with result bit `0x8`, 13 by Blood Raven in Hell
  (MonProp `knock`), 12 set the player to neutral in the hit's own frame and one later; 2 by class 462 started
  mode 19. (fn:COMBAT_GetHit@0x0057CEE0, run:2026-10-27-anim) [I] Why Blood Raven's knockback commands end in neutral at once
  (the planner's point equal to the start, or a refusal in the mode command) is not logged; the length of mode 19 (two
  starts) stays unstaged (Phase 2 parts 2 and 3 name player knockbacks short: part 3's three Hell sessions never met
  Blood Raven, class 267, and logged no new player knockback, run:2026-10-30-anim-p3b); its reading is
  [anim/movement § E](movement.md#e-knockback).
  (fn:sub_0057F090_PlrModeStartMove@0x0057F090)
- M2. [C] All 7 195 logged calls return what M2 gives with 0–2 draws on the defender's seed (none 5 977, one 928, two
  290): early returns 809, below `hp ÷ D` 4 518, the two drawing bands 605 and 613, at `hp ÷ (D ÷ 4)` and above 650; `D`
  16 (5 589 calls) and 8 (774). 102 consecutive pairs on one defender chain (the second's seed before is the first's
  after); 701 have other draws between. (fn:RNG_RangePow2@0x00472210, run:2026-10-27-anim) Over both parts' 81 logs
  the closing check holds `ghr` 9 858 and `block-gate` 2 309 with 0 mismatches. [C] (fn:sub_0057CB00_GetHitRoll@0x0057CB00,
  run:2026-10-27-anim-p2)
- M2. [C] Divisor 32 is met at 38 calls of the 131 logs, 4 of them separating it from 16, all as 32; `GetHitRoll` has
  two callers, 0x0057D0C8 and 0x0057D37A, both in `COMBAT_GetHit` (raw bytes and r2). (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
  [I] Divisor 64 (4 calls) is not shown to separate from 16. `D ÷ 2` and `D ÷ 4` are signed; the get-hit chance per
  band is 3/8, 3/4 and 1 (`RangePow2(n)` is `low & (n − 1)`, [rng](../rng/README.md)). (0x0057CB0B–0x0057CBF5,
  0x0057CBF8, fn:RNG_RangePow2@0x00472210)
- M3. [I] **Hit recovery is the get-hit mode's schedule**: the `GH` record at the get-hit rate `⌊spd · (B_FHR + 50) /
  100⌋` (J2), `n(r) = max(2, ⌈256 F / r⌉)` frames (start frame 0), then neutral (I1); a monster's the same with its
  record. **The block's length** is the block mode's schedule at the block rate. (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30,
  fn:sub_0057FDC0_PlrModeStartBlock@0x0057FDC0, fn:SUNIT_ScheduleModeEvents@0x005539B0) [C] Both rates and both
  schedules hold at every logged call and schedule (E2, J2), 0 mismatches over the 131 logs of parts 1–3; the get-hit's
  at three FHR rates of 30 starts or more for the Amazon, Necromancer, Sorceress, Druid and Assassin (K3). The
  Barbarian's and Paladin's FHR tiers stay short (K3). (run:2026-10-27-anim, run:2026-10-30-anim-p3b)

```
M4. Player mode tests (both mode commands; the second unless forced):
  PlrModeLeaveOk(unit, requested) → bool:                           [I] (fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, all of PlrModeLeaveOk)
      an item on the cursor: only 0 and 17 pass
      requested ∈ {0, 1, 5, 17}: pass
      by the current mode: DT, GH, BL, DD refuse
        A1, A2, SC, TH: pass while PlrModeEndPending, else only a GH or BL request
        KK: pass while PlrModeEndPending;  S1 refuses for class 0, S3 for class 5;  SQ: PlrSeqLeaveOk
        every other mode passes
  PlrModeEndPending(unit) → bool: frame ≤ E + 5, E the least positive frame of the unit's kind-1 events (0 when none)
                                                                    [C] E (fn:sub_0057ED70_PlrModeEndPending@0x0057ED70, run:2026-10-27-anim); [I] the + 5
  PlayerModeAllowed(requested, 1, skill) → bool:                    [I] (fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, 0x0057EF7C, all of PlayerModeAllowed)
      0 under state 54 or in DT or DD;  1 without a used skill
      1 when the request is for the used skill itself and its srvdofunc is 67 or 76
      used skill without interrupt: in neutral a forced neutral command and 1;
                                    else only 7, 8, 10, 11, 13, 18 pass while a mode end is queued
      used skill with interrupt:   under state 42: c ← RNG.Range(seed: unit.seed, n: 100)   ; draw#1
                                                   refuse if c < stat 164 of state 42's list
                                   refuse under state 15
                                   a refusal in neutral is a forced neutral command and 1
```

- M4. [C] 1 027 logged `PlrModeEndPending` values equal the frame of the kind-1 end queued when the request comes.
  (fn:sub_0057ED70_PlrModeEndPending@0x0057ED70, run:2026-10-27-anim) [C] `PlrModeLeaveOk` returned 1 at all 5 633
  first requests after an A1, cast, throw or kick start of run:2026-10-27-anim, and at every request in those modes over
  the 131 logs (1 731); over the 131 logs it refuses 781 requests, all from DT, GH and BL, and passes the requested
  modes 0, 1, 5 and 17. (fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] Its cursor
  test, the A1–TH and KK refusals without a pending end, the S1 and S3 class refusals and SQ's test are not reached.
  One `PlrModeEndPending` value after a catalogue requeue is not compared. (run:2026-10-27-anim)
- M4. [C] 26 696 `PlayerModeAllowed` calls leave the player's seed unchanged; none is under state 42.
  (fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, run:2026-10-27-anim) [I] So the Concentration draw is read from the
  code only: a get-hit, block or knockback during a non-interruptible skill (12 player skills, Kick, Jab, Fend, Zeal,
  Frenzy and Whirlwind among them) never starts, and during an interruptible one under Concentration it starts with
  probability `1 − stat 164 / 100`, one draw per command. (tbl:Skills.txt:interrupt)
- M5. [I] **Stun.** `COMBAT_ApplyStun` sets state 21 until `frame + length` (capped at 250, 13 for a hireling from 12
  up) with a unit event 12 at that frame; a stunned defender's get-hit skips `GetHitRoll` (M1); a monster's next AI
  event after a neutral start comes at `T + 45` under stun (I2); `sandleaper1`'s knockback end waits 45. No state-21
  test is in the two player mode tests. ([combat/delivery § D](../combat/delivery.md#d-stun-cold-freeze-poison-burn),
  fn:COMBAT_ApplyStun@0x0057AAE0, 0x0057AB9A–0x0057ABF9) [C] The 2 logged stunned player get-hits skip `GetHitRoll` and
  the command 4; no stunned monster get-hit, `T + 45`, cap or event 12 is logged. (fn:COMBAT_GetHit@0x0057CEE0,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- M6. [I] **The hit class** is the packet's `+0x60`. Melee delivery fills its low nibble when `+0x64` and `+0x60 & 0xF`
  are 0 from `UnitBaseHitClass(attacker)`: a player's weapon `hit class` (the base record's `+0x13C`), 1 without a
  weapon; a monster's MonStats2 `HitClass`; else 0. A missile's hit sets `+0x60 = Missiles HitClass | (+0x60 & 0xF0)`.
  `COMBAT_GetHit` then ORs an element nibble by `HitClassPick` (cold 0x30, fire 0x20, lightning 0x40, poison 0x50: the
  first with damage above 0 in an order rotated by a global byte counter; else 0x10 for a doubled hit; a class 0
  becomes 13) and copies the whole into `Unit+0xB0`. The server gate found on it is M2's divisor, where any high nibble
  gives 16, so the counter changes no server outcome found. (fn:sub_00623C20_UnitBaseHitClass@0x00623C20,
  fn:sub_0062A180_ItemHitClass@0x0062A180, fn:sub_0057CE30_HitClassPick@0x0057CE30, data:g_HitClassCounter@0x0088CAD0,
  data:g_HitClassElements@0x006E16D8, 0x0057D5EA, 0x005AD863, tbl:Weapons.txt:hitclass, tbl:MonStats2.txt:HitClass,
  tbl:Missiles.txt:HitClass)

### N. Draws and seeds per event kind

```mermaid
sequenceDiagram
  participant O as object seed
  participant D as defender seed
  participant P as player seed
  Note over O: mode start, Sync 0
  O->>O: RangeB(FrameDelta >> 3)
  Note over D: COMBAT_GetHit
  D->>D: RangePow2(2), then RangePow2(4), by band
  Note over P: mode command under state 42
  P->>P: Range(100) against stat 164
```

- N1. [C] Over the 171 functions under the animation machine's 29 roots (three indirect stat-list callbacks
  unfollowed), the only RNG call is the object start draw (C2); the rate (J2), the schedule, the advance and the
  sequences draw nothing: a second, independent walker over the same roots and stops reaches 164 functions with one draw,
  the call to `RNG_RangeB` at 0x00624563, and the first walker's 171 bodies walked again find only `UNIT_AnimInit`'s. (fn:UNIT_AnimInit@0x00624390,
  0x00624563, fn:UNIT_AnimSetRate@0x00623F50, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l))
- N2. [I] On a hit, in delivery order: the durability draws ([items/economy § H](../items/economy.md#h-wear-durability-quantity-charges-replenish)),
  the stat events, the knockback handler, then `COMBAT_GetHit`: `GetHitRoll` (defender seed, 0–2, M2), then the
  command's `PlayerModeAllowed` draw (player seed, 0 or 1, M4). On a player defender these are all the player's own
  seed. The mode functions reach other draws only through other subsystems (skills, combat, death drops, the AI, the
  path plan), plus monster death's class-212 area damage and a quill rat's local seed. (fn:COMBAT_DeliverQueued@0x0057D4F0,
  fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0)
- N3. [C] The `GetHitRoll` draws chain on the defender's seed (M2, 102 chained pairs). (run:2026-10-27-anim) [I] The
  object start draw and the `PlayerModeAllowed` draw have no chained pair in the run; their draw order stays as read.
  (run:2026-10-27-anim)

## Outputs

- [C] Per scheduled mode start: the record `+0x50`, the rate `+0x4C` (and `+0x3C`), the queued kind-0 events
  `(frame, code, index)` and the kind-1 end frame; per every-frame monster frame, `+0x44` and `+0x4E`.
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, fn:UNIT_AnimAdvance@0x00623E00, run:2026-10-27-anim)
- [C] The next mode at each end (§ I; players 10 718, monsters 28 003 logged ends) and the get-hit, block and knockback
  commands of a hit (§ M). (fn:sub_00581020_PlayerModeEnd@0x00581020, fn:COMBAT_GetHit@0x0057CEE0,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [I] An object's start rate and draw (§ C), its draw's place in the object seed's order
  as read. (fn:UNIT_AnimInit@0x00624390)

## Worked example

Derived from the closed forms (K1–K3) over stock records, as `tools/anim_rates.py bp` prints them (`p50b-bp.txt`);
run:2026-10-27-anim's schedules hold `n(r)` at every logged rate (E2), but these particular cases are the tool's.

1. [I] **A Sorceress cast at FCR 20** (`SOSCHTH`: 14 frames, speed 256, event byte 1 at frame 7, `S` 0). J1: `B =
   (120 × 20) ÷ 140 = 17`. J2: `X = min(117, 175) = 117`, `r = (256 × 117) ÷ 100 = 299`. E2: `n = ⌈3584 / 299⌉ = 12`,
   `N = 11`. The do (frame 7) fires at `T + ⌈1792 / 299⌉ = T + 6`. At FCR 9: `B = 1080 ÷ 129 = 8`, `r = 276`, `n = 13`.
   K2 for `m = 12`: `R = ⌈3584 / 12⌉ = 299`, `X = ⌈29900 / 256⌉ = 117`; K3: `y = 17`, `s = ⌈2040 / 103⌉ = 20`. So FCR 20
   is the 12-frame breakpoint. (fn:sub_00621740_AnimRateBonus@0x00621740, [anim/0002 § 7](../../findings/anim/0002-rates.md#7-the-breakpoint-function-derived-not-copied))
   [C] The logs hold these numbers on `SOSC1HS` and `SOSCSTF`, which share `SOSCHTH`'s 14 frames, speed 256 and event
   at frame 7: at FCR 20 the rate is 299, the length 12 and the do at `T + 6` (112 casts); `SOSCHTH` itself is not
   logged. (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
2. [I] **A Paladin get-hit** (`PAGHHTH`: 5 frames, speed 256). FHR 0: `X = 50`, `r = 128`, `n = ⌈1280 / 128⌉ = 10`.
   FHR 7: `B = 840 ÷ 127 = 6`, `X = 56`, `r = 143`, `n = ⌈1280 / 143⌉ = 9`.
   (fn:UNIT_AnimSetRate@0x00623F50) [C] The logs hold FHR 0 on `PAGH1HS` (the same 5 frames, speed 256): rate 128,
   length 10 (28 get-hits); FHR 7 is not logged. (run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
3. [I] **An Amazon's one-handed swing** (`AMA11HS`: 16 frames, start frame 2, event at frame 10) at factor 100: `r =
   256`, `n = ⌈256 · 14 / 256⌉ = 14`, the event (the do) at `T + ⌈256 · 8 / 256⌉ = T + 8`.
   (fn:SUNIT_ScheduleModeEvents@0x005539B0) [C] The logs hold `AMA11HS` at factors 80, 130, 147 and 160: lengths 18,
   11, 10 and 9, the do at `T + 11`, `T + 7`, `T + 6` and `T + 6`; factor 100 is not logged. (run:2026-10-30-anim-p3b,
   [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))

## Reimplementation notes

- [C] **Count the end.** A scheduled mode's end is `n` frames after its start; the community tables count `N = n − 1`
  (the event steps). With the stock client a held normal action restarts at `T + N`, held Lightning at `T + n`; the
  server itself starts the next action in the frame its request arrives (L4: after A1, a cast, a throw and a kick).
  (fn:SUNIT_ScheduleModeEvents@0x005539B0, run:2026-10-27-anim)
- [C] **Two rate calls per server start.** `UNIT_AnimInit` calls the rate before it writes the new `+0x48`, and
  `SUNIT_AnimInit` calls it again after (44 415 logged starts with both, `UNIT_AnimInit`'s first); the schedule uses the
  second call's rate (all 168 starts whose two rates differ). (fn:UNIT_AnimInit@0x00624390, fn:SUNIT_AnimInit@0x005533D0,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k)) [C] The shapeshift base reads `+0x48`, so the first call sees the previous mode's
  live length, the one its start wrote (3 074 init attack calls; in 34 it is not the previous record's length; J4).
  (fn:sub_00646170_WereformAttackBase@0x00646170, run:2026-11-16-sweep2-H6d, [anim/experiments § H6d](../../findings/anim/experiments.md#run2026-11-16-sweep2-h6d))
- [I] **Unsigned divides.** Cast, get-hit, block, attack and default take `(spd × X) mod 2³² ÷ 100` unsigned; only the
  moving branch divides signed. A negative factor gives the fastest rate, not a slow one (unreachable on stock data).
  (fn:UNIT_AnimSetRate@0x00623F50)
- [C] **The record is the display's.** A shapeshifted player takes the form's record, start frame and rate (the logged
  rate calls hold it: attack 235, cast 160, default 231, block 71, move 61), with the mode mapped through
  `g_PlrToMonMode` and the MonStats2 fallback (B3). (fn:UNIT_AnimTransform@0x00645270, run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k),
  run:2026-11-16-sweep2-s6e-2)
- [C] **A monster's frame function result is ignored** (H3: neither `MonModeFrameEvent` nor `MonEventDispatch` tests
  it). (fn:sub_005A7BA0_MonModeFrameEvent@0x005A7BA0, [anim/experiments § S6c](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)) [I] So an every-frame monster attack or skill mode with no
  end call of its own lasts until another command (open questions). (fn:sub_005A7670_MonAttackFrame@0x005A7670)
- [C] **An object's opened mode** is set without an animation start: no start draw at the operate end (161 logged
  event-1 dispatches, none followed by an object start). (fn:sub_00581490_ObjEvOperateEnd@0x00581490,
  run:2026-10-30-anim-p3b, [anim/experiments § S6a](../../findings/anim/experiments.md#addendum-2026-11-15-plan-0066-batch-s6a-new-tallies-over-the-131-kept-logs-lanen66k))
- [I] **A frozen monster loses its scheduled events** (dropped and freed), its mode end among them.
  (fn:sub_005A7F80_MonEventDispatch@0x005A7F80)

## Evidence

- Findings: [anim/0001](../../findings/anim/0001-modes-frames.md) (§§ 1–11 and its two run sections),
  [anim/0002](../../findings/anim/0002-rates.md) (§§ 1–7 and its run section), [anim/0003](../../findings/anim/0003-movement-gates.md)
  (§§ 5–7 and its run section), [anim/leads](../../findings/anim/leads.md) (the verdicts, § 12).
- Runs: [run:2026-10-27-anim](../../findings/anim/experiments.md#run2026-10-27-anim) (55 logs, 0 mismatches),
  [run:2026-10-27-anim-p2](../../findings/anim/experiments.md#run2026-10-27-anim-p2) (part 2: 26 logs, the closing
  check over 81 with 0 mismatches; the catalogue queue, the restart rule),
  [run:2026-10-30-anim-p3](../../findings/anim/experiments.md#run2026-10-30-anim-p3) and
  [run:2026-10-30-anim-p3b](../../findings/anim/experiments.md#run2026-10-30-anim-p3b) (part 3: 33 and 17 kept
  sessions, the closing check over 131 logs with 0 mismatches; the get-hit FHR tiers of five classes),
  [run:2026-10-27-anim-rates-emu](../../findings/anim/experiments.md#run2026-10-27-anim-rates-emu) (the bonus and
  advance maps).
- Plan 0066 raises (Phase 3, `lane/n66v`): the S6a addendum to run:2026-10-30-anim-p3b (new tallies over the 131 kept
  logs), the [S6c static addendum](../../findings/anim/experiments.md#static-addendum-2026-11-15-plan-0066-batch-s6c-second-tools-over-the-code-image-lanen66l)
  (second tools over the code image), the emulations [run:2026-11-16-sweep2-s6e](../../findings/anim/experiments.md#run2026-11-16-sweep2-s6e),
  [run:2026-11-16-sweep2-s6e-2](../../findings/anim/experiments.md#run2026-11-16-sweep2-s6e-2),
  [run:2026-11-16-sweep2-s6e-3](../../findings/anim/experiments.md#run2026-11-16-sweep2-s6e-3) and
  [run:2026-11-16-sweep2-s6f](../../findings/anim/experiments.md#run2026-11-16-sweep2-s6f), and
  [run:2026-10-30-frame-emu-2](../../findings/frame/experiments.md#run2026-10-30-frame-emu-2) (the queue and the list
  runners); the rows and what stays inferred are in [the plan's inventory](../../plans/0066-inventory/anim-timing.md).
- Formats and tables: [formats/animdata](../../formats/animdata.md), [MonSeq](../../tables/MonSeq.md),
  [HitClass](../../tables/HitClass.md), [PlrMode § Timing](../../tables/PlrMode.md#timing-plan-0050-phase-0),
  [MonMode § Timing](../../tables/MonMode.md#timing-plan-0050-phase-0), [ObjMode § Timing](../../tables/ObjMode.md#timing-plan-0050-phase-0),
  [PlrType](../../tables/PlrType.md), [ObjType](../../tables/ObjType.md), and the § Timing sections of CharStats,
  MonStats, MonStats2, Weapons, Skills, States, ItemStatCost and Objects.
- Tools: `tools/anim.py` (the model and `check`), `tools/anim_rates.py` (the rate tables and `bp`), `tools/anim_scan.py`,
  `tools/animdata.py`, `tools/anim_survey.py`. Plan: [0050](../../plans/done/0050-animation-frame-timing.md).
- Upstream: [rng](../rng/README.md), [stats/aggregate](../stats/aggregate.md), [monsters/stats](../monsters/stats.md).
  Downstream: [skills/dispatch](../skills/dispatch.md), [combat](../combat/README.md), [objects](../objects/README.md),
  [anim/movement](movement.md).

## Open questions

- [L] What ends an every-frame monster attack or skill mode (`*mv` set), given the ignored return of its frame
  function, and what ends a generic S3 (`schedule` 0, so nothing runs its frame function); the AI command (phase (5))
  is the likely path.
- [L] Whether `PlayerModeEnd`'s knockback-to-get-hit branch is reached at all.
- [L] `0x0057C980` (called by `SUNIT_SetMode`) is not read; `sub_0064C040`, called by `UNIT_SetMode`, is `UnitMarkUpdated`, [sim/frame § G](../sim/frame.md#g-the-other-per-frame-passes).
- [L] The readers of `Unit+0xB0` on the server; what the 44 unread `FrameCnt1 >> 8` queue sites schedule.
- [L] `SkillEntry+0x0C` bit 12, which turns a move-first skill back to the default rate branch, and item flag `0x4000`,
  which empties a hand for the dual-wield term, are not named.
- [L] `sub_0057ED90_PlrSeqLeaveOk` past its first test.
- [L] **Left short by plan 0050 Phase 2 parts 2 and 3** (run:2026-10-27-anim-p2, survivability-bound at clvl 70 /
  life 400; run:2026-10-30-anim-p3 and run:2026-10-30-anim-p3b, clvl 99 builds; all reviewed): three FHR rates of 30
  for the Barbarian and the Paladin (part 3 built the other five classes, whose tiers K3 states); two FBR rates of 30
  for the classes the records do not name; the Druid's throws, 29 of 30 over parts 1–3 (12, then 17 in part 3's
  `op-dru-th`); the set-2 IAS rates; a third FCR rate for the Amazon, Barbarian and Assassin; P1b-1's restart against
  the request frame for the other classes and action modes (the requests and starts tallied since for get-hit, block
  and S2–S4, L4; no A2 or S1 logged); P1b-2's 30 attacks with the factor above 175 (not played
  in part 3; the clamp stands on part 1's 31 player calls, J2); player knockbacks (none new in part 3: Blood Raven,
  class 267, never seen in three Hell sessions); `VASCHTH` (no stock state transforms a player into the vampire);
  P1b-13 (13 player movement windows under a slow over the 131 logs, not a 30; 327 for monsters), P1b-14 and P1b-15
  (not played in part 3; part 2's record reports no outcome for them; P1b-14's moving floor 25 is since met by monsters, J2). Their statements stay `[I]`; none is waiting
  on a mismatch (0 over 131 logs). The run's turn to a walk at 0 stamina, reached in part 3, is settled in
  [anim/movement § D](movement.md#d-the-run-drain) (D2).

### Community sources: differences of 1.14d

The cross-check of [anim/leads § 12](../../findings/anim/leads.md#12-verdicts-part-2) gave 19 contradictions. Each
is listed so that a reimplementer does not "correct" 1.14d; the 1.14d behaviour is the section named. A row marked
**D2R 2.4+ only** or **1.09 only** has no LoD-era source behind it: the difference may be a version difference, not a
community error.

- [L] src:maxroll-d2r-attack-speed, src:maxroll-d2r-breakpoints (**D2R 2.4+ only**), A1, C1, H1, B1: frames `⌈…⌉ − 1`.
  Held with refinement: their count is `N = n − 1` (K, L4).
- [L] src:basin-wiki-animation (LoD 1.10+), A2: attack frames `⌈256 (F − 1 − S) / r⌉`, the `− 1` inside the ceiling.
  Contradicted: it equals `N` only at `r` 256; 23 A1 restarts of the run separate it (L4).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints, R5: no cap on EIAS. Contradicted: the attack factor is clamped
  15..175 with the skill and weapon terms inside (J2).
- [L] src:maxroll-d2r-attack-speed (**D2R 2.4+ only**), A9: a throw costs 30 off the rate except for the Barbarian.
  Contradicted: the only −30 is a player's real mode 18, any class (J2, J4).
- [L] src:maxroll-d2r-attack-speed (**D2R 2.4+ only**), A10: Charge and Leap Attack ignore WSM inside an attack-rate
  sequence formula. Contradicted: they take the default branch, item IAS does not enter (J4).
- [L] src:maxroll-d2r-attack-speed (**D2R 2.4+ only**), A12, A13: Double Swing at base 120, Frenzy's two swings at
  two factors. Contradicted: one schedule per sequence at base 70 with the dual term (J2, J4).
- [L] src:maxroll-d2r-attack-speed (**D2R 2.4+ only**), A14: the wereform delay from the NU length and a 15-frame
  character. Contradicted: the form's current record and the human A1 record of the weapon's class (J4).
- [L] src:maxroll-d2r-breakpoints (**D2R 2.4+ only**), C2, C4: the Druid's, the Necromancer's, the forms' and the
  vampire's cast bases and action frames. Contradicted: the records give `DZSC*` 15 frames at 208 with the event at
  8, `NESC*` 16, `40SCHTH` 11 at 168 (event 5), `TGSCHTH` 10 at 152 (event 5), `VASCHTH` event 3 (B).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints, H4: the "one-handed swinging" weapon lists. Contradicted: the
  records `DZGH1HS` and `AMBL1HS` go by the weapon class `1hs` held in one hand (B1).
- [L] src:pd-breakpoints, H6: hit recovery above 1/12 of life. Contradicted: `GetHitRoll`'s bands from `hp ÷ D` (M2).
- [L] src:basin-wiki-animation (LoD 1.10+), H10: knockback puts the target into hit recovery. Contradicted for a
  player: its knockback ends in neutral (M1, I1); a monster's ends in a get-hit command (I2).
- [L] src:pd-breakpoints, src:maxroll-d2r-breakpoints, B5: blocks repeat with no cooldown. Contradicted: the block
  gate of `⌊stat 102 / 8⌋ + 15` frames (M1).
- [L] src:pd-breakpoints, D2: the delay runs after the whole cast. Contradicted: it runs from the do (L3).
- [L] src:basin-wiki-animation, src:basin-movement-clarification, src:basin-runwalk-thread (M7 **1.09 only**), M6–M8:
  Slows Target lowers velocity. Contradicted: its state carries stats 68 and 69 only (J5;
  [anim/movement § F](movement.md#f-the-slowing-states)).
- [L] src:basin-runwalk-thread (**1.09 only**), M11, M12: the run factor 65, the floor 15, Charge at 1.5 RB.
  Contradicted: [anim/movement](movement.md) §§ A, F.
