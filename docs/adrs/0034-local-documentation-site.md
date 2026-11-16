# ADR-0034 — A local-only documentation site, built by the user from their own game files and our scripts, with animated illustrations (amends 0012, 0030)

> **Status:** accepted (owner, 2026-11-16; decision: "site can be a full local only publish that user can build out of game files + our scripts")
> **Date:** 2026-11-16
> **Related plan(s):** none yet; the follow-up work is in the backlog entries listed under *Implementation*

## Context

[ADR-0012](0012-human-wiki.md) made the human wiki Markdown in `docs/wiki/` and ruled that "it is not published. It
is no site, no Artifact and no export." It rejected "a rendered site kept local" for two reasons: a static site
generator adds a toolchain, and a rendered form makes pages harder to review in diffs. It added that
[ADR-0009](0009-public-documentation-site.md) makes any rendered form a publication question.

Two things have changed. First, the maze animation pilot (`tools/maze_anim.py`, merged at e14ccf02) showed what a
picture adds to a generator spec. From the game's own tiles it writes one frame per step, a GIF and a local
step-through page. Each step has a "Calculations for this step" panel (draw values, the picked room and side,
overlaps, merge rolls, the Def from the exits) and a "How to read this" box. The owner accepted that format. A second
pilot, a treasure-class drop shown with inventory icons, has started. These outputs are game art. Under
[ADR-0005](0005-presentation-formats-tools-only.md) and `CLAUDE.md` they stay in `workspace/render/` and never enter
git. So the Markdown in git cannot show them, and a page that wants to show them needs a rendered form.

Second, the owner decided on 2026-11-16 that "site can be a full local only publish that user can build out of game
files + our scripts". The site is something a user builds on their own machine, from their own copy of the game and
our scripts. It is not something we host. ADR-0009's risks are about content leaving the machine. A build that stays
on the machine of the person who owns the game files is not a publication.

[ADR-0031](0031-constants-of-the-code-image.md) bounds which constants of the code image may appear in git. An
illustration's calculations can show table values and constants. When they are computed at build time from the
user's own files, none of them enters git.

## Decision

**The repository stays Markdown.** `docs/specs/` and `docs/wiki/` remain the source. Diffs, the gate and review work
on them exactly as now. Nothing rendered enters git.

**A builder script builds a local site.** `tools/site_build.py` uses the standard library only and runs with
`python3 -I`. It writes the site into `workspace/site/`, which is gitignored with the rest of `workspace/`. It builds
from two inputs: (a) the repository's Markdown, and (b) illustrations it generates by running our tools
(`maze_anim.py`, the DS1/DT1 renderers, `item_art.py`, later pilots) on the user's own, legally owned game files.
The user opens the result from disk.

- **What a build may contain.** The wiki and spec pages, the glossary, and their Mermaid diagrams. It may also render
  other `docs/` Markdown so that the specs' links to findings, tables and ADRs resolve; that choice is the builder's
  plan's. It may contain the generated illustrations: frames, GIFs and step-through pages.
- **What it may not do.** It is never committed, never an Artifact, never a hosted page, and never pushed or uploaded
  anywhere. A built page makes no network request: no CDN, no web fonts, no analytics. Mermaid is drawn at build time
  or by a local copy of the bundle the gate already uses (E9, E17). The builder refuses an output path outside
  `workspace/`. Every built page carries a footer saying the site was built locally from the reader's own game files
  and is not to be shared. Sharing it would hand on game art, which ADR-0009 keeps out of any export.
- **"Publish" means a local build.** It is not ADR-0009's publication. ADR-0009's later redacted export is unchanged,
  and it carries no illustrations.

**Animated illustrations follow the Mermaid rule.** They illustrate. They make no claim of their own, as the spec-writer's
pseudocode conventions say of diagrams (§ Diagrams).

- Every caption, "How to read this" line and calculation line restates a tagged statement of a spec or finding, or
  shows a value computed by the replay model that implements that statement (for the maze, `tools/maze_replay.py`
  reading [drlg/0006](../findings/drlg/0006-maze.md)). Where the illustration and the spec disagree, the spec wins and
  the illustration is a bug.
- A value computed by our model is labelled as computed by our model. It is never presented as observed from the game.
- A seed is labelled `illustrative` unless a recorded run or finding names it, and then it cites that record.
- Each generator's docstring names the spec sections it illustrates and the model it runs.
- **Owners.** The archivist lane owns the generators and the builder, in `tools/`, as for every tool under ADR-0005.
  The spec-writer lane owns the pages that place an illustration: the wiki pages under ADR-0012, and the specs.
- **Review.** A lane that writes or changes a generator's caption, "How to read this" or calculation text writes
  explanatory statements over specs. It takes Tier A like a wiki lane that writes statements
  ([ADR-0030](0030-verdict-lanes-and-wiki-tier-a.md)). A lane that changes only drawing code keeps its usual tier.

**A page names an illustration with a fenced block, never with a link to a file.** A relative link to a file that
exists only after a local build would fail the gate's E8 in every checkout. So a page writes a fenced block with the
info string `illustration`, in this form:

````markdown
```illustration
id: drlg-maze-level8
tool: maze_anim.py
args: 8 0x2A
seed: illustrative
illustrates: ../specs/drlg/maze.md#c-random-growth
caption: The maze grows one room at a time; each step shows the draws that picked the room and its side.
```
````

