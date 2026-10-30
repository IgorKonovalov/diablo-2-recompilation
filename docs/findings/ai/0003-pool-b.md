# 0003 — Catalogue batch 2 (pool-B): the think functions of AI rows 17–30

> **Subsystem:** monsters/ai
> **Question:** for each AI table row of batch 2 (17 `SandLeaper` … 30 `Fetish`), what does its think function do on
> an AI event: which `aip` slots and MonStats columns it reads, which AI-control words it keeps, which draws it makes on
> which seed and in which order, and which command, skill or path request it ends in?
> **Date:** 2026-10-30   **Plan:** 0052 (Phase 1, batch P1.2, catalogue batch 2)   **Status:** for review (`lane/r52c`)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-r52c`, decompiled with the scratch
`__fastcall` signatures of batch 1 carried onto the current `re/symbols.csv`, `b2-sym-scratch.csv`; a reading aid, not
symbol rows) and objdump (`b2-asm.txt`, the batch's range `0x005F20A0`–`0x005F56D0`), then emulation of eight think
functions, part of a ninth and row 29's `alt` under ADR-0015/ADR-0021 (§ 3, run:2026-10-30-ai-cat-emu-2). Kept outputs
are under `workspace/logs/r52c/` (manifest `manifest.sha256`, one path base: that directory; the emulation under
`emu/`, its own manifest; the development run under `emu/dev-1/`, its own manifest). Stock values come from
`b2-rows.txt` (`python3 -I tools/ai_survey.py rows workspace/merged/data/global/excel <row>` for the 14 rows, 103
records). Every register argument quoted below was read from objdump (`b2-asm.txt`); the multiplier sites and RNG calls
per function are counted by `b2-draws.py` (`b2-draws.txt`). The machinery (the AI event, the row kinds, the command and
move helpers, the path override) is [ai/0001](0001-machinery.md), the notation and the helpers first read in batch 1
are [ai/0002](0002-pool-a.md) § Notation and § 4; names below are `re/symbols.csv` names.

**Notation** as ai/0002: `G`, `U`, `t` = `ctx+0x08`, `dist` = `ctx+0x14`, `melee` = `ctx+0x18`, `ctl` = `ctx+0x00`,
`M` = `ctx+0x1C`, `d` = `G+0x6D`; `aipK` the s16 at `M + 0x56 + 6(K−1) + 2d`; `draw` one step of the acting unit's seed
`U+0x20/+0x24`, mod 100; `chance(K)` = `draw < aipK` signed; `Range(n)` = `RNG_Range(U seed, n)` (the same step,
`low mod n`). `ctl->v14`, `v18`, `v1C` are `AiCtl+0x14/+0x18/+0x1C`. Helper short names: `SetModeAtUnit(m, t)`,
`Idle(n)`, `Delay(n)` (`MonAiDelay`), `Walk(t, f)`, `Walk13(t, f)` (`MonAiWalkToUnitType13`), `Ring(r)`, `T56(t, b, f)`,
`StepAway(t, n, f)`, `Toward(t, max, ring)` (`MonAiWalkTowardUnit`), `Ovr(type, param, byte)`. Modes are MonMode
rows: 4 A1, 5 A2, 7 SC, 8 S1, 9 S2, 10 S3, 11 S4.

## Answer (summary)

- [I] **The batch.** Fourteen think functions, each `(ECX game, EDX unit; ctx)` with `ret 4`, one per row; row 29
  `BatDemon` also has an `alt` (0x005F4FD0); no row has an `init`. Every row is kind 1 (the think function runs only
  with a target, `ai-rows.txt` of P1.1), so `t` is never null inside them and the `t == 0` tests of rows 23, 25 and 27
  are not reached from the row. (data:g_MonAiTable@0x0073CA18, fn:sub_005B1650_MonAiTargetByKind@0x005B1650)
- [I] **The common shape** of batch 1 again: in melee range one or two `chance` draws choose A1 or A2, out of it one draw
  chooses an approach or a wait. Rows 17, 19 and 21 are close to that; the others add skills (17, 20, 22, 24, 26, 27,
  28), a unit search (18, 22, 23, 25), a parameter record (20, 30), the target's or the unit's life (23, 26, 28, 29,
  30), and a state machine in `AiCtl+0x14` (20, 23–30: a circle flag, a flight counter, a dance step, a flee flag, a
  skill phase, a perch phase, a hit-and-run phase). (§ 2, fn:sub_005F2540_AiScarab@0x005F2540,
  fn:sub_005F3170_AiVulture@0x005F3170, fn:sub_005F39B0_AiWillOWisp@0x005F39B0, struct:AiCtl+0x14)
- [C] **The decision maps of eight functions** (rows 17, 18, 19, 20, 21, 22, 24, 27) from their declared inputs to the
  first callee they reach match the emulation in all 1 920 cases: the callee, its call site, its register and stack
  arguments, the unit seed, `AiCtl+0x14/+0x18` at the call and, where the callee is `AiUnitSearch`, the search block it
  is handed; and row 30's record test and row 29's `alt` (480 cases, no draw before their boundaries, so no control
  separates them). The `<=` and Normal-column controls and the site control fail every case they separate. The `[C]`
  ends at that callee (ADR-0021). (run:2026-10-30-ai-cat-emu-2, § 3)
- [I] **Draws.** Every draw of the fourteen functions is on the acting unit's seed (33 multiplier sites, 37
  `RNG_Range`, 2 `RNG_RangeB` and 1 `RNG_RangePow2` calls, all on `U+0x20`, `b2-draws.txt`); 0–6 per decision, in the
  order of § 2's pseudocode. Draws on other seeds come only from callees (`MonAiFindHostile` in rows 22 and 28; the move
  helpers as in ai/0001 § 7). No function of the batch loops over units with a draw (P1.1 review, reopen condition
  (b)): the four search callbacks draw nothing (three counted in `b2-draws.txt`; `AiSameBaseNearCb` by its direct calls, `MonBaseId`, `MonIsDeathMode` and `UnitDistSq`, none an RNG entry; their own callees not followed), and row 25's loop over the wisps it found sets three words and an idle
  per wisp. (§ 2, `b2-draws.txt`, fn:sub_005F2A00_AiGreaterMummyCb@0x005F2A00, fn:sub_005F30F0_AiWoundedNearCb@0x005F30F0,
  fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00, fn:sub_005F3960_AiWispCb@0x005F3960)
- [I] **Effects outside the unit.** Row 22's Radament class (MonStats row 229) calls `A2Q1_BossSeen` and widens its
  corpse and wounded search; at each of the seven steps of row 25's four-wisp dance, each wisp gives a living player target a
  stat list with stat 80 (`item_magicbonus`) = 50·(d+1) for 1 728 000 frames and queues unit event 12 at its end; row 29 raises its own stat 74
  (`hpregen`) by `aip5`/8 of itself while it perches and takes it back when it leaves. (§§ 2.6, 2.9, 2.13,
  fn:sub_00599420_A2Q1_BossSeen@0x00599420, fn:STATLIST_SetStat@0x00627150, tbl:ItemStatCost.txt:ID)
- [I] **Parameter records.** Row 20 `Scarab` posts a kind-1 record to its group as row 6 `Fallen` does (ai/0002 § 2.5)
  and acts on its own kind-1 head record; row 30 `Fetish` walks to the unit a kind-1 or kind-14 head record names. The
  fetish reads the record's unit as `GameFindUnit(G, rec+0x10, rec+0x0C)` (`EDX` the type), row 14 `QuillRat` as
  `GameFindUnit(G, rec+0x0C, rec+0x10)`: the two readers take the type and the id from opposite words. (§§ 2.4, 2.14,
  0x005F5424–0x005F542B, 0x005F1173–0x005F1177)

## Leads used

None. No community document was read; every claim is read from the code. P1.1 and batch 1 (ai/0001, ai/0002) are
cited by their anchors.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005F20A0` | `sub_005F20A0_AiSandLeaper` | row 17 `SandLeaper` think | I (map `[C]`, § 3) |
| `0x005F22B0` | `sub_005F22B0_AiPantherWoman` | row 18 `PantherWoman` think | I (map `[C]`, § 3) |
| `0x005F2460` | `sub_005F2460_AiSwarm` | row 19 `Swarm` think | I (map `[C]`, § 3) |
| `0x005F2540` | `sub_005F2540_AiScarab` | row 20 `Scarab` think | I (map `[C]`, § 3) |
| `0x005F2850` | `sub_005F2850_AiMummy` | row 21 `Mummy` think | I (map `[C]`, § 3) |
| `0x005F2B10` | `sub_005F2B10_AiGreaterMummy` | row 22 `GreaterMummy` think | I (map `[C]`, § 3) |
| `0x005F2A00` | `sub_005F2A00_AiGreaterMummyCb` | row 22's search callback: a corpse and a wounded ally in range | I |
| `0x005F3170` | `sub_005F3170_AiVulture` | row 23 `Vulture` think | I |
| `0x005F2EB0` | `sub_005F2EB0_AiVultureTakeOff` | clears `Unit+0xC4` bits 1–3 and the unit's collision, pattern 5, mask 0, `Delay(12)` | I |
| `0x005F2FC0` | `sub_005F2FC0_AiVultureLand` | sets `Unit+0xC4` bits 1–3, places the unit where it is, collision back, `Delay(12)`; 1 when placed | I |
| `0x005F30F0` | `sub_005F30F0_AiWoundedNearCb` | row 23's search callback: the nearest living unit at or below `aip3` percent life | I |
| `0x005F3730` | `sub_005F3730_AiMosquito` | row 24 `Mosquito` think | I (map `[C]`, § 3) |
| `0x005F39B0` | `sub_005F39B0_AiWillOWisp` | row 25 `WillOWisp` think | I |
| `0x005F3960` | `sub_005F3960_AiWispCb` | row 25's room-search callback: a living monster of base 118 (`willowisp1`) | I |
| `0x005F4510` | `sub_005F4510_AiArach` | row 26 `Arach` think | I |
| `0x005F4850` | `sub_005F4850_AiThornHulk` | row 27 `ThornHulk` think | I (map `[C]`, § 3) |
| `0x005F4A70` | `sub_005F4A70_AiVampire` | row 28 `Vampire` think | I |
| `0x005F5040` | `sub_005F5040_AiBatDemon` | row 29 `BatDemon` think | I |
| `0x005F4FD0` | `sub_005F4FD0_AiBatDemonAlt` | row 29's `alt` | I (map `[C]`, § 3) |
| `0x005F53E0` | `sub_005F53E0_AiFetish` | row 30 `Fetish` think | I (record map `[C]`, § 3) |
| `0x005B0D00` | `sub_005B0D00_AiSameBaseNearCb` | row 18's search callback: the nearest other living monster of the searcher's base class | I |
| `0x005DE440` | `sub_005DE440_MonAiMoveToPoint` | `(ECX game, EDX unit; x, y, mode)`: command `mode` to the point, stop distance 1 | I |
| `0x005DE490` | `sub_005DE490_MonAiMoveToPointNoStop` | the same with stop distance 0 | I |
| `0x0058EC00` | `sub_0058EC00_AiCtlSetVar` | `(ECX unit, EDX k; v)`: `AiCtl+0x14/+0x18/+0x1C` for k = 1/2/3 of a monster with an AI control | I |
| `0x00650D70` | `sub_00650D70_AlignSame02` | 1 for the same unit, or both alignments 0, or both 2; else 0 | I |

