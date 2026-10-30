# 0002 — Catalogue batch 1 (pool-A): the think functions of AI rows 2–16 and 142

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 1 (2 `Skeleton` … 16 `ClawViper`, 142 `ClawViperEx`), what does its
> think function do on an AI event: which `aip` slots and MonStats columns it reads, which AI-control words it keeps,
> which draws it makes on which seed and in which order, and which command, skill or path request it ends in?
> **Date:** 2026-10-30   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 1)   **Status:** for review (`lane/r52b`)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52b`, decompiled with scratch
`__fastcall` signatures for the AI helpers, `b1-sym-scratch.csv`; the signatures are a reading aid, not symbol rows)
and objdump (`b1-asm.txt`, the batch's range `0x005EFB80`–`0x005F20A0`), then emulation of ten of the sixteen think
functions under ADR-0015/ADR-0021 (§ 3, run:2026-10-30-ai-cat-emu-1). Kept outputs are under `workspace/logs/r52b/`
(manifest `manifest.sha256`, one path base: that directory; the emulation under `emu/`, its own manifest). Stock values
come from `b1-rows.txt` (`python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for the 16 rows,
125 records). The machinery these functions run inside (the AI event, the row kinds, the command and move helpers, the
path override) is [ai/0001](0001-machinery.md); names below are `re/symbols.csv` names.

