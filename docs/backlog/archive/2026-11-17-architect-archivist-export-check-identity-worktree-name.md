---
from: architect
to: archivist
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "git_identity() now derives the repository name from the remote URLs and the main checkout folder (git common dir), never the current worktree folder; tests in tools/test_export_check.py"
---

Plan 0070, found at the review of lane/x14a (2026-11-17): export_check's X4 identity rule (git_identity) takes the checkout folder's name as an identity string, so a build in a worktree whose folder name is a common word drops every unit holding that word (a worktree named 'base' dropped 750 units, the items/properties page among them). The main checkout and the lane worktrees (recompilcation-project-<tag>) are safe today, but the rule is fragile. Asked: derive the identity strings from the repository's own name and the owner's identity only (not the worktree folder), or ignore folder names that are ordinary words; tests both ways; X4 must still fail the working repository's name and the owner's paths. Tier B check.