## Walkthrough

### 1. The rows, their records and the per-record slots

- [I] The rows (`ai-rows.txt` of P1.1, `b2-rows.txt`): 17 `SandLeaper` (7 records), 18 `PantherWoman` (6), 19 `Swarm`
  (5), 20 `Scarab` (8), 21 `Mummy` (6), 22 `GreaterMummy` (10, `unraveler1..9` and `radament`), 23 `Vulture` (5), 24
  `Mosquito` (4), 25 `WillOWisp` (8), 26 `Arach` (7), 27 `ThornHulk` (5), 28 `Vampire` (9), 29 `BatDemon` (7), 30
  `Fetish` (16, `fetish1..8`, `fetish11`, `bonefetish1..7`): 103 records. (tbl:MonStats.txt:AI)
- [I] Where the records of a row differ in a slot the code reads, the code reads each record's own slot, with these
  effects (values `[C]` as data, `b2-rows.txt`): row 28, `aip5` is a bit set (§ 2.12), 3 in `vampire1` (Firewall, no
  Meteor), 5 in `vampire2` (Meteor, no Firewall), 7 in `vampire3`, 4, 6–9 (both), 1 in `vampire5` (neither, only the
  Fireball/Missile pair); row 30, `aip1` 0 in `fetish11` (its melee attack draw never succeeds) where the others have
  100; row 27, `aip6` 5 in `thornhulk5` (3/4/5 in the others), the frenzy repeat count (§ 2.11). (tbl:MonStats.txt:aip5,
  tbl:MonStats.txt:aip1, tbl:MonStats.txt:aip6)

