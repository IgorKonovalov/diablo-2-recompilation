---
spec: data/calc
status: reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [data/excel, rng]
consumed_by: [combat/to-hit]
tags: {C: 77, I: 66, L: 3}
updated: 2026-10-16
---

# Calc formulas: the bytecode, the evaluator and the function table

## Purpose

Some excel cells hold a formula rather than a number: a skill's damage or duration, a number in a skill
description, a missile's damage synergy, a potion's duration and strength. In the shipped data each formula is
already compiled into postfix bytecode, stored in one of four header-less pools (`itemscode.bin`, `misscode.bin`,
`skillscode.bin`, `skilldesccode.bin`), and the record holds an s32 offset into the pool, −1 when the cell is
blank. When the game needs the value, it runs a small stack machine over those bytes with a *context* (a unit, a
skill, a level), a *variable reader* and a *function table*. This spec gives the encoding, the evaluator, the three
contexts with their function tables and variables, and the compiler that writes the bytes under `-txt`. The
evaluator draws random numbers only through the `rand` function, which no stock formula reached in play.

What the formulas compute in combat (a skill's damage, a missile's synergy) is out of scope (ADR-0002); this spec
is the machine that the in-scope consumers call.

```mermaid
flowchart LR
    txt["formula cell text<br/>skills, skilldesc, missiles, misc"] -->|"-txt only: CALC_Compile"| pool["*code.bin pool<br/>postfix bytes, 00-terminated"]
    rec["excel record<br/>s32 offset, -1 = blank"] --> entry
    pool --> entry["context entry point<br/>SKILLS_EvalCalc, SKILLS_EvalDescCalc,<br/>MISS_EvalCalc, ITEMS_EvalCalc"]
    entry -->|"code, len, varFn, funcs, ctx"| eval["CALC_Eval<br/>int32 stack of 64"]
    eval -->|"04 i"| var["variable reader<br/>skillcalc / misscalc / items: 0"]
    eval -->|"01 f"| fn["function table<br/>min max rand skill miss stat sklvl"]
    eval --> out["int32 value"]
```

## Entry points

