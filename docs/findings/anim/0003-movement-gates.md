# 0003 — Movement and the gates: velocities, the per-frame step, and where the frame clock gates combat and skills

> **Subsystem:** anim/movement, anim/timing
> **Question:** how fast does a walking, running or knocked-back unit move and by how much does its position advance
> per game frame; and where do the mode schedule and the rates of anim/0001 and anim/0002 gate the do function, the
> attack's delivery, missile creation, hit recovery, knockback, stun, the block, the skill delay and an object's
> operate, with the draws on those paths and the hit class?
> **Date:** 2026-10-27   **Plan:** 0050 (Phase 1, batch P1.3)   **Status:** open (Phase 1b part 2 and Phase 2
> follow)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p50d`) and objdump. The image
tables, the call sites and the derived models come from `tools/anim_moves.py`; the decompiles and the objdump ranges
cited are kept. All outputs are under `workspace/logs/anim/` (`p50d-manifest.sha256`, one path base:
`p50d-tables.txt` `e5d88a3c…`, `p50d-calls.txt` `03441655…`, `p50d-model.txt` `72bcae68…`, `p50d-decompile.c`
`371eaeb4…`, `p50d-sites.asm` `e1451e39…`, `p50d-monstatsspeeds.asm` `27b50da0…`, and `p50d-commands.txt` `cdd647fb…` with the command lines and the tool
hashes). Unit fields as in `re/types/game.h`, the path fields as in `re/types/anim.h` `PathMove` (new). Positions are
16.16 subtiles (the high word the subtile, as in [drlg/0005](../drlg/0005-collision.md)); a speed `v` is the path's
`+0x7C`. 8.8 means frames × 256.

## Answer (summary)

*2026-10-27, Phase 2:* the step, the speeds (not the floor), the run drain (not its turn to a walk), the monster knockback end, the get-hit roll, the block gate, `PlrModeEndPending` and the delay's start are raised to `[C]` by run:2026-10-27-anim; see [the run section](#plan-0050-phase-2-run2026-10-27-anim), whose tags are the current ones.

- [I] **The per-frame step.** A moving unit's path advances once per call of `sub_00554CA0_UnitMoveStep` (one per
  game frame from its every-frame mode function, 11 call sites): `sub_006502D0_PathVelocityStep` with `k = 0x400`
  makes the step `(d · ((v · 0x400) >> 6)) >> 12` on each axis (`imul`, `sar`), `d` the direction's component from
  `g_PathDirTable` (norm 4096), so `v / 16` subtiles per frame along a straight axis; the step is clamped to land
  exactly on the next path point when both remaining axis distances are at most its larger component, crossing
  subtiles are tested for collision (up to 10 per step), and `UnitMoveStep` returns 2 on the frame the last point is
  reached or the path stops. A unit's path has no acceleration (`PathSetAccel`'s only server caller is
  `MissileCreate`). (fn:sub_00554CA0_UnitMoveStep@0x00554CA0, fn:sub_00650840_PathStep@0x00650840,
  fn:sub_006502D0_PathVelocityStep@0x006502D0, fn:sub_00650090_PathStepSnap@0x00650090,
  fn:sub_00650660_PathStepMove@0x00650660, data:g_PathDirTable@0x006EB7E0, `p50d-calls.txt`)
- [I] **The speeds.** `UNIT_AnimSetRate`'s moving branch sets `v = (pbase · X) / 100`, `X = max(B_FRW + stat 67, 25)`,
  `pbase` = CharStats `WalkVelocity << 8` for a player and MonStats `Velocity << 8` for a monster in every moving mode
  (walk and run alike). A player's run is the walk base with a mode-scoped stat-67 list `RunVelocity × 100 /
  WalkVelocity − 100` (50 on stock data) added at the run's start and dropped at the next mode change: walk `v` 1 536
  (0.375 subtile per frame on an axis), run 2 304 (0.5625) for every stock class at `X` 100 and 150. A monster's
  stat 67 starts at 75 and its run moves at the walk base unless the AI's mode command carries a velocity, which goes
  into a mode-scoped stat-67 list. Knockback moves at `v = 0x1000`, one subtile per frame on an axis. A class with no walk record gets walk base 256 at load (the fallback
  record's speed), so a `Velocity`-0 trap in S1 animates at 192 with a path speed of 0.
  (fn:sub_00621360_AnimPathBaseSpeed@0x00621360, fn:sub_00620E80_RunVelocityStat@0x00620E80,
  fn:sub_005A6380_MonModeVelocity@0x005A6380, fn:UNIT_AnimSetRate@0x00623F50, tbl:CharStats.txt:WalkVelocity,
  tbl:CharStats.txt:RunVelocity, tbl:MonStats.txt:Velocity, `p50d-model.txt` `WALK`, `RUN`, `STEP`)
- [I] **Run drain.** Each run frame outside town takes `max(1, RunDrain · 2 · (armour speed / 10 + 1) + ⌊that ·
  stat 154 / 100⌋)` from stat 10 (stamina, 1/256 units); at 0 or below the stamina is set to 0 and the run restarts
  as a walk in the same frame. (fn:sub_0057F240_RunStaminaDrain@0x0057F240, fn:sub_00580C20_PlrModeMoveFrame@0x00580C20,
  tbl:CharStats.txt:RunDrain, tbl:Armor.txt:speed)
- [I] **Knockback.** The path type-8 planner puts one point `n = (byte +0x90 >> 1) + 1` subtiles from the unit on the
  major axis away from the attacker: `n` 3 (`+0x90` 5) for players and monsters, 6 for base class 78 (`sandleaper1`).
  A player's knockback ends when the path arrives (3 frames on an axis, 5 on a diagonal, from the model), then
  neutral; a monster's ends on its animation (`UNIT_AnimAtEnd` after each advance at the walk-base rate), then
  `MonKnockbackEnd`'s get-hit command. (fn:sub_0067A000_PathPlanKnockback@0x0067A000,
  fn:sub_0057F090_PlrModeStartMove@0x0057F090, 0x005A7844–0x005A784B, 0x005A8636–0x005A864F, `p50d-model.txt` `KB`)
- [I] **The gates.** The do function, a player's normal attack and its delivery, and a skill's `srvmissile` all run
  on the first scheduled event of code 1 or 2 (frame `T + max(1, ⌈256 (f − S) / r⌉)`, anim/0002 § 7) unless bit 6
  is set; the skill delay starts at that do. Hit recovery is the get-hit mode's schedule; a player under a used skill
  without `interrupt`, or in get-hit or block, refuses a new get-hit; a player's block mode starts only when more than
  `⌊stat 102 / 8⌋ + 15` frames have passed since the last (stat 95). Stun gives get-hit without the roll. An object's
  operating mode 1 lasts `FrameCnt1` frames and becomes 2 without an animation start. (fn:sub_00580460_PlrModeSkillFrame@0x00580460,
  fn:SKILLS_SrvDo@0x0056F7F0, fn:COMBAT_GetHit@0x0057CEE0, fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0,
  fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, fn:sub_00581490_ObjEvOperateEnd@0x00581490, 0x0058639A–0x005863B7)
- [I] **The get-hit draw.** `GetHitRoll(defender, packet, hit class)` draws nothing when the defender is frozen, the
  damage is poison only or below 256 (1 HP), or below `maxHP / D`; else up to two `RangePow2` on the **defender's**
  seed: `RangePow2(2) ≠ 0` when the damage is below `maxHP / (D/2)`, then `RangePow2(4) ≠ 0` when below `maxHP / (D/4)`.
  `D` is 8 for hit class 2, 6, 10, 11, 32 for 4 and 8, 64 for 5 and 16 for every other value, including any with the
  element nibble set. A stunned defender skips the roll. (fn:sub_0057CB00_GetHitRoll@0x0057CB00, 0x0057CB4B,
  `p50d-tables.txt` `GHD`)
- [I] **The hit class** is the packet's `+0x60`: melee delivery fills its low nibble from the attacker when empty (a
  player's weapon `hit class`, 1 without one; a monster's MonStats2 `HitClass`), a missile's from Missiles `HitClass`;
  `COMBAT_GetHit` then ORs an element class (cold 0x30, fire 0x20, lightning 0x40, poison 0x50, the first with damage above
  0 in an order rotated by a global byte counter; else 0x10 for a doubled hit) and copies it into `Unit+0xB0`. The
  server gate found on it is `GetHitRoll`'s divisor. (fn:sub_00623C20_UnitBaseHitClass@0x00623C20,
  fn:sub_0057CE30_HitClassPick@0x0057CE30, 0x0057D5EA, 0x005AD863, data:g_HitClassElements@0x006E16D8,
  tbl:Weapons.txt:hitclass, tbl:MonStats2.txt:HitClass)
- [I] **Draws** on these paths: `GetHitRoll`'s (defender), `PlayerModeAllowed`'s `Range(player seed, 100)` against
  stat 164 under state 42 for an interruptible used skill, the unique-monster stun roll (attacker, combat/0001 § 9),
  the durability draws ([items/economy § H](../../specs/items/economy.md#h-wear-durability-quantity-charges-replenish)).
  The movement step, the speeds, the knockback planner and the object operate end draw nothing; the hit-class counter
  is a global byte, not a seed. (fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, 0x0057EF7C)

## Leads used

No lead was used to locate or read this code, and [anim/leads](leads.md) was read only in its § 1 (sources and
versions) before filing ("leads not read before filing"; plan 0050, `lane/p50c` review ruling (b)).
*2026-10-27 (plan 0050 Phase 1b part 2, `lane/p50v`):* the verdicts on the 29 gate, delay, hit-recovery, block and
movement rows, against this finding, anim/0001, anim/0002 and the P0 table docs; agreement promotes nothing, and a
`contradicted` row is a required Phase 2 case ([backlog](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md);
`(version: …)` marks a row whose only source describes D2R or 1.09). Table comparisons: `tools/anim_leads_check.py
code` (`workspace/logs/anim-leads/p50v-code.txt` `99e7b983…`, `p50v-manifest.sha256`).

- [L] src:maxroll-d2r-breakpoints: C4, the cast action frame `⌈B_act · 256 / r⌉` with per-class bases (Amazon by
  weapon 10–13, Assassin 9, Barbarian 9, Druid 10, werewolf 8, werebear 9, Necromancer 8, vampire 5, Paladin 9,
  Sorceress 7, Act 3 mercenary 7). **contradicted (version: D2R)**
  ([P1b-7](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the do runs at `T + max(1, ⌈256 (f − S) / r⌉)` for the first code-1/2 event frame `f` (§ 5,
  fn:sub_00580460_PlrModeSkillFrame@0x00580460), the same form; the records' `f` agree for the Amazon (bow 10, hand
  to hand 11, `1hs`/`2hs`/`xbw` 12, `1ht`/`stf`/`2ht` 13), Assassin, Barbarian, Necromancer, Paladin, Sorceress and
  `IWSC1HS`, and differ for the Druid (`DZSC*` 8), the werewolf (`40SCHTH` 5), the werebear (`TGSCHTH` 5) and the
  vampire (`VASCHTH` 3) (`CAST` lines).
- [L] src:maxroll-d2r-breakpoints: C6, a cast is interrupted by hit recovery, a stun and a block. **held with
  refinement**
  Detail: from SC a get-hit or block request passes `PlrModeLeaveOk`, and `PlayerModeAllowed` passes it for a skill
  with `interrupt` (§ 6.2, fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0; under Concentration with one draw); the 12 player skills without `interrupt` (among them
  Werewolf and Werebear, anim `SC`) are not interrupted (`INTERRUPT` line); a stun interrupts through the get-hit it
  gives without the roll (§ 6.1, fn:COMBAT_GetHit@0x0057CEE0).
- [L] src:maxroll-d2r-breakpoints, src:basin-wiki-animation: D1, the delay starts at the action frame, so casts repeat
  every action frame plus delay (Immolation Arrow: 25 frames plus the action frame). **held with refinement**
  Detail: `SKILLS_SrvDo` sets state 121 for `delay` frames from the do frame and `SKILLS_CanUse` refuses a delay skill
  while it lasts (§ 5, fn:SKILLS_SetDelayState@0x0056EF90, fn:SKILLS_CanUse@0x00647960); Immolation Arrow's `delay` is
  25; the next start also passes the mode tests of § 6.2.
- [L] src:pd-breakpoints: D2, the delay runs after the whole cast (an 11-frame cast with a 25-frame delay repeats every
  36). **contradicted** ([P1b-12](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the delay starts at the do frame (§ 5, fn:SKILLS_SetDelayState@0x0056EF90), not at the mode end; the frames from the do to the end overlap it.
- [L] src:basin-wiki-animation: D3, every delay is global in LoD. **held**
  Detail: one state (121) per unit, and `SKILLS_CanUse` refuses every skill with a `delay` while it is set (§ 5, fn:SKILLS_CanUse@0x00647960).
- [L] src:basin-wiki-animation: D4, the LoD delays in seconds (23 skills); nothing shortens a delay. **held**
  Detail: Skills `delay` equals 25 × the seconds for all 23, and no other row with a `charclass` has a delay (`DELAY
  rows=23 match=23`); the state's length is the `delay` cell, with no stat term read (§ 5, fn:SKILLS_SetDelayState@0x0056EF90, tbl:Skills.txt:delay).
- [L] src:basin-wiki-animation: D5, a delay skill cast by a chance-to-cast item sets an 11-frame block on active
  skills from the action frame, not the skill's delay. **not covered**
  Detail: the item cast path (skills/0015) is not read for the delay here; `SKILLS_SetDelayState`'s three callers are
  `SKILLS_SrvDo` (two) and `sub_0056F020_SkillDelayFromCalc` (§ 5, fn:SKILLS_SetDelayState@0x0056EF90, fn:sub_0056F020_SkillDelayFromCalc@0x0056F020); where an 11-frame value comes from is not found.
- [L] src:maxroll-d2r-breakpoints: H5, no hit recovery on a kill, when frozen, on poison only or below 1 damage; else
  `T = maxLife / D` with `D` 8 (hit class 2, 6, 10, 11), 32 (4, 8), 64 (5), 16 otherwise; below `T` none, below `2T` a
  1-in-2 then a 3-in-4 roll, below `4T` a 3-in-4 roll, else always; some units immune. **held with refinement**
  Detail: § 6.3 (fn:sub_0057CB00_GetHitRoll@0x0057CB00): the tests, the divisor table and the two `RangePow2` draws on
  the defender's seed agree, with `4T` itself always (the "≥" reading); `2T` and `4T` are `hp / (D/2)` and `hp /
  (D/4)` (signed), a kill is a result bit handled before (§ 6.1); `D` reads the whole `+0x60`, so any element or
  doubled nibble gives 16; a stunned defender skips the roll; a monster without a GH mode is never hit.
- [L] src:pd-breakpoints: H6, hit recovery on any hit above 1/12 of maximum life. **contradicted**
  ([P1b-9](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the threshold is `hp / D` with the bands of H5 (§ 6.3, fn:sub_0057CB00_GetHitRoll@0x0057CB00): at `D` 16 a hit from `hp/16` can get hit (3/8) and
  one at or above `hp/12` but below `hp/4` can fail.
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: H7, hit recovery interrupts a cast, an attack, walking,
  running and standing; nothing can be done until it ends; it can be re-entered at once. **held with refinement**
  Detail: get-hit and block refuse every request but death and neutral (§ 6.2, fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0);
  a get-hit during a used skill without `interrupt` (12 player skills, among them Kick, Jab, Fend, Zeal, Frenzy,
  Whirlwind) never starts (fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0); a new get-hit during get-hit is refused, one
  after its end is not.
- [L] src:basin-wiki-animation: H8, a stunned player is not incapacitated but enters hit recovery on every hit while
  stunned, even with no damage. **held with refinement**
  Detail: a stunned defender's get-hit skips `GetHitRoll`, its damage tests included (§ 6.1, fn:COMBAT_GetHit@0x0057CEE0); the command still meets
  the mode tests of § 6.2, and no state-21 test was found in them (§ 6.4).
- [L] src:basin-wiki-animation: H9, a 10-second ceiling on stun, the latest replacing the running one; champions,
  uniques and superuniques stunned 1 time in 10; bosses and static units never. **held with refinement**
  Detail: `COMBAT_ApplyStun` caps the length at 250 frames (13 for a hireling from 12 up), re-sets state 21's end to
  `frame + length`, rolls `Range(100) ≥ 90` on the attacker's seed for a monster with type flag `0x08`, and returns for
  a boss and for `Velocity` 0 (§ 6.4, fn:COMBAT_ApplyStun@0x0057AAE0; combat/0001 § 9); which special monsters carry
  flag `0x08` is combat's.
- [L] src:basin-wiki-animation: H10, knockback moves the target up to three subtiles (sometimes fewer) and puts it into
  hit recovery; not when frozen or killed; it needs a knockback mode, and the chance depends on the target's size.
  **contradicted** ([P1b-10](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the distance `n` 3 (6 for `sandleaper1`), shortened by collision, and the kill test before agree (§ 4,
  fn:sub_0067A000_PathPlanKnockback@0x0067A000); a monster's ends in a get-hit command (fn:sub_005A8520_MonKnockbackEnd@0x005A8520)
  and needs both GH and KB, but a player's ends in neutral when the path arrives (anim/0001 § 9.1,
  fn:sub_00580C20_PlrModeMoveFrame@0x00580C20), with no hit recovery; the chance is stat event 7's `c` 64 or 32/128 by
  MonStats2 flags (fn:sub_005BF960_StatEv07Knockback@0x005BF960).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: B4, the Assassin's Weapon Block uses the block mode and the
  same FBR values. **held with refinement**
  Detail: a blocked hit enters mode 9 through the same path whatever made the block (§ 6.1, fn:COMBAT_GetHit@0x0057CEE0); the `AIBL*` records,
  `ht1`/`ht2` included, are 3 frames at 256 (`TAB fbr Assassin`).
- [L] src:pd-breakpoints, src:maxroll-d2r-breakpoints: B5, a block only in melee or while walking, not while running;
  nothing during the block; blocks repeat with no cooldown. **contradicted**
  ([P1b-11](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: a player's block mode starts only when `frame − stat 95 > ⌊stat 102 / 8⌋ + 15` (§ 6.1, 0x0057D282–0x0057D2D6),
  so a second block within that window plays no block mode; block refuses every request but death and neutral (§ 6.2);
  whether a running player can block at all is the block test's (combat), not read here.
- [L] src:basin-runwalk-thread, src:basin-wiki-animation: M1, every class has `WalkVelocity` 6 and `RunVelocity` 9.
  **held**
  Detail: all seven CharStats rows (`MOVE charstats`, tbl:CharStats.txt:WalkVelocity, tbl:CharStats.txt:RunVelocity).
- [L] src:basin-wiki-animation, src:basin-runwalk-thread, src:basin-movement-clarification: M2, walk `max(WB (100 +
  Speed)/100, WB/4)`, run `max(RB + WB · Speed/100, WB/4)`. **held with refinement**
  Detail: `v = (pbase · X) / 100`, `pbase = WalkVelocity << 8`, `X = max(B_FRW + stat 67, 25)` (§ 1); the run is the
  walk base with stat 67's mode-scoped `RunVelocity · 100 / WalkVelocity − 100` (+50), so `RB` enters only through
  that list (fn:sub_00620E80_RunVelocityStat@0x00620E80) and the floor 25 is `WB/4` for both; integer, 1/256 units.
- [L] src:basin-runwalk-thread, src:basin-movement-clarification, src:basin-wiki-animation: M3, 6 and 9 subtiles (or
  yards) per second. **held with refinement**
  Detail: a speed `v` moves `v / 16` subtiles per frame on an axis (§ 2, fn:sub_006502D0_PathVelocityStep@0x006502D0): `WB / 16` and `RB / 16`, 0.375 and 0.5625,
  in the ratio 2 : 3; the sources' unit is theirs (read as subtiles per second at 25 frames, the 2003 figure is not
  the code's 9.375).
- [L] src:basin-wiki-animation, src:basin-runwalk-thread: M4, item FR/W `⌊150 x / (150 + x)⌋`; skill bonuses, slows
  and the armour penalty undiminished. **held with refinement**
  Detail: `B_FRW = 150 s / (150 + s)` truncated (anim/0002 § 2); stat 67 enters `X` raw (§ 1), an armour's base 67 is
  `−speed` (items/properties A3, fn:sub_00557AB0_ItemInitStats@0x00557AB0).
- [L] src:basin-wiki-animation, src:basin-runwalk-thread: M5, `Speed` is the sum of EFRW, the skill bonuses, the
  armour and shield speeds, cold −50 for a player, Holy Freeze, Decrepify −50 and Slows Target. **held with
  refinement**
  Detail: the sum is `B_FRW + stat 67` floored at 25 (§ 1); the player's chill is −50 (combat/delivery D2,
  fn:COMBAT_ApplyCold@0x0057AF80); the skills' values and their formula are their stat lists' (not read here); Slows
  Target does not enter (M6).
- [L] src:basin-wiki-animation, src:basin-movement-clarification: M6, Slows Target lowers a player's walk and run by
  its percentage, capped at −50. **contradicted**
  ([P1b-13](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: its state carries stats 68 and 69 (attack and default rate), not 67 (skills/0003 handler 19,
  fn:sub_005C0310_StatEv19Slow@0x005C0310), and movement reads only `B_FRW + stat 67` (§ 1).
- [L] src:basin-runwalk-thread: M7, Slows Target of any percentage gives −100 % to walk and run. **contradicted
  (version: 1.09)** ([P1b-13](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: as M6, no stat 67 in its state (fn:sub_005C0310_StatEv19Slow@0x005C0310).
- [L] src:basin-wiki-animation: M8, Slows Target caps (90 % on normal and minion monsters, 50 % on players, mercenaries
  and special monsters); with cold, Decrepify and Holy Freeze no unit below 15 % attack rate or 25 % velocity; the first
  percentage sets velocity, the latest attack rate. **contradicted**
  ([P1b-13](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the floors agree as clamps on every source (attack factor ≥ 15, anim/0002 § 3.6; moving factor ≥ 25, § 1);
  the caps are 50 (players, bosses, hirelings, a `MonTypeFlag`), 75 or 90 (fn:sub_005C0310_StatEv19Slow@0x005C0310);
  Slows Target sets no velocity at all (M6).
- [L] src:basin-runwalk-thread: M9, the final speed keeps its fraction. **held with refinement**
  Detail: `v` is in 1/256 of the walk unit, truncated by the signed divide by 100 (§ 1, fn:sub_00648690_PathSetSpeed@0x00648690), and the step keeps 1/65536
  subtile (§ 2, fn:sub_006502D0_PathVelocityStep@0x006502D0).
- [L] src:basin-runwalk-thread: M10, `WalkVelocity` 0 never moves; negative values walk backwards (modded data).
  **held with refinement**
  Detail: `pbase` 0 gives `v` 0 and `PathStep` stops a path with no speed (§ 2, fn:sub_00650840_PathStep@0x00650840);
  the negative half needs modded data and is not decided (the field's signedness is not read).
- [L] src:basin-runwalk-thread: M11, `effective rw = skill FRW + EFRW + RunVelocity · 100 / WalkVelocity − 100 −
  armour`, floored at 15; `velocity1 = effective rw · factor / 100`, factor 213 (walk, town walk) or 65 (run);
  `velocity2 = WalkVelocity · 256 · effective rw / 100`. **contradicted (version: 1.09)**
  ([P1b-14](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the sum is `X` and `velocity2` is the path speed (§ 1); `velocity1` is the animation rate `vbase · X / 100`
  with `vbase` 0xD5 = 213 for walk and town walk and 0x65 = 101 for run (anim/0002 § 3.4,
  fn:sub_006213D0_AnimMoveBaseRate@0x006213D0; the row's 65 matches only read as hex); the floor is 25, not 15.
- [L] src:basin-runwalk-thread: M12, Charge at `RB · (1 + bonus + armour) · 150 %`, item FR/W not applied.
  **contradicted (version: 1.09)** ([P1b-15](../../backlog/archive/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: start 31 sets `MulDiv(RunVelocity << 8, max(stat 67, 50) + Param1, 100)`, `Param1` 150 (skills/0011 § 5,
  fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0): `RB · (stat 67 + 150) / 100`, 2.5 RB at stat 67 100, not 1.5 RB.
- [L] src:basin-movement-clarification, src:basin-wiki-animation: M13, Charge at `RB · (1 + bonus + armour) + 1.5 RB`,
  item FR/W not applied, the bonus floored at −50 % at the start; normal run speed when slowed mid-charge; 8–9 frames
  between charges. **held with refinement**
  Detail: the start's speed is that formula with stat 67 (no item FR/W) raised to 50 (fn:sub_005CF6B0_SkillSt31Charge@0x005CF6B0); the speed after a
  slow mid-charge and the interval between charges are not read here.
- [L] src:basin-wiki-animation: M14, the fetish walks and runs at 6, the vampire at 9 (floor 2.25), werewolf and
  werebear at the class's 6 and 9. **held with refinement**
  Detail: the path base takes the display class (`AnimPathBaseSpeed(EAX` display class`, ECX` display type`)`,
  0x00624158–0x006241A9): MonStats `Velocity` 6 (wolf, bear, fetish) or 9 (vampire5); the vampire and fetish rows have
  no RN mode, so a run is shown as WL (anim/0001 § 2's fallback) and takes no run list, while wolf and bear keep RN and
  the +50 (`RunVelocityStat` takes the unit's real class, `mov eax, [esi+0x4]` at 0x0062449F; `MOVE shape` lines; fn:sub_00621360_AnimPathBaseSpeed@0x00621360).

No lead was found for monster walk and run speeds, the `fast` mod, object operate frames, the knockback length in
frames or the run drain (part 1, anim/leads § 1): "no lead; derived from code".

## Functions

New names (subsystems `anim/movement` and `anim/timing`) and the existing ones this finding reads; all new rows are I.

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00554CA0` | `sub_00554CA0_UnitMoveStep` | revalidate the target, `PathStep(unit, 0x400)`, room update; 1 moving, 2 stopped (§ 2) | I (unchanged) |
| `0x00650840` | `sub_00650840_PathStep` | one frame of a path (§ 2) | C |
| `0x006502D0` | `sub_006502D0_PathVelocityStep` | acceleration and the step vector | C (skills/0002; unchanged) |
| `0x006503F0` | `sub_006503F0_PathStepTargetCheck` | still heading for the target? else replan (§ 2) | I |
| `0x00650090` | `sub_00650090_PathStepSnap` | clamp the step onto the next point when within it (§ 2) | C |
| `0x00650660` | `sub_00650660_PathStepMove` | the new position, the collision walk, the point index (§ 2) | C |
| `0x00650150` | `sub_00650150_PathStepCollide` | per crossed subtile the collision test, at most 10 (§ 2; raised at the Phase 2 review: the step over the logged collision results, [run section](#plan-0050-phase-2-run2026-10-27-anim)) | C |
| `0x00650350` | `sub_00650350_PathReplan` | re-plan a blocked monster path (types 2, 13, 15) | I |
| `0x006507B0` | `sub_006507B0_PathStop` | snap to the subtile centre, clear flag 0x20, the points and the step | I |
| `0x0064FE40` | `sub_0064FE40_PathAimNextPoint` | direction to the next point, step `(v · d) >> 8` | I |
| `0x00648DC0` | `sub_00648DC0_PathMoveReset` | speed from `+0x80` under flag 0x8000; type 7 without a unit owner | I |
| `0x00648E40` | `sub_00648E40_PathSetKnockDist` | path byte `+0x90` | I |
| `0x00648780` | `sub_00648780_PathPointCount` | path `+0x28` | I |
| `0x0067A000` | `sub_0067A000_PathPlanKnockback` | planner of path type 8 (§ 4) | I |
| `0x00623C20` | `sub_00623C20_UnitBaseHitClass` | a unit's own hit class (§ 7) | I |
| `0x0062A180` | `sub_0062A180_ItemHitClass` | an item's base record byte `+0x13C` | I |
| `0x0057EDD0` | `sub_0057EDD0_PlrModeLeaveOk` | may the player leave its mode for the requested one (§ 6.2) | I |
| `0x0057ED70` | `sub_0057ED70_PlrModeEndPending` | `frame ≤ (first kind-1 event frame) + 5` | C |
| `0x0057ED90` | `sub_0057ED90_PlrSeqLeaveOk` | the sequence mode's leave test (not read past its first test) | I |
| `0x005415A0` | `sub_005415A0_UnitEventFirstFrame` | the least positive frame of the unit's queued events of a kind | I |
| `0x00581490` | `sub_00581490_ObjEvOperateEnd` | object event 1: mode 1 → 2 (§ 6.5) | I |
| `0x005A54F0` | `sub_005A54F0_MonGetHitAddKnockback` | base class 78: a get-hit also knocks back | I |
| `0x0063F690` | `sub_0063F690_ObjectsLoad` | the Objects table load (its `FrameCnt` shift, § 6.5) | I |

Data: `g_HitClassElements` `0x006E16D8` (4 pairs, repeated: packet offset, class), `g_HitClassCounter` `0x0088CAD0`
(byte), `g_PathPlanFuncs` `0x006EB6D8` (16 planners by path type). Read, existing: `sub_0056E5B0_UnitWalkVelocity`,
`sub_00620E80_RunVelocityStat`, `sub_0057F240_RunStaminaDrain`, `sub_00580C20_PlrModeMoveFrame`,
`sub_0057F090_PlrModeStartMove`, `sub_00621360_AnimPathBaseSpeed`, `sub_006213D0_AnimMoveBaseRate`,
`sub_00648690_PathSetSpeed`, `sub_0064FB90_PathSetPoint`, `sub_00649970_PathPlan`, `sub_005A6380_MonModeVelocity`,
`sub_0057EEC0_PlayerModeAllowed`, `sub_005809D0_PlayerModeCmd`, `PLAYER_ModeCmdUnit`, `sub_0057CB00_GetHitRoll`,
`sub_0057CE30_HitClassPick`, `COMBAT_GetHit`, `sub_00554650_PacketHitClassSet`, `sub_0046C140_MonModeAllowed`,
`COMBAT_ApplyStun`, `sub_0064A5A0_MissileHitClass`. *2026-10-27 (Phase 2):* `sub_0057F240_RunStaminaDrain` and
`sub_0057CB00_GetHitRoll` are `C` in `re/symbols.csv`, their evidence moved here (the run section).

## Walkthrough

### 1. Velocities

```c
// fn:sub_00620E80_RunVelocityStat@0x00620E80 (EAX class, EBX unit), trimmed: from UNIT_AnimInit, player form, mode 3 or 19
list = STATLIST_Alloc(pool, 4 /*drop on a mode change*/, 0, unit type, guid);
cs = CharStats[class];
if (cs->WalkVelocity) { SetStat(list, 67, (RunVelocity * 100) / WalkVelocity - 100); LinkToUnit(unit, list); }  // unsigned 64-bit divide
```

- [I] **Player.** `UNIT_AnimInit` calls `RunVelocityStat` for a player form in mode 3 (run) or 19 (knockback) before
  `UNIT_AnimSetRate` (anim/0001 § 3). Its list has flag 4, the flag `sub_006272E0_StatListsDropOnMode` drops at the
  next `UNIT_SetMode` to another mode, so the 50 (stock `RunVelocity` 9, `WalkVelocity` 6 in all seven rows) counts
  only while the run lasts. (fn:sub_00620E80_RunVelocityStat@0x00620E80, fn:sub_006272E0_StatListsDropOnMode@0x006272E0,
  0x00624421, 0x006244A4, `p50d-model.txt` `WALK`, `RUN`)
- [I] **The path speed.** The moving branch of `UNIT_AnimSetRate` (anim/0002 § 3.4) calls `PathSetSpeed(path, (pbase
  · X) / 100)` (signed), `X = max(B_FRW + stat 67, 25)`. `sub_00621360_AnimPathBaseSpeed(EAX class, ECX type)` is
  CharStats `+0x040` (`WalkVelocity`) `<< 8` for type 0 and MonStats `+0x032` (`Velocity`) `<< 8` for type 1, with no
  mode argument: a running monster's path base is its walk `Velocity` (the RN record's speed `+0x38` changes only its
  animation rate). `PathSetSpeed` writes `+0x7C` and the maximum `+0x84`, and `+0x38 = 15` when the speed changed.
  (fn:sub_00621360_AnimPathBaseSpeed@0x00621360, fn:sub_00648690_PathSetSpeed@0x00648690, 0x006241A9–0x006241C9)
- [I] Stock values: a player at `X` 100 walks at `v` 1 536 and runs (with the 50) at 2 304; MonStats `Velocity` is
  0..15 (730 rows), so a monster's `pbase` is at most 3 840. (`p50d-model.txt` `WALK`, `RUN`, `MONVEL`,
  tbl:CharStats.txt:WalkVelocity, tbl:MonStats.txt:Velocity)