**Notation used in every entry.** `G` the game, `U` the acting monster, `ctx` the `AiCtx` the AI event passes
([re/types/ai.h](../../../re/types/ai.h)): `t` = `ctx+0x08` (the target), `dist` = `ctx+0x14`, `melee` = `ctx+0x18`;
`ctl` = `ctx+0x00` (the `AiCtl`), `M` = `ctx+0x1C` (the MonStats record). `d` = `G+0x6D` (difficulty, u8). `aipK` =
the s16 at `M + 0x56 + 6(K−1) + 2d`. `draw` = one step of **the acting unit's seed** `U+0x20/+0x24` (`low·0x6AC690C5 +
high`), giving the new low word mod 100 (unsigned, `mul 0x51EB851F; shr 5`); `chance(K)` = `draw < aipK` as a signed
compare (`jge` past the taken branch). `Range(n)` = `RNG_Range(U seed, n)`, the same step and `low mod n`. The modes are
MonMode rows: 1 NU, 2 WL, 4 A1, 5 A2, 9 S2, 14 SQ, 15 RN. `SetModeAtUnit(m, t)` is `MonAiSetModeAtUnit`, `Idle(n)`
`MonAiIdle`, `Walk(t, f)` `MonAiWalkToUnit`, `Ring(r)` `MonAiWanderRing`, `T56(t, b, f)` `MonAiWalkToUnitType56`,
`StepAway(t, n, f)` `MonAiStepAway`, `Ovr(type, param, byte)` `MonAiPathOverride(U, type; param, byte)`.

## Answer (summary)

- [I] **The batch.** Sixteen think functions, each `(ECX game, EDX unit; ctx)` with `ret 4`, one per row; row 15
  `SandMaggot` also has an `alt` (0x005F1750); no row has an `init`. Every row but 15 is row kind 1 (the think function
  runs only with a target), row 15 kind 4 (only with a target, else the event 20 frames on) (`ai-rows.txt` of P1.1).
  So inside these functions `t` is never null; the `t == 0` tests of rows 13 and 15 are not reached from the row.
  (data:g_MonAiTable@0x0073CA18, fn:sub_005B1650_MonAiTargetByKind@0x005B1650)
- [I] **The common shape.** In melee range (`melee ≠ 0`) one or two `chance` draws choose an attack (`aip3` to
  attack, then `aip4` between A1 and A2, in most rows); out of it one draw chooses an approach (`Walk`, a run, a
  drawn-type walk, a ring point) or a wait (`Idle(aip2)` or `Idle(aip5)`). Rows 2, 9 and 12 are only that; the others
  add a life test (4, 7, 8, 11, 15), a distance test (every row but 2, 7, 9 and 12), the `MonsterData+0x54` test (3, 4, 6, 11,
  14), group records (6, 13, 14) or skills (8, 13, 15, 16, 142). Rows 5, 6, 8, 11, 15, 16 and 142 keep state in
  `AiCtl+0x14/+0x18/+0x1C` between events (a swoop flag, a think counter, a flight timer, a cooldown frame, a lay
  count, a charge mark). (§ 2, fn:sub_005EFCF0_AiSkeleton@0x005EFCF0, fn:sub_005F0700_AiSandRaider@0x005F0700,
  fn:sub_005F0CD0_AiBaboon@0x005F0CD0, struct:AiCtl+0x14)
- [C] **The decision maps of ten functions** (rows 2, 3, 4, 5, 7, 9, 12, 14, 16, 142), from their declared inputs
  (difficulty, frame, the unit seed, `ctx`, the `aip` block, `Skill1`, `AiCtl+0x14/+0x18/+0x20`, `MonsterData+0x54`,
  the target's position) to the first callee they reach, match the emulation in all 2 400 cases: the callee, its call
  site, its register and stack arguments, the unit seed at the call and (row 5) `AiCtl+0x14`; the `<=` and Normal-column
  controls and the site control fail every case they separate (`bighead`, with no draw before its two
  boundaries, has none for the first two). The `[C]` ends at that callee (ADR-0021): the commands
  themselves, and every branch a callee's result decides, stay `[I]`. (run:2026-10-30-ai-cat-emu-1, § 3)
- [I] **Draws.** Every draw of the sixteen functions is on the acting unit's seed; each function draws 0–6 times
  before its command (6 for row 13, § 2.11), in the order of § 2's pseudocode. Draws on other seeds come only from callees: `MonAiFindHostile`
  (rows 4, 13, 15: the forced-target confusion draw and the state-146 candidate test, ai/0001 § 6), and the move
  helpers (`Ring` 4 steps, `T56` 1 step, `MonAiMove`'s refusal with flag 2). No function of the batch loops over units
  with a draw (P1.1 review, reopen condition (b)): the three unit walks (rows 6, 8, 13) draw nothing per unit. (§ 2, fn:sub_005F06B0_AiNearAllyCb@0x005F06B0,
  fn:sub_005F1380_AiFallenCorpseCb@0x005F1380, fn:sub_005DCDA0_AiDeadMinionCb@0x005DCDA0, fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)
- [I] **Group messages.** Rows 6 `Fallen` and 13 `FallenShaman` post a record of kind 1 to the minions of their owner
  group (`MonHelpBlock`, the `AiCtl+0x20` parameter list); a `Fallen` whose head record has kind 1 attacks or walks to
  its target, a `QuillRat` with any head record attacks with A2 when the record's unit exists. A `Fallen` near a monster
  that is dying (mode 0) in a near room, found through the room's ring of the last four dead monsters (`Room+0x38`,
  written by `MonDeathEvent`), steps 12 away and, on 1 draw in 20, sets unit event 17. (§§ 2.5, 2.12, 4; fn:sub_005F02C0_AiFallen@0x005F02C0,
  fn:sub_005F1140_AiQuillRat@0x005F1140, fn:sub_0058F730_MonHelpBlock@0x0058F730, fn:sub_0061AFA0_RoomRecordDeath@0x0061AFA0)
- [I] **Skills.** Row 8 uses `Skill1` (Fire Hit) once its think counter passes `aip5`; row 13 `Skill1` (Resurrect, in
  mode 14 through `MonAiUseSeqSkill`) on a dead minion and `Skill2` (the shaman's missile) at `t` or at a hostile;
  row 15 `Skill1..3` (MagottUp, MagottDown, MagottLay) with a frame cooldown `aip5` and a lay count `aip3`; rows 16 and
  142 `Skill1` (SerpentCharge, Charge) after `MonSkillTargetOk`, setting state 90 or 91 by `aip6`. (§ 2, fn:sub_005F0700_AiSandRaider@0x005F0700,
  fn:sub_005F1440_AiFallenShaman@0x005F1440, fn:sub_005F1800_AiSandMaggot@0x005F1800, fn:sub_005F1B60_AiClawViper@0x005F1B60,
  fn:sub_005F1DE0_AiClawViperEx@0x005F1DE0, fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0, tbl:MonStats.txt:Skill1)

## Leads used

None. No community document was read; every claim is read from the code. P1.1's machinery (ai/0001) is cited by its
anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005EFCF0` | `sub_005EFCF0_AiSkeleton` | row 2 `Skeleton` think | I (map `[C]`, § 3) |
| `0x005EFE20` | `sub_005EFE20_AiZombie` | row 3 `Zombie` think | I (map `[C]`, § 3) |
| `0x005EFF50` | `sub_005EFF50_AiBighead` | row 4 `Bighead` think | I (map `[C]`, § 3) |
| `0x005F00E0` | `sub_005F00E0_AiBloodHawk` | row 5 `BloodHawk` think | I (map `[C]`, § 3) |
| `0x005F02C0` | `sub_005F02C0_AiFallen` | row 6 `Fallen` think | I |
| `0x005EFB80` | `sub_005EFB80_AiBrute` | row 7 `Brute` think | I (map `[C]`, § 3) |
| `0x005F0700` | `sub_005F0700_AiSandRaider` | row 8 `SandRaider` think | I |
| `0x005F06B0` | `sub_005F06B0_AiNearAllyCb` | row 8's search callback: the nearest other alignment-0 living monster | I |
| `0x005F0A20` | `sub_005F0A20_AiWraith` | row 9 `Wraith` think | I (map `[C]`, § 3) |
| `0x005F0B00` | `sub_005F0B00_AiCorruptRogue` | row 10 `CorruptRogue` think | I |
| `0x005F0CD0` | `sub_005F0CD0_AiBaboon` | row 11 `Baboon` think | I |
| `0x005F12A0` | `sub_005F12A0_AiGoatman` | row 12 `Goatman` think | I (map `[C]`, § 3) |
| `0x005F1440` | `sub_005F1440_AiFallenShaman` | row 13 `FallenShaman` think | I |
| `0x005F1380` | `sub_005F1380_AiFallenCorpseCb` | row 13's search callback (a unique shaman): a dead Fallen or shaman in range | I |
| `0x005F1140` | `sub_005F1140_AiQuillRat` | row 14 `QuillRat` think | I (map `[C]`, § 3) |
| `0x005F1800` | `sub_005F1800_AiSandMaggot` | row 15 `SandMaggot` think | I |
| `0x005F1750` | `sub_005F1750_AiSandMaggotAlt` | row 15's `alt`: a kind-14 skill shot, or re-init | I |
| `0x005F1B60` | `sub_005F1B60_AiClawViper` | row 16 `ClawViper` think | I (map `[C]`, § 3) |
| `0x005F1DE0` | `sub_005F1DE0_AiClawViperEx` | row 142 `ClawViperEx` think | I (map `[C]`, § 3) |
| `0x005DE6D0` | `sub_005DE6D0_MonAiWalkTowardUnit` | `(t, max, ring)`: `MonAiMoveToUnitDist(t, 2, max, ring)` | I |
| `0x005DE4E0` | `sub_005DE4E0_MonAiMoveToUnitDist` | a point at most `max` toward (or away from) a ring of radius `ring` around `t`, then the mode | I |
| `0x005DEFB0` | `sub_005DEFB0_MonAiRunToUnitStop` | `(t, stop)`: `MonAiMove(t, 15, 0, 0, stop or 1, 0)` | I |
| `0x0058EC90` | `sub_0058EC90_AiParamsAlloc` | a zeroed 0x1C record linked before the head of `AiCtl+0x20` (`.\Ai\AiGeneral.cpp`) | I |
| `0x0058EF40` | `sub_0058EF40_AiParamsPush` | a record with the five words `+0x08..+0x18` of a block, made the head | I |
| `0x0058EE80` | `sub_0058EE80_AiParamsHead` | `AiCtl+0x20`, the head record (0 without one) | I |
| `0x0058ED10` | `sub_0058ED10_AiParamsPop` | unlink and free the head record | I |
| `0x0058EEF0` | `sub_0058EEF0_AiParamsFind` | `(unit, kind; makeHead)`: the record with `+0x08 = kind` | I |
| `0x005B0BD0` | `sub_005B0BD0_UnitDistSq` | `dx² + dy²` of two units' positions | I |
| `0x005DCDA0` | `sub_005DCDA0_AiDeadMinionCb` | search kind 9's callback: a dead monster of the searcher's group in range | I |
| `0x0061AFA0` | `sub_0061AFA0_RoomRecordDeath` | `Room+0x38 + 4·Room+0x14 ← guid`, index `+1 & 3` | I |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`ai-rows.txt` of P1.1, `b1-rows.txt`): 2 `Skeleton` (9 records: `skeleton1..8`, `hellbovine`), 3
  `Zombie` (5), 4 `Bighead` (10), 5 `BloodHawk` (8, `foulcrow1..8`), 6 `Fallen` (8), 7 `Brute` (9, with `snowyeti1..4`),
  8 `SandRaider` (10), 9 `Wraith` (9), 10 `CorruptRogue` (6), 11 `Baboon` (8), 12 `Goatman` (10), 13 `FallenShaman` (8),
  14 `QuillRat` (8), 15 `SandMaggot` (7), 16 `ClawViper` (5), 142 `ClawViperEx` (5, `clawviper6..10`): 125 records.
  (tbl:MonStats.txt:AI)
