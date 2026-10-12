// Tests for gate-on-commit.js (plan 0007 Phase 3). Run: node --test .claude/hooks/gate-on-commit.test.mjs
//
// Each test builds a throwaway git repo under /tmp/claude-1000/hooktest/ from a copy
// of this checkout's docs/, re/, .claude/ (link targets) and tools/gate.py, makes it
// green (declaring the struct types the real tree is still missing), then feeds the
// hook synthetic PreToolUse JSON.

import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync, execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, cpSync, writeFileSync, appendFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const HOOK = path.join(HERE, "gate-on-commit.js");
const BASE = "/tmp/claude-1000/hooktest";

function git(dir, ...args) {
  return execFileSync("git", ["-C", dir, "-c", "user.name=t", "-c", "user.email=t@t", ...args], {
    encoding: "utf8",
  });
}

function makeRepo(tag) {
  mkdirSync(BASE, { recursive: true });
  const dir = mkdtempSync(path.join(BASE, `${tag}-`));
  for (const p of ["docs", "re", ".claude"]) cpSync(path.join(REPO, p), path.join(dir, p), { recursive: true });
  mkdirSync(path.join(dir, "tools"));
  cpSync(path.join(REPO, "tools", "gate.py"), path.join(dir, "tools", "gate.py"));
  // Make the copy green regardless of open E4 defects in the real tree.
  writeFileSync(path.join(dir, "re", "types", "hooktest.h"), "struct DataTables;\nstruct Game;\nstruct Unit;\n");
  git(dir, "init", "-q");
  git(dir, "add", "docs", "re", "tools", ".claude");
  git(dir, "commit", "-q", "-m", "base");
  return dir;
}

const BROKEN = "\nBroken anchor for the hook test `fn:GAME_InitSeeds@0x0052C281` [C].\n";

function runHook(command, cwd) {
  const r = spawnSync("node", [HOOK], {
    input: JSON.stringify({ hook_event_name: "PreToolUse", tool_name: "Bash", tool_input: { command }, cwd }),
    encoding: "utf8",
    env: { ...process.env, CLAUDE_PROJECT_DIR: cwd },
  });
  assert.equal(r.status, 0, r.stderr);
  const out = JSON.parse(r.stdout);
  const hso = out.hookSpecificOutput;
  return { denied: !!hso && hso.permissionDecision === "deny", reason: hso ? hso.permissionDecisionReason : "", stderr: r.stderr, stdout: r.stdout };
}

test("base copy is green", () => {
  const dir = makeRepo("base");
  const r = spawnSync("python3", ["-I", path.join(dir, "tools", "gate.py"), "--no-warnings", "--root", dir], { encoding: "utf8" });
  assert.equal(r.status, 0, r.stdout);
});

test("(a) staged doc with a broken anchor is denied with the gate's error lines", () => {
  const dir = makeRepo("a");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  git(dir, "add", "docs/specs/rng/seeds.md");
  const r = runHook('git commit -m "docs(specs): x"', dir);
  assert.ok(r.denied);
  assert.match(r.reason, /seeds\.md:\d+: E1 .*GAME_InitSeeds/);
  assert.match(r.reason, /gate fast tier: RED/);
});

test("(a2) chained git add && git commit sees the not-yet-staged path", () => {
  const dir = makeRepo("a2");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook('git add docs/specs/rng/seeds.md && git commit -m "docs(specs): x"', dir);
  assert.ok(r.denied);
  assert.match(r.reason, /E1 .*GAME_InitSeeds/);
});

test("(b) staging only tools/ does not run the gate", () => {
  const dir = makeRepo("b");
  // The working tree is red, but nothing under docs/ or re/ is staged: an allow proves no gate run.
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  writeFileSync(path.join(dir, "tools", "x.py"), "print(1)\n");
  git(dir, "add", "tools/x.py");
  const r = runHook('git add tools/x.py && git commit -m "feat(tools): x"', dir);
  assert.ok(!r.denied, r.reason);
  assert.equal(r.stdout, "{}");
  assert.equal(r.stderr, "");
});

test("(c) a green commit is allowed with no output", () => {
  const dir = makeRepo("c");
  appendFileSync(path.join(dir, "docs/backlog.md"), "\nA harmless line.\n");
  git(dir, "add", "docs/backlog.md");
  const r = runHook('git commit -m "docs: x"', dir);
  assert.ok(!r.denied, r.reason);
  assert.equal(r.stdout, "{}");
  assert.equal(r.stderr, "");
});

