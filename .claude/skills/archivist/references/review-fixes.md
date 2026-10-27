# Common review fixes — archivist

Fixes the architect's reviews keep making on table and format phases. One rule each; check your docs
against all of them before you file the review request. Categories are those of the
[lane run ledger](../../../../docs/plans/metrics.md).

1. **Check the findings before tagging a meaning.** Where a finding states it with addresses, write
   `[I]` and cite it; where a reviewed spec settles it, state it. Seen: the resurrection price `[L]`
   ([0043](../../../../docs/plans/done/0043-items-economy.md) P0); the four `SubWaypoint` levels ([0042](../../../../docs/plans/done/0042-quests-travel.md) P0); a
   raise missed ([0039](../../../../docs/plans/done/0039-backlog-sweep-4.md) P0); a post-boundary outcome under a `[C]` (Levels `Teleport`) and the summons' MonEquip rows "walked" `[I]` with the `oninit` gate unread ([0051](../../../../docs/plans/done/0051-backlog-sweep-6.md) P0b); d2s.md's "the version tested for stat 72 is the save's" `[I]` where save/0001 row 68 (its `lane/s38s` review note) and the spec state it `[C]` (`lane/a71`, [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)).
2. **A sentence about code with no finding is `[L]`**; "no reader" needs a full xref, otherwise write a
   scope note ("combat/0001 reads none of these"). Seen: "set by code" ([0041](../../../../docs/plans/done/0041-stats-and-states.md) P0);
   ItemStatCost "not read" (0039 P0). A builder's own choice written as layout is the same fault: d2s.md's version-71 mode from `location`, the 30 `if` bytes and stat 134's 16 zero bits, listed as choices at the `lane/a72` review ([0038](../../../../docs/plans/0038-inferred-claims-sweep.md)).
3. **Recompute universal data claims over the whole table** (case-insensitive for names) before writing
   "no", "every" or "N rows". Seen: 44 names both a skill and a state (0041 P0); *Find Potion* takes the
   tier above (0043 P0); MonStats2's `m<mode>` "every set bit names a record" checked over the 603 rows MonStats names, not the 609 ([0050](../../../../docs/plans/0050-animation-frame-timing.md) P0); `compellingorb` called "the same code" as the `9A` rows where the file has `9a`, and Missiles `HitClass` linked as the packet's whole `+0x60` without counting the 122 set rows whose value carries a high nibble (`lane/a3f`, 0050).
4. **Re-read the format doc and the findings a column touches.** Seen: ds1.md bits 18–19 against
   drlg/0001, and Levels level 0 as a town (`lane/arc4`, 0039); Missiles `VelLev`'s part 2 link without skills/0002 § 12's review note (a level-1 `spike1` separates it; `lane/a50t`, [0050](../../../../docs/plans/0050-animation-frame-timing.md)); d2s.md's open question still listing ears, personalized names and realm data as unexercised after the lane raised them, and § Realm data saying the field "closes every item record" where an extended item's type fields follow it (`lane/a71`, 0038).
5. **Label every count with its game type, difficulty and index kind.** Seen: 138/208 are classic
   Nightmare/Hell (0039 P0); record index called "Id" (0042 P0).
6. **List everything the request names**: every handler, every row asked for per row. Seen: `OperateFn`
   34 (0042 P0); the aura rows' passive columns (0041 P0).
7. **Quote a composed rule whole**, with its other branch. Seen: the Npc scaling for `v ≥ 0x10000` (0043 P0); Skills `InTown`'s start 40 town test scoped to "a monster with a target" where the finding exempts every monster (0051 P0b); MonStats `aidel`'s re-queue without its "next AI event not later than now" condition and PlrMode's mode ends without row 19's get-hit branch (`lane/a51f`, [0050](../../../../docs/plans/0050-animation-frame-timing.md) items 3–4). d2s.md's base-adjustment row without its 89-and-above default and the version-71 list without the corpse's modes 0, 1, 6 and the failure branches (`lane/a72`, 0038). MonAI's "no index past 147 reaches a row" from `MonAiEntryGet` without items/0001's "with `EDX` = 0": the other branch reads a second table at `0x0073D358` (`lane/a52`, [0052](../../../../docs/plans/0052-monster-ai.md) P0).
8. **Time in frames, never seconds** (ADR-0014). Seen: Shrines' "96 s" (0041 P0).
9. **Surprises for your plan's own later phases go into its *Done when***, not the backlog. Seen: 0041 P0
   ruling 4; 0043 P0 ruling 6; the `dru` `+0x17C` forward sent to "§ Phase 1b item 3" but not written into that item (0051 P0b); HitClass's open question sent to Phase 1.3 but not in its *Done when* (0050 P0). the MonStats `9A` walk-base `[L]` and anim/0002's answered open question left as "the reverser's to close" with no route (`lane/a50t`, folded into P1.3 at the review). When a prompt limits plan edits to the log, list them there; the review folds them (0050 P0 ruling d).
