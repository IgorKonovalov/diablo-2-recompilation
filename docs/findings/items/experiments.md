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
- **Oracle (ADR-0004):** `ITEMS_DropRollQuality`. At each QIN the model asserts the predicted source seed, the
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
  input. A first attempt (`tc-run3.log`) ended with the game gone before any kill, cause not found. The loop is now committed as
  `python3 -I tools/d2hunt.py hunt` (2026-10-12; the later War Cry version, `--button 3` for the right skill).
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
  [d2s.md](../../formats/d2s.md), so no save was edited for it). (run:2026-10-11-tc-drops)
- **Conclusion (both sessions):** 14 resolver calls recorded, 14 reproduced. Covered: NoDrop at two player counts
  (n = 1 and n = 4, with NoDrop' matching the x87 model), the x87 control word (`0x027F`: 53-bit precision, round to
  nearest, in all 10 NDIN lines), `weapN` (`weap3`), one recursive chain (`Act 1 H2H A` → `Act 1 Equip A` → `weap3`;
  all ratio words 0, so ratio inheritance is not exercised). Not covered: the 50-call bar, a champion (negative
  Picks), ratio inheritance with non-zero ratios, unique/superunique (Bishibosh not reached), a level upgrade, base TC
  above mlvl, `noRatio` in NM/Hell (not reached), and the party case (one client only; backlog entry filed). No tag
  promoted: the counts are far below the plan's bar.

### Third session (same run id): waypoints, Cold Plains

- **Setup changes:** the strong `seedtest` copy plus all Act I Normal waypoints, written by
  `python3 -I <plan-0005 worktree>/tools/d2s.py setwp <strong.d2s> <out.d2s> normal 0,1,2,3,4,5,6,7,8` (field `0x283` =
  `ff 01 00 00 00`, checksum stored == computed). `-seed 1`, `tools/gdb/tc-wp.steps` (enter, `/players 8`, run on, the
  camp-waypoint walk from `tools/gdb/d2s-wp-open.steps` on the plan-0005 branch), then two manual clicks to the pad (the NPCs blocked the last
  step). Original save restored afterwards (sha256 `cabccb01…`).
- **Waypoint menu (for the archivist):** `workspace/logs/tc-wp-menu.png` (sha256 `d39b413f…`), taken when the menu
  first opened: one tab "I", headed *Choose your destination*, all **nine rows active** (icon box and white text;
  Rogue Encampment blue, the one in use): Rogue Encampment, Cold Plains, Stony Field, Dark Wood, Black Marsh, Outer
  Cloister, Jail Level 1, Inner Cloister, Catacombs Level 2. Clicking row 2 (*Cold Plains*, y = 173) moved the character onto
  a waypoint pad outdoors (`workspace/logs/tc-wp-coldplains-arrival.png`). The automap title read **"Cold Plains"**
  (`workspace/logs/tc-wp-automap.png`, sha256 `4c180127…`), but that screenshot was taken after five minutes of
  hunting near the pad, not right on arrival. So bits 1, 3, 4, 5 and 7 all show as active rows. Only bit 1 was travelled.
- **Kill method:** the hover-scan loop of the second session, in about 18 min of batches around the Cold Plains
  waypoint.
- **Observed:** `tools/tc.py replay workspace/logs/tc-run5.log`: `31 calls, 31 reproduced, 0 failed` (log sha256
  `dabc6ebc338d3c68d4ad8e5bd89caf0536bfa54a49815e47778d33b934450331`). TCs: `Act 1 H2H A` 25 (3 of them minions,
  `mflags=10`), `Act 1 Cast A` 4, and **`Act 1 Unique A` 1, from a unique monster** (class 58, `mflags=09`).
  `Act 1 Unique A` has `Picks = -3`: NEG rolls 0, 1, 2 with no draw. The rolls walked `Act 1 Uitem A` (ratios
  1024/800/800/800) → `Act 1 Equip A` → `weap3`, and the oracle entry showed `ratio=1024,800,800,800,0,0` (inherited
  through two zero-ratio sub-TCs), plus potions from `Act 1 Cpot A`. Five items were made. Every call ran the x87 path with
  `fctrl=027f`.
- **Conclusion (all three sessions):** **45 resolver calls recorded, 45 reproduced** (4 + 10 + 31), short of the
  plan's 50. Covered: negative Picks (from a unique, not a champion), ratio inheritance (the `parent = 0` → child
  branch only; the max of two non-zero values is not exercised), a unique-monster TC, `weapN`, NoDrop at two player
  counts with the x87 control word, and creation leaving the source seed alone. Not covered: a champion,
  Bishibosh/superunique (not found by the scan), a level upgrade, base TC above mlvl, `noRatio`, and the party case
  (backlog). Promoted in items/0001: the Picks summary, creation leaving the source seed alone, and NoDrop' for
  party 1.

### Fourth session (same run id): Black Marsh

- **Setup:** as the third session (waypoint save, `-seed 1`, `tools/gdb/tc-wp.steps`, a manual click on the camp pad),
  then waypoint row 5 (*Black Marsh*, y = 278). The automap right on arrival read **"Black Marsh"**
  (`workspace/logs/tc-run6-blackmarsh.png`, sha256 `0efbc0ae…`). Original save restored afterwards (sha256 `cabccb01…`).
- **Kill method:** the hover-scan loop, about 17 min in three batches from the Black Marsh pad.
- **Observed:** `tools/tc.py replay workspace/logs/tc-run6.log`: `52 calls, 52 reproduced, 0 failed` (log sha256
  `1c9d1a109f91b802465520c15937c7f2fc1e36ac10003283ee36fc91e7ab2379`). TCs: `Act 1 H2H B` 34, `Act 1 Cast B` 8,
  `Act 1 Miss B` 8, and `Act 1 Unique B` (`Picks = -3`) 2, from unique monsters (classes 1 and 16, `mflags=09`). There
  were 6 minion kills. All 50 positive-pick calls ran the x87 path (`n=4 nd=100 total=60 fctrl=027f`). A check of every
  TCR against `monstats.bin` found the TC column choice right in all 97 calls of the run (normal/minion →
  `TreasureClass1`, unique → `TreasureClass3`).
- **Conclusion (all four sessions):** **97 resolver calls recorded, 97 reproduced** (4 + 10 + 31 + 52), above the
  plan's 50. Covered: negative Picks (3 unique kills), ratio inheritance in the `parent = 0` branch only, unique-monster
  TCs, `weapN`, NoDrop at two player counts with the x87 control word, creation leaving the source seed alone, and the
  TC column for normal, minion and unique monsters. **Not exercised:** the maximum of two non-zero ratios. All 97 QIN
  lines show either all-zero ratios or `1024,800,800,800`, which is `Act 1 Uitem A/B` under a zero-ratio root, and the stock Act 1 chains
  seen have no such pair. **Not reached:** a champion (none found in the Cold Plains or Black Marsh scans), a
  superunique, the level upgrade, base TC above mlvl and `noRatio` (no Nightmare save: the header difficulty meaning is
  `[L]` in d2s.md). The party case is blocked (backlog).

### Fifth session (same run id): Nightmare, then a human player

- **Setup changes:** a Nightmare-capable `seedtest`, built from the strong copy with `tools/d2s.py` (`setwp` for Normal
  and Nightmare bits 0–8, `setstat` for stat 12 `level` = 70, 13 `experience` = 311105466, 1 `energy` = 1000, 8/9
  `mana`/`maxmana` = `8002 << 8`) and a scratch header edit (`progression` `0x025` = 5, `difficulty` `0x0A8` = `00 80 00`,
  header `level` `0x02B` = 70, the `if` skill byte for War Cry (skill 154, class index 28) = 20, right `mouse` skill
  `0x07C` = 154, re-checksummed; `d2s.py survey` clean). Load test: the character screen showed the title **Slayer** and
  the *Select Difficulty* box with Normal and Nightmare enabled and Hell greyed out (`workspace/logs/tc-run7-diffmenu.png`);
  choosing Nightmare entered the Rogue Encampment, and the Nightmare waypoint menu showed all nine Act I rows active
  (`workspace/logs/tc-run7-wpmenu.png`). The automap read *Difficulty: Nightmare* in every area. Melee with the
  level-2 strong save killed nothing in Nightmare (runs 7–8, discarded: 0 calls), which is why the level and War Cry were added.
  `-seed 1` throughout. The original save was restored afterwards (sha256 `cabccb01…`).
- **Kill method, runs 9–18 (agent):** a scratch hover-scan loop casting War Cry (right button) on the monster under the
  pointer when the top-centre name bar (RGB 56,8,4 / 64,20,12) shows, walking otherwise; after a death (empty life orb)
  a driver relaunched the game, found the camp waypoint by its two blue flames and travelled to Black Marsh, Stony
  Field, Dark Wood or Cold Plains. `/players 8` in town, except run 18 (`/players 1` typed; the TCR lines still logged
  `pover=8`, cause not checked). No human input. Committed 2026-10-12: the loop as `tools/d2hunt.py hunt --button 3`, the
  waypoint finder as `tools/d2hunt.py findwp` (with `wpmenu`) and the session recorder as `tools/d2hunt.py record`; the
  relaunch driver (a shell loop that swapped in a save, relaunched `d2run.py` and chained these) was committed on
  2026-10-12 as `tools/d2hunt.py relaunch` (plan 0011 Phase 1, without the save swap: characters go in through
  `tools/saves.py`; see run:2026-10-12-two-clients).
- **Kill method, run 19 (human):** the owner played the harness display while gdb logged (the plan allows this): the
  same Nightmare `seedtest` (Stony Field, Cold Plains), then a new Normal Sorceress `testsorc` (Blood Moor, Cold Plains,
  Bishibosh), and opened chests. No `/players` command (`pover=0`). The saves are in
  `workspace/runtime/saves-backup/s5-human/`.
- **Observed:** `tools/tc.py replay` on each log:

  | log | calls | reproduced | sha256 |
  |---|---|---|---|
  | `tc-run9.log` | 33 | 33 | `51fa25faf1b67c46abd8cf0fd427c4b926c82ffb61980fdd8953a2e404fcf752` |
  | `tc-run10.log` | 27 | 27 | `7f3af58999aca4c1fccd7a5333fc6db759e3bce3bc435494d7762907d493a041` |
  | `tc-run13.log` | 12 | 12 | `1aa4b12dcb312cfe8d42836b93c4d70d07ef592ef1c31b4136d4b41166cc56a5` |
  | `tc-run16.log` | 24 | 24 | `af660d24f232c2901abb7ab69cd6d9cb3cd72d101ba8eb30aa88eda6e10f80c3` |
  | `tc-run17.log` | 16 | 16 | `c0f26e57e6f078cfbb93e6c3f49d068c51f41ee11c7ec6b3ffb64690dea4a64f` |
  | `tc-run18.log` | 6 | 6 | `89f28028c1d60190c3678f5b80a58c1771d78e79b4f52a1cd685bd336befeacd` |
  | `tc-run19.log` | 113 | 113 | `dae5a7a4d646a160cf580144bdc48752b4688b6b1113edad3ef854360fed6b35` |

  Runs 11, 12, 14 and 15 logged no call (the driver missed the waypoint). **231 calls, 231 reproduced.** Of these,
  167 are Nightmare (`diff=1`) and 64 Normal; 220 have a monster source and 11 an object source (`stype=2`,
  `Act 1 Chest A`, `max=6`, 8 of them with forced quality 4 from object class 243). What they cover, beyond sessions 1–4:
  - **Level upgrade, forward walk** (`DROP base → TCR tc`, model asserted by `tc.py`), 12 calls at `lvl=40`:
    `Act 1 (N) Miss A` → `Miss B` (528 → 529, 4 minions of class 160), `Act 1 (N) H2H A` → `H2H B` (444 → 445, 4
    minions of class 53), and `Act 1 (N) Unique A` → `Unique B` (781 → 782, 4 unique monsters, `mflags=09`, classes 53
    and 160). `H2H B` stays put at `lvl=40` in 9 calls (the next TC, `H2H C`, has level 41). All 53 Normal monster
    calls logged `lvl=0` (no upgrade).
  - **Base TC above mlvl (Phase 1b case b):** 146 Nightmare calls keep a base TC whose `level` exceeds the logged mlvl:
    `Act 1 (N) H2H A`, `Cast A`, `Miss A` (level 38) at 36–37, `H2H B`, `Cast B`, `Miss B` (level 40) at 37–38, and
    **Rakanishu**'s `Act 1 (N) Super B` (level 41) at 40. The walk never moves back to a lower TC of the group.
  - **Superunique TC:** Bishibosh (Normal, class 58, `mflags=0b`, `suid=0`) → `Act 1 Super A` (896); Rakanishu
    (Nightmare, class 20, `suid=3`) → `Act 1 (N) Super B` (912) = `superuniques` row `TC(N)`. Both `Picks = -4`.
  - **Maximum of two non-zero ratios:** `Act 1 Super A` (`1024,972,800,800`) pushes `Act 1 Uitem A`
    (`1024,800,800,800`); all 12 QIN lines under it show `ratio=1024,972,800,800,0,0` (parent kept where it is larger,
    equal values kept), as the model predicts.
  - NoDrop: 117 x87 evaluations at `n=4` (`nd=100 total=60`), all `fctrl=027f`; `game+0x6A` = 3 in every call.
- **Not reached:** a **champion** (no `mflags` with `0x04` in 328 calls), the `noRatio` case (all 31 stock `noRatio`
  monsters, e.g. `necroskeleton`, `valkyrie`, `wolf`, are player summons with every `TreasureClass*` column blank, so
  no stock `noRatio` monster drops anything), Hell, and the party case (backlog).
