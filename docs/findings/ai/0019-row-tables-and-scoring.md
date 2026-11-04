# 0019 — Row 106's score by `aitype`, row 94's two tables, row 25's four frame tables and event 12

> **Subsystem:** monsters/ai
> **Question:** what are row 106's per-`aitype` terms, targets, skips and draws; what are the tables rows 94 and 25 read, by ADR-0031; what does unit event 12 do to the wisp's grant?
> **Date:** 2026-11-04   **Plan:** 0052   **Status:** for review (`lane/r71`)

Read whole in objdump of the pinned image: 0x005EB6D0–0x005EC694 (the callback, `AiStateGroupHeld`, `Use`, the think and its data), 0x005E0980–0x005E0C75 (row 94), 0x005F39B0–0x005F3E5B and 0x005F4054–0x005F4370 (row 25's stores and dance). Scans and checks: `tools/ai_const_survey.py`, `tools/ai_sm_check.py`; outputs in `workspace/logs/r71/`, `manifest.sha256`, 7 lines. No game, no Ghidra. Record: [run:2026-11-04-r71-sm](experiments.md#run2026-11-04-r71-sm).

## Answer (summary)

- [I] **Row 106.** Each record of the unit's skill list gets a base `aibonus + reqlevel ÷ 4 + level + res ÷ −10`, then its `aitype`'s terms from ten values the think computes once and a running sum. Cases 1 to 5, 7, 8 and 11 to 13 can keep a record; case 6 only draws `Range(100)` and may set the left skill; cases 9 and 10 have no terms and draw nothing. The draw is not tied to being kept: it comes before the list's test (§ 1.3). (fn:sub_005EB970_AiShadowMaster@0x005EB970, 0x005EBF65–0x005EC536)
- [C] As data, the stock Skills table has only `aitype` 1, 2, 3, 4, 5, 10, 11, 12 and 13 (32 rows), so cases 6, 7 and 8 are reached by no stock skill, and a blank `EType` is byte 0 in `skills.bin` (257 of 357 rows): such a skill reads the target's stat 36. (tbl:Skills.txt:aitype, tbl:Skills.txt:EType, `skills-aitype.txt`)
- [I] The word the entry calls "the `aip1[h]` and 0x005EA2B0 word" is `aip1[h] > 0` and `0x0063A2B0(U)`: the unit holds a state of the set at DataTables `+0xDC`, flag bit 4 `pgsv`, in stock the six `progressive_*` states. (0x005EBE13–0x005EBE2B, fn:sub_0063A130_UnitHasStateInMask@0x0063A130)
- [I] The pseudocode of §§ 1.2 to 1.5, written as a model, matches the think's instructions in all 6 000 synthetic cases, over every callee's words, the seed, the list and `v14`, `v18`; 98 of 99 one-term controls fail it, the one that cannot being a chance of 100 against 101. (run:2026-11-04-r71-sm)
- [I] **Row 94.** `STEP` (0x006E33A0, 16 i32) is one rule; `SWEEP` (0x006E33E0, 64 i32) has no rule by ADR-0031's exclusion, since a description by cases needs one patched cell (d = 3, v = 7), and it is listed in § 2. Neither table has a draw. (0x005E0B3A, 0x005E0B50, 0x005E0B5F)
- [I] **Row 25.** The four tables are 132 dword stores at every entry. `B5` is one rule over `A5`, `A5` is listed (10 values), and `A` and `B` (56 values each, 28 rows of `(x, y)`) have no rule known: **their values are not in this finding**, the architect decides (§ 3). (0x005F39E1–0x005F3E07)
- [I] **Event 12** on the player frees the wisp's list when its end frame comes, by [stats/states C1](../../specs/stats/states.md): nothing else is queued for it. (fn:EVENT_TimedListExpire@0x00580800, 0x005F4262)
- [I] No log tests any of this: 0 decisions of rows 25, 94, 106 or 143 and 0 lines of class 418 in the 160 logs of `workspace/logs/ai/` (0x005B186F, run:2026-11-04-r71-sm).

## Leads used

None. No community document was read for these three rows; `docs/sources.md` is unchanged.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005EB970` | `sub_005EB970_AiShadowMaster` | row 106's think, read whole | I |
| `0x0063A2B0` | `sub_0063A2B0_UnitHasStateInMaskDC` | `(unit)`, `ret 4`: `UnitHasStateInMask` with DataTables `+0xDC` | I |
| `0x00643910` | `sub_00643910_SkillListFirst` | `(list)`, `ret 4`: `list+4`, 0 for no list | I |
| `0x006438F0` | `sub_006438F0_SkillNodeNext` | `(node)`, `ret 4`: `node+4`, 0 for no node | I |
| `0x00643BC0` | `sub_00643BC0_UnitSetLeftSkill` | `(unit, id, owner)`, `ret 0xC`: stores the found node at the list's `+8` | I |
| `0x00644360` | `sub_00644360_SkillNodeMode` | `(node)`, `ret 4`: `node+8`, 0 for no node | I |
| `0x0055B7E0` | `sub_0055B7E0_UnitMonRecord` | `ECX` unit: a monster's `[+0x14]+0` record, else 0 | I |

## 1. Row 106: the score list

### 1.1 The inputs

`aip1[n]`, `aip1[m]`, `aip1[h]` and `aip2[n]` are the columns themselves, not indexed by the game's difficulty: `+0x56`, `+0x58`, `+0x5A`, `+0x5C` of the MonStats record, each read `movsx` from 16 bits (0x005EBECF, 0x005EC0FD, 0x005EC110, 0x005EBE13). `shadowmaster` has 20, 10, 10 and 20 as data (tbl:MonStats.txt:aip1, tbl:MonStats.txt:aip2).

The block is `blk`, filled by `AiUnitSearch(blk, AiShadowMasterCb, 1)`; `+0x8` and `+0x14` start at 0x7FFFFFFF, every other word at 0 and `+0` at `O` (0x005EBD46–0x005EBD81). The think copies them once, before the crowd test (0x005EBDFB–0x005EBE69):

| Name | Word | What it holds | Set at |
|---|---|---|---|
| `life` | `EBP−0x38` | `UnitLifePct(U)`: `100·(stat 6 >> 8) ÷ (max >> 8)`, 0 when the maximum is 0 | 0x005EBDFC, 0x00621F4B |
| `d` | `EBP−0x24` | `DistSq(U, t)`, `t` after step 10 | 0x005EBE08 |
| `state` | `EBP−0x40` | 1 when `aip1[h] > 0` and `0x0063A2B0(U)` is non-zero; else 0, with no call when `aip1[h] ≤ 0` | 0x005EBE13–0x005EBE2B |
| `clear` | `EBP−0x28` | 1 when `UnitLineBlocked(U, t, 4)` returned 0, else 0 | 0x005EBE36–0x005EBE4E |
| `near` | `blk+8` | smallest `DistSq(U, x)` of a hostile `x` within 1024; 0x7FFFFFFF with none | 0x005EBE66 |
| `n10` | `blk+0xC` | hostiles with `DistSq(U, x)` ≤ 100 | 0x005EBE41 |
| `nearO` | `blk+0x10` | the hostile of the search nearest `O`, at any distance; 0 with no owner or none | 0x005EBE54 |
| `nO` | `blk+0x18` | hostiles with `DistSq(O, x)` ≤ 100 | 0x005EBE69 |
| `n32` | `blk+0x1C` | hostiles with `DistSq(U, x)` ≤ 1024 | 0x005EBE60 |
| `allies` | `blk+0x20` | allied monsters of base 410 to 416 but 414, counted before the hostile words (0x005EB72A–0x005EB745) | 0x005EBE5A |
| `acc` | `EBP−0x30` | starts 0 at this think, carried from record to record | 0x005EBED7 |

The state set: DataTables `+0xCC + 4·i` holds the states of flag bit `i` (`docs/tables/States.md`, which gives `pgsv` as bit 4); `+0xDC` is `i` = 4, and the stock rows with `pgsv` are the six `progressive_*` states, 122 to 127 (tbl:States.txt:pgsv, 0x0063A2B9).

### 1.2 The loop

```
score list, from the crowd test on:
L[0] ← (t, 0, 0, 0, 0)                  ; 20-byte records (target, id, score, 0, 0)
k ← 1;  acc ← 0
for each node of U's skill list, first ← list+4, next ← node+4:      ; both at 0x005EBF02, 0x005EC53D
    id ← SkillNodeId(node);  level ← SKILLS_GetSkillLevel(U, node, 1)
    if id < 0 or id ≥ the Skills count or the record is null: next   ; no draw
    x ← t;  sc ← 0
    base ← aibonus + reqlevel ÷ 4 + level                            ; +0x232 s16, +0x174 s16, ÷ truncates
    if EType is in the map: base ← base + STATS_GetUnitStat(t, stat, 0) ÷ −10     ; ÷ truncates
    run the case of aitype (+0x230, read as a byte)                  ; § 1.3; none outside 1..13
    if sc > L[k − 1].score (signed):
        L[k] ← (x, id, sc, 0, 0);  k ← k + 1
```

The `EType` map (+0x1DC, a byte; the byte table at 0x005EC650, the jump table at 0x005EC634): 0 → stat 36, 1 → 39, 2 → 41, 3 → 37, 4 → 43, 5 → 45, 12 → 43; 6 to 11 and above 12 read nothing, a resistance of 0. The stat's argument order is `(t, stat, 0)`, the target of the think and not the case's `x` (0x005EBFA7–0x005EBFDA). The division is the `0x99999999` multiply at 0x005EBFE1–0x005EBFF0, a signed division by −10 truncating toward zero: 25 → −2, −25 → 2 (the model's `res_div` control fails 482 cases, `sm-check.txt`).

`sc` starts 0 at each record, so a case that drops a record leaves it at 0, and 0 is never kept: `L[0].score` is 0 and the test is strict. A negative `sc` is never kept either. Nothing limits `k` in the code. The frame has room for 48 records before the next local (`EBP−0x84`), and a record needs an `aitype`: 32 Skills rows have one, so with the skill ids of a list distinct a stock unit's `k` stays at or below 33 (distinctness is not read here).

### 1.3 The cases

`near ≤ 25` etc. are signed `cmp`s of the words above. Every `Draw` is `RNG_Range(U+0x20, aip2[n])`: a single seed step unless `aip2[n]` ≤ 0, which returns 0 with no step (0x0045C393). `Keep(v)` is `sc ← v`.

```
case 1  (0x005EC00E), x ← U:
    s ← aurastate (+0x80, s16)
    if s > 0 and U lacks state s: drop                     ; no draw; the first loop's test is the reverse
    if near ≤ 25: base ← base − 6
    base ← base − 10 if AiStateGroupHeld(U, s), else base + 10
    Keep(Draw + base)

case 2  (0x005EC069), x ← t:
    if aurastate > 0 and U has it: drop
    if auratargetstate (+0x82) > 0 and t has it: drop
    if near ≤ 25: base ← base − 10
    Keep(Draw + base)

case 3  (0x005EC0BD), x ← t:
    if allies > 5: base ← base − 2·allies
    if near ≤ 25: base ← base − 7
    if n32 < 3: base ← base − 10
    Keep(Draw + base + 3·n32 − 9)

case 4  (0x005EC0FA), x ← t:
    if d > aip1[n]²: base ← base − 10
    base ← base + aip1[m]
    if melee or d ≤ 25: base ← base + 10
    if progressive (+4 bit 2):
        Aura(); may drop
        Keep(Draw + base + aip1[h])
    else if aip1[h] > 0 and state = 0:
        Keep(Draw + base − 10)
    else:
        Keep(Draw + base + 4·acc + 3)

case 5  (0x005EC1A8) and case 11 (0x005EC32F), x ← t:
    if clear = 0: drop
    if srvmissile (+0x46) < 0 and srvmissilea (+0x48) ≥ 0 and its Missiles record exists:
        r ← the record's Range (+0x96, s16) − 1
        if d ≥ r²: drop
    if near ≤ 25: base ← base − 5
    if d ≤ 25: base ← base − 5
    if state ≠ 0: base ← base − 5
    case 5:  Keep(Draw + base)
    case 11: Keep(Draw + base + 3·n32)

case 6  (0x005EC209), never kept:
    v ← Range(100)
    if v < (20 when U has no left skill, else 6): UnitSetLeftSkill(U, id, −1)
    drop

case 7  (0x005EC260):
    v ← Draw + base
    if life > 66: drop
    x ← 0
    if O = 0: Range(40); Range(40)                       ; both results discarded
    Keep(v + 10, or v + 20 when life < 45)

case 8  (0x005EC2FA), x ← U:
    v ← Draw + base
    if life > 66: drop                                   ; x is still t, but nothing is kept
    Keep(2·v, or 4·v when life < 45)

case 9, case 10: drop, no draw                           ; both entries 0x005EC4F5

case 12 (0x005EC3A4), x ← t:
    if t is a monster (UnitGetType = 1):
        r ← UnitMonRecord(t);  if r = 0: drop
        if byte r[+0xA0 + G.difficulty] < 25 (unsigned): drop
    if d > aip1[n]²: base ← base − 10
    base ← base + aip1[m]
    if melee or d ≤ 25: base ← base + 10
    if progressive: Aura(); may drop                     ; the else of case 4 has no counterpart here
    v ← Draw + base
    if life < 75: v ← v + 8
    if life < 50: v ← v + 12
    Keep(v)

case 13 (0x005EC47D), x ← t:
    base ← base + aip1[m]
    if aip1[h] > 0 and state = 0: base ← base − 5
    else: base ← base + acc
    if (life < 50 or n10 > 3) and nearO ≠ 0 and nO < 4 and DistSq(U, nearO) > 25:
        Keep(Draw + base + 20);  x ← nearO
    else:
        if d < 25: drop
        if d > 324: base ← base + 10
        Keep(Draw + base)

Aura(), cases 4 and 12:
    s ← aurastate
    if s > 0 and U has it and UNIT_FindStatListByState(U, s) ≠ 0:
        v ← StatListGetBaseStat(the list, aurastat1 (+0x54, s16), 0)
        acc ← acc + v
        if v ≥ 3: drop                                   ; acc keeps the value
```

Width notes. The flag test is `test BYTE [rec+4], [0x006CE270]`, the third element (4) of the mask table at 0x006CE268, so bit 2 of `+4`, the `progressive` column (tbl:Skills.txt:progressive; 0x005EC124, 0x005EC400). The row reads `+0x230` as a byte where `docs/tables/Skills.md` gives `u16`; the high byte is 0 in all 357 rows (`skills-aitype.txt`), so nothing turns on it. Case 12's byte is the `Drain` cell of the difficulty (`+0x0A0 + d`, `docs/tables/MonStats.md`). In case 13 the choice of `nearO` adds 20 *and* sets `x`; if any of its four tests fails the record falls to the `d` tests with `x` still `t` (0x005EC4A7–0x005EC4CF).

**Case 7's calls.** With an owner it calls the position getters five times on `O` and `t` and once `UnitGetSubY(O)`, keeping no result, and draws nothing there; with none, `Range(40)` twice with a position call after each (0x005EC28F–0x005EC2E0). No stock skill has `aitype` 7. Those results reach no store: `x` stays 0 and the list's last two words are 0.

**Self-targets cannot command.** A record of case 1 or 8 is kept with `x = U`, and `Use`'s first test returns 0 for `x = U` (0x005EB8C7, 0x005EB8CB). So in the pick such a record costs a seed step and may hold the top of the list against lower ones, and commands nothing. `aitype` 1 skills command only in the think's first loop. (fn:sub_005EB8B0_AiShadowUseSkill@0x005EB8B0)

**Wrap.** `aip1[n]²` and `r²` fit: the largest magnitudes are (−32 768)² = 2³⁰ and (−32 769)² = 1 073 807 361. `|res ÷ −10|` ≤ 214 748 364. A sum wraps only with `level` near 2³¹, or in case 8's `4·v` when `|v|` ≥ 2²⁹; the `level` of a copied skill is in [1, 24] by `AiShadowMasterSkLvl`, and no stock skill has case 8.

### 1.4 The draws per record, in the second loop

| `aitype` | Draws | Fails to draw when |
|---|---|---|
| 1, stock | one `Draw` | `aurastate` > 0 and `U` lacks it |
| 2, stock | one `Draw` | either state test drops it |
| 3, stock | one `Draw` | never |
| 4, stock | one `Draw` | `Aura` drops it |
| 5, 11, stock | one `Draw` | `clear` = 0, or beyond the missile's `r` |
| 6 | one `Range(100)` | never |
| 7 | one `Draw`, then two `Range(40)` with no owner and `life` ≤ 66 | never |
| 8 | one `Draw` | never |
| 9, 10 (10 stock) | none | always |
| 12, stock | one `Draw` | the monster test or `Aura` drops it |
| 13, stock | one `Draw` | no `nearO` choice and `d` < 25 |
| anything else, or no `aitype` | none | always |

Every draw is on `U`'s seed. `Draw` with `aip2[n]` = 20 is `low % 20`.

### 1.5 The pick

```
while k > 0:                                     ; k ≥ 1 here: the test at 0x005EC550 never fires
    k ← k − 1;  step the seed once;  low ← its new low word
    if low & 3 ≠ 0:
        m ← InMeleeRange(U, L[k].target, 0)       ; 0 for a null target (0x00622C4A)
        if Use(L[k].id, m, L[k].target, L[k].+0xC, L[k].+0x10):
            if SkillRec(id) ≠ 0 and its +0x2E = 19: v18 ← id;  v14 ← 25
            return
if t ≠ 0:                                        ; t is never 0 here (0x005EC5CA)
    if Use(0, InMeleeRange(U, t, 0), t): return
Idle(15)
```

The two zero words go to `Use`'s fifth and sixth arguments, and from there to `MonAiUseSkill`'s last two (0x005EC59C–0x005EC5A3, 0x005EB93D–0x005EB947). `L[0]` is walked last, with skill 0.

### 1.6 What was tested

`tools/ai_sm_check.py` runs the think from 0x005EB970 in `tools/ai_resume.py`'s interpreter, RNG_Range executed and every other callee a stub that logs its words and returns the case's value, and compares it with a model written from this finding. The stubs are the boundary: the check says the pseudocode and the instructions are the same map from those returns, not what the callees return in play. Over 6 000 cases of `random.Random("r71-sm")`, synthetic records included, it found **0 mismatches and 0 stops**, ending `Idle` 4 554, `RunToUnit` 267, a return 1 179; the trace's sha256 starts `492df4f5`. The model covers the whole think, so steps 1 to 11 and 14 to 16 of [catalogue R106](../../specs/monsters/ai/catalogue.md) were run against the code too, and they hold.

Each of the 99 one-term controls changes one constant or reverses one branch alone. 98 fail at least one case; the last, `p_hi`, cannot fail, as a chance of 101 against `Range(100)` is the same as 100. The weakest separate 1 case (`use1_held`, `use1_chance`), 2 (`a6_none`, `a13_far`) and 3 (`left_chance`, `own_prio_dist`).

Of the think's 142 conditional branches, 136 went both ways. The other 6 did not: 0x005EBADC and 0x005EBF5F (a null record pointer, `base + id·0x23C` = 0), 0x005EBB4B (`aitype` is 1 there, dead after the `sub`), 0x005EC550 (`k` = 0, dead since `k` ≥ 1), 0x005EC5CA (`t` = 0), and 0x005EC612 (`SkillRec` returning 0 for an id already found).

The tag stays `[I]`: the interpreter is ours, not ADR-0015's emulator, and its stubs are declared by the case, not logged (run:2026-11-04-r71-sm).

## 2. Row 94: `SWEEP` and `STEP`

`SWEEP`, 0x006E33E0, 64 i32, read at 0x005E0B3A as `[(v1C mod 8 + 8·(dir mod 8))·4 + 0x006E33E0]`, both signed `mod`s (0x005E0B0F–0x005E0B33). It takes the current index `v` and the wanted direction `d`:

| `d` \ `v` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 1 | 2 | 5 | 6 | 7 | 0 |
| 1 | 1 | 1 | 1 | 2 | 3 | 6 | 7 | 0 |
| 2 | 1 | 2 | 2 | 2 | 3 | 4 | 7 | 0 |
| 3 | 1 | 2 | 3 | 3 | 3 | 4 | 5 | 6 |
| 4 | 1 | 2 | 3 | 4 | 4 | 4 | 5 | 6 |
| 5 | 7 | 2 | 3 | 4 | 5 | 5 | 5 | 6 |
| 6 | 7 | 0 | 3 | 4 | 5 | 6 | 6 | 6 |
| 7 | 7 | 0 | 1 | 4 | 5 | 6 | 7 | 7 |

[C] As an equality on the image's 64 elements, and no claim of how it was generated (0x006E33E0, run:2026-11-04-r71-sm, `sweep_crc`): a step by cases, stay when `d = v`, `v + 1` when `(d − v) mod 8` is 1 to 4, `v − 1` when 5 to 7, all mod 8, equals 63 cells; the cell `d = 3, v = 7` holds 6 where the cases give 0. That is the shape ADR-0031's Negative consequence excludes (`g_PathDirTriples`, one patched cell), so the table is listed. At 64 values it is the size of the table that ADR's Neutral consequence names as allowed.

`STEP`, 0x006E33A0, 8 rows of two i32, read at 0x005E0B50 (`x`) and 0x005E0B5F (`y`). [C] As an equality on its 16 elements (0x006E33A0, run:2026-11-04-r71-sm, `step_rule_mismatches=0`): with `j = (i + 1) mod 8`, `k = (i − 1) mod 8`, `clamp(a) = max(−1, min(1, a))`,

```
STEP[i].x = clamp(2 − min(j, 8 − j))
STEP[i].y = clamp(2 − min(k, 8 − k))
```

[I] Each value of `SWEEP` is 0 to 7, so `STEP`'s index stays in range from `v1C`'s first 0 (0x005E09D6). The two tests of [catalogue R94](../../specs/monsters/ai/catalogue.md) step 8 and all its other steps hold against the instructions. No draw. That `STEP[i]` points the way `Dir64To8`'s index `i` names is not read here: the direction table at 0x00745600 is outside this finding.

## 3. Row 25: the frame tables and event 12

[I] Stores 0x005F39E1–0x005F3E07: 132 dwords, from immediates and from `EAX` (−5), `EDX` (1), `ECX` (−6, then 0 from 0x005F3C3B, then 3 from 0x005F3C47). `ai_const_survey.py summary` reads them from the bytes with a decoder that refuses any other instruction: 132 stores, exactly the 132 words the four tables below use, none left over. `emu` runs the same stores in the interpreter and finds 0 differences over 66 rows (`const-emu.txt`). None depends on the entry's inputs.

| Table | Base | Index | Rows | Readers | Given here |
|---|---|---|---|---|---|
| `A` | `EBP−0x2F4` | `v1C + 4·v14`, 25..52 | 28 `(x, y)` | 0x005F408F, 0x005F40AA | shape only; crc32 in `const-summary.txt` |
| `B` | `EBP−0x214` | as `A` | 28 `(x, y)` | 0x005F4136, 0x005F4140, 0x005F416B, 0x005F4186 | shape only; crc32 in `const-summary.txt` |
| `A5` | `EBP−0x38` | `v1C`, 1..5 | 5 `(x, y)` | 0x005F429C, 0x005F42AE | listed below |
| `B5` | `EBP−0x64` | `v1C`, 1..5 | 5 `(x, y)` | 0x005F42F0, 0x005F42F6, 0x005F430F, 0x005F4321 | by rule below |

`A5[1..5]` = (−5, −5), (3, −5), (6, 3), (3, 6), (−5, 3).

[C] As an equality on the image (0x005F39E1, run:2026-11-04-r71-sm, `wisp_b5_rule_mismatches=0`): `B5[p] = A5[((p + 1) mod 5) + 1]`. [I] So each of the five wisps aims two places on around the ring of `A5`'s points.

**`A` and `B`: no rule known.** Rotating `A`'s four places by one gives `B` at `v14` = 6 only; at the other six states it gives 0 to 3 of the four rows (`const-values.txt`), and a description by cases is no rule by ADR-0031. Size alone does not settle the side: 56 values each is below the 64 and 75 it names, but they are 112 for one function's dance. **Not committed.** `tools/ai_const_survey.py values <game.exe>` prints them; `const-values.txt`, sha256 `c6147dd6…`, holds them under `workspace/logs/r71/`. `B` has one `(0, 0)` row, at `v14` = 12, place 4: that wisp's three shots there are the `v18`-only arm. `B5` has no `(0, 0)`, so the five-wisp `(0, 0)` arm (0x005F42F4–0x005F42FF) is reached by no value of the image.

[I] The think stores these on the stack at each entry and reads them only in the dance, so a reimplementation may hold them as constants (0x005F408F). All of [catalogue R25](../../specs/monsters/ai/catalogue.md)'s trigger and dance hold against the instructions; no correction (0x005F3E0A, 0x005F4370).

**Event 12.** [I] `UnitQueueEvent(G, t; 12, end, 0, 0)` at 0x005F4268 with `end` = `G.frame + 1 728 000`, the list's own end frame set by `StatListSetEnd` at 0x005F4255, and the list allocated with flag 2 at 0x005F422F. So [stats/states C1](../../specs/stats/states.md) applies: at that frame `EVENT_TimedListExpire` frees every counting child of the unit's list with flag 2 and an end frame at or before it, unless extended, and the list's stat 80 goes with it. The grant carries no state, so C2's state removal has no part in it. Earlier, death may free it first (states C3). Each of a dance's grants has its own list and its own event. (fn:EVENT_TimedListExpire@0x00580800, fn:UNIT_ExpireTimedLists@0x00627460, fn:STATLIST_Alloc@0x006251F0)

## 4. What the logs can test

Nothing. Over the 160 `*.log` of `workspace/logs/ai/` (`logs-rows.txt`), `AID` lines with `"ai":106`, `143`, `25` and `94` number 0, and with `"ai":2` (the positive control) 1 530; `"th":6207856` (0x005EB970) 0 and `"c":418,` 0. So catalogue's R25l, R94l and R106l stand (0x005B186F, run:2026-11-04-r71-sm). A kept batch with an Assassin's Shadow Master would test § 1.3's arms past the first boundary with `tools/ai_resume.py`; none of this lane's scope and no game was run.

## 5. Corrections to existing statements

*2026-11-04, `lane/r71`, from the instructions above. `catalogue.md` is left to the spec-writer (the entry named in the plan's log).*

1. **Catalogue R106 step 13**, "by aitype (1–13): its terms and target, or next; a kept one draws": wrong in two ways. The draw comes before the list's test and has nothing to do with being kept (a record whose `sc` does not beat the last has drawn), and cases 9 and 10 have no terms. Case 6's draw is `Range(100)`, not `aip2[n]`, and it is never kept; case 7 can draw three times. (0x005EC4E3–0x005EC4FF, 0x005EC209, 0x005EC28F)
2. **Catalogue R106 line `aip`**, "`aip1[h]` is read by a score term": all three of `aip1` are, `[n]` squared in cases 4 and 12, `[m]` added in 4, 12 and 13, `[h]` in the `state` word and case 4. (0x005EC0FD, 0x005EC110, 0x005EC17C)
3. **Catalogue R106a**, "a score list's `+8` and `+0xC` words are stored 0": from the record's start (`+0` target, `+4` id, `+8` score) the two zero stores are `+0xC` and `+0x10`; `+8` is the score, stored non-zero at 0x005EC521. (0x005EC50B–0x005EC52F)
4. **ai/0006 § 2.11**, "per `aitype` (1–8, 11–13) its terms and one `Range(aip2[n])` draw" and "one in the second [loop]": as point 1; stock `aitype` values have at most one draw per skill there, cases 6 and 7 being the exception no stock skill reaches. [Carried to § 2.11 by a dated note.]
5. **The entry's "0x005EA2B0 word"** reads `0x0063A2B0` at 0x005EBE1B; 0x005EA2B0 is `AiSentryCharge`, not a callee here.

## Open questions

- [L] `A` and `B`: the architect's call on committing them. The think needs them for row 25's dance points to be reimplementable.
- [L] Is `SWEEP`'s odd cell `d = 3, v = 7` a slip in the game's table? It only changes which way round the turret turns from the opposite direction, and the code reads the table as it is. Not settled, and it changes nothing a reimplementation needs.
- [L] `STEP[i]` against `Dir64To8`'s index: not read (§ 2).
- [L] Row 106's arms in play: no log (§ 4).
