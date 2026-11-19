// widget-only/1
// Path search on a toy room. A small tool of our own that restates the search of the path page (types 0 and 16's
// shared walk, run here as type 0): an iterative-deepening depth-first walk under a bound on the cost, a cell store
// kept across the passes, and a fixed fan of turns that is the tie-break. A pass walks from the start; at each node
// it tries the first direction of the fan that is free and within the bound; when its turns run out it goes back. If
// no pass reaches the target the bound grows by 5 and it walks again over the same store, while it stays below the
// caller's last bound. The returned list keeps a node when its step differs from the kept step after it.
// Every value shown is computed by our model in this page, from the cells and numbers set here; none is observed in
// the game. The room, its wall and the numbers offered are illustrative.

const NAME = "path";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function pair(p) {
  return p[0] + "," + p[1];
}

function octile(a, b) {
  const dx = Math.abs(a[0] - b[0]);
  const dy = Math.abs(a[1] - b[1]);
  return 2 * Math.max(dx, dy) + Math.min(dx, dy);
}

// The cell of a direction pair: each term is cut by the other (a term below half the other keeps only its low bit,
// or -1 when negative), clamped to -2..2, and the cell is 5 dx + dy + 12.
function dirCell(a, b) {
  let dx = b[0] - a[0];
  let dy = b[1] - a[1];
  if (Math.abs(dx) >= 2 * Math.abs(dy)) {
    dy = dy < 0 ? -1 : dy & 1;
  } else if (Math.abs(dy) >= 2 * Math.abs(dx)) {
    dx = dx < 0 ? -1 : dx & 1;
  }
  dx = Math.min(2, Math.max(-2, dx));
  dy = Math.min(2, Math.max(-2, dy));
  return 5 * dx + dy + 12;
}

// The first direction of a cell (the octant): a term whose double is at most the other term's size is dropped, and the
// step with the signs left is the direction; the cell with both terms 0 gives the rule's own value.
function octantOf(c, steps, zero) {
  let dx = Math.floor(c / 5) - 2;
  let dy = (c % 5) - 2;
  if (2 * Math.abs(dy) <= Math.abs(dx)) dy = 0;
  else if (2 * Math.abs(dx) <= Math.abs(dy)) dx = 0;
  const want = [Math.sign(dx), Math.sign(dy)];
  if (want[0] === 0 && want[1] === 0) return zero;
  return steps.findIndex((s) => s.at(0) === want[0] && s.at(1) === want[1]);
}

// A wall coordinate: optional sign and decimal digits only, so "3.0" or "1e0" is not a wall.
function wallNum(text) {
  const t = text.trim();
  const from = t.startsWith("+") || t.startsWith("-") ? 1 : 0;
  if (t.length === from) return NaN;
  for (let i = from; i < t.length; i++) {
    if (!"0123456789".includes(t.at(i))) return NaN;
  }
  return Number(t);
}

