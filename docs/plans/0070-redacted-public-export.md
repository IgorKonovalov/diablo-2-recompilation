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
  - **Backlog:** [entry](../backlog/archive/2026-11-17-architect-spec-writer-plan-0070-cut-2-export-readiness.md) to the
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
  [backlog](../backlog/archive/2026-11-17-spec-writer-archivist-local-site-widget-block-fallback.md) to the archivist. **Cut:**
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
  in `test_export_widgets.py`). **Filed:** [backlog](../backlog/archive/2026-11-17-architect-archivist-export-publish-astro-cache.md)
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
- 2026-11-17, archivist, lane/x12d (Phase 11 batch 2: rows 15, 16, 20, 21; publish cache; local widget fallback). Three
  generators on the kit, each with `--theme dark|light`, the data root first, `--schematic` accepted, in
  `SCHEMATIC_TOOLS` (and `test_export_build`'s tuple assertion); tests in the new `tools/test_path_anim.py` (16). **Rows
  15 and 16, `tools/path_anim.py`** (`--mode search|walk|spiral`): a hand-drawn toy room of 16 by 9 subtiles with a wall
  and a gap, a start (2, 4) and a target (13, 4). `search`: search § L2 and § L3 for type 0 with the spec's tables
  (turn rows, steps, `g_DirOctant` column 0, as `docs/tables/PathDirTables.md` lists them): bound 22 (h0), 27 and 32
  with the cell store kept across passes (28, 308 and 113 tries, route 5 corners, start not in it); 6 frames. **The
  model:** `tools/path.py` has no search (it compares logs); the model is `tools/path_emu2.py`'s `Search`, which reads
  its tables from `game.exe`, so `path_anim.search` is a traced restatement of § L3 and the test runs `path_emu2.Search`
  on the same toy room with the spec's tables (stub image, room shifted by 100 to clear the u16 wrap of the margin)
  and asserts the tries, passes, node count and corner list equal over four rooms; no second copy of a rule that a
  test does not tie. The plan's row says "the open set": § L has none (iterative deepening depth first), so the frames
  show the first descent, each pass's cell store with its g values and the reduced route; flagged for the review.
  `walk`: search § I on `rng.step` (seed 0xC0FFEE, limit 12: 6 draws, 7 points, add table of § I step 1, the first
  direction from `PathDirRow` toward the target), one frame per draw, 8 frames. `spiral`: search § J from the middle
  of the room (the start (2, 4) leaves most of it off the grid): the first iteration, the first one that keeps a point
  (iteration 5, (8, 5)) and progress at 32, 64 and 94 iterations (77 points, 26 on the grid); the sine is `math.sin`
  (the table is within 1.8e-07 of it; stated in the step texts and the block's caption). **Row 20,
  `tools/runeword_anim.py`** (`--base lrg --runes ko,ko,mal`, Sanctuary in a large shield, the page's own example):
  `sockets.match` over the real Runes, base and ItemTypes rows; one frame per insert (the match stops while the count
  differs), the full item's tests, the scan (41 complete rows before record 41: 40 differ at rune 1, one at rune 2,
  recomputed and asserted against the match's row), the row's runes against the children, the item-type test through
  the Equiv chain (shie to shld), the result; the model's row is asserted for Sanctuary, Steel (`lsd`, Tir El), the
  wrong order, a magic base and a base of another type. **Row 21, `tools/move_anim.py`** (`--speed walk|run|knockback|N
  --dist D`): `anim.step_model` (movement B1, B3) called once per game frame (the subtile the step enters is learned
  from the model's own `ct-mismatch` report, so no collision rule is restated), `anim.path_step` for the axis step;
  walk 8 frames, run 6 (the last step 12288), knockback 3, the closed form of B3 asserted over four speeds and three
  distances. **Blocks:** five in `workspace/phase11/blocks-batch2.md` under "Path, runeword, movement (x12d)" (row 16 is
  two blocks, walk and spiral); the builder's caption pass drops no sentence from any (checked with `caption_sentences`).
  **Frames viewed** (dark and light): search 0, 1, 3, 4, 5; walk 2, 7; spiral 2, 5; runeword 0, 4, 5, 6 and the
  no-row frame; move 0, 5, 8 and the run's last. Fixed after looking: captions of three lines cut at the old strip
  height (strip now 80 pixels: three lines), two texts past the right edge, a label over the T marker, a "kept" first
  spiral iteration that kept nothing, a "decides" line about item types that D4 does not say. **Publish cache:**
  `export_publish.py` removes `site/node_modules/.astro` and `site/.astro` before the site build (not with
  `--skip-site-build`), tested in `test_export_publish` (42 checks). **Local widget fallback:** `site_build.py` draws a
  `widget` fence as its fallback (the illustration's GIF, or the twin's table) with the caption and a note, no script;
  E19 (`site_build.py check`) parses widget blocks; new `tools/test_site_build.py` (5); both backlog entries closed.
  Tests green: `test_path_anim`, `test_schematic_kit` (29), `test_export_build` (154), `test_export_check` (191),
  `test_export_publish`, `test_site_build`; gate green.
- 2026-11-17, architect, review of lane/x12d (Opus, Tier A): **accept with fixes**, 8: misread 1, omission 2, other 5.
  Checked: frames viewed in both themes (search 0, 1, 3, 4, 5; walk 2, 7; spiral 2, 5; runeword 0, 2, 4, 5, 6, 7; move
  0, 3, 8, 9), each number against the specs: search § A3 (h0 = 2 × 11 + 0 = 22), § L2 (bounds 22, 27, 32 under b1C 33;
  the loop's `first < last`), § L3 (the first descent 4 steps right to the wall; the pass 3 route's g values 2, 5, 8,
  11, 14, …, 32 and f = 32 at the target; the store kept across passes, step 10's "lower g blocks"), Reduce (five
  points, start excluded); § I (draw 2: low `7C66376B` & 31 = 11, add 1, direction 1; points (4, 2), (6, 4)); § J
  (iteration 5: sine at 208 and 80 of 512 × 48000 = 26667, 39910, cell (8, 5); 94 iterations, 26 of 77 inside the room);
  sockets § D1–D4 (quality and quest tests, n ≠ s on inserts 1–2, 41 complete rows ahead, the Equiv chain, D3 with no
  etype); movement § B1, B3 (s = 24576, ⌈196608 ÷ 24576⌉ = 8, the snap on frame 8). **Rulings on the lane's doubts.**
  (1) No open set: § L has none; the frames say "depth first … no open list" and the caption says depth first: right.
  (2) `path_anim.search` as a traced restatement: kept, `values: computed` kept. A refactor onto `path_emu2.Search` is
  not small (its run returns totals only; the frames need each pass's store and the first descent, which would mean
  instrumenting the reverser's checked emulator); the copy is tied by test over four rooms (tries, passes, nodes,
  points), so it is our model and "computed by our model" is true. The 64 turn entries and 25 octant cells copied in the
  tool are listed values of `docs/tables/PathDirTables.md` (ADR-0031 allows them listed; the spec's § L3 already prints
  the turn rows) and no frame or step text prints a table row; the walk's addend table is § I step 1's rule.
  (3) The near-target stop: the toy runs refresh 0; a point target with no unit gives refresh 1, doubled 2, and h < 2
  only at the target, so the result is the game's for such a call; the caption now says that (fix 7). (4) No library
  name in public text (the step texts said "sin(144)", which read as radians): now "sine at 144 of 512" (fix 4).
  (5) `shld`/`shie` in frames: acceptable; the spec uses type codes (`shie`, `weap`, `blun`) and the page has no other
  name; the 33 rune names in the tool are names only, no table values (ADR-0009 risk 3 not touched). **Fixes:**
  (1) misread: `move_anim.py`'s end frame said "the next call snaps … and ends the move"; § B1 runs `PathStop` in the
  same call once the last point is reached (B5: the arrival follows in the step's frame): the frame, the caption and
  the step text say so, and a test. (2) omission: the search's pass frames counted 10 blocked cells where 8 are drawn
  (two lie past the room's edge) and left the start's own g (4) out: "8, and 2 past the room's edge", the start's g
  beside its S. (3) omission: `export_publish.clear_astro_cache` followed a linked `site/node_modules` out of the
  target's `site/` (`rmtree` of the link's `.astro`) and raised on a linked `site/.astro`: both are skipped now (no
  link, real path's parent must be `site/` or `site/node_modules/`), two checks in `test_export_publish` (44).
  (4) other: the spiral's "SIN(208)" in frames and "sin(144)" in step texts read as radians: "SIN(208 OF 512)", "sine
  at 144 of 512", and a test. (5) other: "R grows by 9600 a turn step" → "each iteration"; the 512 of a turn and
  "toward zero" kept in the strip. (6) other: dead `… if False else` in the walk's step text removed; the docstring
  named `test_schematic_kit` for the model test (it is `test_path_anim`) and now records the refresh reasoning.
  **Blocks** (`workspace/phase11/blocks-batch2.md`, corrected there): (7) other: row 15's "sets the near-target stop
  off" now gives why the stop changes nothing for this toy (doubt 3); (8) other: row 20's "takes the item type shld"
  → "allows". Place lines checked against the pages (pathing's three sections, items-other-paths after the flowchart,
  animation's "The step"): right. **Cut:** the five blocks placed in the lane's wiki pages for one build (restored
  after), `export_build.py --out workspace/export-x12d-review`: 71 pages, 0 dropped, the five illustration folders;
  `export_check` 0 failures, 864 warnings (the previous cut's count); no DROP or REWRITE on the three pages; every
  caption sentence of the five blocks present in the cut; the folder removed. **Backlog fixes:** the cache clear (fix 3
  above) and `site_build.py`'s widget fallback (no `<script>` in the body, tested; E19 parses widget blocks, rejects a
  repeated id, an unknown widget folder, a fallback that is no illustration id and a dead anchor; the repository's docs
  pass): right. Tests green: `test_path_anim` (16), `test_site_build` (5), `test_export_publish` (44),
  `test_schematic_kit` (29), `test_export_build` (154), `test_export_check` (191), `test_anim_schematic` (5); gate
  green. Ledger: verdict accept with fixes, 8 (misread 1, omission 2, other 5). **For the spec-writer:** place the five
  blocks as their Place lines say; row 21 caption could add that the path stops in the same frame (the frames say so).
- 2026-11-17, archivist, lane/x12c (Phase 11 batch 2: row 12). One generator on the kit, `tools/outdoor_anim.py`
  (`<root> 0xc0ffee [--diff D] [--theme dark|light]`; `--schematic` accepted; in `SCHEMATIC_TOOLS` and
  `test_export_build`'s tuple assertion, one line each). It animates the Burial Grounds (level 17, Act I), the one
  outdoor level of the wiki's list whose generator is only the seam mark, the border pass and one preset, so every
  draw of the window shows (9). 11 frames: the cell grid (rectangle, 5 * 6 cells, the level seed at the window start,
  the neighbour on the border list); the outline ring with its extra vertex; the seam mark (cell bit 0x1, warp-slot
  flag 0x10 << slot); one frame per ring segment of the border pass (edge piece, its first-use draw, file indexes, the
  seam opening, the corner or the edge piece again at a straight turn); the corner flood; the preset (piece 108 at
  cell (1, 1)); the final cell bits. **The model** is `drlg.Act`, `drlg.act_links` and `drlg.Outdoor` run as they are:
  the instance's `place`, `ring_build`, `seam_mark`, `border_build` and `corner_flood` are wrapped for the run (removed
  after, tested) to record each placement with the grids before and after and the draws it made; the tool computes
  nothing but the grouping of the recorded placements by ring segment (asserted to account for every border placement).
  The level seed is `Seed(A.base + 17)`, the spec's `Init(base + id)`; for map seed 3103, normal, the run is the spec's
  worked example 1 to the word (nine draws, `0x40601` at (1, 5), grid0 `0x40` on cells (0..2, 5), seed out
  `28B0827C:60189741`). No refactor of the model. Only level 17 is offered: Act II's seam pairs, the special areas and
  Act I's wilderness levels (thousands of draws, rivers, roads) have no single readable run; Act III has no border
  pass. **Tests:** new `tools/test_outdoor_anim.py` (11): determinism, both themes and four seeds under
  `verify_illustration` (allow-hex), clip and cut empty over six runs, no tool word or section sign in the step texts,
  the recorded run equals a plain run of the model for six seeds and difficulties (grids, seed, draws, no wrapper
  left), the segment grouping, worked example 1, step texts against the model, no art decoder imported (the model's own
  `ds1` import aside), bad arguments. Green with `test_schematic_kit` (29), `test_anim_schematic`, `test_export_build`
  (154), `test_export_check` (191); gate green. **Frames viewed** (dark and light): 0, 1, 2, 3, 6, 7, 8, 9, 10. Fixed
  after looking: the section sign is not in the 5x7 font (it printed "?"): left out of frame captions; the opening's
  "OPEN" label over the index; the corner and preset fills told apart; "D108" at scale 1; a straight turn at the seam
  vertex was labelled a corner (the spec's E3: the edge piece again). **Block:** "Outdoor (x12c)" in
  `workspace/phase11/blocks-batch2.md` (`drlg-outdoor-burial-grounds-c0ffee`, `values` computed, Place: `levels.md`
  "Outdoor levels", after the bullet list); the caption passes `export_build.caption_sentences` with no drop.
  **Doubts:** (1) the "cell (C, R)" labels and D/I letters are in the frames' key, not the caption. (2) A second level
  (Valley of Snakes, seam pairs and a special area) would add Act II's pair; not built. (3) The neighbour box is drawn
  at its true offset and clipped; for other seeds the neighbour can lie on another side and is clipped to the free area.
- 2026-11-17, architect, review of lane/x12c (Opus, Tier A): **accept with fixes**, 6: misread 2, overclaim 1, other 3.
  Checked: frames viewed in both themes (0xc0ffee 0, 1, 2, 6, 7, 8, 9, 10; map seed 3103 0, 1, 2, 6, 7, 9; seeds 2, 3
  and 8 for the neighbour on the east, west and north sides) and every step text of 0xc0ffee and 3103, against outdoor
  § B (cell and grid0 bits), C3–C5 (ring from v0 up the W side, the seam vertex), D1–D2 (rotation, first use draws,
  one past the draw), E1 (seam mark: `0x1`, `0x10 << k`, end cell included, no draw), E2 (edge pieces from `v + d` to
  `n`, the opening at `min + len ÷ 2`, `0x40400` on level 17), E3 (a straight turn: the edge piece's row again), E4 and
  H7 (`Place(1, 1, 108, −1)`). Map seed 3103 normal is worked example 1 to the word: the nine draws, rect, seed in and
  out, `0x40601` at (1, 5), grid0 `0x40` on (0 … 2, 5) (the lane's test asserts them). **Tracing:** the five wrappers
  hold only the instance's methods; the recorded run equals a plain run for six seeds and difficulties (grids, seed,
  draws). **Rulings.** (a) Level 17 only: kept. Row 12 asks one act; it is the one window whose draws are the border pass
  and one preset, readable whole; Valley of Snakes is not required. (b) Doubt 1: kept, the key is in every frame and
  the caption says it in words. (c) Doubt 3: fixed, below. **Fixes** (`tools/outdoor_anim.py`,
  `tools/test_outdoor_anim.py`): (1) misread: the straight turn's step text said "row 2 of the style table" on every
  seed; row 2 is the edge piece going north, and level 17's seam turn on the south side goes west (row 1, piece 4). The
  row is now `1 + DIRIDX[d]`, named with its direction; a test reads `g_BorderCornerIdx` for the four straight turns
  and the 3103 text. (2) overclaim: the seam segment's caption and step text put the opening "after its rotation draw"
  ("the draw was made") on a segment whose piece was used before and drew nothing: now "after the rotation gave it one",
  "the rotation still counted the cell"; the block caption likewise. (3) misread: the final frame said "none of the
  occupied-mask bits 0x1B81 is clear" (inverted: a cell is free when none is set) and drew the no-out-room conclusion
  from the placement mask; it now counts the cells without the footprint bit `0x200` (0: every cell holds a border
  piece or the preset, as worked example 1 says) and keeps the free count in the step text. (4) other: the wrappers were
  removed after `O.run()` with no `finally`; now a `finally`, and a test raises inside the run. (5) other: the seam
  mark's panel had 12 lines and its last ran over the frame; one blank dropped, the opening put on one line, and the
  panel asserts its 11 lines (the clip test builds ten runs). (6) other: the neighbour box at its true offset hid the
  key column when the neighbour is west (seed 3), overran into the panel gap when east (seed 2) and vanished when north
  (seed 8): over 1 197 runs the neighbour is north in 384, south 366, east 228, west 219. It is now a band beside the grid along the
  neighbour's stretch, with its name and side under the grid; a test for the four sides. **Block**
  (`workspace/phase11/blocks-batch2.md`, "Outdoor (x12c)", corrected there for 2). The Place line resolves to
  `docs/wiki/levels.md` "Outdoor levels", after the bullet ending at outdoor § M, before "When the act generator is
  done". **Cut:** the block placed in the lane's `levels.md` for one build (restored after), `export_build.py --out
  workspace/export-x12c-review`: 71 pages, 0 dropped, the folder built; `export_check` 0 failures, 866 warnings, none
  on `world/levels.md`; every caption sentence present with the seed and values lines; the folder passes
  `verify_illustration` with the allow-hex list (the step texts' `0x40601`, `0x1B81` are spec values under six hex
  digits; draws are low words in decimal); the build was removed. Tests green: `test_outdoor_anim` (14),
  `test_schematic_kit`, `test_anim_schematic`, `test_export_build` (154), `test_export_check` (191); gate green.
  `test_anim_schematic` failed once with 2 errors and passed on three reruns: its fixed output folder
  `workspace/render/test-anim` is shared through the symlink by lanes running at once (not this lane's). **For the
  spec-writer:** place the block as its Place line says; `values: computed`, `seed: illustrative`.
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
- 2026-11-17, architect, review of lane/x12b (Opus, Tier A): **accept with fixes**, 8: misread 1, overclaim 1,
  omission 2, wrong anchor 1, other 3. **The refactor: no change.** A detached worktree at 22d7e75b against the lane's
  tree, on the same data: `monspawn.py check` on the three `monspawn-s*` logs (115 795 checks), the two dev logs, the
  seven `collision-s*` logs (76 608 and 20 537 collision checks), the 39 `monspecial-s*` logs (393 693 and 31 485), the
  four `objects-s*` logs the findings cite and the `monpool-*` logs; `collision.py check` on the `collision-s*` logs, the
  two `monspawn-s*` logs and `objects-s2`–`s30` (300 785 and 28 177); `monpool.py check` (3 040/3 040) and `monpool.py
  pool` on three seeds and three difficulties: all eleven outputs byte-identical, 0 mismatches each. Rerun after this
  review's own `collision.py` change (below) on the `collision-s*`, `monspawn-s*` and `monspecial-s*` sets: identical
  again. Read: `ring_search` is the old loop with the cell tests as the callback (`s`, `smax` recomputed from `rad`
  as the caller did; the guard and the `spawn_on_tile` exit stay before it); `near_point` returns the old loop's
  answer; `build_pool`/`build_all` only gain records. **The group size:** the frames show k = 6 members and a group of
  7; F2's leader plus k, uniform in [MinGrp, MaxGrp] = [4, 8]: both right, and the caption now says both. **Ruling
  (pack_anim's restatement of H3/H4): refactored,** not into `spawn_place.py` but onto the model itself: the toy's test
  and mark are `collision.World.collision_test` and `pattern_op` (pattern `PATTERN_BY_SIZE[size]`, the monster bit
  `0x100`) on a one-room world, `World.one_room` (new, additive); `collision.py`'s `dt1` import is made lazy as in
  `drlg.py`, since the schematic test forbids an art decoder in the tool's process. Every frame byte is unchanged
  (both classes tested) and the `values` key stays computed. **Fixes** (`tools/pack_anim.py`, `tools/pool_anim.py`,
  `tools/collision.py`, `tools/test_monster_anim.py`, 24 tests): (1) misread: the members' step text said "radius 3,
  no box flag"; F2 places them with the group's box (SpawnNearUnit, H's wrappers): now "with the group's box", the
  rectangle bounding the walk and the region test passing on the toy's one region. (2) overclaim: "cells tested"
  counted the cells outside the box, which H2 skips with no predicate call: "cells walked", "outside the box,
  skipped", "walk order"; the block's "a cell is refused when it is outside the box" likewise. (3) wrong anchor: the
  block's member-5 sentence cited § H4 for the ring walk: § H2. (4) omission: WarpDist 100 was not labelled ours on the
  first frame ("TOY: WARPDIST 100") or in the caption ("a toy room of our own … a WarpDist of 100"), and the caption's
  *Not shown* lacked the region-id test and the level's waypoint point, which the wiki's paragraph names. (5) omission:
  row 10's caption sentence with the region seed in hex was dropped by the cut (X1); it now says the frames give both
  seeds. (6) other: pool's "levels built before" rows drew "R AFTER" over long labels ("POOL OF 3" under "R AFTER" on
  Act 4 - Diablo 1, Wilderness 1): the seed after is the box's second line, and a test bounds every level's label.
  (7) other: the H3/H4 ruling above, with a test (no own footprint, the mark's `0x1100` centre and `0x0100` plus, the
  room edge's `0x27`). (8) other: "RING WALK, RADIUS 3" beside "TAKEN ON RING 6" read as a contradiction (MonSpawnTry's
  radius 3 means rings 3, 6 and 9): named as rings in the panel, captions and help; "CENTRE REFUSED" for a plus
  that hits a wall beside a free centre is now "PLUS AT THE CENTRE: NOT CLEAR"; "1 cells". **Frames viewed** (both
  themes): pack 0, 1, 2, 3, 5, 6, 8, 11, 13; pool 0, 2, 3, 4, 7 and level 110's 2 and 4, against spawn § F2, H1–H4
  and the worked example, pool § A–C (the region seed `a28ed4c0` = 2 727 269 568, level 2's 30 draws, the three picks
  `Range(4) = 1`, `Range(3) = 1`, `Range(2) = 0`, rarities 2 + 2 + 1, 3 + 18 draws; level 110's five draws over
  seven, the last ranged). **Blocks** (`workspace/phase11/blocks-batch2.md`, "Monsters (x12b)", corrected there for
  2–5): the Place lines resolve to `docs/wiki/monsters.md`'s paragraphs as written. **Cut:** both blocks placed in the
  lane's `monsters.md` for one build (restored after), `export_build.py --out workspace/export-x12b-review`: 71 pages,
  0 dropped, both folders; `export_check` 0 failures, 864 warnings (the previous cut's count); every caption sentence of
  the two blocks present (11 and 7) after fix 5; the folder removed. Tests green: `test_monster_anim` (24),
  `test_schematic_kit`, `test_anim_schematic`, `test_drlg_anim`, `test_export_build` (154), `test_export_check` (191),
  `test_mon_sweep`, `test_chain`; gate green. **For the spec-writer:** place the two blocks as their Place lines say;
  row 9 keeps `seed: illustrative` and `values: computed` (every cell answer is the model's collision test on our toy
  grid); the pool caption names levels by the table's names, as the wiki's own pool paragraph does.
- 2026-11-17, archivist, lane/x12e (Phase 11 batch 2: rows 17, 18, 19). New `tools/combat_anim.py` (a toy melee hit: to-hit,
  block, build and delivery draws in order on two seeds), `tools/hire_anim.py` (a hire list: the n seeds, ten picks, ten
  entries, 23 frames) and `tools/affix_anim.py` (one magic-affix pick: alvl, draw 1, filter counts, weights, draw 2; 4 to 7
  frames); all in `SCHEMATIC_TOOLS` (new lines in `export_build.py` and its assertion). **Models:** `hirelings.py`
  `build_stock(trace=)` and `roll_entry(trace=)`, and `affixes.py` `Walk.pick(trace=)` (a refused count per test), each with
  an optional trace argument and nothing else changed (no-change proof: 288 hire-list builds and 11 400 picks identical
  before and after; `hirelings.py check` and `affixes.py check` output identical on a kept log). `combat.py` is a log
  checker with no forward function, so `combat_anim.py` writes the spec's rules out with a trace on the model's step,
  range, MulDiv and `Checker.get_defense`, and a test feeds its numbers to `Checker.tohit`, `defence`, `build`,
  `openwounds` and `crushing` as if logged. **Data (ADR-0009 risk 3):** the affix frames show counts only, at most five
  ids with weights, a bar strip with no text and one name (the winner's); the hire frames show name indices, ids,
  levels and prices; a test caps both. Tests: `test_combat_items_anim` (19), `test_schematic_kit`, `test_export_build`,
  `test_export_check`, `test_anim_schematic`; gate green. Blocks: `blocks-batch2.md`, "Combat, hirelings, affixes (x12e)".
- 2026-11-17, architect, review of lane/x12e (Opus, Tier A): **accept with fixes**, 11: overclaim 1, misread 1,
  omission 4, other 5. **No-change proof, reproduced** on a temporary worktree at 1616b1af (removed after):
  `hirelings.py check` over `hire-run.lst`'s 48 logs, `affixes.py check` over `affixes-manifest.txt`'s 51 logs with the
  oracle and with `--staff model`: all three outputs byte for byte identical to the lane's (0 mismatches); a
  deterministic batch of 328 hire-list builds (both games, every seller, each listed entry rolled in three
  difficulties) and 5 700 free-mode `Walk.pick` calls (every seventh base code, six ilvls, five seeds, both sides;
  2 192 with an id, 3 508 none, no exception) hashed identical before and after. The trace arguments only read; the
  refused counters are computed always and read by nothing else. **Row 17's copy:** combat.py has no forward function;
  the toy restates to-hit A1–A6 (no target mods, pct 0), C2 (a monster's `min(stat 20, 75)`), damage A steps 2, 3, 7
  and B1, delivery B3–B4 and E1–E2 on the model's step, range, MulDiv and `Checker.get_defense`, and the tests feed every
  number to `Checker.tohit`, `defence`, `build` (which recomputes min, max, ed and the end packet), `openwounds` (state,
  length, value) and `crushing` (the life after): the x12d precedent holds, `values: computed` kept. The tool builds
  `Checker(None)` and reads no file at cut time; only the test reads `hp_pct` from the image when present, and asserts
  the one-player term is 0. **Data rulings (ADR-0009 risk 3, ADR-0036):** row 18's name indices (the seller's range),
  ids, levels and prices of ten entries are kept: they reveal at most the two or three rows of one act and difficulty,
  each as one `Gold` and band, short illustrative rows. Row 19's counts, five merged ids with weights and one winner's
  name are kept; the strip was not: a bar per candidate gave all 32 weights of the shown pick to the pixel (W = 150 over
  880 px), past the row's "20 rows at most on a frame" (fix 6). **Fixes:** (1) overclaim: the delivery step said "the
  handlers of event 5 run newest first: open wounds, then crushing blow"; delivery B3 makes the order the unit's own
  registration order (the logged characters ran open wounds first): the step text, the frame caption and the block say
  "newest registered first, here open wounds then crushing blow". (2) misread: the hire entry frames said "draw 1 picks
  hireling id 1 among 2"; draw 1 picks a row (E3), whose id is shown: "DRAW 1: RANGE(k), A ROW" and "THAT ROW'S
  HIRELING ID", caption "picks row r of k (hireling id h)". (3) omission: the filter frame, "one line per test in the
  game's order", had no C4f line: added (AUTOMAGIC PICK ONLY: ANOTHER GROUP, refused 0). (4) omission: the combat test's
  miss branch was conditional and none of the six seed pairs missed, so it never ran: (5, 12345) misses and is in the
  traces; the assertion is unconditional. (5) omission: row 17's frames cite delivery E1 and E2 and the block had no § E
  anchor: added. (6) omission: the strip draws bars for the five listed candidates and the winner only, each run of the
  others one hatched block (`affix_anim.segments`); a test checks the nine filter tags and the segments. (7) other: the
  build's draws were labelled `RANGE` where damage A and B name `RangeB`, and the always-drawn step "burning step":
  `RANGEB` and "always drawn", tested. (8) other: the to-hit frame's AR row left its 20 unnamed: "CLASS FACTOR 20".
  (9) other: the filter frame's `REFUSED n` ran into `LEFT n`; right-aligned before it, rows 31 px. Blocks (corrected in
  `workspace/phase11/blocks-batch2.md`): (10) other: row 18 now says no pick of this build lands on a listed name (the
  frames show none); (11) other: row 19's "the group test" → "the test of a group already on the item". Frames viewed
  in both themes: combat 0–8, hire 0, 1, 5, 15 (both), affix 1, 3, 4, 5, 6, and the changed ones again after the fixes;
  every number checked against the specs (c = 100 × 335 ÷ 535 = 62, 62 × 30 × 2 ÷ 50 = 74; ed 40 + 80 = 120, lo 2816,
  hi 6195; Band(30) + 40 = 436; 300 ÷ 4 = 75 points, 57 600 − 3 319 = 54 281 units, 212.03; alvl 30 − 10 = 20; draw 2
  of 93 in the span 86..94). Seed 12345 for rows 18 and 19 is fine: no caption implies 0xC0FFEE. Place lines checked
  against combat, characters and items: right. **Cut:** the three blocks placed in the lane's wiki pages for one build
  (restored after), `export_build.py --out workspace/export-x12e-review`: 71 pages, 0 dropped, the three illustration
  folders; `export_check` 0 failures, 864 warnings; no DROP or REWRITE on the blocks; every caption sentence of the
  three present; the folder removed. Tests green: `test_combat_items_anim` (21), `test_schematic_kit`,
  `test_anim_schematic`, `test_export_build` (154), `test_export_check` (191); gate green. Ledger: verdict accept with
  fixes, 11 (overclaim 1, misread 1, omission 4, other 5). **For the spec-writer:** place the three blocks as their
  Place lines say; row 17's caption now names delivery § E, so the combat page's sentence after the diagram may say
  the stat-event order is the unit's registration order.
- 2026-11-17, spec-writer, lane/x12s (Phase 11 batch 2 placed). **Blocks** (from `workspace/phase11/blocks-batch2.md`,
  as their Place lines say; text, `seed` and `values` keys kept):

  | Row | Block id | Page | Section, place |
  |---|---|---|---|
  | 11 | `drlg-act1-links-c0ffee` | wiki/levels | "Laying out the act: level links", after the first paragraph |
  | 12 | `drlg-outdoor-burial-grounds-c0ffee` | wiki/levels | "Outdoor levels", after the building-block bullets |
  | 13 | `drlg-preset-lutw-rolls` | wiki/levels | "What a preset places", after "**Which seed.**" |
  | 14 | `drlg-warps-cave1-coldplains` | wiki/levels | "Warps, stairs and seams", after "**Pairing**" |
  | 9 | `monsters-pack-toy-room` | wiki/monsters | "Placement: where each monster stands", after the bullets |
  | 10 | `monsters-pool-wilderness2` | wiki/monsters | "Which monsters a level can have: the pool", after the bullets |
  | 15 | `path-search-toy-room` | wiki/pathing | "The search: types 0 and 16", after its first paragraph |
  | 16a | `path-walk-toy-room` | wiki/pathing | "The random walk: type 10", after the 31.7 % paragraph |
  | 16b | `path-spiral-toy-room` | wiki/pathing | "The spiral: type 14", end of section |
  | 20 | `items-runeword-sanctuary-match` | wiki/items-other-paths | "When the children make a runeword", after the flowchart |
  | 21 | `anim-move-walk-3-subtiles` | wiki/animation | "The step", after its first paragraph |
  | 17 | `combat-melee-hit-toy` | wiki/combat | "Draw order and chaining", after the player-attack diagram |
  | 18 | `hire-list-kashya-toy` | wiki/characters | "Hirelings: the hire list", after "The names are …" |
  | 19 | `affix-pick-lsd-30-prefix` | wiki/items | "Magic and rare items: affixes", after "**One affix pick**" |

  **Caption changes:** one, row 21: "With no point left, the path stops in that same frame (§ B5)." added after the
  frame count, as the x12d review offered (movement B5 `[C]`: the arrival follows in the step's frame). No caption was
  wrong against its page. **Combat page:** after the diagram, one sentence: open wounds and crushing blow run newest
  registered first, so their order is the attacker's own registration order, the logged characters running open
  wounds first (delivery B3 `[C]`), as the x12e review offered. **Cut:** `export_build.py --out workspace/export-x12s`:
  71 pages, 0 dropped, the 14 new illustration folders built; all 86 caption sentences of the 14 blocks and the two
  new sentences present in the cut; `export_check workspace/export-x12s --repo workspace/export-repo/` 0 failures, 877
  warnings (864 at the x12e review, the x12a captions' X12 level names among the new); the folder was removed. Gate
  green (E19 parses the blocks); wiki/animation's W4 stays as the x11s lane left it.
- 2026-11-17, architect, review of lane/x12s (Opus, Tier A) and **the redaction review of the cut it makes** (Phase 11
  batch 2's 14 pictures). **Tier A: accept with fixes**, 3: misread 1, bookkeeping splice 1, other 1. Checked: all 14
  placements against their Place lines (row 13 after the "**Which seed.**" paragraph, as the x12a review ruled: right)
  and in the flow of each page; captions against their specs, spot-checked on movement B1, B3 (S = 24576, 8 frames),
  B5 (`PathStop`, the arrival in the step's frame: the added sentence is true), pool C2 (`min(NumMon, 13, count)`),
  spawn F2's group size, search J (`r += 0x2580`, `a += 16`, 77 points), warps F1 and its worked example (k = 3, the
  fallback to slot 0; rank slot 3 without a room, slot 6), preset § 3 (R = 2087073643, R mod 3 = 1, dropped), the
  runeword frames (40 rows differ at rune 1, one at rune 2, record 41) and the combat frames (draws 68, 87, 503, 40, 0,
  90, 50): all true. The combat sentence is true to delivery B3 at its tag; "logged" stays: the exported combat page
  keeps the word 25 times, and its introduction names the logs as its method, so the export does not drop it (no DROP
  on any touched page but three older X9 sentences on items and characters). **Fixes:** (1) misread: the combat
  sentence said "their order is the attacker's own order of registration"; newest first runs them in the reverse of it:
  now "which of the two runs first depends on the order in which the attacker's handlers were registered; for the
  logged characters open wounds ran first". (2) other: on wiki/pathing the random walk's and the spiral's captions said
  "the same toy room", but their sections come before "The search: types 0 and 16", which introduces the room: the walk's
  caption now describes the room ("16 by 9 subtiles with a wall that has a gap, the room the search below uses") and
  the spiral's "same" points back to it. (3) bookkeeping splice: row 21's added sentence left a 180-character caption
  line: rewrapped.
  **Redaction review: pass; this cut's new pictures may be published** (`tools/export_publish.py --push`, the owner's).
  Cut (lane head plus the fixes): `export_build.py --out workspace/export-x12s-review`, 71 pages, 0 dropped, 25
  illustration folders (the 14 new) and the widget folder; `export_check … --repo workspace/export-repo/` **0
  failures, 877 warnings**. The 13 new warnings are all X12 on the four DRLG captions' level names (links 5: Rogue
  Encampment, Burial Grounds, Cold Plains, Black Marsh, "Moo Farm"; outdoor 2; preset 2: Lut Gholein, Lut Gholein's;
  warps 4: Cold Plains, Cave Level twice each), the class the levels page's prose already raises (x12a ruling); none
  matters. Every caption sentence and the three fixed texts are present in the cut. **Pictures opened** (dark, the
  cut's only theme: no block passes `--theme`): first, middle and last frame of all 14 (links 0, 9, 17; outdoor 0, 5,
  10; preset 0, 2, 3; warps 0, 1, 2; pack 0, 7, 13; pool 0, 4, 7; search 0, 3, 5; walk 0, 4, 7; spiral 0, 3, 5;
  runeword 0, 4, 7; move 0, 5, 9; combat 0, 4, 8; hire 0, 11, 22; affix 0, 3, 6) and affix 4 (the weights: five ids
  with weights, the rest one hatched block); the step-through `index.html` and `steps.json` of all 14 scanned for
  image addresses, `sub_`/`fn:`/`run:` tokens, tool, method and path words: none (the only hex values are flags,
  masks, cell bits and the struct offset `+0x28`, which the exported search spec states; combat's "as the logged
  characters did" is the page's own wording). No game art, no repository paths, no table dumps (pool: four
  candidates and three rarities; hire: ten entries' names, ids, levels and prices; affix: filter counts, five ids, one
  winner's name; pack: one row's MinGrp/MaxGrp); every number checked matches its caption. **Real site build** in a
  scratch copy of the export checkout (the cut and `workspace/export-repo/` copied over, the Astro caches removed):
  `SITE_BASE=/arpg-1-14d-notes/ npm run build` 72 pages; `check-site-links.mjs dist` 7 838 links in 97 pages, all
  resolve. **Chromium headless** (Playwright, served under the base): levels, monsters, pathing, items,
  items-other-paths, animation, combat, characters and randomness in dark and light at 1280 px and dark at 375 px:
  the CSP meta on each, no console error or warning, no failed request, every GIF loads (21 on the eight touched
  pages, 2 and the fallback on randomness), no page wider than its viewport at 375 px; the rng widget shows
  `015B2E77` for 12345 and `6AC6935F` for seed 1; the 14 step-through pages load at 375 px with their picture and no
  overflow (the one 404 is the browser's own `/favicon.ico` probe at the server root). **Manifest:**
  `docs/export/reviewed-pages.txt` unchanged (no new page). Scratch builds and copies deleted. Gate green. Ledger:
  verdict accept with fixes, 3 (misread 1, bookkeeping splice 1, other 1).
- 2026-11-17, spec-writer, lane/x13a (export readiness part A, backlog entry items 1–4, 6). Reword only: no claim, tag
  or anchor removed (front-matter counts unchanged, gate E6 green); evidence moved into the parenthetical after a tag or
  into an evidence-only parenthetical, a `run:`/plan/ADR subject replaced by the fact ("the recorded run (run:…)",
  "(plan 0044)"), a code-address call target named from `re/symbols.csv`, tool words moved out of the claim text (a
  mid-sentence tool parenthetical's tool segment moved to a new first Evidence bullet "How the statements above were
  read", per spec). Measured with `tools/export_build.py` on the cut-2 manifest plus the eleven pages (scratch manifest,
  `workspace/export-x13a`), words dropped and pseudocode blocks kept, Open questions and Evidence counted:

  | Spec | Words dropped before | after | Blocks kept before | after |
  |---|---|---|---|---|
  | items/vendors | 27.1 % | 10.3 % | 12/12 | 12/12 |
  | items/inventory | 32.8 % | 13.8 % | 13/18 | 18/18 |
  | items/use | 30.4 % | 17.7 % | 9/11 | 11/11 |
  | combat/README | 33.7 % | 19.6 % | 8/8 | 8/8 |
  | stats/README | 28.4 % | 13.7 % | 1/1 | 1/1 |
  | stats/aggregate | 38.9 % | 9.0 % | 10/10 | 10/10 |
  | stats/states | 34.9 % | 13.6 % | 9/9 | 9/9 |
  | save/d2s | 36.5 % | 21.7 % | 30/36 | 35/36 |
  | skills/catalogue | 30.0 % | 22.2 % | 3/21 | 21/21 |
  | conformance/README | 17.1 % | 17.1 % | 1/1 | 1/1 |
  | monsters/ai/catalogue | 21.4 % | 15.7 % | 131/148 | 131/148 |

  (2) skills/catalogue: every code-address call target in the pseudocode named (73 lines, the `re/symbols.csv` name
  without its `sub_` prefix, the address kept in the line's tail); the unnamed ones (the fatal path, a filter callback,
  a static table, `0x0056EBE0`, `0x00570590`) described without a name, the address in the tail; the four in-block
  constants of 6+ hex digits written as bits or decimal (`0x80000001`, `0x01020304`, `0x4020000`, `0x7FFFFFFF`); the
  mermaid diagrams' addresses named. Still out of the cut: its worked-example table (28 rows, X6, not named in the
  manifest) and its seed values (`0x280687C4`…, X1; an `allow-hex.txt` `section` line would admit them, as for the
  other worked examples): both architect-owned. conformance/README stays out: it is a guide to running
  `tools/golden.py` on our committed sample and the regenerated v1 set, neither of which the export ships; what a case
  holds is the golden-trace format's, so an export-facing page would be that format doc's, not a reword of this one.
  (3) monsters/ai/catalogue: the provenance sentence ("The block was checked against its anchored instructions (the
  finding's prose agrees)" and its eight correction variants) left 21 rows, now "The block is read from the code"; the
  rows, the dated corrections and the clone's added room test moved to a new first Evidence bullet; also the 23
  `p` lines' "(think 0x…, the plan 0069 Phase 4 model)" and the 11 entry-call rows' "from 0x… only" reworded (the
  addresses kept in their evidence parentheticals). Today 21 rows, not the entry's "about 90", carried the sentence.
  (4) Residue: data/excel (the archivist queue), combat/delivery and combat/README (the P1.3 review), items/economy
  (the three "architect review" notes, moved to Evidence), monsters/stats (the ruling, its anchor kept, the ruling in
  Evidence), path/README H2, hirelings/README, combat/reductions, sim/frame, skills/dispatch, monsters/pool and
  drlg/outdoor ("not in a finding" → "not read yet", 6), monsters/ai/machinery and quirks/README (the backlog route,
  "the finding's"), items/inventory's "the reverser's raise"; the Status column of the nine subsystem overview READMEs'
  *Files* tables removed (a spec's status is its front matter and the research map). (6) wiki/inventory's legend row
  and two forced cases ("a field written by hand"), wiki/game-data's "watched the game from before its start-up code".
  Not done here: items (5) and (7) and the part-B specs. Doubts for the review: the "the recorded run (run:…)"
  substitution reads stiffly in a few places ("the 325 of the recorded run and the 40 of the recorded run"); vendors'
  Baal-chain item and d2s's "the other callers" and summary-lines sentences still drop (`broken`, 82, 80 and 29 words);
  monsters/ai/catalogue R142a still says "the finding's". Gate green.
- 2026-11-17, architect, Tier A review of lane/x13a and the redaction review of its specs (Opus). Verdict **accept
  with fixes (7: misread 1, omission 3, wrong anchor 1, other 2)**. *Tier A.* (1) No claim changed: per spec the
  multisets of tags, `run:`/`src:`/`fn:` tokens and finding links are equal before and after but for collapsed
  duplicate `run:` ids (stats/README) and merged links (monsters/ai/catalogue's dated corrections, now one Evidence
  bullet); every removed address is a named call target (132 pairs matched to `re/symbols.csv` by script), a value
  written as bits or decimal (rechecked: `0x2001002` bits 1, 12, 25; `0x4020000` bits 17, 26; `0x80000001` bits 31,
  0; `0x00080000` bit 19; `0x01020304` 16 909 060) or a mermaid label; no tag moved. One anchor lost: inventory C1's
  `ItemSkillQtyAdd` (0x0055C270) kept its name and lost its address; `fn:` restored (wrong anchor). Moved evidence
  sits in each spec's new first Evidence bullet. Gate green. (2) **Ruling on method words:** "the recorded run",
  "read from the code" and "logged" stay, as plain words (decision 8; the export's tags page explains both levels in
  these words). But one phrase for every run misleads: it named emulations "recorded" and made two runs in one
  sentence read as one (vendors G1's "325 … and the 40 of the recorded run", D3–D4, inventory's two pairs, states'
  shrine counts). Each of the 70 is now the run's own name (the first and second vendors runs, the two-client run,
  the stats run, the first and second shortfalls runs, the ground, inventory and use emulations, the lock scan, the
  save play run, …), the id kept after it (misread). (3) Status columns: accepted. The status is each spec's front
  matter and its research-map row (gate E15); no gate rule or link reads the columns, and none is left in any
  overview README. (4) The cut rewrites "### The ADR-0014 boundary" to "### The boundary" and "(the boundary
  section, ADR-0014)" to "(the boundary section)"; the five links to `#the-adr-0014-boundary` lose their label in
  the cut as before (their label holds the ADR). Accepted. (5) conformance/README stays out: agreed (a guide to our
  checker and trace set; a page on what a case holds would be the golden-trace format's). (6) skills/catalogue:
  18 names checked by hand against `re/symbols.csv` (`ReviveTargetTest`, `MonTestN`, `TauntTargetTest`,
  `NearestByFilter`, `MonAiDelay`, `SkillDo09Frenzy`, `SkillDo70DoubleSwing`, `SpawnClassByBase`,
  `ItemTargetRandomPoint`, `CorpsePickNear`, the five `MissCbReseed*`, `SkillSt21Revive`, `MonCorpseTestDead`,
  `AttractTargetTest`, `UnitAlignGet`, `ConversionTest`, `UnitMarkUpdated`), all right. *Fixes in the specs*
  (omission): units the lane reworked that still dropped or lost words: vendors' Baal chain (unnamed call
  targets as subjects; now described, `ClientRemove` and `TownPlayerRemove` named), use's request `0x61` row, the
  Purpose sentences of use and inventory ("Scope is [ADR-0025]:"), save/d2s's other-callers bullet (a run id nested in
  a parenthetical breaks "run"), its `level` header row (`STATS_GetUnitStat`), its worked example's first sentence
  (the paths split into their own sentence), the read flow's legacy reader (`ReadSaveLegacy`), the `unk_2c`
  accessors, skills/catalogue A1 (a finding range after "of") and C0 (`jmp MissileMoveCollide`), inventory's
  inventory-record row (magic 16 909 060); a removal inside a code span the builder keeps silently: states B3's "only
  `0x005BEE15` lies", C2's `call 0x005C0B50` and the cold and freeze callbacks, monsters/ai/catalogue R50's
  `jmp [eax*4 + g_AiMephistoStateJumps]` and `AiUnitSearch(G, U, &blk, AiMephistoPickCb, 1)` (the cut showed the call
  with four arguments), use H5's `→` range; other: inventory F3's "; The code holds", R142a's "the finding's".
  *Redaction review.* Cut `workspace/export-x13a-review` from the lane with the ten specs added (routes
  spec-items/vendors, use, inventory; spec-combat/overview; new groups spec-stats 20 (overview, aggregate, states)
  and spec-save 26 (d2s); spec-skills/catalogue; spec-monster-ai/catalogue; no route collision): 81 pages, 0
  dropped; specs words dropped 16.4 %; `export_check … --repo workspace/export-repo/`: **0 failures**, 1010 warnings
  (X12, as before). Added, words dropped and blocks kept: items/vendors 9.2 % 12/12, items/use 14.5 % 11/11,
  items/inventory 12.9 % 18/18, combat/README 19.5 % 8/8, stats/README 13.7 % 1/1, stats/aggregate 9.0 % 10/10,
  stats/states 13.6 % 9/9, save/d2s 13.2 % 35/36 (its reproduce command drops), skills/catalogue 10.0 % 21/21,
  monsters/ai/catalogue 15.7 % 131/148. Every drop line of the ten read (evidence bullets, Open questions, the
  vendors gambling list, the d2s survey-summary sentence, which describes our tool's output); the 17 catalogue
  blocks that drop hold unnamed call targets in their code part (X1), and their rows read as rows without a block (no
  dangling reference); naming them is part B's work. Read whole as a reader: stats/states, items/use (its golem and
  request sections), skills/catalogue §§ A–B. Left out: none of the ten. *X6:* named `save/d2s.md 315` (the header's
  fields, a file layout), `save/d2s.md 1253` (the worked example's item bit fields) and `skills/catalogue.md 151` (our
  step table of every draw by seed); vendors 658 stays out (item-table content). *allow-hex:* `0BADF00D` (a value
  written by hand into the pass-through field, an illustrative input); pins `00800010` and `800000` on save/d2s
  (the worked example's stored flags, bits 4 and 23, and bit 23 itself in I1's line and the example), `006E9C81` on
  combat/README (the low word after step 3 of example 1, recomputed: `0109323f:20d5284f` steps to
  `0be642ca:006e9c81`). The existing `Worked example` sections already covered skills/catalogue's seeds and the d2s
  checksum. *Hand grep of the whole cut:* `sub_`, `DAT_`, `FUN_`, `findings/`, `ADR-`, plan numbers, `.py`, `.log`,
  `.claude`, Ghidra, harness, objdump, debugger, the repository name, `/home`: 0; `run:` ids 0; image addresses 2,
  both the pinned flag values of save/d2s; `fn:`/`src:` 4, all code text (`src: boss`, `hitfn:`). Manifest and
  `reviewed-pages.txt` updated (2026-11-17). *Found for the builder* (backlog
  [2026-11-17-architect-archivist-export-builder-code-span-and-anchor-column](../backlog/archive/2026-11-17-architect-archivist-export-builder-code-span-and-anchor-column.md)):
  an image-range value removed from inside a code span leaves a changed formula or seed in units the builder keeps,
  on published pages too (drlg/README and maze seed words, drlg/outdoor's four `[ + …]` reads, items/affixes and
  economy seed words, items/properties, monsters/stats `hp ≥` …); and an Inputs table whose cells are all `tbl:`
  anchors loses its name column (15 published specs). The export-readiness entry stays open for part B.
- 2026-11-17, archivist, lane/x13f (builder: code-span removals break the unit; tbl: columns kept; → ranges). Backlog
  entry from the lane/x13a review, items 1–3, in `tools/export_build.py`. *Rules.* (1) A removal inside a backtick
  span that holds anything else (an address, run id, anchor, path or plan reference taken out of it) makes the unit
  `broken` (it drops, reported as such); a span of only removed tokens goes whole as before; spans are paired left to
  right, so a removal between two spans is not inside one. A table cell broken this way becomes a dash. In a pseudocode
  line's code part a removed value beside an operator or an arrow (`if hp ≥ : hp ←`, `& `) leaves the line as it was and
  the block drops (the tail stays lenient). Values that are not addresses but lie in the image range (`0x400000`,
  `0x800000`, `0x7FFFFF`, a seed's low word) still go and now drop their unit: the spec-writer names, pins or rewords.
  (2) `redact_table`: a column whose every filled cell is `tbl:` anchors is a name column and stays (its cells rewrite
  to the name as in prose); a column that mixes `tbl:` with other evidence goes as before. (3) `→` ranges collapse like
  en-dash ranges. Tests: 169 checks in test_export_build (both ways for each: a seed span, a formula span, a call span,
  an address-only span, two address-only spans, a removal between spans, tbl: column kept / mixed column dropped /
  fn:+data: column dropped, the arrow range, the fence operand and the fence tail); export_check 191, widgets 274,
  publish 44 green. *Measure* (cut of main 87b7df0f against the lane's, text only, then one full build with
  illustrations; 81 pages, 0 dropped; specs words dropped 16.6 % (60 692 of 364 889), same as before: the 24 units
  that drop carry few words, tables that keep a name column count more words kept, net per page below); no spec near
  the bar (highest combat/to-hit 24.3 %, anim/movement 24.1 %, both unchanged). Newly dropped prose and table units 24
  (drlg/README 1, maze 5, outdoor 4, warps 1, items/properties 1, quest-drops 2, economy 1, inventory 1, combat/damage 1,
  combat/delivery 1, stats/aggregate 1, skills/dispatch 2, path/README 1, sim/frame 1, save/d2s 1) and 7 pseudocode
  blocks (drlg/lifecycle E, outdoor K, items/economy C and D, properties F, monsters/stats B, player/creation G; all a
  flag or cap value, `0x400000`, `0x800000`, `0x7FFFFF`, left without its operand); words dropped changed on 26 specs
  (e.g. drlg/maze 439 to 583, outdoor 1 536 to 1 676, delivery 1 141 to 1 310, d2s 1 243 to 1 409; fewer where a name
  column is kept: drlg/README 675 to 630, items/use 607 to 561, skills/catalogue 474 to 416); about 90 table rows
  changed words (their Inputs-table name column kept, 15 specs) and 4 rows whose evidence cell is now a dash
  (skills/dispatch and missiles Constants, path/README A, items/affixes example 3's seed cell). Not changed: an arrow
  chain whose head is an address (`(→ ActCreate)` in save/d2s D4 and a chain in quests/travel G1) keeps its lone arrow,
  one for the reader to reword. Full list: `/tmp/claude-1000/-home-igor-Work-recompilcation-project/eb61de30-a30a-401a-a3db-30c67be2439b/scratchpad/x13f/changes-final.txt` (prose and tables; the fence blocks are the seven above).
  `export_check … --repo workspace/export-repo/`: 0 failures, 1014 warnings. Backlog entry closed.
- 2026-11-17, architect, Tier A review of lane/x13f (Opus). Verdict **accept with fixes (8: misread 3, omission 2,
  other 3)**, the fixes made in the review. *The check asked for:* a scratch script compared, page by page, every code
  span and every pseudocode line of the cut with the source after the documented rewrites (anchor to name, `sub_`
  prefix, a citation's folder, `at 0x…`). On the lane's cut 11 spans and 382 lines differed, and some were kept units
  whose code had changed: the operand hole missed `≠` (`if class 527 and ≠ 0`, `if ≠ 0: SetMode(8, 0, 0); end` with
  the call after it gone), call targets outside an operator (`call 0x005B0D70` → `call`, `5. 0x00588DD0` → `5.`) and
  call arguments (`Build(0x006F0B10, check Act5C)` → `Build(check Act5C)`, `Pfx(0x…, 0x…)` → `Pfx`), and command lines
  lost their paths (`python3 -I tools/monpool.py pool workspace/…` → `python3 -I pool`). Two older rules did the same.
  The evidence-parenthetical rule took a call's argument and a span's parenthetical for evidence: `R = Init(0x6AC6935F)`
  → `R = Init`, the seed `(0x280687C4, 0x13ADFE65)` → an empty span. The link rewrite ran inside fenced blocks:
  `g_PathPlanFuncs[ctx.type](ctx)` → `g_PathPlanFuncsctx.type`, `OutdoorAct[a](L)` → `OutdoorActa`. And a span over
  a line break, or one a sentence split cut in two (`#### R<n>. Row <n> `), escaped the span rule:
  `` `excel_bin.py diff` `` → `` ` diff` ``. *Fixes* (`tools/export_build.py`, 25 checks added to test_export_build).
  (1, omission) A pseudocode code part breaks on a removal inside a call's parentheses or outside every parenthetical,
  unless it is an address label (`init 0x005EA510:`, `at 0x…`). A removal in a parenthetical after a space
  (`do 58 (0x005C56C0, Revive)`) is a label and still goes. (2, misread) A parenthetical right after a word, or inside a
  code span, is never an evidence parenthetical. (3, misread) In a fenced block a link is only re-targeted when it
  names an exported page; otherwise it stays as written. (4, omission) Spans pair across a line break, path spans pair
  left to right (no longer matched between two spans), and a sentence never splits inside a span. (5, misread) A table
  cell that opens with its tag and breaks keeps the tag (the lane's dash dropped the tag of three Constants and path
  rows). A value cell whose span broke (items/affixes example 3's seed) breaks the row: a dash would read as "none",
  the x70b2 ruling. (6, other) Arrows: a chain whose head or end was an address leaves no lone arrow (save/d2s D4 now
  reads "(`ActCreate`)"). `73 → 0x0059DB20: refuse` reads `73: refuse`, and a tail `[C] → 0x0056E2F0 or X` reads
  `[C] → X`. (7, other) Tails: a block opener's own colon stays (`case 2  (0x005EC069), x ← t:` had lost it), and
  `; 0x005689E5, the tick` keeps its comment marker. (8, other) An anchor run into a span is one span
  (`` data:g_ObjOperateFns@…`[OperateFn]` `` → `` `g_ObjOperateFns[OperateFn]` ``). *After the fixes* (a full build
  with illustrations, 81 pages, 0 dropped): 27 501 spans checked, 3 differ, all one source defect (unescaped `|` in
  code spans inside the path/README and path/search table cells, which GFM splits whatever the builder does). 12 338
  fence lines checked, 93 differ, each an address label or an evidence parenthetical gone (`(0x00730514)`,
  `init 0x…:`, `(0x005AF030, Frozen Orb)` → `(Frozen Orb)`). Specs: units dropped 973 of 12 428, words dropped
  16.7 % (60 828 of 364 886), fenced blocks kept 808 of 895 (the lane's 838). The highest page is unchanged
  (combat/to-hit 24.3 %). Against main 87b7df0f, 65 units of published spec pages newly drop: 27 prose units and rows
  and 38 pseudocode blocks. They are listed for the spec-writer, sorted into pin, reword and source fix, in backlog
  [2026-11-17-architect-spec-writer-export-cut-units-dropped-by-code-span-rules](../backlog/archive/2026-11-17-architect-spec-writer-export-cut-units-dropped-by-code-span-rules.md);
  the seed constant `0x53454953` of skills/missiles B1, which the parenthetical rule had removed, now fails X1 and
  needs a value entry there. Tests: export_build 194, export_check 191, widgets 274, publish 44, all green.
  `export_check … --repo workspace/export-repo/`: 0 failures, 1018 warnings. Gate green.
- 2026-11-17, spec-writer, lane/x13r (65 units dropped by the code-span rules, backlog
  [2026-11-17-architect-spec-writer-export-cut-units-dropped-by-code-span-rules](../backlog/archive/2026-11-17-architect-spec-writer-export-cut-units-dropped-by-code-span-rules.md)).
  Reword only: no claim, tag or anchor changed (the `[C]`/`[I]`/`[L]` counts of the 29 touched specs are unchanged, and
  no line count changed above a manifest `table` line). The review's list holds 70 DROP lines (the 68 the entry's text
  names, its count says 65, plus anim/timing N1 and data/calc G); measured on a cut of this branch against a cut
  of main 7b984160 by (page, section, kind): **62 restored** with the current allow-hex, **6 restored once the six
  lines below land** (checked with them in a scratch copy of allow-hex.txt), **2 stay dropped** (class C, ruled). Three
  blocks outside the list come back too (items/economy F4 and G3, quests/travel's portal block), so spec units dropped
  fall 874 → 809 in the no-illustration cut.
  **A (values).** Flags and caps reworded, no pin: `0x400000` → `1 << 22` / bit 22 (drlg/outdoor K1, drlg/lifecycle
  E1, items/economy C8, D1, D5 and F4, items/properties F3, items/quest-drops F0, stats/aggregate H6 and the
  `ethereal (flag bit 22)` label), `0x800000` → `1 << 23` (drlg/outdoor K1, drlg/lifecycle E3, save/d2s I1), the caps
  `0x800000`/`0x7FFFFF` → 8388608/8388607 with a `2^23` comment (monsters/stats B8, player/creation G1). Proposed for
  the review to add to docs/export/allow-hex.txt (each seed word is one `Step` of the seed the page gives, recomputed):
  `53454953   the seed constant the monster-owner hook initialises its local seed with (skills/missiles § B1), outside the code image`;
  `pin 0090CE8A specs/drlg/maze.md :: the worked example's seed after R0's draw, E18C3A55:0090CE8A, one Step of 015B2E7F:0000029A`;
  `pin 0090CE8A specs/drlg/README.md :: the same seed word, worked example row 9, one Step of row 2's 015B2E7F:0000029A`;
  `pin 004BC4A3 specs/items/affixes.md :: example 3's seed after draw 1, 004bc4a3:517d17c7, one Step of c35f85d3:0d511944`;
  `pin 007C890F specs/items/economy.md :: example 8's attacker seed after one Step, 007c890f:575b5184, from d1712f2d:0b0beb6e`;
  `pin 006E9C81 specs/combat/damage.md :: the worked example's row 2 seed after RangeB(71104), 0be642ca:006e9c81, one Step of 0109323f:20d5284f`.
  **B (addresses).** Table reads by symbol: `g_RiverForgeSpecials[r]`, `g_BorderCornerIdx[in + 9·out]`,
  `g_A1RiverIdx[p][0|1]`, `g_JungleClearingDefs[v >> 4]`, `g_JungleClearingOff[L.id − 76]` (the read base is 304
  bytes before the symbol), `g_PropFuncTable[f]`, `g_MonModeRecords[mode]`, `[g_PathFaceStep + edx*4]`, the warps
  tables as `T[k]` = `g_ActLinkTables + 240·k`; maze's unnamed Down/Waypoint/Prev/Next tables as "entry `r` of the …
  table". Call targets by symbol (each checked in re/symbols.csv): `VertexRingBuild`, `OutVertsToCells`,
  `RoomAdjLink`, `JungleLayout`, `KurastStack`, `UnitAddStat`, `ItemInvNonEmpty`, `PLAYER_SpendSkillPoint`,
  `SaveViaCallback`, `PLRSAVE_WriteFile`, `STATE_DefaultRemoveCB`, `PlayerGetClient`, `InvBookSkillsRebuild`,
  `A1Q29_NpcTalk`, `A5Q5_SummitPortalAdd`/`Remove`, `PlayerHostileToAny`, `UnitGetSubX`/`Y`, `ItemVarInvGfx`,
  `MissCbReseedFromArg`, `MissCbReseedZigzag`, and in skills/catalogue `RedemptionChanceCb`, `FuryChainCb`,
  `CountUnitsInRange`/`Cb`, `SkillDo06UnitCb`, `AURA_ApplyToTarget`, `CurseApplyCb`, `BaalCorpseCb`, `GroundDropCell`,
  `MissSubDisc`, `MissCbReseedPathX`(`PlusArg`), `MissCbReseedRoll`, `MissCbAddStat25`, `InfernoEnd`(`Monster`),
  `ShapeRemoveCb`, `ItemTargetRandomPoint`, `UnitStoredUnit9C`, `WhipChangeClass`, `VineCreateRow`, `UnitMsgA3`,
  `CorpseTestF12`, `ImpregnateEndCb`, `UnitMarkUpdated`. A call argument takes the name and its anchor goes to the
  line's tail. Unnamed targets (no symbol) are worded by role with the address as a label parenthetical the cut
  drops: the error routine and reallocation (items/inventory), the AI quest calls of R31/R54 ("the first test",
  "its partner", "its quest call"), `call an unnamed routine (0x005B0D70)`, `the drop function (0x00585E00)`, the mask
  byte of dispatch H3, sim/frame's two calls and its global dword, save/d2s's set-state table and host flag.
  **C (tools).** Reworded, restored: monsters/pool (the command moves into the prose sentence before the block,
  which the cut drops as before; the block holds the output only), monsters/ai/catalogue's count sentence,
  items/sockets-runewords E3, save/d2s E (`setwp`), data/calc G (`a model of our own`), anim/timing N1 (the walker
  names, X9). **Stay dropped, ruled:** save/d2s J's `survey` block and the worked example's reproduce block, which
  are command lines and their output only.
  **D.** `\|` in the code spans of path/search's `h` row and path/README's `window` row (the cut's tables now have
  their four cells; spans differ 0).
  **Measure** (full build with illustrations): 81 pages, 0 dropped; specs units dropped 908 of 12 429, words dropped
  16.3 %, fenced blocks kept 850 of 895; highest page combat/to-hit 24.3 %, none over 25 %. `export_check …
  --repo workspace/export-repo/`: 0 failures, 1022 warnings. Span equality: 27 635 spans, 0 differ; 13 888 fence lines,
  359 differ, each an address label, an `init 0x…:` label, a `sub_` prefix or an evidence tail gone (the restored
  blocks carry more of them). Build deleted. **For x13b:** none of the 70 lines is in its files. Gate green.
- 2026-11-17, architect, Tier A review of lane/x13r (Opus). Verdict **accept with fixes (3: other 3)**, the fixes made
  in the review. *No claim changed:* a word diff of the 29 specs (7b984160..cac0f980) shows rewording only; per file the
  `[C]`/`[I]`/`[L]` counts and the distinct `fn:`/`data:`/`run:` anchors are unchanged, finding links kept. Flags read
  `1 << 22` / bit 22 for `0x400000` and `1 << 23` for `0x800000`, the caps 8388608/8388607 exact. Table bases checked
  against re/symbols.csv: `g_BorderCornerIdx` 0x006F1088, `g_A1RiverIdx` 0x006F2680, `g_JungleClearingDefs` 0x006F13BC,
  `g_PropFuncTable` 0x007462F8, `g_MonModeRecords` 0x006E2260, `g_PathFaceStep` 0x006EB548, `g_RiverForgeSpecials`
  0x006F0474 are the read bases the old text gave; `g_JungleClearingOff` is 0x006F2370, 0x130 = 304 bytes = 76 entries
  past the old base 0x006F2240, so `[L.id − 76]` is exact; `T[k] = g_ActLinkTables + 240·k` gives the nine old
  operands for k = 0…8 in the order written. All 48 names the lane wrote for an address checked against
  re/symbols.csv (none wrong); the 31 addresses worded by role (calls, the maze tables, the mask byte, the host flag,
  the set-state table) have no symbol, and the roles ("the first test", "its
  partner", the error routine, the reallocation) are the finding's own words (ai/0013 row 31, items/inventory A2/F3).
  Manifest `table` lines: all 19 headers at the same line in the lane's files. *Fixes (other 3).* (1) The proposed
  value entry `53454953` refused: a four-character code, a domain value the owner kept out of allow-hex; skills/missiles
  B1 now writes `Init(1397049683)`, the same word in decimal (rng/seeds' `0x53454953` will need the same when that page
  joins the cut). (2) save/d2s I3 and I4 read "the table" in the cut once the address went; named "the set-state
  table" by role. (3) monsters/ai/catalogue R31's "if the first test = 0: its partner" had no verb; "call its partner".
  *allow-hex* (docs/export/allow-hex.txt, one block "review of lane/x13r"): the five pins added after recomputing each
  as one `tools/rng.py` step of the seed its page gives (015B2E7F:0000029A → E18C3A55:0090CE8A for drlg/maze and
  drlg/README row 9, c35f85d3:0d511944 → 004bc4a3:517d17c7 for items/affixes example 3, d1712f2d:0b0beb6e →
  007c890f:575b5184 for items/economy § 8, 0109323f:20d5284f → 0be642ca:006e9c81 for combat/damage row 2); none in
  re/symbols.csv. *Cut* (full build with illustrations, review fixes in): 81 pages, 0 dropped; specs units dropped
  902 of 12 429, words 16.2 %; highest page combat/to-hit 24.3 %, none over 25 %. `export_check … --repo
  workspace/export-repo/`: 0 failures, 1024 warnings. Span equality: 27 664 spans, 0 differ; 13 888 fence lines, 360
  differ, each a label, `init 0x…:`, `sub_` prefix or evidence tail gone. *The 70 units:* 62 restored by the lane's
  rewording, 5 restored by the pins, 1 (missiles B1) by the decimal rewording, 2 stay dropped by ruling (save/d2s J's
  `survey` block and the worked example's reproduce block: command lines only, nothing a reader loses). Read as a
  reader: drlg/warps A1, drlg/outdoor J4, monsters/ai R31, save/d2s I3/I4. Build deleted. Backlog entry closed. Gate
  green.
- 2026-11-17, spec-writer, lane/x13b (export readiness part B). Backlog entry items 1 (the eight specs still out),
  5 and 7. Reword only, by part A's method: no tag added, moved or removed (per-spec tag counts equal, gate E6 green),
  every `run:`/`fn:`/`data:`/`tbl:`/`struct:` token and finding link kept; an address taken out of the text went into
  the statement's evidence parenthetical or a pseudocode tail; a named call target from `re/symbols.csv` replaces the
  address in code and in prose (`OutRoomAlloc`, `MazeLevelCreate`, `RoomRestoredGet`, `PortalPartnerGet`,
  `ClientRoomAt`, `MissCbReseed*`, `AiSt11`/`AiSt12`, …), an unnamed one is described ("an unnamed site",
  `unnamed(Shrines[code])` with the address in the tail). Each run is named by what it is (the seed-tree run and the
  second seed-tree run, the room-k run and the room-k sweep, the collision run and the collision sweep, the first and
  second path runs, the objects run and the H5b objects run, the spawn run, the third AI run and the rev 5 AI run, the
  strings run, the lifecycle run, the first monsters sweep, the second chain run, …), the id kept in the parenthetical.
  A run id in running text became "the … run (run:…)"; inside an outer parenthetical, the id moved to the statement's
  own. Tool words (objdump, Ghidra, logger, `tools/…` commands, log file paths) left the claims for a new first Evidence
  bullet "How the statements above were read" in seven specs ("the decoded instructions", "a second walk", "the log
  lines"). Three source shapes the builder reads as broken, fixed where met: a parenthetical holding words beside its
  anchors ("3102 room creations", "row 44", "Phase 1": the words moved out, or "row N" and "Phase 1" into the link
  label), a table cell that opens with a `fn:sub_…` chain (its subject vanishes: names written before the anchors),
  and a `[README.md](README.md)` label (now "the DRLG overview"). Domain masks the allowlist keeps out (its 2026-11-17
  owner note) are written as shifts, exact and checked by hand: `0x3F0FF80` → `0x3F << 20 | 0x1FF << 7`, `0x3F0FF00`,
  `0x1E0FF00`, `0x1E00000`, `0x01E00100` (in a table cell `(0xF << 21) + 0x100`, no `|`), the theme fill values
  `0x12 << 16`, `0xA << 20`, `0x16 << 20` and `0x6 << 20` (the last, `0x600000`, lay in the image range and was cut
  silently before); seeds' `0x0213AE09` now reads as its decimal 34844169, spawn K's logged low word as "low 16 bits
  0 (high half `0xD17D`)". Measured with a scratch manifest adding the eight pages (groups spec-rng 10 and
  spec-objects 15) and the two table lines below, a scratch allowlist adding the proposals below, full build with
  illustrations (`workspace/export-x13b`, 89 pages, 0 dropped; specs 16.2 % of words dropped), Open questions and
  Evidence counted:

  | Spec | Words dropped before | after | Blocks kept before | after |
  |---|---|---|---|---|
  | rng/README | 35.9 % | 12.7 % | 3/3 | 3/3 |
  | rng/seeds | 59.5 % | 15.6 % | 6/7 | 7/7 |
  | data/strings | 25.0 % | 11.1 % | 11/11 | 11/11 |
  | drlg/room-tiles | 44.1 % | 14.5 % | 11/14 | 13/13 |
  | drlg/collision | 25.9 % | 13.7 % | 19/20 | 20/20 |
  | monsters/spawn | 25.2 % | 11.2 % | 17/19 | 19/19 |
  | monsters/ai/README | 31.4 % | 18.5 % | 8/11 | 11/11 |
  | objects/README | 29.7 % | 14.0 % | 16/19 | 19/19 |
  | monsters/special (item 5) | 18.4 % | 14.1 % | 13/13 | 13/13 |

  (room-tiles' fourteenth block was the worked example's command line, now in Evidence.) `export_check …
  --repo workspace/export-repo/` with the scratch manifest and allowlist: 0 failures, 1067 warnings (X12). Span
  equality (the x13f review's script, run on the scratch manifest): 31 296 spans, 3 differ, all path/README and
  path/search's known `|` cells; 14 202 fence lines, 100 differ, on the nine pages each an evidence parenthetical or
  an address label gone. What still drops on the eight, besides Evidence and Open questions: monsters/ai/README H's
  per-think table (line 537, ruled out) and spawn's worked-example sentence on `MinionsSpawn`, whose seed
  `FB397EDF:00835546` has a high word in the image range; a `pin` does not admit it, because the check's pin test
  covers the `0x`/hex-letter spellings only, not an all-digit bare value ("bare address of the code image" is not in
  `HEX_WHATS`): for the archivist, or the example writes that seed `0x`-prefixed. (5) monsters/special § D: the
  Weights and `xfer` columns are gone from the 32-row table; the paragraph above it points to
  [MonUMod § Pick weights per difficulty](../tables/MonUMod.md#pick-weights-per-difficulty) and the table doc's
  *Columns*, which hold every weight, `xfer`, `fPick`, `exclude1` and `enabled` the columns copied; the table now holds
  only our handler and draw readings and can be named. (7) drlg/collision's worked example: the active room is "the one at
  tiles (1032, 1024)", its near rooms and right neighbour are named by tile position, the `CB` line 8034 and the `SN`
  and member lines' numbers left the text (their numbers, the heap pointers and the log name are in the new Evidence
  bullet); objects' and spawn's examples name their session instead of the log file, likewise. *Proposals for the
  architect's files.* manifest: `group spec-rng 10 Spec: Randomness`, `group spec-objects 15 Spec: Objects`;
  `page specs/rng/README.md spec-rng 1 overview`, `page specs/rng/seeds.md spec-rng 2`, `page specs/data/strings.md
  spec-data 5`, `page specs/drlg/room-tiles.md spec-drlg 8`, `page specs/drlg/collision.md spec-drlg 9`,
  `page specs/monsters/spawn.md spec-monsters 6`, `page specs/monsters/ai/README.md spec-monster-ai 1 overview`,
  `page specs/objects/README.md spec-objects 1 overview` (orders chosen to fill the gaps; the cut-2 comment's left-out
  list then names only conformance/README); `table specs/monsters/special.md 383 our per-mod table of handlers and
  draws (the MonUMod values are the table doc's)` in place of the left-out ruling on 381; `table
  specs/objects/README.md 51 our index of the table columns the objects code reads (a schema, no rows)`, as ruled.
  allow-hex: `pin 0090CE87 specs/rng/README.md` (the high word after step 4 of the worked example, as on
  wiki/randomness); `53454953` (rng/seeds' constant local seed, the same value x13f's review asks for skills/missiles
  B1); `pin 00835546 specs/monsters/spawn.md` only with the check change above. The worked examples of the eight
  already have `section` lines. reviewed-pages.txt: the eight at their redaction review. *Stays out:*
  conformance/README (part A's ruling); monsters/ai/README's per-think table. Doubts: "the H5b objects run" and "the
  rev 5 AI run" keep a batch and revision label as their name, the only distinction the ids carry; seeds 7a's
  "In the second seed-tree run 114 server unit seeds had the parent `game+0xD0` every time" moved a parenthetical count
  into a sentence before the same tag; § D's `[C]`/`[I]` row tags still cover the dropped weights only through the table
  doc. Gate green.
- 2026-11-17, architect, Tier A review of lane/x13b and the redaction review of its specs (Opus). Verdict **accept
  with fixes (11: misread 1, omission 7, other 3)**. *Tier A.* (1) No claim changed: per spec the tag counts are equal
  before and after (gate E6), every `run:`/`fn:`/`data:`/`tbl:`/`struct:` id and finding link is kept (three ids
  seen once less in text were duplicates of their statement's parenthetical; rng/seeds gained `MissSubNearReseed` and
  `UnitSeedFromEntry`, objects/README `PortalPartnerGet`, each the name of the address it replaced), and every
  address taken out of the text is still in its spec. 29 call targets named in place of an address matched to
  `re/symbols.csv` by script (`OutRoomAlloc`, `ClientRoomAt`, `RoomRestoredGet`, `ActiveRoomFree`, `Bit2TileNew`,
  `PortalPartnerGet`, `PortalPartnerCreate`, `ObjEvent7Thunk`, `QUESTS_ObjectEvent`, `ARoomSeedStep`, `AiIdle`,
  `UnitInit`, `MissSubNearReseed`, the five `MissCbReseed*`, `g_Orient89Levels`, …), all right; the 30 others were
  instruction sites with no symbol, each moved into its statement's evidence. The shifts recomputed:
  `0x3F << 20 | 0x1FF << 7` = `0x3F0FF80`, `0x3F << 20 | 0xFF << 8` = `0x3F0FF00`, `0xF << 21 | 0xFF << 8` =
  `0x1E0FF00`, `0xF << 21` = `0x1E00000`, `(0xF << 21) + 0x100` = `0x1E00100`, `0x12 << 16`, `0xA << 20`,
  `0x16 << 20`, `0x6 << 20` the old fill values; 34844169 = `0x0213AE09`; spawn K's "low 16 bits 0 (high half
  `0xD17D`)" is `0xD17D0000`. Seeds 7a keeps its claim, count and tag (the 114 seeds now in the sentence, the id in
  the tag's parenthetical). *Run names* (part A's ruling): "the H5b objects run" names a plan batch, not the run: now
  "the second objects run" (objects/README, 6; the spec already says "either objects run"); the same kind of label
  was left as a name elsewhere: data/strings' "H3b calls/hovers/run" (now the data-load sweep, 3), rng/seeds' "the
  H1a session" (the save-load sweep) and "that run" (the second seed-tree run), monsters/ai/README's "S7b counts"
  (the two frame runs) (omission). "The rev 5 AI run" stays: it names the logger revision the run used, which is what
  sets it apart from the third AI run. *Item 5:* § D's table holds only our handler and draw readings; its row tags
  rest on the handler and run anchors they always had. The paragraph said every row's weights and `xfer` were
  "listed" in the table doc; the doc's § Pick weights sums up the pick mods only (misread): now "read from the table:
  the *Columns* define them, and § Pick weights sums up the stock weights, `xfer`, `fPick` and `exclude1` of the pick
  mods". *Item 7:* collision's example still named the pass by its `SN` line and called its case "the R2 case of the
  logging plan": both reworded (omission). *Item 4 (special's other dropping units), fixed:* the § D bullet (a run id
  as subject), § H's MonPlace bullet (an address as subject), the two § J rows (`STATE_Set` named; the 540 and 175
  calls described, their addresses in the tag), the worked example's tool sentence and four "Source:" sentences (the
  log paths and lines moved to a new first Evidence bullet) (omission); left for a later pass: the *Inputs and
  oracles* sentence on plans 0018 and 0014. *Fixes from reading the cut* (omission): rng/seeds' *Entry points* cells,
  `fn:sub_…` chains that the builder removes whole (the function column read `—` or `→ →`), now names before a
  parenthetical of anchors; seeds' step note 2 (a comma line left by a code-span parenthetical), note 3's
  "stores the act ." (an address as object), the pierce-count and Armageddon parentheticals ("for the client/server
  pair", "dated note" outside their link labels); collision's "the architect ruled", its "run:… held 514 of them";
  room-tiles' sentence-initial `Run:2026-10-16-sweep-roomk`, which the check's case-sensitive run rule let through.
  *Redaction review.* Cut `workspace/export-x13b-review` (full, illustrations on): 89 pages, 0 dropped; specs words
  dropped 16.2 % (67 308 of 415 915); `export_check … --repo workspace/export-repo/`: **0 failures**, 1070 warnings
  (X12). Span equality (the x13f review's script): 31 342 spans, 3 differ (path/README and path/search's known `|`
  cells); 14 202 fence lines, 100 differ, each an evidence parenthetical or address label gone. Added, words dropped
  and blocks kept: rng/README 12.7 % 3/3, rng/seeds 15.7 % 7/7, data/strings 11.1 % 11/11, drlg/room-tiles 14.5 %
  13/13, drlg/collision 13.7 % 20/20, monsters/spawn 11.0 % 19/19, monsters/ai/README 18.5 % 11/11 (its per-think
  table, line 537, stays out by the ruling), objects/README 14.0 % 19/19; monsters/special, already in, 11.2 % 13/13.
  Every drop line of the nine read: Evidence and Open questions, the ai/README table, special's plan sentence. Read
  whole in the cut: rng/seeds and drlg/collision. Left out: none. *Manifest:* groups spec-rng 10 and spec-objects 15;
  pages rng/README (spec-rng 1 overview), rng/seeds (2), data/strings (spec-data 3), drlg/room-tiles (spec-drlg 6),
  drlg/collision (8), monsters/spawn (spec-monsters 3), monsters/ai/README (spec-monster-ai 1 overview),
  objects/README (spec-objects 1 overview): the lane's 5, 8, 9 and 6 left the overview tables' order and its gaps
  (other); no route collision. Tables named: special 384 (our per-mod handler and draw table), objects/README 51 (a
  column index); left out: monsters/ai/README 537. *allow-hex:* `pin 0090CE87 specs/rng/README.md` (step 4's high
  word, recomputed from `Init(12345)`); `pin 00835546 specs/monsters/spawn.md` (the leader seed's high word after the
  minion-count draw, recomputed: `013AE0B5:2C86C396` steps to `FB397EDF:00835546`, low:high). **Ruling on
  `53454953`:** it is the four-character code `SEIS`, a domain value the owner's note keeps out of the allowlist; not
  admitted. rng/seeds now writes "the constant 1397049683, whose four bytes spell `SEIS` high byte first" (exact, and
  no hex) (other); skills/missiles B1 is asked to do the same. **Ruling on `00835546`:** the smaller change is the
  spec's: the example writes that seed `0xFB397EDF:0x00835546`, whose `0x` spelling the pin test covers; `HEX_WHATS`
  is not widened (other). *Hand grep of the cut:* `sub_`, `DAT_`, `FUN_`, `findings/`, `ADR-`, plan numbers, `.py`,
  `.log`, `.claude`, Ghidra, harness, objdump, debugger, the repository name, `/home`, `workspace/`, `lane/`: 0; `run:`
  ids 1, items/inventory K1's sentence-initial `Run:` (published since x13a); image addresses 2, the pins of spawn and
  save/d2s; "architect" 2 (monsters/stats, combat/README, both published before). `reviewed-pages.txt`: the eight
  added. *Backlog:* [archivist: export builder sub_ anchor cells and the run-id case](../backlog/archive/2026-11-17-architect-archivist-export-builder-sub-anchor-cells-and-run-case.md)
  (179 *Entry points* rows on published pages read `—` or bare arrows; X2's `run:` rule is case-sensitive);
  [spec-writer: export cut residue after x13b](../backlog/archive/2026-11-17-architect-spec-writer-export-cut-residue-after-x13b.md)
  (special's plan sentence, collision's log-line names, the published residue above, skills/missiles B1's constant).
  Gate green.
- 2026-11-17, spec-writer, lane/x14s (export residue after x13b). Reword only: no claim, tag, anchor or count changed;
  line counts above every named table kept (21 `table` lines checked, each on its header). (1) monsters/special
  *Inputs and oracles*: the plan 0018/0014 sentence now states the fact ("The model of this spec takes the place of
  every special-path oracle the earlier spawn model read from the logs: …"), its counts, tag and run kept; the two tool
  names moved to the Evidence bullet of monsters/0002 § 9. The sentence is now in the cut (special's drops 10 → 9
  units, 11.2 % → 10.5 % words). (2) drlg/collision: the log-line names outside the worked example say what the line
  records: `COR` → corpse-mark lines (entry table, § F5 bullets, the seven-callers table and its header, § D rows 528,
  529, 532, an open question), `DC` → `deadCol`-test lines, `SN` → a pass-entry line logged at the server's
  population pass (the address now in a parenthetical) and the pass-entry snapshots (§ D row 7), `MTT`/`MK0` → 1 777
  tile-placement lines, no mask-test line (§ Inputs); the run ids stay in the tags. (3) items/inventory K1: "The first
  inventory run's 10 of 10 …" for the sentence-initial `Run:` id (still in the parenthetical); monsters/stats Evidence:
  "the scope ruling of plan 0025 Phase 1", "(a review ruling of 2026-10-15)"; combat/README Evidence: "and its
  review", "the review ruling on the creation draws (plan 0045 P1.2)"; sim/frame K7: "the function names the rows
  carry". (4) skills/missiles B1: `Init(1397049683)`, "a constant whose four bytes spell `SEIS` high byte first", as
  rng/seeds; no hex, no allowlist change. (5) monsters/ai/README "the rev 5 AI run": kept as the review accepted it; no
  plainer name found (ai/machinery names the run only by its id). Seen, not in the entry: path/README's corpse table
  and chain/README's oracle table keep `COR`/`SN`-style log-line names in the cut. Checks: full build (89 pages, 0
  dropped); `export_check … --repo workspace/export-repo/` 0 failures, 1076 warnings, the same set as the cut of
  42269df1; span equality 31 495 spans, 0 differ, fence lines 367 differ, as on the base cut; touched specs 10.5 %
  to 21.9 % words dropped; builds deleted. Gate green.
- 2026-11-17 — **Review of lane/x14s (orchestrator, Opus): accept, 0 fixes.** Per touched spec the sorted multiset of
  tags and `fn:`/`data:`/`tbl:`/`struct:`/`run:`/`src:` anchors is identical before and after (seven specs); the word
  diff is rewording only (special's plan sentence states the fact and moves the tool names to Evidence; collision's
  log-line names say what the line records; inventory K1 names its run; missiles B1 spells `SEIS` beside the decimal
  constant, as rng/seeds does; stats and combat/README Evidence lose "the architect's"). The lane's cut: 0 failures,
  span equality 0 differ, all 21 `table` lines on their headers. Left for a later pass: log-line names in path/README's
  corpse table and chain/README's oracle table. Ledger: accept, 0 fixes.
- 2026-11-17, archivist, lane/x14a (sub_ anchors kept as names; run: case-insensitive; test folder). *Rules*
  (`tools/export_build.py`, `tools/export_check.py`): a `fn:sub_XXXXXXXX_Name@0x…` anchor, in prose and in a table cell,
  reads as `` `Name` `` when `Name` passes X1–X5 (no hex run of 6+ digits, no `sub_`, no `DAT_`); a `sub_` anchor with no
  readable name, or whose name holds hex, is still removed whole, and the unit follows the existing `broken` rules.
  X2's `run:` rule and the builder's run-id removal are case-insensitive (`Run:2026-…` at a sentence start fails the
  check, and the builder removes it and drops the unit as broken, so the cut stays green). `tools/test_anim_schematic.py`
  writes to its own `tempfile.mkdtemp` folder under `workspace/render` (the tools accept only outputs under workspace/),
  removed at the end of the run. A second builder rule, found by the span check: a list item or paragraph that ends inside a code span (a source line break puts `+ i)` at a line start, which the Markdown parse makes a bullet of its own, as in monsters/spawn's `classes + 4·(start`) is dropped as broken, because units that held a named `sub_` anchor and were dropped before now survive and exposed it. Tests: export_build 200, export_check 193, widgets 274, publish 44, anim_schematic 5, all
  green. *Measured* (the before figures below are wrong, corrected at the review: see the review entry) (full build, illustrations on, 42269df1 before and after): 89 pages both; units dropped 1734 of 19344
  → 969 of 19671, words dropped 95816 of 540150 (17.7%) → 73884 of 553175 (13.4%); `specs/items/properties.md`, a page
  dropped whole before, is now written (6279 words, 19 units dropped); the units that changed are the *Entry points*
  rows and sentences that held a named `sub_` anchor, on 80 of the 89 pages (every wiki page loses 1–38 dropped
  units). `export_check … --repo workspace/export-repo/`: 0 failures. Span equality (spaneq.py, its anchor list taught that a `sub_` anchor reads as its name): 32321 spans, 0 differ (28415 before);
  fence lines 367 of 15752 differ (306 of 12662 before), the same evidence tails and addresses removed, no new kind. K1 of items/inventory is not in either build as a `Run:` sentence; the
  rule would drop it as broken. Gate green.
- 2026-11-17, architect, review of lane/x14a (Opus Tier A): **accept with fixes** (3: miscount 1, omission 1, other 1).
  *The properties finding.* `specs/items/properties.md` was never dropped in a cut built from the main checkout or a
  lane worktree: the x70a and x70b2 review trials and the Phase 9 cuts all write it (268 units, 19 dropped), and so does
  42269df1. The lane's "before" build ran in a worktree whose folder name, `base`, X4 reads as an identity string
  (`git_identity` takes the work tree's basename; the review's first base build reproduced it): the title "Base stats and
  the property roll" failed X4, the page dropped whole, and 749 other units holding the word dropped with it. The
  published site has not been missing the page. *Measured again* (42269df1 built in a worktree with a neutral name,
  against the lane; full builds, illustrations on): units dropped 965 of 19671 before, 969 after (965 after the
  review's rewraps), words dropped 12.5% → 13.3% (the dropped units now count the names they hold); the drop sets
  differ by 8 units: `items/uniques-sets`' `item.seed` row is kept now, items/inventory K1 drops as broken on its
  sentence-initial `Run:` id (fixed on main by lane/x14s), and the two items each of combat/to-hit and monsters/spawn
  that end inside a code span. The rule's real effect is in the kept units: table rows whose cell was an em dash 735 →
  449, lines with bare arrows 47 → 14. *Names:* 2084 distinct `sub_` names the rule emits from the manifest pages, every
  one passing X1–X5 and X9; none is a Ghidra placeholder or carries a tool word (`Thunk` in four, `Stub` in three and
  `Hook` in two are the game's own code words; left). 5 names are removed whole for a hex-letter run of 6
  (`AiGroupDeadCb`, `BarricadeCaveEntries`, …): a safe false positive. *Meaning:* span equality 32321 spans, 0 differ
  (the script's anchor list given the name rule); the fence-line difference set is the same 367 lines in both builds
  (the lane's 306 was the artifact's), so the rule changes no fence. 31 changed units read across 12 pages (maze,
  party, collision, stats, d2s, machinery, uniques-sets, room-tiles, movement, affixes, quality, lifecycle) against
  their sources: whole and true; evidence parentheticals that also hold words now keep their names, as `fn:` anchors
  always did. *Fixes:* the builder's run-id removal `[Rr]un:` → `(?i:run):`, as X2 (an upper-case `RUN:` id passed the
  builder to fail the check), tests both ways (`RUN:` removed, `Run: the thing` kept); combat/to-hit's
  `` `2·alvl/(alvl + dlvl)` `` and monsters/spawn's `` `classes + 4·(start + i)` `` rewrapped so no line starts with
  `+ ` inside a span (CommonMark made each a list item of its own, in the published site too; no claim or line count
  changed, and neither page has a manifest `table` line); both items are written again. The lane's measured line
  above marked as corrected. The odd-backtick rule counts backticks, so a double-backtick span would drop its unit (none
  in the manifest pages); a drop, never a leak. The leftover `workspace/render/test-anim` folder removed (nothing reads
  it). Tests: export_build 202, export_check 193, widgets 274, publish 44, anim_schematic 5, all green;
  `export_check … --repo workspace/export-repo/`: 0 failures; gate green. Merge over b854ef38: one conflict, this log's
  tail (append on both sides; keep both).
- 2026-11-18 — **Phase 11 batches 1 and 2 served.** The owner pushed the export repository's `main` (five cut commits:
  batch 1 and the rng widget, batch 2, the builder's code-span fix with part A's ten specs, part B's eight specs, the
  named `sub_` anchors); the Pages run passed, and the randomness page, `widgets/rng-stepper/widget.js`,
  `spec-items/properties/`, `spec-rng/seeds/` and `world/levels/` answer 200. The site now serves 89 manifest pages,
  22 new animations and one widget.
- 2026-11-19, archivist, lane/x16c (Phase 11 batch 3, rows 30 and 31: widgets `seedtree` and `path`). Delivered:
  - **`tools/widgets/seedtree/`** (row 30): `compute` is the seed tree of rng/seeds steps 1 to 5 on BigInt words (map and
    game seeds from N, five act seeds with Act II's tomb pairs and Act III's bit, one level's seed as a u32 sum, up to eight
    rooms, each one level draw then one room step); `mount` has four number inputs, a seed preset and one table. `widget.json`:
    multiplier, init word, the tomb constants, four toy seeds, five act labels. The twin reshapes `seedtree_anim.trace`
    (the DRLG model's `Act` and `Seed`), no second copy of the rule. 10 fixture cases (seed 0xC0FFEE over every act, an
    Act II seed whose pair draw rejects, both ends of the seed range, clamped inputs). Level and room numbers are plain
    counters of our own, no level table is read. Fallback: row 2's `rng-seed-tree-c0ffee`.
  - **`tools/widgets/path/`** (row 31): `compute` is search L2 and L3 for type 0 on the toy room of `tools/path_anim.py`
    (the walk, the cell store kept across passes, the fan, Advance, Reduce); `mount` has start, target, bound and pass inputs,
    a 16 by 9 grid of toggle buttons for the walls, a pass table and a live line. `widget.json` holds the stock step, fan and
    direction-octant tables as nested `rows: page` objects (arrays may not nest, so each row is an object; the fan keeps the
    entries the spec's L3 table lists, 8 for the root row and 5 for the others) and the eight toy wall cells. The twin is
    `path_anim.search` (the model `tools/test_path_anim.py` compares with the emulation), no entry point was needed;
    `tools/path.py` is the log comparer and has no search model of its own. 12 fixture cases (the spec's example wall with
    bounds 33, 0 and 255, open lines, a sealed target, a start beside its target, clamped inputs, wall cells typed over the
    start). The widget's input rules (clamping, walls kept in the room and off the start and target) are restated in the twin.
  - **Registration and tests**: `tools/widgets/twins_x16c.py` (twins and cases, kept apart from `twins.py` so parallel lanes
    do not collide; `twins.py` has three added lines), `tools/test_widgets.py` gains a generic first-integer fixture mutation
    and a per-widget `MUTATION` table (it was rng-specific), and spec-derived checks for both widgets: 84 checks, green.
    Both sources pass X13 (the allowlist of member names forced `lead`, `limit`, `ending`, `grid`, `pos`, `way`, `reached`
    for the words `base`, `bound`, `end`, `cells`, `pt`, `face`, `found`; regular expressions do not lex, so wall text is
    split by hand).
  - **Blocks**: `workspace/phase11/blocks-batch3-x16c.md` (not in git): two `widget` blocks with their places and captions,
    both with an illustration fallback already on the page.
  - **Doubts for the review**: the octant table (25 values) is marked `rows: page` because PathDirTables lists it, but the
    search page itself does not print it (it links there); the pass slider shows each pass's final cell store and its chain,
    not one expansion at a time (the model records no per-expansion trace and a trace would not fit the fixture); the wall
    parser accepts `3.0` where the twin's `int()` rejects it (no fixture case has one); styling of the grid buttons relies on
    the host's generic `.widget-host` styles only (marks are text, no colour).
- 2026-11-19, architect, lane/x16c review (Tier A, Opus; ADR-0037). **Accept with fixes 4.** Read whole: both
  `widget.js`, both `widget.json`, `twins_x16c.py`, `seedtree_anim.trace`, `path_anim.search`, the test changes, the
  block drafts; checked against rng/seeds steps 1 to 5 and path/search §§ A1 to A3, L2, L3. Both computes follow the
  spec and their twins (the fan's truncation to 5 entries for a child is safe: a sixth entry is read only on the try that
  pops the node). Rulings on the lane's doubts: (1) **`rows: page` means the exported page prints the rows**; a link to
  a table doc is not enough, and `docs/tables/` is outside the export, so the 25 octant values could not stay in
  `widget.json` (nor be called `toy`). Fixed: the widget computes the octant by a rule (a term whose double is at most
  the other's size is dropped, the step with the signs left, (0, 0) gives the `octant.zero` parameter 6), recomputed
  25 of 25 against `path_anim.DIR_OCTANT` by a new test check; no spec states that rule yet, so **row 31's block is held
  out of the cut** until spec-path/search § A2 does
  ([backlog](../backlog/archive/2026-11-19-architect-spec-writer-path-dir-octant-rule.md)). (2) The wall parser now takes an
  optional sign and ASCII digits only, in the widget and the twin alike, with a fixture case of nine odd wall texts
  (`3.0`, `1e0`, `0x7`, `1_0`, three parts, spaces, signs). (3) Per-pass final state is acceptable: neither the caption
  nor the intro claims a step per expansion, and the candidate row's "watch the search" is met by the pass slider.
  (4) The seedtree labels and caption called the typed N a "game seed", the name the table gives Init(N); now "seed N,
  as an override gives it" (the caption in the block draft too). Tests 87 checks green, twins check clean, gate green.
- 2026-11-19, archivist, lane/x16b (Phase 11 batch 3: scripted widgets, rows 26 to 29; ADR-0037). Delivered four widgets in
  `tools/widgets/<name>/` after rng's pattern (pure `compute`, DOM-only `mount`, `widget.json` of toy or page rows only,
  `fixture.json` written by a twin in `twins.py` from the existing model, no second copy of a rule):
  - **`monstat`** (row 26): the twin builds a `monstats.Tables` with no game data (20 invented level rows and two invented
    monsters packed at the offsets the model reads) and calls `Model.monlvl_stats`; the widget restates stats § A (row
    `min(level, last)`, none below 0, difficulty 0 below 1 and at most 2, `MulDiv(row, cell, 100)`, raw cells). 14 fixture cases.
    `MulDiv` is the 32-bit branch only (the toy values never leave it).
  - **`merc`** (row 27): the twin builds a `hirelings.Tables` with three invented band rows (the first band at level 6, so
    levels below it give a negative `d`) and calls `set_level`; the widget shows the 12 stats of hirelings § G, skills left out
    (the toy rows carry none). 14 cases (band edges, 1, 98, 99, clamped inputs).
  - **`quality`** (row 28): the twin builds a `quality.Tables` of one invented item and the page's records 2 to 5 (the ratio
    table of quality § Inputs, `"rows": "page"`) and calls `roll` with `range_b` forced to lose, so `trace` and `cf["pre"]`
    list every test the roll reaches; the widget restates § C to § E (the magic-find factor, minimum, ratio word, `c`) and
    adds the chance to win (about 128 in `c`) and the chain of results as exact rationals floored to parts per million (BigInt
    in JS, `Fraction` in the twin). Item kinds: ordinary, never rare, always magic, always normal. 19 cases (MF -150 to 1000,
    the diminishing edge at 10 and 11, ratio word 1024, `c` below 1, clamped inputs).
  - **`checksum`** (row 29): the twin calls `d2s.checksum` on each prefix of the typed bytes (no game file, a text field of
    at most 32 hex bytes; offsets 12 to 15 count as 0); the page's 8-digit hex values stay out of the fallback text (X1), which
    is decimal. 12 cases (empty, the zeroed field, 32 and 33 bytes, bad tokens).
  - **Shared files, additive**: `twins.py` (four twins, cases, fallbacks); `test_widgets.py` (a `MUTATIONS` entry per widget in
    place of rng's one hard-coded text, a generic wrong-fixture bump, a `MOUNT_SHOWS` check per new widget); `smoke_mount.mjs`
    sets rng's typed values only for rng. X13's allowlists forced renames of data and output keys (`stats`, `ratio`, `base`,
    `raw`, `d`, `c`, `code`, `bytes`, `error`, `count`, `total` are browser member names): the keys are `result`, `scaled`,
    `rowVals`, `plain`, `dlt`, `chance`, `rc`, `typed`, `fault`, `tally`, `whole`; and `Number.isNaN` and a hex-digit string
    are out, `parseInt(ch, 16)` is in.
  - **Blocks** for the spec-writer: `workspace/phase11/blocks-batch3-x16b.md` (ids `monstat-scaler`, `merc-stats`,
    `quality-chances`, `checksum-stepper`, all with the text fallback; `quality-chances` on the quality spec page, as
    moved at the review below). A scratch build of the four blocks (text fallbacks) dropped none and `check_cut` was clean.
  - **Doubts**: no browser run (node stand-in DOM only; the CSP and the host were exercised for rng in x11w); the quality
    widget's "about 128 in `c`" is the page's own phrase, the draw is `low mod c` and slightly non-uniform; the toy numbers
    of rows 26, 27 and 29 are invented and say so in their intro line.
- 2026-11-19, architect, review of lane/x16b (Tier A on Opus, ADR-0037). Read every `widget.js` and `widget.json`
  whole, the four twins and the fixtures, against monsters/stats § A, hirelings § G, items/quality § A to § E and
  save/d2s § B. Each widget computes only from its `widget.json`; monstat, merc and checksum rows are `toy`; the
  compute matches the spec and its twin on every fixture case, the quality fixture holds the spec's worked examples 1
  and 3 (`c` 50816 … 128; 27022, 9862, 5604, 1344, 1024, −2176), and a 1 600-case random sweep (400 per widget, out of
  range inputs included) gives no difference from the twins. X13's script and data rules pass on all four
  (`js_problems`, `json_problems`); gate green; `test_widgets.py` 141 checks. **Rulings:** (1) quality's records 2 to 5
  are `page` rows only where the page shows them: the block draft put the widget on wiki/items.md, which shows no
  ItemRatio row and no `*Min` value, so `"rows": "page"` did not hold there (ADR-0037, What it may read). The spec
  page that row 28 names, spec-items/quality, shows records 0 to 5 and the four minimums in its Inputs and keeps them
  in the cut; the block moves there, at the end of § E, with the text fallback (a scratch build placed it, wrote the
  fallback table and the check had 0 failures). The four rows are a subset of a reviewed six-row table the same page
  prints, so they are page text, not data lifted from the game files; ADR-0031 concerns constants of the code image and
  is not engaged. (2) The item kinds are the three ItemTypes flags § A3, § D2 and § D3 test (`Normal`, `Rare`,
  `Magic`); an always-magic kind with `Rare` set matches D3's note (rings, amulets). Supported. (3) merc below the first
  band: hirelings § G states that negative `d` truncates and was logged down to −41, so levels 1 to 5 show real
  behaviour and are not clamped. (4) monstat's 32-bit `MulDiv` branch: the inputs only pick among toy rows whose
  largest values (row 9 055, cell 160) sit below both thresholds of § A1, so no input reaches the other branches; the
  note says so. Browser run: still owed, at the redaction review of the cut that first carries these widgets
  (ADR-0037, Review). **Verdict: accept with fixes 2** (misread 1: the quality block placed where its `page` rows are
  not shown, moved to the spec page and the lane's log line corrected; omission 1: the quality caption left out the
  always-normal kind the widget offers).
- 2026-11-19, archivist, lane/x16a (Phase 11 batch 3: rows 23, 24, 25). Delivered:
  - **Widgets** `tools/widgets/tohit/` (to-hit § A3 to A5: the percent, the swaps, `100 AR / (AR + DEF)`, the level factor,
    the 5..95 clamp; 15 fixture cases), `damage/` (damage § B and reductions § A, B1, B2 for the physical field: bounds in
    256ths, the enhanced-damage percent with both shares, the one draw on a seed typed as Init(seed), P, the flat reduction,
    the resistance with a player's cap of 50; 20 cases, the damage page's worked example `lo 41369, hi 112473` among them)
    and `breakpoints/` (timing J1, J2, K1 to K3 for five kinds: attack, cast, get-hit, block, block under Holy Shield;
    length, event frame, the breakpoint rows with least factor and least stat, capped at 40 rows; 27 cases, K3's two
    stock illustrations among them, 14 to 8 frames for the cast and 10 to 4 for the get-hit). Each follows rng's pattern:
    pure `compute`, DOM-only `mount`, `widget.json` of rule parameters, toy presets and text only, `fixture.json` written
    by a twin in `tools/widgets/twins.py`.
  - **Entry points added to the models** (the twin calls what the log checker calls, one copy of each rule):
    `tools/combat.py` gains `tohit_chance`, `phys_ed`, `phys_bounds`, `reduce_value`, `resist_final`, `resist_cap_default` and
    `percent_scale`, lifted out of `Checker.tohit`, the physical roll, `resist_for`, `reduce` and `reductions` (the checker
    now calls them; `combat.py check` on `c37p2-cls-h-plains.log` gives the same output as before, `SUMMARY mismatches=0
    events=1035`, and `test_combat_items_anim.py` 21 tests are green). The breakpoints twin uses `tools/anim_rates.py`
    (`bonus`, `rate_*`, `closed_len`, `sched_len`, `least_x`, `least_stat`), which `anim.py` itself imports as `AR`; the
    row named `anim.py`, but the rate and breakpoint functions live in `anim_rates.py`.
  - **Harness**: `test_widgets.py` takes a per-widget mutation (`MUTATIONS`) and bumps the first number of a case instead of
    reading rng's `rows[0].result`; `smoke_mount.mjs` types rng's values only into rng. Both additive.
  - **X13 lessons** (for the next widget lanes): the allowlist refuses `x[k]` for a variable `k` (use `.at(i)`, or fixed
    member names), `Object`, an array literal whose first item is a string, and any member or key that a browser object
    also has and the list does not name (`count`, `speed`, `event`, `offset`, `range`, `labels`, `scale`, `points`, `rate`,
    `x`, `r`, `c`); bare `frames`, `base`, `event` are refused as names. Fixed names for the inputs and `Array.find` over
    `items` objects (`rows: toy`) replaced the keyed lookups.
  - **Blocks** drafted for the spec-writer in `workspace/phase11/blocks-batch3-x16a.md` (row 23 `fallback: text`, row 24
    the `combat-melee-hit-toy` illustration, row 25 `anim-schedule-cast-fcr20`); no spec or wiki page edited.
  - **Open**: the damage widget leaves out the criticals, the elemental and monster-only fields, absorption and the bypass
    flags, and says so in its note; the to-hit widget takes AR and the percent as typed numbers (no player or monster
    composition); the breakpoint rows start at the current length and go down.
- 2026-11-19, architect, review of lane/x16a (Opus, Tier A; ADR-0037's widget review: every `widget.js` read whole,
  every `widget.json`, the twins). **Accept with fixes**, 6: error 3, omission 2, other 1.
  - **Checked.** No widget reads anything but its `widget.json`; every array is `toy`, no row comes from a game table,
    the one hex value is the multiplier `allow-hex.txt` admits. To-hit A3–A5, damage B1, reductions A1, B1 and B2 (the
    physical row) and timing J1, J2, K1–K3 are restated as written, `MulDiv`'s branches as monsters/stats A1. The
    `combat.py` refactor keeps behaviour: `check -v` over all 77 logs in `workspace/logs/combat/` gives byte-identical
    output before and after (`c37p2-cls-h-plains.log`: `SUMMARY mismatches=0 events=1035`). X13 and E21 pass; gate green.
  - **Fixes (error).** (1) Breakpoints' fixture called `bcase` with `event=` and `speed=`, the names X13 made the lane
    drop: 12 of 27 cases kept the default event 7 and speed 256, so "a slow speed with a rate of 0", "an event that does
    not fire" and the speed-200 and speed-1024 cases tested nothing they named; now `evt=` and `spd=`, with a rate-0 case
    that reaches 0. (2) The event frame used K1's `N = n − 1`, which fires frame S in a one-step action
    (`r ≥ 256 (F − S)`), where E2 and E1's loop fire none; the widget now takes `N = ⌈256 (F − S) / r⌉ − 1`, the twin
    reads the event from `anim_rates.sched_len` (E1's loop, not the closed form), and two one-step cases are added.
    Backlog entry `2026-11-19-architect-spec-writer-timing-k1-no-step-event` asks the spec-writer to align K1 with E2.
    (3) To-hit showed one swap when both of A4's ran (a negative defence that leaves the attack rating negative); the
    widget and the twin now say `both`, with a case.
  - **Fixes (omission).** (4) The attack's "weapon term" defaulted to 0, so the default attack sat on the factor floor
    15 (108 frames for 16); J2's term is stat 68, 100 on a new player (J5): the input is labelled so, defaults to 100,
    and the caption says so. (5) The damage note named neither the bypass flags, sanctuary, the mastery nor absorption;
    it now lists them, with absorption stated as the physical row's absence. The to-hit note now says the make-up of
    AR, its percent and DEF is not shown.
  - **Fix (other).** (6) Breakpoints' length text says 1 when the rate is 0, and the event text gives E2's bound. The
    block drafts in `workspace/phase11/blocks-batch3-x16a.md` carry fixes 4 and 5 in the row 24 and 25 captions.
- 2026-11-19, spec-writer, lane/x16s (Phase 11 batch 3 placed; two backlog entries). **Blocks** (from
  `workspace/phase11/blocks-batch3-x16a.md`, `-x16b.md`, `-x16c.md`, text, `fallback` and `illustrates` kept; the
  x16a file lacked its last closing fence, added on placement):

  | Row | Block id | Page | Section, place |
  |---|---|---|---|
  | 23 | `tohit-calculator` | wiki/combat | "Will it hit? The chance to hit", end of section (before "## Defence"; the draft's "before Building the damage" skips Defence and Block) |
  | 24 | `damage-reduced-toy` | wiki/combat | "Draw order and chaining", right after its fallback `combat-melee-hit-toy` (the draft's places come before that illustration, where the builder refuses a fallback not yet built) |
  | 25 | `breakpoints-calculator` | wiki/animation | "Breakpoints", after the two stock-record bullets |
  | 26 | `monstat-scaler` | wiki/monsters | "Stats at creation", after step 6 |
  | 27 | `merc-stats` | wiki/characters | "The mercenary's stats per level", after the cubic-experience paragraph |
  | 28 | `quality-chances` | spec-items/quality | end of § E, before "### F. Boundaries" (the x16b review's ruling) |
  | 29 | `checksum-stepper` | wiki/saves | "The checksum", after its first paragraph |
  | 30 | `seedtree-expander` | wiki/randomness | "Rooms: one draw each", right after `rng-seed-tree-c0ffee` |
  | 31 | `path-search-toy-grid` | spec-path/search | end of § L3, before "#### L4" (the lane/x16s review's ruling; drafted on wiki/pathing after `path-search-toy-room`; released: § A2 below) |

  **Caption changes:** two. Row 25: "and the logged runs" cut from its *Not shown* sentence, which the builder dropped
  (X9). Row 31: one sentence added on the octant ("the direction toward the target that picks the root's direction and
  each child's row of the fan is the octant, which search § A2 states cell by cell: …, a target on the node itself
  gives direction 6"), rewrapped. The other captions were checked against their spec sections and found consistent
  with their pages' text; they keep the reviewed wording.
  **Backlog, octant rule** (closed): search § A2 gains a `[C]` bullet stating `PathDirOctant` by cases (a term whose
  double is at most the other's size goes to 0, the index of the signed step, `(0, 0)` gives 6), recomputed here over
  the table doc's 25 listed values, 25 of 25 (the listing `tools/test_path_survey.py` compares with the image), the
  same as the x16c review's check against `path_anim.DIR_OCTANT`; anchors data:g_DirOctant, fn:PathDirOctant,
  run:2026-11-03-path-emu-2, the table doc and ADR-0031; it says the equality is on the image's elements and the table
  stays listed. First draft dropped whole from the cut as `broken` (an "ADR-0031's" possessive inside the item):
  rewritten with the references in the trailing parenthesis, and the step order written out (the cut drops the Inputs
  anchor column, so the symbol name alone did not lead to the steps). Search C 117 → 118, updated 2026-11-19, the
  research map row's tags and date with it; wiki/pathing's `based_on` date moved to 2026-11-19.
  **Backlog, K1 vs E2** (closed): timing K1 keeps `n(r)` and the sources' count `N(r) = n(r) − 1` and bounds the event
  frames by a new `steps(r) = ⌈256 (F − S) / r⌉ − 1`, E2's N; a `[C]` K1 note states the no-step exception from E2's
  own evidence (104 emulated no-step schedules with an event, run:2026-11-16-sweep2-s6e; no logged schedule meets it).
  L4's "`T + N`, `N = n − 1`" scoped to an action with a step. Timing C 175 → 176, updated 2026-11-19, the map row
  with it. No new evidence used.
  **Cut:** `export_build.py --out workspace/export-x16s` (the builder refuses an `--out` outside `workspace/`): 89
  pages, 0 dropped; 10 widget folders (the 9 new and rng), fallback picture for rows 24, 25, 30 and 31, text fallback
  for 23, 26 to 29; no caption sentence and none of the new spec text dropped (the only DROP on touched units is the
  pre-existing timing § K tool sentence); `export_check workspace/export-x16s --repo workspace/export-repo/` **0
  failures**, 1 084 warnings, all X12, none on a new caption or the new A2/K1 text. The folder was removed. Gate green.
  **Open for the review:** (1) the path widget's `tables.step` and `tables.fan` are `"rows": "page"`, printed on
  spec-path/search (Inputs, § L3) but not on wiki/pathing, where the block's Place line puts it; by the x16b ruling on
  quality ("rows the page around it already shows") the block may belong on the search spec page, which has no
  illustration for it to fall back on. (2) No browser run (ADR-0037's owed run at the redaction review). (3)
  wiki/animation's W4 on timing is left as it was (dated 2026-11-16), the K1 change not restated there; the page's
  no-step sentence already agrees with E2.
- 2026-11-19, architect, review of lane/x16s (Opus, Tier A) and **the redaction review of the cut it makes** (Phase 11
  batch 3's nine widgets; ADR-0037). **Tier A: accept with fixes**, 1: misread 1.
  - **Checked.** Search § A2's octant bullet recomputed over the table doc's 25-line listing of `g_DirOctant` column 0
    (the listing `tools/test_path_survey.py` compares with the image): the stated cases (a term whose double is at most
    the other's size set to 0, the index of the signed step in Inputs' order, `(0, 0)` 6) give 25 of 25. The tag holds
    as ADR-0031 frames it: an equality on the image's elements, no claim on how the table was made, the table still
    listed under the owner's ruling (ADR-0031, What a rule excludes), so the spec states the description without
    turning the table into a rule. Anchors resolve (`0x00678D10`, `0x006F1518`, `0x005539B0` in `re/symbols.csv`;
    run:2026-11-03-path-emu-2 in path/experiments). The caption's "a target on the node itself gives direction 6" is
    true of `PathDirCell`: one branch of the cut runs, so `(0, 0)` comes only from `dx = dy = 0`. Timing K1: `steps(r)`
    equals E2's `N`; with a step it equals `n − 1`, with none (`n = 2`) it is 0; the `[C]` note carries E2's own
    evidence (104 emulated no-step schedules with an event, run:2026-11-16-sweep2-s6e) and claims no new run; L4's
    scope is right. Counts and the map rows match the gate. Captions against their spec sections: rows 23 to 30 are
    the reviewed drafts, the row 25 cut is the X9 sentence. **Rulings:** (1) row 31's `tables.step` and `tables.fan`
    are the eight steps (Inputs, Tables) and the fan's eight rows (§ L3's table), both on spec-path/search, neither on
    wiki/pathing; by the x16b ruling the block moves to the search spec page, at the end of § L3, after the fan table.
    The rows cannot become `toy`: they are the image's values and the widget's search needs them. The builder has no
    text fallback for `path` (`twins.fallback_table`), so the fallback stays the `path-search-toy-room` picture, built
    from wiki/pathing earlier in the cut and copied into the widget folder (no rule ties a fallback to its page).
    (2) wiki/animation's W4 on timing stays: it predates this lane (the spec was already 2026-11-17), and the page's
    two sentences on the subject (the no-step case "holds under emulation", line 99; "`N = n - 1`, the last step",
    line 209) agree with K1 as rewritten; the date moves at the next wiki refresh of that page, with movement's W4.
  - **Fix (misread).** (1) Row 31 moved from wiki/pathing to spec-path/search § L3 (`illustrates` made page-relative,
    `fallback` kept); its caption names the fan table above and the eight steps under Inputs, and refers to §§ A2, L2
    without "search"; the lane's log row 31 and the octant entry's resolution corrected.
  **Redaction review: pass; this cut's widgets may be published** (`tools/export_publish.py --push`, the owner's),
  with the one layout fix below already in `workspace/export-repo/`. Cut (lane head plus the fix): `export_build.py
  --out workspace/export-x16s-review`, 89 pages, 0 dropped, 10 widget folders (the 9 new and rng), picture fallbacks
  for rows 24, 25, 30, 31, text for 23, 26 to 29; no widget DROP (the first build with `fallback: text` on row 31
  dropped it, "no text fallback for the widget path"); the A2 bullet, the K1 note, `steps(r)` and all nine captions
  are in the cut; `export_check … --repo workspace/export-repo/` **0 failures, 1 084 warnings**, all X12 in the classes
  earlier reviews ruled on, none on a new caption or the new A2 and K1 text. Widget folders scanned: no paths, tool,
  `fn:`, `run:` or `sub_` tokens; the only hex values are `0x10000`, `0x100000`, `0x7FFF`; the four fallback pictures
  are first frames of reviewed schematics. **Real site build** in a scratch copy of the export checkout (the cut and
  `workspace/export-repo/` copied over, the Astro caches removed): `SITE_BASE=/arpg-1-14d-notes/ npm run build` 90
  pages; `check-site-links.mjs dist` 12 026 links in 115 pages, all resolve. **Chromium headless** (Playwright,
  served under the base): the eight pages that carry the ten widgets (characters/combat, running/animation,
  world/monsters, characters/characters, spec-items/quality, characters/saves, foundations/randomness,
  spec-path/search) in dark and light at 1280 px and dark at 375 px: the CSP meta (`connect-src 'none'`,
  `form-action 'none'`) on each, no console error or warning, no failed request, every image loads, every widget
  mounts and its output changes when its first input does (the checksum's text input driven by hand: rotate, then
  add, offsets 12 to 15 counted as 0); rng shows `015B2E77` for 12345; the path widget's default run gives passes 22,
  27 and 32 and the five corners of its fallback's caption. **One defect, fixed:** at 375 px characters/saves was 427
  px wide: the checksum widget's preset `<select>` sizes to its longest option.
  `workspace/export-repo/site/src/styles/site.css` now gives `.widget-host .widget-field` `min-width: 0; max-width: 100%` and `.widget-host input, select`
  `max-width: 100%` (three lines, prepared for the owner as ADR-0037 says); rebuilt, all 24 page loads are clean and
  no page is wider than its viewport; `export_check` unchanged. ADR-0037's owed browser run for batch 3 is done.
  **Manifest:** `docs/export/reviewed-pages.txt` unchanged (no new page). Scratch builds and copies deleted. Gate
  green. Ledger: verdict accept with fixes, 1 (misread 1).
- 2026-11-19 — **Phase 11 batch 3 served.** The owner pushed the export repository's `main` (cut commit 93f455a: the nine widgets of rows 23 to 31 and the narrow-screen style fix); the Pages run passed and the checksum widget's files are served.
