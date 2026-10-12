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
