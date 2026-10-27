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

None. No lead was used to locate or read this code, and [anim/leads](leads.md) was read only in its § 1 (sources and
versions) before filing ("leads not read before filing"; plan 0050, `lane/p50c` review ruling (b)). The movement,
hit-recovery, block and delay rows are decided against this finding in Phase 1b part 2.

## Functions

New names (subsystems `anim/movement` and `anim/timing`) and the existing ones this finding reads; all new rows are I.

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00554CA0` | `sub_00554CA0_UnitMoveStep` | revalidate the target, `PathStep(unit, 0x400)`, room update; 1 moving, 2 stopped (§ 2) | I (unchanged) |
| `0x00650840` | `sub_00650840_PathStep` | one frame of a path (§ 2) | I (unchanged) |
| `0x006502D0` | `sub_006502D0_PathVelocityStep` | acceleration and the step vector | C (skills/0002; unchanged) |
| `0x006503F0` | `sub_006503F0_PathStepTargetCheck` | still heading for the target? else replan (§ 2) | I |
| `0x00650090` | `sub_00650090_PathStepSnap` | clamp the step onto the next point when within it (§ 2) | I |
| `0x00650660` | `sub_00650660_PathStepMove` | the new position, the collision walk, the point index (§ 2) | I |
| `0x00650150` | `sub_00650150_PathStepCollide` | per crossed subtile the collision test, at most 10 (§ 2) | I |
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
| `0x0057ED70` | `sub_0057ED70_PlrModeEndPending` | `frame ≤ (first kind-1 event frame) + 5` | I |
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
`COMBAT_ApplyStun`, `sub_0064A5A0_MissileHitClass`.

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
  0x0058639A–0x005863B7, tbl:Objects.txt:Mode1, tbl:Objects.txt:HasCollision0)

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
  tbl:Objects.txt:HasCollision0, tbl:ItemStatCost.txt:Stat (stats 10, 67, 95, 102, 154, 164).
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
- [L] Whether an every-frame event queued during a frame's monster or player list run first runs in that frame or the
  next (`sub_005415E0_EventQueueEveryFrame` puts it at the list head; the walk order of § 6 of anim/0001 is not
  enough to say); it sets the first call of every moving mode and of the knockback count. Phase 2 logs it.
- [L] `sub_0057ED90_PlrSeqLeaveOk` past its first test (a used skill whose record byte `+0x16` is non-zero passes).