- [I] **Monster stat 67.** 75 at creation (anim/0002 § 4, fn:sub_00573CB0_MonStatsInit@0x00573CB0); the mods and
  states of anim/0002 § 4 add to it; and `MonSetMode` calls `sub_005A6380_MonModeVelocity` when the mode command's
  block has a non-zero `+0x10`: it finds or makes the unit's list with flag `0x4000` (made with flags `0x4004`, so it
  too drops at a mode change), sets stat 67 there to that value and re-runs `UNIT_AnimSetRate`. So a monster's run
  speed above its walk base comes from the AI's command (plan 0052's oracle). (fn:sub_005A6380_MonModeVelocity@0x005A6380,
  fn:sub_005A7C20_MonSetMode@0x005A7C20)
- [I] **The slowing states** reach movement only through stat 67 and the FRW bonus in `X` (chill's 67 = the cold
  effect, `item_slow` and the curses of anim/0002 § 4, each re-running the rate), floored at 25. A mid-move change
  takes effect at once: the moving branch writes the path speed at each re-call, and the step reads `+0x7C` every
  frame. (fn:UNIT_AnimSetRate@0x00623F50, fn:sub_006502D0_PathVelocityStep@0x006502D0)
- [I] **Who else writes a unit's path speed** (`PathSetSpeed`, 25 sites: 10 server, 15 client): `UNIT_AnimSetRate`
  (knockback `0x00624105`, moving `0x006241C9`), `sub_005735A0_MonInitMode` (`0x005735CB`), `sub_0059FA30_MissileCreate`
  (two, a missile's), and five catalogue skill functions (`0x005CBBB5`, `0x005CD47C`, `0x005CF86E` in
  `sub_005CF6B0_SkillSt31Charge`, `0x005D90A6`, `0x005D9FFE` near `sub_005D9F70_LeapAttackPath`), plan 0046's and
  boundary oracles here. Direct stores to path `+0x7C` outside these were not enumerated; one is
  `sub_00648DC0_PathMoveReset`'s `+0x7C = +0x80` under path flag `0x8000`, at every player move start.
  (`p50d-calls.txt` `CALLS sub_00648690_PathSetSpeed 25`, fn:sub_00648DC0_PathMoveReset@0x00648DC0)
