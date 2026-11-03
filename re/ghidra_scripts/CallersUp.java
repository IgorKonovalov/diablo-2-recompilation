// Reverse reachability: from each target function, walk its referrers upward (calls, jumps, and pointers in tables)
// until a declared root, and print, per target, every root reached with one shortest path (plan 0055 P1.2: which
// callers of a function run inside a server frame, which in the message drain, which elsewhere).
// Usage (headless): -postScript CallersUp.java <out-file> <max-depth> <token>...
//   root:0x<addr>=<LABEL>     a function at which the walk stops and the target is credited with LABEL
//   0x<addr>                  a target (the function containing addr)
// A reference from inside a function F makes F a referrer. A reference from data (a pointer in a table) is credited to
// the table: the walk steps back from the pointer in 4-byte steps (at most 0x1000 bytes) to the nearest address that is
// itself referenced, and the functions referencing that address are the referrers (edge kind `tbl@<base>`). A pointer
// whose table base has no reference, or no code reference, is a top `data@<addr>`. Functions with no referrer at all
// are tops `unref`. The walk is breadth first, so each root's path is a shortest one in edges.
// Output:
//   # target 0x<entry> <name>
//   root <LABEL> depth=<n> path=0x<root> -<kind>-> 0x<next> ... -<kind>-> 0x<target>  (each arrow: refers to)
//   top <kind> 0x<entry or addr> <name> depth=<n>
//   summary visited=<n> roots=<labels> tops=<n> truncated=<0|1>
// @category d2-recon

import java.io.PrintWriter;
import java.util.*;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class CallersUp extends GhidraScript {

	static final int MAX_VISIT = 20000;

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 3) throw new IllegalArgumentException("usage: CallersUp.java <out> <max-depth> <token>...");
		int maxDepth = Integer.parseInt(args[1]);
		Map<Long, String> roots = new LinkedHashMap<>();
		List<Long> targets = new ArrayList<>();
		for (int i = 2; i < args.length; i++) {
			String t = args[i];
			if (t.startsWith("root:")) {
				String[] kv = t.substring(5).split("=");
				roots.put(Long.decode(kv[0]), kv[1]);
			} else targets.add(Long.decode(t));
		}
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (long tAddr : targets) {
				Function tf = getFunctionContaining(toAddr(tAddr));
				if (tf == null) { w.printf("# target 0x%08X: no function%n", tAddr); continue; }
				long t0 = tf.getEntryPoint().getOffset();
				w.printf("# target 0x%08X %s%n", t0, tf.getName());
				Map<Long, Long> parent = new HashMap<>();
				Map<Long, String> how = new HashMap<>();
				Map<Long, Integer> depth = new HashMap<>();
				ArrayDeque<Long> q = new ArrayDeque<>();
				q.add(t0); depth.put(t0, 0);
				Map<String, Long> rootHit = new LinkedHashMap<>();
				List<String> tops = new ArrayList<>();
				boolean truncated = false;
				while (!q.isEmpty()) {
					long f = q.poll();
					int d = depth.get(f);
					if (roots.containsKey(f)) {
						String lab = roots.get(f);
						if (!rootHit.containsKey(lab)) rootHit.put(lab, f);
						continue;
					}
					if (d >= maxDepth) { truncated = true; continue; }
					if (depth.size() > MAX_VISIT) { truncated = true; break; }
					Function fn = getFunctionAt(toAddr(f));
					List<long[]> refs = new ArrayList<>();   // (referrer entry, kind code, extra)
					List<String> kinds = new ArrayList<>();
					for (Reference r : getReferencesTo(toAddr(f))) {
						Address from = r.getFromAddress();
						Function in = getFunctionContaining(from);
						if (in != null) {
							refs.add(new long[] { in.getEntryPoint().getOffset() });
							kinds.add(r.getReferenceType().isCall() ? "call" : (r.getReferenceType().isJump() ? "jmp" : "ref"));
							continue;
						}
						// a pointer in data: find the table base
						Address base = null;
						for (int back = 0; back <= 0x1000; back += 4) {
							Address b = from.subtract(back);
							boolean hasRef = false;
							for (Reference rb : getReferencesTo(b)) {
								if (getFunctionContaining(rb.getFromAddress()) != null) { hasRef = true; break; }
							}
							if (hasRef) { base = b; break; }
						}
						if (base == null) { tops.add(String.format("top data@0x%08X 0x%08X %s depth=%d", from.getOffset(), f, fn == null ? "?" : fn.getName(), d)); continue; }
						for (Reference rb : getReferencesTo(base)) {
							Function in2 = getFunctionContaining(rb.getFromAddress());
							if (in2 == null) continue;
							refs.add(new long[] { in2.getEntryPoint().getOffset() });
							kinds.add(String.format("tbl@0x%08X", base.getOffset()));
						}
					}
					if (refs.isEmpty() && tops.stream().noneMatch(s -> s.contains(String.format(" 0x%08X ", f)))) {
						tops.add(String.format("top unref 0x%08X %s depth=%d", f, fn == null ? "?" : fn.getName(), d));
					}
					for (int i = 0; i < refs.size(); i++) {
						long p = refs.get(i)[0];
						if (depth.containsKey(p)) continue;
						depth.put(p, d + 1); parent.put(p, f); how.put(p, kinds.get(i));
						q.add(p);
					}
				}
				for (Map.Entry<String, Long> e : rootHit.entrySet()) {
					StringBuilder sb = new StringBuilder();
					long x = e.getValue();
					while (true) {
						Function fx = getFunctionAt(toAddr(x));
						sb.append(String.format("0x%08X %s", x, fx == null ? "?" : fx.getName()));
						if (!parent.containsKey(x)) break;
						sb.append(" -" + how.get(x) + "-> ");
						x = parent.get(x);
					}
					w.printf("root %s depth=%d path=%s%n", e.getKey(), depth.get(e.getValue()), sb);
				}
				for (String s : tops) w.println(s);
				w.printf("summary visited=%d roots=%s tops=%d truncated=%d%n", depth.size(),
					String.join(",", rootHit.keySet()), tops.size(), truncated ? 1 : 0);
			}
		}
	}
}