- `id` is unique across `docs/` and is the stable name of the built illustration. The builder writes it to
  `workspace/site/illustrations/<id>/`.
- `tool` names a script in `tools/`. `args` are its arguments after the data root, which the builder supplies. They
  hold only a level id, a seed, a table row name or similar, never game data.
- `seed` is `illustrative`, or the record that names it.
- `illustrates` lists the spec sections it shows, as relative links.
- `caption` is in git and reviewed with the page. It restates the spec section it names.

On GitHub or in an editor the block reads as a short note naming the illustration and how to build it. The builder
replaces it with the illustration. A page stays valid Markdown, and passes the gate, without the file.

## Consequences

### Positive
- A reader who owns the game gets the pictures where they help most: a maze growing room by room, a drop resolving
  from its treasure class.
- Nothing about the evidence trail changes. Illustrations add no claims, and the Markdown stays the reviewed text.
- No game art and no table dump enters git. Each user builds the art from their own copy.
- Diff review is unchanged. The illustration block is a few reviewable lines.

### Negative
- **A second renderer to keep in step.** A generator's text can drift from the spec it illustrates, as the wiki can.
  The Tier A rule catches a wrong paraphrase in review, but nothing checks it mechanically.
- **Model, not game.** The calculations come from our replay models. A model that is wrong produces a convincing
  wrong picture. The labelling rule says where the numbers come from, but a reader may still take a picture as proof.
- **The builder costs archivist time** and adds a toolchain, which ADR-0012 wanted to avoid. Stdlib only and the
  existing renderers keep that cost small, but it is not zero.
- **We cannot stop a user from sharing a build.** The footer and this ADR state the rule. Enforcement ends at the
  user's machine.
- Readers without the game see only the block's note on GitHub. The Markdown must still explain the step without the
  picture.

### Neutral
- **This amends [ADR-0012](0012-human-wiki.md) on two points, for local builds only.** Its *Decision* bullet "It is
  not published. It is no site, no Artifact and no export" now allows a site built locally into `workspace/site/` by
  `tools/site_build.py`. "No Artifact and no export" stands. Its rejected alternative "A rendered site kept local"
  is taken up in this narrower form: no third-party generator, the Markdown remains the source, and a local build is
  not a publication.
- **This amends [ADR-0030](0030-verdict-lanes-and-wiki-tier-a.md) on one point.** A lane that writes a generator's
  explanatory text takes Tier A, as a wiki lane does.
- [ADR-0005](0005-presentation-formats-tools-only.md) is unchanged. Rendered output stays under `workspace/`, and the
  docs still do not embed images: an illustration block names an image and holds none. Its "animation playback stays
  out of scope" is about sprite animation (`animdata.d2`, COF timing), not about step-by-step pictures of a generator.
- [ADR-0009](0009-public-documentation-site.md) is unchanged. Its export, if it is ever cut, carries no illustrations.
- [ADR-0031](0031-constants-of-the-code-image.md) is unchanged. Values an illustration shows are computed at build
  time from the user's files and stay in `workspace/`.
- `CLAUDE.md`'s non-negotiables need no edit: `workspace/` is already ignored, and the hooks already keep it out of
  commits.

## Alternatives considered

**A hosted site** (GitHub Pages or similar). It would reach readers who do not own the game. It lost because hosting
is ADR-0009's publication, which the owner deferred to a redacted export with no tie to the repository, and because a
hosted site with the illustrations would distribute game art.

**Commit the GIFs and frames and embed them in the Markdown.** Pages would show the pictures on GitHub with no build
step. It lost because the frames are drawn from the game's tiles and icons. That is game data, which never enters git.

**A third-party static site generator** (MkDocs, Hugo and similar). Mature and well themed. It lost because it adds a
dependency and its plugin code runs over the docs, against the stdlib-only habit of `tools/` (ADR-0005), and because
the illustration step needs our own scripts anyway.

**Keep illustrations as loose files in `workspace/render/`** with no site, as the pilot left them. No new tool. It
lost because the pictures would stay separate from the text they explain, and the owner asked for a site.

## Implementation

Follow-up work, filed as backlog entries (ADR-0018). This ADR builds nothing.

- archivist: `tools/site_build.py`, the illustration interface for the generators (data root, `args`, `--out` under
  `workspace/`), and a gate check that each `illustration` block parses, has a unique `id`, names a script in
  `tools/`, and has links in `illustrates` that resolve. The architect registers that check as a gate rule at
  review. ([entry](../backlog/archive/2026-11-16-architect-archivist-adr-0034-local-site-builder.md))
- spec-writer: an *Illustrations* section in the pseudocode conventions restating the rules above, then the first
  `illustration` blocks: the maze in the levels wiki page, the treasure-class drop in the items wiki page once its
  pilot merges. ([entry](../backlog/archive/2026-11-16-architect-spec-writer-adr-0034-illustration-blocks.md))

Implementation note (`lane/site1` review, 2026-11-16): `tools/site_build.py` and `tools/site_mermaid.mjs` landed, and
the block check is registered as gate rule **E19** (`python3 -I tools/site_build.py check`, run by `tools/gate.py`;
the rule is written in `.claude/skills/architect/references/evidence-rules.md` § Mechanical checks).
