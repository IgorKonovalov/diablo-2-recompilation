---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../findings/save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "2026-10-20 (lane/p49r, plan 0049 P1): the 48 ilvl-1 magic items are starting items. ItemTypes Magic = 1 makes them magic, and sub_00534C70_StartItemCreate then frees their main property list (0x00534CB5), so the affix ids stay. The stock path does not reach it: no stock kit base is Magic = 1. The 5 rare ilvl-99 items are tools/d2s.py-built cube-recipe inputs (names only, default ilvl 99), not game creations. It belongs in player/creation: [player/0001 § Plan 0049 Phase 1](../../findings/player/0001-creation.md#the-s1a-creation-question-affix-ids-with-an-empty-property-list)."
---

[2026-10-16] from architect → reverser: plan 0038 S1a review, creation question (no S1a row depends on it). 53 magic, rare and crafted items in the game-written save corpus carry affix ids but an empty main property list: 48 magic items at ilvl 1 (the ring, amulet, jewel and small charm that the edited `charstats.txt` of run:2026-10-11-d2s-samples gives every class at creation; 40 in `workspace/samples/d2s/qit*.d2s`, 8 in run:2026-10-12-d2s-io's written saves) and 5 rare cube outputs at ilvl 99 (run:2026-10-15-cube-saves). Find why their affixes add no stats: the CharStats starting-item creation path (does it set affix ids without applying the affix properties, or apply them to a list the save does not write?) and the five cube outputs (which recipe and why). Say whether the stock path reaches it (stock CharStats gives no ring or amulet), and where it belongs (player/creation, items/cube or items/affixes). Context: [save/0001 § S1a](../../findings/save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16) (*Seen in passing*), [plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log) (S1a review)