### 2. The think functions

#### 2.1 Row 17 `SandLeaper` (0x005F20A0)

```c
if (Skill1 >= 0 && dist < 5 && chance(1) && MonSkillTargetOk(Skill1, t, 0, 0))   // draw#1 only when the two tests pass
    return MonAiUseSkill(Sk1mode, Skill1, t, 0, 0);                              // Leap
if (!melee) {
    if (dist > 10) { Ovr(0, 75, 0); return MonAiWanderNearUnit(t, 5); }
    if (chance(3)) return Walk(t, 7);                                            // draw#1 or #2
    if (chance(4)) return T56(t, 4, 0);
} else if (chance(2)) return SetModeAtUnit(5, t);
Idle(10);
```

- [I] The leap is tried first, at any range below 5, on `aip1` (20–25 by difficulty). Beyond 10 the leaper wanders near
  its target (override parameter 75) without a draw. In melee range it only ever uses A2. (0x005F20A0–0x005F22A8,
  fn:sub_005DF530_MonAiWanderNearUnit@0x005DF530, tbl:MonStats.txt:Skill1)
- [C] The map. (run:2026-10-30-ai-cat-emu-2, `leaper`)

#### 2.2 Row 18 `PantherWoman` (0x005F22B0)

```c
if (melee) { if (chance(2)) return SetModeAtUnit(4, t); return Idle(aip4); }
if (chance(1)) { Ovr(0, 75, 0); return Walk13(t, 7); }                          // draw#1
s = { unit 0, best 0x7FFFFFFF };  AiUnitSearch(G, U, &s, AiSameBaseNearCb, 1);
if (s.unit && aip3 * aip3 < s.best) { Ovr(0, 75, 0); return Walk(s.unit, 7); }   // rejoin the pack
if (draw < 25) return T56(t, 3, 0); else return Idle(aip4);                     // draw#2
```

- [I] The callback takes a monster (`Unit+0x00` = 1) other than the searcher with the searcher's `MonBaseId`, not in a
  death mode (`MonIsDeathMode`), and keeps the nearest by `UnitDistSq`; so a panther farther than `aip3` (8–24) from
  its nearest packmate walks to it. The search block is a stack block `{+0x00 unit, +0x04 best}` at `EBP − 0x2C`.
  (0x005F22B0–0x005F2455, fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00, fn:sub_00463860_MonBaseId@0x00463860,
  fn:sub_0063EA40_MonIsDeathMode@0x0063EA40)
- [C] The map up to the search, the block's two words included. (run:2026-10-30-ai-cat-emu-2, `panther`)

#### 2.3 Row 19 `Swarm` (0x005F2460)

```c
if (!melee) { if (chance(1)) return Walk(t, 7); }
else if (chance(3)) return SetModeAtUnit(4, t);
Idle(aip2);
```

- [I] Row 9 `Wraith`'s shape with `Walk` for the approach and `aip2` (12–20) for the wait. (0x005F2460–0x005F252D)
- [C] The map. (run:2026-10-30-ai-cat-emu-2, `swarm`)

#### 2.4 Row 20 `Scarab` (0x005F2540)

```c
rec = AiParamsHead(U);
if (!rec) {
    if (dist < 20 && MonsterOwner(U) == U && chance(5)) {                        // a leader: draw#1
        blk.kind = 1; MonHelpBlock(U, &blk); AiParamsPush(U, &blk); rec = &blk;
    }
}
if (rec && rec->kind == 1) {
    if (melee && Skill1 >= 0) { AiParamsPop(U); return MonAiUseSkill(Sk1mode, Skill1, t, 0, 0); }   // Jab
    Ovr(2, 100, 0); if (!Walk(t, 0)) AiParamsPop(U); return;
}
if (!melee) {
    if (ctl->v14) { Ovr(2, 0, 4); Walk(t, 7); if (draw > 10) ctl->v14 = 0; return; }   // draw after the walk
    T56(t, 0, 0); ctl->v14 = 1; return;
}
if (!chance(1)) return Idle(aip3);                                               // draw#1
if (Skill1 >= 0 && chance(4)) return MonAiUseSkill(Sk1mode, Skill1, t, 0, 0);    // draw#2
return SetModeAtUnit(chance(2) ? 4 : 5, t);                                      // draw#2 or #3
```

- [I] The leader's call is row 6's (ai/0002 § 2.5), on `aip5` (20–28) within 20: the stack block's kind word is the only
  word written. A scarab with a kind-1 head record charges (override type 2, parameter 100) and jabs once in melee
  range, dropping the record; a head record of another kind is left in place and the plain decision runs. Out of melee
  range `AiCtl+0x14` alternates a drawn-type walk (`T56(t, 0, 0)`, then 1) with walks under override type 2, parameter 0
  and byte 4, until a draw above 10 clears it. (0x005F2540–0x005F2816, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0,
  fn:sub_0058F730_MonHelpBlock@0x0058F730, struct:AiCtl+0x14)
- [C] The map, `MonsterOwner`'s own `GameFindUnit` call (0x0058F0FA) included as a boundary.
  (run:2026-10-30-ai-cat-emu-2, `scarab`)

#### 2.5 Row 21 `Mummy` (0x005F2850)

```c
if (AiMonState3or19(U) && !melee) return Walk(t, 7);
if (dist <= aip1) {
    if (melee) {
        if (chance(3)) return SetModeAtUnit(chance(4) ? 4 : 5, t);               // draw#1, #2
        Idle(aip5);                                                              // no return: then the walk
    }
    return Walk(t, 7);
}
if (chance(2)) return Ring(3);
Idle(aip5);
```

- [I] `aip1` (5–25) is a range, not a chance: a mummy farther than it wanders (on `aip2`) or waits `aip5` (10). In melee
  range a failed `aip3` draw (100 in every record, so on stock data only when `aip3` is edited) runs `Idle(aip5)` and
  then `Walk(t, 7)` in the same event (0x005F29D7–0x005F29E6: no jump between the two calls).
  (0x005F2850–0x005F290D, tbl:MonStats.txt:aip1)
- [C] The map up to the first callee (the `Idle`; the `Walk` after it is a reading). (run:2026-10-30-ai-cat-emu-2,
  `mummy`)

#### 2.6 Row 22 `GreaterMummy` (0x005F2B10)

