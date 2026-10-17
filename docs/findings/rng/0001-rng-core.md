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
  unsigned `% 7`). Specs must state per call site which form is used. (fn:RNG_Range@0x0045C390,
  fn:DRLG_ActCreate@0x00642DA0, fn:DRLG_RoomCreate@0x0066B3E0)
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

## Plan 0038 batch S1b (2026-10-16)

Static batch S1b of [plan 0038](../../plans/0038-inferred-claims-sweep.md), rows 2, 4 and 7 of
[inventory rng-README](../../plans/0038-inventory/rng-README.md). No session was played. The check is
`python3 -I tools/sweep_s1b.py rng`: GNU objdump's linear decoding of `.text` (through `tools/sweep_s4b.py`), the raw
byte scan, and the kept emulator outputs of run:2026-10-11-rng-emu. Where a statement above is tagged inferred and this
section raises it, the tag and the second source given here are the current ones.

- **Row 2** (spec L34 and L38: 852 multiplier immediates, all inside functions, so all draw sites) **raised in part,
  2 statements.** [C] objdump decodes 852 instructions with the operand `0x6AC690C5`, every one `mov r32, imm32`, at
  the 852 raw occurrences of `C5 90 C6 6A` (each at instruction + 1), the list of `tools/gdb/lcg-sites.txt`; Ghidra's
  count after the LinkPick functions were defined is the same 852. Inside functions: an objdump walk from every direct
  call target (9 151 when `rng` runs alone), every pointer to an instruction in `.rdata`/`.data` and every code immediate that names one
  reaches 836 of them, and 10 more lie in bodies that start after `int3` padding with `push ebp` and are walked from that
  prologue. **Remainder:** 6 sites whose body the walk does not delimit; for those, Ghidra's `instrat` alone. A new
  observation, not a correction: 14 of the sites lie in 9 bodies with no static reference at all (no rel32 call or jump,
  no absolute address): `RNG_RangePow2Plus` and 0x005528E0, 0x0055FB80, 0x0057D760, 0x005E9750, 0x005F7F10,
  0x005F8010, 0x005FD0F0, 0x00675F80 (4 sites). They are draw sites in code no static path reaches, like
  `RangePow2Plus`; a spec that counts call sites should know. (fn:RNG_RangePow2Plus@0x00472240)
- **Row 4** (spec L49, the RNG reads no table) **raised.** [C] The bodies of the seven primitives (145 instructions,
  no calls) address memory only through ECX (`[ecx]`, `[ecx+0x4]`, the seed) and the stack; no instruction has an
  absolute address operand. With the 5 000-case emulator run, which mapped no table (run:2026-10-11-rng-emu), that is
  two sources. (fn:RNG_Step@0x0045C370, fn:RNG_Range@0x0045C390, fn:RNG_RangeB@0x0045C3E0,
  fn:RNG_RangePow2@0x00472210, fn:RNG_SeedInit@0x00650E40, fn:RNG_SeedInitOne@0x00650E30)
- **Row 7** (spec L161, inlined constant-modulus draws and `RangePow2` have no guard) **raised.** [C] In the 7
  emulator cases with `n = 0`, `RNG_RangePow2` stepped the seed every time and returned `low & 0xFFFFFFFF` (equal to
  `tools/rng.py`), while `RNG_Range` and `RNG_RangeB` returned 0 with the seed unchanged (7 of 7 each;
  run:2026-10-11-rng-emu). The inlined `mod 7` of `DRLG_ActCreate` draws unguarded (rng/seeds step 3c, `[C]` by
  run:2026-10-11-seed-tree). (fn:RNG_RangePow2@0x00472210, fn:DRLG_ActCreate@0x00642DA0)

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
