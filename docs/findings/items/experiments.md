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
