# ADR-0037 — Scripted widgets in the public export: small scripts of our own, computing from the specs' rules and hand-written illustrative rows, checked like page text (amends 0035, 0036)

> **Status:** accepted (owner, 2026-11-17: "1 yes / 2 yes / 3 acceptable / 4 ok / 5 yes" to the candidate list and
> batch order, this ADR, the one-time change to the export repository's files, the `toy`/`page` rows capped at 20, and
> the gate rule that needs node; with [ADR-0038](0038-one-command-publish-of-the-export.md) the publish script copies
> the export repository's files, so the owner applies nothing by hand)
> **Date:** 2026-11-17
> **Related plan(s):** [0070-redacted-public-export](../plans/0070-redacted-public-export.md) (Phase 11)

## Context

On 2026-11-17 the owner asked for "as much animations and interactive elements as possible" on the public site
([ADR-0035](0035-public-export-hosting.md): an Astro Starlight site on GitHub Pages, built from the cut that
`tools/export_build.py` writes). Animations are already allowed: [ADR-0036](0036-schematic-illustrations-in-the-export.md)
lets marked schematic GIFs, frames and step-through pages leave the machine, and plan 0070 Phase 11 puts more of them
first. Interactive elements are not. Today the publish check (`tools/export_check.py`) fails raw HTML and every
`<script>` in the cut's Markdown (X7), allows non-Markdown files only in illustration folders (X11), and the export
repository ships no script of ours. The one script that does leave is the step-through page's inline script, the
generator's own template, which ADR-0036 admitted as a marked, listed exception that makes no request.

An interactive element is what a GIF can't be: the reader types a seed and sees its draws, moves a slider for
attack rating and sees the chance to hit, sets a rate and sees on which frame the action falls. Most of those rules are
already in the specs as pseudocode and formulas, and most of the computation is small integer arithmetic. The
repository has Python models of nearly every rule (`tools/rng.py`, `combat.py`, `anim.py`, `path.py`, `hirelings.py`,
`monstats.py` and the rest), checked against the game's own runs. A widget would be a second implementation of a rule
we have already written, in the reader's browser.

What a script adds to the export's exposure, against [ADR-0009](0009-public-documentation-site.md)'s five risks, is
mostly (1) and (3). (1): a page that computes the game's rules is more operational than prose; it must not become a
tool that reads, edits or forges game files, and it must not carry a tie to the binary or to the method. (3): data a
script reads sits in a machine-readable file, which is easier to lift whole than a table in prose; a widget's data
must be smaller and plainer than what the text may hold. A script can also make network requests, which the static
export has never done, and code is harder to check by pattern than prose.

The node runtime the docs gate already uses for Mermaid (E9, E17) can run a script's pure part, so a widget's output
can be compared with our Python model's on a fixture, as the illustration tools' step lists are compared today.

## Decision

**The export may carry scripted widgets: one small, self-contained, hand-written JavaScript module per widget, kept
and tested in this repository, computing only from rules a reviewed spec states and from at most 20 hand-written
illustrative rows, with a static fallback, served from its own folder and loaded by one generic host step in the
export repository.** Everything below is checked mechanically by the publish check or tested by the gate.

- **What a widget is.** A folder `tools/widgets/<name>/` (archivist-owned, under ADR-0005's tools rule) holding
  `widget.js`, `widget.json` and `fixture.json`. `widget.js` is one plain ES module: no `import`, no `export … from`,
  no dependency, no build step, not minified, at most 48 KB. It exports a pure `compute(inputs, data)` and a
  `mount(element, data)` that builds the controls with DOM calls only. A widget makes no claim of its own: as for
  illustrations ([ADR-0034](0034-local-documentation-site.md)), every label restates a tagged statement of a spec,
  every result is labelled as computed by our model, and a default seed is labelled `illustrative`. Where the widget
  and the spec disagree, the spec wins and the widget is a bug.
- **Where its code lives.** In this repository, not in the export repository. The builder copies a widget into the cut
  at `site/public/widgets/<id>/` with a list file (`widget.list.json`: the marker, each file's name and sha256), like
  an illustration folder. The export repository gets one generic host, once: a rehype step in `astro.config.mjs` that
  finds an image whose source is `/widgets/<id>/fallback.<ext>`, wraps it in a `<figure>` the widget mounts into, and
  adds `<script type="module" src="<base>/widgets/<id>/widget.js">`; the widget styles in `site/src/styles/site.css`;
  and a Content-Security-Policy `<meta>` in Starlight's `head` with `connect-src 'none'`, `frame-src 'none'`,
  `object-src 'none'` and `form-action 'none'`, so the browser itself refuses any request a widget might make. A lane
  prepares that change under `workspace/export-repo/`; the owner applies it. No widget code ever goes into the export
  repository's own files.
- **What it may read.** Only its `widget.json`: the inputs (name, range, default), the rule's parameters as the spec
  states them (a hex constant only as `docs/export/allow-hex.txt` admits it; a default seed only one of its
  illustrative seeds), and at most 20 rows per array, each array marked `"rows": "toy"` (invented for the widget) or
  `"rows": "page"` (rows the reviewed page around it already shows). The file is written by hand and reviewed; it is
  never generated from the user's game files, at cut time or any other time, and a widget never takes a game file as
  input: no file picker, no drop zone, no paste of a table. What the reader types is computed in the browser and goes
  nowhere: no storage, no cookie, no request.
- **How a page names it.** A fenced ```` ```widget ```` block in the wiki or spec page, with the keys of an
  illustration block (`id`, `widget`, `illustrates`, `caption`) plus `fallback`: an illustration id whose first frame
  or GIF the builder uses, or `text`, for which the builder writes the fixture's first case as a short Markdown table
  under the caption. Pages stay Markdown; the cut's Markdown holds only the fallback image, the caption and a
  "Try it" line, so X7's bar on raw HTML stays as it is. A block whose widget is missing or fails the check is
  dropped with a report line, as an illustration is.
- **What the check verifies** (a new rule, X13, on each `site/public/widgets/<id>/` folder; X11's allowlist gains the
  folder):
  - only `widget.js`, `widget.json`, `widget.list.json` and one `fallback.png` or `fallback.gif`; each carries the
    marker; each sha256 matches the list; `widget.js` and `widget.json` are byte-equal to the reviewed source in
    `tools/widgets/<name>/`; the fallback image passes ADR-0036's schematic rules; size caps of 48 KB (script) and
    16 KB (data);
  - `widget.js` holds none of: `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `sendBeacon`, `importScripts`,
    `Worker`, `import` in any form, `require(`, `eval`, `Function(`, a string passed to `setTimeout` or `setInterval`,
    `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `document.cookie`, `localStorage`,
    `sessionStorage`, `indexedDB`, `navigator.`, `location`, `window.open`, `postMessage`, `FileReader`, `type="file"`,
    any URL or `//host` shape, a `src` or `href` assignment;
  - every string literal and comment of `widget.js`, and every string of `widget.json`, passes the text rules X1 to
    X4 and X9, and the decompiler artefact names of X5 (`param_N`, `local_XX`, `FUN_`, `DAT_`) fail anywhere in the
    script; `widget.json` is valid JSON, every array has 20 entries or fewer and carries its `rows` key;
  - in the export repository's files, the host step loads nothing but `/widgets/<id>/widget.js`, and the CSP `<meta>`
    is present word for word.
- **Determinism.** Each widget names its Python twin: a function of an existing model in `tools/`, or a short
  reference function beside the widget's fixture writer. `fixture.json` holds inputs and the outputs the twin computes
  for them (seeds, edge values, the spec's worked example where there is one). A new gate rule, E21, runs
  `tools/test_widgets.py`: it loads each `widget.js` under node, calls `compute` on every fixture case, and fails on
  any difference; it is skipped with one warning where node is missing, as E9 is. Integer widths and rounding follow
  the spec (32-bit products by `Math.imul` or `BigInt`, not floating point); the fixture includes the cases where
  they differ.
- **Accessibility and no script.** Without JavaScript, or before it loads, the reader sees the fallback image (its alt
  text the block's caption) and the caption. With it: native form controls, each labelled; everything reachable by
  keyboard; results announced in an `aria-live="polite"` region; no motion without a play control, and none under
  `prefers-reduced-motion`.
- **Theming.** Colours come from Starlight's CSS custom properties (`--sl-color-text`, `--sl-color-bg`,
  `--sl-color-accent` and their kin), so a widget follows the light and dark themes; the schematic palette of
  ADR-0036 (quality colours and the like) is defined once in `site.css`, with a light and a dark value each. A widget
  sets no colour of its own.
- **What stays out.** Game sprites, tiles, icons, palettes, fonts and any styling that imitates the game's interface
  (ADR-0009 risk 4, ADR-0036); data dumps and any table generated from game files; any widget that reads, writes,
  edits or validates a game file or a save (a save's checksum may be shown on hand-typed toy bytes only); code-shaped
  excerpts of the binary; third-party libraries, fonts, analytics or calculators, and their data; anything about copy
  protection, CD keys, Battle.net or Warden.
- **Review.** The lane that adds X13 and E21 to the check and the gate is a safety device and takes Tier A, as plan
  0070 Phase 2 did. Each widget batch takes a Tier A review on Opus (owner's order for plan 0070): the reviewer reads
  every `widget.js` whole, every `widget.json`, and the fixture's twin. The redaction review of the cut that first
  carries widgets opens each one, with and without JavaScript, in both themes.

## Consequences

### Positive
- The reader can try a rule on their own inputs, which is what the owner asked for, and what a GIF can't give.
- Each widget is tested against the model that is tested against the game, so it shows what the spec says.
- The code is ours and in git: reviewed, gated, and the same bytes in the cut. The export repository changes once.
- Without JavaScript the page loses nothing it has today: the fallback is an ADR-0036 picture or a short table.

### Negative
- **Executable code leaves the machine for the first time beyond a fixed template.** A pattern check over JavaScript
  can be evaded by a determined author (string building, aliasing). Three things narrow this: the code is short,
  unminified and read whole at Tier A; the CSP refuses requests in the browser whatever the code does; and nothing in
  the cut lets a widget reach a game file.
- **The site becomes more operational.** A to-hit or breakpoint calculator is a tool, not prose. ADR-0009 risk (1) is
  about the method and the binary, and a widget carries neither, but it does make the export easier to use without
  reading the spec. The no-file-input rule keeps it from being a game utility.
- **Machine-readable rows are easier to lift.** The 20-row cap, the `toy` or `page` marking and the ban on generated
  data keep the JSON smaller than the prose may be; a toy row also teaches less than a real one.
- **A second implementation of each rule, in another language.** Drift outside the fixture's inputs is not caught.
  The fixture takes the spec's edge cases; a widget whose twin changes is re-run by E21 on the next gate.
- **More moving parts.** Node becomes needed for a gate rule (skipped without it); the check grows a rule with many
  words; the export repository needs a host change the owner applies by hand; Starlight's own inline scripts mean the
  CSP can restrict connections and frames but not scripts.
- **More review.** Every widget batch is an Opus Tier A review, and widgets cost more than GIFs per page.

### Neutral
- ADR-0036 is unchanged for illustrations; this ADR adds a second kind of folder beside them. Its step-through
  page's inline script stays the template it admitted.
- ADR-0034's local site may host the same widgets; that is the builder's plan's choice.
- No new rule for the specs: a widget restates them, as an illustration does.

## Alternatives considered

### No scripts: GIFs, frames and static schematic pictures only
The safest, and it needs no new rule (plan 0070 Phase 11 does it first). It lost because the owner asked for
interactive elements, and a picture can't take the reader's input.

### MDX pages with components
Starlight supports it, and widgets would sit inline in the text. It lost because the cut's pages would hold code: every
page would need a JSX-aware check, and X7's simple bar on raw HTML in the cut would no longer hold.

### Each widget in a sandboxed iframe page
The strongest isolation (`sandbox="allow-scripts"` without the same origin), and the step-through page already has the
shape. It lost on use: an iframe can't follow the site's theme or size to its content without messages across the
frame, it is harder to reach by keyboard and screen reader, and X7 bars `<iframe>` for good reasons. The CSP gives the
guarantee that matters (no request) without it. It stays the fallback if a review finds a widget needs isolation.

### Widgets as Astro components in the export repository
The idiomatic Astro way. It lost because the code would live outside this repository's gate and parity tests, every
change would be an owner's hand-applied edit, and the check's list of export-repository files would grow per widget.

### A separate calculator site or repository
It would keep the docs site static. It lost because it splits the reader's place, needs a second check and host, and
a stand-alone calculator drifts from the specs it should restate.
