# 0004 — Catalogue batch 3 (pool-C): the think functions of AI rows 33, 35–40, 43, 45–49, 52, 56, 57, 63

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 3 (the ranged rows, the maggots, the Zakarum, the nests and the act III
> water rows), what does its think function do on an AI event: which `aip` slots and MonStats columns it reads, which
> AI-control words it keeps, which draws it makes on which seed and in which order, and which command, skill or path
> request it ends in?
> **Date:** 2026-10-30   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 3)   **Status:** for review (`lane/r52d`)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52d`, decompiled with the scratch
`__fastcall` signatures of batches 1 and 2 carried onto the current `re/symbols.csv`, `b3-sym-scratch.csv`; a reading
aid, not symbol rows) and objdump (`b3-asm.txt`: the ranges `0x005DF140`–`0x005DF2A0`, `0x005F56D0`–`0x005F5830`,
`0x005F5A20`–`0x005F67B0`, `0x005F6A10`–`0x005F7700`, `0x005F81D0`–`0x005F85C0`, `0x005F8F80`–`0x005F96C0`, which
leave out the boss rows 34, 44, 50, 146, 53, 55 and 144 of batch 7 that lie between them), then emulation of thirteen
think functions and row 52's `alt` under ADR-0015/ADR-0021 (§ 3, run:2026-10-30-ai-cat-emu-3). Kept outputs are under
`workspace/logs/r52d/` (manifest `manifest.sha256`, one path base: that directory; the emulation under `emu/`, its own
manifest; the two development runs under `emu/dev-1/` and `emu/dev-2/`, each with its own manifest and tool copy).
Stock values come from `b3-rows.txt` (`python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for
the 17 rows, 78 records). Every register argument quoted below was read from objdump (`b3-asm.txt`); the multiplier
sites and RNG calls per function are counted by `b3-draws.py` (`b3-draws.txt`). The machinery (the AI event, the row
kinds, the command and move helpers, `MonAiInit` and the `alt` swap) is [ai/0001](0001-machinery.md), the notation and
the helpers first read in batches 1 and 2 are [ai/0002](0002-pool-a.md) § Notation and § 4 and
[ai/0003](0003-pool-b.md); names below are `re/symbols.csv` names.

**Notation** as ai/0002 and ai/0003: `G`, `U`, `t` = `ctx+0x08`, `dist` = `ctx+0x14`, `melee` = `ctx+0x18`, `ctl` =
`ctx+0x00`, `M` = `ctx+0x1C`, `M2` = `ctx+0x20` (the MonStats2 record), `T` = `G+0xA8` (the frame), `d` = `G+0x6D`;
`aipK` the s16 at `M + 0x56 + 6(K−1) + 2d`; `draw` one inline step of the acting unit's seed `U+0x20/+0x24`, mod 100;
`chance(K)` = `draw < aipK` signed; `Range(n)` = `RNG_Range` or `RNG_RangeB` on the unit's seed (`low mod n`, 0 and no
step for `n < 1`). `ctl->v14`, `v18`, `v1C` are `AiCtl+0x14/+0x18/+0x1C`. `U.x, U.y` are the unit's subtile position
(`UnitGetSubX/Y`, inlined or called: `Unit+0x2C` path `+0x02/+0x06` u16 for a monster). Helper short names as before:
`SetModeAtUnit(m, t)`, `SetMode(m, x, y)` (`MonAiSetMode`), `Idle(n)`, `Delay(n)`, `Walk(t, f)`, `Ring(r)`, `T56(t, b,
f)`, `WalkStop(t, n)`, `RunStop(t, n)` (`MonAiRunToUnitStop`), `Run(t)` (`MonAiRunToUnit`), `Toward(t, a, b)`,
`Ovr(type, param, byte)`, `UseSkill(mode, skill, t, x, y)`; new here `StepAwayXY(o, n, f)` (§ 2.0). Modes are MonMode
rows: 0 DT, 4 A1, 5 A2, 8 S1, 12 DD, 14 SQ.

## Answer (summary)

