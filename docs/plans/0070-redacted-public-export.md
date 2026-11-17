# 0070 — The redacted public export: what leaves the machine, how it is redacted, and the check that guards it (ADR-0009, ADR-0035)

> **Status:** in progress: Phase 1 done 2026-11-16; re-cut 2026-11-16 for three later owner decisions (simplification,
> schematic illustrations per ADR-0036, the cheapest residue option); approved (owner, 2026-11-16: "1 b / 2 keep / 3 github pages, similar to @../Ritmolux/ documentation /
> 4 yes / 5 go as recommended"; the account: "My account, like Ritmolux"; hosting recorded in ADR-0035)
> **Created:** 2026-11-16
> **Owner skill(s):** architect, archivist, spec-writer, human
> **Related ADRs:** 0009-public-documentation-site, 0035-public-export-hosting, 0036-schematic-illustrations-in-the-export, 0034-local-documentation-site, 0012-human-wiki, 0031-constants-of-the-code-image, 0005-presentation-formats-tools-only, 0006-docs-gate

## TL;DR

**Question:** what can be put online, how is it redacted, and what stops a mistake from leaving the machine? On
2026-11-16 the owner asked why we can't publish when fan sites publish similar material, and asked for this plan.
[ADR-0009](../adrs/0009-public-documentation-site.md) already gives the answer's shape: a separate, heavily redacted
export, behind a mechanical publish check, published by the owner. ADR-0009 leaves three things to "the plan that
builds the export": the redaction depth, the check, and the footer. This plan sets them. The owner approved it on
2026-11-16. [ADR-0035](../adrs/0035-public-export-hosting.md) records the host: a separate repository under the
owner's GitHub account, an Astro Starlight site on GitHub Pages. When it is done:

- an allowlist names every page the export holds;
- `tools/export_build.py` cuts the export into `workspace/export/` from that allowlist, with the redaction applied, as
  a Markdown tree shaped for Starlight's content collection;
- the export repository's files (the Starlight project, the workflow, README, LICENSE) are prepared under
  `workspace/export-repo/`;
- the cut carries the pages' Mermaid diagrams and their animations, drawn in a schematic mode with our own graphics
  only ([ADR-0036](../adrs/0036-schematic-illustrations-in-the-export.md));
- the redactor may simplify: it drops a sentence, bullet, row or section it can't clean, and logs each drop;
- `tools/export_check.py` is green on the cut and on those files, and its self-tests are a gate rule;
- the architect has reviewed the cut at Tier A, and the owner has read it;
- the owner, and only the owner, creates the export repository, enables Pages and pushes.

Two cuts: the wiki and the glossary first, then the redacted specs.

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
  same state. Its rule that the export carries **no tie to the repository** stands, relaxed by
  [ADR-0035](../adrs/0035-public-export-hosting.md) for the owner's account and name only.
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

## The owner's decisions (2026-11-16)

The owner answered the five questions on 2026-11-16, verbatim: "1 b / 2 keep / 3 github pages, similar to
@../Ritmolux/ documentation / 4 yes / 5 go as recommended". Asked which GitHub account owns the export repository:
"My account, like Ritmolux".

| # | Question | Answer |
|---|---|---|
| 1 | Scope | (b): the wiki and the glossary as the first cut, then the redacted specs as a second cut. |
| 2 | Tags | Keep `[C]`/`[I]`, without anchors. |
| 3 | Host | GitHub Pages, set up like the owner's other documentation site: an Astro Starlight site, a build job with a link check on every push and pull request, a deploy job from `main` only, Mermaid drawn at build time in CI, the base path the repository's name, deployments that queue and never cancel. |
| 4 | The no-tie rule | Keep it. The owner then chose their own account, so ADR-0035 relaxes the rule for the owner's account and name only. Everything else of it stands: no link to the working repository, no repository paths, no finding or run ids, no commit hashes. |
| 5 | Licence and cadence | As recommended: a cut on the owner's request. The plan gave no licence recommendation; the orchestrator chose CC BY 4.0 for our text, in the export repository's LICENSE. The owner may change it before the first push. |

The working repository stays public (owner, 2026-11-16). ADR-0035 holds the hosting decision; this plan holds the
redaction, the check and the phases.

**Three later decisions (owner, 2026-11-16).** They re-cut the phases and the cost; see the log.

| # | Question | Answer |
|---|---|---|
| 6 | May the export simplify? | Yes. Owner, verbatim: "for public export simplifications are fine btw, but diagrams and animations are needed". The redactor may drop whole sentences, bullets, table rows or sections that fail the check. It logs every drop in its report. The spec residue batches (old Phase 8) are gone; the second cut's review reads what was dropped. |
| 7 | How are the animations drawn? | "Schematic" (owner's choice). Our own graphics only: maze rooms as labelled boxes with doors and entry and exit marks, drops as item name cards coloured by quality. No tiles, no icons, no game palette. [ADR-0036](../adrs/0036-schematic-illustrations-in-the-export.md) records it. |
| 8 | Phase 1's residue decision | Owner, verbatim: "yes go with cheapest option". No residue batch. X9 is narrowed to tool names; *emulation* and *emulated* pass as plain words, and *breakpoint* passes as a game term. X2 matches `run:` only in its id form. The simplifier drops what is left: the glossary's offsets, `sub_` names and ADR, plan and finding references, and the Battle.net lines of the characters page. |

## The design (approved 2026-11-16)

### Scope: an allowlist, not a denylist

The export holds only the pages an allowlist names, `docs/export/manifest.txt` (one docs-relative path per line;
architect-owned). A page reaches the export only by being named. Three scopes were offered (question 1); the owner chose (b):

| Scope | Holds | Notes |
|---|---|---|
| (a) | `docs/wiki/` (except `how-we-know.md`), `docs/glossary.md`, the export-only pages | Smallest. The wiki is already free of tags, anchors and addresses. The wiki's links into specs become plain text. |
| (b) **chosen** | (a), then the reviewed specs under `docs/specs/<subsystem>/` | The deliverable itself. It needs the redactor and its simplifier. Cut (a) first; add (b) as a second cut once its check is green. |
| (c) | (b), plus `docs/formats/` and the column-schema pages of `docs/tables/` | File formats are the strongest interoperability case. Table pages listing constants of the code image ([ADR-0031](../adrs/0031-constants-of-the-code-image.md): `PathDirTables`, `ActClockTables`) stay out. |

**Excluded outright, in every scope:** `docs/findings/` (decompile-shaped listings), `re/` (the binary's symbol and
struct map), `docs/plans/`, `docs/adrs/`, `docs/backlog/` and `docs/backlog.md`, `docs/sources.md` (other people's
text), `docs/inventory.md` (file hashes and sizes), `docs/specs/README.md` (the research map, which is about the
repository; the export gets its own index), `docs/wiki/how-we-know.md` (the method page), every game-art illustration and every
file of game art (schematic illustrations may enter, ADR-0036), and every *Open questions* section (it holds the `[L]` leads and the `src:` ids).

### Redaction depth, per ADR-0009's five risks

| Risk (ADR-0009) | Content | Proposal | Why |
|---|---|---|---|
| (1) contract, anti-circumvention | Addresses `0x00XXXXXX`, `sub_XXXXXXXX` names, in-memory `+0x` offsets | **Removed**, everywhere. A name with an address in it (`sub_00556F60_ItemRollQualityCreate`) loses the prefix or is dropped. | They tie each sentence to a place in the binary. A reimplementer does not need them; a verifier does, and the export can't serve verifiers (*Risks*). |
| (1) | `fn:`/`data:`/`struct:`/`tbl:` anchors, `run:` ids, finding ids and links, plan, ADR, backlog and lane names | **Removed.** Evidence parentheticals made only of these are dropped whole. A table column made only of them is dropped. | ADR-0009: no finding ids, no paths, no tie. |
| (1) | Method words, narrowed to tool names (decision 8): Ghidra, gdb, decompile, decompiler, disassembler, disassembly, harness, logger, "logged run" | **Removed from the export text.** The check fails on them. The simplifier drops a sentence that holds one. *Emulation*, *emulated* and *breakpoint* (a game term) pass as plain words. | The export describes the game, not how we read it. It still shows that someone studied the game closely; that can't be redacted away (*Risks*). |
| (1) | Copy protection, CD key, Battle.net authentication, Warden | **Never present.** The simplifier drops any sentence, bullet or row that mentions one, the one-line "out of scope" notes and the characters page's Battle.net menu lines included. The check still fails on any mention left. | ADR-0009's standing ban, made mechanical for the export. |
| (2) code-shaped excerpts | Our pseudocode | **Kept**, inside a line the check enforces (below). | It is our own notation, language-neutral, numbered steps and our names. It describes a method, which copyright does not cover. |
| (2) | Anything decompiler-like | **Never present.** Findings are out; the check also scans specs' blocks. | ADR-0009 risk 2. |
| (2) | Mermaid diagrams | **Kept** as fences, drawn at build time by the export repository's CI (ADR-0035). The check scans their text like any other. | They are ours and illustrate only. |
| (2), (3) | Animated illustrations | **Kept in schematic mode only** (ADR-0036): the generator's `--schematic` output, marked and listed. Game-art output never. Captions and calculation text pass the check like page text. | Owner, decision 6: "diagrams and animations are needed". The art is the only part that is the game's. |
| (3) data | Tables | **Kept only** when 20 body rows or fewer, schema and short illustrative rows. Our own tables over 20 rows (a step list, a decision table) pass only when the manifest names them with a reason, reviewed in Phases 6 and 9. | ADR-0009: a full table is more exposed than its schema; EU database right. |
| (3) | Item, monster, level and skill names; item codes | **Kept** where a statement needs them to name a row. | Naming a thing is nominative and factual. |
| (3) | Flavour text, quest dialogue, string-table text, rows of `.tbl` strings | **Never present.** The check flags quoted runs over 12 words for review; the redaction review reads them. | Creative expression. |
| (3) | Constants of the code image (ADR-0031 listed values) | **Excluded** with their pages; a listed value quoted in a spec is removed with its address. | They are the binary's data, published only as needed in the working docs. |
| (4) trademarks | "Diablo II", "Lord of Destruction", "Blizzard" | **Nominative only**: to name the game and in the footer. No logo, no game art, no Blizzard styling, no domain or site name that uses a mark. | ADR-0009 risk 4. |
| (5) third-party text | `src:` ids, quoted community claims | **Removed** with *Open questions* and with the evidence parentheticals. | Other people's writing, under their terms. |
| (all) | Evidence tags `[C]`/`[I]` | **Kept** (question 2, owner, 2026-11-16). `[L]` never reaches the export (it lives only under *Open questions*). An export-only page says what the two tags mean, in plain words, without naming the method. | The tags are our own claims about our own confidence. They tell a reimplementer where to be careful, and they cost no tie: without anchors they point at nothing. Dropping them would present inferred statements as certain. |

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

- **Builder.** A new `tools/export_build.py`, standard library only, `python3 -I`. It does not render HTML: the
  export repository's CI does that (ADR-0035). It reads the manifest and writes a Markdown tree into
  `workspace/export/` only (refusing any other path, as `site_build.py` does), laid out at the export repository's
  paths: `site/src/content/docs/<route>.md` per page and `site/src/cut.json` (the cut date). Each page gets Starlight
  frontmatter: `title` from its first `# ` heading, which the builder then removes (Starlight draws the title as the
  page heading), and `sidebar.order` from the manifest. The manifest's group becomes the route's folder, so the
  sidebar groups follow it. It keeps ```` ```mermaid ```` fences as they are; CI draws them. It runs each
  ```` ```illustration ```` block of a named page with its `tool` in `--schematic` mode only, into
  `site/public/illustrations/<id>/` (the GIF, the frames, the step-through page, the tool's file list), and replaces
  the block with the GIF, a link to the step-through page and the block's caption. A block whose tool has no schematic
  mode is dropped. It also writes a report, `workspace/export/report.txt`, outside `site/`: every drop and every
  residue item.
- **Redactor.** A pass over each page's Markdown, in this order: drop *Open questions* sections; drop evidence
  parentheticals made only of anchors, run ids, addresses and finding links; drop anchor-only table columns; strip the
  address column from pseudocode lines, keeping the tag; strip `sub_XXXXXXXX_` prefixes.
- **Simplifier** (decision 6). After the redactor, it runs the check's text rules (X1 to X5, X9) on each unit of the
  page and drops a unit that fails. A unit is the smallest of: a sentence of a paragraph, a list item, a table row, a
  fenced block. A section goes when its heading fails or nothing is left under it; a paragraph goes when no sentence is
  left. It never rewrites a word inside a unit it keeps. Each drop is a report line: the page, the heading, the rule,
  and the dropped text. What it can't split cleanly it leaves, and the check reports it.
- **Link rewriter.** A link to a page in the manifest becomes a link to that page's route, written relative to the
  linking page's route, so the cut does not depend on the base path (heading anchors kept when the heading exists
  there). Any other link keeps its text and loses its target. No link leaves the export: no working-repository URL, no
  path into `docs/`, `re/` or `tools/`. The export repository's CI link check catches a route the rewriter got wrong.
- **Export-only pages**, in `docs/export/` (spec-writer, reviewed like a wiki page): the front page (what the
  project is, what is in the export, how to read it), "How to read the tags" and the about page that carries the
  footer's statements and the licence. They make no claim of their own about the game.
- **The export repository's files**, prepared once under `workspace/export-repo/` for the owner to push (ADR-0035):

  | Path | Holds |
  |---|---|
  | `site/package.json` | Astro, `@astrojs/starlight`, `rehype-mermaid`, `playwright`: exact versions, no ranges, as in the owner's other site. No lockfile: the owner's first `npm install` makes it, and it is committed. |
  | `site/astro.config.mjs` | `site` the owner's `github.io` host, `base` from `SITE_BASE` (the repository's name as spelled); Starlight with the sidebar groups, the footer override, one GitHub link to the export repository itself; `rehype-mermaid` with the `img-svg` strategy, so a fence that does not parse fails the build; a hook that fails the build on a page that rendered to an empty body. |
  | `site/src/content.config.ts` | The docs collection. |
  | `site/src/components/Footer.astro` | ADR-0009's footer, word for word, with the cut date read from `site/src/cut.json`. |
  | `site/scripts/check-site-links.mjs` | The link check over `dist/`: every internal link resolves under the base path; an external link outside a short allowlist (the export repository, the licence's page) fails. Node standard library only. |
  | `.github/workflows/pages.yml` | Modelled on the other site's: `build` on every push, pull request and manual run (Node, `npm ci`, the Playwright browser cached by version, `npm run build`, the link check, the Pages artifact); `deploy` only from `main`, with `pages: write` and `id-token: write`; `concurrency` group `pages`, `cancel-in-progress: false`; `SITE_BASE` set once and given to both the build and the check. |
  | `README.md`, `LICENSE`, `.gitignore` | What the site is, how to build it; CC BY 4.0 for our text; `node_modules/`, `dist/`. |

  After the first push the export repository is the files' home. A later change to them is the owner's, or a lane
  prepares it under `workspace/export-repo/` again and the owner applies it.
- **Publish check**, `tools/export_check.py <cut-dir> [--repo <export-repo-dir>]`. Read-only, standard library. It
  must be green before anything is copied to the export repository. It scans the redacted Markdown and, with `--repo`,
  the export repository's files. Starlight's built HTML carries its own scripts, so the check does not scan the build;
  the export repository's CI is the second guard (ADR-0035).

  | Rule | Fails on |
  |---|---|
  | X1 | an address `0x00XXXXXX`, any other hex of 6 digits or more, `sub_XXXXXXXX`, a `+0x` offset |
  | X2 | an anchor `fn:`, `data:`, `struct:`, `tbl:`, `src:`; `run:` only in its id form (followed by an id character, not a space or the end of a line) |
  | X3 | a repository reference: `findings/`, a finding id shape (`items/0002`), `ADR-NNNN`, `plan NNNN`, `lane/`, `docs/`, `re/`, `tools/`, `workspace/`, a `.py` or `.csv` name, a commit hash |
  | X4 | an identity string: the working repository's name and remote URL (read from git at run time, never stored), the git `user.email` of the machine, `/home/` or any absolute path. The owner's name and account pass (ADR-0035). |
  | X5 | a decompiler-like fenced block (the pseudocode line above); ```` ```mermaid ```` fences are exempt from X5 only |
  | X6 | a table over 20 body rows that the manifest does not name |
  | X7 | in the cut: any `http:` or `https:` link, raw HTML (`<script>`, `<iframe>`, `<link>`, `<style>`), `@import`, `url(`. In the repository files: a URL outside the allowlist (the owner's `github.io` host, the export repository, the licence's page, the npm registry in the lockfile), an action outside `actions/*` |
  | X8 | any image: a Markdown image, `<img>`, an image file of any type, `<video>`. The one exception (ADR-0036): a Markdown image or link whose target is a file under `illustrations/<id>/` that X11 allows |
  | X9 | the banned topics (copy protection, CD key, Battle.net in any form, Warden) and the tool names: Ghidra, gdb, decompile, decompiler, disassembler, disassembly, harness, logger, "logged run". *Emulation*, *emulated* and *breakpoint* pass |
  | X10 | a footer component that differs from the footer word for word, or is not registered in the config; a `cut.json` without a date |
  | X11 | in the cut, a file other than `.md`, `cut.json` and the schematic allowlist; in the repository files, a path outside the table above (plus the lockfile); a `.git` directory anywhere. **The schematic allowlist** (ADR-0036): under `site/public/illustrations/<id>/` only, a `.gif`, `.png`, `index.html` or `steps.json` that carries the schematic marker and whose sha256 matches the folder's `schematic.json` (written by the tool in schematic mode only); no other file in the folder; the HTML is the generator's template, with no URL, no `src` outside its folder, and no request. The X7 bar on raw HTML and scripts covers every other file of the cut |
  | X12 (warning) | a quoted run over 12 words, a capitalised name that matches no row name of the manifest pages' tables (a possible string-table leak); read in the review |

- **Gate.** One new rule, E20: `python3 -I tools/test_export_check.py` passes (fixtures in
  `tools/gate/fixtures/export/`, one bad case per rule and one clean cut). The gate does not run the check on
  `docs/`. The working docs keep their full evidence; only the cut must be clean.

### Review

- **Phase 2's check** is a safety device, so its lane takes **Tier A**, not the archivist's usual Tier B.
- **Each cut** takes a **Tier A redaction review** (Phases 6 and 9): the architect runs the check, reads the manifest
  and every X6 and X12 item, and reads a sample in full. For the first cut: every export-only page, five wiki pages,
  the glossary, and every file under `workspace/export-repo/`. For the second: six specs (rng, items/tc,
  items/quality, monsters/spawn, drlg/maze and the page with the most redactions by the report). For each of the
  five risks it greps the cut once more by hand. A verdict of reject sends the cut back to the phase that made it.
- **The owner's read** comes before each push (Phases 7 and 10). The owner reads as much as they choose, and decides.

### Hosting (ADR-0035)

A separate repository under the owner's GitHub account, `<account>.github.io/<repository>/`. Its name is neutral:
not the working repository's name, and no trademark. It holds the cut, the Starlight project and the workflow,
nothing else. Each cut is copied in from `workspace/export/` by hand, never cloned or merged from this repository.
The owner's name may show where the host puts it; nothing links to the working repository.

## Phases

The first cut (wiki, glossary, export-only pages, their diagrams and schematic animations) is Phases 1 to 7. The
second cut (the specs) is Phases 9 and 10; Phase 8 is replaced by the simplifier (decision 6). Re-cut 2026-11-16 (see
the log): Phase 2 takes the narrowed rules, Phase 2b is new, Phase 3 adds the simplifier and the schematic run.

**Order.** Phases 2, 2b, 4 and 5 can run side by side now. Phase 3 needs 2 and 2b. Phase 6 needs 3, 4 and 5.

### Phase 0 — The owner's approval and answers
- **Owner skill:** human
- **What:** approve or abandon this plan; answer questions 1 to 5.
- **Done when:** this plan's status is `approved` with the answers recorded, or `abandoned`. **Done 2026-11-16.**

### Phase 1 — The manifest
- **Owner skill:** architect
- **What:** write `docs/export/manifest.txt` for the first cut: one line per page, its docs-relative path, its
  sidebar group and its order. The wiki (except `how-we-know.md`), the glossary, and the three export-only pages of
  Phase 5. A reason line for each table over 20 rows allowed in advance (expected none).
- **Outputs:** `docs/export/manifest.txt`; this plan's log.
- **Done when:** every path in it exists, except the three `docs/export/` pages Phase 5 writes; none is in an excluded
  tree; the gate is green. **Done 2026-11-16.**

### Phase 2 — The publish check
- **Owner skill:** archivist
- **What:** `tools/export_check.py` with rules X1 to X12, its self-tests and gate rule E20. X9 holds the tool names
  only; X2 matches `run:` only in its id form; X8 and X11 allow the schematic allowlist (ADR-0036) and nothing else.
  The check exposes its text rules (X1 to X5, X9) as a function the builder's simplifier calls on one unit of text.
- **Outputs:** `tools/export_check.py`, `tools/test_export_check.py`, `tools/gate/fixtures/export/`, `tools/gate.py`
  (E20 only).
- **Done when:** each rule fails its own bad fixture and passes the clean one; E20 is green; the check run on an
  unredacted copy of three specs fails on X1, X2 and X3 as expected. Fixtures also show: "emulated" and "attack-speed
  breakpoint" pass X9, "not confirmed by a run:" passes X2, a Battle.net menu line fails X9; a schematic folder whose
  files match its `schematic.json` passes, and each of these fails: a file with no marker, a hash mismatch, an extra
  file in the folder, an image outside an illustration folder, an `index.html` with an external URL. Tier A review.

### Phase 2b — Schematic mode for the illustration tools
- **Owner skill:** archivist
- **What:** a `--schematic` mode in `tools/maze_anim.py` and `tools/tc_anim.py` (ADR-0036). The maze: rooms as
  labelled boxes, their doors, the entry and exit marks; no tiles, no DS1 floor or wall layout. The drop: each item as
  a name card coloured by its quality; no icons. Our own fixed palette and the 5×7 font of `anim_common.py`. The same
  steps, calculation panels, captions and "How to read this" lines as the full mode. In schematic mode only, each
  output file carries a marker (a PNG text chunk, a GIF comment, an HTML meta line, a `steps.json` key) and the tool
  writes `schematic.json` (the tool, its arguments, each file's name and sha256). The full mode never writes the marker.
- **Outputs:** the two tools, `tools/anim_common.py` as needed, their tests.
- **Done when:** both tools run in schematic mode on the two illustration blocks of the wiki (`levels.md`,
  `items.md`); a test runs each in schematic mode with the art decoders (`ds1` tile layers, `dt1`, `dc6`, `item_art`,
  `palette`, `maze_render`) blocked from import and from opening files, and it succeeds; the step lists (`steps.json`
  text and calc) of the schematic and full modes are equal for the same arguments; Phase 2's check passes the output
  folder. Tier A review (it draws the line between game art and our own drawing).

### Phase 3 — The builder, the redactor, the simplifier and the report
- **Owner skill:** archivist
- **What:** `tools/export_build.py` as above: the redactor, the simplifier (calling Phase 2's text rules), the link
  rewriter, and the illustration run in schematic mode (Phase 2b). Run it on the first-cut manifest, then the check on
  its output. Run it once more on a trial manifest that adds every reviewed spec, for the drop and residue counts.
- **Outputs:** `tools/export_build.py` and its tests; `workspace/export/` (never in git); the trial's drop and residue
  counts per rule and per page, written into this plan's log.
- **Done when:** the build refuses a path outside `workspace/export/`, runs an illustration tool only with
  `--schematic`, and makes no network request; every page has a `title` and a `sidebar.order`; every drop is a report
  line (page, heading, rule, text); the two wiki illustrations reach `site/public/illustrations/<id>/` with their
  caption on the page; the check is green on the first cut, apart from the export-only pages if Phase 5 has not
  landed; the log holds the trial's counts, with each page's share of dropped sentences. Tier B check.

### Phase 4 — The export repository's files
- **Owner skill:** archivist
- **What:** write the files of the table above under `workspace/export-repo/`, modelled on the owner's other site
  (read it, never change it). Exact version pins. No `npm` run on this machine: the lane writes files only. The link
  check resolves links to `public/illustrations/` files under the base path.
- **Outputs:** `workspace/export-repo/` (never in git); the file list and the pinned versions in this plan's log.
- **Done when:** `tools/export_check.py --repo workspace/export-repo/` is green; the workflow has the two jobs, the
  build on pull requests, the deploy from `main` only, and `cancel-in-progress: false`; the footer component matches
  the footer word for word. Tier B check; Phase 6 reads every file.

### Phase 5 — The export-only pages
- **Owner skill:** spec-writer
- **What:** write the front page, "How to read the tags" and the about page in `docs/export/`. The about page says the
  animations are schematic drawings of our own, and that the export simplifies.
- **Outputs:** `docs/export/*.md`.
- **Done when:** the gate is green; the check is green on a cut that holds them; Tier A review accepts.

### Phase 6 — The first cut's redaction review
- **Owner skill:** architect
- **What:** the Tier A redaction review above, on a fresh first cut and on `workspace/export-repo/`. It also reads
  every drop line of the report, and looks at every schematic illustration (each GIF and its step-through page).
- **Done when:** a verdict is recorded in this plan's log with the cut date, the check's output, the sample read, the
  number of drops read and the illustrations seen.

### Phase 7 — The owner's read and the first publish
- **Owner skill:** human
- **What:** the owner reads the cut, creates the export repository under their account, sets Pages' source to GitHub
  Actions, copies `workspace/export-repo/` and `workspace/export/site/` into a fresh folder, runs `npm install` once
  to make the lockfile, and pushes through a pull request. The CI build and link check must pass on it; the merge to
  `main` deploys.
- **Done when:** the owner says the site is served. No agent takes part beyond answering questions.

### Phase 8 — The spec residue (replaced 2026-11-16)
- **Replaced** by the simplifier (decision 6). No spec-writer batch runs. The working specs keep their evidence as
  they are; the export drops what it can't clean. No change to the spec-writer's conventions is required.

### Phase 9 — The second cut's redaction review
- **Owner skill:** architect
- **What:** add the reviewed specs to the manifest, cut afresh, and run the Tier A redaction review above. Read every
  drop line of the six sampled specs and the drop counts of every spec. A spec that loses more than a quarter of its
  sentences, or one whose remaining text no longer reads as whole, stays out of the manifest.
- **Done when:** the manifest holds the specs that pass; a verdict is recorded in this plan's log with the cut date,
  the check's output, the sample read, and each left-out spec with its reason.

### Phase 10 — The owner's read and the second publish
- **Owner skill:** human
- **What:** the owner reads the second cut, copies `workspace/export/site/src/` and `site/public/` over the export
  repository's, and pushes through a pull request; the merge deploys.
- **Done when:** the owner says so.

## Cost estimate

From the ledger's means (`python3 -I tools/metrics.py summary`, 782 runs): archivist 167 k tokens a run,
spec-writer 244 k, architect review 163 k, architect check 87 k, architect 146 k. Recomputed 2026-11-16 after
decisions 6 to 8.

| Phase | Lanes | Estimate |
|---|---|---|
| 1 manifest | architect | 0.15 M (spent) |
| 2 check | archivist, Tier A review | 0.30 M + 0.17 M |
| 2b schematic mode | archivist, Tier A review | 0.30 M + 0.17 M |
| 3 builder and simplifier | archivist, Tier B check | 0.35 M + 0.09 M |
| 4 export repository's files | archivist, Tier B check | 0.25 M + 0.09 M |
| 5 export-only pages | spec-writer, Tier A | 0.25 M + 0.17 M |
| 6 first review | architect, Tier A | 0.30 M |
| **First cut** | 12 runs | **about 2.6 M** |
| 8 spec residue | replaced | 0 |
| 9 second review | architect, Tier A | 0.30 M |
| **Second cut** | 1 run | **about 0.3 M** |
| **Total** | 13 runs | **about 2.9 M** |

The total falls from 3.9 M–5.6 M to about 2.9 M. The spec residue batches (1.65 M to 3.3 M) are gone, and no wiki
residue batch (0.42 M) is added. The first cut rises by about 0.6 M, for the schematic mode (Phase 2b) and the
simplifier. No harness slot and no Ghidra.

**Maintenance.** A re-cut is two commands (build, check), the owner's copy and a pull request. It costs no lane while
the check stays green. The simplifier keeps it green: a new sentence that carries evidence in its prose is dropped and
logged, not published. A red cut (a leak the simplifier can't split) costs one small fix (0.1 M to 0.25 M) and a Tier B
check (0.09 M). Each cut the owner publishes takes a review of what changed since the last published cut, its new
drops included (about 0.15 M), and the owner's read. Cadence: a cut on the owner's request, not on every merge (owner,
2026-11-16). Upgrading the export repository's npm pins is the owner's work there.

## Risks

- **This is not legal advice.** ADR-0009 says so, and it holds here. The redaction lowers each of the five risks; it
  removes none. Certainty takes a lawyer in the owner's jurisdiction.
- **The evidence stays public in the working repository, under the same account.** The owner keeps the repository
  public and hosts the export under the same account (ADR-0035). So `docs/findings/` (code-shaped listings) and `re/`
  (the binary's symbol map) are one profile page away from the export. The redaction narrows what the *export*
  exposes. It does not hide the connection.
- **The export shows the game was studied closely.** Exact call order and integer rules say so on their own. Removing
  method words and anchors lowers the signal; it can't hide it.
- **Readers can't follow the evidence.** Without anchors, a `[C]` is our word. "How to read the tags" says so. A
  reader with their own copy can check behaviour, not our sources.
- **Drift.** The export is a cut of a date. Specs change after it. The footer names the cut date, and a stale cut
  is only re-cut on request. A reader of an old cut sees old statements.
- **A simplifier that drops too much.** Dropping a sentence can lose a step, or leave the next sentence pointing at
  nothing ("this is why …"). Every drop is a report line, Phases 6 and 9 read them, and a spec that loses more than a
  quarter of its sentences stays out. The export is simpler than the working specs by design (decision 6); a
  reimplementer who needs the whole text will not find it there.
- **A schematic file that holds art.** The marker is the tool's own promise. Phase 2b's test blocks the art decoders,
  Phase 2b takes Tier A, and Phases 6 and 9 look at every illustration (ADR-0036 § Negative).
- **A check that passes too much.** The check is pattern-based. A leak it has no pattern for passes. The Tier A review,
  the export repository's CI and the owner's read are the next lines.
- **The check does not see the built site.** Starlight adds its own scripts and markup at build time in the export
  repository. The check here covers what we write; the CI link check covers where the built pages point.

## Questions for the owner

All five were answered on 2026-11-16; see *The owner's decisions*.

1. **Scope.** Answered: (b).
2. **Tags.** Answered: keep `[C]`/`[I]` without anchors.
3. **Host.** Answered: GitHub Pages, a Starlight site like the owner's other documentation, under the owner's account
   (ADR-0035).
4. **The "no tie" rule.** Answered: keep it; relaxed for the owner's account and name only (ADR-0035).
5. **Licence and cadence.** Answered: a cut on request; CC BY 4.0 for our text, the owner may change it.

## Open questions

- How much each spec loses to the simplifier. Phase 3's trial counts it; Phase 9 leaves out a spec that loses too much.
- The export repository's name. ADR-0035 rules it neutral; the owner picks it in Phase 7, and Phase 4 leaves it as one
  `SITE_BASE` value and one URL to fill in.

## Implementation log

- 2026-11-16 — approved by the owner (answers above); ADR-0035 records the host. Phases re-cut for a Starlight
  export: the builder writes Markdown, Phase 4 (the export repository's files) is new, the two cuts are Phases 1–7
  and 8–10. Next: Phase 1 (architect).
- 2026-11-16 — **Phase 1 done** (architect, lane/n70m). `docs/export/manifest.txt` and `docs/export/README.md` (the
  format, ownership, the exclusions as rules). The manifest's format: `group <slug> <order> <label>`,
  `page <path> <group|-> <order>`, `table <path> <header line> <reason>`; a page's route is `<group>/<file stem>`.
  Cut 1 holds 24 pages: the three export-only pages at the top level (`export/index.md`, `export/reading-the-tags.md`,
  `export/about.md`; Phase 5 writes them under these names), 20 wiki pages and the glossary, in six groups that follow
  the wiki's reading order: Foundations (randomness, game data), Building the world (levels, monsters, objects), Items
  (items, other item paths, economy, inventory), Characters and combat (characters, combat, stats and states, skills,
  saves), The running game (quests, seed to world, animation, pathing, monster AI, server frame), Reference (quirks,
  glossary). Left out besides `how-we-know.md`: `docs/wiki/README.md`, by the rule that no folder index is exported (it
  states the wiki's working rules and links ADRs and plans; the front page replaces it). No table over 20 body rows in
  any named page (the wiki README's reading-order table is the only one), so no `table` line. Every path exists but the
  three Phase 5 pages; no route repeats; gate green. *What is not known yet* sections are kept (prose, no `[L]`, no
  `src:`); front matter, *Open questions*, illustration blocks and links to pages outside the manifest go by rule.
  **What the named pages hold against the check** (counted with `grep` over the named pages, this worktree): the
  first cut will not be green on the wiki and glossary as they stand, and no phase yet fixes them (Phase 8 is the
  specs only):
  - **Method words (X9):** 218 lines say *emulation*/*emulated*/*emulator*, 20 name a tool (*harness*, *logger*,
    *logged run*, *decompile*, *disassembler*, *Ghidra*). Most in inventory (39), pathing (40), combat (33), monster AI
    (36), server frame (20), game data (15), skills (13). They are how the wiki keeps its "nothing hidden" rule (seen in
    play, confirmed under emulation, read from the code), so the redactor can't remove them without rewording.
  - **"breakpoint" is also a game term** (animation, quirks: attack-speed breakpoints, 8 lines); X9 must not fail it.
  - **X2's `run:`:** 25 wiki lines end a phrase with "run:" ("not confirmed by a run:"); X2 should match the id shape
    `run:` followed by an id character, not the word.
  - **Repository references (X3) in prose and link text:** combat and skills ("the ADR-0014 …" link text, "plan
    0052"); the glossary ("findings/rng/0001", "rng/0002" as link text, ADR-0004, ADR-0021, plan 0052).
  - **The glossary (X1):** 42 lines carry in-memory offsets (`ItemData+0x04`, `Game+0x1B24`), struct sizes in hex and
    `sub_XXXXXXXX` names in prose. It is a working glossary; the redactor will not clean it.
  - **Banned topic (X9):** characters.md lines 74–75 mention the main menu's *Battle.net* button and *Open Battle.net*
    as game types; no authentication, but the plan's rule fails any mention.
  - Cosmetic, not a check failure: each topic page's *Where to read more* names only specs, which cut 1 does not hold;
    the rewriter leaves their text without targets.
  **Needs a decision before Phase 3's green** (the orchestrator or the owner): either (a) a wiki-and-glossary residue
  batch (spec-writer, Tier A, about 0.25 M + 0.17 M), which rewords the method sentences in the working wiki (the
  wiki's own rule then reads "confirmed" or "inferred" without the method), strips the glossary's offsets and
  repository references, and words the Battle.net lines away; or (b) the same edits only in the export, which the
  design rules out (the redactor never rewrites a sentence); or (c) X9 narrowed to tool names, leaving *emulation*
  in, which keeps 218 lines but weakens risk (1)'s mitigation. Recommended: (a), as a Phase 5b beside Phase 5, and
  the two pattern points (breakpoint, `run:`) handed to Phase 2. Next: Phases 2, 4 and 5 (side by side).
- 2026-11-16 — **Re-cut for three owner decisions** (architect, lane/p70b). (6) Simplification: "for public export
  simplifications are fine btw, but diagrams and animations are needed". The redactor gains a simplifier that drops
  whole sentences, bullets, rows, blocks or sections failing the text rules and logs each drop; old Phase 8 (spec
  residue batches) is replaced, and Phase 9 reads the drops. (7) Animations: the owner chose "Schematic";
  [ADR-0036](../adrs/0036-schematic-illustrations-in-the-export.md) (accepted) lets schematic illustrations, our own
  graphics only, enter the export, and amends ADR-0034 and ADR-0035. New Phase 2b (archivist) adds `--schematic` to
  `maze_anim.py` and `tc_anim.py`; the builder runs illustration blocks in that mode only; X8 and X11 allow exactly
  the marked, hash-listed files. (8) Phase 1's residue decision: "yes go with cheapest option". No residue batch. X9
  narrowed to tool names (*emulation*, *emulated*, *breakpoint* pass); X2's `run:` only in the id form; the
  simplifier drops the glossary's offsets, `sub_` names and repository references, and the characters page's
  Battle.net lines (the Battle.net ban stays strict: the line is dropped, never published). `docs/export/README.md`
  updated to match. Cost: about 2.9 M in all (was 3.9 M–5.6 M); first cut about 2.6 M. Next: Phases 2, 2b, 4 and 5,
  side by side; then 3.
- **2026-11-16, Phase 4 (archivist, lane/x70r): files written, check not yet run.** `workspace/export-repo/` holds
  `.gitignore`, `LICENSE` (the CC BY 4.0 legal code), `README.md`, `.github/workflows/pages.yml`, `site/package.json`,
  `site/astro.config.mjs`, `site/src/content.config.ts`, `site/src/components/Footer.astro` and
  `site/scripts/check-site-links.mjs`. `site/src/cut.json`, the content and `public/illustrations/` come from the
  builder. Pinned versions, the same as the owner's other site: astro 7.3.1, @astrojs/starlight 0.42.0,
  rehype-mermaid 3.0.0, playwright 1.63.0; no lockfile, no `npm` run. The workflow has `build` (push, pull request,
  manual) and `deploy` (`main` only), `cancel-in-progress: false`, and `SITE_BASE` from the repository's name as
  spelled. Only `actions/*` actions. The config reads the cut's date and, optionally, `groups` (`[{slug, label}]`, in
  sidebar order) from `site/src/cut.json`: Phase 3's builder should write them. The link check resolves every `href` and
  `src` under the base (illustration files and their step-through pages included), and fails on an external link
  outside this repository and the licence's page. A smoke test on a scratch `dist/` found the broken, off-base and
  external cases. Not done: `tools/export_check.py --repo` does not exist yet (Phase 3), so that done-when item is open.
  The licence text holds other creativecommons.org URLs; X7's allowlist needs to cover `LICENSE`.