test("(d) git -C <other worktree> commit gates that worktree, not the cwd", () => {
  const green = makeRepo("d-cwd");
  const red = makeRepo("d-other");
  appendFileSync(path.join(red, "docs/specs/rng/seeds.md"), BROKEN);
  git(red, "add", "docs/specs/rng/seeds.md");
  const r = runHook(`git -C ${red} commit -m "docs(specs): x"`, green);
  assert.ok(r.denied);
  assert.ok(r.reason.includes(red), r.reason);
  // And the reverse: committing the green repo from the red one's cwd is allowed.
  appendFileSync(path.join(green, "docs/backlog.md"), "\nA harmless line.\n");
  git(green, "add", "docs/backlog.md");
  const r2 = runHook(`git -C ${green} commit -m "docs: x"`, red);
  assert.ok(!r2.denied, r2.reason);
});

test("root without tools/gate.py is allowed silently", () => {
  const dir = makeRepo("nogate");
  git(dir, "rm", "-q", "tools/gate.py");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  git(dir, "add", "docs/specs/rng/seeds.md");
  const r = runHook('git commit -m "x"', dir);
  assert.ok(!r.denied);
  assert.equal(r.stderr, "");
});

// Review fixes (plan 0007 Phase 3 review).

test("(e) cd into a subdirectory: git add paths resolve against it", () => {
  const dir = makeRepo("e");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook('cd docs/specs/rng && git add seeds.md && git commit -m "docs(specs): x"', dir);
  assert.ok(r.denied);
  assert.match(r.reason, /E1 .*GAME_InitSeeds/);
});

test("(f) cd into another repo: that repo is gated, not the cwd", () => {
  const green = makeRepo("f-cwd");
  const red = makeRepo("f-other");
  appendFileSync(path.join(red, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook(`cd ${red} && git add docs/specs/rng/seeds.md && git commit -m "docs(specs): x"`, green);
  assert.ok(r.denied);
  assert.ok(r.reason.includes(red), r.reason);
});

test("(g) a heredoc commit message mentioning git add docs/… is not a command", () => {
  const dir = makeRepo("g");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  writeFileSync(path.join(dir, "tools", "x.py"), "print(1)\n");
  git(dir, "add", "tools/x.py");
  const cmd = "git commit -F - <<'EOF'\nfeat(tools): x\n\ngit add docs/specs/rng/seeds.md\nEOF";
  const r = runHook(cmd, dir);
  assert.ok(!r.denied, r.reason);
  assert.equal(r.stdout, "{}");
  assert.equal(r.stderr, "");
});

test("(h) git add -u counts every modified tracked path", () => {
  const dir = makeRepo("h");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook('git add -u && git commit -m "docs(specs): x"', dir);
  assert.ok(r.denied);
  assert.match(r.reason, /E1 .*GAME_InitSeeds/);
});

test("(i) a bash -c wrapper is unwrapped", () => {
  const dir = makeRepo("i");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook(`bash -c "git add docs/specs/rng/seeds.md && git commit -m x"`, dir);
  assert.ok(r.denied);
  assert.match(r.reason, /E1 .*GAME_InitSeeds/);
});

test("(j) -S takes no separate value: a following path is a commit pathspec", () => {
  const dir = makeRepo("j");
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  const r = runHook('git commit -S docs/specs/rng/seeds.md -m "docs(specs): x"', dir);
  assert.ok(r.denied);
});

test("(k) a crashing gate.py (exit 1, no summary line) fails open with a warning", () => {
  const dir = makeRepo("k");
  writeFileSync(path.join(dir, "tools", "gate.py"), 'raise RuntimeError("stub gate boom")\n');
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  git(dir, "add", "docs/specs/rng/seeds.md");
  const r = runHook('git commit -m "docs(specs): x"', dir);
  assert.ok(!r.denied, r.reason);
  assert.equal(r.stdout, "{}");
  assert.match(r.stderr, /gate-on-commit: tools\/gate\.py crashed \(RuntimeError: stub gate boom\)/);
});

test("(l) an unstaged red edit outside the commit does not block it (gate.py --staged)", () => {
  const dir = makeRepo("l");
  // Another lane's uncommitted broken edit sits in the working tree, not in the commit.
  appendFileSync(path.join(dir, "docs/specs/rng/seeds.md"), BROKEN);
  appendFileSync(path.join(dir, "docs/backlog.md"), "\nA harmless line.\n");
  git(dir, "add", "docs/backlog.md");
  const r = runHook('git commit -m "docs: x"', dir);
  assert.ok(!r.denied, r.reason);
  // The same broken edit, added on the same command line, is overlaid with --also and blocks.
  const r2 = runHook('git add docs/specs/rng/seeds.md && git commit -m "docs(specs): x"', dir);
  assert.ok(r2.denied);
  assert.match(r2.reason, /E1 .*GAME_InitSeeds/);
});
