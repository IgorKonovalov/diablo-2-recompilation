# Tooling recipes

Paths assume the repo root as the working directory. `Game.exe` here means
`workspace/install/app/game.exe` (the pinned one; `tools/ghidra.sh` checks its sha256 against
`docs/inventory.md` before importing).

## Ghidra headless: `tools/ghidra.sh`

```bash
tools/ghidra.sh build                    # import + auto-analysis + replay re/symbols.csv (slow, see log)
tools/ghidra.sh rebuild                  # rm -rf workspace/ghidra, then build
tools/ghidra.sh import-symbols           # replay re/symbols.csv into the existing project
tools/ghidra.sh export-symbols           # user-defined symbols -> re/symbols.csv (keeps tags/evidence)
tools/ghidra.sh decompile 0x0045A1B0 RNG_Next   # C to stdout (address anywhere inside, or a name)
tools/ghidra.sh xrefs 0x006EC7FC         # refs to an address; plus callees if it is a function
tools/ghidra.sh findstring treasureclass # defined strings containing text, with referencing functions
tools/ghidra.sh findscalar 0x6AC690C5    # functions using an immediate: size, callers, hit count
tools/ghidra.sh strings 0x00642AE0       # strings a function references (source paths = module)
tools/ghidra.sh emu 0x0045C390 cases.txt # emulate a __fastcall(u32 *seed, u32 edx) per "low high edx" line
```

- Project: `workspace/ghidra/d2.gpr`, program `game.exe`, language `x86:LE:32:default`, cspec `windows`.
- Logs: `workspace/logs/ghidra-build-<UTC>.log` (+ `.script.log`), and `workspace/logs/ghidra-last.log(.script)`
  for the most recent query. Query commands open the project `-readOnly`, so renames have to go through
  `re/symbols.csv` + `import-symbols` (or the GUI followed by `export-symbols`).
- `SYMBOLS_CSV=<path>` points import/export at another CSV (round-trip tests).
- Each headless call starts a JVM and opens the project: about 10–20 s overhead. Pass several targets
  to one `decompile` call rather than looping.

Scripts in `re/ghidra_scripts/` are **Java** GhidraScripts, compiled at run time, with no Python
dependency. To check they compile without a project: `javac -proc:none -cp "$(find /opt/ghidra/Ghidra -name '*.jar' | tr '\n' :)" -d <tmp> re/ghidra_scripts/*.java`.
- `ImportSymbols.java <csv>`: create or rename functions and labels, apply signatures, put the
  `[tag] subsystem evidence` in a plate/EOL comment.
- `ExportSymbols.java <csv>`: user-defined symbols back out, sorted, merged with the existing
  confidence/subsystem/evidence columns. New names get `L` and are listed in the log. CSV rows with no
  matching symbol are kept and reported, never dropped.
- `Decompile.java`, `Xrefs.java`, `FindString.java <out-file> <targets...>`: write to a file, which the wrapper prints.
- `FindScalar.java`, `StringsIn.java`, `EmuFastcall.java`: as above. `EmuFastcall` uses Ghidra's p-code
  emulator (`EmulatorHelper`, deprecated in 12.1). Pair it with a `tools/` model for bit-exact `[C]` checks
  (see `tools/rng.py check`).
- Planned: `ImportTypes.java re/types/*.h`.

Headless runs lock the project. Never run two at once, and never while the GUI has it open.

## radare2 / rizin quick looks

```bash
r2 -q -c 'izz~Levels.txt' Game.exe                 # all strings matching
r2 -q -c 'aa; axt @ str.<name>' Game.exe            # xrefs to a string (after light analysis)
r2 -q -c '/x c590c66a' Game.exe                     # byte search: 0x6AC690C5 little-endian
r2 -q -c 's 0x0045A1B0; af; pdf' Game.exe           # disassemble one function
rz-bin -S Game.exe; rz-bin -i Game.exe               # sections; imports
```

Use r2 for fast questions. Its function names aren't authoritative, and nothing it names goes into
`symbols.csv` without being read in Ghidra.

## Runtime harness (wine + gdb)

How to *play* on it (scripted rules, owner play, showing a slot, the slot rules) is in [harness-play.md](harness-play.md).

