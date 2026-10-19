# Common review fixes — spec-writer (specs and wiki)

Fixes the architect's reviews keep making on spec and wiki lanes. One rule each; check your diff
against all of them before you file the review request. Categories are those of the
[lane run ledger](../../../../docs/plans/metrics.md).

1. **Take the weaker tag.** A code reading is said "read from the code", never "confirmed" or "seen in
   the game"; when a spec contradicts itself, the wiki takes the weaker tag. Seen: four such fixes at the
   `lane/wiki2` review ([0037](../../../../docs/plans/done/0037-combat-formulas.md)); "never seen in the game" (`lane/wiki1`,
   [0038](../../../../docs/plans/0038-inferred-claims-sweep.md)).
2. **Scope "never", "every" and "only" to the cases the run met.** Seen: "never MonStats `boss`" in a `[C]`
   sentence (`lane/p37t`, 0037); "every choice" (`lane/wiki4`, 0038); the struck warps open question
   (`lane/p38s3`, 0038). Split a code-read part out of a `[C]` sentence: five resurrection NPCs in a `[C]` bullet
   whose run met one (`lane/p43s`, [0043](../../../../docs/plans/0043-items-economy.md)).
3. **Re-read the finding for each restated condition**: who, when, which branch. Seen: `SetBoss` party
   minions and the staff-mods type condition (`lane/wiki5`, [0039](../../../../docs/plans/0039-backlog-sweep-4.md)); warps F1's
   `Warp` = −1 case (`lane/p38s2`, 0038).
4. **Take the order of steps from the anchored instructions**, not from a summary. Seen: the release
   order (`lane/p38s`, 0038).
5. **Recount with a script**: front-matter tags, every number you restate, numbers in commit subjects.
   Seen: six primitives for seven (`lane/wiki5`, 0039); "dispatch" listed as raised in a subject
   (`lane/p38s3`, 0038); "22 claims" listed as 10 + 5 + 6 (`lane/p43s`, 0043).
6. **Rewrite a research-map row or bullet whole**; don't splice a new clause into the old punctuation.
   Seen: three research-map rows (`lane/p39s`, 0039); a sentence run into the next bullet (`lane/wiki1`, 0038).
7. **Close what your change makes stale**: answered open questions, ADR status, wiki paragraphs. Seen:
   ADR-0008 still "proposed" (`lane/p37s`, 0037); drlg/README open questions (`lane/wiki1`, 0038); wiki pages left
   with a W4 warning and an answered "unknown" (`lane/p43s`, 0043).
8. **Don't under-tag**: a raise the accepted ledger allows is stated at its strength. Seen: `burn = 2`
   (`lane/p37s`, 0037); cube G4 (`lane/p39s`, 0039); a shortfall the logs already covered (`lane/p43s`, 0043).
9. **Cite the exact instruction the finding gives**, and link the section that holds the object named.
   Seen: the cold-draw anchor (`lane/p37s`, 0037); the glossary *near list* link (`lane/wiki3`, 0038); a packing
   anchored to the checker's decoder, not the code's globals (`lane/p43s`, 0043).
