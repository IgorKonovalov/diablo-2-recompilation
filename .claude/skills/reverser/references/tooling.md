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

Proven in `run:2026-10-11-seed-tree` (plan 0003 Phase 2). It needs no human and never touches
the user's screen.

**Pieces**

| Piece | Path | Role |
|---|---|---|
| game dir | `workspace/runtime/game/` | `game.exe` (pinned sha256), the signed `binkw32`/`ijl11`/`smackw32` DLLs, `d2.lng` and the MPQs, all copied or symlinked from the **1.14b reference** extraction (`workspace/reference/extracted/1.14b-{d2,d2lod}/{PC,Common}/`). No PlugY, no wrapper DLLs, nothing from `workspace/install/app/` except `game.exe` and the three signed DLLs. Without `d2.lng` the game stops at "Unable to start LNG manager" when it enters a game. |
| prefix | `workspace/wineprefix/` | plain `wineboot -i` prefix (wine 11, new wow64: the game is 32-bit code in a 64-bit process) |
| display | Xwayland `:7` | rootful Xwayland, kept on Hyprland's hidden special workspace `d2harness` by a session window rule. `tools/d2run.py` starts both if missing. |
| input/screens | `tools/xdrive.py` | XTEST clicks/keys and `XGetImage` screenshots on `:7` through ctypes. `--window "Diablo II"` makes coordinates window-relative. |
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
- `pkill -f game.exe` from a shell kills the shell itself, because the pattern is in its own command line.
  Use `WINEPREFIX=… wineserver -k`.
- Saves live in `workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II/`. The harness
  character is `seedtest` (Barbarian, created through `xdrive`). Keep only it there, so it is
  preselected on the character screen. Stray saves go to `workspace/runtime/saves-backup/`.

**Switches that help**

- `-seed N` sets the map seed (`g_SeedOverride`; N = 0 means none, see `rng/0002`).
- `-act N` (1–5) starts a fresh character directly in act N, so that act's `DRLG_ActCreate` runs.
- `-direct -txt` loads loose `.txt` tables (classic modding switch, `[I]` in `data/0001`). It is the
  way to change one table row and observe the effect.

## Bit-exact reproduction

When a function is pure enough (RNG, affix filtering, TC resolution given a seed), reimplement it
in `tools/<name>.py` and compare against values captured at runtime (breakpoint logs) or against
the binary run through an emulator (e.g. `unicorn`, if an ADR allows the dependency). A match over
≥1000 inputs counts as corroboration for `[C]`.
