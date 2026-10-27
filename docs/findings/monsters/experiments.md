# Monster experiments

## run:2026-10-12-mon-pool

- **Question:** (plan 0012 Phase 2) Does the model of [monsters/0001](0001-level-pool.md) predict, from the `-seed N`
  value and the difficulty alone, every level's monster region built at game creation? That means its entries
  (class, rarity), appearance sets, copied Levels fields and the region seed after each level, plus the game-seed draw
  that seeds it. Does it also predict the monster level of the monsters created and the client critter draws?
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7`), wine 11.17,
  GNU gdb 17.2. Logger `tools/gdb/mon-pool.gdb`, which sources `tools/gdb/mon-pool.py`. Model and checker `tools/monpool.py`,
  which reads `levels.bin`, `monstats.bin` and `monstats2.bin` from `workspace/merged/data/global/excel` (the tree of
  the MPQs the harness game loads). Save: the harness character `seedtest`, a fresh expansion Barbarian stub
  (sha256 `cabccb01…`), normal difficulty only, left in place. The saves directory was hashed before the runs and
  restored after them: the game had rewritten `seedtest.ma0` and `seedtest.map` (automap), and both were copied back
  from the pre-run copy. All seven `seedtest.*` sha256 matched the pre-run list afterwards. No walking, no waypoint.
- **Logged** (one JSON line per event, header of `tools/gdb/mon-pool.py`): MPS `0x00547D63` (game seed after its
  step, the low word, difficulty, expansion, game type, `+0x74`, caller, monstats records 722/723); MPR `0x00547B1A` (one
  per level: the whole region as built, and `R` after it); MLV `0x00573E56` (class, chosen level, difficulty index,
  level id); CR0/CRC/CRX `0x0046C460`/`0x0046C548`/`0x0046C56B` (client critters: room seed in, each creation's class
  and seed, seed out).
- **Procedure:**
  1. Before each run `pgrep -af tools/d2run.py` and `pgrep -x game.exe` were empty (a wrapper script waited for both).
  2. `python3 -I tools/d2run.py --seed N --gdb tools/gdb/mon-pool.gdb --steps tools/gdb/enter-sp.steps --after 8 [--game-args "-act A"] --log workspace/logs/monpool-….log`,
     with `MONPOOL_FORCE_DIFF=D` in the environment for every run but the first.
     | log | N | difficulty | act | logger version |
     |---|---|---|---|---|
     | `monpool-1-normal.log` | 1 | normal (natural) | 1 | MPS/MPR/MLV only |
     | `monpool-1-d1.log` | 1 | nightmare (forced) | 1 | + forced field |
     | `monpool-1-d2.log` | 1 | hell (forced) | 1 | + forced field |
     | `monpool-2-d0.log` | 2 | normal (byte rewritten to 0) | 1 | + forced field |
     | `monpool-2-d2.log` | 2 | hell (forced) | 1 | + forced field |
     | `monpool-3-d0-a1.log` … `monpool-5-d0-a5.log` | 3, 3, 4, 4, 5 | normal (rewritten to 0) | 1, 2, 3, 4, 5 | final (+ critters) |
  - **Intervention (ADR-0003, it changes game state):** with `MONPOOL_FORCE_DIFF=D`, the MPS breakpoint at `0x00547D63`
    writes D into the game's difficulty byte `game+0x6D` before the region build reads it at `0x00547D66`. In
    `monpool-1-d1`, `monpool-1-d2` and `monpool-2-d2` this turns a normal game into a nightmare/hell build; in the other
    runs it rewrites 0 over 0. The pool reads difficulty only at that point, so the nightmare/hell region claims rest on
    the forced byte; a natural nightmare/hell game is a required case of the rest of Phase 2.
  3. Check: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-[1-5]-*.log` (the ten logs of this run; the glob leaves out the `monpool-p2-*` logs of [run:2026-10-12-mon-pool-p2](#run2026-10-12-mon-pool-p2)).
- **Observed:**
  ```
  all ten MPS: game-seed draw = 1 from Init(N), exp=1, gtype=3, caller 0x00530DCF; monstats 722/723 = monstats.bin
  MPR 1360 (136 levels x 10 games), MLV 47, CR0/CRX 130 rooms (critters in 12: Act I chicken, Act II bug), CRC 36
  per game: candidates > picks in 85 (normal) / 104 (nightmare, hell) levels; empty pools 11 (the 10 NumMon-0
    levels and Mountain Top, isSpawn 0); 20 rangedspawn levels built; 6-10 regions with a class twice;
    359 (normal) / 369 (nightmare, hell) entries, 670-709 appearance sets; class 723 in level 135 in every game
  monpool: 1557/1557 match
  ```
  No LOGERR line in the final logs. Development runs of the critter logger (`-act 1..5` logs written before two fixes
  to it) were overwritten by the reruns above and are not part of the record.
- **Raw logs:** `workspace/logs/monpool-1-normal.log` (sha256 `d4cf9a8f…3b3d`), `monpool-1-d1.log` (`eb514885…1360`),
  `monpool-1-d2.log` (`2036a0a6…5f1d`), `monpool-2-d0.log` (`fc6b83a0…2337`), `monpool-2-d2.log` (`e7518763…8cde`),
  `monpool-3-d0-a1.log` (`fc830d30…1a84`), `monpool-3-d0-a2.log` (`8a52c22f…4598`), `monpool-4-d0-a3.log` (`aaed7338…50fe`),
  `monpool-4-d0-a4.log` (`8c811ac4…0fa4`), `monpool-5-d0-a5.log` (`b28a526c…d869`).
- **Deviations and limits:**
  - **Nightmare and hell are forced.** The only character the session could use plays normal. The logger writes the
    difficulty byte `game+0x6D` at `0x00547D63`, before `0x00547D66` reads it, so the region build runs the
    nightmare/hell branch on a game object that is otherwise a normal one. The pool code reads nothing else that
    depends on difficulty (the build's `sub_00611D30_DifficultyRec` check passed). The forced games did not continue into the world,
    so the monster level and critters were logged only in normal games. A save swap that would have loaded a
    nightmare/hell character was refused by the session's permission checks.
  - **No classic game.** All ten games are expansion games (`+0x70` = 1).
  - **Monster level** (fn:sub_00573CB0_MonStatsInit@0x00573CB0): the 47 MLV lines are town NPCs created in normal games (no hireling among them), and all take MonStats `Level`.
    They don't separate MonStats `Level` from `MonLvl1Ex` of the towns (both 0), and the expansion nightmare/hell branch
    was not reached. The claim stays `[I]`.
  - **Critters:** `sub_0046C1A0_ClientCritterCreate` draws from the room seed (several draws per critter), which the model
    doesn't cover. Critter rooms are checked up to their first creation (seed, first slot's class and count).
    Rooms without critters are checked to their seed after.
- **Conclusion** (fn:sub_005479C0_MonRegionsBuild@0x005479C0): the pool build, the variant rolls, the region fields and the game-seed draw that seeds them are
  reproduced bit-exactly in ten games (normal over five seeds, nightmare over one, hell over two), every act,
  with no oracle on the pool side. In-scope claims of monsters/0001 sections 1–4, 7 and 8 go to `[C]`. The monster-level rule
  (section 5) and the classic branch stay `[I]`.

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- Logs: the ten `monpool-[1-5]-*.log` above.
- `python3 -I tools/mon_sweep.py pool` (with the seven logs of run:2026-10-12-mon-pool-p2): `tools/monpool.py check` with a
  counting copy of the variant roll, `monpool: 3040/3040 match`; entries by MonStats2 `+0x025` and sets: 0 → 1 set (3360), 1 →
  2 sets (220), 2–15 → 3 (1340), ≥ 16 → 3 (1273); duplicate tests meeting two existing sets 1, tests leaving `tries`
  below 0 0; the counterfactual `tries ≤ 0` stop also gives 3040/3040.
- Backs the plan 0038 S3a raises of pool 10 and the reclassification of pool 27, in
  [monsters/0001 § Plan 0038 batch S3a](0001-level-pool.md#plan-0038-batch-s3a-2026-10-16).


## run:2026-10-12-mon-pool-p2

- **Question:** (plan 0012 Phase 2, rest) Without forcing the difficulty, does `tools/monpool.py` reproduce the
  regions of a natural nightmare and a natural hell game, and of classic (non-expansion) games? Does the monster
  level of monsters created **outside town** follow the rule of [monsters/0001 §5](0001-level-pool.md#5-the-monster-level-sub_00573cb0_monstatsinit):
  `MonLvlEx` in expansion nightmare/hell, MonStats `Level*` in classic games and in normal, and the hireling and
  `noRatio` exceptions?
- **Setup:** as [run:2026-10-12-mon-pool](#run2026-10-12-mon-pool): the ADR-0003 harness (`workspace/runtime/game/`,
  prefix `workspace/wineprefix`, display `:7`), wine 11.17, GNU gdb 17.2, the unchanged logger `tools/gdb/mon-pool.gdb`
  (+ `mon-pool.py`), model and checker `tools/monpool.py` on `workspace/merged/data/global/excel`. `-seed 1` in every
  game. `MONPOOL_FORCE_DIFF` was **not** set in any run (every MPS line logs `"forced":null`). No memory write.
  - **Test characters** (built on copies, never on the samples): `python3 -I tools/monpool_saves.py <dir>` writes
    `expnm/smpsor.d2s` (expansion Sorceress from `samples/d2s-owner/smpsor-l50.d2s`, level 50, Act I waypoints
    0, 2, 6, 8 in every difficulty, header `progression` 5, difficulty bytes `00 80 00`), `exphell/smpsor.d2s`
    (progression 10, `00 00 80`), `exphellmerc/smpsor.d2s` (exphell plus a mercenary in the header: seed 12345,
    hireling id 4 = Rogue Scout *Fire - Hell*, class 271, experience 500000, an empty mercenary item list),
    `cls/smpsor.d2s` (exphell made classic: status bit 5 cleared, the `jf`/`kf` trailer removed, progression 8) and
    `nec/smpnec.d2s` (Necromancer from `samples/d2s/smpnec.d2s`, Hell waypoints 0, 2, 6, 8, Clay Golem at level 1
    on the right button, progression 10). `tools/d2s.py survey` reads all five cleanly. sha256 (first 16 hex):
    expnm `738e5912363bfba7`, exphell `4beb9d411d211931`, exphellmerc `1211b76aa0c3763f`, cls `b29ea52c72d3bd47`,
    nec `0d7201b41225dc4f`.
  - **Saves directory:** only through `tools/saves.py` (owner-approved): `aside p2` before the first run,
    `install p2 <file>` before each run (with `restore p2` + `aside p2` between characters), `restore p2` at the end;
    the final `status` shows the seven `seedtest.*` files (seedtest.d2s `cabccb01…`) and no open aside.
- **Logged:** the MPS, MPR, MLV and CR0/CRC/CRX lines of run:2026-10-12-mon-pool (header of `tools/gdb/mon-pool.py`).
- **Procedure:**
  1. Before each run `pgrep -f 'tools/d2run[.]py'` was empty; after each, the same check (and `wineserver -k`
     for the one interactive run).
  2. `python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/mon-pool.gdb --steps <steps> --after 10 --log workspace/logs/<log>`
     with the character installed:
     | log | character | steps | game | where monsters were created |
     |---|---|---|---|---|
     | `monpool-p2-1-hell-merc-town.log` | exphellmerc | `monpool-hell-town.steps` | expansion hell | Rogue Encampment; the mercenary |
     | `monpool-p2-2-hell-jail.log` | exphell | `monpool-hell-jail.steps` | expansion hell | camp, Jail Level 1 (waypoint) |
     | `monpool-p2-3-nm-jail.log` | expnm | `monpool-nightmare-jail.steps` | expansion nightmare | camp, Jail Level 1 |
     | `monpool-p2-4-classic-hell-jail.log` | cls | `monpool-hell-jail.steps` | classic hell | camp, Jail Level 1 |
     | `monpool-p2-5-classic-nm-jail.log` | cls | `monpool-nightmare-jail.steps` | classic nightmare | camp, Jail Level 1 |
     | `monpool-p2-6-hell-jail-golem.log` | nec | `monpool-hell-route.steps`, `--after 600`, then by hand | expansion hell | camp, Jail Level 1, a Clay Golem |
     | `monpool-p2-7-normal-stony.log` | exphell | `monpool-normal-stony.steps` | expansion normal | camp, Stony Field (waypoint) |
     The steps pick the difficulty in the *Select Difficulty* box (Normal 400,280 / Nightmare 400,323 / Hell 400,366),
     walk the camp route of `d2s-wp-open.steps`, which for these saves ends with the waypoint at the left edge, click
     the pad (15,182) and a row of the Act I tab. Walking is the only way out of town; no other movement.
  3. Run 6: with the Necromancer the route drifted (a first attempt missed the pad and was discarded, its log deleted).
     The run that counts played `monpool-hell-route.steps` (from a scratch copy, so the log header names that path)
     and was then driven by hand through `tools/xdrive.py --display :7 --window "Diablo II"`: `key Tab` (automap),
     `click 280 70`, `click 680 65` (the pad), `click 200 348` (Jail Level 1), `rclick 470 300` (Clay Golem), then
     `wineserver -k`. Screenshots `monpool-p2-6-{town,automap,wpmenu,golem}.png`.
  4. Two exploratory runs (hell, the first route attempt, and an interactive look at the hell camp) logged only the
     camp; their logs were deleted and are not part of the record.
  5. Check: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-p2-*.log`.
- **Observed:**
  ```
  seven MPS: game-seed draw = 1 from Init(1), forced=None, caller 0x00530DCF, gtype 3
    diff/exp: 2/1, 2/1, 1/1, 2/0, 1/0, 2/1, 0/1
  MPR 952 (136 x 7), MLV 162, critter rooms 355
  monpool: 1483/1483 match
  monster levels outside town (class: logged level; MonStats Level[d]; area MonLvlEx[d]):
    exp hell  Jail 1 (29):  384 x7: 71; 70; 71   57 x2: 71; 70; 71   39 x2: 71; 71; 71
    exp nm    Jail 1:       384 x7: 41; 40; 41   57 x2: 41; 40; 41   39 x2: 41; 41; 41
    cls hell  Jail 1:       384 x7: 70; 70; 71   57 x2: 70; 70; 71   39 x2: 71; 71; 71
    cls nm    Jail 1:       384 x7: 40; 40; 41   57 x2: 40; 40; 41   39 x2: 41; 41; 41
    exp normal Stony Field (4): 6 x14: 2; 2; MonLvl1Ex 4   160 x2: 4; 4; 4
    exp hell  hireling 271 (the mercenary, no room): level 1, d = 0 (MonStats Level; Level(H) is 67)
    exp hell  Jail 1, 289 claygolem (noRatio): level 0, d = 2 (MonStats Level(H) blank = 0; MonLvlEx 71)
  town NPCs (acts I, every game): level 0 (MonStats Level* and the camp's MonLvl*Ex are both 0)
  regions: natural nightmare (p2-3) = forced nightmare (monpool-1-d1) and natural hell (p2-2) = forced hell
    (monpool-1-d2), entry for entry and seed after for seed after, all 136 levels; classic = expansion regions
    (same seed and difficulty) except the copied monLvl fields (classic MonLvl vs MonLvlEx), which the check predicts
  ```
  No LOGERR line. 61 of the creations separate the two sources of the level (MonStats `Level*` vs the area level):
  9 in each of the five Jail games (seven 384, two 57; run 6 has the same nine), 14 class 6 in Stony Field, the
  mercenary and the golem.
- **Raw logs:** `workspace/logs/monpool-p2-1-hell-merc-town.log` (sha256 `a5a6231f…892f`), `monpool-p2-2-hell-jail.log`
  (`6f1986fd…f071`), `monpool-p2-3-nm-jail.log` (`0c4eeac1…1cb3`), `monpool-p2-4-classic-hell-jail.log` (`84d7492a…6144`),
  `monpool-p2-5-classic-nm-jail.log` (`434bb32b…6269`), `monpool-p2-6-hell-jail-golem.log` (`30342d58…2abb`),
  `monpool-p2-7-normal-stony.log` (`f853b6df…07d8`); arrival screenshots `monpool-p2-{2,3,4,5,7}-arrive.png`.
- **Deviations and limits:**
  - One seed (1) and Act I only for the nightmare/hell and classic regions; the forced runs of run:2026-10-12-mon-pool
    cover seed 2 hell. The natural regions match the forced ones exactly for seed 1.
  - No classic **normal** game. No `boss` class was created (act bosses need play). Hirelings: only class 271, in an
    expansion hell game. `noRatio`: only `claygolem`, in an expansion hell game.
  - The test saves are header edits (ADR-0003 input, not a memory write): the game accepted them (difficulty box,
    the waypoint menus, the mercenary shown at level 15 on its screen). The region build and the monster level read the game's difficulty
    and expansion flags, which every MPS/MLV line logs, not the save.
- **Conclusion:** [monsters/0001](0001-level-pool.md): the column set per difficulty and the region build are
  reproduced in natural nightmare and hell games and in classic nightmare and hell games; the monster-level rule
  (§5) goes to `[C]` for the cases logged here (expansion normal, nightmare, hell; classic nightmare, hell; hireling;
  `noRatio`); `boss` and classic normal stay `[I]` (fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_005479C0_MonRegionsBuild@0x005479C0).

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- Logs: the seven `monpool-p2-*.log` above, read with those of run:2026-10-12-mon-pool by `python3 -I tools/mon_sweep.py
  pool` (the counts are in that record's addendum).
- Backs pool 10 and pool 27 of [monsters/0001 § Plan 0038 batch S3a](0001-level-pool.md#plan-0038-batch-s3a-2026-10-16).


## run:2026-10-13-mon-spawn

- **Question:** (plan 0014 Phase 2) Does the model of [monsters/0002](0002-room-population.md) reproduce, bit for bit,
  the random population of every room the server activates (gate, attempts, density, class picks and the `spawn`
  substitution, the type roll, groups, specials, minions, every position and every draw on the room, game and unit
  seeds), with the active-room seed **predicted from the `-seed` value** rather than read from the log? It also covers
  the Phase 1b required cases: `MonUMax` (the type-roll draws), the live special count `+0x2C8` across a champion pack,
  and every access to `MonWndr` (fix F5).
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7` moved to a
  visible workspace for the owner), wine 11.17, GNU gdb 17.2. Logger `tools/gdb/mon-spawn.gdb` (sha256 `d2a05950…e3b55284`),
  which sources `tools/gdb/drlg-gen.py` (`91feac40…5c970580`), `tools/gdb/drlg-roomk.py` (`d6b2e6e0…6340ce5be`) and
  `tools/gdb/mon-spawn.py` (`6ad436e8…a2438352`). Model and checker `tools/monspawn.py` (`e6b6b56f…febbfb543`; the run was checked with `8519cd27…2ca34f1b`, and the review-fix pass of 2026-10-13 added counters only, same checks), which runs
  `tools/drlg.py` gen and roomk (`eb9fe18b…8a60ee65`, two inert recording hooks added) and `tools/monpool.py` on the same
  log. Tables: `workspace/merged/data/global/excel` (`.bin`, by position).
  - **Characters** (tool-built inputs, ADR-0003; installed and restored only through `tools/saves.py`, tags `s1`..`s3`,
    final `status` shows the seven `seedtest.*` files and no open aside): session 1 `expnm/smpsor.d2s` of
    `tools/monpool_saves.py` (`738e5912…073e271b`); sessions 2 and 3 `NovaSorc.d2s` (`1f8ece31…4165c263`), built with
    `python3 -I tools/d2s.py build <excel> tools/d2s_recipes/novasorc.json samples/d2s-owner/smpsor-l50.d2s NovaSorc.d2s`, where
    `tools/d2s_recipes/novasorc.json` (`e149aaad…c61e4be9`) is `tools/d2s_recipes/lightsorc.json` with name `NovaSorc`,
    Nova 20 and Nova on the right button (owner's request): level 80, every waypoint and Acts II–V open in all
    difficulties, belt of full rejuvenation potions.
- **Logged** (one JSON line per event, header of `tools/gdb/mon-spawn.py`): the DRLG generator and room-k tags (LC0 … AROOM);
  the room driver RW0–RW4 around the wanderer tick, presets, inactive restore and objects; the pass P0/PG/PR/PB/PN/PA/PC/PT/
  PSP/PGR/PGX/PS2/PSB/PCP/PX (PDEAD on the dead type-1 branch); SpawnPosPick SP0/SPW0/SPW/SPR0/SPR/SPX/SPF; every
  MonSpawnTry MT0/MTX with its oracle calls MR0/MR, MC0/MC, MK0/MK (arguments, result, room and game seed on entry and
  exit), the creation MU0/MU/MUP; MinionsSpawn MM0/MMN/MMX; SpawnGroup G1/GK; the special path SMPX, SMR0/SMR1/SMRX,
  SMA0/SMA1/SMAX, UMN/UMX, CP0/CPN/CPM; the special count SCI/SCD; MonWndr access watchpoints WND.
- **Procedure:**
  1. Before each session `pgrep -af 'tools/d2run[.]py'` was empty; afterwards `wineserver -k` and the same check.
  2. `MONSPAWN_WATCH=<l1,l2> python3 -I tools/d2run.py --seed N --sound --gdb tools/gdb/mon-spawn.gdb --after 5400 --log workspace/logs/<log>`,
     no steps file; the owner played:
     | log | N | character | game | owner's route | watched levels |
     |---|---|---|---|---|---|
     | `monspawn-s1-12345-normal-a1.log` | 12345 | expnm | expansion normal | waypoint to Stony Field | 4, 3 |
     | `monspawn-s2-12345-normal-a2-5.log` | 12345 | NovaSorc | expansion normal | waypoints: Far Oasis, Spider Forest, City of the Damned, Frigid Highlands | 43, 76 |
     | `monspawn-s3-1-hell-a1.log` | 1 | NovaSorc | expansion hell | waypoints: Stony Field, Dark Wood, Jail | 4, 5 |
  3. Check: `python3 -I tools/monspawn.py check workspace/logs/monspawn-s1-12345-normal-a1.log workspace/logs/monspawn-s2-12345-normal-a2-5.log workspace/logs/monspawn-s3-1-hell-a1.log`.
- **Observed:**
  ```
  drlg gen 5402 / 31621 / 16077 checks, roomk 3273 / 23244 / 17676 checks: 0 mismatches each
  passes: gate closed 169, empty 178, populated 169
  rooms with the seed predicted from the map seed: 516; from the log only: 0
  pass-entry room seed predicted end to end (no draw RW1..RW4): 176 rooms, 11 populated (listed below)
  seeds [1, 12345], difficulties [0, 2]; levels 3, 4, 5, 29, 30 (Act I), 43 (II), 76, 77, 84 (III), 106 (IV), 111, 125 (V)
  closed MonDen gates on levels 1, 75, 110 (37 passes)
  creations 916; normal groups 257; champion packs 4 (rolls 0, 9, 4, 15); unique groups 20
  type rolls 346, special 29; MonUMax draws 252 (r = 5: 1, r <= 5: 9); MonUMin draws 115
  champion roll Range(boss seed, 100) vs MonUMod rec 0 +0x1C = 20: 24 rolls, champion iff r < 20
  special-count (+0x2C8) increments 30, each checked against the model's count; no decrement inside a pass
  spawn substitution (threshold 20): taken 14, kept 5; special class from umon (normal) 9; MonStats minions 163
  unit-seed steps after Init(step(game).low) at MU: 2 on 914 creations, 6 and 15 on one each (seed oracle, reported)
  CollisionTest bypassed by R.flags & 0x80: 0; MonSpawnTry exit on x = 0 or y = 0: 0
  oracle calls: CollisionTest 3903, SpawnClassCellTest 3908, LogicRegionIdAt 4823, NearWarpTest 1919,
    presets/restore/objects 516 windows, special mods 24, mod handlers 24 + 6 (pack members)
  MonWndr watch (levels 3, 4, 5, 43, 76): every access is the region build read 0x00547A99
  monspawn: 110302 checks, 0 mismatches
  ```
  - **Rooms whose pass-entry room seed is predicted end to end** (F7 of the Phase 2 review): the room seed is predicted
    from `-seed` through the wanderer tick in all 516 rooms (RW0, RW1), but the presets / inactive-restore / objects window
    (RW1 → RW4) is a seed oracle, so the seed at pass entry is predicted end to end only where that window drew nothing
    (RW1 rs = RW4 rs): 176 rooms, 11 of them populated. Those 11:

    | log | P0 line | level | room | creations |
    |---|---|---|---|---|
    | `monspawn-s1-12345-normal-a1.log` | 5324 | 4 | `042b3400` | 1 |
    | `monspawn-s3-1-hell-a1.log` | 7268 | 4 | `042a2280` | 3 |
    | `monspawn-s3-1-hell-a1.log` | 7421 | 4 | `042a1080` | 2 |
    | `monspawn-s3-1-hell-a1.log` | 7512 | 4 | `042a1e00` | 2 |
    | `monspawn-s3-1-hell-a1.log` | 10035 | 4 | `03167800` | 3 |
    | `monspawn-s3-1-hell-a1.log` | 10438 | 4 | `02762780` | 4 |
    | `monspawn-s3-1-hell-a1.log` | 19186 | 5 | `042a7200` | 7 |
    | `monspawn-s3-1-hell-a1.log` | 19406 | 5 | `042a7180` | 5 |
    | `monspawn-s3-1-hell-a1.log` | 19674 | 5 | `042a4600` | 3 |
    | `monspawn-s3-1-hell-a1.log` | 20309 | 5 | `02d37e00` | 3 |
    | `monspawn-s3-1-hell-a1.log` | 21181 | 5 | `03021700` | 7 |
  - **Unit-seed outliers** (F10, a case for `monsters/stats`): the two creations whose unit seed is not 2 steps past
    `Init(step(game).low)` after `SUnitCreate`. `monspawn-s1-12345-normal-a1.log` line 4101 (MU), level 4, class 53
    `goatman1`, the boss of a unique group (request flags `0x40`, 5 unique minions): **6** steps.
    `monspawn-s3-1-hell-a1.log` line 10222 (MU), level 3, class 19 `fallen1`, a MonStats minion of a class 58
    `fallenshaman1` (request flags `0x40`, radius 4): **15** steps. Which callee of `SUnitCreate` makes the steps is not read.
  - **Branches of `MonSpawnTry` never taken** (F8): no pass request carried flag `0x80` (the 122 `MT0` lines with it, in
    sessions 2 and 3, are all outside the pass windows), so the collision bypass was never used, and the `x = 0 or y = 0`
    exit never fired. Both stay `[I]` (fn:sub_005B2A00_MonSpawnTry@0x005B2A00).
- **Raw logs:** `workspace/logs/monspawn-s1-12345-normal-a1.log` (sha256 `4dab869e…b0193609`),
  `monspawn-s2-12345-normal-a2-5.log` (`c50778b4…06bb16b3`), `monspawn-s3-1-hell-a1.log` (`c0556ed2…6cd152d8`).
- **Deviations and limits:**
  - Development logs are not part of the record: `monspawn-smoke.log` (scripted Blood Moor walk, 1554 checks, 0 mismatches
    with the final checker), `monspawn-dev-hell-jail.log` (the scripted route stayed in camp) and `monspawn-s2-aborted.log`
    (session 2 restarted at once to switch to the Nova build).
  - Two checker fixes during the run, both from code and data: the `umon` count at Levels `+0x35` is 0 in `levels.bin`
    and filled at load (slots up to the first negative, as `tools/monpool.py` counts `mon`/`nmon`); and
    `sub_005A48C0_ChampionMemberMark` calls `SpecialModsApply` on each pack member (read at `0x005A492C` after the
    session 3 log showed it), so a pack member's mod handlers are a seed oracle like the boss's.
  - The wanderer roll never fired (no WRL line); the tick is checked as one room draw on 516 rooms. No `sparsePopulate`
    roll (stock data, ruling of 2026-10-13), no spawnCol-1 tile placement, no tentaclehead minions, no evilhut object:
    the checker stops on each and none occurred. No classic game, no nightmare game, no multiplayer.
  - Oracles (ADR-0004): the gate's DRLG parts (RoomPopLevelId, the level room count, the Chaos quest test), the logic-box
    list, the four position predicates (value oracles, room and game seed asserted unchanged across every call and the
    arguments asserted), and the seed oracles named above. The game seed at each pass entry is run-time state, taken from
    the log; every game-seed draw inside the pass is predicted. The room seed is predicted through the wanderer tick; at pass
    entry it is taken after the presets/objects window (RW4), and is predicted end to end in 176 rooms (11 populated, listed above).
- **Conclusion:** [monsters/0002](0002-room-population.md) §§ 3–6 are reproduced bit-exactly in 516 rooms, `[C]` under the
  oracles named; the `MonUMax` threshold `≤ 5` is observed at `r = 5`; the special count is the live `+0x2C8`; the
  champion chance is MonUMod row 0 (20); `MonWndr` has no reader beyond the two of the static search on the levels watched. (run:2026-10-13-mon-spawn)
- **Addendum 2026-10-15: roomk on the predicted out-room grids, and the tile-entry flags (plan 0027 Phase 2).** No new
  game run. `tools/drlg.py gen` now runs the roomk passes in every log with `OD0` and `LSUB` lines, with the type-1 grids
  of each room's first `LSUB` taken from the drlg/0008 § 16.4 prediction (the logged grids stay the check), and in logs
  with `TL`/`CB` lines it compares every activation dump's tile-entry arrays with the model
  ([drlg/0002 § Entry flags](../drlg/0002-room-build-draws.md#entry-flags-in-full-and-the-entry-chains-plan-0027-phase-2-2026-10-15)).
  Logs of this record used: `monspawn-s1`, `s2`, `s3` and the dev logs `monspawn-dev-hell-jail`, `monspawn-smoke` (no `CB` lines: no entry compared). Command: `python3 -I tools/drlg.py gen <those logs>`. Observed:
  ```
  roomk inside gen: 2065 activations, 48 320 checks, 0 mismatches
  type-1 rooms: first LvlSub grids from GenModel's prediction  421
  entry flags compared (walls, floors, shadows of every near room at each CB)  0
  gen: 71 698 checks, 0 mismatches
  ```
  `python3 -I tools/monspawn.py check` on `monspawn-s1`, `s2`, `s3` (now on the predicted grids): 114 363 checks, 0 mismatches.
  Conclusion: the room-tiles model takes no type-1 grid from these logs any more, and the entry flags are `[C]`
  (drlg/0002). Together with the other four record families: 40 logs, 12 974 activations, 434 721 roomk checks, 2884 type-1
  rooms, 3 684 791 entries, 0 mismatches (the 38 logs of the plan 0026 addendum plus `objects-s29`/`s30`).
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0)

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- Logs: the three `monspawn-s*.log` above.
- `python3 -I tools/mon_sweep.py spawn`: `tools/monspawn.py`'s checker, `monspawn: 114363 checks, 0 mismatches`; closed
  `MonDen` gates on levels 1, 75 and 110 (Normal *Siege 1*). `python3 -I tools/mon_sweep.py pool`: 1786 `SUnitCreate`
  calls (`MU0` → `MU`), the game seed one step in each.
- Backs, with the logs of run:2026-10-14-mon-special and run:2026-10-15-mon-stats, the S3a raises and reclassifications of
  [monsters/0002 § Plan 0038 batch S3a](0002-room-population.md#plan-0038-batch-s3a-2026-10-16) (README 1, spawn 21, 37 and
  the guard rows) and pool 20, 21 of [monsters/0001](0001-level-pool.md#plan-0038-batch-s3a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S3b

- Re-reading of this run's kept logs; no new session (plan 0038 Phase 1). `python3 -I tools/sweep_s3b.py logs` checks
  each log's sha256 against this record and writes the batch manifest `workspace/logs/sweep-s3b-manifest.txt` (sha256 `ea8e196b…1298`).
- Logs: the three `monspawn-s*.log` above.
- `python3 -I tools/sweep_s3b.py spawn`: every `P0` line (the breakpoint at `RoomPopulate`'s entry) of each log carries one
  game pointer, the server game (55 logs over four runs, 4 154 passes).
- Backs spawn 2 of [monsters/0002 § Plan 0038 batch S3b](0002-room-population.md#plan-0038-batch-s3b-2026-10-16).

## run:2026-10-14-mon-special

- **Question:** (plan 0018 Phase 2) Does the model of [monsters/0003](0003-special-monsters.md), written as
  `tools/monspecial.py` and run inside `tools/monspawn.py`, predict every draw of the special-monster path with no oracle:
  the champion roll and the champion and unique mod picks (candidates, `ModEligible`, `MonTypeIsA`, one `Range` each),
  `Range(1)`, the mod handlers (`rndname`'s unit-seed step and the name seed, the aura index on its local seed; every other
  handler and its deep callees asserted to keep the unit, room and game seeds), each minion's transferred mods, the
  superunique build (placement incl. `AutoPos`, fixed mods, the difficulty extra picks, `MinGrp + d .. MaxGrp + d` minions,
  the tail, mod 22), the MonPlace 2 and 3 presets, and the client name roll? Required cases (plan 0018 Phase 1b ruling):
  (2) an `AutoPos` superunique's position, (3) superunique minion counts; the `lightning` × `sandleaper` exclusion if reached.
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7`, windowed and moved
  to a visible workspace for the owner), wine 11.17, GNU gdb 17.2. Play was **agent-driven** (the owner's choice): scripted
  input through `tools/xdrive.py`, steered by `tools/d2pilot.py` (Teleport hops to cells whose activation-time collision value
  has none of the player's blocking bits `0x1C09` in a 3×3 square, on a breadth-first path towards the level's rooms not yet
  activated; Nova every second hop; Energy Shield every 100–150 s from session 4 on; a belt potion below 70 % of the life orb)
  and by screenshots for the waypoint menu and the Tristram portal.
  - Logger `tools/gdb/mon-special.gdb` (`262c4ae7…50eca87d`), which sources `tools/gdb/drlg-gen.py` (`91feac40…5c970580`),
    `tools/gdb/drlg-roomk.py` (`d6b2e6e0…6340ce5be`), `tools/gdb/mon-spawn.py` (`731b020f…f470e3fe`: outside a pass the
    special tags log the seed of the unit's own room; SMR0 adds the difficulty and expansion flag, SMAX the unit and its name
    seed), `tools/gdb/collision.py` (`356735c1…9ed0f720`: adds the `SNP` snapshot at a superunique's and a MonPlace 2/3
    spawn) and `tools/gdb/mon-special.py` (`73f0bc52…874fe198`). One logger version for all twelve sessions.
  - Model and checker `tools/monspecial.py` (`9737fdd7…abf13588`) in `tools/monspawn.py` (`521fe7e7…74e50d09`), with
    `tools/collision.py` (`b250b9d8…f1c5869c`), `tools/drlg.py` and `tools/monpool.py` on the same logs. Tables by position
    from `workspace/merged/data/global/excel`; the handler table, the always-run mods, the aura table and the client's
    fixed-name classes read from the pinned `game.exe`.
  - **Characters** (tool-built inputs, ADR-0003), built with `python3 -I tools/d2s.py build workspace/merged/data/global/excel
    <recipe> <base> workspace/runtime/monspecial-chars/<name>.d2s` and installed only through `tools/saves.py` (tags `ms1`,
    `ms2`, `ms3`; each restored with its manifest check). `SpecNova` (expansion Sorceress, clvl 80, every waypoint and
    `quests: all` in all difficulties, the act byte on Act IV in all three, life and mana 8000, left Teleport, right Nova):
    sessions 1–3 used the first build (`058d7e9f…61b5de30`); sessions 4–6 and 10–12 the build of the committed recipe
    `tools/d2s_recipes/specnova.json` (`b91b2ee7…8a8942c7`, save `649f8450…eba02dd5`), which adds Energy Shield 20 and
    Telekinesis 20 on the weapon-swap right button after two deaths in Hell. Base `workspace/samples/d2s-owner/smpsor-l50.d2s`.
    `SpecClassic` (classic Sorceress, the same stats, progression 8, waypoints 0–29 in all difficulties, left Teleport, right
    Energy Shield): recipe `tools/d2s_recipes/specclassic.json` (`45850aa8…a6b3c486`), save `6d85055e…76a78930`, base
    `workspace/runtime/monspawn-chars/cls/smpsor.d2s`.
- **Logged** (header of `tools/gdb/mon-special.py`): MTI (every `MonTypeIsA` call: class, type, result); MPK (each pick's
  candidate rows and weights, total and draw); HD0/HDX (each handler call: mod, unit, unit/room/game seed in and out), TH0/TH1
  (the same handler on each group member); AUR/AUR2 (the aura draw: name seed, n, level, result, index); XF (a minion's mods
  after `ModsXferCopy`); SU0/SU1/SUT/SUX (superunique entry with the placed bit, mods and minion range before
  `SpecialModsApply`, the tail switch, the exit); PM0/PMC/PMX (MonPlace 2 and 3); CN0/CNR/CNH (the client name roll: the name
  seed the client holds, each table index, the `Range(100)`); PLR (the player's position, for the pilot only). Plus all
  plan 0014, 0017 and 0008 tags.
- **Procedure:**
  1. Per session: `tools/saves.py install <tag> <save>`; `MONSPAWN_WATCH= python3 -I tools/d2run.py --seed N --gdb
     tools/gdb/mon-special.gdb --steps <steps> --after 7200 --log workspace/logs/<log>`; the Act IV waypoint (window click
     712,62), the act tab and the row; `python3 -I tools/d2pilot.py explore <log> --hops 400..700 --hop 12 --nova 2|0
     --drink 0.7 [--es 120 [--es-swap 0]]` until no reachable room of the level was left unactivated; for Tristram
     `--to-pdef 160` (the Cairn Stones preset), a few `hop`s and a click on the portal, then `explore` again. Each session
     ended with `wineserver -k` on the prefix and `pkill -f 'tools/d2r[u]n.py'` (`pgrep` empty afterwards).

     | log | N | character | game | levels explored |
     |---|---|---|---|---|
     | `monspecial-s1-2101-normal.log` | 2101 | SpecNova | expansion normal | Stony Field, Tristram |
     | `monspecial-s2-2102-hell.log` | 2102 | SpecNova | expansion hell | Spider Forest (died) |
     | `monspecial-s3-2103-hell.log` | 2103 | SpecNova | expansion hell | Great Marsh (died) |
     | `monspecial-s4-2104-hell.log` | 2104 | SpecNova (ES) | expansion hell | Black Marsh |
     | `monspecial-s5-2105-hell.log` | 2105 | SpecNova (ES) | expansion hell | Cold Plains |
     | `monspecial-s6-2106-nightmare.log` | 2106 | SpecNova (ES) | expansion nightmare | Arreat Plateau |
     | `monspecial-s7-2107-classic-hell.log` | 2107 | SpecClassic | classic hell | Far Oasis |
     | `monspecial-s8-2108-classic-nightmare.log` | 2108 | SpecClassic | classic nightmare | Great Marsh (105 of 192 rooms) |
     | `monspecial-s9-2109-classic-normal.log` | 2109 | SpecClassic | classic normal | Stony Field (to the cairn), Tristram |
     | `monspecial-s10-2110-hell.log` | 2110 | SpecNova (ES) | expansion hell | Spider Forest (186 of 269 rooms) |
     | `monspecial-s11-2111-hell.log` | 2111 | SpecNova (ES) | expansion hell | Stony Field, Tristram |
     | `monspecial-s12-2112-nightmare.log` | 2112 | SpecNova (ES) | expansion nightmare | Stony Field, Tristram |

     Steps files: `tools/gdb/enter-normal-act4.steps` (sessions 1, 9), `tools/gdb/enter-nightmare.steps` (6, 8, 12),
     `tools/gdb/enter-hell.steps` (2–5, 7, 10, 11).
  2. `tools/saves.py restore ms3`: the seven `seedtest.*` files back, every sha256 equal to the manifest, no aside left.
  3. Check: `python3 -I tools/monspawn.py check workspace/logs/monspecial-s1-2101-normal.log … workspace/logs/monspecial-s12-2112-nightmare.log`
     (the twelve logs above).
  4. The earlier logs again with the oracles replaced: `python3 -I tools/monspawn.py check` on the three logs of
     [run:2026-10-13-mon-spawn](#run2026-10-13-mon-spawn) and on the seven of run:2026-10-14-collision.
- **Observed** (step 3, trimmed):
  ```
  drlg gen and roomk on all twelve logs: 0 mismatches; seeds 2101..2112, difficulties 0, 1, 2, classic and expansion
  passes: populated 471, empty 475, gate 268; preset specials: superunique 11, monplace 2: 4, monplace 3: 4
  creations 2318; special type rolls 93; champion rolls 66 (champion iff r < 20)
  champion packs 20: hell expansion 11, nightmare expansion 5, hell classic 2, normal classic 1, normal expansion 1
    (16 from the pass, 4 from MonPlace 3)
  unique groups 54: hell expansion 38, nightmare classic 6, nightmare expansion 4, normal expansion 3, normal classic 2,
    hell classic 1 (50 from the pass, 4 from MonPlace 2)
  superuniques 11: normal expansion 2, normal classic 2, nightmare expansion 3, hell expansion 3, hell classic 1
  SpecialModsRoll predicted 70 (SMR0..SMRX, mods and exit seed); mod picks: champion 16, unique 153 (candidate list, total
    and draw of each compared); MonTypeIsA calls 153, every result predicted (no exclusion: 0 returned 1)
  handler calls seed-asserted: 606 (boss, pack member, superunique); group-member handler calls 1667; rndname steps 130
  aura draws 12 (n and index predicted); minions with a transferred mod 277 (XF lists predicted)
  client name rolls 94 (41 prefix and suffix, 53 with appellation), each on the name seed of the same unit id & 0xFF
  collision model: CollisionTest 12465, LogicRegionIdAt 5691 + 10425, NearWarpTest 6628, SpawnClassCellTest 12473
    (preset-window snapshots 19)
  monspawn: 390144 checks, 0 mismatches; collision: 31485 checks, 0 mismatches
  ```
  Per session: s1 1 pack, 3 uniques, 2 superuniques (18 612 checks); s2 2, 7, 0 (54 737); s3 2, 10, 0 (60 131); s4 2, 2, 0
  (13 014); s5 1, 5, 1 (10 424); s6 2, 1, 1 (29 191); s7 2, 1, 1 (15 097); s8 0, 6, 0 (61 634); s9 1, 2, 2 (16 289); s10 2,
  8, 0 (77 851); s11 2, 6, 2 (19 222); s12 3, 3, 2 (13 942); 0 mismatches in each.

  Step 4: the plan 0014 logs: 24 special-mods rolls and 30 handler windows predicted, `monspawn: 114363 checks, 0 mismatches`
  (the oracle line "special mods" and "mod handlers" is gone); the run:2026-10-14-collision logs: 7 rolls and 14 windows,
  `monspawn: 75812 checks, 0 mismatches; collision: 20537 checks, 0 mismatches`. Those logs lack what plan 0018 adds: no
  candidate list (MPK) or `MonTypeIsA` line, no per-handler call (only the `SMA1` → `SMAX` window), no name seed, aura draw or
  client roll, no minion mod list after the transfer, and no superunique or MonPlace tag, so their presets-window specials
  stay inside the `RW1` → `RW4` seed oracle. On them the model is checked by the mod lists and exit seeds only.
- **Required cases:**

  | Case | Result |
  |---|---|
  | ≥ 20 champion packs | reproduced: 20 (all three difficulties, classic and expansion) |
  | ≥ 40 unique groups | reproduced: 54 |
  | ≥ 5 superuniques, ≥ 1 in nightmare or hell | reproduced: 11, 7 of them in nightmare or hell (Rakanishu, Griswold, Bishibosh, Threash Socket, Beetleburst) |
  | MonPlace 2 (unique, no `Range(100)`) | reproduced: 4 (Tristram; normal expansion and classic, nightmare, hell) |
  | MonPlace 3 (champion at the point, mod 16, pack) | reproduced: 4 (Tristram, the same games) |
  | a minion with a transferred mod | reproduced: 277 minions |
  | Phase 1b (2): an `AutoPos` superunique's position | reproduced: 6 (Griswold ×4, Bishibosh, Beetleburst), each placed by `SpawnPosPick` anywhere in the room, e.g. Griswold at (25141, 5179) for the preset (25131, 5191) |
  | Phase 1b (3): superunique minion counts `MinGrp + d .. MaxGrp + d` | reproduced: Rakanishu 8 / 9 / 10 (normal ×2, nightmare, hell), Bishibosh hell 4, Beetleburst classic hell 5, and one `RangeB(1)` draw with no minion for `MinGrp` = 0 (Griswold ×4, Threash Socket nightmare) |
  | superunique extra picks (`d` unique picks) | reproduced: 1 in nightmare (3 superuniques), 2 in hell (4) |
  | every champion mod with a weight drawn | `champion` 16 (hell), `ghostly` 36 (nightmare), `fanatic` 37, `possessed` 38, `berserk` 39 (nightmare and hell); in normal no pass champion was rolled (the two normal packs came from MonPlace 3) |
  | every unique mod with a weight drawn | all 13 (`strong`, `fast`, `curse`, `resist`, `fire`, `lightning`, `cold`, `manahit`, `teleport`, `spectralhit`, `stoneskin`, `multishot`, `aura`) in nightmare and in hell; in normal only `manahit`, `teleport`, `stoneskin`, `aura` (5 normal uniques) |
  | `lightning` × `sandleaper` exclusion | unreached: 153 `MonTypeIsA` calls, none on a `sandleaper` class |
  | Radament's `Range(5)` + 2 escorts | unreached (Sewers Level 3 not visited) |
  | superunique tails with quest hooks, EscortSpawn tails, `thief` skipped, an aura superunique (second aura call, Lord De Seis index 5) | unreached |
  | a fixed-name client class (156, 211, …) | unreached |

- **Surprises:**
  - **The client keeps only the low byte of the name seed.** The first client roll of the dev session disagreed with the
    16-bit seed of [monsters/0003 § 8](0003-special-monsters.md#8-names-server-seed-client-roll) and agreed with its low byte.
    The client reader `sub_0045F190_ClientMonAssign` reads 16 bits and keeps `al` (`0x0045F387`); all 94 client rolls of
    the run follow `Init(nameSeed & 0xFF)`.
  - **Monster post-create mods** (`sub_005B21B0_MonPostCreateMods`, by `BaseId`) are appended after the `MU` line, so a
    superunique `scarab2` (Beetleburst) entered `SuperUniqueSpawn` with mod 20 already present; the model now appends them
    (no draw), and the superunique's fixed mods follow them.
  - **Classic aura level.** In classic nightmare two aura uniques (class 8, `Level(N)` 50) drew their aura with level 50,
    where expansion uniques show `MonStatsInit` + 3 (10 of 10). The draw is predicted either way (n is 7 for both); the level
    rule is a `monsters/stats` question.
- **Raw logs:** `workspace/logs/monspecial-s1-2101-normal.log` (sha256 `efa54deb…eb88113b`), `monspecial-s2-2102-hell.log`
  (`4c9554f7…38db6d28`), `monspecial-s3-2103-hell.log` (`269442d0…9ce8567f`), `monspecial-s4-2104-hell.log` (`6aa3b1d6…17295a00`),
  `monspecial-s5-2105-hell.log` (`771ff425…6a90b577`), `monspecial-s6-2106-nightmare.log` (`cf9a5915…7df5e31c`),
  `monspecial-s7-2107-classic-hell.log` (`b5246760…04fbfaa4`), `monspecial-s8-2108-classic-nightmare.log` (`758475db…7daf3b44`),
  `monspecial-s9-2109-classic-normal.log` (`9859863d…85df0733`), `monspecial-s10-2110-hell.log` (`2a12b36e…8aef0ec4`),
  `monspecial-s11-2111-hell.log` (`98f5fd1f…75b28db2`), `monspecial-s12-2112-nightmare.log` (`7c9de83f…8de7abe1`).
- **Deviations and limits:**
  - Not part of the record: `monspecial-dev-1.log` (logger development, expansion normal, Cold Plains: its `HDX` was also
    logged at a null handler's jump target, fixed before session 1; its client roll showed the low-byte name seed).
  - `tools/d2pilot.py` was improved between sessions (a cached path, unreachable rooms skipped, the life-orb gauge incl. the
    green poisoned orb, Energy Shield, long random hops when stuck); the committed version is the last one. It only decides
    where to click and reads nothing that a model uses.
  - Two deaths in hell (sessions 2 and 3) ended those sessions early; the logs up to the death are complete. Sessions 8 and 10
    left 87 and 83 rooms unactivated (out of reach of the pilot's paths). Death, Energy Shield and potions change nothing the
    model reads. `enter-normal-act4.steps` ends with a screenshot to `workspace/logs/collision-arrive.png`, which sessions 1
    and 9 overwrote (an image, not a log of any record).
  - Oracles (ADR-0004) that remain, none on the special path: the presets / inactive-restore / objects window (`RW1` →
    `RW4`, a seed oracle; its superunique and MonPlace 2/3 spawns are modelled from their own entry line, which takes the
    room and game seed there), the grid snapshot at pass entry and at each preset special (`SN`, `SNP`), the DRLG gate
    parts, `SUnitCreate`'s new unit seed (the reported step counts other than 2 include every superunique boss), and the
    seed of another room at its first request. `MonTypeIsA` is not an oracle: its matrix builder is read (monsters/0003 § 3)
    and every call is predicted.
  - The monster level read by the aura handler is compared, not asserted (a `monsters/stats` input; the aura index depends
    on it only through `level ≥ 20`).
- **Conclusion:** [monsters/0003](0003-special-monsters.md) §§ 1–8 are reproduced bit-exactly for the cases listed above,
  in all three difficulties, classic and expansion, with no oracle on the special path: the mod picks, the handlers and their
  seeds, the minion transfer, the superunique build and the MonPlace 2 and 3 presets go to `[C]`; the name roll goes to `[C]`
  with the client's low-byte seed. Unreached cases stay `[I]`. (fn:sub_005A0760_SpecialModsRoll@0x005A0760, fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, fn:sub_004AC870_ClientMonNameBuild@0x004AC870)
- **Addendum 2026-10-15: roomk on the predicted out-room grids, and the tile-entry flags (plan 0027 Phase 2).** No new
  game run. `tools/drlg.py gen` now runs the roomk passes in every log with `OD0` and `LSUB` lines, with the type-1 grids
  of each room's first `LSUB` taken from the drlg/0008 § 16.4 prediction (the logged grids stay the check), and in logs
  with `TL`/`CB` lines it compares every activation dump's tile-entry arrays with the model
  ([drlg/0002 § Entry flags](../drlg/0002-room-build-draws.md#entry-flags-in-full-and-the-entry-chains-plan-0027-phase-2-2026-10-15)).
  Logs of this record used: the ten `monspecial-s*` logs with `OD0` and the dev log `monspecial-dev-1`. Command: `python3 -I tools/drlg.py gen <those logs>`. Observed:
  ```
  roomk inside gen: 3769 activations, 133 829 checks, 0 mismatches
  type-1 rooms: first LvlSub grids from GenModel's prediction  721
  entry flags compared (walls, floors, shadows of every near room at each CB)  1 264 373
  gen: 93 762 checks, 0 mismatches
  ```
  `python3 -I tools/monspawn.py check workspace/logs/monspecial-s[0-9]*-*.log`: 390 144 population and 31 485 collision checks,
  0 mismatches.
  Conclusion: the room-tiles model takes no type-1 grid from these logs any more, and the entry flags are `[C]`
  (drlg/0002). Together with the other four record families: 40 logs, 12 974 activations, 434 721 roomk checks, 2884 type-1
  rooms, 3 684 791 entries, 0 mismatches (the 38 logs of the plan 0026 addendum plus `objects-s29`/`s30`).
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0)

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- Logs: the twelve `monspecial-s*.log` above.
- `python3 -I tools/mon_sweep.py spawn` and `special`: `tools/monspawn.py`'s checker, `monspawn: 390144 checks, 0 mismatches;
  collision: 31485 checks, 0 mismatches`; closed `MonDen` gates on levels 75 and 103; with the mon-stats logs: 392
  `SpecialModsApply` windows (calls 1, 2, 4, then the list's), 685 group walks exact (621 of uniques and superuniques, 64 of
  `SetBoss` champion-pack members), 120 flag-0 aura calls without a draw, 65 aura draws (`n` 6 below level 20, 7 from 20),
  284 unique picks (no power-of-two total), 18 superuniques (placed bit 0), the post-create mods of 42 units; 115
  flag-`0x80` creations on a refused cell; 188 special-count decrements, 7910 region snapshots equal to the live count.
- Backs the S3a sections of [monsters/0002](0002-room-population.md#plan-0038-batch-s3a-2026-10-16) and
  [monsters/0003](0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S3b

- Re-reading of this run's kept logs; no new session (plan 0038 Phase 1). Manifest `workspace/logs/sweep-s3b-manifest.txt` (sha256 `ea8e196b…1298`).
- `python3 -I tools/sweep_s3b.py spawn`: one game pointer in each log's `P0` lines. `python3 -I tools/sweep_s3b.py
  special` (with the other run's logs): 538 minion lists (`XF`), 1 844 handler calls (`HD0`), none on a live minion (a
  later `MU` at the same address ends the minion).
- Backs spawn 2 of [monsters/0002](0002-room-population.md#plan-0038-batch-s3b-2026-10-16) and special 43 of
  [monsters/0003 § Plan 0038 batch S3b](0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16).

## run:2026-10-15-mon-stats

- **Question:** (plan 0025 Phase 2) Does the stat model of [monsters/0004](0004-stats.md), written as `tools/monstats.py`
  and chained after `tools/monspawn.py` / `tools/monspecial.py`, reproduce bit-exactly, for every monster created: the
  unit-seed draws of `MonStatsInit` (appearance, doomknight `Range(4)`, HP, MonProp `chance` and value roll), the base stat
  list after the classic adjustment, after MonProp and at the exit, the MonProp list, the stat list after every special-mod
  handler (flag 1 and flag 0), and, after a `/players` change, the stats of every live monster (no rescale)? Required cases
  (plan 0025 Phase 2 *Done when* and the architect's Phase 0/1 rulings) are tabulated below.
- **Setup:** the ADR-0003 harness on **slot 3** (display `:10`, prefix `workspace/wineprefix-3`, the shared
  `workspace/runtime/game`), wine 11.17, GNU gdb 17.2. Play was **agent-driven**: `tools/d2pilot.py` (`wp` for the waypoint,
  `players N` to type `/players N`, `explore --any-level --hop 12 --nova-key F1 --es-key F2 --es 30 --drink 0.6`; with
  `--any-level` the pilot walks out of a town and follows the frontier across level borders).
  - Logger `tools/gdb/mon-stats.gdb` (`ce923e2f…b05bf747`): every tag of `tools/gdb/mon-special.gdb` (plans 0014–0018,
    `tools/gdb/mon-special.py` and the files it sources unchanged) plus `tools/gdb/mon-stats.py` (`a629656e…ac4d7df6`). One
    logger version for all eleven sessions.
  - Model and checker `tools/monstats.py` (`5e45dc13…a7e6cdcb`), which runs `tools/monspawn.py` (`521fe7e7…74e50d09`) with
    `tools/monspecial.py` (`9737fdd7…abf13588`), `tools/collision.py`, `tools/drlg.py` and `tools/monpool.py` on the same
    logs first. Tables by position from `workspace/merged/data/global/excel` (monstats, monstats2, monlvl, monprop,
    difficultylevels, monumod, properties, itemstatcost, monequip, levels); `g_PlayerHpPct`, `g_PlayerXpPct`,
    `g_ClassicDiffAdjust` and `g_UModHandlers` read from the pinned `game.exe`.
  - **Characters** (tool-built, ADR-0003): `UniqNova` (expansion) and `UniqClassic` (classic), built with
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/uniqnova.json
    workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/monstats-chars/UniqNova.d2s` (recipe `3c2f57dc…78431e98`,
    save `2c793a3d…d7ddc376`) and `… tools/d2s_recipes/uniqclassic.json workspace/runtime/monspawn-chars/cls/smpsor.d2s
    workspace/runtime/monstats-chars/UniqClassic.d2s` (recipe `e58db639…a2f80793`, save `68e46a96…31eaf0ea`). Installed only
    with `tools/saves.py --slot 3` (tag `ms25`), and before every session from session 3 on re-installed fresh (`restore`,
    `aside`, `install`), because the game rewrites the save while it runs. Hotkeys F1 Nova, F2 Energy Shield.
- **Logged** (header of `tools/gdb/mon-stats.py`): `SI0` (`MonStatsInit` entry: unit, id, class, unit seed, level id,
  region entry with its variant-set count and bytes, game bytes `+0x6A`, `+0x6D`, `+0x70`, `+0x74`, the `/players` value
  `0x00883D70`), `SI1` (the `MonPlayerBonus` record, the unit seed after the appearance pick, the appearance bytes), `SI2`
  (level, `L`, `d`, `MonLvlStats` out), `SI3` (the HP draw, the unit seed), `SI4` (base stats after the classic adjustment),
  `SI5` (unit seed, base, full and attached lists after MonProp), `SIX` (the same at the exit); `HST` / `TST` (base stats,
  monster flags and mods after each handler with flag 1 / flag 0); `PCHG` and `LIVE` (at a `/players` change, stats 6, 7,
  12, 13, 100 of every monster in the game's unit lists). Plus every plan 0014–0018 tag.
- **Procedure:**
  1. Per session: `python3 -I tools/saves.py --slot 3 install ms25 workspace/runtime/monstats-chars/<char>.d2s`;
     `MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 3 --seed N --gdb tools/gdb/mon-stats.gdb --steps tools/gdb/<steps>
     --after 5400 --log workspace/logs/<log>`; `tools/d2pilot.py --slot 3 wp <log> <tab> <row>` (classic: `--wp-tab-x0 120
     --wp-tab-w 78`); then per player count of the sequence `tools/d2pilot.py --slot 3 players <log> <n>` and one `explore`
     of the hops given; `python3 -I tools/slots.py stop 3` at the end. Seeds were chosen with `tools/monpool.py pool` so that
     the target level's pool holds a MonProp class (`blunderbore1` in level 52, `quillrat8` in level 123).

     | log | N | character | game | levels (creations) | `/players` sequence | hops |
     |---|---|---|---|---|---|---|
     | `monstats-s1-2502-normal.log` | 2502 | UniqNova | expansion normal | Rogue Encampment, Blood Moor, Cold Plains, Stony Field (376) | 8 (typed in town), 3, 8 | 3 × 70 |
     | `monstats-s2-2505-nightmare.log` | 2505 | UniqNova (as left by session 1) | expansion nightmare | Rogue Encampment, Blood Moor, Cold Plains, Stony Field (369) | 3, 8 | 3 × 70 |
     | `monstats-s3-2508-hell.log` | 2508 | UniqNova | expansion hell | Glacial Trail (462) | 8 | 2 × 80 |
     | `monstats-s4-2505-nightmare.log` | 2505 | UniqNova | expansion nightmare | Halls of Pain (585) | 3 | 2 × 80 |
     | `monstats-s5-2505-classic-nightmare.log` | 2505 | UniqClassic | classic nightmare | Palace Cellar Level 1 (231) | 3, 8 | 2 × 80 |
     | `monstats-s6-2508-classic-hell.log` | 2508 | UniqClassic | classic hell | Palace Cellar Level 1 (131; died at hop 26) | 8 | 26 |
     | `monstats-s7-2509-classic-normal.log` | 2509 | UniqClassic | classic normal | Stony Field, Cold Plains (163) | 1 | 2 × 70 |
     | `monstats-s8-2510-hell.log` | 2510 | UniqNova | expansion hell | Frozen Tundra (811) | 8 | 3 × 90 |
     | `monstats-s9-2511-nightmare.log` | 2511 | UniqNova | expansion nightmare | Ancient's Way (510) | 3 | 3 × 90 |
     | `monstats-s10-2512-hell.log` | 2512 | UniqNova | expansion hell | Arreat Plateau, Frigid Highlands (453) | 8 | 2 × 90 + 14 (died) |
     | `monstats-s11-2513-hell.log` | 2513 | UniqNova | expansion hell | Worldstone Keep Level 2 (480) | 1 | 2 × 100 + 6 (died) |

     Steps files: `tools/gdb/enter-normal-act4.steps` (session 1), `enter-normal.steps` (7), `enter-nightmare.steps`
     (2, 4, 5, 9), `enter-hell.steps` (3, 6, 8, 10, 11). Every count of 4 creations in Act IV town (NPCs) is part of the
     totals.
  2. `python3 -I tools/saves.py --slot 3 restore ms25`: the empty slot back, no aside left, harness idle.
  3. Check: `python3 -I tools/monstats.py check` on the eleven logs above (output kept in
     `workspace/logs/monstats-check-all.txt`).
  4. The plan 0018 logs (run:2026-10-14-mon-special) hold no stat list (no `SI`/`HST` line), so there is nothing to rerun on
     them; Phase 1 had used their unit-seed step counts only.
- **Observed** (step 3, trimmed):
  ```
  monspawn (chain): drlg gen/roomk 0 mismatches on all eleven logs; champion packs 16, unique groups 49, superuniques 7
  monspawn: 296910 checks, 0 mismatches; collision: 29131 checks, 0 mismatches
  creations by (game, difficulty, players): classic hell 1: 56, 8: 75; classic nightmare 1: 61, 3: 90, 8: 80;
    classic normal 1: 163; expansion hell 1: 579, 8: 1627; expansion nightmare 1: 34, 3: 1327, 8: 103;
    expansion normal 1: 15, 3: 133, 8: 228
  creations 4571; appearance: variant set pick 4255, per-component draws 316; entry unit seed not an Init seed 22
  classic nightmare/hell adjustment 354 (Level + 25 d differs from Level(d) in all 354)
  creations where the L- columns differ from the plain ones 3954
  MonProp rows applied 320; player-count changes 13; live monsters compared 302 (re-created from an inactive room 57)
  handler calls (flag 1 / flag 0): hpmultiply 198/266, leveladd 198/266, rndname 198/266, champion 71/8, ghostly 11/0,
    fanatic 3/0, possessed 7/0, strong 12/45, fast 16/57, fire 12/35, lightning 26/60, cold 30/71, manahit 30/62,
    resist 37/85, spectralhit 17/39, stoneskin 28/31, teleport 21/49, aura 30/75
  monstats: 62991 checks, 0 mismatches
  ```
- **Required cases:** the table of [monsters/0004 § 12](0004-stats.md#12-phase-2-results-run2026-10-15-mon-stats).
  Met: ≥ 500 monsters over the three difficulties, classic and expansion, counts 1, 3, 8; player-count changes; champions,
  uniques and superuniques with every stat-changing mod listed there; MonProp in nightmare (incl. the `thorns` value roll)
  and hell; the classic aura level; `L-` columns in single player; Spectral Hit + 20. Not met: `berserk` (and with it the
  berserker level + 3 case), `poisonhit` (weight 0 for uniques), the `willowisp1` halving, MonProp in normal (no reachable
  row), MonEquip (no `oninit` class met), the reversed HP range.
- **Surprises:**
  - **The unit's stat callback.** The first run showed group members' hpregen growing with `hpmultiply` although the
    handler writes no stat 74 with flag 0: `MonStatsInit` gives the unit a stat list with the callback
    `sub_0055B800_MonStatCallback`, whose stat-7 case rescales stat 6 and recomputes stat 74 on every change of max HP
    ([monsters/0004 § 11](0004-stats.md#11-the-stat-callback-sub_0055b800_monstatcallback)). It also corrects Phase 1's
    classic adjustment: stat 6 is halved with stat 7.
  - **Re-created monsters.** At a player-count change, 57 live monsters had stats 7, 12 and 13 of an earlier unit with the
    same id and class: a monster of a room that went inactive is created again through a full `MonsterInit`, and the
    restore writes the first instance's values back (stat 100 is the new instance's). Unit ids are therefore reused within
    a game; the checker matches them per log.
  - **Champion packs get no flag-0 calls**; superunique minions do, also for a fixed `champion` mod.
  - **Tag clash.** The first logger's `MS0`..`MSX` collided with the missile tags `MS`/`MSX` of `tools/gdb/collision.py`;
    the tags were renamed `SI0`..`SIX` before session 1.
- **Raw logs:** `workspace/logs/monstats-s1-2502-normal.log` (sha256 `560b87df…f2f60fdf`), `monstats-s2-2505-nightmare.log`
  (`10c52203…8a567c5c`), `monstats-s3-2508-hell.log` (`93bc469a…f99c99d6`), `monstats-s4-2505-nightmare.log`
  (`c026ade7…b2d13600`), `monstats-s5-2505-classic-nightmare.log` (`11230b0b…0ff03c96`), `monstats-s6-2508-classic-hell.log`
  (`c84e8f4d…ed85eaf2`), `monstats-s7-2509-classic-normal.log` (`1eb89d58…571714e3`), `monstats-s8-2510-hell.log`
  (`f6edfda2…61ff077b`), `monstats-s9-2511-nightmare.log` (`943663fd…7d46e530`), `monstats-s10-2512-hell.log`
  (`c8f3b38e…b489f8f3`), `monstats-s11-2513-hell.log` (`3c252b57…3ed80e24`).
- **Deviations and limits:**
  - Not part of the record: `monstats-dev-2500-nightmare.log` (logger development, with the old `MS*` tags; a converted copy
    showed the callback effect first).
  - Session 1 began with a failed waypoint click (the normal character stands in the Rogue Encampment): `/players 1, 3, 8`
    were typed in town, so its first exploration ran at 8. `tools/d2pilot.py` gained `players`, `--any-level` and the
    town walk during session 1; the committed version (`fe9ae843…b8bd0a50`) is the last one. It only decides where to click.
  - Session 2 started from the save as session 1 left it (the game had rewritten it, so the nightmare character stood in
    the Rogue Encampment and the waypoint click failed); it explored Act I from there. From session 3 on the save was
    re-installed before each session.
  - The `L-` question is settled by comparison, not by a draw: the checker reports, for each creation, whether the plain
    columns would have given other values.
  - Oracles (ADR-0004): `MonEquipInit` (none met), the presets / inactive-restore window of `tools/monspawn.py`, and the
    restore of a re-created monster's stats 7, 12, 13 (taken as the first instance's: a lead for `monsters/spawn`).
    Creations on other paths (22 whose entry seed is no `Init` seed) start from the logged entry seed.
- **Conclusion:** [monsters/0004](0004-stats.md) §§ 2–8 and 11 are reproduced bit-exactly for the cases met: the HP, AC,
  XP, resistance and constant stats, the player count (creation only, no rescale), the classic factors and the
  `Level + 25·d` level (which settles the classic aura level), MonProp and the handler stat writes go to `[C]`; `berserk`,
  `poisonhit` and the `willowisp1` halving stay `[I]`. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_0055B800_MonStatCallback@0x0055B800, fn:sub_005A2120_SpecialModsApply@0x005A2120)
- **Re-analysis 2026-10-15 (static sweep, no new session): the x87 control word of the stat-7 callback.** `python3 -I
  tools/monstats.py fpsens` on the eleven logs above (`tools/monstats.py` `1edc68d2…43f21302`) runs the check without the
  chain, records every stat-7 callback call that writes stat 6 (825 calls, 786 distinct `(new, old, cur)`), and recomputes
  each with exact rounding for precision control 24, 53 and 64 bits and rounding mode nearest or chop:
  ```
  check exit 0; stat-7 callback calls writing stat 6: 825 (distinct inputs 786)
    PC 24, RC nearest: 4 calls differ from the model
    PC 53, RC nearest: 0 calls differ from the model
    PC 64, RC nearest: 0 calls differ from the model
    PC 24, RC chop: 282 calls differ from the model     (also PC 53 and PC 64: 282)
  ```
  Since the check reproduces all 825, the run excludes chop (282 calls) and a 24-bit precision control (4 calls); it
  cannot tell 53 from 64 bits (0 calls differ). The code side is [monsters/0004 § 11](0004-stats.md#11-the-stat-callback-sub_0055b800_monstatcallback).
- **Addendum 2026-10-15: roomk on the predicted out-room grids, and the tile-entry flags (plan 0027 Phase 2).** No new
  game run. `tools/drlg.py gen` now runs the roomk passes in every log with `OD0` and `LSUB` lines, with the type-1 grids
  of each room's first `LSUB` taken from the drlg/0008 § 16.4 prediction (the logged grids stay the check), and in logs
  with `TL`/`CB` lines it compares every activation dump's tile-entry arrays with the model
  ([drlg/0002 § Entry flags](../drlg/0002-room-build-draws.md#entry-flags-in-full-and-the-entry-chains-plan-0027-phase-2-2026-10-15)).
  Logs of this record used: the seven `monstats-s*` logs with `OD0` and the dev log `monstats-dev-2500`. Command: `python3 -I tools/drlg.py gen <those logs>`. Observed:
  ```
  roomk inside gen: 3717 activations, 130 993 checks, 0 mismatches
  type-1 rooms: first LvlSub grids from GenModel's prediction  828
  entry flags compared (walls, floors, shadows of every near room at each CB)  1 256 961
  gen: 66 108 checks, 0 mismatches
  ```
  `python3 -I tools/monstats.py check` on the eleven logs: 62 991 checks, 0 mismatches. A first version of the entry
  comparison failed on `monstats-s5` (level 53): the model's node lists ignored the warp re-linking, fixed by modelling the
  entry chains (drlg/0002).
  Conclusion: the room-tiles model takes no type-1 grid from these logs any more, and the entry flags are `[C]`
  (drlg/0002). Together with the other four record families: 40 logs, 12 974 activations, 434 721 roomk checks, 2884 type-1
  rooms, 3 684 791 entries, 0 mismatches (the 38 logs of the plan 0026 addendum plus `objects-s29`/`s30`).
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0)

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against this record and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- Logs: the eleven `monstats-s*.log` above.
- `python3 -I tools/mon_sweep.py pool`: the `MonRegionFindAdd` model (monsters/0001 § Plan 0038 batch S3a) over the 4571
  creations: found 4216, appended 39 (19 drawing 8–18 unit-seed steps), not appended for `TotalPieces` ≤ 2 313, unit seed
  at `MonStatsInit` entry and the appended sets reproduced in 4568 (3 without a `MonSpawnTry` line), 1145 region snapshots
  equal; the monster level of every creation and its bonuses after `MonStatsInit`.
- `python3 -I tools/mon_sweep.py stats`: `tools/monstats.py`'s checker with counting wrappers, `monstats: 62991 checks, 0
  mismatches`; no logged base entry of value 0 in 234 244; the 825 stat-7 callback calls all at full life (an integer
  product), so 53/64-bit precision and truncation/rounding do not separate. `spawn` and `special`: `monspawn: 296910
  checks, 0 mismatches; collision: 29131 checks, 0 mismatches`; closed gates on levels 1, 103 and 120 (*Mountain Top*);
  35 boxes with left = right = 0 skipped; 125 boxes whose `+0x00` rectangle would give another attempt count.
- Backs the S3a sections of [monsters/0001](0001-level-pool.md#plan-0038-batch-s3a-2026-10-16),
  [monsters/0002](0002-room-population.md#plan-0038-batch-s3a-2026-10-16),
  [monsters/0003](0003-special-monsters.md#plan-0038-batch-s3a-2026-10-16) and
  [monsters/0004](0004-stats.md#plan-0038-batch-s3a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S3b

- Re-reading of this run's kept logs; no new session (plan 0038 Phase 1). Manifest `workspace/logs/sweep-s3b-manifest.txt` (sha256 `ea8e196b…1298`).
- `python3 -I tools/sweep_s3b.py spawn`: one game pointer in each log's `P0` lines. `python3 -I tools/sweep_s3b.py
  special` (with the other run's logs): 538 minion lists (`XF`), 1 844 handler calls (`HD0`), none on a live minion (a
  later `MU` at the same address ends the minion).
- Backs spawn 2 of [monsters/0002](0002-room-population.md#plan-0038-batch-s3b-2026-10-16) and special 43 of
  [monsters/0003 § Plan 0038 batch S3b](0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16).

## run:2026-10-15-berserk-forced

- **Question:** (plan 0027 Phase 3, the `berserk` case of [monsters/0004 § 12](0004-stats.md#12-phase-2-results-run2026-10-15-mon-stats))
  Does `tools/monstats.py` reproduce the stats of `berserk` champions (`sub_005A1280_UModBerserk`: `MonHpAddPct(−75)`,
  stats 25 and 119, no `champion` part), and is a berserker's level + 3 where other champions get + 2?
- **Forced path (ADR-0010), `monumod.bin` only** (`workspace/runtime/game-forced-umb`, `ff6c6376…87ca58d3`,
  `-direct`; excel directory `workspace/runtime/excel-forced-umb`): 13 cells. Row 0 `constants` (the champion chance,
  monsters/0002 § 5) 20 → 100, and `cpick`, `cpick (N)`, `cpick (H)` 1 → 0 on rows 16 `champion`, 36 `ghostly`, 37
  `fanatic` and 38 `possessed`, so `berserk` (39) is the only champion mod with a weight and every special pack that
  is not a unique becomes a champion pack. MonUMod is read by the special branch (chance, pick) and by the handlers
  (`constants`); the edit changes which mod is drawn and how often, not what a handler does with it. `excel_bin.py
  bindiff` lists only these cells. With the stock MonUMod, `tools/monspawn.py check` on `berserkf-3102` fails 3
  (the champion picks); with the edited one, 0.
- **Setup:** slot 3, character `UniqNova` (as in run:2026-10-15-items-chain), logger `tools/gdb/mon-stats.gdb`
  (unchanged since run:2026-10-15-mon-stats). Per session (scratch script): `MONSPAWN_WATCH= tools/d2run.py --slot 3
  --seed N --gdb tools/gdb/mon-stats.gdb --steps tools/gdb/enter-hell.steps --after 3000 --install h27 …UniqNova.d2s
  --game-dir workspace/runtime/game-forced-umb --game-args=-direct`; `d2pilot.py --slot 3 wp <log> 5 2`; `players
  <log> 1`; `explore <log> --any-level --hops H --hop 12 --nova-key F1 --es-key F2 --es 30 --drink 0.6`; `slots.py
  stop 3`. Seeds 3101 (25 hops; the pilot stopped on a missing screenshot directory) and 3102–3106 (160 hops each),
  expansion Hell, `/players 1`, Frigid Highlands and on (levels 110–112, 125). Logs
  `workspace/logs/berserkf-{3101..3106}-hell.log`, manifest `berserk-forced-manifest.txt` (`bd0c98f4…da1bf009`).
- **Tool change first:** `tools/monspawn.py` ran `tools/objects.py` on any log whose `RW1` lines carry `"os"`, which
  `tools/gdb/mon-spawn.py` writes in every log since plan 0023; a `mon-stats.gdb` log has no objects window, so the chain
  failed with "window before any OGC line". It now also requires an `OGC` line (commit 98b64c4); the objects logs are
  unchanged (`objects-s10`: 7822 checks, 0 mismatches).
- **Result:**
  ```
  python3 -I tools/monstats.py check workspace/logs/berserkf-310[1-6]-hell.log --excel workspace/runtime/excel-forced-umb
  drlg gen and roomk: 0 mismatches on all six logs
  creations 1525; champions 19 (packs); handler calls (champion): mod 39 19, (champion member): mod 16 39
  monspawn: 188628 checks, 0 mismatches; collision: 15165 checks, 0 mismatches
  creations by (game, difficulty, players): expansion hell 1: 2242
  ('berserk', 39, 1, 'expansion', 'hell')   33
  monstats: 30863 checks, 0 mismatches
  ```
  - 33 `berserk` handler calls (flag 1, 33 distinct unit/seed pairs) with every stat write predicted: the −75 % life,
    stats 25 and 119; no `champion` part.
  - **Berserker level:** the level after the handlers is the pre-handler level + 3 for all 33 berserkers (`leveladd`
    + 3, no `champion` − 1), and + 2 for all 56 champion-member calls (`leveladd` + 3, `champion` − 1). This settles the
    Phase 1b contradiction of src:arreat-summit-bonuses (berserker + 3).
  - In a champion pack only the first unit gets the drawn mod (here `berserk`); the members get `champion` (16), as
    `tools/monspecial.py` models (0 mismatches).
  - **Counts (architect review 2026-10-15, rerun):** the logs hold 33 `berserk` packs (33 `SMAX` lines with mods
    `[39]`; 3102: 3, 3103: 6, 3104: 3, 3105: 4, 3106: 17), each with one berserker, and `tools/monstats.py` checks
    all 33 handler calls. The monspawn summary's 19 champion packs (and its `mod 39 19`, `mod 16 39`) count the packs
    whose spawn chain the pack model seed-asserts, a subset; it is not the number of berserkers.
  - **The row 0 edit (architect ruling 2026-10-15):** `constants` row 0 is read only by the champion-chance roll
    (`Range(boss.seed, 100) < c[0]`, monsters/0002 § 5); no handler reads it (the handlers read rows 1–33 through
    `sub_005A00F0_UModConstant`, monsters/0004 § 8, and `sub_005A1280_UModBerserk` calls it not at all: −75 and 300 are immediates, r2 at review).
    So it taints no claim of this run; the run backs nothing about the champion chance (every one of the 19 modelled
    rolls passed trivially against 100) and no champion/unique ratio.
- **Conclusion:** the `berserk` handler and the berserker level are `[C]` on a forced path; no frequency claim. (run:2026-10-15-berserk-forced)

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session. The logs are checked against `berserk-forced-manifest.txt`
  (`bd0c98f4…da1bf009`) by `python3 -I tools/mon_sweep.py logs`.
- `python3 -I tools/mon_sweep.py stats` runs `tools/monstats.py` with `--excel workspace/runtime/excel-forced-umb`
  (0 mismatches) and records the 260 stat-7 callback calls: every product an integer, PC 53 and 64 agree, truncation and
  rounding to nearest agree. Only the stat-7 callback is read here, and it reads no MonUMod cell (ADR-0013).
- Backs the reclassification of stats 26 and 27 in [monsters/0004 § Plan 0038 batch S3a](0004-stats.md#plan-0038-batch-s3a-2026-10-16).

## run:2026-10-16-sweep-monsters-b

- **Question:** (plan 0038 batch H4b, `monsters-b`) Do the inferred statements of the H4b rows hold at run time: the skill
  list a monster gets at creation and from the teleport and aura handlers, the aura table and level formula, the client
  name builder per special kind, the inactive-unit restores, every MonPlace preset case, the wanderer tick on populated
  rooms, the tentaclehead branch, the collision masks by `spawnCol` and the class cell test, the player-count record of
  `Align` 1 and 2 classes and hirelings, the doomknight draw, and which code reads `MonSpcWalk`, the region `monLvl`
  fields and the `UniqueTitle` table? Rows: [inventory § 5, H4b](../../plans/0038-inventory/README.md#harness-batches).
- **Setup:** the ADR-0003 harness on **slot 1** (display `:8`, prefix `workspace/wineprefix-1`, the shared
  `workspace/runtime/game`), wine 11.17, GNU gdb 17.2. Play was **agent-driven**: `tools/d2pilot.py --slot 1` `wp`
  (from the Act IV town start, `--wp-x 715 --wp-y 58`; classic `--wp-tab-x0 120 --wp-tab-w 78`), `players`, then
  `explore --any-level --hop 12 --nova-key F1 --es-key F2 --es 30 --drink 0.6` (session 1's first 150 hops with
  `--nova 0`, then `--to-rect` back to the first boss's room so that its room re-activated). Session 5 is the exception
  below.
  - Logger `tools/gdb/mon-stats.gdb` (`befeaffd…80d647dc`, now sourcing `tools/gdb/mon-extra.py`): every tag of
    run:2026-10-15-mon-stats unchanged plus the `mon-extra.py` tags (its header): `SIK`, `HSK`, `AURS`, `RS0`–`RSX`,
    `MNR0`/`MNRH`/`MNRX`, `MMS0`, `PMA0`/`PMAV`/`PMAX`, `RTK0`/`RTK1`, `HWT`, `CTAB`/`CMA`/`CMH`/`CNB`/`CNS`/`CNT`, and
    watchpoints `WCH` chosen per session by `H4B_WATCH`. `mon-extra.py` versions: session 1 `20c848c`; session 2 the same
    plus the `OBJP` tick scan (a pilot helper, no model input); sessions 3–8 `501195fe…72ade4d9` (`cc80406`).
    `MinionRestore`'s tags were renamed `MNR*` before session 1 (`MR0`/`MR` are `mon-spawn.py`'s).
  - Session 9 used `tools/gdb/mon-pool.gdb` unchanged (plan 0012), for a game start only.
  - **Characters** (tool-built, ADR-0003): `UniqNova` and `UniqClassic` of run:2026-10-15-mon-stats (`2c793a3d…d7ddc376`,
    `68e46a96…31eaf0ea`, unchanged), and `MercNova` (`tools/d2s_recipes/mercnova.json`, `0ecc0434…6bcae22f`, built on
    `smpsor-l50.d2s`: `1a80a833…33093140`, as in run:2026-10-16-hirelings). Every session set aside tag `h4b` and
    installed one fresh save (`saves.py --slot 1 restore`/`aside`, `d2run.py --install h4b`); all start in the Act IV
    town.
  - Seeds chosen with `tools/monpool.py pool` (`--draw 1`): 4801 holds `sandleaper` in 41/42, `doomknight` in 107/108,
    `willowisp` in 86/87; 4804 `fetishblow3` (398, `PartyMin` = `PartyMax`) in 78; 4802 `fetishblow6`–`8` in 123/127.
- **Procedure and sessions** (`MONSPAWN_WATCH=` empty in all; `H4B_WATCH` as listed):

  | log | N | character | game | levels | `H4B_WATCH` | play |
  |---|---|---|---|---|---|---|
  | `h4b-s1-4801-normal.log` | 4801 | UniqNova | expansion normal | 103, 104, 105, 106 | `title,reg:104` | 150 hops without Nova, 60 back to the first boss's room, 250 with Nova |
  | `h4b-s2-4801-nightmare.log` | 4801 | UniqNova | expansion nightmare | 107 (wp 4,3) | `spcw:107,reg:107` | 220 hops |
  | `h4b-s3-4802-hell.log` | 4802 | UniqNova | expansion hell | 111 (wp 5,2) | `title,reg:111` | 200 hops |
  | `h4b-s4-4804-normal.log` | 4804 | UniqNova | expansion normal | 78 (wp 3,4) | `spcw:78,reg:78` | 220 hops |
  | `h4b-s5-4801-normal-merc.log` | 4801 | MercNova | expansion normal | 103, 40, 47; then a second game, 103 | `title` | `/players 8`, wp 2,1; *Save and Exit*, a new game in the same process |
  | `h4b-s6-4801-normal-a2.log` | 4801 | UniqNova | expansion normal | 46 (wp 2,9) | `reg:46` | 180 hops; `farm --descend` to a tomb timed out |
  | `h4b-s7-4801-normal-a1.log` | 4801 | UniqNova | expansion normal | 6, 7 (wp 1,5) | `reg:6` | 220 hops |
  | `h4b-s8-4805-classic-normal.log` | 4805 | UniqClassic | classic normal | 3, 2 (wp 1,2) | `title,reg:2` | 200 hops |
  | `h4b-s9-4806-classic-normal-pool.log` | 4806 | UniqClassic | classic normal | game start (103) | — | `mon-pool.gdb`, 15 s |

  Session 5: `/players 8` was typed in the Act IV town; the waypoint to Lut Gholein does not re-create the hireling,
  so the session used *Save and Exit* once (a written save, overwritten by the next install) and started a second game
  in the same process, where the hireling was created with `/players` still 8. For the checkers the log is split at the
  second game's start: `h4b-s5a-4801-normal-merc-game1.log` (lines 1–9515) and `h4b-s5b-4801-normal-merc-game2.log` (the
  `#` header plus lines 9516–end). Cleanup after each: `python3 -I tools/slots.py stop 1`; at the end
  `saves.py --slot 1 restore h4b`.
- **Checks:** `python3 -I tools/sweep_h4b.py check` on sessions 1–4, 5a, 5b, 6–8 (`ddfeff95…88f0e34c`; output in
  `workspace/logs/h4b/sweep-check.txt`); `python3 -I tools/monstats.py check` (`e087526c…84133ebd`, chaining
  `tools/monspawn.py` `340e968a…13778420`) on the same logs; `python3 -I tools/monpool.py check
  workspace/merged/data/global/excel` on session 9. The sweep also re-read the 39 kept logs of run:2026-10-13-mon-spawn,
  run:2026-10-14-collision, run:2026-10-14-mon-special, run:2026-10-15-mon-stats and run:2026-10-15-berserk-forced for its
  `tentacle` and `masks` parts.
- **Observed** (trimmed):
  ```
  sweep_h4b check (9 logs): bad = 0 in every part
    sik      SIK 2678 (difficulty 0 bonus 0: 2153, 1 bonus 3: 249, 2 bonus 7: 276), 1438 with skills, 2102 skills, all as
             MonStats Skill/Sk_lvl + MonsterSkillBonus; HSK teleport 2 (one skill, level 1), aura 8
    aura     AURS 10 reproduced (rows 0, 1, 3, 4, 5, 6; difficulties 0, 1, 2)
    names    builder rows 1, 12, 16, 36-39 in CTAB; 853 client handler calls, each the table's; reproduced: champion 26
             (mod 1 then 16 / 37 / 38), superunique 6, unique 1721 23 and 1722 13, Init(name seed) per call 36; no name for
             164 minions and 92 non-specials; fixed-name class 256 (Izual): string 1014
    restore  SpecialMonRestore 11 (all from 0x005426C8): mods = saved, name seed = the first instance's (11); one with aura:
             two AURS, the second = the first instance's aura, the first another row; MinionRestore 31, handler order 1, 2, 4,
             then the saved list's rows with a handler (31)
    monplace cases 17 (9), 18 (7), 23 (2), 24 (7, hell), 26 (5, hell), 29, 30 (3), 31 (5), 36; fixed classes 27 reproduced
    tick     4785 ticks one room step (4044 on populated rooms), 0 other; populated rooms: seed carried 3033, other draws 750
    masks    spawnCol 0 0x3C01 8005, 1 0x1C0 2, 2 0x3F11 11, 3 0 13
    players  Align 1 at /players 8 (16 classes incl. roguehire): record players 1, hp% 0
    watch    title: load (DATATBLS_LoadTable, MonsterTablesLoad) 5, free (UNameTablesFree) 3, nothing else;
             spcwalk 107: 769, 78: 449, all in MonSpcWalkCheck 0x005B146F; monlvl/monlvl2 of 7 levels armed, 0 hits
    hwt      63 writes in 11 levels, 24 of them setting the bit
  sweep_h4b tentacle + masks on the 39 kept logs: tentacle heads 16, limb requests 81 reproduced, head exits 16; masks
    spawnCol 1 0x1C0 157 (tentaclehead2, tentacle2, hellmeteor), 3 0 438 (barricades, prison door), 2 0x3F11 103
  monstats check: s1+s2 / s2+s3 / s4 / s6+s7 / s5a+s8: monspawn 0 mismatches each; monstats 0 mismatches except s5a (3,
    below); doomknight Range(4) class 311: 99; guard "I1 lo >= hi: no draw" 38 (s4); presets-window SpawnClassCellTest
    predicted: 298 (30), 207 (1)
  monspawn check on the kept logs monstats-s10-2512-hell, monspecial-s6-2106-nightmare: presets-window SpawnClassCellTest
    class 528 predicted 71 (result 0: 48, 1: 23), 0 mismatches
  monpool check (session 9, classic normal): 154/154 match, MPR 136 (levels 110-136 hold their pools)
  ```
- **Surprises:**
  - **A restored aura special gets two auras.** `SpecialMonRestore` runs `SpecialModsApply` first: `rndname` steps the
    seed and the aura handler draws on that fresh name seed (row 6, Holy Shock, in session 2). Only then does it write the
    saved name seed and call `UModAura` again, which gives the first instance's aura (row 3, Holy Freeze). Both skills
    are added (`HSK` after the first: `[214, 6], [118, 7]`).
  - **`PresetFallenVariant` keys on the BaseId** of the class it is given: in level 6 `LevelClassVariant` turns `fallen1`
    into `fallen3`, and `PresetFallenVariant` turns that into `fallen2` (0x0054E2C7–0x0054E2E9).
  - **The doomknight draw is stored**: the logged appearance byte 10 equals the `Range(4)` result in all 99 creations of
    class 311. `tools/monstats.py` did not write it and reported 73 false mismatches; fixed (`7015458`) as monsters/stats
    B3 already states (`MonsterData +0x0E`).
  - **Izual's name** goes through the fixed-name branch of the builder (string 1014).
  - **`/players` survives *Save and Exit*:** the second game of session 5 started with `g_PlayersSetting` 8.
- **Deviations and limits:**
  - `h4b-dev-4801-normal.log`: logger test, not part of the record.
  - Session 5b: the DRLG models (`tools/drlg.py`) fail on a second game in one process (its DT1 lists are those already
    loaded); its 52 `monstats` creation checks pass. Session 5a: three `LIVE` mismatches for the hireling at the
    `/players` change: its stats 7, 12, 13 are the save's (level 30, experience 2 790 000), not its creation values; the
    model does not cover a hireling loaded from a save.
  - Not met: an Act II tomb (class 228; the pilot found no way into one), `suckernest1` (334), `doomknight3` (312),
    a `willowisp` special with `strong`, `champion` or `berserk`, a `MonMakeSpecial` call (Warping Shrine), the camel
    (`Align` 2 at `/players` 8 was met only as `cow`, in run:2026-10-15-mon-stats).
- **Raw logs:** `workspace/logs/h4b/`: `h4b-s1-4801-normal.log` (`baeb486e…c5e5501e`), `h4b-s2-4801-nightmare.log`
  (`035571ca…586244a2`), `h4b-s3-4802-hell.log` (`17ce8a46…5f1d39ec`), `h4b-s4-4804-normal.log` (`d800c506…ca05746b`),
  `h4b-s5-4801-normal-merc.log` (`abe15e5e…ebf76ae6`; split `f4263eae…4801a2b2`, `99fec276…26f3df17`),
  `h4b-s6-4801-normal-a2.log` (`77a3ff18…18fd49f0`), `h4b-s7-4801-normal-a1.log` (`0c7b4716…5944bee7`),
  `h4b-s8-4805-classic-normal.log` (`2cae03c7…cfa36e3e`), `h4b-s9-4806-classic-normal-pool.log` (`9a3baefb…043ea37e`).
- **Conclusion:** the rows are settled one by one in the "Plan 0038 batch H4b" sections of
  [monsters/0001](0001-level-pool.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b),
  [0002](0002-room-population.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b),
  [0003](0003-special-monsters.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b),
  [0004](0004-stats.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b) and
  [hirelings/0001](../hirelings/0001-hirelings.md#plan-0038-batch-h4b-run2026-10-16-sweep-monsters-b).
- **Review (architect, 2026-10-16):** the eleven log hashes above, the split of session 5 (lines 1–9515 and 9516–end,
  byte-identical to the whole) and the tool hashes (`sweep_h4b.py`, `monstats.py`, `monspawn.py`, `mon-stats.gdb`,
  `mon-extra.py`) match the files. Re-run on the lane: `sweep_h4b.py check` on the nine logs gives the summary of
  `workspace/logs/h4b/sweep-check.txt` line for line (bad = 0 in all eleven parts); `monstats.py check` gives 0 mismatches
  on s1+s2 (17 810), s3 (3 860), s4 (3 823; guard `lo ≥ hi` 38), s6+s7 (8 198) and s5b (52), and 3 on s5a+s8 (the three
  `LIVE` values of the hireling, as recorded); the chained `monspawn.py` 0 mismatches on each group but s5b (1, the DRLG
  model on a second game); `monspawn.py check` on `monstats-s10-2512-hell.log` and `monspecial-s6-2106-nightmare.log`
  0 mismatches (class 528 tests 71); `monpool.py check` on s9 154/154. Read with objdump at the review: the doomknight
  writes (311 → `+0x0E`; 312 → `+0x0E` and `+0x0F`, 0x00573D5C–0x00573DAC), the `MonMakeSpecial` jump at `0x005830CC`
  and the shrine-table entry 20 (`0x006E1940` → `0x00583050`), the tentacle call and its `o` (0x005B2903–0x005B290A), and
  the `HWT` write (`0x0066E37E`); `g_UModAuraTable`, `g_ChampionNameStr` and `g_ClientUModHandlers` read from the file
  match the ledger. Verdict and rulings in the [plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log).
- **Tool addendum (2026-10-20, plan 0049 Phase 1, `lane/p49r`; the H4b review's tool follow-ups).** No session. Two
  changes:
  - (a) `tools/monstats.py` compares a hireling's `LIVE` line on stat 100 only. Its stats 7, 12 and 13 come from the
    mercenary load of the save and are counted as `LIVE hirelings` (`case live_hireling`). s5a + s8 now check with 1 718
    checks and 0 mismatches; the hireling, class 271, is the one case.
  - (b) `tools/drlg.py`'s `parse_log` refuses a log that holds a second game. The marker is a second `WNDARM` line with
    `levels`, which `tools/gdb/mon-spawn.py` writes once per game. The unsplit s5 log stops the `monspawn.py` chain with
    "a second game starts at line 9516 … split the log at line 9516", and the split s5a still checks clean (4 238
    checks, 0 mismatches).

  Logs without that tag are not tested for a second game. Outputs `workspace/logs/p49r/monstats-h4b-s5a-s8-p49r-2026-10-20.txt`,
  `monspawn-h4b-s5a-p49r-2026-10-20.txt` and `monspawn-h4b-s5-refused-p49r-2026-10-20.txt`, with tool hashes in
  `p49r-manifest.txt`.

## run:2026-10-21-sweep-monsters-a

- **Question:** (plan 0038 batch H4a, `monsters-a`) Do the inferred statements of the H4a rows hold at run time: the
  superunique tails by record index (Radament's draw and escorts, the council's and the seal bosses' quest hooks, the
  Siege Boss's and Nihlathak's `EscortSpawn`), the aura a superunique runs twice and Lord De Seis's forced index, the
  `thief` mod dropped from fixed mods, the null handler rows, the placed bit, the fixed client names, the `boss` classes'
  monster level, the Chaos Sanctuary population gate, the wanderer class list, and `MonEquipInit`? Rows:
  [inventory § 5, H4a](../../plans/0038-inventory/README.md#harness-batches).
- **Setup:** the ADR-0003 harness on **slot 1** (display `:8`, prefix `workspace/wineprefix-1`, the shared
  `workspace/runtime/game`), wine 11.17, GNU gdb 17.2. Play was **agent-driven** by `tools/h4a_sessions.py run --slot 1
  --tag h4a --saves workspace/runtime/h4a-chars --run h4a SESSION` (`81f7d5b1…e507f22a` at the end of the run; each
  session's commands are its `SESSIONS` row): `tools/d2pilot.py` `wp` from the Act IV town, then `--descend`, `hunt
  --mon-cls`, `explore` or `objop` (Teleport on Shift + left, Nova F1, Energy Shield F2).
  - Logger `tools/gdb/mon-h4a.gdb` (`eb0b61eb…4c5bc04a`) = `tools/gdb/mon-stats.gdb` unchanged (`befeaffd…80d647dc`,
    with `mon-extra.py` `501195fe…72ade4d9`) plus `tools/gdb/mon-h4a.py`: `SUC`/`SUCR` at every call of
    `SuperUniqueSpawn`'s tail cases 0x005A4BFE–0x005A4E43 with the pushed arguments and the return, `SURD` after
    Radament's `Range(us, 5)`, `GQ` at the Chaos Sanctuary gate 0x0054EC27 (room, game, `eax`), and the pilot helpers
    `MON` and `OBJS` (no model input). `mon-h4a.py` versions: sessions raven to nihl `d9546d4e…` (`d050b7d`); shenk,
    nihl2 and chaos7 `0cb41645…f24625c9` (`652f2f8`, adds `OBJS` only). The chaos sessions use
    `tools/gdb/mon-h4a-obj.gdb` (`38615238…1115b206`): the same plus `tools/gdb/objects.py` (`7d78c5e3…0a8b55ae`;
    `OO0`/`OOX` at the operate call). `MONSPAWN_WATCH` and `H4B_WATCH` empty in every session.
  - **Character:** `UniqNova` of run:2026-10-15-mon-stats (`2c793a3d…d7ddc376`, unchanged), expansion; each session
    restored and set aside tag `h4a` and installed the save fresh; all start in the Act IV town, Nightmare
    (`enter-nightmare.steps`).
  - Before the first session, H4b review condition (4): `sweep_h4b.py check` on the nine H4b logs gives the summary of
    `workspace/logs/h4b/sweep-check.txt` line for line (`check/regress-sweep_h4b.txt`), and `monstats.py check` 0
    mismatches on every group (`check/regress-monstats.txt`).
- **Sessions** (`workspace/logs/h4a/`, each `h4a-s1-<seed>-<name>.log` with its `.pilot.txt` and shots):

  | session | seed | levels | play | met |
  |---|---|---|---|---|
  | raven | 4901 | 3 | wp 1,2; explore towards the Burial Grounds | not reached |
  | raven2 | 4807 | 3, 17 | as raven, plan 0048's raven-xn2 map seed | Blood Raven (mods 12, 22; name 3111; `SI2` 43) |
  | tree | 4902 | 5 | wp 1,4; hunt 24 | Treehead WoodFist (record 4), null row 13 |
  | andy | 4903 | 35–37 | wp 1,9; descend; hunt 156 | Andariel (level 49, name 3021) |
  | radament | 4904 | 48, 49 | wp 2,2; descend (LvlWarp 23); hunt 229 | tail 10, r = 0 |
  | council | 4905 | 83 | wp 3,8; explore 220 | tails 26, 27, 29 |
  | durance | 4906 | 101, 102 | wp 3,9; descend; hunt 242 | Bremm Sparkfist's aura twice; tails 28, 30; Mephisto (59, 3062) |
  | foothills | 4908 | 109, 110 | wp 5,1; explore `--any-level` | tail 48; no Siege Boss |
  | nihl | 4909 | 115 | wp 5,5 (the wrong row: Glacial Trail) | none |
  | shenk | 4815 | 110, 111 | wp 5,2; hunt 479 towards (3906, 5114) | tail 42 |
  | nihl2 | 4910 | 123, 124 | wp 5,6; descend (LvlWarp 80); hunt 526 | tail 60; Nihlathak (70) |
  | chaos7 | 4907 | 107, 108 | wp 4,3; into 108; per wing `objop --to-pdef W --pdef-any --skip-operated --obj-near 6` (300 s) on seals 392–396 and a sweep; `objop` on every seal seen; sweep; explore 80; hunt 243 | seals 392, 393, 395, 396 operated; the Infector of Souls (36) and the Grand Vizier (38); seal 394 seen, not reached; 63 `doomknight3`; one wanderer roll; no Diablo |

- **Checks** (`workspace/logs/h4a/check/`, hashed in the manifest): `tools/sweep_h4a.py check` (`7df479f7…3b26c246`) on the
  twelve session logs (`sweep-check.txt`) and on the 63 kept logs of `kept-logs.lst` (`check-kept-final.txt`, from the
  earlier monster runs and run:2026-10-20-chain; their hashes in `kept-logs.sha256`); `tools/monstats.py check`
  (`8d6d0d13…052f1860`, chaining `tools/monspawn.py` `835b4549…0ef81d7f`) per session log (`monstats-h4a.txt`), all run by `check/run-checks.sh` (`dd9be9fc…5a39a788`) under
  `systemd-run --user --scope -p MemoryMax=4G` and on
  the two plan 0048 logs with a `MonEquipInit` creation (`monstats-monequip-kept.txt`); the static reads
  `static-wanderer.txt` (objdump and r2), `static-wanderer-tick.txt` and `static-gate.txt`; `aura-control.txt` (`AUR`
  lines per superunique window) and `doomknight3-app.txt` (class 312's appearance bytes), from the same script.
- **Observed** (trimmed):
  ```
sweep_h4a check, 12 session logs (bad 0 in every part):
  su       SU0 15; fixed mods written in order 15; mod 22 appended last 15; Bremm Sparkfist (28) AUR r 2 twice, AURS rows [2, 2]
  tails    records 10, 26, 27, 29, 36, 38, 42, 60 reproduced; 0, 4, 28, 30, 48, 49 no tail call
           record 10: Range(us, 5) = 0 -> 2 x class 4, then [276, 382, 385, 389]; 6 units
           record 36 / 38: 0x5436b0[23, 36 | 38, room, 0, 1]
           record 42: EscortSpawn(453, 1, 20, 20, 0) -> 20 x 453, return 1; hook 31; 0x545b50; state 118
           record 60: 0x58f030[217, 1, 1, 0, 60]; 0x620bb0; 0x63ec70 -> 458; EscortSpawn(458, 1, 10, 20, 0x40) -> 20 x 458; hook 34
  handlers SpecialModsApply windows 121; null rows skipped: 7 x23, 13 x6, 22 x3, 29 x11, 34 x14
  gate     GQ 91 (level 108), byte 0 -> PG 1 in all 91
  boss     classes 156, 229, 242, 267, 526 at d 1: MonStats Level(N) 49, 49, 59, 43, 70; area MonLvlEx 43, 44, 55, 36, 64
  names    fixed 156 -> 3021, 242 -> 3062; mod 12 (267) -> 3111; superunique names 27, champion 64, unique 78
  wander   RTK0 7184: 7183 one step; WRL 1 (chaos7:97550, level 108, low d17d0000), roll 82 -> two steps
63 kept logs: placed bit set, Stacks 0: refused 3; aura twice 2; null rows 10 x11, 13 x7; RTK0 4785, all one step
aura-control: AUR before / after SpecialModsApply's exit: 28 1/1; 42, 60, 36 1/0 (30 an extra pick)
monstats (monstats.py): 0 mismatches on all 12 logs; doomknight3 63 creations, bytes 10 = 11, values 0..3
  ```
- **Deviations and limits:**
  - Development logs in `workspace/logs/h4a/dev/` (not part of the record): raven-nowp (the waypoint click missed);
    chaos and chaos2 (no object lines, so no seal found); chaos3 and chaos4 (seals not clicked); chaos5-paused (stopped
    by the owner's pause; it opened seals 392 and 393, `OO0`/`OOX`, then its later objops re-targeted them); chaos6
    (stopped by the lane: `--obj-near 4` left it 4.2 sub-tiles from seal 392 with no hop); chaos7-paused (stopped by
    the second pause after seals 392, 393, 395 and 396). Their manifest is `h4a-manifest-dev.sha256`.
  - Chained models (`tools/monstats.py check` runs `tools/monspawn.py` and the DRLG models first): their mismatches,
    none on a tag this batch's rows rest on: council, 3 DRLG room-tile mismatches (`CB` W entries of one DRLG room,
    first difference at entry 18, flags `0x8005`), which `monspawn.py` reports as its 1; nihl2, 1 `monspawn` (Nihlathak's
    mods at `SU1` are `[22, 30]`, the model's `[30]`: mod 22 was already in the list when `SpecialMonPlace` returned,
    `SMPX` mods `[22]`, which the model's post-create table lacks for class 526); chaos7, 2 `monspawn` (the
    `CollisionTest` at the Infector's and the Vizier's placement points returned 4097 and 4096, the collision model 1
    and 0: bit `0x1000` set in the game only) and 10 collision (the creation marks of five units next to them, logged
    none). The superunique checks (`sweep_h4a.py su`, `tails`) read the logged lines and pass on all three logs.
  - Session nihl took the Glacial Trail waypoint row; nihl2 is its retry. Session raven did not reach the Burial
    Grounds; raven2 is its retry on another map seed.
  - The pilot (`tools/d2pilot.py`, `663f57c2…e6bb94ef` at the end) gained `objop --skip-operated` before chaos6. Nothing it
    computes feeds a model.
  - Not met: the Ancients (tails 43–45: no recipe with the quest open), The Countess's and the Cow King's tails (6, 39),
    Baal Subject 2 (62), the class-704 `ubermephisto` aura; a wanderer roll below 3 (a spawn); Lord De Seis (37): seal
    394 (at (7773, 5155) in level 108, logged by `OU0`/`OI0`) was never operated, because `objop` found no hop towards it
    (d 33, in two objops); so no `GQ` with a non-zero byte, and no Diablo (`hunt 243` timed out). Owner play is the route
    (monsters/0003 § H4a).
- **Raw logs:** listed with their sha256 in `workspace/logs/h4a/h4a-manifest.sha256` (`sha256sum -c` from
  `workspace/logs/h4a/`).
- **Conclusion:** the rows are settled one by one in the "Plan 0038 batch H4a" sections of
  [monsters/0001](0001-level-pool.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
  [0002](0002-room-population.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
  [0003](0003-special-monsters.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a),
  [0004](0004-stats.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a) and
  [items/0010](../items/0010-quest-drops.md#plan-0038-batch-h4a-run2026-10-21-sweep-monsters-a).
