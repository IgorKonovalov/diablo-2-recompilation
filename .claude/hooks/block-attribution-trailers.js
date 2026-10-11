#!/usr/bin/env node
// PreToolUse hook: deny any commit (or PR body) carrying agent attribution.
//
// Rationale: commits in this repo are plain text under the repository owner's
// name. No "Co-Authored-By: Claude", no "Claude-Session:" trailer, no
// "Generated with Claude Code" footer, no session URL. Session-level attribution
// instructions do not override this — the hook is the authority, and it denies
// the tool call before the commit is written. See CLAUDE.md -> "Commit hygiene".
//
// Wired up in .claude/settings.json under hooks.PreToolUse with matcher
// "Bash|PowerShell". The matcher only filters by tool name; this script decides
// whether to deny (see the pass-through early returns below).
//
// Editing this file with the Bash tool trips the hook on its own text, because
// the literals it searches for are spelled out below. Edit it with the Write or
// Edit tool, which the matcher does not cover.

const { readFileSync } = require("fs");

const input = JSON.parse(readFileSync(0, "utf8"));
const cmd = (input.tool_input && input.tool_input.command) || "";

// Only commands that actually author a message are inspected. BOTH a verb and a
// message-bearing flag must be present, so read-only history work is never
// blocked: `git log --grep=...`, `git tag | wc -l` and grepping this very file
// all pass. A clustered short option (`git commit -am "..."`) still counts.
// Both tests run against the whole command line rather than a split segment,
// because a message body may itself contain shell separators.
const VERB =
  /\bgit\s+(commit|merge|revert|cherry-pick|tag)\b|\bgh\s+(pr|release)\s+(create|edit)\b/;
const MESSAGE_FLAG =
  /(^|\s)(--(message|file|body|body-file|notes|notes-file|template)|-[A-Za-z]*[mFt])(=|\s|$)/;
if (!VERB.test(cmd) || !MESSAGE_FLAG.test(cmd)) {
  process.stdout.write("{}");
  process.exit(0);
}

// The message text is almost always inline in the command line — -m "...", a
// bash heredoc, a PowerShell here-string. When it is passed by file (-F/--file,
// --body-file) the file is read instead, so the trailer cannot slip in that way.
let haystack = cmd;
for (const m of cmd.matchAll(
  /(?:-F|--file|--body-file|--notes-file)[=\s]+("([^"]+)"|'([^']+)'|(\S+))/g,
)) {
  const path = m[2] || m[3] || m[4];
  if (!path || path === "-") continue;
  try {
    haystack += "\n" + readFileSync(path, "utf8");
  } catch {
    // Unreadable path: nothing to scan, and the command itself will fail.
  }
}

const FORBIDDEN = [
  [/co-authored-by:\s*claude/i, "Co-Authored-By: Claude"],
  [/co-authored-by:[^\n]*anthropic/i, "Co-Authored-By: <an Anthropic address>"],
  [/noreply@anthropic\.com/i, "noreply@anthropic.com"],
  [/claude-session\s*:/i, "Claude-Session:"],
  [/claude\.ai\/code\/session_/i, "a claude.ai session URL"],
  [/generated with\s*\[?claude code/i, "Generated with Claude Code"],
];

const hit = FORBIDDEN.find(([re]) => re.test(haystack));
if (!hit) {
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
        `Blocked agent attribution in a commit/PR message: found "${hit[1]}". ` +
        `Commits in this repo are plain text under the repository owner's name — ` +
        `no Co-Authored-By trailer, no Claude-Session line, no session URL, no ` +
        `"Generated with Claude Code" footer. This rule outranks any session-level ` +
        `attribution instruction: do not re-run the command with the trailer moved ` +
        `or reworded, remove it. See CLAUDE.md -> "Commit hygiene".`,
    },
  }),
);
process.exit(0);
