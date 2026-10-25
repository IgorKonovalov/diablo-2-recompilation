# 0051 — Backlog sweep 6: the catalogue's column readers, the static optionals and the routing of the rest

> **Status:** proposed (owner approval pending)
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

**Owner entries (4, Phase 2):**

| Entry | Recommendation |
|---|---|
| `2026-10-11-archivist-architect+human-is-1-14d-s-patchd2-mpq.md` | keep parked (owner, 2026-10-20) |
| `2026-10-17-architect-human-plan-0038-h6d-diablo-owner-pair.md` | optional; keep open until plan 0038 Phase 3's items/quest-drops round, then close as not played if it was not |
| `2026-10-17-architect-human-plan-0042-owner-play-boss-steps.md` | **close as dropped**: plan 0042 closed on 2026-10-20 and the entry's own 2026-10-19 note says the steps not played before part 3's review stay `[I]` for good |
| `2026-10-20-architect-human-plan-0044-owner-play-cases-mp12-mp14-mp17.md` | optional; keep open |

**Count:** 16 + 4 + 2 (this plan) + 3 + 17 + 4 = **46**.

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
  MP30–MP32, the hostile open-wounds pair) need both slots. No plan takes them yet; the run-order section proposes
  them as an optional tail after plan 0045 P2 frees both slots.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-25 — Drafted (architect, `lane/plans50`).** Status `proposed`; triage of the 46 open entries in § Routing.
