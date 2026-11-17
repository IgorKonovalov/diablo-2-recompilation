---
from: spec-writer
to: archivist
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
  - ../../adrs/0037-scripted-widgets-in-the-export.md
resolution: "tools/site_build.py renders a widget block as its fallback (the named illustration's GIF, or the twin's text table for fallback: text) with its caption and a note that the interactive element is on the published site, no script; E19 (site_build.py check) parses widget blocks: keys by the export builder's parse_widget, unique widget id, the widget folder under tools/widgets/, a fallback that is text or an illustration id under docs/, illustrates links resolve; tested in tools/test_site_build.py [tools/site_build.py](../../../tools/site_build.py)"
---

Found while placing the first ```` ```widget ```` block (`rng-stepper`, wiki/randomness § A worked example; plan 0070 Phase 11,
lane/x11s). The local site builder (`tools/site_build.py`, ADR-0034) has no case for a `widget` fence: `fenced()` renders
it as a plain code block (`<pre><code class="lang-widget">`), so the local page shows the block's keys and caption as
source. Nothing breaks (the build and the gate are green), but the local reader sees raw YAML-like text where the cut
shows the fallback picture and the caption. Asked: render a widget block in the local site as its fallback (the named
illustration's first frame, or the twin's text table for `fallback: text`) with its caption, or at least as a short
note like the `--no-illustrations` one; and let E19 (or E21) parse the widget blocks under docs/ the way it parses
illustration blocks. Not blocking: the export is right.
