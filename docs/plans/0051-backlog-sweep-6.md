# 0051 — Backlog sweep 6: the catalogue's column readers, the static optionals and the routing of the rest

> **Status:** approved 2026-10-25 (owner); Phase 2 in part done at approval (one entry closed)
> **Created:** 2026-10-25
> **Owner skill(s):** archivist, reverser, human
> **Related ADRs:** 0006-docs-gate, 0013-forced-path-runs-cell-level, 0015-emulated-reproduction, 0018-backlog-one-file-per-entry, 0019-backlog-closed-entries-archive, 0021-observed-boundaries-in-emulation

## TL;DR

**Question:** of the 46 open backlog entries (2026-10-25, `python3 -I tools/backlog.py list`), which can be closed now
by a lane with no harness slot, and where does each of the others belong? When it is done, the sixteen archivist
entries are closed (the table docs link the code readers plans 0046 and 0048 found), the reverser's slot-free
remainders are done or annotated, and every other entry carries a dated routing note naming the plan, phase or batch
that closes it. **Phases 0, 1a and 1b need no slot; Phases 0 and 1a need no Ghidra either**, so idle static lanes can
take them as soon as the plan is approved.

## Context

- **The backlog on 2026-10-25:** 46 open entries (the 47 files of `docs/backlog/` less its README), by addressee:
  archivist 16, reverser 8, spec-writer 17, reverser and spec-writer 1 (its reverser half done), human 4.
- **Why now.** Both static lanes are idle: plan 0046 Phase 1 closed on 2026-10-21, plans 0047, 0048 and 0049 are
  closed, and the next static work (plan 0050 P1, plan 0052 P1) waits for its gates. The harness slots are held by
  `lane/h4a` (plan 0038 H4a, slot 1) and `lane/p45h` (plan 0045 P2, slot 2).
- **What this sweep does not take.** The 18 spec-writer entries (17 to the spec-writer and the spec-writer half of
  the S2a tc 64 entry) are plan 0038 Phase 3 inputs, each waiting for a cluster whose harness batches have not all
  been accepted; the § Routing table below records each one's cluster and the batch it waits for, and they stay with
  plan 0038. The harness pieces stay with the batches that carry them. Plan 0039's data/excel fold stays an item of
  plan 0038 Phase 3's data/excel cluster (owner, 2026-10-20).
- **The gate on 2026-10-25** (`python3 -I tools/gate.py`, fast tier GREEN): 11 warnings, all W1 in
  `docs/specs/data/excel.md`, held for that fold (backlog `2026-10-17-reverser-spec-writer-gate-w1-a-c-i-statement.md`).

## Phases

### Phase 0 — Column readers into the table docs
- **Owner skill:** archivist (**no slot, no Ghidra**: may start on approval)
- **What:** link each code reader the entries name from the table doc's column row, with the tag the finding (and its
  review) gives; write the one missing table doc.