- [I] **The batch.** Seventeen think functions, each `(ECX game, EDX unit; ctx)` with `ret 4`, one per row; rows 43 and
  45 share the init 0x005F6630 (which row 129 `GenericSpawner`'s init 0x005E6190 also calls); row 52 `FrogDemon` has an
  `alt` (0x005F81D0). Rows 33–49 and 63 are kind 1 (the think function runs only with a target), 56 and 57 kind 2 and
  52 kind 5 (they run without one too; ai/0001 § 4). (data:g_MonAiTable@0x0073CA18,
  fn:sub_005B1650_MonAiTargetByKind@0x005B1650, `ai-rows.txt` of P1.1)
- [I] **The shapes.** The ranged rows (35 `CorruptArcher`, 37 `SkeletonBow`, 33 `HellMeteor`, 63 `GargoyleTrap`)
  shoot on one or two draws; the archer also keeps its range (a step away inside 6, a walk or a run to `aip8` or
  `aip5`), and the archer and the skeleton archer aim at their own hostile from `MonAiFindHostile`, not at the event's
  target. The egg (40) hatches once on a draw and dies at its next event; the nest (43) and the sarcophagus (45) use a
  skill on a frame timer and count it in `AiCtl+0x14/+0x18`, then die; row 46 `ElementalBeast` closes, casts and kills
  itself. The submerging rows (52, 56, 57) keep a phase in `AiCtl+0x1C` and a ready frame (56, 57) or a count (52) in
  `AiCtl+0x18`. The Zakarum (48, 49) read their own life, a quest word of the target's player (48), a unit search for a
  wounded Zakarum to heal and three skill timers (49). (§ 2, fn:sub_005F5A20_AiCorruptArcher@0x005F5A20,
  fn:sub_005F6650_AiFoulCrowNest@0x005F6650, fn:sub_005F8260_AiFrogDemon@0x005F8260,
  fn:sub_005F72D0_AiZakarumPriest@0x005F72D0)
- [C] **The decision maps of thirteen functions and one `alt`** (rows 33, 36, 37, 38, 39, 40, 43, 45, 46, 47, 52 and
  its `alt`, 57, 63; for 37 and 63 the state or timer test before their first callee only) from their declared
  inputs to the first callee they reach match the emulation in all 3 360 cases: the callee, its call site, its register and stack arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C` and `Unit+0xC4`
  at the call and, where the callee takes a pointer into the frame, the word it addresses. The `le` and Normal-column
  controls and the site control fail every case they separate. The `[C]` ends at that callee (ADR-0021).
  (run:2026-10-30-ai-cat-emu-3, § 3)
- [I] **Draws.** Every draw of the batch's functions (the seventeen think functions, row 52's `alt`, the init, the
  callback and `MonAiStepAwayXY`) is on the acting unit's seed (34 multiplier sites, 21
  `RNG_Range` and 2 `RNG_RangeB` calls, no `RNG_RangePow2`, all on `U+0x20`, `b3-draws.txt`); 0–6 per decision, in the
  order of § 2's pseudocode (six for row 49 at most). Draws on other seeds can come only from callees (`MonAiFindHostile` in
  rows 35, 37 and 57, `MonAiStepAwayXY`'s `MonAiMove` in 35 and 48; the move helpers as in ai/0001 § 7). No function of the batch loops over units with a draw (P1.1
  review, reopen condition (b)): the one search callback of the batch, `AiZakarumHealCb` (row 49), has no multiplier
  site and no RNG call in its body (`b3-draws.txt`, `DRAWS AiZakarumHealCb 0 0 0 0 7`), and none of its seven direct
  calls (`AlignSame02`, `UnitAlignGet`, `MonIsDeathMode`, `MonBaseId`, `MonClassCheck`, `UnitDistSq`, `UnitLifePct`) is
  an RNG entry; their own callees are not followed. (§ 2.12, fn:sub_005F7240_AiZakarumHealCb@0x005F7240)
- [I] **Effects outside the unit.** Rows 40, 46 and 56 kill their own unit (`UnitKilled(G, U; killer, 1)`: the egg with
  its last target as killer, the beast with the event's target, the tentacle with its owner's target or with none when
  it has no owner); rows 43 and 45 set `Unit+0xC4` bit `0x20000` and command mode 0 (DT) after `aip3` spawns (45: `aip3 + 1`); row 46
  queues a kind-0 event (the mode frame event) on itself at `T + 1`; row 48 reads quest word 21 bit 0 of the target's
  player (or of the player who owns a monster target) in act III. (§§ 2.6, 2.7, 2.8, 2.10, 2.14, 2.17,
  fn:sub_0057CCB0_UnitKilled@0x0057CCB0, fn:sub_005417D0_UnitQueueEvent@0x005417D0, fn:QUESTRECORD_GetState@0x0065C310)
- [I] **The heal search keeps the last unit, not the weakest.** Row 49's callback compares each candidate's life with
  the block's `+0x08`, which nothing writes but the `< 1 → 0x7FFFFFFF` reset, so every candidate at or below 60 percent
  life replaces the previous one: the priest heals the last qualifying Zakarum in search order. (§ 2.12,
  0x005F72AF–0x005F72C5)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batches 1–2 (ai/0001–0003) are
cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005F56D0` | `sub_005F56D0_AiHellMeteor` | row 33 `HellMeteor` think | I (map `[C]`, § 3) |
| `0x005F5A20` | `sub_005F5A20_AiCorruptArcher` | row 35 `CorruptArcher` think | I |
| `0x005F5D50` | `sub_005F5D50_AiCorruptLancer` | row 36 `CorruptLancer` think | I (map `[C]`, § 3) |
| `0x005F6070` | `sub_005F6070_AiSkeletonBow` | row 37 `SkeletonBow` think | I (state test `[C]`, § 3) |
| `0x005F6220` | `sub_005F6220_AiMaggotLarva` | row 38 `MaggotLarva` think | I (map `[C]`, § 3) |
| `0x005F6340` | `sub_005F6340_AiPinHead` | row 39 `PinHead` think | I (map `[C]`, § 3) |
| `0x005F6530` | `sub_005F6530_AiMaggotEgg` | row 40 `MaggotEgg` think | I (map `[C]`, § 3) |
| `0x005F6630` | `sub_005F6630_AiNestInit` | init of rows 43 and 45: `AiCtl+0x14` = `T`, `+0x18` = 0 | I |
| `0x005F6650` | `sub_005F6650_AiFoulCrowNest` | row 43 `FoulCrowNest` think | I (map `[C]`, § 3) |
| `0x005F6A10` | `sub_005F6A10_AiSarcophagus` | row 45 `Sarcophagus` think | I (map `[C]`, § 3) |
| `0x005F6B70` | `sub_005F6B70_AiElementalBeast` | row 46 `ElementalBeast` think | I (map `[C]`, § 3) |
| `0x005F6CA0` | `sub_005F6CA0_AiFlyingScimitar` | row 47 `FlyingScimitar` think | I (map `[C]`, § 3) |
| `0x005F6E60` | `sub_005F6E60_AiZakarumZealot` | row 48 `ZakarumZealot` think | I |
| `0x005F7240` | `sub_005F7240_AiZakarumHealCb` | row 49's search callback: a wounded zealot or priest in range | I |
| `0x005F72D0` | `sub_005F72D0_AiZakarumPriest` | row 49 `ZakarumPriest` think (existing name, drlg/0009) | I |
| `0x005F81D0` | `sub_005F81D0_AiFrogDemonAlt` | row 52's `alt` | I (map `[C]`, § 3) |
| `0x005F8260` | `sub_005F8260_AiFrogDemon` | row 52 `FrogDemon` think | I (map `[C]`, § 3) |
| `0x005F8F80` | `sub_005F8F80_AiTentacle` | row 56 `Tentacle` think | I |
| `0x005F9270` | `sub_005F9270_AiTentacleHead` | row 57 `TentacleHead` think | I (map `[C]`, § 3) |
| `0x005F9490` | `sub_005F9490_AiGargoyleTrap` | row 63 `GargoyleTrap` think | I (map `[C]`, § 3) |
| `0x005DF140` | `sub_005DF140_MonAiStepAwayXY` | `(ECX game, EDX unit; other, n, f)`: move `n` away from `other` on each axis | I |
| `0x006488A0` | `sub_006488A0_PathSetFacing` | `(path, dir)`: path `+0x64` and `+0x65` = `dir & 0x3F` | I |
| `0x006E3540` | `g_FacingClass64` | 64 bytes: a direction's quarter (§ 2.16) | I |
| `0x006E353C` | `g_FacingOfClass4` | 4 bytes: the facing of each quarter, 31, 49, 0, 17 (§ 2.16) | I |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`ai-rows.txt` of P1.1, `b3-rows.txt`): 33 `HellMeteor` (1 record), 35 `CorruptArcher` (8), 36
  `CorruptLancer` (9), 37 `SkeletonBow` (11), 38 `MaggotLarva` (6), 39 `PinHead` (6, `blunderbore1..6`), 40 `MaggotEgg`
  (6), 43 `FoulCrowNest` (4), 45 `Sarcophagus` (1), 46 `ElementalBeast` (4), 47 `FlyingScimitar` (1), 48
  `ZakarumZealot` (5), 49 `ZakarumPriest` (6, `cantor1..6`), 52 `FrogDemon` (3), 56 `Tentacle` (3), 57 `TentacleHead`
  (3), 63 `GargoyleTrap` (1): 78 records. (tbl:MonStats.txt:AI)