- [I] Of the 13 rows whose records disagree on which slots they set (MonStats § AI columns), three are in this batch;
  the code reads each record's own slots, with these effects (the values `[C]` as data, `b1-rows.txt`): row 8, `aip6` 1 (`sandraider2`, 4, 7, 9) or 0 (the six
  others), which picks state 90 and overlay 150 against state 91 and overlay 46 (§ 2.7); row 11, `aip4` 0 in
  `baboon1` (15–50 in the others), so `baboon1`'s melee A1/A2 draw always gives A2; row 142, `aip6` 0
  (`clawviper8`), 1 or 2 (`clawviper10`), which picks no state, state 90 or state 91 (§ 2.15). (tbl:MonStats.txt:aip4,
  tbl:MonStats.txt:aip6)

### 2. The think functions

#### 2.1 Row 2 `Skeleton` (0x005EFCF0) and row 12 `Goatman` (0x005F12A0)

```c
// fn:sub_005EFCF0_AiSkeleton@0x005EFCF0, fn:sub_005F12A0_AiGoatman@0x005F12A0
if (!melee) { if (chance(1)) return Walk(t, 7); }                 // draw#1
else if (chance(3)) {                                             // draw#1
    if (Skeleton) return SetModeAtUnit(chance(4) ? 4 : 5, t);     // draw#2: A1 or A2
    return SetModeAtUnit(4, t);                                   // Goatman: A1 only
}
Idle(aip2);
```

- [I] One draw out of melee range (approach on `aip1`), one or two in it (attack on `aip3`; Skeleton then A1 on `aip4`,
  else A2). Walk's flags 7 = cancel the AI event (4), `AiCtl` bit 0 (1) and the ring fallback with its draws (2) on
  refusal (ai/0001 § 7). `Idle(aip2)` is the wait when no draw chose an action. (0x005EFCF0–0x005EFE11,
  0x005F12A0–0x005F1368, tbl:MonStats.txt:aip1)

#### 2.2 Row 3 `Zombie` (0x005EFE20)

```c
if (melee) return SetModeAtUnit(chance(4) ? 4 : 5, t);           // draw#1
if (!AiMonState3or19(U)) {                                       // MonsterData+0x54 not 3 or 19
    if (!(dist < aip2 && chance(1))) {                           // draw#1 only when dist < aip2
        if (RoomGetLevelId(UnitGetRoom(U)) != 17) return Ring(3);
    }
}
Ovr(0, 100, 0); RunToUnit(t);
```

- [I] So a zombie runs at its target (override parameter 100) when `MonsterData+0x54` is 3 or 19, when it is nearer
  than `aip2` and draws below `aip1`, or anywhere in level 17 (Levels `Id` 17, `Act 1 - Graveyard`); otherwise it wanders
  to a ring point of radius 3. The `[C]` of § 3 ends at `UnitGetRoom` on the level branch; the level test is a reading.
  (0x005EFE20–0x005EFF47, fn:sub_0061A1B0_RoomGetLevelId@0x0061A1B0, tbl:Levels.txt:Id)

#### 2.3 Row 4 `Bighead` (0x005EFF50)

```c
if (!melee && AiMonState3or19(U)) return SetModeAtUnit(5, t);
life = AiLifePct(U);
if (life >= aip1) {
    if (melee) return SetModeAtUnit(4, t);
    if (dist < 15 && FindHostile(&dist, &m) && Range(100) < aip3) return SetModeAtUnit(5, t);   // draw#1
    return Walk(t, 7);
}
if (dist < 3)  { Ovr(0, 50, 0); if (!StepAway(t, 5, 1)) SetModeAtUnit(5, t); return; }
if (dist > 15) return WalkToUnitStop(t, 6);
if (FindHostile(&dist, &m) && Range(100) < aip4) return SetModeAtUnit(5, t);                     // draw#1
if (Range(100) < aip2) return T56(t, 3, 0); else return Idle(10);                                // draw#1 or #2
```

- [I] The A2 command is aimed at `t` even when the hostile that `FindHostile` (search kind 6, ai/0001 § 6) found is
  another unit. The `dist` tests after a `FindHostile` read the distance from
  `ctx`, taken before the call. Below `aip1` percent life the bighead keeps 3–15 from its target. (0x005EFF50–0x005F00CC,
  fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_005DD280_AiLifePct@0x005DD280)
- [C] The map up to `AiLifePct` or the `MonsterData+0x54` shortcut (two boundaries, no draw before them).
  (run:2026-10-30-ai-cat-emu-1, `bighead`)

#### 2.4 Row 5 `BloodHawk` (0x005F00E0)

```c
if (ctl->var14 == 1 && melee) { ctl->var14 = 0; return SetModeAtUnit(4, t); }   // the swoop lands: A1
ctl->var14 = 0;
if (!melee) {
    if (chance(1)) { Ovr(0, aip5, dist); ctl->var14 = 1; return Walk(t, 0); }  // swoop: draw#1
    if (dist > 3) { if (chance(2)) { Ovr(0, -50, 0); return Ring(4); }        // draw#2
                    Ovr(0, 0, 0); return Ring(3); }
} else if (chance(3)) return SetModeAtUnit(4, t);                              // draw#1
Ovr(0, aip4, 0); if (!StepAway(t, 4, 1)) SetModeAtUnit(4, t);
```

- [I] `AiCtl+0x14` is the swoop flag: set after an approach walk with override parameter `aip5` (100 in every record)
  and the override byte `dist` (capped at 77 by `MonAiPathOverride`); the next event in melee range attacks at once.
  (0x005F00E0–0x005F02AB, struct:AiCtl+0x14)
- [C] The map, `AiCtl+0x14` at the boundary included. (run:2026-10-30-ai-cat-emu-1, `bloodhawk`)

#### 2.5 Row 6 `Fallen` (0x005F02C0)

