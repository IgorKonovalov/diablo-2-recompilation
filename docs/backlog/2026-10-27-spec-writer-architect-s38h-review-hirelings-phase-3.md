---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/hirelings/README.md
  - ../wiki/characters.md
resolution: ""
---

Review request: plan 0038 Phase 3, the **hirelings** cluster (S3a, S3b, H4b, H1b, H1a, H6f), on `lane/s38h` (from
`main` `fcce5b4d`). A partial pass on the sockets precedent: rows 3, 30 and 33 stay `[I]` for H1c's small re-tag.
hirelings {C 95, I 39, L 6} → **{C 137, I 41, L 7}** (line diff +43 / −1 `[C]`, +32 / −30 `[I]`, +2 / −1 `[L]`),
`updated:` 2026-10-27. Wiki: the hireling sections of [characters](../wiki/characters.md), `based_on` hirelings
2026-10-27. Research-map row rewritten whole; root README row 2026-10-27. Entries: the
[H6f entry](archive/2026-10-27-reverser-spec-writer-h6f-hirelings-raises.md) and the
[H1b entry](archive/2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises.md) closed; the
[H1a entry](2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises.md) annotated (hirelings 32 done; 3,
30, 33 for H1c; player/creation and (k) open). No S2c or S3b entry part names hirelings. Counts entry:
[2026-10-27-spec-writer-architect-s38h-hirelings-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38h-hirelings-counts-for-the-research-map.md).

Suggested spot-checks (statement → batch section of [hirelings/0001](../findings/hirelings/0001-hirelings.md)):
- § C, the two C2 notes (H6f rows 1, 9: the skip `[C]` at 0x00578BD3, the reach `[I]` with 0x00572CFF and the
  0x00572C98 loop, stated as no stock case);
- § F, F1's split lines and its four notes (H6f rows 17, 18, 21: the reads and passes `[C]`, the two refusals `[I]`
  server checks the stock client did not send, the client test unread, ruling 2), the F3 stash note and `HIRE_Hire`'s
  no result;
- § G, the new levelling block G2–G7 and its notes (H6f row 25: `2·gain` and the cap's `min` `[C]`; `M =
  ExpMaxLevel(0) − 1`, tested before the write at 0x0057E8F2, and the loop bound `[I]`; `MERC_CapExpGain`'s unsigned
  width `[I]`; the `·86 >> 8` share);
- § H, H3 and its two notes (row 27 on its built state: the clamp `[C]`, the u16 add and unsigned compare `[I]` with the
  wrap bound 62 124 / 62 125), and H12 (row 29: a shortfall, the `+0x60` list's writer unread, no "no other call");
- § A, the A2 and A3 notes (S3b rows 7, 8: the full-table data check and the writer/reader pairs; the fatal branches
  `[I]`).

Points for the reviewer:
1. **Inline `[I]` added on lines no case reached** (rule 2): A1 (`id > 255`), A2's `i < 0`, D1's `pHireTable`
   return, D5's full-table return, E2's `k = 0`; each carries a short reason.
2. **G2 is `[I]` as a call path** (`XP_Compute` at the mercenary's level, the finding's read-before-run paragraph);
   G3–G7's `[C]` lines check the later steps. G5's test order is not given beyond the two anchored tests; an `[I]`
   note says so rather than guessing an order.
3. **Built states** (ADR-0013 Neutral) are named once in *Evidence* and in the H3 note ("a tool-built save"), backing
   only the reading code.
4. **One `[L]` added** in *Open questions*: the two reads of the reverser entry (the client hire-line test, the
   `PlayerPlaceInAct` list), so the conditional d-none parts have a visible gate. The old not-reached list is struck
   and rewritten.
5. **Not edited:** items/economy's resurrection NPC-class bullet (150 and 515 now run cases), to avoid crossing
   `lane/s38v`; wiki/saves's `based_on` (W4 warning; `lane/wiki`'s page). Both are in the counts entry.