- [I] `sub_0056E5B0_UnitWalkVelocity` (player `WalkVelocity << 8`, monster `Velocity << 8`, else 0x600) has two
  callers, both catalogue (`0x005CBBAE`, `0x005D909C`); the moving branch does not use it. (`p50d-calls.txt`)

#### 1.1 A class with no walk record (the `lane/a50t` review's reads)

- [I] **The walk base at load.** `sub_00650F00_MonStatsSpeeds` takes the walk speed with
  `ANIMDATA_Lookup(mode 2, type 1, base class, no inventory)` (`0x00650F3E`–`0x00650F4F`), which returns the table's
  fallback record when the name has no record (anim/0001 § 2: frames 2048, **speed 256**). So a class whose
  `<Code>WL<BaseW>` record is missing gets `+0x036 = 256`, scaled by `Velocity(i) / Velocity(b)` only when its base row
  `b ≠ i` and `Velocity(b) > 0` (unsigned `div`), then `0 → 0`, capped at `0x7FFF` (`cmp; sbb; and`, `jb`); below
  class 410 its run `+0x038` is `+0x036(b) / 2` (signed) = 128 for such a base, from 410 the `RN` lookup, falling back
  to 256 the same way. This settles MonStats § Timing's `[L]` for the seven classic `9A` rows (traps 326–330, 369,
  355) and the `E9` rows: walk base 256 (and run 128 below 410). (fn:sub_00650F00_MonStatsSpeeds@0x00650F00,
  fn:ANIMDATA_Lookup@0x0066A9B0, 0x00650F80–0x00650F9D, 0x00650FBE–0x00650FD4, `p50d-monstatsspeeds.asm`, tbl:MonStats.txt:Velocity,
  tbl:MonStats.txt:BaseId)
