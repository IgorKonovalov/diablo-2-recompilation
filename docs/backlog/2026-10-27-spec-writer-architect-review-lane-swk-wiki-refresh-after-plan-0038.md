---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#phase-3--re-tag-the-specs
  - archive/2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3.md
  - ../wiki/monsters.md
  - ../wiki/levels.md
  - ../wiki/seed-to-world.md
resolution: ""
---

Please review `lane/swk`: the wiki refresh after plan 0038 Phase 3's monsters and drlg/collision clusters
([entry](archive/2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3.md), closed). Not blocking.
Gate green; W4 0 warnings (60 checked).

- **[wiki/monsters](../wiki/monsters.md)**: `based_on` pool, spawn, special, stats and drlg/collision bumped to
  2026-10-27. The six corrections, each at the spec's tag:
  - the `SetBoss` pack member's minions as group members (the pack-member paragraph of *Champions and uniques* and the
    *What the mods do* definition; stats § G, special C1);
  - the `fast`/`fanatic` bonus, 100 up to `Velocity` 8 and 99 at 9, said "by the formula", with 8 and 9 unmet (new
    bullet; stats G3);
  - the `druidhawk` normal row, reachable by a Druid's Raven by the code and not logged (the MonProp paragraph and the
    stats open-question bullet; stats F3);
  - `PresetFallenVariant` on the base type, with level 6 the logged case and the other levels read from the code (the
    map-presets paragraph; special § H);
  - a restored aura special's two auras (new bullet under *Mod handlers*; special § J);
  - the wanderer roll fired once, with the spawn branch, the mask width and the no-player test kept as code readings
    (spawn § K).

  The raised statements carried:
  - pool C1 and E: the classic normal pool and level, the four further `boss` classes, the classic `MonLvl1..3` columns;
  - spawn A, B, E, I and K: the client never running the pass; the Chaos Sanctuary test's open side, with the closed
    side kept unconfirmed; the special count's preset, superunique and decrease lines; `/players` not scaling the pass,
    with real multiplayer kept unlogged; the tick on populated rooms; the `MonWndr` reader;
  - special B, C3, E1, G and I1: the `sandleaper` exclusion; the transfer's sent list and the handler path, with the
    other readers kept as code; the aura table and skill levels, with the clamps unmet; the `Stacks` refusal, with the
    open-quest case kept as code; the met tails, with Radament's `+ r` kept as code; the second aura call; the client
    names;
  - stats B7, A1, B10 and C1: the reversed HP range by composition, `MulDiv` under emulation, the skill bonus, the
    `Align` no-bonus classes with the camel unmet.

  *What is not known yet* is rewritten for the closed items. One weaker-tag call (rule 1): spawn D's "`Rarity` 0
  never picked" is `[C]`, while pool's same statement is `[I]` ("no stock region has either"). The page says it by
  the code, and that no stock pool holds one.
- **[wiki/levels](../wiki/levels.md)**: collision bumped to 2026-10-27, and spawn added to `based_on` (2026-10-27).
  - § *The collision grid and logic regions*: the logic-region paragraph is rewritten whole over collision G1–G3: the
    single box and its counter reset, the barrier rule, the flood (its unexercised entries and orientations kept as
    code) and the relabelling, all over the 1 475 floods. The warp-test paragraph is rewritten over collision I2: the
    level-seed step in Tristram, the Canyon of the Magi, the Arcane Sanctuary and level 125, no draw on zero matches,
    and the operand for two or more matches kept as code.
  - The *Collision* bullet of the untested list is rewritten whole. Sizes 0 and 1, `sarcophagus`, `evilhut` and the
    NPC patterns are answered, and 334 has no stock source. The NPC upgrade is for `npc` or `inTown` with `interact`
    clear, with only the `inTown` half confirmed. The open items are kept.
  - Beyond the entry, for rule 7: the *Wanderers* paragraph and the lifecycle bullet's "the wanderer roll and spawn"
    now cite spawn § K's one fired roll.
- **[wiki/seed-to-world](../wiki/seed-to-world.md)**: stats bumped to 2026-10-27. Its equipment paragraph already
  matches stats B12, so its text is unchanged.

**For the architect, not done here:**
- [drlg/lifecycle § I](../specs/drlg/lifecycle.md#i-the-wanderer-tick) still says no gate draw passed and keeps the
  roll's no-spawn branch `[I]`, while spawn § K now has that branch `[C]` from run:2026-10-21-sweep-monsters-a. A
  spec-writer follow-up would bring lifecycle I into line.
- Untouched: the specs `lane/s45p3` holds (combat/README, stats/states, items/economy, rng/seeds) and the economy and
  randomness pages.
