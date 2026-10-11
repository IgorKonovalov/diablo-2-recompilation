# RNG experiments

## run:2026-10-11-rng-emu

- **Question:** Do `tools/rng.py`'s step, range, pow2 and init models produce exactly what the binary's own
  functions produce?
- **Setup:** Ghidra 12.1.2 p-code emulator (`EmulatorHelper`, deprecated in 12.1 but present) driven by
  `re/ghidra_scripts/EmuFastcall.java` on the pinned `game.exe` project. No wine, and nothing runs natively.
  The cases come from `python3 -I tools/rng.py cases workspace/logs/rng-emu/cases.txt 5000 1`: 5,000 lines,
  the first 112 being edge cases (seeds 0/0, 1/666, all-ones, carry-out; n = 0, 1, powers of two,
  0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0xFFFFFFFE, 0x80000001), then pseudo-random lines (Python `random`, seed 1).
  sha256 of the cases file: `2774e1f7a9546f9e0edffeb5fcbf6353c138a0862e22822eac672df890faf7ff`.
- **Procedure:** for each function, `tools/ghidra.sh emu <addr> workspace/logs/rng-emu/cases.txt > out-<addr>.txt`,
  then `python3 -I tools/rng.py check <kind> cases.txt out-<addr>.txt`. Each call starts from a fresh
  seed {low, high} at a scratch address, with ECX = &seed, EDX = n (or v), and returns to a sentinel.
- **Observed:**
  ```
  0x0045C370 step:  5000/5000 match
  0x0045C390 range: 5000/5000 match
  0x0045C3E0 range: 5000/5000 match
  0x00472210 pow2:  5000/5000 match
  0x00650E40 init:  5000/5000 match
  0x00650E30 init1: 5000/5000 match
  ```
- **Conclusion:** promotes `RNG_Step`, `RNG_Range`, `RNG_RangeB`, `RNG_RangePow2`, `RNG_SeedInit` and `RNG_SeedInitOne` to `[C]`
  (bit-exact reproduction, evidence rule 4). This includes the `n < 1` "return 0, no draw" rule for `RNG_Range`.
  See [0001-rng-core](0001-rng-core.md). It says nothing about the seed tree in [0002](0002-seed-tree.md).