```c
if (!U || U->mode == 0 || U->mode == 12) return;                 // dying or dead
UNIT_CancelEvents(G, U, 2, 0);                                   // drop the pending AI event
room = UnitGetRoom(U); if (!room) return;
for each room r of DUNGEON_GetNearRooms(room):
    for i in 0..3:                                               // r+0x38: the last four dead monsters
        m = GameFindUnit(G, 1, r->deadGuid[i]);
        if (m && m->mode == 0 && AiDistToPoint(m, U.x, U.y) < 15) {
            ctl->var14 = 1; AiParamsPop(U); Ovr(0, 50, 0);
            if (StepAway(ctx->target, 12, 1)) { if (draw % 20 == 0) UnitSetEvent(U, 17, 0); return; }  // draw#1 (mod 20)
            goto after_scan;                                     // the step was refused
        }
after_scan:
if (U->mode != 1) return Idle(10);                               // only from NU
rec = AiParamsHead(U);
if (!rec) {
    if (!melee && AiMonState3or19(U)) return Walk(t, 0);
    if (dist < 15 && MonsterOwner(U) == U && Range(100) < aip1) {        // a leader: draw#1
        blk.kind = 1; MonHelpBlock(U, &blk); AiParamsPush(U, &blk);       // post to the group and to itself
        return SetModeAtUnit(9, t);                                       // S2
    }
    if (!melee) { if (dist <= aip2) return Walk(t, 7);
                  if (Range(100) < 30) return Ring(3); return Idle(10); } // draw#1
    if (ctl->var14 || Range(100) < aip3) {                                // draw#1 only when var14 = 0
        ctl->var14 = 0; return SetModeAtUnit(Range(100) < aip4 ? 4 : 5, t);
    }
    if (Range(100) < 30) return SetModeAtUnit(9, t); return Idle(10);
}
if (rec->kind == 1) {
    if (!melee) { if (!Walk(t, 0)) AiParamsPop(U); return; }
    if (Range(100) >= aip3) return Idle(5);
    return SetModeAtUnit(Range(100) < aip4 ? 4 : 5, t);
}
AiParamsPop(U); Idle(10);
```

- [I] **The flight.** The scan runs before any mode test but after the dying test, over every near room's four
  `Room+0x38` guids (the ring `RoomRecordDeath` fills from `MonDeathEvent`, 0x005A704D, its only call), looking up a
  **monster** (`GameFindUnit` with `EDX` = 1) still in mode 0 (dying) within AI distance 15 of the fallen. On a hit it
  sets `AiCtl+0x14` (which makes its next melee choice skip the `aip3` draw), drops its head record and steps 12 away
  from `ctx->target` with override parameter 50; a refused step ends the scan. The draw here is `low mod 20`
  (`mul 0xCCCCCCCD; shr 4`), and `< 1` sets unit event 17 (`Unit+0x6E = 17`, `+0x70 = 0`, `Unit+0xC4 |= 0x400`;
  what the client shows for 17 is not read here). (0x005F02C0–0x005F0476, fn:sub_0061AFA0_RoomRecordDeath@0x0061AFA0,
  fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0, fn:sub_00553380_UnitSetEvent@0x00553380)
- [I] **The leader's call.** A fallen whose owner is itself (`MonsterOwner(U) == U`) and that is nearer than 15 posts,
  on `aip1`, a kind-1 record to every minion of its group (`MonHelpBlock`: its owner's `AiCtl+0x34` list, each gets a
  copy as its head) and to itself, and plays S2 at the target. The block is a stack block whose kind word (`+0x08`) is
  the only word written; the other four words the copies take (`+0x0C..+0x18`) are whatever the stack held
  (0x005F04AA–0x005F04D5). A fallen with a kind-1 head walks to its target (dropping the record if the walk is refused)
  or attacks; any other head record is dropped. (fn:sub_0058F730_MonHelpBlock@0x0058F730, fn:sub_0058EF40_AiParamsPush@0x0058EF40,
  fn:sub_0058F0D0_MonsterOwner@0x0058F0D0)
- [I] Draws: the scan's mod-20 draw only after a successful step; then at most three `Range(100)` (aip1 or 30, aip3,
  aip4). `UNIT_CancelEvents` runs on every event before the scan, so a path that only returns (a dying fallen, a
  successful step) queues nothing itself: the next AI event comes from the mode's end (ai/0001 § 2).
  (fn:sub_005F02C0_AiFallen@0x005F02C0, fn:UNIT_CancelEvents@0x00540E60)

#### 2.6 Row 7 `Brute` (0x005EFB80)

```c
if (!melee) { p = clamp(UnitLifePct(U), 40, 100); Ovr(0, 100 - p, 0); return WalkToUnitType13(t, 7); }
if (chance(3)) return SetModeAtUnit(chance(4) ? 4 : 5, t);       // draw#1, draw#2
if (chance(3)) return T56(t, 4, 0);                              // draw#2, aip3 again
Idle(15);
```

- [I] Out of melee range the brute walks at its target (type 13) with an override parameter of `100 − life%`, life
  clamped to 40..100: 0 at full life, 60 at 40 % and below. The second `aip3` draw is the same slot as the first.
  (0x005EFB80–0x005EFCE1, fn:sub_00621F20_UnitLifePct@0x00621F20)
- [C] The melee map; out of melee range up to `UnitLifePct`. (run:2026-10-30-ai-cat-emu-1, `brute`)

#### 2.7 Row 8 `SandRaider` (0x005F0700)

```c
if (ctl->var14 == 0) { STATE_Set(U, 90, 0); STATE_Set(U, 91, 0); ctl->var18 = 0; }
n = ++ctl->var14;
if (n == aip5) { UnitSetOverlayStat(U, aip6 == 1 ? 150 : 46, 0); return Idle(aidel[d] + 1); }
if (n > aip5)  { STATE_Set(U, aip6 == 1 ? 90 : 91, 1); ctl->var18 = 1; }           // armed
if (ctl->var1C < 7 && AiLifePct(U) < aip1) {
    best = { 0, 0x7FFFFFFF }; AiUnitSearch(G, U, &best, AiNearAllyCb, 1);
    if (best.unit) return Walk(best.unit, 0);
    ctl->var1C++;
}
if (dist > 4 && !ctl->var18 && chance(2)) return T56(t, 0, 0);                    // draw#1
if (!melee) { if (ctl->var18 || chance(4)) return Walk(t, 0); goto wait; }        // draw#1/#2
if (ctl->var18 == 1 && Skill1 >= 0) {
    MonAiUseSkill(Sk1mode, Skill1, t, 0, 0); ctl->var14 = 0; ctl->var18 = 0; return;   // Fire Hit
}
if (chance(3)) return SetModeAtUnit(Range(100) >= aip7 ? 4 : 5, t);
wait: k = max(24 - aip5, 6); if (ctl->var14 > aip5 + k) { ctl->var14 = 0; ctl->var18 = 0; }
Idle(15);
```

