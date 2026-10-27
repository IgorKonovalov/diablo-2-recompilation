---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/save/d2s.md
  - ../specs/items/uniques-sets.md
resolution: ""
---

Plan 0038 Phase 3 (`lane/s38s`), the **save/d2s** (S1a, S1e, H1b, H1a) and **items/uniques-sets** (S2b, S2c, S1f,
H2b, H6d, H1a) clusters: old and new `{C, I, L}` for the research-map rows and the wiki's `based_on` dates (gate W4).
Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [save/d2s](../specs/save/d2s.md) | {C 91, I 149, L 3} | **{C 239, I 67, L 3}** | 2026-10-20 → 2026-10-27 |
| [items/uniques-sets](../specs/items/uniques-sets.md) | {C 71, I 55, L 4} | **{C 100, I 38, L 4}** | 2026-10-21 → 2026-10-27 |

- **Research map:** rewrite both rows whole (spec-writer rule 6); the H1a review left them at "Phase 3 ready".
- **Wiki (W4, done on this lane):** [saves](../wiki/saves.md) and [characters](../wiki/characters.md) `based_on`
  save/d2s 2026-10-27, [items](../wiki/items.md) `based_on` items/uniques-sets 2026-10-27. Restated on saves: the
  introduction, the big picture's expansion sections, when the game writes (the death save, no autosave, the host
  hook, the TCP/IP buffer, 8 KiB), the load checks and codes with the single-player reach, the header lists, class 7,
  the status checks, quests and waypoints, the load-time stat fixes and stat 30, the old stat form, skills, item
  lists, one item, property lists, the mercenary header, *What is not known yet*. On items: the override rules, the
  made-uniques set, the identified flag, the set paragraph, the fallback chain, the open-questions line.
  Characters is unchanged apart from the date: its stub-order, class-7 and saved-mercenary paragraphs rest on
  player/creation § A2 and § J and hirelings § F/§ H, which wait for H6g and H6f.
- **Cross-spec, for the review:** the saves page follows save/d2s (now `[C]`) for the header test order and the
  mercenary header's write side, while [player/creation § A2](../specs/player/creation.md#a-the-stub-and-the-servers-checks)
  and [hirelings F8](../specs/hirelings/README.md) still state those `[I]` (rows player-creation 8 and hirelings 24,
  raised by H1a and H1b, waiting for the H6g and H6f rounds). If the review holds rule 1 (the weaker tag) across specs
  here, those two saves passages go back to "read from the code" until then.
- **Not reflected, with the reason:**
  - the S1a pieces H1b met but no reviewed ledger raised (the rows stay S1a, raised in part): row 24's swapped write
    side, row 32's `& 0xFFF` mask, rows 123, 130 and 138's group 52; row 20's pet-type-7 test stays `[I]` beside the
    `[C]` expansion half;
  - the d-none rows and halves (save-d2s 2 and 18's callback halves, 3, 19, 50's ladder test, 67, 77, 78, 89, 95, 134,
    139's `gf` param, and the S1a d-none remainders of 92, 104, 119, 120, 130, 135; uniques-sets 2, 8, 10, 11, 14,
    16, 17, 19, 22, 25, 26, 30, 31, 43, 45) and the d-edit rows (uniques-sets 18, 37, 38, 41), kept `[I]`;
  - the shortfalls (save-d2s 1, 10, 17, 110, 114, 117, 124, 126; uniques-sets 12, 21) and the raised-in-part
    remainders the batch sections name, kept `[I]`;
  - the plan 0039 P1b statements (host bytes, status bit 1, NPC slots, the corpse record, the 8191 restore; the
    uniques-sets C8/C9 identification notes), which no batch carried, kept `[I]`;
  - the H1a entry's (k), the S1b leftovers in data/calc L417 and rng/seeds L362, not taken (other clusters).
