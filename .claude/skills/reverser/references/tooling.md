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

## Wine experiments

- Prefix: `WINEPREFIX=$PWD/workspace/wineprefix`. Game dir: a clean copy holding only the `game`/`game-unverified` files plus the reference MPQs, not `workspace/install/app/` itself, which carries PlugY and wrapper DLLs (see `docs/formats/installer.md` § Launch path).
- `Game.exe -w` runs windowed `[L]`. `-direct -txt` makes the game load `.txt` tables from disk instead of the MPQ `[L]`. That is the classic modding switch, and very useful for experiments: change one row, observe the effect.
- Memory inspection: `winedbg` attaches to the process (`winedbg --gdb <pid>` gives a gdb stub), so breakpoints can be set at our addresses to log RNG state or arguments. Record the exact gdb commands in the experiment entry.
- Saves are in the prefix's `Saved Games/Diablo II/` or the install dir, depending on version `[L]`. Back them up before any experiment.
- Any experiment that needs a human (clicking, playing to a state) is a `human` step. Write the exact steps for the user.

## Bit-exact reproduction

When a function is pure enough (RNG, affix filtering, TC resolution given a seed), reimplement it
in `tools/<name>.py` and compare against values captured at runtime (breakpoint logs) or against
the binary run through an emulator (e.g. `unicorn`, if an ADR allows the dependency). A match over
≥1000 inputs counts as corroboration for `[C]`.
