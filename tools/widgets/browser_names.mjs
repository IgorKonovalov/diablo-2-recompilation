// Writes the two name lists the publish check's X13 reads (ADR-0037; the lane/x11w review's allowlist ruling):
//   browser-globals.txt  every name a bare identifier can reach in a page: the window object's own names and those of
//                        its prototype chain (fetch, open, name, location, Image, ...)
//   browser-members.txt  every property name of the platform: the globals above, and the own names of every global
//                        constructor, its prototype chain and its prototype's chain, and of every global object
// A widget may write a name of either list only where the check's reviewed allowlist admits it; any other name is
// the widget's own (a variable, or a key of its own data), which no browser object answers.
// Usage: node tools/widgets/browser_names.mjs <path to playwright's index.mjs> (the export site's own Playwright)
// Run in Chromium; the names only other engines expose are added by hand below.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const OTHER_ENGINES_GLOBALS = ["InstallTrigger", "content", "dump", "external", "fullScreen", "home", "back", "forward",
  "mozInnerScreenX", "mozInnerScreenY", "netscape", "openDialog", "scrollMaxX", "scrollMaxY", "sidebar", "sizeToContent",
  "uneval", "updateCommands", "webkitURL", "webkitRequestFileSystem", "webkitResolveLocalFileSystemURL", "global",
  "require", "process", "module", "exports", "Buffer", "__dirname", "__filename", "Deno", "Bun"];
const OTHER_ENGINES_MEMBERS = ["ownerGlobal", "wrappedJSObject", "originalTarget", "explicitOriginalTarget", "toSource",
  "mozInputSource", "caller", "callee", "__noSuchMethod__", "watch", "unwatch"];

const { chromium } = await import(process.argv[2]);
const b = await chromium.launch();
const p = await b.newPage();
await p.setContent("<p>x</p>");
const [globals, members] = await p.evaluate(() => {
  const g = new Set(), m = new Set();
  const add = (set, o) => { for (let x = o; x; x = Object.getPrototypeOf(x)) for (const n of Object.getOwnPropertyNames(x)) set.add(n); };
  add(g, window);
  const get = (o, n) => { try { return o[n]; } catch { return undefined; } };
  for (const n of Object.getOwnPropertyNames(window)) {
    const v = get(window, n);
    if (typeof v === "function") { add(m, v); if (v.prototype) add(m, v.prototype); }
    else if (v && typeof v === "object") {
      add(m, v);
      for (const k of Object.getOwnPropertyNames(v)) { const w = get(v, k); if (w && typeof w === "object") add(m, w); }
    }
  }
  const ok = (n) => /^[A-Za-z_$][\w$]*$/.test(n);
  return [[...g].filter(ok), [...m].filter(ok)];
});
await b.close();
const here = dirname(fileURLToPath(import.meta.url));
const G = new Set([...globals, ...OTHER_ENGINES_GLOBALS]);
const M = new Set([...members, ...G, ...OTHER_ENGINES_MEMBERS]);
const write = (f, s) => writeFileSync(join(here, f), [...s].sort().join("\n") + "\n");
write("browser-globals.txt", G);
write("browser-members.txt", M);
console.log(`globals ${G.size}, members ${M.size}`);