- [I] `AiCtl+0x14` counts the raider's AI events since its last Fire Hit; at `aip5` (18 … 4 by record and
  difficulty) it shows an overlay and waits `aidel[d] + 1` frames, past it it holds state 90 (`blue`) or 91 (`red`) by
  `aip6` and is armed (`+0x18 = 1`): the next event in melee range uses `Skill1` (Fire Hit) and starts the count again.
  An armed raider out of melee range walks without a draw. An unarmed one resets after `aip5 + max(24 − aip5, 6)`
  events. The A1/A2 draw is inverted against the others: `Range(100) ≥ aip7` gives A1 (`aip7` = 50 in every record).
  (0x005F0700–0x005F0A17, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode, tbl:MonStats.txt:aidel, tbl:States.txt:state)
- [I] Below `aip1` percent life (up to 7 tries, counted in `AiCtl+0x1C`, never reset by this function) it walks to the
  nearest other monster of alignment 0 that is not in a death mode, by squared distance (`AiNearAllyCb`: candidate ≠
  searcher, type 1, `UnitAlignGet` 0, `MonIsDeathMode` 0, `UnitDistSq` below the best; search kind 1 walks the near
  rooms' unit lists). No draw in the walk. (fn:sub_005F06B0_AiNearAllyCb@0x005F06B0, fn:sub_005B0BD0_UnitDistSq@0x005B0BD0,
  fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0)
- [I] The overlay is `UnitSetOverlayStat(unit, overlay, 0)` (skills/0005); the two values are rows 150 and 46 of
  Overlay.txt by their row index (not followed further here). (fn:sub_00621E40_UnitSetOverlayStat@0x00621E40)

#### 2.8 Row 9 `Wraith` (0x005F0A20)

```c
if (!melee) { if (chance(1)) return MonAiWalkTowardUnit(t, 12, 0); }   // draw#1
else if (chance(3)) return SetModeAtUnit(4, t);                        // draw#1
Idle(aip2);
```

- [I] `MonAiWalkTowardUnit(t, 12, 0)` walks at most 12 subtiles toward the target in mode 2 (§ 4). (0x005F0A20–0x005F0AEA)
- [C] The map. (run:2026-10-30-ai-cat-emu-1, `wraith`)

#### 2.9 Row 10 `CorruptRogue` (0x005F0B00)

```c
MonPlayerBonus(G, &pb, UnitGetRoom(U), U);                       // pb.difficulty: min(d, 2)
if (dist > 20 - 3 * pb.difficulty) { Ovr(13, aip4, 0); return MonAiRunToUnitStop(t, 3); }
if (melee) { if (chance(3)) return SetModeAtUnit(4, t); return Idle(aip2); }   // draw#1
if (!chance(1)) return Idle(aip2);                                              // draw#1
if (chance(5)) { Ovr(13, aip4, 0); return MonAiRunToUnitStop(t, 3); }           // draw#2
Walk(t, 7);
```

- [I] Beyond 20 / 17 / 14 (Normal / Nightmare / Hell) the rogue runs (mode 15, type 13, override parameter `aip4`, 100
  in every record) with stop distance 3; `MonPlayerBonus` is called for its difficulty word only (its `+0x0C`,
  `[ebp−0x18]` at 0x005F0B37; it also clamps `G+0x6D` to 2, monsters/0004 § 3). Nearer, it runs on `aip5` after an
  `aip1` draw. No skill: `corruptrogue3`'s `CountessFirewall` is not used by this function. (0x005F0B00–0x005F0CB8,
  fn:sub_00573930_MonPlayerBonus@0x00573930, fn:sub_005DEFB0_MonAiRunToUnitStop@0x005DEFB0)

#### 2.10 Row 11 `Baboon` (0x005F0CD0)

```c
life = UnitLifePct(U);
bonus = 0; if (Velocity >= 1 && (q = Run * 100 / Velocity) >= 100) bonus = min(q - 100, 120);   // MonStats +0x32, +0x34, signed
if (ctl->var14 == 0) {
    if (!melee) return WalkToUnitType13(t, 7);
    if (AiMonState3or19(U)) {
        if (life < aip1 && Range(100) < 50) {                                        // draw#1
            ctl->var14 = Range(5) + 2;                                               // draw#2: 2..6 events of flight
            s = STATS_GetUnitStat(U, 74, 0);
            ctl->var1C = s ? (aip5 * s) / 8 : 0; if (s) UnitSetStat(U, 74, s + ctl->var1C, 0);
            Ovr(2, bonus, 0); return StepAway(t, 15, 0);
        }
        if (ctl->var18 && Range(100) < 20) { T56(t, 3, 0); ctl->var18 = 0; return; }
    }
    if (ctl->var18 && !chance(3)) {                                                  // aip3 against
        if (Range(100) < aip2) { T56(t, 3, 0); ctl->var18 = 0; }
        return Idle(15);
    }
    ctl->var18 = 1; return SetModeAtUnit(chance(4) ? 4 : 5, t);
}
ctl->var14--; ctl->var18 = 0;                                                        // in flight
if (ctl->var14 == 0 || life > 75) UnitSetStat(U, 74, STATS_GetUnitStat(U, 74, 0) - ctl->var1C, 0);
if (!melee) { if (life > 75) { ctl->var14 = 0; Ovr(13, bonus, 0); return WalkToUnitType13(t, 7); } }
else if (draw < 33) return SetModeAtUnit(chance(4) ? 4 : 5, t);
if (dist > 23 && !AiMonState3or19(U)) { if (Range(100) < 33) T56(t, 4, 0); return Idle(20); }
Ovr(2, bonus, 0);
if (!StepAway(t, 15, 1)) { if (!melee) return Ring(5); return SetModeAtUnit(Range(100) < aip4 ? 4 : 5, t); }
```

- [I] **The flight**, only when `MonsterData+0x54` is 3 or 19: below `aip1` percent life, on a draw below 50, the
  baboon flees for `Range(5) + 2` events with its stat 74 (`hpregen`) raised by `aip5 · s / 8` (a signed 32-bit
  product, divided toward zero: `(x + (x >> 31 & 7)) >> 3`), stepping 15 away with path type 2 and the speed bonus; the
  raise is taken back when the count ends or life passes 75 %. The product wraps only for `|s| > 715 827 882` with the
  stock `aip5` ≤ 3 (`3 · 715 827 882 = 2 147 483 646` fits, `3 · 715 827 883` does not). The bonus is
  `Run · 100 / Velocity − 100`, 0..120 (0 for a `Velocity` below 1 or `Run < Velocity`). `AiCtl+0x18` marks "attacked
  last time": a baboon that attacked draws against `aip3` before attacking again. (0x005F0CD0–0x005F112E,
  tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run, fn:STATS_GetUnitStat@0x00625480, fn:sub_00627260_UnitSetStat@0x00627260)
