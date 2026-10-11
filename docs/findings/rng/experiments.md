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

## run:2026-10-11-seed-tree

- **Question:** Under `-seed N`, does the running game derive the game, act, level and DRLG-room seeds exactly as
  [0002-seed-tree](0002-seed-tree.md) says? Is the derivation reproducible, and does it change with N?
- **Setup:** wine 11.17 (new wow64), prefix `workspace/wineprefix` (plain `wineboot -i`), rootful Xwayland `:7` kept
  off-screen, GNU gdb 17.2. Game dir `workspace/runtime/game/`: pinned `game.exe` (sha256 `631066c1…`), the three
  signed DLLs, and `d2.lng` plus all MPQs from the 1.14b reference extraction. Character `seedtest` (Barbarian,
  expansion, normal, created through `tools/xdrive.py`). Harness per `.claude/skills/reverser/references/tooling.md`
  § Runtime harness: `tools/d2run.py` + `tools/gdb/seed-tree.gdb` (breakpoints at `0x0052C312`, `0x0052C2E2`,
  `0x00642F1A`, `0x00642F61`, `0x00642B67`, `0x0066B47C`) + `tools/gdb/enter-sp.steps`. Seed control: the game's own
  `-seed N` switch.
- **Procedure:**
  1. `python3 -I tools/d2run.py --seed N --gdb tools/gdb/seed-tree.gdb --steps tools/gdb/enter-sp.steps --after 10
     [--game-args "-act K"] --log workspace/logs/run-<N>-<tag>.log` for (N, K) = (12345, –) twice, (777, –),
     (12345, 2), (12345, 3), (12345, 4), (12345, 5), (34844169, 5). 34844169 was chosen because `step(init(N)).low =
     0xFFFFFF87`, so Act V level ids ≥ 121 wrap.
  2. `python3 -I tools/rng.py seedtree workspace/logs/run-*.log` predicts every GAME/ACT/LEVEL/ROOM value from N.
  3. `diff` the two N = 12345 runs.
- **Observed:**
  ```
  run-12345-a      ACT=2 GAME=1 LEVEL=40 ROOM=430      run-12345-act2  ACT=2 GAME=1 LEVEL=19 ROOM=356
  run-12345-b      ACT=2 GAME=1 LEVEL=40 ROOM=430      run-12345-act3  ACT=2 GAME=1 LEVEL=20 ROOM=480
  run-777-a        ACT=2 GAME=1 LEVEL=40 ROOM=436      run-12345-act4  ACT=2 GAME=1 LEVEL=10 ROOM=180
  run-34844169-act5 ACT=2 GAME=1 LEVEL=14 ROOM=410     run-12345-act5  ACT=2 GAME=1 LEVEL=14 ROOM=410
  seedtree: 3353/3353 match

  GAME override=1 map=00003039 seed=00003039:0000029a                              (N = 12345)
  ACT idx=0 map=00003039 base=015b2e77 seed=015b2e77:0000141d tomb94=0 tomb484=0 bit474=0
  LEVEL id=1 act=0 type=2 base=015b2e77 seed=015b2e78:0000029a
  ACT idx=1 map=00003039 base=015b2e77 seed=b7a5c418:63a93a78 tomb94=72 tomb484=71 bit474=0   (-act 2)
  ACT idx=4 map=0213ae09 base=ffffff87 seed=ffffff87:00ddc274 …                    (N = 34844169, -act 5)
  LEVEL id=134 act=4 type=3 base=ffffff87 seed=0000000d:0000029a                   (u32 wrap)
  act-seed steps between 0x00642F1A and 0x00642F61: 0 (I, 12345), 1 (I, 777), 0 (II), 119 (III), 0 (IV), 0 (V)
  ```
  The two N = 12345 runs are identical line for line, rooms included. N = 777 creates the same levels in the same order
  with different seeds. Every act is created twice per game entry, with identical values.
- **Conclusion:** promotes in [0002-seed-tree](0002-seed-tree.md) to `[C]`: the `-seed` override path of
  `GAME_InitSeeds`, the act seed and `+0x470`, the Act II tomb draws and Act III bit, the 0-based act index, the level
  seed sum with its u32 wrap, and the DRLG room seed and `+0x04`. It also showed that the act seed has
  data-dependent consumers inside `DRLG_ActCreate` (`ACTEND` ≠ `ACT` for N = 777 and in Act III), which are now recorded there.
  Active-room and unit seeds were not reached and stay `[I]`.
