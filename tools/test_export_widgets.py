#!/usr/bin/env python3
"""Self-tests of the widget rule X13 and the builder's ```widget step (ADR-0037, plan 0070 Phase 11; gate rule E20).

Usage: python3 -I tools/test_export_widgets.py

js_problems and json_problems on clean and adversarial text (each banned form, the obfuscations the ruling covers, the
forms that must stay allowed); verify_widget on a folder and its tamperings; check_cut and check_repo; the builder's
widget block (text fallback, illustration fallback, drops) and an end-to-end build whose cut passes the check.
Prints `TEST export_widgets: N checks, M failed`.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_build as eb  # noqa: E402
import export_check as ec  # noqa: E402

checks, failed = 0, []
M = ec.WIDGET_MARKER


def ok(cond, what):
    global checks
    checks += 1
    if not cond:
        failed.append(what)
        print(f"FAIL {what}")


def put(path, text, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        f.write(text)


CLEAN = f"// {M}\nconst a = [1, 2];\nexport function compute(i, d) {{ return a.at(i) + d.rule; }}\n"
REAL = os.path.join(HERE, "widgets", "rng")

# (name, line added to CLEAN): every one must fail js_problems
BAD = [
    ("fetch", "fetch(u);"), ("XMLHttpRequest", "new XMLHttpRequest();"), ("WebSocket", "new WebSocket(u);"),
    ("EventSource", "new EventSource(u);"), ("sendBeacon", "q.sendBeacon(u);"), ("importScripts", "importScripts(u);"),
    ("Worker", "new Worker(u);"), ("dynamic import", "import(u);"), ("static import", "import x from 'y';"),
    ("export from", "export * from 'y';"), ("require", "require('x');"), ("eval", "eval(s);"),
    ("Function", "new Function(s);"), ("setTimeout string", "setTimeout('x()', 1);"),
    ("setInterval template", "setInterval(`x`, 1);"), ("setTimeout name", "setTimeout(code, 1);"),
    ("innerHTML", "e.innerHTML = s;"), ("outerHTML", "e.outerHTML = s;"), ("insertAdjacentHTML", "e.insertAdjacentHTML(a, s);"),
    ("document.write", "document.write(s);"), ("document.writeln", "document.writeln(s);"),
    ("localStorage", "localStorage.x = 1;"), ("sessionStorage", "sessionStorage.x = 1;"), ("indexedDB", "indexedDB.open(s);"),
    ("cookie", "document.cookie = s;"), ("navigator", "navigator.sendBeacon;"), ("location", "location.href;"),
    ("window.open", "window.open(s);"), ("postMessage", "p.postMessage(s);"), ("FileReader", "new FileReader();"),
    ("file input", "i.type = 'file';"), ("file word in a comment", "// reads a file"),
    ("URL in a string", "const u = 'https://example.org/x';"), ("protocol-relative", "const u = '//cdn.example.org/x.js';"),
    ("URL in a comment", "// see http://example.org"), ("www", "const u = 'www.x.org';"),
    ("css url(", "e.style.cssText = 'background:url(x)';"), ("css import", "const c = '@import x';"),
    ("src assignment", "img.src = s;"), ("href assignment", "a.href = s;"), ("setAttribute href", "a.setAttribute('href', s);"),
    ("setAttribute name not literal", "a.setAttribute(n, s);"), ("setAttribute on*", "a.setAttribute('onclick', s);"),
    ("string with scheme", "const u = 'javascript:alert';"), ("script element", "document.createElement('script');"),
    ("createElement not literal", "document.createElement(t);"), ("createElement iframe", "document.createElement('iframe');"),
    # obfuscations (the ruling)
    ("window bracket concat", "window['fe' + 'tch'](u);"), ("globalThis", "globalThis.x;"), ("self bracket", "self[k];"),
    ("window alias", "const w = window;"), ("top bare", "top.x;"), ("parent bare", "parent.x;"), ("global", "global.x;"),
    ("hex escape", "const s = '\\x66etch';"), ("unicode escape", "const s = '\\u0066etch';"), ("octal escape", "const s = '\\146etch';"),
    ("fromCharCode", "String.fromCharCode(102);"), ("atob", "atob(s);"), ("constructor chain", "''.constructor.constructor(s)();"),
    ("prototype", "Object.prototype.x;"), ("Reflect", "Reflect.get(a, b);"), ("Proxy", "new Proxy(a, b);"),
    ("this bracket", "this[k];"), ("bracket string key", "obj['fe' + 'tch'];"), ("document bracket", "document['write'](s);"),
    ("document alias", "const d = document;"), ("defaultView", "e.ownerDocument.defaultView;"),
    ("template substitution", "const s = `a${b}`;"), ("with", "with (o) { x; }"), ("Blob", "new Blob([s]);"),
    ("URL class", "URL.createObjectURL(b);"), ("Image", "new Image();"), ("DOMParser", "new DOMParser();"),
    ("alert", "alert(1);"),
    # the text rules on a comment or a string
    ("address in a comment", "// at 0x00556F60"), ("tool name in a string", "const s = 'opened in Ghidra';"),
    ("ADR in a string", "const s = 'see ADR-0037';"), ("Warden in a string", "const s = 'Warden';"),
    ("decompiler name", "const FUN_00112233 = 1;"), ("anchor in a comment", "// fn:Thing@0x004A1B20"),
    ("param_ name in a string", "const s = 'param_3';"),

    # the lane/x11w review's escapes: each passed the ban lists; the allowlist of names and the lexer close them
    ("constructor built from pieces", "const k = 'constr' + 'uctor'; const F = (() => 0)[k]; F('x')();"),
    ("event view is the window", "function f(e) { const w = e.view; w.alert2(1); }"),
    ("computed member by a variable", "const v = rows[i];"), ("computed member by an expression", "const v = rows[i + 1];"),
    ("computed member after a call", "f()[k];"), ("optional computed member", "const w = e?.[k];"),
    ("bare open", "open('/' + '/evil.example/');"), ("bare name (window.name storage)", "name = 'remember';"),
    ("history", "history.pushState(null, '', '/x');"), ("bare status", "status = 'x';"),
    ("regex literal hides code", "const a = /\"/; const g = 1; const b = /\"/;"),
    ("regex after if", "if (a) /\"/.test(''); const g = 1; /\"/;"), ("regex after return", "function f() { return /x/; }"),
    ("slash after a block", "{ }\n/x/;"), ("lone CR ends a comment", "// note\rconst g = 1;"),
    ("U+2028 ends a comment", "// note const g = 1;"), ("HTML comment open", "<!-- x"),
    ("backslash in a name", "const f\\u0065 = 1;"), ("non-ASCII name", "const café = 1;"), ("hash", "#!x"),
    ("createElement.call", "const i = d.createElement.call(d, 'i' + 'mg');"),
    ("setAttribute.call", "a.setAttribute.call(a, 'sr' + 'c', u);"), ("Object.assign", "Object.assign(i, { src: u });"),
    ("destructured ownerDocument", "const { ownerDocument: d } = el;"), ("shorthand view", "const { view } = e;"),
    ("parameter pattern view", "const f = ({ view }) => view;"), ("computed key", "const { [k]: w } = el;"),
    ("computed key in a literal", "const o = { [k]: 1 };"), ("style", "e.style.top = '0';"),
    ("style background url", "e.style.backgroundImage = 'u' + 'rl(/x.png)';"), ("composedPath", "e.composedPath();"),
    ("getRootNode", "el.getRootNode();"), ("anchor click", "document.querySelector('a').click();"),
    ("form submit", "f.submit();"), ("bind", "const g = el.addEventListener.bind(el);"),
    ("call", "f.call(x);"), ("apply", "f.apply(x, []);"), ("toString base 36", "el.textContent = (1767).toString(36);"),
    ("FontFace", "new FontFace('x', u).load();"), ("CSS worklet", "CSS.paintWorklet;"), ("Option", "new Option('x');"),
    ("queueMicrotask", "queueMicrotask(f);"), ("node process", "process.exitCode = 3;"),
    ("setAttribute background", "t.setAttribute('background', u);"), ("setAttribute style", "t.setAttribute('style', u);"),
    ("details open member", "d.open = true;"), ("hex address literal", "const a = 0x00556F60;"),
    ("strings joined spell a home path", "const p = '/ho' + 'me/' + 'someone';"),
    ("a slash after a keyword-header paren", "while (a) /x/;"),
]
# forms that must stay allowed
GOOD = [
"e.textContent = s;", "if (typeof document !== 'undefined') { x(); }",
    "document.createElement('div');", "a.setAttribute('aria-live', 'polite');", "setTimeout(() => { x(); }, 5);",
    "setTimeout(function () { x(); }, 5);", "const m = 0x6AC690C5;", "const b = BigInt(1) * 2n;", "const s = 'a\\nb';",
    "x.addEventListener('input', f);", "const o = { data: 1 };", "const u = 'draws, then 87';", "/* block comment */",
    "// widget text: the seed 12345 is illustrative", "const e = el.querySelector('input');",
    "const v = rows.at(i);", "const v = rows[0];", "const { seed, n } = inputs;", "setTimeout(x => x, 5);",
    "const h = (a + b) / 2;", "const q = a / b / 2;", "const s = x.toString(16);", "if (a) { b(); } else { c(); }",
    "const r = { k: 1, drew: true, low: 2 };", "const w = cond ? [1] : [2];", "const m = matchMedia('(prefers-reduced-motion: reduce)').matches;",
    "const big = BigInt.asUintN(32, 5n);", "for (const { low, high } of rows) { f(low, high); }",
]


def js_tests():
    ec.set_allow(ec.load_allow(os.path.join(HERE, "..", "docs", "export", "allow-hex.txt")))
    ok(ec.js_problems(CLEAN) == [], f"the clean script passes ({ec.js_problems(CLEAN)})")
    real = open(os.path.join(REAL, "widget.js"), encoding="utf-8").read()
    ok(ec.js_problems(real) == [], f"the rng widget.js passes ({ec.js_problems(real)[:3]})")
    for name, line in BAD:
        ok(ec.js_problems(CLEAN + line + "\n") != [], f"js: {name} fails ({line})")
    for line in GOOD:
        ok(ec.js_problems(CLEAN + line + "\n") == [], f"js: allowed form passes ({line}: {ec.js_problems(CLEAN + line + chr(10))[:2]})")
    ok(any("marker" in p for p in ec.js_problems(CLEAN.replace(M, "x"))), "js: no marker fails")
    ok(any("KB" in p for p in ec.js_problems(CLEAN + "// " + "a" * 49200 + "\n")), "js: over 48 KB fails")
    ok(any("lex" in p for p in ec.js_problems(CLEAN + "const s = 'abc;\n")), "js: an unterminated string fails (the safe side)")
    ok(any("lex" in p for p in ec.js_problems(CLEAN + "/* open\n")), "js: an unterminated comment fails")
    ok(any("identity" in p for p in ec.js_problems(CLEAN + "const w = 'Ada ' + 'Love' + 'lace';\n", ("Ada Lovelace",))),
       "js: strings joined that spell the identity fail")
    ok(ec.browser_names("globals") and "fetch" in ec.browser_names("globals") and "view" in ec.browser_names("members"),
       "js: the browser name lists load")
    ok(ec.js_problems(CLEAN + "const s = 'fe' + 'tch';\n") == [], "js: a built word alone is not a name (the global object is unreachable)")
    # the global object reached by a bare name is the only route to a built name: every spelling of it fails
    for g in ("window", "self", "top", "parent", "frames", "globalThis", "global", "opener", "this"):
        ok(ec.js_problems(CLEAN + f"const x = {g};\n") != [], f"js: bare {g} fails")


def json_tests():
    good = {"marker": M, "name": "w1", "a": {"b": 1}, "s": {"rows": "toy", "items": [1, 2, 3]}, "t": "text"}
    p, d = ec.json_problems(json.dumps(good))
    ok(p == [] and d == good, f"json: a clean file passes ({p})")
    p, _ = ec.json_problems(open(os.path.join(REAL, "widget.json"), encoding="utf-8").read())
    ok(p == [], f"json: the rng widget.json passes ({p[:2]})")
    ok(ec.json_problems("{")[0] != [], "json: invalid JSON fails")
    ok(ec.json_problems(json.dumps(dict(good, t=" File ")))[0] != [], "json: a string `file` (an input type) fails")
    ok(ec.json_problems(json.dumps(dict(good, marker="x")))[0] != [], "json: wrong marker fails")
    ok(ec.json_problems(json.dumps(dict(good, name="Bad Name")))[0] != [], "json: a bad name fails")
    ok(ec.json_problems(json.dumps(dict(good, s={"rows": "toy", "items": list(range(20))})))[0] == [], "json: 20 entries pass")
    ok(ec.json_problems(json.dumps(dict(good, s={"rows": "toy", "items": list(range(21))})))[0] != [], "json: 21 entries fail")
    ok(ec.json_problems(json.dumps(dict(good, s=[1, 2])))[0] != [], "json: a bare array fails")
    ok(ec.json_problems(json.dumps(dict(good, s={"items": [1]})))[0] != [], "json: an array with no rows key fails")
    ok(ec.json_problems(json.dumps(dict(good, s={"rows": "real", "items": [1]})))[0] != [], "json: rows other than toy/page fails")
    ok(ec.json_problems(json.dumps(dict(good, s={"rows": "page", "items": [1]})))[0] == [], "json: rows page passes")
    ok(ec.json_problems(json.dumps(dict(good, s={"rows": "toy", "items": [[1]]})))[0] != [], "json: a nested array needs its own marking")
    for bad in ("at 0x00556F60", "opened in Ghidra", "see ADR-0037", "fn:Thing@0x004A1B20", "FUN_00112233 here"):
        ok(ec.json_problems(json.dumps(dict(good, t=bad)))[0] != [], f"json: string fails the text rules ({bad})")
    ok(ec.json_problems(json.dumps(dict(good, **{"0x00556F60": 1})))[0] != [], "json: a key fails the text rules")
    ok(ec.json_problems(json.dumps(dict(good, t="x" * 17000)))[0] != [], "json: over 16 KB fails")
    ok(ec.json_problems(json.dumps(dict(good, t="the multiplier 6AC690C5")))[0] == [], "json: the multiplier passes as allow-hex admits it")


def make_folder(root, wid="w1", name="rng", fallback=None, src=None):
    """A widget folder built the way the builder does. -> folder."""
    folder = os.path.join(root, "site", "public", "widgets", wid)
    os.makedirs(folder, exist_ok=True)
    src = src or os.path.join(REAL)
    for f in ("widget.js", "widget.json"):
        shutil.copyfile(os.path.join(src, f), os.path.join(folder, f))
    files = ["widget.js", "widget.json"]
    if fallback:
        put(os.path.join(folder, fallback), "GIF89a " + ec.MARKER + "\n")
        files.append(fallback)
    relist(folder)
    return folder


def relist(folder):
    names = [f for f in os.listdir(folder) if f != "widget.list.json" and os.path.isfile(os.path.join(folder, f))]
    put(os.path.join(folder, "widget.list.json"),
        json.dumps({"marker": M, "files": {f: ec._sha(os.path.join(folder, f)) for f in sorted(names)}}))


def folder_tests(tmp):
    root = os.path.join(tmp, "f")
    folder = make_folder(root, fallback="fallback.gif")
    probs, okf = ec.verify_widget(folder, ())
    ok(probs == [] and okf == {"widget.js", "widget.json", "fallback.gif"}, f"folder: a clean folder verifies ({probs[:2]})")
    # tamper, one at a time
    def tampered(what, mutate, expect):
        r = os.path.join(tmp, "t_" + what.replace(" ", "_"))
        fo = make_folder(r, fallback="fallback.gif")
        mutate(fo)
        pr, okx = ec.verify_widget(fo, ())
        ok(any(expect in p for p in pr) and not okx, f"folder: {what} fails ({pr[:2]})")
    tampered("an extra file", lambda f: put(os.path.join(f, "extra.js"), "x"), "not allowed")
    tampered("an index.html", lambda f: put(os.path.join(f, "index.html"), "x"), "not allowed")
    tampered("a second fallback", lambda f: (put(os.path.join(f, "fallback.png"), ec.MARKER), relist(f)), "more than one")
    tampered("a subfolder", lambda f: os.makedirs(os.path.join(f, "sub")), "subfolder")
    tampered("a missing list", lambda f: os.remove(os.path.join(f, "widget.list.json")), "widget.list.json")
    tampered("a wrong list marker", lambda f: put(os.path.join(f, "widget.list.json"), json.dumps({"marker": "x", "files": {}})), "marker")
    tampered("a tool key in the list", lambda f: put(os.path.join(f, "widget.list.json"), json.dumps({"marker": M, "files": {}, "tool": "x"})), "extra keys")
    tampered("a hash mismatch", lambda f: put(os.path.join(f, "widget.js"), open(os.path.join(f, "widget.js")).read() + " "), "sha256")
    tampered("a file not listed", lambda f: put(os.path.join(f, "widget.list.json"),
             json.dumps({"marker": M, "files": {"widget.js": ec._sha(os.path.join(f, "widget.js"))}})), "not in widget.list.json")
    tampered("a listed file missing", lambda f: os.remove(os.path.join(f, "fallback.gif")), "missing")
    tampered("a fallback without the schematic marker", lambda f: (put(os.path.join(f, "fallback.gif"), "GIF89a"), relist(f)), "no marker")
    tampered("a js without the marker", lambda f: (put(os.path.join(f, "widget.js"), "export function compute() {}\n"), relist(f)), "no marker")
    tampered("a js that fetches (hash updated)", lambda f: (put(os.path.join(f, "widget.js"),
             open(os.path.join(f, "widget.js")).read() + "\nfetch(u);\n"), relist(f)), "banned")
    tampered("a js unlike the reviewed source", lambda f: (put(os.path.join(f, "widget.js"),
             open(os.path.join(f, "widget.js")).read() + "\nconst z = 1;\n"), relist(f)), "byte-equal")
    tampered("a json unlike the reviewed source", lambda f: (put(os.path.join(f, "widget.json"),
             open(os.path.join(f, "widget.json")).read().replace("12345", "12346")), relist(f)), "byte-equal")
    tampered("a json name with no source", lambda f: (put(os.path.join(f, "widget.json"),
             open(os.path.join(f, "widget.json")).read().replace('"rng"', '"nosuch"')), relist(f)), "byte-equal")
    tampered("an identity string", lambda f: (put(os.path.join(f, "widget.js"), open(os.path.join(f, "widget.js")).read() + "\n// zq-ident\n"),
             relist(f)), "byte-equal")
    r = os.path.join(tmp, "ident")
    fo = make_folder(r)
    pr, _ = ec.verify_widget(fo, ("noodle",))
    ok(pr == [], "folder: an identity string absent from the files passes")
    put(os.path.join(fo, "widget.js"), open(os.path.join(fo, "widget.js")).read() + "// noodle\n")
    relist(fo)
    pr, _ = ec.verify_widget(fo, ("noodle",))
    ok(any("identity" in p for p in pr), "folder: an identity string in widget.js fails")
    # a symlink
    r = os.path.join(tmp, "sym")
    fo = make_folder(r)
    os.remove(os.path.join(fo, "widget.js"))
    os.symlink(os.path.join(REAL, "widget.js"), os.path.join(fo, "widget.js"))
    ok(any("symlink" in p for p in ec.verify_widget(fo, ())[0]), "folder: a symlink fails")
    # a reviewed source tree of its own: the byte-equal rule reads the tree it is given
    alt = os.path.join(tmp, "altsrc", "rng")
    shutil.copytree(REAL, alt)
    put(os.path.join(alt, "widget.js"), open(os.path.join(alt, "widget.js")).read() + "// another reviewed source\n")
    fo = make_folder(os.path.join(tmp, "alt"), src=alt)
    ok(ec.verify_widget(fo, (), src_root=os.path.join(tmp, "altsrc"))[0] == [], "folder: byte-equal to the source tree it is given")
    ok(ec.verify_widget(fo, ())[0] != [], "folder: the same folder fails against the real tree")


MANIFEST = "group g 1 Group\npage w.md g 1\n"


def cut_tests(tmp):
    cut = os.path.join(tmp, "cut")
    make_folder(cut, "w1", fallback="fallback.gif")
    put(os.path.join(cut, "site", "src", "cut.json"), json.dumps({"date": "2026-11-17"}))
    man = os.path.join(tmp, "man.txt")
    put(man, MANIFEST)
    page = ("A page.\n\n![Widget fallback: w1](/widgets/w1/fallback.gif)\n\n"
            "[Try it: change the inputs (needs JavaScript)](/widgets/w1/widget.js)\n")
    put(os.path.join(cut, "site", "src", "content", "docs", "g", "w.md"), "---\ntitle: W\n---\n\n" + page)
    f, _ = ec.check_cut(cut, man, ())
    ok(f == [], f"cut: a widget folder with its image and link passes ({f[:2]})")
    # an unverified folder: its link and image fail, with X13 on the folder
    put(os.path.join(cut, "site", "public", "widgets", "w1", "widget.js"), "// x\n")
    f, _ = ec.check_cut(cut, man, ())
    rules = {x[0] for x in f}
    ok("X13" in rules and any(x[0] == "X8" for x in f), f"cut: a folder that fails X13 serves no image or link ({sorted(rules)})")
    ok(any(x[0] == "X13" and x[2] == 0 for x in f) and any(x[0] == "X13" and x[2] > 0 for x in f), "cut: X13 names the folder and the page line")
    # a link or image to a widget that is not in the cut
    cut2 = os.path.join(tmp, "cut2")
    put(os.path.join(cut2, "site", "src", "cut.json"), json.dumps({"date": "2026-11-17"}))
    put(os.path.join(cut2, "site", "src", "content", "docs", "g", "w.md"), "---\ntitle: W\n---\n\n" + page)
    f, _ = ec.check_cut(cut2, man, ())
    ok({x[0] for x in f} == {"X13", "X8"}, f"cut: a page naming a widget the cut lacks fails ({sorted({x[0] for x in f})})")
    # a file at the widgets root, an unmarked loose file, a symlinked folder
    cut3 = os.path.join(tmp, "cut3")
    make_folder(cut3, "w1")
    put(os.path.join(cut3, "site", "src", "cut.json"), json.dumps({"date": "2026-11-17"}))
    put(os.path.join(cut3, "site", "public", "widgets", "loose.js"), "x")
    f, _ = ec.check_cut(cut3, man, ())
    ok(any(x[0] == "X11" and "loose.js" in x[1] for x in f), "cut: a loose file in widgets/ fails X11")
    # a widget image outside a verified folder is an image
    ok(any(h[0] == "X8" for h in ec.check_page("![x](/widgets/zz/fallback.gif)\n", "p.md", "p", 0, set(), ())), "cut: X8 on an unverified widget image")
    ok(not [h for h in ec.check_page("![x](/widgets/zz/fallback.gif)\n", "p.md", "p", 0, set(), (), None, {("zz", "fallback.gif")})], "cut: a verified widget image passes")
    ok(any(h[0] == "X13" for h in ec.check_page("[x](/widgets/zz/widget.json)\n", "p.md", "p", 0, set(), (), None, {("zz", "widget.json")})),
       "cut: only widget.js is a link target")
    ok(any(h[0] == "X13" for h in ec.check_page("[x](/widgets/../x/widget.js)\n", "p.md", "p", 0, set(), (), None, set())), "cut: a dotted link target fails")
    ok(any(h[0] == "X8" for h in ec.check_page("![x](/illustrations/zz/fallback.gif)\n", "p.md", "p", 0, set(), (), None, {("zz", "fallback.gif")})),
       "cut: a widget-verified id does not admit an illustration path")


def repo_tests(tmp):
    repo = os.path.join(tmp, "repo")
    put(os.path.join(repo, "site", "src", "components", "Footer.astro"), "<p>" + ec.FOOTER.replace("{cut.date}", "{cut.date}") + "</p>")
    cfg = "components: { Footer: './src/components/Footer.astro' },\n"
    put(os.path.join(repo, "site", "astro.config.mjs"), cfg)
    base = ec.check_repo(repo, ())
    ok(not [x for x in base if x[0] == "X13"], "repo: no host and no widgets in the cut: no X13")
    ok(any(x[0] == "X13" and "no host" in x[3] for x in ec.check_repo(repo, (), need_host=True)), "repo: a cut with widgets needs the host step")
    put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), HOST_OK)
    f = [x for x in ec.check_repo(repo, ()) if x[0] == "X13"]
    ok(any("Content-Security-Policy" in x[3] for x in f), "repo: a host step without the CSP meta fails")
    csp = f"head: [{{ tag: 'meta', attrs: {{ 'http-equiv': 'Content-Security-Policy', content: \"{ec.CSP_POLICY}\" }} }}],\n"
    put(os.path.join(repo, "site", "astro.config.mjs"), cfg + csp)
    ok(not [x for x in ec.check_repo(repo, ()) if x[0] == "X13"], "repo: the host step and the CSP word for word pass")
    put(os.path.join(repo, "site", "astro.config.mjs"), cfg + csp.replace("connect-src 'none'", "connect-src 'self'"))
    ok(any("Content-Security" in x[3] for x in ec.check_repo(repo, ()) if x[0] == "X13"), "repo: a changed CSP fails")
    put(os.path.join(repo, "site", "astro.config.mjs"), cfg + csp)
    for bad in ("const p = '/widgets/other/x.js';", "const r = await fetch(u);", "const m = await import(u);", "eval(s);",
                "const p = '/widgets/' + id + '/widget.js';"):
        put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), HOST_OK + bad + "\n")
        ok(any(x[0] == "X13" for x in ec.check_repo(repo, ())), f"repo: host step line fails ({bad})")
    put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), "// a comment names /widgets/<id>/ and fetch\n" + HOST_OK)
    ok(not [x for x in ec.check_repo(repo, ()) if x[0] == "X13"], "repo: a whole-line comment in the host step is not scanned")
    put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), HOST_OK + "const q = 1; // /widgets/x/\n")
    ok(any(x[0] == "X13" for x in ec.check_repo(repo, ())), "repo: a trailing comment is scanned with its line")
    put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), "import { readFileSync } from 'node:fs';\n" + HOST_OK)
    ok(not [x for x in ec.check_repo(repo, ()) if x[0] == "X13"], "repo: a static import of node:fs passes in the host step")
    put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), "const u = 'https://example.org/a.js';\n")
    ok(any(x[0] == "X7" for x in ec.check_repo(repo, ())), "repo: a URL in the host step is X7")
    # the review's host rule: one script, its src the widget.js template, the one link shape
    for name, text in (("a second script", HOST_OK + "const t = { tagName: 'script' };\n"),
                       ("another file name", HOST_OK.replace("/widget.js`", "/other.js`")),
                       ("a second src", HOST_OK + "const u = { src: x };\n"),
                       ("a wider link shape", HOST_OK.replace("([\\w-]+)", "(.+)"))):
        put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), text)
        ok(any(x[0] == "X13" for x in ec.check_repo(repo, ())), f"repo: host step with {name} fails")
    real = os.path.join(HERE, "..", "workspace", "export-repo", "site", "src", "rehype-widgets.mjs")
    if os.path.isfile(real):
        put(os.path.join(repo, "site", "src", "rehype-widgets.mjs"), open(real, encoding="utf-8").read())
        ok(not [x for x in ec.check_repo(repo, ()) if x[0] == "X13"], "repo: the prepared host step passes")


HOST_OK = ("const LINK = /^\\/widgets\\/([\\w-]+)\\/widget\\.js$/;\n"
           "const s = { tagName: 'script', properties: { type: 'module', src: `${prefix}/widgets/${id}/widget.js` } };\n")


def build_tests(tmp):
    docs = os.path.join(tmp, "docs")
    block = ("```widget\nid: rng-demo\nwidget: rng\nillustrates: a seed and its draws\n"
             "caption: Type a seed and a range, and the table lists the seed after each draw.\nfallback: text\n```\n")
    put(os.path.join(docs, "w.md"), f"# W\n\nIntro sentence.\n\n## Try it\n\n{block}\nAfter.\n")
    man = os.path.join(tmp, "m.txt")
    put(man, MANIFEST)
    old_docs = eb.DOCS
    eb.DOCS = docs
    out = os.path.join(eb.WS, "export-selftest-widgets")
    al = ec.load_allow(os.path.join(HERE, "..", "docs", "export", "allow-hex.txt"))
    ec.set_allow(al)
    try:
        pages = eb.build(out, man, tmp, "2026-11-17", al, run_illus=False)
        md = open(os.path.join(out, "site", "src", "content", "docs", "g", "w.md"), encoding="utf-8").read()
        wf = os.path.join(out, "site", "public", "widgets", "rng-demo")
        ok(sorted(os.listdir(wf)) == ["widget.js", "widget.json", "widget.list.json"], f"build: the folder has the three files ({sorted(os.listdir(wf))})")
        ok("| Draw | Operation | Result | low after | high after |" in md and "| 1 | Range(n) | 87 |" in md, "build: the text fallback table is in the page")
        ok("[Try it: change the inputs (needs JavaScript)](/widgets/rng-demo/widget.js)" in md, "build: the Try it link is root-absolute")
        ok("Computed by our model of the rule" in md and "Type a seed and a range" in md, "build: the caption and the model sentence follow")
        ok("```" not in md, "build: no fence reaches the cut")
        for name in ("widget.js", "widget.json"):
            ok(open(os.path.join(wf, name), "rb").read() == open(os.path.join(REAL, name), "rb").read(), f"build: {name} is byte-equal to the source")
        lst = json.load(open(os.path.join(wf, "widget.list.json")))
        ok(lst["marker"] == M and set(lst["files"]) == {"widget.js", "widget.json"}, "build: the list names the marker and the files")
        f, _ = ec.check_cut(out, man, ())
        ok(f == [], f"build: the cut passes export_check ({f[:3]})")
        rep = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
        ok("widget" not in rep.lower() or "| widget |" not in rep, "build: no widget drop in the report")
        # drops
        def drop(blockline, why):
            put(os.path.join(docs, "w.md"), f"# W\n\nIntro.\n\n## Try it\n\n{blockline}\nAfter.\n")
            eb.build(out, man, tmp, "2026-11-17", al, run_illus=False)
            m2 = open(os.path.join(out, "site", "src", "content", "docs", "g", "w.md"), encoding="utf-8").read()
            r2 = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
            ok("widgets/" not in m2 and "```" not in m2 and "widget" in r2.lower(),
               f"build: {why}: the block is dropped with a report line")
            ok(not os.path.isdir(os.path.join(out, "site", "public", "widgets")) or not os.listdir(os.path.join(out, "site", "public", "widgets")),
               f"build: {why}: no folder is left")
        drop(block.replace("widget: rng", "widget: nosuch"), "a missing widget")
        drop(block.replace("id: rng-demo\n", ""), "a block without an id")
        drop(block.replace("fallback: text", "fallback: no-such-illustration"), "a fallback illustration not in the cut")
        drop(block.replace("widget: rng", "widget: ../rng"), "a path in the widget name")
        put(os.path.join(docs, "w.md"), f"# W\n\nIntro.\n\n## Try it\n\n{block}\n{block}\nAfter.\n")
        eb.build(out, man, tmp, "2026-11-17", al, run_illus=False)
        m4 = open(os.path.join(out, "site", "src", "content", "docs", "g", "w.md"), encoding="utf-8").read()
        ok(m4.count("/widgets/rng-demo/widget.js") == 1 and "id used twice" in open(os.path.join(out, "report.txt")).read(),
           "build: the second block of one id is dropped, the first stays")
        # a source that fails X13 is dropped by the builder (a scratch reviewed tree)
        src = os.path.join(tmp, "src")
        shutil.copytree(os.path.join(HERE, "widgets"), src)
        put(os.path.join(src, "rng", "widget.js"), open(os.path.join(src, "rng", "widget.js")).read() + "\nfetch(u);\n")
        eb.WIDGETS_SRC, ec.WIDGETS_SRC = src, src
        put(os.path.join(docs, "w.md"), f"# W\n\nIntro.\n\n## Try it\n\n{block}\nAfter.\n")
        eb.build(out, man, tmp, "2026-11-17", al, run_illus=False)
        r3 = open(os.path.join(out, "report.txt"), encoding="utf-8").read()
        ok("X13" in r3 and not os.path.isdir(os.path.join(out, "site", "public", "widgets", "rng-demo")),
           "build: a widget.js that fails X13 is dropped, its folder removed, the report names X13")
        eb.WIDGETS_SRC, ec.WIDGETS_SRC = os.path.join(HERE, "widgets"), os.path.join(HERE, "widgets")
        # an illustration fallback: the picture is copied to the widget's folder, the page carries the image
        il = os.path.join(out, "site", "public", "illustrations", "ill1")
        put(os.path.join(il, "a.gif"), "GIF89a " + ec.MARKER, "w")
        b2 = block.replace("fallback: text", "fallback: ill1")
        pg = eb.Page({"path": "w.md", "route": "g/w", "order": 1})
        shutil.rmtree(os.path.join(out, "site", "public", "widgets"), ignore_errors=True)
        res = eb.widget_block(pg, {"lines": b2.strip().split("\n")}, out, al, "H")
        txt = "\n".join(l for b in res for l in b["lines"])
        ok("![Widget fallback: rng-demo](/widgets/rng-demo/fallback.gif)" in txt, "build: an illustration fallback is an image with a root-absolute target")
        ok(os.path.isfile(os.path.join(out, "site", "public", "widgets", "rng-demo", "fallback.gif")), "build: the picture is copied as fallback.gif")
        ok(not ec.check_page(txt, "g/w.md", "g/w", 0, set(), (), None, {("rng-demo", "fallback.gif"), ("rng-demo", "widget.js")}),
           "build: the page text of an illustration fallback passes the check")
    finally:
        eb.DOCS = old_docs
        eb.WIDGETS_SRC, ec.WIDGETS_SRC = os.path.join(HERE, "widgets"), os.path.join(HERE, "widgets")


def main():
    tmp = tempfile.mkdtemp(prefix="widget-export-test-")
    try:
        js_tests()
        json_tests()
        folder_tests(tmp)
        cut_tests(tmp)
        repo_tests(tmp)
        build_tests(os.path.join(tmp, "b"))
    finally:
        ec.set_allow(None)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(os.path.join(eb.WS, "export-selftest-widgets"), ignore_errors=True)
    print(f"TEST export_widgets: {checks} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
