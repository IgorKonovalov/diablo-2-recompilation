# Common review fixes — spec-writer (specs and wiki)

Fixes the architect's reviews keep making on spec and wiki lanes. One rule each; check your diff
against all of them before you file the review request. Categories are those of the
[lane run ledger](../../../../docs/plans/metrics.md).

1. **Take the weaker tag.** A code reading is said "read from the code", never "confirmed" or "seen in
   the game"; when a spec contradicts itself, or two specs a page is based on disagree, the wiki takes the weaker tag. Seen: four such fixes at the
   `lane/wiki2` review ([0037](../../../../docs/plans/done/0037-combat-formulas.md)); "never seen in the game" (`lane/wiki1`,
   [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)); four code readings stated flat and a menu known only
   from a screenshot (`lane/wiki5`, [0042](../../../../docs/plans/done/0042-quests-travel.md)); the chest cut and `ilvl` hand-off stated confirmed on the objects page while objects § J3 kept `[I]` (`lane/s38h2c`, 0038). The wanderer gate's "1 in 32 768" and `MonWndr` test stated flat on wiki/levels and wiki/monsters while spawn K keeps the mask width and lifecycle I1 the `MonWndr` test `[I]` (`lane/swk`, 0038).
2. **Scope "never", "every" and "only" to the cases the run met.** Seen: "never MonStats `boss`" in a `[C]`
   sentence (`lane/p37t`, 0037); "every choice" (`lane/wiki4`, 0038); the struck warps open question
   (`lane/p38s3`, 0038). Split a code-read part out of a `[C]` sentence: five resurrection NPCs in a `[C]` bullet
   whose run met one (`lane/p43s`, [0043](../../../../docs/plans/done/0043-items-economy.md)); the partial repair's
   rounding and Wirt's ilvl floor inside `[C]` notes (`lane/p43t`, 0043). A boundary reached on one path is `[C]` on that
   path only: do 46's finisher calls, reached only on a bad skill id (`lane/s46c`, [0046](../../../../docs/plans/0046-skills-function-catalogue.md)); helper 2's test "at the caster's position" whose cases had casters of types 0, 1 and 3 only (`lane/s46d`, 0046). A wiki summary keeps the run's scope: "every room, monster, object and drop predicted" from the seed alone, for 37 games rebuilt with the walk, the fights and counted values taken from the recordings (`lane/s48p4`, [0048](../../../../docs/plans/done/0048-seed-to-world.md)). `MonRegionFindAdd`'s `nPool` clause and call arguments, the model's reading, inside the raise's `[C]`; spawn K1's header over the gate's `[I]` mask and `+0x78` tests (`lane/s38m`, 0038). Bit 13's writers named "NPCs with `interact` clear" in a `[C]` row while F2 keeps the `npc` half `[I]` (`lane/s38n`, 0038). `MulDiv`'s branches "overflow included" checked under emulation, on a wiki page, without the one faulting input the emulation leaves out (`lane/swk`, 0038).
3. **Re-read the finding for each restated condition**: who, when, which branch. Seen: `SetBoss` party
   minions and the staff-mods type condition (`lane/wiki5`, [0039](../../../../docs/plans/done/0039-backlog-sweep-4.md)); warps F1's
   `Warp` = −1 case (`lane/p38s2`, 0038); the store record's 4505 scoping (`lane/p43t`, 0043); handlers 21 and 30's chance ≤ 0 and no-record exits, which decide whether handler 30 steps a seed (`lane/s46d`, [0046](../../../../docs/plans/0046-skills-function-catalogue.md)). Level 6, the logged `PresetFallenVariant` case, listed among the unlogged ones (`lane/s38m`, 0038).
4. **Take the order of steps from the anchored instructions**, not from a summary. Seen: the release
   order (`lane/p38s`, 0038); do 124's bit 6 and list steps dropped around its draw and store (`lane/srng`,
   [0046](../../../../docs/plans/0046-skills-function-catalogue.md)). Restate every step between two anchored calls.
5. **Recount with a script**: front-matter tags, every number you restate, numbers in commit subjects.
   Seen: six primitives for seven (`lane/wiki5`, 0039); "dispatch" listed as raised in a subject
   (`lane/p38s3`, 0038); "22 claims" listed as 10 + 5 + 6 (`lane/p43s`, 0043). "With its two items" for one item per creation, two in all (`lane/s38m`, 0038).
6. **Rewrite a research-map row or bullet whole**; don't splice a new clause into the old punctuation.
   Seen: three research-map rows (`lane/p39s`, 0039); a sentence run into the next bullet (`lane/wiki1`, 0038).
7. **Close what your change makes stale**: answered open questions, ADR status, wiki paragraphs. Seen:
   ADR-0008 still "proposed" (`lane/p37s`, 0037); drlg/README open questions (`lane/wiki1`, 0038); wiki pages left
   with a W4 warning and an answered "unknown" (`lane/p43s`, 0043); quest-drops' Wirt-body
   route bullet left saying a run would settle it (`lane/p43t`, 0043); states E3's "stamina shrine not reached" left after the same clause in G6 was fixed (`lane/s47p3b`, [0047](../../../../docs/plans/done/0047-simulation-shortfalls.md)). Pool's "unit proxies" left for draw 3 after rng/0002 named it the store (`lane/s38m`, 0038).
8. **Don't under-tag**: a raise the accepted ledger allows is stated at its strength. Seen: `burn = 2`
   (`lane/p37s`, 0037); cube G4 (`lane/p39s`, 0039); a shortfall the logs already covered (`lane/p43s`, 0043). Split a mixed tag, don't extend the weaker one: H5's marks, compared in order (`[C]`), said read from the code with their call path (`[I]`) (`lane/s48p4`, 0048). A constant raised in one spec is raised in every spec that states it: lifecycle's *wanderer list* row left `[I]` beside spawn's `[C]` Inputs row (`lane/sfx`, 0038).
9. **Cite the exact instruction the finding gives**, and link the section that holds the object named.
   Seen: the cold-draw anchor (`lane/p37s`, 0037); the glossary *near list* link (`lane/wiki3`, 0038); a packing
   anchored to the checker's decoder, not the code's globals (`lane/p43s`, 0043). Keep the finding's mood: chain/0001's
   "the creation would be the monsters chain's" restated as "is" in a `[C]` row (`lane/s48p3`, [0048](../../../../docs/plans/done/0048-seed-to-world.md)). The `spawnCol` mask row anchored to the session run alone, for counts that are mostly kept-log calls (`lane/s38m`, 0038). The same row in drlg/collision, and "exercised since" / "reached since" the run that only counted what earlier logs held (`lane/s38n`, 0038).
