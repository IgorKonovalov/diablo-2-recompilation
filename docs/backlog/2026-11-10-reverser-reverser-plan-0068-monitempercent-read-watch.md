---
from: reverser
to: reverser
date: 2026-11-10
status: open
context: ["../findings/data/0006-loaded-tables-and-bundles.md", "../plans/done/0068-game-files-coverage.md"]
resolution: ""
---

**Harness piece (reverser, harness lane): a read watch on the `MonItemPercent` records.** Not blocking (plan 0068
Phase 4 carries nothing for this table: it has no reader).

[data/0006 § 1](../findings/data/0006-loaded-tables-and-bundles.md#1-monitempercent-plan-item-1) finds the table loaded
in every run (`sub_00654F20_MonItemPctLoad`, records in `g_pMonItemPercent` 0x0096D484) and its getter
0x00654FE0 dead (no caller in the image, two tools). That "no reader" is `[I]` only because a static scan cannot see an
address computed at run time.

The piece: in any already-planned stock session that kills monsters (Normal is enough; a champion and a unique kill
help), log the record pointer at 0x00654FAD and set a hardware read watch (`rwatch`, 8 bytes) on it for the whole
play window, plus a breakpoint on 0x00654FE0. Control, live over the same window: a read watch on one `monstats`
`TreasureClass1` cell of a monster class killed in the session, which `MONSTER_DropItems` reads at each death. Pass:
the control fires at each logged death and neither the watch nor the breakpoint fires (except the unload's free at
0x00654FC0, which reads the pointer, not the records). This raises data/0006 § 1.3 to `[C]` for the session.
