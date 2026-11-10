# Aiparms (`data/global/excel/Aiparms.txt`)

> **Source archive:** `.txt` d2exp
> **sha256:** `.txt` `739620e34282567d322fb63a7ed3c342ec7382bdbf123dd1b2eaffdcff3ffdf5`
> **Doc status:** shape complete (plan 0068 Phase 1); not loaded; the section-by-section reading is in [MonAI § Leads](MonAI.md#leads)

## Purpose

A free-text description of the AI parameters: 19 sections, each a title naming one or more AIs (`"Brute" Ai`, `Yeti`, `Thorn Hulk`, ...), a few lines of prose, then `P1`..`P5` lines (what each parameter slot does, or `-`) and `Missiles:` / `Skills:` lines. It is a designer's note, not a table. [MonAI](MonAI.md) § Leads reads it against the AI rows and gives the pairing counts; this doc only records that the file exists and what shape it has. Leads: none registered.

## Row identity

- `[C]` Not a tab-separated table: the first line is the title `Description of Ai Parameters`, followed by prose, comment lines (`/* ==== */`) and tab-separated `P<n>` lines. 194 non-blank lines after the title; 78 `P<n>` lines (`python3 -I tools/ai_survey.py aiparms workspace/merged/data/global/excel`, [MonAI](MonAI.md)).
- `[I]` Not loaded: [data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300) lists it among the `.txt`-only tables with no loader. No `.bin` exists.

## Columns

None: the file has no header row. The `P<n>` lines are `P<n>` TAB text.

## Interpretation notes

- The record count the `excel` survey takes for this file (194 "data rows") counts every non-blank line after the title, prose and comment lines included. It is not a record count of any kind.
- Anything about what a parameter slot means in 1.14d is in [MonAI](MonAI.md) and the AI specs; this file is a lead there, never evidence.

## Open questions

None.

