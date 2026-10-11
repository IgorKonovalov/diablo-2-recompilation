#!/usr/bin/env node
// PreToolUse hook: deny broad `git add` (-A / --all / bare "." / ":/").
//
// Rationale: this repo is scaffolded to run agent sessions (and, later, parallel
// git worktrees) that may share a working tree. Broad staging sweeps stray
// untracked files and another session's in-progress work into a commit. Stage
// explicit paths instead. See CLAUDE.md -> "Commit hygiene".
//
// Wired up in .claude/settings.json under hooks.PreToolUse with matcher
// "Bash|PowerShell". The matcher only filters by tool name; this script decides
// whether to deny (see the pass-through early return below).

const { readFileSync } = require("fs");

const input = JSON.parse(readFileSync(0, "utf8"));
const cmd = (input.tool_input && input.tool_input.command) || "";

// Inspect every `git add ...` occurrence, even inside a compound command line
// like `python3 tools/x.py && git add -A && git commit`. Split on shell separators first.
const segments = cmd.split(/&&|\|\||;|\|/);
let offending = null;
for (const seg of segments) {
  const m = seg.match(/\bgit\s+add\b(.*)$/);
  if (!m) continue;
  const args = m[1];
  // Broad stagers: -A / --all / --no-ignore-removal, a bare "." (or "./"),
  // and the ":/" repo-root pathspec. Explicit file paths (e.g. "docs/plans/0001-bootstrap.md",
  // "./tools/inventory.py") are left alone.
  if (
    /(^|\s)(-A|--all|--no-ignore-removal)(\s|$)/.test(args) ||
    /(^|\s)\.(\/)?(\s|$)/.test(args) ||
    /(^|\s):\/(\s|$)/.test(args)
  ) {
    offending = seg.trim();
    break;
  }
}

if (!offending) {
  // Pass-through: let the original command run unchanged.
  process.stdout.write("{}");
  process.exit(0);
}

process.stdout.write(
  JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason:
        `Blocked broad staging: "${offending}". Broad "git add -A / --all / . / :/" ` +
        `sweeps untracked and cross-session files into your commit. Stage only the ` +
        `files you changed, by explicit path (e.g. "git add docs/findings/rng/0001-step.md ` +
        `re/symbols.csv"). Run "git status" first if unsure. See CLAUDE.md.`,
    },
  }),
);
process.exit(0);
