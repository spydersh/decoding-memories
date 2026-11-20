"""
Supplementary thesis figures (static, 300 dpi PNG): location and crowding, perceptual map,
aspects criticised together, narrative arc, complaint profile.
Usage: python make_figures2.py <dir with phase5 csv files> <out_dir>
Same style and colours as make_figures.py.
"""
import os, sys, numpy as np, pandas as pd, matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Circle
from matplotlib.colors import LinearSegmentedColormap
from statsmodels.stats.proportion import proportion_confint
D, OUTD = sys.argv[1], sys.argv[2]; os.makedirs(OUTD, exist_ok=True)
INK, INK2, MUTED, GRID, AXIS = "#22201c", "#57524a", "#8a8375", "#e9e4d8", "#bdb6a6"
COL = {"Ryokan": "#1f6fa8", "Hotel": "#d9452b", "Hybrid": "#c9a227"}
S = 0.87
mpl.rcParams.update({"font.family": ["Liberation Serif", "DejaVu Sans"], "font.size": 9.5, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "axes.labelsize": 9.5, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 300, "text.color": INK, "legend.frameon": False, "legend.fontsize": 9, "axes.titlesize": 10.5,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlecolor": INK, "axes.titlepad": 10})
def save(fig, name): fig.savefig(os.path.join(OUTD, name + ".png"), bbox_inches="tight", pad_inches=0.08); plt.close(fig)
short = lambda s: s.replace(" Kyoto", "").replace(" Ryokan", "").replace("The ", "")
rd = lambda f: pd.read_csv(os.path.join(D, f))

# ------------------------------------------------------------------ location map + crowding by property
L, Hs = rd("locations.csv"), rd("hotspots.csv")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2 * S, 5.9 * S), gridspec_kw={"width_ratios": [1.7, 1], "wspace": 0.55})
B = dict(w=135.7370, e=135.7940, s=34.9815, n=35.0265); kx = np.cos(np.radians(35)); KM = 110.95
X = lambda lon: (lon - B["w"]) * kx * KM; Y = lambda lat: (lat - B["s"]) * KM
a1.set_xlim(0, X(B["e"])); a1.set_ylim(0, Y(B["n"])); a1.set_aspect("equal"); a1.grid(False)
for sp in a1.spines.values(): sp.set_visible(True); sp.set_color(AXIS)
a1.set_xticks([]); a1.set_yticks([])
river = [(35.0265, 135.7712), (35.017, 135.7712), (35.010, 135.7712), (35.0037, 135.7716), (34.996, 135.769), (34.989, 135.7672), (34.9815, 135.766)]
a1.plot([X(p[1]) for p in river], [Y(p[0]) for p in river], color="#d9e6f2", lw=4, solid_capstyle="round", zorder=1)
a1.text(X(135.7712) - 0.08, Y(35.0248), "Kamo River", ha="right", va="center", fontsize=8.2, color=MUTED)
ins = Hs[(Hs.lon.between(B["w"], B["e"])) & (Hs.lat.between(B["s"], B["n"]))]
for _, h in ins[ins.area == "Gion / Kiyomizu"].iterrows():
    a1.add_patch(Circle((X(h.lon), Y(h.lat)), 1.0, fill=False, ls=(0, (3, 3)), lw=0.7, ec=MUTED, zorder=2, clip_on=True))
a1.scatter(X(ins.lon), Y(ins.lat), marker="D", s=22, color=MUTED, edgecolor="white", linewidth=0.8, zorder=3)
HO = {"Kiyomizu-dera": (0, -9, "center"), "Yasaka Shrine (Gion)": (-6, -7, "right"), "Heian Shrine": (6, 0, "left"), "Nishiki Market": (-6, 0, "right"), "Kyoto Station": (6, 0, "left"), "Nijo Castle": (0, -9, "center")}
for _, h in ins.iterrows():
    dx, dy, ha = HO.get(h["name"], (6, 0, "left"))
    a1.annotate(h["name"].replace(" (Gion)", ""), (X(h.lon), Y(h.lat)), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=8.2, color=INK2)
a1.scatter(X(L.lon), Y(L.lat), s=42, color=[COL[t] for t in L.type], edgecolor="white", linewidth=1, zorder=4)
PO = {"Muromachi Yutone": (-7, 0, "right"), "Ryokufuso": (-7, 0, "right"), "Nazuna Nijo-jo": (-6, 5, "right"), "Nazuna Gosho": (6, 4, "left"), "Park Hyatt Kyoto": (6, 3, "left"), "Four Seasons Kyoto": (-6, 3, "right"), "Hyatt Regency Kyoto": (6, -4, "left"), "Shiraume": (6, 5, "left")}
for _, p in L.iterrows():
    dx, dy, ha = PO.get(p.property, (6, 0, "left"))
    a1.annotate(short(p.property), (X(p.lon), Y(p.lat)), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=8.9, color=INK, fontweight="bold")