```c
if (melee && chance(1)) return SetModeAtUnit(4, t);                              // draw#1
if (dist < 5 && chance(1)) return SetModeAtUnit(5, t);                           // draw#1 or #2
s = { corpse 0, wounded 0, taken 0, inRange 0, bound aip5², undead 0, uniquesToo 0 };
if (U->class == (MonStatsCount > 229 ? 229 : -1)) {                              // Radament
    A2Q1_BossSeen(G, U); s.bound = (aip5 + 10)²; s.undead = 1; if (d == 0) s.uniquesToo = 1;
}
AiUnitSearch(G, U, &s, AiGreaterMummyCb, 1);
if (Skill2 >= 0 && s.wounded && chance(3)) { UnitSetPathTargetUnit(U, s.wounded);
    return MonAiUseSkill(Sk2mode, Skill2, s.wounded, 0, 0); }                    // Bestow
if (s.corpse && chance(2) && MonSkillTargetOk(Skill1, s.corpse, 0, 0)) { UnitSetPathTargetUnit(U, s.corpse);
    return MonAiUseSeqSkill(Skill1, s.corpse, 0, 0); }                           // Resurrect2, mode 14
if (Skill3 >= 0 && chance(4) && (h = FindHostile(&dist, 0)))
    return MonAiUseSkill(Sk3mode, Skill3, h, 0, 0);                              // UnHolyBolt
if (s.inRange < 1) { Ovr(0, 50, 0); return WalkToUnitStop(t, 3); }
if (draw > 49) return Idle(6); else return T56(t, 3, 0);
```

- [I] **The callback** (`AiGreaterMummyCb`, block `{+0x00 corpse, +0x04 wounded, +0x08 taken, +0x0C inRange, +0x10
  bound, +0x14 undead, +0x18 uniquesToo}` at `EBP − 0x40`): a monster other than the searcher, on the same side
  (`AlignSame02`), alignment not 2, `Unit+0xC4` bit `0x02`, not in state set 33 (`UnitHasStateSet33`); then with
  `undead` 0 its MonStats `lUndead` (`+0x0D` bit 3), with `undead` 1 `MONSTATS_IsUndead`; then unless `uniquesToo`, not a
  unique (`MonTypeFlag(unit, 8)`); then `UnitDistSq` ≤ `bound`. Each such unit counts in `inRange`; one in mode 12
  (dead) with no state of the `+0xD4` mask becomes `corpse`, one in another mode than 0 whose stat 6 (`hitpoints`)
  differs from `UnitGetMaxHp` becomes `wounded`; each taken one counts in `taken`. The last one met of each kind is
  kept. (0x005F2A00–0x005F2B03, fn:sub_00650D70_AlignSame02@0x00650D70, fn:MONSTATS_IsUndead@0x0063E990,
  fn:sub_005A0180_MonTypeFlag@0x005A0180, tbl:MonStats.txt:lUndead)
- [I] **Radament** (MonStats row 229, the class compare inlined as `((count > 229) − 1 & 0xFFFFFF1A) + 229`) searches
  10 farther, any undead, and uniques too in Normal. Both bounds are 32-bit signed `imul` squares of an s16, which
  fit for every s16 (`(32767 + 10)² = 1 074 331 729 < 2³¹`; the largest negative, `(−32768)² = 2³⁰`). **Draw order:** the two melee/near draws on `aip1`; then `aip3` only
  with `Skill2 ≥ 0` and a wounded unit, `aip2` only with a corpse, `aip4` only with `Skill3 ≥ 0`, and the 50/50 only
  with a unit in range. (0x005F2C15–0x005F2C6E, 0x005F2C85–0x005F2E9F, tbl:MonStats.txt:Skill2, tbl:MonStats.txt:Skill3)
- [C] The map up to `A2Q1_BossSeen` or the search, the block's seven words included in the non-Radament case.
  (run:2026-10-30-ai-cat-emu-2, `gmummy`)

#### 2.7 Row 23 `Vulture` (0x005F3170)

```c
fly = ctl->v14;                                             // >0 airborne events left, 0 ground, -1 just landed
far = UnitDistSq(U, t) > 144;
if (RoomOf(t) != RoomOf(U) && far) {
    if (fly < 1) return Toward(t, 9, 0);
    if (Land(U)) { MoveToUnitDist(U, 9, 2, 3); Delay(12); ctl->v14 = -1; return; }   // the unit itself as the target
}
if (fly == 0 && !MonsterOwner(U) && far && Range(100) < 60) {                    // take off
    TakeOff(U); ctl->v14 = 24 + RangePow2(8); MoveToUnitDist(t, 8, 8, 8); return Delay(12);
}
s = { unit 0, bound 121, pct aip3 };  AiUnitSearch(G, U, &s, AiWoundedNearCb, 1);
if (fly >= 2) {
    if (s.unit || (dist < 6 && Range(100) < 15)) { ctl->v14 = 1; goto land; }
    TakeOff(U);                                                                  // again; see below
    if (!v18 || !v1C || AiPathDistToPoint(U, v18, v1C) < 2) {                    // a new circling point
        c = fly + 8;  x = tx - c + RangeB(2c);  y = ty - c + RangeB(2c);  r = clamp(2c, 12, 36);
        while (AiPathDistToPoint(U, x, y) < r) { step x and y one away from U's position; if at it, both +1; }
        ctl->v18 = x; ctl->v1C = y; Ovr(1, 0, 0); MoveToPoint(x, y, 8); Delay(12); ctl->v14--; return;
    }
    FreeNearFallback(room of t, then of U, (v18, v1C), size, 0xFFFF, 1) → (v18, v1C) when found;
    ctl->v14--; Ovr(7, 0, 0); MoveToPoint(v18, v1C, 8); return Delay(12);
}
if (fly == 1) {
land: if (Land(U)) { MoveToUnitDist(t, 9, 2, 3); Delay(12); ctl->v14 = -1; return; }
      ctl->v14 = 8; Delay(12);                                                   // no room to land: fly 8 more
}
if (melee) { if (chance(1)) return SetModeAtUnit(4, t); return Delay(aip2); }
if (fly != -1 && Range(100) >= aip5) return Delay(aip2);
if (Range(100) < aip4) T56(t, 6, 0); else Toward(t, 9, 0);
ctl->v14 = 0; Delay(12);
```

