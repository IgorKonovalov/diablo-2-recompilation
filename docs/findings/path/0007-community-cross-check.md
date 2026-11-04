# 0007 — Community cross-check of the path findings (plan 0054 Phase 1b)

> **Subsystem:** path/search
> **Question:** what do community documents say about pathing (monsters stuck on corners, Charge, Leap, Whirlwind, Teleport, Blessed Hammer's spiral, the random-walk missiles, corpses as obstacles), and what verdict does each comparable claim get against [path/0001](0001-pathplan-register.md) to [path/0006](0006-holdout.md)?
> **Date:** 2026-11-04   **Plan:** 0054 (Phase 1b, `lane/r1b`)   **Status:** for review (Tier A, ADR-0030)

No Ghidra, no game, no emulation, no new code reading. The findings were read first and their statements are
quoted below as they stand; the community pages were fetched in the session (ADR-0007), keyword-scanned for
code before any was read (ADR-0001), and registered in `docs/sources.md` before use. Agreement promotes nothing
(`evidence-rules.md` § Community cross-checks); no `[C]` or `[I]` of path/0001 to 0006 changes tag here.

## Answer (summary)

- **Almost nothing in the community record bears on the path planner.** The search (12 queries, § Search log)
  found no page that describes monster or missile pathing at the level of a planner, a grid or a collision mask.
  What exists is skill-page prose (Whirlwind, Leap, Charge, Blessed Hammer), one modding guide with a few
  collision columns, and one floor-flag table whose values the fetch could not align.
- **11 claims compared: 1 `held`, 2 `held with refinement`, 0 `contradicted`, 8 `not covered`.** All
  agreement is weak: the sources name no patch (P01, P02) or describe D2R (P09).
- **No claim is contradicted, so no required case is filed and no backlog entry is raised.** The refinements
  and the uncovered claims that a spec writer might meet are listed under *Open questions*, for the spec's
  Open questions.
- **Phase 1b's earlier reason does not hold in one respect:** path/0001 to 0006 said "no registered source with a
  comparable claim". `src:d2mods-monstats-guide` (article 359) was registered and holds the `deadCol` and `SizeX`
  claims compared here (P01, P02).
- **Rejected or unread:** `src:pk-missile-functions-guide` (pseudocode-style formulas of game logic: rejected,
  unread beyond the scan); four pages that returned HTTP 402 or 403 (`src:diablowiki-leap-teleport-charge`,
  `src:fandom-diablo-pathing-ai`; nothing used). `pk-pathfinding-thread` stays rejected for code and was not opened.

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

Nothing at all came back for **random-walk missiles** (the movement math of Frozen Orb, Lightning Fury and the
like) or for **Teleport as a pathing event**; both are searched and empty. The Median XL slide deck
(`src:wue-d2-ai-slides`) was already registered.

## Leads used

The comparison table is one verdict per claim, in the form of `evidence-rules.md`. "Finding" quotes the
statements of path/0001 to 0006 whole, with their tags; scopes are stated on both sides. All sources are
community documents of unknown or other patches, so **agreement is weak** and is stated as such.

### The MonStats2 guide (`src:d2mods-monstats-guide`, article 359; no patch named)

- [L] **P01** src:d2mods-monstats-guide: `deadCol` "states whether the unit's corpse collides or not with other
  units." **held with refinement**
  - *Finding (server copy, the planner's grid):* path/0005 C1/C2 `[C]`, "`MonDeathEvent` sets mode 0 and calls
    0x005A6520, which tests `deadCol` (`edx` = 0x13, `+0x06` bit 3, at 0x005A65CD) and, when it is 0, calls
    `UnitCorpseColl(unit, 1)` at 0x005A65D9: the live mark off and a 3×3 of `0x8000` (0x00649FD8), mask and pattern
    untouched." and "C2: `deadCol` 1, the live mark stays." (path/0006: C2 `[C]` for classes 403 and 404, 18 distinct
    dead with no `0x8000` cell and the live mark kept; class 273's server arm `[I]`.) *Client copy:* the tests at
    0x004B05DB and 0x004B09FB call `UnitCorpseColl(unit, 0)`, a plus (path/0005, `[C]` for the client's copy).
  - *Verdict:* the finding agrees on the direction at the server's grid: `deadCol` 1 keeps the unit's live mark
    (a corpse that collides like a live monster), `deadCol` 0 takes it off. **Refinement:** `deadCol` 0 does not
    leave the cells free in the grid; it writes a 3×3 of `0x8000` (a plus on the client). Whether that bit blocks
    anything is the finding's `[I]` C4: "`0x8000` is in no move mask read so far", so no planner of path/0001 to
    0006 was seen to refuse it. The guide says "other units", which the findings do not separate from the planner's
    own mask. Weak: no patch named, and the guide is a column description, not a behaviour test.
  - Anchor: 0x005A65CD, 0x005A65D9, 0x00649FD8, tbl:MonStats2.txt:deadCol.
- [L] **P02** src:d2mods-monstats-guide: `SizeX` and `SizeY` are the "X-diameter in sub-tiles, used for collision and
  proximity checking. It ranges from -1 to 3." **held with refinement**
  - *Finding (the path record, both copies):* path/0001 `[I]`, "`PATH_DynamicCreate` ...: `+0x44` `UNIT_GetSizeX`,
    `+0x48` `PATH_PatternFromSize`" (not emulated), with `MonStats2 +0x08` as `SizeX`; path/0005 T1 `[C]`, "Under
    path flag `0x800` `PathPlan` unmarks a target whose `UNIT_GetSizeX` is not 0, whatever its type
    (0x00649B10–0x00649B25), and re-marks it at the tail (0x00649BD7) when the unmark returned non-zero".
  - *Verdict:* a monster's `SizeX` does feed its collision footprint (the path record's size and pattern, `[I]`)
    and a non-zero value gates the target's unmark. **Refinements:** the findings read `SizeX` only; `SizeY` is
    not read in any of them. The range -1 to 3 and "proximity checking" are not compared. A size of 0 is a
    separate branch (no unmark, "read, not run"). Weak: unversioned.
  - Anchor: 0x00649B10, 0x00649BD7, fn:sub_00649970_PathPlan@0x00649970.
- [L] **P03** src:d2mods-monstats-guide: `NoGfxHitTest` "controls whenever the game uses the x/y diameter settings
  for collision detection" (or "special, superimposed values", the `htTop`..`htHeight` box). **not covered**
  - Finding: no statement in path/0001 to 0006 reads `NoGfxHitTest` or the `ht*` box; the path code reads the
    size, not a hit box. Hit tests are not this subsystem.
- [L] **P04** src:d2mods-monstats-guide: `unFlatDeath` "states whether the unit's corpse can be walked through or
  not." **not covered**
  - Finding: path/0001 to 0006 do not read `unFlatDeath`. Their corpse statements are all about `deadCol` and the
    marks it selects. This is the one corpse-as-obstacle claim of the search with a named column; the spec's
    Open questions keep it.
- [L] **P05** src:d2mods-monstats-guide: "while pets do not use this setting towards the players, they can still
  block each other"; necromancers that teleport along with large monsters ("a size bigger than 1") end with
  all their minions "blocked into the same position". **not covered**
  - Finding: path/0005 gives a pet's route as `[I]` ("`PATH_SetMarkMask(path, 0x100)` at 0x00574D80, which marks,
    when 0x0063EA40 returns 0", callee unfollowed) and nothing on pets against players or on stacking after a
    teleport. No pet-versus-player mask was read.

### The walkable-flags overview (`src:pk-walkable-flags-overview`; 2006, no patch)

- [L] **P06** src:pk-walkable-flags-overview: the DT1 floor flags set, per value, "allow player / minion /
  mercenary / monster walk", "allow jumping over", "allow teleport" and "allow missiles pass". **not covered**
  - Finding: path/0001 to 0006 take the grid as built (`CB`, the predicted grid, the live grid) and name the bits
    of the runtime sub-tile word (`0x400`, `0x1000`, `0x8000`, ...). The map from a floor flag to a bit is
    drlg/collision's, not the planner's, and the fetch did not keep the table's values aligned with its columns
    (§ Sources). Nothing is compared. (drlg/collision was cross-checked against `src:pk-walkable-thread` in plan 0017.)

### Whirlwind, Leap and Charge (`src:fextralife-d2-whirlwind`; wiki prose, no patch)

- [L] **P07** src:fextralife-d2-whirlwind: "Whirlwind will not stop until you reached your destination (ground or a
  monster)", and for a fleeing monster "until you reached the monster, or the path becomes blocked by
  obstacles". **not covered**
  - Finding: the findings cover the plan, not the flight. The nearest statements are path/0005 L1 `[I]`: "Four skill
    starts mark the landing point before the flight, with `COLL_PatternMark` and the unit's pattern: Whirlwind
    0x005D9123 (`0x80` for a player, else `0x100`) ... Landing unmarks the reserved cells (... 0x005D94E8 ...) and
    sets the mask back", and path/0006 `[C]` for three of the four sites reached "each as read" (Whirlwind 128
    lines). That a destination cell is reserved fits "reaches its destination"; it says nothing of what stops a
    flight on the way. The per-frame step is outside path/0001 to 0006.
