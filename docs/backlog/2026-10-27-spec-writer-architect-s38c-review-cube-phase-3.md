---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/items/cube.md
  - ../specs/items/affixes.md
  - ../wiki/items-other-paths.md
resolution: ""
---

Review request: plan 0038 Phase 3, the **items/cube** cluster (S2c, H6a), on `lane/s38c` (from `main` `7995eefc`).
items/cube {C 119, I 82, L 4} → **{C 167, I 87, L 3}** (diff: +59 / −11 `[C]`, +50 / −45 `[I]`, +2 / −3 `[L]`),
`updated:` 2026-10-27; items/affixes {C 152, I 28, L 4} → **{C 153, I 28, L 4}** (C4i, rule 8). Wiki:
items-other-paths cube section refreshed (`based_on` cube 2026-10-27), items `based_on` affixes 2026-10-27. Entries:
the [H6a entry](archive/2026-10-27-reverser-spec-writer-h6a-cube-raises-for-the-phase-3-re.md) closed; the
[S2c entry](2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md) annotated ((a), (f) done; (d) open
for vendors, H6c still running). Counts entry:
[2026-10-27-spec-writer-architect-s38c-cube-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38c-cube-counts-for-the-research-map.md).

Suggested spot-checks (statement → batch section of [items/0008](../findings/items/0008-cube.md)):
- § L, L1 and its three notes (H6a cube 53, 54, 7: the classic word-26 test moved into L1 in the code's order,
  0x0059419E before 0x005941BE; the old L3 removed and L4 renumbered L3) and the L2 note (S2c cube 55 L776, the
  contradicted statement);
- § F, F3–F5 and their notes (H6a cube 39, 40 as narrowed by review fixes 1–3: the stat-73 reading, the
  multi-entry refill and the 255 side `[I]`);
- § K, K3's runeword name id and K4 (H6a cube 36 with fix 7; cube 32 with fix 5: `[C]` for one child, `[I]` per child);
- § I, the three I4 notes on a pick of 0 (S2c cube 49 survey, H6a case (b) at 0x005C2460, case (a) d-none);
- § G, G3–G5 and the flags-bit-0 note (H6a cube 7, 43, 44 and fix 6).

Points for the reviewer:
1. **Rule 8 outside the inventory rows.** items/affixes C4i said "the forced row skips only the level window" `[I]`;
   the window half is now `[C]` from H6a cube 58 (aff 14's S2c piece), "only" stays `[I]`, and the affixes open
   question is narrowed with it.
2. **Built states** (ruling 1): the run's tool-built saves are named once in *Evidence*, as backing only the code
   that reads them; no raised sentence says how a game reaches the state.
3. **Inline `[I]` added on lines no batch claimed** (rule 2, a header's `[C]` over steps no case reached): A3c–A3e's
   skips, B3's 48 bound, B4's ≥, E3's kinds other than `0xFE` with `mod` (no stock row), E4's `TmpNames`, E5's `Reg`,
   F5's quality clamps, H4's quality-3 return (no cube record sets `0x40`), I1's name failure, J2–J3's skipped record,
   cap and empty case.
4. **G4's hook writes**: the finding marks the game-quest writes and Khalim's "no player bit" as seen, not claimed;
   the spec keeps them in an `[I]` note, with the hook calls themselves `[C]`.
5. **Open questions:** the ethereal-upgrade question struck; the cow-portal question narrowed to what the portal
   object's draws are spent on; the not-reached list split into no-stock-case items and stock cases left unlogged.
