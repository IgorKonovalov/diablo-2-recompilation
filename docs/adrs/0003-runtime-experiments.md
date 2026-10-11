# ADR-0003 — How runtime experiments are run: wine, a subreaper launcher that becomes gdb, logged breakpoints

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0003-seed-tree-runtime-harness (closed); used next by 0004 and 0005 Phase 4

## Context

ADR-0001 makes a `run:` anchor one of the four ways to corroborate a claim, and notes that `[C]`
"often needs a wine experiment, which needs a harness". Plan 0003 left the method open ("winedbg,
gdb with wine's gdbserver, or an injected logger") until Phase 2 showed what works on this machine.
The p-code emulator used for the RNG primitives (run:2026-10-11-rng-emu) covers pure functions
only. It can't follow code that walks live game structures.

Phase 2 and the Phase 1 extension tried the candidates. The host has `kernel.yama.ptrace_scope = 1`,
so only an ancestor process may ptrace. `winedbg --gdb <pid>` fails with error 5, `gdb -p` from a
shell fails, and `winedbg --gdb game.exe` hung. Wine's `start.exe` exits after it spawns `game.exe`,
so the game is reparented away from whoever launched it. The game's windows also open on the active
workspace and accept stray input there. A character was created by accident in the first test.

What worked: `tools/d2run.py` marks itself a child subreaper (`PR_SET_CHILD_SUBREAPER`), launches the
game under wine with `-w -ns -seed N`, drives the menus with XTEST on a separate rootful Xwayland
display (`:7`, hidden workspace), waits for the game to become its child, then `exec`s gdb, which keeps
the PID and so is the game's ancestor. Breakpoints come from command files in `tools/gdb/`
(`break *ADDR`, `printf`, `continue`). Two experiment records (run:2026-10-11-seed-tree,
run:2026-10-11-seed-tree-p1, 12 runs) logged 5954 values, and `tools/rng.py seedtree` predicted all
of them from N alone. Same-N runs were identical once heap pointers were masked.

## Decision

Runtime experiments on `Game.exe` use this harness: the pinned binary under wine in
`workspace/wineprefix`, launched by `tools/d2run.py` on the isolated display, never on the user's
display, with the seed set by the game's own `-seed N` switch and observations taken by gdb
breakpoint command files kept in `tools/gdb/`. A breakpoint prints and continues. It never writes
game memory or registers. Each experiment's raw log goes to `workspace/logs/`. Its record in
`experiments.md` names the exact command lines, the `.gdb` and steps files and the checker. A
`run:` anchor counts as corroboration only when a `tools/` checker or model reproduces the logged
values from the recorded inputs, or when the record states the observed values the claim depends on.
The operational detail (pieces, traps, switches) lives in
`.claude/skills/reverser/references/tooling.md` § Runtime harness and is kept current there. The
p-code emulator stays the method for pure functions.

## Consequences

### Positive

- Read-only observation of the unmodified pinned binary. The process image is the one the anchors
  refer to, with no injected code, so the run and the static read can't disagree because of the method.
- Reproducible from the record alone. Determinism under `-seed` is itself checked (same-N runs diff clean).
- Unattended: no human input and nothing on the user's screen, so a lane can run experiments mid-task.
- Every later `[C]` that needs a live run (items/tc in plan 0004, the `.d2s` work in plan 0005 Phase 4,
  monster spawning) reuses the same launcher, steps files and log format.

### Negative

- **A breakpoint sees only code the run reaches.** The menu steps enter the Act I town, so the
  server population pass (`0x0054EC90`) and anything that needs combat, travel or drops never fired.
  Reaching them needs longer steps files (walking, killing, `-act K`) or a saved character placed
  where the code runs. Until then, such claims stay `[I]`.
- **Host-specific.** The display trick depends on Hyprland, rootful Xwayland and XTEST. Another
  host needs its own isolated display, and the launcher needs a subreaper-capable Linux kernel.
- **Throughput and timing.** Every hit stops the thread. About 500 hits per game entry is fine, but
  a hot path (every RNG step) would slow the game and change real-time behaviour. That doesn't
  matter for seed-driven logic, but it rules out timing questions.
- **One process holds server and client.** Single player runs both, so breakpoints in shared code
  fire for both copies and the log has to tell them apart (return address, act pointer).
- Menu steps are pixel coordinates on the 1.14d menus, and they break if the window size or the
  save list changes. The harness keeps exactly one character (`seedtest`) for that reason.

### Neutral

- gdb on wow64 needs the 32-bit register views and `displaced-stepping off`. This is recorded in tooling.md.
- Logs and saves live under `workspace/` and never enter git. The checker and the command files do.

## Alternatives considered

**winedbg (`--gdb` attach or launch).** Attach fails under `ptrace_scope = 1`, and launch mode hung
before reaching the game. A harness that hangs can't run unattended.

**gdb attach after lowering `ptrace_scope`.** Rejected because it weakens a host security setting
for every process on the user's machine, while the subreaper gets the same result without changing it.

**An injected logger DLL (hooks at named addresses).** This would be faster on hot paths, but it puts
our code in the process and patches the binary in memory, so a `run:` result would have to be checked
for interference from the hook itself. It is kept in reserve for the case the Negative section names
(hot paths), and needs its own ADR if adopted.

**Extending the p-code emulator.** Rejected for structure-walking code: it needs a faithful game state
to start from, which only the running game has.
