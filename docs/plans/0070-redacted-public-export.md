# 0070 — The redacted public export: what leaves the machine, how it is redacted, and the check that guards it (ADR-0009, ADR-0035)

> **Status:** in progress: Phase 1 done 2026-11-16; Phases 2 to 7 done 2026-11-17 (the first cut served at https://igorkonovalov.github.io/arpg-1-14d-notes/); Phase 9 done 2026-11-17 (the second cut: 46 reviewed specs; served 2026-11-17, Phase 10 done; Phase 11 in progress); re-cut 2026-11-16 for three later owner decisions (simplification,
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
  number of drops read and the illustrations seen. **Done 2026-11-17** (accept with fixes; see the log).

### Phase 7 — The owner's read and the first publish
- **Owner skill:** human
- **What:** the owner reads the cut, creates the export repository under their account, sets Pages' source to GitHub
  Actions, copies `workspace/export-repo/` and `workspace/export/site/` into a fresh folder, runs `npm install` once
  to make the lockfile, and pushes through a pull request. The CI build and link check must pass on it; the merge to
  `main` deploys.
- **Done when:** the owner says the site is served. No agent takes part beyond answering questions.
- **Preconditions (Phase 6 review, 2026-11-17).** (a) The real site build and its link check on `dist/` have never
  run: this machine has no npm, so they run first on the owner's machine (step 4 below) and again in CI; a red build
  or link check stops the publish. (b) Before the first push the check's repository allowance narrows to the export
  repository's name (step 2): today X7 passes any `https://github.com/igorkonovalov…` URL (Phase 2 review, ruling 6).
- **The owner's checklist.** `<name>` is the export repository's name, `arpg-1-14d-notes` (chosen 2026-11-17; the site is
  `https://igorkonovalov.github.io/arpg-1-14d-notes/`). `$W` is the working checkout. No agent runs any of these steps beyond the check in step 2.
  1. **Read the cut**: the pages under `$W/workspace/export/site/src/content/docs/` and the drops in
     `$W/workspace/export/report.txt` (never copied). Rebuild it first if the docs changed since 2026-11-17:
     `python3 -I tools/export_build.py`.
  2. **Done 2026-11-17** (archivist lane x70n): `<name>` = `arpg-1-14d-notes`, written into the check: `URL_ALLOW` in `tools/export_check.py` takes
     `https://github.com/igorkonovalov/<name>` in place of the bare account prefix (an archivist lane, or the owner,
     with a test that the account's other repositories fail). Then, from `$W`:
     `python3 -I tools/export_check.py workspace/export --repo workspace/export-repo/` must print 0 failures.
  3. **Assemble a fresh folder** outside `$W`, never a clone of it:
     `mkdir ~/Work/<name> && cd ~/Work/<name> && git init -b main && cp -r $W/workspace/export-repo/. . && cp -r $W/workspace/export/site/. site/`
     (this copies `site/src/content/docs/`, `site/src/cut.json` and `site/public/illustrations/` beside the
     project files; `report.txt` stays behind). `git status` must show no `.git` folder copied and nothing else.
  4. **Build and check locally**, from `site/`: `npm install` (writes `package-lock.json`, which is committed),
     `npx playwright install chromium`, `SITE_BASE=/<name>/ npm run build`, then
     `SITE_BASE=/<name>/ node scripts/check-site-links.mjs dist`. Both must pass; `SITE_BASE=/ npm run build` and
     `npm run preview` give a local look. Remove `dist/` and `.astro/` (ignored anyway).
  5. **Create the repository** `arpg-1-14d-notes` on GitHub under the owner's account, empty (no README, licence or
     `.gitignore` from GitHub); in Settings, Pages, set the source to GitHub Actions. If it already exists, it must
     be empty and Pages' source must be GitHub Actions (step 6 pushes into it).
  6. **First commit and pull request.** `git commit --allow-empty -m "chore: start"` on `main` and push it (it holds no
     workflow, so nothing runs); then `git switch -c cut-2026-11-17`, stage the files by path
     (`git add .github .gitignore LICENSE README.md site`), commit, push the branch and open a pull request. The
     `build` job (install, Mermaid, build, link check) must be green on it.
  7. **Merge** the pull request into `main`; the `deploy` job publishes `https://igorkonovalov.github.io/<name>/`.
     Open the front page, one page with a diagram and both illustrations (the GIF and its step-through page), and
     say the site is served; that closes Phase 7.

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
  unchanged. Rerun the trial and log the new share per spec before Phase 9 starts. Tier B check. *Done* (`lane/x70a`,
  reviewed 2026-11-17). Still before the cut (review of `lane/x70a`): the check also fails a `.log` file name, a partial
  address with `x` digits (`0x0063xxxx`) and a `.claude/` path, which pass today (20 log names in the trial); and the
  second redactor round the review entry names (*Residue*), then the trial is measured again. *Done* (`lane/x70b2`, 2026-11-17): the check fails `.log` names, partial addresses
  and `.claude/` paths; the second redactor round is in; the trial is measured in words (see the log).
- **What:** add the reviewed specs to the manifest, cut afresh, and run the Tier A redaction review above. Read every
  drop line of the six sampled specs and the drop counts of every spec. A spec that loses more than a quarter of its
  sentences, or one whose remaining text no longer reads as whole, stays out of the manifest.
- **Done when:** the manifest holds the specs that pass; a verdict is recorded in this plan's log with the cut date,
  the check's output, the sample read, and each left-out spec with its reason. **Done 2026-11-17** (accept; see the log).

### Phase 10 — The owner's read and the second publish
- **Owner skill:** human
- **What:** the owner reads the second cut, copies `workspace/export/site/src/` and `site/public/` over the export
  repository's, and pushes through a pull request; the merge deploys.
- **Done when:** the owner says so.

### Phase 11 — More illustrations and interactive elements (owner, 2026-11-17)
- **Owner skill:** architect, then archivist (tools) and spec-writer (captions); added at the owner's request
  ("as much animations and interactive elements as possible"), after the second cut, in the order the owner approved.
- **What:** (1) the architect lists candidates, one per page where a picture earns its place (seed to world, the RNG
  steps, pack and minion placement, the affix pick, the path search, room stitching), each with its tool, its inputs
  and what it may show; (2) an ADR on scripted widgets in the export: today the check fails raw HTML and the export
  repository ships no script of ours, and a widget may compute only from rules and short illustrative rows, never from
  game tables (ADR-0031, ADR-0009 risk 3); the ADR states what a widget may contain and the check rule that verifies it;
  (3) pre-rendered schematic animations under ADR-0036 need no new rule and go first, in archivist tool lanes; (4) each
  batch is reviewed on Opus and enters the next cut.
- **Steps (architect, 2026-11-17).** (1) and (2) are written: the candidates below, and
  [ADR-0037](../adrs/0037-scripted-widgets-in-the-export.md) (proposed). Then, once the owner accepts both:
  (3a) one archivist lane builds the schematic kit (row 0) and batch 1's new generators; the spec-writer places each
  ```` ```illustration ```` block with its caption in the wiki or spec page; one Opus Tier A review per lane pair.
  (3b) batch 2 likewise, in two or three lanes. (4a) one archivist lane adds X13 and E21 (ADR-0037) to the check and
  the gate, `tools/test_widgets.py` and the builder's ```` ```widget ```` block, and prepares the export repository's
  host step, styles and CSP under `workspace/export-repo/` for the owner (Tier A: a safety device). (4b) batches 3 and
  4, a few widgets per lane. Each batch enters the next cut and its redaction review, which opens every new picture
  and widget. A generator reads the user's own files at cut time, as ADR-0034 and ADR-0036 allow (tables, and image
  constants as `maze_anim.py` already does through `maze_replay.py`); only what a frame shows reaches the export, and
  it passes the check. A widget's data never comes from them (ADR-0037).
