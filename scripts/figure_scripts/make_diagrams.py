"""Two schematic figures for the thesis: conceptual framework and DMF 1.0. Usage: python make_diagrams.py <out_dir>"""
import os, sys
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTD = sys.argv[1]; os.makedirs(OUTD, exist_ok=True)
INK, INK2, MUTED, LINE, FILL, FILL2 = "#22201c", "#57524a", "#8a8375", "#8a8375", "#f4f1e8", "#ffffff"
mpl.rcParams.update({"font.family": ["Liberation Serif", "DejaVu Sans"], "savefig.dpi": 300, "figure.facecolor": "white"})

def box(ax, x, y, w, h, title, lines=(), fc=FILL2, tsize=8.8, lsize=7.8, dy=0.05):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.012", fc=fc, ec=LINE, lw=0.9, zorder=2))
    n = len(lines)
    ty = y + h / 2 + dy * n / 2
    ax.text(x + w / 2, ty, title, ha="center", va="center", fontsize=tsize, color=INK, fontweight="bold", zorder=3)
    for i, l in enumerate(lines):
        ax.text(x + w / 2, ty - dy * (i + 1), l, ha="center", va="center", fontsize=lsize, color=INK2, zorder=3)

def arrow(ax, p0, p1, head=True):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>" if head else "-", mutation_scale=9, lw=1.1, color=INK2,
                                 zorder=1, shrinkA=0 if not head else 2, shrinkB=0 if not head else 2))

def line(ax, pts):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=INK2, lw=1.1, zorder=1, solid_capstyle="round")

# ------------------------------------------------------------------ conceptual framework
fig, ax = plt.subplots(figsize=(6.3, 4.0)); ax.set_xlim(-0.01, 1.01); ax.set_ylim(0, 1); ax.axis("off")
C1, C2, C3, BW = 0.0, 0.335, 0.635, 0.265
for (y, t, l) in [(0.60, "Relational aspects", ["staff and service"]), (0.40, "Cultural aspects", ["culture, dining, bath"]),
                  (0.20, "Physical and functional", ["room, location, value"])]:
    box(ax, C1, y, BW, 0.17, t, l, tsize=8.4)
box(ax, C2, 0.20, 0.23, 0.57, "Online review", ["narrated experience:", "what guests choose", "to write after the stay"], fc=FILL)
for (y, t, l) in [(0.60, "Memory", ["what is narrated: salience,", "memory language"]),
                  (0.40, "Satisfaction", ["star rating,", "sentence sentiment"]),
                  (0.20, "Behavioral intention", ["recommendation,", "return intent"])]:
    box(ax, C3, y, BW, 0.17, t, l)
for y in (0.685, 0.485, 0.285):
    arrow(ax, (C1 + BW, y), (C2, y)); arrow(ax, (C2 + 0.23, y), (C3, y))
ax.text((C1 + BW + C2) / 2, 0.715, "H1", ha="center", fontsize=8.8, color=INK, fontweight="bold")
box(ax, 0.20, 0.885, 0.50, 0.10, "Accommodation type: Ryokan vs. Hotel", tsize=8.6)
arrow(ax, (0.45, 0.885), (0.45, 0.772))
ax.text(0.465, 0.825, "RQ1", ha="left", va="center", fontsize=8.8, color=INK, fontweight="bold")
line(ax, [(0.70, 0.935), (0.945, 0.935), (0.945, 0.51)]); arrow(ax, (0.945, 0.51), (C3 + BW, 0.51))
ax.text(0.955, 0.80, "H2", ha="left", va="center", fontsize=8.8, color=INK, fontweight="bold")
box(ax, 0.20, 0.015, 0.50, 0.10, "Season: peak vs. off-peak months", tsize=8.6)
line(ax, [(0.70, 0.065), (0.985, 0.065), (0.985, 0.46)]); arrow(ax, (0.985, 0.46), (C3 + BW, 0.46))
ax.text(0.84, 0.095, "H3: type × season", ha="center", va="center", fontsize=8.8, color=INK, fontweight="bold")
fig.savefig(os.path.join(OUTD, "figA_conceptual_framework.png"), bbox_inches="tight", pad_inches=0.06); plt.close(fig)

# ------------------------------------------------------------------ DMF 1.0
fig, ax = plt.subplots(figsize=(6.3, 4.0)); ax.set_xlim(-0.01, 1.01); ax.set_ylim(0, 1); ax.axis("off")
mods = [("M1  Scope", ["comparison groups, period,", "selection rule; the property", "is the unit of comparison"]),
        ("M2  Collect", ["public review text, rating", "and date; no personal data;", "collection log"]),
        ("M3  Prepare", ["audit duplicates and", "language; split sentences;", "remove property names"]),
        ("M4  Discover", ["topic model (k by coherence,", "stability); aspect dictionary;", "distinctive terms"]),
        ("M5  Measure", ["sentence sentiment with", "validity check; memory and", "intention proxies"]),
        ("M6  Infer and report", ["property-level exact tests;", "reward–penalty and seasonal", "models; reporting checklist"])]
W, H, GX = 0.30, 0.235, 0.05
xs = [0.0, W + GX, 2 * (W + GX)]
R1, R2, R3 = 0.755, 0.435, 0.03
for i, (t, l) in enumerate(mods):
    r, c = divmod(i, 3); y = R1 if r == 0 else R2
    box(ax, xs[c], y, W, H, t, l, lsize=7.6, tsize=9, dy=0.048)
    if c < 2: arrow(ax, (xs[c] + W, y + H / 2), (xs[c + 1], y + H / 2))
mid = (R1 + R2 + H) / 2
line(ax, [(xs[2] + W / 2, R1), (xs[2] + W / 2, mid), (xs[0] + W / 2, mid)]); arrow(ax, (xs[0] + W / 2, mid), (xs[0] + W / 2, R2 + H))
outs = [("Experience profile", ["what guests narrate and", "how they evaluate it"]),
        ("Reward–penalty map", ["basic factors and delighters,", "by accommodation type"]),
        ("Seasonal stability", ["peak-season effect and", "type × season difference"])]
OH = 0.20
for c, (t, l) in enumerate(outs):
    box(ax, xs[c], R3, W, OH, t, l, fc=FILL, lsize=7.6, tsize=9, dy=0.048)
bar = (R2 + R3 + OH) / 2 + 0.02
line(ax, [(xs[2] + W / 2, R2), (xs[2] + W / 2, bar), (xs[0] + W / 2, bar)])
for c in range(3):
    arrow(ax, (xs[c] + W / 2, bar), (xs[c] + W / 2, R3 + OH))
ax.text((xs[0] + W / 2 + xs[1] + W / 2) / 2, bar - 0.045, "OUTPUTS", ha="center", va="center", fontsize=7.6, color=MUTED, fontweight="bold")
fig.savefig(os.path.join(OUTD, "figB_dmf.png"), bbox_inches="tight", pad_inches=0.06); plt.close(fig)
print("diagrams written")
