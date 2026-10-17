---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-17] from architect → reverser: plan 0038 S1f review follow-ups (tools, not blocking). (a) `tools/ghidra.sh` writes every non-build command's log to the fixed `workspace/logs/ghidra-last.log`; `workspace/` is shared by all worktrees, so two lanes running Ghidra at once truncate and read each other's log (`check_log` can fail a run on the other lane's error, and `import-symbols`/`export-symbols`/`decompile-range` grep it for their result). Take the log path from an env variable (`GHIDRA_LOG`), defaulting to a name derived from `GHIDRA_PROJ_DIR` (e.g. `ghidra-last-<basename of the project dir>.log`, so the default project keeps `ghidra-last.log`), make the three greps read that path, and replace the workaround paragraph in [tooling.md § emutrace](../../.claude/skills/reverser/references/tooling.md) with the variable. (b) tooling.md § emutrace, *Memory spec*: write a scratch structure the code reads through an image pointer (DataTables and the like) one field per field the claim reads, not as a whole page, so a read of any other field is traced (S1f review, ruling 4); whole-page specs of earlier records stand. Context: [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log) (S1f review, rulings 4 and 5)
