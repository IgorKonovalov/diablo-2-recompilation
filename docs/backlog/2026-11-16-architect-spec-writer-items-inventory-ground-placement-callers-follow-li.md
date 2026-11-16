---
from: architect
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../specs/items/inventory.md
  - ../specs/drlg/lifecycle.md
  - ../wiki/inventory.md
resolution: ""
---

items/inventory § K's three-lives table names the ItemPlaceOnGround row's callers as "a player's drop, an overflow, DropGoldAmount, NPC menus, the cube's", and wiki/inventory's row ("How it got to the ground") follows it. drlg/lifecycle § A now states [C] that ItemPlaceOnGround has 12 direct calls in 11 functions, adding QUESTS_GiveItem, DropEar, PLAYER_CorpseCreate and TargetBeltItemToGround (drlg/0009 § 13); wiki/levels already gives the twelve. Bring the items/inventory row in line with lifecycle (the twelve calls [C] by the scan; what each caller drops stays [I], lifecycle's own tag), then wiki/inventory's row from it (and its based_on). Found at the lane/n66w review; not blocking.
