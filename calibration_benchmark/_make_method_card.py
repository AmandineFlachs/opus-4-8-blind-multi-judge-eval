"""Render the method-summary card (1200x800) for social.
Left: the 4 method steps. Right: a framed screenshot of the blind-scoring tool.
Bottom: the consensus verdict. Matches the palette/typography of _make_charts.py.

Requires ../assets/_scoring_shot.png (a screenshot of blind_scoring.html). Regenerate it via:
  chrome --headless=new --force-device-scale-factor=2 --window-size=1280,820 \
         --screenshot=<abs>/assets/_scoring_shot.png file:///<abs>/calibration_benchmark/blind_scoring.html
Writes ../assets/method_card.png.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).parent
ASSETS = HERE.parent / "assets"
ASSETS.mkdir(exist_ok=True)
SHOT = ASSETS / "_scoring_shot.png"

# palette (from _make_charts.py)
BLUE   = "#2563eb"
INK    = "#1e293b"
SLATE  = "#475569"
MUTE   = "#64748b"
BANNER = "#eff6ff"
BANED  = "#bfdbfe"
FRAME  = "#cbd5e1"

plt.rcParams.update({"font.family": "DejaVu Sans"})

# 1200x800 at dpi=100
FW, FH = 1200, 800
fig = plt.figure(figsize=(FW / 100, FH / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

# ---- header ----
ax.text(0.038, 0.955, "How the benchmark was built",
        fontsize=25, fontweight="bold", color=INK, va="center")
ax.text(0.039, 0.905,
        "Is Opus 4.8 more honest than 4.7? Four method choices that make it more than vibes.",
        fontsize=13, color=MUTE, va="center")

# ---- left: four numbered steps ----
steps = [
    ("1", "Adversarial prompts",
     "15 prompts, 3 categories. Each hides a way to look\nhelpful while wrong; ground truth fixed before scoring."),
    ("2", "Clean-room runs",
     "Stripped every account-context channel from the harness,\nafter catching a real company-name leak in run one."),
    ("3", "Blind A / B",
     "No judge sees which model is which. Responses shown as\nA / B in random order, unmasked only after scoring."),
    ("4", "Cross-lineage panel",
     "Four blind judges: Claude, GPT-5.4, Kimi + a human.\nThree lineages, so “biased toward Claude” can’t hold."),
]
col_x = 0.045
top, bottom = 0.82, 0.315
ys = [top - i * (top - bottom) / (len(steps) - 1) for i in range(len(steps))]
for (num, head, body), y in zip(steps, ys):
    ax.scatter([col_x], [y], s=470, color=BLUE, zorder=4)
    ax.text(col_x, y, num, ha="center", va="center", color="white",
            fontsize=13, fontweight="bold", zorder=5)
    ax.text(col_x + 0.026, y + 0.004, head, ha="left", va="center",
            fontsize=14, fontweight="bold", color=INK)
    ax.text(col_x + 0.026, y - 0.048, body, ha="left", va="top",
            fontsize=9.5, color=SLATE, linespacing=1.45)

# vertical divider between steps and screenshot
ax.plot([0.395, 0.395], [0.20, 0.85], color="#e2e8f0", lw=1.4)

# ---- right: framed screenshot of the live scoring tool (enlarged) ----
ax.text(0.415, 0.86, "STEP 3, LIVE", fontsize=10.5, fontweight="bold",
        color=BLUE, va="center", ha="left")
img = mpimg.imread(SHOT)
ih, iw = img.shape[:2]
panel_x, panel_w = 0.413, 0.549
panel_top = 0.835
panel_h = (panel_w * FW) * (ih / iw) / FH   # preserve aspect in figure coords
panel_y = panel_top - panel_h
ax_img = fig.add_axes([panel_x, panel_y, panel_w, panel_h])
ax_img.imshow(img)
ax_img.set_xticks([]); ax_img.set_yticks([])
for s in ax_img.spines.values():
    s.set_edgecolor(FRAME); s.set_linewidth(1.5)
ax.text(panel_x, panel_y - 0.032,
        "Blind, randomized Response A / B. No model names.",
        fontsize=10.5, color=MUTE, va="center", ha="left", style="italic")

# ---- verdict banner (shorter, squarer corners) ----
left, right = 0.038, 0.962
by0, bbh = 0.05, 0.086
banner = FancyBboxPatch((left, by0), right - left, bbh,
                        boxstyle="round,pad=0.004,rounding_size=0.006",
                        facecolor=BANNER, edgecolor=BANED, linewidth=1.6)
ax.add_patch(banner)
ax.text(left + 0.028, by0 + bbh * 0.70, "THE VERDICT",
        fontsize=10.5, fontweight="bold", color=BLUE, va="center", ha="left")
ax.text(left + 0.028, by0 + bbh * 0.30,
        "All four blind judges rank Opus 4.8 > 4.7",
        fontsize=14, fontweight="bold", color=INK, va="center", ha="left")
ax.text(right - 0.028, by0 + bbh * 0.66, "82.5  vs  46.5",
        fontsize=18, fontweight="bold", color=BLUE, va="center", ha="right")
ax.text(right - 0.028, by0 + bbh * 0.27, "consensus / 90   ·   +36 gap",
        fontsize=11, color=MUTE, va="center", ha="right")

# ---- footer ----
ax.text(0.5, 0.018,
        "Calibration benchmark · 15 prompts × 2 models · 4 blind judges (3 model lineages + 1 human)",
        ha="center", fontsize=9, color="#94a3b8")

fig.savefig(ASSETS / "method_card.png", facecolor="white")
plt.close(fig)
print("wrote method_card.png")
