// Runs one widget's compute on every case of its fixture and prints the outputs as JSON.
// Usage: node run_fixture.mjs <widget.mjs> <widget.json> <fixture.json>
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [mod, dataPath, fixPath] = process.argv.slice(2);
const widget = await import(pathToFileURL(mod).href);
const data = JSON.parse(readFileSync(dataPath, "utf8"));
const fixture = JSON.parse(readFileSync(fixPath, "utf8"));
const out = fixture.cases.map((c) => widget.compute(c.inputs, data));
process.stdout.write(JSON.stringify(out));
