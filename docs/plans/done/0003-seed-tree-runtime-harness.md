# 0003 — Seed tree to reviewed, and the first runtime harness

> **Status:** done (closed 2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments

## TL;DR

Plan 0001 left the seed tree at all-`[I]` (finding `rng/0002`, spec `rng/seeds.md`, `draft spec`).
This plan closes that work. It applies the review fixes to findings `rng/0001` and `rng/0002`, answers
the open reverser backlog on the seed tree, and builds the first **runtime harness**: `Game.exe`
under wine with `-seed N`, a breakpoint or memory read at a named address, and a logged value.
That harness promotes game → act → level to `[C]`. The `items/tc` corroboration (plan 0004) and
every later `[C]` that needs a live run reuse it. When it's done, `rng/seeds` is `reviewed` and
`docs/findings/rng/experiments.md` holds a repeatable `-seed` run.

## Context

- Research-map row `rng/seeds` (ADR-0002 enabler), status `draft spec`. Its dependency `rng` is
  `reviewed`, with step, range and init `[C]` (run:2026-10-11-rng-emu).
- ADR-0001 § Negative: "Upgrading to `[C]` often needs a wine experiment, which needs a harness".
  The p-code emulator route used for the RNG primitives doesn't scale to code that walks game
  structures, so this harness is needed early.
- Leads: none registered. The d2-landmarks attributions in 0001/0002 are unregistered (see Phase 1).

### Review of plan 0001's findings (architect, 2026-10-11)

Re-decompiled for this review: `RNG_Range` 0x0045C390, `RNG_EntropySeed` 0x00650DE0, `GAME_InitSeeds`
0x0052C280, `GAME_SetSeedOverride` 0x0052C320, `sub_0044D860_ApplySeedOption` 0x0044D860, `DRLG_ActCreate`
0x00642DA0, `DRLG_LevelCreate` 0x00642AE0, `DRLG_RoomActivate` 0x006422A0 and `DUNGEON_RoomCreate`
0x00619890, plus xrefs of `DRLG_LevelCreate` and `DRLG_RoomCreate`. Every anchor resolves and every
summary statement matches the decompile. Tags are honest: `[C]` only where run:2026-10-11-rng-emu
backs it. **Verdict: accept with fixes.** The fixes are Phase 1's first five items:

1. `rng/0001` last summary bullet, "Seeds are not shared: each game object owns its own pair",
   contradicts `rng/0002` § Other seed sites (three creators draw from one seed at `+0xD0`) and the
   accepted spec wording. Restate it as "a draw is one step of a specific seed object, and every
   consumer of that object interleaves in call order".
2. `DRLG_RoomActivate`: the step and the active-room creation happen **only if** `room[+0x54]` has a
   non-zero `+0x18` or `+0x20`. The finding states the step as unconditional. It also passes a flags
   argument (0, 1 or 4, from room `+0x28` bit `0x40000` and `+0x60` bit 0) and `room[+0x54] + 0x14` to
   `DUNGEON_RoomCreate`. Record the condition, and what `room+0x54` is.
3. `DRLG_ActCreate`: after the act-specific draws it calls `0x00641F60`, `0x0061B7E0`, `0x00678AD0`,
   and creates or looks up an initial level when stack arg 3 is non-zero (`DRLG_LevelCreate` +
   `0x006424A0`). Whether any of these draws from the act seed `+0x000` is unrecorded, and the Act II
   tomb draws are only meaningful if the act seed's later consumers are known.
4. `DRLG_LevelCreate` adds `act[+0x470]` and `levelId` as 32-bit ints, so the sum wraps mod 2³². Record
   the width. It answers part of backlog (b). The level-definition record comes from `FUN_0061E470`,
   which should be named once plan 0002 identifies the table.
5. `DRLG_LevelCreate` has six callers besides `DRLG_ActCreate` (`0x00642BB0`, `0x00642BE0`, `0x00642C30`,
   `0x00642D10`, `0x00642F70`, `0x00643060`). A level's seed doesn't depend on which one runs first,
   but the finding should list them, since `drlg/overview` will need the on-demand creation path.

## Phases

### Phase 1 — Finding fixes and the seed-tree backlog
- **Owner skill:** reverser
- **What:** Apply review fixes 1–5 above, then answer the reverser backlog entries on the RNG core and
  the seed tree.
- **Outputs:** updated `docs/findings/rng/0001-rng-core.md`, `docs/findings/rng/0002-seed-tree.md`,
  `re/symbols.csv`, and `docs/sources.md` (or the attributions dropped).
- **Done when:** each of the following is recorded in a finding with a tag and an anchor, and the
  matching backlog entry is struck through with a link:
  - review fixes 1–5;
  - core: the 11 `C5 90 C6 6A` byte matches classified (any in code is a draw site, so name its
    function); a data-reference search for `RNG_RangePow2Plus` 0x00472240; the owner of the `ECX+0x6C`
    seed in 0x005BDFF0;
  - seed tree: the `DRLG_RoomCreate` type dispatch (1 → 0x0067D6D0, 2 → 0x00666630) and whether those
    callees draw; the unit-constructor predicate (room lookup only when the two position arguments
    are not both zero) and whether the pair is really (x, y); whether type 4's 0x00627C90/0x00627DC0 calls
    in 0x00465FD0 draw; type 1 (monsters) not built through 0x00465FD0; the widths of the
    `RNG_EntropySeed` LCG and `config+0x21A`; whether the act index is 0-based; the second
    `DUNGEON_ActCreate` caller (0x0044E100);
  - sources: the d2-landmarks lead and the "community docs say 1 = maze…" line either registered as a
    `src:` id in `docs/sources.md` or the attribution dropped.

### Phase 2 — Runtime harness and the `-seed` experiment
- **Owner skill:** reverser
- **What:** Run the pinned `Game.exe` under wine in `workspace/wineprefix` (single player, `-seed N`,
  windowed), with a method that stops at, or reads memory at, a named address. Use it to log the map
  seed, `act[+0x470]` and the level seeds at `DRLG_LevelCreate`.
- **Outputs:** `tools/` harness script(s) (launch, attach, break, dump), a "Runtime harness" section in
  `.claude/skills/reverser/references/tooling.md`, `run:YYYY-MM-DD-seed-tree` in
  `docs/findings/rng/experiments.md`, and updated tags in `rng/0002`.
- **Done when:**
  - Two runs with the same `N` log identical `act[+0x470]` and level seeds for every level created,
    and a third run with a different `N` differs.
  - `tools/rng.py` (extended with the seed-tree derivation) predicts every logged value from `N`
    alone: `+0x470 = step(init(N)).low`, and level seed = `init(+0x470 + levelId)`. Bit-exact for every
    logged level.
  - Where the method can reach them, the Act II tomb pair and room seeds `+0x14` are logged too and
    predicted.
  - The game → act → level chain in `rng/0002` is promoted to `[C]` with the run anchor. Anything the
    run didn't reach stays `[I]`.
  - The harness is written up well enough for another session to rerun the experiment from the
    tooling doc alone.

### Phase 3 — Spec update: rng and rng/seeds
- **Owner skill:** spec-writer
- **What:** Carry the Phase 1 and 2 results into `docs/specs/rng/README.md` and `docs/specs/rng/seeds.md`,
  and clear the spec-writer backlog entry from the plan 0001 close.
- **Outputs:** the two spec files, plus the glossary if new terms appear.
- **Done when:** `specs/rng/README.md` frontmatter says `status: reviewed`; `seeds.md` step 7 states the
  literal predicate; the promoted claims cite `run:…-seed-tree`; every closed open question is removed
  or re-pointed; and the architect's review passes, which moves `rng/seeds` to `reviewed`.

## Open questions

- ~~**Harness method (decision):** winedbg, gdb with wine's gdbserver, or an injected logger. The
  method decides how every later experiment is run, so once Phase 2 shows what works, the architect
  writes it up as ADR-0003 (*how runtime experiments are run*).~~ Decided in
  [ADR-0003](../../adrs/0003-runtime-experiments.md): a subreaper launcher that `exec`s gdb, logged breakpoints.
- **Scope guard:** the item and monster seed branches (item seed from creation parameter `+0x48`/`+0x4C`,
  monster spawn seed, the `+0xD0` consumers) stay with plans 0004 and the monster plans. This plan
  only records them as leads it touched.
- The meaning of act `+0x094`/`+0x484` (which tomb is the real one) and `+0x474` (the Act III bit) needs
  their readers. That belongs to `drlg/overview` and the quest work. Don't chase it here unless it is
  on the path.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Approved (human).** No phase started yet.
- **2026-10-11 — Phase 2 done (reverser).** Runtime harness built and proven: rootful Xwayland `:7` on a hidden
  Hyprland workspace, `tools/xdrive.py` (XTEST input, screenshots), `tools/d2run.py` (subreaper launcher that
  `exec`s gdb, because `ptrace_scope = 1` blocks every attach from a non-ancestor), and gdb command files in
  `tools/gdb/`. Write-up: `tooling.md` § Runtime harness. Experiment `run:2026-10-11-seed-tree`: 8 runs (seeds
  12345 ×2, 777, 34844169; all five acts through `-act K`). `tools/rng.py seedtree` predicts **3353/3353** logged
  values from N alone. Same-N runs are identical (rooms included); a different N differs. Promoted to `[C]` in `rng/0002`: override path,
  act seed and `+0x470`, Act II tombs, Act III bit, 0-based act index, the level sum with u32 wrap (seed 34844169 → level 134 seed
  `0x0000000D`), DRLG room seed and `+0x04`. Active-room and unit seeds not reached (`[I]`). New: the act seed has
  data-dependent consumers inside `DRLG_ActCreate` (level-link builder `0x006772C0` at level 6; Act III link code,
  119 steps for seed 12345), recorded in `rng/0002`.
  Phase 1 items closed along the way: fix 4 (u32 width, by run); fix 3 partly (the trailing calls' draws are
  identified and observed, though the Act III code isn't read yet); core (a) the 11 byte matches are nine link
  callbacks, `sub_…_LinkPick`, and all 852 matches are now instructions inside functions; seed tree: `DRLG_RoomCreate` dispatch
  callees don't draw, and the act index is 0-based. Still open for Phase 1: fixes 1, 2 and 5, core (b) and (c), the unit
  predicate, the type 4/type 1 constructor questions, the `RNG_EntropySeed`/`config+0x21A` widths, caller
  `0x0044E100`, and the sources attributions.
- **2026-10-11 — Phase 1 done (reverser).** Every Phase 1 "Done when" item is recorded with a tag and an anchor in
  `rng/0001` or `rng/0002`, and the four matching backlog entries are struck through. Fix 1: the "draw" bullet is restated
  (`[C]`: one step of a specific seed object, consumers interleave). Fix 2: `DRLG_RoomActivate`'s `RoomTile` condition,
  its flags (0/1/4 → active room `+0x34`) and `room+0x54` (a `RoomTile.cpp` record) are recorded. Also found: the
  activation path first **re-seeds the DRLG room from `+0x04`** (`0x0066EE40`), then the room-type code draws k = 50–376
  times. Fix 3: as before (the Act III code is left for `drlg/overview`). Fix 4: done in Phase 2. Fix 5: the six
  get-or-create level callers are listed. Core: (b) `RNG_RangePow2Plus` is dead code (no pointer, no rel32 reference);
  (c) the `+0x6C` seed belongs to the active room, stepped by the server population pass `0x0054EC90`. Seed tree: the
  unit predicate is (x, y) ≠ (0, 0). **Those constructors are client-side**: server units (`0x00555230`, monsters
  included) draw from the game seed `+0xD0` `[C]`. Type 4's calls don't draw, and type 1 errors out. `RNG_EntropySeed` is all
  32-bit `[C]` and `config+0x21A` is a 32-bit int slot `[C]`. The second `DUNGEON_ActCreate` caller `0x0044E100` is the client,
  fed the map seed by message handler 3 (`[C]`: return addresses logged). Sources: the d2-landmarks lines are restated as
  internal hypotheses, and the "community docs" line is replaced by anchors. The optional harness extension is done:
  `seed-tree.gdb` +10 breakpoints, new `entropy.gdb`, `rng.py seedtree` extended. run:2026-10-11-seed-tree-p1:
  **5954/5954** values match over all logs. `re/symbols.csv` +26 rows, 6 tags raised, `import-symbols` OK. Handoff:
  spec-writer for Phase 3 (backlog entry lists the three places where `seeds.md` changes, notably that step 7 describes the
  client constructor). Then architect review.
- **2026-10-11 — Phase 3 done (spec-writer).** `specs/rng/README.md`: `status: reviewed` (per the plan 0001 close); the
  "draw" definition restated and `[C]` (run:2026-10-11-seed-tree-p1); `RNG_RangePow2Plus` marked dead code; the 852 byte
  matches stated as draw sites; three closed open questions removed. Tags C 22 / I 8 / L 1. `specs/rng/seeds.md` rewritten from
  `rng/0002`: steps 1–5 `[C]` (run:2026-10-11-seed-tree), clock path, `RNG_EntropySeed` and the 32-bit `config+0x21A` `[C]`;
  server and client act copies (step 3, note 3); new step 6 (re-seed from `+0x04`, k room-type draws, activation draw only if
  the `RoomTile` test passes; server and client active-room seeds can differ); step 7 split into 7a, server units from game
  `+0xD0` `[C]`, and 7b, the client constructors with the literal predicate (x ≠ 0 or y ≠ 0, `[I]`). The worked example is now
  **observed** (seed 12345 through one active room and the first server units, plus the u32 wrap for 34844169). Tags C 51 /
  I 17 / L 7. The seven open questions all point at later owners (`drlg/overview` ×3, items plan 0004 ×2, monster/object
  plans, `monsters/spawn`); none blocks the seed tree itself. The active-room seed stays implementable only by running the
  room-type code (k), which is stated in step note 6. Glossary +3 (game seed, DRLG/active room, server/client act copy).
  The three spec-writer backlog entries are struck through. `seeds.md` stays `status: draft` until the architect's review
  moves `rng/seeds` to `reviewed`.
- **2026-10-11 — Reviewed and closed (architect).** Verdict: **accept with fixes**; no blocking finding.
  `specs/rng/README.md` (already `reviewed` per the plan 0001 close) holds up: the restated "draw" definition is `[C]`
  on a named run that shows game-seed consumers interleaving, and `RangePow2Plus` is correctly `[I]` dead code.
  `specs/rng/seeds.md`: 31 `fn:`/`data:` anchors spot-checked across both specs, and all of them resolve in `re/symbols.csv`. The tag counts in both
  frontmatters match the bodies (22/8/1, 51/17/7), and every `[L]` sits under *Open questions*. Every summary statement of
  [rng/0002 § Active room and § Units](../../findings/rng/0002-seed-tree.md#active-room) is carried over with the same tag.
  The worked example was recomputed by an independent model (not `tools/rng.py`) and matches every row. The rows were then
  found in `run-p1-12345-a.log`: level 1 room 3 `+0x04 = F923BEE2`, RACT after k = 64 `2CE81EC1:55A43D6F`, AROOM `flags=0` in the
  server act (DACT `0x0053ACA5`), the player's SUNIT `B7A5C418`, the first item `8F16A0F0`, and the next unit's pre-seed `FD29EDF2:3BAE5B0E`.
  The plan's Phase 3 *Done when* holds: step 7b states the literal predicate, the promoted claims cite both runs, and the closed
  open questions are gone.
  **Judgement on k:** an acceptable deferral, not a blocker. The spec defines the active-room seed exactly as
  `Init(Step^(k+1)(Init(R[+0x04])).low)`, so the seed-tree part is complete. k is the draw count of the room-content code, which is
  DRLG behaviour, and the spec says so where a reimplementer would look (step note 6) and names an owner. `reviewed` attests that
  the spec is correct and complete within its stated scope, and the scope boundary here is explicit. Condition: `drlg/overview`
  must take k as a *Done when*. The research-map row now says so.
  Mixed tags inside a step (step 4 dispatch, 6c flags, 7b predicate, note 2's `-1` case) are fine: each tag sits on the line it covers.
  The server-side active-room consumers are honestly `[I]` in note 6, and the open question is the runtime gap.
  **Fixes (spec-writer, backlog):** (1) set `status: reviewed` in `seeds.md`; (2) note 2 drops the finding's caveat that `atol`
  overflow (text above 2³¹−1) is CRT-dependent and unchecked. State it, and say that seeds ≥ 2³¹ are given as their negative
  decimal; (3) the worked-example row "player (type 0): draw#5" reads against 7a's `if type = 0: return`. Name the player-creation
  caller path (step note 7a) in the row. **Harness method:** [ADR-0003](../../adrs/0003-runtime-experiments.md) written. The reverser → architect
  backlog entries on the method and on the room-type draws are struck through. Research map `rng/seeds` → `reviewed`.
