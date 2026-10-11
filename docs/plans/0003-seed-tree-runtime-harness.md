# 0003 — Seed tree to reviewed, and the first runtime harness

> **Status:** draft
> **Created:** 2026-10-11
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers

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

- **Harness method (decision):** winedbg, gdb with wine's gdbserver, or an injected logger. The
  method decides how every later experiment is run, so once Phase 2 shows what works, the architect
  writes it up as ADR-0003 (*how runtime experiments are run*).
- **Scope guard:** the item and monster seed branches (item seed from creation parameter `+0x48`/`+0x4C`,
  monster spawn seed, the `+0xD0` consumers) stay with plans 0004 and the monster plans. This plan
  only records them as leads it touched.
- The meaning of act `+0x094`/`+0x484` (which tomb is the real one) and `+0x474` (the Act III bit) needs
  their readers. That belongs to `drlg/overview` and the quest work. Don't chase it here unless it is
  on the path.

## Implementation log

_(lanes append dated entries as phases land)_
