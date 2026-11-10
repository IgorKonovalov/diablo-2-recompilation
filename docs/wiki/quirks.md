---
based_on:
  - docs/specs/quirks/README.md 2026-11-10
---

# Quirks: the traps a faithful rebuild must keep

This page is a reader's tour of the project's list of quirks. A quirk here is behaviour of the 1.14d game that a
careful programmer would "fix" by accident: a divide made signed, a random draw skipped because its result is thrown
away, a "less than or equal" turned into "less than", a table edge read the sensible way. The reviewed specs each
state their own traps in their notes. The [quirks index](../specs/quirks/README.md#purpose) gathers them in one place,
527 entries in nine classes, so that a rebuild can be checked against the whole list. This page makes no claim of its
own. It tells you what kinds of trap the game holds, shows a few of the most striking, and points into the index. The
one-line entries of the index leave out conditions, so read the owning spec section an entry links before you rely on
it; where the index and a spec differ, the spec is right
([how to read an entry](../specs/quirks/README.md#how-to-read-an-entry)).

For the meaning of "confirmed" and "read from the code", see [How we know](how-we-know.md).

## The classes

The index's nine classes, with the number of entries in each and how many of them are confirmed
([the table](../specs/quirks/README.md#entries)). The rest were read from the code and not yet confirmed by anything
independent.

| Class | Entries | Confirmed |
|---|---|---|
| [1. Arithmetic width and sign](#1-arithmetic-width-and-sign) | 26 | 19 |
| [2. Rounding and float](#2-rounding-and-float) | 21 | 15 |
| [3. Wrap and overflow](#3-wrap-and-overflow) | 10 | 3 |
| [4. Bounds, comparisons and table edges](#4-bounds-comparisons-and-table-edges) | 79 | 56 |
| [5. Draw order and dead draws](#5-draw-order-and-dead-draws) | 143 | 117 |
| [6. Data-dependent branches](#6-data-dependent-branches) | 134 | 103 |
| [7. Timing and frame edges](#7-timing-and-frame-edges) | 28 | 14 |
| [8. Multiplayer edges](#8-multiplayer-edges) | 16 | 12 |
| [9. Deliberate oddities that look like bugs](#9-deliberate-oddities-that-look-like-bugs) | 70 | 30 |
| **Total** | 527 | 369 |

### 1. Arithmetic width and sign

Integers in the game are of a fixed width, and whether a divide, a compare or a shift treats them as signed or unsigned
changes the result for large or negative values. The random number generator's range reduction divides unsigned, so a
signed rebuild goes wrong once the low word reaches 2^31. Experience is unsigned all the way up. The string-table hash
reads key bytes as signed characters, so a byte of 0x80 or more lands in another slot than the textbook hash gives.
Trade prices divide one sum signed and another unsigned by a stackable item's stack size, so with a stack size above 1 a negative stat sum divides as a huge number. Objects with a negative spacing in the table step 249 to 255 subtiles, not backwards.
Entries: [class 1](../specs/quirks/README.md#1-arithmetic-width-and-sign).

### 2. Rounding and float

Where the game truncates, floors or carries a fractional value changes the last digit, and the last digit is what a
check against the game compares. Kill-experience level penalties are fractions of 256 (207/256, 13/256), not the
rounded percentages people quote. The chance to hit truncates its first quotient to an integer before the level factor,
so one combined expression gives other numbers. Trade prices carry three running values through every step, including
the steps whose result a mode throws away, and the order of terms matters through later truncations. The treasure
class "no drop" weight is recomputed per pick in double precision.
Entries: [class 2](../specs/quirks/README.md#2-rounding-and-float).

### 3. Wrap and overflow

Some values wrap around instead of saturating. A level's seed is a 32-bit sum that wraps rather than a draw from the act
seed, and the multiply-divide helper keeps the low 32 bits of a quotient that does not fit. This class also holds
three paths that the specs read in the code and that would crash or hang the game (an integer divide that overflows,
in two places, and a progressive ring whose step count is never tested); all three are read from the code only and were
not provoked. Entries: [class 3](../specs/quirks/README.md#3-wrap-and-overflow).

### 4. Bounds, comparisons and table edges

The edge of a range is where rebuilds drift. The to-hit clamp tests "5 or less" and "95 or more", so a rolled attack is
never certain and never impossible. A damage maximum is exclusive: the roll never reaches it. Life below 256 internal units
counts as zero, so a hit that leaves less than one life point kills. The command-line seed 0 cannot be asked for,
because 0 means "use the clock". Entries: [class 4](../specs/quirks/README.md#4-bounds-comparisons-and-table-edges).

### 5. Draw order and dead draws

The largest class, and the one that decides whether a rebuild gives the same world from the same seed. A draw must
happen in the same place even when its result is discarded, and must not happen where the game skips it. Some range
helpers return 0 without drawing for a count below 1, but others (and draws written inline with a constant modulus)
have no such guard and step the seed anyway. Maps derive from one seed and server units from another, and a room that
wakes re-seeds from its own field, so carrying the generation seed over is wrong. The Act II tomb loop uses an
unguarded modulus and in principle has no bound. Entries: [class 5](../specs/quirks/README.md#5-draw-order-and-dead-draws).

### 6. Data-dependent branches

Behaviour that depends on which row, flag or value is in play. A monster's critical strike doubles every damage field,
physical and elemental, while the index records a player's critical or deadly strike as doubling only the physical part
(that second one is read from the code). Leech uses the reduced, life-capped physical damage, and elemental damage never
leeches. A monster with few hit points has no regeneration at all, because the product rounds to 0 (read from the code). A formula the game
cannot compile is stored as an error and evaluates to 0, where a forgiving parser would succeed. Entries:
[class 6](../specs/quirks/README.md#6-data-dependent-branches).

### 7. Timing and frame edges

When things happen, in frames. A scheduled action ends a number of frames after it starts, and the community
breakpoint tables count one less. A scheduled action does not follow a rate change made after it starts, while an every-frame monster takes the new rate at its next advance (read from the code). A monster's attack
rolls its extra-damage draws when the attack begins, and the to-hit and damage at the hit frame, with the monster's
own thinking drawing in between. Nearly half of this class is read from the code only (10 of 19 confirmed). Entries:
[class 7](../specs/quirks/README.md#7-timing-and-frame-edges).

### 8. Multiplayer edges

What the number of players and the game type change. The player count is fixed when a monster is created, so changing
it later changes nothing on live monsters. The `/players` setting is a floor, not an addition, in single player and on
a host. A server rebuild seeds units from the game seed, because the room-seed rule belongs to the client. The saved
map seed survives only in single player. A party's shared kill experience measures distance from the killed monster,
not from the killer. Entries: [class 8](../specs/quirks/README.md#8-multiplayer-edges).

### 9. Deliberate oddities that look like bugs

Behaviour that reads as a mistake and is faithful, or that contradicts a community description. The random number
generator takes the remainder directly, with no correction for bias. The two place-group modes keep three quarters
and one quarter, the reverse of what the names suggest. Rares have 3 to 6 affixes, not 2 to 6. Magic find is linear up
to 10. With one player, crushing blow takes a quarter of the defender's current life on uniques and champions, not an eighth; more players raise the divisor. A hireling's
experience curve is cubic, not quadratic. Keep them all. Entries:
[class 9](../specs/quirks/README.md#9-deliberate-oddities-that-look-like-bugs).

## Crash and hang paths

The index lists nine such paths, wherever the specs state them; they live in the classes above. Only one of the nine
happened in a game: on one of the cube's crafting recipes, at a low item level, a recorded run logged the game's fault.
Two more were reached only under emulation, the game's own code run on its own and not in a game: the game's fatal path
on three paths of the skill catalogue, and the same path for a party's ninth member, which no stock game reaches: read from the code, a party holds
at most eight players. The other six come from readings of the code. None was provoked for the index, and the harness has provoked
none since that rule; the logged fault is older, from a run that expected it
([crash and hang paths](../specs/quirks/README.md#crash-and-hang-paths)).

## Community claims

Thirty claims from community bug lists were compared with the code
([community claims](../specs/quirks/README.md#community-claims)): 20 hold, 4 are contradicted, 3 do not apply to
1.14d and 3 could not be settled. Agreement with a community page proves nothing by itself, because much of that
knowledge comes from older versions. Each claim that holds is listed as an ordinary entry at its own level, and most of
those are read from the code only: of their 21 entries, 5 are confirmed and 16 are not.

The claims that do not hold are
[listed in the index](../specs/quirks/README.md#community-claims-that-do-not-hold). A rebuild must not restore them.

- **Monsters with life, mana or stamina steal do not do double melee damage.** A monster's life drain, a hireling's
  aside, is one term added to the physical damage, which it does not repeat. Mana and stamina drains are not in that
  total, and what can double is a drain already in the packet; those two parts are read from the code.
- **Curse resistance does not cut every timed list.** The cut applies when the state is a curse, and Fade's cell is
  blank (read from the code).
- **Hratli's magic level is 0, not 1.** The community is right that a misspelled header is the cause; the value is the
  default for an absent column.
- **Eth does not make the target's defence negative.** The percent is clamped to 0 to 100 and halved on a boss, player,
  superunique or hireling (read from the code).
- **Kick does not take elemental damage from weapons in 1.14d.** Kick's own start skips the damage build, and the build the
  kicks do use first unlinks the damage stats of a weapon in either hand; elemental stats from other items still reach
  it (read from the code).
- **No runeword property code is misspelled.** None of the 508 code cells in 169 rows is unknown.
- **The "n minus 1" bug, a ranged modifier that never reaches its maximum, is not in 1.14d.**

Three more claims stay open leads, with the reason each could not be settled: a shared timeout id for delayed boss death
effects, delayed trapped-soul drops that ignore gold and magic find, and a Cloak of Shadows crash near the Ancients
([open questions](../specs/quirks/README.md#open-questions)).

## Seen in play, emulated, or read from the code

The index ([how to read an entry](../specs/quirks/README.md#how-to-read-an-entry)) follows the project's tags ([How we know](how-we-know.md#three-levels-of-confidence)), and a reader of this
page should keep two things apart.

- **Confirmed does not always mean seen in play.** A map of the code that emulation reproduced is confirmed as what the
  code does, and it was not seen in play. Many confirmed entries rest on a recorded run of the real game. Some
  rest on the game's own code run on its own in an emulator, or on a second code path or a game data table that agrees with the
  reading. An entry marked as "the code's map" says that no logged case separates the possibilities; it describes what the
  code does, not something a player saw. The party-share distance rule is one such: the code's map reproduced under
  emulation, with no logged kill separating it. Emulation shows what a function does with its inputs, not who calls it
  or how often in a real game ([what emulation can confirm](how-we-know.md#emulated-reproduction-one-function-run-on-its-own)).
- **Read from the code is the weaker statement.** About three in ten of the entries (158 of 527) are only read from the
  code and not yet checked against anything independent. A trap in this group is probably real and has not been
  tested.

When a statement here carries a number ("20 hold", "508 cells"), it is a count from the index or the spec that owns it,
tied there to the runs or the table reads behind it.

## What is not known yet

- The step notes of the reviewed specs were not all swept for entries; a later pass may add more
  ([open questions](../specs/quirks/README.md#open-questions)).
- Three community claims are unsettled, as above.
- Only the cube fault is a recorded crash. For the other eight crash and hang paths the outcome is the code's: six read,
  two reached under emulation.
