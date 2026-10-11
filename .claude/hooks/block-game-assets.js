#!/usr/bin/env node
// PreToolUse hook: deny any `git add` that could stage game data.
//
// Rationale: the game files, extracted MPQ contents and the Ghidra project are copyrighted
// material and never enter git (ADR-0001). .gitignore keeps them out of a normal `git add`; this
// hook closes the two ways around it: a forced add (`-f` / `--force`) and naming such a path
// explicitly. See CLAUDE.md -> "Commit hygiene".
//
// Wired up in .claude/settings.json under hooks.PreToolUse with matcher "Bash". Reuses the
// command reader from block-push-and-history-rewrite.js, so a commit message that merely mentions
// `git add -f` passes.

const { readFileSync } = require("fs");
const { simpleCommands } = require("./block-push-and-history-rewrite.js");

const ADD = /^git(?:\s+(?:-C|-c)\s+\S+)*\s+add\b(.*)$/s;
const FORCED = /(^|\s)(-f|--force|-[A-Za-z]*f[A-Za-z]*)(\s|$)/;
const GAME_PATH = /(^|[\s"'/])workspace\/|\.(mpq|exe|dll|bin|ds1|dt1|dc6|dcc|d2s|gpr)(["'\s]|$)/i;

function offending(seg) {
  const m = seg.match(ADD);
  if (!m) return null;
  return FORCED.test(m[1]) || GAME_PATH.test(m[1]) ? seg.trim() : null;
}

module.exports = { offending };

if (require.main === module) {
  const input = JSON.parse(readFileSync(0, "utf8") || "{}");
  const cmd = (input.tool_input && input.tool_input.command) || "";
  const hit = simpleCommands(cmd).map(offending).find(Boolean);
  if (!hit) {
    process.stdout.write("{}");
    process.exit(0);
  }
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason:
          `Blocked "${hit}". Game data, workspace/ and the Ghidra project never enter git ` +
          `(ADR-0001), and a forced add is how they would. Stage docs, re/ and tools/ files by ` +
          `explicit path. See CLAUDE.md -> "Commit hygiene".`,
      },
    }),
  );
  process.exit(0);
}
