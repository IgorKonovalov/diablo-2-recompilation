#!/usr/bin/env python3
"""export_publish.py: one-command publish of the public export (ADR-0038, plan 0070).

Publishing
  python3 -I tools/export_publish.py [--target DIR] [--base /name/] [--date YYYY-MM-DD] [--no-illustrations]
                                     [--skip-site-build] [--push]

Steps, one line each; the first failure stops the run with a non-zero exit:
  1 refuse --push inside an agent session (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT set; exit 2)
  2 target checks: a git repo on `main`, clean tree, fast-forwarded from origin
  3 every manifest page is in docs/export/reviewed-pages.txt
  4 build the cut into workspace/export (export_build.py), then export_check.py with --repo (0 failures)
  5 copy workspace/export-repo/ project files, then the cut (content, illustrations, widgets, cut.json), into the target
  6 `npm ci` in site/ when package-lock.json changed or node_modules is missing
  7 clear Astro's content cache (site/node_modules/.astro, site/.astro), then site build and link check (logs under
    workspace/export-publish-logs/)
  8 commit `docs: cut <date>` by explicit paths; nothing changed means "nothing to publish", exit 0
  9 with --push only: `git push origin main` and print the Pages URL
The owner runs --push in their own terminal; re-running after a commit is a no-op except the push.
This script writes only into the target and the gitignored workspace/ of this repository.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WS = os.path.join(REPO, "workspace")
DOCS = os.path.join(REPO, "docs")
DEFAULT_TARGET = "~/Work/arpg-1-14d-notes"
# Folders of the export repository's project files whose deletions are mirrored (never node_modules, dist, .git).
MIRROR = ("site/src/components", "site/src/styles", "site/scripts", ".github/workflows")
# What is copied from the cut, relative to workspace/export/.
CUT_DIRS = ("site/src/content/docs", "site/public/illustrations", "site/public/widgets")
CUT_FILES = ("site/src/cut.json",)


class Stop(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


def say(msg):
    print(msg, flush=True)


def default_run(cmd, cwd=None, env=None, log=None):
    """Run a command; return (exit code, tail of its output). Output goes to `log` when given."""
    e = dict(os.environ, **(env or {}))
    p = subprocess.run(cmd, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if log:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a") as f:
            f.write("$ " + " ".join(cmd) + "\n" + p.stdout)
    return p.returncode, "\n".join(p.stdout.splitlines()[-15:])


def git(target, *args, check=True):
    p = subprocess.run(["git", "-C", target] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode:
        raise Stop(f"git {' '.join(args)} failed: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip() if check else p


def refuse_push_in_agent(push, env=None):
    env = os.environ if env is None else env
    if push and (env.get("CLAUDECODE") or env.get("CLAUDE_CODE_ENTRYPOINT")):
        raise Stop("--push is the owner's: run --push in your own terminal", 2)


def check_target(target):
    if not os.path.isdir(os.path.join(target, ".git")):
        raise Stop(f"{target} is not a git repository")
    br = git(target, "rev-parse", "--abbrev-ref", "HEAD")
    if br != "main":
        raise Stop(f"target is on branch {br}, not main")
    if git(target, "status", "--porcelain"):
        raise Stop("target working tree is not clean")
    git(target, "fetch", "origin")
    ahead, behind = (int(x) for x in git(target, "rev-list", "--left-right", "--count",
                                         "main...origin/main").split())
    if behind and ahead:
        raise Stop(f"main has diverged from origin/main ({ahead} ahead, {behind} behind)")
    if behind:
        git(target, "merge", "--ff-only", "origin/main")
        return f"fast-forwarded {behind} commit(s) from origin/main"
    return "up to date" if not ahead else f"{ahead} unpushed commit(s)"


def listed(path):
    out = set()
    with open(path) as f:
        for ln in f:
            ln = ln.split("#", 1)[0].strip()
            if ln:
                out.add(ln.split()[0])
    return out


def manifest_pages(path):
    pages = []
    with open(path) as f:
        for ln in f:
            w = ln.split("#", 1)[0].split()
            if len(w) >= 2 and w[0] == "page":
                pages.append(w[1])
    return pages


def check_reviewed(manifest, reviewed):
    missing = [p for p in manifest_pages(manifest) if p not in listed(reviewed)]
    if missing:
        raise Stop("needs a redaction review (not in reviewed-pages.txt): " + ", ".join(missing))
    return len(manifest_pages(manifest))


def tree_files(root):
    out = []
    for d, _, fs in os.walk(root):
        out += [os.path.relpath(os.path.join(d, f), root) for f in fs]
    return sorted(out)


def replace_dir(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    if os.path.isdir(src):
        shutil.copytree(src, dst)


def copy_project(repo_files, target):
    """Copy the export repository's files; mirror deletions in MIRROR folders only. Returns the copied paths."""
    rels = tree_files(repo_files)
    for m in MIRROR:
        base = os.path.join(target, m)
        if os.path.isdir(base):
            for f in tree_files(base):
                if os.path.join(m, f) not in rels:
                    os.remove(os.path.join(base, f))
    for r in rels:
        dst = os.path.join(target, r)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(repo_files, r), dst)
    return rels


def copy_cut(cut, target):
    for d in CUT_DIRS:
        replace_dir(os.path.join(cut, d), os.path.join(target, d))
    for f in CUT_FILES:
        dst = os.path.join(target, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(cut, f), dst)


