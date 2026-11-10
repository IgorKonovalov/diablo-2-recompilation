---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md
  - ../plans/0064-cleanroom/S1.md
resolution: ""
---

Two fixes to tools/cleanroom.py found by the S1 run (2026-11-10). (1) make writes score.sh with the absolute path of the checkout make ran in; when that lane worktree was removed, score.sh failed (the orchestrator repointed the four sandboxes by hand). Resolve the tool path from the main checkout or the sandbox MANIFEST, never a lane worktree. (2) audit flags words inside heredoc bodies and quoted text (S1 transcript: 6 false VIOLATIONs at lines 120 and 139, a Python source heredoc and the ledger heredoc; manual inspection found no read outside the sandbox). Skip heredoc bodies, or downgrade words not in a read position to a warning, and add a test. Also let audit allow the harness's own tool-results file for a Read of a persisted command output.
