// widget-only/1
// Formula stepper. A small tool of our own that restates the evaluator of the calc page: the bytes are run one by one
// over a stack of 32-bit values; a variable byte reads a number now, a constant byte pushes one, an operator pops its
// operands (the right one first) and pushes its result, the condition byte keeps its then-value when the condition is
// not 0, and every value is read or called at its own byte, so both branches of a condition are read.
// The bytes and numbers are typed here as toy bytes and numbers; every value shown is computed by our model, not
// observed in the game.

const NAME = "calc";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

// One or two hex digits per token; returns { octets, fault } with fault 0 none, 1 a bad token, 2 too many bytes
function parseBytes(text, maxBytes) {
  const octets = [];
  let token = [];
  let fault = 0;
  const flush = () => {
    if (token.length === 0) return;
    if (token.length > 2) fault = 1;
    else octets.push(token.reduce((acc, v) => acc * 16 + v, 0));
    token = [];
  };
  for (const raw of text) {
    const v = parseInt(raw, 16);
    if (raw === " " || raw === ",") flush();
    else if (isNaN(v)) {
      fault = 1;
      token = [];
    } else token.push(v);
  }
  flush();
  if (fault === 0 && octets.length > maxBytes) fault = 2;
  return { octets: fault === 0 ? octets : [], fault };
}

// the size of the operand a byte takes: 0 for none
function operandSize(op) {
  if (op === 1 || op === 4 || op === 7) return 1;
  if (op === 5 || op === 8) return 2;
  if (op === 6 || op === 9) return 4;
  return 0;
}

// the bytes that end an evaluation: 0, 2, 3 and everything above 0x16
function ends(op) {
  return op === 0 || op === 2 || op === 3 || op > 0x16;
}

// true when an operand starts inside the bytes and runs past the last one, on the path the evaluation takes
function cutOperand(octets) {
  let p = 0;
  while (p < octets.length) {
    const op = octets.at(p);
    p += 1;
    const n = operandSize(op);
    if (n > 0) {
      if (p < octets.length && p + n > octets.length) return true;
      p += n;
    } else if (ends(op)) {
      return false;
    }
  }
  return false;
}

// the operand read little-endian: signed for the constants and for the two wider variable indexes, unsigned for the narrow ones
function operand(octets, p, op) {
  const n = operandSize(op);
  let v = 0;
  for (let i = n - 1; i >= 0; i--) v = v * 256 + octets.at(p + 1 + i);
  if (op === 4 || op === 1) return v;
  const range = 2 ** (8 * n);
  return v >= range / 2 ? v - range : v;
}

function power(bs, exp) {
  if (exp <= 0) return 1;
  let result = 1;
  let b = bs | 0;
  let e = exp;
  while (e > 0) {
    if (e % 2 === 1) result = Math.imul(result, b);
    b = Math.imul(b, b);
    e = Math.trunc(e / 2);
  }
  return result;
}

// The pure part: no page access. inputs: { formula, lvl, par1, par2 }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const lvl = toInt(inputs.lvl, lim.lvl.min, lim.lvl.max, lim.lvl.default);
  const par1 = toInt(inputs.par1, lim.par1.min, lim.par1.max, lim.par1.default);
  const par2 = toInt(inputs.par2, lim.par2.min, lim.par2.max, lim.par2.default);
  const parsed = parseBytes(String(inputs.formula), rule.maxBytes);
  const out = { fault: parsed.fault, tally: 0, rows: [], how: "empty", result: 0 };
  if (parsed.fault !== 0) return out;
  const octets = parsed.octets;
  if (cutOperand(octets)) {
    out.fault = 3;
    return out;
  }
  out.tally = octets.length;
  let stack = [];
  const push = (v) => {
    if (stack.length < rule.stackLimit) stack.push(v | 0);
  };
  const pop = () => (stack.length > 0 ? stack.pop() : 0);
  let p = 0;
  let how = "past";
  let result = 0;
  if (octets.length === 0) return out;
  while (p < octets.length) {
    const op = octets.at(p);
    const n = operandSize(op);
    const row = { pos: p, op, arg: null, size: 1 + n, octs: octets.slice(p, p + 1 + n), stack: [] };
    if (n > 0 && p + 1 >= octets.length) {
      row.stack = [];
      out.rows.push(row);
      how = "cut";
      break;
    }
    if (n > 0) row.arg = operand(octets, p, op);
    p += 1 + n;
    if (op === 4 || op === 5 || op === 6) {
      push(row.arg === 0 ? lvl : row.arg === 1 ? par1 : row.arg === 2 ? par2 : 0);
    } else if (op === 7 || op === 8 || op === 9) {
      push(row.arg);
    } else if (op === 1) {
      push(0);
    } else if (op >= 0x0a && op <= 0x14) {
      const right = pop();
      const left = pop();
      let r = 0;
      if (op === 0x0a) r = left < right ? 1 : 0;
      else if (op === 0x0b) r = left > right ? 1 : 0;
      else if (op === 0x0c) r = left <= right ? 1 : 0;
      else if (op === 0x0d) r = left >= right ? 1 : 0;
      else if (op === 0x0e) r = left === right ? 1 : 0;
      else if (op === 0x0f) r = left !== right ? 1 : 0;
      else if (op === 0x10) r = (left + right) | 0;
      else if (op === 0x11) r = (left - right) | 0;
      else if (op === 0x12) r = Math.imul(left, right);
      else if (op === 0x13) {
        if (left === rule.intMin && right === -1) {
          row.stack = stack.slice();
          out.rows.push(row);
          how = "trap";
          result = 0;
          break;
        }
        r = right === 0 ? 0 : Math.trunc(left / right) | 0;
      } else r = power(left, right);
      push(r);
    } else if (op === 0x15) {
      push(-pop());
    } else if (op === 0x16) {
      const other = pop();
      const then = pop();
      const cond = pop();
      push(cond !== 0 ? then : other);
    } else {
      result = pop();
      row.stack = stack.slice();
      out.rows.push(row);
      how = "end";
      break;
    }
    row.stack = stack.slice();
    out.rows.push(row);
  }
  out.how = how;
  out.result = how === "end" ? result : 0;
  return out;
}