- [I] Of the 13 rows whose records disagree on which `aip` slots they set (MonStats § AI columns), 35 and 36 are here,
  and in both the disagreement is in slots the code reads only behind a skill test (values `[C]` as data,
  `b3-rows.txt`): `cr_archer1..5` have no skills and `aip6`/`aip7` 0, `cr_archer6..8` have three skills (`MonBow`, an
  arrow skill, a second arrow skill) and set `aip6` 20/25/30 and `aip7` 15, the draws of Skill2 and Skill3 (§ 2.2);
  `aip8`, the walk-stop distance, is 12 in 1–5 and 16 in 6–8. `cr_lancer1..5` have no skills and `aip6`/`aip7` 0,
  `cr_lancer6..8` (two rows named `cr_lancer8`, 617 and 723) have Skill1 `Jab` and a second skill and set `aip6`
  20/25/30 and `aip7` 20, the draws of those skills (§ 2.3). Elsewhere the records differ in values only: row 36's
  `aip4` is 0 in Normal in every record (a lancer never runs to its target in Normal), row 37's `aip5` is 6 in
  `sk_archer1..5` and 12 in 6–11 (the third argument of its approach), row 40's `aip1` (the delay after hatching) is
  250 down to 150 in Normal and 200 above, row 43's `aip3` (the spawn count) 6–15 in Normal up to 15–24 in Hell.
  (tbl:MonStats.txt:aip6, tbl:MonStats.txt:aip8, tbl:MonStats.txt:Skill1)
- [I] Row 37's records 6–11 have Skill1 `SkeletonRaise`; the think function reads no skill column (§ 2.4), so the
  skill is used, if at all, by another path. (0x005F6070–0x005F620C, tbl:MonStats.txt:Skill1)

### 2. The think functions

#### 2.0 The helper `MonAiStepAwayXY` (0x005DF140)

```c
ux = U.x; uy = U.y; ox = o.x; oy = o.y;                                          // u32 compares
sx = ux < ox ? -1 : ux > ox ? 1 : 0;  sy = uy < oy ? -1 : uy > oy ? 1 : 0;
if ((u8)n > 5) AiPathOverrideSet(U's MonPathCtl or 0, 0; 0, n);                  // 0x005DF250-0x005DF26D
return MonAiMove(G, U, 0, 15, ux + (u8)n * sx, uy + (u8)n * sy, 1, f ? 4 : 0);
```

- [I] It moves the unit `n` subtiles away from `o` on each axis where the two differ (a diagonal step when both
  differ), and returns `MonAiMove`'s result, which its callers (rows 35 and 48) take as "done" when non-zero. Called
  also from 0x005E67D0, 0x005E825E, 0x005E8307 and 0x005EBEBB (later batches; unfollowed). No draw in its body
  (`b3-draws.txt`); its callees are not followed. (0x005DF140–0x005DF29C, fn:sub_005DEB60_MonAiMove@0x005DEB60,
  fn:sub_005A6260_AiPathOverrideSet@0x005A6260)

#### 2.1 Row 33 `HellMeteor` (0x005F56D0)

```c
if (Skill1 >= 0 && chance(1)) {                                                  // draw#1
    x = U.x + Range(2*aip3) - aip3;  y = U.y + Range(2*aip3) - aip3;            // RNG_RangeB, draw#2, #3
    return UseSkill(Sk1mode, Skill1, 0, x, y);
}
Idle(aip2);
```

- [I] A point from `−aip3` to `aip3 − 1` (10) off itself on each axis, no target unit. The x getter runs before the first
  `RangeB` and the y getter between the two. Widths: `aip3` s16, `2·aip3` and the sums 32-bit, the position u16
  zero-extended, so nothing wraps. (0x005F56D0–0x005F5828, fn:RNG_RangeB@0x0045C3E0)
- [C] The map. (run:2026-10-30-ai-cat-emu-3, `meteor`)

#### 2.2 Row 35 `CorruptArcher` (0x005F5A20)

```c
r = dist;  h = FindHostile(&r, 0);                                               // r: the hostile's distance
if (!h) { if (draw > 49) return Idle(aip3); return T56(t, 3, 0); }              // draw#1, unsigned
if (!melee && AiMonState3or19(U)) return SetModeAtUnit(4, h);
if (r < 6 && chance(4)) { Ovr(0, 100, 0); if (StepAwayXY(h, 12, 1)) return; }   // draw#1
if (0 < aip8 && aip8 < r && Range(100) < aip1) { Ovr(0, 10, 0); return WalkStop(h, (u8)aip8); }
if (aip5 < r) { Ovr(0, 100, 0); return RunStop(h, (u8)aip5); }
if (!chance(2)) return Idle(aip3);
if (Skill2 >= 0 && Range(100) < aip6) return UseSkill(Sk2mode, Skill2, h, 0, 0);
if (Skill3 >= 0 && Range(100) < aip7) return UseSkill(Sk3mode, Skill3, h, 0, 0);
if (Skill1 < 0) return SetModeAtUnit(4, h);
return UseSkill(Sk1mode, Skill1, h, 0, 0);
```

- [I] After `FindHostile` every distance test reads `r`, the hostile's distance (`0x7FFFFFFF` without one; ai/0001
  § 6), not the event's; every command after it is aimed at the hostile `h`, the no-hostile wander at `t`. Closer than
  6 the archer steps 12 away (on `aip4`, 20–60); past `aip8` (12 or 16) it walks to that distance on `aip1`; past
  `aip5` (20 or 24) it runs to it; otherwise it shoots on `aip2` (70–99), Skill2 and Skill3 tried first in 6–8, and 1–5
  use A1 (no Skill1). The `aip8` test is `movzx` s16 then `jle` on the 16-bit `test`, signed. Up to five draws.
  (0x005F5A20–0x005F5D3E, fn:sub_005DDC30_MonAiFindHostile@0x005DDC30, fn:sub_005DF140_MonAiStepAwayXY@0x005DF140,
  tbl:MonStats.txt:aip8)
- [I] Not emulated: `FindHostile` is the function's first call (0x005F5A51, § 3).

#### 2.3 Row 36 `CorruptLancer` (0x005F5D50)