**Slots.** Several copies run side by side, one per slot (`tools/slots.py`): slot 0 = `:7` + `workspace/wineprefix`
(everything below, and the default of every tool), slot N ≥ 1 = `:(7+N)` + `workspace/wineprefix-N`. `--slot N` on
`d2run.py`, `d2pilot.py`, `xdrive.py`, `d2hunt.py` and `saves.py` selects one; `slots.py create N | status | stop N`
makes, lists and stops them. A lane only touches the slot(s) its prompt gives it (harness-play.md § Slots). On slot N ≥ 1
every `xdrive` `shot` path gets `-sN` before its extension (`workspace/logs/d2run-last-s1.png`), and `d2pilot.py`
names its screenshots `pilot-sN-*.png` / `stall-sN-*.png`; slot 0 keeps the historical names.

Proven in `run:2026-10-11-seed-tree` (plan 0003 Phase 2). It needs no human and never touches
the user's screen.

**Pieces**

| Piece | Path | Role |
|---|---|---|
| game dir | `workspace/runtime/game/` | `game.exe` (pinned sha256), the signed `binkw32`/`ijl11`/`smackw32` DLLs, `d2.lng` and the MPQs, all copied or symlinked from the **1.14b reference** extraction (`workspace/reference/extracted/1.14b-{d2,d2lod}/{PC,Common}/`). No PlugY, no wrapper DLLs, nothing from `workspace/install/app/` except `game.exe` and the three signed DLLs. Without `d2.lng` the game stops at "Unable to start LNG manager" when it enters a game. |
| prefix | `workspace/wineprefix/` (slot N: `workspace/wineprefix-N/`) | plain `wineboot -i` prefix (wine 11, new wow64: the game is 32-bit code in a 64-bit process); a slot's prefix is a clone made by `tools/slots.py create N`. No prefix holds game files: the registry's `InstallPath` is `workspace/runtime/game`. |
| display | Xwayland `:7` (slot N: `:(7+N)`) | rootful Xwayland, kept on Hyprland's hidden special workspace `d2harness` by a session window rule. `tools/d2run.py` starts both if missing. |
| input/screens | `tools/xdrive.py` | XTEST clicks/keys and `XGetImage` screenshots on `:7` (or `--slot N`) through ctypes. `--window "Diablo II"` makes coordinates window-relative. |
| launcher | `tools/d2run.py` | starts the game with `-w -ns -seed N [--game-args]`, plays a steps file, then `exec`s gdb on the game process |
| breakpoints | `tools/gdb/*.gdb` | gdb command files: `break *ADDR` + `commands … printf … continue` |
| menu steps | `tools/gdb/enter-sp.steps` | main menu → Single Player → OK on the first saved character |

**Run**

```bash
python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/seed-tree.gdb \
    --steps tools/gdb/enter-sp.steps --after 10 [--game-args "-act 2"] --log workspace/logs/run-X.log
python3 -I tools/rng.py seedtree workspace/logs/run-X.log      # check against the model
```

`seed-tree.gdb` logs the game, act, level and room seeds, the active-room activation (RRESEED/RACT/AROOM) and the
server/client unit seeds. `tools/gdb/entropy.gdb` with `--seed 0` (not applied, so the clock path runs) logs the
`RNG_EntropySeed` inputs. `rng.py seedtree` checks every line type (run:2026-10-11-seed-tree-p1).

One run takes about 60 s. The log starts with a `# d2run seed=… args=…` header, then one line
per breakpoint hit. The steps file ends with a screenshot (`workspace/logs/d2run-last.png`). Look at
it whenever a run logs nothing.

**Why it is built this way (the traps)**

- `kernel.yama.ptrace_scope = 1`: only an ancestor may ptrace. `winedbg --gdb <pid>` (error 5) and
  `gdb -p` from a shell both fail, and `winedbg --gdb game.exe` hung. Wine's `start.exe` exits after
  spawning `game.exe`, so the game is reparented to the nearest subreaper. `d2run.py` makes itself a
  subreaper (`prctl(PR_SET_CHILD_SUBREAPER)`), waits for the game to become its child, then
  `exec`s gdb. gdb keeps the PID, so it is the game's ancestor.
