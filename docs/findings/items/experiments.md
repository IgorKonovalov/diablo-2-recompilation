# Item experiments

## run:2026-10-11-tc-drops

- **Question:** Does `tools/tc.py` reproduce recorded `TC_ResolveDrops` calls bit for bit (every pick draw, every
  oracle-entry seed, the output and the final source seed), per plan 0004 Phase 2?
- **Setup:** the plan 0003 harness unchanged (wine 11.17 new wow64, prefix `workspace/wineprefix`, rootful Xwayland
  `:7`, GNU gdb 17.2, pinned `game.exe`), per ADR-0003. Character `seedtest` (Barbarian, level 1, expansion, Normal),
  single player, `-seed 12345`. Logger `tools/gdb/tc-drops.gdb` (breakpoints at `0x0055AFED` DROP, `0x0055A6D0` TCR,
  `0x0055A8EE` PARTY, `0x0055A8F9` PLAYERS, `0x0055A926` CAP, `0x0055A93B` NDIN with `$fctrl`, `0x0055A9D9` NDP,
  `0x0055AA3F` PICK, `0x0055AAC2` NEG, `0x0055AB35` SEL, `0x0055AB75` SUB, `0x00558640` QIN (only when the return
  address is `0x0055ADBF`), `0x0055ADBF` QOUT, `0x0055AEE7` CPRE, `0x0055AEEC` CPOST, `0x0055AF80` TCEND).
- **Oracle (ADR-0004):** `sub_00558640_DropRollQuality`. At each QIN the model asserts the predicted source seed, the
  item index, `ilvl` and the six ratio words; it then takes the quality and the exit seed from QOUT.
- **Method that produced the kills:** scripted input through `tools/xdrive.py` on `:7`, driven by the agent.
  `tools/gdb/tc-bloodmoor.steps` enters the game and walks north-east out of the Rogue Encampment into the Blood Moor;
  the attacks were then issued as single `xdrive click` commands at monster positions read from screenshots (no human
  input, no fixed script for the combat itself). The kills are not replayable click for click, which the check does
  not need: every call carries its own inputs.
- **Procedure:**
  ```
  python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/tc-drops.gdb --steps tools/gdb/tc-bloodmoor.steps \
      --after 1500 --log workspace/logs/tc-run2.log
  # ... xdrive clicks on monsters, then wineserver -k
  python3 -I tools/tc.py replay workspace/logs/tc-run2.log -v
  ```
  Log sha256 `4269d84cc4d5956fa5b91ddeed6619ae147ce69c4ab4c15f1b5c1472a403ee43` (workspace, not in git). An earlier
  attempt (`tc-run1.log`) stopped at its first TCR: the logger dereferenced a 32-bit game pointer as a 64-bit gdb
  pointer (`**(unsigned**)`), which is fixed in the committed script.
- **Observed:**
  ```
  ok   #0 tc=430 'Act 1 H2H A' src=1/5  diff=0 base=430 lvl=0 picks=3 q=1 count=1 nodrop=[(100, 60, 1, 100)]
  ok   #1 tc=430 'Act 1 H2H A' src=1/19 diff=0 base=430 lvl=0 picks=1 q=0 count=0 nodrop=[(100, 60, 1, 100)]
  ok   #2 tc=430 'Act 1 H2H A' src=1/19 diff=0 base=430 lvl=0 picks=1 q=0 count=0 nodrop=[(100, 60, 1, 100)]
  ok   #3 tc=430 'Act 1 H2H A' src=1/19 diff=0 base=430 lvl=0 picks=1 q=0 count=0 nodrop=[(100, 60, 1, 100)]
  4 calls, 4 reproduced, 0 failed
  ```
  Call #0 (monster class 5) went `Act 1 H2H A` → `Act 1 Equip A` → `weap3` and dropped item 25 with the
  oracle's quality 1; the other three (class 19, fallen) rolled NoDrop. All four: six pick draws on the source seed
  matched `RNG_Range(total + NoDrop)`, one sub-TC push and one auto `weapN` selection matched, the single oracle-entry
  seed matched, CPRE seed == CPOST seed, and the count and final seed matched. Every TCR logged `g6a=3`, `pover=0`;
  `n` was 1 in every call, so the NoDrop x87 path (NDIN, `$fctrl`) never ran.
