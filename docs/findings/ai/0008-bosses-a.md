# 0008 — Catalogue batch 7 (bosses-A): the think functions of AI rows 34, 44, 50, 53, 55, 59, 90, 144 and 146

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 7 (34 `Andariel`, 44 `Duriel`, 50 `Mephisto`, 53 `Summoner`, 55
> `Izual`, 59 `BloodRaven`, 90 `Griswold`, 144 `UberIzual`, 146 `UberMephisto`), what do its init and think functions
> do: which `aip` slots and MonStats columns they read, which AI-control words they keep, which draws they make on
> which seed and in which order, and which command, skill or path request they end in? And does a think function of
> rows 50 and 146 read `aidist` (plan 0052 P1.2)?
> **Date:** 2026-11-03   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 7)   **Status:** reviewed (`lane/r52g`; plan 0052 closed 2026-11-04)

Static reading of the pinned `Game.exe` in Ghidra and objdump, as batch 6 ([ai/0007](0007-hirelings.md), its opening
paragraph: the Ghidra copy, the scratch signatures, `b67-asm.txt`, `b67-draws.txt`, `b67-rngsites.txt`, `b67-refs.txt`,
`b67-tblrows.txt`, `b67-rows.txt`), over the ranges `0x005E5AC0`–`0x005E5B70`, `0x005E6300`–`0x005E6800`,
`0x005F5830`–`0x005F5A20`, `0x005F67B0`–`0x005F6A10`, `0x005F7700`–`0x005F81D0` and `0x005F85C0`–`0x005F8F80`, which
hold no function of another batch; `0x005B4390` (Izual's quest call) is copied from a whole-image objdump into
`b67-asm-extra.txt`. Emulation: run:2026-10-30-ai-cat-emu-6 (§ 4), eleven of its eighteen families. Kept outputs under
`workspace/logs/r52g/` (manifest `manifest.sha256`; `emu/` and `emu/dev-1/` their own manifests). Notation as
[ai/0007](0007-hirelings.md) and [ai/0006](0006-summons.md); `aidel` the byte at `M + 0x4F + d`; `RangeB(n)` =
`RNG_RangeB` on the unit's seed; `x, y` of a target = its static path's `+0x0C/+0x10` for unit types 2, 4 and 5, else
`PathGetX/Y` of its path (0 without one); `WalkToward(t, a, b)` = `MonAiWalkTowardUnit`.

## Answer (summary)

- [I] **The batch.** Ten entries for nine table rows: one think each, and row 59 an init (0x005E6300); plus
  Mephisto's target pick 0x005F77C0 and its search callback 0x005F7700, the A4Q1 step 0x005B4390, and two functions
  with no reference (0x005F7F10, 0x005F8010). Every row is of kind 1 (`MonAiTargetOrIdle`: the think runs only with a
  target; `b67-tblrows.txt`, ai/0001 § 4). No row has an `alt`. (data:g_MonAiTable@0x0073CA18,
  fn:sub_005B1650_MonAiTargetByKind@0x005B1650)
- [I] **`aidist` (rows 50 and 146).** No instruction of 0x005F7700–0x005F7EF0 (Mephisto's think, pick and callback),
  0x005F7F10–0x005F81C0 or 0x005F81C0–0x005F81D0 (row 146) reads MonStats `+0x52..+0x54` (`b67-aidist.txt`: 0, 0, 0);
  Mephisto's `aidist` 0/40/46 is read by the machinery's target search before the think (ai/0001 § 6, `aidist[d]`, 35
  when 0). (fn:sub_005F78B0_AiMephisto@0x005F78B0, tbl:MonStats.txt:aidist)
- [I] **The shapes.** 34 `Andariel`: in melee `Skill1` (`AndrialSpray`) on `aip1`, else A1; at range idle on `aip2`,
  a skill on `aip3` (`Skill1` on `Range < aip4`, else `Skill2`), else a walk to the target. 44 `Duriel`: grants itself
  `Skill4` (`Holy Freeze`) at level `aip1` as its right skill once; in melee `Skill3` on `aip2`, `Skill2` on `aip3`, A2
  on `aip4`, else A1; at range `Skill1` (`Charge`) on `aip5`, else a walk. 50 `Mephisto`: a five-way state machine
  in `v1C` (§ 2.3) with a casting burst over `Skill1..6` whose weights come from the count of its skills and whose
  NM/Hell arms add `Skill6` (`Blizzard`, on a blocked line or beyond 30) and `Skill5` (`MephFrostNova`, within 15);
  the casting target is the lowest-life hostile within 32 on `aip2`. 53 `Summoner`: element by the target's
  resistances (cold when its cold resistance is at most its fire resistance, flipped on `aip3`), `Frost Nova` and
  `VampireFirewall` on timers in `v18`/`v1C` (`aip4`, `aip5` frames), `Weaken` on `aip2`. 55 `Izual` and 144
  `UberIzual`: melee on `aip1`, a `Skill1` (`Frost Nova`) cast on `aip4` in melee or `aip3` within 10, after which
  `v18` = `aip5` idles once and `v1C` = `aip6` melee events follow without a draw; 144 first keeps its `Chilling Armor`
  state up and teleports (`Skill3`) when the line to the target is blocked. 59 `BloodRaven`: a leash to a saved home
  point (parameter record kind 10, 50 subtiles), a raise skill `Skill1` (`Nest`) at a random point near herself at most
  `2d + 8` times, `Skill2` (`Quick Strike`) on `(d + 4)·10`. 90 `Griswold`: A1 on `draw < 80` in melee, else a walk on
  `draw < 50`, else idle 10. 146 `UberMephisto`: the think is `ret 4` alone. (§ 2, fn:sub_005F5830_AiAndariel@0x005F5830,
  fn:sub_005F67B0_AiDuriel@0x005F67B0, fn:sub_005F85C0_AiSummoner@0x005F85C0, fn:sub_005F89B0_AiIzual@0x005F89B0,
  fn:sub_005E6320_AiBloodRaven@0x005E6320, fn:sub_005E5AC0_AiGriswold@0x005E5AC0, fn:sub_005F81C0_AiUberMephisto@0x005F81C0)
- [C] **The decision maps of the eleven emulated functions** from their declared inputs to the first callee they reach
  (or the return) match the emulation in all 2 640 cases of 11 families: the callee, its call site, its register and
  stack arguments, the unit seed and `v14`/`v18`/`v1C`, and for Mephisto's pick the search block. Full maps: 34
  `Andariel` (the tier AI), 90 `Griswold`, row 59's init, row 146; 44 `Duriel` with no `Skill4`; 55 `Izual` from its
  `v14` test on; 53 `Summoner` and 144 `UberIzual` up to their first stat or state call. Entry calls only: 50, its
  pick (with its block's ten words) and 59's think. The `le`, `d0`, `cmp` and site controls fail every case they
  separate. The `[C]` ends at that callee (ADR-0021). (run:2026-10-30-ai-cat-emu-6, § 4)
- [I] **Draws.** Every draw of the batch's think functions is on the acting unit's seed: multiplier-constant loads
  Griswold 1, Blood Raven 2, Andariel 3, Duriel 4, Mephisto 9 and its pick 2, Summoner 4, Izual 2 (27), and 13
  `RNG_Range`, 2 `RNG_RangeB` and 3 `RNG_RangePow2` calls (Blood Raven 4/2/3, Andariel 1, Mephisto 2, Izual 2,
  UberIzual 4), each with `ECX` = `U + 0x20` (`b67-rngsites.txt` sites 9–26: `lea ecx,[r+0x20]` or `add ecx,0x20` in
  the window, or a register set so at 0x005E653B, 0x005F584E, 0x005F78D8 and 0x005F8BEB). The pick steps the seed of
  its `EDX` unit, row 50's `U` (0x005F7BC6). No `RNG_RandLoHi`; the two unreferenced functions step their `EDX` unit's
  seed once each. (`b67-draws.txt`, § 3)
- [I] **H6 (which monster uses which skill, when)** for these rows is the slot table of § 2: each skill use names its
  `SkillK` slot, its `SkKmode`, its target or point, and the draw or timer that gates it. (§ 2,
  fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0, tbl:MonStats.txt:Skill1)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batches 1–6 (ai/0001–0007) are
cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005B4390` | `sub_005B4390_A4Q1_IzualSeen` | `(ECX game)`: quest record 22, if active (`+0x09`) and `+0x0B < 2`: `+0x14 = 0`, `QUESTS_SetState(0, A4Q1_StepBits, 1)` | I |
| `0x005E5AC0` | `sub_005E5AC0_AiGriswold` | row 90 `Griswold` think | I (map `[C]`, § 4) |
| `0x005E6300` | `sub_005E6300_AiBloodRavenInit` | row 59's init: `v1C = 0` | I (map `[C]`, § 4) |
| `0x005E6320` | `sub_005E6320_AiBloodRaven` | row 59 `BloodRaven` think | I (entry call `[C]`, § 4) |
| `0x005F5830` | `sub_005F5830_AiAndariel` | row 34 `Andariel` think | I (map `[C]`, § 4); first boundary live `C`, ai/0015 |
| `0x005F67B0` | `sub_005F67B0_AiDuriel` | row 44 `Duriel` think | I (map `[C]`, § 4) |
| `0x005F7700` | `sub_005F7700_AiMephistoPickCb` | the pick's search callback: counts, nearest, lowest life, nearest for a player searcher | I |
| `0x005F77C0` | `sub_005F77C0_AiMephistoPickTarget` | `(ECX game, EDX unit; M, t)`: the lowest-life hostile within 32 on `aip2`, else `t` | I (entry call `[C]`, § 4) |
| `0x005F78B0` | `sub_005F78B0_AiMephisto` | row 50 `Mephisto` think | I (entry call `[C]`, § 4) |
| `0x005F7EF0` | `g_AiMephistoStateJumps` | five code addresses, Mephisto's `v1C` dispatch (0x005F7B36) | I |
| `0x005F7F10` | `sub_005F7F10_UberMinionSpawn` | spawns one of classes 725–730 by the unit seed with state 184 (`uberminion`); no reference | I |
| `0x005F8010` | `sub_005F8010_PickPlayerWeighted` | a weighted pick over the eight player slots at `G+0x10F8`; no reference | I |
| `0x005F81C0` | `sub_005F81C0_AiUberMephisto` | row 146 `UberMephisto` think: `ret 4` | I (map `[C]`, § 4) |
| `0x005F85C0` | `sub_005F85C0_AiSummoner` | row 53 `Summoner` think | I (map to the stat call `[C]`, § 4) |
| `0x005F89B0` | `sub_005F89B0_AiIzual` | row 55 `Izual` think | I (map `[C]`, § 4) |
| `0x005F8C80` | `sub_005F8C80_AiUberIzual` | row 144 `UberIzual` think | I (map to the state or line call `[C]`, § 4) |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`b67-rows.txt`): 34 `Andariel` (156 `andariel`, 707 `uberandariel`, the same values), 44 `Duriel`
  (211, 708), 50 `Mephisto` (242), 53 `Summoner` (250), 55 `Izual` (256), 59 `BloodRaven` (267), 90 `Griswold` (365),
  144 `UberIzual` (706), 146 `UberMephisto` (704): 11 records. Each row's two records agree on every `aip` (rows 34,
  44), so no row of the batch is one of the 13 whose records disagree (MonStats § AI columns). Rows 59 and 90 set no
  `aip`. Every row is `{1, init, think, 0}` with an init only on row 59 (`b67-tblrows.txt`; values `[C]` as data).
  (tbl:MonStats.txt:AI, tbl:MonStats.txt:aip1)

### 2. The think functions

#### 2.1 Row 34 `Andariel` (fn:sub_005F5830_AiAndariel@0x005F5830) and row 90 `Griswold` (fn:sub_005E5AC0_AiGriswold@0x005E5AC0)

```c
think34: if (melee) { if (Skill1 >= 0 && draw < aip1) return UseSkill(Sk1mode, Skill1, t, 0, 0);   // draw#1
                      return SetModeAtUnit(4, t); }
         if (draw < aip2) return Idle(5);                                                         // draw#1
         if (draw < aip3) {                                                                       // draw#2
             if (Skill1 >= 0 && Range(100) < aip4) return UseSkill(Sk1mode, Skill1, t, 0, 0);     // draw#3
             if (Skill2 >= 0) return UseSkill(Sk2mode, Skill2, t, 0, 0); }
         Ovr(1, 0, 0);  Walk(t, 7);
think90: if (melee) { if (draw < 80) return SetModeAtUnit(4, t); }                                // draw#1
         else if (draw < 50) return Walk(t, 7);                                                   // draw#1
         Idle(10);
```

- [I] Stock: Andariel `aip1` 30/35/35 (the spray in melee), `aip2` 10/8/6 (idle), `aip3` 30/32/34, `aip4` 50/55/60;
  `Skill1` `AndrialSpray` (`seq` mode), `Skill2` `AndyPoisonBolt` (`A1`). The draws compare signed (`jge`); the
  `Skill` tests are sign tests of the s16 (`cmp word,0; jl`). The `Range` takes `ECX` = `U + 0x20` set at entry
  (0x005F584E). (0x005F5830–0x005F5A0F, fn:sub_005DE190_MonAiPathOverride@0x005DE190,
  fn:sub_005DEC80_MonAiWalkToUnit@0x005DEC80, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:aip4)
- [C] Both maps. (run:2026-10-30-ai-cat-emu-6, `andariel`, `griswold`)

#### 2.2 Row 44 `Duriel` (fn:sub_005F67B0_AiDuriel@0x005F67B0)

```c
if (Skill4 >= 0 && !UNIT_GetRightSkill(U)) {
    UnitSkillAdd(U, Skill4, aip1, 1);  PlayerSetSkill(U, 0, Skill4, -1); }        // the aura, level aip1
if (!melee) { if (Skill1 >= 0 && draw < aip5) return UseSkill(Sk1mode, Skill1, t, 0, 0);
              Ovr(13, 0, 0);  return Walk(t, 7); }
if (Skill3 >= 0 && draw < aip2) return UseSkill(Sk3mode, Skill3, t, 0, 0);
if (Skill2 >= 0 && draw < aip3) return UseSkill(Sk2mode, Skill2, t, 0, 0);
if (draw < aip4) return SetModeAtUnit(5, t);
SetModeAtUnit(4, t);
```

- [I] `UnitSkillAdd(ECX U, EDX Skill4; aip1, 1)` and `PlayerSetSkill(ECX U, EDX 0; Skill4, −1)` (0x005F67E3–0x005F680B).
  Stock `aip1` 5/5/6 is so the level of `Holy Freeze`; `aip2` 33 (`Smite`), `aip3` 50 (`Jab`), `aip4` 0 and `aip5` 0:
  with stock data the A2 and `Charge` arms are never taken (`draw < 0`), though each still makes its draw.
  (fn:UNIT_GetRightSkill@0x006201D0, fn:sub_0056DEB0_UnitSkillAdd@0x0056DEB0, fn:sub_005701B0_PlayerSetSkill@0x005701B0)
- [C] The map with `Skill4` < 0, and the `GetRightSkill` call with `Skill4` ≥ 0. (run:2026-10-30-ai-cat-emu-6,
  `duriel`)

#### 2.3 Row 50 `Mephisto` (fn:sub_005F78B0_AiMephisto@0x005F78B0)

```c
L = max(0, (100 - UnitLifePct(U)) / 5);        // imul 0x66666667; sar 1; signed
st = v1C;
if (melee) {
    if (draw > aip1) st = 3;                                                        // draw#1
    else { st = 2; v14 = step % 3 + 3; } }                                          // draw#2: low word mod 3
else if (dist > 20) st = 4;
else if (v1C > 4) goto move;                                                        // unsigned
else if (v1C == 0) {
    if (life <= 20 && dist < 5 && draw < 40) st = 1;                                // draw#1
    else if (draw < L + 50) { st = 2; v14 = step % 3 + 3; }                         // draw, then a step mod 3
    else move: { if (draw >= 65) { v1C = 0; return Idle(10); }
                 if (draw >= 65 && dist <= 5) { Ovr(0, 0, 4); Walk(t, 7); }
                 else T56(t, 4, 0);
                 v1C = 0; return; } }
switch (st) {                                                                       // g_AiMephistoStateJumps
case 0: Idle(5); v1C = 4; return;
case 1: Ovr(0, 50, 0); if (StepAway(t, 8, 1)) { v1C = 0; return; }
        if (melee) { UseSkill(Sk3mode, Skill3, t, 0, 0); v1C = 0; return; }   /* else fall into case 2 with st 0 */
case 2: if (--v14 == 0) st = 0;
        if (v18 == 0) { v18 = 2; if (!T56(t, 3, 1)) WanderRing(12); v1C = st; return; }
        v18++;  t2 = AiMephistoPickTarget(M, t);
        n = leading Skill1..8 >= 0;  if (n <= 0) WanderRing(6);
        else { q = 100 / n;  r = draw;
               if (d > 0 && ((t2 && UnitLineBlocked(U, t2, 4)) || dist > 30)) UseSkill(Sk6mode, Skill6, t2, 0, 0);
               else if (dist < 15 && r < q && d > 0)   UseSkill(Sk5mode, Skill5, t2, 0, 0);
               else if (r < 2*q)                        UseSkill(Sk4mode, Skill4, t2, 0, 0);
               else if (r < 3*q)                        UseSkill(Sk2mode, Skill2, t2, 0, 0);
               else                                     UseSkill(Sk1mode, Skill1, t2, 0, 0); }
        if (draw < 50 - L) v18 = 0;
        v1C = st; return;
case 3: st = 0;
        if (Range(100) < L + 80) { if (Range(100) < 80 - L) SetModeAtUnit(4, t); else UseSkill(Sk3mode, Skill3, t, 0, 0); }
        else { Ovr(0, 50, 0); if (!T56(t, 3, 1)) WanderRing(12); }
        v1C = 0; return;
case 4: st = 0; Ovr(0, 50, 0);
        if (!WanderNear(t, 6)) { UNIT_CancelEvents(G, U, 2, 0); if (!WalkToward(t, 12, 6)) WanderRing(12); }
        v1C = 0; return;
}
```

- [I] **The melee test is `draw <= aip1`** for state 2 (`cmp ecx,eax; jle`, 0x005F7960), `> aip1` for state 3;
  `v14 = (x mod 3) + 3` from the next step's low word (`0xAAAAAAAB`, `shr 1`, 0x005F798B–0x005F79A8). Not in melee:
  `dist > 20` (`jle` skip, 0x005F79B3) → state 4; `v1C` above 4 (`ja`, 0x005F7B2D) → the move block; 1–4 → that
  state; 0 → the low-life test (`life ≤ 20`, `dist < 5`, `draw < 40`; 0x005F79CC–0x005F7A09), then `draw < L + 50`
  (0x005F7A48) → state 2, else the move block (0x005F7A52–0x005F7AF0: `draw ≥ 65` idles 10; else a second draw: `≥ 65`
  and `dist ≤ 5` walk with `Ovr(0, 0, 4)`, else `T56(t, 4, 0)`). The dispatch is `jmp [eax*4 + 0x005F7EF0]`
  (0x005F7B36) over five words `0x005F7B3D`, `0x005F7B4B`, `0x005F7BB1`, `0x005F7DE8`, `0x005F7E67`
  (`b67-tblrows.txt`); no path above dispatches 0 (melee gives 2 or 3, `dist > 20` 4, a stored `v1C` of 1–4 itself,
  and a stored 0 takes the `v1C == 0` arm), so case 0 is not reached from this function.
  (0x005F78B0–0x005F7EEA, fn:sub_00621F20_UnitLifePct@0x00621F20, data:g_AiMephistoStateJumps@0x005F7EF0)
- [I] **The casting burst (case 2).** `v18` counts casts (`add eax,1`, 0x005F7BCE) and is cleared on `draw < 50 − L`
  (0x005F7D88–0x005F7D9E): the lower Mephisto's life, the longer the burst. `n` counts `Skill1..8` up to the first
  negative (0x005F7BF3–0x005F7C05), `q = 100 / n` (`idiv`, 0x005F7C15); every skill use in case 2 targets `t2`. The
  difficulty tests are `cmp byte [G+0x6D],0; jbe` (0x005F7C4B, 0x005F7C79, 0x005F7CBC): in Normal only `Skill4`,
  `Skill2` and `Skill1` are cast. Stock: six skills (`PrimeLightning`, `PrimeBolt`, `PrimePoisonNova`,
  `MephistoMissile`, `MephFrostNova`, `Blizzard`), so `n` = 6 and `q` = 16: in Normal `r < 32` `MephistoMissile`, `r <
  48` `PrimeBolt`, else `PrimeLightning`. Skills `Skill3` (`PrimePoisonNova`) is cast only from cases 1 and 3, on
  `t`. (0x005F7BB1–0x005F7DE5, fn:sub_00622AA0_UnitLineBlocked@0x00622AA0, tbl:MonStats.txt:Skill6)
- [I] **The target pick** `(ECX game, EDX unit; M, t)` runs `AiUnitSearch(G, U, &blk, 0x005F7700, 1)` with a
  ten-word block `{0, 0x7FFFFFFF, 0, 0, 0x7FFFFFFF, 0, 0x7FFFFFFF, 0, 0, 0}` at `EBP − 0x28`. The callback `(ECX game,
  EDX searcher; cand, blk)` takes a living candidate other than the searcher with `Unit+0xC4` bit `0x4` that is
  hostile to it (`UnitsHostile`) and within `UnitDistSq ≤ 1024`: `blk[7]++`, `blk[2]++` within 225, `blk[0..1]` the
  nearest, `blk[3..4]` the lowest `hitpoints >> 8` (stat 6, `sar`), and `blk[5..6]` the nearest only when the searcher's
  `Unit+0x00` is 0 (a player). The pick returns `blk[3]` on `draw < aip2` (`+0x5C`), else, when `blk[5]` is set, a
  second draw `< aip3` (`+0x62`) returns `blk[3]` too; else `t`. Its one caller is row 50 with `EDX` = Mephisto
  (0x005F7BDE), a monster, so `blk[5]` stays 0 and the second draw never happens there. (0x005F7700–0x005F78A3,
  fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, fn:sub_005541B0_UnitIsDead@0x005541B0, fn:sub_00554200_UnitsHostile@0x00554200,
  fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)
- [C] The entry call `UnitLifePct(U)` (0x005F78E6) and the pick's search call with its block. (run:2026-10-30-ai-cat-emu-6,
  `mephisto`, `mpick`)

#### 2.4 Row 53 `Summoner` (fn:sub_005F85C0_AiSummoner@0x005F85C0)

```c
if (v14 == 0) { A2Q5_BossSeen(G, U); v14 = 1; }
if (dist < 5 && draw < aip6) StepAway(t, 6, 0);                       // result not read; draw#1
cold = STATS_GetUnitStat(t, 43, 0) <= STATS_GetUnitStat(t, 39, 0);    // coldresist <= fireresist
if (draw < aip1) {                                                    // draw#2
    if (Skill5 >= 0 && draw < aip2) return UseSkill(Sk5mode, Skill5, t, x, y);      // Weaken; draw#3
    t2 = FindHostile(&e, 0);
    if (draw > aip3) cold = !cold;                                                  // draw
    if (cold) { if (Skill2 >= 0 && v18 < T && dist < aip7) goto nova;
                if (Skill1 >= 0 && t2 && dist < aip8) return UseSkill(Sk1mode, Skill1, t2, x, y); }
    if (Skill4 >= 0 && v1C < T) { v1C = T + aip5; return UseSkill(Sk4mode, Skill4, t, x, y); }
    if (Skill3 >= 0 && t2 && dist < aip8) return UseSkill(Sk3mode, Skill3, t2, x, y);
    if (!cold && Skill2 >= 0 && v18 < T && dist < aip7)
        nova: { v18 = T + aip4; return UseSkill(Sk2mode, Skill2, t, x, y); }
    if (Skill5 >= 0) return UseSkill(Sk5mode, Skill5, t, x, y);
}
WanderRing(4);
```

- [I] Stock: `aip1` 85/93/98, `aip2` 5, `aip3` 63, `aip4` 40, `aip5` 120/100/80, `aip6` 33/20/10, `aip7` 5/8/11,
  `aip8` 40; `Skill1` `Glacial Spike`, `Skill2` `Frost Nova`, `Skill3` `Fire Ball`, `Skill4` `VampireFirewall`, `Skill5`
  `Weaken`. `x, y` are always `t`'s, also when `t2` is the skill's target. The step away does not end the event
  (0x005F8648, no test after it). `A2Q5_BossSeen(ECX G, EDX U)` (0x005F85ED). The timers compare signed with `T`.
  (0x005F85C0–0x005F89A0, fn:sub_0059C330_A2Q5_BossSeen@0x0059C330, fn:sub_005DEFE0_MonAiStepAway@0x005DEFE0,
  tbl:MonStats.txt:aip8)
- [C] The map up to the first `STATS_GetUnitStat(t, 43, 0)`. (run:2026-10-30-ai-cat-emu-6, `summoner`)

#### 2.5 Rows 55 `Izual` and 144 `UberIzual` (fn:sub_005F89B0_AiIzual@0x005F89B0, fn:sub_005F8C80_AiUberIzual@0x005F8C80)

```c
think55: if (v14 == 0) { v14 = 1; A4Q1_IzualSeen(G); }
think144: if (Skill2 valid && (st = Skills[Skill2].aurastate) >= 0 && !UNIT_HasState(U, st))
              return UseSkill(Sk2mode, Skill2, 0, 0, 0);                       // Chilling Armor
          if (UnitLineBlocked(U, t, 6)) return UseSkill(Sk3mode, Skill3, 0, x, y);   // MonTeleport
both:  if (v18) { Idle(v18); v18 = 0; return; }
       if (melee) {
           if (v1C < 1 && !(roll < aip1)) {                                    // 55: draw; 144: Range(100)
               v1C = 0;
               if (Skill1 < 0 || !(Range(100) < aip4)) return Idle(aidel);
               cast: UseSkill(Sk1mode, Skill1, t, x, y); v18 = aip5; v1C = aip6; return; }
           if (v1C > 0) v1C--;  return SetModeAtUnit(4, t); }
       if (Skill1 >= 0 && dist < 10) { if (v1C > 0) return Walk(t, 7); if (Range(100) < aip3) goto cast; }
       if (v1C < 1 && !(roll < aip2)) return dist < 11 ? Idle(aidel) : WalkToward(t, 6, 9);   // 55: draw; 144: Range
       Walk(t, 7);
```

- [I] `A4Q1_IzualSeen(ECX G)`: `QUESTS_FindById(G, 22)`; a record with `+0x09` non-zero and `+0x0B < 2` (unsigned)
  gets `+0x14 = 0` and `QUESTS_SetState(rec; 0, A4Q1_StepBits, 1)` (`b67-asm-extra.txt`, 0x005B4390–0x005B43C2).
  Stock (both rows): `aip1` 45/50/50, `aip2` 50, `aip3` 66, `aip4` 0/75/100, `aip5` 20/5/0, `aip6` 3/4/4, `aidel`
  15/12/8; so in Normal the melee cast never happens (`aip4` 0) and after a cast `v1C` = 3–4 melee events (or walks)
  follow with no draw. Izual draws inline for the `aip1`/`aip2` rolls and with `Range` for `aip3`/`aip4`; UberIzual uses
  `Range` for all four (`b67-draws.txt`: Izual 2 and 2, UberIzual 0 and 4). (fn:QUESTS_FindById@0x00543640,
  fn:QUESTS_SetState@0x00544300, fn:sub_005B3940_A4Q1_StepBits@0x005B3940, fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0,
  tbl:MonStats.txt:aidel, tbl:Skills.txt:aurastate)
- [C] Izual's map with `v14` ≠ 0, and the quest call at `v14` = 0 (with `v14` already 1 at the call); UberIzual up to its
  `UNIT_HasState` or `UnitLineBlocked` call. (run:2026-10-30-ai-cat-emu-6, `izual`, `uizual`)

#### 2.6 Row 59 `BloodRaven` (init fn:sub_005E6300_AiBloodRavenInit@0x005E6300, think fn:sub_005E6320_AiBloodRaven@0x005E6320)

```c
init59: v1C = 0;
think59:
    h = AiParamsFind(U, 10, 0);
    if (!h) { AiParamsPush(U, {kind 10, U's own x, y}); h = AiParamsFind(U, 10, 0); }   // the home point
    hd = 0;
    if (h) { hd = DistToPointSized(t, home);                                // the target's: ECX = t, 0x005E63F8
             if (dist > 45) return Idle(5);
             if (hd > 49 || DistToPointSized(U, home) > 50) {               // second compare unsigned
                 v1C = 1; Ovr(7, 100, 0); if (RunToPoint(h->x, h->y)) return; UNIT_CancelEvents(G, U, 2, 0); }
             if (v1C && DistToPointSized(U, home) > 5) {
                 Ovr(7, 100, 0); if (RunToPoint(h->x, h->y)) return; UNIT_CancelEvents(G, U, 2, 0); }
             v1C = 0; }
    if (dist > 20 && hd < 50) { dist = max(12, dist >> 1); Ovr(7, 100, 0);       // the local copy of dist
                                if (RunNearUnit(t, dist)) return; UNIT_CancelEvents(G, U, 2, 0); }
    v14 += 3;
    if (Skill1 >= 0 && !melee && v18 < 2*d + 8 && Range(100) < v14) {        // draw#1
        a = Range(15) + 5;                                                   // draw#2
        if (Pow2(2) == 0) { dx = RangeB(a); dy = a; } else { dx = a; dy = RangeB(a); }   // draw#3, #4
        if (Pow2(2)) dx = -dx;  if (Pow2(2)) dy = -dy;                       // draw#5, #6
        UseSkill(Sk1mode, Skill1, 0, subX(t) + dx, subY(t) + dy);  v18++;  v14 = 0;  return; }
    if (dist > 5) {
        if (draw < 5 && hd < 50) { Ovr(7, 100, 0); RunNearUnit(t, 12); return; }
        if ((h2 = FindHostile(&e, &hd)) && !AiMonState3or19(U) && Range(100) < 80) {
            if (Skill2 >= 0 && Range(100) < (d + 4) * 10) return UseSkill(Sk2mode, Skill2, h2, 0, 0);
            return SetModeAtUnit(4, h2); }
        Ovr(0, 50, 0); if (T56(t, 4, 1)) return; }
    if (draw < 30 && dist < 12) { Ovr(7, 100, 0); if (StepAwayXY(t, 12 - dist, 0)) return; UNIT_CancelEvents(G, U, 2, 0); }
    SetModeAtUnit(4, t);
```

- *Corrected 2026-11-04 (`lane/s52b` review, architect, read against the instructions):* `hd` was given as the unit's distance from home; the first `AiDistToPointSized` has `ECX` = `t` (0x005E63F8), so `hd` is the target's, and only the two later compares are the unit's (0x005E6429, 0x005E6484). The raise's point was given around the unit; `edi` is `t` at 0x005E65E5, so it is around the target.

- [I] The home point is parameter record kind 10 (`AiParamsFind(ECX U, EDX 10; 0)`, 0x005E6356), pushed with the
  unit's own static or dynamic path point when missing; its leash compares are `jle`/`jge` signed except the second
  home distance (`jbe`, 0x005E6433) and the `> 5` test (`jbe`, 0x005E648E). The raise skill is cast at most `2d + 8`
  times (`lea ecx,[ecx+ecx*1+0x8]`, 0x005E653E; 8/10/12 by difficulty), with a chance `v14` that grows by 3 per event
  and resets on a cast. The `dist` of the later tests is the local copy, halved (at least 12) after a failed run near
  the target. The `hd` slot is reused: `FindHostile`'s melee pointer writes it (0x005E66A0–0x005E66AC). Stock: `Skill1`
  `Nest`, `Skill2` `Quick Strike`, no `aip`. (0x005E6320–0x005E67F4, fn:sub_0058EEF0_AiParamsFind@0x0058EEF0,
  fn:sub_0058EF40_AiParamsPush@0x0058EF40, fn:sub_005DC480_AiDistToPointSized@0x005DC480,
  fn:sub_005DF680_MonAiRunNearUnit@0x005DF680, fn:RNG_RangeB@0x0045C3E0, fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0,
  fn:sub_005DF140_MonAiStepAwayXY@0x005DF140)
- [C] The init's map (`v1C` = 0, return) and the think's entry call. (run:2026-10-30-ai-cat-emu-6, `brinit`, `braven`)

#### 2.7 Row 146 `UberMephisto` and the two unreferenced functions

- [I] Row 146's think is `ret 4` (0x005F81C0): a kind-1 event with a target commands nothing from the think; without
  a target the machinery's `MonAiTargetOrIdle` idles (ai/0001 § 4). (fn:sub_005F81C0_AiUberMephisto@0x005F81C0)
- [I] 0x005F7F10 `(ECX game, EDX unit; flag)`: one step of the unit's seed, `k = low & 7`, a class from `{725, 725, 726,
  726, 727, 728, 729, 730}[k]` (`skeleton8`, `sk_archer11`, `skmage_fire7`, `skmage_ltng7`, `skmage_cold6`,
  `skmage_pois7`) spawned by `SpawnNearUnitNoBox(class, 8, 4, 0)` with `Unit+0xC4 |= 0x4000000` and state 184
  (`uberminion`). 0x005F8010: over the eight player slots at `G+0x10F8`, a living player on the unit's level within
  1020 of the unit's point (unsigned), one step per such player, the last kept when `w[class] + (low mod 20) > −1`
  (0x005F8154–0x005F8164; `w` = {35, 40, 30, 20, `EBX`, 25, 10}, slot 4 the register's value at 0x005F810C); a
  non-player unit there takes the fatal path (0x005F8191). Neither has a `call`, `jmp`, `push`, `mov` immediate or
  data-word reference in the image (`b67-refs.txt`: `code=0 data=0`). (fn:sub_005B23C0_SpawnNearUnitNoBox@0x005B23C0,
  fn:sub_0061A1B0_RoomGetLevelId@0x0061A1B0, fn:sub_005DC530_AiDistToPoint@0x005DC530)
- [C] Row 146's map (the return, `v14`/`v18`/`v1C` unchanged). (run:2026-10-30-ai-cat-emu-6, `umeph`)

### 3. Callers and the helpers

- [I] **Callers** (`b67-refs.txt`): the ten entries are data words of `g_MonAiTable` only (rows 34, 44, 50, 53, 55,
  59 `+4`/`+8`, 90, 144, 146), with no code reference; the pick is called once (0x005F7BDE), its callback pushed once
  (0x005F77F9), the jump table read once (0x005F7B36), `A4Q1_IzualSeen` called once (0x005F8A57). The scan does not see a
  computed address. No function of the batch calls the action helpers 0x005DF850, 0x005DF990, 0x005DFA00 or 0x005DFBF0
  (`b67-draws.txt` `CALLEES`). (fn:sub_005F77C0_AiMephistoPickTarget@0x005F77C0, fn:sub_005F7700_AiMephistoPickCb@0x005F7700,
  fn:sub_005B4390_A4Q1_IzualSeen@0x005B4390)
- [I] **The callback draws nothing** by its body (`b67-draws.txt`: `MephistoCb 0 0 0 0 4 0 0`) and none of its four
  direct calls (`UnitIsDead`, `UnitsHostile`, `UnitDistSq`, `STATS_GetUnitStat`) is an RNG entry; their callees are
  not followed (P1.1 review, reopen condition (b): not met by direct calls). (fn:sub_005F7700_AiMephistoPickCb@0x005F7700)

### 4. Emulation (run:2026-10-30-ai-cat-emu-6)

- [C] Eleven families of this batch, 240 cases each, 2 640 cases, all matching, none stopped, no traced access outside
  the declared memory (`emu/check.txt`; with batch 6's seven, 4 320 cases, `result=ok`). Method, comparison and
  controls as ai/0007 § 4 (run:2026-10-30-ai-cat-emu-6):

  | family | row | outcomes (site: cases) | drew | `le` | `d0` | `cmp` | compares met at equality (`EDGES`) |
  |---|---:|---|---:|---:|---:|---:|---|
  | `andariel` | 34 | `UseSkill` 0x005F58BE: 20, 0x005F59B0: 4, 0x005F59E3: 17; `SetModeAtUnit` 0x005F58D7: 103; `Idle` 0x005F592C: 32; `PathOverride` 0x005F59FF: 64 | 204 | 24 | 53 | 0 | `draw<aip1` 5, `draw<aip2` 13, `draw<aip3` 10, `Range<aip4` 1 |
  | `duriel` | 44 | `GetRightSkill` 0x005F67DF: 53; `UseSkill` 0x005F6884: 13, 0x005F68F7: 19, 0x005F69D5: 23; `SetModeAtUnit` 0x005F694E: 16, 0x005F6964: 43; `PathOverride` 0x005F69EE: 73 | 149 | 27 | 44 | 0 | `draw<aip2` 4, `draw<aip3` 8, `draw<aip4` 7, `draw<aip5` 8 |
  | `mephisto` | 50 | `UnitLifePct` 0x005F78E6: 240 | 0 | 0 | 0 | 0 | — |
  | `mpick` | pick | `AiUnitSearch` 0x005F780B: 240 | 0 | 0 | 0 | 0 | — |
  | `summoner` | 53 | `A2Q5_BossSeen` 0x005F85F2: 49; `StepAway` 0x005F864D: 26; `STATS_GetUnitStat` 0x005F8657: 165 | 93 | 8 | 16 | 36 | `dist<5` 36, `draw<aip6` 8 |
  | `izual` | 55 | `A4Q1_IzualSeen` 0x005F8A5C: 44; `Idle` 0x005F8A71: 59, 0x005F8B8E: 12, 0x005F8C4D: 24; `SetModeAtUnit` 0x005F8C73: 33; `WalkToward` 0x005F8B75: 10; `UseSkill` 0x005F8AE8: 15; `Walk` 0x005F8BA7: 43 | 78 | 10 | 40 | 51 | `draw<aip1` 7, `draw<aip2` 2, `Range<aip3` 2, `dist<10` 5, `dist>10` 1, `v1C>0` 51 |
  | `brinit` | 59 init | return: 240 | 0 | 0 | 0 | 0 | — |
  | `braven` | 59 | `AiParamsFind` 0x005E6356: 240 | 0 | 0 | 0 | 0 | — |
  | `griswold` | 90 | `SetModeAtUnit` 0x005E5B12: 94; `Walk` 0x005E5B4B: 51; `Idle` 0x005E5B5B: 95 | 240 | 11 | 0 | 0 | `draw<50` 5, `draw<80` 6 |
  | `uizual` | 144 | `UNIT_HasState` 0x005F8D5B: 71; `UnitLineBlocked` 0x005F8D90: 169 | 0 | 0 | 0 | 30 | `s2<count` 37 |
  | `umeph` | 146 | return: 240 | 0 | 0 | 0 | 0 | — |

  The `le` … `cmp` columns count the cases each control separates (it passed none); `site_control_passed=0` in every
  family. **Edges with no control:** Izual's `Range(100) < aip4` (met at equality in no case, so its strictness is
  not tested), the `==`/`!=` and null tests (the `melee` word, Summoner's and Izual's `v14 == 0`, Izual's `v18 ≠ 0`,
  UberIzual's record test), and the sign tests of the `Skill` slots and of UberIzual's `aurastate`: a wrong reading of
  these gives another boundary or site on the cases that hold the other value, but no control moves their edge. The
  entry families take no draw and no compare before their call. Not covered: every callee and everything after it, so
  Mephisto's states, the pick's two draws, Blood Raven past its record lookup, Duriel past `GetRightSkill`, Summoner
  and UberIzual past their first stat or state call, and the walks after each `PathOverride` stay `[I]`.
  (run:2026-10-30-ai-cat-emu-6)
- [I] **The development run** as ai/0007 § 4: `emu/dev-1/`, the same cases and outputs, checked by its own tool copy;
  the kept `emu/` run wrote its own outputs. (run:2026-10-30-ai-cat-emu-6)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip8 (`+0x56 + 6(k−1) + 2d`), tbl:MonStats.txt:aidel (`+0x4F + d`),
  tbl:MonStats.txt:Skill1 … Skill8 (`+0x170 + 2(k−1)`), tbl:MonStats.txt:Sk1mode … Sk6mode (`+0x180 + (k−1)`),
  tbl:MonStats.txt:aidist (`+0x52`, not read by these functions); the Skills count and records (`g_pDataTables+0xBA0`,
  `+0xB98`), tbl:Skills.txt:aurastate (`+0x080`); stats 6 (`hitpoints`), 39 (`fireresist`), 43 (`coldresist`).
- struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtl+0x20 (parameter records, kind 10),
  struct:AiCtx+0x08, struct:AiCtx+0x14, struct:AiCtx+0x18, struct:AiCtx+0x1C, struct:Unit+0x00, struct:Unit+0x20,
  struct:Unit+0x2C, struct:Unit+0xC4, struct:Game+0x6D, struct:Game+0xA8, struct:Game+0x10F8.

## Dead ends

- Ghidra could not follow Mephisto's `jmp [eax*4+0x005F7EF0]` ("Too many branches") and shows the dispatch as a call;
  the five cases were read from objdump with the table words read from the image (`b67-tblrows.txt`).

## Open questions

- *2026-11-03 (Phase 1c, `lane/r52n`):* answered in [ai/0016](0016-uber-event.md): no Uber-specific driver found. Refinement of § 2.7: the stack argument of 0x005F7F10, written `flag` there, is the unit to spawn near, or 0 for the caller (0x005F7FAF–0x005F7FE3, read as `EDX`). (fn:sub_005F7F10_UberMinionSpawn@0x005F7F10)
- Row 146 `UberMephisto` commands nothing from its think: what moves and casts Uber Mephisto (another function by
  class or by state, a skill's own logic, or the two unreferenced functions reached by a computed address) is not
  read here (a scan for the class 704 and the state 184 outside the AI table; batch 11 holds Uber Diablo and Baal).
- Mephisto's pick: whether any other searcher reaches 0x005F7700 (a player's `blk[5]` arm) is not scanned past the
  one push (0x005F77F9).
