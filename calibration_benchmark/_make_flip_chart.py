"""Render the 'flipped verdict' chart for the LinkedIn post.
On ops_05 (the SaaStr launch-plan prompt), all three model judges rank Opus 4.8
higher; the human alone ranks 4.7 higher. Reuses the house style from
_make_charts.py. Writes ../assets/flip_ops05.png.
"""

import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
ASSETS = HERE.parent / "assets"
ASSETS.mkdir(exist_ok=True)
KEY = json.loads((HERE / "_judge2_key.json").read_text(encoding="utf-8"))
AXES = ["correctness", "uncertainty_handling", "assumption_discipline"]
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]
PID = "ops_05"

# ---- load the four judges (same plumbing as _make_charts.py) ----
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

JUDGE_ORDER = ["Claude", "GPT-5.4", "Kimi", "Human"]
judges = {k: judges[k] for k in JUDGE_ORDER if k in judges}

def total(jd, model):
    return sum(jd.get((PID, model), {}).get(a, 0) for a in AXES)

v48 = [total(judges[j], MODELS[0]) for j in judges]
v47 = [total(judges[j], MODELS[1]) for j in judges]
print("ops_05 4.8:", dict(zip(judges, v48)))
print("ops_05 4.7:", dict(zip(judges, v47)))

# ---- style (matches _make_charts.py) ----
C48, C47 = "#2563eb", "#94a3b8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#cbd5e1", "axes.grid": True,
                     "grid.color": "#eef2f7", "grid.linewidth": 1})
FOOT = "Calibration benchmark · prompt ops_05 (v2 launch plan) · 4 blind judges (3 model lineages + 1 human)"

fig, ax = plt.subplots(figsize=(9.2, 5.6))
x = np.arange(len(judges)); w = 0.38

# highlight the human group to mark the flip
ax.axvspan(x[-1] - 0.5, x[-1] + 0.5, color="#fef3c7", alpha=0.55, zorder=0)

b1 = ax.bar(x - w/2, v48, w, color=C48, label="Opus 4.8", zorder=3)
b2 = ax.bar(x + w/2, v47, w, color=C47, label="Opus 4.7", zorder=3)

ax.set_xticks(x); ax.set_xticklabels(list(judges.keys()), fontsize=12)
ax.set_ylim(0, 7.6); ax.set_ylabel("Total score / 6", fontsize=11.5, color="#475569")
ax.set_yticks(range(0, 7))
ax.tick_params(length=0); ax.set_axisbelow(True)
ax.set_title("Same prompt, flipped verdict", fontsize=17, fontweight="bold", pad=18, loc="left")
ax.text(0, 1.02, "“Launch v2 by SaaStr” plan · total / 6. Three model judges rank 4.8 higher — the human alone ranks 4.7 higher.",
        transform=ax.transAxes, fontsize=10.5, color="#64748b", va="bottom")
ax.legend([b1, b2], ["Opus 4.8", "Opus 4.7"], frameon=False, fontsize=12, loc="upper left",
          ncol=2, bbox_to_anchor=(0.0, 1.0))

def labels(bars):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 0.09, f"{h:.0f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color="#334155")
labels(b1); labels(b2)

# annotate the flip
ax.annotate("the flip", xy=(x[-1] + w/2, 5.1), xytext=(x[-1] - 1.05, 6.7),
            fontsize=11.5, fontweight="bold", color="#b45309",
            arrowprops=dict(arrowstyle="->", color="#b45309", lw=1.6))

fig.text(0.5, 0.015, FOOT, ha="center", fontsize=9, color="#94a3b8")
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(ASSETS / "flip_ops05.png", dpi=200, facecolor="white")
plt.close(fig)
print("wrote flip_ops05.png")
