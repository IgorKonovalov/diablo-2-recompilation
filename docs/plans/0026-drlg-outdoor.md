# 0026 — DRLG outdoor generator: act layouts, borders, paths and substitutions

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** how does a `DrlgType` 3 (outdoor) level become its grid of outdoor rooms? The question covers:
- which act-specific generator runs;
- how it lays out borders, cliffs, rivers, paths and town or level edges;
- where it places the preset areas inside the wilderness (camps, the Tristram and Den entries, Act III's jungle chain,
  Act V's Bloody Foothills siege rows);
- what it draws from the level seed, and in which order.

Today the act layouts are the outdoor-layout ADR-0004 seed oracle of [drlg/overview](../specs/drlg/README.md) step 9 (log lines `OD0`–`OD1`, drlg/0003).
`sub_006750F0_OutdoorRoomsCreate` and the `LvlSub` roll that follow it are already read. This plan reads the
generators, models them in `tools/drlg.py`, and replaces the oracle. When it is done:
- `docs/findings/drlg/0008-outdoor.md` holds the layouts at `[C]` for the logged levels;
- `docs/specs/drlg/outdoor.md` is drafted;
- the overview, room-tiles and monsters/spawn specs point at it instead of at an oracle.

## Context

- Research-map row `drlg/outdoor`: `not started` (moved from `drlg/preset` on 2026-10-13). Its dependency
  [drlg/overview](../specs/drlg/README.md) is reviewed.
- Its neighbour [plan 0022](0022-drlg-maze-warps.md) (maze and warps) is in progress. 0022 owns the act link builder
  and the warp points, and reads only the warp code the outdoor generators share. This plan consumes those warp
  results: its Phase 1 starts after 0022 Phase 1 is accepted, so the two readings don't overlap.
- **Code already named:**
  - `sub_00675320_OutdoorLevelCreate` (no draw, `[I]`) and `sub_00675360_OutdoorLevelBuild` (`[C]`);
  - `sub_006750F0_OutdoorRoomsCreate` (`[C]`) and `sub_0067D540_OutRoomCreate`;
  - the LvlSub family: `LVLSUB_GetRecordByType`, `sub_006706A0_LvlSubRoll` (`[C]`), `sub_006707A0_LvlSubApply`,
    `sub_0066FF50_LvlSubApplyAll`, `sub_00670170_LvlSubApplyPick`, `sub_0066FCF0_LvlSubFits`,
    `sub_0066FE00_LvlSubMatches`, `sub_0066FAD0_LvlSubStamp` and `sub_006704E0_LvlSubLoadDs1` (mostly `[I]`);
  - the outdoor grid cell's bits 16–19, which choose the preset file index (drlg/0003);
  - the grid prepare `0x0067D2D0` (drlg/0002).
- Data:
  - [Levels](../tables/Levels.md) gives `DrlgType`, `SizeX/Y`, `OffsetX/Y`, `SubType`, `SubTheme`, `SubWaypoint`,
    `SubShrine`, `Vis*` and `Warp*`;
  - [LvlPrest](../tables/LvlPrest.md) gives the outdoor border and edge presets (`Outdoors` flag, the per-act DS1
    families);
  - [LvlSub](../tables/LvlSub.md) has a complete layout, with semantics partial;
  - [LvlTypes](../tables/LvlTypes.md).
- Harness: `tools/gdb/` DRLG logging (run:2026-10-12-drlg-gen and the collision run) already logs outdoor rooms and
  their seeds. The run:2026-10-12-drlg-gen logs can be rerun with the oracle replaced.
- Leads: little community documentation covers the outdoor generator. Phase 1b searches and records "none found" if so.

## Phases

### Phase 0 — Outdoor data survey
- **Owner skill:** archivist
- **What:** survey the data the outdoor generators read: the outdoor levels per act, their sizes and offsets, the
  `LvlPrest` rows of each act's border, edge and fill families, and the LvlSub semantics the data can show.
- **Outputs:**
  - `docs/tables/Levels.md` § Outdoor survey;
  - `docs/tables/LvlPrest.md` § Outdoor presets: the families by DS1 path prefix, their sizes and `Files` counts;
  - LvlSub.md semantics completed where the data shows them;
  - a `tools/outdoor_survey.py` command, gate survey `outdoor`, with a baseline.
- **Done when:** for each act, one command prints:
  - the outdoor levels with size and offset;
  - the preset families the act's generator can place, with DS1 sizes;
  - the LvlSub types each level rolls.

  Layouts are `[C]` by data; meanings stay `[L]`.

### Phase 1 — Read the act generators
- **Owner skill:** reverser
- **What:** read the outdoor generator of each act that `OutdoorLevelBuild` dispatches to, then choose the Phase 2
  boundary.
- **Outputs:**
  - `docs/findings/drlg/0008-outdoor.md`;
  - `re/symbols.csv` rows (subsystem `drlg/outdoor`);
  - `re/types/` additions (the outdoor grid and its cell bits).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the dispatch:** which generator each outdoor level runs, by act and level id;
  - **per act:** the grid size, how borders and level edges are laid, how paths, rivers and cliffs are drawn (if
    drawn), and how preset areas are positioned. Every level-seed draw is listed in order, with its range;
  - **the cell bits:** how the grid cells encode the preset file index (bits 16–19), the warp id (20–25, shared with
    0022) and the other flags;
  - **the room split:** how the grid becomes `OutdoorRoomsCreate` rooms, as far as drlg/overview doesn't already say;
  - **the LvlSub step:** its remaining `[I]` functions, as they apply to the act grids;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register community documents on outdoor map generation (wilderness layouts, the Act III
  jungle chain, the Act V siege rows). Compare blind. Downloads go to the scratchpad only.
- **Outputs:** `docs/sources.md` entries or a "none found" note listing the searches made; verdicts, if any, in the
  finding's *Leads used*.
- **Done when:** each layout claim carries a verdict or `not covered`.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  most of the work is a level walk with no fighting)
- **What:** extend `tools/drlg.py` with the outdoor generators, replace the outdoor-layout oracle, and rerun the
  run:2026-10-12-drlg-gen logs. Log a new run over the outdoor levels of all five acts.
