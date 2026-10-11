# 0001 — RNG core: seed state, step, range reduction, initialisers

> **Subsystem:** rng
> **Question:** What is the game's random number generator in 1.14d: its state, its step, how it reduces to a range, and how a seed is initialised?
> **Date:** 2026-10-11   **Plan:** 0001   **Status:** answered

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
  `C5 90 C6 6A` matches. The other 11 are not counted as instruction immediates by Ghidra (data, misaligned matches, or code it did not disassemble). Not checked yet. Only the functions above are out-of-line helpers
  (`RNG_Range` has 154 callers, `RNG_RangeB` 114, `RNG_RangePow2` 8, `RNG_Step` 1). Every inlined copy read so far
  (in `DRLG_ActCreate`, `DRLG_RoomCreate`, `DRLG_RoomActivate`, `sub_00465FD0_UnitInit`, `GAME_InitSeeds`) is the
  same `mul`/`add`/`adc` sequence. **An inlined range draw may drop the `n < 1` guard** when `n` is a constant
  (e.g. `% 7` in `DRLG_ActCreate`, compiled as a multiply by `0x24924925` plus a correction, which is an exact
  unsigned `% 7`). Specs must state per call site which form is used.
- [I] The "draw" a spec counts is one step of a specific seed object. Seeds are not shared: each game object
  owns its own `{low, high}` pair (see [0002-seed-tree](0002-seed-tree.md)).

## Leads used

- [L] `.claude/skills/reverser/references/d2-landmarks.md` (general knowledge, not a registered source):
  "64-bit seed, `low * 0x6AC690C5 + high`, range helper `low % n`". **Held** for 1.14d. It had no 666 and no
  `n < 1` rule, which we found in the code.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0045C370` | `RNG_Step` | `__fastcall(seed)`: one step, no return value | C |
| `0x0045C390` | `RNG_Range` | `__fastcall(seed, n)`: guarded range draw | C |
| `0x0045C3E0` | `RNG_RangeB` | byte-for-byte different compile of the same function | C |
| `0x00472210` | `RNG_RangePow2` | `__fastcall(seed, n)`: unguarded `low & (n−1)` | C |
| `0x00472240` | `RNG_RangePow2Plus` | `(seed /*ECX*/, base /*EDX*/, n /*stack*/)`: step, `(low & (n−1)) + base`; no static callers | I |
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

- `0x005BDFF0` steps a seed at `ECX + 0x6C` (with a null check) and returns a global pointer. It is a caller-side
  inline, not a primitive. Not named yet.
- `0x00472240` (`RNG_RangePow2Plus`) has no static callers. It may be reached through a function table. It is
  named, but nothing depends on it yet.

## Open questions

- Which of the 427 inlining functions draw with or without the `n < 1` guard is answered per subsystem, as
  each spec reads its own call sites.
- `0x00472240` callers (indirect?). Resolve with a data-reference search for its address.