- [I] `AiCtl+0x14` is the flight counter: a vulture with no owner, more than 12 subtiles from its target (squared 144),
  takes off on 60 % of events (24–31 airborne events), circles points drawn around the target (`RNG_RangeB` twice, a
  square of half-side `fly + 8`) at least `clamp(2(fly + 8), 12, 36)` from itself, and lands when the counter reaches
  1, when the callback finds a unit at or below `aip3` percent life within 11 subtiles (`AiWoundedNearCb`: a monster or
  player other than itself, not dying, `UnitDistSq` ≤ 121, stat 6 ≤ `UnitGetMaxHp / 100 · aip3`, keeping the nearest),
  or, within 6, on 15 %. `AiCtl+0x18/+0x1C` hold the circling point. On the ground it attacks in melee on `aip1`,
  waits `aip2` events, and walks; the `aip5` wait draw is skipped in the event after a landing. Modes 8 and 9 are the
  move commands' modes here (`MoveToPoint(…, 8)`, `MoveToUnitDist(…, 9, …)`). The decompile was checked against the
  asm for the branch order (0x005F3190–0x005F3340, 0x005F35C0–0x005F3728).
  (fn:sub_005F3170_AiVulture@0x005F3170, fn:sub_005F2EB0_AiVultureTakeOff@0x005F2EB0,
  fn:sub_005F2FC0_AiVultureLand@0x005F2FC0, fn:sub_005F30F0_AiWoundedNearCb@0x005F30F0, fn:RNG_RangeB@0x0045C3E0,
  fn:RNG_RangePow2@0x00472210, struct:AiCtl+0x18)
- [I] Not emulated: the first callee is `UnitDistSq` and the next two `UnitGetRoom`, before any draw.
  (0x005F31C4, 0x005F31DB, 0x005F31E3, fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)

#### 2.8 Row 24 `Mosquito` (0x005F3730)

```c
if (melee) {
    if (chance(3) || ctl->v18 == 0) {                                            // draw#1 always taken
        ctl->v18++;
        if (Skill1 >= 0 && chance(4)) return MonAiUseSkill(Sk1mode, Skill1, t, 0, 0);   // the drain
        return SetModeAtUnit(4, t);
    }
    if (draw > 20) return Idle(15);                                              // draw#2
    ctl->v14 = 2; ctl->v18 = 0;
}
switch (ctl->v14) {
case 0: Ovr(13, 100, 0); return Walk(t, 0);
case 1: Ovr(0, 50, 0); Ring(4); if (++ctl->v18 > aip5) ctl->v14 = ctl->v18 = 0; return;
case 2: Ovr(2, 100, 0); StepAway(t, 10, 1); ctl->v14 = 1; ctl->v18 = 0; return;
default: ctl->v14 = ctl->v18 = 0; return Idle(10);
}
```

- [I] An attack-and-retreat cycle: `AiCtl+0x18` counts the attacks of a melee bout (the first is free of the `aip3`
  draw); a failed `aip3` draw then 21 % of the time starts the retreat (state 2: step 10 away), then `aip5` + 1 ring
  points (state 1, 5 in every record), then the approach under override type 13 (state 0). (0x005F3730–0x005F394F,
  struct:AiCtl+0x18)
- [C] The map, `AiCtl+0x14/+0x18` at the boundary included. (run:2026-10-30-ai-cat-emu-2, `mosquito`)

#### 2.9 Row 25 `WillOWisp` (0x005F39B0)

- [I] **The gather trigger.** At entry, when `AiCtl+0x1C` < the frame, `UnitDistSq(U, t)` < 1024, `AiCtl+0x14` < 4 and
  `Range(1000) ≤ d + 2` (3, 4 or 5 in 1000), `AiCtl+0x14` becomes 4. `AiCtl+0x1C` is the gather cooldown: a dance that
  ends sets it to frame + 1800. (0x005F3E0A–0x005F3E46)
