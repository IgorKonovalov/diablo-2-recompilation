# 0005 — Catalogue batch 4 (pool-D): the think functions of AI rows 64–66, 68–80, 87 and 92

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 4 (64 `SkeletonMage` to the traps: 64–66, 68–80, 87, 92), what does
> its think function do on an AI event: which `aip` slots and MonStats columns it reads, which AI-control words it
> keeps, which draws it makes on which seed and in which order, and which command, skill or path request it ends in?
> **Date:** 2026-10-30   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 4)   **Status:** for review (`lane/r52e`)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52e`, symbols replayed from
`re/symbols.csv`, then decompiled with the scratch `__fastcall` signatures of batches 1–3 carried onto it,
`b4-sym-scratch.csv`, built by `b4-scratch.py`; a reading aid, not symbol rows) and objdump (`b4-asm.txt`: the batch's
one range `0x005F96C0`–`0x005FBB00`, which holds no function of another batch), then emulation of the eighteen think
functions and row 65's `alt` under ADR-0015/ADR-0021 (§ 3, run:2026-10-30-ai-cat-emu-4). Kept outputs are under
`workspace/logs/r52e/` (manifest `manifest.sha256`, one path base: that directory; the emulation under `emu/`, its
own manifest; the development run under `emu/dev-1/`, its own manifest and tool copy). Stock values come from
`b4-rows.txt` (`python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for the 18 rows, 90
records). Every register argument quoted below was read from objdump (`b4-asm.txt`); the multiplier sites and RNG
calls per function are counted by `b4-draws.py` (`b4-draws.txt`). The machinery (the AI event, the row kinds, the
command and move helpers, `MonAiInit`, the `alt` swap, the unit search and its kinds) is [ai/0001](0001-machinery.md),
the notation and the helpers first read in batches 1–3 are [ai/0002](0002-pool-a.md) § Notation and § 4,
[ai/0003](0003-pool-b.md) and [ai/0004](0004-pool-c.md); names below are `re/symbols.csv` names.

**Notation** as ai/0002–0004: `G`, `U`, `t` = `ctx+0x08`, `dist` = `ctx+0x14`, `melee` = `ctx+0x18`, `ctl` =
`ctx+0x00`, `M` = `ctx+0x1C`, `T` = `G+0xA8` (the frame), `d` = `G+0x6D`; `aipK` the s16 at `M + 0x56 + 6(K−1) + 2d`;
`SkillK` the s16 at `M + 0x170 + 2(K−1)`, `SkKmode` the byte at `M + 0x180 + (K−1)`; `draw` one inline step of the
acting unit's seed `U+0x20/+0x24`, mod 100; `chance(K)` = `draw < aipK` signed; `Range(n)` = `RNG_Range` on the unit's
seed (`low mod n`, 0 and no step for `n < 1`); `rchance(K)` = `Range(100) < aipK`. `ctl->v14`, `v18`, `v1C` are
`AiCtl+0x14/+0x18/+0x1C`. `U.x, U.y` the unit's subtile position. Helper short names as before: `SetModeAtUnit(m, t)`,
`SetMode(m, x, y)` (`MonAiSetMode`), `Idle(n)`, `Delay(n)`, `Walk(t, f)` (`MonAiWalkToUnit`), `Walk13(t, f)`
(`MonAiWalkToUnitType13`), `T56(t, b, f)`, `WalkStop(t, n)`, `StepAway(o, n, f)` (`MonAiStepAway`), `Ring(r)`
(`MonAiWanderRing`), `Near(u, n)` (`MonAiWanderNearUnit`), `MoveToPoint(x, y, n)`, `Ovr(type, param, byte)`
(`MonAiPathOverride(U, type; param, byte)`), `UseSkill(mode, skill, t, x, y)`, `SeqSkill(skill, t, x, y)`
(`MonAiUseSeqSkill`), `Search(blk, cb, kind)` (`AiUnitSearch(G, U; blk, cb, kind)`), `FindHostile(&d, 0)`,
`HasState(u, s)` (`UNIT_HasState`). Modes are MonMode rows: 0 DT, 4 A1, 5 A2, 10 S3, 11 S4, 12 DD.

## Answer (summary)

- [I] **The batch.** Eighteen think functions, each `(ECX game, EDX unit; ctx)` with `ret 4`, one per row, laid out
  in row order in `0x005F96C0`–`0x005FBAF4` with the trap rows 87 and 92 last (92 before 87); row 65 `FetishShaman` has
  an `alt` (0x005F9950). Five helpers sit between them: three unit-search callbacks (rows 65, 71, 74) and two private
  helpers (row 68's spawn-skill placer 0x005F9E30, the trap arrows' kind 0x005FB650). Row 66 is kind 0 (the think
  function runs with no search), 77 and 80 kind 2 (they run without a target too), the other sixteen kind 1 (only with
  a target; ai/0001 § 4). No row has an `init`. (data:g_MonAiTable@0x0073CA18,
  fn:sub_005B1650_MonAiTargetByKind@0x005B1650, `ai-rows.txt` of P1.1)
- [I] **The shapes.** The melee rows (69 `VileDog`, 72 `DoomKnight`, 87 `Trap-Melee`) draw once to attack or once to
  approach; 75 `QuillMother` the same after a state test that posts a group call. The casters keep a distance or a
  timer: 64 `SkeletonMage` aims at its own hostile from `FindHostile` (approach, step away, attack, each on a draw), 70
  `FingerMage` runs a flee state in `AiCtl+0x14/+0x18` on its own life, 73 `AbyssKnight` casts `Skill2` on its own life
  and `Skill1` on a cooldown in `AiCtl+0x14`, 74 `OblivionKnight` keeps near a `doomknight1` and casts four skills, two
  of them on a frame timer in `AiCtl+0x14`. The spawners count: 66 `SandMaggotQueen` lays `aip1` young in three-event
  cycles (`AiCtl+0x14/+0x18/+0x1C`), 68 `VileMother` places `Skill1` toward the target while fewer than `aip2` of its
  children are within 25, 76 `EvilHole` spawns every `aip2` frames from a stock of `aip1` and keeps its own mode cycle
  (S3, S4); 71 `Regurgitator` walks to a dead monster, eats it with `Skill1` and steps away, a five-state machine in
  `AiCtl+0x14..+0x1C`. 65 `FetishShaman` breathes `Skill1` inside the skill's level as a distance and revives the
  nearest dead fetish with `Skill3`. The traps: 77, 80 and 92 shoot `aip2` times inside `aip1`, every second event,
  then die (`Unit+0xC4 |= 0x20000`, mode 0); 78 and 79 shoot along one axis on a frame timer with a kind chosen once
  per level region. (§ 2, fn:sub_005F96C0_AiSkeletonMage@0x005F96C0, fn:sub_005FA710_AiRegurgitator@0x005FA710,
  fn:sub_005FB410_AiEvilHole@0x005FB410, fn:sub_005FB6C0_AiTrapRightArrow@0x005FB6C0)