```c
if (dist > aip5) { PathSetStopDist(U.path, M2.MeleeRng); Ovr(13, 100, 0);
                   RunStop(t, M2.MeleeRng); ctl->v14 = 1; return; }               // the charge
if (!melee) {
    if (!chance(1)) return Idle(aip3);                                           // draw#1
    PathSetStopDist(U.path, M2.MeleeRng);
    if (!chance(4)) return WalkStop(t, 3);                                       // draw#2
    Ovr(13, 100, 0); return RunStop(t, M2.MeleeRng);
}
if (ctl->v14 == 0 && !chance(2)) return Idle(aip3);                              // draw#1
ctl->v14 = 0;
if (Skill1 >= 0 && chance(6))       return UseSkill(Sk1mode, Skill1, t, 0, 0);   // Jab
if (Skill2 >= 0 && Range(100) < aip7) return UseSkill(Sk2mode, Skill2, t, 0, 0);
if (Skill3 >= 0 && Range(100) < aip8) return UseSkill(Sk3mode, Skill3, t, 0, 0);
SetModeAtUnit(4, t);
```

- [I] `M2.MeleeRng` is the MonStats2 byte `+0x0E` (`MeleeRng`). After a charge (`v14` = 1) the first melee decision
  attacks without the `aip2` draw. Up to four draws. (0x005F5D50–0x005F6067, fn:sub_00649070_PathSetStopDist@0x00649070,
  tbl:MonStats2.txt:MeleeRng, struct:AiCtl+0x14)
- [C] The map. (run:2026-10-30-ai-cat-emu-3, `lancer`)

#### 2.4 Row 37 `SkeletonBow` (0x005F6070)

```c
r = dist;
if (AiMonState3or19(U) && (h = FindHostile(&r, 0))) return SetModeAtUnit(4, h);
h = FindHostile(&r, 0);
if (!h || r > 19) { if (chance(3)) return Toward(t, aip4, aip5); return Idle(20); }   // draw#1
if (chance(1)) return SetModeAtUnit(4, h);                                       // draw#1
if (draw < 20) return T56(t, 3, 0);                                              // draw#2
Idle(aip2);
```

- [I] Shoots (A1) at its own hostile within 19 on `aip1` (75–99), else repositions on 20 percent; beyond 19 or with no
  hostile it approaches the event's target on `aip3` (50). No skill column is read. (0x005F6070–0x005F620C,
  fn:sub_005DE6D0_MonAiWalkTowardUnit@0x005DE6D0)
- [C] The state test up to the first or second `FindHostile`, the pointer argument (`EBP + 8`, the `ctx` slot holding
  `dist`) included; no draw before it. (run:2026-10-30-ai-cat-emu-3, `skelbow`)

#### 2.5 Rows 38 `MaggotLarva` (0x005F6220) and 39 `PinHead` (0x005F6340)

```c
// row 38
if (!melee) { ctl->v14 = 0; if (chance(3)) return Walk(t, 1); return Idle(aip4); }
if (ctl->v14 == 0 && chance(1)) { ctl->v14 = 1; return SetModeAtUnit(4, t); }
ctl->v14 = 0; Idle(aip2);
// row 39
if (!melee) { ctl->v14 = 0; if (chance(3)) return Walk(t, 7); return Idle(aip4); }
if (ctl->v14 != 0 && !chance(1)) return Idle(aip2);                              // draw#1
ctl->v14 = 1;
if (Skill1 >= 0 && chance(5)) return UseSkill(Sk1mode, Skill1, t, 0, 0);         // Smite
if (Skill2 >= 0 && chance(6)) return UseSkill(Sk2mode, Skill2, t, 0, 0);
SetModeAtUnit(4, t);
```

- [I] The larva alternates an attack with a wait (`v14` set by the attack, cleared by the next decision). The pin head
  skips the `aip1` wait draw on its first melee decision (`v14` = 0) and makes it after that; the skill draws come
  after it either way. (0x005F6220–0x005F6336,
  0x005F6340–0x005F6529, struct:AiCtl+0x14)
- [C] Both maps. (run:2026-10-30-ai-cat-emu-3, `larva`, `pinhead`)

#### 2.6 Row 40 `MaggotEgg` (0x005F6530)

```c
if (Skill1 >= 0 && ctl->v14 != 1 && chance(2)) {                                 // draw#1
    UseSkill(Sk1mode, Skill1, t, 0, 0); Delay(aip1); ctl->v14 = 1; return;       // hatch
}
if (ctl->v14 == 1) UnitKilled(G, U, UNIT_GetTargetUnit(G, U), 1);                // no return
Idle(aip1);
```

