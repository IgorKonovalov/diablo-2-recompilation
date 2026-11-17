---
from: architect
to: archivist
date: 2026-11-17
status: open
context:
  - ../plans/0070-redacted-public-export.md
  - ../export/manifest.txt
resolution: ""
---

Review of lane/x13b (plan 0070, 2026-11-17). Two export tool gaps found in the cut. (1) tools/export_build.py: a table cell whose content is a chain of `fn:sub_XXXXXXXX_Name@0x…` anchors (the *Entry points* tables' Function column above all) renders as `—` or as bare arrows (`→ →`), because a `sub_` anchor is removed whole (the docstring near RE_SUB) while a `fn:NAME@` anchor is rewritten to its name. 179 rows across the published spec pages read this way (e.g. drlg/collision's nine entry rows, objects/README's six, player/creation's eleven; rng/seeds' were fixed in the source at the review by writing the names before a parenthetical of anchors). Asked: rewrite `fn:sub_XXXXXXXX_Name@0x…` to `Name` (backticked) wherever `Name` itself passes X1–X5, as the specs' own prose does since lane/x13a (the re/symbols.csv name without its sub_ prefix); tests both ways (a named sub_ anchor kept as its name, a name holding hex still removed). (2) tools/export_check.py X2: the run-id rule matches `run:` case-sensitively, so a sentence-initial `Run:2026-…` passes the check and reaches the cut (items/inventory K1 on main; drlg/room-tiles fixed at the review). Asked: make it case-insensitive, with a test.