- [C] **The decision maps of thirteen functions** (rows 66, 69, 71, 72, 75, 76, 77, 78, 79, 80, 87, 92 and 65's
  think up to its skill-sign test) from their declared inputs to the first callee they reach (or, for row 66, the
  return) match the emulation in all 4 560 cases of nineteen families: the callee, its call site, its register and
  stack arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C`, `Unit+0xC4`, the trap region's `+0x2D4` word and, where
  the callee takes a pointer into the frame, the words it addresses. The six `entry` families (rows 64, 65's `alt`,
  68, 70, 73, 74) reach their first callee before any test: only that call's site and arguments are covered (and row
  74's search block). The `le`, `d0`, `cmp` and `r4` controls and the site control fail every case they separate. The
  `[C]` ends at that callee (ADR-0021). (run:2026-10-30-ai-cat-emu-4, § 3)
- [I] **Draws.** Every draw of the batch's functions is on the acting unit's seed: 24 multiplier-constant loads for
  26 inline steps (rows 69 and 72 load the constant once for two exclusive steps), 10 `RNG_Range` calls and one
  `RNG_RandLoHi` call (the trap arrows' kind, § 2.17), every one on `U+0x20` (`b4-draws.txt`; the `lea ecx,[r+0x20]`
  before each call, row 73's through `edi` = `lea [ebx+0x20]`, 0x005FABA9); no `RNG_RangeB`, no `RNG_RangePow2`. 0–5 per
  decision in the order of § 2's pseudocode. Draws on other seeds can come only from callees (`MonAiFindHostile` in
  rows 64 and 74, ai/0001 § 6; the move helpers as in ai/0001 § 7). No function of the batch loops over units with a
  draw (P1.1 review, reopen condition (b)): the three search callbacks have no multiplier site and no RNG call in
  their bodies (`b4-draws.txt`: `AiFetishReviveCb 0 0 0 0 7 0`, `AiRegurgitatorCb 0 0 0 0 5 0`,
  `AiOblivionKnightCb 0 0 0 0 6 0`), and none of their direct calls is an RNG entry; their callees are not followed.
  Row 68's placer loops over eight directions with no draw in its body (`AiVileMotherSpawn 0 0 0 0 13 0`).
  (§§ 2.3, 2.5, 2.8, 2.11)
- [I] **The trap arrows draw on the first trap of a region.** Rows 78 and 79 take their kind from the word `+0x2D4` of
  the level's monster region (`MonRegionGet(G+0xF0, level id)`): when it is below 0 the first trap to shoot sets it,
  to 0 in a level below 40 (acts I and II) and to `RNG_RandLoHi(U seed; 0, 3)` (0, 1 or 2) from level 40 up; kind 1
  uses `Skill1`, any other kind plays A1. Which code sets the word to −1 is not read. (§ 2.17,
  fn:sub_005FB650_AiTrapArrowKind@0x005FB650)
- [I] **Effects outside the unit.** Rows 77, 80 and 92 set `Unit+0xC4` bit `0x20000` and command mode 0 (DT) after
  their `aip2` shots or when the target leaves `aip1` (as the nests of ai/0004 § 2.7); rows 66 and 76 spawn monsters
  (`SpawnClassByBase` then `SpawnAtPos`, the spawn's `+0xC4 |= 0x4000000`; 76 also `0x20000`, and for class 711
  `demonhole` state 184 and overlay stat 202); row 65 posts kind-1 and kind-14 records to its group (`MonHelpBlock`),
  row 75 a kind-1 record; row 65's `alt` clears state 12. (§§ 2.2, 2.3, 2.4, 2.12, 2.13, 2.14, 2.18,
  fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0, fn:sub_005B2F20_SpawnAtPos@0x005B2F20,
  fn:sub_0058F730_MonHelpBlock@0x0058F730, fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0)
- [I] **The two group-call blocks disagree on their word order.** Row 65 writes the target's guid at the block's
  `+0x0C` and its type at `+0x10` (both of its blocks); row 75 writes the type at `+0x0C` and the guid at `+0x10`, the
  order row 14's reader takes (re/types/ai.h `AiParam`). One of the two is read wrongly by its consumer, or the
  consumers differ; not settled here. (0x005F9AE8–0x005F9B0E, 0x005F9C14–0x005F9C2C, 0x005FB2CA–0x005FB2EE; § 2.18)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batches 1–3 (ai/0001–0004) and the
findings named in place are cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005F96C0` | `sub_005F96C0_AiSkeletonMage` | row 64 `SkeletonMage` think | I (entry call `[C]`, § 3) |
| `0x005F9950` | `sub_005F9950_AiFetishShamanAlt` | row 65's `alt`: clear state 12, `MonAiInit`, `Idle(1)` | I (entry call `[C]`, § 3) |
| `0x005F99A0` | `sub_005F99A0_AiFetishReviveCb` | row 65's search callback: the nearest dead and the nearest living fetish | I |
| `0x005F9A80` | `sub_005F9A80_AiFetishShaman` | row 65 `FetishShaman` think | I (skill-sign test `[C]`, § 3) |
| `0x005F9CF0` | `sub_005F9CF0_AiSandMaggotQueen` | row 66 `SandMaggotQueen` think | I (map `[C]`, § 3) |
| `0x005F9E30` | `sub_005F9E30_AiVileMotherSpawn` | row 68's helper: `Skill1` at a free cell three steps toward the target | I |
| `0x005FA010` | `sub_005FA010_AiVileMother` | row 68 `VileMother` think | I (entry call `[C]`, § 3) |
| `0x005FA280` | `sub_005FA280_AiVileDog` | row 69 `VileDog` think | I (map `[C]`, § 3) |
| `0x005FA380` | `sub_005FA380_AiFingerMage` | row 70 `FingerMage` think | I (entry call `[C]`, § 3) |
| `0x005FA690` | `sub_005FA690_AiRegurgitatorCb` | row 71's search callback: the nearest dead monster with a MonStats2 flag | I |
| `0x005FA710` | `sub_005FA710_AiRegurgitator` | row 71 `Regurgitator` think | I (map `[C]`, § 3) |
| `0x005FAA90` | `sub_005FAA90_AiDoomKnight` | row 72 `DoomKnight` think | I (map `[C]`, § 3) |
| `0x005FAB80` | `sub_005FAB80_AiAbyssKnight` | row 73 `AbyssKnight` think | I (entry call `[C]`, § 3) |
| `0x005FAE40` | `sub_005FAE40_AiOblivionKnightCb` | row 74's search callback: the nearest `doomknight1` ally, and the nearest below 40 % life | I |
| `0x005FAF00` | `sub_005FAF00_AiOblivionKnight` | row 74 `OblivionKnight` think | I (entry call `[C]`, § 3) |
| `0x005FB2A0` | `sub_005FB2A0_AiQuillMother` | row 75 `QuillMother` think | I (map `[C]`, § 3) |
| `0x005FB410` | `sub_005FB410_AiEvilHole` | row 76 `EvilHole` think | I (map `[C]`, § 3) |
| `0x005FB5B0` | `sub_005FB5B0_AiTrapMissile` | row 77 `Trap-Missile` think | I (map `[C]`, § 3) |
| `0x005FB650` | `sub_005FB650_AiTrapArrowKind` | `(ECX game, EDX unit)`: the level region's trap-arrow kind, set once | I (map `[C]` inside rows 78, 79, § 3) |
| `0x005FB6C0` | `sub_005FB6C0_AiTrapRightArrow` | row 78 `Trap-RightArrow` think | I (map `[C]`, § 3) |
| `0x005FB7E0` | `sub_005FB7E0_AiTrapLeftArrow` | row 79 `Trap-LeftArrow` think | I (map `[C]`, § 3) |
| `0x005FB900` | `sub_005FB900_AiTrapPoison` | row 80 `Trap-Poison` think | I (map `[C]`, § 3) |
| `0x005FB9B0` | `sub_005FB9B0_AiTrapNova` | row 92 `Trap-Nova` think | I (map `[C]`, § 3) |
| `0x005FBA60` | `sub_005FBA60_AiTrapMelee` | row 87 `Trap-Melee` think | I (map `[C]`, § 3) |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`ai-rows.txt` of P1.1, `b4-rows.txt`): 64 `SkeletonMage` (27 records), 65 `FetishShaman` (8), 66
  `SandMaggotQueen` (5), 68 `VileMother` (5), 69 `VileDog` (10: `vilechild1..5`, `painworm1..5`), 70 `FingerMage` (5),
  71 `Regurgitator` (4), 72 `DoomKnight` (3: `doomknight1`, `dkfig1..2`), 73 `AbyssKnight` (1, `doomknight2`), 74
  `OblivionKnight` (4: `doomknight3`, `dkmag1..3`), 75 `QuillMother` (5, `quillbear1..5`), 76 `EvilHole` (6:
  `evilhole1..5`, `demonhole`), 77 `Trap-Missile` (2), 78, 79, 80, 87, 92 (1 each): 90 records. (tbl:MonStats.txt:AI)
