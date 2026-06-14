"""Re-render ONLY correctness_by_judge.png with the updated title, without
touching the other (avatar-composited) chart PNGs. Reuses the loader + style
from _make_charts.py. Run after editing the title string there.
"""

import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ASSETS = HERE.parent / "assets"
KEY = json.loads((HERE / "_judge2_key.json").read_text(encoding="utf-8"))
AXES = ["correctness", "uncertainty_handling", "assumption_discipline"]
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))

judges = {}
claude = {}
for row in csv.DictReader((HERE / "results_scored.csv").open(encoding="utf-8")):
    claude[(row["prompt_id"], row["model"])] = {a: int(row[a]) for a in AXES}
judges["Claude"] = claude
for f in sorted(HERE.glob("_perplexity_*_scores.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    nm = d.get("_meta", {}).get("judge", f.stem).split()[0]
    jd = {}
    for pid, slots in d.items():
        if pid.startswith("_"): continue
        for s in ("A", "B"):
            jd[(pid, KEY[pid][s])] = {a: int(slots[s][a]) for a in AXES}
    judges[nm] = jd
hd = {}
for row in csv.DictReader((HERE / "_judge2_scoresheet.csv").open(encoding="utf-8")):
    vals = {a: int(row[a]) for a in AXES if row.get(a, "").strip() != ""}
    if vals: hd[(row["prompt_id"], KEY[row["prompt_id"]][row["slot"]])] = vals
judges["Human"] = hd
judges = {k: judges[k] for k in ["Claude", "GPT-5.4", "Kimi", "Human"] if k in judges}

C48, C47 = "#2563eb", "#94a3b8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#cbd5e1", "axes.grid": True,
                     "grid.color": "#eef2f7", "grid.linewidth": 1})
FOOT = "Calibration benchmark · 15 prompts × 2 models · 4 blind judges (3 model lineages + 1 human)"

c47 = [sum(judges[j].get((pid, MODELS[1]), {}).get("correctness", 0)
           for p in PROMPTS for pid in [p["id"]]) for j in judges]
print("4.7 correctness by judge:", dict(zip(judges, c47)))

fig, ax = plt.subplots(figsize=(10.2, 5.4))
bars = ax.bar(list(judges.keys()), c47, color=["#94a3b8", "#94a3b8", "#94a3b8", "#2563eb"])
ax.set_title("Same answers, a split on what 'correct' means", fontsize=17, fontweight="bold", pad=18, loc="left")
ax.text(0, 1.02, "Opus 4.7 correctness / 30, by judge. Models scored confident invention as wrong; the human as miscalibrated.",
        transform=ax.transAxes, fontsize=9.5, color="#64748b", va="bottom")
ax.set_ylim(0, 33); ax.set_ylabel("4.7 correctness / 30", fontsize=11.5, color="#475569")
ax.tick_params(length=0); ax.set_axisbelow(True)
for b in bars:
    h = b.get_height()
    ax.text(b.get_x() + b.get_width()/2, h + 33*0.012, f"{h:.0f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold", color="#334155")
fig.text(0.5, 0.015, FOOT, ha="center", fontsize=9, color="#94a3b8")
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(ASSETS / "correctness_by_judge.png", dpi=200, facecolor="white")
plt.close(fig)
print("wrote correctness_by_judge.png")