- **Items (16)**, in two lane runs:
  - **P0a (8), the plan 0046 entries of 2026-10-20:**
    1. `2026-10-20-reverser-archivist-plan-0046-9a-missile-do-params.md` (Missiles `SubMissile1`, `Param1..5`, `Range`,
       `Size`; Skills `calc1`/`calc2`);
    2. `2026-10-20-reverser-archivist-plan-0046-9b-missiles-skills-column-readers.md` (Missiles `dParam1/2`, `EType`,
       `DmgCalc1`, `ProgOverlay`, `HitFlags`/`ResultFlags`; Skills `ELen` bands, `Param1/2`; MonStats2 `small`/`large`);
    3. `2026-10-20-reverser-archivist-plan-0046-9c-missiles-skills-column-readers.md` (Missiles `HitSubMissile2..4`,
       `sHitPar1/2`, `SHitCalc1`; Skills `TargetPet`, `auratargetstate`, `aurastate`, `aurafilter`, `Param1..6`);
    4. `2026-10-20-reverser-archivist-plan-0046-9d-missiles-skills-column-readers.md` (Skills `Kick`, the physical and
       elemental length maps; Missiles `sHitPar1..3`, `Param4`, `CollideKill`, `pSrvHitFunc`; MonStats2 `large`);
    5. `2026-10-20-reverser-archivist-plan-0046-ama-skills-column-readers.md` (Skills `ToHit` map, `calc1..3`, the aura
       block, `srvmissileb`, the summon words; MonStats2 `MeleeRng`);
    6. `2026-10-20-reverser-archivist-plan-0046-nec-skills-monstats-column-readers.md` (Skills aura and summon words,
       `srvmissilea`; MonStats2 `corpseSel`, `revive`; MonStats `Velocity`; DifficultyLevels `AiCurseDivisor`; States
       `udead`);
    7. `2026-10-20-reverser-archivist-plan-0046-pal-skills-charstats-column-readers.md` (Skills `mana`/`lvlmana`/
       `manashift`, `perdelay`, aura and passive words, `Param1`; CharStats `RunVelocity`; MonStats `Run`, signed);
    8. `2026-10-20-reverser-archivist-plan-0046-sor-skills-missiles-column-readers.md` (Skills `startmana`,
       `progressive`, `Param2`/`Param7`/`Param1`, `aurarangecalc`, `auralencalc`, `calc1/2`, the Hydra summon words;
       Missiles `Vel`/`VelLev`, `Size`).
  - **P0b (8), the plan 0046 entries of 2026-10-21 and the MonEquip doc:**
    9. `2026-10-21-reverser-archivist-plan-0046-8a-skills-monstats-missiles-column-reade.md`;
    10. `2026-10-21-reverser-archivist-plan-0046-8b-skills-missiles-column-readers.md`;
    11. `2026-10-21-reverser-archivist-plan-0046-8c-skills-monstats-column-readers.md`;
    12. `2026-10-21-reverser-archivist-plan-0046-ass-skills-levels-column-readers.md`;
    13. `2026-10-21-reverser-archivist-plan-0046-bar-skills-monstats2-column-readers.md`;
    14. `2026-10-21-reverser-archivist-plan-0046-dru-skills-missiles-column-readers.md`;
    15. `2026-10-21-reverser-archivist-plan-0046-item-skills-pettype-books-shrines-column.md`;
    16. `2026-10-20-architect-archivist-monequip-table-doc-for-plan-0048.md`: `docs/tables/MonEquip.md` (new), every
        column with offset, width and value range, the `oninit` rows and the classes and levels they name (the
        reverser's layout note of 2026-10-20 in the entry; classes 234 and 267).
- **Read first.** Several entries were released "with fixes" at their plan 0046 batch reviews, and some carry a
  correction made at the review (for example the `item` entry's shrine count, the `ass` entry's `Teleport` and
  `PrgCalcByCharge` re-reads). For each entry, read its batch review in the
  [plan 0046 log](0046-skills-function-catalogue.md#implementation-log) and apply the entry as the review left it.
- **Three data questions in the entries** may need code, not layouts: the `bar` entry's Skills `+0x005` bit 0 (which
  column sets it), the `dru` entry's DataTables `+0x17C`/`+0x180` state list (which loader and which States column),
  and the `8c` entry's monster-data bytes `+0x0E`/`+0x0F` (whether a column fills them). The archivist answers what
  the layouts and `tools/excel_bin.py` show; what needs a reading goes to Phase 1b as an item, named in the entry's
  annotation, and the entry closes with that pointer.
- **Done when:** each item's entry is closed with its resolution (`python3 -I tools/backlog.py close`); each linked
  row cites the finding section and keeps the finding's tag (a meaning the finding tags `[I]` stays `[I]`); the
  `excel_layout` baseline is regenerated if a layout changed; the gate is green.
- **Merge order:** before plan 0050 Phase 0 (it edits Skills, Missiles, MonStats, MonStats2, CharStats and States as
  well), one at a time.

### Phase 1a — Prune and stage, no Ghidra
- **Owner skill:** reverser (**no slot, no Ghidra**: may start on approval, in a static lane's idle time)
- **What:** check four harness-bound entries against what has landed, annotate them, and prepare the logger lines and
  recipes their sessions need, so the batch that carries them spends no slot time on preparation.
- **Items (4):**
  1. `2026-10-16-architect-reverser-plan-0038-s2c-review-harness-pieces.md`: prune the H2b piece (sock 44, met in part
     at the H2b run, [plan 0038 log](0038-inferred-claims-sweep.md#implementation-log), H2b filed and reviewed) and
     annotate the four that remain with their batches (H6a, H6b, H6c, H6e1); the entry stays open for those;
  2. `2026-10-16-architect-reverser-plan-0038-phase-2-leftover-pieces.md`: write and test off-slot the two lines it asks
     for (a hover marker in `tools/gdb/calc.gdb` at the client caller `0x00486370`; a caller `ra` on `SUNITPRE` in
     `tools/gdb/seed-tree.gdb`), then assign the sessions to a named host batch: **H1a** (it loads characters; the
     re-seed comes with the load) unless the lane shows another batch loads either logger first; annotate;
  3. `2026-10-20-architect-reverser-plan-0044-p2-review-agent-stageable-shortfalls.md` (2)–(4): write the recipes and
     the checker lines that need no game (MP18's rune and socketed item, MP25's `0x8000` aura, MP30's e9/e10 line in
     `tools/quests.py`, the hostile open-wounds pair of (4)), and the MP31 and MP32 predictions where the findings
     already give them (a prediction that needs a new reading goes to Phase 1b); the sessions wait for a two-client
     run with both slots (§ Routing); annotate;
  4. `2026-10-16-architect-reverser-plan-0038-h4b-review-follow-ups.md`: check its H4a pieces (a)–(f) against
     `lane/h4a`'s resume note when that lane lands, and its H5d piece against H5d's design; annotate which the batches
     took. If `lane/h4a` has not landed when this phase runs, annotate the entry "with H4a" and leave it.
- **Done when:** each entry is annotated with a dated note naming what was done and what remains with which batch;
  the new logger lines and recipes are committed and pass their off-slot tests (a parse or a dry run under the
  checker); no slot was used; the gate is green.

### Phase 1b — Static optionals, one Ghidra
- **Owner skill:** reverser (**no slot; one headless Ghidra**, `-Xmx3G`)
- **What:** the two optional emulations left open by plan 0049, and the code questions Phase 0 forwards.
- **Items (2, plus any Phase 0 forwards):**
  1. `2026-10-17-reverser-reverser-plan-0041-op-6-7-emulation.md`: `STAT_ByTimeValue` (`0x0065CA30`) and
     `sub_00626200_StatEvaluate` cases 6 and 7 under `tools/ghidra.sh emutrace` over a declared image (ADR-0015), the
     only route past `[I]` for the contradicted op 6/7 lead;
  2. `2026-10-17-architect-reverser-plan-0038-s1e-review-follow-ups.md` (b): re-run run:2026-10-16-calc-emu's cases
     under `emutrace` so its read set is enumerated by the tool (an addendum; no tag depends on it);
  3. the data questions Phase 0 could not answer from the layouts, each as its own item.
     Named at the P0b review (2026-10-27): **(3a)** who fills `DataTables+0x17C` (`u16` state ids) and `+0x180` (`s16`
     count), the list skill do 121's `0x005C8980` walks ([skills/0013 § 6](../findings/skills/0013-druid.md#6-the-melee-functions-start-56-57-58-do-121-122)):
     the loader and the States column or flag it selects on; the data candidates are `restrict` (139, 140, 177),
     `group` 3 and `transform` ([States § Open questions](../tables/States.md#open-questions)); from the closed
     [`dru` entry](../backlog/archive/2026-10-21-reverser-archivist-plan-0046-dru-skills-missiles-column-readers.md).
     The other two P0 data questions were answered from the layouts (`bar`'s `InTown`, 8c's `S3v`/`S4v`). The
     Phase 1a forwards MP31 and MP32 ride with this item (that review's ruling 4).
- **Done when:** each entry is closed with a resolution or annotated with the reason it stays open; any `[C]` from an
  emulation names its run id and meets ADR-0015's conditions (ADR-0021 if a case ends at a callee); the architect's
  review passes. Both items are optional: this phase may be skipped whole if a gated plan needs the Ghidra lane first.

### Phase 2 — Owner decisions on the human entries
- **Owner skill:** human
- **What:** decide each of the four entries addressed to the owner (§ Routing, last block). No lane work.
- **Done when:** each entry is closed or annotated with the owner's decision.

## Routing (the triage, 2026-10-25)

Every open entry, once. "Waits" names the batch or phase whose acceptance releases it; plan 0038 Phase 3 runs per
cluster once all of that cluster's batches are accepted.

**This plan (22):** Phase 0 the sixteen archivist entries; Phase 1a four reverser entries; Phase 1b two reverser
entries (the four Phase 1a entries stay open for their batches after their annotation).

**Stays with a harness batch or a plan phase (3):**

| Entry | Lane | Goes to |
|---|---|---|
| `2026-10-17-reverser-reverser-plan-0038-h6d-a-piece-for.md` | reverser | plan 0038 H1a (us 21, its reach condition) |
| `2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md` | reverser | plan 0045 Phase 2 (`lane/p45h`), cases C1–C5 |
| `2026-10-16-architect-reverser+spec-writer-plan-0038-s2a-tc-64-and.md` | spec-writer (reverser half done) | plan 0038 P3 objects cluster (objects § J3), waits H6e2 |

**Plan 0038 Phase 3 inputs (17 spec-writer entries)**, recorded here and not annotated (each round of plan 0038
Phase 3 already reads the entries of its cluster):

| Entry (`2026-10-…-reverser-spec-writer-` unless named) | Open parts and clusters | Waits |
|---|---|---|
| `16-…-corrections-from-run-2026-10-16.md` | monsters/special, monsters/spawn | H4a; spawn also H5d |
| `16-…-for-plan-0038-phase-3-after.md` | (b) drlg/collision F | H5d |
| `16-…-plan-0038-s1a-corrections-and-additions.md` | save/d2s | H1a, H1b |
| `16-…-plan-0038-s1b-for-phase-3.md` | (a), (c), (d) data/excel, data/strings | H3b |
| `16-…-plan-0038-s2c-corrections-for-phase.md` | (a)–(g) items/cube, quest-drops, vendors, sockets-runewords | H6a; H4a, H6e1, H6e2; H6c; H6b |
| `16-…-plan-0038-s3b-corrections-and-additions.md` | (a)–(e) monsters/stats, pool, spawn; player/creation (d) | H4a; H5d; H1a, H6g |
| `16-…-plan-0038-s4b-corrections-for-phase.md` | (a) objects, (d) drlg/collision | H6e2; H5d |
| `16-…-two-statements-that-batch-s3a-found.md` | monsters/stats § G, monsters/special § C, monsters/pool | H4a |
| `2026-10-17-architect-spec-writer-plan-0038-s1e-review-additions-to.md` | (a), (c) data/excel, data/strings; (d) save/d2s | H3b; H1a, H1b |
| `17-…-gate-w1-a-c-i-statement.md` | the 11 W1 in data/excel | H3b (the plan 0039 fold) |
| `17-…-plan-0038-h6d-for-the-phase.md` | (a)–(g) items/quest-drops; (i) items/uniques-sets | H4a, H6e1, H6e2; H1a |
| `17-…-plan-0038-s1e-corrections-and-additions.md` | (a) data/excel, data/strings, save/d2s; (b); (f) | H3b; H1a, H1b |
| `17-…-plan-0038-s1f-for-phase-3.md` | (a)–(e), (g) monsters/stats, pool, uniques-sets, data/excel | H4a; H1a; H3b |
| `17-…-plan-0039-phase-2-the-p1b.md` | (a) data/excel | H3b (the plan 0039 fold) |
| `17-…-plan-0039-phase-2-the-p1c.md` | (a) data/excel | H3b (the plan 0039 fold) |
| `20-…-h2b-items-chain-spec-updates.md` | (c)–(g) items/uniques-sets; (r)–(s) items/sockets-runewords | H1a; H6b |
| `20-…-h5b-objects-spec-updates.md` | objects, drlg/collision | H6e2; H5d |

**Owner entries (4, Phase 2; one closed at approval, 3 open):**

| Entry | Recommendation |
|---|---|
| `2026-10-11-archivist-architect+human-is-1-14d-s-patchd2-mpq.md` | keep parked (owner, 2026-10-20) |
| `2026-10-17-architect-human-plan-0038-h6d-diablo-owner-pair.md` | optional; keep open until plan 0038 Phase 3's items/quest-drops round, then close as not played if it was not |
| `2026-10-17-architect-human-plan-0042-owner-play-boss-steps.md` (now in `archive/`) | **closed as dropped** (owner, 2026-10-25): plan 0042 closed on 2026-10-20 and the entry's own 2026-10-19 note says the steps not played before part 3's review stay `[I]` for good |
| `2026-10-20-architect-human-plan-0044-owner-play-cases-mp12-mp14-mp17.md` | optional; keep open |

**Count:** 16 + 4 + 2 (this plan) + 3 + 17 + 4 = **46** at the triage; after the owner closed the plan 0042 entry
(2026-10-25), **45 open**: 16 + 4 + 2 + 3 + 17 + 3. The other three owner entries stay open as recommended (owner,
2026-10-25).

## Resources and limits

- **Harness:** none. (At most **two harness lanes** across all plans, on **slots 1 and 2**; slot 0 is the owner's.
  This plan takes neither.)
- **Static:** at most **two static lanes** at once across all plans, and at most **two headless Ghidra** at once,
  `-Xmx3G` each. Phases 0 and 1a hold a lane but no Ghidra; Phase 1b holds one Ghidra. Phase 0 (archivist) and Phase
  1a (reverser) may run at once in the two static lanes.
- **Replays:** an off-slot dry run of a logger or checker over kept logs that is heavy runs under
  `systemd-run --user --scope -p MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
  Phase 0 is sized as two runs (P0a, P0b); either may be split at an item boundary.

## Open questions

- **The two-client run.** The sessions of the plan 0044 shortfalls entry (MP16, MP18, MP20, MP21, MP25, MP27, MP28,
  MP30–MP32, the hostile open-wounds pair) need both slots. No plan takes them; the owner kept them as an optional,
  deferred tail of the run order (2026-10-25). Phase 1a still stages them.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-25 — Drafted (architect, `lane/plans50`).** Status `proposed`; triage of the 46 open entries in § Routing.
- **2026-10-25 — Approved (owner, via the orchestrator).** Approved as drafted; may start at once. Phase 2: the plan
  0042 owner-play entry closed as dropped
  ([archive](../backlog/archive/2026-10-17-architect-human-plan-0042-owner-play-boss-steps.md)); the patch, Diablo-pair
  and plan 0044 owner-play entries stay open as recommended; the two-client tail optional and deferred.
- **2026-10-25 — Phase 0a landed for review (archivist, `lane/p51a`, no slot, no Ghidra).** The eight plan 0046
  column-reader entries of 2026-10-20 (9a, 9b, 9c, 9d, `ama`, `nec`, `pal`, `sor`) are folded and closed. Each column
  the entries name now ends its row's Meaning cell with `*plan 0046 readers:*`, a tagged reader, the finding section
  (skills/0004–0011) and an `fn:` or address anchor. Tables touched:
  [Skills](../tables/Skills.md), [Missiles](../tables/Missiles.md), [MonStats2](../tables/MonStats2.md)
  (`MeleeRng`, `corpseSel`, `revive`, `small`, `large`), [MonStats](../tables/MonStats.md) (`Velocity` and `Run` as
  two rows of § Readers at creation and at attack time), [CharStats](../tables/CharStats.md) (`RunVelocity`),
  [DifficultyLevels](../tables/DifficultyLevels.md) (`AiCurseDivisor`: `DiffDivide` read, the three other readers
  still not read) and [States](../tables/States.md) (`udead`, a dated note on its bullet). In Skills the reader goes on
  the § Dispatch row where one carries the column's code meanings (missiles, `progressive`, parameters, costs,
  summons), else on the § Columns row (the § Passive and aura table has no Meaning cell). One row per column; a run
  of columns read together sits on its first column's row, and the others say "as `X`". Where an entry differs from
  the finding, the finding was followed: 9b's `ELenCalc` is `ELenSymPerCalc`; `srvmissilec` is taken at a charge of 3
  or more; the `Kick` minimum for a non-player is `max(3·level, 1) / 4 << 8`.
  - **The tags are the findings', as their reviews left them, where an entry says otherwise.** Do 7's `Param1` period
    and `Size` edge distance are `[I]` (re-plan, skills/0004 § 10). Do 8/10/17's creation of `SubMissile1` comes after
    the `COLL_CellTestAt` boundary, so it is `[I]`. Do 28 and do 34 are `[C]` (ADR-0021), as the 9b review raised them;
    the entry had `[I]`. The radii of hits 14, 22, 24 and 44 are `[I]` (9c ruling 1), and so are hit 9's disc radius,
    hit 4's switch and hit 22's bolt count. The ring steps of hits 52 and 59 and the `CollideKill` return values are
    `[I]`, as is row 568's word being `pSrvHitFunc` (9d ruling 4). The `ama` and `pal` values are `[C]` and their
    meanings `[I]` (fixes 4 and 3 of those reviews). `srvmissileb` is `[C]` for weapon word 0 only.
  - Also changed: `HitSubMissile2..4`'s layout note "slot by stride `[L]`" is replaced by hit 4's reader (`[C]`,
    ADR-0021). `Kick`'s maximum divides by 3 (`sub_00644C20_SkillKickDamage`), not by 4. MonStats `Run` is laid out
    u16 and read signed by Charge; stock 0..20 cannot tell them apart. The layout and the `excel_layout` baseline are
    unchanged.
  - **Left open:** `SubMissile3`'s "slot by stride `[L]`" stays. Do 34 reads three pairs, but the finding does not
    give the third slot's offset. The three data questions of § Phase 0 belong to P0b's entries; none of P0a needs a
    decompile reading, so nothing is forwarded to Phase 1b.
  - Gate fast tier GREEN (the 11 W1 warnings are `main`'s, in `docs/specs/data/excel.md`). Next: P0b (items 9–16).
- **2026-10-25 — Phase 0a review paused (architect, on `lane/p51a` at `61c0f41`; owner's usage-limit stop).** `main`
  (`9e221ed`) is the lane's base, so no merge was needed. Checked against skills/0004–0011 and the 9b and `pal` review
  entries: the readers on Missiles (`pSrvHitFunc`, `HitSubMissile2..4`, `SubMissile1..3`, `Param1..5`, `sHitPar1..3`,
  `dParam1/2`, `EType`, `CollideKill`, `Size`, `Vel`/`VelLev`), Skills (aura, passive and summon words, `calc1..4`,
  `Param1..7`, `ToHit`, `ELen`, the mana columns, `perdelay`, `progressive`, `srvmissilea..c`, `startmana`), MonStats2,
  MonStats, CharStats, DifficultyLevels and States. Their tags follow the findings, and the anchors resolve to the
  findings' sections. `Kick`'s maximum `/ 3` (`[I]`) and minimum (`[C]`) match skills/0007 § 3, and `TargetPet` matches
  skills/0006 § 6. The narrowed `AiCurseDivisor` open question is right. The diff has no `[L]` outside Open questions
  except the layout cells' existing "slot by stride". `tools/` and `re/` are unchanged. No fix has been found so far.
  **Left:** the gate's result, the verdict, closing the review request (`backlog.py close`, then stage the archive/
  path), the ledger rows in `docs/plans/metrics.md` (lane: archivist, static, 183 561 tokens, 59 tools, 14 min;
  review: "—"), and the review-fixes Seen lines.
- **2026-10-27 — Phase 0a reviewed (architect, on `lane/p51a`, resumed at `171ee5a`): accept, 0 fixes.** Merged
  `main` (`cf25f22`, lane/h4a) first: no conflict; `backlog.py archive` moved nothing. Resumed checks: the readers
  re-read against the finding sections they cite (row 568's `pSrvHitFunc` 64 948 `[I]` never called, as skills/0002
  § 5 and 9d ruling 4 have it); the lane's other edits outside the tables are `backlog.py` link rewrites to
  `archive/` in plan 0046 and three archived review entries, no claim changed; full gate GREEN after the merge.
  **Rulings:** (1) the folded readers stand with the findings' tags; where an entry and its finding differed, the
  finding's reading is the right one. (2) `SubMissile3`'s "slot by stride `[L]`" stays as a layout lead until a
  finding gives do 34's third slot. (3) No review-fixes Seen line: no fix was made, so no rule recurred. Review request
  closed ([archive](../backlog/archive/2026-10-25-archivist-architect-review-plan-0051-phase-0a-column-readers.md)).
  Ledger rows filed. Next: P0b (items 9–16).
- **2026-10-25 — Phase 1a done (reverser, `lane/p51r`, from `main` `9e221ed`; no slot, no Ghidra, no game run).**
  Four entries annotated, all four still open as the plan says (each annotation names what remains and with which
  batch). Off-slot outputs: `workspace/logs/p51r/` (manifest `manifest.sha256`, `22169f4a…`; `commands.txt` lists the
  command behind each file; tool revisions in `tools-revisions.txt`).
  1. **S2c harness pieces**
     ([entry](../backlog/2026-10-16-architect-reverser-plan-0038-s2c-review-harness-pieces.md)): the H2b piece (sock
     44) is pruned. It was met in part at H2b's run and review, and its remainder (a request of 4 or more) is out of
     this plan. H6a, H6b, H6c and H6e1 are left, each still in its inventory § 5 row.
  2. **S1b leftover pieces**
     ([entry](../backlog/2026-10-16-architect-reverser-plan-0038-phase-2-leftover-pieces.md)): `tools/gdb/calc.py`
     writes the hover marker `CH` at `0x00486370`, and `tools/calc.py hover` counts it. The `SUNITPRE` line of
     `seed-tree-core.gdb` carries the caller's `ra=`, which `tools/rng.py seedtree` names among the six direct calls of
     `0x00552DF0`. The call sites behind both come from a kept objdump scan (`call-sites.txt`). The session is staged as
     `tools/gdb/s1b-pieces.gdb` + `.steps` (CalcSor: hover, drink, Save and Exit, load again) and assigned to plan 0038
     **H1a**, one extra session: no open batch loads either logger first. Tests: `tools/test_p51_staging.py`.
  3. **Plan 0044 shortfalls (2)–(4)**
     ([entry](../backlog/2026-10-20-architect-reverser-plan-0044-p2-review-agent-stageable-shortfalls.md)): staged
     MP18 (recipe `mp-sock-join`, logger `two-sockets.gdb`), MP25's offensive auras (recipe `mp-pal-conv`, `two-combat.gdb`
     and `mp_check.py aura` as they stand), MP30 (the QL0..QL1 lines in `tools/gdb/quests.py`, checker `mp_check.py
     leave`) and the open-wounds pair (recipe `mp-wound-join`, *Ripsaw*, logger `two-wounds.gdb`). `mp_saves.py check`:
     30 recipes, 21 pairs, 0 bad. The predictions are the ones the findings already give (multiplayer/0001 § 2 and § 4,
     stats/0002 § 2 and § 6). The sessions wait for the two-client run with both slots (§ Routing, Open questions).
     **Forwarded to Phase 1b**, as new readings: MP31's prediction (the player-to-player trade, not read) and MP32's
     (the arithmetic of `sub_00540900_PartyGoldShare`; items/0011 gives only "a split by `PartyCount`").
  4. **H4b follow-ups**
     ([entry](../backlog/2026-10-16-architect-reverser-plan-0038-h4b-review-follow-ups.md)): **with H4a**. `lane/h4a`
     has not landed (paused 2026-10-21, nothing claimed). The H5d piece is still in H5d's § 5 row.
  - **Not touched:** no slot, no Ghidra, no game launch. No tool that `lane/h4a` or `lane/p45h` edits on its branch
    (`d2pilot.py`, `sweep_h4a.py`, the `mon-h4a*` and `skills*` files) was changed. The inventory of plan 0038 is not
    edited (the H1a session is for the architect to add to § 5).
  - **Backlog:** review request
    [p51r review](../backlog/archive/2026-10-25-reverser-architect-p51r-plan-0051-phase-1a-review.md).
- **2026-10-27 — Phase 1a review (architect, `lane/p51r`): accept with fixes.** Reviewed after merging `main` `cf25f22`
  (the `lane/h4a` merge) into the lane. Re-run on the review side: `test_p51_staging.py` 9 OK; `mp_saves.py check` 30
  recipes, 21 pairs, 0 bad; `manifest.sha256` and `tools-revisions.txt` pass (the merge touched none of the lane's
  tools). objdump reads of the pinned image: `0x00486370` (called once, from `0x0048E978`) holds the three
  `ITEMS_EvalCalc` calls `0x0048642F`, `0x004864D0`, `0x00486506` before its last `ret 4` at `0x00486562`; the six
  direct calls of `0x00552DF0` (none by `jmp`); its prologue `push ebp; mov ebp, esp`, so `[EBP+4]` at `0x00552E2F` is
  the return address; the e10 dispatch at `0x00543CA2` (event word 10 stored just before) and the reset call at
  `0x00592CDC`.
  - **Fixes (3):** the H4b follow-ups entry annotated with what H4a took ((a) and (c)) and what is out of this plan
    ((b), (d), (e) with the owner as the entry says, (f) dropped), now open for H5d only (stale cross-reference:
    `lane/h4a` landed after the lane ran, item 4's own condition); monsters/0003's H4b section, special 66's mod 12
    remainder marked met since H4a (stale cross-reference, left by the `lane/h4a` review, which marked only the
    class-312 piece); the S1b session written into H1a's row of inventory § 5 (sessions ~19) and § 8's cap note
    (omission; the lane's point 1, left to the architect).
  - **Rulings.** (1) The H1a assignment stands: no open batch loads `calc.gdb` or `seed-tree.gdb`, the session is
    its own (its own logger, CalcSor), and H1a stays under the cap of 20 at about 19; if H1a counts more than 20
    before it starts, the S1b session is the first piece to leave it (§ 8's split rule). (2) The hover marker's call
    sites rest on the kept objdump scan (`call-sites.txt`) and the review's re-read; no tag depends on them before H1a's
    session. The fold keeps the last run of identical entries unflushed at the end of a log; `calc.py hover` counts
    lines and evaluations, not `n`, so nothing is lost. (3) `two-wounds.gdb` loading `combat.py` and `stats.py`
    together is staged, parse-tested only, as the lane says; the session's first minutes are its test. (4) MP31 and
    MP32 are Phase 1b forwards, alongside its item 3 (each a new reading: the trade path, `PartyGoldShare`'s
    arithmetic); they ride on the plan 0044 shortfalls entry's annotation, which stays open.
  - **Ledger:** no statement moved (staging only); the Routing count stands at 45 open (no entry closed).
  - **Backlog:** review request closed (archive).
  - **Next:** Phase 1b (optional, one Ghidra), with the MP31 and MP32 forwards.
- **2026-10-27 — Phase 0b landed for review (archivist, `lane/p51b`, no slot, no Ghidra).** The seven plan 0046
  column-reader entries of 2026-10-21 (8a, 8b, 8c, `ass`, `bar`, `dru`, `item`) are folded and closed, and the MonEquip
  entry is done. Each reader ends its row's Meaning cell with `*plan 0046 readers:*` (P0a's convention: the § Dispatch row
  in Skills where one exists, else § Columns), a tagged reader, the finding section (skills/0012–0018) and an `fn:` or
  address anchor. Tables touched: [Skills](../tables/Skills.md) (38 rows), [Missiles](../tables/Missiles.md) (`Vel`,
  `VelLev`, `Param1`, `Param2`, `Size`), [MonStats2](../tables/MonStats2.md) (`InfernoLen`, `InfernoAnim`, `corpseSel`,
  `soft`, `large`, `small`, `SizeX`, `S3v`, `S4v`), [MonStats](../tables/MonStats.md) (§ Spawn columns `spawn`,
  `spawnx`/`spawny`, `spawnmode`, whose name readings `[L]` are replaced by the summon readers; `+0x04B`; a `BaseId` row
  in § Readers), [States](../tables/States.md) (`srvactivefunc`, an Open question), [Levels](../tables/Levels.md)
  (`Teleport`), [PetType](../tables/PetType.md), [Books](../tables/Books.md), [Shrines](../tables/Shrines.md) (§ Effects:
  codes 19, 21, 22; the `[L]` bullet narrowed to 16–18) and [Misc](../tables/Misc.md) (`pSpell` 10, 11).
  - **The tags are the findings', as their reviews left them.** Values and tests `[C]` up to each ADR-0021 boundary,
    meanings and what follows a boundary `[I]` (`bar`: the archivist entry's `[C]` items carry values only; `dru` fix 2:
    `InTown` and `aurarangecalc` give the branch and its calls `[C]`, "the state is removed", "the period ends" `[I]`; 8c
    fix 3: `srvactivefunc` 147's call `[C]`, the path move `[I]`; `ass`: "0 forbids, 2 restricts" and stat 8 as mana `[I]`;
    `item` fix 3: 5 to 9 potion **tries**, a try with no free spot making none). Where an entry and its finding differ
    in wording, the finding's text is used: `SKILLS_PayCost`'s 0 refuses nothing (`item` review fix 2, added); start
    60's packet is set on the bit-0 return by the caller (as start 58's); `PrgCalcByCharge` is `[C]` only as part of the
    entries' maps. One count recomputed: the Skills `.txt` has 357 rows, not the 358 skills/0013 § 6 writes; the fact
    (only 239 and 242 use start 58 and do 122, both `ResultFlags` blank) holds.
  - **The three data questions of § Phase 0.** (a) `bar`'s Skills `+0x005` bit 0 is the `InTown` column by the layout
    (`[C]`), as the `dru` entry names it: answered, no Phase 1b item. (b) 8c's monster-data bytes `+0x0E`/`+0x0F` hold no
    table column; by monsters/0004 § 6 MonsterData `+0x04 + k` is MonStats2 component `k`'s drawn variant, so they are
    `S3v` (k = 10) and `S4v` (k = 11), `[I]`, and the data agree (the DoomKnightMissile classes' `S3v` and `necromage`'s
    `S4v` have 4 variants each, and `undeadmissile1..4`, `necromage1..4` run in Missiles): answered on the MonStats2 and
    Skills `srvmissilea` rows, no Phase 1b item. (c) `dru`'s DataTables `+0x17C`/`+0x180` list needs its loader read:
    **forwarded to Phase 1b** (§ Phase 1b item 3), with the data candidates in States § Open questions (`restrict`,
    exactly 139, 140, 177; `group` 3; `transform`).
  - **MonEquip** ([MonEquip](../tables/MonEquip.md), new): a `monequip` layout in `tools/excel_layouts.py` (45 records ×
    12 fields = 540 cells, 0 mismatches; `loc2`/`loc3` and `mod2`/`mod3` placed by order, `[I]`, since the 9 rows that
    set slot 2 set slot 3 alike), the `excel_layout` baseline regenerated (69 tables). The `oninit` rows are the first
    rows of 267 `bloodraven` and 234 `flyingscimitar`, level 0, one location; the other 42 rows are the summons
    `valkyrie` (357), `shadowwarrior` (417), `shadowmaster` (418), walked by the summon code's own `MonEquipInit` calls
    (`[I]`). `mod1..3` stay `[L]`; whether `MonEquipInit`'s last argument skips the `oninit` test is an open question of
    the doc, not needed by oracle 13.
  - Left open: none of P0b's entries. `tools/` changes: the layout and the baseline only; `re/` unchanged. Gate fast tier GREEN (the 11 W1
    warnings are `main`'s, in `docs/specs/data/excel.md`); `--full=excel_layout` GREEN against the new baseline. Review
    request filed ([entry](../backlog/archive/2026-10-27-archivist-architect-review-plan-0051-phase-0b-column-readers.md)); ledger
    row added. Next: Phase 1b (with the `dru` item).
- **2026-10-27 — Phase 0b review (architect, `lane/p51b`): accept with fixes.** Reviewed after merging `main` `3fa5209`
  into the lane (the plan log and the ledger kept both sides; `backlog.py archive` moved nothing). Re-run on the review
  side: `excel_bin.py survey` over `workspace/merged/data/global/excel` gives the committed baseline line exactly (69
  tables, 11 502 records, 946 629 cells, 0 unexplained; against the old line only `tables`, `records`, `cells` and the
  two `monequip` keys differ, +45 records, +540 cells); `excel_bin.py diff … monequip`: 45 × 12 = 540 cells, 0
  mismatches, the one unmatched reference the `*end*` row. The MonEquip `.txt` re-read by script: the five classes
  and their row counts, `level` 0..27 (20 distinct), `mod1` 3 ×5, 4 ×18, 6 ×21, the 8 location-only rows, the 9
  three-slot rows with one location and one mod (so `loc2`/`loc3` and `mod2`/`mod3` by order stays `[I]`). Data
  answers re-checked: Skills `+0x005` bit 0 is `InTown` in the layout; do 148's classes (`doomknight2`, `doomknight3`,
  `dkmag1..3`) carry `S3v` `pos,fir,col,unh` and do 149's `necromage` `S4v` `pos,cld,fir,lht`, `undeadmissile1..4` and
  `necromage1..4` consecutive; `restrict` set on exactly 139, 140, 177 and `group` 3 on 117, 120, 139, 140, 176, 177;
  Misc `pSpell` values 1, 2, 3, 5–9. The recount: `skills.txt` has 357 rows and the `.bin` count is 357; start 58 is
  row 239 only and do 122 row 242 only, both `ResultFlags` blank. Readers read against their finding sections:
  Levels `Teleport` (skills/0014 § 4), Shrines 19, 21, 22 (skills/0015 § 8), Books (skills/0015 § 4), PetType
  `basemax` and the `+0x0BC` list (skills/0015 § 10), Skills `InTown` (skills/0012 § 6, skills/0013 § 5), MonStats
  `spawn` (skills/0013 § 3, 0014 § 6, 0016 §§ 4–5, 0017 § 5, 0018 § 4–5), MonStats2 `S3v`/`S4v` (skills/0018 § 3,
  monsters/0004 § 6), Missiles `Param1` do 99 (skills/0017 § 3), Skills `ResultFlags` (skills/0013 § 6), MonEquip
  (monsters/0004 § 6, chain/0002 § 11, skills/0003 § 7, skills/0014 § 6).
  - **Fixes (7):** Levels `Teleport`: `0x006229F0`'s outcome (non-zero → 0, zero → the teleport) tagged `[I]`, being
    past that boundary in skills/0014 § 4 (overclaim). MonEquip § Interpretation notes: the summons' rows were
    "walked" `[I]` while the doc's own open question leaves the `oninit` gate for a last argument of 0 unread; now the
    summon code calls `MonEquipInit` and whether the walk runs is open, and "their last argument is 0" narrowed to
    do 49's (skills/0003 records no arguments for `SummonInitStats`' call) (overclaim). Skills `InTown`: start 40's
    town test applies to a caster that is not a monster, type 1 taking the monster branch with or without a target
    (skills/0012 § 6; the fold read "other than a monster with a target") (misread). MonStats `spawn`: do 131's class
    change, `EDX` 0 after its boundary (skills/0018 § 4), added `[I]` (omission). Phase 1b item 3 named as **3a**, the
    `+0x17C`/`+0x180` loader with the data candidates and the closed `dru` entry; the P0b entry had sent it to "item
    3", which named no question (omission). skills/0013 § 6: "358 Skills rows" → 357 (miscount, the lane's recount
    written into the finding), and its open question on `+0x17C` no longer "an archivist question" but Phase 1b item
    3a (stale cross-reference).
  - **Rulings.** (1) The folds stand with the findings' tags: values and tests `[C]` to each ADR-0021 boundary, what
    follows `[I]`, as Phase 0a ruled; the seven fixes above are the exceptions found. (2) The 8c bytes `+0x0E`/`+0x0F`
    as `S3v`/`S4v` drawn variants stay `[I]` (monsters/0004 § 6 is `[I]`; the data agree, the dkmag classes carry four
    `S4v` variants as well, which the reading does not use). (3) `bar`'s bit closes on the layout, `[C]`, no Phase 1b
    item. (4) The `dru` list is Phase 1b item 3a; the States § Open questions bullet stays `[L]` until it is read.
    (5) Whether `MonEquipInit`'s last argument skips the `oninit` test is a reverser question, not Phase 1b's: no
    oracle needs it, and chain/0002 § 11's "unreachable with the stock table" holds only if the summons' calls are
    gated; it stays in MonEquip § Open questions.
  - **Ledger:** lane row filled (usage from the orchestrator), review row added.
  - **Backlog:** review request closed (archive).
  - **Next:** Phase 1b (optional, one Ghidra): items 1, 2 and 3a, with the MP31 and MP32 forwards.
- **2026-10-27 — Phase 1b done (reverser, `lane/p51s`, from `main` `7ff8d98`; no slot, one headless Ghidra on the lane
  copy `ghidra-p51s`, `-Xmx3G`, no game).** Two entries closed, one annotated. The items are item 1, item 2 and the
  two Phase 1a forwards; P0b (`lane/p51b`, running at the same time) had forwarded nothing to `main`, so item 3 holds
  only MP31 and MP32. Emulation outputs: `workspace/logs/p51s/emu/` (`manifest.txt` `b16c2780…`, 79 files;
  `check.txt` `7ee746af…`; `commands.txt`, `tools-revisions.txt`). Static outputs: `workspace/logs/p51s/static/`
  (`manifest.txt` `1464d267…`: the findstring, objdump excerpts and call-site scan behind multiplayer/0002). Tool: `tools/sweep_p51s.py`.
  1. **Op 6/7 emulation** ([archive](../backlog/archive/2026-10-17-reverser-reverser-plan-0041-op-6-7-emulation.md)),
     closed. `STAT_ByTimeValue` ran 6 000 calls, and `StatEvaluate` cases 6/7 with `ActTimeOfDay`, `MulDiv`, ops 10,
     12 and above 13 and nested sources ran 3 000. Result: 0 mismatches, 0 undeclared reads (the jump table and the
     `.rdata` mask are declared, both read-only), 0 stops, every branch reached. Negative controls: the lead's "op 6/7
     add nothing" fails 2 110, op 7 on the own sum 1 103, no 359 fold 3 302, floor division 2 416. **[C] as a code
     map** (ADR-0015), run:2026-10-27-p51s-emu, in stats/0001 § 10 (new). The Answer bullet, § 4's note, the
     contradicted lead's detail and the Open question are updated. Still `[I]`: what `owner +0x1C` and its `+0x04`
     record hold in play. No symbol row is raised (review-fixes 14: an emulation confirms the map, not the name).
  2. **S1e follow-ups (b)** ([archive](../backlog/archive/2026-10-17-architect-reverser-plan-0038-s1e-review-follow-ups.md)),
     closed with (a) and (c) done earlier. The eleven runs of run:2026-10-16-calc-emu were re-run unchanged under
     `emutrace`. Every output is byte-identical to the kept one. The kept `calc_funcs.py` checkers pass on it, and
     fail with every EAX + 1. The tool's read set adds two read-only `.text` switch tables (`MISS_CalcVar` 0x0064B62C,
     `CALC_Eval` 0x006C1164) to data/0005 § 11's list. That is an addendum there and in data/experiments; no claim
     changes.
  3. **MP31, MP32** (plan 0044 shortfalls entry, annotated, stays open for the two-client run): the trade path and
     `PartyGoldShare`'s arithmetic are read in the new **multiplayer/0002** (`[I]` throughout). Gold share:
     `share = amount / n`, with `n` the members in the level who are not dead. Others get `min(share, room)`, and the
     picker the rest plus their overflow, clipped. The payment loop tests the **picker's** mode, so a dead member in
     the level is paid but not counted (three or more players; out of the two-client run). Trade: the `0x4F` buttons
     3/4/7/8 over `PlayerData+0x50`; the offer is clipped to the partner's room; the commit re-checks gold, cap,
     room and the quest gate, then moves `ItemCopy` units and carried gold. Predictions in multiplayer/0002 § 3;
     multiplayer/0001 rows MP31 and MP32 and items/0011 § 6 (the pickup line, the Open question) updated.
  - **Symbols:** 15 added (`I`): `UnitGetMode`, `PartyGoldClip`, and 13 trade functions (`TradeRequest` …
    `TradeBlocked`). No rename, no tag change; names checked against `main`'s `re/symbols.csv`.
  - **Backlog:** review request
    [p51s review](../backlog/2026-10-27-reverser-architect-p51s-plan-0051-phase-1b-review.md).