- [I] None of the 13 rows whose records disagree on which `aip` slots they set (MonStats § AI columns) is in this batch;
  the records differ in values only (values `[C]` as data, `b4-rows.txt`). Those a reader needs: row 64's `aip2` (the
  approach distance and the walk-stop) is 9/10/11 in 19 records and 15/18/20 in the eight records 620–624 and 727–729
  (`skmage_fire5`, `fire6`, `ltng5`, `ltng6`, `cold5`, `fire7`, `ltng7`, `cold6`), its `aip6` (the attack distance) 18/17/16 against 15/18/20 in the same eight; row 65's `aip2`
  (the revive filter, § 2.3) 0/1/2 to 0/2/3 and `aip3` 15/16/18 to 15/18/22; row 66's `aip1` (the brood size) 7/8/9 in
  `maggotqueen1` up to 11/12/13 in 5, `aip2` (the delay) 12 down to 4; row 70's `aip1`..`aip4` rise from
  `fingermage1` to 3; row 71's `aip1`, `aip3` and `aip5` from `regurgitator1` to 3; row 76's `demonhole` has `aip1`
  3 and `aip2` 25 where `evilhole1..5` have 10 and 50. Row 74's four records share every value. Row 77's
  `aip1`..`aip3` are 25/30/32, 1, 15 (one shot inside 25–32, then death), 78's and 79's 5, 15, 30/23/18, 200.
  (tbl:MonStats.txt:aip1, tbl:MonStats.txt:aip2, tbl:MonStats.txt:aip6)
- [I] Row 64's records carry `SkeletonRaise` as Skill1 and the think function reads no skill column (§ 2.1); row 72's
  records have no skills; row 76's `Nest` (Skill1) is not read by its think function (it spawns through
  `SpawnClassByBase`, § 2.16). (0x005F96C0–0x005F9948, 0x005FAA90–0x005FAB74, 0x005FB410–0x005FB59E,
  tbl:MonStats.txt:Skill1)

### 2. The think functions

#### 2.1 Row 64 `SkeletonMage` (0x005F96C0)

```c
d = dist; h = FindHostile(&d, 0);                     // d is the frame word EBP+8; FindHostile may rewrite it
if (h) {
    if (d > aip2 && chance(3)) { Ovr(0, 10, 0); return WalkStop(h, (u8)aip2); }      // draw#1
    if (d <= aip4 && chance(5)) { Ovr(0, 25, 0); if (StepAway(h, 5, 1)) return;
                                  return SetModeAtUnit(4, t); }                         // draw#1 or #2
    if (d < aip6 && chance(1)) return SetModeAtUnit(4, h);                             // draw#1..#3
}
if (d > aip2 && chance(3)) { Ovr(0, 10, 0); return WalkStop(t, (u8)aip2); }
if (chance(7)) return T56(t, 4, 0);
Idle(aip8);
```

- [I] The mage approaches the hostile it found to `aip2` (9–20) when farther, steps 5 away from it inside `aip4`
  (5/6/7) and attacks it inside `aip6`; failing those it does the same approach toward the event's target, then
  `T56(t, 4, 0)` on `aip7` (20) or idles `aip8` (5). A refused step away plays A1 at the event's target `t`, not at
  `h`. The walk-stop distance is the low byte of `aip2` (`movzx … BYTE PTR [ebx+eax*2+0x5c]`, 0x005F9755, 0x005F98BD);
  the compares use the full s16. At most five draws (three on the hostile branch, two after it). (0x005F96C0–0x005F9948,
  fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_005DEF80_MonAiWalkToUnitStop@0x005DEF80,
  fn:sub_005DEFE0_MonAiStepAway@0x005DEFE0)
- [C] The entry call: `FindHostile(G, U; EBP+8, 0)` from 0x005F96E9 with `dist` in the frame word it addresses, before
  any test. (run:2026-10-30-ai-cat-emu-4, `skmage`)

#### 2.2 Row 65's `alt` `FetishShamanAlt` (0x005F9950)

```c
if (HasState(U, 12)) STATE_Set(U, 12, 0);             // state 12 `inferno`
MonAiInit(ctl, ctl->state);
Idle(1);
```

- [I] Clears the `inferno` state the think function's breath tests (§ 2.3), re-inits the AI on its current state and
  idles one frame. States row 12 is `inferno` (`states.txt`). (0x005F9950–0x005F9999, fn:STATE_Set@0x00639DB0,
  fn:sub_005B0E00_MonAiInit@0x005B0E00)
- [C] The entry call `HasState(U, 12)` from 0x005F9965. (run:2026-10-30-ai-cat-emu-4, `fetishalt`)

#### 2.3 Row 65 `FetishShaman` (0x005F9A80) and its callback `AiFetishReviveCb` (0x005F99A0)

```c
n = 1;
if (Skill1 >= 0 && (s = SkillFindByOwner(U, Skill1; -1)) && (lv = SKILLS_GetSkillLevel(U, s, 1)) > 0) n = lv;
if (Skill1 >= 0 && dist < n && !HasState(U, 12)) {
    blk.kind = 1; blk.w0C = t ? t->guid : -1; blk.w10 = t ? t->type : 6; MonHelpBlock(U, &blk);
    return UseSkill(Sk1mode, Skill1, t, 0, 0);
}
if (HasState(U, 12)) STATE_Set(U, 12, 0);
s = { dead 0, deadD2 0x7FFFFFFF, r2 aip5*aip5, live 0, liveD2 0x7FFFFFFF, count 0, filter aip2 };
Search(&s, AiFetishReviveCb, 1);
if (s.dead && chance(1) && MonSkillTargetOk(U; Skill3, s.dead, 0, 0)) {              // draw#1
    blk.kind = 14; blk.w0C = s.dead->guid; blk.w10 = 1; MonHelpBlock(U, &blk);
    if (s.deadD2 > aip3) return Near(s.dead, 10);
    return SeqSkill(Skill3, s.dead, 0, 0);
}
if (chance(4)) return T56(t, 4, 0);                                                  // draw#1 or #2
Idle(10);
```

- [I] The breath (`FetishInferno`, Skill1) is used while the target is nearer than the skill's level (7–11 in Normal
  by the records' `Sk1lvl`, before any level bonus): the think function compares `dist` with
  `SKILLS_GetSkillLevel`'s return, 1 when the unit has no such skill or the level is below 1 (0x005F9AAB–0x005F9ADA).
  Each breath posts a kind-1 group record. Outside it, state 12 is cleared, and the shaman looks for a dead fetish
  within `aip5` (50): on `aip1` and when `MonSkillTargetOk` accepts `Skill3` (`Resurrect2`) on it, it posts a kind-14
  record naming the corpse and either walks near it (squared distance above `aip3`) or uses `Resurrect2` through
  `MonAiUseSeqSkill`; else `T56(t, 4, 0)` on `aip4` (66) or `Idle(10)`. `aip3` is compared with a **squared** distance
  (`cmp [ebp-0x4c], aip3`, 0x005F9C41: `deadD2` from the callback's `UnitDistSq`). (0x005F9A80–0x005F9CE6,
  fn:sub_006439B0_SkillFindByOwner@0x006439B0, fn:SKILLS_GetSkillLevel@0x006442A0,
  fn:sub_005FD470_MonSkillTargetOk@0x005FD470, fn:sub_0058F730_MonHelpBlock@0x0058F730,
  fn:sub_005DE000_MonAiUseSeqSkill@0x005DE000, fn:sub_005DF530_MonAiWanderNearUnit@0x005DF530)
- [I] **The callback** `(ECX game, EDX unit; cand, s)` takes a candidate that is not the unit, is a monster (type 1)
  with `Unit+0xC4` bit `0x02`, is not in state set 33 (`UnitHasStateSet33`), and, when `s.filter` (`aip2`) is 0, whose
  owner is the shaman (`MonsterOwner(cand) == U`); whose class by `MonClassCheck(MonBaseId(cand))` is 141
  (`fetish1`), or 396 (`fetishblow1`) unless the filter is 1; of alignment 0; for a filter below 3 not of the
  `MonTypeFlag(cand, 12)` type; and within `UnitDistSq ≤ s.r2`. A candidate in mode 12 (DD) replaces `s.dead` when
  strictly nearer; any other counts in `s.count` and replaces `s.live` when strictly nearer. It returns 0 (the
  search goes on). The think function reads only `s.dead` and `s.deadD2`. No draw (§ Answer, Draws).
  (0x005F99A0–0x005F9A74, fn:sub_0063A770_UnitHasStateSet33@0x0063A770, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0,
  fn:sub_00463900_MonClassCheck@0x00463900, fn:sub_005A0180_MonTypeFlag@0x005A0180,
  fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)