- [I] Two life readers: this function reads `UnitLifePct` (0x00621F20) directly, rows 4, 8 and 15 read `AiLifePct`
  (0x005DD280); ai/0001 names both.

#### 2.11 Row 13 `FallenShaman` (0x005F1440)

```c
if (melee && chance(3)) return SetModeAtUnit(4, t);                                   // draw#1
srch = { 0, 0, 0, aip4 * aip4 };
if (!MonTypeFlag(U, 8) || MonTypeFlag(U, 4)) AiUnitSearch(G, U, &srch, 0, 9);         // own group's dead
else                                          AiUnitSearch(G, U, &srch, AiFallenCorpseCb, 1);   // a unique: near rooms
if (chance(1)) { blk.kind = 1; MonHelpBlock(U, &blk); }                               // post to the group
if (srch.unit && srch.count && chance(1) && MonSkillTargetOk(Skill1, srch.unit, 0, 0))
    return MonAiUseSeqSkill(Skill1, srch.unit, 0, 0);                                 // Resurrect, mode 14
if (t && dist < aip5 && chance(2)) return MonAiUseSkill(Sk2mode, Skill2, t, 0, 0);
h = FindHostile(&dist, 0);
if (h && dist < aip5 && chance(2)) return MonAiUseSkill(Sk2mode, Skill2, h, 0, 0);
if (chance(3)) return T56(t, 3, 0); else return Idle(10);
```

- [I] **Which dead.** A shaman that is not a unique, or is a champion (`MonTypeFlag` 8 clear or 4 set,
  `MonsterData+0x16`, monsters/0003), searches kind 9: its owner's group (`AiSearchOwnerGroup`), the table's callback
  `AiDeadMinionCb` taking a monster in mode 12 (dead) with `Unit+0xC4` bit `0x02`, no state of the DataTables `+0x150`
  set, owned by the searcher, at AI distance (`AiDistUnits`) ≤ `aip4²`. A unique shaman that is not a champion
  (Bishibosh's class) searches kind 1, the near rooms' units, with `AiFallenCorpseCb`: a monster whose `MonBaseId` is
  19 or 58 (`fallen1`, `fallenshaman1`), alignment 0, `Unit+0xC4` bit `0x02`, no state of `+0x150`, in mode 12, no state of
  `+0xD4`, squared distance (`UnitDistSq`) ≤ `aip4²`, and neither champion nor unique (`MonTypeFlag` `0x0C` clear).
  Both callbacks count the candidates and keep the last one taken (`+0x04` the count, `+0x00` the unit, `+0x08` its
  distance); the bound is `aip4²` in both, so the kind-9 bound compares an AI distance with a square
  (`aip4` = 24..30: 576..900). (0x005F14BC–0x005F150E, fn:sub_005DCDA0_AiDeadMinionCb@0x005DCDA0,
  fn:sub_005F1380_AiFallenCorpseCb@0x005F1380, fn:sub_005A0180_MonTypeFlag@0x005A0180, fn:sub_005DD050_AiSearchOwnerGroup@0x005DD050)
- [I] **Draw order:** melee `aip3`; the `aip1` call to the group (every event that gets this far, whether or not a
  corpse was found); the `aip1` resurrect draw (only with a corpse); then up to two `aip2` draws for the missile and
  one `aip3` for the approach. `FindHostile` adds its callees' draws (ai/0001 § 6). Resurrect is `Skill1` in mode 14
  without `Sk1mode` (`MonAiUseSeqSkill`); the missile is `Skill2` with `Sk2mode` (ShamanFire, ShamanIce or ShamanFireEx
  by record). (tbl:MonStats.txt:Skill2, fn:sub_005DE000_MonAiUseSeqSkill@0x005DE000, fn:sub_005FD470_MonSkillTargetOk@0x005FD470)

#### 2.12 Row 14 `QuillRat` (0x005F1140)

```c
if ((rec = AiParamsHead(U))) {
    if (GameFindUnit(G, rec->type /* +0x0C */, rec->guid /* +0x10 */)) { SetModeAtUnit(5, t); AiParamsPop(U); return; }
    AiParamsPop(U);
}
if (melee) return SetModeAtUnit(4, t);
if (AiMonState3or19(U)) return SetModeAtUnit(5, t);
if (dist < aip1) {
    if (chance(2)) return SetModeAtUnit(5, t);                        // draw#1
    if (StepAway(t, aip4 & 0xFF, 1)) return;
    if (dist < 4) return SetModeAtUnit(5, t);
}
Ring(aip4 < 3 ? 3 : aip4 & 0xFF);
```

- [I] A head record whose unit is found makes it shoot (A2) at its target once and drop the record; the record's
  kind is not tested. Within `aip1` it shoots on `aip2` or steps `aip4` away; beyond, it wanders to a ring point of
  radius `max(aip4, 3)` (signed word compare, `cmp word, 3; jge`). The ring argument is the target pointer's stack slot
  with its low byte replaced (`mov byte [ebp+8]`, 0x005F127B/0x005F1283), so its upper 24 bits are the target's;
  `MonAiWanderRing` uses `r & 0xFF` (ai/0001 § 7). (0x005F1140–0x005F1299)
- [C] The map, the ring argument's upper bits included (24 cases). (run:2026-10-30-ai-cat-emu-1, `quillrat`)

#### 2.13 Row 15 `SandMaggot` (think 0x005F1800, alt 0x005F1750)

```c
h = FindHostile(&hd, 0); ph = ctl->var14;                                   // ph: 1 up, 2 laying, 3 down
if (ph == 3 && ctl->var18 < G->frame && Skill1 >= 0) {                     // under ground, cooldown over
    MonAiUseSkill(Sk1mode, Skill1, t, 0, 0); MonAiDelayEarlier(25);
    ctl->var18 = G->frame + aip5; ctl->var14 = 1; return;                   // MagottUp
}
if (ph == 3) return MonAiDelayEarlier(20);
if (AiLifePct(U) < 25 && Skill2 >= 0 && hd < 7 && ctl->var18 < G->frame && Range(100) < 20) {
    MonAiUseSkill(Sk2mode, Skill2, t, 0, 0); MonAiDelayEarlier(30);
    ctl->var18 = G->frame + aip5; ctl->var14 = 3; return;                   // MagottDown
}
if (melee && chance(4)) return SetModeAtUnit(4, t);
if (h && hd < 15 && Range(100) < aip2) return SetModeAtUnit(5, h);
if (draw < 20) return T56(t, 6, 0);
if (ctl->var1C < aip3 && Range(100) < aip1) {
    if (ph != 2 || Skill3 < 0) { T56(t, 6, 0); ctl->var14 = 2; return; }
    ctl->var1C++; ctl->var14 = 1; MonAiUseSkill(Sk3mode, Skill3, t, 0, 0); return MonAiDelayEarlier(20);   // MagottLay
}
MonAiDelayEarlier(12);
```

- [I] The row is kind 4, so `t` is set; the function's branches for `t == 0` (a burrow with `Skill2` at no target when
  the hostile is absent or beyond 10, 0x005F1856–0x005F18A8) are not reached from the row. `hd` is the distance
  `FindHostile` returns (`0x7FFFFFFF` without a hostile). A maggot lays at most `aip3` (2, or 3–4 in Nightmare and Hell
  for `sandmaggot6`, 7) eggs over its life (`AiCtl+0x1C`, which the alt keeps), each after a walk that sets phase 2.
  The A2 shot is aimed at the hostile `h`, not at `t`. The AI event is re-queued by `MonAiDelayEarlier` after each
  skill and wait (it only moves the event earlier, ai/0001 § 2). (0x005F1800–0x005F1B48, tbl:MonStats.txt:Skill3,
  fn:sub_005DE130_MonAiDelayEarlier@0x005DE130)
