#!/usr/bin/env python3
"""PreToolUse guard (ADR-0001): game data never enters git.

Blocks `git add -f/--force` and any `git add` that names workspace/ or game file extensions.
"""
import json, re, sys

cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
for seg in re.split(r"&&|\|\||;|\n", cmd):
    if not re.search(r"\bgit\b.*\badd\b", seg):
        continue
    if re.search(r"(\s-f\b|--force)", seg) or re.search(
        r"workspace/|\.(mpq|exe|dll|bin|ds1|dt1|dc6|dcc|d2s)\b", seg, re.I
    ):
        print("Blocked: game data and workspace/ never enter git (ADR-0001).", file=sys.stderr)
        sys.exit(2)