- **Conclusion (all five sessions):** **328 resolver calls recorded, 328 reproduced** (97 + 231). Phase 2's required set is
  met except the champion branch (not reached), `noRatio` (not reachable with stock tables) and the party case (one
  client; backlog).
  The base-TC and upgrade-level check is now part of `tools/tc.py replay` (plan 0004 Phase 2 review, F3): for every
  monster source it derives the base TC from `monstats.bin` (`TreasureClass1/2/3` by `mflags`, per difficulty) or
  `superuniques.txt` (`TC`/`TC(N)`/`TC(H)` by `suid`) and the expected `DROP lvl` (0 in Normal, the source's level in
  Nightmare), and asserts both against the `DROP` line. Re-run on the eleven logs (runs 2, 4, 5, 6, 9, 10, 13, 16–19):
  328/328 calls reproduced, all 317 monster calls pass (280 normal, 28 minion, 7 unique, 2 superunique, 0 champion).

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-run{2,4,5,6,9,10,13,16,17,18,19}.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-11-tc-drops files=11 calls=328 reproduced=328 failed=0`, quality
  roll modelled at MF 0 (the record's).
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them the x87 NoDrop evaluations at `n = 4` (with
  run:2026-10-12-tc-party's at `n = 2`: 2909, five distinct `(NoDrop, T, n)`, which `p·T/(1 − p)`, 24-bit and 64-bit
  arithmetic also reproduce), the resolver steps D1–D5 and the `DROP`/`TCR` pairing. The counts and checks per statement
  are in [items/0001 § Plan 0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan
  0038 batch S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-12-two-clients

- **Question:** can the harness put two clients into one multiplayer game, in one party, with gdb logging the resolver
  on the side that runs the server game, and does `tools/tc.py replay` still reproduce the calls (plan 0011 Phase 1)?
- **What was tried first:** a second `game.exe` in the same prefix (`workspace/wineprefix`, second display `:8`). The
  game refused it with the message box "Only one copy of Diablo II may run at a time": `sub_004F5610`
  (window creation) calls `FindWindowA` with its own window class before creating its window and stops if one exists
  (`[I]`, read in Ghidra, 0x004F5610). One wine session shares one window list, so a second copy needs its own wineserver.
- **Setup (departure from ADR-0003, for the architect):** two `game.exe` processes, each under its own wine prefix and
  X display, meeting in a TCP/IP game over `127.0.0.1`:
  - host: `workspace/wineprefix`, display `:7`, gdb attached by `tools/d2run.py` (the host runs the server game);
  - joiner: `workspace/wineprefix2` (new plain `wineboot -i` prefix, wine 11.17, created for this plan), display `:8`
    (rootful Xwayland, same hidden Hyprland workspace rule), started by `tools/d2run.py --prefix workspace/wineprefix2
    --display :8` with no debugger;
  - menus: `tools/gdb/two-host.steps` (Other Multiplayer → TCP/IP Game → Host Game → OK) and `tools/gdb/two-join.steps`
    (… → Join Game → `127.0.0.1` → OK → OK); party by `tools/gdb/two-party-invite.steps` (`:7`) and
    `tools/gdb/two-party-accept.steps` (`:8`).
  - The game listens on TCP 4000 on all interfaces while hosting. Breakpoints still only print and continue.
  - `tools/d2run.py` gained `--prefix` and a driver pidfile per display (`d2run-driver.pid` for `:7`,
    `d2run-driver-8.pid` for `:8`), so the two launchers do not kill each other's driver and each driver's
    `wineserver -k` reaches only its own prefix.
- **Characters (tool-built inputs):** host `seedtest`, the strong copy of run:2026-10-11-tc-drops (Barbarian, str/dex/vit
  1000, life 8000) with every Normal waypoint set by `tools/d2s.py setwp`, swapped in with `tools/saves.py aside p0011` /
  `install` / `restore` (sha256 `cabccb01…` again afterwards). Joiner `smpsor`, the level-50 Sorceress sample with
  `tools/d2s.py setstats` (stats 0/2/3 = 1000, 6/7 = `8000 << 8`) and `setwp normal all`, placed by hand in the new
  prefix's empty saves directory (`workspace/wineprefix2/drive_c/users/$USER/Saved Games/Diablo II/`, not covered by
  `saves.py`; nothing else lives there). Both `d2s.py survey` clean. In a TCP/IP game both saves are rewritten by the
  game during play (the host's level rose from 2 to 3 between sessions although every session ended with
  `wineserver -k`).
- **Logger:** `tools/gdb/tc-party.gdb` = `tc-drops.gdb` plus `tools/gdb/tc-party.py`, a gdb Python breakpoint at
  `TC_DropByIndex` entry `0x0055AFA0` (ECX game, EDX source, `[esp+4]` killer) that prints, before the call's
  `DROP`/`TCR`: `PLR` per player unit (`game+0x1120` lists: unit id `+0x0C`, class, mode `+0x10`, subtile x/y from the
  dynamic path `unit+0x2C` `+0x02`/`+0x06`, level id via path `+0x1C` room → `+0x10` → `+0x58` level → `+0x1D0`,
  dead bit `+0xC6`), `PTY` per party (`game+0x1D2C`), and `KILL` (source and killer positions). Offsets read in this
  binary: `0x006488C0`, `0x00648900`, `0x00648A80`, `0x0061A1B0`, `0x0066BAB0`, `0x00540290`, `0x00540710`
  (`[I]`). `tools/tc.py replay` now checks every `PARTY` line against the party model of items/0001 §6 computed from
  these lines, and every `PLAYERS` line against the alive player units.
- **Procedure (session 1):**
  ```
  python3 -I tools/saves.py aside p0011; python3 -I tools/saves.py install p0011 <host>/seedtest.d2s
  python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/tc-party.gdb --steps tools/gdb/two-host.steps \
      --after 3600 --log workspace/logs/tc-party-1.log &
  python3 -I tools/d2run.py --seed 1 --steps tools/gdb/two-join.steps --after 3600 \
      --prefix workspace/wineprefix2 --display :8 --log workspace/logs/p0011/join-1.log &
  python3 -I tools/xdrive.py --display :7 --window "Diablo II" run tools/gdb/two-party-invite.steps
  python3 -I tools/xdrive.py --display :8 --window "Diablo II" run tools/gdb/two-party-accept.steps
  python3 -I tools/d2hunt.py findwp; xdrive click 200 173 (Cold Plains); python3 -I tools/d2hunt.py hunt 300 --log …
  python3 -I tools/tc.py replay workspace/logs/tc-party-1.log -v
  ```
  Log sha256 `583a4c61d522b09a13761bc5a1a69e00eb733d4385bbb4a28bf90058b1374cd6` (workspace, not in git).
- **Observed:** both characters in one game: the host's party screen listed `smpsor` (Sorceress, level 50) and, after
  invite/accept, "In your party … Rogue Encampment" (`workspace/logs/two-party-accept.png`); `PTY id=3 members=2,1`
  in every call. Every resolver call was logged by the host's gdb (the joiner has none, and the host's log holds the
  kills), which answers the plan's open question: in a TCP/IP game the server side, and so `TC_ResolveDrops`, runs in
  the host's process. **31 calls, 31 reproduced** (24 normal, 6 minion, 1 unique monster source). Every `TCR`
  logged **`g6a=2`** (single player logged 3 in every call of run:2026-10-11-tc-drops), `diff=0 exp=1 pover=0`.
  With the joiner in the Rogue Encampment and the killer in Cold Plains, the 30 `PARTY` lines are 1 and the 30
  `PLAYERS` lines 2. The positions in this log are `-1` (the first logger version read the room's level at
  `room+0x58` without the `+0x10` hop, see items/0001 §6 correction); session 2 of run:2026-10-12-tc-party has them.
- **Kill tools committed:** `tools/d2hunt.py` (`hunt`, `findwp`, `wpmenu`, `record`, and the new `relaunch`: start
  `d2run.py`, wait, waypoint, hunt until death or time, `wineserver -k` on that prefix, next attempt). `relaunch` was
  run once on 2026-10-12 (single player, strong `seedtest`, `--hunt 40`, 200 s): two attempts, logs
  `workspace/logs/p0011/relaunch-1.log` (8 calls) and `-2.log` (1 call), all reproduced, no driver left behind.
- **Conclusion:** two clients in one game, in one party, with the resolver logged and reproduced on the host. The
  method departs from ADR-0003 in four ways the architect should judge: a second process (undebugged), a second
  prefix (`workspace/wineprefix2`) and display (`:8`), a TCP/IP game (listening socket), and a hand-placed save in
  the second prefix.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-party-1.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-12-two-clients files=1 calls=31 reproduced=31 failed=0`, quality
  roll as the ADR-0004 oracle (no record gives the players' magic find).
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them the resolver steps D1–D5 and F1–F4 in a TCP/IP
  game. The counts and checks per statement are in [items/0001 § Plan 0038 batch
  S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-12-tc-party

- **Question:** plan 0011 Phase 2: does 1.14d count a partied player toward NoDrop when that player is in the killer's
  level but far away (items/0001 §6: level-id equality, no distance test; both community sources say "within two
  screens"), and do an unpartied player and a partied player in another level give `party = 1`? Also a champion kill,
  and the x87 control word in a multiplayer game.
- **Setup:** as run:2026-10-12-two-clients (same characters, logger, steps, `-seed 1`), session 2 of the harness.
  Session 3 (Nightmare champion attempt): host `LightSorc`, the owner's tool-built level-60 Sorceress
  (`workspace/runtime/owner-chars/LightSorc.d2s`, sha256 `da53fbd4…`, built by `tools/d2s.py build`; an ADR-0003
  input, installed with `saves.py aside p0011b` / `install` / `restore`). It loaded on first use (character screen,
  then *Select Difficulty* with Normal, Nightmare and Hell); Nightmare was chosen.
- **Kill method:** session 2: the agent's `d2hunt.py hunt` in Cold Plains with the joiner in town, then on Cold Plains'
  waypoint; then **the owner played the host** (Blood Moor, Cold Plains, Catacombs 1–2) while the agent moved the
  joiner (still partied) by waypoint to Catacombs Level 2 and later made it leave the party
  (`tools/gdb/two-party-leave.steps`); after the owner stopped, the agent's `hunt` again in Catacombs Level 2 for the
  last unpartied kills. Session 3: the agent's `hunt --button 3` (Chain Lightning) in the Nightmare Black Marsh, alone
  (the joiner `smpsor` could not join: it has no Nightmare access and the join screen fell back to *TCP/IP Options*);
  the character died after 9 calls.
- **Procedure:** as run:2026-10-12-two-clients with `--log workspace/logs/tc-party-2.log` (session 2) and
  `tc-party-3.log` (session 3, `two-host.steps` then a click on *Nightmare* at (400,323)); then
  `python3 -I tools/tc.py replay workspace/logs/tc-party-N.log -v`. Ended with `wineserver -k` on both prefixes.
  Log sha256: `tc-party-2.log` `70630dd5d5673e3f0e93619d4a97347148813430187fd6eada9039d2dc8dbf01`, `tc-party-3.log`
  `d729fc558fc6616ad600f1a986cb2661a3a89bb1978f0fd08774d81c262e4acd` (workspace, not in git).
- **Observed:** `tc-party-2.log` **166 calls, 166 reproduced** (105 normal, 27 minion, 7 unique monster sources; the
  rest chests), every `TCR` `g6a=2 diff=0 exp=1 pover=0`; `tc-party-3.log` **9 calls, 9 reproduced**
  (`g6a=2 diff=1`, 6 normal, 3 minion). Every `PARTY` and `PLAYERS` line of session 2 equals the party model computed
  from the logged `PLR`/`PTY` lines. By case (distances in subtiles between killer and joiner at `TC_DropByIndex`
  entry; a subtile is 1/5 of the 160×80 tile diamond of [dt1.md](../../formats/dt1.md), so screen offsets are
  `16·|dx − dy|` × `8·|dx + dy|` px against an 800×600 screen):

  | case | joiner | level ids (joiner/killer) | calls with `PARTY` | `party` | `players` | distance |
  |---|---|---|---|---|---|---|
  | (a) partied, same level | Cold Plains wp, Catacombs 2 wp | 3/3, 35/35 | 44 | **2** | 2 | 26–375; 37 calls beyond two screens, 30 at ≥ 311 (largest dx=352, dy=−129: 9.6 screens across, 3.0 down) |
  | (b) partied, other level | camp, Cold Plains, Catacombs 2 | 1/3, 3/2, 3/33, 3/34, 35/34 | 84 | 1 | 2 | 133–17202 |
  | (b) unpartied, same level | Catacombs 2 (after *Leave*) | 35/35 | 4 | 1 | 2 | 175–317 |

  The 44 party-2 monster calls ran the x87 path once each (`NDIN n=2 nd=100 total=60`); chests the host opened while
  the joiner was in the same level added 24 `NDIN n=2 nd=100 total=47` lines (6 calls of `Act 1 Chest C`, TC 387, object sources, no
  `PLR` lines, so outside the party-model check). All 68 lines have `fctrl=027f`, and every `NoDrop'` matched the
  model at 53-bit precision. Party-1 calls have `n = 1 + (2 − 1)/2 = 1` and
  no `NDIN`. **No champion** (`mflags` `0x04`) in 175 calls; session 3 reached Nightmare (`diff=1`, base TCs and
  upgrade levels checked) but no champion before the scripted Sorceress died.
- **Conclusion:** case (a) settles the party claim: a partied player alive in the killer's level counts fully
  (`party = 2`) at 311–375 subtiles, far beyond "two screens", and (b) gives `party = 1` both for an unpartied player
  in the same level and for a partied player in another level. The code read of items/0001 §6 holds; the community
  "within two screens" rule stays `contradicted`. The `party ≥ 2` NoDrop branch and its x87 evaluation reproduce,
  and the control word in the TCP/IP host is `0x027F` as in single player. Not reached: a champion kill (needs a human
  player with a character that survives Nightmare, or more scripted time).

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-party-2.log, tc-party-3.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-12-tc-party files=2 calls=175 reproduced=175 failed=0`, quality
  roll as the ADR-0004 oracle.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them F1–F4 with `party = 2` (the `n = 2`
  evaluations) and the resolver steps. The counts and checks per statement are in [items/0001 § Plan 0038 batch
  S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-12-tc-champion

- **Question:** plan 0011 Phase 2 case (c): does a champion (monster type flag `0x04`) take `monstats`
  `TreasureClass2`, ahead of the unique test, and does its drop walk the champion group in Nightmare
  (items/0001 §3, §4)?
- **Setup:** single player (no second client, so no TCP/IP listener), `workspace/wineprefix`, display `:7`, gdb on the
  game by `tools/d2run.py`, `-seed 1011` (logged `GAME override=1 seed=000003f3:0000029a`), fullscreen (the new
  `--fullscreen` option of `tools/d2run.py`). Logger `tools/gdb/tc-party.gdb` (sha256 `698ab287…0132`) with
  `tools/gdb/tc-party.py` (`3140f569…e2502`), unchanged since run:2026-10-12-tc-party; breakpoints only print and
  continue.
- **Character (tool-built input, ADR-0003):** `LightSorc`, Sorceress, level 80. Recipe
  `tools/d2s_recipes/lightsorc.json` (now level 80, sha256 `3389981e…bde1`); the installed save is the level-60 build
  `workspace/runtime/owner-chars/LightSorc60.d2s` (sha256 `da53fbd4dff11b38d8499b854b80ddf4911842b2f7cdb7efeadda96b58f15bd0`)
  passed through `tools/d2s.py setstats … 12=80 13=742730244` (level and experience), giving
  `workspace/runtime/owner-chars/LightSorc.d2s` (sha256 `0063262a558b9948a9893f4764f6919b8c99f93a8375a008a391ec66d85f4a69`).
  Installed and restored only with `tools/saves.py` (tag `p0011c`: `aside`, `install`, `restore`; `seedtest` back at
  `cabccb01…` afterwards). The save as the game left it was copied to
  `workspace/runtime/saves-backup/p0011c/LightSorc-after.d2s` (sha256
  `2af0d4813672bac9000ebcfef714413c9557d83db5239a6cce6c32a65559eba2`).
- **Kill method:** the owner played the session in Nightmare (logged level ids 35 Catacombs 2, 37 Catacombs 4, 55
  Tomb 1 A). A first launch (`tc-champion-0-aborted.log`, 0 resolver calls) was stopped before any kill to raise the
  character to level 80.
- **Procedure:**
  ```
  python3 -I tools/saves.py aside p0011c; python3 -I tools/saves.py install p0011c workspace/runtime/owner-chars/LightSorc.d2s
  python3 -I tools/d2run.py --seed 1011 --gdb tools/gdb/tc-party.gdb --after 10800 --sound --fullscreen \
      --log workspace/logs/tc-champion-1.log
  python3 -I tools/saves.py restore p0011c
  python3 -I tools/tc.py replay workspace/logs/tc-champion-1.log
  ```
  Log sha256 `934111ecc088a801b0c39f8972259929e96e96446d56da7a915e44a0cb8d3efe` (workspace, not in git).
- **Observed:** `124 calls, 124 reproduced, 0 failed; monster sources checked: normal 98, minion 17, champion 2,
  unique 4, superunique 0` (rerun by the reverser). Every `TCR` has `g6a=3 diff=1 exp=1 pover=0`; 121 monster
  sources (`stype=1`) and 3 chests (`stype=2`, `Act 1 (N) Chest C` ×2, `Act 2 (N) Chest A` ×1); every `PARTY` line is
  `party=1` and every `PLAYERS` line `players=1`, so no `NDIN` line. `mflags` values: `00` ×98, `10` ×17, `09` ×3,
  `08` ×1, `0d` ×2. The two champion calls (log lines 818 and 948, Catacombs 2), trimmed:
  ```
  DROP base=698 lvl=44 src=03bc4000
  TCR src=03bc4000 stype=1 sclass=61 seed=6bdcf6a1:1d87530c killer=04862600 tc=700 fq=0 ilvl=44 … diff=1 exp=1 pover=0 mflags=0d suid=0 …
  DROP base=698 lvl=44 src=03bc7c00
  TCR src=03bc7c00 stype=1 sclass=61 seed=3b1d869a:0b079bd6 killer=04862600 tc=700 fq=0 ilvl=44 … diff=1 exp=1 pover=0 mflags=0d suid=0 …
  ```
  Class 61 is `fallenshaman4`; its Nightmare columns are `TreasureClass1(N)` 488, `TreasureClass2(N)` 698
  (`Act 1 (N) Champ C`, group 18, level 41), `TreasureClass3(N)` 783 (`Act 1 (N) Unique C`), `TreasureClass4(N)` 0.
  The base 698 is the champion column although `0x08` is also set. A unique of the **same class** (line 568,
  `mflags=09`) logged `DROP base=783 lvl=45` → `tc=786`. The champion drops upgraded at mlvl 44 from 698 through 699
  (`Act 2 (N) Champ A`, level 42) to 700 (`Act 2 (N) Champ B`, level 44); 701 (`Act 2 (N) Champ C`, level 45) is
  above mlvl. `Picks = -2`: two `NEG` picks per call, both reproduced. Also in the log: Andariel (class 156,
  `mflags=08`, line 1452) `DROP base=834 lvl=0` (`Andarielq (N)`, her `TreasureClass4(N)`; upgrade level 0, her
  `monstats` row has `boss`). The replay accepts the quest column without checking it, because the killer's quest
  state is not logged.
- **Interventions:** none (gdb wrote no memory; the save is a tool-built input).
- **Conclusion:** case (c) met. The champion column `TreasureClass2` and the champion-before-unique test order are
  `[C]` for Nightmare, expansion, single player, class 61 ([items/0001](0001-tc-resolution.md) summary and §3), and the
  forward upgrade walk ran on the champion group (§4 observed part). Live champions carry `0x0d`. Not reached: a
  Normal or Hell champion, a classic game, a monster with both `0x02` and `0x04`. (run:2026-10-12-tc-champion)

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-champion-1.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-12-tc-champion files=1 calls=124 reproduced=124 failed=0`, quality
  roll modelled at MF 100.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them the Andariel sighting (items/tc row 28):
  `python3 -I tools/tc_sweep.py b6save` reads Nightmare quest word 6 of the installed save (sha256 `0063262a…`, now
  `workspace/runtime/owner-chars/LightSorc-noacts.d2s`) as 0, and `b6_model` then takes `TreasureClass4(N)` 834, the
  logged base. The counts and checks per statement are in [items/0001 § Plan 0038 batch
  S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-12-quality

- **Question:** plan 0010 Phase 2: does `tools/quality.py`'s model of `ITEMS_DropRollQuality`
  ([items/0002](0002-quality-roll.md)) reproduce every drop quality roll **with no oracle**, at a non-zero magic find
  high enough for the unique/set/rare diminishing returns to decide rolls, and does `tools/tc.py replay` then reproduce
  whole resolver calls with the roll modelled?
- **Inputs:** two owner-played sessions, both single player, expansion, Nightmare, same character; no new wine run by
  the reverser (this record re-runs the two logs).
  - **Session A** = the log of [run:2026-10-12-tc-champion](#run2026-10-12-tc-champion) (`-seed 1011`,
    `workspace/logs/tc-champion-1.log`, sha256 `934111ecc088a801b0c39f8972259929e96e96446d56da7a915e44a0cb8d3efe`;
    setup, procedure and post-session save there).
  - **Session B** (new, 2026-10-12): the same harness (`workspace/wineprefix`, `:7`, gdb on the game by
    `tools/d2run.py`), logger `tools/gdb/tc-party.gdb` (sha256 `698ab287…0132`, sourcing `tools/gdb/tc-drops.gdb` as
    committed before this run, sha256 `53911de0…73b7`, and `tools/gdb/tc-party.py` `3140f569…1502`; breakpoints only
    print and continue). Logged `GAME override=1 seed=000003f4:0000029a`.
    ```
    python3 -I tools/saves.py aside p0010q; python3 -I tools/saves.py install p0010q workspace/runtime/owner-chars/LightSorc.d2s
    python3 -I tools/d2run.py --seed 1012 --gdb tools/gdb/tc-party.gdb --after 10800 --sound --fullscreen \
        --log workspace/logs/tc-quality-1.log
    python3 -I tools/saves.py restore p0010q
    ```
    Log sha256 `f115a1a16275ad9247be76b440c57d8c2b93739358bdcb49936ea48d809c2121` (workspace, not in git). The save as
    the game left it: `workspace/runtime/saves-backup/p0010q/LightSorc-after.d2s`, sha256
    `e96dbe6ed452a590a14b76adb6f912b7e839e04d2c3aedf41acb1c46dc8c295a`. Restore verified. The owner played (logged
    level ids 35–91, Acts I–III); no interventions, no gear change, no mercenary (owner's instruction).
- **Character (tool-built input, ADR-0003):** `LightSorc`, recipe `tools/d2s_recipes/lightsorc.json` (sha256
  `3389981e…bde1`), installed save `workspace/runtime/owner-chars/LightSorc.d2s` (sha256
  `0063262a558b9948a9893f4764f6919b8c99f93a8375a008a391ec66d85f4a69`), installed and restored only through
  `tools/saves.py`, in both sessions.
- **Magic find is an input, not a logged value.** The logger of both sessions has no stat-80 line (the QROW/QKMF/QOMF/QMF
  lines were added to `tools/gdb/tc-drops.gdb` after this run, untested). The value comes from the save:
  `python3 -I tools/d2s.py dump workspace/merged/data/global/excel <save>` lists no character stat 80, and the ten
  equipped items (location 1) carry stat 80 on two: Harlequin Crest (`uap`, unique 248) `(80, None, [50])` and
  Wartraveler (`xtb`, unique 240) `(80, None, [50])`, so **MF = 100**. The two post-session copies
  (`p0011c/LightSorc-after.d2s` `2af0d481…eba2`, `p0010q/LightSorc-after.d2s` `e96dbe6e…2a5a`) have the same ten equipped
  items (same item seeds and property lists; only durability changed) and no charm in the inventory; merc header fields
  all 0. Killers: every `TCR` with a killer logs `ktype=0 kclass=1` (the Sorceress): 1261 of 1269 calls in B, 122 of
  124 in A; the other calls have `killer=00000000` (MF 0 by items/0002 §7; 1 such roll reaches the tests, in A, and
  its result is the same at MF 0 and 100).
- **Procedure (reverser, static):**
  ```
  python3 -I tools/quality.py check workspace/logs/tc-quality-1.log --mf 100            # and --mf 0, --mf-linear
  python3 -I tools/quality.py check workspace/logs/tc-champion-1.log --mf 100
  python3 -I tools/tc.py replay workspace/logs/tc-quality-1.log --quality model --mf 100   # no oracle
  python3 -I tools/tc.py replay workspace/logs/tc-champion-1.log --quality model --mf 100
  python3 -I tools/tc.py replay workspace/logs/tc-runN.log --quality model                 # N = 2 4 5 6 9 10 13 16 17 18 19
  ```
- **Observed, rolls (`tools/quality.py check`, code and exit seed asserted per QIN/QOUT pair, no resync):**

  | Log | MF input | Pairs | Reproduced | Failed |
  |---|---|---|---|---|
  | B `tc-quality-1.log` | 100 | 782 | **782** | 0 |
  | B | 0 | 782 | 751 | 31 |
  | B | 100, `--mf-linear` | 782 | 751 | 31 |
  | A `tc-champion-1.log` | 100 | 65 | **65** | 0 |
  | A | 0 | 65 | 63 | 2 |
  | A | 100, `--mf-linear` | 65 | 62 | 3 |

  B at MF 100: `codes 1:2 2:687 3:13 4:53 5:9 6:14 7:4; draws 0:617 1:4 2:18 3:55 4:3 5:83 6:2; itemratio rows 2:107
  3:36 4:18 5:4 None:617; 29 QOUT without QIN (forced quality) skipped`. The QOUT codes of the log are 1 ×2, 2 ×687,
  3 ×13, 4 ×82, 5 ×9, 6 ×14, 7 ×4 (the 82 are 53 rolled and 29 forced). Exits (`-v`): `Normal` type 617 (no draw, no
  row), always-`Magic` type 10 (`ring` 5, `scha` 2, `lcha`, `amul`, `jewl`), unique won on a draw 4, set won on a draw
  9, rare 14 (8 on a draw, 6 with no draw), magic 43 (3 on a draw, 40 with no draw at ratio 1024), superior 13 (all on
  a draw), normal 70 with no draw, low 2 (`normal:lose-draw`, QIN#215 item 316 at `ilvl` 1 from a chest, QIN#371 item 97 at `ilvl` 47). Three charm rolls skip the rare
  test (type `Rare` = 0). A at MF 100: `codes 1:2 2:55 4:5 5:1 6:1 7:1`, rows 2:13 3:2 4:1 5:1.
- **MF scan:** the same check with every MF from −150 to 400 as the input: **session A and session B each reproduce
  only at MF = 100**; on the old logs, `tc-run6.log` and `tc-run19.log` reproduce only at MF = 0 (the others, with fewer
  rolls, are consistent with 0 among other values). Scratch scan, not kept.
- **Linear vs diminishing (`--mf-linear`, F = MF + 100 for unique/set/rare, as for magic):** 31 rolls of B and 3 of A
  come out wrong. For each, the first test whose outcome differs between the two models (scratch comparison of the two
  traces): B unique 8 (linear wins 4 that the game lost, loses 4 the game won), set 11 (3 / 8), rare 12 (8 / 4); A set
  2, unique 1. Examples (`c` the final chance, `x` the draw, `RNG_RangeB(c)`):
  - B QIN#53, item 396, ilvl 46, ratio `0,0,0,0,0,0`: game **unique** (`c` 30091, `x` 1); linear `c` 25728, `x` 776,
    loses every test and ends low (1).
  - B QIN#216, item 48, ilvl 49, ratio 0: game normal (unique `c` 27022, `x` 11932 lost); linear unique `c` 23104,
    `x` 12, a unique the game did not make.
  - B QIN#286, item 143, ilvl 46: game superior; linear wins rare (`c` 6400, `x` 106; the game's `c` is 6918, `x` 3848).
  - A QIN#38, item 520, ilvl 49, ratio `1024,1024,995,995,0,0`: game unique (`c` 747, `x` 79); linear `c` 638, `x` 165,
    then wins set.
  The full list prints with `tools/quality.py check … --mf 100 --mf-linear` (each FAIL line carries both traces).
- **Sensitivity (scratch variants of the model, not kept), over B and A:** one `k` of 250 for all three tests: 25 + 2
  failures; unique/set `k` swapped: 19 + 1; set/rare swapped: 25 + 2; magic without MF: 3 + 0; magic diminished with
  `k` 600: 10 + 1; diminishing from MF 1 (no linear branch): 0 + 0 (not discriminated: MF 100 is above the branch).
  Over all 1113 rolls (266 + 65 + 782): `itemratio` uber key forced to 0: 7 failures, forced to 1: 13; class-specific
  key forced to 0: 10. No roll reached a `*Min` clamp (the pre-clamp chance stayed above `UniqueMin` 6400, `RareMin`
  3200, `SetMin` 5600, `MagicMin` 192 in every test). *Corrected 2026-10-14:* the names `SetMin` and `RareMin` were
  swapped here; the values are the table's (`RareMin` `+0x14`, `SetMin` `+0x20`).
- **Observed, whole calls with no oracle (`tools/tc.py replay --quality model`):** B at MF 100 `1269 calls, 1269
  reproduced, 0 failed; monster sources checked: normal 995, minion 156, champion 48, unique 32, superunique 6`; A at
  MF 100 `124 calls, 124 reproduced, 0 failed`; with the oracle (default) both are also 1269/1269 and 124/124. The eleven
  logs of [run:2026-10-11-tc-drops](#run2026-10-11-tc-drops) at MF 0, no oracle: 4 + 10 + 31 + 52 + 33 + 27 + 12 + 24 +
  16 + 6 + 113 = **328 calls, 328 reproduced** (266 rolls). B at MF 0 or linear MF 100: 1245/1269 (24 calls fail).
- **Killers' MF in run:2026-10-11-tc-drops (Phase 2 precondition):** 0. Saves: `seedtest-strong/seedtest.d2s`
  (`8f93935d…`; runs 4–18 used it or copies edited by `setstat`/`setwp`/header bytes, which write no item) equips `hax` and `buc`, normal quality, no stat 80; `s5-human/seedtest-played.d2s`
  (`9179ef03…`, after run 19, the Nightmare `seedtest`) equips `chn` (rare), `vgl` (magic), `hax`, `buc`, none with stat
  80; `s5-human/testsorc.d2s` (`70627803…`) equips `lgl` (magic) and `sst`, no stat 80; no character stat 80 and no
  mercenary in any of them. The original `seedtest` (`cabccb01…`, run 2) is a 335-byte stub `d2s.py` does not parse
  (the game gives a new character its starting kit, which has no magic find). One roll of run 19 has a monster killer
  (`navi`, class 266); its owner/stat 80 is unknown but the roll is the same at MF 0. Supporting this, the MF scan above.
- **Conclusion:** promotes in [items/0002](0002-quality-roll.md) the chance formula, the test order, the magic-find
  diminishing returns (MF > 10) and the linear magic term, the four `Version` 1 `itemratio` rows, the codes 1–7 and
  the superior/low split, scoped to Nightmare, expansion, single player, a player killer, MF 0 and 100; and in
  [items/0001](0001-tc-resolution.md) the quality hand-off arguments (item, `ilvl`, the four ratio words, the killer)
  and the returned code. Not exercised: MF 1–10 (the linear branch), MF < 0, the `*Min` clamp, a minion/summon or
  hireling killer (owner MF), classic games, Normal and Hell difficulty, the unique-flag and quest early returns.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-quality-1.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-12-quality files=1 calls=1269 reproduced=1269 failed=0`, quality
  roll modelled at MF 100.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them 48 Nightmare champion calls, and one call that
  the `MAX_DROP` stop ends with picks left (the no-stop model fails it). The counts and checks per statement are in
  [items/0001 § Plan 0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038
  batch S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-13-quality

- **Question:** plan 0010 Phase 2, the remaining cases. Does `tools/quality.py`'s model of
  `ITEMS_DropRollQuality` ([items/0002](0002-quality-roll.md)) still reproduce every roll with no oracle
  (1) at a magic find in 1–10, the linear branch and a second non-zero value, (2) for a kill by a summon, where the
  owner's MF should count, and (3) in a **classic** game, where src:pd-item-generation says the `Version` 0
  `itemratio` rows are used and the code reading says the `Version` 1 rows? This is also the first wine run of the
  QROW/QKMF/QOWN/QOMF/QMF logger lines.
- **Setup:** two owner-played sessions, single player, `workspace/wineprefix`, display `:7` fullscreen, gdb on the game
  by `tools/d2run.py`. Logger `tools/gdb/tc-party.gdb` (sha256 `698ab287…0132`), which sources `tools/gdb/tc-drops.gdb`
  as of b00199f (`dfba1ad2…1322`) and `tools/gdb/tc-party.py` (`3140f569…1502`). Breakpoints only print and continue.
  Characters were built by the architect with `tools/d2s.py build` (ADR-0003 tool-built inputs).
  - **MfNecro:** recipe `tools/d2s_recipes/mfnecro.json` (`83bb8d97…c89d`), save `workspace/runtime/owner-chars/MfNecro.d2s`
    (`da6ee2f5639793bcf8d355de0d853b815a633bfd2165e9b754f8d2d1ef922a56`). Expansion Necromancer, clvl 80, no
    mercenary. Stat 80 comes only from one item: Wisp (`rin`, unique 319) `(80, None, [10])`. Of the eight equipped
    items, no other has stat 80. There is no character stat 80 and no charm, so **MF = 10**.
  - **ClassicSorc:** recipe `tools/d2s_recipes/classicsorc.json` (`ba7645b2…ba4e`), save
    `workspace/runtime/owner-chars/ClassicSorc.d2s` (`d9fb35b5676a7ebc5dd714d0af0e85fd3e52c08a4d62d1466bf5d5381f86a3fc`).
    Status 0 (classic), Sorceress, clvl 40, Normal. Two equipped items (`sst`, `hbl`), no stat 80, so **MF = 0**.
  ```
  python3 -I tools/saves.py aside p0010r
  python3 -I tools/saves.py install p0010r workspace/runtime/owner-chars/MfNecro.d2s
  python3 -I tools/d2run.py --seed 1013 --gdb tools/gdb/tc-party.gdb --after 10800 --sound --fullscreen \
      --log workspace/logs/tc-quality-2.log
  python3 -I tools/saves.py install p0010r workspace/runtime/owner-chars/ClassicSorc.d2s
  python3 -I tools/d2run.py --seed 1014 --gdb tools/gdb/tc-party.gdb --after 10800 --sound --fullscreen \
      --log workspace/logs/tc-quality-3.log
  python3 -I tools/saves.py restore p0010r
  ```
  Logged `GAME override=1 seed=000003f5:0000029a` (×10, session 1) and `000003f6:0000029a` (×4, session 2). The owner
  used *Save and Exit* and re-entered the same character within a session, so each `GAME` line opens one game; the
  replay needs no game boundary. Each session ended with *Save and Exit*. The idle process at the main menu was then
  stopped with `wineserver -k`. Restore verified: `seedtest` back, all seven sha256 match.
- **Logs** (workspace, not in git): `tc-quality-2.log` sha256 `a963b7eb4130c682df3eee70f79f8a56a5e9f124562ea729651b69df4053bb81`;
  `tc-quality-3.log` sha256 `27605001c2238fe5a2b3192c8e9b7fac121f36f5a18a68683c9c45554a40e1d5`.
- **Saves after the sessions:** `workspace/runtime/saves-backup/p0010r/MfNecro-after.d2s`
  (`9458e641072ef03b19156dee6e2c41e42a4bd867e2b3abcf9546a3ac341e9b85`) and `ClassicSorc-after.d2s`
  (`e1dc8fbd25287abfcfacd2b42f19e7c5ada07a70d2522893e94159f5a35c4670`). Each has the same equipped items as before
  (same item seeds and property lists; only durability changed), one item with stat 80 (MfNecro) or none
  (ClassicSorc), and no charm. Picked-up items lay in the inventory only (potions, a gem, two magic items on
  MfNecro). ClassicSorc's status went 0 → 8: bit 3 is "dead" ([d2s.md](../../formats/d2s.md)) and bit 5
  (expansion) stayed clear.
- **What was played** (`PLR lvl=` of the kills): session 1 Nightmare (`diff=1`, `exp=1`), levels 110, 111, 112 and
  125, `ilvl` 2–80, 954 kills. Session 2 Normal classic (`diff=0`, `exp=0` on all 485 `TCR`), levels 46, 66, 79, 107
  and 108, `ilvl` 1–33, 459 kills. No interventions.
- **Logger lines, first run under wine (they work):** QROW, QKMF, QOWN, QOMF and QMF printed between QIN and QOUT
  on every roll that passed the early returns: 141 in session 1 and 52 in session 2. `quality.py check` asserts
  `QMF = QKMF + QOMF` on each of them, with no failure. Killers:

  | Session | Killer (`QKMF`) | Owner (`QOWN`/`QOMF`) | `QMF` | Rolls |
  |---|---|---|---|---|
  | 1 | player, Necromancer (class 2), `kmf=10` | none | 10 | 53 |
  | 1 | monster class 363 (`necroskeleton`), `kmf=0` | player class 2, `omf=10` | 10 | 85 |
  | 1 | none (`killer=00000000`) | — | 0 | 3 |
  | 2 | player, Sorceress (class 1), `kmf=0` | none | 0 | 49 |
  | 2 | none | — | 0 | 3 |

- **Procedure (reverser, static):**
  ```
  python3 -I tools/quality.py check workspace/logs/tc-quality-2.log --mf 10  # a logged QMF wins over --mf
  python3 -I tools/quality.py check workspace/logs/tc-quality-3.log
  python3 -I tools/tc.py replay workspace/logs/tc-quality-2.log --quality model --mf 10
  python3 -I tools/tc.py replay workspace/logs/tc-quality-3.log --quality model
  ```
  Counterfactuals use scratch copies of the logs and two throw-away wrappers around `quality.py`, not kept:
  - **logged MF removed:** QMF/QKMF/QOWN/QOMF dropped (and QROW in session 2), then `--mf N`;
  - **no owner MF:** `QOMF omf=0` and `QMF mf=0` on the 85 rolls that have an owner;
  - **diminishing from MF 10:** `diminish` with `< 110` in place of `<= 110`;
  - **classic rows:** `ITEMRATIO_Select` called with version 0.
- **Observed, rolls (`tools/quality.py check`; code and exit seed asserted per QIN/QOUT pair, no resync, no oracle):**
  ```
  tc-quality-2.log: 574 pairs, 574 reproduced, 0 failed (mf input=10; mf source logged:141 unused:433); codes 1:3 2:488 3:9 4:55 5:3 6:15 7:1; draws 0:433 1:1 2:5 3:63 4:5 5:64 6:3; itemratio rows 2:87 3:44 4:5 5:5 None:433; 10 QOUT without QIN (forced quality) skipped
  tc-quality-3.log: 229 pairs, 229 reproduced, 0 failed (mf input=0; mf source logged:52 unused:177); codes 1:9 2:199 3:3 4:12 6:4 7:2; draws 0:177 1:2 3:14 4:2 5:15 6:19; itemratio rows 2:51 3:1 None:177; 12 QOUT without QIN (forced quality) skipped
  ```
  The `--mf 10` input of session 1 is never used: each of the 141 rolls that reach a test logs its QMF, and the
  433 `unused` rolls stop before one. Without `--mf` the line is the same except `mf input=0` (review fix F1,
  2026-10-14).
  Exits (`-v`):
  - **Session 1:** `Normal` type 433, always-magic type 7, unique 1, set 3, rare 15, magic 48 (43 with no draw),
    superior 9, normal 55 with no draw, low 3.
  - **Session 2:** `Normal` type 177, always-magic type 2, unique 2, rare 4, magic 10 (8 with no draw), superior 3,
    normal 22 (10 on a draw), low 9.

  | Check | Failures |
  |---|---|
  | Session 1, logged MF removed, `--mf N` for N in −20, 0, 5, 8, 9, **10**, 11, 12, 15, 20, 50, 100 | 31, 37, 35, 38, 30, **0**, 9, 30, 36, 39, 31, 48 |
  | Session 1, `--mf-linear` (MF 10) | 0, the same model: at MF 10 the linear branch is taken anyway |
  | Session 1, diminishing already at MF 10 (`F` 109 in place of 110) | 24 |
  | Session 1, no owner MF on the 85 skeleton kills | 27 |
  | Session 2, logged MF removed, `--mf N` for N in **0**, 5, 10, 20 | **0**, 9, 10, 11 |
  | Session 2, `Version` 0 rows (logged rows removed) | 29 of the 52 that reach a test |
  | Session 2, `Version` 0 rows (logged QROW kept) | 52: every logged row is record 2 or 3, never 0 or 1 |

  Under the `Version` 0 rows the changed outcomes are 20 normal, 1 low, 1 superior, 2 magic, 3 rare and both
  uniques. Every draw is `RNG_RangeB(c)`, so a different `c` changes the draw itself, not only the threshold.
  - **QIN#0** (item 46, `ilvl` 19, ratio words 0): the game uses record 2 and ends normal. The normal test has
    `c` 128 and draw 82, and 82 < 128 wins. With record 0 the normal test has `c` 512 and draw 466, and 466 ≥ 128
    means low quality.
  - **QIN#91** (item 350, `ilvl` 22): the game rolls a unique with `c` 50816 and draw 110. Record 0 gives `c` 51072,
    draw 22382: a loss, and the item ends normal.
  - **QIN#136** (item 54, `ilvl` 30): the game rolls a unique with `c` 49408 and draw 47. Record 0 gives `c` 50304
    and ends low quality.
- **Observed, whole calls with no oracle (`tools/tc.py replay --quality model`):**
  - **Session 1:** `944 calls, 944 reproduced, 0 failed; monster sources checked: normal 687, minion 185, champion
    6, unique 21, superunique 19`. The first replay failed 18 calls on the superunique base TC: `tc.py` read
    `superuniques.txt` with the `Expansion` marker row counted as a record, so every superunique id ≥ 42 was off by
    one. The marker takes no record ([SuperUniques](../../tables/SuperUniques.md)). Fixed in `tc.py`. The logged
    ids then match the table: 42 Siege Boss (class 479), 49 Megaflow Rectifier (453), 51 Threash Socket (443) and 56
    Sharp Tooth Sayer (481), each with its `TC(N)` (923 Act 5 (N) Super A, 970 Super Cx, 924 Super B). No earlier
    log had an Act V superunique. After the fix, `tc-quality-1.log` gives 1269/1269 and `tc-champion-1.log` 124/124,
    both with no oracle.
  - **Session 2:** `485 calls, 302 reproduced, 183 failed`. All 183 stop at `classic selection not modelled`:
    `tc.py` models only the expansion pick (`cumExp`), and the classic pick (`cumClassic`, items/0001 §5) is not
    implemented. This is outside the quality roll; the 229 rolls of the session are reproduced by `quality.py`
    directly. Backlog entry reverser → reverser.
  - **Session 2, classic TC pick (added check, plan 0020 Phase 2, 2026-10-14; same log, no new session).**
    `tools/tc.py replay` now models the classic branch of [items/0001](0001-tc-resolution.md) §5–§8: `totalClassic`,
    the linear scan that skips expansion-only entries (§5.1), the `version ≥ 100` reject, and the throwable refund
    with its Long Sword fallback (§8). The `cm=`…`cg=` raises stay unmodelled; stock data has none, and the loader
    stops on one.
    ```
    python3 -I tools/tc.py replay workspace/logs/tc-quality-3.log --quality model
    485 calls, 485 reproduced, 0 failed; monster sources checked: normal 416, minion 36, champion 0, unique 4, superunique 3; quality: model, no oracle (mf input 0; rolls by mf source: logged 52, unused 177)
    classic calls reproduced 485: scan 664, plain 664, skip 0, miss 0, vreject 0, refund 16, lsd 0
    ```
    The oracle mode (`--quality` omitted) gives the same counts. Every pick roll, `SEL` index, quality roll, `CPRE`
    and `TCEND` of the 485 calls is asserted with no oracle. The 459 monster calls also confirm that a classic game
    takes the same `monstats` `TreasureClass*` columns and upgrade level 0.
    - **Selection:** 664 classic selections. 53 of them were in a TC with expansion-only entries. In 14 of those
      the chosen entry was the last classic one, directly followed by expansion-only entries. No pick had an
      expansion-only entry *before* the chosen one (`skip 0`), and no scan ran off the end (`miss 0`).
    - **Throwables:** 16 picks were refunded after their quality roll and upgrade draws. The items were potions of
      type `tpot` (`gpl`, `gpm`, `opm`, 11), javelins (`9ja`, `glv`, `pil`), a throwing axe (`bal`) and a throwing
      knife (`bkf`). The most in one call was 3, so the Long Sword fallback (`lsd 0`) was never reached.
    - **Not reached:** no `version ≥ 100` reject (`vreject 0`). Classic TCs reach no expansion item record here.

    | Counterfactual (scratch copies of `tc.py`, not kept) | Calls failed of 485 |
    |---|---|
    | `totalExp` and the `cumExp` search in place of the classic total and scan | 41 |
    | classic total, `cumExp` binary search in place of the scan | 0 (no pick had a skipped entry before it) |
    | classic scan without the expansion-only skip | 0 (same reason) |
    | no throwable refund | 13 |

    The checks confirm the classic total and the throwable refund. The selection rule is confirmed where no
    expansion-only entry comes before the pick. In that case the scan and the `cumExp` search agree, so the
    skip itself, the off-the-end miss, the `version` reject and the Long Sword fallback stay unexercised.
- **Conclusion:** in [items/0002](0002-quality-roll.md) this promotes, for single player and a player or summon
  killer:
  - magic find 1–10 through the linear branch (`F = mf + 100` at MF 10; the diminishing form fails 24 rolls);
  - the second non-zero MF value (10);
  - the owner's stat 80 added for a summon killer (Raise Skeleton, class 363);
  - **classic drops using the `Version` 1 rows** (contradicting src:pd-item-generation);
  - the whole roll in a classic Normal game.

  Still not exercised: MF < 0, the `*Min` clamp, a hireling or monster-minion killer, Hell, and the unique-flag and
  quest early returns. The drlg-preset logger asked for in the backlog (2026-10-13, architect → reverser, an
  `acts_open` save) was **not** attached: this run used only the drop logger.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: tc-quality-2.log, tc-quality-3.log.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-13-quality files=2 calls=1429 reproduced=1429 failed=0
  classic=485`, quality roll modelled (logged `QMF`).
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them the classic claims: the A2 clauses (without the
  `version` clause, or the sub-TC clause, classic calls fail), the classic scan, and that its skip has no observable; 6
  rolls of kills credited to no unit (`QMF 0`, no stat read). The counts and checks per statement are in [items/0001 §
  Plan 0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

## run:2026-10-14-uniques

- **Question:** plan 0019 Phase 2, stock data. Does `tools/uniques.py`, the model of
  `sub_00557450_ItemCreateByQuality` up to the builder chain's return ([items/0004](0004-uniques-sets.md) § 10),
  reproduce every logged creation on the stock tables? The Phase 1 ruling makes `sub_0065FEC0_ItemApplyProps` and the
  rare, magic, superior, low and normal builders ADR-0004 oracles. This is also the stock-data run that ADR-0010
  requires next to the forced run below.
- **Setup:** 30 agent-driven sessions, single player, expansion, Hell, `workspace/wineprefix`, display `:7`, gdb by
  `tools/d2run.py`, game directory `workspace/runtime/game` (stock: no loose data file, no `-direct`). Logger
  `tools/gdb/uniques.gdb` (`513b825c…23e7d4b5`). It sources `tools/gdb/pilot.py` (`82e542c6…56b00e79`; the
  lines the pilot steers by), `tools/gdb/uniques.py` (`9b3e988f…dd67b808`; IC0 … ICX, the lines the model checks) and
  `tools/gdb/tc-drops.gdb` as committed (`842f8613…2eba7c64`; TC resolution and the quality roll, with
  QKMF/QOMF/QMF). Breakpoints only print and continue.
  - **Character:** `UniqNova`, expansion Sorceress, clvl 80, built with `tools/d2s.py build
    workspace/merged/data/global/excel tools/d2s_recipes/uniqnova.json workspace/samples/d2s-owner/smpsor-l50.d2s
    workspace/runtime/uniques-chars/UniqNova.d2s` (ADR-0003 tool-built input). It was installed only with
    `tools/saves.py` (tag `u19`) and restored at the end with every sha256 matching. The magic find comes from stock
    uniques plus magic small charms *of Good Luck* (`magicsuffix` record 290, `mag%` 6–7 at max). The recipe went
    through four revisions during the run; the committed recipe (`3c2f57dc…78431e98`) is the last one:
    - rev 1, seeds 1951–1960: Harlequin Crest, belt of `rvl`, two kept scrolls (save `11383da9…`);
    - rev 2, seeds 1961–2011: Griffon's Eye for damage, belt columns `rvl rvl rvl mp5` (save `300659b6…`);
    - rev 3, the forced run: no kept scrolls (save `9eca59b5…`). The base save's `tsc`/`isc` at inventory (9, 2) and
      (9, 3) had covered two charms in rev 1 and 2;
    - rev 4, forced seed 3040 and later: hotkeys F1 Nova, F2 Energy Shield (save `2c793a3d…d7ddc376`).
  - **Magic find:** the game used QMF `mf=508` in rev 1 and `mf=458` in rev 2, on every roll with a player killer.
    The saved stat 80 totals are 522 and 472. The 14-point gap is the two covered charms, and rev 3 gives the logged
    472 (forced run).
  - **Route** (the owner's loop, [harness-play.md](../../../.claude/skills/reverser/references/harness-play.md)): Act
    IV town → waypoint Act V row 2 (Frigid Highlands) → Eldritch the Rectifier's pack. Every session is a new game on a
    new seed, ended by `wineserver -k`. Driver: a detached session loop (scratch `farm.py`). Per seed it starts
    `python3 -I tools/d2run.py --seed N --gdb tools/gdb/uniques.gdb --steps tools/gdb/uniques-hell.steps --after 900
    --log workspace/logs/uniques-N-hell.log`, waits for the first PLR, then runs
    `python3 -I tools/d2pilot.py farm <log> --wp 5,2 --es 30 [--players 8] --time 60`. Pilot defaults at the time:
    `--nova-hold 1.6 --max-res 75 --mana-drink 0.3 --mana-col 4`. Seeds 1951–1959: the steps file's `/players 8`
    typing landed before the game took keys, so PLAYERS = 1. From 1961 on, the pilot typed it, PLAYERS = 8.
    Energy Shield was cast through the weapon swap in this run. The owner saw it stick on the swap set (Energy Shield
    in place of Nova), which slowed the kills but changes nothing the model reads. Seeds 1960, 1963–1966, 1969, 2005
    and 2009 created no item: Eldritch lightning enchanted (resist 90, skipped), or not killed in 60 s.
- **Logs** (workspace, not in git): `workspace/logs/uniques-{1951..1969,2001..2011}-hell.log`, 30 files, sha256 per
  file in `workspace/logs/uniques-stock-manifest.txt` (`a948caf3…3cf80fbc`). The dev logs `uniques-dev-*`,
  `uniqdev*` and `uniqdev2/3-*` (pilot development, three Durance of Hate sessions that the owner stopped) are not
  part of the run.
- **Procedure:**
  ```
  python3 -I tools/uniques.py check $(cat stock.lst)                  # the 30 logs
  304 creations reproduced, 0 failed
  drop seeds {start, 666} at IC0: 304, not: 0
    unique   exp hell drop row           -       1
    set      exp hell drop no-candidate  magic   3
    rare 28, magic 23, superior 4, normal 245
  python3 -I tools/quality.py check $(cat stock.lst)
  304 pairs, 304 reproduced, 0 failed (mf source logged:76 …)
  for f in $(cat stock.lst); do python3 -I tools/tc.py replay $f --quality model; done    # summed
  284 calls, 284 reproduced, 0 failed
  ```
- **Yield** (for the plan's decision, not a frequency claim): over 30 sessions, 304 creations, 76 quality rolls with a
  player's MF, 1 unique build and 3 set builds, about 0.13 unique or set builds per session. This led to ADR-0010.
- **Conclusion:** the whole path, from the TC to the quality roll to `ItemCreateByQuality`, reproduces on stock data
  with 0 mismatches, including the unique pick (row 73 of 1 candidate) and three set failures. Those failures took
  the durability step (×2) and fell back to magic from `{S, 666}`. The required counts come from the forced run.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against `uniques-stock-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: the 30 `uniques-*-hell.log` of the stock sessions.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-14-uniques files=30 calls=284 reproduced=284 failed=0`, quality
  roll modelled (logged `QMF`); `tools/uniques.py check` over the same logs: 304 creations reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them Hell calls (the `(H)` columns), `QROW` in Hell,
  and the creation-side boundary claims of items/quality. The counts and checks per statement are in [items/0001 § Plan
  0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `uniques-stock-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the 30 `uniques-*-hell.log` (no affix or property lines).
- `tools/uniques.py check`: 304 creations reproduced, 0 failed. `tools/items_sweep.py scan` reads the switch
  qualities, the overrides, the unique and set picks (`UPK`, `SPK`, `UMADE`) and the fallbacks of every creation.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16).

## run:2026-10-14-uniques-forced

- **Question:** plan 0019 Phase 2 under [ADR-0010](../../adrs/0010-forced-path-runs.md): reproduce the unique and set
  builders and their fallbacks over ≥ 30 builds each, in classic and expansion, on ≥ 2 difficulties, with the required
  cases (a), (c) and (e), with an edited **ItemRatio** (the decision table) and every other table stock.
- **Why the path still gets stock inputs:** ItemRatio is read only by `ITEMRATIO_Select`. That function is called
  only from the drop quality roll and from the drawing body of `sub_00556F60_ItemRollQualityCreate`, which drops
  never enter ([items/0004 § 9](0004-uniques-sets.md#9-no-itemratio-read-on-the-builder-path-the-adr-0010-precondition)).
  The builders read UniqueItems, SetItems, the item bases, ItemTypes, the item seed and ilvl, none of them edited.
- **Edited table:** written with `python3 -I tools/excel_edit.py workspace/merged/data/global/excel itemratio <out>
  …` (`a13e6364…5b64feea`). The edit goes through the `itemratio` layout of `tools/excel_layouts.py`. The edited
  `.txt`/`.bin` pair passes `python3 -I tools/excel_bin.py diff <out> itemratio` (114 cells, 0 mismatches), and
  `excel_bin.py bindiff` against the stock `.bin` (`9285afed…7088b0b1`) lists only the cells below.
  - **Variant A** (`'*:Unique=0' '*:UniqueMin=1170' '*:Set=0' '*:SetMin=900'`), `itemratio.bin` `3554ac6d…cd637058`,
    24 cells, all six records:

    | record | Unique | UniqueMin | Set | SetMin |
    |---|---|---|---|---|
    | 0 (`Version` 0) | 400 → 0 | 6400 → 1170 | 125 → 0 | 5600 → 900 |
    | 1 (`Version` 0, uber) | 240 → 0 | 6400 → 1170 | 96 → 0 | 5600 → 900 |
    | 2 (`Version` 1) | 400 → 0 | 6400 → 1170 | 160 → 0 | 5600 → 900 |
    | 3 (`Version` 1, uber) | 400 → 0 | 6400 → 1170 | 160 → 0 | 5600 → 900 |
    | 4 (class specific) | 240 → 0 | 6400 → 1170 | 120 → 0 | 5600 → 900 |
    | 5 (class specific, uber) | 240 → 0 | 6400 → 1170 | 120 → 0 | 5600 → 900 |

    With the base term at 0 the chance clamps to the `Min` column, so the unique and set tests win about
    128/(Min · (1024 − TC ratio)/1024) of the time. Magic find no longer matters for those two tests.
  - **Variant U** (`'*:Unique=0' '*:UniqueMin=128'`), `itemratio.bin` `965d07e0…131506ab`: the same Unique cells,
    UniqueMin 6400 → 128 in all six records, 12 cells. Every item that reaches the unique test wins it. Used for the
    classic case (e) and for a repeated unique in one game (case (a)).
- **Game directories:** `workspace/runtime/game-forced-ir` (variant A) and `workspace/runtime/game-forced-iru`
  (variant U). Each holds symlinks to every file of `workspace/runtime/game` (pinned `game.exe` `631066c1…`, the
  stock MPQs) plus one loose file, `data/global/excel/itemratio.bin`. No other file is under `data/`. Started with
  `tools/d2run.py --game-dir <dir> --game-args=-direct` (no `-txt`).
- **The other tables are stock, and the game loaded the edited one**, shown by replaying the same logs:
  - with an excel directory holding the stock tables plus the edited `itemratio`, `tools/quality.py check` reproduces
    1469/1469 rolls (variant A) and 57/57 (variant U);
  - with the stock `itemratio`, it fails 177 and 17 of them;
  - `tools/tc.py replay --quality model` reproduces 1226/1226 TC calls (A) and 41/41 (U) on the stock TreasureClassEx,
    MonStats, item and ItemTypes tables;
  - `tools/uniques.py check` reproduces all creations on the stock UniqueItems, SetItems, item and ItemTypes tables.
- **Characters:**
  - `UniqNova` rev 3 for the forced seeds 3001–3031 and 3101–3203, rev 4 from 3040 (see the stock run). QMF
    `mf=472` on every roll with a player killer.
  - `UniqClassic`: classic Sorceress, clvl 80, the same stats. Built with `tools/d2s.py build … tools/d2s_recipes/uniqclassic.json
    workspace/runtime/monspawn-chars/cls/smpsor.d2s workspace/runtime/uniques-chars/UniqClassic.d2s` (recipe
    `e58db639…a2f80793`, save `68e46a96…31eaf0ea`). Gear: Tarnhelm, Chance Guards, Goldwrap, two Nagelrings, a magic
    amulet and leather boots *of Fortune* (`magicsuffix` record 73, `mag%` 35), belt columns `rvl rvl rvl mp5`,
    hotkeys F1 Nova, F2 Energy Shield. Saved stat 80 total 250, QMF `mf=250`.

  Saves were installed with `tools/saves.py` (tag `u19`; aside, restore and aside again to switch characters) and
  restored at the end: `seedtest` back, all seven sha256 match, `aside: none`, `harness: idle`.
- **Sessions** (driver as in the stock run; `--players 8` on every session):

  | seeds | mode, difficulty, variant | route | pilot options beyond `farm --wp`, `--es` |
  |---|---|---|---|
  | 3001–3031 | expansion Hell, A | Eldritch (wp 5,2) | `--time 60` |
  | 3040 | expansion Hell, A | Eldritch | `--time 60 --nova-key F1 --es-key F2 --es 20` |
  | 3101–3112 | expansion Nightmare, A | Eldritch, then sweep | `--time 150 --sweep` |
  | 3201–3203 | expansion Normal, A | Eldritch, then sweep | `--time 280 --sweep` |
  | 3301, 3303–3306 | classic Nightmare, A | Travincal council (wp 3,8) | `--wp-tab-x0 120 --wp-tab-w 78 --nova-key F1 --es-key F2 --es 20 --time 200` (3301, 3303) / `280 --sweep` |
  | 3401–3402 | classic Nightmare, U | Travincal | as 3304 |

  3301 went to Arcane Sanctuary: the 5-tab spacing picked the Act II tab in the classic 4-tab menu, which led to the
  new `--wp-tab-*` options. In 3402 the pilot wandered without a kill. Both logs are kept; they hold 4 and 0
  creations. Sessions 3008, 3011, 3013, 3029 and 3031 created nothing (Eldritch skipped or not killed).
- **Logs:** `workspace/logs/uforced-{3001..3031,3040}-hell.log`, `uforced-{3101..3112}-nightmare.log`,
  `uforced-{3201..3203}-normal.log`, `uforcedc-{3301,3303..3306}-nightmare.log`, `uforcedu-{3401,3402}-nightmare.log`:
  54 files, sha256 per file in `workspace/logs/uniques-forced-manifest.txt` (`af3783a4…bc46a02e`).
- **Procedure:**
  ```
  python3 -I tools/uniques.py check -v $(cat forced-a.lst forced-u.lst)
  1519 creations reproduced, 0 failed
  drop seeds {start, 666} at IC0: 1519, not: 0
  ```

  | switch quality | exit | expansion Hell | expansion Nightmare | expansion Normal | classic Nightmare |
  |---|---|---|---|---|---|
  | unique | row | 17 | 28 | 5 | 26 |
  | unique | no candidate → rare | 7 | 12 | 9 | 10 |
  | unique | already made → rare | – | – | – | 1 |
  | set | row | 12 | 9 | 3 | 4 |
  | set | no candidate → magic | 15 | 13 | 6 | 10 |

  Totals: 115 unique builds and 72 set builds; with the stock run, 116 and 75. Every failure went through the
  durability step, when the base has durability, and through one fallback step from `{S, 666}`. That fallback
  builder (rare or magic, an oracle) succeeded every time.
  - **Multi-candidate bases:** unique classic `rin` (120/121/122) and expansion Normal `rin` (120/121); set `amu`
    (nine candidates, three builds), `rin` (29/52) and `mbl` (5/110).
  - **(a)** classic Nightmare `brs`: row 86 was picked again in the game that had built it. UMADE listed 86, the
    build failed and fell back to rare, with durability ×3 (stats 72/73 34/50 → 102/150).
  - **(c)** `Djinnslayer` (290, `7sm`) and `Leviathan` (317, `uld`) in expansion Hell: ladder rows picked with
    `Game+0x6A` = 3 and `Game+0x74` = 0.
  - **(e)** classic `rin` at ilvl 53: candidates [120, 121, 122], cumulative weights 0/15/30, total 31, r = 20 → 121.
- **Not reached:** a fallback builder failing in turn; a `unique`-flag base with no candidate; a quest base; a set-29
  row; a TC-named row; an override that changes the rolled quality. The only override that wrote was `Normal` → 2,
  1 097 times, each over a record quality of 2.
- **Conclusion:** with the ItemRatio decision table edited and every other table stock, the model reproduces 1 519
  creations with 0 mismatches. That includes 115 unique builds and 72 set builds over expansion Hell, Nightmare and
  Normal and classic Nightmare, and the cases (a), (c) and (e). Together with the stock run above, it confirms the builder claims
  that items/0004 § 10 names. No claim about how often a quality comes up rests on this run.

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `uniques-forced-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the 54 logs of the record (no affix or property lines).
- `tools/uniques.py check`: 1 519 creations reproduced, 0 failed. `tools/items_sweep.py scan`: unique and set picks,
  among them the classic set picks of `uforcedc-3306` whose version test removes an expansion-set row, and the made
  bits after set builds.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16). This run is an ItemRatio-only forced run: the
  claims it backs are about code after the drop quality roll, which reads no ItemRatio cell (ADR-0013; the read list is
  items/0004 § Plan 0038 batch S2b, row 3). It backs no frequency.

## run:2026-10-14-affixes

- **Question:** plan 0021 Phase 2, stock data. Does `tools/affixes.py`, the model of the affix builders and the
  automagic pick ([items/0005](0005-affixes.md)), chained after `tools/uniques.py`, reproduce every logged creation
  on the stock tables? Boundary (architect ruling, plan 0021 Phase 1): `sub_0065FEC0_ItemApplyProps` and
  `ITEMS_RollStaffMods` are ADR-0004 oracles (entry seed asserted, exit seed taken from the log). The post-switch
  ethereal and socket rolls (items/0004 § 8) are outside both plans: their entry seed is asserted and their exit
  seed taken from the log, so the automagic pick starts from a logged seed.
- **Setup:** agent-driven sessions, single player, `/players 8` typed by the pilot, stock game directory
  `workspace/runtime/game` (no loose data file, no `-direct`), gdb by `tools/d2run.py`. Logger
  `tools/gdb/affixes.gdb` (`3bb4dfe9…f24bfa9d`, commit 5f07cec) sources `tools/gdb/pilot.py` (`82e542c6…56b00e79`),
  `tools/gdb/uniques.py` (`9b3e988f…dd67b808`), `tools/gdb/affixes.py` (`47b5b2fd…21d95500`) and
  `tools/gdb/tc-drops.gdb` (`842f8613…2eba7c64`). Seed 2101 ran `tools/gdb/affixes.py` without its `STFC` line; every
  later seed ran the committed file. Breakpoints only print and continue.
  - **Slots** (ADR-0011): slot 0 (display `:7`, `workspace/wineprefix`) for seeds 2101–2120, 2141–2145 and
    2201–2212; slot 3 (display `:10`, `workspace/wineprefix-3`) for seeds 2121–2126 and 2301–2308.
  - **Characters:** `UniqNova` rev 4 (expansion Sorceress, clvl 80, MF 472; save `2c793a3d…d7ddc376`) and
    `UniqClassic` (classic Sorceress, MF 250; save `68e46a96…31eaf0ea`), both rebuilt for this run from
    `tools/d2s_recipes/uniqnova.json` (`3c2f57dc…78431e98`) and `uniqclassic.json` (`e58db639…a2f80793`) with
    `tools/d2s.py build`, byte-identical to the plan 0019 saves. Installed only with `tools/saves.py`: slot 0 tags `a21`
    (UniqNova) and `a21c` (UniqClassic; restore and aside again to switch), slot 3 tag `a21n` (an empty aside). All
    restored at the end: slot 0 seven `seedtest` files back with every sha256 matching, slot 3 empty; `aside: none`,
    `harness: idle` on both.
  - **Driver:** a detached session loop (scratch `farm2.py`; seeds 2101–2120 ran an earlier copy without `--slot`
    that ended each session with `wineserver -k` on the slot 0 prefix). Per seed: `python3 -I tools/d2run.py --slot S
    --seed N --gdb tools/gdb/affixes.gdb --steps tools/gdb/uniques-<difficulty>.steps --after <time + 400> --log
    workspace/logs/<prefix>-N-<difficulty>.log`, wait for the first `PLR` line (120 s at most), then `python3 -I
    tools/d2pilot.py --slot S farm <log> --time T <options>`, then `python3 -I tools/slots.py stop S`.

  | seeds | slot | mode, difficulty | route | farm options beyond `--players 8 --sweep --nova-key F1 --es-key F2 --es 20 --mana-col 4 --mana-drink 0.3` |
  |---|---|---|---|---|
  | 2101–2120, 2141–2145 | 0 | expansion Nightmare | Frigid Highlands (wp 5,2) and on | `--wp 5,2 --time 240` |
  | 2121–2126 | 3 | expansion Nightmare | as above | as above |
  | 2201–2212 | 0 | classic Nightmare | Travincal (wp 3,8) and on | `--wp 3,8 --wp-tab-x0 120 --wp-tab-w 78 --time 280` |
  | 2301–2308 | 3 | expansion Normal | Cold Plains (wp 1,2) and on | `--wp 1,2 --time 240` |

  Sessions that created nothing: 2105 (the pilot's first hop left the level), 2121, 2122, 2124–2126, 2302, 2304, 2305
  and 2307 (all slot 3: the game exited at the menu or never reached a game; a screenshot of 2126 showed the `:10`
  window at 800 × 515, so the steps file's clicks missed the character screen's OK). The slot 3 expansion loop was
  stopped there; its logs are kept and hold no creation.
- **Logs** (workspace, not in git): `workspace/logs/affixes-{2101..2126,2141..2145}-nightmare.log`,
  `affixesc-{2201..2212}-nightmare.log`, `affixesn-{2301..2308}-normal.log`: 51 files, 41 with creations, sha256 per
  file in `workspace/logs/affixes-manifest.txt` (`649a41e2…d1ff1b52`). The dev log `affixes-dev-2100-nightmare.log`
  (logger development) is not part of the run.
- **Procedure** (`run.lst` = the 51 logs; `tools/affixes.py` `aeb89d9a…a0aa8`, commit 7a2a372):
  ```
  python3 -I tools/affixes.py check -v $(cat run.lst)
  3102 creations reproduced, 0 failed
  python3 -I tools/uniques.py check $(cat run.lst)
  3102 creations reproduced, 0 failed
  drop seeds {start, 666} at IC0: 3029, not: 0; skipped (restore / version 0 / no record quality): 73
  python3 -I tools/quality.py check $(cat run.lst)
  3063 pairs, 3063 reproduced, 0 failed
  for f in $(cat run.lst); do python3 -I tools/tc.py replay $f --quality model; done     # summed
  2532 calls, 2532 reproduced, 0 failed
  ```
  The 73 skipped creations are gold (record quality 0), which no builder handles.

  | builds (successful) | classic Nightmare | expansion Nightmare | expansion Normal | total |
  |---|---|---|---|---|
  | magic (`ITEMS_BuildMagic`, incl. 24 fallbacks from a failed set) | 120 | 218 | 28 | 366 |
  | rare (`ITEMS_BuildRare`) | 18 | 76 | 11 | 105 |
  | superior | 4 | 27 | 4 | 35 |
  | low | – | – | 31 | 31 |
  | normal | 396 | 1 762 | 314 | 2 472 |
  | automagic rows (expansion) | – | 34 | 2 | 36 |
  | unique / set (tools/uniques.py) | 3 / 10 | 6 / 24 | 0 / 1 | 9 / 35 |

  Mismatches: 0 in every column. Picks: 449 magic, 261 rare prefix, 253 rare suffix, 36 automagic; 283 magic picks
  ended on draw #1 (bit 0 = 0, no roll). Every builder's exit seed equals the join seed (`ICJ`), every oracle entry
  seed and the return seed (`ICX`) match.
- **Required cases:**
  - **Weighted picks against alvl (Phase 1b contradiction 1):** in 998 of 999 picks alvl ≠ ilvl + 2, 962 picks have a
    candidate set different from the rows with `level` ≤ ilvl + 2, and 989 draw over unequal weights (51 on `magic lvl`
    bases with `frequency × level`); each reproduces with alvl and the `frequency` weights.
  - **Rare counts (contradiction 2):** counts 3/4/5/6 drawn 14/16/41/34 times; affixes on the item 3/4/5/6:
    14/16/42/33. No rare has fewer than 3 affixes; one has fewer than its count: an expansion Normal `buc` (ilvl 1,
    alvl 1), count 6, sides p p p s s, then the third suffix pick found no candidate, closed the suffix side, and the
    loop ended with both sides closed at 3 prefixes and 2 suffixes. A second closure, `lgl` ilvl 2, count 5: the
    suffix side closed at slot 3 and the slot was retried on the prefix side (3 + 2 = 5). No rare jewel was logged.
  - **Names before affixes (contradiction 3):** all 105 rares draw `name1` (rare prefix block) and `name2` (rare
    suffix block) before the count draw and before any affix pick.
  - **A slot with no eligible affix:** the two rare suffix picks above (no suffix group left at alvl 1 and 2). No base
    whose type has no eligible affix at all was logged: with stock data those are the classic throwing weapons only
    (`python3 -I tools/affixes.py survey`), and none dropped as magic or rare.
  - **`classspecific`:** 26 picks of a class-specific row, 4 of them on a class item (`ob2` sorceress orb *Blazing*,
    `dr2` *Shaman's*, `dr3` *Terra's*, `ba2` *Resonant*), 22 on a classless type (e.g. *Raging* on a `hal`, *Slayer's*
    on a `bal`).
  - **Automagic on a class item:** 36 automagic rows, all on class items (type classes 0–3: amazon, sorceress,
    necromancer, paladin), on qualities 2 (10), 3 (1), 4 (22) and 6 (3).
  - **Forced affixes:** every pick had `forcedId` 0; the drop path does not reach the forced rows.
  - **Last-candidate rule:** 12 picks drew x = W and took the last candidate.
  - **Superior:** 40 rows refused by the type test, 22 redraws of a tried row.
- **Architect's extra checks (2026-10-14):** (1) staff mods: 74 rolls logged `firstSkill(c)`, each the first id of the
  class's `Skills` run (class 1: 36 ×18, 2: 66 ×24, 3: 96 ×5, 4: 126 ×15, 5: 221 ×10, 6: 251 ×2; class 0 not
  logged). (2) automagic `class_affix` in a save: not reached; no session writes a save.
- **Not reached:** a rare jewel (count `3 + low % 2`); a classic stackable or throwable base at a pick; a `sock` row
  refused by the socket test; a rare name pick with no candidate; a failed magic builder; the charm path of the normal
  builder; automagic skipped on quality 5 or 7; the version-0 bodies (no `AV0` line).
- **Plan 0019 logs rerun** with the affix builders modelled (the logs have no affix lines, so only builders that need
  no oracle can be closed): run:2026-10-14-uniques 304 creations reproduced, 0 failed (the join seed asserted after
  246 low or normal builds, 58 builds left to their oracles); run:2026-10-14-uniques-forced 1 519 reproduced, 0
  failed (1 305 asserted, 214 left).
- **Conclusion:** with the property roll and the staff mods as oracles and the ethereal and socket rolls as logged
  boundaries, the model reproduces 3 102 creations with 0 mismatches: 366 magic, 105 rare, 35 superior, 31 low and
  2 472 normal builds and 36 automagic picks, over classic and expansion and over Normal and Nightmare. It upgrades the
  selection claims of items/0005 named there. No frequency claim rests on this run.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against `affixes-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: the 51 logs of the record.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-14-affixes files=51 calls=2532 reproduced=2532 failed=0
  classic=316`, quality roll modelled (logged `QMF`); `tools/uniques.py check`: 3102 creations reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them the classic Nightmare calls (the classic scan,
  the A2 clauses, the classic upgrade gate: 316 calls with level 0, and 12 classic champions). The counts and checks per
  statement are in [items/0001 § Plan 0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and
  [items/0002 § Plan 0038 batch S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `affixes-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the 51 logs of the record.
- `tools/affixes.py check --staff model` (`ITEMS_RollStaffMods` modelled, no oracle): 3 102 creations reproduced, 0
  failed; 75 staff-mods exit seeds predicted (74 with `STFC` compared; seed 2101 has no `STFC` line), 2 934 calls on
  types without `StaffMods`. The default (oracle) check still gives 3 102 reproduced, 0 failed.
- `tools/items_sweep.py cf`: the staff-mods and pick counterfactuals over this run with the quest and items-chain
  logs (sensitivity only).
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16).

## run:2026-10-14-props

- **Question:** plan 0024 Phase 2, stock data. Does `tools/props.py`, the model of [items/0006](0006-properties.md)
  (base stats, the property roll, ethereal, sockets), chained after `tools/uniques.py`, reproduce every logged
  creation, with no ADR-0004 oracle for the property roll? The forced run below carries the counts; this run is the
  stock-data run that ADR-0010 requires next to it.
- **Setup:** agent-driven sessions on **slot 1** (display `:8`, `workspace/wineprefix-1`, ADR-0011), single player,
  expansion, Hell, gdb by `tools/d2run.py`, game directory `workspace/runtime/game` (stock: no loose data file, no
  `-direct`). Logger `tools/gdb/props.gdb` (`dca558d9…16fb616`). It sources `tools/gdb/pilot.py` (`82e542c6…56b00e79`),
  `tools/gdb/uniques.py` (`9b3e988f…dd67b808`), `tools/gdb/props.py` (`441a81b3…f17a19d`: IIS0/IIS1, APE/SLOT/SLOTR/
  ROLL/ROLLR/WR/EVD/APX, ETH*, SOK*/SSET, PDT, LX) and `tools/gdb/tc-drops.gdb` (`842f8613…2eba7c64`), all as
  committed. Breakpoints only print and continue.
  - **Character:** `UniqNova` as in run:2026-10-14-uniques (recipe rev 4, save `2c793a3d…d7ddc376`), installed with
    `tools/saves.py --slot 1` (tag `p24`). Slot 1's saves directory was empty, so `saves.py aside` was extended to set
    aside an empty directory (`tools/test_slots.py`); `restore` at the end left it empty again (`aside: none`).
  - **Route:** waypoint Act V row 2 (Frigid Highlands), Eldritch the Rectifier, then a sweep. Driver: a detached
    session loop (scratch `farm.py`): per seed `tools/d2run.py --slot 1 --seed N --gdb tools/gdb/props.gdb --steps
    tools/gdb/uniques-hell.steps --after 900`, then `tools/d2pilot.py farm <log> --slot 1 --wp 5,2 --players 1
    --time 150 --sweep --nova-key F1 --es-key F2 --es 20 --mana-col 4 --mana-drink 0.3`, then `tools/slots.py stop 1`.
  - **Sessions:** seeds 5101–5117. 5105–5107, 5109 and 5110 created items. 5101–5104 never reached the game: with
    three harness displays on Hyprland's special workspace the tiled `Xwayland on :8` window shrank below 600 pixels
    high and the menu clicks missed (fixed by floating `:8` and `:9` at 1030×800 with a session window rule; slot 0's
    window kept its size). 5108 skipped a lightning-immune Eldritch. 5111–5116 opened no waypoint menu, because the
    game rewrites the installed save on exit and the character then started in Harrogath; 5117 was stopped by hand.
    Later sessions reinstalled the save before every game (`saves.py --slot N install p24` between sessions).
- **Logs** (workspace, not in git): `workspace/logs/props-{5105,5106,5107,5109,5110}-hell.log`, sha256 per file in
  `workspace/logs/props-stock-manifest.txt` (`543ebcd8…88031c5d`). The empty logs of the other seeds are kept but are
  not part of the run.
- **Procedure:**
  ```
  python3 -I tools/props.py check $(cat stock.lst)
  168 creations reproduced, 0 failed (base-stat blocks: 168 ok, 0 failed)
    base stats: armor 16, gold 36, misc 77, quiver 6, weapon 33 (expansion)
    items: magic 22, rare 12, superior 3, normal 131 (Hell)
    ItemApplyProps calls: mode 0 85, mode 1 3; ethereal draws 4 ethereal, 38 not; socket draws 2 socketed, 12 not
    final lists checked at LX: 168
  python3 -I tools/quality.py check $(cat stock.lst)                  168 pairs, 168 reproduced, 0 failed
  tools/tc.py replay <log> --quality model, summed                     238 calls, 238 reproduced, 0 failed
  ```
- **Conclusion:** on stock data the base stats, the magic, rare and superior property rolls, the ethereal and socket
  draws and the final stat lists reproduce with 0 mismatches. No unique or set row was built in this run; the stock
  unique roll is covered by the rerun of run:2026-10-14-uniques below.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against `props-stock-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: `props-{5105,5106,5107,5109,5110}-hell.log`.
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-14-props files=5 calls=238 reproduced=238 failed=0`, quality roll
  modelled (logged `QMF`); `tools/uniques.py check`: 168 creations reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them Hell calls, 3 Hell champions. The counts and
  checks per statement are in [items/0001 § Plan 0038 batch S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16)
  and [items/0002 § Plan 0038 batch S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `props-stock-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: `props-{5105,5106,5107,5109,5110}-hell.log`.
- `tools/items_chain.py props --staff model`: 168 creations reproduced, 0 failed; all 168 join seeds predicted (the
  5 builders that ended in the oracle with no logged exit are closed); the `item_singleskill` entries at `LX`
  predicted on all 168 (2 items with staff-mod entries). `tools/props.py check`: 168 reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of the kept stock logs; no new session. `python3 -I tools/sweep_s2c.py props` and `sockets` read their
  `ETH0`, `SOK0` and `SSET` lines (with run:2026-10-15-items-chain's, through `tools/tc_sweep.py`'s stock set, sha256
  checked): no ethereal or socket roll of a drop had `rec+0x80 & 0x14`, and the 5 drop `ITEMS_SetSockets` calls of the
  two runs returned the request. Backs [items/0006 § Plan 0038 batch S2c](0006-properties.md#plan-0038-batch-s2c-2026-10-16) and [items/0007 § Plan 0038 batch S2c](0007-sockets-runewords.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-14-props-forced

- **Question:** plan 0024 Phase 2 under [ADR-0010](../../adrs/0010-forced-path-runs.md): the counts of the
  Done-when (≥ 300 base stats over weapons, armour, misc, classic and expansion and two difficulties; ≥ 50 unique,
  ≥ 30 set and ≥ 200 magic or rare property rolls; ≥ 20 socketed and ≥ 10 ethereal drops), the Phase 1b
  contradictions and the architect's required cases, with an edited **ItemRatio** and every other table stock.
- **Why the path gets stock inputs:** as in run:2026-10-14-uniques-forced. ItemRatio is read only by
  `ITEMRATIO_Select` on the drop quality roll; the builders, `ItemInitStats`, `ItemApplyProps`, the handlers, the
  ethereal and socket rolls read the item bases, ItemTypes, UniqueItems, SetItems, the affix tables, QualityItems,
  Properties, ItemStatCost and Skills, none of them edited. The edit only changes which quality a drop gets.
- **Edited table:** written with `python3 -I tools/excel_edit.py workspace/merged/data/global/excel itemratio <out> …`;
  each pair passes `excel_bin.py diff` (114 cells, 0 mismatches) and `excel_bin.py bindiff` lists only these cells:
  - **Variant A**, as in run:2026-10-14-uniques-forced (`'*:Unique=0' '*:UniqueMin=1170' '*:Set=0' '*:SetMin=900'`),
    `itemratio.bin` `3554ac6d…cd637058`, game directory `workspace/runtime/game-forced-ir`.
  - **Variant S** (`'*:Set=0' '*:SetMin=128'`), `itemratio.bin` `c80b7aea…b4301834`, 12 cells: `Set` 125/96/160/160/
    120/120 → 0 and `SetMin` 5600 → 128 in records 0–5. Every item that reaches the set test wins it. Game directory
    `workspace/runtime/game-forced-irs`.
  
  Each game directory holds symlinks to every file of `workspace/runtime/game` (pinned `game.exe` `631066c1…`, the
  stock MPQs) and one loose file, `data/global/excel/itemratio.bin`; started with `--game-dir <dir>
  --game-args=-direct` (no `-txt`).
- **The other tables are stock, and the game loaded the edited one**, shown by replaying the same logs:
  - with an excel directory holding the stock tables plus the edited `itemratio`, `tools/quality.py check`
    reproduces 1413/1413 rolls (variant A) and 691/691 (variant S); with the stock `itemratio` it fails 166 and 157;
  - `tools/tc.py replay --quality model` reproduces 1996/1996 (A) and 965/965 (S) TC calls on the stock tables;
  - `tools/props.py check` reproduces every creation on the stock item, ItemTypes, unique, set, affix, quality,
    Properties, ItemStatCost and Skills tables.
- **Characters:** `UniqNova` (as above) and `UniqClassic` (classic Sorceress, save `68e46a96…31eaf0ea`, as in
  run:2026-10-14-uniques-forced), each installed with `tools/saves.py --slot N … install p24` before every game.
- **Sessions** (driver and pilot as in the stock run; `--players 1` on every session):

  | seeds | slot | mode, difficulty, variant | route | pilot options beyond the stock run's |
  |---|---|---|---|---|
  | 5205–5219 | 2 (`:9`, `wineprefix-2`) | expansion Hell, A | Eldritch (wp 5,2), sweep | — |
  | 5303–5316 | 1 | expansion Nightmare, S | Eldritch, sweep | — |
  | 5401–5407 | 1 | expansion Normal, A | Eldritch, sweep | `--time 280` |
  | 5501–5508 | 2 | classic Nightmare, A | Travincal council (wp 3,8), sweep | `--wp-tab-x0 120 --wp-tab-w 78 --time 280` |
  | 5602 | 2 | expansion Hell, A (d2s-io session) | Eldritch | `--time 90`, no sweep; then pick-ups and *Save and Exit* |

  Seeds 5201–5204 (the display problem above), 5220–5230 (the rewritten save, before the reinstall step), 5301–5302
  (the same, in Nightmare), 5408 (stopped at the end) and 5601 (a lightning-immune Eldritch) created no item; their
  logs are kept and not part of the run.
- **The saved sample (d2s-io style, the one session allowed to *Save and Exit*):** in seed 5602, after Eldritch died,
  sixteen small charms were dropped from the full inventory to make room, three drops were picked up with Alt held
  (`7cm` rare *Highland Blade*, `brs` unique *Breast Plate*, `cqv` bolts) and the game was left by *Save and Exit*
  (`key Escape`, `click 400 262`). The written save was copied to `workspace/runtime/props-saves/UniqNova-5602.d2s`
  (`7b791f92…6327e4`) before `restore`. A saved item's `seed` is `Unit+0x28` ([save/0001 § 6](../save/0001-d2s-io.md)),
  the low word of the unit seed at IIS0, which ties it to its logged creation.
- **Logs:** `workspace/logs/propsf-{5205..5219}-hell.log`, `propss-{5303..5316}-nightmare.log`,
  `propsf-{5401..5407}-normal.log`, `propsfc-{5501..5508}-nightmare.log`, `propsf-5602-hell.log`: 45 files, sha256
  per file in `workspace/logs/props-forced-manifest.txt` (`4e6aa8a3…68f890e6`).
- **Procedure:**
  ```
  python3 -I tools/props.py check $(cat forced.lst)
  2113 creations reproduced, 0 failed (base-stat blocks: 2113 ok, 0 failed)
  python3 -I tools/props.py check $(cat stock.lst forced.lst)        # both runs together
  2281 creations reproduced, 0 failed (base-stat blocks: 2281 ok, 0 failed)
  python3 -I tools/props.py saved workspace/runtime/props-saves/UniqNova-5602.d2s workspace/logs/propsf-5602-hell.log
  3 saved items matched to logged creations: 3 reproduced, 0 failed
  ```

  Both runs together (stock + forced):

  | | expansion Hell | expansion Nightmare | expansion Normal | classic Nightmare | total |
  |---|---|---|---|---|---|
  | base stats (IIS: unit seed, values, picture) | 833 | 707 | 487 | 254 | 2281 |
  | unique rows (mode 3, 12-block walk) | 36 | 3 | 8 | 13 | 60 |
  | set rows (mode 4, prop + aprop walk) | 8 | 45 | 7 | 5 | 65 |
  | magic / rare items | 76 / 36 | 125 / 4 | 31 / 27 | 31 / 15 | 263 / 82 |
  | superior items (mode 1) | 13 | 0 | 10 | 4 | 27 |

  - base stats by category: armour 167 (20 classic), weapon 414 (50 classic), misc 1106 (120 classic), quiver 115
    (16 classic), gold 478 (48 classic);
  - `ItemApplyProps` calls: mode 0 727 (affixes and automagic), mode 1 27, mode 3 60, mode 4 65; every call's slots,
    rolls, writes, item seed and stat lists match;
  - slots per func: 1:935, 2:54, 3:75, 5:38, 6:76, 7:152, 8:78, 10:14, 11:25, 13:15, 14:6, 15:42, 16:42, 17:80,
    19:15, 20:3, 21:18, 22:6;
  - ethereal draws: 375 (15 ethereal, 360 not); socket draws: 88 (29 socketed, 59 not);
  - the final stat lists of 2264 items checked at LX (the other 17 went through a fallback durability step or a low
    builder, whose stat changes the model does not take);
  - unique and set `ItemApplyProps` calls checked on the item seed inside `tools/uniques.py` (PROPS → BRET): 125;
  - `PDT`: `DataTables+0xC6C` = 6, `+0xC70` = 63 in all 37 logged games.

  The table counts the creation by its final quality and the difficulty of its game.
  The run counts for the decision only; no frequency claim rests on a `-forced` run.
- **Phase 1b contradictions** (each a required case):
  - **func 1, superior `att`:** 11 superior items rolled `att` over 1..3 (1 ×5, 2 ×4, 3 ×2), never "max".
  - **func 2, `ac%`:** 26 magic (mode 0), 3 superior (mode 1), 17 unique and 6 set armour blocks rolled their value
    (e.g. superior `urg` 11 %, `mbt` 12 %, `fhl` 12 %); the base defense became `maxac + 1` (e.g. `ung` maxac 489 →
    490), checked in every APX list.
  - **func 6, `dmg-max`:** 76 slots, every value reproduced; no drop-path block of `dmg-max` (Properties row 28) has a
    negative `min` or `max` in any of uniqueitems, setitems (prop and aprop), the three affix tables or qualityitems
    (data check), so the clamp to `−b` is not reached on stock data.
  - **func 13, superior `dur%`:** 15 superior items rolled 10..15 (10 ×3, 11, 12 ×3, 13 ×2, 14 ×2, 15 ×3), never
    "max"; stat 72 then equals the evaluated max durability (EVD).
  - **func 19, charges:** 13 magic `charged` suffixes and 2 uniques. Example `7ss` with `magicsuffix` record 609
    (block `[243, 106, −20, −4]`, skill 106 `reqlevel` 12): L = 3, c = 20 + ⌊20 · 3 / 8⌋ = 27, the draw r = 19 over
    `27 − 3` gives 23 of 27 charges; with the item level instead of L the formula would give a different `c`. All 15
    charged stats match the logged lists (param `skill << 6 | L`).
- **Other required cases:**
  - **sockets, `startSeed % cap + 1`:** 29 socketed drops, every count equal to `start % cap + 1`; the difficulty cap
    clamped `ItemMaxSockets` in expansion Normal (cap 3 under max 4 or 5, 15 draws) and classic Nightmare (cap 4 under
    max 6: `mpi` with 4 sockets); Hell drops reached caps up to 6 (`lbb`, `mau`, `am4`). Draws under 33 socketed and
    draws at or above 33 did not, in both directions (59 not socketed).
  - **ethereal, `< 5` of 100:** 15 ethereal drops (r 0..4) and 360 eligible drops not ethereal (r ≥ 5); every
    ethereal durability became `⌊max/2⌋ + 1`, current = the logged EVD, and the base damage or defense ×3/2.
  - **a `nodurability` weapon:** 80 bows, crossbows and throwing potions drew their durability on the unit seed (e.g.
    `6hb` durability 32 → current 26, max 32).
  - **a set item with an `aprop` on the main list:** three *Civerb's Cudgel* (`gsc`, setitems row 2, `add func` 0),
    all in variant S Nightmare: `aprop1a` `dmg/lvl` (func 17, `par` 8) went to the main list (state 0, flags `0x40`)
    with the `prop` blocks. Set rows with `add func` 1 or 2 put their `aprop`s in the lists of state 165 and up
    (103 slots).
  - **quivers (archivist sweep 6):** 62 `aqv` with quantities 103..348 and 53 `cqv` with 60..246, every one drawn as
    `minstack + RangeB(maxstack − minstack)` on the unit seed; `spawnstack` is not read on that path. The saved `cqv`
    of seed 5602 holds the logged quantity.
  - **`spawnstack`:** 29 keys (`key`, minstack 1, spawnstack 6) with quantities 1..5.
- **Not reached:** func 12 (`skill-rand`, *Ormus' Robes*), func 18 (`ac/time`, ruled no case), func 23 (`ethereal`
  uniques, so *Wraithflight* too), func 24 (`reanimate`), func 36 (`randclassskill`, *Hellfire Torch*); the func 7
  fallback (+1 max damage) on a low-damage weapon; a func 14 block on a base whose `ItemMaxSockets` is 0; a
  superior ethereal item with `dur%`; classic body armour reaching the socket roll's no-draw branch.
- **Rerun of the plan 0019 logs with the property oracle replaced:**
  ```
  python3 -I tools/props.py rerun $(cat uniques-stock.lst)    # run:2026-10-14-uniques, 30 logs
  304 creations reproduced, 0 failed; ItemApplyProps calls checked on the seed (PROPS -> BRET): 1
  python3 -I tools/props.py rerun $(cat uniques-forced.lst)   # run:2026-10-14-uniques-forced, 54 logs
  1519 creations reproduced, 0 failed; ItemApplyProps calls checked on the seed (PROPS -> BRET): 104
  ```
  Those logs have no APE lines, so the rerun predicts only the item seed after each unique (77) and set (28) roll,
  from the tables alone, and compares it with the BRET seed.
- **Value inputs and oracles left:** the evaluated max durability (EVD) is a logged input; in all 15 func 13 cases it
  equals `max + ⌊max · dur% / 100⌋` of the base max (an observation, the evaluation code is not read). The staff
  mods (`ITEMS_RollStaffMods`, items/0005) stay a seed oracle inside the builders: their `item_singleskill` (107)
  entries are taken from the logged lists. The affix and automagic picks stay plan 0019 / 0021 seed oracles
  (`tools/affixes.py` is not merged); their `ItemApplyProps` calls are modelled.
- **Conclusion:** the model of items/0006 reproduces 2 281 creations with 0 mismatches over both runs, with the
  property roll modelled (no ADR-0004 oracle) for every reached func, the base stats, the ethereal and socket draws
  and the final stat lists, and 3 saved items match their logged lists. With the stock run and the rerun, it
  confirms the claims of items/0006 that the finding cites to these runs.
- **Re-analysis 2026-10-15 (static sweep, no new session): EVD predicted.** `tools/props.py` (`6bf0da0f…8c8f45ef47`)
  now computes the evaluated max durability as items/0006 § 4 reads it (`Item.eval_maxdur`: own stat 73 +
  `MulDiv(base 73, evaluated stat 75, 100)`) and compares it with every logged EVD; the logged value is still what the
  model carries on. Over both manifests:
  ```
  python3 -I tools/props.py check $(cat stock.lst forced.lst)
  2281 creations reproduced, 0 failed (base-stat blocks: 2281 ok, 0 failed)
  evaluated max durability (EVD) model vs log: func 13 15, ethereal 15 (of them with dur% 0)
  ```
  So the 15 func-13 values and the 15 ethereal halvings are predicted, not only logged. No ethereal item with `dur%`
  was among them.

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `props-forced-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the 45 logs of the record.
- `tools/items_chain.py props --staff model`: 2 113 creations reproduced, 0 failed; 1 988 join seeds predicted, the 37
  builders that ended in the oracle with no logged exit closed; `LX` staff-mod entries predicted on 2 110 (23 items;
  3 not compared because a property also wrote stat 107). `tools/props.py check`: 2 113 reproduced, 0 failed.
- `tools/items_sweep.py scan`: the low-quality `9b7` of `propsf-5406-normal` (durability from the unit seed, damage
  ×75/100), the set-29 picks of `propss-5303` and `-5315`, the set row built twice in `propss-5308`, the automagic
  skip on the set item of `propss-5309`, the classic set picks of `propsfc-5506`…`5508`, and the identified flag of
  the uniques and set items logged at `LX`.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16). This run is an ItemRatio-only forced run: the
  claims it backs are about code after the drop quality roll, which reads no ItemRatio cell (ADR-0013; the read list is
  items/0004 § Plan 0038 batch S2b, row 3). It backs no frequency.

## Re-analysis 2026-10-15: the affix and property models chained (no new session)

- **Question:** (backlog, architect → reverser, 2026-10-14) with `tools/affixes.py` and `tools/props.py` chained, does
  each run still reproduce once neither keeps the other's part as a seed oracle: the property roll in affixes.py
  (`ItemApplyProps`, APR0 → APR1) and the builders' picks plus the automagic pick in props.py?
- **Setup:** `tools/items_chain.py` (`56acff1b…7032a8d`) over `tools/affixes.py` (`75f12394…a227ce87`) and
  `tools/props.py` (`c9009b83…6c779f339`). affixes.py gained a hook (`PROPS_HOOK`) and a log-free walk
  (`Walk(free=True)`); props.py gained `apply_seed` (the seed-only walk of one affix or QualityItems row). Both
  tools' own `check` is unchanged when run alone (3 102 and 2 281 creations, 0 failed).
- **Logs:** run:2026-10-14-affixes (51 logs, `workspace/logs/affixes-manifest.txt`), run:2026-10-14-props and
  run:2026-10-14-props-forced (`props-stock-manifest.txt`, `props-forced-manifest.txt`). No log of either run carries
  both line sets: 0 of the 50 property logs has an `AF0`/`AFC`/`RN`/`RC`/`SUPD`/`LOWR`/`APR0` line and 0 of the 51
  affix logs has an `APE`/`SLOT`/`WR`/`ROLL`/`IIS0`/`EVD` line (grep), so each direction runs on its own run.
- **Procedure and observed:**
  ```
  python3 -I tools/items_chain.py affixes $(cat run.lst)            # run:2026-10-14-affixes
  3102 creations reproduced, 0 failed
  ItemApplyProps exit seeds predicted by tools/props.py: 1034
  staff mods on a type without StaffMods: seed unchanged: 2934
  python3 -I tools/items_chain.py props $(cat stock.lst forced.lst)  # run:2026-10-14-props + -props-forced
  2281 creations reproduced, 0 failed (base-stat blocks: 2281 ok, 0 failed)
    ItemApplyProps calls predicted (affix model -> APE)                754
    builders run by the affix model: magic 263, rare 83, superior 27, low 1, normal 1783
    join seeds predicted (ICJ)                                         2114
    automagic picks run by the affix model                             18
    return seeds predicted after the automagic pick (ICX)              18
    staff mods: exit not checkable                                     42
    APE lines of unique/set builders (props.py's own walk)             125
  chain: 2281 creations reproduced, 0 failed
  ```
- **What the chain covers that neither tool did alone:**
  - On the affix run, the exit seed of all 1 034 property rolls of the magic, rare, superior and automagic rows is
    predicted from the tables, no longer taken from APR1.
  - On the property runs, every one of the 754 affix and QualityItems `ItemApplyProps` calls is predicted: which row
    (affix id), in which order, and from which item seed. Before, its entry seed came from the APE line. The builders'
    success and the join seed are predicted for 2 114 creations. The 18 automagic picks run from the model's socket or
    ethereal exit seed to the return seed, which closes the join-to-automagic gap of
    [specs/items/affixes](../../specs/items/affixes.md) *Open questions* on these runs.
  - The rule that `ITEMS_RollStaffMods` moves no seed on a type without `StaffMods`, which both tools assumed for
    their legacy logs, holds in all 2 934 such calls of the affix run.
- **Limits:**
  - 42 builders end in `ITEMS_RollStaffMods` on a `StaffMods` type, which the property logs do not bracket. Their
    calls are compared, their exit seed is not.
  - No single creation is checked end to end with both the pick lines (candidates, W, draws) and the property lines
    (slots, rolls, writes, lists). That needs a run whose logger sources both `tools/gdb/affixes.gdb` and
    `tools/gdb/props.gdb` (AF0/AFC/AFX/AFR, RN0/RN/RNX, RC, SUPD/SUPT, LOWR, STF0/STF1 together with APE…APX, ETH0/
    ETHR/ETHX, SOK*, EVD, LX), with the tag clashes checked first (both log the ethereal and socket entries:
    ETH0/ETH1 against ETH0/ETHR/ETHX).

- **Addendum 2026-10-16: plan 0038 batch S1a (static, no new session; `tools/sweep_s1a.py` sha256 `c07086a3…`, log manifest `workspace/logs/sweep-s1a-manifest.txt` `18318973…1676`).** Session 5602's log (sha256
  as in `props-forced-manifest.txt`) and its saved file, re-read by `python3 -I tools/sweep_s1a.py props`, which runs
  `tools/props.py saved` (3 saved items matched to logged creations, 3 reproduced: armour, weapon and quiver fixed
  fields) and `tools/player.py check` on the new-character logs of run:2026-10-16-player (269 saved items). The save
  code reads no `ItemRatio` cell (ADR-0013). Conclusion: [save/0001 § Plan 0038 batch S1a](../save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16)
  (rows 92–96, 104, 135).

## run:2026-10-15-items-chain

- **Question:** (plan 0027 Phase 3) With both item loggers in one session, does the chained model
  (`tools/items_chain.py both`) reproduce each creation end to end, with no seed taken from the log between the affix
  or QualityItems pick and the property roll? Required case: a superior ethereal item with `dur%`
  ([items/0006 § 4](0006-properties.md#4-the-handlers-per-func), the `h + ⌊h · dur%/100⌋` reading).
- **Setup:** pinned `game.exe` in `workspace/runtime/game` (stock sessions) or a forced copy (below), slot 3 (`:10`,
  `workspace/wineprefix-3`), wine 11.17, GNU gdb 17.2. Agent-driven play only. Logger `tools/gdb/items-chain.gdb`
  (commit d38390e): `pilot.py`, `uniques.py`, `affixes.py` (ethereal bracket renamed `ETB0`/`ETB1`), `props.py` and the
  drop lines of `tc-drops.gdb`. The two item loggers share no tag; where both break on one address (`0x0065FEC0`,
  `0x00556CA0`, `0x00556B60`), each handler writes its own line.
- **Character:** `UniqNova` (expansion Sorceress, clvl 80, MF 472; recipe `tools/d2s_recipes/uniqnova.json`
  `95c8be4e…168cdc1f`, save `2c793a3d…d7ddc376`, byte-identical to the plan 0021 save), reinstalled at every launch by
  `tools/d2run.py --install h27` (slot 3 set aside empty under tag `h27`, restored at the end: `aside: none`).
- **Forced variants (ADR-0010), `itemratio.bin` only.** ItemRatio is read only by the drop quality roll
  (`ITEMRATIO_Select`); the builders, the picks, `ItemApplyProps`, the ethereal and socket rolls read none of it
  (run:2026-10-14-props-forced, *Why the path gets stock inputs*). Each loose `.bin` alone in
  `<game-copy>/data/global/excel/`, started with `--game-args=-direct`:
  - **Variant Q** (`workspace/runtime/game-forced-irq`, `9bfc9a3f…cf048603`): `Magic` → 0, `MagicMin` → 256,
    `HiQuality` → 0 in records 0–5 (18 cells).
  - **Variant H** (`workspace/runtime/game-forced-irh`, `cf24edf4…f2bd7b8d`), written with
    `tools/excel_edit.py … itemratio <out> '*:Unique=100000' '*:Set=100000' '*:Rare=100000' '*:Magic=100000'
    '*:HiQuality=0'` (30 cells; `excel_bin.py diff` 0 mismatches, `bindiff` only these cells). A base term of 100000
    gives `c = 100000 << 7`, which stays inside i32 after the `× 100` of the magic-find step (items/quality D5), and
    loses each of the four tests except with odds below 10⁻⁵; `HiQuality` 0 then wins the superior test with no draw.
    So every weapon or armour drop that is not always-magic becomes superior: one QualityItems pick per such drop.
  - **The game loaded the edited table and the other tables are stock:** `tools/quality.py check` reproduces 627/627
    quality rolls of variant H with `workspace/runtime/excel-forced-irh` (stock tables plus the edited itemratio) and
    fails 154 with the stock itemratio; variant Q 76/76 with `excel-forced-irq`; the stock sessions 167/167 on the stock
    tables. `tools/items_chain.py` runs on the stock tables for every session.
- **Sessions** (expansion Hell, Eldritch the Rectifier from the Act V waypoint row 2, then a sweep). Driver: a detached
  session loop (scratch); per seed `tools/d2run.py --slot 3 --seed N --gdb tools/gdb/items-chain.gdb --steps
  tools/gdb/uniques-hell.steps --after <T + 400> --install h27 …UniqNova.d2s [--game-dir … --game-args=-direct]`, wait
  for the first `PLR`, `tools/d2pilot.py --slot 3 farm <log> --wp 5,2 --players 1 --time 150 --sweep --nova-key F1
  --es-key F2 --es 20 --mana-col 4 --mana-drink 0.3`, then `tools/slots.py stop 3`.

  | seeds | variant | creations | end-to-end picks |
  |---|---|---|---|
  | 2701–2709 | stock | 186 | 36 |
  | 2801–2804 | Q | 76 | 22 |
  | 2901–2919 | H | 627 | 161 |

  Seeds 2701–2709 and 2801–2803 ran in the morning session of this lane (interrupted; their loop recorded the farm
  call as `--wp 5,2 --time 150`), 2804 and 2901–2919 in the evening. Sessions with no creation (2702, 2707: the
  first hop left the level; 2803: the game never reached the waypoint) are kept and count for nothing.
- **Logs:** `workspace/logs/ichain-{2701..2709}-hell.log`, `ichainf-{2801..2804}-hell.log`,
  `ichainh-{2901..2919}-hell.log`: 32 files, sha256 per file in `workspace/logs/items-chain-manifest.txt`
  (`a2a091c7…ba5f801d`).
- **Procedure and result:**
  ```
  python3 -I tools/items_chain.py both $(cat ichain.lst)          # the 32 logs
  == (1) the affix lines, property roll modelled ==
  889 creations reproduced, 0 failed
  == (2) the property lines, builders modelled ==
  889 creations reproduced, 0 failed (base-stat blocks: 889 ok, 0 failed)
  chain: 889 creations reproduced, 0 failed
  == coverage ==
    creations (IC0 .. ICX)                                                           889
    creations with both line sets                                                    889
    creations with an affix/QualityItems pick checked from both sides (end to end)   219
      ItemApplyProps calls of the picks: auto 15, pick 45, rare-p 35, rare-s 39, superior 165
      of them with an ITEMS_PickMagicAffix pick                                      66
    ethereal creations                                                               10
    superior ethereal creations                                                      9
    superior ethereal creations with a dur% slot (func 13)                           3
  both: every creation reproduced by both passes
  ```
  Every creation is checked twice: from the affix lines with the property roll modelled (no `APR1` seed taken), and
  from the property lines with the builders modelled (no `APE` entry seed taken). The 219 end-to-end creations carry
  both the pick lines (candidates, weights, draws, `SUPD`) and the slot, roll and write lines of the same
  `ItemApplyProps` call, so nothing between the pick and the property roll comes from the log.
- **Required case, superior ethereal with `dur%`** (all three variant H, all predicted by `tools/props.py`'s EVD
  model, `evaluated max durability (EVD) model vs log: … ethereal … (of them with dur% 3)`):

  | log | base | base max (73) | `dur%` | EVD at func 13 | `h = ⌊max/2⌋ + 1` | stat 73 | stat 72 = EVD after the halving |
  |---|---|---|---|---|---|---|---|
  | `ichainh-2903` | `xrs` | 50 | 11 | 55 | 26 | 26 | 28 = 26 + ⌊26·11/100⌋ |
  | `ichainh-2904` | `7ba` | 35 | 12 | 39 | 18 | 18 | 20 = 18 + ⌊18·12/100⌋ |
  | `ichainh-2908` | `7ha` | 28 | 15 | 32 | 15 | 15 | 17 = 15 + ⌊15·15/100⌋ |

  The code's order (`h` first, the percentage on `h`) holds in all three. None of the three discriminates it from
  src:arreat-summit-item-pages' `⌊⌊max/2⌋ · (100 + dur%)/100⌋ + 1` (the two differ only when
  `⌊(m+1)·d/100⌋ > ⌊m·d/100⌋`, `m = ⌊max/2⌋`; here 2 = 2 each time), so the contradicted verdict stays a code reading.
- **Conclusion:** the chained model of items/0005 and items/0006 reproduces 889 creations from both sides with
  0 mismatches, 219 of them end to end from the pick to the written stats, and the superior ethereal `dur%` path
  (`h + ⌊h · dur%/100⌋`, stat 73 = `h`) in three cases. No frequency claim rests on variants Q and H.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against `items-chain-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: the stock sessions only, `ichain-{2701..2709}-hell.log` (the forced 28xx/29xx sessions are left out).
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-15-items-chain files=9 calls=256 reproduced=256 failed=0`, quality
  roll modelled (logged `QMF`); `tools/uniques.py check`: 186 creations reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them Hell calls, 3 Hell champions, the creation
  seeds of items/quality F. The counts and checks per statement are in [items/0001 § Plan 0038 batch
  S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `items-chain-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the stock sessions only, `ichain-{2701..2709}-hell.log`.
- `tools/items_chain.py both --staff model`: 186 creations reproduced by both passes, 0 failed; 3 staff-mods exit
  seeds predicted at `STF1`, 185 join seeds predicted in the property pass (3 oracle builders closed), the `LX`
  staff-mod entries of 2 items predicted.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of the kept stock logs; no new session. With run:2026-10-14-props (its addendum of the same date): the
  drop records' forced bits (none set) and the drop `ITEMS_SetSockets` calls, two normal drops among them with 3
  sockets. Backs [items/0006 § Plan 0038 batch S2c](0006-properties.md#plan-0038-batch-s2c-2026-10-16) and [items/0007 § Plan 0038 batch S2c](0007-sockets-runewords.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-15-items-chain-forced

- **What:** the ADR-0010 id of the forced sessions of run:2026-10-15-items-chain (architect review 2026-10-15): seeds
  2801–2804 (ItemRatio variant Q) and 2901–2919 (variant H), with the setup, variants, logs and manifest recorded there.
  A `[C]` that rests on these sessions cites this id; run:2026-10-15-items-chain alone means the whole set.
- **Split** (`tools/items_chain.py both`, rerun at review on the merged tools):

  | sessions | creations, both passes | end to end | of them with an `ITEMS_PickMagicAffix` pick | superior ethereal `dur%` |
  |---|---|---|---|---|
  | stock 2701–2709 | 186, 0 failed | 36 | 33 | 0 |
  | forced 2801–2804, 2901–2919 | 703, 0 failed | 183 | 33 | 3 |

- **What it backs:** the three superior ethereal `dur%` items (all variant H), so the stat 73 = `⌊max/2⌋ + 1` and
  stat 72 values of [items/0006 § 4](0006-properties.md#4-the-handlers-per-func) for these three cases; the chained
  model on superior QualityItems picks. It backs no frequency, and nothing about the quality roll that reads ItemRatio.
  Variant H is an ADR-0010 decision-table edit: the cells are listed in the parent record, the builders, picks,
  `ItemApplyProps` and the ethereal roll read no ItemRatio cell, and `tools/quality.py check` shows the edited table
  loaded (627/627) with the other tables stock.

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `items-chain-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: `ichainf-{2801..2804}-hell.log`, `ichainh-{2901..2919}-hell.log`.
- `tools/items_chain.py both --staff model`: 703 creations reproduced by both passes, 0 failed; 21 staff-mods exit
  seeds predicted, 702 join seeds, `LX` staff-mod entries of 16 items. `tools/items_sweep.py scan`: the seven
  superior weapons whose `dmg%` took the `+1` max-damage fallback (`ichainh-2910` … `2919`), and the func-10 params.
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16). This run is an ItemRatio-only forced run: the
  claims it backs are about code after the drop quality roll, which reads no ItemRatio cell (ADR-0013; the read list is
  items/0004 § Plan 0038 batch S2b, row 3). It backs no frequency.

## run:2026-10-15-uniques-tcnamed-forced

- **Question:** (plan 0027 Phase 3, items/0004 cases (b) and (d)) Is a TC-named unique row taken with no draw when
  it passes the filter, and does a TC cell naming a duplicated name resolve to its **first** row, here the disabled
  `Azurewrath` (row 29, `crs`), which then fails `enabled` and falls to the weighted pick over `crs` candidates?
- **Forced path (ADR-0010), `treasureclassex.bin` only.** No stock TC that a monster reaches names a unique
  (`tools/uniques.py survey`: only `Annihilus` in `ROP (N)`/`ROP (H)`). Written with
  `tools/excel_edit.py … treasureclassex <out> '777:Item1=The Oculus' '777:Item2=Azurewrath' '822:Item1=The Oculus'
  '822:Item2=Azurewrath'` (text cells, commit 98b64c4): records 777 `Act 5 (H) Super A` and 822 `Act 5 (H) Super Ax`
  (same group 18, level 90; Eldritch's Hell TC and its group mate). `Prob1`/`Prob2` stay 2 and 2, `Picks` −4, so each
  kill of a superunique on that TC makes two Oculus and two Azurewrath creations. `excel_bin.py diff` 0 mismatches,
  `bindiff` 4 changed fields. Game copy `workspace/runtime/game-forced-tcn` (`5c200dd6…1bebdda5`, `-direct`); excel
  directory `workspace/runtime/excel-forced-tcn` (stock plus the edited pair). The TC table feeds only the drop
  resolution; the builders read UniqueItems, ItemTypes and the item bases, none edited.
- **Sessions:** seeds 3201–3203, expansion Hell, slot 3, `UniqNova` as in run:2026-10-15-items-chain, logger
  `tools/gdb/items-chain.gdb`, `farm --wp 5,2 --players 1 --time 120 --sweep` (other options as there). Eldritch died in
  all three. Logs `workspace/logs/tcnamed-{3201..3203}-hell.log`, manifest `tcnamed-forced-manifest.txt`
  (`6df87083…4695de8b`).
- **Result:**
  ```
  python3 -I tools/uniques.py check workspace/logs/tcnamed-320[1-3]-hell.log --excel workspace/runtime/excel-forced-tcn -v
  108 creations reproduced, 0 failed
    unique exp hell drop  made               rare   3     # the second Oculus of a game
    unique exp hell drop  no-candidate:fail  rare   6     # Azurewrath -> crs, disabled
    unique exp hell drop  row                -      4     # 3 Oculus (named, no draw) + 1 ordinary unique
  -- named (12)
     oba row+1 285 forced 284      (x6)
     crs row+1 30  forced -1       (x6)
  python3 -I tools/tc.py replay <each log> --excel workspace/runtime/excel-forced-tcn    # 44 + 61 + 58 calls, 0 failed
  python3 -I tools/items_chain.py both workspace/logs/tcnamed-320[1-3]-hell.log             # 108 reproduced, 0 failed
  ```
  - **(b)** The named `The Oculus` (row 284, record `+0x40` = 285) passed the filter and was taken with no draw, three
    times (once per game); the second named creation of each game found the row made and fell back to rare.
  - **(d)** `Azurewrath` resolved to row 29 (record `+0x40` = 30), the first of its two rows (the second is the
    enabled ladder `7cr` row): the row failed `enabled`, the weighted pick over `crs` had no candidate, the build
    failed and fell back to rare, six times.
  - `tools/tc.py` now resolves unique and set names (data/0001 § 7 steps 3–4); the replay builds the entries with
    flags `0x11`, index = the row's base, `aux` = the row, and reproduces every TC call of the three logs.
- **Conclusion:** the TC-named preference, its filter test and the first-row rule of the name tree are reproduced on
  a forced path; no frequency claim. **Architect review 2026-10-15:** the run agrees with items/0004 §§ 3.2, 6 but
  raises no tag. The edited cells are the TC cells those claims are about, and only edited data reaches a named row in
  a run, so under ADR-0010 they stay `[I]` (the plan 0019 ruling on case (d) stands). (run:2026-10-15-uniques-tcnamed-forced)

## run:2026-10-15-sockets

- **Question:** plan 0029 Phase 2. Does `tools/sockets.py`, the model of
  [items/0007](0007-sockets-runewords.md) (the insert tests, the gem/rune transfer, the link, `RUNEWORD_Match`,
  `RUNEWORD_Apply` through `tools/props.py`'s handlers, the charge refill) and of the client test
  `sub_004843E0_UiCanInsertSocket`, reproduce every logged insert, runeword and client verdict, with the child's item
  seed at the insert as the one input (ADR-0004, items/0007 § 8)?
- **Setup:** agent-driven sessions on slots 2 and 4 (displays `:9`, `:11`) and one on slot 1 (`:8`), single player,
  Normal, gdb by `tools/d2run.py`, game directory `workspace/runtime/game` (stock: no loose data file, no `-direct`).
  Logger `tools/gdb/sockets.gdb` (`6f61e197…7ae901`) sourcing `tools/gdb/sockets.py` (`d82f7871…375fac4`), as
  committed in 8057bb5 and unchanged since; breakpoints only print and continue. Entry `tools/gdb/sock-enter.steps`
  (`5145caea…76d`); inserts played by `tools/d2pilot.py insert <log> --slot N $(cat tools/gdb/sock-<name>.plan)`
  (inventory, cube and paper-doll cells in [tooling](../../../.claude/skills/reverser/references/tooling.md)
  § Inventory actions). Each session installs one character with `d2run.py --install`, after `saves.py --slot N
  restore`/`aside`.
- **Characters:** one per session, built with `tools/d2s.py build` from `tools/d2s_recipes/sock-<name>.json`
  (written by `tools/socket_sessions.py write`, `e9183d55…cac68cb`) on the expansion or classic base save; the load
  session uses `socketnova.json` (Phase 0, save `2f2cb8dd…14ff1a`, three bases pre-filled in the cube).
- **Built (forced) states (ADR-0010):** the test-state keys of `d2s.py build` make states the game's own builders do
  not: `"quality"` on a plain code (an empty-affix low, superior, rare or crafted base: sessions `cases1`, `cases2`,
  `forced`, `gems5`, `jewels`), `"identified": false` (`refuse`: a magic cap with two sockets and a magic jewel),
  socket counts above the `ITEMS_SetSockets` quality clamps (`forced`: magic crystal sword 6, magic shield 4, rare
  crystal sword 5, crafted long sword 4; `"unclamped_sockets": true` in the recipe since the builder learnt the
  clamp), and runes in a classic character (`classic1`, `classic2`). None of these changes a path the model
  reproduces: they are loaded through `ITEMS_SetSocketsOnLoad` and the save reader, and the insert reads them as
  the run logs them.
- **Sessions** (log `workspace/logs/sockets-<name>-s<slot>-<seed>.log`):

  | session | slot, seed | game | holds | inserts |
  |---|---|---|---|---|
  | rw1 … rw7 | 2, 2001–2007 | expansion | runeword bases and their runes, right and wrong orders, wrong types, magic/rare/crafted bases, *Wirt's Leg*, the *Bramble* 3-of-4 case, *Spirit* (a `server` row) | 15, 16, 18, 16, 21, 21, 17 |
  | gems1 … gems5 | 4, 4001–4005 | expansion | every gem and skull into a helm, an armour, a weapon and a shield | 24, 27, 26, 17, 13 |
  | gems1 | 2, 2011 | expansion | gems1 again, a second character build | 27 |
  | jewels | 4, 4006 | expansion | magic and rare jewels into every class | 8 |
  | cases1, cases2 | 4, 4007–4008 | expansion | low, superior, rare and crafted bases (the Phase 1b crafted cap case) | 10, 14 |
  | forced | 4, 4009 | expansion | the above-clamp socket counts, filled | 22 |
  | refuse | 4, 4010 | expansion | a potion onto a socketed item, a gem onto an unsocketed buckler, onto an unidentified socketed cap, onto a full item; an unidentified jewel | 5 |
  | classic1, classic2 | 2, 2013–2014 | classic | gems into every class; a rune into a helm | 20, 2 |
  | cubenef | 2, 2012 and 2015 | expansion | 3 Tir → Nef in the cube, then *Black* completed by the new Nef (2012 logged 2 inserts; 2015 repeated the session) | 2, 3 |
  | load | 1, 1001 | expansion | `socketnova`: five pre-filled children (save reader), *Tir El* into a short sword (*Steel*), a gem onto it full | 7 |

  An earlier calibration log (`sockets-cal-s2.log`, slot 2, seed 101, 09:04) was taken with the logger before its
  commit (8057bb5, 09:12) and is not part of the run. The lane was interrupted after the other 22 sessions (by
  09:32); when it resumed, after merging `main` (ebde719), the `load` session (18:55) replaced the calibration log
  with the committed logger and the same `socketnova` save (`2f2cb8dd…`). The
  calibration log is kept in the workspace; it reproduces too (8 inserts, 0 mismatches, architect review
  2026-10-15), so dropping it removes no failing case.
- **Logs** (workspace, not in git): the 23 files listed in `workspace/logs/sockets-run.lst` (`8476a47a…554827`),
  sha256 per file in `workspace/logs/sockets-run-manifest.txt` (`f800b80b…dda7d0d9`).
- **Procedure:**
  ```
  python3 -I tools/sockets.py check $(cat workspace/logs/sockets-run.lst)
  351 inserts reproduced, 0 failed; 357 client tests
    insert outcomes: packet inserted 345, packet child not identified 1, reader inserted 5
    successful inserts: gems 178 (packet exp 154, classic 21, reader 3), runes 159 (packet exp 157, classic 1,
      reader 1), jewels 13 (packet magic 10, rare 2, reader 1); gems and runes into weapon, shield and helm/armour
    runewords made: 50 from 29 rows
    client test verdicts: ok 346, cursor item not a socket filler 4, target full 2, target not socketed 5
    transfers: gem group 0/1/2 69/54/55, rune group 0/1/2 58/58/43, jewel (none) 13
    gem x group coverage: 105 of 105 (gems 35 x groups 3)
    charges refilled 50 (14 with an entry raised); full item, no runeword 60; one rune more than the sockets 1;
    server row in a non-ladder game 1
    runeword property funcs reached (added 2026-10-15 after the review; per func in items/0007 § 5):
      1 2 3 5 6 7 8 10 11 15 16 17 19 21 22 23; stock lines not reached: 20 24
  exit 0
  ```
- **Done-when coverage (plan 0029 Phase 2):**
  - inserts: 351 (≥ 150); every gem and skull of every grade into each of the three `gemapplytype` groups; runes into
    each class; magic and rare jewels.
  - runewords: 50 from 29 rows (≥ 30 from ≥ 8). Ranged lines made repeatedly: *Splendor* 5 times (`ac%` 89, 71, 74,
    67, 98), *Sanctuary* 4. Aura: *Bramble* twice (Thorns level 19 and 18). Refused: wrong type (*Splendor*'s runes in
    a helm), wrong order (*Lum Eth* in a shield), magic, rare and crafted bases, a `quest` base (*Wirt's Leg*), a
    `server` row in a non-ladder game (*Spirit*), the 3-socket *Bramble* prefix.
  - refused inserts: five different situations, four different first-failing tests: a potion (client: not a socket
    filler), an unsocketed buckler (client: not socketed), an unidentified socketed cap (client: not socketed, its
    client flags lack bit 11), a full item (client: full), an unidentified jewel (server: child not identified, after
    `child_sock`). The server's other refusals (cursor, parent mode, `hasinv`, full) sit behind the client's test and
    cannot be reached by clicks.
  - classic: gems accepted into every class; a rune, placed into a helm, was sent by the client and accepted by the
    server (no game-type test anywhere); no runeword can form (no classic-legal row, Phase 0 survey).
  - Phase 1b cases: the crafted cap of 3 (`forced`: a crafted long sword with 4 sockets loaded and took 4); the
    `gemoffset` text is not observable on stock data (items/0007 *Leads used*).
  - § F6 clamps: magic bases with 6 and 4 sockets, a rare with 5 and a crafted with 4 loaded and filled (forced path).
    `ITEMS_SetSockets`' own clamps are not executed by any insert and stay inferred.
- **Conclusion:** every insert, transfer, link, match, runeword roll, refill and client verdict of the run reproduces
  with 0 mismatches. The completing rune's item seed is `{startSeed, 666}` for the 49 runes loaded from a save and an
  advanced seed for the rune the cube made; *Black* completed by it reproduced from that seed.
- **Limits:** no rune above the character's level (no level test observed either way); `etype` untested (no stock
  `complete` row uses it); the client's identified, flag `0x100`, `ItemMaxSockets` and UI-state tests were not
  reached; the golem reader and the item copier did not run.

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of this run's kept logs; no new session. `python3 -I tools/sweep_s2c.py logs` checks each log's sha256
  against `sockets-run-manifest.txt` (`workspace/logs/sweep-s2c-manifest.txt` (sha256 `5820525c…9280ba`)).
- Logs: the 23 of `sockets-run.lst`. `python3 -I tools/sweep_s2c.py sockets`: the 5 reader inserts (child in mode 4,
  parent bit 0 left clear), the 345 successful packet inserts (parent bit 0 set in all, bit 14 cleared in the 18 that
  had it), the 337 transfers (160 with `nummods` different from the group's blocks, 327 with a gems row other than 0),
  the runes inserted (Pul 3, Ith 4, Sol 6, Ohm 6), the *Spirit* row returned by the match, and `ItemData+0x38` still 0
  on the 50 runewords made.
- Backs the plan 0038 S2c rulings in [items/0007 § Plan 0038 batch S2c](0007-sockets-runewords.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-15-cube

- **Question:** plan 0030 Phase 2. Does `tools/cube.py`, the model of [items/0008](0008-cube.md) chained after
  `tools/items_chain.py` (tools/uniques.py, tools/affixes.py, tools/props.py), reproduce every logged transmute from
  the cube's contents and the game seed at `CUBE_Transmute` (the CUB0 line): the rows that reach the matcher and their
  results, the matched row and its three output slots, every output's creation record, every game-seed, unit-seed and
  item-seed draw, every builder pick and property roll, the mod lines, the destroy and the placed items, with no
  seed oracle between the match and the output?
- **Setup:** agent-driven sessions on slot 1 (display `:8`, prefix `workspace/wineprefix-1`), single player, game
  directory `workspace/runtime/game` (stock: no loose data file, no `-direct`), gdb by `tools/d2run.py`. Logger
  `tools/gdb/cube.gdb` (`406fd79b…1c8f68`) sourcing `tools/gdb/uniques.py` and `tools/gdb/props.py` (unchanged) and
  `tools/gdb/cube.py`, in three revisions that differ only by fields added to the UNIT dump (no line, address or
  breakpoint changed): r1 as committed in 6ad1627 (`754b82bf…ecc96`) for cal, craft1–5 and reroll1; r2 = r1 plus
  `xy` (the item's grid cell) for reroll2, reroll3, forced, rare1, rare2, upg1, upg2 and sock1–3; r3 = r2 plus
  `seed28` (`Unit+0x28`), as committed in 085beeb (`e0cbd2ef…75aa8c`), for the other sessions. Entry steps
  `tools/gdb/cube-enter-{normal,nightmare,hell}.steps`. Transmutes played by `python3 -I tools/d2pilot.py cube <log>
  --slot 1 --plan tools/gdb/cube-<name>.plan --ins-gap 1.2 --pick-wait 0.5` (open the inventory and the cube, move
  each step's inputs from their inventory cells into the cube, press Transmute at (240, 340), wait for the CUBX line,
  put the output back into input 1's cells from the cube cell the CUBX line gives, or the inputs back when nothing
  was produced). Each session installs one character with `d2run.py --install h30p2`, after `saves.py --slot 1
  restore`/`aside`.
- **Characters:** one per session, built with `tools/d2s.py build` from `tools/d2s_recipes/cube-<name>.json` (written
  by `tools/cube_sessions.py write`, `572a2b1c…`; the build hashes are in `tools/test_d2s.py`) on the expansion base
  save (the classic session on the classic one): an expansion Sorceress of level 80 unless the table says otherwise.
- **Built (forced) states (ADR-0010):** the inputs are builder items (magic items with one suffix, rare items with
  names and no affixes, normal bases, uniques with their maximal properties), as plan 0030 Phase 0's ruling (3)
  allows for match inputs; the rerolled and crafted outputs are new items, so none of the input properties reach an
  output except through a copy (`useitem`, `mod`), whose lists are compared with the input's. The cow sessions use
  the recipe keys `quests: "all"` and `quest_bits` (the player's quest words 4 bit 10 and 40 bit 0), and Wirt's Leg
  carries stat 356 (`item_stats`) in Nightmare and Hell: the save states a game in those difficulties would hold.
- **Sessions** (log `workspace/logs/cube-<name>-s1-<seed>.log`; transmutes in the last column):

  | session | seed | game, difficulty, level | holds | n |
  |---|---|---|---|---|
  | cal | 3005 | exp, Normal, 80 | a gem and a rune upgrade, a magic reroll, a crafted ring, two chipped rubies (no row) | 5 |
  | craft1 … craft5 | 3011–3015 | exp, Normal, 80/80/20/99/50 | 9 crafted rings and amulets each, the four families in turn, input ilvl 1–99 | 45 |
  | craftgear | 3017 | exp, Normal, 80 | crafted gloves, boots, belt, helm (two), `upg` inputs (rows 66, 74, 85, 91, 73) | 5 |
  | reroll1 … reroll3 | 3021–3023 | exp, Normal, 80/80/40 | row 60 on magic rings, amulets, jewels and small charms, ilvl 1–99 | 27 |
  | forced | 3024 | exp, Normal, 80 | rows 6–10 (the `pre=` rows) | 8 |
  | rare1, rare2 | 3031, 3032 | exp, Normal, 80/60 | row 61 (six perfect skulls) and row 62 (skull and *The Stone of Jordan*) | 14 |
  | upg1, upg2 | 3041, 3042 | exp, Normal, 80 | 12 gem upgrades; rune upgrades 51, 52, 55, 59, 100, 103 and the ladder rows 104, 107, 111, 122 | 22 |
  | sock1 … sock3 | 3051–3053 | exp, Normal, 80 | the rune socket rows 123–126 on body armours, helms, shields, weapons | 10 |
  | sock4 | 3054 | exp, Normal, 80 | rows 15, 16, 147; row 63 on a rare amulet (no row); the next step's items left in the cube (no CUB0) | 4 |
  | sock5 | 3055 | exp, Normal, 80 | row 63 on a rare short sword, cap and kite shield | 3 |
  | nomatch | 3061 | exp, Normal, 80 | eleven contents that match no row (counts, qualities, missing or extra items) | 11 |
  | cowopen | 3071 | exp, Normal, 80 | row 2 (opens), row 2 again (refused), rows 148, 149, 150 | 5 |
  | cowking, cowbaal | 3072, 3073 | exp, Normal, 80 | row 2 with the player's word 4 bit 10 set; with word 40 bit 0 clear | 2 |
  | cownm | 3074 | exp, Nightmare, 80 | row 2 with a leg of stat 356 = 0 (no row), then 356 = 1 (opens) | 2 |
  | cowhell | 3075 | exp, Hell, 80 | row 2 with a leg of 356 = 1 (no row), then 356 = 2 (opens) | 2 |
  | kinds1, kinds2 | 3081, 3082 | exp, Normal, 80 | rows 129, 133, 130 (`mod` upgrades), 137, 139 (`rep`, `rch`), 17, 18 (`suf=`), 19 (an item type) | 8 |
  | classic | 3091 | classic, Normal, 50 | rows 23, 28, 47, 5, 13, 7, 61, 11, and row 60 (version 100: no row) | 9 |

  Calibration logs taken while the pilot was written (`cube-cal-s1-3001..3003`, `cube-dbg-s1-3004`: the output was
  picked up at the wrong cube cell, so later steps ran on wrong contents) and the first craftgear session
  (`cube-craftgear-s1-3016`, the same fault on a 2 x 2 output) are not part of the run; craftgear was repeated with
  the fixed pilot (3017). The model reproduces those five logs too (12 transmutes, 0 failed; architect review
  2026-10-15): the fault changed what was in the cube, not the model's agreement with the game.
- **Logs** (workspace, not in git): the 29 files listed in `workspace/logs/cube-run.lst` (`63003177…5e64913`), sha256
  per file in `workspace/logs/cube-run-manifest.txt` (`67513910…4ff6f`).
- **Procedure:**
  ```
  python3 -I tools/cube.py check $(cat workspace/logs/cube-run.lst)
  182 transmutes reproduced, 0 failed
  rows: 60:28, 71:7, 61:8, 62:7, 70:6, 79:6, 80:6, 89:6, 88:5, 97:5, 98:5, 2:6, 123:3, 125:3, 23:3, 63:3, 7:3, ...
        (69 rows in all), none:16
  outputs: usetype q8 51, usetype q4 33, usetype q6 15, item q2 30, item q4 10, type q4 1, useitem 18,
           cow portal 6, pandemonium portal 1, pandemonium finale portal 1
    ItemApplyProps calls predicted (affix model -> APE) 301; ItemInitStats (created) 140; join seeds predicted 140
    builders run by the affix model: crafted 51, magic 44, rare 15, normal 30, low 1; pick forced row 12
    crafted count (tier): 2 (1) 1, 2 (2) 8, 3 (1) 2, 3 (2) 2, 3 (3) 11, 4 (1) 2, 4 (2) 4, 4 (3) 4, 4 (4) 17
    creation roll (record quality 0) -> 1: 9, -> 2: 14, -> 3: 4, -> 6: 2
    ItemCopy useitem 15, mod 3; mod: ItemInitStats on the copy 3; mod lines 170 (funcs 1, 2, 8, 11, 14); sock= 3
  exit 0
  ```
  The model is also unchanged on the earlier runs it builds on: `tools/items_chain.py affixes` on run:2026-10-14-affixes
  (3102 creations) and `props` on run:2026-10-14-props (168), and `tools/sockets.py check` on run:2026-10-15-sockets
  (351 inserts), 0 failed each.
- **Test vectors** (2026-10-16): `python3 -I tools/cube.py vector <log> <n>` re-checks the n-th transmute of a log
  and prints every draw in order with its seed (game, unit, item), checking each seed's continuity to CUBX. Two are
  published in [items/0008 § 8.5](0008-cube.md#85-test-vectors-backlog-2026-10-15-from-run2026-10-15-cube):
  `cube-craft1-s1-3011.log` 2 (row 70) and `cube-reroll1-s1-3021.log` 2 (row 60). Of the 182 transmutes, 181 print
  as one continuous sequence; `cube-cowopen-s1-3071.log` 5 has none (§ 8.5).
- **Done-when coverage (plan 0030 Phase 2):** 182 transmutes (≥ 150); 51 crafted (≥ 40; hit power, blood, caster
  and safety, rings, amulets and five pieces of gear); 28 magic rerolls (≥ 20); 15 rare rerolls (≥ 10); 27 rune or
  gem upgrades (≥ 20); 16 socket recipes (≥ 10: rows 123–126, 15, 16, 147, 63); 16 transmutes that match no row
  (≥ 10); the cow portal opened three times (Normal, Nightmare, Hell) and refused three ways; a classic session in
  which row 60 (version 100) reaches no matcher. No seed oracle lies between the match and an output: every created
  item, every copy and every mod line is predicted from the game seed at CUB0. The only boundary oracles are the cow
  portal's spot search (`0x00545340`) and portal object (`0x0056D130`): their return values and the game seed after
  each (they draw from it) are taken from the log; no item is created after them in a transmute.
- **Phase 1b cases:**
  - ladder rows in single player: rows 104, 107, 111 and 122 (`ladder` 1) matched and made their runes, with
    `Game+0x6A` = 3 and the ladder word 0;
  - op 28: Wirt's Leg with stat 356 = 1 matches in Nightmare and 356 = 2 in Hell; 356 = 0 in Nightmare and 356 = 1 in
    Hell match no row. So the test is stat 356 ≥ the difficulty, and equality passes;
  - the rune socket rows: every one rolls `sock` 1..6 whatever the class: a gothic plate rolled 6 (4 sockets), a
    great helm 5 (3), a kite shield 5 (3), a quilted armour 5 (2); the count is then the `sock` handler's cap
    (ItemMaxSockets and the size), not a per-class range of 1–4 / 1–3 / 1–4;
  - the Pandemonium rows: row 148 and row 149 were matched (CROW), their handler entered (PAN 2, PAN 3) and returned 0;
    nothing was destroyed or placed, and the keys and organs stayed in the cube.
- **Other observations:**
  - row 63 refused a rare amulet: output A is `useitem` with `sock`, and the socketable first-input test
    (`ItemMaxSockets` = 0) keeps it out of input 1, so no row matched; a rare short sword, cap and kite shield
    took the socket;
  - the output's cell in the cube after the placement (oracle `sub_00560200_InvPlaceItem`, not modelled): a 1 x 1
    output at (2, 3) (70 times), a 2 x 1 at (1, 3), larger ones at (0, 0);
  - the forced ids are block-relative: `pre=331` gave prefix *Prismatic* (merged id 747 + 331), `pre=372`, 353, 392,
    412 *Garnet*, *Cobalt*, *Coral*, *Jade*, `pre=191` *Savage*, `suf=162` *of Spikes*, `suf=352` *of the Leech*.
- **Conclusion:** every transmute of the run reproduces with 0 mismatches; the claims of [items/0008](0008-cube.md)
  that the run exercised are confirmed (§ 8 of the finding lists them, and what stays inferred).
- **Limits:** no `output b`/`output c`, `uns`, `rem`, `reg`, `tmp`, mod `chance`, op 1–27 (no stock row has them);
  `rep` only on items already at full durability and `rch` only on an item with no charges; no ethereal upgrade (the
  open question on `ItemInitStats` and the ethereal bonus stays open); no stackable output with `qty=`; one item-type
  output (row 19); the cow portal's spot search and object creation are oracles; ops on the player (1–14) and on
  input 1 (15–27) are not reached. The created item's flag word is read from its CRECX line, not predicted
  (architect review 2026-10-15: no claim of § 8 rests on it; the identified bit set at placement is predicted).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/sweep_s2c.py logs` checks each log's sha256 against `cube-run-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2c-manifest.txt` (sha256 `5820525c…9280ba`); the reports are `workspace/logs/sweep-s2c-*.txt`.
- Logs: the 29 of `cube-run.lst`. `python3 -I tools/sweep_s2c.py cube` runs `tools/cube.py`'s model per transmute
  (182 reproduced, 0 failed) and adds: the output placement modelled with tools/player.py's inventory spot search on
  the 3 × 4 cube grid (100 logged cells reproduced, 0 mismatches; 61 cells not logged by logger r1), the 140 creation
  records (`+0x28` = 1, `+0x2A` = the item version, `+0x18` = 4), the 12 forced picks against their rows' level windows
  (all inside), the ethereal skip bit on the 132 outputs that carry it, the 104 tests of the `exc` input rows, and the
  cow portal's game-seed steps (spot search 0, portal object 171, 173, 171).
- Backs the plan 0038 S2c rulings in [items/0008 § Plan 0038 batch S2c](0008-cube.md#plan-0038-batch-s2c-2026-10-16), [items/0005 § Plan 0038 batch S2c](0005-affixes.md#plan-0038-batch-s2c-2026-10-16),
  [items/0006 § Plan 0038 batch S2c](0006-properties.md#plan-0038-batch-s2c-2026-10-16), [items/0002 § Plan 0038 batch S2c](0002-quality-roll.md#plan-0038-batch-s2c-2026-10-16) and [items/0004 § Plan 0038 batch S2c](0004-uniques-sets.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-15-vendors

- **Question:** plan 0031 Phase 2. Do the three vendor saves load and come back item for item? Does
  `tools/vendors.py`, the model of [items/0009](0009-vendors.md) (the store seed end to end: the candidate lists,
  `VENDOR_BuildStock`, `VENDOR_PickNormalQuality`, the stock upgrade draw, `GAMBLE_BuildInv` with `GAMBLE_Upgrade`; the
  triggers), reproduce every logged stock build and gamble window, and does each created item reproduce in the item
  model (`tools/items_chain.py`)? Boundary (architect ruling, plan 0031 log): `HIRE_BuildStock` is a logged oracle
  (S asserted at its entry, taken at its exit); the `g_GambleList` order is dumped once per run (`VGL`) and used as
  data.
- **Setup:** agent-driven sessions on harness slot 1 (display `:8`, prefix `workspace/wineprefix-1`), single player,
  pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by `tools/d2run.py`, `-seed` per session. Logger
  `tools/gdb/vendors.gdb` (`b80f5a7a…`, 8b1bb0a) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`), `tools/gdb/uniques.py`
  (`9b3e988f…`), `tools/gdb/affixes.py` (`47b5b2fd…`) and `tools/gdb/vendors.py` (`eddbff8c…`, cff86d0, unchanged
  for every run session); the props session uses `tools/gdb/vendors-props.gdb` (`a9af02ae…`) with
  `tools/gdb/props.py` (`441a81b3…`) in place of `affixes.py`. Breakpoints only print and continue. NPCs driven by
  `tools/d2pilot.py npc` and `wpchain` ([tooling](../../../.claude/skills/reverser/references/tooling.md) § NPC actions;
  the pilot was refined between sessions and feeds no model; final version b9632a8). Entry steps
  `tools/gdb/enter-{normal,nightmare,hell}.steps`. Each session installs one save with `d2run.py --install h31p2`,
  after `saves.py --slot 1 restore`/`aside`.
- **Characters:** the Phase 0 recipes, built with `tools/d2s.py build` on the Phase 0 bases: `VendorNova`
  (`vendornova.json`, expansion, clvl 30, `eed8939c…`), `VendorNova75` (`vendornova75.json`, clvl 75, `dc2ca939…`),
  `VendorClassic` (`vendorclassic.json`, classic, clvl 30, `d2e264dc…`; status byte `0x00`, the waypoint list shows
  four act tabs). No test-state key: no forced state.

### Step 1: the three vendor saves (Phase 0 review ruling)

- **Procedure:** for each save, `python3 -I tools/d2run.py --slot 1 --seed 12345 --install h31p2 <Save>.d2s --steps
  tools/gdb/vendor-load.steps --after 3 --log workspace/logs/vendor-load-<tag>.log` (no debugger): *Single Player*,
  *OK*, *Normal*, inventory and character sheet shown, *Save and Exit Game*; the written save copied out and compared
  with the built one (`d2s.py dump` diff, `d2s.py survey`, `d2s.py roundtrip`, a byte diff).
- **Observed:** all three load; the character enters the Act IV town (the difficulty bytes' act 3). The written files
  have the same size and the same two items (Town Portal and Identify scrolls, same cells and fields); the item
  difference is the `new` flag cleared (bit `0x2000`, bytes `0x357`, `0x365`). Header differences only: checksum,
  `last_played`, one appearance byte (`0x8D`), the map seed (12345), the difficulty bytes `83 83 83` → `83 00 00`
  (only the played difficulty keeps bit 7), and, in the two expansion saves, quest byte `0x1AA` (as in
  run:2026-10-15-cube-saves). Gold is not clamped on load: 300 000 / 750 000 inventory and 2 000 000 stash are shown
  and written back. `d2s.py survey` 3 files 0 errors; `roundtrip` 6 items 0 differences. Written sha256:
  VendorNova `f7026b39…`, VendorNova75 `3f8cd14b…`, VendorClassic `bd21c8ca…`.
- **Result:** the built hashes are pinned in `tools/test_d2s.py` (`RECIPE_BASES`, 9b143a6; 41 tests OK). Logs
  `workspace/logs/vendor-load-{nova,nova75,classic}.log` (launcher headers only), screenshots and saves in
  `workspace/logs/vendor-saves/` and `workspace/scratch-h31p2/saves/`.

### Step 2: the stock and gamble sessions

- **Sessions** (log `workspace/logs/vendors-s1-<seed>-<tag>.log`):

  | seed, tag | save | game, difficulty | NPCs opened (trade; gamble windows) | stock builds | gamble windows |
  |---|---|---|---|---:|---:|
  | 3201 normal | VendorNova | expansion, Normal | all 16 store NPCs of Acts I–V; Jamella 40, Anya 5, Alkor 5, Elzix 5, Gheed 5 | 20 | 60 |
  | 3202 nightmare | VendorNova | expansion, Nightmare | all 16; gambles as 3201 | 20 | 60 |
  | 3203 hell | VendorNova75 | expansion, Hell | all 16; Jamella 50, Anya 10, Alkor 10, Elzix 10, Gheed 10 | 20 | 90 |
  | 3204 normal75 | VendorNova75 | expansion, Normal | Halbu, Jamella, Malah, Larzuk, Anya, Ormus (the Normal caps of Acts III–V) | 6 | 30 |
  | 3205 classic | VendorClassic | classic, Normal | the 12 classic store NPCs of Acts I–IV | 13 | 55 |
  | 3206 classicnm | VendorClassic | classic, Nightmare | the 12 classic store NPCs | 12 | 15 |
  | 3207 hellprops | VendorNova75 | expansion, Hell, props logger | Halbu, Jamella, Larzuk; Jamella 10, Anya 5 | 3 | 15 |

  Each tour: Act IV first (Halbu, Jamella, a run of Jamella gamble windows, then a wait so that more than 240 s pass
  before leaving), then Acts V, III, II and I by waypoint, the hirelings opened once (Kashya, Greiz, Asheara,
  Qual-Kehk), a waypoint hop out of a town to a wilderness waypoint of the same act and back (Act I in 3202 and 3203,
  Act III in 3201, and Act II → Lost City by a misrouted hop in 3201, 3202 and 3205), and back to Act IV to trade with
  Halbu and Jamella again. Run list `workspace/logs/vendors-run.lst` (`63592608…`), per-file sha256 (with the three
  load logs) in `workspace/logs/vendors-run-manifest.txt` (`4f48ef49…`).
- **Calibration logs, not part of the run:** `vendors-s1-probe1`, `-probe2`, `-3111-normal`, `-3112-normal`,
  `-3113-normal`, `-3121-nightmare` were taken while the logger and the pilot were being written (logger versions
  before cff86d0: no `TICK`, `STALEX` or `OBJS`, `HBX` also logged on the join of `NPC_OpenStore`). With the
  committed model they reproduce with 0 mismatches except `probe2`, whose single failure is that `HBX` without an
  `HB0`. They are kept in the workspace.
- **Procedure:**
  ```
  python3 -I tools/vendors.py check $(cat workspace/logs/vendors-run.lst)          # exit 0
  python3 -I tools/items_chain.py props workspace/logs/vendors-s1-3207-hellprops.log  # exit 0
  ```
- **Observed** (`tools/vendors.py check`, trimmed; the full output is `workspace/scratch-h31p2/run-check.txt`):
  ```
  games 7; store seeds predicted (NPCSTORE_CtlCreate) 7; gamble list dumps (VGL) 7 (one order, the same each run)
  stock builds 94 (candidate lists compared with the record 94); stock items created 4656; not placed 348
  gamble builds 325 (4550 slots); classic gamble redraws (expansion base) 94
  store-seed draws: stock builds 7513, gamble builds 16130; HIRE_BuildStock oracle (S taken at HBX) 16
  item seeds predicted from the game seed 9206 (game-seed steps per creation: 2)
  items reproduced by the item chain (uniques -> affixes -> props) 8787; checked on IC0 only (property log) 419
  stock upgrade draws: nightmare 1532, hell 1189
    nightmare exp: none 419, NightmareUpgrade 513, uber 50
    nightmare classic: none 184, NightmareUpgrade 338, uber 28
    hell exp: none 584, none+HellUpgrade 452, uber 67, uber+HellUpgrade 61, ultra 14, ultra+HellUpgrade 11
  gamble qualities: normal magic 1820, rare 208, set 1, unique 1; nightmare magic 955, rare 93, set 2;
    hell magic 1341, rare 129
  gamble upgrade tests 2292 (uber 1669, ultra 623), passed 440; with lvl - qlvl <= 2: 185;
    bound <= 0, no draw: uber 1340, ultra 626
  gambled ilvl - clvl: clvl 30 and clvl 75: -5 .. +4 (every value)
  NPCSTORE_ActStale: townEmpty 0 26, townEmpty 1 6; stores marked stale 7 (252.5 .. 375.7 s after the build);
    stores reset by a town leave 20; stale rebuilds (reset at the open) 7
  vendors: 0 mismatches
  ```
  `items_chain.py props` on 3207: 419 creations reproduced, 0 failed (base stats 419); the affix model run inside
  the property log: 419 creations, 0 failed.
- **Done-when coverage (plan 0031 Phase 2):**
  - every store NPC of Acts I–V opened in at least two difficulties: the 16 expansion store NPCs in Normal, Nightmare
    and Hell (3201–3203), the 12 classic ones in Normal and Nightmare (3205, 3206); 4656 stock items (≥ 1 000), each
    reproduced from the store seed and the game seed at its build.
  - 4550 gambled items over 325 gamble windows (≥ 300 over ≥ 50) at clvl 30 and clvl 75; every window was opened by
    *Gamble* after the previous window's close (`GFREE` from `sub_00572F20_NpcInteractRemove`).
  - rebuilds of the same vendor in one game: Halbu and Jamella after a stale mark (3201, 3202, 3203), Ormus, Alkor,
    Akara, Gheed and Charsi after a same-act waypoint hop (3201, 3202, 3203).
  - classic sessions: 3205 and 3206.
  - the Phase 1b cases: below.
- **Phase 1b and Phase 1 required cases:**
  - (a) `<Vendor>MagicLvl` is a minimum stock level: Charsi in Normal Act I (stock `ilvl` 12) gave no magic copy of
    `hla` (`MagicLvl` 15), `stu` (20) or `rng` (255), Gheed none of his 14 `MagicLvl`-20 bases; `MagicLvl` 255 bases
    (`tgl`, `hgl`, `tbt`, `tbl`, `scy`, `lxb`, `rng`) never got one at any `ilvl` up to 80; and 4097 of the 4375 affix
    picks on magic stock items have `alvl` above the entry's `MagicLvl` (e.g. `mpi`, `MagicLvl` 20, `ilvl` 35:
    `alvl` 26).
  - (b) the gamble upgrade: every one of the 2292 tests reproduced its bound `(lvl − qlvl)·Gamble* + 1` and its draw
    `R(S, 10000)`; at `lvl = qlvl` the bound is 1 (pass only on r = 0); 623 elite tests, each after a failed
    exceptional draw of the same slot, none otherwise.
  - (c) the gambled affix window: every slot's `ilvl` lies in `clvl − 5 .. clvl + 4` at both levels, and every affix
    pick of a gambled item reproduced from that `ilvl` by the general alvl rule (`tools/affixes.py`): picks on a
    clvl-75 character ranged from `alvl` = clvl − 34 to clvl + 17 (bases with a magic level), so there is no
    `+6/−3` window around the character's level.
  - the classic Nightmare/Hell `ubercode` fatal assert (Phase 1 open question): **not reachable on stock data.** In
    3206, 28 classic stock items took their `ubercode` (e.g. `swb` → `8sw`, `chn` → `xhn`) and were created and
    reproduced; every `ubercode`, `NightmareUpgrade` and `HellUpgrade` of every classic stock entry is a classic
    base (`version` 0: 972 cells, 0 expansion targets; computed from the item tables with `tools/vendors.py`'s
    `Tables`). The Phase 1 example `hax` → `9ha` is classic too.
- **Triggers observed** (`STALE`/`STALEX`, `RESET`, `TO`): a waypoint hop to **another act** reaches
  `NPCSTORE_ActStale` from `sub_00537340_TownLevelLeave` (return 0x00537402) with `townEmpty` 0 in all 26 cases: the
  act's built stores are marked stale only when more than 240 000 ms have passed since their build (7 marked, at
  252.5–375.7 s after it, from the `buildTick` before and after the call; none marked sooner, which the model would
  report as a mismatch), and each was reset and rebuilt at its next trade open (`TO` stale 1, sole 1 → `RESET` →
  `BS0`). A hop to a waypoint of the **same act** (Lut Gholein → Lost City, Kurast Docks → Spider Forest,
  Rogue Encampment → Cold Plains) gives `townEmpty` 1 in all 6 cases: every built store of the act is destroyed at
  once, by `NPCSTORE_Reset` when its NPC unit is still there with no interaction, or by the clear path (built 0, no
  `RESET` line) when the unit is gone (Asheara and Hratli in 3201), and rebuilt at the next trade open. All 94 trade
  opens built (81 first opens, 6 after a reset, 7 of a stale store); no trade open met a built, non-stale store.
- **Conclusion:** the stock model, the gamble model and the triggers of items/0009 reproduce with 0 mismatches over
  94 builds, 325 gamble windows and 9206 created items, and every created item reproduces in the item model. The
  claims it promotes are listed in [items/0009 § Phase 2](0009-vendors.md#phase-2-runtime-results-run2026-10-15-vendors).
- **Limits:** no level-up between builds (the level-up note stays inferred); no multiplayer game (the shared stock,
  the sole-interactor test with two players and the stale mark with players left in town stay inferred); no purchase (the
  copy and `sub_00576F50_StoreItemSold` not exercised); no `Cracked` retry and no code mismatch (`CRK`, `CMM` never
  logged: stock quality is never 1 at `ilvl` ≥ 6, and no created code differed from the chosen one); the gamble `lvl`
  clamp to 5..99 not reached (clvl 30 and 75); 348 stock items found no room on their tab (`VENDOR_CreateStockItem`
  0, placement) and none of the 94 builds reached 33 failures; `HIRE_BuildStock` stays an oracle.
  Added at the review (architect, 2026-10-16): no walk out of a town (every same-act exit was a waypoint), and the
  `STALE`/`STALEX` lines carry no current tick, so the age of a store kept unmarked is not in the log: the 240 000 ms
  threshold is shown from the marking side only (7 marks, all after 240 s, none sooner), the kept side rests on the
  code (0x0053730A).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of this run's kept logs; no new session. `python3 -I tools/sweep_s2c.py logs` checks each log's sha256
  against `vendors-run-manifest.txt` (`workspace/logs/sweep-s2c-manifest.txt` (sha256 `5820525c…9280ba`)).
- Logs: the 7 of `vendors-run.lst`. `python3 -I tools/sweep_s2c.py vendors`: the 9 206 store creation records at
  `IC0` (`+0x80` = 2, row 0, no restore, quality and ilvl as passed, the game's item version), the identified flag on
  all 4 656 stock and 4 550 gamble items, the stock qualities (2 ×848, 3 ×131, 4 ×3 677), no `CRK`/`CMM`, the 419 trade
  opens against the slot table, the 32 stale-test record lists in class order, and the `buildTick` order of 83 builds
  against the 7 stale marks (0 out of order).
- Backs the plan 0038 S2c rulings in [items/0009 § Plan 0038 batch S2c](0009-vendors.md#plan-0038-batch-s2c-2026-10-16), [items/0004 § Plan 0038 batch S2c](0004-uniques-sets.md#plan-0038-batch-s2c-2026-10-16) and
  [items/0005 § Plan 0038 batch S2c](0005-affixes.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-16-quest-drops

- **Question:** plan 0032 Phase 2. Do the five quest saves load and come back with no quest bit lost? Do the B6 test
  (`tools/tc.py`'s `b6_model`), the scripted drops on the quest seed and the three NPC item services
  (`tools/questdrops.py`) reproduce what the game does, every created item through the item chain, and does an act
  boss keep its MonStats level in an expansion Nightmare and Hell game (`tools/monpool.py`)? Boundary (architect
  ruling, plan 0032 log): quest bits and per-player counts are inputs; each scripted drop takes the quest seed it finds
  (`QGS`, a boundary oracle) and the start value is checked once at `QUESTS_InitGame`.
- **Setup:** agent-driven sessions on harness slots 3 (display `:10`, `workspace/wineprefix-3`) and 4 (`:11`,
  `workspace/wineprefix-4`, from 11:22 on, at most one game per slot), stock data, pinned `game.exe`, gdb by
  `tools/d2run.py`, `-seed` per session. Logger `tools/gdb/quests.gdb` (`9793f746…`) sourcing `pilot.py`
  (`1ad48a4c…`), `uniques.py` (`9b3e988f…`), `affixes.py` (`f2ac1c63…`), `vendors.py` (`eddbff8c…`), `mon-pool.py`
  (`2c17c655…`), `quests.py` and `tc-drops.gdb` (`842f8613…`). `quests.py` changed during the run: sessions up to 3322
  have no `FOP` line, sessions up to 3343 log ECX (the game) as the `B6X` tc (the checkers then rely on the `DROP`
  base), from 3344 on `e8a2a3e8…` (dd177b8). Breakpoints only print and continue. Played by `tools/d2pilot.py`
  (`npc … imbue|socket|personalize`, `objop`, `hunt`, `farm`, `explore`, `wpchain`, `cube`; the pilot was refined
  between sessions and feeds no model), driven by session scripts in the lane's scratch directory. No owner play.
- **Characters** (built with `tools/d2s.py build` on `smpsor-l50.d2s`, level 80 Nova Sorceress; hashes pinned in
  `tools/test_d2s.py`): the Phase 0 recipes `QuestFresh` (`9a12da6e…`), `QuestFreshV` (`0a495ee7…`), `QuestRewards`
  (`7dfe9bc2…`), `QuestRewardsH` (`4e7b9134…`; both the recipes at commit `32a1a6e`, revised after this run, see Result), `QuestCows` (`6700b4e3…`), and four made for this run:
  `QuestServices` (`questservices.json`: `QuestRewardsH`'s bits, the Hellforge Hammer **equipped** in the right hand,
  five magic caps, two plain caps, the Soulstone with stat 356 = 2; first revision `5637d644…` for sessions 3311–3324,
  then `a9e32c29…` whose hammer carries stat 356 = 2, sessions 3325 on), `QuestB6` (`questb6.json`: `QuestFresh` plus
  word 6 bit 1 and a Horadric Staff, `c28e894c…`), `QuestFreshVH` (`QuestFreshV` plus a staff, `a3ef1b20…`),
  `QuestDurielK` (`QuestFreshVH` plus word 14 bit 5, `fc022ab5…`). Stat 356 on the hammer is a state the game itself
  gives a created quest item (Hephasto's `hfh`), written by the builder's `item_stats`; no test-state key, no table edit.

### Step 1: the five quest saves (Phase 0 review ruling)

- **Procedure:** for each save, `d2run.py --slot 3 --seed 12345 --install h32p2 <Save>.d2s --steps
  tools/gdb/quest-load.steps --after 3` (no debugger): *Single Player*, *OK*, *Normal*, inventory and character
  sheet, *Save and Exit*; the written save compared with the built one (`d2s.py questbits <written> <built>`,
  `survey`, `roundtrip`, a byte diff).
- **Observed:** all five load (Act I town; the difficulty bytes give act 0). `questbits`: `QuestFresh`, `QuestFreshV`
  0 words differ. `QuestRewards`, `QuestRewardsH`: bit 15 added to words 3, 35 and 38 in all three difficulties (each
  had bit 1 saved: the loader's copy, items/0010 § 3) and word 40 bit 10 added in Normal only; `QuestCows`: word 40
  bit 10 in Normal. No bit lost. Word 40 bit 10 is set at the join by `sub_0058E430_A5Q6_PlayerJoin` (`QS` return
  0x0058E4D0 in every session whose save had word 40 bit 0) in the played difficulty: this is the `0x1AA` byte of
  run:2026-10-15-cube-saves and run:2026-10-15-vendors. Other differences: checksum, `last_played`, appearance bytes,
  the map seed, the Nightmare/Hell difficulty bytes `0x80 → 0`, current mana and stamina regenerated past the built
  value (the gear's bonuses), the items' `new` flag. `survey` 5 files 0 errors; `roundtrip` 149 items 0 differences.
  Written sha256: QuestFresh `13e6d6e5…`, QuestFreshV `15647120…`, QuestRewards `ada4d161…`, QuestRewardsH
  `aaea6dc9…`, QuestCows `69cf7cba…`. The reward states offer their reward with bit 15 set beside bit 1 (the handlers
  test bit 1 only): imbue, socket and personalize were served in every services session. The Hellforge of the
  Phase 0 reward recipes cannot be struck above Normal (their hammer has no stat 356; Step 2): backlog to the archivist.
- **Result:** the five built hashes are pinned in `tools/test_d2s.py` (`RECIPE_BASES`). **Update (architect, review of
  `lane/abl`, 2026-10-16):** the archivist then revised `questrewards.json`/`questrewardsh.json` (hammer equipped;
  356 = 2 on the H hammer), so those two pins are `None` until a load; the loaded saves rebuild from
  `git show 32a1a6e:tools/d2s_recipes/questrewards.json` (and `questrewardsh.json`) with the command above.

### Step 2: the sessions

Logs `workspace/logs/quests-s<slot>-<seed>-<tag>-<difficulty>.log`; screenshots `workspace/logs/h32p2/<seed>/`.
`quests-s3-3301-probe.log` (logger calibration: `PZ` at the wrong address, one forge) is not part of the run.

| seeds | save | difficulty | what | result |
|---|---|---|---|---|
| 3311–3318 | QuestServices | Normal | imbue (Act I), socket and personalize (Act V), Hellforge | 8 imbues, 6 sockets, 6 personalizations; forge 3315, 3317, 3318 (3311–3314 never reached it, 3316 clicks did not operate) |
| 3321–3326 | QuestServices | Nightmare | the same | 6 / 6 / 6; forge 3325, 3326 (3321–3324: strikes refused, hammer without stat 356) |
| 3331–3333 | QuestServices | Hell | the same | 3 / 3 / 3; forge: died on the way three times |
| 3341–3347 | QuestFresh, QuestB6, QuestFreshV | Normal | Andariel | kills 3344 (fresh), 3345 (bits 1, 15), 3347 (done); 3341–3343, 3346 routing failures |
| 3348–3350 | QuestRewards | Nightmare, Hell | Andariel created (boss case) | 3349 Nightmare (created, not killed), 3350 Hell (killed); 3348 routing failure |
| 3351–3359 | QuestFresh, QuestFreshV | Normal | Mephisto | 3356 fresh killed; quest done: 3352, 3357, 3358, 3359 failed (moat, descent) |
| 3361 | QuestCows | Normal | cow portal, cows | 565 hell bovines killed; the Cow King not met |
| 3362–3371 | QuestB6, QuestFreshVH, QuestDurielK | Normal | Duriel: staff in the orifice, portal, kill | 3364 fresh, 3368 bit 0 only, 3371 bit 5; 3362 wrong tomb, 3369 orifice not reached |
| 3401–3408, 3421–3423 | QuestFresh, QuestFreshV, QuestRewards, QuestB6 | Normal, Nightmare | the Countess | none killed (see shortfalls) |

- **Procedure:**
  ```
  python3 -I tools/questdrops.py check <run logs>
  for l in <run logs>; do python3 -I tools/tc.py replay $l; python3 -I tools/items_chain.py affixes $l; done
  python3 -I tools/monpool.py check workspace/merged/data/global/excel <run logs>
  ```
- **Observed** (53 session logs: run list `workspace/logs/quests-run.lst` `6c940900…`, per-file sha256 with the five load
  logs in `workspace/logs/quests-run-manifest.txt` `874d63db…`):
  ```
  questdrops: quest seed starts 53 (each = {low of one game-seed step, 666}); quest-bit writes 1431, each "old" word
    as the earlier writes left it; quest-seed fetches 28, every entry seed the one the model held (no oracle taken)
  B6 (b6_model, B60..B6X): Andariel Normal taken 2 (fresh; bit 0 only), not taken 1 (bits 1 and 15: stops at 15),
    Hell taken 1 (bit 0 only); Duriel taken 2 (fresh; bit 0 only), not taken 1 (bit 5); Mephisto taken 1 (fresh)
  scripted draws: Andariel 3 (gcy skc gsg), Hellforge waves 20 and runes 5 (r03 r07 r10 Normal, r13 r19 Nightmare);
    hammer drops 11 (hfh, quality 7, no draw); not modelled, no draw: Mephisto's mss (1), the Jade Figurine j34 (1)
  imbues 17 (clvl 80 -> ilvl 84, quality 6, same index, flags80 0x22); Larzuk 15 (magic caps, max 2:
    RangeB(item seed, 2) -> 1 x8, 2 x7, stat 194 = n); personalizations 15 (flag 0x1000000, the name)
  questdrops: 0 mismatches
  tc.py replay: 2724 TC_ResolveDrops calls reproduced, 0 failed (565 hell bovines among them); every B6 group tied
    to its DROP base; 3341 and 3354 have no kill (exit 1 for an empty log only)
  items_chain.py affixes: 1856 creations reproduced, 0 failed (the 17 imbued rares among them)
  monpool.py check: 23306/23306 match (Andariel Nightmare level 49, Hell level 75: Level(N)/Level(H), not MonLvlEx)
  ```
- **Done-when coverage (plan 0032 Phase 2):**
  - the five quest saves loaded, written back, `questbits` clean beyond the load rules; hashes pinned (Step 1).
  - B6 taken and not taken: Andariel (Normal) and Duriel (Normal) both ways, Mephisto (Normal) taken only (the
    not-taken case is a shortfall); every quest-TC drop reproduced by `tc.py`.
  - the Countess with her quest not done and done in two difficulties: **shortfall** (below).
  - Hellforge: 5 operations, the gems and the rune reproduced in Normal (3) and Nightmare (2); Hell is a shortfall.
  - Charsi's imbue 17 times and Larzuk's sockets 15 times, each a fresh game from the reward save, reproduced.
  - the cow portal and 565 cow kills with their drops; the Cow King was not met.
  - the `boss` case: Andariel created in an expansion Nightmare and Hell game, level reproduced by `monpool.py`.
  - the Phase 1b case (the Act I `TCQuestId` label): Andariel's `TCQuestId` 6 read record word 6 in every B6 group.
- **Shortfalls** (claims stay `[I]`; attempts are consecutive scripted sessions) (run:2026-10-16-quest-drops):
  - Mephisto with his quest done (B6 not taken): 4 attempts (3352, 3357, 3358, 3359): the Durance descent or the moat.
  - The Countess (no quest dependence, her rune TC): not killed in 10 attempts over the four states (Normal not done
    3401, 3402, 3404, 3405; Normal done 3406, 3407, 3408; Nightmare done 3421, 3423; Nightmare not done 3422; 3403 ended by
    a script error): the five-cellar descent stalls, and twice she was created but not reached (3404).
  - The Hellforge in Hell: 3 attempts (3331, 3332, 3333), each a death on the way.
  - The Cow King's eight `vps`: not met in 3361.
  - Not attempted: a kill by a hireling, a golem or an `exp`-state caster; a party; a classic game; the imbue below
    clvl 6; Larzuk on a non-magic item.
- **Owner-played addendum (proposed, same run id):** slot 4, `tools/gdb/quests.gdb`, no steps, `--after 3600`; one
  session per line, never *Save and Exit*:
  1. Mephisto, quest done (`QuestFreshV`, Normal): waypoint Durance of Hate 2, down to 3, kill Mephisto.
  2. The Countess, quest not done (`QuestFresh`, Normal): Black Marsh, Forgotten Tower, Tower Cellar 5, kill her.
  3. The Countess, quest done (`QuestFreshV`, Normal): the same.
  4. The Countess, quest not done (`QuestB6`, Nightmare): the same.
  5. The Countess, quest done (`QuestRewards`, Nightmare): the same.
  6. The Cow King (`QuestCows`, Normal): open the cube (it holds the leg and a tome), Transmute, take the red portal,
     kill the Cow King (and cows).
  7. The Hellforge in Hell (`QuestServices`, Hell): River of Flame, click the forge once (soulstone), three strikes,
     wait for the gems and the rune.
- **Conclusion:** the quest-TC switch, the quest seed and its scripted draws, the three NPC services and the `boss`
  level exception reproduce with 0 mismatches over 53 sessions; the promoted claims are listed in
  [items/0010 § Phase 2](0010-quest-drops.md#phase-2-runtime-results-run2026-10-16-quest-drops).
- **Addendum 2026-10-16 (static, lane `rbl`, no new session):** read again from the 53 logs of `quests-run.lst` with
  `python3 -I`: (1) in every log the `QI0` game seed (at `QUESTS_InitGame`'s entry) is exactly three LCG steps past
  `Init(N)` of the header's `-seed N` (53 of 53), so the quest seed is game-seed draw 4
  ([items/0010 § 1](0010-quest-drops.md#1-quest-objects-events-and-the-quest-seed)); (2) the values of the four
  worked examples of items/quest-drops (sessions 3344, 3311, 3315) are copied as test vectors into
  [items/0010 § Test vectors](0010-quest-drops.md#test-vectors-the-worked-examples-of-itemsquest-drops) and
  `tools/test_questdrops.py` (6 tests, OK, no game data needed); (3) the `QGS` lines of the 53 logs are 28
  `QUESTS_GetSeed` fetches (`0x0059664D` 2, `0x005966C0` 1, `0x005B6772` 5, `0x005B67BE` 10, `0x005B6807` 5,
  `0x005B68C7` 5), each the seed the model held.

### Addendum 2026-10-16: plan 0038 batch S2a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/tc_sweep.py logs` checks each log's sha256 against `quests-run-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2a-manifest.txt` (sha256 `850698f9…ba10e0`).
- Logs: the 53 session logs `quests-s3-*`, `quests-s4-*` of `quests-run.lst` (the load logs hold no resolver call).
- `python3 -I tools/tc_sweep.py replay`: `run:2026-10-16-quest-drops files=53 calls=2724 reproduced=2724 failed=0`,
  quality roll modelled (logged `QMF`); `tools/uniques.py check`: 1856 creations reproduced, 0 failed.
- Backs, with the other runs' logs: the plan 0038 S2a raises, among them 30 Normal and 5 Hell champions, three Duriel
  calls that the `MAX_DROP` stop ends with picks left, the `hellbovine` flag bit of the creation record (221 cow drops),
  7 rolls of kills credited to no unit, the first fallback steps (4 unique → rare) and the base-`unique` success with no
  row. The counts and checks per statement are in [items/0001 § Plan 0038 batch
  S2a](0001-tc-resolution.md#plan-0038-batch-s2a-2026-10-16) and [items/0002 § Plan 0038 batch
  S2a](0002-quality-roll.md#plan-0038-batch-s2a-2026-10-16).

### Owner-played addendum (same run id, 2026-10-16): result

- **State: owner-played.** The seven sessions of the proposed list above, played by the owner on 2026-10-16 on slot 0
  (display `:7`, `workspace/wineprefix`), fullscreen with sound, no steps, no *Save and Exit* (each session ended by
  the harness killing the game; one game per session, one `QI0` per log): `python3 -I tools/d2run.py --slot 0 --seed N
  --gdb tools/gdb/quests.gdb --after 3600 --sound --fullscreen --install o32 <save>`. Logger `tools/gdb/quests.gdb`
  (`9793f746…`) with `tools/gdb/quests.py` `e8a2a3e8…`, as from session 3344 on. Stock data, pinned `game.exe`, no
  forced path. Slot 0 instead of the proposed slot 4. Saves built with `python3 -I tools/d2s.py build
  workspace/merged/data/global/excel <recipe> workspace/samples/d2s-owner/smpsor-l50.d2s` (the hashes match the
  run's pins and each log's `installed` line); `QuestRewards` from the recipe at `32a1a6e`, the revision the run loaded.
- **Sessions** (logs `workspace/logs/quests-s0-<seed>-owner-<what>-<difficulty>.log`, list
  `workspace/logs/quests-owner-run.lst` `749bf34b…`, per-file sha256 in `workspace/logs/quests-owner-manifest.txt`
  `b163281a…`):

  | seed | save | difficulty | addendum item | reached |
  |---|---|---|---|---|
  | 3501 | QuestFreshV (`0a495ee7…`) | Normal | 1. Mephisto, quest done | killed; word 22 = `0x0001` |
  | 3502 | QuestFresh (`9a12da6e…`) | Normal | 2. the Countess, not done | killed (superunique 6, class 45); word 5 = 0 |
  | 3503 | QuestFreshV | Normal | 3. the Countess, done | killed; word 5 = `0x0001` |
  | 3504 | QuestB6 (`c28e894c…`) | Nightmare | 4. the Countess, not done | killed; word 5 = 0 |
  | 3505 | QuestRewards@32a1a6e (`7dfe9bc2…`) | Nightmare | 5. the Countess, done | killed; word 5 = `0x0001` |
  | 3506 | QuestCows (`6700b4e3…`) | Normal | 6. the Cow King | cube portal, 126 hell bovines and the Cow King (superunique 39) killed |
  | 3507 | QuestServices (`a9e32c29…`) | Hell | 7. the Hellforge in Hell | Hephasto (superunique 41) killed, soulstone placed, three strikes, four waves and the rune |

  Word values are the built saves' (`d2s.py questbits`) for the played difficulty, which the load leaves as they are
  (Step 1).
- **Procedure** (re-run by the reverser lane on the seven logs, `python3 -I`):
  ```
  python3 -I tools/questdrops.py check <log>
  python3 -I tools/tc.py replay --excel workspace/merged/data/global/excel <log>
  python3 -I tools/items_chain.py affixes --excel workspace/merged/data/global/excel <log>
  python3 -I tools/monpool.py check workspace/merged/data/global/excel <log>
  ```
- **Observed:**
  ```
  seed  questdrops (bit writes / scripted / mismatches)  tc.py replay       items_chain         monpool
  3501  30 / 0 / 0   B6 class 242 not taken 1             4/4 reproduced     17 reproduced, 0 f  309/309
  3502  13 / 0 / 0                                        14/14 (su 1)       52, 0 failed        844/844
  3503  29 / 0 / 0                                        9/9 (su 1)         74, 0 failed        993/993
  3504  14 / 0 / 0                                        22/22 (su 1)       61, 0 failed        821/821
  3505  34 / 0 / 0                                        14/14 (su 1)       68, 0 failed        702/702
  3506  39 / 8 vps (no draw) / 0                          127/127 (su 1)     52, 0 failed        507/507
  3507  36 / 6: forge 4 + rune 1 + hfh 1 / 0              31/31 (su 1)       31, 0 failed        561/561
  total 195 quest-bit writes, 14 scripted creations, 0 mismatches; 221 TC_ResolveDrops calls, 0 failed;
        355 creations, 0 failed; 4737/4737 monster levels
  ```
  - In all seven logs the `QI0` game seed is three LCG steps past `Init(N)` of `-seed N` (7 of 7, `tools/rng.py`
    `steps_between`): the quest seed is game-seed draw 4, as in the 53 run logs.
  - **Mephisto, quest done (3501).** `B60` class 242, `TCQuestId` 22, `TCQuestCP` 0, `tc` 848 (`Mephisto`), `tc4` 851
    (`Mephistoq`), killer the player `[0,1,1]`; `B6P` word 22 = 1; `GetState` 15 → 0, 1 → 0, `TCQuestCP` (0) → 1 →
    `B6X` tc 848, the `DROP` base. No `QDI` after the kill (no `mss`: the killer's word 22 bit 0 is set); his death
    wrote only the game-wide record (word 22 bit 13, already set).
  - **The Countess (3502–3505).** One kill each, class 45, superunique 6, killer the player. TC 1004 `Countess` in both
    Normal games (not done and done) and 1005 `Countess (N)` in both Nightmare games: the same TC whatever the quest
    state. No `B60` line in any of the four (class 45 has `TCQuestId` 0, so `MONSTER_DropItems` never reaches the
    quest-TC test) and no `QDI`/`QGS` (her scripts created nothing and fetched no quest seed). Drops (all reproduced):
    3502 `gld tsc vbt r06 r06`, 3503 `gld tri r05 r06`, 3504 `aqv r09 r02`, 3505 `hp5 2ax r11`; ilvl 11 Normal, 45
    Nightmare. Quest bits: in the two not-done games word 5 got bit 2 (return 0x005948E6) and bit 4 (0x00594920)
    before the kill, and **after** the drop's `TCEND` bit 13 (0x00594F57), bit 0 (0x00594F61) and a clear of bit 1
    (0x00594F6B), from the per-player code at 0x00594F2A–0x00594F6B (word 5 bit 0 clear and the player's level 25,
    the Tower Cellar Level 5); the game-wide record got bit 13. In the two done games no word-5 write at all.
  - **The Cow King (3506).** His own TC 986 `Cow King` (class 391, superunique 39) resolved first (`TCR`/`TCEND`,
    5 items, ilvl 31); then killer word 4 bit 10 set (return 0x00593EFB, word 4 was `0x0001`; word 40 bit 0 set, so he
    qualifies), the per-player code set it again (0x00593E63), and eight `QDI` with code `vps `, quality **0**
    requested, source the Cow King, return 0x00593F46, all on the same quest seed `1fad7e04:0000029a` (no draw). The
    eight `QDX` items are quality **2**, ilvl 31 (his level), flags `0x00082010`.
  - **The Hellforge in Hell (3507).** Hephasto (class 409, superunique 41, TC 877 `Haphesto (H)`) dropped his TC, then
    `hfh` quality 7 ilvl 88 without a draw. `FOP` mode 0 (the soulstone placed), then mode 2 with strikes 0, 1, 2: the
    third click wrote word 27 bits 13 and 1 (0x005B5D41, 0x005B5D4E; word 27 was `0x0004`). The hammer and the
    soulstone of `QuestServices` carry stat 356 = 2, equal to the Hell difficulty: both were found. Four waves on the
    quest seed `d050968a:0000029a` (unchanged since `QUESTS_InitGame`): `gpg` (perfect), `glr`, `glb` (flawless),
    `gsb` (standard), then `QGS` 0x005B68C7 with `880e6842:019ecdba` → one step → `c6662884:38bf7f40`,
    `0xc6662884 mod 11 = 4` → `r19`, the fifth entry of the Hell table `r15`…`r25`
    (data:g_ForgeRunesHell@0x0073E540; Normal's fifth would be `r05`, Nightmare's `r16`). All five quality 2, ilvl 85
    = `MonLvl3Ex` of level 107 (`Levels.txt`: 27 / 57 / 85 Ex).
- **Done-when coverage (the addendum list):** all seven items reached. Mephisto done: B6 not taken. The Countess in
  the four states: killed in each, same TC per difficulty. The Cow King's eight `vps`. The Hellforge in Hell: the
  waves and the rune from the third table.
- **Not covered by the addendum (stay as listed under Shortfalls):** a killer that has already been credited for the
  Cow King (word 4 bit 10) or has not finished Baal (and the classic word 26 test); the Countess in Hell; a classic
  game's forge (no rune); every item under *Not attempted*.
- **Conclusion:** the addendum reproduces with 0 mismatches over 7 owner-played sessions; the claims it raises are
  listed in [items/0010 § Phase 2](0010-quest-drops.md#owner-played-addendum-run2026-10-16-quest-drops-2026-10-16).
  Nothing in the seven logs contradicts items/0010 or items/quest-drops; one refinement: the Cow King's quality-0
  request comes out as a quality-2 item.

### Addendum 2026-10-16: plan 0038 batch S2b

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/items_sweep.py logs` checks each log's sha256 against `quests-run-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s2b-manifest.txt` (sha256 `870bc2ee…3f082f1`). The reports of the other subcommands are kept
  next to it (`sweep-s2b-{staff,cf,scan,tables,static}.txt`).
- Logs: the 53 session logs `quests-s3-*`, `quests-s4-*`.
- `tools/affixes.py check --staff model`: 1 856 creations reproduced, 0 failed; 27 staff-mods exit seeds predicted
  (`STFC` compared on all 27), 1 360 calls on types without `StaffMods`. `tools/items_sweep.py scan`: the two quest
  creations whose base `unique` turns quality 2 into 7 with the record's quality left at 2 (`j34`, `mss`), and the
  221 `hellbovine` creations (no set pick on a set-29 base among them).
- Backs, with the other runs' logs: the plan 0038 S2b raises. The counts and checks per statement are in
  [items/0004 § Plan 0038 batch S2b](0004-uniques-sets.md#plan-0038-batch-s2b-2026-10-16),
  [items/0005 § Plan 0038 batch S2b](0005-affixes.md#plan-0038-batch-s2b-2026-10-16) and
  [items/0006 § Plan 0038 batch S2b](0006-properties.md#plan-0038-batch-s2b-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of this run's kept logs and of its owner-played addendum; no new session. `python3 -I
  tools/sweep_s2c.py logs` checks each log's sha256 against `quests-run-manifest.txt` and `quests-owner-manifest.txt`
  (`workspace/logs/sweep-s2c-manifest.txt` (sha256 `5820525c…9280ba`)).
- Logs: the 53 session logs and the 7 owner-played ones. `python3 -I tools/sweep_s2c.py quests`: the 17 `GetState(…,
  15)` and `(…, 1)` results against the logged words, the 1 626 bit writes (bit 15 only on the game record, 913), the
  Mephisto kill's word 22 bits 13, 0, 11 and the staff placement's word 10 bits 0 and 13, the ilvl of the 25
  monster-sourced and 30 forge-sourced scripted creations, the `mss` creation, and the imbued item as the action's
  argument (17 of 17).
- Backs the plan 0038 S2c rulings in [items/0010 § Plan 0038 batch S2c](0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16), [items/0007 § Plan 0038 batch S2c](0007-sockets-runewords.md#plan-0038-batch-s2c-2026-10-16),
  [items/0005 § Plan 0038 batch S2c](0005-affixes.md#plan-0038-batch-s2c-2026-10-16) and [items/0004 § Plan 0038 batch S2c](0004-uniques-sets.md#plan-0038-batch-s2c-2026-10-16).

## run:2026-10-17-sweep-quest-b6

- **Question:** (plan 0038 Phase 2, batch H6d, [inventory § 5](../../plans/0038-inventory/README.md#5-batch-list))
  Does the quest-TC switch resolve a hireling's or a summon's kill to the owner and pass the unresolved killer on? Do
  Diablo's and Baal's kills order the drop before their scripts and give the quest TC by word state? Does Warriv's report
  clear bit 1 so that the quest TC comes back in a later game? Do Andariel's gems drop in Nightmare, Hell and classic, the
  Nightmare forge accept a stat-356-1 hammer, and Baal's first kill drop its gold as items/0010 reads it? Boundary as in
  run:2026-10-16-quest-drops: quest bits and per-player counts are inputs, and each scripted draw takes the quest seed it
  finds (`QGS`).
- **Setup:** agent-driven sessions on harness **slot 2** (display `:9`, `workspace/wineprefix-2`, game in
  `workspace/runtime/game`), one game at a time, the Xwayland window kept on `special:d2harness`, stock data, pinned
  `game.exe`, gdb by `tools/d2run.py`. All sessions ran on map seed 3811 (3815 once), because its Rogue Encampment
  waypoint is on the screen at the start. Driven by `tools/h6d_sessions.py run --slot 2 --tag h6d --saves <dir> --run
  quest-b6 <session>` (`3677d586…`). Per session it restores and sets aside the slot's empty saves directory (tag `h6d`),
  starts `d2run.py --seed 3811 --gdb tools/gdb/quests.gdb --steps tools/gdb/enter-<difficulty>.steps --after 2400
  --install h6d <save>`, plays the listed `tools/d2pilot.py` commands, and ends with `tools/slots.py stop 2`. Playing
  is `wpchain`, `farm --sweep --descend`, `hunt`, `objop`, `explore`, `npc warriv talk`, `insert` and a Save and Exit for
  the Warriv save. Pilot options `--nova-key F1 --es-key F2 --es 25 --radius 9 --mana-col 4 --drink 0.5 --nova-hold 1.6
  --max-res 1000`.
  - **Pilot additions** (`tools/d2pilot.py` `42bb44da…`; it decides where to click only, nothing feeds a model): `hunt
    --pet R` stands within R sub-tiles of the target and casts nothing, so the mercenary or a summon makes the kill;
    `--summon-key F3 --summon-every 3` places Hydra towards the target; `hunt --goal X,Y` gives the target's place on the
    map seed when the target is not seen yet; `objop --pdef-any` heads for preset rooms of any built level; the `warriv`
    NPC entry.
  - **Logger** `tools/gdb/quests.gdb` (`9793f746…`, unchanged) sourcing `pilot.py` (`1ad48a4c…`), `uniques.py`
    (`9b3e988f…`), `affixes.py` (`f2ac1c63…`), `vendors.py` (`eddbff8c…`), `mon-pool.py` (`2c17c655…`), `quests.py` and
    `tc-drops.gdb` (`842f8613…`). `quests.py` gained five lines (tags only; the run:2026-10-16-quest-drops lines are
    unchanged): `QME` 0x00543AB5, `MMR` 0x005A7D51, `BG0` 0x0058E02E, `BGR` 0x0058E061 and `GLD` 0x0055A1BD (sessions
    1–4: `cfcdf667…`), then `OOP` 0x0058450E for the pilot's object clicks (sessions 5–19: `7f07110b…`).
  - **Characters** (`tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/<recipe>.json <base>
    <out>`, base `smpsor-l50.d2s` `0913e5f0…`, the classic one on `smpsor.d2s` `b29ea52c…`): `QuestFreshT`
    (`questfresht.json` `697bbc82…`, save `09fd6ec4…`: `questfresh`'s quest bits and gear, all three difficulties open,
    Hydra 20 and Fire Mastery 20, hotkeys F1 Nova, F2 Energy Shield, F3 Hydra); `QuestFreshM` (`questfreshm.json`
    `c4dd3252…`, save `b1d80559…`: `QuestFreshT` plus a level-75 Rogue Scout, Hireling Id 0, with `lbb`, `brs`, `hlm`);
    `QuestBaalF` (`questbaalf.json` `3db0d034…`, save `4078ca7a…`: `quests: all` less word 40 bit 0); `QuestAllDone`
    (`questalldone.json` `2bba0337…`, save `501eb4a8…`); `QuestSvcOne` (`questservicesone.json` `1fc94e87…`, save
    `1f628a4a…`: `questservices` with stat 356 = 1 on the equipped hammer); `QuestFreshCT` (`questfreshct.json`
    `574460e7…`, save `84888ad5…`: `questfreshc` with Lightning Mastery and the hotkeys; status byte `0x00`, classic).
    Stat 356 on the hammer is a value the game itself gives a created quest item, written by the builder's
    `item_stats`; no test-state key, no table edit. The Warriv session's written save (Save and Exit in session 6) is
    `b50b68dd…`, `d2s.py questbits` against the built save: Normal word 0 bit 0, word 6 bits 0, 3, 4, 13. The six
    built saves and the written one are kept in `workspace/logs/h6d/saves/` (the written one under `written/`),
    manifest `workspace/logs/h6d/quest-b6-saves.sha256` (`0c2db76f…`; added at the review, 2026-10-17, from the lane's
    session scratch, hashes unchanged).

| # | Log (`workspace/logs/h6d/`) | Save, difficulty | What | Result |
|---|---|---|---|---|
| 1 | `failed/quest-b6-s2-3811-andy-warriv.log` | QuestFreshM, Normal | `farm --wp 1,9` | the default waypoint click missed; stopped |
| 2 | `quest-b6-s2-3811-andy-warriv.log` | QuestFreshM, Normal | Andariel (Nova), Town Portal, Warriv | kill (player, fresh); the portal clicked twice, so no report |
| 3 | `failed/quest-b6-s2-3815-andy-warriv.log` | QuestFreshM, Normal | the same, map seed 3815 | town waypoint off the screen; no play |
| 4 | `quest-b6-s2-3811-andy-warriv-r2.log` | QuestFreshM, Normal | the same | Andariel not found in Catacombs 4 |
| 5 | `quest-b6-s2-3811-andy-warriv-r3.log` | QuestFreshM, Normal | the same | kill (player, fresh) and Warriv's report; Save and Exit missed |
| 6 | `quest-b6-s2-3811-andy-warriv-r4.log` | QuestFreshM, Normal | Andariel (`hunt --pet 8`), report, Save and Exit | **kill by the mercenary**, report, written save |
| 7 | `failed/quest-b6-s2-3811-andy-reported.log` | session 6's save | — | the save was installed under the wrong file name; no character listed |
| 8 | `quest-b6-s2-3811-andy-reported.log` | session 6's save, Normal | Andariel (Hydra) | Catacombs descent failed |
| 9 | `quest-b6-s2-3811-andy-reported-r2.log` | session 6's save, Normal | Andariel (`--pet 8 --summon-key F3`) | **kill by a Hydra** on the reported word |
| 10 | `quest-b6-s2-3811-andy-nm.log` | QuestFreshT, Nightmare | Andariel (Nova) | kill, gems |
| 11 | `quest-b6-s2-3811-andy-hell.log` | QuestFreshT, Hell | Andariel (Nova) | kill, gems |
| 12 | `quest-b6-s2-3811-andy-classic.log` | QuestFreshCT, Normal (classic) | Andariel (Nova) | kill, gems |
| 13–15 | `quest-b6-s2-3811-forge-nm.log`, `-r2`, `-r3` | QuestSvcOne, Nightmare | River of Flame to the Hellforge | not reached (a lava edge near x 7765) |
| 16 | `quest-b6-s2-3811-baal-fresh.log` | QuestBaalF, Normal | Worldstone Keep 2 down | `--descend 87,88` named the .txt rows; the loaded records are 86/87 (the `Expansion` marker row is not loaded: [LvlWarp](../../tables/LvlWarp.md#row-identity), [excel-bin](../../formats/excel-bin.md)) |
| 17 | `quest-b6-s2-3811-baal-fresh-r2.log` | QuestBaalF, Normal | WSK 2 → 3 → Throne, five waves, the Chamber portal (563), Baal | **Baal killed, fresh**; gold |
| 18 | `quest-b6-s2-3811-baal-done.log` | QuestAllDone, Normal | the same | **Baal killed, done** |
| 19 | `quest-b6-s2-3811-diablo-fresh.log` | QuestFreshT, Normal | River of Flame → Chaos Sanctuary, seals, Diablo | Sanctuary reached, no seal operated (the runner was stopped and one manual `objop` tried, in the pilot record) |

- **Procedure:**
  ```
  python3 -I tools/sweep_h6d.py logs $(cat workspace/logs/h6d/quest-b6-run.lst)          # in workspace/logs/h6d
  python3 -I tools/questdrops.py check <the 19 logs>
  for l in <the 19 logs>; do python3 -I tools/tc.py replay $l; python3 -I tools/items_chain.py affixes $l; done
  python3 -I tools/monpool.py check workspace/merged/data/global/excel <the 19 logs>
  python3 -I tools/sweep_h6d.py static workspace/runtime/game/game.exe
  python3 -I tools/sweep_h6d.py copies workspace/logs/quests-s3-33{1,2,3}*-svc-*.log           # run:2026-10-16-quest-drops
  python3 -I tools/test_sweep_h6d.py
  ```
  The heavy replays ran under `systemd-run --user --scope -p MemoryMax=4G`.
- **Observed** (19 logs: list `workspace/logs/h6d/quest-b6-run.lst` `8484a63f…`, per-file sha256 in
  `workspace/logs/h6d/quest-b6-manifest.sha256` `aae6f6ac…`; reports `check-*.txt` beside them; checker
  `tools/sweep_h6d.py` `3a85c589…`, tests `tools/test_sweep_h6d.py` `c2d93ce4…`, 8 tests OK):
  ```
  sweep_h6d logs: B6 Andariel diff 0: killer player taken 3, hireling -> owner player taken 1,
                  summon -> owner player taken 1; diff 1 player taken 1; diff 2 player taken 1
                  Baal diff 0: player taken 1 (fresh), not taken 1 (bit 0 set)
                  order MMR (mode 0, 0x006E2260, start 0x005A6FF0) < B6X < QME: Andariel 7, Baal 2
                  Warriv: QC bit 1 (word 0x201a) 2, QS bit 0 (word 0x2018) 2
                  Andariel's gems gcr gcy gsb: expansion Normal 3, Nightmare 1, Hell 1, classic Normal 1
                  Baal gold: 1 loop (Normal, 1 player), 1 draw reproduced, 1 pile with stat 14 = 2178
                  0 bad
  questdrops: 18 quest seed starts, 332 quest-bit writes, 19 quest-seed fetches (19 predicted), 18 scripted draws
              reproduced (Andariel), 0 mismatches
  tc.py replay: 1322 TC_ResolveDrops calls reproduced (66 of them classic), 0 failed; B6 tied to the DROP base in all 9 kills
  items_chain.py affixes: 1153 creations reproduced, 0 failed
  monpool.py check: 8607/8607 match
  sweep_h6d static: MonModeRecord gives no class a special mode-0 record; ItemCreateFromOldRec's +0x2C store at
                    0x00530FDA, callers 0x0053105E, 0x0053139C; 0 bad
  sweep_h6d copies (run:2026-10-16-quest-drops, 17 service logs): LZ0 15 and PZ 15 with no IC0 after their MA
  ```
- **Shortfalls** (claims stay `[I]`): Diablo in both states (1 session: the Chaos Sanctuary was reached, the seals
  not operated); the Nightmare Hellforge with the stat-356-1 hammer (3 sessions, all stopped at the same lava edge); the
  `exp`-state killer (not attempted: it needs a Necromancer's Attract or Confuse, or a Paladin's Conversion, on a
  monster that then kills a quest boss). Session 19's runner was stopped after the scripted seal clicks failed. One manual
  `objop --obj-cls 394` was tried on the live game (logged in the pilot record) before the slot was stopped. (run:2026-10-17-sweep-quest-b6)
- **Owner-played addendum (proposed, same run id):** slot given by the architect, `tools/gdb/quests.gdb`, no steps,
  `--after 3600`, never *Save and Exit*:
  1. Diablo fresh (`QuestFreshT`, Normal): River of Flame waypoint, Chaos Sanctuary, the five seals, kill Diablo.
  2. Diablo done (`QuestAllDone`, Normal): the same.
  3. The Nightmare Hellforge (`QuestSvcOne`, Nightmare): River of Flame, the forge, one click with the soulstone,
     three strikes with the stat-356-1 hammer equipped.
- **Conclusion:** the owner resolution of a hireling's and a summon's kill (B6 and the death event), the unresolved
  killer in the TC walk, Warriv's report and the quest TC after it, Andariel's gems in four difficulty and game-type
  states, Baal's quest TC both ways, his death order and his gold reproduce with 0 mismatches over 19 sessions. The
  raised claims are in [items/0010 § Plan 0038 batch H6d](0010-quest-drops.md#plan-0038-batch-h6d-2026-10-17),
  [items/0001](0001-tc-resolution.md#plan-0038-batch-h6d-2026-10-17) and [items/0004](0004-uniques-sets.md#plan-0038-batch-h6d-2026-10-17).
- **Review re-run (architect, 2026-10-17):** `sha256sum -c` on the manifest, 19 of 19 OK. `sweep_h6d.py logs`
  (output byte-identical to `check-sweep_h6d.txt`), `sweep_h6d.py static` (identical to `check-static.txt`),
  `sweep_h6d.py copies` (LZ0 15, PZ 15, IMB0 17, no `IC0`) and `test_sweep_h6d.py` (8 tests OK) re-run. `questdrops.py
  check` on the 19 logs under `systemd-run --user --scope -p MemoryMax=4G`: 0 mismatches, report identical. `tc.py
  replay` on sessions 6, 9, 12, 17 and 18: 65, 73, 66, 147 and 142 calls, 0 failed, the same counts as `check-tc.txt`,
  each with its B6 test reproduced. The 19 report lines sum to 1 322 calls, the classic session's 66 included (the
  first draft read 1 322 + 66). `d2s.py questbits` on the kept written save against `QuestFreshM` gives word 0 bit 0
  and word 6 bits 0, 3, 4, 13, as above. objdump re-read `MonModeRecord` (0x005A78A0–0x005A79B0),
  `MonsterOwnerRef`, the death event's owner lookup, Warriv's two calls, Baal's gold loop, `DropGoldAmount`'s cap and
  `PlayerFindItemByCode`'s tests; fixes in the finding sections (review entry in the plan 0038 log).

## run:2026-10-17-economy

**Status: done** (plan 0043 Phase 2, harness lane `lane/p43h`; sessions 4311–4322 on 2026-10-17, the rest on
2026-10-18/19 after a rotation). 0 mismatches over every claim log; the shortfalls against the plan's *Done when* are
named under *Limits*.

- **Question:** plan 0043 Phase 2. Does `tools/economy.py`, the model of [items/0011](0011-economy.md) (the price
  core in modes 0–3 with the gamble path, `RepairCost`, `PayGold`, the gold adds, the gold amount at creation, gold
  find, death loss, resurrection, Cain, the wear draws and the quantity use), reproduce what the game computes at each
  logged event, and which event kinds move the game seed or the player's seed?
- **Setup:** agent-driven sessions on harness **slot 1** (display `:8`, prefix `workspace/wineprefix-1`), single player,
  pinned `game.exe` (stock data), `-seed` per session, one game at a time. Logger `tools/gdb/economy.gdb` =
  `tools/gdb/pilot.py`, `tools/gdb/vendors.py` and `tools/gdb/economy.py` (entry and exit of every economy function of
  items/0011, each line with the game seed, the player's seed, gold and stash; price payloads written once per
  distinct input, `k` an id); session 4334 used `tools/gdb/economy-hire.gdb` (the same plus `mon-pool.py` and
  `hirelings.py`). Logger versions: 4311 ran `tools/gdb/economy.py` of commit 5507e36; 4321–4334 that of b43ef61 (adds
  `ra2` and the control watchpoint `SWC`); 4335 and later that of df4659d, which fixes the watchpoint handler (`$eip`
  did not convert on this gdb, so every watch hit of 4311–4334 was lost as a `LOGERR economy watch` line, one per hit;
  no other line of those sessions is affected). Drivers: `tools/economy_sessions.py` (`tour`: waypoint hops and
  `tools/d2pilot.py npc … --stay`, then hover sweeps of the store grid, the inventory and the repair cursor, sales and
  purchases; `die`: optionally `npc qualres resurrect` in Harrogath, then waypoint 4,2 in Hell and walking
  `explore` until `PLAYER_DeathGoldLoss` returns, twice), `tools/d2pilot.py npc … hire --repeat N --buy 1`,
  `tools/d2pilot.py explore --any-level --walk --melee [--melee-button 3]` (wear), and `farm --sweep` then `explore
  --any-level` with Nova (gold). Characters built with `tools/d2s.py build` from `tools/d2s_recipes/econ*.json`; saves
  in `workspace/scratch-p43h/saves/`. Command lines (every session launched on slot 1 with the save installed, tag
  `p43h`): deaths `tools/economy_sessions.py --slot 1 die --seed S --save EconK<n>.d2s --resurrect 5:qualres --deaths 2`
  (the resurrection-only sessions `--deaths 0`); wear `tools/d2pilot.py explore <log> --slot 1 --any-level --hops 400
  --persist 20 --walk --melee [--melee-button 3] --radius 14 --give-up 40 --burst 6 --cast-wait 0.5`; gold
  `tools/d2pilot.py farm <log> --slot 1 --wp W --players P --time 40 --sweep --nova-key F1 --es-key F2 --es 30 --mana-col
  4 --mana-drink 0.3`, then `explore <log> --slot 1 --any-level --hops 600 --persist 20 --nova-key F1 --es-key F2 --es
  30` for 480–600 s (the loops that chained these were shell scripts in the lane's scratch). Pilot additions (`tools/d2pilot.py`, decide where to click only): the NPC
  entry `qualres` (Qual-Kehk's menu with a dead mercenary, measured: talk, resurrect, hire, cancel) and Tyrael's
  menu order (not exercised).
- **Sessions** (logs `workspace/logs/<name>.log`, sha256 in `workspace/logs/economy-run-manifest.txt`, itself sha256
  `addf7737…6c5ea1`, which also hashes the logger, checker, drivers and check outputs; every path is relative to the
  repository root, so `sha256sum -c workspace/logs/economy-run-manifest.txt` runs from there, 52 of 52 OK; the lane's
  version `ecfe97e0…ab2dbb` mixed two path bases and was normalised at the review):

  | name | save (recipe) | difficulty | what was played | status |
  |---|---|---|---|---|
  | `economy-s1-4311-normal` | EconA (`econa.json`, clvl 30, every quest done) | Normal | 20 stops: the trade windows of 14 NPCs, five gamble windows, Charsi's repair-all, three sales, a purchase, Kashya's hire list | run |
  | `economy-s1-4322-nova` | EconN (`econn.json`, Nova, no gold find) | Normal | `farm --sweep --wp 1,2 --players 8`, 45 s | short |
  | `economy-s1-4331-nightmare` | EconB (`econb.json`: set, socketed sword, rare and unidentified rings, crossbow, class shield) | Nightmare | Jamella trade and gamble, Halbu (repair cursor), Larzuk, Malah, Anya trade and gamble, Fara, Drognan, Elzix gamble, Lysander; 2 sales, 1 purchase (Ormus and Hratli were put in Act IV by mistake and not found) | run |
  | `economy-s1-4332-hell` | EconDL75 (`econdl75.json`: 40 one-cell rings, amulets, charms; clvl 75) | Hell | Jamella trade and 3 gamble windows, Halbu, Larzuk, Malah, Anya trade and 2 gamble windows, Fara, Elzix 2 gamble windows, Lysander; 40 sales, 13 purchases | run |
  | `economy-s1-4333-questoff` | EconC (`econc.json`: EconA's kind of items, quest words 4, 9, 17, 35, 41 bits 0–1 cleared) | Normal | 19 stops over the five towns (Charsi's menu did not open; Cain not found in Act IV); 1 sale | run |
  | `economy-s1-4334-hire` | EconA | Normal | Charsi trade, single-item repair clicks, repair-all, Akara; 10 hires at Kashya, 12 at Qual-Kehk | run |
  | `economy-s1-4335-watch` | EconA | Normal | Charsi trade, repair, repair-all (the watch set at its trade opening), Gheed, Kashya's list, Fara, Drognan | run (the watch control) |
  | `economy-s1-4351..4360-die-k1..k10` | EconK1..K10 (`econk1..10.json`: level, gold and stash vary, 5 hit points, a dead Act I mercenary) | Hell | resurrection at Qual-Kehk, then two deaths in the City of the Damned | run, 10 sessions |
  | `economy-s1-4373/4375/4377/4378-res-k3/k5/k7/k8` | EconK3, K5, K7, K8 | Hell | resurrection only (the four saves whose gold covers the cost) | run |
  | `economy-s1-4381-wear` | EconW (`econw.json`, Barbarian clvl 85, 7 armour slots minus the left hand) | Normal | walking melee out of the Pandemonium Fortress, 12 min | run |
  | `economy-s1-4382-throw` | EconT (`econt.json`, Barbarian, Throw on the right button, throwing axe of quantity 130) | Normal | walking `explore --melee --melee-button 3`, 10 min (the steps file missed the difficulty click; clicked by hand) | run |
  | `economy-s1-4391/4394/4398-gold-*` | EconG (gold find) / EconN / EconG | Normal | Nova farm and explore, Black Marsh / Dark Wood, `/players 8` | run |
  | `economy-s1-4392/4396-gold-nm*` | EconN / EconG | Nightmare | the same, Black Marsh | run |
  | `economy-s1-4393/4395/4397-gold-hell*` | EconG / EconG / EconN | Hell | the same; 4393 died after 17 hops (`/players 8`), 4395 at `/players 1`, 4397 at `/players 3` (Cold Plains) | run (4393 short) |
  | `economy-s1-4401-reduced` | EconG (Gheed's Fortune in the inventory: `item_reducedprices`) | Normal | Larzuk (repair cursor), Malah, Anya trade and gamble, Halbu, Jamella gamble | run |
  | `economy-s1-4403-cain` | EconC | Normal | Cain in Harrogath: paid identify; Larzuk | run |
  | `economy-dev1`, `economy-s1-4321-wear`, `economy-dev2-k1`, `economy-dev3-k1`, `economy-s1-4351-die-k1-dev1792348055`, `economy-dev4-4402-cain`, `economy-dev5-4341-die-k1` | | | development: the first sweeps; the Barbarian on Teleport hops (0 hits); the resurrect menu measured; two death attempts that stood still at the waypoint; a Cain session whose game closed after Larzuk; the first `die` attempt (resurrect menu wrong) | development logs, no claim |

- **Procedure:** `python3 -I tools/economy.py check workspace/merged/data/global/excel $(cat
  workspace/logs/economy/claim-logs.txt)` over the 33 claim logs (output `workspace/logs/economy/check-run.txt`, sha256
  `fd00d8d5…2abb3`); `python3 -I tools/hirelings.py check workspace/merged/data/global/excel
  workspace/logs/economy-s1-4334-hire.log` (`workspace/logs/economy/check-hire-4334.txt`). Unit tests
  `tools/test_economy.py` (9 tests). Checker additions in this run (commits df4659d, db75f28): the quest-group and
  `item_reducedprices` coverage, the resurrection's payment, the object piles' ilvl, Cain's payment, the armour pick
  compared with the item `ITEMS_DurabilityLossRoll` then rolls, and the wear chain kept within one log.
  - The first check of the death logs failed four resurrections (paid 0, cost 6 750 to 50 000): in each the gold and
    stash together were below the cost. Read again: `MERC_Resurrect` calls `PayGold` and returns at 0x00579CAE without
    reviving when it refuses (`PayGold` returns 0), which items/0011 had not stated; the checker now expects 0 then.
- **Observed** (trimmed from `check-run.txt`):
  ```
  logs 33; games 8
  price calls 26525; distinct inputs: mode 0 2513, mode 1 852, mode 2 272, mode 3 125 (3762)
    by difficulty (distinct): mode 0 1818/367/328, mode 1 552/79/221, mode 2 140/42/90, mode 3 108/17/0
    quality 1 316, 2 1048, 3 128, 4 2033, 5 66, 6 18, 7 153; socketed 10; charged 76; ethereal sales 68;
    unidentified 311; staff mods 326; player stat 87 > 0 376; quest group A on 1261 / off 2229, B on 764 / off 169
  repair-all sums 138; NpcRepair 2; ItemRepairAll 3115; PayGold 54
  sales checked (gold given = the lower price) 43 of 46; purchases checked (PayGold = price x count) 14 of 15
  hires 22 (PayGold); resurrections 14 (10 paid, 4 refused: gold short); resurrect costs 34; Cain 1 (100 for 1)
  death losses 20 (total above 500 L 12, below 8)
  gold amounts at creation 545; gold find scalings 433 (gold find 0 207, > 0 226); object piles (ilvl checked) 102
  wear rolls 1061 (armour chance 10 914, weapon 4 90, throwable 10 7; losses 81; armour broken 1; weapon to 0 1;
    no durability 50); melee wear events 1412; armour picks 964, all checked against the rolled item (W 18 802,
    W 10 162, W = 0 11); wear chained draw pairs 1878
  quantity uses 130; replenish ticks 287 (gaps 501 at r 5: 131, 834 at r 3: 76)
  seeds: PR 26525, RC 138, IR 3115, NR 2, PG 54, UG 97, MC 34 (player seed logged in 20), MR 14, CI 1, RP 287, IC 130, UA 142: game and player
         seed unchanged; NB 15: game seed +2; NS 46: game seed +2 in 41, +4 in 3, unchanged in 2; GG 46: +2 in 3;
         DA 10: +2; DG 20: +2 in 7, unchanged in 13; DL 1061: player seed +1 in 1011, unchanged in 50 (no
         durability); CD 1412: player seed +3 in 914, +2 in 50, +1 in 97, unchanged in 351
  economy: 0 mismatches
  hirelings (4334): hires 22; 41 MISMATCH lines, every one a "LOGERR economy watch" line of the broken handler, 0 others
  ```
  Gold amounts from monsters (the `GFK` lines, killer known) by difficulty: Normal 228, Nightmare 140, Hell 65.
- **Phase 1b required cases (backlog `2026-10-17-reverser-reverser-plan-0043-p2-contradicted-cases`):** (1) the armour
  slot weights: `COMBAT_DurabilityLoss`'s `W` (EBX at 0x0057D480) equals the sum of `g_ArmorWearSlots` weights 3/5/4/4/2/2/2
  over the occupied slots in all 975 events with the slot list logged (W 18 with six slots worn, W 10 with head, body
  and belt; the lead's 2/3/2/1/1/1 gives 10 and 6), and the slot picked from `RangeB(7)` and `RangeB(W)` is the slot
  whose item is rolled in 964 of 964 picks; (2)–(5) as before: ethereal sale `S / 4` (68 distinct mode-1 inputs of
  ethereal items now), the ethereal throwing stack 1 040, the all-resistance `S` over 1024, the computed gamble price.
- **Question 9 (`NpcStoreRec` readers):** in session 4335 the control watch on Charsi's record `+0x00` fired at
  0x00535EC3 (`NPCSTORE_FindRec`'s compare, the instruction after it) 40 times (the line cap) from 7 distinct call
  chains; the 4-byte watch on `+0x24..+0x27` fired once, at 0x005794A2: `NPC_TradeOpen`'s `cmp byte [edi+0x27], 0`
  (0x0057949E) on the trade opening that set the watch. No read of `+0x24..+0x26` over Charsi's trade, repair,
  repair-all, Gheed, Kashya, Fara and Drognan. Sessions 4401 and 4403 (watch set at a Harrogath trade opening) give
  the control 40 lines each and no `+0x24..+0x27` read. Review note (architect, 2026-10-19): in all three sessions the
  control's 40 lines fall within two frames of `SWSET` (4335 frames 1967–1968, 4401 1308–1309, 4403 1989–1990), so the
  absence of later reads is uncontrolled; only the `+0x27` read is raised. The single error line of 4311 (logger before the fix) is an
  unidentified hit, most likely the same opening's.
- **Limits** (against the plan's *Done when*):
  - prices: no crafted item (quality 8), ear or body part, Encode 4 stat term, version-0 item, recharge cost case; no
    Hell repair price (mode 3 difficulty 2); quest group C is set by no stock Npc row;
  - repairs: no quest repair, no partial repair (gold short), no ethereal or broken item at a repairer; single-item
    repair clicks gave `NpcRepair` 2;
  - gold: no Wirt's gold, no Baal's gold, no stash cap; no `GoldPickup` or stash move (pickup and stash UI not
    scripted); Hell monster gold 65;
  - wear: no classic throwable, no version-0 item, no stack refill (`q > 1` at `D′ < 1`); the weapon that reached 0
    had no broken flag at the roll's exit (one case). Review note (architect, 2026-10-19, plan 0043 Phase 3 review):
    the lane listed "no indestructible item", but all 50 of the "no durability" rolls are on two indestructible items
    of session 4381 (stat 152 = 1 in the full cache: a set `xtb`, 12 rolls, first at frame 791; a unique `uit`, 38),
    whose bases have `nodurability` 0 and `durability` 18 and 86; every roll without stat 152 drew. Counted from the
    `DL0`/`DL1` pairs of the 33 claim logs (seed unchanged = no draw), so the indestructible clause is met, not short.
    Also at that review: the stat-term and NPC-step large forms of `Scale` are separated by the run (a copy of
    `tools/economy.py` with the `0xFFFF` test made false at line 295, or at line 491, reports 2 737 or 1 846 mismatch
    lines on the same claim logs; the same edit at line 417, `AddTerm`, reports 0, so that form is not separated);
  - no charge use (`UseCharge`), no skill wear; no gamble at clvl 3 (EconDL3 not run);
  - Cain one case (paid; the free path not run).

## run:2026-10-19-economy2

**Status: done** (plan 0043 Phase 2b, harness lane `lane/p43b`, slot 1, 2026-10-19). 0 mismatches over the five claim
logs; shortfalls under *Limits*.

- **Question:** plan 0043 Phase 2b (backlog `2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder`): the quest
  repair (or its absence), Wirt's gold, crafted prices, the Hell repair price, the gamble at clvl 3, partial, broken and
  ethereal repairs, question 9 with a control live to the session's end, and the two P2 sales that left the game seed
  unchanged.
- **Setup:** agent-driven sessions on harness **slot 1** (display `:8`, `workspace/wineprefix-1`), single player, pinned
  `game.exe`, stock data, one game at a time, `-seed` per session. Logger `tools/gdb/economy2.gdb` = `pilot.py`,
  `vendors.py`, `quests.py` (the service lines `IMBX`/`LZY`/`PZ`, `OOP`, `QDI`/`QDX`) and `economy.py`, which adds for
  this phase `NSX` (the sale's store-copy decision), `WG0`/`WG1`/`WGS`/`WGN` (Wirt's gold), `DUL` (the ilvl
  `DropItemAtUnit` computes), item `id` and `ind` (stat 152), and the control watch `SWC` at most one line per 10 frames
  with no cap. Logger revisions: 4501 ran `tools/gdb/economy.py` of commit 02e65c3; 4503 and 4504 that of 2635d28
  (adds `ind`); 4505 and 4506 that of 55eebbc, which reads `ItemRepairBroken`'s item from the stack (the earlier
  revisions read EDX, the player: 4504's one `IB` line is on the player and is not used). Driver
  `tools/economy_sessions.py --watchdog 120,LIMIT` (each session in its own process group; abort on a log quiet 120 s,
  gdb's exit line or the limit, then `slots.py stop 1` and `saves.py restore`; it fired on gdb's exit line at the end
  of each session, after the session's own stop), every run under `timeout`. Characters built with `tools/d2s.py build`
  on `workspace/samples/d2s-owner/smpsor-l50.d2s` from `tools/d2s_recipes/econq.json` (EconQ: Normal, quest services
  pending, 300 gold, no stash, damaged and sale items), `econh.json` (EconH: Hell, clvl 75, tool-built crafted items with
  the new `crafted` key, a broken cap with the new `broken` key, an ethereal armour), `econdl3.json`, `econn.json`; tag
  `p43b`.
- **Sessions** (logs `workspace/logs/<name>.log`; manifest `workspace/logs/economy2-run-manifest.txt`, sha256
  `cb72ac21…31e6f9`, every path relative to the repository root, `sha256sum -c` 20 of 20 OK from there; it also hashes
  the check output, the scan output, the logger, checker, driver, scan and builder and the four recipes):

  | name | save | difficulty | what was played | status |
  |---|---|---|---|---|
  | `economy2-s1-4501-quest` | EconQ | Normal | Charsi trade (fix attempts, sales, repair-all, store), imbue; Gheed trade and gamble, Akara, Kashya's list; Larzuk trade, socket; Anya personalize; Malah; Charsi again | run (the `fix:` token clicked no confirm box yet: no single repair) |
  | `economy2-dev1-4502` | EconQ | Normal | the repair confirm box measured by hand (one paid, one partial repair) | development log, no claim |
  | `economy2-s1-4503-repair` | EconQ | Normal | Charsi: partial repair, ethereal fix, four sales (Annihilus, broken, plain, ethereal), partial again, cheap fix at gold 0, repair-all; Gheed, Akara, Kashya, Gheed gamble, Charsi again | run |
  | `economy2-s1-4504-hell` | EconH | Hell | Larzuk: hovers, broken and ethereal fixes, repair-all, four crafted sales, store; Malah, Anya, Halbu, Charsi | run |
  | `economy2-s1-4505-gamble3` | EconDL3 (clvl 3) | Normal | ten gamble windows: Gheed ×3, Anya ×3, Jamella ×2, Alkor ×2 | run |
  | `economy2-s1-4506-wirt` | EconN | Normal | Stony Field waypoint, the cairn stones (`objop --obj-cls 17 --to-pdef 160 --approach`), the Tristram portal (class 60), Wirt's body (`objop --obj-cls 268 --to-pdef 300 --done WG0`) | run |

  Command line (4501; the others alike with their stops): `timeout 3400 python3 -I tools/economy_sessions.py --watchdog
  120,3200 --slot 1 tour --tag p43b --seed 4501 --diff normal --gdb tools/gdb/economy2.gdb --log
  workspace/logs/economy2-s1-4501-quest.log --save workspace/scratch-p43b/saves/EconQ.d2s "1:charsi:trade:…" …`; 4506:
  `… wirt --tag p43b --seed 4506 --diff normal --log workspace/logs/economy2-s1-4506-wirt.log --save …/EconN.d2s`.
- **Procedure:** `python3 -I tools/economy.py check workspace/merged/data/global/excel $(cat
  workspace/logs/economy2/claim-logs.txt)` (output `workspace/logs/economy2/check-run.txt`, sha256 `4cb39d92…30b4`,
  checker of commit 7451f64); `python3 -I tools/economy_scan.py workspace/install/app/game.exe qrepair` (output
  `workspace/logs/economy-scan/economy-qrepair.out`). `tools/test_economy.py` 9 tests OK. The checker of this phase
  also re-reads Phase 2's 33 claim logs with 0 mismatches (its added store-stock restoration check was dropped to a
  count after 2 of 2 565 P2 stock items kept D < M with no stat 152 logged).
- **Observed** (summarised from `check-run.txt`, not verbatim; the exact lines are in the hashed output):
  ```
  logs 5; games 4
  price calls 7376; distinct: mode 0 542, mode 1 79, mode 2 153, mode 3 59
    quality 8 55 (mode 0 diff 2 3, mode 1 diff 2 35, mode 3 diff 2 17); mode 3 diff 2 25; gamble at clvl 3 125
  repair-all sums 193; NpcRepair one item 4 (partial taken 2, partial refused 1, paid (broken) 1); repair all 2
  ItemRepairAll from socket (quest) 1, personalize (quest) 1 (damaged, restored); imbue (quest) 1 (not identified,
    unchanged); restorations checked 10
  sales 11: copied, game seed +2 6; copy refused, +0: carry1 unique 1, flag 0x100 2, flag 0x400000 2
  Wirt gold events 18; pile counts 1; piles (ilvl checked) 18; gold amounts at creation 40
  seeds: PR 7376, RC 193, IR 894, NR 6, PG 8, GG 11, UG 15, RP 12, IB 1: game and player seed unchanged;
         NS 11: +2 in 6, same in 5; WG 18: game seed +2
  watch: SWW 5 hits, all at 0x005794A2; control SWC 66 lines, from the watch's setting to the last line of
         each log (4501 1207..12694, 4503 2275..7648, 4504 1313..9446, 4505 2729..7738;
         4505's watch set at 1769)
  economy: 0 mismatches
  ```
- **Limits:** the imbue's repair acts on an unidentified item and changes nothing (one case); one broken repair (its
  `ItemRepairBroken` line misread, the `ItemRepairAll` lines used); the ethereal refusal is client-side (no server call
  logged); crafted items tool-built (no recipe mods); one Wirt game (count 18; `MonLvl1` = `MonLvl1Ex` = 6 in Normal);
  question 9 covers only the windows listed in items/0011 § Phase 2b; the `Cracked` and `0x0055F590` copy refusals not
  reached.

## run:2026-10-20-sweep-items-tc

- **Question:** (plan 0038 Phase 2, batch H2a, [inventory § 5](../../plans/0038-inventory/README.md#5-batch-list))
  Which function chain makes a monster's death drop and a corpse skill's re-drop, and when is the death drop skipped?
  What do `mul=` and gold find do to a gold pile's stat 14, and does the item that reaches `max` get gold find? Does
  `/players` apply in a TCP/IP game hosted alone, and is an object source left uncapped? Does the negative-`Picks`
  stop fire on the classic Countess? Does a `noNoDrop` call leave NoDrop out of the range? And, over the kept stock
  logs and the new ones, does the quality roll's minimum (D6) act, and where? Boundary as in run:2026-10-11-tc-drops:
  the resolver is replayed from the source seed it starts with (`tools/tc.py replay`); item creation is the
  `tools/uniques.py` model.
- **Setup:** agent-driven sessions on harness **slot 2** (display `:9`, `workspace/wineprefix-2`, game in
  `workspace/runtime/game`), one game at a time, the Xwayland window kept on `special:d2harness`, stock data (no loose
  data file, no `-direct`), pinned `game.exe`, gdb by `tools/d2run.py`. Driven by `tools/h2a_sessions.py run --slot 2
  --tag h2a --saves workspace/logs/h2a/saves --run items-tc <session>` (final `c2cdec89…`; it reuses the session
  machinery of `tools/h6d_sessions.py` `3677d586…` with the logger changed). Per session it restores and sets aside
  the slot's empty saves directory (tag `h2a`), starts `d2run.py --seed N --gdb tools/gdb/tc-h2a.gdb --steps
  tools/gdb/<steps>.steps --after 1500 --install h2a <save>`, plays the listed `tools/d2pilot.py` commands and ends
  with `tools/slots.py stop 2`. Sessions were added to the driver between runs (additions only: `andy`, `andy-b`,
  `andy-c`, `countess-goal`, and the `hunt` step that ends `countess`, first used by session 8); each session's commands
  are in its `.pilot.txt` beside the log. Sorceress pilot options `--nova-key F1 --es-key F2 --es 25 --radius 9
  --mana-col 4 --drink 0.5 --nova-hold 1.6 --max-res 1000` (classic: `--wp-tab-x0 120 --wp-tab-w 78`).
  - **Pilot addition** (`tools/d2pilot.py` `f7e805d9…`; it decides where to click only, nothing feeds a model):
    `corpse`, a Barbarian's loop: War Cry (the right skill, F1, cast on the player like Nova) at what comes within
    `--radius`, Find Item (F2, Shift + right click on the corpse's cell, up to three offsets) on each MON corpse (mode
    12) within `--corpse-r`, walking (`--walk`) towards the nearest live monster within `--chase` sub-tiles otherwise.
  - **Logger** `tools/gdb/tc-h2a.gdb` (`39306661…`): the `tools/gdb/quests.gdb` chain (`pilot.py` `1ad48a4c…`,
    `uniques.py` `9b3e988f…`, `affixes.py` `f2ac1c63…`, `vendors.py` `eddbff8c…`, `mon-pool.py` `2c17c655…`,
    `quests.py` `7f07110b…`), the H2a lines, then `tc-drops.gdb` (`842f8613…`, unchanged). New lines (addresses read with objdump on the pinned image; the readings are in
    [items/0001 § Plan 0038 batch H2a](0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20)): `MDD0` 0x005A6830
    (return address, monster, class, `+0xC4`), `MDDB` 0x005A686D (the bit-17 test), `MDDC` 0x005A68A3 (the collision
    test), `MDDX` 0x005A68D1, `MDI` 0x005A6600 (return address, monster, `noNoDrop`), `MNN` 0x005A8000, `CFI`
    0x005D8780, `GTY` 0x0055AEFA, `GMUL` 0x0055AF21, `GMULX` 0x0055AF2F, `GMAX` 0x0055AF4F, `GF0`–`GF6`
    0x005589A0–0x00558A02. `tools/tc.py` skips these tags (additions only, `36892d1a…`).
  - **Steps:** `enter-normal.steps` (`96942bdc…`), `uniques-hell.steps` (`afb60595…`), and the new
    `h2a-tcpip-host.steps` (`54c76ede…`: `two-host.steps` plus the Normal click of the difficulty box, no joiner).
  - **Characters** (`tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/<recipe>.json <base>
    <out>`; kept in `workspace/logs/h2a/saves/`, manifest `items-tc-saves.sha256` `a973acf1…`): `UniqNova`
    (`uniqnova.json` `95c8be4e…` on `smpsor-l50.d2s`; save `2c793a3d…`, byte-identical to run:2026-10-14-uniques rev
    4; QMF 472, gold find 440 in GF2), `UniqClassic` (`uniqclassic.json` `0a6efe81…` on the classic `smpsor.d2s`;
    save `68e46a96…`, as in run:2026-10-14-affixes; status byte classic; gold find 355), and the new `FindBar`
    (`h2afind.json` `d8115721…`: `combatbar.json`'s Barbarian on `workspace/samples/d2s/smpbar.d2s` with War Cry 20
    and Find Item 20 on F1/F2; save `38f0fc57…`; gold find 80). No test-state key, no table edit.

| # | Log (`workspace/logs/h2a/`) | Save, game | What | Result |
|---|---|---|---|---|
| 1 | `items-tc-s2-3811-gold-normal.log` | UniqNova, Normal, `/players 8` | Cold Plains: Nova sweep 240 s, then 8 container clicks | 148 calls; 4 chests operated |
| 2 | `items-tc-s2-3821-eldritch-hell.log` | UniqNova, Hell, `/players 8` | Frigid Highlands, Eldritch's pack (`farm --wp 5,2`) | 35 calls |
| 3 | `items-tc-s2-3822-eldritch-hell-b.log` | the same | the same, map seed 3822 | 32 calls |
| 4 | `items-tc-s2-3823-eldritch-hell-c.log` | the same | the same, map seed 3823 | 31 calls |
| 5 | `items-tc-s2-3811-tcpip.log` | UniqNova, TCP/IP host alone, Normal, `/players 8` | as session 1 | 161 calls, `g6a` 2; no container reached |
| 6 | `items-tc-s2-3811-find.log` | FindBar, Normal | Cold Plains: War Cry, Find Item on 36 corpses (`corpse`, 420 s) | 64 calls, 12 Find Item drops |
| 7 | `items-tc-s2-3811-countess.log` | UniqClassic, classic Normal | Black Marsh → Tower Cellar Level 5, sweep | her room never activated |
| 8 | `items-tc-s2-3811-countess-r2.log` | the same | the same, then `hunt --mon-cls 45` | seen at 57 sub-tiles, not reached |
| 9 | `items-tc-s2-3811-andy.log` | UniqNova, Normal, `/players 8` | Andariel (`h6d_sessions.andariel("nova")`) | killed; quest TC (`Andarielq`, 833) |
| 10 | `items-tc-s2-3811-countess-goal.log` | UniqClassic, classic Normal | the route, then `hunt --goal 12517,11064 --hop 16` | **the Countess killed** |
| 11 | `items-tc-s2-3812-andy-b.log` | UniqNova, Normal, `/players 8` | Andariel, map seed 3812, `hunt` without a goal | killed; quest TC |
| 12 | `items-tc-s2-3813-andy-c.log` | the same | the same, map seed 3813 | killed; quest TC |

- **Procedure** (in `workspace/logs/h2a`; the S2a log set from `workspace/logs`):
  ```
  python3 -I tools/sweep_h2a.py logs $(cat items-tc-run.lst)                         # check/check-sweep_h2a.txt
  python3 -I tools/sweep_h2a.py static ../../runtime/game/game.exe                   # check/check-static.txt
  python3 -I tools/sweep_h2a.py clamp $(cat items-tc-run.lst)                        # check/check-clamp-h2a.txt
  python3 -I tools/sweep_h2a.py clamp <the S2a manifest's logs less tc-champion-1, tc-quality-1>   # check-clamp-s2a.txt
  python3 -I tools/sweep_h2a.py clamp --mf 100 tc-champion-1.log tc-quality-1.log    # check-clamp-s2a-mf100.txt
  python3 -I tools/sweep_h2a.py killers <the S2a logs> <the 19 H6d logs> <the 12 H2a logs>   # check-killers.txt
  for l in $(cat items-tc-run.lst); do python3 -I tools/tc.py replay $l; done        # check/tc-<log>.txt, check-tc.txt
  python3 -I tools/quality.py check $(cat items-tc-run.lst)                          # check/check-quality.txt
  python3 -I tools/uniques.py check $(cat items-tc-run.lst)                          # check/check-uniques.txt
  python3 -I tools/test_sweep_h2a.py                                                 # check/check-tests.txt
  ```
  The S2a log set is the 195 logs of `workspace/logs/sweep-s2a-manifest.txt` (`850698f9…`; 7 326 quality rolls
  in all, the two plan 0010 logs at their MF 100). The replays and the clamp scans ran under `systemd-run --user --scope
  -p MemoryMax=4G`.
- **Observed** (12 logs: list `items-tc-run.lst` `1d2d40c9…`, per-file sha256 in `items-tc-manifest.sha256`
  `94957d46…`, `sha256sum -c` from `workspace/logs/h2a`; checker `tools/sweep_h2a.py` `983ed539…`, tests
  `tools/test_sweep_h2a.py` `b361cae9…`, 9 tests OK; `tools/quality.py` `4837f4f8…` with the H2a counterfactual keys;
  reports in `check/`, sha256 `check-sweep_h2a.txt` `7ea37c28…`, `check-static.txt` `d1bc1830…`, `check-clamp-h2a.txt`
  `1c8c2ffb…`, `check-clamp-s2a.txt` `2bd668e1…`, `check-clamp-s2a-mf100.txt` `eb92745d…`, `check-killers.txt`
  `f41476c9…`, `check-tc.txt` `0e6017ab…`, `check-quality.txt` `5c2de726…`, `check-uniques.txt` `9fe300cc…`). From
  `check-sweep_h2a.txt` (lines abridged; the `MDD0 ret` and per-type lines left out):
  ```
  MDD0 973 (ret 005a702c 973): bit 17 skipped 113 (fallen1 79, fallen4 34), collision skipped 2, MDDX 858
  MDI ret 005a68d6 858 (nonodrop 0), ret 005a801c 12 (nonodrop 1); DROP 870
  CFI 31: CFI -> MNN 12, CFI without MNN 19; nonodrop calls 12, range = total (nd' 100 not added) 12
  PLAYERS g6a=2 pover=8 players=8 159; g6a=3 pover=8 players=8 376; g6a=3 pover=0 players=1 319
  object calls 4: no CAP line, NDIN n=4 16
  NEG pick 63, NEG stop (roll >= total) 1
  created units 713: gold 207; mul= products 1 (word 1280); gold find products 202 (factors 540 162, 455 37, 180 3)
    gold find skipped: own type not 4 489, no killer 14; max reached (count 6) 8, none followed by GF0
  0 bad
  ```
  ```
  check-static: MonDeathDrop: call 0x005A7027; DropItems: calls 0x005A68D1, 0x005A8017; MonDropNoNoDrop: call
                0x005D888F; CorpseFindItem: no rel32, absolute 0x007323D0 (.data); MonDeathEvent: absolute 0x006E2260
                (.rdata); DropGoldFind: call 0x0055AF59; the seven instruction patterns ok
  clamp (H2a logs): 720 rolls reproduced; the clamp acts in 39; without it 9 break, after the ratio word 7 break
  clamp (S2a set): 6479 + 847 rolls reproduced; the clamp acts in 628 (0 in the two MF-100 logs); without it 129 break,
                   after the ratio word 199 break
  killers: ktype 1 kclass 363 / 352 / 271 with QOWN the player: 85 / 6 / 39 rolls, mf = kmf + omf in all;
           killer none 89; no killer type other than 0 and 1 in 8 753 rolls
  tc.py replay: 873 calls, 873 reproduced, 0 failed (109 classic); B6 reproduced in the three Andariel kills
  quality.py check: 720 pairs, 720 reproduced, 0 failed
  uniques.py check: 1022 creations reproduced, 0 failed
  ```
- **Shortfalls** (claims stay `[I]`; run:2026-10-20-sweep-items-tc): `mul=` reached once (the Countess's `Countess Item` gold; no champion was killed,
  and the three Andariel kills took her quest TC, whose gold has no `mul=`); `bonewall`'s fatal error (class 344 never
  died); a monster-killer owner missing or gone, and a killer of type 2 or more (no case in 8 753 rolls); game type 1
  and the types outside 1–3. Sessions 7 and 8 are kept in the record: their calls replay with 0 failures and are in
  the counts above.
- **Conclusion:** the death-drop chain and its two skips, the Find Item re-drop with `noNoDrop`, `GOLD_TYPE`, the
  gold-find product and its skip at `max`, `/players` in a TCP/IP game, the uncapped object source, the classic
  Countess's negative-`Picks` stop and the quality roll's minimum with its place reproduce with 0 mismatches over 12
  sessions and the kept S2a set. The per-row ledger (raised, raised in part, shortfall) is in
  [items/0001 § Plan 0038 batch H2a](0001-tc-resolution.md#plan-0038-batch-h2a-2026-10-20) and
  [items/0002 § Plan 0038 batch H2a](0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20).
- **Addendum 2026-10-20 (write-up, static; no session).** Three further checks, outputs in `workspace/logs/h2a/check/`:
  ```
  python3 -I tools/sweep_h2a.py clamp $(cat items-tc-run.lst)                 # check-clamp-h2a-r2.txt       37b8e962…
  python3 -I tools/sweep_h2a.py clamp <the 193 S2a logs>                     # check-clamp-s2a-r2.txt       f82f2e6a…
  python3 -I tools/sweep_h2a.py clamp --mf 100 tc-champion-1.log tc-quality-1.log   # check-clamp-s2a-mf100-r2.txt fec4a734…
  for l in <the 193 S2a logs>; do echo "## $l"; python3 -I tools/sweep_h2a.py clamp $l | grep -E 'acting|no D6'; done
                                                                             # check-clamp-s2a-perlog.txt   b6fa1eaa…
  python3 -I tools/sweep_h2a.py goldtypes                                    # check-goldtypes.txt          0afea2e6…
  python3 -I tools/quality.py check $(cat items-tc-run.lst)                  # check-quality-r2.txt         5c2de726…
  python3 -I tools/test_sweep_h2a.py                                         # check-tests-r2.txt           67cfe670…, 9 tests OK
  ```
  `tools/quality.py` `ed525200…` adds the counterfactual key `{"clamp": "before-mf"}` (D6 before magic find; additions
  only, the game's roll unchanged: `check-quality-r2.txt` equals `check-quality.txt`); `tools/sweep_h2a.py` `9e3785ca…`
  adds it to `clamp` and adds the `goldtypes` full-table check (additions only; the per-log split ran on `983ed539…`).
  Results: the earlier two counterfactual counts are unchanged; D6 before magic find breaks 9 (H2a) + 129 (S2a) rolls
  and 0 of the MF-100 rolls; per log, the clamp acts in run:2026-10-14-affixes (479), run:2026-10-14-uniques (66),
  run:2026-10-14-props (43) and run:2026-10-15-items-chain (40), in none of the plan 0010, objects and quest-drop logs;
  `goldtypes`: of 659 item records only `gld` is of itemtypes record 4 by its type, `type2` or their `Equiv` ancestors.
  The replays and scans ran under `systemd-run --user --scope -p MemoryMax=4G`.
