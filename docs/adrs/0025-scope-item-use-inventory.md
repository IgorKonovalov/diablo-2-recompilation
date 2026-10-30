# ADR-0025 — Item use and inventory enter scope as game rules: the server's outcomes only, beside ADR-0017

> **Status:** accepted (owner, 2026-10-30, with the approval of plan 0060 "as recommended")
> **Date:** 2026-10-30
> **Amends:** [ADR-0002](0002-scope-creation-paths-and-enablers.md) (scope), alongside [ADR-0017](0017-scope-quests-travel-economy.md) (whose three areas are unchanged)
> **Related plan(s):** [0060-item-use-inventory](../plans/0060-item-use-inventory.md)

## Context

ADR-0017 brought quest progression, travel and the item economy into scope as game rules beside the simulation
phases of ADR-0014. What a player does with an item once it exists was left out: ADR-0022's alternatives named
"player-side game rules (item use from the belt and inventory, pickup and the ground drop's placement, the stash)" and
did not recommend them on 2026-10-27. The owner's 2026-10-30 instruction ("plan as many as you can") opened them as
plan 0060, whose question 1 asks for this ADR.

The pieces are spread over reviewed specs and cited as edges: a potion's state clear (stats/states B3, `[I]`), the
starting items' belt placement (player/creation § E, `ItemToBelt` `0x0055E9B0`, `[C]`), scroll and book use as skills
(skills/0015, `PlayerUseBeltItem` `0x00562390`), the town portal tome's refusal in town (quests/travel G1, `[C]`), gold
pickup (items/economy G, `[I]`), identify's attach and the cursor consume (items/quest-drops, `ItemIdentifyAttach`
`0x0055FE00`, `CursorItemConsume` `0x0055EEA0`, `[C]`), the ground item's collision mark (drlg/collision, `[C]`), and the
inactive item record's expiry and 1 500-frame sweep (drlg/lifecycle). No spec owns the use dispatch by `Misc` use type,
the grids, the placement search, stacking, pickup refusals, the stash or a ground item's lifetime in an active room.
`save/d2s`'s ground positions stay `[L]` for want of that owner.

## Decision

Item use and inventory enter scope as **game rules**, beside ADR-0017's three areas: the server's handling of a
player's request to use, move, pick up, drop, stack, split or identify an item; the use dispatch by `Misc` use type
(potions, rejuvenation, scrolls and tomes, identify, keys and the other `pSpell` kinds) with its draws in order; the
inventory, belt, cursor and **stash** grids and the placement search into each, the cube's grid as an inventory page
(its transmute stays [items/cube](../specs/items/cube.md)'s); the ground drop's cell search; and the **ground item's
lifetime** and despawn, a server timer. Claims are stated from the server's outcomes in game frames (ADR-0014 § Time):
the client's UI (drag, tooltips, the belt and inventory display, screen coordinates read from `belts` and `inventory`)
stays out, and so does **trading** ([multiplayer/0002](../findings/multiplayer/0002-trade-and-party-gold.md) keeps the trade test; a full trade flow needs a later plan). The
evidence is ADR-0014's per-event reproduction, with a request's fields as logged inputs. The research-map row is
`items/use` under Game rules (plan 0060).

## Consequences

### Positive

- The cited edges get one owner, and the specs that now take an item's slot or a potion's effect as an input can link
  a reviewed section instead.
- `save/d2s`'s ground-position `[L]` and drlg/lifecycle's item expiry gain the active-room half they lack.
- The work is mostly static reading of request handlers already reached from `g_SrvPacketTable` (`0x006E0D18`), so it
  fills static lanes; it needs one harness slot.

### Negative

- **Scope grows again**, for a part with no creation-path payoff: the three priority areas gain nothing directly, and
  the research map's "done" point moves out by one row.
- **The boundary between server and client is not always clean.** Some refusals may be checked on both sides, and some
  `belts` and `inventory` columns are read by both; a claim the server does not decide is out, and Phase 0 and P1.2
  must say which reader is the server's. A rule checked only by the client is recorded as out of scope, not as absent.
- **Trading stays a gap**: an item that leaves one player's grid for another's in a trade is not specified.

### Neutral

- Evidence rules, tags and ADR-0014's per-event rules are unchanged; ADR-0017's areas and ADR-0022's frame phase are
  untouched. The request handlers' order inside one drain stays plan 0055's (sim/frame), with plan 0060's P1.3 reading
  only the item handlers in it.

## Alternatives considered

**Leave it out (ADR-0022's 2026-10-27 recommendation).** The edges would stay inputs and named-only links. It lost
because the owner asked for the next plans by value, and a reimplementer cannot run a game without the belt, the grids
and the ground drop; the frame phase that argued against it then is now planned and running.

**Fold it into ADR-0017 by plan, with no ADR.** ADR-0017 names three areas and its rows by plan; widening it silently
would leave its text wrong. A short sibling ADR keeps each scope statement accurate at the cost of one file.

**Include trading now.** It would close the last way an item moves between grids, but it is a multi-message flow
between two clients, needs both harness slots and the owner, and adds little the single-player rules do not already
specify; it lost on cost and stays a later plan.