- [I] **`+0x4C` of a `Velocity`-0 class in S1.** A classic class's S1 takes the moving branch (anim/0002 § 1), which
  returns without a write only when the unit has no path; every monster that `SUnitCreate` makes with create flag bit
  0 gets a dynamic path (drlg/0005: the spawn and preset paths pass it), so the branch writes `+0x4C = ⌊256 · X / 100⌋`
  (192 at the new-monster `X` 75) and the path speed `(0 << 8) · X / 100 = 0`: the animation runs at the walk-base rate
  while the unit does not move. A monster created without flag bit 0 (no path) keeps the `+0x4C` of its previous rate
  call. (fn:UNIT_AnimSetRate@0x00623F50, 0x00624128–0x006241D4, fn:sub_00554850_SUnitPathCreate@0x00554850,
  fn:sub_00621360_AnimPathBaseSpeed@0x00621360)

### 2. The per-frame step

```c
// fn:sub_00650840_PathStep@0x00650840 (unit, k = 0x400 from UnitMoveStep), trimmed
p = unit->pPath;  p->flags &= ~8;
if ((p->flags & 0x20) && p->nPoints > 0 && p->speed && ((p->flags & 0x40000) || PathStepTargetCheck(p))
    && p->iPoint < p->nPoints) {
    PathVelocityStep(p, k);                         // step = (d * ((speed * k) >> 6)) >> 12, accel every 5th call
    if (p->stepX || p->stepY) {
        PathStepMove(p, &x, &y);                    // snap, collision walk, iPoint++ on a reached point
        PathSetPoint(p, x, y, 0);
        if (p->type != 4 && p->iPoint < p->nPoints) PathAimNextPoint(p, 1);
        if (p->iPoint < p->nPoints) return 1;
    }
}
PathStop(p);  return 0;                             // UnitMoveStep: 2 - (ret != 0)
```

- [I] **The step.** `PathVelocityStep(EAX path, ECX k)`: `k ≤ 0` → 0x400; with an acceleration (`+0x88`), every fifth
  call `v += accel` (capped at `+0x84`, which zeroes the acceleration; floored at 0); then `s = (v · k) >> 6` and
  `stepX = (+0x6A · s) >> 12`, `stepY = (+0x6E · s) >> 12` (all `imul` and `sar`, signed 32-bit). `PathStep` has
  three call sites, one server (`UnitMoveStep`, `k = 0x400`), so on the server `s = 16 v` and the axis step is
  `(d · 16 v) >> 12` = `⌊d · v / 256⌋` 1/65536 subtile. (fn:sub_006502D0_PathVelocityStep@0x006502D0, 0x00650899–0x0065089E,
  `p50d-sites.asm` `## 0x6502d0`, `p50d-tables.txt` `PVS`, `p50d-calls.txt` `CALLS sub_00650840_PathStep 3`)