- **Conclusion:** the replay pipeline works end to end, but 4 calls is far below the plan's 50 and covers none of the
  required cases (negative Picks, ratio inheritance, unique/superunique, NoDrop at two player counts, level upgrade,
  and the three Phase 1b cases). Nothing in items/0001 is promoted on this run. It is consistent with §5 (pick draw),
  §5.1 (expansion selection), §7 (sub-TC push), §9 (one `weap3` entry) and the claim that item creation does not step
  the source seed, each on one to six observations. It answers one open question by observation: `game+0x6A` is 3 in
  this single-player game.

### Second session (same run id): strong save, `/players 8`

- **Setup changes:** `seedtest` was first written as a full save (the harness copy had been a 335-byte stub because
  `wineserver -k` never lets the game save; entered once without gdb and left through *Save and Exit Game*). Then
  `tools/d2s.py setstat` raised stat 0 `strength`, 2 `dexterity` and 3 `vitality` to 1000 and 6/7 `hitpoints`/`maxhp`
  to `8000 << 8`, re-checksummed (`stored == computed`). No weapon change: `d2s.py` has no item writer. The original
  save was backed up before and restored after (sha256 `cabccb01…` again). `tools/gdb/tc-bloodmoor.steps` now types
  `/players 8` in town before leaving, and toggles running.
- **Kill method:** `tools/gdb/tc-bloodmoor.steps`, then an agent-written hover-scan loop (scratch script, not
  committed): it moves the pointer over a grid on `:7`, reads the hover name bar of the game (dark-red pixels at the
  top centre) with `XGetImage`, holds the left button on a hit for 1.2 s, and otherwise holds a walk click. No human
  input. A first attempt (`tc-run3.log`) ended with the game gone before any kill, cause not found.
- **Procedure:**
  ```
  python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/tc-drops.gdb --steps tools/gdb/tc-bloodmoor.steps \
      --after 2400 --log workspace/logs/tc-run4.log
  # hover-scan loop for ~10 min, then wineserver -k
  python3 -I tools/tc.py replay workspace/logs/tc-run4.log -v
  ```
  Log sha256 `694069b8bc16c820bd6b7216df862ec4f7299f5aa5c4aebb8b1e11aaf0c47232` (workspace, not in git).
- **Observed:** `10 calls, 10 reproduced, 0 failed`. Every TCR logged `pover=8`; PLAYERS 8, CAP 8, party 1, so
  `n = 1 + (8 − 1) / 2 = 4`. The x87 path ran on every positive pick: `NDIN n=4 nd=100 total=60 fctrl=027f` (9 calls,
  `Act 1 H2H A`, NoDrop' 10) and `NDIN n=4 nd=125 total=38 fctrl=027f` (1 call, `Quill 1`, NoDrop' 20); the model at
  53-bit precision gives both. TCs seen: `Act 1 H2H A` (9), `Quill 1` (1); all Normal, no champion, unique or
  superunique died, no Nightmare save (the header `difficulty`/`progression` fields are layout `[C]`, meaning `[L]` in
  [d2s.md](../../formats/d2s.md), so no save was edited for it).
- **Conclusion (both sessions):** 14 resolver calls recorded, 14 reproduced. Covered: NoDrop at two player counts
  (n = 1 and n = 4, with NoDrop' matching the x87 model), the x87 control word (`0x027F`: 53-bit precision, round to
  nearest, in all 10 NDIN lines), `weapN` (`weap3`), one recursive chain (`Act 1 H2H A` → `Act 1 Equip A` → `weap3`;
  all ratio words 0, so ratio inheritance is not exercised). Not covered: the 50-call bar, a champion (negative
  Picks), ratio inheritance with non-zero ratios, unique/superunique (Bishibosh not reached), a level upgrade, base TC
  above mlvl, `noRatio` in NM/Hell (not reached), and the party case (one client only; backlog entry filed). No tag
  promoted: the counts are far below the plan's bar.
