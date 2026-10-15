---
spec: player/overview
status: draft
target: Diablo II LoD 1.14d, Game.exe sha256 631066c1649c4ea9…
depends_on: [rng, rng/seeds, items/uniques-sets, items/properties, items/affixes, monsters/stats, save/d2s]
consumed_by: [save/d2s]
tags: {C: 0, I: 0, L: 0}
updated: 2026-10-16
---

# Player: new character, experience and level-up

## Purpose

This subsystem specifies what a single-player character starts with and how it grows: the stub a new character
begins as, the attributes, skills and items the server gives it (with every game-seed step), the experience table, the
experience a kill is worth, and the level-up. This page is the map; the claims, with their tags, are in the file below.

## Files

| File | Covers | Status |
|---|---|---|
| [creation.md](creation.md) | the stub and its checks, `NewCharFromStub` in order, starting values per class, starting skills, starting items (creation record, draws, belt / equip / inventory placement), the experience table, `XP_Compute`, `PLAYER_AddExperience`, `PLAYER_LevelUp`, the `-act` grant, party share, death loss, attribute spending | draft |

Not covered: skill effects and the skill tree (ADR-0002), Battle.net and ladder characters, CharTemplate (read only
for a template game's class), mercenaries (their levels come from `Hireling`).

## Upstream and downstream

- Upstream: [rng](../rng/README.md) and [rng/seeds](../rng/seeds.md) (the game seed and unit seeds), the item model
  ([items/uniques-sets § A](../items/uniques-sets.md#a-the-item-seed-at-entry), [items/properties](../items/properties.md),
  [items/affixes](../items/affixes.md)) for each starting item, [monsters/stats](../monsters/stats.md) for a monster's
  experience.
- Downstream: [save/d2s](../save/d2s.md) writes the first save of a new character.