- **Candidates (architect, 2026-11-17; accepted by the owner the same day).** Kind: **P** a pre-rendered schematic animation (GIF,
  frames, step-through page; ADR-0036, no new rule), **S** a static schematic picture (one marked frame from a P
  tool), **W** a scripted widget (ADR-0037; its fallback is the P row named, or a short table). Routes are the second
  cut's. Inputs name the spec sections the captions restate and the illustrative values; a seed is one of
  `allow-hex.txt`'s illustrative seeds or a new line there. Tools are the archivist's, in `tools/` (a widget in
  `tools/widgets/<name>/`); "over X" names the model the generator drives. Effort is an estimate: S about a
  lane-hour, M half a lane, L a lane. Batch order is priority; within a batch, row order.

  | # | Page (route), section | Shows | Kind | Inputs | Tool | Effort | Batch |
  |---|---|---|---|---|---|---|---|
  | 0 | (all P rows) | The schematic kit: boxes, a cell grid, bars, a number tape, a legend, a palette with light and dark values | — | ADR-0036's palette and 5×7 font | `anim_common.py` | M | 1 |
  | 1 | foundations/randomness, The generator | One seed's two words, the multiply-and-add, the draw and its `mod n`, eight draws in a row | P | randomness § The generator, § A worked example; seed 12345 | new `rng_anim.py` over `rng.py` | S | 1 |
  | 2 | foundations/randomness, Two roots to Rooms; running/seed-to-world, The build | The seed tree: game seed, act seeds, level seeds (a sum), room seeds (one draw each) | P | randomness § From the map seed to § Rooms; spec-chain § 1; seed 0xC0FFEE | new `seedtree_anim.py` over `drlg.py` | M | 1 |
  | 3 | items/items, More players, fewer empty picks | The same drop with one player and with eight: NoDrop shrinking, pick by pick | P | tc § E; the existing block's monster and seed, `--players 8` | `tc_anim.py` (new block only) | S | 1 |
  | 4 | world/levels, Maze levels | A second maze, another level of the maze list, for a different start shape and theme count | P | maze § B–E, § H; seed 0xC0FFEE | `maze_anim.py` (new block only) | S | 1 |
  | 5 | spec-items/quality, Test order and § D–E; items/items, The quality roll | The quality ladder: unique, set, rare, magic, superior, normal, low; each test's chance, its draw, magic find's diminished term | P | quality § C–E; the ratio row the page shows; ilvl, mlvl, MF illustrative | new `quality_anim.py` over `quality.py` | M | 1 |
  | 6 | world/monsters, Champions and uniques; spec-monsters/special § A–D | Champion or unique, then the weighted mod picks with their exclusions and per-mod draws | P | special § A, § B, § D; illustrative seed and class | new `special_anim.py` over `monspecial.py roll` | S | 1 |
  | 7 | running/animation, The schedule; spec-anim/timing § E, F, J | The frame counter advancing at a rate, the event frames, the action frame | P | timing § E, § F, § J; an illustrative frame count and rate | new `timing_anim.py` over `anim.py` | S | 1 |
  | 8 | running/server-frame, The tick and its passes; spec-sim/frame § B–D, J | One tick pass by pass, and which seeds each pass draws on | P | frame § B–D, § J (the spec's pass list, no log) | new `frame_anim.py` | S | 1 |
  | 9 | world/monsters, Groups and minions, Placement; spec-monsters/special § E, F | A pack placed on a schematic room: the leader's spot, each member's spot, refused cells | P | special § E–F; collision's spawn predicates; illustrative seed | new `pack_anim.py` over `monspawn.py`, `collision.py` | L | 2 |
  | 10 | world/monsters, Which monsters a level can have; spec-monsters/pool § A–C | The region seed and the pool pick, class by class | P | pool § A–C; an illustrative level | new `pool_anim.py` over `monspawn.py` | M | 2 |
  | 11 | world/levels, Laying out the act; spec-drlg/warps § B, C | The act link builder placing level rectangles, with its retries | P | warps § B–C; seed 0xC0FFEE | new `links_anim.py` over `drlg.py` | M | 2 |
  | 12 | world/levels, Outdoor levels; spec-drlg/outdoor § B–G | Outdoor stitching: the cell grid, the outline, the presets, the seams and the border pass | P | outdoor § B–G (one act); seed 0xC0FFEE | new `outdoor_anim.py` over `drlg.py` | L | 2 |
  | 13 | world/levels, What a preset places; spec-drlg/preset § 2, 3 | A preset's units, each keep or drop roll in turn | P | preset § 2–3; an illustrative preset and seed | new `preset_anim.py` over `drlg.py` | M | 2 |
  | 14 | spec-drlg/warps § E, F | Two levels' warp points and how they pair | S | warps § E–F | `links_anim.py` (one frame) | S | 2 |
  | 15 | running/pathing, The plan, step by step; spec-path/search § L | The search on a toy grid: the open set, each expansion, the path | P | search § A, § L; a hand-drawn toy grid | new `path_anim.py` over `path.py` | M | 2 |
  | 16 | spec-path/search § I, J | The random walk and the spiral on the same toy grid | P | search § I–J; illustrative seed | `path_anim.py` | S | 2 |
  | 17 | characters/combat, Draw order and chaining | One melee hit: the to-hit, block, damage and delivery draws in order | P | to-hit § A–C, damage § A–B, delivery § A–B; toy attacker and defender | new `combat_anim.py` over `combat.py` | M | 2 |
  | 18 | characters/characters, Hirelings: the hire list; spec-hirelings § D, E | A hire list rolled entry by entry | P | hirelings § B, § D–E; illustrative seed | new `hire_anim.py` over `hirelings.py list` | M | 2 |
  | 19 | spec-items/affixes § B, C | One affix pick: the candidates filtered by alvl, type and group, then the weighted pick (20 rows at most on a frame) | P | affixes § B–C; illustrative ilvl and base | new `affix_anim.py` over `affixes.py` | M | 2 |
  | 20 | spec-items/sockets-runewords § D | The runeword match: socket order against a recipe | P | sockets § D–E; one recipe the page names | new `runeword_anim.py` over `sockets.py` | S | 2 |
  | 21 | spec-anim/movement § B | A moving unit's per-frame step on subtiles | P | movement § A–B; illustrative speed | new `move_anim.py` over `anim.py` | S | 2 |
  | 22 | foundations/randomness, The generator | Type a seed and a count, see each draw (fallback: row 1) | W | as row 1; the multiplier from `allow-hex.txt` | `widgets/rng`, twin `rng.py` | S | 3 |
  | 23 | characters/combat, Will it hit; spec-combat/to-hit § A | Chance to hit from attack rating, defence and levels, with its clamp | W | to-hit § A; toy inputs | `widgets/tohit`, twin `combat.py` | S | 3 |
  | 24 | characters/combat, Building the damage, Reductions; spec-combat/damage § A–B, reductions § A | The damage built and reduced, step by step (fallback: row 17) | W | damage § A–B, reductions § A; a toy weapon | `widgets/damage`, twin `combat.py` | M | 3 |
  | 25 | running/animation, Breakpoints; spec-anim/timing § J, K | Frames per action from a frame count and a rate; the breakpoints (fallback: row 7) | W | timing § J–K; toy inputs | `widgets/breakpoints`, twin `anim.py` | S | 3 |
  | 26 | world/monsters, Stats at creation; spec-monsters/stats § A | A monster stat scaled by level and difficulty | W | stats § A; a toy row | `widgets/monstat`, twin `monstats.py` | S | 3 |
  | 27 | characters/characters, The mercenary's stats per level; spec-hirelings § G | A mercenary's stats at any level | W | hirelings § G; a toy row | `widgets/merc`, twin `hirelings.py` | S | 3 |
  | 28 | spec-items/quality § C–D | The quality chances for an ilvl, qlvl and magic find (fallback: row 5) | W | quality § B–D; the ratio row the page shows | `widgets/quality`, twin `quality.py` | S | 3 |
  | 29 | characters/saves, The checksum | The checksum step by step over hand-typed toy bytes | W | saves § The checksum | `widgets/checksum`, twin `d2s.py` | S | 3 |
  | 30 | foundations/randomness, Two roots to Rooms | Type a game seed, expand the seed tree (fallback: row 2) | W | as row 2 | `widgets/seedtree`, twin `drlg.py` | M | 3 |
  | 31 | running/pathing; spec-path/search § L | Draw walls on a toy grid, watch the search (fallback: row 15) | W | as row 15 | `widgets/path`, twin `path.py` | L | 3 |
  | 32 | spec-data/calc § B, D | A toy formula evaluated step by step | W | calc § B, § D | `widgets/calc`, twin `calc.py` | M | 4 |
  | 33 | items/inventory, Where an item can go | Toy items placed in a toy grid by the placement rule | W | inventory § Where an item can go | `widgets/grid`, twin `inventory.py` | M | 4 |
  | 34 | items/economy, Prices; spec-items/economy § A–C | A toy item's price, term by term | W | economy § A–C | `widgets/price`, twin `economy.py` | M | 4 |
  | 35 | running/quests, A few quests, bit by bit; spec-quests/progression § A, D | A quest word's bits as events arrive | S | progression § A, § D; one quest the page walks | new `quest_anim.py` over `quests.py` | M | 4 |
  | 36 | items/items-other-paths, The Horadric Cube; spec-items/cube § A, B, M | A recipe matched and its output built, with its draws | P | cube § A–B, § M; one recipe the page names | new `cube_anim.py` over `cube.py vector` | M | 4 |
  | 37 | world/levels, The collision grid; world/monsters, Placement | The four spawn tests on a toy room's subtiles | P | the levels and monsters sections; a toy room | new `collision_anim.py` over `collision.py` | M | 4 |
  | 38 | world/objects, The eight slots, Finding a spot | A room's object slots, the member pick, the spot search | P | objects § The eight slots, § Finding a spot; seed 0xC0FFEE | new `objects_anim.py` over `objects.py` | M | 4 |
  | 39 | spec-skills/missiles § D, E | A missile's per-frame step and its hit | P | missiles § B, § D–E; a toy missile | new `missile_anim.py` over `skills.py` | M | 4 |
  | 40 | characters/stats-and-states, Regeneration | The regeneration accumulator over frames | W | stats-and-states § Regeneration; toy inputs | `widgets/regen`, twin `stats.py` | S | 4 |

  40 candidates and the kit: 24 P, 2 S (rows 14, 35), 14 W. Batch 1 is the kit and rows 1 to 8 (rows 3 and 4 are new
  blocks on existing tools); batch 2, rows 9 to 21 (13); batch 3, rows 22 to 31, the first 10 widgets; batch 4,
  rows 32 to 40 (9). A model named "over X" is the archivist's to confirm when the lane starts; one that needs a run
  log to drive it gets a small entry point from the spec's inputs, or the row moves later. Left out on purpose:
  experience per level (a table, not a rule), any save or item-bit editor (ADR-0037: no game-file input), the AI
  state machine (Mermaid already draws it).
- **Done when:** the candidate list and the widget ADR are accepted by the owner, and the first batch is served.

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
  string `schematic-only/1` inside every `.gif`, `.png`, `index.html` and `steps.json` of the folder;
  `schematic.json` is `{"marker": "schematic-only/1", "files": {"<relative path>": "<sha256>"}}` listing every
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
  font. The marker is the byte string `schematic-only/1` (the one Phase 2's check, lane/x70c, looks for) in every
  file: PNG `tEXt` chunk, GIF comment extension, an HTML comment, `steps.json` (an object `{"schematic_only", "steps"}`
  in schematic mode; the full mode keeps the bare list). `schematic.json` is `{"marker", "args", "files":
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
  vs embedded*: embed, with a rehype step in Phase 4's config; before Phase 6 ([entry](../backlog/archive/2026-11-17-architect-archivist-plan-0070-before-phase-6-neutral-marker-inline.md)).
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
- **2026-11-17, archivist, lane/x70m (neutral marker, inline GIF; entry from the Phase 3 review).** (1) *Marker:*
  `schematic-only/1` (`MARKER`; the PNG `tEXt` keyword and GIF comment key `MARKER_NAME` is `schematic-only`) in
  `tools/anim_common.py` and `tools/export_check.py`; `schematic.json` is `{"marker", "args", "files"}`, no `tool` key
  (`write_schematic_json` lost the parameter; `maze_anim.py` and `tc_anim.py` follow) and the check refuses a `tool`
  key (X11). The Phase 2 design text above names the new string; the ruling at "Rulings on the lane's choices" keeps the
  old one as history. The TC illustration's calc text no longer names `--mlvl` ("not modelled here", "an input
  default"). The `clean` and `X11-*` fixtures and `X8-image-outside/pic.gif` were rewritten by a scratch script that
  swaps the marker in the PNG `tEXt` chunk (CRC recomputed), the GIF comment and the text files and recomputes the
  hashes (the hash-mismatch fixture keeps its deliberate mismatch). The fixtures' Markdown images are root-absolute.
  (2) *Inline GIF:* the builder writes `![Animation: <id>](/illustrations/<id>/<gif>)` plus the step-through link
  (relative, as before). X8 accepts only a root-absolute `/illustrations/<id>/<file>` of a verified folder (a relative,
  an unlisted or an elsewhere target fails); `RE_ABS` (X4) skips that image-target shape. Tests: 3 new checks in
  `tools/test_export_check.py` (marker has no project name, `tool` key refused, X8 target shapes), 2 in
  `tools/test_export_build.py` (inline image, X8 only for a verified folder), `test_anim_schematic.py` asserts no
  `tool` key and no `d2recon`/`--mlvl` text. **Export repository (workspace, not git):** `site/astro.config.mjs` gained
  `rehypeIllustrationBase()` (prefixes `SITE_BASE` to an `<img>` whose `src` starts `/illustrations/`, added to
  `markdown.rehypePlugins` after Mermaid); `site/scripts/check-site-links.mjs` needed no change (it already resolves
  every `src="..."` against the base). No npm here: the site build and the link check on `dist/` are not run; Phase 6
  runs them. Result: first cut rebuilt (25 pages, 0 dropped), `export_check` 0 failures (326 X12 warnings), `--repo`
  0 failures, `grep -r d2recon workspace/export/site` empty, the three test files green.
- **2026-11-17, architect, Tier B check of lane/x70m (Opus).** Verdict **accept with fixes (1)**. Every item of the
  [entry](../backlog/archive/2026-11-17-architect-archivist-plan-0070-before-phase-6-neutral-marker-inline.md) is done:
  the marker `schematic-only/1` (keyword `schematic-only`) names no project, repository or person; `schematic.json` is
  `{"marker", "args", "files"}` and a `tool` key fails X11; the TC calc text no longer names `--mlvl`; the builder writes
  `![Animation: <id>](/illustrations/<id>/<gif>)` plus the relative step-through link. X8 passes an image only when its
  target is `/illustrations/<id>/<file>` with `(id, file)` in the verified folder's listing, so a relative, unlisted,
  dot-segment or elsewhere target fails, and `<img>` HTML still fails. `rehypeIllustrationBase()` (read in the
  workspace export repository) rewrites only `img` elements whose `src` starts `/illustrations/`, prefixing `SITE_BASE`
  without its trailing slash (`/` gives an unchanged path); Mermaid's `data:` images are untouched; the site build and
  `check-site-links.mjs` on `dist/` stay Phase 6's. **Fix (omission 1):** `RE_ABS`'s skip matched any
  `/illustrations/<a>/<b>)` in prose, dot segments included (`(/illustrations/../home)` passed X4); it now skips only
  right after `](`, with segments that don't start with a dot (test added). Rebuilt here into a scratch cut: 25 pages
  written, 0 pages dropped, 50 unit-drop report lines; `report.txt` byte-identical to the Phase 3 review's cut, and the
  only page changes are the two image lines (no redaction regressed). `export_check` 0 failures (326 X12 warnings),
  `--repo` 0 failures; no `d2recon`, `maze_anim`, `tc_anim` or `.py` in the cut. Tests: export_check 117/0,
  export_build 38/0, anim_schematic OK. **For the Phase 6 review:** the illustration calc text cites working spec
  files: `tc.md B1` style (ruled acceptable at the Phase 3 review) but also `spec drlg/maze.md G1` and
  `drlg/README.md`, which carry a directory and read as the repository paths ADR-0035 bars; rule there. Request
  [closed](../backlog/archive/2026-11-17-archivist-architect-review-plan-0070-neutral-marker-and-inline-gif.md).
  Ledger: verdict accept with fixes, 1 fix: omission 1 (the X4 skip's shape).
- **2026-11-17, architect, Phase 6: the first cut's redaction review (Opus, Tier A, lane/x70r6).** Verdict **accept
  with fixes (8)**; Phase 6 done. **Cut:** 2026-11-17, `python3 -I tools/export_build.py` from `main` at 6519f8d3 plus
  this lane's fixes, into `workspace/export`: 25 pages written, 0 dropped, two illustration folders (`drlg-maze-level36`,
  43 frames; `items-tc-andariel-hell`, 87 frames). **Checks:** `export_check.py workspace/export`: 0 failures, 330 X12
  warnings, exit 0; `--repo workspace/export-repo/`: 0 failures, 0 warnings; self-tests 117/0 (check) and 41/0
  (builder), `test_anim_schematic.py` OK, gate full green. **X12 read:** 165 distinct capitalised names, all game names
  (areas, skills, items, monsters), the illustrations' rare names and the nominative marks; no string-table text. The
  two quoted-run warnings (pathing, server-frame) are spans between two short quotes, not a quotation. **Drops read:**
  all 14 lines of the fresh cut's report, then the 6 left after the fixes: 2 caption sentences naming our tools (the
  builder's own label sentence replaces them), the characters page's 2 Battle.net sentences (meant), and 2 method
  sentences whose loss leaves the paragraph whole (randomness, the 852 inlined copies; items, a re-reading). Eight of
  the 14 were claims lost to a tool word (the run drain's formula, the socket-count claim, the server frame's pair
  counts and others); the wiki now says them without it (fix 7). **Read whole:** the front page, about, reading the
  tags, randomness, glossary, monster AI, levels, items, characters, saves; read around every drop and residue hit in
  animation, server frame, pathing, inventory and quirks; hand greps of all 25 pages per risk: (1) no address,
  `sub_`/`DAT_`, `+0x` offset or anchor; tool names only where X9 allows; (2) 76 Mermaid fences and two plain fences
  (the saves example's 48 header bytes, our own test save), no pseudocode; (3) no table over 20 rows (the longest 18
  body rows), no flavour text; (4) "Blizzard" only on the about page and in the footer; (5) no `src:` id, no Open
  questions section. Nothing says where a game file came from, nothing implies affiliation, no identity beyond
  ADR-0035 (no owner name in the text). **Illustrations seen:** both GIFs (a GIF89a with the marker comment), maze
  frames 20 and 42, drop frames 50 and 86 (boxes, door bars, name cards, the 5x7 font, our palette; no game pixel),
  both step-through pages (template text, the help list, the script: no URL, no request, frames set by
  `setAttribute`), the 96 and 134 distinct step texts (numbers folded) and both `schematic.json`. **Every file of
  `workspace/export-repo/` read** (README, LICENSE head, `.gitignore`, the workflow, `package.json`, `astro.config.mjs`,
  `content.config.ts`, `Footer.astro`, `check-site-links.mjs`).
  - **Fixes** (category in brackets): (1) [tools] the redactor left the closing punctuation of an evidence
    parenthetical that sat on its own line on the next line, so pages read "confirmed ." 265 times over 20 pages;
    `drop_evidence_parens` now joins it back (2 tests). (2) [tools] 13 pages ended "and how we know." with the
    method page's link dropped: a manifest line `alias <path> <page>` (README's format table, builder, 1 test), and
    `alias wiki/how-we-know.md export/reading-the-tags.md`, so those links reach the tags page. (3) [tools] the
    illustration captions' folder paths, ruling 1 below. (4) [wording] five wiki link texts `anim/README`,
    `combat/README`, `monsters/README` (and `README § Data flow`), `skills/README`, `stats/README` now name the
    subsystem. (5) [wording] the glossary's "the findings' NPC seed". (6) [wording] process residue naming our records:
    "driven by an agent" (inventory), "the findings did not find" (pathing), five sentences of monster AI ("a finding",
    "raises no role and no symbol", "no earlier review caught"), reworded without changing the claim. (7) [wording]
    eight units dropped for a tool word (`logger`, `logged run`, `harness`) reworded to "the logs", "a run": the cut
    now keeps the run-drain formula, the socket caps' order and the server frame's counts. (8) [tools] the export
    repository's `astro.config.mjs` gave the top-level pages (How to read the tags, About) no sidebar entry; they now
    come first, by their `sidebar.order` (run under node on the cut's tree; `node --check` clean; original kept in the
    lane's scratch). Ledger: verdict accept with fixes, 8 fixes: tools 4, wording 4.
  - **Ruling 1 (spec citations in illustration text).** A spec named by its file and section (`tc.md B1`,
    `maze.md G1`) or by its subsystem name (`player/creation § J`, `rng/seeds`) passes: it names a document of the
    second cut and gives no place in the working repository. A folder and a `.md` together (`drlg/README.md`,
    `drlg/maze.md`, `drlg/warps.md`, `data/strings.md`) or a `README` name read as repository paths and go. Fixed in
    both modes, so the steps stay equal: `tools/maze_anim.py` writes "the DRLG overview spec, step 9", "maze.md G1"
    and "warps.md"; `tools/tc_anim.py` "strings.md D and C"; `test_anim_schematic.py` OK. The check is not widened;
    Phase 9's specs carry many such citations, and its rewrite rule should apply this ruling.
  - **Ruling 2 (the site build).** The real Astro build and the link check on `dist/` were never run (no npm here).
    They are a Phase 7 precondition, run on the owner's machine before the first push and again in CI; the commands
    are Phase 7's step 4.
  - **Ruling 3 (X7's account allowance).** Narrowing `github.com/igorkonovalov` to the export repository's name is
    Phase 7's step 2, before the first push, with the check rerun.
  - **Left as they are (noted, not reject-grade):** glossary links land on the glossary's top, since its entries are
    list items with no anchor; a few pages say "follow the links" or "each links its section" of spec mentions that
    are now plain text (the front page says why); method words the plan keeps (*emulation*, *batch*, "raised",
    "the project's notes"); the glossary's two source-file names of the room records (names, not data).
  - **For the owner (Phase 7):** (a) read the cut; (b) choose the export repository's neutral name, so that X7 can be
    narrowed and the check rerun; (c) run the build and the link check locally (never run here); (d) create the
    repository, set Pages to GitHub Actions, open the first pull request, merge when green; (e) the licence stays
    CC BY 4.0 unless changed before the first push. The checklist is in Phase 7.
- 2026-11-17 — **Maze schematic: entry and exit marks on the room boxes** (archivist, lane/x70w; owner feedback: "on
  maze there is no exit/entry marks on last step on the map"). The schematic's final frame now marks each room box that
  holds a warp with a cyan diamond at the box centre, labelled `ENTRY:`/`EXIT:` and the destination level as in the
  full mode, and the corner legend is one line ("room holding a warp, position in room not shown"). Source choice: the
  specs give no room-level fact (warps.md § D and LvlPrest § Warp slots are per-record DS1 surveys; the model's
  `warp_grid` is keyed by cell), and a copied Def-to-slot table would dump that survey and drift. So a narrow helper,
  `ds1.room_warp_slots(data)` in `tools/ds1.py`, runs the existing `_scan_cells` rule and returns a `frozenset` of
  slot numbers only; `maze_anim.warp_rooms()` is its one caller, mapping (room, slot) through Levels `Vis`; no cell,
  coordinate or layer reaches drawing code. `test_anim_schematic.py` blocks `_scan_cells` except under the helper,
  admits `parse` and the `layers` key to the helper (and `_scan_cells` reached through it) beside `PresetUnitData.ds1`,
  and checks the return is a frozenset of ints below 8. The two warp lines of the steps are now equal between the
  modes (`ART_LINES` keeps only the icon and name-card lines); the "ROOM NOT SHOWN" legend and the help line
  (`MARKS_SCHEM`) are reworded. Full mode: the unchanged command on `main` and on the branch gives 46 equal files.
  Rebuilt the cut (`export_build.py` into `workspace/export`): `export_check.py` 0 failures; `test_anim_schematic.py`,
  `test_export_check.py` (117), `test_export_build.py` (41) green. Looked at the final maze frame (level 36, seed
  0xC0FFEE): diamonds on R1 (entry, Catacombs Level 2) and R17 (exit, Catacombs Level 4). This is a second DS1 read
  in the schematic mode, so it needs an architect ruling under ADR-0036: review request filed in
  `docs/backlog/2026-11-17-archivist-architect-plan-0070-maze-schematic-warp-marks-review-request.md` (closed:
  `docs/backlog/archive/`).
- 2026-11-17 — **Maze warp marks review** (architect, Tier A, lane/x70w): **accept with fixes 1.**
  - **Ruling (second DS1 read).** Within ADR-0036, on the reading of the Phase 2b review's Ruling 1: the schematic
    mode may read a DS1 as model input when what leaves the read is a fact the drawing could state in a table, and
    no layout reaches drawing code. `ds1.room_warp_slots` reduces the wall layer to at most eight slot numbers per
    room; the frame shows which box holds a warp, which is what the ADR's "entry and exit marks" names, and no cell,
    shape or position. ADR-0036's wording is not amended: its "does not open ... DS1 tile layers" names what the mode
    must not draw from, and the two rulings here record the narrower reading. The rejected Def-to-slot table is worse:
    it would copy a DS1 survey into `tools/` as data (ADR-0009's dumps), drift from the files, and break the full
    and schematic modes' shared rule (`_scan_cells`), which is why their steps are now equal.
  - **Test.** Tight enough. Two probes on a scratch copy of `tools/`: `warp_rooms` calling
    `ds1._scan_cells(ds1.parse(...))` directly fails ("ds1.parse outside the preset-unit model blocked"), and a helper
    returning the slot dict (cells inside) fails ("must return slot numbers only"). Reran after merging `main`:
    `test_anim_schematic.py` OK (5), `test_export_check.py` 119 checks, `test_export_build.py` 41 checks, 0 failed.
  - **Full mode.** `main` and the branch, level 36 seed 0xc0ffee: the 46 full-mode files are byte-identical; the
    branch's full and schematic `steps.json` are equal (43 steps, no exception left in the maze).
  - **Fix 1 (legibility, `tools/maze_anim.py`).** The diamond at the box centre covered the room's DEF and F lines;
    it now sits in the box's lower right corner (radius min(w, h)/7, further warps of one room step left), the label
    stays centred over the box. The legend's "position in room not shown" stands, and a corner mark reads less like a
    position than a centred one would. Steps unchanged, full mode still byte-identical. Final frame (R1 entry,
    Catacombs Level 2; R17 exit, Catacombs Level 4) and the step-31 conversion frame looked at: boxes, doors, labels
    in our palette, no game pixel. Cut rebuilt (`export_build.py`, 25 pages, 0 dropped); `export_check.py
    workspace/export --repo workspace/export-repo/` 0 failures; the cut's maze frame 42 equals the review's run.

- **2026-11-17, Phase 7 step 2 (archivist, lane x70n).** The export repository is `arpg-1-14d-notes`. In
  `tools/export_check.py` the bare `https://github.com/igorkonovalov` and `https://igorkonovalov.github.io` prefixes
  are replaced by `RE_URL_ALLOW`, case-insensitive: `https://github.com/igorkonovalov/arpg-1-14d-notes` followed only
  by `/`, `#`, `?`, `.git` or the end, and the Pages host with the same name rule (the bare Pages host with no path
  also passes, as the site's own `site:` setting and the link script's `SELF`). `https://github.com/${` stays: it is
  the template literal in `astro.config.mjs` (account and name joined at build time), not a URL. Tests: this repository
  passes in both cases; the account's other repositories, a prefix-extended name (`-old`, `2`), the bare account and
  another account fail. Export repository (workspace): `check-site-links.mjs` named the account as two literals; it now
  has one `ACCOUNT` constant and a template, so the check passes with the narrowed allowance. `astro.config.mjs`,
  `README.md` and `pages.yml` need no name: `SITE_BASE` comes from `github.event.repository.name`, and the base and the
  repo URL follow from it. Rebuilt the cut; `export_check.py workspace/export --repo workspace/export-repo/`: 0 failures;
  `test_export_check` 119, `test_export_build` 41, 0 failed. Phase 7 checklist filled with the name; step 2 done.
- 2026-11-17 — **Phase 7 steps 3 and 4 run** (orchestrator, at the owner's request; the machine has npm through
  mise after all). The fresh folder `~/Work/arpg-1-14d-notes` (git init, no commit) holds `workspace/export-repo/` and
  the cut's `site/`. The first real build found three faults in the export repository's files, fixed in
  `workspace/export-repo/` and the folder: (1) `site/package.json` lacked `@astrojs/markdown-remark` 7.3.0, which
  Astro 7 needs for `markdown.rehypePlugins` (the owner's other site pins it); (2) the sidebar used Starlight's old
  `autogenerate` group with a `label`, removed in Starlight 0.39: each group is now `{label, items: [{autogenerate}]}`;
  (3) the link check found 27 problems: 26 pages linked `/favicon.svg`, which no file supplied, and the 404 page's
  canonical `/404/` (the page is `404.html`). A `site/public/favicon.svg` of our own (a plain square glyph) is added,
  and `tools/export_check.py` admits exactly that path, checked by shape (`favicon_problems`: ASCII, one `<svg>` root
  with the SVG namespace, only svg/rect/path/circle/g, no link, URL, script, style, image or handler; 6 new tests,
  125 checks); `check-site-links.mjs` skips own-host links on `404.html` only. Results: `SITE_BASE=/arpg-1-14d-notes/
  npm run build` 26 pages, 76 diagrams drawn (152 light and dark SVGs), Pagefind index, both GIFs under the base;
  `check-site-links.mjs dist`: 1490 links in 28 pages, all resolve; `export_check.py --repo`: 0 failures.
  `npm install` warns of 4 audit findings (3 low, 1 moderate) in the pinned tree and an unapproved esbuild
  postinstall; the build does not need it. Next: the owner's steps 5 to 7. The maze warp-mark lane (x70w) is still
  under review; when it merges, re-copy `workspace/export/site/` into the folder and rebuild.
- 2026-11-17 — **Phase 7 done: the first cut is served** at `https://igorkonovalov.github.io/arpg-1-14d-notes/`.
  Pages enabled with GitHub Actions as its source (orchestrator, `gh api`); the owner pushed `main` (an empty first
  commit) and the branch `cut-2026-11-17`; pull request 1's `build` job passed and the owner merged it; the `deploy`
  run on `main` passed, and the front page, a page with a diagram and the maze GIF answer 200. Owner feedback during
  the read, applied before the push: the schematic maze marks its entry and exit on the warp rooms (lane/x70w) and the
  main column is 60rem wide (`site/src/styles/site.css`). Next, on the owner's word: the second cut (Phases 9 and 10),
  whose prerequisite is the anchor rewrite noted at the Phase 3 review.
- 2026-11-17, archivist, lane/x70a (anchor rewrite, Phase 9 prerequisite). `tools/export_build.py` now rewrites
  anchors inside a unit (a sentence, a list item or quote, a table cell, a heading, a caption sentence) before the
  simplifier's drop test, as ruling (a) asks. `fn:`, `data:`, `tbl:` (with `.Column`/`:column`) and `fmt:` anchors, with
  or without `@0x…`, become `` `Name` `` when the name holds no hex run of 6+ digits, no `sub_`, no `DAT_` and nothing
  X1 to X5 would fail (it asks `text_rules`), else the whole token goes; an anchor already in backticks is not
  doubled. Removed whole: `struct:` tokens, `run:` and `src:` ids, finding ids (`items/0012`, with a slug, `#fragment`
  or `.md`) and links whose target holds `findings/` (label and all); the `sub_XXXXXXXX_` strip now runs after the
  rewrite, so `fn:sub_…_x` is removed, not turned into `x`. Clean-up works only next to a removal mark: an emptied cell
  becomes `—`, doubled list separators, empty or separator-only parentheticals, and "at", "see", "per" (also "and",
  "or") left before nothing go, and the spaces around the gap are closed. A unit left with no letters is dropped as a
  new rule `empty` (counted as a drop). Spec citations: `folder/file.md § X` becomes `file.md § X`, a folder path
  `.md` without a section (with a "spec" before it) is removed, and so is a bare `README.md` without a section; link
  targets are never touched. The citation rule was not ambiguous in the specs sampled, so both halves are in; the
  check is unchanged. Every rewritten unit is a report line `REWRITE<TAB>page<TAB>heading<TAB>before<TAB>after`
  (160 characters each), and the report header gains `rewrites: N`. Tests: `test_export_build` 74 checks (was 41), 0
  failed; `test_export_check` 125, `test_anim_schematic` OK. **Cut 1** rebuilt: 25 pages, check 0 failures, 330
  warnings as before; the pages read the same except one rewrite (the wiki monster-ai bullet on the Uber forced cases
  lost its link to a finding, whose label "G1, G2, G3 and G5" went with it); 1 REWRITE line. **Trial** (every spec
  with status `reviewed`: 65, groups `s-<folder path>` so that `monsters/` and `monsters/ai/` READMEs do not collide:
  20 groups; manifest and per-spec table in scratch, output in `workspace/export-trial-x70a/`, built with
  `--no-illustrations`): 90 pages, 19266 units, 4414 dropped; of the 65 specs 14120 units, **4408 dropped (31.2%)**
  (was 44.4%). Drops per rule: X1 3869, X3 901, X2 508, X5 214, X9 95, open-questions 63 sections, `parent` 16,
  `empty` 10; by kind (specs): 1636 list items, 1625 table rows, 705 fenced blocks, 417 sentences, 71 sections, 5
  tables. 2913 REWRITE lines. The check on the trial: **14 failures, all X6** (tables of 21 to 136 body rows the
  manifest does not name: drlg/maze 23 (line 314), drlg/outdoor 21 (68), items/properties 25 (224), items/vendors 36
  (334), monsters/ai README 23 (297), monsters/special 32 (178), quirks 26 (64), 73 (134), 136 (212), 94 (353), 22
  (476), 25 (505), 30 (541), 59 (598)), 814 warnings, no X1 to X5, X7 to X11. **48 of 65 specs are above 25%, 2 above
  50%**: rng/seeds 59%, drlg/lifecycle 53% (then save/d2s 46, monsters/ai/machinery 44, monsters/pool 44, anim/movement
  43, drlg/README 43, items/inventory 43, skills/catalogue 42, path/search 41, path/README 40, monsters/spawn 40,
  drlg/room-tiles 40, skills/missiles 39, quests/travel 39, stats/aggregate 39, drlg/warps 37, items/quest-drops 37,
  quests/progression 36, then 34% to 25%: combat/delivery, rng/README, sim/frame, items/affixes, objects/README,
  items/cube, drlg/preset, monsters/ai README, combat/damage, combat/README, player/creation, stats/README, items/tc,
  items/economy, anim/timing, drlg/maze, items/uniques-sets, items/sockets-runewords, monsters/special, items/use,
  skills/dispatch, monsters/ai/catalogue, drlg/collision, items/properties, items/vendors, chain/README,
  combat/reductions, drlg/outdoor, data/excel). What still drops is outside the rewrite: bare addresses and `+0x`
  offsets in prose, "plan NNNN" and ADR references (X3), and `[C] (0x…)` evidence lists in pseudocode fences (705
  fenced blocks). One reading flaw: a sentence whose removed link was its subject reads "takes 's reading" (a
  finding link inside a quotation); not handled. Next: the architect's Tier B check.
- 2026-11-17, architect, review of `lane/x70a` (Opus, Tier A rigour). **Verdict: accept with fixes (3: omission 2,
  other 1)**, fixed in this commit. (1) *Safety, omission:* the citation rule reduced any folder path with a section to
  its file name, so `findings/items/0012-x.md § 3`, `../plans/0070-….md § 3`, `docs/adrs/0031-….md § X` and
  `docs/backlog/….md § x` became bare file names that pass X3 (latent: none in the trial). A citation into a working-tree
  folder (`findings`, `plans`, `done`, `adrs`, `backlog`, `archive`, `re`, `tools`, `workspace`, `.claude`, `skills`,
  `references`, `export`) or of a numbered file is never reduced: without a section it goes, with one the unit drops.
  (2) *Reading, omission:* about 350 of the 2913 rewrites left a unit that no longer read whole: an item whose head
  before the colon went (`-: the CRC check.`, 185), `Findings:.`, a removed possessive (`takes 's reading`, the lane's
  flag), a removed object or complement (`the classic session of resolved`, `this is ;`). These now drop under a new
  rule `broken` (the report's after-text reads `(dropped: broken)`): a removed token before `:` at the unit's head, before
  `'s`, after a determiner, `is`/`are`/`was`/`were`/`be` or `with`/`to`/`under`/`on`/`for`/`into`/`through`/`between`/`than`,
  after `of`/`from`/`in`/`by`/`via` with words following, a label whose list went, or one followed by `(`. "of", "from",
  "in", "by", "via" before punctuation go with the token, like the lane's "at"/"see"/"per". (3) *Other:* separators
  left at a cell's or a sentence's start (`| , K3 |`, `[C], 994 022 draws`), `(: x-talk2)` and arrow-only cells
  (`| → → |`, now `—`). Tests: `test_export_build` 100 checks (was 74), the lane's four expectations that encoded a
  flaw corrected; `test_export_check` 125, `test_anim_schematic` OK. Rulings: the lane's extensions ("and"/"or" as
  dangling words, `empty`, the `sub_` strip after the rewrite) are accepted; *The pick, holds.* (a removed apposition) is
  accepted unfixed, it changes no meaning. **Checks.** Fresh trial (`workspace/export-x70a-review-trial3`, the lane's
  manifest): 14 failures, all X6 as before, 794 warnings; spec units 14124, **4642 dropped (32.9%**, the lane's 31.2%
  plus the 414 `broken`); 50 of 65 specs above 25%. Cut 1 (`workspace/export-x70a-review-cut1`, `--repo
  workspace/export-repo/`): 0 failures, 330 warnings; its text differs from the served cut by the lane's one rewrite
  only. Hand greps of the trial: no `sub_`, `DAT_`, `src:`, `run:` id, `struct:`, `fn:`, `/00`, plan or ADR reference;
  hex of 6+ digits only the five allowlisted values; `findings` only as a plain word (3); `.md §` only spec and format
  names; but 20 `.log` names and one `0x0063xxxx`, which the check lets pass (Phase 9's *Before the cut* now asks for
  them). **Residue** (every failing spec unit of the trial captured whole, 4191, and classified by what fails; recovery
  simulated with a prototype of each rule and the `broken` test, then discounted 15% for the reading misses a sample of
  14 showed). The units measure hides the worst loss: **639 of the 651 pseudocode blocks drop** (the head line's
  `[C] (fn:…@0x…, run:…)` evidence alone fails it), and by words the specs lose 51.6%, not 32.9%. Safe classes, all
  removals: evidence tails on pseudocode lines (+183 units, all blocks), code-image addresses as tokens in prose, items
  and cells (+764), plan, ADR and lane references (+115), repository paths and `.py`/`.csv`/`.log` names (+82), a cell
  made only of `+0x` offsets becoming `—` (+76): about 1040 units after the discount, the share to about 25.7%, 33 specs
  at or under 25%. Rule changes: X5 read our set braces and `(unsigned)` notes as C (+54, an architect ruling on the
  check); worked-example seed values in specs (`9d613dad:1dba1b44`, ~560 units, an allowlist widening: the owner's);
  in-memory `+0x` offsets in text (~1400 units, ADR-0009's risk (1) as the owner approved it: the owner's). Measure the
  bar in words of the body, not units, and count a spec whose pseudocode blocks dropped as not whole. **Recommendation
  A**: a second redactor round with the safe classes and the X5 ruling, then measure again; B today would publish 15
  specs (7 by words), none with its pseudocode. Ledger: verdict accept with fixes, 3 (omission 2, other 1).
- 2026-11-17, archivist, lane/x70b2 (second redactor round; owner decisions on offsets and worked-example seeds).
  **Check** (`tools/export_check.py`): (1) an in-memory struct offset passes X1: `Name+0x10`, a chain `Name+0x10+0x4` and a
  bare `+0x1C` (up to 5 hex digits); 6+ digits, an offset on a `sub_`/`DAT_`/`FUN_`/`PTR_` name and every code-image
  value in any spelling (`0x00…`, `@0x…`, bare 8-digit, bare 6-digit with a letter) still fail; bare offsets: both tried,
  a bare `+0x1C` passes (a table column of offsets is content; only 6+ digits is image-shaped). (4) X5 narrowed (the
  architect's ruling): a brace fails only as a lone `{`, a line starting with `}` or ending in `{`; a cast only as a
  pointer cast or glued to its operand, so `(unsigned)` and `(int32)` notes pass; `goto` only with `LAB_`; `*(` only
  with a type and `*`; a line ending in `;` only when it also assigns with `=` from the line's start, declares a type or
  compares with `==`/`!=`/`&&`/`||` (our `;` separators and `=` as equality pass). (5) New fails: a `.log` file name
  (`console.log` of the export repository's JS excepted, tested beside `run.log`), a partial address (`0x0063xxxx`,
  `0x4xxxxx`, `0x006XXXXX`) and a `.claude` path. **Builder** (`tools/export_build.py`): (3a) a pseudocode line's tail is
  rewritten (the evidence parenthetical goes, an anchor becomes its bare name, a trailing `; … 0x…` or `// …` evidence
  comment goes, a comment marker or label left empty goes, the `[C]`/`[I]` tag stays, as in prose); a removed token in
  the code part leaves the line as it was and the block drops; (3b) code-image addresses, partial addresses and `@0x…`
  go as tokens (`at` goes with them; a removed subject, a token before a dash or `=`, a determiner or `run`/`using`/
  `above`/`outside` before it is `broken`; a pinned value of the page stays); (3c) `plan NNNN Phase x`, `ADR-NNNN` and
  `lane/x` go; (3d) repository paths and `.py`/`.csv`/`.log` names go (a backticked span holding one goes whole); (3e) a
  cell of addresses only is `—`. A heading keeps its words when a token goes (it was dropping whole sections:
  "The ADR-0014 boundary"). A link fragment whose slug carries a hex run is dropped (a worked-example heading kept under
  an allowed section would put its seed into the linking page). The offset-only parenthetical is content now.
  **Measure:** the report gives per page and in total units dropped, **words dropped** (body words, evidence tokens not
  counted as words) and **fenced blocks kept/total**, and a `specs:` total. Tests: `test_export_build` 137 checks (was 100),
  `test_export_check` 136 (was 125), `test_anim_schematic` OK, 0 failed. **Allowlist:** 58 `section` lines
  `section specs/<path>.md Worked example :: …` (every spec of the trial manifest with a `## Worked example`: anim/movement,
  anim/README, anim/timing, chain/README, combat/damage, combat/delivery, combat/README, combat/reductions, combat/to-hit,
  data/calc, data/excel, data/strings, drlg/collision, drlg/lifecycle, drlg/maze, drlg/outdoor, drlg/preset, drlg/README,
  drlg/room-tiles, drlg/warps, hirelings/README, items/affixes, items/cube, items/economy, items/inventory,
  items/properties, items/quality, items/quest-drops, items/sockets-runewords, items/tc, items/trade,
  items/uniques-sets, items/use, items/vendors, monsters/ai/catalogue, monsters/ai/machinery, monsters/ai/README,
  monsters/pool, monsters/spawn, monsters/special, monsters/stats, objects/README, path/README, path/search,
  player/creation, player/party, quests/progression, quests/travel, rng/README, rng/seeds, save/d2s, sim/frame,
  skills/catalogue, skills/dispatch, skills/missiles, skills/README, stats/aggregate, stats/states); the sections cover
  their `### Example n` children. No `pin` added; none admits an image-range value. **Cut 1** (`workspace/export-x70b2-cut1`,
  `--repo workspace/export-repo/`): 0 failures, 330 warnings. Three pages differ from the main build: the glossary (31
  lines now keep their `Name+0x…` offsets, which were dropped as evidence parentheticals; the wiki had offsets in
  parentheticals only), and the captions of `world/levels` and `items/items`, which lost a `(tools/….py)` parenthetical
  and so keep their sentence (it was dropped before for the file names). **Trial** (65 specs, `--no-illustrations`,
  `workspace/export-trial-x70b2`): 90 pages, check **24 failures, all X6** (14 before: the tables that survive more
  rows now pass the 20-row bar), 1037 warnings, no X1 to X5, X7 to X11. Specs: **units 1160/14172 dropped (8.2%; was
  32.9%), words 85292/416438 (20.5%; 16.3% without the Open questions sections, which hold 20583 words), fenced blocks
  kept 867/1000 (was 12/651)**. Drops per rule (all pages): X1 235, X2 7, X3 8, X5 1, X9 75, broken 837, empty 13,
  Open questions 63 sections. **51 of 65 specs at or under 25.0% words dropped** (data/strings is 25.05%), 50 of them with most pseudocode blocks
  kept (skills/catalogue keeps 3 of 21: its blocks carry bit-mask constants). Over 25% (13): rng/seeds 60, rng/README 49,
  drlg/room-tiles 46, combat/README 34, save/d2s 31, stats/aggregate 30, stats/states 29, stats/README 28, drlg/preset 27,
  drlg/lifecycle 27, drlg/collision 27, drlg/README 26, items/use 26; main reasons `broken` (evidence items and lines
  whose subject was a removed token) then X1. **Residue**: (a) 162 units fail X1 on non-image hex that is game math,
  not a seed: bit masks and magic constants (`0x7FFFFFFF` 32, `0x100000` 30, `0x80000000` 17, `0xFFFFFFFF` 12,
  `0x1000000`, `0x2000000`, `0x200000`, `0x40000000`, `0xAAAAAAAB`), mostly in pseudocode blocks and the long
  Algorithm items of rng/seeds and drlg/room-tiles: an allowlist widening, the owner's; (b) 75 units keep an image-range
  value (the address as a call target in pseudocode, `r ← 0x00588D60(&u)`; a worked-example seed in the image's range
  is removed by the rewrite as an address, so such an example loses its value unless it is pinned); (c) X9 75 units
  (tool names in prose: Ghidra, logger, harness, Battle.net, disassembly). Hand greps of the trial: no `sub_` or `DAT_`
  name, no `findings/`, `plans/`, `.py`, `.log`, `.claude`, `lane/` or plan reference; `0x00` followed by 5 hex
  digits only as values out of the image (`0x00082010` flags, `0x0000029A`, `0x00000055`); 3 `fn:` lines and 2 `src:` lines, all
  pseudocode parameters (`hitfn(…)`, `src: object`) or the word "`fn:`" quoted in a sentence (they pass X2); `run:` only
  as the word (50 lines); one `ADR` word ("that ADR excludes…", a reading flaw: the sentence kept its pointer word);
  no partial address. Per-spec table: `/tmp/claude-1000/-home-igor-Work-recompilcation-project/eb61de30-a30a-401a-a3db-30c67be2439b/scratchpad/x70b2/per-spec-table.txt`.
- 2026-11-17, architect, review of `lane/x70b2` (Opus, Tier A rigour). **Verdict: accept with fixes (4: omission 3,
  other 1)**, fixed in this commit. (1) *Safety, omission:* other spellings of an image value passed X1: `0X004A1B20`
  and `0X4A1B20` (the rules matched lowercase `0x` only), MASM `4A1B20h`, `0x0045_1B20`, a partial `0x0063????` (the
  trailing `\b` never matched after `?`), and an offset from the image or a module (`Game.exe+0x5C00`, `image base +
  0x1A2B3`, `D2Common.dll+0x1234`: an address of the image below `0x500000` written as a 4- or 5-digit offset). All fail
  now; `Game+0x10F4` and `base +0x114` (structs) pass, and a flag in a question (`0x40000?`, `0x66?`, two mermaid
  blocks) is no partial address: a partial needs 6 to 8 places and `x` or `??` placeholders. The lane's other cases
  hold: `+0x4A1B20`, `Name+0x0045ABCD`, `base+0x5C0000`, `sub_`/`DAT_`/`FUN_`/`LAB_`/`PTR_` with or without an offset
  fail; a bare 5-digit value (`4A1B2`, `Name+0x4A1B2`) is below the image and passes. Decimal spellings (`4856608`) stay
  out of reach of any rule. (2) *Safety, omission:* X5's narrowing let C lines through: compound assignments (`x += 3;`,
  `x |= 0x10;`), `unsigned int`/`struct Unit *` declarations, `DWORD dw;` (the rule read `[DW]ORD`, not `DWORD`),
  `--i;`, a bare call or `return x;`, a C comment after the `;` (`x = 1; // c`) and a one-line block (`if (x) { y = 1;
  }`). They fail now; our `;` comments (`r.init(game, unit, &blk)     ; blk laid out …;`), `&=`/`|=` without `;` and
  `type Seed { low: u32; high: u32 }` pass: the trial keeps the lane's 867 of 1000 blocks. (3) *Reading, omission:* the
  owner's offsets decision left `struct:Game+0x6A` removed as evidence; it becomes `` `Game+0x6A` `` as an anchor
  becomes its name (one with hex in its name or a 6+ digit offset still goes). (4) *Reading, other:* a statement cell
  broken by the new address class became `—`, which reads as "none": "Q80 | —" in quirks, "The collision test
  `0x0064FF90`'s result per crossed subtile" → `—`. A broken cell with 3+ words of its own that does not open with its
  evidence (a tag, an anchor, a run id, an address) now drops the row (`broken`, 53 rows in the trial); an evidence
  cell is a dash as before; a header row never breaks. The lane's two unrequested fixes are accepted (a heading keeps
  its words; a link fragment carrying a hex run is dropped). Tests: `test_export_build` 141 (was 137),
  `test_export_check` 160 (was 136), `test_anim_schematic` OK. **Checks.** Cut 1 (`workspace/export-x70b2-review-cut1`,
  `--repo workspace/export-repo/`): 0 failures, 330 warnings, identical to the lane's cut; the glossary's kept offsets
  are 36 tokens on 31 lines, all game structs (`Unit`, `ItemData`, `MonsterData`, `PlayerData`, `Game`, `level`,
  `drlgRoom`, `activeRoom`, `path`, `StatList`, `QuestControl`, `NpcStoreCtl`, `MonRegion`, `AiCtl`, `act`). Trial
  (`workspace/export-x70b2-review-trial2`, the x70a manifest): 24 failures, all X6; specs units 1210/14172 dropped
  (8.5%), words 86243/417111 (20.7%), fenced blocks 867/1000; 49 of 65 specs at or under 25% words. Sections: all 58
  spec sections read; each admits only its `Worked example` heading and its children (scope ends at the next `##`);
  about 1300 admitted tokens, seeds `hi:lo`, draw lows and computed flags, none in the image's range (those the rewrite
  removes, as the lane says). Two kinds to read at the Phase 9 sample: drlg/collision's example names rooms by heap
  pointers (`0x035A5600`, `0x02DCAB00`, not image values) beside "the `CB` line 8034", a log line; drlg/lifecycle's
  flags `0x05382000`. Hand greps of the trial: no `sub_`, `DAT_`, `FUN_`, `LAB_`, `PTR_`, `.py`, `.log`, `.claude`,
  `/home`, repository name, `Ghidra`, `harness`, plan reference; `0x00` only as short or out-of-image values;
  image-range tokens only the four `pin` values of the wiki pages; `fn:` 3 and `src:` 2 (pseudocode parameters), `run:`
  47 (the word), `findings` 3 (the word), `ADR` 1 (the lane's "that ADR"). X9 does not list `objdump` (49 lines) or
  `r2` as the tool ("by objdump and r2 alike"; most of the 119 `r2` are variables), nor `debugger` (4): tool names in prose,
  a reading for Phase 9 (`breakpoint`, 27, is the game's frame-breakpoint term). Ledger: verdict accept
  with fixes, 4 (omission 3, other 1).
- 2026-11-17, architect, **Phase 9: the second cut's redaction review** (Opus, Tier A, `lane/x70p9`). Verdict
  **accept**; Phase 9 done, Phase 10 (the owner) next. **Decisions recorded** (owner, 2026-11-17, not reopened):
  in-memory struct offsets pass; worked-example seed sections admitted (x70b2); pure-arithmetic hex constants admitted as
  `value` lines (limits and masks, powers of two, compiler division reciprocals, the two well-known LCG constants), domain
  values stay out; every plan 0070 review on Opus; the main column 60rem; code-image addresses fail everywhere. **Bar
  used:** the builder report's words dropped per page, Open questions sections counted, over 25.0 % stays out; a page
  whose pseudocode blocks mostly went, or that describes our method or carries provenance throughout, stays out.
  **Cut:** 2026-11-17, `python3 -I tools/export_build.py` (default `--out workspace/export`, illustrations run) from
  this branch: **71 pages** (the 25 of cut 1 and 46 specs), 0 dropped, both illustration folders (`drlg-maze-level36`,
  `items-tc-andariel-hell`); 15 spec groups after the wiki's six. Report: specs units 764/9662 dropped (7.9 %), words
  48086/281696 (17.1 %), fenced blocks kept 590/621; all pages 772/14834 units, words 12.3 %; drops per rule X1 46, X2 1,
  X3 5, X6 3, X9 58, broken 534, empty 9, Open questions 44 sections, parent 1; 3184 rewrites. **Check:**
  `export_check.py workspace/export --repo workspace/export-repo/`: **0 failures, 863 warnings** (all X12: 19 quoted runs,
  the rest capitalised names; exit 0). Self-tests: `test_export_check` 180, `test_export_build` 149, 0 failed.
  - **X12 read.** 311 distinct capitalised names: areas, skills, items, monsters, runes (`Lum Eth`, `Ko Ko Mal`) and
    hireling classes; no string-table text. The 19 quoted runs: 12 page titles (the front matter's quoted `title:`), the
    rest spans between two short quotes (cube 18, progression 155, quirks 156, sim 754, pathing and server-frame as at
    cut 1).
  - **Specs added (46):** data/README, data/excel, data/calc; drlg/README, drlg/lifecycle, drlg/preset, drlg/maze,
    drlg/outdoor, drlg/warps; monsters/README, monsters/pool, monsters/special, monsters/stats; monsters/ai/machinery;
    items/tc, items/quality, items/affixes, items/uniques-sets, items/properties, items/sockets-runewords,
    items/quest-drops, items/cube, items/economy, items/trade; player/README, player/creation, player/party;
    hirelings/README; combat/to-hit, combat/damage, combat/reductions, combat/delivery; skills/README, skills/dispatch,
    skills/missiles; anim/README, anim/timing, anim/movement; path/README, path/search; sim/frame; quests/README,
    quests/progression, quests/travel; chain/README; quirks/README. The highest kept share is combat/to-hit 24.3 %.
    Groups `spec-<subsystem>` labelled "Spec: Items" etc., orders 11 to 28; a spec `README.md` takes the route stem
    `overview`, so `monsters` and `monsters/ai` do not collide (`spec-monsters/overview`, `spec-monster-ai/…`).
  - **Left out (19 of 65), by words dropped:** rng/seeds 59.7 %, drlg/room-tiles 44.1, stats/aggregate 38.9, rng/README
    35.9, stats/states 34.9, combat/README 33.7, items/inventory 32.8, monsters/ai/README 31.4, items/use 30.4, save/d2s
    29.7, stats/README 28.4, objects/README 27.7, items/vendors 27.1, drlg/collision 25.9, monsters/spawn 25.6,
    data/strings 25.05 (16). **Not whole:** skills/catalogue (20.1 % words, but 3 of its 21 pseudocode blocks kept: code
    addresses as call targets); conformance/README (a guide to running our trace set and checker, which the export does
    not ship; its command row dropped). **Provenance:** monsters/ai/catalogue (21.4 %, but about 90 rows say "The block
    was checked against its anchored instructions (the finding's prose agrees)"). The loss is mostly `broken` units
    (a run id, plan or ADR reference or address as a subject) and tool words mid-claim, plus the Evidence and Open
    questions sections. What readers lose: the RNG and seed-tree specs (the wiki's randomness page stays), the stats
    specs, the save format, the room spawn pass; wiki links to them keep their text and lose their target (checked on
    randomness: "two specs: the RNG core and the seed tree."). The 1741 relative links of the cut's pages (the front page's included) all resolve to a page.
  - **X6 rulings** (the 24 of the trial; ruling (d)): *named* with a reason (16 lines): drlg/maze 709 (worked-example
    steps), drlg/outdoor 124 (our index of the constant tables: names and shapes, no values), items/cube 1017 (worked
    example 1), items/properties 410 (handlers per func), monsters/pool 53 and monsters/special 58 (column indexes, a
    schema), path/README 62 (the path record's fields, offsets by the owner's decision), quirks 77, 108, 149, 233, 382,
    522, 555, 585 (our quirk entries), skills/dispatch 1014 (stat-event handlers). *Left out*: monsters/special 381 (its
    `Weights` and `xfer` columns copy MonUMod's `upick`/`cpick`/`fPick`/`exclude`/`xfer`/`enabled` for every mod: table
    content, ADR-0009 risk 3), quirks 673 (community-claim verdicts: third-party claims and our cross-check) and 730
    (coverage of the specs: repository bookkeeping). Ruled on pages left out: items/vendors 658 out (the gambling list by
    level: item-table content), monsters/ai/README 536 out (a per-think evidence record); objects/README 51, save/d2s 315
    and 1252, skills/catalogue 151 would be named. *Treatment of an unnamed table:* the builder ignored `table` lines and
    the check counted allowed tables per route, so a left-out table failed the cut. Now the builder reads each `table`
    line's source header line and drops, whole and with a report line (`X6`, the row count, the source line), a table
    still over 20 rows after redaction that no line names; a line that names no table is a report line (`unmatched`).
    Readers lose special § D's per-mod draws (its handlers and draws per mod; the prose bullets around it stay), the
    quirks' community verdict list and coverage table.
  - **Allow-hex lines added (32 values):** limits and masks `7FFFFFFF`, `FFFFFFFF`, `0FFFFFFF`, `F0000000`,
    `FFFF0000`, `FFFFFF00`, `FFFFF000`, `1FFFFF`, `3FFFFFF`; powers of two `100000`, `200000`, `1000000`, `2000000`,
    `4000000`, `8000000`, `10000000`, `20000000`, `40000000`, `80000000` (`0x400000` and `0x800000` are in the image's
    range and the loader refuses them); reciprocals `AAAAAAAB`, `55555555`, `55555556`, `CCCCCCCD`, `66666667`,
    `24924925`, `38E38E39`, `88888889`, `68DB8BAD`; LCG `19660D`, `3C6EF35F`. Left out as domain values: `0xD17D0000`
    (a logged seed word), `0x01020304`, `0x80001FFF`, the flag masks `0x3F0FF80`, `0x1E0FF00`, `0x3F0FF00`, `0xFFF800FF`,
    `0x3000000`, `0x4020000`, `0x402000E`, `0x4020200`, `0x2001002`, `0xC00010`, the theme values `0x120000`,
    `0xA00000`, `0x1600000`, the four-character codes (`0x20786168`, `0x53454953` …), `0x0213AE09`, `0x0BADF00D`,
    `91fdb5f0`.
  - **X9 change:** `objdump`, `debugger` and the plurals `loggers`, `harnesses` fail; `r2` fails in a tool's shape
    only (beside objdump, Python, Ghidra or "bytes"; after "by"/"with" unless an assignment follows; as the subject of
    reads, gives, finds, lists, walks, LCG, pushes, sites, beside, alike): 12 tool and 6 variable cases tested
    (`r2 ← aip(5)`, `r1 and r2`). This drops four units of the served wiki (inventory's tag legend row "Seen in a game"
    and two forced-case sentences, game-data's start-up sentence, all for "debugger"): reworded in the backlog entry
    below, before Phase 10.
  - **Tools, other changes:** (1) a `page` line's optional fifth field names the route stem (builder and check); (2) a
    parenthetical right after a `[C]`/`[I]` tag that, once rewritten, still fails a text rule (a tool name, an address,
    a path) goes whole and the statement stays; a table cell that opens with its tag keeps the tag alone in that case;
    a passing one stays (4 tests). It recovers 38 units the new X9 names would have dropped. (3) A bare identifier
    mixing letter cases (`deadD2`) is a name, not hex, unless its value is in the image (2 tests). Ledger: tools fixes
    6, omission 3 (the X9 gap, its plurals, the unnamed-table drop), other 3 (the route stem, the tag evidence rule,
    the identifier).
  - **Sample read (six specs).** Every drop line of items/tc (20), items/quality (11), drlg/maze (9), drlg/lifecycle
    (16), monsters/special (13) and, from the trial with every spec (`workspace/export-x70p9-a`), drlg/collision (37,
    left out); items/quality read whole; the worked example of drlg/lifecycle read whole; the drops of every spec read
    as counts. The drops are evidence items, Evidence-section link lists, run-sourced sentences, Open questions, and
    claims whose subject was a run, plan or tool (items/tc B1's writers, F1/F2's multiplayer facts; lifecycle's 31 pin
    sites): the spec-writer can reword those. items/quality reads whole: purpose, tables, every step and step note,
    the test table, draw order and outputs; method words the plan keeps ("logged", "the model", "reproduce") stand, as
    at cut 1. Lifecycle's `0x05382000` → `0x05282000` is a worked-example value (the room's DRLG flags in our example
    session, outside the image), inside the owner's section scope: passes. Collision's heap pointers beside "the `CB`
    line 8034" are log artefacts; moot while it is out, routed for its return. Kept but noted (within the approved
    design, for the owner's read): small whole tables of game data pass the 20-row rule (items/quality's six ItemRatio
    records with their values); runtime-state rows naming registers ("EAX at entry"); ~25 sentences on 13 kept pages name
    our records without a tie ("queued for the archivist in the backlog", "(architect review, 2026-10-19)", "not in a
    finding", overview READMEs' `reviewed` status columns).
  - **Hand greps of the cut** (all 71 pages): `sub_`/`DAT_`/`FUN_`/`LAB_`/`PTR_` 0; `0x00[4-9]xxxxx` 0; 8-digit values in
    the image's range 2, the two wiki pins; `fn:`/`src:`/`run:`/`data:`/`struct:`/`tbl:` ids 0; `findings/`, `ADR-`,
    plan NNNN, `.py`/`.log`/`.claude`, `/home`, the repository name, `lane/`, Ghidra, harness, objdump, debugger,
    logger(s): 0; `r2` as a tool 0 (one "by r2:" found and fixed above); "emulator" 31 and "logged" 1007 (method words
    the plan keeps; not tool names).
  - **Backlog:** [entry](../backlog/2026-11-17-architect-spec-writer-plan-0070-cut-2-export-readiness.md) to the
    spec-writer: the 19 left-out specs' export-facing wording, the residue sentences, monsters/special § D's two copied
    columns, the four wiki units (before Phase 10), collision's example.
  - **For the owner (Phase 10):** read the cut at `workspace/export/site/src/content/docs/` and `report.txt`; copy
    `site/src/content/docs/`, `site/public/illustrations/` and `site/src/cut.json` over the export repository's; the
    sidebar's new groups come from `cut.json` (no change to `astro.config.mjs` expected; the build and link check run
    in CI). The four wiki units above drop from the served pages until the spec-writer rewords them; publishing before
    that loses them.
- 2026-11-17 — **Second cut built** (orchestrator). On `main` after the x70p9 merge: `export_build.py` 71 pages (0
  dropped), 3882 report lines (3184 rewrites); `export_check.py workspace/export --repo workspace/export-repo/` **0
  failures**, 863 warnings (X12). In the export repository (outside this one; its project files unchanged): branch
  `cut-2026-11-17b` from `origin/main` (PR 1's merge), the cut's `site/src/content/docs/`, `site/public/illustrations/`
  and `site/src/cut.json` copied over; `SITE_BASE=/arpg-1-14d-notes/ npm run build` passes (74 pages);
  `check-site-links.mjs dist`: 7790 links in 74 pages, all resolve. One commit, 67 files. Ledger rows for x70a, x70b2,
  their reviews and x70p9 are in. Points for the owner's read (Phase 10): items/quality carries the whole six-row
  ItemRatio table with its values (under the 20-row rule; ADR-0031's "short illustrative rows" read narrowly would cut
  it); about 25 sentences on 13 spec pages name our own records without a tie ("queued for the archivist", a review
  date, `reviewed` status columns); register names such as "EAX at entry"; the four wiki units the new X9 words drop.
  All four are in the spec-writer's backlog entry for the next cut. Phase 11 (animations and interactive elements) is
  added above, at the owner's request.
- 2026-11-17, archivist, lane/x70pub (ADR-0038: tools/export_publish.py). The one-command publish is built with
  `tools/test_export_publish.py` (35 checks, 0 failed; build 149 and check 180 still green). Dry run on a copy of the
  export checkout (main fast-forwarded, no push): build and check 0 failures, link check 7790 links in 74 pages all
  resolve, one commit `docs: cut 2026-11-17`, and its tree equals the `cut-2026-11-17b` branch (empty diff).
- 2026-11-17 — **Review of lane/x70pub (architect, Opus): accept with fixes 1.** Read `tools/export_publish.py`
  whole against ADR-0038: the push guard refuses `--push` under `CLAUDECODE` or `CLAUDE_CODE_ENTRYPOINT`; the target
  must be on a clean `main`, fast-forwarded and never diverged; every manifest page must be in `reviewed-pages.txt`;
  the build and check stop on a non-zero exit (`export_check.py` returns 1 on any failure); the cut's two folders are
  replaced wholesale, project files mirror deletions only in four folders, `.git`, `node_modules` and `dist` are never
  touched; staging is by explicit paths, deleted ones included; the commit takes the target's own identity, with no
  trailer; re-running after a commit pushes only. The dry run on a copy reproduced the `cut-2026-11-17b` tree exactly.
  Fix: a failure after the copy (npm, site build, link check) left the target dirty with no hint, and the next run
  refused it; those messages now print the commands that restore the target (`reset`, `checkout`, `clean -fd`, which
  keeps the ignored `node_modules` and `dist`). Tests 35, 0 failed. Ledger: accept with fixes, 1 fix: omission 1.
- 2026-11-17, architect, lane/x70i (Phase 11 candidates and the widget ADR). Phase 11 steps (1) and (2) written, both
  **awaiting the owner's acceptance**. The candidate list (Phase 11, *Candidates*): 40 rows and the schematic kit, 24
  pre-rendered animations, 2 static pictures and 14 scripted widgets, in four batches; batch 1 is the kit, six new
  generators (the RNG steps, the seed tree, the quality ladder, the special-monster roll, the frame timeline, the
  server tick) and two new blocks on `tc_anim.py` and `maze_anim.py`, all under ADR-0036 with no new rule.
  [ADR-0037](../adrs/0037-scripted-widgets-in-the-export.md) (proposed): a widget is a hand-written, self-contained
  JavaScript module kept and tested in `tools/widgets/`, reading only a hand-written JSON of rules and at most 20
  `toy` or `page` rows, copied into the cut beside a fallback picture and loaded by one generic host step and a CSP
  `<meta>` in the export repository; a new check rule X13 and gate rule E21 (parity with the Python twin under node).
  No tool or widget is written in this lane.
- 2026-11-17 — **Owner accepts Phase 11's candidate list and ADR-0037** ("1 yes / 2 yes / 3 acceptable / 4 ok / 5
  yes"): the list and batch order (batch 1 first), the ADR as written, the one-time change to the export repository's
  files (prepared in `workspace/export-repo/`; ADR-0038's script copies it), widget data of `toy` and `page` rows at
  most 20 per array, and gate E21 needing node (skipped with a warning without it). Next: batch 1 (archivist lane, then
  a spec-writer lane for blocks and captions) and, in parallel, the widget groundwork of ADR-0037 (check X13, gate E21,
  the builder's widget block, the export repository's host step), each reviewed on Opus.
- 2026-11-17 — **Phase 10 done: the second cut is served.** The owner ran `tools/export_publish.py --push` in their own
  terminal (ADR-0038's first real run): 71 manifest pages listed, check 0 failures (863 warnings), 11 project files and
  the cut copied, site build and link check green (7790 links in 74 pages), commit `docs: cut 2026-11-17` on the export
  repository's `main`, pushed; the Pages run passed, and `spec-items/tc/` and `spec-monsters/overview/` answer 200. The
  branch `cut-2026-11-17b` is superseded (same tree) and can be deleted.
- 2026-11-17, archivist, lane/x11a (Phase 11 batch 1 part 1: the kit, rows 1–4). **Row 0, the kit:**
  `tools/schematic_kit.py` (a new module beside `anim_common.py`): class `Kit` (rect, outline, lines and arrows,
  text at any scale, labelled box, cell grid, proportion bar in integer arithmetic, number tape, legend, caption
  strip), the dark and light value sets of ADR-0036's palette (same names, same order; dark is `anim_common.SCHEM_UI`
  unchanged, so the two earlier tools' palette stays), `fill_rect`/`outline_rect`, and `write_illustration` (PNG with
  marker, GIF, step page, steps.json, schematic.json). **Byte-identity proof:** `maze_anim.py` (its box and outline
  helpers) and `tc_anim.py` (`Canvas.rect`, `frame_rect`) now call the kit's rectangle functions; sha256 of all
  138 files of `maze_anim.py 36 0xc0ffee --schematic` and `tc_anim.py andariel 0xc0ffee --difficulty 2 --mf 200
  --schematic`, before and after the refactor and after the `tc_anim.py` stack-row change below: identical (diff of the
  two sorted hash lists empty). **Row 1:** `tools/rng_anim.py` (seed 12345, 8 draws of range 100; the first draw 87
  and the new seed `{015b2e77:0000141d}` are the randomness page's worked example; values from `rng.rng_range`,
  the displayed product asserted equal to `rng.step`). **Row 2:** `tools/seedtree_anim.py` over `drlg.Act` and
  `drlg.Seed` (the five acts, three levels as a sum, three rooms as one draw each); for seed 12345 the model's tree
  equals the seeds.md worked example (base `015b2e77`, tombs 72/71, act seed `b7a5c418:63a93a78`, level 1
  `015b2e78:0000029a`, room draws `f61e44f2`, `f3cffcc1`, `6b277fa8`, room 3 `f923bee2:2cb17800`; a test).
  Both new tools take `--theme dark|light`, take the data root first and ignore it, and are in `SCHEMATIC_TOOLS`
  (and `test_export_build`'s assertion of the tuple). **Row 3:** `tc_anim.py` already had `--players`; one change:
  the stack row shows a scaled NoDrop as `ND a>b` (the table's value and the pick's scaled one) when they differ, so
  the one-player output is unchanged and the eight-player frames show NoDrop shrinking (19 to 0 for Andariel's own TC
  at n = 4). **Row 4:** `maze_anim.py 47 0xc0ffee` (Sewers Level 1) opens with a ring start shape (the 36 block's
  is the two-arm Catacombs shape) and has 3 theme assignments for 14 rooms against 4 for 17 (maze § H1); no code
  change. **Tests:** new `tools/test_schematic_kit.py` (15 tests: palettes, contrast of text colours in both themes,
  widgets, determinism of each tool, numbers equal to the models and the seeds.md anchor, marker and file list,
  `export_check.verify_illustration` clean on every folder, no art decoder imported, tc scaled NoDrop equals
  `tc.nodrop_scaled` at n = 4, level 47 ring and theme count); `test_anim_schematic`, `test_export_build`,
  `test_export_check` green. **Findings for the review:** (1) the check's `html_problems` URL rule matches `ws:`
  inside any word ending in "ws" followed by a colon ("draws: ..." fails as "external URL"): the seed-tree text avoids
  it, the rule is the architect's and is not narrowed here; (2) the dark palette's `dim` and `bad` reach contrast 4.37
  and 3.82 on the panel colour (earlier tools' values, left alone). **allow-hex:** no line added (`0xC0FFEE`,
  `6AC690C5`, `0000029A` and `00003039` were present; frames carry hex only as pixels, texts use decimals and
  `{low:high}` states). **Blocks:** the proposed `illustration` blocks of rows 1–4 with draft captions are in
  `workspace/phase11/blocks-batch1.md` (gitignored; moved there and corrected at the review below)
  (ids `rng-seed-12345`, `rng-seed-tree-c0ffee`, `items-tc-andariel-hell-8players`, `drlg-maze-level47`) for the
  spec-writer lane. Not done: a cut build with the blocks placed (the spec-writer places them).
- 2026-11-17, architect, review of lane/x11a (Opus, Tier A): **accept with fixes**, 9: misread 2, overclaim 1,
  omission 1, other 5. Checked: no art decoder imported by `rng_anim.py`, `seedtree_anim.py` or the kit (the test's
  import guard, and read); frames viewed in both themes (rng 0, 1, 9; seed tree 2, 7, 8, 10; tc eight players 4; maze
  47 final), each number against the model and the specs: the rng draw (randomness § The generator, RNG core § 2 and
  its worked example: 12345 gives 87 and `{015b2e77:0000141d}`), the seed tree (seeds § steps 1, 3a–3c, 4, 5 and
  step note 3: all five acts share the base; the Act II calc's "(steps − 1) / 2 pairs" is honest, `drlg.Act` steps
  the act seed only in 3b and 3c, and seed 12345 gives seeds.md's 2 pairs), tc § F (n = 1 + 7 ÷ 2 = 4; 19 → 0 from
  r = 19/68; two NoDrop picks with one player, none with eight; six items, D1's monster limit), maze § E1, § F2 and
  § H1 (level 47's ring, dock path and want = max(2, 14 ÷ 5 + 1) = 3 against 17 ÷ 5 + 1 = 4). **Byte identity**
  reproduced: a temporary worktree at 1b35f8df and the lane commit gave the same 138 sha256 for the maze 36 and
  Andariel schematic runs (worktree removed). **Fixes** (`tools/`): (1) misread: `maze_anim.py` said "Fixed Def and
  file index (locked)" at a room's placement from its final lock state, so rooms the theme pass locks later read as
  fixed (level 47 rooms 7, 8, 13; level 36 rooms 6, 7, 11, 16, already served), and called a parent's Def recomputed
  after a special's new room is attached to it "special-room table entry sets Def" (maze § H1 themes only free rooms;
  § F2): placement now says locked only for a room made locked (`attach_locked`, a special's new room), and the parent
  step says its Def is recomputed and it stays free; a test (no themed room's placement says locked; level 47's
  locked placements are rooms 9, 12, 14). (2) other: the rng frames wrote the seed N and the range n both as "N" in
  the upper-case font ("MOD N" read as mod the seed): now "mod the range", and "64-bit result" for the sum.
  (3) other: the seed tree's caption strip gave decimals beside hex boxes and the map seed in decimal beside the game
  seed in hex: the strip and the map seed box are hex now (pixels; the step page keeps decimals and `{low:high}`
  states), and the kit draws dim text on the highlight fill as text colour (3.59 in dark). (4) omission: the
  eight-player tc frames never said eight players and wrote `ND 19>0`: the header adds "8 PLAYERS" when players > 1 and
  the row reads `ND 19->0` (one-player frames unchanged). (5) other, the lane's doubt (1), the reviewer's rule:
  `export_check.html_problems`' scheme test starts at a word boundary (`\b(?:https?|ftp|wss?):`); tests both ways
  ("draws: 3", "news: none" pass; `ws://x`, `wss://x`, ` ws:x`, `ftp:x`, a protocol-relative host fail).
  (6) other, ruling on doubt (2): change, not keep. The dark `dim` (130, 130, 145) → (150, 150, 165) and `bad`
  (215, 70, 70) → (235, 95, 95) reach 5.66 and 4.98 on the panel; the kit's test asks 4.5 of every text colour in
  both themes. The served maze 36 and Andariel illustrations change on the next cut (they are re-cut anyway).
  **Blocks** (doubt 4): copied to `workspace/phase11/blocks-batch1.md` and corrected there: (7) overclaim: row 2 said
  the map seed is the game's seed number without the override condition (seeds § step 1); (8) misread: row 4 said
  the ring "closed with a door link" and growth and specials are "the same passes"; it now names the ring's three
  growths and the Sewers finisher's dock path (§ F2, anchor added); (9) other: row 3's place line pointed at a section
  the page does not have, and row 2's second placement needs its own id. **Cut:** the four blocks placed in the lane's
  wiki pages for one build (restored after), `export_build.py --out workspace/export-x11a-review`: 71 pages, the six
  illustration folders, `export_check` 0 failures (864 warnings, none new from the blocks); the folder was removed.
  Tests green: `test_schematic_kit` (15), `test_anim_schematic`, `test_export_build`, `test_export_check`; gate green.
- 2026-11-17, archivist, lane/x11w (Phase 11 step 4a: widget groundwork, ADR-0037; first widget rng). Delivered:
  - **Widget `rng`** (`tools/widgets/rng/`): `widget.js` (pure `compute(inputs, data)` on BigInt for the 64-bit step, `mount` with
    DOM calls only, mounts itself into `figure[data-widget-name="rng"]` on load), `widget.json` (multiplier as
    `6AC690C5`, init word 666, three inputs, four illustrative seeds as `{"rows": "toy", "items": [...]}`, labels), `fixture.json`
    (13 cases: the page's worked example, n of 0 and -5, 1, 7, 8, 100, the largest n, seeds at both ends, clamped inputs),
    written by the twin `tools/widgets/twins.py` (`write` / `check`; the twin calls `tools/rng.py`'s `rng_range`, no second
    copy of the rule). The text fallback (`fallback_table`) is the 12345 / Range(100) / five-draw case, in decimal.
  - **Builder** (`tools/export_build.py`): a ```` ```widget ```` block (keys `id`, `widget`, `illustrates`, `caption`,
    `fallback`) writes `site/public/widgets/<id>/` (`widget.js`, `widget.json`, `widget.list.json` with marker `widget-only/1` and the
    sha256 of each file, and `fallback.gif|png` copied from an illustration folder built earlier in the same cut), verifies
    the folder with X13 and removes it on failure, and puts in the page the fallback (picture, or table for `fallback: text`),
    the caption plus the sentence "Computed by our model...", and one link line `[Try it ...](/widgets/<id>/widget.js)`.
    A block whose widget is missing, whose id repeats, whose fallback illustration is absent or whose folder fails X13 is a
    report line. The caption loop of `illustration_block` is now `caption_sentences` (shared). `export_publish.py`: `CUT_DIRS`
    gains `site/public/widgets` (test added).
  - **X13** (`tools/export_check.py`, `verify_widget`, `js_problems`, `json_problems`): fixed file list, marker, sha list,
    byte-equal to `tools/widgets/<name>/`, caps 48 KB / 16 KB, the ADR's banned names and forms, every string and comment through
    X1-X5 and X9 (a mini lexer, `${` in a template and an unterminated string fail), arrays only as `items` of an object with
    `rows` toy|page and at most 20; a page link or image into `/widgets/<id>/` must name a verified folder; `check_repo` needs
    the host step `site/src/rehype-widgets.mjs` (new allowed path) and the CSP word for word when the cut has widgets or the
    host file exists, and scans the host file (only `widgets/${...}` paths, no fetch, dynamic import, eval, `Function`, process or
    network modules; whole-line comments skipped). **Obfuscation ruling** (the ADR is silent): a pattern list cannot see a name
    built from pieces, so the routes to one are banned: the global object by every bare name (`window`, `self`, `top`, `parent`,
    `frames`, `globalThis`, `global`, `opener`, `this`, also `with`, `arguments`), a string literal in a bracket, `.constructor`,
    `.prototype`, `Reflect`, `Proxy`, `defaultView`, escapes (`\x`, `\u`, octal), `fromCharCode` and `atob` kin, `createElement`
    and `setAttribute` with anything but a literal of a short safe list (and never `src`, `href`, `style`, `on...`), `document` as
    anything but `document.<name>`, a timer whose first argument is not a function expression or arrow. Banned words are searched
    in comments and strings too (a stricter reading than the ADR's list). The marker for widget files is `widget-only/1`; the fallback
    keeps `schematic-only/1`. Where the ADR says the host wraps the image, the host here acts on the "Try it" line for both
    fallback kinds (the image stays where it is; ADR silent on a text fallback).
  - **E21** (`tools/gate.py`, `check_widgets`): runs `tools/test_widgets.py` (fixture equals the twin's output; `compute` run
    under node per case; a stand-in DOM mounts the module, types into the inputs and reads the table and the live region; mutation
    checks that the harness sees a changed widget, a wrong fixture and a mount that never returns), warns once when node is missing
    (`SKIP node`). E20 also runs the new `tools/test_export_widgets.py`.
  - **Tests**: `test_export_widgets.py` 205 checks (82 adversarial script forms, 17 allowed ones, JSON, folder tamperings,
    cut, repo and builder, end to end), `test_widgets.py` 26, `test_export_build.py` 149, `test_export_check.py` 180,
    `test_export_publish.py` 37, `test_anim_schematic.py` 5 (all green); `tools/gate.py` green with E21 counted.
  - **Export repository change** (prepared under `workspace/export-repo/`, never in git; ADR-0038's script copies it):
    (1) new `site/src/rehype-widgets.mjs`, the generic host (replaces each Try it paragraph with a `<figure class="widget-host">`
    carrying `widget.json` as a data attribute, read at build time because the CSP refuses a request for it, and adds one
    `<script type="module" src="<base>/widgets/<id>/widget.js">`); (2) `site/astro.config.mjs`: imports and registers it,
    constant `CSP` and a Starlight `head` meta `Content-Security-Policy` (`connect-src 'none'`, `frame-src 'none'`,
    `object-src 'none'`, `form-action 'none'`, scripts from self plus Starlight's inline ones and `wasm-unsafe-eval` for
    Pagefind); (3) `site/src/styles/site.css`: `.widget-host` styles in Starlight's variables only (both themes follow them).
    `export_check --repo workspace/export-repo` is green.
  - **Dry run**: scratch copy of `docs/` with a `rng-stepper` widget block (text fallback) under the randomness page's worked
    example; builder to a scratch cut (71 pages, 0 dropped), `export_check <cut> --repo workspace/export-repo` 0 failures; cut and
    export repository copied into a scratch copy of the export repository folder (node_modules copied), `SITE_BASE=/arpg-1-14d-notes/ npm run build`
    ok (72 pages), `check-site-links` "7787 links in 72 pages, all resolve", dist holds `widgets/rng-stepper/widget.js|json|list`
    (`widget.js` byte-equal to the source), the page head holds the CSP meta word for word and the module script. In headless
    Chromium (the site's own Playwright): the widget mounts, shows 87 / 015B2E77 / 0000141D for seed 12345 and range 100, follows
    typing, a `fetch` from the page is refused by the policy, Pagefind search still returns results (its worker's requests are not
    covered by a page's meta policy; do not add `worker-src`), dark theme looks right. The browser run found a real mount bug
    (a helper calling itself) that the node tests did not; the stand-in DOM test was added for it. The scratch copy and cut were deleted.
  - **Doubts / for the review**: the check bans words in strings and comments too, so a widget cannot say "location" or "file" in prose;
    only Chromium was tried (Firefox's handling of module scripts under the policy and the worker-vs-meta rule is untested);
    the host acts on the Try it link, not the image; no row 1 picture exists yet, so every fallback is a table; `widget.json` is read
    by the host at build time (its code is in the export repository but loads only `/widgets/<id>/widget.js` as a script).
- 2026-11-17, architect, review of `lane/x11w` (Opus, Tier A: a safety device; ADR-0037 read as the reference).
  **Verdict: accept with fixes (6: overclaim 2, omission 4).** Fixes, in `fix(tools): … (review of lane/x11w)`:
  - **X13's ban list was leaky (overclaim: "with the global object unreachable a built name has nothing to index").**
    51 escape scripts written at the review, none in the lane's 82; 32 of the first 38 passed `js_problems`: a name
    built from pieces read with `x[k]` (`(() => 0)[k]` is `Function`), `e.view` (an event's window), bare `open(`,
    `name =` (window.name keeps a value across pages), `history`, `createElement.call(d, "i" + "mg")`,
    `setAttribute.call`, `style.backgroundImage`, `composedPath()`, `getRootNode()`, `.click()`, `.bind`,
    destructuring `{ [k]: w } = …`, `toString(36)` (spells words from numbers), `FontFace`, `CSS.paintWorklet`,
    `Option`, `process` (the gate's node), a `background` attribute, and code hidden from the lexer by a regular
    expression literal holding a quote (also after `if (…)`), a lone carriage return or U+2028 ending a `//` comment.
    **Ruling: an allowlist of names, the bans kept as a second layer.** A real lexer (`js_tokens`) for the subset a
    widget needs: a regular expression literal, an ambiguous slash, a backslash, `#`, `@`, a non-ASCII character
    outside a string, a control or line-separator character or an HTML comment marker fails. On its tokens
    (`js_name_problems`): a bare name is a keyword, one of `JS_GLOBAL_ALLOW` (Math, Number, BigInt, JSON, document,
    timers, `matchMedia`, typed arrays, …) or a name the browser's global object does not have; a member name (after
    `.`/`?.`, and every key of an object literal or pattern, since a destructuring key reads) is one of
    `JS_MEMBER_ALLOW` or a name no browser object has; `x[…]` takes only an integer literal (`.at(i)` for a variable
    index); no computed key; `toString` radix 2, 10 or 16 only; a hex literal passes the text rules; the strings
    joined (spaces and case aside) spell no identity string or home path; `setAttribute` names from an allowlist
    (`aria-*`, `data-*`, `role`, `id`, …). Why names and not more bans: no ban list can name every route, while a
    name the browser does not know can only be the widget's own variable or data. The two name lists
    (`tools/widgets/browser-globals.txt`, 1 026 names; `browser-members.txt`, 4 775) are written by the new
    `tools/widgets/browser_names.mjs` from Chromium (the export site's Playwright) plus a hand list of other engines'
    and node's names; a name only another engine has and the list misses is the residue, with the CSP and the Tier A
    read behind it. One probe still passes, harmless: `input.type = "ima" + "ge"` (no `src` can be set). The rng `widget.js` changed with it: `0xFFFFFFFFn` masks became `BigInt.asUintN(32, …)` (the hex
    literal failed X1) and `rows[rows.length - 1]` became `rows.at(-1)`; fixture unchanged, E21 green, browser-checked.
    Tests: 51 escape forms and 13 allowed forms added to `test_export_widgets.py`, with the joined-identity case and the
    lists' load.
  - **The CSP, tightened (overclaim: "`wasm-unsafe-eval` for Pagefind").** Checked on a scratch build in Chromium:
    Pagefind runs in its own worker, whose requests and WebAssembly follow the worker's policy, so the page needs
    neither `connect-src` nor `wasm-unsafe-eval` for search. Now, in `workspace/export-repo/site/astro.config.mjs` and
    `CSP_POLICY` word for word: `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self'
    'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'none'; worker-src 'self'; manifest-src 'self';
    frame-src 'none'; object-src 'none'; form-action 'none'; base-uri 'none'`. `'unsafe-inline'` scripts stay
    (Starlight's own inline scripts), which is why HTML injection stays banned in X13. A meta policy can't cover
    navigation (`open`, `location`, a link's click): X13's allowlist is the only bar there, and it holds.
  - **The host step's check (omission).** `check_repo` scanned only for `widgets/` paths, so a host adding
    `/widgets/${id}/other.js` passed. It now requires exactly one `'script'`, one `src:`, the template
    `` `${prefix}/widgets/${id}/widget.js` `` and the link shape `/^\/widgets\/([\w-]+)\/widget\.js$/`; 4 tests, and the
    prepared host passes.
  - **E21 ran any `widget.js` under node unchecked and unsandboxed (omission).** `test_widgets.py` now runs X13
    (`js_problems`, `json_problems`) on the sources first (so the gate also catches a refused widget at commit time, not
    only at publish) and never hands a failing one to node; node runs with `--permission`, read access to the widgets
    folder and its scratch folder only, and `--disallow-code-generation-from-strings`; 4 tests that the sandbox refuses
    a process, a write, a read outside and code from a string.
  - **Text-rule gaps (omission):** a hex literal in code and strings joined across `+` were outside the text rules
    (both closed above, counted once here).
  - **`widget.json` string `file` (omission):** fails (an input type a widget may not create); test added.
  - **Rulings.** The lane's departure from ADR-0037 (the host acts on the "Try it" link, not on the fallback image):
    **accepted**. The ADR's guarantees hold (without JavaScript the reader keeps the fallback picture or table and the
    caption; the host loads only `/widgets/<id>/widget.js`), the link is builder-written and X13-verified, and one rule
    serves both fallback kinds where wrapping the image leaves `fallback: text` with nothing to wrap; with JavaScript the
    picture stays above the widget. Banning the words in strings and comments too (the lane's stricter reading) stays.
  - **Checked and right:** `compute` against `tools/rng.py` (`rng_range` with the u32 pattern of n, the 64-bit step on
    BigInt, `low mod n` unsigned, n below 1 no draw) and the randomness worked example (12345, Range 100: 87,
    `015B2E77`, `0000141D`); the fixture is the twin's (`twins.py check` OK); widget.json rows `toy`, ≤ 20, strings
    through the text rules; byte-equality to `tools/widgets/<name>/`; X13 on every widget folder of the cut; the link
    and image rule for `/widgets/`; E21 skips with one warning without node (and still runs X13 on the sources), fails
    on a changed fixture or a refused widget; gate 40 s.
  - **Browser** (scratch copy of the export checkout, cut with a `rng-stepper` text-fallback block under the worked
    example, `SITE_BASE=/arpg-1-14d-notes/` build, link check "all resolve"; Chromium headless): the widget mounts in
    dark and light, shows 87 / `015B2E77` / `0000141D`, follows typing and the arrow key, labels bound to their inputs,
    Tab order seed → range → draws → preset, live region updates, no page overflow at 375 px, no animation (nothing for
    `prefers-reduced-motion` to stop); without JavaScript the table, caption and "needs JavaScript" figure show. A probe
    `widget.js` swapped into the scratch build was refused by the policy for `new Function`, `eval`, a string
    `setTimeout`, `fetch`, XHR, WebSocket, EventSource, `import()` (external and `data:`), an external image, audio,
    `FontFace`, a blob worker and a `<base>`; search answered under the policy; no policy error on three pages. Firefox
    was not run (no engine installed): the residue of the meta-policy rules in other engines stays with the redaction
    review of the first cut that carries a widget (ADR-0037: it opens each widget in both themes).
  - **At merge:** the export repository files in `workspace/export-repo/` (`astro.config.mjs` CSP changed here, the
    host and styles as the lane left them) are copied by the publish script; nothing to apply by hand.
- 2026-11-17, archivist, lane/x11b (Phase 11 batch 1 part 2: rows 5–8). Four generators on the kit, each with
  `--theme dark|light`, the data root first, `--schematic` accepted, in `SCHEMATIC_TOOLS` (and `test_export_build`'s
  tuple assertion). **Row 5, `tools/quality_anim.py`** (`lsd 28 0xc0ffee --mf 200`): the ladder of tests, one frame
  per test reached (base term, magic find's `F`, the minimum, the ratio word, the chance, the draw and its bar), then
  the outcome; the roll is `quality.roll` with its trace and its per-test record of the chance before the minimum
  (`cf["pre"]`); the base term and `F` shown are recomputed with `quality.cdiv/diminish` and asserted equal to the
  model's chance, and the seed after each draw is rebuilt with `quality.range_b` and asserted equal to the roll's exit
  seed. For these inputs unique, set and rare are lost and the magic draw (15) wins; 6 frames. **Row 6,
  `tools/special_anim.py`** (`zombie1 0xc0ffee --difficulty hell`; `4 --difficulty nightmare` is a champion): the
  champion draw against `MonUMod[0].constants`, the `Range(1)` step, one frame per pick, the mod list; the model is
  `monspecial.Data.mods_roll` and the records of its picks; the number of unit-seed steps is asserted equal to special
  § A1's count by stepping `rng.step`. **The special § D note:** the per-mod table is not drawn. A pick frame shows the
  rows that carry a weight of the pick's kind, the number of candidates, their total, the draw and the winner's name
  with its one weight; no per-mod list of weights and no `xfer` column. The only inference a reader can draw is that
  a champion pick's total equals its candidate count (the stock champion weights are all 1), which § B2 (kept in the
  export) already says; flagged for the review. **Row 7, `tools/timing_anim.py`** (defaults: a 14-frame cast record, speed
  256, event on frame 7, FCR 20 = the timing worked example 1): the rate from `anim_rates.bonus` and `rate_cast`
  (`--mode gethit` uses `rate_gethit`), the queue from `anim.schedule`, and `anim_rates.closed_len`, `sched_len` and
  the E2 event-frame formula asserted equal to it; one frame per scan step (11 steps, 13 frames). The attack branch
  is not offered: its `X` also takes stat 68, which the toy record does not model. The tool reads nothing from the data
  root. **Row 8, `tools/frame_anim.py`**: no model of the tick exists in `tools/` to drive, so the frames draw the
  spec's pass list (B1, D1) as a fixed sequence with each pass's draws and seeds from the J table (the tags of the
  inferred ones are named in the step page) and compute only the modulo tests of ranks 17 to 19 and the sweep on
  `--frame N` (default 1320; 1321 shows the skips); no log is read. **Kit:** `Kit.caption` records any caption it had
  to cut in `schematic_kit.CAPTION_CUT`; a test asserts the four tools cut none. **Tests:** `test_schematic_kit.py`
  grows from 15 to 26 tests: each tool deterministic, both themes' palettes, `export_check.verify_illustration`
  clean on each folder, no art decoder imported (the `run` helper), quality's per-test chance, draw and `F` equal
  `quality.roll`/`diminish`, special's picks, totals, draws and seed states equal `mods_roll`, timing's
  rate 299, `T + 6` and `T + 12` and the get-hit example 2 (rate 143, `T + 9`), frame's pass and walk names and order
  equal the spec's B1 and D1 listings and the periodic tests; `test_anim_schematic`, `test_export_build` (149 checks),
  `test_export_check` (191 checks) and `gate.py` green. **Frames viewed** (dark and light): quality 0, 2, 4, 5 and the
  no-draw normal test; special 1, 2, 4, 5, 6 and a champion pick; timing 0, 6, 12 and a get-hit step; frame 0, 4, 6,
  14. Fixed after looking: a heading overlapping the seed line, a truncated caption (found with the new cut check),
  a label colliding with DONE, an overlong seeds line; all read at scale 2 with contrast 4.5 from the kit's palette.
  **allow-hex:** no line needed (`0xC0FFEE` is present; texts use decimals and `{low:high}` states). **Blocks:** rows
  5–8 with draft captions and Place lines are in `workspace/phase11/blocks-batch1.md` under "Rows 5–8" (ids
  `items-quality-lsd-mf200`, `monsters-special-zombie1-hell`, `anim-schedule-cast-fcr20`, `frame-tick-passes`).
- 2026-11-17, architect, review of lane/x11b (Opus, Tier A): **accept with fixes**, 12: misread 2, overclaim 3,
  omission 3, other 4. Checked: frames viewed in both themes (quality 0, 1, 2, 3, 4, 5; special 1, 3, 6 and the
  champion branch's pick 2; timing 0, 7, 12; frame 0, 2, 4, 7, 10 and at 1321 frames 14 and 17), each number against
  the specs: quality § C–D (d = 8; F = 211, 242, 250 from `Diminish` with 250, 500, 600 at MF 200, 300 for magic;
  23780, 8251, 4915, 1365 after `× 100 ÷ F`; minimums kept; four draws, magic on 15), special § A1/B1/B2 (draw 68 ≥ 20,
  `Range(1)`, three unique picks of 12 candidates and total 72 in Hell, five unit-seed steps = 1 + (1 + 2) + 1; the
  champion branch 10 < 20, five candidates of weight 1), timing § J1–J2 and § E2 with worked example 1 (B 17, X 117,
  r 299, the do at T + 6, the end at T + 12, 11 steps), frame § B1, C, D1, J (ranks, walks, slot 1320 % 64 = 40, the
  periodic tests). **Rulings.** (a) Row 8 is kept: the owner accepted it as "the spec's pass list, no log", ADR-0036's
  decision asks that illustrations make no claim of their own and restate a spec, which the frames do (the test ties
  the names and order to the B1 and D1 listings), and the only numbers are computed; its caption drops the sentence on
  how ranks were established (seen in windows, read from the code), which is method talk the picture does not need.
  (b) Row 6 and § D: kept. The frames show per pick the candidate count, the total, the draw and the winner's one
  weight; the stock weights (1 and 6), the candidate counts and the mod names are on the wiki page and in § B2 already,
  and no per-mod draw or `xfer` column is drawn. (c) `CAPTION_CUT`: accepted (a test asserts the four tools cut none).
  **Fixes** (`tools/`): (1) misread: `timing_anim.py` drew the schedule as a scan running one step per game frame
  ("STEP 7, ON GAME FRAME T + 7"); E1 is one call at the mode start that walks every step and queues for T + k: the
  first frame says so, step headers and captions read "for game frame T + k", the help line and docstring too.
  (2) misread: `frame_anim.py` tagged rank 3's seeds confirmed; § J has them `[I]` (the routes `[C]`). (3) omission:
  rank 14's seeds dropped "the saves' seed is not read". (4) overclaim: the first frame said "the host loop, once per
  40 ms" (a time in ms, ADR-0014; the 40 ms is the flush's throttle, A3 `[I]`) and the last "next: drain, then a
  tick" where C4 allows several drains between two frames: now "one pass of the host loop" and "a drain or more".
  (5) overclaim: `quality_anim.py`'s outcome said the seed carries the draws "to the next roll"; the spec says the
  resolver's next draw continues on the same seed. (6) other: in the upper-case font a multiplication written `X` read
  as the variable X of the rate or the draw X (`SPEED X X / 100`, `C - W X C`): `*` in both tools' frames and step
  texts, and a test. (7) other: code names in the upper-case font (`NEWROOMSUPDATE`, `GAMERUNUNITEVENTS`) now in words,
  the pass labels follow the wiki page's names (frame stats, frame reset, release, sweep tick), one label collided with
  DONE and one title overran the panel; a test bounds the labels. (8) overclaim: `export_build.py` appended "Seed:
  illustrative, an input of our own" to every illustration, rows 7 and 8 included, which draw on no seed: a block's
  `seed: none` now gives "No seed is drawn on." (ADR-0034 labels a seed that exists; a generator with no draw has none),
  with a test. **Blocks** (`workspace/phase11/blocks-batch1.md`, corrected there): (9) omission: row 5's caption gave
  the diminished factor without its "above magic find 10" condition, and (10) omission: row 6's "class and version
  tests" for `ModEligible` (now the disabled row, the expansion row in classic, the excluded type, the class's mode)
  and the draw's range (0 to the total minus 1); row 7's caption rewritten for (1), with `×`, `÷` and `⌈ ⌉`. (11) other:
  all eight captions named a tool path (the builder strips it) and carried their own "Every value shown is computed by
  our model" sentence, which the builder appends again: both removed; rows 7 and 8 take `seed: none`. (12) other: the
  Place lines of rows 5–8 name the exact paragraphs. **Cut:** all eight blocks placed in the lane's wiki pages for one
  build (restored after), `export_build.py --out workspace/export-x11b-review`: 71 pages, ten illustration folders,
  0 caption sentences dropped; `export_check` 0 failures (864 warnings, none from the blocks); the folder was removed.
  Tests green: `test_schematic_kit` (28), `test_anim_schematic`, `test_export_build` (151), `test_export_check` (191);
  gate green. **For the spec-writer:** place the eight blocks as their Place lines say; rows 7 and 8 keep `seed: none`;
  the wiki's own schedule flowchart (animation, "The schedule") says "step k, on game frame T + k", which reads as a
  per-frame scan where E1 is one call at the mode start; worth the same rewording when the block goes in.
- 2026-11-17, spec-writer, lane/x11s (Phase 11 batch 1 placed; the rng widget placed). **Blocks** (from
  `workspace/phase11/blocks-batch1.md`, as their Place lines say): row 1 `rng-seed-12345`, wiki/randomness, end of
  "The generator: eight bytes and one multiplication"; row 2 `rng-seed-tree-c0ffee`, wiki/randomness, end of "Rooms:
  one draw each, then a restart", and the same block as `rng-seed-tree-c0ffee-build` in wiki/seed-to-world, end of "B.
  Acts and levels"; row 3 `items-tc-andariel-hell-8players`, wiki/items, end of "More players, fewer empty picks"; row 4
  `drlg-maze-level47`, wiki/levels, "Maze levels", after the level 36 block; row 5 `items-quality-lsd-mf200`,
  wiki/items, "The quality roll and magic find", before the magic find paragraph; row 6
  `monsters-special-zombie1-hell`, wiki/monsters, "Champions and uniques", before "Pack members and preset champions";
  row 7 `anim-schedule-cast-fcr20` (`seed: none`), wiki/animation, "The schedule", before "An every-frame monster
  instead"; row 8 `frame-tick-passes` (`seed: none`), wiki/server-frame, "The tick and its passes", after the
  flowchart. Captions as reviewed, three typographic changes only, to match the page and the caption beside them:
  row 3's `1 + (8 - 1) / 2` and row 4's `rooms / 5 + 1` written with `−` and `÷` as the items page and the level 36
  caption write them, row 5's `c - 1` as `c − 1`. **Widget:** `rng-stepper` (widget `rng`) in wiki/randomness § A
  worked example, after "Step 1 in full"; fallback `rng-seed-12345` (picture, its first frame, built earlier on the
  same page), not the text table, as ADR-0037 prefers; the caption says what the reader types (seed, range, draws 1–12,
  or an illustrative preset), what the table computes (Init, each Range(n): result, low and high after, in hex; n
  below 1 no draw) and what the fallback picture is. **Animation:** wiki/animation "The schedule": the paragraph and the
  flowchart now say one call at the mode start on frame `T` walks the steps ahead and queues step k's events due on
  `T + k`, and the end due one frame after the last step (timing § E1), in place of "step k, on game frame T + k".
  **Local site:** `site_build.py` renders a `widget` fence as a plain code block (no break);
  [backlog](../backlog/2026-11-17-spec-writer-archivist-local-site-widget-block-fallback.md) to the archivist. **Cut:**
  `export_build.py --out workspace/export-x11s`: 71 pages, 0 dropped, eleven illustration folders, the widget folder
  `site/public/widgets/rng-stepper/` (`widget.js`, `widget.json`, `widget.list.json`, `fallback.png`); no caption
  sentence of the new blocks dropped (the report's only wiki drops on these pages are two older X9 text sentences);
  `export_check workspace/export-x11s --repo workspace/export-repo/` 0 failures, 864 warnings (the x11b review cut's
  count); the folder was removed. Gate green (E21 included). Left: wiki/animation's W4 (timing and movement updated
  2026-11-17 by plan 0066's follow-ups) is older than this lane and stays for a refresh.
- 2026-11-17, architect, review of lane/x11s (Opus, Tier A) and **the redaction review of the cut it makes** (the
  first cut with a widget; Phase 11 step 4). **Tier A: accept with fixes**, 5: overclaim 1, omission 1, other 3.
  Checked: each placement (page, section, flow) and each caption against its spec: rng § Algorithm and the worked
  example (Init high 666; 87, `015B2E77`, `0000141D`; the eight draws and the final seed recomputed), seeds § steps
  1–5 (base `A28ED4C0` for all five acts, tombs 70 and 69, gate bit 1, the three room draws recomputed), tc § F2–F4
  and § D1 (n = 4, NoDrop 19 → 0 at each of Andariel's seven picks, the drop stops at the limit of 6; two NoDrop picks
  with one player), maze § E1, § F2, § H (ring north, west, south; the dock path's rooms 7–9 and 10–12, the free
  room 13 south of the dock as `a` = 3 gives, the Next special on it and its Def recomputed; 3 themed of 14),
  quality § C, § D, `Diminish` K1, special § A–B, timing § E1–E2 and § J, frame § B1, D1, J; the animation page's
  rewording and flowchart against E1 (one call at the mode start, step k queued for T + k, the end at t + 1): right.
  **Fixes:** (1) overclaim (the lane's flag): the builder appended "Every value shown is computed by our model" to row
  8, whose frames restate § B1/D1/J and compute only divisibility tests. Ruling: an optional seventh block key,
  `values: computed` (default) or `restated`; `restated` gives "The picture restates the spec; nothing shown is
  observed in the game." (`export_build.py`, `site_build.py` accepts the key, `pseudocode-conventions.md`'s key
  table; 3 tests in `test_export_build.py`); row 8 takes it. (2) other: `seed: none`'s "No seed is drawn on." read,
  beside row 8's seeds per pass, as a claim about the tick: now "The picture takes no seed." (3) other: the widget
  caption's "Without JavaScript the picture shows …" implied the picture is there only without JavaScript; it stays
  above the table either way: "The picture is the first frame …; without JavaScript it stands in for the table."
  (4) other: row 8's last frame wrote its running ranks past the canvas edge ("…, 18, 19," then nothing): the lists
  now sit on their own lines (`frame_anim.py`), and `schematic_kit.Kit.text` records any line past the canvas in
  `TEXT_CLIPPED`, which a new test (frame at 1320 and 1321, timing, rng, seed tree, and the guard itself) asserts
  empty. (5) omission: **the picture fallback 404'd on the served site.** The builder writes it as root-absolute
  `/widgets/<id>/fallback.png`, and the base step in `astro.config.mjs` prefixed `/illustrations/` only (the x11w
  review's browser run used a text fallback, so no picture fallback had been built under the base); the link check
  on `dist/` reported it. The base step now prefixes `/(illustrations|widgets)/` (in `workspace/export-repo/`, which
  the publish script copies), and `check_repo` fails X13 when the config lacks that step (`WIDGET_BASE_STEP`, a test
  in `test_export_widgets.py`). **Filed:** [backlog](../backlog/2026-11-17-architect-archivist-export-publish-astro-cache.md)
  to the archivist: the Astro content cache (`node_modules/.astro/data-store.json`) kept the old HTML of an unchanged
  page after the config change until removed; `export_publish.py` should clear it (not blocking: the randomness page's
  text changed in this cut, so it re-renders).
  **Redaction review: pass; the owner may publish this cut with `tools/export_publish.py --push`.** Cut (lane head plus
  the fixes): `export_build.py --out workspace/export-x11s-review`, 71 pages, 0 dropped, eleven illustration folders
  and the widget folder; `export_check … --repo workspace/export-repo/` **0 failures**, 864 warnings (the previous
  cut's count). Report on the touched pages: two drops, both older X9 text sentences (randomness's inlined-site count,
  items' "read again in the disassembly"); no caption sentence of the new blocks dropped; no rewrite on them.
  **Pictures opened** (dark, the cut's theme; light rendered for the six tools that take `--theme`): rng 0, 1, 2, 9;
  seed tree 0, 3, 5, 10 (both folders the same output); tc eight players 0, 4, 36, 72; maze 47 0, 5, 20, 33; quality
  0, 2, 4, 5; special 0, 1, 3, 6 and pick 2; timing 0, 6, 7, 12; frame 0, 4, 9, 17; and the step-through texts of all
  eleven folders and the widget's two JSON files scanned for addresses, tool, method and path words (none). No game
  art, no addresses, no repository paths; tables only as the reviewed pages already state them (the ItemRatio row the
  items page shows, the per-pick totals ruled at the x11b review); every number matches its caption. **The widget:**
  `site/public/widgets/rng-stepper/` `widget.js` and `widget.json` byte-equal to `tools/widgets/rng/`, the fallback
  byte-equal to the row 1 folder's first frame, X13 green, toy rows 4 and 5 (≤ 20). **Real site build** in a scratch
  copy of the export checkout (cut and `workspace/export-repo/` copied over, `node_modules` copied, not linked: a
  link breaks Astro's compile), `SITE_BASE=/arpg-1-14d-notes/ npm run build`: 72 pages; `check-site-links.mjs dist`:
  7 810 links, all resolve (after fix 5). **Chromium headless** (served locally under the base): the seven touched
  pages load with the CSP meta, no console error or warning, no failed request, all 12 pictures load (11 GIFs and the
  fallback); the widget mounts in dark and light and shows 87 / `015B2E77` / `0000141D` for 12345 / 100; typing seed
  1 gives 51 / `6AC6935F`; ArrowUp on the draws field adds a row; Tab order seed → range → draws → preset, labels
  bound; live region updates; at 375 px no page overflows (the table scrolls inside its figure); search answers (5
  results for "multiplier"); without JavaScript the fallback picture, the caption and "Interactive version: needs
  JavaScript." show. **Firefox:** installed after all (`/usr/bin/firefox`, headless `--screenshot`, own profile): the
  widget mounts under the meta policy in light and dark with the same rows, and its console dump holds no policy
  message; keyboard not driven there (residue). **Manifest:** `docs/export/reviewed-pages.txt` unchanged (no new
  page). Scratch builds and copies deleted. Tests: `test_schematic_kit` (29), `test_export_build` (154),
  `test_export_widgets` (274); gate green. Ledger: verdict accept with fixes, 5 (overclaim 1, omission 1, other 3).
- 2026-11-17, archivist, lane/x12a (Phase 11 batch 2: rows 11, 13, 14). Two generators on the kit, each with
  `--theme dark|light`, the data root first, `--schematic` accepted, in `SCHEMATIC_TOOLS` (and `test_export_build`'s
  tuple assertion, one line each). **Row 11, `tools/links_anim.py`** (`0xc0ffee --act 0`; `--act 1|3|4`, `--diff 0..2`
  also run): one frame per pick call of every table with two or more shown levels (pick kind, draws on the copy of the
  act seed, side, rectangle, the check's answer and reason), a frame per finished table, and level 27's index step after
  the table that holds the Black Marsh; 18 frames for Act I. The model is `drlg.Act` and `drlg.act_links`, run with
  `drlg.PICK` and the three check functions wrapped (restored after), so the frames are the model's own calls; the draws
  shown are the copy's `Seed.log`; a reject's reason uses `drlg.gap_overlap`; the level 27 index is recomputed from the
  table's entry seed and asserted equal to `Act.idx27`. A fixed far entry (Moo Moo Farm: an anchor pick nobody anchors
  to) is named and left out of the picture. For the three picks whose stored choice is a size (Act V's `0x0067D830`,
  `0x0067D8E0`, `0x0067D980`) the frame says "shape", not "side"; the picks that draw on every call (`0x00676C00`, `0x0067D830`,
  `0x0067D8E0`) say "picks again and draws again" after a reject, the others "next choice with no new draw" (warps
  B1). **Row 14, `links_anim.py --warps`** (no seed): three frames, the warp points of Cave Level 1 and the two pairings
  of the warps worked example. Level 3's slots come from the model (`Act`, `act_links`) and level 9's from the Levels
  row (`drlg.LV`); the points are `(x + w / 2) * 5` and the pairing is `pair()`, a small function of the F1 rule: the
  model keeps that rule inside `Model.warp_pair`, which needs a run log, so this is a second copy of the rule's
  arithmetic, tied by tests to the spec's worked example (rank fails at k = 3 and slot 0 pairs; rank slot 3 has no room,
  the walk 3 to 6 ends on slot 6) and to a toy rank-hit case. **The rooms of this output (level 9's two, and Cold Plains'
  cave mouth on slot 6) are the worked example's inputs, not a run**: the block takes `values: restated`. **Row 13,
  `tools/preset_anim.py`** (`0xc0ffee --preset lutw|lutn|catne`): a frame with the unit list as one cell per unit in walk
  order, one frame per roll (the seed before and after, r, the test and its answer, the keep chance as a bar, the
  units passed with no draw), and the kept list; for Lut Gholein's LutW 4 frames (68 units, 2 rolls: vendor 204 kept,
  205 dropped). The model is `PresetUnitData.ds1` (the unit list: ids and positions only, no layer is drawn) and
  `drop_rolls`; which unit drew is found by running `drop_rolls` on each prefix of the list, and each roll's answer is
  asserted equal to the spec's step 3a test (a table in the tool, tested over a period of 12 for its chance). The
  preset is named by a key (`lutw`, `lutn`, `catne`), not a file path, so `schematic.json` carries no path. **Tests:**
  new `tools/test_drlg_anim.py` (17 tests; not in `test_schematic_kit.py`, to leave that file to the parallel lane):
  determinism, both themes, folder clean under `export_check.verify_illustration` (allow-hex), no art decoder imported,
  `TEXT_CLIPPED` and `CAPTION_CUT` empty over six link runs, the warps output and three presets in both themes, traced
  rects, draws, level 27 index and act seed equal a plain run of the model (five act, seed, difficulty runs), the warps
  worked example 1 (Cold Plains, Blood Moor's four sides, Rogue, Burial Grounds, Black Marsh's reject then side 3, index
  1, draw `2FAADC42`) and 2 (points (7880, 6520), (7640, 6840); level 3's Vis and Warp lists), the preset worked example
  (LutW and LutN draws, `r mod 3`, kept lists, seeds), every reject has a named reason over five seeds. Green:
  `test_drlg_anim`, `test_schematic_kit` (29), `test_anim_schematic`, `test_export_build` (154), `test_export_check` (191),
  `gate.py`. **Frames viewed** (dark and light): links Act I 1, 3, 6, 7, 9, 16, 17 (a Rogue overlap reject, a side-table
  reject, the Burial Grounds accept, the table-done frame, the level 27 step), Act II 3 and Act V 2; warps 0, 1, 2; preset
  0, 1, 2, 3. Fixed after looking: slot boxes too narrow for "WARP -1", captions that read "it the Rogue Encampment's
  side is not in the table" (reasons are now whole clauses), "side -1" on an anchor pick, level names in capitals mid
  sentence, "57 units passed since the last roll" before the first roll, the fallback walk shown without the rank slot it
  repeats (F1 walks every slot naming the source). **Doubts:** (1) row 14's rooms are inputs of the worked example, so
  the block says "restated"; a computed version would need the maze model's level 9 for a level seed, which `drlg.py`
  has only through a log replay. (2) Row 11 shows Act I only in the block; the tool draws Acts II, IV and V too, and
  Act III is refused (its layout is the jungle generator). (3) Act V's table has no check and the frames say "no check:
  kept". (4) Row 13 has two rolls only (LutW); `catne` has one; a preset with more rolls could be added as a key if the
  reviewer wants a busier picture. **Blocks:** rows 11, 13, 14 with draft captions and Place lines are in
  `workspace/phase11/blocks-batch2.md` under "DRLG (x12a)" (ids `drlg-act1-links-c0ffee`, `drlg-preset-lutw-rolls`,
  `drlg-warps-cave1-coldplains`); each caption passes `export_build.caption_sentences` with no sentence dropped.
- 2026-11-17, architect, review of lane/x12a (Opus, Tier A): **accept with fixes**, 7: misread 2, overclaim 1,
  omission 1, other 3. Checked: frames viewed in both themes (links Act I on 0xc0ffee 0, 3, 4, 5, 8, 10, 14, 17; warps
  0, 1, 2; preset LutW 0, 1, 2, 3) and every step text of the three outputs, against warps § B1–B4, C1, E1, F1 and its
  worked examples, and preset § 2, § 3 (3a, step notes 2 and 5) and its worked example. Spot check: a plain
  `drlg.act_links` on Act I, 0xc0ffee, normal gives Rogue Encampment `(1120, 1192, 56, 40)`, Burial Grounds
  `(1136, 968, 40, 48)`, level 27 index 0 = `(~0x7C66376B) & 1` and the act seed `7c66376b:43cd3a7d` after, as the
  frames; level 3's `Vis`/`Warp` lists are the same for seven seeds and three difficulties (the warps output's Act I
  run takes no seed of its own). **Tracing (row 11):** sound. `drlg.PICK` is restored in place (the dict `link_build`
  reads) and the three checks by name in a `finally`, so an exception leaves the model as it was; `act_links` reads the
  check names at call time, and the depth guard keeps `_chk1a`/`_chk1b`'s inner `_chk_plain` call from recording a
  second answer; the wrappers set only the copy's `Seed.log`, which no value reads. A nested trace would restore in
  order; nothing runs it concurrently. **Row 14 ruling: (a), refactor.** F1 is now two pure functions of the model,
  `drlg.warp_rank_slot` and `drlg.warp_pair_slot` (with `rank`, false for a seam slot: F1 makes the rank search only
  when `LevelWarpId(S, m) ≠ −1`, which the tool's copy lacked); `GenModel.warp_pair` calls them, and the tool's
  `pair()` is gone. The model's own replay `drlg.py gen workspace/logs/maze/*.log` gives byte-identical output before
  and after (181 108 checks, 0 mismatches, the same 7 warp pairing coverage lines). The block keeps `values: restated`
  (its rooms are the worked example's inputs). Row 13's keep table (`RULES`) only labels the rule and its chance; the
  kept/dropped answer is the model's `drop_rolls`, asserted equal per roll: kept. **Fixes** (`tools/links_anim.py`,
  `tools/drlg.py`, `tools/test_drlg_anim.py`): (1) misread: the table-done frames' step text gave "the act seed itself"
  as the value after level 27's draw (the end of the whole run), at table 1 and before the level 27 frame; B1: the
  layout never steps the act seed. Now "the layout did not step the act seed, still" the table's entry seed, and the
  level 27 frame gives the table's seed after. (2) misread: every no-draw call said "the choice comes from the entry's
  stored first choice", and anchor picks "Side -1"; B1: the next choice follows from the current one, the stored first
  only ends the cycle, and anchor and fixed picks never draw. (3) overclaim: "each is linked both ways to its anchor"
  for tables whose anchors have none (Stony Field, Moo Moo Farm, Monastery Gate): now each level placed against an
  anchor; the same in row 11's block caption. (4) omission: E1's other branch, a waypoint room's point, was missing
  from the warps first frame and row 14's caption: both now say so, and that a seam slot adds none. (5) other: the
  row 14 ruling above, with tests (the rank-off case, no `pair` left in the tool). (6) other: reject captions named
  the side without the flip, so the Rogue Encampment's (2, 0) and (2, 1) rejects read the same; "BIT 0: SLOT 0" read
  as flag bit 0 (now "WARP BIT OF SLOT 0"); a shape pick's reject said "next side". (7) other: row 13's caption said
  "an illustrative seed started with Init" without saying that in a game Lut Gholein's rolls run on its level seed
  while its rooms are made (preset § 2 and the worked example). **Blocks** (`workspace/phase11/blocks-batch2.md`,
  DRLG part, corrected there for 3, 4 and 7). Place lines resolve to `docs/wiki/levels.md`'s paragraphs as written.
  **Cut:** the three blocks placed in the lane's `levels.md` for one build (restored after), `export_build.py --out
  workspace/export-x12a-review`: 71 pages, 0 dropped, the three folders built; `export_check` 0 failures, 875
  warnings, the 11 new all X12 on the captions' level names (Rogue Encampment, Cold Plains, Black Marsh …), the class
  the page's own prose already raises; every caption sentence present, with the seed and values lines as keyed; the
  folder was removed. Tests green: `test_drlg_anim` (18), `test_schematic_kit` (29), `test_anim_schematic`,
  `test_export_build` (154), `test_export_check` (191); gate green. **For the spec-writer:** place the three blocks as
  their Place lines say (row 13: after the "Which seed." paragraph); row 14 keeps `seed: none` and `values: restated`;
  the captions name levels in words, which X12 warns on (not a failure).
- 2026-11-17, archivist, lane/x12b (Phase 11 batch 2: rows 9, 10). Two generators on the kit, each with `--theme`, in
  `SCHEMATIC_TOOLS` (a new line). **Row 9, `pack_anim.py`:** one normal group of `swarm1` (MinGrp 4, MaxGrp 8, size 2, no
  minion) on a toy room of ours (a logic box, three walls, one warp point), 14 frames on `0xC0FFEE`: the leader's tries
  (try 1 refused by the warp distance, tries 2 and 3 by the probe, try 4 stands), the exact placement and its centre mark,
  the group size on the leader's seed (k = 6), one frame per member with its ring walk and every refused cell (outside the
  box, blocked), the end. **Row 10, `pool_anim.py`:** the game seed's first draw, the region seed, the levels built before
  the shown one (draw counts, seeds), the level's candidates, one frame per pick (the draw over the remaining slots, the
  class, kept or dropped; every redraw of a `rangedspawn` level's first pick) and the pool; `--level` (default 3, Act 1 -
  Wilderness 2), `--difficulty`. **Model functions.** The pool's numbers come from `monpool.first_draw_low`, `build_all`
  and the pick records of `build_pool`; the two now take optional `seed` and `traces`/`trace` arguments (no other change).
  The placement rules lived inside the log checker's interleaved replay, so they are **refactored into pure functions both
  call**, in the new `tools/spawn_place.py`: `ring_search` (MonSpawnTry's ring walk, spawn § H2), `near_point` (NearWarpTest's
  distance rule, § H1 note), the seed class `S` and `MASK_BY_SPAWNCOL` moved there; `monspawn.py` and `collision.py` import
  them. **No-change proof:** `monspawn.py check` on six logs (the three `monspawn-*` logs, two `collision-*` logs with the
  grid snapshot, one `monpool-*` log) prints byte-identical output before and after (115 795 and 20 481 checks, 0
  mismatches, 5 669 collision checks, the guard counters and the 98 near-warp hits equal); `monpool.py check` 361/361; a
  hash of `build_all` over 3 seeds, 3 difficulties and both game types is equal before and after. **Not shown / restated:**
  the toy's collision test (the plus footprint against the mask, the 0x1000 centre mark) restates § H3, H4 for one room; the
  creation draw on the game seed, the class cell test, the region-id test, the waypoint point and minions are not drawn.
  **Tests** (`tools/test_monster_anim.py`, 21): determinism, both themes, `verify_illustration` clean, no art decoder, clip
  and cut lists empty, no tool names in step texts; `ring_search` reproduces members 1 and 2 of the spawn worked example
  (cells, 39 and 4135 refusals, the seeds after) and its group-size draw; the pool equals `build_all` on every checked
  level and the pool worked example (seed 1, levels 1 to 3: 26 draws, 17 appearance draws). Also green: `test_schematic_kit`
  (29), `test_export_build` (154), `test_export_check` (191), `test_anim_schematic`, `test_drlg_anim` (18); gate green.
  **Frames viewed** in both themes: pack 0, 1, 2, 5, 9, 11, 13; pool 0, 2, 3, 4, 5, 7 and the rangedspawn level 110.
  **Blocks:** `workspace/phase11/blocks-batch2.md`, "Monsters (x12b)", Place lines into `docs/wiki/monsters.md`.
