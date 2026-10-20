# Common review fixes — archivist

Fixes the architect's reviews keep making on table and format phases. One rule each; check your docs
against all of them before you file the review request. Categories are those of the
[lane run ledger](../../../../docs/plans/metrics.md).

1. **Check the findings before tagging a meaning.** Where a finding states it with addresses, write
   `[I]` and cite it; where a reviewed spec settles it, state it. Seen: the resurrection price `[L]`
   ([0043](../../../../docs/plans/done/0043-items-economy.md) P0); the four `SubWaypoint` levels ([0042](../../../../docs/plans/done/0042-quests-travel.md) P0); a
   raise missed ([0039](../../../../docs/plans/0039-backlog-sweep-4.md) P0).
2. **A sentence about code with no finding is `[L]`**; "no reader" needs a full xref, otherwise write a
   scope note ("combat/0001 reads none of these"). Seen: "set by code" ([0041](../../../../docs/plans/done/0041-stats-and-states.md) P0);
   ItemStatCost "not read" (0039 P0).
3. **Recompute universal data claims over the whole table** (case-insensitive for names) before writing
   "no", "every" or "N rows". Seen: 44 names both a skill and a state (0041 P0); *Find Potion* takes the
   tier above (0043 P0).
4. **Re-read the format doc and the findings a column touches.** Seen: ds1.md bits 18–19 against
   drlg/0001, and Levels level 0 as a town (`lane/arc4`, 0039).
5. **Label every count with its game type, difficulty and index kind.** Seen: 138/208 are classic
   Nightmare/Hell (0039 P0); record index called "Id" (0042 P0).
6. **List everything the request names**: every handler, every row asked for per row. Seen: `OperateFn`
   34 (0042 P0); the aura rows' passive columns (0041 P0).
7. **Quote a composed rule whole**, with its other branch. Seen: the Npc scaling for `v ≥ 0x10000` (0043 P0).
8. **Time in frames, never seconds** (ADR-0014). Seen: Shrines' "96 s" (0041 P0).
9. **Surprises for your plan's own later phases go into its *Done when***, not the backlog. Seen: 0041 P0
   ruling 4; 0043 P0 ruling 6.