- gdb on wow64: use the 32-bit register views (`$esi`, `$ebx`…), and set `displaced-stepping off`,
  because gdb's amd64 decoder can't relocate 32-bit instructions. `handle all nostop noprint pass` keeps
  wine's own signals out of the way. The "architecture … not compatible" warning is harmless.
- Breakpoints stop the thread. Keep `commands` short (`printf` + `continue`). About 500 hits per game
  entry is fine.
- Input: never move wine's windows with X calls, because wine keeps its own idea of the window position
  and clicks land in the wrong place. The game's **first click only activates the window**, so steps
  start with a click on empty background. Hold the button about 0.25 s, since the game samples input per frame.
- Never run the game on the user's display (`:0`). Wine windows open on the active workspace, in
  front of the user's work. The 1.14d menus also accept stray clicks there: a character was
  created by accident in the first test.
- The driver child (steps, then `--after`, then `wineserver -k`) writes `workspace/runtime/d2run-driver.pid`
  (slot N: `d2run-driver-slotN.pid`) and exits without `wineserver -k` once its game is gone; a new `d2run.py` on the
  same slot kills a live stale driver first. Before a run, `python3 -I tools/slots.py status` should show no driver
  left on your slot from an older run (timers from before the fix fire `wineserver -k` into a later run's game).
  The log header ends with `slot=N`.
- Memory cap: `d2run.py` first re-execs itself in its own systemd user scope `d2run-<pid>.scope` (MemoryMax 4G,
  MemorySwapMax 1G; a run takes about 0.5 GB), and each Xwayland it starts gets its own 1G scope. On 2026-10-15
  systemd-oomd killed the whole editor scope (every lane at once) when RAM and swap passed 90%; capped, a runaway run
  is stopped alone. A run that hit the cap ends early, and `journalctl --user -u 'd2run-*'` shows `oom-kill`.
  `--mem-max 8G` raises it for one run, `--mem-max off` drops it. Keep large dumps in `workspace/`, not `/tmp`
  (a tmpfs, held in RAM).
- Room-level DRLG logging: `tools/gdb/drlg-roomk.gdb` (gdb Python, JSON lines), checked by
  `python3 -I tools/drlg.py roomk <log>…` (run:2026-10-11-drlg-roomk). Scripted walks drift when many rooms
  build under the logger; take a `shot` after each click, or let the owner play.
- `pkill -f game.exe` from a shell kills the shell itself, because the pattern is in its own command line, and it
  would kill every slot's game. Use `python3 -I tools/slots.py stop N` (or `WINEPREFIX=<slot prefix> wineserver -k`).
- Saves live in `workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II/` (slot N: under
  `workspace/wineprefix-N/`). The harness
  character is `seedtest` (Barbarian, created through `xdrive`). Keep only it there, so it is
  preselected on the character screen. Stray saves go to `workspace/runtime/saves-backup/`.

**Switches that help**

- `-seed N` sets the map seed (`g_SeedOverride`; N = 0 means none, see `rng/0002`).
- `-act N` (1–5) starts a fresh character directly in act N, so that act's `DRLG_ActCreate` runs.
- `-direct -txt` loads loose `.txt` tables (classic modding switch, `[I]` in `data/0001`). It is the
  way to change one table row and observe the effect.
- `d2run.py --sound` omits `-ns`. Use it for owner-played runs: no steps file, a long `--after`, and the owner moves
  the `:7` window to a visible workspace and plays (run:2026-10-12-drlg-gen, owner-run addendum).
- Save logging: `tools/gdb/d2s-io.gdb` logs every save written (header sources, items, the whole buffer) and read
  (checksum, map-seed test, stats, items, `D2S_LoadFinish`, error code), plus drops (`CPOST`) and `.tbl` crcs;
  `python3 -I tools/d2sio.py check <excel-dir> <log> [saved.d2s…]` compares them (run:2026-10-12-d2s-io). *Save and
  Exit* is `key Escape` then `click 400 262`; afterwards the game is at the main menu, and *Single Player* → *OK*
  reloads the same save in the same process. Copy a written save **from** the saves directory before `restore`.
- `d2run.py --game-dir <dir>` starts the game elsewhere (a copy of `game/` with loose `data/…` files for `-direct`;
  pass switches as `--game-args=-direct`). A start-up fatal leaves `BlizzardError/<time>/Crash.txt` in that dir.
- `xdrive.py keydown Alt_L` / `keyup Alt_L` hold a key (item labels on the ground: click a label to pick it up).
- Test characters: `python3 -I tools/d2s.py setwp` sets waypoints, and `python3 -I tools/d2s.py setstats <excel> <in.d2s>
  <out.d2s> <stat>=<value>…` sets character stats (e.g. raise a sample to level 50) and re-checksums. Swap it in
  with `python3 -I tools/saves.py [--slot N] aside <tag>`, then `install <tag> <out.d2s>…`, run, and `restore <tag>`
  (sha256 checked against the manifest; the aside copy is kept on any mismatch). Slot 0's asides are
  `workspace/runtime/saves-aside-<tag>`, slot N's `workspace/runtime/slot-N/saves-aside-<tag>`; a tag restores only
  into its own slot. On slot N ≥ 1 an empty saves directory (a fresh `slots.py create N`) is set aside as an empty
  manifest, so `restore` returns it to empty; slot 0 refuses an empty `aside`. The three refuse while the slot is busy (a `game.exe` in its prefix, or a `d2run.py` on it or on
  a slot its command line does not tell); `status` shows the directory, open asides and the harness state. This tool is allow-listed in
  `.claude/settings.json`; do not move or delete saves by hand.

### Inventory actions (plan 0029, run:2026-10-15-sockets)

`tools/d2pilot.py insert <log> TOKEN… --slot N` plays inventory clicks against a `tools/gdb/sockets.gdb` log:
`A>B` picks the item at cell A up and clicks it onto the centre of footprint B, then waits for the logger's answer
(`INSX` inserted or refused, or a client swap `PKT` 0x1F, which it undoes); `key:i`, `click:CELL`, `rclick:CELL`,
`sleep:S`, `shot:PATH`. Cells are window-relative on the 800x600 frame, measured once from screenshots (no y scaling:
clicks at screenshot coordinates landed):

| page | cell (c, r) top-left | size | notes |
|---|---|---|---|
| `inv:c,r[,w,h]` | (418 + 29c, 316 + 29r) | 10 x 4 | `key i` |
| `cube:c,r[,w,h]` | (198 + 29c, 199 + 29r) | 3 x 4 | right-click the cube in the inventory; the inventory and paper doll stay open beside it |
| `eq:SLOT` | head (562, 92), tors (562, 177), rarm (447, 163), larm (678, 163), neck (620, 104), glov (447, 266), belt (562, 252), feet (678, 266), rrin (505, 252), lrin (620, 252) | | paper doll |

A footprint `c,r,w,h` is clicked at its centre, so a swapped parent goes back to its own cells. `tools/socket_sessions.py`
writes one recipe (`tools/d2s_recipes/sock-*.json`) and one token list (`tools/gdb/sock-*.plan`) per session.

### Cube sessions (plan 0030, run:2026-10-15-cube)

`tools/d2pilot.py cube <log> --slot N --plan tools/gdb/cube-<name>.plan --ins-gap 1.2 --pick-wait 0.5` plays a cube
session against a `tools/gdb/cube.gdb` log. Tokens: the insert ones (`key:`, `click:`, `rclick:`, `xy:`, `sleep:`,
`shot:`), `mv:A>B` (move an item between cells), `tm` (press Transmute at (240, 340), wait for the CUBX line, print the
row and the outputs), `out:inv:x,y,w,h` (pick the output up at the cube cell its CUBX line gives, put it there).
The panels cover the whole window, so there is no floor to drop on; a 1 x 1 output lands at cube (2, 3), larger
ones at (0, 0). `tools/cube_sessions.py write` writes one recipe and one plan per session; check with
`python3 -I tools/cube.py check <logs>`. Wait about a second after `tm` before moving the output: the client shows it
late, and a click into an empty cell desynchronises the rest of the plan.

### New characters and level-ups (plan 0034, run:2026-10-16-player)

`tools/player_sessions.py newchar --slot N --tag TAG --out DIR --seed S SPEC…` creates characters through the menu in
one game process (`tools/gdb/player.gdb`), Save and Exit after each; SPEC is `cls[:x|c][:h]` (`ama sor nec pal bar
dru asn`, expansion or classic, hardcore). Menu coordinates, window-relative on the 800x600 frame, measured once
from screenshots:

| screen | control | (x, y) |
|---|---|---|
| main menu | SINGLE PLAYER | (400, 307) |
| character select (once a character exists) | CREATE NEW CHARACTER | (115, 500) |
| Select Hero Class | Amazon, Assassin, Necromancer, Barbarian, Paladin, Sorceress, Druid | (100, 310), (200, 310), (300, 300), (400, 300), (520, 300), (620, 320), (720, 310) |
| Select Hero Class (after a class) | EXPANSION CHARACTER box (checked by default), HARDCORE box, OK | (326, 533), (326, 553), (690, 556) |
| hardcore warning box | OK | (468, 322) |

The name field has the focus after the class click; `type` enters lower case. With no character the menu goes from
SINGLE PLAYER straight to the class screen; `--game-args "-act N"` starts the new character in act N. A level-up
session (`player_sessions.py levelup … [--diff hell] [--melee] SAVE`) installs a save, enters with
`enter-normal.steps`/`enter-hell.steps`, then runs `d2pilot.py explore --any-level` (Nova; `--walk --melee`: walk and
left-click the nearest live monster outside town) until the log has a `LUX` line.

### Calc sessions (plan 0035, run:2026-10-16-calc)
`tools/gdb/calc.gdb` logs every `CALC_Eval` call (`CE`/`CX`) with its variable reads (`CV`/`CVR`) and function
calls (`CF`/`CFR`); `calc-field.gdb` adds the pilot's loggers. `tools/calc_sessions.py write` writes one recipe per
class (`calc-<cls>.json`, `calc-<cls>-field.json` starting in Act IV) and two step files: `calc-<cls>-hover.steps`
(skill tree at window (440 + 68·(col−1), 97 + 69·(row−1)), tabs at x 675, y 430/325/215 for pages 1/2/3; then the
potions) and `calc-<cls>-cast.steps` (F1–F8, three right clicks). The skill tree's description evaluates about 150
formulas a second while the pointer rests on a skill. Check with `python3 -I tools/calc.py check <excel-dir> <logs>`.
A fresh Act I character starts beside Warriv, not the waypoint: start field sessions in Act IV (progression 15,
difficulty bytes 131) so `d2pilot.py farm --wp 1,2` finds the waypoint.

### NPC actions (plan 0031, run:2026-10-15-vendors)

`tools/d2pilot.py npc <log> <name> trade|gamble|hire --slot N [--repeat K] [--stay] [--buy ROW] [-v]` opens a town NPC's trade,
gamble or hire window, steered by the `NPC` (every town-NPC unit, `[class, id, mode, x, y]`), `OBJP` (the town
waypoint), `OBJS` (every object) lines of `tools/gdb/vendors.py` and the `PLR`/`CB`/`RL`/`WRP` lines of
`tools/gdb/pilot.py`; a logger for another plan sources `vendors.py` too (plans 0033, 0032 Phase 2). Per opening:

1. **Find the NPC.** Its unit exists only while the player is near its room: when the log has not seen it, the pilot
   walks first to the NPC's usual place (an offset from the town waypoint, the `NPCS` table in `d2pilot.py`, or
   `--hint DX,DY`), then along breadth-first paths to the nearest cell of the town 30 sub-tiles or more from
   everywhere the player has been. It never leaves the town level (it stops if the player does).