- [I] **The direction.** `(+0x6A, +0x6E)` is `sub_0064FC60_PathDirection`'s vector from the position to the next point
  (`sub_0064FE40_PathAimNextPoint`, after each plan and each move): a `g_PathDirTable` row with the axes swapped and
  signed by octant; every row's norm² lies between 16 767 217 and 16 777 216 (4096²), so `d` is a unit vector × 4096
  and a speed `v` moves `v / 16` subtiles per frame on an axis (`v · 2896 / 4096 / 16` on the diagonal row 127).
  (fn:sub_0064FE40_PathAimNextPoint@0x0064FE40, fn:sub_0064FC60_PathDirection@0x0064FC60, `p50d-tables.txt` `DIR`)
- [I] **The point snap.** `sub_00650090_PathStepSnap` (not for path type 4): with `m = max(|stepX|, |stepY|)` and the
  next point at its subtile centre (`(word << 16) + 0x8000`), when both `|point − position|` axes are ≤ `m` the step
  becomes exactly the remaining delta and the point counts as reached. So the frames to a point `d` subtiles away on
  an axis are `⌈65536 d / step⌉` (the last one partial), e.g. walk 8 frames for 3 subtiles, run 6, knockback 3.
  (fn:sub_00650090_PathStepSnap@0x00650090, `p50d-model.txt` `FRAMES`)
- [I] **The move.** `sub_00650660_PathStepMove`: a zero step stops the path at the subtile centre. When the step
  changes the subtile, `sub_00650150_PathStepCollide` walks the crossed subtiles (the step added repeatedly from the
  old position until the target subtile, at most 10 crossings) with the collision test `0x0064FF90`; at a blocked one
  the position stops at the centre of the last free subtile, and then a monster path with flag `0x10` re-plans
  (`sub_00650350_PathReplan`), any other path sets `+0x24 = +0x28` (ends). A reached point increments `+0x24`; the
  path byte `+0x90` is decremented at each subtile change for path types other than 8 and 11.
  *2026-10-27 (`lane/p50d` review):* the walk's increment is not the step itself: `0x00678F00` first halves both
  axes together (`sar 1`) until each lies within `±0x10000` (one subtile), and the walk adds that increment, testing
  only when the subtile changes. Each free tested subtile counts in path `+0x1D4` (recorded at `+0x1D8…` under flag
  `0x20000`); at the 10th the walk stops testing and the full step's target is taken unchecked (`jge 0x00650292`),
  with flag `0x8` set when any subtile was counted; a blocked test returns 1, otherwise 0.
  (0x00650177, 0x0065022F–0x0065023D, 0x00650259–0x00650279, 0x00650292–0x006502AA)
  (fn:sub_00650660_PathStepMove@0x00650660, fn:sub_00650150_PathStepCollide@0x00650150, fn:sub_00650350_PathReplan@0x00650350)
- [I] **The end.** `PathStep` returns 1 while points remain; otherwise `sub_006507B0_PathStop` snaps the position to
  the subtile centre, clears flag `0x20`, the point count and index and the step, and `UnitMoveStep` returns 2.
  `sub_006503F0_PathStepTargetCheck` (unless flag `0x40000`) re-plans when the target unit has moved more than 5
  subtiles from the planned end, or ends a path whose target is within its byte `+0x93`. The planning itself
  (`PathPlan`, the target) is phase (5)'s. (fn:sub_006507B0_PathStop@0x006507B0, fn:sub_006503F0_PathStepTargetCheck@0x006503F0,
  fn:sub_00554CA0_UnitMoveStep@0x00554CA0)
- [I] **No acceleration for units.** `PathSetAccel` (`+0x88`) has two call sites, `0x0059FDCC` in
  `sub_0059FA30_MissileCreate` and one client; `PathSetMaxSpeed` likewise. A player's or monster's path keeps the
  speed the rate code set. (`p50d-calls.txt` `CALLS sub_00648700_PathSetAccel 2`)
- [I] **Wrap bound.** `d · s` with `|d| ≤ 4096` and `s = 16 v` fits 32 bits for `v ≤ 32 767` (`4096 × 16 × 32 767 =
  2 147 418 112`) and wraps from `v = 32 768` (`4096 × 16 × 32 768 = 2³¹`) on a component of +4096 (rows 0 and its
  octant images), turning that axis step negative (−4096 reaches −2³¹ without wrapping; smaller components wrap later); `v · 0x400`
  itself fits up to `v = 2 097 151`. No test guards it. A player (`pbase` 1 536) reaches `v = 32 768` from `X = 2 134`
  (`X = 2 133` gives 32 762); a monster with `Velocity` 15 (`pbase` 3 840) from `X = 854` (853 gives 32 755). Whether a
  stock source reaches such an `X` is not surveyed (open questions). (0x00650330–0x00650345, `p50d-model.txt` `EDGE`)

### 3. Who steps, per mode

- [I] The 11 `UnitMoveStep` sites (`p50d-calls.txt`): `PlrModeSkillFrame` (move-first skills, `0x005804A9`),
  `PlrModeMoveFrame` (`0x00580C6E`: walk, run, town walk, knockback), the monster DT frame (`0x005A7366`, only while
  moving), S3 (`0x005A74A6`), `MonAttackFrame` (two, every-frame attack modes and the move-first skill), WL
  (`0x005A84C4`), RN (`0x005A84F6`), KB (`0x005A8636`), `MonSeqFrame` (`0x005A86C9`), and a missile's move
  (`0x005AE24D`, skills/0002). Each runs once per call of its mode's every-frame event (anim/0001 §§ 9–10), so the
  step is one per game frame for every moving mode. (fn:sub_00554CA0_UnitMoveStep@0x00554CA0)
- [I] Player walk and run end when `UnitMoveStep` returns 2 (`PlrModeMoveFrame`: neutral, or the queued interact or
  skill); monster WL and RN likewise (`MonModeEndGeneric`). The animation frame of a walking monster advances
  (anim/0001 § 8) but does not end the mode. (0x005A84C9–0x005A84D2, 0x005A84FB–0x005A8504,
  fn:sub_00580C20_PlrModeMoveFrame@0x00580C20)
- [I] `PlrModeMoveFrame` also runs, before the step, state 13's handler (`0x005C9D90`) and, for mode 3, the run drain
  (§ 3.1); after it, a 20-entry position history (`PlayerData+0xA0…`) by `GetTickCount` (25 ms) and a squared distance
  over 45: wall-clock data, not game state that the step reads. (0x00580C49–0x00580D7C)

#### 3.1 Run drain

- [I] `sub_0057F240_RunStaminaDrain(EDI unit)`: in a town room returns 1 (no drain). Else `q = RunDrain · 2`
  (CharStats `+0x042`); with an inventory, the body-location-3 item's base record `+0xD8` (Armor `speed`, 0, 5 or 10)
  multiplies it by `speed / 10 + 1` (signed; 1, 1, 2); `q += q · stat 154 / 100` (signed, truncating; `item_staminadrainpct`)
  when stat 154 ≠ 0; `q < 1 → 1`; stat 10 `−= q`; returns 1 while stat 10 > 0, else sets it to 0 and returns 0.
  A unit without an inventory returns 0 without draining. On 0, `PlrModeMoveFrame` restarts the move
  (`PlrModeStartMove`), which turns a run with stamina 0 into a walk (anim/0001 § 9.1), before this frame's step.
  (fn:sub_0057F240_RunStaminaDrain@0x0057F240, 0x0057F290–0x0057F2E6, tbl:CharStats.txt:RunDrain,
  tbl:Armor.txt:speed, tbl:ItemStatCost.txt:Stat, `p50d-model.txt` `ARMORSPEED`, `DRAIN`)

### 4. Knockback

- [I] **Start.** A player: `COMBAT_GetHit` with result bit `0x8` issues `PLAYER_ModeCmdUnit(0, 19, attacker)`;
  `PlrModeStartMove(19)` sets path type 8 and `+0x90 = 5`, plans, and starts the every-frame move. A monster:
  `COMBAT_GetHit` turns `0x8` into `0x4` (get-hit) when the class lacks the KB mode (`MonModeAllowed(13)`), and
  base class 78 adds `0x8` to every get-hit unless frozen (`sub_005A54F0_MonGetHitAddKnockback`); a knockback command
  runs `0x005A77D0`: refused unless the class has both GH and KB (MonStats2 mode bits, `sub_0046C140_MonModeAllowed`),
  then path type 8, `+0x90` = 10 for base class 78 else 5, plan, `SUNIT_SetMode(13)`. (fn:COMBAT_GetHit@0x0057CEE0,
  fn:sub_005A54F0_MonGetHitAddKnockback@0x005A54F0, 0x005A77E3–0x005A785F, fn:sub_0046C140_MonModeAllowed@0x0046C140)