- [I] **The alt** runs when `MonAiInit` is called for a maggot whose think function is already the row's (ai/0001 § 3):
  it takes (or makes) its parameter record of kind 14; if the record's `+0x18` is 1 and `Skill1 ≥ 0`, it uses `Skill1`
  at `UNIT_GetTargetUnit(G, U)`, delays 30 and clears it; otherwise it re-inits the AI with the current state
  (`MonAiInit(ctl, ctl->state)`, which clears `+0x14/+0x18`, frees the records and installs the row's think function),
  restores `AiCtl+0x1C` and delays 1. The kind-14 record is made by `AiCtlParamGet` with `+0x18 = 0`, and no writer of
  its `+0x18` was found: of `AiCtlParamGet`'s 15 calls only 0x005F175F passes 14, and the 20 direct calls of
  `AiParamsFind` outside it pass `EDX` 10, 4, 5, 7, 3 or a `[reg+0xa]` (five, the register unresolved)
  (`b1-paramget-pushes.txt`, `b1-paramfind-edx.txt`); direct `+0x18` stores into a record were not scanned. So the
  skill branch of the alt has no writer found here. (fn:sub_005F1750_AiSandMaggotAlt@0x005F1750,
  fn:sub_0058EFA0_AiCtlParamGet@0x0058EFA0, fn:sub_005B0E00_MonAiInit@0x005B0E00, fn:UNIT_GetTargetUnit@0x00553540)

#### 2.14 Row 16 `ClawViper` (0x005F1B60)

```c
if (ctl->var14 && aip6) STATE_Set(U, aip6 == 2 ? 91 : 90, 0);
if (melee) { if (!chance(3)) return Idle(aip5); return SetModeAtUnit(chance(4) ? 4 : 5, t); }
if (Skill1 >= 0 && dist < aip2 && chance(1) && MonSkillTargetOk(Skill1, t, t.x, t.y)) {
    MonAiUseSkill(Sk1mode, Skill1, t, 0, 0);                         // SerpentCharge
    if (aip6) STATE_Set(U, aip6 == 2 ? 91 : 90, 1);
    ctl->var14 = 1; return;
}
if (draw < 50) return Walk(t, 7); else return Idle(aip5);
```

- [I] `AiCtl+0x14` is set at the first charge and never cleared here, so from then on every event clears the state it
  set (when `aip6 ≠ 0`). `t.x, t.y` are the target's subtile position (`UnitGetSubX/Y`). (0x005F1B60–0x005F1DC9)
- [C] The map. (run:2026-10-30-ai-cat-emu-1, `viper`)

#### 2.15 Row 142 `ClawViperEx` (0x005F1DE0)

```c
if (ctl->var14 && aip6) STATE_Set(U, aip6 == 2 ? 91 : 90, 0);
if (melee) { if (chance(3)) return SetModeAtUnit(5, t); return Idle(aip5); }
if (dist < aip7 && chance(4)) {
    if (ctl->var18 < G->frame) { SetModeAtUnit(4, t); ctl->var18 = G->frame + aip8; return; }   // A1, cooldown aip8
    return Idle(aip5);
}
/* the row-16 charge and approach, as § 2.14 */
```

- [I] Unlike row 16, in melee range it uses A2 only; within `aip7` (18–28) it uses A1 at most once per `aip8` (50)
  frames. The charge is `Skill1` (Charge). (0x005F1DE0–0x005F2091, tbl:MonStats.txt:aip7, tbl:MonStats.txt:aip8)
- [C] The map up to the A1 command; the `+0x18` store after it is a reading only. (run:2026-10-30-ai-cat-emu-1, `viperex`)

### 3. Emulation (run:2026-10-30-ai-cat-emu-1)

- [C] Ten families, 240 cases each, 2 400 cases, all matching, none stopped, no traced access outside the declared
  memory (`emu/check.txt`). Each case runs one think function on a declared image (§ Notation; the target unit with a
  path for the two vipers) and ends at the first observed callee; the checker compares the callee, the call site
  (return address), `ECX`/`EDX` where the callee takes them, the stack arguments, the unit seed and, for `bloodhawk`,
  `AiCtl+0x14`. Callees run on the declared image rather than observed: `RNG_Range`, `AiMonState3or19` with
  `MonData54Get`, `AiParamsHead`, and the position getters `UnitGetSubX/Y` (with `PathGetX/Y`). Controls: `le` (each
  draw compared with `<=`) and `d0` (every `aip` from the Normal column) fail every case they separate, and the site
  control (each call site one byte later) fails every case (run:2026-10-30-ai-cat-emu-1):

  | family | row | boundaries reached | `le` separating | `d0` separating |
  |---|---:|---|---:|---:|
  | `skeleton` | 2 | 4 | 31 | 128 |
  | `zombie` | 3 | 4 | 26 | 50 |
  | `bighead` | 4 | 2 | 0 | 0 |
  | `bloodhawk` | 5 | 6 | 34 | 106 |
  | `brute` | 7 | 5 | 29 | 37 |
  | `wraith` | 9 | 3 | 38 | 119 |
  | `goatman` | 12 | 3 | 40 | 138 |
  | `quillrat` | 14 | 6 | 5 | 44 |
  | `viper` | 16 | 7 | 18 | 87 |
  | `viperex` | 142 | 8 | 28 | 114 |

  `bighead` reaches its two boundaries with no draw and no `aip` read, so no control separates it; its `[C]` is the
  map of the two tests (melee, `MonsterData+0x54`) only. Not covered: every callee and everything after it, so the
  commands, the move helpers' draws, the life and level tests, the `StepAway` results and the stores after a command.
  (run:2026-10-30-ai-cat-emu-1)
- [I] Not emulated: rows 6, 8, 10, 11, 13 and 15. Each reaches, before or between its decisions, a callee whose read
  set is not declarable in a small image (`UNIT_CancelEvents` and the near-room walk for row 6; the unit search for 8
  and 13; `MonPlayerBonus` and the room for 10; `UnitLifePct` first for 11; `MonAiFindHostile` first for 15), so an
  observed boundary there would end each case before its first draw. Phase 2's logs reproduce them (rows 6 and 13 are
  tier AIs). (fn:sub_005F02C0_AiFallen@0x005F02C0, fn:sub_005F1440_AiFallenShaman@0x005F1440)