a1.plot([0.15, 1.15], [0.18, 0.18], color=INK, lw=1.5); a1.text(1.22, 0.18, "1 km", va="center", fontsize=7.3, color=INK2)
a1.text(X(B["e"]) - 0.1, Y(B["n"]) - 0.15, "N ↑", ha="right", va="top", fontsize=7.8, color=INK2)
a1.set_title("(a) Location in central Kyoto")
a1.legend(handles=[Line2D([], [], marker="o", ls="", color=COL[t], label=t, markersize=5) for t in ["Ryokan", "Hotel", "Hybrid"]] + [Line2D([], [], marker="D", ls="", color=MUTED, label="Busy sight", markersize=4)],
          loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=4, fontsize=7.6, handletextpad=0.2, columnspacing=0.9)
o = L.sort_values("crowd_exposed")
for i, r in enumerate(o.itertuples()):
    k = int(round(r.crowd_exposed * r.n / 100)); lo, hi = proportion_confint(k, r.n, method="wilson")
    a2.plot([lo * 100, hi * 100], [i, i], color=COL[r.type], lw=2, alpha=0.45, solid_capstyle="round")
    a2.text(hi * 100 + 0.4, i, f"{r.crowd_exposed:.1f}%", va="center", fontsize=8.6, color=INK2)
a2.scatter(o.crowd_exposed, range(len(o)), s=34, color=[COL[t] for t in o.type], edgecolor="white", linewidth=1, zorder=3)
a2.set_yticks(range(len(o))); a2.set_yticklabels([short(p) for p in o.property], fontsize=9)
a2.set_xlim(0, 13.5); a2.set_xticks([0, 4, 8, 12]); a2.set_xticklabels([f"{v}%" for v in [0, 4, 8, 12]]); a2.grid(axis="y", visible=False)
a2.set_xlabel("Reviews describing crowding\n(line: 95% interval)"); a2.set_title("(b) Crowding language")
save(fig, "figC_location_crowding")

# ------------------------------------------------------------------ perceptual map
P = rd("perceptual.csv")
fig, ax = plt.subplots(figsize=(7.0 * S, 4.2 * S))
ax.axhline(0, color=AXIS, lw=0.8); ax.axvline(0, color=AXIS, lw=0.8); ax.grid(False)
asp, prop = P[P.kind == "aspect"], P[P.kind == "property"]
ax.scatter(asp.dim1, asp.dim2, marker="D", s=26, color=MUTED, edgecolor="white", linewidth=0.8, zorder=3)
ax.scatter(prop.dim1, prop.dim2, s=42, color=[COL[t] for t in prop.type], edgecolor="white", linewidth=1, zorder=4)
OFF = {"Staff & service": (4, -9, "left"), "Park Hyatt Kyoto": (-4, 9, "right"), "Hyatt Regency Kyoto": (4, -9, "left"), "Value & price": (6, 4, "left"), "Room": (6, 3, "left"),
       "Culture": (-6, 0, "right"), "Dining": (6, 0, "left"), "Shiraume": (6, -8, "left"), "Nazuna Nijo-jo": (6, 0, "left"), "Nazuna Gosho": (-6, 0, "right"), "Four Seasons Kyoto": (6, 0, "left")}
for _, r in P.iterrows():
    dx, dy, ha = OFF.get(r.label, (6, 0, "left")); isA = r.kind == "aspect"
    ax.annotate(r.label if isA else short(r.label), (r.dim1, r.dim2), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=8, color=INK2 if isA else INK, fontstyle="italic" if isA else "normal", fontweight="normal" if isA else "bold")
ax.set_xlabel(f"Dimension 1 ({P.inertia1.iloc[0]:.1f}% of the variation)"); ax.set_ylabel(f"Dimension 2 ({P.inertia2.iloc[0]:.1f}%)")
ax.set_xlim(P.dim1.min() - 0.08, P.dim1.max() + 0.12); ax.set_ylim(P.dim2.min() - 0.05, P.dim2.max() + 0.05)
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=COL[t], label=t, markersize=5) for t in ["Ryokan", "Hotel", "Hybrid"]] + [Line2D([], [], marker="D", ls="", color=MUTED, label="Aspect", markersize=4)], loc="upper right", fontsize=7.8)
save(fig, "figD_perceptual_map")