2. **Walk.** Clicks along a breadth-first path over cells free of the player's blocking bits, never within 2
   sub-tiles of an object (a click on the stash opens it) or another NPC, never within 4 of a warp (Lut Gholein's
   sewer), until the NPC is 9 sub-tiles away. Roofs hide some NPCs (Halbu, Larzuk) and eat clicks on the cells under them: after two clicks without a move the pilot takes a 3.5-sub-tile
   step the same way, then random short steps; eight clicks without a move stop it with a screenshot.
3. **Never a stray Escape.** In single player an Escape with no window open brings up the game menu and pauses the
   game, and a walking click could then land on *Save and Exit*. `vendors.py` writes a `TICK` heartbeat every 0.5 s
   while the server runs; after each Escape, and between walking clicks, a log that stopped growing means the game
   is paused, and the pilot presses Escape again until it grows.
4. **The menu.** Clicked 44 px above the NPC's feet. The menu is a translucent box above the NPC: the name, then the
   options 15 px apart, the first one highlighted in blue. The pilot finds that blue line (blue > red + 50, > green
   + 40, > 100), counts the option lines below it by their white text, and clicks option k at the blue line's x and
   y + 15 (k − 1). A greeting or quest text (white text in x 240..560, y 5..130) is ended with Escape and the NPC
   clicked again.
