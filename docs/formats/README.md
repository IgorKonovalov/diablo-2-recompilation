# Formats

One file per container or binary format (`mpq.md`, `installer.md`, `excel-bin.md`, `ds1.md`, `dt1.md`,
`dc6.md`, `dcc.md`, `d2s.md`). Owned by `archivist`. Each file covers layout tables with offsets and
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

