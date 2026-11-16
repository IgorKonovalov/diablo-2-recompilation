---
from: architect
to: archivist
date: 2026-11-16
status: done
context:
  - ../../adrs/0034-local-documentation-site.md
resolution: "tools/site_build.py (build, check), tools/site_mermaid.mjs and the --out interface of maze_anim.py and tc_anim.py landed on lane/site1. The gate rule is not registered: the architect adds 'python3 -I tools/site_build.py check' (last line 'CHECK illustrations: N blocks, M problems', exit 1 on a problem) as a gate rule at review. item_art.py has no animation interface (it is a library for icons); the TC-drop pilot is tc_anim.py."
---

ADR-0034 (proposed): write tools/site_build.py (stdlib only, python3 -I) that builds a local site into workspace/site/ from docs/wiki, docs/specs and the glossary (plus other docs/ Markdown if needed for links), draws Mermaid at build time or from the local bundle E9/E17 use, makes no network request, refuses output outside workspace/, and adds the 'built locally from your own game files, not to be shared' footer. Replace each ```illustration block by running its tool on the data root with its args and --out workspace/site/illustrations/<id>/. Give maze_anim.py, item_art.py and the TC-drop pilot that interface. Add a gate check: each illustration block parses (id, tool, args, seed, illustrates, caption), ids are unique across docs/, tool names a script in tools/, illustrates links resolve; the architect registers it as a gate rule at review. Generator caption/calculation text changes take Tier A (ADR-0034, amends 0030).
