# D2 landmarks: where to start, per subsystem

**Everything in this file is `[L]`.** It comes from general knowledge of the game and community
documentation, not from our binary. Use it to search, never to cite. Once a landmark is confirmed,
move it into `re/symbols.csv` and a finding, and strike it here with a link.

## Binary shape (1.14d)

- A single `Game.exe`, x86-32, MSVC-compiled. The former DLLs (Storm, Fog, D2Common, D2Game,
  D2Client, D2Win, D2Gfx, D2Lang, D2Net, D2CMP, D2Launch, D2MCPClient, Bnclient, D2DDraw/D2Direct3D/
  D2Glide) are linked statically, roughly grouped by original module within `.text`.
- Assert and log strings often include source paths like `..\Source\D2Common\DRLG\Drlg.cpp` and
  line numbers. These are the best way to label regions by original module and file.
- Excel tables are loaded by name through a generic table compiler (one loader per table, each
  passing a field-descriptor array: column name string, type, offset). **Finding the descriptor
  arrays gives you every table's in-memory record layout**, which is high value and should be done early.

## RNG

- A 64-bit seed struct `{u32 low; u32 high}`. Step: `new = (u64)low * 0x6AC690C5 + high`, then
  `low = (u32)new`, `high = (u32)(new >> 32)`. A range helper returns `low % n` (check for 0 and
  negative handling).
- Search: the bytes `C5 90 C6 6A` (imm32 little-endian). Expect several inlined copies.
- Seeds exist per game, per unit, per item, per room or DRLG `[L]`. Map who seeds whom.

## Items

- Generation chain `[L]`: monster death → TC chosen by difficulty and monster type → recursive TC
  resolution (Picks, NoDrop scaled by player count) → base item → quality roll (unique → set → rare
  → magic → superior → normal → low, each checked against ItemRatio-derived chances with magic find
  applied) → quality-specific generation (affixes by alvl, unique/set candidate lookup with
  fallback to rare or magic) → sockets, ethereal, durability, defense.
- Anchors to find: strings `TreasureClassEx`, `ItemRatio`, `MagicPrefix`; the quality enum (1 low … 8 crafted).

## Monsters

- Level population `[L]`: on room activation, the level's monster list (Levels mon/nmon/umon by
  difficulty) is sampled. Pack size comes from MonStats `MinGrp`/`MaxGrp`, density from `Levels.MonDen`,
  and unique/champion counts from `MonUMin`/`MonUMax`. Monster level comes from `Levels.MonLvl*`.
- Anchors: strings `MonStats`, `MonUMod`, `SuperUniques`; the room-activation path (DRLG room → spawn).

## DRLG

- Three generator types per `Levels.DrlgType` `[L]`: 1 = maze, 2 = preset, 3 = outdoor/wilderness.
- Act-level structure: act → levels → rooms (RoomEx/Room1/Room2 in community naming; use our own
  names once confirmed). Presets come from DS1, tiles from DT1 via LvlTypes.
- Anchors: strings `LvlPrest`, `LvlMaze`, `LvlSub`, `.ds1`, and source paths containing `Drlg`.
- The seed of each level is derived from the game seed, so the same game seed gives the same maps `[L]`.
  Confirming this early unlocks deterministic experiments.
