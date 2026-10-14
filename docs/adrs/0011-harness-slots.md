# ADR-0011 — Harness slots: several game copies at once, one per display and prefix

> **Status:** accepted
> **Date:** 2026-10-14
> **Related plan(s):** every harness Phase 2 (0021, 0022, 0023, 0024, 0025, 0026); amends ADR-0003 and ADR-0008

## Context

ADR-0003 runs one game under wine in `workspace/wineprefix` on display `:7`. ADR-0008 added a second client
(`workspace/wineprefix2`, display `:8`) only to join the first one's game. Every reproduction phase needs the harness,
and with one copy the harness is the bottleneck of the whole plan queue: static phases run in parallel on per-lane
Ghidra copies, while the harness phases wait for each other. The machine (16 cores, about 16 GB free) can run several
games with gdb at once. Two copies already shared `workspace/runtime/game` in plan 0011.

## Decision

The harness has numbered **slots**. Slot 0 is display `:7` with `workspace/wineprefix` and keeps every historical path.
Slot N (1–8) is display `:(7+N)` with `workspace/wineprefix-N`, a copy of the base prefix with an empty saves
directory, made by `tools/slots.py create N`. All slots start the same `workspace/runtime/game`. `d2run.py`,
`d2pilot.py`, `xdrive.py`, `d2hunt.py` and `saves.py` take `--slot N`. A `--display` or `--prefix` that contradicts it
is an error. Saves, set-aside copies, driver pidfiles and screenshots are per slot. A lane is given its slot or slots
in its prompt and never touches another slot. Cleanup is per slot (`slots.py stop N`), and `wineserver -k` without
that slot's `WINEPREFIX` is never run. A run record names the slot of each session. Slots don't change what a run
proves: each session is still one game with its own seed and log. ADR-0008's two-client games use two slots (slot 0
hosts, slot 1 joins) in place of `wineprefix2`/`:8`. `workspace/wineprefix2` stays as plan 0011's historical prefix.

## Consequences

### Positive

- Harness phases of different plans run side by side, and one phase can spread its sessions over several slots.
- Every tool resolves display and prefix together, so a stray kill or keystroke can't reach another slot.

### Negative

- Each slot costs about 770 MB of prefix (a reflink copy where the filesystem supports it) and a core or more while
  gdb's Python handlers fire. The working budget is 3–4 slots.
- Lane prompts must assign slots, and the architect must track which lane holds which slot.

### Neutral

- Defaults stay on slot 0, so old commands and run records still read correctly.

## Alternatives considered

**Several games in one prefix.** Lost because one `wineserver -k` would end every game, and the saves directory would
be shared.

**Containers or VMs per copy.** Lost because the cost is heavier with no gain over wine prefixes, which already
isolate the saves and the wine session.