- [I] So the filter `aip2` widens with difficulty: 0 (Normal in every record) revives only the shaman's own minions,
  1 any `fetish1`-based dead, 2 also the `fetishblow1` base, 3 (Hell in `fetishshaman4..8`) drops the type test.
  (0x005F99E8–0x005F9A36, tbl:MonStats.txt:aip2)
- [C] The skill-sign test up to `SkillFindByOwner(U, Skill1; −1)` (0x005F9AB2) or, for `Skill1 < 0`, `HasState(U, 12)`
  (0x005F9B4B). (run:2026-10-30-ai-cat-emu-4, `fetish`)

#### 2.4 Row 66 `SandMaggotQueen` (0x005F9CF0)

```c
if (ctl->v1C) { Idle(25 * aip2); ctl->v1C = 0; return; }
if (ctl->v18 == 0) {
    if (ctl->v14 < aip1) { MoveToPoint(U.x, U.y, 8); Delay(aip2); ctl->v18 = 1; }
    return;                                                // the brood is complete: no command
}
SpawnClassByBase(U; &cls, &x, &y, &mode, 0, MonLinkClass3C);
if ((room = RoomAtSubtile(UnitGetRoom(U), x; y)) && (m = SpawnAtPos(G, room; x, y, cls, mode, 2, 0x42))) {
    m->+0xC4 |= 0x4000000; ctl->v14++;
}
Delay(aip2); ctl->v18 = 0; ctl->v1C = 1;
```

- [I] A three-event cycle while fewer than `aip1` (7–13) young were spawned: a `MoveToPoint` at its own position with
  8 and `Delay(aip2)`; then the spawn (class, point and mode from `SpawnClassByBase`, skills/0018) and `Delay(aip2)`;
  then `Idle(25 × aip2)` (s32 product). `AiCtl+0x14` counts successful spawns only; once it reaches `aip1` the
  function returns with no command at all. No draw. The row is kind 0: the function runs with no target search.
  (0x005F9CF0–0x005F9E1E, fn:sub_005DE440_MonAiMoveToPoint@0x005DE440, fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0,
  fn:sub_00463740_RoomAtSubtile@0x00463740, fn:sub_005B2F20_SpawnAtPos@0x005B2F20)
- [C] The map of `AiCtl+0x14/+0x18/+0x1C` to `Idle` (0x005F9D1D), `MoveToPoint` (0x005F9D5D, `U.x`, `U.y` read
  through `UnitGetSubX/Y`), `SpawnClassByBase` (0x005F9DA8, its seven stack arguments) or the return. The write of
  `ctl->v1C = 0` after the `Idle` and every write after a boundary are not covered. (run:2026-10-30-ai-cat-emu-4,
  `queen`)

#### 2.5 Row 68 `VileMother` (0x005FA010)

```c
pos = MONSTATS_GetClassChainPos(U ? U.class : -1, 0, 0);
child = MonClassChainStep(count > 301 ? 301 : -1, pos);  // ECX 301 `vilechild1` when the MonStats count passes it
if (ctl->v14 < aip1 && UnitAlignGet(U) == 0 && chance(3)) {                      // draw#1
    s = { child, 25, 0 }; Search(&s, 0, 12);             // kind 12: count the living `child` within 25 (ai/0001 § 6)
    if (s.count < aip2 && AiVileMotherSpawn(G, U; t, M)) { ctl->v14++; return; }
}
if (melee) { if (chance(4)) return SetModeAtUnit(4, t); return Idle(aip7); }      // draw#1 or #2
if (ctl->v14 < aip1 && draw >= aip5) {                                             // draw#1 or #2
    if (chance(6)) return T56(t, 4, 0);                                            // draw#2 or #3
    return Idle(15);
}
Walk(t, 7);
```

- [I] The mother places her `Nest` skill (`Skill1`) in up to `aip1` (16–22) events in all, each on `aip3` and only
  while fewer than `aip2` (5/6) of her chain's child class live within 25; her child class is the class at her own
  chain position in `vilechild1`'s chain (`MonClassChainStep`, monsters/0003). In melee she attacks on `aip4` (80–95)
  or idles `aip7`; outside it, while she still has spawns left, she `T56`s on `aip6` (30) after a draw at or above
  `aip5` (70/60/50), and walks to the target otherwise. The `ECX` of `MonClassChainStep` is
  `(count > 0x12D) ? 0x12D : −1` (`setg; sub 1; and 0xFFFFFED2; add 0x12D`, 0x005FA052–0x005FA06A). (0x005FA010–0x005FA270,
  fn:MONSTATS_GetClassChainPos@0x006510C0, fn:sub_0054DA60_MonClassChainStep@0x0054DA60,
  fn:sub_006259B0_UnitAlignGet@0x006259B0)
- [I] **The placer** `AiVileMotherSpawn(ECX game, EDX unit; t, M)` (0x005F9E30): the direction from the unit to the
  target (`UnitDirToPoint`, 64 steps) cut to eight (`Dir64To8`); for eight tries from that direction, the try's
  8-direction index `k & 7` maps through the stack table `{6, 4, 2, 2, 2, 0, 6, 6}` to a `DirOffset` direction, the
  cell is the unit's position plus three times that offset, and when `Skill1 ≥ 0` and `SpawnClassCellTest`
  (class `MONSTATS_ValidId(298)`, `vilemother1`) accepts the cell, `UseSkill(Sk1mode, Skill1, 0, x, y)` and return 1;
  after eight refusals, 0. No draw. (0x005F9E30–0x005FA007, fn:sub_00621DC0_UnitDirToPoint@0x00621DC0,
  fn:sub_0063E7A0_Dir64To8@0x0063E7A0, fn:sub_0063E7E0_DirOffset@0x0063E7E0, fn:MONSTATS_ValidId@0x004E6C50,
  fn:sub_005FD350_SpawnClassCellTest@0x005FD350)
- [C] The entry call `MONSTATS_GetClassChainPos(U.class, 0, 0)` from 0x005FA045, before any test.
  (run:2026-10-30-ai-cat-emu-4, `vmother`)

#### 2.6 Row 69 `VileDog` (0x005FA280)

```c
if (ctl->v14 == 0) { ctl->v14 = 1; return Idle(5); }      // the first event after the spawn
if (melee) { if (chance(1)) return SetModeAtUnit(4, t); return Idle(aip2); }      // draw#1
if (chance(3)) return Walk(t, 7);                                                // draw#1
Idle(10);
```

- [I] One idle of 5 on the first event, then one draw per event: A1 on `aip1` (80/85/90) in melee or `Idle(aip2)`
  (10); outside melee a walk on `aip3` (80/85/90) or `Idle(10)`. The two exclusive steps share one constant load
  (0x005FA2C2). (0x005FA280–0x005FA37A)
- [C] The map, `AiCtl+0x14` included. (run:2026-10-30-ai-cat-emu-4, `vdog`)

#### 2.7 Row 70 `FingerMage` (0x005FA380)

```c
life = UnitLifePct(U);
p = Velocity > 0 ? min(max(Run * 100 / Velocity - 100, 0), 120) : 0;           // s16 columns, idiv
if (AiMonState3or19(U)) {
    ctl->v14 = 0;
    if (melee) return SetModeAtUnit(4, t);
    if (Skill1 >= 0 && dist < aip5) return UseSkill(Sk1mode, Skill1, t, 0, 0);
}
if (ctl->v14 == 1) {                                                             // fleeing
    ctl->v18++;
    if (life > aip3 || draw < 25 || ctl->v18 > aip6) ctl->v14 = 0;              // draw#1 (only when life <= aip3)
    else if (dist < 14) { Ovr(0, p, 0); return StepAway(t, 14, 0); }
    return Idle(15);
}
if (MonsterOwner(U) == 0 && life < aip4) { ctl->v14 = 1; ctl->v18 = 0; return StepAway(t, 9, 0); }
if (melee) {
    if (chance(1)) return SetModeAtUnit(4, t);                                    // draw#1
    if (Skill1 >= 0 && rchance(2)) return UseSkill(Sk1mode, Skill1, t, 0, 0);     // draw#2
    return T56(t, 5, 0);
}
if (dist >= aip5) { if (dist < aip7) return Walk(t, 7); return Idle(15); }
if (Skill1 >= 0 && rchance(2)) return UseSkill(Sk1mode, Skill1, t, 0, 0);         // draw#1
if (HasState(t, 84)) return Walk(t, 0);                                           // state 84 `fingermagecurse`
Idle(aip8);
```