- [I] **State 4.** A room unit search of radius 32 around the wisp (`RoomUnitSearchInit` with flags 0x583,
  `AiWispCb`: a monster not dying whose `MonBaseId` is 118, `willowisp1`'s row). With exactly 4 found, each gets
  `AiCtl+0x14` = 6, `+0x18` = 0, `+0x1C` = its index 1–4 (`AiCtlSetVar`) and `Idle(337 − frame mod 337)`; with 5,
  state 5 and indices 1–5; the wisp itself then idles to the same frame. Any other count: `AiCtl+0x14` = 2, `Idle(8)`.
  (0x005F3E5B–0x005F4051, fn:sub_005F3960_AiWispCb@0x005F3960, fn:sub_0058EC00_AiCtlSetVar@0x0058EC00,
  fn:sub_0065A950_RoomUnitSearchInit@0x0065A950)
- [I] **The dance** (state 5 for five wisps; states 6–12 for four, `AiCtl+0x1C` the wisp's place 1–5): the point is an
  origin plus an entry of a constant offset table the function writes on its stack at entry (index
  `place + 4·state` for the four-wisp dance, 8-byte `(x, y)` entries from `EBP − 0x2F4`). Farther than 3 from it
  (`AiPathDistToPoint`), the wisp wanders a ring point of radius 4 on 34 % or moves to it (`MoveToPointNoStop(x, y,
  2)`); there, it waits for a frame multiple of 67, then for three sub-steps casts (`MonAiSetMode(7, x', y')` at a
  second table's offset, when non-zero) and counts `AiCtl+0x18`; after three, the four-wisp dance moves to the next
  state (6 to 12; past 12 it ends: state 2, cooldown). At **each** such advance, after `Idle(337 − frame mod 337)`, when
  `t` is a living player (`Unit+0x00` = 0, not `UnitIsDead`), `t` gets a new stat list (`STATLIST_Alloc` flags 2) with
  stat 80 = 50·(d + 1), ending at frame + 1 728 000 (`StatListSetEnd`), a unit event 12 queued on `t` at that frame,
  linked to `t` (0x005F41AA–0x005F4271: the end-of-dance reset is skipped over, not the grant). So each of the four
  wisps grants on each of its seven advances. The four-wisp origin is the target's subtile position (0x005F407E–
  0x005F40AA); the five-wisp dance's origin is not read here. The five-wisp dance (state 5) ends after three sub-steps
  with no such grant. (0x005F4054–0x005F4366, fn:STATLIST_Alloc@0x006251F0,
  fn:STATLIST_LinkToUnit@0x00626E10, fn:sub_005417D0_UnitQueueEvent@0x005417D0, tbl:ItemStatCost.txt:item_magicbonus)
- [I] **The plain states.** State 1 (after an approach): with `AiCtl+0x18` < 1, in melee range S1 (`SetModeAtUnit(8, 0)`)
  and state 3, else on `aip1` S1 and state 2; otherwise `AiCtl+0x18`−−, and `Range(100) < aip3` walks to `t`, else a
  ring point of radius 6 (state 1). States 0, 2, 3: out of melee range, state 2 or `aip1` casts SC at `t`
  (`SetModeAtUnit(7, t)`, Chain Lightning by `Skill1`'s mode) and state 0; in melee range, state 3 or `aip2` attacks A1
  and state 0; otherwise `Range(100) < aip3` walks to `t`, else a ring point of radius 4, state 1, `AiCtl+0x18` = 3.
  (0x005F4366–0x005F4500)
- [I] Not emulated: `UnitDistSq` comes first on most events and the room search in state 4. The offset tables (two of
  (x, y) pairs for the four-wisp dance, one for the five-wisp dance) are not transcribed here (§ Open questions).
  (0x005F3E1C, 0x005F3F14, fn:sub_005B0BD0_UnitDistSq@0x005B0BD0)

#### 2.10 Row 26 `Arach` (0x005F4510)

```c
life = UnitLifePct(U);
if (ctl->v14 == 1) {                                                             // retreating after a lay
    ctl->v18 = 0;
    if (life > 75) { ctl->v14 = 0; if (chance(3)) { ctl->v14 = 2; return Walk13(t, 0); } return T56(t, 6, 0); }
    if (melee && aip1 > 25 && Range(100) < aip1 - 25) return SetModeAtUnit(4, t);
    if (dist >= aip4 && !AiMonState3or19(U)) { ctl->v14 = 0; return T56(t, 12, 0); }
    return StepAway(t, 4, 0);
}
if (!melee) {
    if (AiMonState3or19(U) || ctl->v18 == 1) { ctl->v18 = 1; return Walk13(t, 0); }
    if (++ctl->v1C > 20) ctl->v1C = 0;  ctl->v18 = 0;
    if (ctl->v1C == 1 && Range(100) < aip3) { ctl->v18 = 1; return Walk13(t, 0); }
    if (Range(100) < 20) return Ring(6); return Idle(15);
}
ctl->v14 = 2;
if (chance(1)) return SetModeAtUnit(4, t);                                       // draw#1
if (life >= aip5) { if (Range(100) < aip2) return T56(t, 4, 0); return Idle(15); }
ctl->v14 = 1;
if (Skill1 >= 0 && !UNIT_HasState(U, 22)) return MonAiUseSkill(Sk1mode, Skill1, 0, 0, 0);   // SpiderLay, no target
StepAway(t, 8, 0);
```

- [I] Below `aip5` percent life (25–45) a spider in melee range lays (state 22 `spiderlay` not yet set) and retreats
  (state 1) until above 75 % life; `AiCtl+0x1C` is a 21-event cycle that gives one approach draw per cycle out of
  melee range. (0x005F4510–0x005F4840, fn:UNIT_HasState@0x00639DF0, tbl:States.txt:spiderlay)
- [I] Not emulated: `UnitLifePct` is the first callee (its stat-list read set is not a small image; ai/0002 § 3).
  (fn:sub_00621F20_UnitLifePct@0x00621F20, fn:STATS_GetUnitStat@0x00625480)

#### 2.11 Row 27 `ThornHulk` (0x005F4850)

```c
if (!melee) { ctl->v14 = 0; return Walk13(t, 7); }
if (ctl->v14 < 1) {
    if (!chance(1)) { if (Range(100) < aip3) return T56(t, 4, 0); return Idle(15); }
    if (ctl->v18 < 1 && Range(100) < aip4) {
        MonAiUseSkill(5, Skill1, t, 0, 0);                                       // MonFrenzy, in mode A2
        f = UnitEventFirstFrame(G, U, 1); if (G->frame < f) Delay(aip5 - G->frame + f);
        ctl->v14 = aip6; return;
    }
    ctl->v18--;
    return SetModeAtUnit(Range(100) < aip2 ? 5 : 4, t);
}
MonAiUseSkill(5, Skill1, t, 0, 0);
f = UnitEventFirstFrame(G, U, 1); if (G->frame < f) Delay(aip5 - G->frame + f);
if (--ctl->v14 < 1) ctl->v18 = 3;
```

- [I] A frenzy bout: once started (on `aip4`, while `AiCtl+0x18` < 1) the hulk repeats the skill for `aip6` (3–5)
  events, then `AiCtl+0x18` = 3 makes the next three melee decisions plain attacks. The skill is always used in mode 5
  (A2), not `Sk1mode`. `AiCtl+0x18` keeps decreasing below 0 on further plain attacks. (0x005F4850–0x005F4A60,
  fn:sub_005415A0_UnitEventFirstFrame@0x005415A0, tbl:MonStats.txt:aip6)
- [C] The map up to the first callee (the `Delay` and the stores after the skill are readings).
  (run:2026-10-30-ai-cat-emu-2, `thornhulk`)

#### 2.12 Row 28 `Vampire` (0x005F4A70)

- [I] **Inputs.** `bits = aip5` (§ 1): bit 0 allows the Fireball/Missile pair at the hostile, bit 1 Skill2 (Firewall),
  bit 2 Skill3 (Meteor). `AiCtl+0x1C` is a skill cooldown (decremented each event when positive, set to 11 after Skill2
  or Skill3); `AiCtl+0x14` 1 engaged, 2 fleeing; `AiCtl+0x18` the largest distance below 30 seen under the
  `MonsterData+0x54` 3-or-19 test. `FindHostile(&hd, 0)` runs on every event, then `AiMonState3or19`, then
  `UnitLifePct(U)`. (0x005F4A70–0x005F4AD0, fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)
- [I] **The pair.** "The pair at `x`" below is `Range(100) < 50 ? MonAiUseSkill(Sk1mode, Skill1, x) :
  MonAiUseSkill(Sk4mode, Skill4, x)` (Fireball or VampireMissile). Under the 3-or-19 test in melee range: a draw above
  30 or bit 0 clear attacks A1, else the pair at `t`. Fleeing (state 2): above 74 % life back to state 1 and `Walk(t,
  7)`; nearer than 14 or than `AiCtl+0x18`, a step 8 away under override parameter `clamp(Run·100/Velocity − 100, 0,
  120)` (MonStats `+0x34`/`+0x32`); then `dist ≥ aip3` or `Range(100) ≥ aip2` waits 15; then Skill2 on bit 1, Skill3 on
  bit 2 (each with the cooldown at 0 and `Range(100) < aip4`), at `t`; then without bit 0, a hostile or with `hd` > 20
  a drawn-type walk, else the pair at the hostile. Engaged: below 33 % life it flees (state 2, step 8 away); in melee
  range (state 1), on `aip1`: A1, unless bit 0, a hostile and a draw ≤ 30, when the pair goes at the hostile if it is
  within 20; otherwise (no `aip1`, or the hostile beyond 20) 33 % a drawn-type walk, else `Idle(10)`. Out of melee
  range, at `aip3` or beyond it walks (`Walk(t, 7)`) only when already in state 1, else waits 15; inside `aip3` (state
  1), `Range(100) ≥ aip2` keeps a distance (a walk beyond 20, a 50 % step 8 away inside 9, else a 50 % drawn-type walk
  or `Idle(10)`); else Skill2/Skill3 as above at `t`; else without bit 0, a hostile, or with `hd` > 20 `Walk(t, 7)`;
  else a draw above 74 a drawn-type walk, else the pair at the hostile.
  (0x005F4AD0–0x005F4FBB, tbl:MonStats.txt:Skill4, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run)
  - *Refinement (2026-10-30, lane/rfix; backlog ai-0003-vampire-flee-velocity-guard):* the flee step's override
    parameter is computed only when `Velocity > 0`, as a signed 16-bit test (`movzx ecx, word [esi+0x32]; test cx, cx;
    jle`, 0x005F4BC0–0x005F4BC9); otherwise it is 0. With the guard met: `q = (s16 Run · 100) / (s16 Velocity)`, a
    signed `idiv` (truncation toward zero), then `q − 100`; a result ≤ 0 becomes 0 (`setle; sub 1; and`) and one
    ≥ 120 becomes 120 (0x005F4BCB–0x005F4BEC). So `p = Velocity > 0 ? clamp(Run·100/Velocity − 100, 0, 120) : 0`,
    passed to `MonAiPathOverride(unit, 0, p, 0)` (0x005F4BF8) before the step 8 away (0x005F4C09). This is the one
    such computation in 0x005F4A70–0x005F4FBB; the engaged flee's step takes no override. `Run · 100` cannot wrap
    (|s16| · 100 ≤ 3 276 800). (fn:sub_005DE190_MonAiPathOverride@0x005DE190, tbl:MonStats.txt:Velocity)
- [I] Not emulated: `MonAiFindHostile` is the first callee (ai/0002 § 3). (fn:sub_005DDC30_MonAiFindHostile@0x005DDC30)

#### 2.13 Row 29 `BatDemon` (think 0x005F5040, alt 0x005F4FD0)

```c
life = UnitLifePct(U);
switch (ctl->v14) {
case 0: case 4:                                              // perch
    SetModeAtUnit(10, 0); Delay(8); ctl->v14 = 1; ctl->v18 = 0;
    if ((r = stat74(U))) { ctl->v1C = aip5 * r / 8; UnitSetStat(U, 74, r + ctl->v1C, 0); } else ctl->v1C = 0;
    return;
case 1:
    if (ctl->v18 > 1 && !(!melee && dist > 6 && !AiMonState3or19(U) && (dist > 13 || life < 51))) {
        if (ctl->v1C) UnitSetStat(U, 74, stat74(U) - ctl->v1C, 0);
        SetModeAtUnit(9, 0); Delay(6); ctl->v14 = 3; return;                     // leave the perch
    }
    SetModeAtUnit(11, 0); Delay(ctl->v18 == 0 ? 10 : 15); ctl->v18++; return;   // stay perched
case 2:
    if (life < aip1 && StepAway(t, 15, 0)) { ctl->v14 = 4; return; }
    if (Range(100) < 33) { Walk(t, 0); ctl->v14 = 3; return; }
    if (Range(100) < 15) return Ring(6); return Idle(10);
case 3:
    if (life < aip1 && StepAway(t, 15, 0)) { ctl->v14 = 4; return; }
    if (!melee) return Walk(t, 0);
    if (ctl->v18 > 0) { SetModeAtUnit(5, t); ctl->v18 = 0; return; }
    if (AiMonState3or19(U) && Range(100) < aip2 && StepAway(t, 12, 0)) { ctl->v14 = 2; return; }
    if (Range(100) < aip3) return SetModeAtUnit(Range(100) < aip4 ? 5 : 4, t);
    return Idle(10);
default:
    if (dist < 15) { Walk(t, 0); ctl->v14 = 3; return; }  ctl->v14 = 4; return Idle(15);
}
```

- [I] Stat 74 (`hpregen`) is raised by `aip5`/8 of itself (signed, truncated: `(x + (x >> 31 & 7)) >> 3`; `aip5` 8 in
  every record, so doubled) while perched and the same amount taken back on leaving; below `aip1` (33) percent life it
  flees and perches again (state 4). The first attack after a perch is A2 (`AiCtl+0x18` > 0). (0x005F5040–0x005F53D3,
  fn:STATS_GetUnitStat@0x00625480, fn:sub_00627260_UnitSetStat@0x00627260, tbl:ItemStatCost.txt:hpregen)
- [I] **The alt** (run by `MonAiInit` when the think is already installed, ai/0001 § 3): a unit in mode 11 (S4) sets
  `AiCtl+0x14` = 1 and `Delay(1)`; else state 4 becomes 1 with `SetModeAtUnit(10, 0)`; else `MonAiInit(ctl, ctl->state)`
  and `Idle(1)`. (0x005F4FD0–0x005F5031, fn:sub_005B0E00_MonAiInit@0x005B0E00)
- [C] The alt's map (no draw). (run:2026-10-30-ai-cat-emu-2, `batalt`)
- [I] Not emulated: the think's first callee is `UnitLifePct`. (fn:sub_00621F20_UnitLifePct@0x00621F20)

#### 2.14 Row 30 `Fetish` (0x005F53E0)

```c
if ((rec = AiParamsHead(U))) {
    if ((rec->kind == 1 || rec->kind == 14) && (u = GameFindUnit(G, rec+0x10, rec+0x0C))) {
        ctl->v14 = ctl->v18 = 0; Ovr(13, 50, 0); Walk(u, 0); AiParamsPop(U); return;
    }
    AiParamsPop(U);
}
tl = UnitLifePct(t);                                                             // the target's life
switch (ctl->v14) {
case 0: if (melee) { ctl->v18 = 0; ctl->v14 = 1; if (chance(1)) return SetModeAtUnit(4, t); return Idle(aip2); }
        break;
case 1: if (++ctl->v18 > aip3 && tl > aip4) {                                    // hit and run
            ctl->v14 = 2; ctl->v18 = 0; Ovr(2, 50, 0); return StepAway(t, 14, 1); }
        if (melee) { if (Range(100) < aip1) return SetModeAtUnit(4, t); return Idle(aip2); }
        break;
case 2: if (dist > 12) { if (++ctl->v18 > 1) ctl->v14 = ctl->v18 = 0;
                         if (draw < 20) return T56(t, 4, 0); return Idle(10); }
        Ovr(2, 50, 0); if (StepAway(t, 14, 1)) return; ctl->v14 = ctl->v18 = 0; return Idle(10);
default: return Idle(10);
}
Ovr(13, 50, 0); Walk(t, 7);
```

- [I] After `aip3` (4 or 5) melee decisions against a target above `aip4` (33) percent life a fetish steps 14 away, and
  comes back after two events beyond 12. A kind-1 or kind-14 head record whose unit exists makes it walk to that unit;
  any other head record is dropped. No writer of a kind-14 record with a unit was found in this batch (§ Open
  questions). (0x005F53E0–0x005F56BD)
- [C] The record map up to `GameFindUnit`, `AiParamsPop` or `UnitLifePct` (no draw before them).
  (run:2026-10-30-ai-cat-emu-2, `fetish`)

### 3. Emulation (run:2026-10-30-ai-cat-emu-2)

- [C] Ten families, 240 cases each, 2 400 cases, all matching, none stopped, no traced access outside the declared
  memory (`emu/check.txt`). Each case runs one think function (or row 29's alt) on a declared image (the docstring of
  `tools/ai_cat_emu2.py`) and ends at the first observed callee; the checker compares the callee, the call site (the
  return address), `ECX`/`EDX` where the callee takes them, the stack arguments, the unit seed, `AiCtl+0x14/+0x18` and,
  at an `AiUnitSearch` boundary, the words of the search block at the pointer argument (its address `EBP − 0x2C` or
  `EBP − 0x40`, read from the stack dump). Callees run on the declared image rather than observed: `RNG_Range`,
  `AiMonState3or19` with `MonData54Get`, `AiParamsHead` and `MonsterOwner` (whose `GameFindUnit` is observed).
  Controls: `le` (each draw compared with `<=`, and `>` with `>=`) and `d0` (every `aip` from the Normal column) fail
  every case they separate, and the site control (each call site one byte later) fails every case
  (run:2026-10-30-ai-cat-emu-2):

  | family | row | boundaries reached | `le` separating | `d0` separating |
  |---|---:|---|---:|---:|
  | `leaper` | 17 | 6 | 17 | 45 |
  | `panther` | 18 | 4 | 26 | 99 |
  | `swarm` | 19 | 3 | 34 | 120 |
  | `scarab` | 20 | 9 | 28 | 71 |
  | `mummy` | 21 | 7 | 25 | 101 |
  | `gmummy` | 22 | 4 | 20 | 106 |
  | `mosquito` | 24 | 7 | 16 | 26 |
  | `thornhulk` | 27 | 7 | 28 | 42 |
  | `fetish` | 30 | 4 | 0 | 0 |
  | `batalt` | 29 alt | 3 | 0 | 0 |

  `fetish` and `batalt` reach their boundaries with no draw and no `aip` read, so no control separates them; their
  `[C]` is the map of their record and mode/state tests only. Not covered: every callee and everything after it.
  (run:2026-10-30-ai-cat-emu-2)
- [I] Not emulated: rows 23, 25, 26, 28 and 29's think, and row 30 past its record test. Each reaches, before its first
  draw, a callee whose read set is not declarable in a small image (`UnitDistSq` and `UnitGetRoom` for 23 and 25;
  `UnitLifePct` for 26, 29 and 30; `MonAiFindHostile` for 28), so an observed boundary there ends each case before its
  first draw. Phase 2's logs reproduce them (rows 28, 29 and 30 are tier AIs).
  (fn:sub_005F4A70_AiVampire@0x005F4A70, fn:sub_005F5040_AiBatDemon@0x005F5040, fn:sub_00621F20_UnitLifePct@0x00621F20)

## Data touched

- tbl:MonStats.txt:aip1 … tbl:MonStats.txt:aip6 (`+0x56 + 6(k−1) + 2d`), tbl:MonStats.txt:Skill1 … Skill4
  (`+0x170 + 2(k−1)`), tbl:MonStats.txt:Sk1mode … Sk4mode (`+0x180 + (k−1)`), tbl:MonStats.txt:Velocity (`+0x32`),
  tbl:MonStats.txt:Run (`+0x34`), tbl:MonStats.txt:lUndead (`+0x0D` bit 3), tbl:ItemStatCost.txt:hitpoints (6),
  tbl:ItemStatCost.txt:hpregen (74), tbl:ItemStatCost.txt:item_magicbonus (80), tbl:States.txt:spiderlay (22).
- struct:AiCtl+0x00, struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C, struct:AiCtl+0x20, struct:AiCtl+0x28,
  struct:AiCtx+0x14, struct:AiCtx+0x18, struct:MonsterData+0x54, struct:Unit+0x04, struct:Unit+0x10, struct:Unit+0xC4,
  struct:Game+0x6D, struct:Game+0xA8, `g_pDataTables` `+0xA80` (the MonStats count).

## Dead ends

- The decompile of row 25 mis-indexes its stack tables (it shows them as separate locals); the table reads were taken
  from objdump (`EBP + 8·(place + 4·state) − 0x2F4`), and the table values themselves are left open.

## Open questions

- Row 25's dance offset tables (the `(x, y)` pairs written on the stack at entry, 0x005F39E1–0x005F3E07): their values
  are not transcribed; an emulation dump of the stack after the prologue, or a P2 log of a dance, settles them.
- Who posts a kind-1 or kind-14 record naming a unit to a fetish (§ 2.14), and in which word order: the fetish reads the
  type from `+0x10`, the quill rat (ai/0002 § 2.12) from `+0x0C`. **Answered [I] in [ai/0005](0005-pool-d.md) § 2.18**:
  row 65 `FetishShaman` writes the guid at `+0x0C` and the type at `+0x10` (the fetish's order), row 75 `QuillMother`
  the type at `+0x0C` (the quill rat's); the readers and writers agree in pairs (0x005F9AE8, 0x005FB2CA, fn:sub_0058F730_MonHelpBlock@0x0058F730).
- Who writes `MonsterData+0x54` (the 3-or-19 test, rows 21, 26, 28, 29): still unnamed (ai/0001's open question).
- What unit event 12 queued on the player at the end of the wisp grant does: not read here.
