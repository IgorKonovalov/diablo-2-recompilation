---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../../plans/done/0042-quests-travel.md#implementation-log
resolution: "Done: (a) [Levels § Travel](../../tables/Levels.md#travel-plan-0042-phase-0) QuestFlag/QuestFlagEx, Portal, Position; (b) [Objects § Waypoints and portals](../../tables/Objects.md#waypoints-and-portals-plan-0042-phase-0) handlers, 410 never placed, Sync 0 rows; (c) quest-w9lost, quest-w9book, quest-w39summit in [d2s.md § Quest and travel saves](../../formats/d2s.md#quest-and-travel-saves) (built, not loaded)."
---

[2026-10-17] from reverser → archivist: plan 0042 Phase 1 readers for the table docs (not blocking). (a) [Levels § Travel](../../tables/Levels.md#travel-plan-0042-phase-0): `QuestFlag`/`QuestFlagEx` are read by the portal operate `0x00584870` (0x005849BB–0x00584A19: the destination level's word, bit 0, for someone else's class-59 portal; expansion reads `QuestFlagEx`), [quests/0002 § 6](../../findings/quests/0002-travel.md#6-town-portals); `Portal` (leveldefs `+0x8C`) has no reader in the 28 `LevelDefGet` sites; `Position` decides the level-seed step of every placement (quests/0002 § 4). (b) [Objects § Waypoints and portals](../../tables/Objects.md#waypoints-and-portals-plan-0042-phase-0): the handlers are now named (`OBJOP_Portal` 15, `sub_00584E30_WaypointOperate` 23, `OBJOP_ArcanePortal` 34, `OBJOP_LevelPortal` 43, `sub_00584750_DurancePortalOperate` 46; `OBJINIT_TownPortal` 11, `OBJINIT_Portal` 12, `OBJINIT_Waypoint` 17); 410 `Siege Control` is never placed; the five `Sync` 0 waypoint rows (429, 494, 496, 511, 539) draw their unit seed at each mode change. (c) Quest-step saves for Phase 2: quests/0001 § 7–10 name the steps; a word-9 creator with bits 0 and 5 and no `ass` (the join clear) and a word-39 save at the summit (the 120 → 118 refusal) are the two not covered by the Phase 0 recipes. Context: [plan 0042 log](../../plans/done/0042-quests-travel.md#implementation-log)