5. **Confirmation.** trade: a `TO` line with gamble 0; gamble: `GBX` (the window built); hire: the hire list on the
   screen (white rows in x 180..620, y 125..360), which the client opens without a packet. `HIRE_BuildStock` runs when
   the NPC is first clicked, not at the menu choice. Escape closes the window (unless `--stay`); closing a gamble
   window frees the player's gamble inventory (`GFREE`), so `--repeat K` gives K fresh gamble lists.

Menus in the state of the vendor saves (every quest done). "Talk" comes and goes (a greeting or news to tell): when
the option count is one more or one less than the table's, the pilot shifts by the first line; extras such as
Larzuk's sockets or Anya's personalisation come after trade, gamble and hire.

| NPC (class) | options | usual place from the waypoint |
|---|---|---|
| Akara (148), Charsi (154) | talk, trade, cancel (Akara in Hell: one more line, after trade) | Act I layouts vary: none |
| Kashya (150) | talk, hire, cancel | none |
| Gheed (147) | talk, trade, gamble, cancel | none |
| Fara (178), Drognan (177), Lysander (202) | talk, trade (Fara: trade/repair), cancel | (49, −7), (20, −52), (47, 27) |
| Elzix (199) | talk, trade, gamble, cancel | (−36, 19) |
| Greiz (198) | talk, hire, cancel | (−35, −31) |
| Ormus (255), Hratli (253) | talk, trade, cancel | (−41, 36), (−34, 117) |
| Alkor (254) | talk, trade, gamble, cancel | (−76, −41) |
| Asheara (252) | talk, **hire, trade**, cancel | (−125, 44) |
| Jamella (405), Halbu (257) | (talk,) trade, gamble / trade/repair, cancel | (39, 39), (39, 4) |
| Malah (513), Larzuk (511) | talk, trade, cancel | (−32, −39), (31, −38) |
| Anya (512) | talk, trade, gamble, cancel | (−8, 46) |
| Qual-Kehk (515) | talk, hire, cancel | (−56, 12) |

