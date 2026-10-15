# Format experiments

Owned by `archivist`. Runs whose claim is about a file format's bytes: a save written and reloaded, a
parser-edited file loaded in the game (evidence-rules § Experiments). Runs about game code go in
`docs/findings/<subsystem>/experiments.md`. Each record follows ADR-0003: exact command lines, the
steps, and the raw-log path or a statement that none was kept.

Common setup for every run here: the plan 0003 harness (`.claude/skills/reverser/references/tooling.md`
§ Runtime harness). wine 11 (new wow64), prefix `workspace/wineprefix`, rootful Xwayland `:7`, pinned
`game.exe` in `workspace/runtime/game/`. Saves are written to
`workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II/`. No debugger and no breakpoints.
Input goes through `tools/xdrive.py --display :7 --window "Diablo II"` (window-relative clicks on
the 800×600 window).

## run:2026-10-11-d2s-samples

- **Question:** what does the pinned game write for a new character, for a fresh character after
  *Save and Exit*, and for items of every quality? These are the samples for
  [d2s.md](d2s.md#samples).
- **Setup:**
  - Stock saves: game dir `workspace/runtime/game/`, unmodified data.
  - Item saves: game dir `workspace/runtime/game-mod/`. Every entry is symlinked from `game/`, plus a
    real `data/global/excel/` that holds the two edited tables:
    `python3 -I tools/d2s_samples.py workspace/merged/data/global/excel workspace/runtime/game-mod/data/global/excel <variant>`.
    The variant per sample is in [d2s.md § Samples](d2s.md#samples) (`lvl1` for `qit1ama`, `a`
    for `qitnec` and `qitbar`, `b` for the rest). The `b` output is byte-identical to the tables now
    in `game-mod`.
  - Launch, as `tools/d2run.py` starts the game (its step 2), from the game dir:
    `WINEPREFIX=workspace/wineprefix DISPLAY=:7 wine game.exe -w -ns`, with `-direct -txt` added for
    `game-mod`. Whether a `-seed N` switch was also given was not recorded. The seed changes item
    seeds and rolls, not the layout.
- **Procedure:**
  1. Character: main menu → *Single Player* (`click 400 307`) → *Create New Character* → class →
     type the name (`type <name>`) → *OK*. The game writes the 335-byte stub at this point.
  2. In Act I town: `key Escape` → *Save and Exit Game*. The full save replaces the stub.
  3. Item saves only, before step 2: `key i`, `rclick` the cube to open it, move the Scroll of
     Identify into it, *Transmute*, then close the panels.
  4. `qitbarb` only: Tir, then El, socketed into the sword by hand, then step 2.
  5. Copy each `.d2s` to `workspace/samples/d2s/`. The two stubs are the files of characters
     `seedtest` and `uiu` as created, copied before their first *Save and Exit* as
     `stub-<name>.d2s`.

  The *Single Player* coordinate is the one in `tools/gdb/enter-sp.steps`. The click coordinates
  used on the class screen, the name field, the cube and the inventory were sent one command at a
  time and not recorded. No steps file was kept. A rerun must re-measure them from a screenshot
  (`xdrive.py shot`).
- **Observed:** 19 files, sha256 in [d2s.md § Sample hashes](d2s.md#sample-hashes). File times
  (`saves-backup/p0005/` and the copies) give the order: `smp*` (18:17–18:21), `qit1ama`, then
  `qitama`, `qitasn`, `qitnec`, `qitbar`, `qitpal`, `qitdru`, `qitsor` (18:28–18:33, variant `a`),
  then `qitnecb` and `qitbarb` (18:35–18:37, variant `b`). Variants `a` and `b` differ only in the
  Necromancer and Barbarian recipes.
  The tooltip of the `qitbarb` sword read "Steel … Ethereal (Cannot be Repaired), Socketed (2)".
  `python3 -I tools/d2s.py survey workspace/merged/data/global/excel workspace/samples/d2s/*.d2s`
  exits 0. In `qit1ama` the three level-1 cube outputs are a rare ring, a rare amulet and a magic
  ring (quality 6, 6, 4), from a recipe asking for `rin,uni`, `amu,rar` and *Angelic Halo*.
- **Raw log:** none kept. No screenshots kept. The saves are the record: `workspace/samples/d2s/`,
  plus the `.key`/`.ma0`/`.map` side files of the item and fresh saves in
  `workspace/runtime/saves-backup/p0005/`.
- **Conclusion:** gives the sample set behind the `[C]` layout rows of [d2s.md](d2s.md). The
  level-1 unique/set fallback is creation behaviour, `[L]` in d2s.md until a code anchor exists
  (backlog D2S (a)).

## run:2026-10-11-d2s-edit

- **Question:** does the game load a save rewritten by `tools/d2s.py`, and does it check the checksum?
- **Setup:** game dir `workspace/runtime/game/` (stock data), launched as in
  run:2026-10-11-d2s-samples without `-direct -txt`. Inputs: `workspace/samples/d2s/smpbar.d2s` and
  `smpsor.d2s` from that run. Outputs in `workspace/samples/d2s-edited/`.
- **Procedure:**
  1. `python3 -I tools/d2s.py setstat workspace/merged/data/global/excel workspace/samples/d2s/smpbar.d2s workspace/samples/d2s-edited/smpbar.d2s 0 45`.
     `cmp -l` against the original: offset `0x300` (one byte of the stat stream) and the checksum
     bytes `0x0E`–`0x0F`.
  2. `d2s-edited/smpsor.d2s`: `smpsor.d2s` with the byte at `0x2B` (header `level`) changed from 1
     to 2, and the checksum **not** fixed (`cmp -l`: only offset `0x2B`).
  3. `d2s-edited/smpsor-fixed.d2s`: the same bytes with the checksum recomputed
     (`d2s.py checksum` to compute it; `cmp -l` against step 2: only offset `0x0E`).
  4. For each file: put it alone in the save directory under its character's name, launch, then
     *Single Player* → select → *OK* (the sequence of `tools/gdb/enter-sp.steps`), then `key c` for
     the character screen. If the game was entered, `key Escape` → *Save and Exit Game*, and copy the
     written file back as `d2s-edited/<name>-resaved.d2s`.
- **Observed:**
  1. `smpbar` entered the game. The character screen showed Strength **45**.
  2. `smpsor` showed "Level 2 Sorceress" on the select screen. *OK* gave "Unable to enter game,
     generic bad file".
  3. `smpsor-fixed` entered the game.

  Both re-saved files have valid checksums (`d2s.py survey` exits 0 on them).
  `smpsor-resaved.d2s` has header `level` 1 again.
- **Raw log:** none kept. No screenshots kept. The five files in `workspace/samples/d2s-edited/`
  (sha256 in [d2s.md § Sample hashes](d2s.md#sample-hashes)) are the record.
- **Conclusion:** confirms the checksum algorithm and the stat-stream layout `[C]` in
  [d2s.md](d2s.md#checksum): the game accepts a parser-written save. The checksum alone accounts
  for the refusal in (2), because (3) has the same level mismatch and loads. Three behaviour
  observations stay `[L]` in d2s.md until a code anchor exists (backlog D2S (a)): the select screen
  skips the checksum, entering the game refuses a bad one, and the save rewrites the header level.

## run:2026-10-11-d2s-waypoints

Written ahead by plan 0008 Phase 0b and run on 2026-10-11 by the archivist lane.

- **Question:** does the game load a save whose `WS` bit field was rewritten by `tools/d2s.py setwp`;
  does its waypoint menu list exactly the waypoints whose bits are set, with bit *n* = the level whose
  `levels.txt` `Waypoint` is *n* ([d2s.md § Waypoints](d2s.md#waypoints-ws)); and does a travel by
  waypoint to a maze level (Catacombs Level 2, `DrlgType` 1) succeed? The last part makes the save
  reusable by plan 0008 Phases 2 and 3 and by `monsters/spawn` runs.
- **Setup:** game dir `workspace/runtime/game/` (stock data), launched by `tools/d2run.py` (no
  `--gdb`, so its last step is a plain wait) on `:7`. Input `workspace/samples/d2s/smpsor.d2s`
  (sha256 `fd2f770d…540c5e`, [d2s.md § Sample hashes](d2s.md#sample-hashes)). Outputs in
  `workspace/samples/d2s-waypoints/`. Run only when no other run holds the harness. Let
  `SAVES="workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II"`.
- **Procedure:**
  1. Set the save directory aside: `mv "$SAVES" "$SAVES.keep-wp" && mkdir "$SAVES"`.
  2. Make the two saves:
     ```
     mkdir -p workspace/samples/d2s-waypoints
     python3 -I tools/d2s.py setwp workspace/samples/d2s/smpsor.d2s workspace/samples/d2s-waypoints/smpsor-a.d2s normal 0,2,6,8
     python3 -I tools/d2s.py setwp workspace/samples/d2s/smpsor.d2s workspace/samples/d2s-waypoints/smpsor-b.d2s normal 0,9,12,18,26,27,29,30,35,38
     ```
     For each: `cmp -l` against `smpsor.d2s` lists only offsets inside `0x0C`–`0x0F` (checksum) and
     `0x283`–`0x287` (the normal bit field); `python3 -I tools/d2s.py checksum <file>` exits 0;
     `python3 -I tools/d2s.py dump workspace/merged/data/global/excel <file>` lists, under
     `waypoints normal`, A: Rogue Encampment, Stony Field, Jail Level 1, Catacombs Level 2; B: Rogue
     Encampment, Lut Gholein, Halls of the Dead Level 2, Kurast Docktown, Durance of Hate Level 2, The
     Pandemonium Fortress, River of Flame, Harrogath, Halls of Death's Calling, The Worldstone Keep
     Level 2. Record the sha256 of both files.
  3. Save A: `cp workspace/samples/d2s-waypoints/smpsor-a.d2s "$SAVES/smpsor.d2s"` (alone in the
     directory, so it is the preselected character), then
     `python3 -I tools/d2run.py --seed 1 --steps tools/gdb/enter-sp.steps --after 900 --log workspace/logs/d2s-waypoints-a.log`.
     The steps enter Act I town on normal and write `workspace/logs/d2run-last.png`; `--after 900`
     leaves 15 minutes for steps 4–7 before the wine session is killed.
  4. Open the waypoint: from the screenshot, find the Rogue Encampment waypoint (the stone pad) and
     `python3 -I tools/xdrive.py --display :7 --window "Diablo II" click <x> <y>` on it; repeat
     (`shot` after each move) until the waypoint menu opens. Write the clicks that worked, with their
     `sleep`s, to `tools/gdb/d2s-wp-open.steps`, so later runs replay them after `enter-sp.steps`
     (the town layout is the same for the same save and `--seed`; record if it is not).
  5. `xdrive.py --display :7 shot workspace/logs/d2s-waypoints-a-menu.png` with the Act I tab shown.
     Record every entry the menu lists as travelable and every one shown greyed or absent. The
     hypothesis predicts exactly Rogue Encampment, Stony Field, Jail Level 1 and Catacombs Level 2,
     and not Cold Plains, Dark Wood, Black Marsh, Outer Cloister or Inner Cloister.
  6. Click *Catacombs Level 2*. After `sleep 10`: `key Tab` (automap, which names the area) and
     `shot workspace/logs/d2s-waypoints-a-catacombs.png`. Record the area name shown.
  7. `key Escape` → *Save and Exit Game*. Copy `"$SAVES/smpsor.d2s"` to
     `workspace/samples/d2s-waypoints/smpsor-a-resaved.d2s` and run `d2s.py survey` and `dump` on it;
     record its `waypoints` lines (does the game keep bits 2, 6, 8 and add nothing else?).
  8. Save B: empty `"$SAVES"`, copy `smpsor-b.d2s` there as `smpsor.d2s`, and repeat steps 3–5 with
     log and screenshot names `-b`, replaying `tools/gdb/d2s-wp-open.steps`. Click each act tab
     (I–V) and shoot it (`d2s-waypoints-b-act<N>.png`). Record, per tab, whether the tab can be
     opened and which entries it lists. The hypothesis predicts Act I: Rogue Encampment; II: Lut
     Gholein, Halls of the Dead Level 2; III: Kurast Docktown, Durance of Hate Level 2; IV: The
     Pandemonium Fortress, River of Flame; V: Harrogath, Halls of Death's Calling, The Worldstone
     Keep Level 2. If a tab is locked (the save has no quest progress), record that: its bits then
     stay `[L]`. Do not travel; `key Escape`, *Save and Exit Game*, keep the file as
     `smpsor-b-resaved.d2s`.
  9. Restore: `rm -r "$SAVES" && mv "$SAVES.keep-wp" "$SAVES"`.
- **Deviations from the procedure:** step 4's clicks were found by walking with automap (`key Tab`)
  screenshots in between, because the pad is off screen at game entry. In step 9 the four files the
  game wrote (`smpsor.d2s/.key/.ma0/.map`) were removed by name and the empty directory removed with
  `rmdir`. The sha256 of the seven files in the saves directory (`seedtest.*`) was taken before
  step 1 and after step 9, and the two lists are identical.
- **Observed:**
  1. Step 2: both files as predicted. `cmp -l` against `smpsor.d2s` lists only checksum bytes
     `0x0C`–`0x0F` and field bytes `0x283`–`0x284` (A) or `0x284`–`0x287` (B). `d2s.py checksum`
     exits 0 on both, and `dump` lists the predicted levels under `waypoints normal`, with nightmare and
     hell still `bits [0]`. sha256: `smpsor-a.d2s` `2c965bc2…94332`, `smpsor-b.d2s` `3105dc9f…5e6`
     (full hashes in [d2s.md § Sample hashes](d2s.md#sample-hashes)).
  2. Save A entered the Act I town, on normal. The waypoint pad is north-east of the start, past the
     camp fire. Clicking it opened a menu with **one tab, "I"**, headed *Choose your destination*. Its
     nine rows, in order:

     | row | entry | shown as |
     |---|---|---|
     | 1 | Rogue Encampment | icon, blue text (the waypoint you are standing on) |
     | 2 | Cold Plains | no icon, grey text |
     | 3 | Stony Field | icon, white text |
     | 4 | Dark Wood | no icon, grey text |
     | 5 | Black Marsh | no icon, grey text |
     | 6 | Outer Cloister | no icon, grey text |
     | 7 | Jail Level 1 | icon, white text |
     | 8 | Inner Cloister | no icon, grey text |
     | 9 | Catacombs Level 2 | icon, white text |

     This is exactly the hypothesis: Stony Field, Jail Level 1 and Catacombs Level 2 travelable, the
     five others not.
  3. Clicking *Catacombs Level 2* moved the character onto a waypoint pad in a dungeon room. The
     automap title read **"Catacombs Level 2"** (`d2s-waypoints-a-catacombs.png`). The travel works.
  4. `smpsor-a-resaved.d2s` (958 bytes, like the input): `d2s.py checksum` passes, and `survey` exits
     0 (`saves 1, bad 0`). Its 80-byte `WS` section (`0x279`–`0x2C8`) is **byte-identical** to
     `smpsor-a.d2s`: normal `bits [0, 2, 6, 8]`, nightmare and hell `bits [0]`, tails zero. Nothing
     was added or dropped. The bytes that differ from the written file are `0x0C`–`0x0F`
     (checksum), `0x30`–`0x31`, `0xAB`–`0xAE`, `0x165`, and one byte in each of the seven items
     (`0x34A` + 14·k, k = 0..6). None of them is in `WS`.
  5. Save B, after replaying `enter-sp.steps` and then `tools/gdb/d2s-wp-open.steps` unchanged
     (`xdrive.py … run`): the replay opened the waypoint menu with no manual help. The menu again had
     **one tab, "I"**, but was headed *No Other Waypoints Activated*. Rogue Encampment showed an icon
     and blue text. All eight other Act I rows showed no icon and grey text, Stony Field, Jail Level 1
     and Catacombs Level 2 among them (their bits 2, 6 and 8 are clear in B).
     **No tabs II–V were drawn.** Clicking where they would sit (y = 75, x = 175, 235, 295, 355)
     left the Act I page unchanged (`d2s-waypoints-b-act1.png` … `-act5.png` all show it). So none of
     B's bits 9–38 reached the menu: the tabs are absent, as expected for a save with no quest
     progress past Act I.
  6. `smpsor-b-resaved.d2s`: `checksum` and `survey` pass, and its `WS` section is **byte-identical**
     to `smpsor-b.d2s`. The game kept normal `bits [0, 9, 12, 18, 26, 27, 29, 30, 35, 38]`, including
     byte `0x287` (bits 32–39, here 35 and 38), through a load and a save. Differing bytes as in
     (4), except `0x165`.
  7. The town layout and the walk were the same for both saves with `--seed 1`. No crash.
- **Raw log:** `workspace/logs/d2s-waypoints-a.log` and `-b.log` hold only the `d2run` header and
  the game pid (no `--gdb`). Screenshots in `workspace/logs/`: `d2s-waypoints-a-menu.png` (sha256
  `607011fd…91de6`), `d2s-waypoints-a-catacombs.png` (`3c044972…959d7`),
  `d2s-waypoints-b-act1.png` … `-act5.png`, the step replay's `d2s-wp-open-last.png`, and the
  exploration shots `wp-a-*.png`, `wp-b-*.png`. The four save files in
  `workspace/samples/d2s-waypoints/` (sha256 in d2s.md) are the record. For reuse: save
  `smpsor-a.d2s`, command `d2s.py setwp … normal 0,2,6,8`, launch
  `d2run.py --seed 1 --steps tools/gdb/enter-sp.steps --after 900`, then
  `xdrive.py --display :7 --window "Diablo II" run tools/gdb/d2s-wp-open.steps`, then click
  *Catacombs Level 2* at window (230, 418).
- **Conclusion:**
  - The game loads a `setwp`-written save, and its Act I waypoint menu shows exactly the waypoints
    whose bits are set. Every observation fits bit *n* = Act I menu row *n*+1 = the level whose
    `levels.txt` `Waypoint` is *n*. But only bits 2, 6 and 8 (Stony Field, Jail Level 1, Catacombs
    Level 2) were seen **both set and clear**: set in A, clear in B. Bits 1, 3, 4, 5 and 7 were seen
    clear only (in both saves), and bit 0 set only (in both saves). So the run raises bits 2, 6 and 8,
    and the LSB-first order across bytes `+0x02` and `+0x03` (bit 8 is bit 0 of `+0x03`), to `[C]` in
    [d2s.md](d2s.md#waypoints-ws). Bits 0, 1, 3, 4, 5 and 7 stay `[L]`: the run is consistent with the
    rule but doesn't tell them apart. The [addendum](#addendum-pending) (save C) and plan 0004 Phase 2's
    Cold Plains travel are meant to settle them.
  - The block at `0x281` is the **normal** block: on normal difficulty the menu follows it, and the
    other two blocks were left at `bits [0]`.
  - A waypoint travel from a `setwp` save to a maze level (Catacombs Level 2) works. Save `smpsor-a.d2s`
    with `tools/gdb/d2s-wp-open.steps` is the reusable start for plan 0008 Phases 2 and 3.
  - Not settled: bits 9–38. B's Act II–V tabs were not drawn, so the run shows nothing about their
    mapping, and the 5-byte width stays `[L]`. The run only observed that the game keeps bits up to 38
    (byte `+0x06`) through a load and a save. Which code hides the tabs (quest state, presumably) is
    a code question. Whether the game forces bit 0 was not tested, since both saves set it. The
    nightmare and hell block order stays `[L]`.

### Addendum (PENDING)

**PENDING: not yet run.** Written ahead by the plan 0008 Phase 0b review. Save A set bits 0, 2, 6 and 8
and save B set bit 0 plus bits 9–38, so bits 1, 3, 4, 5 and 7 were never seen set and bit 0 never
clear. Save C sets exactly those five and clears bit 0. Whoever runs it fills in Observed and
Conclusion and may then raise the bits it settles in [d2s.md](d2s.md#waypoints-ws).

- **Question:** with bits 1, 3, 4, 5 and 7 set and bit 0 clear, does the Act I tab list exactly Cold
  Plains, Dark Wood, Black Marsh, Outer Cloister and Inner Cloister as travelable, besides Rogue
  Encampment (the waypoint the character stands on)? And after a re-save, is bit 0 set again (does the
  game force it on)?
- **Setup:** as in the main run (game dir, `d2run.py` without `--gdb`, display `:7`, `$SAVES` set aside
  and restored with a sha256 check). Run only when no other run holds the harness. Before launching,
  make sure no stale `tools/d2run.py` driver from an earlier run is alive (see `docs/backlog.md`).
- **Procedure:**
  1. `python3 -I tools/d2s.py setwp workspace/samples/d2s/smpsor.d2s workspace/samples/d2s-waypoints/smpsor-c.d2s normal 1,3,4,5,7`.
     Check it as in step 2 of the main run: `cmp -l` shows only `0x0C`–`0x0F` and `0x283`; `checksum`
     exits 0; `dump` lists `waypoints normal … bits [1, 3, 4, 5, 7]`. Record its sha256.
  2. Put it alone in `$SAVES` as `smpsor.d2s` and run
     `python3 -I tools/d2run.py --seed 1 --steps tools/gdb/enter-sp.steps --after 900 --log workspace/logs/d2s-waypoints-c.log`.
     If the game refuses to load or enter the save, record that and stop at step 5.
  3. `python3 -I tools/xdrive.py --display :7 --window "Diablo II" run tools/gdb/d2s-wp-open.steps`,
     then `xdrive.py --display :7 shot workspace/logs/d2s-waypoints-c-menu.png`. Record, for each of
     the nine Act I rows, icon or none and white, blue or grey text.
  4. `key Escape` → *Save and Exit Game*. Copy `$SAVES/smpsor.d2s` to
     `workspace/samples/d2s-waypoints/smpsor-c-resaved.d2s`. Run `d2s.py survey` and `dump` on it, and
     record the `waypoints normal` bits: is bit 0 back, and are 1, 3, 4, 5 and 7 kept?
  5. Kill the session (the `d2run.py` driver by PID, then `wineserver -k`) and restore `$SAVES`.
- **Observed:**
- **Conclusion:**

## run:2026-10-15-socket-saves

Plan 0029 Phase 0, archivist lane, harness slot 3 (display `:10`, prefix `workspace/wineprefix-3`).

- **Question:** does the game load saves that `tools/d2s.py build` wrote with socketed items (`sockets`, `filled`)
  and items in the stash (`store` 5), and does it write them back unchanged?
- **Setup:** pinned `game.exe` in `workspace/runtime/game/` (stock data), `tools/d2run.py` without `--gdb`, seed
  12345. Saves built from the committed recipes on the test bases:
  `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/socketnova.json workspace/samples/d2s-owner/smpsor-l50.d2s SocketNova.d2s`
  (sha256 `2f2cb8dde892ed0619813f22278f919b98dcfbcaf8b4cc49e6dd77995c14ff1a`, 1691 bytes, 47 items: 42 top-level,
  5 socketed) and
  `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/socketclassic.json workspace/runtime/monspawn-chars/cls/smpsor.d2s SocketClassic.d2s`
  (sha256 `5e14a113d06656efac1f5171df6ffd600c033279b04855f3f6f6f05cb9cf612a`, 1270 bytes, 24 items: 23 top-level,
  1 socketed). SocketNova holds socketed bases with 2–6 empty sockets in the stash and the inventory, three
  pre-filled bases in the cube (a short sword with two gems, a skull cap with one of two sockets filled, a small
  shield with El and a magic jewel), and loose runes, gems and jewels; SocketClassic holds classic bases with 2–6
  sockets in the inventory and stash, a cap with one of two sockets filled, and loose gems.
- **Procedure:**
  1. `python3 -I tools/saves.py --slot 3 aside a29p0` (the slot's saves directory was empty).
  2. `python3 -I tools/d2run.py --slot 3 --seed 12345 --install a29p0 SocketNova.d2s --steps tools/gdb/socket-load-normal.steps --after 8 --log workspace/logs/socket-load-nova.log`:
     *Single Player*, *OK*, *Normal*, inventory open and closed, `key Escape`, *Save and Exit Game*.
  3. Copy the written `SocketNova.d2s` out of the saves directory; compare it with the built file
     (`d2s.py survey`, `d2s.py roundtrip`, a field-by-field comparison of every parsed item).
  4. `saves.py --slot 3 restore a29p0`, `aside a29p0` again (a first classic attempt with both characters in the
     directory selected SocketNova and wrote nothing for SocketClassic; it is not counted), then
     `python3 -I tools/d2run.py --slot 3 --seed 12345 --install a29p0 SocketClassic.d2s --steps tools/gdb/socket-load-classic.steps --after 8 --log workspace/logs/socket-load-classic.log`
     (no difficulty box: progression 0), and step 3 for `SocketClassic.d2s`.
  5. `python3 -I tools/slots.py stop 3`, `saves.py --slot 3 restore a29p0` (aside: none, slot empty).
- **Observed:**
  - Both characters entered the game in the Rogue Encampment; the inventory screenshot of SocketNova shows the
    socketed short sword, the loose runes, gems and jewels and the cube where the recipe placed them
    (`workspace/logs/socket-load-nova-inv-s3.png`).
  - Both written saves parse clean (`d2s.py survey`: checksum, sections and every item boundary match) and
    re-encode byte for byte (`d2s.py roundtrip`: 4 files, 142 items, 0 differences, built and written).
  - Every item of both written saves equals its built counterpart field by field, in the same order: 47 and 24
    items, the counts 42 and 23, the socketed parents' flags bit 11, socket counts (2–6) and `n_filled`, the
    socketed children (location 6, `x` = socket index, after their parent), the magic jewels' suffix and property
    list, and the stash items (`store` 5, at their `x`, `y`). The bytes that differ are header fields only: the
    checksum, `last_played`, the appearance bytes, the map seed (now 12345), and in the classic save two bytes of
    the `WS` section (`0x29B`, `0x2B3`).
  - sha256 of the written files: SocketNova `679b8888e5f1bc350d34e29bd06456d3c471c777cabeedd26982f10999eb0dd1`,
    SocketClassic `82bfe4697bce5576db3db8f6dd4430fd51b070445c19e51156aee37639ce2011`.
- **Raw log:** `workspace/logs/socket-load-{nova,classic}.log` (launcher headers only, no debugger), the
  screenshots `workspace/logs/socket-load-{nova,classic}-{ingame,inv,menu}-s3.png`, and the built and written saves
  in `workspace/logs/socket-saves/`.
- **Conclusion:** the builder's socketed items and stash items are what the game loads and writes back
  ([d2s.md § Building socketed items](d2s.md#building-socketed-items)): `store` 5 = stash moves from `[L]` to `[C]`
  for the layout, and the socketed-child form (`location` 6, `x` = socket index, byte-aligned after the parent,
  not counted) is confirmed on built items of every class. What the game does at insert time (stats, runewords) is
  not tested here; that is plan 0029 Phases 1–2.
