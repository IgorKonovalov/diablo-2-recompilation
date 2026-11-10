---
from: architect
to: archivist
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md
resolution: ""
---

Found while starting plan 0064 Phase 5 (2026-11-10). (1) 'make SLICE --force' keeps the previous implementer's code and candidates (and the score log) in the sandbox, so a Phase 5 re-run there could read the Phase 2 implementation; the orchestrator built fresh sandboxes with --out (S1r, S2r, S3r). Add a re-run mode (or make --force refuse when non-sandbox files exist, unless --keep-code), and say in the brief that a re-run needs a fresh directory. (2) 'make --out DIR' writes a score.sh without --out, so its runs log into workspace/cleanroom/SLICE, not DIR; the orchestrator patched the three score.sh by hand. Write --out into score.sh when the sandbox is not the default path, and add a test.