- **Logging:** at each outdoor level build: the level, the seed, every generator draw, the final grid (cell values),
  the rooms created with their preset file indices, and the seed at exit.
- **Done when:** a run `run:YYYY-MM-DD-drlg-outdoor` shows, with 0 mismatches against the model:
  - every outdoor level of Acts I–V generated at least three times (different game seeds), in at least two
    difficulties, classic and expansion where the level exists in both;
  - the final grid matches cell for cell, and the room list and file indices match;
  - the level seed after the generator matches;
  - the Phase 1b cases, if any.

  In-scope claims go to `[C]`.

### Phase 3 — Spec: drlg/outdoor
- **Owner skill:** spec-writer
- **What:**
  - write `docs/specs/drlg/outdoor.md` and link it from the drlg README;
  - replace the outdoor-layout oracle rows in drlg/overview and the outdoor notes in room-tiles and monsters/spawn
    with links.
- **Done when:**
  - the spec follows the template, and every statement is tagged;
  - it gives each act's generator as an ordered draw sequence, with a Mermaid diagram of the grid layout per act;
  - it has worked examples from the run;
  - the architect's review passes.

## Open questions

- Town levels (DrlgType 2 presets) are drlg/preset. Only the wilderness that borders a town is in scope.
- Objects that the outdoor DS1s carry are drlg/preset and plan 0023. Only their placement inside the grid is in
  scope.

## Implementation log

- 2026-10-14 (architect): drafted and approved on the owner's request. Phase 0 (archivist) may start.
- **2026-10-14 — Phase 0 landed (archivist, branch `lane/a0026p0`).** New `tools/outdoor_survey.py <root> [--quiet] [--act N]`,
  registered as gate survey `outdoor` (baseline `tools/gate/baselines/outdoor.txt`, generated by the survey). For each
  act, `--act N` prints the outdoor levels with size and offset, the preset families the act's generator can place
  with their DS1 sizes, and the LvlSub records each level rolls. Docs:
  [Levels § Outdoor survey](../tables/Levels.md#outdoor-survey-plan-0026-phase-0),
  [LvlPrest § Outdoor presets](../tables/LvlPrest.md#outdoor-presets-plan-0026-phase-0),
  [LvlSub § Outdoor survey](../tables/LvlSub.md#outdoor-survey-plan-0026-phase-0). Every count is `[C]` by command.
  Meanings stay `[L]`.
  - **Levels:** 31 outdoor levels, 8 level types. Per generator act: I 8 (2–7, 17, 39), II 7 (41–46 and level 134 by
    the drlg/0003 override), III 8 (76–83), IV 4 (104–106, 108), V 4 (110–112, 117). Sizes are equal in all
    difficulties and are multiples of 8. **Surprise:** Barricade 1 and 2 (111, 112) have −1 in every size and offset cell.
  - **Presets:** the survey rule finds 450 records in 126 families (I 56/27, II 52/27, III 156/26, IV 50/13,
    V 136/33). No record fits two acts. Every DS1 size equals its record's size. Several level sizes are exact
    sums of family record sizes: Siege 1 = 15 × 16×48 strips, Jungle = 2 × 6 cells of 32 with 64×32 `Head`/`Tail`,
    Kurast 4 = the 48×16 `Bridge`, Travincal = 16+32+16 × 32+32, Diablo 1 = 5 × 5 of 24×24. Acts I, II and IV each
    have a 12-record 8×8 border family, and Act III's `Jungle` 530–544 is named in maze exit-mask order.
  - **Rule limits:** types 22 and 28 are shared with maze levels, so the `Mephisto` families (769–795) and the
    Act IV Lava records (836, 852–862) are listed although they may be maze records.
  - **LvlSub:** draws per out room are 6 (Act I wilderness), 7 (Act II deserts and 134), 3 (Barricade 1/2),
    2 (Barricade Snow) and 0 elsewhere (every Act III/IV level, Siege, Graveyard, Moo Moo Farm). **Surprise:**
    the five records with `BordType` ≠ −1 (`Type` 0–3, 12) are exactly the five `tag_type` 2 DS1s, the five with
    all-zero `Prob`/`Trials`/`Max`/`Dt1Mask`, and the five types no level names. `Expansion` 1 marks exactly the
    `Type` 10–12 records. `GridSize` 2 occurs only on `Barricade`.
  - Questions for Phase 1 are in the backlog (archivist → reverser).
- 2026-10-14 (architect): Phase 0 accepted. Rulings: (1) families grouped by record `Name` with variant tokens removed, as delivered, replace the plan's "by DS1 path prefix" (path stems would make every record its own family). (2) The data-only act-membership rule stands, with its blind spot flagged: records of the shared types 22 and 28 (`Mephisto *` 769–795, Act IV Lava 836, 852–862) may be maze records; Phase 1 settles it with 0022. (3) The four reverser questions (Barricade size, `tag_type` 2 LvlSub records, shared-type records, bits 16–19 beyond `Files`) are required items of Phase 1.
