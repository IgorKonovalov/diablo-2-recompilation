# ADR-0008 — Two clients in one game: a second prefix and display, a local TCP/IP game, gdb on the host only

> **Status:** accepted (owner, 2026-10-16) on one condition: before any hosting run, the lane makes sure TCP port 4000 cannot be reached from outside loopback (a firewall rule, or a confirmed existing block) and records how in the run record. Host and joiner run on two non-zero slots; slot 0 stays the owner's (ADR-0011 placed the host on slot 0).
> **Date:** 2026-10-12
> **Related plan(s):** 0011-two-client-harness (done); used next by 0014 (player-count cases) and `monsters/stats`

## Context

ADR-0003 fixes how runtime experiments run: one game under wine in `workspace/wineprefix` on the isolated display
`:7`, launched by `tools/d2run.py`, which becomes gdb. Some claims need a second player in the same game: the party
count behind `NoDrop` (items/0001 §6, plan 0004 Phase 2 case (a)), and later player-count scaling in `monsters/stats`
and `monsters/spawn`. A single-player game cannot host a second player.

Plan 0011 Phase 1 (run:2026-10-12-two-clients) tried the options. One wine session refuses a second copy of the game:
`0x004F5610` calls `FindWindowA` and stops with "Only one copy of Diablo II may run at a time". A second plain prefix,
`workspace/wineprefix2`, on its own rootful Xwayland display `:8`, runs a second copy. The two meet in a **TCP/IP**
game: the host on `:7` creates it, the joiner on `:8` joins `127.0.0.1`. While hosting, the game listens on TCP port
4000 on **all interfaces**. Every resolver call ran in the host's process (`g6a` = 2 in every logged call; single
player logs 3), so gdb on the host sees the server side. Run:2026-10-12-tc-party then reproduced 206 calls with
`tools/tc.py replay`, including the party check computed from the logged positions.

The joiner's saves live in the second prefix, which `tools/saves.py` (owner-approved for `workspace/wineprefix` only)
does not cover. TCP/IP character saves are rewritten during play, even when a session ends with `wineserver -k`.

## Decision

A multiplayer experiment runs two copies of the pinned `Game.exe`: the **host** in `workspace/wineprefix` on `:7`,
launched by `tools/d2run.py` with gdb attached exactly as ADR-0003 says, and a **joiner** in `workspace/wineprefix2`
on `:8`, launched by `tools/d2run.py --prefix workspace/wineprefix2 --display :8` with no debugger. They play one
TCP/IP game over `127.0.0.1`, created by the host. Only the host's process is observed; a claim that rests on
client-side state of the joiner needs its own decision. The joiner's characters are tool-built saves (ADR-0003 input),
placed only in `workspace/wineprefix2`, and listed with their sha256 in the run record; the host's saves go through
`tools/saves.py` as before. A session lasts only as long as the run needs, and ends with `wineserver -k` on both
prefixes and no driver left. The recipe lives in `.claude/skills/reverser/references/tooling.md` § "Two clients in one game".

## Consequences

### Positive
- The party, player-count and multiplayer (`g6a` = 2) branches become testable without a second machine.
- The host side is unchanged from ADR-0003, so every existing logger and checker works as before.

### Negative
- **An untrusted binary listens on the network.** While hosting, the game accepts connections on TCP 4000 on every
  interface, not only loopback. It is open for the length of a session only. A firewall rule that drops inbound
  4000 from anything but loopback removes the exposure; until the owner adds one, sessions stay short and are never
  left running unattended.
- The joiner's saves directory is outside `tools/saves.py`'s manifest and restore check. A lane may write it only
  with tool-built characters and must list what it placed.
- TCP/IP saves change during play, so a host save after a session is not the save that went in; the record keeps a
  copy (`workspace/runtime/saves-backup/<plan>/`).
- Two games and two displays double the resource use and the chance of a stray driver killing a later run; the
  per-display driver pidfile is the guard.

### Neutral
- `game+0x6A` (`g6a`) is 2 in these games and 3 in single player; claims that depend on it state which.

## Alternatives considered

Two windows in one prefix lost because the game refuses a second copy per wine session (`0x004F5610`). Two machines
lost on cost and on the debugger: the host would still need the ADR-0003 ancestry trick, and the joiner would be out
of reach. A patched binary without the single-instance check lost because every address claim refers to the pinned,
unmodified `Game.exe`. Open Battle.net emulators lost because they add a third program and ADR-0002 defers network play.