- [I] An ownerless mage below `aip4` (30–50) percent life flees (`AiCtl+0x14` = 1, a step of 9); while fleeing, each
  event counts in `AiCtl+0x18` and steps 14 away with the path override parameter `p` (the run speed's excess over the
  walk speed in percent, 0–120) while `dist < 14`, until life rises above `aip3` (50–70), a draw below 25, or more
  than `aip6` (5) events. Otherwise: in melee A1 on `aip1`, `FingerMageSpider` on `aip2`, else `T56(t, 5, 0)`; outside
  `aip5` (15/20/26) a walk up to `aip7` (40); inside it the spider on `aip2`, a walk when the target has state 84, else
  `Idle(aip8)` (12/10/8). The `p` clamp: `t = Run·100 / Velocity − 100` (signed `idiv`), `t ≤ 0 → 0`
  (`setle; sub 1; and`), `t ≥ 120 → 120`, 0x005FA3B0–0x005FA3E7. (0x005FA380–0x005FA68A, fn:sub_00621F20_UnitLifePct@0x00621F20,
  fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run)
- [C] The entry call `UnitLifePct(U)` from 0x005FA3AB, before any test. (run:2026-10-30-ai-cat-emu-4, `fmage`)

#### 2.8 Row 71 `Regurgitator` (0x005FA710) and its callback `AiRegurgitatorCb` (0x005FA690)

```c
switch (ctl->v14) {
case 5: StepAway(t, 16, 1); ctl->v14 = 0; return;
case 2: m = GameFindUnit(G, 1, ctl->v18);                                // walking to the corpse
        if (!m || m->mode != 12) { v14 = v18 = v1C = 0; return Ring(8); }
        if (UnitDistSq(U, m) > 4) {
            if (ctl->v1C >= 6) { v14 = v18 = v1C = 0; return Ring(8); }
            WalkStop(m, 1); ctl->v1C++;
        }
        ctl->v14 = 3; return Idle(8);
case 3: m = GameFindUnit(G, 1, ctl->v18);                                // eating
        if (Skill1 >= 0 && m && m->mode == 12) { UseSkill(Sk1mode, Skill1, m, 0, 0); ctl->v14 = 4; return; }
        v14 = v18 = v1C = 0; return Ring(8);
case 4: if (!melee) { SetModeAtUnit(5, t); ctl->v14 = 5; return; }
        return StepAway(t, 8, 1);
}
s = { 0, aip6 * aip6 }; Search(&s, AiRegurgitatorCb, 1);                 // the nearest corpse within aip6
if (ctl->v14 == 1) {
    if (s.found) { ctl->v18 = s.found->guid;
                   if (UnitDistSq(U, s.found) > 2) { WalkStop(s.found, 1); v14 = 2; v1C = 0; return; }
                   Idle(8); v14 = 3; v1C = 0; return; }
    if (Range(100) < 20) { v14 = v18 = v1C = 0; return; }                // draw#1
    return Ring(8);
}
if (s.found) {
    if (UnitDistSq(U, s.found) < 9 && rchance(2)) goto eat;               // draw#1
    if (rchance(5)) goto eat;                                             // draw#1 or #2
}
r = Range(100);                                                           // draw#1..#3
if (melee) { if (r < aip1) return SetModeAtUnit(4, t); return Idle(15); }
if (r < aip3) return Walk(t, 0);
if (s.found && rchance(4)) goto eat;                                      // draw#2..#4
return Idle(8);
eat: WalkStop(s.found, 1); ctl->v14 = 2; ctl->v18 = s.found->guid; ctl->v1C = 0;
```

- [I] A state machine in `AiCtl+0x14` (0 idle, 1 looking, 2 walking, 3 eating, 4 after the meal, 5 stepping away)
  with the corpse's guid in `+0x18` and a walk count in `+0x1C` (six walks at most). Nothing in the function sets
  state 1 (its twelve stores to `AiCtl+0x14` write 0, 2, 3, 4 or 5, the zeros through `xor`ed registers;
  0x005FA710–0x005FAA8A); only the search path, which runs in states 0 and 1 (and any other value), tests it. Up to four
  `Range(100)` draws in one decision (two corpse tests, the command draw, the late corpse test). The `GameFindUnit`
  type in `EDX` is 1 (monster), computed as `state − 1` and `state − 2` (0x005FA767, 0x005FA803). In state 4 a unit
  out of melee plays A2 at the target and goes to state 5; one in melee steps 8 away and stays in 4.
  (0x005FA710–0x005FAA8A, fn:sub_00552F60_GameFindUnit@0x00552F60, fn:sub_005DE200_MonAiWanderRing@0x005DE200,
  fn:RNG_Range@0x0045C390)
- [I] **The callback** `(ECX game, EDX unit; cand, s)` takes a monster other than the unit with `Unit+0xC4` bit `0x200`
  clear and bit `0x02` set, in a death mode (`MonIsDeathMode`), not in state set 33, of alignment 0, with the MonStats2
  flag `MonStats2FlagTest` tests, within `UnitDistSq ≤ s.r2`; it keeps the last such candidate at or nearer than the
  current best (`jg` skips, so ties replace). No draw. (0x005FA690–0x005FA708, fn:sub_0063EA40_MonIsDeathMode@0x0063EA40,
  fn:sub_004638A0_MonStats2FlagTest@0x004638A0)
- [C] The state dispatch: states 5, 2, 3 and 4 (both melee cases) to their first callee and the search's block
  (`{0, aip6²}` at `EBP−0x34`, callback 0x005FA690, kind 1) for every other value; no draw before them.
  (run:2026-10-30-ai-cat-emu-4, `regurg`)

#### 2.9 Row 72 `DoomKnight` (0x005FAA90)

```c
if (!melee) { if (chance(3)) return Walk13(t, 7); return Idle(aip4); }           // draw#1
if (chance(1)) return SetModeAtUnit(4, t);                                       // draw#1
Idle(aip2);
```

- [I] One draw per event: in melee A1 on `aip1` (90/95/100) or `Idle(aip2)` (10/5/5); outside, the type-13 walk on
  `aip3` (80/85/90) or `Idle(aip4)` (10). (0x005FAA90–0x005FAB74, fn:sub_005DED40_MonAiWalkToUnitType13@0x005DED40)
- [C] The map. (run:2026-10-30-ai-cat-emu-4, `dknight`)

#### 2.10 Row 73 `AbyssKnight` (0x005FAB80)

```c
life = UnitLifePct(U);
if (Skill2 in [0, Skills count) && (st = Skills[Skill2].aurastate) >= 0 && !HasState(U, st)
    && life < aip1 && rchance(2))                                                    // draw#1
    return UseSkill(Sk2mode, Skill2, 0, 0, 0);
if (melee) { if (chance(3)) return SetModeAtUnit(4, t); return Idle(aip4); }       // draw#1 or #2
if (dist < aip5 && ctl->v14 <= 0) ctl->v14 = aip6;
if (Skill1 >= 0 && ctl->v14 == 0 && !(U is a monster with MonsterData+0x0E >= 4)) {
    UseSkill(Sk1mode, Skill1, t, 0, 0); ctl->v14 = aip6; return;
}
if (ctl->v14 > 0) ctl->v14--;
if (chance(7)) { Ovr(2, 0, 6 + (step().low & 1)); return Walk(t, 7); }             // draw#1/#2, then one more step
if (dist < aip8) return T56(t, 3, 0);
Idle(15);
```