- [L] **P08** src:fextralife-d2-whirlwind: "The Barbarian will fly through" a pack of monsters. **not covered**
  - Finding: path/0005 L1 `[I]` found "no such call [setting the path mask to 0] ... in the starts of Whirlwind or
    Jump, whose ends restore it (0x005D94F2, 0x005CBA46)", where Leap's flight sets the mask to 0 (0x005D9F9C). What
    mask Whirlwind flies with is therefore open in the findings; the claim is a lead for it, not a comparison.
- Leap Attack and Charge pages (same wiki): no statement on walls, obstacles or collision; no claim to compare.

### Blessed Hammer (`src:gamerguides-d2r-blessed-hammer`; **D2R**, patch 2.4 listed, not 1.14d)

- [L] **P09** src:gamerguides-d2r-blessed-hammer: the hammer moves in "an ever-widening spiral". **held**
  - *Finding (the type-14 planner, server):* path/0003 § 9 `[I]`, "from the 16.16 position `(fx, fy)`, with `r = 0`,
    `a = 0`, `k = 0`: `r += 0x2580`, `a += 16`, `x = trunc(cos(a) · r) + fx`, `y = trunc(sin(a) · r) + fy` from
    `g_SineTable`; when `x >> 16` or `y >> 16` differs from the last kept cell, `points[k++]`, until `k = 77`."
    The radius grows by a constant each step, so the planned path widens. The truncation is `[C]` on 233 natural
    plans (path/0006). Scope: the plan's 77 points, not the missile's flight. Weak: D2R text on a 1.14d
    mechanic; it adds no detail the reading does not already hold.
  - Anchor: fn:sub_0067A140_PathPlanSpiral@0x0067A140, 0x0067A1A1.
