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
  See [0001-rng-core](0001-rng-core.md). It says nothing about the seed tree in [0002](0002-seed-tree.md). (run:2026-10-11-rng-emu)

- **Addendum 2026-10-16: plan 0038 batch S1b (static, no new run; `tools/sweep_s1b.py` sha256 `f0df814a30306bab…`).**
  The kept `cases.txt` and `out-*.txt` re-read for the `n = 0` lines (outputs are `eax low high`):
  ```
  python3 -I tools/sweep_s1b.py rng
  S1B rng pow2_n0_cases=7 pow2_n0_stepped=7 pow2_n0_model_eq=7 range_0045C390_n0_unchanged=7
      range_0045C3E0_n0_unchanged=7 prim_insns=145 prim_calls=0 lcg_instructions=852 lcg_raw_occurrences=852
      lcg_mov_r32_imm32=852 bad=0
  ```
  `RNG_RangePow2` steps for `n = 0`, `RNG_Range`/`RangeB` do not. With the objdump read of the primitives (memory only
  through ECX and the stack) this backs [rng/0001 § Plan 0038 batch S1b](0001-rng-core.md#plan-0038-batch-s1b-2026-10-16)
  rows 4 and 7.

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
  Active-room and unit seeds were not reached and stay `[I]`. (run:2026-10-11-seed-tree)

## run:2026-10-11-seed-tree-p1

- **Question:** (plan 0003 Phase 1) At runtime, how are the active-room seeds and the server and client unit seeds
  derived? Does the clock path of `GAME_InitSeeds` match the model, and is `-seed 0` ignored? Which callers create the
  two copies of each act?
- **Setup:** as run:2026-10-11-seed-tree (same game dir, prefix, character `seedtest`, wine 11.17, gdb 17.2).
  `tools/gdb/seed-tree.gdb` extended with breakpoints at `0x006194A0` (DACT: `DUNGEON_ActCreate` entry, return
  address and args), `0x0066EE40` (RRESEED), `0x0064233A` (RACT: `DRLG_RoomActivate` before its step), `0x0064236E`
  (AROOM: after `DUNGEON_RoomCreate`), `0x00552E2F`/`0x00552E55`/`0x00552E7D` (SUNITPRE/SUNIT/SUNITENT: server unit
  seed), `0x0046606A`/`0x00466098` (CUNITPRE/CUNIT: client unit seed) and `0x005BDFFB` (POPSTEP); the GAME line now
  also logs the game pointer. New `tools/gdb/entropy.gdb`: `0x00650DF6`/`0x00650E22` (ENTIN/ENTOUT: `RNG_EntropySeed`
  inputs and result) and `0x0052C2E2` (GAMECLOCK). Checker: `tools/rng.py seedtree`, extended for the new lines.
- **Procedure:**
  1. `python3 -I tools/d2run.py --seed N --gdb tools/gdb/seed-tree.gdb --steps tools/gdb/enter-sp.steps --after 15
     --log workspace/logs/run-p1-N-X.log` for N = 12345 (twice) and N = 777.
  2. `python3 -I tools/d2run.py --seed 0 --gdb tools/gdb/entropy.gdb --steps tools/gdb/enter-sp.steps --after 10
     --log workspace/logs/run-p1-entropy-0.log`.
  3. `python3 -I tools/rng.py seedtree workspace/logs/run-*.log` (Phase 2 logs included).
  4. Compare the two N = 12345 logs with heap pointers masked out.
- **Observed:**
  ```
  run-p1-12345-a   AROOM=54 CUNIT=256 DACT=2 GAME=1 LEVEL=40 RACT=54 ROOM=430 SUNIT=36
  run-p1-12345-b   (identical to -a once pointers are masked)
  run-p1-777-a     AROOM=49 CUNIT=227 DACT=2 GAME=1 LEVEL=40 RACT=49 ROOM=436 SUNIT=42
  run-p1-entropy-0 ENTOUT=2 GAMECLOCK=1
  seedtree: 5954/5954 match   (all Phase 2 and Phase 1 logs)

  DACT ret=0053aca5 act=0 seed=00003039 arg3=0          server copy
  DACT ret=0044e142 act=0 seed=00003039 arg3=1          client copy
  RRESEED room=033d3800 r04=61c87b80 seed=61c87b80:278dbce6 type=2
  RACT    room=033d3800 r04=61c87b80 seed=64a412d0:50a5d027      k steps after init(r04), k in 50..376
  AROOM   room=033d3800 drlgseed=ba5d4a37:29f9ff9a aseed=ba5d4a37:0000029a flags=0
  SUNITPRE type=0 class=4 p=02df014c (= g 02df007c + 0xD0) pre=eef1409d:2838bb47   (5th draw of init(N))
  SUNIT    post=b7a5c418:63a93a78 useed=b7a5c418:0000029a u28=b7a5c418
  game-seed draw index per server unit: 0:5 4:6 4:8 4:10 … 2:22 2:23 1:24 …   (type:index)
  ENTIN tick=018c171f time=6acb9a61 salt=70473f3d → ENTOUT 489b76ea
  ENTIN tick=018c171f time=6acb9a61 salt=2f8224ac → ENTOUT 30805685
  GAMECLOCK override=0 map=30805685 seed=2f8224ac:1e48b08a
  ```
  Server act (flags 0): 9 active rooms per run; client act (flags 4): 45 (12345) / 40 (777). Every CUNIT room is in
  the client act. Rooms activated in both acts: 9; their active seeds differ for 6 (12345) / 8 (777). POPSTEP and
  SUNITENT never fired (only the Act I town was entered).
- **Conclusion:** promotes in [0002-seed-tree](0002-seed-tree.md) to `[C]`: the clock path of `GAME_InitSeeds` and the
  32-bit `RNG_EntropySeed`; `-seed 0` not applied; the 32-bit `config+0x21A`; the server/client act copies with
  the same seed; the activation sequence (re-seed from `+0x04`, k type-code draws, one activation draw,
  `active.seed = init(low)`); server unit seeds from game `+0xD0`; client unit seeds from client active rooms. Supports
  the restated "draw" bullet in [0001-rng-core](0001-rng-core.md). (run:2026-10-11-seed-tree-p1)
- **Addendum 2026-10-16: plan 0038 batch S1b (static, no new session; `tools/sweep_s1b.py` sha256
  `f0df814a30306bab…`).** The logs of this run and of run:2026-10-11-seed-tree-p1 (12 files, sha256 recorded in
  `workspace/logs/sweep-s1b-manifest.txt`, `d06d2aac…c9506fb`; the record gave none) re-read by room type and unit type:
  ```
  python3 -I tools/sweep_s1b.py seeds
  S1B seeds rooms_type1=876 rooms_type1_predicted=876 rooms_type2=3552 rooms_type2_predicted=3552
      server_units_type0=3 server_units_type1=27 server_units_type2=60 server_units_type4=24 client_units_type2=739 bad=0
  ```
  Conclusion: [rng/0002 § Plan 0038 batch S1b](0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16) rows 3, 11 (in part),
  15 and 16 (in part), with the objdump pins and closures of `sweep_s1b.py static`.
