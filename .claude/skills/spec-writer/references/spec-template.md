---
spec: <subsystem>/<algorithm>
status: draft | reviewed
target: Diablo II LoD 1.14d, Game.exe sha256 <first 16 hex>…
depends_on: [rng, ...]
consumed_by: [...]
tags: {C: n, I: n, L: n}        # counts, updated on every edit
updated: YYYY-MM-DD
---

# <Algorithm name>

## Purpose

Two or three sentences: what goes in, what comes out, and when the game runs it.

## Entry points

| When | Function | Tag |
|---|---|---|
| Monster dies | fn:Name@0x00XXXXXX | [I] |

## Inputs

### Tables
| Anchor | Used for |
|---|---|
| tbl:TreasureClassEx.txt:Picks | number of picks |

### Runtime state
| State | Type | Source |
|---|---|---|
| item seed | Seed64 (see rng spec) | derived from … |

### Constants
| Name | Value | Anchor | Tag |
|---|---|---|---|

## Algorithm

```
1. ...                                   [I] (0x00XXXXXX)
2. r1 ← RNG.Range(itemSeed, 100)         [C] draw#1  (0x…, run:…)
3. if difficulty = Hell then ...         [I] (0x…)
```

Step notes, if any, follow the block and are numbered to match.

## Outputs

What the algorithm produces, and its exact shape.

## Worked example

Input, the draws in order, the output. Source: `run:<id>` or a `tools/` reproduction.

## Reimplementation notes

Traps, edge cases, behaviour that looks like a bug but is faithful.

## Evidence

Links to every finding and table doc used.

## Open questions

- [L] … (what would resolve it; backlog link)
