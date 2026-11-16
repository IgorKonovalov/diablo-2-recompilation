# 0070 — The redacted public export: what leaves the machine, how it is redacted, and the check that guards it (ADR-0009)

> **Status:** draft (2026-11-16; for the owner's approval; not started)
> **Created:** 2026-11-16
> **Owner skill(s):** architect, archivist, spec-writer, human
> **Related ADRs:** 0009-public-documentation-site, 0034-local-documentation-site, 0012-human-wiki, 0031-constants-of-the-code-image, 0005-presentation-formats-tools-only, 0006-docs-gate

## TL;DR

**Question:** what can be put online, how is it redacted, and what stops a mistake from leaving the machine? On
2026-11-16 the owner asked why we can't publish when fan sites publish similar material, and asked for this plan.
[ADR-0009](../adrs/0009-public-documentation-site.md) already gives the answer's shape: a separate, heavily redacted
export, with no tie to this repository, behind a mechanical publish check, published by the owner. ADR-0009 leaves
three things to "the plan that builds the export": the redaction depth, the check, and the footer. This plan proposes
them. When it is done:

- an allowlist names every page the export holds;
- `tools/export_build.py` cuts the export into `workspace/export/` from that allowlist, with the redaction applied;
- `tools/export_check.py` is green on the cut, and its self-tests are a gate rule;
- the architect has reviewed the cut at Tier A, and the owner has read it;
- the owner, and only the owner, chooses a host and publishes.

No agent publishes, uploads or pushes anything under this plan.

## Context

- **What fan sites do, and why this is different.** Community pages describe mechanics in their own words: drop
  rates, affix tables, breakpoints. Copyright covers expression, not methods or facts (ADR-0009 § Context). Our specs
  are also our own words. They differ in three ways. They carry addresses and anchors into the binary on nearly every
  line. Their pseudocode follows the code step by step. And they show, by design, that the game was reverse
  engineered. ADR-0009's five risk kinds are about exactly those differences. The export removes them, and what is
  left is close to what fan sites publish, only more exact.
- **The working repository stays public.** The owner decided on 2026-11-16: "working repo should stay public, I
  think risk is rather small". This plan takes that as settled. It does not reopen it. ADR-0009 § Negative recorded the
  same state. Its decision that the export carries **no tie to the repository** stands as written. Question 4 asks
  whether the owner wants to revisit that rule now that the repository's visibility is settled; this plan does not
  change it.
- **The local site exists.** [ADR-0034](../adrs/0034-local-documentation-site.md) added `tools/site_build.py` (stdlib,
  `python3 -I`, writes `workspace/site/`, no network request, Mermaid drawn at build time to inline SVG). It builds
  about 1 012 pages: the wiki, the specs, the glossary and every page they link. Its illustrations are game art. ADR-0034
  says ADR-0009's export carries none. Its footer ("Built locally from your own game files; not to be shared.") is for
  the local build only.
- **The size of the redaction** (counted at `main` `200625e8` by `grep -o` over the trees):

  | Tree | Files | Lines | Addresses `0x00XXXXXX` | `fn:`/`data:`/`struct:`/`tbl:` anchors | `run:` ids | Links into `findings/` | `sub_XXXXXXXX` names | `+0x` offsets |
  |---|---|---|---|---|---|---|---|---|
  | `docs/specs/` | 68 | 56 122 | 21 459 | 13 074 | 8 668 | 2 826 | 6 913 | 4 735 |
  | `docs/wiki/` | 23 | 11 226 | 0 | 0 | 0 | 8 | 2 | 0 |
  | `docs/glossary.md` | 1 | 163 | 0 | 0 | 0 | 0 | 2 | 36 |

  The wiki is close to publishable already. The gate's E10 bars tags, anchors and addresses from it (ADR-0012). The
  specs carry the whole evidence trail inline: an address on most pseudocode lines, an anchor group after most
  statements. Their 11 530 tags sit next to those anchors. So the specs need a mechanical redactor and a measured
  residue, not a hand edit.
- **Where the evidence sits in a spec.** Most of it is in three places a redactor can find: the parenthetical after
  a tag (`[C] … (fn:X@0x…, run:…, [items/0002 § 1](…))`), the address column at the end of a pseudocode line
  (`[I] (0x00558660–0x00558668)`), and the anchor and tag columns of tables. The residue is evidence written into the
  prose ("`TC_ResolveDrops` at 0x0055ADBA is the only call site"). Phase 3 measures it.

## Decisions this plan proposes

### Scope: an allowlist, not a denylist

The export holds only the pages an allowlist names, `docs/export/manifest.txt` (one docs-relative path per line;
architect-owned). A page reaches the export only by being named. Three scopes are offered (question 1):

| Scope | Holds | Notes |
|---|---|---|
| (a) | `docs/wiki/` (except `how-we-know.md`), `docs/glossary.md`, the export-only pages | Smallest. The wiki is already free of tags, anchors and addresses. The wiki's links into specs become plain text. |
| (b) **recommended** | (a), then the reviewed specs under `docs/specs/<subsystem>/` | The deliverable itself. It needs the redactor and Phase 4's residue fix. Cut (a) first; add (b) as a second cut once its check is green. |
| (c) | (b), plus `docs/formats/` and the column-schema pages of `docs/tables/` | File formats are the strongest interoperability case. Table pages listing constants of the code image ([ADR-0031](../adrs/0031-constants-of-the-code-image.md): `PathDirTables`, `ActClockTables`) stay out. |

**Excluded outright, in every scope:** `docs/findings/` (decompile-shaped listings), `re/` (the binary's symbol and
struct map), `docs/plans/`, `docs/adrs/`, `docs/backlog/` and `docs/backlog.md`, `docs/sources.md` (other people's
text), `docs/inventory.md` (file hashes and sizes), `docs/specs/README.md` (the research map, which is about the
repository; the export gets its own index), `docs/wiki/how-we-know.md` (the method page), every illustration and every
file of game art, and every *Open questions* section (it holds the `[L]` leads and the `src:` ids).

### Redaction depth, per ADR-0009's five risks

| Risk (ADR-0009) | Content | Proposal | Why |
|---|---|---|---|
| (1) contract, anti-circumvention | Addresses `0x00XXXXXX`, `sub_XXXXXXXX` names, in-memory `+0x` offsets | **Removed**, everywhere. A name with an address in it (`sub_00556F60_ItemRollQualityCreate`) loses the prefix or is dropped. | They tie each sentence to a place in the binary. A reimplementer does not need them; a verifier does, and the export can't serve verifiers (*Risks*). |
| (1) | `fn:`/`data:`/`struct:`/`tbl:` anchors, `run:` ids, finding ids and links, plan, ADR, backlog and lane names | **Removed.** Evidence parentheticals made only of these are dropped whole. A table column made only of them is dropped. | ADR-0009: no finding ids, no paths, no tie. |
| (1) | Method words: Ghidra, decompile, disassembly, gdb, breakpoint, harness, emulation, logger, "logged run" | **Removed from the export text.** The check fails on them. Phase 4 moves any left in spec prose into the evidence parenthetical, where the evidence rules put them anyway. | The export describes the game, not how we read it. It still shows that someone studied the game closely; that can't be redacted away (*Risks*). |
| (1) | Copy protection, CD key, Battle.net authentication, Warden | **Never present.** The check fails on any mention, the one-line "out of scope" notes included. | ADR-0009's standing ban, made mechanical for the export. |
| (2) code-shaped excerpts | Our pseudocode | **Kept**, inside a line the check enforces (below). | It is our own notation, language-neutral, numbered steps and our names. It describes a method, which copyright does not cover. |
| (2) | Anything decompiler-like | **Never present.** Findings are out; the check also scans specs' blocks. | ADR-0009 risk 2. |
| (2) | Mermaid diagrams | **Kept**, drawn at build time to inline SVG. The check scans their text like any other. | They are ours and illustrate only. |
| (3) data | Tables | **Kept only** when 20 body rows or fewer, schema and short illustrative rows. Our own tables over 20 rows (a step list, a decision table) pass only when the manifest names them with a reason, reviewed in Phase 5. | ADR-0009: a full table is more exposed than its schema; EU database right. |
| (3) | Item, monster, level and skill names; item codes | **Kept** where a statement needs them to name a row. | Naming a thing is nominative and factual. |
| (3) | Flavour text, quest dialogue, string-table text, rows of `.tbl` strings | **Never present.** The check flags quoted runs over 12 words for review; Phase 5 reads them. | Creative expression. |
| (3) | Constants of the code image (ADR-0031 listed values) | **Excluded** with their pages; a listed value quoted in a spec is removed with its address. | They are the binary's data, published only as needed in the working docs. |
| (4) trademarks | "Diablo II", "Lord of Destruction", "Blizzard" | **Nominative only**: to name the game and in the footer. No logo, no game art, no Blizzard styling, no domain or site name that uses a mark. | ADR-0009 risk 4. |
| (5) third-party text | `src:` ids, quoted community claims | **Removed** with *Open questions* and with the evidence parentheticals. | Other people's writing, under their terms. |
| (all) | Evidence tags `[C]`/`[I]` | **Kept** (question 2). `[L]` never reaches the export (it lives only under *Open questions*). An export-only page says what the two tags mean, in plain words, without naming the method. | The tags are our own claims about our own confidence. They tell a reimplementer where to be careful, and they cost no tie: without anchors they point at nothing. Dropping them would present inferred statements as certain. |

**The pseudocode line.** A fenced block may reach the export when it has numbered or labelled steps, our names, `←`
for assignment, and at most a width annotation (`i32`, `u8`). The check fails a block on: a line ending in `;`,
braces, `->` or `*(` pointer forms, casts such as `(int)`, `goto` or labels, `__` calling-convention words, any
decompiler artefact name (`param_N`, `local_XX`, `uVarN`, `iVarN`, `FUN_`, `DAT_`), any address or `+0x` offset left
after redaction. Today one decompiler artefact name stands in the specs (counted above under `DAT_|FUN_|param_…`).

**The footer**, on every page, close to ADR-0009's words:

> An unofficial, non-commercial preservation project. Not affiliated with or endorsed by Blizzard Entertainment.
> Diablo and Blizzard Entertainment are trademarks of Blizzard Entertainment, Inc. No game files, art, text dumps or
> code are included. Descriptions of behaviour are written in our own words. Cut on YYYY-MM-DD.

The cut is named by its date only. A commit hash would tie the export to this repository.

### Mechanics

- **Builder.** A new `tools/export_build.py`, not a profile of `site_build.py`. It imports `site_build`'s Markdown
  renderer and Mermaid step, so the HTML looks the same. It is a separate file because its job is the opposite:
  `site_build` follows links to pull pages in, the export refuses any page the manifest does not name. It never runs an
  illustration tool and drops every ```` ```illustration ```` block. It writes `workspace/export/site/` only (refusing any
  other path, as `site_build` does) and a residue report, `workspace/export/report.txt`.
- **Redactor.** A pass over each page's Markdown before rendering, in this order: drop *Open questions* sections;
  drop evidence parentheticals made only of anchors, run ids, addresses and finding links; drop anchor-only table
  columns; strip the address column from pseudocode lines, keeping the tag; strip `sub_XXXXXXXX_` prefixes. It never
  rewrites a sentence. What it can't clean it leaves, and the check reports it.
- **Link rewriter.** A link to a page in the manifest becomes a link to that page's export file (heading anchors
  kept when the heading exists there). Any other link keeps its text and loses its target. No link leaves the export:
  no repository URL, no owner name, no path into `docs/`, `re/` or `tools/`.
- **Export-only pages**, in `docs/export/` (spec-writer, reviewed like a wiki page): the front page (what the
  project is, what is in the export, how to read it), "How to read the tags" and the about page that carries the
  footer's statements. They make no claim of their own about the game.
- **Publish check**, `tools/export_check.py <export-dir>`. Read-only. It must be green before anything leaves the
  machine. It scans the built HTML, the inline SVG text and the redacted Markdown it was made from:

  | Rule | Fails on |
  |---|---|
  | X1 | an address `0x00XXXXXX`, any other hex of 6 digits or more, `sub_XXXXXXXX`, a `+0x` offset |
  | X2 | an anchor `fn:`, `data:`, `struct:`, `tbl:`, `src:`, `run:` |
  | X3 | a repository reference: `findings/`, a finding id shape (`items/0002`), `ADR-NNNN`, `plan NNNN`, `lane/`, `docs/`, `re/`, `tools/`, `workspace/`, a `.py` or `.csv` name |
  | X4 | an identity string: the repository's host path, the git `user.name` and `user.email` of the machine (read at run time, never stored), `/home/` or any absolute path |
  | X5 | a decompiler-like block (the pseudocode line above) |
  | X6 | a table over 20 body rows that the manifest does not name |
  | X7 | any `http:` or `https:` reference in `src`, `href` to an asset, `<script src>`, `<link>`, `@import` or `url(`; any `<script>` at all (the built pages need none) |
  | X8 | any image: `<img>`, an image file of any type, `<iframe>`, `<video>`; inline `<svg>` passes only with the Mermaid marker the builder sets |
  | X9 | the banned topics (copy protection, CD key, Battle.net authentication, Warden) and the method words |
  | X10 | a page without the footer, word for word, or with a footer missing its cut date |
  | X11 | a file type other than `.html` and `.css`; a `.git` directory or any dotfile |
  | X12 (warning) | a quoted run over 12 words, a capitalised name that matches no row name of the manifest pages' tables (a possible string-table leak); read in Phase 5 |

- **Gate.** One new rule, E20: `python3 -I tools/test_export_check.py` passes (fixtures in
  `tools/gate/fixtures/export/`, one bad case per rule and one clean page). The gate does not run the check on
  `docs/`. The working docs keep their full evidence; only the cut must be clean.

### Review

- **Phase 2's check** is a safety device, so its lane takes **Tier A**, not the archivist's usual Tier B.
- **The cut** takes a **Tier A redaction review** (Phase 5): the architect runs the check, reads the manifest and
  every X6 and X12 item, and reads a sample in full: every export-only page, five wiki pages, six specs (rng, items/tc,
  items/quality, monsters/spawn, drlg/maze and the page with the most redactions by the report), and the glossary.
  For each of the five risks it greps the cut once more by hand. A verdict of reject sends the cut back to Phase 4.
- **The owner's final read** comes last (Phase 6). The owner reads as much as they choose, and decides.

### Hosting (the owner chooses; question 3)

| Option | For | Against |
|---|---|---|
| GitHub Pages, a separate account and repository | Free, simple, static. Commits come from the publishing account. | Same platform as the working repository; the two accounts must not share an email, a name or a profile link. Takedowns follow GitHub's DMCA process. |
| Codeberg Pages | Non-profit, EU-based, static. | Its terms expect free-licensed content (check them; question 5 picks a licence). Fewer pages served per day. |
| A plain static host with upload (Neocities and similar) | No git history to leak an identity; upload the folder. | Another account; some hosts inject scripts or analytics, which must be off (X7 can be re-run on the served pages). |
| A self-hosted server | Full control, no third-party scripts. | Ties to a payment identity and a domain registrant; upkeep. |

Whatever the host: the owner copies `workspace/export/site/` into a fresh folder, not a clone of this repository, and
publishes under a neutral identity. No CDN asset is in the output (X7), so none can be added by the host unseen
unless the host injects it.

## Phases

### Phase 0 — The owner's approval and answers
- **Owner skill:** human
- **What:** approve or abandon this plan; answer questions 1 to 5.
- **Done when:** this plan's status is `approved` with the answers recorded, or `abandoned`.

### Phase 1 — The manifest
- **Owner skill:** architect
- **What:** write `docs/export/manifest.txt` for the chosen scope, with the reason line for each table over 20 rows
  allowed in advance (expected none at first).
- **Outputs:** `docs/export/manifest.txt`; this plan's log.
- **Done when:** every path in it exists, none is in an excluded tree, and the gate is green.

### Phase 2 — The publish check
- **Owner skill:** archivist
- **What:** `tools/export_check.py` with rules X1 to X12, its self-tests and gate rule E20.
- **Outputs:** `tools/export_check.py`, `tools/test_export_check.py`, `tools/gate/fixtures/export/`, `tools/gate.py`
  (E20 only).
- **Done when:** each rule fails its own bad fixture and passes the clean one; E20 is green; the check run on
  `workspace/site/` (the local build) fails on X1, X2, X8 and X10 as expected. Tier A review.

### Phase 3 — The builder, the redactor and the residue report
- **Owner skill:** archivist
- **What:** `tools/export_build.py` as above, run on the manifest; then the check on its output.
- **Outputs:** `tools/export_build.py` and its tests; `workspace/export/` (never in git); the residue report's counts
  per rule and per page, written into this plan's log.
- **Done when:** the build refuses a path outside `workspace/export/`, runs no illustration tool, and makes no
  network request; for scope (a) the check is green; for scope (b) or (c) the log holds the residue counts per rule and
  per page. Tier B check.

### Phase 4 — The residue and the export-only pages
- **Owner skill:** spec-writer
- **What:** write the three export-only pages; then, for scope (b) or (c), fix the residue at its source: move
  evidence that sits in spec prose into the evidence parenthetical, so the redactor removes it. No statement changes
  its meaning or its tag. Batches by subsystem, about 300 residue lines each; the count follows Phase 3's report. Add
  the habit to the spec-writer's pseudocode conventions: prose states behaviour, evidence goes in the parenthetical.
- **Outputs:** `docs/export/*.md`; edits to `docs/specs/`; `.claude/skills/spec-writer/references/pseudocode-conventions.md`.
- **Done when:** the check is green on a fresh cut; the gate is green; each batch's Tier A review accepts.

### Phase 5 — The redaction review
- **Owner skill:** architect
- **What:** the Tier A redaction review above, on a fresh cut.
- **Done when:** a verdict is recorded in this plan's log with the cut date, the check's output and the sample read.

### Phase 6 — The owner's read, the host, the publish
- **Owner skill:** human
- **What:** the owner reads the cut, picks a host, creates its account, copies the cut and publishes.
- **Done when:** the owner says so. No agent takes part in this phase beyond answering questions.

## Cost estimate

From the ledger's means (`python3 -I tools/metrics.py summary`, 782 runs): archivist 167 k tokens a run,
spec-writer 244 k, architect review 163 k, architect check 87 k, architect 146 k.

| Phase | Lanes | Estimate |
|---|---|---|
| 1 manifest | architect | 0.15 M |
| 2 check | archivist, Tier A review | 0.25 M + 0.17 M |
| 3 builder | archivist, Tier B check | 0.30 M + 0.09 M |
| 4 pages, scope (a) | spec-writer, 1 batch, Tier A | 0.25 M + 0.17 M |
| 4 residue, scope (b) | spec-writer, 4 to 8 batches, Tier A each | 1.0 M to 2.0 M + 0.65 M to 1.3 M |
| 5 review | architect, Tier A | 0.25 M |
| **Total, scope (a)** | 6 runs | **about 1.6 M** |
| **Total, scope (b)** | 10 to 18 runs | **about 2.9 M to 4.5 M** |

No harness slot and no Ghidra. Scope (c) adds a Phase 4 batch or two for formats and tables, about 0.4 M to 0.8 M.

**Maintenance.** A re-cut is two commands (build, check) and costs no lane while the check stays green. The
Phase 4 convention keeps it green: a spec lane that writes evidence into prose turns the next cut red. A red cut
costs one small spec-writer fix (0.1 M to 0.25 M) and a Tier B check (0.09 M). Each cut the owner publishes takes a
Phase 5 review of what changed since the last published cut (about 0.15 M) and the owner's read. Proposed cadence:
a cut on the owner's request, not on every merge (question 5).

## Risks

- **This is not legal advice.** ADR-0009 says so, and it holds here. The redaction lowers each of the five risks; it
  removes none. Certainty takes a lawyer in the owner's jurisdiction.
- **The evidence stays public in the working repository.** The owner keeps the repository public. So `docs/findings/`
  (code-shaped listings) and `re/` (the binary's symbol map) stay reachable on GitHub, whatever the export redacts.
  The export's redaction narrows what the *export* exposes and what it leads to. It does not narrow what is already
  public, and someone who connects the two by content can see both.
- **The export shows the game was studied closely.** Exact call order and integer rules say so on their own. Removing
  method words and anchors lowers the signal; it can't hide it.
- **Readers can't follow the evidence.** Without anchors, a `[C]` is our word. "How to read the tags" says so. A
  reader with their own copy can check behaviour, not our sources.
- **Drift.** The export is a cut of a date. Specs change after it. The front page names the cut date, and a stale cut
  is only re-cut on request. A reader of an old cut sees old statements.
- **A redactor that drops too much.** Dropping a parenthetical whose prose mattered would lose meaning silently. The
  redactor drops only parentheticals made entirely of evidence tokens, and Phase 5 reads the most-redacted page.
- **A check that passes too much.** The check is pattern-based. A leak it has no pattern for passes. The Tier A review
  and the owner's read are the second and third line.

## Questions for the owner

1. **Scope.** (a) wiki and glossary; (b) **recommended**: (a) first, then the redacted specs as a second cut; (c)
   (b) plus file formats and table schemas.
2. **Tags.** Keep `[C]`/`[I]` without anchors (**recommended**), or drop them.
3. **Host.** One of the four options above, or none yet (the plan can run to Phase 5 without a host).
4. **The "no tie" rule.** ADR-0009 bars any link from the export to this repository. With the repository public by
   the owner's choice, a link would let readers follow the evidence. Keep the rule (**recommended**: a link makes the
   export a front door to `findings/` and `re/`, and changing the rule takes a superseding ADR), or revisit it.
5. **Licence and cadence.** A licence for our text in the export (CC BY 4.0, CC BY-SA 4.0, or none stated), and how
   often to re-cut (on request is recommended).

**Decided, not asked.** The working repository stays public (owner, 2026-11-16: "working repo should stay public, I
think risk is rather small"). This plan does not revisit it.

## Open questions

- The `+0x` offsets in `docs/formats/` describe file layouts, not the binary's memory. Scope (c) may need X1 to
  allow them on format pages only. Decided in Phase 1 if (c) is chosen.
- Whether a spec's sentence can always shed its evidence without rewording. Phase 3's residue report answers it; a
  spec that can't is left out of the manifest, not rewritten for the export.

## Implementation log

_(lanes append dated entries as phases land)_