`d2pilot.py npc <log> waypoint walk` walks next to the town waypoint (its `OBJP` line); `wpchain --chain "A,1"` then
takes it to act A's town (row 1 of tab A). `wpchain` waits for the log to stop growing, which the `NPC` lines never
let happen in town: cap it (`timeout 30`).

### Hire sessions (plan 0033, run:2026-10-16-hirelings)

`tools/gdb/hirelings.gdb` = `pilot.py` + `vendors.py` (NPC positions, `TICK`, the NPC seed) + `mon-pool.py` (`MLV`) +
`hirelings.py` (hire tables, every `HIRELING_RollEntry`, hires, `MERC_Init`, `MERC_SetLevel` stats, the save's
mercenary header, `MERC_Create`'s act test, `ITEMS_DropMagicFind`). `d2pilot.py npc <log> <seller> hire --buy 1
[--repeat K]` hires the top row of the list after each opening: rows at window (300, 140 + 34·(k − 1)); with a
mercenary already hired the game asks "This Mercenary will replace your current one", Yes at (300, 149); the hire is
confirmed by the `HHX` line, and the NPC menu comes back after it (Escape closes it). The list detection
(`hire_box`, 600 white pixels) misses a list of one or two rows; in `--buy` mode the pilot does not wait for it.
`tools/hireling_sessions.py tour|load|kill|saves` drives one game per session (the Act IV start, `wpchain` capped at
20 s, the sellers in the order Qual-Kehk, Asheara, Kashya, Greiz: the Greiz walk is the least reliable and once
entered the Lut Gholein sewer). Check with `python3 -I tools/hirelings.py check <excel-dir> <logs>` and
`tools/monpool.py check` on the same logs.

### Two clients in one game (plan 0011, run:2026-10-12-two-clients)

The game refuses a second copy in one wine session ("Only one copy of Diablo II may run at a time": `FindWindowA`
on its own window class at `0x004F5610`). The second client therefore runs in **its own prefix and display** (a
second slot), and the two meet in a **TCP/IP game** over `127.0.0.1`. A two-client lane is given two slots; below,
slots 0 and 1. Plan 0011's runs used `workspace/wineprefix2` on `:8` for the joiner; that prefix is kept for the
record (ADR-0008) but is not a slot, and `:8` is now slot 1's display, so new runs use slot 1:

| | host (server) | joiner |
|---|---|---|
| slot | 0: `:7`, `workspace/wineprefix` | 1: `:8`, `workspace/wineprefix-1` (`tools/slots.py create 1`, same hidden workspace rule) |
| saves | `tools/saves.py aside/install/restore` | `tools/saves.py --slot 1 aside/install/restore`, a test character built with `tools/d2s.py` |
| launcher | `d2run.py --gdb …` (gdb on this process) | `d2run.py --slot 1` (no `--gdb`) |
| menus | `tools/gdb/two-host.steps` (Other Multiplayer → TCP/IP → Host → OK) | `tools/gdb/two-join.steps` (… → Join → `127.0.0.1` → OK → OK), started once the host is in game |

```bash
python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/tc-party.gdb --steps tools/gdb/two-host.steps \
    --after 3600 --log workspace/logs/tc-party-N.log &                  # wait ~50 s
python3 -I tools/d2run.py --slot 1 --seed 1 --steps tools/gdb/two-join.steps --after 3600 \
    --log workspace/logs/join-N.log &                                    # wait ~55 s
python3 -I tools/xdrive.py --slot 0 --window "Diablo II" run tools/gdb/two-party-invite.steps
python3 -I tools/xdrive.py --slot 1 --window "Diablo II" run tools/gdb/two-party-accept.steps
python3 -I tools/d2hunt.py --slot 1 findwp      # optional: move the joiner (then click a row on :8)
```

- gdb goes on the **host**: it runs the server game, so `TC_ResolveDrops` and the party count run there (every
  resolver call of the two-client runs was logged by the host's gdb). The joiner is a plain client.
- Each slot has its own driver pidfile (`d2run-driver.pid` for slot 0, `d2run-driver-slot1.pid` for slot 1), and
  each driver's `wineserver -k` reaches only its own prefix. End a session with `tools/slots.py stop` on **both**
  slots.
- Two characters with different names (the host's and the joiner's). The party screen (`p`) lists the other player
  on row 1: `INVITE` / `ACCEPT` / `LEAVE` buttons at window (297,141) and (333,87).
- `tools/gdb/tc-party.gdb` = `tc-drops.gdb` plus `tc-party.py`: at `TC_DropByIndex` entry it logs every player unit
  (`PLR`: id, subtile position, level id, mode, dead flag), the party list (`PTY`) and the source/killer position
  (`KILL`); `tools/tc.py replay` checks every `PARTY` and `PLAYERS` line against them and `-v` prints the distances.
- The game listens on TCP port 4000 while hosting (all interfaces). A TCP/IP character's save is rewritten by the
  game during play (the host's level went up in the saves directory without *Save and Exit*), so restore with
  `saves.py` afterwards as usual.
- `tools/d2hunt.py relaunch` is the unattended loop (relaunch, waypoint, hunt) for one client; `d2hunt.py record`
  records an owner-played session.

## Bit-exact reproduction

When a function is pure enough (RNG, affix filtering, TC resolution given a seed), reimplement it
in `tools/<name>.py` and compare against values captured at runtime (breakpoint logs) or against
the binary run through an emulator (e.g. `unicorn`, if an ADR allows the dependency). A match over
≥1000 inputs counts as corroboration for `[C]`.
