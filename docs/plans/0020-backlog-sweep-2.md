# 0020 — Backlog sweep 2: doc follow-ups, the classic TC replay and the Acts III–V owner session

> **Status:** approved (2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer, human
> **Related ADRs:** 0003-runtime-experiments, 0006-docs-gate

## TL;DR

**Question:** which open backlog entries can be closed with the data, logs and code reading already in hand? Plans
0014 and 0016 left table-doc follow-ups, and plan 0010 left one model gap. Two spec wordings are also open. The
`tools/d2s.py build` quest recipe is half done, and it blocks the owner session that plan 0016 left for Acts III and V.
This plan works through those entries in the manner of [plan 0015](done/0015-backlog-sweep.md):
1. data docs and the recipe;
2. the classic TC pick in `tools/tc.py replay` against a log that is already recorded;
3. the spec edits;
4. one owner session for the runtime cases.

When it is done, every backlog entry listed below is struck or carries a **Plan:** pointer to a planned row. The
classic branch of items/0001 is reproduced on the recorded log. The Acts III–V preset cases that the session reaches
are `[C]`.

## Context

- Entries in scope (all in [backlog](../backlog.md)):
  - archivist: the act/quest recipe for `tools/d2s.py build` (`acts_open` done, "all quests completed" not; from
    [save/0002 § Recipe](../findings/save/0002-quest-words.md#recipe-for-toolsd2spy-build));
  - archivist: the plan 0014 Phase 1 follow-ups, part (a), linking the answered MonStats and Levels meanings;
  - archivist: the plan 0016 Phase 1 and Phase 2 results for LvlPrest, ds1.md and MonPreset, and the act-index-2
    rewrites in `tools/ds1.py`;
  - archivist: the Levels `umon` count at `+0x035`;
  - reverser: `tools/tc.py replay` and the classic TC pick (183 of 485 calls of `workspace/logs/tc-quality-3.log` stop
    at `classic selection not modelled`);
  - spec-writer: the links to items/0001 § 10 left in [specs/items/tc.md](../specs/items/tc.md);
  - spec-writer: scope the `save/d2s` width-clamp pitfall to the item writer;
  - reverser and human: the Acts III–V `drlg-preset` coverage and the client row-skip counter (both from plan 0016,
    "opportunistic").
- Out of scope, routed elsewhere:
  - the MonUMod table doc in the plan 0014 follow-ups (b) and in the Levels `umon` entry → [plan 0018](0018-monsters-special.md)
    Phase 0;
  - the MonStats2 `spawnCol` survey, part (c) → [plan 0017](0017-drlg-collision.md) Phase 0;
  - the `MonSpawnTry` early exits → reverser backlog (plan 0014 closed with them open; not blocking);
  - the plan 0010 Phase 2 fixes F1/F2 → plan 0010;
  - the MonPlace keyword names and `0x0054E2A0` → plan 0018 Phase 1;
  - the d2s affix and runeword fields → `items/affixes`, `items/sockets-runewords`;
  - DS1 (c) bits, `LvlSub` groups, path `action` → `drlg/outdoor` and monster AI;
  - the `lvlmaze` columns → `drlg/maze`;
  - the 1.14d `patch_d2.mpq` question and the `*code.bin` formats → `data/calc`, no plan.
- Lane load: the archivist also has plan 0017 Phase 0 and plan 0018 Phase 0. Phase 1 here is small and can go first
  or in between. The reverser's Phase 2 here uses a recorded log only, so it can fill gaps between the plan 0017 and
  0018 reading phases.

## Phases

### Phase 1 — Data docs and the quest recipe
- **Owner skill:** archivist
- **What:** apply the table-doc follow-ups from plans 0014 and 0016, and finish the quest recipe of `tools/d2s.py build`.
- **Outputs:**
  - [MonStats](../tables/MonStats.md) § Spawn columns and [Levels](../tables/Levels.md) (`MonWndr`, `MonSpcWalk`,
    `MonUMin`/`MonUMax`, `WarpDist`, and the `umon` count at `+0x035`, filled at load), linked to monsters/0002;
  - [LvlPrest](../tables/LvlPrest.md): `Populate`, `Logicals`, `Pops`, `PopPad` and the other drlg/0004 meanings,
    linked;
  - [ds1.md](../formats/ds1.md) and [MonPreset](../tables/MonPreset.md): the act-index-2 rewrites (MonStats 297 →
    object 382, 366 → object 404, each made a type-2 unit, mode 0) and object `flags` bit 0, with the provisional act-3
    survey counts settled;
  - `tools/ds1.py` with the act-index-2 rewrites;
  - the recipe key `quests: all` in `tools/d2s.py build` (words 1–6, 9–14, 17–22, 25–27, 35–40 per difficulty, leaving
    0, 8, 16, 24, 29–34 and 41, then re-checksum).
- **Done when:**
  - each entry's lettered points are struck or answered in the backlog;
  - `d2s.py survey` reads a `quests: all` save clean;
  - the ds1 survey prints act-3 counts with no provisional mark;
  - the gate is green.

### Phase 2 — The classic TC pick in the replay
- **Owner skill:** reverser
- **What:** model the classic selection (`cumClassic`/`totalClassic`, [items/0001 § 5](../findings/items/0001-tc-resolution.md#5-the-pick-loop--tc_resolvedrops-0x0055a6d0))
  in `tools/tc.py replay`.
- **Outputs:** `tools/tc.py`; an added check in [run:2026-10-13-quality](../findings/items/experiments.md#run2026-10-13-quality)
  (same run, a new check, no new session); items/0001 § 5 classic bullets.
- **Done when:**
  - `tools/tc.py replay` on `workspace/logs/tc-quality-3.log` reproduces all 485 calls (0 `classic selection not
    modelled`, 0 mismatches);
  - the command and its output are quoted in the run record;
  - the classic-branch bullets of items/0001 are raised to `[C]` citing the run, or the case that differs is named.

### Phase 3 — Spec links and small edits
- **Owner skill:** spec-writer
- **What:** apply the two spec-writer entries, and take the items/0001 classic tags of Phase 2 into the spec.
- **Outputs:** [specs/items/tc.md](../specs/items/tc.md) (links to items/0002 § 1–§ 2 and § Answer; the classic-branch
  tags), [specs/save/d2s.md](../specs/save/d2s.md) (the width-clamp pitfall scoped to `BITBUF_WriteClamped`, with the
  `gf` contrast at 0x0056965B–0x00569661).
- **Done when:**
  - both entries are struck;
  - `items/tc` stays `reviewed`, with the tag counts in its header updated;
  - `save/d2s` stays `draft`;
  - the gate is green.

### Phase 4 — Owner session: Acts III and V
- **Owner skill:** human (the reverser prepares the save and the logger, and writes the record)
- **What:** one played session on a `quests: all` save (Phase 1), under the `drlg-preset` logger with a row-skip
  counter added.
- **Outputs:** a run `run:YYYY-MM-DD-acts-3-5` in [drlg experiments](../findings/drlg/experiments.md) and, for the
  load test, in [save experiments](../findings/save/experiments.md); bullets of drlg/0004 and save/0002 raised where
  reached.
- **Done when:**
  - the record states, per case, reproduced or unreached. The drlg cases are: a maze preset room in Act III and in Act
    V; the act-index-2 rewrite of 366; the act-index-4 rewrites 537..539; the draws of MonStats 371/372, MonPlace 33
    and objects 196/261; MonPlace 35 dropped; at least one client row skip on a floor main
    (`DRLG_PresetClientUnitsB`, switch `0x0066638C`);
  - the load test of save/0002 is recorded: the Act II–V waypoint tabs shown for a `quests: all` save;
  - every reproduced case raises its bullet to `[C]`, and the reverser files a spec-writer entry for the
    [drlg/preset](../specs/drlg/preset.md) revision.

## Open questions

- Phase 4 is a played session, so some cases may stay unreached (an Act V maze preset depends on where the player
  walks). An unreached case keeps its `[I]` and its backlog entry. It does not block closing the plan.
- If the `quests: all` save loads with quest scripts in a state that changes the preset rolls (e.g. a quest object
  already used), Phase 4 notes it. A preset whose roll depends on quest state is a `drlg/preset` revision, not a fix
  here.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted (architect).** Collected from the open backlog entries that the data, logs and reading
  already in hand can close. The runtime cases from plan 0016 are kept as one owner session. Waits for the owner's
  approval.
- **2026-10-14 — Approved (human).** No changes to the draft. Phase 1 (archivist) and Phase 2 (reverser) can start.
- **2026-10-14 — Phase 1 landed (archivist, branch `lane/a0020p1`).**
  - Quest recipe: `tools/d2s.py build` has the key `quests` (`"all"`, or a list of difficulties). It sets the
    `acts_open` words plus 1–6, 9–14, 17–22 and 25–27 (and 35–40 in an expansion save), leaves 0, 8, 16, 24, 29–34
    and 41–47 untouched, and re-checksums ([d2s.md § Writer](../formats/d2s.md#writer-build)). The waypoint field
    and `progression` stay with their own keys.
    - Check: a copy of `lightsorc.json` with `"quests": "all"` was built on `samples/d2s-owner/smpsor-l50.d2s` into
      `workspace/scratch/a0020p1/` (sha256 `952b1f7c…`). `d2s.py survey` exits 0. Bit 0 is set in exactly those
      31 words in all three blocks, and no other quest word changed. A copy of `classicsorc.json` with
      `"quests": ["normal"]` (same base) changes only block 0.
    - The existing recipes in `tools/d2s_recipes/` are unchanged. Phase 4 builds its own save.
  - Data docs, linked to monsters/0002:
    - [MonStats § Spawn columns](../tables/MonStats.md#spawn-columns-plan-0014-phase-0): `MinGrp`/`MaxGrp`,
      `PartyMin`/`PartyMax` and `minion1/2` are now `[C]`. `sparsePopulate` is `[I]`. `SetBoss`, `BossXfer`,
      `Align` and `neverCount` are `[I]` reads whose effect is still open.
    - [Levels](../tables/Levels.md): `MonDen` density, `MonUMin`/`MonUMax` with (0,0) meaning no random
      specials, the `umon` pick with its `+0x035` count (now `[C]`), `MonWndr`, `MonSpcWalk` and `WarpDist`.
  - Data docs, linked to drlg/0004:
    - [LvlPrest](../tables/LvlPrest.md) has a new § Semantics from the preset findings, which covers every
      remaining column and `+0x024`.
    - [ds1.md](../formats/ds1.md): `flags` bit 0, the act rewrites, and LvlPrest groups as dead data.
    - [MonPreset](../tables/MonPreset.md): the rewrites, and the per-kind spawning answered.
  - `tools/ds1.py` `_units` applies the act-index-2 and act-index-4 rewrites (`ACT_REWRITES`). Each rewritten unit
    becomes type 2, mode 0, as in `tools/drlg.py`. `ds1.py units` now prints the six rewrites and `rewrites=6`;
    the gate baseline `ds1_units` is updated (monsters 2102 → 2101, npcs 165 → 160, objects 14105 → 14111).
  - Act-3 counts settled: 799 monsters, 18 npcs and 3 801 objects; in the MonStats range, 394 units (12 classes).
    The act-5 row changed too: the four act-index-4 rewrites had been counted as npcs, and are now objects.
  - Surprise: the ds1.md paths note had called the townwest object path owner the rewritten `nihlathak`. The
    pre-change survey did not rewrite at all, and its two object owners were stored objects (rows 379 and 543).
    With the rewrites there are four object owners, two in each file. Corrected.
  - Commands: `python3 -I tools/ds1.py units workspace/merged` (exit 0, `rewrites=6 … errors=0`);
    `python3 -I tools/gate.py --full=ds1_units,ds1,d2s,d2s_roundtrip` is green.
  - Backlog: the plan 0016 Phase 1 and Phase 2 entries are struck. Part (a) of the plan 0014 follow-ups is struck.
    The Levels `umon` part is struck, and its MonUMod part stays with plan 0018. The recipe request is struck,
    and its load test stays with Phase 4.
- **2026-10-14 — Phase 2 landed (reverser).** `tools/tc.py replay` models the classic branch of items/0001 §5–§8:
  `totalClassic`, the linear scan that skips expansion-only entries, the `version ≥ 100` reject, and the throwable
  refund with its Long Sword fallback. The recorded `workspace/logs/tc-quality-3.log` is replayed with no new run.
  - **Result:** `python3 -I tools/tc.py replay workspace/logs/tc-quality-3.log --quality model` gives `485 calls, 485
    reproduced, 0 failed` with no oracle, and the classic line `scan 664, plain 664, skip 0, miss 0, vreject 0,
    refund 16, lsd 0`. The oracle mode gives the same result. The earlier expansion logs are unchanged:
    `tc-quality-1` 1269/1269, `tc-quality-2` 944/944, `tc-champion-1` 124/124, `tc-party-1..3` and `tc-run19`.
  - **Record:** added as a check in [run:2026-10-13-quality](../findings/items/experiments.md#run2026-10-13-quality),
    with the command, its output and four counterfactuals. Using `totalExp` with the `cumExp` search breaks 41 calls,
    and dropping the throwable refund breaks 13. The `cumExp` search, or a scan without the skip, breaks none,
    because no pick had an expansion-only entry before it.
  - **items/0001:** two `[C]` "observed part" bullets were added. In §5.1, the classic total and the scan with no
    skipped entry. In §8, the throwable refund. The skip itself, the off-the-end miss, the `version` reject and the
    Long Sword after ten throwables are named as not exercised and stay `[I]`. The status line is updated, and
    items/0002's check table now reads 485/485.
  - **Backlog:** the reverser → reverser entry is struck. A new entry to the spec-writer lists the specs/items/tc
    tags that Phase 3 picks up.
  - **Next:** Phase 3 (spec-writer) can take the classic tags. The gate is green.