// The pure part: no page access. inputs: { walls, sx, sy, tx, ty, b1c }; walls is a list of "x,y" texts.
export function compute(inputs, data) {
  const lim = data.inputs;
  const gw = data.grid.wide;
  const gh = data.grid.high;
  const sx = toInt(inputs.sx, lim.sx.min, lim.sx.max, lim.sx.default);
  const sy = toInt(inputs.sy, lim.sy.min, lim.sy.max, lim.sy.default);
  const tx = toInt(inputs.tx, lim.tx.min, lim.tx.max, lim.tx.default);
  const ty = toInt(inputs.ty, lim.ty.min, lim.ty.max, lim.ty.default);
  const b1c = toInt(inputs.b1c, lim.b1c.min, lim.b1c.max, lim.b1c.default);
  const start = [sx, sy];
  const target = [tx, ty];
  const wallSet = new Set();
  for (const w of inputs.walls) {
    const parts = String(w).split(",");
    if (parts.length !== 2) continue;
    const x = wallNum(parts.at(0));
    const y = wallNum(parts.at(1));
    if (!Number.isInteger(x) || !Number.isInteger(y)) continue;
    if (x >= 0 && x < gw && y >= 0 && y < gh) wallSet.add(x + "," + y);
  }
  wallSet.delete(pair(start));
  wallSet.delete(pair(target));
  const walls = [...wallSet].sort();
  const steps = data.tables.step.items.map((r) => r.items);
  const fan = data.tables.fan.items.map((r) => r.items);
  const dirOf = (a, b) => octantOf(dirCell(a, b), steps, data.octant.zero);
  const turnAt = (row, ent) => {
    const e = fan.at(row).at(ent);
    return e === undefined ? 0 : e;
  };
  const blocked = (x, y) => x < 0 || x >= gw || y < 0 || y >= gh || wallSet.has(x + "," + y);

  const memo = new Map();
  const h0 = octile(start, target);
  let limit = h0;
  const last = Math.max(h0, b1c);
  const passes = [];
  let finalNode = null;
  for (;;) {
    const root = { pos: start, g: 0, h: h0, cost: h0, way: dirOf(start, target) & 7, row: 0, ent: 0, n: -3, up: null, down: null };
    let node = root;
    let count = 1;
    let tries = 0;
    let descent = null;
    let found = null;
    let ending = "";
    while (ending === "") {
      if (node.pos[0] === tx && node.pos[1] === ty) {
        ending = "target";
        found = node;
        break;
      }
      tries += 1;
      if (tries > data.limits.tryMax) {
        ending = "tries";
        break;
      }
      const sd = steps.at(node.way);
      const nx = node.pos[0] + sd.at(0);
      const ny = node.pos[1] + sd.at(1);
      const key = nx + "," + ny;
      const c = memo.has(key) ? memo.get(key) : 0;
      let skip = false;
      if (c === 0 && blocked(nx, ny)) {
        memo.set(key, 1);
        skip = true;
      } else {
        const g = node.g + (nx !== node.pos[0] && ny !== node.pos[1] ? 3 : 2);
        if (c !== 0 && c < g) {
          skip = true;
        } else {
          memo.set(key, g);
          const h = octile([nx, ny], target);
          const f = g + h;
          if (f > limit) {
            skip = true;
          } else {
            let kid = node.down;
            if (kid === null) {
              if (count === data.limits.nodeMax) {
                ending = "nodes";
                break;
              }
              count += 1;
              kid = { up: node, down: null };
              node.down = kid;
            }
            kid.h = h;
            kid.g = g;
            kid.cost = f;
            kid.n = 0;
            kid.row = (dirOf([nx, ny], target) - node.way) & 7;
            kid.ent = 0;
            kid.way = (node.way + turnAt(kid.row, 0)) & 7;
            kid.pos = [nx, ny];
            node = kid;
            continue;
          }
        }
      }
      if (skip) {
        if (descent === null) {
          const chain = [];
          for (let q = node; q !== null; q = q.up) chain.push(pair(q.pos));
          descent = chain.reverse().join(" ");
        }
        // Advance: the node's next turn while it has one under 4 tries, then back to the nodes above.
        if (node.n < 4) {
          node.ent += 1;
          node.way = (node.way + turnAt(node.row, node.ent)) & 7;
        }
        node.n += 1;
        if (node.n === 5) {
          let gone = false;
          for (;;) {
            if (node.up === null) {
              gone = true;
              break;
            }
            node = node.up;
            node.ent += 1;
            node.way = (node.way + turnAt(node.row, node.ent)) & 7;
            node.n += 1;
            if (node.n !== 5) break;
          }
          if (gone) {
            ending = "exhausted";
            break;
          }
        }
      }
    }
    const rows = [];
    for (let y = 0; y < gh; y++) {
      const cells = [];
      for (let x = 0; x < gw; x++) {
        const v = memo.has(x + "," + y) ? memo.get(x + "," + y) : 0;
        cells.push(v === 0 ? "." : v === 1 ? "#" : String(v));
      }
      rows.push(cells.join(" "));
    }
    let chainText = "";
    if (found !== null) {
      const chain = [];
      for (let q = found; q !== null; q = q.up) chain.push(pair(q.pos));
      chainText = chain.reverse().join(" ");
    }
    passes.push({
      limit, tries, nodes: count, ending, descent: descent === null ? "" : descent, chain: chainText, grid: rows,
    });
    limit += data.limits.step;
    if (found !== null) {
      finalNode = found;
      break;
    }
    if (ending === "nodes") break;
    if (!(limit < last)) break;
  }
  // The returned list: from the end back, a node is kept when its step differs from the kept step after it.
  let route = [];
  if (finalNode !== null) {
    const buf = [];
    let prev = [-2, -2];
    let q = finalNode;
    while (q !== null && buf.length < 78) {
      if (q.up !== null) {
        const sd = [q.pos[0] - q.up.pos[0], q.pos[1] - q.up.pos[1]];
        if (sd[0] !== prev[0] || sd[1] !== prev[1]) {
          buf.push(pair(q.pos));
          prev = sd;
        }
      }
      q = q.up;
    }
    if (buf.length >= 2 && buf.length <= 77) route = buf.reverse();
  }
  return {
    start: pair(start), target: pair(target), b1c, walls, h0, last,
    reached: finalNode !== null, passes, route: route.join(" "),
  };
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

export function mount(element, data) {
  const t = data.text;
  const gw = data.grid.wide;
  const gh = data.grid.high;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const wallSet = new Set(data.walls.items);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const li = data.inputs;
  const sxIn = field(form, uid + "-sx", t.sxLabel, li.sx, li.sx.default);
  const syIn = field(form, uid + "-sy", t.syLabel, li.sy, li.sy.default);
  const txIn = field(form, uid + "-tx", t.txLabel, li.tx, li.tx.default);
  const tyIn = field(form, uid + "-ty", t.tyLabel, li.ty, li.ty.default);
  const bIn = field(form, uid + "-b1c", t.bLabel, li.b1c, li.b1c.default);
  const passIn = field(form, uid + "-pass", t.passLabel, li.pass, li.pass.default);
  const clearBtn = make(document.createElement("button"), t.clearLabel);
  clearBtn.type = "button";
  const resetBtn = make(document.createElement("button"), t.resetLabel);
  resetBtn.type = "button";
  form.append(clearBtn, resetBtn);
  const gridTable = make(document.createElement("table"), undefined, "widget-table widget-grid");
  gridTable.setAttribute("aria-label", t.gridLabel);
  const key = make(document.createElement("p"), t.keyLine, "widget-note");
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, gridTable, key, table, live, note);
  element.replaceChildren(root);

  let out = null;
  const buttons = [];
  for (let y = 0; y < gh; y++) {
    const tr = document.createElement("tr");
    for (let x = 0; x < gw; x++) {
      const cell = document.createElement("td");
      const b = document.createElement("button");
      b.type = "button";
      b.addEventListener("click", () => {
        const k = x + "," + y;
        if (wallSet.has(k)) wallSet.delete(k);
        else wallSet.add(k);
        solve(true);
      });
      cell.append(b);
      tr.append(cell);
      buttons.push(b);
    }
    gridTable.append(tr);
  }

  function draw() {
    const pn = toInt(passIn.value, 1, out.passes.length, out.passes.length);
    const shown = out.passes.at(pn - 1);
    const cells = shown.grid.map((r) => r.split(" "));
    const chain = new Set(shown.chain === "" ? [] : shown.chain.split(" "));
    const corners = new Set(pn === out.passes.length && out.route !== "" ? out.route.split(" ") : []);
    for (let y = 0; y < gh; y++) {
      for (let x = 0; x < gw; x++) {
        const k = x + "," + y;
        const b = buttons.at(y * gw + x);
        const isWall = out.walls.includes(k);
        let mark = cells.at(y).at(x);
        if (isWall) mark = "#";
        if (chain.has(k)) mark = "*";
        if (corners.has(k)) mark = "o";
        if (k === out.start) mark = "S";
        if (k === out.target) mark = "T";
        b.textContent = mark;
        b.setAttribute("aria-label", k + " " + (isWall ? t.wallWord : t.freeWord) + " " + mark);
        b.setAttribute("aria-pressed", isWall ? "true" : "false");
      }
    }
  }

  function solve(resetPass) {
    out = compute({
      walls: [...wallSet], sx: sxIn.value, sy: syIn.value, tx: txIn.value, ty: tyIn.value, b1c: bIn.value,
    }, data);
    if (resetPass) passIn.value = String(out.passes.length);
    passIn.max = String(out.passes.length);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    out.passes.forEach((p, i) => {
      const tr = document.createElement("tr");
      const at = t.endings.items.indexOf(p.ending);
      tr.append(td(String(i + 1)), td(String(p.limit)), td(String(p.tries)), td(String(p.nodes)),
        td(at < 0 ? p.ending : t.endNames.items.at(at)));
      body.append(tr);
    });
    table.append(thead, body);
    live.textContent = t.liveHead + " " + out.start + ", " + t.liveTarget + " " + out.target + ", " + t.liveH0 + " " +
      out.h0 + ": " + out.passes.length + " " + t.livePass + ", " +
      (out.reached ? t.liveReached : t.liveNot) + "; " + t.liveRoute + ": " +
      (out.route === "" ? t.liveNone : out.route) + ".";
    draw();
  }

  for (const el of [sxIn, syIn, txIn, tyIn, bIn]) el.addEventListener("input", () => solve(true));
  passIn.addEventListener("input", draw);
  clearBtn.addEventListener("click", () => {
    wallSet.clear();
    solve(true);
  });
  resetBtn.addEventListener("click", () => {
    wallSet.clear();
    for (const w of data.walls.items) wallSet.add(w);
    solve(true);
  });
  solve(true);
}

if (typeof document !== "undefined") {
  for (const el of document.querySelectorAll('figure[data-widget-name="' + NAME + '"]')) {
    if (!el.dataset.mounted) {
      el.dataset.mounted = "1";
      mount(el, JSON.parse(el.dataset.widgetData));
    }
  }
}