- [I] **The point.** `g_PathPlanFuncs[8]` = `sub_0067A000_PathPlanKnockback`: `n = (+0x90 >> 1) + 1`; with `(dx, dy)` the
  unit's subtile minus the target unit's and `M = max(|dx|, |dy|)`, the point is the unit's subtile plus `(n·dx/M,
  n·dy/M)` (signed division; unchanged when `M` is 0), passed through `0x00679720` (not read) and set as the path's
  one point; no point when it equals the start. (fn:sub_0067A000_PathPlanKnockback@0x0067A000, `p50d-tables.txt` `PLAN 8`)
- [I] **Speed and length.** The knockback branch of `UNIT_AnimSetRate` sets the path speed to `0x1000` (anim/0002
  § 3.3), one subtile per frame on an axis. A player's knockback ends with the path (§ 2): 3 frames for `n` 3 on an
  axis, 5 on the diagonal (6 and 9 for `n` 6), fewer when the collision walk stops it; then `PlrModeMoveFrame` sets
  neutral (anim/0001 § 9.1). A monster's KB frame (`0x005A8630`) steps, advances the animation, and ends when
  `UNIT_AnimAtEnd` holds (`+0x48 ≤ +0x44 + r` after the advance), so from `+0x44 = 0` it lasts `max(1, ⌈L / r⌉ − 1)`
  calls of its every-frame event for the `GH` record's length `L` at `r` = MonStats `+0x36` (anim/0002 § 3.3), however
  far the path got (whether the first call runs in the start's own frame is not read here; open questions). Then
  `MonKnockbackEnd` (anim/0001 § 10). (0x005A8636–0x005A864F, fn:UNIT_AnimAtEnd@0x006217C0, `p50d-model.txt` `KB`)

### 5. The frame events as gates

- [I] **The do function.** A player's skill mode is scheduled at its start (anim/0001 § 7); `PlrModeSkillFrame` runs
  the used skill's do on an event of code 1 or 2 while `Unit+0xC4` bit 6 is clear (cleared by the start). So the do
  runs at `T + max(1, ⌈256 (f − S) / r⌉)` for the first frame `f ≥ S` of the record (or player sequence) whose event
  byte is 1 or 2 within the scanned steps, `r` the cast, attack or default rate of anim/0002; again at each later
  code-1/2 event unless the do set bit 6. A move-first skill instead runs its do on the arrival frame of its step.
  (fn:sub_00580460_PlrModeSkillFrame@0x00580460, fn:SUNIT_ScheduleModeEvents@0x005539B0, anim/0002 § 7's formula)
- [I] **The attack's delivery.** A player's normal attack is the do of skill 0 (`SKILL_AttackDo`), which runs the hit
  test, the build, the queue and `COMBAT_DeliverQueued` in that call, so the delivery is on the do frame. A monster's
  plain attack strikes in `MonAttackFrame` on each scheduled event (any code 1–4) or, in an every-frame mode, on a
  frame whose event byte is 1 (anim/0001 § 10). (fn:SKILL_AttackDo@0x0056F070, fn:sub_005A7670_MonAttackFrame@0x005A7670)
- [I] **Missile creation.** `SKILLS_SrvDo` creates the row's `srvmissile` after the do function in the same call
  (skills/0001 § 6), so on the do frame; missiles that a do function creates itself likewise. (fn:SKILLS_SrvDo@0x0056F7F0)
- [I] **The skill delay.** `SKILLS_SrvDo` sets state 121 for `delay` frames from the do's frame (a player only;
  a sequence skill only on its first event, `+0x38 >> 8 = 0`), and `SKILLS_CanUse` refuses a skill with a `delay`
  while it lasts. So the delay runs from the action frame, and the frames from the mode start to the do frame are
  not part of it. Callers of `SKILLS_SetDelayState`: 3 (`0x0056F065` in `sub_0056F020_SkillDelayFromCalc`, a
  catalogue path; `0x0056FAC1`, `0x0056FAD6` in `SKILLS_SrvDo`). (fn:SKILLS_SetDelayState@0x0056EF90,
  fn:SKILLS_CanUse@0x00647960, tbl:Skills.txt:delay, `p50d-calls.txt`)

### 6. Hit recovery, block, stun and the mode tests

#### 6.1 `COMBAT_GetHit`

```c
// fn:COMBAT_GetHit@0x0057CEE0 (defender, packet; EDX attacker), trimmed
if (in a town room && !(attacker is a monster whose MonStats +0x00D bit 2 is set)) return;
if (pkt->result & 1 /*hit*/) {
    if (!pkt->b64 && !(pkt->hitClass & 0xF0)) pkt->hitClass = HitClassPick(pkt, pkt->hitClass);
    def->hitClassB0 = pkt->hitClass;                                       // Unit+0xB0
}
if (HasState(def, 54)) { if (result & 2) STATE_Set(def, 92 /*death_delay*/, 1); return; }
player:  0x80 dodged → mode 13 under state 65's skill; 0x100 avoided → state 66's; 0x200 evaded → state 68's event;
         0x8010 blocked → unless 0x4000: block mode 9 if frame − stat95 > stat102/8 + 15, then stat95 = frame;
         0x2 killed → mode 0 (unless in DT or DD); 0x8 knockback → mode 19 at the attacker;
         0x4 get-hit → mode 4 if stunned (state 21's list) or GetHitRoll(def, pkt, hitClass) == 0; else flag 0x8000
monster (not in DT or DD): knockback → get-hit if no KB mode; base 78 adds 0x8; 0x2 → UnitKilled;
         0x8 → command 13; 0x10 → block mode 6 unless 0x4000, classes 243, 333, 705 or no BL mode;
         0x4 → command 3 (and the on-hit hook 0x005A43A0) if stunned or GetHitRoll == 0
```

- [I] As above (0x0057CEE0–0x0057D3BD). The order of the player tests is the order of the result bits read: dodge,
  avoid, evade, block, killed, knockback, get-hit, each returning. A get-hit is a mode **command** for a player
  (`sub_005809D0_PlayerModeCmd(0, 4, damage, 0, 0)`, unforced), which passes the two mode tests of § 6.2 before
  `PlrModeStartGetHit` runs. (fn:COMBAT_GetHit@0x0057CEE0, fn:sub_005809D0_PlayerModeCmd@0x005809D0)
- [I] **The hit-recovery length** is the get-hit mode's schedule: the `GH` record at the get-hit rate
  `⌊spd · (B_FHR + 50) / 100⌋` (anim/0002 § 3.2), `n(r) = max(2, ⌈256 F / r⌉)` frames (start frame 0), then neutral (anim/0001 § 9).
  For a monster the same with its record and `B_FHR` (mode 3). (fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30,
  fn:SUNIT_ScheduleModeEvents@0x005539B0)
- [I] **The block length** is the block mode's schedule at the block rate (anim/0002 § 3.2). A player's block
  animation starts only when `frame − stat 95 (lastblockframe) > ⌊stat 102 / 8⌋ + 15` (stat 102
  `item_fasterblockrate`, the raw stat, signed division by 8 toward zero); when that test passes, stat 95 is set to the
  frame after the command whether or not the command was accepted, and when it fails nothing is written and the
  function returns (`jle 0x0057D3BD`); the block itself (the result bit) is combat's. A monster blocks in
  mode 6 when its class has the BL mode and is not 243, 333 or 705. (0x0057D282–0x0057D2D6, `p50d-sites.asm`
  `## 0x57d270`, tbl:ItemStatCost.txt:Stat)

#### 6.2 The player mode tests

- [I] **`sub_0057EDD0_PlrModeLeaveOk(EAX unit, EBX requested)`** (first in both `PlayerModeCmd` and
  `PLAYER_ModeCmdUnit`): with an item on the cursor every request but 0 (DT) and 17 (DD) is refused. Requests 0, 1,
  5 and 17 pass. Others by the current mode (`p50d-tables.txt` `LEAVE`): DT, GH, BL, DD refuse; A1, A2, SC, TH pass
  while a mode-end event is queued (`sub_0057ED70_PlrModeEndPending`: `frame ≤ E + 5`, `E` the least positive frame
  of the unit's kind-1 events, 0 when none), and otherwise only a GH or BL request; KK passes while a mode end is
  queued; S1 refuses for class 0 (Amazon) and S3 for class 5 (Druid); SQ by `sub_0057ED90_PlrSeqLeaveOk`; every other
  mode passes. So a player in get-hit or block keeps the mode to its end (bar death and neutral requests).
  (fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, fn:sub_0057ED70_PlrModeEndPending@0x0057ED70,
  fn:sub_005415A0_UnitEventFirstFrame@0x005415A0, 0x0057EDFA–0x0057EE17)
- [I] **`sub_0057EEC0_PlayerModeAllowed(requested, 1, skill)`** (second, unless the command is forced; 4 call sites:
  the two commands, `PlayerModeEnd`'s knockback branch, `sub_0054D750_SrvPacketDispatch`): 0 under state 54 or in DT
  or DD; 1 without a used skill (a get-hit start clears it); 1 when the request is for the used skill itself and its
  `srvdofunc` is 67 or 76; for a used skill **without** `interrupt` (Skills `+0x007` bit 7): in neutral a forced
  neutral command and 1, else only requests 7, 8, 10, 11, 13, 18 pass while a mode end is queued; **with**
  `interrupt`: under state 42 (`concentration`), `Range(player unit seed, 100)` (draw) and a refusal when the draw is
  below stat 164 (`skill_concentration`) of that state's list; then a refusal under state 15 (`concentrate`); a
  refusal in neutral is a forced neutral command and 1. So a get-hit, block or knockback during a non-interruptible
  skill never starts, and during an interruptible one under Concentration it starts with probability `1 − stat 164 /
  100` (one draw per command). (fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, 0x0057EF7C, tbl:Skills.txt:interrupt,
  tbl:Skills.txt:srvdofunc, `p50d-calls.txt` `CALLS sub_0057EEC0_PlayerModeAllowed 4`)
- [I] **Monsters** have no such test on the get-hit path beyond the mode bits: `sub_0046C140_MonModeAllowed(class,
  mode)` is MonStats2 `+0x0F0` bit `mode` (the `m<mode>` flags) of the class's MonStats2 row, and `MonSetMode`'s
  state-54 assert (anim/0001 § 10). (fn:sub_0046C140_MonModeAllowed@0x0046C140, tbl:MonStats2.txt:mDT)

#### 6.3 The get-hit roll

```c
// fn:sub_0057CB00_GetHitRoll@0x0057CB00 (def, pkt, hc) -> 0: get hit, 1: not
if (HasState(def, 1 /*freeze*/) || (pkt->poison && pkt->poison == pkt->total) || pkt->total < 0x100) return 1;
hp = UnitGetMaxHp(def);
D = (hc in {2,6,10,11}) ? 8 : (hc in {4,8}) ? 32 : (hc == 5) ? 64 : 16;    // jump table 0x0057CBF8 on hc - 1 (0..11)
if (pkt->total < hp / D) return 1;                                         // idiv
if (pkt->total < hp / (D / 2) && RangePow2(&def->seed, 2) == 0) return 1;  // draw 1
if (pkt->total < hp / (D / 4) && RangePow2(&def->seed, 4) == 0) return 1;  // draw 2 (or the only one)
if (def is a monster && !MonModeAllowed(def->class, 3 /*GH*/)) return 1;
return 0;
```

- [I] As above: signed divisions of the max HP (1/256 units, as the total `+0x4C`); `D/2` and `D/4` are signed
  (`cdq; sub; sar 1` and `cdq; and 3; add; sar 2`). Draws on the defender's unit seed (`Unit+0x20`): none below
  `hp/D` or at `hp/(D/4)` and above; one at `[hp/(D/2), hp/(D/4))`; one or two at `[hp/D, hp/(D/2))` (the second
  only when the first is non-zero). The get-hit probability per band is 3/8, 3/4, 1. `hc` is the whole `+0x60`, so
  any class with a high nibble takes 16. Two callers, both in `COMBAT_GetHit` (player `0x0057D37A`, monster
  `0x0057D0C8`). (0x0057CB0B–0x0057CBF5, `p50d-sites.asm` `## 0x57cb00`, `p50d-tables.txt` `GHD`,
  `p50d-model.txt` `GETHIT`, fn:RNG_RangePow2@0x00472210)
- [I] Whether the roll runs at all is gated earlier: result bit `0x4` is set by the hit test only on a hit without
  state 54 (combat/0001 § 4, fn:COMBAT_MeleeHitTest@0x0057EC10); a stunned defender takes the get-hit without it.

#### 6.4 Stun

- [I] `COMBAT_ApplyStun(attacker, length)` (one caller, in `COMBAT_ApplyDamage`): state 21 until `frame + length`
  (capped at 250, 13 for a hireling from 12 up; the unique roll and the boss and `Velocity` 0 refusals as combat/0001
  § 9), and a unit event 12 at that frame (re-set when the list exists). Its timing effects found here: a stunned
  defender's get-hit skips the roll (§ 6.1); a monster's next AI event after a neutral start is at `T + 45` under
  stun (anim/0001 § 10), and `sandleaper1`'s knockback end waits 45. No test of state 21 was found in the two player
  mode tests of § 6.2. (fn:COMBAT_ApplyStun@0x0057AAE0, 0x0057AB9A–0x0057ABF9)

#### 6.5 Objects: the operate frames

- [I] **`FrameCnt` is 8.8 in memory.** `sub_0063F690_ObjectsLoad` shifts each record's eight `FrameCnt` dwords
  (`+0xD8`…`+0xF4`) left by 8 after loading (`p50d-tables.txt` `OBJSHL`), so `UNIT_AnimInit`'s object `+0x48 =
  FrameCnt[mode]` is frames << 8 like every other type's. *This corrects anim/0001 § 1* ("objects unshifted"; dated
  note there). (0x00640E33–0x00640E64, fn:sub_0063F690_ObjectsLoad@0x0063F690, tbl:Objects.txt:FrameCnt0)
- [I] **The operating mode.** After a chest's drops, `OBJOP_Chest` sets mode 1 when `Mode1` is set and queues object
  event 1 at `frame + (FrameCnt1 >> 8) + 1`, i.e. `FrameCnt1 + 1` frames on; event 1 (`sub_00581490_ObjEvOperateEnd`)
  sets `Unit+0x10 = 2` when the object is still in mode 1 and the row has `Mode2`, **without** `UNIT_SetMode` (no
  animation start, so no `Sync` draw), and unmarks the footprint (`UNIT_CollUnmarkRect`) when `HasCollision2` is 0.
  The same `FrameCnt1 >> 8` + frame + 1 queue appears at 46 sites (`p50d-calls.txt` `FC8`); two are read here
  (`0x0058639A`, `0x00586475`), the other 44 are not. (fn:OBJOP_Chest@0x00585F60, fn:sub_00581490_ObjEvOperateEnd@0x00581490,
  0x0058639A–0x005863B7, 0x005814A7–0x005814BE, tbl:Objects.txt:FrameCnt1, tbl:Objects.txt:Mode1, tbl:Objects.txt:Mode2,
  tbl:Objects.txt:HasCollision2) *(2026-10-27, `lane/a3f` review: the anchor read `HasCollision0`; event 1 tests `+0x122`, `HasCollision2`.)*

### 7. The hit class

- [I] **Sources of `+0x60`.** Melee delivery (`COMBAT_DeliverQueued`, `0x0057D5EA`): when the packet's `+0x64` is 0
  and `+0x60 & 0xF` is 0, `+0x60 |= sub_00623C20_UnitBaseHitClass(attacker)`: a player's weapon from
  `SkillSrcDamWeapon(unit, 0)` → `sub_0062A180_ItemHitClass` (the base record's `+0x13C`, Weapons `hit class`), 1
  without a weapon; a monster's MonStats2 `+0x014` (`HitClass`); 0 otherwise. A missile's hit
  (`MISSILE_ApplyDamage`, `0x005AD863`): `+0x60 = Missiles HitClass | (+0x60 & 0xF0)`. A doubled monster hit
  (`sub_005A5560_MonCritDouble`): `sub_00554650_PacketHitClassSet(0x10)` when the high nibble is empty.
  *This corrects combat/0001 § 6*, which names `HitClassPick` at the delivery; that call is `UnitBaseHitClass`, and
  `HitClassPick`'s two calls are in `COMBAT_GetHit` and its helper `0x0057CEC0` (dated note there).
  (fn:sub_00623C20_UnitBaseHitClass@0x00623C20, fn:sub_0062A180_ItemHitClass@0x0062A180, fn:COMBAT_DeliverQueued@0x0057D4F0,
  fn:MISSILE_ApplyDamage@0x005AD730, `p50d-sites.asm` `## 0x57d5dc`, `## 0x5ad85f`, tbl:Weapons.txt:hitclass,
  tbl:MonStats2.txt:HitClass, tbl:Missiles.txt:HitClass)
- [I] **`HitClassPick(ESI packet, EAX class)`**: `i = g_HitClassCounter & 3` (a byte, then incremented); the first of
  the four `g_HitClassElements` entries from `i` whose packet field is > 0 (signed) gives the high nibble: cold `+0x24`
  → 0x30, fire `+0x10` → 0x20, lightning `+0x1C` → 0x40, poison `+0x28` → 0x50 (the table holds the four twice, so
  the scan wraps); none → 0x10 when the result has `0x2000` (doubled), else 0; a class of 0 becomes 13 (`over`);
  returns `nibble | class`. The counter is global (all games in the process) and is not an RNG seed.
  (fn:sub_0057CE30_HitClassPick@0x0057CE30, data:g_HitClassCounter@0x0088CAD0, data:g_HitClassElements@0x006E16D8,
  `p50d-sites.asm` `## 0x57ce30`, `p50d-tables.txt` `HCE`)
- [I] **What the server does with it.** `GetHitRoll`'s divisor (§ 6.3), where any element or doubled nibble gives 16
  whatever the counter picked, so the counter does not change a server outcome there. It is also copied into
  `Unit+0xB0` on every hit (and `MonKnockbackEnd` writes `0xA0` there); the readers of `Unit+0xB0` were not
  enumerated (open questions). (fn:COMBAT_GetHit@0x0057CEE0, fn:sub_005A8520_MonKnockbackEnd@0x005A8520)

### 8. Draws, seeds and the chaining reading (ADR-0014)

- [I] **Movement step**: no draw (`UnitMoveStep`, `PathStep` and the functions of § 2 call no RNG function; the
  replan and the target revalidation reach `PathPlan`, whose planners are phase (5)'s, the random-walk type 10 among
  them, drlg/0009). Inputs: the path (position, points, speed, direction, flags), the collision grid; outputs: the
  position, the point index, the room links. (fn:sub_00650840_PathStep@0x00650840, fn:sub_00649970_PathPlan@0x00649970)
- [I] **Mode commands on a hit**, in the order of a delivery (combat/0001 § 6): the durability draws
  (attacker's weapon, then the defender's armour slot, weight and roll, items/economy § H), the stat events 7 and 3,
  the knockback handler `0x005D10C0`, then `COMBAT_GetHit`: `GetHitRoll` (defender seed, 0–2), then the command's
  `PlayerModeAllowed` draw (player seed, 0 or 1). On a player defender all of these are the player's own seed, so they
  chain with the player's other events on it (combat/0001 § 11). (fn:COMBAT_DeliverQueued@0x0057D4F0)
- [I] The run drain, the knockback planner (no draw in `0x0067A000`'s read part), the stun, the delay state and the
  object operate end draw nothing. (fn:sub_0057F240_RunStaminaDrain@0x0057F240, fn:sub_00581490_ObjEvOperateEnd@0x00581490)
- [I] **Event kind: movement step** (ADR-0014): one per moving unit per frame, inside its mode's every-frame event;
  inputs the path speed (rate code, § 1), the planned points (phase (5)), the collision grid; output the position;
  no draw. It chains on nothing. (fn:sub_00554CA0_UnitMoveStep@0x00554CA0)

### 9. Boundary recommendation for Phase 2 (for the P1.3 review)

- **Oracles:** the mode request (plan 0045) and the AI's command and its velocity block (plan 0052); the path plan
  (points, phase (5)) and `0x00679720`; the catalogue speed writers of § 1 and the reschedules of anim/0001 § 7.1;
  the client.
- **Modelled:** the speeds (§ 1), the step and the snap (§ 2), the run drain, the knockback point and its length,
  the gates of §§ 5–6, `GetHitRoll` with its draws, the hit-class nibble, the object operate end.
- **Log windows:** the step per frame of one unit in a window (position before and after, `+0x7C`, the direction,
  the point index, the return of `UnitMoveStep`), not every unit every frame (ADR-0014 § Log volume); `COMBAT_GetHit`
  at entry (result bits, `+0x60`, total, max HP, the defender's seed) and the mode command it issues with
  `PlayerModeAllowed`'s seed before and after; `sub_0057EDD0_PlrModeLeaveOk`'s result; object event 1.

## Data touched

- Tables: tbl:CharStats.txt:WalkVelocity, tbl:CharStats.txt:RunVelocity, tbl:CharStats.txt:RunDrain,
  tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run, tbl:MonStats2.txt:HitClass, tbl:MonStats2.txt:mDT,
  tbl:Armor.txt:speed, tbl:Weapons.txt:hitclass, tbl:Missiles.txt:HitClass, tbl:Skills.txt:interrupt,
  tbl:Skills.txt:srvdofunc, tbl:Skills.txt:delay, tbl:Objects.txt:FrameCnt0, tbl:Objects.txt:Mode1,
  tbl:Objects.txt:Mode2, tbl:Objects.txt:HasCollision2, tbl:ItemStatCost.txt:Stat (stats 10, 67, 95, 102, 154, 164).
- Unit: struct:Unit+0x10, struct:Unit+0x20, struct:Unit+0x2C, struct:Unit+0x60, struct:Unit+0xB0, struct:Unit+0xC4;
  path (`PathMove`): `+0x00`/`+0x04` position, `+0x24`/`+0x28` point index and count, `+0x34` flags, `+0x3C` type,
  `+0x58` target unit, `+0x6A`/`+0x6E` direction, `+0x72`/`+0x76` step, `+0x7C` speed, `+0x80`, `+0x84` maximum,
  `+0x88` acceleration, `+0x8C` counter, `+0x90`, `+0x93`, `+0x9C` points; packet struct:DamagePacket+0x04,
  struct:DamagePacket+0x4C, struct:DamagePacket+0x60, struct:DamagePacket+0x64.

## Dead ends

- Ghidra shows `UnitMoveStep` calling `PathStep(unit, 0x400)` and `PathStep` with one parameter; objdump shows the
  `0x400` taken from `[ebp+0xC]` into `ECX` for `PathVelocityStep` (0x00650899).
- `0x005A77D0`, `0x005A8630`, `0x005A8490`, `0x005A84F0` and `0x00581490` had no Ghidra function before this lane's
  import; read from objdump (`p50d-sites.asm`).
- The Objects `FrameCnt` shift is in the loader, not in the `.bin` (the layout docs' values are the file's).

## Open questions

- [L] Whether any stock source gives a moving `X` of 854 (a monster with `Velocity` 15) or 2 134 (a player) or more,
  where the step product wraps (§ 2); not surveyed.
- [L] The readers of `Unit+0xB0` (the stored hit class) on the server.
- [L] What the 44 unread `FrameCnt1 >> 8` queue sites schedule (other operate kinds, portals, quest objects), and
  `0x00679720` (the knockback point's adjustment).
- [L] Whether a player under stun is refused anything other than through the get-hit it takes; no state-21 test was
  found in `PlrModeLeaveOk` or `PlayerModeAllowed`.
- ~~Whether an every-frame event queued during a frame's monster or player list run first runs in that frame or the
  next.~~ *2026-10-27 (Phase 2, run:2026-10-27-anim):* in that frame when queued before its type's every-frame list
  is walked, else in the next (9 682 starts, [the run section](#plan-0050-phase-2-run2026-10-27-anim)).
- [L] `sub_0057ED90_PlrSeqLeaveOk` past its first test (a used skill whose record byte `+0x16` is non-zero passes).

## Plan 0050 Phase 2 (run:2026-10-27-anim)

The closing check of [run:2026-10-27-anim](experiments.md#run2026-10-27-anim) (55 logs; `2026-10-27-anim-check.txt`,
`2026-10-27-anim-summary.txt`; setup and boundary in [anim/0001's run section](0001-modes-frames.md#plan-0050-phase-2-run2026-10-27-anim)).
Every compared kind has 0 mismatches; where a statement above is tagged inferred and this section raises it, the tag
and the run given here are the current ones. The collision test `0x0064FF90`, the path plan and replan, the catalogue
speed writers (Charge, Leap Attack) and the mode requests are oracles.

- **The step** (§ 2) **raised.** [C] 99 241 consecutive path steps of the windowed units (the player always, one
  monster at a time) reproduce the next position (16.16) and point index (`step`, `step-point` 97 139): `(d · 16 v) >>
  12` per axis from `PathVelocityStep`, the point snap, and the collision walk (the halved increment, the 10-crossing
  exit) over the logged collision results, 3 steps stopped by a blocked subtile and 2 102 after a replan among them.
  (fn:sub_00650840_PathStep@0x00650840, fn:sub_006502D0_PathVelocityStep@0x006502D0,
  fn:sub_00650090_PathStepSnap@0x00650090, fn:sub_00650660_PathStepMove@0x00650660,
  fn:sub_00650150_PathStepCollide@0x00650150, run:2026-10-27-anim)
- **The speeds** (§ 1) **raised in part** (not the floor). [C] At every moving and knockback rate exit the path speed is
  `(pbase · max(B_FRW + stat 67, 25)) / 100` with CharStats `WalkVelocity << 8` (player) or MonStats `Velocity << 8` (monster), and
  `0x1000` in knockback (`pathspeed` 127 584); each windowed step's speed equals the last such call's (`pathspeed-step`
  131 167; not compared after a catalogue writer: sp-pal-chg's 160 Charge steps run at 5 760, `ps-p-m18-v`, stat 67 100 at all 156 Charge calls, P1b-15).
  Walk 1 536 and run 2 304 for the players at `X` 100 and 150; the floor at 25 is not reached (P1b-14), so it stays
  `[I]`. (fn:sub_00621360_AnimPathBaseSpeed@0x00621360, fn:sub_00620E80_RunVelocityStat@0x00620E80,
  fn:UNIT_AnimSetRate@0x00623F50, run:2026-10-27-anim)
- **The run drain** (§ 1) **raised in part.** [C] 37 434 run frames take
  `max(1, RunDrain · 2 · (armour speed / 10 + 1) + ⌊that · stat 154 / 100⌋)` from stat 10 (`drain`). [I] The turn to a walk at 0 is not reached (no run ran out of
  stamina). (fn:sub_0057F240_RunStaminaDrain@0x0057F240, run:2026-10-27-anim)
- **The monster knockback** (§ 4) **raised.** [C] 541 monster knockbacks end (`MonKnockbackEnd`) in the frame their
  advance reaches the length, and no knockback frame before it ends one (`kb-end` 3 585 frames).
  (fn:sub_005A8520_MonKnockbackEnd@0x005A8520, fn:UNIT_AnimAtEnd@0x006217C0, run:2026-10-27-anim)
- **A player's knockback** (§ 4, H10, P1b-10). [C] 15 hits on a player with result bit `0x8`: 13 by Blood Raven in
  Hell (MonProp `knock`), 12 of which set the player to neutral (mode 1) in the hit's own frame and one later; 2 by
  class 462 started mode 19 (the knockback branch's rate `0xD5` and path speed `0x1000` at its 2 calls). After, `[I]`:
  why Blood Raven's knockback commands end in neutral at once (the planner's point equal to the start, or a refusal
  in the mode command) is not logged. (fn:COMBAT_GetHit@0x0057CEE0, fn:sub_0057F090_PlrModeStartMove@0x0057F090,
  run:2026-10-27-anim)
- **The get-hit roll** (§ 6.3) **raised.** [C] All 7 195 logged `GetHitRoll` calls return what § 6.3 gives, with
  0–2 `RangePow2` draws on the defender's seed (`ghr`: none 5 977, one 928, two 290): the early returns (freeze, poison only,
  below 256) 809, below `hp / D` 4 518, the two drawing bands 605 and 613, `hp / (D/4)` and above 650, `D` 16 (5 589) and 8 (774), the max HP the
  boundary; P1b-9: 64 get-hits in `[hp/16, hp/12)` and 332 refusals above `hp/12`. 102 consecutive pairs on one
  defender chain (the second's seed before is the first's after), 701 have other draws between. [I] The divisors 32 (19 calls) and
  64 (4) are met but not shown to separate from 16. (fn:sub_0057CB00_GetHitRoll@0x0057CB00, fn:RNG_RangePow2@0x00472210, run:2026-10-27-anim)
- **The block gate** (§ 6.1, P1b-11) **raised.** [C] For 867 blocked hits on a player the block command is issued
  exactly when `frame − stat 95 > ⌊stat 102 / 8⌋ + 15` (618 open, 249 shut), and of the 618 the mode test refused 51.
  (fn:COMBAT_GetHit@0x0057CEE0, run:2026-10-27-anim)
- **The mode tests** (§ 6.2). [C] 1 027 `PlrModeEndPending` values equal the frame of the kind-1 end queued when the
  request comes (`endpending-E`; one after a catalogue requeue not compared). 26 696 `PlayerModeAllowed` calls leave
  the player's seed unchanged (`pma-seed`): none under state 42, so the draw itself is not reached and stays `[I]`.
  Get-hit and block are never left before their end (anim/0001's P1b-1 tallies). [I] `PlrModeLeaveOk` returned 1 at
  all 5 633 first requests after an A1, cast, throw or kick start (`rv-req-*` of `2026-10-27-anim-check-review.txt`),
  so none of its refusals is reached and § 6.2 stays as above. (fn:sub_0057ED70_PlrModeEndPending@0x0057ED70,
  fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0, fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0, run:2026-10-27-anim)
- **The skill delay** (§ 5, P1b-12, D1 and D2). [C] With Frozen Orb held, 72 of the 73 next casts that start within
  3 frames of the delay state's end start exactly at the `SKILLS_SetDelayState` frame (the do's) plus `d`, one 3
  frames later: the delay runs from the do (D1), not after the whole cast (D2). (fn:SKILLS_SetDelayState@0x0056EF90,
  fn:SKILLS_SrvDo@0x0056F7F0, run:2026-10-27-anim)
- **Every-frame first run** (open question below): answered in [anim/0001's run section](0001-modes-frames.md#plan-0050-phase-2-run2026-10-27-anim)
  (`ef-first` 9 682), so the first step of a moving mode and the first knockback count run in the start's frame
  when it is queued before the type's every-frame list is walked. (fn:sub_005415E0_EventQueueEveryFrame@0x005415E0,
  run:2026-10-27-anim)
