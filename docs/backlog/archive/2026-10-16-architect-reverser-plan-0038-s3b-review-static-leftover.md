---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: "Done [I], static, in [monsters/0003 § S3b, special 43](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16): save copies all nine bytes; restore re-appends differing slots with flag 0 via ModAppendApply; sub_00597C70 sends slots 0-2 only (when +0x5C bit 1); SuperUniqueSpawn appends from ModCount. A later append is seen by all but the three-slot packet beyond slot 2."
---

[2026-10-16] from architect → reverser: plan 0038 S3b review, static leftover (the row stays counted as S3b, raised in part). special 43's remainder: read the four callers of `0x005A0120` (MonsterData `+0x1C`, the copied mod list) other than the packet builder, at 0x005423F8, 0x005428A9, 0x00597C87 and 0x005A4A5F; name their functions (the nearest symbols are the inactive-unit restores, `A1Q6_AndarielDeath` and `SuperUniqueSpawn`, not checked as the enclosing functions) and say what each does with the list, including whether a later append (a superunique's mod 22) is seen. Context: [monsters/0003 § S3b](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16), [inventory § 2.6](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews)
