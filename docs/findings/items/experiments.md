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
  [d2s.md](../../formats/d2s.md), so no save was edited for it).
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
