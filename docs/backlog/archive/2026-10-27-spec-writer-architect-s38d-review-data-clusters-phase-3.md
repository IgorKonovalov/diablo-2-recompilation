---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/data/excel.md
  - ../../specs/data/strings.md
  - ../../specs/data/README.md
  - ../../wiki/game-data.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (10), plan 0038 log § lane/s38d review. Counts data/README {C 9, I 2, L 0}, data/excel {C 144, I 51, L 2}, data/strings {C 88, I 31, L 3}; rulings on the three points recorded there."
---

Review request, plan 0038 Phase 3, the **data/excel**, **data/strings** and **data/README** clusters (`lane/s38d`, from
`main` `41500789`). Their batches are S1b, S1e, S1f (data/excel 65, 69) and H3b (inventory § 5), all accepted (S1b
2026-10-16, S1e and S1f 2026-10-17, H3b 2026-10-27); the data/excel round folds plan 0039 P1b (a), P1c (a) and the 11 W1
warnings. Every raise was checked against the "Plan 0038 batch S1b, S1e, S1f, H3b" sections of data/0001–0004 and
player/0001 and the inventory § 2.6 blocks.

- **Counts** (script over the body, the gate's rule): data/README {C 3, I 5, L 0} → **{C 9, I 2, L 0}**; data/excel
  {C 42, I 100, L 8} → **{C 144, I 45, L 2}**; data/strings {C 60, I 42, L 3} → **{C 88, I 29, L 3}**; `updated:`
  2026-10-27 on all three. The new `[C]` count exceeds the raised rows because restated evidence bullets carry their own tag
  and mixed rows were split (rule 8).
- **H3b** (run:2026-10-27-sweep-data-load): data/README 2–4 and the TC row 5 (callers named, `TC_GetByName` an `[I]`
  dead-code note, ruling (b)); data/excel 1–7, 8 (as row 5), 17, 18, 20, 24, 25 (with the outside-`LoadTable` reads),
  27, 50 (byte `[C]`, clamp `[I]`, ruling (1)), 71 (J4 with levels `+0x033..+0x035` and their writers, ruling (d);
  monstats `+0x036`/`+0x038`, `+0x04A`/`+0x04B` and "never written" outside the window `[I]`), 74 (fallback `[I]`); the S1b
  remainders data/README 1 and data/excel 30 (scoped to `DATATBLS_LoadTable`, the `hitclass` read and the 18th `sounds`
  call, ruling (c)); data/strings 2, 6, 22 (raw name `[I]`), 29 (byte `[C]`, clamp `[I]`) and the `CYR` correction in § H
  (order and exit `[C]`, the test `[I]`, ruling (e)); G1a the post-pass lookups `[C]`, the store `[I]` (fix (9)).
- **S1b:** data/excel 9–14, 19, 21, 23, 26, 29, 31, 33 (split), 34 ×4, 35, 38, 41 ×6, 42 ×8 (split per sub-claim), 45–49,
  55, 57 (split), 61–63 (split), 67, 68, 72, 73 (split), 75–78; data/strings 1, 3, 11, 21, 31, 33.
- **S1e** (run:2026-10-17-sweep-emu): data/excel 16, 36, 37, 40, 51 (index map `[C]`, values and fault `[I]`, architect
  addition (a)), 52, 53, 56, 60, 64, 66; data/strings 4, 5, 10, 12, 14, 16, 17, 20 (index `[C]`, cache-miss text `[I]`,
  addition (c)), 24, 25, 32, 35. The unreachability sentences of strings § C keep `[I]`.
- **S1f** (run:2026-10-17-sweep-emu2): J3's five rows with the widths ((d)), the 0x17/0x18 length/row/column `[I]`, the
  J2f–J3 order note; (g) the NULL-callback skip and the first pass's registration gate as `[I]` notes.
- **Plan 0039:** P1b (a) the G2 auto-TC details moved into G2 `[C]` (the rebuild-failure branch `[I]`), the post-pass
  and walk open question struck, the u16 list at `0x0096CA78` stated in § D `[I]`; P1c (a) H3's every-reader scan `[I]`
  beside the pool's `[C]`. **W1:** the 11 data/excel warnings cleared (gate W1 0 for the spec).
- **Open questions:** data/excel 8 → 2 `[L]` (loose files, H3, G2, post-pass, `Lilith`, the u16 list struck; d2kfixup/d2delta
  kept; the padding-reader question narrowed); data/strings keeps 3, its fallback `[L]` narrowed to the fatals.
- **Points to check:** (1) data/excel 28 (d-none) is restated, not raised: B1's mixed-archive note now states the S1b
  compile identity `[C]` and that the authoritative side has no observable, and drops "the `patch_d2` `.txt` edits are not
  live" (also from the reimplementation notes and the wiki). (2) The Constants row of the archive priorities is `[C]` on
  H3b's logged opens (A1 is raised with the same numbers), beyond S1b row 11's "d-none for the numbers". (3) data/excel
  I3's case-sensitivity stays `[I]` per S1b row 57, while data/strings E2 states the case-sensitive `strcmp` `[C]` (plan
  0028); one of the two may want aligning. (4) The E2 duplicate note: the rule `[C]`, "never fires on stock data" `[I]`.
- **Backlog:** closed the H3b, W1, plan 0039 P1b and P1c, and S1b entries; annotated the S1e corrections entry (save/d2s
  open), the S1e review additions entry ((d) open) and the S1f entry (items/uniques-sets open). Counts entry
  [2026-10-27-spec-writer-architect-s38d-data-clusters-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38d-data-clusters-counts-for-the-research-map.md).
- **Not edited** (no entry required it): monsters/*, skills/*, combat/*, stats/states, items/economy, rng/seeds; the
  skills/missiles F1 entry waits for `lane/rbd`.

Not blocking.