def clear_astro_cache(site):
    """Remove Astro's content cache before a build: it re-renders only entries whose text changed, so a changed rehype step or
    config would otherwise publish stale HTML for the pages whose text did not. Both places the cache lives; -> the ones removed."""
    gone = []
    for rel in (os.path.join("node_modules", ".astro"), ".astro"):
        d = os.path.join(site, rel)
        if os.path.isdir(d):
            shutil.rmtree(d)
            gone.append(rel)
    return gone


def lock_changed(target):
    lock = "site/package-lock.json"
    p = git(target, "diff", "--quiet", "HEAD", "--", lock, check=False)
    return p.returncode != 0


def stage_paths(target, project_rels):
    paths = list(project_rels) + list(CUT_DIRS) + list(CUT_FILES) + list(MIRROR)
    paths.append("site/package-lock.json")
    return [p for p in dict.fromkeys(paths) if os.path.exists(os.path.join(target, p))
            or git(target, "ls-files", "--", p)]


def pages_url(target):
    url = git(target, "remote", "get-url", "origin")
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    return f"https://{m.group(1)}.github.io/{m.group(2)}/" if m else "(see the remote)"


def publish(a, run=default_run):
    target = os.path.abspath(os.path.expanduser(a.target))
    cut = os.path.join(WS, "export")
    repo_files = os.path.join(WS, "export-repo")
    logs = os.path.join(WS, "export-publish-logs", "publish.log")
    refuse_push_in_agent(a.push)
    say("1 push guard: ok")
    say("2 target: " + check_target(target))
    n = check_reviewed(os.path.join(DOCS, "export", "manifest.txt"), os.path.join(DOCS, "export", "reviewed-pages.txt"))
    say(f"3 reviewed pages: {n} manifest pages listed")
    bcmd = [sys.executable, "-I", os.path.join(HERE, "export_build.py"), "--out", cut]
    bcmd += ["--date", a.date] if a.date else []
    bcmd += ["--no-illustrations"] if a.no_illustrations else []
    rc, tail = run(bcmd, log=logs)
    if rc:
        raise Stop("export_build failed:\n" + tail)
    rc, tail = run([sys.executable, "-I", os.path.join(HERE, "export_check.py"), cut, "--repo", repo_files], log=logs)
    if rc:
        raise Stop("export_check failed:\n" + tail)
    say("4 build and check: " + (tail.splitlines()[-1] if tail else "ok"))
    with open(os.path.join(cut, "site", "src", "cut.json")) as f:
        date = json.load(f)["date"]
    rels = copy_project(repo_files, target)
    copy_cut(cut, target)
    say(f"5 copied {len(rels)} project files and the cut ({date})")
    site = os.path.join(target, "site")
    # From here a failure leaves the copied files in the target, and the next run refuses a dirty tree.
    undo = f"\nthe target holds the copied files; to start over: git -C {target} reset -q && git -C {target} checkout -- . && git -C {target} clean -fdq"
    if lock_changed(target) or not os.path.isdir(os.path.join(site, "node_modules")):
        rc, tail = run(["npm", "ci"], cwd=site, log=logs)
        if rc:
            raise Stop("npm ci failed:\n" + tail + undo)
        say("6 npm ci: done")
    else:
        say("6 npm ci: skipped (lock unchanged, node_modules present)")
    if a.skip_site_build:
        say("7 site build: skipped")
    else:
        base = a.base or "/" + os.path.basename(target) + "/"
        env = {"SITE_BASE": base}
        gone = clear_astro_cache(site)
        say("7 astro cache: " + (", ".join(gone) + " removed" if gone else "none present"))
        rc, tail = run(["npm", "run", "build"], cwd=site, env=env, log=logs)
        if rc:
            raise Stop("site build failed:\n" + tail + undo)
        rc, tail = run(["node", "scripts/check-site-links.mjs", "dist"], cwd=site, env=env, log=logs)
        if rc:
            raise Stop("link check failed:\n" + tail + undo)
        say("7 site build and link check: " + (tail.splitlines()[-1] if tail else "ok"))
    paths = stage_paths(target, rels)
    git(target, "add", "--", *paths)
    if not git(target, "status", "--porcelain"):
        say("8 nothing to publish")
    else:
        git(target, "commit", "-q", "-m", f"docs: cut {date}")
        say("8 committed: " + git(target, "log", "-1", "--format=%h %s"))
        say(git(target, "show", "--stat", "--format=", "HEAD").splitlines()[-1].strip())
    if a.push:
        git(target, "push", "origin", "main")
        say("9 pushed; Pages URL: " + pages_url(target))
    else:
        say("9 not pushed. To publish, run in your own terminal: python3 -I tools/export_publish.py --push")
        say(f"  or: git -C {target} push origin main")
    return 0


def main(argv=None, run=default_run):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--base", help="SITE_BASE for the site build (default /<target folder name>/)")
    ap.add_argument("--date", help="cut date YYYY-MM-DD (default today)")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--no-illustrations", action="store_true")
    ap.add_argument("--skip-site-build", action="store_true")
    a = ap.parse_args(argv)
    if a.date and not re.fullmatch(r"\d{4}-\d\d-\d\d", a.date):
        ap.error("--date is YYYY-MM-DD")
    try:
        return publish(a, run)
    except Stop as e:
        print(f"export_publish: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
