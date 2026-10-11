# Formats

One file per container or binary format (`mpq.md`, `installer.md`, `excel-bin.md`, `ds1.md`, `dt1.md`,
`palette.md`, `dc6.md`, `dcc.md`, `d2s.md`). Owned by `archivist`. Each file covers layout tables with offsets and
sizes, endianness, the confidence of every field, and which `tools/` parser implements it.

| format | doc | parser | status |
|---|---|---|---|
| MPQ archives | [mpq.md](mpq.md) | `tools/mpq_dump.py`, `mpq_verify.py` | done |
| installer | [installer.md](installer.md) | — | done |
| excel `.bin` | [excel-bin.md](excel-bin.md) | `tools/excel_bin.py` | done |
| string tables | [tbl.md](tbl.md) | `tools/tbl.py` | keys only; values in plan 0005 Phase 3 |
| DS1 preset maps | [ds1.md](ds1.md) | `tools/ds1.py` | plan 0005 Phase 1, reviewed |
| DT1 tiles | [dt1.md](dt1.md) | `tools/dt1.py` | plan 0005 Phase 2, reviewed |
| D2S saves | [d2s.md](d2s.md) | `tools/d2s.py` | plan 0005 Phase 4 |


## Docs gate

`python3 -I tools/gate.py --full` reruns every survey registered in `SURVEYS` in `tools/gate.py`
(`ds1`, `dt1`, `d2s`, `excel` today) against `workspace/`. It compares each survey's last line,
`SURVEY <tool> key=value …` (integer counts only), key by key with `tools/gate/baselines/<tool>.txt`
(ADR-0006). `--full=<tool>` runs one survey. A missing `workspace/` prints `SKIPPED: workspace absent`
and exits 0 unless `--require-workspace` is given.

To refresh a baseline after a deliberate parser change:

1. Run the gate. On a mismatch it prints the survey's new line after `now:`.
2. Copy that line, and nothing else, into `tools/gate/baselines/<tool>.txt`.
3. Commit the baseline with the parser change, and say in the commit message which count moved and why.

To register a new survey, end its output with a `SURVEY <tool> …` line, add one `Survey(...)` line to
`SURVEYS` and commit its baseline. A survey that takes over 60 s gets `opt_in=True`.