- [I] `MonBoneArmor` (Skill2) below `aip1` (40/75/100) percent life when the unit lacks its `aurastate` (Skills
  `+0x080`, records at `DataTables+0xB98`, `0x23C` bytes each, count `+0xBA0`), on `aip2` (80). In melee A1 on `aip3`
  (90/94/97). Outside, `AiCtl+0x14` is a countdown: armed to `aip6` (1/1/0) inside `aip5` (6/6/5) when it is at or below
  0, and `DoomKnightMissile` (Skill1) fires when it is 0; it counts down by one per event otherwise. The Skill1 gate
  also requires `MonsterData+0x0E < 4` for a monster: the appearance byte that class 311 draws as `Range(4)` at its
  creation (monsters/0004, stats 14), so 0–3 and always passing for the stock record. Then the walk on `aip7` (70/65/50)
  with path override type 2 and byte 6 or 7 from the **low bit of the next step's low word** (not mod 100;
  `and al,1; add al,6`, 0x005FADB3–0x005FADC7), `T56(t, 3, 0)` inside `aip8` (40), else `Idle(15)`. Up to three
  steps (the `Range` and two inline). (0x005FAB80–0x005FAE32, fn:sub_00621F20_UnitLifePct@0x00621F20,
  fn:UNIT_HasState@0x00639DF0, tbl:Skills.txt:aurastate, tbl:MonStats.txt:Skill2)
- [C] The entry call `UnitLifePct(U)` from 0x005FABAF, before any test. (run:2026-10-30-ai-cat-emu-4, `aknight`)

#### 2.11 Row 74 `OblivionKnight` (0x005FAF00) and its callback `AiOblivionKnightCb` (0x005FAE40)

```c
s = { knight 0, weak 0, r2 2500, knightD2 0x7FFFFFFF, weakD2 0x7FFFFFFF }; Search(&s, AiOblivionKnightCb, 1);
if (dist < aip1) {
    if (Skill4 > 0 && Skill4 < Skills count && (st = Skills[Skill4].auratargetstate) > 0 && !HasState(t, st))
        goto curse4;
    if (s.knight && UnitDistSq(s.knight, t) > dist * dist && Walk(s.knight, 4)) return;
    Ovr(2, 50, 0); if (StepAway(t, 10, 1)) return;
    if (Skill3 >= 0) return UseSkill(Sk3mode, Skill3, t, 0, 0);
}
h = FindHostile(&d2, 0);
if (h && d2 < aip2) {                                   // d2: the frame word EBP-0x10, not set before the call
    if (Skill6 > 0 && ctl->v14 < T && rchance(4)) goto curse6;                      // draw#1
    if (chance(5)) {                                                                 // draw#1 or #2
        if (Skill3 >= 0 && rchance(6)) return UseSkill(Sk3mode, Skill3, h, 0, 0);    // draw#2 or #3
        if (Skill1 >= 0 && !(U is a monster with MonsterData+0x0E >= 4)) return UseSkill(Sk1mode, Skill1, h, 0, 0);
    }
}
if (dist > aip8 && chance(7)) return Near(t, 6);                                    // draw
if (draw > 69) return Idle(10);                                                     // draw
return T56(t, 3, 0);
curse4: UseSkill(Sk4mode, Skill4, t, 0, 0); ctl->v14 = T + aip3; return;
curse6: UseSkill(Sk6mode, Skill6, t, 0, 0); ctl->v14 = T + aip3; return;
```

- [I] Inside `aip1` (6/7/8) the knight curses with `Decrepify` (Skill4) when the target lacks its `auratargetstate`
  (Skills `+0x082`), else keeps a `doomknight1` (the callback's) between itself and the target (it walks to the
  knight when that knight is farther from the target than it is), else steps 10 away with override 50, else casts
  `MonBoneSpirit` (Skill3) at the target. Then at its own hostile within `aip2` (25–27): `MonCurseCast` (Skill6) on
  `aip4` (50) when its frame timer `AiCtl+0x14` has passed, aimed at the event's target, and both curses re-arm the timer
  to `T + aip3` (500/350/200 frames); else on `aip5` (80/85/90) `MonBoneSpirit` on `aip6` (30) at the hostile, or
  `DoomKnightMissile` with the appearance-byte gate of § 2.10. Last: `Near(t, 6)` beyond `aip8` (9/10/11) on `aip7`
  (30), `Idle(10)` on a draw above 69, else `T56(t, 3, 0)`. Up to five draws. (0x005FAF00–0x005FB28F,
  fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, tbl:Skills.txt:auratargetstate, tbl:MonStats.txt:Skill4)
- [I] **The callback** `(ECX game, EDX unit; cand, s)`: a monster other than the unit, not in a death mode, with
  `Unit+0xC4` bit `0x02`, of base class 310 (`doomknight1`; `MonBaseId` in `[0, MonStats count)` and equal to `0x136`),
  within `UnitDistSq ≤ 2500`, on the unit's side (`AlignSame02`) and of alignment 0: the nearest strictly nearer goes
  to `s.knight`, the nearest below 40 percent life to `s.weak`; the think function reads `s.knight` only. No draw.
  (0x005FAE40–0x005FAEF4, fn:sub_00650D70_AlignSame02@0x00650D70, fn:sub_00463860_MonBaseId@0x00463860)
- [C] The entry call `Search(EBP−0x40, 0x005FAE40, 1)` from 0x005FAF4D with its block's five words
  (`0, 0, 2500, 0x7FFFFFFF, 0x7FFFFFFF`), before any test. (run:2026-10-30-ai-cat-emu-4, `oknight`)

#### 2.12 Row 75 `QuillMother` (0x005FB2A0)

```c
if (AiMonState3or19(U)) {
    blk.kind = 1; blk.w0C = t ? t->type : 6; blk.w10 = t ? t->guid : -1; MonHelpBlock(U, &blk);
    if (melee) return SetModeAtUnit(4, t); return Walk(t, 7);
}
if (!melee) { if (chance(2)) return Walk(t, 7); return Idle(aip4); }              // draw#1
if (chance(1)) return SetModeAtUnit(4, t);                                       // draw#1
Idle(aip3);
```

- [I] In the 3-or-19 state the mother posts a kind-1 group record with the target and attacks or walks without a
  draw; otherwise one draw: A1 on `aip1` (60–95) in melee or `Idle(aip3)` (16 down to 6), a walk on `aip2` (50–90)
  outside or `Idle(aip4)` (15). (0x005FB2A0–0x005FB402, fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0)
- [C] The map, the group block's three words at `EBP−0x20` included. (run:2026-10-30-ai-cat-emu-4, `quill`)

#### 2.13 Row 76 `EvilHole` (0x005FB410)

```c
if (ctl->v14 <= 0) { ctl->v14 = T + aip2; ctl->v18 = aip1; }       // first event: the timer and the stock
switch (U ? U.mode : 0) {
case 1:  if (dist > 5) return Idle(5); SetMode(10, 0, 0); return Delay(20);     // NU: S3 when the target is near
case 10: SetMode(11, 0, 0); return Delay(20);                                    // S3 -> S4
case 11: if (ctl->v18 > 0) {
             if (T > ctl->v14) {
                 ctl->v14 = T + aip2;
                 SpawnClassByBase(U; &cls, &x, &y, &mode, 0, 0);
                 if ((room = RoomAtSubtile(UnitGetRoom(U), x; y)) && (m = SpawnAtPos(G, room; x, y, cls, mode, 2, 0x42))) {
                     ctl->v18--; m->+0xC4 |= 0x4020000;
                     if (U.class == 711) { STATE_Set(m, 184, 1); UnitSetOverlayStat(m, 202, 0); }   // `demonhole`
                 }
             }
             return Delay(aip2);
         }
}
SetMode(0, 0, 0);                                    // any other mode, or S4 with the stock spent: DT
```

- [I] The hole opens (S3, S4) when a target is within 5, then in S4 spawns one monster every `aip2` (50; 25 for
  `demonhole`) frames from a stock of `aip1` (10; 3), counted down on each placed spawn, and dies (mode 0) when the
  stock is spent or in any mode but 1, 10 and 11. The `demonhole`'s spawns get state 184 (`uberminion`).
  (0x005FB410–0x005FB59E, fn:sub_005DDFC0_MonAiSetMode@0x005DDFC0, fn:sub_00621E40_UnitSetOverlayStat@0x00621E40)