- [I] One hatch per egg: after it, the next event kills the egg with its own last target as the killer and still
  queues `Idle(aip1)` (0x005F6601–0x005F6614, no jump between the two calls). (0x005F6530–0x005F661F,
  fn:UNIT_GetTargetUnit@0x00553540, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- [C] The map up to the skill, `UNIT_GetTargetUnit` (its stack arguments `G`, `U` and `UnitKilled`'s pending 1) or
  the idle. (run:2026-10-30-ai-cat-emu-3, `egg`)

#### 2.7 Rows 43 `FoulCrowNest` (0x005F6650) and 45 `Sarcophagus` (0x005F6A10)

```c
// init 0x005F6630 (both rows): ctl->v14 = T; ctl->v18 = 0;
if (dist > R) return Idle(25);                                                   // R = 20 (43), 25 (45)
if (ctl->v18 >= aip3 /* 43 */ || ctl->v18 > aip3 /* 45 */) {
    U->flagsC4 |= 0x20000; return SetMode(0, 0, 0);                              // die
}
e = |T - ctl->v14|;                                                              // 32-bit sub, then neg if negative
if (Skill1 >= 0 && e >= aip1) {
    [43: ctl->v14 = T;]
    cls = MonStatsCount > C ? C : -1;                                            // C = 206 (43), 228 (45)
    if (SpawnClassCellTest(cls, UnitGetRoom(U), U.x, U.y, 0)) {
        ctl->v18++; [45: ctl->v14 = T;]  return UseSkill(Sk1mode, Skill1, t, 0, 0);   // Nest
    }
}
Idle(20 + draw10);                                                               // draw10 = low mod 10, draw#1
```

- [I] Every `aip1` frames (100/80/70 for the nests, 125/110/90 for the sarcophagus) the spawner uses its `Nest` skill
  if the cell where it stands passes `SpawnClassCellTest` for MonStats row 206 (`crownest1`, for all four nest
  records) or 228 (`sarcophagus`); the class compare is inlined as `((count > C) − 1 & mask) + C`. After `aip3` spawns
  (43) or `aip3 + 1` (45) it dies. The nest moves its timer to `T` before the cell test, so a failed test waits a full
  `aip1` again; the sarcophagus moves it only on success and tries again at the next event. The only draw is the
  idle's `low mod 10` (the inline `0xCCCCCCCD` divide, unsigned). `e` cannot wrap on a timer that holds a past frame;
  for `T − v14 = −2³¹` the `neg` leaves `−2³¹`, below any `aip1`. (0x005F6630–0x005F6649, 0x005F6650–0x005F67A9,
  0x005F6A10–0x005F6B69, fn:sub_005FD350_SpawnClassCellTest@0x005FD350, fn:sub_00620BB0_UnitGetRoom@0x00620BB0,
  struct:Unit+0xC4)
- [C] Both maps up to `SpawnClassCellTest` (its `ECX` class, `EDX` room and the position arguments), the death
  command (with `Unit+0xC4`) or an idle. (run:2026-10-30-ai-cat-emu-3, `nest`, `sarco`)

#### 2.8 Row 46 `ElementalBeast` (0x005F6B70)

```c
switch (ctl->v14) {
case 2: return UnitKilled(G, U, t, 1);
case 0: if (dist < aip2 || AiMonState3or19(U)) { SetModeAtUnit(8, t); ctl->v14 = 1; return; }
        return Idle(aip3);
case 1: if (melee) { SetModeAtUnit(8, t); UnitQueueEvent(G, U, 0, T + 1, 0, 0); ctl->v14 = 2; return; }
        if (Range(100) < aip1) return Walk(t, 0);                                // draw#1
        return Ring(8);
default: return Idle(aip3);
}
```

- [I] The orb casts S1 once when the target comes within `aip2` (16–24), flies at it (`aip1` 20 percent a walk, else a
  ring), and in melee range casts S1 again and queues a kind-0 event (the mode frame event, anim/0001; code 0, index 0) at
  `T + 1`, then dies at the event after (killer: the target). (0x005F6B70–0x005F6C9B, fn:sub_005417D0_UnitQueueEvent@0x005417D0, struct:AiCtl+0x14)
- [C] The map. (run:2026-10-30-ai-cat-emu-3, `beast`)

#### 2.9 Row 47 `FlyingScimitar` (0x005F6CA0)

```c
if (!melee) {
    if (chance(1)) return Toward(t, 8, 1);                                       // draw#1
    if (chance(1)) return Walk(t, 7);                                            // draw#2, aip1 again
} else {
    if (chance(2)) return SetModeAtUnit(4, t);                                   // draw#1
    if (chance(4)) return T56(t, 2, 0);                                          // draw#2
}
Idle(aip3);
```

- [I] Both approach draws read `aip1` (90). The second step of each branch reuses the multiplier held in a register
  (3 immediate sites for 4 steps, `b3-draws.txt`). (0x005F6CA0–0x005F6E17)
- [C] The map. (run:2026-10-30-ai-cat-emu-3, `scimitar`)

#### 2.10 Row 48 `ZakarumZealot` (0x005F6E60)

```c
run = 0;
if (Velocity > 0) { run = Run*100/Velocity - 100; if (run < 1) run = 0; if (run >= 120) run = 120; }  // idiv, trunc
life = UnitLifePct(U);
if (t) {
    p = t;
    if (t->type == 1) { MonsterOwnerRef(t, &guid, &type); if (type == 0) p = GameFindUnit(G, 0, guid); }
    if (p && p->type == 0 && DRLG_ActFromLevelId(RoomGetLevelId(UnitGetRoom(U))) == 2
          && QUESTRECORD_GetState(PlayerData(p)->quests[d], 21, 0)) {
        Ovr(0, run, 0); if (StepAwayXY(t, 8, 1)) return; return Ring(6);
    }
}
if (AiMonState3or19(U)) {
    if (ctl->v18 == 0 && life < aip3) {
        ctl->v14 = 0; Ovr(0, run, 0); if (StepAwayXY(t, 8, 1)) return; ctl->v18 = 5;
    }
    if (COLL_CellTestAt(UnitGetRoom(U), U.x, U.y, 0x40))
        return melee ? T56(t, 4, 0) : Walk(t, 7);
}
if (ctl->v18) ctl->v18--;
if (!melee) { ctl->v14 = 0; if (!chance(4)) return Walk(t, 7); Ovr(0, run, 0); return Run(t); }   // draw#1
if (ctl->v14 && !chance(1)) {                                                    // draw#1
    ctl->v14 = 0; if (Range(100) < 80) return Idle(10); return T56(t, 4, 0);     // draw#2
}
ctl->v14 = 1;
SetModeAtUnit(chance(2) ? 5 : 4, t);                                             // draw#1 or #2
```

- [I] **The act III truce.** In an act III level (act index 2) a zealot whose target is a player, or a monster whose
  owner record names a player (`MonsterOwnerRef` type 0, found by GUID), steps 8 away from it and wanders when that
  player's quest record of the game's difficulty has quest word 21 bit 0 (the word the Durance portal tests, d2s.md
  MP27). `run` is the override parameter from MonStats `Run`/`Velocity` (`+0x34`/`+0x32`, s16, signed `idiv`), 0–120.
  (0x005F6E60–0x005F6F7D, fn:sub_0058F090_MonsterOwnerRef@0x0058F090, fn:DRLG_ActFromLevelId@0x006427F0,
  fn:UNIT_GetPlayerData@0x006221A0, fn:QUESTRECORD_GetState@0x0065C310, tbl:MonStats.txt:Run, tbl:MonStats.txt:Velocity)
- [I] **The rest.** With `MonsterData+0x54` 3 or 19 and life below `aip3` (35–50) it steps away once and then holds a
  five-decision cooldown in `v18`; with that state and a cell that fails mask `0x40` it moves. Otherwise it walks or
  runs (`aip4`, 50–90, the run share) out of melee range, and in melee range attacks with A2 on `aip2` (50–65) or A1,
  pausing after an attack on `aip1`. Up to two draws. (0x005F6F7D–0x005F722F, fn:COLL_CellTestAt@0x0064CB30,
  struct:AiCtl+0x18, tbl:MonStats.txt:aip3)
- [I] Not emulated: `UnitLifePct` is the function's first call (0x005F6EC6, § 3).

#### 2.11 Row 49 `ZakarumPriest` (0x005F72D0)

```c
life = UnitLifePct(U);
if (melee || AiMonState3or19(U)) {
    if (Skill3 >= 0 && life < 33 && T > ctl->v14) {                              // MonTeleport
        ctl->v14 = T + 4*aip5;  s = melee ? 2 : 0;
        x = t.x + ((t.x - U.x) << s);  y = t.y + ((t.y - U.y) << s);
        if (MonSkillTargetOk(Skill3, 0, x, y)) return UseSkill(Sk3mode, Skill3, 0, x, y);
    }
    if (melee && chance(1)) return SetModeAtUnit(4, t);                          // draw#1
}
s = { unit 0, count 0, best 0x7FFFFFFF, bound aip6² };
AiUnitSearch(G, U, &s, AiZakarumHealCb, 1);
if (Skill1 >= 0 && s.unit && draw < 25) return UseSkill(Sk1mode, Skill1, s.unit, 0, 0);   // ZakarumHeal
if (!AiLineClear(U, t)) {
    if (chance(1) && Skill4 >= 0 && ctl->v18 < T && Range(100) < aip2) goto blizzard;
} else if (chance(4)) {
    if (Skill4 >= 0 && ctl->v18 < T && Range(100) < aip2) {
blizzard: UseSkill(Sk4mode, Skill4, t, 0, 0); ctl->v18 = T + aip5; return; }       // MonBlizzard
    if (Skill2 >= 0 && ctl->v1C < T && Range(100) < aip3) {
        UseSkill(Sk2mode, Skill2, t, 0, 0); ctl->v1C = T + 20; return; }          // ZakarumLightning
}
if (draw < 30) return T56(t, 4, 0);
Idle(20);
```

- [I] **The teleport** goes to the far side of the target: the target's point plus the unit-to-target offset (×4 in
  melee range, ×1 otherwise), with a `4·aip5` (480) frame cooldown in `v14`; below 33 percent life only. The first
  `GetSubX/Y` pair is the unit's, the second the target's (`ECX` = `[ebp−4]` then `[ebp+8]`, 0x005F7350–0x005F737B).
  The offset is a u16 difference, so `<< 2` cannot wrap. **The heal** goes on 25 percent (unsigned compare) to the
  unit the search keeps (§ 2.12). **Blizzard** (Skill4) has a `v18` cooldown of `aip5` (120) frames, Skill2 a `v1C` of
  20. A blocked line to the target (`AiLineClear` 0: `UnitLineBlocked(U, t, 4)` non-zero) allows only Blizzard, on
  `aip1` then `aip2`; a clear line allows both on `aip4` then `aip2`/`aip3`. Up to six draws. (0x005F72D0–0x005F76F1, fn:sub_005FD470_MonSkillTargetOk@0x005FD470,
  fn:sub_005DD290_AiLineClear@0x005DD290, fn:sub_005DD0B0_AiUnitSearch@0x005DD0B0, struct:AiCtl+0x1C)
- [I] Not emulated: `UnitLifePct` is the function's first call (0x005F72F9, § 3).

#### 2.12 Row 49's callback `AiZakarumHealCb` (0x005F7240)

- [I] Takes a monster other than the searcher, `AlignSame02` with it, alignment not 2, not in a death mode, whose
  `MonClassCheck(MonBaseId)` is 235 (`zealot1`) or 238 (`cantor1`), with `UnitDistSq ≤ bound` and `UnitLifePct ≤ 60`;
  each such unit adds one to `+0x04` and becomes `+0x00`, since `+0x08` stays `0x7FFFFFFF` (written only when below 1)
  and every life is below it. Returns 0 (the search goes on). Block `{+0x00 unit, +0x04 count, +0x08 best, +0x0C
  bound}` at `EBP − 0x4C`. (0x005F7240–0x005F72CC, fn:sub_00650D70_AlignSame02@0x00650D70,
  fn:sub_006259B0_UnitAlignGet@0x006259B0, fn:sub_00463900_MonClassCheck@0x00463900, fn:sub_00621F20_UnitLifePct@0x00621F20)

#### 2.13 Row 52 `FrogDemon` (think 0x005F8260, alt 0x005F81D0)

```c
// think: v1C 0 = start, 1 = submerged, 2 = surfaced (`Submerge` = Skill1, `Emerge` = Skill2)
if (ctl->v1C == 0) {
    if (Skill1 >= 0 && dist > 12) { UseSkill(Sk1mode, Skill1, t, 0, 0); Delay(8); ctl->v1C = 1;
                                    AiVultureTakeOff(G, U); return; }
    if (Skill2 >= 0 && AiVultureLand(G, U)) goto emerge;
    if (!COLL_CellTestAt(UnitGetRoom(U), U.x, U.y, 0xC01)) ctl->v1C = 2;
    return Idle(12);
}
if (ctl->v1C == 1) {
    if (Skill2 >= 0 && (dist < aip8 && AiVultureLand(G, U)
                        || dist < 20 && ctl->v18 > 64 && AiVultureLand(G, U))) {
emerge: UseSkill(Sk2mode, Skill2, U, 0, 0); ctl->v1C = 2; return; }
    AiVultureTakeOff(G, U); Delay(24); ctl->v18++; ctl->v1C = 1; return;
}
if (!t) return Delay(32);
if (melee) {
    if (Range(100) < aip2) return SetModeAtUnit(5, t);
    if (Range(100) < aip1) return SetModeAtUnit(4, t);
    if (Range(100) < aip3) return T56(t, 3, 0);
    return Delay(aip7);
}
if (dist < aip6) {
    if (Range(100) < aip5) return SetModeAtUnit(5, t);
    if (Range(100) < aip4) return T56(t, 4, 0);
    return Delay(aip7);
}
if (Range(100) < aip4) return T56(t, 3, 0);
WalkStop(t, 4);
// alt
if (ctl->state != 10 && ctl->state != 11 && Skill1 >= 0 && ctl->v1C >= 2) {
    UseSkill(Sk1mode, Skill1, t, 0, 0); ctl->v1C = 1; return AiVultureTakeOff(G, U);
}
MonAiInit(G, U, ctl, ctl->state); Delay(1);
```

- [I] The frog uses the vulture's take-off and landing helpers (ai/0003 § 2.7, the collision off and on) for its
  submerge and emerge. Submerged, it surfaces within `aip8` (9) of its target, or within 20 after more than 64
  submerged events; each failed event adds one to `v18`. Kind 5: with no target a surfaced frog delays 32. The `alt`
  runs when `MonAiInit` swaps the think function (ai/0001 § 4): a surfaced frog whose state changes to anything but
  10 or 11 submerges first; otherwise it re-runs `MonAiInit`, which installs the row's think. The skill's `x, y` are 0
  (the pushed `EDX` is the zero `v1C`, 0x005F82A7). Up to three draws. (0x005F8260–0x005F85B8, 0x005F81D0–0x005F8254,
  fn:sub_005F2EB0_AiVultureTakeOff@0x005F2EB0, fn:sub_005F2FC0_AiVultureLand@0x005F2FC0,
  fn:sub_005B0E00_MonAiInit@0x005B0E00, struct:AiCtl+0x1C)
- [C] Both maps up to the first callee: the landing helper, the cell test (its stack arguments, room, `U.x`, `U.y`,
  `0xC01`), the take-off, the commands and delays. (run:2026-10-30-ai-cat-emu-3, `frog`, `frogalt`)

#### 2.14 Row 56 `Tentacle` (0x005F8F80)

```c
o = MonsterOwner(U);
if (!o) return UnitKilled(G, U, 0, 1);
if (o->mode == 12 && draw < 40) return UnitKilled(G, U, UNIT_GetTargetUnit(G, o), 1);   // draw#1, unsigned
if (Skill1 >= 0) {                                                                       // Submerge
    if (ctl->v1C == 0) goto submerge8;
    if (ctl->v1C == 2 && ctl->v18 < T &&
        (dist > aip6 || !melee && Range(100) < aip2 || o->mode == 14 && Range(100) < 50)) {
submerge8: UseSkill(Sk1mode, Skill1, t, 0, 0); Delay(8); ctl->v18 = T + 25*aip3; ctl->v1C = 1; return; }
}
if (Skill2 >= 0) {                                                                       // Emerge
    if (ctl->v1C != 1) goto act;
    if (ctl->v18 < T && (melee || dist < aip6 || o->mode != 14 && Range(100) < 5)) {
        UseSkill(Sk2mode, Skill2, U, 0, 0); ctl->v18 = T + 25*aip4; ctl->v1C = 2; return; }
}
if (ctl->v1C == 1) return Delay(aip5);
act: if (melee && Range(100) < aip1) return SetModeAtUnit(4, t);
Idle(aip5);
```

- [I] A tentacle follows its owner, the head (row 57): it dies when it has none, and with 40 percent per event once
  the owner is in mode 12 (DD), the owner's target the killer; it submerges with 50 percent while the owner is in mode
  14 (SQ) and surfaces by itself (5 percent) only while it is not. Timers: `25·aip3` frames submerged at least
  (300–400), `25·aip4` surfaced (300–400). `25·aip` is 32-bit and fits for every s16 (`25 · 32767 = 819 175`); the
  sum with `T` wraps only past frame `2³¹ − 819 176`. Up to four draws. (0x005F8F80–0x005F9263,
  fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, struct:AiCtl+0x18)
- [I] Not emulated: `MonsterOwner`'s `GameFindUnit` is reached before the first draw (0x005F8FAC, § 3).

#### 2.15 Row 57 `TentacleHead` (0x005F9270)

```c
// row 56 without the owner: no death test, no mode-14 terms
if (Skill1 >= 0) {
    if (ctl->v1C == 0) { UseSkill(Sk1mode, Skill1, t, 0, 0); Delay(8); goto arm; }
    if (ctl->v1C == 2 && ctl->v18 < T && (dist > aip6 || !melee && Range(100) < aip2)) {
        UseSkill(Sk1mode, Skill1, t, 0, 0); Delay(20);
arm:    ctl->v18 = T + 25*aip3; ctl->v1C = 1; return; }
}
if (Skill2 >= 0 && ctl->v1C == 1 && ctl->v18 < T && (melee || dist < aip6)) {
    UseSkill(Sk2mode, Skill2, U, 0, 0); ctl->v18 = T + 25*aip4; ctl->v1C = 2; return; }
if (ctl->v1C == 1) return Delay(aip5);
r = dist; h = FindHostile(&r, 0);
if (chance(1)) return SetModeAtUnit(4, h);                                       // draw after the search
Idle(aip5);
```

- [I] The head surfaces only when the target is close (melee or within `aip6`, 12–14), never by chance, and its A1 is
  aimed at its own hostile `h`, which may be 0 when `FindHostile` finds none (the call is made with it). Its later
  submerges delay 20, the first 8. (0x005F9270–0x005F947E, fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)
- [C] The map up to the skills, the delay or `FindHostile` (the word at its pointer argument, `EBP − 4`, holding
  `dist`). (run:2026-10-30-ai-cat-emu-3, `thead`)

#### 2.16 Row 63 `GargoyleTrap` (0x005F9490)

```c
if (ctl->v14 > 0) { Idle(ctl->v14); ctl->v14 = 0; return; }                     // the cooldown after a shot
UnitSetPathTargetUnit(U, t);
dx = t.x - U.x;  dy = t.y - U.y;
(px, py) = |dx| < |dy| ? (U.x, t.y) : (t.x, U.y);                                 // the point on the unit's row or column
PathSetFacing(U.path, g_FacingOfClass4[g_FacingClass64[(u8)UnitDirToPoint(U, px, py)]]);
if ((|dx| <= 5 || |dy| <= 5) && Skill1 >= 0 && dist < aip1 && chance(2)) {       // draw#1
    UseSkill(Sk1mode, Skill1, t, 0, 0); ctl->v14 = aip3; return; }
Idle(aip4);
```

- [I] The trap turns to one of four facings and shoots only at a target within 5 subtiles of its row or column, within
  `aip1` (24–28), on `aip2` (20/50/80); the event after a shot idles `aip3` (12/10/8) frames, a decision without a shot idles `aip4`
  (15/7/0).
  `UnitDirToPoint`'s low byte indexes the 64-byte table at 0x006E3540, whose quarter indexes the four bytes at
  0x006E353C (`b3-dirtab.txt`): directions 57–63 and 0–8 → 31, 9–24 → 49, 25–40 → 0, 41–56 → 17. (0x005F9490–0x005F96B0,
  fn:sub_00621DC0_UnitDirToPoint@0x00621DC0, fn:sub_006488A0_PathSetFacing@0x006488A0, data:g_FacingClass64@0x006E3540,
  data:g_FacingOfClass4@0x006E353C)
- [C] The cooldown test up to `Idle` or `UnitSetPathTargetUnit` (no draw before them).
  (run:2026-10-30-ai-cat-emu-3, `garg`)

#### 2.17 Effects of rows 40, 46 and 56 on the unit's life

- [I] The three `UnitKilled(G, U, killer, 1)` calls pass the killer on the stack and the trailing 1 (pushed first):
  0x005F65F3–0x005F6601 (egg), 0x005F6BA2–0x005F6BA9 (beast), 0x005F8FB8–0x005F8FBF and 0x005F9012–0x005F9020
  (tentacle). What `UnitKilled` does with the killer (the drop and quest paths of items/0010) is not read here.
  (fn:sub_0057CCB0_UnitKilled@0x0057CCB0)

#### 2.18 The parameter list and the action helpers

- [I] No function of the batch calls `AiParamsHead`, `AiParamsPush` or `AiParamsPop`, and none calls the action
  helpers 0x005DF850, 0x005DF990, 0x005DFA00 or 0x005DFBF0 (`grep -c 'call   0x5df850\|call   0x5df990\|call
  0x5dfa00\|call   0x5dfbf0' b3-asm.txt`: 0). (`b3-asm.txt`)

### 3. Emulation (run:2026-10-30-ai-cat-emu-3)

- [C] Fourteen families, 240 cases each, 3 360 cases, all matching, none stopped, no traced access outside the
  declared memory (`emu/check.txt`). Each case runs one think function (or row 52's alt) on a declared image (the
  docstring of `tools/ai_cat_emu3.py`) and ends at the first observed callee; the checker compares the callee, the call
  site (the return address), `ECX`/`EDX` where the callee takes them, the stack arguments, the unit seed,
  `AiCtl+0x14/+0x18/+0x1C`, `Unit+0xC4` and, at a `FindHostile` boundary, the word its pointer argument addresses
  (`EBP + 8` or `EBP − 4`, from the stack dump). Callees run on the declared image rather than observed: `RNG_Range`,
  `RNG_RangeB`, `AiMonState3or19` with `MonData54Get`, `UnitGetSubX/Y` with `PathGetX/Y`, and `UnitGetRoom` with
  `PathGetRoom`. Controls: `le` (each draw compared with `<=`) and `d0` (every `aip` from the Normal column) fail every
  case they separate, and the site control (each call site one byte later) fails every case
  (run:2026-10-30-ai-cat-emu-3):

  | family | row | boundaries reached | cases with a draw | `le` separating | `d0` separating |
  |---|---:|---:|---:|---:|---:|
  | `meteor` | 33 | 2 | 157 | 16 | 151 |
  | `lancer` | 36 | 8 | 160 | 25 | 106 |
  | `skelbow` | 37 | 2 | 0 | 0 | 0 |
  | `larva` | 38 | 4 | 153 | 20 | 131 |
  | `pinhead` | 39 | 6 | 237 | 23 | 116 |
  | `egg` | 40 | 3 | 110 | 11 | 98 |
  | `nest` | 43 | 4 | 28 | 0 | 48 |
  | `sarco` | 45 | 4 | 79 | 0 | 84 |
  | `beast` | 46 | 6 | 49 | 5 | 46 |
  | `scimitar` | 47 | 5 | 240 | 35 | 120 |
  | `frog` | 52 | 14 | 95 | 18 | 54 |
  | `frogalt` | 52 alt | 2 | 0 | 0 | 0 |
  | `thead` | 57 | 5 | 18 | 3 | 27 |
  | `garg` | 63 | 2 | 0 | 0 | 0 |

  `skelbow`, `frogalt` and `garg` reach their boundaries with no draw and no `aip` read, so no control separates them;
  their `[C]` is the map of their state, mode and timer tests only. The `nest` and `sarco` draw (the idle's
  `low mod 10`) is compared with nothing, so `le` cannot separate it, and `d0` only moves the `aip` column, not the
  direction of a compare. The draw is checked by its value (the `Idle` argument `seed mod 10 + 20` and the moved seed
  match in all 28 and 79 drawing cases). Two substitute controls, run at the lane check on the kept outputs
  (`workspace/logs/r52d/ctl-nest-sarco.py`, output `ctl-nest-sarco.txt`, both in the manifest): the death compare
  flipped (`>=` for `>` and back) separates 53 nest and 72 sarcophagus cases and fails all of them; the range test
  moved by one (`dist > R+1`) separates 30 and 24 and fails all of them. The cases do reach the equality edges of
  the death and range tests; the `e >= aip1` edge has no control. Not covered: every callee and everything after it.
  (run:2026-10-30-ai-cat-emu-3)
- [I] **The development runs** (rule 6): `emu/dev-1/` (3 360 cases, all matching, with the case writer before the
  nest, sarcophagus, elemental beast and tentacle head tuning) and `emu/dev-2/` (3 360 cases, all matching, before the
  tentacle head's distance tuning), each checked by its own copy of the tool (`ai_cat_emu3.py.rev`); the models are
  the same in all three runs, and no kept output was written over a development one. (run:2026-10-30-ai-cat-emu-3)
- [I] Not emulated: rows 35 and 37 past their `FindHostile`, 48 and 49 (`UnitLifePct` first), 56 (`MonsterOwner`'s
  `GameFindUnit` first). Each reaches, before its first draw, a callee whose read set is not declarable in a small
  image, so an observed boundary there ends each case before its first draw. Phase 2's logs reproduce them (rows 35
  and 37 are tier AIs). (fn:sub_005F5A20_AiCorruptArcher@0x005F5A20, fn:sub_005F6E60_AiZakarumZealot@0x005F6E60,
  fn:sub_00621F20_UnitLifePct@0x00621F20)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip8 (`+0x56 + 6(k−1) + 2d`), tbl:MonStats.txt:Skill1 … Skill4
  (`+0x170 + 2(k−1)`), tbl:MonStats.txt:Sk1mode … Sk4mode (`+0x180 + (k−1)`), tbl:MonStats.txt:Velocity (`+0x32`),
  tbl:MonStats.txt:Run (`+0x34`), tbl:MonStats2.txt:MeleeRng (`+0x0E`), the MonStats count `g_pDataTables+0xA80` (the
  class compares of rows 43 and 45).
- struct:AiCtl+0x00, struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtx+0x14, struct:AiCtx+0x18,
  struct:AiCtx+0x20, struct:MonsterData+0x54, struct:Unit+0x10, struct:Unit+0x2C, struct:Unit+0xC4,
  struct:Game+0x6D, struct:Game+0xA8, the player data's quest records `+0x10 + 4d` (row 48).

## Dead ends

- None in the batch's own code. The decompile of row 49 shows a stray `local_1c = high(low·M)` before each inline draw
  (the high half of the multiply saved for the carry); objdump shows it is the step's own `mul`.

## Open questions

- Who writes `MonsterData+0x54` (the 3-or-19 test, rows 35, 37, 46, 48, 49): still unnamed (ai/0001's open question).
- Row 37's records 6–11 carry `SkeletonRaise` as Skill1 and the think function reads no skill: which path uses it,
  if any (a later batch's raise helper, or none).
- What `UnitKilled`'s killer argument does for the three self-kills (§ 2.17): the egg names its last target, the
  beast the event's target, the tentacle its head's target; a P2 log of an egg hatching settles whether the target is
  credited.