| When | Function | Tag |
|---|---|---|
| `-txt` only: a formula cell of skills, skilldesc, missiles, or weapons/armor/misc is compiled | fn:sub_00611BD0_SkillsCalcCell@0x00611BD0, fn:sub_00611C70_SkillDescCalcCell@0x00611C70, fn:sub_006619A0_MissCalcCell@0x006619A0, fn:sub_00631530_ItemCalcCell@0x00631530 → fn:CALC_Compile@0x006C1AE0 | [C] |
| A skill formula (`skillscode`) is needed | fn:SKILLS_EvalCalc@0x00646CA0 (76 call sites seen) | [C] |
| A skill description number (`skilldesccode`) is shown | fn:SKILLS_EvalDescCalc@0x00646D00, from 0x004EDEF1 and 0x004EDF0D (the skill tree's description) | [C] |
| A skill's formula-valued variable, elemental synergy or to-hit formula is read | fn:CALC_Eval@0x006C0BC0 called directly from fn:SKILLS_CalcVar@0x00646460 (0x00646A07), fn:SKILLS_GetElemMin@0x00644D50 / fn:SKILLS_GetElemMax@0x00644E40 / fn:SKILLS_GetElemLen@0x00644F20, fn:SKILLS_GetToHit@0x006449F0 | [C] |
| A missile formula (`misscode`) is needed | fn:MISS_EvalCalc@0x0064B7C0, from fn:MISS_GetElemMin@0x0064B100 / fn:MISS_GetElemMax@0x0064B1D0 | [I] |
| A stamina, antidote or thawing potion is drunk (`itemscode`) | fn:ITEMS_EvalCalc@0x00627C20, from the item-use functions of data:g_ItemUseFns@0x00741790 by the used item's `pSpell`, reached through fn:sub_005BF240_ItemUse@0x005BF240 (the stamina, antidote and thawing potions through fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0: its `len`, `calc1`, `calc2`) | [I] |

All rows: [data/0005 § 6](../../findings/data/0005-calc.md#6-run-time-entry-points-contexts-and-functions),
[§ 10](../../findings/data/0005-calc.md#10-the-evaluator-at-run-time-phase-2-run2026-10-16-calc); the run-time rows
from the return addresses of run:2026-10-16-calc. The missile and item rows stay `[I]` because their callers
were read only through the run's return addresses, not as code.

## Inputs

### Tables

| Anchor | Used for |
|---|---|
| tbl:Skills.txt:calc1 and the other 35 formula columns of [Skills.md](../../tables/Skills.md) | offsets into `skillscode` |
| skilldesc `ddam calc1/2`, `p1..3dmmin`, `p1..3dmmax`, `desccalca/b1..6`, `dsc2calca/b1..4`, `dsc3calca/b1..7` (no table doc) | offsets into `skilldesccode` |
| missiles `SrvCalc1`, `CltCalc1`, `SHitCalc1`, `CHitCalc1`, `DmgCalc1`, `DmgSymPerCalc`, `EDmgSymPerCalc` (no table doc) | offsets into `misscode` |
| tbl:Misc.txt:len, tbl:Misc.txt:calc1, `calc2`, `calc3`, `spelldesccalc` (the same columns, absent, in weapons and armor) | offsets into `itemscode` |
| tbl:SkillCalc.txt:code | variable names of skill and skilldesc formulas: row index = variable operand |
| tbl:MissCalc.txt:code | variable names of missile formulas: row index = variable operand |
| tbl:Skills.txt:Param1 … `Param8`, `ToHit`, `LevToHit`, `ToHitCalc`, `mana`, `lvlmana`, `manashift`, `calc1..4`, `auralencalc` | read by the row-only and formula-valued skill variables (§ G) |
| the pools `itemscode.bin`, `misscode.bin`, `skillscode.bin`, `skilldesccode.bin` | the bytecode ([calc.md format](../../formats/calc.md)) |

### Runtime state

| State | Type | Source |
|---|---|---|
| pool buffer and size | bytes, u32 | `struct:DataTables+0x40` skillscode, `+0x4C` skilldesccode, `+0x60` misscode, `+0x98` itemscode (size after each) |
| skills context | `{unit, skill: i32, lvl: i32}` | built by the skills entry points |
| missile context | `{missile, owner, missileId: i32, lvl: i32}` | built by `MISS_EvalCalc` |
| item context | `{unit, arg2}` | built by `ITEMS_EvalCalc`; `arg2` not read |
| unit seed | Seed (see [rng](../rng/README.md)) | `Unit+0x20`, used only by `rand` |

**Inputs that are unit state (value oracles).** The following values read the unit and are inputs to this spec, not
derived by it. A reimplementation supplies them from its own skills and stats code; the run took them from the log
(ADR-0004 value oracles, no seed crosses them).

- [C] Functions: `skill(s, v)` (skills and missiles contexts), `miss(m, v)`, `stat(id, k)`, and `sklvl(s, v, w)`
  when `v` or `w` is a unit-reading variable. (run:2026-10-16-calc, [data/0005 § 10](../../findings/data/0005-calc.md#10-the-evaluator-at-run-time-phase-2-run2026-10-16-calc))
- [C] Variables (21 `skillcalc` codes): `edmn edmx edln edns edxs enma exma enms exms m1en m1ex m2en m2ex m3en m3ex
  m1eo m1ey ulvl math madm macr`. (run:2026-10-16-calc, fn:SKILLS_CalcVar@0x00646460)

The run confirms only that these are inputs, consumed by the evaluator in code order; what each one computes is
stated in § F and § G, with its own tag, for orientation only.

### Constants

| Name | Value | Anchor | Tag |
|---|---|---|---|
| `STACK_SLOTS` | 64 int32 slots | fn:CALC_Push@0x006C0B80 | [I] |
| `COMPILE_BUF` | 1 024 bytes per compiled cell | fn:sub_00611BD0_SkillsCalcCell@0x00611BD0 | [C] |
| `MAX_OPERATORS` | 64 on the compiler's operator stack | 0x006C1B77 | [I] |
| `PREC[00..16]` | `17 01 02 03 09 09 09 09 09 09 0F 0F 0F 0F 0F 0F 11 11 13 13 14 15 16` | data:g_CalcPrecedence@0x006FC874 | [C] |
| skills function table | 7 entries `{fn, argc}` | data:g_SkillsCalcFuncs@0x00745774, data:g_nSkillsCalcFuncs@0x007457AC | [C] |
| missiles function table | 4 entries | data:g_MissCalcFuncs@0x00745828, data:g_nMissCalcFuncs@0x00745848 | [I] |
| items function table | 4 entries | data:g_ItemCalcFuncs@0x0074463C, data:g_nItemCalcFuncs@0x0074465C | [I] |

## Algorithm

### A. Pools and formula columns

- [C] A formula column holds an s32 offset into its family's pool, or −1 when the cell is blank, the column is absent
  from the `.txt`, or the compile failed. The pool is the compiled cells' bytes appended in record order (weapons, then
  armor, then misc for `itemscode`), within a record in `.txt` column order, with no sharing: two equal texts are
  stored twice. (fn:sub_006118B0_CalcPoolAppend@0x006118B0, [data/0005 § 1](../../findings/data/0005-calc.md#1-formula-columns-and-pools), [§ 8](../../findings/data/0005-calc.md#8-reproduction))
- [I] Within a record the cells present in the `.txt` are compiled in `.txt` column order, then the descriptor
  entries the `.txt` lacks, in descriptor order (they store −1). Stock data cannot tell the two orders apart; an
  edited `skills.txt` with `perdelay`, `skpoints` and `delay` all filled can. (fn:EXCEL_ParseTxt@0x006BD780, [data/0005 § 9](../../findings/data/0005-calc.md#9-compile-order-within-a-row-backlog-2026-10-15-static))
- [C] Stock pool sizes: `misscode` 196, `skillscode` 5 891, `skilldesccode` 4 252, `itemscode` 158 bytes; 1 790
  compiled cells over 30 217 formula fields. (fn:CALC_Compile@0x006C1AE0, [data/0005 § 8](../../findings/data/0005-calc.md#8-reproduction))
- [I] A run-time entry point evaluates only when `offset < size` (unsigned compare), so −1 yields 0 without calling the
  evaluator. (fn:SKILLS_EvalCalc@0x00646CA0, 0x0064B818, fn:ITEMS_EvalCalc@0x00627C20)

### B. The encoding

```mermaid
flowchart LR
    t["(lvl &lt; 4) ? lvl : (2+lvl/3)"] --> b["04 10 | 07 04 | 0A | 04 10 | 07 02 | 04 10 | 07 03 | 13 | 10 | 16 | 00"]
    b --> d["lvl, 4, &lt;, lvl, 2, lvl, 3, ÷, +, ?:, end"]
```

Postfix: the operands of an operator are pushed before it. One opcode byte, then a fixed operand.

| Byte | Operand | Meaning | Tag |
|---|---|---|---|
| `00` | — | end: the value is the top of the stack | [C] (0x006C1148, run:2026-10-16-calc) |
| `01` | u8 *f* | call function *f* of the context's table on the values pushed before it | [C] (0x006C0D06, run:2026-10-16-calc) |
| `02` | — | an unclosed `(` flushed by the compiler; ends evaluation like `00` | [C] (0x006C1148, run:2026-10-16-calc) |
| `03` | — | ends evaluation like `00` (no compiler path emits it) | [I] (0x006C1148) |
| `04` | u8 *i* | push variable *i* (index read unsigned) | [C] (0x006C0C0E, run:2026-10-16-calc) |
| `05` | s16 *i* | push variable *i* | [I] (0x006C0C0E) |
| `06` | s32 *i* | push variable *i* | [I] (0x006C0C0E) |
| `07` | s8 | push constant | [C] (0x006C0CA9, run:2026-10-16-calc) |
| `08` | s16 | push constant | [C] (0x006C0CA9, run:2026-10-16-calc) |
| `09` | s32 | push constant | [I] (0x006C0CA9) |
| `0A` | — | `<` | [C] (0x006C1164, run:2026-10-16-calc) |
| `0B` | — | `>` | [C] (0x006C1164, run:2026-10-16-calc) |
| `0C` `0D` `0E` `0F` | — | `<=` `>=` `==` `!=` | [I] (0x006C1164) |
| `10` `11` `12` `13` | — | `+`, binary `−`, `×`, `÷` | [C] (0x006C1164, 0x006C0E9C, run:2026-10-16-calc) |
| `14` | — | `^` (power) | [I] (0x006C0F57) |
| `15` | — | unary `−` | [C] (0x006C1164, run:2026-10-16-calc) |
| `16` | — | `?:` | [C] (0x006C0F02, run:2026-10-16-calc) |
| > `16` | — | ends evaluation like `00` | [I] (0x006C1148) |

Multi-byte operands are little-endian. Tags: the bytes in stock pools are `[C]` by recompiling every stock cell
byte for byte and by the run executing every one of them; the others are read from the code only.
(fn:CALC_EmitConst@0x006C19C0, fn:CALC_EmitVar@0x006C1A50, fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc,
[data/0005 § 4–5](../../findings/data/0005-calc.md#4-the-compiler-calc_compile))

- [C] Constants and variable indices take the narrowest form: −128..127 → `07`/`04` + 1 byte, −32 768..32 767 →
  `08`/`05` + 2 bytes, else `09`/`06` + 4 bytes. Stock data uses `07`, `08` and `04` only. (fn:CALC_EmitConst@0x006C19C0, fn:CALC_EmitVar@0x006C1A50)
- [C] The opcodes present in the stock pools are exactly `00 01 02 04 07 08 0A 0B 10 11 12 13 15 16`; the item pool
  holds only constants (`00 07 08`). ([data/0005 § 8](../../findings/data/0005-calc.md#8-reproduction), fn:CALC_Compile@0x006C1AE0)

### C. The compiler (`-txt` only)

A stock run never compiles: the pools ship compiled. A reimplementation that reads `.txt` sources must reproduce
this compiler to get the same bytes, and the same −1 where the game rejects a cell.

**C1. Tokens.** `CALC_NextToken` returns one token per call; a token the tokenizer cannot read ends the stream and
whatever follows is ignored.

- [C] Spaces and `"` characters are skipped (a spreadsheet-quoted `"min(24,ln12)"` reads as `min(24,ln12)`). (fn:CALC_NextToken@0x006C11C0)
- [C] A digit starts an unsigned decimal number, accumulated as `value ← value × 10 + digit` in int32 with no overflow
  check. (0x006C1235)
- [C] A letter starts a name of letters and digits (`_` ends it). If the next non-space character is `(` and the
  context knows the name as a function, the token is a function call and the `(` is consumed; otherwise the name
  goes to the identifier callback (C2). (0x006C1387, 0x006C1467)
- [C] `'text'` takes everything up to the next `'` (at most 255 characters) and goes to the identifier callback;
  `.name` does too and always yields a constant (a negative callback result ends the stream). (0x006C12A1, 0x006C1692)
- [C] Operators: `( ) , + - * / ? : ^ <= < > >= == !=`. A lone `!` or `=`, NUL and any other character end the
  stream. (0x006C14C2)

**C2. Names, per context.** The identifier callback returns an index and a flag (1 = constant, 0 = variable); it knows
which function call, if any, encloses the name.

- [C] Function names, case-insensitive: skills and skilldesc `min`=0 `max`=1 `rand`=2 `skill`=3 `miss`=4 `stat`=5
  `sklvl`=6 (arity 3 for `sklvl`, else 2); missiles `min max rand skill miss` = 0–4 (arity 2); items `min max rand
  stat` = 0–3 (arity 2). (fn:sub_00611930_SkillsCalcFnLookup@0x00611930, fn:sub_006119E0_SkillsCalcFnArity@0x006119E0,
  fn:sub_00661800_MissCalcFnLookup@0x00661800, fn:sub_00631430_ItemCalcFnLookup@0x00631430)
- [C] Skills and skilldesc identifiers: inside `skill(` or `sklvl(` a skill name becomes its skills row (constant),
  else the `skillcalc` code of the name's first four characters (space-padded) becomes that row (constant); inside
  `miss(` the same against missiles and `misscalc`; inside `stat(` an itemstatcost `Stat` name becomes its row, else
  `base` → 1, `mod` → 2, anything else → 0 (constants); elsewhere the `skillcalc` row, **as a variable**. Name
  lookups are case-insensitive and take the first matching row. (fn:sub_006119F0_SkillsCalcIdent@0x006119F0)
- [C] Missile identifiers: inside `skill(` a skill name (constant), else the `skillcalc` code; inside `miss(` a missile
  name, else the `misscalc` code; elsewhere the `misscalc` row as a variable. (fn:sub_00661880_MissCalcIdent@0x00661880)
- [C] Item identifiers: inside `stat(` as for skills; elsewhere variable 0. An unknown identifier anywhere compiles
  to the constant 0. (fn:sub_006314A0_ItemCalcIdent@0x006314A0)

**C3. Operator precedence.**

```
Compile(text, ctx) → bytes or FAIL:                                     [C] (fn:CALC_Compile@0x006C1AE0, fn:CALC_PushOperator@0x006C18A0)
  ops: stack of (op: u8, arg: i32)  ; at most 64 entries
  depth: i32 ← 0                    ; values the emitted code would leave on the stack
  operand: bool ← false             ; last token was a number, variable or function name
  hasVar: bool ← false
  for each token:
    "("      : push (2, 0)
    ")"      : if ops is empty: FAIL
               loop:
                 if top.op = 2: break
                 n ← Arity(top); if depth < n: FAIL
                 emit top.op; depth ← depth + 1 − n
                 if top.op = 1: emit (u8) top.arg; break      ; a call closes at its ")"
                 pop; if ops is empty: FAIL
               pop                                            ; the "(" marker or the call
    ","      : Flush(3)                                       ; pushes nothing; operand unchanged
    "-"      : Flush(operand ? 0x11 : 0x15); push it; operand ← false
    "?"      : Flush(0x16); push 0x16                         ; operand unchanged
    ":"      : Flush(0x17)                                    ; pushes nothing; operand unchanged
    other operator with opcode c : Flush(c); push c; operand ← false
    number   : EmitConst(value); operand ← true
    variable : EmitVar(index); operand ← true; hasVar ← true
    function : push (1, index); operand ← true; hasVar ← true
  Flush(0); if nothing was emitted: FAIL; emit 00               ; the final flush
  if not hasVar:                                                [C] (0x006C1EB8)
    v: i32 ← Eval(bytes, varFn: none, funcs: none)            ; constant folding
    bytes ← EmitConst(v) ++ 00
  return bytes                                                ; FAIL → the cell stores −1

Flush(c):
  while ops not empty and top.op ≠ 1 and c ≠ 1 and top.op < 0x17 and PREC[top.op] ≥ c:
    n ← Arity(top.op); if depth < n: FAIL
    emit top.op; pop; depth ← depth + 1 − n
```

Operator opcodes: `<` `0A`, `>` `0B`, `<=` `0C`, `>=` `0D`, `==` `0E`, `!=` `0F`, `+` `10`, binary `-` `11`, `*`
`12`, `/` `13`, `^` `14`, unary `-` `15`, `?` `16`. Arity: `0A`–`14` take 2, `15` takes 1, `16` takes 3, `01` the
function's arity, every other opcode 0. Note that the loop compares `PREC[top]` with the incoming **opcode**, not
with the incoming operator's precedence; with this table both give the same output.

- [C] Effect of the table: `+ −` pop `+ − × ÷ ^ neg ?:`; `× ÷` pop `× ÷ ^ neg ?:`; `^` pops `^ neg ?:` (left-associative);
  comparisons pop everything but `(` and calls; `?` pops only `?:`; `:` pops nothing `?` left behind. Every stock
  ternary has its condition in parentheses, and those reproduce. (data:g_CalcPrecedence@0x006FC874, [data/0005 § 4](../../findings/data/0005-calc.md#4-the-compiler-calc_compile))
- [I] The resulting quirks, which no stock cell exercises: unparenthesised `a < b ? c : d` compiles as `a b c d ?: <`;
  an operator inside an unparenthesised then-branch fails the compile (`lvl ? 1+lvl : 3` → −1); an unparenthesised
  else-branch takes the whole ternary as its left operand (`lvl ? 2 : 3+lvl` is `(lvl?2:3)+lvl`); `-` after `,`, `?`,
  `:` or `(` that follows a function name is binary, so `min(-1,lvl)` and `a ? -1 : 2` fail. (0x006C18DE, fn:CALC_PushOperator@0x006C18A0)
- [C] An unclosed `(` stays on the operator stack and the final flush emits it as byte `02`. Stock case: skills
  `Fire Wall` `EDmgSymPerCalc` = `(skill('Warmth'.blvl)*par8+skill('Inferno'.blvl)*par7` (no `)`), whose bytes end
  `… 12 10 02 00`. An unclosed function call is never flushed and is lost. (fn:CALC_PushOperator@0x006C18A0)
- [C] A cell whose text yields no token (one space: skilldesc `revive` `desccalcb2`) emits nothing and fails: −1, no
  pool entry. (0x006C1992)
- [C] Folding: `-100` is stored as `07 9C 00` and `-37` as `07 DB 00`, not `07 64 15 00`. (fn:CALC_Compile@0x006C1AE0, 0x006C1EB8)
- [I] Limits: more than 64 stacked operators, or more than 1 024 output bytes, fail the compile. (0x006C1B77, 0x006C1942)

### D. The evaluator — `CALC_Eval`

```mermaid
flowchart TD
    s["op ← next byte"] --> e{"op"}
    e -->|"04 05 06"| v["push varFn(i, ctx)"]
    e -->|"07 08 09"| c["push constant"]
    e -->|"01 f"| f["pop argc args, push funcs[f](a, b, c, ctx)"]
    e -->|"0A..14"| b["r ← pop, l ← pop, push l OP r"]
    e -->|"15"| n["push −pop"]
    e -->|"16"| t["else, then, cond ← pop ×3<br/>push cond ? then : else"]
    e -->|"00 02 03 > 16"| r["return top, 0 if empty"]
    v --> s
    c --> s
    f --> s
    b --> s
    n --> s
    t --> s
```

```
Eval(code: bytes, len: u32, varFn, funcs, nFuncs: i32, ctx) → i32:      [C] (fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc)
  stack: i32[64], empty
  p: u32 ← 0
  0. if (i32) len ≤ 0: return 0                                           [I] (0x006C0BCD)
  1. while p < len:
  2.   op: u8 ← code[p]; p ← p + 1
  3.   if an operand of op would start at or past len: return 0          [I] (0x006C0BC0)
  4.   switch op:
  4a.  case 04, 05, 06:                                                   [C] (0x006C0C0E, run:2026-10-16-calc)
         i ← u8 | s16 | s32 operand
         if varFn is none: return 0                                       [I] (0x006C0C0E)
         Push(varFn(i, ctx))                                              ; read now, in code order
  4b.  case 07, 08, 09: Push(s8 | s16 | s32 operand)                      [C] (0x006C0CA9, run:2026-10-16-calc)
  4c.  case 01:                                                           [C] (0x006C0D06, run:2026-10-16-calc)
         f: u8 ← operand
         if f ≥ nFuncs: Push(0); continue                                 [I] (0x006C0D06) ; the arguments stay on the stack
         argc ← funcs[f].argc
         argc 3: c ← Pop(); b ← Pop(); a ← Pop()
         argc 2: b ← Pop(); a ← Pop(); c ← 0
         argc 1: a ← Pop(); b ← 0; c ← 0                                  [I] (0x006C0D06) ; no stock function has argc 0 or 1
         argc 0: a ← b ← c ← 0                                            [I] (0x006C0D06)
         other : Push(0); continue                                        [I] (0x006C0D06)
         Push(funcs[f].fn(a, b, c, ctx))                                  ; called now, in code order
  4d.  case 0A, 0B: r ← Pop(); l ← Pop(); Push(l < r | l > r ? 1 : 0)     [C] (0x006C1164, run:2026-10-16-calc) ; signed
  4e.  case 0C..0F: r ← Pop(); l ← Pop(); Push(l <= r | l >= r | l = r | l ≠ r ? 1 : 0)   [I] (0x006C1164) ; signed
  4f.  case 10, 11, 12: r ← Pop(); l ← Pop(); Push(l + r | l − r | l × r) [C] (0x006C1164, run:2026-10-16-calc)
         ; int32; on overflow the result wraps modulo 2^32               [I] (0x006C1164)
  4g.  case 13: r ← Pop(); l ← Pop()                                      [C] (0x006C0E9C, run:2026-10-16-calc)
         if r = 0: Push(0)                                                [I] (0x006C0EC6)
         else: Push(l ÷ r)                                                ; truncation toward zero (idiv)
         ; no guard for INT32_MIN ÷ −1: the idiv raises the x86 divide error [I] (0x006C0ECE)
  4h.  case 14: e ← Pop(); b ← Pop()                                      [I] (0x006C0F57)
         Push(e ≤ 0 ? 1 : b multiplied by itself e − 1 times)             ; int32, wraps
  4i.  case 15: Push(−Pop())                                              [C] (0x006C1164, run:2026-10-16-calc)
  4j.  case 16: else_ ← Pop(); then_ ← Pop(); cond ← Pop()                [C] (0x006C0F02, run:2026-10-16-calc)
         Push(cond ≠ 0 ? then_ : else_)
  4k.  case 00, 02: return stack empty ? 0 : Pop()                        [C] (0x006C1148, run:2026-10-16-calc)
  4l.  case 03, > 16: return stack empty ? 0 : Pop()                      [I] (0x006C1148)
  5. return 0                                                             [I] (fn:CALC_Eval@0x006C0BC0) ; ran past len

Push(x): if 64 values are on the stack, x is dropped; else push x        [I] (fn:CALC_Push@0x006C0B80)
Pop(): 0 if the stack is empty; else pop                                  [I] (fn:CALC_Pop@0x006C0BA0)
```

Step notes:

- 4a, 4c. [C] Every variable is read and every function called at its own opcode, in code order, whether or not the
  surrounding ternary keeps its value: the postfix code evaluates both branches. Raise Skeleton's `petmax` reads `lvl`
  three times at level 3 though only the then-branch is used, and Zeal's description at level 4 reads the
  else-branch's `lvl` and `par4` though it keeps the then-branch's 0 (worked examples 1 and 3). The replay requires
  the logged reads and calls, in order, for every one of the run's 386 ternary evaluations (150 else, 236 then), and
  the code has no jump opcode that could skip a branch. (fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc,
  [data/0005 § 10](../../findings/data/0005-calc.md#10-the-evaluator-at-run-time-phase-2-run2026-10-16-calc))
- 4c. [C] The function is called with `a` in ECX, `b` in EDX and `c`, `ctx` on the stack; the logged function pointer
  for each index is the context table's entry. (data:g_SkillsCalcFuncs@0x00745774, run:2026-10-16-calc)
- 4g. [C] Division truncates toward zero, not toward −∞: 25 logged evaluations divided a negative value inexactly and
  match `idiv`. (0x006C0E9C, run:2026-10-16-calc)
- 4g. [I] Between the zero test and `cdq; idiv` there is no other test, and `CALC_Eval` sets up no exception frame:
  `INT32_MIN ÷ −1` raises the processor's divide error instead of returning a value. No stock formula can produce
  it; a reimplementation that must not crash should treat it as undefined. (0x006C0EC6, 0x006C0ECE, fn:CALC_Eval@0x006C0BC0)
- 4j. [I] The condition's pop is guarded separately: with fewer than three values on the stack the else-value wins.
  (0x006C0F2C)
- 4k. [C] `02` ends the evaluation with the top of the stack: Fire Wall's unclosed `(` returned at `02` in 100
  logged evaluations, the `00` after it never reached. (0x006C1148, run:2026-10-16-calc)

### E. Contexts

```mermaid
flowchart LR
    sk["SKILLS_EvalCalc / SKILLS_EvalDescCalc<br/>(unit, offset, skill, lvl)"] --> ctxs["ctx = {unit, skill, lvl}<br/>sub_00646BE0_SkillsCalcVar, g_SkillsCalcFuncs × 7"]
    direct["SKILLS_CalcVar, GetElemMin/Max/Len, GetToHit<br/>(own frame)"] --> ctxs
    ms["MISS_EvalCalc<br/>(missile, owner, offset, missileId, lvl)"] --> ctxm["ctx = {missile, owner, missileId, lvl}<br/>sub_0064B6E0_MissCalcVar, g_MissCalcFuncs × 4"]
    it["ITEMS_EvalCalc<br/>(unit, arg2, offset)"] --> ctxi["ctx = {unit, arg2}<br/>sub_00627B40_ItemCalcVar → 0, g_ItemCalcFuncs × 4"]
    ctxs --> ev["CALC_Eval(pool + offset, size − offset, …)"]
    ctxm --> ev
    ctxi --> ev
```

```
EvalSkill(pool, unit, offset: u32, skill: i32, lvl: i32) → i32:         [C] (fn:SKILLS_EvalCalc@0x00646CA0, fn:SKILLS_EvalDescCalc@0x00646D00, run:2026-10-16-calc)
  1. if offset ≥ pool.size: return 0                                      [I] (fn:SKILLS_EvalCalc@0x00646CA0) ; unsigned, so −1 → 0
  2. ctx ← {unit, skill, lvl}
  3. return Eval(pool.bytes + offset, pool.size − offset,
                 SkillVar, SKILLS_FUNCS, 7, ctx)
     ; pool = skillscode for SKILLS_EvalCalc, skilldesccode for SKILLS_EvalDescCalc

EvalMissile(missile, owner, offset: u32, missileId: i32, lvl: i32) → i32:   [C] (fn:MISS_EvalCalc@0x0064B7C0, run:2026-10-16-calc-emu; step 4's "0 without data" [I])
  1. if offset ≥ misscode.size: return 0
  2. if missile ≠ none and missile is not unit type 3: return 0
  3. if missileId < 0: missileId ← missile's class (Unit+0x04)
  4. if lvl < 0: lvl ← s16 at +0x0C of the missile's data (Unit+0x14), 0 without data
  5. ctx ← {missile, owner, missileId, lvl}
  6. return Eval(misscode + offset, misscode.size − offset, MissVar, MISS_FUNCS, 4, ctx)

EvalItem(unit, item, offset: u32) → i32:                                  [I] (fn:ITEMS_EvalCalc@0x00627C20)
  1. if offset ≥ itemscode.size: return 0
  2. ctx ← {unit, item}                                                    ; the user and the used item
  3. return Eval(itemscode + offset, itemscode.size − offset, ItemVar, ITEM_FUNCS, 4, ctx)
     ; ItemVar returns 0 for every index
```

- [C] The length passed is the pool size minus the offset, not the cell's length: evaluation stops at the cell's
  `00` (or `02`). The direct callers (`SKILLS_CalcVar`, `SKILLS_GetElemMin`/`Max`/`Len`, `SKILLS_GetToHit`) build
  the same `{unit, skill, lvl}` context in their own frame and call `CALC_Eval` with the same reader and table.
  (fn:CALC_Eval@0x006C0BC0, 0x00646A07, 0x00644E02, 0x00644EE1, 0x00645007, 0x00644A79, run:2026-10-16-calc)
- [C] The evaluator itself reproduced all 56 item-context evaluations of the run, all of them potion drinks; the
  missile context ran 1 044 times, every one with only `skill` calls and no variable read. (fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc)
- [I] Hovering a potion evaluated nothing; `ITEMS_EvalCalc` ran from 0x005BEDA0 when a stamina, antidote or thawing
  potion was drunk, on its `len`, `calc1` and `calc2` cells. (fn:ITEMS_EvalCalc@0x00627C20, run:2026-10-16-calc)
- [I] **The item context.** The callers are the item-use functions of `g_ItemUseFns` (`{test, use}` pairs indexed by
  the used item's `pSpell`, 31 entries), called from `sub_005BF240_ItemUse`; each passes **the user** as `unit` and
  **the used item** as the second argument. Since the item variable reader returns 0 and `rand`/`stat` read
  `ctx.unit`, no stock formula reads the item. (0x00627C7A, 0x005BF2D3–0x005BF388, fn:sub_005BF240_ItemUse@0x005BF240,
  data:g_ItemUseFns@0x00741790, fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0)
- [C] **The missile context, by emulation.** On the stock `misscode` pool and the 684 stock `missiles` records,
  `MISS_EvalCalc` evaluated the 13 distinct stock cells that need no unit at 9 levels each, once with no missile
  (`missileId` and `lvl` as given) and once with a missile unit (type 3, class = the row, level in its data `+0x0C`)
  and `missileId = lvl = −1`, so both came from the unit; a type-1 unit and an offset at the pool's end gave 0. 236
  calls, 0 mismatches against `tools/calc.py`. The emulation covers the code's map from the bytes it reads: that the
  `s16` at `+0x0C` of a missile's data is the missile's level is not shown by it.
  (fn:MISS_EvalCalc@0x0064B7C0, fn:sub_0064B6E0_MissCalcVar@0x0064B6E0, fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc-emu)

### F. Function tables

| Index | Skills / skilldesc | Missiles | Items | argc |
|---|---|---|---|---|
| 0 | `min` | `min` | `min` | 2 |
| 1 | `max` | `max` | `max` | 2 |
| 2 | `rand` | `rand` | `rand` | 2 |
| 3 | `skill` | `skill` | `stat` | 2 |
| 4 | `miss` | — (compiles as `miss`, index ≥ 4 at run time) | — | 2 |
| 5 | `stat` | — | — | 2 |
| 6 | `sklvl` | — | — | 3 |

- [C] The skills table has 7 entries in this order with these argument counts. (data:g_SkillsCalcFuncs@0x00745774, data:g_nSkillsCalcFuncs@0x007457AC, run:2026-10-16-calc)
- [I] The missile and item tables have 4 entries each, in the order shown. A missile formula that calls `miss`
  compiles to `01 04` and, at run time, pushes 0 and leaves its two arguments on the stack (4c). No stock missile
  formula calls it. (data:g_MissCalcFuncs@0x00745828, data:g_ItemCalcFuncs@0x0074463C)

```
min(a, b) → a < b ? a : b              ; signed                         [C] (fn:sub_006436E0_SkillsCalcMin@0x006436E0, run:2026-10-16-calc)
max(a, b) → a > b ? a : b              ; signed                         [C] (fn:sub_006436F0_SkillsCalcMax@0x006436F0, run:2026-10-16-calc-emu)
rand(a, b):                                                             [C] (fn:sub_00643700_SkillsCalcRand@0x00643700, fn:RNG_RangeB@0x0045C3E0, run:2026-10-16-calc-emu)
  if ctx is none: return 0
  if a ≥ b: return a                                    ; no draw
  return a + RNG.Range(seed: ctx.unit.seed (Unit+0x20), n: b − a + 1)    ; draw#1
sklvl(s, v, w):                                                         [C] (fn:sub_00646C60_SkillsCalcSklvl@0x00646C60, run:2026-10-16-calc)
  L: i32 ← SkillVar(v, ctx.unit, ctx.skill, ctx.lvl)
  return SkillVar(w, ctx.unit, s, L)
skill(s, v)  → input: variable v of skill s at the unit's current level of s (bonuses included)   [I] (fn:sub_00646C00_SkillsCalcSkill@0x00646C00)
miss(m, v)   → input: missile variable v of missile m at ctx.lvl                                  [I] (fn:sub_00643740_SkillsCalcMiss@0x00643740)
stat(id, k)  → input: the unit's stat id; k = 1 base, k = 2 the second accessor, else the full value; id 19 the attack rating   [I] (fn:sub_00643770_SkillsCalcStat@0x00643770)
```

- [C] `min` is computed and matched 979 times; `sklvl` 50 times where both its variables read only the row (§ G). (run:2026-10-16-calc, fn:sub_006436E0_SkillsCalcMin@0x006436E0)
- [C] **`min`, `max` and `rand` of all three tables, by emulation**: 5 000 cases each (edge values `0`, `±1`,
  `INT32_MIN/MAX`, a range that wraps to `n ≤ 0`, a NULL context, then random), 45 000 calls, 0 mismatches. Each
  `rand` stepped its seed in 2 913 cases: the skills and items ones the seed at `ctx.unit + 0x20`, the missiles one the
  8 bytes at `ctx + 0x20`, and none touched the other copy. So `max` of row 326 (`BearSmite`) and `rand` of row 282
  (`Imp Inferno`), the only stock cells calling them, are these functions. (fn:sub_006436F0_SkillsCalcMax@0x006436F0,
  fn:sub_00643700_SkillsCalcRand@0x00643700, fn:sub_00627B50_ItemCalcMin@0x00627B50, fn:sub_00627B60_ItemCalcMax@0x00627B60,
  fn:sub_00627B70_ItemCalcRand@0x00627B70, fn:sub_0064B700_MissCalcMin@0x0064B700, fn:sub_0064B710_MissCalcMax@0x0064B710,
  fn:sub_0064B720_MissCalcRand@0x0064B720, run:2026-10-16-calc-emu)
- [I] `skill(s, v)` takes the level through `SKILLS_FindUnitSkill` and `SKILLS_GetSkillLevel(unit, entry, 1)` (base
  plus bonus levels, clamped to `[0, max]`), 0 when the unit lacks the skill, then `SkillVar(v, unit, s, level)`. The
  missile copy reads the context's `owner`. (fn:SKILLS_FindUnitSkill@0x00643810, fn:SKILLS_GetSkillLevel@0x006442A0, fn:sub_0064B760_MissCalcSkill@0x0064B760)
- [I] `stat(id, k)`: no unit, `id < 0` or `id ≥` the itemstatcost count → 0; `id = 19` → the player's attack rating
  (fatal for a non-player); `k = 1` → `STATS_GetUnitBaseStat`, `k = 2` → `sub_00625500_UnitGetStat`, else
  `STATS_GetUnitStat`. The item copy has the same body. (fn:STATS_GetUnitBaseStat@0x006253B0, fn:sub_00625500_UnitGetStat@0x00625500, fn:STATS_GetUnitStat@0x00625480, fn:sub_00627BB0_ItemCalcStat@0x00627BB0)
- [I] The missile `rand`'s seed `ctx + 0x20` (stepped as shown by the emulation above) is a stack address inside
  `MISS_EvalCalc`'s frame holding its offset and missile-id arguments, so the draw is a function of those two values
  and advances no game seed. No stock missile formula calls `rand`. (fn:sub_00627B70_ItemCalcRand@0x00627B70, fn:sub_0064B720_MissCalcRand@0x0064B720, 0x0064B742)

### G. Variables

**G1. Skills and skilldesc: `SkillVar(code, unit, skill, lvl)`** is `SKILLS_CalcVar`; `code` is the
[SkillCalc](../../tables/SkillCalc.md) row. A `skill` out of range gives 0. `rec` is the skill's record and `ParN`
its `ParamN`.

```
SkillVar(code, unit, skill, lvl) → i32:                                  [C] (fn:SKILLS_CalcVar@0x00646460, run:2026-10-16-calc)
  ln12 ln34 ln56 ln78  (0 2 4 6):  lvl < 1 ? 0 : ParA + (lvl − 1) × ParB          ; (A, B) = (1, 2) (3, 4) (5, 6) (7, 8)
  dm12 dm34 dm56       (1 3 5):    lvl < 1 ? 0 : DimReturns(lvl, ParA, ParB)
  par1 … par8          (8–15):     ParN
  lvl                  (16):       lvl
  toht                 (20):       lvl < 1 → 0
                                   rec.ToHitCalc = −1 → rec.ToHit + (lvl − 1) × rec.LevToHit
                                   else → Formula(rec.ToHitCalc)
  usmc                 (42):       ((rec.lvlmana × (lvl − 1) + rec.mana) << rec.manashift);  0 when lvl < 1
  mps                  (22):       (((rec.lvlmana × (lvl − 1) + rec.mana) × 25 ÷ 2) << rec.manashift) >> 8;  0 when lvl < 1
  clc1 clc4            (55 58):    Formula(rec.calc1), Formula(rec.calc4)
  len                  (54):       Formula(rec.auralencalc)

Formula(offset) = EvalSkill(skillscode, unit, offset, skill, lvl)     ; one nested evaluation, same context

DimReturns(lvl, a, b) → i32:                                             [C] (fn:SKILLS_DimReturns@0x00645B20, run:2026-10-16-calc)
  q: i32 ← lvl × 110 ÷ (lvl + 6)                                         ; truncation toward zero
  r: i32 ← q × (b − a) ÷ 100 + a                                         ; truncation toward zero
  return min(r, b)                                                       [C] (fn:SKILLS_DimReturns@0x00645B20, run:2026-10-16-calc-emu) ; the cap
```

- [C] Those codes were computed from the skills record at the context's (skill, level) and matched 38 076 logged
  row-only reads; the formula-valued ones (`clc1 clc4 len`, `toht` with a formula) were each exactly one nested
  evaluation in the same context, 682 reads. `mana` is `s16` at `+0x18A`, `lvlmana` `s16` at `+0x18C`, `manashift`
  the byte at `+0x188`. (fn:SKILLS_CalcVar@0x00646460, run:2026-10-16-calc, [data/0005 § 7.1](../../findings/data/0005-calc.md#71-skillcalc-codes-skills_calcvarunit-code-skill-lvl-skill-out-of-range--0))
- [C] The `min(r, b)` cap of `DimReturns` was never reached in the harness run (every logged `dm` read had `r ≤ b`,
  levels 1–20); under emulation the diminishing-returns codes of `MISS_CalcVar` went through `SKILLS_DimReturns` and
  hit the cap 373 times, 0 mismatches. (fn:SKILLS_DimReturns@0x00645B20, fn:MISS_CalcVar@0x0064B340, run:2026-10-16-calc-emu)

- [I] **What `ToHitCalc` feeds.** `SKILLS_GetToHit` (the `toht` value: `ToHit + (lvl − 1) × LevToHit`, or the
  `ToHitCalc` formula) is the attack-rating **percent** a player skill's melee hit passes to the hit test as `arPct`;
  it is added to the item and mastery percents and applied as `AR + MulDiv(AR, pct, 100)`
  ([combat/to-hit § A](../combat/to-hit.md#a-the-chance-to-hit-combat_tohitroll)). The normal attack passes stat 325
  instead. (fn:SKILLS_GetToHit@0x006449F0, 0x005C76B0, fn:COMBAT_ToHitRoll@0x0057D9B0)

The codes the run did not reach as variables, read from the code only:

| Codes (row) | Value | Tag |
|---|---|---|
| `dm78` (7) | `DimReturns(lvl, Par7, Par8)` with **no** `lvl < 1` test | [I] (0x0064651F) |
| `mana` (21) | `usmc >> 8` | [I] (fn:SKILLS_CalcVar@0x00646460) |
| `clc2 clc3` (56 57), `rng` (59) | `Formula(rec.calc2)`, `Formula(rec.calc3)`, `Formula(rec.aurarangecalc)` | [I] (fn:SKILLS_CalcVar@0x00646460) |
| `ast1`–`ast6` (60–65), `pst1`–`pst5` (66–70) | `Formula` of `aurastatcalc1..6`, `passivecalc1..5` | [I] (fn:SKILLS_CalcVar@0x00646460) |
| `pets` (71), `skpt` (72) | the `petmax` (`+0xC0`) and `skpoints` (`+0x170`) formula fields | [I] (fn:SKILLS_CalcVar@0x00646460) |
| `m1rn m2rn m3rn` (35–37) | description missile *k*'s `LevRange × lvl + Range` | [I] (fn:SKILLS_CalcVar@0x00646460) |
| `blvl` (41) | the unit's base points in the skill, 0 without it (unit state) | [I] (fn:SKILLS_GetSkillLevel@0x006442A0) |
| `m1el m2el m3el` (28 31 34), `edma` (51), `m2eo m2ey me3o me3y` (45–48) | elemental lengths and 256ths of the description missiles and the skill (unit state) | [I] (0x006468BE) |

- [I] The description-missile index of `m1eo`…`me3y` is `(code − 43) ÷ 3` for codes two apart, so `m2eo`/`m2ey` read
  the first description missile (as `m1eo`/`m1ey` do) and `me3o`/`me3y` the second. (0x006468BE)
- [I] The 21 unit-reading codes listed under *Inputs* read, roughly: the skill's elemental min/max/length
  (`edmn edmx edln`, `>> 8` or in 256ths: `edns edxs`, with the elemental mastery: `enma exma enms exms`), the
  description missiles' elemental min/max (`m1en`…`m3ex`, `m1eo m1ey`), the unit's level (`ulvl`, stat 12) and the
  weapon-mastery passive formulas (`math madm macr`). Their arithmetic is in [data/0005 § 7.1](../../findings/data/0005-calc.md#71-skillcalc-codes-skills_calcvarunit-code-skill-lvl-skill-out-of-range--0)
  and belongs to the skills subsystem. (fn:SKILLS_GetElemMin@0x00644D50, fn:SKILLS_GetMasteryCalc@0x00647E00)

**G2. Missiles: `MissVar(code, missile, owner, missileId, lvl)`** is `MISS_CalcVar`, `code` a
[MissCalc](../../tables/MissCalc.md) row.

- [I] A non-missile unit or a `missileId` out of range gives 0. `par1`–`par5` (0–4), `cpa1`–`cpa5` (5–9), `hpa1`–`hpa3`
  (10–12), `chp1`–`chp3` (13–15), `dpa1 dpa2` (16 17) read the record's `Param1..5`, `CltParam1..5`, `sHitPar1..3`,
  `cHitPar1..3`, `dParam1/2`; `lvl` (18) is `lvl`; `rang` (28) is `LevRange × lvl + Range`; `sl12 sl34 cl12 cl34 shl1
  chl1 dl12` (29 … 41, odd) are `A + (lvl − 1) × B` and `sd12 sd34 cd12 cd34 shd1 chd1 dd12` (30 … 42, even)
  `DimReturns(lvl, A, B)` over the pairs (Param1, 2), (Param3, 4), (CltParam1, 2), (CltParam3, 4), (sHitPar1, 2),
  (cHitPar1, 2), (dParam1, 2); `edmn edmx edln edns edxs damn damx dmns dmxs` (19–27) read the missile's elemental and
  physical damage (unit state). No variable was read in a missile context in the harness run.
  (fn:MISS_CalcVar@0x0064B340, [data/0005 § 7.2](../../findings/data/0005-calc.md#72-misscalc-codes-miss_calcvarmissile-owner-code-missileid-lvl))
- [C] **Codes 0–18 and 28–42, by emulation**: 5 000 calls of `MISS_CalcVar` on four random 0x1A4-byte records (and the
  code byte with garbage above it, codes 43 and 255, missile ids −1, 4, `0x7FFFFFFF`, a type-1 unit), levels −5…119
  plus wide ones, 0 mismatches, `ret 0x14` each time. Codes 19–27 call the elemental and physical damage getters and
  were not cased: they stay inferred as above. (fn:MISS_CalcVar@0x0064B340, fn:SKILLS_DimReturns@0x00645B20,
  run:2026-10-16-calc-emu, [data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu))

**G3. Items.** [I] The item variable reader returns 0 for every index, and the item compiler turns every bare
identifier into variable 0, so an item formula's only inputs are its constants and `stat`/`rand`. All 45 stock item
cells are constants. (fn:sub_00627B40_ItemCalcVar@0x00627B40, fn:sub_006314A0_ItemCalcIdent@0x006314A0)

## Outputs

One `i32` per evaluation. The caller decides what it means (a duration in frames, a percentage, a description
number); this spec does not. A blank cell (−1) yields 0 at every entry point (§ A, `[I]`, fn:SKILLS_EvalCalc@0x00646CA0).

## Worked example

All values from run:2026-10-16-calc (`workspace/logs/calc-s3-*.log`, not in git) and recomputed with
`python3 -I tools/calc.py eval` on the stock pools.

**1. A stock skill formula: Raise Skeleton `petmax`** (skills row 70, `(lvl < 4) ?lvl:(2+lvl/3)`), `skillscode`
offset 1464, evaluated by the Necromancer sessions with ctx `{unit, skill 70, lvl 3}`, 52 times, result 3.

| # | Byte(s) | Action | Stack after |
|---|---|---|---|
| 1 | `04 10` | read `lvl` (row 16) → 3 | 3 |
| 2 | `07 04` | push 4 | 3 4 |
| 3 | `0A` | 3 < 4 → 1 | 1 |
| 4 | `04 10` | read `lvl` → 3 | 1 3 |
| 5 | `07 02` | push 2 | 1 3 2 |
| 6 | `04 10` | read `lvl` → 3 | 1 3 2 3 |
| 7 | `07 03` | push 3 | 1 3 2 3 3 |
| 8 | `13` | 3 ÷ 3 = 1 | 1 3 2 1 |
| 9 | `10` | 2 + 1 | 1 3 3 |
| 10 | `16` | else 3, then 3, cond 1 → then | 3 |
| 11 | `00` | return 3 | |

- [C] The game read `lvl` three times, in the order of rows 1, 4 and 6, though the else-branch's value was dropped,
  and returned 3. (fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc)
- [C] The skill-description copy of the same text (`skilldesccode` offset 918, `desccalca2`) evaluated at level 4
  takes the else-branch: `2 + 4 ÷ 3` = 3, also logged as 3. (fn:SKILLS_EvalDescCalc@0x00646D00, run:2026-10-16-calc)

**2. A Misc `calc` cell: the potions drunk** (`ITEMS_EvalCalc`, from 0x005BEDA0).

| Potion | Cell | Text | `itemscode` offset | Bytes | Value |
|---|---|---|---|---|---|
| Stamina (`vps`) | `len` | `750` | 3 | `08 EE 02 00` | 750 |
| Stamina (`vps`) | `calc1` | `5000` | 7 | `08 88 13 00` | 5000 |
| Antidote (`yps`) | `len` | `750` | 11 | `08 EE 02 00` | 750 |
| Antidote (`yps`) | `calc1` | `50` | 15 | `07 32 00` | 50 |
| Antidote (`yps`) | `calc2` | `10` | 18 | `07 0A 00` | 10 |

- [C] Each drink evaluated these cells in this order, `len` from the call at 0x005BEDFF and `calc1`/`calc2` from the call at 0x005BEF11, with
  the item reader and table; each returned its constant (`08` reads `EE 02` as 750). The thawing potion (`wms`) has the
  same three texts at its own offsets. Note the pool order: `len` is stored before `calc1` because `len` precedes
  `calc1` in `misc.txt`, although its field (`+0xB0`) comes after `calc1`'s (`+0xA4`). (fn:ITEMS_EvalCalc@0x00627C20, run:2026-10-16-calc)

**3. A unit-state input: Zeal's description** (`skilldesccode` offset 1990,
`((lvl < 5) ? 0 : ((lvl-4) * par4) )+skill('Sacrifice'.blvl)*par8`), Paladin with Sacrifice at base level 2.

```
04 10 07 05 0A | 07 00 | 04 10 07 04 11 04 0B 12 | 16 | 07 60 07 29 01 03 | 04 0F 12 | 10 | 00
lvl 5 <          0       lvl 4 − par4 ×            ?:   96 41 skill        par8 ×      +    end
```

- [C] At level 4 the reads are `lvl` 4, `lvl` 4, `par4` 6, then `skill(96, 41)` (Sacrifice's row, `blvl`'s
  `skillcalc` row) taken from the unit → 2, then `par8` 12: `(4 < 5 ? 0 : 0·6) + 2·12` = 24. At level 5 the else-branch
  gives `(5 − 4)·6 + 24` = 30. Both match the log. (fn:CALC_Eval@0x006C0BC0, run:2026-10-16-calc)

## Reimplementation notes

- **Both ternary branches run.** `?:` is an operator over three values already on the stack; every read and call in
  the unused branch still happens (§ D 4a). With `rand` in a branch, the draw happens either way ([I] for `rand`, fn:sub_00643700_SkillsCalcRand@0x00643700).
- **Truncating division.** `÷` is C division (toward zero), and a zero divisor gives 0 rather than a fault (the zero test [I], 0x006C0EC6).
- **Fire Wall's `02`.** Skills `Fire Wall` `EDmgSymPerCalc` ends in `02 00`; `02` must end the evaluation with the top
  of the stack, exactly like `00`.
- **The length is the rest of the pool.** Do not copy each cell into its own buffer with its own length unless the
  cell's `00` is kept; the evaluator stops at the first terminating opcode.
- **No sharing in the pools.** Rebuilding a pool must store every non-blank cell, duplicates included, in record and
  `.txt` column order, or the offsets of every later cell shift.
- **The compile can fail** where a permissive parser would succeed (`min(-1,lvl)`, operators in an unparenthesised
  then-branch, a lone space): the game stores −1 and the formula evaluates to 0. [I] for the first two (§ C,
  0x006C18DE, fn:CALC_PushOperator@0x006C18A0); [C] for the lone space (§ C, 0x006C1992).
- **Variable index widths.** `04` reads its index unsigned (0–255), so a hand-made `04 80` is variable 128, not
  −128; the compiler itself writes indices above 127 as `05`.
- **`dm78`** lacks the `lvl < 1` guard of the other `dm` codes; at `lvl` 0 it gives `DimReturns(0, Par7, Par8)` =
  `min(Par7, Par8)` rather than 0. [I] (0x0064651F)

## Evidence

- [data/0005](../../findings/data/0005-calc.md): the compiler (§ 2–4), the evaluator (§ 5), contexts and functions
  (§ 6), variables (§ 7), the recompile of every stock cell (§ 8), the compile order (§ 9), the run (§ 10), the
  emulation of the function tables, `MISS_CalcVar` and the missile context (§ 11, run:2026-10-16-calc-emu, ADR-0015).
- [experiments § run:2026-10-16-calc](../../findings/data/experiments.md#run2026-10-16-calc): 14 sessions, 44 529
  evaluations, 0 mismatches, 1 188 cells, all 14 stock opcodes executed.
- [formats/calc.md](../../formats/calc.md): the four pools, cell ↔ bytes pairing, opcode bytes seen.
- [formats/excel-bin.md § Calc columns](../../formats/excel-bin.md#calc-columns-formulas): the s32 offset fields.
- Tables: [SkillCalc](../../tables/SkillCalc.md), [MissCalc](../../tables/MissCalc.md), [Skills](../../tables/Skills.md),
  [Misc](../../tables/Misc.md).
- Upstream: [data/excel](excel.md) (loading, `.txt` compile order), [rng](../rng/README.md) (`RNG_RangeB`, for `rand`).

## Open questions

- ~~`max` and `rand` were not reached, nor the missile variable reader and the missile context layout.~~ Confirmed by
  emulation (§ F, § E, § G2; run:2026-10-16-calc-emu), `MISS_CalcVar` codes 19–27 excepted.
- [L] A monster actually casting `BearSmite` or `Imp Inferno`: which unit's seed `rand` draws on in that cast, and when,
  is game simulation that the emulation does not cover; and `MISS_CalcVar` codes 19–27 (the damage getters).
  ([data/0005 § 11](../../findings/data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu))
- [L] `ITEMS_EvalCalc`'s second argument (the used item, § E, read statically) in a live evaluation: no stock formula
  reads it, so no run can show it.
- [L] Not reached in any run: the zero divisor, the 32-bit wrap, `0B` false, `^`, the code-only opcodes, an empty-stack
  pop, a full stack, and the 30 `skillcalc` codes of § G1's table. Stock data cannot reach most of them; an edited
  `-txt` pool could.
