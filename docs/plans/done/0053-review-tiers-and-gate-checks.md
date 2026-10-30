# 0053 — Review tiers and gate checks for the mechanical fix categories

> **Status:** done (closed 2026-10-30; approved 2026-10-27 by the owner; ADR-0023 accepted, ADR-0024 proposed)
> **Created:** 2026-10-27
> **Owner skill(s):** archivist (phases 0–1), architect (phases 2 and 4), human (phase 3)
> **Related ADRs:** [0023-review-tiers-and-gate-first-fixes](../../adrs/0023-review-tiers-and-gate-first-fixes.md) (accepted), [0024-lane-check-touched-documents-and-routing](../../adrs/0024-lane-check-touched-documents-and-routing.md) (proposed), [0006-docs-gate](../../adrs/0006-docs-gate.md)

## TL;DR

This plan answers how to cut the cost of reviews (30.9% of agent tokens, 172 runs at a 150k mean) without weakening
what reaches `docs/specs/`. When it is done:

- `tools/gate.py` has four new checks for the mechanical fix categories: miscount, stale cross-reference and
  bookkeeping splice.
- The architect skill has a Tier B lane check beside the full review.
- The ledger has ten Tier B checks and two audits, measured against the full reviews they replaced.
- ADR-0023 is accepted or withdrawn on those numbers.

## Context

The evidence is in ADR-0023 § Context. Of 708 categorised fixes, 134 are mechanical (miscount 53, stale
cross-reference 50, wrong anchor 27, bookkeeping splice 4). The new checks below target the copies that drift:

- **E15 (miscount, stale cross-reference):** the research map repeats each spec's status, tag counts and `updated:`
  date.
- **E16 (stale cross-reference):** the plans index repeats each plan's `Status:`, and each index states a next free
  number.
- **W7 (miscount):** batch and recount tables carry totals.
- **E14 (bookkeeping splice):** merges splice table rows.

Most wrong-anchor fixes are semantic: a real symbol that is not what the sentence claims. E1 already checks the rest,
so this plan adds nothing for that category.

Phases 0 and 1 do not depend on ADR-0023 being accepted, because the checks pay for themselves under either review
model. Phases 2–4 start only once the owner accepts the ADR as proposed (status `accepted (trial)`).

## Phases

### Phase 0 — Measure the candidate checks on the current tree
- **Owner skill:** archivist
- **What:** prototype E14–E16 and W7 as a dry run (a `--candidate` flag or a scratch module under `tools/gate/`),
  list every hit on `main`, and classify each hit as a true or a false positive.
