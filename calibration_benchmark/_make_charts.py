"""Render publication-quality charts for the shareable report + social.
Reloads all four blind judges, computes consensus + pairwise weighted kappa,
and writes PNGs to ../assets/.
"""

import csv, json, statistics
from itertools import combinations
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
AXIS_LBL = {"correctness": "Correctness", "uncertainty_handling": "Uncertainty\nhandling",
            "assumption_discipline": "Assumption\ndiscipline"}
MODELS = ["claude-opus-4-8", "claude-opus-4-7"]
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
PID2CAT = {p["id"]: p["category"] for p in PROMPTS}
CATS = ["code_and_tool_traps", "ambiguous_operator", "conflicting_spec"]
CAT_LBL = {"code_and_tool_traps": "Code & tool\ntraps", "ambiguous_operator": "Ambiguous\noperator",
           "conflicting_spec": "Conflicting\nspec"}
ITEMS = [(p["id"], m) for p in PROMPTS for m in MODELS]

# ---- load judges ----
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

def jtotal(jd, model):
    return sum(jd.get((pid, model), {}).get(a, 0) for p in PROMPTS for pid in [p["id"]] for a in AXES)

def consensus_cell(pid, m, a):
    vals = [jd[(pid, m)][a] for jd in judges.values() if (pid, m) in jd and a in jd[(pid, m)]]
    return statistics.median(vals) if vals else 0

def quad_kappa(pairs):
    cats=[0,1,2]; n=len(pairs)
    if n==0: return None
    O={(i,j):0 for i in cats for j in cats}; r1={c:0 for c in cats}; r2={c:0 for c in cats}
    for a,b in pairs: O[(a,b)]+=1; r1[a]+=1; r2[b]+=1
    num=den=0.0
    for i in cats:
        for j in cats:
            w=(i-j)**2; num+=w*O[(i,j)]; den+=w*(r1[i]*r2[j]/n)
    return None if den==0 else 1-num/den

# ---- style ----
C48, C47 = "#2563eb", "#94a3b8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#cbd5e1", "axes.grid": True,
                     "grid.color": "#eef2f7", "grid.linewidth": 1})
FOOT = "Calibration benchmark · 15 prompts × 2 models · 4 blind judges (3 model lineages + 1 human)"

def style(ax, title, sub, ymax, ylabel):
    ax.set_title(title, fontsize=17, fontweight="bold", pad=18, loc="left")
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10.5, color="#64748b", va="bottom")
    ax.set_ylim(0, ymax); ax.set_ylabel(ylabel, fontsize=11.5, color="#475569")
    ax.tick_params(length=0)
    ax.set_axisbelow(True)

def legend(ax):
    ax.legend(["Opus 4.8", "Opus 4.7"], frameon=False, fontsize=12, loc="upper right", ncol=2)

def labels(ax, bars, fmt="{:.0f}"):
    for b in bars:
        h=b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+ (ax.get_ylim()[1]*0.012), fmt.format(h),
                ha="center", va="bottom", fontsize=11, fontweight="bold", color="#334155")

def footer(fig):
    fig.text(0.5, 0.015, FOOT, ha="center", fontsize=9, color="#94a3b8")

def grouped(fname, groups, v48, v47, title, sub, ymax, ylabel, fmt="{:.0f}"):
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    x=np.arange(len(groups)); w=0.38
    b1=ax.bar(x-w/2, v48, w, color=C48, label="Opus 4.8")
    b2=ax.bar(x+w/2, v47, w, color=C47, label="Opus 4.7")
    ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=12)
    style(ax,title,sub,ymax,ylabel); legend(ax); labels(ax,b1,fmt); labels(ax,b2,fmt)
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(ASSETS/fname, dpi=200, facecolor="white"); plt.close(fig)
    print("wrote", fname)

# 1. Gap by judge (+ consensus)
jt48=[jtotal(judges[j],MODELS[0]) for j in judges]; jt47=[jtotal(judges[j],MODELS[1]) for j in judges]
cons48=sum(consensus_cell(pid,MODELS[0],a) for p in PROMPTS for pid in [p["id"]] for a in AXES)
cons47=sum(consensus_cell(pid,MODELS[1],a) for p in PROMPTS for pid in [p["id"]] for a in AXES)
grouped("gap_by_judge.png", list(judges.keys())+["Consensus\n(median)"],
        jt48+[cons48], jt47+[cons47],
        "Four blind judges, one verdict: Opus 4.8 > 4.7",
        "Total score / 90. Every judge — 3 model lineages + 1 human — ranks 4.8 higher.",
        100, "Score / 90")

