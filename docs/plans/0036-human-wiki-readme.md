# 0036 — A human wiki over the reviewed specs, and a refreshed main README

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, spec-writer
> **Related ADRs:** 0006-docs-gate, 0009-public-documentation-site, 0012-human-wiki

## TL;DR

**Question:** can a person who has played Diablo II understand from a few pages how the game builds a level, fills
it with monsters and objects, and decides what drops, without reading the specs? This plan writes that wiki under
ADR-0012 in `docs/wiki/` (not published) and brings the main `README.md` up to date. **It runs last in the queue**:
it explains the specs that are reviewed when it starts, and it is refreshed by later plans.

When it is done:
- `docs/wiki/README.md` is the index, with a reading order;
- one page per topic below, each based only on reviewed specs and linking them section by section;
- the gate checks the wiki's rules;
- `README.md` shows the current status, the wiki, and a short "how to read this repository" path.

## Context

- Reviewed specs on 2026-10-15: `rng`, `rng/seeds`, `data/excel`, `drlg/overview`, `drlg/room-tiles`, `drlg/preset`,
  `drlg/collision`, `drlg/maze`, `drlg/warps`, `drlg/outdoor`, `objects`, `items/tc`, `items/quality`,
  `items/affixes`, `items/uniques-sets`, `items/properties`, `monsters/pool`, `monsters/spawn`, `monsters/special`,
  `monsters/stats`, `save/d2s`. Plans 0028–0035 may add `data/strings`, `items/sockets-runewords`, `items/cube`,
  `items/vendors`, `items/quest-drops`, `hirelings`, `player/creation` and `data/calc` before this plan starts.
- [ADR-0012](../adrs/0012-human-wiki.md) sets the rules: no claims of its own, links per section, no tags, anchors,
  addresses or decompile-shaped code, reviewed specs only, a `based_on:` front matter, owned by the spec-writer, not
  published. [ADR-0009](../adrs/0009-public-documentation-site.md) still governs any publication.
- The gate (ADR-0006) already checks links (E8) and Mermaid (E9) in every tracked `.md`, so wiki pages get both for
  free. The ADR-0012 rules need a new check.
- [README.md](../../README.md) lists the reviewed specs and the done plans in a long run-on sentence; it doesn't
  mention the wiki, the harness or how a newcomer should read the repository.

## Phases

### Phase 0 — Gate rules for `docs/wiki/`
- **Owner skill:** archivist (owner of `tools/`)
- **What:** add the wiki checks to `tools/gate.py`, with fixtures and tests.
- **Outputs:** `tools/gate.py` (new rules), `tools/gate/fixtures/` cases, `tools/test_gate.py` tests; the rule list in
  `.claude/skills/architect/references/evidence-rules.md` § Mechanical checks, updated by the architect when the phase
  is reviewed (backlog entry).
- **Done when:** for files under `docs/wiki/`, the gate reports:
  - an **error** for a confidence tag (`[C]`, `[I]`, `[L]`), a `fn:`/`data:`/`tbl:`/`struct:` anchor, or an address
    of the form `0x00XXXXXX`;
  - an **error** for a page (other than the index) with no `based_on:` front matter, or with a `based_on:` path that
    is not a spec, or a spec whose `status:` is not `reviewed`;
  - an **error** for a `##` section with no relative link into `docs/specs/`;
  - a **warning** when a `based_on:` date is older than that spec's `updated:` date.

  The fixtures cover each rule both ways; the gate is green on `main`.

### Phase 1 — The wiki pages
- **Owner skill:** spec-writer
- **What:** write the index and the topic pages from the reviewed specs, in plain prose with diagrams.
- **Outputs:** `docs/wiki/README.md` and these pages (merged or split as the material demands; the index says why):
  - `randomness.md`: one seed per thing: the RNG, the seed tree, why the same game seed gives the same map
    (`rng`, `rng/seeds`);
  - `game-data.md`: what the excel tables are and how the game reads them (`data/excel`, `data/strings` if reviewed);
  - `levels.md`: how a level is built: acts, levels, rooms, the three generators, presets, warps, the collision grid
    (the `drlg/*` specs);
  - `monsters.md`: which monsters a level can have, how a room is populated, packs and minions, champions, uniques
    and superuniques, their stats (`monsters/*`);
  - `objects.md`: shrines, chests and other objects, and what a chest drops (`objects`);
  - `items.md`: one item drop end to end: treasure class, quality and magic find, uniques and sets, affixes and rare
    names, base stats, sockets and ethereal (`items/*`), plus the other creation paths whose specs are reviewed by
    then (cube, vendors, quest drops, sockets and runewords);
  - `saves.md`: what a `.d2s` holds and how an item is stored (`save/d2s`);
  - `how-we-know.md`: how the project works and how to read a spec. This covers the evidence tags, runs and
    bit-exact reproduction, and what "reviewed" means. It summarises ADR-0001, ADR-0003, ADR-0004 and the
    evidence rules, and links them. It does not link a spec section, so its front matter says
    `based_on: [process]` and the gate exempts it from the section-link rule.