### 4. The helpers first read here

- [I] **`MonAiMoveToUnitDist(ECX game, EDX unit; t, mode, max, ring)`** (0x005DE4E0; 4 calls, one the wrapper
  `MonAiWalkTowardUnit`, which passes mode 2, 15 calls): `D = AiDistUnits(U, t)`; `dir = −1` when `D < ring`, else +1;
  `n = min(|D − ring|, max)`; with `dx = |tx − ux|`, `dy = |ty − uy|`, `s = max(dx + dy, n)`: for `s > 0`, `ix = dx·n/s`,
  `iy = dy·n/s` (signed division) and, while `ix + iy < n`, both are incremented; the point `(ux + sgn(tx−ux)·ix·dir,
  uy + sgn(ty−uy)·iy·dir)`; then `MonCmdInit(U, mode)`, `PathSetStopDist(path, 1)`, the point into the command and
  `MonSetMode(…, 1)`. No draw. (fn:sub_005DE4E0_MonAiMoveToUnitDist@0x005DE4E0, fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0)
- [I] **`MonAiRunToUnitStop(ECX game, EDX unit; t, stop)`** (0x005DEFB0, 5 calls): `MonAiMove(t, 15, 0, 0, stop ? stop
  : 1, 0)` (the stop byte replaced by 1 when 0). (fn:sub_005DEFB0_MonAiRunToUnitStop@0x005DEFB0)
- [I] **The parameter list `AiCtl+0x20/+0x24`** (ai/0001 § 4): records of 0x1C bytes `{next, prev, kind, +0x0C,
  +0x10, +0x14, +0x18}` in a circular list, `+0x20` the head. `AiParamsAlloc(EDX unit)` links a zeroed record before
  the head (the first record becomes the head); `AiParamsPush(EDX unit; blk)` copies `blk+0x08..+0x18` into a new record
  and makes it the head; `AiParamsHead(ECX unit)` returns the head; `AiParamsPop(EDX unit)` unlinks and frees it;
  `AiParamsFind(ECX unit, EDX kind; makeHead)` returns the first record of that kind from the head and with `makeHead`
  makes it the head. `MonHelpBlock(EDX unit; blk)` pushes a copy to each minion of the unit's owner (§ 2.5). Callers:
  `AiParamsPush` 12, `MonHelpBlock` 10, `AiParamsPop` 14, `AiParamsHead` 10, `AiParamsFind` 22 (`b1-callers.txt`).
  (fn:sub_0058EC90_AiParamsAlloc@0x0058EC90, fn:sub_0058EF40_AiParamsPush@0x0058EF40, fn:sub_0058EE80_AiParamsHead@0x0058EE80,
  fn:sub_0058ED10_AiParamsPop@0x0058ED10, fn:sub_0058EEF0_AiParamsFind@0x0058EEF0)
- [I] **`UnitDistSq(ECX a, EDX b)`** (0x005B0BD0, 33 calls): `dx² + dy²` of the positions (path `+0x0C/+0x10` for unit
  types 2, 4, 5, else `PathGetX/Y`, 0 without a path), 32-bit signed `imul` and `add`: one square fits for
  `|dx| ≤ 46 340` (`46 340² = 2 147 395 600`) and wraps from 46 341 (`2 147 488 281`), and the sum wraps once
  `dx² + dy² ≥ 2³¹`; the wrapped value is compared signed by its callers (rows 8 and 13: a sum wrapped into the
  negative reads as near). Units in near rooms are far closer than that on stock maps, so no stock path reaches it (`[I]`). **`RoomRecordDeath(room, guid)`** (0x0061AFA0, its one
  call 0x005A704D in `MonDeathEvent`): `Room+0x38 + 4·(u8 Room+0x14) ← guid`, then `Room+0x14 ← (Room+0x14 + 1) & 3`.
  (fn:sub_005B0BD0_UnitDistSq@0x005B0BD0, fn:sub_0061AFA0_RoomRecordDeath@0x0061AFA0)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip8 (`+0x56 + 6(k−1) + 2d`), tbl:MonStats.txt:aidel (`+0x4F + d`, row 8),
  tbl:MonStats.txt:Skill1 (`+0x170`), tbl:MonStats.txt:Skill2 (`+0x172`), tbl:MonStats.txt:Skill3 (`+0x174`),
  tbl:MonStats.txt:Sk1mode (`+0x180`, `+0x181`, `+0x182`), tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run (row 11),
  tbl:Levels.txt:Id (17, row 3).
- struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtl+0x20, struct:AiCtx+0x14, struct:AiCtx+0x18,
  struct:MonsterData+0x16, struct:MonsterData+0x54, struct:DungeonRoomLife+0x14, struct:DungeonRoomLife+0x38, struct:Unit+0x10,
  struct:Unit+0x6E, struct:Unit+0xC4, struct:Game+0x6D, struct:Game+0xA8.

## Dead ends

- Ghidra with no signatures drops the `ECX`/`EDX` of every AI helper call (the helpers are `__fastcall` with stack
  arguments); the decompile was redone with scratch signatures (`b1-sym-scratch.csv`), and every register argument
  quoted above was read from objdump.

## Open questions

- Who sets the kind-14 record's `+0x18` that row 15's alt tests (§ 2.13): a direct store into a record found by a list
  walk was not scanned. A `writes 0x18` scan restricted to functions that walk `AiCtl+0x20`, or a P2 log of the alt,
  settles it.
- What unit event 17 (row 6, § 2.5) shows on the client, and what `Unit+0xC4` bit `0x02` (both corpse callbacks)
  means: neither is read here.
- Who writes `MonsterData+0x54` (the 3-or-19 test, rows 3, 4, 6, 11, 14): still unnamed (ai/0001's open question).
- Which units are their own owner (`MonsterOwner(U) == U`, row 6's leader test): the writer of the self-link is not
  read here.
