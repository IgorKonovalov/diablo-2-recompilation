# 0070 — The redacted public export: what leaves the machine, how it is redacted, and the check that guards it (ADR-0009, ADR-0035)

> **Status:** in progress: Phase 1 done 2026-11-16; Phases 2, 2b, 3, 4 and 5 done 2026-11-17; re-cut 2026-11-16 for three later owner decisions (simplification,
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
  output file carries a marker (a PNG text chunk, a GIF comment, an HTML comment (the check bars `<meta`; amended at the Phase 2b review), a `steps.json` key) and the tool
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
  landed; the log holds the trial's counts, with each page's share of dropped sentences. Tier B check. **Done
  2026-11-17** (Tier A review, accept with fixes).

### Phase 4 — The export repository's files
- **Owner skill:** archivist
- **What:** write the files of the table above under `workspace/export-repo/`, modelled on the owner's other site
  (read it, never change it). Exact version pins. No `npm` run on this machine: the lane writes files only. The link
  check resolves links to `public/illustrations/` files under the base path.
- **Outputs:** `workspace/export-repo/` (never in git); the file list and the pinned versions in this plan's log.
- **Done when:** `tools/export_check.py --repo workspace/export-repo/` is green; the workflow has the two jobs, the
  build on pull requests, the deploy from `main` only, and `cancel-in-progress: false`; the footer component matches
  the footer word for word. Tier B check; Phase 6 reads every file. **Done 2026-11-17.**

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
- **Before the cut (Phase 3 review, 2026-11-17).** The archivist adds one redactor rule first, so that rows and bullets
  carrying an anchor are rewritten, not dropped (the trial dropped 44% of the specs' units, mostly for that): inside any
  unit, `fn:Name@0x…`, `data:Name@0x…` and `tbl:Name` become `` `Name` `` when `Name` itself holds no hex, `sub_` or
  `DAT_`; a `struct:Name+0x…` token, a `run:` id, a finding id or link and a `src:` id are removed as tokens; a cell left
  empty becomes `—`; a list or parenthetical left empty goes. Every rewrite is a report line (`REWRITE`, page, heading,
  before, after), and the simplifier then runs on the rewritten unit, so a residue still drops it. The check is
  unchanged. Rerun the trial and log the new share per spec before Phase 9 starts. Tier B check.
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
- 2026-11-17 — **Phase 5 written** (spec-writer, lane/x70p). `docs/export/index.md` (front page: the project, what
  the site holds and that it is simplified, where to start, the six manifest groups as links to their 22 pages),
  `docs/export/reading-the-tags.md` (`[C]` and `[I]` with the wiki's words for each, the corroboration kinds in plain
  words without a tool name, leads left out, *What is not known yet* kept, diagrams untagged) and
  `docs/export/about.md` (the footer's statements, the simplified edition, the animations as schematic drawings of our
  own per ADR-0036, CC BY 4.0). No claim about the game; no owner name in the text (ADR-0035: only where the host puts
  it); no repository name. `tools/export_check.py` was not on main, so X1–X12 were self-checked against the rules'
  text with a regex pass: clean (no fence, no table over 20 rows, no quoted run over 12 words). Found on the way: the
  wiki's game-data title "Game data: tables, …" matches X2's `data:` as the rule is written; the front page's link
  text avoids it, but the wiki page's title will hit it in the cut (Phase 2 or 3 to decide: narrow X2's `data:` to the
  id form, or let the simplifier handle the title). Gate full green. Review request
  [filed](../backlog/archive/2026-11-17-spec-writer-architect-review-0070-phase5-export-pages.md) (Tier A).
- 2026-11-17 — **Phase 5 reviewed: accept with fixes (3)** (architect, Tier A, lane/x70p). All three pages read in
  full. Owner decisions, ADR-0035 (no owner name, no repository name, no path or id), ADR-0036 (schematic drawings,
  our colours, model-computed values, illustrative seeds) and the footer's statements hold; the six groups and 22 links
  match the manifest's `page` lines and resolve; nothing states where a game file came from, and nothing implies
  affiliation. X1–X12 checked by hand: clean; X12 warnings only for the nominative names (Diablo II, Lord of
  Destruction, Blizzard Entertainment, Creative Commons), accepted. The tag table matches the evidence rules' two
  levels and the four corroboration kinds without a tool name. Fixes, all in `reading-the-tags.md` (category: wording,
  claim scope): (1) "each statement says how far it can be trusted" overclaimed the wiki, which marks what is inferred
  ("nothing hidden"), now "they say it wherever a statement is only inferred"; (2) the leads bullet now allows the
  quirks page's community claims compared with the code, as our own statements; (3) the bracketed tags are said to
  belong to the specifications, not yet on the site (cut 1 holds no tag). Noted, not this phase's: X2's `data:` against
  the wiki title "Game data: …" (Phase 2 or 3). Phase 5's other *Done when* items wait: the check green on a cut that
  holds the pages (Phases 2 and 3). Lesson 11 added to the spec-writer's `review-fixes.md`.
- 2026-11-17 — **Phase 2 done** (archivist, lane/x70c; Tier A review requested in the backlog). `tools/export_check.py`
  (rules X1 to X12; `CUT_DIR`, `--repo DIR`, or both; `--manifest`, `--identity`, `--no-git-identity`),
  `tools/test_export_check.py` (75 checks), fixtures in `tools/gate/fixtures/export/`, gate rule E20 in
  `tools/gate.py` (runs the self-tests; the gate does not run the check on `docs/`). **Text rules as a function:**
  `export_check.check_text(unit, identity=None)` returns `[(rule, line, detail)]` for X1 to X5 and X9 on one unit
  (a sentence, item, row or fenced block; a fence inside the unit is tracked); `text_rules(unit)` returns the rule
  set. Both read the git identity once (cached); the builder should call `text_rules` with that default.
  **Fixtures:** `clean` (a cut with a table, mermaid, pseudocode and a verified schematic folder) and `pass-*`
  (emulated and "attack-speed breakpoint" pass X9, "not confirmed by a run:" passes X2, a 25-row table the manifest
  names passes X6, a warning-only X12 case) pass; one `X<n>-*` bad case per rule X1 to X11, including a Battle.net
  menu line (X9), and the schematic cases: no marker, hash mismatch, an extra file, no `schematic.json`, an
  `index.html` with an external URL, an `index.html` with a `src` outside its folder (all X11) and an image outside
  an illustration folder (X8). `repo/clean` and `repo/X7-*`, `X9`, `X10-*`, `X11` cover `--repo`. The `.git` directory
  cases are built at run time. The test also runs the check on an unredacted copy of three specs (rng, items, drlg
  READMEs): X1, X2 and X3 fail as required. **Late change (orchestrator, Phase 5 lane):** X2's `data:` and the other
  anchors match only when a name character follows (`data:ItemTypes`), so prose such as "Game data: tables, strings
  and formulas" passes; fixture `pass-x2-data-prose` and two unit checks.
  **Choices the review should confirm:** (1) *The schematic marker*, which Phase 2b's generators must write: the byte
  string `d2recon-schematic/1` inside every `.gif`, `.png`, `index.html` and `steps.json` of the folder;
  `schematic.json` is `{"marker": "d2recon-schematic/1", "files": {"<relative path>": "<sha256>"}}` listing every
  file but itself; frame files may sit in subfolders (`frames/f1.png`). (2) X6 matches a manifest `table` line by
  the page's route, not by line number (the redactor moves lines): a page may hold as many oversized tables as the
  manifest names for it. (3) `report.txt` at the cut root is skipped (the builder writes it there; it is never
  published). (4) In `--repo` mode X1 to X4 and X9 scan every text file but the lockfile, X5 is not applied (the
  files are not pseudocode), and any path outside the plan's table plus `site/package-lock.json` is X11, so the
  check on a repository that already holds a cut needs the cut mode on its `site/` content, not `--repo` alone.
  (5) Heuristics: X1 and X3 also flag bare hex of 6 and of 7 to 40 digits when it holds a digit and a letter a to f;
  X3's repository paths (`docs/`, `re/`, `tools/`, `workspace/`) match only when not preceded by a letter, digit or
  `/` (so the export repository's own `site/src/content/docs/` passes); X4's generic absolute path needs a leading
  space, quote or bracket; X12 is noisy by design. (6) X7 in repo mode allows `igorkonovalov.github.io`,
  `github.com/IgorKonovalov` and `github.com/${…}`, any `creativecommons.org` page, and `registry.npmjs.org` in the
  lockfile only.
  **`--repo workspace/export-repo/` result:** green, 0 failures, 0 warnings, after two rule narrowings that were
  false positives on correct text: `docs/` inside `site/src/content/docs/` (README) and `startsWith('data:')`
  (the link checker). `LICENSE`'s creativecommons.org text passes X7. Nothing for Phase 4 to fix.
- 2026-11-17 — **Phase 2 review: accept with fixes** (architect, Tier A, on lane/x70c). Each rule matches the
  design's table, and the self-tests, `--repo workspace/export-repo/` (green) and the gate were rerun. Fixes, made in
  `tools/export_check.py` with eight new self-tests (83 checks): (1) X3's repository-path narrowing exempted any `docs/`
  after a `/`, so `../../docs/plans/…` and `../docs/specs/…` passed; only `content/docs/` is exempt now, and the
  finding-id shape no longer skips a `/` before it. (2) X1 missed an address after `_` (`DAT_00556F60`, a name ending
  in an address) and a bare all-digit address; bare hex after `_` and `00[4-7]` plus five digits now fail. (3) The
  text of a schematic folder was never read: `steps.json` and `index.html` (hex colours aside) and `schematic.json`
  (hashes aside; it holds the tool's arguments) now pass X1 to X4 and X9, and every file's bytes are searched for an
  identity string or a home path; a failure is X11 for the folder. (4) X4 fails `/home/`, `/Users/` and `file:/`
  anywhere (a `file:///home/…` link passed); the lockfile now gets X4. (5) X7 in the cut fails `ftp:`, `mailto:`,
  `javascript:`, `file:/` and protocol-relative `//` targets, not only `http(s):`. (6) X9 also fails `Battle-net` and
  the tool names radare2, rizin, x64dbg, ollydbg, IDA Pro and wine (no wiki hit; *debugger*, 3 wiki lines, stays out
  of X9 per decision 8). **Rulings on the lane's choices:** (1) marker `d2recon-schematic/1` and the `schematic.json`
  shape accepted; Phase 2b must write the tool's arguments without absolute paths or `workspace/` (they now fail X3
  and X4). (2) X6 by route accepted. (3) `report.txt` skipped at the cut root only, accepted; Phase 7 copies `site/`
  only. (4) `--repo` scope accepted, with X4 on the lockfile. (5) The hex heuristics accepted as widened. (6) X7's
  allowlist of the whole `github.com/IgorKonovalov` prefix accepted for now: the working repository's remote name is
  an X4 identity string, so a link to it fails; narrow it to the export repository's name once that is chosen
  (Phase 7). X12 accepted as noise by design. The two other narrowings are safe: an anchor always has a name after
  the colon, and the link checker's `'data:'` is followed by a quote. Indented code blocks get no X5 (only X1 to X4
  and X9); findings are out of every scope, so accepted. **Dry run on the cut-1 wiki and glossary as they stand**
  (copied unredacted, front matter and *Open questions* stripped by hand as the builder will; the three Phase 5 pages
  absent): 174 failures and 318 X12 warnings (164 distinct). X1 124 (glossary 40; elsewhere 15 `sub_` names, 62 bare
  hex, mostly seeds, 7 `0x` values such as the save magic and the RNG multiplier), X3 27 (12 commit-hash shapes, all
  game seeds such as `5389700c`; 6 ADR, 3 `findings/`, 2 plan, 2 `.py`, 2 path), X9 22 (logger 13, logged run 2,
  Battle.net 2, one each of decompile, disassembler, disassembly, Ghidra, harness), X5 1 (inside an illustration
  block, which the builder replaces); X2, X4, X6, X7, X8 none. With front matter kept, X3 rose to 108. **Phase 3
  input:** the simplifier will drop every sentence holding a seed or a game-math value in hex (randomness.md's worked
  example, 17 lines), as X1 is written ("any other hex of 6 digits or more"). Whether such values may pass by a
  manifest line is a design question for the architect before Phase 6, not a check change. Next: Phases 2b, 3.
- 2026-11-17 — **Phase 2b done** (archivist, lane/x70s; review requested, Tier A). `--schematic` in `tools/maze_anim.py` and
  `tools/tc_anim.py`. Maze: rooms as labelled boxes (room number; Def and preset file index from the conversion steps
  on), green door bars on shared edges, the level's entry and exit marks on the final frame. Drop: name cards coloured
  by quality, no icon. Our palette (`SCHEM_UI` in `tools/anim_common.py`, 768-byte global palette, no `tRNS`) and the 5x7
  font. The marker is the byte string `d2recon-schematic/1` (the one Phase 2's check, lane/x70c, looks for) in every
  file: PNG `tEXt` chunk, GIF comment extension, an HTML comment, `steps.json` (an object `{"schematic_only", "steps"}`
  in schematic mode; the full mode keeps the bare list). `schematic.json` is `{"marker", "tool", "args", "files":
  {name: sha256}}`, every file but itself; args are as given, without the data root and `--out`. The full mode writes
  none of it (byte-identical PNG and GIF to before the change; test).
  - **Splits for the no-art import rule.** `maze_render.convert` and its tables moved to the new `tools/maze_conv.py`
    (`maze_render` re-exports them); `tools/drlg.py` imports `dt1` lazily (only `dt1_keys` needs it), because
    `maze_replay` imports `drlg`. `tc_anim.py` loads `dc6`, `item_art` and `palette` only inside the full mode's
    `Icons`; schematic mode takes the base names from the weapons, armor and misc tables (`Names`, same "first row of a
    code" rule as `item_art.cmd_index`). Full-mode steps differ in one calculation line only: "The tiles drawn are that
    DS1's floor and wall cells..." now also says the schematic mode draws a box (both modes print the same line).
  - **What cannot be equal, and why.** The maze's warp lines (per-room "This preset holds a warp" and the final
    frame's "Warp" lines) come from the DS1 wall layer (orientation 10/11 cells), which the schematic mode does not
    read; it shows the level's Levels Vis entry and exit marks (destination names) on the final frame without placing
    them in a room. The drop's "Inventory icon" line becomes "Name card". Every other step text and calculation is
    equal (test, 43 maze steps and 87 drop steps).
  - **The DS1 reads that stay.** The map-scan model (`convert` step 5a, `drlg.PresetUnitData.ds1`) needs a preset DS1's
    object list and its `floor0` cell values for the draw counts, so the DS1 file is opened and that one caller reads
    that layer; no drawing code reads a layer. The test enforces exactly this (a guard on the `layers` key that admits
    only that caller), together with blocked imports of `dt1`, `dc6`, `item_art`, `palette` and `maze_render`, blocked
    opens of `.dt1`, `.dc6`, `.dcc`, `.pl2` and palette folders, and blocked `ds1._Tiles`, `_scan_cells`, `ds1_files`.
    This is a narrower reading of "ds1 tile layers blocked" than the done-when's wording; the reviewer should rule on it.
  - **Fits with the check's rules** (x70c's `export_check.py`, read from lane/x70c, commit 5475952b, not merged): its
    `html_problems` bars `<meta` and a `src=` attribute-like string, so the step-through page in schematic mode has no
    `<meta>` (pure ASCII with character references; the marker is an HTML comment) and sets the frame with
    `setAttribute('src', ...)`. The plan's "HTML meta" line becomes "HTML comment". The check passes the two
    output folders below as illustration folders of a cut-shaped tree (0 failures); the done-when item "Phase 2's check
    passes the output folder" is met against that unmerged version and should be re-run after the merge.
  - **Runs** into `workspace/render/schematic/` (never git): `drlg-maze-level36/` (`maze_anim.py 36 0xc0ffee`, 43 frames,
    0.7 MB) and `items-tc-andariel-hell/` (`tc_anim.py andariel 0xc0ffee --difficulty 2 --mf 200`, 87 frames, 1.6 MB),
    the args of the two wiki illustration blocks. Test: `python3 -I tools/test_anim_schematic.py` (5 tests, about
    20 s; skipped without `workspace/merged`). Next: the architect's review; then Phase 3 can run illustration blocks.
- 2026-11-17 — **Phase 2b review** (architect, Tier A, lane/x70s): **accept with fixes 4; one done-when item open.**
  Full mode: PNG frames and GIFs byte-identical to `main` for both wiki blocks (rerun of `main`'s tools against the
  branch's full output); `index.html` and `steps.json` differ only by the intended lines (the "tiles drawn" line, the
  drop help's name-card note). No marker, no `schematic.json` in the full mode (test). Renders looked at (maze final and
  a conversion frame, the drop's last frame): boxes, door bars, cards and the 5x7 font in our palette; no game pixel.
  - **Ruling 1 (DS1 read).** Within ADR-0036: the schematic mode depicts no layout, and the DS1 file is opened only
    for its object list, which is model input (the map scan's keep/drop draws), not art. The lane's reason was off: the
    draw counts use the object list only; `floor0` is copied by `PresetUnitData.ds1` into its cache and never read on
    this path. Fix (test tightened): `ds1.parse` is admitted only from `PresetUnitData.ds1`, the `layers` key is
    hidden from the mapping (no `items`, iteration or copy reaches it) and handed only to that caller, and the
    `floor0` copy of `PresetUnitData.ds1`'s result is hidden from any caller outside `tools/drlg.py`. A probe confirmed
    each guard raises.
  - **Ruling 2 (warps).** Accepted: entry and exit by Levels Vis, not placed in a room; the help line says so. The
    steps equality exceptions (4 warp lines in the maze, 5 icon or card lines in the drop) are exactly the lines from
    the art; every step text is equal.
  - **Ruling 3 (HTML marker).** Accepted; the Phase 2b *What* now says "an HTML comment".
  - **Names on cards** (base, unique, set and affix names from the tables) are text naming a row, kept by the
    redaction-depth table's names row; fine under ADR-0036.
  - **Fixes from the merged check** (lane/x70c, merged in 2ec0152c; X11 now runs X1-X4 and X9 on the folder's text):
    `schematic.json` names the tool without `.py` (X3) and writes a hex argument in decimal (X1); the drop's captions
    and help say "our property model" and "without a model here" in place of `tools/props.py` and `tools/` (X3, both
    modes, so the steps stay equal).
  - **Open (done-when "Phase 2's check passes the output folder", not met against the merged check):** the captions'
    RNG arithmetic writes the seed, each draw's `lo` and the LCG multiplier in hex (about 300 values over the two
    folders), and X1 fails every one; X3 reads `00c0ffee` as a commit hash. Not fixed here and the check is not
    weakened. Options for the orchestrator or the owner: (a) the schematic mode writes these numbers in decimal (X1's
    risk is addresses; seeds and draws are our model's values, but the multiplier is a code-image constant, ADR-0031);
    (b) drop the hex-carrying calculation lines in schematic mode (loses the arithmetic the animation exists for);
    (c) a scoped allowance in the check. Re-run the check on both folders after the ruling and after merging `main`.
  - Ledger: architect-review, accept with fixes 4 (tests 1, tools 2, plan 1).
- 2026-11-17 — **Phase 4 reviewed: accept with fixes (3); Phase 4 done** (architect, Opus with Tier B scope, every
  file of `workspace/export-repo/` read, lane/x70r). Held: `site/package.json` pins astro 7.3.1, @astrojs/starlight
  0.42.0, rehype-mermaid 3.0.0 and playwright 1.63.0 exactly, the owner's other site's versions; no lockfile and no
  `node_modules/`. The workflow has `build` on every push, pull request and manual run and `deploy` gated on
  `refs/heads/main` with `pages: write` and `id-token: write`; `concurrency` group `pages`, `cancel-in-progress:
  false`; `SITE_BASE` set once from the repository's name and seen by the build and the link check; only `actions/*`
  (checkout, setup-node, cache, upload-pages-artifact, deploy-pages). `Footer.astro` matches the plan's footer word
  for word with the date from `cut.json`, and is registered in the config. `LICENSE` is the CC BY 4.0 legal code
  (all eight sections and the closing notice; no reference copy offline to hash against). The README says nothing of
  where game files come from, implies no affiliation (it carries the disclaimer), and names no game file or tool of
  ours; the only identity is the owner's GitHub account in the config's host and repository link (ADR-0035).
  **Fixes, made in `workspace/export-repo/`** (category: tools correctness; originals kept in the review's scratch):
  (1) `site/astro.config.mjs`, the empty-page hook: it took the text from the content container to `</main>`, which
  holds Starlight's pagination and our footer, so no page could ever read empty and a Mermaid fence that does not
  parse (Astro stores the entry without HTML; rehype-mermaid's throw does not stop the build) would publish a title
  over nothing; it also failed every page without the container. It now fails a page whose container closes on
  itself and skips a page without one, as the other site's hook does. (2) `site/scripts/check-site-links.mjs`:
  Starlight writes each page's canonical link as an absolute URL on the site's own host
  (`https://igorkonovalov.github.io/<base>/…`; seen in the other site's build), which the allowlist failed, so the
  first CI build would have been red on every page; a link on the own host is now resolved as an internal link under
  the base (a missing page or another base still fails). (3) The same script: a relative link climbing above the
  site root now fails instead of resolving against files outside `dist/`. Smoke test on a scratch `dist/` at base
  `/proj/`: canonical links, absolute and relative illustration GIFs and a step-through page pass; a missing own-host
  page, another base on the own host, an above-root link, an outside host and a missing GIF fail (5 of 5).
  **`python3 -I tools/export_check.py --repo workspace/export-repo/`** from the main checkout after the fixes: 0
  failures, 0 warnings, exit 0; this closes the done-when item the lane left open. Noted for later phases: the
  config needs `site/src/cut.json` (Phase 3's builder writes it, with `groups`); X7's `github.com/IgorKonovalov`
  allowance is narrowed to the export repository at Phase 7 (Phase 2 review, ruling 6). Fixes count: tools 3.
- 2026-11-17 — **Owner decision: game-math hex passes by a short allowlist** (owner, via the orchestrator; implemented in
  lane/x70b). Hex values that are game math, not code addresses, are not X1/X3 failures: RNG seeds used as illustrative
  examples, the RNG multiplier and similar named constants, the randomness page's worked example, and the draw values in
  the schematic animations' calculation panels. Three mechanisms in `tools/export_check.py` (`load_allow`, `Allow`,
  `SectionTracker`, `RE_DRAW_CTX`), one reviewed config file, `docs/export/allow-hex.txt` (architect-owned, a reason on
  every line): (1) **values**, matched in any spelling: `6AC690C5` (the RNG multiplier), `0000029A` (the 666 second word of
  an initialised seed), `AA55AA55` (the save file's signature word), `0xC0FFEE` (the illustrations' seed), `00003039`
  (12345, the randomness example's seed); (2) **sections**, `section <page> <heading start> :: <reason>`: any hex of 6+
  digits under that heading of that page (the check follows the manifest's page to route map): the worked examples of
  randomness, levels (both), seed-to-world, characters, quests (two sections) and saves, 7 entries; (3) a **scoped rule in
  schematic illustration folders** for `steps.json` and `index.html`: hex passes only in the shapes the generators print
  for a draw, `{hi:lo}` seed states, `{start, 666} = {hex, 666}` and `lo`/`seed`/`draw` `= 0x…`. **Never allowed, by
  any of the three:** a value in the code image's range `0x00400000`-`0x007FFFFF` (the loader refuses such a values entry;
  a section or draw-shape value that falls in the range still fails, and the simplifier drops its unit: the saves
  example's `0x6D6D80` is one, dropped), a `sub_`/`DAT_` name, a `+0x` offset, a hex after `_` or `+`. The allowance applies
  to X1 and X3 only. **ADR-0031** governs constants of the code image (table data and values the binary holds: `PathDirTables`,
  `ActClockTables`); the allowlist respects it because it holds no value of the image's range and no table content: the
  multiplier is an arithmetic constant that the randomness page already states in words and the specs state, and every
  other entry is an input our own examples chose or a value computed from one. The multiplier is the one entry the
  reviewer should weigh against ADR-0031 (it is also a code-image immediate); the owner's decision names it. Fixtures and
  tests (`tools/test_export_check.py`, 101 checks): an allowed seed passes, the same value outside the allowlist fails, an
  image-range entry is refused with `load_allow`, an address next to an allowed value still fails, the draw shapes pass
  only in a folder and an address in a folder fails (built at run time from the `clean` fixture).
- 2026-11-17 — **Phase 3 done** (archivist, lane/x70b; Tier A review requested by the owner). `tools/export_build.py`,
  `tools/test_export_build.py` (31 checks; gate E20 now runs both test files), `docs/export/allow-hex.txt`, the allowance
  in `tools/export_check.py`, one text change in `tools/tc_anim.py` (below). **What it does:** redactor (front matter,
  *Open questions*, evidence parentheticals, anchor-only columns, address column of pseudocode lines, `sub_XXXXXXXX_`
  prefixes), simplifier (units: sentence of a paragraph, list item with its children, table row, fenced block, quote;
  caption sentences; a heading that fails takes its section; an empty section goes; `[L]` is rule `XL`), link rewriter
  (manifest pages to routes relative to the linking page's URL directory, anchors kept only if the heading survives;
  every other link keeps its text), illustration runner (`maze_anim.py` and `tc_anim.py` only, `python3 -I … <root>
  <args> --schematic --out <folder>`; a tool without the mode or a failed run is a report line). `--out` is refused unless
  `workspace/export` or `workspace/export-<name>`; no network module. `report.txt` at the cut root: per-rule drop counts,
  a per-page row (units, units dropped, share) and one `DROP <page> | <heading> | <rule> | <kind> | <text>` line per drop.
  **Choices the review should confirm:** (1) *The GIF is linked, not embedded.* A Markdown image of a public file needs the
  base path: a relative `../../illustrations/…` is an asset import to Astro and a root-absolute `/illustrations/…` ignores
  the base, so the page carries `[Animation: <id> (GIF)](…)`, `[Step through <id>](…/index.html)` and the caption, plus
  one added sentence ("Seed: illustrative … computed by our model, not observed in the game"). Inline embedding needs a
  small rehype step in `astro.config.mjs` (Phase 4's file) that prefixes the base to `/illustrations/` image sources;
  decision for the architect. (2) Evidence parentheticals are recognised by a token grammar (anchor, run id, address,
  finding link or id, ADR/plan word, date, `see`/`and`/`at`/`addendum`); a parenthetical with any other word stays and
  its unit goes to the simplifier. (3) The `XL` rule (an `[L]` tag anywhere outside *Open questions*) is the builder's own,
  not the check's. (4) `tools/tc_anim.py`: the creation-record line wrote `Game+0x6A 3` (an in-memory offset, X1) and
  "as logged for drops"; it now reads "Creation record for drops: item version 101, ladder 0, …" in both modes (the
  steps-equality test still holds, 5 tests OK). The value 3 is no longer shown; its meaning was not in the line.
  **First cut** (25 pages, merged with `main` at 4685ecae): `export_build.py` then `export_check.py workspace/export`:
  **0 failures**, 326 X12 warnings (noise by design; nominative names and table row names). Illustrations in
  `site/public/illustrations/drlg-maze-level36/` (43 frames) and `items-tc-andariel-hell/` (87 frames), each with its GIF,
  `index.html`, `steps.json`, `schematic.json`; the check verifies their hashes, marker and text (draw values by the
  scoped rule). Drops: 56 report lines, 5172 units, 69 dropped (1.3%): X1 33, X3 5, X9 19; by kind 38 list items (X9,
  the characters page's Battle.net lines, the glossary's offsets), 13 sentences, 2 rows (`0x6D6D80` in the saves
  example), 1 table, 2 caption sentences (the illustrations' "computed by tools/…" sentence, X3). Pages with drops: the
  glossary 34 of 161 units (21%), monster-ai 20 of 354 (5.6%, 13 are children of 7 dropped bullets), animation 2 (1.2%),
  quirks 1 (1.0%), server-frame 3, characters 2, items 2, then one each on randomness, levels, items-other-paths, saves,
  pathing; 14 pages none. The two illustration blocks do not appear in the drops.
  **Trial cut** (every reviewed spec added: 65 specs, status `reviewed`, in groups `s-<subsystem>`; manifest and output
  in scratch and `workspace/export-trial/`, never in git): 90 pages, 19223 units, 6310 dropped; of the 65 specs 14051
  units, **6241 dropped (44.4%)**. Drops per rule (a unit may carry several): X1 4876, X2 3048, X3 1580, X5 214, X9 114,
  open-questions 63 sections, children of dropped items 18; by kind (specs): 2814 table rows, 2147 list items, 703
  fenced blocks, 527 sentences, 79 sections, 7 tables. The check on the trial cut: **11 failures, all X6** (tables of
  21 to 135 body rows the manifest does not name: drlg/maze 23, drlg/outdoor 21, items/properties 25, items/vendors 36,
  monsters/ai 23, quirks 26, 73, 135, 22, 30 and 59), 703 X12 warnings, no X1 to X5, X7 to X11 residue: the simplifier
  leaves nothing the check would fail. Share of dropped units per spec, dropped/units: anim/README 12/36 (33%); anim/movement
  49/83 (59%); anim/timing 111/214 (52%); chain/README 49/142 (34%); combat/README 74/146 (51%); combat/damage 43/88
  (49%); combat/delivery 80/169 (47%); combat/reductions 40/104 (38%); combat/to-hit 39/107 (36%); conformance/README
  22/82 (27%); data/README 5/25 (20%); data/calc 60/208 (29%); data/excel 101/230 (44%); data/strings 33/129 (26%);
  drlg/README 76/109 (70%); drlg/collision 165/374 (44%); drlg/lifecycle 142/219 (65%); drlg/maze 87/218 (40%);
  drlg/outdoor 145/483 (30%); drlg/preset 109/200 (54%); drlg/room-tiles 91/171 (53%); drlg/warps 104/195 (53%);
  hirelings/README 82/236 (35%); items/affixes 126/261 (48%); items/cube 158/311 (51%); items/economy 122/251 (49%);
  items/inventory 118/216 (55%); items/properties 106/268 (40%); items/quality 61/186 (33%); items/quest-drops 140/263
  (53%); items/sockets-runewords 111/227 (49%); items/tc 126/273 (46%); items/trade 42/137 (31%); items/uniques-sets
  90/207 (44%); items/use 52/126 (41%); items/vendors 98/223 (44%); monsters/README 13/28 (46%); monsters/ai/README
  87/203 (43%); monsters/ai/catalogue 386/1230 (31%); monsters/ai/machinery 84/168 (50%); monsters/pool 126/218 (58%);
  monsters/spawn 130/280 (46%); monsters/special 156/371 (42%); monsters/stats 133/358 (37%); objects/README 159/338
  (47%); path/README 136/227 (60%); path/search 80/183 (44%); player/README 1/7 (14%); player/creation 100/211 (47%);
  player/party 23/101 (23%); quests/README 8/37 (22%); quests/progression 228/529 (43%); quests/travel 94/200 (47%);
  quirks/README 263/683 (38%); rng/README 30/56 (54%); rng/seeds 86/115 (75%); save/d2s 168/302 (56%); sim/frame 109/245
  (44%); skills/README 27/57 (47%); skills/catalogue 81/161 (50%); skills/dispatch 179/336 (53%); skills/missiles
  117/186 (63%); stats/README 19/32 (59%); stats/aggregate 88/142 (62%); stats/states 61/130 (47%). 21 specs lose more
  than half their units, 61 of 65 more than a quarter. Reading: the second cut as built keeps under three fifths of
  the specs and mostly their prose and pseudocode; most losses are table rows and bullets that carry an anchor, an
  address or a finding id inside the unit, which the redactor does not strip (it removes parentheticals and whole
  columns only, never an anchor inside a row), so a cheaper redactor rule (strip `fn:Name@0x…` inside a cell or bullet
  to `Name`) would recover many; that is a design choice for the architect before Phase 8/9, not made here. Also noted:
  X12 warnings 703 on the trial. Next: the architect's Tier A review, then Phase 6.
- 2026-11-17 — **Phase 3 review: accept with fixes (6); Phase 3 done** (architect, Opus Tier A, lane/x70b). Read the
  builder, both test files, the allowance in the check, the allowlist, gate E20 and the `tc_anim.py` caption change; cut
  afresh into `workspace/export-review/` and checked it. **Fixes (applied in the review commit):** (1) *The image range
  was too narrow* (blocking grade): `0x00400000`-`0x007FFFFF` covers `.text` and part of `.rdata` only; the pinned
  `Game.exe` maps to `0x009B9FFF` (SizeOfImage `0x5BA000`; `.data`/`.bss` from `0x705000`, 125 symbols above
  `0x7FFFFF`, the highest `0x00994C88`), so a `.data` address passed inside a worked-example section. `IMAGE_HI` is now
  `0x009B9FFF`, and X1's bare all-digit address shape covers `00[4-9]…`. (2) *The log's "a draw-shape value in the range
  still fails" was false*: the folder rule returned before the range test. Now only the brace seed states (`{hi:lo}`,
  `{start, 666}`) admit an in-range value (the TC illustration's `{a28ed4c0:00507fab}` is one); `lo =`, `seed`, `draw`
  shapes refuse it. (3) *Pins*: with the true range, three worked-example values fell in it (`0090CE87` randomness step
  4, `0090CE8A` the Den of Evil's first maze room, `0x800010` the saves example's flags) besides `0x6D6D80`. A new
  allowlist form `pin <hex> <docs path> :: <reason>` admits one in-range value on one page; the loader refuses a pin
  that `re/symbols.csv` names. The four are pinned, so the saves row of `0x6D6D80` is back; a section still admits no
  in-range value. (4) *A `[L]` tag fails X2* in the check, not only the builder's `XL`. (5) *X3 fails a working-docs
  path* (`specs/…`, `tables/`, `formats/`, `findings/`, `plans/`, `adrs/`, `backlog/`): the glossary carried 126
  `See specs/…` pointers, repository paths under ADR-0035's no-tie rule. The redactor now drops a `See <links>.`
  sentence whose links are all labelled by a path, and (6) a parenthetical made only of in-memory offsets
  (`` (`unit+0x20`) ``). Tests: check 112, builder 36, all pass. **Rulings.** The allowlist is the owner's decision and
  no wider: five values (none in the image's range), seven sections (each a wiki worked example, its heading scope ending
  at the next heading of its level; read: illustrative seeds and values computed from them), four pins. *The multiplier
  `6AC690C5`* stays: ADR-0031 governs constants a rule can't give and asks for the rule where one exists; the
  multiplier is the rule itself, a reimplementation can't do without it, it holds no table content, and the specs and
  the randomness page already state it. *`0x6D6D80`*: the drop was the conservative reading; it is a computed checksum,
  now pinned. (a) *Anchors inside a unit*: rewrite, don't drop; written as a Phase 9 prerequisite above. (b) *GIF linked
  vs embedded*: embed, with a rehype step in Phase 4's config; before Phase 6 ([entry](../backlog/2026-11-17-architect-archivist-plan-0070-before-phase-6-neutral-marker-inline.md)).
  (c) *`XL`*: accepted, and now also a check rule (fix 4). (d) *The 11 X6 tables*: second-cut matter; at Phase 9 each is
  named in the manifest with a reason (our own step or decision tables) or left out (a list of game-table rows). The
  link layout (`../../illustrations/…`, routes as directories) and the caption's added sentence are accepted. **First
  cut, rebuilt** (`export_build.py --out workspace/export-review`, then `export_check.py`): 25 pages, **0 failures**,
  326 X12 warnings; 50 drop lines (X1 27, X3 4, X9 19); the glossary 29 of 161 units (18%), monster-ai 20 of 354. Hand
  greps of the cut for tool names, method words, the working repository's name, the owner's paths, anchors and
  addresses: none, except below. **Readability (Phase 6 reads these):** the front page and randomness read whole. The
  glossary keeps every entry's sense but loses the core seed vocabulary the wiki links to (Map seed, Game seed, Item
  seed and five more) and keeps a repository note in its preamble and five method-only entries; [entry](../backlog/archive/2026-11-17-architect-spec-writer-glossary-export-readiness-plan-0070.md)
  to the spec-writer. monster-ai's *The first call* and *Past the first call* are about our method and no longer read
  whole after the drops ("So the 12 614 …" points at a dropped row; "They are exactly the decisions …" at a dropped
  sentence); Phase 6 decides between a spec-writer rewrite and a manifest directive that drops a named section. The two
  illustration pages read whole; their calc text names spec sections (`tc.md D`), acceptable. **A tie missed at the
  Phase 2 review:** the schematic marker `d2recon-schematic/1` is the working repository's project name, in every
  published illustration file, and `schematic.json` names our tools; renamed before Phase 6 (the archivist entry
  above). Request [closed](../backlog/archive/2026-11-17-archivist-architect-review-plan-0070-phase-3-builder-redactor-simplifi.md).
  Ledger: verdict accept with fixes, 6 fixes: misread 1 (the image range), overclaim 1 (the draw-shape claim),
  omission 3 (pins for the true range, `[L]` in the check, working-docs paths), other 1 (the offset parenthetical).
- 2026-11-17 — **Glossary and monster-ai ready for the cut** (spec-writer, lane/x70g; Tier A review
  [requested](../backlog/archive/2026-11-17-spec-writer-architect-review-x70g-glossary-monster-ai-export-readiness.md)). The
  glossary's 29 dropped entries (27 X1, 2 X3) now carry their offsets and addresses in trailing evidence-only
  parentheticals, so each definition stands alone and the working text keeps every offset; the preamble note left the
  body (its rule is in the spec-writer skill, step 6); the five method-only entries stay, since wiki pages in the cut
  use the terms. monster-ai: the X9 units of *The first call* and *Past the first call* (and the three *shorts* items
  dropped for the same word) reworded, and six link-only parentheticals on a line of their own joined to their
  sentence (each left a stray full stop). Cut into `workspace/export-x70g`: glossary 29 of 161 units dropped before, 0
  of 159 after; monster-ai 20 of 354 before, 0 after; `export_check` 0 failures. Entry
  [closed](../backlog/archive/2026-11-17-architect-spec-writer-glossary-export-readiness-plan-0070.md).
- 2026-11-17 — **Review of lane/x70g (architect, Tier A, Opus): accept with fixes 2.** The 29 reshaped glossary
  entries keep their sense and every offset (word diff read entry by entry; `NpcStoreCtl+0x08` and
  `QuestControl+0x18` match the vendors and quest-drops specs, `Unit+0xC4` bit 6 the dispatch spec); the monster-ai
  rewordings claim nothing new and keep their tag-words, and "the logging" still says the inputs were logged, which is
  honest and outside X9's tool names. A fresh cut (`workspace/export-x70gr`): glossary 0 of 159 units dropped,
  monster-ai 0 of 354; the glossary entries read whole without their parentheticals and *See* links, *The first call*
  and *Past the first call* read whole; `export_check` 0 failures (330 warnings, none on these pages' claims). The
  method-only entries (Boundary oracle, Retired oracle, First boundary, Activation-order record, Tier AI) use
  "log", "logged" and "emulation", which name the method, not a tool; kept. The skill edit stays in the spec-writer
  skill (that lane adds the glossary's terms), with a pointer to the export decision. Fixes: the Sparkle chest's flag
  named as the objects spec names it (sparkle flag, not super-chest flag); the skill's rule cites ADR-0035 and the
  manifest and says the *See* link drops too. Request
  [closed](../backlog/archive/2026-11-17-spec-writer-architect-review-x70g-glossary-monster-ai-export-readiness.md).
  Ledger: verdict accept with fixes, 2 fixes: misread 1 (the flag's name), omission 1 (the skill rule's source and
  the *See* link).