- [C] The map, the first event's `AiCtl+0x14/+0x18` and the re-armed `+0x14` before `SpawnClassByBase` included;
  `SetMode`'s `Delay(20)` after it is not covered. (run:2026-10-30-ai-cat-emu-4, `ehole`)

#### 2.14 Rows 77 `Trap-Missile` (0x005FB5B0), 80 `Trap-Poison` (0x005FB900) and 92 `Trap-Nova` (0x005FB9B0)

```c
if (t && dist <= aip1 && ctl->v14 < aip2) {
    if (ctl->v18 == 0) { shot; ctl->v14++; ctl->v18 = 1; return; }   // 77: SetModeAtUnit(4, t); 80, 92: if Skill1 >= 0,
                                                                      //     UseSkill(Sk1mode, Skill1, t, 0, 0)
    ctl->v18 = 0; return Idle(aip3);
}
if (U) U->+0xC4 |= 0x20000;
SetMode(0, 0, 0);
```

- [I] The three traps shoot on every second event while the target is within `aip1` (25/30/32 for 77, 20 for 80
  and 92) and they have shot fewer than `aip2` (1) times, idling `aip3` (15) between; then, or when the target is gone or
  out of range, they set `Unit+0xC4` bit `0x20000` and die (mode 0). Row 77 shoots by A1 (its records have no
  skill), 80 and 92 by `Skill1` (`PrimePoisonNova`, `Trap Nova`); in 80 and 92 a `Skill1 < 0` falls to the idle
  branch with `v18 = 0`. Rows 77 and 80 are kind 2 (also run with no target; that path dies), 92 kind 1. No draw.
  (0x005FB5B0–0x005FB641, 0x005FB900–0x005FB9AB, 0x005FB9B0–0x005FBA5B)
- [C] The three maps, `AiCtl+0x18` and `Unit+0xC4` before the boundaries included; the shot's `v14++` and `v18 = 1`
  come after their call and are not covered. (run:2026-10-30-ai-cat-emu-4, `tmissile`, `tpoison`, `tnova`)

#### 2.15 Row 87 `Trap-Melee` (0x005FBA60)

```c
if (!melee) return Idle(40);
if (chance(1)) return SetModeAtUnit(4, t);                                       // draw#1
Idle(aip2);
```

- [I] A1 on `aip1` (70) inside melee range, else `Idle(aip2)` (15); outside melee `Idle(40)`.
  (0x005FBA60–0x005FBAF1)
- [C] The map. (run:2026-10-30-ai-cat-emu-4, `tmelee`)

#### 2.16 Rows 78 `Trap-RightArrow` (0x005FB6C0) and 79 `Trap-LeftArrow` (0x005FB7E0)

```c
if (dist < aip1 || dist > aip2) return Idle(40);
UnitGetPos(U, &u); UnitGetPos(t, &v);
a = 78 ? u.x - v.x : u.y - v.y;                         // s32, |a| by `jns; neg`
if (|a| <= 2 && T > ctl->v14) {
    ctl->v14 = T + aip3;
    if (AiTrapArrowKind(G, U) != 1) return SetModeAtUnit(4, t);
    if (Skill1 >= 0) { ctl->v1C = T + aip4; return UseSkill(Sk1mode, Skill1, t, 0, 0); }
}
Idle(30);
```

- [I] The right-arrow trap shoots when the target is within 2 of its own **x**, the left-arrow trap within 2 of its
  **y** (the first and second words of `UnitGetPos`, 0x005FB716, 0x005FB836), between `aip1` (5) and `aip2` (15), and
  its frame timer `AiCtl+0x14` has passed; the timer re-arms to `T + aip3` (30/23/18) before the kind is read. Kind 1
  uses `Skill1` (`PoisonBallTrap`) and writes `AiCtl+0x1C = T + aip4` (200), which nothing in the function reads;
  other kinds play A1 at the target. `CursedBallTrap…` (Skill2) is not read. (0x005FB6C0–0x005FB7D9,
  0x005FB7E0–0x005FB8F9, fn:sub_00620870_UnitGetPos@0x00620870, tbl:MonStats.txt:Skill1)
- [C] The two maps, the kind helper and the region word included (§ 2.17). (run:2026-10-30-ai-cat-emu-4, `trarrow`,
  `tlarrow`)

#### 2.17 The trap-arrow kind `AiTrapArrowKind` (0x005FB650)

```c
lvl = RoomGetLevelId(UnitGetRoom(U));
r = MonRegionGet(G + 0xF0, lvl);                          // [ECX + 4 * EDX]
if (r->+0x2D4 < 0) r->+0x2D4 = lvl < 40 ? 0 : RNG_RandLoHi(&U->seed; 0, 3);   // 0, 1 or 2: low mod 3
return r->+0x2D4;
```

- [I] One kind per level's monster region, chosen by the first arrow trap that shoots there, on that trap's own
  seed; 0 below level 40. `RNG_RandLoHi(ECX seed, EDX lo; hi)` returns `lo` for `hi ≤ lo` and otherwise steps once and
  returns `lo + low mod (hi − lo)` (here `hi − lo` = 3 is not a power of two; 0x004BC500–0x004BC54E). Which code
  writes −1 into `+0x2D4` (the region's creation) is not read. (0x005FB650–0x005FB6B1,
  fn:sub_0061A1B0_RoomGetLevelId@0x0061A1B0, fn:sub_00547BB0_MonRegionGet@0x00547BB0, fn:RNG_RandLoHi@0x004BC500)
- [C] Inside rows 78 and 79: the region word before and after, the step and its `mod 3`, the `lvl < 40` edge
  (`cmp ebx,0x28; jge`, met at level 40 in 7 cases of each family). (run:2026-10-30-ai-cat-emu-4, `trarrow`, `tlarrow`)

#### 2.18 The group-call blocks of rows 65 and 75

- [I] Both build a stack block for `MonHelpBlock` (ai/0002 § 2.5: it copies the block's `+0x08..+0x18` to the head of
  each minion of the group) with `+0x08` the kind and two more words. Row 65: kind 1, `+0x0C` the target's guid
  (`[t+0xC]`, −1 for no target), `+0x10` its type (`[t]`, 6 for none) (0x005F9AE8–0x005F9B0E); kind 14, `+0x0C` the
  corpse's guid, `+0x10` 1 (0x005F9C14–0x005F9C2C). Row 75: kind 1, `+0x0C` the type (6 for none), `+0x10` the guid
  (−1 for none) (0x005FB2CA–0x005FB2EE). Row 14's reader takes `+0x0C` as a type and `+0x10` as a guid (re/types/ai.h);
  `+0x14` and `+0x18` are left as the stack held them in all three. (fn:sub_0058F730_MonHelpBlock@0x0058F730)

#### 2.19 The parameter list and the action helpers

- [I] No function of the batch calls `AiParamsHead`, `AiParamsPush` or `AiParamsPop` directly, and none calls the
  action helpers 0x005DF850, 0x005DF990, 0x005DFA00 or 0x005DFBF0 (`grep -c 'call   0x5df850\|call   0x5df990\|call
  0x5dfa00\|call   0x5dfbf0' b4-asm.txt`: 0). (`b4-asm.txt`)

- [I] **The helpers' callers.** A scan of the whole image's disassembly for a `call`, `jmp` or `push` of the five
  helper addresses (`b4-helper-refs.txt`) finds each callback pushed once, by its row (0x005F9B93, 0x005FA8C2,
  0x005FAF25), the placer called once, by row 68 (0x005FA116), and the kind helper twice, by rows 78 and 79
  (0x005FB749, 0x005FB869); other reference forms (a pointer in a data table) were not scanned.
  (fn:sub_005F9E30_AiVileMotherSpawn@0x005F9E30, fn:sub_005FB650_AiTrapArrowKind@0x005FB650)

### 3. Emulation (run:2026-10-30-ai-cat-emu-4)

