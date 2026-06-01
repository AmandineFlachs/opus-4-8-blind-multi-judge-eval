"""Inter-rater reliability across N judges.

Judges auto-discovered:
  - "Claude (blind)"   <- committed scores in results_scored.csv
  - every _perplexity_*_scores.json (model judges; display name from _meta.judge)
  - "Human (author)" <- _judge2_scoresheet.csv, if filled
All model/human judges are un-blinded via _judge2_key.json (A/B -> model).

Outputs: per-judge totals, pairwise agreement (exact % + mean weighted kappa),
a consensus (median) score, and the genuinely contested items (range >= 2).
"""

import csv
import json
import statistics
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).parent
KEY = json.loads((HERE / "_judge2_key.json").read_text(encoding="utf-8"))
AXES = ["correctness", "uncertainty_handling", "assumption_discipline"]
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]
PROMPTS = [p["id"] for p in json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))]
ITEMS = [(pid, m) for pid in PROMPTS for m in MODELS]

judges = {}  # name -> {(pid, model): {axis: int}}

# Judge: Claude, from committed CSV
claude = {}
for row in csv.DictReader((HERE / "results_scored.csv").open(encoding="utf-8")):
    claude[(row["prompt_id"], row["model"])] = {a: int(row[a]) for a in AXES}
judges["Claude (blind)"] = claude

# Judges: model judges from _perplexity_*_scores.json
for f in sorted(HERE.glob("_perplexity_*_scores.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    name = data.get("_meta", {}).get("judge", f.stem)
    jd = {}
    for pid, slots in data.items():
        if pid.startswith("_"):
            continue
        for slot in ("A", "B"):
            jd[(pid, KEY[pid][slot])] = {a: int(slots[slot][a]) for a in AXES}
    judges[name] = jd

# Judge: human scoresheet, if filled
sheet = HERE / "_judge2_scoresheet.csv"
if sheet.exists():
    hd = {}
    for row in csv.DictReader(sheet.open(encoding="utf-8")):
        vals = {a: int(row[a]) for a in AXES if row.get(a, "").strip() != ""}
        if vals:  # keep partial rows; missing axes simply absent
            hd[(row["prompt_id"], KEY[row["prompt_id"]][row["slot"]])] = vals
    if hd:
        judges["Human (author)"] = hd


def quad_weighted_kappa(pairs):
    cats = [0, 1, 2]
    n = len(pairs)
    if n == 0:
        return None
    O = {(i, j): 0 for i in cats for j in cats}
    r1 = {c: 0 for c in cats}
    r2 = {c: 0 for c in cats}
    for a, b in pairs:
        O[(a, b)] += 1; r1[a] += 1; r2[b] += 1
    num = den = 0.0
    for i in cats:
        for j in cats:
            w = (i - j) ** 2
            num += w * O[(i, j)]
            den += w * (r1[i] * r2[j] / n)
    return None if den == 0 else 1 - num / den


def totals(jd):
    out = {m: {a: 0 for a in AXES} for m in MODELS}
    cnt = {m: {a: 0 for a in AXES} for m in MODELS}
    for (pid, m), sc in jd.items():
        for a in AXES:
            if a in sc:
                out[m][a] += sc[a]
                cnt[m][a] += 1
    return out, cnt


print("#" * 64)
print(f"Judges: {list(judges)}")
print("\n--- Per-judge totals (out of 30/axis; only over items that judge scored) ---")
for name, jd in judges.items():
    t, cnt = totals(jd)
    print(f"\n{name}:")
    for m in MODELS:
        s = t[m]
        flags = " ".join(f"{a}:n={cnt[m][a]}" for a in AXES if cnt[m][a] < len(PROMPTS))
        note = f"   [partial: {flags}]" if flags else ""
        print(f"  {m.replace('claude-opus-',''):4s} C={s['correctness']:2d} "
              f"U={s['uncertainty_handling']:2d} A={s['assumption_discipline']:2d}  "
              f"total={sum(s.values())}/90{note}")

print("\n--- Pairwise agreement ---")
for n1, n2 in combinations(judges, 2):
    j1, j2 = judges[n1], judges[n2]
    common = [it for it in ITEMS if it in j1 and it in j2]
    if not common:
        continue
    print(f"\n{n1}  vs  {n2}   (n={len(common)} items)")
    exact = cells = 0
    kappas = []
    for axis in AXES:
        pairs = [(j1[it][axis], j2[it][axis]) for it in common if axis in j1[it] and axis in j2[it]]
        ag = sum(1 for a, b in pairs if a == b)
        w1 = sum(1 for a, b in pairs if abs(a - b) <= 1)
        k = quad_weighted_kappa(pairs)
        if k is not None:
            kappas.append(k)
        kstr = f"{k:.3f}" if k is not None else "n/a"
        print(f"  {axis:24s} exact={ag}/{len(pairs)} ({100*ag/len(pairs):3.0f}%)  "
              f"within1={100*w1/len(pairs):3.0f}%  wkappa={kstr}")
        exact += ag; cells += len(pairs)
    mk = f"{statistics.mean(kappas):.3f}" if kappas else "n/a"
    print(f"  -> overall exact {exact}/{cells} ({100*exact/cells:.0f}%), mean wkappa {mk}")

# Consensus (median across all judges that scored each cell)
print("\n--- Consensus (median across all judges) ---")
consensus = {m: {a: 0.0 for a in AXES} for m in MODELS}
for (pid, m) in ITEMS:
    for a in AXES:
        vals = [jd[(pid, m)][a] for jd in judges.values() if (pid, m) in jd and a in jd[(pid, m)]]
        if vals:
            consensus[m][a] += statistics.median(vals)
for m in MODELS:
    s = consensus[m]
    print(f"  {m.replace('claude-opus-',''):4s} C={s['correctness']:.1f} "
          f"U={s['uncertainty_handling']:.1f} A={s['assumption_discipline']:.1f}  "
          f"total={sum(s.values()):.1f}/90")

# Genuinely contested items: range >= 2 on any axis across judges
print("\n--- Contested items (judges span >= 2 pts on an axis) ---")
any_c = False
for (pid, m) in ITEMS:
    for a in AXES:
        vals = [jd[(pid, m)][a] for jd in judges.values() if (pid, m) in jd and a in jd[(pid, m)]]
        if vals and max(vals) - min(vals) >= 2:
            any_c = True
            detail = ", ".join(f"{nm.split()[0]}={jd[(pid,m)][a]}" for nm, jd in judges.items() if (pid, m) in jd and a in jd[(pid,m)])
            print(f"  {pid:10s} {m.replace('claude-opus-',''):4s} {a}: {detail}")
if not any_c:
    print("  (none — no axis where judges span 2 full points)")
