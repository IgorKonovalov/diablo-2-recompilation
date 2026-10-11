# 0001 — RNG core: seed state, step, range reduction, initialisers

> **Subsystem:** rng
> **Question:** What is the game's random number generator in 1.14d: its state, its step, how it reduces to a range, and how a seed is initialised?
> **Date:** 2026-10-11   **Plan:** 0001, 0003   **Status:** answered

## Answer (summary)

- [C] The RNG state is two little-endian u32 words, `low` at `+0x0` and `high` at `+0x4`. One step computes
  the unsigned 64-bit value `low * 0x6AC690C5 + high` and stores bits 0–31 to `low` and bits 32–63 to `high`.
  (fn:RNG_Step@0x0045C370, run:2026-10-11-rng-emu)
- [C] **Range draw `RNG_Range(seed, n)`:** if `(int32)n < 1` it returns 0 **and does not step the seed**. Otherwise it
  steps once and returns `low % n` (unsigned 32-bit), where `low` is the new low word. For power-of-two `n` the
  code computes `low & (n − 1)` instead, which is the same value. There are two identical copies.
  (fn:RNG_Range@0x0045C390, fn:RNG_RangeB@0x0045C3E0, run:2026-10-11-rng-emu)
- [C] `RNG_RangePow2(seed, n)` has no guard: it always steps and returns `low & (n − 1)`. Callers pass a power of
  two. (fn:RNG_RangePow2@0x00472210, run:2026-10-11-rng-emu)
- [C] **Initialisers:** `RNG_SeedInit(seed, v)` sets `low = v, high = 666 (0x29A)`, and `RNG_SeedInitOne(seed)` sets
  `low = 1, high = 666`. Nothing else is computed. (fn:RNG_SeedInit@0x00650E40, fn:RNG_SeedInitOne@0x00650E30,
  run:2026-10-11-rng-emu)
- [I] **The step is mostly inlined.** The multiplier immediate occurs in 841 instructions (Ghidra
  `findscalar`): 837 inside 427 functions and 4 outside any defined function. A raw byte search finds 852
  `C5 90 C6 6A` matches. All 852 are in `.text` and each one follows a `mov r32, imm32` opcode (B8–BF). The 11
  that Ghidra did not count were in code it had not disassembled: nine DRLG level-link callbacks reached only through
  data tables at `0x006F07xx`–`0x006F0Exx` (`sub_…_LinkPick`, see [0002-seed-tree](0002-seed-tree.md)). With those
  functions defined, `tools/ghidra.sh instrat` reports all 852 as instructions inside functions. So all 852 are draw sites. Only the functions above are out-of-line helpers
  (`RNG_Range` has 154 callers, `RNG_RangeB` 114, `RNG_RangePow2` 8, `RNG_Step` 1). Every inlined copy read so far
  (in `DRLG_ActCreate`, `DRLG_RoomCreate`, `DRLG_RoomActivate`, `sub_00465FD0_UnitInit`, `GAME_InitSeeds`) is the
  same `mul`/`add`/`adc` sequence. **An inlined range draw may drop the `n < 1` guard** when `n` is a constant
  (e.g. `% 7` in `DRLG_ActCreate`, compiled as a multiply by `0x24924925` plus a correction, which is an exact
  unsigned `% 7`). Specs must state per call site which form is used.
- [C] **A draw is one step of a specific seed object, and every consumer of that object interleaves in call
  order.** Many seed objects exist (game `+0xD0`, act, level, DRLG room, active room, unit…), and several consumers
  share one. For example, every server unit constructor, the object-region and monster-region code and the
  per-room population pass all step the game seed `+0xD0`, so a reimplementation must reproduce the order of
  those calls, not just each formula. In three runs all 114 server unit seed draws use that one game seed pointer, at
  draw indices 5, 6, 8, 10… from `init(N)`, with other consumers' draws in the gaps. (fn:sub_00552DF0_UnitSeedInit@0x00552DF0,
  fn:sub_0054EC90_RoomPopulate@0x0054EC90, run:2026-10-11-seed-tree-p1, see [0002-seed-tree](0002-seed-tree.md))

## Leads used