- **Outputs:** a dated entry in this plan's Implementation log with per-check hit counts, the false positives and
  their causes, and the value sets found (spec `status:` values against the map's status words).
- **Done when:** each check has a hit count and a false-positive count. Each false positive has either a rule change
  proposed below or a reason the check should be dropped.

### Phase 1 — Implement the checks
- **Owner skill:** archivist
- **What:** add the rules below to `tools/gate.py`, with fixtures under `tools/gate/fixtures/` and tests beside the
  existing ones.
- **Rules** (the architect copies them into `references/evidence-rules.md` § Mechanical checks in the Phase 1
  review commit; until then they are this text):

  | # | Rule | Applies to |
  |---|---|---|
  | E14 | Outside code blocks, every row of a markdown table has as many cells as its header row. Escaped `\|` and pipes inside code spans don't split cells. | every tracked `.md` except `tools/gate/fixtures/` |
  | E15 | For each spec linked from a research-map row's Status cell: the status words before ` · ` (bold stripped) equal the spec's `status:` under the mapping Phase 0 found. A `C n / I n / L n` group after the link and before the next link equals the spec's `tags:`. An `updated YYYY-MM-DD` after the link equals `updated:`. | `docs/specs/README.md` |
  | E16 | In `docs/plans/README.md`, each row's Status cell starts with the linked plan's `Status:` value (first word). The link points under `done/` if and only if that value is `done` or `abandoned`. In `docs/plans/README.md` and `docs/adrs/README.md`, the "Next free number" is greater than every number in use in that directory, `done/` included. | those two indexes |

  | # | Heuristic (warning) | Applies to |
  |---|---|---|
  | W7 | A table row whose first cell is `Total` (bold allowed): each numeric cell (spaces, narrow spaces and commas as separators) equals the sum of the numeric cells above it in that column, back to the header or the previous `Total` row. | specs, findings, plans |

- **Outputs:** `tools/gate.py` with E14–E16 and W7, fixtures, tests, and the module docstring updated. `main` is green
  under the new errors: the lane fixes the hits in files it owns, and files the rest as backlog entries to the owning
  lane (architect: the research map and the indexes). Until those land, their checks stay at warning level, with the
  reason in the commit message.
- **Done when:** `python3 -I tools/gate.py` passes on the lane tip. Each new rule has a fixture that fails and one that
  passes. The hit counts on the tip match Phase 0's counts minus the fixes, and the log shows the arithmetic.

### Phase 2 — Tier B in the skills and the ledger
- **Owner skill:** architect
- **What:** once ADR-0023 is `accepted (trial)`, fix the Phase 1 backlog entries addressed to the architect, raise any
  warning-level E14–E16 back to error, and write the lane check.
- **Outputs:**
  - `references/lane-check.md`: the Tier B steps from ADR-0023, the diff command, the escalation list, a scope limit
    (no reads outside the diff except the anchors spot-checked and `review-fixes.md`), and the verdict format.
  - `SKILL.md` Mode 3: which tier applies to which lane kind, the promotion re-check of imported `[C]`, and the audit
    rule.
  - `docs/plans/metrics.md`: a new Kind `architect-check`; an audit row is an `architect-review` whose Fixes cell
    begins `audit of <lane>:`.
  - The orchestrator's lane-model memory note, pointed at the tiers.
- **Done when:** a Tier B check can be started from the skill alone, with no other instructions, and the gate is green
  with E14–E16 at error.

### Phase 3 — Trial: ten Tier B checks and two audits
- **Owner skill:** human (the orchestrator, with the owner's go)
- **What:** route the next ten non-spec lanes through Tier B on Sonnet, batching where the diffs are disjoint, and give
  the fifth and tenth a Tier A audit as well.
- **Outputs:** ledger rows for every check and audit.
- **Done when:** ten `architect-check` rows and two audit rows exist, each with tokens, verdict and fixes by category.

### Phase 4 — Evaluate and settle ADR-0023
- **Owner skill:** architect
- **What:** compare the trial with the full reviews of the same lane kinds.
- **Outputs:** an evaluation entry in this log, ADR-0023's status set to `accepted` or `superseded`/withdrawn with the
  reason, and the plan closed.
- **Done when:** the entry gives:
  - mean tokens per Tier B check, against the 150k full-review mean for the same kinds (`metrics.py summary --by kind`);
  - the reject-grade problems the audits found that the checks missed;
  - the fixes the next spec promotions made to imported `[C]` statements.

  The decision follows the ADR's audit rule.

## Open questions

- Does E15 need its own format for map rows that link several specs, or does Phase 0 show a shape every row already
  follows?
- Should the Tier A promotion re-check use a gate helper, such as a list of a finding's statements changed since a
  commit, rather than `git log -L` by hand? This is deferred until Phase 4 shows what the re-check costs.
- Wrong anchor (27 fixes) gets no check here. A warning for a bare `0x00XXXXXX` in a spec with no symbol row would
  find unnamed addresses, not wrong ones. It is left out unless Phase 0 shows otherwise.

## Implementation log

_(lanes append dated entries as phases land)_

### 2026-10-27 — Phases 0 and 1 (archivist, `lane/p53a`, from `main` 506fb55b)

**Phase 0: the rules as the table states them, run over the tree at 506fb55b.**

| Check | Checked | Hits | True | False | Causes |
|---|---|---|---|---|---|
| E14 | 1 446 tables | 8 | 7 | 1 | 6 findings rows with a fifth cell (a `(C since the lane/h2b review: …)` note before the Tag cell); 1 row of `docs/tables/README.md` (LvlWarp, a stray empty cell). False positive: `evidence-rules.md:147`, the E9 row, whose code span ``` ` ```mermaid ` ``` holds a triple-backtick run; the cell splitter toggled on every backtick, so the span was never closed. This is an implementation fault, not a rule fault: the splitter now pairs a backtick run with the next run of equal length (CommonMark). |
| E15 | 38 map rows with a spec link | 6 | 4 | 2 | True: `monsters/pool` and `monsters/spawn` (Status cell begins `reviewed: [`, no ` · `); `player/creation` (`updated 2026-10-20` against 2026-10-21); `stats/aggregate` (C 64 / L 5 against C 65 / L 4). False: `combat/README` (the group `C 240 / I 191 / L 24` is stated as "the five front matters summed"); `skills/dispatch` (the first group after the `skills/README` link is `dispatch C 75 / I 191 / L 10`, a label for the other spec; the overview's own group follows it and is right). |
| E16 | 55 plan rows + 2 indexes | 0 | 0 | 0 | none. |
| W7 | 7 `Total` rows | 0 | 0 | 0 | none. |

Value sets. Spec `status:`: `reviewed` 49, `draft` 2. Map status words: `reviewed` (bold or plain), `findings in progress`, `not started`, plus the malformed `reviewed:` twice. Mapping used: `reviewed` to `reviewed`, `draft` to `draft spec`; no map row links a draft spec today, so that half of the mapping is untested on real data. A row whose links are all findings or plans (`findings in progress`, `not started`) is not checked, since it links no spec. Plan `Status:` first words: `done` 48 (all under `done/`), `approved` 5 (none under `done/`); no `abandoned` plan exists yet.

Rule-change proposals (the table is the architect's; Phase 1 implements the rules as stated):

1. E15, the tag group: accept the row when any `C n / I n / L n` group between the link and the next spec link equals the spec's tags, instead of the first group only. This clears `skills/dispatch` and still catches a stale single group. Cost: dispatch's own group (the one before "and the overview") is then not checked, because no group sits between its link and the next one.
2. E15, sums: a segment that contains the word `summed` is exempt from the tag comparison (`combat/README`), or the map states the sum in words and not as a `C/I/L` group. The first is the cheaper rule.
3. E15, partial groups: the implementation compares the numbers a group gives; `C 15 / I 0` (monsters overview) is checked on C and I only. State it in the rule.
4. W7: add `All` (any case) to `Total` as the first-cell label. Four more rows exist (`plans/0038-inventory/README.md` twice, `findings/stats/experiments.md`, `tables/Skills.md`; `formats/ds1.md` is out of scope), checked by scratch script: all 4 sum correctly, so the extension costs no false positives and covers 4 wide tables. Today's seven `Total` rows are all single-column tallies in `plans/0038-inventory/`.
5. E14 scope: the rule text covers every tracked `.md`; nothing needs narrowing.

Side finding, done on the owner's request as its own commit (`perf(tools): gate W3 …`): the fast tier took 153 to 183 s, of which 151 s was the W3 loop (about 50 000 `re.search` calls over the joined corpus), so the commit hook's 20 s timeout failed open. W3 now looks names up in a word set built once (a name with another character falls back to the regex). W3 was 0 warnings on 3 666 symbols before and after. The new checks add about 6 s on the old timing and use no per-symbol or per-line corpus scan. Wall time after: `gate.py --no-warnings` 5.4 s, `gate.py --staged --no-warnings` 5.6 s.

**Phase 1: implemented in `tools/gate.py`** (`iter_tables`, `check_table_cells`, `check_map_rows`, `check_plans_index`, `check_index_numbers`, `check_totals`; the module docstring and the rule list updated; `DEMOTED` holds the rules reported as warnings). The cell splitter `table_cells` was rewritten to pair backtick runs (see E14 above). Fixtures: `E14`, `E15`, `E15-tags`, `E15-updated`, `E16`, `E16-next`, `E16-done`, `E16-adr`, `W7`, and base files for the map, the plan and ADR indexes, a table with code spans and a fenced table, and a `Total` table. `tools/test_gate.py` has a case for each (23 tests, green).

Hits and the arithmetic (counts are warnings or errors reported by the gate at the tip):

| Check | Phase 0 | Fixed here | Filed | At the tip | Level at the tip |
|---|---|---|---|---|---|
| E14 | 8 | 2 (`docs/tables/README.md` stray cell; the splitter fault, so `evidence-rules.md:147` no longer hits) | 6, reverser | 6 | warning (`DEMOTED`) |
| E15 | 6 | 0 | 6, architect | 6 | warning (`DEMOTED`) |
| E16 | 0 | 0 | 0 | 0 | error |
| W7 | 0 | 0 | 0 | 0 | warning |

8 - 2 = 6 and 6 - 0 = 6. E14 and E15 stay warnings because the files they flag belong to other lanes; Phase 2 empties `DEMOTED` once the entries are fixed. Backlog entries: `2026-10-27-archivist-reverser-e14-table-rows-with-an-extra-cell-in.md` and `2026-10-27-archivist-architect-e15-research-map-rows-that-disagree-with-their.md`.

**Review request (architect).** Review `lane/p53a` at its tip. Check (a) the E15 mapping and the five proposals above against your intent for the rule table, (b) that `DEMOTED = {"E14", "E15"}` with the two backlog entries is the handoff you want for Phase 2, and (c) the `table_cells` rewrite, which every table check shares (W2 and the new checks); the gate output elsewhere is unchanged, and (d) the W3 commit. Copy E14, E15, E16 and W7 into `evidence-rules.md` § Mechanical checks in the review commit.

### 2026-10-27 — Review of `lane/p53a` (architect, Mode 3 for a tools lane): accept with fixes (4)

Checked from `git diff main...lane/p53a` and the log above. The four rules match the plan's table; each has a failing
fixture and the base passes (E15 three overlays, E16 four). `table_cells`: the gate on the lane tree with `main`'s
splitter swapped in differs from the lane's output only in E14's `evidence-rules.md:147` hit, so the rewrite changes
no other check (W2 4 648 checked, 0 warnings, both ways). W3's word set is equivalent to the bounded search for a
`[A-Za-z0-9_]+` name and falls back otherwise; 0 warnings on 3 666 symbols. `DEMOTED` with two entries is the handoff
wanted.

Rulings on the questions (the evidence-rules table now states them):

1. **E15, groups after a link:** the looser rule is refused. The first group between a link and the next link is
   compared, and the map convention is that a spec's own group comes first after its link. The `skills/dispatch` row
   is rewritten that way, so both groups are checked.
2. **E15, sums:** no exemption. A sum over several specs is written in words (`sum to C 240, I 191, L 24`), not as a
   group. The combat row now gives the overview's own `C 41 / I 42 / L 5` and the sum in words (checked: 41+34+80+46+39,
   42+30+64+25+30, 5+5+4+5+5).
3. **E15, partial groups:** tightened. A group must give all three numbers, and a group without `L` is an E15 error
   (fixture `E15-partial`). The monsters overview's `C 15 / I 0` becomes `C 15 / I 0 / L 0`.
4. **W7, `All` rows:** accepted (any case), fixture `W7-all`. 11 rows checked, 0 warnings.

Fixes (4): miscount 1 (the W3 commit subject's literal "160 s to ~Xs"; the log's 153 s to 5.4 s is right; noted, not
amended); other 3 (partial groups made an error, the `All` label added, the E15 status message cut to 40 characters
where it printed a whole cell).

The research-map hits are fixed in this commit, because rulings 1–3 are map conventions (Phase 2 below closes the
entry): `monsters/pool` and `monsters/spawn` get `**reviewed** · `; `player/creation` reads updated 2026-10-21 with
plan 0048 P3's staff-mod oracle rewording; `stats/aggregate` reads C 65 / I 42 / L 4, updated 2026-10-20, with plan 0047
P1's J4 (the full Trang-Oul's `state` and `oskill` blocks `[C]`) in place of the stale `[I]`. E15 leaves `DEMOTED`.
E14, E15, E16 and W7 are in `evidence-rules.md` § Mechanical checks.

### 2026-10-27 — Phase 2 (architect, `lane/p53a`)

- **Backlog.** The E15 entry to the architect is closed (archive/) with the review commit's map fixes. `DEMOTED` now
  holds only E14: its six findings rows wait for the reverser's entry
  `2026-10-27-archivist-reverser-e14-table-rows-with-an-extra-cell-in.md`, and whoever lands that entry empties the set
  in the same commit (`tools/gate.py`, `evidence-rules.md`'s sentence under the errors table). Until then the Phase 2
  *Done when*'s "E14–E16 at error" holds for E15 and E16 only.
- **Lane check.** `.claude/skills/architect/references/lane-check.md`: which lane kinds are Tier B, the inputs and the
  scope limit (the diff, the request, the lane's `review-fixes.md`, and range reads for three anchors), the four checks,
  the escalation list, batching of up to three disjoint lanes, the verdict format.
- **Skill.** `SKILL.md` Mode 3 opens with the tiers, the promotion re-check of imported `[C]` (`git log -L`), the
  every-fifth audit with its ledger form and its two-in-five rule, and gate first; References lists the lane check.
- **Ledger.** `docs/plans/metrics.md` § Kinds (new): the kind list with `architect-check`, one row per lane for a
  batched check, and the audit row as an `architect-review` whose Fixes cell begins `audit of <lane>:`. No rows added.
- **Not done here:** the orchestrator's lane-model memory note (an Outputs item) is the orchestrator's own file; it
  should point at `SKILL.md` Mode 3 § Tiers and `lane-check.md` before Phase 3 starts.

**Next: Phase 3** (human, the orchestrator): the next ten non-spec lanes through `lane-check.md` on Sonnet, the fifth
and tenth also at Tier A as audits, every run in the ledger.

### 2026-10-30 — Phase 3 closed (architect, `lane/p53e`, from `main` 2a43b9f1)

The trial's *Done when* holds. The ledger has 11 `architect-check` rows and 2 audit rows, each with tokens, tool uses,
wall minutes, a verdict and fixes by category:

- the checks: `lane/r52`, `p50f`, `h6g`, `wiki50`, `h6gs`, `r52b`, `a55`, `a54`, `h1c`, `r52c`, `a7b`;
- the audits: `lane/h6gs` (reverser-static) and `lane/a7b` (archivist).

One check is extra. In ledger order the audits fell on the 5th and the 11th Tier B lane, not on the 5th and the 10th
(`lane/r52c`). The orchestrator's merge subjects call `lane/a7b` "the 10th-check audit", so its count left one check
out. That does not bias the sample: the audit was taken on the next lane, and from now on it falls on every fifth row
in ledger order. No lane was escalated. One Tier A lane fell inside the trial, `lane/r55`, which plan 0055 sent to
Tier A as a P1.1 gate.

### 2026-10-30 — Phase 4: evaluation, and ADR-0023 settled (architect, `lane/p53e`)

**Cost.** These figures come from `metrics.py summary --by kind` and from the ledger's `architect-review` rows, each
joined to the kind of the lane it reviewed (by lane name, with the trial's two audits included).

| Lane kind | Tier B checks | Tier B mean | Tier A reviews | Tier A mean |
|---|--:|--:|--:|--:|
| reverser-static | 4 | 70 825 | 59 | 149 150 |
| reverser-harness | 3 | 79 308 | 33 | 171 589 |
| archivist | 3 | 61 337 | 24 | 112 407 |
| wiki | 1 | 74 320 | 12 | 129 965 |
| Every kind (means over all runs) | 11 | 70 868 | 128 | 146 247 |

- A check costs 48% of a Tier A review of the same kind. It takes 9 to 21 tool uses and 2 to 3 wall minutes.
- The two audits cost 117 526 and 111 770 (mean 114 648).
- Counting the audits, a Tier B lane costs 70 868 + 114 648 / 5 = 93 798 tokens, against 146 247 at Tier A: a saving of
  52 449 per lane (36%).
- Over the trial's 11 lanes the saving is 11 × 146 247 − (779 553 + 229 296) = 599 868 tokens.

**Quality.**

- The checks made 12 fixes in 11 lanes (1.1 per lane): overclaim 5, omission 4, stale cross-reference 2, other 1.
  Four lanes got none. The seed's Tier A rate for these kinds was 3.7 to 5.6 fixes per reviewed run.
- In the two audited lanes the checks found 2 fixes and the audits found 9 more. The checks therefore found 2 of the
  11 fixes in those lanes (18%).
- **Reject-grade misses: none in either audit.** No miss was a `[C]` without its source that later work rests on, or a
  wrong address under a claim.
- **The 9 misses by category:** stale cross-reference 4, omission 4, misread 1.
- **The 9 misses by cause:**
  - (a) 3 stale sentences in the same document outside the diff hunks (MonAI.md § The AI table, § Batches, open
    questions 1 and 3; `lane/a7b`);
  - (b) 1 stale sentence in a finding the diff contradicted (quests/0001's arming bullet; `lane/h6gs`);
  - (c) 2 disagreements with another finding, "routed" or written around with no backlog entry (the corrected `anc`
    session and the J2 wording; ai/0001's state-row overcount);
  - (d) 1 problem inside the diff that the check saw and left as a nit (two missing register sites);
  - (e) 2 that needed the disassembly (the altar operate's step-4 exit, a misread; the grant's step-0 call, an
    omission).

  Causes (a) to (d), 7 of the 9, are what the two auditors named: a pass over the touched document and the findings it
  touches, and a routing entry for every disagreement. Cause (e) is outside Tier B by design. The promotion re-check
  holds it.

**Promotion re-check.**

- One spec promotion fell in the trial: `lane/s50p3`, 2026-10-27, Tier A ([plan 0050](../0050-animation-frame-timing.md)
  § Phase 3 review).
- It re-checked the two finding statements that had been raised under a Tier B check (`lane/p50f`): `UnitQueueEvent`'s
  partial raise and the restart correction. Both held, and neither got a fix.
- The re-check's cost cannot be separated from the 205 688-token review. Open question 2 (a gate helper that lists a
  finding's statements changed since a commit) therefore stays deferred: one promotion with two imported statements
  does not justify it.

**Decision.**

- **ADR-0023 is `accepted`.** By its own rule, no lane kind goes back to Tier A: the audits found 0 reject-grade
  misses, and the rule needs 2 in 5 audits of one kind to trigger.
- The audits so far cover one reverser-static lane and one archivist lane. Harness and wiki have no audit yet. The
  every-fifth rotation continues in ledger order.
- The misses, 4 to 5 per audited lane, are real but cheap. Two kinds of them do not resurface on their own, so they are
  settled in two parts:
  1. **In `lane-check.md` now:** check 5 (every disagreement with a document the lane does not own has a backlog entry
     in the diff, or the check files one, counted as an omission) and check 6 (no silent nits). Both stay inside
     ADR-0023's scope limit, because they read only the diff. Causes (c) and (d), 3 of the 9.
  2. **Proposed in [ADR-0024](../../adrs/0024-lane-check-touched-documents-and-routing.md)**, for the owner: a pass
     bounded by greps over each touched findings, table, format or wiki document, and over `docs/findings/`, for the
     subjects of the changed lines. Causes (a) and (b), 4 of the 9. It widens the scope limit that ADR-0023 § Decision
     states, so it needs the owner's approval. The estimated cost is +15k to 25k tokens per check, which brings the
     saving from 36% down to about 20%. The next two audits measure both the misses and the cost.
- `SKILL.md` Mode 3 and `lane-check.md` now name ADR-0023 as accepted and ADR-0024 as proposed.

**Residual.** E14 is still in `DEMOTED`. It waits for the reverser's open entry
[`2026-10-27-archivist-reverser-e14-table-rows-with-an-extra-cell-in.md`](../../backlog/2026-10-27-archivist-reverser-e14-table-rows-with-an-extra-cell-in.md),
whose lander empties the set (see Phase 2). This plan closes with the entry homed there.

**Owner question.** Accept ADR-0024? That means widening Tier B's scope with the grep-bounded touched-document and
touched-findings passes, at about +20k tokens per check. The alternative is to keep ADR-0023's diff-only scope and
accept about 2 stale sentences per lane that wait for a later touch or a promotion.

**Plan closed:** status `done`, moved to `done/`, the plans index updated. The ADR index has 0023 `accepted` and 0024
`proposed`, and the next free ADR number is 0025.
