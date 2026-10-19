---
from: architect
to: spec-writer
date: 2026-10-19
status: done
context:
  - ../plans/0043-items-economy.md#implementation-log
  - ../specs/items/economy.md
resolution: "Done 2026-10-19 (spec-writer, lane/p43t): new page docs/wiki/economy.md (Prices, repair, gold and wear) from the re-tagged items/economy, linked from the wiki index and from items-other-paths' vendor section; review request 2026-10-19-spec-writer-architect-plan-0043-economy-retag-and-wiki-review."
---

Plan 0043, wiki owner for the reviewed [items/economy](../specs/items/economy.md) (from the Phase 3 review, 2026-10-19; architect review-fixes rule 8). Add the item economy to the wiki (ADR-0012): a new page or a section of [items-other-paths](../wiki/items-other-paths.md) that covers prices (the three values, the NPC multipliers, `max buy`, the sell's lower-of-two), the gamble price, repair, gold (payment from gold then stash, the caps, the pile amount and gold find, the death loss) and wear (the armour pick, the chances, replenish), each section linking the spec. Take the weaker tag where the spec is `[I]` ("read from the code"). Replace the sentence "no wiki page covers it yet" in items-other-paths' vendor section with a link to the new text. When Phase 2b (`lane/p43b`) lands and the spec is re-tagged, write from the updated spec. Not blocking.
