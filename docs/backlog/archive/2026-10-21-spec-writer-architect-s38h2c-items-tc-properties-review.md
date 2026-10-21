---
from: spec-writer
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/items/tc.md
  - ../../specs/items/properties.md
  - ../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21
  - ../../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21
resolution: "Reviewed 2026-10-21 (architect, on lane/s38h2c): accept with fixes (4: overclaim 2, misread 1, stale cross-reference 1); rulings and fixes in the plan 0038 log"
---

Review request, plan 0038 Phase 3, the **items/tc** and **items/properties** clusters (`lane/s38h2c`, from `main` `f805cdf`). Both waited on H2c (accepted 2026-10-21); every accepted batch of the two clusters is folded in one round: items/tc S2a, S4b (tc 64), H6d, H2a, H2b, H2c; items/properties S2b, S2c (prop 19), H2b, H2c.

- **Counts** (script over the body, the gate's rule): items/tc {C 49, I 81, L 6} → **{C 119, I 60, L 5}**; items/properties {C 130, I 35, L 2} → **{C 152, I 22, L 3}**; `updated:` 2026-10-21 on both. For the research-map rows (both still give the old counts and "updated 2026-10-20" / "2026-10-17").
- **items/tc raised `[C]`** (inventory rows): S2a tc 3, 4, 5, 7, 12, 16, 18, 21, 24, 25, 28, 32, 35, 36, 39, 50, 52, 61, 62, 66; tc 64 (S4b: § J with the J1 arithmetic and the `ilvl` hand-off); H2a tc 1, 2, 11, 34 (L361), 37, 45, 47, 59, 71; H2b tc 68; H6d tc 26; H2c tc 10 ×2, 55.
- **items/tc split** along the ledgers' remainders (remainder `[I]`): S2a tc 14 (unique/set clause), 19 (the `max(1, ·)` floor, now its own pseudocode line), 23 (superunique first), 29 and 31 (`noRatio`, its own pseudocode line), 30 (`idx ≥ g_nTreasureClasses`), 33 (fatal `0xF44`, `T = 0`, `0xFFFF`, the classic run off the end: each tagged on its line), 38, 40, 42 (the cap never acted, the clamp at 8), 48 (`cur ≥ 64`), 49 (classic raises), 51 (the H1 header now `[C]` "unless tagged", with H2, H3, H4 unique/set, H5 and the H6 `type`/`type2` reading tagged `[I]` on their lines), 57, 67, 69, 72, 73; H2a tc 22 (`bonewall`), 34 (L388, `Picks = 0`), 60 (equivalence, signedness), 70; H2b tc 58 (classic refusal); H6d tc 27 (`exp` state, party); H2c tc 56 (the `version ≥ 100` reject).
- **items/tc restated as no stock case, `[I]`:** tc 13 and 15 (new A1/A3 note), 41 (E2 note), 74 (reimplementation note).
- **H2c rulings followed:** tc 55's `type` against `type2` stays `[I]` (a pseudocode comment and its own H6 note; the upgrade draws between the roll and the test likewise, ratio words 4 and 5 were 0); "classic only" is `[C]` on the H2b expansion control, not on the `THR` flag; `sub_00633680_ItemIndexByCode` is cited for `lsd` (index 31).
- **items/properties raised `[C]`:** S2b prop 4 ×2 (staff mods modelled: *Inputs* row and H4 note), 5 (the closure added), 6, 8, 16, 18 L450 (E2 line and a note); S2c prop 19 L535 and L549 (F2 and F4 pseudocode, a new skip-bits note); H2b prop 20 ×2 (F4 line and note); H2c prop 12 (table row; the funcs-12-and-36 bullet split, func 36 `[I]`).
- **items/properties split:** prop 18 L454 (the reset after a change `[I]`), prop 19 L573 (the forced bits after the draw `[I]`), prop 14 (make branch `[C]` as "no `PROP_WriteStat` call", skips `[I]`; table row and a new bullet). prop 1 and prop 2 are rewritten with S2b's two corrections and stated `[C]` whole (the ledger's remainder was only the rewording); prop 1's vendors sentence, which S2b did not check, is split off `[I]`. **Ruling asked:** prop 9 (B3 note) I stated `[C]` whole, since its S2b remainder ("what 1 and 2 change when worn") is now the next note's `[C]` (plan 0041, stats/aggregate § J); take it back to "in part" if the remainder should stay on this note.
- **items/properties kept `[I]`:** prop 7 ×3 (A5 note restated as no stock case), prop 23 (the reimplementation note says why), prop 24 (the H2b shortfall added), prop 15 (func 24; its own `[L]` under *Open questions* with the Hellforge route, as the review ruled), prop 21 (*Wraithflight*, d-edit), prop 12's func-36 half.
- **Stale text closed:** tc *Open questions*: the chest-cut `[L]` struck; Hell, the `boss` gate, the negative-`Picks` stop, the Long Sword and the champions answered; `game.type` narrowed to value 1. tc's A note "upgrade draws of H6" corrected to H5. properties *Open questions*: the `MulDiv` line, the not-reached `[L]` rewritten, "`ITEMS_RollStaffMods` stays an oracle" struck.
- **Mismatch to note:** [objects § J3](../../specs/objects/README.md#j-operate-chests-and-containers-up-to-the-drop) still tags the tier-as-`ilvl` hand-off `[I]` (its raise waits for the objects round), while [items/tc § J](../../specs/items/tc.md#j-object-drops-named-only) and the objects wiki page now state it confirmed.
- **Wiki:** [items](../../wiki/items.md) (champions and Hell, the quest TC by a pet or hireling, the death-drop skips, the level-upgrade gates, the six-item stop, auto TCs, gold, chests, classic throwables and the Long Sword, `/players` and the cap, the drop seeds, the quantity rule, the property kinds, classic body armour, the untested lists) and [objects](../../wiki/objects.md) (the chest tier and the `ilvl` hand-off); `based_on` 2026-10-21 for items/tc on both pages and for items/properties on items.
- **Backlog:** closed the H2c, H2a and S2b-corrections entries; annotated (done in part) the H2b, H6d, S4b and S2a tc 64 entries. The S2c raise of prop 19 had no spec-writer entry; it is applied from the S2c ledger.

Not blocking.