# ------------------------------------------------------------------ aspects criticised together (hotels)
C = rd("cooccurrence.csv"); C = C[(C.type == "Hotel") & (C.polarity == "neg")]
ORD = ["Staff & service", "Room", "Dining", "Value & price", "Location", "Bath", "Culture"]
M = C.pivot(index="aspect_a", columns="aspect_b", values="lift").reindex(index=ORD, columns=ORD)
N = C.pivot(index="aspect_a", columns="aspect_b", values="n_both").reindex(index=ORD, columns=ORD)
fig, ax = plt.subplots(figsize=(6.2 * S, 4.0 * S)); ax.grid(False)
cm = LinearSegmentedColormap.from_list("o", ["#fbf1ee", COL["Hotel"]])
V = M.where(N >= 5); im = ax.imshow(V.values.astype(float), cmap=cm, vmin=1, vmax=np.nanmax(V.values.astype(float)))
for i in range(7):
    for j in range(7):
        if i == j: continue
        v = V.iat[i, j]; ax.text(j, i, "·" if pd.isna(v) else f"{v:.1f}", ha="center", va="center", fontsize=8.3, color=INK if (pd.isna(v) or v < 5.5) else "white")
ax.set_xticks(range(7)); ax.set_yticks(range(7)); ax.set_xticklabels([a.replace(" & ", " &\n") for a in ORD], fontsize=7.8); ax.set_yticklabels(ORD, fontsize=8.3)
ax.xaxis.tick_top(); ax.set_xticks(np.arange(-.5, 7, 1), minor=True); ax.set_yticks(np.arange(-.5, 7, 1), minor=True); ax.grid(which="minor", color="white", lw=2); ax.tick_params(which="minor", length=0)
for sp in ax.spines.values(): sp.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03); cb.set_label("Lift (1 = no association)", fontsize=8.8, color=INK2); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=8.3, length=0)
save(fig, "figE_cooccurrence")

# ------------------------------------------------------------------ narrative arc
Ar = rd("arc.csv")
fig, axs = plt.subplots(1, 2, figsize=(7.4 * S, 3.1 * S), gridspec_kw={"wspace": 0.42})
for ax, (m, ttl) in zip(axs, [("bert", "(a) Transformer classifier"), ("vader", "(b) Lexicon (VADER)")]):
    g = Ar[Ar.measure == m]
    for t in ["Ryokan", "Hybrid", "Hotel"]:
        s = g[g.type == t].sort_values("pos"); ax.plot(s.pos, s.sentiment, color=COL[t], lw=1.6, marker="o", ms=4, mec="white", mew=0.8)
        ax.text(5.12, s.sentiment.iloc[-1] + (0.012 if (m == "vader" and t == "Hybrid") else -0.006 if (m == "vader" and t == "Ryokan") else 0), t, color=COL[t], fontsize=8, va="center", fontweight="bold")
    ax.set_xticks([1, 2, 3, 4, 5]); ax.set_xticklabels(["Opening", "Early", "Middle", "Late", "Closing"], fontsize=8); ax.set_xlim(0.8, 5.9); ax.grid(axis="x", visible=False); ax.set_title(ttl)
axs[0].set_ylabel("Mean sentence sentiment"); axs[1].set_ylabel("Mean sentence sentiment (different scale)")
save(fig, "figF_narrative_arc")

# ------------------------------------------------------------------ complaint profile
Cp = rd("complaints.csv"); o = Cp[Cp.type == "Hotel"].sort_values("low_rated_share").aspect.tolist()
fig, ax = plt.subplots(figsize=(6.0 * S, 3.4 * S)); h = 0.36
for k, t in enumerate(["Ryokan", "Hotel"]):
    g = Cp[Cp.type == t].set_index("aspect").reindex(o); y = np.arange(len(o)) + (h / 2 if t == "Ryokan" else -h / 2)
    ax.barh(y, g.low_rated_share, height=h * 0.92, color=COL[t], label=f"{t} (n = {int(g.n_low_rated.iloc[0])})")
    for yy, v in zip(y, g.low_rated_share): ax.text(v + 0.3, yy, f"{v:.1f}%", va="center", fontsize=7.8, color=INK2)
ax.set_yticks(range(len(o))); ax.set_yticklabels(o); ax.grid(axis="y", visible=False); ax.set_xlim(0, 27)
ax.set_xticks([0, 5, 10, 15, 20, 25]); ax.set_xticklabels([f"{v}%" for v in [0, 5, 10, 15, 20, 25]])
ax.set_xlabel("Low-rated reviews with a negative mention of the aspect"); ax.legend(loc="lower right", handlelength=1, handleheight=0.8, fontsize=8.3)
save(fig, "figG_complaints")
print("figures written to", OUTD)