function hex(v) {
  return v.toString(16).toUpperCase().padStart(2, "0");
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

function field(form, id, label, spec, value) {
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), label);
  lab.htmlFor = id;
  const inp = document.createElement("input");
  inp.type = "number";
  inp.id = id;
  inp.min = String(spec.min);
  inp.max = String(spec.max);
  inp.step = "1";
  inp.value = String(value);
  wrap.append(lab, inp);
  form.append(wrap);
  return inp;
}

// what a row says, from the opcode, its operand and the stack after it
function describe(row, data) {
  const w = data.text.word;
  const op = row.op;
  const peek = row.stack.length > 0 ? row.stack.at(-1) : 0;
  if (op === 4 || op === 5 || op === 6) {
    return w.readVar + " " + row.arg + (row.arg > 2 || row.arg < 0 ? " (" + w.readVarEmpty + ")" : "") + " -> " + peek;
  }
  if (op === 7 || op === 8 || op === 9) return w.push + " " + row.arg;
  if (op === 1) return w.invoke + " " + row.arg + ": " + w.invokeNone;
  if (op >= 0x0a && op <= 0x14) {
    const o = data.ops.items.at(op - 0x0a);
    return o.text + " (" + o.sym + "): " + w.binary + " " + peek;
  }
  if (op === 0x15) return w.negate + " -> " + peek;
  if (op === 0x16) {
    const o = data.ops.items.at(12);
    return o.text + " -> " + peek;
  }
  return w.halt;
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const lim = data.inputs;
  const codeWrap = make(document.createElement("div"), undefined, "widget-field");
  const codeLab = make(document.createElement("label"), t.formulaLabel);
  codeLab.htmlFor = uid + "-code";
  const codeIn = document.createElement("input");
  codeIn.type = "text";
  codeIn.id = uid + "-code";
  codeIn.value = lim.formula.default;
  codeWrap.append(codeLab, codeIn);
  form.append(codeWrap);
  const ins = {
    lvl: field(form, uid + "-lvl", t.caps.lvl, lim.lvl, lim.lvl.default),
    par1: field(form, uid + "-par1", t.caps.par1, lim.par1, lim.par1.default),
    par2: field(form, uid + "-par2", t.caps.par2, lim.par2, lim.par2.default),
  };
  const all = [codeIn, ins.lvl, ins.par1, ins.par2];
  const presetWrap = make(document.createElement("div"), undefined, "widget-field");
  const presetLab = make(document.createElement("label"), t.presetLabel);
  presetLab.htmlFor = uid + "-preset";
  const preset = document.createElement("select");
  preset.id = uid + "-preset";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t.presetNone;
  preset.append(none);
  data.presets.items.forEach((p, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = p.name;
    preset.append(o);
  });
  presetWrap.append(presetLab, preset);
  form.append(presetWrap);
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, live, note);
  element.replaceChildren(root);

  function render() {
    const o = compute({ formula: codeIn.value, lvl: ins.lvl.value, par1: ins.par1.value, par2: ins.par2.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    o.rows.forEach((r, i) => {
      const tr = document.createElement("tr");
      const bytes = r.octs.map((v) => hex(v)).join(" ");
      const what = o.how === "cut" && i === o.rows.length - 1 ? t.word.cut : o.how === "trap" && i === o.rows.length - 1 ? t.word.trap : describe(r, data);
      tr.append(td(String(i + 1)), td(bytes), td(what), td(r.stack.join(" ")));
      body.append(tr);
    });
    table.append(thead, body);
    if (o.fault === 1) live.textContent = t.errBad + " " + codeIn.value;
    else if (o.fault === 2) live.textContent = t.errLong;
    else if (o.fault === 3) live.textContent = t.errCut;
    else if (o.how === "empty") live.textContent = t.word.blank;
    else if (o.how === "past") live.textContent = t.result + ": 0 (" + t.word.past + ").";
    else if (o.how === "cut") live.textContent = t.result + ": 0 (" + t.word.cut + ").";
    else if (o.how === "trap") live.textContent = t.word.trap + ".";
    else live.textContent = t.result + ": " + o.result + ".";
  }

  for (const el of all) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      codeIn.value = p.formula;
      render();
    }
  });
  render();
}

if (typeof document !== "undefined") {
  for (const el of document.querySelectorAll('figure[data-widget-name="' + NAME + '"]')) {
    if (!el.dataset.mounted) {
      el.dataset.mounted = "1";
      mount(el, JSON.parse(el.dataset.widgetData));
    }
  }
}
