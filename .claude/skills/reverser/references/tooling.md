# Tooling recipes

Paths assume the repo root as the working directory. `Game.exe` here means
`workspace/install/Game.exe` (the pinned one; check its sha256 against `docs/inventory.md`).

## Ghidra headless

The wrapper is `tools/ghidra.sh` (Plan 0001 phase 4 builds it; until then, use the raw commands).
On Arch, the `ghidra` package installs to `/opt/ghidra`, so `analyzeHeadless` is at
`/opt/ghidra/support/analyzeHeadless`. Verify with `pacman -Ql ghidra | grep analyzeHeadless`.

```bash
# one-time import + auto-analysis (slow: tens of minutes for a ~3.5 MB merged exe)
/opt/ghidra/support/analyzeHeadless workspace/ghidra d2 \
  -import workspace/install/Game.exe -processor x86:LE:32:default -cspec windows \
  -scriptPath re/ghidra_scripts -postScript ImportSymbols.java re/symbols.csv \
  -log workspace/logs/ghidra-import.log

# later runs: operate on the existing program without re-analysis
/opt/ghidra/support/analyzeHeadless workspace/ghidra d2 -process Game.exe -noanalysis \
  -scriptPath re/ghidra_scripts -postScript Decompile.java 0x0045A1B0
```

Scripts in `re/ghidra_scripts/` are **Java** GhidraScripts. They compile at run time and have no
Python dependency. Planned set:
- `ImportSymbols.java <csv>`: create or rename functions and labels from the CSV, and apply signatures.
- `ExportSymbols.java <csv>`: write user-defined symbols back out (sorted, merged with existing confidence/evidence columns).
- `Decompile.java <addr|name> [...]`: print the decompiled C to stdout.
- `Xrefs.java <addr|name>`: callers and callees, one per line.
- `FindBytes.java <hexpattern>`, `FindString.java <text>`: entry-point hunting.
- `ImportTypes.java re/types/*.h`: parse C headers into the data type manager.

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

- Prefix: `WINEPREFIX=$PWD/workspace/wineprefix`. Game dir: `workspace/install/`.
- `Game.exe -w` runs windowed `[L]`. `-direct -txt` makes the game load `.txt` tables from disk instead of the MPQ `[L]`. That is the classic modding switch, and very useful for experiments: change one row, observe the effect.
- Memory inspection: `winedbg` attaches to the process (`winedbg --gdb <pid>` gives a gdb stub), so breakpoints can be set at our addresses to log RNG state or arguments. Record the exact gdb commands in the experiment entry.
- Saves are in the prefix's `Saved Games/Diablo II/` or the install dir, depending on version `[L]`. Back them up before any experiment.
- Any experiment that needs a human (clicking, playing to a state) is a `human` step. Write the exact steps for the user.

## Bit-exact reproduction

When a function is pure enough (RNG, affix filtering, TC resolution given a seed), reimplement it
in `tools/<name>.py` and compare against values captured at runtime (breakpoint logs) or against
the binary run through an emulator (e.g. `unicorn`, if an ADR allows the dependency). A match over
≥1000 inputs counts as corroboration for `[C]`.