# 2. By axis (consensus)
ax48=[sum(consensus_cell(pid,MODELS[0],a) for p in PROMPTS for pid in [p["id"]]) for a in AXES]
ax47=[sum(consensus_cell(pid,MODELS[1],a) for p in PROMPTS for pid in [p["id"]]) for a in AXES]
grouped("by_axis.png", [AXIS_LBL[a] for a in AXES], ax48, ax47,
        "The gap is calibration, not raw correctness",
        "Consensus score per axis / 30. The split widens on knowing what it doesn't know.",
        33, "Consensus score / 30", fmt="{:.1f}")

# 3. By category (consensus)
cc48=[sum(consensus_cell(pid,MODELS[0],a) for p in PROMPTS for pid in [p["id"]] if PID2CAT[pid]==c for a in AXES) for c in CATS]
cc47=[sum(consensus_cell(pid,MODELS[1],a) for p in PROMPTS for pid in [p["id"]] if PID2CAT[pid]==c for a in AXES) for c in CATS]
grouped("by_category.png", [CAT_LBL[c] for c in CATS], cc48, cc47,
        "4.7 struggles most when it must volunteer uncertainty",
        "Consensus score per category / 30. Biggest gap: open-ended asks with missing inputs.",
        37, "Consensus score / 30", fmt="{:.1f}")

# 4. Pairwise weighted-kappa heatmap
names=list(judges.keys()); n=len(names)
K=np.ones((n,n))
for (i,a),(j,b) in [((i,a),(j,b)) for i,a in enumerate(names) for j,b in enumerate(names)]:
    if i==j: continue
    common=[it for it in ITEMS if it in judges[a] and it in judges[b]]
    ks=[]
    for ax_ in AXES:
        pairs=[(judges[a][it][ax_],judges[b][it][ax_]) for it in common if ax_ in judges[a][it] and ax_ in judges[b][it]]
        k=quad_kappa(pairs)
        if k is not None: ks.append(k)
    K[i,j]=sum(ks)/len(ks) if ks else np.nan
fig,ax=plt.subplots(figsize=(8.2,7.0))
fig.subplots_adjust(left=0.16, right=0.88, top=0.80, bottom=0.20)
im=ax.imshow(K, cmap="YlGnBu", vmin=0, vmax=1)
ax.set_xticks(range(n)); ax.set_yticks(range(n)); ax.set_xticklabels(names); ax.set_yticklabels(names)
ax.tick_params(length=0); ax.grid(False)
for i in range(n):
    for j in range(n):
        v=K[i,j]; ax.text(j,i, "1.00" if i==j else f"{v:.2f}", ha="center", va="center",
                          color="white" if v>0.55 else "#1e293b", fontsize=14, fontweight="bold")
fig.text(0.16, 0.93, "Inter-rater agreement (quadratic weighted κ)", fontsize=16.5, fontweight="bold")
fig.text(0.16, 0.875, "Model↔model agreement is substantial (0.59–0.72); the human is the lenient outlier.",
         fontsize=10.5, color="#64748b")
fig.text(0.16, 0.845, "Low human↔model κ is partly the base-rate paradox — within-1 agreement stays 93–100%.",
         fontsize=10.5, color="#64748b")
cb=fig.colorbar(im, fraction=0.046, pad=0.04); cb.outline.set_visible(False)
footer(fig)
fig.savefig(ASSETS/"kappa_heatmap.png", dpi=200, facecolor="white"); plt.close(fig)
print("wrote kappa_heatmap.png")

# 5. 4.7 correctness by judge (the nuance)
c47=[jtotal_axis if False else sum(judges[j].get((pid,MODELS[1]),{}).get("correctness",0) for p in PROMPTS for pid in [p["id"]]) for j in judges]
fig,ax=plt.subplots(figsize=(9.2,5.4))
bars=ax.bar(list(judges.keys()), c47, color=["#94a3b8","#94a3b8","#94a3b8","#2563eb"])
style(ax,"Models penalize confident confabulation; the human doesn't",
      "Opus 4.7 correctness / 30, by judge. Humans read polished-but-invented answers as 'correct'.",
      33,"4.7 correctness / 30")
labels(ax,bars)
footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
fig.savefig(ASSETS/"correctness_by_judge.png", dpi=200, facecolor="white"); plt.close(fig)
print("wrote correctness_by_judge.png")

print("\nNumbers used:")
print(" per-judge 4.8:", dict(zip(judges, jt48)), "consensus", cons48)
print(" per-judge 4.7:", dict(zip(judges, jt47)), "consensus", cons47)
print(" axis 4.8/4.7:", list(zip(AXES, ax48, ax47)))
print(" cat  4.8/4.7:", list(zip(CATS, cc48, cc47)))
print(" 4.7 correctness by judge:", dict(zip(judges, c47)))
