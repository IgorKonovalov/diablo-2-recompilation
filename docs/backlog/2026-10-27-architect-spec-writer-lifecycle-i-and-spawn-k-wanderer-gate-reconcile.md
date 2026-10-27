---
from: architect
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../specs/drlg/lifecycle.md#i-the-wanderer-tick
  - ../specs/monsters/spawn.md#k-wanderers-the-tick
  - ../plans/0038-inferred-claims-sweep.md#log
resolution: ""
---

From the `lane/swk` review (plan 0038 log). Not blocking. Bring the two wanderer-tick sections into line, each at the weaker tag where the evidence is one case:

- **[drlg/lifecycle § I](../specs/drlg/lifecycle.md#i-the-wanderer-tick)** still says no gate draw passed and keeps the roll and its no-spawn branch `[I]`. Since run:2026-10-21-sweep-monsters-a ([spawn § K](../specs/monsters/spawn.md#k-wanderers-the-tick), monsters/0002 § Plan 0038 batch H4a) one gate pass is logged in the Chaos Sanctuary: `WandererRoll` entered on that seed, one more step, mod 100 = 82, no further draw. Raise I1's roll draw and its `≥ 3` return to `[C]` on that run; keep the spawn branch, the region `+0x2C4` test and the mask width `[I]`; rewrite the first `[I]` bullet (no longer "no gate draw passed"); recount the front matter.
- **spawn § K1**: the header tags `[C]` everything but the mask width, the room `+0x78` test and the spawn branch, so the Levels `MonWndr` ≠ 0 test (0x0054F0AA) reads as confirmed. The one pass came in a `MonWndr` 1 level, and no logged tick passed the mask in a `MonWndr` 0 level, so the run cannot separate that test either (lifecycle I1 tags it `[I]`). Add it to the `[I]` bullet and the header's `[I]` list; the separate `[C]` bullet that `MonWndr` has no other reader stays.

After both land, bump `based_on` for drlg/lifecycle and monsters/spawn in wiki/levels, wiki/monsters and wiki/seed-to-world (their text already takes the weaker tags).
