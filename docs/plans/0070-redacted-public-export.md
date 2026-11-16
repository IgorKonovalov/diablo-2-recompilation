# 0070 — The redacted public export: what leaves the machine, how it is redacted, and the check that guards it (ADR-0009, ADR-0035)

> **Status:** in progress: Phase 1 done 2026-11-16; approved (owner, 2026-11-16: "1 b / 2 keep / 3 github pages, similar to @../Ritmolux/ documentation /
> 4 yes / 5 go as recommended"; the account: "My account, like Ritmolux"; hosting recorded in ADR-0035)
> **Created:** 2026-11-16
> **Owner skill(s):** architect, archivist, spec-writer, human
> **Related ADRs:** 0009-public-documentation-site, 0035-public-export-hosting, 0034-local-documentation-site, 0012-human-wiki, 0031-constants-of-the-code-image, 0005-presentation-formats-tools-only, 0006-docs-gate

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

## The design (approved 2026-11-16)

### Scope: an allowlist, not a denylist

The export holds only the pages an allowlist names, `docs/export/manifest.txt` (one docs-relative path per line;
architect-owned). A page reaches the export only by being named. Three scopes were offered (question 1); the owner chose (b):

| Scope | Holds | Notes |
|---|---|---|
| (a) | `docs/wiki/` (except `how-we-know.md`), `docs/glossary.md`, the export-only pages | Smallest. The wiki is already free of tags, anchors and addresses. The wiki's links into specs become plain text. |
| (b) **chosen** | (a), then the reviewed specs under `docs/specs/<subsystem>/` | The deliverable itself. It needs the redactor and Phase 8's residue fix. Cut (a) first; add (b) as a second cut once its check is green. |
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
| (1) | Method words: Ghidra, decompile, disassembly, gdb, breakpoint, harness, emulation, logger, "logged run" | **Removed from the export text.** The check fails on them. Phase 8 moves any left in spec prose into the evidence parenthetical, where the evidence rules put them anyway. | The export describes the game, not how we read it. It still shows that someone studied the game closely; that can't be redacted away (*Risks*). |
| (1) | Copy protection, CD key, Battle.net authentication, Warden | **Never present.** The check fails on any mention, the one-line "out of scope" notes included. | ADR-0009's standing ban, made mechanical for the export. |
| (2) code-shaped excerpts | Our pseudocode | **Kept**, inside a line the check enforces (below). | It is our own notation, language-neutral, numbered steps and our names. It describes a method, which copyright does not cover. |
| (2) | Anything decompiler-like | **Never present.** Findings are out; the check also scans specs' blocks. | ADR-0009 risk 2. |
| (2) | Mermaid diagrams | **Kept** as fences, drawn at build time by the export repository's CI (ADR-0035). The check scans their text like any other. | They are ours and illustrate only. |
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
  sidebar groups follow it. It never runs an illustration tool and drops every ```` ```illustration ```` block. It
  keeps ```` ```mermaid ```` fences as they are; CI draws them. It also writes a residue report,
  `workspace/export/report.txt`, outside `site/`.
- **Redactor.** A pass over each page's Markdown, in this order: drop *Open questions* sections; drop evidence
  parentheticals made only of anchors, run ids, addresses and finding links; drop anchor-only table columns; strip the
  address column from pseudocode lines, keeping the tag; strip `sub_XXXXXXXX_` prefixes. It never rewrites a sentence.
  What it can't clean it leaves, and the check reports it.
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
  | X2 | an anchor `fn:`, `data:`, `struct:`, `tbl:`, `src:`, `run:` |
  | X3 | a repository reference: `findings/`, a finding id shape (`items/0002`), `ADR-NNNN`, `plan NNNN`, `lane/`, `docs/`, `re/`, `tools/`, `workspace/`, a `.py` or `.csv` name, a commit hash |
  | X4 | an identity string: the working repository's name and remote URL (read from git at run time, never stored), the git `user.email` of the machine, `/home/` or any absolute path. The owner's name and account pass (ADR-0035). |
  | X5 | a decompiler-like fenced block (the pseudocode line above); ```` ```mermaid ```` fences are exempt from X5 only |
  | X6 | a table over 20 body rows that the manifest does not name |
  | X7 | in the cut: any `http:` or `https:` link, raw HTML (`<script>`, `<iframe>`, `<link>`, `<style>`), `@import`, `url(`. In the repository files: a URL outside the allowlist (the owner's `github.io` host, the export repository, the licence's page, the npm registry in the lockfile), an action outside `actions/*` |
  | X8 | any image: a Markdown image, `<img>`, an image file of any type, `<video>` |
  | X9 | the banned topics (copy protection, CD key, Battle.net authentication, Warden) and the method words |
  | X10 | a footer component that differs from the footer word for word, or is not registered in the config; a `cut.json` without a date |
  | X11 | in the cut, a file other than `.md` and `cut.json`; in the repository files, a path outside the table above (plus the lockfile); a `.git` directory anywhere |
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

The first cut (wiki, glossary, export-only pages) is Phases 1 to 7. The second cut (the specs) is Phases 8 to 10.
After Phase 1, Phases 2, 4 and 5 can run side by side; Phase 3 needs 1 and 2.

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
  tree; the gate is green.

### Phase 2 — The publish check
- **Owner skill:** archivist
- **What:** `tools/export_check.py` with rules X1 to X12, its self-tests and gate rule E20.
- **Outputs:** `tools/export_check.py`, `tools/test_export_check.py`, `tools/gate/fixtures/export/`, `tools/gate.py`
  (E20 only).
- **Done when:** each rule fails its own bad fixture and passes the clean one; E20 is green; the check run on an
  unredacted copy of three specs fails on X1, X2 and X3 as expected. Tier A review.

### Phase 3 — The builder, the redactor and the residue report
- **Owner skill:** archivist
- **What:** `tools/export_build.py` as above. Run it on the first-cut manifest, then the check on its output. Run it
  once more on a trial manifest that adds every reviewed spec, for the residue counts only.
- **Outputs:** `tools/export_build.py` and its tests; `workspace/export/` (never in git); the residue counts per rule
  and per page for the trial, written into this plan's log.
- **Done when:** the build refuses a path outside `workspace/export/`, runs no illustration tool, and makes no
  network request; every page has a `title` and a `sidebar.order`; the check is green on the first cut, apart from
  the export-only pages if Phase 5 has not landed; the log holds the trial's residue counts. Tier B check.

### Phase 4 — The export repository's files
- **Owner skill:** archivist
- **What:** write the files of the table above under `workspace/export-repo/`, modelled on the owner's other site
  (read it, never change it). Exact version pins. No `npm` run on this machine: the lane writes files only.
- **Outputs:** `workspace/export-repo/` (never in git); the file list and the pinned versions in this plan's log.
- **Done when:** `tools/export_check.py --repo workspace/export-repo/` is green; the workflow has the two jobs, the
  build on pull requests, the deploy from `main` only, and `cancel-in-progress: false`; the footer component matches
  the footer word for word. Tier B check; Phase 6 reads every file.

### Phase 5 — The export-only pages
- **Owner skill:** spec-writer
- **What:** write the front page, "How to read the tags" and the about page in `docs/export/`.
- **Outputs:** `docs/export/*.md`.
- **Done when:** the gate is green; the check is green on a cut that holds them; Tier A review accepts.

### Phase 6 — The first cut's redaction review
- **Owner skill:** architect
- **What:** the Tier A redaction review above, on a fresh first cut and on `workspace/export-repo/`.
- **Done when:** a verdict is recorded in this plan's log with the cut date, the check's output and the sample read.

### Phase 7 — The owner's read and the first publish
- **Owner skill:** human
- **What:** the owner reads the cut, creates the export repository under their account, sets Pages' source to GitHub
  Actions, copies `workspace/export-repo/` and `workspace/export/site/` into a fresh folder, runs `npm install` once
  to make the lockfile, and pushes through a pull request. The CI build and link check must pass on it; the merge to
  `main` deploys.
- **Done when:** the owner says the site is served. No agent takes part beyond answering questions.

### Phase 8 — The spec residue
- **Owner skill:** spec-writer
- **What:** fix the residue at its source: move evidence that sits in spec prose into the evidence parenthetical, so
  the redactor removes it. No statement changes its meaning or its tag. Batches by subsystem, about 300 residue lines
  each; the count follows Phase 3's trial. Add the habit to the spec-writer's pseudocode conventions: prose states
  behaviour, evidence goes in the parenthetical.
- **Outputs:** edits to `docs/specs/`; `.claude/skills/spec-writer/references/pseudocode-conventions.md`.
- **Done when:** the check is green on a trial cut with the specs; the gate is green; each batch's Tier A review
  accepts.

### Phase 9 — The second cut's redaction review
- **Owner skill:** architect
- **What:** add the reviewed specs to the manifest, cut afresh, and run the Tier A redaction review above. A spec that
  can't shed its evidence without rewording stays out of the manifest.
- **Done when:** the manifest holds the specs; a verdict is recorded in this plan's log with the cut date, the check's
  output and the sample read.

### Phase 10 — The owner's read and the second publish
- **Owner skill:** human
- **What:** the owner reads the second cut, copies `workspace/export/site/src/` over the export repository's, and
  pushes through a pull request; the merge deploys.
- **Done when:** the owner says so.

## Cost estimate

From the ledger's means (`python3 -I tools/metrics.py summary`, 782 runs): archivist 167 k tokens a run,
spec-writer 244 k, architect review 163 k, architect check 87 k, architect 146 k. Recomputed 2026-11-16 for the
approved scope and the export repository's files (Phase 4, new).

| Phase | Lanes | Estimate |
|---|---|---|
| 1 manifest | architect | 0.15 M |
| 2 check | archivist, Tier A review | 0.25 M + 0.17 M |
| 3 builder | archivist, Tier B check | 0.30 M + 0.09 M |
| 4 export repository's files | archivist, Tier B check | 0.25 M + 0.09 M |
| 5 export-only pages | spec-writer, Tier A | 0.25 M + 0.17 M |
| 6 first review | architect, Tier A | 0.25 M |
| **First cut** | 9 runs | **about 2.0 M** |
| 8 spec residue | spec-writer, 4 to 8 batches, Tier A each | 1.0 M to 2.0 M + 0.65 M to 1.3 M |
| 9 second review | architect, Tier A | 0.25 M |
| **Second cut** | 9 to 17 runs | **about 1.9 M to 3.6 M** |
| **Total** | 18 to 26 runs | **about 3.9 M to 5.6 M** |

No harness slot and no Ghidra. The first cut adds about 0.4 M to the draft's scope (a) figure, for the export
repository's files and their check.

**Maintenance.** A re-cut is two commands (build, check), the owner's copy and a pull request. It costs no lane while
the check stays green. The Phase 8 convention keeps it green: a spec lane that writes evidence into prose turns the
next cut red. A red cut costs one small spec-writer fix (0.1 M to 0.25 M) and a Tier B check (0.09 M). Each cut the
owner publishes takes a review of what changed since the last published cut (about 0.15 M) and the owner's read.
Cadence: a cut on the owner's request, not on every merge (owner, 2026-11-16). Upgrading the export repository's npm
pins is the owner's work there.

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
- **A redactor that drops too much.** Dropping a parenthetical whose prose mattered would lose meaning silently. The
  redactor drops only parentheticals made entirely of evidence tokens, and Phase 9 reads the most-redacted page.
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

- Whether a spec's sentence can always shed its evidence without rewording. Phase 3's trial residue report answers it;
  a spec that can't is left out of the manifest, not rewritten for the export.
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