- **Done when:**
  - every page passes the Phase 0 rules;
  - each topic page has at least one Mermaid diagram of its main flow and one worked example taken from a spec's
    worked example (numbers copied, not invented), with a link to it;
  - every `[I]` point and open question of a spec that a page touches is mentioned in words where it matters;
  - the index gives a reading order and a one-line answer per page ("read this to learn…");
  - the glossary is linked for every D2 term on first use;
  - the architect's review passes. The review checks, on at least three sections per page, that the prose claims no
    more than the spec it links.

### Phase 2 — Main README
- **Owner skill:** spec-writer
- **What:** refresh `README.md`: the status table from the research map (all bands, reviewed or not, with the date),
  the wiki as the first stop for readers, a "how to read this repository" path (wiki → spec → finding → run record),
  the plans in flight, and the done plans as a short list instead of the run-on sentence.
- **Done when:** every row of the research map appears in README with the same status; README links the wiki index,
  the research map, the plans index and the ADR index; the setup section is still accurate (checked against
  `.claude/skills/reverser/references/tooling.md`); there is no provenance wording about where the game files came
  from; the gate is green; the architect's review passes.

## Open questions

- Whether the wiki should later include `[I]`-heavy topics with a visible "provisional" banner (needs an ADR-0012
  amendment).
- The redacted export of ADR-0009 may start from these pages. That is a separate plan, written only if the owner takes
  publication up again.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a human wiki, not published, plus a README update, as
  the last plan of the unattended queue. ADR-0012 is written alongside. Written in the architect worktree
  `lane/plans0028`.
- **2026-10-15 — Phase 0 landed (archivist, `lane/afu`).** Rules E10 (tags, anchors, addresses), E11 (`based_on:`
  to reviewed specs, index exempt), E12 (each `##` section links `docs/specs/`, `process` pages exempt) and the W4
  staleness warning in `tools/gate.py`; fixtures for each rule both ways (green base wiki plus seven overlays), 22
  gate self-tests pass, gate green on the repo. The `based_on:` form is `docs/specs/<...>.md YYYY-MM-DD` per entry
  (flow or block list) or `[process]`; Phase 1 writes it that way. No surprises.
- **2026-10-15 — Phase 0 accepted (architect review, `lane/afu`).** All four *Done when* bullets met, fixtures
  both ways, 22 self-tests OK, gate green. The architect added the E10–E12 and W4 rows to `evidence-rules.md`
  § Mechanical checks. Notes for Phase 1: E10 also rejects the tag strings on the `process` page, so it names the
  tags in words; `run:` and `src:` ids are not caught by E10 but are anchors all the same, so pages leave them out;
  a page with no `##` section passes E12 trivially, so topic pages use `##` sections.
- **2026-10-16 — Phase 1 landed (spec-writer, `lane/w36`).** `docs/wiki/`: the index plus ten pages, over every row
  `reviewed` on 2026-10-16 (all 32 reviewed spec files; the two draft READMEs, `items/README` and `save/README`, are left out).
  Two changes to the planned cut, explained in the index: items split into [items](../wiki/items.md) (one drop end to
  end) and [items-other-paths](../wiki/items-other-paths.md) (sockets and runewords, cube, vendors, quests), and a new
  [characters](../wiki/characters.md) page for `player/creation` and `hirelings`, reviewed after the plan was written.
  Each topic page has a main-flow Mermaid diagram (29 diagrams in all), worked examples copied from the specs' worked
  examples with links, a *What is not known yet* section, and its `based_on:` lists every spec it links. Each page
  was drafted from its specs and then checked section by section by a second pass against the same specs (every
  worked-example number, every `##` section for over-claiming, glossary first use); that pass made about 80 wording
  fixes, mostly hedges restored on code-only points and generalisations narrowed. Gate green (E10–E12 0 errors, no
  W4). Spec inconsistencies met on the way are filed in the backlog (spec-writer and architect); none blocks a page,
  which follows the spec section it links and says where two specs differ (the chest-tier input on
  [objects](../wiki/objects.md)).
