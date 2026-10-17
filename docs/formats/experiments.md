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

## run:2026-10-15-cube-saves

Plan 0030 Phase 0, archivist lane, harness slot 1 (display `:8`, prefix `workspace/wineprefix-1`).

- **Question:** (1) how does the game compile each `cubemain.txt` cell and column into `cubemain.bin`, including the
  columns and keywords no stock row uses; (2) do the six cube recipe saves that `tools/d2s.py build` writes load,
  and does the game write them back unchanged?
- **Setup:**
  - Compile runs: a game directory `workspace/runtime/game-cubeprobe/` holding a symlink to every entry of
    `workspace/runtime/game/` and a real `data/global/excel/` with one file, the `cubemain.txt` under test. The game
    runs with `-direct -txt`; it compiles every table when a game is entered (not at the main menu: two runs that
    stayed in the menu wrote nothing) and writes the `.bin` files into that directory. Launcher, per compile:
    `python3 -I tools/d2run.py --slot 1 --seed 12345 --install a30p0 CubeRunes.d2s --steps <enter.steps> --after 2
    --game-dir workspace/runtime/game-cubeprobe --game-args="-direct -txt" --log workspace/logs/a30p0-cubeprobe-<tag>.log`,
    where the steps file is `tools/gdb/cube-load-normal.steps` cut after its first screenshot (*Single Player*,
    *OK*, *Normal*, 12 s), then `python3 -I tools/slots.py stop 1`.
  - Load runs: the pinned `game.exe` in `workspace/runtime/game/` (stock data), no `--gdb`, seed 12345. Saves built
    from the committed recipes, expansion ones on `workspace/samples/d2s-owner/smpsor-l50.d2s`, the classic one on
    `workspace/runtime/monspawn-chars/cls/smpsor.d2s`:
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/<recipe>.json <base> <Name>.d2s`.

    | recipe | save | sha256 (built) | items |
    |---|---|---|---:|
    | `cuberunes.json` | CubeRunes | `416cb60e442bf2e13bfeaeace0f322206d4344e2a35f0094b175340693261b7c` | 45 |
    | `cubereroll.json` | CubeReroll | `1a1ec8918f4860bb026b3346b7ad5143026eb6303b8505ae2f4d79d03021a17d` | 41 |
    | `cubecraft.json` | CubeCraft | `6b4c6eb6b0194c075813974fb728a77dd07e9204cdcecd5900b4db7eeed025e6` | 53 |
    | `cubesock.json` | CubeSock | `fc5674f780e62ac90791636433212c4cbbc39348a963c42aaac367da1ef3d52d` | 30 (29 top-level) |
    | `cubeportal.json` | CubePortal | `3b8a86449deaca038dfb3898232e97994e94c5c1ab4bedea7a4055b9903732a2` | 17 |
    | `cubeclassic.json` | CubeClassic | `a87fba7a84b3f76e88b79768fc0f8c69451cde8605b3be7d5bd4a08bf0b06093` | 48 |

    The transmutes each recipe carries (first group in the cube, the rest in the inventory, then the stash), by
    [CubeMain](../tables/CubeMain.md) row: **CubeRunes** 51 (cube), 52, 59, 100, 103, 104 (ladder), 111 (ladder),
    23, 32, 37, 46, 47, 49, and two chipped amethysts (no row); **CubeReroll** 60 (cube: magic ring + three perfect
    gems), 60 (magic amulet, small charm, jewel), 61 (rare ring, rare amulet + six perfect skulls), 62 (rare ring +
    perfect skull + *The Stone of Jordan*), and two no-row sets (two perfect gems; a normal ring); **CubeCraft** 71
    (cube: Hit Power ring), 80, 89, 98 (Blood, Caster, Safety rings), 70, 79, 88, 97 (amulets), 66, 75, 84, 93
    (gloves `mgl`, `vgl`, `lgl`, `hgl`), and a normal ring (no row); **CubeSock** 123 (cube: quilted armor + Tal +
    Thul + perfect topaz), 124, 125, 126, 63 (rare amulet + three perfect skulls + *The Stone of Jordan*), 141 (a
    socketed cap holding a sapphire + Hel + Town Portal scroll), and a socketed short sword (no row: `nos`);
    **CubePortal** 2 (cube: Wirt's Leg + Tome of Town Portal), 2 again, 148, 149, 150, and Wirt's Leg + Identify
    scroll (no row); **CubeClassic** 23 (cube), 3, 5, 7, 13, 11, 147, 61, 6, 15, and 60 (version 100, to be refused
    in classic). Magic items carry one suffix (`suffix`), rare items names only (`rare`), the jewels suffix 260.
- **Procedure:**
  1. Compile the stock `cubemain.txt`; compare the written `cubemain.bin` with the shipped one.
  2. `python3 -I tools/cubemain.py probe-txt workspace/merged/data/global/excel <dir>` writes the stock rows plus the
     probe rows (a first version had 78). Its compile wrote no `cubemain.bin` (88 other tables written, the game
     window black). Bisection by compiling subsets of the probe rows: header rows, input rows, the first 22 output
     rows each compiled; the other 21 did not, then 15 of them, 9, 3, and finally the single row with output
     `useitem,sock`. That row was dropped from `PROBE_OUTPUTS`.
  3. Compile the probe (77 rows); then once more with four rows added for the input/output head order (`key`,
     `axe,mag` as inputs, `axe`, `key,mag` as outputs): 81 probe rows, 232 records. Decode with
     `python3 -I tools/excel_bin.py diff workspace/cmp/cubeprobe-excel cubemain` (the probe pair, with links to the
     stock tables the references need).
  4. Diff the plan 0005 sample table compiled the same way on 2026-10-11 (`workspace/runtime/game-mod/`, copied to
     `workspace/cmp/cubesamples-excel/`).
  5. `python3 -I tools/saves.py --slot 1 aside a30p0` (slot saves directory empty), then per save
     `saves.py --slot 1 restore a30p0`, `aside a30p0`,
     `python3 -I tools/d2run.py --slot 1 --seed 12345 --install a30p0 <Name>.d2s --steps tools/gdb/cube-load-normal.steps --after 6 --log workspace/logs/cube-load-<Name>.log`
     (`cube-load-classic.steps` for CubeClassic: no difficulty box), which enters Act I town, opens the inventory,
     right-clicks the cube at inventory (8, 2), closes both, and uses *Save and Exit*; `slots.py stop 1`; copy the
     written save out; compare it with the built one item by item (`d2s.parse`, every field but the byte offsets)
     and run `d2s.py survey` and `d2s.py roundtrip` on both sets.
  6. `python3 -I tools/slots.py stop 1`, `saves.py --slot 1 restore a30p0`: aside none, harness idle.
- **Observed:**
  - Step 1: the compiled `cubemain.bin` is byte-identical to the shipped one (sha256 `a907396d…40fdd`).
  - Step 2: the output cell `useitem,sock` alone stops the compile; every other probe cell compiles.
  - Step 3: `excel_bin.py diff` with the layout of [CubeMain](../tables/CubeMain.md): 232 records × 164 fields =
    38 048 cells, 0 mismatches, after three model corrections the probe forced (an input head is resolved as an item
    type before an item code, an output head as an item code first; `sock=N` in an input sets the `sock` flag only;
    a fourth `pre=` fills `suf1`). The stock pair: 24 764 cells, 0 mismatches. Further compiler facts read off the
    probe: `min diff`, `class`, `op`, `lvl`, `plvl`, `ilvl` and the mod `chance` are bytes (300 → 44); `param` and
    `value` are s32; the mod `param` is u16, `min` and `max` s16; a skill name in a mod `param` compiles to its
    digit-by-digit integer; `useitem,reg` stores kind `0xFF`; `nos`, `noe`, `upg`, `bas`, `nru` in an output change no
    byte; `sock=` and `qty=` share the output's byte 7, the later one wins; a named unique or set item stores record
    index + 1.
  - Step 4: the sample table: 158 records, 25 912 cells, 0 mismatches (its `key` output, an item, is what first showed
    the output head order).
  - Step 5: all six saves entered Act I town with the cube's contents shown (`workspace/logs/cube-load-<Name>-cube.png`).
    Every item of every written file equals its built counterpart field by field, in order (45, 41, 53, 30, 17 and 48
    items); `d2s.py survey` (6 files, 0 errors, 0 leftover bytes) and `d2s.py roundtrip` (12 files, 468 items,
    0 differences) pass. The bytes that differ are header fields (checksum, `last_played`, appearance bytes, the map
    seed), in CubeClassic two bytes of the `WS` section (`0x29B`, `0x2B3`, as in run:2026-10-15-socket-saves), and
    in CubePortal one quest byte (`0x1AA`, the high byte of normal-difficulty quest word 40, an Act V quest the
    recipe's `quests: "all"` had set bit 0 of).
  - sha256 of the written files: CubeRunes `ceb6ce86be6577b68ac11929923c8bf6d622b79732f37a7de4280515e71aac43`,
    CubeReroll `311f81a0dff83da7a580594ee18254ff036be9fd8ac45edff5aead367e271acc`,
    CubeCraft `8728688452ec434ec3462ef4d47b5e08dcfaa391e6270b00c1ab6b697485e690`,
    CubeSock `c292662a11612ca45d2d3602319158e72041c16880ba19d66170e43ac40baff4`,
    CubePortal `e9b345a7e44e733cf444b7e695653b5dba48b783506ccb7cb2d2199ca4dd573f`,
    CubeClassic `ba2fc3d35a2cc7cb19427b517c576ce94234a07cd5c2fa658237611b7c6e79e0`.
- **Raw log:** `workspace/logs/a30p0-cubeprobe*.log` and `workspace/logs/cube-load-<Name>.log` (launcher headers only,
  no debugger); screenshots `workspace/logs/cube-load-<Name>-{ingame,inv,cube,menu}.png`; the built and written
  saves and the probe files (`cubemain.txt` with 81 probe rows, sha256 `211dc6aa4c9aaea0a43ba0e86a7a296b2502c52f564e9905f3ed3709749c431c`; its compiled
  `cubemain.bin`, sha256 `14df5bf049c3eb20d59bf96aaff4468cb576be6b94b5b65ba0234ee60bbe5a63`; the stock compile; the two bisection tables) in
  `workspace/logs/cube-saves/`.
- **Conclusion:** the `cubemain` record layout and the compiled form of every input and output keyword are `[C]` by
  data behaviour over three compiled tables, one of them written to exercise every column
  ([CubeMain](../tables/CubeMain.md)); what the transmute does with them is plan 0030 Phase 1. The six cube recipe
  saves load and survive *Save and Exit* unchanged ([d2s.md § Cube recipe saves](d2s.md#cube-recipe-saves)). No
  transmute was pressed in this run.

### Addendum 2026-10-16: the whole `.bin` set the compile wrote (plan 0039 A3)

Asked by the reverser (plan 0038 S1b, [data/0001 § Plan 0038 batch S1b](../findings/data/0001-excel-loader.md#plan-0038-batch-s1b-2026-10-16)
rows 26, 29, 30; [data/0004 § Plan 0038 batch S1b](../findings/data/0004-cell-converters.md#plan-0038-batch-s1b-2026-10-16)).
No new run: this reads the kept output of the compile runs above, the directory
`workspace/runtime/game-cubeprobe/data/global/excel/` as the last compile (step 3, the 81-row probe) left it
(timestamps 2026-10-15 09:23), against the shipped files in `workspace/merged/data/global/excel/`.

- **Commands:** `python3 -I tools/sweep_s1b.py compile` (rerun 2026-10-16 in the `lane/p39a` worktree; since
  2026-10-17 it also prints the per-table compare, last bullet), and at first a
  per-table compare of the 15 code lists, `compcode` and the four `*code.bin` pools (a scratch script outside the
  repository: byte compare of each written file with the shipped one, and the archives that ship it).
- **Observed:**
  - `S1B compile bad=0 bins_written=90 codebin_written=4 codelist_bin_in_stock_archives=15 codelist_bin_written=15
    no_loader_bin_written=0 no_loader_txt_in_archives=4 shipped_not_written=2 txt_in_probe_dir=1
    written_byte_identical=88 written_differs=2`.
  - The two that differ: `cubemain.bin` (76 100 bytes written, 49 532 shipped: the probe's own table, as step 3
    intends) and `monstats.bin`, two bytes: record 707 (`uberandariel`) `NameStr` (u16 at `+0x006`) compiled 11154,
    shipped 5382.
  - Shipped but not written: `cubemod.bin`, `cubetype.bin`. Written but not shipped: none. No `.bin` for
    `treasureclass`, `aiparms`, `monname` or `weaponclass`, although all four `.txt` are in the archives.
  - The 15 code-list tables of `DATATBLS_LoadCodeLists` (`playerclass`, `bodylocs`, `storepage`, `elemtypes`,
    `hitclass`, `colors`, `hiredesc`, `monmode`, `plrmode`, `monai`, `monplace`, `skillcalc`, `misscalc`, `skills`,
    `events`), `compcode` and the four `*code.bin` pools were all written and are all byte-identical to the shipped
    files. Every one of them also ships as a `.bin`: `playerclass`, `bodylocs`, `storepage`, `hitclass`, `colors`,
    `hiredesc`, `plrmode` in d2exp; `elemtypes`, `monmode`, `skills` in d2exp and patch_d2; `monai`, `monplace`,
    `skillcalc`, `misscalc`, `events`, `compcode` and the four pools in patch_d2.
- **Conclusion:** `[C]` the pinned game's `-direct -txt` compile writes the shipped `.bin` byte for byte for 88 of the
  90 tables it wrote, the two exceptions being the probe table and one `monstats` cell. The table docs' `.bin` layouts
  are therefore the layouts this binary's compiler produces, not only those of the shipped files. The `monstats` cell
  is the `Lilith` string-key case of [MonStats](../tables/MonStats.md): the pinned compiler, given this install's
  string tables (`patchstring` entry 1154 is `Lilith`), stores 11154; the shipped file holds 5382, an index from
  string tables without that key (how the shipped file was made stays an inference, data/0004). The code-list tables'
  docs ([StorePage](../tables/StorePage.md), [ElemTypes](../tables/ElemTypes.md), [colors](../tables/colors.md),
  [HireDesc](../tables/HireDesc.md), [MonMode](../tables/MonMode.md), [PlrMode](../tables/PlrMode.md),
  [MonPlace](../tables/MonPlace.md), [SkillCalc](../tables/SkillCalc.md), [MissCalc](../tables/MissCalc.md),
  [Skills](../tables/Skills.md)) cite this addendum; "a stock run never loads them" stays `[I]` (data/0001 § S1b row
  30): the `.bin` files ship, so their absence cannot show it.
- **Re-run (architect review, 2026-10-16):** `sweep_s1b.py compile` gives the same summary line, and an independent
  byte compare of the 15 code lists, `compcode` and the four `*code.bin` pools (`misscode`, `skillscode`,
  `skilldesccode`, `itemscode`) between the same two directories finds all 20 written and identical.
- **Per-table compare in the tool (2026-10-17, `lane/arc4`):** `sweep_s1b.py compile` now compares each of those 20
  tables itself, prints one `code table <name>: identical|DIFFERS (shipped in <archives>)` line per table, adds the
  key `codetable_identical` (and `codetable_differs`, `codetable_missing`, each a `bad`), and so reproduces the
  per-table claim above without the scratch script. Rerun on the same directories: the summary line as above plus
  `codetable_identical=20`, `bad=0`, and the 20 lines name the same archives as the bullet *Observed*.
