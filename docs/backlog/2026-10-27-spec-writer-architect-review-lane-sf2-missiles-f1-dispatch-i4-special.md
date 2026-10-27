---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/skills/missiles.md#f-the-packet-at-the-hit-missile_builddamage
  - ../specs/skills/dispatch.md#i-the-skill-packet
  - ../specs/monsters/special.md#j-other-entry-paths-and-pre-existing-mods
  - ../specs/drlg/room-tiles.md
resolution: ""
---

**Review request: `lane/sf2`** (spec-writer, branched from `main` `6ad383c4`). Carries out the two entries released at the `lane/rbd` review: [missiles F1 and dispatch I4](archive/2026-10-27-architect-spec-writer-skills-missiles-f1-mastery-and-dispatch-i4-kick.md) and [MonPostCreateBoss and 0x400](archive/2026-10-27-reverser-spec-writer-postcreateboss-table-and-entry-bit-0x400.md). Specs touched: skills/missiles (C 46, I 92 → 95, L 6 → 7), skills/dispatch (C 72 → 73, I 187 → 189, L 10 → 11), monsters/special (C 149 → 151, I 70 → 86, L 4), drlg/room-tiles (C 121 → 122, I 34 → 35, L 0; `updated:` 2026-10-21 → 2026-10-27). Wiki: skills (F1 and I4 text, two open items), `based_on` of levels, randomness and seed-to-world for room-tiles. Points to check: I4's non-Kick `SrcDam` 0 formula raised to `[C]` with the Kick minimum (skills/0007 § 3 and the Skills table doc hold it `[C]`, rule 8); Kick's start-hit damage not settled by skills/0003 § 5, so an `[L]` and a [reverser entry](2026-10-27-spec-writer-reverser-kick-start-hit-damage.md); special § J's case table carries a tag per row (13 `[I]`, the 526 row split `[C]` mod / `[I]` hook). Plan 0038 log entry and the ledger row (usage —) added.