- [C] Nineteen families, 240 cases each, 4 560 cases, all matching, none stopped, no traced access outside the
  declared memory (`emu/check.txt`). Each case runs one think function (or row 65's `alt`) on a declared image (the
  docstring of `tools/ai_cat_emu4.py`) and ends at the first observed callee or, for row 66, at the function's
  return; the checker compares the callee, the call site (the return address), `ECX`/`EDX` where the callee takes
  them, the stack arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C`, `Unit+0xC4`, the region's `+0x2D4` and, where
  the callee takes a pointer into the frame, the words it addresses (the `FindHostile` slot `EBP+8`, the search blocks
  at `EBP−0x34` and `EBP−0x40`, the group block at `EBP−0x20`; from the stack dump). Callees run on the declared image
  rather than observed: `RNG_Range`, `RNG_RandLoHi`, `AiMonState3or19` with 0x005734E0, `UnitGetSubX/Y` and
  `UnitGetPos` with `PathGetX/Y`, `UnitGetRoom` with `PathGetRoom`, `RoomGetLevelId` with `RoomLevelId`,
  `MonRegionGet` and `AiTrapArrowKind`. Controls: `le` (each draw compared with `<=`), `d0` (every `aip` from the
  Normal column), `cmp` (every compare that is not a draw with its strictness switched), `r4` (the arrow kind as
  `low mod 4`) fail every case they separate, and the site control (each call site one byte later) fails every case
  that ends at a callee (run:2026-10-30-ai-cat-emu-4):

  | family | row | boundaries reached | cases with a draw | `le` | `d0` | `cmp` | `r4` | compares met at equality (`EDGES`) |
  |---|---:|---:|---:|---:|---:|---:|---:|---|
  | `skmage` | 64 | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `fetish` | 65 | 2 | 0 | 0 | 0 | 0 | 0 | — |
  | `fetishalt` | 65 alt | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `queen` | 66 | 3 + return | 0 | 0 | 64 | 29 | 0 | `v14<aip1` 29 |
  | `vmother` | 68 | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `vdog` | 69 | 5 | 200 | 34 | 69 | 0 | 0 | draws `aip1` 15, `aip3` 19 |
  | `fmage` | 70 | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `regurg` | 71 | 6 | 0 | 0 | 77 | 0 | 0 | — |
  | `dknight` | 72 | 4 | 240 | 27 | 136 | 0 | 0 | draws `aip1` 12, `aip3` 15 |
  | `aknight` | 73 | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `oknight` | 74 | 1 | 0 | 0 | 0 | 0 | 0 | — |
  | `quill` | 75 | 5 | 137 | 17 | 75 | 0 | 0 | draws `aip1` 7, `aip2` 10 |
  | `ehole` | 76 | 5 | 0 | 0 | 75 | 67 | 0 | `v14<=0` 38, `dist>5` 17, `v18>0` 12, `T>v14` 4 |
  | `tmissile` | 77 | 3 | 0 | 0 | 64 | 52 | 0 | `dist<=aip1` 54, `v14<aip2` 49 |
  | `trarrow` | 78 | 4 | 21 | 0 | 71 | 53 | 14 | `dist<aip1` 44, `dist>aip2` 25, `\|a\|<=2` 25, `T>v14` 9, `lvl<40` 7 |
  | `tlarrow` | 79 | 4 | 24 | 0 | 78 | 62 | 20 | `dist<aip1` 46, `dist>aip2` 36, `\|a\|<=2` 30, `T>v14` 16, `lvl<40` 7 |
  | `tpoison` | 80 | 3 | 0 | 0 | 62 | 56 | 0 | `dist<=aip1` 62, `v14<aip2` 42 |
  | `tmelee` | 87 | 3 | 117 | 13 | 71 | 0 | 0 | draws `aip1` 13 |
  | `tnova` | 92 | 3 | 0 | 0 | 62 | 44 | 0 | `dist<=aip1` 58, `v14<aip2` 36 |

  The `le` … `r4` columns count the cases each control separates (it passed none). Every threshold compare of the
  thirteen covered maps is met at equality in at least one case (the `EDGES` lines of `check.txt`), so each has a
  strictness control. **Edges with no control:** the `==` and `!=` tests (`AiCtl` states and flags, row 71's state
  dispatch, row 69's first-event flag, the arrow kind `!= 1`, the traps' `v18 == 0`) and the sign tests (`Skill1 ≥ 0`,
  `t != 0`): a wrong reading of these gives another boundary or site on the cases that hold the other value, but no
  control moves their edge. Row 71 draws nothing before its boundaries, so `le` and `cmp` separate nothing there; its
  `d0` cases are the search radius `aip6²` in the block. The six `entry` families take no draw and no compare before
  their call: no control separates them and their `[C]` is the call's site and arguments only. Not covered: every
  callee and everything after it. (run:2026-10-30-ai-cat-emu-4)
- [I] **The development run** (rule 6): `emu/dev-1/` (4 560 cases, all matching, every control failing every case it
  separates, with the case writer before the trap arrows' tuning, which there left 4 and 10 cases reaching the kind
  draw), checked by its own copy of the tool (`dev-1/ai_cat_emu4.py.rev`); the models are the same in both runs, and
  no kept output was written over a development one. The kept `check.txt` comes from the committed tool, which adds the
  `EDGES` line to the development tool's output. (run:2026-10-30-ai-cat-emu-4)
- [I] Not emulated past their entry call: rows 64 (`FindHostile`), 65's `alt` and 65 past its skill-sign test
  (`HasState`, `SkillFindByOwner`), 68 (`MONSTATS_GetClassChainPos`), 70 and 73 (`UnitLifePct`), 74 (`AiUnitSearch`).
  Each reaches, before its first draw, a callee whose read set is not declarable in a small image (the hostile search
  over rooms, the state and skill lists, the class chain, the unit's stats). Phase 2's logs reproduce them (row 64 is
  the batch's tier AI). (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_00621F20_UnitLifePct@0x00621F20)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip8 (`+0x56 + 6(k−1) + 2d`), tbl:MonStats.txt:Skill1 … Skill6
  (`+0x170 + 2(k−1)`), tbl:MonStats.txt:Sk1mode … Sk6mode (`+0x180 + (k−1)`), tbl:MonStats.txt:Velocity (`+0x32`),
  tbl:MonStats.txt:Run (`+0x34`), the MonStats count `g_pDataTables+0xA80` (rows 68, 74), tbl:Skills.txt:aurastate
  (`+0x080`, row 73), tbl:Skills.txt:auratargetstate (`+0x082`, row 74), the Skills records and count
  (`g_pDataTables+0xB98`, `+0xBA0`).
- struct:AiCtl+0x00, struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtx+0x14, struct:AiCtx+0x18,
  struct:MonsterData+0x0E, struct:Unit+0x04, struct:Unit+0x10, struct:Unit+0xC4, struct:Game+0x6D, struct:Game+0xA8,
  struct:Game+0xF0 (the monster regions by level id), the region's `+0x2D4`, the DRLG room's `+0x58` and the level's
  `+0x1D0` (its id).

## Dead ends

- None in the batch's own code. Ghidra's decompile of row 74 drops the `imul` of `dist * dist` before the
  `UnitDistSq` compare (0x005FB00D–0x005FB012) and of row 65's `alt` shows `MonAiInit(*ctx, *puVar1)`; objdump gives
  both.

## Open questions

- Rows 65 and 75 write the group-call block's `+0x0C`/`+0x10` in opposite orders (§ 2.18): which consumer reads a
  kind-1 or kind-14 record from these rows, and whether one order is a defect. A P2 log of a `fetishshaman` breath and
  a `quillbear` in the 3-or-19 state settles what the minions do with it.
- Who writes the region's `+0x2D4` (the trap-arrow kind's −1, § 2.17) and whether every region starts at −1.
- Row 71's state 1 (`AiCtl+0x14` = 1) is tested but set by no code of the function (§ 2.8): whether another path
  sets it (an `alt`, a parameter record), or the branch is unreachable on stock data.
- Row 73's and 74's `DoomKnightMissile` gate on `MonsterData+0x0E < 4` (§§ 2.10, 2.11): the stock classes 311 and 312
  always pass (monsters/0004); what the `dkmag1..3` records (classes 701, 702, 713) hold there is not read.
- Who writes `MonsterData+0x54` (the 3-or-19 test, rows 70 and 75): still unnamed (ai/0001's open question).
