# 0062 — Debug and cut content: developer switches left in the exe, and data and code the stock game never reaches

> **Status:** draft (architect, `lane/plans57`, 2026-10-30), for the owner's approval
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phase 1), archivist (phase 2), spec-writer (phase 3)
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers

## TL;DR

What did the developers leave in the 1.14d `Game.exe` and its data that the stock game never uses? Debug switches and
command-line options, developer-only messages, table rows no spawner, warp or drop reaches, and code paths with no
caller. A reimplementer needs this list for two reasons: the switches that change behaviour (the harness already uses
some command-line options, and `/players` changes drops) must be known, and the unreachable rows must still be loaded
the same way so that indices do not shift. When it is done, a finding lists each item with its anchor and reach
(reachable by a stock option, by a switch, or never), and each switch that changes behaviour is a branch in its
owning spec. No spec row unless owner question 1 asks for one.

## Context

- **Where the pieces live now:** `GameTick`'s debug fault switch at `Game+0x1DC8` (values 1–4) and `g_ServerFps`'s
  setter with no caller, frame/0001 (`[I]`); `RangePow2Plus` with no caller and eight more unreferenced bodies, rng
  (`[C]`); unread table columns, data/0001 and data/excel; MonStats rows with no stock spawner and class 560 with no
  row, monsters/pool E2; levels 39 and 134 as named boundaries, drlg/outdoor; AI table rows no stock row names, plan
  0052 (the whole AI table, owner 2026-10-27); unused skill and missile functions, plan 0046's function index; the
  `-act` grants and other options the harness drives, player/creation J1 and the harness notes; `/players`,
  items/tc and monsters/stats.
- **The gap:** no single list; the command-line parser and the chat-command table (if any in 1.14d) are unread; the
  unreachable data rows are counted per spec but not together.
- **Dependencies:** none open. The AI and skill catalogues (0052, 0046) feed the "never reached" list as they land;
  this plan cites them rather than waiting.

## Phases

### Phase 1 — The switches, from the code
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G`; no slot)
- **What:** the command-line parser (every option, what it sets, who reads it), any chat or developer command table,
  the debug globals the frame and the game structure carry, and the developer-only client messages (flagged in
  `g_SrvPacketTable`, if plan 0061 has not read them yet).
- **Outputs:** `docs/findings/archaeology/0001-switches.md`; `re/symbols.csv`.
- **Done when:** every option the parser accepts is listed with its target and its readers `[I]` or better, and each
  behaviour-changing switch names the spec section it changes.

### Phase 2 — The unreached data, counted
- **Owner skill:** archivist (no Ghidra)
- **What:** a survey over the tables of rows no stock path reaches, from the readers the specs already name (Levels
  rows with no warp and no waypoint, MonStats rows no pool, TC, summon or preset names, items with no TC, no vendor and
  no recipe, unused states and skills), each with the spec that defines "reach".
- **Outputs:** `docs/findings/archaeology/0002-unreached-rows.md`; `tools/unreached.py`.
- **Done when:** each table's count of unreached rows is reproduced by the tool, and each "unreached" cites the reader
  that would reach it.

### Phase 3 — The behaviour-changing switches into their specs
- **Owner skill:** spec-writer (Sonnet suffices)
- **What:** each Phase 1 switch that changes a specified outcome becomes a branch or an input of its owning spec, with
  the finding's tag; the rest stay in the findings. (The wiki covers reviewed specs only, ADR-0012, so the findings get
  no wiki page unless question 1 makes a row.)
- **Done when:** every behaviour-changing switch is named in its owning spec or listed under its open questions, and
  the gate is green.

## Resources and limits

- One static lane run with one Ghidra; one archivist run; one short spec-writer run. No slot.
- **Estimate:** P1 one reverser run; P2 one archivist run; P3 one short run.

## Owner questions (recommendations)

1. **Row or findings only?** *Recommendation: findings only, no spec row and so no wiki page*; a switch that changes
   behaviour goes into its owning spec as a branch (Phase 3). A row `archaeology` (and a wiki page over it) is the
   alternative if the owner wants the list readable outside the findings.
2. **Priority.** *Recommendation: last of this batch*; it fills a static slot when nothing higher is ready.
3. **Exercise the switches in the harness?** *Recommendation: no*, except the ones the harness already uses.

## Open questions

- Whether 1.14d keeps any developer chat command at all; the plan does not assume one.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 6 (archaeology, low priority); three
  owner questions.