- [L] **P10** src:gamerguides-d2r-blessed-hammer: the hammer spawns left of the Paladin, swings above, to his right,
  then below, "completing several rotations". **not covered**
  - Finding: path/0003 § 9 holds the spiral about the 16.16 start `(fx, fy)` with the angle step 16 of
    `g_SineTable`, but no finding turns it into a start direction, a turning sense or a rotation count (the table's
    size and the sine table's unit are not stated there). The first point's side is a function of the missile's
    start and the table, which the findings do not compute.
- [L] **P11** src:gamerguides-d2r-blessed-hammer: a hammer that "comes into contact with a wall, pillar, or other bit
  of scenery" vanishes and no longer spirals. **not covered**
  - Finding: path/0003 § 9 `[I]` "No draw, no grid, neither `+0x90` nor `+0x91`": the plan reads no collision.
    That is compatible with a wall ending the missile in its own movement and collision code, which no finding of
    path/0001 to 0006 covers (as for the random walk: "the missile's collision is its own", path/0003 § 8 `[C]`).
    A plan that ignores the grid and a missile that dies on it do not contradict; the finding is silent on the
    second.

## Not compared

- **Random-walk missiles (type 10) and Teleport:** no source (§ Search log, queries 5 and 11).
- **Monsters stuck on corners:** only mercenary anecdotes on the D2R forum, D2R mechanisms unstated, and other
  games' pages. A corner stall is a property of a planner (path/0002's walk, path/0003's greedy) and its
  `0x1000`/`0x400` cells; no source describes one for 1.14d.
- **Charge's path:** nothing beyond "closes the distance", stun/weapon-swap bug reports and the "not already in melee range" use limit, none
  with a collision statement.

## Open questions

For the spec's Open questions; none is a contradiction, so none is a required case of a later run.

- `[L]` **Do corpses block movement in 1.14d?** `src:d2mods-monstats-guide` has `unFlatDeath` ("can be walked
  through or not") and `deadCol`; path/0005's C4 `[I]` says the server's `0x8000` 3×3 appears in "no move mask
  read so far". A reimplementer should not treat the `0x8000` corpse mark as a blocker until a mask that tests it
  is found; this is a statement of what the findings did not find, not a finding.
- `[L]` **What does the findings' `SizeY` do?** `src:d2mods-monstats-guide` lists `SizeX` and `SizeY` together; the
  path findings read `SizeX` only.
- `[L]` **Whirlwind's flight mask** (P07, P08): path/0005 L1 found no mask-zeroing call at Whirlwind's start, as
  Leap has; the community says the flight passes through monsters. The two together are a question for the skills
  lane, not for the planner.
- `[L]` **Whirlwind's and the hammer's collision with scenery** (P07, P11) belong to the movement/collision step, which
  no path finding covers.

## Sources

Registered 2026-11-04 in `docs/sources.md`: `src:pk-walkable-flags-overview`, `src:fextralife-d2-whirlwind`,
`src:gamerguides-d2r-blessed-hammer` (kept); `src:pk-missile-functions-guide` (rejected: pseudocode-style formulas,
unread beyond the scan); `src:diablowiki-leap-teleport-charge` and `src:fandom-diablo-pathing-ai` (not read: HTTP
403 and 402). `src:d2mods-monstats-guide` is re-used, its row extended. Every page was scanned for code before it
was read; none of the kept pages had any. No file was run or saved; the pages were read through the fetch tool.
