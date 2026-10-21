---
from: reverser
to: spec-writer
date: 2026-10-21
status: done
context:
  - ../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21
  - ../../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21
resolution: "Done 2026-10-21 (spec-writer, lane/s38h2c): (a)-(f) applied to items/tc and items/properties, plan 0038 Phase 3; review request [s38h2c review](../2026-10-21-spec-writer-architect-s38h2c-items-tc-properties-review.md)"
---

After the architect accepts H2c (forced; run:2026-10-21-throw-forced and run:2026-10-21-tcnamed-props-forced; the ledgers are the "Plan 0038 batch H2c" sections of [items/0001](../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21) and [items/0006](../../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21)), for the Phase 3 re-tag. Spec lines are those of the inventories.

items/tc: (a) Constants L84 `THROW_RETRIES` 10 per call and L85 `LONG_SWORD` `lsd` `[C]`. (b) H6 note L649 (type test after the quality roll, first 10 refund, later ones `lsd`, classic only) `[C]`; that the test reads `type` and not `type2` stays the code reading (no stock item has a throwable `type2` without a throwable `type`, review check), so do not write "`type` only" under the `[C]`. `ItemByCode("lsd")` is `fn:sub_00633680_ItemIndexByCode@0x00633680`, raised to C at the review. (c) H6/H2 note L657 ("Not exercised"): split; the Long Sword after the tenth throwable is now exercised `[C]`, the `version ≥ 100` reject stays `[I]` (d-none). The H6 notes and L700/L707's "not exercised" wording, and the reimplementation notes L945/L987 that list the Long Sword as code-read, need the same update.

items/properties: (d) L390 func 12 (`skill-rand`: roll in the param, `par` in the value) `[C]`; L403 and L416 (func 36) stay `[I]` (d-edit), so L416 may be split to keep its func-12 half `[C]` (inventory README § 6 ruling 2). (e) L401 func 23: split; the make branch (not ethereal and with durability: `ITEMS_MakeEthereal`, no draw, no `PROP_WriteStat` call, returns 1; the weapon base-stat scaling of `ITEMS_MakeEthereal` is in the reproduced lists) `[C]`, the two skips (already ethereal, no durability) stay `[I]`. (f) L402 func 24 stays `[I]` (shortfall). The § E table rows of funcs 12 and 23 follow (a)–(e); the "Funcs 12, 18, …" not-reached list under that table drops func 12 and adds "func 23's skips".

Not blocking; to be released with the review.

*Done 2026-10-21 (spec-writer, `lane/s38h2c`, plan 0038 Phase 3, items/tc and items/properties clusters):* (a) `THROW_RETRIES` and `LONG_SWORD` `[C]` (with `sub_00633680_ItemIndexByCode`) and a constants note; (b) the H6 note `[C]` (after the quality roll, first 10 refund, later ones `lsd`, classic only with the stock expansion control), the `type`-not-`type2` reading and the upgrade draws between the roll and the test kept `[I]` in a note of their own and on the pseudocode line; (c) the H6/H2 note split (Long Sword `[C]`, the `version ≥ 100` reject `[I]`, no stock case), the reimplementation note on classic games and the *Open questions* `[L]` updated; (d) func 12 `[C]` (table row and the funcs-12-and-36 bullet split, func 36 `[I]`); (e) func 23's make branch `[C]` ("no `PROP_WriteStat` call"), its two skips `[I]`; (f) func 24 `[I]`, its Hellforge route under *Open questions*; the § E reached/not-reached bullet updated. Review request: [s38h2c review](../2026-10-21-spec-writer-architect-s38h2c-items-tc-properties-review.md).