- Hypothesis from our own lead notes (`.claude/skills/reverser/references/d2-landmarks.md`, no external source,
  nothing to register): "64-bit seed, `low * 0x6AC690C5 + high`, range helper `low % n`". **Held** for 1.14d. It
  had no 666 and no `n < 1` rule, which we found in the code.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0045C370` | `RNG_Step` | `__fastcall(seed)`: one step, no return value | C |
| `0x0045C390` | `RNG_Range` | `__fastcall(seed, n)`: guarded range draw | C |
| `0x0045C3E0` | `RNG_RangeB` | byte-for-byte different compile of the same function | C |
| `0x00472210` | `RNG_RangePow2` | `__fastcall(seed, n)`: unguarded `low & (n−1)` | C |
| `0x00472240` | `RNG_RangePow2Plus` | `(seed /*ECX*/, base /*EDX*/, n /*stack*/)`: step, `(low & (n−1)) + base`; unreferenced (below) | I |
| `0x00650E30` | `RNG_SeedInitOne` | `low = 1, high = 666` | C |
| `0x00650E40` | `RNG_SeedInit` | `low = v, high = 666` | C |

All take the seed pointer in ECX. `RNG_Range` and `RNG_RangePow2` take `n` in EDX.

## Walkthrough

```asm
; fn:RNG_Range@0x0045C390 (our binary; comments ours)
push esi
mov  esi, edx            ; n
test esi, esi
jg   draw                ; signed: n <= 0 -> return 0, seed untouched
xor  eax, eax
pop  esi
ret
draw:
mov  eax, [ecx]          ; low
push ebx
push edi
mov  edx, 0x6AC690C5
lea  edi, [esi-1]
mul  edx                 ; edx:eax = low * 0x6AC690C5   (unsigned 32x32 -> 64)
xor  ebx, ebx
test esi, edi            ; n & (n-1)
je   pow2
mov  edi, [ecx+4]        ; high
add  eax, edi
adc  edx, ebx            ; + high, with carry
mov  [ecx+4], edx        ; new high
mov  [ecx], eax          ; new low
xor  edx, edx
div  esi                 ; unsigned: new_low % n
...
mov  eax, edx
ret
pow2:                    ; same step, then eax = new_low & (n-1)
```

Pseudocode for the spec-writer:

```
struct Seed { u32 low; u32 high; }              // 8 bytes

step(s):          t = u64(s.low) * 0x6AC690C5 + u64(s.high); s.low = u32(t); s.high = u32(t >> 32)
range(s, n:i32):  if n < 1: return 0           // no draw consumed
                  step(s); return s.low % u32(n)
pow2(s, n:u32):   step(s); return s.low & (n - 1)
init(s, v:u32):   s.low = v; s.high = 666
init_one(s):      s.low = 1; s.high = 666
```

## Data touched

None. No table is read.

## Dead ends

- [I] `0x005BDFF0` (`sub_005BDFF0_ARoomSeedStep`) is not a primitive. It steps the **active room's** seed at `+0x6C`
  (pointer `room + 0x6C`, or a null pointer if `room` is null) and returns the global at `0x007415F0`. Its only
  caller is `sub_0054EC90_RoomPopulate` (`0x0054EEE6`), which passes its `EDX` argument as `ECX`. That argument is
  a `Dungeon.cpp` active room: `sub_0052D160_NewRoomsUpdate` walks each act's room list (`dungeonAct+0x10`, next
  `+0x7C`, the list `DUNGEON_RoomCreate` links into) and calls `0x0054EC90(game /*ECX*/, room /*EDX*/)` for each
  room whose `+0x34` bit 0 is clear, then sets that bit. (0x0054EEE4, 0x0052D1E9, fn:DUNGEON_RoomCreate@0x00619890,
  see [0002-seed-tree](0002-seed-tree.md#active-room))
- [I] `0x00472240` (`RNG_RangePow2Plus`) is unreferenced. A byte search of the whole file finds no absolute pointer to
  `0x00472240`, so no function table, vtable or relocated data holds it. A scan of every `E8`/`E9` rel32 at every `.text`
  offset (disassembled or not) finds no call or jump to it, and Ghidra lists no xref. It follows `RNG_RangePow2`
  after `int3` padding. It is dead code in this build, and specs can ignore it. Only a computed address could still
  reach it, and we saw no sign of one.

## Open questions

- Which of the 427 inlining functions draw with or without the `n < 1` guard is answered per subsystem, as
  each spec reads its own call sites.
