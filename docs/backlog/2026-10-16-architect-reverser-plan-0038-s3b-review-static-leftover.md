---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 S3b review, static leftover (the row stays counted as S3b, raised in part). special 43's remainder: read the four callers of `0x005A0120` (MonsterData `+0x1C`, the copied mod list) other than the packet builder, at 0x005423F8, 0x005428A9, 0x00597C87 and 0x005A4A5F; name their functions (the nearest symbols are the inactive-unit restores, `A1Q6_AndarielDeath` and `SuperUniqueSpawn`, not checked as the enclosing functions) and say what each does with the list, including whether a later append (a superunique's mod 22) is seen. Context: [monsters/0003 § S3b](../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16), [inventory § 2.6](../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews)
