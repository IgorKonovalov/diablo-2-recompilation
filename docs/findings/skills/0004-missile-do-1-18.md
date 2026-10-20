# 0004 — Catalogue batch 9a: missile server do functions 1–18

> **Subsystem:** skills/catalogue
> **Question:** what does each missile server do function 1–18 (`pSrvDoFunc`, `g_MissileSrvDoFuncs`) do: which
> Missiles columns and `MissileData` words it reads, which missiles, units, items or portals it creates, which draws it
> makes on which seed, and which of that the emulator can confirm?
> **Date:** 2026-10-20   **Plan:** 0046 (Phase 1, batch 9a)   **Status:** open (the architect's review; 9b–9d follow)

Static reading of the pinned `Game.exe` in Ghidra 12.1.2 (lane copy `workspace/ghidra-p46m1`, symbols replayed from
`re/symbols.csv`) and objdump, then emulation of the functions' own code under ADR-0015 with a new script,
`re/ghidra_scripts/EmuBoundary.java` (§ 2; run:2026-10-20-cat-emu-9a in [experiments](experiments.md)). Missiles
columns are named as in [Missiles](../../tables/Missiles.md), Skills columns as in [Skills](../../tables/Skills.md);
offsets are record offsets. The machinery (creation, the frame step, the hit, `MissileData`) is
[skills/0002](0002-missiles.md); the tier-A entries of this batch (do 1, 3, 5) are read in
[skills/0002 § 4](0002-missiles.md#4-each-frame) and [skills/0003 § 6](0003-handlers.md#6-tier-a-missile-do-hit-and-damage-functions)
and are not re-read here. Stock values below come from `workspace/logs/skills-cat-9a/rows.txt` (`6cfad638…`,
`excel_bin.py dump` of the batch's rows).

## Answer (summary)

- *Tags (architect, `lane/p46m1` review):* the emulated claims below that end at a boundary call are `[I]` until
  the owner accepts the proposed [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); then `[C]` up to
  that call. The refusal paths that return are `[C]` now (§ 2). (run:2026-10-20-cat-emu-9a)
- [I] **The batch.** 17 entries (numbers 1–18, 4 unused): do 1, 3, 5 are tier A (not re-read); this batch reads
  the other 14 and the do-1 table slot. Entry 1 of `g_MissileSrvDoFuncs` is a 5-byte thunk, `jmp 0x005AE1F0`, so
  "do 1 is `sub_005AE1F0_MissileMoveCollide`" holds through the thunk. Every function read here ends with a call of
  do 1 (the path step, the range count and the collision) and returns its result (do 18 after its cookie check); a
  missing record, owner or sub-missile returns 2 (free) instead. (data:g_MissileSrvDoFuncs@0x0073C768, fn:sub_005B0BC0_MissDo01Thunk@0x005B0BC0,
  `static.txt` `do table`)
- [I] **Draws.** Only three code paths of the batch draw: `sub_005A9820_MissSubNearReseed` (do 8, 10, 17)
  re-seeds the **missile's** seed to `(SubX + elapsed, 666)` and draws two `RNG_RangeB(seed, 2(r − 1))` offsets
  (none when `r ≤ 1`); do 18 draws two `RNG_RangeB(seed, 2·Param3 + 1)` offsets on the missile's seed per gold drop,
  with no re-seed. Every other function makes no draw of its own before the creation, spawn or path call it ends in:
  no unit seed is read on those paths (the traced read set holds none). The draws of the callees (MissileCreate's
  `SUnitCreate` and critical rolls, the path planner, the spawn, the item creation) are theirs (skills/0002 § 9).
  (run:2026-10-20-cat-emu-9a, fn:sub_005A9820_MissSubNearReseed@0x005A9820, fn:sub_005AF300_MissDo18ChestSpawner@0x005AF300)
- [I] **Sub-missiles at the missile.** Do 6 (firewallmaker and its kin), 9 (bat lightning bolt) and 12 (diabwallmaker)
  create `SubMissile1` at the missile's own sub-tile on each frame whose path flag 8 is set (path `+0x34 & 8`), with
  the missile's skill and level; do 6 and 12 need an owner and `SubMissile1 ≥ 0` (else 2), do 9 tests neither. Do 2
  (poisonjav) does the same through `sub_005A9720_MissSubAtSelf` with velocity 0, the parent as source, the loop
  count `2·lvl − 2`, and creation flag 8 only when `SrvCalc1` evaluates above 0. (§ 3, § 4; run:2026-10-20-cat-emu-9a)
- [I] **Frozen Orb** (do 15): every `Param1` frames (1 on stock data: each frame) one `SubMissile1`
  (`frozenorbbolt`) aimed at offset `g_Circle64[k]` (64 points on a radius-30 circle) from the orb, `k = |w % 64|` with
  `w = MissileData+0x28`; `+0x28` becomes `(Param2 + k) % 64` (C remainder; stock `Param2` 19). The orb nova (do 16)
  turns its path target `(a, b)` = `(+0x28, +0x2C)` into `((a − b) / 2, (a + b) / 2)` (truncating) on the frames
  `elapsed < Param1` with `elapsed % Param2 == 0` and re-plans its path. (§ 5, § 6; run:2026-10-20-cat-emu-9a,
  fn:sub_005AF030_MissDo15OrbBolts@0x005AF030, fn:sub_005AF170_MissDo16TurnTarget@0x005AF170)
- [I] **Scatter around the missile** (do 8 monblizcenter, do 10 blizzardcenter, do 17 cairnstones): one
  `SubMissile1` per period at a random offset in `[−(r − 1), r − 1)` on each axis, refused where
  `COLL_CellTestAt(room, x, y, 5)` is non-zero. Do 8: `r = Param1 + max(lvl / Param3', 2)`, period
  `max(Param2 − lvl / Param3', 3)` (`Param3' = max(Param3, 1)`); do 10: `r` = the skill's `calc1`, period its `calc2`
  (Blizzard's); do 17: `r = Param3`, period `Param2`, only while `Param1 < left < Range − Param1`, then once a
  permanent portal to level `Param4` (38, Tristram) when `left ≤ Param5 + Param1` and `+0x28` is 0. (§ 7;
  run:2026-10-20-cat-emu-9a, fn:sub_005AE8A0_MissDo08ScatterByLevel@0x005AE8A0, fn:sub_005AEA60_MissDo10ScatterBySkill@0x005AEA60,
  fn:sub_005AF240_MissDo17CairnStones@0x005AF240)
- [I] **towerchestspawner** (do 18): at `left == Range − Param1` (raw `Range`) it runs the chest's drop function
  (`0x00585E00`) on the chest whose guid is `+0x28` and starts the gold phase (`+0x2C = 1`; set even when the chest is
  gone); then every `4·Param2` frames (8) a gold pile at a random offset `[−Param3, Param3]` (±5) is placed through
  `0x00555DA0`; at `left == 1` the chest gets unit event `0x5C`. (§ 8)
- [I] **Homing.** Do 11 (fingermagespider) steps its path target `max(Param3, 1)` sub-tiles towards its (or its
  owner's) target on each axis every `Param1` frames when the edge distance is ≤ `Param2`, and re-plans. Do 7 is
  raised in part: its refusals are `[C]` (§ 2: no record, no owner, owner dead, a town room); its re-plan,
  which needs a live hostile target, stays `[I]`, and so does the writer of bit 0 (Guided Arrow's and Bone Spirit's
  skill do 10, set when cast at a unit) (§ 9, § 10). Do 14's
  call `CallDoFunc(Param2, skill, lvl)` every `Param1` frames with a skill and level above 0 (§ 11).
  (run:2026-10-20-cat-emu-9a, fn:sub_005AEB60_MissDo11StepToTarget@0x005AEB60, fn:sub_005AE780_MissDo07Homing@0x005AE780,
  fn:sub_005AEF70_MissDo14PeriodicDo@0x005AEF70)
- [I] **Bone Wall** (do 13): on each path-flag-8 frame while `+0x2C` (pieces left) is non-zero, a monster of the
  skill's `summon` class and `pettype` is spawned at the missile, owned by the first wall piece (`+0x28`, its guid),
  added to that piece's group, given mod 15, the summon stats and the caster as owner; `+0x2C` decrements. Not
  emulated: `SkillSummonClass`'s read set (§ 12). (fn:sub_005AEDA0_MissileSpawnOwnedMonster@0x005AEDA0)

## Leads used

None. No community document was opened for this batch.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005B0BC0` | `sub_005B0BC0_MissDo01Thunk` | do-table entry 1: `jmp sub_005AE1F0_MissileMoveCollide` | I |
| `0x005AE400` | `sub_005AE400_MissDo02SubMissile` | (P1.2 name) do 2 | I |
| `0x005A9720` | `sub_005A9720_MissSubAtSelf` | do 2's helper: `SubMissile1` at the parent, velocity 0, loops `2·lvl − 2` | I |
| `0x005AE680` | `sub_005AE680_MissDo06SubPerCell` | do 6 | I |
| `0x005AE780` | `sub_005AE780_MissDo07Homing` | do 7 (refusals `[C]`, § 2) | I |
| `0x005AE8A0` | `sub_005AE8A0_MissDo08ScatterByLevel` | do 8 | I |
| `0x005AE940` | `sub_005AE940_MissDo09SubPerCell` | do 9 | I |
| `0x005AEA60` | `sub_005AEA60_MissDo10ScatterBySkill` | do 10 | I |
| `0x005AEB60` | `sub_005AEB60_MissDo11StepToTarget` | do 11 | I |
| `0x005AECA0` | `sub_005AECA0_MissDo12SubPerCell` | do 12 | I |
| `0x005AEDA0` | `sub_005AEDA0_MissileSpawnOwnedMonster` | (items/0002 name) do 13 | I |
| `0x005AEF70` | `sub_005AEF70_MissDo14PeriodicDo` | (P1.2 name) do 14 (refusals `[C]`, § 2) | I |
| `0x005AF030` | `sub_005AF030_MissDo15OrbBolts` | do 15 | I |
| `0x005AF170` | `sub_005AF170_MissDo16TurnTarget` | do 16 | I |
| `0x005AF240` | `sub_005AF240_MissDo17CairnStones` | do 17 | I |
| `0x005AF300` | `sub_005AF300_MissDo18ChestSpawner` | do 18 | I |
| `0x005A9820` | `sub_005A9820_MissSubNearReseed` | (P1.3 name) re-seed, two offsets, cell test, `SubMissile1` | I |
| `0x006416D0` | `sub_006416D0_UnitEdgeDistance` | distance between two units' footprints (do 7, 11) | I |
| `0x00553490` | `sub_00553490_PathTargetRevalidate` | drops a path's target unit that is gone or a picked-up item | I |
| `0x00648AD0` | `sub_00648AD0_PathSetTargetPoint` | path `+0x10`, `+0x12` (u16) = the point, `+0x58` = 0 | I |
| `0x00648BF0`, `0x00648BB0` | `sub_00648BF0_PathGetTargetUnit`, `sub_00648BB0_PathGetTargetTypeGuid` | path `+0x58`; `+0x5C`/`+0x60` | I |
| `0x00620870` | `sub_00620870_UnitGetPos` | a unit's sub-tile pair (path `+0x02`/`+0x06`, or the static path's) | I |
| `0x005DB6D0` | `sub_005DB6D0_SkillDo10GuidedMissile` | `srvdofunc` 10 (Guided Arrow, Bone Spirit): writes do 7's `+0x28`/`+0x2C` | I |
| `0x006E2B78`, `0x006E2A78` | `g_Circle64X`, `g_Circle64Y` | 64 s32 each, the circle of do 15 (`static.txt`) | I |
| `0x006E10E0` | `g_UnitHashOffsets` | per unit type 0–4 the game offset of its 128 hash buckets (`GameFindUnit`) | I |

## Walkthrough

### 1. The table slots and the shared shape

- [I] `g_MissileSrvDoFuncs[1..18]` (`static.txt` `do table`): 1 `0x005B0BC0` (thunk), 2 `0x005AE400`, 3 `0x005AE480`,
  4 null, 5 `0x005AE520`, 6 `0x005AE680` … 18 `0x005AF300`, one function per number. Each is
  `(ECX game, EDX missile) → 1 keep / 2 free`. They read their record as `DataTables+0xB64 + 0x1A4 · Unit+0x04` after
  the bound test `0 ≤ class < DataTables+0xB6C`. (0x005B0BC0, 0x005AE6A7–0x005AE6D5)
- [I] **Fault paths.** Do 8, 9 and 10, on a class out of range, test `WORD PTR ds:0x18` (the null record's
  `SubMissile1`): a read of address `0x18`, an access violation the emulator does not model; the case writers leave
  it out (ADR-0015 (5)). No stock missile has a class out of range. (0x005AE8D2, 0x005AE97B, 0x005AEA98)
- [I] **Do 18 returns do 1's value** after `__security_check_cookie`, which keeps EAX; Ghidra shows it `void`.
  (0x005AF521–0x005AF536)

### 2. Emulation: boundaries instead of callees

Most of these functions end in a call whose read set is not declarable: `MissileCreate` (a unit allocation), the path
planner, `SpawnOwnedMonster`, the free-spot search, the chest's drop. ADR-0015 (1) forbids stubbing them, and its (3)
scopes a `[C]` to "the bytes it writes". `EmuBoundary.java` (`286393aa…`) is `EmuTrace.java` with one more memory-spec
directive, `observe <addr>`: a case whose pc reaches that address **ends there**, and the script prints the registers
and the 64 bytes at ESP (the return address, then the stack arguments); the stack is dumped (`d` lines) so a parameter
block passed by pointer is read back. No instruction is patched; the code before the boundary is the program's own.
The claim of such a case is the map from its inputs to the boundary call's arguments and to every byte written before
the call, nothing after. The nine boundaries (`skills_catalogue_emu.py` `BOUND`): `0x005AE1F0` do 1, `0x0059FA30`
MissileCreate, `0x00649970` PathPlan, `0x0064CB30` COLL_CellTestAt, `0x005A9930` PermPortalAtUnit, `0x00553380`
UnitSetEvent, `0x00585E00` the chest drop, `0x00555DA0` the free spot, `0x0056D810` CallDoFunc.

- [C] Nine families, 13 800 cases, **0 mismatches**, 0 traced reads outside the declared set, 0 cases stopped other
  than at a boundary; each family's negative control fails (`check.txt` `3e1f2587…`; run:2026-10-20-cat-emu-9a):

  | Family | Functions | Cases | Neg. control (fails) | Branches reached |
  |---|---|---:|---|---|
  | `cellsub` | do 6, 9, 12 | 1 800 | do 12 flags `0x01` (173) | create, create with no owner and with `SubMissile1` < 0 (do 9), no path (do 12), do-1 call, return 2 |
  | `orb` | do 15 | 1 500 | `k = w & 63` (266) | create (negative elapsed 380, negative `w` 268, negative next index 345), do-1 call, return 2 |
  | `spiral` | do 16 | 1 500 | arithmetic shift for `/ 2` (223) | turn (odd negative sums 223), do-1 call, return 2 |
  | `scatter` | do 8, 10, 17 and `0x005A9820` | 2 400 | re-seed without `elapsed`; calcs swapped; portal bound + 1 (394) | period 0, off-beat, no owner, no room, 0 and 2 draws, invalid skill, calc offset out of the pool, do 17's window and portal |
  | `chest` | do 18 | 1 500 | x and y draws swapped (247) | event at `left == 1`, chest drop, chest gone, idle, off-beat, drop with its two draws |
  | `homing` | do 11 | 1 500 | sizes left out of the distance (22) | no target, the owner's target, off-beat, too far, step (an axis unchanged 60) |
  | `periodic` | do 14 | 1 200 | level test dropped (149) | call, do-1 call, return 2 (record, skill or level) |
  | `sublob` | do 2 and `0x005A9720` | 1 200 | flag 8 for a value ≥ 0 (187) | no sub-missile, no flag 8, no owner, flag 8 and not, calc offset out |
  | `guided` | do 7 | 1 200 | owner-dead test dropped (128) | return 2 (record, no owner, owner dead, town), bit 0 set and clear, a missile target |

- [C] **Declared image reads** (ADR-0015 (2); `static.txt` `e2b2f9a1…`): `g_UnitHashOffsets` `0x006E10E0`,
  `g_Circle64X/Y`, the town tables `0x006426C0`/`0x006426C8`, the `CALC_Eval` jump table `0x006C1164` and
  `UNIT_GetSizeX`'s `0x0062057C`, all in `.rdata` or `.text`; the calc function counts `0x007457AC` and `0x00745848`
  (`.data`, 0 stores in `.text`; the constant programs `09 <s32> 00` the cases use call no function, so no output
  depends on them); the security cookie (do 18; xor in, xor out). Scratch structures are written one field per field
  read (S1f ruling 4), so any other field read would have been traced.
- [I] **Not reached** (stay `[I]` from the reading): the fault paths of § 1; what happens after each boundary;
  do 11 and do 7 with a player or monster target (`UNIT_GetSizeX` of types 0–2, `UnitsHostile`); the path target
  cleared by `0x00553490` (the found unit always equals the stored one in the cases); do 13. ADR-0015 (3): the `[C]`
  covers the code as a map; what the offsets mean keeps its own tag (the Missiles columns are `[C]` by layout; the
  `MissileData` words are `[I]`, skills/0002 § 1), and nothing here says when the game runs these functions or on
  which seed state.
- *Architect ruling, `lane/p46m1` review (2026-10-20):* a case that ends at an `observe` boundary does **not** meet
  ADR-0015 (1) and (3) as written: (1) gives a reached callee two treatments (run emulated, or an ADR-0004 oracle,
  which logs the exit and the return value and continues), and (3)'s outputs do not include a call's register
  arguments. The method is sound in substance (nothing patched, no output depends on a callee), so the architect
  drafted [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) (**proposed**, for the owner). Until it is
  accepted, every claim of this finding that rests on a case ending at a boundary is `[I]` (the Answer and §§ 3–11);
  on acceptance they return to `[C]` without a re-run, scoped as ADR-0021 states (nothing after the boundary).
  ADR-0021 (b) asks the checker to test the call site; this run's checker tests the boundary only, and the review's
  check of the kept outputs found one call site per function and boundary
  (`workspace/logs/skills-cat-9a-review/callsites.txt` `8ea8058b…`, from `callsites.py` `9eb02fb7…` beside it; do 8's
  do-1 call is its tail jump, the case's own return sentinel). Later batches add the site to the checker.
  (run:2026-10-20-cat-emu-9a, fn:sub_005A9820_MissSubNearReseed@0x005A9820)
- [C] **The paths that return** (compared on EAX and the bytes popped, no boundary reached; `check.txt` outcomes
  `ret2*` and `skill_invalid`): do 6 and 12 return 2 with no record, `SubMissile1 < 0` or no owner (do 6 also with no
  path); do 15 with no record, `SubMissile1 < 0` or no owner; do 16 with no record; do 10 when the missile's skill is
  no Skills row; do 14 with no record, or a skill or level ≤ 0 on its period; do 7 with no record, no owner, an owner
  `UnitIsDead` calls dead, or a missile in a town room. (run:2026-10-20-cat-emu-9a, fn:sub_005AE780_MissDo07Homing@0x005AE780,
  fn:sub_005AEF70_MissDo14PeriodicDo@0x005AEF70)

### 3. Do 6, 9, 12: `SubMissile1` at the missile, per path flag 8

```c
// fn:sub_005AE680_MissDo06SubPerCell@0x005AE680 (ECX game, EDX m), trimmed; do 12 (0x005AECA0) is the same
owner = UnitGetOwner(game, m);
if (!owner || !rec || rec->SubMissile1 < 0 || !m->path) return 2;          // do 12: no path test; flag(0) = 0
if (PathFlag08(m->path)) {                                                   // path +0x34 & 8
    p = {0}; p.flags = 0x21; p.owner = owner; p.x = p.tx = SubX(m); p.y = p.ty = SubY(m);
    p.skill = MISSDATA_GetSkill(m); p.lvl = MISSDATA_GetLevel(m); p.cls = rec->SubMissile1;
    MissileCreate(game, &p);
}
return MissileMoveCollide(game, m);
```

- [I] As above for do 6 and do 12 (do 12 tests the record, `SubMissile1` and the owner before the flag; a null path
  reads as flag 0 there, while do 6 returns 2). Do 9 (`0x005AE940`) creates with flags `1` (start given; the target
  then defaults to the start, skills/0002 § 2), takes its point from the path (`PathGetX/Y`, the same `+0x02`/`+0x06`
  words), and tests neither the owner nor `SubMissile1` (`MissileCreate` itself refuses an owner of 0 or a class below
  0). Flags `0x21` and `1` give the same start and target. (run:2026-10-20-cat-emu-9a `cellsub`,
  0x005AE6E6–0x005AE766, 0x005AE994–0x005AEA4C, 0x005AECEB–0x005AED84)
- [I] Stock rows: do 6 68 firewallmaker → 69 firewall, 130 vampirefirewallmaker → 131, 452 moltenboulder → 455
  moltenboulderfirepath, 653 countessfirewallmaker → 331 countessfirewall; do 9 123 bat lightning bolt → 124 bat
  lightning trail; do 12 179 diabwallmaker → 180 diabwall. No `Param` is read (452's `Param1` 3 is not this
  function's). When the path step sets flag 8 is the path code's (skills/0003 § 10); a reading that it marks a new
  cell is `[L]`. (tbl:Missiles.txt:SubMissile1, `rows.txt`)

### 4. Do 2 and `sub_005A9720_MissSubAtSelf`

- [I] Do 2: with a record and `SubMissile1 ≥ 0`, `v = MISS_EvalCalc(m, owner, SrvCalc1, class, lvl)`, then
  `0x005A9720(ECX game, EDX m; SubMissile1, 0, v)`: when path flag 8 is set and the owner exists, a block with flags
  `5` (`| 8` when `v > 0`), owner, source = the parent, `cls`, start = the parent's sub-tile, skill, level and loops
  `2·lvl − 2` (written whether or not flag 8 is set; read only with it). Then do 1. The second argument, a range
  override (`> 0` → flag `0x8000`), is 0 from do 2. This raises skills/0002 § 4's do-2 reading.
  (run:2026-10-20-cat-emu-9a `sublob`, 0x005A9720–0x005A9812, fn:sub_005AE400_MissDo02SubMissile@0x005AE400)
- [I] Stock rows 38 poisonjav and 648 viper_poisjav (→ 39, 649 the clouds), 245/246 trap poison balls (no
  `SubMissile1`: only do 1). (tbl:Missiles.txt:SrvCalc1)

### 5. Do 15: the Frozen Orb's bolts

```c
// fn:sub_005AF030_MissDo15OrbBolts@0x005AF030, trimmed
if (!rec || rec->SubMissile1 < 0 || !(owner = UnitGetOwner(game, m))) return 2;
if (MISSDATA_GetElapsed(m) % max(Param1, 1) > 0) return MissileMoveCollide(game, m);   // C remainder
k = MISSDATA_GetSeedLow(m) % 64;  if (k < 0) k = -k;                                    // 0x005AF106–0x005AF114
p = {0}; p.flags = 2; p.owner = owner; p.source = m; p.cls = rec->SubMissile1;
p.skill = skill(m); p.lvl = lvl(m); p.tx = g_Circle64X[k]; p.ty = g_Circle64Y[k];
MISSDATA_SetSeedLow(m, (Param2 + k) % 64);                                              // signed, may be negative
MissileCreate(game, &p);  return MissileMoveCollide(game, m);
```

- [I] As above: the period test creates on a remainder ≤ 0, so a negative elapsed with a remainder below 0 creates
  too; `k` is the absolute C remainder; the stored index is the plain C remainder of `Param2 + k` (no absolute value,
  32-bit sum). `g_Circle64X/Y` are image data, `(30, 0), (29, 2) … (29, −2)`: `round(30·cos, 30·sin)` of 64 steps
  (`static.txt` lists them; the rounding reading is `[I]`). `MissileData+0x28` is a direction index here, not a seed
  word. (run:2026-10-20-cat-emu-9a `orb`, 0x005AF099–0x005AF154)
- [I] Stock: row 260 frozenorb, `Param1` 1, `Param2` 19, `SubMissile1` 261 frozenorbbolt; Skills 64 Frozen Orb has
  `srvdofunc` 0, so the orb is `SKILLS_SrvDo`'s `srvmissile` with no callback and `+0x28` starts at 0
  (`sub_0064A100_MissileDataAlloc` zeroes the 0x34 bytes). So the bolts go in directions 0, 19, 38, 57, 12, 31 …,
  one per frame. (fn:sub_0064A100_MissileDataAlloc@0x0064A100, tbl:Missiles.txt:Param2, tbl:Skills.txt:srvmissile)

### 6. Do 16: the orb nova's turn

- [I] With a record: `step = max(Param2, 1)`; when `elapsed < Param1` (signed) and `elapsed % step == 0`, with
  `a = +0x28`, `b = +0x2C`: `a' = (a − b) / 2`, `b' = (a + b) / 2` (32-bit sums, division truncating toward zero),
  path target point = `(SubX + a', SubY + b')` (u16 stores, `+0x58` cleared by `sub_00648AD0_PathSetTargetPoint`),
  `PathPlan(path, m, 0)`; then `+0x28 = a'`, `+0x2C = b'` (after the plan, not covered; the registers at the plan's entry
  carry `a'` and `b'`) and do 1. (run:2026-10-20-cat-emu-9a `spiral`, 0x005AF1AF–0x005AF22F)
- [I] Stock: 262 frozenorbnova, `Param1` 6, `Param2` 2: a 45° turn of the offset, scaled by 1/√2, at elapsed
  0, 2 and 4. The starting `(a, b)` is written by its creator, hit function 29 of the orb (batch 9c). (tbl:Missiles.txt:Param1)

### 7. Do 8, 10, 17 and `sub_005A9820_MissSubNearReseed`

```c
// fn:sub_005A9820_MissSubNearReseed@0x005A9820 (EAX period, ESI m; game, r, cls, mask) -> 0, or MissileCreate's
if (!period || MISSDATA_GetElapsed(m) % period) return 0;
if (!(owner = UnitGetOwner(game, m)) || !UnitGetRoom(m)) return 0;
RNG_SeedInit(&m->seed, SubX(m) + MISSDATA_GetElapsed(m));        // (low, 666)
p = {0}; p.flags = 3; p.owner = owner; p.skill = skill(m); p.lvl = lvl(m); p.cls = cls;
dx = RNG_RangeB(&m->seed, 2 * (r - 1)) - (r - 1);                 // draw 1 (none when 2(r-1) <= 0)
dy = RNG_RangeB(&m->seed, 2 * (r - 1)) - (r - 1);                 // draw 2
p.x = SubX(m) + dx;  p.y = SubY(m) + dy;                          // p.tx = p.ty = 0: offset 0, target = start
if (COLL_CellTestAt(UnitGetRoom(m), p.x, p.y, mask)) return 0;
return MissileCreate(game, &p);
```

- [I] As above up to `COLL_CellTestAt` (its four arguments and the missile's seed at that call are compared): the
  period and radius come in EAX and on the stack (a register convention Ghidra's decompile drops); the re-seed uses
  the missile's own sub-tile x plus the elapsed frame count; `RNG_RangeB(n ≤ 0)` returns 0 without a step, so a
  radius of 1 or less draws nothing and puts the sub-missile on the missile's x offset by `1 − r`; the cell test is on
  the missile's room, not the target point's. The block after the test is `[I]`. (run:2026-10-20-cat-emu-9a `scatter`,
  0x005A9820–0x005A990C; objdump `lea edx,[eax+eax*1]` at 0x005A98B7, `idiv edi` at 0x005A983D)
- [I] **Do 8** (`0x005AE8A0`): `q = lvl / max(Param3, 1)` (signed), `r = Param1 + max(q, 2)`, period
  `max(Param2 − q, 3)`, mask 5, `SubMissile1`; then do 1 (tail jump). No owner or sub-missile test of its own.
  **Do 10** (`0x005AEA60`): the missile's skill must be a Skills row (else 2); `r = SKILLS_EvalCalc(owner, calc1,
  skill, lvl)`, period `SKILLS_EvalCalc(owner, calc2, skill, lvl)` (Skills `+0x138`, `+0x13C`), mask 5; then do 1.
  **Do 17** (`0x005AF240`): with `left` = frames left, when `SubMissile1 > 0`, `left < Range − Param1` and
  `left > Param1`: period `Param2`, `r = Param3`; then, when `Param4 ≥ 0`, `+0x28 == 0` and `left ≤ Param5 + Param1`,
  `sub_005A9930_PermPortalAtUnit(game, m, Param4)` (which sets `+0x28 = 1` first, quests/0002); then do 1. `Range`
  here is the raw column (`+0x96`), not the creation range. (run:2026-10-20-cat-emu-9a `scatter`, 0x005AE8E9–0x005AE936,
  0x005AEAB5–0x005AEB47, 0x005AF27E–0x005AF2E7, tbl:Missiles.txt:Param3, tbl:Skills.txt:calc1, tbl:Skills.txt:calc2)
- [I] Stock: 106 monblizcenter (`Param1` 5, `Param2` 8, `Param3` 4: radius `5 + max(lvl/4, 2)`, period
  `max(8 − lvl/4, 3)`) → 107 monbliz1; 158 blizzardcenter (Skills 59 Blizzard's `calc1`/`calc2`) → 159 blizzard1;
  288 cairnstones (`Range` 300, `Param1` 40, `Param2` 2, `Param3` 17, `Param4` 38, `Param5` 100) → 289
  cairnstonessky: every second frame while `40 < left < 260`, offsets −16 … 15, and the Tristram portal once when
  `left ≤ 140`. This answers quests/0001's open question for missile 288. (`rows.txt`, tbl:Missiles.txt:Param4)

### 8. Do 18: towerchestspawner

```c
// fn:sub_005AF300_MissDo18ChestSpawner@0x005AF300, trimmed
left = MISSDATA_GetRemaining(m);
if (left == 1 && (o = GameFindUnit(game, 2, +0x28))) UnitSetEvent(o, 0x5C, 0);
if (left == rec->Range - Param1) {
    if ((o = GameFindUnit(game, 2, +0x28))) ChestDrop_00585E00(&{game, o, 0, &o->seed, o->class});
    +0x2C = 1;
}
if (+0x2C && left % max(4 * Param2, 1) == 0) {
    pt = UnitGetPos(m);
    pt.x += RNG_RangeB(&m->seed, 2 * Param3 + 1) - Param3;       // draw 1, missile seed
    pt.y += RNG_RangeB(&m->seed, 2 * Param3 + 1) - Param3;       // draw 2
    if ((room = FreeSpot_00555DA0(UnitGetRoom(m), &pt, &out, 1, 1))) {
        mlvl = LevelMonLvl(RoomGetLevelId(room), game->difficulty, game->expansion);    // read only from here
        ItemCreate(game, &{source m, game, ilvl mlvl, item 'gld ', 3, out, room, 1, game+0x78, quality 2}, 0);
    }
}
return MissileMoveCollide(game, m);
```

- [I] As above up to each boundary (`UnitSetEvent`'s registers, the chest-drop block, the two draws and the point
  passed to `0x00555DA0`); the gold phase starts at the `Range − Param1` frame even when the chest is not found; the
  period is `4·Param2` (32-bit) floored at 1. (run:2026-10-20-cat-emu-9a `chest`, 0x005AF359–0x005AF474)
- [I] After the free spot: the item block (`0x84` bytes) is the drop record of items/0001's `DropCreateItem` with
  item `gld ` (`sub_00633680_ItemIndexByCode(0x20646C67)`), `+0x18` = 3, `+0x28` = 1, `+0x2A` = `game+0x78`, `+0x30`
  = 2, ilvl = `sub_0061DCA0_LevelMonLvl(level, game+0x6D, game+0x70)`; the item seed comes from the game seed
  (items/0001). What `0x00585E00` drops is the objects lane's (items/0010 § Dead ends: three chest drops, then two
  items of two codes). (0x005AF483–0x005AF518, fn:sub_00558D90_ItemCreate@0x00558D90)
- [I] Stock: 332 towerchestspawner (`Range` 400, `LevRange` 1, `Param1` 150, `Param2` 2, `Param3` 5), created by the
  Countess's death (`sub_005954F0_A1Q5_DeathSpawn`, `MissileCreateAt(0, 1, 332, …)` at each recorded chest, `+0x28` =
  the chest's guid, `+0x2C` = 0): the chest opens 150 frames (plus `LevRange · lvl`) after creation, then a gold pile
  within ±5 every 8 frames until the missile ends. This answers quests/0001's open question for missile 332.
  (fn:sub_005954F0_A1Q5_DeathSpawn@0x005954F0, 0x00595679)

### 9. Do 11: stepping towards a target

- [I] `t = UNIT_GetTargetUnit(game, m)`, or, when 0 and an owner exists, the owner's; without one, do 1. With
  `period = Param1 > 0 ? Param1 : 5`, when `left % period == 0` and `UnitEdgeDistance(m, t) ≤ Param2`:
  `s = max(Param3, 1)`, `dx = sign(SubX(t) − SubX(m))·s`, `dy` the same, path target point `(SubX(m) + dx,
  SubY(m) + dy)`, `PathPlan(path, m, 0)`; then do 1. (run:2026-10-20-cat-emu-9a `homing`, 0x005AEBA1–0x005AEC93)
- [I] `sub_006416D0_UnitEdgeDistance(a, b)`: `dx = |x_b − x_a|`, `dy = |y_b − y_a|`, each minus `size_b/2 + size_a/2`
  (`UNIT_GetSizeX`, signed halves) and floored at 0; the result is `(max·2 + min) / 2`. Covered for missile-type
  units (size = Missiles `Size`); other unit types `[I]`. (0x006416D0–0x006417AF)
- [I] `UNIT_GetTargetUnit` first runs `sub_00553490_PathTargetRevalidate`: the path's stored target is cleared when
  `GameFindUnit` by its stored type and guid no longer finds that unit, or finds an item in mode 1 or 2; it returns
  the target unless it is the unit itself. (0x00553490–0x00553515, 0x00553540)
- [I] Stock: 177 fingermagespider (`Param1` 5, `Param2` 20, `Param3` 2). (tbl:Missiles.txt:Param3)

### 10. Do 7: Guided Arrow and Bone Spirit

- [I] **Gates:** with a record, an owner that `UnitIsDead` calls alive (`Unit+0xC6` bit 0 clear, and mode not 0 nor
  the death mode: 0x11 for a player, 0xC for a monster; any other type counts as dead), and a missile room that is not
  a town (`sub_006426A0_LevelIsTown` of the room's level: 1, 40, 75, 103, 109); else 2. Then, only when `+0x28` bit 0
  is set: `0x00553490`, the target from `UNIT_GetTargetUnit`, dropped when dead or not hostile to the owner; a
  missile target is always dropped (`UnitIsDead` is 1 for type 3). (run:2026-10-20-cat-emu-9a `guided`,
  0x005AE780–0x005AE843, fn:sub_005541B0_UnitIsDead@0x005541B0)
- [I] **Re-plan:** with a live hostile target, `period = Param1 > 0 ? Param1 : 5`; when `left % period == 0` and the
  edge distance is in `[4, 24]`, `PathPlan(path, m, 0)` towards the path's target unit. Not emulated (`UnitsHostile`
  reads the party and owner chains). (0x005AE843–0x005AE879)
- [I] `+0x28` is written by `sub_005DB6D0_SkillDo10GuidedMissile` (`srvdofunc` 10 of Skills 22 Guided Arrow and 93
  Bone Spirit): 1 when cast at a unit, 2 when cast at a point (creation flags `0x20`, or `0x420` with no target
  unit), and `+0x2C` = the packed offset `(dy << 16) + dx` of the target point from the caster; the missile is
  `srvmissilea`, or `srvmissileb` when it is set and the weapon class test `0x00623C60` is not 1; a non-zero `calc1`
  adds the creation callback `0x005DB6A0` (not read). Stock 86 guidedarrow, 193 bonespirit (`Param1` 5, `Param2` 15: not read here), 329
  monbonespirit. (0x005DB6D0–0x005DB83A, tbl:Skills.txt:srvmissilea)

### 11. Do 14

- [I] With a record: `period = Param1 > 0 ? Param1 : 1`; when `elapsed % period == 0` and the missile's skill and
  level are both above 0, `CallDoFunc(ECX game, EDX m; Param2, skill, lvl)` and then do 1; when they are not, 2; off
  the period, do 1. Raises skills/0002 § 8's do-14 reading. (run:2026-10-20-cat-emu-9a `periodic`,
  0x005AEFC0–0x005AF020)

### 12. Do 13: Bone Wall's pieces

- [I] Read only (items/0002 § (e) named it): owner and `+0x2C` non-zero, else 2; on path flag 8, the skill record
  (`SKILLS_GetRecord`), `SkillSummonClass(owner, skill, lvl, &mode, 0, 0)` (< 0 → 0), the `pettype` byte (Skills
  `+0xBE`, 0 when out of PetType), the monster `+0x28` names (`GameFindUnit(game, 1, +0x28)`); a spawn block
  `{flags 0xD, owner, class, 0, mode, SubX, SubY, pettype, 0}` to `SpawnOwnedMonster`; on success `MonSetOwner(piece,
  first piece's guid, 1, 0, 0)`, `MonGroupAddMember(first, piece)`, `ModAppendApply(piece, 15, 0)`, `SummonInitStats`,
  `UnitSetOwner(piece, owner)`, `TargetListAdd(piece, 0, 9)`, `+0x2C −= 1`; then do 1. No draw of its own; the spawn's
  are monsters/spawn's. (0x005AEDA0–0x005AEF64)
- [I] The two makers come from `sub_005C58B0_SkillBoneWallDo` (Skills 78 `srvdofunc` 60): after the first piece at
  the target point, two `bonewallmaker` missiles (flags `0x21`) in the two directions perpendicular to the cast,
  each with `+0x28` = the first piece's guid and `+0x2C = calc2 / 2` (only when that is above 1).
  (0x005C5A33–0x005C5B92)
- [I] Not emulated: `SkillSummonClass` (`0x0063EA70`, `0x0058F710`) and the PetType bound read Skills, MonStats and
  PetType records the batch did not declare; a later batch can add the family.

## Data touched

`tbl:Missiles.txt:pSrvDoFunc`, `SubMissile1`, `Param1`, `Param2`, `Param3`, `Param4`, `Param5`, `SrvCalc1`, `Range`,
`Size`; `tbl:Skills.txt:calc1`, `calc2`, `srvmissile`, `srvmissilea`, `srvmissileb`, `srvdofunc`, `summon`, `pettype`;
`struct:MissileData+0x0A` (skill), `+0x0C` (level), `+0x0E`, `+0x10` (range, left), `struct:MissileData+0x28` (do 7
mode, do 13 piece guid, do 15 direction, do 16 `a`, do 17 portal done, do 18 chest guid), `struct:MissileData+0x2C`
(do 7 offset, do 13 pieces left, do 16 `b`, do 18 gold phase); `Unit+0x00`, `+0x04`, `+0x0C`, `+0x10`, `+0x14`,
`+0x20` (seed), `+0x2C`, `+0x94`, `+0x98`, `+0xC6` bit 0, `+0xC8` bit 10, `+0xE4`; path `+0x02`, `+0x06`, `+0x10`,
`+0x12`, `+0x1C` (room), `+0x34` bit 3, `+0x58`, `+0x5C`, `+0x60`; room `+0x10` → `+0x58` → `+0x1D0` (level id);
`Game+0x1120 + 0x200·k` hash buckets, `+0x1B20`, `+0x6D`, `+0x70`, `+0x78`.

## Dead ends

- Ghidra's decompile of do 8, 10 and 17 passes `sub_005A9820` four stack values and drops EAX and ESI: EAX is the
  period and ESI the missile (`mov edi,eax` at 0x005A9827, `[esi+…]` throughout). Read from objdump.
- Do 16's `MISSDATA_GetSeedLow` is not a seed: no function of this batch re-seeds from `+0x28`; it is a word each
  missile kind uses its own way (§ Data touched).

## Open questions

- ~~[L] **The `observe` boundary under ADR-0015.**~~ Ruled at the `lane/p46m1` review (§ 2): not met as written;
  ADR-0021 proposed; the boundary claims are `[I]` until the owner accepts it. (run:2026-10-20-cat-emu-9a)
- [L] What sets path flag 8 (`+0x34 & 8`) and so how often do 2, 6, 9, 12 and 13 create (the path step's; skills/0003
  § 10).
- [L] The `(a, b)` hit 29 gives each frozenorbnova (batch 9c) and the starting index of an orb created by anything but
  `SKILLS_SrvDo`.
- [L] Do 7's re-plan and do 11 with player or monster targets, and do 13: emulation with a declared `UnitsHostile`,
  `UNIT_GetSizeX` and `SkillSummonClass` read set.
