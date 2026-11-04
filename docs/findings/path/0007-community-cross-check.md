# 0007 — Community cross-check of the path findings (plan 0054 Phase 1b)

> **Subsystem:** path/search
> **Question:** what do community documents say about pathing (monsters stuck on corners, Charge, Leap, Whirlwind, Teleport, Blessed Hammer's spiral, the random-walk missiles, corpses as obstacles), and what verdict does each comparable claim get against [path/0001](0001-pathplan-register.md) to [path/0006](0006-holdout.md) and the reviewed specs they rest on?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 1b, `lane/r1b`)   **Status:** reviewed (`lane/r1b`, Tier A, accept with fixes)

No Ghidra, no game, no emulation, no new code reading in the lane; the review read four call sites of the image to check an anchor, named where used. The findings were read first and their statements are
quoted below as they stand; the community pages were fetched in the session (ADR-0007), keyword-scanned for
code before any was read (ADR-0001), and registered in `docs/sources.md` before use. Agreement promotes nothing
(`evidence-rules.md` § Community cross-checks); no finding's or spec's tag changes here. The lane compared against path/0001 to 0006 only; the review widened the base to reviewed specs, tables and other findings, and moved five verdicts.

## Answer (summary)

- **Almost nothing in the community record bears on the path planner.** The search (12 queries, § Search log)
  found no page that describes monster or missile pathing at the level of a planner, a grid or a collision mask.
  What exists is skill-page prose (Whirlwind, Leap, Charge, Blessed Hammer), two column guides with a few
  collision columns, and one floor-flag table, whose first part (values 00 to 04) is aligned and whose other parts are not.
- **15 claims compared: 2 `held`, 7 `held with refinement`, 1 `contradicted`, 5 `not covered`.** All
  agreement is weak: the sources are column guides without a version for these columns (P01, P02, P13), a 2006 list its author calls not final (P06), a wiki page with no patch for its claim (P07, P08) or describe D2R (P09, P10, P11). Nothing is raised on them.
- **One contradiction, outside the planner:** floor flag 01 "allow missiles pass" against skills/missiles D3's own-cell test (P12). [Backlog entry](../../backlog/2026-11-04-architect-reverser+spec-writer-0054-p12-missile-own-cell-bit0-vs-floor.md). It does not touch a statement of path/0001 to 0006 and is not a case of plan 0054. A second entry asks for `unflatDead`'s readers, on which two sources disagree (P04, P14): [entry](../../backlog/2026-11-04-architect-reverser-0054-unflatdead-reader-corpse-walk-or-draw.md).
- **Phase 1b's earlier reason did not hold.** The `lane/p54c` lane's statement, that no registered source held a comparable claim, was kept by its review as "true of `docs/sources.md`" (plan log, ruling 4; [path/0006](0006-holdout.md) § Floors). Two registered sources hold such claims: `src:d2mods-monstats-guide` (article 359: `deadCol`, `SizeX`) and `src:d2dfg-blizzard` (`deadCol`, `unflatDead`, `noGfxHitTest`, and `SizeX` already compared at drlg/0005). (tbl:MonStats2.txt:deadCol)
- **Rejected or unread:** `src:pk-missile-functions-guide` (pseudocode-style formulas of game logic: rejected,
  unread beyond the scan, nothing used); five pages that returned HTTP 402 or 403 (`src:diablowiki-leap-teleport-charge` three of them,
  `src:fandom-diablo-pathing-ai`, and an Icy Veins page in query 2, unregistered; nothing used). `pk-pathfinding-thread` stays rejected for code and was not opened.

## Search log

Standard-mode `WebSearch`, 2026-11-04, 12 queries; then stopped. A result is "kept" when it was fetched and
scanned; the rest were not opened.

| # | Query (shortened) | Came back | Kept |
|---:|---|---|---|
| 1 | D2 monster pathing stuck on corners | Blizzard D2R forum threads on mercenary AI (anecdote, D2R), gamedev.net "AI pathing in something like Diablo" (guess at A*), Fandom "Pathing AI" | none; Fandom 402 |
| 2 | Blessed Hammer spiral path | d2emu, Icy Veins, Gamer Guides, rankedboost, diablowiki, PD2 guides | Gamer Guides (Icy Veins 403) |
| 3 | Teleport, Charge, Leap, Whirlwind blocked by walls | diablowiki Leap / Leap Attack / Teleport, Fandom, Fextralife, PlanetDiablo Whirlwind mini-guide | Fextralife Whirlwind, Leap Attack (diablowiki 403) |
| 4 | corpses block movement | diablowiki Corpse Spitter, Corpulent, MonStats2 scribd copy, D2R forum on Corpse Explosion targeting, OTLand | none (projectile and targeting claims, other games) |
| 5 | "Pathing AI" teleport leap wiki | Fandom Pathing AI and Teleportation, diablowiki Leap, D2R forum | none |
| 6 | Missiles.txt Blessed Hammer modding guide | d2mods.info "Guide to Almost All Missile Functions" | scanned, rejected |
| 7 | MonStats2 collision SizeX flags | d2mods.info articles 359 and 360, scribd copies, Daum Cafe copy | article 359 (already registered) |
| 8 | monsters walk through each other, corpse blocks path, Whirlwind stops | Fextralife Whirlwind, realmsbeyond WW strategy, d2mods article 443, OTLand | Fextralife Whirlwind, article 443 |
| 9 | Charge paladin around obstacles, stops at wall | diablowiki / Fextralife / PureDiablo Charge pages, Lurker Lounge threads | Fextralife Charge (nothing comparable; PureDiablo 403) |
| 10 | collision mask sub-tile flags walkable | article 443, Tristram archive DT1 doc, OpenDiablo2 package docs | article 443 (the DT1 documents are already registered: `src:siramy-dt1-doc`, `src:pk-walkable-thread`) |
| 11 | missile random movement, bounce | Median XL slide deck, Bone Spirit and Frozen Orb wiki pages | none: no movement math anywhere |
| 12 | monster chase, give up, pathfinding range | MonStats guide copies, Lurker Lounge threads on target choice | none |

No readable page came back for **random-walk missiles** (the movement math of Frozen Orb, Lightning Fury and the
like). For **Teleport as a pathing event** the pages the search named returned 403 and were not read, so that is unread, not empty. The Median XL slide deck
(`src:wue-d2-ai-slides`) was already registered. The review added no query; it re-fetched the kept pages and read `src:d2dfg-blizzard`'s MonStats2 section, already registered.

## Leads used

The comparison table is one verdict per claim, in the form of `evidence-rules.md`. "Finding" quotes the
statements with their tags; scopes are stated on both sides. All sources are
community documents of unknown or other patches, so **agreement is weak** and is stated as such.

### The MonStats2 guide (`src:d2mods-monstats-guide`, article 359; no version for these columns: its text cites 1.10+ under `SpawnCol`, its category is "File Guides (1.10 - 1.14)")

- [L] **P01** src:d2mods-monstats-guide: `deadCol` "states whether the unit's corpse collides or not with other
  units." **held with refinement**
  - *Finding (server copy, the planner's grid):* path/0005 C1/C2 `[C]`, "`MonDeathEvent` sets mode 0 and calls
    0x005A6520, which tests `deadCol` (`edx` = 0x13, `+0x06` bit 3, at 0x005A65CD) and, when it is 0, calls
    `UnitCorpseColl(unit, 1)` at 0x005A65D9: the live mark off and a 3×3 of `0x8000` (0x00649FD8), mask and pattern
    untouched." and "C2: `deadCol` 1, the live mark stays." (path/0006: C2 `[C]` for classes 403 and 404, 18 distinct
    dead with no `0x8000` cell and the live mark kept; class 273's server arm `[I]`.) *Client copy:* the tests at
    0x004B05DB and 0x004B09FB call `UnitCorpseColl(unit, 0)`, a plus (path/0005, `[C]` for the client's copy).
  - *Verdict:* the finding agrees on the direction at the server's grid (0x005A65CD): `deadCol` 1 keeps the unit's live mark
    (a corpse that collides like a live monster), `deadCol` 0 takes it off. **Refinement:** `deadCol` 0 does not
    leave the cells free in the grid; it writes a 3×3 of `0x8000` (a plus on the client). Whether that bit blocks
    anything is the finding's `[I]` C4: "`0x8000` is in no move mask read so far", so no planner of path/0001 to
    0006 was seen to refuse it. The guide says "other units", which the findings do not separate from the planner's
    own mask. Weak: no version for this column, and the guide is a column description, not a behaviour test.
  - Anchor: 0x005A65CD, 0x005A65D9, 0x00649FD8, tbl:MonStats2.txt:deadCol.
- [L] **P02** src:d2mods-monstats-guide: `SizeX` and `SizeY` are the "X-diameter in sub-tiles, used for collision and
  proximity checking. It ranges from -1 to 3." **held with refinement**
  - *Finding (the path record, both copies):* path/0001 `[I]`, "`PATH_DynamicCreate` ...: `+0x44` `UNIT_GetSizeX`,
    `+0x48` `PATH_PatternFromSize`" (not emulated), with `MonStats2 +0x08` as `SizeX`; path/0005 T1 `[C]`, "Under
    path flag `0x800` `PathPlan` unmarks a target whose `UNIT_GetSizeX` is not 0, whatever its type
    (0x00649B10–0x00649B25), and re-marks it at the tail (0x00649BD7) when the unmark returned non-zero".
    *Footprint:* [drlg/collision § F](../../specs/drlg/collision.md#f-unit-marks) `[C]`, "monster patterns by `SizeX` 0, 1 or 2 in 9213 compared creation marks"; "only objects read a Y size".
  - *Verdict:* a monster's `SizeX` does feed its collision footprint (`[C]` for the marks, `[I]` for the path record) and a non-zero value gates the target's unmark. **Refinements:** it is a footprint class, not a diameter: size 0 marks nothing, 1 and 2 the same plus, 3 the 3×3 (`g_CollPatternBySize`, as drlg/0005 already ruled against `src:d2dfg-blizzard`). `UNIT_GetSizeY` reads a monster's `+0x09`, and no monster footprint uses it (`[I]`, MonStats2 table doc, drlg/0005 § 5); the two columns are equal in every stock row (`[C]`, MonStats2 table doc), so the data cannot separate them. Stock values are 0 to 3 (45, 12, 356, 196 rows): -1 is not stock. "Proximity checking" is not compared. A size of 0 is a separate branch of T1 (no unmark, "read, not run"). Weak: no version for this column.
  - Anchor: 0x00649B10, 0x00649BD7, fn:sub_00649970_PathPlan@0x00649970, fn:UNIT_GetSizeY@0x006205A0, data:g_CollPatternBySize@0x006EB3DC, tbl:MonStats2.txt:SizeY.
- [L] **P03** src:d2mods-monstats-guide: `NoGfxHitTest` "controls whenever the game uses the x/y diameter settings
  for collision detection" (or "special, superimposed values", the `htTop`..`htHeight` box). **not covered**
  - Finding: no statement in the findings or specs reads the column (`noGfxHitTest`, `+0x004` bit 0, 11 stock rows, in the table doc only) or the `ht*` box; the path code reads the size, not a hit box. See P15, which calls it a mouse selection box. (tbl:MonStats2.txt:noGfxHitTest)
- [L] **P04** src:d2mods-monstats-guide: `unFlatDeath` "states whether the unit's corpse can be walked through or
  not." **not covered**
  - Finding: the game's column is `unflatDead` (`+0x006` bit 4, 9 stock rows, `[C]` in the table doc), and no finding or spec reads it; their corpse statements are all about `deadCol` and the
    marks it selects. This is the one corpse-as-obstacle claim of the search with a named column, and P14 contradicts it from the other side, so the spec's
    Open questions keep it and a backlog entry asks for its readers. (tbl:MonStats2.txt:unflatDead)
- [L] **P05** src:d2mods-monstats-guide (under `SizeX - SizeY`): "while pets do not use this setting towards the players, they can still
  block each other"; necromancers that teleport along with large monsters end with
  all their minions "blocked into the same position". **not covered**
  - Finding: path/0005 gives a pet's route as `[I]` ("`PATH_SetMarkMask(path, 0x100)` at 0x00574D80, which marks,
    when 0x0063EA40 returns 0", callee unfollowed) and nothing on pets against players or on stacking after a
    teleport. No pet-specific mask was read; drlg/collision's monster masks `[I]` and bit table hold `0x1000` for monsters in general, so "block each other" is what the general rule would give, not a comparison for pets. (fn:PATH_MonTestMask@0x00648480)

### The Data File Guide (`src:d2dfg-blizzard`, registered; no version on the page, treated as later than 1.14d)

Added at the review. The lane did not open it for this question.

- [L] **P13** src:d2dfg-blizzard: `deadCol` "If equals 1, then the monster's corpse will have collision with other units." **held with refinement**
  - The same as P01: the direction holds at the server's grid; `deadCol` 0 still writes `0x8000`. Weak: a later build. (0x005A65CD, tbl:MonStats2.txt:deadCol)
- [L] **P14** src:d2dfg-blizzard: `unflatDead` "If equals 1, then ignore the corpse draw order for rendering the sprite on top of others, while the monster is dead." **not covered**
  - No finding reads the bit. It is a drawing statement and P04's is a walking one, so the two sources disagree with each other, and neither is compared with code. (tbl:MonStats2.txt:unflatDead)
- [L] **P15** src:d2dfg-blizzard: `noGfxHitTest` "If equals 1, then enable the mouse selection bounding box functionality around the monster." **not covered**
  - No finding reads the bit. It fits the table doc's `ht*` "hit box", and takes the column away from the path code if true. (tbl:MonStats2.txt:noGfxHitTest)

### The walkable-flags overview (`src:pk-walkable-flags-overview`; 2006, no patch, "shouldn't be considered final")

The page has four tables. **The first, values 00 to 04, has five values under five headers, in order** (raw lines re-read at the review); the other three hold rows of 3 or 4 values under five headers, and no cell of them is used. Flags 01 and 04 are single bits, and `COLL_StampTile` ORs the sub-tile byte unmasked, so each is the grid's bit 0 or bit 2 ([drlg/collision](../../specs/drlg/collision.md) bit table).

- [L] **P06** src:pk-walkable-flags-overview: flag 01: player, minion and monster walk "no"; flag 04: walk "yes", missiles pass "no". **held with refinement**
  - *Finding:* drlg/collision's bit table: bit 0 in `0x3C01`, `0x3401`, `0x1C09`, `0x3F11` `[C]`; bit 2 in flying `0x1804` and wraith `0x804`. skills/missiles D3 `[I]`: a crossed cell with `k & 4` ends a missile. (fn:COLL_StampTile@0x0064C4C0, fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0)
  - *Verdict:* walk at 01 and missiles at 04 hold. **Refinement:** flyers do not test bit 0 and do test bit 2, so "monster walk" is the ground masks only. Jumping, teleport, line of sight, light and the corpse rows are not compared. The grid is the planners' input, so this bears on path/search only through `CB`. Weak: 2006, no patch, not final.
  - Anchor: fn:COLL_StampTile@0x0064C4C0, fn:PATH_MonTestMask@0x00648480, fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0.
- [L] **P12** src:pk-walkable-flags-overview: flag 01: "allow missiles pass" yes. **contradicted**
  - *Finding:* skills/missiles D3 `[I]`, "`c: u16 ← PathCellCollision(path); if c & 5: return 2`", own cell: freed, no hit function, for a do-function-1 missile with a `CollideType`. A cell with bit 0 and not bit 2 therefore frees it, against the table. One of the two is wrong for such a cell; neither is shown by a run. Nothing is demoted: D3 stays `[I]`, the source is weak. [Backlog entry](../../backlog/2026-11-04-architect-reverser+spec-writer-0054-p12-missile-own-cell-bit0-vs-floor.md). Not a statement of a path finding: "the missile's collision is its own" (path/0003 § 8). (fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0)
  - Anchor: fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0, fn:sub_00648EB0_PathCellCollision@0x00648EB0.

### Whirlwind, Leap and Charge (`src:fextralife-d2-whirlwind`; wiki prose on a D2R wiki, no patch for these claims)

Two masks are in play and the lane's first text read one for the other: `testMask` (`+0x50`, set by `PathSetCollMask` 0x00648CE0) is what a move tests, `markMask` (`+0x4C`, set by `PATH_SetMarkMask` 0x00648C30) is what the unit writes. path/0005 L1's "path mask" is the second: its anchors 0x005D94F2 and 0x005D9F9C call 0x00648C30 (read at the review).

- [L] **P07** src:fextralife-d2-whirlwind: "Whirlwind will not stop until you reached your destination (ground or a
  monster)", and for a fleeing monster "until you reached the monster, or the path becomes blocked by
  obstacles". **held with refinement**
  - *Finding:* [anim/movement § B4](../../specs/anim/movement.md) `[I]`: at a blocked subtile "the position stops at the centre of the last free subtile (a monster path with flag `0x10` then re-plans, any other path ends)", the walk `[C]` over logged test results for paths in general, Whirlwind not named. path/0005 L1 `[I]`: "Four skill starts mark the landing point before the flight"; path/0006 `[C]` for Whirlwind's site, 128 lines. (fn:sub_00650150_PathStepCollide@0x00650150, 0x005D9123)
  - *Verdict:* a Whirlwind path ends at a blocked subtile, and its last point is reserved. **Refinement:** "blocked" is the flight's test mask `0x401` (P08), so walls by bit 0 and objects by `0x400`; a door's `0x800` is tested only by the plan's `0xC01`. No run compares a Whirlwind flight stopping. Weak: no patch.
  - Anchor: fn:sub_00650150_PathStepCollide@0x00650150, 0x005D9123, 0x005D90B4.
- [L] **P08** src:fextralife-d2-whirlwind: "The Barbarian will fly through" a pack of monsters. **held**
  - *Finding:* [skills/0012 § 6](../skills/0012-barbarian.md) and [skills/catalogue K11](../../specs/skills/catalogue.md) `[C]` to the boundary (ADR-0021): start 38's no-target branch sets "the path's `+0x50` = 0xC01 (`PathSetCollMask`), `PathSetType(path, 7)`"; `[I]` past it: after the plan, "the mask 0x401" (pushed at 0x005D90AE, called at 0x005D90B4, read at the review), the old `0x1C09` or `0x3C01` kept at `ebp−0x14`. Neither mask holds `0x100`, `0x1000` or `0x2000`, so no live unit's mark refuses the plan or the flight.
  - *Verdict:* the reading gives what the page says. It stays `[I]` for the flight; agreement adds nothing. The target-in-melee branch takes no path. Mark mask: L1 found no zeroing at Whirlwind's start, so the flyer's own mark is written as it moves; what that does to others is not compared. Weak: no patch, a wiki page's tip. (0x005D90B4)
  - Anchor: 0x005D9042, 0x005D90AE, fn:sub_005D8F50_SkillSt38Whirlwind@0x005D8F50.
- Leap Attack and Charge pages (same wiki): no statement on walls, obstacles or collision; no claim to compare (re-fetched at the review).

### Blessed Hammer (`src:gamerguides-d2r-blessed-hammer`; **D2R**, last updated 2023, not 1.14d)

- [L] **P09** src:gamerguides-d2r-blessed-hammer: the hammer moves in "an ever-widening spiral". **held**
  - *Finding (the type-14 planner, server):* path/0003 § 9 `[I]` (fn:sub_0067A140_PathPlanSpiral@0x0067A140), "from the 16.16 position `(fx, fy)`, with `r = 0`,
    `a = 0`, `k = 0`: `r += 0x2580`, `a += 16`, `x = trunc(cos(a) · r) + fx`, `y = trunc(sin(a) · r) + fy` from
    `g_SineTable`; when `x >> 16` or `y >> 16` differs from the last kept cell, `points[k++]`, until `k = 77`."
    The radius grows by a constant each step, so the planned path widens. The truncation is `[C]` on 233 natural
    plans (path/0006). Scope: the plan's 77 points, not the missile's flight. Weak: D2R text on a 1.14d
    mechanic; it adds no detail the reading does not already hold.
  - Anchor: fn:sub_0067A140_PathPlanSpiral@0x0067A140, 0x0067A1A1.
- [L] **P10** src:gamerguides-d2r-blessed-hammer: the hammer spawns left of the Paladin, swings above, to his right,
  then below, "completing several rotations". **held with refinement**
  - *Finding:* path/0003 § 9 `[I]` as P09, and its Functions table: `g_SineTable` "512 float32, within 1.8e-07 of `sin(2πk/512)`", so `a += 16` is 1/32 of a turn. path/0006: 43 804 stored products over 233 plans, two products per iteration, so 94 iterations on average: 94 · 16 ÷ 512 = 2.94 turns, ending at `r` = 94 · 0x2580 = 13.77 subtiles. drlg/0007: the client's `SubtileToScreen`, `X = (x − y)·16`, `Y = (x + y)·8`. (data:g_SineTable@0x00707800, fn:sub_00643260_SubtileToScreen@0x00643260)
  - *Verdict:* with screen `Y` down (assumed), `a` rising turns below, left, above, right: the page's order and sense, and about three turns are "several". **Refinement:** the turn starts at +x, below and to the right, not at the left: from a cell-centred start the first kept cell is at iteration 5, `a` = 80, and the plan reaches the screen's left at `a` = 192, `r` = 1.76 subtiles, so what a player sees first may well be the left. Arithmetic on `[I]` readings, no new tag; scope the plan, not the flight. Weak: D2R. (0x0067A1AF)
  - Anchor: data:g_SineTable@0x00707800, fn:sub_00643260_SubtileToScreen@0x00643260, 0x0067A1AF.
- [L] **P11** src:gamerguides-d2r-blessed-hammer: a hammer that "comes into contact with a wall, pillar, or other bit
  of scenery" vanishes and no longer spirals. **held with refinement**
  - *Finding:* path/0003 § 9 `[I]` "No draw, no grid, neither `+0x90` nor `+0x91`": the plan reads no collision. [skills/missiles § D3](../../specs/skills/missiles.md) `[I]` holds the rest: Missiles row 92 `blessedhammer` has `pSrvDoFunc` 1 and `CollideType` 3, and that do function frees a missile whose own cell has bit 0 or 2, with no hit function, and ends one crossing a cell with bit 2 and no unit. (fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0, tbl:Missiles.txt:CollideType)
  - *Verdict:* the plan ignores the grid and the missile's own step ends it. **Refinement:** "scenery" is a cell with bit 0 or 2; an object cell of `0x400` alone does not end it, so a pillar depends on its tile's or its `BlockMissile`'s bit. Bit 0 alone is P12's question. Weak: D2R.
  - Anchor: fn:sub_005AE1F0_MissileMoveCollide@0x005AE1F0, tbl:Missiles.txt:CollideType, tbl:Missiles.txt:pSrvDoFunc.

## Not compared

- **Random-walk missiles (type 10):** no readable source (§ Search log, query 11). **Teleport:** the named pages were not readable (queries 3 and 5).
- **Monsters stuck on corners:** only mercenary anecdotes on the D2R forum, D2R mechanisms unstated, and other
  games' pages. A corner stall is a property of a planner (path/0002's walk, path/0003's greedy) and its
  `0x1000`/`0x400` cells; no source describes one for 1.14d.
- **Charge's path:** nothing beyond "closes the distance", stun/weapon-swap bug reports and the "not already in melee range" use limit, none
  with a collision statement.

## Open questions

For the spec's Open questions. P12 is the one contradiction, and it belongs to skills/missiles, not to a case of this plan.

- `[L]` **Do corpses block movement in 1.14d?** path/0005's C4 `[I]` says the server's `0x8000` 3×3 appears in "no move mask
  read so far", and `PathCellCollision`'s `0x7FFF` leaves the bit out too (skills/missiles D3 `[I]`). A reimplementer should not treat the `0x8000` corpse mark as a blocker until a mask that tests it
  is found; this is a statement of what the findings did not find, not a finding. `unflatDead`: `src:d2mods-monstats-guide` says walking, `src:d2dfg-blizzard` says drawing, no reader read ([entry](../../backlog/2026-11-04-architect-reverser-0054-unflatdead-reader-corpse-walk-or-draw.md)).
- `[L]` **Pets against players** (P05): no pet-specific mask read.
- `[L]` **A missile over a bit-0 cell** (P12), for skills/missiles' Open questions, [entry](../../backlog/2026-11-04-architect-reverser+spec-writer-0054-p12-missile-own-cell-bit0-vs-floor.md).
- `[L]` **Whirlwind's flight** (P07, P08): `0x401` is a reading past the emulation's boundary, and no run compares a flight stopping or passing a unit. The mask itself is not an open question, as the lane's first text had it, and neither is `SizeY`, which drlg/0005 § 5 answers (P02).

## Sources

Registered 2026-11-04 in `docs/sources.md`: `src:pk-walkable-flags-overview`, `src:fextralife-d2-whirlwind`,
`src:gamerguides-d2r-blessed-hammer` (kept); `src:pk-missile-functions-guide` (rejected: pseudocode-style formulas,
unread beyond the scan, nothing used); `src:diablowiki-leap-teleport-charge` and `src:fandom-diablo-pathing-ai` (not read: HTTP
403 and 402, again at the review). `src:d2mods-monstats-guide` and `src:d2dfg-blizzard` are re-used, their rows extended. Every page was scanned for code before it
was read; none of the kept pages had any. No file was run or saved; the pages were read through the fetch tool.
